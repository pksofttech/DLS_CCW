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
from app.core.database import System_User, create_session

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
