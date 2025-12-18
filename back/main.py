import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import database, generator, training, audio
from . import database_config
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MuGAN API", version="1.0.0")

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db_client():
    database_config.connect_to_mongo()
    print("[STARTUP] Connected to MongoDB - using 'raw_data' collection for database routes")

@app.on_event("shutdown")
def shutdown_db_client():
    database_config.close_mongo_connection()

app.include_router(database.router, prefix="/api", tags=["database"])
app.include_router(generator.router, prefix="/api", tags=["generator"])
app.include_router(audio.router, prefix="/api", tags=["audio"])
app.include_router(training.router, prefix="/api/training", tags=["training"])

@app.get("/")
async def root():
    print("Root endpoint called")
    return {"message": "MuGAN API is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    print("Health check")
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "8000"))
    api_reload = os.getenv("API_RELOAD", "True").lower() == "true"
    
    print(f"Starting MuGAN API server on {api_host}:{api_port}...")
    uvicorn.run(app, host=api_host, port=api_port, reload=api_reload)
