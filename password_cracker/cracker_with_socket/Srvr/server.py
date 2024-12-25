import socket
import threading

class MyServer:
    def __init__(self, host='127.0.0.6', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.clients = []  # Bağlı istemcileri saklamak için bir liste

    def listen(self):
        self.server_socket.listen(5)
        print(f"Sunucu {self.host}:{self.port} üzerinde dinleniyor...")

    def broadcast_message(self, message):
        """
        Tüm bağlı istemcilere mesaj gönder.
        """
        print(f"Tüm istemcilere mesaj gönderiliyor: {message}")
        for client_socket in self.clients:
            try:
                client_socket.sendall(message.encode('utf-8'))
            except Exception as e:
                print(f"Mesaj gönderilemedi: {e}")
                self.clients.remove(client_socket)

    def handle_client(self, client_socket, client_address):
        """
        İstemci bağlantısını ele al.
        """
        print(f"Yeni bağlantı: {client_address}")
        self.clients.append(client_socket)  # İstemciyi listeye ekle

        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                print(f"Gelen mesaj {client_address}: {data}")
                # İstemciden gelen mesaja yanıt gönder
                client_socket.sendall("Mesaj alındı!".encode('utf-8'))
        except Exception as e:
            print(f"{client_address} ile iletişim kesildi: {e}")


    def accept_client(self):
        """
        Yeni istemci bağlantılarını kabul et.
        """
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                # Her yeni istemci için ayrı bir iş parçacığı oluştur
                client_thread = threading.Thread(
                    target=self.handle_client, args=(client_socket, client_address)
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("\nSunucu kapatılıyor...")
            self.close_socket()

    def close_socket(self):
        """
        Sunucuyu kapat.
        """
        for client_socket in self.clients:
            client_socket.close()
        self.server_socket.close()

if __name__ == "__main__":
    server = MyServer()
    server.listen()
    threading.Thread(target=server.accept_client).start()

    # Broadcast mesajı başlatıcı
    while True:
        try:
            message = input("Tüm istemcilere mesaj gönder (çıkmak için 'exit'): ")
            if message.lower() == "exit":
                server.close_socket()
                break
            server.broadcast_message(message)
        except KeyboardInterrupt:
            print("\nSunucu kapatılıyor...")
            server.close_socket()
            break
