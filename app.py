import pandas as pd
import streamlit as st
import io
from tqdm import tqdm
import requests
import json
import re
from time import sleep

def LCS(s1, s2):
    m = [[0] * (1 + len(s2)) for _ in range(1 + len(s1))]
    for x in range(1, 1 + len(s1)):
        for y in range(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
            else:
                m[x][y] = max(m[x - 1][y], m[x][y - 1])
    return round(m[len(s1)][len(s2)]/len(s2), 2)

st.title("Automatic Evaluator")

def clean_text(text):
    return re.sub(r'[^\w\s]', '', text)

def convert_df(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output.getvalue()

if 'result_file' not in st.session_state:
    st.session_state['result_file'] = None

if 'step' not in st.session_state:
    st.session_state['step'] = 0

uploaded_file = st.file_uploader("아래에 평가를 위한 엑셀 파일을 업로드해주세요.", type=['xlsx'])

if uploaded_file is not None and st.session_state['step'] == 0:
    data_df = pd.read_excel(uploaded_file)
    st.session_state['data_df'] = data_df
    save_df = pd.DataFrame(columns=['입력', '예상 답변', '답변', '점수'])
    st.session_state['save_df'] = save_df
    st.session_state['step'] = 1
    st.experimental_rerun()

if st.session_state['step'] == 1:
    user_input = st.text_area("시스템 프롬프트를 입력하세요:", height=200, value="다음 질문에 한국어로 답변해줘")
    if st.button("다음"):
        st.session_state['user_input'] = user_input
        st.session_state['step'] = 2
        st.experimental_rerun()

if st.session_state['step'] == 2:
    port = st.text_input("포트를 입력하세요:", value="http://211.39.140.232:9090/v1/chat/completions")
    if st.button("다음"):
        st.session_state['port'] = port
        st.session_state['step'] = 3
        st.experimental_rerun()

if st.session_state['step'] == 3:
    temperature = st.text_input("temperature 값을 입력하세요:", value="0")
    if st.button("다음"):
        st.session_state['temperature'] = temperature
        st.session_state['step'] = 4
        st.experimental_rerun()

if st.session_state['step'] == 4:
    frequency_penalty = st.text_input("frequency_penalty 값을 입력하세요:", value="1")
    if st.button("다음"):
        st.session_state['frequency_penalty'] = frequency_penalty
        st.session_state['step'] = 5
        st.experimental_rerun()

if st.session_state['step'] == 5:
    data_df = st.session_state['data_df']
    save_df = st.session_state['save_df']
    user_input = st.session_state['user_input']
    port = st.session_state['port']
    temperature = st.session_state['temperature']
    frequency_penalty = st.session_state['frequency_penalty']
    
    for index, data in tqdm(data_df.iterrows()):
        if (index + 1) % 10 == 0:
            sleep(3)
            st.write(f"3초간 프로세싱을 중단합니다.")
        try:
            input_data = clean_text(str(data['입력']))
            label = clean_text(str(data['예상 답변']))
        except Exception as e:
            st.write(f"{e} in index {index}")
        
        messages = [
            {"role": "system", "content": user_input},
            {"role": "user", "content": input_data}
        ]
        
        response = requests.post(port, 
            data=json.dumps({"model": "wisenut_llama", "messages": messages, "stream": False, "temperature": float(temperature), "frequency_penalty": float(frequency_penalty)}), 
            headers={"Content-Type": "application/json"},
            stream=False)
        
        if response.status_code == 200:
            response_data = response.json()
            try:
                message = response_data["choices"][0]["message"]["content"]
                score = LCS(label, message)
                save_df.loc[len(save_df)] = [input_data, label, message, score]
            except Exception as e:
                st.write(f"{index+1}행을 처리하는 도중 오류가 발생했습니다.: {e}")
        else:
            st.write(f"{index+1}번째 행 처리 중 오류가 발생했습니다. 상태 코드: {response.status_code}")
        st.write(f"{index+1}번째 행 처리중입니다.")
    
    if not save_df.empty:
        result_file = convert_df(save_df)
        st.download_button("결과저장", result_file, "result.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.write("평가 완료")
        uploaded_file = None
        st.session_state['step'] = 0
