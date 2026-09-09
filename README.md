# FreeCAD Bespoke Furniture
<img src="resources/atelier_meuble.png" width="800">

<img src="resources/Bureau3D.png" width="150"><img src="resources/bibliotheque.png" width="220"><img src="resources/cuisine.png" width="265"><img src="resources/placard_01.png" width="150"><img src="resources/sous-escalier.png" width="260"><img src="resources/Dressing_face_01.png" width="240"><img src="resources/Placard_vue_01.png" width="100"><img src="resources/SdB_portes-ouvertes_01.png" width="150"><img src="resources/coupe_placard_01.png" width="150"><img src="resources/VueOrtho01.png" width="300"><img src="resources/caisson_haut_vitre.png" width="150"><img src="resources/Dressing_vue_globale_01.png" width="150"><img src="resources/Gemini_Generated_Image.png" width="200"><img src="resources/sous-escalier_02.png" width="150">

[Résumé](#résumé)

[Commandes](#commandes-disponibles)

- [Caisson](#caisson)

- [Ajout de composants](#ajout-de-composants)

- [Assemblage](#assemblage)

- [Utilitaires](#utilitaires)

[Méthode manuelle](#méthode-manuelle)

[Paramètres](#paramètres)

[Intégration IA](#intégration-ia)

[Installation](#installation)
## Résumé

Un ensemble d'objets paramétriques et de macros pour créer un meuble paramétrique dans FreeCAD. Il s'agit de meubles fabriqués à partir de panneaux de bois, mélaminé, MDF, plaqué massif (latté chêne...), lamellé-collé... Ces panneaux sont donc de simples parallélépipèdes. On peut cependant dessiner des formes plus complexes dont les dimensions externes sont reliées à un panneau de référence (exemples à venir).

Les dimensions des pièces sont d'abord faites pour obtenir les tailles de fabrication, et non pour obtenir un visuel rigoureux du résultat final chez un client (ou pour soi).

A ce stade les commandes ne permettent pas de créer un modèle à partir de rien, il faut d'abord ouvrir un modèle de base (dossier ./CAD/ de ce dépôt github):
- [Caisson droit](./CAD/Modele_caisson_parts_FC1-1-0_v7.FCStd): modèle de base d'un meuble rectangulaire
- [Caisson pente droite](./CAD/Modele_caisson_pente-droite_v1-1_FC1.FCStd): modèle de meuble sous pente, descendant vers la droite
- [Caisson pente gauche](./CAD/Modele_caisson_pente-gauche_v2.FCStd): modèle sous-pente, descendant vers la gauche

La structure du modèle générique est un assemblage de conteneurs Part imbriqués. Le meuble contient un caisson, le support du caisson si besoin, les fileurs extérieurs si besoin. Le caisson contient les composants (Part + Body + Géométries).
Un VarSet `Parametres` rassemble les paramètres globaux du meuble, ainsi que les paramètres utiles à plusieurs composants.
Un VarSet `Montants` regroupent les paramètres qui augmentent la taille des montants gauche et droit dans le cas où ceux-ci doivent aller jusqu'au mur du fond, au plafond, sol et découpés sur le chantier pour suivre les parois. Un décalage est également modifiable pour dépasser le caisson et recouvrir l'épaisseur des portes par exemple.

Les macros d'ajout de composant et d'assemblage ne sont pas indispensables pour concevoir un meuble, elles accélèrent beaucoup son dessin. Le modèle générique de meuble est fait avec des propriétés ajoutées aux objets classiques de FreeCAD (Part, AdditiveBox... ) et des expressions qui calculent dimensions et positions à partir d'autres éléments ou de paramètres (essentiellement centralisés dans le VarSet `Parametres`). J'ai d'ailleurs commencé à faire mes meubles paramétriques sans les macros, en concevant les éléments de base paramétriques (tablette/traverse, montant, fond, tiroir, porte), en les dupliquant et en changeant manuellement les paramètres.

## Maturité et robustesse des macros
**Remarque générale**
Toutes les macros ont été écrites au fur et à mesure de mes besoins de productivité. Le code était au début 100% de mon jus de codeur autodidacte et pas pro du tout. Puis j'ai exploité l'IA de plus en plus, en regardant plus ou moins le code généré, selon la qualité du résultat et le temps que j'avais à relire. Même si j'avais l'envie dès le départ d'un jour partager tout ce travail, ma priorité était clairement mon usage personnel (4 ans de menuiserie dont 3 à mon compte) pour accélérer tout le processus de conception, chiffrage, préparation à la fabrication.
Donc cela manque de factorisation, d'optimisation d'architecture, et c'est très propablement loin des règles d'un code propre, sauf peut-être pour certaines parties assistées par IA.

**Boites de dialogues**
Quelques boites de dialogues sont soit devenues inutiles et ne sont pas encore supprimées du code (macros d'assemblage), soit méritent une refonte.

**Épaisseur des composants**
J'ai ajouté récemment la propriété BOM_mat à tous les composants ajoutés, avec un panneau par défaut défini (avant, l'ajout se faisait lors de la création de la BOM, après la conception du meuble). A terme l'objectif est de modifier l'épaisseur des objets en fonction du choix du panneau. Actuellement l'épaisseur est un paramètre global, étant donné que mon usage est quasi 100% avec des panneaux de 19mm.
En l'état, pour gérer plusieurs épaisseurs il faut créer un paramètre par nouvelle épaisseur et l'utiliser dans la propriété ad-hoc des objets concernés (Height pour des traverses, Length pour des montants...).
L'épaisseur des panneaux est une épine dans le pied depuis le début, car j'ai abusé du fait que la quasi totalité des meubles sont en une seule épaisseur, pour aller vite. Le mieux c'est de l'associer au choix du matériau, mais ce qui me gêne c'est que l'épaisseur doit rester un paramètre qui change automatiquement en fonction du choix du panneau, sans macro. Il faut donc repenser les objets panneaux, qui ne sont au moment où j'écris, qu'une ligne de texte dans une propriété d'un VarSet. Peut-être en créant un objet panneau sur la base d'un VarSet par matériau.

## Commandes disponibles

### Modèles 3D

|                      Icon                      | Command                  | Description                                                                                                       |
| :--------------------------------------------: | :----------------------- | :---------------------------------------------------------------------------------------------------------------- |
|    <img src="Icons/caisson.svg" width="32">    | Meuble rectangulaire     | Ajoute un meuble de base à compléter dans un nouveau document                                                     |
|    <img src="Icons/pente_g.svg" width="32">    | Meuble pente gauche      | Ajoute un meuble sous pente gauche à compléter dans un nouveau document                                           |
|    <img src="Icons/pente_d.svg" width="32">    | Meuble pente droite      | Ajoute un meuble sous pente droite à compléter dans un nouveau document                                           |
|  <img src="Icons/porte_cadre.svg" width="32">  | Panneau cadre simple     | Ajoute un panneau avec un cadre simple dans un nouveau document. Peut être lié à une façade (porte, tiroir, joue) |
|  <img src="Icons/bloc_tiroir.svg" width="32">  | Bloc tiroir              | Ajoute un bloc tiroir sans façade dans un nouveau document                                                        |
| <img src="Icons/panneau_cadre.svg" width="32"> | Panneau cadre et moulure | Ajoute un panneau avec moulure dans un nouveau document. Peut être lié à une façade (porte, tiroir, joue)         |
### Caisson
Les commandes suivantes qui permettent de créer un caisson de base ne sont pas directement exploitables à ce stade. Les pièces dépendent les unes des autres et des erreurs apparaissent dans les expressions avec la dernière version de FreeCAD 1.1.3.
Pour l'instant elles ont un intérêt pour rapidement faire évoluer le modèle de base, lorsque les formules paramétriques évoluent. A terme l'intérêt est de pouvoir dessiner plusieurs caissons dans un même meuble plutôt que d'assembler plusieurs meubles, dans certains cas.

|                  Icon                  | Command         | Description                                    |
| :------------------------------------: | :-------------- | :--------------------------------------------- |
| <img src="Icons/TvInf.svg" width="32"> | Add bottom beam | Ajoute une traverse inférieure dans le caisson |
| <img src="Icons/TvSup.svg" width="32"> | Add top beam    | Ajoute une traverse supérieure dans le caisson |
|  <img src="Icons/MtG.svg" width="32">  | Add left panel  | Ajoute le montant gauche dans le caisson       |
|  <img src="Icons/MtD.svg" width="32">  | Add right panel | Ajoute le montant droit dans le caisson        |
### Ajout de composants

|                       Icon                        | Command                       | Description                                                                                                                                                                                                                                                                                    | Propriétés de l'objet                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| :-----------------------------------------------: | :---------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
|      <img src="Icons/AddMt.svg" width="32">       | Add vertical part             | Ajout d'un montant.<br>Par défaut le montant est relié aux traverses inférieure et supérieure du caisson.<br>Sélectionner 2 traverses avant d'ajouter le montant pour l'y relier à la création                                                                                                 | Les propriétés de base sont dans l'AdditiveBox du Corps. Sous le groupe "UserProp":<br>- fond: si Vrai le montant a la profondeur du caisson, quand on veut qu'il y ait un panneau de fond de chaque côté du montant. Dans ce cas c'est l'objet rainuré du corps qu'il faut rendre visible.<br>- offset: active le décalage du montant selon la valeur de offset_profondeur vers l'avant ou l'arrière.<br>- offset_profondeur: valeur du décalage, par défaut reliée à un paramètre global qui permet de décaler un ensemble de composants.                                                                                                                                                                                                                                                                                                                                                                                                      |
|      <img src="Icons/AddTv.svg" width="32">       | Add horizontal part           | Ajout d'une traverse.<br>Par défaut la traverse est reliée aux montants gauche et droit du caisson.<br>Sélectionner 2 montants avant d'ajouter la traverse pour l'y relier à la création                                                                                                       | Les propriétés de base sont dans l'AdditiveBox du Corps.<br>Sous le groupe "UserProp":<br>- fond: si Vrai le montant a la profondeur du caisson, quand on veut qu'il y ait un panneau de fond de chaque côté du montant. Dans ce cas c'est l'objet rainuré du corps qu'il faut rendre visible.<br>- offset: active le décalage du montant selon la valeur de offset_profondeur vers l'avant ou l'arrière.<br>- offset_profondeur: valeur du décalage, par défaut reliée à un paramètre global qui permet de décaler un ensemble de composants.<br>- Cremaillere: liste de choix qui définit les jeux utilisés. Les valeurs sont dans les paramètres globaux.<br>Sous le groupe "Parametres":<br>- type:<br>    - Tablette: pour une étagère qui a du jeu avec les montants et le fond. Utilise le choix "Cremaillère" ci-dessus pour définir le jeu.<br>	- Traverse: pour une pièce qui est fixée aux montants. Les jeux ne sont plus appliqués. |
|     <img src="Icons/AddBack.svg" width="32">      | Add back                      | Ajoute un fond.<br>Par défaut les parois du caisson définissent ses dimensions.<br>Sinon les 4 parois sélectionnées servent de référence à la création                                                                                                                                         | Les propriétés du fond sont dans les paramètres globaux: épaisseur, retrait par rapport à la profondeur, profondeur de dépassement dans les parois.<br>`Parametres`, groupe `Fond`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
|      <img src="Icons/Porte.svg" width="32">       | Add door                      | Ajoute une porte.<br>Par défaut les parois du caisson définissent ses dimensions.<br>Sinon les 4 parois sélectionnées servent de référence à la création                                                                                                                                       | Le choix de l'interface de la porte avec ses parois se fait dans le VarSet `Porte_param` situé dans le Corps `Porte b` de l'objet.<br>Les 4 propriétés telles que `offset_dessous` offrent une liste de choix:<br>- Rien: les dimensions de la porte correspondent aux faces externes des parois.<br>- Paroi: ajoute un jeu entre la porte et une paroi fictive (un mur, un autre meuble...) défini dans les paramètres globaux: 2*`jeu_largeur` du groupe `Facade`<br>- Autre facade: idem que Paroi avec 1*`jeu_largeur`, car l'autre façade aura également ce jeu ce qui fera une distance de 2*`jeu_largeur` entre les objets<br>- Encastree: ajoute un jeu de 2*`jeu_largeur` avec les faces internes des parois qui dimensionnent la porte<br>- Milieu: lorsqu'il s'agit de 2 portes jumelées sur un montant par exemple. La face externe de la porte est positionnée au milieu du montant (ou traverse) moins 1*`jeu_largeur`             |
|      <img src="Icons/Tiroir.svg" width="32">      | Add drawer front              | Ajoute une façade de tiroir (ou un panneau de fermeture).<br>Par défaut les parois du caisson définissent ses dimensions.<br>Sinon les 4 parois sélectionnées servent de référence à la création                                                                                               | Similaire à la porte. VarSet `Tiroir_param` dans le Corps `Tiroir b`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|    <img src="Icons/AddMtPente.svg" width="32">    | Add vertical part right slope | Ajoute un montant qui s'adapte à la hauteur de la traverse supérieure selon la position latérale                                                                                                                                                                                               |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|   <img src="Icons/AddMtPenteG.svg" width="32">    | Add vertical part left slope  | Ajoute un montant qui s'adapte à la hauteur de la traverse supérieure selon la position latérale                                                                                                                                                                                               |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|   <img src="Icons/PortePenteG.svg" width="32">    | Add door left slope           | Ajoute une porte qui s'adapte à la pente d'un meuble incliné à gauche                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| <img src="Icons/AddBackLeftSlope.svg" width="32"> | Add back left slope           | Ajoute un fond qui s'adapte à la pente d'un meuble incliné à gauche                                                                                                                                                                                                                            |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|      <img src="Icons/shelf.svg" width="32">       | Add several tab as shelf      | Ajoute ou modifie plusieurs étagères ou montants en une seule fois.<br>Si 2 montants ou 2 traverses sont sélectionnés l'outil crée un nouveau découpage de l'espace.<br>Si une étagère ou un montant faisant partie d'un groupe existant est sélectionné, l'outil permet de modifier ce groupe |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|  <img src="Icons/remove_object.svg" width="32">   | Remove selected objects       | Supprime les objets sélectionnés: tout le contenu de l'objet Part conteneur parent à la sélection est supprimé, sans avertissement.                                                                                                                                                            |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|                                                   |                               |                                                                                                                                                                                                                                                                                                |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
### Assemblage

Ces outils permettent d'assigner les objets externes à un composant qui définissent ses dimensions et sa position.
Aucun contrôle n'est fait sur les objets sélectionnés, cela peut produire des erreurs (une formule qui conduit à une dimension inférieure à 0). Cela permet d'avoir des assemblages moins triviaux comme une traverse entre un montant et une traverse, pour des configurations de meuble moins triviales également.

|                      Icon                      | Command                          | Description                                                                                                                                                                                                       |
| :--------------------------------------------: | :------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <img src="Icons/TvEntreDeuxMt.svg" width="32"> | Horizontal between 2 vertical    | A partir d'une sélection de 3 composants, tente d'en relier un aux deux autres: une traverse entre deux montants. Ou une porte entre deux montants                                                                |
| <img src="Icons/MtEntreDeuxTv.svg" width="32"> | Vertical between 2 horizontal    | A partir d'une sélection de 3 composants, tente d'en relier un aux deux autres: un montant entre deux traverses. Ou une façade de tiroir entre deux traverses                                                     |
| <img src="Icons/ObjEntreDeux.svg" width="32">  | Set one between other            | A partir d'une sélection de 5 composants, cherche une porte, un fond ou une façade de tiroir dans la sélection, et relie cet objet aux quatre autres supposés être des parois (2 montants, 2 traverses)           |
|    <img src="Icons/MtsurTv.svg" width="32">    | Set slope vertical part on H one | A partir d'une sélection de 2 objets, relie celui qui le peut à l'autre objet présumé au-dessous. Cas typique d'usage pour les montants de meuble incliné dont la hauteur est définie par la traverse supérieure. |
|    <img src="Icons/cutTab.svg" width="32">     | Cut the selected tab             | Permet de couper une traverse en 2 parties, la longueur de la deuxième dépendant de la première. Cas typique: longueur trop longue pour le panneau de bois utilisé.                                               |
### Utilitaires

|                            Icon                            | Command                       | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| :--------------------------------------------------------: | :---------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|        <img src="Icons/AddBOMprop.svg" width="32">         | Add selection to BOM          | Ajoute des propriétés aux objets sélectionnés pour gérer la liste des matériaux (BOM: Bill Of Materials).<br>- BOM_destination: permet de filtrer qu'on ne veut plus l'objet dans la BOM sans avoir à supprimer de propriétés BOM_* sur l'objet (maintien la gestion de la couleur pour les pièces de taille identique qui ne sont pas dans la BOM individuellement).<br>- BOM_mat: choix parmi la liste de panneaux du modèle. Utilisé pour la couleur, et bien sûr le tri pour la feuille de débit et le calepinage. Sert également à déduire certaines opérations de fabrication<br>- BOM_quantity: nombre de pièces identiques à celle-là.<br>- Nest_Allow_Rotation: faux si le motif du panneau doit avoir une orientation précise<br>- Nest_Thickness: propriété de l'objet qui correspond à l'épaisseur du panneau. Pour déduire les deux autres dimensions qui servent au calepinage<br>- Nest_grain: sans du motif ou du fil du bois, pour orienter le calepinage, et sert également de référence au choix des chants collés.<br>- Nesting: permet de filtrer les pièces pour le calepinage, sans avoir à supprimer de propriétés Nest_* utiles par ailleurs. |
|    <img src="Icons/BOMobjToSpreadsheet.svg" width="32">    | BOM prop to spreadsheet       | Exporte les propriétés des objets avec BOM_destination = True dans une `Spreadsheet`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|       <img src="Icons/MaterialMgmt.svg" width="32">        | BOM prop tools                | Boite de dialogue pour gérer les propriétés des composants du meuble                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|        <img src="Icons/PanelsMgmt.svg" width="32">         | Panels management             | Boite de dialogue qui permet de gérer les panneaux de bois utilisés. Gère une bibliothèque utilisateur et dans le document actif.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|       <img src="Icons/ChoixPanneau.svg" width="32">        | Document panel management     | Boite de dialogue pour gérer les panneaux du document actif.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|       <img src="Icons/WorkingSteps.svg" width="32">        | Manufacturing step management | Boite de dialogue pour ajouter des étapes de fabrication à l'objet. Fonctionnalité ajoutée pour faire le devis dans un tableur externe.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|          <img src="Icons/Nesting.svg" width="32">          | Nesting                       | Lance le calepinage à partir de la Spreadsheet BOM, place le résultat dans un nouveau document.<br>Remarque: les algorithmes de calepinage sont assez basiques. Pas assez performants pour optimiser la découpe d'un panneau, mais suffisant pour estimer le nombre de panneaux. Plus précisément la manière d'optimiser la découpe n'est pas un choix universel, et peu de stratégies ont été codées.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| <img src="Icons/CopyToExternalSpreadsheet.svg" width="32"> | Copy to external spreadsheet  | Boite de dialogue qui permet de définir les valeurs de la Spreadsheet BOM à exporter. Lance l'export qui consiste à écrire les valeurs des cellules dans un fichier texte. Ensuite des scripts python externes (obligatoire car le code python de FreeCAD ne permet pas d'accéder à LibreOffice, en tous cas je n'ai pas trouvé de solutions). Les scripts externes [[bridge_watcher.py]] (qui appelle [[bridge_calc.py]]) lance LibreOffice Calc en mode écoute, vérifie le contenu du fichier texte avec les valeurs, ouvre le fichier Calc ou y accède, et copie les valeurs.<br>Cas d'usage: je m'en sers pour remplir mon fichier Calc de chiffrage qui contient aussi un tableau croisé dynamique pour la feuille de débit. Un autre usage est le remplissage du formulaire de découpe d'un fournisseur de panneau, avec l'indication des chants à coller le cas échéant.<br>Gain de temps important par rapport au copier-coller quand on modifie/corrige le meuble plusieurs fois juste avant la fabrication (ou l'envoi de la fiche de débit au fournisseur).                                                                                                 |
|          <img src="Icons/layers.svg" width="32">           | Current panel choice          | Pour choisir le panneau par défaut utilisé lors de l'ajout de composants.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |

## Paramètres

### Groupe : Chassis

| Propriété | Type | Valeur | Description |
| --- | --- | --- | --- |
| Chassis_epaisseur | PropertyLength | 22.0 mm | Epaisseur du matériau utilisé pour le châssis |
| Chassis_hauteur | PropertyLength | 80.0 mm | Distance entre le bas du caisson et le sol |
| Chassis_marge_verrin | PropertyLength | 10.0 mm | La hauteur réelle du châssis doit permettre d'absorber les aléas du sol, ce paramètre indique la marge à utiliser. C'est la hauteur maxi d'une bosse du sol qui peut être absorbée sans que la hauteur du meuble augmente |
| Chassis_retrait_montant_droit | PropertyLength | 40.0 mm | Paramètre qui positionne la plinthe fixée sur le châssis, ou marge à utiliser pour ne pas être géné par la plinthe d'un mur adjacent |
| Chassis_retrait_montant_gauche | PropertyLength | 40.0 mm | Paramètre qui positionne la plinthe fixée sur le châssis, ou marge à utiliser pour ne pas être géné par la plinthe d'un mur adjacent |
| Chassis_retrait_traverse_arriere | PropertyLength | 30.0 mm | En général c'est la marge pour ne pas buter sur la plinthe du mur contre lequel le meuble est placé |
| Chassis_retrait_traverse_avant | PropertyLength | 40.0 mm | Si cette valeur vaut l'épaisseur de la plinthe, la plinthe est alignée avec le montant |
### Groupe : Configuration

| Propriété | Type | Valeur | Description |
| --- | --- | --- | --- |
| Configuration_Fond | PropertyBool | True | Obsolète. A vérifier pour supprimer le paramètre |
| Configuration_Montant_droit_dessus | PropertyBool | True |  |
| Configuration_Montant_gauche_dessus | PropertyBool | True |  |
| Configuration_Plinthe | PropertyBool | True | Prise en compte ou non du châssis et des plinthes pour la hauteur du caisson. Typique vrai pour un meuble posé au sol, faux pour un caisson suspendu. |
| Configuration_Traverse_haute_droit_dessus | PropertyBool | True |  |
| Configuration_Traverse_haute_gauche_dessus | PropertyBool | True |  |
| Configuration_fileur_droit | PropertyBool | True | Prise en compte du fileur dans la largeur du caisson |
| Configuration_fileur_gauche | PropertyBool | True | Prise en compte du fileur dans la largeur du caisson |
| Configuration_fileur_haut | PropertyBool | False | Prise en compte du fileur dans la hauteur du caisson |
### Groupe : Facades

| Propriété | Type | Valeur | Description |
| --- | --- | --- | --- |
| Facades_jeu_en_profondeur | PropertyLength | 1.5 mm | Distance entre une porte et le caisson. 1.5mm est la valeur nominale de charnières Blum par exemple |
| Facades_jeu_hauteur | PropertyLength | 1.0 mm | Abitrairement la moitié du jeu réel. Car avec plusieurs façades l'une au-dessus de l'autre, le jeu obtenu est le double de cette valeur. |
| Facades_jeu_largeur | PropertyLength | 1.0 mm | Même remarque que pour la hauteur |
### Groupe : Fileurs

| Propriété | Type | Valeur | Description |
| --- | --- | --- | --- |
| Fileurs_hauteur_haut | PropertyLength | 30.0 mm | Distance entre le mur ou ce qui est autour du meuble et le caisson. |
| Fileurs_largeur_droite | PropertyLength | 30.0 mm | idem hauteur |
| Fileurs_largeur_gauche | PropertyLength | 30.0 mm | idem hauteur |
| Fileurs_marge_decoupe | PropertyLength | 15.0 mm | Ajouté à la largeur ou hauteur du fileur pour avoir la taille réelle de la pièce de bois à découper |
| Fileurs_retrait_en_profondeur | PropertyDistance | 0.0 mm | Pour pouvoir positionner les fileurs dans le plan des façades ou en retrait |
### Groupe : Fond

| Propriété | Type | Valeur | Description |
| --- | --- | --- | --- |
| Fond_depassement_rainure | PropertyLength | 5.0 mm |  |
| Fond_epaisseur | PropertyLength | 8.0 mm |  |
| Fond_retrait | PropertyLength | 12.0 mm | Avec ces valeurs, le fond enlève (épaisseur+retrait) = 8+12 = 20mm de profondeur utile au meuble par rapport à la profondeur du caisson. |
### Groupe : Hors_tout

| Propriété | Type | Valeur | Description |
| --- | --- | --- | --- |
| Hors_tout_epaisseur | PropertyLength | 19.0 mm | En l'état du projet c'est l'épaisseur de tous les panneaux du meuble |
| Hors_tout_epaisseur_2 | PropertyLength | 38.0 mm | 2ème valeur exploitable par les composants en changeant leurs formules. Seuls les montants gauche et droit ont un paramètre qui permet de choisir entre les 2 épaisseurs des Paramètres.                                                                                                                                                                                           meuble et de la présence des fileurs |
| Hors_tout_hauteur | PropertyLength | 2400.0 mm |  |
| Hors_tout_hauteur_caisson | PropertyLength | Hors_tout_hauteur - (Configuration_Plinthe == True ? Chassis_hauteur : 0 mm) - (Configuration_fileur_haut == True ? Fileurs_hauteur_haut : 0 mm) | Déduite de la hauteur du meuble en fonction du châssis et du fileur haut |
| Hors_tout_largeur | PropertyLength | 1000.0 mm |  |
| Hors_tout_largeur_caisson | PropertyLength | Hors_tout_largeur - (Configuration_fileur_gauche == True ? Fileurs_largeur_gauche : 0 mm) - (Configuration_fileur_droit == True ? Fileurs_largeur_droite : 0 mm) | Déduite de la largeur du |
| Hors_tout_profondeur | PropertyLength | 600.0 mm |  |
### Groupe : Matrice

| Propriété | Type | Valeur | Description |
| --- | --- | --- | --- |
| Matrice_Colonne_1 | PropertyLength | Matrice_largeur_fraction_1 | Ces propriétés du groupe Matrice servent à positionner des montants ou tablettes à des fractions de la largeur ou hauteur du caisson. Soit pour avoir des volumes de tailles identiques, soit pour avoir des façades de tailles identiques.<br>Ces propriétés sont alors utilisées dans les expressions de Placement des composants.<br>L'outil "Ajout d'étagère" fait à peu près la même chose. |
| Matrice_Colonne_2 | PropertyLength | 0.0 mm |  |
| Matrice_Ligne_1 | PropertyLength | 300.0 mm |  |
| Matrice_Ligne_2 | PropertyLength | 500.0 mm |  |
| Matrice_colonne_1_complementaire | PropertyLength | Hors_tout_largeur - Matrice_Colonne_1 - 3 * Hors_tout_epaisseur |  |
| Matrice_colonne_2_complementaire | PropertyLength | Hors_tout_largeur - Matrice_Colonne_1 - Matrice_Colonne_2 - 4 * Hors_tout_epaisseur |  |
| Matrice_fraction_1 | PropertyInteger | 2 |  |
| Matrice_fraction_2 | PropertyInteger | 3 |  |
| Matrice_largeur_fraction_1 | PropertyLength | (Hors_tout_largeur_caisson - (Matrice_fraction_1 + 1) * Hors_tout_epaisseur) / Matrice_fraction_1 |  |
| Matrice_largeur_fraction_2 | PropertyLength | (Hors_tout_largeur_caisson - (Matrice_fraction_2 + 1) * Hors_tout_epaisseur) / Matrice_fraction_2 |  |
| offset_1 | PropertyLength | 50.0 mm | Variable utilisée pour mettre en retrait des composants internes au meuble. Cas typique: ajout de tiroirs intérieurs "en applique" ou derrière des charnières. |
### Groupe : Plinthes

| Propriété | Type | Valeur | Description |
| --- | --- | --- | --- |
| Plinthes_hauteur | PropertyLength | Chassis_hauteur + Fileurs_marge_decoupe | Hauteur des pièces de bois à découper car intègre la marge de découpe du groupe Fileurs |
### Groupe : Plateau

| Propriété | Type | Valeur | Description |
| --- | --- | --- | --- |
| Plt_epaisseur | PropertyLength | 26.0 mm |  |
| Plt_ext_arriere_hors_tout | PropertyBool | True | Quand le plateau doit s'ajuster aux parois qui l'entoure (les murs), la marge de découpe du groupe Fileurs est utilisée pour avoir la taille de la pièce de bois avant découpe sur le chantier. |
| Plt_ext_avant_hors_tout | PropertyBool | True | Si Vrai le plateau recouvre les façades |
| Plt_ext_droite_hors_tout | PropertyBool | True | Idem hauteur |
| Plt_ext_gauche_hors_tout | PropertyBool | True | Idem hauteur |
| Plt_extension_arriere | PropertyLength | Plt_ext_arriere_hors_tout * Fileurs_marge_decoupe |  |
| Plt_extension_droite | PropertyLength | Plt_ext_droite_hors_tout * (Fileurs_marge_decoupe + Configuration_fileur_droit * Fileurs_largeur_droite) |  |
| Plt_extension_gauche | PropertyLength | Plt_ext_gauche_hors_tout * (Fileurs_marge_decoupe + Configuration_fileur_gauche * Fileurs_largeur_gauche) |  |
| Plt_presence | PropertyBool | True | Prise en compte du plateau dans la hauteur du meuble, réduisant la hauteur du caisson. |
| Plt_retrait_avant | PropertyDistance | -(Facades_jeu_en_profondeur + Hors_tout_epaisseur) * Plt_ext_avant_hors_tout |  |
### Groupe : Tablettes

| Propriété | Type | Valeur | Description |
| --- | --- | --- | --- |
| Tablettes_jeu_lateral | PropertyLength | 1.0 mm | Jeu des étagères avec les crémaillères ou panneaux (côtés et fond) |
## Méthode manuelle
**Si une macro ne fonctionne pas ou plus**

Une contrainte de base du modèle générique du meuble que j'ai voulu est de ne pas dépendre d'un atelier, de macros ou autres scripts, qui deviennent forcément obsolètes sans maintenance. Le modèle CAO FreeCAD devait être exploitable même après plusieurs années. Dans les limites de la rétrocompatibilité de FreeCAD.

Pour ce faire il faut avoir tous les composants de base dans un ou plusieurs fichiers pour pouvoir les dupliquer dans le meuble en cours de conception. Avec des expressions dans les propriétés des objets la duplication n'est pas évidente, par défaut FreeCAD ajoute les dépendances, et le modèle devient ingérable car le VarSet des paramètres est dupliqué également.

La méthode que j'ai utilisé avant les macros, c'est de déployer toute l'arborescence d'un conteneur Part, donc l'objet Origin du Part, du Body, de tout ce qu'il contient... Là le raccourci clavier Alt + `flèche vers le bas` aide bien. Ensuite il faut tout sélectionner, faire un copier, cliquer sur `Utiliser la sélection d'origine` et vous obtiendrez les objets dupliqués sans erreur.
Enfin il faut modifier les paramètres des composants, par exemple pour un montant il faut cliquer sur les propriétés obj_dessus, obj_dessous pour sélectionner les traverses haute et basse sur lesquelles le montant est fixé.

## Intégration IA

A titre expérimental j'ai relié un LLM à ces outils de conception de meuble paramétrique. Pas pour gagner en performace car avec mes outils je vais plus vite qu'à faire des prompts qui donnent des résultats approximatifs. Intéressé par l'intégration de l'IA dans l'ingénierie, industrielle, autre que le monde du développement logiciel, j'ai voulu tester le cas de la CAO, et dans le cadre simple de la conception de meubles qui n'a pas de formes complexes.

L'architecture est la suivante:
_Scriptes python externes à FreeCAD : (autre dépôt github à créer) _
 - boite de dialogue `"Tchat"` connecté à une API Mistr
 - al ou Groq, permettant d'appeler des outils via un serveur MCP
 - serveur MCP qui communique avec un serveur RPC lancé dans FreeCAD
 _Macros FreeCAD :_
- Macros qui lance, arrête ou relance le serveur RPC
- Macros des actions possibles dans FreeCAD, dérivées des outils de conception
- une macro qui génère une géométrie fonctionnelle du meuble: les cellules, alvéoles qui représentent les espaces de rangement. C'est ce qui donne au LLM la capacité de "comprendre" le meuble. Chaque cellule peut avoir un rôle, comme une penderie à chemises, ce qui permet au LLM de proposer un volume cohérent avec l'usage

A ce jour je n'utilise que des plans gratuits pour accéder aux API des modèles LLM. J’atteins très vite les limites de requêtes par minute ou par jour.
La chaine LLM <-> FreeCAD est en place, et je peux jouer sur le choix des outils FreeCAD à rendre accessibles, la remontée d'informations du modèle au LLM, l'optimisation du contexte envoyé à chaque prompt utilisateur.

|                        Icon                         | Command                | Description                                                            |
| :-------------------------------------------------: | :--------------------- | :--------------------------------------------------------------------- |
|  <img src="Icons/rpc_server_start.svg" width="32">  | Start the RPC server   | Start the RPC server                                                   |
|  <img src="Icons/rpc_server_stop.svg" width="32">   | Stop the RPC server    | Stop the RPC server                                                    |
| <img src="Icons/rpc_server_restart.svg" width="32"> | Restart the RPC server | Restart the RPC server                                                 |
|                                                     | Geo meuble             | Geométrie simplifiée du meuble, créée dans FreeCAD et transmise au LLM |

## Installation

### Atelier personnalisé (workbench)
Dans la console FreeCAD, taper `App.getUserAppDataDir()` pour obtenir le répertoire utilisateur. Dans ce dossier, créer le répertoire "Mod" s'il n'existe pas.
Dans un terminal, aller dans le répertoire Mod, puis lancer la commande:
```powershell
  git clone https://github.com/Matt-Kron/FreeCAD_BespokeFurniture.git
```

### Mode macros, essentiellement pour du développement
Pour éviter les problèmes de reload() à chaque modification du code, j'ai développé toutes les fonctionnalités comme de simples macros, réunies dans un sous-dossier du répertoire macro de l'utilisateur et j'ai créé une barre d'outils pour appeler ces macros.
Dans FreeCAD, récupérer le répertoire des macros avec fc_macros=App.getUserMacroDir()  
Dans un terminal en remplaçant fc_macros par le bon répertoire:  
**Ubuntu (ou autre distri linux):**
```bash
cd fc_macros
git clone https://github.com/Matt-Kron/FreeCAD_BespokeFurniture.git
ln -s ./FreeCAD_BespokeFurniture/utils/BespokeFurnitureToolbarCreation.py BespokeFurnitureToolbarCreation.py
```

**Windows:**
```powershell
cd fc_macros
git clone https://github.com/Matt-Kron/FreeCAD_BespokeFurniture.git
```

dans un terminal en mode administrateur pour créer le lien symbolique
```powershell
cd fc_macros
mklink BespokeFurnitureToolbarCreation.py .\FreeCAD_BespokeFurniture\utils\BespokeFurnitureToolbarCreation.py
```

Puis dans FreeCAD, lancer la macro BespokeFurnitureToolbarCreation.py pour ajouter la barre d'outils