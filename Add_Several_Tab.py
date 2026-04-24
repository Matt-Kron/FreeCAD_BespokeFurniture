import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets
from FreeCAD_BespokeFurniture.Ajouter_Tab import Add_tab
from FreeCAD_BespokeFurniture.lib_menuiserie import *
from FreeCAD_BespokeFurniture.Objects_classes import bspfObj
import os

__dir__ = os.path.dirname(__file__)

def get_selected_objects():
    selection = Gui.Selection.getSelection()
    if len(selection) != 2:
        QtWidgets.QMessageBox.warning(None, "Erreur", "Veuillez sélectionner exactement 2 objets (montants latéraux).")
        return None, None
    return selection[0], selection[1]

def get_useful_height(obj):
    if obj.TypeId == "App::Part":
        body = None
        for child in obj.Group:
            if child.TypeId == "PartDesign::Body":
                body = child
                break
        if not body:
            QtWidgets.QMessageBox.warning(None, "Erreur", "Aucun Body trouvé dans la Part sélectionnée.")
            return None

        additive_box = None
        for feature in body.Group:
            if hasattr(feature, "Shape") and feature.Shape.isValid() and feature.Label == "AdditiveBox":
                additive_box = feature
                break
        if not additive_box:
            QtWidgets.QMessageBox.warning(None, "Erreur", "Aucun AdditiveBox trouvé dans le Body.")
            return None

        bbox = additive_box.Shape.BoundBox
    else:
        bbox = obj.Shape.BoundBox

    return bbox.ZLength

def get_min_height(obj1, obj2):
    height1 = get_useful_height(obj1)
    height2 = get_useful_height(obj2)

    if not height1 or not height2:
        return None

    return min(height1, height2)

