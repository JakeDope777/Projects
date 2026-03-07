"""
Authentication API endpoints.

POST /auth/signup - Register new users
POST /auth/login  - Authenticate existing users
POST /auth/refresh - Refresh access token
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from ..core.config import settings
from ..db.session import get_db
from ..db import models
from ..db.schemas import UserCreate, UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and return access/refresh tokens."""
    # Check if user already exists
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = models.User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role="user",
    )
    db.add(user)
    db.flush()

    # Create token account
    token_account = models.TokenAccount(
        user_id=user.id,
        balance=settings.FREE_TIER_MONTHLY_TOKENS,
        tier="free",
    )
    db.add(token_account)
    db.commit()
    db.refresh(user)

    # Generate tokens
    token_data = {"sub": user.id, "email": user.email, "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return access/refresh tokens."""
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token_data = {"sub": user.id, "email": user.email, "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh an access token using a valid refresh token."""
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    token_data = {"sub": user.id, "email": user.email, "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        __import__("app.core.dependencies", fromlist=["get_current_user"]).get_current_user
    ),
):
    """Get the current authenticated user's information."""
    return current_user
