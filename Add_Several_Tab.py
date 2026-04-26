import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets
from FreeCAD_BespokeFurniture.Ajouter_Tab import Add_tab
from FreeCAD_BespokeFurniture.Ajouter_Mti import Add_mti
from FreeCAD_BespokeFurniture.lib_menuiserie import *
from FreeCAD_BespokeFurniture.Objects_classes import bspfObj
from FreeCAD_BespokeFurniture.PartBetween2Other import classify_object
import os

__dir__ = os.path.dirname(__file__)

def get_selected_objects():
    selection = Gui.Selection.getSelection()
    if len(selection) != 2:
        QtWidgets.QMessageBox.warning(None, "Erreur", "Veuillez sélectionner exactement 2 objets (montants latéraux).")
        return None, None
    return selection[0], selection[1]

def get_useful_height(obj, orientation):
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
            if hasattr(feature, "Shape") and feature.Shape.isValid() and feature.TypeId == "PartDesign::AdditiveBox":
                additive_box = feature
                break
        if not additive_box:
            QtWidgets.QMessageBox.warning(None, "Erreur", f"Aucun AdditiveBox trouvé dans le Body {body.Label}.")
            return None

        bbox = additive_box.Shape.BoundBox
    else:
        bbox = obj.Shape.BoundBox

    return bbox.ZLength if orientation == "V" else bbox.XLength

def get_min_height(obj1, obj2, orientation):
    height1 = get_useful_height(obj1, orientation)
    height2 = get_useful_height(obj2, orientation)

    if not height1 or not height2:
        return None

    return min(height1, height2)

def addObj(fc_obj):
    obj = bspfObj()
    obj.object = fc_obj
    obj.temp = False
    return obj

