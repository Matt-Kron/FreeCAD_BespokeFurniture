import FreeCAD
import FreeCADGui
import re, os
import Draft
from datetime import datetime
from PySide import QtGui, QtCore

# =============================================================================
# DEFINITION DES PANNEAUX DE MATIERE DISPONIBLES (inchangé)
# =============================================================================
WOOD_PANELS = {"mdf2440" : ("mdf2440", 2440, 1220, 19, 10, 10),
               "mdf2800" : ("mdf2800", 2800, 2070, 19, 10, 10),
               "mela8" : ("mela", 2800, 2070, 8, 10, 10),
               "mela19" : ("mela", 2800, 2070, 19, 10, 10),
               "tab600" : ("tab", 2800, 600, 19, 10, 0),
               "tab500" : ("tab", 2800, 500, 19, 10, 0),
               "tab400" : ("tab", 2800, 400, 19, 10, 0),
               "valchromat" : ("valchromat", 2440, 1830, 19, 10, 10),
               "latte chene 2.5" : ("latte chene 2.5", 2500, 1220, 19, 10, 10),
               "latte chene 3" : ("latte chene 3", 3050, 1530, 19, 10, 10),
               "CTP chene 9mm" : ("CTP chene 9mm", 2500, 1220, 9, 10, 10),
               "Chene massif 27mm 1.5" : ("Chene massif 27mm 1.5", 1500, 1250, 27, 10, 10),
               "Chene massif 27mm 2.5" : ("Chene massif 27mm 2.5", 2480, 1250, 27, 10, 10),
               }

COLUMNS = { "material" : "H",
            "length" : "D",
            "width" : "F",
            "height" : "E",
            "label" : "C",
            "rotation" : "I",
            "quantity" : "G",
            "parent" : "B",
            }

SAW_WIDTH = 3
REFRESH_CUT_X = 10
REFRESH_CUT_Y = 10

NESTED_OBJECT_SUFFIX = "_nested"

VERBOSE = True

def msg_console(message):
    if VERBOSE:
        print(f"{message}\n")

# =============================================================================
# Classes de définition
# =============================================================================
class Panel:

    def __init__(self, material = "mela"):

        self.material = material
        self.length = 2500
        self.width = 1220
        self.height = 19
        self.objects = []
        self.refreshCut_x = REFRESH_CUT_X
        self.refreshCut_y = REFRESH_CUT_Y
        self.area = self.length * self.width
        self.sawCut = []

    def update_area(self):
        self.area = self.length * self.width

    # CORRECTION: RÉINTRODUCTION DE addSawCut
    def addSawCut(self, start, end):
        """Ajoute une ligne de coupe à la liste sawCut du panneau."""
        self.sawCut.append((start, end))

    def copy(self):

        c = Panel(self.material)
        c.length = self.length
        c.width = self.width
        c.height = self.height
        c.objects = self.objects.copy()
        c.refreshCut_x = self.refreshCut_x
        c.refreshCut_y = self.refreshCut_y
        c.area = self.area
        return c

class n_object:

    def __init__(self, material = "mela"):

        self.length = 100
        self.width = 30
        self.height = 19
        self.material = material
        self.rotation = False
        self.panelPosition_x = 0
        self.panelPosition_y = 0
        self.panelRotation = 0
        self.cutOrientation = [True, True, True, True] # x~x', y~y', x~y', y~x'
        self.area = self.length * self.width
        self.label = "Nested object"

    def update_area(self):
        self.area = self.length * self.width

    def copy(self):

        c = n_object(self.material)
        c.length = self.length
        c.width = self.width
        c.height = self.height
        c.rotation = self.rotation
        c.panelPosition_x = self.panelPosition_x
        c.panelPosition_y = self.panelPosition_y
        c.panelRotation = self.panelRotation
        c.cutOrientation = self.cutOrientation
        c.area = self.area
        c.label = self.label
        return c

