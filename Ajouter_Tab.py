# import os, ast
#
# nom_fichier = "config_macro_caisson.cfg"
# repertoire_macros = FreeCAD.getUserMacroDir()
# chemin_complet_fichier = os.path.join(repertoire_macros, nom_fichier)
# monDoc = FreeCAD.ActiveDocument
#
# liste_objets = {"Tablette caisson p":"Tablette_caisson_p",
#                 "Tablette caisson b":"Tablette_caisson_b",
#                 "Tablette caisson":"Tablette_caisson",
#                 "Box042":"Tablette_caisson_bxr",
#                 "tablette caisson rainuree":"Tablette_caisson_rainure"
#                 }
#
# OBJ_NAME = 0
# OBJ_TYPE = 1
# PROP_NAME = 2
# PROP_GROUP = 3
# PROP_TYPE = 4
# PROP_VALUE_EXP = 5
# PROP_CONTENU = 6
#
# def lire_configuration_caisson(nom_fichier="config_macro_caisson.cfg"):
#     """
#     Lit le fichier de configuration de la macro et retourne un dictionnaire de paramètres.
#     """
#
#     # 1. Construire le chemin complet du fichier
#     repertoire_macros = FreeCAD.getUserMacroDir()
#     chemin_complet_fichier = os.path.join(repertoire_macros, nom_fichier)
#
#     config_data = []
#
#     try:
#         # 2. Ouvrir le fichier en mode lecture ('r')
#         with open(chemin_complet_fichier, 'r') as f:
#
#             # 3. Parcourir chaque ligne du fichier
#             for ligne in f:
#
#                 # Nettoyer la ligne (enlever les espaces de début/fin)
#                 ligne = ligne.strip()
#
#                 # Ignorer les lignes vides ou les lignes de commentaire (si vous en ajoutez,
#                 # par exemple avec '#' ou ';')
#                 if not ligne or ligne.startswith('#') or ligne.startswith(';'):
#                     continue
#
#                 # objet | type objet | propriété | groupe de la propriété | type de la propriété | type valeur ou expression | valeur ou expression
#                 # 4. Rechercher le séparateur ' | '
#                 if '|' in ligne:
#
#                     element = ligne.split('|')
#                     config_data.append(element)
#
#
#         print(f"✅ Configuration chargée avec succès depuis : {chemin_complet_fichier}")
#         return config_data
#
#     except FileNotFoundError:
#         print(f"❌ Le fichier de configuration est introuvable à : {chemin_complet_fichier}")
#         print("   Retourne les paramètres par défaut ou un dictionnaire vide.")
#         return {}
#     except Exception as e:
#         print(f"❌ Erreur inattendue lors de la lecture du fichier : {e}")
#         return {}
#
# def AjouterMontantIntermediaire():
#     liste_elements = lire_configuration_caisson()
#     elements_Mti = []
#     for ele in liste_elements:
#         if "Tablette_caisson" in ele[OBJ_NAME]:
#             elements_Mti.append(ele)
#     piece = monDoc.addObject('App::Part', "Tablette_caisson_p")
#     piece.Label = piece.Name.replace("_", " ")
#     corps = monDoc.addObject('PartDesign::Body',"Tablette_caisson_b")
#     corps.Label = corps.Name.replace("_", " ")
#     piece.addObject(corps)
#     nom = "Tablette_caisson"
#     etiquette = nom.replace("_", " ")
#     forme = monDoc.addObject('PartDesign::AdditiveBox',nom)
#     forme.Label = nom.replace("_", " ")
#     corps.addObject(forme)
#     if etiquette != forme.Label:
#         for ele in elements_Mti:
#             i = elements_Mti.index(ele)
#             elements_Mti[i][PROP_CONTENU] = elements_Mti[i][PROP_CONTENU].replace(f"<<{etiquette}>>",f"<<{forme.Label}>>")
#     for ele in elements_Mti:
#         if ele[OBJ_NAME] == nom:
#             if ele[PROP_VALUE_EXP] == "value":
#                 forme.addProperty(ele[PROP_TYPE], ele[PROP_NAME], ele[PROP_GROUP])
#                 if ele[PROP_TYPE] == "App::PropertyLinkGlobal":
#                     setattr(forme, ele[PROP_NAME], monDoc.getObjectsByLabel(ele[PROP_CONTENU])[0])
#                 elif ele[PROP_TYPE] == "App::PropertyEnumeration":
#                     setattr(forme, ele[PROP_NAME], ast.literal_eval(ele[PROP_CONTENU]))
#                 elif ele[PROP_TYPE] == "App::PropertyBool":
#                     setattr(forme, ele[PROP_NAME], 'True' == ele[PROP_CONTENU])
#                     # print(f"forme: {ele[OBJ_NAME]}, propriété: {ele[PROP_NAME]}, valeur: {ele[PROP_CONTENU]}, valeur bool(): {bool(ele[PROP_CONTENU])}")
#                 else:
#                     setattr(forme, ele[PROP_NAME], ele[PROP_CONTENU])
#     for ele in elements_Mti:
#         if ele[OBJ_NAME] == nom:
#             if ele[PROP_VALUE_EXP] == "expression":
#                 # if "Placement" in ele[PROP_NAME]:
#                 #     forme.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])
#                 # elif "AttachmentOffset" in ele[PROP_NAME]:
#                 #     forme.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])
#                 # else
#                 forme.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])
#     nom = "Tablette_caisson_bxr"
#     forme = monDoc.addObject('PartDesign::SubtractiveBox',nom)
#     forme.Label = nom.replace("_", " ")
#     corps.addObject(forme)
#     forme.AttachmentSupport = [(monDoc.getObject(corps.Origin.OriginFeatures[0].Name),'')]
#     forme.MapMode = 'ObjectXY'
#     subobj = monDoc.getObject(forme.Name)
#     for ele in elements_Mti:
#         if ele[OBJ_NAME] == nom:
#             if ele[PROP_VALUE_EXP] == "value":
#                 forme.addProperty(ele[PROP_TYPE], ele[PROP_NAME], ele[PROP_GROUP])
#                 if ele[PROP_TYPE] == "App::PropertyLinkGlobal":
#                     setattr(forme, ele[PROP_NAME], monDoc.getObjectsByLabel(ele[PROP_CONTENU])[0])
#                 elif ele[PROP_TYPE] == "App::PropertyEnumeration":
#                     setattr(forme, ele[PROP_NAME], ast.literal_eval(ele[PROP_CONTENU]))
#     for ele in elements_Mti:
#         if ele[OBJ_NAME] == nom:
#             if ele[PROP_VALUE_EXP] == "expression":
#                 forme.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])
#     nom = "Tablette_caisson_rainure"
#     forme = monDoc.addObject('PartDesign::LinearPattern',nom)
#     forme.Label = nom.replace("_", " ")
#     forme.Originals = monDoc.getObject(subobj.Name)
#     forme.Mode = 'length'
#     forme.Occurrences = 2
#     forme.Direction = (monDoc.getObject(corps.Origin.OriginFeatures[2].Name),[''])
#     corps.addObject(forme)
#     # forme.AttachmentSupport = [(monDoc.getObject(corps.Origin.OriginFeatures[0].Name),'')]
#     # forme.MapMode = 'ObjectXY'
#     for ele in elements_Mti:
#         if ele[OBJ_NAME] == nom:
#             if ele[PROP_VALUE_EXP] == "value":
#                 forme.addProperty(ele[PROP_TYPE], ele[PROP_NAME], ele[PROP_GROUP])
#                 if ele[PROP_TYPE] == "App::PropertyLinkGlobal":
#                     setattr(forme, ele[PROP_NAME], monDoc.getObjectsByLabel(ele[PROP_CONTENU])[0])
#                 elif ele[PROP_TYPE] == "App::PropertyEnumeration":
#                     setattr(forme, ele[PROP_NAME], ast.literal_eval(ele[PROP_CONTENU]))
#     for ele in elements_Mti:
#         if ele[OBJ_NAME] == nom:
#             if ele[PROP_VALUE_EXP] == "expression":
#                 forme.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])
#     nom = "Tablette_caisson_p"
#     # for ele in elements_Mti:
#     #     if ele[OBJ_NAME] == nom:
#     #         if ele[PROP_VALUE_EXP] == "value":
#     #             setattr(piece, ele[PROP_NAME], ele[PROP_CONTENU])
#     for ele in elements_Mti:
#         if ele[OBJ_NAME] == nom:
#             if ele[PROP_VALUE_EXP] == "expression":
#                 piece.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])
#     nom = "Tablette_caisson_b"
#     # for ele in elements_Mti:
#     #     if ele[OBJ_NAME] == nom:
#     #         if ele[PROP_VALUE_EXP] == "value":
#     #             setattr(corps, ele[PROP_NAME], ele[PROP_CONTENU])
#     for ele in elements_Mti:
#         if ele[OBJ_NAME] == nom:
#             if ele[PROP_VALUE_EXP] == "expression":
#                 corps.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])
#     monDoc.getObjectsByLabel("Caisson")[0].addObject(piece)

# AjouterMontantIntermediaire()
from FreeCAD_BespokeFurniture.add_object_lib import addObjectPartBodyBox

dftStruct = (
                "Tablette caisson p",
                "Tablette caisson b",
                "Tablette caisson",
                "Tablette caisson r1",
                "Tablette caisson rainure",
            )

addObjectPartBodyBox(dftStruct, FreeCAD.ActiveDocument,"Caisson")
