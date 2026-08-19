import json
import sys
import FreeCAD as App
from collections import defaultdict

from ..lib_menuiserie import get_parent_part

# Variable globale pour stocker le conteneur
JSON_CONTAINER_NAME = "meuble_simplifie"


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


def set_alveole_role(doc, alveole_id, role):
    """
    Modifie le rôle d'une alvéole dans le document.

    Args:
        doc: Document FreeCAD
        alveole_id: ID de l'alvéole (ex: "A1", "B2")
        role: Nouveau rôle à attribuer (ex: "penderie", "pulls", "livres", "assiettes")
    """
    if not doc:
        App.Console.PrintError("Aucun document fourni.\n")
        return False

    # Trouver l'objet App::Part contenant le JSON
    json_container = None
    for obj in doc.Objects:
        if obj.Name == "meuble_simplifie" and obj.isDerivedFrom("App::Part"):
            json_container = obj
            break

    if not json_container:
        App.Console.PrintError(f"Objet 'meuble_simplifie' non trouvé dans le document.\n")
        return False

    # Lire le JSON existant
    if not hasattr(json_container, "JSONData") or not json_container.JSONData:
        App.Console.PrintError("Aucune donnée JSON trouvée dans l'objet.\n")
        return False

    try:
        data = json.loads(json_container.JSONData)
    except json.JSONDecodeError as e:
        App.Console.PrintError(f"Erreur de décodage JSON: {e}\n")
        return False

    # Trouver et modifier l'alvéole
    found = False
    for alveole in data.get("alveoles", []):
        if alveole.get("id") == alveole_id:
            alveole["role"] = role
            found = True
            break

    if not found:
        App.Console.PrintError(f"Alvéole '{alveole_id}' non trouvée.\n")
        return False

    # Mettre à jour la propriété
    json_container.JSONData = json.dumps(data, indent=4, ensure_ascii=False)
    App.Console.PrintMessage(f"Rôle de l'alvéole '{alveole_id}' mis à jour avec succès.\n")
    return True


def get_json_container(doc, container_name=JSON_CONTAINER_NAME):
    """
    Récupère ou crée l'objet App::Part contenant le JSON.

    Args:
        doc: Document FreeCAD
        container_name: Nom de l'objet conteneur (par défaut: JSON_CONTAINER_NAME)

    Returns:
        L'objet App::Part contenant le JSON, ou None
    """
    # Chercher un objet existant
    for obj in doc.Objects:
        if obj.Name == container_name and obj.isDerivedFrom("App::Part"):
            return obj

    # Créer un nouvel objet App::Part
    try:
        json_container = doc.addObject("App::Part", container_name)
        doc.recompute()
        return json_container
    except Exception as e:
        App.Console.PrintError(f"Erreur lors de la création de l'objet conteneur: {e}\n")
        return None


def create_alveole_annotations(doc, alveoles_list, json_container):
    """
    Crée des annotations Draft pour chaque alvéole avec son ID et son rôle.

    Args:
        doc: Document FreeCAD
        alveoles_list: Liste des alvéoles
        json_container: L'objet App::Part conteneur
    """
    if not App.GuiUp:
        return

    try:
        import Draft
    except ImportError:
        App.Console.PrintWarning("Draft module non disponible, pas d'annotations créées.\n")
        return

    # Supprimer les anciennes annotations des alvéoles du conteneur
    for obj in json_container.Group[:]:  # Copie de la liste pour itération sûre
        if obj.Name.startswith("Text") or (hasattr(obj, 'Label') and "Alvéole" in str(obj.Label)):
            doc.removeObject(obj.Name)

    for alveole in alveoles_list:
        alveole_id = alveole.get("id", "?")
        role = alveole.get("role")
        position = alveole.get("position", [0, 0, 0])
        largeur = alveole.get("largeur", 0)
        hauteur = alveole.get("hauteur", 0)

        # Position de l'annotation : au centre de la face avant de l'alvéole, légèrement décalée vers l'avant
        x, y, z = position

        # Position au centre horizontal et vertical de la face avant
        annotation_pos = App.Vector(
            x + largeur / 2,
            y - 50,  # Décalage de 50mm vers l'avant (face avant)
            z + hauteur / 2
        )

        # Créer le texte de l'annotation
        text = f"{alveole_id}"
        if role and role != "non défini" and role is not None:
            text += f"\nRôle: {role}"

        # Créer l'annotation avec Draft.make_text
        try:
            # Créer un placement avec la position
            pl = App.Placement()
            pl.Base = annotation_pos
            pl.Rotation = App.Rotation()  # Rotation par défaut

            # Créer le texte avec Draft.make_text
            text_obj = Draft.make_text([text], placement=pl)

            # Ajouter manuellement au conteneur App::Part
            json_container.addObject(text_obj)

            # Configurer le label
            text_obj.Label = f"Nom alvéole {alveole_id}"

            # Style visuel
            if App.GuiUp and text_obj.ViewObject:
                text_obj.ViewObject.TextColor = (0.0, 0.0, 0.0)  # Noir
                text_obj.ViewObject.FontSize = 30  # Taille de police
                text_obj.ViewObject.DisplayMode = u"Screen"

        except Exception as e:
            App.Console.PrintWarning(f"Erreur lors de la création de l'annotation pour {alveole_id}: {e}\n")

