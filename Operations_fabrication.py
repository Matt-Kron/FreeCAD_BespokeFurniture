# -*- coding: utf-8 -*-
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
import os
import json

# ====================================================================
# DÉLÉGUÉS ET OUTILS GRAPHIQUES SPÉCIFIQUES
# ====================================================================

class FloatSpinBoxDelegate(QtGui.QItemDelegate):
    def createEditor(self, parent, option, index):
        # Les colonnes d'opérations (index 2 et au-delà) sont éditables
        if index.column() > 1:
            editor = QtGui.QDoubleSpinBox(parent)
            editor.setMinimum(0.0)
            editor.setMaximum(100000.0)
            editor.setDecimals(3)
            editor.setSingleStep(1.0)
            editor.setLocale(QtCore.QLocale(QtCore.QLocale.C)) 
            return editor
        return super(FloatSpinBoxDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.EditRole) 
        editor.setValue(float(value))

    def setModelData(self, editor, model, index):
        value = editor.value()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class ButtonDelegate(QtGui.QItemDelegate):
    clear_column_requested = QtCore.Signal(str) 

    def paint(self, painter, option, index):
        if index.column() == 1 and index.data(QtCore.Qt.UserRole):
            style = QtGui.QApplication.style()
            opt = QtGui.QStyleOptionButton()
            opt.rect = option.rect.adjusted(2, 2, -2, -2)
            opt.text = "Effacer"
            
            if option.state & QtGui.QStyle.State_Sunken:
                opt.state |= QtGui.QStyle.State_Sunken
            
            style.drawControl(QtGui.QStyle.CE_PushButton, opt, painter)
        else:
            super(ButtonDelegate, self).paint(painter, option, index)

    def editorEvent(self, event, model, option, index):
        if index.column() == 1 and event.type() == QtCore.QEvent.MouseButtonRelease:
            if index.data(QtCore.Qt.UserRole):
                internal_name = index.data(QtCore.Qt.UserRole)
                self.clear_column_requested.emit(internal_name)
                return True
        return super(ButtonDelegate, self).editorEvent(event, model, option, index)

class AutoButtonDelegate(QtGui.QItemDelegate):
    """Gère l'affichage et les événements du bouton 'Auto' dans le QTreeWidget."""
    
    # Signal pour notifier la Boîte de Dialogue qu'un bouton 'Auto' a été cliqué
    auto_calculation_requested = QtCore.Signal(str) 

    def paint(self, painter, option, index):
        # Afficher le bouton uniquement si c'est la colonne 2 (Auto) et si un nom interne est stocké
        if index.column() == 2 and index.data(QtCore.Qt.UserRole):
            
            style = QtGui.QApplication.style()
            opt = QtGui.QStyleOptionButton()
            opt.rect = option.rect.adjusted(2, 2, -2, -2) # Marge
            opt.text = "Auto"
            
            if option.state & QtGui.QStyle.State_Sunken:
                opt.state |= QtGui.QStyle.State_Sunken
            
            style.drawControl(QtGui.QStyle.CE_PushButton, opt, painter)
        else:
            super(AutoButtonDelegate, self).paint(painter, option, index)

    def editorEvent(self, event, model, option, index):
        """Gère les clics de souris sur le bouton."""
        if index.column() == 2 and event.type() == QtCore.QEvent.MouseButtonRelease:
            if index.data(QtCore.Qt.UserRole):
                internal_name = index.data(QtCore.Qt.UserRole)
                self.auto_calculation_requested.emit(internal_name)
                return True
        return super(AutoButtonDelegate, self).editorEvent(event, model, option, index)
    
# ====================================================================
# CONFIGURATION ET GESTION DE FICHIERS
# ====================================================================

CONFIG_FILE_NAME = "operations_config.json"
PROPERTY_GROUP = "Fabrication" 

def getConfigFilePath():
    macro_dir = App.getUserMacroDir()
    return os.path.join(macro_dir, CONFIG_FILE_NAME)

