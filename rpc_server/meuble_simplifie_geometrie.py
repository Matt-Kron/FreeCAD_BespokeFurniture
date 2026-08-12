import json
import sys
import FreeCAD as App
import Part

# Importer la fonction de mise à jour depuis extract_segments_alveoles
from .extract_segments_alveoles import update_meuble_simplifie, JSON_CONTAINER_NAME


def sanitize_name(name):
    """
    Assure que le nom d'objet FreeCAD ne contient que des caractères autorisés.
    """
    clean = "".join(c if c.isalnum() else "_" for c in name)
    if clean and clean[0].isdigit():
        clean = "obj_" + clean
    return clean or "unnamed"


def get_json_data_from_container(doc):
    """
    Récupère les données JSON depuis l'objet App::Part conteneur.

    Args:
        doc: Document FreeCAD

    Returns:
        dict: Les données JSON ou None si non trouvés
    """
    # Trouver l'objet conteneur
    json_container = None
    for obj in doc.Objects:
        if obj.Name == JSON_CONTAINER_NAME and obj.isDerivedFrom("App::Part"):
            json_container = obj
            break

    if not json_container:
        App.Console.PrintError(f"[ERREUR] Objet '{JSON_CONTAINER_NAME}' non trouvé dans le document.\n")
        return None

    if not hasattr(json_container, "JSONData") or not json_container.JSONData:
        App.Console.PrintError(f"[ERREUR] Aucune donnée JSON dans l'objet '{JSON_CONTAINER_NAME}'.\n")
        return None

    try:
        return json.loads(json_container.JSONData)
    except json.JSONDecodeError as e:
        App.Console.PrintError(f"[ERREUR] Échec du décodage JSON: {e}\n")
        return None


