import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Porte pente G p",
                "Porte pente G b",
                "Porte pente G",
                "Porte pente G coupee",
                "Porte pente G param",
            )

sel_obj = Gui.Selection.getSelection()
part = addObjectPartBodyBox(dftStruct, FreeCAD.ActiveDocument,"Caisson")
if sel_obj:
    Gui.Selection.addSelection(part)
    from FreeCAD_BespokeFurniture.PartBetween2Other import run_orchestrator
    run_orchestrator()
