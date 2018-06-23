# -*- coding: utf-8 -*-

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

expediteur = "verifmail.messagerie@gmail.com"
pwd = '**********'


def envoyer_confirmation(adresse, code, username):
    message = MIMEMultipart()
    message["From"] = expediteur
    message["To"] = adresse
    message["Subject"] = "Verifiez votre Email !"

    text = "Bonjour "+username+",\n\nBienvenue sur notre messagerie. Pour confirmer votre email et pouvoir utiliser nos services, veuillez vous connecter et saisir le code suivant :\n\n\t"+str(code)+"\n\n\nVous avez 7 jours a compter de la creation du compte pour valider votre adresse email, sinon votre compte sera supprime.\nMerci de nous avoir choisi et bonne utilisation !"
    message.attach(MIMEText(text, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(expediteur, pwd)
    text_to_send = message.as_string()
    server.sendmail(expediteur, adresse, text_to_send)
    server.quit()
