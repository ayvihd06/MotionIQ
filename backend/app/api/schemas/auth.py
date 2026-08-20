from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    display_name: Optional[str] = Field(None, max_length=100)

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    age_category: Optional[str] = None # e.g. "20-29", "30-39", "40-49", "50+"
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    running_experience: Optional[str] = None # e.g. "Beginner", "Intermediate", "Advanced"
    weekly_running_volume_km: Optional[float] = None
    typical_easy_pace: Optional[str] = None # e.g. "5:30 /km"
    video_retention_preference: Optional[bool] = False
    optional_profile_preferences: Optional[Dict[str, Any]] = None

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: Optional[str] = None
    age_category: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    running_experience: Optional[str] = None
    weekly_running_volume_km: Optional[float] = None
    typical_easy_pace: Optional[str] = None
    video_retention_preference: bool = False
    optional_profile_preferences: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    profile: Optional[UserProfileResponse] = None

class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    message: str
