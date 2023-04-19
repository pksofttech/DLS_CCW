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
from app.core.database import Bank, Device_Qr, Qr_Code, Qr_Code_Pay, System_User, create_session
from app.core.auth import access_cookie_token
from app.service.ksher_pay_sdk import KsherPay

from ..stdio import *
from app.core import config
from app.core.auth import get_user
from app.service import apiqrpayment, scb_easynet
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


@router_page.get("/dashboard", tags=["public"])
async def router_dashboard(
    db: Session = Depends(create_session),
    user: System_User = Depends(access_cookie_token),
    bank_id: int = None,
):
    if not user:
        return RedirectResponse(url="/")
    if user.status.lower() == "disable":
        return templates.TemplateResponse("disable_user.html", {"request": {}, "user": user})
    _now = time_now()

    devices = range(4)
    devices_off = range(2)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": {},
            "user": user,
            "devices": devices,
            "devices_off": devices_off,
            "now": _now,
        },
    )


@router_page.get("/device", tags=["public"])
async def router_device(
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
        "device.html",
        {
            "request": {},
            "user": user,
            "devices": devices,
            "devices_off": devices_off,
            "now": _now,
        },
    )


@router_page.get("/dashboard_device", tags=["public"])
async def router_device(
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

    condition = True
    if user.user_level != "root":
        condition = or_(Bank.system_user_id == user.id)
    sql = select(Bank.name).where(condition)
    # print(sql)
    _banks: Bank = db.exec(sql).all()

    datas = {}
    return templates.TemplateResponse(
        "record.html",
        {
            "request": {},
            "user": user,
            "banks": _banks,
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
async def heartbeat_esp32(
    sn: str,
    db: Session = Depends(create_session),
):
    _now = time_now()
    _device: Device_Qr = db.exec(select(Device_Qr).where(Device_Qr.sn == sn)).one_or_none()
    if _device:
        _device.last_heartbeat = _now
        db.commit()
    else:
        return "sn not found"
    return "successful"


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
