import streamlit as st
import typing as t
from prompt import (
    supported_programs,
    SpecResult,
    CheckPayload,
    check,
    SecurityCheckProgram,
)
from utils import (
    normalize_text,
    read_as_plain_text,
    patch_script_thread_eventloop_if_needed,
)


def initialize_state():
    if "analyzing" not in st.session_state:
        st.session_state.analyzing = False

    if "results" not in st.session_state:
        st.session_state.results = []

    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4"


def has_openai_api_key_secret() -> bool:
    if "OPENAI_API_KEY" in st.secrets and st.secrets.OPENAI_API_KEY:
        return True
    return False


def openai_api_key() -> t.Optional[str]:
    if "openai_api_key" in st.session_state and st.session_state.openai_api_key:
        return st.session_state.openai_api_key

    if "OPENAI_API_KEY" in st.secrets and st.secrets.OPENAI_API_KEY:
        return st.secrets.OPENAI_API_KEY

    return None


def must_resolve_openai_api_key() -> str:
    t = openai_api_key()
    if not t:
        st.error("No OpenAPI token set, please provide via the OpenAI Token input")
    return t


def ask_openai(spec: str):
    payload = CheckPayload(
        openapi_key=must_resolve_openai_api_key(),
        model=st.session_state.openai_model,
        spec=spec,
    )

    _selected_programs = selected_programs()
    print(f"Selected programs: {_selected_programs}")

    patch_script_thread_eventloop_if_needed()
    st.session_state.results = check(_selected_programs, payload)
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

    if len(selected_programs()) < 1:
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


# source: https://icons.getbootstrap.com/icons/github/
# license: MIT
_github_link = """
<div style="display: flex; align-items: center; margin-bottom: 1rem">
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-github" viewBox="0 0 16 16">
<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
</svg>
<a style="margin-left: 8px" href="https://github.com/b4fun/seckubegpt">b4fun/seckubegpt</a>
</div>
"""


def ui_title():
    st.title(f"🙈 SecKubeGPT")
    st.caption("Your Kubernetes GPT Security Power Pack Has Arrived!")
    st.markdown(_github_link, unsafe_allow_html=True)


def ui_openai_api_key():
    st.write("### Before we start...")
    st.write(
        "Please provide your OpenAI token. "
        "If you do not have one, you can get one [here](https://platform.openai.com/account/api-keys)."
    )
    st.write("We guarantee that your token will not be stored anywhere.")
    st.text_input(
        "OpenAI Token (sk-xxx)",
        key="openai_api_key",
        type="password",
    )


_sample_spec = """
apiVersion: v1
kind: Pod
metadata:
  name: sec-kube-gpt-demo
spec:
  hostNetwork: true
  containers:
  - name: busybox
    image: busybox
    command: ["sh", "-c", "sleep 1h"]
""".strip()


def ui_input_source():
    st.write("### 1. Provide some Kubernetes specs")
    tab_text_area, tab_file_upload = st.tabs(["From String", "From Files"])
    with tab_text_area:
        if st.button("Load Sample"):
            st.session_state.spec = _sample_spec
            st.experimental_rerun()
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

    (tab_programs, tab_openai) = st.tabs(["Programs", "OpenAI"])
    with tab_programs:
        st.caption(
            "Each program defines a collection of security checks to run on the provided spec. "
            "At least one program must be selected."
        )
        for program in supported_programs:
            st.checkbox(
                label=program.name,
                key=program_as_key(program),
                value=True,
                help=program.help,
            )

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


program_key_prefix = "__program_"


def program_as_key(program: SecurityCheckProgram) -> str:
    return f"{program_key_prefix}{program.id}"


def selected_programs() -> t.List[SecurityCheckProgram]:
    rv = []
    for program in supported_programs:
        key = program_as_key(program)
        if key in st.session_state and st.session_state[key]:
            rv.append(program)
    return rv


def ui_analyze_results():
    st.write("### 3. Results")
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

if not has_openai_api_key_secret():
    ui_openai_api_key()

ui_input_source()
ui_analyze_settings()
ui_analyze_results()
