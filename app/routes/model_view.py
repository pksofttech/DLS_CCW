import base64
import json
import os
import re
import time
from io import BytesIO
from statistics import mode

from fastapi import APIRouter, Depends, FastAPI, File, Form, Request, Response, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from PIL import Image
from sqlmodel import Session, func, join, or_, select

from app.core import config
from app.core.auth import access_cookie_token, get_current_user, get_password_hash

# from sqlalchemy import or_
# from sqlalchemy.orm import Session
from app.core.database import Bank, Device_Qr, Qr_Code, Qr_Code_Pay, System_User, create_session

from ..stdio import *

DIR_PATH = config.DIR_PATH

# ****************************************************************************************************************************************
router_systems_user = APIRouter(prefix="/api/systems_user")


@router_systems_user.get("/")
async def path_system_user_get(id: int, user=Depends(get_current_user), db: Session = Depends(create_session)):
    _item: System_User = db.exec(select(System_User).where(System_User.id == id)).one_or_none()
    if _item:
        return _item
    else:
        return {"success": False, "msg": "item not found"}


@router_systems_user.post("/")
async def path_systems_user_post(
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
    username: str = Form(...),
    password: str = Form(default=None),
    status: str = Form(default=None),
    user_level: str = Form(...),
    image_upload: UploadFile = File(None),
    remark: str = Form(...),
    id: int = Form(default=None),
):
    if id:
        _system_user = db.exec(select(System_User).where(System_User.id == id)).one_or_none()
        if not _system_user:
            return {"success": False, "msg": "item is not already in database"}

        if username.lower() == "root" and user != _system_user:
            return {"success": False, "msg": f"root not already in use please other name !?@#@$)(**&*&^%&(()^&%^$#$#$$^^&^*^"}

        if user.username == "root" and username != "root" and _system_user.username == "root":
            return {"success": False, "msg": f"root not chang other name !?@#@$)(**&*&^%&(()^&%^$#$#$$^^&^*^"}

        if username == "root":
            user_level = None
            status = None

        if username:
            _system_user.username = username
        if password:
            _system_user.password = get_password_hash(password)
        if status:
            _system_user.status = status
        if user_level:
            _system_user.user_level = user_level
        if remark:
            _system_user.remark = remark

        db.commit()
        db.refresh(_system_user)
        print_warning("chang data user")
        print_warning(_system_user)
    else:
        _system_user = db.exec(select(System_User).where(System_User.username == username)).one_or_none()
        if _system_user:
            return {"success": False, "msg": "item is already in database"}

        _system_user = System_User(
            username=username,
            password=get_password_hash(password),
            status=status,
            user_level=user_level,
            remark=remark,
            create_by=user.username,
        )
        db.add(_system_user)
        db.commit()
        db.refresh(_system_user)

    if image_upload:
        image_content = await image_upload.read()
        image_upload = Image.open(BytesIO(image_content))

        if image_upload.format == "PNG":
            image_upload = image_upload.convert("RGB")
        try:
            _path = f"/static/image/system_user/{_system_user.id}.jpg"
            image_upload.save(f"{DIR_PATH}{_path}")
            _system_user.pictureUrl = _path + f"?time_stamp={time.gmtime()}"
            db.commit()

        except Exception as e:
            print_error(e)

    return {"success": True, "msg": "successfully"}


@router_systems_user.delete("/{id}")
async def path_system_user_delete(id: int, user: System_User = Depends(get_current_user), db: Session = Depends(create_session)):
    _system_user: System_User = db.exec(select(System_User).where(System_User.id == id)).one_or_none()
    if _system_user:
        if _system_user.username == "root":
            return {"success": False, "msg": f"root not remove out of system !?@#@$)(**&*&^%&(()^&%^$#$#$$^^&^*^"}

        if _system_user.banks:
            return {"success": False, "msg": "item is use banks in database"}
        try:
            db.delete(_system_user)
            db.commit()
            return {"success": True, "msg": "item is remove"}
        except Exception as e:
            return {"success": False, "msg": str(e)}

    else:
        return {"success": False, "msg": "item not found"}


