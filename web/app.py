"""
web/app.py

Version Web locale du Simulateur Financier Autonome.
Réutilise le moteur financier et le service IA existants.
"""

from __future__ import annotations

import os
import sys
import uuid
import csv
import secrets
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, request, render_template_string, session, Response

RACINE_PROJET = Path(__file__).resolve().parent.parent

if str(RACINE_PROJET) not in sys.path:
    sys.path.insert(0, str(RACINE_PROJET))

from services.calcul_projection import CalculProjection
from services.service_projection import ServiceProjection
from services.service_ia import ServiceIA

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "simulateur-financier-autonome-session-v1-2026",
)

service_ia = ServiceIA()

ADMIN_STATS_USER = os.environ.get(
    "ADMIN_STATS_USER",
    "admin",
)
ADMIN_STATS_PASSWORD = os.environ.get(
    "ADMIN_STATS_PASSWORD",
    "",
)


# --- Statistiques de fréquentation ---
DOSSIER_STATS = RACINE_PROJET / "donnees"
FICHIER_VISITES = DOSSIER_STATS / "statistiques_visites.csv"
ENTETES_VISITES = ["date_utc", "heure_utc", "session", "origine", "appareil", "action", "chemin"]

def _origine_visite():
    referer = (request.referrer or "").lower()
    if "facebook.com" in referer or "fbclid" in request.args: return "Facebook"
    if "google." in referer: return "Google"
    if referer: return "Autre site"
    return "Direct"

def _appareil_visite():
    agent = (request.headers.get("User-Agent") or "").lower()
    if "bot" in agent or "crawler" in agent or "spider" in agent: return "Robot"
    if "android" in agent: return "Android"
    if "iphone" in agent or "ipad" in agent: return "iPhone/iPad"
    if "windows" in agent: return "Windows"
    if "macintosh" in agent or "mac os" in agent: return "Mac"
    if "linux" in agent: return "Linux"
    return "Autre"

def enregistrer_visite(action):
    appareil = _appareil_visite()
    if appareil == "Robot": return
    identifiant = session.get("stat_session")
    if not identifiant:
        identifiant = uuid.uuid4().hex[:12]
        session["stat_session"] = identifiant
    maintenant = datetime.now(timezone.utc)
    DOSSIER_STATS.mkdir(parents=True, exist_ok=True)
    nouveau = not FICHIER_VISITES.exists()
    with FICHIER_VISITES.open("a", newline="", encoding="utf-8-sig") as fichier:
        writer = csv.writer(fichier, delimiter=";")
        if nouveau: writer.writerow(ENTETES_VISITES)
        writer.writerow([maintenant.strftime("%d/%m/%Y"), maintenant.strftime("%H:%M:%S"),
                         identifiant, _origine_visite(), appareil, action, request.path])

def enregistrer_ouverture_unique():
    if not session.get("visite_comptee"):
        enregistrer_visite("Ouverture")
        session["visite_comptee"] = True

def _identifiants_statistiques_valides():
    autorisation = request.authorization

    if not ADMIN_STATS_PASSWORD:
        return False

    if not autorisation:
        return False

    utilisateur_valide = secrets.compare_digest(
        autorisation.username or "",
        ADMIN_STATS_USER,
    )
    mot_de_passe_valide = secrets.compare_digest(
        autorisation.password or "",
        ADMIN_STATS_PASSWORD,
    )

    return utilisateur_valide and mot_de_passe_valide


@app.route("/statistiques/telecharger")
def telecharger_statistiques():
    if not _identifiants_statistiques_valides():
        return Response(
            "Accès administrateur requis.",
            status=401,
            headers={
                "WWW-Authenticate": (
                    'Basic realm="Statistiques administrateur"'
                )
            },
        )

    contenu = (
        FICHIER_VISITES.read_text(
            encoding="utf-8-sig"
        )
        if FICHIER_VISITES.exists()
        else ";".join(ENTETES_VISITES) + "\n"
    )

    return Response(
        contenu,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                "attachment; "
                "filename=statistiques_visites.csv"
            )
        },
    )



