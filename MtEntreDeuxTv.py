import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets, QtCore, QtGui

# Paramètres de persistance
PARAM_GROUP = "User parameter:BaseApp/Preferences/Macros/MtEntreDeuxTv"

# =============================================================================
# FONCTIONS DE RECHERCHE DANS L'ARBORESCENCE
# =============================================================================

def get_parent_part(obj):
    """Remonte l'arborescence pour trouver le App::Part parent d'un objet."""
    current = obj
    # On remonte tant qu'on n'est pas sur une Part et qu'il y a un parent
    while current and current.TypeId != "App::Part":
        # Vérification des parents via InList (objets qui contiennent cet objet)
        parents = current.InList
        if not parents:
            break
        # On prend le premier parent trouvé (généralement le conteneur direct)
        current = parents[0]

    return current if current and current.TypeId == "App::Part" else None

def find_box_with_properties(part_obj):
    """Cherche l'objet interne (souvent une Box) possédant les propriétés métier."""
    if not part_obj: return None

    def search(obj):
        plist = obj.PropertiesList
        if "obj_dessous" in plist: return obj, "vertical_2prop"
        if "obj_pos_dessous" in plist: return obj, "vertical_4prop"
        # Si c'est un conteneur (Part ou Body), on cherche à l'intérieur
        if hasattr(obj, "Group"):
            for child in obj.Group:
                res = search(child)
                if res: return res
        return None
    return search(part_obj)

# =============================================================================
# INTERFACE ET DIALOGUE
# =============================================================================

