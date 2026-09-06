import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Porte p",
                "Porte b",
                "Porte",
                "Porte param",
            )

def main():
    sel_obj = Gui.Selection.getSelection()
    part = addObjectPartBodyBox(dftStruct, App.ActiveDocument,"Caisson")
    if sel_obj:
        Gui.Selection.addSelection(part)
        from FreeCAD_BespokeFurniture.PartBetween2Other import run_orchestrator
        run_orchestrator()

if __name__ == "__main__":
    main()
