"""
web/app.py

Version Web locale du Simulateur Financier Autonome.
Réutilise le moteur financier et le service IA existants.
"""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, request, render_template_string

RACINE_PROJET = Path(__file__).resolve().parent.parent

if str(RACINE_PROJET) not in sys.path:
    sys.path.insert(0, str(RACINE_PROJET))

from services.calcul_projection import CalculProjection
from services.service_ia import ServiceIA

app = Flask(__name__)
service_ia = ServiceIA()


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
    --fond:#101010;
    --panneau:#2b2b2b;
    --panneau2:#303030;
    --bordure:#414141;
    --bleu:#1995e8;
    --cyan:#4fc3f7;
    --texte:#f5f5f5;
    --secondaire:#b8b8b8;
}
*{box-sizing:border-box}
body{
    margin:0;
    min-height:100vh;
    background:var(--fond);
    color:var(--texte);
    font-family:Arial,Helvetica,sans-serif;
}
.page{
    width:min(1480px,calc(100% - 30px));
    margin:0 auto;
    padding:22px 0 50px;
}
h1{
    margin:0 0 22px;
    text-align:center;
    color:var(--cyan);
    font-size:30px;
    letter-spacing:1.5px;
}
.zone-haute{
    display:grid;
    grid-template-columns:minmax(0,1.45fr) minmax(360px,.85fr);
    gap:16px;
}
.bloc{
    background:var(--panneau);
    border:1px solid var(--bordure);
    border-radius:14px;
    padding:22px;
}
.bloc h2{
    margin:0 0 20px;
    text-align:center;
    font-size:24px;
}
.champs{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:14px;
}
label{
    display:block;
    margin-bottom:6px;
    font-size:14px;
}
input{
    width:100%;
    height:42px;
    padding:0 12px;
    border:1px solid #555;
    border-radius:8px;
    background:#333;
    color:#fff;
    font-size:15px;
}
.actions{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:14px;
    margin-top:26px;
}
button,.bouton-lien{
    min-height:42px;
    display:flex;
    align-items:center;
    justify-content:center;
    border:0;
    border-radius:8px;
    padding:10px 18px;
    text-decoration:none;
    font-size:15px;
    font-weight:700;
    cursor:pointer;
}
button{background:var(--bleu);color:#fff}
.bouton-lien{background:#555;color:#fff}
.erreur{
    margin-top:18px;
    padding:12px;
    border:1px solid #a55;
    border-radius:8px;
    background:#3b1e1e;
    color:#ffc1c1;
}
.resultat-ligne{
    display:grid;
    grid-template-columns:1fr auto;
    gap:16px;
    align-items:center;
    margin:8px 0;
    padding:12px 14px;
    border-radius:9px;
    background:var(--panneau2);
}
.resultat-ligne strong{font-size:14px}
.resultat-ligne span{font-size:17px;font-weight:700}
.graphique{margin-top:16px}
.graphique h2{margin-bottom:10px}
.graphique-zone{
    min-height:270px;
    padding:8px;
    border-radius:10px;
    background:#252525;
}
.graphique-zone svg{width:100%;height:270px;display:block}
.graphique-legende{
    display:flex;
    justify-content:space-between;
    margin-top:6px;
    color:#aaa;
    font-size:12px;
}
.attente{
    min-height:220px;
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    color:#888;
}
.zone-basse{
    display:grid;
    grid-template-columns:minmax(0,1.2fr) minmax(360px,.8fr);
    gap:16px;
    margin-top:16px;
}
.projection h2,.ia h2{color:var(--cyan)}
.projection-sous-titre{
    margin-top:-10px;
    margin-bottom:16px;
    text-align:center;
    color:#c3c3c3;
    font-size:14px;
}
.table-wrap{
    max-height:360px;
    overflow:auto;
    border-radius:10px;
}
table{
    width:100%;
    border-collapse:collapse;
    background:#162743;
}
th{
    position:sticky;
    top:0;
    padding:10px;
    background:#087fff;
    text-align:left;
}
td{
    padding:9px 10px;
    border-bottom:1px solid #243b5f;
}
.carte-ia{
    margin-bottom:10px;
    padding:14px;
    border-radius:10px;
    background:#353535;
}
.carte-ia h3{margin:0 0 8px;font-size:16px}
.carte-ia p{
    margin:0;
    color:#e0e0e0;
    line-height:1.55;
    white-space:pre-line;
}
.scenarios{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:8px;
}
.scenario{
    padding:10px;
    border-radius:8px;
    background:#292929;
}
.scenario strong{
    display:block;
    margin-bottom:5px;
    color:var(--cyan);
}
.avertissement{
    margin:28px auto 0;
    max-width:960px;
    color:#888;
    text-align:center;
    font-size:12px;
    line-height:1.55;
}
@media(max-width:1050px){
    .zone-haute,.zone-basse{grid-template-columns:1fr}
    .champs{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:620px){
    .page{width:calc(100% - 18px)}
    .champs,.actions,.scenarios{grid-template-columns:1fr}
    .bloc{padding:16px}
    h1{font-size:23px}
}
</style>
</head>
<body>
<div class="page">

<h1>SIMULATEUR FINANCIER AUTONOME</h1>

<div class="zone-haute">

<section class="bloc">
<h2>PARAMÈTRES DE SIMULATION</h2>

<form method="post">

<div class="champs">

<div>
<label>Capital initial (€)</label>
<input type="number" name="capital_initial" min="0" step="100"
value="{{ valeurs.capital_initial }}" required>
</div>

<div>
<label>Versement mensuel (€)</label>
<input type="number" name="versement_mensuel" min="0" step="10"
value="{{ valeurs.versement_mensuel }}" required>
</div>

<div>
<label>Rendement annuel (%)</label>
<input type="number" name="taux_annuel" min="0" max="100" step="0.1"
value="{{ valeurs.taux_annuel }}" required>
</div>

<div>
<label>Durée (années)</label>
<input type="number" name="duree" min="1" max="100" step="1"
value="{{ valeurs.duree }}" required>
</div>

</div>

<div class="actions">
<button type="submit">Calculer</button>
<a class="bouton-lien" href="/">Réinitialiser</a>
</div>

</form>

{% if erreur %}
<div class="erreur">{{ erreur }}</div>
{% endif %}

</section>

<section class="bloc">
<h2>RÉSULTATS</h2>

<div class="resultat-ligne">
<strong>CAPITAL FINAL</strong>
<span>{{ capital_final }}</span>
</div>

<div class="resultat-ligne">
<strong>VERSEMENTS</strong>
<span>{{ total_versements }}</span>
</div>

<div class="resultat-ligne">
<strong>PLUS-VALUE</strong>
<span>{{ gains }}</span>
</div>

<div class="resultat-ligne">
<strong>PERFORMANCE</strong>
<span>{{ performance }}</span>
</div>

<div class="resultat-ligne">
<strong>DURÉE</strong>
<span>{{ duree_resultat }}</span>
</div>

<div class="resultat-ligne">
<strong>RENDEMENT</strong>
<span>{{ rendement_resultat }}</span>
</div>

</section>
</div>

<section class="bloc graphique">
<h2>ÉVOLUTION DU CAPITAL</h2>

{% if simulation %}

<div class="graphique-zone">
<svg viewBox="0 0 1000 260" preserveAspectRatio="none">
<line x1="20" y1="240" x2="980" y2="240" stroke="#666" stroke-width="1"/>
<polyline
points="{{ graphique_points }}"
fill="none"
stroke="#1995e8"
stroke-width="4"
vector-effect="non-scaling-stroke"
/>
</svg>
</div>

<div class="graphique-legende">
<span>Départ</span>
<span>{{ duree_resultat }}</span>
</div>

{% else %}

<div class="attente">
Lancez une simulation pour afficher l'évolution du capital.
</div>

{% endif %}

</section>

<div class="zone-basse">

<section class="bloc projection">
<h2>📊 PROJECTION DU CAPITAL</h2>

<div class="projection-sous-titre">
Projection annuelle de l'investissement
</div>

{% if projection_annuelle %}

<div class="table-wrap">
<table>
<thead>
<tr>
<th>Année</th>
<th>Capital</th>
<th>Gain</th>
</tr>
</thead>

<tbody>
{% for ligne in projection_annuelle %}
<tr>
<td>{{ ligne.annee }}</td>
<td>{{ ligne.capital }}</td>
<td>{{ ligne.gain }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>

{% else %}

<div class="attente">
La projection annuelle apparaîtra ici.
</div>

{% endif %}

</section>

<section class="bloc ia">
<h2>IA FINANCIÈRE</h2>

<div class="carte-ia">
<h3>🟢 Analyse</h3>
<p>{{ analyse }}</p>
</div>

<div class="carte-ia">
<h3>💡 Lecture descriptive</h3>
<p>{{ conseils }}</p>
</div>

<div class="carte-ia">
<h3>📈 Scénarios V2</h3>
<div class="scenarios">

<div class="scenario">
<strong>Prudent</strong>
{{ scenario_prudent }}
</div>

<div class="scenario">
<strong>Normal</strong>
{{ scenario_normal }}
</div>

<div class="scenario">
<strong>Optimiste</strong>
{{ scenario_optimiste }}
</div>

</div>
</div>

<div class="carte-ia">
<h3>📊 Indicateurs</h3>
<p>{{ indicateurs }}</p>
</div>

<div class="carte-ia">
<h3>⚠ Alertes</h3>
<p>{{ alertes }}</p>
</div>

</section>

</div>

<div class="avertissement">
Outil pédagogique de simulation. Les résultats dépendent exclusivement
des hypothèses saisies et ne constituent ni une recommandation financière
ni une garantie de résultat futur.
</div>

</div>
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
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )
