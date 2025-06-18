
from app.db.base import BaseDAO
from app.db.models import Delo, EFRSBRecord, TelegramUser,Promocode,UserPromocode


class UserDAO(BaseDAO[TelegramUser]):
    model = TelegramUser
    
class PromocodeDAO(BaseDAO[Promocode]):
    model = Promocode

class UserPromocodeDAO(BaseDAO[UserPromocode]):
    model = UserPromocode

class EFRSBRecordDAO:
    model = EFRSBRecord

class DeloEFRSBDAO:
    model = Delo