import streamlit as st
import os, sys
import re
from difflib import SequenceMatcher
from urllib.parse import quote
import requests

sys.path.append(os.path.dirname(__file__))

from modules.database import (register_user, login_user, get_chat_history, get_session_history, save_chat,
                              get_learner_profile_stats, init_database, save_batch_quiz_attempts,
                              get_topic_learning_level, delete_chat_session, reset_learner_state, reset_session_stats)
from modules.nlp_module import process_user_input
from modules.rl_agent import choose_action, update_q
from modules.prompt_builder import build_prompt, build_followup_prompt
from modules.llm_generator import generate_llm_content, parse_llm_response
from modules.reward_engine import calculate_reward

init_database()

st.set_page_config(page_title="Learning Engine", layout="wide", page_icon="✨", initial_sidebar_state="expanded")

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")

def is_strong_password(password):
    return bool(PASSWORD_REGEX.match(password or ""))

# ════════════════════════════════════════════════════════════════════════════
#  MODERN PREMIUM DESIGN SYSTEM
#  Inspired by: 21st Dev (bold minimalism), Pinterest (visual discovery),
#  UI Movements (sophisticated animations)
# ════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Bricolage+Grotesque:wght@500;700;800&display=swap');

:root {
    --bg-app: #f7f4ee;
    --bg-sidebar: rgba(255, 252, 246, 0.88);
    --bg-card: #fffcf7;
    --bg-chat-ai: #fff8ed;
    --bg-hover: #f5ede1;

    --text-primary: #231f1a;
    --text-secondary: #62584a;
    --text-muted: #7d7162;

    --accent: #0f766e;
    --accent-1: #0f766e;
    --accent-2: #db5f33;
    --accent-3: #d97706;

    --grad-user: linear-gradient(130deg, #0f766e 0%, #14b8a6 100%);
    --grad-primary: linear-gradient(135deg, #0f766e 0%, #db5f33 100%);
    --grad-accent: linear-gradient(135deg, #ef4444 0%, #f59e0b 100%);
    --grad-cool: radial-gradient(circle at 20% 20%, rgba(15, 118, 110, 0.24), transparent 55%);

    --border: rgba(35, 31, 26, 0.12);
    --border-light: rgba(35, 31, 26, 0.1);
    --border-medium: rgba(15, 118, 110, 0.3);
    --border-glow: rgba(219, 95, 51, 0.26);

    --shadow-sm: 0 6px 16px rgba(35, 31, 26, 0.08);
    --shadow-md: 0 14px 32px rgba(35, 31, 26, 0.12);
    --shadow-lg: 0 28px 56px rgba(35, 31, 26, 0.16);
    --shadow-glow: 0 12px 36px rgba(15, 118, 110, 0.24);

    --radius: 18px;
}

* {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text-primary) !important;
    -webkit-font-smoothing: antialiased;
}

h1, h2, h3, .signup-title, .dash-title, .qz-done-txt {
    font-family: 'Bricolage Grotesque', sans-serif !important;
    letter-spacing: -0.02em;
}

header, footer, #MainMenu { visibility: hidden !important; }

.stApp {
    background:
        radial-gradient(circle at 10% 0%, rgba(15, 118, 110, 0.18), transparent 28%),
        radial-gradient(circle at 90% 18%, rgba(219, 95, 51, 0.16), transparent 32%),
        repeating-linear-gradient(45deg, rgba(98, 88, 74, 0.02) 0px, rgba(98, 88, 74, 0.02) 2px, transparent 2px, transparent 8px),
        var(--bg-app) !important;
}

[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-light) !important;
    backdrop-filter: blur(14px);
}

.sb-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 4px;
}

.sb-icon {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--grad-primary);
    box-shadow: var(--shadow-sm);
}

.sb-name {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 1.12rem;
    font-weight: 800;
}

.sb-sec {
    margin: 14px 0 8px;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-muted) !important;
}

div[data-testid="column"]:has(span#chat-col-marker),
div[data-testid="column"]:has(span#profile-col-marker),
div[data-testid="column"]:has(span#auth-col-marker) {
    min-height: 100vh !important;
}

.landing-wrap {
    min-height: 64vh;
    border-radius: 34px;
    margin: 20px 0 28px;
    padding: 54px 28px 44px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    background:
        linear-gradient(160deg, rgba(15, 118, 110, 0.95) 0%, rgba(219, 95, 51, 0.9) 100%),
        var(--bg-card);
    box-shadow: var(--shadow-lg);
    position: relative;
    overflow: hidden;
    animation: rise-in 0.6s ease-out;
}

.landing-wrap::before,
.landing-wrap::after {
    content: '';
    position: absolute;
    border-radius: 999px;
    filter: blur(8px);
}

.landing-wrap::before {
    width: 230px;
    height: 230px;
    top: -70px;
    right: -40px;
    background: rgba(255, 255, 255, 0.22);
    animation: drift 9s ease-in-out infinite;
}

.landing-wrap::after {
    width: 180px;
    height: 180px;
    left: -40px;
    bottom: -60px;
    background: rgba(255, 236, 179, 0.28);
    animation: drift 11s ease-in-out infinite reverse;
}

.landing-logo {
    width: 78px;
    height: 78px;
    border-radius: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 18px;
    font-size: 2.4rem;
    background: rgba(255, 255, 255, 0.16);
    border: 1px solid rgba(255, 255, 255, 0.26);
}

.landing-greet,
.landing-sub,
.landing-logo {
    color: #fffdf9 !important;
    position: relative;
    z-index: 1;
}

.landing-greet {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: clamp(1.9rem, 4vw, 3rem);
    font-weight: 800;
    margin-bottom: 10px;
}

.landing-sub {
    font-size: 1rem;
    opacity: 0.94;
    margin-bottom: 10px;
}

.login-card, .signup-card {
    background: linear-gradient(180deg, #fffcf7 0%, #fff8ed 100%);
    border: 1px solid var(--border-light);
    border-radius: 26px;
    padding: 44px 38px;
    box-shadow: var(--shadow-md);
    margin-bottom: 16px;
}

.signup-logo {
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-size: 0.76rem;
    color: var(--accent-1) !important;
    margin-bottom: 14px;
}

.signup-title, .login-form-head {
    font-size: clamp(1.7rem, 4vw, 2.3rem);
    text-align: center;
    margin-bottom: 8px;
}

.signup-sub, .login-form-sub {
    color: var(--text-secondary) !important;
    text-align: center;
    margin-bottom: 24px;
}

.login-divider-line {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 24px 0;
    color: var(--text-muted) !important;
}

.login-divider-line::before,
.login-divider-line::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border-light);
}

.stTextInput > div > div > input {
    background: #fffefb !important;
    border: 1px solid var(--border-light) !important;
    border-radius: 14px !important;
    padding: 13px 14px !important;
    color: var(--text-primary) !important;
    transition: all 0.2s ease !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent-1) !important;
    box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.14) !important;
}

