import re

from datetime import datetime

def generate_vpa(name: str, bank_name: str) -> str:
    """Generate a Virtual Payment Address (VPA) from user name and bank name"""
    clean_name = re.sub(r'[^a-z0-9]', '', name.lower())
    clean_bank = re.sub(r'[^a-z0-9]', '', bank_name.lower())
    return f"{clean_name}@{clean_bank}"



def generate_timestamped_transaction_id():
    return f"txn_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4]}"
