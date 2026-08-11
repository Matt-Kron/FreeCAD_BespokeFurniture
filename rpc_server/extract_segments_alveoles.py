import json
import os
import sys
import FreeCAD as App

# S'assurer que le chemin des macros est présent dans sys.path pour importer librairie.py
macro_dir = App.getUserMacroDir()

from ..lib_menuiserie import get_parent_part


def group_coordinates(coords, tolerance):
    """
    Regroupe des coordonnées proches (selon une tolérance) pour éviter
    les doublons dus aux approximations de calcul flottant en CAO.
    """
    if not coords:
        return []
    coords = sorted(coords)
    grouped = []
    current_group = [coords[0]]
    for c in coords[1:]:
        if c - current_group[-1] <= tolerance:
            current_group.append(c)
        else:
            grouped.append(sum(current_group) / len(current_group))
            current_group = [c]
    grouped.append(sum(current_group) / len(current_group))
    return grouped


def covers_interval(segments_list, coord, start, end, tolerance):
    """
    Vérifie si une bordure d'intervalle [start, end] à la coordonnée `coord`
    est entièrement couverte par un ou plusieurs segments colinéaires.
    """
    intervals = []
    for c, s_min, s_max in segments_list:
        if abs(c - coord) <= tolerance:
            intervals.append((s_min, s_max))

    if not intervals:
        return False

    # Fusionner les segments qui se chevauchent ou se touchent
    intervals.sort()
    merged = []
    for s_min, s_max in intervals:
        if not merged:
            merged.append([s_min, s_max])
        else:
            prev_min, prev_max = merged[-1]
            if s_min <= prev_max + tolerance:
                merged[-1][1] = max(prev_max, s_max)
            else:
                merged.append([s_min, s_max])

    # Vérifier si un des segments fusionnés couvre la totalité de la plage demandée
    for m_min, m_max in merged:
        if m_min <= start + tolerance and m_max >= end - tolerance:
            return True
    return False


def has_horizontal_crossing(v1, v2, u1, u2, horiz_segs, tolerance):
    """
    Vérifie si une étagère horizontale traverse l'intérieur de l'alvéole [u1, u2] x (v1, v2).
    """
    for v, u_min, u_max in horiz_segs:
        if v1 + tolerance < v < v2 - tolerance:
            # S'il y a intersection entre l'intervalle du panneau et la largeur de la cellule
            if max(u_min, u1) < min(u_max, u2) - tolerance:
                return True
    return False


def find_boundary_segment(segments_list, is_vertical, target_coord, range_start, range_end, horiz_axis_idx, vert_axis_idx, tolerance):
    """
    Trouve le nom du segment physique qui forme la frontière de l'alvéole
    en calculant le meilleur alignement géométrique et chevauchement.
    """
    best_seg = None
    max_overlap = -1.0
    best_dist = float('inf')

    for s in segments_list:
        if is_vertical and s["role"] != "vertical":
            continue
        if not is_vertical and s["role"] != "horizontal":
            continue

        u_start = s['debut'][horiz_axis_idx]
        v_start = s['debut'][vert_axis_idx]
        u_end = s['fin'][horiz_axis_idx]
        v_end = s['fin'][vert_axis_idx]

        if is_vertical:
            coord = u_start
            s_min = min(v_start, v_end)
            s_max = max(v_start, v_end)
        else:
            coord = v_start
            s_min = min(u_start, u_end)
            s_max = max(u_start, u_end)

        dist = abs(coord - target_coord)
        if dist <= tolerance:
            # Calcule la longueur de l'intersection avec la bordure de l'alvéole
            overlap = max(0.0, min(s_max, range_end) - max(s_min, range_start))
            if overlap > 0.1:
                # Priorité au segment le plus proche géométriquement, puis à celui qui chevauche le plus
                if dist < best_dist - 0.1:
                    best_dist = dist
                    max_overlap = overlap
                    best_seg = s
                elif abs(dist - best_dist) <= 0.1 and overlap > max_overlap:
                    max_overlap = overlap
                    best_seg = s

    return best_seg["nom"] if best_seg else None