class ShelfDialog(QtWidgets.QDialog):
    def __init__(self, min_height, obj1, obj2, parent=None, mode = "V0", duplicate = None):
        super(ShelfDialog, self).__init__(parent)
        self.min_height = min_height
        self.mode = mode
        msgCsl(f"{__name__} self.mode = {self.mode}")
        self.objects = []
        self.group_index = None
        self.backProp = False
        self.group_type = None
        if int(self.mode[1]):
            self.duplicate = duplicate
            self.initObj()
        self.obj1, self.obj2 = obj1, obj2
        self.heightObjRef = obj1 if get_useful_height(obj1, mode[0]) == min_height else obj2
        self.placementProp = ".Placement.Base.z" if mode[0] == "V" else ".Placement.Base.x"

        self.setup_ui()

    def initObj(self):
        objects = [addObj(self.duplicate)]
        self.group_index = int(getObjTag(self.duplicate)["groupe_etageres"][4:])
        target_group = getObjTag(self.duplicate)["groupe_etageres"]
        fcDoc = self.duplicate.Document
        for o in fcDoc.Objects:
            tag_prop = getObjTag(o)
            if tag_prop:
                if tag_prop["groupe_etageres"] == target_group and o.Name != self.duplicate.Name:
                    objects.append(addObj(o))
        self.objects = sorted(objects, key=lambda o:o.part.Placement.Base.z)
        self.backProp = self.objects[0].object.fond
        self.group_type = getObjTag(self.objects[0].object)["groupe_etageres"][:4]

    def setup_ui(self):
        # Charger le fichier UI
        ui_file = __dir__ + "/Add_Several_Tab.ui"
        self.ui = Gui.PySideUic.loadUi(ui_file)

        # Configurer la fenêtre
        self.setWindowTitle("Ajouter des étagères")
        self.setMinimumWidth(600)

        # Récupérer les widgets depuis le fichier UI
        self.num_shelves_spin = self.ui.findChild(QtWidgets.QSpinBox, "numShelvesSpin")
        if self.objects:
            self.num_shelves_spin.setValue(len(self.objects))
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
        self.ui.checkBox_BackProp.setChecked(self.backProp)
        if self.group_type:
            if self.group_type[3] == "C": self.distribution_equidistant_center.setChecked(True)
            if self.group_type[3] == "T": self.distribution_equidistant_no_thickness.setChecked(True)
            if self.group_type[3] == "A": self.distribution_arbitrary.setChecked(True)
        if self.objects:
            props = [item[0] for item in self.objects[0].part.ExpressionEngine]
            if self.placementProp in props:
                self.ui.relativePosition.setChecked(True)
            else:
                self.ui.absolutePosition.setChecked(True)

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
        # if self.obj1.TypeId != "App::Part":
        #     obj1_p = get_parent_part(self.obj1)
        # if self.obj2.TypeId != "App::Part":
        #     obj2_p = get_parent_part(self.obj2)
        if self.mode[0] == "V":
            if self.obj1.Placement.Base.x < self.obj2.Placement.Base.x:
                obj_left = self.obj1
                obj_right = self.obj2
        if self.mode[0] == "H":
            if self.obj1.Placement.Base.z < self.obj2.Placement.Base.z:
                obj_left = self.obj1
                obj_right = self.obj2
        self.ui.label_LeftJamb.setText(obj_left.Label)
        self.ui.label_LeftJamb_height.setText(str(get_useful_height(obj_left, self.mode[0])))
        # self.ui.label_LeftJamb.setStyleSheet("""
        #     QLabel {
        #         transform: rotate(90deg);
        #         transform-origin: center;
        #         min-height: 100px;
        #         min-width: 50px;
        #     }
        # """)
        self.ui.label_RightJamb.setText(obj_right.Label)
        self.ui.label_RightJamb_height.setText(str(get_useful_height(obj_right, self.mode[0])))

        # Configurer les connexions
        self.distribution_equidistant_center.toggled.connect(self.update_sliders)
        self.distribution_equidistant_no_thickness.toggled.connect(self.update_sliders)
        self.distribution_arbitrary.toggled.connect(self.update_sliders)
        self.num_shelves_spin.valueChanged.connect(self.update_sliders)
        self.top_thickness_check.stateChanged.connect(lambda: self.top_thickness_edit.setEnabled(self.top_thickness_check.isChecked()))
        self.bottom_thickness_check.stateChanged.connect(lambda: self.bottom_thickness_edit.setEnabled(self.bottom_thickness_check.isChecked()))
        self.ui.absolutePosition.toggled.connect(self.update_sliders)
        self.ui.relativePosition.toggled.connect(self.update_sliders)
        self.ui.checkBox_BackProp.toggled.connect(self.backPropToggled)

        # Initialiser les sliders
        self.sliders = []
        self.slider_labels = []
        self.h_inputs = []
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
        previous_shelves_number = len(self.objects)
        msgCsl(f"{__name__} previous_shelves_number = {previous_shelves_number}, current shelves number = {self.num_shelves_spin.value()}")
        num_shelves = self.num_shelves_spin.value()
        previous_sliders_number = len(self.sliders)
        for slider in self.sliders[num_shelves:]:
            self.sliders_layout.removeWidget(slider)
            slider.deleteLater()
        for label in self.slider_labels[num_shelves:]:
            self.sliders_layout.removeWidget(label)
            label.deleteLater()
        for h_input in self.h_inputs[num_shelves:]:
            self.sliders_layout.removeWidget(h_input)
            h_input.deleteLater()
        self.sliders = self.sliders[:num_shelves]
        self.slider_labels = self.slider_labels[:num_shelves]
        self.h_inputs = self.h_inputs[:num_shelves]
        max_height = self.min_height if self.ui.absolutePosition.isChecked() else 100
        self.groupTypeChange()

        for i in range(previous_sliders_number, num_shelves):
            label = QtWidgets.QLabel(f"Étagère {i+1}:")
            slider = QtWidgets.QSlider(QtCore.Qt.Vertical)
            slider.sliderMoved.connect(lambda state, x=i : self.sliderChanged(x))
            h_input = QtWidgets.QDoubleSpinBox()
            self.sliders_layout.addWidget(label)
            self.sliders_layout.addWidget(h_input)
            self.sliders_layout.addWidget(slider)
            self.slider_labels.append(label)
            self.sliders.append(slider)
            self.h_inputs.append(h_input)
            if (i+1) > previous_shelves_number:
                self.addShelf()
            # if self.objects and i < len(self.objects):
            self.objects[i].part.Visibility = True
            # self.objects[i].temp = False
        for i in range(num_shelves):
            msgCsl(f"update_sliders max_height = {max_height}, absolute = {self.ui.absolutePosition.isChecked()}")
            position = self.getPosition(i, "update_sliders")
            self.sliders[i].setRange(0, int(max_height))
            self.sliders[i].setEnabled(self.distribution_arbitrary.isChecked())
            self.h_inputs[i].setRange(0, max_height)
            self.sliders[i].setValue(int(position))
            msgCsl(f"self.sliders[i].setValue(int(position)) {self.sliders[i].value()}")
            self.h_inputs[i].setValue(position)
            msgCsl(f"self.h_inputs[i].setValue(position) {self.h_inputs[i].value()}")
            self.updateObjPosition(i)
            setObjTag(self.objects[i].object, groupe_etageres=self.group_type + str(self.group_index))
        if num_shelves < previous_shelves_number:
            for i in range(num_shelves, previous_shelves_number):
                self.objects[i].part.Visibility = False
                # self.objects[i].temp = True
            # for obj in self.objects[num_shelves:]:
            #     obj.removeObject()

    def getPosition(self, index, caller):
        msgCsl(f"getPosition caller = {caller}")
        max_height = self.min_height if self.ui.absolutePosition.isChecked() else 100
        num_shelves = self.num_shelves_spin.value()
        position = self.h_inputs[index].value()
        if self.distribution_equidistant_center.isChecked():
            position = (index + 1) / (num_shelves + 1) * max_height
        if self.distribution_equidistant_no_thickness.isChecked():
            gap = (self.min_height - num_shelves * self.objects[index].thickness \
                   - self.top_thickness_check.isChecked() * float(self.top_thickness_edit.text()) \
                    - self.bottom_thickness_check.isChecked() * float(self.bottom_thickness_edit.text())) \
                    / (num_shelves + 1)
            position = (gap * (index + 1) + self.objects[index].thickness * index)
            position = position if self.ui.absolutePosition.isChecked() else position / self.min_height * 100
        if self.distribution_arbitrary.isChecked():
            msgCsl(f"getPosition self.objects[index].part = {self.objects[index].part.Label}")
            if caller == "update_sliders":
                position = getattr(self.objects[index].part.Placement.Base, self.placementProp[-1]) - getattr(self.heightObjRef.Placement.Base, self.placementProp[-1])
                msgCsl(f"self.placementProp[-1] {position}")
                position = position if self.ui.absolutePosition.isChecked() else position / self.min_height * 100
            elif caller == "updateObjPosition":
                position = self.sliders[index].value()
        return position

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
        part = Add_tab() if self.mode[0] == "V" else Add_mti()
        obj.object = find_additive_box(part)
        if not self.group_index: self.group_index = getMaxShelvesIndex() + 1
        if not self.group_type:
            self.groupTypeChange()
        obj.setTag(groupe_etageres = f"{self.group_type}{self.group_index}")
        obj.temp = True
        obj.object.fond = self.backProp
        self.objects.append(obj)

    def groupTypeChange(self):
        if self.mode[0] == "V": grpTyp = "ETG"
        if self.mode[0] == "H": grpTyp = "MTI"
        if self.distribution_equidistant_center.isChecked(): self.group_type = f"{grpTyp}C"
        if self.distribution_equidistant_no_thickness.isChecked(): self.group_type = f"{grpTyp}T"
        if self.distribution_arbitrary.isChecked(): self.group_type = f"{grpTyp}A"

    def updateObjPosition(self, index):
        if isinstance(index, str):
            if index == "all":
                i = 0
                for h_input in self.h_inputs:
                    if self.ui.absolutePosition.isChecked() :
                        self.objects[i].part.setExpression(self.placementProp, None)
                        # self.objects[i].part.Placement.Base.z = h_input.value()
                        setattr(self.objects[i].part.Placement.Base, self.placementProp[-1],
                                h_input.value() + getattr(self.heightObjRef.Placement.Base, self.placementProp[-1]))
                    else:
                        self.objects[i].part.setExpression(self.placementProp, f"<<{self.heightObjRef.Label}>>{self.placementProp} "
                                                                               f"+ {h_input.value()/100} * {get_useful_height(self.heightObjRef, self.mode[0])}")
                    i += 1
                # self.objects[0]._object.Document.recompute()
        if isinstance(index, int):
            position = self.getPosition(index, "updateObjPosition")
            if self.ui.absolutePosition.isChecked():
                self.objects[index].part.setExpression(self.placementProp, None)
                setattr(self.objects[index].part.Placement.Base, self.placementProp[-1],
                        position + getattr(self.heightObjRef.Placement.Base, self.placementProp[-1])) #self.h_inputs[index].value()
            else:
                # self.objects[index].part.setExpression(self.placementProp, f"<<{self.heightObjRef.Label}>>{self.placementProp} "
                #                                                             f"+ {self.h_inputs[index].value()/100} * <<{find_additive_box(self.heightObjRef).Label}>>.Height")
                self.objects[index].part.setExpression(self.placementProp,
                                                       f"<<{self.heightObjRef.Label}>>{self.placementProp} "
                                                       f"+ {position / 100} * <<{find_additive_box(self.heightObjRef).Label}>>"
                                                       f".{"Height" if self.mode[0] == "V" else "Length"}")
            # msgCsl(f"{__name__} position étagère {index} à {self.h_inputs[index].value() * (self.min_height/100 if self.ui.relativePosition.isChecked() else 1)}")
            msgCsl(f"{__name__} position étagère {index} à {position * (self.min_height/100 if self.ui.relativePosition.isChecked() else 1)}")
            self.objects[index].part.Document.recompute()

    def sliderChanged(self, index):
        self.updateObjPosition(index)

    def backPropToggled(self):
        self.backProp = self.ui.checkBox_BackProp.isChecked()

    def accept(self):
        for obj in self.objects:
            if obj.part.Visibility:
                obj.temp = False
                obj.object.fond = self.backProp
                msgCsl(f"{__name__} obj.object {obj.object.Label}, self.backProp = {self.backProp}, obj.object.fond = {obj.object.fond}")
                if self.backProp:
                    obj.object._Body.Group[-1].ViewObject.Visibility = True
                else:
                    obj.object.Visibility = True
            else:
                obj.temp = True
        self.obj1.Document.recompute()
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
    selection = Gui.Selection.getSelection()
    ''' mode definition
        V for vertical duplicated objects, shelves
        H for horizontal duplicated objects, jambs
        0 when no duplicated objects in selection
        1 when duplicated objects in selection
    '''
    mode = "V0"
    obj1, obj2, duplicate = None, None, None
    for _obj in selection:
        obj = find_additive_box(get_parent_part(_obj))
        if hasattr(obj, "bspf_tag"):
            tag_prop = getObjTag(obj)
            if tag_prop:
                if "ETG" in tag_prop["groupe_etageres"]:
                    mode = "V1"
                    obj1 = obj.obj_gauche
                    obj2 = obj.obj_droit
                    duplicate = obj
                    userMsg(f"Duplicated object found {obj.Label}")
                    msgCsl(f"{obj.Label}, obj1 = {obj1.Label}, obj2 = {obj2.Label}")
                    break
                if "MTI" in tag_prop["groupe_etageres"]:
                    mode = "H1"
                    obj1 = obj.obj_dessous
                    obj2 = obj.obj_dessus
                    duplicate = obj
                    userMsg(f"Duplicated object found {obj.Label}")
                    msgCsl(f"{obj.Label}, obj1 = {obj1.Label}, obj2 = {obj2.Label}")
                    break

    if len(selection) == 2: # and not int(mode[1]):
        obj1, obj2 = get_parent_part(selection[0]), get_parent_part(selection[1])
        class_obj1 = classify_object(obj1)
        class_obj2 = classify_object(obj2)
        if class_obj1["is_ext_V"] and class_obj2[ "is_ext_V" ]:
            mode = "H0"
        if class_obj1["is_ext_H"] and class_obj2["is_ext_H"]:
            mode = "V0"
        msgCsl(f"{__name__} obj1 = {obj1.Label}, obj2 = {obj2.Label}")
    # obj1, obj2 = get_selected_objects()
    # if not obj1 or not obj2:
    #     return

    if obj1 and obj2:
        min_height = get_min_height(obj1, obj2, mode[0])
        if not min_height:
            userMsg("No height value could be extract from selection.")
            return

        dialog = ShelfDialog(min_height, obj1, obj2, mode = mode, duplicate = duplicate)
        dialog.show()
        # if dialog.exec() == QtWidgets.QDialog.Accepted:
        #     shelf_positions = dialog.get_shelf_positions()
        #     add_shelves(shelf_positions)
    else:
        userMsg("No valid selection.")

main()
