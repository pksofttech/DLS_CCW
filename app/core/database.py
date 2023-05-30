import os
import json
from typing import List, Optional

from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, delete, select

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
# SQLALCHEMY_DATABASE_URL = "postgresql://root:12341234@47.254.250.76/ccw"
# SQLALCHEMY_DATABASE_URL = "postgresql://root:12341234@172.17.0.18/ccw"
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "postgresql://root:12341234@157.230.246.160/ccw"
print_success(f"SQLALCHEMY_DATABASE_URL : {SQLALCHEMY_DATABASE_URL}")

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
    projects: List["Project"] = Relationship(back_populates="system_user")


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    createDate: datetime = Field(default=time_now(), nullable=False)
    status: str = Field(default="")
    remark: str = Field(default="")
    address: str = Field(default="")
    staff: str = Field(default="")
    phone: str = Field(default="")
    pictureUrl: str = Field(default="/static/image/logo.png")
    system_user_id: Optional[int] = Field(foreign_key="system_user.id", nullable=False)
    system_user: Optional[System_User] = Relationship(back_populates="projects")


class Device(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sn: str = Field(unique=True)
    name: str = Field(unique=True)
    createDate: datetime = Field(default=time_now(), nullable=False)
    last_heart_beat: datetime = Field(default=time_now(), nullable=False)
    create_by: str
    service_times: str = Field(default="")
    price_rates: str = Field(default="")
    status: str = Field(default="")
    remark: str = Field(default="")
    count_pay: int = Field(default=0)
    project_id: Optional[int] = Field(foreign_key="project.id", nullable=False)


# ******************** Time DB ********************************
class Log_status(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    time: datetime
    sn: str = Field(nullable=False)
    value: str = Field(nullable=False)


class Log_mqtt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    time: datetime
    topic: str = Field(nullable=False)
    sn: str = Field(nullable=False)
    message: str = Field(nullable=False)


class Log_pay(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    time: datetime
    amount: int = Field(nullable=False)
    sn: str = Field(nullable=False)
    name: str = Field(nullable=False)
    type: str = Field(nullable=False)
    device_id: Optional[int] = Field(foreign_key="device.id", nullable=False)
    project_id: Optional[int] = Field(foreign_key="project.id", nullable=False)


# with Session(engine) as session:
#     pass
#     sql = "ALTER TABLE bank ADD bank_type VARCHAR DEFAULT 'scb_payment'"
#     session.execute(sql)

# Base.metadata.create_all(engine)


def set_drop_table():
    print_warning("Drop table")
    with Session(engine) as session:
        table_drop = [Project, Device]

        for _t in table_drop:
            sql = delete(_t)
            print_warning(session.exec(sql))
            session.commit()


# set_drop_table()

print_success("import success module database.py")

from .auth import get_password_hash


# SQLModel.metadata.drop_all(engine)
# SQLModel.metadata.create_all(engine)


async def set_init_database():
    # return
    print_success("set_init_database")

    with Session(engine) as session:
        statement = select(System_User).where(System_User.username == "root")
        _root: System_User = session.exec(statement).one_or_none()

        if not _root:
            print_warning(f"NOT ROOT System User")
            root_user = System_User()
            root_user.username = "root"
            root_user.password = get_password_hash("12341234")
            # root_user.email = "pksofttech@gmail.com"
            _reg = time_now().strftime("%Y-%m-%dT%H:%M%z")
            root_user.createDate = datetime.strptime(f"{_reg}", "%Y-%m-%dT%H:%M%z")
            root_user.create_by = "Default System"
            root_user.status = "SYSTEM"
            root_user.user_level = "root"
            session.add(root_user)
            session.commit()
            user_demo = ["ตลาดธีรรัตน์", "ccw"]
            for i in user_demo:
                _u = System_User()
                _u.username = i
                _u.password = get_password_hash("12341234")
                # root_user.email = "pksofttech@gmail.com"
                _reg = time_now().strftime("%Y-%m-%dT%H:%M%z")
                _u.createDate = datetime.strptime(f"{_reg}", "%Y-%m-%dT%H:%M%z")
                _u.create_by = "Default_Test"
                _u.status = "Test User"
                _u.user_level = "admin"
                session.add(_u)
                print_warning(f"add user for test :{_u.username}")
            session.commit()
        else:
            return 0
            _root.user_level = "root"
            _root.status = "Enable"
            session.commit()

        rows = session.exec(select(Project)).all()
        if not rows:
            p = Project()
            p.name = "Project ตลาดธีรรัตน์"
            p.system_user_id = 2
            p.status = "Demo"
            p.staff = "mr.ตลาดธีรรัตน์"
            p.address = "123/456 ตลาดธีรรัตน์"
            p.phone = "02-123-4567"
            # p.pictureUrl = "/static/image/logo.png"
            session.add(p)

            p = Project()
            p.name = "Project Demo 02"
            p.system_user_id = 3
            p.status = "Demo"
            p.staff = "mr.demo"
            p.address = "123/456 demonstrating"
            p.phone = "02-123-4567"
            session.add(p)

            p = Project()
            p.name = "Project CCW 01"
            p.system_user_id = 3
            p.status = "CCW"
            p.staff = "mr.CCW"
            p.address = "123/456 demonstrating"
            p.phone = "02-123-4567"
            session.add(p)

        session.commit()
        rows = session.exec(select(Project)).all()
        print_success(rows)

        rows = session.exec(select(Device)).all()
        if not rows:
            d = Device(
                sn="m_oum001",
                name="ตู้ ตลาดธีรรัตน์ 001",
                project_id=1,
                create_by="System for test",
                status="demo",
                price_rates="101010101010",
            )
            session.add(d)
            session.commit()
            print_success(d)

            d = Device(
                sn="m_oum002",
                name="ตู้ ตลาดธีรรัตน์ 002",
                project_id=1,
                create_by="System for test",
                status="demo",
                price_rates="101010101010",
            )
            session.add(d)
            session.commit()
            print_success(d)

            d = Device(
                sn="m_ccw001",
                name="ทดสอบ test_001",
                project_id=2,
                create_by="System for test",
                status="demo",
                price_rates="101010101010",
            )
            session.add(d)
            session.commit()
            print_success(d)

        rows = session.exec(select(Device)).all()
        print_success(rows)
    print_success("set_init_database successfully")


# ? *************************************************************************************************!SECTION
async def process_mqtt_data(data: dict):
    sn = data.get("sn", None)
    topic = data.get("topic", None)
    message = data.get("message", None)
    json_msg = json.loads(message)
    try:
        _now = time_now()
        with Session(engine) as session:
            # print_success(sn)
            _device: Device = session.query(Device).where(Device.sn == sn).one_or_none()

            if _device:
                if topic == "info":
                    pass
                elif topic == "heartbeat":
                    pass
                elif topic == "getmoney":
                    _pay = json_msg.get("amount", 0)
                    _type = json_msg.get("type", "-")
                    _device.count_pay += _pay

                    if _type == "BV20":
                        _type = "ธนบัตร"
                    _log_pay = Log_pay(
                        time=_now,
                        sn=sn,
                        name=_device.name,
                        amount=_pay,
                        type=_type,
                        device_id=_device.id,
                        project_id=_device.project_id,
                    )
                    session.add(_log_pay)
                    session.commit()

                elif topic == "stats":
                    _coin = json_msg.get("coin", 0)
                    _bank = json_msg.get("bank", 0)
                    _qr = json_msg.get("qr", 0)
                    _hpwater = json_msg.get("hpwater", 0)
                    _foam = json_msg.get("foam", 0)
                    _air = json_msg.get("air", 0)
                    _water = json_msg.get("water", 0)
                    _pay = int(_coin) + int(_bank) + int(_qr)
                    _device.count_pay += _pay

                    print(_coin, _bank, _qr)
                    if _coin:
                        _log_pay_coin = Log_pay(
                            time=_now,
                            sn=sn,
                            name=_device.name,
                            amount=int(_coin),
                            type="COIN",
                            device_id=_device.id,
                            project_id=_device.project_id,
                        )
                        session.add(_log_pay_coin)
                        session.commit()

                    if _bank:
                        _log_pay_bank = Log_pay(
                            time=_now,
                            sn=sn,
                            name=_device.name,
                            amount=int(_bank),
                            type="ธนบัตร",
                            device_id=_device.id,
                            project_id=_device.project_id,
                        )
                        session.add(_log_pay_bank)
                        session.commit()

                    if _qr:
                        _log_pay_qr = Log_pay(
                            time=_now,
                            sn=sn,
                            name=_device.name,
                            amount=int(_qr),
                            type="QR",
                            device_id=_device.id,
                            project_id=_device.project_id,
                        )
                        session.add(_log_pay_qr)
                        session.commit()

                    print(message)
                else:
                    print_warning(f"Warning {topic} is not implemented")

                _device.last_heart_beat = _now
                # print_success(_device)
                session.commit()
                # print_success(f"set heartbeat of {sn} : {_device.last_heart_beat}")
                _log_mqtt = Log_mqtt(
                    sn=sn,
                    topic=topic,
                    message=message,
                    time=_now,
                )
                session.add(_log_mqtt)
                session.commit()

                print_success(f"seve_to_log_mqtt {topic}:{sn}")
            else:
                pass
                # print_warning(f"Warning {sn} is not in database")

    except Exception as err:
        print_error(f"seve_to_log_mqtt exception : {err}")
        return None

    return True
