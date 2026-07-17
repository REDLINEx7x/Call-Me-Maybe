# Src Verification Report (Against Subject PDF)

Date: 2026-07-17

## Subject used for validation

- Readable PDF used: `/home/redline/Downloads/en.subject.pdf`
- Corrupted PDF still present: `en.subject_call_maybe.pdf` (unreadable)

## Scope checked

- `src/__main__.py`
- `src/args_parse.py`
- `src/decoder.py`
- `src/models.py`
- `src/utils.py`

## Quick status

- **Current status:** Project is **not complete** for mandatory requirements.
- **Main reason:** End-to-end execution path is broken by import/signature/name errors, and output generation is not fully implemented.

## Done vs Missing (mandatory requirements)

### 1) Input validation and parsing
- ✅ Prompt/function JSON loading with validation exists (`utils.py`).
- ⚠️ `load_prompts` returns `PromptModel` objects, but `__main__.py` treats items like dicts (`prompt.get(...)`), causing runtime failure.

### 2) LLM-based function selection
- ⚠️ Partial skeleton exists (selection phase in `decoder.py`), but currently broken:
  - undefined variables (`valid_names`, `valid_function_names`, `vocabm`)
  - typo variables (`genertaed_txt`/`generated_txt`)
  - inconsistent function arguments between caller/callee

### 3) Constrained decoding (schema-safe JSON)
- ⚠️ State machine and token filter structure exist, but implementation is not runnable due to undefined names and mismatched variables (`token_text` vs `token_txt`, etc.).
- ⚠️ No proven 100% valid JSON output path yet.

### 4) Output format (`prompt`, `name`, `parameters`)
- ❌ Not implemented end-to-end:
  - no correct result object assembly per required keys
  - no reliable write to `data/output/function_calling_results.json`

### 5) CLI usage (`python -m src ...`)
- ❌ Entry point currently broken:
  - invalid imports in `__main__.py` (`from ..llm_sdk`, `from decoder`)
  - undefined variable `result` used
  - broad exception block hides real errors

### 6) Error handling robustness
- ⚠️ Some graceful handling exists in loaders.
- ❌ Critical execution path still crashes before meaningful handling.

## Concrete issues in `src` to complete

1. `src/args_parse.py` is empty (either implement and use it, or remove and keep argparse cleanly in `__main__.py`).
2. `src/__main__.py`:
   - fix import paths
   - stop treating Pydantic models as dicts
   - fix wrong function-call signature for decoder
   - replace `result`/`results` mismatch
   - implement output writing logic
3. `src/decoder.py`:
   - resolve all undefined/misspelled identifiers
   - align state machine + filter function arguments
   - ensure deterministic stop criteria and valid JSON object emission
4. `src/utils.py`:
   - `load_vocab(model: Small_LLM_Model)` uses `Small_LLM_Model` annotation without importing it (runtime issue in current form).

## What needs improvement (priority)

1. **Runability first:** fix imports + undefined names so `python -m src` runs.
2. **Contract consistency:** align function signatures and call sites (`__main__` ↔ `decoder`).
3. **Output compliance:** enforce exact required output schema for each prompt.
4. **Constrained decoding reliability:** guarantee schema-safe token masking and valid termination.
5. **Quality gates:** pass flake8 + mypy and test with changed input files/edge cases from subject.

## Verification commands run

- `python3 -m compileall src` ✅ (syntax only)
- Runtime execution could not be fully validated in this environment because required tooling/dependencies are missing (`uv`, `pydantic` not installed in current shell).
