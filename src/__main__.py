import sys
import argparse
from .utils import load_functions, load_prompts


def main():

    all_answers = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--functions_definition", type=str, default="data/input/functions_definition.json")
    parser.add_argument("--input", type=str, default="data/input/function_calling_tests.json")
    parser.add_argument("--output", type=str, default="data/input/function_calling_results.json")
    args = parser.parse_args()

    try:
        validated_prompts = load_prompts(args.input)
        validated_functions = load_functions(args.functions_definition)

        if not validated_functions or not validated_prompts:
            return
    except Exception as e:
        print(f"")

    for p in validated_prompts:
        print(p)

main()
