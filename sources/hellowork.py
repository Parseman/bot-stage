def get_offres():
    url = "https://www.hellowork.com/fr-fr/emploi/recherche.html?k=stage%20developpeur&l=ile-de-france"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    offres = []
    for job in soup.select(".offer"):
        offres.append({
            "titre": job.find("h3").text,
            "lien": job.find("a")["href"],
            "source": "HelloWork"
        })
    return offres
