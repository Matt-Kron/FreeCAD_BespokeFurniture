import FreeCAD

from FreeCAD_BespokeFurniture import add_object_lib
from add_object_lib import addObjectPartBodyBox

# Descripteur
TOOL_META = {
        "name": "add_object",
        "description": """Ajoute un composant de meuble dans FreeCAD (Montant, Tablette, Porte, Tiroir).""",
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
            }
        }
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

def run(object_type: str, parent_obj_label: str = "Caisson") -> dict:

    part = addObjectPartBodyBox(DFT_STRUCT_MAP[object_type], FreeCAD.ActiveDocument, parent_obj_label)

    return {
        "status": "success",
        "label": part.Label,
        "type": object_type
        # "dimensions": [obj.Length.Value, obj.Width.Value, obj.Height.Value],
        # "position": [x, y, z]
    }
