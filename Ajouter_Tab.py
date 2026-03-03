from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Tablette caisson p",
                "Tablette caisson b",
                "Tablette caisson",
                "Tablette caisson r1",
                "Tablette caisson rainure",
            )

addObjectPartBodyBox(dftStruct, FreeCAD.ActiveDocument,"Caisson")
