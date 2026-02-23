import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Make `src/` importable (so we can `import ai`, `assessment`, `routing`, etc.)
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from assessment.neuroticism import score_neuroticism
from assessment.job_anxiety import score_job_anxiety
from interventions.loader import load_interventions
from routing.personalize import route

# NEW: LLM chat modules
from ai.llm_client import LLMClient
from ai.prompts import SYSTEM_CHAT_STYLE
from ai.analyzer import analyze_chat

LIB_PATH = "src/interventions/library.json"

st.set_page_config(page_title="AI焦虑-工作替代焦虑干预系统", layout="centered")

# Load optional local env; real LLM config must come from environment variables.
load_dotenv()
APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "admin123")

# ---------- Theme ----------
st.markdown(
    """
    <style>
        :root {
            --bg: #efe6d7;
            --panel: #fbf7ef;
            --text: #4a3428;
            --muted: #6b5648;
            --accent: #9caf88;
            --accent-2: #b48e6e;
            --accent-3: #d4c6a5;
            --border: #dbcdb6;
            --shadow: 0 8px 24px rgba(74, 52, 40, 0.08);
        }
        .stApp {
            background: linear-gradient(180deg, #f4eee3 0%, var(--bg) 60%, #efe1cc 100%);
            color: var(--text);
        }
        [data-testid="stHeader"], [data-testid="stToolbar"] {
            background: transparent;
        }
        .stMarkdown, .stText, .stCaption, .stRadio, .stTextInput, .stTextArea, .stSlider, .stSelectbox {
            color: var(--text);
        }
        .stChatMessage {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 10px 14px;
            margin-bottom: 10px;
        }
        .stButton>button {
            background: var(--accent);
            color: #2f261f;
            border: none;
            border-radius: 10px;
            padding: 0.45rem 0.9rem;
            transition: transform 120ms ease, box-shadow 120ms ease, background 120ms ease;
        }
        .stButton>button:hover {
            background: #a8b89a;
            transform: translateY(-1px);
            box-shadow: var(--shadow);
        }
        .stTextInput>div>div>input,
        .stTextArea>div>textarea {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text);
        }
        .stTextInput>div>div>input::placeholder,
        .stTextArea>div>textarea::placeholder {
            color: var(--muted);
        }
        .stTextInput>div>div>input:focus,
        .stTextArea>div>textarea:focus {
            border-color: var(--accent-2);
            box-shadow: 0 0 0 3px rgba(180, 142, 110, 0.18);
            outline: none;
        }
        .stRadio label, .stRadio div[role="radiogroup"] label {
            color: var(--text) !important;
        }
        .stRadio div[role="radiogroup"] span {
            color: var(--text) !important;
        }
        .stRadio [data-testid="stMarkdownContainer"] p {
            color: var(--text) !important;
        }
        .stRadio [data-baseweb="radio"] {
            background: var(--panel);
            border-radius: 10px;
            padding: 6px 8px;
            border: 1px solid var(--border);
        }
        [data-testid="stChatInput"] textarea {
            background: var(--panel) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
        }
        [data-testid="stChatInput"] textarea::placeholder {
            color: var(--muted) !important;
        }
        .stChatMessage [data-testid="stMarkdownContainer"] p {
            color: var(--text);
        }
        .stSlider>div>div>div {
            color: var(--text);
        }
        .section {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 18px 20px;
            margin: 12px 0 22px;
            box-shadow: 0 6px 16px rgba(74, 52, 40, 0.06);
        }
        .section-title {
            color: var(--text);
        }
        .stInfo, .stWarning, .stError, .stSuccess {
            border-radius: 12px;
        }
        .divider-line {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--border), transparent);
            margin: 14px 0 18px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Helpers ----------
def likert(label: str, key: str) -> int:
    return st.radio(label, [1, 2, 3, 4, 5], horizontal=True, key=key)

def reset_session():
    for k in list(st.session_state.keys()):
        del st.session_state[k]

# ---------- Login ----------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "users" not in st.session_state:
    # In-memory users for this session only; seed with env defaults.
    st.session_state["users"] = {APP_USERNAME: APP_PASSWORD}

if st.session_state["logged_in"]:
    with st.sidebar:
        st.caption("已登录")
        if st.button("退出登录"):
            st.session_state["logged_in"] = False
            st.rerun()
else:
    st.markdown("## 用户登录")
    st.caption("可在 .env 设置 APP_USERNAME / APP_PASSWORD。")
    tab_login, tab_register = st.tabs(["登录", "注册"])

    with tab_login:
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("用户名", key="login_user")
            password = st.text_input("密码", type="password", key="login_pass")
            submitted = st.form_submit_button("登录")

        if submitted:
            if st.session_state["users"].get(username) == password:
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("用户名或密码错误。")

    with tab_register:
        with st.form("register_form", clear_on_submit=True):
            new_user = st.text_input("新用户名", key="reg_user")
            new_pass = st.text_input("新密码", type="password", key="reg_pass")
            new_pass2 = st.text_input("确认密码", type="password", key="reg_pass2")
            submitted_reg = st.form_submit_button("注册")

        if submitted_reg:
            if not new_user or not new_pass:
                st.error("用户名和密码不能为空。")
            elif new_user in st.session_state["users"]:
                st.error("用户名已存在。")
            elif new_pass != new_pass2:
                st.error("两次密码不一致。")
            else:
                st.session_state["users"][new_user] = new_pass
                st.success("注册成功，请在“登录”页签登录。")
    st.stop()

# ---------- Header ----------
st.title("AI焦虑干预系统")
st.caption("说明：这是一个自我反思与行动支持工具，不提供诊断或职业预测。")

# ---------- Load library once ----------
if "library" not in st.session_state:
    st.session_state["library"] = load_interventions(LIB_PATH)

# ---------- State machine ----------
step = st.session_state.get("step", "A")  # A -> B -> C -> D

# =========================
# Screen A: Intro
# =========================
if step == "A":
    st.markdown(
        "这是一个聚焦 **AI 工作替代焦虑** 的自助干预系统，帮助你更清晰地识别担忧来源，"
        "并在不做职业预测的前提下，找到可执行的小行动，恢复掌控感。"
    )
    st.markdown(
        "流程很简单：先完成两个量表，随后进入与 AI 的对话，最后生成个性化总结与行动建议。"
    )

    st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

    if st.button("开始"):
        st.session_state["step"] = "B"
        st.rerun()

# =========================
# Screen B: Assessments
# =========================
elif step == "B":
    st.subheader("B. 量表填写（用于个性化）")

    st.markdown("### 基础状态评估（6题）")
    st.caption("请选择最符合你当前感受的选项。")
    n_items = [
        likert("1. 面对不确定的新技术时，我会紧张。", "N1"),
        likert("2. 我经常担心自己跟不上变化。", "N2"),
        likert("3. 技术出错会让我长时间不安。", "N3"),
        likert("4. 我容易反复想潜在风险。", "N4"),
        likert("5. 面对复杂系统，我倾向回避而不是尝试。", "N5"),
        likert("6. 我很难忽略对不利未来的担忧。", "N6"),
    ]
    st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

    st.markdown("### AI工作替代焦虑评估（4题）")
    st.caption("请选择最符合你当前感受的选项。")
    j_items = [
        likert("1. 我害怕 AI 会取代人类的工作。", "J1"),
        likert("2. 我担心 AI 会取代类似我这样的岗位。", "J2"),
        likert("3. 我担心使用 AI 会让我依赖并削弱推理能力。", "J3"),
        likert("4. 我担心 AI 会让人更懒、更依赖。", "J4"),
    ]
    role = st.text_input("你的角色/职业（例如：产品经理/设计师/学生）", key="role")

    if st.button("继续 → 进入对话"):
       # Store assessments
        n_res = score_neuroticism(n_items)
        j_res = score_job_anxiety(j_items)

        st.session_state["neuro_total"] = n_res.total
        st.session_state["neuro_band"] = n_res.band
        st.session_state["j_total"] = j_res.total
        st.session_state["j_intensity"] = j_res.intensity_0_10

        # IMPORTANT: "role" is controlled by the text_input widget key="role"
        # Do not assign to st.session_state["role"] here.
        st.session_state["role_clean"] = st.session_state.get("role", "").strip()

        st.session_state["step"] = "C"
        st.rerun()


# =========================
# Screen C: Reflection + Driver pick
# =========================
elif step == "C":
    st.subheader("C. 和 AI 对话")

    band = st.session_state["neuro_band"]
    j0 = st.session_state["j_intensity"]

    st.info(
        f"评估结果：你当前的 AI 工作替代焦虑强度为 **{j0}/10**。"
        " 数值越高表示当前焦虑体验越强烈，但这不代表结论或预测。"
    )
    st.markdown("接下来，将由聊天机器人和你沟通这种焦虑情绪。")

    # ---------- Chat state ----------
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []
    if "pending_user_input" not in st.session_state:
        st.session_state["pending_user_input"] = None
    if "pending_request_id" not in st.session_state:
        st.session_state["pending_request_id"] = None
    if "request_counter" not in st.session_state:
        st.session_state["request_counter"] = 0
    if "last_processed_request_id" not in st.session_state:
        st.session_state["last_processed_request_id"] = 0
    if "llm_error" not in st.session_state:
        st.session_state["llm_error"] = None

    llm_client = LLMClient()
    llm_mode = "Real" if llm_client.enabled() else "Mock"
    llm_model = os.getenv("LLM_MODEL", "").strip()
    if llm_mode == "Real":
        st.caption(f"LLM 模式：Real（{llm_model}）")
    else:
        st.caption("LLM 模式：Mock（未配置 LLM_* 环境变量）")

    if st.session_state.get("llm_error"):
        st.error(f"LLM 调用失败：{st.session_state['llm_error']}")

    # Render chat history
    chat_block = st.container()
    with chat_block:
        for m in st.session_state["chat_messages"]:
            with st.chat_message(m["role"]):
                st.write(m["content"])

    # In-page chat input (avoid floating chat box)
    st.markdown("#### 输入你的话，然后点击发送")
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "聊天输入",
            placeholder="例如：我担心 AI 会取代我，觉得很不安…",
            key="chat_input",
            height=90,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("发送")

    if submitted and user_input.strip():
        st.session_state["request_counter"] += 1
        st.session_state["pending_request_id"] = st.session_state["request_counter"]
        st.session_state["pending_user_input"] = user_input.strip()
        st.rerun()

    pending_id = st.session_state.get("pending_request_id")
    if pending_id and pending_id != st.session_state.get("last_processed_request_id"):
        st.session_state["last_processed_request_id"] = pending_id
        pending_text = st.session_state["pending_user_input"]
        st.session_state["chat_messages"].append({"role": "user", "content": pending_text})

        sys_prompt = SYSTEM_CHAT_STYLE[band]
        client = LLMClient()
        msgs = [{"role": "system", "content": sys_prompt}] + st.session_state["chat_messages"]
        reply = client.chat(msgs, temperature=0.4)
        st.session_state["llm_error"] = client.last_error

        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})
        st.session_state["pending_user_input"] = None
        st.session_state["pending_request_id"] = None
        st.rerun()

    if "chat_done" not in st.session_state:
        st.session_state["chat_done"] = False

    st.markdown('<hr class="divider-line">', unsafe_allow_html=True)
    if st.button("结束对话"):
        st.session_state["chat_done"] = True

    # Optional: allow user to confirm intensity before generating plan
    if st.session_state.get("chat_done"):
        st.markdown("#### 再次确认你当前的 AI 工作替代焦虑强度（0–10）")
        j_confirm = st.slider("J 强度", 0, 10, int(j0), key="j_confirm")

        if st.button("生成总结（焦虑情况 + 干预建议）"):
            summary = analyze_chat(st.session_state["chat_messages"])
            st.session_state["summary"] = summary
            st.session_state["llm_error"] = summary.get("_llm_error")

            # Use analyzer-inferred driver; fallback if missing
            st.session_state["driver"] = summary.get("driver", "value_threat")

            # Store confirmed intensity as baseline for this round
            st.session_state["j_intensity_confirm"] = int(j_confirm)

            st.session_state["step"] = "D"
            st.rerun()

# =========================
# Screen D: Personalized actions
# =========================
elif step == "D":
    summary = st.session_state.get("summary")
    if st.button("重置（重新开始）"):
        reset_session()
        st.rerun()
    if st.session_state.get("llm_error"):
        st.error(f"LLM 调用失败：{st.session_state['llm_error']}")
    if summary:
        st.markdown("### 对话总结（自动生成）")
        st.write(f"**主导焦虑类型（driver）**：{summary.get('driver')}")
        st.write("**不良思维模式（unhelpful thoughts）**：")
        for x in summary.get("unhelpful_thoughts", []):
            st.write(f"- {x}")
        st.write("**纠偏观点（reframe）**：")
        st.write(summary.get("reframe", ""))
        st.divider()

    st.subheader("D. 个性化微行动（≤10分钟）")

    band = st.session_state["neuro_band"]
    driver = st.session_state["driver"]
    j_before = st.session_state.get("j_intensity_confirm", st.session_state["j_intensity"])
    lib = st.session_state["library"]

    st.write(f"个性化参数：神经质风格 **{band}** ｜担忧类型 **{driver}**")
    st.info("我们不解决未来，只做一件小事来恢复控制感。完成即可算成功。")

    actions = route(driver=driver, band=band, library_data=lib)
    if not actions:
        st.error("未找到匹配的行动卡。请检查 library.json 是否包含对应项。")
        st.stop()

    st.markdown("### 选择一个你愿意现在就做的行动：")
    titles = [f"{a['title']}（{a['time_minutes']}分钟）" for a in actions]
    pick = st.radio("行动选项", options=list(range(len(actions))), format_func=lambda i: titles[i])

    a = actions[pick]
    st.markdown(f"#### {a['title']}")
    st.write(f"**目标：** {a['goal']}")
    st.write(f"**预计用时：** {a['time_minutes']} 分钟")

    st.markdown("**步骤：**")
    for i, s in enumerate(a["steps"], start=1):
        st.write(f"{i}. {s}")

    st.write(f"**完成标准：** {a['success_criteria']}")
    st.write(f"**卡住时：** {a['fallback_if_stuck']}")

    done = st.checkbox("我完成了（或至少开始做了）", key="done_check")

    st.markdown("### 做完后，现在你的 J 焦虑强度是多少？（0–10）")
    j_after = st.slider("J 强度（后测）", 0, 10, int(j_before), key="j_after")

    if st.button("提交本次结果"):
        st.success("已记录（MVP 默认仅本地会话，不上传）。谢谢你完成一次行动。")
        st.write(f"- 前测：{j_before}")
        st.write(f"- 后测：{j_after}")
        st.write(f"- 变化：{j_after - j_before:+d}")

        if j_after <= j_before - 1:
            st.write("✅ 本次达到 MVP 成功标准之一：焦虑强度下降 ≥ 1")
        st.write("你可以点上方“重置”开始下一次，或换一个行动再做一轮。")
