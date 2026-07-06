from pydantic import BaseModel, Field
from typing import Literal

class PromptModel(BaseModel):

    prompt: str = Field(..., min_length=1)

class propertyType(BaseModel):

    type: Literal["string", "number", "boolean"]

class FunctionDefinition(BaseModel):

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    parameters: dict[str, propertyType]
    returns:propertyType

