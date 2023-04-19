from typing import List, Optional

from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, delete

from ..stdio import *

# from models import SystemUsers

SQLALCHEMY_DATABASE_URL = "sqlite:///sqlacm.db"
# ? connect_args={"check_same_thread": False} For Sqlite เท่านั้น
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# data_base_ip = "localhost"
# data_base_name = "dpark7"
# data_base_password = "dls@1234"

# print_warning("Connect DataBase")
# _password = urllib.parse.quote_plus(data_base_password)
# SQLALCHEMY_DATABASE_URL = F"mssql+pymssql://sa:{_password}@{data_base_ip}/{data_base_name}?charset=utf8"


# engine = create_engine(SQLALCHEMY_DATABASE_URL)

# For postgres DB
# SQLALCHEMY_DATABASE_URL = 'postgresql://root:dls@2021@172.17.0.3/postgres';
# engine = create_engine(SQLALCHEMY_DATABASE_URL);

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# metadata = MetaData(engine)
# mapper(Trans, Table('tran.transaction', metadata, autoload=True))
# print_success(F"Table Trans: {Trans}")

# mapper(Ticket, Table('ticket', metadata, autoload=True))
# print_success(F"Table Ticket: {Ticket}")

# mapper(PriceProfile, Table('tran.priceProfile', metadata, autoload=True))
# print_success(F"Table PriceProfile: {PriceProfile}")

# mapper(SystemParam, Table('param.systemParam', metadata, autoload=True))
# print_success(F"Table SystemParam: {SystemParam}")

# mapper(SysUser, Table('sysUser', metadata, autoload=True))
# print_success(F"Table SysUser: {SysUser}")

# mapper(Car, Table('car', metadata, autoload=True))
# print_success(F"Table Car: {Car}")

# ? MAIN LIB+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
async def create_session() -> Session:
    with Session(engine) as session:
        yield session

    # try:
    #     yield ss_db
    # except Exception as err:
    #     print_error(f"database session exception : {err}")
    # finally:
    #     ss_db.close()


class System_User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    password: str = Field(unique=True)
    createDate: datetime = Field(default=time_now(), nullable=False)
    create_by: str
    # last_login_Date = Column(DateTime)
    status: str
    user_level: str
    pictureUrl: str = Field(default="")
    remark: str = Field(default="")

    banks: List["Bank"] = Relationship(back_populates="system_user")


class Bank(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    pictureUrl: str = Field(default="")
    logo_enable: bool = Field(default=False)
    createDate: datetime = Field(default=time_now(), nullable=False)
    create_by: str
    status: str = Field(
        default="enable",
    )
    API_KEY: str
    API_SECRET: str
    BILLER_ID: str
    REF3: str
    scb_authorize: str = Field(default="https://api-sandbox.partners.scb/partners/sandbox/v2/oauth/authorize")
    scbGenerateAccessToken: str = Field(default="https://api-sandbox.partners.scb/partners/sandbox/v1/oauth/token")
    scbQRCodeAPI: str = Field(default="https://api-sandbox.partners.scb/partners/sandbox/v1/payment/qrcode/create")
    scbCheckPaySuccess: str = Field(default="https://api-sandbox.partners.scb/​partners/​v1/​payment/​billpayment/​inquiry")
    remark: str
    bank_type: str
    system_user_id: Optional[int] = Field(default=None, foreign_key="system_user.id")
    system_user: Optional[System_User] = Relationship(back_populates="banks")

    device_qrs: List["Device_Qr"] = Relationship(back_populates="bank")


class Device_Qr(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sn: str = Field(unique=True)
    name: str
    MERCHANT_ID: str
    REF2: str
    createDate: datetime = Field(default=time_now(), nullable=False)
    create_by: str
    last_connect: Optional[datetime] = Field(default=time_now())
    status: str = Field(
        default="enable",
    )
    remark: str = Field(default="")
    last_qr: Optional[str] = Field(default="")
    last_pay_success: Optional[str] = Field(default="")
    last_heartbeat: Optional[datetime] = Field(default=time_now())
    type: str = Field(default="MODULE")
    profile: str = Field(default="{}")
    bank_id: Optional[int] = Field(default=None, foreign_key="bank.id")
    bank: Optional[Bank] = Relationship(back_populates="device_qrs")

    qr_codes: List["Qr_Code"] = Relationship(back_populates="device_qr")


class Qr_Code(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    REF1: str
    REF2: str
    REF3: str
    amount: int
    qr_code_data: str
    createDate: datetime = Field(default=time_now(), nullable=False)
    status: str = Field(default="created")
    remark: str = Field(default="")

    device_qr_id: Optional[int] = Field(default=None, foreign_key="device_qr.id")
    device_qr: Optional[Device_Qr] = Relationship(back_populates="qr_codes")

    qr_code_pays: List["Qr_Code_Pay"] = Relationship(back_populates="qr_code")


class Qr_Code_Pay(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    createDate: datetime = Field(default=time_now(), nullable=False)
    payeeProxyId: str
    payeeProxyType: str
    payeeAccountNumber: str
    payeeName: str
    payerProxyId: str
    payerProxyType: str
    payerAccountNumber: str
    payerName: str
    sendingBankCode: str
    receivingBankCode: str
    amount: str
    channelCode: str
    transactionId: str
    transactionDateandTime: str
    billPaymentRef1: str
    billPaymentRef2: str
    billPaymentRef3: str
    currencyCode: str
    transactionType: str

    qr_code_id: Optional[int] = Field(default=None, foreign_key="qr_code.id")
    qr_code: Optional[Qr_Code] = Relationship(back_populates="qr_code_pays")


# with Session(engine) as session:
#     pass
#     sql = "ALTER TABLE bank ADD bank_type VARCHAR DEFAULT 'scb_payment'"
#     session.execute(sql)

# Base.metadata.create_all(engine)
SQLModel.metadata.create_all(engine)


def set_drop_table():
    print_warning("Drop table")
    with Session(engine) as session:
        table_drop = [Qr_Code_Pay, Qr_Code]
        for _t in table_drop:
            sql = delete(_t)
            print_warning(session.exec(sql))
        session.commit()


# set_drop_table()

print_success("import success module database.py")
