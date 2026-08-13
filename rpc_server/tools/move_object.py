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
                "description": "[1er argument - OBLIGATOIRE EN PREMIER] L'étiquette (label) de l'élément à déplacer"
            },
            "value": {
                "type": "float",
                "description": "[2ème argument] Indique le déplacement à effectuer. La valeur est relative, elle sera ajoutée à la position de l'élément."
            },
            "user_confirmation": {
                "type": "bool",
                "description": "[3ème argument - OBLIGATOIRE EN DERNIER] Indique si l'utilisateur a confirmé d'écraser la formule"
            }
        }
}

def run(object_label: str, value: float, user_confirmation: bool = False) -> dict:
    print(f"move_object object_label: {object_label}, value: {value}, user_confirmation: {user_confirmation} ")
    # 1. Vérification sécurisée de l'existence de l'objet
    objs = FreeCAD.ActiveDocument.getObjectsByLabel(object_label)
    if not objs:
        raise ValueError(f"L'objet n'est pas déplaçable: l'étiquette '{object_label}' ne correspond à aucun objet")
    obj = objs[0]

    parent_obj = get_parent_part(obj)
    obj_box = find_additive_box(parent_obj)
    tag_prop = getObjTag(obj_box)

    msgCsl(tag_prop["type"][-1])
    if int(tag_prop["type"][-1]) != 2:
        raise ValueError("L'objet n'est pas déplaçable: l'objet n'est pas valide")

    # 2. Détermination de l'axe
    if tag_prop["type"][1] == "V":
        axis = "x"
    elif tag_prop["type"][1] == "H":
        axis = "z"
    else:
        axis = "x"  # Axe par défaut de sécurité

    # 3. Vérification de la demande de confirmation
    placement_prop = f"Placement.Base.{axis}"
    status = "failed"

    for prop_name, exp in parent_obj.ExpressionEngine:
        if placement_prop in prop_name:
            if not user_confirmation:
                status = "user_request"
            break

    # 4. Exécution du déplacement si confirmé (ou pas de formule bloquante)
    if status == "user_request":
        return {
            "status": "user_request",
            "description": f"Le déplacement de {value} mm sur l'axe {axis.upper()} nécessite une confirmation de l'utilisateur."
        }

    # Récupération et mise à jour effective dans FreeCAD
    position = getattr(parent_obj.Placement.Base, axis)
    parent_obj.setExpression("Placement.Base." + axis, None)

    new_base = parent_obj.Placement.Base
    setattr(new_base, axis, position + value)
    parent_obj.Placement.Base = new_base

    # Recalcul de la scène 3D
    FreeCAD.ActiveDocument.recompute()
    status = "success"

    return {
        "status": status,
        "description": f"L'objet '{object_label}' a bien été déplacé de {value} mm sur l'axe {axis.upper()}.",
    }
