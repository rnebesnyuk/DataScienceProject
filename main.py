import asyncio
import uvicorn

from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.routes import auth, users, admin
from src.routes.auth import blacklisted_tokens
from src.utils.utils import periodic_clean_blacklist


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs on startup
    task = asyncio.create_task(periodic_clean_blacklist(60))
    
    yield
    
    # This runs on shutdown
    task.cancel()


app = FastAPI(swagger_ui_parameters={"operationsSorter": "method"}, lifespan=lifespan, title="Parking Application")
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


@app.middleware("http")
async def block_blacklisted_tokens(request: Request, call_next: Callable):
    authorization_header = request.headers.get("Authorization")
    if authorization_header is None:
        # Якщо відсутній заголовок "Authorization", пропустити до наступного обробника
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

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to VIP PIT!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
    

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


if __name__ == '__main__':
    uvicorn.run("main:app", host="localhost", port=7385, reload=True)