def loadOperationsConfig():
    """Charge la configuration des opérations depuis le fichier JSON. Crée le fichier par défaut s'il n'existe pas."""
    config_path = getConfigFilePath()
    
    # --- NOUVELLE CONFIGURATION PAR DÉFAUT (BASÉE SUR LA DEMANDE) ---
    default_config = {
        "Massif": {
            "Op_Delignage": "Délignage",
            "Op_Degauchissage": "Dégauchissage",
            "Op_Rabotage": "Rabotage"
        },
        "Panneau": {
            "Op_Decoupe_Format": "Découpe",
            "Op_Decoupe_Forme": "Découpe forme",
            "Op_Clamex": "Clamex",
            "Op_Autre_Fixation": "Autre fixation",
            "Op_Rainure_Fond": "Rainure fond",
            "Op_Rainure_Cremaillere": "Rainure crémaillère",
            "Op_Autres_Rainures": "Autres rainures"
        },
        "Chant": {
            "Op_Collage_Chant_Grand": "Collage chant grand",
            "Op_Collage_Chant_Petit": "Collage chant petit",
            "Op_Poncage_Chant_Grand": "Ponçage chant grand",
            "Op_Poncage_Chant_Petit": "Ponçage chant petit"
        },
        "Finition": {
            "Op_Poncage_Faces": "Ponçage faces",
            "Op_Rubio": "Rubio",
            "Op_Laque": "Laque",
            "Op_Plaquage": "Plaquage"
        },
        "Quincaillerie": {
            "Op_Fixation_Coulisse": "Fixation coulisse",
            "Op_Fixation_Charniere": "Fixation charnière",
            "Op_Fixation_Tip_on": "Fixation Tip-on",
            "Op_Fixation_Facade_Tiroir": "Fixation Façade tiroir",
            "Op_Fixation_Poignee": "Fixation poignée"
        },
        "Autre": {
            "Op_CAO": "CAO",
            "Op_Montage_Blanc": "Montage à blanc"
        }
    }
    # --- FIN NOUVELLE CONFIGURATION PAR DÉFAUT ---

    if not os.path.exists(config_path):
        try:
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
        except Exception as e:
            App.Console.PrintError(f"Erreur lors de la création du fichier de configuration : {e}\n")
            return {}
    else:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            App.Console.PrintError(f"Erreur lors du chargement du fichier de configuration. Utilisation d'une structure vide : {e}\n")
            return {}

def saveOperationsConfig(config):
    config_path = getConfigFilePath()
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        App.Console.PrintError(f"Erreur lors de la sauvegarde du fichier de configuration : {e}\n")
        return False

# ====================================================================
# MODÈLE DE DONNÉES POUR QTableView
# ====================================================================
class FabricationModel(QtCore.QAbstractTableModel):
    def __init__(self, config, parent=None):
        super(FabricationModel, self).__init__(parent)
        self.config = config
        self.objects = []
        self.internal_operations = []
        self._map_operations()
        self.loadData()
        
    def _map_operations(self):
        self.internal_operations.clear()
        for category, operations in self.config.items():
            for internal_name in operations.keys():
                self.internal_operations.append(internal_name)

    def loadData(self):
        self.beginResetModel()
        self.objects.clear()
        doc = App.ActiveDocument
        if doc:
            PROPERTY_NAME = 'BOM_destination'
            for obj in doc.Objects:
                if hasattr(obj, PROPERTY_NAME) and getattr(obj, PROPERTY_NAME) is True:
                    self.objects.append(obj)
        self.endResetModel()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.objects)

    def columnCount(self, parent=QtCore.QModelIndex()):
        # 1 (Label) + 1 (BOM_mat) + N (Opérations)
        return 2 + len(self.internal_operations)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            if section == 0:
                # Affichage sur 2 lignes
                return "Objet\n(BOM_destination)" 
            elif section == 1:
                # Nouvelle colonne
                return "Matériau\n(BOM_mat)" 
            else:
                internal_name = self.internal_operations[section - 2] # Décalage d'indice
                for ops in self.config.values():
                    if internal_name in ops:
                        # Affichage du nom avec remplacement pour tenter un retour à la ligne
                        display_name = ops[internal_name].replace(' ', '\n', 1) 
                        return display_name
                return internal_name
        
        elif role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Vertical:
            return section + 1
            
        return None

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        obj = self.objects[row]

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if col == 0:
                return obj.Label
            
            elif col == 1: # Colonne Matériau
                if hasattr(obj, 'BOM_mat'):
                    # Ne doit pas être éditable, donc pas de role EditRole
                    return str(getattr(obj, 'BOM_mat'))
                return ""
                
            else: # Colonnes d'opérations (index 2 et suivants)
                prop_name = self.internal_operations[col - 2] # Décalage d'indice
                value = 0.0
                if hasattr(obj, prop_name):
                    try:
                        value = float(getattr(obj, prop_name))
                    except:
                        pass
                
                if role == QtCore.Qt.EditRole:
                    return value 
                
                # Affichage des décimales uniquement si nécessaire
                if abs(value) < 1e-9:
                    return ""
                
                # Vérification si la valeur est proche d'un entier
                if abs(value - round(value)) < 1e-9:
                    return str(int(round(value)))
                
                # Sinon, affichage avec max 3 décimales (et suppression des zéros inutiles)
                return f"{value:.3f}".rstrip('0').rstrip('.')


        if col > 1 and role == QtCore.Qt.TextAlignmentRole: # Les opérations sont à partir de l'index 2
            return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        
        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        # Uniquement les colonnes d'opérations (index > 1) sont modifiables
        if index.isValid() and role == QtCore.Qt.EditRole and index.column() > 1:
            obj = self.objects[index.row()]
            prop_name = self.internal_operations[index.column() - 2] # Décalage d'indice

            new_value = float(value)

            if abs(new_value) > 1e-9:
                if not hasattr(obj, prop_name):
                    display_name = next((ops[prop_name] for ops in self.config.values() if prop_name in ops), prop_name)
                    obj.addProperty("App::PropertyFloat", prop_name, PROPERTY_GROUP, display_name)
                
                setattr(obj, prop_name, new_value)
            
            elif hasattr(obj, prop_name):
                obj.removeProperty(prop_name)

            self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole])
            App.ActiveDocument.recompute()
            Gui.updateGui()
            return True
            
        return False
        
    def flags(self, index):
        default_flags = super(FabricationModel, self).flags(index)
        # Seules les colonnes d'opérations (index > 1) sont éditables
        if index.column() > 1: 
            return default_flags | QtCore.Qt.ItemIsEditable
        return default_flags
        
    def get_used_operations(self):
        used_ops = set()
        for obj in self.objects:
            for prop_name in self.internal_operations:
                if hasattr(obj, prop_name):
                    try:
                        if abs(float(getattr(obj, prop_name))) > 1e-9:
                            used_ops.add(prop_name)
                    except:
                        pass
        return used_ops

