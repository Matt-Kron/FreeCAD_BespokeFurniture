import FreeCAD

TOOL_META = {
        "name": "remove_object",
        "description": "Supprime un composant de meuble dans FreeCAD",
        "parameters": {
            "object_label": {
                "type": "str",
                "description": "l'étiquette - label - de l'objet à supprimer"
            }
        }
}

def run(object_label: str) -> dict:

    obj = FreeCAD.ActiveDocument.getObjectsByLabel(object_label)[0]
    label = obj.Label
    obj.removeObjectsFromDocument()
    FreeCAD.ActiveDocument.removeObject(obj.Name)
    return {
        "status": "success",
        "label": label,
        # "dimensions": [obj.Length.Value, obj.Width.Value, obj.Height.Value],
        # "position": [x, y, z]
    }
