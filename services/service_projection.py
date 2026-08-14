from modeles.simulation import Simulation
from services.service_stockage import ServiceStockage
from services.calcul_projection import CalculProjection


class ServiceProjection:

    _instance = None


    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(cls)

            cls._instance.dernier_resultat = None
            cls._instance.simulations = []
            cls._instance.stockage = ServiceStockage()

            cls._instance._charger()

        return cls._instance



    def _charger(self):

        donnees = self.stockage.charger(
            "simulations.json"
        )

        self.simulations = []

        if not donnees:
            return


        for element in donnees:

            try:

                simulation = Simulation.from_dict(
                    element
                )

                self.simulations.append(
                    simulation
                )

            except Exception:

                pass


        if self.simulations:

            self.dernier_resultat = (
                self.simulations[-1]
            )



    def calculer(
        self,
        capital_initial,
        versement_mensuel,
        taux_annuel,
        duree,
    ):

        simulation = CalculProjection.calculer(
            capital_initial,
            versement_mensuel,
            taux_annuel,
            duree,
        )

        self.dernier_resultat = simulation

        return simulation



    def calculer_scenarios(
        self,
        capital_initial,
        versement_mensuel,
        taux_annuel,
        duree,
    ):

        scenarios = {}


        scenarios["prudent"] = CalculProjection.calculer(
            capital_initial,
            versement_mensuel,
            taux_annuel * 0.7,
            duree,
        )


        scenarios["normal"] = CalculProjection.calculer(
            capital_initial,
            versement_mensuel,
            taux_annuel,
            duree,
        )


        scenarios["optimiste"] = CalculProjection.calculer(
            capital_initial,
            versement_mensuel,
            taux_annuel * 1.3,
            duree,
        )


        return scenarios



    def _sauvegarder(self):

        donnees = [

            simulation.to_dict()

            for simulation in self.simulations

        ]


        self.stockage.sauvegarder(
            "simulations.json",
            donnees,
        )



    def ajouter_simulation(
        self,
        simulation,
    ):

        self.simulations.append(
            simulation
        )

        self.dernier_resultat = simulation

        self._sauvegarder()



    def obtenir_simulations(self):

        return self.simulations



    def obtenir_simulation(
        self,
        index,
    ):

        if 0 <= index < len(self.simulations):

            return self.simulations[index]

        return None



    def supprimer_simulation(
        self,
        index,
    ):

        if 0 <= index < len(self.simulations):

            del self.simulations[index]


            if self.simulations:

                self.dernier_resultat = (
                    self.simulations[-1]
                )

            else:

                self.dernier_resultat = None


            self._sauvegarder()



    def vider(self):

        self.simulations.clear()

        self.dernier_resultat = None

        self._sauvegarder()



    def obtenir_dernier_resultat(self):

        return self.dernier_resultat
