from getpass import getpass
import binascii
import math
import os

def uncrypt(fichier, password):
    f=open(fichier,"rb")
    text = f.read()
    f.close()
    file_type = text.split("\n")[0][21:]
    nbr_zeros = text.split('\n')[1]
    text = "\n".join(text.split("\n")[2:])
    buffer_zeros = ""
    for x in range(int(nbr_zeros)):
        buffer_zeros+="0"
    text = buffer_zeros+bin(int(binascii.hexlify(text), 16))[2:]
    pass_crypt = bin(int(binascii.hexlify(password), 16))[2:]
    texte_dechiffre = ""
    tabl_buffer = []
    toursafaire = len(text)
    for x in range(len(text)):
        bit_t = text[x]
        bit_p = pass_crypt[x%len(pass_crypt)]
        bit_d = str(int(math.fabs(int(bit_t)-int(bit_p))))
        tabl_buffer.append(bit_d)
    texte_dechiffre = hex(int('0b'+"".join(tabl_buffer), 2))
    texte_dechiffre = texte_dechiffre[2:len(texte_dechiffre)-1]
    if len(texte_dechiffre)%2==1:
        texte_dechiffre = "0"+texte_dechiffre
    texte_dechiffre = binascii.unhexlify(texte_dechiffre)
    f = open(fichier, "wb")
    f.write(texte_dechiffre)
    f.close()





def uncrypt_message(message, password):
    text = message
    nbr_zeros = text.split('/')[0]
    text = "/".join(text.split("/")[1:])
    buffer_zeros = ""
    for x in range(int(nbr_zeros)):
        buffer_zeros+="0"
    text = buffer_zeros+bin(int(text, 16))[2:]
    pass_crypt = bin(int(binascii.hexlify(password), 16))[2:]
    texte_dechiffre = ""
    tabl_buffer = []
    toursafaire = len(text)
    for x in range(len(text)):
        bit_t = text[x]
        bit_p = pass_crypt[x%len(pass_crypt)]
        bit_d = str(int(math.fabs(int(bit_t)-int(bit_p))))
        tabl_buffer.append(bit_d)
    texte_dechiffre = hex(int('0b'+"".join(tabl_buffer), 2))
    texte_dechiffre = texte_dechiffre[2:len(texte_dechiffre)-1]
    if len(texte_dechiffre)%2==1:
        texte_dechiffre = "0"+texte_dechiffre
    texte_dechiffre = binascii.unhexlify(texte_dechiffre)
    return texte_dechiffre

def verif_path(path):
    try:
        open(path, 'r')
        return True
    except IOError:
        return False

def setup(path_given = False):
    if not path_given :
        fichier = raw_input("Quel est le chemin d'acces au fichier a decrypter ? > ")
        while not verif_path(fichier):
            print "Ce fichier est introuvable... Veuillez reessayer !"
            fichier = raw_input("Quel est le chemin d'acces au fichier a decrypter ? > ")
        mdp = getpass("Veuillez saisir le mot de passe a utiliser pour dechiffer le document > ")
        while not mdp:
            print "Le mot de passe ne doit pas etre vide... Veuillez reessayer !"
            mdp  = getpass("Veuillez saisir le mot de passe a utiliser pour chiffer le document > ")
        return fichier, mdp
    else:
        mdp = getpass("Veuillez saisir le mot de passe a utiliser pour dechiffer le document > ")
        while not mdp:
            print "Le mot de passe ne doit pas etre vide... Veuillez reessayer !"
            mdp  = getpass("Veuillez saisir le mot de passe a utiliser pour chiffer le document > ")
        return mdp



if __name__ == "__main__":
    fichier, mdp = setup()
    uncrypt(fichier, mdp)
