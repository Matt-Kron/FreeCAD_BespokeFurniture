import FreeCAD
from ...lib_menuiserie import get_parent_part

def get_document_tree():
    doc = FreeCAD.ActiveDocument
    if not doc:
        return {"document": None, "objects": []}

    objects_data = []
    for obj in doc.Objects:
        if hasattr(obj, "BOM_mat"):
            parent_part = get_parent_part(obj)
            conteneur = get_parent_part(parent_part).Label or None
            objects_data.append({
                "name": parent_part.Name,
                "label": parent_part.Label,
                "parent": conteneur
                # "dimensions": [obj.Length.Value, obj.Width.Value, obj.Height.Value],
                # "position": [obj.Placement.Base.x, obj.Placement.Base.y, obj.Placement.Base.z]
            })
    return {"document": doc.Name, "objects": objects_data}
