import sqlite3


def init_db():
    conn = sqlite3.connect("ecole.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eleves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            classe TEXT NOT NULL,
            date_naissane TEXT NOT NULL,
            sexe TEXT NOT NULL,
            profile TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_complet TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            mot_de_passe TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# C'est ici qu'on appelle la fonction, tout à fait à gauche (hors de la fonction)
if __name__ == "__main__":
    init_db()
    print("Base de données et tables créées avec succès !")