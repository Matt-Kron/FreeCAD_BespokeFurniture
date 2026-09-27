import FreeCAD as App
import FreeCADGui as Gui
from add_object_lib import addObjectPartBodyBox
from lib_menuiserie import get_caisson_from_selection

def Add_TvInf():
    dftStruct = (
                    "Tv inf p",
                    "Tv inf b",
                    "Tv inf",
                    "Tv inf rainuree",
                )

    sel_obj = Gui.Selection.getSelection()
    caisson = get_caisson_from_selection(sel_obj)
    conteneur = caisson.Label if caisson else "Caisson"
    part = addObjectPartBodyBox(dftStruct, App.ActiveDocument, conteneur)

    # if sel_obj:
    #     Gui.Selection.addSelection(part)
    #     import MtEntreDeuxTv as MacroVertical
    #     MacroVertical.run_assignment_macro()
    return part

if __name__ == "__main__":
    Add_TvInf()
