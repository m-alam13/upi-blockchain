from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from urllib.parse import urlencode
import base64
from fastapi import Form
from app.core.db import get_db
from sqlalchemy.orm import Session
import time
import random
import os
from pathlib import Path
from app.models.user_model import User
from app.middleware.jwt import verify_access_token, create_access_token
from app.core.config import settings
from typing import Optional



router = APIRouter(tags=["blockchain"])
@router.get("/transection_data")
async def get_transactions_details(
    request: Request,

    transection: str
):
    try:
        verify_token = verify_access_token(
            transection, settings.SERVER_TO_SERVER_SECRET_KEY
        )
        print("Decoded Token:", verify_token)
        return {
            "message": "hello",
            "success": True,
            "data": verify_token
        }
    except Exception as e:
        print("Token Verification Failed:", e)
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
