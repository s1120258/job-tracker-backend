# app/api/routes_auth.py

import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.crud import user as crud_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    GoogleAuthResponse,
    GoogleTokenRequest,
    RefreshToken,
    Token,
    UserCreate,
    UserRead,
)
from app.services.google_oauth_service import google_oauth_service

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


@router.post("/register", response_model=UserRead)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = crud_user.get_user_by_email(db, user_in.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud_user.create_user(db, user_in)


@router.post("/token", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    db_user = crud_user.get_user_by_email(db, form_data.username)
    if not db_user or not security.verify_password(
        form_data.password, db_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = security.create_access_token(data={"sub": db_user.email})
    refresh_token = security.create_refresh_token(data={"sub": db_user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str = Body(..., embed=True)):
    payload = security.verify_refresh_token(refresh_token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    access_token = security.create_access_token(data={"sub": payload["sub"]})
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    from jose import JWTError, jwt

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud_user.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user


@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/google/verify", response_model=GoogleAuthResponse)
async def google_auth_verify(
    token_request: GoogleTokenRequest, db: Session = Depends(get_db)
):
    """
    Verify Google ID token and authenticate user.
    This endpoint is used by frontend-driven OAuth flow.
    """
    try:
        logger.info(f"Starting Google authentication for token length: {len(token_request.id_token)}")

        # Verify the Google ID token
        google_user_info = await google_oauth_service.verify_id_token(
            token_request.id_token
        )

        logger.info(f"Google token verified successfully for user: {google_user_info['email']}")

        # Parse user data for database operations
        user_data = google_oauth_service.parse_user_data(google_user_info)
        logger.info(f"Parsed user data: {user_data}")

        # Get or create user in database
        try:
            user = crud_user.get_or_create_google_user(db, user_data)
            logger.info(f"User retrieved/created successfully: {user.email}")
        except Exception as db_error:
            logger.error(f"Database operation failed: {db_error}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database operation failed: {str(db_error)}",
            )

        # Generate JWT tokens
        try:
            access_token = security.create_access_token(data={"sub": user.email})
            refresh_token = security.create_refresh_token(data={"sub": user.email})
            logger.info(f"JWT tokens generated successfully for user: {user.email}")
        except Exception as token_error:
            logger.error(f"Token generation failed: {token_error}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token generation failed: {str(token_error)}",
            )

        logger.info(f"Successfully authenticated Google user: {user.email}")

        return GoogleAuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserRead.model_validate(user),
        )

    except HTTPException:
        # Re-raise HTTP exceptions from the service
        logger.warning(f"Google authentication failed with HTTP exception")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Google authentication: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}",
        )


@router.post("/google/register", response_model=GoogleAuthResponse)
async def google_register(
    token_request: GoogleTokenRequest, db: Session = Depends(get_db)
):
    """
    Register new user with Google OAuth.
    Alternative endpoint that ensures user doesn't already exist.
    """
    try:
        # Verify the Google ID token
        google_user_info = await google_oauth_service.verify_id_token(
            token_request.id_token
        )

        # Check if user already exists
        existing_user = crud_user.get_user_by_email(db, google_user_info["email"])
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Parse user data and create new user
        user_data = google_oauth_service.parse_user_data(google_user_info)
        user = crud_user.create_google_user(db, user_data)

        # Generate JWT tokens
        access_token = security.create_access_token(data={"sub": user.email})
        refresh_token = security.create_refresh_token(data={"sub": user.email})

        logger.info(f"Successfully registered new Google user: {user.email}")

        return GoogleAuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserRead.model_validate(user),
        )

    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Google registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.get("/google/status")
async def google_auth_status():
    """
    Check Google OAuth service status and configuration.
    Useful for debugging authentication issues.
    """
    try:
        from app.services.google_oauth_service import google_oauth_service

        status_info = {
            "service_configured": bool(google_oauth_service.client_id),
            "client_id_configured": bool(google_oauth_service.client_id),
            "client_secret_configured": bool(google_oauth_service.client_secret),
            "client_id_prefix": google_oauth_service.client_id[:20] + "..." if google_oauth_service.client_id else None,
            "jwks_url": google_oauth_service.GOOGLE_JWKS_URL,
        }

        logger.info(f"Google OAuth status check: {status_info}")
        return status_info

    except Exception as e:
        logger.error(f"Error checking Google OAuth status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}",
        )
