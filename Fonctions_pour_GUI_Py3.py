# -*- coding: utf-8 -*-

import socket
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
import random
import argparse
from Crypto.PublicKey import RSA 
import getpass
from win10toast import ToastNotifier

import Crypt as crpt
import Uncrypt as ucrpt
import generate_random_passwords as r_pass



def initialise_connection():
	"""
	Cette fonction initialise la connection avec le serveur. Elle renvoie un objet "Connection" qui est en charge de cette liaison avec le serveur.
	Elle doit être appellée au début du programme. Si ce fichier est le fichier principal, alors le lancement est automatique.
	Si la connection n'a pas pu s'effectuer, elle renvoie un code d'erreur (1). Dans ce cas, permettre à l'utilisateur une consultation des messages deja téléchargés.
	"""
	hote = "josso.fr"
	port = 26281
	connection_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		connection_server.connect((hote, port))
	except:
		return 1
	return connection_server

class Connection(threading.Thread):

	"""
	Cette classe gère la connection avec le serveur et permet de donner la parole aux fonctions.
	Principe de fonctionnement pour pouvoir parler avec le serveur :

	1 - Demander un ticket auprès de la méthode 'ask_for_ticket()'
	2 - Modifier la valeur qui correspond au ticket dans le dictionnaire 'requests'
	3 - Demander l'envoi du message avec la methode 'ask_for_send()', en passant en argument le ticket
	4 - Recuperer la réponse du serveur avec la fonction 'attendre_reponse()', en passant en argument le ticket

	Exemple : 

	connection = Connection
	ticket = connection.ask_for_ticket()
	connection.requests[ticket] = "VotreMessage"
	connection.ask_for_send(ticket)
	reponse_du_serveur = attendre_reponse(ticket)
	"""

	def __init__(self, connection):
		threading.Thread.__init__(self)
		self.msg = str()
		self.next_msg = str()
		self.requests = {}
		self.__requests_to_acces = []
		self.__connection = connection
		self.answers = {}
		self.test = 1
		self.logged_in = False
		self.started = True

	def ask_for_ticket(self):
		self.ticket = int("".join([str(random.randint(0, 9)) for x in range(5)]))
		if not self.ticket in list(self.requests.keys()):
			self.requests[self.ticket] = str()
			self.answers[self.ticket] = str()
			return self.ticket

	def __envoyer(self, message):
		self.__connection.send((message + chr(23)).encode("utf-8"))
		return self._inbox()

	def ask_for_send(self, ticket):
		if ticket in list(self.requests.keys()):
			self.__requests_to_acces.append(ticket)
			return 0
		else:
			raise ValueError("No ticket {} found in requests. Please use the ask_for_ticket() function to get a valid ticket.".format(ticket))

	def run(self):
		while self.started:
			if self.test:
				self.test = 0 
			if not len(self.__requests_to_acces) == 0:
				self.answers[self.__requests_to_acces[0]] = self.__envoyer(self.requests[self.__requests_to_acces[0]])
				self.requests.pop(self.__requests_to_acces[0])
				self.__requests_to_acces.pop(0)
			else:
				if self.logged_in:
					try:
						receptionner_messages(self, self.__connection)
					except Exception as e :
						if not self.started:
							pass
						else:
							raise e
				else:
					pass

	def _inbox(self):
		self.msg = ''
		self.msg += self.next_msg
		while self.msg == '' and not chr(23) in self.msg.strip():
			try:
				self.msg += self.__connection.recv(33554432).decode("utf-8")
			except Exception as e:
				# --- AVERTIR L'UTILISATEUR AVEC UNE POPUP ET FERMER L'APPLICATION ---
				pass

		if not self.msg == "":
			self.next_msg = self.msg[self.msg.index(chr(23))+1:]
			self.msg = self.msg[:self.msg.index(chr(23))]
			self.msg = self.msg.strip()

			if self.msg == "SERVER\\SHUTDOWN":
				self.__connection.send(("OK"+chr(23)).encode("utf-8"))
				# --- AVERTIR L'UTILISATEUR AVEC UNE POPUP ET FERMER L'APPLICATION ---
				pass
			elif self.msg.split("\\")[0] == "ERROR":
				# --- AVERTIR L'UTILISATEUR AVEC UNE POPUP ET FERMER L'APPLICATION ---
				pass
			else:
				return self.msg
		else:
			return None

	def quitter(self):

		"""
		Appeler cette fonction ferme la connection avec le serveur et demande à l'instance de la classe Connection d'arrêter le relevé
		Pour terminer le programme, utiliser la méthode 'join()' sur le thread. Exemple : connection.join()
		"""

		self.started = False
		self.__connection.close()

