#!/usr/bin/python3

import os, sys, socket, select,signal,atexit
HOST = sys.argv[1]  # or 'localhost' or '' - Standard loopback interface address
PORT = int(sys.argv[2])  # Port to listen on (non-privileged ports are > 1023)
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

def send_to_all_clients(message, sender_socket):
    # Parcours de toutes les sockets dans socketlist
    for client_socket in socketlist:
        # Vérifie si la socket est différente de la socket du serveur et du socket envoyant le message
        if client_socket != serversocket and client_socket != sender_socket:
            try:
                # Envoi du message à la socket du client
                client_socket.sendall(message)
            except Exception as e:
                # Gestion des erreurs lors de l'envoi du message
                print("Erreur lors de l'envoi du message :", e)
                client_socket.close()
                socketlist.remove(client_socket)

def send_to(Destinataire, message, socketdenvoie):
    pass

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
                source_info = f"[{carnet[s.getpeername()[1]][0]}] : "
                msg_with_source = source_info.encode() + msg +"\n".encode()
                os.write(1, msg_with_source)
                """ if msg[0] == '@' :
                    i = 1
                    for i in range(len(msg)) :
                        if msg[i] == " ":
                            break
                        i = i+1
                    nom = msg[1:i]
                    send_to(nom,msg,s)
                else :
                    send_to_all_clients(msg_with_source, s) """

sys.exit(0)