@router_systems_user.get("/datatable")
async def path_systems_user_get_datatable(
    req_para: Request,
    user=Depends(get_current_user),
    db: Session = Depends(create_session),
):
    params = dict(req_para.query_params)
    select_columns = set()
    for k in params:
        # print(f"{k}:{params[k]}")
        match = re.search(r"^columns\[.*\]\[data\]", k)
        if match:
            select_columns.add(f"{params[k]}")
    # print(select_columns)
    order_by_col = params["order[0][column]"]
    order_by_column = params.get(f"columns[{order_by_col}][data]")
    order_dir = params["order[0][dir]"]

    limit = params["length"]
    skip = params["start"]
    condition = ""
    search = params["search[value]"]

    _table = System_User
    _order_columns = _table.id
    if order_by_column:
        _order_columns = getattr(_table, order_by_column, _table.id)

    print(f"order_by_column : {_order_columns}")
    rows = []
    condition = True
    if search:
        condition = or_(
            _table.id.like(f"%{search}%"),
            _table.username.like(f"%{search}%"),
        )
    print_success(condition)
    _order_by = _order_columns.asc() if order_dir == "asc" else _order_columns.desc()

    # ? ----------------------- select ---------------------------------------!SECTION
    sql = select(_table)
    recordsTotal = db.exec(select([func.count()]).select_from(sql)).one()
    if search:
        _sql = sql.where(condition)
        recordsFiltered = db.exec(select([func.count()]).select_from(_sql)).one()
    else:
        recordsFiltered = recordsTotal

    rows = db.exec(sql.where(condition).order_by(_order_by).offset(skip).limit(limit)).all()

    return {"draw": params["draw"], "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data": rows}


# ****************************************************************************************************************************************

router_banks = APIRouter(prefix="/api/banks", tags=["Bank"])


@router_banks.get("/")
async def path_bank_get(id: int, user=Depends(get_current_user), db: Session = Depends(create_session)):
    _item: Bank = db.exec(select(Bank).where(Bank.id == id)).one_or_none()
    if _item:
        _item.API_KEY = "API_KEY"
        _item.API_SECRET = "API_SECRET"
        return _item
    else:
        return {"success": False, "msg": "item not found"}


@router_banks.post("/")
async def path_banks_post(
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
    bank_type: str = Form(...),
    name: str = Form(...),
    API_KEY: str = Form(...),
    BILLER_ID: str = Form(...),
    API_SECRET: str = Form(...),
    REF3: str = Form(...),
    scb_authorize: str = Form(default=None),
    scbGenerateAccessToken: str = Form(default=None),
    scbQRCodeAPI: str = Form(default=None),
    scbCheckPaySuccess: str = Form(default=None),
    remark: str = Form(...),
    id: int = Form(default=None),
    image_upload: UploadFile = File(None),
    logo_enable: str = Form(...),
):
    try:
        if id:
            _bank: Bank = db.exec(select(Bank).where(Bank.id == id)).one_or_none()
            _bank_name: Bank = db.exec(select(Bank).where(Bank.name == name)).one_or_none()
            if _bank_name:
                if _bank.id != _bank_name.id:
                    return {"success": False, "msg": "name already in bank other"}
        else:
            _bank: Bank = db.exec(select(Bank).where(Bank.name == name)).one_or_none()
            if _bank:
                return {"success": False, "msg": "name already in bank"}
            _bank = Bank()
            _bank.create_by = user.username
            _bank.createDate = time_now()
            _bank.system_user_id = user.id

        _bank.bank_type = bank_type
        _bank.name = name
        if API_KEY != "API_KEY":
            _bank.API_KEY = API_KEY
        if API_SECRET != "API_SECRET":
            _bank.API_SECRET = API_SECRET
        _bank.remark = remark
        _bank.REF3 = REF3
        _bank.BILLER_ID = BILLER_ID

        _bank.logo_enable = True if logo_enable == "true" else False

        if scb_authorize:
            _bank.scb_authorize = scb_authorize
        else:
            _bank.scb_authorize = ""

        if scbGenerateAccessToken:
            _bank.scbGenerateAccessToken = scbGenerateAccessToken
        else:
            _bank.scbGenerateAccessToken = ""
        if scbQRCodeAPI:
            _bank.scbQRCodeAPI = scbQRCodeAPI
        else:
            _bank.scbQRCodeAPI = ""
        if scbCheckPaySuccess:
            _bank.scbCheckPaySuccess = scbCheckPaySuccess
        else:
            _bank.scbCheckPaySuccess = ""

        if not id:
            db.add(_bank)
        db.commit()
        db.refresh(_bank)
    except Exception as e:
        print_error(e)
        return {"success": False, "msg": str(e)}

    if image_upload:
        image_content = await image_upload.read()
        image_upload = Image.open(BytesIO(image_content))

        if image_upload.format == "PNG":
            image_upload = image_upload.convert("RGB")
        try:
            _path = f"/static/image/bank/{_bank.id}.jpg"
            image_upload.save(f"{DIR_PATH}{_path}")
            _bank.pictureUrl = _path + f"?time_stamp={time.gmtime()}"
            db.commit()

        except Exception as e:
            print_error(e)

    return {"success": True, "msg": "successfully"}