def receptionner_messages(acces, connection):

	"""
	Cette fonction permet de relever le courrier de l'utilisateur. Elle ne doit jamais être appelée par le programmeur. 
	Le seul moyen pour cette fonction d'être executée est d'être appellée par une instance de la classe Connection.
	"""
	toaster = ToastNotifier()
	connection.send("GET\\unreaded\\s_conv"+chr(23))
	msg_from_server = acces._inbox()
	if msg_from_server == None:
		return None
	elif msg_from_server.split("\\")[0] == "GIVE" and msg_from_server.split("\\")[1] == "unreaded":
		nbr_convs = int(msg_from_server.split("\\")[3])
	if nbr_convs:
		for x in range(nbr_convs):
			connection.send(("GET\\unreaded\\s_conv\\"+str(x)+chr(23)))
			msg_from_server = acces._inbox()
			if msg_from_server == None:
				return None
			elif msg_from_server.split("\\")[0]=="KEY":
				verif_path(username+os.sep+"keys", folder = True)
				f = open(username+os.sep+"keys"+os.sep+msg_from_server.split("\\")[1]+"key",'w')
				f.write("\\".join(msg_from_server.split("\\")[2:]))
				f.close()
				msg_from_server = acces._inbox()
				if msg_from_server == None:
					return None
			verif_path(os.path.join(username, 'messages'), folder = True)
			conv = open(username+os.sep+"messages"+os.sep+msg_from_server.split("\\")[3]+"crypted",'w')
			conv.write("\\".join(msg_from_server.split("\\")[4:]))
			conv.close()
			decrypted = decrypter_conv(username+os.sep+"messages"+os.sep+msg_from_server.split("\\")[3]+"crypted",username+os.sep+"keys"+os.sep+msg_from_server.split("\\")[3]+"key", username+os.sep+"messages"+os.sep+msg_from_server.split("\\")[3])
			trier_conv(username+os.sep+"messages"+os.sep+msg_from_server.split("\\")[3])
			result = toaster.show_toast(msg_from_server.split("\\")[3], "\n".join(["]".join(x.split("]")[1:]) for x in decrypted.split("\n")]), duration = 10, threaded = True)
	#Recuperation des groupes
	connection.send("GET\\unreaded\\group"+chr(23))
	msg_from_server = acces._inbox()
	if msg_from_server == None:
		return None
	if msg_from_server.split("\\")[0] == "GIVE" and msg_from_server.split("\\")[1] == "unreaded":
		nbr_convs = int(msg_from_server.split("\\")[3])
		verif_path(username+os.sep+"datas"+os.sep+"groupsids.pkl")
		f = open(username+os.sep+"datas"+os.sep+"groupsids.pkl","r")
		Upckl = pickle.Unpickler(f)
		try:
			id_to_group = Upckl.load()
		except:
			id_to_group = {}
		f.close()
	if nbr_convs:
		for x in range(nbr_convs):
			i = 0
			connection.send("GET\\unreaded\\group\\"+str(x)+chr(23))
			msg_from_server = acces._inbox()
			if msg_from_server == None:
				return None
			if msg_from_server.split("\\")[0]=="INFOS":
				verif_path(username+os.sep+"groups"+os.sep+"infos"+os.sep+msg_from_server.split("\\")[1]+".info")
				verif_path(username+os.sep+"groups"+os.sep+"messages", True)
				key_file_name = username+os.sep+"groups"+os.sep+"infos"+os.sep+msg_from_server.split("\\")[1]+".info"
				f = open(key_file_name,'w')
				f.write("\n".join(msg_from_server.split("\\")[2:]))
				f.close()
				id_to_group[msg_from_server.split("\\")[4].split("=")[1]] = msg_from_server.split("\\")[1]
				groupsids_f = open(username+os.sep+"datas"+os.sep+"groupsids.pkl", "w")
				pklgroupsids = pickle.Pickler(groupsids_f)
				pklgroupsids.dump(id_to_group)
				groupsids_f.close()
				msg_from_server = acces._inbox()
				if msg_from_server == None:
					return None
			conv = open(username+os.sep+"groups"+os.sep+"messages"+os.sep+id_to_group[msg_from_server.split("\\")[3]]+"crypted",'w')
			conv.write("\\".join(msg_from_server.split("\\")[4:]))
			conv.close()
			datas_f = open(username+os.sep+"groups"+os.sep+"infos"+os.sep+id_to_group[msg_from_server.split("\\")[3]]+".info", "r")
			datas = datas_f.read().split("\n")
			datas_f.close()
			decrypted = decrypter_conv(username+os.sep+"groups"+os.sep+"messages"+os.sep+id_to_group[msg_from_server.split("\\")[3]]+"crypted","=".join(datas[0].split("=")[1:]), username+os.sep+"groups"+os.sep+"messages"+os.sep+id_to_group[msg_from_server.split("\\")[3]])
			trier_conv(username+os.sep+"groups"+os.sep+"messages"+os.sep+id_to_group[msg_from_server.split("\\")[3]])
			result = toaster.show_toast(id_to_group[msg_from_server.split("\\")[3]], "\n".join([ x.split("]")[0].split("\\")[1] + " : " + "]".join(x.split("]")[1:]) for x in decrypted.split("\n")]), duration = 10, threaded = True)

