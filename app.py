import os
import sqlite3
from uuid import uuid4
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, session, url_for, request, flash
from datetime import datetime
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "e5aa46e55736147c1d3863aa1d6ca74399f3250846ecafd3e9416e9ebb1ca6ad"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Créer le dossier s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    connect = sqlite3.connect("ecole.db")
    connect.row_factory = sqlite3.Row
    eleves = connect.execute("SELECT * FROM eleves").fetchall()
    connect.close()
    return render_template("index.html", eleves=eleves)

@app.route("/connexion")
def connexion():
     
    return render_template("connexion.html")

@app.route("/traitement_connexion", methods=["GET", "POST"])
def traitement_connexion():
    email= request.form.get("email", "").strip()
    mot_de_passe= request.form.get("mot_de_passe", "").strip()
    if not email or not mot_de_passe:
        flash("Tous les champs sont obligatoires !", "danger")
        return render_template("connexion.html")
    connect = sqlite3.connect("ecole.db")
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    user= cursor.execute(
        "SELECT * FROM users WHERE email= ?",(email,)
    ).fetchone()
    connect.close()
    if user is None:
        flash("Adresse e-mail ou mot de passe incorrect !", "danger")
        return render_template("connexion.html")
    
    hashed_password = user["mot_de_passe"]
    if (not bcrypt.check_password_hash(hashed_password, mot_de_passe)):
        flash("Adresse e-mail ou mot de passe incorrect !", "danger")
        return render_template("connexion.html")
    session["user_id"] = user["id"]
    session["user"] = user["nom_complet"]
    return redirect(url_for("index"))
  
@app.route("/deconnexion")
def deconnexion():
    session.pop("user", None)
    session.pop("user_id", None)
    return redirect(url_for("index"))       
    

@app.route("/inscription")
def inscription():
    return render_template("inscription.html")

@app.route('/traitement_inscription',methods=['GET','POST'])
def traitement_inscription():
    nom_complet = request.form.get("nom_complet", "").strip()
    email = request.form.get("email", "").strip()
    mot_de_passe = request.form.get("mot_de_passe", "")
    mot_de_passe_conf = request.form.get("mot_de_passe_conf", "")

    if not nom_complet or not email or not mot_de_passe or not mot_de_passe_conf:
        flash("Tous les champs sont obligatoires !", "danger")
        return render_template("inscription.html")
    if mot_de_passe != mot_de_passe_conf:
        flash("Les mots de passe ne correspondent pas !", "danger")
        return render_template("inscription.html")

    mot_de_passe_hash = bcrypt.generate_password_hash(mot_de_passe).decode("utf-8")
    connect = sqlite3.connect("ecole.db")
    cursor = connect.cursor()
    email_exists = cursor.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    if email_exists:
        flash("Cet e-mail est déjà utilisé !", "danger")
        return render_template("inscription.html")
    cursor.execute(
        "INSERT INTO users(nom_complet,email,mot_de_passe) VALUES(?,?,?)",
        (nom_complet, email, mot_de_passe_hash),
    )
    connect.commit()
    connect.close()
    flash("Inscription réussie !", "success")
    return redirect(url_for("connexion"))
 