def col_index_to_letter(index):
    """
    Convertit un index de colonne (0-based) en lettres (0 -> A, 25 -> Z, 26 -> AA, etc.)
    """
    letter = ""
    while index >= 0:
        letter = chr(65 + (index % 26)) + letter
        index = (index // 26) - 1
    return letter


def run():
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("Aucun document actif trouvé dans FreeCAD.\n")
        return

    App.Console.PrintMessage("=============================================\n")
    App.Console.PrintMessage("Macro : Analyse de Meuble et Déduction d'Alvéoles (Enrichi)\n")
    App.Console.PrintMessage("=============================================\n")

    # 1. Recherche de tous les AdditiveBox ou SubtractiveBox avec la propriété BOM_mat
    additive_boxes = []
    for obj in doc.Objects:
        is_box = obj.isDerivedFrom("PartDesign::AdditiveBox") or obj.isDerivedFrom("PartDesign::SubtractiveBox")
        if (is_box and hasattr(obj, "bspf_tag")) and "CS" in obj.bspf_tag:
            additive_boxes.append(obj)

    App.Console.PrintMessage(f"-> Trouvé {len(additive_boxes)} objets 'Box' avec la propriété 'bspf_tag'.\n")

    if not additive_boxes:
        App.Console.PrintWarning("Aucun AdditiveBox ou SubtractiveBox avec la propriété bspf_tag n'a été détecté.\n")
        return

    # 2. Extraction des segments des panneaux verticaux et horizontaux
    segments_list = []
    for obj in additive_boxes:
        label_lower = obj.Label.lower()

        # Filtres selon extract_role_dimensions.md
        is_vertical = any(term in label_lower for term in ['mt d', 'mt g', 'mt i', 'mt'])
        is_horizontal = any(term in label_lower for term in ['tv sup', 'tv inf', 'tv', 'traverse', 'tab', 'tablette'])

        if not (is_vertical or is_horizontal):
            continue

        child = obj
        parent_list = []
        parent_part = child.getParentGeoFeatureGroup()
        i=1
        # if parent_part: App.Console.PrintMessage(f"parent {i}, {parent_part.Label}\n")
        while parent_part and i<5:
            parent_list.append(parent_part)
            child = parent_part
            parent_part = child.getParentGeoFeatureGroup()
            i += 1
            # if parent_part: App.Console.PrintMessage(f"parent {i}, {parent_part.Label}\n")

        vec = App.Vector(0, 0, 0)
        # App.Console.PrintMessage(f"parent list {parent_list}\n")
        if parent_list:
            for parent_part in parent_list:
                vec = vec.add(parent_part.Placement.Base)
                # pos_x = parent_part.Placement.Base.x
                # pos_y = parent_part.Placement.Base.y
                # pos_z = parent_part.Placement.Base.z
                # App.Console.PrintMessage(f"parent {parent_part.Label}\n")
                # App.Console.PrintMessage(f"vec {vec}:.2f \n")
            pos_x = vec[0]
            pos_y = vec[1]
            pos_z = vec[2]
        else:
            pos_x = obj.Placement.Base.x
            pos_y = obj.Placement.Base.y
            pos_z = obj.Placement.Base.z

        bbox = obj.Shape.BoundBox
        largeur = bbox.XLength
        profondeur = bbox.YLength
        hauteur = bbox.ZLength

        if is_vertical:
            debut = [pos_x, pos_y, pos_z]
            fin = [pos_x, pos_y, pos_z + hauteur]
            role = "vertical"
        else:  # is_horizontal
            debut = [pos_x, pos_y, pos_z]
            fin = [pos_x + largeur, pos_y, pos_z]
            role = "horizontal"

        segments_list.append({
            "nom": obj.Label,
            "role": role,
            "debut": debut,
            "fin": fin,
            "largeur": largeur,
            "profondeur": profondeur,
            "hauteur": hauteur
        })

    App.Console.PrintMessage(f"-> Extraits {len(segments_list)} panneaux (montants verticaux et traverses horizontales).\n")
    if not segments_list:
        return

    # 3. Détection automatique de l'orientation du meuble (Axe horizontal = X ou Y ?)
    xs = [pt[0] for s in segments_list for pt in (s['debut'], s['fin'])]
    ys = [pt[1] for s in segments_list for pt in (s['debut'], s['fin'])]

    range_x = max(xs) - min(xs) if xs else 0.0
    range_y = max(ys) - min(ys) if ys else 0.0

    if range_x >= range_y:
        horiz_axis_idx = 0  # L'axe horizontal principal est X
        depth_axis_idx = 1  # L'axe de profondeur est Y
        axis_name = "X"
    else:
        horiz_axis_idx = 1  # L'axe horizontal principal est Y
        depth_axis_idx = 0  # L'axe de profondeur est X
        axis_name = "Y"
    vert_axis_idx = 2       # L'axe vertical est toujours Z

    App.Console.PrintMessage(f"-> Orientation CAO détectée : Axe horizontal = {axis_name} (Plage X = {range_x:.1f} mm, Plage Y = {range_y:.1f} mm)\n")

    # 4. Projection 2D (u, v) des segments
    # u = coordonnée horizontale (X ou Y selon orientation)
    # v = coordonnée verticale (Z)
    horiz_segs = [] # tuples (v, u_min, u_max)
    vert_segs = []  # tuples (u, v_min, v_max)

    for s in segments_list:
        u_start = s['debut'][horiz_axis_idx]
        v_start = s['debut'][vert_axis_idx]
        u_end = s['fin'][horiz_axis_idx]
        v_end = s['fin'][vert_axis_idx]

        if s['role'] == 'vertical':
            u = u_start
            v_min = min(v_start, v_end)
            v_max = max(v_start, v_end)
            vert_segs.append((u, v_min, v_max))
        elif s['role'] == 'horizontal':
            v = v_start
            u_min = min(u_start, u_end)
            u_max = max(u_start, u_end)
            horiz_segs.append((v, u_min, u_max))

    # Calcul de la profondeur moyenne de positionnement pour reconstruire le 3D
    depth_coords = [s['debut'][depth_axis_idx] for s in segments_list] + [s['fin'][depth_axis_idx] for s in segments_list]
    w_avg = sum(depth_coords) / len(depth_coords) if depth_coords else 0.0

    # 5. Extraction des découpes uniques de coordonnées candidates pour la grille
    u_coords = []
    for u, v_min, v_max in vert_segs:
        u_coords.append(u)
    for v, u_min, u_max in horiz_segs:
        u_coords.append(u_min)
        u_coords.append(u_max)

    v_coords = []
    for v, u_min, u_max in horiz_segs:
        v_coords.append(v)
    for u, v_min, v_max in vert_segs:
        v_coords.append(v_min)
        v_coords.append(v_max)

    TOLERANCE = 26.0 # Tolérance de 26mm pour compenser les micro-écarts CAO

    u_candidates = group_coordinates(u_coords, TOLERANCE)
    v_candidates = group_coordinates(v_coords, TOLERANCE)

    # 6. Algorithme de déduction des alvéoles minimales (analyse des cycles fermés)
    cells = []
    for i in range(len(v_candidates)):
        for j in range(i + 1, len(v_candidates)):
            v1 = v_candidates[i]
            v2 = v_candidates[j]

            # Vérifier qu'il existe bien au moins un panneau aux niveaux horizontaux v1 et v2
            any_at_v1 = any(abs(v - v1) <= TOLERANCE for v, _, _ in horiz_segs)
            any_at_v2 = any(abs(v - v2) <= TOLERANCE for v, _, _ in horiz_segs)
            if not (any_at_v1 and any_at_v2):
                continue

            # Identifier les montants verticaux qui chevauchent l'intervalle de hauteur (v1, v2)
            overlapping_vert_u = []
            for u, v_min, v_max in vert_segs:
                if v_min < v2 - TOLERANCE and v_max > v1 + TOLERANCE:
                    overlapping_vert_u.append(u)

            if len(overlapping_vert_u) < 2:
                continue

            # Les parois d'une alvéole doivent être adjacentes dans la liste ordonnée des parois verticales
            u_walls = group_coordinates(overlapping_vert_u, TOLERANCE)

            for k in range(len(u_walls) - 1):
                u1 = u_walls[k]
                u2 = u_walls[k + 1]

                # Vérifications de fermeture des 4 côtés :
                # 1. Bordure basse (v1)
                if not covers_interval(horiz_segs, v1, u1, u2, TOLERANCE):
                    continue
                # 2. Bordure haute (v2)
                if not covers_interval(horiz_segs, v2, u1, u2, TOLERANCE):
                    continue
                # 3. Bordure gauche (u1)
                if not covers_interval(vert_segs, u1, v1, v2, TOLERANCE):
                    continue
                # 4. Bordure droite (u2)
                if not covers_interval(vert_segs, u2, v1, v2, TOLERANCE):
                    continue

                # Vérification : Aucune étagère horizontale ne doit couper l'intérieur de l'alvéole
                if has_horizontal_crossing(v1, v2, u1, u2, horiz_segs, TOLERANCE):
                    continue

                cells.append({
                    'u1': u1,
                    'u2': u2,
                    'v1': v1,
                    'v2': v2
                })

    App.Console.PrintMessage(f"-> Déduites {len(cells)} alvéoles physiques.\n")

    # 7. Attribution des IDs de grille et construction de l'enveloppe détaillée
    unique_u1s = group_coordinates([cell['u1'] for cell in cells], TOLERANCE)
    unique_v1s = group_coordinates([cell['v1'] for cell in cells], TOLERANCE)

    def find_closest_index(val, val_list):
        closest_idx = 0
        min_diff = float('inf')
        for idx, v in enumerate(val_list):
            diff = abs(v - val)
            if diff < min_diff:
                min_diff = diff
                closest_idx = idx
        return closest_idx

    alveoles_list = []
    for cell in cells:
        col_idx = find_closest_index(cell['u1'], unique_u1s)
        row_idx = find_closest_index(cell['v1'], unique_v1s)

        col_letter = col_index_to_letter(col_idx)
        row_num = row_idx + 1
        cell_id = f"{col_letter}{row_num}"

        # 7a. Identification individuelle de chaque panneau de l'enveloppe
        left_name = find_boundary_segment(segments_list, True, cell['u1'], cell['v1'], cell['v2'], horiz_axis_idx, vert_axis_idx, TOLERANCE)
        right_name = find_boundary_segment(segments_list, True, cell['u2'], cell['v1'], cell['v2'], horiz_axis_idx, vert_axis_idx, TOLERANCE)
        bottom_name = find_boundary_segment(segments_list, False, cell['v1'], cell['u1'], cell['u2'], horiz_axis_idx, vert_axis_idx, TOLERANCE)
        top_name = find_boundary_segment(segments_list, False, cell['v2'], cell['u1'], cell['u2'], horiz_axis_idx, vert_axis_idx, TOLERANCE)

        # 7b. Recherche de la profondeur minimale parmi les panneaux identifiés
        boundary_depths = []
        boundary_segments = {}
        for name in [left_name, right_name, bottom_name, top_name]:
            if name:
                for s in segments_list:
                    if s["nom"] == name:
                        boundary_depths.append(s["profondeur"])
                        boundary_segments[name] = s
                        break
        min_depth = min(boundary_depths) if boundary_depths else 0.0

        # Calcul des positions et dimensions selon les instructions
        # Position x (axe horizontal) = position de la paroi gauche + largeur de la paroi gauche
        if left_name and left_name in boundary_segments:
            left_segment = boundary_segments[left_name]
            pos_x = left_segment['debut'][horiz_axis_idx] + left_segment['largeur']
        else:
            pos_x = cell['u1']

        # Position z (axe vertical) = position de la paroi inférieur + hauteur de la paroi inférieur
        if bottom_name and bottom_name in boundary_segments:
            bottom_segment = boundary_segments[bottom_name]
            pos_z = bottom_segment['debut'][vert_axis_idx] + bottom_segment['hauteur']
        else:
            pos_z = cell['v1']

        # Position y (axe profondeur) = position de la paroi horizontale la plus en retrait vers l'arrière
        # On prend la coordonnée depth la plus petite parmi tous les panneaux de l'enveloppe
        depth_positions = []
        for name in [left_name, right_name, bottom_name, top_name]:
            if name and name in boundary_segments:
                seg = boundary_segments[name]
                depth_positions.append(seg['debut'][depth_axis_idx])
        pos_y = min(depth_positions) if depth_positions else w_avg

        # Largeur = position paroi droite - position.x de l'alvéole
        if right_name and right_name in boundary_segments:
            right_segment = boundary_segments[right_name]
            largeur = right_segment['debut'][horiz_axis_idx] - pos_x
        else:
            largeur = abs(cell['u2'] - cell['u1'])

        # Hauteur = position paroi haute - position.z de l'alvéole
        if top_name and top_name in boundary_segments:
            top_segment = boundary_segments[top_name]
            hauteur = top_segment['debut'][vert_axis_idx] - pos_z
        else:
            hauteur = abs(cell['v2'] - cell['v1'])

        # Reconstruction des coordonnées du coin inférieur gauche (position)
        def make_3d_point(u_val, v_val, w_val):
            pt = [0.0, 0.0, 0.0]
            pt[horiz_axis_idx] = u_val
            pt[vert_axis_idx] = v_val
            pt[depth_axis_idx] = w_val
            return pt

        position_alveole = make_3d_point(pos_x, pos_z, pos_y)

        alveoles_list.append({
            "id": cell_id,
            "role": None,  # null par défaut en JSON
            "enveloppe": {
                "paroi gauche": left_name,
                "paroi droite": right_name,
                "paroi basse": bottom_name,
                "paroi haute": top_name
            },
            "position": position_alveole,
            "largeur": largeur,
            "profondeur": min_depth,
            "hauteur": hauteur
        })

    # Tri des alvéoles par ID de façon naturelle (A1, A2, B1, B2...)
    alveoles_list.sort(key=lambda x: (len(x['id']), x['id']))

    # 8. Préparation des données JSON de sortie
    segments_json = []
    for s in segments_list:
        segments_json.append({
            "nom": s["nom"],
            "debut": s["debut"],
            "fin": s["fin"]
        })

    output_data = {
        "segments": segments_json,
        "alveoles": alveoles_list
    }

    # Sauvegarde dans le fichier meuble_simplifie.json
    output_path = os.path.join(macro_dir, "meuble_simplifie.json")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        App.Console.PrintMessage(f"\n[SUCCÈS] Fichier JSON exporté avec succès : '{output_path}'\n")
    except Exception as e:
        App.Console.PrintError(f"\n[ERREUR] Impossible de sauvegarder le fichier JSON: {e}\n")


if __name__ == "__main__":
    run()
