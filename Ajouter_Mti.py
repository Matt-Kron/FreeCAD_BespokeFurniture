import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Mt i p",
                "Mt i b",
                "Mt i",
                "Mt i r1",
                "Mt i rainure",
            )

sel_obj = Gui.Selection.getSelection()

part = addObjectPartBodyBox(dftStruct, App.ActiveDocument, "Caisson")

if sel_obj:
    Gui.Selection.addSelection(part)
    import FreeCAD_BespokeFurniture.MtEntreDeuxTv as MacroVertical
    MacroVertical.run_assignment_macro()


