import socket, threading
import client_handler
address = ('0.0.0.0', 6543)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(address)
server.listen(100)
while True:
    client, addr = server.accept()
    p = threading.Thread(target=client_handler.handler, args=(client, addr))
    p.start()
