# -*- coding: utf-8 -*-
import pandas as pd
import json
import requests
import streamlit as st
import io

def LCS(s1, s2):
    m = [[0] * (1 + len(s2)) for _ in range(1 + len(s1))]
    for x in range(1, 1 + len(s1)):
        for y in range(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
            else:
                m[x][y] = max(m[x - 1][y], m[x][y - 1])
    return round(m[len(s1)][len(s2)]/len(s2),2)

st.title("Automatic Evaluator") # app 제목

@st.cache_data
def convert_df(df):
    output = io.BytesIO() # BytesIO buffer 생성
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer: # pandas ExcelWriter 파일 버퍼로 사용
        df.to_excel(writer, index=False)
    output.seek(0) # 시작 지점으로 돌아감
    return output.getvalue()

if 'result_file' not in st.session_state:
    st.session_state['result_file'] = None
    
# 다운로드 버튼을 배치하는 함수
def button_placeholder(key):
    result_file = st.session_state.get('result_file', None)
    if result_file is not None:
        st.download_button("결과저장", result_file, "result.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=key)
    else:
        pass
    
button_placeholder("평가중")

uploaded_file = st.file_uploader("아래에 엑셀 파일을 업로드해주세요.", type=['xlsx']) # streamlit에서 업로드할 파일 불러옴

if uploaded_file is not None:
    data_df = pd.read_excel(uploaded_file) # pd 메서드를 이용해서 변수로 파일 저장
    save_df = pd.DataFrame(columns=['입력','생성형 답변','예상 답변','생성형 점수','추출형 답변','추출형 점수'])
    
    server_num = '29'
    torchserve_address = f'211.39.140.{server_num}:9090'
    model_endpoint = "qa"  # TorchServe에 등록된 모델의 엔드포인트  
    torchserve_host = f"http://{torchserve_address}/predictions/{model_endpoint}"  # TorchServe가 실행 중인 호스트 및 포트

    
    for index,data in data_df.iterrows():
        try:
            input_data = eval(data['입력'])
            label = data['예상 답변']
            request_data = json.dumps(input_data) # Torchserve에 보낼 JSON 형식의 요청 데이터 생성

            response = requests.post(torchserve_host, data=request_data)
        except:
            st.error(f"Error in input data at row {index}")
            continue
        if response.status_code == 200:
            result = response.json()
            gen = result['choices'][0]['message']['content'][0][0]
            ext = result['choices'][0]['message']['content'][1][0]
            gen_scr = LCS(label,gen)
            ext_scr = LCS(label,ext)
            save_df.loc[len(save_df)] = [input_data,gen,label,gen_scr,ext,ext_scr]
        else:
            st.error(f"Failed to get response from model server for row {index}")
        
        st.write(save_df.tail(1)) # Sample_result.xlsx 대신 저장할 엑셀 파일명 입력
        
    if not save_df.empty:
        result_file = convert_df(save_df)
        st.session_state['result_file'] = result_file
        button_placeholder("평가완료")

    # 결과 파일 다운로드 버튼 생성 및 다운로드 버튼에 넣을 문구 표기
    st.write("평가 완료")
else:
    st.write("엑셀 파일을 업로드 해주세요.")