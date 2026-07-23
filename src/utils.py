"""Utility functions for loading and validating input files."""

import json
from pathlib import Path
from typing import List, Dict, Any

from pydantic import ValidationError

from .models import PromptModel, FunctionDefinition
from llm_sdk.llm_sdk import Small_LLM_Model


def load_prompts(file_path: str) -> List[Dict[str, Any]]:
    """Read and validate the prompts JSON file.

    Args:
        file_path: Path to the prompts JSON file.

    Returns:
        A list of validated prompt dictionaries.
        Returns empty list if file is invalid or validation fails.
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

    validated_prompts: List[Dict[str, Any]] = []
    try:
        for item in data:
            if isinstance(item, dict):
                prompt_model = PromptModel(**item)
                validated_prompts.append(prompt_model.dict())
            else:
                print(f"Error: Invalid item format in '{file_path}'. Expected dictionary.")
                return []
    except ValidationError as e:
        print(f"Error: Pydantic validation failed for prompts in '{file_path}':\n{e}")
        return []

    return validated_prompts


def load_functions(file_path: str) -> List[Dict[str, Any]]:
    """Read and validate the functions definition JSON file.

    Args:
        file_path: Path to the functions definition JSON file.

    Returns:
        A list of validated function definition dictionaries.
        Returns empty list if file is invalid or validation fails.
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

    validated_functions: List[Dict[str, Any]] = []
    try:
        for item in data:
            if isinstance(item, dict):
                func_def = FunctionDefinition(**item)
                validated_functions.append(func_def.dict())
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



def build_prompt(user_prompt: str, functions: List[Dict[str, Any]]) -> str:
    """Construct a prompt that gives the model context on available functions.

    Args:
        user_prompt: The raw natural language request.
        functions: The list of available function definitions.

    Returns:
        A prompt string describing available functions, a worked example,
        and the user request — formatted to steer the model toward
        correct JSON-style output with values extracted from the request.
    """
    lines = []
    for f in functions:
        param_names = ", ".join(f["parameters"].keys())
        lines.append(
            f'- "{f["name"]}": {f["description"]} '
            f'(parameters: {param_names})'
        )
    functions_desc = "\n".join(lines)

    return (
        "You are a function calling assistant. Given the user's request, "
        "choose the correct function and respond with a JSON object.\n\n"
        f"Available functions:\n{functions_desc}\n\n"
        "Respond only with JSON in this exact shape: "
        '{"name": "<function_name>", "parameters": {...}}\n\n'
        "Example:\n"
        "User request: Greet mary\n"
        'Function call: {"name": "fn_greet", "parameters": {"name": "mary"}}\n\n'
        f"User request: {user_prompt}\n"
        "Function call:"
    )
