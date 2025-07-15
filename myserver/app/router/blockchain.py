from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.core.db import get_db
from app.models.block_model import Block
from app.middleware.jwt import verify_access_token
from app.core.config import settings
from app.block import Blockchain

router = APIRouter(tags=["blockchain"])
templates = Jinja2Templates(directory="app/templates")

# Custom Jinja filter for consistent datetime formatting
templates.env.filters["datetimeformat"] = lambda ts: datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")

def process_block_addition(transaction_data: dict, db_session: Session):
    now = datetime.now()
    transaction_data["formatted_timestamp"] = now.strftime("%Y-%m-%d %H:%M:%S")
    
    blockchain = Blockchain(db_session)
    new_block = blockchain.add_block(transaction_data)
    
    # Optional: log or save result if needed
    # with open("blockchain_log.txt", "a") as f:
    #     f.write(json.dumps({
    #         "index": new_block.index,
    #         "timestamp": new_block.timestamp,
    #         "data": json.loads(new_block.data),
    #         "previous_hash": new_block.previous_hash,
    #         "nonce": new_block.nonce,
    #         "hash": new_block.hash,
    #         "signature": new_block.signature
    #     }, indent=2) + "\n")

@router.get("/transection_data")
async def store_block(
    request: Request,
    transection: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Accepts a JWT transaction token and schedules block creation in the background.
    """
    try:
        transaction_data = verify_access_token(transection, settings.SERVER_TO_SERVER_SECRET_KEY)
        transaction_data.pop("exp", None)

        # Add background task to process block
        background_tasks.add_task(process_block_addition, transaction_data, db)

        return {
            "message": "Block is being added in the background...",
            "success": True
        }

    except Exception as e:
        print("❌ Error starting background task:", e)
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
        
# @router.get("/transection_data")
# async def store_block(request: Request, transection: str, db: Session = Depends(get_db)):
#     """
#     Accepts a JWT transaction token, decodes it, formats the timestamp,
#     and adds a new block to the blockchain.
#     """
#     try:
#         # Decode and extract transaction details
#         transaction_data = verify_access_token(transection, settings.SERVER_TO_SERVER_SECRET_KEY)
#         transaction_data.pop("exp", None)  # Remove expiry if present

#         # Add human-readable timestamp
#         now = datetime.now()
#         transaction_data["formatted_timestamp"] = now.strftime("%Y-%m-%d %H:%M:%S")

#         # Add block to the chain
#         blockchain = Blockchain(db)
#         new_block = blockchain.add_block(transaction_data)

#         return {
#             "message": " Block added with full transaction details",
#             "block": {
#                 "index": new_block.index,
#                 "timestamp": new_block.timestamp,
#                 "data": json.loads(new_block.data),
#                 "previous_hash": new_block.previous_hash,
#                 "nonce": new_block.nonce,
#                 "hash": new_block.hash,
#                 "signature": new_block.signature
#             },
#             "success": True
#         }

#     except Exception as e:
#         print("❌ Error storing block:", e)
#         return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@router.get("/view_chain", response_class=HTMLResponse)
async def view_chain(request: Request, db: Session = Depends(get_db)):
    """
    Fetches all blocks from the blockchain and renders them using a Jinja2 HTML template.
    """
    try:
        blocks = db.query(Block).order_by(Block.index.desc()).all()
        block_list = []

        for block in blocks:
            try:
                data = json.loads(block.data) if block.data else {}
            except json.JSONDecodeError:
                data = {}

            # Use the transaction timestamp if available
            display_time = data.get("formatted_timestamp", block.timestamp)

            block_list.append({
                "index": block.index,
                "timestamp": display_time,
                "data": data,
                "previous_hash": block.previous_hash,
                "nonce": block.nonce,
                "hash": block.hash,
                "signature": block.signature or "N/A"
            })

        return templates.TemplateResponse("view_blockchain.html", {
            "request": request,
            "blocks": block_list,
            "length": len(block_list)
        })

    except Exception as e:
        print("❌ Error fetching blockchain:", e)
        return HTMLResponse(content=f"<h2>Error: {str(e)}</h2>", status_code=500)


    except Exception as e:
        return HTMLResponse(content=f"❌ Error loading blockchain: {str(e)}", status_code=500)
