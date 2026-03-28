from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template
from flask import session , url_for , redirect


app = Flask(__name__)

app.secret_key = "secret_key_admin_2026"  


# Configuration PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:54321@localhost:5432/pfe'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================== Models ==================
class Administrateur(db.Model):
    __tablename__ = 'administrateur'
    id_administrateur = db.Column(db.Integer, primary_key=True)
    nom_administrateur = db.Column(db.String(100), nullable=False)
    nom_utilisateur = db.Column(db.String(100), nullable=False, unique=True)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)


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


class Fichier(db.Model):
    __tablename__ = 'fichier'
    id_fichier = db.Column(db.Integer, primary_key=True)
    nom_fichier = db.Column(db.String(150), nullable=False)
    type_fichier = db.Column(db.String(50))
    taille_fichier = db.Column(db.Integer)
    id_projet = db.Column(db.Integer, db.ForeignKey('projet.id_projet'), nullable=False)

with app.app_context():
    db.create_all()

#--------------------Route dashboard ------------------

@app.route("/dashboard_admin")
def dashboard_admin():
    if "admin_id" not in session:  
        return redirect("/")
    return render_template("dashboard_admin.html")

# ================== Route login / add new ==================
@app.route("/")
def home():
    return render_template("page_administrateur.html")
    
@app.route("/add_admin", methods=["POST"])
def add_admin():
    try:
        print(request.form)
        adminname = request.form.get("admin-name")
        username = request.form.get("user-name")
        password = request.form.get("password")
        email = request.form.get("email")  

        user = Administrateur.query.filter_by(nom_utilisateur=username).first()

        if user:
            # Username existe → check password
            if check_password_hash(user.mot_de_passe, password):
                session["admin_id"] = user.id_administrateur
                session["admin_name"] = user.nom_administrateur
                return jsonify({
                    "status": "success",
                    "message": "Connexion réussie !",
                    "redirect": "/dashboard_admin"
                })
            else:
                return jsonify({"status": "error", "message": "Mot de passe incorrect."})
        else:
            
            hashed_password = generate_password_hash(password)
            new_admin = Administrateur(
                nom_administrateur=adminname,
                nom_utilisateur=username,
                email=email if email else f"{username}@gmail.com",
                mot_de_passe=hashed_password
            )
            db.session.add(new_admin)
            db.session.commit()

            
            session["admin_id"] = new_admin.id_administrateur
            session["admin_name"] = new_admin.nom_administrateur

            return jsonify({
                "status": "success",
                "message": f"Administrateur {username} ajouté et connecté !",
                "redirect": "/dashboard_admin"
            })
    
    except Exception as e:
    
        print("Erreur:", e)
        return jsonify({"status": "error", "message": f"Erreur serveur: {e}"})
    


@app.route("/logout_admin")
def logout_admin():
    session.clear()
    return redirect(url_for('home'))

@app.route("/api/utilisateurs")
def get_utilisateurs():
    users = Administrateur.query.all()
    result = []
    
    for u in users:
        # table utilisateur
        utilisateur = Utilisateur.query.filter_by(nom_utilisateur=u.nom_utilisateur).first()
        
        # count projets 
        nb_projets = 0
        if utilisateur:
            nb_projets = Projet.query.filter_by(
                id_utilisateur_createur=utilisateur.id_utilisateur
            ).count()
        
        result.append({
            "id": u.id_administrateur,
            "name": u.nom_utilisateur,
            "email": u.email,
            "status": "active",
            "projects": nb_projets,  
            "avatar": u.nom_utilisateur[0].upper()
        })
    
    return jsonify(result)


@app.route("/api/supprimer_utilisateur/<int:user_id>", methods=["DELETE"])
def supprimer_utilisateur(user_id):
    try:
        user = Administrateur.query.get(user_id)
        if not user:
            return jsonify({"status": "error", "message": "Utilisateur non trouvé"})
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({"status": "success", "message": f"{user.nom_utilisateur} supprimé"})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    

