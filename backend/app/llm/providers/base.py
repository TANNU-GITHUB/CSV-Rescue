from __future__ import annotations


class LLMProvider:
    name = "base"

    async def complete(self, messages: list[dict], timeout: int) -> str:
        raise NotImplementedError
