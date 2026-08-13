import FreeCAD

from FreeCAD_BespokeFurniture.rpc_server.extract_segments_alveoles import set_alveole_role

# Descripteur
TOOL_META = {
        "name": "set_alveole_role",
        "description": """Modifie le rôle d'une alvéole pour guider la conception. Exemple: penderie, bandes dessinées, livres de poche, vêtements...""",
        "parameters": {
            "alveole_id": {
                "type": "str",
                "description": "Identifiant de l'alvéole, de type D3, lettre + indice"
            },
            "role": {
                "type": "str",
                "description": "La fonction de l'alvéole, le rôle du compartiment"
            }
        }
}

def run(alveole_id: str, role: str) -> dict:

    result  = set_alveole_role(FreeCAD.ActiveDocument, alveole_id, role)

    return {
        "status": "success" if result else "failed",
        "alveole_id": alveole_id,
        "role": role
        # "dimensions": [obj.Length.Value, obj.Width.Value, obj.Height.Value],
        # "position": [x, y, z]
    }