# --- Méthodes utilitaires pour la navigation FreeCAD ---

def _get_parent_body(obj):
    """Retourne le Body parent de l'objet, ou None."""
    while obj:
        if obj.TypeId == "PartDesign::Body":
            return obj
        if hasattr(obj, 'Host'):
            obj = obj.Host
        elif hasattr(obj, 'InList') and obj.InList:
            obj = obj.InList[0]
        else:
            return None
    return None
    
def _get_parent_part(obj):
    """
    Retourne l'objet Part parent de l'objet, ou None.
    Ceci est souvent le conteneur de niveau supérieur pour les pièces assemblées.
    """
    current_obj = obj
    while current_obj:
        if current_obj.TypeId == "App::Part":
            return current_obj
        
        # Logique pour remonter la hiérarchie FreeCAD
        if hasattr(current_obj, 'Host'):
            current_obj = current_obj.Host
        elif hasattr(current_obj, 'InList') and current_obj.InList:
            # Si l'objet est un résultat d'opération (InList), on remonte au premier objet d'entrée
            current_obj = current_obj.InList[0]
        else:
            # Si on ne peut plus remonter (par exemple, on est à la racine), on arrête
            return None
    return None


def _is_body_param_type(body):
    """
    MODIFIÉ : Vérifie si le Body contient un objet avec Parametres_Type == 'Traverse'.
    """
    if body and hasattr(body, 'OutList'):
        for obj in body.OutList:
            if hasattr(obj, 'Parametres_Type'):
                try:
                    # Vérification que la valeur de la propriété est bien 'Traverse'
                    if getattr(obj, 'Parametres_Type') == 'Traverse':
                        return True
                except:
                    # Ignore si la propriété n'est pas un nombre
                    pass
    return False

# --- Fin des Méthodes utilitaires ---

