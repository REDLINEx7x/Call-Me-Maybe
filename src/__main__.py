import sys
import argparse
from .utils import load_functions, load_prompts


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--functions_definition", type=str, default="data/input/functions_definition.json")
    parser.add_argument("--input", type=str, default="data/input/function_calling_tests.json")
    parser.add_argument("--output", type=str, default="data/input/function_calling_results.json")
    args = parser.parse_args()

    try:
        validated_functions = load_functions(args.functions_definition)
        validated_prompts = load_functions(args.input)
        if not validated_functions or not validated_prompts:
            return
    except Exception as e:
        print(f"")


main()
