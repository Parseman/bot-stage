import sqlite3

conn = sqlite3.connect("offres.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS offres (
    lien TEXT PRIMARY KEY
)
""")

def est_nouvelle(lien):
    c.execute("SELECT lien FROM offres WHERE lien=?", (lien,))
    if c.fetchone():
        return False
    c.execute("INSERT INTO offres VALUES (?)", (lien,))
    conn.commit()
    return True
