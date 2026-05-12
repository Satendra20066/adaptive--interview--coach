"""
Question Bank Module
Stores HR, Technical, and Mixed questions with difficulty levels (Easy, Medium, Hard)
"""

QUESTIONS = {
    "HR": {
        "Easy": [
            "Tell me something about yourself.",
            "What are your hobbies and interests?",
            "Why did you choose this field?",
            "Where are you from?",
            "What are your strengths?",
        ],
        "Medium": [
            "Where do you see yourself in 5 years?",
            "Why should we hire you?",
            "Tell me about a challenge you faced and how you overcame it.",
            "How do you handle pressure and stressful situations?",
            "What motivates you the most?",
        ],
        "Hard": [
            "Describe a situation where you had a conflict with a teammate. How did you resolve it?",
            "Tell me about a time you failed. What did you learn?",
            "If two urgent deadlines clash, how would you prioritize?",
            "How do you handle constructive criticism?",
            "Describe a time when you showed leadership without a formal title.",
        ],
    },
    "Technical": {
        "Easy": [
            "What is Python? Why is it popular?",
            "What is the difference between a list and a tuple in Python?",
            "What is machine learning in simple terms?",
            "What is an API?",
            "What is the difference between supervised and unsupervised learning?",
        ],
        "Medium": [
            "Explain how a decision tree algorithm works.",
            "What is overfitting and how do you prevent it?",
            "What is the difference between SQL and NoSQL databases?",
            "Explain the concept of feature engineering.",
            "What is cross-validation and why is it important?",
        ],
        "Hard": [
            "Explain the math behind backpropagation in neural networks.",
            "How would you handle a highly imbalanced dataset?",
            "Compare LSTM and Transformer architectures. When would you use each?",
            "Explain the bias-variance tradeoff with an example.",
            "How would you deploy a machine learning model to production?",
        ],
    },
    "Mixed": {
        "Easy": [
            "What project are you most proud of and why?",
            "How did you learn programming?",
            "What tools do you use for data analysis?",
            "Describe your final year project briefly.",
            "What is one technical skill you want to improve?",
        ],
        "Medium": [
            "Walk me through a project where you solved a real problem using AI/ML.",
            "How do you keep yourself updated with new technologies?",
            "Describe a situation where your technical decision had a business impact.",
            "How do you approach debugging a complex issue?",
            "Tell me about a time you had to learn something new quickly for a project.",
        ],
        "Hard": [
            "If given a dataset with 80% missing values, what would your approach be?",
            "How would you design a recommendation system from scratch?",
            "Explain a time when your model performed well in testing but failed in production.",
            "How would you explain a complex ML model to a non-technical stakeholder?",
            "Design an AI system to detect fake news. What approach would you take?",
        ],
    },
}


def get_question(category: str, difficulty: str, used_indices: list) -> dict:
    pool = QUESTIONS[category][difficulty]
    available = [i for i in range(len(pool)) if (category, difficulty, i) not in used_indices]
    if not available:
        available = list(range(len(pool)))
    import random
    idx = random.choice(available)
    return {
        "text": pool[idx],
        "category": category,
        "difficulty": difficulty,
        "index": (category, difficulty, idx),
    }


def get_next_difficulty(current_difficulty: str, stress_score: float, answer_quality: float) -> str:
    levels = ["Easy", "Medium", "Hard"]
    idx = levels.index(current_difficulty)
    if stress_score > 65 and answer_quality < 50:
        return levels[max(0, idx - 1)]
    elif stress_score < 35 and answer_quality > 70:
        return levels[min(2, idx + 1)]
    else:
        return current_difficulty
