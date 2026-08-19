import unittest
import json
import urllib.request
from pathlib import Path

RPC_URL = "http://127.0.0.1:9147"

DIRPATH = Path(__file__).parent

TEST_MODEL = DIRPATH / "Test_Modele_caisson_parts_FC1-1-0_v7.FCStd"
TEST_MODEL_PENTEG = DIRPATH / "Test_Modele_caisson_pente-gauche_v2.FCStd"
TEST_MODEL_PENTED = DIRPATH / "Test_Modele_caisson_pente-droite_v1-1_FC1.FCStd"

def rpc_call(method: str, params: list = None):
    """Client HTTP JSON-RPC minimaliste pour les tests."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or [],
        "id": 1
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(RPC_URL, data=data, headers={'Content-Type': 'application/json'})
    print(data)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

class TestFreeCADRPCServer(unittest.TestCase):

    func_obj_list = [
                        ["Montant", "Mt i p001"],
                        ["Tablette", "Tablette caisson p004"],
                        # ["Fond", "Fond p001"],
                        # ["Porte", "Porte p"],
                        # ["Tiroir", "Tiroir p"]
    ]

    def setUp(self):
        """Réinitialise le document avant chaque test."""
        # FreeCAD.openDocument(TEST_MODEL)
        # test_model = TEST_MODEL.stem
        # FreeCAD.activeDocument(test_model)
        pass

    def test_add_object(self):
        for obj_type, label in self.func_obj_list:
            if label == "Tablette caisson p004":
                res =  rpc_call("add_object", [obj_type, "Caisson", ["Mt i p", "Mt d p"]])
            else:
                res =  rpc_call("add_object", [obj_type, "Caisson"])
            result = res["result"]
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["label"], label)
            self.assertEqual(result["type"], obj_type)

    def test_move_object(self):
        res = rpc_call("move_object", ["Tablette caisson p003", 200])
        result = res["result"]
        self.assertEqual(result["status"], "user_request")
        res = rpc_call("move_object", ["Tablette caisson p003", 200, True])
        result = res["result"]
        self.assertEqual(result["status"], "success")

    def test_lier_objets(self):
        res = rpc_call("lier_objets", [["Mt i p001", "Tablette caisson p001", "Tablette caisson p002"]])
        result = res["result"]
        self.assertEqual(result["message"], "Liaison des 3 objets effectuée")
        self.assertEqual(result["status"], "success")

    # def test_remove_object(self):
    #     for obj_type, label in self.func_obj_list:
    #         if not label == "Tablette caisson p004":
    #             res =  rpc_call("remove_object", [label])
    #             result = res["result"]
    #             self.assertEqual(result["status"], "success")
    #             self.assertEqual(result["label"], label)

    # def test_01_add_component(self):
    #     """Test de la création d'un panneau verticall."""
    #     res = rpc_call("add_component", ["montant", "Cote_Gauche", 0.0, 0.0, 0.0])
    #     self.assertNotIn("error", res)

    #     result = res["result"]
    #     self.assertEqual(result["status"], "created")
    #     self.assertEqual(result["name"], "Cote_Gauche")
    #     self.assertEqual(result["dimensions"], [18.0, 400.0, 800.0])

    # def test_02_update_dimensions(self):
    #     """Test de la mise à jour des dimensions d'un objet existant."""
    #     rpc_call("add_component", ["traverse", "Etagere_1", 0.0, 0.0, 200.0])

    #     # Modification de la longueur
    #     res = rpc_call("update_dimensions", ["Etagere_1", 900.0, None, None])
    #     self.assertNotIn("error", res)

    #     result = res["result"]
    #     self.assertEqual(result["status"], "updated")
    #     self.assertEqual(result["dimensions"], [900.0, 380.0, 18.0])

    # def test_03_get_document_tree(self):
    #     """Test de la récupération de l'arbre d'objets."""
    #     res = rpc_call("get_document_tree")
    #     self.assertNotIn("error", res)

    #     tree = res["result"]
    #     self.assertIn("document", tree)
    #     self.assertIn("objects", tree)
    #     self.assertIsInstance(tree["objects"], list)

    def test_04_method_not_found(self):
        """Test de la Fondtion d'erreur sur une méthode inexistante."""
        res = rpc_call("invalide_method")
        self.assertIn("error", res)
        self.assertEqual(res["error"]["code"], -32601)

    # def test_05_update_non_existing_object(self):
    #     """Test d'erreur lors de la modification d'un objet introuvable."""
    #     res = rpc_call("update_dimensions", ["ObjetFantome", 100.0, 100.0, 100.0])
    #     self.assertIn("error", res)
    #     self.assertIn("introuvable", res["error"]["message"])

    # def test_get_geo_structure_check(self):
    #         """Test la génération de la géométrie simplifiée"""
    #         rpc_call("get_geo_structure", [])

if __name__ == "__main__":
    unittest.main()
