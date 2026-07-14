import numpy as np
import json
from ..llm_sdk import Small_LLM_Model
from models import JSONState, JSONStateMachine

def generate_constrained_json(prompt, model, tokenizer, schema):

    vocab_path = model.get_path_to_vocab_file()
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    input_ids = model.encode(prompt)
    genertaed_txt = ""
    state = JSONStateMachine.from_schema(schema)

    while True:

        ids_logits = model.get_logits_from_input_ids(input_ids)
        filtred_logits = filter_tokens(ids_logits, state, vocab)
        next_token_id = np.argmax(filtered_logits)
        input_ids = np.append(input_ids, next_token_id)
        next_token_txt = mode.decode(next_token_id)
        genertaed_txt += next_token_txt

        state.update(next_token_txt)




def filter_tokens(logits, state, vocab):

    wrong_ids = []
    current_state = state.current_state

    for token_str, text in vocab.items():
        token_id = int(token_str)
        if current_state == "START":
            if not text.startswith("{"):
                wrong_ids.append(token_id)
        elif current_state == "EXPECT_KEY":
            pass

    if wrong_ids:
        logits[wrong_ids] = -float("inf")
    return logits
