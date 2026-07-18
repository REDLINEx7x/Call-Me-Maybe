import sys
import argparse
from utils import load_functions, load_prompts, load_vocab
from llm_sdk.llm_sdk import Small_LLM_Model
from decoder import generate_constrained_json


def main():

    all_answers = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--functions_definition", type=str, default="data/input/functions_definition.json")
    parser.add_argument("--input", type=str, default="data/input/function_calling_tests.json")
    parser.add_argument("--output", type=str, default="data/input/function_calling_results.json")
    args = parser.parse_args()

    model = Small_LLM_Model()
    #vocab = load_vocab(model)

    try:
        validated_prompts = load_prompts(args.input)
        validated_functions = load_functions(args.functions_definition)
        if not validated_functions or not validated_prompts:
            return
    except Exception as e:
        print(f"Error loading files: {e}")
        return


    valid_function_names = [func.get("name") for func in validated_functions]
    schemas_dict = {func.get("name"): func for func in validated_functions}
    #for prompt in validated_prompts:
    #    text_prompt = prompt.get("prompt", "")
    #    results = generate_constrained_json(text_prompt, model, vocab, schema_dict, valid_function_names)
    #    all_answers.append(results)

    #with open(args.output, "w", encoding="utf-8") as f:
    #    json.dump(all_answers, f, indent=4)

    #print(f"Done! Results saved successfully to {args.output}")
    print(schemas_dict)
if __name__ == "__main__":
    main()