class Nest:

    def __init__(self, panels = None, objects = None):

        self.panels = panels
        self.objects = objects
        self.SawCut = True
        self.SawWidth = SAW_WIDTH
        self.CrossCut = True
        self.nofit_objects = []
        self.left_area = 0


    def optimize(self, panel, n_type = "", obj_sort_type = "area"):

        if not self.objects:
            print("Objects list is empty")
            return

        if len(self.panels) < 1:
            print("Panels list is empty")
            return
        copy_objects=[]
        match obj_sort_type:
            case "area":
                self.objects = sorted(self.objects, key=lambda objet: objet.area)
                copy_objects = self.objects.copy()
            case "length":
                for obj in self.objects:
                    # Fixe l'orientation initiale pour le tri
                    if obj.width > obj.length and obj.rotation:
                        w = obj.width
                        obj.width = obj.length
                        obj.length = w
                self.objects.sort(key = lambda objet: (objet.length, objet.area))
                copy_objects = self.objects.copy()

        self.remove_objects_too_big(copy_objects, panel.area)

        # move objects deleted in copy_objects from objects list to nofit objects
        for obj in self.objects:
            if obj.label not in [o.label for o in copy_objects]:
                self.nofit_objects.append(obj)
                self.remove_object(obj.label)

        rect = []
        # Initialisation du rectangle d'emboîtement (zone utile du panneau)
        rect.append((panel.length - 2*panel.refreshCut_x,
                     panel.width - 2*panel.refreshCut_y,
                     (panel.refreshCut_x, panel.refreshCut_y),
                     (panel.length - 2*panel.refreshCut_x)*(panel.width - 2*panel.refreshCut_y)
                     ))

        while len(rect)>0 and copy_objects:
            rect = sorted(rect, key=lambda re: re[3])
            """ remove objects with area bigger than max area of rect list """
            self.remove_objects_too_big(copy_objects, rect[-1][3])

            rec = rect.pop(0)

            if copy_objects:
                omin = Closest_Object(copy_objects[-1], copy_objects[:-1])

                if omin:
                    copy_objects.remove(omin)
                    copy_objects.insert(-1, omin)

                if rec[3] > 0:
                    rect_d, rect_h = self.Nest_step(panel, rec, copy_objects, n_type)

                    if rect_d[3] > 0:
                        rect.append(rect_d)
                    if rect_h[3] > 0:
                        rect.append(rect_h)


    def remove_object(self, obj_label):
        for i in range(0, len(self.objects)):
            if obj_label == self.objects[i].label:
                del self.objects[i]
                break

    def Nest_step(self, panel, rect, objs, n_type):

        """
         rect = (length, width, (pos x, pos y), area)
         pos x, pos y = x, y absolute position in the panel
        """

        PRINT_NESTED_OBJECT = True

        max_i = len(objs)-1
        for i in range(max_i, -1, -1):
            o = objs[i]
            if o.area <= rect[3]:
                match n_type:
                    case "align_longer":
                        if o.length <= rect[0] and o.width <= rect[1]:
                            o.panelPosition_x = rect[2][0]
                            o.panelPosition_y = rect[2][1]
                            self.remove_object(o.label)
                            o.label = o.label + NESTED_OBJECT_SUFFIX
                            panel.objects.append(o)
                            objs.pop(i)

                            rect_d = (rect[0] - (o.length + self.SawWidth*self.SawCut), rect[1],
                                      (rect[2][0] + o.length + self.SawWidth*self.SawCut, rect[2][1]),
                                      (rect[0] - o.length - self.SawWidth*self.SawCut)*rect[1])

                            rect_h = (o.length, rect[1] - o.width - self.SawWidth*self.SawCut,
                                      (rect[2][0], rect[2][1] + o.width + self.SawWidth*self.SawCut),
                                      o.length * (rect[1] - o.width - self.SawWidth*self.SawCut))

                            if rect_h[1]>0:
                                panel.addSawCut(FreeCAD.Vector(rect[2][0] ,
                                                               rect[2][1] + o.width + self.SawWidth*self.SawCut/2  ,
                                                               0 ),
                                                        FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length,
                                                                       rect[2][1] + o.width + self.SawWidth*self.SawCut/2 ,
                                                                       0 )
                                                        )
                            if rect_d[0] > 0:
                                panel.addSawCut(FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length ,
                                                               rect[2][1]  ,
                                                               0 ),
                                                        FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length,
                                                                       rect[2][1] + rect[1] ,
                                                                       0 )
                                                        )
                            return rect_d, rect_h

                    case "minimal_length_left":
                        dcuts = []
                        dX = rect[0] - o.length
                        dcuts.append(["dX", dX])
                        dY = rect[1] - o.width
                        dcuts.append(["dY", dY])
                        dXr = dYr = 1000000
                        if o.rotation:
                            dXr = rect[0] - o.width
                            dcuts.append(["dXr", dXr])
                            dYr = rect[1] - o.length
                            dcuts.append(["dYr", dYr])

                        # Remove all cases where the object is larger than the container
                        dcuts.sort( key=lambda item: item[1])
                        while dcuts[0][1] < 0 :
                            del dcuts[0]
                            if not dcuts : return (0, 0, (0, 0), 0), (0, 0, (0, 0), 0)

                        # Ajout des contraintes avec l'objet voisin pour affiner le choix (core v2 logic)
                        key_list = [key[0] for key in dcuts]
                        cuthv = None
                        if len(objs)> 1:
                            omin = objs[i-1]
                        else:
                            omin = None
                        if omin:
                            if "dX" in key_list:
                                if o.cutOrientation[1]:
                                    dcuts.append(["dX", dX - omin.length - self.SawWidth])
                                if o.cutOrientation[3]:
                                    dcuts.append(["dX", dX - omin.width - self.SawWidth])
                            if "dY" in key_list:
                                if o.cutOrientation[0]:
                                    dcuts.append(["dY", dY - omin.width - self.SawWidth])
                                if o.cutOrientation[2]:
                                    dcuts.append(["dY", dY - omin.length - self.SawWidth])
                            if "dXr" in key_list:
                                if o.cutOrientation[0]:
                                    dcuts.append(["dXr", dXr - omin.width - self.SawWidth])
                                if o.cutOrientation[2]:
                                    dcuts.append(["dXr", dXr - omin.length - self.SawWidth])
                            if "dYr" in key_list:
                                if o.cutOrientation[1]:
                                    dcuts.append(["dYr", dYr - omin.length - self.SawWidth])
                                if o.cutOrientation[3]:
                                    dcuts.append(["dYr", dYr - omin.width - self.SawWidth])

                            dcuts.sort( key=lambda item: item[1])
                            while dcuts[0][1] < 0 :
                                del dcuts[0]
                                if not dcuts : return (0, 0, (0, 0), 0), (0, 0, (0, 0), 0)

                        if not cuthv:
                            cuthv = dcuts[0][0]

                        # Application de la coupe et placement (conservée de la v2)
                        match cuthv:
                            case "dX":  # coupe horizontale, objet non tourné
                                if dY >= 0:
                                    o.panelPosition_x = rect[2][0]
                                    o.panelPosition_y = rect[2][1]
                                    self.remove_object(o.label)
                                    o.label = o.label + NESTED_OBJECT_SUFFIX
                                    panel.objects.append(o)
                                    objs.pop(i)

                                    rect_d = (rect[0] - (o.length + self.SawWidth*self.SawCut), o.width,
                                              (rect[2][0] + o.length + self.SawWidth*self.SawCut, rect[2][1]),
                                              (rect[0] - o.length - self.SawWidth*self.SawCut)*o.width)
                                    rect_h = (rect[0], rect[1] - o.width - self.SawWidth*self.SawCut,
                                              (rect[2][0], rect[2][1] + o.width + self.SawWidth*self.SawCut),
                                              rect[0]*(rect[1] - o.width - self.SawWidth*self.SawCut))
                                    if rect_d[0] > 0:
                                        panel.addSawCut(FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length , rect[2][1] , 0 ),
                                                        FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length , rect[2][1] + o.width + self.SawWidth*self.SawCut/2 , 0 ))
                                    if rect_h[1]>0:
                                        panel.addSawCut(FreeCAD.Vector(rect[2][0], rect[2][1] + o.width + self.SawWidth*self.SawCut/2  , 0 ),
                                                        FreeCAD.Vector(rect[2][0] + rect[0], rect[2][1] + o.width + self.SawWidth*self.SawCut/2 , 0 ))
                                    return rect_d, rect_h
                            case "dY":  # coupe verticale, objet non tourné
                                if dX >= 0:
                                    o.panelPosition_x = rect[2][0]
                                    o.panelPosition_y = rect[2][1]
                                    self.remove_object(o.label)
                                    o.label = o.label + NESTED_OBJECT_SUFFIX
                                    panel.objects.append(o)
                                    objs.pop(i)

                                    rect_d = (rect[0] - (o.length + self.SawWidth*self.SawCut), rect[1],
                                              (rect[2][0] + o.length + self.SawWidth*self.SawCut, rect[2][1]),
                                              (rect[0] - o.length - self.SawWidth*self.SawCut)*rect[1])

                                    rect_h = (o.length, rect[1] - o.width - self.SawWidth*self.SawCut,
                                              (rect[2][0], rect[2][1] + o.width + self.SawWidth*self.SawCut),
                                              o.length * (rect[1] - o.width - self.SawWidth*self.SawCut))

                                    if rect_h[1]>0:
                                        panel.addSawCut(FreeCAD.Vector(rect[2][0] , rect[2][1] + o.width + self.SawWidth*self.SawCut/2  , 0 ),
                                                        FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length, rect[2][1] + o.width + self.SawWidth*self.SawCut/2 , 0 ))
                                    if rect_d[0] > 0:
                                        panel.addSawCut(FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length , rect[2][1]  , 0 ),
                                                        FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length, rect[2][1] + rect[1] , 0 ))
                                    return rect_d, rect_h
                            case "dXr":  # coupe horizontale, objet tourné
                                if dYr >= 0:
                                    w = o.width
                                    o.width = o.length
                                    o.length = w
                                    o.panelPosition_x = rect[2][0]
                                    o.panelPosition_y = rect[2][1]
                                    self.remove_object(o.label)
                                    o.label = o.label + NESTED_OBJECT_SUFFIX
                                    panel.objects.append(o)
                                    objs.pop(i)

                                    rect_d = (rect[0] - (o.length + self.SawWidth*self.SawCut), o.width,
                                              (rect[2][0] + o.length + self.SawWidth*self.SawCut, rect[2][1]),
                                              (rect[0] - o.length - self.SawWidth*self.SawCut)*o.width)
                                    rect_h = (rect[0], rect[1] - o.width - self.SawWidth*self.SawCut,
                                              (rect[2][0], rect[2][1] + o.width + self.SawWidth*self.SawCut),
                                              rect[0]*(rect[1] - o.width - self.SawWidth*self.SawCut))
                                    if rect_d[0] > 0:
                                        panel.addSawCut(FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length , rect[2][1]  , 0 ),
                                                        FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length , rect[2][1] + o.width + self.SawWidth*self.SawCut/2 , 0 ))
                                    if rect_h[1]>0:
                                        panel.addSawCut(FreeCAD.Vector(rect[2][0], rect[2][1] + o.width + self.SawWidth*self.SawCut/2  , 0 ),
                                                        FreeCAD.Vector(rect[2][0] + rect[0], rect[2][1] + o.width + self.SawWidth*self.SawCut/2 , 0 ))
                                    return rect_d, rect_h
                            case "dYr":  # coupe verticale, objet tourné
                                if dXr >= 0:
                                    w = o.width
                                    o.width = o.length
                                    o.length = w
                                    o.panelPosition_x = rect[2][0]
                                    o.panelPosition_y = rect[2][1]
                                    self.remove_object(o.label)
                                    o.label = o.label + NESTED_OBJECT_SUFFIX
                                    panel.objects.append(o)
                                    objs.pop(i)

                                    rect_d = (rect[0] - (o.length + self.SawWidth*self.SawCut), rect[1],
                                              (rect[2][0] + o.length + self.SawWidth*self.SawCut, rect[2][1]),
                                              (rect[0] - o.length - self.SawWidth*self.SawCut)*rect[1])

                                    rect_h = (o.length, rect[1] - o.width - self.SawWidth*self.SawCut,
                                              (rect[2][0], rect[2][1] + o.width + self.SawWidth*self.SawCut),
                                              o.length * (rect[1] - o.width - self.SawWidth*self.SawCut))

                                    if rect_h[1]>0:
                                        panel.addSawCut(FreeCAD.Vector(rect[2][0] , rect[2][1] + o.width + self.SawWidth*self.SawCut/2  , 0 ),
                                                        FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length, rect[2][1] + o.width + self.SawWidth*self.SawCut/2 , 0 ))
                                    if rect_d[0] > 0:
                                        panel.addSawCut(FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length , rect[2][1]  , 0 ),
                                                        FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length, rect[2][1] + rect[1] , 0 ))
                                    return rect_d, rect_h
                            case "toto": # Stratégie par défaut/simple de la v2 (placement et découpe)
                                if o.length <= rect[0] and o.width <= rect[1]:
                                    o.panelPosition_x = rect[2][0]
                                    o.panelPosition_y = rect[2][1]
                                    self.remove_object(o.label)
                                    o.label = o.label + NESTED_OBJECT_SUFFIX
                                    panel.objects.append(o)
                                    objs.pop(i)

                                    # Découpe horizontale
                                    rect_d = (rect[0] - (o.length + self.SawWidth*self.SawCut), o.width*1,
                                              (rect[2][0] + o.length + self.SawWidth*self.SawCut, rect[2][1]),
                                              (rect[0] - (o.length + self.SawWidth*self.SawCut))*o.width
                                            )
                                    # Découpe verticale
                                    rect_h = (rect[0]*1, rect[1] - (o.width + self.SawWidth*self.SawCut),
                                              (rect[2][0], rect[2][1] + o.width + self.SawWidth*self.SawCut),
                                              rect[0]*(rect[1] - (o.width + self.SawWidth*self.SawCut))
                                            )
                                    if rect_d[0] > 0:
                                        panel.addSawCut(FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length , rect[2][1]  , 0 ),
                                                        FreeCAD.Vector(rect[2][0] + self.SawWidth*self.SawCut/2 + o.length , rect[2][1] + o.width + self.SawWidth*self.SawCut/2 , 0 ))
                                    if rect_h[1]>0:
                                        panel.addSawCut(FreeCAD.Vector(rect[2][0], rect[2][1] + o.width + self.SawWidth*self.SawCut/2  , 0 ),
                                                        FreeCAD.Vector(rect[2][0] + rect[0], rect[2][1] + o.width + self.SawWidth*self.SawCut/2 , 0 ))
                                    return rect_d, rect_h

        return (0, 0, (0, 0), 0), (0, 0, (0, 0), 0)

    def remove_objects_too_big(self, sorted_objects, area):

        run = True
        while run and sorted_objects:
            o = sorted_objects[-1]
            if o.area > area:
                sorted_objects.pop()
            else:
                run = False
        return

    def draw_nested_objects(self, YY, container):
        """
        Dessine les résultats dans le document spécifié par le container.
        """

        START_OFFSET = (0, YY)
        OFFSETX_BETWEEN_PANELS = 100
        ZAXIS = FreeCAD.Vector(0, 0, 1)
        doc = container.Document

        p_offset=[START_OFFSET[0], START_OFFSET[1]]
        p_translation = FreeCAD.Vector(0, 0, 0)
        mat_translation = FreeCAD.Vector(p_offset[0], p_offset[1], 0)

        # Crée un conteneur App::Part pour le matériau
        mat = self.panels[0].material
        g_mat = doc.addObject('App::Part', f'MaterialGroup_{mat}')
        g_mat.Placement = FreeCAD.Placement(mat_translation, FreeCAD.Rotation(ZAXIS, 0))
        container.addObject(g_mat)

        p_i = 1
        for p in self.panels:

            p_placement = FreeCAD.Placement(p_translation, FreeCAD.Rotation(ZAXIS, 0))

            # Dessin du panneau
            rect_p = Draft.makeRectangle(p.length, p.width, face=True)
            rect_p.Label = f"{p.material} Panel {p_i} {NESTED_OBJECT_SUFFIX}"

            # Crée un conteneur App::Part pour chaque panneau
            g_panel = doc.addObject('App::Part', f'PanelGroup_{mat}_{p_i}')
            g_panel.Placement = p_placement

            g_mat.addObject(g_panel)
            g_panel.addObject(rect_p)

            # Dessin des objets sur le panneau
            for o in p.objects:
                obj_placement = FreeCAD.Placement(FreeCAD.Vector(o.panelPosition_x, o.panelPosition_y, p.height + 1), FreeCAD.Rotation(ZAXIS, o.panelRotation))
                rect_o = Draft.makeRectangle(o.length, o.width, face=True, placement=obj_placement)
                rect_o.Label = o.label

                try:
                    # Nécessite l'importation de App pour Material, mais FreeCAD le gère souvent
                    rect_o.ViewObject.ShapeAppearance = (App.Material(DiffuseColor=(0.33,0.67,1.00),AmbientColor=(0.33,0.33,0.33),SpecularColor=(0.53,0.53,0.53),EmissiveColor=(0.00,0.00,0.00),Shininess=(0.90),Transparency=(0.00),))
                except Exception:
                    pass

                g_panel.addObject(rect_o)

            # Dessin des traits de coupe (Saw cuts)
            for sawCut in p.sawCut:
                l = Draft.make_line(sawCut[0] + FreeCAD.Vector(0,0,p.height), sawCut[1] + FreeCAD.Vector(0,0,p.height))
                l.Label = f"SawCut_{p_i}_{p.sawCut.index(sawCut) + 1} {NESTED_OBJECT_SUFFIX}"
                try:
                    l.ViewObject.LineColor = (1.0, 0.2, 0.2)
                    l.ViewObject.LineWidth = 3
                except Exception:
                    pass

                g_panel.addObject(l)

            p_i += 1
            p_translation = p_translation.add(FreeCAD.Vector(p.length + OFFSETX_BETWEEN_PANELS, 0, 0))