def create_geometry_in_container(doc):
    """
    Crée les géométries (segments et alvéoles) dans l'objet App::Part du document.

    Args:
        doc: Document FreeCAD contenant le JSON
    """
    # Récupérer les données
    data = get_json_data_from_container(doc)
    if not data:
        return False

    # Trouver le conteneur App::Part "meuble_simplifie"
    meuble_part = None
    for obj in doc.Objects:
        if obj.Name == JSON_CONTAINER_NAME and obj.isDerivedFrom("App::Part"):
            meuble_part = obj
            break

    if not meuble_part:
        App.Console.PrintError(f"[ERREUR] Objet conteneur '{JSON_CONTAINER_NAME}' non trouvé.\n")
        return False

    # 1. Création des segments (sous forme de lignes Part)
    segments = data.get("segments", [])
    App.Console.PrintMessage(f"Création de {len(segments)} segments...\n")

    # Supprimer les anciennes géométries et annotations
    for obj in meuble_part.Group:
        if obj.Name.startswith("Segment_") or obj.Name.startswith("Alveole_") or obj.Name.startswith("Annotation_Alveole_"):
            doc.removeObject(obj.Name)

    for s in segments:
        s_nom = s.get("nom", "Segment")
        debut = s.get("debut")
        fin = s.get("fin")

        if not debut or not fin:
            continue

        p1 = App.Vector(debut[0], debut[1], debut[2])
        p2 = App.Vector(fin[0], fin[1], fin[2])

        try:
            line_shape = Part.makeLine(p1, p2)
            internal_name = sanitize_name(f"Segment_{s_nom}")

            # Assurer un nom unique dans le document
            unique_name = doc.getUniqueObjectName(internal_name)
            if unique_name != internal_name:
                # Supprimer l'ancien objet s'il existe
                try:
                    doc.removeObject(internal_name)
                except:
                    pass

            line_obj = doc.addObject("Part::Feature", internal_name)
            line_obj.Shape = line_shape
            line_obj.Label = s_nom

            # Ranger l'objet dans le App::Part
            meuble_part.addObject(line_obj)

            # Style visuel (si l'interface graphique FreeCAD est active)
            if App.GuiUp:
                import FreeCADGui as Gui
                view_obj = line_obj.ViewObject
                if view_obj:
                    view_obj.LineColor = (1.0, 0.0, 0.0)  # Rouge vif
                    view_obj.LineWidth = 3.0              # Épaisseur des lignes
        except Exception as e:
            App.Console.PrintError(f"Erreur lors de la création du segment '{s_nom}': {e}\n")

    # 2. Création des alvéoles (sous forme de cubes Part)
    alveoles = data.get("alveoles", [])
    App.Console.PrintMessage(f"Création de {len(alveoles)} alvéoles...\n")

    if alveoles:
        # Déterminer dynamiquement l'axe horizontal principal
        xs = [cell["position"][0] for cell in alveoles if "position" in cell]
        ys = [cell["position"][1] for cell in alveoles if "position" in cell]

        range_x = max(xs) - min(xs) if xs else 0.0
        range_y = max(ys) - min(ys) if ys else 0.0

        if range_x >= range_y:
            horiz_axis_idx = 0  # X est l'axe horizontal, Y est l'axe de profondeur
            depth_axis_idx = 1
            App.Console.PrintMessage("Axe horizontal détecté pour les alvéoles : X\n")
        else:
            horiz_axis_idx = 1  # Y est l'axe horizontal, X est l'axe de profondeur
            depth_axis_idx = 0
            App.Console.PrintMessage("Axe horizontal détecté pour les alvéoles : Y\n")

        for cell in alveoles:
            cell_id = cell.get("id", "A")
            position = cell.get("position")
            largeur = cell.get("largeur", 0.0)
            profondeur = cell.get("profondeur", 300.0)
            hauteur = cell.get("hauteur", 0.0)

            if not position:
                continue

            # Si la profondeur est nulle ou très faible, on applique une valeur de secours
            if profondeur < 1.0:
                profondeur = 300.0

            # Calcul du placement
            if horiz_axis_idx == 0:  # X est l'axe horizontal, Y est l'axe de profondeur
                x_min = position[0]
                z_min = position[2]
                y_min = position[1]

                dx = largeur
                dy = profondeur
                dz = hauteur
            else:  # Y est l'axe horizontal, X est l'axe de profondeur
                y_min = position[1]
                z_min = position[2]
                x_min = position[0]

                dx = profondeur
                dy = largeur
                dz = hauteur

            try:
                internal_name = sanitize_name(f"Alveole_{cell_id}")
                unique_name = doc.getUniqueObjectName(internal_name)
                if unique_name != internal_name:
                    # Supprimer l'ancien objet s'il existe
                    try:
                        doc.removeObject(internal_name)
                    except:
                        pass

                box_obj = doc.addObject("Part::Box", internal_name)
                box_obj.Length = dx
                box_obj.Width = dy
                box_obj.Height = dz
                box_obj.Placement.Base = App.Vector(x_min, y_min, z_min)
                box_obj.Label = f"Alvéole {cell_id}"

                # Ranger l'objet dans le App::Part
                meuble_part.addObject(box_obj)

                # Style visuel (si l'interface graphique FreeCAD est active)
                if App.GuiUp:
                    import FreeCADGui as Gui
                    view_obj = box_obj.ViewObject
                    if view_obj:
                        view_obj.ShapeColor = (0.2, 0.6, 1.0)  # Bleu ciel
                        view_obj.Transparency = 70             # Transparence à 70%
                        view_obj.LineColor = (0.1, 0.4, 0.8)   # Bordures bleues
            except Exception as e:
                App.Console.PrintError(f"Erreur lors de la création de l'alvéole '{cell_id}': {e}\n")

    # Recalculer le document
    doc.recompute()
    App.Console.PrintMessage("Recomputation du document terminée.\n")

    # Ajuster la caméra pour cadrer tout le meuble
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.SendMsgToActiveView("ViewFit")
        App.Console.PrintMessage("Vue 3D cadrée sur le meuble.\n")

    return True


def run():
    """
    Fonction principale : analyse le document actif, crée/met à jour le JSON,
    puis crée les géométries dans le même document.
    """
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("[ERREUR] Aucun document actif.\n")
        return

    App.Console.PrintMessage("=== Mise à jour du meuble simplifié ===\n")

    # Étape 1 : Mettre à jour les données JSON
    if not update_meuble_simplifie(doc):
        App.Console.PrintError("[ERREUR] Échec de la mise à jour des alvéoles.\n")
        return

    # Étape 2 : Créer les géométries dans le même document
    if not create_geometry_in_container(doc):
        App.Console.PrintError("[ERREUR] Échec de la création des géométries.\n")
        return

    App.Console.PrintMessage("=== Terminé ===\n")


if __name__ == "__main__":
    run()
