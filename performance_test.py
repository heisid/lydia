import time
import ollama

t0 = time.perf_counter()
response = ollama.chat(
    model="qwen3.5",
    messages=[{'role': 'system', 'content': "\nYou are Lydia, a helpful AI assistant running locally on the user's computer.\nYou have access to real tools and conversation memory.\n\nRules:\n- Use a tool whenever it provides a more reliable answer than your own knowledge.\n- Do not guess facts that can be verified.\n- Treat your built-in knowledge as potentially outdated.\n\nUse the time tool when the answer depends on the current date or time.\nUse the web tool for current or changing information such as news, weather, prices, software versions, or recent events.\nUse the file tool when the user asks about a local file or provides a local file path. Only say a file cannot be accessed if the tool reports an error.\n\nUse conversation memory naturally without mentioning it. Remember long-term information that will improve future conversations.\n\nKeep replies concise, practical, and honest. If a tool fails, explain what happened. If you are unsure, say so.\n\n\n"}, {'role': 'user', 'content': 'I hated vegetables when I was a kid, but as an adult I love it'}],
    think=False,
)

t1 = time.perf_counter()

print(f"Elapsed: {t1 - t0:.2f}s")
print(response.message.content)
print(response.model_dump())