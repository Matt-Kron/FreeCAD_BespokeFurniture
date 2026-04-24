import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

def Add_tab():
    dftStruct = (
                    "Tablette caisson p",
                    "Tablette caisson b",
                    "Tablette caisson",
                    "Tablette caisson r1",
                    "Tablette caisson rainure",
                )
    
    sel_obj = Gui.Selection.getSelection()
    
    part = addObjectPartBodyBox(dftStruct, App.ActiveDocument, "Caisson")
    
    if sel_obj:
        Gui.Selection.addSelection(part)
        import FreeCAD_BespokeFurniture.TabEntreDeuxMt as MacroHorizontal
        MacroHorizontal.run_assignment_macro()
    return part
        
if __name__ == "__main__":
    Add_tab()