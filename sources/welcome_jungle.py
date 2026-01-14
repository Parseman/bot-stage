from bs4 import BeautifulSoup
import requests

def get_offres():
    url = "https://www.welcometothejungle.com/fr/jobs?query=stage%20developpeur&aroundQuery=Île-de-France"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    offres = []
    for job in soup.select("a.sc-j4th9j-0"):
        offres.append({
            "titre": job.text.strip(),
            "lien": "https://www.welcometothejungle.com" + job["href"],
            "source": "Welcome to the Jungle"
        })
    return offres
