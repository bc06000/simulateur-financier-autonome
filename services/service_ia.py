"""
services/service_ia.py

Service local d'analyse descriptive des simulations financières.

Ce service décrit les résultats calculés par le simulateur.
Il ne fournit aucun conseil, aucune recommandation financière
et ne décide pas à la place de l'utilisateur.
"""

from dataclasses import dataclass


@dataclass
class AnalyseIA:
    score: float
    profil: str
    analyse: str
    conseils: str
    alertes: list


class ServiceIA:

    def __init__(self):
        pass

    def analyser(self, simulation):
        performance = simulation.performance

        if performance >= 50:
            score = 9.0
            profil = "Croissance élevée"
            analyse = (
                "Dans les hypothèses saisies, la projection présente "
                "une croissance élevée par rapport aux sommes versées."
            )
            conseils = (
                "Lecture descriptive : ce résultat dépend directement "
                "du capital, des versements, du rendement hypothétique "
                "et de la durée renseignés par l'utilisateur."
            )
            alertes = [
                (
                    "i",
                    "Une projection ne constitue pas une garantie "
                    "de résultat futur."
                )
            ]

        elif performance >= 20:
            score = 7.5
            profil = "Croissance soutenue"
            analyse = (
                "Dans les hypothèses saisies, la projection présente "
                "une croissance soutenue du capital."
            )
            conseils = (
                "Lecture descriptive : la modification d'une hypothèse "
                "peut être comparée à cette simulation afin d'observer "
                "son effet sur le résultat."
            )
            alertes = [
                (
                    "i",
                    "Les résultats correspondent uniquement "
                    "aux hypothèses de cette simulation."
                )
            ]

        elif performance >= 10:
            score = 6.5
            profil = "Croissance modérée"
            analyse = (
                "Dans les hypothèses saisies, la projection présente "
                "une croissance modérée du capital."
            )
            conseils = (
                "Lecture descriptive : le résultat affiché permet "
                "d'observer l'effet combiné des paramètres renseignés."
            )
            alertes = [
                (
                    "i",
                    "Toute modification des paramètres entraîne "
                    "une nouvelle projection."
                )
            ]

        else:
            score = 5.0
            profil = "Croissance limitée"
            analyse = (
                "Dans les hypothèses saisies, l'écart entre les sommes "
                "versées et le capital projeté reste limité."
            )
            conseils = (
                "Lecture descriptive : cette simulation peut servir "
                "de point de comparaison avec d'autres hypothèses "
                "définies librement par l'utilisateur."
            )
            alertes = [
                (
                    "i",
                    "Le simulateur analyse un scénario et ne fournit "
                    "aucune recommandation financière."
                )
            ]

        return AnalyseIA(
            score=score,
            profil=profil,
            analyse=analyse,
            conseils=conseils,
            alertes=alertes
        )
