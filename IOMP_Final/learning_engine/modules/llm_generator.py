import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Active Groq models in priority order — DO NOT add llama-3.1-70b-versatile (decommissioned)
GROQ_MODEL_FALLBACK = [
    "llama-3.3-70b-versatile",   # best quality
    "llama-3.1-8b-instant",      # fast fallback
    "mixtral-8x7b-32768",        # fallback mixtral
    "gemma2-9b-it",              # last resort
]

def generate_llm_content(messages):
    """
    Calls the Groq API with automatic model fallback.
    On rate limit (429) or decommission (400 model_decommissioned), tries next model.
    """
    if not os.getenv("GROQ_API_KEY"):
        return "ERROR: No 'GROQ_API_KEY' found in .env file. Real AI generation disabled."

    last_error = ""
    for model in GROQ_MODEL_FALLBACK:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=8000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            err_str = str(e)
            last_error = err_str
            # Fall through to next model on rate limit OR decommissioned model errors
            if any(code in err_str for code in ["429", "rate_limit", "rate limit", "model_decommissioned", "decommissioned", "400"]):
                continue
            # Any other error (auth, bad request, etc.) — fail immediately
            return f"ERROR: API call failed. Details: {err_str}"

    return f"ERROR: All models unavailable. Please wait a few minutes and try again. Details: {last_error}"

def parse_llm_response(response_text):
    """
    Parses the structured output into a dictionary for Streamlit rendering.
    Splits the explanation from the potential quiz payload and parses MCQ questions.
    """
    data = {
        "explanation": response_text.strip(),
        "questions": [],
        "suggestions": []
    }
    
    try:
        import re

        # Parse and remove all explicit SUGGESTIONS blocks; keep only last block to avoid duplicates.
        sugg_blocks = re.findall(r"(?is)SUGGESTIONS:\s*(.*?)\s*END_SUGGESTIONS", response_text)
        if sugg_blocks:
            chosen = sugg_blocks[-1]
            for line in chosen.split('\n'):
                # Strip leading numbering/bullets
                line = re.sub(r"^(\d+[\.\)]|-|\*)\s*", "", line.strip()).strip()
                # Strip END_SUGGESTIONS token even if it appears mid-line or end-of-line
                line = re.sub(r"(?i)\s*END_SUGGESTIONS\s*$", "", line).strip()
                line = re.sub(r"(?i)\s*SUGGESTIONS:\s*$", "", line).strip()
                # Only add if non-empty and not a bare token
                if line and line.upper() not in {"SUGGESTIONS:", "END_SUGGESTIONS", "SUGGESTIONS"}:
                    data["suggestions"].append(line)
            response_text = re.sub(r"(?is)SUGGESTIONS:\s*.*?\s*END_SUGGESTIONS", "", response_text).strip()

        # Additional safety: strip any stray END_SUGGESTIONS or SUGGESTIONS: tokens left anywhere in explanation
        response_text = re.sub(r"(?im)^\s*END_SUGGESTIONS\s*$", "", response_text).strip()
        response_text = re.sub(r"(?im)^\s*SUGGESTIONS:\s*$", "", response_text).strip()
        # Strip inline END_SUGGESTIONS that appears after content on same line
        response_text = re.sub(r"(?i)\s*END_SUGGESTIONS", "", response_text).strip()

        # Fallback: if model prints plain "Suggestions:" list without END_SUGGESTIONS
        if not data["suggestions"]:
            loose_match = re.search(r"(?is)\bSuggestions:\s*((?:\n\s*\d+[\.\)]\s+.*){2,8})", response_text)
            if loose_match:
                for line in loose_match.group(1).split("\n"):
                    line = re.sub(r"^\s*\d+[\.\)]\s*", "", line.strip()).strip()
                    if line:
                        data["suggestions"].append(line)
                response_text = response_text.replace(loose_match.group(0), "").strip()

        # Safety cleanup — strip all forms of suggestion tokens from explanation
        response_text = re.sub(r"(?im)^\s*SUGGESTIONS:\s*$", "", response_text)
        response_text = re.sub(r"(?im)^\s*END_SUGGESTIONS\s*$", "", response_text)
        response_text = re.sub(r"(?i)END_SUGGESTIONS", "", response_text)
        response_text = response_text.strip()

        # Only split when there is strong evidence of MCQ payload.
        # This avoids truncating regular lessons that include markdown separators or numbered lists.
        has_mcq_markers = bool(
            re.search(r"(?im)^\s*QUESTION\s*[\d\.\:]*\s*:", response_text)
            and re.search(r"(?im)^\s*OPTIONS\s*:\s*$", response_text)
            and re.search(r"(?im)^\s*CORRECT[_\s]*ANSWER\s*:\s*[A-D]\s*$", response_text)
        )

        if has_mcq_markers:
            match = re.search(r"(?im)^\s*QUESTION\s*[\d\.\:]*\s*:", response_text)
            split_point = match.start() if match else 0
            data["explanation"] = response_text[:split_point].strip()
            questions_payload = response_text[split_point:].strip()
        else:
            questions_payload = ""
            data["explanation"] = response_text.strip()

        # Question parsing - Split by standard question markers
        # Captures: "QUESTION:", "1.", "2.", "Question 1:", etc.
        q_blocks = re.split(r"(?i)(?:\n|^)\s*(?:QUESTION\s*[\d\.\:]*|\d+[\)\.]\s*(?:QUESTION)?)\s*", questions_payload)
        
        for block in q_blocks:
            block = block.strip()
            if not block or len(block) < 10: continue
            
            # --- EXTRACT QUESTION TEXT ---
            # Question text ends before the first option (A/B/C/D)
            q_match = re.search(r"(?is)^(.*?)(?=\s*[A-D][\)\.\:]\s+)", block)
            if not q_match: 
                # Try finding options anywhere if the block is small
                q_match = re.search(r"(?is)^(.*?)(?=\s*[A-D][\)\.\:])", block)
            
            if not q_match: continue
            q_text = q_match.group(1).strip()
            # Clean up residual markers
            q_text = re.sub(r"(?is)^(---\s*|###\s*.*?|OPTIONS:?\s*|QUIZ:?\s*|QUESTION:?\s*)", "", q_text).strip()
            
            # --- EXTRACT OPTIONS ---
            # Find all strings like "A) text" or "A. text" or "A: text"
            opts_list = []
            opt_matches = re.findall(r"(?i)\s+([A-D])[\)\.\:]\s+(.*?)(?=\s+[A-D][\)\.\:]\s+|(?:\n|$)\s*(?:CORRECT|ANSWER|KEY|Answer|Correct|Key):?|$)", block, re.S)
            
            for label, text in opt_matches:
                clean_text = text.strip()
                if clean_text:
                    opts_list.append(f"{label.upper()}) {clean_text}")
            
            # --- EXTRACT CORRECT ANSWER ---
            # Look for ANY form of Answer/Correct/Key followed by A, B, C, or D
            ans_match = re.search(r"(?i)(?:CORRECT|ANSWER|KEY|Answer|Correct|Key|Ans):\s*([A-D])", block)
            if not ans_match:
                # Try finding a standalone letter A-D at the very end of the block
                ans_match = re.search(r"(?i)(?:\s+)([A-D])\s*$", block)
            
            if len(opts_list) >= 4 and ans_match:
                data["questions"].append({
                    "question": q_text,
                    "options": opts_list[:4],
                    "correct_answer": ans_match.group(1).upper()
                })
                
    except Exception as e:
        print(f"DEBUG: Parsing failure in llm_generator.py - {str(e)}")
    
    return data
