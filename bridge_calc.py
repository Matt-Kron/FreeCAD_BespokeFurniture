# import sys, json, os
#
# # --- AJOUT FORCÉ DES CHEMINS LIBREOFFICE ---
# def add_uno_paths():
#     extra_paths = [
#         "/usr/lib/python3/dist-packages",
#         "/usr/lib/libreoffice/program",
#         "/usr/lib64/libreoffice/program" # Pour certaines distros
#     ]
#     for p in extra_paths:
#         if os.path.exists(p) and p not in sys.path:
#             sys.path.append(p)
#
#     # Définit les variables d'environnement requises par UNO
#     if "/usr/lib/libreoffice/program" not in os.environ.get("PATH", ""):
#         os.environ["PATH"] += os.pathsep + "/usr/lib/libreoffice/program"
#
# add_uno_paths()
#
# print("--- DÉBUT DU PONT ---")
#
# try:
#     import uno
#     from com.sun.star.beans import PropertyValue
#     print("Module UNO chargé avec succès")
# except ImportError as e:
#     print(f"ERREUR : Module UNO introuvable. {e}")
#     print(f"PATH actuel : {sys.path}") # Pour debug
#     sys.exit(1)

import sys, json, os

# --- AJOUT DES CHEMINS (gardé pour le fonctionnement Snap/AppImage) ---
def add_uno_paths():
    extra_paths = ["/usr/lib/python3/dist-packages", "/usr/lib/libreoffice/program"]
    for p in extra_paths:
        if os.path.exists(p) and p not in sys.path:
            sys.path.append(p)
    os.environ["PATH"] += os.pathsep + "/usr/lib/libreoffice/program"

add_uno_paths()

def run_bridge(input_data):
    try:
        if os.path.exists(input_data):
            with open(input_data, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = json.loads(input_data)

        import uno
        local_ctx = uno.getComponentContext()
        resolver = local_ctx.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local_ctx)
        ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
        desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

        file_url = "file://" + os.path.abspath(data['file_path']).replace("\\", "/")

        # Recherche du document ouvert
        components = desktop.getComponents().createEnumeration()
        doc = None
        while components.hasMoreElements():
            c = components.nextElement()
            if hasattr(c, "getLocation") and c.getLocation() == file_url:
                doc = c
                break

        if doc is None:
            doc = desktop.loadComponentFromURL(file_url, "_blank", 0, ())

        sheet = doc.getSheets().getByName(data['sheet_name'])

        # --- LOGIQUE DE PRÉPARATION DU TABLEAU ---
        rows_data = data['rows']
        num_rows = len(rows_data)
        if num_rows == 0: return

        # On s'assure que toutes les lignes ont la même longueur (indispensable pour setDataArray)
        num_cols = max(len(r) for r in rows_data)

        formatted_data = []
        for r in rows_data:
            new_row = []
            for i in range(num_cols):
                val = r[i] if i < len(r) else "" # Comble si une cellule manque
                try:
                    # Conversion nombre
                    new_row.append(float(str(val).replace(',', '.')))
                except:
                    # Sinon texte (UNO refuse None, on met une chaîne vide)
                    new_row.append(str(val) if val is not None else "")
            formatted_data.append(tuple(new_row))

        # --- DÉFINITION DE LA PLAGE (C'est ici que l'erreur 4921 se produisait) ---
        # Syntaxe : getCellRangeByPosition(col_debut, lig_debut, col_fin, lig_fin)
        target_range = sheet.getCellRangeByPosition(
            data['start_col'],
            data['start_row'],
            data['start_col'] + num_cols - 1, # Colonne FIN
            data['start_row'] + num_rows - 1  # Ligne FIN
        )

        target_range.setDataArray(tuple(formatted_data))
        print(f"✅ Export instantané réussi ({num_rows} lignes).")

    except Exception as e:
        print(f"ERREUR CRITIQUE : {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_bridge(sys.argv[1])
