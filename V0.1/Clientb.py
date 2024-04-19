#!/usr/bin/python3

import os, sys, signal,select ,socket,time

# if len(sys.argv) != 3:
#     print('Usage:', sys.argv[0], 'hote port')
#     sys.exit(1)

def signal_handler(sig,frame):
    print("Déconexion...")
    sys.exit(0)

UserName = input("Entrez un nom d'utilisateur :")
TUBE = "/var/tmp/"+UserName+".fifo"
LOG  = "/var/tmp/"+UserName+".log"

pid_LOGcreat = os.fork()
if pid_LOGcreat == 0 :
    os.execvp("touch",["touch",LOG])

pid_affichage = os.fork()
if pid_affichage == 0 :
    os.execvp("xterm",["xterm","-e","tail -f ",LOG])

pid_saisie = os.fork()
if pid_saisie == 0 :
    os.execvp("xterm",["xterm","-e","cat >"+TUBE])


time.sleep(1)
os.open(TUBE,os.O_RDONLY)
os.open(LOG,os.O_WRONLY)