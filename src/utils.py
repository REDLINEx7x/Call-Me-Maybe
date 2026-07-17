import json
from pathlib import Path
from typing import List, Any
from pydantic import ValidationError
from .models import PromptModel, FunctionDefinition
def load_prompts(file_path: str) -> List[PromptModel]:
    """Read and validate the prompts JSON file.

    Args:
        file_path (str): Path to the prompts JSON file.

    Returns:
        List[PromptModel]: A list of validated PromptModel objects,
                           or an empty list if validation fails.
    """
    path = Path(file_path)

    if path.suffix.lower() != '.json':
        print(f"Error: The file '{file_path}' must have a .json extension.")
        return []

    try:
        with open(path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                print(f"Error: The file '{file_path}' contains invalid JSON syntax.")
                return []
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []

    if not isinstance(data, list):
        print(f"Error: The root of '{file_path}' must be a JSON array (list).")
        return []

    validated_prompts: List[PromptModel] = []
    try:
        for item in data:
            if isinstance(item, dict):
                validated_prompts.append(PromptModel(**item))
            else:
                print(f"Error: Invalid item format in '{file_path}'. Expected dictionary.")
                return []
    except ValidationError as e:
        print(f"Error: Pydantic validation failed for prompts in '{file_path}':\n{e}")
        return []

    return validated_prompts


def load_functions(file_path: str) -> List[FunctionDefinition]:
    """Read and validate the functions definition JSON file.

    Args:
        file_path (str): Path to the functions definition JSON file.

    Returns:
        List[FunctionDefinition]: A list of validated FunctionDefinition objects,
                                  or an empty list if validation fails.
    """
    path = Path(file_path)
    if path.suffix.lower() != '.json':
        print(f"Error: The file '{file_path}' must have a .json extension.")
        return []

    try:
        with open(path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                print(f"Error: The file '{file_path}' contains invalid JSON syntax.")
                return []
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []

    if not isinstance(data, list):
        print(f"Error: The root of '{file_path}' must be a JSON array (list).")
        return []

    validated_functions: List[FunctionDefinition] = []
    try:
        for item in data:
            if isinstance(item, dict):
                validated_functions.append(FunctionDefinition(**item))
            else:
                print(f"Error: Invalid item format in '{file_path}'. Expected dictionary.")
                return []
    except ValidationError as e:
        print(f"Error: Pydantic validation failed for functions in '{file_path}':\n{e}")
        return []

    return validated_functions


def load_vocab(model: Small_LLM_Model) -> dict[int, str]:
    """Load the vocab file and return an id-to-token lookup.

    Args:
        model: The SDK model instance, used to locate the vocab file.

    Returns:
        A mapping from token id to its string representation.

    Raises:
        RuntimeError: If the vocab file cannot be read or parsed.
    """
    try:
        path = model.get_path_to_vocab_file()
        with open(path, "r", encoding="utf-8") as f:
            raw_vocab = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not load vocab file: {exc}") from exc

    return {token_id: token_str for token_str, token_id in raw_vocab.items()}
