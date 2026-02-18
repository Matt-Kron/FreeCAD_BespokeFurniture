# -*- coding: utf-8 -*-
import FreeCAD
import re

print('Macro: Mise à jour de la Nomenclature (BOM) - UID déplacé en colonne A')

# --- FONCTION CORRIGÉE POUR ÉVITER LES BOUCLES INFINIES ---
def get_recursively_shaped_objects(objects_list, visited_objects=None):
    """
    Récupère tous les objets avec une Shape, y compris ceux des conteneurs récursifs, 
    tout en évitant les boucles infinies via un suivi des objets visités.
    """
    if visited_objects is None:
        visited_objects = set()
        
    shaped_objects = []
    
    for obj in objects_list:
        # Évite de traiter l'objet s'il a déjà été vu (STOPPER LA RÉCURSION EN CAS DE BOUCLE)
        if obj in visited_objects:
            continue
            
        visited_objects.add(obj)

        # 1. Traitement des objets avec une Shape
        if hasattr(obj, "Shape"):
            shaped_objects.append(obj)
        
        # 2. Récursion dans les conteneurs
        if hasattr(obj, "OutListRecursive"):
            # Passer le set des objets visités aux appels récursifs
            shaped_objects.extend(get_recursively_shaped_objects(obj.OutListRecursive, visited_objects))
            
    return shaped_objects
# --------------------------------------------------------

# --- DÉFINITION DES NOUVELLES OPÉRATIONS ---
OP_PROPERTIES = {
    "Op_Delignage": "Délignage",
    "Op_Degauchissage": "Dégauchissage",
    "Op_Rabotage": "Rabotage",
    "Op_Decoupe_Format": "Découpe",
    "Op_Decoupe_Forme": "Découpe forme",
    "Op_Clamex": "Clamex",
    "Op_Autre_Fixation": "Autre fixation",
    "Op_Rainure_Fond": "Rainure fond",
    "Op_Rainure_Cremaillere": "Rainure crémaillère",
    "Op_Autres_Rainures": "Autres rainures",
    "Op_Collage_Chant_Grand": "Collage chant grand",
    "Op_Collage_Chant_Petit": "Collage chant petit",
    "Op_Poncage_Chant_Grand": "Ponçage chant grand",
    "Op_Poncage_Chant_Petit": "Ponçage chant petit",
    "Op_Poncage_Faces": "Ponçage faces",
    "Op_Rubio": "Rubio",
    "Op_Laque": "Laque",
    "Op_Plaquage": "Plaquage",
    "Op_Fixation_Coulisse": "Fixation coulisse",
    "Op_Fixation_Charniere": "Fixation charnière",
    "Op_Fixation_Tip_on": "Fixation Tip-on",
    "Op_Fixation_Facade_Tiroir": "Fixation Façade tiroir",
    "Op_Fixation_Poignee": "Fixation poignée",
    "Op_CAO": "CAO",
    "Op_Montage_Blanc": "Montage à blanc",
    "EdgeBands_Avant": "Chant avant",
    "EdgeBands_Arriere": "Chant arrière",
    "EdgeBands_Gauche": "Chant gauche",
    "EdgeBands_Droit": "Chant droit",
}

# Fonction utilitaire pour convertir un index (base 0) en nom de colonne (A, B, C, ..., AA, AB...)
def get_column_letter(index):
    result = ''
    while index >= 0:
        result = chr(ord('A') + index % 26) + result
        index = index // 26 - 1
    return result

# --- 1. Préparation de la Spreadsheet ---

try:
    bom = App.activeDocument().BOM
except:
    bom = App.activeDocument().addObject('Spreadsheet::Sheet','BOM')

# Configuration des colonnes
UID_COLUMN = 'A'
# Les données classiques vont de l'index 1 à 8 (B à I)
DATA_FIXED_START_INDEX = 1 
DATA_FIXED_END_INDEX = 8 
# Les opérations commencent à l'index 9 (J)
OP_START_INDEX = 9
NUM_OP_COLUMNS = len(OP_PROPERTIES) # 25
OP_END_INDEX = OP_START_INDEX + NUM_OP_COLUMNS - 1 # 9 + 25 - 1 = 33 (AH)

# La dernière colonne de données est AI (index 34)
LAST_DATA_COLUMN = get_column_letter(OP_END_INDEX) 

# Liste des colonnes de données (B à AI) pour l'effacement
# UID est en A, ne pas effacer.
DATA_COLUMNS = [get_column_letter(i) for i in range(DATA_FIXED_START_INDEX, OP_END_INDEX + 1)] 

