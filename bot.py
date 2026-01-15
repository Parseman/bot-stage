import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
from datetime import time
import requests
from bs4 import BeautifulSoup
import sqlite3
from keep_alive import keep_alive

# -----------------------------
# CONFIGURATION
# -----------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1461140319205851281  # Ton salon ID

# Mots-clés obligatoires dans le titre
KEYWORDS = ["développeuse", "développeur", "dev", "informatique", "python", "web", "full stack", "backend", "frontend", "data", "software"]

# Header pour simuler un vrai navigateur (Anti-Bot basique)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
}

# -----------------------------
# INTENTS
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# BASE DE DONNÉES (SQLITE)
# -----------------------------
conn = sqlite3.connect("offres.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS offres (
    lien TEXT PRIMARY KEY
)
""")
conn.commit()

def est_nouvelle(lien):
    """Vérifie si l'offre est déjà en base, sinon l'ajoute."""
    c.execute("SELECT lien FROM offres WHERE lien=?", (lien,))
    if c.fetchone():
        return False
    c.execute("INSERT INTO offres VALUES (?)", (lien,))
    conn.commit()
    return True

# -----------------------------
# FONCTIONS SCRAPING
# -----------------------------
def get_offres_wtj():
    """Scraping Welcome to the Jungle"""
    print("--- Scraping WTJ ---")
    url = "https://www.welcometothejungle.com/fr/jobs?query=stage%20developpeur&aroundQuery=Île-de-France"
    offres = []
    
    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print(f"❌ Erreur WTJ : Status {r.status_code}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        
        # Recherche plus large : tous les liens contenant /jobs/ et /companies/
        # Cela évite de dépendre des classes CSS aléatoires comme 'sc-j4th9j-0'
        for a in soup.find_all('a', href=True):
            href = a['href']
            if "/fr/companies/" in href and "/fr/jobs/" in href:
                titre = a.text.strip()
                # Filtrage basique pour éviter les titres vides ou trop longs (bruit)
                if titre and len(titre) < 150:
                    lien = "https://www.welcometothejungle.com" + href
                    # Éviter les doublons dans la même liste
                    if not any(o['lien'] == lien for o in offres):
                        offres.append({"titre": titre, "lien": lien, "source": "Welcome to the Jungle"})
        
        print(f"✅ WTJ : {len(offres)} offres brutes trouvées")
        return offres

    except Exception as e:
        print(f"❌ Exception WTJ : {e}")
        return []

def get_offres_hellowork():
    """Scraping HelloWork"""
    print("--- Scraping HelloWork ---")
    # L'URL contient déjà les filtres : stage + developpeur + ile-de-france
    url = "https://www.hellowork.com/fr-fr/emploi/recherche.html?k=stage%20developpeur&l=ile-de-france"
    offres = []

    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print(f"❌ Erreur HelloWork : Status {r.status_code}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        
        # HelloWork structure souvent ses titres dans des balises <h3> ou des liens spécifiques
        # On cherche les liens qui ont un attribut title ou une classe liée aux offres
        # Méthode générique : chercher dans la liste des résultats
        
        # Sélecteur commun HelloWork (peut changer, donc on essaie de viser large sur les liens d'offres)
        items = soup.select("ul.cr-results > li")
        
        if not items:
            # Plan B: chercher n'importe quel lien qui ressemble à une offre
            items = soup.select("a[href*='/fr-fr/emplois/']")

        for item in items:
            # Si c'est un LI, on cherche le lien A dedans, sinon c'est déjà un A (Plan B)
            tag_a = item.find("a") if item.name == "li" else item
            
            if tag_a and tag_a.get("href"):
                titre = tag_a.text.strip()
                # Nettoyage du titre (parfois HelloWork met le nom de l'entreprise dedans)
                if not titre:
                    continue
                    
                lien = "https://www.hellowork.com" + tag_a.get("href")
                
                # Vérif doublon liste
                if not any(o['lien'] == lien for o in offres):
                    offres.append({"titre": titre, "lien": lien, "source": "HelloWork"})

        print(f"✅ HelloWork : {len(offres)} offres brutes trouvées")
        return offres

    except Exception as e:
        print(f"❌ Exception HelloWork : {e}")
        return []

# -----------------------------
# FILTRAGE
# -----------------------------
def filtrer(offres):
    """Filtre les offres par mots-clés uniquement."""
    result = []
    for o in offres:
        titre = o["titre"].lower()

        # 1. Vérifier mots-clés (Obligatoire)
        if not any(k in titre for k in KEYWORDS):
            continue
        
        # NOTE : On ne filtre plus la LOCALISATION ni la DURÉE ici.
        # Pourquoi ? Parce que "Stage Python" ne contient pas "Île-de-France" dans le titre.
        # L'URL de recherche fait déjà le travail de localisation.
        
        result.append(o)
    
    print(f"📊 Après filtrage mots-clés : {len(result)} offres retenues")
    return result

# -----------------------------
# ENVOI DISCORD
# -----------------------------
async def envoyer_offres_channel(channel):
    offres = []
    
    # Récupération
    offres += get_offres_wtj()
    offres += get_offres_hellowork()
    
    # Filtrage
    offres_filtrees = filtrer(offres)

    # Vérification base de données (pour ne pas renvoyer les anciennes)
    nouvelles = [o for o in offres_filtrees if est_nouvelle(o["lien"])]
    
    print(f"✨ Nouvelles offres à envoyer : {len(nouvelles)}")

    if not nouvelles:
        await channel.send("Pas de nouvelles offres pour l'instant (mais le script fonctionne !) 🕵️‍♂️")
        return

    # Envoi
    await channel.send(f"**📢 J'ai trouvé {len(nouvelles)} nouvelle(s) offre(s) !**")
    
    for o in nouvelles:
        embed = discord.Embed(
            title=o["titre"],
            url=o["lien"],
            color=0x00ff00
        )
        embed.set_footer(text=f"Source : {o['source']} | Île-de-France")
        await channel.send(embed=embed)

# -----------------------------
# TÂCHE RÉCURRENTE
# -----------------------------
@tasks.loop(time=time(hour=9, minute=0)) # 9h00 du matin c'est mieux que 1h
async def recherche_quotidienne():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        print("⏰ Lancement de la tâche quotidienne...")
        await envoyer_offres_channel(channel)
    else:
        print(f"❌ Channel {CHANNEL_ID} introuvable")

# -----------------------------
# COMMANDES
# -----------------------------
@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")

@bot.command()
async def recherche(ctx):
    """Commande manuelle"""
    await ctx.send("🔍 Je lance la recherche, patiente un instant...")
    await envoyer_offres_channel(ctx.channel)
    await ctx.send("✅ Recherche terminée.")

# -----------------------------
# DÉMARRAGE
# -----------------------------
@bot.event
async def on_ready():
    print(f"🤖 Connecté en tant que {bot.user}")
    print(f"📦 Base de données : connectée")
    print(f"📡 Prêt à scraper !")
    if not recherche_quotidienne.is_running():
        recherche_quotidienne.start()

keep_alive()  # <--- Ajoute cette ligne ici
bot.run(TOKEN)