import json
from typing import List, Dict, Any
from ai.llm_client import LLMClient
from ai.prompts import SYSTEM_ANALYZER, ANALYZER_SCHEMA_HINT

DRIVERS = ("job_loss", "value_threat", "skill_erosion")

def _heuristic_driver(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["裁员", "失业", "岗位消失", "取代", "替代"]):
        return "job_loss"
    if any(k in t for k in ["不重要", "没价值", "无用", "没人需要", "被边缘"]):
        return "value_threat"
    if any(k in t for k in ["依赖", "退化", "变笨", "不用脑", "思考能力下降"]):
        return "skill_erosion"
    return "value_threat"

def analyze_chat(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    messages: chat transcript (user+assistant)
    returns dict matching schema in prompts.py
    """
    # concatenate user messages for heuristic fallback
    user_text = "\n".join([m["content"] for m in messages if m.get("role") == "user"])

    client = LLMClient()
    if not client.enabled():
        # Mock analysis
        driver = _heuristic_driver(user_text)
        return {
            "driver": driver,
            "intensity_guess_0_10": 6,
            "unhelpful_thoughts": ["灾难化想象：把不确定当成必然", "全或无：要么被取代要么毫无价值"],
            "reframe": "你现在面对的是不确定性带来的压力，而不是一个已确定的结局。与其预测未来，不如把注意力放到你能控制的协作方式与价值环节上。我们用一次小行动来恢复掌控感。",
            "suggested_actions": [
                "写下你工作中3个关键环节，并标注AI可替代程度（10分钟）",
                "做一次三段协作：我先写要点→AI扩写→我复核删改（10分钟）"
            ],
            "_llm_error": None,
        }

    # LLM analysis: ask for JSON only
    prompt_messages = [
        {"role": "system", "content": SYSTEM_ANALYZER + "\n" + ANALYZER_SCHEMA_HINT},
        {"role": "user", "content": "CHAT TRANSCRIPT:\n" + json.dumps(messages, ensure_ascii=False)}
    ]
    raw = client.chat(prompt_messages, temperature=0.2, force_json=True)
    llm_error = client.last_error

    def _extract_json(raw_text: str) -> Dict[str, Any]:
        text = raw_text.strip()
        if text.startswith("```"):
            lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
            text = "\n".join(lines).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        return json.loads(text)

    def _normalize(obj: Dict[str, Any]) -> Dict[str, Any]:
        driver = obj.get("driver") if obj.get("driver") in DRIVERS else _heuristic_driver(user_text)
        try:
            intensity = int(obj.get("intensity_guess_0_10", 6))
        except (TypeError, ValueError):
            intensity = 6
        intensity = max(0, min(10, intensity))
        unhelpful = obj.get("unhelpful_thoughts") or []
        if not isinstance(unhelpful, list):
            unhelpful = [str(unhelpful)]
        reframe = obj.get("reframe") or ""
        actions = obj.get("suggested_actions") or []
        if not isinstance(actions, list):
            actions = [str(actions)]
        return {
            "driver": driver,
            "intensity_guess_0_10": intensity,
            "unhelpful_thoughts": unhelpful,
            "reframe": reframe,
            "suggested_actions": actions,
            "_llm_error": llm_error,
        }

    # try to parse JSON; fall back to heuristic
    try:
        obj = _extract_json(raw)
        return _normalize(obj)
    except Exception:
        driver = _heuristic_driver(user_text)
        return {
            "driver": driver,
            "intensity_guess_0_10": 6,
            "unhelpful_thoughts": ["模型输出未能解析为JSON，已使用降级策略"],
            "reframe": raw[:800],
            "suggested_actions": [],
            "_llm_error": llm_error,
        }
