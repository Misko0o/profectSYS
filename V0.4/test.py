#!/usr/bin/python3

import socket

HOST = '127.0.0.1'  # L'adresse IP du serveur
PORT = 2005         # Le port sur lequel le serveur écoute

# Créer un socket TCP/IP
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connecter le socket au serveur
clientsocket.connect((HOST, PORT))

while True:
    # Attendre que l'utilisateur entre une commande à envoyer au serveur
    command = input("Entrez une commande à envoyer au serveur (ou 'exit' pour quitter): ")

    # Envoyer la commande au serveur
    clientsocket.sendall(command.encode())

    # Recevoir la réponse du serveur
    response = clientsocket.recv(4096)

    # Afficher la réponse
    print("Réponse du serveur:", response.decode())

    # Vérifier si l'utilisateur veut quitter
    if command.lower() == 'exit':
        break
        
# Fermer la connexion
clientsocket.close()
