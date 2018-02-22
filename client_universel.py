# -*- coding: utf-8 -*-

"""Code par Victor Josso"""

#from __future__ import unicode_literals
import socket
import getpass
import hashlib
import threading
import sys
import datetime
import time
import os
import pickle
import zipfile
import glob
import shutil
import binascii

import Crypt as crpt
import Uncrypt as ucrpt
import generate_random_passwords as r_pass

hote = "127.0.0.1"
port = 26281

colours = {
	"default"    :    "\033[0m",
	# style
	"bold"       :    "\033[1m",
	"underline"  :    "\033[4m",
	"blink"      :    "\033[5m",
	"reverse"    :    "\033[7m",
	"concealed"  :    "\033[8m",
	# couleur texte
	"black"      :    "\033[30m",
	"red"        :    "\033[31m",
	"green"      :    "\033[32m",
	"yellow"     :    "\033[33m",
	"blue"       :    "\033[34m",
	"magenta"    :    "\033[35m",
	"cyan"       :    "\033[36m",
	"white"      :    "\033[37m",
	# couleur fond
	"on_black"   :    "\033[40m",
	"on_red"     :    "\033[41m",
	"on_green"   :    "\033[42m",
	"on_yellow"  :    "\033[43m",
	"on_blue"    :    "\033[44m",
	"on_magenta" :    "\033[45m",
	"on_cyan"    :    "\033[46m",
	"on_white"   :    "\033[47m" }

class Releve(threading.Thread):
    def __init__(self):
        self.msg_received = False
        threading.Thread.__init__(self)
        self.running = True

    def run(self):
        while True:
            msg=connection_server.recv(33554432) #reception du message envoye par le server.
            if msg == "SERVER\\SHUTDOWN":
                #Permet de deverouiller le server et d'afficher un message pour l'utilisateur en cas d'arret programme du server.
                connection_server.send("OK")
                self.running = False
                print "Server has been shutdowned. Please wait until it restarts."
                server_reachable = False
                break
            else:
                #Enregistement du message dans un fichier afin de le recuperer dans le MainThread.
                with verrou:
                    f = open("response", "w")
                    f.write(msg)
                    f.close()
                    self.msg_received = True
            if not self.running:
                break

def zipdirectory(filezip, pathzip):
    #Cette fonction cree une archive Zip. Elle est utlisee pour faire des sauvegardes lors de la deconnexion.
    lenpathparent = len(pathzip)+1   ## utile si on veut stocker les chemins relatifs
    def _zipdirectory(zfile, path):
        for i in glob.glob(path+'/*'):
            if os.path.isdir(i): _zipdirectory(zfile, i )
            else:
                zfile.write(i, i[lenpathparent:]) ## zfile.write(i) pour stocker les chemins complets
    zfile = zipfile.ZipFile(filezip,'w',compression=zipfile.ZIP_DEFLATED)
    _zipdirectory(zfile, pathzip)
    zfile.close()

def backup():
    global username
    global mdp
    zipdirectory("backup.zip", username)
    backup_crpt = crpt.crypt("backup.zip", mdp)
    bkp_file = open(backup_crpt, 'rb')
    msg_to_send = "BACKUP\\"+binascii.hexlify(bkp_file.read())
    print "Envoi de la sauvegarde..."
    connection_server.send(msg_to_send)
    print "Envoye ! "
    bkp_file.close()
    os.remove(backup_crpt)
    with open("bkp_sended.txt", "a") as f:
        f.write(msg_to_send)
    return backup_crpt

def dezip(filezip, pathdst = ''):
    if pathdst == '': pathdst = os.getcwd()  ## on dezippe dans le repertoire locale
    zfile = zipfile.ZipFile(filezip, 'r')
    for i in zfile.namelist():  ## On parcourt l'ensemble des fichiers de l'archive
        if os.path.isdir(i):   ## S'il s'agit d'un repertoire, on se contente de creer le dossier
            try: os.makedirs(pathdst + os.sep + i)
            except: pass
        else:
            try: os.makedirs(pathdst + os.sep + os.path.dirname(i))
            except: pass
            data = zfile.read(i)                   ## lecture du fichier compresse
            fp = open(pathdst + os.sep + i, "wb")  ## creation en local du nouveau fichier
            fp.write(data)                         ## ajout des donnees du fichier compresse dans le fichier local
            fp.close()
    zfile.close()

