#!/usr/bin/python3

import os, sys, socket, select,signal,atexit
HOST = "134.59.2.160"  # or 'localhost' or '' - Standard loopback interface address
PORT = int(sys.argv[1])  # Port to listen on (non-privileged ports are > 1023)
MAXBYTES = 4096
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4, TCP
serversocket.bind((HOST, PORT))
serversocket.listen()
print("server listening on port:", PORT)
nb_open = 0
carnet = dict()
# Create list of potential active sockets and place server socket in
# first positionezr 
socketlist = [serversocket]
first = True

def clafin():
    serversocket.close()
    print("Last connection closed. Bye!")
    sys.exit(0)
atexit.register(clafin)
def signal_handler(sig,frame):
    print("\nDéconexion...")
    clafin()
    sys.exit(0) 

signal.signal(signal.SIGINT, signal_handler)

def send_to_user(message,sender_socket,recivier):
    pass

def broadcast_message(message, sender_socket):
    # Parcours de toutes les sockets dans socketlist
    for client_socket in socketlist:
        # Vérifie si la socket est différente de la socket du serveur et du socket envoyant le message
        if client_socket != serversocket:
            try:
                # Envoi du message à la socket du client
                client_socket.sendall(message)
            except Exception as e:
                # Gestion des erreurs lors de l'envoi du message
                print("Erreur lors de l'envoi du message :", e)
                client_socket.close()
                socketlist.remove(client_socket)

while first or nb_open > 0:
    first = False
    (activesockets, _, _) = select.select(socketlist, [], [])
    for s in activesockets:
        if s == serversocket:
            (clientsocket, (addr, port)) = serversocket.accept()
            socketlist.append(clientsocket)
            UserName = clientsocket.recv(MAXBYTES).decode()
            carnet[port] = (UserName,addr)
            # print(f"{carnet}")
            print(f"Incoming connection from {UserName} {addr} on port {port}...")
            nb_open += 1
        else:
            msg = s.recv(MAXBYTES)
            if len(msg) == 0:
                print(f"NULL message. Closing connection for {carnet[s.getpeername()[1]][0]}")
                s.close()            
                socketlist.remove(s)
                nb_open -= 1
            else:
                source_info = f"[{carnet[s.getpeername()[1]][0]}] : {msg.decode()}"
                msg_mine = source_info.encode()
                os.write(1, msg_mine)
                # Vérifie si le message commence par "@"
                if msg.startswith(b"@"):
                    msg_str = msg.decode()
                    # Extract the username from the part "@user"
                    recipient_username = msg_str.split(" ")[0][1:]
                    # Send the message only to this user
                    send_to_user(msg_mine, recipient_username,None)
                    broadcast_message(msg_mine, s)
                else:
                # Envoie le message a tout les clients
                    broadcast_message(msg_mine, s)
sys.exit(0)


