# -*- coding: utf-8 -*-
"""
Created on Sun Mar 30 18:58:04 2025

@author: Matthieu
"""

import os, sys

#sys.path.append("/usr/lib/freecad/lib/")
import FreeCADGui, FreeCAD, Draft
from PySide import QtCore, QtGui
# from PySide.QtWidgets import QLineEdit
sys.path.append(FreeCAD.getUserMacroDir())
from lib_menuiserie import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

__dir__ = os.path.dirname(__file__)
ui_file = __dir__ + "/BOM_objects_managment.ui"
global iconPath
iconPath = __dir__ + '/Icons/'
global myDialog
myDialog = None

ModeVerbose = True
def msgCsl(message):
    if ModeVerbose:
        FreeCAD.Console.PrintMessage(message + "\n")

def userMsg(message):
	FreeCAD.Console.PrintMessage(message + "\n")

# use "icons" as prefix which we used in the .ui file
QtCore.QDir.addSearchPath("icons", iconPath)

PROP_GROUP = "UserProp"
PROP_LIST = ("Nesting",
             "Nest_grain",
             "Nest_Allow_Rotation",
             "Nest_Thickness",
             "BOM_destination",
             "BOM_mat",
             "BOM_quantity" )

class bom_obj():
    def __init__(self, fcObj = None):
        self.fcObj
        self.grain = ""
        

