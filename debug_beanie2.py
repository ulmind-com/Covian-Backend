from beanie import Document, Indexed
from pydantic import EmailStr

class TestUser1(Document):
    email: Indexed(EmailStr, unique=True)

class TestUser2(Document):
    email: EmailStr

try:
    print("TestUser1.email:", TestUser1.email)
except Exception as e:
    print("TestUser1 failed:", type(e), e)

try:
    print("TestUser2.email:", TestUser2.email)
except Exception as e:
    print("TestUser2 failed:", type(e), e)

