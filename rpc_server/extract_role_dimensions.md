**v(a, b, c)** représente un vecteur selon (x, y, z)
**l(l, m, n)** représente des longueurs selon les axes x, y et z
**role**: panneau vertical,
  la propriété `Label` de l'objet contient l'une des chaines de caractères de la liste (mt, mt d, mt g, mt i)
  - **dimensions** = l(largeur, profondeur, hauteur): les dimensions qui correspondent à l(BoundBox.XLength, BoundBox.YLength, BoundBox;ZLength)
  - **position** = v(Placement.Base.x, Placement.Base.y, Placement.Base.z): valeurs du vecteur Placement.Base de l'objet App::Part parent. Si plusieurs parents sont imbriqués, il faut appliquer position.add(parent.Placement.Base) à chaque parent de niveau inférieur.
  représentation géométrique simplifiée:
   -  **segment**:
      - **origine** = position
      - **longueur** = l(0, 0, dimensions.hauteur)

**role**: panneau horizontal,
  la propriété Label de l'objet contient l'une des chaines de caractères de la liste (tv, tv sup, tv inf, traverse, tab, tablette)
  - **dimensions** = l(largeur, profondeur, hauteur): les dimensions qui correspondent à l(BoundBox.XLength, BoundBox.YLength, BoundBox;ZLength)
  - **position** = v(Placement.Base.x, Placement.Base.y, Placement.Base.z): valeurs du vecteur Placement.Base de l'objet App::Part parent. Si plusieurs parents sont imbriqués, il faut appliquer position.add(parent.Placement.Base) à chaque parent de niveau inférieur.
  représentation géométrique simplifiée:
  - **segment**:
	  - **origine** = position
	  - **longueur** = l(dimensions.largeur, 0, 0)

**role**: panneau porte,
  la propriété Label de l'objet contient l'une des chaines de caractères de la liste (porte, facade)
  - **dimensions** = l(largeur, profondeur, hauteur): les dimensions qui correspondent à l(BoundBox.XLength, BoundBox.YLength, BoundBox;ZLength)
  - **position** = v(Placement.Base.x, Placement.Base.y, Placement.Base.z): valeurs du vecteur Placement.Base de l'objet App::Part parent. Si plusieurs parents sont imbriqués, il faut appliquer position.add(parent.Placement.Base) à chaque parent de niveau inférieur.
  représentation géométrique simplifiée:
 - **rectangle**:
	 - **origine** = position
	 - **longueur** = l(dimensions.largeur, 0, 0)
