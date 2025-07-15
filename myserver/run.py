from fastapi import FastAPI
# from app.routes import user_routes
from app.main import app
# import ngrok
import uvicorn


if __name__ == "__main__":
    
    
    # print(listner.url())
    try:
        uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True)
    finally:
        print("disconnecting....")
        
    #http://localhost:5000/view_chain
