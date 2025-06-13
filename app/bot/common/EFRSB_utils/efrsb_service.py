import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import aiohttp
from sqlalchemy import select

from app.bot.common.EFRSB_utils.models import ObjectEFRSBListAdapter
from app.config import settings

from app.db.dao import EFRSBRecordDAO
from app.db.models import EFRSBRecord
from app.db.schemas import EFRSBRecordSchema
from app.db.dao import DeloEFRSBDAO
from app.db.database import async_session_maker

logger = logging.getLogger(__name__)


# Функция-адаптер для сохранения информации о деле ЕФРСБ через DAO
async def append_delo_db(
    session,
    revision,
    fullname,
    publish_date,
    birthdate=None,
    birthplace=None,
    address=None,
    inn=None,
    snils=None,
    court_region=None,
    case_number=None,
    decision_date=None,
):
    record_data = {
        "revision": revision,
        "fullname": fullname,
        "birthdate": birthdate,
        "birthplace": birthplace,
        "address": address,
        "inn": inn,
        "snils": snils,
        "court_region": court_region,
        "case_number": case_number,
        "decision_date": decision_date,
        "publish_date": publish_date,
    }
    # Валидируем и создаем объект записи через схему
    record = EFRSBRecordSchema(**record_data)
    await EFRSBRecordDAO.add(session, record)


