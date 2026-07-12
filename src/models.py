from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class PromptModel(BaseModel):

    prompt: str = Field(..., min_length=1)

class propertyType(BaseModel):

    type: Literal["string", "number", "boolean"]

class FunctionDefinition(BaseModel):

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    parameters: dict[str, propertyType]
    returns:propertyType


class JSONState(Enum):
    """Enum representing the current structural state of the JSON parser."""

    START = "START"
    EXPECT_KEY = "EXPECT_KEY"


class JSONStateMachine(BaseModel):
    """Tracks the structural parsing state and expected schema definitions."""

    current_state: JSONState = JSONState.START
    expected_keys: List[str] = Field(default_factory=list)
    required_types: Dict[str, str] = Field(default_factory=dict)
    seen_keys: List[str] = Field(default_factory=list)
    buffer: str = ""

    def update(next_token: str):

        self.buffer.append += next_token
        if self.current_state.START:
            if '{' in next_token:
                self.current_state = "{EXPECT_KEY"
                i = next_token.index("{")
                self.buffer = next_token[i + 1:]
        elif self.current_state.EXPECT_KEY:
            pass


    @classmethod
    def from_schema(cls, schema_dict: Dict[str, Any]) -> "JSONStateMachine":
        """Initialize the state machine and fill it with schema properties.

        Args:
            schema_dict: The dictionary containing the function definitions.

        Returns:
            An instance of JSONStateMachine configured for the schema.
        """
        # Katjib les arguments w types dyalhom men 'parameters' dyal l'json
        parameters = schema_dict.get("parameters", {})
        properties = parameters.get("properties", {})

        expected_keys = list(properties.keys())
        required_types = {
            key: val.get("type", "string")
            for key, val in properties.items()
        }

        return cls(
            current_state=JSONState.START,
            expected_keys=expected_keys,
            required_types=required_types,
            seen_keys=[],
            buffer=""
        )


