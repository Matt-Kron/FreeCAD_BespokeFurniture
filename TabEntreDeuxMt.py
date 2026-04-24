import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets, QtCore, QtGui

# Nom du groupe de paramètres pour la persistance
PARAM_GROUP = "User parameter:BaseApp/Preferences/Macros/TabEntreDeuxMt"

# =============================================================================
# FONCTIONS DE RÉSOLUTION D'ARBORESCENCE (INDÉPENDANCE DU CLIC)
# =============================================================================

def get_parent_part(obj):
    """Remonte l'arborescence pour trouver le App::Part parent."""
    current = obj
    while current and current.TypeId != "App::Part":
        parents = current.InList
        if not parents: break
        current = parents[0]
    return current if current and current.TypeId == "App::Part" else None

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

# def find_additive_box(parent_obj):
#     """Cherche une AdditiveBox pour les propriétés de taille."""
#     if not parent_obj: return None
#     for child in parent_obj.OutList:
#         if "AdditiveBox" in child.TypeId:
#             print(f"Enfant AdditiveBox {child.Label}")
#             return child
#         if hasattr(child, 'Group') or child.TypeId.startswith("PartDesign::Body"):
#             res = find_additive_box(child)
#             if res:
#                 print(f"Enfant AdditiveBox {res.Label}")
#                 return res
#     return None

def find_box_with_properties(part_obj):
    """Détecte si l'objet est une Tablette et identifie son schéma de propriétés."""
    def search(obj):
        plist = obj.PropertiesList
        # Schéma A : Ancien
        if "obj_gauche" in plist and "obj_droit" in plist:
            return obj, "classique"
        # Schéma B : Nouveau (Position + Taille)
        if "obj_pos_gauche" in plist and "obj_pos_droit" in plist:
            return obj, "complet"
        if hasattr(obj, "Group"):
            for child in obj.Group:
                res = search(child)
                if res: return res
        return None
    return search(part_obj)

# =============================================================================
# INTERFACE UTILISATEUR
# =============================================================================

