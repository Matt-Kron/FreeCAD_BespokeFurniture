import FreeCAD

from FreeCAD_BespokeFurniture.rpc_server.meuble_simplifie_geometrie import get_json_data_from_container, run as meuble_simplifie_geometrie_run

TOOL_META = {
        "name": "get_geo_structure",
        "description": """Récupère la géométrie simplifiée du meuble du document actif.
                    Cet outil fournit l'organisation fonctionnelle du meuble, comment il est découpé en plusieurs espaces de rangements.
                    Les alvéoles sont les espaces élémentaires de rangement réels.
                    Les segments sont la représentation simplifiée de la structure qui forme les alvéoles. C'est sur eux qu'il faut agir pour obtenir les alvéoles conformes à la demande utilisateur""",
        "parameters": {},
}

def run():
    doc = FreeCAD.ActiveDocument
    if not doc:
        raise ValueError(f"Aucun document actif")
    meuble_simplifie_geometrie_run()
    geo_struct = get_json_data_from_container(doc)
    if not geo_struct:
        raise ValueError(f"Erreur, la géométrie simplifiée n'a pas pu être construite ou récupérée")
    return {
        "status": "success",
        "document": doc.Name,
        "geo_structure": geo_struct
    }