@app.route("/api/modifier_utilisateur/<int:user_id>", methods=["PUT"])
def modifier_utilisateur(user_id):
    try:
        admin = Administrateur.query.get(user_id)
        if not admin:
            return jsonify({"status": "error", "message": "Utilisateur non trouvé"})
        
        data = request.get_json()
        
        ancien_username = admin.nom_utilisateur
        
        # modifier les infos
        admin.nom_utilisateur = data.get("name", admin.nom_utilisateur)
        admin.email = data.get("email", admin.email)
        
        # modifier aussi dans table utilisateur
        utilisateur = Utilisateur.query.filter_by(
            nom_utilisateur=ancien_username
        ).first()
        
        if utilisateur:
            utilisateur.nom_utilisateur = admin.nom_utilisateur
            utilisateur.email = admin.email
        
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Modifié avec succès"})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})
    


@app.route("/api/projets_utilisateur/<int:user_id>")
def projets_utilisateur(user_id):
    try:
        
        admin = Administrateur.query.get(user_id)
        if not admin:
            return jsonify([])
        
        
        utilisateur = Utilisateur.query.filter_by(
            nom_utilisateur=admin.nom_utilisateur
        ).first()
        
        if not utilisateur:
            return jsonify([])
        
        
        projets = Projet.query.filter_by(
            id_utilisateur_createur=utilisateur.id_utilisateur
        ).all()
        
        return jsonify([{
            "id": p.id_projet,
            "nom": p.nom_projet,
            "categorie": p.categorie or "—",
            "date_debut": str(p.date_debut) if p.date_debut else "—",
            "date_fin": str(p.date_fin) if p.date_fin else "—",
            "budget": str(p.budget) if p.budget else "0"
        } for p in projets])
    
    except Exception :
        return jsonify ([])
    

@app.route("/api/projets")
def get_projets():
    try:
        projets = Projet.query.all()
        result = []
        
        for p in projets:
            
            utilisateur = Utilisateur.query.filter_by(
                id_utilisateur=p.id_utilisateur_createur
            ).first()
            
            
            nb_fichiers = Fichier.query.filter_by(
                id_projet=p.id_projet
            ).count()
            
            result.append({
                "id": p.id_projet,
                "nom": p.nom_projet,
                "categorie": p.categorie or "—",
                "date_debut": str(p.date_debut) if p.date_debut else "—",
                "date_fin": str(p.date_fin) if p.date_fin else "—",
                "budget": str(p.budget) if p.budget else "0",
                "utilisateur": utilisateur.nom_utilisateur if utilisateur else "—",
                "nb_datasets": nb_fichiers
            })
        
        return jsonify(result)
    
    except Exception :
        return jsonify([])


@app.route("/api/stats/projets_par_utilisateur")
def stats_projets_par_utilisateur():
    try:
        users = Administrateur.query.all()
        result = []
        
        for u in users:
            utilisateur = Utilisateur.query.filter_by(
                nom_utilisateur=u.nom_utilisateur
            ).first()
            
            nb_projets = 0
            if utilisateur:
                nb_projets = Projet.query.filter_by(
                    id_utilisateur_createur=utilisateur.id_utilisateur
                ).count()
            
            result.append({
                "username": u.nom_utilisateur,
                "nb_projets": nb_projets
            })
        
        return jsonify(result)
    
    except Exception:
        return jsonify([])
    



@app.route("/api/stats/duree_projets")
def stats_duree_projets():
    try:
        projets = Projet.query.filter(
            Projet.date_debut != None,
            Projet.date_fin != None
        ).all()
        
        result = []
        for p in projets:
            duree = (p.date_fin - p.date_debut).days
            result.append({
                "nom": p.nom_projet,
                "duree": duree  
            })
        
        return jsonify(result)
    
    except Exception:
        return jsonify([])
    



