*This project has been created as part of the 42 curriculum by moamhouc.*

# call-me-maybe

## Description

This project implements a function-calling engine that translates natural language
prompts into structured, schema-compliant function calls using a small language
model (Qwen3-0.6B, ~500M parameters).

Small models are notoriously unreliable at producing valid structured output when
simply prompted to do so — success rates around 30% are typical. Instead of relying
on prompting alone, this project implements **constrained decoding**: at every
generation step, the model's output logits are masked so that only tokens
consistent with valid JSON syntax *and* the target function's schema can be
selected. This guarantees syntactically and semantically valid output — the model
chooses *which* function to call and *what* values to extract, but it can never
produce invalid JSON, an unknown function name, a wrong parameter type, or a
missing required argument.

Given a prompt like `"What is the sum of 2 and 3?"`, the program outputs:
```json
{
  "prompt": "What is the sum of 2 and 3?",
  "name": "fn_add_numbers",
  "parameters": {"a": 2.0, "b": 3.0}
}
```

## Instructions

### Requirements
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) for dependency management
- The `llm_sdk` package, copied into the project root (next to `src/`)

### Installation
```bash
uv sync
```

### Running
```bash
uv run python -m src [--functions_definition <path>] [--input <path>] [--output <path>]
```
By default, the program reads from `data/input/functions_definition.json` and
`data/input/function_calling_tests.json`, and writes to
`data/output/function_calling_results.json`.

Example:
```bash
uv run python -m src \
  --functions_definition data/input/functions_definition.json \
  --input data/input/function_calling_tests.json \
  --output data/output/function_calling_results.json
```

### Linting
```bash
make lint

make lint-strict

```

## Algorithm Explanation

Generation happens in two phases, driven by a single token-by-token loop:

**1. Function selection.** The model generates the function name character by
character. At each step, every candidate token in the vocabulary is checked: does
appending it keep the partial string a valid *prefix* of at least one function
name declared in `functions_definition.json`? Every token that would break this is
masked to `-inf` before the next token is sampled. Selection completes the moment
the partial string exactly matches a real function name.

**2. Parameter generation.** Once the function is known, its parameter schema
(names and types) becomes the active constraint set. A state machine
(`JSONStateMachine`) tracks the current position in the JSON grammar
(`START → EXPECT_KEY → EXPECT_COLON → EXPECT_VALUE → EXPECT_KEY/DONE`) and, at
each state, only tokens consistent with that position — and, for values, with the
parameter's declared type (`string`, `number`, `boolean`, `null`) — remain unmasked.
Required-key completeness is enforced before the closing brace is ever allowed,
and duplicate keys are rejected.

**Zero-parameter functions** are handled as a special case: if a selected function
declares no parameters, the `PARAMETER_GENERATION` phase is skipped entirely and
the state machine transitions directly to `DONE`, since entering `EXPECT_KEY` with
an empty key set would mask every token and crash.

Three structural safety nets exist on top of this: any token id absent from the
loaded vocabulary (e.g. special/control tokens) is masked unconditionally; if
every token is ever masked at once, generation raises immediately with the exact
state and buffer content; and a stall detector raises if the state machine remains
in the same state for more than 50 consecutive tokens without progress.

## Design Decisions

- **Functions over classes for decoding logic.** The state machine's transition
  and validity-check logic is implemented as data (`JSONStateMachine`, a pydantic
  model holding state) plus functions that operate on it, rather than a class with
  hidden behavioral methods layered on top — this keeps state explicit and each
  transition testable in isolation.
- **`Literal` over `Enum` for state representation.** A `Literal["START", "EXPECT_KEY", ...]`
  type alias gives full mypy-checked safety against typo'd state names without the
  syntactic overhead of an `Enum` class — plain strings are used throughout, with
  static checking catching any invalid value at lint time.
- **Allowlist-style masking for unknown tokens.** Early versions only masked
  tokens explicitly found invalid by the grammar/schema check, which left any
  token *outside* the loaded vocabulary (e.g. end-of-sequence/control tokens)
  unmasked by omission. The final version explicitly masks every token id not
  present in the vocabulary lookup as a first step, closing that gap.
- **Direct state transitions for value-terminated types.** Numeric, boolean, and
  string values that are immediately followed by a delimiter (`,` or `}`) fused
  into the same token transition directly to `EXPECT_KEY`/`DONE` rather than
  deferring to a separate `EXPECT_SEPARATOR` state — deferring caused a stale,
  already-consumed delimiter to corrupt the next transition (see Challenges Faced).
- **Prompt includes function context and two worked examples.** Constrained
  decoding only guarantees valid *structure*; it has no influence over which
  function or values the model *intends* to pick. The prompt sent to the model
  explicitly lists available functions and includes two fixed examples: one
  demonstrating direct value extraction (e.g. a name from a greeting request),
  and one demonstrating pattern synthesis (e.g. a regex that matches a whole
  category rather than copying a literal substring from the input).

