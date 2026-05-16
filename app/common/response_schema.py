from pydantic import BaseModel, ConfigDict, Field

class ErrorResponse(BaseModel):
    error: str = Field(..., description='Error message describing the issue that occurred')
    request_id: str = Field(..., description='Unique identifier for the request, useful for debugging and tracing')
    
    model_config = ConfigDict(extra='forbid')