@app.route("/api/activites_recentes")
def activites_recentes():
    try:
        activites = []
        
        
        dernier_user = Utilisateur.query.order_by(
            Utilisateur.id_utilisateur.desc()
        ).first()
        
        if dernier_user:
            activites.append({
                "type": "user",
                "message": f"{dernier_user.nom_utilisateur} vient de créer un compte",
                "titre": "Nouvel utilisateur inscrit",
                "temps": "récent"
            })
        
        
        dernier_fichier = Fichier.query.order_by(
            Fichier.id_fichier.desc()
        ).first()
        
        if dernier_fichier:
            projet = Projet.query.get(dernier_fichier.id_projet)
            createur = None
            if projet:
                createur = Utilisateur.query.get(
                    projet.id_utilisateur_createur
                )
            
            activites.append({
                "type": "dataset",
                "message": f"{createur.nom_utilisateur if createur else '—'} a importé {dernier_fichier.nom_fichier} dans {projet.nom_projet if projet else '—'}",
                "titre": "Dataset importé",
                "temps": "récent"
            })
        
        
        dernier_projet = Projet.query.order_by(
            Projet.id_projet.desc()
        ).first()
        
        if dernier_projet:
            createur = Utilisateur.query.get(
                dernier_projet.id_utilisateur_createur
            )
            activites.append({
                "type": "projet",
                "message": f"{createur.nom_utilisateur if createur else '—'} a créé '{dernier_projet.nom_projet}'",
                "titre": "Nouveau projet créé",
                "temps": "récent"
            })
        
        return jsonify(activites)
    
    except Exception :
        return jsonify([])
    

@app.route("/api/stats/datasets_par_projet")
def stats_datasets_par_projet():
    try:
        projets = Projet.query.all()
        result = []
        
        for p in projets:
            nb_fichiers = Fichier.query.filter_by(
                id_projet=p.id_projet
            ).count()
            
            result.append({
                "nom": p.nom_projet,
                "nb_datasets": nb_fichiers
            })
        
        return jsonify(result)
    
    except Exception:
        return jsonify([])




@app.route("/api/fichiers_projet/<int:project_id>")
def fichiers_projet(project_id):
    try:
        fichiers = Fichier.query.filter_by(id_projet=project_id).all()
        return jsonify([{
            "id": f.id_fichier,
            "nom_fichier": f.nom_fichier,
            "type_fichier": f.type_fichier or "—",
            "taille_fichier": f.taille_fichier or 0
        } for f in fichiers])
    except Exception:
        return jsonify([])
    


@app.route("/api/supprimer_projet/<int:project_id>", methods=["DELETE"])
def supprimer_projet(project_id):
    try:
        
        Fichier.query.filter_by(id_projet=project_id).delete()
        

        projet = Projet.query.get(project_id)
        if not projet:
            return jsonify({"status": "error", "message": "Projet non trouvé"})
        
        db.session.delete(projet)
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Projet supprimé"})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})
    


@app.route("/api/datasets")
def get_datasets():
    try:
        fichiers = Fichier.query.all()
        result = []
        
        for f in fichiers:
            projet = Projet.query.get(f.id_projet)
            result.append({
                "id": f.id_fichier,
                "nom": f.nom_fichier,
                "type": f.type_fichier or "—",
                "taille": f.taille_fichier or 0,
                "projet": projet.nom_projet if projet else "—",
                "id_projet": f.id_projet
            })
        
        return jsonify(result)
    
    except Exception:
        return jsonify([])
    


@app.route("/api/supprimer_dataset/<int:dataset_id>", methods=["DELETE"])
def supprimer_dataset(dataset_id):
    try:
        fichier = Fichier.query.get(dataset_id)
        if not fichier:
            return jsonify({"status": "error", "message": "Dataset non trouvé"})
        
        db.session.delete(fichier)
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Dataset supprimé"})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})
    

@app.route("/api/stats/budget_projets")
def stats_budget_projets():
    try:
        projets = Projet.query.filter(
            Projet.budget != None
        ).all()    
        
        return jsonify([{
            "nom": p.nom_projet,
            "budget": float(p.budget)
        } for p in projets])
    
    except Exception:
        return jsonify([])


@app.route("/api/stats/total_fichiers")
def total_fichiers():
    try:
        total = Fichier.query.count()
        return jsonify({"total": total})
    except Exception:
        return jsonify({"total": 0})
    