def verif_path(path, folder = False):

	"""
	Cette fonction permet de verifier l'existence d'un fichier. Si il n'existe pas, il sera créé ainsi que tous les sous-dossiers dont il depend.
	Lorsque la valeur du paramètre 'folder' est passée à True, la fonction verifiera l'existance d'un repertoire.
	"""

	if folder:
		path+=os.sep+"creating_file"
	if not os.path.exists(path):
		original_path = os.getcwd()
		path_to_create = ""
		for x in path.split(os.sep)[:len(path.split(os.sep))-1]:
			path_to_create += x+os.sep
			try:
				os.mkdir(path_to_create)
			except Exception as error:
				pass
		if not folder:
			a = open(path, "w")
			a.close()
	else:
		pass

def find_key_in_dict(dict, phrase):

	"""
	Cette fonction permet de retrouver la clé correspondant a une valeur dans un dictionnaire
	"""

	for cle, val in list(dict.items()):
		if val == phrase:
			return cle
	return None

def zipdirectory(filezip, pathzip):
	
	"""
	Cette fonction compresse un dossier en archive ZIP.
	Les paramètres sont les suivants :

		- filezip : Le fichier ZIP à créer
		- pathzip : Le dossier à compresser
	"""

	lenpathparent = len(pathzip)+1
	def _zipdirectory(zfile, path):
		for i in glob.glob(path+'/*'):
			if os.path.isdir(i): _zipdirectory(zfile, i )
			else:
				zfile.write(i, i[lenpathparent:])
	zfile = zipfile.ZipFile(filezip,'w',compression=zipfile.ZIP_DEFLATED)
	_zipdirectory(zfile, pathzip)
	zfile.close()

def attendre_reponse(ticket):

	"""
	Cette fonction est utilisée pour récuperer la reponse donée par le serveur pour un ticket.
	Pour savoir comment obtenir un ticket, se référer à la documentation de la classe 'Connection'
	"""

	while connection_server.answers[ticket] == "":
		pass
	return connection_server.answers[ticket]

