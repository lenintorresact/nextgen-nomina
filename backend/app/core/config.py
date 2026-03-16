import os
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Request, HTTPException, Depends
from functools import lru_cache

# Initialize Firebase Admin
# In production, credentials would be loaded from service account or environment
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

db = firestore.Client()

async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    id_token = auth_header.split(" ").pop()
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
