# SPDX-License-Identifier: GPL-3.0-or-later

"""Atelier FreeCAD Meuble."""

import FreeCAD as App
import FreeCADGui as Gui
from pathlib import Path

translate = App.Qt.translate

from utils.BespokeFurnitureToolbarCreation import get_cmds

__dir__ = Path(__file__).parent
iconPath = __dir__ / "Icons"

class _CommandMeuble():

    def __init__(self, name='NouveauMeuble', menutext='Nouveau Meuble', tooltip='Ajoute un nouveau meuble', icon='meuble.svg', command='', modul=''):
        self.name = name
        self.menutext = menutext
        self.tooltip = tooltip
        self.icon = str(iconPath / icon)
        self.command = command
        self.modul = modul

    def GetResources(self):
        return {'Pixmap' : self.icon, 'MenuText': self.menutext, 'ToolTip': self.tooltip}

    def IsActive(self):
        if ".FCStd" in self.command or Gui.ActiveDocument:
            return True
        else:
            return False

    def Activated(self):
        if ".FCStd" in self.command:
            Gui.doCommand(f"{self.command}")
        else:
            App.ActiveDocument.openTransaction(self.name)

            try:
                # doCommand importe le module et exécute la fonction en une seule fois
                Gui.doCommand(f"import {self.modul}")
                Gui.doCommand(f"{self.modul}.{self.command}()")

                App.ActiveDocument.commitTransaction()
                App.ActiveDocument.recompute()

            except Exception as e:
                App.ActiveDocument.abortTransaction()
                App.Console.PrintError(
                    f"Erreur lors de l'exécution de {self.name} : {str(e)}\n"
                )

class CommandGroup():
    """Group of commands for GUI (toolbar, menu...)."""

    def __init__(self, cmdlist, menu, tooltip=None):
        """Initialize group of commands."""
        self.cmdlist = cmdlist
        self.menu = menu
        self.tooltip = tooltip if tooltip is not None else menu

    def GetCommands(self):
        """Get command group's commands (callback)."""
        return tuple(self.cmdlist)

    def GetResources(self):
        """Get command group's resources (callback)."""
        return {"MenuText": self.menu, "ToolTip": self.tooltip}

def load_Furniture(name):
    models_folder = __dir__ / "CAD"
    filename = ""
    if name == "Meuble rectangulaire":
        filename = models_folder / "Modele_caisson_parts_FC1-1-0_v7.FCStd"
    elif name == "Meuble pente gauche":
        filename = models_folder / "Modele_caisson_pente-gauche_v2.FCStd"
    elif name == "Meuble pente droite":
        filename = models_folder / "Modele_caisson_pente-droite_v1-1_FC1.FCStd"
    elif name == "Porte cadre":
        filename = models_folder / "Porte_Cadre_modele.FCStd"
    elif name == "Bloc tiroir":
        filename = models_folder / "Modele_box_tiroir_v1.FCStd"
    if filename:
        App.openDocument(filename)

class MeubleWorkbench(Gui.Workbench):

    MenuText: str = translate(
            "Meuble",
            "Atelier Meuble",
        )

    ToolTip: str = translate(
            "Meuble",
            "Conception de meuble sur mesure",
        )

    Icon: str = str(iconPath / "meuble-wb.svg")


    def Initialize(self) -> None:
        App.Console.PrintMessage("Atelier Meuble initialisé\n")
        # Adding menus and toolbars when the Workbench is active (example)

        # FreeCAD models loading
        models_folder = __dir__ / "CAD"
        cmds_addCAD = [
            ("CmdMeubleRect", "Meuble rectangulaire", iconPath / "caisson.svg", models_folder / "Modele_caisson_parts_FC1-1-0_v7.FCStd"),
            ("CmdMeublePenteG", "Meuble pente gauche", iconPath / "pente_g.svg", models_folder / "Modele_caisson_pente-gauche_v2.FCStd"),
            ("CmdMeublePenteD", "Meuble pente droite", iconPath / "pente_d.svg", models_folder / "Modele_caisson_pente-droite_v1-1_FC1.FCStd"),
            ("CmdPorteCadre", "Porte cadre", iconPath / "porte_cadre.svg", models_folder / "Porte_Cadre_modele.FCStd"),
            ("CmdBlocTiroir", "Bloc tiroir", iconPath / "bloc_tiroir.svg", models_folder / "Modele_box_tiroir_v1.FCStd"),
            ("CmdPanneauMoulure", "Panneau Moulures", iconPath / "panneau_cadre.svg", models_folder / "Panneau_moulures.FCStd"),
        ]

        cmds_list = []
        for cmd_id, text, icone, fichier in cmds_addCAD:
            # Normalisation du chemin avec / pour éviter les bugs sous Windows
            chemin_propice = str(fichier).replace("\\", "/")

            cmd_instance = _CommandMeuble(
                name=cmd_id,
                menutext=text,
                tooltip=f"Ouvre {text}",
                icon=icone,
                command=f"FreeCAD.openDocument('{chemin_propice}')"
            )

            Gui.addCommand(cmd_id, cmd_instance)
            cmds_list.append(cmd_id)

        cmds_grp = CommandGroup(cmds_list, "Modèles de meuble", "Ouvre un meuble de base ou un composant")
        grp_name = "CADmodels"
        Gui.addCommand(grp_name, cmds_grp)

        cmds = get_cmds()
        commands = []
        commands.append(grp_name)
        for cmd in cmds:
            # nom_sans_extension, extension = os.path.splitext(cmd["macroName"])
            nom_sans_extension = Path(cmd["macroName"]).stem
            print(nom_sans_extension)
            if nom_sans_extension == "meuble_simplifie_geometrie":
                modul = Path(cmd["macroName"])
                modul = modul.parent / modul.stem
                modul = ".".join(modul.parts)
                Gui.addCommand(nom_sans_extension, _CommandMeuble(cmd["macroName"], cmd["menu_text"], cmd["tooltip_text"], cmd["pixmap_text"], cmd["command"], modul))
            Gui.addCommand(nom_sans_extension, _CommandMeuble(cmd["macroName"], cmd["menu_text"], cmd["tooltip_text"], cmd["pixmap_text"], cmd["command"], nom_sans_extension))
            # name='NouveauMeuble', text='Nouveau Meuble', tooltip='Ajoute un nouveau meuble', icon='meuble.svg', command='', modul=''
            commands.append(nom_sans_extension)
        # commands = [CmdNouveauMeuble.Name, CmdNouveauCaisson.Name]
        self.appendToolbar("Meuble", commands)
        self.appendMenu("Meuble", commands)

    def Activated(self) -> None:
        App.Console.PrintMessage("Atelier Meuble activé\n")

    def Deactivated(self) -> None:
        App.Console.PrintMessage("Atelier Meuble désactivé\n")

    def ContextMenu(self, recipient: str) -> None:
        App.Console.PrintMessage("Menu contextuel Meuble\n")
        # Adding context menus when the Workbench is active (example)
        # self.appendContextMenu("", [CmdNouveauMeuble.Name, CmdNouveauCaisson.Name])

    @classmethod
    def Install(cls) -> None:
        print(cls.Icon)
        Gui.addWorkbench(cls)
