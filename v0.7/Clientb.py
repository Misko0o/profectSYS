#!/usr/bin/python3

import os, sys, signal, socket, time
import select
if len(sys.argv) != 3:
    print('Usage:', sys.argv[0], 'hote port')
    sys.exit(1)

HOST = sys.argv[1]
PORT = int(sys.argv[2])

def signal_handler(sig,frame):
    print("\nDéconexion...")
    clientsocket.close()
    os.remove(TUBE)
    os.remove(LOG)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
UserName=""
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

while True:
    # Attendre que l'utilisateur entre une commande à envoyer au serveur
    readable, _, _ = select.select([Writer, clientsocket], [], [])
    for r in readable:
        if r == Writer:
            # Lecture de l'entrée utilisateur depuis le tube
            msg = os.read(Writer, 4096).decode()
            # Envoi du message au serveur
            clientsocket.sendall(msg.encode())
        elif r == clientsocket:
            # Réception des messages du serveur
            response = clientsocket.recv(4096)
            # Écriture de la réponse dans le fichier de log
            os.write(Reader, response)
            print("Réponse du serveur:", response.decode())

    # Vérifier si l'utilisateur veut quitter
# Fermer la connexion
clientsocket.close()