import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Tiroir p",
                "Tiroir b",
                "Tiroir",
                "Tiroir param",
            )

sel_obj = Gui.Selection.getSelection()
part = addObjectPartBodyBox(dftStruct, FreeCAD.ActiveDocument,"Caisson")
if sel_obj:
    Gui.Selection.addSelection(part)
    from FreeCAD_BespokeFurniture.PartBetween2Other import run_orchestrator
    run_orchestrator()