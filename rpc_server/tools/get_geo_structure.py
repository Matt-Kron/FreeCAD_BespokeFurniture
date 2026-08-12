import FreeCAD

from ..meuble_simplifie_geometrie import get_json_data_from_container, run

def get_geo_structure():
    doc = FreeCAD.ActiveDocument
    if not doc:
        raise ValueError(f"Aucun document actif")
    run()
    geo_struct = get_json_data_from_container(doc)
    if not geo_struct:
        raise ValueError(f"Erreur, la géométrie simplifiée n'a pas pu être construite ou récupérée")
    return {
        "status": "success",
        "document": doc.Name,
        "geo_structure": geo_struct
    }
