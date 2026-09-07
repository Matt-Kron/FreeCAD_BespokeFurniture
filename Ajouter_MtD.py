import FreeCAD as App
import FreeCADGui as Gui
from add_object_lib import addObjectPartBodyBox

def Add_mtd():
    dftStruct = (
                    "Mt d p",
                    "Mt d b",
                    "Mt d",
                    "Mt d rainure",
                )

    sel_obj = Gui.Selection.getSelection()

    part = addObjectPartBodyBox(dftStruct, App.ActiveDocument, "Caisson")

    if sel_obj:
        Gui.Selection.addSelection(part)
        import MtEntreDeuxTv as MacroVertical
        MacroVertical.run_assignment_macro()
    return part

if __name__ == "__main__":
    Add_mtd()
