import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets
import FreeCAD_BespokeFurniture.MtEntreDeuxTv as MacroVertical
import FreeCAD_BespokeFurniture.TabEntreDeuxMt as MacroHorizontal
from FreeCAD_BespokeFurniture.lib_menuiserie import get_parent_part

# =============================================================================
# LOGIQUE DE CLASSIFICATION ET DÉTECTION
# =============================================================================

def get_box_props(part_obj):
    """
    Récupère la liste des propriétés de la box interne.
    CORRECTION : Utilise une recherche partielle pour détecter obj_pos_... etc.
    """
    for child in part_obj.OutList:
        plist = child.PropertiesList
        # On vérifie si une des propriétés contient une des racines clés
        if any(any(key in p_name for key in ["obj_gauche", "obj_droit", "obj_dessous", "obj_dessus", "obj_pos", "obj_taille"])
               for p_name in plist):
            return plist
    return []

def classify_object(part_obj):
    """
    Classe l'objet selon les catégories hôtes et extrémités.
    """
    label = part_obj.Label.lower()
    props = get_box_props(part_obj)

    has_v_props = "obj_dessous" in props or "obj_dessus" in props
    has_h_props = "obj_gauche" in props or "obj_droit" in props
    # Détection des familles de propriétés par sous-chaîne
    has_v_props = any("dessous" in p or "dessus" in p or "pos_dess" in p.lower() for p in props)
    has_h_props = any("gauche" in p or "droit" in p or "pos_gauche" in p.lower() or "pos_droit" in p.lower() for p in props)

    # Mots-clés catégories
    is_mt = any(k in label for k in ["mt", "montant"])
    is_tv = any(k in label for k in ["tv", "traverse", "tab", "tablette"])
    is_ambiguous_name = any(k in label for k in ["fond", "tiroir", "porte", "facade"])

    # Un hôte est ambigu s'il porte un nom spécifique OU possède les deux types de propriétés
    is_ambiguous_host = is_ambiguous_name or (has_v_props and has_h_props)

    result = {
        "obj": part_obj,
        "is_ambiguous_host": is_ambiguous_host,
        "is_ext_V": is_tv or (not is_mt and has_h_props),
        "is_ext_H": is_mt or (not is_tv and has_v_props),
        "has_v_props": has_v_props,
        "has_h_props": has_h_props
    }
    print(f"{part_obj.Label}\n{result}")
    return result

def run_orchestrator():
    selection = Gui.Selection.getSelection()

    # Résolution des parents Part uniques
    resolved = []
    seen = set()
    for obj in selection:
        p = get_parent_part(obj)
        if p and p.Name not in seen:
            resolved.append(p)
            seen.add(p.Name)

    count = len(resolved)
    data = [classify_object(p) for p in resolved]

    if count == 3:
        # --- CAS 3 OBJETS ---
        # 1. On cherche l'hôte (celui qui a des propriétés de pilotage)
        host_item = next((d for d in data if d["has_v_props"] or d["has_h_props"]), None)

        if host_item:
            others = [d for d in data if d["obj"].Name != host_item["obj"].Name]

            # --- DÉCISION DE LA STRATÉGIE ---

            # Cas A : L'objet n'a que des propriétés Verticales
            if host_item["has_v_props"] and not host_item["has_h_props"]:
                MacroVertical.run_assignment_macro()

            # Cas B : L'objet n'a que des propriétés Horizontales
            elif host_item["has_h_props"] and not host_item["has_v_props"]:
                MacroHorizontal.run_assignment_macro()

            # Cas C : L'objet est mixte (Ambigu) -> On tranche par les extrémités
            else:
                # Si les deux autres sont des extrémités Verticales (ex: Traverses)
                if all(d["is_ext_V"] for d in others):
                    App.Console.PrintMessage(f">>> Hôte mixte : choix VERTICAL d'après extrémités\n")
                    MacroVertical.run_assignment_macro()
                # Sinon par défaut on tente l'horizontale (ou si ce sont des Montants)
                else:
                    App.Console.PrintMessage(f">>> Hôte mixte : choix HORIZONTAL d'après extrémités\n")
                    MacroHorizontal.run_assignment_macro()

    elif count == 5:
        # --- CAS 5 OBJETS (RECHERCHE DE L'HÔTE AMBIGU) ---
        # L'hôte peut être n'importe lequel des 5
        host_item = next((d for d in data if d["is_ambiguous_host"]), None)

        if not host_item:
            App.Console.PrintWarning("Aucun hôte ambigu (Fond, Porte...) détecté parmi les 5 objets.\n")
            return

        others = [d for d in data if d["obj"].Name != host_item["obj"].Name]
        ext_v = [d["obj"] for d in others if d["is_ext_V"]]
        ext_h = [d["obj"] for d in others if d["is_ext_H"]]

        # 1. Stratégie Verticale
        if len(ext_v) >= 2:
            App.Console.PrintMessage(f">>> AUTO-V : {host_item['obj'].Label}\n")
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(host_item["obj"])
            Gui.Selection.addSelection(ext_v[0])
            Gui.Selection.addSelection(ext_v[1])
            MacroVertical.run_assignment_macro()

        # 2. Stratégie Horizontale
        if len(ext_h) >= 2:
            App.Console.PrintMessage(f">>> AUTO-H : {host_item['obj'].Label}\n")
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(host_item["obj"])
            Gui.Selection.addSelection(ext_h[0])
            Gui.Selection.addSelection(ext_h[1])
            MacroHorizontal.run_assignment_macro()

        # Restaurer la sélection de départ pour l'utilisateur
        Gui.Selection.clearSelection()
        for p in resolved: Gui.Selection.addSelection(p)

    else:
        App.Console.PrintWarning(f"Sélection de {count} objets non supportée (3 ou 5 requis).\n")

