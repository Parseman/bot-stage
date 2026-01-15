from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Je suis en vie !"

def run():
    # On récupère le port donné par Render (via la variable d'env), sinon on prend 8080
    port = int(os.environ.get("PORT", 8080))
    # On écoute sur 0.0.0.0 (obligatoire pour Render)
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()