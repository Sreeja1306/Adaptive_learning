import re

def process_user_input(text):
    """
    NLP Processor: 
    Extracts keywords as 'topic' and determines the user's intent.
    Differentiates between knowledge queries and task assignments.
    """
    text = str(text).lower().strip()
    
    # Define Intent Categories
    intent_keywords = {
        "quiz": ["quiz", "test", "question", "assess", "exam", "trivia", "mcq", "quizzes", "quizees", "quizes"],
        "explain": ["explain", "what", "how", "why", "define", "detail", "more", "example", "summary", "key terms", "deep dive"],
        "story": ["story", "tale", "storytelling", "legend", "narrative", "scenario"]
    }
    
    # Intent Detection
    intention = "learn"
    for intent, keys in intent_keywords.items():
        if any(word in text for word in keys):
            intention = intent
            break

    # Type Classification: Query vs Assignment
    assignment_words = ["generate", "give", "create", "show", "make", "take", "bring", "list", "do", "perform", "tell"]
    input_type = "QUERY"
    if any(text.startswith(word) for word in assignment_words) or \
       (intention in ["quiz", "story"] and any(word in text for word in ["me", "now", "on", "about", "provide", "a"])):
        input_type = "ASSIGNMENT"
        
    # Contextual awareness: if they say "above", "this", "it", it's likely a follow-up
    is_contextual = any(word in text for word in ["above", "this", "that", "it", "previous", "earlier", "on this", "about that"])
    
    # Stop words for Topic Extraction (includes intent keywords to prevent overlap)
    all_intent_keys = [k for v in intent_keywords.values() for k in v]
    stop_words = ["what", "is", "a", "an", "the", "how", "to", "why", "can", "you", 
                  "about", "me", "tell", "give", "some", "details", "i", "need",
                  "on", "in", "above", "topic", "for", "please", "now", "want", "show",
                  "generate", "create", "make", "me", "a", "an", "the", "provide"] + all_intent_keys
    
    words = re.findall(r'\b\w+\b', text)
    # A word is only a topic keyword if it's NOT a stop word AND NOT an intent word
    keywords = [w for w in words if w not in stop_words]
    
    topic = " ".join(keywords) if keywords else ""
    
    return {
        "topic": topic,
        "intention": intention,
        "type": input_type,
        "is_contextual": is_contextual,
        "original_text": text
    }