def Closest_Object(oM, objs):
    # =============================================================================
    # return the object from the list which as its length or width the closest to the reference object
    # =============================================================================
    omin = None
    orientation = [False, False, False, False]
    dlmin = 1000000

    for o in objs:
        dX = oM.length - o.length
        if dX >= 0 and dX <= dlmin:
            if dX < dlmin:
                orientation = [True, False, False, False]
            dlmin = dX
            omin = o
            orientation[0] = True
        dY = oM.width - o.width
        if dY >=0 and dY <= dlmin:
            if dY < dlmin:
                orientation = [False, True, False, False]
            omin = o
            dlmin = dY
            orientation[1] = True

        if o.rotation:
            dX = oM.length - o.width
            if dX >= 0 and dX <= dlmin:
                if dX < dlmin:
                    orientation = [False, False, True, False]
                omin = o
                dlmin = dX
                orientation[2] = True
            dY = oM.width - o.length
            if dY >=0 and dY <= dlmin:
                if dY < dlmin:
                    orientation = [False, False, False, True]
                omin = o
                dlmin = dY
                orientation[3] = True

    if omin:
        oM.cutOrientation = orientation

    return omin

def import_object_from_spreadsheat(spreadsheet, COLUMNS, line):

    filled_row = ""
    try:
        filled_row = spreadsheet.get(f"B{line}")
    except:
        return []

    if filled_row:
        try:
            o = n_object(str(spreadsheet.get(f"{COLUMNS['material']}{line}")))
            o.length = float(spreadsheet.get(f"{COLUMNS['length']}{line}"))
            o.width = float(spreadsheet.get(f"{COLUMNS['width']}{line}"))
            o.height = float(spreadsheet.get(f"{COLUMNS['height']}{line}"))

            parent = str(spreadsheet.get(f"{COLUMNS['parent']}{line}"))
            label = str(spreadsheet.get(f"{COLUMNS['label']}{line}"))
            o.label = f"{parent} - {label}"

            if str(spreadsheet.get(f"{COLUMNS['rotation']}{line}")).lower() == "true":
                o.rotation = True
            else:
                o.rotation = False
            o.update_area()

            qty = int(float(spreadsheet.get(f"{COLUMNS['quantity']}{line}")))
        except Exception as e:
            print(f"Erreur d'importation ligne {line}: {e}\n")
            return []

        objs = []
        if qty >= 1 :
            for nb in range(0, qty):
                new_obj = o.copy()
                new_obj.label = f"{parent} - {label} {nb+1}"
                objs.append(new_obj)
        return objs