def backup():

	"""
	Cette fonction crée une archive chiffrée du dossier personnel de l'utilisateur et l'envoie au serveur.
	Elle est utile pour permettre au client de se déconnecter de l'application sans pour autant perdre ses données.
	On pourrait également appeler cette fonction à intervalle de temps régulier afin d'assurer les donées du client.
	"""

	global username
	global mdp
	zipdirectory("backup.zip", username)
	backup_crpt = crpt.crypt("backup.zip", mdp)
	bkp_file = open(backup_crpt, 'rb')
	msg_to_send = "BACKUP\\"+binascii.hexlify(bkp_file.read())
	bkp_file.close()
	# --- AFFICHER UNE ANIMATION D'ATTENTE ET INFORMER : SAUVEGARDE DES DONNEES EN COURS ---
	ticket = connection_server.ask_for_ticket()
	connection_server.requests[ticket] = msg_to_send
	connection_server.ask_for_send(ticket)
	msg_from_server = attendre_reponse(ticket)
	if msg_from_server == "BACKUP\\OK":
		# --- AFFICHER A L'ECRAN : ENVOI DE LA SAUVEGARDE REUSSI ---
		os.remove(backup_crpt)
		with open("bkp_sended.txt", "a") as f:
			f.write(msg_to_send)
		return backup_crpt
	else:
		# --- AVERTIR L'UTILISATEUR AVEC UNE POPUP ET FERMER L'APPLICATION ---
		return "ERROR"

def dezip(filezip, pathdst = ''):

	"""
	Cette fonction décompresse une archive ZIP.
	Les paramètres sont les suivants:

		- filezip : chemin d'accès (relatif ou non) de l'archive à décompresser
		- pathdst (optionnel) : Permet de spécifier un repertoire de destination. Par default, décompresse dans le repertoire courant.
	"""

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
	global private_key

	ticket = connection_server.ask_for_ticket()
	connection_server.requests[ticket] = "GET\\backup"
	connection_server.ask_for_send(ticket)
	msg_from_server = attendre_reponse(ticket)
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
		ticket_2 = connection_server.ask_for_ticket()
		connection_server.requests[ticket_2] = "GET\\private_key"
		connection_server.ask_for_send(ticket_2)
		msg_from_server = attendre_reponse(ticket_2)
		private_key = ucrpt.uncrypt_message("\\".join(msg_from_server.split("\\")[2:]), mdp)
		try:
			os.mkdir(username)
		except:
			pass
		f = open(username+os.sep+"RSAPrivateKey.key", "w")
		f.write(private_key)
		private_key = RSA.importKey(private_key)
		f.close()
	elif msg_from_server.split("\\") == "GET\\REFUSED":
		# --- AVERTIR L'UTILISATEUR AVEC UNE POPUP ET FERMER L'APPLICATION ---
		os.remove("log_infos.pkl")
		sys.exit()

