import FreeCAD as App
import FreeCADGui as Gui
from add_object_lib import addObjectPartBodyBox
from lib_menuiserie import get_caisson_from_selection

dftStruct = (
                "Porte p",
                "Porte b",
                "Porte",
                "Porte param",
            )

def main():
    sel_obj = Gui.Selection.getSelection()
    caisson = get_caisson_from_selection(sel_obj)
    conteneur = caisson.Label if caisson else "Caisson"
    part = addObjectPartBodyBox(dftStruct, App.ActiveDocument, conteneur)
    if sel_obj:
        Gui.Selection.addSelection(part)
        from PartBetween2Other import run_orchestrator
        run_orchestrator()

if __name__ == "__main__":
    main()
