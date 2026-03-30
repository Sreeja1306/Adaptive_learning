import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "learning.db")

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")

def get_connection():
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def migrate_db(conn):
    """
    Checks if session_id exists in chat_history, and adds it if it doesn't.
    (SQLite schema migrations mechanism)
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(chat_history)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "session_id" not in columns:
        print("Migrating DB: Adding session_id to chat_history table.")
        cursor.execute("ALTER TABLE chat_history ADD COLUMN session_id TEXT DEFAULT 'legacy_session'")
        conn.commit()

def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learners (
        learner_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # LEARNER STATE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learner_state (
        learner_id INTEGER PRIMARY KEY,
        understanding_level TEXT DEFAULT 'beginner',
        recent_accuracy REAL DEFAULT 0.0,
        attempts INTEGER DEFAULT 0,
        confidence REAL DEFAULT 0.5,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (learner_id) REFERENCES learners(learner_id)
            ON DELETE CASCADE
    );
    """)

    # LEARNING CONTENT
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learning_content (
        content_id INTEGER PRIMARY KEY AUTOINCREMENT,
        learner_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        strategy_used TEXT NOT NULL,
        content_text TEXT NOT NULL,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (learner_id) REFERENCES learners(learner_id)
            ON DELETE CASCADE
    );
    """)

    # INTERACTIONS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        learner_id INTEGER NOT NULL,
        content_id INTEGER,
        quiz_score INTEGER,
        total_questions INTEGER,
        accuracy REAL,
        hints_used INTEGER DEFAULT 0,
        time_spent INTEGER,
        feedback TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (learner_id) REFERENCES learners(learner_id)
            ON DELETE CASCADE,
        FOREIGN KEY (content_id) REFERENCES learning_content(content_id)
            ON DELETE SET NULL
    );
    """)

    # CHAT HISTORY
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        learner_id INTEGER NOT NULL,
        session_id TEXT NOT NULL,
        user_query TEXT,
        ai_response TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (learner_id) REFERENCES learners(learner_id)
            ON DELETE CASCADE
    );
    """)

    # QUIZ ATTEMPTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
        learner_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        is_correct BOOLEAN NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (learner_id) REFERENCES learners(learner_id)
            ON DELETE CASCADE
    );
    """)

    conn.commit()
    migrate_db(conn)
    conn.close()
    
def register_user(full_name, username, password):
    full_name = (full_name or "").strip()
    username = (username or "").strip()
    password = password or ""

    if not full_name:
        return False, "Full name is required."
    if not username:
        return False, "Username or email is required."
    if not PASSWORD_REGEX.match(password):
        return False, "Password must be at least 8 characters and include uppercase, lowercase, digit, and special character."

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO learners (full_name, username, password) VALUES (?, ?, ?)", 
                       (full_name, username, password))
        learner_id = cursor.lastrowid
        cursor.execute("INSERT INTO learner_state (learner_id) VALUES (?)", (learner_id,))
        conn.commit()
        return True, "Registration successful"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def login_user(username, password):
    username = (username or "").strip()
    password = password or ""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT learner_id FROM learners WHERE lower(username)=lower(?) AND password=?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        return True, user[0]
    return False, None

def get_chat_history(learner_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT session_id, user_query, created_at 
        FROM chat_history 
        WHERE learner_id=? 
        ORDER BY created_at ASC
    """, (learner_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_session_history(learner_id, session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_query, ai_response 
        FROM chat_history 
        WHERE learner_id=? AND session_id=? 
        ORDER BY created_at ASC
    """, (learner_id, session_id))
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_chat(learner_id, session_id, user_query, ai_response):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (learner_id, session_id, user_query, ai_response) VALUES (?, ?, ?, ?)", 
                   (learner_id, session_id, user_query, ai_response))
    conn.commit()
    conn.close()

