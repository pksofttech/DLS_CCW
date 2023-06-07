import base64
import os
import io
from statistics import mode
from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
)
from fastapi.responses import StreamingResponse, PlainTextResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import (
    FileResponse,
    RedirectResponse,
)
import json
from sqlalchemy.orm import Session
from sqlmodel import func, join, select, or_
from app.core.database import Device, Project, System_User, create_session
from app.core.auth import access_cookie_token

from ..stdio import *
from app.core import config
from app.core.auth import get_user
from app.service.mqtt import fast_mqtt


DIR_PATH = config.DIR_PATH

templates = Jinja2Templates(directory="templates")
router_page = APIRouter()

ksher_pubkey_pem = "./ksher_pubkey.pem"
Mch41423_PrivateKey = "./Mch41423_PrivateKey.pem"
PERMISSION_ADMIN = ["admin", "root"]
PERMISSION_SYSTEM = ["root"]


def check_permission(user_level, permission="admin") -> bool:
    if permission == "system":
        if user_level in PERMISSION_SYSTEM:
            return True
    elif permission == "admin":
        if user_level in PERMISSION_ADMIN:
            return True
    print_warning("check_permission not access")
    return False


@router_page.get("/favicon.ico", tags=["public"])
async def get_favicon():
    _pathImage = f"{DIR_PATH}/static/favicon.png"
    if not os.path.exists(_pathImage):
        print_warning("Not favicon.ico found")
        raise HTTPException(status_code=404, detail="Item not found")
    return FileResponse(_pathImage)


@router_page.get("/", tags=["public"])
async def main_page():
    _now = time_now()
    return templates.TemplateResponse(
        "login.html",
        {"request": {}, "now": _now, "app_title": config.APP_TITLE},
    )


@router_page.get("/ping", tags=["public"])
async def ping():
    _now = time_now()
    return f"Time process : {time_now() - _now}"


@router_page.get("/home", tags=["public"])
async def router_home(db: Session = Depends(create_session), user: System_User = Depends(access_cookie_token)):
    if not user:
        return RedirectResponse(url="/")
    if user.status.lower() == "disable":
        return templates.TemplateResponse("disable_user.html", {"request": {}, "user": user})

    _now = time_now()

    datas = {}
    return templates.TemplateResponse(
        "home.html",
        {
            "request": {},
            "user": user,
            "datas": datas,
            "now": _now,
        },
    )


@router_page.get("/project", tags=["public"])
async def router_project(
    db: Session = Depends(create_session),
    user: System_User = Depends(access_cookie_token),
):
    if not user:
        return RedirectResponse(url="/")
    if user.status.lower() == "disable":
        return templates.TemplateResponse("disable_user.html", {"request": {}, "user": user})
    _now = time_now()
    print_success(f"My user is {user.username}")

    owners = []
    if user.username == "root":
        projects = db.query(Project).order_by(Project.id).all()
        _system_user = db.query(System_User.username).where(System_User.username != "root").all()
        for _s in _system_user:
            owners.append(_s[0])
    else:
        owners = ["ME"]
        projects = db.query(Project).where(Project.system_user_id == user.id).order_by(Project.id).all()

    # print(projects)
    device_count = []
    for project in projects:
        _c = db.exec(select([func.count(Device.id)]).where(Device.project_id == project.id)).one()
        # print(_c)
        device_count.append(_c)
    print(device_count)
    return templates.TemplateResponse(
        "project.html",
        {
            "request": {},
            "user": user,
            "projects": projects,
            "device_count": device_count,
            "now": _now,
            "owners": owners,
        },
    )


@router_page.get("/dashboard", tags=["public"])
async def router_dashboard(
    db: Session = Depends(create_session),
    user: System_User = Depends(access_cookie_token),
    project_id: int = None,
):
    if not user:
        return RedirectResponse(url="/")
    if user.status.lower() == "disable":
        return templates.TemplateResponse("disable_user.html", {"request": {}, "user": user})
    _now = time_now()

    if user.username == "root":
        projects = db.query(Project).all()
    else:
        projects = db.query(Project).where(Project.system_user_id == user.id).all()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": {},
            "user": user,
            "projects": projects,
            "project_id": project_id if project_id else projects[0].id,
            "now": _now,
        },
    )


import random

TIME_OUT_HEARTBEAT = 6000


