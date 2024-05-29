# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import io
from tqdm import tqdm
import requests
import json
import textwrap

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

def convert_df(df):
    output = io.BytesIO() # BytesIO buffer 생성
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer: # pandas ExcelWriter 파일 버퍼로 사용
        df.to_excel(writer, index=False)
    output.seek(0) # 시작 지점으로 돌아감
    return output.getvalue()

if 'result_file' not in st.session_state:
    st.session_state['result_file'] = None

uploaded_file = st.file_uploader("아래에 평가를 위한 엑셀 파일을 업로드해주세요.", type=['xlsx']) # streamlit에서 업로드할 파일 불러옴

if uploaded_file is not None:
    data_df = pd.read_excel(uploaded_file) # sample.xlsx 대신 불러올 엑셀 파일명 입력 - 이 스크립트와 같은 폴더 내에 있어야 합니다.
    save_df = pd.DataFrame(columns=['입력','예상 답변','답변','점수'])

    user_input = st.text_area("시스템 프롬프트를 입력하세요:", height=200)
    if user_input:
        port = st.text_area("포트를 입력하세요:", height=200)
        # http://211.39.140.232:9090/v1/chat/completions
        if port:
            for index,data in tqdm(data_df.iterrows()):
                try:
                    input_data = eval(data['입력'])
                    label = data['예상 답변']
                except Exception as e:
                    st.write(f"{e} in index {index}")
                messages = [
                    {user_input}, {input_data}
                ]
                
                # POST 요청을 보내서 요약 결과를 가져옵니다.
                response = requests.post(
                    port,
                    data=json.dumps({"model": "wisenut_llama", "messages": messages, "stream": False}),
                    stream=False
                )
                
                prediction = []
                summary_placeholder = st.empty()  # 빈 위치 확보
                max_line_length = 50  # 한 줄에 표시할 최대 글자 수
                
                # 결과를 실시간으로 받아옵니다.
                for chunk in response.iter_content(chunk_size=None):
                    try:
                        chunk_data = chunk.decode("utf-8").strip()
                        if chunk_data:
                            # JSON 데이터에서 유효한 부분만 추출
                            json_data = chunk_data.split("data: ")[-1]
                            if json_data:
                                data = json.loads(json_data)
                                if "choices" in data and len(data["choices"]) > 0:
                                    message = data["choices"][0].get("delta", {}).get("content", "")
                                    if message:
                                        prediction.append(message)
                                        # 기존 내용에 새로 받은 내용을 추가하여 출력
                                        current_text = "".join(prediction)
                                        wrapped_text = "\n".join(textwrap.wrap(current_text, max_line_length))
                                        summary_placeholder.text(wrapped_text)
                    except json.JSONDecodeError as e:
                        pass
                    except Exception as e:
                        pass
                score = LCS(label,formats)
                answer = "".join(map(str, prediction))
                save_df.loc[len(save_df)] = [input_data,label,answer,score]
                st.text_area("요약 결과", "".join(prediction), height=200)
            else:
                st.warning("문서를 입력해주세요.")
            # 전체 요약 결과를 화면에 표시합니다.
        
    if not save_df.empty:
        result_file = convert_df(save_df)
        st.download_button("결과저장", result_file, "result.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        # 결과 파일 다운로드 버튼 생성 및 다운로드 버튼에 넣을 문구 표기
        st.write("평가 완료")
else:
    st.write("엑셀 파일을 업로드 해주세요.")
