# -*- coding: utf-8 -*-
# Add the following custom properties to selected objects

# Type, Name, Group, Description, Value
USER_PROPERTIES = (
                    ("App::PropertyBool", "BOM_destination", "UserProp", "Property to filter objects for BOM", True),
                    ("App::PropertyEnumeration", "BOM_mat", "UserProp", "Material name", []),
                    ("App::PropertyInteger", "BOM_quantity", "UserProp", "Part quantity to consider in BOM", 1),
                    ("App::PropertyBool", "Nesting", "UserProp", "Property to filter objects to nest", True),
                    ("App::PropertyBool", "Nest_Allow_Rotation", "UserProp", "Allow rotation in nesting computation", True),
                    ("App::PropertyEnumeration", "Nest_Thickness", "UserProp", "The thickness to use for nesting", ["XLength", "YLength", "ZLength"]),
                    ("App::PropertyEnumeration", "Nest_grain", "UserProp", "The orientation to use for nesting", ["XLength", "YLength", "ZLength"]),
                    )
PROP_HEADERS = {
                "type" : 0,
                "name" : 1,
                "group" : 2,
                "description" : 3,
                "value" : 4
                }

DEFAULT_PANELS_LIST = (
                        "Mela 2800x2070x19",
                        "Mela 2800x2070x8",
                        "Tab 2800x600x19",
                        "Valchromat 2440x1830x19",
                        "Latte chene 2500x1220x19",
                        "CTP chassis 2500x100x22",
                      )
DEFAULT_MAT = 0

print('Add BOM property')
obj = FreeCADGui.Selection.getSelection()

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

# --- 1. Définition du Panneau ---

class Panneau:
    PROPERTIES = [
        "nom_aggr", "nom", "longueur", "largeur", "epaisseur",
        "raf_longueur", "raf_largeur", "couleur"
    ]

    TYPES = {
        "nom_aggr": str, "nom": str, "couleur": str,
        "longueur": float, "largeur": float, "epaisseur": float,
        "raf_longueur": float, "raf_largeur": float
    }

    def __init__(self, data=None):
        # Mela 2800x2070x19;Mela;2800.0;2070.0;19.0;10.0;10.0;#cccccc
        self.nom_aggr = "Mela 2800x2070x19"
        self.nom = "Mela"
        self.longueur = 2800.0
        self.largeur = 2070.0
        self.epaisseur = 19.0
        self.raf_longueur = 10.0
        self.raf_largeur = 10.0
        self.couleur = "#cccccc"

        if isinstance(data, dict):
            self.from_dict(data)
        elif isinstance(data, str):
            self.from_string(data)

        self.rebuild_nom_aggr()

    def rebuild_nom_aggr(self):
        """Reconstruit le nom agrégé à partir des dimensions actuelles (arrondies)."""
        self.nom_aggr = (
            f"{self.nom} "
            f"{int(round(self.longueur))}x"
            f"{int(round(self.largeur))}x"
            f"{int(round(self.epaisseur))}"
        )

    def to_dict(self):
        return {prop: getattr(self, prop) for prop in self.PROPERTIES}

    def to_string(self):
        data_dict = self.to_dict()
        str_values = [str(data_dict[prop]) for prop in self.PROPERTIES]
        return ";".join(str_values)

    def from_dict(self, data):
        for prop, val in data.items():
            if prop in self.PROPERTIES:
                try:
                    setattr(self, prop, self.TYPES[prop](val))
                except ValueError:
                    FreeCAD.Console.PrintWarning(f"Valeur '{val}' non valide pour la propriété '{prop}' du panneau.\n")

    def from_string(self, line):
        values = line.split(";")
        if len(values) != len(self.PROPERTIES):
            FreeCAD.Console.PrintWarning(f"Ligne de panneau format incorrect: {line}\n")
            return

        data_dict = dict(zip(self.PROPERTIES, values))
        self.from_dict(data_dict)
        self.rebuild_nom_aggr()

