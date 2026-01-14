def get_offres():
    url = "https://fr.indeed.com/jobs?q=stage+developpeur&l=Île-de-France"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    offres = []
    for job in soup.select(".job_seen_beacon"):
        offres.append({
            "titre": job.find("h2").text,
            "lien": "https://fr.indeed.com" + job.find("a")["href"],
            "source": "Indeed"
        })
    return offres
