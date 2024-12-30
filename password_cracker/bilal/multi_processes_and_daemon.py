import multiprocessing
import random
import string
import hashlib
import os
import requests
import asyncio
import time
import aiohttp

BASE_URL = "http://127.0.0.1:5000"

PASSWORD_MIN_LENGTH = 1
PASSWORD_MAX_LENGTH = 6
TIMEOUT = 5
MAX_RETRIES = 3


def get_password_from_api():
    """  API'den hash'i alır. """
    response = requests.get(f"{BASE_URL}/get_password")
    md5_hash = response.json()['password']
    return md5_hash

async def check_password(password: str) -> str:
    """
    Asynchronous istek atar  to check password apisine.
    """
    async with aiohttp.ClientSession() as session:
        # Belirli sayıda tekrar deneyelim
        for attempt in range(MAX_RETRIES):
            try:
                async with session.post(f"{BASE_URL}/check_password", json={"password": password}, timeout=TIMEOUT) as response:
                    response.raise_for_status()
                    return (await response.json())['message']
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # Hata durumunda tekrar denemek için bekleyelim
                print(f"Error for {password}: {e}")
                await asyncio.sleep(2**attempt)
        return "failed"

def generate_password_for_workers(api_passwd, queue, stop_event):
    """
    Rastgele şifreler oluşturarak verilen hash'e eşleşen şifreyi bulmaya çalışır.
    """
    i = 0

    # Hash'i bulana kadar rastgele şifreler oluştur
    while not stop_event.is_set():
        i += 1
        # Rastgele bir şifre oluştur
        password = "".join(random.choices(string.ascii_lowercase + " ", k=random.randint(PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH)))
        # Şifreyi hash'le
        hashed_passwd = hashlib.md5(password.encode()).hexdigest()
        # Hash'ler eşleşirse doğru şifreyi bulduk
        if api_passwd == hashed_passwd:
            print(f"Worker found correct password: {password}")
            print(f"Worker tried {i} passwords")
            # Doğru şifreyi queue'ya koy
            queue.put(password)
            break

async def daemon_task(queue, stop_event):
    """
        Daemon process sürekli rastgele şifre üretir ve API'ye gönderir.
        Eğer worker process'lerden birinden doğru şifre gelirse onu kullanır.
    """
    while not stop_event.is_set():
        # Rastgele bir şifre oluştur
        password = "".join(random.choices(string.ascii_lowercase+" ", k=random.randint(PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH)))
        print(f"Daemon sending password: {password}")

        try:
            # API'ye şifreyi gönder
            api_answer = await check_password(password=password)

            #API'den gelen cevap başarılıysa doğru şifreyi bulduk
            if api_answer == 'Success':
                print(f"Daemon found correct password: {password}")
                # Doğru şifreyi queue'ya koy
                queue.put(password)
                # Worker process'leri durdur
                stop_event.set()
                break
        except Exception as e:
            print(f"Error: {e}")

        # Worker process'lerden bir şifre geldi mi kontrol et
        if not queue.empty():
            # Doğru şifre geldi
            correct_password = queue.get()
            print(f"Daemon received correct password: {correct_password}")
            print(f"Daemon sending correct password to API :" + correct_password)
            # API'ye doğru şifreyi gönder
            api_answer = await check_password(password=correct_password)
            # API'den gelen cevabı yazdır
            print(f"API answer: {api_answer}")
            # Worker process'leri durdur
            stop_event.set()
            break

def daemon_process(queue, stop_event):
    """
        Wrapper fonksiyon, daemon_task fonksiyonunu çalıştırır.
        Multiprocessing içine async fonksiyonlar yazılamadığı için bu fonksiyon kullanılır.
    """
    asyncio.run(daemon_task(queue, stop_event))

def cracker(api_passwd: str, number_of_processes: int = 1):
    """
    Belirtilen hash'e karşılık gelen şifreyi brute-force yöntemiyle bulur.

    Args:
        api_passwd (str): Hedef hash (MD5 formatında).
        number_of_processes (int): Kullanılacak process sayısı.
    """

    # Daemon ve Worker process'leri başlatmak için gerekli değişkenler
    processes = []
    queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()

    # Daemon process'i başlat
    daemon = multiprocessing.Process(target=daemon_process, args=(queue, stop_event))
    daemon.daemon = True
    daemon.start()

    # Worker process'leri başlat
    for _ in range(number_of_processes):
        p = multiprocessing.Process(target=generate_password_for_workers, args=(api_passwd, queue, stop_event))
        processes.append(p)
        p.start()

    # Worker process'lerin bitmesini bekle
    for p in processes:
        p.join()

    # Daemon process'in durdurulmasını bekle
    daemon.join()


if __name__ == "__main__":

    # API'den hash'i al
    target_hash = get_password_from_api()
    print(f"Target hash: {target_hash}")

    # CPU sayısını yazdır (işlemci sayısı kadar process kullanılacak)
    print(f"CPU Count: {os.cpu_count()}")

    # 2 saniye bekle
    time.sleep(2)

    # Windows'ta multiprocessing kullanılırken spawn methodu kullanılır
    multiprocessing.set_start_method("spawn")

    # Kullanılacak süreç sayısını belirtelim
    cracker(target_hash, number_of_processes=os.cpu_count())