def get_backup():
    global username
    global mdp
    connection_server.send("GET\\backup")
    msg_from_server = attendre_reponse()
    if msg_from_server.split("\\")[:3] == ["GIVE", "backup", "OK"]:
        bkp = msg_from_server.split("\\")[3]
        bkp = binascii.unhexlify(bkp)
        new_backup = open("backup.zip","wb")
        new_backup.write(bkp)
        new_backup.close()
        ucrpt.uncrypt("backup.zip", mdp)
        dezip("backup.zip", username)
        os.remove("backup.zip")
    elif msg_from_server.split("\\")[:3] == ["GIVE", "backup", "UNABLE"]:
        pass
    elif msg_from_server.split("\\") == "GET\\REFUSED":
        print "Accès refusé. Veuillez réessayer !"
        os.remove("log_infos.pkl")
        sys.exit()

def verif_answer(prompt, rep_available, error_message):
    print prompt
    rep = raw_input(">>")
    while not rep in rep_available:
        print error_message
        print prompt
        rep = raw_input(">>")
    return rep

def attendre_reponse():
    while not releve.msg_received :
        pass
    releve.msg_received = False
    msg_from_server = open("response", "r").read()
    os.remove("response")
    return msg_from_server

def log_in(already_in = False, user = "", passwd = "", hash_512 = ""):
    global username
    global mdp
    if not already_in :
        print "                                           \r", #Permet d'effacer le message "Connexion au server en cours..."
        if not os.path.exists("log_infos.pkl"): #Aucune info de log n'est enregistree.
            ans = verif_answer("Bienvenue sur [NOM]\nVous pouvez effectuer les actions suivantes : \n\n\t[1]Vous connecter\n\t[2]Vous inscrire",["1","2"],"Veuillez sasir l'une des valeurs entre crochets.")
            if ans == "1":
                while True:
                    username = raw_input("Nom d'utilisateur : ")
                    while not username :
                        print "Le nom d'utilisateur ne doit pas etre vide... Veuillez réessayer !"
                        username = raw_input("Nom d'utilisateur : ")
                    passwd = getpass.getpass("Mot de passe : ")
                    while not passwd :
                        print "Le mot de passe ne doit pas etre vide... Veuillez réessayer !"
                        passwd = getpass.getpass("Mot de passe : ")


                    infos = hashlib.sha512((username+" : "+passwd).encode("utf-8")).hexdigest() #Chiffrage de la combinaison username+" : "+pwd grace au SHA512.
                    connection_server.send(("CONNECT\\"+infos)) #Envoi des infos de connexion.
                    msg_from_server = attendre_reponse()
                    if msg_from_server.split("\\")[0] == 'CONNECT' and msg_from_server.split("\\")[1] == "OK":
                        print 'Identification réussie !' #Le serveur a repondu positivement.
                        f = open("log_infos.pkl", "w")
                        P = pickle.Pickler(f)
                        log_infos = {"user":username, "passwd":passwd, "hash":infos}
                        P.dump(log_infos) #Sauvegarde des infos de log dans un fichier. Ce fichier sera supprime si l'utilisateur demande sa deconnexion.
                        f.close()
                        mdp = passwd
                        get_backup() #Recuperation de la sauvegarde.
                        try:
                            os.mkdir(username) #Creation des dossiers necessaires au stockage des messages etc...
                            os.mkdir(username+os.sep+"messages")
                        except:
                            pass
                        break
                    else :
                        #Le serveur a refuse l'authentification.
                        print "L'authentification à echouée... Veuillez réessayer."
            elif ans == "2":
                register()
                log_in()
        else: #Des donnees de connexion ont ete trouvees.
            f = open("log_infos.pkl","r")
            U = pickle.Unpickler(f)
            datas = U.load()
            f.close()
            print "Données de connection trouvées . Tentative de connection avec les données de "+datas["user"]
            log_in(already_in = True, user = datas["user"], passwd = datas["passwd"], hash_512 = datas["hash"])
    else:
        connection_server.send(("CONNECT\\"+hash_512))
        msg_from_server = attendre_reponse()
        if msg_from_server.split("\\")[0] == 'CONNECT' and msg_from_server.split("\\")[1] == "OK":
            print "Identification réussie !"
            username = user
            mdp = passwd
        else :
            print "Les identifiants enregistrés semblent etre incorrects. Merci de saisir vos identifiants ci dessous."
            os.remove("log_infos.pkl")
            log_in()

