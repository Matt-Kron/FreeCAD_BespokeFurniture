import FreeCAD

# from FreeCAD_BespokeFurniture import add_object_lib
from FreeCAD_BespokeFurniture.lib_menuiserie import find_additive_box, get_parent_part, getObjTag, msgCsl

# Descripteur
TOOL_META = {
        "name": "move_object",
        "description": """
            Déplace un objet selon sa nature:
                - seuls les montants et les traverses internes au meuble sont déplaçables.
                - les traverses supérieure et inférieure changent en fonction de paramètres globaux du meuble, ainsi que les montants gauche et droit.
                  Ce sont les composants qui constituent le cadre du caisson qui ne sont pas modifiables directement.
                - un montant peut être déplacé horizontalement, selon l'axe X
                - une tablette ou traverse peut être déplacée verticalement, selon l'axe Z
                - si l'outil retourne le statut "user_request", la position de l'élément est définie par une expression dans FreeCAD,
                  il faut demander l'accord de l'utilisateur pour écraser la formule et modifier la propriété "user_confirmation" à Vrai

        """,
        "parameters": {
            "object_label": {
                "type": "str",
                "description": "L'étiquette (label) de l'élément à déplacer"
            },
            "value": {
                "type": "float",
                "description": "Indique le déplacement à effecture. La veleur sera ajoutée à la position de l'élément."
            },
            "user_confirmation": {
                "type": "bool",
                "description": "Indique si l'utilisateur à confirmer d'écraser la formule"
            }
        }
}

def run(object_label: str, value: float, user_confirmation: bool = False) -> dict:

    obj = FreeCAD.ActiveDocument.getObjectsByLabel(object_label)[0]
    if not obj:
        erreur = "l'étiquette ne correspond à aucun objet"
        raise ValueError(f"L'objet n'est pas déplaçable: {erreur}")

    parent_obj = get_parent_part(obj)
    obj_box = find_additive_box(parent_obj)
    tag_prop = getObjTag(obj_box)
    msgCsl(tag_prop["type"][-1])
    if int(tag_prop["type"][-1]) != 2:
        erreur = "l'objet n'est pas valide"
        raise ValueError(f"L'objet n'est pas déplaçable: {erreur}")

    status = "failed"
    if tag_prop["type"][1] == "V":
        axis = "x"
    elif tag_prop["type"][1] == "H":
        axis = "z"
    placement_prop = f"Placement.Base.{axis}"
    for prop_name, exp in parent_obj.ExpressionEngine:
        if placement_prop in prop_name:
            if not user_confirmation:
                status = "user_request"
            break
    if not status == "user_request":
        position = getattr(parent_obj.Placement.Base, axis)
        parent_obj.setExpression("Placement.Base." + axis, None)
        setattr(parent_obj.Placement.Base, axis, position + value)
        status = "success"

    return {
        "status": status, # success, failed or user_request
        "description": f"L'objet a bien été déplacé de {value}",
    }
