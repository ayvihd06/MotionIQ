from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from app.config import (
    AUTH_COOKIE_NAME, AUTH_COOKIE_SECURE, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.db.session import get_db
from app.db.models import User, UserProfile
from app.auth.security import get_password_hash, verify_password, create_access_token
from app.auth.dependencies import get_current_user
from app.api.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, UserProfileUpdateRequest,
    UserResponse, UserProfileResponse, AuthResponse
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def set_auth_cookie(response: Response, token: str):
    """Sets secure HTTP-only session cookie for the authenticated runner."""
    max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=max_age,
        expires=max_age,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite="lax",
        path="/"
    )

def clear_auth_cookie(response: Response):
    """Clears the authentication session cookie."""
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite="lax",
        path="/"
    )

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    request_data: UserRegisterRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Registers a new user account and creates their initial profile."""
    # Check if email is already taken
    existing_user = db.query(User).filter(User.email == request_data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Create User
    new_user = User(
        email=request_data.email.lower(),
        password_hash=get_password_hash(request_data.password),
        last_login_at=datetime.now(timezone.utc)
    )
    db.add(new_user)
    db.flush() # populate new_user.id

    # Create default UserProfile
    profile = UserProfile(
        user_id=new_user.id,
        display_name=request_data.display_name or request_data.email.split("@")[0],
        video_retention_preference=False
    )
    db.add(profile)
    db.commit()
    db.refresh(new_user)

    # Generate JWT token & set HTTP-only cookie
    token = create_access_token({"sub": str(new_user.id), "email": new_user.email})
    set_auth_cookie(response, token)

    return AuthResponse(
        user=UserResponse.model_validate(new_user),
        access_token=token,
        token_type="bearer",
        message="Registration successful. Welcome to MotionIQ!"
    )

@router.post("/login", response_model=AuthResponse)
def login(
    request_data: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Authenticates user credentials and issues an authentication session."""
    user = db.query(User).filter(User.email == request_data.email.lower()).first()
    if not user or not verify_password(request_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated."
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email})
    set_auth_cookie(response, token)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=token,
        token_type="bearer",
        message="Login successful."
    )

@router.post("/logout")
def logout(response: Response):
    """Terminates the user's session and clears the session cookie."""
    clear_auth_cookie(response)
    return {"status": "success", "message": "Logged out successfully."}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieves the authenticated user's profile and account metadata."""
    return UserResponse.model_validate(current_user)

@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates the authenticated runner's profile settings and preferences."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    update_dict = profile_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(profile, field, value)

    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)

    return UserProfileResponse.model_validate(profile)

@router.delete("/account")
def delete_account(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permanently deletes the authenticated user's account, profile, analyses, metrics, and observations."""
    user_id = current_user.id
    
    # Delete user from DB (Cascades automatically to profile, analyses, metrics, observations)
    db.delete(current_user)
    db.commit()

    clear_auth_cookie(response)
    return {
        "status": "success",
        "message": f"Account {user_id} and all associated personal biomechanics data have been permanently deleted."
    }
