from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Mt i p",
                "Mt i b",
                "Mt i",
                "Mt i r1",
                "Mt i rainure",
            )

addObjectPartBodyBox(dftStruct, FreeCAD.ActiveDocument,"Caisson")