## Performance Analysis

- **Validity**: 100% of generated outputs are valid, schema-compliant JSON — this
  is a structural guarantee of the masking approach, not a statistical outcome.
- **Accuracy**: across an 11-prompt test set, function selection and argument
  extraction were correct in the large majority of cases. The main remaining
  source of error is semantic: the 500M-parameter model can reason poorly about
  abstract patterns (e.g. regex synthesis). This reflects the model's capability
  ceiling, not a defect in the constrained decoding mechanism, which cannot
  enforce semantic correctness by design.
- **Speed**: the full test set completes well within the required 5-minute budget.

## Challenges Faced

- **Special/control tokens outside the loaded vocabulary.** The model would
  occasionally select a token id (e.g. an end-of-sequence token) with no entry in
  the vocabulary file, causing a `KeyError`. Root cause: masking logic only
  visited tokens present in the vocab dict, so ids outside it were never
  evaluated and stayed unmasked by omission. Fixed by explicitly masking every
  token id not found in the vocabulary as an unconditional first step.
- **Stale delimiter corruption.** When a numeric or string value's closing
  delimiter (`,`/`}`) arrived fused with the preceding token, an early
  implementation detected but did not consume it, deferring to a later state that
  then encountered — and mishandled — the leftover character. This silently
  desynchronized the state machine, causing it to reject a valid subsequent key
  and hang until the step limit was reached. Fixed by transitioning directly and
  consuming the delimiter as soon as it is detected in the current buffer.
- **Every prompt converging on the same function.** All prompts, regardless of
  content, were resolving to the same function. Root cause: the raw prompt text
  was encoded directly, with no information about the available functions ever
  reaching the model — constrained decoding restricted the model to *valid*
  function names, but gave it no signal for *which* valid name matched the
  request. Fixed by constructing a full prompt including function descriptions
  and a worked example before encoding.
- **Premature object closure.** An early separator-masking rule allowed both `,`
  and `}` whenever any required key remained unfilled, rather than restricting to
  `,` only in that case. This allowed the model to close an object before all
  required parameters were generated. Fixed by making `}` illegal whenever
  unfilled required keys remain.

## Testing Strategy

The implementation was validated primarily through direct token-by-token tracing:
each selected token id and its decoded string were logged during generation,
allowing state-machine bugs (stuck states, corrupted buffers, premature
transitions) to be diagnosed precisely rather than inferred from final output
alone. The provided 11-prompt test set was run end-to-end after each fix to
confirm both that generation completed without error and that the resulting JSON
was structurally and semantically reasonable. Edge cases specifically exercised
included: multi-parameter functions, string values containing embedded escaped
quotes, and functions requiring more than one required argument.

## Example Usage

```bash
uv run python -m src \
  --functions_definition data/input/functions_definition.json \
  --input data/input/function_calling_tests.json \
  --output data/output/function_calling_results.json
```

Sample input (`function_calling_tests.json`):
```json
[
  {"prompt": "What is the sum of 2 and 3?"},
  {"prompt": "Greet john"}
]
```

Sample output (`function_calling_results.json`):
```json
[
  {
    "prompt": "What is the sum of 2 and 3?",
    "name": "fn_add_numbers",
    "parameters": {"a": 2.0, "b": 3.0}
  },
  {
    "prompt": "Greet john",
    "name": "fn_greet",
    "parameters": {"name": "john"}
  }
]
```

## Resources

- [Hugging Face — Tokenizer Summary](https://huggingface.co/docs/transformers/tokenizer_summary) —
  background on subword tokenization (BPE/SentencePiece) and why tokens don't
  align with characters; directly relevant to building the vocabulary lookup
  in `load_vocab` and the token-level prefix/mask checks in `filter_tokens`.

- [Bycroft — LLM Visualization](https://bbycroft.net/llm) —
  interactive 3D walkthrough of a GPT-style transformer's internals
  (embeddings, attention heads, MLP layers, logits), useful for grounding
  the generation pipeline (`get_logits_from_input_ids`) in the actual
  architecture producing those logits.

- (https://youtu.be/U2hZFMVNSE0) —

- (https://youtu.be/zduSFxRajkE) —

- (https://youtu.be/wjZofJX0v4M) —

### AI Usage

## AI Usage

AI was used throughout this project as a debugging and conceptual-explanation
partner, Its main uses were: walking through the constrained
decoding and JSON state machine logic before implementation, diagnosing bugs from pasted
error output and code (e.g. the empty-mask crash on zero-parameter functions, the
premature object closure, the generation-stall issue), and reviewing/critiquing draft
code changes I wrote myself. All final implementation decisions and code were written and
understood by me; AI was not used to generate the solution wholesale.