class DragDropLineEdit(QtWidgets.QLineEdit):
    objectDropped = QtCore.Signal(str, str)
    def __init__(self, target_field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.target_field = target_field
        self.setReadOnly(True)
        self.setPlaceholderText("Glissez un objet ici...")
        self.setStyleSheet("background-color: #f0f0ff; color: #1a1a1a; border: 1px solid #778899; padding: 5px; border-radius: 4px;")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()

    def dropEvent(self, event):
        name = event.mimeData().text()
        obj = App.ActiveDocument.getObject(name)
        parent = get_parent_part(obj)
        target = parent if parent else obj
        if target:
            self.setText(f"{target.Label} ({target.Name})")
            self.objectDropped.emit(self.target_field, target.Name)
            event.acceptProposedAction()

class AssignmentDialog(QtWidgets.QDialog):
    def __init__(self, initial, all_data, schema, pref_show):
        super().__init__()
        self.schema = schema
        self.assigned = {"tablette": initial.get("tablette"),
                         "gauche": initial.get("gauche"),
                         "droit": initial.get("droit")}
        self.setWindowTitle(f"Configuration Tablette - Mode {schema}")
        self.setMinimumWidth(550)
        self.setupUi(all_data, pref_show)
        self.update_preview()

    def setupUi(self, all_data, pref_show):
        layout = QtWidgets.QVBoxLayout(self)

        grid = QtWidgets.QGridLayout()
        self.list_items = QtWidgets.QListWidget()
        self.list_items.setDragEnabled(True)
        for n, l in all_data.items():
            item = QtWidgets.QListWidgetItem(f"{l} ({n})")
            item.setData(QtCore.Qt.UserRole, n)
            self.list_items.addItem(item)

        grid.addWidget(QtWidgets.QLabel("Pièces détectées :"), 0, 0)
        grid.addWidget(self.list_items, 1, 0, 4, 1)

        labels = ["Tablette (Box) :", "Montant Gauche :", "Montant Droit :"]
        self.edits = {}
        for i, key in enumerate(["tablette", "gauche", "droit"]):
            grid.addWidget(QtWidgets.QLabel(labels[i]), i+1, 1)
            edit = DragDropLineEdit(key)
            edit.objectDropped.connect(self.sync)
            if self.assigned[key]:
                o = App.ActiveDocument.getObject(self.assigned[key])
                if o: edit.setText(f"{o.Label} ({o.Name})")
            grid.addWidget(edit, i+1, 2)
            self.edits[key] = edit

        layout.addLayout(grid)

        # Zone de prévisualisation
        self.group_preview = QtWidgets.QGroupBox("Récapitulatif de l'affectation")
        prev_layout = QtWidgets.QVBoxLayout()
        self.lbl_preview = QtWidgets.QLabel("En attente de sélection...")
        self.lbl_preview.setStyleSheet("color: #2e4a85; background-color: #f4f4f4; padding: 10px; border-radius: 4px;")
        prev_layout.addWidget(self.lbl_preview)
        self.group_preview.setLayout(prev_layout)
        layout.addWidget(self.group_preview)

        self.check_ui = QtWidgets.QCheckBox("Toujours afficher cette fenêtre")
        self.check_ui.setChecked(pref_show)
        layout.addWidget(self.check_ui)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def sync(self, key, name):
        self.assigned[key] = name
        self.update_preview()

    def update_preview(self):
        t, g, d = self.assigned["tablette"], self.assigned["gauche"], self.assigned["droit"]
        if t and g and d:
            ot, og, od = [App.ActiveDocument.getObject(n) for n in [t, g, d]]
            self.lbl_preview.setText(f"✅ <b>{ot.Label}</b> sera placée entre :<br>• Gauche : {og.Label}<br>• Droit : {od.Label}")
        else:
            self.lbl_preview.setText("❌ Veuillez assigner les 3 composants.")

# =============================================================================
# LOGIQUE MÉTIER
# =============================================================================

def apply_assignments(t_name, g_name, d_name, schema):
    try:
        doc = App.ActiveDocument
        tablette_part = doc.getObject(t_name)
        g_obj = doc.getObject(g_name)
        d_obj = doc.getObject(d_name)

        box_data = find_box_with_properties(tablette_part)
        if not box_data: return False
        box, _ = box_data

        if schema == "classique":
            box.obj_gauche, box.obj_droit = g_obj, d_obj
            box.obj_taille_gauche = find_additive_box(g_obj)
        else:
            box.obj_pos_gauche, box.obj_pos_droit = g_obj, d_obj
            print(f"g_obj {g_obj.Label}, d_obj: {d_obj.Label}")
            # Gestion automatique des tailles
            print("obj_taille_gauche")
            box.obj_taille_gauche = find_additive_box(g_obj)
            print("obj_taille_droit")
            box.obj_taille_droit = find_additive_box(d_obj)

        doc.recompute()
        return True
    except Exception as e:
        App.Console.PrintError(f"Erreur : {str(e)}\n")
        return False

def run_assignment_macro(force_ui=None):
    params = App.ParamGet(PARAM_GROUP)
    pref_show = params.GetBool("AlwaysShowDialog", True)
    show_ui = force_ui if force_ui is not None else pref_show

    # Résolution des parents App::Part
    sel = Gui.Selection.getSelection()
    resolved = []
    seen = set()
    for obj in sel:
        p = get_parent_part(obj)
        if p and p.Name not in seen:
            resolved.append(p)
            seen.add(p.Name)

    # Détection auto
    t_name, schema, g_name, d_name = None, None, None, None
    if len(resolved) == 3:
        for p in resolved:
            found = find_box_with_properties(p)
            if found:
                t_name, schema = p.Name, found[1]
                others = [o for o in resolved if o.Name != t_name]
                # Tri par l'axe X (Gauche < Droit)
                if others[0].Placement.Base.x < others[1].Placement.Base.x:
                    g_name, d_name = others[0].Name, others[1].Name
                else:
                    g_name, d_name = others[1].Name, others[0].Name
                break
    else:
        show_ui = True

    if not show_ui and t_name and g_name and d_name:
        if apply_assignments(t_name, g_name, d_name, schema):
            App.Console.PrintMessage("Affectation Tablette auto réussie.\n")
            return

    # Ouverture Interface
    all_data = {p.Name: p.Label for p in resolved}
    initial = {"tablette": t_name, "gauche": g_name, "droit": d_name}
    dlg = AssignmentDialog(initial, all_data, schema if schema else "complet", pref_show)

    if dlg.exec_() == QtWidgets.QDialog.Accepted:
        params.SetBool("AlwaysShowDialog", dlg.check_ui.isChecked())
        res = dlg.assigned
        apply_assignments(res["tablette"], res["gauche"], res["droit"], dlg.schema)

if __name__ == "__main__":
    run_assignment_macro()
