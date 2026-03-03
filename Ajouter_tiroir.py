from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Tiroir p",
                "Tiroir b",
                "Tiroir",
                "Tiroir param",
            )
addObjectPartBodyBox(dftStruct, FreeCAD.ActiveDocument,"Caisson")