def log_in(user, passwd):

	"""
	Cette fonction permet d'identifier le client auprès du serveur.
	Elle doit être appelée à chaque fois que la connection entre client et serveur est établie.
	Elle nécessite de demander à l'utilisateur son identifiant et son mot de passe au préalable.
	Lorsque la connection est un succès, elle enregistre les données au format pickle dans le fichier 'log_infos.pkl'.
	Les données enregistrées sont {"user":username, "passwd":password, "hash":user&password hashés avec sha512}

	///// ATTENTION \\\\\
	Pernser à vérifier que des données de connection ne sont pas deja enregistrées avant de les demander à l'utilisateur. 
	Cette fonction ne le verfie pas.
	"""

	global username
	global mdp

	infos = hashlib.sha512((user+" : "+passwd).encode("utf-8")).hexdigest()
	acces = connection_server.ask_for_ticket()
	connection_server.requests[acces] = "CONNECT\\"+user+"\\"+infos
	connection_server.ask_for_send(acces)
	msg_from_server = attendre_reponse(acces)
	if msg_from_server.split("\\")[0] == 'CONNECT' and msg_from_server.split("\\")[1] == "OK":
		# --- Connection reussie, passer a l'ecran suivant ---
		username = user
		mdp = passwd
		connection_server.logged_in = True
		f = open("log_infos.pkl", "w")
		P = pickle.Pickler(f)
		log_infos = {"user":username, "passwd":passwd, "hash":infos}
		P.dump(log_infos) #Sauvegarde des infos de log dans un fichier. Ce fichier sera supprime si l'utilisateur demande sa deconnexion.
		f.close()
		return 0

	elif msg_from_server.split("\\")[0] == 'CONNECT' and msg_from_server.split("\\")[1] == "CONFIRM_EMAIL":
		while True:
			# --- DEMANDER A L'UTILISATEUR DE SAISIR LE CODE DE VERIFICATION ---
			code = "" # --- Renvoyer le code de verification saisi par l'utilisateur dans cette variable ---
			acces = connection_server.ask_for_ticket()
			connection_server.requests[acces] = "VERIF_MAIL\\"+infos+"\\"+str(code)
			connection_server.ask_for_send(acces)
			msg_from_server = attendre_reponse(acces)
			if msg_from_server == "VERIF_MAIL\\VERIFIED":
				# --- INFORMER QUE LE CODE EST BON ET QUE SON COMPTE A ETE VALIDE. ATTENDRE CONFIRMATION
				# DE L'UTILISATEUR ET RENDRE LA MAIN A LA FONCTION ---

				log_in(user, passwd)
				break
			elif msg_from_server == "VERIF_MAIL\\INVALID":
				# --- INFORMER L'UTILISATEUR QUE LE CODE SAISI EST INVALIDE ---
				pass
			elif msg_from_server == "VERIF_MAIL\\UNABLE":
				# --- INFORMER L'UTILISATEUR QU'UNE ERREUR S'EST PRODUITE ET L'INVITER A ESSAYER A NOUVEAU ---
				pass

	else:
		#Erreur, avertir l'utilisateur et lui demander de recommencer
		return 1

def register(usr, passwd, mail):

	"""
	Cette fonction permet de créer un compte sur le serveur de messagerie.
	La fonction prend 3 paramètres : 

		- usr : le nom d'utilisateur souhaité
		- passwd : le mot de passe du compte
		- mail : l'adresse mail de l'utilisateur
	"""

	sha = hashlib.sha512((usr+" : "+passwd).encode()).hexdigest()
	key = RSA.generate(2048)
	public_key = key.publickey()
	key_to_send = crpt.crypt_message(key.exportKey(format='PEM'), passwd)
	acces = connection_server.ask_for_ticket()
	connection_server.requests[acces] = "REGISTER\\"+"\\".join([usr, sha, mail, key_to_send, "\\".join(public_key.exportKey().split("\n"))])
	connection_server.ask_for_send(acces)
	msg_from_server = attendre_reponse(acces)
	if msg_from_server == "REGISTER\\OK":
		# --- Avertir l'utilisateur et lui proposer de se connecter ---
		pass
	elif msg_from_server == "REGISTER\\ERROR":
		# --- Avertir l'utilisateur et quitter l'application ---
		pass
	elif msg_from_server == "REGISTER\\USERNAME_ALREADY_EXISTS":
		# --- Avertir l'utilisateur que ce nom d'utilisateur est deja pris et lui proposer de recommencer avec les autres cases préremplies ---
		pass
	elif msg_from_server == "REGISTER\\EMAIL_ALREADY_USED":
		# --- Avertir l'utilisateur que ce mail est deja utilise et lui proposer de recommencer avec les autres cases préremplies ---
		pass

def trier_conv(fichier):

	"""
	Cette fonction trie les conversations selon la date d'envoi des messages.
	"""

	conv = open(fichier,"r").read()
	messages = conv.split("\n")[:len(conv.split("\n"))-1]
	messages.sort()
	conv = open(fichier,"w")
	conv.write("\n".join(messages))
	conv.write("\n")
	conv.close()

