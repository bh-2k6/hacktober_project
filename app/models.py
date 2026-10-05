from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ItemAnalysis(BaseModel):
    category: str = ""
    object_type: str = ""
    color: str = ""
    brand: str = ""
    characteristics: List[str] = Field(default_factory=list)
    distinctive_features: List[str] = Field(default_factory=list)
    visible_text: str = ""
    other_attributes: dict = Field(default_factory=dict)
    confidence: float = 0.0


class ItemCreate(BaseModel):
    type: str = Field(..., pattern="^(lost|found)$")
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=2000)
    location: str = Field(..., min_length=1, max_length=200)
    date_time: str = Field(..., description="ISO format datetime")


class ItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    location: Optional[str] = Field(default=None, min_length=1, max_length=200)
    date_time: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(active|reunited|expired)$")


class ItemResponse(BaseModel):
    id: int
    type: str
    title: str
    description: Optional[str]
    category: Optional[str]
    object_type: Optional[str]
    color: Optional[str]
    brand: Optional[str]
    characteristics: List[str]
    distinctive_features: List[str]
    visible_text: Optional[str]
    other_attributes: dict
    location: str
    date_time: str
    image_path: Optional[str]
    status: str
    created_at: str
    updated_at: str


class MatchResponse(BaseModel):
    id: int
    lost_item_id: int
    found_item_id: int
    score: float
    explanation: str
    factor_scores: dict
    status: str
    created_at: str
    lost_item: Optional[ItemResponse] = None
    found_item: Optional[ItemResponse] = None


class MatchUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|confirmed|rejected)$")


class ContactRequestCreate(BaseModel):
    match_id: int
    requester_type: str = Field(..., pattern="^(lost_owner|found_finder)$")
    message: str = Field(..., min_length=1, max_length=1000)


class ContactRequestResponse(BaseModel):
    id: int
    match_id: int
    requester_type: str
    message: str
    status: str
    created_at: str


class DashboardStats(BaseModel):
    total_lost: int
    total_found: int
    total_matches: int
    confirmed_matches: int
    reunited_items: int
    pending_matches: int
