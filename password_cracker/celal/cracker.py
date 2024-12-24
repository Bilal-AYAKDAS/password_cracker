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
class PasswordControllerThread(threading.Thread):
    def __init__(session:aiohttp.ClientSession,
                 base_url:str,
                 endpoint:str,
                 password):#password is a tuple of (password,hash) we need to send hash
        pass ## TODO: implement constructor
    #bunu neden kullandım belki asenkron bir thread ile local olarak kontrol etmek hızlı olabilir emin değilim

        
    async def check_password_using_api(session:aiohttp.ClientSession,base_url:str,endpoint:str,password)->str:
        async with session.post(base_url + endpoint, json={"password": password}) as response:
            message = await response.json()
            return message.get("message")


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
        #beklediğim gibi çalışıyor bu method a*password_length - 9*password_length a kadar çalışıyor
        #kombinasyonları getiriyor atomik olarak burayı çektim
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
        #burası yarım ne yazacam bilemdim
    
    

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
        self.passwords = []

    async def start_cracking(self,session:aiohttp.ClientSession):
        for length in range(self.min_password_length,self.max_password_length+1):
            logging.info(f"Starting to crack passwords of length {length}")
            cracker_threads = []
            for i in range(self.min_password_length,self.max_password_length):
                cracker_threads.append(PasswordCrackerThread(i,self.characters))
            
            for thread in cracker_threads:
                thread.start()
            
            for thread in cracker_threads:
                thread.join()
            
            for thread in cracker_threads:
                self.passwords += thread.password_tuples
            
            logging.info(f"Finished cracking passwords of length {length}")
            #burası yarım daha kafamda kuramadım belki kontrol etmeyi async thread yapabiliriz 
            

    async def get_password_from_api(session:aiohttp.ClientSession,base_url:str,endpoint:str)->str:
        async with session.get(base_url + endpoint) as response:
            password = await response.json()
            return password.get("password")
    

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