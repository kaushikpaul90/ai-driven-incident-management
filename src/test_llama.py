import ollama

response = ollama.chat(
    model="llama3",
    messages=[{"role": "user", "content": "Explain what a TLB error is."}],
)

print(response["message"]["content"])