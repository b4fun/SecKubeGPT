import streamlit as st
import typing as t
from prompt import PodSecurityStandard, SpecResult, CheckPayload
from utils import normalize_text, read_as_plain_text


def initialize_state():
    if "analyzing" not in st.session_state:
        st.session_state.analyzing = False

    if "results" not in st.session_state:
        st.session_state.results = []

    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-3.5-turbo"


def ask_openai(spec: str):
    if "OPENAI_TOKEN" not in st.secrets:
        st.error("OPENAI_TOKEN secret is not set")
        return

    payload = CheckPayload(
        openapi_key=st.secrets.OPENAI_TOKEN,
        model=st.session_state.openai_model,
        spec=spec,
    )

    st.session_state.results = [
        PodSecurityStandard().check(payload),
    ]
    print(st.session_state.results)


def get_analyze_content() -> t.Optional[str]:
    if len(st.session_state.spec_files) == 0:
        return normalize_text(st.session_state.spec)

    for f in st.session_state.spec_files:
        print(dir(f))

    return "---\n".join(
        s
        for f in st.session_state.spec_files
        if (s := normalize_text(read_as_plain_text(f)))
    )


def can_submit_analyze() -> bool:
    if st.session_state.analyzing:
        return False

    return True


def do_analyze():
    if not can_submit_analyze():
        return

    analyze_content = get_analyze_content()
    if not analyze_content:
        return

    st.session_state.analyzing = True

    try:
        ask_openai(analyze_content)
    finally:
        st.session_state.analyzing = False


def ui_title():
    st.title(
        "🙈 SecKubeGPT", help="your GPT powered Kubernetes security helper has arrived"
    )


def ui_input_source():
    st.write("### 1. Provide some Kubernetes specs")
    tab_text_area, tab_file_upload = st.tabs(["From String", "From Files"])
    with tab_text_area:
        st.text_area(
            "Spec",
            key="spec",
            height=400,
            help="If files upload is used, this will be ignored",
        )
    with tab_file_upload:
        st.file_uploader(
            "Upload your Kubernetes spec files",
            type=["yaml", "yml", "json"],
            key="spec_files",
            accept_multiple_files=True,
        )


def ui_analyze_settings():
    st.write("### 2. What settings to use?")

    (tab_openai,) = st.tabs(["OpenAI"])
    with tab_openai:
        st.selectbox(
            "OpenAI Model",
            [
                "gpt-3.5-turbo",
                "gpt-4",
            ],
            key="openai_model",
        )


def format_result_title(result: SpecResult) -> str:
    if result.has_issues:
        return f"🚨 {result.program_name}"

    return f"✅ {result.program_name}"


def ui_analyze_results():
    st.write("### 3. 🤔 Results")
    st.button(
        "Analyze",
        disabled=not can_submit_analyze(),
        on_click=do_analyze,
    )

    if not st.session_state.results:
        return

    result_tab_titles = [
        format_result_title(result) for result in st.session_state.results
    ]
    result_tabs = st.tabs(result_tab_titles)
    for idx, result in enumerate(st.session_state.results):
        with result_tabs[idx]:
            st.markdown(result.formatted_response)


initialize_state()
ui_title()
ui_input_source()
ui_analyze_settings()
ui_analyze_results()
