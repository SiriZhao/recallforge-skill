from __future__ import annotations

import json
from typing import Any


class BaseLLMProvider:
    name = "base"

    def generate_json(self, prompt: str, schema: dict | None = None) -> dict:
        raise NotImplementedError

    def generate_markdown(self, prompt: str) -> str:
        raise NotImplementedError

    def summarize(self, text: str, max_words: int = 120) -> str:
        raise NotImplementedError

    def extract_topics(self, chunks: list[Any]) -> list[dict]:
        raise NotImplementedError

    def generate_questions(self, exam_points: list[dict], count: int = 10, mode: str = "s-priority") -> list[dict]:
        raise NotImplementedError


class MockLLMProvider(BaseLLMProvider):
    name = "mock"

    def generate_json(self, prompt: str, schema: dict | None = None) -> dict:
        try:
            return json.loads(prompt)
        except Exception:
            return {"mock": True, "summary": self.summarize(prompt)}

    def generate_markdown(self, prompt: str) -> str:
        return self.summarize(prompt, 160)

    def summarize(self, text: str, max_words: int = 120) -> str:
        compact = " ".join(text.split())
        return compact[: max_words * 2] + ("..." if len(compact) > max_words * 2 else "")

    def extract_topics(self, chunks: list[Any]) -> list[dict]:
        topics = []
        seen = set()
        for ch in chunks:
            for kw in getattr(ch, "keywords", [])[:4]:
                if kw in seen or kw in {"老师说", "这里", "答案"}:
                    continue
                seen.add(kw)
                topics.append({"topic_name": kw, "source_chunks": [ch.chunk_id], "source_refs": ch.source_refs})
        return topics

    def generate_questions(self, exam_points: list[dict], count: int = 10, mode: str = "s-priority") -> list[dict]:
        questions = []
        pool = exam_points or [{"exam_point_id": "EP000", "topic_id": "T000", "topic_name": "需人工确认考点", "source_refs": []}]
        for i in range(count):
            ep = pool[i % len(pool)]
            topic = ep.get("topic_name", "考点")
            questions.append({
                "question_id": f"Q{i+1:03d}",
                "question_text": f"【{mode}】说明或计算：{topic} 的考试核心要求是什么？",
                "question_type": "short_answer",
                "topic_id": ep.get("topic_id", "T000"),
                "exam_point_id": ep.get("exam_point_id", "EP000"),
                "difficulty": ep.get("difficulty", 2),
                "answer": f"围绕 {topic} 写出定义、关键步骤、公式适用条件，并引用资料中的例题或实验情境。",
                "explanation": "Mock provider 生成的规则题，用于无 API key 时闭环运行；真实使用时可替换为外部 LLM。",
                "common_trap": "只背结论，不写条件、单位、步骤或误差来源。",
                "source_refs": ep.get("source_refs", []),
                "confidence": min(ep.get("confidence", 0.7), 0.8),
            })
        return questions


class FallbackLLMProvider(BaseLLMProvider):
    name = "fallback"

    def __init__(self, preferred: BaseLLMProvider | None = None, warnings: list[str] | None = None):
        self.preferred = preferred or MockLLMProvider()
        self.mock = MockLLMProvider()
        self.warnings = warnings if warnings is not None else []

    def _safe(self, method: str, *args, **kwargs):
        try:
            return getattr(self.preferred, method)(*args, **kwargs)
        except Exception as exc:
            self.warnings.append(f"LLM {method} failed: {exc}; fallback to mock/rules.")
            return getattr(self.mock, method)(*args, **kwargs)

    def generate_json(self, prompt: str, schema: dict | None = None) -> dict:
        return self._safe("generate_json", prompt, schema)

    def generate_markdown(self, prompt: str) -> str:
        return self._safe("generate_markdown", prompt)

    def summarize(self, text: str, max_words: int = 120) -> str:
        return self._safe("summarize", text, max_words)

    def extract_topics(self, chunks: list[Any]) -> list[dict]:
        return self._safe("extract_topics", chunks)

    def generate_questions(self, exam_points: list[dict], count: int = 10, mode: str = "s-priority") -> list[dict]:
        return self._safe("generate_questions", exam_points, count, mode)


class OpenAIProvider(BaseLLMProvider):
    name = "openai-placeholder"


class DeepSeekProvider(BaseLLMProvider):
    name = "deepseek-placeholder"


class ClaudeProvider(BaseLLMProvider):
    name = "claude-placeholder"
