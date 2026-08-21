# -*- coding: utf-8 -*-
"""
Created on Sat Feb 21 17:15:19 2026

@author: Matthieu

includes FreeCAD code
"""

import FreeCADGui as Gui
import FreeCAD as App
import os

from PySide import QtGui
from PySide.QtGui import QToolBar

from typing import ClassVar
from pathlib import Path



def create_custom_command(
        toolbar,
        filename,
        menu_text,
        tooltip_text,
        whats_this_text,
        status_tip_text,
        pixmap_text,
    ):
    """Create a custom command and reload the active workbench so that toolbars get recreated."""
    command_name = Gui.Command.createCustomCommand(
        filename, menu_text, tooltip_text, whats_this_text, status_tip_text, pixmap_text
    )
    toolbar.SetString(command_name, "FreeCAD")

    # Force the toolbars to be recreated
    wb = Gui.activeWorkbench()
    wb.reloadActive()

def create_new_custom_toolbar():
    """Create a new custom toolbar and returns its preference group."""

    # We need two names: the name of the auto-created toolbar, as it will be displayed to the
    # user in various menus, and the underlying name of the toolbar group. Both must be
    # unique.

    # First, the displayed name
    custom_toolbar_name = TOOLBAR_NAME
    custom_toolbars = App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar").GetGroups()
    name_taken = check_for_toolbar(custom_toolbar_name)
    if name_taken:
        i = 2  # Don't use (1), start at (2)
        while True:
            test_name = custom_toolbar_name + f" ({i})"
            if not check_for_toolbar(test_name):
                custom_toolbar_name = test_name
                break
            i = i + 1

    # Second, the toolbar preference group name
    i = 1
    while True:
        new_group_name = "Custom_" + str(i)
        if new_group_name not in custom_toolbars:
            break
        i = i + 1

    custom_toolbar = App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar").GetGroup(new_group_name)
    custom_toolbar.SetString("Name", custom_toolbar_name)
    custom_toolbar.SetBool("Active", True)
    return custom_toolbar

def check_for_toolbar(toolbar_name: str) -> bool:
    """Returns True if the toolbar exists, otherwise False"""
    return get_toolbar_with_name(toolbar_name) is not None

def get_toolbar_with_name(name: str):
    """Try to find a toolbar with a given name. Returns the preference group for the toolbar
    if found, or None if it does not exist."""
    custom_toolbars = App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar").GetGroups()
    for toolbar in custom_toolbars:
        group = App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar").GetGroup(toolbar)
        group_name = group.GetString("Name", "")
        if group_name == name:
            return group
    return None

def delete_toolbar(toolbar_name: str):

    for com in cmds:
        macro_path = os.path.join(bespokefurnitureFolder, com["macroName"])
        # if the command exists, it is removed and recreated
        cmd_gui = Gui.Command.findCustomCommand(macro_path)
        i = 0
        while cmd_gui and i <= 10:
            Gui.Command.removeCustomCommand(cmd_gui)
            cmd_gui = Gui.Command.findCustomCommand(macro_path)
            i += 1

    custom_toolbars = App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar").GetGroups()
    for tb in custom_toolbars:
        if toolbar_name in tb:
            App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar").RemGroup(tb)

    mw = Gui.getMainWindow()

    # Trouver la barre d'outils par le nom d'objet défini dans le script ("MaBarrePerso")
    tb = mw.findChild(QToolBar, toolbar_name)

    if tb:
        # Retirer la barre d'outils de la fenêtre
        mw.removeToolBar(tb)
        # Libérer la mémoire
        tb.deleteLater()
        # print("Barre d'outils supprimée avec succès.")
    # else:
        # print("Barre d'outils introuvable.")

def add_separator(toolbar_name: str):
    mw = Gui.getMainWindow()
    tb = mw.findChild(QToolBar, toolbar_name)
    tb.addSeparator()


