import streamlit as st
import typing as t
from prompt import get_pss_results_from_openai


def normalize_text(s: t.Optional[str]) -> str:
    if not s:
        return ''
    return s.strip()


st.title('Pod Security Standard with GPT')

if 'analyzing' not in st.session_state:
    st.session_state.analyzing = False

if 'result' not in st.session_state:
    st.session_state.result = ''

if 'openai_model' not in st.session_state:
    st.session_state.openai_model = 'gpt-3.5-turbo'


def ask_openai(spec: str):
    if 'OPENAI_TOKEN' not in st.secrets:
        st.error('OPENAI_TOKEN secret is not set')
        return

    model = st.session_state.openai_model

    try:
        st.session_state.result = get_pss_results_from_openai(
            st.secrets.OPENAI_TOKEN,
            model,
            spec,
        )
    except Exception as e:
        st.session_state.result = f'{e}'
        st.error('error running OpenAI API')


def do_analyze():
    if st.session_state.analyzing:
        # already running...
        return
    st.session_state.analyzing = True

    try:
        spec_content = normalize_text(st.session_state.spec)
        if not spec_content:
            st.error('spec is empty')
            return

        ask_openai(spec_content)
    finally:
        st.session_state.analyzing = False


left_column, right_column = st.columns(2)
    
with left_column:
    st.text_area('Spec', key='spec')
    st.button(
        'Analyze',
        disabled=st.session_state.analyzing,
        on_click=do_analyze,
    )


with right_column:
    if s := normalize_text(st.session_state.result):
        st.markdown(s)