def delete_chat_session(learner_id, session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE learner_id=? AND session_id=?", (learner_id, session_id))
    conn.commit()
    conn.close()

def save_batch_quiz_attempts(learner_id, topic, results_list):
    conn = get_connection()
    cursor = conn.cursor()
    for is_correct in results_list:
        cursor.execute("INSERT INTO quiz_attempts (learner_id, topic, is_correct) VALUES (?, ?, ?)",
                       (learner_id, topic, is_correct))
    
    # Fetch total questions historically natively handled for attempts counting
    cursor.execute("SELECT COUNT(*) FROM quiz_attempts WHERE learner_id=?", (learner_id,))
    total_questions = cursor.fetchone()[0] or 0
    
    # Last 5 results for confidence calculation
    cursor.execute("SELECT is_correct FROM quiz_attempts WHERE learner_id=? ORDER BY created_at DESC LIMIT 5", (learner_id,))
    last_5_results = [r[0] for r in cursor.fetchall()]

    confidence = 0.5
    if len(last_5_results) > 0:
        confidence = sum(last_5_results) / len(last_5_results)

    # Fetch old accuracy and level to perform weighted moving average
    cursor.execute("SELECT understanding_level, recent_accuracy FROM learner_state WHERE learner_id=?", (learner_id,))
    row = cursor.fetchone()
    current_level = row[0] if row else "beginner"
    old_accuracy = row[1] if row else 0.0
    
    batch_total = len(results_list)
    batch_correct = sum(1 for r in results_list if r)
    batch_percentage = (batch_correct / batch_total) if batch_total > 0 else 0.0
    
    # Evaluate new weighted moving average: 0.4 old + 0.6 new
    if total_questions <= batch_total:
        new_accuracy = batch_percentage
    else:
        new_accuracy = round(old_accuracy * 0.4 + batch_percentage * 0.6, 3)

    # Decide level natively (intermediate / advanced thresholds) based on this new fractional score
    if new_accuracy > 0.70:
        new_level = "intermediate" if current_level == "beginner" else "advanced"
    elif new_accuracy >= 0.40:
        new_level = "intermediate"
    else:
        new_level = "intermediate" if current_level == "advanced" else "beginner"

    # Save to database
    cursor.execute("SELECT 1 FROM learner_state WHERE learner_id=?", (learner_id,))
    if cursor.fetchone():
        cursor.execute("""
            UPDATE learner_state 
            SET understanding_level=?, recent_accuracy=?, attempts=?, confidence=?, last_updated=CURRENT_TIMESTAMP
            WHERE learner_id=?
        """, (new_level, new_accuracy, total_questions, confidence, learner_id))
    else:
        cursor.execute("""
            INSERT INTO learner_state (learner_id, understanding_level, recent_accuracy, attempts, confidence, last_updated)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (learner_id, new_level, new_accuracy, total_questions, confidence))
    
    conn.commit()
    conn.close()
    return new_level

def get_learner_profile_stats(learner_id, topic=None):
    conn = get_connection()
    cursor = conn.cursor()

    if topic:
        cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) FROM quiz_attempts WHERE learner_id=? AND lower(topic)=lower(?)", (learner_id, topic))
        attempts, correct = cursor.fetchone()
        attempts = attempts or 0
        correct = correct or 0

        cursor.execute("SELECT is_correct FROM quiz_attempts WHERE learner_id=? AND lower(topic)=lower(?) ORDER BY created_at DESC LIMIT 5", (learner_id, topic))
        last_5_results = [row[0] for row in cursor.fetchall()][::-1]

        accuracy = (correct / attempts * 100) if attempts > 0 else 0.0

        confidence = "Low"
        if len(last_5_results) > 0:
            conf_val = sum(last_5_results) / len(last_5_results)
            if conf_val >= 0.8:
                confidence = "High"
            elif conf_val >= 0.4:
                confidence = "Medium"

        level = "Beginner"
        if attempts > 0:
            score = correct / attempts
            if score >= 0.75:
                level = "Advanced"
            elif score >= 0.45:
                level = "Intermediate"

        cursor.execute("SELECT COUNT(DISTINCT topic) FROM quiz_attempts WHERE learner_id=?", (learner_id,))
        topics_count = cursor.fetchone()[0] or 0

        conn.close()
        return {
            "accuracy": accuracy,
            "topics_explored": topics_count,
            "last_5_trend": last_5_results,
            "confidence": confidence,
            "level": level
        }

    # Global stats
    cursor.execute("SELECT COUNT(DISTINCT topic) FROM quiz_attempts WHERE learner_id=?", (learner_id,))
    topics_count = cursor.fetchone()[0] or 0

    # Trend: last 5 attempts (1 for correct, 0 for incorrect)
    cursor.execute("SELECT is_correct FROM quiz_attempts WHERE learner_id=? ORDER BY created_at DESC LIMIT 5", (learner_id,))
    last_5_results = [row[0] for row in cursor.fetchall()][::-1] # reverse to get chronological 
    
    # Read derived profile stats from learner_state
    cursor.execute("SELECT understanding_level, recent_accuracy, confidence FROM learner_state WHERE learner_id=?", (learner_id,))
    row = cursor.fetchone()
    
    level = "Beginner"
    accuracy = 0.0
    confidence = "Low"
    
    if row:
        level = row[0].title()
        accuracy = row[1] * 100
        conf_val = row[2]
        if conf_val >= 0.8:
            confidence = "High"
        elif conf_val >= 0.4:
            confidence = "Medium"

    conn.close()
    
    return {
        "accuracy": accuracy,
        "topics_explored": topics_count,
        "last_5_trend": last_5_results,
        "confidence": confidence,
        "level": level
    }

def get_topic_learning_level(learner_id, topic):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*), SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END)
        FROM quiz_attempts
        WHERE learner_id=? AND lower(topic)=lower(?)
        """,
        (learner_id, topic),
    )
    attempts, correct = cursor.fetchone()
    attempts = attempts or 0
    correct = correct or 0
    conn.close()

    if attempts == 0:
        return "beginner"

    score = correct / attempts
    if score >= 0.75:
        return "advanced"
    if score >= 0.45:
        return "intermediate"
    return "beginner"

def reset_learner_state(learner_id):
    """Resets learner_state to defaults for a new session (beginner, 0% accuracy)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE learner_state
        SET understanding_level = 'beginner',
            recent_accuracy = 0.0,
            attempts = 0,
            confidence = 0.5,
            last_updated = CURRENT_TIMESTAMP
        WHERE learner_id = ?
    """, (learner_id,))
    conn.commit()
    conn.close()

def reset_session_stats(learner_id):
    """
    Clears all quiz_attempts for this learner so that Confidence,
    Topics Explored, and Score Trend all reset to zero on a new session.
    Also resets learner_state to defaults.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Clear all quiz history for this learner
    cursor.execute("DELETE FROM quiz_attempts WHERE learner_id = ?", (learner_id,))
    # Reset derived state
    cursor.execute("""
        UPDATE learner_state
        SET understanding_level = 'beginner',
            recent_accuracy = 0.0,
            attempts = 0,
            confidence = 0.5,
            last_updated = CURRENT_TIMESTAMP
        WHERE learner_id = ?
    """, (learner_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")
