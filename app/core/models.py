from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timedelta, timezone
from ..stdio import *


class SystemUsers_type(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_type: str


class SystemUsers(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50)
    password: str = Field(max_length=256)
    create_date: datetime = Field(default=time_now())
    create_by: str = Field(default="SYSTEM")
    status: str = Field(default="REGISTERED")
    user_level: str = Field(default="OPERATOR")
    remark: str = Field(default="")
    type: int = Field(nullable=True, foreign_key="systemusers_type.id")


class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    time: Optional[datetime] = Field(default=time_now())
    log_type: Optional[str] = Field(default="info")
    msg: str
    log_owner: int = Field(default=None, foreign_key="systemusers.id")


class ScbPayLog(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    payeeProxyId: str = Field(max_length=64)
    billPaymentRef1: str = Field(max_length=64)
    amount: int
    transactionDateandTime: datetime
    payerName: str = Field(max_length=64)
