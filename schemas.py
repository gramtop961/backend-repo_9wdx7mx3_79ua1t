"""
Raksha Healthcare Platform Schemas

Each Pydantic model corresponds to one MongoDB collection (lowercased class name).
Use these models for validating incoming requests and shaping responses.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# -------------------------------------------------
# Core domain models
# -------------------------------------------------

class User(BaseModel):
    name: str
    email: EmailStr
    role: Literal["patient", "doctor", "admin"] = "patient"
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True


class Medicine(BaseModel):
    name: str = Field(..., description="Medicine display name")
    brand: Optional[str] = None
    category: str = Field(..., description="Therapeutic category")
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    stock: int = Field(0, ge=0)
    requires_rx: bool = Field(False, description="Whether prescription is required")
    forms: List[str] = Field(default_factory=list, description="e.g., tablet, syrup")
    strengths: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None


class Doctor(BaseModel):
    name: str
    specialty: str
    experience_years: int = Field(ge=0, default=0)
    rating: float = Field(ge=0, le=5, default=4.5)
    fee: float = Field(ge=0, default=0)
    languages: List[str] = Field(default_factory=list)
    available: bool = True
    image_url: Optional[str] = None


class Prescription(BaseModel):
    user_id: str
    doctor_id: Optional[str] = None
    notes: Optional[str] = None
    file_url: Optional[str] = Field(None, description="If uploaded, a file URL")
    status: Literal["pending", "approved", "rejected"] = "pending"


class Consultation(BaseModel):
    user_id: str
    doctor_id: str
    mode: Literal["video", "chat"] = "video"
    datetime_iso: str = Field(..., description="ISO timestamp for appointment")
    status: Literal["scheduled", "completed", "cancelled"] = "scheduled"


class OrderItem(BaseModel):
    medicine_id: str
    name: str
    price: float
    quantity: int


class Order(BaseModel):
    user_id: str
    items: List[OrderItem]
    total_amount: float
    address: str
    payment_method: Literal["cod", "card", "upi"] = "cod"
    status: Literal["placed", "packed", "shipped", "delivered", "cancelled"] = "placed"
    prescription_id: Optional[str] = None


# -------------------------------------------------
# Response helpers
# -------------------------------------------------

class IdResponse(BaseModel):
    id: str

class MessageResponse(BaseModel):
    message: str

class Paginated(BaseModel):
    total: int
    items: list

# Timestamps are auto-managed by database.create_document
