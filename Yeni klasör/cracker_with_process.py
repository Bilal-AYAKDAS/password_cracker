import requests
import string
import random
import hashlib
from multiprocessing import Process, Event, Lock, Pipe

BASE_URL = "http://127.0.0.1:5000"

md5_hash = None
lock = Lock()
password_found = Event()  # Şifre bulunduğunu işaret eden bayrak

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
        random.choices(string.ascii_letters + string.digits, k=random.randint(2, 4))
    )
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    return password, hashed_password

def crack_password(pipe):
    global md5_hash

    while not password_found.is_set():  # Şifre bulunduysa diğer process'ler durur
        password, hashed_password = generate_password()
        if hashed_password == md5_hash:
            with lock:  # Bir process şifreyi bulduğunda sonucu yazdırır
                if not password_found.is_set():
                    pipe.send(password)  # Şifreyi pipe'a yaz
                    password_found.set()  # Şifre bulundu, bayrağı ayarla
            break

if __name__ == '__main__':
    get_password_from_api()

    process_count = 6
    processes = []
    parent_pipes = []

    for _ in range(process_count):
        parent_conn, child_conn = Pipe()
        parent_pipes.append(parent_conn)
        p = Process(target=crack_password, args=(child_conn,))
        processes.append(p)
        p.start()

    found_password = None

    # Main process pipe'lardan şifreyi okur
    for parent_conn in parent_pipes:
        if parent_conn.poll():  # Eğer pipe'da veri varsa
            found_password = parent_conn.recv()
            break

    # Tüm process'leri sonlandır
    password_found.set()
    for p in processes:
        p.join()

    if found_password:
        print(f"Password found: {found_password}")
    else:
        print("No password found.")

    print("Tüm işlemler tamamlandı.")
