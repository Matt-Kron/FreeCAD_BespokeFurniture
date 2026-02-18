import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui, QtWidgets
import os
import difflib

# --- Fonction Utilitaire ---
def find_closest_match(target_string, choices):
    if not choices: return ""
    lower_target = target_string.lower()
    for choice in choices:
        if choice.lower() == lower_target: return choice
    matches = difflib.get_close_matches(target_string, choices, n=1, cutoff=0.1)
    return matches[0] if matches else choices[0]

# --- 1. Définition du Panneau ---
class Panneau:
    PROPERTIES = ["nom_aggr", "nom", "longueur", "largeur", "epaisseur", "raf_longueur", "raf_largeur", "couleur"]
    TYPES = {"nom_aggr": str, "nom": str, "couleur": str, "longueur": float, "largeur": float, "epaisseur": float, "raf_longueur": float, "raf_largeur": float}

    def __init__(self, data=None):
        self.nom_aggr = ""
        self.nom = "Mela"
        self.longueur, self.largeur, self.epaisseur = 2800.0, 2070.0, 19.0
        self.raf_longueur, self.raf_largeur = 10.0, 10.0
        self.couleur = "#cccccc"
        if isinstance(data, dict): self.from_dict(data)
        elif isinstance(data, str): self.from_string(data)
        self.rebuild_nom_aggr()

    def rebuild_nom_aggr(self):
        self.nom_aggr = f"{self.nom} {int(round(self.longueur))}x{int(round(self.largeur))}x{int(round(self.epaisseur))}"

    def to_dict(self): return {prop: getattr(self, prop) for prop in self.PROPERTIES}
    def to_string(self): return ";".join([str(getattr(self, p)) for p in self.PROPERTIES])

    def from_dict(self, data):
        for prop, val in data.items():
            if prop in self.PROPERTIES:
                try: setattr(self, prop, self.TYPES[prop](val))
                except: pass

    def from_string(self, line):
        values = line.split(";")
        if len(values) == len(self.PROPERTIES):
            self.from_dict(dict(zip(self.PROPERTIES, values)))
            self.rebuild_nom_aggr()

# --- 2. Modèle de Tableau ---
class PanneauTableModel(QtCore.QAbstractTableModel):
    HEADERS = ["Nom Agrégé", "Nom", "Longueur", "Largeur", "Épaisseur", "Raf. Longueur", "Raf. Largeur", "Couleur"]

    def __init__(self, panneaux, parent=None):
        super(PanneauTableModel, self).__init__(parent)
        self._panneaux = panneaux

    def rowCount(self, parent=QtCore.QModelIndex()): return len(self._panneaux)
    def columnCount(self, parent=QtCore.QModelIndex()): return len(Panneau.PROPERTIES)

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal: return self.HEADERS[section]

    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self._panneaux): return None
        p = self._panneaux[index.row()]
        prop = Panneau.PROPERTIES[index.column()]
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole): return str(getattr(p, prop))
        if role == QtCore.Qt.BackgroundRole and prop == "couleur":
            try: return QtGui.QBrush(QtGui.QColor(getattr(p, prop)))
            except: return None
        return None

    def setData(self, index, value, role):
        if role != QtCore.Qt.EditRole: return False
        p = self._panneaux[index.row()]
        prop = Panneau.PROPERTIES[index.column()]
        try:
            setattr(p, prop, Panneau.TYPES[prop](value))
            p.rebuild_nom_aggr()
            self.dataChanged.emit(self.index(index.row(), 0), self.index(index.row(), 0))
            self.dataChanged.emit(index, index)
            return True
        except: return False

    def flags(self, index): return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def add_panneau(self, p=None):
        self.beginInsertRows(QtCore.QModelIndex(), len(self._panneaux), len(self._panneaux))
        self._panneaux.append(p if p else Panneau())
        self.endInsertRows()

    def remove_panneaux(self, indexes):
        rows = sorted([idx.row() for idx in indexes], reverse=True)
        for row in rows:
            self.beginRemoveRows(QtCore.QModelIndex(), row, row)
            del self._panneaux[row]
            self.endRemoveRows()

    def duplicate_panneau(self, index):
        if index.row() >= len(self._panneaux): return
        original = self._panneaux[index.row()]
        new_p = Panneau(original.to_dict())
        new_p.nom += "_copie"
        self.beginInsertRows(QtCore.QModelIndex(), index.row() + 1, index.row() + 1)
        self._panneaux.insert(index.row() + 1, new_p)
        self.endInsertRows()

    def rebuild_agg_name_for_panneau(self, index):
        if index.row() >= len(self._panneaux): return
        self._panneaux[index.row()].rebuild_nom_aggr()
        self.dataChanged.emit(self.index(index.row(), 0), self.index(index.row(), 0))

    def get_panneau(self, index): return self._panneaux[index.row()]
    def get_aggregated_names(self): return [p.nom_aggr for p in self._panneaux]

