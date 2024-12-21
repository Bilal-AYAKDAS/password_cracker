import logging
import threading
import hashlib
import string
import asyncio
import aiohttp
from numba import jit

BASE_URL = "http://localhost:5000/"
GET_ENDPOINT = "get_password"
POST_ENDPOINT = "check_password"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
    
class PasswordCrackerThread(threading.Thread):
    def __init__(self, 
                 password_length:int,
                 character_set:str):
        super().__init__(self,name=f"CrackerThread-{password_length}")
        self.password_length = password_length
        self.character_set = character_set
        self.password_tuples = []
    
    @staticmethod
    @jit(nopython=True,nogil=True)
    def brute_force_password(characters: str, password_length: int):
        results = []
        total_combinations = len(characters) ** password_length
        for i in range(total_combinations):
            combination = []
            temp = i
            for _ in range(password_length):
                combination.append(characters[temp % len(characters)])
                temp //= len(characters)
            results.append("".join(combination))
        return results
    
    def run(self):
        for password in self.brute_force_password(self.character_set,self.password_length):
            password_hash = hashlib.md5(password.encode()).hexdigest()
            self.password_tuples.append((password,password_hash))
        

    def join(self):
        super().join()
    
    

class PasswordCrackerDaemon(threading.Thread):
    def __init__(self,
                 min_password_length:int,
                 max_password_length:int,
                 characters:str,
                 base_url:str,
                 get_endpoint:str,
                 post_endpoint:str,
                 chunk_size:int=100000):
        super().__init__(self,name="CrackerDaemon",daemon=True)
        self.min_password_length = min_password_length
        self.max_password_length = max_password_length
        self.characters = characters
        self.base_url = base_url
        self.get_endpoint = get_endpoint
        self.post_endpoint = post_endpoint
        self.chunk_size = chunk_size

    async def start_cracking(self,session:aiohttp.ClientSession):
        for length in range(self.min_password_length,self.max_password_length+1):
            logging.info(f"Starting to crack passwords of length {length}")
            cracker_thread = PasswordCrackerThread(length,self.characters)

            if len(password_tuples) <= self.chunk_size:
                message = await self.check_password_using_api(session,cracker_thread.password_tuples)
                logging.info(message)
                if message == "Success":
                    break
            

    async def get_password_from_api(session:aiohttp.ClientSession,base_url:str,endpoint:str)->str:
        async with session.get(base_url + endpoint) as response:
            password = await response.json()
            return password.get("password")
    
    async def check_password_using_api(session:aiohttp.ClientSession,base_url:str,endpoint:str,password:str)->str:
        async with session.post(base_url + endpoint, json={"password": password}) as response:
            message = await response.json()
            return message.get("message")
    

    def run(self):
        asyncio.run(self.start_cracking())  



if __name__ == "__main__":
    characters = string.ascii_letters + string.digits
    min_password_length = 8
    max_password_length = 16
    
    daemon = PasswordCrackerDaemon(min_password_length,
                                   max_password_length,
                                   characters,
                                   BASE_URL,
                                   GET_ENDPOINT,
                                   POST_ENDPOINT)
    daemon.start()
    daemon.join()