import json
import os
import urllib.request
import urllib.error
from typing import List, Dict, Optional


class LLMClient:
    def __init__(self):
        # OpenAI-compatible endpoint
        self.base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
        if self.base_url.endswith("/v1"):
            self.base_url = self.base_url[:-3]
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "").strip()
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        self.last_error: Optional[str] = None

    def enabled(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        force_json: bool = False,
    ) -> str:
        """
        messages: [{"role":"system|user|assistant","content":"..."}]
        Uses OpenAI-compatible /v1/chat/completions.
        """
        if not self.enabled():
            missing = []
            if not self.base_url:
                missing.append("LLM_BASE_URL")
            if not self.api_key:
                missing.append("LLM_API_KEY")
            if not self.model:
                missing.append("LLM_MODEL")
            if missing and any([self.base_url, self.api_key, self.model]):
                self.last_error = f"缺少环境变量: {', '.join(missing)}"
                return self._mock_chat(messages, error=self.last_error, show_prefix=False)
            self.last_error = None
            return self._mock_chat(messages, show_prefix=True)

        try:
            self.last_error = None
            reply = self._call_chat(messages, temperature=temperature, force_json=force_json, response_format_enabled=True)
            return self._dedupe_or_fallback(messages, reply)
        except urllib.error.HTTPError as e:
            body = self._read_http_error_body(e)
            err_text = self._format_http_error(e, body)
            self.last_error = err_text
            if force_json and self._should_retry_without_response_format(e, body):
                try:
                    reply = self._call_chat(messages, temperature=temperature, force_json=True, response_format_enabled=False)
                    return self._dedupe_or_fallback(messages, reply)
                except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError) as e2:
                    self.last_error = str(e2)
                    return self._mock_chat(messages, error=self.last_error, show_prefix=False)
            return self._mock_chat(messages, error=err_text, show_prefix=False)
        except (urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
            # fail closed to mock to keep MVP usable
            self.last_error = str(e)
            return self._mock_chat(messages, error=self.last_error, show_prefix=False)

    def _call_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        force_json: bool,
        response_format_enabled: bool,
    ) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        payload_messages = messages
        if force_json and not response_format_enabled:
            payload_messages = [
                {"role": "system", "content": "Return ONLY valid JSON, no markdown or code fences."}
            ] + messages
        payload = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
        }
        if force_json and response_format_enabled:
            payload["response_format"] = {"type": "json_object"}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = resp.read().decode("utf-8")
        obj = json.loads(body)
        return obj["choices"][0]["message"]["content"]

    def _should_retry_without_response_format(self, error: urllib.error.HTTPError, body: Optional[str]) -> bool:
        if error.code in (400, 404, 422):
            return True
        if not body:
            return False
        lowered = body.lower()
        return "response_format" in lowered or "json_object" in lowered

    def _read_http_error_body(self, error: urllib.error.HTTPError) -> Optional[str]:
        try:
            body = error.read()
        except Exception:
            return None
        try:
            return body.decode("utf-8")
        except Exception:
            return None

    def _format_http_error(self, error: urllib.error.HTTPError, body: Optional[str]) -> str:
        msg = f"HTTP {error.code}"
        if error.code == 402:
            msg += " Payment Required"
        if not body:
            return msg
        try:
            obj = json.loads(body)
            if isinstance(obj, dict):
                err = obj.get("error") or {}
                if isinstance(err, dict):
                    detail = err.get("message") or err.get("type")
                    if detail:
                        return f"{msg}: {detail}"
        except Exception:
            pass
        return f"{msg}: {body[:200]}"

    def _dedupe_or_fallback(self, messages: List[Dict[str, str]], reply: str) -> str:
        last_assistant = ""
        for m in reversed(messages):
            if m.get("role") == "assistant":
                last_assistant = m.get("content", "")
                break
        if last_assistant and reply.strip() == last_assistant.strip():
            return self._mock_chat(messages, error="LLM重复回复")
        return reply

    def _mock_chat(self, messages: List[Dict[str, str]], error: Optional[str] = None, show_prefix: bool = True) -> str:
        # Stateful mock: progress based on chat history
        prefix = "（Mock 模式）" if show_prefix else ""
        if error:
            prefix += f"（LLM调用失败：{error[:80]}）"

        user_texts = [m.get("content", "") for m in messages if m.get("role") == "user"]
        assistant_texts = [m.get("content", "") for m in messages if m.get("role") == "assistant"]
        all_user = "\n".join(user_texts)

        asked_worst = any("最害怕的结果是什么" in t for t in assistant_texts)
        asked_driver = any("更像哪一种" in t or "岗位消失/不重要/退化" in t for t in assistant_texts)

        def driver_of(text: str) -> str:
            if any(k in text for k in ["裁员", "失业", "岗位消失", "取代", "替代", "失去工作"]):
                return "job_loss"
            if any(k in text for k in ["不重要", "没价值", "无用", "没人需要", "被边缘"]):
                return "value_threat"
            if any(k in text for k in ["依赖", "退化", "变笨", "不用脑", "思考能力下降"]):
                return "skill_erosion"
            return "value_threat"

        drv = driver_of(all_user)

        if not asked_worst:
            return (
                f"{prefix}我听到你在担心 AI 会影响你的工作，这种不安很真实。\n"
                "我们先把担忧落到一个具体问题上：你最害怕的结果是什么？"
                "（例如：失业、收入下降、价值感受损、能力退化）"
            )

        if asked_worst and not asked_driver:
            return (
                f"{prefix}我明白了，你描述的“最坏结果”已经很具体了。\n"
                "为了更精准地帮你，我们把它归到一种主导类型里（选一个最像的）：\n"
                "A 岗位消失（job_loss）\n"
                "B 变得不重要/不被需要（value_threat）\n"
                "C 依赖 AI 导致能力退化（skill_erosion）\n"
                "你觉得更像 A/B/C？"
            )

        if drv == "job_loss":
            return (
                f"{prefix}你现在面对的是“不确定性→灾难化想象”的自然反应，不代表结局已定。\n"
                "我们不做预测，先做一件能恢复控制感的小事（10 分钟）：\n"
                "1) 写下你工作流程中 3 个关键环节\n"
                "2) 标注每个环节 AI 可替代程度（低/中/高）\n"
                "3) 选 1 个“低可替代”环节写一句：‘这个环节的价值在于____’\n"
                "你愿意从哪 3 个环节开始写？"
            )
        if drv == "skill_erosion":
            return (
                f"{prefix}你担心“依赖→退化”，这非常合理。关键不是不用 AI，而是设定协作边界。\n"
                "10 分钟微行动：\n"
                "1) 选一个小问题，你先写 3 条推理要点\n"
                "2) 让 AI 扩写成完整论证\n"
                "3) 你删 1 句不同意的、补 1 句你认为关键的\n"
                "你想用哪个小问题来做这次练习？"
            )
        return (
            f"{prefix}你更像是“价值感被威胁”的担忧：担心自己变得不重要。\n"
            "10 分钟微行动：\n"
            "1) 写下最近一次别人需要你‘判断/沟通/取舍’的具体事件（各 1 句）\n"
            "2) 写一句：‘AI 可以帮我____，但这类价值仍需要我来____’\n"
            "你愿意写哪个事件？"
        )
