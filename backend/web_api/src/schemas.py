from datetime import datetime

from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class PasteCreate(BaseModel):
    title: str
    category_id: int
    syntax: str = "plain"
    raw_data: str
    expiration_datetime: datetime | None = None
    password: str | None = None
    burn_after_read: bool = False


class PasteOut(BaseModel):
    uid: str
    title: str
    category: CategoryOut
    syntax: str
    raw_data: str
    burn_after_read: bool
    expiration_datetime: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PasteCreatedOut(BaseModel):
    uid: str

    model_config = {"from_attributes": True}
