import pandas as pd
import streamlit as st
import io
from tqdm import tqdm
import requests
import json
import re

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

uploaded_file = st.file_uploader("아래에 평가를 위한 엑셀 파일을 업로드해주세요.", type=['xlsx'])

if uploaded_file is not None:
    data_df = pd.read_excel(uploaded_file)
    save_df = pd.DataFrame(columns=['입력', '예상 답변', '답변', '점수'])

    user_input = st.text_area("시스템 프롬프트를 입력하세요:", height=200)
    
    if user_input:
        port = st.text_input("포트를 입력하세요:", value="http://211.39.140.232:9090/v1/chat/completions")
        
        if port:
            temperature = st.text_input("temperature 값을 입력하세요:", value="0")
            
            if temperature:
                frequency_penalty = st.text_input("frequency_penalty 값을 입력하세요:", value="1")
                
                if frequency_penalty:
                    for index, data in tqdm(data_df.iterrows()):
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
else:
    st.write("엑셀 파일을 업로드 해주세요.")
