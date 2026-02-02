import streamlit as st

from src.assessment.neuroticism import score_neuroticism
from src.assessment.job_anxiety import score_job_anxiety
from src.interventions.loader import load_interventions
from src.routing.personalize import route

LIB_PATH = "src/interventions/library.json"

st.set_page_config(page_title="AI-anxiety MVP (J)", layout="centered")

# ---------- Helpers ----------
def likert(label: str, key: str) -> int:
    return st.radio(label, [1, 2, 3, 4, 5], horizontal=True, key=key)

def reset_session():
    for k in list(st.session_state.keys()):
        del st.session_state[k]

# ---------- Header ----------
st.title("AI-anxiety MVP（岗位替代焦虑 J）")
st.caption("说明：这是一个自我反思与行动支持工具，不提供诊断或职业预测。")

if st.button("重置（重新开始）"):
    reset_session()
    st.rerun()

# ---------- Load library once ----------
if "library" not in st.session_state:
    st.session_state["library"] = load_interventions(LIB_PATH)

# ---------- State machine ----------
step = st.session_state.get("step", "A")  # A -> B -> C

# =========================
# Screen A: Assessment
# =========================
if step == "A":
    st.subheader("A. 快速识别（个性化用）")

    st.markdown("### 1) 神经质短表（6题）")
    n_items = [
        likert("1. 面对不确定的新技术时，我会紧张。", "N1"),
        likert("2. 我经常担心自己跟不上变化。", "N2"),
        likert("3. 技术出错会让我长时间不安。", "N3"),
        likert("4. 我容易反复想潜在风险。", "N4"),
        likert("5. 面对复杂系统，我倾向回避而不是尝试。", "N5"),
        likert("6. 我很难忽略对不利未来的担忧。", "N6"),
    ]

    st.markdown("### 2) 岗位替代焦虑 J（4题）")
    j_items = [
        likert("1. 我害怕 AI 会取代人类的工作。", "J1"),
        likert("2. 我担心 AI 会取代类似我这样的岗位。", "J2"),
        likert("3. 我担心使用 AI 会让我依赖并削弱推理能力。", "J3"),
        likert("4. 我担心 AI 会让人更懒、更依赖。", "J4"),
    ]

    role = st.text_input("（可选）你的角色/职业（例如：产品经理/设计师/学生）", key="role")

    if st.button("继续 → 进入对话"):
        n_res = score_neuroticism(n_items)
        j_res = score_job_anxiety(j_items)

        st.session_state["neuro_total"] = n_res.total
        st.session_state["neuro_band"] = n_res.band
        st.session_state["j_total"] = j_res.total
        st.session_state["j_intensity"] = j_res.intensity_0_10
        st.session_state["role"] = role.strip()

        st.session_state["step"] = "B"
        st.rerun()

# =========================
# Screen B: Reflection + Driver pick
# =========================
elif step == "B":
    st.subheader("B. 识别你此刻最强的担忧")

    band = st.session_state["neuro_band"]
    j0 = st.session_state["j_intensity"]
    role = st.session_state.get("role", "")

    st.info(f"你的当前 J 焦虑强度（0–10）：{j0}（用于个性化，不做诊断）")

    st.markdown("请用一句话写下你最担心的点（可选）：")
    fear_text = st.text_area("例如：我担心 1-2 年内工作会被替代", key="fear_text")

    # Mirror + constraints (no predictions)
    if fear_text.strip():
        st.markdown("**我理解你在担心：**")
        if band == "high":
            st.write("你不是在问“未来会怎样”，你是在感受一种强烈的威胁感。我们先把注意力放回到你今天能控制的部分。")
        elif band == "mid":
            st.write("这种担心很常见。我们不做行业预测，只把它拆成当下可以处理的部分。")
        else:
            st.write("我们可以把担忧拆成结构化问题：哪些环节可被替代，哪些需要你负责判断与取舍。")

    st.markdown("### 下面哪一种最像你此刻的担忧？（选一个）")
    driver = st.radio(
        "J driver",
        options=[
            ("job_loss", "我担心“岗位会消失/被取代”。"),
            ("value_threat", "我担心“我会变得不重要/不被需要”。"),
            ("skill_erosion", "我担心“我会依赖 AI、技能退化”。"),
        ],
        format_func=lambda x: x[1],
        key="driver_choice",
    )[0]

    # Re-check intensity (simple slider)
    st.markdown("### 再确认一下你此刻强度（0–10）")
    j_confirm = st.slider("J 强度", 0, 10, int(j0), key="j_confirm")

    if st.button("继续 → 给我行动方案"):
        st.session_state["driver"] = driver
        st.session_state["j_intensity_confirm"] = j_confirm
        st.session_state["step"] = "C"
        st.rerun()

# =========================
# Screen C: Personalized actions
# =========================
elif step == "C":
    st.subheader("C. 个性化微行动（≤10分钟）")

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
