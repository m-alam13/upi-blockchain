from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import HTMLResponse
from app.schemas import user_schema
from app.controllers import auth
from app.core.db import get_db
from sqlalchemy.orm import Session

router = APIRouter()

# Example route: User signup
@router.post("/signup", response_model=user_schema.Token )
async def signup(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    return await auth.signup(user, db)

@router.get("/signup", response_class=HTMLResponse)
async def getsignup(request: Request):
    # print(request)
    templates = request.app.state.templates 
    return templates.TemplateResponse("signup.html", {"request": request, "message": "Hello from FastAPI!"})
# You can add 

# Example route: User login
@router.post("/login", response_model=user_schema.Token)
async def login(response: Response, user: user_schema.UserLogin, db: Session = Depends(get_db)):
    # print(response_model)
    return await auth.login(response, user, db)


@router.get("/login", response_class=HTMLResponse)
async def getlogin(request: Request):
    print(request)
    templates = request.app.state.templates 
    return templates.TemplateResponse("login.html", {"request": request, "message": "Hello from FastAPI!"})
# You can add more user-related routes here...