def segment_traverse_cellule(seg_tuple, cell, is_vert, tolerance=26.0):
    """Vérifie si un segment traverse intégralement la cellule de bord à bord."""
    u1, u2 = cell['u1'], cell['u2']
    v1, v2 = cell['v1'], cell['v2']

    if is_vert:
        u_seg, v_min, v_max = seg_tuple
        if u1 + tolerance < u_seg < u2 - tolerance:
            if v_min <= v1 + tolerance and v_max >= v2 - tolerance:
                return True, u_seg
    else:
        v_seg, u_min, u_max = seg_tuple
        if v1 + tolerance < v_seg < v2 - tolerance:
            if u_min <= u1 + tolerance and u_max >= u2 - tolerance:
                return True, v_seg

    return False, None

def decomposer_cellule_recursive(cell, parent_id, vert_segs, horiz_segs, tolerance=26.0):
    """Décompose récursivement une cellule et génère les identifiants hiérarchiques."""
    u1, u2 = cell['u1'], cell['u2']
    v1, v2 = cell['v1'], cell['v2']

    # Découpes verticales (colonnes)
    split_u = []
    for s in vert_segs:
        cuts, u_val = segment_traverse_cellule(s, cell, is_vert=True, tolerance=tolerance)
        if cuts:
            split_u.append(u_val)
    split_u = group_coordinates(split_u, tolerance)

    # Découpes horizontales (étagères/rangées)
    split_v = []
    for s in horiz_segs:
        cuts, v_val = segment_traverse_cellule(s, cell, is_vert=False, tolerance=tolerance)
        if cuts:
            split_v.append(v_val)
    split_v = group_coordinates(split_v, tolerance)

    # Si aucune découpe ne traverse : cellule terminale (alvéole)
    if not split_u and not split_v:
        cell['id'] = parent_id
        return [cell]

    leaves = []

    # Priorité aux séparations en colonnes
    if split_u:
        u_bounds = sorted([u1] + split_u + [u2])
        for idx in range(len(u_bounds) - 1):
            col_letter = col_index_to_letter(idx)
            child_id = col_letter if not parent_id else f"{parent_id}-{col_letter}"
            sub_cell = {'u1': u_bounds[idx], 'u2': u_bounds[idx+1], 'v1': v1, 'v2': v2}
            leaves.extend(decomposer_cellule_recursive(sub_cell, child_id, vert_segs, horiz_segs, tolerance))

    # Sinon, séparations en rangées
    elif split_v:
        v_bounds = sorted([v1] + split_v + [v2])
        for idx in range(len(v_bounds) - 1):
            row_num = idx + 1
            if parent_id and parent_id[-1].isalpha():
                child_id = f"{parent_id}{row_num}"
            elif parent_id and parent_id[-1].isdigit():
                child_id = f"{parent_id}-{row_num}"
            else:
                child_id = f"{row_num}"
            sub_cell = {'u1': u1, 'u2': u2, 'v1': v_bounds[idx], 'v2': v_bounds[idx+1]}
            leaves.extend(decomposer_cellule_recursive(sub_cell, child_id, vert_segs, horiz_segs, tolerance))

    return leaves

