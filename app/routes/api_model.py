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
from app.core.database import Project, System_User, Device, create_session

from ..stdio import *

DIR_PATH = config.DIR_PATH

# ****************************************************************************************************************************************
router_api = APIRouter(prefix="/api_model")


@router_api.get("/project/{id}")
async def path_get_project(
    id: int,
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
):
    _project = db.exec(select(Project).where(Project.id == id)).one_or_none()
    if not _project:
        return {"success": False, "msg": "item is not already in database"}
    # if _project.system_user_id != user.id:
    #     return {"success": False, "msg": "item is not yours"}

    return {"success": True, "msg": "successfully", "data": _project, "project_owner": _project.system_user}


@router_api.post("/project/")
async def path_post_project(
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
    project_owner: str = Form(...),
    project_name: str = Form(...),
    project_address: str = Form(...),
    project_staff: str = Form(...),
    project_phone: str = Form(...),
    image_upload: UploadFile = File(None),
    id: int = Form(default=None),
):
    if id:
        _project = db.exec(select(Project).where(Project.id == id)).one_or_none()

        if not _project:
            return {"success": False, "msg": "item is not already in database"}

        if project_name != _project.name:
            _p = db.exec(select(Project).where(Project.id != id, Project.name == project_name)).one_or_none()
            if _p:
                return {"success": False, "msg": f"project name : ({project_name}) is already in use"}

        _project.name = project_name
        _project.address = project_address
        _project.staff = project_staff
        _project.phone = project_phone
        db.commit()
        db.refresh(_project)
        print_warning(_project)
    else:
        _project = db.exec(select(Project).where(Project.name == project_name)).one_or_none()
        if _project:
            return {"success": False, "msg": "item is already in database(รายการ ซ้ำ)"}

        if project_owner == "ME" or project_owner == "":
            owner_id = user.id
        else:
            if user.username != "root":
                return {"success": False, "msg": "user is not root"}
            else:
                owner: System_User = db.exec(select(System_User).where(System_User.username == project_owner)).one_or_none()
                if not owner:
                    return {"success": False, "msg": "user is not in database"}
                owner_id = owner.id
        _project = Project(
            name=project_name,
            createDate=time_now(),
            address=project_address,
            staff=project_staff,
            phone=project_phone,
            system_user_id=owner_id,
        )
        print_success(_project)
        db.add(_project)
        db.commit()
        db.refresh(_project)

    if image_upload:
        image_content = await image_upload.read()
        image_upload = Image.open(BytesIO(image_content))
        print(image_upload)

        if image_upload.format == "PNG":
            image_upload = image_upload.convert("RGB")
        try:
            _path = f"/static/image/project/{_project.id}.jpg"
            print(_path)
            image_upload.save(f"{DIR_PATH}{_path}")
            _project.pictureUrl = _path + f"?time_stamp={time.gmtime()}"
            db.commit()

        except Exception as e:
            print_error(e)

    return {"success": True, "msg": "successfully"}


@router_api.delete("/project/{id}")
async def path_delete_project(
    id: int,
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
):
    _project = db.exec(select(Project).where(Project.id == id)).one_or_none()
    if not _project:
        return {"success": False, "msg": "item is not already in database"}
    if user.username != "root":
        if _project.system_user_id != user.id:
            return {"success": False, "msg": "item is not yours"}
    try:
        db.delete(_project)
        db.commit()
    except Exception as e:
        print_error(e)
        return {"success": False, "msg": str(e)}
    return {"success": True, "msg": "successfully"}


# ****************************************************************************************************************************************


@router_api.get("/device/{id}")
async def path_get_device(
    id: int,
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
):
    _device: Device = db.exec(select(Device).where(Device.id == id)).one_or_none()
    if not _device:
        return {"success": False, "msg": "item is not already in database"}
    # if _project.system_user_id != user.id:
    #     return {"success": False, "msg": "item is not yours"}
    _project: Project = db.exec(select(Project).where(Project.id == _device.project_id)).one_or_none()

    return {"success": True, "msg": "successfully", "data": _device, "device_project_name": _project.name}


@router_api.post("/device/")
async def path_post_project(
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
    device_name: str = Form(...),
    device_sn: str = Form(...),
    device_project_name: str = Form(...),
    id: int = Form(default=None),
):
    if id:
        _device: Device = db.exec(select(Device).where(Device.id == id)).one_or_none()

        if not _device:
            return {"success": False, "msg": "item is not already in database"}

        if device_name != _device.name:
            _d = db.exec(select(Device).where(Device.id != id, Device.name == device_name)).one_or_none()
            if _d:
                return {"success": False, "msg": f"Device name : ({device_name}) is already in use"}

        if device_sn != _device.sn:
            _d = db.exec(select(Device).where(Device.id != id, Device.sn == device_sn)).one_or_none()
            if _d:
                return {"success": False, "msg": f"serial number  : ({device_sn}) is already in use"}

        _device.name = device_name
        _device.sn = device_sn

        db.commit()
        db.refresh(_device)
        print_warning(_device)
    else:
        _device = db.exec(select(Device).where(Device.name == device_name)).one_or_none()
        if _device:
            return {"success": False, "msg": "item is already in database(รายการ ซ้ำ)"}

        _device = db.exec(select(Device).where(Device.sn == device_sn)).one_or_none()
        if _device:
            return {"success": False, "msg": "serial number is already in database(รายการ ซ้ำ)"}

        _project: Project = db.exec(select(Project).where(Project.name == device_project_name)).one_or_none()
        if not _project:
            return {"success": False, "msg": "Project is not in database"}
        else:
            if user.username != "root":
                if _project.system_user_id != user.id:
                    return {"success": False, "msg": "Project is already in user permitted"}

        _device = Device(
            name=device_name,
            sn=device_sn,
            createDate=time_now(),
            create_by=user.username,
            project_id=_project.id,
        )
        print_success(_device)
        db.add(_device)
        db.commit()
        db.refresh(_device)

    return {"success": True, "msg": "successfully"}


@router_api.delete("/device/{id}")
async def path_delete_device(
    id: int,
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
):
    _device = db.exec(select(Device).where(Device.id == id)).one_or_none()
    if not _device:
        return {"success": False, "msg": "item is not already in database"}
    if user.username != "root":
        _p = db.exec(select(Project).where(Project.id == _device.project_id)).one_or_none()
        if _p.system_user_id != user.id:
            return {"success": False, "msg": "item is not yours"}
    try:
        db.delete(_device)
        db.commit()
    except Exception as e:
        print_error(e)
        return {"success": False, "msg": str(e)}
    return {"success": True, "msg": "successfully"}
