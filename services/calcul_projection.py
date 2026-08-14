"""
calcul_projection.py
--------------------

Service dédié au calcul financier des projections.

Responsabilité :
- Calcul de l'évolution du capital.
- Construction de l'historique mensuel.
- Calcul des indicateurs de performance.

Aucune sauvegarde.
Aucune gestion mémoire.
"""

from modeles.simulation import Simulation


class CalculProjection:
    """Calculateur financier."""

    NB_MOIS_PAR_AN = 12

    @classmethod
    def calculer(
        cls,
        capital_initial: float,
        versement_mensuel: float,
        taux_annuel: float,
        duree: int,
    ) -> Simulation:

        taux_mensuel = taux_annuel / cls.NB_MOIS_PAR_AN
        nb_mois = duree * cls.NB_MOIS_PAR_AN

        capital = float(capital_initial)
        historique = []

        for mois in range(1, nb_mois + 1):

            interets = capital * taux_mensuel

            capital += interets
            capital += versement_mensuel

            historique.append(
                {
                    "mois": mois,
                    "capital": round(capital, 2),
                    "interets": round(interets, 2),
                }
            )

        total_versements = (
            capital_initial
            + versement_mensuel * nb_mois
        )

        gains = capital - total_versements

        performance = (
            gains / total_versements * 100
            if total_versements > 0
            else 0
        )

        return Simulation(
            capital_initial=capital_initial,
            versement_mensuel=versement_mensuel,
            taux=taux_annuel * 100,
            duree=duree,
            capital_final=round(capital, 2),
            total_versements=round(
                total_versements,
                2,
            ),
            gains=round(gains, 2),
            performance=round(
                performance,
                2,
            ),
            historique=historique,
        )
