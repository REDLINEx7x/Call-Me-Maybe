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


JSONState = Literal["START", "EXPECT_KEY", "EXPECT_COLON", "EXPECT_VALUE", "EXPECT_SEPARATOR", "DONE"]

class JSONStateMachine(BaseModel):
    """Tracks the structural parsing state and expected schema definitions."""

    current_state: JSONState = "START"
    expected_keys: List[str] = Field(default_factory=list)
    required_types: Dict[str, str] = Field(default_factory=dict)
    seen_keys: List[str] = Field(default_factory=list)
    current_key: str = ""
    buffer: str = ""

    def update(self, next_token: str):

        self.buffer += next_token
        if self.current_state == "START":
            if '{' in self.buffer:
                self.current_state = "EXPECT_KEY"
                i = self.buffer.index("{")
                self.buffer = self.buffer[i + 1:]
                return
        elif self.current_state == "EXPECT_KEY":
            quote_count = self.buffer.count('"')
            if quote_count >= 2:
                first_quote = self.buffer.index('"')
                sec_quote = self.buffer.index('"', first_quote + 1)
                sliced_key = self.buffer[first_quote + 1:sec_quote]
                self.current_key = sliced_key
                self.current_state = "EXPECT_COLON"
                self.buffer = self.buffer[sec_quote + 1:]
                return
        elif self.current_state == "EXPECT_COLON":
            if ":" in self.buffer:
                i = self.buffer.index(":")
                self.buffer = self.buffer[i + 1 :]
                self.current_state = "EXPECT_VALUE"
                return
        elif self.current_state == "EXPECT_VALUE":
            expected_type = self.required_types.get(self.current_key)
            if expected_type == "string":
                if self.buffer.count('"') >= 2:
                    first_quote = self.buffer.index('"')
                    sec_quote = self.buffer.index('"', first_quote + 1)
                    sliced_val = self.buffer[first_quote + 1:sec_quote]
                    #print(f"Parsed String Value: {extracted_value}")
                    self.buffer = self.buffer[sec_quote + 1:]
                    self.current_state = "EXPECT_SEPARATOR"
                    return

            elif expected_type in ["number", "integer"]:
                if "," in self.buffer or "}" in self.buffer:
                    delimiters = [self.buffer.index(char) for char in [",", "}"] if char in self.buffer]
                    end_idx = min(delimiters)
                    extracted_num = self.buffer[:end_idx].strip()
                    #print(f"Parsed Number Value: {extracted_num}")
                    self.buffer = self.buffer[end_idx:]
                    self.current_state = "EXPECT_SEPARATOR"
                    return
            elif expected_type in ["boolean", "null"]:
                if expected_type == "boolean":
                    parsed_val = True if raw_val == "true" else False
                elif expected_type == "null":
                    parsed_val = None

        elif self.current_state == "EXPECT_SEPARATOR":
            if "," in self.buffer:
                i = self.buffer.index(',')
                self.buffer = self.buffer[i + 1:]
                self.current_state = "EXPECT_KEY"
                return
            elif "}" in self.buffer:
                self.buffer = ""
                self.current_state = "DONE"
                return

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


