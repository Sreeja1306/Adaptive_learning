import json
import os
import random

QTABLE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "qtable.json")

ACTIONS = ["easy_content", "medium_content", "hard_content"]
ALPHA = 0.1
GAMMA = 0.9
EPSILON = 0.2

def load_qtable():
    if os.path.exists(QTABLE_PATH):
        with open(QTABLE_PATH, "r") as f:
            return json.load(f)
    return {}

def save_qtable(qtable):
    os.makedirs(os.path.dirname(QTABLE_PATH), exist_ok=True)
    with open(QTABLE_PATH, "w") as f:
        json.dump(qtable, f, indent=4)

def get_q(state, action):
    qtable = load_qtable()
    if state not in qtable:
        qtable[state] = {a: 0.0 for a in ACTIONS}
    return qtable[state].get(action, 0.0)

def choose_action(state):
    qtable = load_qtable()
    
    # Initialize state if not present
    if state not in qtable:
        qtable[state] = {a: 0.0 for a in ACTIONS}
        save_qtable(qtable)
        
    # Epsilon-greedy
    if random.random() < EPSILON:
        return random.choice(ACTIONS)
        
    # Exploit best action
    q_values = qtable[state]
    return max(q_values, key=q_values.get)

def update_q(state, action, reward):
    qtable = load_qtable()
    
    if state not in qtable:
        qtable[state] = {a: 0.0 for a in ACTIONS}
        
    current_q = qtable[state].get(action, 0.0)
    new_q = current_q + ALPHA * (reward - current_q)
    
    qtable[state][action] = new_q
    save_qtable(qtable)
