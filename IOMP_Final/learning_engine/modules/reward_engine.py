def calculate_reward(feedback_type, current_state, strategy_used):
    """
    Calculates the reward based on user feedback to update RL Q-table.
    
    feedback_type: 'positive', 'neutral', 'negative'
    """
    
    if feedback_type == "positive":
        return 1.0  # High reward for fully understanding
    elif feedback_type == "neutral":
        return 0.5  # Partial understanding
    elif feedback_type == "negative":
        return -1.0 # Penalty for not understanding
    
    return 0.0
