import FreeCAD as App
from FreeCAD_BespokeFurniture.lib_menuiserie import *

class bspfObj:
    def __init__(self):
        self.type = "" # first field of bspf_tag property, defining wether the object is vertical or horizontal, assembled at the end or in the middle
        self.temp = False # True for temporary object to be deleted at the end of the macro which uses the class
        self.caisson = "" # second field of bspf_tag property, defining the owner sub-assembly
        self.group = "" # second field of bspf_tag property, defining the group (shelves, jambs)
        self._object = None # FreeCAD object that define the geometry, might be a PartDeisgn:: AdditiveBox
        self.part = None # Part contener of self.object

    def getTag(self):
        if self._object:
            # msgCsl(f"Fonction {__name__} {self._object.Label}")
            self.type, self.caisson, self.group = getObjTag(self._object).values()

    def removeObject(self):
        if self.part:
            self.part.removeObjectsFromDocument()
            self.part.Document.removeObject(self.part.Name)
            self.part = None
            self.type, self.caisson, self.group = "", "", ""
            self.temp = False
            self._object = None

    def getPart(self):
        self.part = get_parent_part(self._object)

    @property
    def object(self):
        return self._object

    @object.setter
    def object(self, obj):
        self._object = obj
        self.getPart()
        self.getTag()

    def setTag(self, typ = None, caisson = None, groupe_etageres = None):
        setObjTag(self._object, typ, caisson, groupe_etageres)

