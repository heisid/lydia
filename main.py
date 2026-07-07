import uuid
from pathlib import Path

from lt_memory import *
from tools.calculator import *
from tools.filesystem import *

SYSTEM_PROMPT = """Your name is Lydia. Named after Skyrim character
who swore to carry the burdens.
You are a helpful, persistent AI assistant with memory across sessions.
You have access to summaries of past conversations and key facts about the user.
Use this context naturally — don't announce that you're using memory, just apply it.
If the user tells you something important about themselves, remember it.
Be concise, direct, and useful."""

AVAILABLE_TOOLS = {
            'get_sum': get_sum,
            'multiply': multiply,
            'divide': divide,
            'list_directory_content': list_directory_content,
            'get_current_directory': get_current_directory,
            'is_file': is_file,
            'get_file_size': get_file_size,
            'read_file': read_file,
}

class Lydia:
    def __init__(self, session_id: str = None, model: str|None = None,
                 db_path: Path|None = None) -> None:
        self.model = model if model is not None else get_config("MODEL")
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
                        result = AVAILABLE_TOOLS[tc.function.name](**tc.function.arguments)
                        messages.append({'role': 'tool', 'tool_name': tc.function.name, 'content': str(result)})
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
    print("Memory ready. Type 'quit' to end, 'remember KEY=VALUE' to store facts.\n")

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

