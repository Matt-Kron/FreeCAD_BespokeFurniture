import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD_BespokeFurniture.lib_menuiserie import *
from FreeCAD_BespokeFurniture.Objects_classes import *

tab = Gui.Selection.getSelection()[0]
obj = bspfObj()
obj.object = find_additive_box(get_parent_part(tab))

for prop, exp in obj.object.ExpressionEngine:
    if "Length" == prop:
        tab_exp = exp
        break
for prop, exp in obj.part.ExpressionEngine:
    if ".Placement.Base.x" == prop:
        posX_exp = exp
        break

Gui.Selection.clearSelection()
# Gui.Selection.addSelection([obj.object.obj_gauche, obj.object.obj_droit])
if hasattr(obj.object, "obj_gauche"):
    Gui.Selection.addSelection(obj.object.obj_gauche)
    Gui.Selection.addSelection(obj.object.obj_droit)

from FreeCAD_BespokeFurniture.Ajouter_Tab import Add_tab
from FreeCAD_BespokeFurniture.Ajouter_TvInf import Add_TvInf
from FreeCAD_BespokeFurniture.Ajouter_TvSup import Add_TvSup
if "Tablette" in obj.object.Label:
    p = Add_tab()
if "Tv inf" in obj.object.Label:
    p = Add_TvInf()
if "Tv sup" in obj.object.Label:
    p = Add_TvSup()
obj2 = bspfObj()
obj2.object = find_additive_box(p)
prop_name = "longueur_avant_coupe"
obj.object.addProperty("App::PropertyLength", prop_name, "UserProp")
obj.object.setExpression(prop_name, tab_exp)
# obj.object.setExpression("Length", None)
obj.object.setExpression("Length", None)
obj.object.Length = 3/4 * obj.object.Length
# obj2.object.setExpression("Length", f"<<{obj.object.Label}>>.Length / <<{obj.object.Label}>>.{prop_name} * (1mm - <<{obj.object.Label}>>.{prop_name})")
obj2.object.setExpression("Length", f"<<{obj.object.Label}>>.{prop_name} - <<{obj.object.Label}>>.Length")
obj2.part.setExpression(".Placement.Base.x", f"<<{obj.part.Label}>>.Placement.Base.x + <<{obj.object.Label}>>.Length")
obj2.part.setExpression(".Placement.Base.z", f"<<{obj.part.Label}>>.Placement.Base.z")