# =============================================================================
# GUI Dialog Class (inchangée)
# =============================================================================
class NestingDialog(QtGui.QDialog):
    def __init__(self, obj2nest_data, panel_materials, parent=None):
        super(NestingDialog, self).__init__(parent)
        self.setWindowTitle("Options de Calepinage")
        self.setMinimumSize(850, 650)

        self.obj2nest_data = obj2nest_data
        self.panel_materials = panel_materials
        self.selected_nesting_types = ["minimal_length_left", "toto"]
        self.selected_obj_sort_types = ["length", "area"]

        self.init_ui()

    def init_ui(self):
        main_layout = QtGui.QVBoxLayout(self)
        lists_hbox = QtGui.QHBoxLayout()

        # 1a. Objects list
        obj_group = QtGui.QGroupBox("Objets à Calepiner")
        obj_layout = QtGui.QVBoxLayout(obj_group)
        self.obj_table_widget = QtGui.QTableWidget()
        self.obj_table_widget.setColumnCount(3)
        self.obj_table_widget.setHorizontalHeaderLabels(["Label", "Quantité", "Matériau"])
        self.obj_table_widget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.obj_table_widget.setSelectionMode(QtGui.QAbstractItemView.NoSelection)

        if self.obj2nest_data:
            self.obj_table_widget.setRowCount(len(self.obj2nest_data))
            for row, data in enumerate(self.obj2nest_data):
                self.obj_table_widget.setItem(row, 0, QtGui.QTableWidgetItem(data['label']))
                self.obj_table_widget.setItem(row, 1, QtGui.QTableWidgetItem(str(data['quantity'])))
                self.obj_table_widget.setItem(row, 2, QtGui.QTableWidgetItem(data['material']))
        else:
            self.obj_table_widget.setRowCount(1)
            self.obj_table_widget.setItem(0, 0, QtGui.QTableWidgetItem("Aucun objet trouvé dans la BOM"))

        header = self.obj_table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QtGui.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtGui.QHeaderView.ResizeToContents)

        obj_layout.addWidget(self.obj_table_widget)
        lists_hbox.addWidget(obj_group, 3)

        # 1b. Panels list
        panel_group = QtGui.QGroupBox("Panneaux Disponibles")
        panel_layout = QtGui.QVBoxLayout(panel_group)
        self.panel_list_widget = QtGui.QListWidget()

        if self.panel_materials:
            for material_name, material_data in self.panel_materials.items():
                self.panel_list_widget.addItem(f"{material_name}: L{material_data[1]} x W{material_data[2]} x H{material_data[3]}")
        else:
            self.panel_list_widget.addItem("Aucun panneau défini")

        self.panel_list_widget.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        panel_layout.addWidget(self.panel_list_widget)
        lists_hbox.addWidget(panel_group, 1)

        main_layout.addLayout(lists_hbox)

        # Bottom section: Nesting and Sorting Types (Multiple Selection)
        options_hbox = QtGui.QHBoxLayout()

        # Nesting Type Selection (Multiple)
        nesting_group = QtGui.QGroupBox("Type de Calepinage (Sélection Multiple)")
        nesting_layout = QtGui.QVBoxLayout(nesting_group)
        self.nesting_type_list = QtGui.QListWidget()
        self.nesting_type_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        nesting_types = ["minimal_length_left", "toto", "align_longer"]
        for n_type in nesting_types:
            item = QtGui.QListWidgetItem(n_type)
            if n_type in self.selected_nesting_types:
                item.setSelected(True)
            self.nesting_type_list.addItem(item)

        nesting_layout.addWidget(self.nesting_type_list)
        options_hbox.addWidget(nesting_group)

        # Object Sort Type Selection (Multiple)
        sort_group = QtGui.QGroupBox("Type de Tri des Objets (Sélection Multiple)")
        sort_layout = QtGui.QVBoxLayout(sort_group)
        self.obj_sort_type_list = QtGui.QListWidget()
        self.obj_sort_type_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        sort_types = ["length", "area"]
        for s_type in sort_types:
            item = QtGui.QListWidgetItem(s_type)
            if s_type in self.selected_obj_sort_types:
                item.setSelected(True)
            self.obj_sort_type_list.addItem(item)

        sort_layout.addWidget(self.obj_sort_type_list)
        options_hbox.addWidget(sort_group)

        main_layout.addLayout(options_hbox)

        # Standard buttons
        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def accept(self):
        self.selected_nesting_types = [item.text() for item in self.nesting_type_list.selectedItems()]
        self.selected_obj_sort_types = [item.text() for item in self.obj_sort_type_list.selectedItems()]
        super(NestingDialog, self).accept()