class BOM_dialog(QtCore.QObject):
    def __init__(self):
        super(BOM_dialog, self).__init__() # Initialisation du parent

        # Chargement de l'UI
        self.widget = FreeCADGui.PySideUic.loadUi(ui_file)
        # On définit une fonction locale qui appelle votre méthode de classe
        # INSTALLATION DU FILTRE (C'est l'espion qui capte la croix)
        self.widget.installEventFilter(self)

        self.widget.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.objects = []
        self.grain_objs = {}
        self.edgeband_objs = {}
        self.obj_transparency = {}
        self.my_model = QtGui.QStandardItemModel()
        self.widget.BOM_objects_listView.setModel(self.my_model)
        self.materials_model = QtGui.QStandardItemModel()
        self.widget.material_listView.setModel(self.materials_model)
        self.BOM_objects_List_update()
        self.BOM_materials_list_update()
        self.h_separator = QtGui.QFrame()
        self.h_separator.setFrameShape(QtGui.QFrame.HLine)
        self.h_separator.setFrameShadow(QtGui.QFrame.Sunken)
        # self.h_separator.setMinimumHeight(2)
        self.h_separator.setStyleSheet("background-color: rgb(150, 150, 150);")
        self.widget.verticalLayout.insertWidget(1, self.h_separator)
        self.h_separator2 = QtGui.QFrame()
        self.h_separator2.setFrameShape(QtGui.QFrame.HLine)
        self.h_separator2.setFrameShadow(QtGui.QFrame.Sunken)
        self.h_separator2.setStyleSheet("background-color: rgb(150, 150, 150);")
        self.widget.verticalLayout.insertWidget(4, self.h_separator2)
        self.h_separator3 = QtGui.QFrame()
        self.h_separator3.setFrameShape(QtGui.QFrame.HLine)
        self.h_separator3.setFrameShadow(QtGui.QFrame.Sunken)
        self.h_separator3.setStyleSheet("background-color: rgb(150, 150, 150);")
        self.widget.verticalLayout.insertWidget(8, self.h_separator3)
        self.widget.Panel_label.setPixmap(QtGui.QPixmap("icons:planche.png"))
        # self.widget.setUpdatesEnabled(False)
        self.widget.EdgeBand_widget.hide()
        self.widget.layout().activate()
        self.widget.adjustSize()
        # self.widget.setUpdatesEnabled(True)
        self.updateEdgeBands = False

        self.connections_for_button_clicked = {"Close_pushButton"				        : "Close_clicked",
                                               "excludeFilter_update_pushButton"        : "BOM_objects_List_update",
                                               "resetFilter_pushButton"                 : "resetFilter",
                                               "setBOMtoTrue_pushButton"                : "setBOMtoTrue",
                                               "setBOMtoFalse_pushButton"               : "setBOMtoFalse",
                                               "selectFreeCAD_pushButton"               : "onSelectFreeCAD_clicked",
                                               "selectBodiesOfMat_pushButton"           : "onClickSelectBodiesOfMat",
                                               "selectObjectsOfMat_pushButton"          : "onClickSelectObjectsOfMat",
                                               "RemoveBOMandNestingProperties_pushButton" : "onClickRemoveBOMandNestingProperties",
                                               "WoodGrainDisplay_pushButton"            : "onClickWoodGrainDisplay",
                                               "Edit_pushButton"                        : "onClickEdit",
                                               "AutoEdgeBand_pushButton"                : "onClickAutoEdgeBand",
                                               }
        self.connections_for_checkbox_checkchanged = {"BOM_True_checkBox"        : "BOM_objects_List_update",
                                                      "BOM_False_checkBox"       : "BOM_objects_List_update",
                                                      "WoodGrainDisplay_checkBox": "onClickWoodGrainDisplay",
                                                      "LeftEdgeBand_checkBox"    : "onClickLeftEdgeBandCheckChanged",
                                                      "RightEdgeBand_checkBox"   : "onClickRightEdgeBandCheckChanged",
                                                      "FrontEdgeBand_checkBox"   : "onClickFrontEdgeBandCheckChanged",
                                                      "RearEdgeBand_checkBox"    : "onClickRearEdgeBandCheckChanged",
                                                      }
        self.connections_for_lineEdit_textChanged = {
                                                    "excludeFilter_lineEdit"        : "BOM_objects_List_update",
                                                    "includeFilter_lineEdit"        : "BOM_objects_List_update",
                                                    }
        self.connections_for_listView_selectionChanged = {
                                                            "BOM_objects_listView" : "on_bom_selection_changed",
                                                            "material_listView"    : "onMaterialSelectionChanged",
                                                         } 
        
        for m_key, m_val in self.connections_for_button_clicked.items():
            # msgCsl( "Connecting : " + str(m_key) + " and " + str(m_val) )
            getattr(self.widget, str(m_key)).clicked.connect(getattr(self, str(m_val)))

        for m_key, m_val in self.connections_for_checkbox_checkchanged.items():
            # msgCsl( "Connecting : " + str(m_key) + " and " + str(m_val) )
            getattr(self.widget, str(m_key)).stateChanged.connect(getattr(self, str(m_val)))

        for m_key, m_val in self.connections_for_lineEdit_textChanged.items():
            #msgCsl( "Connecting : " + str(m_key) + " and " + str(m_val) )
            getattr(self.widget, str(m_key)).textChanged.connect(getattr(self, str(m_val)))

        for m_key, m_val in self.connections_for_listView_selectionChanged.items():
            #msgCsl( "Connecting : " + str(m_key) + " and " + str(m_val) )
            getattr(self.widget, str(m_key)).selectionModel().selectionChanged.connect(getattr(self, str(m_val)))

    def onClickAutoEdgeBand(self):
        KeyToDefaultEdgeBand = {
                                "XLength" : ("Avant"),
                                "YLength" : ("Avant", "Arriere", "Gauche", "Droit"),
                                "ZLength" : ("Avant"),
                                }
        if QtGui.QMessageBox.question(self.widget,                   # Fenêtre parente
                                    "Confirmation",                # Titre de la fenêtre
                                    "Toutes les propriétés de chants déjà configurées vont être écrasées, voulez-vous continuer ?", # Message
                                    QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel # Boutons affichés
                                ):
            for i in range(self.widget.BOM_objects_listView.model().rowCount()):
                item = self.widget.BOM_objects_listView.model().item(i) # Récupère l'objet QStandardItem
                obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
                for key, edgeband in EDGEBAND_PROPERTIES.items():
                    prop_name = (edgeband["Group"] + "_" if edgeband["Prefix"] else "") + edgeband["Name"]
                    if not hasattr(obj, prop_name):
                        obj.addProperty(edgeband["Type"], prop_name, edgeband["Group"])
                    if hasattr(obj, "Nest_Thickness"):
                        if key in KeyToDefaultEdgeBand[obj.Nest_Thickness] and not "fond" in obj.Label.lower():
                            setattr(obj, prop_name, True)
                        else:
                            setattr(obj, prop_name, False)
            self.updateEdgeBandCheckBoxFromObj()

    def SelectedObjectsPropertyChange(self, prop, value):
        for index in self.widget.BOM_objects_listView.selectedIndexes():
            item = self.widget.BOM_objects_listView.model().itemFromIndex(index)
            obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
            # if prop.Prefix: prefix = prop.Group else: prefix = ""
            prop_name = (prop["Group"] + "_" if prop["Prefix"] else "") + prop["Name"]
            # msgCsl(f"prop_name {prop_name}")
            if not hasattr(obj, prop_name):
                obj.addProperty(prop["Type"], prop_name, prop["Group"])
            setattr(obj, prop_name, value)
            if self.drawEdgeBand(obj):
                FreeCAD.ActiveDocument.recompute()

    def updateEdgeBandCheckBoxFromObj(self):
        keyToObj = {
                    "Gauche" : "LeftEdgeBand_checkBox",
                    "Droit"  : "RightEdgeBand_checkBox",
                    "Avant"  : "FrontEdgeBand_checkBox",
                    "Arriere": "RearEdgeBand_checkBox",
                    }
        self.updateEdgeBands = False
        f_recompute = False
        if self.widget.BOM_objects_listView.selectedIndexes():
            for index in self.widget.BOM_objects_listView.selectedIndexes():
                item = self.widget.BOM_objects_listView.model().itemFromIndex(index)
                # msgCsl(f"updateEdgeBandCheckBoxFromObj, obj = None, item {item.text()}")
                obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
                for key, edgeband in EDGEBAND_PROPERTIES.items():
                    # msgCsl(f"updateEdgeBandCheckBoxFromObj, key edgeband {key}, obj {obj.Label}")
                    prop_name = (edgeband["Group"] + "_" if edgeband["Prefix"] else "") + edgeband["Name"]
                    if hasattr(obj, prop_name):
                        getattr(self.widget, keyToObj[key]).setChecked(getattr(obj, prop_name))
                    else:
                        getattr(self.widget, keyToObj[key]).setChecked(False)
                f_recompute = self.drawEdgeBand(obj)
        else:
            self.updateEdgeBands = True
            return
        if f_recompute: FreeCAD.ActiveDocument.recompute()
        # self.onSelectFreeCAD_clicked()
        self.updateEdgeBands = True

    def drawEdgeBand(self, obj):
        
        # label = obj.Label.lower()
        # is_mt = any(k in label for k in ["mt", "montant"])
        # is_tv = any(k in label for k in ["tv", "traverse", "tab", "tablette"])
        # is_ambiguous_name = any(k in label for k in ["fond", "tiroir", "porte", "facade"])
        EdgeBand_created = False
        GRAIN_OBJ_OFFSET = 20
        # GRAIN_OBJ_THICKNESS = 19
        # if hasattr(obj, "Nest_grain"):
        x_length = obj.Shape.BoundBox.XLength
        y_length = obj.Shape.BoundBox.YLength
        z_length = obj.Shape.BoundBox.ZLength
        Points = []
        Points.append(FreeCAD.Vector(0.0, 0.0, 0.0))
        Points.append(FreeCAD.Vector(x_length, 0.0, 0.0))
        Points.append(FreeCAD.Vector(x_length, 0.0, z_length))
        Points.append(FreeCAD.Vector(0.0, 0.0, z_length))
        Points.append(FreeCAD.Vector(0.0, y_length, 0.0))
        Points.append(FreeCAD.Vector(x_length, y_length, 0.0))
        Points.append(FreeCAD.Vector(x_length, y_length, z_length))
        Points.append(FreeCAD.Vector(0.0, y_length, z_length))
        Faces = {
                "Front" : (Points[0], Points[1], Points[2], Points[3]),
                "Rear" : (Points[4], Points[5], Points[6], Points[7]),
                "Left" : (Points[0], Points[3], Points[7], Points[4]),
                "Right" : (Points[1], Points[2], Points[6], Points[5]),
                "Top" : (Points[3], Points[2], Points[6], Points[7]),
                "Bottom" : (Points[0], Points[1], Points[5], Points[4]),
                }
        KeyToFace = {
                    "XLength" : { "YLength": { "Front" : "Top", "Rear" : "Bottom", "Left" : "Front", "Right" : "Rear"},
                                 "ZLength": { "Front" : "Front", "Rear" : "Rear", "Left" : "Bottom", "Right" : "Top"}},
                    "YLength" : { "XLength": { "Front" : "Top", "Rear" : "Bottom", "Left" : "Left", "Right" : "Right"},
                                 "ZLength": { "Front" : "Left", "Rear" : "Right", "Left" : "Bottom", "Right" : "Top"}},
                    "ZLength" : { "XLength": { "Front" : "Front", "Rear" : "Rear", "Left" : "Left", "Right" : "Right"},
                                 "YLength": { "Front" : "Left", "Rear" : "Right", "Left" : "Rear", "Right" : "Front"}},
                    }
        AvantToFront = { "Avant" : "Front", "Arriere" : "Rear", "Gauche" : "Left", "Droit" : "Right"}
        Offset = {
                    "Front" : (0.0, -1.0, 0.0),
                    "Rear" : (0.0, 1.0, 0.0),
                    "Left" : (-1.0, 0.0, 0.0),
                    "Right" : (1.0, 0.0, 0.0),
                    "Top" : (0.0, 0.0, 1.0),
                    "Bottom" : (0.0, 0.0, -1.0),
                }
        o_parent = get_parent_part(obj)
        # pl = o_parent.Placement
        try:
            if not "PartDesign" in obj.TypeId:
                pl_obj = obj.Placement
            else:
                pl_obj = FreeCAD.Placement()
        except:
            pl_obj = FreeCAD.Placement()
            # msgCsl(f"pl_obj {pl_obj}")
        if obj.InList[0].TypeId == "PartDesign::Body":
            pl_body = obj.InList[0].Placement
            # msgCsl(f"pl_body {pl_body}")
        else:
            pl_body = FreeCAD.Placement()
        ocolor = (0, 255, 255)
        for key, edgeband in EDGEBAND_PROPERTIES.items():
            prop_name = (edgeband["Group"] + "_" if edgeband["Prefix"] else "") + edgeband["Name"]
            translation = FreeCAD.Vector(0.0, 0.0, 0.0)
            if self.edgeband_objs.get(obj.Label):
                if self.edgeband_objs[obj.Label].get(edgeband["Name"]):
                    self.edgeband_objs[obj.Label][edgeband["Name"]].Visibility = getattr(obj, prop_name)
                    continue
            if hasattr(obj, prop_name):
                # msgCsl(f"obj {obj.Label}, prop_name {prop_name}")
                if getattr(obj, prop_name):
                    face = KeyToFace[obj.Nest_Thickness][obj.Nest_grain][AvantToFront[edgeband["Name"]]]
                    points = Faces[face]
                    translation = translation.add(FreeCAD.Vector(Offset[face]))*GRAIN_OBJ_OFFSET
                    oline = Draft.make_wire(points, placement=FreeCAD.Placement(), closed=True, face=True, support=None)
                    pl_res = pl_obj.multiply(pl_body)
                    # msgCsl(f"pl_obj.multiply(pl_res) {pl_res}")
                    pl_res.move(translation)
                    oline.Placement = pl_res
                    # msgCsl(f"oline.Placement {oline.Placement}")
                    o_parent.addObject(oline)
                    oline.Label = "EdgeBand"
                    oline.ViewObject.ShapeAppearance = (FreeCAD.Material(DiffuseColor=ocolor,AmbientColor=ocolor,SpecularColor=ocolor,EmissiveColor=ocolor,Shininess=1.00,Transparency=(0.00),))
                    oline.ViewObject.LineColor = ocolor
                    oline.ViewObject.PointColor = ocolor
                    oline.ViewObject.Transparency = 0
                    oline.ViewObject.LineWidth = 0.01
                    if obj.Label not in self.edgeband_objs:
                        self.edgeband_objs[obj.Label] = {}
                    self.edgeband_objs[obj.Label][edgeband["Name"]] = oline
                    EdgeBand_created = True
                else:
                    if self.edgeband_objs.get(obj.Label):
                        if self.edgeband_objs[obj.Label].get(edgeband["Name"]):
                            self.edgeband_objs[obj.Label][edgeband["Name"]].Visibility = getattr(obj, prop_name)
        return EdgeBand_created

    def onClickRightEdgeBandCheckChanged(self):
        if self.updateEdgeBands:
            prop = EDGEBAND_PROPERTIES["Droit"]
            # msgCsl(f"prop edgeband {prop}")
            self.SelectedObjectsPropertyChange(prop, self.widget.RightEdgeBand_checkBox.isChecked())

    def onClickLeftEdgeBandCheckChanged(self):
        if self.updateEdgeBands:
            prop = EDGEBAND_PROPERTIES["Gauche"]
            # msgCsl(f"prop edgeband {prop}")
            self.SelectedObjectsPropertyChange(prop, self.widget.LeftEdgeBand_checkBox.isChecked())

    def onClickFrontEdgeBandCheckChanged(self):
        if self.updateEdgeBands:
            prop = EDGEBAND_PROPERTIES["Avant"]
            # msgCsl(f"prop edgeband {prop}")
            self.SelectedObjectsPropertyChange(prop, self.widget.FrontEdgeBand_checkBox.isChecked())

    def onClickRearEdgeBandCheckChanged(self):
        if self.updateEdgeBands:
            prop = EDGEBAND_PROPERTIES["Arriere"]
            # msgCsl(f"prop edgeband {prop}")
            self.SelectedObjectsPropertyChange(prop, self.widget.RearEdgeBand_checkBox.isChecked())

    def onMaterialSelectionChanged(self, selected, deselected):
        # 'selected' contient les indexes qui viennent d'être cochés/cliqués
        indices = selected.indexes()
        
        if indices:
            index = indices[0] # Récupère le premier index sélectionné
            material = index.data() # Récupère le texte de l'item
            selection_model = self.widget.BOM_objects_listView.selectionModel()
            # On vide la sélection actuelle
            selection_model.clearSelection()
            for i in range(self.my_model.rowCount()):
                item = self.my_model.item(i) # Récupère l'objet QStandardItem 
                obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
                if material == obj.BOM_mat:
                    selection_model.select(self.my_model.index(i, 0), 
                                QtCore.QItemSelectionModel.Select)

    def on_bom_selection_changed(self, selected, deselected):
        self.setUnSelectedObjectTransparent()
        if self.widget.WoodGrainDisplay_checkBox.isChecked():
            self.onClickWoodGrainDisplay()
        if self.widget.Edit_pushButton.text() == "Editer <<":
            # msgCsl("lancement de updateEdgeBandCheckBoxFromObj à partir de on_bom_selection_changed")
            self.updateEdgeBandCheckBoxFromObj()

    def objTransparencyBackupRestore(self, mode = "Backup" ):
        if mode == "Backup":
            for i in range(self.my_model.rowCount()):   #self.widget.BOM_objects_listView.model()
                item = self.widget.BOM_objects_listView.model().item(i) # Récupère l'objet QStandardItem
                viewer_container = getParentViewObject(FreeCAD.ActiveDocument.getObjectsByLabel(item.text())[0])
                if self.obj_transparency.get(item.text()) == None:
                    # msgCsl(f"self.obj_transparency.get(item.text()) {self.obj_transparency.get(item.text())}")
                    self.obj_transparency[item.text()] = viewer_container.ViewObject.Transparency
        elif mode == "Restore":
            for key, value in self.obj_transparency.items():
                viewer_container = getParentViewObject(FreeCAD.ActiveDocument.getObjectsByLabel(key)[0])
                viewer_container.ViewObject.Transparency = value

    def setUnSelectedObjectTransparent(self):
        if self.widget.Transparency_checkBox.isChecked():
            selindexes = self.widget.BOM_objects_listView.selectedIndexes()
    
            for i in range(self.widget.BOM_objects_listView.model().rowCount()):
                item = self.widget.BOM_objects_listView.model().item(i) # Récupère l'objet QStandardItem
                obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
                viewer_container = getParentViewObject(obj)
                if not item.index() in selindexes:
                    viewer_container.ViewObject.Transparency = 90
                    if self.edgeband_objs.get(obj.Label):
                        for edgeband in EDGEBAND_PROPERTIES.values():
                            if self.edgeband_objs[obj.Label].get(edgeband["Name"]):
                                self.edgeband_objs[obj.Label][edgeband["Name"]].Visibility = False
                else:
                    viewer_container.ViewObject.Transparency = 0
        else:
            self.objTransparencyBackupRestore("Restore")

    def onClickEdit(self):
        if self.widget.EdgeBand_widget.isVisible():
            self.widget.EdgeBand_widget.hide()
            self.widget.Edit_pushButton.setText(self.widget.Edit_pushButton.text()[:-2] + ">>")
        else:
            self.widget.EdgeBand_widget.show()
            self.widget.Edit_pushButton.setText(self.widget.Edit_pushButton.text()[:-2] + "<<")
            self.updateEdgeBandCheckBoxFromObj()
        self.widget.layout().activate()
        self.widget.adjustSize()

    def onClickWoodGrainDisplay(self):
        self.GrainObjectsListUpdate()
        if not self.widget.Transparency_checkBox.isChecked():
                self.onSelectFreeCAD_clicked()

    def GrainObjectsListUpdate(self):

        f_recompute = False
        # For objects which aren't anymore in ListView, corresponding grain_obj has to be deleted'
        obj_labels = []
        for ob in self.objects:
            obj_labels.append(FreeCAD.ActiveDocument.getObject(ob[1]).Label)
        for key in self.grain_objs:
            # msgCsl(f"obj_labels {obj_labels}")
            # msgCsl(f"grain_objs {self.grain_objs}")
            if not key in obj_labels:
                # msgCsl(f"remove key {key}")
                self.removeGrainObj(key)
        selindexes = self.widget.BOM_objects_listView.selectedIndexes()

        # grain_obj of non-selected objects are hidden, those existing and selected are shown, other created
        # if selindexes:
        for i in range(self.widget.BOM_objects_listView.model().rowCount()):
            item = self.widget.BOM_objects_listView.model().item(i) # Récupère l'objet QStandardItem
            if not item.index() in selindexes:
                # item = self.widget.BOM_objects_listView.model().itemFromIndex(i)
                obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
                if self.grain_objs.get(obj.Label):
                    self.grain_objs[obj.Label].Visibility = False
        for index in selindexes:
            item = self.widget.BOM_objects_listView.model().itemFromIndex(index)
            obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
            # msgCsl(f"obj wood grain: {obj.Label}")
            try:
                self.grain_objs[obj.Label].Visibility = True and self.widget.WoodGrainDisplay_checkBox.isChecked()
            except:
                f_recompute = self.createGrainObj(obj)
        if f_recompute: FreeCAD.ActiveDocument.recompute()
                    
    def removeGrainObj(self, grain_obj_label):
        try:
            FreeCAD.ActiveDocument.removeObject(self.grain_objs[grain_obj_label].Name)
            self.grain_objs.pop(grain_obj_label)
        except:
            pass
                
    def createGrainObj(self, obj):
        GRAIN_OBJ_OFFSET = 40
        GRAIN_OBJ_THICKNESS = 19
        f_recompute = False
        if hasattr(obj, "Nest_grain"):
            parent_obj = get_parent_part(obj)
            x_length = obj.Shape.BoundBox.XLength
            y_length = obj.Shape.BoundBox.YLength
            z_length = obj.Shape.BoundBox.ZLength
            o_parent = get_parent_part(obj)
            msgCsl(f"createGrainObj parent = {o_parent.Label}")
            pl = o_parent.Placement
            try:
                if not "PartDesign" in obj.TypeId:
                    pl_obj = obj.Placement
                else:
                    pl_obj = FreeCAD.Placement()
            except:
                pl_obj = FreeCAD.Placement()
                # msgCsl(f"pl_obj {pl_obj}")
            if obj.InList[0].TypeId == "PartDesign::Body":
                pl_body = obj.InList[0].Placement
                # msgCsl(f"pl_body {pl_body}")
            else:
                pl_body = FreeCAD.Placement()
            if obj.Nest_grain == "XLength":
                translation = FreeCAD.Vector(0.0, -GRAIN_OBJ_OFFSET, z_length/2-GRAIN_OBJ_THICKNESS/2)
                points = [FreeCAD.Vector(0.0, 0.0, 0.0), FreeCAD.Vector(x_length, 0.0, 0.0), FreeCAD.Vector(x_length, 0.0, GRAIN_OBJ_THICKNESS), FreeCAD.Vector(0.0, 0.0, GRAIN_OBJ_THICKNESS)]
                ocolor = (255, 0, 0)
            elif obj.Nest_grain == "YLength":
                translation = FreeCAD.Vector(-GRAIN_OBJ_OFFSET, 0.0, z_length/2-GRAIN_OBJ_THICKNESS/2)
                points = [FreeCAD.Vector(0.0, 0.0, 0.0), FreeCAD.Vector(0.0, y_length, 0.0), FreeCAD.Vector(0.0, y_length, GRAIN_OBJ_THICKNESS), FreeCAD.Vector(0.0, 0.0, GRAIN_OBJ_THICKNESS)]
                ocolor = (0, 255, 0)
            elif obj.Nest_grain == "ZLength":
                translation = FreeCAD.Vector(x_length/2-GRAIN_OBJ_THICKNESS/2, -GRAIN_OBJ_OFFSET, 0.0)
                points = [FreeCAD.Vector(0.0, 0.0, 0.0), FreeCAD.Vector(0.0,0.0, z_length), FreeCAD.Vector(GRAIN_OBJ_THICKNESS, 0.0, z_length), FreeCAD.Vector(GRAIN_OBJ_THICKNESS, 0.0, 0.0)]
                ocolor = (0, 0, 255)

            oline = Draft.make_wire(points, placement=FreeCAD.Placement(), closed=True, face=True, support=None)
            # pl_res = pl_body.multiply(pl)
            # msgCsl(f"pl_body.multiply(pl) {pl_res}")
            pl_res = pl_obj.multiply(pl_body)
            # msgCsl(f"pl_obj.multiply(pl_res) {pl_res}")
            pl_res.move(translation)
            oline.Placement = pl_res
            # msgCsl(f"oline.Placement {oline.Placement}")
            # oline.Placement.move(translation)
            o_parent.addObject(oline)
            oline.Label = "Grain_direction"
            oline.ViewObject.ShapeAppearance = (App.Material(DiffuseColor=ocolor,AmbientColor=ocolor,SpecularColor=ocolor,EmissiveColor=ocolor,Shininess=(1.0),Transparency=(0.00),))
            oline.ViewObject.LineColor = ocolor
            oline.ViewObject.PointColor = ocolor
            # oline.ViewObject.Transparency = 50
            oline.ViewObject.LineWidth = 0.01
            self.grain_objs[obj.Label] = oline
            f_recompute = True
        return f_recompute

    def onClickRemoveBOMandNestingProperties(self):
        for obj in FreeCADGui.Selection.getSelection():
            for prop in obj.PropertiesList:
                if obj.getGroupOfProperty(prop) == PROP_GROUP and prop in PROP_LIST:
                    r = obj.removeProperty(prop)

    def onClickSelectObjectsOfMat(self):
        if self.widget.material_listView.currentIndex():
            # for index in self.widget.BOM_objects_listView.selectedIndexes():
            #     item = self.widget.BOM_objects_listView.model().itemFromIndex(index)
            current_index = self.widget.material_listView.currentIndex()
            material = current_index.data(QtCore.Qt.DisplayRole)
            objs = []
            for obj in self.objects:
                oFC = FreeCAD.ActiveDocument.getObject(obj[1])
                if oFC.BOM_mat == material:
                    objs.append(oFC.Name)
            if objs:
                FreeCADGui.Selection.clearSelection()
                for obj in objs:
                    FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.getObject(obj))

    def onClickSelectBodiesOfMat(self):
        if self.widget.material_listView.currentIndex():
            # for index in self.widget.BOM_objects_listView.selectedIndexes():
            #     item = self.widget.BOM_objects_listView.model().itemFromIndex(index)
            current_index = self.widget.material_listView.currentIndex()
            material = current_index.data(QtCore.Qt.DisplayRole)
            bodies = []
            for obj in self.objects:
                oFC = FreeCAD.ActiveDocument.getObject(obj[1])
                if oFC.BOM_mat == material:
                    if "PartDesign::" in oFC.TypeId:
                        FreeCADGui.Selection.clearSelection()
                        FreeCADGui.Selection.addSelection(oFC)
                        sels = Gui.Selection.getSelectionEx("", 0)
                        sel = sels[0]
                        # doc = sel.Document
                        sub = sel.SubElementNames[0] if sel.SubElementNames else ""
                        subs = sub.split(".")[:-1]
                        # path = [sel.Object] + [doc.getObject(name) for name in subs]
                        # msgCsl(f"{[o.Label for o in path]}")
                        # msgCsl(f"Object {obj[1]} Body name: {subs[-2]}")
                        bodies.append(subs[-2])
                    if "Part::" in oFC.TypeId:
                        bodies.append(oFC.Name)
            if bodies:
                FreeCADGui.Selection.clearSelection()
                for body in bodies:
                    FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.getObject(body))

    def onSelectFreeCAD_clicked(self):
        self.setUnSelectedObjectTransparent()
        FreeCADGui.Selection.clearSelection()
        for index in self.widget.BOM_objects_listView.selectedIndexes():
            item = self.widget.BOM_objects_listView.model().itemFromIndex(index)
            obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
            # msgCsl(f"selected row {item.row()}, data {item.text()}, self.objects : index {self.objects[item.row()][0]}, name {self.objects[item.row()][1]}")
            FreeCADGui.Selection.addSelection(obj)

    def setBOMtoTrue(self):
        for index in self.widget.BOM_objects_listView.selectedIndexes():
            item = self.widget.BOM_objects_listView.model().itemFromIndex(index)
            obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
            obj.BOM_destination = True
        self.BOM_objects_List_update()

    def setBOMtoFalse(self):
        for index in self.widget.BOM_objects_listView.selectedIndexes():
            item = self.widget.BOM_objects_listView.model().itemFromIndex(index)
            obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
            obj.BOM_destination = False
        self.BOM_objects_List_update()

    def resetFilter(self):
        self.widget.excludeFilter_lineEdit.setText("")
        self.widget.includeFilter_lineEdit.setText("")

    def BOM_objects_List_update(self):
        # self.widget.Parts_listView.clear()
        # self.clear_ListView(self.widget.Parts_listView)
        # Model = QtGui.QStandardItemModel(self.widget.BOM_objects_listView)
        # Model.clear()
        self.my_model.clear()
        # msgCsl(f"BOM_objects_List_update start {Model.rowCount()}")
        list_obj = []
        self.objects = []
        i = 0
        for obj in FreeCAD.ActiveDocument.Objects:
            add_obj = False
            if hasattr(obj,"BOM_destination"):
                if self.widget.excludeFilter_lineEdit.text():
                    if not self.widget.excludeFilter_lineEdit.text() in obj.Label.lower():
                        add_obj = True
                else:
                    add_obj = True
                if add_obj and self.widget.includeFilter_lineEdit.text():
                    if not self.widget.includeFilter_lineEdit.text() in obj.Label.lower():
                        add_obj = False
                if add_obj:
                    match [self.widget.BOM_True_checkBox.isChecked(), self.widget.BOM_False_checkBox.isChecked()]:
                        case [True, False]:
                            add_obj =  obj.BOM_destination
                        case [False, True]:
                            add_obj = not obj.BOM_destination
            if add_obj:
                list_obj.append(obj.Label)
                self.objects.append([i, obj.Name])
                i += 1
        for item in list_obj:
            listitem = QtGui.QStandardItem(item)
            self.my_model.appendRow(listitem)
            # listitem.setData(QtGui.QIcon(os.path.join(iconPath, 'Geofeaturegroup.svg')),QtCore.Qt.DecorationRole)
            listitem.setData(FreeCAD.ActiveDocument.getObjectsByLabel(item)[0].ViewObject.Icon,QtCore.Qt.DecorationRole)
        # msgCsl(f"BOM_objects_List_update end {self.my_model.rowCount()}")
        # self.widget.BOM_objects_listView.setModel(Model)
        self.BOM_materials_list_update()
        self.objTransparencyBackupRestore("Backup")
        self.setUnSelectedObjectTransparent()
        self.GrainObjectsListUpdate()
        return True

    def BOM_materials_list_update(self):
        if self.objects:
            mat_list = []
            for obj in self.objects:
                oFC = FreeCAD.ActiveDocument.getObject(obj[1])
