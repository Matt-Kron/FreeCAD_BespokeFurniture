import json
import os
import sys
import FreeCAD as App
import Part

def sanitize_name(name):
    """
    Assure que le nom d'objet FreeCAD ne contient que des caractères autorisés.
    """
    clean = "".join(c if c.isalnum() else "_" for c in name)
    if clean and clean[0].isdigit():
        clean = "obj_" + clean
    return clean or "unnamed"

def run():
    macro_dir = App.getUserMacroDir()
    json_path = os.path.join(macro_dir, "meuble_simplifie.json")

    if not os.path.exists(json_path):
        App.Console.PrintError(f"[ERREUR] Fichier JSON introuvable : {json_path}\n")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        App.Console.PrintError(f"[ERREUR] Échec de la lecture du fichier JSON: {e}\n")
        return

    # Création d'un nouveau document FreeCAD s'il n'est pas déja ouvert
    doc_name = "MeubleSimplifieGeometrie"
    if doc_name in App.listDocuments().keys():
        doc = App.getDocument(doc_name)
    else:
        doc = App.newDocument(doc_name)
        App.Console.PrintMessage("Nouveau document 'MeubleSimplifieGeometrie' créé.\n")

    # Création du conteneur principal App::Part étiqueté "meuble simplifie"
    meuble_part_name = "MeubleSimplifie"
    meuble_part = doc.getObject(meuble_part_name)
    if not meuble_part:
        meuble_part = doc.addObject("App::Part", meuble_part_name)
        meuble_part.Label = "meuble simplifie"
        App.Console.PrintMessage("Conteneur App::Part 'meuble simplifie' créé.\n")

    # 1. Création des segments (sous forme de lignes Part)
    segments = data.get("segments", [])
    App.Console.PrintMessage(f"Création de {len(segments)} segments...\n")
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

            # Assurer un nom unique dans le document pour éviter les collisions
            unique_name = doc.getUniqueObjectName(internal_name)
            if unique_name != internal_name:
                doc.removeObject(internal_name)

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
        # Déterminer dynamiquement l'axe horizontal principal à partir des positions des alvéoles
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

            # Calcul du placement en centrant l'alvéole sur l'axe de profondeur
            if horiz_axis_idx == 0:  # X est l'axe horizontal, Y est l'axe de profondeur
                x_min = position[0]
                z_min = position[2]
                y_min = position[1] # - profondeur / 2.0

                dx = largeur
                dy = profondeur
                dz = hauteur
            else:  # Y est l'axe horizontal, X est l'axe de profondeur
                y_min = position[1]
                z_min = position[2]
                x_min = position[0] # - profondeur / 2.0

                dx = profondeur
                dy = largeur
                dz = hauteur

            try:
                internal_name = sanitize_name(f"Alveole_{cell_id}")
                unique_name = doc.getUniqueObjectName(internal_name)
                if unique_name != internal_name:
                    doc.removeObject(internal_name)

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
                        view_obj.Transparency = 70             # Transparence à 70% pour voir à travers
                        view_obj.LineColor = (0.1, 0.4, 0.8)   # Bordures bleues plus soutenues
            except Exception as e:
                App.Console.PrintError(f"Erreur lors de la création de l'alvéole '{cell_id}': {e}\n")

    # Recalculer le document pour dessiner toutes les formes géométriques
    doc.recompute()
    App.Console.PrintMessage("Recomputation du document terminée.\n")

    # Ajuster la caméra pour cadrer tout le meuble
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.SendMsgToActiveView("ViewFit")
        App.Console.PrintMessage("Vue 3D cadrée sur le meuble.\n")


if __name__ == "__main__":
    run()
