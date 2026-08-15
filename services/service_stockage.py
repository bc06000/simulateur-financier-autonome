"""
services/service_stockage.py

Service local de stockage JSON.

Chaque fichier de stockage peut être identifié par un nom
spécifique afin de séparer les données des utilisateurs.
"""

import json
from pathlib import Path


class ServiceStockage:

    def __init__(self):
        self.dossier = (
            Path(__file__).resolve().parent.parent
            / "donnees"
        )

        self.dossier.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _chemin(self, nom_fichier):
        """
        Retourne le chemin du fichier demandé.
        """

        return self.dossier / nom_fichier

    def charger(self, nom_fichier):
        """
        Charge les données JSON d'un fichier.
        """

        chemin = self._chemin(
            nom_fichier
        )

        if not chemin.exists():
            return []

        try:
            with chemin.open(
                "r",
                encoding="utf-8",
            ) as fichier:

                donnees = json.load(
                    fichier
                )

                if isinstance(
                    donnees,
                    list,
                ):
                    return donnees

                return []

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return []

    def sauvegarder(
        self,
        nom_fichier,
        donnees,
    ):
        """
        Sauvegarde les données dans le fichier demandé.
        """

        chemin = self._chemin(
            nom_fichier
        )

        try:
            with chemin.open(
                "w",
                encoding="utf-8",
            ) as fichier:

                json.dump(
                    donnees,
                    fichier,
                    ensure_ascii=False,
                    indent=4,
                )

            return True

        except OSError:
            return False

    def supprimer(
        self,
        nom_fichier,
    ):
        """
        Supprime un fichier de stockage s'il existe.
        """

        chemin = self._chemin(
            nom_fichier
        )

        try:
            if chemin.exists():
                chemin.unlink()

            return True

        except OSError:
            return False
