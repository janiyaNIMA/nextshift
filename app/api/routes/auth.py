from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserRegisterRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student or employer",
)
def register(user_in: UserRegisterRequest, db: DbSession):
    auth_service = AuthService(db)
    user = auth_service.register(user_in)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and obtain JWT access token",
)
def login(login_in: LoginRequest, db: DbSession):
    auth_service = AuthService(db)
    user = auth_service.authenticate(email=login_in.email, password=login_in.password)
    return auth_service.create_token_for_user(user)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def get_me(current_user: CurrentUser):
    return current_user