def trier_conv(fichier):
    conv = open(fichier,"r").read()
    messages = conv.split("\n")[:len(conv.split("\n"))-1]
    messages.sort()
    conv = open(fichier,"w")
    conv.write("\n".join(messages))
    conv.write("\n")
    conv.close()

def decrypter_conv(fichier, pwd, dest):
    #print "Params : \n\t-fichier : "+fichier+"\n\t-pwd : "+pwd+"\n\t-dest : "+dest
    f = open(fichier,"r")
    msg = f.read()
    f.close()
    passwdf = open(pwd, "r")
    passwd = passwdf.read()
    passwdf.close()
    msg = msg.split("\n")
    decrypted = []
    for x in msg:
        if not x=="" or x == " ":
            xsplit = x.split("]")
            msg_decrypted = ucrpt.uncrypt_message("]".join(xsplit[1:]), passwd)
            decrypted.append("]".join([xsplit[0],msg_decrypted]))

    s = open(dest,'a')
    s.write("\n".join(decrypted)+"\n")
    s.close()
    os.remove(fichier)
    while os.path.exists(fichier):
        os.remove(fichier)

def inbox(already_in = False):
    global sender
    connection_server.send(("GET\\unreaded"))
    msg_from_server = attendre_reponse()
    if msg_from_server.split("\\")[0] == "GIVE" and msg_from_server.split("\\")[1] == "unreaded":
        nbr_convs = int(msg_from_server.split("\\")[2])
    if nbr_convs:
        for x in range(nbr_convs):
            connection_server.send(("GET\\unreaded\\"+str(x)))
            msg_from_server = attendre_reponse()
            if msg_from_server.split("\\")[0]=="KEY":
                try:
                    os.mkdir(username+os.sep+"keys")
                except:
                    pass
                f = open(username+os.sep+"keys"+os.sep+msg_from_server.split("\\")[1]+"key",'w')
                f.write("\\".join(msg_from_server.split("\\")[2:]))
                f.close()
                msg_from_server = attendre_reponse()
            conv = open(username+os.sep+"messages"+os.sep+msg_from_server.split("\\")[2]+"crypted",'w')
            conv.write("\\".join(msg_from_server.split("\\")[3:]))
            conv.close()
            decrypter_conv(username+os.sep+"messages"+os.sep+msg_from_server.split("\\")[2]+"crypted",username+os.sep+"keys"+os.sep+msg_from_server.split("\\")[2]+"key", username+os.sep+"messages"+os.sep+msg_from_server.split("\\")[2])
            trier_conv(username+os.sep+"messages"+os.sep+msg_from_server.split("\\")[2])
    if not already_in:
        convs = os.listdir(username+os.sep+"messages")
        if len(convs) == 0:
            print "Vous n'avez aucun message. Retour au Menu principal."
            afficher_menu()
            return 0
        menu_text = ""
        menu_text += "\n Veuillez entrer le numéro de la conversation que vous souhaitez visualiser :\n[ 0 ] Retour au menu principal\n"
        rep_available = ["0"]
        for x in range(len(convs)):
            menu_text += "[ "+str(x+1)+" ] "+ convs[x]+"\n"
            rep_available.append(str(x+1))
        menu_text += "\n"
        rep = verif_answer(menu_text,rep_available, "Non pris en charge... Réessayer.")
        if rep == "0":
            afficher_menu()
            return 0
        sender = convs[int(rep)-1]
    print "Voici votre conversation avec "+sender+"\n\n"
    f = open(username+os.sep+"messages"+os.sep+sender,'r')
    disc = f.read()
    f.close()
    for x in disc.split("\n"):
        if x == "":
            continue
        if x.split("]")[0].split("\\")[1] == username:
            print "Vous :", x.split("]")[1]
        else :
            print x.split("]")[0].split("\\")[1],":",x.split(']')[1]
    rep_available = ["r","m"]
    rep = verif_answer("\nTaper r pour répondre, m pour retourner au menu précédent.", rep_available, "Valeur non prise en charge... Veuillez réessayer !")
    if rep == "r":
        envoyer_message(dest = sender)
        inbox(already_in = True)
    else:
        inbox()

