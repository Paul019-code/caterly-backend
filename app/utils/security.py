# app/utils/security.py
import re


def validate_password_strength(password):
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"

    return True, ""


def sanitize_user_data(user_data):
    """
    Remove sensitive fields from user data before sending to client
    """
    sensitive_fields = ['password_hash', 'verification_token', 'failed_login_attempts']
    return {k: v for k, v in user_data.items() if k not in sensitive_fields}