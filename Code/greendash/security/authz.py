def encrypt_feedback(data: str) -> str:
    return f"encrypted_{data}"

def issue_token(role: str, customer_id: str | None = None) -> str:
    return f"token_{customer_id}"