def run_orchestrator_by_labels(labels):
    """
    Équivalent à run_orchestrator mais prend une liste d'étiquettes (labels) d'objets FreeCAD
    au lieu d'utiliser la sélection active.
    """
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintWarning("Aucun document actif trouvé.\n")
        return

    # Résolution des objets à partir des labels
    resolved = []
    seen = set()
    for label in labels:
        objs = doc.getObjectsByLabel(label)
        if objs:
            obj = objs[0]
            p = get_parent_part(obj)
            print(f"parent dans run_orchestrator_by_labels: {p.Label}  ")
            if p and p.Name not in seen:
                resolved.append(p)
                seen.add(p.Name)

    count = len(resolved)
    data = [classify_object(p) for p in resolved]

    # structure: {"is_ext_V number;is_ext_H number;is_ambiguous_host number": strategy "V" or "H"}
    strategy_map = {
        "2;1;0" : "V",
        "1;2;0" : "H",
        "2;0;1" : "V",
        "0;2;1" : "H"
    }
    obj_map = f"{len([d for d in data if d['is_ext_V'] and not d['is_ambiguous_host']])};"
    obj_map += f"{len([d for d in data if d['is_ext_H'] and not d['is_ambiguous_host']])};"
    obj_map += f"{len([d for d in data if d['is_ambiguous_host']])}"
    print(obj_map)

    if count == 3:
        # --- CAS 3 OBJETS ---
        # Construire la liste des labels pour les 3 objets
        labels_for_macro = [p.Label for p in resolved]

        if strategy_map[obj_map] == "V":
            print(f"run_orchestrator_by_labels lancement MacroVertical")
            MacroVertical.run_assignment_macro(labels=labels_for_macro)

        elif strategy_map[obj_map] == "H":
            print(f"run_orchestrator_by_labels lancement MacroHorizontal")
            MacroHorizontal.run_assignment_macro(labels=labels_for_macro)

        else:
            # 1. On cherche l'hôte (celui qui a des propriétés de pilotage)
            host_item = next((d for d in data if d["has_v_props"] or d["has_h_props"]), None)

            if host_item:
                others = [d for d in data if d["obj"].Name != host_item["obj"].Name]

                # --- DÉCISION DE LA STRATÉGIE ---

                # Cas A : L'objet n'a que des propriétés Verticales
                if host_item["has_v_props"] and not host_item["has_h_props"]:
                    print(f"run_orchestrator_by_labels lancement MacroVertical")
                    MacroVertical.run_assignment_macro(labels=labels_for_macro)

                # Cas B : L'objet n'a que des propriétés Horizontales
                elif host_item["has_h_props"] and not host_item["has_v_props"]:
                    print(f"run_orchestrator_by_labels lancement MacroHorizontal")
                    MacroHorizontal.run_assignment_macro(labels=labels_for_macro)

                # Cas C : L'objet est mixte (Ambigu) -> On tranche par les extrémités
                else:
                    # Si les deux autres sont des extrémités Verticales (ex: Traverses)
                    if all(d["is_ext_V"] for d in others):
                        App.Console.PrintMessage(f">>> Hôte mixte : choix VERTICAL d'après extrémités\n")
                        print(f"run_orchestrator_by_labels lancement MacroVertical")
                        MacroVertical.run_assignment_macro(labels=labels_for_macro)
                    # Sinon par défaut on tente l'horizontale (ou si ce sont des Montants)
                    else:
                        App.Console.PrintMessage(f">>> Hôte mixte : choix HORIZONTAL d'après extrémités\n")
                        print(f"run_orchestrator_by_labels lancement MacroHorizontal")
                        MacroHorizontal.run_assignment_macro(labels=labels_for_macro)

    elif count == 5:
        # --- CAS 5 OBJETS (RECHERCHE DE L'HÔTE AMBIGU) ---
        # L'hôte peut être n'importe lequel des 5
        host_item = next((d for d in data if d["is_ambiguous_host"]), None)

        if not host_item:
            App.Console.PrintWarning("Aucun hôte ambigu (Fond, Porte...) détecté parmi les 5 objets.\n")
            return

        others = [d for d in data if d["obj"].Name != host_item["obj"].Name]
        ext_v = [d["obj"] for d in others if d["is_ext_V"]]
        ext_h = [d["obj"] for d in others if d["is_ext_H"]]

        # 1. Stratégie Verticale
        if len(ext_v) >= 2:
            App.Console.PrintMessage(f">>> AUTO-V : {host_item['obj'].Label}\n")
            # Passer les labels des 3 objets directement
            labels_for_macro = [host_item["obj"].Label, ext_v[0].Label, ext_v[1].Label]
            print(f"run_orchestrator_by_labels lancement MacroVertical")
            MacroVertical.run_assignment_macro(labels=labels_for_macro)

        # 2. Stratégie Horizontale
        if len(ext_h) >= 2:
            App.Console.PrintMessage(f">>> AUTO-H : {host_item['obj'].Label}\n")
            # Passer les labels des 3 objets directement
            labels_for_macro = [host_item["obj"].Label, ext_h[0].Label, ext_h[1].Label]
            print(f"run_orchestrator_by_labels lancement MacroHorizontal")
            MacroHorizontal.run_assignment_macro(labels=labels_for_macro)

        # Pas besoin de restaurer la sélection car on utilise les labels directement

    else:
        App.Console.PrintWarning(f"Sélection de {count} objets non supportée (3 ou 5 requis).\n")

if __name__ == '__main__':
    run_orchestrator()
