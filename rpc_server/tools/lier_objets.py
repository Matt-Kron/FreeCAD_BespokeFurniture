import FreeCAD
from FreeCAD_BespokeFurniture.PartBetween2Other import run_orchestrator_by_labels

# Descripteur
TOOL_META = {
    "name": "lier_objets",
    "description": """Assigne à un objet donnée les autres objets qui définissent ses dimensions.
                    Par exemple avec 3 objets (2 tablettes et 1 montant), le montant sera positionné entre les 2 tablettes.
                    Avec 5 objets (1 porte et 4 parois), les 4 parois seront assignées aux propriétés de la porte.""",
    "parameters": {
        "labels": {
            "type": "list[str]",
            "description": "Liste des labels des objets FreeCAD à lier (3 ou 5 objets requis)"
        }
    }
}

def run(labels: list[str]) -> dict:
    run_orchestrator_by_labels(labels)
    return {
        "status": "success",
        "message": f"Liaison des {len(labels)} objets effectuée",
        "labels": labels
    }
