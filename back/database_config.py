import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "mugan_project")

client = None
database = None

def connect_to_mongo():
    global client, database
    print(f"[DATABASE CONFIG] Connecting to MongoDB: {MONGODB_URL}")
    client = MongoClient(MONGODB_URL)
    database = client[MONGODB_DB_NAME]
    print(f"[DATABASE CONFIG] Connected to database: {MONGODB_DB_NAME}")
    
    collections = database.list_collection_names()
    print(f"[DATABASE CONFIG] Existing collections: {collections}")
    
    return database

def close_mongo_connection():
    global client
    if client:
        print("[DATABASE CONFIG] Closing MongoDB connection")
        client.close()

def get_database():
    return database
