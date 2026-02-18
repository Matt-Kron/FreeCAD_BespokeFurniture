import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui, QtWidgets
import sys 

# --- 1. Nouvelle Boîte de Dialogue de Sélection de Panneau ---

class PanneauSelectorDialog(QtWidgets.QDialog):
    """Petite boîte de dialogue pour sélectionner un seul panneau dans une liste."""
    def __init__(self, panneau_names, parent=None):
        super(PanneauSelectorDialog, self).__init__(parent, QtCore.Qt.Window)
        self.setWindowTitle("Choisir le Panneau BOM_mat à Affecter")
        self.selected_panneau = None
        
        main_layout = QtWidgets.QVBoxLayout(self)
        
        label = QtWidgets.QLabel("Sélectionnez le nouveau Panneau à affecter aux objets choisis :")
        main_layout.addWidget(label)
        
        self.panneau_list = QtWidgets.QListView()
        self.panneau_model = PanneauListModel(panneau_names) 
        self.panneau_list.setModel(self.panneau_model)
        self.panneau_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.panneau_list.clicked.connect(self._handle_selection)
        main_layout.addWidget(self.panneau_list)
        
        # Bouton OK/Annuler
        button_layout = QtWidgets.QHBoxLayout()
        self.ok_button = QtWidgets.QPushButton("OK - Affecter")
        self.cancel_button = QtWidgets.QPushButton("Annuler")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.setEnabled(False) 
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)
        
    def _handle_selection(self, index):
        """Met à jour l'état et active le bouton OK."""
        self.selected_panneau = self.panneau_model.get_name(index)
        self.ok_button.setEnabled(True)
        
    def get_selected_panneau(self):
        return self.selected_panneau

# --- 2. Classes de Modèles Qt pour les Vues ---

class ObjectTableModel(QtCore.QAbstractTableModel):
    HEADERS = ["Nom de l'Objet", "Label", "BOM_mat (Actuel)"]

    def __init__(self, objects, parent=None):
        super(ObjectTableModel, self).__init__(parent)
        self._objects = objects

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._objects)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.HEADERS)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        obj = self._objects[row]

        if role == QtCore.Qt.DisplayRole:
            if col == 0:
                return obj.Name
            elif col == 1:
                return obj.Label
            elif col == 2:
                return getattr(obj, "BOM_mat", "N/A")
             
        return None

    def get_object(self, index):
        if not index.isValid():
            return None
        return self._objects[index.row()]
        
    def get_objects(self):
        return self._objects

    def refresh(self):
        self.beginResetModel()
        self.endResetModel()

class PanneauListModel(QtCore.QAbstractListModel):
    def __init__(self, aggregated_names, parent=None):
        super(PanneauListModel, self).__init__(parent)
        self._names = aggregated_names

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._names)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
            
        if role == QtCore.Qt.DisplayRole:
            return self._names[index.row()]
            
        return None
        
    def get_name(self, index):
        if not index.isValid():
            return None
        return self._names[index.row()]
        
    def get_names(self):
        return self._names

    def refresh(self, new_names):
        self.beginResetModel()
        self._names = new_names
        self.endResetModel()


# --- 3. Boîte de Dialogue Principale (Mise à jour des messages) ---

