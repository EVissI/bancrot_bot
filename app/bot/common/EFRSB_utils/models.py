from pydantic import BaseModel, Field, TypeAdapter
from datetime import datetime


class ObjectEFRSB(BaseModel):
    efrsb_id: int | None
    arbitr_manager_id: int | None = Field(alias='ArbitrManagerID')
    bankrupt_id: int | None = Field(alias='BankruptId')
    inn: str | None = Field(alias='INN')
    snils: str | None = Field(alias='SNILS')
    ogrn: str | None = Field(alias='OGRN')
    publish_date: datetime | None = Field(alias='PublishDate')
    body: str | None = Field(alias='Body')
    message_info_message_type: str | None = Field(alias='MessageInfo_MessageType')
    number: str | None = Field(alias='Number')
    message_guid: str | None = Field(alias='MessageGUID')
    revision: int | None = Field(alias='Revision')


ObjectEFRSBListAdapter = TypeAdapter(list[ObjectEFRSB])
