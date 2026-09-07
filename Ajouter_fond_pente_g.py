import FreeCAD as App
import FreeCADGui as Gui
from add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Fond pente G p",
                "Fond pente G b",
                "Fond pente G",
                "Fond pente G coupee",
            )

def main():
    sel_obj = Gui.Selection.getSelection()
    part = addObjectPartBodyBox(dftStruct, App.ActiveDocument,"Caisson")
    if sel_obj:
        Gui.Selection.addSelection(part)
        from PartBetween2Other import run_orchestrator
        run_orchestrator()

if __name__ == "__main__":
    main()
