import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Security, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Form
from src.database.db import get_db
from src.models.models import User
from src.repository import users as repository_users
from src.schemas.user import UserCreateSchema, TokenSchema, UserResponseSchema, RequestEmail, ConfirmationResponse, \
    LogoutResponseSchema
from src.services.auth import auth_service
from src.services.email import send_email
from src.conf import messages
from src.schemas.auth import LoginSchema, RegisterSchema
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="src/services/templates")

router = APIRouter(tags=["auth"])

blacklisted_tokens = set()

get_refresh_token = HTTPBearer()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request,
                  user: User = Depends(auth_service.get_current_user_from_cookie)):
    print(user)  # Log the user object
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

@router.post("/signup", response_class=HTMLResponse)
async def signup(background_tasks: BackgroundTasks,
                  request: Request,
                  email: str = Form(...),
                  name: str = Form(...),
                  password: str = Form(...),
                  phone: str = Form(None),
                  car_number: str = Form(None),
                  db: AsyncSession = Depends(get_db)):
    body = UserCreateSchema(
        email=email,
        name=name,
        password=password,
        phone=phone,
        car_number=car_number,
        password_confirmation=password  # або отримайте з форми, якщо це передбачено
    )
    if not secrets.compare_digest(body.password, body.password_confirmation):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.PASSWORDS_NOT_MATCH)
    del body.password_confirmation
    exist_user = await repository_users.get_user_by_email(email=body.email, db=db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.ACCOUNT_EXISTS)
    body.password = await auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db=db)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)




@router.post("/login", response_class=HTMLResponse)
async def login(request: Request,
                 email: str = Form(...),
                 password: str = Form(...),
                 db: AsyncSession = Depends(get_db)):
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_EMAIL)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.INACTIVE_USER)
    if not await auth_service.verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_PASSWORD)

    access_token = await auth_service.create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="profile", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)  # Set cookie as HttpOnly for security
    return response

@router.post("/logout", response_model=LogoutResponseSchema)
async def logout(request: Request, 
                 access_token: str = Depends(auth_service.get_user_access_token),
                 user: User = Depends(auth_service.get_current_user_from_cookie),
                 db: AsyncSession = Depends(get_db)) -> dict:
    blacklisted_tokens.add(access_token)
    user.refresh_token = None
    await db.commit()

    response = RedirectResponse(url="login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return {"message": "Logout successful."}


@router.get('/refresh_token', response_model=TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(get_refresh_token),
                        db: AsyncSession = Depends(get_db)) -> dict:
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if not secrets.compare_digest(user.refresh_token, token):
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_REFRESH_TOKEN)

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token_ = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token_, db)
    return {"access_token": access_token, "refresh_token": refresh_token_, "token_type": "bearer"}


@router.post("/request_email")
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)) -> dict:
    user = await repository_users.get_user_by_email(body.email, db)
    if user.confirmed:
        return {"message": messages.EMAIL_ALREADY_CONFIRMED}
    if user:
        background_tasks.add_task(send_email, user.email, user.name, str(request.base_url))
    return {"message": messages.CHECK_EMAIL_FOR_CONFIRMATION}


@router.get('/confirmed_email/{token}', response_model=ConfirmationResponse)
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)) -> ConfirmationResponse:
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return ConfirmationResponse(message="Your email is already confirmed")
    await repository_users.confirmed_email(email, db)
    return ConfirmationResponse(message="Email confirmed")

