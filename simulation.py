from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Simulation:

    id: int = 0

    date_creation: datetime = field(
        default_factory=datetime.now
    )

    capital_initial: float = 0.0

    versement_mensuel: float = 0.0

    taux: float = 0.0

    duree: int = 0

    capital_final: float = 0.0

    total_versements: float = 0.0

    gains: float = 0.0

    performance: float = 0.0

    historique: list = field(
        default_factory=list
    )

    commentaires_ia: str = ""

    client: str = ""

    # =====================================================
    # CONVERSION -> DICTIONNAIRE
    # =====================================================

    def to_dict(self):

        return {
            "id": self.id,
            "date_creation": self.date_creation.isoformat(),
            "capital_initial": self.capital_initial,
            "versement_mensuel": self.versement_mensuel,
            "taux": self.taux,
            "duree": self.duree,
            "capital_final": self.capital_final,
            "total_versements": self.total_versements,
            "gains": self.gains,
            "performance": self.performance,
            "historique": self.historique,
            "commentaires_ia": self.commentaires_ia,
            "client": self.client
        }

    # =====================================================
    # CONVERSION <- DICTIONNAIRE
    # =====================================================

    @classmethod
    def from_dict(cls, donnees):

        simulation = cls()

        simulation.id = donnees.get("id", 0)

        date = donnees.get("date_creation")

        if date:
            try:
                simulation.date_creation = datetime.fromisoformat(date)
            except ValueError:
                simulation.date_creation = datetime.now()

        simulation.capital_initial = donnees.get(
            "capital_initial",
            0.0
        )

        simulation.versement_mensuel = donnees.get(
            "versement_mensuel",
            0.0
        )

        simulation.taux = donnees.get(
            "taux",
            0.0
        )

        simulation.duree = donnees.get(
            "duree",
            0
        )

        simulation.capital_final = donnees.get(
            "capital_final",
            0.0
        )

        simulation.total_versements = donnees.get(
            "total_versements",
            0.0
        )

        simulation.gains = donnees.get(
            "gains",
            0.0
        )

        simulation.performance = donnees.get(
            "performance",
            0.0
        )

        simulation.historique = donnees.get(
            "historique",
            []
        )

        simulation.commentaires_ia = donnees.get(
            "commentaires_ia",
            ""
        )

        simulation.client = donnees.get(
            "client",
            ""
        )

        return simulation