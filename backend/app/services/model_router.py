def choose_model(task: str) -> str:
    if task == "parsing":
        return "gemma3n:e2b"
    elif task == "reasoning":
        return "llama3:8b"
    else:
        return "gemma3n:e2b"  # default fallback 