def afficher_menu():
    if server_reachable:
        rep_available = ["1","99", "2","99+"]
        menu_text = "\nQue voulez-vous faire ?\n[1] Envoyer un message.\n[2] Accéder a ma boite de réception.\n[99] Quitter l'application.\n[99+] Vous déconnecter et quitter l'application.\n"
        rep = verif_answer(menu_text, rep_available, "Non pris en charge... Réessayer.")
        if rep == "1":
            envoyer_message()
        elif rep == "99" or rep == "99+":
            if rep == "99+":
                os.remove("log_infos.pkl")
                fichier = backup()
                shutil.rmtree(username)
            releve.running = False
            connection_server.send("ASKQUITTING")
            releve.join()
            sys.exit()
        elif rep == "2":
            inbox()

def envoyer_message(dest = None):

    if not dest:
        connection_server.send(("GET\\friends"))
        msg_from_server = attendre_reponse()
        if msg_from_server == "GET\\friends\\REFUSED":
            print "Erreur lors de la récuperation de vos amis. Cela est probablement dut à une erreur dans votre connection. Solution proposee : rédemarer l'application et se reconnecter."
        else:
            menu_text = ""
            menu_text += "\nVoici la liste de vos amis. Tapez leur numéro pour leur envoyer un message.\n[ 0 ] Retour au menu principal\n"
            rep_available = ["0", "G"]
            msg_from_server = msg_from_server.split(", ")
            for x in msg_from_server:
                if x == " ":
                    msg_from_server.remove(x)
            for x in range(len(msg_from_server)):
                menu_text += "[ "+str(x+1)+" ] "+msg_from_server[x]+"\n"
                rep_available.append(str(x+1))
            if len(rep_available) == 0 :
                menu_text += "Si tu n'as pas d'amis, prend un curly ;)\n"
            menu_text += "[ + ] Ajouter un ami.\n"
            rep_available.append("+")
            if len(rep_available) > 1 :
                menu_text += "[ - ] Supprimer un ami.\n"
                rep_available.append("-")
            menu_text += "[ G ] Créer un nouveau groupe.\n"
            menu_text += "\n"
            rep = verif_answer(menu_text, rep_available, "Non pris en charge... Réessayer.")
            if rep == "+":
                friend_to_add = raw_input("Quel est le nom d'utilisateur de votre nouvel ami ? \nLaisser vide pour retourner au menu précédent. \n>>")
                if not len(friend_to_add)==0:
                    connection_server.send(("ADD\\friend\\"+friend_to_add))
                    msg_from_server = attendre_reponse()
                    if msg_from_server == "ADD\\friend\\OK":
                        print "Ami ajoute avec succes !"
                    elif msg_from_server == "ADD\\friend\\404":
                        print "Cet ami n'existe pas !"
                    elif msg_from_server == "ADD\\friend\\REFUSED":
                        print "Acces refuse !"
                elif len(friendpass_to_add) == 0:
                    envoyer_message()
                    return 0
            elif rep == "-":
                rep_available = []
                menu_text = ""
                menu_text += "Tapez le numéro de l'ami qui n'en est plus un : \n[ 0 ] Retour en arriere\n"
                for x in range(len(msg_from_server)):
                    menu_text += "[ "+str(x+1)+" ] "+msg_from_server[x]+"\n"
                    rep_available.append(str(x+1))
                rep_available.append("0")
                rep = verif_answer(menu_text, rep_available, "Valeur non prise en charge... Réessayez !")
                if rep == "0":
                    envoyer_message()
                    return 0
                connection_server.send(("REMOVE\\friend\\"+msg_from_server[int(rep)-1]))
                msg_from_server = attendre_reponse()
                if msg_from_server == "REMOVE\\friend\\OK":
                    print "Ami supprimé avec succès"
                elif msg_from_server == "REMOVE\\friend\\404":
                    print "Cet ami ne fait pas parti des votres !"
                elif msg_from_server == "REMOVE\\friend\\REFUSED":
                    print "Acces refuse !"
            elif rep == "0":
                afficher_menu()
                return 0
            elif rep == "G":
                nom = raw_input("Donnez un nom à ce nouveau groupe.\nLaissez vide pour annuler et revenir en arriere.\n>>")
                if len(nom)==0:
                    envoyer_message()
                    return 0
                else:
                    friends_to_add = []
                    while True:
                        menu_text = "Entrez le numéro de l'ami à ajouter au groupe.\n[ 0 ] Annuler la création du groupe et retourner au menu précédent.\n"
                        rep_available = ["0"]
                        if not len(friends_to_add) == 0:
                            menu_text += "[ - ] Retirer des amis déjà ajouté.\n"
                            rep_available.append("-")
                        for x in range(len(msg_from_server)):
                            if not msg_from_server[x] in friends_to_add:
                                menu_text += "[ "+str(x+1)+" ] "+msg_from_server[x]+"\n"
                                rep_available.append(str(x+1))
                            else:
                                menu_text += "[ + ] "+msg_from_server[x]+"\n"
                        if len(friends_to_add)>1:
                            menu_text+="[ "+str(len(msg_from_server)+1)+ " ] Valider et créer le groupe.\n"
                            rep_available.append(str(len(msg_from_server)+1))
                        rep = verif_answer(menu_text, rep_available, "Valeur non pris en charge... Réessayer.")
                        if rep == "0":
                            envoyer_message()
                            return 0
                        elif rep == "-":
                            menu_text = "Entrez le numéro de l'ami qui ne doit pas être ajouté au groupe.\n[ 0 ] Annuler et retourner au menu précédent.\n"
                            rep_available = ["0"]
                            for x in range(len(friends_to_add)):
                                menu_text += "[ "+str(x+1)+" ] "+friends_to_add[x]+"\n"
                                rep_available.append(str(x+1))
                            rep = verif_answer(menu_text, rep_available, "Non pris en charge... Réessayer.")
                            friends_to_add.pop(int(rep)-1)
                        elif rep==str(len(msg_from_server)+1):
                            key = r_pass.generate(256)
                            connection_server.send("START\\group\\"+nom+"\\"+key+"\\"+str(len(friends_to_add))+"\\"+"\\".join(friends_to_add))
                            msg_from_server = attendre_reponse()
                            if msg_from_server == "GROUP\\CREATED":
                                print "Groupe créé avec succès."
                                try:
                                    os.mkdir(username+os.sep+"groups")
                                except:
                                    pass
                                f=open(username+os.sep+"groups"+os.sep+nom+".info", "w")
                                f.write("Key="+key+"\nMembers="+", ".join(friends_to_add))
                                f.close()
                                break

                        else:
                            friends_to_add.append(msg_from_server[int(rep)-1])
            else:
                print msg_from_server[int(rep)-1],"selectionne."
                if not os.path.exists(username+os.sep+"messages"+os.sep+msg_from_server[int(rep)-1]):
                    key = r_pass.generate(256)
                    destinataire = msg_from_server[int(rep)-1]
                    try:
                        os.mkdir(username+os.sep+"keys")
                    except:
                        pass
                    f = open(username+os.sep+"keys"+os.sep+destinataire+"key","w")
                    f.write(key)
                    f.close()
                    connection_server.send("START\\s_conv\\"+msg_from_server[int(rep)-1]+"\\"+key)
                    msg_from_server = attendre_reponse()
                    if msg_from_server == "S_CONV\\CREATED":
                        print "Les messages de cette conversation seront chiffrés avec une clé unique."
                    elif msg_from_server == "S_CONV\\REFUSED":
                        print "ACCES REFUSE. Vous allez etre déconnecte."
                        return 1
                else :
                    destinataire = msg_from_server[int(rep)-1]
                    f = open(username+os.sep+"keys"+os.sep+destinataire+"key","r")
                    key = f.read()
                    f.close()
                print "Tapez votre message ci dessous et appuyez sur entrée pour l'envoyer.\nLaissez le champ vide pour retrourner en arriere."
                message = raw_input(">>")
                if not len(message) == 0:
                    msg_crypted = crpt.crypt_message(message, key)
                    connection_server.send(("SEND\\"+destinataire+"\\"+msg_crypted))
                    msg_from_server = attendre_reponse()
                    if msg_from_server == "SEND\\OK":
                        prev_conv = ""
                        print "Message envoyé !\n\n"
                        try:
                            f = open(username+os.sep+"messages"+os.sep+destinataire,"r")
                            prev_conv = f.read()
                            f.close()
                        except:
                            pass
                        finally:
                            f = open(username+os.sep+"messages"+os.sep+destinataire,"w")
                            f.write(prev_conv)
                            f.write("["+datetime.datetime.isoformat(datetime.datetime.now())+"\\"+username+"]"+message+"\n")
                            f.close()
                            trier_conv(username+os.sep+"messages"+os.sep+destinataire)
                elif len(message) == 0 :
                    envoyer_message()
                    return 0

                else :
                    print "Le message n'a pas été remis.\n\n"
        afficher_menu()
    else:
        f = open(username+os.sep+"keys"+os.sep+dest+"key","r")
        key = f.read()
        f.close()
        print "Tapez votre message ci dessous et appuyez sur entré pour l'envoyer. Laissez le champ vide pour annuler et retourner à la conversation."
        message = raw_input(">>")
        if not len(message) == 0:
            msg_crypted = crpt.crypt_message(message, key)
            connection_server.send(("SEND\\"+dest+"\\"+msg_crypted))
            msg_from_server = attendre_reponse()
            if msg_from_server == "SEND\\OK":
                prev_conv = ""
                print "Message envoyé !\n\n"
                try:
                    f = open(username+os.sep+"messages"+os.sep+dest,"r")
                    prev_conv = f.read()
                    f.close()
                except:
                    pass
                finally:
                    f = open(username+os.sep+"messages"+os.sep+dest,"w")
                    f.write(prev_conv)
                    f.write("["+datetime.datetime.isoformat(datetime.datetime.now())+"\\"+username+"]"+message+"\n")
                    f.close()
                    trier_conv(username+os.sep+"messages"+os.sep+dest)

            else :
                print "Le message n'a pas été remis.\n\n"
        else:
            return 0

