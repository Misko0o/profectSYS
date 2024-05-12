#!/usr/bin/python3

import os, sys, signal, socket, time
import select


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
carnet = {}
# def create_user_directory(username):
#     user_directory = "/" + username
#     if not os.path.exists(user_directory):
#         try:
#             os.makedirs(user_directory)
#             print(f"Répertoire utilisateur créé avec succès : {user_directory}")
#         except Exception as e:
#             print(f"Erreur lors de la création du répertoire utilisateur : {e}")
#     return user_directory

# TUBE = "/~"+create_user_directory(UserName) + "/" + UserName + ".fifo"
# LOG = "/~"+create_user_directory(UserName) + "/" + UserName + ".log"
# COOKIE = "/~"+create_user_directory(UserName) + "/" + UserName + ".tmp"
def create_cookie_file(cookie_path):
    try:
        if not os.path.exists(cookie_path):
            with open(cookie_path, 'w+'):
                print(f"Fichier cookie créé avec succès : {cookie_path}")
                return os.open(cookie_path,os.O_RDWR)
        else:
            print(f"Le fichier cookie existe déjà : {cookie_path}")
            return os.open(cookie_path,os.O_RDWR)
    except Exception as e:
        print(f"Erreur lors de la création du fichier cookie : {e}")
    

TUBE = "/var/tmp/"+UserName+".fifo"
LOG  = "/var/tmp/"+UserName+".log"
COOKIE="/var/tmp/"+UserName+"temp"+".txt"


Write=True
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
tmp=create_cookie_file(COOKIE)

clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
os.write(Reader,"\n \n \n".encode())

Conexion_etablie=False
try:
    clientsocket.connect((HOST, PORT))
except ConnectionRefusedError:  # Utilisez ConnectionRefusedError au lieu de "Connection refused"
    os.write(Reader,"   Server injoignable voulez vous reesayer?\n      --<!connect pour reesayer>--\n".encode())
    while not Conexion_etablie:
        Courage=os.read(Writer, 4096)
        if Courage.strip(b"!connect"):
            os.write(Reader,"Tentative de connexion>".encode())
            try:
                clientsocket.connect((HOST, PORT))
                Conexion_etablie=True   
            except ConnectionRefusedError:
                pass
        elif Courage.strip(b"!!Exit"):
            print("\n Déconnexion...")
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
clientsocket.send(b"")
var=os.read(tmp,4096)
if var.startswith(b"!C="):
        clientsocket.sendall(var[3:9])
        os.write(1,var[3:9])

os.waitpid(pid_LOGcreat,0)

def update_carnet(carnet_str):
    global Mon_etat
    print(carnet_str)
    valeurs = carnet_str.split('#') 
    UserName=valeurs[0]
    etat = valeurs[1]
    carnet[UserName]=etat
    
def affiche_carnet(carnet_str):
    for username,etat in carnet.items():
        Utilisateurs=f"-{username}=>(╗{etat}╝)\n"
        Util=Utilisateurs.encode()
        os.write(Reader,Util)

pid_child = os.fork()
signal.signal(signal.SIGINT, signal_handler)
if pid_child == 0:
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
                    elif(Write==True):                      
                        clientsocket.sendall(msg.encode())
            elif r == clientsocket:
                response = clientsocket.recv(4096)
                if response.startswith(b"#CARNET"):
                    update_carnet(response[8:].decode())
                elif response.startswith(b"!ban"):
                    os.kill(os.getpid(), signal.SIGINT)
                    #os.remove(COOKIE)
                elif response.startswith(b"!suspend"):
                    os.write(Reader, "Ecriture Gelée".encode())
                    Write=False
                elif response.startswith(b"!forgive"):
                    Write=True
                elif response.startswith(b"!start"):
                    coockie="!C=".encode()
                    coockie+=response[7:13]
                    os.write(1,coockie)
                    os.write(tmp,coockie)
                else:
                    os.write(Reader, response)
        
else:
    os._exit(0)
