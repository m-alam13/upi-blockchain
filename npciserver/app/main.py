from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse, JSONResponse
# from app.controllers import user_controller
from app.core.db import Base, engine
from app.routes import auth_route, wallet_route, bank_route, transection_route
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", 'http://localhost:8000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)



# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates folder
templates = Jinja2Templates(directory="app/templates")

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == status.HTTP_302_FOUND:
        return RedirectResponse(url="/login")
    # Fallback: return default JSON error response manually
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )



# Include routes
app.include_router(auth_route.router)
app.include_router(wallet_route.router)
app.include_router(bank_route.router)
app.include_router(transection_route.router)
app.state.templates = templates  
# app.include_router(user_controller.router)

# Root route to show the index page
@app.get("/")
async def read_index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
