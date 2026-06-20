from app.core.security import verify_password, get_password_hash
hash_pwd = get_password_hash("adminpassword123")
print("Hash:", hash_pwd)
is_valid = verify_password("adminpassword123", hash_pwd)
print("Is valid:", is_valid)
