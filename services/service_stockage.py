"""
services/service_stockage.py

Service local de stockage JSON.
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
        return self.dossier / nom_fichier

    def charger(self, nom_fichier):
        chemin = self._chemin(nom_fichier)

        if not chemin.exists():
            return []

        try:
            with chemin.open(
                "r",
                encoding="utf-8",
            ) as fichier:
                return json.load(fichier)

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
        chemin = self._chemin(nom_fichier)

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
