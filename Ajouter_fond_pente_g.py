import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Fond pente G p",
                "Fond pente G b",
                "Fond pente G",
                "Fond pente G coupee",
            )

sel_obj = Gui.Selection.getSelection()
part = addObjectPartBodyBox(dftStruct, FreeCAD.ActiveDocument,"Caisson")
if sel_obj:
    Gui.Selection.addSelection(part)
    from FreeCAD_BespokeFurniture.PartBetween2Other import run_orchestrator
    run_orchestrator()
