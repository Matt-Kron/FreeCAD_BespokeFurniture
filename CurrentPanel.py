# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 18:37:01 2026

@author: Matthieu
"""

import os
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui
from FreeCAD_BespokeFurniture.lib_menuiserie import *


__dir__ = os.path.dirname(__file__)
ui_file = __dir__ + "/CurrentPanel.ui"
global iconPath
iconPath = __dir__ + '/Icons/'

class CurrentPanel_dialog(QtCore.QObject):
    def __init__(self):
        super(CurrentPanel_dialog , self).__init__() # Initialisation du parent

        # Chargement de l'UI
        self.widget = Gui.PySideUic.loadUi(ui_file)
        self.panels = []
        self.panels_model = QtGui.QStandardItemModel()
        self.widget.panels_listView.setModel(self.panels_model)
        self.widget.buttonBox.accepted.connect(self.Ok_clicked)
        self.widget.buttonBox.rejected.connect(self.Cancel_clicked)
        self.PanelsUpdate()

    
    def PanelsUpdate(self):
        fcDoc = App.ActiveDocument
        if hasattr(fcDoc, 'PanneauManager'):
            if hasattr(fcDoc.PanneauManager, "liste_panneaux"):
                current_panel = getCurrentWoodPanel()[0].split(';')[0]
                lines = fcDoc.PanneauManager.liste_panneaux
                i = 0
                for line in lines[1:]:  
                    if line.strip():
                        parts = line.split(';')
                        if len(parts) >= 5:
                            nom_abrege = parts[0]
                            # msgCsl(f"PanelsUpdate nom_abrege {nom_abrege}")
                            if nom_abrege == current_panel: 
                                # msgCsl(f"PanelsUpdate nom_abrege {nom_abrege} == current_panel {current_panel}, {i}")
                                index = i
                            item_nom = QtGui.QStandardItem(nom_abrege)
                            self.panels_model.appendRow(item_nom)
                    i += 1
                self.widget.panels_listView.setCurrentIndex(self.panels_model.index(index, 0))
                # self.widget.panels_listView.setCurrentIndex(self.panels_model.index(1, 0))
            else:
                userMsg("No panels list found")
                self.Cancel_clicked()
                
        else:
            userMsg("No panels list found")
            self.Cancel_clicked()

    def cleanUp(self):
        if hasattr(App, "CurrentPanel_Dialog"):
            delattr(App, "CurrentPanel_Dialog")
        
    def Ok_clicked(self):
        index = self.widget.panels_listView.selectedIndexes()[0]
        App.ActiveDocument.PanneauManager.current_panel = index.row() + 1
        
        self.Cancel_clicked()
    
    def Cancel_clicked(self):
        self.cleanUp()
        self.widget.close()

# ====================================================================
# FONCTION PRINCIPALE DE LA MACRO 
# ====================================================================
def run():
    # Vérifier si une instance existe déjà
    if hasattr(App, "CurrentPanel_Dialog"):
        try:
            # Essayer de fermer l'ancienne fenêtre proprement
            App.CurrentPanel_Dialog.widget.close()
        except:
            # Si le widget a déjà été supprimé mais la réf est restée
            pass

    # Créer la nouvelle instance
    App.CurrentPanel_Dialog = CurrentPanel_dialog()
    App.CurrentPanel_Dialog.widget.show()

if __name__ == '__main__':
    run()
