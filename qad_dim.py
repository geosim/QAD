# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per la gestione delle quote
 
                              -------------------
        begin                : 2014-02-20
        copyright            : (C) 2013 IREN Acqua Gas SpA
        email                : geosim.dev@irenacquagas.it
        developers           : roberto poltini (roberto.poltini@irenacquagas.it)
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import math


import qad_debug
import qad_utils
from qad_variables import *


#===============================================================================
# QadDimTypeEnum class.
#===============================================================================
class QadDimTypeEnum():
   ALIGNED   = 0 # quota lineare allineata ai punti di origine delle linee di estensione
   ANGULAR   = 1 # quota angolare, misura l'angolo tra i 3 punti o tra gli oggetti selezionati
   BASE_LINE = 2 # quota lineare, angolare o coordinata a partire dalla linea di base della quota precedente o di una quota selezionata
   CENTER    = 3 # crea il centro o le linee d'asse di cerchi e archi
   DIAMETER  = 4 # quota per il diametro di un cerchio o di un arco
   LEADER    = 5 # crea una linea che consente di collegare un'annotazione ad una lavorazione
   LINEAR    = 6 # quota lineare con una linea di quota orizzontale, verticale o ruotata
   RADIAL    = 7 # quota radiale, misura il raggio di un cerchio o di un arco selezionato e visualizza il testo di quota con un simbolo di raggio davanti
   DIAMETER  = 8 # quota per il diametro di un cerchio o di un arco


#===============================================================================
# QadDimStyleTxtVerticalPosEnum class.
#===============================================================================
class QadDimStyleTxtVerticalPosEnum():
   CENTERED_LINE = 0 # testo centrato alla linea di quota
   ABOVE_LINE    = 1 # testo sopra alla linea di quota
   BELOW_LINE    = 2 # testo sotto alla linea di quota 


#===============================================================================
# QadDimStyleTxtHorizontalPosEnum class.
#===============================================================================
class QadDimStyleTxtHorizontalPosEnum():
   CENTERED_LINE      = 0 # testo centrato alla linea di quota
   FIRST_EXT_LINE     = 1 # testo vicino alla prima linea di estensione
   SECOND_EXT_LINE    = 2 # testo vicino alla seconda linea di estensione
   FIRST_EXT_LINE_UP  = 3 # testo sopra e allineato alla prima linea di estensione
   SECOND_EXT_LINE_UP = 4 # testo sopra e allineato alla seconda linea di estensione


#===============================================================================
# QadDimStyleTxtRotEnum class.
#===============================================================================
class QadDimStyleTxtRotModeEnum():
   HORIZONTAL   = 0 # testo orizzontale
   ALIGNED_LINE = 1 # testo allineato con la linea di quota
   ISO          = 2 # testo allineato con la linea di quota se tra le linee di estensione,
                    # altrimenti testo orizzontale


#===============================================================================
# QadDimStyleArcSymbolPosEnum class.
#===============================================================================
class QadDimStyleArcSymbolPosEnum():
   BEFORE_TEXT = 0 # simbolo prima del testo
   ABOVE_TEXT  = 1 # simbolo sopra il testo
   NONE        = 2 # niente simbolo


#===============================================================================
# QadDimStyleTextBlocksAdjustEnum class.
#===============================================================================
class QadDimStyleTextBlocksAdjustEnum():
   BOTH_OUTSIDE_EXT_LINES = 0 # sposta testo e freccie fuori dalle linee di estensione
   FIRST_BLOCKS_THEN_TEXT = 1 # sposta prima le freccie poi, se non basta, anche il testo
   FIRST_TEXT_THEN_BLOCKS = 2 # sposta prima il testo poi, se non basta, anche le freccie
   WHICHEVER_FITS_BEST    = 3 # Sposta indistintamente il testo o le frecce (l'oggetto che si adatta meglio)


#===============================================================================
# QadDim dimension style class
#===============================================================================
class QadDimStyle():   
   name = "standard" # nome dello stile
   dimType = QadDimTypeEnum.ALIGNED # tipo di quotatura
   
   # testo di quota
   textPrefix = "" # prefisso per il testo della quota
   textSuffix = "" # suffisso per il testo della quota
   textSuppressLeadingZeros = True # per sopprimere o meno gli zero all'inizio del testo
   textSuppressTrailingZeros = True # per sopprimere o meno gli zero in fondo al testo
   textHeight = 1.0 # altezza testo (DIMTXT)
   textVerticalPos = QadDimStyleTxtVerticalPosEnum.ABOVE_LINE # posizione verticale del testo rispetto la linea di quota (DIMTAD)
   textHorizontalPos = QadDimStyleTxtHorizontalPosEnum.CENTERED_LINE # posizione orizzontale del testo rispetto la linea di quota (DIMTAD)
   textOffsetDist = 0.5 # distanza aggiunta intorno al testo quando per inserirlo viene spezzata la linea di quota
   textRotMode = QadDimStyleTxtRotModeEnum.ALIGNED_LINE # modalità di rotazione del testo
   
   # linee di quota
   line1Show = True # Mostra o nasconde la prima linea di quota (DIMSD1)
   line2Show = True # Mostra o nasconde la seconda linea di quota (DIMSD2)
   lineSpaceOffset = 3.75 # Controlla la spaziatura delle linee di quota nelle quote da linea di base (DIMDLI)

   # simboli per linee di quota
   block1Name = "triangle2" # nome del simbolo da usare come punta della freccia sulla prima linea di quota (DIMBLK1)
   block2Name = "triangle2"  # nome del simbolo da usare come punta della freccia sulla seconda linea di quota (DIMBLK2)
   blockLeaderName = "triangle2" # nome del simbolo da usare come punta della freccia sulla linea della direttrice (DIMLDRBLK)
   blockSize = 1.0 # dimensione del simbolo (DIMASZ)
   blockSuppressionForNoSpace = False # Sopprime le punte della frecce se non c'è spazio sufficiente all'interno delle linee di estensione (DIMSOXD)
   centerMarkSize = 0.0 # disegna o meno il marcatore di centro o le linee d'asse per le quote create con
                        # DIMCENTER, DIMDIAMETER, e DIMRADIUS (DIMCEN).
                        # 0 = niente, > 0 dimensione marcatore di centro, < 0 dimensione linee d'asse
   arcSymb = QadDimStyleArcSymbolPosEnum.BEFORE_TEXT # disegna o meno il simbolo dell'arco con DIMARC (DIMARCSYM). 

   # adattamento del testo e delle freccie
   textBlockAdjust = QadDimStyleTextBlocksAdjustEnum.WHICHEVER_FITS_BEST
   
   # linee di estensione
   extLine1Show = True # Mostra o nasconde la prima linea di estensione (DIMSE1)
   extLine2Show = True # Mostra o nasconde la seconda linea di estensione (DIMSE2)
   extLineOffset = 0.0 # distanza della linea di estensione oltre la linea di quota (DIMEXE)
   extLineOffset = 0.0 # distanza della linea di estensione dai punti da quotare (DIMEXO)
   extLineLent = False # Attiva lunghezza fissa delle line di estensione (DIMFXLON)
   extLineLent = 1.0 # lunghezza fissa delle line di estensione (DIMFXL)
                     # (il punto medio va sulla linea di quota ma la linea di estensione non va oltre il punto da quotare)
       
   
   def __init__(self, dim = None):
      if dim is None:
         return
      #self.set(arc.center, arc.radius, arc.startAngle, arc.endAngle)
