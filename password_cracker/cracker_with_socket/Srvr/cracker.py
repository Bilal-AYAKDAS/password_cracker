from server import MyServer
import multiprocessing
import random
import string
import hashlib
import os
import requests
import threading

BASE_URL ="http://127.0.0.1:5000"

def get_password_from_api():
    response = requests.get(f"{BASE_URL}/get_password")
    md5_hash = response.json()['password']
    return md5_hash

def check_password_with_api(password):
    response = requests.post(f"{BASE_URL}/check_password", json={"password": password})
    return response.json()['message']

def generate_password(api_passwd, pipe):
    """
    Rastgele şifreler oluşturarak verilen hash'e eşleşen şifreyi bulmaya çalışır.
    """
    count = 0
    while True:
        password = "".join(
            random.choices( string.digits, k=random.randint(6, 7))
        )
        hashed_passwd = hashlib.md5(password.encode()).hexdigest()
        if count % 1000 == 0:
            print(f"Trying password: {count}")
        count += 1
        if api_passwd == hashed_passwd:
            pipe.send(password)
            pipe.close()
            return

def cracker(api_passwd: str, number_of_processes: int = 1) -> str:
    """
    Belirtilen hash'e karşılık gelen şifreyi brute-force yöntemiyle bulur.

    Args:
        api_passwd (str): Hedef hash (MD5 formatında).
        number_of_processes (int): Kullanılacak süreç sayısı.

    Returns:
        str: Hash'e karşılık gelen şifre.
    """
    processes = []
    pipes = []

    # Çoklu işlemi başlatıyoruz
    for _ in range(number_of_processes):
        parent_conn, child_conn = multiprocessing.Pipe(False)
        p = multiprocessing.Process(target=generate_password, args=(api_passwd, child_conn))
        processes.append(p)
        pipes.append(parent_conn)
        p.start()

    # Doğru şifreyi bulan ilk süreci bekleyip sonucu döndürüyoruz
    result_passwd = None
    while result_passwd is None:
        for pipe in pipes:
            if pipe.poll():
                result_passwd = pipe.recv()
                break

    # Tüm süreçleri sonlandırıyoruz
    for p in processes:
        p.terminate()

    return result_passwd

if __name__ == "__main__":
    target_hash = get_password_from_api()
    print(f"Target hash: {target_hash}")
    server = MyServer()
    server.listen()
    while True:
        threading.Thread(target=server.accept_client).start()
        if len(server.clients) > 0:
            break
    server.broadcast_message(target_hash)
    print(f"CPU Count: {os.cpu_count()}")
    multiprocessing.set_start_method("spawn")

    # Kullanılacak süreç sayısını belirtelim
    found_password = cracker(target_hash, number_of_processes=os.cpu_count())

    print(f"Password found: {found_password}")
    print(f"Check result: {check_password_with_api(found_password)}")

