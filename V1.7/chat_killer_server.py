#!/usr/bin/python3

import os, sys, socket, select,signal,atexit,time,random
HOST = "127.0.0.1"  # or 'localhost' or '' - Standard loopback interface address
PORT = int(sys.argv[1])  # Port to listen on (non-privileged ports are > 1023)
MAXBYTES = 4096
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4, TCP
serversocket.bind((HOST, PORT))
serversocket.listen()
print("server listening on port:", PORT)
nb_open = 0
Detecteur=""
etat="Vivant"
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
    sys.exit(0) 
signal.signal(signal.SIGINT, signal_handler)

def send_to_user(message,recivier):
    for s in socketlist:
        if s != serversocket and s != Writer:
            name = carnet[s.getpeername()[1]][0]
            if name in recivier:
                s.sendall(message)


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

def send_commande(destinaire,commande):
    for s in socketlist:
        if s != serversocket and s != Writer:
            name = carnet[s.getpeername()[1]][0]
            if name in destinaire:
                s.sendall(commande.encode())
lancé = False
while first or nb_open > 0:
    (activesockets, _, _) = select.select(socketlist, [], [])
    for s in activesockets: 
        if s == serversocket:
            if not lancé :
                (clientsocket, (addr, port)) = serversocket.accept()
                socketlist.append(clientsocket)
                UserName = clientsocket.recv(MAXBYTES).decode()
                # _ = clientsocket.recv(MAXBYTES).decode() #ignore la deuxieme entrée
                cookie = random.randint(100000,999999)
                mots_courants = ["maison","chat","voiture","chien","ordinateur","table","téléphone","arbre","café","livre","fenêtre","porte","avion","banane","musique","soleil","pluie","sac","télévision","crayon"]
                carnet[port] = (UserName,addr,etat,str(cookie),clientsocket,random.choice(mots_courants))
                for page in carnet:
                    a = f"#CARNET#{carnet[page][0]}#{carnet[page][2]} "
                    clientsocket.sendall(a.encode())
                    time.sleep(0.1)
                cookie_volatil = f"#CARNET#{UserName}#{etat}"
                print(f"Incoming connection from {UserName} {addr} on port {port}... id {cookie}")
                cokie_encodé=cookie_volatil.encode()
                broadcast_message(cokie_encodé)
                first = False   
                nb_open += 1
            else:
                (clientsocket, (addr, port)) = serversocket.accept()

                UserName = clientsocket.recv(MAXBYTES).decode()
                CookieRecu = clientsocket.recv(MAXBYTES).decode() #ignore la deuxieme entrée
                for (index,page) in carnet.items() :
                    (User,oldaddr,etat,cookie,oldsocket,mot) = page
                    if User == UserName:
                        if CookieRecu != cookie:
                            clientsocket.send("La partie a commencé".encode())
                            os.write(1,"Une conection a été refusée".encode())
                            clientsocket.close()
                        else :
                            del carnet[index]
                            carnet[port] = (UserName,addr,etat,cookie,clientsocket,mot)
                            print(f"Incoming connection from {UserName} {addr} on port {port}... id {cookie}")

                            socketlist.append(clientsocket)
                        break
                
                print(f"{carnet}")
        elif s == Writer :
            msg = os.read(Writer, 4096)
            if msg.startswith(b'!start') and not lancé: #On Cook severe ici
                lancé = True
                ordre = []
                for (index,page) in carnet.items() :
                    UserName,_,_,cookie,clientsocket,mot = page #c caca
                    ordre.append(index)
                    lancement = f"!start {cookie}".encode()
                    # os.write(1,lancement)
                    clientsocket.send(lancement)
                broadcast_message("La partie est lancé vous allez recevoir vos cible\n".encode())
                random.shuffle(ordre)
                os.write(1,str(ordre).encode())
                for i in range(len(ordre)):
                    nomcible,motcible,socketkiller = carnet[ordre[i-1]][0] , carnet[ordre[i-1]][5] , carnet[ordre[i]][4]
                    message = f"Ta cible est {nomcible} son mot est {motcible}\n"
                    socketkiller.sendall(message.encode())
            elif msg.startswith(b"@"):
                recipient = msg.decode().split(" ")
                destinataires = []
                iscommande = False
                for e in recipient :
                        if e[0] == '@' :
                            destinataires.append(e[1:])
                        elif e[0] == '!': 
                            commande = e
                            send_commande(destinataires,commande)
                            iscommande = True
                if not iscommande:
                    send_to_user(msg,destinataires)
                    print(f"*Comande invalide*\n")
            elif msg != '' and msg != "\n":
                msg = msg
                os.write(1,msg)
                broadcast_message(msg)
        else:
            msg = s.recv(MAXBYTES)
            if len(msg) == 0:
                print("NULL message. Closing connection for", carnet[s.getpeername()[1]][0], s.getpeername())
                port = s.getpeername()[1]  # Obtenez le numéro de port à partir de la socket
                condamné = carnet[port]  # Utilisez le numéro de port pour accéder à l'entrée dans carnet
                a = f"#CARNET#{condamné[0]}#Mort".encode()  # Utilisez le nom d'utilisateur de l'entrée carnet
                broadcast_message(a)
                s.close()
                socketlist.remove(s)
                
                nb_open -= 1
            else:
                qui = s.getpeername()[1]
                source_info = f"[{carnet[qui][0]}] : {msg.decode()}"
                msg_mine = source_info.encode() 
                os.write(1, msg_mine)
                if lancé and (carnet[qui][5] in msg.decode()):
                    broadcast_message(f"{carnet[qui][0]} est mort !\n".encode())
                if msg.startswith(b"@Admin"):
                    pass
                elif msg.startswith(b"@"):
                    msg_str = msg.decode()
                    recipient_username = msg_str.split(" ")
                    destinataires = [s]
                    for e in recipient_username:
                        if e[0] == '@':
                            destinataires.append(e[1:])
                    send_to_user(msg_mine, destinataires)
                else:
                    broadcast_message(msg_mine)
sys.exit(0)
