import os, ast
import FreeCAD as App
from FreeCAD_BespokeFurniture.lib_menuiserie import *

cfg_file = ADD_OBJECT_PARAM_FILE
macros_path = BF_MACROS_PATH
file_full_path = os.path.join(macros_path, cfg_file)

OBJ_NAME = 0
OBJ_TYPE = 1
PROP_NAME = 2
PROP_GROUP = 3
PROP_TYPE = 4
PROP_VALUE_EXP = 5
PROP_CONTENU = 6

liste_objets = {"Mt i p 01":"Mt_i_p",
                "Mt i b 01":"Mt_i_b",
                "Mt i 01":"Mt_i",
                "Box001":"Mt_i_bxr",
                "Mt i rainure 01":"Mt_i_rainure"
                }
dftStruct = (
                "Mt i p",
                "Mt i b",
                "Mt i",
                "Mt i r1",
                "Mt i rainure",
            )

def objName(objLabel = ""):
    if objLabel:
        return objLabel.replace(" ", "_")
    return

def lire_configuration_caisson():
    """
    Lit le fichier de configuration de la macro et retourne un dictionnaire de paramètres.
    """

    global file_full_path

    config_data = []

    try:
        # 2. Ouvrir le fichier en mode lecture ('r')
        with open(file_full_path, 'r') as f:

            # 3. Parcourir chaque ligne du fichier
            for ligne in f:

                # Nettoyer la ligne (enlever les espaces de début/fin)
                ligne = ligne.strip()

                # Ignorer les lignes vides ou les lignes de commentaire (si vous en ajoutez,
                # par exemple avec '#' ou ';')
                if not ligne or ligne.startswith('#') or ligne.startswith(';'):
                    continue

                # objet | type objet | propriété | groupe de la propriété | type de la propriété | type valeur ou expression | valeur ou expression
                # 4. Rechercher le séparateur ' | '
                if '|' in ligne:

                    element = ligne.split('|')
                    config_data.append(element)


        print(f"✅ Configuration chargée avec succès depuis : {file_full_path}")
        return config_data

    except FileNotFoundError:
        print(f"❌ Le fichier de configuration est introuvable à : {file_full_path}")
        print("   Retourne les paramètres par défaut ou un dictionnaire vide.")
        return {}
    except Exception as e:
        print(f"❌ Erreur inattendue lors de la lecture du fichier : {e}")
        return {}

def updateValueExpression(name, shape, elements_Obj, myDoc):
    for ele in elements_Obj:
        if ele[OBJ_NAME] == name:
            if ele[PROP_VALUE_EXP] == "value":
                if not hasattr(shape, ele[PROP_NAME]):
                    shape.addProperty(ele[PROP_TYPE], ele[PROP_NAME], ele[PROP_GROUP])
                if ele[PROP_TYPE] == "App::PropertyLinkGlobal":
                    setattr(shape, ele[PROP_NAME], myDoc.getObjectsByLabel(ele[PROP_CONTENU])[0])
                elif ele[PROP_TYPE] == "App::PropertyEnumeration":
                    setattr(shape, ele[PROP_NAME], ast.literal_eval(ele[PROP_CONTENU]))
                elif ele[PROP_TYPE] == "App::PropertyBool":
                    setattr(shape, ele[PROP_NAME], 'True' == ele[PROP_CONTENU])
                    # print(f"shape: {ele[OBJ_NAME]}, propriété: {ele[PROP_NAME]}, valeur: {ele[PROP_CONTENU]}, valeur bool(): {bool(ele[PROP_CONTENU])}")
                else:
                    setattr(shape, ele[PROP_NAME], ele[PROP_CONTENU])
    for ele in elements_Obj:
        if ele[OBJ_NAME] == name:
            if ele[PROP_VALUE_EXP] == "expression":
                shape.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])