# =============================================================================
# Nettoyage et Initialisation
# =============================================================================
def clear_reportView():
    try:
        mw = FreeCADGui.getMainWindow()
        rv = mw.findChild(QtGui.QTextEdit, "Report view")
        if rv:
            rv.clear()
    except Exception as e:
        print(f"Warning: Could not clear Report View. {e}\n")

def find_last_row(spsheet):
    # Gestion des différents formats de retour de getNonEmptyRange() (chaîne ou tuple/liste)
    try:
        range_info = spsheet.getNonEmptyRange()
        if not range_info:
            return 1

        last_cell = ""

        # Si c'est une liste ou un tuple (ex: ('A1', 'H10')), on prend le dernier élément.
        if isinstance(range_info, (list, tuple)):
            last_cell = range_info[-1]
        # Si c'est une chaîne (ex: 'A1:H10'), on splitte.
        elif isinstance(range_info, str):
            last_cell = range_info.split(':')[-1]
        else:
            return 1

        # On extrait le numéro de ligne de la référence de cellule (ex: 'H10' -> 10)
        last_row_match = re.search(r'([A-Z]+)(\d+)$', last_cell)
        if last_row_match:
            return int(last_row_match.group(2))
        return 1
    except Exception as e:
        print(f"Erreur dans find_last_row: {e}\n")
        return 1