class AssignationPanneauxDialog(QtWidgets.QDialog):
    
    OBJECT_MANAGER_NAME = "Liste panneaux" 
    PROP_NAME = "liste_panneaux"

    def __init__(self):
        super(AssignationPanneauxDialog, self).__init__(FreeCADGui.getMainWindow(), QtCore.Qt.Window) 
        self.setWindowTitle("Gestion des Assignations BOM_mat")
        self.resize(1000, 500)
        
        self.doc_obj_manager = self._get_doc_object_manager()
        self.doc_panneaux_data = self._load_panneau_data()
        
        self._setup_ui()
        self._load_data()
        self._connect_signals()
        
    # --- Méthodes de chargement de données (Inchg.) ---
    
    def _get_doc_object_manager(self):
        if FreeCAD.ActiveDocument is None:
            return None
            
        for obj in FreeCAD.ActiveDocument.Objects:
            if obj.Label == self.OBJECT_MANAGER_NAME and hasattr(obj, self.PROP_NAME):
                return obj
        return None

    def _load_panneau_data(self):
        panneaux_list = []
        if self.doc_obj_manager:
            string_list = getattr(self.doc_obj_manager, self.PROP_NAME)
            
            if string_list and string_list[0].startswith("nom_aggr;"):
                string_list = string_list[1:]

            for line in string_list:
                parts = line.split(";")
                if parts:
                    panneaux_list.append(parts[0]) 
                    
        return sorted(list(set(panneaux_list)))

    def _load_data(self):
        if FreeCAD.ActiveDocument is None:
            self.status_label.setText("Erreur: Aucun document FreeCAD actif.")
            return

        objects_with_bom_mat = [
            obj for obj in FreeCAD.ActiveDocument.Objects 
            if hasattr(obj, "BOM_mat") and obj.ViewObject
        ]
        self.object_model = ObjectTableModel(objects_with_bom_mat)
        self.object_view.setModel(self.object_model)
        
        self.panneau_model = PanneauListModel(self.doc_panneaux_data)
        self.panneau_view.setModel(self.panneau_model)
        
        self.object_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.object_view.horizontalHeader().setSectionResizeMode(
            2, QtWidgets.QHeaderView.Stretch) 
            
        self.status_label.setText(
            f"Prêt. {len(objects_with_bom_mat)} objets avec BOM_mat chargés. {len(self.doc_panneaux_data)} panneaux disponibles.")

    def _setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        top_group = QtWidgets.QGroupBox("Contrôle et Statut")
        top_layout = QtWidgets.QVBoxLayout(top_group)
        
        self.status_label = QtWidgets.QLabel("Initialisation...")
        top_layout.addWidget(self.status_label)

        # Ligne 2: Boutons d'action
        action_layout = QtWidgets.QHBoxLayout()
        
        self.assign_btn = QtWidgets.QPushButton("➡️ AFFECTER BOM_mat (Objets sélectionnés)") 
        self.assign_btn.setToolTip("Ouvre une liste de choix pour définir la nouvelle valeur BOM_mat des objets sélectionnés.")
        action_layout.addWidget(self.assign_btn)
        action_layout.addStretch(1)
        
        self.edit_panneaux_btn = QtWidgets.QPushButton("⚙️ Éditer Liste Panneaux (BdD)")
        action_layout.addWidget(self.edit_panneaux_btn)
        
        self.apply_colors_btn = QtWidgets.QPushButton("🎨 Mettre à jour Couleurs Objets")
        action_layout.addWidget(self.apply_colors_btn)
        
        self.refresh_btn = QtWidgets.QPushButton("🔄 Rafraîchir")
        action_layout.addWidget(self.refresh_btn)
        
        top_layout.addLayout(action_layout)
        main_layout.addWidget(top_group)

        main_layout.addWidget(QtWidgets.QFrame(
            frameShape=QtWidgets.QFrame.HLine, frameShadow=QtWidgets.QFrame.Sunken))

        # Zone principale : Listes
        lists_layout = QtWidgets.QHBoxLayout()

        # Bloc Gauche : Objets
        object_group = QtWidgets.QGroupBox("Objets avec BOM_mat (Sélectionner les objets à inspecter ou modifier)")
        object_layout = QtWidgets.QVBoxLayout(object_group)
        self.object_view = QtWidgets.QTableView()
        self.object_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.object_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        object_layout.addWidget(self.object_view)
        lists_layout.addWidget(object_group, 2)

        # Bloc Droit : Panneaux disponibles (Pour la sélection croisée uniquement)
        panneau_group = QtWidgets.QGroupBox("Panneaux disponibles (Clic : Sélectionne les objets ayant ce panneau)")
        panneau_layout = QtWidgets.QVBoxLayout(panneau_group)
        self.panneau_view = QtWidgets.QListView()
        self.panneau_view.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        panneau_layout.addWidget(self.panneau_view)
        
        lists_layout.addWidget(panneau_group, 1)

        main_layout.addLayout(lists_layout)
        
    def _connect_signals(self):
        self.assign_btn.clicked.connect(self._assign_bom_mat_with_dialog) 
        self.panneau_view.clicked.connect(self._handle_panneau_clicked) 
        self.object_view.clicked.connect(self._clear_panneau_selection)
        
        self.edit_panneaux_btn.clicked.connect(self._open_bdd_panneaux)
        self.apply_colors_btn.clicked.connect(self._apply_colors_from_panneaux)
        self.refresh_btn.clicked.connect(self._refresh_data)

    def _clear_panneau_selection(self, index):
        selected_panneau_index = self.panneau_view.currentIndex()
        if selected_panneau_index.isValid():
            panneau_name = self.panneau_model.get_name(selected_panneau_index)
            obj = self.object_model.get_object(index)
            
            if not hasattr(obj, "BOM_mat") or getattr(obj, "BOM_mat") != panneau_name:
                self.panneau_view.selectionModel().clearSelection()

    def _handle_panneau_clicked(self, index):
        self.panneau_view.selectionModel().setCurrentIndex(
            index, QtCore.QItemSelectionModel.ClearAndSelect
        )
        self._select_objects_by_panneau(index)


    def _assign_bom_mat_with_dialog(self):
        """Ouvre une sous-fenêtre pour choisir le panneau et assigne la valeur."""
        
        # 1. Obtenir les objets sélectionnés
        object_indexes = self.object_view.selectionModel().selectedRows()
        if not object_indexes:
            # MESSAGE DANS LA CONSOLE (au lieu de QMessageBox.warning)
            FreeCAD.Console.PrintWarning("Assignation BOM_mat : Veuillez sélectionner au moins un objet à gauche à modifier.\n")
            return
            
        # 2. Ouvrir le sélecteur de panneau
        selector_dialog = PanneauSelectorDialog(self.doc_panneaux_data, parent=self)
        
        if selector_dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_bom_mat = selector_dialog.get_selected_panneau()
            
            if new_bom_mat:
                self._apply_assignment(object_indexes, new_bom_mat)
            else:
                 # MESSAGE DANS LA CONSOLE (au lieu de QMessageBox.warning)
                 FreeCAD.Console.PrintMessage("Assignation BOM_mat : Aucun panneau sélectionné. Opération annulée par l'utilisateur.\n")
        
    def _apply_assignment(self, object_indexes, new_bom_mat):
        """Fonction interne pour appliquer l'assignation après la sélection du panneau."""
        updated_count = 0
        
        for index in object_indexes:
            obj = self.object_model.get_object(index)
            if hasattr(obj, "BOM_mat"):
                try:
                    setattr(obj, "BOM_mat", new_bom_mat)
                    updated_count += 1
                except Exception as e:
                    FreeCAD.Console.PrintError(f"Échec de l'assignation de BOM_mat pour {obj.Name}: {e}\n")

        # 4. Rafraîchir les vues
        if updated_count > 0:
            FreeCAD.ActiveDocument.recompute()
            self.object_model.refresh()
            
            # MESSAGE DANS LA CONSOLE (au lieu de QMessageBox.information)
            FreeCAD.Console.PrintMessage(
                f"✅ Assignation BOM_mat réussie : {updated_count} objet(s) mis à jour avec la valeur '{new_bom_mat}'.\n"
            )
            
            self._apply_colors_from_panneaux()


    def _select_objects_by_panneau(self, index):
        panneau_name = self.panneau_model.get_name(index)
        
        if not panneau_name:
            self.object_view.selectionModel().clearSelection()
            return
            
        self.object_view.selectionModel().clearSelection()
        
        objects = self.object_model.get_objects()
        
        for row, obj in enumerate(objects):
            if hasattr(obj, "BOM_mat") and getattr(obj, "BOM_mat") == panneau_name:
                obj_index = self.object_model.index(row, 0)
                
                self.object_view.selectionModel().select(
                    obj_index, 
                    QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows 
                )


    def _refresh_data(self):
        if 'BdD_panneaux' in sys.modules:
             try:
                 bdd_module = sys.modules['BdD_panneaux']
                 if hasattr(bdd_module, '_panneau_dialog_instance') and bdd_module._panneau_dialog_instance is not None:
                    bdd_module._panneau_dialog_instance._save_doc_data()
             except Exception:
                 pass
            
        self.doc_panneaux_data = self._load_panneau_data()
        self._load_data() 
        
        self.object_model.dataChanged.emit(self.object_model.index(0, 2), 
                                           self.object_model.index(self.object_model.rowCount() - 1, 2))
        
        self.panneau_model.refresh(self.doc_panneaux_data)


    def _open_bdd_panneaux(self):
        """Ouvre la boîte de dialogue BdD_panneaux.py en l'important (messages console uniquement)."""
        try:
            import BdD_panneaux 
            FreeCAD.Console.PrintMessage("Ouverture de la boîte de dialogue BdD_panneaux.py...\n")
            BdD_panneaux.showPanneauDialog() 
            
        except ImportError:
            # MESSAGE DANS LA CONSOLE (au lieu de QMessageBox.critical)
            FreeCAD.Console.PrintError(
                "ERREUR : Impossible de trouver la macro 'BdD_panneaux.py'. Assurez-vous qu'elle est dans le répertoire des macros.\n"
            )
        except AttributeError:
             # MESSAGE DANS LA CONSOLE (au lieu de QMessageBox.critical)
             FreeCAD.Console.PrintError(
                 "ERREUR : La fonction 'showPanneauDialog()' n'est pas trouvée dans 'BdD_panneaux.py'. Vérifiez le nom de la fonction.\n"
             )
        except Exception as e:
             # MESSAGE DANS LA CONSOLE (au lieu de QMessageBox.critical)
             FreeCAD.Console.PrintError(
                 f"ERREUR INATTENDUE : Une erreur s'est produite lors de l'ouverture de BdD_panneaux : {e}\n"
             )
                
    def _apply_colors_from_panneaux(self):
        
        # if 'BdD_panneaux' in sys.modules:
            # try:
                # bdd_module = sys.modules['BdD_panneaux']
                # if hasattr(bdd_module, '_panneau_dialog_instance') and bdd_module._panneau_dialog_instance is not None:
                    # bdd_module._panneau_dialog_instance._apply_colors_to_objects()
                    # return 
            # except Exception:
                # pass 
        
        doc_obj_manager = self._get_doc_object_manager()
        if not doc_obj_manager:
            FreeCAD.Console.PrintWarning("Couleurs : Impossible de trouver l'objet 'Liste panneaux'.\n")
            return

        color_map = {}
        string_list = getattr(doc_obj_manager, self.PROP_NAME)
        if string_list and string_list[0].startswith("nom_aggr;"): string_list = string_list[1:]

        for line in string_list:
            parts = line.split(";")
            if len(parts) >= 8:
                nom_aggr = parts[0]
                couleur_hex = parts[7].strip()
                try:
                    qcolor = QtGui.QColor(couleur_hex)
                    r_norm = qcolor.red() / 255.0
                    g_norm = qcolor.green() / 255.0
                    b_norm = qcolor.blue() / 255.0
                    color_map[nom_aggr] = (r_norm, g_norm, b_norm, 0.0)
                except Exception:
                    continue 

        if not color_map: 
             FreeCAD.Console.PrintWarning("Couleurs : Aucune couleur de panneau valide n'a été trouvée.\n")
             return

        doc = FreeCAD.ActiveDocument
        colored_count = 0
        
        for obj in doc.Objects:
            try:
                if hasattr(obj, "BOM_mat"):
                    material_name = getattr(obj, 'BOM_mat')
                    if material_name in color_map:
                        target_color = color_map[material_name]
                        target_object = obj
                        if obj.InList:
                            parent = obj.InList[0]
                            if parent.TypeId == 'PartDesign::Body':
                                target_object = parent
                                
                        if hasattr(target_object, 'ViewObject') and hasattr(target_object.ViewObject, 'ShapeColor'):
                            target_object.ViewObject.ShapeColor = target_color
                            colored_count += 1
            except Exception as e:
                FreeCAD.Console.PrintError(f"Erreur lors de l'application de la couleur à {obj.Label}: {e}\n")

        try:
            FreeCADGui.updateGui()
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"Erreur de rafraîchissement de l'interface graphique: {e}\n")
        
        if colored_count > 0:
             FreeCAD.Console.PrintMessage(f"Couleurs appliquées à {colored_count} objets.\n")
        else:
             FreeCAD.Console.PrintMessage("Aucun objet n'a été coloré (vérifier BOM_mat).\n")


# --- Exécution de la Macro ---

global _assignation_panneaux_dialog_instance 
_assignation_panneaux_dialog_instance = None

def showAssignationPanneauxDialog():
    """Lance la boîte de dialogue en mode non modal."""
    global _assignation_panneaux_dialog_instance
    
    if FreeCAD.ActiveDocument is None:
        # MESSAGE DANS LA CONSOLE (au lieu de QMessageBox.warning)
        FreeCAD.Console.PrintWarning("Impossible d'ouvrir l'outil : Veuillez ouvrir un document FreeCAD d'abord.\n")
        return
        
    if _assignation_panneaux_dialog_instance is None:
        _assignation_panneaux_dialog_instance = AssignationPanneauxDialog()
    
    _assignation_panneaux_dialog_instance.show() 
    _assignation_panneaux_dialog_instance.raise_()
    _assignation_panneaux_dialog_instance.activateWindow()

showAssignationPanneauxDialog()