class ShelfDialog(QtWidgets.QDialog):
    def __init__(self, min_height, parent=None):
        super(ShelfDialog, self).__init__(parent)
        self.min_height = min_height
        self.objects = []
        self.obj1, self.obj2 = get_selected_objects()
        self.group_index = None
        self.setup_ui()

    def setup_ui(self):
        # Charger le fichier UI
        ui_file = __dir__ + "/Add_Several_Tab.ui"
        self.ui = Gui.PySideUic.loadUi(ui_file)

        # Configurer la fenêtre
        self.setWindowTitle("Ajouter des étagères")
        self.setMinimumWidth(600)

        # Récupérer les widgets depuis le fichier UI
        self.num_shelves_spin = self.ui.findChild(QtWidgets.QSpinBox, "numShelvesSpin")
        self.distribution_equidistant_center = self.ui.findChild(QtWidgets.QRadioButton, "distributionEquidistantCenter")
        self.distribution_equidistant_no_thickness = self.ui.findChild(QtWidgets.QRadioButton, "distributionEquidistantNoThickness")
        self.distribution_arbitrary = self.ui.findChild(QtWidgets.QRadioButton, "distributionArbitrary")
        # self.param_table_view = self.ui.findChild(QtWidgets.QTableView, "paramTableView")
        # self.panel_table_view = self.ui.findChild(QtWidgets.QTableView, "panelTableView")
        self.top_thickness_check = self.ui.findChild(QtWidgets.QCheckBox, "topThicknessCheck")
        self.top_thickness_edit = self.ui.findChild(QtWidgets.QLineEdit, "topThicknessEdit")
        self.bottom_thickness_check = self.ui.findChild(QtWidgets.QCheckBox, "bottomThicknessCheck")
        self.bottom_thickness_edit = self.ui.findChild(QtWidgets.QLineEdit, "bottomThicknessEdit")
        self.sliders_layout = self.ui.findChild(QtWidgets.QHBoxLayout, "slidersLayout")
        self.ok_button = self.ui.findChild(QtWidgets.QPushButton, "okButton")
        self.cancel_button = self.ui.findChild(QtWidgets.QPushButton, "cancelButton")

        # Configurer les modèles pour les QTableView
        # self.param_model = QtGui.QStandardItemModel()
        # self.param_model.setHorizontalHeaderLabels(["Propriété", "Valeur"])
        # self.param_table_view.setModel(self.param_model)
        # self.param_table_view.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        # self.param_table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        # self.param_table_view.selectionModel().selectionChanged.connect(self.on_param_selection_changed)

        # self.panel_model = QtGui.QStandardItemModel()
        # self.panel_model.setHorizontalHeaderLabels(["Nom abrégé", "Épaisseur (mm)"])
        # self.panel_table_view.setModel(self.panel_model)
        # self.panel_table_view.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        # self.panel_table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        # self.panel_table_view.selectionModel().selectionChanged.connect(self.on_panel_selection_changed)

        # Remplir les modèles
        # self.fill_param_model()
        # self.fill_panel_model()

        # Configurer les boutons
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        # Configurer les montants
        # obj1, obj2 = get_selected_objects()
        if self.obj1.TypeId != "App::Part":
            obj1_p = get_parent_part(self.obj1)
        if self.obj2.TypeId != "App::Part":
            obj2_p = get_parent_part(self.obj2)
        if obj1_p.Placement.Base.x < obj2_p.Placement.Base.x:
            obj_left = self.obj1
            obj_right = self.obj2
        self.ui.label_LeftJamb.setText(obj_left.Label)
        self.ui.label_LeftJamb_height.setText(str(get_useful_height(obj_left)))
        # self.ui.label_LeftJamb.setStyleSheet("""
        #     QLabel {
        #         transform: rotate(90deg);
        #         transform-origin: center;
        #         min-height: 100px;
        #         min-width: 50px;
        #     }
        # """)
        self.ui.label_RightJamb.setText(obj_right.Label)
        self.ui.label_RightJamb_height.setText(str(get_useful_height(obj_right)))

        # Configurer les connexions
        self.distribution_equidistant_center.toggled.connect(self.update_sliders)
        self.distribution_equidistant_no_thickness.toggled.connect(self.update_sliders)
        self.distribution_arbitrary.toggled.connect(self.update_sliders)
        self.num_shelves_spin.valueChanged.connect(self.update_sliders)
        self.top_thickness_check.stateChanged.connect(lambda: self.top_thickness_edit.setEnabled(self.top_thickness_check.isChecked()))
        self.bottom_thickness_check.stateChanged.connect(lambda: self.bottom_thickness_edit.setEnabled(self.bottom_thickness_check.isChecked()))

        # Initialiser les sliders
        self.sliders = []
        self.slider_labels = []
        self.update_sliders()

        # Ajouter le layout principal
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.ui)

    # def fill_param_model(self):
    #     if hasattr(App, 'ActiveDocument') and hasattr(App.ActiveDocument, 'VarSet') and hasattr(App.ActiveDocument.VarSet, 'Parametres'):
    #         for prop_name in App.ActiveDocument.VarSet.Parametres.PropertiesList:
    #             if "epaisseur" in prop_name.lower():
    #                 prop_value = getattr(App.ActiveDocument.VarSet.Parametres, prop_name)
    #                 item_prop = QtGui.QStandardItem(prop_name)
    #                 item_value = QtGui.QStandardItem(f"{prop_value:.1f}")
    #                 self.param_model.appendRow([item_prop, item_value])
    #
    # def fill_panel_model(self):
    #     if hasattr(App, 'ActiveDocument') and hasattr(App.ActiveDocument, 'VarSet') and hasattr(App.ActiveDocument.VarSet, 'Liste_Panneaux'):
    #         lines = App.ActiveDocument.VarSet.Liste_Panneaux.split('\n')
    #         for line in lines[1:]:
    #             if line.strip():
    #                 parts = line.split(';')
    #                 if len(parts) >= 5:
    #                     nom_abrege = parts[0]
    #                     try:
    #                         epaisseur = float(parts[4])
    #                         item_nom = QtGui.QStandardItem(nom_abrege)
    #                         item_epaisseur = QtGui.QStandardItem(f"{epaisseur:.1f}")
    #                         self.panel_model.appendRow([item_nom, item_epaisseur])
    #                     except ValueError:
    #                         continue

    # def on_param_selection_changed(self, selected, deselected):
    #     if selected.indexes():
    #         self.panel_table_view.selectionModel().clearSelection()
    #
    # def on_panel_selection_changed(self, selected, deselected):
    #     if selected.indexes():
    #         self.param_table_view.selectionModel().clearSelection()

    def update_sliders(self):
        previous_shelves_number = len(self.sliders)
        for slider in self.sliders:
            self.sliders_layout.removeWidget(slider)
            slider.deleteLater()
        for label in self.slider_labels:
            self.sliders_layout.removeWidget(label)
            label.deleteLater()
        self.sliders = []
        self.slider_labels = []

        num_shelves = self.num_shelves_spin.value()
        for i in range(num_shelves):
            label = QtWidgets.QLabel(f"Étagère {i+1}:")
            slider = QtWidgets.QSlider(QtCore.Qt.Vertical)
            slider.setRange(0, int(self.min_height))
            slider.setValue(int(self.min_height * (i+1) / (num_shelves + 1)))
            slider.setEnabled(self.distribution_arbitrary.isChecked())
            slider.sliderMoved.connect(lambda state, x=i : self.sliderChanged(x))
            self.sliders_layout.addWidget(label)
            self.sliders_layout.addWidget(slider)
            self.slider_labels.append(label)
            self.sliders.append(slider)
            if (i+1) > previous_shelves_number:
                self.addShelf()
                self.updatePosition(i)
        if num_shelves < previous_shelves_number:
            for obj in self.objects[num_shelves:]:
                obj.removeObject()

    def get_selected_thickness(self):
        # if self.param_table_view.selectionModel().selectedIndexes():
        #     index = self.param_table_view.selectionModel().selectedIndexes()[0]
        #     return float(self.param_model.item(index.row(), 1).text())

        # if self.panel_table_view.selectionModel().selectedIndexes():
        #     index = self.panel_table_view.selectionModel().selectedIndexes()[0]
        #     return float(self.panel_model.item(index.row(), 1).text())

        return getattr(App.ActiveDocument.Parametres, 'Hors_tout_epaisseur', 18)

    def get_shelf_positions(self):
        num_shelves = self.num_shelves_spin.value()
        top_thickness = float(self.top_thickness_edit.text()) if self.top_thickness_check.isChecked() else 0
        bottom_thickness = float(self.bottom_thickness_edit.text()) if self.bottom_thickness_check.isChecked() else 0
        shelf_thickness = float(self.get_selected_thickness())

        useful_height = self.min_height - top_thickness - bottom_thickness - (num_shelves * shelf_thickness)

        if self.distribution_equidistant_center.isChecked():
            return [useful_height * (i+1) / (num_shelves + 1) + bottom_thickness + (i * shelf_thickness) + shelf_thickness/2 for i in range(num_shelves)]
        elif self.distribution_equidistant_no_thickness.isChecked():
            return [useful_height * (i+0.5) / num_shelves + bottom_thickness + (i * shelf_thickness) + shelf_thickness/2 for i in range(num_shelves)]
        else:
            return [slider.value() for slider in self.sliders]

    def addShelf(self):
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(self.obj1)
        Gui.Selection.addSelection(self.obj2)
        obj = bspfObj()
        part = Add_tab()
        obj.object = find_additive_box(part)
        if not self.group_index: self.group_index = getMaxShelvesIndex() + 1
        obj.setTag(groupe_etageres = f"ETG{self.group_index}")
        obj.temp = True
        self.objects.append(obj)

    def updatePosition(self, index):
        if isinstance(index, str):
            if index == "all":
                i = 0
                for slider in self.sliders:
                    self.objects[i].part.setExpression('.Placement.Base.z', None)
                    self.objects[i].part.Placement.Base.z = slider.value()
                    i += 1
                # self.objects[0]._object.Document.recompute()
        if isinstance(index, int):
            self.objects[index].part.setExpression('.Placement.Base.z', None)
            self.objects[index].part.Placement.Base.z =  self.sliders[index].value()
            msgCsl(f"{__name__} position étagère {index} à {self.sliders[index].value()}")
            # self.objects[index]._object.Document.recompute()

    def sliderChanged(self, index):
        self.updatePosition(index)

    def accept(self):
        for obj in self.objects:
            obj.temp = False
        super().accept()
        self.reject()

    def reject(self):
        for obj in self.objects:
            if obj.temp: obj.removeObject()
        for slider in self.sliders:
            self.sliders_layout.removeWidget(slider)
            slider.deleteLater()
        self.sliders = []
        super().reject()

def add_shelves(shelf_positions):
    selection = Gui.Selection.getSelection()
    if len(selection) != 2:
        QtWidgets.QMessageBox.warning(None, "Erreur", "Deux objets doivent être sélectionnés pour ajouter les étagères.")
        return

    for pos in shelf_positions:
        Gui.Selection.clearSelection()
        for obj in selection:
            Gui.Selection.addSelection(obj)
        t_part = Add_tab()
        t_part.Placement.Base.z = pos
        

def main():
    obj1, obj2 = get_selected_objects()
    if not obj1 or not obj2:
        return

    min_height = get_min_height(obj1, obj2)
    if not min_height:
        return

    dialog = ShelfDialog(min_height)
    dialog.show()
    # if dialog.exec() == QtWidgets.QDialog.Accepted:
    #     shelf_positions = dialog.get_shelf_positions()
    #     add_shelves(shelf_positions)

main()
