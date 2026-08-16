"""
web/app.py

Version Web locale du Simulateur Financier Autonome.
Réutilise le moteur financier et le service IA existants.
"""

from __future__ import annotations

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

from flask import Flask, request, render_template_string

RACINE_PROJET = Path(__file__).resolve().parent.parent

if str(RACINE_PROJET) not in sys.path:
    sys.path.insert(0, str(RACINE_PROJET))

from services.calcul_projection import CalculProjection
from services.service_ia import ServiceIA

app = Flask(__name__)
service_ia = ServiceIA()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
journal = logging.getLogger("simulateur_financier")

def enregistrer_utilisation(simulation):
    """
    Enregistre chaque simulation validée dans les logs Render.
    Aucune donnée permettant d'identifier l'utilisateur n'est enregistrée.
    """
    try:
        journal.info(
            "SIMULATION_UTILISEE | capital_initial=%.2f | "
            "versement_mensuel=%.2f | rendement_annuel=%.2f%% | "
            "duree=%s | capital_final=%.2f",
            float(simulation.capital_initial),
            float(simulation.versement_mensuel),
            float(simulation.taux),
            simulation.duree,
            float(simulation.capital_final),
        )
    except Exception:
        journal.info("SIMULATION_UTILISEE")


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

<div class="note">Outil pédagogique de simulation — aucune projection ne constitue une garantie de résultat futur.</div>
</main>
</div>

{% if simulation_locale %}
<script>
(function () {
    const simulation = {{ simulation_locale|tojson }};
    const cle = "simulateur_financier_historique_v1";
    let historique = [];

    try {
        historique = JSON.parse(localStorage.getItem(cle) || "[]");
        if (!Array.isArray(historique)) historique = [];
    } catch (e) {
        historique = [];
    }

    historique.push(simulation);
    localStorage.setItem(cle, JSON.stringify(historique));
})();
</script>
{% endif %}
</body>
</html>
"""


@app.route(
    "/",
    methods=["GET", "POST"],
)
def accueil():
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

            enregistrer_utilisation(simulation)

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
        simulation_locale=(
            simulation.to_dict()
            if simulation
            else None
        ),
    )


COMPARAISON_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Comparaison de scénarios</title>
<style>
:root{--fond:#020813;--panneau:#06101f;--cyan:#37e8ff;--cyan2:#9ff8ff;--texte:#f5fbff;--secondaire:#77dbe8}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:var(--fond);color:var(--texte);font-family:"Segoe UI",Arial,sans-serif}
.entete{height:68px;padding:11px 30px;background:#1d2633;border-bottom:1px solid #27384b;position:relative}
.entete h1{margin:0;color:#48bfff;font-size:19px}.entete p{margin:4px 0 0;color:#b9d9ed;font-size:12px}
.actions-entete{position:absolute;right:30px;top:15px;display:flex;gap:10px}
.retour,.imprimer{padding:9px 18px;border:1px solid var(--cyan);border-radius:5px;color:var(--cyan);text-decoration:none;font-size:12px;font-weight:700;background:#071728;cursor:pointer;font-family:inherit}
.page{width:min(1180px,96vw);margin:0 auto;padding:20px 0}
h2{text-align:center;margin:0;color:var(--cyan);font-size:26px}.sous{text-align:center;color:#b9d9ed;margin:6px 0 18px}
.selection{display:grid;grid-template-columns:1fr 1fr;gap:18px;background:#071321;border:1px solid #17384c;border-radius:8px;padding:16px;margin-bottom:16px}
.selection label{display:block;color:var(--cyan);font-size:12px;font-weight:700;margin-bottom:6px}
select{width:100%;height:38px;background:#0b2032;color:white;border:1px solid #28718d;border-radius:5px;padding:0 10px}
.colonnes{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.scenario{background:#071321;border:1px solid #17384c;border-radius:8px;padding:14px 18px}
.scenario h3{text-align:center;color:var(--cyan);margin:0 0 12px}
.ligne{display:flex;justify-content:space-between;gap:20px;padding:9px 4px;border-bottom:1px solid #132d3d;font-size:13px}
.ligne strong{color:#dffaff}.ligne span{color:white}.vide{text-align:center;color:#7da0ad;padding:35px}
@media(max-width:800px){.selection,.colonnes{grid-template-columns:1fr}}
@media print{.actions-entete,.selection{display:none!important}html,body{background:white!important;color:black!important}.entete{background:white!important}.scenario{background:white!important;color:black!important;border:1px solid #777!important}.ligne strong,.ligne span,h2,.scenario h3{color:black!important}}
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
<div id="comparaison-vide" class="scenario vide" style="display:none">Il faut au moins deux simulations enregistrées dans l'historique.</div>
<div id="comparaison-contenu" style="display:none">
<div class="selection">
<div><label>SCÉNARIO A</label><select id="scenario-a"></select></div>
<div><label>SCÉNARIO B</label><select id="scenario-b"></select></div>
</div>
<div class="colonnes">
<section class="scenario"><h3>SCÉNARIO A</h3><div id="details-a"></div></section>
<section class="scenario"><h3>SCÉNARIO B</h3><div id="details-b"></div></section>
</div>
</div>
</main>
<script>
(function(){
 const cle="simulateur_financier_historique_v1";
 let historique=[];
 try{historique=JSON.parse(localStorage.getItem(cle)||"[]");if(!Array.isArray(historique))historique=[];}catch(e){historique=[];}
 const vide=document.getElementById("comparaison-vide"),contenu=document.getElementById("comparaison-contenu");
 if(historique.length<2){vide.style.display="block";return;}
 contenu.style.display="block";
 const a=document.getElementById("scenario-a"),b=document.getElementById("scenario-b");
 const euros=v=>Number(v||0).toLocaleString("fr-FR",{minimumFractionDigits:2,maximumFractionDigits:2})+" €";
 const dateSim=s=>{if(!s.date_creation)return "-";const d=new Date(s.date_creation);return Number.isNaN(d.getTime())?"-":d.toLocaleString("fr-FR",{day:"2-digit",month:"2-digit",year:"numeric",hour:"2-digit",minute:"2-digit"});};
 historique.forEach((s,i)=>{const t=`${i+1} - ${dateSim(s)} - ${euros(s.capital_final)}`;const oa=document.createElement("option"),ob=document.createElement("option");oa.value=ob.value=String(i);oa.textContent=ob.textContent=t;a.appendChild(oa);b.appendChild(ob);});
 a.value="0";b.value="1";
 const ligne=(l,v)=>`<div class="ligne"><strong>${l}</strong><span>${v}</span></div>`;
 function afficher(id,s){document.getElementById(id).innerHTML=
 ligne("Date",dateSim(s))+ligne("Capital initial",euros(s.capital_initial))+ligne("Versement mensuel",euros(s.versement_mensuel))+
 ligne("Rendement annuel",Number(s.taux||0).toFixed(2)+" %")+ligne("Durée",Number(s.duree||0)+" ans")+
 ligne("Total versé",euros(s.total_versements))+ligne("Capital final",euros(s.capital_final))+ligne("Plus-value",euros(s.gains))+
 ligne("Performance",Number(s.performance||0).toFixed(2)+" %");}
 function actualiser(){afficher("details-a",historique[Number(a.value)]);afficher("details-b",historique[Number(b.value)]);}
 a.addEventListener("change",actualiser);b.addEventListener("change",actualiser);actualiser();
})();
</script>
</body>
</html>
"""


