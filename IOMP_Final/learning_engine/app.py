import streamlit as st
import os, sys
import re
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

st.set_page_config(page_title="Learning Engine", layout="wide", page_icon="🎓")

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")

def is_strong_password(password):
    return bool(PASSWORD_REGEX.match(password or ""))

# ════════════════════════════════════════════════
#  DESIGN SYSTEM (Clean Light Theme)
# ════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');

/* ══ DESIGN TOKENS ══ */
:root {
    --bg-app: #f5f5f5;
    --bg-card: #ffffff;
    --border: #e0e0e0;
    --text-main: #1a1a1a;
    --text-sec: #666666;
    --accent: #7c6ef2;
    --accent-hover: #5b4fd4;
    --accent-light: rgba(124,110,242,0.08);
    --user-bubble: #e8e4ff;
    --input-border: #d0caff;
    
    --msg-success-bg: #d4f5e2;
    --msg-success-txt: #1a5c35;
    --msg-error-bg: #fde8e8;
    --msg-error-txt: #8b1a1a;
    --msg-info-bg: #e8f0ff;
    --msg-info-txt: #1a3a8b;
    --msg-warn-bg: #fff8e1;
    --msg-warn-txt: #7a5c00;
}

/* ══ RESET ══ */
*, html, body { font-family: 'Outfit', sans-serif; box-sizing: border-box; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-app); }
::-webkit-scrollbar-thumb { background: var(--input-border); border-radius: 4px; }

/* ══ SHARED APP BACKGROUND ══ */
.stApp {
    background: var(--bg-app) !important;
    min-height: 100vh;
    color: var(--text-main);
}
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown div {
    color: var(--text-main) !important;
}
h1, h2, h3, h4, h5, h6 { 
    font-family: 'Cormorant Garamond', serif !important; 
    color: var(--text-main) !important; 
}

/* ChatGPT Style Chat Bubbles */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: var(--user-bubble) !important;
    border-radius: 16px;
    padding: 16px !important;
    margin-bottom: 10px;
    color: var(--text-main) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) * {
    color: var(--text-main) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: var(--bg-card) !important;
    color: var(--text-main) !important;
    border-radius: 16px;
    padding: 16px !important;
    margin-bottom: 10px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) * {
    color: var(--text-main) !important;
}

/* Simple readable suggestions */
.sugg-text-list {
    margin-top: 10px;
    padding-left: 18px;
    color: var(--text-main);
}
.sugg-text-list li {
    margin-bottom: 4px;
    color: var(--text-main);
}


/* ════════════════════════════════════
   LOGIN & SIGNUP PAGES
   ════════════════════════════════════ */
.auth-center-wrap {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 30px 20px;
}
.login-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 34px 28px 28px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    max-width: 460px;
    width: 100%;
}

.login-form-head {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.3rem; font-weight: 700; color: var(--text-main);
    line-height: 1.1; margin-bottom: 8px;
}
.login-form-sub { font-size: 0.88rem; color: var(--text-sec); margin-bottom: 36px; }
.login-divider-line {
    display: flex; align-items: center; gap: 12px;
    margin: 18px 0; font-size: 0.76rem; color: var(--text-sec); opacity: 0.7;
}
.login-divider-line::before, .login-divider-line::after {
    content:''; flex:1; height:1px; background: var(--border);
}
.login-footer {
    margin-top: 44px; font-size: 0.73rem;
    color: var(--text-sec); text-align: center;
}

.signup-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 50px 46px 42px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.04);
    max-width: 460px; width: 100%; margin: 0 auto;
}
.signup-logo {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.1rem; font-weight: 700; letter-spacing: 3px;
    text-transform: uppercase; color: var(--accent); margin-bottom: 20px;
}
.signup-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.1rem; font-weight: 700; color: var(--text-main);
    line-height: 1.1; margin-bottom: 6px;
}
.signup-sub { font-size: 0.84rem; color: var(--text-sec); margin-bottom: 28px; }

