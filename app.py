"""FixForge AI: explain coding errors, suggest fixes, generate tests, and verify them."""

import difflib
import os

import streamlit as st
from dotenv import load_dotenv

from llm import DEFAULT_MODEL, analyze
from runner import run_pytest

load_dotenv()

st.set_page_config(page_title="FixForge AI", page_icon="🛠️", layout="wide")

SAMPLE_CODE = """def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)


print(factorial("5"))
"""
SAMPLE_ERROR = "TypeError: unsupported operand type(s) for -: 'str' and 'int'\n  at line 4"

# Initialise widget state once, so edits survive reruns.
st.session_state.setdefault("code", SAMPLE_CODE)
st.session_state.setdefault("error", SAMPLE_ERROR)
st.session_state.setdefault("result", None)
st.session_state.setdefault("test_results", None)

st.title("FixForge AI")
st.caption("Understand • Fix • Test • Verify: plain-English debugging, powered by NVIDIA Nemotron via Nebius.")

with st.sidebar:
    st.header("How it works")
    st.markdown(
        "1. Paste your Python code and the error message.\n"
        "2. Read a plain-English explanation and a minimal fix.\n"
        "3. Run the generated tests against your original and fixed code."
    )
    st.divider()
    st.caption(f"Model: `{os.getenv('NEBIUS_MODEL', DEFAULT_MODEL)}`")
    if not os.getenv("NEBIUS_API_KEY"):
        st.warning("NEBIUS_API_KEY is not set. Add it to your .env file before analyzing.")

left, right = st.columns(2)
with left:
    st.subheader("Your code")
    st.text_area("Code", key="code", height=260, label_visibility="collapsed")
with right:
    st.subheader("Error message")
    st.text_area("Error", key="error", height=260, label_visibility="collapsed")

if st.button("Get AI Analysis", type="primary"):
    if not st.session_state.code.strip() or not st.session_state.error.strip():
        st.error("Paste both your code and the error message first.")
    else:
        with st.spinner("Nemotron is reading your code..."):
            try:
                st.session_state.result = analyze(st.session_state.code, st.session_state.error)
                st.session_state.test_results = None
            except Exception as exc:  # show a readable message instead of a stack trace
                st.session_state.result = None
                st.error(f"Analysis failed: {exc}")

result = st.session_state.result
if result:
    st.subheader("What went wrong")
    st.markdown(result["explanation"])
    st.markdown(f"**Root cause:** {result['root_cause']}")

    tab_fix, tab_tests = st.tabs(["Suggested fix", "Generated tests"])

    with tab_fix:
        diff_lines = difflib.unified_diff(
            st.session_state.code.splitlines(),
            result["fixed_code"].splitlines(),
            fromfile="your_code.py",
            tofile="fixed_code.py",
            lineterm="",
        )
        st.code("\n".join(diff_lines) or "No changes suggested.", language="diff")
        st.markdown(result["changes"])
        st.code(result["fixed_code"], language="python")

    with tab_tests:
        st.code(result["tests"], language="python")
        if st.button("Run tests", type="primary"):
            with st.spinner("Running tests in a clean temporary folder..."):
                before = run_pytest(st.session_state.code, result["tests"])
                after = run_pytest(result["fixed_code"], result["tests"])
            st.session_state.test_results = (before, after)

    if st.session_state.test_results:
        before, after = st.session_state.test_results
        col1, col2 = st.columns(2)
        col1.metric("Original code", f"{before['passed']} passed, {before['failed']} failed")
        col2.metric("Fixed code", f"{after['passed']} passed, {after['failed']} failed")

        if after["ok"]:
            st.success("Verified: the fixed code passes every generated test.")
        else:
            st.error("The fixed code did not pass every test. Check the output below.")

        with st.expander("Test output"):
            st.markdown("**Original code**")
            st.code(before["output"], language="text")
            st.markdown("**Fixed code**")
            st.code(after["output"], language="text")
