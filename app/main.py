# Python > 3.8
# Edit by Pksofttech for user
# ? main for set application
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, JSONResponse, RedirectResponse, HTMLResponse
from starlette.middleware.cors import CORSMiddleware

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
from starlette.exceptions import HTTPException

from fastapi.staticfiles import StaticFiles

from .stdio import *
import logging


from app.core import database
from app.core import auth
from app.routes import model_view, views, websocket

# root_logger = logging.getLogger()
# root_logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler("applog.log", "w", "utf-8")
# handler.setFormatter(logging.Formatter(f"%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s"))
# root_logger.addHandler(handler)

app = FastAPI()

from app.service import mqtt

mqtt.fast_mqtt.init_app(app)

app.mount("/static", StaticFiles(directory="./static"), name="static")
# app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

# Set all CORS enabled origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    print_success(f"Server Start Time : {time_now()}")
    await auth.create_systems_user()


@app.on_event("shutdown")
def shutdown_event():
    print_warning(f"Server shutdown Time : {time_now()}")


# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     start_time = time.time()
#     print("*************************************************")
#     response = await call_next(request)
#     process_time = time.time() - start_time
#     response.headers["X-Process-Time"] = str(process_time)

#     return response


app.include_router(auth.router)

app.include_router(model_view.router_systems_user)


app.include_router(websocket.router)

app.include_router(views.router_page)
# app.include_router(views.router_bup_payment)


@app.exception_handler(HTTPException)
async def app_exception_handler(request: Request, exception: HTTPException):
    url_str = str(request.url).split("/")[-1]
    print_error(url_str)
    if request.method == "GET":
        print_error(exception.detail)
        if exception.detail == "Not Found":
            if "." in url_str:
                return HTMLResponse(str(exception.detail), status_code=exception.status_code)
            return templates.TemplateResponse(
                "404.html",
                {
                    "request": {},
                },
            )
        return PlainTextResponse(str(exception.detail), status_code=exception.status_code)

    else:
        return JSONResponse(str(exception.detail), status_code=exception.status_code)
