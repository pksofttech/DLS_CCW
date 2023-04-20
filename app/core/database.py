from typing import List, Optional

from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, delete

from ..stdio import *

# from models import SystemUsers

# SQLALCHEMY_DATABASE_URL = "sqlite:///sqlacm.db"
# ? connect_args={"check_same_thread": False} For Sqlite เท่านั้น
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# data_base_ip = "localhost"
# data_base_name = "dpark7"
# data_base_password = "dls@1234"

# print_warning("Connect DataBase")
# _password = urllib.parse.quote_plus(data_base_password)
# SQLALCHEMY_DATABASE_URL = F"mssql+pymssql://sa:{_password}@{data_base_ip}/{data_base_name}?charset=utf8"


# engine = create_engine(SQLALCHEMY_DATABASE_URL)

# For postgres DB
SQLALCHEMY_DATABASE_URL = "postgresql://root:12341234@47.254.250.76/ccw"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

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
    projects: List["Project"] = Relationship()


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    createDate: datetime = Field(default=time_now(), nullable=False)
    create_by: str
    # last_login_Date = Column(DateTime)

    status: str = Field(default="")
    remark: str = Field(default="")
    owner: int = Field(nullable=False)
    system_user_id: Optional[int] = Field(default=None, foreign_key="system_user.id")


class Device(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sn: str = Field(unique=True)
    createDate: datetime = Field(default=time_now(), nullable=False)
    create_by: str
    # last_login_Date = Column(DateTime)
    service_times: str = Field(default="")
    price_rates: str = Field(default="")
    status: str = Field(default="")
    remark: str = Field(default="")
    system_user_id: int = Field(nullable=False)


# ******************** Time DB ********************************
class Log_status(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    time: datetime
    sn: str = Field(nullable=False)
    value: str = Field(nullable=False)


# with Session(engine) as session:
#     pass
#     sql = "ALTER TABLE bank ADD bank_type VARCHAR DEFAULT 'scb_payment'"
#     session.execute(sql)

# Base.metadata.create_all(engine)
SQLModel.metadata.create_all(engine)


def set_drop_table():
    print_warning("Drop table")
    with Session(engine) as session:
        table_drop = [System_User, Device, Log_status]
        for _t in table_drop:
            sql = delete(_t)
            print_warning(session.exec(sql))
        session.commit()


set_drop_table()

print_success("import success module database.py")
