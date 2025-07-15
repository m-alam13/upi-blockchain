import time
import hashlib
import json
import base64
import os
from sqlalchemy.orm import Session
from app.models.block_model import Block
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256


class Blockchain:
    def __init__(self, db: Session, difficulty: int = 4):
        self.db = db
        self.difficulty = difficulty

    def calculate_hash(self, index, previous_hash, timestamp, json_data, nonce):
        block_string = f"{index}{previous_hash}{timestamp}{json_data}{nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def get_block_string(self, index, previous_hash, timestamp, json_data, nonce):
        """Return the full string used for both hashing and signing"""
        return f"{index}{previous_hash}{timestamp}{json_data}{nonce}"

    def sign_block_data(self, block_string: str) -> str:
        """Sign the block string and return base64 encoded signature"""
        key_path = os.path.join("app", "keys", "private_key.pem")
        with open(key_path, "rb") as f:
            key = RSA.import_key(f.read())

        h = SHA256.new(block_string.encode())
        signature = pkcs1_15.new(key).sign(h)
        return base64.b64encode(signature).decode()

    def mine_block(self, index, previous_hash, timestamp, json_data):
        nonce = 0
        while True:
            block_string = self.get_block_string(index, previous_hash, timestamp, json_data, nonce)
            hash_result = hashlib.sha256(block_string.encode()).hexdigest()
            if hash_result.startswith('0' * self.difficulty):
                return nonce, hash_result
            nonce += 1

    def get_unique_timestamp(self) -> float:
        last_block = self.get_latest_block()
        new_time = time.time()
        while last_block and round(float(last_block.timestamp), 6) == round(new_time, 6):
            print(f"⏱ Waiting: Detected duplicate timestamp {new_time}, retrying...")
            time.sleep(0.001)
            new_time = time.time()
        return new_time

    def create_block(self, index, data: dict, previous_hash: str) -> Block:
        timestamp = self.get_unique_timestamp()
        data["formatted_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

        json_data = json.dumps(data, sort_keys=True)  #  Consistent sorting

        nonce, hash_result = self.mine_block(index, previous_hash, timestamp, json_data)
        block_string = self.get_block_string(index, previous_hash, timestamp, json_data, nonce)
        signature = self.sign_block_data(block_string)

        block = Block(
            index=index,
            timestamp=timestamp,
            data=json_data,
            previous_hash=previous_hash,
            nonce=nonce,
            hash=hash_result,
            signature=signature
        )
        return block

    def get_latest_block(self) -> Block:
        return self.db.query(Block).order_by(Block.index.desc()).first()

    def initialize_blockchain(self, first_transaction_data: dict):
        if self.db.query(Block).count() == 0:
            genesis_block = self.create_block(index=0, data=first_transaction_data, previous_hash="0")
            self.db.add(genesis_block)
            self.db.commit()
            self.db.refresh(genesis_block)
            print(" Genesis block created with first transaction data")

    def add_block(self, data: dict) -> Block:
        if self.db.query(Block).count() == 0:
            self.initialize_blockchain(first_transaction_data=data)
            return self.get_latest_block()

        last_block = self.get_latest_block()
        new_block = self.create_block(index=last_block.index + 1, data=data, previous_hash=last_block.hash)

        self.db.add(new_block)
        self.db.commit()
        self.db.refresh(new_block)

        print(f" Block #{new_block.index} added with hash {new_block.hash} at timestamp {new_block.timestamp}")
        return new_block

    def get_chain_descending(self):
        return self.db.query(Block).order_by(Block.index.desc()).all()
