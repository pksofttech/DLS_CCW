import base64
import os
import io
from statistics import mode
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    Form,
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
from app.service.ksher_pay_sdk import KsherPay

from ..stdio import *
from app.core import config
from app.core.auth import get_user
import qrcode
from promptpay import qrcode as promptpay_qrcode
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
        projects = db.query(Project).all()
        _system_user = db.query(System_User.username).where(System_User.username != "root").all()
        for _s in _system_user:
            owners.append(_s[0])
    else:
        owners = ["ME"]
        projects = db.query(Project).where(Project.system_user_id == user.id).all()

    return templates.TemplateResponse(
        "project.html",
        {
            "request": {},
            "user": user,
            "projects": projects,
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
            "project_id": project_id,
            "now": _now,
        },
    )


import random


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
    _now = time_now(0)

    devices = []
    project_name = []
    if project_id:
        project_name = db.query(Project.name).where(Project.id == project_id).one()
        devices = db.query(Device).where(Device.project_id == project_id).all()
    else:
        if user.username == "root":
            project_ids = db.query(Project.id, Project.name).all()
        else:
            project_ids = db.query(Project.id, Project.name).where(Project.system_user_id == user.id).all()
        print(project_ids)
        for project_id in project_ids:
            # print_warning(project_id[1])
            project_name.append(project_id[1])
            ds = db.query(Device).where(Device.project_id == project_id[0]).all()
            for d in ds:
                devices.append(d)

    devices_on = []
    devices_off = []
    print(devices)
    for device in devices:
        d: Device = device
        print(_now)
        print(d.last_heart_beat)
        print(_now - d.last_heart_beat)
        print(d)
        devices_on.append(
            {
                "id": d.id,
                "pay": random.randint(100, 5000),
                "sn": d.sn,
                "last_heart_beat": d.last_heart_beat,
                "sh": "OK",
                "on": "OK",
                "ps": "OK",
                "vf": "OK",
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
    bank_id: int = None,
    device_id: int = None,
):
    if not user:
        return RedirectResponse(url="/")
    if user.status.lower() == "disable":
        return templates.TemplateResponse("disable_user.html", {"request": {}, "user": user})
    _now = time_now()
    devices = range(4)
    devices_off = range(2)
    return templates.TemplateResponse(
        "dashboard_device.html",
        {
            "request": {},
            "user": user,
            "devices": devices,
            "devices_off": devices_off,
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
    return templates.TemplateResponse(
        "record.html",
        {
            "request": {},
            "user": user,
            "datas": datas,
            "now": _now,
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