/* ════════════════════════════════════
   DASHBOARD / LAYOUT
   ════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-main) !important;
}
[data-testid="stSidebar"] button {
    background: #ffffff !important;
    color: #1a1a1a !important;
    border: 1px solid #d9dce8 !important;
}
[data-testid="stSidebar"] button:hover {
    background: #f5f7ff !important;
    color: #1a1a1a !important;
    border-color: #cfd5f6 !important;
}
[data-testid="stSidebar"] button p,
[data-testid="stSidebar"] button span,
[data-testid="stSidebar"] button div {
    color: #1a1a1a !important;
}
[data-testid="stSidebar"] [data-testid="baseButton-primary"] {
    background: var(--accent) !important;
    color: #fff !important;
    border-color: var(--accent) !important;
}

div[data-testid="column"]:has(span#profile-col-marker),
div[data-testid="column"]:has(span#auth-col-marker) {
    background: var(--bg-card) !important;
    border-left: 1px solid var(--border) !important;
    min-height: 100vh !important; padding: 30px 20px !important;
}
div[data-testid="column"]:has(span#chat-col-marker) {
    background: transparent !important;
    padding: 30px 34px !important; min-height: 100vh !important;
}

/* Sidebar brand */
.sb-brand {
    display: flex; align-items: center; gap: 10px;
    padding-bottom: 20px; margin-bottom: 22px;
    border-bottom: 1px solid var(--border);
}
.sb-icon {
    width: 36px; height: 36px; border-radius: 10px; flex-shrink: 0;
    background: var(--accent);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; color: #fff;
}
.sb-name {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.35rem; font-weight: 700; color: var(--text-main); line-height: 1;
}
.sb-sub { font-size: 0.62rem; color: var(--accent); letter-spacing: 2px; text-transform: uppercase; font-weight: 600; }

.sb-user {
    background: var(--accent-light); border: 1px solid var(--input-border);
    border-radius: 14px; padding: 13px 15px;
    display: flex; align-items: center; gap: 11px; margin-bottom: 20px;
}
.sb-av {
    width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
    background: var(--accent);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.95rem; font-weight: 700; color: #fff;
}
.sb-uname { font-size: 0.88rem; font-weight: 600; color: var(--text-main); }
.sb-role  { font-size: 0.68rem; color: var(--accent); letter-spacing: 0.4px; }

.sb-sec {
    font-size: 0.64rem; font-weight: 700; letter-spacing: 2.5px;
    text-transform: uppercase; color: var(--text-sec);
    margin: 18px 0 10px;
}

.dash-bar {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 22px; padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
}
.dash-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.8rem; font-weight: 700; color: var(--text-main); line-height: 1;
}
.dash-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--accent-light); border: 1px solid var(--input-border);
    border-radius: 20px; padding: 5px 14px;
    font-size: 0.77rem; font-weight: 500; color: var(--accent);
}

.prof-head {
    position: relative; border-radius: 16px; overflow: hidden;
    margin-bottom: 18px; height: 115px;
}
.prof-head img {
    width: 100%; height: 100%; object-fit: cover;
    filter: brightness(1.1); display: block;
}
.prof-head-ov {
    position: absolute; inset: 0;
    background: linear-gradient(180deg, transparent 20%, rgba(255,255,255,0.95) 100%);
    display: flex; align-items: flex-end; padding: 14px 16px;
}
.prof-head-lbl {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.05rem; font-weight: 700; color: var(--text-main);
}

.mc {
    background: var(--bg-card);
    border: 1px solid rgba(124,110,242,0.20);
    border-radius: 14px; padding: 15px 14px;
    margin-bottom: 9px; text-align: center;
}
.mc-lbl {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: var(--text-sec); margin-bottom: 7px;
}
.mc-val {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.65rem; font-weight: 700; color: var(--accent);
}

/* Quiz card */
.qz-wrap {
    background: var(--bg-card);
    border: 1px solid var(--input-border);
    border-radius: 20px; padding: 26px 28px;
    margin-top: 14px; margin-bottom: 10px;
}
.qz-eye {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 2.5px;
    text-transform: uppercase; color: var(--accent); margin-bottom: 12px;
}
.qz-q {
    font-family: 'Outfit', sans-serif;
    font-size: 1.1rem; font-weight: 600; color: var(--text-main);
    line-height: 1.4; margin-bottom: 8px;
}
.qz-done {
    position: relative; border-radius: 16px; overflow: hidden;
    margin-bottom: 20px; height: 105px;
    border: 1px solid var(--border);
}
.qz-done-inner {
    position: absolute; inset: 0;
    background: linear-gradient(90deg, var(--bg-card), var(--accent-light));
    display: flex; align-items: center; padding: 0 28px;
}
.qz-done-txt {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.6rem; font-weight: 700; color: var(--accent);
}

