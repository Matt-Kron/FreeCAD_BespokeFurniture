import FreeCAD as App
import FreeCADGui as Gui

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

ModeVerbose = True
def msgCsl(message):
    if ModeVerbose:
        App.Console.PrintMessage(message + "\n")

def userMsg(message):
	App.Console.PrintMessage(message + "\n")
    
def get_parent_part(obj):
    current = obj
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