bespokefurnitureFolder = "FreeCAD_BespokeFurniture"
prm = App.ParamGet("User parameter:BaseApp/Preferences/Macro")
mpath = prm.GetString("MacroPath", "")
bespokefurnitureFolder = os.path.join(mpath, bespokefurnitureFolder)
iconFolder = os.path.join(bespokefurnitureFolder, "Icons")
TOOLBAR_NAME = "Bespoke Furniture"

cmds = []

# menu text: Add bottom beam
cmds.append({
    "macroName": "Ajouter_TvInf.py",
    "menu_text": "Add bottom beam",
    "tooltip_text": "Add bottom beam",
    "whats_this_text": "Add bottom beam",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "TvInf.svg")
})

# menu text: Add top beam
cmds.append({
    "macroName": "Ajouter_TvSup.py",
    "menu_text": "Add top beam",
    "tooltip_text": "Add top beam",
    "whats_this_text": "Add top beam",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "TvSup.svg")
})

# menu text: Add left panel
cmds.append({
    "macroName": "Ajouter_MtG.py",
    "menu_text": "Add left panel",
    "tooltip_text": "Add left panel",
    "whats_this_text": "Add left panel",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "MtG.svg")
})

# menu text: Add right panel
cmds.append({
    "macroName": "Ajouter_MtD.py",
    "menu_text": "Add right panel",
    "tooltip_text": "Add right panel",
    "whats_this_text": "Add right panel",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "MtD.svg")
})

# menu text: Add vertical part
cmds.append({
    "macroName": "Ajouter_Mti.py",
    "menu_text": "Add vertical part",
    "tooltip_text": "Add vertical part",
    "whats_this_text": "Add vertical part",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "AddMt.svg")
})

# menu text: Add horizontal part
cmds.append({
    "macroName": "Ajouter_Tab.py",
    "menu_text": "Add horizontal part",
    "tooltip_text": "Add horizontal part",
    "whats_this_text": "Add horizontal part",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "AddTv.svg")
})

# menu text: Add back
cmds.append({
    "macroName": "Ajouter_Fond.py",
    "menu_text": "Add back",
    "tooltip_text": "Add back",
    "whats_this_text": "Add back",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "AddBack.svg")
})

# menu text: Add door
cmds.append({
    "macroName": "Ajouter_porte.py",
    "menu_text": "Add door",
    "tooltip_text": "Add door",
    "whats_this_text": "Add door",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "Porte.svg")
})

# menu text: Add drawer front
cmds.append({
    "macroName": "Ajouter_tiroir.py",
    "menu_text": "Add drawer front",
    "tooltip_text": "Add drawer front",
    "whats_this_text": "Add drawer front",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "Tiroir.svg")
})

# menu text: Add vertical part right slope
cmds.append({
    "macroName": "Ajouter_Mti_pente.py",
    "menu_text": "Add vertical part right slope",
    "tooltip_text": "Add vertical part right slope",
    "whats_this_text": "Add vertical part right slope",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "AddMtPente.svg")
})

# menu text: Add vertical part left slope
cmds.append({
    "macroName": "Ajouter_Mti_penteG.py",
    "menu_text": "Add vertical part left slope",
    "tooltip_text": "Add vertical part left slope",
    "whats_this_text": "Add vertical part left slope",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "AddMtPenteG.svg")
})

# menu text: Add door left slope
cmds.append({
    "macroName": "Ajouter_porte_pente_g.py",
    "menu_text": "Add door left slope",
    "tooltip_text": "Add door left slope",
    "whats_this_text": "Add door left slope",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "PortePenteG.svg")
})

# menu text: Add back left slope
cmds.append({
    "macroName": "Ajouter_fond_pente_g.py",
    "menu_text": "Add back left slope",
    "tooltip_text": "Add back left slope",
    "whats_this_text": "Add back left slope",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "AddBackLeftSlope.svg")
})

# menu text: Add several tab as shelf
cmds.append({
    "macroName": "Add_Several_Tab.py",
    "menu_text": "Add several tab as shelf",
    "tooltip_text": "Add several tab as shelf",
    "whats_this_text": "Add several tab as shelf",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "shelf.svg")
})