class DragDropLineEdit(QtWidgets.QLineEdit):
    objectDropped = QtCore.Signal(str, str)
    def __init__(self, target_field_name, *args, **kwargs):
        super(DragDropLineEdit, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.target_field_name = target_field_name
        self.setReadOnly(True)
        self.setPlaceholderText("Glissez un objet ici...")
        self.setStyleSheet("background-color: #e0e0f8; color: #1a1a1a; border: 1px solid #778899; padding: 5px; border-radius: 4px;")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()

    def dropEvent(self, event):
        name = event.mimeData().text()
        obj = App.ActiveDocument.getObject(name)
        # Si on dépose un sous-objet, on récupère sa Part parente
        parent_part = get_parent_part(obj) if obj else None
        target = parent_part if parent_part else obj

        if target:
            self.setText(f"{target.Label} ({target.Name})")
            self.objectDropped.emit(self.target_field_name, target.Name)
            event.acceptProposedAction()

class AssignmentDialog(QtWidgets.QDialog):
    def __init__(self, initial, all_data, prop_type, pref_show):
        super().__init__()
        self.prop_type = prop_type
        self.assigned = {"montant": initial.get("montant"), "role1": initial.get("role1"), "role2": initial.get("role2")}
        self.setWindowTitle(f"Configuration - Mode {prop_type.capitalize()}")
        self.setMinimumWidth(500)
        self.setupUi(all_data, pref_show)
        self.update_displays()

    def setupUi(self, all_data, pref_show):
        layout = QtWidgets.QVBoxLayout(self)
        grid = QtWidgets.QGridLayout()

        self.list_widgets = QtWidgets.QListWidget()
        self.list_widgets.setDragEnabled(True)
        for name, label in all_data.items():
            item = QtWidgets.QListWidgetItem(f"{label} ({name})")
            item.setData(QtCore.Qt.UserRole, name)
            self.list_widgets.addItem(item)

        grid.addWidget(QtWidgets.QLabel("Pièces Parentes détectées :"), 0, 0)
        grid.addWidget(self.list_widgets, 1, 0, 4, 1)

        labels = ["Montant Central :",
                  "Inférieur / Gauche :" if self.prop_type == "vertical_2prop" else "Position Inf :",
                  "Supérieur / Droite :" if self.prop_type == "vertical_2prop" else "Position Sup :"]

        self.edits = {}
        for i, key in enumerate(["montant", "role1", "role2"]):
            grid.addWidget(QtWidgets.QLabel(labels[i]), i+1, 1)
            edit = DragDropLineEdit(key)
            edit.objectDropped.connect(self.sync_assigned)
            if self.assigned[key]:
                obj = App.ActiveDocument.getObject(self.assigned[key])
                if obj: edit.setText(f"{obj.Label} ({obj.Name})")
            grid.addWidget(edit, i+1, 2)
            self.edits[key] = edit

        layout.addLayout(grid)

        self.group_preview = QtWidgets.QGroupBox("Prévisualisation")
        preview_layout = QtWidgets.QVBoxLayout()
        self.lbl_preview = QtWidgets.QLabel("")
        self.lbl_preview.setWordWrap(True)
        self.lbl_preview.setStyleSheet("color: #2e4a85; font-weight: bold; background-color: #f0f4ff; padding: 10px; border-radius: 5px;")
        preview_layout.addWidget(self.lbl_preview)
        self.group_preview.setLayout(preview_layout)
        layout.addWidget(self.group_preview)

        self.check_pref = QtWidgets.QCheckBox("Toujours afficher cette interface")
        self.check_pref.setChecked(pref_show)
        layout.addWidget(self.check_pref)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def sync_assigned(self, key, name):
        self.assigned[key] = name
        self.update_displays()

    def update_displays(self):
        m, r1, r2 = self.assigned["montant"], self.assigned["role1"], self.assigned["role2"]
        if m and r1 and r2:
            o_m = App.ActiveDocument.getObject(m)
            o_r1 = App.ActiveDocument.getObject(r1)
            o_r2 = App.ActiveDocument.getObject(r2)
            if o_m and o_r1 and o_r2:
                self.lbl_preview.setText(f"✅ <b>Liaison prête</b><br>Montant: {o_m.Label}<br>Assigné entre {o_r1.Label} et {o_r2.Label}")
                return
        self.lbl_preview.setText("❌ Sélection incomplète.")

# =============================================================================
# LOGIQUE D'APPLICATION ET EXECUTION
# =============================================================================

def _find_first_child_by_type(parent_obj, type_string):
    """
    Cherche récursivement le premier enfant d'un type donné sous un objet parent.
    Utile pour trouver une AdditiveBox ou un autre sous-élément.
    """
    group_properties = ['Group', 'OutList', 'GroupBase', 'Elements']

    if parent_obj.TypeId == type_string:
        return parent_obj

    for prop_name in group_properties:
        if hasattr(parent_obj, prop_name):
            children = getattr(parent_obj, prop_name)

            if not children:
                continue

            if isinstance(children, (list, tuple)):
                for child in children:
                    # Vérification directe du type
                    if child.TypeId == type_string:
                        return child

                    # Recherche récursive pour les conteneurs
                    if hasattr(child, 'Group') or hasattr(child, 'OutList') or \
                       child.TypeId.startswith("PartDesign::Body") or \
                       child.TypeId == "App::Part" or \
                       child.TypeId == "App::DocumentObjectGroup":
                        result = _find_first_child_by_type(child, type_string)
                        if result is not None:
                            return result
    return None

def apply_assignments(m_name, r1_name, r2_name, p_type):
    try:
        doc = App.ActiveDocument
        target_data = find_box_with_properties(doc.getObject(m_name))
        if not target_data: return False
        target, _ = target_data

        obj_r1 = doc.getObject(r1_name)
        obj_r2 = doc.getObject(r2_name)

        if p_type == "vertical_2prop":
            target.obj_dessous, target.obj_dessus = obj_r1, obj_r2
            # Recherche des AdditiveBox pour la taille
            child = _find_first_child_by_type(obj_r1, "PartDesign::AdditiveBox")
            print(f"objet partfeature: {child.Label}")
            if child: # "AdditiveBox" in child.TypeId:
                setattr(target, "obj_taille_dessous", child)
        else:
            target.obj_pos_dessous, target.obj_pos_dessus = obj_r1, obj_r2
            # Recherche des AdditiveBox pour la taille
            for role, prop in [(obj_r1, "obj_taille_dessous"), (obj_r2, "obj_taille_dessus")]:
                child = _find_first_child_by_type(role, "PartDesign::AdditiveBox")
                print(f"objet partfeature: {child.Label}")
                #for child in role.OutList:
                if child: # "AdditiveBox" in child.TypeId:
                    setattr(target, prop, child)
                    # break
        doc.recompute()
        return True
    except: return False

def run_assignment_macro(force_ui=None):
    params = App.ParamGet(PARAM_GROUP)
    pref_show = params.GetBool("AlwaysShowDialog", True)
    show_ui = force_ui if force_ui is not None else pref_show

    # --- LOGIQUE DE RÉSOLUTION DES PARENTS ---
    sel = Gui.Selection.getSelection()
    resolved_parts = []
    seen_names = set()

    for obj in sel:
        parent = get_parent_part(obj)
        if parent and parent.Name not in seen_names:
            resolved_parts.append(parent)
            seen_names.add(parent.Name)

    # Identification auto basée sur les parents résolus
    m_name, m_type, r1_name, r2_name = None, None, None, None
    if len(resolved_parts) == 3:
        for p in resolved_parts:
            found = find_box_with_properties(p)
            if found:
                m_name, m_type = p.Name, found[1]
                others = [o for o in resolved_parts if o.Name != m_name]
                # Tri par Z (à titre d'exemple pour l'auto-détection)
                if others[0].Placement.Base.z < others[1].Placement.Base.z:
                    r1_name, r2_name = others[0].Name, others[1].Name
                else:
                    r1_name, r2_name = others[1].Name, others[0].Name
                break
    else:
        show_ui = True # On n'a pas 3 pièces distinctes -> Interface obligatoire

    if not show_ui and m_name and r1_name and r2_name:
        if apply_assignments(m_name, r1_name, r2_name, m_type):
            App.Console.PrintMessage("Succès automatique sur objets parents.\n")
            return

    # Boîte de dialogue
    all_data = {p.Name: p.Label for p in resolved_parts}
    initial = {"montant": m_name, "role1": r1_name, "role2": r2_name}
    dlg = AssignmentDialog(initial, all_data, m_type if m_type else "vertical_2prop", pref_show)
    if dlg.exec_() == QtWidgets.QDialog.Accepted:
        params.SetBool("AlwaysShowDialog", dlg.check_pref.isChecked())
        res = dlg.assigned
        apply_assignments(res["montant"], res["role1"], res["role2"], dlg.prop_type)

if __name__ == "__main__":
    run_assignment_macro()
