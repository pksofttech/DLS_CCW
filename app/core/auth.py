from __future__ import annotations

from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Any, Optional, Union

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import PyJWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core import config
from app.core.database import engine, create_session, System_User
from ..stdio import *

print("Load authenticate module")


class Token(BaseModel):
    access_token: str
    token_type: str


OAUTH_PATH = "/oauth"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=OAUTH_PATH)
router = APIRouter()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(
    session: Session,
    username: Optional[str],
) -> System_User:
    statement = select(System_User).where(System_User.username == username)
    results = session.exec(statement).one_or_none()
    print_success(results)
    return results
    # return await db.query(System_User).filter(System_User.username == username).first()


def authenticate_user(
    db,
    username: str,
    password: str,
) -> Union[bool, System_User]:
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = None) -> bytes:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        config.API_SECRET_KEY,
        algorithm=config.API_ALGORITHM,
    )
    print(to_encode)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(create_session)) -> System_User:
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # print(token)
    try:
        payload = jwt.decode(
            token,
            config.API_SECRET_KEY,
            algorithms=[config.API_ALGORITHM],
        )
        username = payload.get("sub")

        if username is None:
            raise credentials_exception
        # token_data = TokenData(username=username)

    except PyJWTError:
        raise credentials_exception

    user = get_user(db, username=username)

    if user is None:
        raise credentials_exception
    return user


async def access_cookie_token(request: Request, token_name="Authorization", db: Session = Depends(create_session)):
    token = None
    user = None
    try:
        _cookie_str = request.headers.get("cookie")
        if _cookie_str:
            cookies = _cookie_str.split(";")
            for c in cookies:
                c = c.strip()
                # print(c)
                if c.startswith(f"{token_name}=bearer "):
                    token = c.split(" ")[1]
                    user = await get_current_user_token(token)
        if user:
            _system_user = db.exec(select(System_User).where(System_User.username == user)).one_or_none()
            return _system_user

        print_warning("Not Authorization")
    except Exception as e:
        print_warning(f"Exception : {e}")
    return None


async def get_current_user_token(token: str) -> str:
    # print(token)
    try:
        payload = jwt.decode(
            token,
            config.API_SECRET_KEY,
            algorithms=[config.API_ALGORITHM],
        )
        username = payload.get("sub")

    except PyJWTError:
        return None

    return username


@router.get("/login_session", tags=["OAuth"])
async def login_session(user=Depends(get_current_user)):
    return user


@router.get("/logout_session", tags=["OAuth"])
async def logout_session(user=Depends(get_current_user)):
    access_token_expires = timedelta(seconds=1)
    print(access_token_expires)
    access_token = create_access_token(
        data={"sub": user.username},  # type: ignore
        expires_delta=access_token_expires,
    )
    return access_token


@router.post(OAUTH_PATH, response_model=Token, tags=["OAuth"])
async def login_for_access_token(
    db=Depends(create_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, Any]:
    user = authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        seconds=config.API_ACCESS_TOKEN_EXPIRE_MINUTES,
        # seconds=10,
    )
    access_token = create_access_token(
        data={"sub": user.username},  # type: ignore
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}
