import numpy as np
from numba import cuda
import hashlib

BASE_URL = "http://127.0.0.1:5000"
CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
CHARSET_SIZE = len(CHARS)

@cuda.jit
def crack_password_kernel(md5_hash, found_flag, result, max_length):
    idx = cuda.grid(1)  # Global thread index

    # Eğer bir thread şifreyi bulmuşsa diğerlerini durdur
    if found_flag[0]:
        return

    # Thread indexine göre bir şifre oluştur
    password = cuda.local.array(8, dtype=cuda.uint8)
    temp_idx = idx
    for i in range(max_length):
        password[i] = ord(CHARS[temp_idx % CHARSET_SIZE])
        temp_idx //= CHARSET_SIZE

    # Şifreyi byte dizisine çevir
    password_bytes = bytearray(password[:max_length])

    # MD5 hash hesapla
    hashed_password = hashlib.md5(password_bytes).digest()

    # Hash eşleşirse sonucu kaydet ve diğer thread'leri durdur
    if hashed_password == md5_hash:
        for i in range(max_length):
            result[i] = password[i]
        found_flag[0] = True


def main():
    # Hedef MD5 hash (elle belirtilmiş)
    md5_hash = bytes.fromhex("8ff944a148b9ef870bc34d9db06a0c0b")  # Hex formatını byte dizisine dönüştür
    print(f"Target MD5 Hash: {md5_hash.hex()}")

    # Parametreler
    max_length = 4  # Şifre uzunluğu
    total_combinations = CHARSET_SIZE ** max_length

    # CUDA ayarları
    threads_per_block = 256
    blocks = (total_combinations + threads_per_block - 1) // threads_per_block

    # CUDA belleği hazırlığı
    found_flag = np.array([False], dtype=np.bool_)
    result = np.zeros(max_length, dtype=np.uint8)

    d_md5_hash = cuda.to_device(np.frombuffer(md5_hash, dtype=np.uint8))
    d_found_flag = cuda.to_device(found_flag)
    d_result = cuda.to_device(result)

    # Kernel çağrısı
    crack_password_kernel[blocks, threads_per_block](d_md5_hash, d_found_flag, d_result, max_length)

    # Sonuçları GPU'dan al
    d_found_flag.copy_to_host(found_flag)
    d_result.copy_to_host(result)

    if found_flag[0]:
        password = ''.join([chr(c) for c in d_result])
        print(f"Password found: {password}")
    else:
        print("Password not found.")

if __name__ == "__main__":
    main()
