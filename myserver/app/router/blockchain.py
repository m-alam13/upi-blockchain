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
from app.models.user_model import Kyc_User
from app.middleware.jwt import verify_access_token, create_access_token
from app.core.config import settings
from typing import Optional
from app.block import Blockchain
from fastapi.templating import Jinja2Templates
from datetime import datetime
import json
from app.models.block_model import Block



router = APIRouter(tags=["blockchain"])
templates = Jinja2Templates(directory="app/templates")

# Add timestamp formatter
templates.env.filters["datetimeformat"] = lambda ts: datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

@router.get("/transection_data")
async def store_block(request: Request, transection: str, db: Session = Depends(get_db)):
    try:
        transaction_data = verify_access_token(transection, settings.SERVER_TO_SERVER_SECRET_KEY)
        print(" Decoded transaction data:", transaction_data)

        blockchain = Blockchain(db)
        new_block = blockchain.add_block(transaction_data)

        #  Print block details in terminal
        print(" New block added:")
        print(f"Index         : {new_block.index}")
        print(f"Timestamp     : {datetime.fromtimestamp(new_block.timestamp)}")
        print(f"Previous Hash : {new_block.previous_hash}")
        print(f"Hash          : {new_block.hash}")
        print(f"Nonce         : {new_block.nonce}")
        print(f"Data          : {json.loads(new_block.data)}")

        # Serialize block
        block_dict = {
            "index": new_block.index,
            "timestamp": new_block.timestamp,
            "data": json.loads(new_block.data),
            "previous_hash": new_block.previous_hash,
            "nonce": new_block.nonce,
            "hash": new_block.hash,
        }

        return {
            "message": "Block added with full transaction details",
            "block": block_dict,
            "success": True
        }
    except Exception as e:
        print("Error storing block:", e)
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@router.get("/view_chain", response_class=HTMLResponse)
async def view_chain(request: Request, db: Session = Depends(get_db)):
    try:
        blocks = db.query(Block).order_by(Block.timestamp.desc()).all()

        block_list = []
        for b in blocks:
            try:
                data = json.loads(b.data)
            except Exception:
                data = {}
            block_list.append({
                "index": b.index,
                "timestamp": b.timestamp,
                "data": data,
                "previous_hash": b.previous_hash,
                "nonce": b.nonce,
                "hash": b.hash
            })

        return templates.TemplateResponse("view_blockchain.html", {
            "request": request,
            "blocks": block_list,
            "length": len(block_list)
        })

    except Exception as e:
        return HTMLResponse(content=f"Error loading blockchain: {str(e)}", status_code=500)

# Example transaction data
#{'transaction_id': 'txn_2025051914433655d5', 'payer_uupi': '1747665536501665', 'payee_uupi': '1747665736868195', 'payer_vpa': '1747665536501665@wallet', 'payee_vpa': '1747665736868195@wallet', 'amount': 100.0, 'payer_account': '', 'payer_ifsc': 'WALLET', 'payee_account': 'wallet-1747665736868195@wallet', 'payee_ifsc': 'WALLET', 'exp': 1747666416}