import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Fond p",
                "Fond b",
                "Fond",
            )
sel_obj = Gui.Selection.getSelection()

part = addObjectPartBodyBox(dftStruct, App.ActiveDocument, "Caisson")

if sel_obj:
    Gui.Selection.addSelection(part)
    from FreeCAD_BespokeFurniture.PartBetween2Other import run_orchestrator
    run_orchestrator()