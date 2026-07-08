import time
import uuid
from pathlib import Path
from pprint import pprint

from lt_memory import *
from tools.calculator import CALCULATOR_TOOLS
from tools.extras import EXTRA_TOOLS
from tools.filesystem import FILESYSTEM_TOOLS
from tools.web import WEB_TOOLS
from utilities import ToolResponse

SYSTEM_PROMPT = """
You are Lydia, a helpful AI assistant running locally on the user's computer.
You have access to real tools and conversation memory.

Rules:
- Use a tool whenever it provides a more reliable answer than your own knowledge.
- Do not guess facts that can be verified.
- Treat your built-in knowledge as potentially outdated.

Use the time tool when the answer depends on the current date or time.
Use the web tool for current or changing information such as news, weather, prices, software versions, or recent events.
Use the file tool when the user asks about a local file or provides a local file path. Only say a file cannot be accessed if the tool reports an error.

Use conversation memory naturally without mentioning it. Remember long-term information that will improve future conversations.

Keep replies concise, practical, and honest. If a tool fails, explain what happened. If you are unsure, say so.
"""

AVAILABLE_TOOLS = {
    **CALCULATOR_TOOLS,
    **FILESYSTEM_TOOLS,
    **WEB_TOOLS,
    **EXTRA_TOOLS,
}

class Lydia:
    def __init__(self, session_id: str = None, model: str|None = None,
                 db_path: Path|None = None) -> None:
        self.model = model if model is not None else get_config("MODEL", "qwen3.5")
        db_path = db_path if db_path is not None else DB_PATH
        self.session_id = session_id or str(uuid.uuid4())
        self.conn = init_db(db_path)
        self.turn_count = 0

        print(f"[Lydia] Session: {self.session_id[:8]}...")

    def chat(self, user_message: str) -> str:
        save_turn(self.conn, self.session_id, "user", user_message)

        memory_context = get_memory_context(self.conn, self.session_id)
        recent = get_recent_turns(self.conn, self.session_id, limit=10)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + memory_context}
        ]
        for turn in recent[:-1]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})

        lydia_reply = ''
        while True:
            # start = time.perf_counter()
            # print(messages)
            # pprint(messages, width=120)
            response = ollama.chat(
                model=self.model,
                messages=messages,
                tools=AVAILABLE_TOOLS.values(),
                keep_alive="30m",
                think=False,
            )
            # print(f"chat took {time.perf_counter() - start:.2f}s")
            messages.append(response.message)
            lydia_reply += response.message.content.strip()
            if response.message.tool_calls:
                for tc in response.message.tool_calls:
                    if tc.function.name in AVAILABLE_TOOLS:
                        result: ToolResponse = AVAILABLE_TOOLS[tc.function.name](**tc.function.arguments)
                        messages.append({'role': 'tool', 'tool_name': tc.function.name, 'content': result.model_dump_json(indent=2)})
                        save_turn(self.conn, self.session_id, "tool", result.model_dump_json(), tc.function.name, str(tc.function.arguments))
            else:
                break

        save_turn(self.conn, self.session_id, "assistant", lydia_reply)
        self.turn_count += 1

        if self.turn_count % 30 == 0:
            summarize_session(self.conn, self.session_id, model=self.model)

        return lydia_reply

    def remember(self, key: str, value: str):
        upsert_fact(self.conn, key, value)
        print(f"[memory] Stored: {key} = {value}")

    def end_session(self):
        summarize_session(self.conn, self.session_id, model=self.model)
        self.conn.close()
        print(f"[Lydia] Session {self.session_id[:8]} saved to memory.")


if __name__ == "__main__":
    import sys

    session_id = sys.argv[1] if len(sys.argv) > 1 else None

    lydia = Lydia(session_id=session_id)
    try:
        while True:
            user_input = input("Me: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ('quit', 'exit', 'q'):
                break
            if user_input.lower().startswith("remember ") and "=" in user_input:
                _, kv = user_input.split(" ", 1)
                k, v = kv.split("=", 1)
                lydia.remember(k.strip(), v.strip())
                continue

            reply = lydia.chat(user_input)
            print(f"\nLydia: {reply}\n")

    except KeyboardInterrupt:
        pass
    finally:
        lydia.end_session()

