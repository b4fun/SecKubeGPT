import typing as t
import streamlit as st

def normalize_text(s: t.Optional[str]) -> str:
    if not s:
        return ''
    return s.strip()


st.title('Pod Security Standard with GPT')

if 'analyzing' not in st.session_state:
    st.session_state.analyzing = False

if 'error' not in st.session_state:
    st.session_state.error = ''

if st.session_state.error:
    st.error(st.session_state.error)


def set_error(error: str) -> None:
    st.session_state.error = error


def do_analyze():
    if st.session_state.analyzing:
        # already running...
        return
    st.session_state.analyzing = True
    set_error('')

    try:
        spec_content = normalize_text(st.session_state.spec)
        if not spec_content:
            set_error('spec is empty')
            return
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
    st.text_area(
        'Result',
        key='result',
        disabled=True,
    )