# NOUVEAUX EN-TÊTES
# L'UID est maintenant en A1
HEADERS = {
    'A1': "UID", 
    'B1': "Objet parent",      # Ancien A
    'C1': "Libelle",           # Ancien B
    'D1': "Nest_grain",        # Ancien C
    'E1': "Thickness",         # Ancien D
    'F1': "3eme",              # Ancien E
    'G1': "Quantité",          # Ancien F
    'H1': "Matériau",           # Ancien G
    'I1': "Nest rotation allowed", # Ancien H
}

# Ajout dynamique des en-têtes d'opérations (à partir de J1, index 9)
for i, header_name in enumerate(OP_PROPERTIES.values()):
    col_letter = get_column_letter(OP_START_INDEX + i)
    HEADERS[f'{col_letter}1'] = header_name

for cell, value in HEADERS.items():
    bom.set(cell, value)
    
# --- 2. Lecture des UID existants dans la Spreadsheet (Colonne A) ---
existing_uids_map = {}
max_row = 1000 

for row in range(2, max_row + 1):
    cell_id = f"{UID_COLUMN}{row}"
    
    for col_char in DATA_COLUMNS:
        bom.set(f"{col_char}{row}", "")
    try:
        uid_value = bom.get(cell_id)
    except Exception:
        uid_value = ""
        
    if uid_value:
        existing_uids_map[str(uid_value)] = row
    else:
        break

# --- 3. Filtrage des objets FreeCAD ---

filtered_objects = {}

all_objects = FreeCAD.ActiveDocument.Objects
recursive_shaped_objects = get_recursively_shaped_objects(all_objects) 

for obj in recursive_shaped_objects:
    if hasattr(obj, "BOM_destination") and obj.BOM_destination:
        try:
            uid = f"{obj.Parents[0][0].Label}&&{obj.Label}"
            filtered_objects[uid] = obj
        except IndexError:
             uid = f"{obj.Name}&&NoParent"
             filtered_objects[uid] = obj
        

# --- 4. Mise à jour de la Spreadsheet ---

# modif pour trier selon l'étiquette du Parent
filtered_uids_prov = set(filtered_objects.keys())
filtered_objects_temp = {}
for key in filtered_uids_prov:
    filtered_objects_temp[key]=filtered_objects[key]
# Trie par label du parent
filtered_objects_sorted = dict(sorted(filtered_objects_temp.items(), key=lambda item: item[1].Parents[0][0].Label)) 
filtered_uids = list(filtered_objects_sorted.keys())

# --- A. Mise à jour des objets existants et "désactivation" des objets perdus ---

for uid, row in existing_uids_map.items():
    
    cell = row
    
    if uid in filtered_uids:
        obj = filtered_objects[uid]
        
        # A: Écriture de l'UID
        bom.set(f"{UID_COLUMN}{cell}", uid) 
        
        # B à I (Colonnes de données fixes, décalées de A à B, H à I)
        
        # B: Objet parent
        try:
            bom.set(f"B{cell}", obj.Parents[0][0].Label)
        except:
            bom.set(f"B{cell}","")
            
        # C: Libelle
        bom.set(f"C{cell}", obj.Label)

        # D, E, F: Nesting
        try:
            if hasattr(obj, 'Nest_grain') and hasattr(obj, 'Nest_Thickness'):
                bom.set(f"D{cell}", f"{getattr(obj.Shape.BoundBox, obj.Nest_grain):.1f}")
                bom.set(f"E{cell}", f"{getattr(obj.Shape.BoundBox, obj.Nest_Thickness):.1f}")
                all_dims = ["XLength", "YLength", "ZLength"]
                used_dims = [obj.Nest_grain, obj.Nest_Thickness]
                dim = [l for l in all_dims if l not in used_dims][0]
                bom.set(f"F{cell}", f"{getattr(obj.Shape.BoundBox, dim):.1f}")
            else:
                 bom.set(f"D{cell}", "")
                 bom.set(f"E{cell}", "")
                 bom.set(f"F{cell}", "")
        except Exception:
            bom.set(f"D{cell}", "")
            bom.set(f"E{cell}", "")
            bom.set(f"F{cell}", "")
            
        # G: Quantité 
        try:
             bom.set(f"G{cell}",f'{obj.BOM_quantity}')
        except:
             bom.set(f"G{cell}",'1')
             
        # H: Matériau 
        try:
             bom.set(f"H{cell}",f'{obj.BOM_mat}')
        except:
             bom.set(f"H{cell}",'mela')
             
        # I: Nest rotation allowed 
        try:
            bom.set(f"I{cell}", f"{obj.Nest_Allow_Rotation}")
        except:
            bom.set(f"I{cell}", "")
            
        # J à AI (Nouvelles colonnes d'Opérations)
        op_current_index = OP_START_INDEX # Index 9 (colonne J)
        for prop_name in OP_PROPERTIES.keys():
            col_letter = get_column_letter(op_current_index)
            
            # Écrire la valeur de la propriété, ou vide si elle n'existe pas
            if hasattr(obj, prop_name):
                bom.set(f"{col_letter}{cell}", str(getattr(obj, prop_name)))
            else:
                bom.set(f"{col_letter}{cell}", "")
                
            op_current_index += 1

        filtered_uids.remove(uid)
        
    # Cas 2: L'UID n'est plus dans la liste de filtrage (LIGNE À DÉSACVTIVER)
    else:
        # Effacer les colonnes de données (B à AI), mais CONSERVER L'UID en A
        for col_char in DATA_COLUMNS: 
            bom.set(f"{col_char}{cell}", "")


