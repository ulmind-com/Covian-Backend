from app.models.user import User

print("User model imported")
try:
    print(User.email)
except Exception as e:
    print("Failed to access User.email", type(e), e)
