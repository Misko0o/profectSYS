
#!/usr/bin/python3

import os, sys, signal, socket, time
import select

carnet = {}
if len(sys.argv) != 3:
    print('Usage:', sys.argv[0], 'hote port')
    sys.exit(1)

HOST = sys.argv[1]
PORT = int(sys.argv[2])

# Fonction pour gérer le signal d'interruption (Ctrl+C)
def signal_handler(sig, frame):
    print("\nDéconnexion...")
    # # # # # # # if pid_child > 0:
    # # # # # # #     os.kill(pid_child, signal.SIGINT) c'est debile XD
    clientsocket.close()
    os.remove(TUBE)
    os.remove(LOG)
    os._exit(0)


signal.signal(signal.SIGINT, signal_handler)

UserName = ""
UserName = input("Entrez un nom d'utilisateur :")
UserName = UserName.replace(' ', '_')
print("Nom d'utilisateur traité :", UserName)

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
clientsocket.connect((HOST, PORT))
clientsocket.sendall(UserName.encode())
os.waitpid(pid_LOGcreat,0)


def update_carnet(carnet_str):
    global carnet
    carnet = eval(carnet_str)

def affiche_carnet(carnet_str):
    global carnet
    carnet = eval(carnet_str)
    for port, (username, addr) in carnet.items():
        if (username==UserName):
            print(f"moi")
        else:
            print(f"{username} ({addr})")




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
                        print("Affichage du carnet :")
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
                elif response.startswith(b"#EXIT#"):
                    os.kill(os.getpid(), signal.SIGINT)
                else:
                    os.write(Reader, response)
        
else:
    os._exit(0)
    