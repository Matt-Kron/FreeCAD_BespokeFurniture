# SPDX-License-Identifier: GPL-3.0-or-later

"""Atelier FreeCAD Meuble."""

import FreeCAD as App
import FreeCADGui as Gui
from pathlib import Path

translate = App.Qt.translate

from FreeCAD_BespokeFurniture.utils.BespokeFurnitureToolbarCreation import get_cmds

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
        if Gui.ActiveDocument:
            return True
        else:
            return False

    def Activated(self):
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
        cmds = get_cmds()
        commands = []
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
