import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import image_analyzer_config as config
from io import BytesIO
from datetime import datetime
import base64
import markdown
import os
from dotenv import load_dotenv

# ==========================================
# 1. 설정
# ==========================================
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# ==========================================
# 2. 화면 구성
# ==========================================
st.set_page_config(
    page_title="애니톡 그림 분석기", 
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바 항상 표시 (접기 버튼 숨김)
st.markdown("""
<style>
    [data-testid="collapsedControl"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.title("애니톡 만화학원")
    st.caption("by 애니톡 기획실")
    st.markdown("---")
    st.subheader("그림 분석기")
    
    selected_analyzer = st.radio(
        "분석 유형을 선택하세요:",
        ["ANALYZER_1", "ANALYZER_2", "ANALYZER_3"],
        format_func=lambda x: getattr(config, f"{x}_NAME")
    )
    
    st.markdown("---")
    if st.button("분석 기록 지우기 🗑️"):
        st.session_state.analysis_result = None
        st.rerun()

# 메인 타이틀
st.title(f"🔍 {getattr(config, f'{selected_analyzer}_NAME')}")

# ==========================================
# 3. 모델 설정
# ==========================================
system_instruction = getattr(config, f"{selected_analyzer}_INSTRUCTION")

# ==========================================
# 4. 입력 영역
# ==========================================
st.markdown("### 📤 그림을 업로드하고 설명을 입력하세요")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader(
        "그림 파일 업로드 (PNG, JPG)",
        type=["png", "jpg", "jpeg"],
        help="분석할 그림을 업로드하세요"
    )
    if uploaded_file:
        st.image(uploaded_file, caption="업로드된 이미지", use_container_width=True)

with col2:
    st.markdown("**실기 주제 입력 (선택사항)**")
    subject_tab1, subject_tab2 = st.tabs(["✏️ 텍스트로 입력", "🖼️ 이미지로 입력"])
    
    with subject_tab1:
        description = st.text_area(
            "주제 직접 입력",
            height=150,
            placeholder="예: 여기에 실기주제를 넣으면 더 자세히 분석합니다",
            label_visibility="collapsed"
        )
    
    with subject_tab2:
        subject_image = st.file_uploader(
            "주제 이미지 업로드",
            type=["png", "jpg", "jpeg"],
            help="실기 주제가 적힌 이미지를 업로드하면 자동으로 텍스트를 추출합니다",
            key="subject_uploader"
        )
        if subject_image:
            st.image(subject_image, caption="주제 이미지", use_container_width=True)
            # 이미지에서 텍스트 추출
            if st.button("📖 주제 텍스트 추출", key="extract_btn"):
                with st.spinner("🔍 이미지에서 주제를 읽는 중..."):
                    try:
                        ocr_model = genai.GenerativeModel(model_name="gemini-flash-latest")
                        subject_bytes = subject_image.getvalue()
                        ocr_response = ocr_model.generate_content([
                            "이 이미지에 적힌 실기 주제 또는 지문 내용을 정확하게 추출해서 텍스트로 알려줘. 다른 설명 없이 주제 내용만 출력해.",
                            {"mime_type": subject_image.type, "data": subject_bytes}
                        ])
                        extracted_text = ocr_response.text
                        st.session_state.extracted_subject = extracted_text
                        st.success("✅ 주제 추출 완료!")
                        st.text_area("추출된 주제:", value=extracted_text, height=100, disabled=True)
                    except Exception as e:
                        st.error(f"⚠️ 추출 실패: {e}")

# 최종 주제 결정 (텍스트 입력 > 추출된 주제)
final_description = description if description else st.session_state.get("extracted_subject", "")

# ==========================================
# 5. 분석 버튼 & 결과
# ==========================================
if st.button("🔍 분석 시작", type="primary", use_container_width=True):
    if uploaded_file is None:
        st.error("⚠️ 그림을 업로드해주세요!")
    else:
        with st.spinner("🎨 교수님이 그림을 꼼꼼히 보고 계십니다..."):
            try:
                # 이미지 준비
                image_bytes = uploaded_file.getvalue()
                
                # Gemini Vision 모델 호출
                model = genai.GenerativeModel(
                    model_name="gemini-flash-latest",
                    system_instruction=system_instruction
                )
                
                # 프롬프트 구성
                prompt_text = "이 그림을 분석해주세요."
                if final_description:
                    prompt_text += f"\n\n학생이 제공한 실기 주제:\n{final_description}"
                
                # 이미지와 함께 전송
                response = model.generate_content([
                    prompt_text,
                    {"mime_type": uploaded_file.type, "data": image_bytes}
                ])
                
                analysis_result = response.text
                st.session_state.analysis_result = analysis_result
                st.session_state.analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.analyzer_name = getattr(config, f'{selected_analyzer}_NAME')
                
            except Exception as e:
                st.error(f"⚠️ 분석 중 에러 발생: {e}")

# ==========================================
# 6. 리포트 카드 출력 (HTML만)
# ==========================================
if "analysis_result" in st.session_state and st.session_state.analysis_result:
    st.markdown("---")
    
    # 마크다운을 HTML로 변환 (테이블 지원)
    formatted_result = markdown.markdown(
        st.session_state.analysis_result,
        extensions=['tables', 'fenced_code', 'nl2br']
    )
    
    report_html = f"""
    <style>
        .report-card h1, .report-card h2, .report-card h3 {{
            color: #ffa500;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .report-card h1 {{ font-size: 24px; border-bottom: 2px solid #ffa500; padding-bottom: 10px; }}
        .report-card h2 {{ font-size: 20px; }}
        .report-card h3 {{ font-size: 16px; }}
        .report-card strong {{ color: #ffa500; }}
        .report-card table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            overflow: hidden;
        }}
        .report-card th {{
            background: rgba(255,165,0,0.2);
            color: #ffa500;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #ffa500;
        }}
        .report-card td {{
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .report-card tr:hover {{ background: rgba(255,165,0,0.1); }}
        .report-card ul, .report-card ol {{ margin: 10px 0; padding-left: 20px; }}
        .report-card li {{ margin: 5px 0; }}
        .report-card p {{ margin: 10px 0; line-height: 1.8; }}
        .report-card hr {{ border: none; border-top: 1px solid #ffa500; margin: 20px 0; }}
    </style>
    <div class="report-card" style="
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 20px;
        padding: 30px;
        color: white;
        font-family: 'Pretendard', sans-serif;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        border: 1px solid #ffa500;
        margin-top: 20px;
    ">
        <div style="text-align: center; margin-bottom: 25px;">
            <h1 style="color: #ffa500; margin: 0; font-size: 28px;">🎨 애니톡 만화학원</h1>
            <p style="color: #888; font-size: 14px; margin-top: 5px;">그림 분석 리포트</p>
        </div>
        
        <div style="display: flex; gap: 15px; margin-bottom: 20px;">
            <div style="
                flex: 1;
                background: rgba(255,165,0,0.1);
                border-radius: 10px;
                padding: 15px;
                border-left: 4px solid #ffa500;
            ">
                <p style="margin: 0; color: #ffa500; font-weight: bold; font-size: 12px;">📌 분석 유형</p>
                <p style="margin: 5px 0 0 0; font-size: 16px;">{st.session_state.analyzer_name}</p>
            </div>
            <div style="
                flex: 1;
                background: rgba(255,255,255,0.05);
                border-radius: 10px;
                padding: 15px;
            ">
                <p style="margin: 0; color: #ffa500; font-weight: bold; font-size: 12px;">📅 분석 일시</p>
                <p style="margin: 5px 0 0 0; font-size: 16px;">{st.session_state.analysis_time}</p>
            </div>
        </div>
        
        <div style="
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 20px;
        ">
            <p style="margin: 0 0 15px 0; color: #ffa500; font-weight: bold;">📝 분석 내용</p>
            <div style="line-height: 1.8; font-size: 14px;">{formatted_result}</div>
        </div>
        
        <div style="text-align: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid #333;">
            <p style="color: #666; font-size: 12px; margin: 0;">by 애니톡 기획실 | Powered by Gemini AI</p>
        </div>
        
        <!-- 스크린샷 버튼 -->
        <div style="text-align: center; margin-top: 20px;">
            <button id="screenshotBtn" style="
                background: linear-gradient(135deg, #ffa500 0%, #ff6b00 100%);
                color: white;
                border: none;
                padding: 15px 40px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(255,165,0,0.4);
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                📸 리포트 이미지 저장
            </button>
        </div>
    </div>
    
    <!-- html2canvas 라이브러리 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
        document.getElementById('screenshotBtn').addEventListener('click', function() {{
            const reportCard = document.querySelector('.report-card');
            this.textContent = '⏳ 이미지 생성 중...';
            this.disabled = true;
            
            html2canvas(reportCard, {{
                backgroundColor: '#1a1a2e',
                scale: 2,
                useCORS: true
            }}).then(canvas => {{
                const link = document.createElement('a');
                link.download = 'anitok_report_{st.session_state.analysis_time.replace("-", "").replace(":", "").replace(" ", "_")}.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
                
                document.getElementById('screenshotBtn').textContent = '📸 리포트 이미지 저장';
                document.getElementById('screenshotBtn').disabled = false;
            }});
        }});
    </script>
    """
    
    # components.html로 확실하게 렌더링
    components.html(report_html, height=900, scrolling=True)



