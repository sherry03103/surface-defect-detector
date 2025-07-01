import streamlit as st
import requests
from PIL import Image, ImageDraw
import io
import pandas as pd

# Roboflow 설정
ROBOFLOW_API_KEY = "bq6CaytImULcYO8MdkW5"
PROJECT_NAME = "capston-fzvww"
PROJECT_VERSION = "2"
upload_url = f"https://detect.roboflow.com/{PROJECT_NAME}/{PROJECT_VERSION}?api_key={ROBOFLOW_API_KEY}"

st.title("🔍 표면결함 정적탐지 AI 시스템 by HINT")
st.write("업로드한 이미지를 기반으로 도금막 표면의 결함을 AI가 분석합니다. 결과 이미지를 시각화하고 CSV 파일로 저장할 수 있습니다.")

# 이미지 업로드
uploaded_file = st.file_uploader("이미지를 선택하세요", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 원본 이미지 열기
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="업로드된 이미지", use_container_width=True)

    # 이미지 바이트 변환
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_bytes = buffered.getvalue()

    # API 요청
    with st.spinner("AI가 결함을 탐지 중입니다..."):
        response = requests.post(
            upload_url,
            files={"file": ("image.jpg", img_bytes, "image/jpeg")}
        )

    if response.status_code == 200:
        result = response.json()
        st.subheader("📄 AI 응답 JSON")
        st.json(result)

        predictions = result.get("predictions", [])

        if predictions:
            # 이미지 복사 + 박스 그리기
            draw_img = image.copy()
            draw = ImageDraw.Draw(draw_img)

            # CSV용 리스트 만들기
            data = []

            for pred in predictions:
                x = pred["x"]
                y = pred["y"]
                w = pred["width"]
                h = pred["height"]
                cls = pred["class"]
                conf = pred["confidence"]

                # 박스 그리기
                x0 = x - w / 2
                y0 = y - h / 2
                x1 = x + w / 2
                y1 = y + h / 2

                draw.rectangle([x0, y0, x1, y1], outline="red", width=3)
                draw.text((x0, y0 - 10), f"{cls} ({conf:.2f})", fill="red")

                # CSV용 데이터 추가
                data.append({
                    "class": cls,
                    "confidence": round(conf, 3),
                    "x": round(x),
                    "y": round(y),
                    "width": round(w),
                    "height": round(h)
                })

            # 결과 이미지 표시
            st.subheader("📸 탐지 결과 이미지")
            st.image(draw_img, caption="탐지된 결함", use_container_width=True)

            # 이미지 다운로드 버튼 (JPG)
            img_buffer = io.BytesIO()
            draw_img.save(img_buffer, format="JPEG")
            st.download_button(
                label="📥 탐지 이미지 다운로드 (JPG)",
                data=img_buffer.getvalue(),
                file_name="defect_detection_result.jpg",
                mime="image/jpeg"
            )

            # CSV 생성 및 다운로드 버튼
            df = pd.DataFrame(data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📊 결함 결과표 다운로드 (CSV)",
                data=csv_buffer.getvalue(),
                file_name="defect_detection_results.csv",
                mime="text/csv"
            )

        else:
            st.warning("⚠️ 탐지된 결함이 없습니다. 다른 이미지를 시도해보세요.")

    else:
        st.error(f"❌ 오류 발생: 상태 코드 {response.status_code}")
        st.text("서버 응답:")
        st.code(response.text)
