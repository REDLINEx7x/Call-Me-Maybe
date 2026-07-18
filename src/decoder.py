import numpy as np
import json
from models import JSONState, JSONStateMachine
from llm_sdk.llm_sdk import Small_LLM_Model
def generate_constrained_json(prompt: str, model: Small_LLM_Model, vocab: dict, schema: dict, valid_names: list[str]):

    vocab_path = model.get_path_to_vocab_file()
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    inputs = model.encode(prompt)
    input_ids = inputs[0].tolist()
    genertaed_txt = ""
    state = JSONStateMachine.from_schema(schema)
    phase = "FUNCTION_SELECTION"
    current_buffer = ""

    while True:

        ids_logits = model.get_logits_from_input_ids(input_ids)
        filtered_logits = filter_tokens(ids_logits, state, vocabm, phase, current_buffer, valid_names)
        next_token_id = int(np.argmax(filtered_logits))
        input_ids.append(next_token_id)
        next_token_txt = model.decode([next_token_id])
        genertaed_txt += next_token_txt

        if phase == "FUNCTION_SELECTION":
            current_buffer += next_token_txt
            if current_buffer in valid_function_names:
                name = current_buffer
                phase = "PARAMETER_GENERATION"
        elif phase == "PARAMETER_GENERATION":
            state.update(next_token_txt)

            if state.current_state == "DONE" or "}" in next_token_txt:
                break

    return {
        "function": current_buffer,
        "parameters": generated_txt
    }
def filter_tokens(logits, state, vocab, phase, current_buffer, valid_names):

    logits = np.array(logits)
    wrong_ids = []
    current_state = state.current_state

    if phase == "FUNCTION_SELECTION":
        for token_id, token_txt in vocab.items():
            potential_str = current_buffer + token_txt
            is_valid = any(target.startswith(potential_str) for target in valid_names)
            if not is_valid:
                wrong_ids.append(token_id)
    elif phase == "PARAMETER_GENERATION":
        current_state = state.current_state

        for token_id, token_txt in vocab.items():
            if current_state == "START":
                if "{" not in token_txt:
                    wrong_ids.append(token_id)
            elif current_state == "EXPECT_KEY":
                valid_keys = [f'"{key}"' for key in state.expected_keys if key not in state.seen_keys]

                for token_id, token_txt in vocab.items():
                    potential_str = state.buffer + token_txt
                    is_valid = any(key_target.startswith(potential_str) for key_target in valid_keys)

                    if not is_valid:
                        wrong_ids.append(token_id)

            elif current_state == "EXPECT_COLON":
                if ":" not in token_text:
                    wrong_ids.append(token_id)

            elif current_state == "EXPECT_VALUE":
                expected_type = state.required_types.get(state.current_key)

                for token_id, token_txt in vocab.items():

                    if expected_type == "string":
                        if state.buffer.strip() == "" and '"' not in token_txt:
                            wrong_ids.append(token_id)

                    elif expected_type in ["number", "integer"]:
                        valid_chars = "0123456789.-, \n}"
                        if any(char not in valid_chars for char in token_txt):
                            wrong_ids.append(token_id)

                    elif expected_type == "boolean":
                        valid_chars = "truefals, \n}"
                        if any(char not in valid_chars for char in token_txt):
                            wrong_ids.append(token_id)

            elif current_state == "EXPECT_SEPARATOR":
                if "," not in token_text and "}" not in token_txt:
                    wrong_ids.append(token_id)

    if wrong_ids:
        logits[wrong_ids] = -float("inf")
    return logits