# --- B. Ajout des nouveaux objets (UIDs restants) à la fin ---

last_used_row = 1
if existing_uids_map:
    last_used_row = max(existing_uids_map.values())
    
next_new_row = last_used_row + 1 

if filtered_uids:
    print(f"Ajout de {len(filtered_uids)} nouveaux objets à partir de la ligne {next_new_row}")
    
    for uid in filtered_uids:
        obj = filtered_objects[uid]
        cell = next_new_row
        
        # A: Écriture de l'UID
        bom.set(f"{UID_COLUMN}{cell}", uid)
        
        # B: Objet parent
        try:
            bom.set(f"B{cell}", obj.Parents[0][0].Label)
        except:
            bom.set(f"B{cell}","")
            
        # C: Libelle
        bom.set(f"C{cell}", obj.Label)

        # D, E, F: Nesting
        try:
            if hasattr(obj, 'Nest_grain') and hasattr(obj, 'Nest_Thickness'):
                bom.set(f"D{cell}", f"{getattr(obj.Shape.BoundBox, obj.Nest_grain):.1f}")
                bom.set(f"E{cell}", f"{getattr(obj.Shape.BoundBox, obj.Nest_Thickness):.1f}")
                all_dims = ["XLength", "YLength", "ZLength"]
                used_dims = [obj.Nest_grain, obj.Nest_Thickness]
                dim = [l for l in all_dims if l not in used_dims][0]
                bom.set(f"F{cell}", f"{getattr(obj.Shape.BoundBox, dim):.1f}")
            else:
                 bom.set(f"D{cell}", "")
                 bom.set(f"E{cell}", "")
                 bom.set(f"F{cell}", "")
        except Exception:
            bom.set(f"D{cell}", "")
            bom.set(f"E{cell}", "")
            bom.set(f"F{cell}", "")
            
        # G: Quantité
        try:
             bom.set(f"G{cell}",f'{obj.BOM_quantity}')
        except:
             bom.set(f"G{cell}",'1')
            
        # H: Matériau
        try:
             bom.set(f"H{cell}",f'{obj.BOM_mat}')
        except:
             bom.set(f"H{cell}",'mela')
             
        # I: Nest rotation allowed
        try:
            bom.set(f"I{cell}", f"{obj.Nest_Allow_Rotation}")
        except:
            bom.set(f"I{cell}", "")
            
        # J à AI (Nouvelles colonnes d'Opérations)
        op_current_index = OP_START_INDEX # Index 9 (colonne J)
        for prop_name in OP_PROPERTIES.keys():
            col_letter = get_column_letter(op_current_index)
            
            # Écrire la valeur de la propriété, ou vide si elle n'existe pas
            if hasattr(obj, prop_name):
                bom.set(f"{col_letter}{cell}", str(getattr(obj, prop_name)))
            else:
                bom.set(f"{col_letter}{cell}", "")
                
            op_current_index += 1
            
        next_new_row += 1
else:
    print("Aucun nouvel objet à ajouter.")

# ajout total de la colonne quantité
bom.set(f"F{next_new_row}", "Total")
bom.set(f"G{next_new_row}", f"=sum(G2:G{next_new_row-1})")

App.ActiveDocument.recompute()
