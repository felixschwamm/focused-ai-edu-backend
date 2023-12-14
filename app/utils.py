import jwt

def generate_mock_jwt(user_id: str):
    return jwt.encode({
        "sub": user_id,
    }, "secret", algorithm="HS256")