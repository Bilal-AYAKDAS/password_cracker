import requests
import string
import random
import hashlib
import threading

BASE_URL ="http://127.0.0.1:5000"


md5_hash = None
lock = threading.Lock()

def get_password_from_api():
    global md5_hash
    response = requests.get(f"{BASE_URL}/get_password")
    md5_hash = response.json()['password']
    print(md5_hash)

def check_password_request(password):
    response = requests.post(f"{BASE_URL}/check_password", json={"password": password})
    return response.json()['message']

def generate_password():
    password = "".join(
        random.choices(string.ascii_letters + string.digits, k=random.randint(8, 16))
    )
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    return  password,hashed_password

def crack_password():

    global md5_hash

    while True:
        password, hashed_password = generate_password()
        if hashed_password == md5_hash:
            with lock:
                print(f"Password found: {password}")
            break

if __name__ == '__main__':
    get_password_from_api()

    thread_count = 5
    threads = []

    for _ in range(thread_count):
        t = threading.Thread(target=crack_password)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("Tüm threadler tamamlandı.")