@router_page.get("/device", tags=["public"])
async def router_device(
    db: Session = Depends(create_session),
    user: System_User = Depends(access_cookie_token),
    project_id: int = None,
):
    if not user:
        return RedirectResponse(url="/")
    if user.status.lower() == "disable":
        return templates.TemplateResponse("disable_user.html", {"request": {}, "user": user})
    _now = time_now()

    devices = []
    project_name = []
    if project_id:
        project_name = db.query(Project.name).where(Project.id == project_id).one()
        devices = db.query(Device).where(Device.project_id == project_id).order_by(Device.sn).all()
    else:
        if user.username == "root":
            project_ids = db.query(Project.id, Project.name).order_by(Project.id).all()
        else:
            project_ids = db.query(Project.id, Project.name).where(Project.system_user_id == user.id).all()
        print(project_ids)
        for project_id in project_ids:
            # print_warning(project_id[1])
            project_name.append(project_id[1])
            ds = db.query(Device).where(Device.project_id == project_id[0]).order_by(Device.sn).all()
            for d in ds:
                devices.append(d)

    devices_on = []
    devices_off = []
    # print(devices)
    for device in devices:
        d: Device = device
        print(_now)
        _ts_now = int(round(_now.timestamp()))
        last_heart_beat = d.last_heart_beat + timedelta(hours=7)

        diff_of_heartbeat = _ts_now - last_heart_beat.timestamp()
        print(diff_of_heartbeat)
        # print(d)
        # ? Chack Time_out is device active
        if diff_of_heartbeat <= TIME_OUT_HEARTBEAT:
            devices_on.append(
                {
                    "id": d.id,
                    "pay": d.count_pay,
                    "name": d.name,
                    "sn": d.sn,
                    "last_heart_beat": last_heart_beat,
                    "sh": d.id,
                    "on": "OK",
                    "ps": "OK",
                    "vf": "OK",
                    "project_id": d.project_id,
                }
            )
        else:
            devices_off.append(
                {
                    "id": d.id,
                    "pay": d.count_pay,
                    "name": d.name,
                    "sn": d.sn,
                    "last_heart_beat": last_heart_beat,
                    "sh": "OK",
                    "on": "OK",
                    "ps": "OK",
                    "vf": "OK",
                    "project_id": d.project_id,
                }
            )

    return templates.TemplateResponse(
        "device.html",
        {
            "request": {},
            "user": user,
            "project_name": project_name,
            "devices_on": devices_on,
            "devices_off": devices_off,
            "now": _now,
        },
    )


@router_page.get("/dashboard_device", tags=["public"])
async def router_dashboard_device(
    db: Session = Depends(create_session),
    user: System_User = Depends(access_cookie_token),
    id: int = None,
):
    if not user:
        return RedirectResponse(url="/")
    if user.status.lower() == "disable":
        return templates.TemplateResponse("disable_user.html", {"request": {}, "user": user})
    _now = time_now()
    device: Device = db.query(Device).where(Device.id == id).one_or_none()

    if not device:
        return f"dashboard_device is not installed"
    if len(device.status) != 5:
        device.status = "11111"
        db.commit()
        db.refresh(device)
    str_price_rates = device.price_rates
    price_rates = str_price_rates.split(",")
    p01 = price_rates[0]
    if len(p01) <= 15:
        p01 = p01.ljust(15, "0")
    price_rate_01 = [
        p01[0:2],
        p01[2:4],
        p01[4:6],
        p01[6:8],
        p01[8:10],
        p01[10:12],
        p01[12:15],
    ]
    _d_s = device.status
    device_status = [
        int(_d_s[0:1]),
        int(_d_s[1:2]),
        int(_d_s[2:3]),
        int(_d_s[3:4]),
        int(_d_s[4:5]),
    ]

    print(device_status)
    return templates.TemplateResponse(
        "dashboard_device.html",
        {
            "request": {},
            "user": user,
            "device": device,
            "price_rate": price_rate_01,
            "device_status": device_status,
            "now": _now,
        },
    )


@router_page.get("/record", tags=["public"])
async def router_record(db: Session = Depends(create_session), user: System_User = Depends(access_cookie_token)):
    if not user:
        return RedirectResponse(url="/")
    if user.status.lower() == "disable":
        return templates.TemplateResponse("disable_user.html", {"request": {}, "user": user})
    _now = time_now()

    datas = {}
    if user.username == "root":
        projects = db.query(Project).all()
    else:
        projects = db.query(Project).where(Project.system_user_id == user.id).all()
    return templates.TemplateResponse(
        "record.html",
        {
            "request": {},
            "user": user,
            "datas": datas,
            "now": _now,
            "projects": projects,
        },
    )


@router_page.get("/admin", tags=["public"])
async def router_admin(db: Session = Depends(create_session), user: System_User = Depends(access_cookie_token)):
    if not user:
        return RedirectResponse(url="/")
    if user.status.lower() == "disable":
        return templates.TemplateResponse("disable_user.html", {"request": {}, "user": user})
    _now = time_now()

    if not user:
        return templates.TemplateResponse(
            "403.html",
            {
                "request": {},
            },
        )
    print(user.user_level)
    if not check_permission(user.user_level, permission="system"):
        return templates.TemplateResponse(
            "403.html",
            {
                "request": {},
            },
        )

    datas = {}
    datas["line_token"] = config.LINE_TOKEN
    datas["filter"] = filter
    datas["table_title"] = "ข้อมูลผู้ใช้งานระบบ"
    datas["username"] = user.username

    return templates.TemplateResponse(
        "system_config.html",
        {
            "request": {},
            "user": user,
            "datas": datas,
            "now": _now,
        },
    )


# bankCheckAccountBalance
# ******************** ESP32 ******************************!SECTION
@router_page.get("/heartbeat", tags=["esp32"], response_class=PlainTextResponse)
@router_page.get("/test_mqtt", tags=["mqtt"])
async def path_test_mqtt(
    publish: str = "/payment/test001",
    id: str = "test001",
    amound: str = 10,
    payer: str = "123456789",
    method: str = "test",
):
    d = {"id": id, "amound": amound, "payer": payer, "method": method}
    msg_json = json.dumps(d)
    fast_mqtt.publish(publish, msg_json)
    return {"success": True, "msg": f"{publish} : {msg_json}"}
