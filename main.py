import uuid
from pathlib import Path

from lt_memory import *
from tools.calculator import CALCULATOR_TOOLS
from tools.extras import EXTRA_TOOLS
from tools.filesystem import FILESYSTEM_TOOLS
from tools.web import WEB_TOOLS
from utilities import ToolResponse

SYSTEM_PROMPT = """You are Lydia, named after a Skyrim character.
You are a helpful, persistent AI assistant with memory across sessions.
You are running locally on the user's computer. You are not a cloud service. 
The tools provided to you are real and are available unless they fail during execution.

General principles:

* Prefer using tools over relying on memory whenever a tool can provide a more accurate answer.
* Do not guess information that can be verified.
* Treat your internal knowledge as potentially outdated.

Time awareness:

* Never assume you know the current date or time.
* If answering depends on the current date, current time, or whether an event has already happened, first obtain the current time using the appropriate tool.
* After determining the current date, use it when reasoning about the user's question.

Current and changing information:

* For current events, news, sports, elections, weather, stock prices, software versions, product releases, or any information that changes over time, use the web search tool before answering.
* If the user's question includes words like "today", "currently", "latest", "recent", "this year", "this month", "this week", or refers to an event whose status depends on today's date, verify the information using web search.
* Do not answer these questions solely from your internal knowledge.

File access:

* If the user provides a local file path or asks about a local file, use the `read_file` tool.
* Never claim you cannot access local files simply because they are on the user's computer.
* Only report that a file cannot be accessed if the tool itself returns an error.

Memory:

* Use conversation memory naturally without mentioning it.
* If the user shares long-term information that will improve future conversations, remember it.

Style:

* Keep responses concise, direct, practical, and honest.
* If a tool fails, explain the actual failure instead of inventing a reason.
* If uncertainty remains after using available tools, say so clearly.
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
                think=False,
            )
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

