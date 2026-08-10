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
from FreeCAD_BespokeFurniture.lib_menuiserie import *

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


def preparer_liste_objets_for():
    doc_actuel = FreeCAD.ActiveDocument
    if not doc_actuel:
        return []

    objets_structures = []
    cles_de_controle = set()

    # 1. OBRETS LOCAUX (Rang 0)
    for obj in doc_actuel.Objects:
        if hasattr(obj, "BOM_destination"):
            if obj.Name not in cles_de_controle:
                cles_de_controle.add(obj.Name)
                objets_structures.append({
                    "obj_reference": obj,
                    "nom_unique": obj.Name,
                    "parent_label": ""  # Pas de parent externe
                })

    # Fonction d'aide pour remonter l'arborescence interne d'un fichier externe
    def reconstruire_chemin_interne(obj_ext, doc_externe):
        """Remonte les parents dans le doc externe pour créer la chaîne de noms (ex: ['Part', 'Part017', 'Body', 'Box'])"""
        chemin = [obj_ext.Name]
        courant = obj_ext
        # On remonte tant qu'on trouve un parent dans le même document externe
        while hasattr(courant, "InList") and courant.InList:
            parent = None
            for p in courant.InList:
                # On cherche un parent physique de type conteneur (Part, Body, Group) dans le même document
                if p.Document == doc_externe and ("Part" in p.TypeId or "Group" in p.TypeId or "Body" in p.TypeId):
                    parent = p
                    break
            if parent:
                chemin.insert(0, parent.Name)
                courant = parent
            else:
                break
        return chemin

    # 2. ANALYSE DES DOCUMENTS EXTERNES VIA LEUR CATALOGUE .OBJECTS
    for lnk in doc_actuel.Objects:
        if hasattr(lnk, "LinkedObject") and lnk.LinkedObject:
            doc_externe = lnk.LinkedObject.Document

            if doc_externe != doc_actuel:
                # On parcourt à plat tous les objets du document externe
                for obj_ext in doc_externe.Objects:

                    if hasattr(obj_ext, "BOM_destination"):
                        # Reconstruction du chemin hiérarchique complet au sein du doc externe
                        chemin_noms = reconstruire_chemin_interne(obj_ext, doc_externe)

                        # Construction du nom composé complet à partir du document actif
                        # Exemple : "Link004.Part.Part017.Body.Box"
                        cle_complete = f"{lnk.Name}.{'.'.join(chemin_noms)}"

                        if cle_complete not in cles_de_controle:
                            cles_de_controle.add(cle_complete)

                            # On stocke directement LE VRAI OBJET COMPLET du document externe
                            objets_structures.append({
                                "obj_reference": obj_ext,
                                "nom_unique": cle_complete,
                                "parent_label": lnk.Label  # Label du conteneur (ex: "tiroir pente 2")
                            })

    return objets_structures

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
        self.widget.linkObjects_checkBox.setChecked(True)
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
                                                      "linkObjects_checkBox"     : "BOM_objects_List_update",
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

        self.widget.masseVolumique_spinBox.valueChanged.connect(self.majMasse)

    def getObjFromListViewItem(self, nom_unique):
        mon_objet = None
        # nom_unique = item.data(QtCore.Qt.UserRole)
        if "." in nom_unique:
            # CAS EXTERNE : L'adresse est sous la forme "NomDuLien.NomDeLObjet"
            nom_lien, nom_sous_obj = nom_unique.split(".", 1)

            lien_local = FreeCAD.ActiveDocument.getObject(nom_lien)
            if lien_local:
                # On utilise getSubObject pour obtenir l'objet virtuel lié
                mon_objet = lien_local.LinkedObject.Document.getObject(nom_sous_obj.split(".")[-1])
                # msgCsl(f"Objet lié:{mon_objet.Label} , lien local: {nom_lien}")
        else:
            # CAS LOCAL : L'objet est directement dans le document actif
            mon_objet = FreeCAD.ActiveDocument.getObject(nom_unique)
        return mon_objet

    def majMasse(self):
        selindexes = self.widget.BOM_objects_listView.selectedIndexes()
        volume = 0.0
        for index in selindexes:
            item = self.my_model.itemFromIndex(index)
            obj = self.getObjFromListViewItem(item.data(QtCore.Qt.UserRole))
            if hasattr(obj, "Shape"):
                volume += obj.Shape.Volume
        unit = FreeCAD.ActiveDocument.UnitSystem.split("(")[1].split(",")[0]
        if unit == "mm":
            volume = volume / 1000 ** 3
            self.widget.masse_label.setText(f"{volume * self.widget.masseVolumique_spinBox.value():.2f} kg")
        else:
            self.widget.masse_label.setText(f"Unité {unit} non prise en compte")

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
            # obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
            ext_label = item.data(QtCore.Qt.UserRole)
            msgCsl(f"SelectedObjectsPropertyChange ext_label {ext_label} ")
            obj = self.getObjFromListViewItem(ext_label)
            # if prop.Prefix: prefix = prop.Group else: prefix = ""
            prop_name = (prop["Group"] + "_" if prop["Prefix"] else "") + prop["Name"]
            # msgCsl(f"prop_name {prop_name}")
            if not hasattr(obj, prop_name):
                obj.addProperty(prop["Type"], prop_name, prop["Group"])
            setattr(obj, prop_name, value)
            if self.drawEdgeBand(ext_label):
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
                # obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
                ext_label = item.data(QtCore.Qt.UserRole)
                obj = self.getObjFromListViewItem(ext_label)
                msgCsl(f"updateEdgeBandCheckBoxFromObj ext_label {ext_label} ")
                for key, edgeband in EDGEBAND_PROPERTIES.items():
                    # msgCsl(f"updateEdgeBandCheckBoxFromObj, key edgeband {key}, obj {obj.Label}")
                    prop_name = (edgeband["Group"] + "_" if edgeband["Prefix"] else "") + edgeband["Name"]
                    if hasattr(obj, prop_name):
                        getattr(self.widget, keyToObj[key]).setChecked(getattr(obj, prop_name))
                    else:
                        getattr(self.widget, keyToObj[key]).setChecked(False)
                f_recompute = self.drawEdgeBand(ext_label)
        else:
            self.updateEdgeBands = True
            return
        if f_recompute: FreeCAD.ActiveDocument.recompute()
        # self.onSelectFreeCAD_clicked()
        self.updateEdgeBands = True

    def drawEdgeBand(self, ext_label):

        # label = obj.Label.lower()
        # is_mt = any(k in label for k in ["mt", "montant"])
        # is_tv = any(k in label for k in ["tv", "traverse", "tab", "tablette"])
        # is_ambiguous_name = any(k in label for k in ["fond", "tiroir", "porte", "facade"])
        EdgeBand_created = False
        GRAIN_OBJ_OFFSET = 20
        # GRAIN_OBJ_THICKNESS = 19
        # if hasattr(obj, "Nest_grain"):
        msgCsl(f"drawEdgeBand ext_label {ext_label} ")
        obj = self.getObjFromListViewItem(ext_label)
        activedoc = FreeCAD.ActiveDocument
        tmp_obj = activedoc.getObject(ext_label.split(".")[0])
        if hasattr(tmp_obj, "LinkedObject"):
            targetdoc = activedoc.getObject(ext_label.split(".")[0]).LinkedObject.Document
        else:
            targetdoc = activedoc
        # msgCsl(f"targetdoc {targetdoc.Name}")

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
        # ext_label = f"<{obj.Document.Name}>{obj.Label}"
        # msgCsl(f"drawEdgeBand ext_label {ext_label} ")
        for key, edgeband in EDGEBAND_PROPERTIES.items():
            prop_name = (edgeband["Group"] + "_" if edgeband["Prefix"] else "") + edgeband["Name"]
            translation = FreeCAD.Vector(0.0, 0.0, 0.0)
            if self.edgeband_objs.get(ext_label):
                if self.edgeband_objs[ext_label].get(edgeband["Name"]):
                    self.edgeband_objs[ext_label][edgeband["Name"]].Visibility = getattr(obj, prop_name)
                    continue
            if hasattr(obj, prop_name):
                # msgCsl(f"obj {obj.Label}, prop_name {prop_name}")
                if getattr(obj, prop_name):
                    face = KeyToFace[obj.Nest_Thickness][obj.Nest_grain][AvantToFront[edgeband["Name"]]]
                    points = Faces[face]
                    translation = translation.add(FreeCAD.Vector(Offset[face]))*GRAIN_OBJ_OFFSET
                    FreeCAD.setActiveDocument(targetdoc.Name)
                    oline = Draft.make_wire(points, placement=FreeCAD.Placement(), closed=True, face=True, support=None)
                    FreeCADGui.Selection.clearSelection()
                    FreeCAD.setActiveDocument(activedoc.Name)
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
                    if ext_label not in self.edgeband_objs:
                        self.edgeband_objs[ext_label] = {}
                    self.edgeband_objs[ext_label][edgeband["Name"]] = oline
                    EdgeBand_created = True
                else:
                    if self.edgeband_objs.get(ext_label):
                        if self.edgeband_objs[ext_label].get(edgeband["Name"]):
                            self.edgeband_objs[ext_label][edgeband["Name"]].Visibility = getattr(obj, prop_name)
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
                # obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
                obj = self.getObjFromListViewItem(item.data(QtCore.Qt.UserRole))
                # msgCsl(f"onMaterialSelectionChanged: item.data {item.data(QtCore.Qt.UserRole)} - {obj.Label}")
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
        self.majMasse()

    def objTransparencyBackupRestore(self, mode = "Backup" ):
        if mode == "Backup":
            for i in range(self.my_model.rowCount()):   #self.widget.BOM_objects_listView.model()
                # item = self.widget.BOM_objects_listView.model().item(i) # Récupère l'objet QStandardItem
                item = self.my_model.item(i)
                # msgCsl(f"text listview: {i} - {item.text()}")
                obj = self.getObjFromListViewItem(item.data(QtCore.Qt.UserRole))
                # msgCsl(f"objTransparencyBackupRestore obj: {obj}")
                viewer_container = getParentViewObject(obj) #FreeCAD.ActiveDocument.getObjectsByLabel(item.text())[0])
                if self.obj_transparency.get(item.data(QtCore.Qt.UserRole)) == None:
                    # msgCsl(f"self.obj_transparency.get(item.text()) {self.obj_transparency.get(item.text())}")
                    self.obj_transparency[item.data(QtCore.Qt.UserRole)] = viewer_container.ViewObject.Transparency
        elif mode == "Restore":
            for key, value in self.obj_transparency.items():
                obj = self.getObjFromListViewItem(key)
                viewer_container = getParentViewObject(obj)
                viewer_container.ViewObject.Transparency = value

    def setUnSelectedObjectTransparent(self):
        if self.widget.Transparency_checkBox.isChecked():
            selindexes = self.widget.BOM_objects_listView.selectedIndexes()

            for i in range(self.widget.BOM_objects_listView.model().rowCount()):
                item = self.my_model.item(i) #self.widget.BOM_objects_listView.model().item(i) # Récupère l'objet QStandardItem
                # obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
                obj = self.getObjFromListViewItem(item.data(QtCore.Qt.UserRole))
                viewer_container = getParentViewObject(obj)
                if not item.index() in selindexes:
                    viewer_container.ViewObject.Transparency = 90
                    ext_label = item.data(QtCore.Qt.UserRole)
                    # msgCsl(f"setUnSelectedObjectTransparent key {key} ")
                    if self.edgeband_objs.get(ext_label):
                        for edgeband in EDGEBAND_PROPERTIES.values():
                            if self.edgeband_objs[ext_label].get(edgeband["Name"]):
                                self.edgeband_objs[ext_label][edgeband["Name"]].Visibility = False
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
        # select the object in Gui if transparency is not checked
        if not self.widget.Transparency_checkBox.isChecked():
            self.onSelectFreeCAD_clicked()

    def GrainObjectsListUpdate(self):

        f_recompute = False
        # For objects which aren't anymore in ListView, corresponding grain_obj has to be deleted'
        obj_labels = []
        for ob in self.objects:
            obj_labels.append(ob[1])
        for key in self.grain_objs.keys():
            # msgCsl(f"obj_labels {obj_labels}")
            # msgCsl(f"grain_objs {self.grain_objs}")
            if not key in obj_labels:
                # msgCsl(f"remove key {key}")
                self.removeGrainObj(key)
        selindexes = self.widget.BOM_objects_listView.selectedIndexes()

        # grain_obj of non-selected objects are hidden, those existing and selected are shown, other created
        # if selindexes:
        for i in range(self.widget.BOM_objects_listView.model().rowCount()):
            item = self.my_model.item(i) # Récupère l'objet QStandardItem
            if not item.index() in selindexes:
                # item = self.widget.BOM_objects_listView.model().itemFromIndex(i)
                ext_label = item.data(QtCore.Qt.UserRole)
                # obj = self.getObjFromListViewItem(ext_label) #FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
                if self.grain_objs.get(ext_label):
                    self.grain_objs[ext_label].Visibility = False
        for index in selindexes:
            item = self.my_model.itemFromIndex(index)
            ext_label = item.data(QtCore.Qt.UserRole)
            # obj = self.getObjFromListViewItem(ext_label)
            # msgCsl(f"obj wood grain: {obj.Label}")
            try:
                self.grain_objs[ext_label].Visibility = True and self.widget.WoodGrainDisplay_checkBox.isChecked()
            except:
                f_recompute = self.createGrainObj(ext_label)
        if f_recompute: FreeCAD.ActiveDocument.recompute()

    def removeGrainObj(self, grain_obj_label):
        try:
            obj = self.getObjFromListViewItem(grain_obj_label)
            obj.Document.removeObject(self.grain_objs[grain_obj_label].Name)
            self.grain_objs.pop(grain_obj_label)
        except:
            pass

    def createGrainObj(self, ext_label):
        GRAIN_OBJ_OFFSET = 40
        GRAIN_OBJ_THICKNESS = 19
        f_recompute = False
        obj = self.getObjFromListViewItem(ext_label)
        if hasattr(obj, "Nest_grain"):
            # parent_obj = get_parent_part(obj)
            x_length = obj.Shape.BoundBox.XLength
            y_length = obj.Shape.BoundBox.YLength
            z_length = obj.Shape.BoundBox.ZLength
            o_parent = get_parent_part(obj)
            # msgCsl(f"createGrainObj parent = {o_parent.Label}")
            # pl = o_parent.Placement
            try:
                if not "PartDesign" in obj.TypeId:
                    pl_obj = obj.Placement
                else:
                    pl_obj = FreeCAD.Placement()
            except:
                pl_obj = FreeCAD.Placement()
                # msgCsl(f"pl_obj {pl_obj}")
            if  hasattr(obj, "_Body"): # obj.InList[0].TypeId == "PartDesign::Body":
                pl_body = obj._Body.Placement  #InList[0].Placement
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

            activedoc = FreeCAD.ActiveDocument
            # msgCsl(f"createGrainObj, ext_label {ext_label} ")
            tmp_obj = activedoc.getObject(ext_label.split(".")[0])
            if hasattr(tmp_obj, "LinkedObject"):
                targetdoc = activedoc.getObject(ext_label.split(".")[0]).LinkedObject.Document
            else:
                targetdoc = activedoc
            # msgCsl(f"targetdoc {targetdoc.Name}")
            FreeCAD.setActiveDocument(targetdoc.Name)
            # FreeCAD.ActiveDocument = FreeCAD.getDocument(targetdoc.Name)
            # FreeCADGui.setActiveDocument(targetdoc.Name)
            # FreeCADGui.ActiveDocument = FreeCADGui.getDocument(targetdoc.Name)
            oline = Draft.make_wire(points, placement=FreeCAD.Placement(), closed=True, face=True, support=None)
            FreeCADGui.Selection.clearSelection()
            # msgCsl(f"activedoc {activedoc.Name}")
            FreeCAD.setActiveDocument(activedoc.Name)
            # FreeCAD.ActiveDocument = FreeCAD.getDocument(activedoc.Name)
            # FreeCADGui.setActiveDocument(activedoc.Name)
            # FreeCADGui.ActiveDocument = FreeCADGui.getDocument(activedoc.Name)
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
            oline.ViewObject.ShapeAppearance = (FreeCAD.Material(DiffuseColor=ocolor,AmbientColor=ocolor,SpecularColor=ocolor,EmissiveColor=ocolor,Shininess=(1.0),Transparency=(0.00),))
            oline.ViewObject.LineColor = ocolor
            oline.ViewObject.PointColor = ocolor
            # oline.ViewObject.Transparency = 50
            oline.ViewObject.LineWidth = 0.01
            # key = f"<{obj.Document.Name}>{obj.Label}"
            self.grain_objs[ext_label] = oline
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
                oFC = self.getObjFromListViewItem(obj[1])
                if oFC.BOM_mat == material:
                    # if oFC.Name == obj[1]:
                    objs.append(obj[1])
                    # elif oFC.Name in obj[1]:
                    #     objs.append(f"{obj[1].split(oFC.Name)[0]}{oFC.Name}")
            if objs:
                FreeCADGui.Selection.clearSelection()
                for obj in objs:
                    names = obj.split(".")
                    obj_name = names[0]
                    if len(names) > 1:
                        subobj = ".".join(names[1:]) + "."
                        # msgCsl(f"onSelectFreeCAD_clicked: {FreeCAD.ActiveDocument.Name} - {obj_name} -> {subobj}")
                        FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Name, obj_name, subobj)
                    else:
                        FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Name, obj_name)

    def onClickSelectBodiesOfMat(self):
        if self.widget.material_listView.currentIndex():
            # for index in self.widget.BOM_objects_listView.selectedIndexes():
            #     item = self.widget.BOM_objects_listView.model().itemFromIndex(index)
            current_index = self.widget.material_listView.currentIndex()
            material = current_index.data(QtCore.Qt.DisplayRole)
            bodies = []
            for obj in self.objects:
                oFC = self.getObjFromListViewItem(obj[1])
                if oFC.BOM_mat == material:
                    # if "PartDesign::" in oFC.TypeId:
                    #     FreeCADGui.Selection.clearSelection()
                    #     FreeCADGui.Selection.addSelection(oFC)
                    #     sels = Gui.Selection.getSelectionEx("", 0)
                    #     sel = sels[0]
                    #     # doc = sel.Document
                    #     sub = sel.SubElementNames[0] if sel.SubElementNames else ""
                    #     subs = sub.split(".")[:-1]
                    #     # path = [sel.Object] + [doc.getObject(name) for name in subs]
                    #     # msgCsl(f"{[o.Label for o in path]}")
                    #     # msgCsl(f"Object {obj[1]} Body name: {subs[-2]}")
                    #     bodies.append(subs[-2])
                    # if "Part::" in oFC.TypeId:
                    viewObj = getParentViewObject(oFC)
                    if viewObj.Name == obj[1]:
                        bodies.append(obj[1])
                    elif viewObj.Name in obj[1]:
                        bodies.append(f"{obj[1].split(viewObj.Name)[0]}{viewObj.Name}")
            if bodies:
                FreeCADGui.Selection.clearSelection()
                for body in bodies:
                    names = body.split(".")
                    obj_name = names[0]
                    if len(names) > 1:
                        subobj = ".".join(names[1:]) + "."
                        # msgCsl(f"onSelectFreeCAD_clicked: {FreeCAD.ActiveDocument.Name} - {obj_name} -> {subobj}")
                        FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Name, obj_name, subobj)
                    else:
                        FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Name, obj_name)

    def onSelectFreeCAD_clicked(self):
        self.setUnSelectedObjectTransparent()
        FreeCADGui.Selection.clearSelection()
        for index in self.widget.BOM_objects_listView.selectedIndexes():
            # item = self.widget.BOM_objects_listView.model().itemFromIndex(index)
            # obj = FreeCAD.ActiveDocument.getObject(self.objects[item.row()][1])
            # msgCsl(f"selected row {item.row()}, data {item.text()}, self.objects : index {self.objects[item.row()][0]}, name {self.objects[item.row()][1]}")
            # FreeCADGui.Selection.addSelection(obj)
            item = self.my_model.itemFromIndex(index)
            ext_label = item.data(QtCore.Qt.UserRole)
            names = ext_label.split(".")
            obj_name = names[0]
            if len(names) > 1:
                subobj = ".".join(names[1:]) + "."
                # msgCsl(f"onSelectFreeCAD_clicked: {FreeCAD.ActiveDocument.Name} - {obj_name} -> {subobj}")
                FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Name, obj_name, subobj)
            else:
                FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Name, obj_name)

    def setBOMtoTrue(self):
        for index in self.widget.BOM_objects_listView.selectedIndexes():
            item = self.my_model.itemFromIndex(index)
            obj = self.getObjFromListViewItem(item.data(QtCore.Qt.UserRole))
            obj.BOM_destination = True
        self.BOM_objects_List_update()

    def setBOMtoFalse(self):
        for index in self.widget.BOM_objects_listView.selectedIndexes():
            item = self.my_model.itemFromIndex(index)
            obj = self.getObjFromListViewItem(item.data(QtCore.Qt.UserRole))
            obj.BOM_destination = False
        self.BOM_objects_List_update()

    def resetFilter(self):
        self.widget.excludeFilter_lineEdit.setText("")
        self.widget.includeFilter_lineEdit.setText("")

    def BOM_objects_List_update(self):
        self.my_model.clear()
        self.objects = []
        i = 0

        # On prépare une structure uniforme pour les objets locaux
        objets_bom = []
        if self.widget.linkObjects_checkBox.isChecked():
            objets_bom = preparer_liste_objets_for()
        else:
            # Si décoché, on recrée la même structure de dictionnaire pour le local
            for obj in FreeCAD.ActiveDocument.Objects:
                if hasattr(obj, "BOM_destination"):
                    objets_bom.append({
                        "obj_reference": obj,
                        "nom_unique": obj.Name,
                        "parent_label": ""
                    })

        for item_struct in objets_bom:
            if item_struct["parent_label"] == "":
                obj = item_struct["obj_reference"]
            else:
                doc = FreeCAD.ActiveDocument.getObjectsByLabel(item_struct["parent_label"])[0].LinkedObject.Document
                obj = doc.getObject(item_struct["nom_unique"].split(".")[-1])
            add_obj = False

            # Filtres d'exclusion / inclusion basés sur le Label d'origine de l'objet
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
                        add_obj = obj.BOM_destination
                    case [False, True]:
                        add_obj = not obj.BOM_destination

            if add_obj:
                # Formatage du texte affiché dans la ListView
                if item_struct["parent_label"]:
                    label_affichage = f"<{item_struct['parent_label']}> {obj.Label}"
                else:
                    label_affichage = obj.Label

                # Création de l'item de liste Qt
                listitem = QtGui.QStandardItem(label_affichage)

                # SÉCURITÉ : On stocke le nom interne unique (ex: 'Link004.Box002') TRÈS IMPORTANT pour la sélection future
                listitem.setData(item_struct["nom_unique"], QtCore.Qt.UserRole)

                # Gestion de l'icône directement via l'objet référencé (marche en local et en externe)
                if hasattr(obj, "ViewObject") and obj.ViewObject and hasattr(obj.ViewObject, "Icon"):
                    listitem.setData(obj.ViewObject.Icon, QtCore.Qt.DecorationRole)

                self.my_model.appendRow(listitem)

                # self.objects suit la structure [index, NomUnique]
                self.objects.append([i, item_struct["nom_unique"]])
                i += 1

        for i in range(self.my_model.rowCount()):
            item = self.my_model.item(i)
            # msgCsl(f"nom dans le model : {item.text()} - {item.data(QtCore.Qt.UserRole)}")
            # msgCsl(f"self.objects: {i} - {self.objects[i][1]}")
        self.BOM_materials_list_update()
        self.objTransparencyBackupRestore("Backup")
        self.setUnSelectedObjectTransparent()
        self.GrainObjectsListUpdate()
        return True

    def BOM_materials_list_update(self):
        if self.objects:
            mat_list = []
            for obj in self.objects:
                oFC = self.getObjFromListViewItem(obj[1])
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
                # name = self.grain_objs[key].Name
                # FreeCAD.ActiveDocument.removeObject(name)
                self.removeGrainObj(key)
                # msgCsl(f"Suppression de l'objet : {name}")
            except:
                pass
        # 1. Supprimer les objets de edgeband dans le document
        for key in list(self.edgeband_objs.keys()):
            for edge in list(self.edgeband_objs[key].keys()):
                try:
                    name = self.edgeband_objs[key][edge].Name
                    obj = self.getObjFromListViewItem(key)
                    obj.Document.removeObject(name)
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
