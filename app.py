import json
import streamlit as st
import typing as t

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

    import openai
    openai.api_key = st.secrets.OPENAI_TOKEN

    prompt = '\n'.join([
        'Please detect potential security issues in the following Kubernetes spec.',
        'Please output the result as a JSON file. Your output should be a valid JSON.'
        'Don\'t explain your output.'
        'Your JSON output should be a list of object. Each object should have 3 fields, "Rule", "Message", and "Location".'
        'The "Location" field describes the source code location, while the "Message" field describes the security issue.'
        'If there is no security issue, please output empty JSON.'
        'If the input is invalid, return an empty JSON.',
        '',
        '',
        'input:',
        '```',
        f'{spec}',
        '```',
        'output:',
    ])

    print('=' * 80)
    print('prompt:')
    print(prompt)
    print('=' * 80)

    print('running...')

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {
                'role': 'system',
                'content': ('You are a helpful assistant that helps developers '
                            'detect potential security issues in their Kubernetes '
                            'YAML files using pod security standard.'),
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ],
        temperature=0.0,
    )
    response_content = response['choices'][0]['message']['content']
    print('=' * 80)
    print('response:')
    print(response_content)
    print('=' * 80)

    try:
        issue_dicts = json.loads(response_content)
        if len(issue_dicts) < 1:
            st.session_state.result = '😊 no security issue detected!'
            return

        result_table = '| Rule | Message | Location |\n|--|--|--|\n'
        for issue_dict in issue_dicts:
            rule_name = issue_dict.get('Rule')
            message = issue_dict.get('Message')
            location = json.dumps(issue_dict.get('Location'))
            result_table += f'| {rule_name} | {message} | {location} |\n'
        st.session_state.result = result_table

    except Exception as e:
        print('=' * 80)
        print('decode error:', e)
        print('=' * 80)

        # dump the full response for now
        st.session_state.result = f"Response from OpenAI:\n\n```\n{response_content}\n```"
        st.error('invalid JSON response returned from OpenAI...')
        return



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