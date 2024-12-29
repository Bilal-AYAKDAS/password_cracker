import requests
import string
import hashlib
import threading

BASE_URL ="http://127.0.0.1:5000"

md5_hash = None
lock = threading.Lock()
CHARS = string.ascii_letters + string.digits
CHARSET_SIZE = len(CHARS)


def get_password_from_api():
    global md5_hash
    response = requests.get(f"{BASE_URL}/get_password")
    md5_hash = response.json()['password']
    print(md5_hash)


def check_password_request(password):
    response = requests.post(f"{BASE_URL}/check_password", json={"password": password})
    return response.json()['message']


def generate_combination(start, end, max_length):
    for i in range(start, end):
        password = []
        temp = i
        for _ in range(max_length):
            password.append(CHARS[temp % CHARSET_SIZE])
            temp //= CHARSET_SIZE
        yield ''.join(password)


def crack_password(start, end, max_length):
    global md5_hash

    for password in generate_combination(start, end, max_length):
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        if hashed_password == md5_hash:
            with lock:
                print(f"Password found: {password}")
                response = requests.post(f"{BASE_URL}/check_password", json={"password": password})
                print(response.json())
            break


if __name__ == '__main__':
    get_password_from_api()

    thread_count = 6
    max_length = 4  # Şifre uzunluğu
    total_combinations = CHARSET_SIZE ** max_length
    chunk_size = total_combinations // thread_count

    threads = []

    for i in range(thread_count):
        start = i * chunk_size
        end = start + chunk_size if i < thread_count - 1 else total_combinations
        t = threading.Thread(target=crack_password, args=(start, end, max_length))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("Tüm threadler tamamlandı.")
