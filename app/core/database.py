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
SQLALCHEMY_DATABASE_URL = "postgresql://root:12341234@47.254.250.76/ccw"
SQLALCHEMY_DATABASE_URL = "postgresql://root:12341234@172.17.0.18/ccw"
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
    status: str = Field(default="")
    remark: str = Field(default="")
    address: str = Field(default="")
    staff: str = Field(default="")
    phone: str = Field(default="")
    pictureUrl: str = Field(default="/static/image/logo.png")
    system_user_id: Optional[int] = Field(foreign_key="system_user.id", nullable=False)


class Device(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sn: str = Field(unique=True)
    createDate: datetime = Field(default=time_now(), nullable=False)
    last_heart_beat: datetime = Field(default=time_now(), nullable=False)
    create_by: str
    service_times: str = Field(default="")
    price_rates: str = Field(default="")
    status: str = Field(default="")
    remark: str = Field(default="")
    project_id: Optional[int] = Field(foreign_key="project.id", nullable=False)


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
SQLModel.metadata.drop_all(engine)
SQLModel.metadata.create_all(engine)


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


async def set_init_database():
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
            user_demo = ["demo", "ccw"]
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
            _root.user_level = "root"
            _root.status = "Enable"
            session.commit()

        rows = session.exec(select(Project)).all()
        if not rows:
            statement = select(System_User).where(System_User.username == "demo")
            demo: System_User = session.exec(statement).one()

            p = Project()
            p.name = "Project Demo 01"
            p.system_user_id = demo.id
            p.status = "Demo"
            p.staff = "mr.demo"
            p.address = "123/456 demonstrating"
            p.phone = "02-123-4567"
            # p.pictureUrl = "/static/image/logo.png"
            session.add(p)

            p = Project()
            p.name = "Project Demo 02"
            p.system_user_id = demo.id
            p.status = "Demo"
            p.staff = "mr.demo"
            p.address = "123/456 demonstrating"
            p.phone = "02-123-4567"
            session.add(p)

        session.commit()
        rows = session.exec(select(Project)).all()
        print_success(rows)

        rows = session.exec(select(Device)).all()
        if not rows:
            d = Device(
                sn="sn_demo-001",
                project_id=1,
                create_by="System for test",
                status="demo",
                price_rates="[{p01=5,p02=10,p03=15,p04=20}]",
            )
            session.add(d)
            session.commit()
            print_success(d)

            d = Device(
                sn="sn_demo-002",
                project_id=2,
                create_by="System for test",
                status="demo",
                price_rates="[{p01=5,p02=10,p03=15,p04=20}]",
            )
            session.add(d)
            session.commit()
            print_success(d)

        rows = session.exec(select(Device)).all()
        print_success(rows)
    print_success("set_init_database successfully")
