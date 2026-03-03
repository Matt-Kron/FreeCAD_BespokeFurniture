from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Porte p",
                "Porte b",
                "Porte",
                "Porte param",
            )
addObjectPartBodyBox(dftStruct, FreeCAD.ActiveDocument,"Caisson")
