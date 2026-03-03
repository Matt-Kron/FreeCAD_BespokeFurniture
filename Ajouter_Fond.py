from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Fond p",
                "Fond b",
                "Fond",
            )
addObjectPartBodyBox(dftStruct, FreeCAD.ActiveDocument,"Caisson")
