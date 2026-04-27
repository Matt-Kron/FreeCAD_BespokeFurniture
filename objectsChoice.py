import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets
import os

__dir__ = os.path.dirname(__file__)

class ObjChoiceDialog(QtWidgets.QDialog):
    def __init__(self):
        super(ObjChoiceDialog, self).__init__()
        self.objs = []
        self.setup_ui()

    def setup_ui(self):
        # Charger le fichier UI
        ui_file = __dir__ + f"/{os.path.splitext(os.path.basename(__file__))[0]}.ui"
        print(f"Opening {ui_file}")
        self.ui = Gui.PySideUic.loadUi(ui_file)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.my_model = QtGui.QStandardItemModel()

        self.my_model.clear()
        list_obj = []
        i = 0
        for obj in App.ActiveDocument.Objects:
            if obj.TypeId in ['PartDesign::AdditiveBox', 'Part::Box', 'Part::*',] and obj.Shape.Solids:
                list_obj.append(obj.Label)
        for item in list_obj:
            listitem = QtGui.QStandardItem(item)
            self.my_model.appendRow(listitem)
            listitem.setData(App.ActiveDocument.getObjectsByLabel(item)[0].ViewObject.Icon,QtCore.Qt.DecorationRole)
        self.ui.objects_listView.setModel(self.my_model)
        self.ui.objects_listView.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, selected, deselected):
        """Gère les changements de sélection dans la liste."""
        selected_items = self.ui.objects_listView.selectionModel().selectedIndexes()
        if len(selected_items) > 2:
            # Limiter la sélection à 2 objets
            last_selected = selected_items[-1]
            self.ui.objects_listView.selectionModel().select(last_selected, QtCore.QItemSelectionModel.Deselect)
            QtWidgets.QMessageBox.warning(self, "Attention", "Vous ne pouvez sélectionner que 2 objets maximum.")

    def cleanUp(self):
        if hasattr(App, "ObjChoiceDialog"):
            delattr(App, "ObjChoiceDialog")

    def accept(self):
        # return self.obj1, self.obj2
        selected_items = self.ui.objects_listView.selectionModel().selectedIndexes()

        # Récupérer les objets FreeCAD correspondants
        for index in selected_items:
            label = self.my_model.itemFromIndex(index).text()
            self.objs.append(App.ActiveDocument.getObjectsByLabel(label)[0])
        super().accept()
        # self.reject()

    def reject(self):
        # self.cleanUp()
        # self.ui.close()
        super().reject()

def main():
    dialog = ObjChoiceDialog()
    # dialog.ui.show()
    if dialog.ui.exec() == QtWidgets.QDialog.Accepted:
    # if dialog.exec() == QtWidgets.QDialog.Accepted:
        Gui.Selection.clearSelection()
        for obj in dialog.objs:
            Gui.Selection.addSelection(obj)


if __name__ == "__main__":
    main()
    # if objs:
    #     Gui.Selection.clearSelection()
    #     Gui.Selection.addSelection(objs)