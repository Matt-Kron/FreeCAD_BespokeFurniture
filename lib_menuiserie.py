import FreeCAD as App
import FreeCADGui as Gui
import os

ADD_OBJECT_PARAM_FILE = "config_macro_caisson.cfg"
BF_MACROS_PATH = os.path.dirname(__file__)

# Group , Name, Type, Prefix
EDGEBAND_PROPERTIES = {
                        "Avant" :   {
                                    "Group" : "EdgeBands",
                                    "Name"  : "Avant",
                                    "Type"  : "App::PropertyBool",
                                    "Prefix": True,
                                    },
                        "Arriere" :   {
                                    "Group" : "EdgeBands",
                                    "Name"  : "Arriere",
                                    "Type"  : "App::PropertyBool",
                                    "Prefix": True,
                                    },
                        "Gauche" :   {
                                    "Group" : "EdgeBands",
                                    "Name"  : "Gauche",
                                    "Type"  : "App::PropertyBool",
                                    "Prefix": True,
                                    },
                        "Droit" :   {
                                    "Group" : "EdgeBands",
                                    "Name"  : "Droit",
                                    "Type"  : "App::PropertyBool",
                                    "Prefix": True,
                                    },
                       }

WOODPANELS_VarSet = "PanneauManager"
WOODPANELS_ListProperty = "liste_panneaux"

# Type, Name, Group, Description, Value
USER_PROPERTIES = (
                    ("App::PropertyBool", "BOM_destination", "UserProp", "Property to filter objects for BOM", True),
                    ("App::PropertyEnumeration", "BOM_mat", "UserProp", "Material name", []),
                    ("App::PropertyInteger", "BOM_quantity", "UserProp", "Part quantity to consider in BOM", 1),
                    ("App::PropertyBool", "Nesting", "UserProp", "Property to filter objects to nest", True),
                    ("App::PropertyBool", "Nest_Allow_Rotation", "UserProp", "Allow rotation in nesting computation", True),
                    ("App::PropertyEnumeration", "Nest_Thickness", "UserProp", "The thickness to use for nesting", ["XLength", "YLength", "ZLength"]),
                    ("App::PropertyEnumeration", "Nest_grain", "UserProp", "The orientation to use for nesting", ["XLength", "YLength", "ZLength"]),
                    )
PROP_HEADERS = {
                "type" : 0,
                "name" : 1,
                "group" : 2,
                "description" : 3,
                "value" : 4
                }

ModeVerbose = True
def msgCsl(message):
    if ModeVerbose:
        App.Console.PrintMessage(message + "\n")

def userMsg(message):
	App.Console.PrintMessage(message + "\n")
    
def get_parent_part(obj):
    current = obj
    if current and current.TypeId == "App::Part":
        return current
    while current:
        # 1. Tenter d'accéder directement au parent structurel (si disponible)
        if hasattr(current, "getParent") and current.getParent():
            current = current.getParent()
        else:
            # 2. Sinon, chercher dans InList mais filtrer les liens logiques
            parents = current.InList
            found_parent = None
            for p in parents:
                # On vérifie si 'p' contient 'current' dans sa structure
                # App::Part et les Groupes stockent leurs enfants dans OutList
                if p.TypeId == "App::Part" or p.isDerivedFrom("App::DocumentObjectGroup"):
                    if current in p.OutList:
                        found_parent = p
                        break
            current = found_parent

        # Si on a trouvé un App::Part, on a fini
        if current and current.TypeId == "App::Part":
            return current

        # Si on n'a plus de parents structurels, on arrête
        if not current:
            break

    return None

def find_additive_box(parent_obj):
    """
    Cherche un objet de type PartDesign::AdditiveBox dans l'arborescence de parent_obj.
    """
    group_properties = ['Group', 'OutList', 'GroupBase', 'Elements']

    for prop_name in group_properties:
        if hasattr(parent_obj, prop_name):
            children = getattr(parent_obj, prop_name)

            if not children:
                continue

            if isinstance(children, (list, tuple)):
                for child in children:
                    if child.TypeId == "PartDesign::AdditiveBox":
                        return child
                    # Recursive search if child is a container
                    if child.TypeId.startswith("PartDesign::Body") or \
                       child.TypeId == "App::Part" or \
                       child.TypeId == "App::DocumentObjectGroup":
                        result = find_additive_box(child)
                        if result is not None:
                            return result
    return None