# menu text: remove objects
cmds.append({
    "macroName": "cmd_remove_object.py",
    "menu_text": "Remove selected objects",
    "tooltip_text": "Remove selected objects",
    "whats_this_text": "Remove selected objects",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "remove_object.svg")
})

# Add separator
cmds.append({"macroName": "separator"})

# menu text: Horizontal between 2 vertical
cmds.append({
    "macroName": "TabEntreDeuxMt.py",
    "menu_text": "Horizontal between 2 vertical",
    "tooltip_text": "Horizontal between 2 vertical",
    "whats_this_text": "Horizontal between 2 vertical",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "TvEntreDeuxMt.svg")
})

# menu text: Vertical between 2 horizontal
cmds.append({
    "macroName": "MtEntreDeuxTv.py",
    "menu_text": "Vertical between 2 horizontal",
    "tooltip_text": "Vertical between 2 horizontal",
    "whats_this_text": "Vertical between 2 horizontal",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "MtEntreDeuxTv.svg")
})

# menu text: Set one between other
cmds.append({
    "macroName": "PartBetween2Other.py",
    "menu_text": "Set one between other",
    "tooltip_text": "Set one between other",
    "whats_this_text": "Set one between other",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "ObjEntreDeux.svg")
})

# menu text: Set slope vertical part on H one
cmds.append({
    "macroName": "MtPenteSurTvInf.py",
    "menu_text": "Set slope vertical part on H one",
    "tooltip_text": "Set slope vertical part on H one",
    "whats_this_text": "Set slope vertical part on H one",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "MtsurTv.svg")
})

# menu text: Cut the selected tab
cmds.append({
    "macroName": "cutTab.py",
    "menu_text": "Cut the selected tab",
    "tooltip_text": "Cut the selected tab",
    "whats_this_text": "Cut the selected tab",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "cutTab.svg")
})

# Add separator
cmds.append({"macroName": "separator"})

# menu text: Add selection to BOM
cmds.append({
    "macroName": "Add_BOM_property_to_selection.py",
    "menu_text": "Add selection to BOM",
    "tooltip_text": "Add BOM custom properties to the selected objects",
    "whats_this_text": "Add BOM custom properties to the selected objects",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "AddBOMprop.svg")
})

# menu text: BOM prop to spreadsheet
cmds.append({
    "macroName": "BOM_to_spreadsheet_when_BOM-property-True.py",
    "menu_text": "BOM prop to spreadsheet",
    "tooltip_text": "Copy BOM properties when BOM_destination is True in 'BOM' spreadsheet",
    "whats_this_text": "Copy BOM properties when BOM_destination is True in 'BOM' spreadsheet",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "BOMobjToSpreadsheet.svg")
})

# menu text: BOM prop tools
cmds.append({
    "macroName": "BOM_objects_managment.py",
    "menu_text": "BOM prop tools",
    "tooltip_text": "Tools to manage objects with BOM properties",
    "whats_this_text": "Tools to manage objects with BOM properties",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "MaterialMgmt.svg")
})

# menu text: Panels management
cmds.append({
    "macroName": "BdD_panneaux_multi.py",
    "menu_text": "Panels management",
    "tooltip_text": "Panels management",
    "whats_this_text": "Panels management",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "PanelsMgmt.svg")
})

# menu text: Document panel management
cmds.append({
    "macroName": "ChoisirPanneau.py",
    "menu_text": "Document panel management",
    "tooltip_text": "Document panel management",
    "whats_this_text": "Document panel management",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "ChoixPanneau.svg")
})

# menu text: Manufacturing step management
cmds.append({
    "macroName": "Operations_fabrication.py",
    "menu_text": "Manufacturing step management",
    "tooltip_text": "Manufacturing step management",
    "whats_this_text": "Manufacturing step management",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "WorkingSteps.svg")
})

