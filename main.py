"""
credit: https://dev.to/satstack/give-your-ai-agent-long-term-memory-with-sqlite-and-ollama-4fon
with some minor adjustments
"""
import uuid
from pathlib import Path

from lt_memory import *

SYSTEM_PROMPT = """You are a helpful, persistent AI assistant with memory across sessions.
Your name is Gemma.
You have access to summaries of past conversations and key facts about the user.
Use this context naturally — don't announce that you're using memory, just apply it.
If the user tells you something important about themselves, remember it.
Be concise, direct, and useful."""

class Gemma:
    def __init__(self, session_id: str = None, model: str|None = None,
                 db_path: Path|None = None) -> None:
        self.model = model if model is not None else get_config("MODEL")
        db_path = db_path if db_path is not None else DB_PATH
        self.session_id = session_id or str(uuid.uuid4())
        self.conn = init_db(db_path)
        self.turn_count = 0

        print(f"[Gemma] Session: {self.session_id[:8]}...")

    def chat(self, user_message: str) -> str:
        save_turn(self.conn, self.session_id, "user", user_message)

        memory_context = get_memory_context(self.conn, self.session_id)
        recent = get_recent_turns(self.conn, self.session_id, limit=10)

        # Format messages for the LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + memory_context}
        ]
        for turn in recent[:-1]:  # Exclude the turn we just saved
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})

        response = ollama.chat(model=self.model, messages=messages,
                               options={"temperature": 0.7})
        assistant_reply = response['message']['content'].strip()

        save_turn(self.conn, self.session_id, "assistant", assistant_reply)
        self.turn_count += 1

        if self.turn_count % 30 == 0:
            summarize_session(self.conn, self.session_id, model=self.model)

        return assistant_reply

    def remember(self, key: str, value: str):
        upsert_fact(self.conn, key, value)
        print(f"[memory] Stored: {key} = {value}")

    def end_session(self):
        summarize_session(self.conn, self.session_id, model=self.model)
        self.conn.close()
        print(f"[Gemma] Session {self.session_id[:8]} saved to memory.")


# --- CLI Interface ---
if __name__ == "__main__":
    import sys

    session_id = sys.argv[1] if len(sys.argv) > 1 else None

    gemma = Gemma(session_id=session_id)
    print("Memory ready. Type 'quit' to end, 'remember KEY=VALUE' to store facts.\n")

    try:
        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ('quit', 'exit', 'q'):
                break
            if user_input.lower().startswith("remember ") and "=" in user_input:
                _, kv = user_input.split(" ", 1)
                k, v = kv.split("=", 1)
                gemma.remember(k.strip(), v.strip())
                continue

            reply = gemma.chat(user_input)
            print(f"\nGemma: {reply}\n")

    except KeyboardInterrupt:
        pass
    finally:
        gemma.end_session()

