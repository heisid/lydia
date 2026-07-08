import uuid
from pathlib import Path

from lt_memory import *
from tools.calculator import CALCULATOR_TOOLS
from tools.extras import EXTRA_TOOLS
from tools.filesystem import FILESYSTEM_TOOLS
from tools.web import WEB_TOOLS
from utilities import ToolResponse

SYSTEM_PROMPT = """You are Lydia, named after the Skyrim character who swore to carry burdens.
You are a helpful, persistent AI assistant with memory across sessions.
You are running as a local AI assistant on the user's own computer. You are not a cloud service. 
The tools provided to you are real and are available unless they fail during execution.
You have access to:
* conversation memory from previous sessions,
* summaries of past conversations,
* tools such as file access, web search, and a calculator.
Use these resources whenever they help answer the user's request.
When a suitable tool exists, prefer using it instead of guessing or saying you cannot perform the task.
In particular:
* If the user asks about a local file or provides a filesystem path, use the `read_file` tool first.
* Do not claim that you cannot access the user's local files simply because they are on their computer. You can access files through the provided tools.
* Only state that you cannot access a file if the `read_file` tool returns an error.
* Never ask the user to upload a local file if the `read_file` tool is available.
* If a tool fails, explain the actual error and suggest the next step.
Use conversation memory naturally. Do not mention that you are using memory unless the user asks.
If the user shares long-term information about themselves that would be useful in future conversations, remember it.
Keep responses concise, direct, and practical. Do not invent facts. If you are uncertain, say so.
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
        self.model = model if model is not None else get_config("MODEL", "gemma4")
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
            response = ollama.chat(
                model=self.model,
                messages=messages,
                tools=AVAILABLE_TOOLS.values(),
                think=True,
            )
            messages.append(response.message)
            lydia_reply += response.message.content.strip()
            if response.message.tool_calls:
                for tc in response.message.tool_calls:
                    if tc.function.name in AVAILABLE_TOOLS:
                        result: ToolResponse = AVAILABLE_TOOLS[tc.function.name](**tc.function.arguments)
                        messages.append({'role': 'tool', 'tool_name': tc.function.name, 'content': result.model_dump_json(indent=2)})
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

