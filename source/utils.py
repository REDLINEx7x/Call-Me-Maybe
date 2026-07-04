from pathlib import Path
import json
from src.models import PromptModel, FunctionDefinition


def function_calling(file_path):
    path = Path("data/input/function_calling_tests.json")
    if path.suffix.lower() != '.json':
        print(f"Error: The file '{file_path}' must have a .json extension.")
        return []
    try:
        with open(load_path, "r") as file:

            data = json.load(file)

    except Exception as e:
        print(f"Error loading JSON data: {e}")
        return None

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

def functions_definition(file_path):

    path = Path("data/input/functions_definition.json")

    if path.suffix.lower() != "json":
        print(f"Error: The file '{file_path}' must have a .json extension.")
        return []

    with open(path, "r") as file:

        data = json.load(file)


