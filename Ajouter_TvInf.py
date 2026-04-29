import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

def Add_TvInf():
    dftStruct = (
                    "Tv inf p",
                    "Tv inf b",
                    "Tv inf",
                    "Tv inf rainuree",
                )

    # sel_obj = Gui.Selection.getSelection()

    part = addObjectPartBodyBox(dftStruct, App.ActiveDocument, "Caisson")

    # if sel_obj:
    #     Gui.Selection.addSelection(part)
    #     import FreeCAD_BespokeFurniture.MtEntreDeuxTv as MacroVertical
    #     MacroVertical.run_assignment_macro()
    return part

if __name__ == "__main__":
    Add_TvInf()