/* ════════════════════════════════════
   SHARED FORM ELEMENTS
   ════════════════════════════════════ */
.stTextInput > div > div > input {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-main) !important;
    caret-color: var(--text-main) !important;
    padding: 13px 16px !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-light) !important;
}
.stTextInput label { font-size: 0.76rem !important; font-weight: 600 !important; color: var(--text-sec) !important; }

/* Secondary Base Button */
[data-testid="baseButton-secondary"] {
    border-radius: 8px !important;
    font-weight: 500 !important; font-size: 0.8rem !important;
    padding: 8px 16px !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    color: var(--text-main) !important;
}
[data-testid="baseButton-secondary"]:hover {
    background: #f5f7ff !important;
    border-color: #cfd5f6 !important;
    color: #1a1a1a !important;
}

/* Base Primary Button */
[data-testid="baseButton-primary"] {
    border-radius: 8px !important;
    background: var(--accent) !important;
    border: none !important; color: #fff !important;
    font-weight: 600 !important;
}
[data-testid="baseButton-primary"]:hover {
    background: var(--accent-hover) !important;
}
[data-testid="stButton"] > button {
    background: #ffffff !important;
    color: #1a1a1a !important;
    border: 1px solid #d9dce8 !important;
    border-radius: 10px !important;
    min-height: 46px !important;
}
[data-testid="stButton"] > button:hover {
    background: #f5f7ff !important;
    color: #1a1a1a !important;
    border-color: #cfd5f6 !important;
}
[data-testid="stButton"] > button[kind="primary"] {
    background: var(--accent) !important;
    color: #ffffff !important;
    border-color: var(--accent) !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    background: var(--accent-hover) !important;
}
[data-testid="stFormSubmitButton"] button {
    background: #ffffff !important;
    color: #1a1a1a !important;
    border: 1px solid #d9dce8 !important;
    border-radius: 10px !important;
    min-height: 46px !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    background: #f5f7ff !important;
    color: #1a1a1a !important;
    border-color: #cfd5f6 !important;
}
[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"] {
    background: var(--accent) !important;
    color: #ffffff !important;
    border-color: var(--accent) !important;
}
[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"] {
    background: #ffffff !important;
    color: #1a1a1a !important;
    border-color: #d9dce8 !important;
}

[data-testid="stChatInput"] {
    background: var(--bg-card) !important;
    border: 2px solid var(--input-border) !important;
    border-radius: 14px !important;
}
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div {
    background: transparent !important;
}
[data-testid="stChatInput"] textarea {
    color: var(--text-main) !important; 
    caret-color: var(--text-main) !important;
    font-weight: 500 !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-sec) !important; 
}
[data-testid="stChatInput"] svg {
    fill: var(--accent) !important;
}

.stRadio label, .stRadio p, .stRadio div[role="radiogroup"] label p { 
    color: var(--text-main) !important; 
}
div[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}

[data-testid="stAlert"] p, [data-testid="stAlert"] span {
    color: #1a1a1a !important;
}
div[data-testid="stAlert"] {
    border-radius: 10px !important;
}
.stSuccess { background: var(--msg-success-bg) !important; border-color: var(--msg-success-bg) !important; color: var(--msg-success-txt) !important; }
.stWarning { background: var(--msg-warn-bg) !important; border-color: var(--msg-warn-bg) !important; color: var(--msg-warn-txt) !important; }
.stError   { background: var(--msg-error-bg) !important; border-color: var(--msg-error-bg) !important; color: var(--msg-error-txt) !important; }
.stInfo    { background: var(--msg-info-bg) !important; border-color: var(--msg-info-bg) !important; color: var(--msg-info-txt) !important; }

hr { border-color: var(--border) !important; margin: 14px 0 !important; }
[data-testid="stSpinner"] p { color: var(--accent) !important; }
.stCaption { color: var(--text-sec) !important; font-size: 0.74rem !important; }