async def get_needed_info(data, session) -> list[dict]:
    """
    Обрабатывает массив объектов, полученных из ЕФРСБ,
    извлекает нужные данные, сохраняет их через DAO и возвращает список словарей.
    """
    all_objts = []
    for obj in data:
        try:
            root = ET.fromstring(obj.body)
        except ET.ParseError:
            await append_delo_db(
                session,
                revision=obj.revision,
                publish_date=obj.publish_date,
                fullname="incorrect",
            )
            continue
        except Exception:
            await append_delo_db(
                session,
                revision=obj.revision,
                publish_date=obj.publish_date,
                fullname="incorrect",
            )
            continue

        # Поиск данных о банкроте
        bankrupt = root.find(".//BankruptPerson")
        fio = bankrupt
        if bankrupt is None:
            bankrupt = root.find(".//Bankrupt")
            if bankrupt is None:
                await append_delo_db(
                    session,
                    revision=obj.revision,
                    publish_date=obj.publish_date,
                    fullname="incorrect",
                )
                continue
            fio = bankrupt.find(".//Fio")
            if fio is None:
                await append_delo_db(
                    session,
                    revision=obj.revision,
                    publish_date=obj.publish_date,
                    fullname="incorrect",
                )
                continue

        first_name = fio.findtext("FirstName", default="") if fio is not None else ""
        middle_name = fio.findtext("MiddleName", default="") if fio is not None else ""
        last_name = fio.findtext("LastName", default="") if fio is not None else ""
        full_name = f"{last_name} {first_name} {middle_name}".strip()

        birthdate_str = bankrupt.findtext("Birthdate", default="")
        birthplace = bankrupt.findtext("Birthplace", default="")
        address = bankrupt.findtext("Address", "")
        inn = bankrupt.findtext("Inn", "")
        snils = bankrupt.findtext("Snils", "")
        message_info = root.find("MessageInfo")
        if message_info is None:
            court_name = "incorrect"
            case_number = "incorrect"
            decision_date_str = None
            await append_delo_db(
                session,
                revision=obj.revision,
                fullname=full_name,
                birthdate=birthdate_str,
                birthplace=birthplace,
                address=address,
                inn=inn,
                snils=snils,
                court_region=court_name,
                case_number=case_number,
                decision_date=decision_date_str,
                publish_date=obj.publish_date,
            )
            continue
        message_type = message_info.attrib.get("MessageType", "")

        if message_type == "ArbitralDecree":
            court_decision = message_info.find("CourtDecision")
            if court_decision is None:
                continue
            citizen_not_released = court_decision.find(
                "CitizenNotReleasedFromResponsibility"
            )
            if (
                citizen_not_released is None
                or citizen_not_released.get(
                    "{http://www.w3.org/2001/XMLSchema-instance}nil"
                )
                != "true"
            ):
                court_name = "incorrect"
                case_number = "incorrect"
                decision_date_str = None
                await append_delo_db(
                    session,
                    revision=obj.revision,
                    fullname=full_name,
                    birthdate=birthdate_str,
                    birthplace=birthplace,
                    address=address,
                    inn=inn,
                    snils=snils,
                    court_region=court_name,
                    case_number=case_number,
                    decision_date=decision_date_str,
                    publish_date=obj.publish_date,
                )
                continue
            decision_type = court_decision.find("DecisionType")
            decree_name = (
                decision_type.attrib.get("Name") if decision_type is not None else ""
            )
            court_decree = court_decision.find("CourtDecree")
            court_name = (
                court_decree.findtext("CourtName", default="")
                if court_decree is not None
                else ""
            )
            case_number = root.findtext(".//CaseNumber", "").strip()
            decision_date_str = (
                court_decree.findtext("DecisionDate", default="")
                if court_decree is not None
                else ""
            )
            if decree_name == "о завершении реализации имущества гражданина":
                type_message = "Сообщение о завершении реализации имущества гражданина"
            else:
                type_message = None
                court_name = "incorrect"
                case_number = "incorrect"
                decision_date_str = None
        elif message_type == "CompletionOfExtrajudicialBankruptcy":
            type_message = (
                "Сообщение о завершении процедуры внесудебного банкротства гражданина"
            )
            court_name = "ВБФЛ"
            case_number = "ВБФЛ"
            decision_date_str = None
        else:
            type_message = None
            court_name = "incorrect"
            case_number = "incorrect"
            decision_date_str = None

        # Преобразование дат, если они заданы
        decision_date = (
            datetime.strptime(decision_date_str, "%Y-%m-%d")
            if decision_date_str
            else None
        )
        birthdate_dt = (
            datetime.strptime(birthdate_str, "%d.%m.%Y") if birthdate_str else None
        )

        obj_info = {
            "type_message": type_message,
            "full_name": full_name,
            "birthdate": birthdate_dt,
            "birthplace": birthplace,
            "address": address,
            "inn": inn,
            "snils": snils,
            "court_region": court_name,
            "case_number": case_number,
            "decision_date": decision_date,
            "publish_date": obj.publish_date,
            "revision": obj.revision,
        }
        # Сохраняем запись через DAO
        await append_delo_db(
            session,
            revision=obj.revision,
            fullname=full_name,
            birthdate=birthdate_str,
            birthplace=birthplace,
            address=address,
            inn=inn,
            snils=snils,
            court_region=court_name,
            case_number=case_number,
            decision_date=decision_date,
            publish_date=obj.publish_date,
        )
        all_objts.append(obj_info)
    return all_objts


async def get_async_request(
    session,
    min_revision: int = 0,
    portion_size: int = 2000,
    token: str = settings.EFRSB_TOKEN,
):
    url = "https://probili.ru/efrsb/repl-api.php/message"
    params = {
        "portion-size": portion_size,
        "revision-greater-than": min_revision,
        "auth-token": token,
        "no-base64": "",
    }
    async with aiohttp.ClientSession() as http_session:
        async with http_session.get(url, params=params) as response:
            if response.status == 200:
                logger.info("Запрос прошел успешно")
                data = await response.text()
                valid_data = ObjectEFRSBListAdapter.validate_json(data)
                res = await get_needed_info(valid_data, session)
                if res:
                    last = sorted(res, key=lambda x: x["publish_date"])[-1]
                    logger.info(
                        f"Получили данные запросом для ЕФРСБ до {last['publish_date']}"
                    )
                return res
            else:
                logger.error(f"Ошибка {response.status} при получении данных с ЕФРСБ")
                return None


