def build_prompt(nlp_result, strategy, learner_level="beginner"):
    """
    Constructs a prompt for the LLM based on RL strategy and learner level.
    """
    topic = nlp_result.get("topic", "general concepts")
    input_type = nlp_result.get("type", "QUERY")
    
    level_instruction = ""
    if learner_level == "beginner":
        level_instruction = "Beginner: Use simple language and analogies. Zero jargon."
    elif learner_level == "intermediate":
        level_instruction = "Intermediate: Moderate depth building on basics."
    elif learner_level == "advanced":
        level_instruction = "Advanced: Full technical depth with algorithms, tradeoffs, and citations."
        
    strategy_instruction = {
        "easy_content": "Keep explanations short, simple, and beginner friendly with tiny vocabulary.",
        "medium_content": "Use balanced depth with examples and concise definitions.",
        "hard_content": "Use deeper technical detail with edge cases and trade-offs."
    }.get(strategy, "Use balanced depth based on learner profile.")

    assignment_instruction = ""
    if input_type == "ASSIGNMENT":
        assignment_instruction = "The user has given you a specific assignment/task. SKIP the general textbook explanation and perform the requested task directly and conversationally."

    adaptive_instructions = f"- Learner Level: {level_instruction}\n- Strategy: {strategy_instruction}"
    if assignment_instruction:
        adaptive_instructions += f"\n- Assignment: {assignment_instruction}"
    adaptive_instructions += "\n- If the topic is gibberish or inappropriate, return exactly 'INVALID_TOPIC'."

    prompt = f"""You are an expert educational content writer and researcher. Your task is to generate comprehensive, detailed, textbook-quality educational content on a given topic.

CONTENT REQUIREMENTS:
- Write in the style of Wikipedia or a university textbook \u2014 thorough, well-structured, academically rich
- Each section should be AT LEAST 3-5 paragraphs with deep explanations
- Include: definitions, history/background, how it works (step-by-step), real-world examples, advantages, disadvantages, use cases, and related concepts
- Use clear headings and subheadings
- Explain technical terms when first introduced
- Include analogies to make complex ideas accessible
- MINIMUM 2500 words. Target 3000–4000 words. Write a full textbook chapter, not a summary. Do not truncate. Every section must be fully developed with multiple paragraphs.

ADAPTIVE INSTRUCTIONS:
{adaptive_instructions}

SUGGESTIONS REQUIREMENTS:
- At the END of your response, after all content, output EXACTLY ONE suggestions block
- Format it like this \u2014 no labels, no prefixes, just clean questions:

SUGGESTIONS:
1. [First follow-up question]
2. [Second follow-up question]
3. [Third follow-up question]
4. [Fourth follow-up question]
5. [Fifth follow-up question]
END_SUGGESTIONS

CRITICAL RULES:
- Do NOT show suggestions anywhere except at the very end
- Do NOT add [question one], [question two] or any label prefixes to suggestions
- Do NOT repeat the suggestions list \u2014 output it ONLY ONCE
- Do NOT add any text after END_SUGGESTIONS

Topic to cover: {topic}"""
    return prompt

def build_followup_prompt(user_input, current_topic, learner_level, nlp_result=None):
    intention = nlp_result.get("intention") if nlp_result else "learn"
    input_type = nlp_result.get("type", "QUERY") if nlp_result else "QUERY"
    
    level_instruction = ""
    if learner_level == "beginner":
        level_instruction = "Beginner: Use simple language and analogies. Zero jargon."
    elif learner_level == "intermediate":
        level_instruction = "Intermediate: Moderate depth building on basics."
    elif learner_level == "advanced":
        level_instruction = "Advanced: Full technical depth with algorithms, tradeoffs, and citations."
    
    assignment_instruction = ""
    if input_type == "ASSIGNMENT":
        assignment_instruction = "The user has given you a specific assignment/task. SKIP the general context bridge and perform the requested task directly and conversationally."

    adaptive_instructions = f"- Study Context: {current_topic}\n- User Message: {user_input}\n- Learner Level: {level_instruction}"
    if assignment_instruction:
        adaptive_instructions += f"\n- Assignment: {assignment_instruction}"

    prompt = f"""You are an expert tutor responding to a learner follow-up.

ADAPTIVE INSTRUCTIONS:
{adaptive_instructions}

CONTENT REQUIREMENTS:
- Respond directly to the latest user message first.
- Stay grounded in the current study topic unless the user clearly requests a new topic.
- Keep explanations concise, accurate, and non-repetitive.
- Use clean markdown headings only. No decorative separators or placeholder text.
- If asked for steps, code, comparison, summary, or assignment output, provide exactly that format.
- If input is unclear, gibberish, or inappropriate, return exactly: INVALID_TOPIC

SUGGESTIONS REQUIREMENTS:
- At the end, output exactly one suggestions block:
SUGGESTIONS:
1. [First follow-up question]
2. [Second follow-up question]
3. [Third follow-up question]
4. [Fourth follow-up question]
5. [Fifth follow-up question]
END_SUGGESTIONS
- Do not output anything after END_SUGGESTIONS."""
    return prompt