# menu text: Nesting
cmds.append({
    "macroName": "Wood_panel_nesting.py",
    "menu_text": "Nesting",
    "tooltip_text": "Nesting",
    "whats_this_text": "Nesting",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "Nesting.svg")
})

# menu text: Copy to external spreadsheet
cmds.append({
    "macroName": "BOM_to_Spreadsheet.py",
    "menu_text": "Copy to external spreadsheet",
    "tooltip_text": "Copy to external spreadsheet",
    "whats_this_text": "Copy to external spreadsheet",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "CopyToExternalSpreadsheet.svg")
})

# menu text: Current panel choice used by the other tools (Add tab...)
cmds.append({
    "macroName": "CurrentPanel.py",
    "menu_text": "Current panel choice used by the other tools (Add tab...)",
    "tooltip_text": "Current panel choice used by the other tools (Add tab...)",
    "whats_this_text": "Current panel choice used by the other tools (Add tab...)",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "layers.svg")
})

# Add separator
cmds.append({"macroName": "separator"})

rpc_path = "rpc_server/"

# menu text: Start the RPC server
cmds.append({
    "macroName": f"{rpc_path}cmd_start_rpc_server.py",
    "menu_text": "Start the RPC server",
    "tooltip_text": "Start the RPC server",
    "whats_this_text": "Start the RPC server",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "rpc_server_start.svg")
})

# menu text: Stop the RPC server
cmds.append({
    "macroName": f"{rpc_path}cmd_stop_rpc_server.py",
    "menu_text": "Stop the RPC server",
    "tooltip_text": "Stop the RPC server",
    "whats_this_text": "Stop the RPC server",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "rpc_server_stop.svg")
})

# menu text: Restart the RPC server
cmds.append({
    "macroName": f"{rpc_path}cmd_restart_rpc_server.py",
    "menu_text": "Restart the RPC server",
    "tooltip_text": "Restart the RPC server",
    "whats_this_text": "Restart the RPC server",
    "status_tip_text": "",
    "pixmap_text": os.path.join(iconFolder, "rpc_server_restart.svg")
})

# menu text: génère la géométrie simplifiée du meuble
cmds.append({
    "macroName": f"{rpc_path}meuble_simplifie_geometrie.py",
    "menu_text": "Geo meuble",
    "tooltip_text": "Geométrie simplifiée du meuble",
    "whats_this_text": "Geométrie simplifiée du meuble",
    "status_tip_text": "",
    "pixmap_text": ""
})

toolbar = get_toolbar_with_name(TOOLBAR_NAME)

if toolbar:
    delete_toolbar(TOOLBAR_NAME)
    toolbar = get_toolbar_with_name(TOOLBAR_NAME)

if not toolbar:
    toolbar = create_new_custom_toolbar()

for cmd in cmds:
    if cmd["macroName"] == "separator":
        add_separator(TOOLBAR_NAME)
    else:
        macroPath = os.path.join(bespokefurnitureFolder, cmd["macroName"])
        # if the command exists, it is removed and recreated
        cmdgui = Gui.Command.findCustomCommand(macroPath)
        if cmdgui : Gui.Command.removeCustomCommand(cmdgui)
        create_custom_command(toolbar,
                              macroPath,
                              cmd["menu_text"],
                              cmd["tooltip_text"],
                              cmd["whats_this_text"],
                              cmd["status_tip_text"],
                              cmd["pixmap_text"])


