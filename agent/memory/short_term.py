from collections import deque


class ShortTermMemory:
    """
    Sliding window of the last `max_turns` message pairs.
    Keeps the recent conversation in the LLM context without blowing up token count.
    """

    def __init__(self, max_turns: int = 10):
        # Each turn = one message dict {role, content}
        self._buffer: deque[dict] = deque(maxlen=max_turns * 2)

    def add(self, role: str, content: str) -> None:
        self._buffer.append({"role": role, "content": content})

    def get_messages(self) -> list[dict]:
        return list(self._buffer)

    def clear(self) -> None:
        self._buffer.clear()

    def __len__(self) -> int:
        return len(self._buffer)
