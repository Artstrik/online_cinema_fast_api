"""
Password validation utilities.

Provides password complexity validation according to security requirements.
"""
import re


def validate_password_complexity(password: str) -> str:
    """
    Validate password complexity.

    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character

    Args:
        password: The password to validate

    Returns:
        The validated password

    Raises:
        ValueError: If password doesn't meet complexity requirements
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")

    # Special characters
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`';]", password):
        raise ValueError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>_-+=[]\\\/~`';)")

    return password


def check_password_strength(password: str) -> dict:
    """
    Check password strength and return detailed feedback.

    Args:
        password: The password to check

    Returns:
        Dictionary with strength info:
        {
            'is_strong': bool,
            'score': int (0-5),
            'feedback': list of strings
        }
    """
    score = 0
    feedback = []

    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Password should be at least 8 characters")

    if len(password) >= 12:
        score += 1

    # Character variety checks
    if re.search(r"[A-Z]", password):
        score += 1
    else:
        feedback.append("Add uppercase letters")

    if re.search(r"[a-z]", password):
        score += 1
    else:
        feedback.append("Add lowercase letters")

    if re.search(r"\d", password):
        score += 1
    else:
        feedback.append("Add numbers")

    if re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`';]", password):
        score += 1
    else:
        feedback.append("Add special characters")

    # Check for common patterns
    common_patterns = [
        r"12345", r"password", r"qwerty", r"abc123",
        r"111111", r"123123", r"admin"
    ]

    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            score -= 1
            feedback.append(f"Avoid common patterns like '{pattern}'")
            break

    is_strong = score >= 5 and len(feedback) == 0

    return {
        'is_strong': is_strong,
        'score': max(0, score),
        'feedback': feedback if feedback else ["Password is strong"]
    }