@router_banks.delete("/{id}")
async def path_banks_delete(id: int, user=Depends(get_current_user), db: Session = Depends(create_session)):
    _bank: Bank = db.exec(select(Bank).where(Bank.id == id)).one_or_none()

    if _bank:
        sql = select(Device_Qr).where(Device_Qr.bank_id == _bank.id)
        devices_count = db.exec(select([func.count()]).select_from(sql)).one()
        if devices_count:
            return {"success": False, "msg": f"bank is connected to device: {devices_count} Unit"}

        try:
            db.delete(_bank)
            db.commit()
            return {"success": True, "msg": "item is remove"}
        except Exception as e:
            return {"success": False, "msg": str(e)}

    else:
        return {"success": False, "msg": "item not found"}


# ****************************************************************************************************************************************
router_devices = APIRouter(prefix="/api/devices", tags=["devices"])


@router_devices.get("/{id}")
async def path_devices_get(id: int, user=Depends(get_current_user), db: Session = Depends(create_session)):
    _device: Device_Qr = db.exec(select(Device_Qr).where(Device_Qr.id == id)).one_or_none()
    if _device:
        return _device
    else:
        return {"success": False, "msg": "item not found"}


@router_devices.post("/")
async def path_devices_post(
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
    name: str = Form(...),
    sn: str = Form(...),
    remark: str = Form(...),
    REF2: str = Form(...),
    MERCHANT_ID: str = Form(...),
    status: str = Form(...),
    type: str = Form(default=None),
    profile: str = Form(default=""),
    bank_id: int = Form(default=None),
    id: int = Form(default=None),
):
    print_success(bank_id)
    if bank_id:
        _bank: Bank = db.exec(select(Bank).where(Bank.id == bank_id)).one_or_none()
    else:
        _bank: Bank = db.exec(select(Bank).where(Bank.system_user_id == user.id)).first()

    if not _bank:
        return {"success": False, "msg": "bank is not already in database"}

    _bank: Bank = _bank

    print_success(id)
    try:
        if id:
            _device: Device_Qr = db.exec(select(Device_Qr).where(Device_Qr.id == id)).one_or_none()
            _device_name: Device_Qr = db.exec(select(Device_Qr).where(Device_Qr.name == name, Device_Qr.bank_id == bank_id)).one_or_none()
            if _device_name:
                if _device.id != _device_name.id:
                    return {"success": False, "msg": "name already in device list"}
        else:
            _device = db.exec(select(Device_Qr).where(Device_Qr.name == name)).one_or_none()
            if _device:
                return {"success": False, "msg": "name already in device"}
            _device = Device_Qr()
            _device.create_by = user.username
            _device.createDate = time_now()
            _device.bank_id = _bank.id

        _device.name = name
        _device.sn = sn
        _device.profile = profile
        _device.MERCHANT_ID = MERCHANT_ID
        if remark:
            _device.remark = remark

        if REF2:
            _device.REF2 = REF2

        if status:
            _device.status = status
        if type:
            _device.type = type

        if not id:
            db.add(_device)
        db.commit()
        db.refresh(_device)
    except Exception as e:
        print_error(e)
        return {"success": False, "msg": str(e)}

    return {"success": True, "msg": "successfully"}


