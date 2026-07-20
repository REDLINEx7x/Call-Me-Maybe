"""Constrained decoding for structured JSON generation."""
import numpy as np
from .models import JSONStateMachine
from llm_sdk.llm_sdk import Small_LLM_Model
from typing import Dict, List, Any
from .utils import build_prompt

def generate_constrained_json(
    prompt: str,
    model: Small_LLM_Model,
    vocab: Dict[int, str],
    schema: Dict[str, Dict[str, Any]],
    valid_names: List[str]
) -> Dict[str, Any]:
    """Generate constrained JSON function call from natural language prompt.

    Uses two-phase constrained decoding:
    1. FUNCTION_SELECTION: Identify which function to call
    2. PARAMETER_GENERATION: Generate valid JSON parameters for that function

    Args:
        prompt: Natural language prompt to process.
        model: LLM model instance for token generation.
        vocab: Token ID to token string mapping.
        schema: Dict mapping function names to their definitions.
        valid_names: List of available function names to select from.

    Returns:
        Dict with keys "name" (function name) and "parameters" (parsed args dict).
    """
    full_prompt = build_prompt(prompt, list(schema.values()))
    inputs = model.encode(full_prompt)
    input_ids = inputs[0].tolist()

    state = None  # Will be initialized after function selection
    phase = "FUNCTION_SELECTION"
    current_buffer = ""
    selected_function_name = None
    max_steps = 100
    for _ in range(max_steps):
        ids_logits = model.get_logits_from_input_ids(input_ids)
        filtered_logits = filter_tokens(
            ids_logits,
            state,
            vocab,
            phase,
            current_buffer,
            valid_names
        )
        if np.isneginf(filtered_logits).all():
            # FIXED: raise instead of silently breaking with partial/wrong output
            raise RuntimeError(
                f"All tokens masked — phase={phase}, "
                f"state={state.current_state if state else None}, "
                f"buffer={state.buffer if state else current_buffer!r}"
            )
        next_token_id = int(np.argmax(filtered_logits))
        input_ids.append(next_token_id)
        next_token_txt = vocab[next_token_id]
        print(repr(vocab[next_token_id]))
        if phase == "FUNCTION_SELECTION":
            current_buffer += next_token_txt

            #print(f"buffer so far: {current_buffer!r}")
            if current_buffer in valid_names:
                selected_function_name = current_buffer
                selected_schema = schema[selected_function_name]
                state = JSONStateMachine.from_schema(selected_schema)
                phase = "PARAMETER_GENERATION"
                current_buffer = ""

        elif phase == "PARAMETER_GENERATION" and state is not None:
            try:
                state.update(next_token_txt)
            except ValueError as e:
                raise RuntimeError(f"State machine error: {e}") from e
            if state.current_state == "DONE":
                break

    if selected_function_name is None:
         raise RuntimeError("Model failed to select a valid function name")

    return {
        "name": selected_function_name or "",
        "parameters": state.parsed_data if state is not None else {}
    }


def filter_tokens(
    logits: np.ndarray,
    state: JSONStateMachine | None,
    vocab: Dict[int, str],
    phase: str,
    current_buffer: str,
    valid_names: List[str]
) -> np.ndarray:
    """Filter logits to only valid tokens for current phase and state.

    Args:
        logits: Raw logits from model.
        state: Current JSON state machine (None during function selection).
        vocab: Token ID to token string mapping.
        phase: Current generation phase.
        current_buffer: Accumulated tokens in current phase.
        valid_names: List of valid function names.

    Returns:
        Filtered logits with invalid tokens set to -infinity.
    """
    logits = np.array(logits, dtype=float)
    wrong_ids = set()

    all_ids = set(range(len(logits)))
    known_ids = set(int(tid) for tid in vocab.keys())
    wrong_ids |= (all_ids - known_ids)
    if phase == "FUNCTION_SELECTION":
        for token_id, token_txt in vocab.items():
            tid = int(token_id)
            ttxt = str(token_txt)
            if not ttxt:  # empty token can never make progress
                wrong_ids.add(tid)
                continue
            potential_str = current_buffer + ttxt
            # Check if this potential string is a prefix of any valid function name
            is_valid = any(
                target.startswith(potential_str)
                for target in valid_names
            )
            if not is_valid:
                wrong_ids.add(tid)

    elif phase == "PARAMETER_GENERATION" and state is not None:
        for token_id, token_txt in vocab.items():
            tid = int(token_id)
            ttxt = str(token_txt)

            if state.current_state == "START":
                if "{" not in ttxt:
                    wrong_ids.add(tid)

            elif state.current_state == "EXPECT_KEY":
                if any(c in ttxt for c in "()"):
                    wrong_ids.add(tid)
                    continue
                valid_keys = [
                    f'"{k}"'
                    for k in state.expected_keys
                    if k not in state.seen_keys
                ]
                potential_str = state.buffer + ttxt
                is_valid = any(
                    key_target.startswith(potential_str)
                    for key_target in valid_keys
                )
                if not is_valid:
                    wrong_ids.add(tid)

            elif state.current_state == "EXPECT_COLON":
                if ":" not in ttxt:
                    wrong_ids.add(tid)

            elif state.current_state == "EXPECT_VALUE":
                expected_type = state.required_types.get(state.current_key)

                if expected_type == "string":
                    if state.buffer.strip() == "" and '"' not in ttxt:
                        wrong_ids.add(tid)
                elif expected_type in ["number", "integer"]:
                    digit_chars = "0123456789.-"
                    has_digits = any(c.isdigit() for c in state.buffer.strip())
                    remaining_keys = [
                        k for k in state.expected_keys
                        if k not in state.seen_keys and k != state.current_key
                    ]
                    allowed_separators = ",}" if remaining_keys else "}"
                    allowed_separators += " \n"
                    for ch in ttxt:
                        if ch in digit_chars:
                            continue
                        if ch in allowed_separators and has_digits:
                            continue
                        wrong_ids.add(tid)
                        break


                elif expected_type == "boolean":
                    value_so_far = state.buffer.strip()
                    potential_str = value_so_far + ttxt
                    # FIXED: real prefix matching, not character-set membership
                    is_valid = any(
                        candidate.startswith(potential_str)
                        for candidate in ["true", "false"]
                    )
                    if not is_valid:
                        wrong_ids.add(tid)

            elif state.current_state == "EXPECT_SEPARATOR":
                remaining_keys = [k for k in state.expected_keys if k not in state.seen_keys]
                allowed = "}," if remaining_keys else "}"
                if not any(ch in allowed for ch in ttxt):
                    wrong_ids.add(tid)

    if wrong_ids:
        logits[list(wrong_ids)] = -float("inf")
    return logits
