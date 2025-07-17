import json
import re
from typing import Any, Dict, List

try:
    import ollama
except ImportError:
    ollama = None

try:
    import demjson3
except ImportError:
    demjson3 = None

try:
    import rapidjson
except ImportError:
    rapidjson = None

def build_reasoning_prompt(structured_query: Dict[str, Any], retrieved_chunks: List[Dict[str, Any]]) -> str:
    prompt = (
        "You are an expert insurance policy assistant.\n"
        "Given the following structured query and relevant policy document clauses, reason step by step and output a JSON with fields: decision, amount, justification (with clauses and explanation).\n"
        f"Structured Query: {json.dumps(structured_query)}\n"
        f"Relevant Clauses:\n"
    )
    for idx, chunk in enumerate(retrieved_chunks, 1):
        prompt += f"Clause {idx}: {chunk['text']}\n"
    prompt += "\nRespond with a valid JSON object only, using double quotes for all keys and string values, double quotes around all array elements, no trailing commas, and do not include any explanation, comments, or text before or after the JSON. Ensure all braces are closed."
    return prompt


def run_llm_with_fallback(prompt: str, primary_model: str, fallback_model: str = None) -> str:
    if not ollama:
        raise ImportError("ollama is not installed.")
    try:
        response = ollama.chat(
            model=primary_model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"].strip()
    except Exception as e:
        if fallback_model:
            try:
                response = ollama.chat(
                    model=fallback_model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response["message"]["content"].strip()
            except Exception as e2:
                return f"Both models failed: {e}, {e2}"
        else:
            return f"Model failed: {e}"


def extract_json_from_response(content: str) -> dict:
    # Remove code block markers if present
    content = content.strip()
    if content.startswith('```'):
        content = content.strip('`\n')
    # Remove lines that are just ellipses or non-JSON tokens
    cleaned_lines = []
    for line in content.splitlines():
        line = line.strip()
        # Skip lines that are just '...', '…', or empty
        if line in {'...', '…', ''}:
            continue
        # Skip lines that look like comments or explanations
        if line.startswith('#') or line.lower().startswith('note') or line.lower().startswith('explanation'):
            continue
        cleaned_lines.append(line)
    cleaned_content = '\n'.join(cleaned_lines)
    # Find the first {...} block in the cleaned response
    match = re.search(r'\{[\s\S]*?\}', cleaned_content)
    if match:
        return json.loads(match.group(0))
    raise ValueError("No JSON object found in LLM response")


def repair_with_llm(raw_content: str) -> dict:
    """Attempt to repair malformed JSON using the local LLM."""
    if not ollama:
        raise ImportError("ollama is not installed.")
    repair_prompt = (
        "Convert the following text into valid JSON. Only return the JSON object.\n"
        f"Text: {raw_content}"
    )
    response = ollama.chat(
        model="gemma3n:e2b",  # Use a fast, lightweight model for repair
        messages=[{"role": "user", "content": repair_prompt}]
    )
    content = response["message"]["content"].strip()
    # Try to parse the result as JSON
    try:
        return json.loads(content)
    except Exception:
        # Try demjson3 or rapidjson as a last resort
        if demjson3:
            try:
                return demjson3.decode(content)
            except Exception:
                pass
        if rapidjson:
            try:
                return rapidjson.loads(content)
            except Exception:
                pass
        raise ValueError("LLM repair failed to produce valid JSON.")


def run_llm_reasoning(structured_query: Dict[str, Any], retrieved_chunks: List[Dict[str, Any]], primary_model: str = "llama3:8b", fallback_model: str = "gemma3n:e2b") -> Dict[str, Any]:
    prompt = build_reasoning_prompt(structured_query, retrieved_chunks)
    content = run_llm_with_fallback(prompt, primary_model, fallback_model)
    # Try to extract JSON from the response
    try:
        result = extract_json_from_response(content)
    except Exception as e:
        # Try to repair with demjson3 if available
        if demjson3:
            try:
                result = demjson3.decode(content)
            except Exception as e2:
                # Try rapidjson if available
                if rapidjson:
                    try:
                        result = rapidjson.loads(content)
                    except Exception as e3:
                        # Try LLM repair as last resort
                        try:
                            result = repair_with_llm(content)
                        except Exception as e4:
                            return {"error": "Failed to parse and repair LLM response (demjson3, rapidjson, LLM)", "raw_response": content, "exception": f"{e}; Repair failed: {e2}; RapidJSON failed: {e3}; LLM failed: {e4}"}
                else:
                    # Try LLM repair as last resort
                    try:
                        result = repair_with_llm(content)
                    except Exception as e4:
                        return {"error": "Failed to parse and repair LLM response (demjson3, LLM)", "raw_response": content, "exception": f"{e}; Repair failed: {e2}; LLM failed: {e4}"}
        elif rapidjson:
            try:
                result = rapidjson.loads(content)
            except Exception as e3:
                # Try LLM repair as last resort
                try:
                    result = repair_with_llm(content)
                except Exception as e4:
                    return {"error": "Failed to parse and repair LLM response (rapidjson, LLM)", "raw_response": content, "exception": f"{e}; RapidJSON failed: {e3}; LLM failed: {e4}"}
        else:
            # Try LLM repair as last resort
            try:
                result = repair_with_llm(content)
            except Exception as e4:
                return {"error": "Failed to parse and repair LLM response (LLM)", "raw_response": content, "exception": f"{e}; LLM failed: {e4}"}
    # Add a summary field for user-facing applications
    summary = None
    if isinstance(result, dict):
        # Try to use a plain-language answer if present
        if "decision" in result and isinstance(result["decision"], str):
            summary = result["decision"]
        elif "justification" in result and isinstance(result["justification"], str):
            summary = result["justification"]
        elif "justification" in result and isinstance(result["justification"], dict):
            explanation = result["justification"].get("explanation")
            if explanation:
                summary = explanation
        if not summary and "decision" in result:
            summary = f"Decision: {result['decision']}"
        result["summary"] = summary
    return result