@router_devices.delete("/{id}")
async def path_devices_delete(id: int, user=Depends(get_current_user), db: Session = Depends(create_session)):
    _device: Device_Qr = db.exec(select(Device_Qr).where(Device_Qr.id == id)).one_or_none()
    if _device:
        try:
            db.delete(_device)
            db.commit()
            return {"success": True, "msg": "item is remove"}
        except Exception as e:
            return {"success": False, "msg": str(e)}

    else:
        return {"success": False, "msg": "item not found"}


# ****************************************************************************************************************************************
router_qr_code_payment = APIRouter(prefix="/api/qr_code_payment")


@router_qr_code_payment.get("/info/{id}")
async def path_qr_code_payment_get(id: int, user=Depends(get_current_user), db: Session = Depends(create_session)):
    qr_code_payment: Qr_Code_Pay = db.exec(select(Qr_Code_Pay).where(Qr_Code_Pay.id == id)).one_or_none()
    if qr_code_payment:
        return qr_code_payment
    else:
        return {"success": False, "msg": "item not found"}


@router_qr_code_payment.get("/datatable")
async def path_qr_code_pay_get_datatable(
    req_para: Request,
    date_range: str = None,
    bank_name: str = None,
    user=Depends(get_current_user),
    db: Session = Depends(create_session),
):
    try:
        d_start, d_end = date_range.split(" - ")
        d_start = d_start.replace("/", "-")
        d_end = d_end.replace("/", "-")

    except ValueError as e:
        return {"success": False, "msg": str(e)}

    _table = Qr_Code_Pay

    params = dict(req_para.query_params)
    select_columns = set()
    for k in params:
        # print(f"{k}:{params[k]}")
        match = re.search(r"^columns\[.*\]\[data\]", k)
        if match:
            select_columns.add(f"{params[k]}")
    # print(select_columns)
    order_by_col = params["order[0][column]"]
    order_by_column = params.get(f"columns[{order_by_col}][data]")
    order_dir = params["order[0][dir]"]

    limit = params["length"]
    skip = params["start"]
    condition = ""
    search = params["search[value]"]

    _order_columns = _table.id
    if order_by_column:
        _order_columns = getattr(_table, order_by_column, _table.id)

    print(f"order_by_column : {_order_columns}")
    rows = []
    condition = True

    if search:
        try:
            s_amount = int(search)
            condition = or_(
                _table.amount == f"{s_amount}",
            )
        except ValueError:
            pass
            condition = or_(
                _table.payerName.like(f"%{search}%"),
                _table.billPaymentRef1.like(f"%{search}%"),
                _table.billPaymentRef2.like(f"%{search}%"),
                _table.billPaymentRef3.like(f"%{search}%"),
                _table.amount.like(f"%{search}%"),
            )
    # print_success(condition)
    _order_by = _order_columns.asc() if order_dir == "asc" else _order_columns.desc()
    # ? ----------------------- select ---------------------------------------!SECTION
    sql = select(_table, Device_Qr).where(_table.createDate.between(d_start, d_end))
    sql = sql.outerjoin(Qr_Code, (_table.qr_code_id == Qr_Code.id))
    sql = sql.outerjoin(Device_Qr, (Qr_Code.device_qr_id == Device_Qr.id))
    sql = sql.join(Bank, (_table.billPaymentRef3 == Bank.REF3))
    sql = sql.where(Bank.name == bank_name)

    recordsTotal = db.exec(select([func.count()]).select_from(sql)).one()

    if search:
        _sql = sql.where(condition)
        recordsFiltered = db.exec(select([func.count()]).select_from(_sql)).one()
    else:
        recordsFiltered = recordsTotal

    _sql = sql.where(condition).order_by(_order_by).offset(skip).limit(limit)
    rows = db.exec(_sql).all()
    # print(rows)

    return {"draw": params["draw"], "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data": rows}


