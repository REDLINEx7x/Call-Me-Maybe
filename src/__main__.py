import sys
import argparse
from .utils import load_functions, load_prompts, load_vocab, build_prompt
from llm_sdk.llm_sdk import Small_LLM_Model
from .decoder import generate_constrained_json
import json
from pathlib import Path



def main() -> None:
    """Main execution function.

    Loads function definitions and prompts, then processes each prompt
    through constrained decoding to generate structured function calls.
    """
    all_answers = []

    parser = argparse.ArgumentParser(
        description="Function calling with constrained decoding"
    )
    parser.add_argument(
        "--functions_definition",
        type=str,
        default="data/input/functions_definition.json",
        help="Path to function definitions JSON file"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/input/function_calling_tests.json",
        help="Path to input prompts JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/output/function_calling_results.json",
        help="Path to output results JSON file"
    )
    args = parser.parse_args()

    # Load model and vocabulary
    try:
        model = Small_LLM_Model()
        vocab = load_vocab(model)
    except RuntimeError as e:
        print(f"Error loading model or vocab: {e}")
        return

    # Load input files
    try:
        validated_prompts = load_prompts(args.input)
        validated_functions = load_functions(args.functions_definition)

        if not validated_functions or not validated_prompts:
            print("Error: No valid prompts or functions loaded.")
            return
    except FileNotFoundError as e:
        print(f"Error: Input file not found: {e}")
        return
    except ValueError as e:
        print(f"Error: Invalid input: {e}")
        return

    # Create function lookup
    valid_function_names = [func.get("name") for func in validated_functions]
    schema_dict = {func.get("name"): func for func in validated_functions}

    # Process each prompt
    for idx, prompt in enumerate(validated_prompts, 1):
        print(f"[{idx}/{len(validated_prompts)}] processing: {prompt.get('prompt', '')}")
        text_prompt = prompt.get("prompt", "")
        if not text_prompt:
            continue

        try:
            # Generate constrained JSON (returns {"name": "...", "parameters": {...}})
            result = generate_constrained_json(
                text_prompt,
                model,
                vocab,
                schema_dict,
                valid_function_names
            )

            # Format output with original prompt
            output_item = {
                "prompt": text_prompt,
                "name": result.get("name", ""),
                "parameters": result.get("parameters", {})
            }
            all_answers.append(output_item)
            print(f"[{idx}/{len(validated_prompts)}] done")

        except Exception as e:
            print(f"Error processing prompt '{text_prompt}': {e}")
            continue

    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write results
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_answers, f, indent=4, ensure_ascii=False)
        print(f"Done! Results saved successfully to {args.output}")
    except IOError as e:
        print(f"Error writing output file: {e}")
        return


if __name__ == "__main__":
    main()
