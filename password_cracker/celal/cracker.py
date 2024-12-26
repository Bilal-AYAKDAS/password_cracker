import asyncio
import aiohttp
import logging
import itertools
import string
import multiprocessing

logging.basicConfig(
    format="%(levelname)s @ %(asctime)s : %(message)s",
    datefmt="%d.%m.%Y %H:%M:%S",
    level=logging.INFO,
    handlers=[logging.FileHandler("requests.log", mode="w"), logging.StreamHandler()],
)

async def get_password(session:aiohttp.ClientSession,url):
        response = await session.get(f"{url}/get_password")
        password = (await response.json()).get("password")
        return password
        
async def post_password(session:aiohttp.ClientSession,url,password,retrie=3):
    for _ in range(retrie):
        try:
            response = await session.post(
                f"{url}/check_password",
                json={"password": password}
            )
            response.raise_for_status()
            logging.info(f"Request returned for {password} with status code {response.status}")
            message = (await response.json()).get("message")
            if message == "Success":
                logging.info(f"Password {password} is correct")
                return "Success"
            return "Failed" 
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logging.error(f"Error for {password}: {e}")
            continue
    return "Retrie"
    

async def get_main():
    url = "http://127.0.0.1:5000"
    async with aiohttp.ClientSession() as session:
        password = await get_password(session, url)
        return password

async def post_main(password):
    url = "http://127.0.0.1:5000"
    async with aiohttp.ClientSession() as session:
        message = await post_password(session, url, password)
        return message

def generate_combinations(charset: str, length: int = 4):
    for combo in itertools.product(charset, repeat=length):
        yield ''.join(combo)

async def main(length):
    charset = string.digits + string.ascii_letters
    found_password = False  # Flag to track if password is found

    try:        
        generator = generate_combinations(charset, length)
        combination_count = len(charset) ** length
        batch_size = combination_count / 10
        print(f"Total combinations: {combination_count}")
        passwords = []
        retrie_passwords = []
        passwords += retrie_passwords.copy()

        for combination in generator:
            if found_password:  
                break

            retrie_passwords = []        
            passwords.append(combination)
            if len(passwords) > batch_size:
                tasks = [post_main(password) for password in passwords]
                results = await asyncio.gather(*tasks)
                    
                if "Success" in results:
                    found_password = True
                    success_index = results.index("Success")
                    logging.info(f"Password found: {passwords[success_index]}")
                    break

                if "Retrie" in results:
                    retrie_passwords.append(passwords[results.index("Retrie")])
                    
                passwords = []
                print(f"Retrie passwords: {retrie_passwords}")
                    
    except StopIteration:
        pass

    if not found_password:
        logging.info("No password found")

if __name__ == "__main__":
    password = asyncio.run(get_main())
    
    print(f"Target hash: {password}")
    for i in range(1, 5):
        asyncio.run(main(length=i))