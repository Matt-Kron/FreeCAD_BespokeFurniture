import FreeCAD as App
import FreeCADGui as Gui
from add_object_lib import addObjectPartBodyBox
from lib_menuiserie import get_caisson_from_selection

def Add_tab():
    dftStruct = (
                    "Tablette caisson p",
                    "Tablette caisson b",
                    "Tablette caisson",
                    "Tablette caisson r1",
                    "Tablette caisson rainure",
                )

    sel_obj = Gui.Selection.getSelection()
    caisson = get_caisson_from_selection(sel_obj)
    conteneur = caisson.Label if caisson else "Caisson"
    part = addObjectPartBodyBox(dftStruct, App.ActiveDocument, conteneur)

    if sel_obj:
        Gui.Selection.addSelection(part)
        import TabEntreDeuxMt as MacroHorizontal
        MacroHorizontal.run_assignment_macro()
    return part

if __name__ == "__main__":
    Add_tab()