# =============================================================================
# MAIN SCRIPT EXECUTION
# =============================================================================
log_filepath = os.path.join(FreeCAD.getUserMacroDir(), "nesting.log")

def log_write(message):
    with open(log_filepath, 'a') as f:
        f.write(f"{timestamp()} : {message}\n")
import time
def timestamp():
    t = time.localtime()
    timestp = time.strftime('%d-%m-%Y_%H:%M', t)
    return timestp

with open(log_filepath, 'w') as f:
        f.write(f"{timestamp()} : Starting nesting\n")

def Main():
    clear_reportView()
    print("Starting Macro Nesting")

    # 1. CONTRÔLE DE SÉCURITÉ : VÉRIFIER L'EXISTENCE D'UN DOCUMENT ACTIF
    log_write("ActiveDocument not None")
    if FreeCAD.ActiveDocument is None:
        print("ERROR: Aucun document FreeCAD actif trouvé. Veuillez ouvrir un document (contenant la feuille de calcul 'BOM') et relancer la macro.\n")
        return

    # 3. Récupération de la feuille de calcul
    log_write("getting BOM")
    try:
        spsheet = FreeCAD.ActiveDocument.getObject("BOM")
        if spsheet == None:
            log_write("spsheet = None")
            print("ERROR: Aucun objet nommé 'BOM' trouvé dans le document actif. Assurez-vous qu'une feuille de calcul nommée 'BOM' existe.\n")

            return
    except Exception:
        print("ERROR: Aucun objet nommé 'BOM' trouvé dans le document actif. Assurez-vous qu'une feuille de calcul nommée 'BOM' existe.\n")

        return

    # 2. Suppression des objets calepinés précédents dans le document actif
    log_write("deleting nest objects with NESTED_OBJECT_SUFFIX")
    for o in [ob for ob in FreeCAD.ActiveDocument.Objects if NESTED_OBJECT_SUFFIX in ob.Label]:
        if hasattr(o,"Shape"):
            FreeCAD.ActiveDocument.removeObject(o.Name)

    # 4. Détermination de la dernière ligne
    log_write("find_last_row of BOM")
    last_data_row = find_last_row(spsheet)

    if last_data_row < 2:
        print("No data found in the BOM spreadsheet (starts from row 2).\n")

        return

    # 5. Importation des objets à calepiner
    log_write("Importation des objets à calepiner")
    Obj2Nest = []
    for cell in range(2, last_data_row + 1):
        objs = import_object_from_spreadsheat(spsheet, COLUMNS, cell)
        if objs:
            Obj2Nest.extend(objs)

    if not Obj2Nest:
        print("No objects to nest found in the BOM after processing.\n")

        return

    print(f"Found {len(Obj2Nest)} objects to nest.")

    # 6. CHARGEMENT DYNAMIQUE DES PANNEAUX
    log_write("chargement des panneaux du fichier config")
    monDoc = FreeCAD.ActiveDocument
    PROPERTIES = ("nom_aggr", "nom", "longueur", "largeur", "epaisseur",
            "raf_longueur", "raf_largeur", "couleur")


    CONFIG_FILENAME = "panneaux_config.txt"
    chemin_fichier = os.path.join(FreeCAD.getUserMacroDir(), CONFIG_FILENAME)
    if os.path.exists(chemin_fichier):
        try:
            with open(chemin_fichier, 'r') as f:
                lines = f.readlines()

            if lines and lines[0].strip() == ";".join(PROPERTIES):
                lines = lines[1:]

            for line in lines:
                line = line.strip()
                if not line: continue

                values = line.split(";")
                valeurs = []
                for val in values:
                    try:
                        valeurs.append(float(val))
                    except:
                        valeurs.append(val)

                if len(valeurs) >= 7:
                    WOOD_PANELS[valeurs[0]] = (valeurs[1], valeurs[2], valeurs[3], valeurs[4], valeurs[5], valeurs[6])
            print(f"WOOD_PANELS mis à jour depuis {CONFIG_FILENAME}.")
        except Exception as e:
            print(f"Erreur lors du chargement du fichier de configuration: {e}.\n")

    log_write("chargement des panneaux du document")
    try:
        liste_panneaux = monDoc.getObjectsByLabel("Liste panneaux")[0]
        string_list = getattr(liste_panneaux, "liste_panneaux")
        if string_list and string_list[0] == ";".join(PROPERTIES):
            string_list = string_list[1:]

        print(f"string_list = {string_list}")
        WOOD_PANELS = {}
        for line in string_list:
            values = line.split(";")
            valeurs = []
            for val in values:
                try:
                    valeurs.append(float(val))
                except:
                    valeurs.append(val)
            if len(valeurs) >= 7:
                # print(f"valeurs = {valeurs}")
                WOOD_PANELS[valeurs[0]] = (valeurs[1], valeurs[2], valeurs[3], valeurs[4], valeurs[5], valeurs[6])
                # print(f"WOOD_PANELS line {valeurs[0]} = {WOOD_PANELS[valeurs[0]]}")
        print(f"WOOD_PANELS mis à jour depuis 'Liste panneaux'.")
    except Exception as e:
        print(f"Erreur lors de la copie de la liste de panneaux du document: {e}.\n")
        pass

    # 7. Préparation des données pour la GUI
    log_write("préparation des données pour la boite de dialogue")
    unique_parts_data = {}
    for o in Obj2Nest:
        key = o.label.rsplit(' ', 1)[0]
        if key not in unique_parts_data:
            unique_parts_data[key] = {
                'label': key,
                'quantity': 0,
                'material': o.material,
            }
        unique_parts_data[key]['quantity'] += 1

    obj2nest_data_for_dialog = list(unique_parts_data.values())

    # 8. APPEL DE L'INTERFACE GRAPHIQUE
    log_write("ouverture de la boite de dialogue")
    dialog = NestingDialog(obj2nest_data_for_dialog, WOOD_PANELS)
    if dialog.exec_():
        selected_nesting_types = dialog.selected_nesting_types
        selected_obj_sort_types = dialog.selected_obj_sort_types

        if not selected_nesting_types or not selected_obj_sort_types:
            print("ERROR: Veuillez sélectionner au moins un Type de Calepinage et un Type de Tri des Objets.\n")

            return

        mat_list = sorted(list(set([o.material for o in Obj2Nest])))

        if mat_list:
            nest_solutions = []

            # CRÉATION DU NOUVEAU DOCUMENT POUR LES RÉSULTATS
            new_doc_name = "NestingResults_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            new_doc = FreeCAD.newDocument(new_doc_name)
            FreeCADGui.setActiveDocument(new_doc.Name)
            container = new_doc.addObject('App::Part', "NestingSolutions")

            starttime_nest = datetime.now()

            for mat in mat_list:
                print(f"Material {mat}:")
                p = Panel(mat)

                try:
                    panel_data = WOOD_PANELS[mat]
                    p.length = panel_data[1]
                    p.width = panel_data[2]
                    p.height = panel_data[3]
                    p.refreshCut_x = panel_data[4]
                    p.refreshCut_y = panel_data[5]
                    p.update_area()
                except KeyError:
                    print(f"WARNING: Panel definition for material '{mat}' not found. Skipping.")
                    continue

                nest_solutions_mat = []

                # BOUCLES DYNAMIQUES IMBRIQUÉES
                for nesting_type in selected_nesting_types:
                    for obj_sort_type in selected_obj_sort_types:
                        print(f"  > Strategy: {nesting_type} / {obj_sort_type}")

                        list_o_mat = [o.copy() for o in Obj2Nest if o.material == mat]
                        n = Nest([], list_o_mat)

                        i=0
                        while n.objects and i<= 100:
                            new_panel = p.copy()
                            n.panels.append(new_panel)
                            n.optimize(n.panels[i], nesting_type, obj_sort_type)

                            if len(n.panels[i].objects) == 0:
                                del n.panels[i]
                                break
                            i += 1

                        if n.panels and len(n.panels[0].objects) > 0:
                            nest_solutions_mat.append([n, len(n.panels), f"{nesting_type} - {obj_sort_type}"])
                        n = None

                print(f"Material {mat} nesting ended after {datetime.now() - starttime_nest}")

                # Sélection de la meilleure solution
                if nest_solutions_mat:
                    nest_solutions_mat.sort(key=lambda s: s[1])
                    best_solution = nest_solutions_mat[0]
                    print(f"Best solution for material {mat} uses {best_solution[1]} panels with type {best_solution[2]}")
                    nest_solutions.append(best_solution)

            # 9. Dessin de la meilleure solution dans le nouveau document
            starttime = datetime.now()

            current_YY_offset = 0
            for nest_sol in nest_solutions:
                print(f"Drawing solution for {nest_sol[0].panels[0].material}: Type {nest_sol[2]}")
                nest_sol[0].draw_nested_objects(current_YY_offset, container)

                # Calculer le Y d'offset pour le prochain matériau
                max_y_panel = 0
                for p in nest_sol[0].panels:
                    max_y_panel = max(max_y_panel, p.width)
                current_YY_offset += max_y_panel + 300

            print(f"Drawing step ended after {datetime.now()-starttime}")

            # 10. Vérification des objets non calepinés
            nested_obj = []
            for nest_sol in nest_solutions:
                print(f"liste des objects des panneaux {nest_sol[0].panels[0].material}:")
                nb = 0
                for p in nest_sol[0].panels:
                    nb += len(p.objects)
                    i=1
                    for o in p.objects:
                        nested_obj.append(o.label)
                        nested_obj[-1] = nested_obj[-1].replace(NESTED_OBJECT_SUFFIX,"")
                        print(f"objet: {nested_obj[-1]}")
                        i+=1
                    print(f"Nombre d'objets calepinés: {nb} dans le panneau {i}")

            nested_labels_set = set(nested_obj)
            not_nested_obj = [o for o in Obj2Nest if o.label not in nested_labels_set]

            if not_nested_obj:
                print(f"❌ {len(not_nested_obj)} objets non calepinés: ")
                for o in not_nested_obj:
                    print(f"Object: {o.label}")
            else:
                print("✅ Tous les objets ont été calepinés")

            # FreeCAD.Gui.updateGui()
            # FreeCADGui.SendMsgToActiveView("ViewFit")
            FreeCADGui.ActiveDocument.ActiveView.fitAll()
            msg_console("ActiveView fitAll")
        else:
            print("No material defined in BOM spreadsheet")
    else:
        print("Nesting cancelled by user.")

Main()