def decrypter_conv(fichier, pwd, dest):

	"""
	Cette fonction permet de déchiffrer les messages chiffrés juste téléchargés depuis le serveur.
	Elle est utilisée par la fonction de téléchargement des messages.
	"""

	f = open(fichier,"r")
	msg = f.read()
	f.close()
	if os.path.exists(pwd):
		passwdf = open(pwd, "r")
		passwd = passwdf.read()
		passwdf.close()
	else:
		passwd = pwd
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

	return "\n".join(decrypted)

def envoyer_message(type = str(), dest = str(), message = str()):

	"""
	Cette fonction permet d'envoyer un message. Elle doit terminer d'être codée.
	Elle prend 3 paramètres :

		- type : Deux valeurs possibles, à savoir 'single' ou 'group', correspondant respectivement à une conversation avec une seule personne
		et à une conversation de groupe.
		- dest : le destinataire dans le cas d'une conversation avec une seule personne, le nom du groupe dans le cas d'un groupe.
		- message : le message à envoyer.
	"""
	if type == "single":

		key_file = open(os.path.join(username, "keys", dest+"key"), "r")
		key = key_file.read()
		key_file.close()

		msg = "["+datetime.datetime.isoformat(datetime.datetime.now())+"\\"+username+"]"+crpt.crypt_message(message, key)

		acces = connection_server.ask_for_ticket()
		connection_server.requests[acces] = "SEND\\"+dest+"\\"+msg
		connection_server.ask_for_send(acces)
		msg_from_server = attendre_reponse(acces)

		if msg_from_server == "SEND\\OK":
			# --- LE MESSAGE À ÉTÉ ENVOYÉ, INFORMER L'UTILISATEUR (VIA UN PETIT SIGNE SUR LE MESSAGE, CF WHATSAPP PAR EXEMPLE)
			conv_file = open(os.path.join(username,"messages",dest), "a")
			conv_file.write("["+datetime.datetime.isoformat(datetime.datetime.now())+"\\"+username+"]"+message+"\n")
			conv_file.close()

			trier_conv(os.path.join(username, "messages", dest))

		else :
			# --- LE MESSAGE N'A PAS ETE REMIS. AVERTIR L'UTILISATEUR ---
			pass

	elif type == "group":

		config_file = open(os.path.join(username,"groups", "infos", dest+".info"), "r")
		config = config_file.read()
		config_file.close()

		group_key = config.split("\n")[0].split("=")[1]
		group_members = config.split("\n")[1].split("=")[1].split(", ")
		group_id = config.split('\n')[2].split('=')[1]

		msg = "["+datetime.datetime.isoformat(datetime.datetime.now())+"\\"+username+"]"+crpt.crypt_message(message, group_key)

		acces = connection_server.ask_for_ticket()
		connection_server.requests[acces] = "SEND_GROUP\\"+", ".join(group_members)+"\\"+group_id+"\\"+msg
		connection_server.ask_for_send(acces)
		msg_from_server = attendre_reponse(acces)

		if msg_from_server == "SEND\\OK":
			# --- LE MESSAGE À ÉTÉ ENVOYÉ, INFORMER L'UTILISATEUR (VIA UN PETIT SIGNE SUR LE MESSAGE, CF WHATSAPP PAR EXEMPLE)
			pass
		else :
			# --- LE MESSAGE N'A PAS ETE REMIS. AVERTIR L'UTILISATEUR ---
			pass

		pass
	else:
		raise ValueError("Expected 'single' or 'group', {} found".format(type))

def start_single_conv(dest):

	"""
	Cette fonction permet de demander au serveur d'initialiser une conversation avec l'un des amis du client.
	"""

	key = r_pass.generate(256)
	try:
		os.mkdir(username+os.sep+"keys")
	except:
		pass
	f = open(username+os.sep+"keys"+os.sep+dest+"key","w")
	f.write(key)
	f.close()
	acces = connection_server.ask_for_ticket()
	connection_server.requests[acces] = "START\\s_conv\\"+dest+"\\"+key
	connection_server.ask_for_send(acces)
	msg_from_server = attendre_reponse(acces)
	if msg_from_server == "S_CONV\\CREATED":
		return 0
		# Recuperer l'output et agir en consequence
	elif msg_from_server == "S_CONV\\REFUSED":

		# Acces refuse, avertir l'utilisateur qu'il doit reessayer
		os.remove(username+os.sep+"keys"+os.sep+dest+"key")
	return 1

