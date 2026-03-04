import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets, QtCore, QtGui
import math

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


# =============================================================================
# CLASSES D'INTERFACE UTILISATEUR (PySide)
# =============================================================================

class DragDropLineEdit(QtWidgets.QLineEdit):
    """
    Un QLineEdit personnalisé qui accepte les événements de glisser-déposer
    pour recevoir des noms d'objets de FreeCAD.
    """

    # Signal émis lorsque le contenu a été mis à jour par un drop
    objectDropped = QtCore.Signal(str, str) # (target_field_name, object_name)

    def __init__(self, target_field_name, *args, **kwargs):
        super(DragDropLineEdit, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.target_field_name = target_field_name
        self.setPlaceholderText("Glissez-déposez un objet ici")
        self.setReadOnly(True)
        # --- MISE À JOUR DU STYLE POUR UN MEILLEUR CONTRASTE ---
        self.setStyleSheet("""
            background-color: #e0e0f8; /* Fond légèrement bleuté */
            color: #1a1a1a;          /* Texte très foncé */
            border: 1px solid #778899; /* Bordure gris-bleu */
            padding: 5px;
            border-radius: 4px;
        """)

    def dragEnterEvent(self, event):
        """Accepte le drop si les données sont du texte (le nom de l'objet)."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Traite l'événement de drop, extrait le nom de l'objet et émet le signal."""
        object_name = event.mimeData().text()

        # Le QListWidget stocke le nom interne de l'objet, ce qui est parfait.
        if object_name:
            # Récupère l'objet réel pour affichage
            obj = App.ActiveDocument.getObject(object_name)
            if obj:
                self.setText(f"{obj.Label} ({obj.Name})")
                self.objectDropped.emit(self.target_field_name, obj.Name)

            event.acceptProposedAction()
        else:
            event.ignore()

class ObjectListWidget(QtWidgets.QListWidget):
    """
    Un QListWidget personnalisé pour permettre de glisser les éléments.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        """Initialise le glisser-déposer avec le nom interne de l'objet."""
        item = self.currentItem()
        if item:
            mimeData = QtCore.QMimeData()
            # On stocke le nom interne de l'objet (stocké dans userData de l'item)
            object_name = item.data(QtCore.Qt.UserRole)
            mimeData.setText(object_name)

            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            drag.exec_(QtCore.Qt.MoveAction)


class AssignmentDialog(QtWidgets.QDialog):
    """
    Boîte de dialogue principale pour l'assignation des objets avec glisser-déposer.
    Les rôles sont ici adaptés pour un meuble vertical (Montant / Traverse inférieure).
    """
    # Nouveaux champs pour les rôles Montant / Traverse inférieure
    FIELD_MONTANT = "montant"
    FIELD_TRAVERSE_INF = "traverse_inferieure"

    def __init__(self, initial_assignments, all_objects_data):
        super().__init__()
        self.setWindowTitle("Assignation du Montant et de la Traverse Inférieure")

        # Dictionnaire pour stocker les noms internes des objets sélectionnés
        self.assigned_objects = {
            self.FIELD_MONTANT: initial_assignments.get(self.FIELD_MONTANT, None),
            self.FIELD_TRAVERSE_INF: initial_assignments.get(self.FIELD_TRAVERSE_INF, None),
        }
        self.all_objects_data = all_objects_data

        self.setupUi()
        self.populate_lists()
        self.update_displays()

        # Ajustement de la largeur
        self.adjustSize()
        new_width = int(self.width() * 1.2)
        if new_width < 720:
             new_width = 720
        self.setFixedWidth(new_width)


    def setupUi(self):
        """Configure les widgets et la mise en page."""

        main_layout = QtWidgets.QVBoxLayout(self)

        # --- Section 1: Glisser-Déposer / Assignation ---
        assign_group = QtWidgets.QGroupBox("Assignation des Rôles")
        assign_layout = QtWidgets.QGridLayout(assign_group)

        # Liste des objets sélectionnés
        assign_layout.addWidget(QtWidgets.QLabel("Objets à Assigner (Glisser)"), 0, 0, 1, 2)
        self.list_widget = ObjectListWidget(self)
        assign_layout.addWidget(self.list_widget, 1, 0, 4, 2)

        # Champs de drop (Mis à jour pour Montant/Traverse inférieure)
        fields = [self.FIELD_MONTANT, self.FIELD_TRAVERSE_INF]
        labels = ["Montant (Contient la Box)", "Traverse Inférieure"]

        self.line_edits = {}
        for i, field_name in enumerate(fields):
            label = labels[i]

            # Label
            assign_layout.addWidget(QtWidgets.QLabel(label + " :"), i + 1, 2)

            # Drop Field
            edit = DragDropLineEdit(field_name, self)
            edit.objectDropped.connect(self.handleObjectDrop)
            assign_layout.addWidget(edit, i + 1, 3)
            self.line_edits[field_name] = edit

        main_layout.addWidget(assign_group)

        # --- Section 2: Détails et Prévisualisation ---
        details_group = QtWidgets.QGroupBox("Détails & Prévisualisation des Modifications")
        details_layout = QtWidgets.QFormLayout(details_group)

        # Champs d'information sur le Montant
        # obj_dessous
        self.current_dessous_label = QtWidgets.QLabel("N/A")

        details_layout.addRow("Valeur actuelle 'obj_dessous' :", self.current_dessous_label)
        details_layout.addRow(QtWidgets.QLabel("---"), QtWidgets.QLabel("---"))

        # Prévisualisation
        self.preview_inf_label = QtWidgets.QLabel("Sélectionnez l'objet...")

        details_layout.addRow("Futur 'obj_dessous' (Nom interne) :", self.preview_inf_label)

        main_layout.addWidget(details_group)

        # --- Section 3: Boutons ---
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def populate_lists(self):
        """Remplit la QListWidget avec les objets initiaux."""
        self.list_widget.clear()
        for obj_name, obj_label in self.all_objects_data.items():
            item = QtWidgets.QListWidgetItem(f"{obj_label} ({obj_name})")
            # Stocke le nom interne de l'objet dans UserRole pour le drag
            item.setData(QtCore.Qt.UserRole, obj_name)
            self.list_widget.addItem(item)

            # Initialise les champs de drop avec les valeurs de la détection automatique
            for field_name, assigned_obj_name in self.assigned_objects.items():
                if assigned_obj_name == obj_name:
                    self.line_edits[field_name].setText(f"{obj_label} ({obj_name})")


    def check_montant_properties(self, obj_name):
        """
        Vérifie si l'objet contient une fonction (Box, AdditiveBox, etc.)
        avec la propriété REQUISE pour un montant : 'obj_dessous'.
        """
        doc = App.ActiveDocument
        obj = doc.getObject(obj_name)

        if not obj:
            return False, "Objet App::Part non trouvé dans le document."

        # Utilise la nouvelle fonction de recherche récursive adaptée aux nouvelles propriétés
        box_object = find_box_with_properties(obj)

        if not box_object:
            return False, "Aucune Box, AdditiveBox, ou forme avec la propriété 'obj_dessous' trouvée à l'intérieur."

        # La recherche récursive garantit que l'objet a la propriété.
        return True, box_object


    def handleObjectDrop(self, target_field_name, object_name):
        """
        Gère la validation et l'assignation après un drop.
        """
        doc = App.ActiveDocument

        # Validation spécifique pour le 'montant'
        if target_field_name == self.FIELD_MONTANT:
            is_valid, box_or_msg = self.check_montant_properties(object_name)
            if not is_valid:
                QtWidgets.QMessageBox.warning(self, "Erreur de Validation",
                    f"L'objet sélectionné n'est pas un montant valide :\n{box_or_msg}")
                # Annule l'assignation dans le champ visuel et logique
                self.line_edits[target_field_name].setText("INVALIDE - Réessayez")
                self.assigned_objects[target_field_name] = None
                self.update_displays()
                return

        # Assignation si la validation passe (ou si ce n'est pas le montant)
        self.assigned_objects[target_field_name] = object_name

        # Mise à jour des affichages (courant et prévisualisation)
        self.update_displays()


    def update_displays(self):
        """
        Met à jour les labels affichant l'état actuel et la prévisualisation.
        """
        montant_name = self.assigned_objects.get(self.FIELD_MONTANT)
        traverse_inf_name = self.assigned_objects.get(self.FIELD_TRAVERSE_INF)

        # --- Mise à jour de l'état actuel du montant ---
        if montant_name:
            doc = App.ActiveDocument
            obj_montant = doc.getObject(montant_name)

            # On vérifie la box à nouveau pour être sûr d'avoir l'objet Box interne
            is_valid, box_obj = self.check_montant_properties(montant_name)

            if is_valid:
                # Lecture des valeurs actuelles (obj_dessous)
                val_dessous = getattr(box_obj, 'obj_dessous', 'N/A')

                # Affiche le nom de l'objet lié si c'est un lien
                dessous_str = val_dessous.Label if hasattr(val_dessous, 'Label') else str(val_dessous)

                self.current_dessous_label.setText(dessous_str)
            else:
                self.current_dessous_label.setText("Box non trouvée ou propriété manquante.")

        else:
            self.current_dessous_label.setText("Aucun montant assigné.")


        # --- Mise à jour de la prévisualisation ---

        # Traverse Inférieure (obj_dessous)
        if traverse_inf_name:
            traverse_inf_obj = App.ActiveDocument.getObject(traverse_inf_name)
            self.preview_inf_label.setText(f"-> {traverse_inf_obj.Name} (Label: {traverse_inf_obj.Label})")
            self.preview_inf_label.setStyleSheet("color: green;")
        else:
            self.preview_inf_label.setText("Traverse inférieure manquante.")
            self.preview_inf_label.setStyleSheet("color: orange;")

# =============================================================================
# LOGIQUE PRINCIPALE DE LA MACRO
# =============================================================================

def find_box_with_properties(part_obj):
    """
    Cherche un objet (Box, AdditiveBox, etc.) avec la propriété
    'obj_dessous' dans l'arborescence de l'App::Part.
    """
    # Propriétés attendues pour le mode vertical
    EXPECTED_PROPERTIES = ["obj_dessous"]
    group_properties = ['Group', 'OutList', 'GroupBase', 'Elements']

    def search_children(parent_obj):
        # 1. Vérification des propriétés de l'objet parent lui-même
        if hasattr(parent_obj, 'PropertiesList') and \
           all(prop in parent_obj.PropertiesList for prop in EXPECTED_PROPERTIES):
            return parent_obj

        # 2. Parcourir les enfants pour la récursion
        for prop_name in group_properties:
            if hasattr(parent_obj, prop_name):
                children = getattr(parent_obj, prop_name)

                if not children:
                    continue

                if isinstance(children, (list, tuple)):
                    for child in children:
                        # 3. Vérification directe des propriétés sur l'enfant
                        if hasattr(child, 'PropertiesList') and \
                           all(prop in child.PropertiesList for prop in EXPECTED_PROPERTIES):
                            return child

                        # 4. Recherche récursive si l'enfant est un autre conteneur
                        if child.TypeId.startswith("PartDesign::Body") or \
                           child.TypeId == "App::Part" or \
                           child.TypeId == "App::DocumentObjectGroup":

                            result = search_children(child)
                            if result is not None:
                                return result
        return None

    return search_children(part_obj)


def run_assignment_macro():
    """
    Fonction principale de la macro.
    """

    # 0. Initialisation et validation du document
    if App.ActiveDocument is None:
        App.Console.PrintError("Veuillez ouvrir un document FreeCAD.\n")
        return

    # Récupérer la sélection
    selected = Gui.Selection.getSelection()

    # 1. Vérification de la sélection
    if len(selected) != 2:
        App.Console.PrintError("Veuillez sélectionner exactement 2 objets.\n")
        QtWidgets.QMessageBox.critical(None, "Erreur de Sélection",
            "Veuillez sélectionner exactement 2 objets dans la vue arborescente (Tree View).")
        return

    # Filtrer pour s'assurer qu'il s'agit d'objets App::Part
    all_parts = [obj for obj in selected if obj.TypeId == "App::Part"]

    if len(all_parts) != 2:
        App.Console.PrintError("La sélection doit contenir exactement 2 objets de type 'App::Part'.\n")
        QtWidgets.QMessageBox.critical(None, "Erreur de Type",
            "Les 2 objets sélectionnés doivent être de type 'App::Part'.")
        return

    # --- Détection automatique ---

    montant = None
    traverse_inferieure = None

    # Chercher le 'montant' (celui avec la propriété obj_dessous)
    for obj in all_parts:
        if find_box_with_properties(obj) is not None:
            if montant is None:
                montant = obj
            else:
                App.Console.PrintWarning(f"Attention: Plus d'un montant potentiel trouvé. Le montant sera: {montant.Label}, l'autre objet sera la traverse.\n")

    # L'autre objet est la traverse inférieure
    remaining_objects = [obj for obj in all_parts if obj is not montant]
    if len(remaining_objects) == 1:
        traverse_inferieure = remaining_objects[0]
    elif montant is None and len(all_parts) == 2:
        # If no montant was found, it means the user might have selected the traverse first
        # and the second object is assumed to be the montant (which will be validated by the dialog)
        # For simplicity in this modified version, we assume if one has the property, it's the montant.
        # If none have it, or both have it, we need to handle it.
        pass # Error will be caught below if montant is still None
    else:
        App.Console.PrintError("Impossible d'identifier clairement le montant ou la traverse inférieure.\n")
        QtWidgets.QMessageBox.critical(None, "Erreur de Détection",
            "Impossible d'identifier un montant et une traverse inférieure uniques parmi les objets sélectionnés.")
        return

    # Si 'montant' est toujours None, c'est qu'aucun des objets n'avait la propriété attendue.
    if montant is None:
        App.Console.PrintError("Aucun des objets sélectionnés n'est un montant valide (propriété 'obj_dessous' manquante).\n")
        QtWidgets.QMessageBox.critical(None, "Erreur de Détection",
            "Aucun des objets sélectionnés n'est un montant valide (propriété 'obj_dessous' manquante).")
        return

    # Après avoir identifié le montant, l'autre objet doit être la traverse inférieure.
    if traverse_inferieure is None:
        # This should ideally not happen if len(all_parts) == 2 and montant was found
        # Re-assign if necessary, making sure traverse_inferieure is the one *not* montant.
        for obj in all_parts:
            if obj is not montant:
                traverse_inferieure = obj
                break
        if traverse_inferieure is None:
            App.Console.PrintError("Impossible d'identifier la traverse inférieure.\n")
            QtWidgets.QMessageBox.critical(None, "Erreur de Détection",
                "Impossible d'identifier la traverse inférieure parmi les objets sélectionnés.")
            return

    # --- Préparation des données pour la boîte de dialogue ---

    initial_assignments = {}
    if montant:
        initial_assignments[AssignmentDialog.FIELD_MONTANT] = montant.Name
    if traverse_inferieure:
        initial_assignments[AssignmentDialog.FIELD_TRAVERSE_INF] = traverse_inferieure.Name

    all_objects_data = {obj.Name: obj.Label for obj in all_parts}

    # 4. Afficher la boîte de dialogue
    dialog = AssignmentDialog(initial_assignments, all_objects_data)

    if dialog.exec() == QtWidgets.QDialog.Accepted:

        # --- 5. Application des modifications ---

        final_assignments = dialog.assigned_objects

        montant_name = final_assignments.get(AssignmentDialog.FIELD_MONTANT)
        traverse_inf_name = final_assignments.get(AssignmentDialog.FIELD_TRAVERSE_INF)

        # Vérification finale des deux objets assignés
        if not all([montant_name, traverse_inf_name]):
            QtWidgets.QMessageBox.critical(None, "Erreur d'Assignation",
                "Veuillez assigner un objet valide à chacun des deux champs.")
            return

        # Récupération des objets
        doc = App.ActiveDocument
        obj_montant = doc.getObject(montant_name)
        obj_traverse_inf = doc.getObject(traverse_inf_name)

        if not all([obj_montant, obj_traverse_inf]):
             App.Console.PrintError("Erreur: Un ou plusieurs objets n'ont pas pu être trouvés dans le document.\n")
             return

        # Double vérification finale du montant
        box_obj = find_box_with_properties(obj_montant)
        if not box_obj:
            QtWidgets.QMessageBox.critical(None, "Erreur Critique",
                f"L'objet {obj_montant.Label} n'est plus un montant valide (propriété 'obj_dessous' manquante). Les modifications n'ont pas été appliquées.")
            return

        # 6. Modification de la propriété 'obj_dessous' de la Box interne

        try:
            # La propriété 'obj_dessous' doit pointer vers la traverse inférieure
            box_obj.obj_dessous = obj_traverse_inf
            box_obj.obj_taille_dessous = find_additive_box(obj_traverse_inf)

            # Recompute pour mettre à jour les liens et la géométrie si nécessaire
            doc.recompute()

            App.Console.PrintMessage("--- MODIFICATIONS APPLIQUÉES AVEC SUCCÈS (Mode Vertical simplifié) ---\n")
            App.Console.PrintMessage(f"Montant ({obj_montant.Label}) mis à jour:\n")
            App.Console.PrintMessage(f"  obj_dessous pointe maintenant vers: {obj_traverse_inf.Name}\n")

        except Exception as e:
            App.Console.PrintError(f"Échec de l'application des modifications : {e}\n")
            QtWidgets.QMessageBox.critical(None, "Erreur d'Application",
                f"Une erreur est survenue lors de la mise à jour des propriétés : {e}")

    else:
        App.Console.PrintMessage("Opération annulée par l'utilisateur.\n")

# Lancement de la macro
if __name__ == '__main__':
    run_assignment_macro()
