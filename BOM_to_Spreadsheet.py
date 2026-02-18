import FreeCAD as App
import FreeCADGui as Gui
from PySide2 import QtGui, QtCore, QtWidgets
import json, os, re, subprocess

# --- CONFIGURATION ---
HEADERS = {
    'A1': "UID", 'B1': "Objet parent", 'C1': "Libelle", 'D1': "Nest_grain",
    'E1': "Thickness", 'F1': "3eme", 'G1': "Quantité", 'H1': "Matériau",
    'I1': "Nest rotation allowed"
}

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

class BOMToSpreadsheet(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BOM to Spreadsheet - Version Complète Fixée")
        self.setMinimumSize(1000, 600)

        # Initialisation Bibliothèque
        self.global_json = os.path.join(App.getUserMacroDir(), "BOM_Library.json")
        if not os.path.exists(self.global_json):
            with open(self.global_json, 'w', encoding='utf-8') as f: json.dump([], f)

        self.setup_ui()
        self.load_from_varset()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        btns = QtWidgets.QHBoxLayout()
        self.btn_add_file = QtWidgets.QPushButton("📁 Ajouter Classeur")
        self.btn_add_file.clicked.connect(self.add_file)

        # --- NOUVEAU BOUTON ---
        self.btn_manage_lib = QtWidgets.QPushButton("📚 Gérer Biblio")
        self.btn_manage_lib.clicked.connect(self.manage_library)

        # self.btn_listen = QtWidgets.QPushButton("🚀 Ecoute Calc (Port 2002)")
        # self.btn_listen.clicked.connect(self.start_libreoffice_listen)
        btns.addWidget(self.btn_add_file)
        # btns.addWidget(self.btn_listen)
        btns.addWidget(self.btn_manage_lib) # Ajout au layout
        btns.addStretch()
        layout.addLayout(btns)

        self.tree = QtWidgets.QTreeView()
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Structure", "Configuration", "État"])
        self.tree.setModel(self.model)
        # Charger les données existantes
        self.load_from_varset()


        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.context_menu)
        layout.addWidget(self.tree)



    # --- SYNCHRO VARSET (CORRIGÉE) ---
    # def sync_to_varset(self):
    #     doc = App.ActiveDocument
    #     if not doc: return
    #     vs = doc.getObject("BOM_to_Spreadsheet") or doc.addObject("App::VarSet", "BOM_to_Spreadsheet")
    #     for p in vs.PropertiesList:
    #         try: vs.removeProperty(p)
    #         except: pass
    #
    #     for i in range(self.model.rowCount()):
    #         f_item = self.model.item(i)
    #         f_grp = f"File_{i:03d}"
    #         vs.addProperty("App::PropertyString", f"{f_grp}_Label", f_grp)
    #         setattr(vs, f"{f_grp}_Label", str(f_item.text()))
    #         vs.addProperty("App::PropertyString", f"{f_grp}_Path", f_grp)
    #         setattr(vs, f"{f_grp}_Path", str(f_item.data(QtCore.Qt.UserRole) or ""))
    #
    #         for j in range(f_item.rowCount()):
    #             s_item = f_item.child(j)
    #             s_grp = f"{f_grp}_Sheet_{j:03d}"
    #             vs.addProperty("App::PropertyString", f"{s_grp}_Label", s_grp)
    #             setattr(vs, f"{s_grp}_Label", str(s_item.text()))
    #
    #             for k in range(s_item.rowCount()):
    #                 data_item = s_item.child(k, 1)
    #                 if data_item:
    #                     p_name = f"{s_grp}_Plage_{k:03d}"
    #                     vs.addProperty("App::PropertyString", p_name, s_grp)
    #                     setattr(vs, p_name, json.dumps(data_item.data(QtCore.Qt.UserRole)))
    #     doc.recompute()

    def sync_to_varset(self):
        doc = App.ActiveDocument
        if not doc: return
        vs = doc.getObject("BOM_to_Spreadsheet") or doc.addObject("App::VarSet", "BOM_to_Spreadsheet")

        # Nettoyage des anciennes propriétés
        for p in vs.PropertiesList:
            try: vs.removeProperty(p)
            except: pass

        for i in range(self.model.rowCount()):
            f_item = self.model.item(i)
            f_grp = f"F{i:02d}"

            # SAUVEGARDE DU FICHIER (on sauve le dictionnaire JSON de la colonne 0)
            p_file = f"{f_grp}_Data"
            vs.addProperty("App::PropertyString", p_file, "Classeurs")
            data_f = f_item.data(QtCore.Qt.UserRole)
            setattr(vs, p_file, json.dumps(data_f))

            for j in range(f_item.rowCount()):
                s_item = f_item.child(j)
                s_grp = f"{f_grp}_S{j:02d}"

                # SAUVEGARDE DE LA FEUILLE
                p_sheet = f"{s_grp}_Data"
                vs.addProperty("App::PropertyString", p_sheet, f_item.text())
                data_s = s_item.data(QtCore.Qt.UserRole)
                setattr(vs, p_sheet, json.dumps(data_s))

                for k in range(s_item.rowCount()):
                    # On prend l'item de la COLONNE 0 (l'instruction)
                    inst_item = s_item.child(k, 0)
                    if inst_item:
                        p_inst = f"{s_grp}_I{k:02d}"
                        vs.addProperty("App::PropertyString", p_inst, s_item.text())
                        # On sauve tout le dictionnaire (dest, colonnes, filtres, type)
                        data_i = inst_item.data(QtCore.Qt.UserRole)
                        setattr(vs, p_inst, json.dumps(data_i))

        doc.recompute()
                # Déplier tout l'arbre par défaut
        self.tree.expandAll()

        h = self.tree.header()
        # 1. On définit le mode sur 'Interactive' pour garder le contrôle
        h.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        h.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        # 2. On impose les largeurs fixes
        h.resizeSection(0, 300) # Colonne Plage
        h.resizeSection(1, 500) # Colonne Dest
        # 3. On laisse la dernière colonne (Statut) absorber tout le reste
        # C'est ce qui empêchera la colonne 'Path' de déborder
        h.setStretchLastSection(True)

    # def load_from_varset(self):
    #     vs = App.ActiveDocument.getObject("BOM_to_Spreadsheet")
    #     if not vs: return
    #     self.model.clear()
    #     self.model.setHorizontalHeaderLabels(["Structure", "Configuration", "État"])
    #     all_p = vs.PropertiesList
    #     for f_p in sorted([p for p in all_p if p.startswith("File_") and p.endswith("_Label") and "_Sheet_" not in p]):
    #         grp = f_p.replace("_Label", "")
    #         f_item = QtGui.QStandardItem(getattr(vs, f_p))
    #         f_item.setData(getattr(vs, grp + "_Path", ""), QtCore.Qt.UserRole)
    #         self.model.appendRow([f_item, QtGui.QStandardItem(f_item.data(QtCore.Qt.UserRole)), QtGui.QStandardItem("FILE")])
    #         for s_p in sorted([p for p in all_p if p.startswith(grp + "_Sheet_") and p.endswith("_Label")]):
    #             s_item = QtGui.QStandardItem(getattr(vs, s_p))
    #             f_item.appendRow([s_item, QtGui.QStandardItem("SHEET")])
    #             for p_p in sorted([p for p in all_p if p.startswith(s_p.replace("_Label", "") + "_Plage_")]):
    #                 data = json.loads(getattr(vs, p_p))
    #                 c0, c1 = QtGui.QStandardItem("📥 Plage"), QtGui.QStandardItem(f"Dest: {data['dest']}")
    #                 c1.setData(data, QtCore.Qt.UserRole)
    #                 s_item.appendRow([c0, c1, QtGui.QStandardItem("PRÊT")])
    #     self.tree.expandAll()

    def load_from_varset(self):
        # --- AJOUTER CETTE LIGNE ---
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Plage / Nom", "Destination", "Statut"])
        # ---------------------------
        doc = App.ActiveDocument
        if not doc: return
        vs = doc.getObject("BOM_to_Spreadsheet")
        if not vs: return

        # On récupère toutes les propriétés et on les trie par nom pour garder l'ordre
        props = sorted(vs.PropertiesList)

        # Dictionnaires temporaires pour reconstruire la hiérarchie
        files = {}
        sheets = {}

        for p in props:
            # IGNORER les propriétés système de FreeCAD qui ne sont pas des données
            if p in ['Label', 'Proxy', 'Visibility', 'Group', 'ExpressionEngine']:
                continue

            try:
                raw_val = getattr(vs, p)
                if not raw_val or not isinstance(raw_val, str): continue

                # Vérification sommaire si c'est du JSON (doit commencer par { )
                if not raw_val.strip().startswith('{'):
                    continue

                data = json.loads(raw_val)
                item_type = data.get('type')

                if item_type == 'file':
                    # Recréation du fichier
                    fi = QtGui.QStandardItem(os.path.basename(data['path']))
                    fi.setData(data, QtCore.Qt.UserRole)
                    # Colonnes d'affichage : Nom, Chemin, Status
                    row = [fi, QtGui.QStandardItem(data['path']), QtGui.QStandardItem("FILE")]
                    self.model.appendRow(row)
                    files[p.split('_')[0]] = fi # On stocke l'ID (ex: F00)

                elif item_type == 'sheet':
                    # Recréation de la feuille
                    file_id = p.split('_')[0]
                    if file_id in files:
                        si = QtGui.QStandardItem(data.get('name', 'Feuille'))
                        si.setData(data, QtCore.Qt.UserRole)
                        row = [si, QtGui.QStandardItem("SHEET")]
                        files[file_id].appendRow(row)
                        sheets[p[:6]] = si # On stocke l'ID (ex: F00_S00)

                elif item_type == 'instruction':
                    sheet_id = p[:6]
                    if sheet_id in sheets:
                        c0 = QtGui.QStandardItem("📥 Plage")
                        # On utilise notre nouvelle fonction de résumé ici
                        summary_text = self.format_instruction_summary(data)
                        c1 = QtGui.QStandardItem(summary_text)
                        c2 = QtGui.QStandardItem("RUN")

                        c0.setData(data, QtCore.Qt.UserRole)
                        sheets[sheet_id].appendRow([c0, c1, c2])
            except Exception as e:
                App.Console.PrintWarning(f"Erreur lors du chargement de la propriété {p}: {str(e)}\n")

        # Déplier tout l'arbre par défaut
        self.tree.expandAll()

        h = self.tree.header()
        # 1. On définit le mode sur 'Interactive' pour garder le contrôle
        h.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        h.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        # 2. On impose les largeurs fixes
        h.resizeSection(0, 300) # Colonne Plage
        h.resizeSection(1, 500) # Colonne Dest
        # 3. On laisse la dernière colonne (Statut) absorber tout le reste
        # C'est ce qui empêchera la colonne 'Path' de déborder
        h.setStretchLastSection(True)

    # --- BIBLIOTHÈQUE ---
    # def export_library(self, item):
    #     # On récupère l'item de donnée (colonne 1)
    #     idx0 = item.index().sibling(item.row(), 0)
    #     data_item = self.model.itemFromIndex(idx0).parent().child(item.row(), 1)
    #     data = data_item.data(QtCore.Qt.UserRole)
    #
    #     name, ok = QtWidgets.QInputDialog.getText(self, "💾 Sauvegarder", "Nom du réglage :")
    #     if ok and name:
    #         try:
    #             # Lecture de l'existant
    #             lib = []
    #             if os.path.exists(self.global_json):
    #                 with open(self.global_json, 'r', encoding='utf-8') as f:
    #                     content = f.read()
    #                     if content: lib = json.loads(content)
    #
    #             # Ajout du nouveau réglage
    #             lib.append({"name": name, "data": data})
    #
    #             # Sauvegarde propre
    #             with open(self.global_json, 'w', encoding='utf-8') as f:
    #                 json.dump(lib, f, indent=4)
    #
    #             App.Console.PrintMessage(f"✅ Réglage '{name}' ajouté à la bibliothèque.\n")
    #         except Exception as e:
    #             App.Console.PrintError(f"❌ Erreur export biblio : {str(e)}\n")

    def format_instruction_summary(self, data):
        """ Génère le résumé : Dest | Plage Source | Nb Col | Filtres """
        dest = data.get('dest', '?')
        selected = data.get('selected_cols', [])

        # --- CALCUL DE LA PLAGE SOURCE (ex: B:H) ---
        source_range = "?"
        if selected:
            # On récupère le mapping actuel du BOM pour traduire les noms en lettres
            bom = App.ActiveDocument.getObject("BOM")
            if bom:
                # Création d'un mapping temporaire Nom -> Lettre
                _, end_cell = bom.getNonEmptyRange()
                last_col_idx, _ = self.addr_to_pos(end_cell)
                mapping = {}
                for c in range(last_col_idx + 1):
                    let = get_column_letter(c)
                    h = bom.get(f"{let}1")
                    if h: mapping[h] = let

                # On récupère les lettres des colonnes sélectionnées présentes dans le BOM
                letters = [mapping[name] for name in selected if name in mapping]
                if letters:
                    # On trie pour avoir la première et la dernière lettre (ordre alphabétique A, B, C...)
                    letters.sort(key=lambda x: (len(x), x))
                    source_range = f"{letters[0]}:{letters[-1]}"

        # --- FILTRES ---
        parents = data.get('filter_p', [])
        matieres = data.get('filter_m', [])
        txt_p = f"P:{','.join(parents)}" if parents else "P:Tous"
        txt_m = f"M:{','.join(matieres)}" if matieres else "M:Toutes"

        # Retourne le format : "A2 | B:H | 9 col. | P:Socle | M:Chêne"
        return f"{dest}  |  {source_range}  |  {len(selected)} col.  |  {txt_p}  |  {txt_m}"

    def export_library(self, item):
        # 1. On force la récupération de la colonne 0 (là où est le dictionnaire)
        idx0 = item.index().sibling(item.row(), 0)
        instruction_item = self.model.itemFromIndex(idx0)

        # 2. On récupère le dictionnaire de données
        data = instruction_item.data(QtCore.Qt.UserRole)

        # Sécurité : on vérifie que c'est bien un dictionnaire d'instruction
        if not data or not isinstance(data, dict):
            App.Console.PrintError("❌ Impossible d'exporter : données invalides.\n")
            return

        name, ok = QtWidgets.QInputDialog.getText(self, "💾 Sauver dans la Biblio", "Nom du réglage :")
        if ok and name:
            try:
                lib = []
                if os.path.exists(self.global_json):
                    with open(self.global_json, 'r', encoding='utf-8') as f:
                        try:
                            lib = json.load(f)
                            if not isinstance(lib, list): lib = []
                        except:
                            lib = []

                # On ajoute l'entrée avec le format 'name' + 'data'
                # On fait une copie du dictionnaire pour éviter les références directes
                lib.append({
                    "name": name,
                    "data": data.copy()
                })

                with open(self.global_json, 'w', encoding='utf-8') as f:
                    json.dump(lib, f, indent=4)

                App.Console.PrintMessage(f"✅ Sauvegardé dans la bibliothèque : {name}\n")
            except Exception as e:
                App.Console.PrintError(f"❌ Erreur export biblio : {str(e)}\n")

    def import_library(self, sheet_item):
        try:
            if not os.path.exists(self.global_json):
                App.Console.PrintWarning("La bibliothèque est vide (fichier inexistant).\n")
                return

            with open(self.global_json, 'r', encoding='utf-8') as f:
                lib = json.load(f)

            if not lib:
                App.Console.PrintWarning("La bibliothèque est vide.\n")
                return

            # On extrait les noms pour la liste de choix
            names = [entry['name'] for entry in lib if 'name' in entry]

            if not names:
                App.Console.PrintWarning("Aucun réglage valide trouvé dans le JSON.\n")
                return

            sel, ok = QtWidgets.QInputDialog.getItem(self, "📥 Importer", "Choisir un réglage :", names, 0, False)

            if ok and sel:
                # On retrouve la donnée correspondante au nom choisi
                selected_data = next(item['data'] for item in lib if item['name'] == sel)
                # On crée l'instruction sous la feuille
                self.add_instruction(sheet_item, data=selected_data)
                self.sync_to_varset() # On n'oublie pas de sauver dans FreeCAD
                App.Console.PrintMessage(f"✅ Réglage '{sel}' importé.\n")

        except Exception as e:
            App.Console.PrintError(f"❌ Erreur import biblio : {str(e)}\n")

    # --- ACTIONS ---
    def run_instruction(self, item):
        # 1. On remonte TOUJOURS à la colonne 0 pour avoir les données
        idx0 = item.index().sibling(item.row(), 0)
        node = self.model.itemFromIndex(idx0)

        # 2. Récupération sécurisée du dictionnaire d'instruction (Colonne 0)
        data = node.data(QtCore.Qt.UserRole)
        if not data or not isinstance(data, dict):
            App.Console.PrintError("❌ Erreur : Données d'instruction introuvables sur cette ligne.\n")
            return

        # 3. Récupération de la hiérarchie
        sheet_item = node.parent()
        file_item = sheet_item.parent() if sheet_item else None

        if not sheet_item or not file_item:
            App.Console.PrintError("❌ Erreur : Structure de l'arbre corrompue.\n")
            return

        sheet_name = sheet_item.text()

        # Le chemin du fichier est dans le UserRole du parent de la feuille
        file_data = file_item.data(QtCore.Qt.UserRole)
        file_path = file_data.get('path') if isinstance(file_data, dict) else file_data

        # 4. Extraction des données du BOM FreeCAD
        bom = App.ActiveDocument.getObject("BOM")
        if not bom:
            App.Console.PrintError("❌ Erreur : Objet 'BOM' introuvable dans le document FreeCAD.\n")
            return

        try:
            start_cell, end_cell = bom.getNonEmptyRange()
            last_column, last_row = self.addr_to_pos(end_cell)

            # Mapping des colonnes (ex: {"UID": "A", "Libelle": "B"})
            mapping = {}
            for c in range(last_column + 1):
                col_let = get_column_letter(c)
                header = bom.get(f"{col_let}1")
                if header: mapping[header] = col_let

            d_col, d_row = self.addr_to_pos(data['dest'])
            rows = []

            # 5. Boucle de filtrage et lecture
            for r in range(2, last_row + 1):
                # Filtres (Parent en B, Matière en H par défaut)
                val_p = str(bom.get(f"B{r}") or "")
                val_m = str(bom.get(f"H{r}") or "")

                match_p = not data.get('filter_p') or val_p in data['filter_p']
                match_m = not data.get('filter_m') or val_m in data['filter_m']

                if match_p and match_m:
                    row_vals = []
                    for col_name in data['selected_cols']:
                        if col_name in mapping:
                            col_let = mapping[col_name]
                            try:
                                val = bom.get(f"{col_let}{r}")
                            except:
                                val=""
                            row_vals.append(val if val is not None else "")
                        else:
                            row_vals.append("") # Colonne demandée absente du BOM
                    rows.append(row_vals)

            # 6. Préparation du signal pour le Watcher
            payload = {
                "file_path": file_path,
                "sheet_name": sheet_name,
                "start_col": d_col,
                "start_row": d_row,
                "rows": rows
            }

            trigger_path = "/home/matthou/snap/freecad/common/bridge_trigger.json"

            with open(trigger_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
                f.flush()
                os.fsync(f.fileno())

            App.Console.PrintMessage(f"✅ Signal envoyé : {len(rows)} lignes vers {sheet_name}\n")

        except Exception as e:
            App.Console.PrintError(f"❌ Erreur lors de l'exécution : {str(e)}\n")

    # def run_instruction(self, item):
    #     idx0 = item.index().sibling(item.row(), 0)
    #     node = self.model.itemFromIndex(idx0)
    #     data = node.parent().child(item.row(), 1).data(QtCore.Qt.UserRole)
    #     sheet_name = node.parent().text()
    #     file_path = node.parent().parent().data(QtCore.Qt.UserRole)
    #     bom = App.ActiveDocument.getObject("BOM")
    #     if not bom: return
    #     start_cell, end_cell = bom.getNonEmptyRange()
    #     last_column, last_row = self.addr_to_pos(end_cell)
    #     # Mapping des colonnes basé sur la première ligne
    #     mapping = {}
    #     for c in range(last_column + 1):
    #         header = bom.get(f"{get_column_letter(c)}1")
    #         if header: mapping[header] = get_column_letter(c)
    #     # print(f"mapping {mapping}")
    #     d_col, d_row = self.addr_to_pos(data['dest'])
    #     rows = []
    #     for r in range(2, last_row + 1):
    #         if (not data['filter_p'] or data['filter_p'].lower() in bom.get(f"B{r}").lower()) and \
    #            (not data['filter_m'] or data['filter_m'].lower() in bom.get(f"H{r}").lower()):
    #             row_vals = []
    #             for col_name in data['selected_cols']:
    #                 # print(f"col_name {col_name}")
    #                 col_let = mapping[col_name]
    #                 # print(f"{col_let}{r}")
    #                 try:
    #                     val = bom.get(f"{col_let}{r}")
    #                 except:
    #                     val=""
    #                 row_vals.append(val)
    #             rows.append(row_vals)
    #     payload = {
    #                 "file_path": file_path,
    #                 "sheet_name": sheet_name,
    #                 "start_col": d_col,
    #                 "start_row": d_row,
    #                 "rows": rows
    #                 }
    #
    #     # print(f"{payload}")
    #     script_path = os.path.join(App.getUserMacroDir(), "bridge_calc.py")
    #     # print(f"script_path {script_path}")
    #     json_payload = json.dumps(payload)
    #     # print(f"json_payload {json_payload}")
    #
    #     # --- LOGIQUE DE DIAGNOSTIC AVANCÉ ---
    #     # try:
    #     #     # On utilise le chemin absolu de python3 pour éviter les problèmes de PATH
    #     #     python_bin = "/usr/bin/python3"
    #     #
    #     #     process = subprocess.run(
    #     #         [python_bin, script_path, json_payload],
    #     #         capture_output=True,
    #     #         text=True
    #     #     )
    #     #
    #     #     # On affiche TOUT dans la console FreeCAD pour comprendre
    #     #     App.Console.PrintMessage(f"--- DEBUG BRIDGE ---\n")
    #     #     App.Console.PrintMessage(f"STDOUT: {process.stdout}\n")
    #     #     App.Console.PrintMessage(f"STDERR: {process.stderr}\n")
    #     #     App.Console.PrintMessage(f"Code retour: {process.returncode}\n")
    #     #     App.Console.PrintMessage(f"--------------------\n")
    #     #
    #     #     if process.returncode != 0:
    #     #         QtWidgets.QMessageBox.warning(self, "Erreur Bridge",
    #     #             f"STDOUT: {process.stdout}\nSTDERR: {process.stderr}")
    #     #
    #     # except Exception as e:
    #     #     App.Console.PrintError(f"Erreur d'exécution subprocess: {str(e)}\n")
    #
    #     # --- LOGIQUE D'ÉVASION DU SNAP ---
    #     # try:
    #     #     # On utilise 'usr/bin/env' avec l'option -u pour supprimer les variables Snap
    #     #     # qui forcent Python à regarder dans le mauvais dossier
    #     #     command = [
    #     #         'usr/bin/env',
    #     #         '-u', 'PYTHONPATH',
    #     #         '-u', 'PYTHONHOME',
    #     #         '-u', 'SNAP',
    #     #         '-u', 'SNAP_NAME',
    #     #         '/usr/bin/python3', script_path, json_payload
    #     #     ]
    #     #
    #     #     # Note : on utilise shell=False pour la sécurité,
    #     #     # mais on pointe vers le binaire absolu
    #     #     process = subprocess.run(
    #     #         command,
    #     #         capture_output=True,
    #     #         text=True,
    #     #         executable='/usr/bin/env'
    #     #     )
    #     #
    #     #     App.Console.PrintMessage(f"--- DEBUG ÉVASION ---\n")
    #     #     App.Console.PrintMessage(f"STDOUT: {process.stdout}\n")
    #     #     App.Console.PrintMessage(f"STDERR: {process.stderr}\n")
    #     #
    #     #     if "Module UNO chargé avec succès" in process.stdout:
    #     #         App.Console.PrintMessage("🚀 Évasion réussie : LibreOffice contacté !\n")
    #     # except Exception as e:
    #     #     App.Console.PrintError(f"Erreur d'exécution subprocess: {str(e)}\n")
    #     # Chemin où FreeCAD a le droit d'écrire
    #     trigger_path = "/home/matthou/snap/freecad/common/bridge_trigger.json"
    #
    #     # try:
    #     #     with open(trigger_path, "w", encoding="utf-8") as f:
    #     #         json.dump(payload, f)
    #     #     App.Console.PrintMessage("✅ Signal envoyé au surveillant externe (Calc).\n")
    #     # except Exception as e:
    #     #     App.Console.PrintError(f"❌ Erreur d'écriture du signal : {str(e)}\n")
    #
    #     try:
    #         # Utiliser un fichier temporaire puis le renommer est la méthode la plus sûre
    #         # mais ici un 'with' avec flush suffit généralement
    #         with open(trigger_path, "w", encoding="utf-8") as f:
    #             json.dump(payload, f)
    #             f.flush()
    #             os.fsync(f.fileno()) # Force l'écriture sur le disque
    #         App.Console.PrintMessage("✅ Signal envoyé.\n")
    #     except Exception as e:
    #         App.Console.PrintError(f"❌ Erreur : {str(e)}\n")

    # def context_menu(self, pos):
    #     idx = self.tree.indexAt(pos)
    #     if not idx.isValid(): return
    #     item = self.model.itemFromIndex(idx.sibling(idx.row(), 0))
    #     lvl = self.get_lvl(item)
    #     menu = QtWidgets.QMenu()
    #     if lvl == 0:
    #         menu.addAction("📄 Ajouter Feuille").triggered.connect(lambda: self.add_sheet(item))
    #     elif lvl == 1:
    #         menu.addAction("➕ Ajouter Plage").triggered.connect(lambda: self.add_instruction(item))
    #         menu.addAction("📥 Importer Biblio").triggered.connect(lambda: self.import_library(item))
    #     elif lvl == 2:
    #         menu.addAction("▶️ EXÉCUTER").triggered.connect(lambda: self.run_instruction(item))
    #         menu.addAction("⚙️ Éditer").triggered.connect(lambda: self.edit_instruction_range(item))
    #         menu.addAction("💾 Sauver Biblio").triggered.connect(lambda: self.export_library(item))
    #     menu.addSeparator()
    #     menu.addAction("🗑️ Supprimer").triggered.connect(lambda: self.delete_item(item))
    #     menu.exec_(self.tree.viewport().mapToGlobal(pos))

    def context_menu(self, point):
        index = self.tree.indexAt(point)
        if not index.isValid(): return

        # 2. FORCE LA COLONNE 0 : Peu importe si tu cliques sur la col 1 ou 2,
        # on récupère l'item de la première colonne de la même ligne.
        index_col0 = index.sibling(index.row(), 0)
        item = self.model.itemFromIndex(index_col0)
        data = item.data(QtCore.Qt.UserRole)
        # 3. Récupération des données
        data = item.data(QtCore.Qt.UserRole)

        # Sécurité : Si data est None, on tente une déduction par la hiérarchie
        if data is None:
            if not item.parent(): item_type = 'file'
            elif not item.parent().parent(): item_type = 'sheet'
            else: item_type = 'instruction'
            data = {'type': item_type}

        menu = QtWidgets.QMenu()

        if data.get('type') == 'file':
            # Menu pour le fichier complet
            action_run_all = menu.addAction("🚀 Tout lancer (Fichier)")
            action_run_all.triggered.connect(lambda: self.run_all(item))
            menu.addSeparator()
            action_add_sheet = menu.addAction("📄 Ajouter Feuille")
            action_add_sheet.triggered.connect(lambda: self.add_sheet(item))

        elif data.get('type') == 'sheet':
            # Menu pour une feuille
            action_run_sheet = menu.addAction("🚀 Tout lancer (Feuille)")
            action_run_sheet.triggered.connect(lambda: self.run_all(item))
            menu.addSeparator()
            action_add_inst = menu.addAction("➕ Ajouter Instruction")
            action_add_inst.triggered.connect(lambda: self.add_instruction(item))
            action_import = menu.addAction("📥 Importer Biblio")
            action_import.triggered.connect(lambda: self.import_library(item))

        elif data.get('type') == 'instruction':
            # Menu pour une instruction seule
            menu.addAction("⚙️ Éditer").triggered.connect(lambda: self.edit_instruction_range(item))
            action_run = menu.addAction("▶️ Lancer l'instruction")
            action_run.triggered.connect(lambda: self.run_instruction(item))
            action_save = menu.addAction("💾 Sauver Biblio")
            action_save.triggered.connect(lambda: self.export_library(item))
            action_del = menu.addAction("🗑️ Supprimer")
            action_del.triggered.connect(lambda: self.delete_item(item))

        menu.exec_(self.tree.viewport().mapToGlobal(point))

    # --- HELPERS ---
    def edit_instruction_range(self, item):
        idx0 = item.index().sibling(item.row(), 0)
        c0 = self.model.itemFromIndex(idx0)
        c1 = c0.parent().child(item.row(), 1)
        data = c0.data(QtCore.Qt.UserRole)

        # --- RÉCUPÉRATION DES VALEURS UNIQUES DU BOM ---
        bom = App.ActiveDocument.getObject("BOM")
        unique_parents = set()
        unique_materials = set()

        if bom:
            # On scanne le BOM pour remplir les sets (on commence ligne 2)
            _, end_cell = bom.getNonEmptyRange()
            _, last_row = self.addr_to_pos(end_cell)
            for r in range(2, last_row + 1):
                p = bom.get(f"B{r}")
                m = bom.get(f"H{r}")
                if p: unique_parents.add(str(p))
                if m: unique_materials.add(str(m))

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Configuration de l'export")
        dialog.setMinimumWidth(500)
        lay = QtWidgets.QVBoxLayout(dialog)

        # 1. Liste des colonnes à exporter
        lay.addWidget(QtWidgets.QLabel("<b>1. Colonnes à exporter :</b>"))
        lw_cols = QtWidgets.QListWidget()
        all_cols = list(HEADERS.values()) + list(OP_PROPERTIES.values())
        for c in all_cols:
            it = QtWidgets.QListWidgetItem(c)
            it.setFlags(it.flags() | QtCore.Qt.ItemIsUserCheckable)
            it.setCheckState(QtCore.Qt.Checked if c in data.get('selected_cols', []) else QtCore.Qt.Unchecked)
            lw_cols.addItem(it)
        lay.addWidget(lw_cols)

        # 2. Filtre Parents (Multi-sélection)
        lay.addWidget(QtWidgets.QLabel("<b>2. Filtrer par Parents (Ctrl+Clic pour plusieurs) :</b>"))
        lw_p = QtWidgets.QListWidget()
        lw_p.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        for p in sorted(list(unique_parents)):
            it = lw_p.addItem(p)
            if p in data.get('filter_p', []):
                lw_p.item(lw_p.count()-1).setSelected(True)
        lay.addWidget(lw_p)

        # 3. Filtre Matières (Multi-sélection)
        lay.addWidget(QtWidgets.QLabel("<b>3. Filtrer par Matières :</b>"))
        lw_m = QtWidgets.QListWidget()
        lw_m.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        for m in sorted(list(unique_materials)):
            lw_m.addItem(m)
            if m in data.get('filter_m', []):
                lw_m.item(lw_m.count()-1).setSelected(True)
        lay.addWidget(lw_m)

        # 4. Destination
        dest_in = QtWidgets.QLineEdit(data.get('dest', 'A2'))
        lay.addWidget(QtWidgets.QLabel("<b>4. Destination (ex: A2) :</b>"))
        lay.addWidget(dest_in)

        btn = QtWidgets.QPushButton("✅ Enregistrer")
        btn.clicked.connect(dialog.accept)
        lay.addWidget(btn)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data.update({
                'type': 'instruction',
                'selected_cols': [lw_cols.item(i).text() for i in range(lw_cols.count()) if lw_cols.item(i).checkState() == QtCore.Qt.Checked],
                'filter_p': [i.text() for i in lw_p.selectedItems()],
                'filter_m': [i.text() for i in lw_m.selectedItems()],
                'dest': dest_in.text()
            })

            c0.setData(data, QtCore.Qt.UserRole)

            # --- MISE À JOUR DE L'AFFICHAGE EN COLONNE 1 ---
            if c1:
                c1.setText(self.format_instruction_summary(data))

            self.sync_to_varset()

    def add_file(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Calc", "", "Calc (*.ods)")
        if p:
            # On crée un dictionnaire propre pour le fichier
            data = {"type": "file", "path": p}
            fi = QtGui.QStandardItem(os.path.basename(p))
            fi.setData(data, QtCore.Qt.UserRole) # On stocke le dict ici

            # On ajoute la ligne (3 colonnes)
            self.model.appendRow([fi, QtGui.QStandardItem(p), QtGui.QStandardItem("FILE")])
            self.sync_to_varset()
            self.tree.viewport().update() # Force Qt à redessiner le widget

    def add_sheet(self, file_item):
        n, ok = QtWidgets.QInputDialog.getText(self, "Feuille", "Nom :")
        if ok and n:
            # On crée un dictionnaire pour la feuille
            data = {"type": "sheet", "name": n}
            si = QtGui.QStandardItem(n)
            si.setData(data, QtCore.Qt.UserRole) # Important !

            file_item.appendRow([si, QtGui.QStandardItem("SHEET")])
            self.sync_to_varset()
            self.tree.viewport().update() # Force Qt à redessiner le widget

    def add_instruction(self, sheet_item, data=None):
        if not data:
            data = {"type": "instruction", "selected_cols": ["UID", "Libelle"], "dest": "A2", "filter_p": "", "filter_m": ""}
        else:
            # On s'assure que le type est présent si on importe de la biblio
            data["type"] = "instruction"

        c0 = QtGui.QStandardItem("📥 Plage")
        c1 = QtGui.QStandardItem(f"Dest: {data['dest']}")

        # On stocke le dictionnaire dans la COLONNE 0 pour que le clic droit le trouve
        c0.setData(data, QtCore.Qt.UserRole)

        sheet_item.appendRow([c0, c1, QtGui.QStandardItem("RUN")])  #  PRÊT

        # --- MISE À JOUR DE L'AFFICHAGE EN COLONNE 1 ---
        if c1:
            c1.setText(self.format_instruction_summary(data))

        self.sync_to_varset()
        self.tree.viewport().update() # Force Qt à redessiner le widget

    def delete_item(self, item): (item.parent() or self.model).removeRow(item.row()); self.sync_to_varset()

    def get_lvl(self, item):
        l = 0
        while item.parent(): l += 1; item = item.parent()
        return l
    def addr_to_pos(self, addr):
        m = re.match(r"([A-Z]+)([0-9]+)", addr.upper())
        if not m: return 0, 0
        c = 0
        for char in m.group(1): c = c * 26 + (ord(char) - ord('A') + 1)
        return c - 1, int(m.group(2)) - 1

    # def start_libreoffice_listen(self): subprocess.Popen('soffice --accept="socket,host=localhost,port=2002;urp;"', shell=True)

    def manage_library(self):
        if not os.path.exists(self.global_json):
            QtWidgets.QMessageBox.information(self, "Biblio", "La bibliothèque est vide.")
            return

        try:
            with open(self.global_json, 'r', encoding='utf-8') as f:
                lib = json.load(f)

            # On filtre pour n'avoir que les entrées valides
            valid_entries = [e for e in lib if isinstance(e, dict) and 'name' in e]

            if not valid_entries:
                QtWidgets.QMessageBox.information(self, "Biblio", "Aucun réglage valide à supprimer.")
                return

            # Création d'une fenêtre de gestion simple
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Gérer la Bibliothèque")
            dialog.setMinimumSize(400, 300)
            layout = QtWidgets.QVBoxLayout(dialog)

            list_widget = QtWidgets.QListWidget()
            for e in valid_entries:
                list_widget.addItem(e['name'])
            layout.addWidget(list_widget)

            btn_delete = QtWidgets.QPushButton("🗑️ Supprimer la sélection")
            layout.addWidget(btn_delete)

            def do_delete():
                selected_items = list_widget.selectedItems()
                if not selected_items: return

                for item in selected_items:
                    name_to_del = item.text()
                    # On filtre la liste pour enlever l'élément
                    nonlocal valid_entries
                    valid_entries = [e for e in valid_entries if e['name'] != name_to_del]
                    # On retire de la liste visuelle
                    list_widget.takeItem(list_widget.row(item))

                # Sauvegarde immédiate du fichier JSON
                with open(self.global_json, 'w', encoding='utf-8') as f:
                    json.dump(valid_entries, f, indent=4)
                App.Console.PrintMessage("✅ Bibliothèque mise à jour.\n")

            btn_delete.clicked.connect(do_delete)
            dialog.exec_()

        except Exception as e:
            App.Console.PrintError(f"❌ Erreur gestion biblio : {str(e)}\n")

    # def run_all(self, item):
    #     # On détermine si on a cliqué sur un fichier ou une feuille
    #     instructions = []
    #
    #     if item.data(QtCore.Qt.UserRole).get('type') == 'file':
    #         # On récupère toutes les instructions de toutes les feuilles
    #         for i in range(item.rowCount()):
    #             sheet_item = item.child(i)
    #             for j in range(sheet_item.rowCount()):
    #                 instructions.append(sheet_item.child(j))
    #     else:
    #         # On récupère seulement les instructions de la feuille sélectionnée
    #         for j in range(item.rowCount()):
    #             instructions.append(item.child(j))
    #
    #     if not instructions:
    #         App.Console.PrintWarning("Aucune instruction trouvée.\n")
    #         return
    #
    #     App.Console.PrintMessage(f"⏳ Lancement de {len(instructions)} instructions...\n")
    #
    #     for inst in instructions:
    #         self.run_instruction(inst)
    #         # Petit délai pour laisser le temps au watcher de traiter le fichier
    #         # 0.5s est généralement suffisant pour le système de fichier
    #         import time
    #         time.sleep(2)
    #
    #     App.Console.PrintMessage("✅ Toutes les instructions ont été envoyées.\n")

    def run_all(self, item):
        import time
        # On détermine si on a cliqué sur un fichier ou une feuille
        instructions = []
        trigger_path = "/home/matthou/snap/freecad/common/bridge_trigger.json"

        # 1. Collecte des instructions
        if item.data(QtCore.Qt.UserRole).get('type') == 'file':
            for i in range(item.rowCount()):
                sheet_item = item.child(i)
                for j in range(sheet_item.rowCount()):
                    instructions.append(sheet_item.child(j))
        else:
            for j in range(item.rowCount()):
                instructions.append(item.child(j))

        if not instructions:
            App.Console.PrintWarning("Aucune instruction trouvée.\n")
            return

        App.Console.PrintMessage(f"⏳ Lancement séquentiel de {len(instructions)} instructions...\n")

        for idx, inst in enumerate(instructions):
            # --- LOGIQUE D'ATTENTE ---
            # Avant d'envoyer l'instruction, on vérifie si le fichier précédent est traité
            max_wait = 30  # Secondes
            waited = 0
            while os.path.exists(trigger_path):
                if waited == 0:
                    App.Console.PrintWarning(f"  -> Attente libération du canal pour l'instruction {idx+1}...\n")

                time.sleep(0.5)
                waited += 0.5

                if waited >= max_wait:
                    App.Console.PrintError(f"❌ STOP : Le bridge met trop de temps (timeout). Processus arrêté.\n")
                    return

            # --- EXÉCUTION ---
            # Le canal est libre, on peut appeler run_instruction
            self.run_instruction(inst)

            # On laisse un tout petit délai de sécurité pour que le fichier apparaisse sur le disque
            time.sleep(0.2)

        App.Console.PrintMessage("✅ Toutes les instructions ont été traitées par le bridge.\n")

if __name__ == "__main__":
    d = BOMToSpreadsheet()
    d.load_from_varset() # Assurez-vous que le chargement est fait
    d.tree.expandAll()    # <--- Déplie tout l'arbre
    d.show()