def getParentViewObject(oFC):
    viewObj = None
    if "PartDesign::" in oFC.TypeId:
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(oFC)
        sels = Gui.Selection.getSelectionEx("", 0)
        sel = sels[0]
        sub = sel.SubElementNames[0] if sel.SubElementNames else ""
        subs = sub.split(".")[:-1]
        # msgCsl(f"Object {oFC.Label} Body name: {subs[-2]}")
        viewObj = App.ActiveDocument.getObject(subs[-2])
        Gui.Selection.clearSelection()
    if "Part::" in oFC.TypeId:
        viewObj = App.ActiveDocument.getObject(oFC.Name)
    return viewObj

def getCurrentWoodPanel():
    fcDoc = App.ActiveDocument
    if hasattr(fcDoc, WOODPANELS_VarSet):
        panels_obj = fcDoc.getObject(WOODPANELS_VarSet)
        if hasattr(panels_obj, WOODPANELS_ListProperty):
            if not hasattr(panels_obj, "current_panel"):
                panels_obj.addProperty("App::Integer", "current_panel")
                setattr(fcDoc.PanneauManager, "current_panel", 1)
            return getattr(panels_obj, WOODPANELS_ListProperty)[getattr(panels_obj, "current_panel")], getattr(panels_obj, "current_panel")
        else:
            userMsg(f"No {WOODPANELS_ListProperty} property found in {panels_obj.Label}")
            return []
    else:
        userMsg(f"No {WOODPANELS_VarSet} object found in active docuement")
        return []

def getPanelsShortName():
    fcDoc = App.ActiveDocument
    panels_shortnames = []
    if hasattr(fcDoc, WOODPANELS_VarSet):
        panels_obj = fcDoc.getObject(WOODPANELS_VarSet)
        if hasattr(panels_obj, WOODPANELS_ListProperty):
            panels = getattr(panels_obj, WOODPANELS_ListProperty)[1:]
            for panel in panels:
                panels_shortnames.append(panel.split(";")[0])
    return panels_shortnames

def getShelves():
    fcDoc = App.ActiveDocument
    shelves = []
    for obj in fcDoc.Objects:
        if hasattr(obj, "bspf_tag"):
            if "ETG" in obj.bspf_tag:
                shelves.append(obj)
    return shelves

def getMaxShelvesIndex():
    shelves = getShelves()
    maxIndex = 0
    if shelves:
        for obj in shelves:
            index = int(obj.bspf_tag.split(";")[2][4:])
            if index > maxIndex: maxIndex = index
    return maxIndex

def add_BOM_Mat(obj):
    prop = USER_PROPERTIES[1]
    prop_name = prop[PROP_HEADERS["name"]]
    obj.addProperty(prop[PROP_HEADERS["type"]], prop_name, prop[PROP_HEADERS["group"]], prop[PROP_HEADERS["description"]])
    setattr(obj, prop_name, prop[PROP_HEADERS["value"]])
    # if prop_name == "BOM_mat":
    panels_shortnames = getPanelsShortName()
    obj.BOM_mat = panels_shortnames
    obj.BOM_mat = getCurrentWoodPanel()[1] - 1

def get_BOM_mat_thickness(obj):
    if hasattr(obj, "BOM_mat"):
        # return getPanelsShortName()[obj.BOM_mat].split("x")[-1]
        return float(obj.BOM_mat.split("x")[-1])
    else:
        return 0
    
def getObjTag(obj):
    tag_prop = {}
    if hasattr(obj, "bspf_tag"):
        tag_obj = obj.bspf_tag.split(";")
        tag_prop = {
                        "type" : tag_obj[0],
                        "caisson" : tag_obj[1],
                        "groupe_etageres" : tag_obj[2] if len(tag_obj) > 2 else ""
                    }
    return tag_prop

def getLastEtgGrpIndex():
    fcDoc = App.ActiveDocument
    max_index = 0
    for obj in fcDoc.Objects:
        tag_prop = getObjTag(obj)
        if tag_prop:
            index = int(tag_prop["groupe_etageres"][4:])
            max_index = max(max_index, index)
    return max_index

def setObjTag(obj, typ = None, caisson = None, groupe_etageres = None):
    if not hasattr(obj, "bspf_tag"):
        obj.addProperty("App::PropertyString", "bspf_tag", "UserProp")
        obj.bspf_tag = ";;"
    tag_prop = getObjTag(obj)
    tag_prop = {
                    "type" : typ if typ != None else tag_prop["type"],
                    "caisson" : caisson if caisson != None else tag_prop["caisson"],
                    "groupe_etageres" : groupe_etageres if groupe_etageres != None else tag_prop["groupe_etageres"],
                }
    obj.bspf_tag = ";".join(tag_prop.values())
