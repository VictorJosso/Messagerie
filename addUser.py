# -*- coding: utf-8 -*-
"""Code par Victor Josso"""
import pickle
import os
import getpass
import hashlib
import argparse
import sys
import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description="Permet d'ajouter des utilisateurs à la messagerie.")
    parser.add_argument("-u", "--username", help = "Spécifie un nom d'utilisateur.")
    parser.add_argument("-s", "--sha512", help = "Spécifie le hash sha512 correspondant à l'utilisateur")
    parser.add_argument("-e", "--email", help = "Spécifie une adresse email.")
    return  parser.parse_args()


def createPath():
    paths_to_add = ["clients", "clients"+os.sep+"Backups", "clients"+os.sep+"datas", "clients"+os.sep+"convert-tables", "clients"+os.sep+"Keys", "clients"+os.sep+"groups", "clients"+os.sep+"messages", "clients"+os.sep+"groups"+os.sep+"infos", "clients"+os.sep+"groups"+os.sep+"messages","clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"new_groups", "clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"groups_already_joined" ]
    for path in paths_to_add:
        while not os.path.exists(path):
            try:
                os.mkdir(path)
            except OSError as e:
                # path already exist
                pass
            except:
                # something wrong append
                e = sys.exc_info()[0] # get error
                print("Error: {}".format(e))


def createUser(username, email, filename, ip_source, private_key, public_key, verif_code):
    createPath()

    identifiant = str(len(os.listdir("clients/datas")) + 1)
    identifiant = "{}{}".format('0' * (10 - len(identifiant)), identifiant)

    f = open("clients"+os.sep+"datas"+os.sep+filename, 'w')
    f.write("username = " + username + "\n")
    f.write("email = " + email + "\n")
    f.write("email_verified = False\n")
    f.write("id = " + identifiant + "\n")
    f.write("friends =  \n")
    f.write("joined = "+datetime.datetime.isoformat(datetime.datetime.now())+"\n")
    f.write("Creation_IP = "+ip_source+"\n")
    f.write("verif_code_email = "+str(verif_code))
    f.close()

    try:
        f = open("clients"+os.sep+"convert-tables"+os.sep+"users", "a+")
    except IOError:
        f = open("clients"+os.sep+"convert-tables"+os.sep+"users", "w")
    f.write(username + "\n")
    f.close()

    try:
        f = open("clients"+os.sep+"convert-tables"+os.sep+"mails", "a+")
    except IOError:
        f = open("clients"+os.sep+"convert-tables"+os.sep+"mails", "w")
    f.write(email + "\n")
    f.close()

    os.mkdir("clients"+os.sep+"messages"+os.sep+"" + username)
    os.mkdir("clients"+os.sep+"Backups"+os.sep+"" + username)
    os.mkdir("clients"+os.sep+"Keys"+os.sep+"" + username)
    os.mkdir("clients"+os.sep+"groups"+os.sep+"infos"+os.sep+"" + username)
    os.mkdir("clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"" + username)
    os.mkdir("clients"+os.sep+"datas"+os.sep+filename+"-datas")

    try:
        f = open("clients"+os.sep+"convert-tables"+os.sep+"users_ids","r")
    except IOError :
        f = open("clients"+os.sep+"convert-tables"+os.sep+"users_ids","w")
        f.close()
        f = open("clients"+os.sep+"convert-tables"+os.sep+"users_ids","r")
    except Error as error:
        # something wrong append
        e = sys.exc_info()[0] # get error
        print("Error: {}, {}".format(e, error))
    u = pickle.Unpickler(f)
    try:
        table = u.load()
    except:
        table = {}
    f.close()
    table[username] = identifiant
    f = open("clients"+os.sep+"convert-tables"+os.sep+"users_ids", "w")
    p = pickle.Pickler(f)
    p.dump(table)
    f.close()

    f = open("clients"+os.sep+"datas"+os.sep+filename+"-datas"+os.sep+"RSAPrivateKey.key", "w")
    f.write(private_key)
    f.close()

    try:
        f = open("clients"+os.sep+"convert-tables"+os.sep+"username_to_publicKey","r")
    except IOError :
        f = open("clients"+os.sep+"convert-tables"+os.sep+"username_to_publicKey","w")
        f.close()
        f = open("clients"+os.sep+"convert-tables"+os.sep+"username_to_publicKey","r")
    except Error as error:
        # something wrong append
        e = sys.exc_info()[0] # get error
        print("Error: {}, {}".format(e, error))
    u = pickle.Unpickler(f)
    try:
        table = u.load()
    except:
        table = {}
    f.close()
    table[username] = public_key
    f = open("clients"+os.sep+"convert-tables"+os.sep+"username_to_publicKey", "w")
    p = pickle.Pickler(f)
    p.dump(table)
    f.close()

    try:
        f = open("clients"+os.sep+"convert-tables"+os.sep+"username_to_config_folder","r")
    except IOError :
        f = open("clients"+os.sep+"convert-tables"+os.sep+"username_to_config_folder","w")
        f.close()
        f = open("clients"+os.sep+"convert-tables"+os.sep+"username_to_config_folder","r")

    u = pickle.Unpickler(f)
    try:
        table = u.load()
    except:
        table = {}
    f.close()

    table[username] = os.path.join("clients", "datas", filename+"-datas")
    f = open("clients"+os.sep+"convert-tables"+os.sep+"username_to_config_folder", "w")
    p = pickle.Pickler(f)
    p.dump(table)
    f.close()

if __name__ == "__main__":
    args = parse_arguments()

    createUser(args.username, args.email, args.sha512)
