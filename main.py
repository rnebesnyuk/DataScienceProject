import asyncio
import uvicorn
from typing import Callable

from fastapi import FastAPI, HTTPException, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from src.database.db import get_db
from src.routes import auth, users, admin
from src.routes.auth import blacklisted_tokens
from src.utils.utils import periodic_clean_blacklist
from fastapi.templating import Jinja2Templates

app = FastAPI(swagger_ui_parameters={"operationsSorter": "method"}, title="Parking Application")
templates = Jinja2Templates(directory="src/services/templates")

# CORS configuration
origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.middleware("http")
async def block_blacklisted_tokens(request: Request, call_next: Callable):
    authorization_header = request.headers.get("Authorization")
    if authorization_header is None:
        response = await call_next(request)
        return response
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Token is invalid"})
    access_token = parts[1]
    if access_token in blacklisted_tokens:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Token is blacklisted"})

    response = await call_next(request)
    return response

@app.on_event("startup")
async def startup():
    asyncio.create_task(periodic_clean_blacklist(60))

@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)