# ****************************************************************************************************************************************


# ****************************************************************************************************************************************
router_qr_code_generator = APIRouter(prefix="/api/router_qr_code_generator")


@router_qr_code_generator.get("/datatable")
async def path_qr_code_generator_get_datatable(
    req_para: Request,
    date_range: str = None,
    bank_name: str = None,
    user=Depends(get_current_user),
    db: Session = Depends(create_session),
):
    try:
        d_start, d_end = date_range.split(" - ")
        d_start = d_start.replace("/", "-")
        d_end = d_end.replace("/", "-")

    except ValueError as e:
        return {"success": False, "msg": str(e)}

    _table = Qr_Code

    params = dict(req_para.query_params)
    select_columns = set()
    for k in params:
        # print(f"{k}:{params[k]}")
        match = re.search(r"^columns\[.*\]\[data\]", k)
        if match:
            select_columns.add(f"{params[k]}")
    # print(select_columns)
    order_by_col = params["order[0][column]"]
    order_by_column = params.get(f"columns[{order_by_col}][data]")
    order_dir = params["order[0][dir]"]

    limit = params["length"]
    skip = params["start"]
    condition = ""
    search = params["search[value]"]

    _order_columns = _table.id
    if order_by_column:
        _order_columns = getattr(_table, order_by_column, _table.id)

    print(f"order_by_column : {_order_columns}")
    rows = []
    condition = True

    if search:
        try:
            s_amount = int(search)
            condition = or_(
                _table.amount == s_amount,
            )
        except ValueError:
            pass
            condition = or_(
                _table.REF1.like(f"%{search}%"),
                _table.REF2.like(f"%{search}%"),
                _table.REF3.like(f"%{search}%"),
            )
    # print_success(condition)
    _order_by = _order_columns.asc() if order_dir == "asc" else _order_columns.desc()
    # ? ----------------------- select ---------------------------------------!SECTION
    count_of_qr_pay = (
        select(
            [func.count(Qr_Code_Pay.id)],
        )
        .select_from(Qr_Code_Pay)
        .where(Qr_Code_Pay.qr_code_id == Qr_Code.id)
    ).label("count_of_qr_pay")

    sql = select(
        _table,
        Device_Qr,
        count_of_qr_pay,
    ).where(_table.createDate.between(d_start, d_end))
    # sql = sql.outerjoin(Qr_Code_Pay, (Qr_Code_Pay.qr_code_id == _table.id))
    sql = sql.join(Device_Qr, (Qr_Code.device_qr_id == Device_Qr.id))
    sql = sql.join(Bank, (Device_Qr.bank_id == Bank.id))
    sql = sql.where(Bank.name == bank_name)

    recordsTotal = db.exec(select([func.count()]).select_from(sql)).one()

    if search:
        _sql = sql.where(condition)
        recordsFiltered = db.exec(select([func.count()]).select_from(_sql)).one()
    else:
        recordsFiltered = recordsTotal

    _sql = sql.where(condition).order_by(_order_by).offset(skip).limit(limit)

    rows = db.exec(_sql).all()

    # rows = _rows
    # print(rows)

    return {"draw": params["draw"], "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data": rows}


# ****************************************************************************************************************************************
