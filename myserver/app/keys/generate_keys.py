from Crypto.PublicKey import RSA
import os

# Create directory if not exists
os.makedirs("app/keys", exist_ok=True)

# Generate key pair
key = RSA.generate(2048)

# Write private key
with open("app/keys/private_key.pem", "wb") as priv_file:
    priv_file.write(key.export_key())

# Write public key
with open("app/keys/public_key.pem", "wb") as pub_file:
    pub_file.write(key.publickey().export_key())

print(" RSA key pair saved in app/keys/")



