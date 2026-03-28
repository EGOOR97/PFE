from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:54321@localhost:5432/pfe'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.secret_key = "secret_key"

# ================= Models =================

class Administrateur(db.Model):
    __tablename__ = 'administrateur'
    id_administrateur = db.Column(db.Integer, primary_key=True)
    nom_administrateur = db.Column(db.String(100))
    nom_utilisateur = db.Column(db.String(100))
    mot_de_passe = db.Column(db.String(255))
    email = db.Column(db.String(150))


class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'
    id_utilisateur = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(100))
    email = db.Column(db.String(150))
    mot_de_passe = db.Column(db.String(255))
    id_administrateur = db.Column(db.Integer)


class Projet(db.Model):
    __tablename__ = 'projet'
    id_projet = db.Column(db.Integer, primary_key=True)
    nom_projet = db.Column(db.String(150), nullable=False)
    id_utilisateur_createur = db.Column(db.Integer, nullable=False)
    categorie = db.Column(db.String(100))
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    budget = db.Column(db.Numeric(15, 2))


# ================= Routes =================

@app.route("/")
def home():
    return render_template("page_d'intro.html")


@app.route("/login")
def login():
    return render_template("login.html")


# ================= Login utilisateur =================

@app.route("/login_user", methods=["POST"])
def login_user():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    # Check utilisateur table
    user = Utilisateur.query.filter_by(nom_utilisateur=username).first()
    if user:
        if check_password_hash(user.mot_de_passe, password) and user.email == email:
            session["user_id"] = user.id_utilisateur
            session["username"] = user.nom_utilisateur
            return jsonify({"status": "success", "redirect": url_for("creation_projet")})
        else:
            return jsonify({"status": "error", "message": "Email ou mot de passe incorrect"})

    # Check admin table
    admin = Administrateur.query.filter_by(nom_utilisateur=username).first()
    if admin:
        if check_password_hash(admin.mot_de_passe, password) and admin.email == email:
            hashed_password = generate_password_hash(password)
            new_user = Utilisateur(
                nom_utilisateur=username,
                email=email,
                mot_de_passe=hashed_password,
                id_administrateur=admin.id_administrateur
            )
            db.session.add(new_user)
            db.session.commit()
            session["user_id"] = new_user.id_utilisateur
            session["username"] = new_user.nom_utilisateur
            return jsonify({"status": "success", "redirect": url_for("creation_projet")})
        else:
            return jsonify({"status": "error", "message": "Email ou mot de passe incorrect (admin)"})

    return jsonify({"status": "error", "message": "Utilisateur non autorisé"})


# ================== Page création projet ==================

@app.route("/creation_projet", methods=["GET", "POST"])
def creation_projet():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]
    username = session.get("username", "")

    if request.method == "POST":
        nom_projet = request.form.get("nom_projet")
        categorie = request.form.get("categorie")
        date_debut = request.form.get("date_debut")
        date_fin = request.form.get("date_fin")
        budget = request.form.get("budget")

        existing_project = Projet.query.filter_by(
            nom_projet=nom_projet,
            id_utilisateur_createur=user_id
        ).first()

        if existing_project:
            return render_template(
                "creation_projet.html",
                username=username,
                message="Ce projet existe déjà."
            )

        new_project = Projet(
            nom_projet=nom_projet,
            categorie=categorie,
            date_debut=datetime.strptime(date_debut, "%Y-%m-%d").date() if date_debut else None,
            date_fin=datetime.strptime(date_fin, "%Y-%m-%d").date() if date_fin else None,
            budget=float(budget) if budget else 0,
            id_utilisateur_createur=user_id,
        )
        db.session.add(new_project)
        db.session.commit()

        session["project_id"] = new_project.id_projet
        session["nom_projet"] = new_project.nom_projet

        # Redirect to Streamlit analytics app with project context as URL params
        import urllib.parse
        streamlit_url = (
            "http://localhost:8501"
            f"?project_id={new_project.id_projet}"
            f"&project_name={urllib.parse.quote(nom_projet)}"
            f"&username={urllib.parse.quote(username)}"
        )
        return redirect(streamlit_url)

    return render_template("creation_projet.html", username=username)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Crée les tables si elles n'existent pas
    app.run(debug=True, port=5001)
