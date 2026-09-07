import FreeCAD as App
import FreeCADGui as Gui
from add_object_lib import addObjectPartBodyBox

def Add_TvSup():
    dftStruct = (
                    "Tv sup p",
                    "Tv sup b",
                    "Tv sup",
                    "Tv sup rainuree",
                )

    # sel_obj = Gui.Selection.getSelection()

    part = addObjectPartBodyBox(dftStruct, App.ActiveDocument, "Caisson")

    # if sel_obj:
    #     Gui.Selection.addSelection(part)
    #     import MtEntreDeuxTv as MacroVertical
    #     MacroVertical.run_assignment_macro()
    return part

if __name__ == "__main__":
    Add_TvSup()