def register():
    username = raw_input("Nom d'utilisateur : ")
    while not username :
        print "Le nom d'utilisateur ne doit pas etre vide... Veuillez réessayer !"
        username = raw_input("Nom d'utilisateur : ")
    passwd = ""
    passwd_conf = "a"
    while not passwd == passwd_conf:
        passwd = getpass.getpass("Mot de passe : ")
        while not passwd :
            print "Le mot de passe ne doit pas etre vide... Veuillez réessayer !"
            passwd = getpass.getpass("Mot de passe : ")
        passwd_conf = getpass.getpass("Confirmation du mot de passe : ")
        while not passwd_conf :
            print "Le mot de passe ne doit pas etre vide... Veuillez réessayer !"
            passwd_conf = getpass.getpass("Confirmation du mot de passe : ")
        if not passwd == passwd_conf:
            print "Les mots de passe ne correspondent pas... Veuillez réessayer !"
    email = raw_input("Email : ")
    while not email:
        print "L'email ne doit pas etre vide... Veuillez réessayer !"
        email = raw_input("Email : ")
    sha = hashlib.sha512((username+" : "+passwd).encode()).hexdigest()
    connection_server.send(("REGISTER\\"+"\\".join([username, sha, email])))
    msg_recu = attendre_reponse()
    if msg_recu == "REGISTER\\OK":
        print "Enregistement reussi !"
    elif msg_recu == "REGISTER\\ERROR":
        print "Something went wrong... Please try again !"
        sys.exit()
    elif msg_recu == "REGISTER\\USERNAME_ALREADY_EXISTS":
        print "Ce nom d'utilisateur est déja pris... Veuillez réessayer !"
        register()
    elif msg_recu == "REGISTER\\EMAIL_ALREADY_USED":
        print "Cette adresse mail à deja été utilisée... Veuillez réessayer !"
        register()

print "Connexion au serveur en cours...\r",

if __name__ == "__main__":

    mainthread = threading.currentThread()
    server_reachable = True
    connection_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection_server.connect((hote, port))

    verrou = threading.RLock()

    releve = Releve()
    releve.start()

    username = ""
    sender = ""
    mdp = ""

    log_in()
    afficher_menu()