def get_all_convs():

	"""
	Cette fonction renvoie toutes les conversations de l'utilisateur.
	Elle renvoie une liste, contenant deux dictionnaires, le premier contenant les conversations avec une seule personne, l'autre les groupes.

	Chacun de ces dictionnaires suit la structure suivante :

		{nom de la conversation : [chemin d'accès de la conversation, chemin d'accès du fichier de configuration de la conversation]}

	Elle pourra être utilisée pour la programmation de la GUI afin de ne pas avoir à 
	"""

	single = {}
	groups = {}

	for x in os.listdir(os.path.join(username, "messages")):
		single[x] = [os.path.join(username, "messages", x), os.path.join(username, 'keys', x+"key")]

	for x in os.listdir(os.path.join(username, "groups", "messages")):
		groups[x] = [os.path.join(username, "groups", "messages", x), os.path.join(username, "groups", "infos", x+".info")]

	return [single, groups]

def set_profile_picture(photo_file):

	"""
	Permet de définir une photo de profil. Donner en paramètre un chemin d'accès à la photo. Format d'image : PNG. 
	Si ce format n'est pas idéal pour le developpement de la GUI, l'indiquer, ainsi que le format d'image souhaité, dans le DOCSTRING de cette fonction.
	"""

	file = open(photo_file, "rb")
	photo = binascii.hexlify(file.read())
	file.close()

	acces = connection_server.ask_for_ticket()
	connection_server.requests[acces] = "SET\\PROFILE_PICTURE\\"+photo
	connection_server.ask_for_send(acces)
	msg_from_server = attendre_reponse(acces)

	if msg_from_server == "SET\\PROFILE_PICTURE\\OK":
		# --- LA PHOTO DE PROFIL A ETE MISE A JOUR. INFORMER L'UTILISATEUR ET ENREGISTRER LA PHOTO DANS LE DOSSIER PERSONEL DE L'UTILISATEUR, 
		# A L'ENDROIT CHOISI PAR LE DEVELOPPEUR DE L'INTERFACE GRAPHIQUE ---
		return 0

	else:
		# --- LA PHOTO DE PROFIL N'A PAS ETE MISE A JOUR. ---
		return 1



def start_group(name, friends_to_add):

	"""
	Cette fonction permet de demander au serveur d'initialiser une conversation de groupe avec les amis, spécifiés dans le tableau 'friends_to_add'
	"""


	key = r_pass.generate(256)
	friends_to_add.append(username)
	acces = connection_server.ask_for_ticket()
	connection_server.requests[acces] = "START\\group\\"+name+"\\"+key+"\\"+str(len(friends_to_add))+"\\"+"\\".join(friends_to_add)
	connection_server.ask_for_send(acces)
	msg_from_server = attendre_reponse(acces)
	if msg_from_server.split("\\")[:2] == ["GROUP", "CREATED"]:
		# --- Groupe cree avec succes, avertir l'utilisateur ---
		try:
			os.mkdir(username+os.sep+"groups")
		except:
			pass
		try:
			os.mkdir(username+os.sep+"groups"+os.sep+"infos")
		except :
			pass
		f=open(username+os.sep+"groups"+os.sep+"infos"+os.sep+nom+".info", "w")
		f.write("Key="+key+"\nMembers="+", ".join(friends_to_add)+"\nGroup id="+msg_from_server.split("\\")[2])
		f.close()
		return msg_from_server.split("\\")[2]
		#Renvoie l'ID du groupe, attribué par le serveur


#if __name__ == "__main__":
username = ""
sender = ""
mdp = ""
private_key = ""
init = initialise_connection()
if not init == 1:
	connection_server = Connection(init)
	connection_server.start()

else:
	# --- AVERTIR L'UTILISATEUR AVEC UNE POPUP ET AUTORISER LA CONSULTATION DES MESSAGES DEJA STOCKES SUR L'APPAREIL ---
	pass



