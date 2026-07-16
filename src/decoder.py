import numpy as np
import json
from ..llm_sdk import Small_LLM_Model
from models import JSONState, JSONStateMachine

def generate_constrained_json(prompt, model, tokenizer, schema):

    vocab_path = model.get_path_to_vocab_file()
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    inputs = model.encode(prompt)
    input_ids = [int(x) for x in raw_input_ids]
    genertaed_txt = ""
    state = JSONStateMachine.from_schema(schema)
    phase = "FUNCTION_SELECTION"
    current_buffer = ""

    while True:

        ids_logits = model.get_logits_from_input_ids(input_ids)
        filtered_logits = filter_tokens(ids_logits, state, vocab)
        next_token_id = int(np.argmax(filtered_logits))
        input_ids = np.append(input_ids, next_token_id)
        next_token_txt = model.decode(next_token_id)
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
                pass

            elif current_state == "EXPECT_COLON":
                if ":" not in token_text:
                    wrong_ids.append(token_id)

            elif current_state == "EXPECT_SEPARATOR":
                if "," not in token_text and "}" not in token_text:
                    wrong_ids.append(token_id)

    if wrong_ids:
        logits[wrong_ids] = -float("inf")
    return logits