def addObjectPartBodyBox(objStruct = dftStruct, myDoc = App.ActiveDocument, parentObjLabel = None):
    # get the objects properties from the configuration file
    liste_elements = lire_configuration_caisson()
    elements_Obj = []
    objBaseName = objName(objStruct[2])

    # filter the properties of the current object structure
    for ele in liste_elements:
        if objBaseName in ele[OBJ_NAME]:
            elements_Obj.append(ele)

    part = myDoc.addObject('App::Part', objName(objStruct[0])) # "Mt_i_p")
    part.Label = objStruct[0] # "Mt i p"
    body = myDoc.addObject('PartDesign::Body', objName(objStruct[1]) ) # "Mt_i_b")
    body.Label = objStruct[1]  # "Mt i b"
    part.addObject(body)
    # nom = "Mt_i"
    label = objStruct[2]
    shape = myDoc.addObject('PartDesign::AdditiveBox',objBaseName)
    shape.Label = label
    body.addObject(shape)
    if label != shape.Label:
        for ele in elements_Obj:
            i = elements_Obj.index(ele)
            elements_Obj[i][PROP_CONTENU] = elements_Obj[i][PROP_CONTENU].replace(f"<<{label}>>",f"<<{shape.Label}>>")

    updateValueExpression(objBaseName, shape, elements_Obj, myDoc)
    # for ele in elements_Obj:
    #     if ele[OBJ_NAME] == objBaseName:
    #         if ele[PROP_VALUE_EXP] == "value":
    #             shape.addProperty(ele[PROP_TYPE], ele[PROP_NAME], ele[PROP_GROUP])
    #             if ele[PROP_TYPE] == "App::PropertyLinkGlobal":
    #                 setattr(shape, ele[PROP_NAME], myDoc.getObjectsByLabel(ele[PROP_CONTENU])[0])
    #             elif ele[PROP_TYPE] == "App::PropertyEnumeration":
    #                 setattr(forme, ele[PROP_NAME], ast.literal_eval(ele[PROP_CONTENU]))
    #             elif ele[PROP_TYPE] == "App::PropertyBool":
    #                 setattr(shape, ele[PROP_NAME], 'True' == ele[PROP_CONTENU])
    #                 # print(f"shape: {ele[OBJ_NAME]}, propriété: {ele[PROP_NAME]}, valeur: {ele[PROP_CONTENU]}, valeur bool(): {bool(ele[PROP_CONTENU])}")
    #             else:
    #                 setattr(shape, ele[PROP_NAME], ele[PROP_CONTENU])
    # for ele in elements_Obj:
    #     if ele[OBJ_NAME] == objBaseName:
    #         if ele[PROP_VALUE_EXP] == "expression":
    #             shape.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])

    name = objName(objStruct[3]) # "Mt_i_bxr"
    shape = myDoc.addObject('PartDesign::SubtractiveBox',name)
    shape.Label = objStruct[3]
    body.addObject(shape)
    shape.AttachmentSupport = [(myDoc.getObject(body.Origin.OriginFeatures[0].Name),'')]
    # shape.MapMode = 'ObjectXY'
    updateValueExpression(name, shape, elements_Obj, myDoc)
    # for ele in elements_Obj:
    #     if ele[OBJ_NAME] == name:
    #         if ele[PROP_VALUE_EXP] == "value":
    #             shape.addProperty(ele[PROP_TYPE], ele[PROP_NAME], ele[PROP_GROUP])
    #             if ele[PROP_TYPE] == "App::PropertyLinkGlobal":
    #                 setattr(shape, ele[PROP_NAME], myDoc.getObjectsByLabel(ele[PROP_CONTENU])[0])
    #             # else:
    #             #     setattr(shape, ele[PROP_NAME], ele[PROP_CONTENU])
    # for ele in elements_Obj:
    #     if ele[OBJ_NAME] == name:
    #         if ele[PROP_VALUE_EXP] == "expression":
    #             shape.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])

    name = objName(objStruct[4])# "Mt_i_rainure"
    if "Tablette" in name:
        subobj = myDoc.getObject(shape.Name)
        shape = myDoc.addObject('PartDesign::LinearPattern',name)
        shape.Label = objStruct[4]
        shape.Originals = myDoc.getObject(subobj.Name)
        shape.Mode = 'length'
        shape.Occurrences = 2
        shape.Direction = (myDoc.getObject(body.Origin.OriginFeatures[2].Name),[''])
        body.addObject(shape)
    else:
        shape = myDoc.addObject('PartDesign::SubtractiveBox',name)
        shape.Label = objStruct[4]
        body.addObject(shape)
        shape.AttachmentSupport = [(myDoc.getObject(body.Origin.OriginFeatures[0].Name),'')]

    updateValueExpression(name, shape, elements_Obj, myDoc)

    # shape.MapMode = 'ObjectXY'
    # for ele in elements_Obj:
    #     if ele[OBJ_NAME] == name:
    #         if ele[PROP_VALUE_EXP] == "value":
    #             shape.addProperty(ele[PROP_TYPE], ele[PROP_NAME], ele[PROP_GROUP])
    #             if ele[PROP_TYPE] == "App::PropertyLinkGlobal":
    #                 setattr(shape, ele[PROP_NAME], myDoc.getObjectsByLabel(ele[PROP_CONTENU])[0])
    #             # else:
    #             #     setattr(shape, ele[PROP_NAME], ele[PROP_CONTENU])
    # for ele in elements_Obj:
    #     if ele[OBJ_NAME] == name:
    #         if ele[PROP_VALUE_EXP] == "expression":
    #             shape.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])

    name = objName(objStruct[0]) # "Mt_i_p"
    # for ele in elements_Obj:
    #     if ele[OBJ_NAME] == name:
    #         if ele[PROP_VALUE_EXP] == "value":
    #             setattr(part, ele[PROP_NAME], ele[PROP_CONTENU])
    for ele in elements_Obj:
        if ele[OBJ_NAME] == name:
            if ele[PROP_VALUE_EXP] == "expression":
                part.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])

    name = objName(objStruct[1]) # "Mt_i_b"
    # for ele in elements_Obj:
    #     if ele[OBJ_NAME] == name:
    #         if ele[PROP_VALUE_EXP] == "value":
    #             setattr(body, ele[PROP_NAME], ele[PROP_CONTENU])
    for ele in elements_Obj:
        if ele[OBJ_NAME] == name:
            if ele[PROP_VALUE_EXP] == "expression":
                body.setExpression(ele[PROP_NAME], ele[PROP_CONTENU])

    if parentObjLabel != None: myDoc.getObjectsByLabel(parentObjLabel)[0].addObject(part)