def update_meuble_simplifie(doc):
    """
    Fonction principale pour analyser le meuble et mettre à jour l'objet meuble_simplifie.
    Peut être appelée depuis d'autres scripts.
    Description du nommage des alvéoles, exemple:
        Soit un meuble divisé en 3 colonnes A, B, C. La colonne A est divisée par plusieurs traverses, A1, A2, A3, A4.
        La deuxième étagère est encore divisée en 2 colonnes. Leur nom doivent être A2-A et A2-B.
        Et si A2-A est divisée verticalement par d'autres traverses, alors on a les noms A2-A1, A2-A2... Et pour A2-B ce serait A2-B1, A2-B2...
        On pourrait aussi avoir dans le même principe A3-A-A, A3-A-B, A3-A-C, si A3 est découpé en plusieurs colonnes et
        que la première colonne est encore découpée en colonne.

    Args:
        doc: Document FreeCAD à analyser

    Returns:
        bool: True si succès, False sinon
    """
    if not doc:
        App.Console.PrintError("Aucun document fourni.\n")
        return False

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

        # Récupérer le parent via get_parent_part
        parent_part = get_parent_part(obj)
        parent_label = parent_part.Label if parent_part else obj.Label

        child = obj
        parent_list = []
        if parent_part:
            parent_list.append(parent_part)
            child = parent_part
            grand_parent = child.getParentGeoFeatureGroup()
            i = 1
            while grand_parent and i < 5:
                parent_list.append(grand_parent)
                child = grand_parent
                grand_parent = child.getParentGeoFeatureGroup()
                i += 1

        vec = App.Vector(0, 0, 0)
        if parent_list:
            for pp in parent_list:
                vec = vec.add(pp.Placement.Base)
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

        liaisons = []
        print(f"update_meuble_simplifie obj {obj.Label} ")
        if is_vertical:
            debut = [pos_x, pos_y, pos_z]
            fin = [pos_x, pos_y, pos_z + hauteur]
            role = "vertical"
            if hasattr(obj, "obj_dessous"):
                liaisons.append(obj.obj_dessous.Label)
            if hasattr(obj, "obj_dessus"):
                liaisons.append(obj.obj_dessus.Label)
            epaisseur = largeur
        else:  # is_horizontal
            debut = [pos_x, pos_y, pos_z]
            fin = [pos_x + largeur, pos_y, pos_z]
            role = "horizontal"
            if hasattr(obj, "obj_gauche"):
                liaisons.append(obj.obj_gauche.Label)
            if hasattr(obj, "obj_droit"):
                liaisons.append(obj.obj_droit.Label)
            epaisseur = hauteur

        segments_list.append({
            "nom": parent_label,
            "role": role,
            "debut": debut,
            "fin": fin,
            "largeur": largeur,
            "profondeur": profondeur,
            "hauteur": hauteur,
            "epaisseur": epaisseur,
            "liaisons": liaisons
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

    TOLERANCE = 26.0 # Tolérance de 26mm pour compenser les micro-écarts CAO

    # 5. Décomposition hiérarchique récursive
    all_u = [s['debut'][horiz_axis_idx] for s in segments_list] + [s['fin'][horiz_axis_idx] for s in segments_list]
    all_v = [s['debut'][vert_axis_idx] for s in segments_list] + [s['fin'][vert_axis_idx] for s in segments_list]

    root_cell = {
        'u1': min(all_u),
        'u2': max(all_u),
        'v1': min(all_v),
        'v2': max(all_v)
    }

    cells = decomposer_cellule_recursive(root_cell, "", vert_segs, horiz_segs, TOLERANCE)

    App.Console.PrintMessage(f"-> Déduites {len(cells)} alvéoles physiques.\n")

    # 6. Construction de l'enveloppe détaillée des alvéoles

    alveoles_list = []
    for cell in cells:
        cell_id = cell['id']

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

        # Position y (axe profondeur) = position de la paroi la plus en arrière
        # On prend la coordonnée depth la plus grande (y max) parmi tous les panneaux de l'enveloppe
        depth_positions = []
        for name in [left_name, right_name, bottom_name, top_name]:
            if name and name in boundary_segments:
                seg = boundary_segments[name]
                depth_positions.append(seg['debut'][depth_axis_idx])
        pos_y = max(depth_positions) if depth_positions else w_avg

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

    # Tri final naturel des alvéoles par leur identifiant hiérarchique
    alveoles_list.sort(key=lambda x: (x['id'],))

    # 8. Préparation des données JSON de sortie
    segments_json = []
    for s in segments_list:
        segments_json.append({
            "nom": s["nom"],
            "debut": s["debut"],
            "fin": s["fin"],
            "epaisseur": s["epaisseur"],
            "liaisons": s["liaisons"]
        })

    new_output_data = {
        "segments": segments_json,
        "alveoles": alveoles_list
    }

    # 9. Récupérer ou créer l'objet conteneur App::Part
    json_container = get_json_container(doc, "meuble_simplifie")
    if not json_container:
        App.Console.PrintError("Impossible de créer l'objet conteneur.\n")
        return

    # 10. Logique de mise à jour
    existing_data = None
    if hasattr(json_container, "JSONData") and json_container.JSONData:
        try:
            existing_data = json.loads(json_container.JSONData)
        except json.JSONDecodeError:
            existing_data = None

    if existing_data:
        # Mise à jour : conserver les rôles des alvéoles existantes
        # Créer un dictionnaire des alvéoles existantes indexées par leurs 4 parois
        existing_alveoles_by_walls = {}
        for existing_alveole in existing_data.get("alveoles", []):
            enveloppe = existing_alveole.get("enveloppe", {})
            wall_key = (
                enveloppe.get("paroi gauche"),
                enveloppe.get("paroi droite"),
                enveloppe.get("paroi basse"),
                enveloppe.get("paroi haute")
            )
            existing_alveoles_by_walls[wall_key] = existing_alveole

        updated_alveoles = []
        preserved_roles_count = 0

        for new_alveole in alveoles_list:
            enveloppe = new_alveole.get("enveloppe", {})
            wall_key = (
                enveloppe.get("paroi gauche"),
                enveloppe.get("paroi droite"),
                enveloppe.get("paroi basse"),
                enveloppe.get("paroi haute")
            )

            # Vérifier si une alvéole existante a les mêmes 4 parois
            if wall_key in existing_alveoles_by_walls:
                existing_alveole = existing_alveoles_by_walls[wall_key]
                # Conserver le rôle de l'alvéole existante
                new_alveole["role"] = existing_alveole.get("role")
                preserved_roles_count += 1

            updated_alveoles.append(new_alveole)

        # Créer les données finales avec les segments nouveaux et les alvéoles mises à jour
        output_data = {
            "segments": segments_json,
            "alveoles": updated_alveoles
        }
        App.Console.PrintMessage(f"-> Mise à jour de {len(updated_alveoles)} alvéoles ({preserved_roles_count} rôles conservés).\n")
    else:
        # Première exécution : créer les données
        output_data = new_output_data
        App.Console.PrintMessage(f"-> Création de {len(alveoles_list)} alvéoles.\n")

    # 11. Stocker le JSON dans la propriété de l'objet
    try:
        # Ajouter la propriété JSONData si elle n'existe pas
        if not hasattr(json_container, "JSONData"):
            json_container.addProperty("App::PropertyString", "JSONData", "JSON", "Données JSON du meuble simplifié")

        json_container.JSONData = json.dumps(output_data, indent=4, ensure_ascii=False)
        doc.recompute()
        App.Console.PrintMessage(f"\n[SUCCÈS] JSON stocké dans l'objet '{JSON_CONTAINER_NAME}'.\n")
    except Exception as e:
        App.Console.PrintError(f"\n[ERREUR] Impossible de stocker le JSON: {e}\n")
        return False

    # 12. Créer les annotations pour les alvéoles
    try:
        create_alveole_annotations(doc, output_data.get("alveoles", []), json_container)
        doc.recompute()
        App.Console.PrintMessage("Annotations des alvéoles créées.\n")
    except Exception as e:
        App.Console.PrintWarning(f"Avertissement : Impossible de créer les annotations: {e}\n")

    return True


def run():
    """
    Fonction d'entrée pour l'exécution directe du script.
    Appelle update_meuble_simplifie sur le document actif.
    """
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("Aucun document actif trouvé dans FreeCAD.\n")
        return

    update_meuble_simplifie(doc)


if __name__ == "__main__":
    run()