@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("connexion"))

    connect = sqlite3.connect("ecole.db")
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    user = cursor.execute(
        "SELECT id, nom_complet, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    if user is None:
        connect.close()
        session.clear()
        return redirect(url_for("connexion"))

    if request.method == "GET":
        connect.close()
        return render_template("profile.html", user=user)

    nom_complet = request.form.get("nom_complet", "").strip()
    email = request.form.get("email", "").strip()
    mot_de_passe = request.form.get("mot_de_passe", "")
    mot_de_passe_conf = request.form.get("mot_de_passe_conf", "")

    if not nom_complet or not email:
        connect.close()
        flash("Le nom complet et l'e-mail sont obligatoires !", "danger")
        return render_template("profile.html", user=user)

    if mot_de_passe != mot_de_passe_conf:
        connect.close()
        flash("Les mots de passe ne correspondent pas !", "danger")
        return render_template("profile.html", user=user)

    email_exists = cursor.execute(
        "SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id)
    ).fetchone()
    if email_exists:
        connect.close()
        flash("Cet e-mail est déjà utilisé !", "danger")
        return render_template("profile.html", user=user)

    if mot_de_passe:
        mot_de_passe_hash = bcrypt.generate_password_hash(mot_de_passe).decode("utf-8")
        cursor.execute(
            "UPDATE users SET nom_complet = ?, email = ?, mot_de_passe = ? WHERE id = ?",
            (nom_complet, email, mot_de_passe_hash, user_id),
        )
    else:
        cursor.execute(
            "UPDATE users SET nom_complet = ?, email = ? WHERE id = ?",
            (nom_complet, email, user_id),
        )

    connect.commit()
    connect.close()
    session["user"] = nom_complet
    flash("Profil mis à jour avec succès !", "success")
    return redirect(url_for("profile"))
        

@app.route("/ajouter", methods=["GET", "POST"])
def ajouter():
    today=datetime.now().strftime("%Y-%m-%d")
    if session.get("user") is None:
     return redirect(url_for("connexion"))
    else: 
     if request.method== "POST":
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        classe = request.form["classe"]
        date_naissane = request.form["date_naissane"]
        sexe = request.form["sexe"]
        profile = request.files.get("profile")
        if(not nom or not prenom or not classe or not date_naissane or not sexe):
         flash("Tous les champs sont obligatoires !", "danger") 
         return render_template("index.html")
        if date_naissane > today:
            flash("La date de naissance ne peut pas être dans le futur !", "danger")
            return render_template("index.html")
        age= datetime.now().year - datetime.strptime(date_naissane, "%Y-%m-%d").year 
        if age < 6:
         flash("L'élève doit avoir au moins 5 ans !", "danger") 
         return render_template("index.html")
        filename = secure_filename(profile.filename) if profile and profile.filename else ""
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename) if filename else ""
        if profile and filename:
            profile.save(file_path)
        # 3. Insertion dans la base de données ecole.db  
        connect = sqlite3.connect('ecole.db')
        cursor = connect.cursor()
        cursor.execute('INSERT INTO eleves(nom, prenom, classe, date_naissane, sexe, profile) VALUES (?, ?, ?, ?, ?, ?)', (nom, prenom, classe, date_naissane, sexe, filename))
        connect.commit()
        connect.close()
        # flash("Élève et photo ajoutés avec succès !", "success")
        flash("L'élève a été ajouté avec succès !", "success")
        return redirect(url_for("index"))

    return redirect(url_for("index"))


@app.route("/modifier/<int:eleve_id>", methods=["GET", "POST"])
def modifier(eleve_id):
    if session.get("user") is None:
     return redirect(url_for("connexion"))
    else:
        connect = sqlite3.connect("ecole.db")
        connect.row_factory = sqlite3.Row
        eleve = connect.execute(
            "SELECT * FROM eleves WHERE id = ?", (eleve_id,)
        ).fetchone()

        if eleve is None:
            connect.close()
            return "Élève introuvable", 404

        if request.method == "GET":
            connect.close()
            return render_template("form.html", eleve=eleve)

        nom = request.form["nom"]
        prenom = request.form["prenom"]
        classe = request.form["classe"]
        date_naissane = request.form["date_naissane"]
        sexe = request.form["sexe"]
        profile = request.files.get("profile")
        profile_path = eleve["profile"]

        if profile and profile.filename:
            filename = secure_filename(profile.filename)
            profile.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            profile_path = filename

        connect.execute(
            """UPDATE eleves
               SET nom = ?, prenom = ?, classe = ?, date_naissane = ?,
                   sexe = ?, profile = ?
               WHERE id = ?""",
            (nom, prenom, classe, date_naissane, sexe, profile_path, eleve_id),
        )
        connect.commit()
        connect.close()
        flash("Élève modifié avec succès !", "success")
        return redirect(url_for("index"))


@app.route("/supprimer/<int:eleve_id>", methods=["POST"])
def supprimer(eleve_id):
    if session.get("user") is None:
        return redirect(url_for("connexion"))
    else:
        connect = sqlite3.connect("ecole.db")
        connect.execute("DELETE FROM eleves WHERE id = ?", (eleve_id,))
        connect.commit()
        connect.close()
        flash("Élève supprimé avec succès !", "success")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)