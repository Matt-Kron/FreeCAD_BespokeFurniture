import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

def Add_mti_pente():
    dftStruct = (
                    "Mt i pente p",
                    "Mt i pente b",
                    "Mt i pente",
                    "Mt i pente r1",
                    "Mt i pente rainure",
                )

    sel_obj = Gui.Selection.getSelection()

    part = addObjectPartBodyBox(dftStruct, App.ActiveDocument, "Caisson")

    if sel_obj:
        Gui.Selection.addSelection(part)
        import FreeCAD_BespokeFurniture.MtPenteSurTvInf as MacroVertical
        MacroVertical.run_assignment_macro()
    return part

if __name__ == "__main__":
    Add_mti_pente()
