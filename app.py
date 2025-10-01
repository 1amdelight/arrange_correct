import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import random
import os
from pathlib import Path

# -----------------------------
# App Config
# -----------------------------
st.set_page_config(page_title="사진 순서 맞추기 - 초3 활동", page_icon="🍎", layout="wide")

# Constants
TOTAL_PROBLEMS = 3           # 고정 3문제
MAX_APPLES = 5               # 기회(사과) 5개
IMAGE_ROOT = Path("images")  # images/problem_1, images/problem_2 ... 폴더 구조 사용 권장

# -----------------------------
# Helpers
# -----------------------------
def load_problem_images(problem_index: int):
    """
    문제 폴더 구조:
    images/problem_1, images/problem_2, images/problem_3
    올바른 정답 순서는 파일명 오름차순으로 판단합니다.
    (예: 01_..., 02_..., 03_...)
    폴더가 없거나 비어 있으면, 플레이스홀더 이미지를 자동 생성합니다.
    """
    folder = IMAGE_ROOT / f"problem_{problem_index+1}"
    folder.mkdir(parents=True, exist_ok=True)
    
    image_files = sorted([p for p in folder.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"}])
    if not image_files:
        # 플레이스홀더 4장 자동 생성
        for i in range(1, 5):
            img = Image.new("RGB", (640, 400), (240, 240, 240))
            draw = ImageDraw.Draw(img)
            text = f"P{problem_index+1}-{i}"
            try:
                font = ImageFont.load_default()
            except:
                font = None
            w, h = draw.textbbox((0, 0), text, font=font)[2:]
            draw.text(((640 - w) / 2, (400 - h) / 2), text, fill=(0, 0, 0), font=font)
            outfile = folder / f"{i:02d}_placeholder.png"
            img.save(outfile)
        image_files = sorted([p for p in folder.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"}])
    
    # 정답(올바른 순서)은 파일명 오름차순
    correct_order = [p.name for p in image_files]
    # 표시용 이미지 로드
    images = [Image.open(p) for p in image_files]
    return images, correct_order, folder

def show_apples(apples_remaining: int):
    apple_bar = " ".join(["🍎"] * apples_remaining + ["⚪"] * (MAX_APPLES - apples_remaining))
    st.markdown(f"**기회(사과):** {apple_bar}")

def init_problem_state():
    if "problem_states" not in st.session_state:
        st.session_state.problem_states = [{} for _ in range(TOTAL_PROBLEMS)]
    for i in range(TOTAL_PROBLEMS):
        if "shuffled" not in st.session_state.problem_states[i]:
            st.session_state.problem_states[i]["shuffled"] = None

def reset_all():
    st.session_state.current_problem = 0
    st.session_state.apples = MAX_APPLES
    st.session_state.failed_problems = 0
    st.session_state.completed_problems = 0
    st.session_state.last_result = None  # "O" or "X" or None
    init_problem_state()

# -----------------------------
# Session State Init
# -----------------------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    reset_all()

if "current_problem" not in st.session_state:
    reset_all()

# 상단 헤더
st.title("📚 사진 순서 맞추기 (초등 3학년)")
st.caption("사진을 올바른 순서로 배열하면 **O**, 틀리면 **X**. 기회는 사과 5개! 사과가 모두 사라지면 다음 문제로 넘어갑니다. 3문제를 모두 틀리면 처음부터 다시 시작해요.")

# 컨트롤 바
with st.sidebar:
    st.header("교사용 설정")
    st.write("이미지 폴더 구조: `images/problem_1`, `images/problem_2`, `images/problem_3`")
    st.write("파일명 오름차순이 정답이 됩니다. (예: 01_..., 02_..., 03_...)")
    if st.button("🔄 전체 초기화(처음부터)"):
        reset_all()
        st.success("처음부터 다시 시작합니다.")

# 현재 문제 불러오기
problem_idx = st.session_state.current_problem
images, correct_order, folder = load_problem_images(problem_idx)
num_images = len(images)

# 문제 진행 표시
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.subheader(f"문제 {problem_idx+1} / {TOTAL_PROBLEMS}")
with col_b:
    show_apples(st.session_state.apples)
with col_c:
    if st.session_state.last_result is not None:
        if st.session_state.last_result == "O":
            st.success("정답! O")
        elif st.session_state.last_result == "X":
            st.error("오답! X")

# 셔플 상태 초기화
init_problem_state()
if st.session_state.problem_states[problem_idx]["shuffled"] is None:
    shuffled = correct_order.copy()
    random.shuffle(shuffled)
    st.session_state.problem_states[problem_idx]["shuffled"] = shuffled

shuffled_names = st.session_state.problem_states[problem_idx]["shuffled"]

# 이미지와 선택 UI
st.write("아래 사진을 보고, **위에서부터 1번, 2번, 3번... 순서**로 맞게 골라 보세요.")
thumb_cols = st.columns(num_images)
for i, (col, img, fname) in enumerate(zip(thumb_cols, images, correct_order)):
    with col:
        st.image(img, caption=f"정답순서 #{i+1} 힌트 아님 / 파일: {fname}", use_column_width=True)
st.caption("※ 교사용: 위 캡션의 파일명 오름차순이 정답입니다. 학생에게는 파일명이 보이지 않도록 이미지를 준비해 주세요.")

st.markdown("---")
st.subheader("순서 선택")

labels = [f"사진 {i+1}" for i in range(num_images)]
name_to_label = {name: label for name, label in zip(shuffled_names, labels)}
label_to_name = {v: k for k, v in name_to_label.items()}

if "choices" not in st.session_state:
    st.session_state.choices = {}
if problem_idx not in st.session_state.choices:
    st.session_state.choices[problem_idx] = [name_to_label[n] for n in shuffled_names]

chosen_labels = []
for pos in range(num_images):
    default_value = st.session_state.choices[problem_idx][pos]
    chosen = st.selectbox(
        label=f"{pos+1}번 자리에 올 사진을 고르세요",
        options=labels,
        index=labels.index(default_value) if default_value in labels else 0,
        key=f"select_{problem_idx}_{pos}"
    )
    chosen_labels.append(chosen)

if len(set(chosen_labels)) != len(chosen_labels):
    st.warning("⚠️ 같은 사진을 여러 칸에 넣었어요. 각 칸에 다른 사진을 선택해 주세요.")

submit = st.button("✅ 채점하기")

def go_next_problem(after_fail: bool = False):
    st.session_state.current_problem += 1
    st.session_state.apples = MAX_APPLES
    st.session_state.last_result = None
    if st.session_state.current_problem >= TOTAL_PROBLEMS:
        st.session_state.current_problem = 0
    init_problem_state()

if submit:
    user_order_names = [label_to_name[lab] for lab in chosen_labels]
    is_correct = user_order_names == correct_order
    
    if is_correct:
        st.session_state.last_result = "O"
        st.balloons()
        go_next_problem(after_fail=False)
    else:
        st.session_state.last_result = "X"
        st.session_state.apples -= 1
        if st.session_state.apples <= 0:
            st.session_state.failed_problems += 1
            st.warning("사과가 모두 사라졌어요. 다음 문제로 넘어갑니다.")
            go_next_problem(after_fail=True)
            if st.session_state.failed_problems >= TOTAL_PROBLEMS:
                st.error("3문제를 모두 틀렸어요. 처음부터 다시 합니다.")
                reset_all()

st.markdown("---")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("↩️ 현재 문제 다시 섞기"):
        shuffled = correct_order.copy()
        random.shuffle(shuffled)
        st.session_state.problem_states[problem_idx]["shuffled"] = shuffled
        st.session_state.choices[problem_idx] = [f"사진 {i+1}" for i in range(num_images)]
with c2:
    if st.button("⏭️ 다음 문제로 건너뛰기(교사용)"):
        go_next_problem(after_fail=False)
with c3:
    if st.button("🧹 전체 리셋"):
        reset_all()
        st.success("초기화 완료")

st.caption("© 2025 사진 순서 맞추기 · Streamlit")
