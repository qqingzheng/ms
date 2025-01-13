from pydantic import BaseModel

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str = "Unknown error"