@app.route("/comparaison")
def comparaison():
    return render_template_string(COMPARAISON_HTML)


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
<div style="position:absolute;right:30px;top:15px;display:flex;gap:10px">
<a class="retour" style="position:static" href="/comparaison">COMPARER</a>
<button id="vider-historique" style="padding:9px 18px;border:1px solid #ff6677;border-radius:5px;color:#ff6677;background:#071728;font-size:12px;font-weight:700;cursor:pointer">VIDER L'HISTORIQUE</button>
<a class="retour" style="position:static" href="/">RETOUR COCKPIT</a>
</div>
</header>
<main class="page">
<h2>HISTORIQUE DES SIMULATIONS</h2>
<div id="historique-vide" class="vide">Aucune simulation enregistrée.</div>
<div id="historique-tableau" class="tableau" style="display:none">
<table>
<thead><tr>
<th>N°</th><th>Date</th><th>Capital initial</th><th>Versement mensuel</th>
<th>Rendement annuel</th><th>Durée</th><th>Total versé</th>
<th>Capital final</th><th>Plus-value</th><th>Performance</th><th>Action</th>
</tr></thead>
<tbody id="historique-corps"></tbody>
</table>
</div>

<script>
(function () {
    const cle = "simulateur_financier_historique_v1";
    let historique = [];

    try {
        historique = JSON.parse(localStorage.getItem(cle) || "[]");
        if (!Array.isArray(historique)) historique = [];
    } catch (e) {
        historique = [];
    }

    if (!historique.length) return;

    const euros = valeur =>
        Number(valeur || 0).toLocaleString("fr-FR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }) + " €";

    const corps = document.getElementById("historique-corps");

    historique.forEach((sim, index) => {
        const date = sim.date_creation
            ? new Date(sim.date_creation).toLocaleString("fr-FR", {
                day:"2-digit", month:"2-digit", year:"numeric",
                hour:"2-digit", minute:"2-digit"
              })
            : "-";

        const ligne = document.createElement("tr");
        ligne.innerHTML = `
            <td>${index + 1}</td>
            <td>${date}</td>
            <td>${euros(sim.capital_initial)}</td>
            <td>${euros(sim.versement_mensuel)}</td>
            <td>${Number(sim.taux || 0).toFixed(2)} %</td>
            <td>${sim.duree || 0} ans</td>
            <td>${euros(sim.total_versements)}</td>
            <td>${euros(sim.capital_final)}</td>
            <td>${euros(sim.gains)}</td>
            <td>${Number(sim.performance || 0).toFixed(2)} %</td>
            <td><button class="supprimer-simulation" data-index="${index}" style="padding:6px 10px;border:1px solid #ff6677;border-radius:4px;background:#24111a;color:#ff6677;font-weight:700;cursor:pointer">SUPPRIMER</button></td>
        `;
        corps.appendChild(ligne);
    });

    document.getElementById("historique-vide").style.display = "none";
    document.getElementById("historique-tableau").style.display = "block";

    document.querySelectorAll(".supprimer-simulation").forEach((bouton) => {
        bouton.addEventListener("click", function () {
            if (!confirm("Supprimer cette simulation de l'historique ?")) return;
            const index = Number(this.dataset.index);
            historique.splice(index, 1);
            localStorage.setItem(cle, JSON.stringify(historique));
            location.reload();
        });
    });

    document.getElementById("vider-historique").addEventListener("click", function () {
        if (!historique.length) return;
        if (!confirm("Supprimer définitivement toutes les simulations enregistrées ?")) return;
        localStorage.removeItem(cle);
        location.reload();
    });
})();
</script>
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
</main>
</body>
</html>
"""


@app.route("/historique")
def historique():
    return render_template_string(
        HISTORIQUE_HTML,
        simulations=[],
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
