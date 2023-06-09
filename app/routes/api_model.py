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
from sqlmodel import Session, func, join, or_, select, delete, update

from app.core import config
from app.core.auth import access_cookie_token, get_current_user, get_password_hash

# from sqlalchemy import or_
# from sqlalchemy.orm import Session
from app.core.database import Log_pay, Project, System_User, Device, create_session
from app.service.mqtt import fast_mqtt

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
async def path_post_device(
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

        _device = Device(name=device_name, sn=device_sn, createDate=time_now(), create_by=user.username, project_id=_project.id, price_rates="20202020202060")
        print_success(_device)
        db.add(_device)
        db.commit()
        db.refresh(_device)

    return {"success": True, "msg": "successfully"}


@router_api.post("/device_set_config/")
async def path_post_device_set_config(
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
    id: int = Form(default=None),
    price_rate_01: int = Form(...),
    price_rate_02: int = Form(...),
    price_rate_03: int = Form(...),
    price_rate_04: int = Form(...),
    price_rate_05: int = Form(...),
    price_rate_06: int = Form(...),
    price_rate_07: int = Form(...),
):
    if id:
        _device: Device = db.exec(select(Device).where(Device.id == id)).one_or_none()

        if not _device:
            return {"success": False, "msg": "item is not already in database"}

        if price_rate_01 == 0 or price_rate_02 == 0 or price_rate_03 == 0 or price_rate_04 == 0:
            return {"success": False, "msg": "data is not available"}

        if price_rate_01 > 60 or price_rate_02 > 60 or price_rate_03 > 60 or price_rate_04 > 60:
            return {"success": False, "msg": "data is not available"}

        price_rates = (
            str(price_rate_01).zfill(2)
            + str(price_rate_02).zfill(2)
            + str(price_rate_03).zfill(2)
            + str(price_rate_04).zfill(2)
            + str(price_rate_05).zfill(2)
            + str(price_rate_06).zfill(2)
            + str(price_rate_07).zfill(3)
        )

        _device.price_rates = price_rates
        try:
            publish: str = f"/config/{_device.sn}"
            d = {
                "cmd": "fntime",
                "fn1": str(price_rate_01),
                "fn2": str(price_rate_02),
                "fn3": str(price_rate_03),
                "fn4": str(price_rate_04),
                "fn5": str(price_rate_05),
                "fn6": str(price_rate_06),
                "fn7": str(price_rate_07),
            }
            msg_json = json.dumps(d)
            print(publish)
            fast_mqtt.publish(publish, msg_json)
            db.commit()
            db.refresh(_device)
            print_warning(_device)
        except Exception as e:
            print_error(e)
            return {"success": False, "msg": e}
    else:
        return {"success": False, "msg": "Device is already in database"}

    return {"success": True, "msg": "successfully"}


@router_api.post("/device_set_active/")
async def path_post_device_set_active(
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
    id: int = Form(default=None),
    op01: str = Form(...),
    op02: str = Form(...),
    op03: str = Form(...),
    op04: str = Form(...),
    op05: str = Form(...),
):
    if id:
        _device: Device = db.exec(select(Device).where(Device.id == id)).one_or_none()

        if not _device:
            return {"success": False, "msg": "item is not already in database"}

        print(op01)
        try:
            op01 = "1" if op01 == "true" else "0"
            op02 = "1" if op02 == "true" else "0"
            op03 = "1" if op03 == "true" else "0"
            op04 = "1" if op04 == "true" else "0"
            op05 = "1" if op05 == "true" else "0"
            status = op01 + op02 + op03 + op04 + op05

            print(status)

            publish: str = f"/config/{_device.sn}"
            d = {
                "cmd": "setup",
                "machineActive": True if op01 == "1" else False,
                "multiMode": True if op02 == "1" else False,
                "bankAccept": True if op03 == "1" else False,
                "coinAccept": True if op04 == "1" else False,
                "qrAccept": True if op05 == "1" else False,
            }
            msg_json = json.dumps(d)
            print(publish)
            fast_mqtt.publish(publish, msg_json)
            _device.status = status
            db.commit()
            db.refresh(_device)
        except Exception as e:
            print_error(e)
            return {"success": False, "msg": e}
    else:
        return {"success": False, "msg": "Device is already in database"}

    return {"success": True, "msg": "successfully"}


@router_api.post("/device_reset_count/{id}")
async def path_device_reset_count(
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
        _device.count_pay = 0
        db.commit()
        sql = delete(Log_pay).where(Log_pay.device_id == _device.id)
        row = db.exec(sql)
        print(row)
        db.commit()
    except Exception as e:
        print_error(e)
        return {"success": False, "msg": str(e)}
    return {"success": True, "msg": "successfully"}


@router_api.post("/device_restart/{id}")
async def path_device_restart(
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
        publish: str = f"/config/{_device.sn}"
        d = {
            "cmd": "reset",
        }
        msg_json = json.dumps(d)
        print(publish)
        fast_mqtt.publish(publish, msg_json)
    except Exception as e:
        print_error(e)
        return {"success": False, "msg": str(e)}
    return {"success": True, "msg": "successfully to restart devices"}


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


# ****************************************************************************************************************************************


@router_api.post("/ota_getlist/")
async def path_post_ota_getlist(
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
):
    dir_path = "./static/ota"
    # list to store files
    ota_list = []

    # Iterate directory
    for path in os.listdir(dir_path):
        # check if current path is a file
        if os.path.isfile(os.path.join(dir_path, path)):
            tm = datetime.fromtimestamp(os.path.getmtime(os.path.join(dir_path, path)))
            ota_file = {"file_name": path, "timestamp": tm}
            ota_list.append(ota_file)

    return {"success": True, "msg": "successfully", "data": ota_list}


@router_api.post("/ota_upload_file/")
async def path_post_ota_upload_file(
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
    ota_file: UploadFile = File(...),
):
    dir_path = "./static/ota"
    # list to store files
    file_location = f"{dir_path}/{ota_file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(ota_file.file.read())
    return {"success": True, "msg": "successfully", "data": ota_file}


@router_api.post("/ota_remove_file/")
async def path_post_ota_ota_remove_file(
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
    file_name: str = Form(...),
):
    dir_path = "./static/ota"

    path = os.path.join(dir_path, file_name)
    os.remove(path)
    return {"success": True, "msg": "successfully"}


OTA_URL = os.getenv("OTA_URL")
print_success(f"OTA_URL : {OTA_URL}")


@router_api.post("/ota_upload_to_devices/")
async def path_post_ota_upload_to_devices(
    user: System_User = Depends(get_current_user),
    db: Session = Depends(create_session),
    file_ota: str = Form(...),
    devices: str = Form(...),
):
    devices_ota = devices.split(",")
    result = 0
    error = None
    for device_ota in devices_ota:
        if device_ota:
            _device = db.query(Device).where(Device.sn == device_ota).one_or_none()
            if _device:
                try:
                    publish: str = f"/ota/{device_ota}"
                    d = {
                        "ota": "on",
                        "ver": file_ota,
                        "url": f"{OTA_URL}{file_ota}",
                    }
                    msg_json = json.dumps(d)
                    print(publish)
                    fast_mqtt.publish(publish, msg_json)
                    result += 1
                except Exception as e:
                    print_error(e)
                    error = f"{device_ota} : {e}"
                    break
            else:
                error = f"{device_ota} : not found in device database !..."
                break

    if error:
        return {"success": False, "msg": error}

    return {"success": True, "msg": f"OTA MQTT device successfully ({result})"}