# --- 3. Délégués ---
class SpinBoxDelegate(QtWidgets.QItemDelegate):
    def createEditor(self, parent, option, index):
        if Panneau.TYPES[Panneau.PROPERTIES[index.column()]] == float:
            editor = QtWidgets.QDoubleSpinBox(parent)
            editor.setRange(0, 100000); editor.setDecimals(2)
            return editor
        return super(SpinBoxDelegate, self).createEditor(parent, option, index)

class ColorPickerDelegate(QtWidgets.QItemDelegate):
    def editorEvent(self, event, model, option, index):
        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            color = QtWidgets.QColorDialog.getColor(QtGui.QColor(index.data()), None, "Couleur", QtWidgets.QColorDialog.DontUseNativeDialog)
            if color.isValid(): model.setData(index, color.name(), QtCore.Qt.EditRole)
            return True
        return False
    def paint(self, painter, option, index):
        color = QtGui.QColor(index.data())
        painter.fillRect(option.rect, color)
        painter.drawText(option.rect, QtCore.Qt.AlignCenter, index.data())

# --- 4. Dialogue Principal ---
class PanneauDialog(QtWidgets.QDialog):
    CONFIG_FILENAME = "panneaux_config.txt"
    PROP_NAME = "liste_panneaux"
    OBJECT_NAME = "Liste panneaux"

    def __init__(self):
        super(PanneauDialog, self).__init__(FreeCADGui.getMainWindow(), QtCore.Qt.Window)
        self.setWindowTitle("Gestionnaire Panneaux (Sécurisé)")
        self.resize(1500, 1500)
        self.config_filepath = os.path.join(FreeCAD.getUserMacroDir(), self.CONFIG_FILENAME)
        self.config_panneaux = []
        self.doc_panneaux = []

        self._load_config_file()
        self._setup_ui()
        self._refresh_doc_lists()
        self._apply_delegates()
        self._connect_signals()
        # --- SÉLECTION DU DOCUMENT ACTIF ---
        active_doc = FreeCAD.ActiveDocument
        if active_doc:
            # On cherche le nom du doc actif dans la liste
            items = self.list_doc_source.findItems(active_doc.Name, QtCore.Qt.MatchExactly)
            if items:
                self.list_doc_source.setCurrentItem(items[0])
                self._load_selected_doc()
            elif self.list_doc_source.count() > 0:
                # Repli sur le premier si non trouvé
                self.list_doc_source.setCurrentRow(0)
                self._load_selected_doc()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        # --- SECTION FICHIER ---
        cfg_widget = QtWidgets.QWidget()
        cfg_lyt = QtWidgets.QVBoxLayout(cfg_widget)
        cfg_lyt.addWidget(QtWidgets.QLabel("<b>1. Base de données Fichier (panneaux_config.txt)</b>"))
        self.config_table = QtWidgets.QTableView()
        self.config_model = PanneauTableModel(self.config_panneaux)
        self.config_proxy = QtCore.QSortFilterProxyModel()
        self.config_proxy.setSourceModel(self.config_model)
        self.config_table.setModel(self.config_proxy)
        self.config_table.setSortingEnabled(True)
        self.config_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.config_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        cfg_lyt.addWidget(self.config_table)

        btns_cfg = QtWidgets.QHBoxLayout()
        self.btn_cfg_add = QtWidgets.QPushButton("Ajouter")
        self.btn_cfg_dup = QtWidgets.QPushButton("Dupliquer")
        self.btn_cfg_del = QtWidgets.QPushButton("Supprimer")
        self.btn_cfg_reb = QtWidgets.QPushButton("Réinit Noms")
        self.btn_cfg_to_doc = QtWidgets.QPushButton("Copier vers Doc Source ->")
        self.btn_cfg_save = QtWidgets.QPushButton("💾 Sauvegarder Fichier")
        btns_cfg.addWidget(self.btn_cfg_add); btns_cfg.addWidget(self.btn_cfg_dup)
        btns_cfg.addWidget(self.btn_cfg_del); btns_cfg.addWidget(self.btn_cfg_reb)
        btns_cfg.addStretch(); btns_cfg.addWidget(self.btn_cfg_to_doc); btns_cfg.addWidget(self.btn_cfg_save)
        cfg_lyt.addLayout(btns_cfg)
        main_splitter.addWidget(cfg_widget)

        # --- SECTION GESTION DOCUMENTS ---
        doc_main_widget = QtWidgets.QWidget()
        doc_main_lyt = QtWidgets.QHBoxLayout(doc_main_widget)

        doc_side_widget = QtWidgets.QWidget()
        doc_side_lyt = QtWidgets.QVBoxLayout(doc_side_widget)

        doc_side_lyt.addWidget(QtWidgets.QLabel("<b>2. Doc Source (Édition)</b>"))
        self.list_doc_source = QtWidgets.QListWidget()
        doc_side_lyt.addWidget(self.list_doc_source)

        doc_side_lyt.addWidget(QtWidgets.QLabel("<b>3. Docs Destinataires (Cibles)</b>"))
        self.list_doc_dest = QtWidgets.QListWidget()
        self.list_doc_dest.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        doc_side_lyt.addWidget(self.list_doc_dest)

        self.btn_refresh_docs = QtWidgets.QPushButton("🔄 Actualiser documents")
        doc_side_lyt.addWidget(self.btn_refresh_docs)

        doc_side_lyt.addWidget(QtWidgets.QLabel("Type d'objet :"))
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["App::VarSet", "Part::FeaturePython"])
        doc_side_lyt.addWidget(self.type_combo)

        self.btn_create_obj = QtWidgets.QPushButton("Créer 'Liste panneaux'")
        doc_side_lyt.addWidget(self.btn_create_obj)
        doc_main_lyt.addWidget(doc_side_widget, 1)

        doc_data_widget = QtWidgets.QWidget()
        doc_data_lyt = QtWidgets.QVBoxLayout(doc_data_widget)

        self.doc_table = QtWidgets.QTableView()
        self.doc_model = PanneauTableModel(self.doc_panneaux)
        self.doc_proxy = QtCore.QSortFilterProxyModel()
        self.doc_proxy.setSourceModel(self.doc_model)
        self.doc_table.setModel(self.doc_proxy)
        self.doc_table.setSortingEnabled(True)
        self.doc_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.doc_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        doc_data_lyt.addWidget(self.doc_table)

        btns_doc = QtWidgets.QHBoxLayout()
        self.btn_doc_add = QtWidgets.QPushButton("Ajouter")
        self.btn_doc_dup = QtWidgets.QPushButton("Dupliquer")
        self.btn_doc_del = QtWidgets.QPushButton("Supprimer")
        self.btn_doc_reb = QtWidgets.QPushButton("Réinit Noms")
        self.btn_doc_to_cfg = QtWidgets.QPushButton("<- Copier vers Fichier")
        btns_doc.addWidget(self.btn_doc_add); btns_doc.addWidget(self.btn_doc_dup)
        btns_doc.addWidget(self.btn_doc_del); btns_doc.addWidget(self.btn_doc_reb)
        btns_doc.addStretch(); btns_doc.addWidget(self.btn_doc_to_cfg)
        doc_data_lyt.addLayout(btns_doc)

        btns_actions = QtWidgets.QHBoxLayout()
        self.btn_bom = QtWidgets.QPushButton("MAJ Enum BOM")
        self.btn_col = QtWidgets.QPushButton("Appliquer Couleurs")
        self.btn_doc_save = QtWidgets.QPushButton("💾 Sauvegarder Doc Source")
        btns_actions.addWidget(self.btn_bom); btns_actions.addWidget(self.btn_col)
        btns_actions.addStretch(); btns_actions.addWidget(self.btn_doc_save)
        doc_data_lyt.addLayout(btns_actions)

        transfer_group = QtWidgets.QGroupBox("Transfert groupé")
        transfer_lyt = QtWidgets.QHBoxLayout(transfer_group)
        self.btn_copy_sel = QtWidgets.QPushButton("Copier SÉLECTION")
        self.btn_copy_full = QtWidgets.QPushButton("Copier TOUT")
        transfer_lyt.addWidget(self.btn_copy_sel); transfer_lyt.addWidget(self.btn_copy_full)
        doc_data_lyt.addWidget(transfer_group)

        doc_main_lyt.addWidget(doc_data_widget, 4)
        main_splitter.addWidget(doc_main_widget)
        layout.addWidget(main_splitter)
        main_splitter.setSizes([600, 500])
        self.status_bar = QtWidgets.QStatusBar()
        layout.addWidget(self.status_bar)

    def _notify(self, msg, is_err=False):
        c = "red" if is_err else "green"
        self.status_bar.setStyleSheet(f"QStatusBar {{ color: {c}; font-weight: bold; }}")
        self.status_bar.showMessage(msg, 6000)

    def _refresh_doc_lists(self):
        self.list_doc_source.blockSignals(True)
        self.list_doc_source.clear()
        self.list_doc_dest.clear()
        for name in FreeCAD.listDocuments().keys():
            self.list_doc_source.addItem(name)
            self.list_doc_dest.addItem(name)
        self.list_doc_source.blockSignals(False)

    def _get_src_idxs(self, table):
        proxy = table.model()
        if not proxy: return []
        selection = table.selectionModel().selectedIndexes()
        if not selection: return []
        unique = sorted(list(set([proxy.mapToSource(i).row() for i in selection])), reverse=True)
        return [proxy.sourceModel().index(r, 0) for r in unique]

    def _load_selected_doc(self):
        item = self.list_doc_source.currentItem()
        if not item: return
        doc_name = item.text()
        doc = FreeCAD.getDocument(doc_name)
        if not doc: return

        # Bloquer les signaux du modèle pendant la purge pour éviter le crash au dessin
        self.doc_model.beginResetModel()
        self.doc_panneaux.clear()
        obj = next((o for o in doc.Objects if o.Label == self.OBJECT_NAME), None)
        if obj and hasattr(obj, self.PROP_NAME):
            data = getattr(obj, self.PROP_NAME)
            if data:
                start = 1 if "nom_aggr" in data[0] else 0
                for l in data[start:]: self.doc_panneaux.append(Panneau(l))
        self.doc_model.endResetModel()
        self._notify(f"Doc '{doc_name}' chargé.")

    def _save_doc_data(self):
        item = self.list_doc_source.currentItem()
        if not item: return
        doc = FreeCAD.getDocument(item.text())
        if not doc: return
        obj = next((o for o in doc.Objects if o.Label == self.OBJECT_NAME), None)
        if obj:
            try:
                setattr(obj, self.PROP_NAME, [";".join(Panneau.PROPERTIES)] + [p.to_string() for p in self.doc_panneaux])
                doc.recompute()
                self._notify("Doc sauvegardé.")
            except Exception as e: self._notify(f"Erreur save: {e}", True)

    def _copy_bulk(self, mode="selected"):
        dest_items = self.list_doc_dest.selectedItems()
        if not dest_items: return

        lines = []
        if mode == "selected":
            idxs = self._get_src_idxs(self.doc_table)
            lines = [self.doc_model.get_panneau(i).to_string() for i in idxs]
        else:
            lines = [p.to_string() for p in self.doc_panneaux]
        if not lines: return

        for item in dest_items:
            doc = FreeCAD.getDocument(item.text())
            if not doc: continue
            obj = next((o for o in doc.Objects if o.Label == self.OBJECT_NAME), None)
            if not obj:
                obj = doc.addObject(self.type_combo.currentText(), "PanneauManager")
                obj.Label = self.OBJECT_NAME
                obj.addProperty("App::PropertyStringList", self.PROP_NAME)

            header = [";".join(Panneau.PROPERTIES)]
            if mode == "selected":
                curr = getattr(obj, self.PROP_NAME) or header
                setattr(obj, self.PROP_NAME, curr + lines)
            else:
                setattr(obj, self.PROP_NAME, header + lines)
            try: doc.recompute()
            except: pass
        self._notify("Copie groupée terminée.")

    def _connect_signals(self):
        self.list_doc_source.itemSelectionChanged.connect(self._load_selected_doc)
        self.btn_refresh_docs.clicked.connect(self._refresh_doc_lists)
        self.btn_create_obj.clicked.connect(self._create_doc_object)
        # Fichier
        self.btn_cfg_add.clicked.connect(lambda: self.config_model.add_panneau())
        self.btn_cfg_dup.clicked.connect(lambda: self.config_model.duplicate_panneau(self._get_src_idxs(self.config_table)[0]) if self._get_src_idxs(self.config_table) else None)
        self.btn_cfg_del.clicked.connect(lambda: self.config_model.remove_panneaux(self._get_src_idxs(self.config_table)))
        self.btn_cfg_reb.clicked.connect(lambda: [self.config_model.rebuild_agg_name_for_panneau(i) for i in self._get_src_idxs(self.config_table)])
        self.btn_cfg_save.clicked.connect(self._save_config_file)
        # Doc Source
        self.btn_doc_add.clicked.connect(lambda: self.doc_model.add_panneau())
        self.btn_doc_dup.clicked.connect(lambda: self.doc_model.duplicate_panneau(self._get_src_idxs(self.doc_table)[0]) if self._get_src_idxs(self.doc_table) else None)
        self.btn_doc_del.clicked.connect(lambda: self.doc_model.remove_panneaux(self._get_src_idxs(self.doc_table)))
        self.btn_doc_reb.clicked.connect(lambda: [self.doc_model.rebuild_agg_name_for_panneau(i) for i in self._get_src_idxs(self.doc_table)])
        self.btn_doc_save.clicked.connect(self._save_doc_data)
        # Transferts
        self.btn_cfg_to_doc.clicked.connect(self._cfg_to_doc)
        self.btn_doc_to_cfg.clicked.connect(self._doc_to_cfg)
        self.btn_copy_sel.clicked.connect(lambda: self._copy_bulk("selected"))
        self.btn_copy_full.clicked.connect(lambda: self._copy_bulk("all"))
        self.btn_bom.clicked.connect(self._update_bom)
        self.btn_col.clicked.connect(self._apply_colors)

    def _cfg_to_doc(self):
        for i in self._get_src_idxs(self.config_table):
            self.doc_model.add_panneau(Panneau(self.config_model.get_panneau(i).to_dict()))

    def _doc_to_cfg(self):
        for i in self._get_src_idxs(self.doc_table):
            self.config_model.add_panneau(Panneau(self.doc_model.get_panneau(i).to_dict()))

    def _create_doc_object(self):
        item = self.list_doc_source.currentItem()
        if not item: return
        doc = FreeCAD.getDocument(item.text())
        obj = doc.addObject(self.type_combo.currentText(), "PanneauManager")
        obj.Label = self.OBJECT_NAME
        obj.addProperty("App::PropertyStringList", self.PROP_NAME)
        doc.recompute()
        self._load_selected_doc()

    def _apply_delegates(self):
        s, c = SpinBoxDelegate(self), ColorPickerDelegate(self)
        for t in [self.config_table, self.doc_table]:
            for col in [2,3,4,5,6]: t.setItemDelegateForColumn(col, s)
            t.setItemDelegateForColumn(7, c)

    def _load_config_file(self):
        if os.path.exists(self.config_filepath):
            with open(self.config_filepath, 'r') as f:
                lines = f.readlines()
                for l in lines[1:]: self.config_panneaux.append(Panneau(l.strip()))

    def _save_config_file(self):
        with open(self.config_filepath, 'w') as f:
            f.write(";".join(Panneau.PROPERTIES) + "\n")
            f.writelines([p.to_string() + "\n" for p in self.config_panneaux])
        self._notify("Config sauvée.")

    def _update_bom(self):
        names = self.doc_model.get_aggregated_names()
        item = self.list_doc_source.currentItem()
        if not item: return
        doc = FreeCAD.getDocument(item.text())
        for o in doc.Objects:
            if hasattr(o, "BOM_mat"): setattr(o, "BOM_mat", names)
        doc.recompute(); self._notify("BOM MAJ.")

    def _apply_colors(self):
        cmap = {p.nom_aggr: (QtGui.QColor(p.couleur).red()/255.0, QtGui.QColor(p.couleur).green()/255.0, QtGui.QColor(p.couleur).blue()/255.0, 0.0) for p in self.doc_panneaux}
        item = self.list_doc_source.currentItem()
        if not item: return
        doc = FreeCAD.getDocument(item.text())
        for o in doc.Objects:
            if hasattr(o, "BOM_mat") and getattr(o, "BOM_mat") in cmap:
                t = o.InList[0] if o.InList and o.InList[0].TypeId == 'PartDesign::Body' else o
                if hasattr(t, 'ViewObject'): t.ViewObject.ShapeColor = cmap[getattr(o, "BOM_mat")]
        FreeCADGui.updateGui(); self._notify("Couleurs OK.")

# --- Lancement ---
global _panneau_dialog_instance
_panneau_dialog_instance = None
def showPanneauDialog():
    global _panneau_dialog_instance
    if _panneau_dialog_instance is None: _panneau_dialog_instance = PanneauDialog()
    _panneau_dialog_instance.show()
showPanneauDialog()
