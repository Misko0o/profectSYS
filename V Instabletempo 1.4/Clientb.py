#!/usr/bin/python3

import os, sys, signal, socket, time
import select

carnet = {}
if len(sys.argv) != 3:
    print('Usage:', sys.argv[0], 'hote port')
    sys.exit(1)

HOST = sys.argv[1]
PORT = int(sys.argv[2])

UserName = ""
UserName = input("Entrez un nom d'utilisateur :")
MyUserName = UserName.replace(' ', '_')
print("Nom d'utilisateur traité :", UserName)
etat="Vivant"

TUBE = "/var/tmp/"+UserName+".fifo"
LOG  = "/var/tmp/"+UserName+".log"

pid_LOGcreat = os.fork()
if pid_LOGcreat == 0 :
    os.execvp("touch",["touch",LOG])

pid_affichage = os.fork()
if pid_affichage == 0 :
    souscommande = "tail -f {}".format(LOG)
    os.execvp("xterm",["xterm","-e",souscommande])

pid_saisie = os.fork()
if pid_saisie == 0 :
    os.execvp("xterm",["xterm","-e","cat >"+TUBE])

print("Terminal de saisie ouvert sur : {}\nTerminal de lecture ouvert sur : {}\nPrograme principal ouvert sur :{}".format(pid_saisie,pid_affichage,os.getpid()))

time.sleep(1)
Writer=os.open(TUBE,os.O_RDONLY)
Reader=os.open(LOG,os.O_WRONLY)

clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    clientsocket.connect((HOST, PORT))
except ConnectionRefusedError:  # Utilisez ConnectionRefusedError au lieu de "Connection refused"
    print("Serveur Non atteignable")
    # Supprimer les fichiers TUBE et LOG
    if os.path.exists(TUBE):
        os.remove(TUBE)
    if os.path.exists(LOG):
        os.remove(LOG)
    try:
        os.kill(pid_affichage, signal.SIGTERM)
        os.waitpid(pid_affichage, 0)
    except ChildProcessError:
        pass

    try:
        os.kill(pid_saisie, signal.SIGTERM)
        os.waitpid(pid_saisie, 0)
    except ChildProcessError:
        pass
    
    sys.exit(0) 

def signal_handler(sig, frame):
    print("\n Déconnexion...")
    clientsocket.close()
    os.remove(TUBE)
    os.remove(LOG)

    try:
        os.kill(pid_affichage, signal.SIGTERM)
        os.waitpid(pid_affichage, 0)
    except ChildProcessError:
        pass

    try:
        os.kill(pid_saisie, signal.SIGTERM)
        os.waitpid(pid_saisie, 0)
    except ChildProcessError:
        pass

    os._exit(0)

clientsocket.sendall(UserName.encode())
os.waitpid(pid_LOGcreat,0)


Mon_addr = ""
Mon_port = ""
Mon_etat = ""

def update_carnet(carnet_str):
    global Mon_addr, Mon_port, Mon_etat
    valeurs = carnet_str.split('#') 
    UserName=valeurs[0]
    if UserName == MyUserName:
        Mon_addr = valeurs[1]
        Mon_port = valeurs[2]
        Mon_etat = valeurs[3]
        print(Mon_addr, Mon_port, Mon_etat, UserName)
    else:
        addr = valeurs[2]
        port = valeurs[3]
        etat = valeurs[1]
        carnet[port] = (UserName, addr, etat)



def affiche_carnet(carnet_str):
    for port, (username, addr, port, etat) in carnet.items():
        if (username==UserName):
            moi = "-moi(" + etat + ")\n"
            moi2 = moi.encode()
            os.write(Reader,moi2)
        else:
            Utilisateurs=f"-{username} ({addr} ,{etat})\n"
            Util=Utilisateurs.encode()
            os.write(Reader,Util)

pid_child = os.fork()
signal.signal(signal.SIGINT, signal_handler)
if pid_child == 0:
    print(os.getpid())
    # Code exécuté dans le processus enfant

    while True:
        readable, _, _ = select.select([Writer, clientsocket], [], [])
        for r in readable:
            if r == Writer:
                msg = os.read(Writer, 4096).decode()
                if msg != '':
                    if msg.strip() == "!List":
                        msg_Affi = "Affichage du carnet :\n".encode()
                        os.write(Reader, msg_Affi)
                        affiche_carnet(str(carnet))
                    elif msg.strip() == "!!Exit":
                        
                        os.kill(os.getpid(), signal.SIGINT)
                        break
                    else:
                        clientsocket.sendall(msg.encode())
            elif r == clientsocket:
                response = clientsocket.recv(4096)
                if response.startswith(b"#CARNET#"):
                    update_carnet(response[8:].decode())
                    print(carnet)
                elif response.startswith(b"Mort"):
                    print(response)
                elif response.startswith(b"!ban"):
                    Mon_etat="Mort"
                    cookie_volatil = cookie_volatil = f"#CARNET#{MyUserName}#{Mon_addr}#{Mon_port}#{etat}#".encode()
                    time.sleep(5)
                    clientsocket.sendall(cookie_volatil)
                    os.kill(os.getpid(), signal.SIGINT)
                else:
                    os.write(Reader, response)
        
else:
    os._exit(0)