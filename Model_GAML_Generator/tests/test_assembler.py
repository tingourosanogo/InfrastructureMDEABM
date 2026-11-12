# tests/test_assembler.py

import sys
import logging
import unittest
from pathlib import Path

# Configuration du chemin du projet
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
sys.path.insert(0, str(project_root))

# Imports du code métier
from src.model_intermediate.assembler import ModelAssembler
from src.model_intermediate.structures import SocioEcosystemModel

# Chemins absolus des données d'entrée
XMI_TEST_PATH = str(project_root / "input" / "modeleElevage_en.xmi")
INPUT_DIR     = str(project_root / "input")

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S"
)

class TestModelAssembler(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Vérifie que les fichiers d'entrée existent avant de lancer les tests."""
        missing = []
        if not Path(XMI_TEST_PATH).exists():
            missing.append(XMI_TEST_PATH)
        if not Path(INPUT_DIR).is_dir():
            missing.append(INPUT_DIR)
        if missing:
            raise FileNotFoundError(
                f"Fichiers / dossiers d'entrée manquants :\n" + "\n".join(missing)
            )

    def setUp(self):
        """Instancie l'assembleur et construit le modèle intermédiaire M'."""
        self.assembler = ModelAssembler(XMI_TEST_PATH, INPUT_DIR)
        self.model_m_prime: SocioEcosystemModel = self.assembler.assemble()

    def test_assemblage_success(self):
        """L'assemblage doit produire un modèle non vide."""
        self.assertIsInstance(self.model_m_prime, SocioEcosystemModel)
        self.assertGreater(len(self.model_m_prime.agents), 0,
                           "Aucun agent n'a été extrait du XMI.")
        self.assertGreater(len(self.model_m_prime.processes), 0,
                           "Aucun processus n'a été extrait du XMI.")
        self.assertGreater(len(self.model_m_prime.properties), 0,
                           "Aucune propriété/ressource n'a été extraite du XMI.")

    def test_agent_structure_fusion(self):
        """Vérifie la fusion XMI → AgentModel (position, actions, hiérarchie)."""
        agent_crop = next(
            (a for a in self.model_m_prime.agents.values() if a.name == "Crop"), None
        )
        self.assertIsNotNone(agent_crop, "Agent 'Crop' non trouvé.")
        self.assertIsNotNone(agent_crop.pos_x, "pos_x manquant.")
        self.assertIsNotNone(agent_crop.pos_y, "pos_y manquant.")

        self.assertGreater(len(agent_crop.actions), 0,
                           "Aucune action liée à l'agent 'Crop'.")
        self.assertTrue(
            any(p.name == "crop_production" for p in agent_crop.actions),
            "Processus 'crop_production' non lié à 'Crop'."
        )

        Biodiversity = next(
            (a for a in self.model_m_prime.agents.values() if a.name == "Biodiversity"), None
        )
        self.assertIsNotNone(Biodiversity, "Agent 'Biodiversity' non trouvé.")
        self.assertIsNotNone(Biodiversity.partOfParentAgent_ref,
                             "Référence parent manquante pour Biodiversity.")
        parent = self.model_m_prime.get_agent_by_id(Biodiversity.partOfParentAgent_ref)
        self.assertIsNotNone(parent, "Parent de Biodiversity non résolu.")
        self.assertTrue(parent.is_parent, "Le parent n'a pas été marqué comme parent.")

    ''' 
    def test_resource_initialization_fusion(self):
        """Vérifie le lien heldBy et la fusion de la valeur initiale (JSON)."""
        soil_nitrogen = next(
            (p for p in self.model_m_prime.properties.values() if p.name == "soil_nitrogen"), None
        )
        self.assertIsNotNone(soil_nitrogen, "Ressource 'soil_nitrogen' non trouvée.")
        self.assertTrue(soil_nitrogen.heldBy_refs,
                        "heldBy_refs vide pour 'soil_nitrogen'.")
        holder = self.model_m_prime.get_agent_by_id(soil_nitrogen.heldBy_refs[0])
        self.assertIsNotNone(holder, "Agent détenteur de 'soil_nitrogen' non résolu.")
        self.assertIn(soil_nitrogen, holder.attributes,
                      "'soil_nitrogen' n'est pas dans les attributes de son détenteur.")

        if soil_nitrogen.value is not None:
            self.assertIsInstance(soil_nitrogen.value, (int, float)),
            "La valeur initiale fusionnée doit être numérique."
    '''
    

    def test_global_data_fusion(self):
        """Vérifie la fusion des paramètres globaux, config spatio-temporelle et indicateurs."""
        self.assertGreaterEqual(len(self.model_m_prime.global_parameters), 0,
                                "Aucun paramètre global chargé.")
        self.assertTrue(
            any(p.get("name") == "natural_litter_to_c" for p in self.model_m_prime.global_parameters),
            "Paramètre 'natural_litter_to_c' manquant."
        )

        temporal = self.model_m_prime.initialization_config.get("temporal", {})
        self.assertIn("time_step", temporal,
                      "Clé 'time_step' absente de la configuration temporelle.")
        self.assertEqual(temporal.get("time_step"), "1 day",
                         "Valeur de 'time_step' incorrecte.")

        self.assertGreater(len(self.model_m_prime.indicators), 0,
                           "Aucun indicateur chargé.")
        self.assertTrue(
            any(i.get("id") == "PA.01.01" for i in self.model_m_prime.indicators),
            "Indicateur 'PA.01.01' manquant."
        )

        self.assertIsInstance(self.model_m_prime.scenarios, list)

    def test_unresolved_references_warning(self):
        """Le logger doit émettre un warning si des références restent non résolues."""
        with self.assertLogs(level="WARNING") as cm:
            temp_assembler = ModelAssembler(XMI_TEST_PATH, INPUT_DIR)
            temp_model = temp_assembler.assemble()  # On récupère le modèle pour vérifier

        # Calcul des références non résolues depuis le modèle
        unresolved_refs = [
            ref for agent in temp_model.agents.values()
            for ref in (agent.partOfParentAgent_ref,) if ref and ref not in temp_model.agents
        ]

        if unresolved_refs:
            self.assertTrue(
                any("non résolus" in msg for msg in cm.output),
                "Warning de référence non résolue attendu mais absent."
            )
        else:
            # Utilisation correcte du logger
            logging.getLogger(__name__).info(
                "Pas de références non résolues – dataset valide, test OK."
            )

            
if __name__ == "__main__":
    unittest.main(verbosity=2)