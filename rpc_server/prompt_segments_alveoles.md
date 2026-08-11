tu es expert développeur python FreeCAD.
Ecrit ou modifie le script [[extract_segments_alveoles]] qui:
- cherche tous les AdditiveBox ou SubtractiveBox avec une propriété bspf_tag qui contient "CS"
- récupère tous les parents App::Part de l'objet avec [[lib_menuiserire.py]] get_parent_part()
- à partir de la specification [[extract_role_dimensions]] crée un fichier json `meuble_simplifie.json` de sortie qui contient uniquement les panneaux verticaux et horizontaux:
  - segments
    - nom: Label du additivebox
      - debut: vecteur segment.origine
      - fin: debut + vecteur segment.longueur
  - alveoles: à déduire à partir des segments. utilise une librairie python qui fait ce genre de tâche s'il en existe
    - ID: des lettres pour les colonnes, et un nombre pour les lignes. car cela ressemblera à un quadrillage. Les lettres sont croissantes en fonction de la coordonnée y du point inférieur gauche de l'alvéole
    - role: null par défaut. pourra être des fonctionnalités de meuble comme (penderie, pulls, livres, assiettes)
    - enveloppe: les panneaux qui constituent l'enveloppe, pour pouvoir les identifier afin de les modifier pour agrandir, réduire, scinder l'alvéole selon sa fonction.
	    - paroi gauche: nom du segment de gauche
	    - paroi droite: nom du segment de droite
	    - paroi basse: nom du segment inférieur
	    - paroi haute: nom du segment supérieur
	- position: le coin inférieur gauche de l'enveloppe
		- x = position de la paroi gauche + largeur de la paroi gauche
		- y = position de la paroi horizontale la plus en retrait vers l'arrière
		- z = position de la paroi inférieur + hauteur de la paroi inférieur
	- largeur = position paroi droite - position.x de l'alvéole
	- profondeur: profondeur du panneau le moins profond de l'enveloppe
	- hauteur = position paroi haute - position.z de l'alvéole

update
   1) pour les noms de parois, enregistre plutôt le label de l'objet parent de la géométrie obtenue avec get_parent_part importé en début de script.
   2) au lieu d'enregistrer le json dans le fichier indiqué, crée un objet App::Part du même nom dans le document actif qui a été analysé. Ajoute lui une propriété PropertyString qui contient le json.
   3) quand le script est appelé:
      a) si aucun json n'est dans le document, à l'endroit indiqué au point 2, ajoute le
      b) sinon met le json à jour: les segments peuvent être écrasés, mais les alvéoles doivent juste être mise à jour pour les existantes pour conserver le rôle. une alvéole existe encore si elle a les mêmes 4 parois.
   4) crée une fonction qui permet de modifier le rôle d'une alvéole

[@meuble_simplifie_goemetrie.py](file:///home/matthou/snap/freecad/common/FreeCAD_BespokeFurniture/rpc_server/meuble_simplifie_goemetrie.py) modifie le script pour
1) pouvoir être appelé par [@extract_segments_alveoles.py](file:///home/matthou/snap/freecad/common/FreeCAD_BespokeFurniture/rpc_server/extract_segments_alveoles.py) et ajouter ou mettre à jour les éléments dans le App::Part meuble_simplifie
2) ajoute une étiquette du module Draft de FreeCAD pour chaque cellule indiquant son id et son rôle
3) dans [@extract_segments_alveoles.py](file:///home/matthou/snap/freecad/common/FreeCAD_BespokeFurniture/rpc_server/extract_segments_alveoles.py) appelle [@meuble_simplifie_goemetrie.py](file:///home/matthou/snap/freecad/common/FreeCAD_BespokeFurniture/rpc_server/meuble_simplifie_goemetrie.py) pour ajouter/mettre à jour les alvéoles