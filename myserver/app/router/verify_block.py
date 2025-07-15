from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.block_model import Block
from app.core.db import get_db
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64
import json
import os
from fastapi import Query

router = APIRouter(tags=["signature-verification"])

def reconstruct_block_string(block: Block) -> str:
    """
    Recreate the exact string that was signed using the original block components.
    This must match the format used during signing in Blockchain class.
    """
    try:
        data_dict = json.loads(block.data)
        sorted_json_data = json.dumps(data_dict, sort_keys=True)
    except Exception as e:
        raise ValueError(f"Failed to parse block data (index={block.index}): {e}")

    return f"{block.index}{block.previous_hash}{block.timestamp}{sorted_json_data}{block.nonce}"


@router.get("/verify-block")
def verify_block_by_transaction_id(transaction_id: str = Query(...), db: Session = Depends(get_db)):
    blocks = db.query(Block).all()

    # Try to find block by matching the field inside the JSON data
    target_block = None
    for block in blocks:
        try:
            data_dict = json.loads(block.data)
            if data_dict.get("transaction_id") == transaction_id:
                target_block = block
                break
        except json.JSONDecodeError:
            continue
    print(target_block)
    if not target_block:
        return {"status": "error", "message": "Block with that transaction_id not found"}

    try:
        key_path = os.path.join("app", "keys", "public_key.pem")
        with open(key_path, "rb") as f:
            public_key = RSA.import_key(f.read())

        block_string = reconstruct_block_string(target_block)
        hash_obj = SHA256.new(block_string.encode())
        signature_bytes = base64.b64decode(target_block.signature)
        pkcs1_15.new(public_key).verify(hash_obj, signature_bytes)

        return {
            "transaction_id": transaction_id,
            "valid_signature": True,
            "verified_hash": hash_obj.hexdigest()
        }

    except (ValueError, TypeError) as e:
        return {
            "transaction_id": transaction_id,
            "valid_signature": False,
            "error": f"Verification failed: {str(e)}"
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "message": "🔑 public_key.pem not found at app/keys/"
        }

    except Exception as e:
        return {
            "transaction_id": transaction_id,
            "valid_signature": False,
            "error": f"Unexpected error: {str(e)}"
        }
