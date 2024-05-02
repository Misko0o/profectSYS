#!/usr/bin/python3

import os, sys, socket, select,signal,atexit,time
HOST = "127.0.0.1"  # or 'localhost' or '' - Standard loopback interface address
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
TUBE = "/var/tmp/admin.fifo"
pid_saisie = os.fork()
if pid_saisie == 0 :
    os.execvp("xterm",["xterm","-e","cat >"+TUBE])#Detache une fenetre fifo(TUBE)
time.sleep(1)
Writer=os.open(TUBE,os.O_RDONLY)
socketlist = [serversocket,Writer]
first = True

def clafin():
    os.remove(TUBE)
    print("Last connection closed. Bye!")
atexit.register(clafin)

def signal_handler(sig,frame):
    print("\nDéconexion...")
    clafin()
    sys.exit(0) 
signal.signal(signal.SIGINT, signal_handler)

def send_to_user(message,sender_socket,recivier):
    for s in socketlist:
        if s != serversocket:
            name = carnet[s.getpeername()[1]][0]
            if name in recivier:
                s.sendall(message)
    sender_socket.sendall(message)

def broadcast_message(message):
    # Parcours de toutes les sockets dans socketlist
    for client_socket in socketlist:
        # Vérifie si la socket est différente de la socket du serveur et du socket envoyant le message
        if client_socket != serversocket and client_socket != Writer:
            try:
                # Envoi du message à la socket du client
                client_socket.sendall(message)
            except Exception as e:
                # Gestion des erreurs lors de l'envoi du message
                print("Erreur lors de l'envoi du message :", e)
                client_socket.close()
                socketlist.remove(client_socket)

while first or nb_open > 0:
    (activesockets, _, _) = select.select(socketlist, [], [])
    for s in activesockets:
        if s == serversocket:
            (clientsocket, (addr, port)) = serversocket.accept()
            socketlist.append(clientsocket)
            UserName = clientsocket.recv(MAXBYTES).decode()
            carnet[port] = (UserName,addr)
            # print(f"{carnet}")
            print(f"Incoming connection from {UserName} {addr} on port {port}...")
            first = False
            nb_open += 1
        elif s == Writer :
            msg = os.read(Writer, 4096).decode()
            if msg != '':
                print(msg,end='')
                broadcast_message(msg.encode())
        else:
            msg = s.recv(MAXBYTES)
            if len(msg) == 0:
                print(f"NULL message. Closing connection for {carnet[s.getpeername()[1]][0]} {s.getpeername()}")
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
                    recipient_username = msg_str.split(" ")
                    destinataires = []
                    for e in recipient_username :
                        if e[0] == '@' :
                            destinataires.append(e[1:])

                    # Send the message only to this user
                    send_to_user(msg_mine, s,destinataires)
                else:
                # Envoie le message a tout les clients
                    broadcast_message(msg_mine)
sys.exit(0)