# --- 4. Boîte de Dialogue Principale ---

class Panneaux:

    CONFIG_FILENAME = "panneaux_config.txt"
    PROP_NAME = "liste_panneaux"
    OBJECT_NAME = "Liste panneaux"
    DIMENSION_COLUMNS = [2, 3, 4, 5, 6]
    COLOR_COLUMN = 7

    def __init__(self):

        self.config_filepath = os.path.join(FreeCAD.getUserMacroDir(), self.CONFIG_FILENAME)

        self.config_panneaux = []
        self.doc_panneaux = []
        self._load_config_file()

        self._load_doc_data()


    def _load_config_file(self):
        self.config_panneaux.clear()

        if not os.path.exists(self.config_filepath):
            FreeCAD.Console.PrintMessage(f"Fichier de configuration non trouvé: {self.config_filepath}. Un nouveau sera créé à la sauvegarde.\n")
            self.config_panneaux.append(Panneau())
            return

        with open(self.config_filepath, 'r') as f:
            lines = f.readlines()

        if lines and lines[0].strip() == ";".join(Panneau.PROPERTIES):
            lines = lines[1:]

        for line in lines:
            line = line.strip()
            if line:
                self.config_panneaux.append(Panneau(line))
        if not self.config_panneaux:
             self.config_panneaux.append(Panneau())

    def _get_doc_object(self):
        if FreeCAD.ActiveDocument is None:
            return None

        for obj in FreeCAD.ActiveDocument.Objects:
            if obj.Label == self.OBJECT_NAME and hasattr(obj, self.PROP_NAME):
                return obj
        return None

    def _load_doc_data(self):
        self.doc_panneaux.clear()
        doc_obj = self._get_doc_object()

        if doc_obj is None:
            print("Statut: Objet **'Liste panneaux'** introuvable dans le document.")
            return

        print(f"Statut: Chargé depuis l'objet {doc_obj.Name} (Label: '{self.OBJECT_NAME}'). Type: {doc_obj.TypeId.split('::')[-1]}")

        string_list = getattr(doc_obj, self.PROP_NAME)

        if string_list and string_list[0] == ";".join(Panneau.PROPERTIES):
            string_list = string_list[1:]

        for line in string_list:
            self.doc_panneaux.append(Panneau(line))

        if not self.doc_panneaux:
             self.doc_panneaux.append(Panneau())


    def _create_doc_object(self):
        object_type = "App::VarSet"
        type_label = "VarSet"

        try:
            obj = FreeCAD.ActiveDocument.addObject(object_type, "PanneauManager")
            obj.Label = self.OBJECT_NAME

            obj.addProperty("App::PropertyStringList", self.PROP_NAME, "Panneaux", "Liste des définitions de panneaux")

            FreeCAD.ActiveDocument.recompute()
            print(f"Création Réussie, Objet {self.OBJECT_NAME} de type {type_label} créé.")

            self._load_doc_data()

        except Exception as e:
            print(f"Erreur de Création, Impossible de créer l'objet {type_label} dans le document: {e}")

    def _save_doc_data(self):
        doc_obj = self._get_doc_object()

        if doc_obj is None:
            print(f"Erreur, L'objet 'Liste panneaux' est introuvable. Créez-le d'abord.")
            return

        try:
            string_list = [";".join(Panneau.PROPERTIES)]
            string_list.extend([panneau.to_string() for panneau in self.doc_panneaux])

            setattr(doc_obj, self.PROP_NAME, string_list)

            FreeCAD.ActiveDocument.recompute()

            print(f"Sauvegarde Document Réussie, La liste de panneaux a été sauvegardée dans la propriété StringList de **'{self.OBJECT_NAME}'**.")
        except Exception as e:
            print(f"Erreur de Sauvegarde Document, Impossible de sauvegarder dans le document: {e}")

    def _copy_selected_to_doc(self):
        indexes = []
        for i in range(len(self.config_panneaux)):
            aggr = getattr(self.config_panneaux[i], "nom_aggr")
            if aggr in DEFAULT_PANELS_LIST:
                print(f"index {i}, nom_aggr {aggr}")
                indexes.append(i)
        if not indexes:
            return

        for index in indexes:
            panneau_to_copy = self.config_panneaux[index]
            self.doc_panneaux.append(Panneau(panneau_to_copy.to_dict()))

    def _update_bom_materials(self):
        if FreeCAD.ActiveDocument is None:
            print(f"Erreur, Veuillez ouvrir un document FreeCAD d'abord.")
            return

        # 1. Préparer la nouvelle liste d'énumération
        aggregated_names = self.doc_model.get_aggregated_names()
        bom_enum_list = sorted(list(set(aggregated_names)))

        default_panneau_name = Panneau().nom_aggr
        valid_bom_list = [name for name in bom_enum_list if name != default_panneau_name]

        if not valid_bom_list:
             print(f"Avertissement, La liste des panneaux est vide. La propriété BOM_mat ne sera pas mise à jour sur les objets.")
             return

        # 2. Parcourir tous les objets dans le document
        doc = FreeCAD.ActiveDocument
        updated_count = 0
        changed_value_count = 0

        for obj in doc.Objects:
            try:
                if hasattr(obj, "BOM_mat"):

                    old_value = getattr(obj, 'BOM_mat')

                    # --- ÉTAPE A : Mettre à jour la liste des options d'énumération ---
                    setattr(obj, 'BOM_mat', valid_bom_list)

                    # --- ÉTAPE B : Persistance/Sélection de la valeur ---

                    if old_value not in valid_bom_list:
                        closest_match = find_closest_match(old_value, valid_bom_list)

                        # Mettre à jour l'attribut avec la nouvelle valeur
                        setattr(obj, 'BOM_mat', closest_match)
                        changed_value_count += 1

                    updated_count += 1

            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Impossible de mettre à jour BOM_mat pour l'objet {obj.Label}: {e}\n")

        # 3. Informer l'utilisateur
        doc.recompute()

        summary_message = (
            f"La liste d'énumération de la propriété **'BOM_mat'** a été mise à jour sur **{updated_count} objets** "
            f"avec les {len(valid_bom_list)} noms de panneaux.\n"
            f"**{changed_value_count} valeurs** ont été modifiées car elles n'existaient plus (proche correspondance ou défaut)."
        )

        if updated_count > 0:
            print(f"Mise à Jour Réussie {summary_message}")
        else:
            print(f"Mise à Jour, Aucun objet possédant la propriété 'BOM_mat' n'a été trouvé ou mis à jour.")

    def _apply_colors_to_objects(self):
        if FreeCAD.ActiveDocument is None:
            print(f"Erreur, Veuillez ouvrir un document FreeCAD d'abord.")
            return

        # 1. Créer un dictionnaire de correspondance Nom Agrégé -> Couleur (RGB normalisé)
        color_map = {}
        for panneau in self.doc_panneaux:
            # Conversion de la couleur HTML (#RRGGBB) en tuple RGB normalisé [R, G, B] (0.0 à 1.0)
            try:
                # Utiliser QColor pour la conversion
                qcolor = hex_to_rgb(panneau.couleur)
                r_norm = qcolor[0] / 255.0
                g_norm = qcolor[1] / 255.0
                b_norm = qcolor[2] / 255.0
                # L'alpha est souvent inclus dans FreeCAD, mettons-le à 0 (opaque)
                color_map[panneau.nom_aggr] = (r_norm, g_norm, b_norm, 0.0)
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Erreur de conversion de couleur pour {panneau.nom_aggr}: {e}\n")

        if not color_map:
            print(f"Avertissement, Aucune couleur de panneau valide à appliquer.")
            return

        # 2. Parcourir les objets
        doc = FreeCAD.ActiveDocument
        colored_count = 0

        for obj in doc.Objects:
            try:
                if hasattr(obj, "BOM_mat"):
                    material_name = getattr(obj, 'BOM_mat')

                    if material_name in color_map:
                        target_color = color_map[material_name]

                        # Déterminer l'objet cible (l'objet lui-même ou son Body parent)
                        target_object = obj

                        # Vérifier le parent immédiat
                        if obj.InList:
                            parent = obj.InList[0]
                            # Le typeId pour PartDesign::Body est 'PartDesign::Body'
                            if parent.TypeId == 'PartDesign::Body':
                                target_object = parent

                        # Appliquer la couleur si l'objet cible a un ViewObject et la propriété 'ShapeColor'
                        if hasattr(target_object, 'ViewObject') and hasattr(target_object.ViewObject, 'ShapeColor'):

                            target_object.ViewObject.ShapeColor = target_color
                            colored_count += 1

            except Exception as e:
                FreeCAD.Console.PrintError(f"Erreur lors de l'application de la couleur à {obj.Label}: {e}\n")

        # 3. Informer l'utilisateur

        # --- CORRECTION DE LA LIGNE D'ERREUR : Utiliser FreeCADGui.updateGui() ---
        try:
            FreeCADGui.updateGui()
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"Erreur de rafraîchissement de l'interface graphique: {e}\n")
        # -------------------------------------------------------------------

        if colored_count > 0:
            print(f"Couleurs Appliquées, La couleur du panneau a été appliquée à **{colored_count} objets** ou leurs Bodies parents.")
        else:
            print(f"Couleurs, Aucun objet avec la propriété 'BOM_mat' correspondant à un panneau n'a été trouvé ou mis à jour.")