#                userMsg(f"objet étiquette {oFC.Label}")
                if hasattr(oFC,"BOM_mat"):
                    mat = oFC.BOM_mat
                    matInList = False
                    for matitem in mat_list:
                        if mat == matitem:
                            matInList = True
                    if not matInList:
                        mat_list.append(mat)
            # Model = QtGui.QStandardItemModel(self.widget.material_listView)
            # Model.clear()
            self.materials_model.clear()
            for item in mat_list:
                listitem = QtGui.QStandardItem(item)
                self.materials_model.appendRow(listitem)
            # self.widget.material_listView.setModel(Model)

    def excludeFilter_changed(self):
        # msgCsl("Exclude filter changed")
        self.BOM_objects_List_update()

    def eventFilter(self, obj, event):
        """ Capte tous les événements du widget """
        # On vérifie si l'événement est une fermeture (Type 19 dans Qt)
        if obj == self.widget and event.type() == QtCore.QEvent.Close:
            # msgCsl("L'utilisateur a fermé la fenêtre (Croix ou bouton Close)")
            self.clean_up_everything()
            return False # On laisse l'événement continuer pour fermer réellement

        return super(BOM_dialog, self).eventFilter(obj, event)

    def clean_up_everything(self):
        """ Centralisation du nettoyage """
        # msgCsl("Début du nettoyage mémoire et objets 3D...")

        # 1. Supprimer les objets de grain dans le document
        for key in list(self.grain_objs.keys()):
            try:
                name = self.grain_objs[key].Name
                FreeCAD.ActiveDocument.removeObject(name)
                # msgCsl(f"Suppression de l'objet : {name}")
            except:
                pass
        # 1. Supprimer les objets de edgeband dans le document
        for key in list(self.edgeband_objs.keys()):
            for edge in list(self.edgeband_objs[key].keys()):
                try:
                    name = self.edgeband_objs[key][edge].Name
                    FreeCAD.ActiveDocument.removeObject(name)
                    # msgCsl(f"Suppression de l'objet : {name}")
                except:
                    pass

        self.grain_objs.clear()
        self.edgeband_objs.clear()
        self.objTransparencyBackupRestore("Restore")

        FreeCAD.ActiveDocument.recompute()

        # 2. Supprimer la référence globale dans FreeCAD
        if hasattr(FreeCAD, "BOM_Dialog_Instance"):
            delattr(FreeCAD, "BOM_Dialog_Instance")

        # msgCsl("Nettoyage terminé.")

    def Close_clicked(self):
        """ Le bouton Close appelle simplement close(), l'eventFilter fera le reste """
        self.widget.close()

# ====================================================================
# FONCTION PRINCIPALE DE LA MACRO MODIFIÉE
# ====================================================================
def run():
    # Vérifier si une instance existe déjà
    if hasattr(FreeCAD, "BOM_Dialog_Instance"):
        try:
            # Essayer de fermer l'ancienne fenêtre proprement
            FreeCAD.BOM_Dialog_Instance.widget.close()
        except:
            # Si le widget a déjà été supprimé mais la réf est restée
            pass

    # Créer la nouvelle instance
    FreeCAD.BOM_Dialog_Instance = BOM_dialog()
    FreeCAD.BOM_Dialog_Instance.widget.show()

if __name__ == '__main__':
    run()
