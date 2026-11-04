from datetime import datetime
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    workspace_id: int
    uploaded_by_id: int
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True