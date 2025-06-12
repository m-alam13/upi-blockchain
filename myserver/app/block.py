import time
import hashlib
import json
from sqlalchemy.orm import Session
from app.models.block_model import Block

class Blockchain:
    def __init__(self, db: Session, difficulty: int = 4):
        self.db = db
        self.difficulty = difficulty

    def calculate_hash(self, index, previous_hash, timestamp, data, nonce):
        block_string = f"{index}{previous_hash}{timestamp}{data}{nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def get_unique_timestamp(self) -> float:
        """Ensures each timestamp is unique by comparing with the last block."""
        last_block = self.get_latest_block()
        new_time = time.time()
        while last_block and round(float(last_block.timestamp), 6) == round(new_time, 6):
            print(f"⏱ Waiting: Detected duplicate timestamp {new_time}, retrying...")
            time.sleep(0.001)
            new_time = time.time()
        return new_time

    def mine_block(self, index, previous_hash, data):
        nonce = 0
        while True:
            timestamp = self.get_unique_timestamp()
            hash_result = self.calculate_hash(index, previous_hash, timestamp, json.dumps(data), nonce)
            if hash_result.startswith('0' * self.difficulty):
                return timestamp, nonce, hash_result
            nonce += 1

    def create_block(self, index, data: dict, previous_hash: str) -> Block:
        timestamp, nonce, hash_result = self.mine_block(index, previous_hash, data)
        return Block(
            index=index,
            timestamp=timestamp,
            data=json.dumps(data),
            previous_hash=previous_hash,
            nonce=nonce,
            hash=hash_result
        )

    def get_latest_block(self) -> Block:
        return self.db.query(Block).order_by(Block.index.desc()).first()

    def initialize_blockchain(self, first_transaction_data: dict):
        if self.db.query(Block).count() == 0:
            genesis_block = self.create_block(index=0, data=first_transaction_data, previous_hash="0")
            self.db.add(genesis_block)
            self.db.commit()
            print("Genesis block created with first transaction data")

    def add_block(self, data: dict) -> Block:
        if self.db.query(Block).count() == 0:
            self.initialize_blockchain(first_transaction_data=data)
            return self.get_latest_block()

        last_block = self.get_latest_block()
        new_block = self.create_block(index=last_block.index + 1, data=data, previous_hash=last_block.hash)
        self.db.add(new_block)
        self.db.commit()
        print(f"Block #{new_block.index} added with hash {new_block.hash} at timestamp {new_block.timestamp}")
        return new_block

    def get_chain_descending(self):
        return self.db.query(Block).order_by(Block.index.desc()).all()
