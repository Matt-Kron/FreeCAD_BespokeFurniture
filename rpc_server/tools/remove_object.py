import FreeCAD

def remove_object(object_label: str):

    obj = FreeCAD.ActiveDocument.getObjectsByLabel(object_label)[0]
    label = obj.Label
    obj.removeObjectsFromDocument()
    FreeCAD.ActiveDocument.removeObject(obj.Name)
    return {
        "status": "removed",
        "label": label,
        # "dimensions": [obj.Length.Value, obj.Width.Value, obj.Height.Value],
        # "position": [x, y, z]
    }