# ====================================================================
# CLASSE DE LA BOITE DE DIALOGUE PRINCIPALE
# ====================================================================
class FabricationDialog(QtGui.QDialog):
    def __init__(self):
        super(FabricationDialog, self).__init__()
        self.setWindowTitle("Gestion des Opérations de Fabrication (Grille & Filtres)")
        self.setGeometry(500, 500, 2500, 1000)
        self.config = loadOperationsConfig()
        
        if not self.config:
            self.reject()
            return
            
        self.model = FabricationModel(self.config)
        
        mainLayout = QtGui.QVBoxLayout(self)
        
        # 1. Grille et Panneau de Filtre
        splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        
        self.tableView = self._createTableViewPanel()
        splitter.addWidget(self.tableView)

        self.filterPanel = self._createFilterPanel()
        splitter.addWidget(self.filterPanel)
        
        splitter.setSizes([2050, 450])
        
        mainLayout.addWidget(splitter)

        # 2. Panneau de Gestion des Configurations (taille fixe)
        self.configPanel = self._createConfigManagementPanel()
        mainLayout.addWidget(self.configPanel)
        
        mainLayout.setStretch(0, 1)
        self.configPanel.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        
        # 3. Boutons d'Action (Bas)
        buttonLayout = QtGui.QHBoxLayout()
        self.recomputeButton = QtGui.QPushButton("Actualiser les données")
        self.recomputeButton.clicked.connect(self._recomputeAndRefresh) # CONNECTÉ ICI
        buttonLayout.addWidget(self.recomputeButton)
        
        self.closeButton = QtGui.QPushButton("Fermer")
        self.closeButton.clicked.connect(self.accept)
        buttonLayout.addWidget(self.closeButton)
        mainLayout.addLayout(buttonLayout)
        
        self._updateFilterOptions()
        self.tableView.resizeColumnsToContents()
        
    # --- Création des Widgets (Inchangé) ---
    
    def _createTableViewPanel(self):
        tableView = QtGui.QTableView()
        tableView.setModel(self.model)
        
        # Le délégué doit cibler les colonnes > 1 pour les opérations (excluant Objet et BOM_mat)
        tableView.setItemDelegate(FloatSpinBoxDelegate(tableView))
        
        tableView.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked | 
                                  QtGui.QAbstractItemView.AnyKeyPressed |
                                  QtGui.QAbstractItemView.SelectedClicked)
        
        # Configuration de l'en-tête pour le retour à la ligne
        header = tableView.horizontalHeader()
        # Maintien de l'ajustement auto pour les premières colonnes
        header.setSectionResizeMode(0, QtGui.QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(1, QtGui.QHeaderView.ResizeToContents) 
        header.setStretchLastSection(False)
        
        # Hauteur suffisante pour deux lignes (nécessaire sans setWordWrap)
        header.setMinimumHeight(45) 
        
        # Pour les vieilles versions de PySide, il n'y a pas de setWordWrap. 
        # On se contente d'utiliser \n dans le headerData et d'augmenter la hauteur.
        # header.setWordWrap(True) # <- C'était la ligne problématique

        return tableView
    
    def _createFilterPanel(self):
        """Crée le panneau avec le QTreeWidget pour les filtres hiérarchiques."""
        groupBox = QtGui.QGroupBox("Filtrage des Colonnes")
        groupBoxLayout = QtGui.QVBoxLayout(groupBox)

        self.filterTree = QtGui.QTreeWidget()
        self.filterTree.setHeaderLabels(["Opération", "Effacer", "Auto"])
        self.filterTree.setColumnCount(3)
        
        # Délégué pour le bouton d'Effacement (Colonne 1)
        self.buttonDelegate = ButtonDelegate(self.filterTree)
        self.buttonDelegate.clear_column_requested.connect(self._clearColumn)
        self.filterTree.setItemDelegateForColumn(1, self.buttonDelegate)
        
        # Délégué pour le bouton Auto (Colonne 2)
        self.autoDelegate = AutoButtonDelegate(self.filterTree)
        self.autoDelegate.auto_calculation_requested.connect(self._runAutomaticCalculation) 
        self.filterTree.setItemDelegateForColumn(2, self.autoDelegate) 
        
        # Connecter le signal de changement d'état de la case à cocher
        self.filterTree.itemChanged.connect(self._handleItemChanged)

        groupBoxLayout.addWidget(self.filterTree)
        return groupBox

    # --- Logique de Rechargement / Configuration (Inchangé) ---
    
    def _createSeparator(self, orientation):
        separator = QtGui.QFrame()
        if orientation == QtCore.Qt.Horizontal:
            separator.setFrameShape(QtGui.QFrame.HLine)
        else:
            separator.setFrameShape(QtGui.QFrame.VLine)
        separator.setFrameShadow(QtGui.QFrame.Sunken)
        return separator

    def _createConfigManagementPanel(self):
        group = QtGui.QGroupBox("Gestion de la Configuration")
        layout = QtGui.QHBoxLayout(group)
        cat_label = QtGui.QLabel("Ajouter Catégorie:")
        self.newCatName = QtGui.QLineEdit()
        self.newCatName.setPlaceholderText("Nom de la nouvelle catégorie")
        cat_button = QtGui.QPushButton("Ajouter Catégorie")
        cat_button.clicked.connect(self._addCategory)
        op_label = QtGui.QLabel("Ajouter Opération:")
        self.newOpCat = QtGui.QComboBox()
        self.newOpName = QtGui.QLineEdit()
        self.newOpName.setPlaceholderText("Nom affiché (ex: Coupe onglet)")
        self.newOpInternalName = QtGui.QLineEdit()
        self.newOpInternalName.setPlaceholderText("Nom interne (ex: Op_Coupe_Onglet)")
        op_button = QtGui.QPushButton("Ajouter Opération")
        op_button.clicked.connect(self._addOperation)

        layout.addWidget(cat_label)
        layout.addWidget(self.newCatName)
        layout.addWidget(cat_button)
        separator = self._createSeparator(QtCore.Qt.Vertical)
        layout.addWidget(separator)
        layout.addWidget(op_label)
        layout.addWidget(self.newOpCat)
        layout.addWidget(self.newOpName)
        layout.addWidget(self.newOpInternalName)
        layout.addWidget(op_button)

        self._updateCategoryComboBox()
        return group
    
    def _recomputeAndRefresh(self):
        """Forcer l'actualisation de FreeCAD et recharger les données, puis mettre à jour l'interface."""
        App.ActiveDocument.recompute()
        self.model.loadData() 
        self._refreshInterfaceStructure()
        self.tableView.resizeColumnsToContents()
        Gui.updateGui()

    def _updateCategoryComboBox(self):
        self.newOpCat.clear()
        self.newOpCat.addItems(sorted(self.config.keys()))

    def _addCategory(self):
        cat_name = self.newCatName.text().strip()
        if not cat_name:
            QtGui.QMessageBox.warning(self, "Erreur", "Le nom de la catégorie ne peut pas être vide.")
            return
        if cat_name in self.config:
            QtGui.QMessageBox.warning(self, "Erreur", f"La catégorie '{cat_name}' existe déjà.")
            return

        self.config[cat_name] = {}
        saveOperationsConfig(self.config)
        self.newCatName.clear()
        self._refreshInterfaceStructure()
        self._updateCategoryComboBox()


    def _addOperation(self):
        category = self.newOpCat.currentText()
        display_name = self.newOpName.text().strip()
        internal_name = self.newOpInternalName.text().strip()

        if not category or not display_name or not internal_name:
            QtGui.QMessageBox.warning(self, "Erreur", "Tous les champs doivent être remplis.")
            return
            
        if not internal_name.startswith("Op_"):
            internal_name = "Op_" + internal_name.replace(" ", "_").strip()
            
        if internal_name in [key for ops in self.config.values() for key in ops.keys()]:
            QtGui.QMessageBox.warning(self, "Erreur", f"Le nom interne '{internal_name}' existe déjà.")
            return

        self.config[category][internal_name] = display_name
        saveOperationsConfig(self.config)
        
        self.newOpName.clear()
        self.newOpInternalName.clear()
        self._refreshInterfaceStructure()
        self.tableView.resizeColumnsToContents()

    def _refreshInterfaceStructure(self):
        self.model = FabricationModel(self.config) 
        self.tableView.setModel(self.model)
        self.tableView.setItemDelegate(FloatSpinBoxDelegate(self.tableView))
        self._updateFilterOptions()
        
    # --- Logique de Filtrage (avec décalage d'index) ---
    
    def _updateParentCheckState(self, parent_item, total_children, checked_count):
        if total_children == 0:
            return
            
        if checked_count == total_children:
            parent_item.setCheckState(0, QtCore.Qt.Checked)
        elif checked_count == 0:
            parent_item.setCheckState(0, QtCore.Qt.Unchecked)
        else:
            parent_item.setCheckState(0, QtCore.Qt.PartiallyChecked)

    def _handleItemChanged(self, item, column):
        """Gère la propagation des états de coche lorsque l'utilisateur clique."""
        
        # Déconnecter temporairement pour éviter une boucle infinie de signaux
        self.filterTree.itemChanged.disconnect(self._handleItemChanged)

        try:
            state = item.checkState(0)
            
            # A. Propagation Parent -> Enfants (si ce n'est pas un état partiel)
            if item.childCount() > 0 and state != QtCore.Qt.PartiallyChecked:
                for i in range(item.childCount()):
                    child = item.child(i)
                    if child.childCount() == 0: 
                        child.setCheckState(0, state)
            
            # B. Propagation Enfant -> Parents
            # La propagation vers le haut n'est nécessaire que si ce n'est pas l'élément global "Toutes"
            if item.parent():
                parent = item.parent()
                
                # Mise à jour des parents uniquement si l'élément changeant est une opération (enfant sans enfant)
                if item.childCount() == 0:
                    
                    # 1. Mise à jour de la Catégorie
                    if parent.parent(): # Si le parent est la Catégorie (et pas "Toutes")
                        total_children = parent.childCount()
                        checked_count = sum(1 for i in range(total_children) if parent.child(i).checkState(0) == QtCore.Qt.Checked)
                        self._updateParentCheckState(parent, total_children, checked_count)
                        
                        # 2. Propagation à "Toutes"
                        global_parent = parent.parent()
                        total_categories = global_parent.childCount()
                        checked_categories = 0
                        
                        for i in range(total_categories):
                            cat_item = global_parent.child(i)
                            if cat_item.checkState(0) == QtCore.Qt.Checked:
                                checked_categories += 1
                            elif cat_item.checkState(0) == QtCore.Qt.PartiallyChecked:
                                checked_categories = -1 
                                break
                                
                        if checked_categories == -1:
                            global_parent.setCheckState(0, QtCore.Qt.PartiallyChecked)
                        elif checked_categories == total_categories:
                            global_parent.setCheckState(0, QtCore.Qt.Checked)
                        else:
                            global_parent.setCheckState(0, QtCore.Qt.Unchecked)

            # C. Application du filtre de colonne (uniquement pour les opérations)
            
            internal_name = item.data(1, QtCore.Qt.UserRole)
            
            # Correction : Vérifier explicitement que le nom interne existe dans notre dictionnaire de référence
            # (Cela élimine les KeyErrors si l'élément parent génère un signal avant que l'enfant ne soit traité)
            if internal_name in self.operationItems:
                _, col_index = self.operationItems[internal_name]
                
                show = (state == QtCore.Qt.Checked)
                self.tableView.setColumnHidden(col_index, not show)

        finally:
            # Reconnecter le signal
            self.filterTree.itemChanged.connect(self._handleItemChanged)
            
    def _updateFilterOptions(self):
        """Recrée les éléments du QTreeWidget et filtre l'affichage au démarrage."""
        
        # --- 1. DÉCONNEXION pour éviter la réinitialisation par le signal de propagation ---
        try:
            self.filterTree.itemChanged.disconnect(self._handleItemChanged)
        except RuntimeError:
            # RuntimeError est levée si la connexion n'existe pas (ce qui est normal après un clear)
            pass 
        
        # ----------------------------------------------------------------------------------
        
        self.filterTree.clear()
        self.operationItems = {}
        used_operations = self.model.get_used_operations()
        
        # --- 2. Construction de la Hiérarchie ---
        
        # Élément Global "Toutes"
        all_item = QtGui.QTreeWidgetItem(self.filterTree, ["Toutes"])
        all_item.setFlags(all_item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
        all_item.setCheckState(0, QtCore.Qt.Unchecked) 
        all_item.setData(2, QtCore.Qt.UserRole, "ALL_OPERATIONS") 

        global_total_ops = 0
        
        for category_name, operations in self.config.items():
            category_item = QtGui.QTreeWidgetItem(all_item, [category_name])
            category_item.setFlags(category_item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
            
            category_checked_count = 0
            
            for internal_name, display_name in operations.items():
                # Décalage de +2 (Objet, Matériau, Opérations)
                col_index = self.model.internal_operations.index(internal_name) + 2 
                is_visible = internal_name in used_operations
                
                op_item = QtGui.QTreeWidgetItem(category_item, [display_name])
                op_item.setFlags(op_item.flags() | QtCore.Qt.ItemIsUserCheckable)
                
                # C'EST LA LIGNE D'INITIALISATION
                op_item.setCheckState(0, QtCore.Qt.Checked if is_visible else QtCore.Qt.Unchecked)
                
                op_item.setData(1, QtCore.Qt.UserRole, internal_name) 
                op_item.setData(2, QtCore.Qt.UserRole, internal_name) 
                self.tableView.setColumnHidden(col_index, not is_visible)
                self.operationItems[internal_name] = (op_item, col_index)
                
                if is_visible:
                    category_checked_count += 1
                
                global_total_ops += 1
            
            # Application de l'état Partiel/Coché/Décoché au parent Catégorie
            self._updateParentCheckState(category_item, len(operations), category_checked_count)
            
        # --- 3. Finalisation de l'Élément Global "Toutes" ---
        if global_total_ops > 0:
            total_categories = all_item.childCount()
            checked_cats = sum(1 for i in range(total_categories) if all_item.child(i).checkState(0) == QtCore.Qt.Checked)
            partial_cats = sum(1 for i in range(total_categories) if all_item.child(i).checkState(0) == QtCore.Qt.PartiallyChecked)

            if partial_cats > 0 or (checked_cats > 0 and checked_cats < total_categories):
                 all_item.setCheckState(0, QtCore.Qt.PartiallyChecked)
            elif checked_cats == total_categories:
                 all_item.setCheckState(0, QtCore.Qt.Checked)
            else:
                 all_item.setCheckState(0, QtCore.Qt.Unchecked)
             
        self.filterTree.expandAll()
        self.filterTree.resizeColumnToContents(0)
        
        # --- 4. RECONNEXION ET AJUSTEMENT DE LARGEUR ---
        self.filterTree.itemChanged.connect(self._handleItemChanged)
        
        # Ajustement des colonnes 'Effacer' et 'Auto'
        self.filterTree.resizeColumnToContents(1) # Colonne 'Effacer'
        self.filterTree.resizeColumnToContents(2) # Colonne 'Auto'


    def _clearColumn(self, internal_name):
        reply = QtGui.QMessageBox.question(self, 'Confirmation',
            f"Êtes-vous sûr de vouloir effacer toutes les quantités pour l'opération '{internal_name}' dans le document actif ? Cela supprimera la propriété sur tous les objets.",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.No:
            return

        try:
            # Décalage de +2 (Objet, Matériau, Opérations)
            col_index = self.model.internal_operations.index(internal_name) + 2
            
            for row in range(self.model.rowCount()):
                index = self.model.index(row, col_index)
                self.model.setData(index, 0.0, QtCore.Qt.EditRole) 
                
            App.Console.PrintMessage(f"Colonne '{internal_name}' effacée pour tous les objets.\n")
            
            self.model.loadData()
            self._refreshInterfaceStructure()

        except Exception as e:
            App.Console.PrintError(f"Erreur lors de l'effacement de la colonne : {e}\n")

# --- Logique de Calcul Automatique ---

    def _runAutomaticCalculation(self, internal_name):
        
        if internal_name == "ALL_OPERATIONS":
            operations_to_process = self.model.internal_operations
            # Optionnel : demander confirmation pour tout le document
            if QtGui.QMessageBox.question(self, "Confirmation Auto", 
                "Êtes-vous sûr de vouloir exécuter le calcul automatique pour TOUTES les opérations ? Les quantités seront écrasées.",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
                return
        else:
            operations_to_process = [internal_name]

        App.Console.PrintMessage(f"Démarrage du calcul automatique pour: {internal_name}\n")

        # 1. Pré-calcul : Construction des listes d'objets (pour éviter les boucles FreeCAD inutiles)
        objects = self.model.objects 
        model_ops = self.model.internal_operations
        
        # Dictionnaire pour stocker les résultats {obj: {Op_Name: Qty}}
        results = {}

        # NOUVEAU PRÉ-CALCUL POUR COULISSES (OP_FIXATION_COULISSE)
        # 1. Compter le nombre de références de panneaux latéraux de tiroir par Body
        drawer_references_per_body = {} 
        tiroir_list = [o for o in objects if "tiroir" in o.Label.lower()]
        tiroir_params = []
        for t_obj in tiroir_list:
            # for ob in _get_parent_body(t_obj).OutList:
            for ob in t_obj.getParentGeoFeatureGroup().OutList:
                if "tiroir param" in ob.Label.lower() or "tiroir_param" in ob.Label.lower():
                    tiroir_params.append(ob)
        # print(f"Liste des tiroirs {[ob.Label for ob in tiroir_params]}")

        for t_obj in tiroir_params:
            for prop_name in ['obj_taille_gauche', 'obj_taille_droit']:
                if hasattr(t_obj, prop_name):
                    target_obj = getattr(t_obj, prop_name)
                    
                    if target_obj: 
                        # target_obj_body = _get_parent_body(target_obj)
                        target_obj_body = target_obj.getParentGeoFeatureGroup()
                        # print(f"target_obj {target_obj.Label} target_obj_body {target_obj_body.Label}")
                        if target_obj_body:
                            # Incrémenter le compte pour ce Body (chaque Body supporte X tiroirs)
                            # print(f"Objet {target_obj.Label} body {target_obj_body.Label} nombre de tiroirs {drawer_references_per_body.get(target_obj_body, 0)}")
                            drawer_references_per_body[target_obj_body] = drawer_references_per_body.get(target_obj_body, 0) + 1
        # FIN NOUVEAU PRÉ-CALCUL
        
        # 2. Exécution des règles (Boucle sur les objets)
        for obj in objects:
            
            label = obj.Label.lower()
            
            # Récupération du matériau (BOM_mat)
            bom_mat = ""
            if hasattr(obj, 'BOM_mat'):
                try:
                    bom_mat = str(getattr(obj, 'BOM_mat')).lower()
                except:
                    pass
            
            # --- CORRECTION ROBUSTE POUR Z_LENGTH (Adresse l'AttributeError) ---
            z_length = 0.0
            if hasattr(obj, 'Shape') and hasattr(obj.Shape, 'BoundBox'):
                try:
                    # Tenter d'accéder à la valeur de la Quantity (si c'est bien une Quantity)
                    z_length = obj.Shape.BoundBox.ZLength.Value
                except AttributeError:
                    # Si ZLength est déjà un float (l'erreur précédente)
                    z_length = obj.Shape.BoundBox.ZLength
                except Exception:
                    # Gérer les autres cas où la géométrie est invalide ou manquante
                    z_length = 0.0
            # -------------------------------------------------------------------
            
            body =obj.getParentGeoFeatureGroup() # = _get_parent_body(obj)
            # is_in_param_caisson utilise maintenant la vérification de la valeur '1.0'
            is_in_param_caisson = _is_body_param_type(body)
            
            
            # --- RÈGLES DE DÉDUCTION ---
            
            # Règle : CAO (Op_CAO)
            if "Op_CAO" in operations_to_process:
                results.setdefault(obj, {})["Op_CAO"] = 1.0

            # Règle : Montage à blanc (Op_Montage_Blanc)
            if "Op_Montage_Blanc" in operations_to_process:
                results.setdefault(obj, {})["Op_Montage_Blanc"] = 1.0

            # Règle : Poignée (Op_Fixation_Poignee)
            if "Op_Fixation_Poignee" in operations_to_process and ("porte" in label or "tiroir" in label):
                results.setdefault(obj, {})["Op_Fixation_Poignee"] = 1.0
                
            # Règle : Façade Tiroir (Op_Fixation_Facade_Tiroir) - NOUVELLE RÈGLE
            if "Op_Fixation_Facade_Tiroir" in operations_to_process and "tiroir" in label:
                results.setdefault(obj, {})["Op_Fixation_Facade_Tiroir"] = 1.0
                
            # Règle : Coulisse (Op_Fixation_Coulisse)
            if "Op_Fixation_Coulisse" in operations_to_process:
                # Le panneau doit être un "montant" ("mt ") pour recevoir l'opération
                # print(f"Liste des tiroirs {tiroir_params}")
                # print(f"Liste des panneaux référencés dans liste des tiroirs {bodies_with_referenced_panels}")
                if "mt " in label: 
                    obj_body = obj.getParentGeoFeatureGroup() # _get_parent_body(obj)
                    
                    # Récupérer le nombre de références de tiroirs (coulisses) pour ce Body
                    qty = drawer_references_per_body.get(obj_body, 0)
                    
                    if qty > 0:
                        results.setdefault(obj, {})["Op_Fixation_Coulisse"] = qty
            
            # Règle : Charnières (Op_Fixation_Charniere)
            if "Op_Fixation_Charniere" in operations_to_process and "porte" in label:
                qty = 0
                if 0 < z_length <= 1000:
                    qty = 2
                elif 1000 < z_length <= 1500:
                    qty = 3
                elif z_length > 1500:
                    qty = 4
                
                if qty > 0:
                    results.setdefault(obj, {})["Op_Fixation_Charniere"] = qty

            # Règle : Clamex (Op_Clamex)
            if "Op_Clamex" in operations_to_process:
                # 1. Règle Tv inf/sup
                if "tv inf" in label or "tv sup" in label or "mt i" in label:
                    results.setdefault(obj, {})["Op_Clamex"] = 4.0
                
                # 2. Règle tablette caisson (MAINTENANT AVEC is_in_param_caisson qui vérifie la valeur 1)
                if "Op_Clamex" not in results.get(obj, {}) and "tablette caisson" in label and is_in_param_caisson:
                    results.setdefault(obj, {})["Op_Clamex"] = 4.0

            # Règle : Rainure fond (Op_Rainure_Fond)
            if "Op_Rainure_Fond" in operations_to_process and ("tv " in label or "mt " in label or "tablette caisson " in label):
                
                # 1. Identifier le conteneur Part de l'objet de la grille
                parent_part = _get_parent_part(obj)
                
                if parent_part:
                    
                    # 2. Identifier tous les objets 'fond' dans la liste des objets BOM
                    fond_objects = [o for o in objects if "fond" in o.Label.lower()]

                    for fond_obj in fond_objects:
                        # 3. Vérifier si le fond_obj référence le parent_part via les propriétés
                        for prop_name in ["obj_dessus", "obj_dessous", "obj_gauche", "obj_droit"]:
                            # Comparaison par objet FreeCAD
                            if hasattr(fond_obj, prop_name) and getattr(fond_obj, prop_name) == parent_part:
                                results.setdefault(obj, {})["Op_Rainure_Fond"] = 1.0
                                break # 1 seule rainure nécessaire
                        
                        # 4. Sortir de la boucle fond_objects si l'opération a déjà été ajoutée pour l'objet actuel
                        if "Op_Rainure_Fond" in results.get(obj, {}):
                            break

            # --- NOUVELLES RÈGLES BASÉES SUR LE MATÉRIAU (BOM_mat) ---
            
            # 1. Ponçage de Face et Chant (latte chene, valchromat, mdf)
            sanding_mats = ["latte chene", "valchromat", "mdf"]
            needs_sanding = any(m in bom_mat for m in sanding_mats)
            
            if needs_sanding:
                if "Op_Poncage_Faces" in operations_to_process:
                    results.setdefault(obj, {})["Op_Poncage_Faces"] = 2.0
                if "Op_Poncage_Chant_Grand" in operations_to_process:
                    results.setdefault(obj, {})["Op_Poncage_Chant_Grand"] = 2.0
                if "Op_Poncage_Chant_Petit" in operations_to_process:
                    results.setdefault(obj, {})["Op_Poncage_Chant_Petit"] = 2.0
            
            # 2. Rubio (latte chene, valchromat)
            rubio_mats = ["latte chene", "valchromat"]
            needs_rubio = any(m in bom_mat for m in rubio_mats)
            
            if needs_rubio:
                if "Op_Rubio" in operations_to_process:
                    results.setdefault(obj, {})["Op_Rubio"] = 2.0
            
            # 3. Collage Chant (latte chene)
            if "latte chene" in bom_mat:
                
                # a. Règle tablette caisson ou mt
                if "tablette caisson" in label or "mt " in label or "tv " in label:
                    if "Op_Collage_Chant_Grand" in operations_to_process:
                        results.setdefault(obj, {})["Op_Collage_Chant_Grand"] = 1.0
                
                # b. Règle porte ou tiroir (Écrase la règle 'a' si elle s'applique aussi)
                if "porte" in label or "tiroir" in label:
                    if "Op_Collage_Chant_Grand" in operations_to_process:
                        results.setdefault(obj, {})["Op_Collage_Chant_Grand"] = 2.0
                    if "Op_Collage_Chant_Petit" in operations_to_process:
                        results.setdefault(obj, {})["Op_Collage_Chant_Petit"] = 2.0


        # 3. Application des résultats au modèle FreeCAD
        modified_indexes = []
        for obj, op_quantities in results.items():
            row = objects.index(obj) 
            for op_name, qty in op_quantities.items():
                if op_name in model_ops:
                    # Décalage de +2 (Objet, Matériau, Opérations)
                    col = model_ops.index(op_name) + 2
                    index = self.model.index(row, col)
                    
                    # Mise à jour via setData pour créer/supprimer la propriété si nécessaire
                    self.model.setData(index, qty, QtCore.Qt.EditRole) 
                    modified_indexes.append(index)

        # 4. Rafraîchissement de l'interface
        if modified_indexes:
            App.ActiveDocument.recompute()
            # Un simple rechargement est suffisant pour les données et le rafraichissement
            self._recomputeAndRefresh() 
            App.Console.PrintMessage(f"Calcul automatique terminé. {len(modified_indexes)} propriétés mises à jour.\n")
        else:
            App.Console.PrintMessage("Calcul automatique terminé. Aucune propriété mise à jour. (Vérifiez les labels et les références FreeCAD).\n")
            
            
# ====================================================================
# FONCTION PRINCIPALE DE LA MACRO
# ====================================================================
def run():
    if App.ActiveDocument is None:
        App.newDocument()
        
    dialog = FabricationDialog()
    if dialog.layout(): 
        dialog.exec_()
    else:
        App.Console.PrintWarning("La boîte de dialogue n'a pas pu être créée.\n")

if __name__ == '__main__':
    run()
