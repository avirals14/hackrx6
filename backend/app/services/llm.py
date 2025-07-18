import json
import re
from typing import Any, Dict, List
import logging
import os
from dotenv import load_dotenv

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

import google.generativeai as genai
import openai

# Load .env for Gemini and OpenAI API keys
load_dotenv(dotenv_path=".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print("[DEBUG] OpenAI Key:", OPENAI_API_KEY)
print("[DEBUG] Gemini Key:", GEMINI_API_KEY)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_parser")

def build_reasoning_prompt(structured_query: dict, retrieved_chunks: list) -> str:
    # Compose a strict, clause-anchored, audit-grade prompt
    prompt = (
        "You are a strict insurance claim evaluator. Your task is to determine if a treatment is covered under a specific insurance policy based ONLY on the structured query and the exact clauses provided below.\n"
        "You must only make decisions that can be supported by specific text in the provided clauses. If a decision cannot be made definitively, mark it as 'pending_info'.\n"
        "Always mention the exact Clause number(s) you used in justification. Never invent or generalize clause numbers.\n"
        "\nStructured Query:\n"
        f"{json.dumps(structured_query, indent=2)}\n"
        "\nRelevant Clauses:\n"
        + "\n".join([
            f"Clause {chunk['metadata'].get('clause_number', i+1)}: {chunk['text']}" for i, chunk in enumerate(retrieved_chunks)
        ]) +
        "\n\nOutput ONLY valid JSON with no markdown. Format:\n"
        '{\n'
        '  "decision": "approved | denied | pending_info | excluded",\n'
        '  "amount": 0,\n'
        '  "justification": "Reason for decision, referencing specific clause numbers if applicable.",\n'
        '  "clauses_used": ["Clause 4.2", "Clause 6.1"],\n'
        '  "summary": "Plain-language user-facing output",\n'
        '  "confidence": 0.0\n'
        '}\n'
        "Also include a confidence score between 0.0 and 1.0 based on your certainty from the provided clauses. Use 0.95+ only for clear approvals/denials. Use <0.5 for vague cases.\n"
        "Do NOT include code fences, markdown, or any explanation outside the JSON."
    )
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


def run_llm_with_priority(prompt: str) -> str:
    # 1. Try OpenAI
    try:
        logger.info("Trying OpenAI GPT-4o...\n")
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",  # or another preferred model
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info("OpenAI GPT-4o succeeded.\n")
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"OpenAI failed: {e}\n")
    # 2. Try Gemini Pro
    try:
        logger.info("Trying Gemini Pro...\n")
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        logger.info("Gemini Pro succeeded.\n")
        return response.text.strip()
    except Exception as e:
        logger.warning(f"Gemini Pro failed: {e}\n")
    # 3. Try local LLMs (Ollama)
    if not ollama:
        raise ImportError("ollama is not installed.")
    try:
        logger.info("Trying local LLM (Ollama)...\n")
        response = ollama.chat(
            model="llama3:8b",
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info("Local LLM (Ollama) succeeded.\n")
        return response["message"]["content"].strip()
    except Exception as e:
        logger.error(f"All LLMs failed: {e}\n")
        return f"All LLMs failed: {e}"


def extract_json_from_response(content: str) -> dict:
    logger.info("Trying regex+json.loads for LLM output...")
    logger.debug(f"Raw LLM output: {content}")
    content = content.strip()
    if content.startswith('```'):
        content = content.strip('`\n')
    cleaned_lines = []
    for line in content.splitlines():
        line = line.strip()
        if line in {'...', '…', ''}:
            continue
        if line.startswith('#') or line.lower().startswith('note') or line.lower().startswith('explanation'):
            continue
        cleaned_lines.append(line)
    cleaned_content = '\n'.join(cleaned_lines)
    match = re.search(r'\{[\s\S]*?\}', cleaned_content)
    if match:
        return json.loads(match.group(0))
    raise ValueError("No JSON object found in LLM response")


def repair_with_llm(raw_content: str) -> dict:
    logger.info("Trying LLM repair for LLM output...")
    if not ollama:
        raise ImportError("ollama is not installed.")
    repair_prompt = (
        "Convert the following text into valid JSON. Only return the JSON object. "
        "Use double quotes for all keys and string values. No comments, explanations, or text before/after the JSON. "
        "Arrays must contain only double-quoted strings or numbers. No trailing commas. Ensure all braces are closed.\n"
        f"Text: {raw_content}"
    )
    response = ollama.chat(
        model="gemma3n:e2b",  # Use a fast, lightweight model for repair
        messages=[{"role": "user", "content": repair_prompt}]
    )
    content = response["message"]["content"].strip()
    logger.debug(f"LLM repair output: {content}")
    try:
        return json.loads(content)
    except Exception:
        if demjson3:
            try:
                logger.info("Trying demjson3 for LLM repair output...")
                return demjson3.decode(content)
            except Exception:
                pass
        if rapidjson:
            try:
                logger.info("Trying rapidjson for LLM repair output...")
                return rapidjson.loads(content)
            except Exception:
                pass
        raise ValueError("LLM repair failed to produce valid JSON.")


def repair_with_gemini(raw_content: str, api_key: str = None) -> dict:
    if not api_key:
        api_key = GEMINI_API_KEY
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")
    prompt = (
        "You are a JSON repair and validation assistant. "
        "Given the following text, return only a valid JSON object. "
        "Do NOT include any explanation, comments, or text before/after the JSON. "
        "If the input is already valid JSON, return it unchanged. "
        "Input:\n"
        f"{raw_content}"
    )
    response = model.generate_content(prompt)
    content = response.text.strip()
    try:
        return json.loads(content)
    except Exception as e:
        raise ValueError(f"Gemini Pro failed to produce valid JSON: {e}\nRaw output: {content}")


def run_llm_reasoning(structured_query: Dict[str, Any], retrieved_chunks: List[Dict[str, Any]], primary_model: str = "llama3:8b", fallback_model: str = "gemma3n:e2b") -> Dict[str, Any]:
    prompt = build_reasoning_prompt(structured_query, retrieved_chunks)
    content = run_llm_with_fallback(prompt, primary_model, fallback_model)
    logger.info("Received LLM output. Attempting to parse...")
    logger.debug(f"Raw LLM output: {content}")
    try:
        result = extract_json_from_response(content)
        logger.info("Parsed LLM output with regex+json.loads.")
    except Exception as e:
        if demjson3:
            try:
                logger.info("Trying demjson3 for LLM output...")
                result = demjson3.decode(content)
                logger.info("Parsed LLM output with demjson3.")
            except Exception as e2:
                if rapidjson:
                    try:
                        logger.info("Trying rapidjson for LLM output...")
                        result = rapidjson.loads(content)
                        logger.info("Parsed LLM output with rapidjson.")
                    except Exception as e3:
                        try:
                            result = repair_with_llm(content)
                            logger.info("Parsed LLM output with LLM repair.")
                        except Exception as e4:
                            try:
                                logger.info("Trying Gemini Pro for LLM output...")
                                result = repair_with_gemini(content)
                                logger.info("Parsed LLM output with Gemini Pro.")
                            except Exception as e5:
                                logger.error(f"All repair steps failed: {e}; {e2}; {e3}; {e4}; {e5}")
                                return {"error": "Failed to parse and repair LLM response (demjson3, rapidjson, LLM, Gemini)", "raw_response": content, "exception": f"{e}; Repair failed: {e2}; RapidJSON failed: {e3}; LLM failed: {e4}; Gemini failed: {e5}"}
                else:
                    try:
                        result = repair_with_llm(content)
                        logger.info("Parsed LLM output with LLM repair.")
                    except Exception as e4:
                        try:
                            logger.info("Trying Gemini Pro for LLM output...")
                            result = repair_with_gemini(content)
                            logger.info("Parsed LLM output with Gemini Pro.")
                        except Exception as e5:
                            logger.error(f"All repair steps failed: {e}; {e2}; {e4}; {e5}")
                            return {"error": "Failed to parse and repair LLM response (demjson3, LLM, Gemini)", "raw_response": content, "exception": f"{e}; Repair failed: {e2}; LLM failed: {e4}; Gemini failed: {e5}"}
        elif rapidjson:
            try:
                logger.info("Trying rapidjson for LLM output...")
                result = rapidjson.loads(content)
                logger.info("Parsed LLM output with rapidjson.")
            except Exception as e3:
                try:
                    result = repair_with_llm(content)
                    logger.info("Parsed LLM output with LLM repair.")
                except Exception as e4:
                    try:
                        logger.info("Trying Gemini Pro for LLM output...")
                        result = repair_with_gemini(content)
                        logger.info("Parsed LLM output with Gemini Pro.")
                    except Exception as e5:
                        logger.error(f"All repair steps failed: {e}; {e3}; {e4}; {e5}")
                        return {"error": "Failed to parse and repair LLM response (rapidjson, LLM, Gemini)", "raw_response": content, "exception": f"{e}; RapidJSON failed: {e3}; LLM failed: {e4}; Gemini failed: {e5}"}
        else:
            try:
                result = repair_with_llm(content)
                logger.info("Parsed LLM output with LLM repair.")
            except Exception as e4:
                try:
                    logger.info("Trying Gemini Pro for LLM output...")
                    result = repair_with_gemini(content)
                    logger.info("Parsed LLM output with Gemini Pro.")
                except Exception as e5:
                    logger.error(f"All repair steps failed: {e}; {e4}; {e5}")
                    return {"error": "Failed to parse and repair LLM response (LLM, Gemini)", "raw_response": content, "exception": f"{e}; LLM failed: {e4}; Gemini failed: {e5}"}
    summary = None
    if isinstance(result, dict):
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