async def get_nearest_values(session, date1: datetime, date2: datetime):
    # Предполагается, что у вас есть DAO для работы с сохраненными записями ЕФРСБ

    logger.info(f"Получаем срез объектов от {date1.date()} до {date2.date()}")
    data = sorted(
        await DeloEFRSBDAO.find_all(session, filters={"date_range": [date1, date2]}),
        key=lambda x: (x.publish_date, x.id),
    )
    if data and data[0].publish_date.date() > date1.date():
        before_date1 = data[0]
        logger.info("Левая граница не подходит. Ищем новую")
        min_revision = before_date1.id - settings.STEP
        while True:
            res = sorted(
                await get_async_request(
                    session, min_revision=min_revision, portion_size=settings.STEP
                ),
                key=lambda x: (x["publish_date"], x["revision"]),
            )
            if res is None:
                logger.info(f"Уснули на левой границе: {min_revision}")
                await asyncio.sleep(60)
            else:
                min_revision -= settings.STEP
                if res[0]["publish_date"].date() < date1.date():
                    logger.info("Обновили before_date1")
                    data = sorted(
                        await DeloEFRSBDAO.find_all(
                            session, filters={"date_range": [date1, date2]}
                        ),
                        key=lambda x: (x.publish_date, x.id),
                    )
                    break
    # Если правая граница не соответствует
    if data and data[-1].publish_date.date() < date2.date():
        after_date2 = data[-1]
        logger.info("Правая граница не подходит. Ищем новую")
        min_revision = after_date2.id
        while True:
            res = sorted(
                await get_async_request(
                    session, min_revision=min_revision, portion_size=settings.STEP
                ),
                key=lambda x: (x["publish_date"], x["revision"]),
            )
            if res is None:
                logger.info(f"Уснули на правой границе: {min_revision}")
                await asyncio.sleep(60)
            else:
                min_revision += settings.STEP
                if res[-1]["publish_date"].date() > date2.date():
                    logger.info("Обновили after_date2")
                    data = sorted(
                        await DeloEFRSBDAO.find_all(
                            session, filters={"date_range": [date1, date2]}
                        ),
                        key=lambda x: (x.publish_date, x.id),
                    )
                    break
    logger.info("Все объекты среза загружены")
    return data


async def find_bankruptcy_by_user(full_name: str, birthdate: str) -> list[dict]:
    """
    Ищет банкротства по ФИО и дате рождения в базе ЕФРСБ.

    Args:
        full_name (str): ФИО в формате "Фамилия Имя Отчество"
        birthdate (str): Дата рождения в строковом формате

    Returns:
        list[dict]: Список найденных банкротств
    """
    try:
        # Преобразуем строковую дату в datetime
        birth_date = (
            datetime.strptime(birthdate, "%d.%m.%Y").date() if birthdate else None
        )

        async with async_session_maker() as session:
            # Создаем SQL запрос
            query = select(EFRSBRecord).where(
                EFRSBRecord.full_name.ilike(f"%{full_name}%")
            )

            if birth_date:
                # Добавляем условие по дате рождения, если она указана
                query = query.where(EFRSBRecord.birthdate == birth_date)

            # Выполняем запрос
            result = await session.execute(query)
            records = result.scalars().all()

            # Преобразуем результаты в список словарей
            bankruptcies = []
            for record in records:
                bankruptcies.append(
                    {
                        "type_message": "Сообщение о банкротстве",
                        "full_name": record.full_name,
                        "birthdate": record.birthdate,
                        "birthplace": record.birthplace,
                        "address": record.address,
                        "inn": record.inn,
                        "snils": record.snils,
                        "court_region": record.court_region,
                        "case_number": record.case_number,
                        "decision_date": record.decision_date,
                        "publish_date": record.publish_date,
                    }
                )

            logger.info(
                f"Найдено {len(bankruptcies)} записей о банкротстве для {full_name}"
            )
            return bankruptcies

    except Exception as e:
        logger.error(f"Ошибка при поиске банкротств: {str(e)}")
        return []
