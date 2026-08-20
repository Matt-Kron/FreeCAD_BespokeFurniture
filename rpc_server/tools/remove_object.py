import FreeCAD, FreeCADGui
from FreeCAD_BespokeFurniture.lib_menuiserie import find_additive_box, get_parent_part, getObjTag, msgCsl, userMsg


TOOL_META = {
        "name": "remove_object",
        "description": "Supprime un composant de meuble dans FreeCAD",
        "parameters": {
            "object_label": {
                "type": "str",
                "description": "l'étiquette - label - de l'objet à supprimer. ne peut pas être le nom d'une alvéole, doit être le nom d'un segment interne à la structure"
            }
        }
}

def gui_remove():
    sel_obj = FreeCADGui.Selection.getSelection()
    for obj in sel_obj:
        run(obj.Label)

def run(object_label: str) -> dict:

    obj = FreeCAD.ActiveDocument.getObjectsByLabel(object_label)[0]
    obj_parent = get_parent_part(obj)
    box = find_additive_box(obj_parent)
    obj_tag = getObjTag(box)
    label = obj_parent.Label
    if not "O" in obj_tag["type"]:
        userMsg(f"L'objet {label} ne peut pas être supprimé, ce n'est pas un composant du meuble")
        return  {
               "status": "failed",
               "label": label,
               "description": "L'objet ne peut pas être supprimé, ce n'est pas un composant du meuble"
        }
    obj_parent.removeObjectsFromDocument()
    FreeCAD.ActiveDocument.removeObject(obj_parent.Name)
    return {
        "status": "success",
        "label": label,
        # "dimensions": [obj.Length.Value, obj.Width.Value, obj.Height.Value],
        # "position": [x, y, z]
    }