ADMIN_STATISTIQUES_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Statistiques administrateur</title>
<style>
:root{--fond:#020813;--panneau:#071321;--cyan:#37e8ff;--texte:#f5fbff}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:var(--fond);color:var(--texte);font-family:"Segoe UI",Arial,sans-serif}
.entete{padding:18px 30px;background:#1d2633;border-bottom:1px solid #27384b;display:flex;justify-content:space-between;align-items:center}
.entete h1{margin:0;color:#48bfff;font-size:20px}
.actions{display:flex;gap:10px}
.bouton{padding:9px 16px;border:1px solid var(--cyan);border-radius:5px;color:var(--cyan);text-decoration:none;font-size:12px;font-weight:700;background:#071728}
.page{width:min(1450px,96vw);margin:0 auto;padding:25px 0}
.resume{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px}
.carte{background:var(--panneau);border:1px solid #17384c;border-radius:8px;padding:18px;text-align:center}
.carte strong{display:block;color:var(--cyan);font-size:28px;margin-bottom:5px}
.carte span{color:#b9d9ed;font-size:12px}
.tableau{overflow:auto;border:1px solid #17384c;border-radius:8px;background:var(--panneau)}
table{width:100%;border-collapse:collapse;min-width:950px}
th{background:#0b2032;color:var(--cyan);text-align:left;padding:12px 10px;font-size:12px}
td{padding:10px;border-top:1px solid #132d3d;font-size:12px;white-space:nowrap}
.vide{text-align:center;padding:40px;color:#7da0ad}
@media(max-width:700px){.resume{grid-template-columns:1fr}.entete{align-items:flex-start;gap:12px;flex-direction:column}}
</style>
</head>
<body>
<header class="entete">
<h1>STATISTIQUES DE FRÉQUENTATION</h1>
<div class="actions">
<a class="bouton" href="/statistiques/telecharger">TÉLÉCHARGER CSV</a>
<a class="bouton" href="/">RETOUR COCKPIT</a>
</div>
</header>
<main class="page">
<div class="resume">
<div class="carte"><strong>{{ total_lignes }}</strong><span>ÉVÉNEMENTS</span></div>
<div class="carte"><strong>{{ total_sessions }}</strong><span>VISITEURS / SESSIONS</span></div>
<div class="carte"><strong>{{ total_simulations }}</strong><span>SIMULATIONS</span></div>
</div>
{% if lignes %}
<div class="tableau">
<table>
<thead><tr><th>Date UTC</th><th>Heure UTC</th><th>Session</th><th>Origine</th><th>Appareil</th><th>Action</th><th>Chemin</th></tr></thead>
<tbody>
{% for ligne in lignes %}
<tr>
<td>{{ ligne.date_utc }}</td><td>{{ ligne.heure_utc }}</td><td>{{ ligne.session }}</td>
<td>{{ ligne.origine }}</td><td>{{ ligne.appareil }}</td><td>{{ ligne.action }}</td><td>{{ ligne.chemin }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
{% else %}
<div class="vide">Aucune statistique enregistrée.</div>
{% endif %}
</main>
</body>
</html>
"""


@app.route("/admin/statistiques")
def admin_statistiques():
    if not _identifiants_statistiques_valides():
        return Response(
            "Accès administrateur requis.",
            status=401,
            headers={"WWW-Authenticate": 'Basic realm="Statistiques administrateur"'},
        )

    lignes = []
    if FICHIER_VISITES.exists():
        with FICHIER_VISITES.open("r", newline="", encoding="utf-8-sig") as fichier:
            lignes = list(csv.DictReader(fichier, delimiter=";"))

    lignes.reverse()
    sessions = {ligne.get("session", "") for ligne in lignes if ligne.get("session")}
    total_simulations = sum(1 for ligne in lignes if ligne.get("action") == "Simulation")

    return render_template_string(
        ADMIN_STATISTIQUES_HTML,
        lignes=lignes,
        total_lignes=len(lignes),
        total_sessions=len(sessions),
        total_simulations=total_simulations,
    )

def obtenir_service_projection_utilisateur():
    return ServiceProjection()


def formater_euros(valeur: float) -> str:
    return f"{valeur:,.2f} €".replace(",", " ")


def formater_euros_entier(valeur: float) -> str:
    return f"{valeur:,.0f} €".replace(",", " ")


def construire_projection_annuelle(simulation):
    lignes = []

    for numero, ligne_historique in enumerate(
        simulation.historique[11::12],
        start=1,
    ):
        capital = float(ligne_historique["capital"])

        versements = (
            simulation.capital_initial
            + simulation.versement_mensuel * (numero * 12)
        )

        gain = capital - versements

        lignes.append(
            {
                "annee": numero,
                "capital": formater_euros(capital),
                "gain": formater_euros(gain),
            }
        )

    return lignes


def construire_points_graphique(simulation):
    historique = simulation.historique

    if not historique:
        return ""

    largeur = 1000
    hauteur = 260
    marge_x = 20
    marge_y = 20

    capitaux = [float(element["capital"]) for element in historique]

    maximum = max(capitaux) if capitaux else 1
    minimum = min(0, min(capitaux) if capitaux else 0)
    amplitude = maximum - minimum

    if amplitude <= 0:
        amplitude = 1

    nb_points = len(capitaux)
    points = []

    for index, capital in enumerate(capitaux):
        if nb_points <= 1:
            x = largeur / 2
        else:
            x = (
                marge_x
                + index
                * (largeur - 2 * marge_x)
                / (nb_points - 1)
            )

        y = (
            hauteur
            - marge_y
            - ((capital - minimum) / amplitude)
            * (hauteur - 2 * marge_y)
        )

        points.append(f"{x:.1f},{y:.1f}")

    return " ".join(points)


def calculer_risque(simulation):
    performance = simulation.performance

    if performance >= 50:
        return "Faible"

    if performance >= 20:
        return "Modéré"

    return "Élevé"


PAGE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Simulateur Financier Autonome</title>
<style>
:root{
    --fond:#020813;
    --panneau:#06101f;
    --cyan:#37e8ff;
    --cyan2:#9ff8ff;
    --texte:#f5fbff;
    --secondaire:#77dbe8;
}
*{box-sizing:border-box}
html,body{margin:0;width:100%;height:100%;background:var(--fond);color:var(--texte);font-family:"Segoe UI",Arial,sans-serif}
body{overflow:hidden}
.cockpit{
    min-height:100vh;
    position:relative;
    overflow:hidden;
    background:
      radial-gradient(circle at 50% 52%,rgba(0,184,255,.14),transparent 23%),
      radial-gradient(circle at 50% 52%,rgba(0,85,170,.10),transparent 43%),
      #020813;
}
.entete{
    height:68px;
    padding:11px 30px;
    background:#1d2633;
    border-bottom:1px solid #27384b;
}
.entete h1{margin:0;color:#48bfff;font-size:19px}
.entete p{margin:4px 0 0;color:#b9d9ed;font-size:12px}
.entete{position:relative}
.navigation-web{
    position:absolute;right:30px;top:15px;display:flex;gap:10px;
}
.bouton-comparaison{
    padding:9px 18px;border:1px solid var(--cyan);
    border-radius:5px;color:var(--cyan);text-decoration:none;
    font-size:12px;font-weight:700;background:#071728;
}
.bouton-comparaison:hover{background:#0c3148}
.scene{
    width:min(1180px,96vw);
    height:calc(100vh - 68px);
    margin:0 auto;
    position:relative;
    overflow:hidden;
}
.orbite{
    position:absolute;
    left:50%;top:52%;
    transform:translate(-50%,-50%);
    width:360px;height:360px;
    border:1px solid var(--cyan);
    border-radius:50%;
    box-shadow:0 0 25px rgba(55,232,255,.16),inset 0 0 30px rgba(55,232,255,.08);
}
.orbite:before,.orbite:after{
    content:"";position:absolute;border:1px solid var(--cyan);border-radius:50%;
    left:50%;top:50%;transform:translate(-50%,-50%);
}
.orbite:before{width:278px;height:278px}
.orbite:after{width:198px;height:198px}
.coeur{
    position:absolute;left:50%;top:52%;transform:translate(-50%,-50%);
    width:122px;height:122px;border-radius:50%;
    background:radial-gradient(circle,#eaffff 0 5%,#45e8ff 6% 18%,#148dd9 19% 42%,rgba(0,145,255,.15) 43% 70%,transparent 71%);
    box-shadow:0 0 45px #18cfff;
}
.rayon{
    position:absolute;left:50%;top:52%;height:1px;width:255px;background:var(--cyan);
    transform-origin:left center;opacity:.8;
}
.r1{transform:rotate(205deg)} .r2{transform:rotate(335deg)}
.r3{transform:rotate(270deg)} .r4{transform:rotate(25deg)}
.carte{
    position:absolute;width:200px;min-height:108px;padding:14px 12px;
    border:1px solid var(--cyan2);background:rgba(2,8,19,.84);
    text-align:center;box-shadow:0 0 15px rgba(55,232,255,.05);
}
.carte .titre{color:var(--cyan);font-size:12px;text-transform:uppercase}
.carte .valeur{margin-top:9px;font-weight:700;font-size:15px}
.carte .detail{margin-top:9px;color:var(--secondaire);font-size:11px}
.capital{left:105px;top:24%}.risque{left:50%;top:5%;transform:translateX(-50%)}
.score{right:105px;top:24%}.rendement{left:105px;bottom:8%}
.profil{right:105px;bottom:8%}.objectifs{left:50%;bottom:5%;transform:translateX(-50%)}
.decision{
    position:absolute;left:50%;bottom:27%;transform:translateX(-50%);
    width:215px;padding:6px;border:1px solid var(--cyan2);background:#06101f;text-align:center;
    font-size:12px;color:var(--cyan2);
}
.decision strong{display:block;color:var(--cyan);margin-bottom:3px}
.commande{
    position:absolute;left:50%;top:52%;transform:translate(-50%,-50%);
    width:470px;height:470px;border-radius:50%;
}
.formulaire{
    position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
    width:350px;padding:20px;background:rgba(3,12,24,.96);border:1px solid var(--cyan);
    border-radius:8px;z-index:5;display:none;
}
.formulaire.ouvert{display:block}
.formulaire h2{text-align:center;color:var(--cyan);font-size:18px;margin:0 0 16px}
.champs{display:grid;grid-template-columns:1fr 1fr;gap:10px}
label{display:block;font-size:11px;color:#9edce7;margin-bottom:4px}
input{width:100%;height:34px;background:#071728;border:1px solid #25748a;color:white;padding:0 9px;border-radius:4px}
.actions{display:flex;gap:8px;margin-top:15px}
button,.reset{flex:1;border:0;padding:10px;background:#0c9bd8;color:white;font-weight:700;border-radius:4px;cursor:pointer;text-align:center;text-decoration:none;font-size:12px}
.reset{background:#344351}
.lancer{
    position:absolute;left:50%;top:52%;transform:translate(-50%,-50%);
    z-index:4;border:1px solid var(--cyan);background:#071728;color:var(--cyan);
    width:102px;height:102px;border-radius:50%;font-size:12px;
}
.erreur{position:absolute;left:50%;top:15px;transform:translateX(-50%);z-index:9;background:#4b2020;padding:10px 15px;border-radius:5px}
.note{position:absolute;bottom:4px;width:100%;text-align:center;color:#477887;font-size:10px}
@media(max-width:900px){
 .scene{height:850px}.carte{width:180px}.capital,.rendement{left:10px}.score,.profil{right:10px}
}

@media(max-height:720px){
    .entete{height:58px;padding:7px 30px}
    .scene{height:calc(100vh - 58px)}
    .orbite{width:315px;height:315px}
    .orbite:before{width:244px;height:244px}
    .orbite:after{width:174px;height:174px}
    .coeur{width:106px;height:106px}
    .rayon{width:225px}
    .carte{width:188px;min-height:94px;padding:10px}
    .carte .detail{margin-top:6px}
    .capital,.rendement{left:125px}
    .score,.profil{right:125px}
    .decision{bottom:27%;font-size:11px}
    .lancer{width:88px;height:88px}
}

</style>
</head>
<body>
<div class="cockpit">
<header class="entete">
<h1>Simulateur financier autonome</h1>
<p>Simulez • Projetez • Décidez</p>
<div class="navigation-web">
<a class="bouton-comparaison" href="/historique">HISTORIQUE</a>
<a class="bouton-comparaison" href="/comparaison">COMPARAISON</a>
<a class="bouton-comparaison" href="/contact">NOUS CONTACTER</a>
</div>
</header>

{% if erreur %}<div class="erreur">{{ erreur }}</div>{% endif %}

<main class="scene">
<div class="orbite"></div><div class="coeur"></div>
<div class="rayon r1"></div><div class="rayon r2"></div><div class="rayon r3"></div><div class="rayon r4"></div>

<section class="carte capital">
<div class="titre">Capital</div>
<div class="valeur">{{ capital_final if simulation else "0 €" }}</div>
<div class="detail">Capital final projeté</div>
</section>

<section class="carte risque">
<div class="titre">Risque</div>
<div class="valeur">{{ risque if simulation else "En attente" }}</div>
<div class="detail">Niveau calculé</div>
</section>

<section class="carte score">
<div class="titre">Score IA</div>
<div class="valeur">{{ score_ia if simulation else "0.0 / 10" }}</div>
<div class="detail">Évaluation IA</div>
</section>

<section class="carte rendement">
<div class="titre">Rendement</div>
<div class="valeur">{{ performance if simulation else "+0.0 %" }}</div>
<div class="detail">Performance calculée</div>
</section>

<section class="carte profil">
<div class="titre">Profil IA</div>
<div class="valeur">{{ profil_ia if simulation else "En attente" }}</div>
<div class="detail">Profil calculé</div>
</section>

<section class="carte objectifs">
<div class="titre">Objectifs</div>
<div class="valeur">{{ duree_resultat if simulation else "En attente" }}</div>
<div class="detail">Projection long terme</div>
</section>

<div class="decision">
<strong>DÉCISION IA</strong>
{% if simulation %}
Profil : {{ profil_ia }}<br>
Capital : {{ capital_final }}<br>
Confiance : {{ score_ia }}
{% else %}
Profil : En attente<br>
Lancer une simulation<br>
Confiance : en attente
{% endif %}
</div>

<button class="lancer" type="button" onclick="document.getElementById('formulaire').classList.add('ouvert')">
SIMULER
</button>

<form id="formulaire" class="formulaire {% if request.method == 'POST' and erreur %}ouvert{% endif %}" method="post">
<h2>PARAMÈTRES DE SIMULATION</h2>
<div class="champs">
<div><label>Capital initial (€)</label><input type="number" name="capital_initial" min="0" step="100" value="{{ valeurs.capital_initial }}" required></div>
<div><label>Versement mensuel (€)</label><input type="number" name="versement_mensuel" min="0" step="10" value="{{ valeurs.versement_mensuel }}" required></div>
<div><label>Rendement annuel (%)</label><input type="number" name="taux_annuel" min="0" max="100" step="0.1" value="{{ valeurs.taux_annuel }}" required></div>
<div><label>Durée (années)</label><input type="number" name="duree" min="1" max="100" step="1" value="{{ valeurs.duree }}" required></div>
</div>
<div class="actions"><button type="submit">CALCULER</button><a class="reset" href="/">RÉINITIALISER</a></div>
</form>

<div class="note">Outil pédagogique de simulation — aucune projection ne constitue une garantie de résultat futur.<br>© 2026 Simulateur Financier Autonome — Tous droits réservés.</div>
</main>
</div>
</body>
</html>
"""


@app.route(
    "/",
    methods=["GET", "POST"],
)
def accueil():
    enregistrer_ouverture_unique()
    service_projection = obtenir_service_projection_utilisateur()

    simulation = None
    analyse_ia = None
    scenarios = None
    erreur = None

    valeurs = {
        "capital_initial": "10000",
        "versement_mensuel": "500",
        "taux_annuel": "8",
        "duree": "10",
    }

    if request.method == "POST":
        try:
            valeurs = {
                "capital_initial": request.form.get("capital_initial", "0"),
                "versement_mensuel": request.form.get("versement_mensuel", "0"),
                "taux_annuel": request.form.get("taux_annuel", "0"),
                "duree": request.form.get("duree", "1"),
            }

            capital_initial = float(
                valeurs["capital_initial"].strip().replace(",", ".")
            )

            versement_mensuel = float(
                valeurs["versement_mensuel"].strip().replace(",", ".")
            )

            taux_pourcentage = float(
                valeurs["taux_annuel"].strip().replace(",", ".")
            )

            duree_float = float(
                valeurs["duree"].strip().replace(",", ".")
            )

            if not duree_float.is_integer():
                raise ValueError(
                    "La durée doit être exprimée en années entières."
                )

            duree = int(duree_float)

            if capital_initial < 0:
                raise ValueError(
                    "Le capital initial ne peut pas être négatif."
                )

            if versement_mensuel < 0:
                raise ValueError(
                    "Le versement mensuel ne peut pas être négatif."
                )

            if taux_pourcentage < 0:
                raise ValueError(
                    "Le rendement annuel ne peut pas être négatif."
                )

            if duree <= 0:
                raise ValueError(
                    "La durée doit être supérieure à zéro."
                )

            taux_decimal = taux_pourcentage / 100

            simulation = CalculProjection.calculer(
                capital_initial,
                versement_mensuel,
                taux_decimal,
                duree,
            )

            service_projection.ajouter_simulation(simulation)
            enregistrer_visite("Simulation")

            scenarios = {
                "prudent": CalculProjection.calculer(
                    capital_initial,
                    versement_mensuel,
                    taux_decimal * 0.7,
                    duree,
                ),
                "normal": CalculProjection.calculer(
                    capital_initial,
                    versement_mensuel,
                    taux_decimal,
                    duree,
                ),
                "optimiste": CalculProjection.calculer(
                    capital_initial,
                    versement_mensuel,
                    taux_decimal * 1.3,
                    duree,
                ),
            }

            analyse_ia = service_ia.analyser(simulation)

        except ValueError as exc:
            erreur = str(exc)

        except Exception as exc:
            erreur = (
                "Impossible d'effectuer la simulation : "
                f"{exc}"
            )

    if simulation:
        projection_annuelle = construire_projection_annuelle(simulation)
        graphique_points = construire_points_graphique(simulation)

        capital_final = formater_euros(simulation.capital_final)
        total_versements = formater_euros(simulation.total_versements)
        gains = formater_euros(simulation.gains)
        performance = f"{simulation.performance:.2f} %"

        duree_resultat = (
            f"{simulation.duree} an"
            if simulation.duree == 1
            else f"{simulation.duree} ans"
        )

        rendement_resultat = f"{simulation.taux:.2f} %"

        risque = calculer_risque(simulation)
        score_ia = f"{min(10.0, max(0.0, 5.0 + simulation.performance / 20)):.1f} / 10"
        if simulation.performance >= 50:
            profil_ia = "Croissance élevée"
        elif simulation.performance >= 20:
            profil_ia = "Croissance modérée"
        else:
            profil_ia = "Prudent"

        analyse = analyse_ia.analyse
        conseils = analyse_ia.conseils

        scenario_prudent = formater_euros_entier(
            scenarios["prudent"].capital_final
        )

        scenario_normal = formater_euros_entier(
            scenarios["normal"].capital_final
        )

        scenario_optimiste = formater_euros_entier(
            scenarios["optimiste"].capital_final
        )

        indicateurs = (
            f"Capital final : {capital_final}\n"
            f"Gains : {gains}\n"
            f"Performance : {performance}\n"
            f"Durée : {duree_resultat}\n"
            f"Risque indicatif : {calculer_risque(simulation)}"
        )

        if analyse_ia.alertes:
            alertes = "\n".join(
                f"{icone} {message}"
                for icone, message in analyse_ia.alertes
            )
        else:
            alertes = "Aucune alerte."

    else:
        projection_annuelle = []
        graphique_points = ""

        capital_final = "0,00 €"
        total_versements = "0,00 €"
        gains = "0,00 €"
        performance = "0,00 %"
        duree_resultat = "0 an"
        rendement_resultat = "0,00 %"

        risque = "En attente"
        score_ia = "0.0 / 10"
        profil_ia = "En attente"

        analyse = "Lancez une simulation."
        conseils = "Les informations descriptives apparaîtront ici."

        scenario_prudent = "-"
        scenario_normal = "-"
        scenario_optimiste = "-"

        indicateurs = (
            "Capital final : -\n"
            "Gains : -\n"
            "Performance : -\n"
            "Durée : -"
        )

        alertes = "Aucune alerte."

    return render_template_string(
        PAGE_HTML,
        simulation=simulation,
        valeurs=valeurs,
        erreur=erreur,
        capital_final=capital_final,
        total_versements=total_versements,
        gains=gains,
        performance=performance,
        duree_resultat=duree_resultat,
        rendement_resultat=rendement_resultat,
        projection_annuelle=projection_annuelle,
        graphique_points=graphique_points,
        analyse=analyse,
        conseils=conseils,
        scenario_prudent=scenario_prudent,
        scenario_normal=scenario_normal,
        scenario_optimiste=scenario_optimiste,
        indicateurs=indicateurs,
        alertes=alertes,
        risque=risque,
        score_ia=score_ia,
        profil_ia=profil_ia,
    )


COMPARAISON_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Comparaison de scénarios</title>
<style>
:root{
    --fond:#020813;--panneau:#06101f;--cyan:#37e8ff;
    --cyan2:#9ff8ff;--texte:#f5fbff;--secondaire:#77dbe8;
}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:var(--fond);color:var(--texte);font-family:"Segoe UI",Arial,sans-serif}
.entete{
    height:68px;padding:11px 30px;background:#1d2633;
    border-bottom:1px solid #27384b;position:relative;
}
.entete h1{margin:0;color:#48bfff;font-size:19px}
.entete p{margin:4px 0 0;color:#b9d9ed;font-size:12px}
.actions-entete{
    position:absolute;right:30px;top:15px;display:flex;gap:10px;
}
.retour,.imprimer{
    padding:9px 18px;border:1px solid var(--cyan);border-radius:5px;
    color:var(--cyan);text-decoration:none;font-size:12px;font-weight:700;
    background:#071728;cursor:pointer;font-family:inherit;
}
.retour:hover,.imprimer:hover{background:#0c3148}
@media print{
    @page{size:A4 portrait;margin:7mm}
    .actions-entete,.selection{display:none!important}
    html,body{width:100%!important;min-height:0!important;margin:0!important;padding:0!important;background:white!important;color:black!important;font-size:9px!important}
    .entete{height:42px!important;padding:4px 10px!important;background:white!important;border-bottom:1px solid #999!important}
    .entete h1{color:black!important;font-size:14px!important;line-height:17px!important}
    .entete p{color:black!important;margin:1px 0 0!important;font-size:8px!important}
    .page{width:100%!important;max-width:none!important;margin:0!important;padding:7px 0 0!important}
    h2{color:black!important;font-size:18px!important;line-height:20px!important;margin:0!important}
    .sous{color:#333!important;margin:2px 0 7px!important;font-size:9px!important}
    .colonnes{display:grid!important;grid-template-columns:1fr 1fr!important;gap:7px!important;break-inside:avoid!important;page-break-inside:avoid!important}
    .scenario{background:white!important;color:black!important;border:1px solid #777!important;border-radius:5px!important;padding:5px 8px!important;break-inside:avoid!important;page-break-inside:avoid!important}
    .scenario h3{color:black!important;font-size:12px!important;margin:0 0 3px!important}
    .ligne{padding:3px 1px!important;border-bottom:1px solid #ccc!important;font-size:8px!important;line-height:11px!important}
    .ligne strong,.ligne span{color:black!important}
    .synthese{margin-top:7px!important;padding:5px 7px!important;background:white!important;color:black!important;border:1px solid #777!important;border-radius:5px!important;break-inside:avoid!important;page-break-inside:avoid!important}
    .synthese h3{color:black!important;font-size:11px!important;margin:0 0 4px!important}
    .synthese-grille{display:grid!important;grid-template-columns:repeat(4,1fr)!important;gap:4px!important}
    .synthese-grille div{min-height:34px!important;padding:4px 2px!important;background:white!important;border:1px solid #999!important;border-radius:4px!important}
    .synthese-grille strong{color:black!important;font-size:7px!important;margin-bottom:3px!important}
    .synthese-grille span{color:black!important;font-size:7px!important}
    .copyright{color:#333!important;font-size:7px!important;margin:6px 0 0!important;padding:0!important;break-inside:avoid!important;page-break-inside:avoid!important}
}
.page{width:min(1180px,96vw);margin:0 auto;padding:20px 0}
h2{text-align:center;margin:0;color:var(--cyan);font-size:26px}
.sous{text-align:center;color:#b9d9ed;margin:6px 0 18px}
.selection{
    display:grid;grid-template-columns:1fr 1fr;gap:18px;
    background:#071321;border:1px solid #17384c;border-radius:8px;
    padding:16px;margin-bottom:16px;
}
.selection label{display:block;color:var(--cyan);font-size:12px;font-weight:700;margin-bottom:6px}
select{
    width:100%;height:38px;background:#0b2032;color:white;
    border:1px solid #28718d;border-radius:5px;padding:0 10px;
}
.colonnes{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.scenario{
    background:#071321;border:1px solid #17384c;border-radius:8px;
    padding:14px 18px;
}
.scenario h3{text-align:center;color:var(--cyan);margin:0 0 12px}
.ligne{
    display:flex;justify-content:space-between;gap:20px;
    padding:9px 4px;border-bottom:1px solid #132d3d;font-size:13px;
}
.ligne strong{color:#dffaff}
.ligne span{color:white}
.vide{text-align:center;color:#7da0ad;padding:35px}
.synthese{margin-top:16px;background:#071321;border:1px solid #17384c;border-radius:8px;padding:14px 16px}
.synthese h3{text-align:center;color:var(--cyan);margin:0 0 12px}
.synthese-grille{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.synthese-grille div{border:1px solid #28718d;border-radius:6px;padding:12px;text-align:center;background:#0b2032}
.synthese-grille strong{display:block;font-size:12px;margin-bottom:8px}
.synthese-grille span{font-size:12px}
.copyright{text-align:center;color:#477887;font-size:10px;margin:18px 0 4px}
@media(max-width:800px){
    .selection,.colonnes{grid-template-columns:1fr}
    .synthese-grille{grid-template-columns:1fr 1fr}
}
</style>
</head>
<body>
<header class="entete">
<h1>Simulateur financier autonome</h1>
<p>Simulez • Projetez • Décidez</p>
<div class="actions-entete">
<button class="imprimer" type="button" onclick="window.print()">IMPRIMER</button>
<a class="retour" href="/">RETOUR COCKPIT</a>
</div>
</header>

<main class="page">
<h2>COMPARAISON DE SCÉNARIOS</h2>
<div class="sous">Comparez deux simulations enregistrées</div>

{% if simulations|length < 2 %}
<div class="scenario vide">Au moins 2 simulations sont requises pour effectuer une comparaison.</div>
{% else %}
<form class="selection" method="get">
<div>
<label>SCÉNARIO A</label>
<select name="a" onchange="this.form.submit()">
{% for item in simulations %}
<option value="{{ loop.index0 }}" {% if loop.index0 == index_a %}selected{% endif %}>
{{ loop.index }} - {{ item.date_creation.strftime('%d/%m/%Y %H:%M') }} - {{ euros(item.capital_final) }}
</option>
{% endfor %}
</select>
</div>
<div>
<label>SCÉNARIO B</label>
<select name="b" onchange="this.form.submit()">
{% for item in simulations %}
<option value="{{ loop.index0 }}" {% if loop.index0 == index_b %}selected{% endif %}>
{{ loop.index }} - {{ item.date_creation.strftime('%d/%m/%Y %H:%M') }} - {{ euros(item.capital_final) }}
</option>
{% endfor %}
</select>
</div>
</form>

<div class="colonnes">
{% for titre, sim in [('SCÉNARIO A', simulation_a), ('SCÉNARIO B', simulation_b)] %}
<section class="scenario">
<h3>{{ titre }}</h3>
<div class="ligne"><strong>Capital initial</strong><span>{{ euros(sim.capital_initial) }}</span></div>
<div class="ligne"><strong>Versement mensuel</strong><span>{{ euros(sim.versement_mensuel) }}</span></div>
<div class="ligne"><strong>Rendement annuel</strong><span>{{ "%.2f"|format(sim.taux) }} %</span></div>
<div class="ligne"><strong>Durée</strong><span>{{ sim.duree }} ans</span></div>
<div class="ligne"><strong>Total versé</strong><span>{{ euros(sim.total_versements) }}</span></div>
<div class="ligne"><strong>Capital final</strong><span>{{ euros(sim.capital_final) }}</span></div>
<div class="ligne"><strong>Plus-value</strong><span>{{ euros(sim.gains) }}</span></div>
<div class="ligne"><strong>Performance</strong><span>{{ "%.2f"|format(sim.performance) }} %</span></div>
</section>
{% endfor %}
</div>

<section class="synthese">
<h3>SYNTHÈSE AUTOMATIQUE</h3>
<div class="synthese-grille">
<div><strong>Meilleur capital final</strong><span>{{ meilleur_capital }}</span></div>
<div><strong>Meilleure plus-value</strong><span>{{ meilleure_plus_value }}</span></div>
<div><strong>Meilleure performance</strong><span>{{ meilleure_performance }}</span></div>
<div><strong>Écart de capital final</strong><span>{{ ecart_capital }}</span></div>
</div>
</section>
{% endif %}
<div class="copyright">© 2026 Simulateur Financier Autonome — Tous droits réservés.</div>
</main>
</body>
</html>
"""


@app.route("/comparaison")
def comparaison():
    service_projection = obtenir_service_projection_utilisateur()
    simulations = list(service_projection.obtenir_simulations())

    if len(simulations) < 2:
        return render_template_string(
            COMPARAISON_HTML,
            simulations=simulations,
            simulation_a=None,
            simulation_b=None,
            index_a=0,
            index_b=0,
            euros=formater_euros,
        )

    try:
        index_a = int(request.args.get("a", len(simulations) - 2))
    except (TypeError, ValueError):
        index_a = len(simulations) - 2

    try:
        index_b = int(request.args.get("b", len(simulations) - 1))
    except (TypeError, ValueError):
        index_b = len(simulations) - 1

    index_a = max(0, min(index_a, len(simulations) - 1))
    index_b = max(0, min(index_b, len(simulations) - 1))

    simulation_a = simulations[index_a]
    simulation_b = simulations[index_b]

    if simulation_a.capital_final >= simulation_b.capital_final:
        meilleur_capital = f"Scénario A — {formater_euros(simulation_a.capital_final)}"
    else:
        meilleur_capital = f"Scénario B — {formater_euros(simulation_b.capital_final)}"

    if simulation_a.gains >= simulation_b.gains:
        meilleure_plus_value = f"Scénario A — {formater_euros(simulation_a.gains)}"
    else:
        meilleure_plus_value = f"Scénario B — {formater_euros(simulation_b.gains)}"

    if simulation_a.performance >= simulation_b.performance:
        meilleure_performance = f"Scénario A — {simulation_a.performance:.2f} %"
    else:
        meilleure_performance = f"Scénario B — {simulation_b.performance:.2f} %"

    ecart_capital = formater_euros(
        abs(simulation_a.capital_final - simulation_b.capital_final)
    )

    return render_template_string(
        COMPARAISON_HTML,
        simulations=simulations,
        simulation_a=simulation_a,
        simulation_b=simulation_b,
        index_a=index_a,
        index_b=index_b,
        euros=formater_euros,
        meilleur_capital=meilleur_capital,
        meilleure_plus_value=meilleure_plus_value,
        meilleure_performance=meilleure_performance,
        ecart_capital=ecart_capital,
    )


HISTORIQUE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Historique des simulations</title>
<style>
:root{--fond:#020813;--panneau:#06101f;--cyan:#37e8ff;--texte:#f5fbff}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:var(--fond);color:var(--texte);font-family:"Segoe UI",Arial,sans-serif}
.entete{height:68px;padding:11px 30px;background:#1d2633;border-bottom:1px solid #27384b;position:relative}
.entete h1{margin:0;color:#48bfff;font-size:19px}.entete p{margin:4px 0 0;color:#b9d9ed;font-size:12px}
.retour{position:absolute;right:30px;top:15px;padding:9px 18px;border:1px solid var(--cyan);border-radius:5px;color:var(--cyan);text-decoration:none;font-size:12px;font-weight:700;background:#071728}
.page{width:min(1500px,96vw);margin:0 auto;padding:24px 0}
h2{text-align:center;color:var(--cyan);font-size:26px;margin:0 0 20px}
.tableau{overflow:auto;border:1px solid #17384c;border-radius:8px;background:#071321}
table{width:100%;border-collapse:collapse;min-width:1050px}
th{background:#0b2032;color:var(--cyan);text-align:left;padding:12px 10px;font-size:12px}
td{padding:11px 10px;border-top:1px solid #132d3d;font-size:12px;white-space:nowrap}
tr:hover td{background:#0a1a2a}
.vide{text-align:center;padding:45px;color:#7da0ad}
</style>
</head>
<body>
<header class="entete">
<h1>Simulateur financier autonome</h1>
<p>Simulez • Projetez • Décidez</p>
<a class="retour" href="/">RETOUR COCKPIT</a>
</header>
<main class="page">
<h2>HISTORIQUE DES SIMULATIONS</h2>
{% if simulations %}
<div class="tableau">
<table>
<thead><tr>
<th>N°</th><th>Date</th><th>Capital initial</th><th>Versement mensuel</th>
<th>Rendement annuel</th><th>Durée</th><th>Total versé</th>
<th>Capital final</th><th>Plus-value</th><th>Performance</th>
</tr></thead>
<tbody>
{% for sim in simulations %}
<tr>
<td>{{ loop.index }}</td>
<td>{{ sim.date_creation.strftime('%d/%m/%Y %H:%M') }}</td>
<td>{{ euros(sim.capital_initial) }}</td>
<td>{{ euros(sim.versement_mensuel) }}</td>
<td>{{ "%.2f"|format(sim.taux) }} %</td>
<td>{{ sim.duree }} ans</td>
<td>{{ euros(sim.total_versements) }}</td>
<td>{{ euros(sim.capital_final) }}</td>
<td>{{ euros(sim.gains) }}</td>
<td>{{ "%.2f"|format(sim.performance) }} %</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
{% else %}
<div class="vide">Aucune simulation enregistrée.</div>
{% endif %}
<div style="text-align:center;color:#477887;font-size:10px;margin:18px 0 4px">© 2026 Simulateur Financier Autonome — Tous droits réservés.</div>
</main>
</body>
</html>
"""


CONTACT_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nous contacter</title>
<style>
:root{--fond:#020813;--panneau:#06101f;--cyan:#37e8ff;--texte:#f5fbff}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:var(--fond);color:var(--texte);font-family:"Segoe UI",Arial,sans-serif}
.entete{height:68px;padding:11px 30px;background:#1d2633;border-bottom:1px solid #27384b;position:relative}
.entete h1{margin:0;color:#48bfff;font-size:19px}.entete p{margin:4px 0 0;color:#b9d9ed;font-size:12px}
.retour{position:absolute;right:30px;top:15px;padding:9px 18px;border:1px solid var(--cyan);border-radius:5px;color:var(--cyan);text-decoration:none;font-size:12px;font-weight:700;background:#071728}
.page{width:min(760px,92vw);margin:0 auto;padding:45px 0}
h2{text-align:center;color:var(--cyan);font-size:28px;margin:0 0 10px}
.intro{text-align:center;color:#b9d9ed;margin-bottom:25px}
.carte{background:#071321;border:1px solid #17384c;border-radius:10px;padding:25px}
label{display:block;color:var(--cyan);font-weight:700;font-size:12px;margin:15px 0 6px}
input,textarea{width:100%;background:#0b2032;color:white;border:1px solid #28718d;border-radius:5px;padding:11px;font:inherit}
textarea{min-height:150px;resize:vertical}
button{width:100%;margin-top:20px;padding:12px;border:1px solid var(--cyan);border-radius:5px;background:#0c3148;color:var(--cyan);font-weight:800;cursor:pointer}
.info{text-align:center;color:#7da0ad;font-size:12px;margin-top:18px}
</style>
</head>
<body>
<header class="entete">
<h1>Simulateur financier autonome</h1>
<p>Simulez • Projetez • Décidez</p>
<a class="retour" href="/">RETOUR COCKPIT</a>
</header>
<main class="page">
<h2>NOUS CONTACTER</h2>
<div class="intro">Une question ou une remarque concernant le simulateur ?</div>
<div class="carte">
<form action="mailto:" method="post" enctype="text/plain">
<label>Nom</label>
<input type="text" name="Nom" required>
<label>Adresse e-mail</label>
<input type="email" name="Email" required>
<label>Objet</label>
<input type="text" name="Objet" required>
<label>Message</label>
<textarea name="Message" required></textarea>
<button type="submit">PRÉPARER LE MESSAGE</button>
</form>
<div class="info">Le bouton ouvre le logiciel de messagerie configuré sur l'ordinateur.</div>
</div>
<div class="info">© 2026 Simulateur Financier Autonome — Tous droits réservés.</div>
</main>
</body>
</html>
"""


@app.route("/historique")
def historique():
    service_projection = obtenir_service_projection_utilisateur()
    simulations = list(service_projection.obtenir_simulations())
    return render_template_string(
        HISTORIQUE_HTML,
        simulations=simulations,
        euros=formater_euros,
    )


@app.route("/contact")
def contact():
    return render_template_string(CONTACT_HTML)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )
