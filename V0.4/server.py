#!/usr/bin/python3

import os, sys, socket, select,signal
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
socketlist = [serversocket]
first = True
while first or nb_open > 0:
    first = False
    (activesockets, _, _) = select.select(socketlist, [], [])
    for s in activesockets:
        if s == serversocket:
            (clientsocket, (addr, port)) = serversocket.accept()
            socketlist.append(clientsocket)
            UserName = clientsocket.recv(MAXBYTES).decode()
            carnet[port] = (UserName,addr)
            print(f"{carnet}")
            print(f"Incoming connection from {UserName} {addr} on port {port}...")
            nb_open += 1
        else:
            msg = s.recv(MAXBYTES)
            if len(msg) == 0:
                print("NULL message. Closing connection...")
                s.close()            
                socketlist.remove(s)
                nb_open -= 1
            else:
                source_info = f"[{carnet[s.getpeername()[1]][0]}] : "
                msg_with_source = source_info.encode() + msg +"\n".encode()
                os.write(1, msg_with_source)
                # question 2: on veut que le serveur execute la commande `msg` et 
                # renvoie le resultat au client.
                # opérations à effectuer: fork, redirection, exec (dans cet ordre)
                """ pid = os.fork()
                if pid == 0:
                    os.dup2(s.fileno(), 0)
                    os.dup2(s.fileno(), 1)
                    os.dup2(s.fileno(), 2)
                    os.close(s.fileno())
                    args = msg.decode().split()
                    os.execvpe(args[0], args, os.environ) 
                else:
                    os.waitpid(pid, 0)"""
serversocket.close()
print("Last connection closed. Bye!")
sys.exit(0)