@app.route("/api/stats/activite")
def stats_activite():
    try:
        total_users = Utilisateur.query.count()
        
        users_actifs = Utilisateur.query.filter(
            Utilisateur.id_utilisateur.in_(
                db.session.query(Projet.id_utilisateur_createur).distinct()
            )
        ).count()
        
        pourcentage = round((users_actifs / total_users * 100)) if total_users > 0 else 0
        
        return jsonify({"pourcentage": pourcentage})
    except Exception:
        return jsonify({"pourcentage": 0})


@app.route("/api/stats/top5_utilisateurs")
def top5_utilisateurs():
    try:
        from sqlalchemy import func
        result = db.session.query(
            Utilisateur.nom_utilisateur,
            func.count(Projet.id_projet).label('nb_projets')
        ).join(
            Projet, Projet.id_utilisateur_createur == Utilisateur.id_utilisateur
        ).group_by(
            Utilisateur.nom_utilisateur
        ).order_by(
            func.count(Projet.id_projet).desc()
        ).limit(5).all()
        
        return jsonify([{
            "username": r[0],
            "nb_projets": r[1]
        } for r in result])
    except Exception:
        return jsonify([])


@app.route("/api/admin_info")
def admin_info():
    try:
        admin_id = session.get("admin_id")
        admin = Administrateur.query.get(admin_id)
        if not admin:
            return jsonify({"status": "error"})
        return jsonify({
            "nom_administrateur": admin.nom_administrateur,
            "nom_utilisateur": admin.nom_utilisateur,
            
        })
    except Exception:
        return jsonify({})
    


@app.route("/api/modifier_admin_info", methods=["PUT"])
def modifier_admin_info():
    try:
        admin_id = session.get("admin_id")
        admin = Administrateur.query.get(admin_id)
        if not admin:
            return jsonify({"status": "error", "message": "Admin non trouvé"})
        
        data = request.get_json()
        admin.nom_administrateur = data.get("nom_administrateur", admin.nom_administrateur)
        
        db.session.commit()
        
        # update session
        session["admin_name"] = admin.nom_administrateur
        
        return jsonify({"status": "success", "message": "Modifié avec succès"})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/ajouter_utilisateur", methods=["POST"])
def ajouter_utilisateur():
    try:
        data = request.get_json()
        
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        
        
        admin_id = session.get("admin_id")
        admin = Administrateur.query.get(admin_id)
        if admin:
            nom_admin = admin.nom_administrateur
        else:
            return jsonify({"status": "error", "message": "Session expirée, reconnectez-vous"})

        # check doublon
        existing = Administrateur.query.filter_by(
            nom_utilisateur=username
        ).first()
        if existing:
            return jsonify({
                "status": "error", 
                "message": "Nom d'utilisateur déjà existant"
            })

        existing_email = Administrateur.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({
                "status": "error",
                "message": "Email déjà existant"
            })

        
        hashed = generate_password_hash(password)
        new_admin = Administrateur(
            nom_administrateur=nom_admin, 
            nom_utilisateur=username,
            email=email,
            mot_de_passe=hashed
        )
        db.session.add(new_admin)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"{username} ajouté avec succès"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})



@app.route("/api/users_rapport")
def users_rapport():
    try:
        admins = Administrateur.query.all()
        result = []
        
        for a in admins:
            utilisateur = Utilisateur.query.filter_by(
                nom_utilisateur=a.nom_utilisateur
            ).first()
            
            projets_data = []
            if utilisateur:
                projets = Projet.query.filter_by(
                    id_utilisateur_createur=utilisateur.id_utilisateur
                ).all()
                
                for p in projets:
                    nb_datasets = Fichier.query.filter_by(
                        id_projet=p.id_projet
                    ).count()
                    projets_data.append({
                        "nom": p.nom_projet,
                        "nb_datasets": nb_datasets
                    })
            
            result.append({
                "username": a.nom_utilisateur,
                "email": a.email,
                "projets": projets_data
            })
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify([])


if __name__ == "__main__":
    app.run(debug=True)