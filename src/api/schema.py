from pydantic import BaseModel, Field
from typing import List, Optional

class UploadResponse(BaseModel):
    message: str
    files: List[str]

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The question to ask")

class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: List[str] = Field(default=[], description="Source documents")
    needs_info: Optional[bool] = Field(default=None, description="Whether assistant needs contact info")
    form_prompt: Optional[str] = Field(default=None, description="Next prompt for conversational form")
    form_complete: Optional[bool] = Field(default=None, description="Whether the form has completed")
    form_data: Optional[dict] = Field(default=None, description="Collected form data if complete")

class HealthResponse(BaseModel):
    status: str

class StatusResponse(BaseModel):
    has_documents: bool
    vectorstore_loaded: bool
    documents_directory: str
    chroma_db_directory: str

class ErrorResponse(BaseModel):
    detail: str