# class RPCServerStart:
#     """Commande pour créer un nouveau meuble paramétrique."""
#
#     # Utilisation d'une constante pour le nom de la commande
#     Name: ClassVar[str] = "BspfRPCServerStart"
#
#     def __init__(self) -> None:
#         """Initialisation de la commande."""
#         pass
#
#     def GetResources(self) -> dict[str, str]:
#         """Définit l'apparence de la commande dans l'interface utilisateur."""
#         return {
#             "Pixmap": os.path.join(iconFolder, "rpc_server_start.svg"),
#             "MenuText": "Start RPC Server",
#             "ToolTip": "Lance le serveur RPC",
#         }
#
#     def IsActive(self) -> bool:
#         # """L'outil est actif seulement si un document est ouvert."""
#         # return App.ActiveDocument is not None
#         return True
#
#     def Activated(self) -> None:
#         """Méthode principale appelée au clic sur l'icône ou le menu."""
#         # App.Console.PrintMessage("Commande 'Nouveau Meuble' activée.\n")
#
#         from FreeCAD_BespokeFurniture.rpc_server.freecad_rpc import start_rpc_server
#         start_rpc_server()
#
# class RPCServerRestart:
#     """Commande pour créer un nouveau meuble paramétrique."""
#
#     # Utilisation d'une constante pour le nom de la commande
#     Name: ClassVar[str] = "BspfRPCServerReStart"
#
#     def __init__(self) -> None:
#         """Initialisation de la commande."""
#         pass
#
#     def GetResources(self) -> dict[str, str]:
#         """Définit l'apparence de la commande dans l'interface utilisateur."""
#         return {
#             "Pixmap": os.path.join(iconFolder, "rpc_server_restart.svg"),
#             "MenuText": "Restart RPC Server",
#             "ToolTip": "Relance le serveur RPC",
#         }
#
#     def IsActive(self) -> bool:
#         # """L'outil est actif seulement si un document est ouvert."""
#         # return App.ActiveDocument is not None
#         return True
#
#     def Activated(self) -> None:
#         """Méthode principale appelée au clic sur l'icône ou le menu."""
#         # App.Console.PrintMessage("Commande 'Nouveau Meuble' activée.\n")
#
#         from FreeCAD_BespokeFurniture.rpc_server.freecad_rpc import restart_rpc_server
#         restart_rpc_server()
#
# class RPCServerStop:
#     """Commande pour créer un nouveau meuble paramétrique."""
#
#     # Utilisation d'une constante pour le nom de la commande
#     Name: ClassVar[str] = "BspfRPCServerStop"
#
#     def __init__(self) -> None:
#         """Initialisation de la commande."""
#         pass
#
#     def GetResources(self) -> dict[str, str]:
#         """Définit l'apparence de la commande dans l'interface utilisateur."""
#         return {
#             "Pixmap": os.path.join(iconFolder, "rpc_server_stop.svg"),
#             "MenuText": "Stop RPC Server",
#             "ToolTip": "Arrête le serveur RPC",
#         }
#
#     def IsActive(self) -> bool:
#         # """L'outil est actif seulement si un document est ouvert."""
#         # return App.ActiveDocument is not None
#         return True
#
#     def Activated(self) -> None:
#         """Méthode principale appelée au clic sur l'icône ou le menu."""
#         # App.Console.PrintMessage("Commande 'Nouveau Meuble' activée.\n")
#
#         from FreeCAD_BespokeFurniture.rpc_server.freecad_rpc import stop_rpc_server
#         stop_rpc_server()
#
# # On récupère la liste de TOUTES les commandes enregistrées dans FreeCAD
# toutes_les_commandes = Gui.listCommands()
# commandes_existantes = [item[0] for item in toolbar.GetContents()]
#
# cmd_name_list = [
#                 [RPCServerStart.Name, RPCServerStart()],
#                 [RPCServerRestart.Name, RPCServerRestart()],
#                 [RPCServerStop.Name, RPCServerStop()]
# ]
# for cmd_name, cmd_func in cmd_name_list:
#     if cmd_name not in toutes_les_commandes:
#         Gui.addCommand(cmd_name, cmd_func)
#         print("Commande enregistrée pour la première fois.")
#     else:
#         print("La commande existe déjà dans le système FreeCAD.")
#
#     if cmd_name not in commandes_existantes:
#         toolbar.SetString(cmd_name, cmd_name)
#         App.Console.PrintMessage(f"Commande '{cmd_name}' ajoutée avec succès à la barre d'outils.\n")
#     else:
#         App.Console.PrintMessage(f"La commande '{cmd_name}' est déjà présente dans la barre.\n")