Panx = Panneaux()

doc_obj = Panx._get_doc_object()
if doc_obj is None:
    Panx._create_doc_object()
    Panx._copy_selected_to_doc()
    Panx.doc_panneaux.pop(0)
    Panx._save_doc_data()

WOOD_MATERIALS = []
for panel in Panx.doc_panneaux:
    WOOD_MATERIALS.append(panel.nom_aggr)

if len(obj)!=0:
   print('nombre objets: ', len(obj))
   for o in obj:
      if hasattr(o,"Shape"): # and obj.Shape.Solids:
#         print('object has shape')
         for prop in USER_PROPERTIES:
             prop_name = prop[PROP_HEADERS["name"]]
             if hasattr(o, prop_name):
                 if prop_name == "BOM_destination":
                    setattr(o, prop_name, prop[PROP_HEADERS["value"]])
             else:
                 o.addProperty(prop[PROP_HEADERS["type"]], prop_name, prop[PROP_HEADERS["group"]], prop[PROP_HEADERS["description"]])
                 setattr(o, prop_name, prop[PROP_HEADERS["value"]])
                 if prop_name == "BOM_mat":
                     o.BOM_mat = WOOD_MATERIALS
                     o.BOM_mat = WOOD_MATERIALS[DEFAULT_MAT]
                 elif prop_name == "Nest_Thickness":
                     min_length = ["XLength", o.Shape.BoundBox.XLength]
                     if o.Shape.BoundBox.YLength < min_length[1]: min_length = ["YLength", o.Shape.BoundBox.YLength]
                     if o.Shape.BoundBox.ZLength < min_length[1]: min_length = ["ZLength", o.Shape.BoundBox.ZLength]
                     o.Nest_Thickness = min_length[0]
                 elif prop_name == "Nest_grain":
                     if "porte" in o.Label.lower():
                         max_length = "ZLength"
                     elif "tiroir" in o.Label.lower():
                         max_length = "XLength"
                     else:
                         max_length = "XLength" if o.Shape.BoundBox.XLength > o.Shape.BoundBox.ZLength else "ZLength"
                     ThicknessToGrain = {
                                        "XLength": "ZLength",
                                        "YLength": max_length,
                                        "ZLength": "XLength",
                                        }
                     o.Nest_grain = ThicknessToGrain[o.Nest_Thickness]

Panx._apply_colors_to_objects()
