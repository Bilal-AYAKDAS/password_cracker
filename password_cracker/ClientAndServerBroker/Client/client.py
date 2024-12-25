import socket

class MyClient:
    def __init__(self, server_host='127.0.0.6', server_port=12345):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_server(self):
        try:
            # Sunucuya bağlan
            self.client_socket.connect((self.server_host, self.server_port))
            print("Sunucuya bağlanıldı.")
            # Mesaj gönder
            message = "Hello!"
            self.client_socket.sendall(message.encode('utf-8'))
        except ConnectionRefusedError:
            print("Sunucuya bağlanılamadı!")

    def receive_message(self):
        response = self.client_socket.recv(1024).decode('utf-8')


    def send_message(self, message):
        self.client_socket.sendall(message.encode('utf-8'))

    def close_socket(self):
        self.client_socket.close()

if __name__ == "__main__":
    client = MyClient()
    client.connect_server()
    client.close_socket()
