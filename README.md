<<<<<<< HEAD
# FixForge AI

A beginner-friendly debugging assistant. Paste Python code and an error message, and FixForge AI:

1. Explains the error in plain English (NVIDIA Nemotron via Nebius).
2. Suggests a minimal fix, shown as a diff.
3. Generates pytest tests.
4. Runs the tests for real against the original and fixed code.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then add your NEBIUS_API_KEY
streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501).

## Project files

- `app.py`: Streamlit interface.
- `llm.py`: sends code and error to Nemotron, then validates the JSON answer.
- `runner.py`: writes code and tests to a temp folder and runs pytest with a timeout.

## Things to check before the demo

- **Model ID:** The default is `nvidia/nemotron-3-ultra-550b-a55b`. Confirm the exact ID in your Nebius Token Factory console and set `NEBIUS_MODEL` in `.env` if it differs. Some third-party routers use different IDs such as `nebius/nvidia/...`, so don't assume.
- **Reasoning models:** Nemotron models can spend tokens on reasoning. If you see "empty answer" errors, raise `max_tokens` in `llm.py` or try a non-reasoning model via `NEBIUS_MODEL`.
- **Code execution is not a security sandbox:** generated code runs on your machine in a temp folder with a 15-second timeout. That's fine for a local demo. For a public deployment, run each test job in a container with no network access.
- **Python only:** explanations work for any language, but the test runner only runs Python.
=======
# FixForgeAI
FixForge AI is an AI-powered debugging assistant designed to help developers identify, understand, and fix coding errors.
>>>>>>> 63eb80ed68b4ac85d61b1102d08b02ae5d567049
