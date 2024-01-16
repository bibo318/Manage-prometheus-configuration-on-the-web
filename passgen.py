from werkzeug.security import generate_password_hash
import os

USERS_FILE = '/root/Web-quantri/users.txt'

# Hàm này tạo ra một mật khẩu hash và lưu vào file
def create_user(username, password):
    password_hash = generate_password_hash(password)
    with open(USERS_FILE, 'a') as file:
        file.write(f"{username}:{password_hash}\n")

# Yêu cầu nhập thông tin người dùng
username = input("Enter username: ")
password = input("Enter password: ")

# Tạo người dùng
create_user(username, password)
print(f"User {username} has been created.")

