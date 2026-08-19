import FreeCAD

from FreeCAD_BespokeFurniture import add_object_lib
from FreeCAD_BespokeFurniture.PartBetween2Other import run_orchestrator_by_labels
from add_object_lib import addObjectPartBodyBox

# Descripteur
TOOL_META = {
        "name": "add_object",
        "description": """Ajoute un composant de meuble dans FreeCAD (Montant, Tablette, Porte, Tiroir, Fond), relié à plusieurs autres composants.
                Un composant doit être ajouter à un sous-ensemble de type Caisson.
                Le composant doit être relié à d'autres composants:
                    un montant est relié à 2 traverses ou tablettes,
                    une tablette ou traverse est reliée à 2 montants,
                    Une porte, un tiroir ou un fond est reliée à 4 objets qui l'encadrent: 2 montants et 2 traverses
                Exemple pour un montant:
                    object_type = Montant
                    parent_obj_label = Caisson
                    labels = ["Tv inf p", "Tablette caisson p"]
                Exemple pour un fond:
                    object_type = Fond
                    parent_obj_label = Caisson
                    labels = ["Tv inf p", "Tablette caisson p", "Mt g p", "Mt i p"]""",
        "parameters": {
            "object_type": {
                "type": "str",
                "enum": ["Montant", "Tablette", "Porte", "Tiroir", "Fond"],
                "description": "Le type de composant à ajouter"
            },
            "parent_obj_label": {
                "type": "str",
                "default": "Caisson",
                "description": "Label de l'objet parent dans l'arbre FreeCAD"
            },
            "labels": {
                "type": "list[str]",
                "description": "Liste des labels des objets FreeCAD à lier (3 ou 5 objets requis)"
            }
        }
}

MAP_OBJECT_TYPE_LINKED_OBJECTS = {
    "Montant": ["Tv inf p", "Tv sup p"],
    "Tablette": ["Mt g p", "Mt d p"],
    "Porte": ["Tv inf p", "Tv sup p", "Mt g p", "Mt d p"],
    "Tiroir": ["Tv inf p", "Tv sup p", "Mt g p", "Mt d p"],
    "Fond": ["Tv inf p", "Tv sup p", "Mt g p", "Mt d p"]
}

# Dictionnaire des structures dftStruct pour chaque fichier Ajouter_*
DFT_STRUCT_MAP = {
    "Fond": (
        "Fond p",
        "Fond b",
        "Fond",
    ),
    "Montant": (
        "Mt i p",
        "Mt i b",
        "Mt i",
        "Mt i r1",
        "Mt i rainure",
    ),
    "Ajouter_Mti_pente": (
        "Mt i pente p",
        "Mt i pente b",
        "Mt i pente",
        "Mt i pente r1",
        "Mt i pente rainure",
    ),
    "Ajouter_Mti_penteG": (
        "Mt i pente G p",
        "Mt i pente G b",
        "Mt i pente G",
        "Mt i pente G r1",
        "Mt i pente G rainure",
    ),
    "Tablette": (
        "Tablette caisson p",
        "Tablette caisson b",
        "Tablette caisson",
        "Tablette caisson r1",
        "Tablette caisson rainure",
    ),
    "Ajouter_TvInf": (
        "Tv inf p",
        "Tv inf b",
        "Tv inf",
        "Tv inf rainuree",
    ),
    "Ajouter_TvSup": (
        "Tv sup p",
        "Tv sup b",
        "Tv sup",
        "Tv sup rainuree",
    ),
    "Ajouter_fond_pente_g": (
        "Fond pente G p",
        "Fond pente G b",
        "Fond pente G",
        "Fond pente G coupee",
    ),
    "Porte": (
        "Porte p",
        "Porte b",
        "Porte",
        "Porte param",
    ),
    "Ajouter_porte_pente_g": (
        "Porte pente G p",
        "Porte pente G b",
        "Porte pente G",
        "Porte pente G coupee",
        "Porte pente G param",
    ),
    "Tiroir": (
        "Tiroir p",
        "Tiroir b",
        "Tiroir",
        "Tiroir param",
    ),
}

def run(object_type: str, parent_obj_label: str = "Caisson", labels: list[str] = []) -> dict:

    part = addObjectPartBodyBox(DFT_STRUCT_MAP[object_type], FreeCAD.ActiveDocument, "Caisson")
    if labels and part:
        labels.append(part.Label)
        print(f"add_object: run_orchestrator_by_labels {labels} ")
        run_orchestrator_by_labels(labels)

    linked_labels = labels if labels else MAP_OBJECT_TYPE_LINKED_OBJECTS[object_type]

    return {
        "status": "success",
        "label": part.Label,
        "type": object_type,
        "links": f"object linked to "
        # "dimensions": [obj.Length.Value, obj.Width.Value, obj.Height.Value],
        # "position": [x, y, z]
    }