code {
    color: var(--accent) !important;
    background: var(--accent-light) !important;
    padding: 2px 6px; border-radius: 4px; font-weight: 600;
}
pre {
    background: var(--bg-app) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 16px !important;
}
pre code {
    color: var(--text-main) !important;
    background: transparent !important;
    font-weight: 400;
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════
# SESSION STATE
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
# SYSTEM PROMPT
# ════════════════════════════════════════
def get_system_prompt(accuracy_score, current_topic, chat_history_text):

    if accuracy_score <= 30:
        band = "BEGINNER"
        depth_rules = """
- Assume zero prior knowledge. The learner is hearing this topic for the very first time.
- Open with one warm, friendly sentence that makes the topic feel approachable, not scary.
- Use real-life analogies throughout — compare to food, sports, daily objects, school life.
- Every technical term must be defined in plain English in the same sentence it appears.
- Write short paragraphs of 3–4 sentences. Never write walls of text.
- Use "Imagine...", "Think of it like...", "It's similar to..." constructions freely.
- Show a concrete example BEFORE introducing the abstract concept behind it.
- Friendly, encouraging, patient tone throughout.
- Minimum 6 sections. Each section minimum 3 full paragraphs.
- Minimum total response: 2000 words. Do not stop early."""

    elif accuracy_score <= 70:
        band = "INTERMEDIATE"
        depth_rules = """
- Assume basic awareness but no deep understanding. Skip surface definitions.
- Go straight to mechanisms — explain HOW and WHY things work, not just WHAT they are.
- Introduce proper terminology with a brief inline explanation when first used.
- Use numbered steps when describing any process, workflow, or sequence.
- Reference real tools, real systems, real people, real case studies by name.
- Compare and contrast with related concepts the learner may already know.
- Medium-to-high technical depth — like a well-written university textbook chapter.
- Minimum 7 sections. Each section minimum 4 full paragraphs.
- Minimum total response: 2500 words. Do not stop early."""

    else:
        band = "ADVANCED"
        depth_rules = """
- Assume strong domain knowledge. Skip all basics and foundational context.
- Use precise technical vocabulary without simplification or hand-holding.
- Discuss edge cases, failure modes, performance trade-offs, and design decisions.
- Reference research, frameworks, benchmarks, and industry standards where relevant.
- Present competing approaches and challenge assumptions — introduce debate.
- Every paragraph must add new insight. Never repeat or pad.
- Graduate-level depth throughout.
- Minimum 8 sections. Each section minimum 5 full paragraphs.
- Minimum total response: 3000 words. Do not stop early."""

    return f"""You are an expert educational author writing a complete textbook chapter.
You are NOT a chatbot giving a quick answer. You are NOT writing a Wikipedia summary.
You are writing the way the world's best teachers write — deep, clear, structured, and specific.

═══════════════════════════════════════════
LEARNER PROFILE
═══════════════════════════════════════════
Accuracy Score : {accuracy_score}/100  →  {band} band
Topic          : {current_topic}
Chat History   :
{chat_history_text}

═══════════════════════════════════════════
DEPTH RULES FOR THIS LEARNER ({band})
═══════════════════════════════════════════
{depth_rules}

═══════════════════════════════════════════
HOW TO DECIDE YOUR SECTION HEADINGS
═══════════════════════════════════════════
This is the most important part of your job. Read it carefully.

Your section headings must be INVENTED specifically for the topic: "{current_topic}"
They must never come from a template. Every topic in the world has a different shape.

STEP 1 — UNDERSTAND THE TOPIC'S DOMAIN
First ask yourself: what kind of topic is this?

  • Is it a SPORT or GAME?
    → Its shape includes: rules, playing field/equipment, positions/roles, scoring, formats/variations, history, famous figures, tournaments, strategy

  • Is it a SCIENCE CONCEPT or BIOLOGICAL PROCESS?
    → Its shape includes: what triggers it, the inputs/outputs, the step-by-step mechanism, the organs/structures involved, why it matters to life, what happens when it fails, real-world applications

  • Is it a TECHNOLOGY or ENGINEERING SYSTEM?
    → Its shape includes: the problem it solves, how it works internally, its architecture/components, how it learns or processes, types/variants, real-world use cases, limitations, future directions

  • Is it a HISTORICAL EVENT or PERIOD?
    → Its shape includes: the root causes, the key actors and their motivations, the sequence of major events, the turning points, the human cost, the aftermath, the long-term legacy

  • Is it a PERSON, FIGURE, or BIOGRAPHY?
    → Its shape includes: early life and influences, rise to prominence, major works or decisions, controversies or challenges, impact on their field, legacy and how they are remembered

  • Is it a COUNTRY, PLACE, or GEOGRAPHY?
    → Its shape includes: location and physical landscape, history and formation, people and culture, economy and trade, government and politics, global relationships, current challenges

  • Is it a MATHEMATICAL or LOGICAL CONCEPT?
    → Its shape includes: the problem it was invented to solve, the formal definition, step-by-step mechanics, visual or intuitive explanation, proofs or derivations (if advanced), common mistakes, real-world applications

  • Is it an ART FORM, MUSIC GENRE, or CULTURAL MOVEMENT?
    → Its shape includes: origins and historical context, defining characteristics, key figures and works, how it evolved over time, regional or global variations, influence on other art forms, relevance today

  • Is it an ECONOMIC, POLITICAL, or SOCIAL CONCEPT?
    → Its shape includes: definition and origin of the idea, the real-world problem it addresses, how it works in practice, arguments in favour, criticisms and limitations, historical or current examples, comparison with alternatives

  • Is it a MEDICAL, HEALTH, or PSYCHOLOGICAL TOPIC?
    → Its shape includes: what it is and who it affects, causes and risk factors, symptoms and diagnosis, what happens in the body or mind, treatment options, prevention, social and emotional dimensions

  • Is it a LANGUAGE, LITERATURE, or PHILOSOPHICAL IDEA?
    → Its shape includes: origin and historical context, core meaning and definition, key thinkers or authors, how it developed over time, real-life implications, criticisms and counter-arguments, relevance today

  • Does it NOT fit any category above?
    → Ask yourself: "What are the 7-9 most important things a person needs to know to truly understand {current_topic}?" Each answer becomes a heading.

STEP 2 — WRITE HEADINGS THAT NAME THE ACTUAL CONTENT
Once you know the domain shape, write headings that:
  ✓ Name the specific concept, mechanism, event, or dimension covered in that section
  ✓ Are worded so that reading the headings alone tells the reader what the chapter covers
  ✓ Feel like they belong in a book specifically about {current_topic}
  ✓ Would change completely if the topic were different

STEP 3 — BANNED HEADINGS (never use these for any topic)
  ✗ "Introduction"
  ✗ "Overview"  
  ✗ "Key Terms"
  ✗ "Step by Step"
  ✗ "Summary" or "Conclusion" or "Key Takeaways"
  ✗ "How it works (simple version)"
  ✗ "A simple analogy" as a standalone section
  ✗ "Real-world example" as a standalone section
  ✗ "What is [Topic]?" as the ONLY first heading — only acceptable if followed by highly specific headings
  ✗ Any heading so generic it could appear in a chapter on any other topic

STEP 4 — SELF-CHECK BEFORE WRITING
Before you write a single word of content, list your planned headings mentally and ask:
  "If I replaced '{current_topic}' with 'Climate Change' or 'The Roman Empire' or 'Quantum Physics',
   would any of these headings still make sense?"
  If YES → that heading is too generic. Make it specific.
  If NO → the heading is correctly specific to {current_topic}. Keep it.

═══════════════════════════════════════════
CONVERSATION CONTINUITY
═══════════════════════════════════════════
You have the full chat history above. Use it:
- Vague inputs ("tell me more", "go deeper", "I don't get it", "continue", "explain in detail"):
  → Stay on {current_topic}. Never ask for clarification. Use history to know what was already covered and add NEW depth.
- Explicit new topic → teach it as a completely fresh chapter with new topic-specific headings
- User typed a number ("1", "2", "3", "4", "5"):
  → They are selecting that numbered suggestion from the previous suggestions list in chat history
  → Find that suggestion, extract the topic it refers to, and teach THAT as a full chapter
  → Never treat the number as a literal message

═══════════════════════════════════════════
SUGGESTIONS — mandatory, once, at the very end
═══════════════════════════════════════════
After all content, append exactly ONE suggestions block.
Each suggestion must be a specific follow-up question about {current_topic} — no generic questions.
Match depth to the {band} band.

FORMAT (copy exactly):
SUGGESTIONS:
1. [specific question]
2. [specific question]
3. [specific question]
4. [specific question]
5. [specific question]
END_SUGGESTIONS

Rules:
✗ Nothing after END_SUGGESTIONS
✗ No suggestions anywhere else in the response
✗ No label prefixes on suggestions
✗ No generic suggestions like "Can you explain more about this?"
✓ Every suggestion must name something specific from or related to {current_topic}"""

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
        # 1) Try Wikipedia summary API
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
        # 2) Fallback to Wikipedia search + page extract
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
            <div class="signup-card" style="padding-top:30px;">
                <div class="signup-logo">LEARNING ENGINE ✦</div>
                <div class="signup-title">Login</div>
                <div class="signup-sub">Sign in to your adaptive learning account.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Username or Email", placeholder="username_or_email")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            st.caption("Password must include 8+ chars, upper, lower, digit, special character.")
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
            <div class="signup-logo">LEARNING ENGINE ✦</div>
            <div class="signup-title">Create your account.</div>
            <div class="signup-sub">Join thousands of learners. Free, forever.</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("signup_form"):
            full_name = st.text_input("Full Name", placeholder="Ada Lovelace")
            username  = st.text_input("Username or Email", placeholder="ada_learns or ada@mail.com")
            password  = st.text_input("Password", type="password", placeholder="min. 8 characters")
            st.caption("Use at least 8 characters with uppercase, lowercase, number, and special character.")
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
        <div class="sb-brand">
            <div class="sb-icon">🎓</div>
            <div>
                <div class="sb-name">Learning Engine</div>
                <div class="sb-sub">AI Tutor</div>
            </div>
        </div>
        <div class="sb-user">
            <div class="sb-av">{initial}</div>
            <div>
                <div class="sb-uname">{uname.title()}</div>
                <div class="sb-role">Active Learner ✦</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("＋  New Session", use_container_width=True, type="primary"):
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

        st.markdown("<div class='sb-sec'>Recent Sessions</div>", unsafe_allow_html=True)

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
                        if st.button("🗑️", key=f"del_{sid}", use_container_width=True, help="Delete Session"):
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
            st.markdown("<div style='font-size:0.82rem;color:var(--text-sec);padding:10px 0 4px;'>No sessions yet.</div>", unsafe_allow_html=True)

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

    # ── CENTER CHAT & RIGHT PROFILE ──
    col_center, col_right = st.columns([3, 1], gap="small")

    with col_right:
        st.markdown('<span id="profile-col-marker"></span>', unsafe_allow_html=True)
        st.markdown("""
        <div class="prof-head">
            <img src="https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=600&q=80" />
            <div class="prof-head-ov">
                <div class="prof-head-lbl">Your Profile</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        stats = get_learner_profile_stats(st.session_state.learner_id, st.session_state.current_topic)

        st.markdown(f"""
        <div class="mc">
            <div class="mc-lbl">Level</div>
            <div class="mc-val lv">🏅 {stats['level']}</div>
        </div>
        <div class="mc">
            <div class="mc-lbl">Accuracy</div>
            <div class="mc-val">🎯 {stats['accuracy']:.1f}%</div>
        </div>
        <div class="mc">
            <div class="mc-lbl">Confidence</div>
            <div class="mc-val cf">🧠 {stats['confidence']}</div>
        </div>
        <div class="mc">
            <div class="mc-lbl">Topics Explored</div>
            <div class="mc-val">📚 {stats['topics_explored']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='mc-lbl' style='margin-top:14px;'>Score Trend</div>", unsafe_allow_html=True)
        if stats['last_5_trend']:
            st.bar_chart(stats['last_5_trend'], height=110)
        else:
            st.markdown(
                "<div style='font-size:0.78rem; color:#aaa; text-align:center; padding:18px 0;'>No quiz data yet</div>",
                unsafe_allow_html=True
            )

    with col_center:
        st.markdown('<span id="chat-col-marker"></span>', unsafe_allow_html=True)
        topic_label = st.session_state.current_topic.title() if st.session_state.current_topic else "New Session"
        st.markdown(f"""
        <div class="dash-bar">
            <div class="dash-title">Learning Session</div>
            <div class="dash-pill">🔖 {topic_label}</div>
        </div>
        """, unsafe_allow_html=True)

        for i, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg.get("text", ""))
                    
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
                            with st.spinner("Creating quiz from this lesson..."):
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
                                st.warning("Could not generate quiz for this lesson. Please try again.")
                    
                    # Suggestions are intentionally shown only once after quiz completion.

        # ── ACTIVE BATCH QUIZ ──
        if st.session_state.pending_quiz:
            questions = st.session_state.pending_quiz["data"].get("questions", [])
            if not questions:
                st.warning("Quiz could not be loaded correctly. Please generate the quiz again.")
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
                            "text": "You are wrong in these specific points. Please review carefully:\n\n" + wrong_feedback,
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

                # Auto-remedial flow when learner scores below 40%
                if batch_score < 0.4:
                    st.session_state.quiz_completed = False
                    with st.spinner("Low score detected. Re-explaining the same topic with better clarity..."):
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

        # ── QUIZ COMPLETE ──
        elif st.session_state.quiz_completed:
            if st.session_state.quiz_skipped:
                st.info("⏭️ Quiz skipped. You can continue with the session.")
            else:
                st.markdown("""
                <div class="qz-done">
                    <div class="qz-done-inner">
                        <div class="qz-done-txt">🎉 Assessment Score Summary</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                num_wrong = len(st.session_state.wrong_answers)
                total     = st.session_state.quiz_total_questions or 5
                num_correct = total - num_wrong

                if num_wrong == 0:
                    st.success(f"🏆 Perfect score! You got {total} out of {total} correct.")
                elif num_correct > 0:
                    st.info(f"✨ Great effort! You got **{num_correct}** out of **{total}** correct.")
                else:
                    st.warning(f"💪 You got {num_correct} out of {total} correct. Review the content and try again!")

                if st.session_state.wrong_answers:
                    with st.expander("📋 Review Incorrect Answers", expanded=True):
                        for w in st.session_state.wrong_answers:
                            st.markdown(f"**Q:** {w['question']}")
                            st.markdown(f"❌ Your answer: `{w['your_answer']}`")
                            st.markdown(f"✅ Correct: `{w['correct_answer']}`")
                            st.markdown("---")

                if st.session_state.get("last_batch_score", 1) < 0.6 and st.session_state.current_topic:
                    st.warning("I noticed this topic is still difficult. I will now explain it in shorter and simpler vocabulary.")
                    if st.button("Explain This Again (Simple)", use_container_width=True, type="primary"):
                        st.session_state.quiz_completed = False
                        weak_areas = ", ".join([w["question"] for w in st.session_state.wrong_answers[:4]])
                        remedial_prompt = (
                            f"This topic was difficult for me. Re-explain the SAME TOPIC ({st.session_state.current_topic}) "
                            f"using very simple words, short sentences, and exactly 3 easy examples. "
                            f"Focus more on these weak areas from my wrong answers: {weak_areas}. "
                            f"Do not switch topic and do not give only a basic definition."
                        )
                        run_learning_flow(remedial_prompt)
                        st.rerun()

            # Show suggestions exactly once, only after quiz stage.
            if st.session_state.get("post_quiz_suggestions"):
                st.markdown("### Recommended Topics")
                ordered = st.session_state.post_quiz_suggestions[:5]
                for idx, s in enumerate(ordered, start=1):
                    st.markdown(f"{idx}. {s}")
                cols = st.columns(len(ordered))
                for idx, s in enumerate(ordered):
                    with cols[idx]:
                        if st.button(f"Learn {idx+1}", key=f"post_quiz_sugg_{idx}", type="primary", use_container_width=True):
                            st.session_state.quiz_completed = False
                            run_learning_flow(f"__SUGGESTION__:{s}")
                            st.rerun()

            c1, c2 = st.columns([1, 1], gap="small")
            with c1:
                # User requested exactly "Dive Deeper into this Topic"
                if st.button("Dive Deeper into this Topic", use_container_width=True, type="primary"):
                    st.session_state.quiz_completed = False
                    user_input = f"Dive deeper into {st.session_state.current_topic}. Provide advanced details, novel examples, and deeper conceptual explanations. DO NOT repeat previous content."
                    run_learning_flow(user_input)
                    st.rerun()
            with c2:
                # User requested exactly "Start New Topic"
                if st.button("Start New Topic", type="primary", use_container_width=True):
                    st.session_state.quiz_completed = False
                    st.session_state.current_topic  = None
                    st.session_state.post_quiz_suggestions = []
                    st.session_state.post_quiz_topic = None
                    st.rerun()

        user_input = st.chat_input("Type a topic to explore, or ask a follow-up…")
        if user_input:
            run_learning_flow(user_input)
            st.rerun()

def run_learning_flow(user_input):
    st.session_state.update({
        "pending_quiz": None, "quiz_completed": False, "wrong_answers": [],
        "post_quiz_suggestions": [], "post_quiz_topic": None,
    })

    # ── STEP 1: Detect suggestion click (prefixed call) ──────────────
    is_suggestion_click = isinstance(user_input, str) and user_input.startswith("__SUGGESTION__:")
    if is_suggestion_click:
        user_input = user_input[len("__SUGGESTION__:"):].strip()
        st.session_state.current_topic = user_input

    # ── STEP 2: Detect numeric shortcut — user typed "1" to "5" ──────
    if not is_suggestion_click and re.fullmatch(r"[1-5]", (user_input or "").strip()):
        num = int(user_input.strip()) - 1
        suggestions = st.session_state.get("post_quiz_suggestions", [])
        if suggestions and num < len(suggestions):
            chosen = suggestions[num]
            user_input = chosen
            st.session_state.current_topic = chosen
            is_suggestion_click = True

    # ── STEP 3: Vague follow-up detection ────────────────────────────
    vague_patterns = [
        r"explain in detail", r"tell me more", r"go deeper",
        r"elaborate", r"i don.?t get it",
        r"go on", r"continue", r"again"
    ]
    is_vague = (not is_suggestion_click) and any(
        re.search(p, user_input, re.IGNORECASE) for p in vague_patterns
    )

    # ── STEP 4: Guard — nothing to work with ─────────────────────────
    resolved_topic = st.session_state.current_topic if is_vague else user_input
    if not resolved_topic:
        msg = "Hello! I'm your AI Adaptive Tutor. What topic would you like to explore today?"
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "text": msg})
        save_chat(st.session_state.learner_id, st.session_state.current_session_id, user_input, msg)
        return

    # ── STEP 5: NLP topic extraction (only when NOT a suggestion/vague) ─
    nlp = process_user_input(user_input)
    prompt_topic = nlp.get("topic")

    if is_suggestion_click:
        pass  # topic already set correctly — never overwrite with NLP output
    elif not is_vague:
        st.session_state.current_topic = prompt_topic if prompt_topic else user_input
    elif not st.session_state.current_topic:
        st.session_state.current_topic = prompt_topic or user_input

    # ── STEP 6: Final resolved topic ─────────────────────────────────
    topic = st.session_state.current_topic or "not yet set"
    
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Build Chat History Text
    chat_history_lines = []
    for m in st.session_state.chat_history[:-1]:
        role_label = "User" if m["role"] == "user" else "AI"
        content_text = m.get("content", m.get("text", ""))
        chat_history_lines.append(f"{role_label}: {content_text}")
    chat_history_text = "\n".join(chat_history_lines) if chat_history_lines else "No history yet"

    # Fetch Adaptive Accuracy Score
    accuracy_score = int(round(st.session_state.get("session_accuracy", 0.0) * 100))
    
    # Generate System Prompt via JS Logic Request
    system_prompt_text = get_system_prompt(accuracy_score, topic, chat_history_text)
    api_msgs = [{"role": "system", "content": system_prompt_text}]
    
    reference_context = fetch_reference_context(topic)
    final_user_msg = user_input
    if reference_context:
        final_user_msg += f"\n\n[Reference Data: {reference_context}]"
        
    api_msgs.append({"role": "user", "content": final_user_msg})

    with st.spinner(f"Generating lesson on **{topic}**…"):
        raw = generate_llm_content(api_msgs)
        if raw.strip() == "INVALID_TOPIC":
            st.session_state.chat_history.append({"role":"assistant","text":"⚠️ Couldn't identify a valid topic. Please try again."})
            save_chat(st.session_state.learner_id, st.session_state.current_session_id, user_input, "INVALID_TOPIC")
            return
        elif raw.startswith("ERROR:"):
            st.session_state.chat_history.append({"role":"assistant","text":f"⚠️ {raw} Check your `.env` file."})
            return
    parsed = parse_llm_response(raw)

    full_text = parsed["explanation"]
    
    # state must be a string for the RL Q-table (dict keys must be hashable)
    cs = get_topic_learning_level(st.session_state.learner_id, topic)  # returns "beginner" / "intermediate" / "advanced"
    strat = choose_action(cs)  # derive real strategy from current level
    generated_quiz = generate_quiz_from_content(topic, full_text, cs)

    import time
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        simulated_text = ""
        chunk_size = 5
        # Simulate ChatGPT streaming with the | cursor
        for i in range(0, len(full_text), chunk_size):
            simulated_text += full_text[i:i+chunk_size]
            message_placeholder.markdown(simulated_text + "|")
            time.sleep(0.005)
        message_placeholder.markdown(simulated_text)

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

if st.session_state.logged_in:
    show_dashboard()
elif st.session_state.show_signup:
    show_signup_page()
else:
    show_login_page()