[data-testid="stButton"] > button {
    border-radius: 14px !important;
    border: 1px solid var(--border-light) !important;
    background: #fffefb !important;
    font-weight: 600 !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
    box-shadow: var(--shadow-sm) !important;
}

[data-testid="stButton"] > button:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md) !important;
    border-color: var(--border-medium) !important;
}

[data-testid="stButton"] > button[kind="primary"] {
    border: none !important;
    color: #ffffff !important;
    background: var(--grad-primary) !important;
}

.dash-bar {
    margin: 10px 0 24px;
    padding: 24px 28px;
    border-radius: 24px;
    border: 1px solid var(--border-light);
    background: linear-gradient(140deg, #fff9ef 0%, #fffcf7 100%);
    box-shadow: var(--shadow-sm);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}

.dash-title {
    font-size: clamp(1.4rem, 3.1vw, 2.1rem);
}

.dash-pill {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    background: #fff;
    border: 1px solid var(--border-glow);
    padding: 8px 14px;
    color: var(--accent-1) !important;
    font-weight: 700;
}

[data-testid="stChatMessage"] {
    padding: 0 !important;
    margin-bottom: 12px !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    margin-left: auto;
    max-width: 78%;
    border-radius: 20px 20px 6px 20px !important;
    background: var(--grad-user) !important;
    border: none !important;
    box-shadow: var(--shadow-sm) !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) * {
    color: #ffffff !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-radius: 20px !important;
    border: 1px solid var(--border-light) !important;
    background: var(--bg-chat-ai) !important;
    box-shadow: var(--shadow-sm) !important;
}

[data-testid="stChatInput"] {
    margin-top: 18px;
    border-radius: 16px !important;
    border: 1px solid var(--border-light) !important;
    background: #ffffff !important;
    box-shadow: var(--shadow-sm) !important;
}

[data-testid="stChatInput"] textarea {
    background: #ffffff !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--accent-1) !important;
    box-shadow: var(--shadow-glow) !important;
}

.qz-wrap {
    margin: 18px 0;
    border-radius: 20px;
    padding: 24px;
    border: 1px solid var(--border-light);
    background: linear-gradient(145deg, #fff8ed 0%, #fffcf7 100%);
    box-shadow: var(--shadow-sm);
}

.qz-eye {
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--accent-1) !important;
    margin-bottom: 8px;
}

.qz-q {
    font-size: 1.02rem;
    line-height: 1.55;
    font-weight: 600;
    margin-bottom: 10px;
}

.qz-done {
    margin: 18px 0;
    border-radius: 22px;
    padding: 28px;
    background: var(--grad-primary) !important;
    box-shadow: var(--shadow-md);
}

.qz-done-txt {
    color: #fffdf9 !important;
    font-size: clamp(1.2rem, 3vw, 1.8rem);
}

.stRadio label {
    border-radius: 12px !important;
    border: 1px solid var(--border-light) !important;
    background: #fffefb !important;
    margin-bottom: 8px !important;
}

.stRadio label:hover {
    border-color: var(--accent-1) !important;
    background: var(--bg-hover) !important;
}

div[data-testid="stExpander"] {
    border-radius: 16px !important;
    border: 1px solid var(--border-light) !important;
    background: #fffdf8 !important;
    box-shadow: var(--shadow-sm) !important;
}

[data-testid="stAlert"] {
    border-radius: 14px !important;
    border: 1px solid transparent !important;
}

.stSuccess { background: #ebfbf4 !important; border-color: #34d399 !important; }
.stInfo { background: #eef8ff !important; border-color: #38bdf8 !important; }
.stWarning { background: #fff7df !important; border-color: #f59e0b !important; }
.stError { background: #ffefee !important; border-color: #ef4444 !important; }

hr { border-color: var(--border-light) !important; }

.stCaption {
    color: var(--text-muted) !important;
}

pre {
    border-radius: 14px !important;
    border: 1px solid var(--border-light) !important;
    background: #1f2937 !important;
}

pre code {
    color: #e5f9ff !important;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, var(--accent-1), var(--accent-2));
    border-radius: 999px;
}

@keyframes rise-in {
    from { transform: translateY(16px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

@keyframes drift {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-18px); }
}

[data-testid="stSpinner"] p {
    color: var(--accent-1) !important;
    font-weight: 700;
}

@media (max-width: 960px) {
    .dash-bar {
        flex-direction: column;
        align-items: flex-start;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        max-width: 100%;
    }

    .login-card, .signup-card {
        padding: 34px 24px;
    }
}

</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════
# SESSION STATE (same as before)
# ════════════════════════════════════════
defaults = {
    "logged_in": False, "learner_id": None, "username": None,
    "chat_history": [], "show_signup": False,
    "pending_quiz": None, "quiz_completed": False, "wrong_answers": [],
    "current_session_id": None, "current_topic": None, "show_topic_options": False,
    "quiz_skipped": False, "quiz_total_questions": 0,
    "post_quiz_suggestions": [], "post_quiz_topic": None,
    "session_accuracy": 0.0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.current_session_id is None:
    import uuid
    st.session_state.current_session_id = str(uuid.uuid4())

# ════════════════════════════════════════
# SYSTEM PROMPT (same as before)
# ════════════════════════════════════════
def get_system_prompt(accuracy_score, current_topic, chat_history_text):
    if accuracy_score <= 30:
        band = "BEGINNER"
        depth_rules = """
- Assume zero prior knowledge.
- Explain core ideas in simple words first, then add one deeper layer.
- Define every technical term immediately when first used.
- Use one relatable analogy and one concrete real-world example.
- Keep the lesson compact: around 250-450 words.
"""
    elif accuracy_score <= 70:
        band = "INTERMEDIATE"
        depth_rules = """
- Assume basic familiarity, then focus on mechanisms and reasoning.
- Use correct terminology with brief inline definitions when needed.
- Include practical examples and common mistakes.
- Keep the lesson focused: around 400-700 words.
"""
    else:
        band = "ADVANCED"
        depth_rules = """
- Assume strong fundamentals.
- Prioritize architecture, trade-offs, edge cases, and performance implications.
- Compare at least two approaches where relevant.
- Keep the lesson dense but readable: around 600-900 words.
"""

    return f"""You are an expert tutor helping a learner with one topic at a time.

LEARNER PROFILE:
- Accuracy Score: {accuracy_score}/100
- Band: {band}
- Topic: {current_topic}
- Recent Chat Context:
{chat_history_text}

ADAPTIVE DEPTH RULES:
{depth_rules}

RESPONSE RULES:
- Answer the user's latest query directly and stay on topic.
- Use clean markdown only. Do not use decorative separators, ASCII art, or placeholder text.
- Structure the explanation with clear headings:
  1) What it is
  2) How it works
  3) Example
  4) Key takeaways
- If the user asks for a specific task (assignment, list, steps, code, comparison), do that task first.
- Avoid repetition, filler, and vague statements.
- If the topic is unclear/gibberish/inappropriate, return exactly: INVALID_TOPIC

MANDATORY SUGGESTIONS FOOTER:
After the explanation, output exactly one suggestions block in this format:
SUGGESTIONS:
1. [specific follow-up question]
2. [specific follow-up question]
3. [specific follow-up question]
4. [specific follow-up question]
5. [specific follow-up question]
END_SUGGESTIONS

Do not output anything after END_SUGGESTIONS."""

# [All other function implementations remain exactly the same - keeping original logic unchanged]
def generate_quiz_from_content(topic, lesson_text, learner_level):
    lesson_excerpt = (lesson_text or "")[:3500]
    subtopic_msgs = [
        {"role": "system", "content": "Extract exactly 5 key subtopics from the lesson. Return numbered list only."},
        {"role": "user", "content": f"Topic: {topic}\nLesson content:\n{lesson_excerpt}\n\nReturn only 5 subtopics."}
    ]
    raw_subtopic_text = generate_llm_content(subtopic_msgs)
    subtopics = []
    for line in (raw_subtopic_text or "").splitlines():
        clean = re.sub(r"^\s*\d+[\)\.\-]?\s*", "", line).strip(" -")
        if clean:
            subtopics.append(clean)
    subtopics = subtopics[:5]
    subtopic_targets = ", ".join(subtopics) if subtopics else "main subtopics from this lesson"

    quiz_system = f"""You are an AI tutor creating a quiz for the topic '{topic}'.
Create between 3 and 7 MCQs (usually 5) to test understanding of the SAME lesson text.
Rules:
- Use ONLY concepts present in the lesson content.
- Keep difficulty aligned to learner level: {learner_level}.
- Ensure broad coverage: test different subtopics from: {subtopic_targets}
- DO NOT include any subtopic trace or tags like [Subtopic: ...] in the question text. Keep questions direct and clean.
- Return only this format:
---
QUESTION: [Text]
OPTIONS:
A) [Text]
B) [Text]
C) [Text]
D) [Text]
CORRECT_ANSWER: [A/B/C/D]
"""
    quiz_messages = [
        {"role": "system", "content": quiz_system},
        {"role": "user", "content": f"Lesson content:\n{lesson_excerpt}\n\nGenerate the quiz now."}
    ]
    raw_quiz = generate_llm_content(quiz_messages)
    if raw_quiz.startswith("ERROR:") or raw_quiz.strip() == "INVALID_TOPIC":
        return None
    parsed_quiz = parse_llm_response(raw_quiz)
    if parsed_quiz.get("questions") and len(parsed_quiz["questions"]) > 0:
        return parsed_quiz
    return None

def generate_mistake_feedback(topic, lesson_text, wrong_answers):
    if not wrong_answers:
        return ""
    lesson_excerpt = (lesson_text or "")[:3200]
    wrong_bundle = "\n".join(
        [
            f"- Q: {w.get('question','')}\n  Your answer: {w.get('your_answer','')}\n  Correct answer: {w.get('correct_answer','')}"
            for w in wrong_answers[:5]
        ]
    )
    msgs = [
        {
            "role": "system",
            "content": (
                f"You are an adaptive tutor for '{topic}'. "
                "Explain exactly where learner is wrong for each item. "
                "For each wrong question, provide: wrong point, correct concept, and one anti-mistake tip. "
                "Keep it clear and specific."
            ),
        },
        {
            "role": "user",
            "content": f"Lesson:\n{lesson_excerpt}\n\nWrong responses:\n{wrong_bundle}",
        },
    ]
    raw = generate_llm_content(msgs)
    if raw.startswith("ERROR:") or raw.strip() == "INVALID_TOPIC":
        return ""
    return raw.strip()

def order_suggestions(topic, suggestions):
    cleaned = [s.strip() for s in (suggestions or []) if s and s.strip()]
    if len(cleaned) <= 1:
        return cleaned

    try:
        base_list = "\n".join([f"{idx+1}. {s}" for idx, s in enumerate(cleaned)])
        msgs = [
            {
                "role": "system",
                "content": (
                    f"Order suggestions for topic '{topic}' as a progressive learning path. "
                    "First should be the immediate next concept after the main topic, then build from basic to advanced. "
                    "Return only numbered reordered lines, reusing the same suggestions."
                ),
            },
            {"role": "user", "content": base_list},
        ]
        raw = generate_llm_content(msgs)
        ordered = []
        for line in (raw or "").splitlines():
            item = re.sub(r"^\s*\d+[\)\.\-]?\s*", "", line).strip()
            if item and item in cleaned and item not in ordered:
                ordered.append(item)
        for s in cleaned:
            if s not in ordered:
                ordered.append(s)
        return ordered[:5]
    except Exception:
        return cleaned[:5]

def generate_remedial_explanation(topic, lesson_text, wrong_answers, learner_level):
    weak_points = ", ".join([w.get("question", "") for w in wrong_answers[:5]]) or "key parts of this topic"
    lesson_excerpt = (lesson_text or "")[:3500]
    remedial_system = f"""You are an adaptive tutor for '{topic}'.
Learner scored below 40%. Re-teach the SAME topic in a better, clearer way.
Rules:
- Keep this same topic only. Do not switch to other topic.
- Explain weak points: {weak_points}
- Use simple language, short sentences, and better analogies.
- Provide a Wikipedia-like narrative explanation (not rigid section template).
- Include exactly 3 easy examples.
- At the end include suggestions block:
SUGGESTIONS:
1. ...
2. ...
3. ...
4. ...
5. ...
END_SUGGESTIONS
"""
    msgs = [
        {"role": "system", "content": remedial_system},
        {"role": "user", "content": f"Original lesson content:\n{lesson_excerpt}\n\nPlease re-explain better for weak understanding."}
    ]
    raw = generate_llm_content(msgs)
    if raw.startswith("ERROR:") or raw.strip() == "INVALID_TOPIC":
        return None
    return parse_llm_response(raw)

def fetch_reference_context(topic):
    topic = (topic or "").strip()
    if not topic:
        return ""

    try:
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(topic)}"
        r = requests.get(summary_url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            extract = (data.get("extract") or "").strip()
            if extract:
                return extract[:6000]
    except Exception:
        pass

    try:
        search_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": topic,
                "format": "json",
            },
            timeout=8,
        )
        if search_resp.status_code == 200:
            sdata = search_resp.json()
            hits = sdata.get("query", {}).get("search", [])
            if not hits:
                return ""
            title = hits[0].get("title", topic)
            extract_resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "prop": "extracts",
                    "explaintext": 1,
                    "redirects": 1,
                    "titles": title,
                    "format": "json",
                },
                timeout=8,
            )
            if extract_resp.status_code == 200:
                edata = extract_resp.json()
                pages = edata.get("query", {}).get("pages", {})
                for p in pages.values():
                    extract = (p.get("extract") or "").strip()
                    if extract:
                        return extract[:6000]
    except Exception:
        pass

    return ""

def _normalize_text_for_match(text):
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def _is_explicit_followup_query(user_input):
    text = (user_input or "").lower()
    followup_patterns = [
        r"\bthis\b", r"\bthat\b", r"\bit\b", r"\bthese\b", r"\bthose\b",
        r"\babove\b", r"\bprevious\b", r"\bearlier\b", r"\bfrom summary\b",
        r"\bfrom the summary\b", r"\bon this\b", r"\babout this\b"
    ]
    return any(re.search(p, text) for p in followup_patterns)

def _is_new_topic_request(user_input, current_topic, nlp_topic):
    if not current_topic:
        return True

    text = (user_input or "").strip().lower()
    candidate_topic = (nlp_topic or "").strip() or (user_input or "").strip()

    # If user explicitly refers to existing context, treat as follow-up.
    if _is_explicit_followup_query(text):
        return False

    current_norm = _normalize_text_for_match(current_topic)
    candidate_norm = _normalize_text_for_match(candidate_topic)
    if not candidate_norm:
        return False

    if candidate_norm in current_norm or current_norm in candidate_norm:
        return False

    similarity = SequenceMatcher(None, current_norm, candidate_norm).ratio()
    explicit_new_topic_markers = [
        r"\bwhat is\b", r"\bexplain\b", r"\bintroduction to\b", r"\bbasics of\b",
        r"\boverview of\b", r"\bteach me\b", r"\bdefine\b"
    ]
    has_new_topic_marker = any(re.search(p, text) for p in explicit_new_topic_markers)

    # Very different topic phrases should switch topic even without explicit marker.
    if similarity < 0.42:
        return True

    return has_new_topic_marker and similarity < 0.6

def _dedupe_generated_text(text):
    src = (text or "").strip()
    if not src:
        return src

    # If the model repeats the entire answer twice, keep the first half.
    half = len(src) // 2
    if half > 400:
        left = src[:half].strip()
        right = src[half:].strip()
        if left and right and left == right:
            return left

    # Remove duplicated paragraphs while preserving order.
    blocks = [b.strip() for b in re.split(r"\n\s*\n", src) if b.strip()]
    seen = set()
    unique_blocks = []
    for b in blocks:
        key = re.sub(r"\s+", " ", b).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique_blocks.append(b)

    if unique_blocks:
        return "\n\n".join(unique_blocks).strip()
    return src

# ════════════════════════════════════════
# LOGIN PAGE
# ════════════════════════════════════════
def show_login_page():
    st.write("")
    st.write("")
    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown('<span id="auth-col-marker"></span>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="login-card" style="padding-top:30px;">
                <div class="signup-logo">✨ LEARNING ENGINE</div>
                <div class="signup-title">Welcome Back</div>
                <div class="signup-sub">Sign in to continue your learning journey.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Username or Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            st.caption("Password: 8+ chars, uppercase, lowercase, number, special character")
            st.write("")
            submit = st.form_submit_button("Sign In  →", type="primary", use_container_width=True)

        if submit:
            success, learner_id = login_user(username, password)
            if success:
                st.session_state.logged_in  = True
                st.session_state.learner_id = learner_id
                st.session_state.username   = username
                st.rerun()
            else:
                st.error("Invalid username/email or password.")

        st.markdown("<div class='login-divider-line'>or</div>", unsafe_allow_html=True)

        if st.button("Create a new account", type="primary", use_container_width=True):
            st.session_state.show_signup = True
            st.rerun()

# ════════════════════════════════════════
# SIGNUP PAGE
# ════════════════════════════════════════
def show_signup_page():
    st.write(""); st.write("")
    _, center, _ = st.columns([1, 1.3, 1])
    with center:
        st.markdown('<span id="auth-col-marker"></span>', unsafe_allow_html=True)
        st.markdown("""
        <div class="signup-card">
            <div class="signup-logo">✨ LEARNING ENGINE</div>
            <div class="signup-title">Start Learning Today</div>
            <div class="signup-sub">Join a community of curious minds. Free, forever.</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("signup_form"):
            full_name = st.text_input("Full Name", placeholder="Ada Lovelace")
            username  = st.text_input("Email or Username", placeholder="ada@example.com")
            password  = st.text_input("Password", type="password", placeholder="min. 8 characters")
            st.caption("Use 8+ chars: uppercase, lowercase, number, special character.")
            st.write("")
            submit = st.form_submit_button("Create Account  →", type="primary", use_container_width=True)

        if submit:
            if not is_strong_password(password):
                st.error("Password must include 8+ characters, uppercase, lowercase, number, and special character.")
                st.stop()
            success, msg = register_user(full_name, username, password)
            if success:
                st.success("✅ Account created! You can now sign in.")
                st.session_state.show_signup = False
                st.rerun()
            else:
                st.error(f"Error: {msg}")

        st.write("")
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.show_signup = False
            st.rerun()

# ════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════
def show_dashboard():
    with st.sidebar:
        uname   = st.session_state.username or "Learner"
        initial = uname[0].upper()

        st.markdown(f"""
        <div class="sb-brand" style="border:none; margin-bottom:12px;">
            <div class="sb-icon">✨</div>
            <div class="sb-name">Copilot</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("💬  New Chat", use_container_width=True, type="primary"):
            import uuid
            reset_session_stats(st.session_state.learner_id)
            st.session_state.update({
                "chat_history": [], "pending_quiz": None,
                "quiz_completed": False, "wrong_answers": [],
                "current_topic": None,
                "current_session_id": str(uuid.uuid4()),
                "post_quiz_suggestions": [], "post_quiz_topic": None,
                "session_accuracy": 0.0,
            })
            st.rerun()

        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='sb-sec'>📜 Chat History</div>", unsafe_allow_html=True)

        db_history = get_chat_history(st.session_state.learner_id)
        seen = set()
        if db_history:
            for item in db_history:
                sid, topic_full, created_at = item
                if sid not in seen:
                    seen.add(sid)
                    snippet = topic_full[:24] + "…" if len(topic_full) > 24 else topic_full
                    st.caption(created_at.split()[0])
                    
                    hc1, hc2 = st.columns([5, 1])
                    with hc1:
                        if st.button(f"📖  {snippet}", key=f"h_{sid}", use_container_width=True):
                            past = get_session_history(st.session_state.learner_id, sid)
                            restored = []
                            for m in past:
                                restored.append({"role":"user",      "content": m[0]})
                                restored.append({"role":"assistant", "text":    m[1]})
                            st.session_state.update({
                                "chat_history": restored, "pending_quiz": None,
                                "quiz_completed": False, "wrong_answers": [],
                                "current_session_id": sid,
                                "current_topic": past[0][0] if past else None,
                                "post_quiz_suggestions": [], "post_quiz_topic": None,
                                "session_accuracy": 0.0,
                            })
                            st.rerun()
                    with hc2:
                        if st.button("🗑️", key=f"del_{sid}", use_container_width=True, help="Delete"):
                            delete_chat_session(st.session_state.learner_id, sid)
                            if st.session_state.current_session_id == sid:
                                import uuid
                                reset_session_stats(st.session_state.learner_id)
                                st.session_state.update({
                                    "chat_history": [], "pending_quiz": None, "quiz_completed": False,
                                    "wrong_answers": [], "current_topic": None, 
                                    "current_session_id": str(uuid.uuid4()), "post_quiz_suggestions": [],
                                    "post_quiz_topic": None, "session_accuracy": 0.0,
                                })
                            st.rerun()
        else:
            st.markdown("<div style='font-size:0.82rem;color:var(--text-secondary);padding:10px 0 4px;'>No sessions yet</div>", unsafe_allow_html=True)

        st.write("")
        st.markdown("<div class='sb-sec'>Account</div>", unsafe_allow_html=True)
        if st.button("⎋  Logout", use_container_width=True):
            reset_session_stats(st.session_state.learner_id)
            st.session_state.update({
                "logged_in": False, "learner_id": None, "username": None,
                "chat_history": [], "pending_quiz": None,
                "quiz_completed": False, "wrong_answers": [],
                "post_quiz_suggestions": [], "post_quiz_topic": None,
                "session_accuracy": 0.0,
            })
            st.rerun()

        # Profile Section
        st.markdown("<div style='margin-top:32px; border-top:1px solid var(--border-light); padding-top:24px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(240, 147, 251, 0.1) 100%); border-radius: 16px; padding: 20px; border: 1px solid var(--border-glow);">
            <div style="font-size: 0.85rem; font-weight: 700; color: var(--accent-1); margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.5px;">Your Profile</div>
        """, unsafe_allow_html=True)

        stats = get_learner_profile_stats(st.session_state.learner_id, st.session_state.current_topic)
        st.markdown(f"""
        <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border-light);">
            <div style="font-size: 0.9rem; color: var(--text-secondary);">Level</div>
            <div style="font-size: 1rem; font-weight: 700; color: var(--text-primary);">🏅 {stats['level']}</div>
        </div>
        <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border-light);">
            <div style="font-size: 0.9rem; color: var(--text-secondary);">Accuracy</div>
            <div style="font-size: 1rem; font-weight: 700; color: var(--accent-1);">🎯 {stats['accuracy']:.1f}%</div>
        </div>
        <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; padding: 8px 0;">
            <div style="font-size: 0.9rem; color: var(--text-secondary);">Topics</div>
            <div style="font-size: 1rem; font-weight: 700; color: var(--text-primary);">📚 {stats['topics_explored']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # Main Content Area
    _, col_center, _ = st.columns([0.05, 1, 0.05], gap="small")

    with col_center:
        st.markdown('<span id="chat-col-marker"></span>', unsafe_allow_html=True)

        # Landing Page
        if not st.session_state.chat_history and not st.session_state.pending_quiz:
            hour = __import__("datetime").datetime.now().hour
            greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 18 else "Good Evening"
            user_name = st.session_state.get('username', 'Learner')
            
            st.markdown(f"""
            <div class="landing-wrap">
                <div class="landing-logo">✨</div>
                <div class="landing-greet">{greeting}, {user_name}</div>
                <div class="landing-sub">What would you like to explore today?</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Suggestion Chips
            chips = ["Quantum Computing", "Ancient Rome", "Photosynthesis", "Python Multithreading", "Economics 101", "Human Anatomy"]
            st.markdown('<div class="chip-grid">', unsafe_allow_html=True)
            cols = st.columns(3)
            for idx, c_text in enumerate(chips):
                with cols[idx % 3]:
                    if st.button(c_text, key=f"chip_{idx}", use_container_width=True, type="secondary"):
                        run_learning_flow(c_text)
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        else:
            # Active Session
            topic_label = st.session_state.current_topic.title() if st.session_state.current_topic else "Session"
            st.markdown(f"""
            <div class="dash-bar">
                <div class="dash-title">Exploring</div>
                <div class="dash-pill">🔖 {topic_label}</div>
            </div>
            """, unsafe_allow_html=True)

            # Render Chat Messages
            for i, msg in enumerate(st.session_state.chat_history):
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(msg.get("text", ""))
                        
                        in_content_suggs = msg.get("suggestions", [])
                        if in_content_suggs:
                            st.write("")
                            st.markdown("**✨ SUGGESTIONS:**")
                            for idx, s in enumerate(in_content_suggs[:5], start=1):
                                st.markdown(f"{idx}. {s}")

                        if "quiz_available" in msg and msg["quiz_available"]:
                            if st.button("🎯 Take Quiz", key=f"qo_{i}", type="primary"):
                                st.session_state.pending_quiz = msg["quiz_available"]
                                st.session_state.wrong_answers = []
                                st.session_state.quiz_skipped = False
                                st.session_state.quiz_total_questions = len(msg["quiz_available"]["data"].get("questions", []))
                                msg.pop("quiz_available")
                                st.rerun()
                        else:
                            topic_val = msg.get("current_topic", st.session_state.current_topic or "")
                            lesson_text = msg.get("text", "").strip()
                            if topic_val and lesson_text and st.button("🎯 Generate Quiz", key=f"gen_quiz_{i}", type="secondary"):
                                with st.spinner("Creating quiz..."):
                                    level_now = get_topic_learning_level(st.session_state.learner_id, topic_val)
                                    quiz_data = generate_quiz_from_content(topic_val, lesson_text, level_now)
                                if quiz_data:
                                    st.session_state.pending_quiz = {
                                        "topic": topic_val,
                                        "data": quiz_data,
                                        "state": level_now,
                                        "strategy": choose_action(level_now),
                                        "current_question_index": 0
                                    }
                                    st.session_state.wrong_answers = []
                                    st.session_state.quiz_skipped = False
                                    st.session_state.quiz_total_questions = len(quiz_data.get("questions", []))
                                    st.rerun()
                                else:
                                    st.warning("Could not generate quiz. Please try again.")

        # Quiz Interface
        if st.session_state.pending_quiz:
            questions = st.session_state.pending_quiz["data"].get("questions", [])
            if not questions:
                st.warning("Quiz could not be loaded. Please try again.")
                st.session_state.pending_quiz = None
                st.stop()

            st.markdown(f"""
            <div class="qz-wrap">
                <div class="qz-eye">📝 Assessment · {len(questions)} Questions</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form(key="batch_quiz_form"):
                user_answers = []
                for idx, q_data in enumerate(questions):
                    st.markdown(f"<div class='qz-q'>{idx+1}. {q_data['question']}</div>", unsafe_allow_html=True)
                    ans = st.radio("Options", q_data["options"], index=None, label_visibility="collapsed", key=f"q_{idx}")
                    user_answers.append(ans)
                    st.write("")
                
                c1, c2 = st.columns([2, 1])
                with c1: submitted = st.form_submit_button("Submit All Answers", type="primary", use_container_width=True)
                with c2: skipped = st.form_submit_button("Skip", type="primary", use_container_width=True)
                
            if submitted:
                if None in user_answers:
                    st.warning("Please answer all questions before submitting.")
                    st.stop()
                
                results_list = []
                st.session_state.wrong_answers = []
                for idx, q_data in enumerate(questions):
                    sel = user_answers[idx].strip()[0].upper()
                    cor = q_data["correct_answer"].strip().upper()
                    is_correct = (sel == cor)
                    results_list.append(is_correct)
                    if not is_correct:
                        cor_text = next((o for o in q_data["options"] if o.startswith(cor)), cor)
                        st.session_state.wrong_answers.append({
                            "question": q_data["question"],
                            "your_answer": user_answers[idx], "correct_answer": cor_text
                        })
                
                save_batch_quiz_attempts(st.session_state.learner_id, st.session_state.pending_quiz["topic"], results_list)
                
                batch_score = sum(results_list) / len(results_list) if results_list else 0
                
                if st.session_state.session_accuracy == 0.0:
                    st.session_state.session_accuracy = batch_score
                else:
                    st.session_state.session_accuracy = round(st.session_state.session_accuracy * 0.4 + batch_score * 0.6, 3)

                feedback = "positive" if batch_score >= 0.6 else "negative"
                r = calculate_reward(feedback, st.session_state.pending_quiz["state"], st.session_state.pending_quiz["strategy"])
                update_q(st.session_state.pending_quiz["state"], st.session_state.pending_quiz["strategy"], r)
                st.session_state.last_batch_score = batch_score

                topic_now = st.session_state.pending_quiz["topic"]
                raw_suggestions = st.session_state.pending_quiz.get("suggestions", [])
                st.session_state.post_quiz_topic = topic_now
                st.session_state.post_quiz_suggestions = order_suggestions(topic_now, raw_suggestions)
                last_assistant_text = ""
                for m in reversed(st.session_state.chat_history):
                    if m.get("role") == "assistant":
                        last_assistant_text = m.get("text", "")
                        break

                if st.session_state.wrong_answers:
                    wrong_feedback = generate_mistake_feedback(
                        topic_now, last_assistant_text, st.session_state.wrong_answers
                    )
                    if wrong_feedback:
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "text": "❌ Review these specific points where you went wrong:\n\n" + wrong_feedback,
                            "suggestions": [],
                            "quiz_available": None,
                            "current_topic": topic_now
                        })
                        save_chat(
                            st.session_state.learner_id,
                            st.session_state.current_session_id,
                            f"MISTAKE_FEEDBACK::{topic_now}",
                            wrong_feedback
                        )

                if batch_score < 0.4:
                    st.session_state.quiz_completed = False
                    with st.spinner("Low score detected. Re-explaining..."):
                        remedial = generate_remedial_explanation(
                            topic_now,
                            last_assistant_text,
                            st.session_state.wrong_answers,
                            st.session_state.pending_quiz["state"]
                        )
                    if remedial:
                        remedial_text = remedial.get("explanation", "")
                        remedial_suggestions = remedial.get("suggestions", [])
                        remedial_quiz = generate_quiz_from_content(
                            topic_now,
                            remedial_text,
                            st.session_state.pending_quiz["state"]
                        )
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "text": remedial_text,
                            "suggestions": remedial_suggestions,
                            "quiz_available": {
                                "topic": topic_now,
                                "data": remedial_quiz,
                                "state": st.session_state.pending_quiz["state"],
                                "strategy": st.session_state.pending_quiz["strategy"],
                                "current_question_index": 0
                            } if remedial_quiz and remedial_quiz.get("questions") else None,
                            "current_topic": topic_now
                        })
                        save_chat(
                            st.session_state.learner_id,
                            st.session_state.current_session_id,
                            f"AUTO_REMEDIAL::{topic_now}",
                            remedial_text
                        )
                
                st.session_state.pending_quiz = None
                st.session_state.quiz_completed = False if batch_score < 0.4 else True
                st.session_state.quiz_skipped = False
                st.rerun()

            if skipped:
                topic_now = st.session_state.pending_quiz["topic"]
                raw_suggestions = st.session_state.pending_quiz.get("suggestions", [])
                st.session_state.post_quiz_topic = topic_now
                st.session_state.post_quiz_suggestions = order_suggestions(topic_now, raw_suggestions)
                st.session_state.pending_quiz = None
                st.session_state.quiz_completed = True
                st.session_state.quiz_skipped = True
                st.rerun()

        # Quiz Complete Screen
        elif st.session_state.quiz_completed:
            if st.session_state.quiz_skipped:
                st.info("⏭️ Quiz skipped. Continue exploring whenever ready!")
            else:
                st.markdown("""
                <div class="qz-done">
                    <div class="qz-done-txt">🎉 Assessment Complete</div>
                </div>
                """, unsafe_allow_html=True)

                num_wrong = len(st.session_state.wrong_answers)
                total     = st.session_state.quiz_total_questions or 5
                num_correct = total - num_wrong

                if num_wrong == 0:
                    st.success(f"🏆 Perfect! All {total} answers correct!")
                elif num_correct > 0:
                    st.info(f"✨ Great! You got **{num_correct}** out of **{total}** correct.")
                else:
                    st.warning(f"💪 You got {num_correct} out of {total}. Keep practicing!")

                if st.session_state.wrong_answers:
                    with st.expander("📋 Review Incorrect Answers", expanded=True):
                        for w in st.session_state.wrong_answers:
                            st.markdown(f"**Q:** {w['question']}")
                            st.markdown(f"❌ Your answer: `{w['your_answer']}`")
                            st.markdown(f"✅ Correct: `{w['correct_answer']}`")
                            st.markdown("---")

            # Suggestions after quiz
            if st.session_state.get("post_quiz_suggestions"):
                st.markdown("### 🌟 Recommended Next Topics")
                ordered = st.session_state.post_quiz_suggestions[:5]
                for idx, s in enumerate(ordered, start=1):
                    st.markdown(f"{idx}. {s}")
                
                cols = st.columns(min(len(ordered), 3))
                for idx, s in enumerate(ordered[:3]):
                    with cols[idx]:
                        if st.button(f"Learn →", key=f"post_quiz_sugg_{idx}", type="primary", use_container_width=True):
                            st.session_state.quiz_completed = False
                            run_learning_flow(f"__SUGGESTION__:{s}")
                            st.rerun()

            c1, c2 = st.columns([1, 1], gap="small")
            with c1:
                if st.button("Dive Deeper", use_container_width=True, type="primary"):
                    st.session_state.quiz_completed = False
                    user_input = f"Dive deeper into {st.session_state.current_topic}. Provide advanced details and deeper explanations."
                    run_learning_flow(user_input)
                    st.rerun()
            with c2:
                if st.button("New Topic", type="primary", use_container_width=True):
                    st.session_state.quiz_completed = False
                    st.session_state.current_topic  = None
                    st.session_state.post_quiz_suggestions = []
                    st.session_state.post_quiz_topic = None
                    st.rerun()

        # Chat Input
        user_input = st.chat_input("Explore a topic or ask a follow-up…")
        if user_input:
            run_learning_flow(user_input)
            st.rerun()

def run_learning_flow(user_input):
    st.session_state.update({
        "pending_quiz": None, "quiz_completed": False, "wrong_answers": [],
        "post_quiz_suggestions": [], "post_quiz_topic": None,
    })

    is_suggestion_click = isinstance(user_input, str) and user_input.startswith("__SUGGESTION__:")
    if is_suggestion_click:
        user_input = user_input[len("__SUGGESTION__:"):].strip()
        st.session_state.current_topic = user_input

    if not is_suggestion_click and re.fullmatch(r"[1-5]", (user_input or "").strip()):
        num = int(user_input.strip()) - 1
        suggestions = st.session_state.get("post_quiz_suggestions", [])
        
        if not suggestions:
            for m in reversed(st.session_state.chat_history):
                if m.get("role") == "assistant" and m.get("suggestions"):
                    suggestions = m.get("suggestions")
                    break
                    
        if suggestions and num < len(suggestions):
            chosen = suggestions[num]
            user_input = chosen
            st.session_state.current_topic = chosen
            is_suggestion_click = True

    vague_patterns = [
        r"explain in detail", r"tell me more", r"go deeper",
        r"elaborate", r"i don.?t get it",
        r"go on", r"continue", r"again"
    ]
    is_vague = (not is_suggestion_click) and any(
        re.search(p, user_input, re.IGNORECASE) for p in vague_patterns
    )

    resolved_topic = st.session_state.current_topic if is_vague else user_input
    if not resolved_topic:
        msg = "Hello! What topic would you like to explore?"
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "text": msg})
        save_chat(st.session_state.learner_id, st.session_state.current_session_id, user_input, msg)
        return

    nlp = process_user_input(user_input)
    prompt_topic = nlp.get("topic")

    if is_suggestion_click:
        pass
    elif not is_vague:
        st.session_state.current_topic = prompt_topic if prompt_topic else user_input
    elif not st.session_state.current_topic:
        st.session_state.current_topic = prompt_topic or user_input

    topic = st.session_state.current_topic or "not yet set"
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Detect when the user asks for a summary, so we summarize the latest lesson
    # instead of generating a brand-new lesson from scratch.
    summary_patterns = [
        r"\bsummary\b", r"\bsummarize\b", r"\bsummarise\b", r"\btldr\b",
        r"\bbrief\b", r"\bin short\b", r"\bshort note\b"
    ]
    is_summary_request = any(re.search(p, user_input, re.IGNORECASE) for p in summary_patterns)

    last_assistant_text = ""
    for m in reversed(st.session_state.chat_history[:-1]):
        if m.get("role") == "assistant" and m.get("text"):
            last_assistant_text = m.get("text", "").strip()
            break

    has_prior_context = bool(last_assistant_text)
    is_new_topic = _is_new_topic_request(user_input, st.session_state.current_topic, nlp.get("topic", ""))
    if has_prior_context and is_new_topic and not is_suggestion_click and not is_vague:
        st.session_state.current_topic = prompt_topic if prompt_topic else user_input
        topic = st.session_state.current_topic

    is_context_followup = bool(nlp.get("is_contextual") or is_vague or _is_explicit_followup_query(user_input))
    use_followup_mode = has_prior_context and (is_summary_request or (is_context_followup and not is_new_topic))

    chat_history_lines = []
    for m in st.session_state.chat_history[:-1]:
        role_label = "User" if m["role"] == "user" else "AI"
        content_text = m.get("content", m.get("text", ""))
        chat_history_lines.append(f"{role_label}: {content_text}")
    chat_history_text = "\n".join(chat_history_lines) if chat_history_lines else "No history"

    accuracy_score = int(round(st.session_state.get("session_accuracy", 0.0) * 100))
    api_msgs = []

    if use_followup_mode and is_summary_request:
        summary_system = (
            "You are an expert tutor. Create a precise summary from provided lesson context. "
            "Do not invent facts beyond the context. If context is missing, say so briefly.\n\n"
            "Output structure:\n"
            "1) A concise overview (4-7 bullet points).\n"
            "2) Key terms (3-6 terms with one-line meanings).\n"
            "3) Practical takeaway (2-3 lines).\n\n"
            "At the end include exactly one suggestions block:\n"
            "SUGGESTIONS:\n"
            "1. ...\n2. ...\n3. ...\n4. ...\n5. ...\n"
            "END_SUGGESTIONS"
        )
        api_msgs = [
            {"role": "system", "content": summary_system},
            {
                "role": "user",
                "content": (
                    f"Current topic: {topic}\n"
                    f"User request: {user_input}\n\n"
                    f"Lesson context (source of truth):\n{last_assistant_text[:7000]}"
                ),
            },
        ]
    elif use_followup_mode:
        learner_level = get_topic_learning_level(st.session_state.learner_id, topic)
        followup_prompt = build_followup_prompt(user_input, topic, learner_level, nlp)
        reference_context = fetch_reference_context(topic)
        user_payload = f"Follow-up request: {user_input}\n\nPrior lesson context:\n{last_assistant_text[:7000]}"
        if reference_context:
            user_payload += f"\n\nExternal reference context:\n{reference_context[:1200]}"
        user_payload += "\n\nCRITICAL: Stay grounded in the prior lesson context and include SUGGESTIONS block at the end."
        api_msgs = [
            {"role": "system", "content": followup_prompt},
            {"role": "user", "content": user_payload},
        ]
    else:
        system_prompt_text = get_system_prompt(accuracy_score, topic, chat_history_text)
        api_msgs = [{"role": "system", "content": system_prompt_text}]
        reference_context = fetch_reference_context(topic)
        final_user_msg = user_input
        if reference_context:
            final_user_msg += f"\n\n[Reference: {reference_context[:1000]}]"
        final_user_msg += "\n\nCRITICAL: Include SUGGESTIONS block at the end!"
        api_msgs.append({"role": "user", "content": final_user_msg})

    with st.spinner(f"Generating lesson on **{topic}**…"):
        raw = generate_llm_content(api_msgs)
        if raw.strip() == "INVALID_TOPIC":
            st.session_state.chat_history.append({"role":"assistant","text":"⚠️ Invalid topic. Please try again."})
            return
        elif raw.startswith("ERROR:"):
            st.session_state.chat_history.append({"role":"assistant","text":f"⚠️ {raw}"})
            return
        raw = _dedupe_generated_text(raw)

    parsed = parse_llm_response(raw)
    full_text = parsed["explanation"]
    
    cs = get_topic_learning_level(st.session_state.learner_id, topic)
    strat = choose_action(cs)
    generated_quiz = generate_quiz_from_content(topic, full_text, cs)

    import time
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        simulated_text = ""
        chunk_size = 5
        for i in range(0, len(full_text), chunk_size):
            simulated_text += full_text[i:i+chunk_size]
            message_placeholder.markdown(simulated_text + "|")
            time.sleep(0.005)
            
        final_markdown = simulated_text
        live_suggs = parsed.get("suggestions", [])
        if live_suggs:
            final_markdown += "\n\n**✨ SUGGESTIONS:**\n\n"
            for idx, s in enumerate(live_suggs[:5], start=1):
                final_markdown += f"{idx}. {s}\n"
                
        message_placeholder.markdown(final_markdown)

    st.session_state.chat_history.append({
        "role": "assistant",
        "text": full_text,
        "suggestions": parsed.get("suggestions", []),
        "quiz_available": {
            "topic": topic, "data": generated_quiz, "state": cs,
            "strategy": strat, "current_question_index": 0,
            "suggestions": parsed.get("suggestions", []),
        } if generated_quiz and generated_quiz.get("questions") else None,
        "current_topic": topic
    })
    save_chat(st.session_state.learner_id, st.session_state.current_session_id, user_input, full_text)

# Main Entry Point
if st.session_state.logged_in:
    show_dashboard()
elif st.session_state.show_signup:
    show_signup_page()
else:
    show_login_page()