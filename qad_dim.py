# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per la gestione delle quote
 
                              -------------------
        begin                : 2014-02-20
        copyright            : iiiii
        email                : hhhhh
        developers           : bbbbb aaaaa ggggg
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
import codecs
import ConfigParser
import math
import sys


import qad_utils
import qad_stretch_fun
import qad_layer
import qad_label
from qad_entity import *
from qad_variables import *


"""
La classe quotatura é composta da tre layer: testo, linea, simbolo con lo stesso sistema di coordinate.

Il layer testo deve avere tutte le caratteristiche del layer testo di QAD ed in più:
- il posizionamento dell'etichetta con modalita "Intorno al punto" con distanza = 0 
  (che vuol dire punto di inserimento in basso a sx)
- la dimensione del testo in unità mappa (la dimensione varia a seconda dello zoom).
- dimStyleFieldName = "dim_style"; nome del campo che contiene il nome dello stile di quota (opzionale)
- dimTypeFieldName = "dim_type"; nome del campo che contiene il tipo dello stile di quota (opzionale)
- l'opzione "Mostra etichette capovolte" deve essere su "sempre" nel tab "Etichette"->"Visualizzazione"
- rotFieldName = "rot"; nome del campo che contiene la rotazione del testo
- la rotazione deve essere letta dal campo indicato da rotFieldName
- idFieldName = "id"; nome del campo che contiene il codice della quota (opzionale)
- la rotazione deve essere derivata dal campo rotFieldName
- il font del carattere può essere derivata da un campo
- la dimensione del carattere può essere derivata da un campo
- il colore del testo può essere derivato da un campo (opzionale)


Il layer simbolo deve avere tutte le caratteristiche del layer simbolo di QAD ed in più:
- il simbolo freccia con rotazione 0 deve essere orizzontale con la freccia rivolta verso destra
  ed il suo punto di inserimento deve essere sulla punta della freccia
- la dimensione del simbolo in unità mappa (la dimensione varia a seconda dello zoom),
  impostare la dimensione del simbolo in modo che la larghezza della freccia sia 1 unità di mappa.
- componentFieldName = "type"; nome del campo che contiene il tipo di componente della quota (vedi QadDimComponentEnum) (opzionale)
- symbolFieldName = "block"; nome del campo che contiene il nome del simbolo (opzionale)
- idParentFieldName = "id_parent"; nome del campo che contiene il codice del testo della quota (opzionale)
- scaleFieldName = "scale"; nome del campo che contiene il fattore di scala del simbolo (opzionale)
  se usato usare lo stile "singolo simbolo" (unico che consente di impostare la scala come diametro scala)
  la scala deve essere impostata su attraverso Stile->avanzato->campo di dimensione della scala-><nome del campo scala>
  la modalità di scala deve essere impostata su attraverso Stile->avanzato->campo di dimensione della scala->diametro scala
- rotFieldName = "rot"; nome del campo che contiene la rotazione del simbolo 
  la rotazione deve essere letta dal campo indicato da rotFieldName (360-rotFieldName)

Il layer linea deve avere tutte le caratteristiche del layer linea ed in più:
- componentFieldName = "type"; nome del campo che contiene il tipo di componente della quota (vedi QadDimComponentEnum) (opzionale)
- lineTypeFieldName = "line_type"; nome del campo che contiene il tipolinea (opzionale)
- colorFieldName = "color"; nome del campo che contiene il colore 'r,g,b,alpha'; alpha é opzionale (0=trasparente, 255=opaco) (opzionale)
- idParentFieldName = "id_parent"; nome del campo che contiene il codice del testo della quota (opzionale)

"""


#===============================================================================
# QadDimTypeEnum class.   
#===============================================================================
class QadDimTypeEnum():
   ALIGNED    = "AL" # quota lineare allineata ai punti di origine delle linee di estensione
   ANGULAR    = "AN" # quota angolare, misura l'angolo tra i 3 punti o tra gli oggetti selezionati
   BASE_LINE  = "BL" # quota lineare, angolare o coordinata a partire dalla linea di base della quota precedente o di una quota selezionata
   DIAMETER   = "DI" # quota per il diametro di un cerchio o di un arco
   LEADER     = "LD" # crea una linea che consente di collegare un'annotazione ad una lavorazione
   LINEAR     = "LI" # quota lineare con una linea di quota orizzontale o verticale
   RADIUS     = "RA" # quota radiale, misura il raggio di un cerchio o di un arco selezionato e visualizza il testo di quota con un simbolo di raggio davanti
   ARC_LENTGH = "AR" # quota per la lunghezza di un cerchio o di un arco


#===============================================================================
# QadDimComponentEnum class.
#===============================================================================
class QadDimComponentEnum():
   DIM_LINE1 = "D1" # linea di quota ("Dimension line 1")
   DIM_LINE2 = "D2" # linea di quota ("Dimension line 2")
   EXT_LINE1 = "E1" # prima linea di estensione ("Extension line 1")
   EXT_LINE2 = "E2" # seconda linea di estensione ("Extension line 2")
   LEADER_LINE = "L" # linea porta quota usata quando il testo é fuori dalla quota ("Leader")
   BLOCK1 = "B1" # primo blocco della freccia ("Block 1")
   BLOCK2 = "B2" # secondo blocco della freccia ("Block 2")
   LEADER_BLOCK = "LB" # blocco della freccia nel caso leader ("Leader Block")
   ARC_BLOCK = "AB" # simbolo dell'arco ("Arc Block")
   DIM_PT1 = "D1" # primo punto da quotare ("Dimension point 1")
   DIM_PT2 = "D2" # secondo punto da quotare ("Dimension point 2")
   TEXT_PT = "T" # punto del testo di quota ("Text")


#===============================================================================
# QadDimStyleAlignmentEnum class.
#===============================================================================
class QadDimStyleAlignmentEnum():
   HORIZONTAL      = 0 # orizzontale
   VERTICAL        = 1 # verticale
   ALIGNED         = 2 # allineata
   FORCED_ROTATION = 3 # rotazione forzata


#===============================================================================
# QadDimStyleTxtVerticalPosEnum class.
#===============================================================================
class QadDimStyleTxtVerticalPosEnum():
   CENTERED_LINE = 0 # testo centrato alla linea di quota
   ABOVE_LINE    = 1 # testo sopra alla linea di quota ma nel caso la linea di quota non sia orizzontale 
                     # e il testo sia dentro le linee di estensione e forzato orizzontale allora il testo diventa centrato
   EXTERN_LINE   = 2 # testo posizionato nella parte opposta ai punti di quotatura 
   BELOW_LINE    = 4 # testo sotto alla linea di quota ma nel caso la linea di quota non sia orizzontale 
                     # e il testo sia dentro le linee di estensione e forzato orizzontale allora il testo diventa centrato


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
   HORIZONTAL      = 0 # testo orizzontale
   ALIGNED_LINE    = 1 # testo allineato con la linea di quota
   ISO             = 2 # testo allineato con la linea di quota se tra le linee di estensione,
                       # altrimenti testo orizzontale
   FORCED_ROTATION = 3 # testo con rotazione forzata


#===============================================================================
# QadDimStyleArcSymbolPosEnum class.
#===============================================================================
class QadDimStyleArcSymbolPosEnum():
   BEFORE_TEXT = 0 # simbolo prima del testo
   ABOVE_TEXT  = 1 # simbolo sopra il testo
   NONE        = 2 # niente simbolo


#===============================================================================
# QadDimStyleArcSymbolPosEnum class.
#===============================================================================
class QadDimStyleTxtDirectionEnum():
   SX_TO_DX = 0 # da sinistra a destra
   DX_TO_SX = 1 # da destra a sinistra 


#===============================================================================
# QadDimStyleTextBlocksAdjustEnum class.
#===============================================================================
class QadDimStyleTextBlocksAdjustEnum():
   BOTH_OUTSIDE_EXT_LINES = 0 # sposta testo e frecce fuori dalle linee di estensione
   FIRST_BLOCKS_THEN_TEXT = 1 # sposta prima le frecce poi, se non basta, anche il testo
   FIRST_TEXT_THEN_BLOCKS = 2 # sposta prima il testo poi, se non basta, anche le frecce
   WHICHEVER_FITS_BEST    = 3 # Sposta indistintamente il testo o le frecce (l'oggetto che si adatta meglio)


#===============================================================================
# QadDim dimension style class
#===============================================================================
class QadDimStyle():     
          
   def __init__(self, dimStyle = None):
      self.name = "standard" # nome dello stile
      self.description = ""
      self.path = "" # percorso e nome del file in cui è stato salvato/caricato
      self.dimType = QadDimTypeEnum.ALIGNED # tipo di quotatura
      
      # testo di quota
      self.textPrefix = "" # prefisso per il testo della quota
      self.textSuffix = "" # suffisso per il testo della quota
      self.textSuppressLeadingZeros = False # per sopprimere o meno gli zero all'inizio del testo
      self.textDecimalZerosSuppression = True # per sopprimere gli zero finali nei decimali
      self.textHeight = 1.0 # altezza testo (DIMTXT) in unità di mappa
      self.textVerticalPos = QadDimStyleTxtVerticalPosEnum.ABOVE_LINE # posizione verticale del testo rispetto la linea di quota (DIMTAD)
      self.textHorizontalPos = QadDimStyleTxtHorizontalPosEnum.CENTERED_LINE # posizione orizzontale del testo rispetto la linea di quota (DIMTAD)
      self.textOffsetDist = 0.5 # distanza aggiunta intorno al testo quando per inserirlo viene spezzata la linea di quota (DIMGAP)
      self.textRotMode = QadDimStyleTxtRotModeEnum.ALIGNED_LINE # modalità di rotazione del testo (DIMTIH e DIMTOH)
      self.textForcedRot = 0.0 # rotazione forzata del testo
      self.textDecimals = 2 # numero di decimali (DIMDEC)
      self.textDecimalSep = "." # Separatore dei decimali (DIMDSEP)
      self.textFont = "Arial" # nome del font di testo (DIMTXSTY)
      self.textColor = "255,255,255,255" # Colore per i testi della quota (DIMCLRT); bianco con opacità totale
      self.textDirection = QadDimStyleTxtDirectionEnum.SX_TO_DX # specifica la direzione del testo di quota (DIMTXTDIRECTION) 0 = da sx a dx, 1 = da dx a sx
      self.arcSymbPos = QadDimStyleArcSymbolPosEnum.BEFORE_TEXT # disegna o meno il simbolo dell'arco con DIMARC (DIMARCSYM). 
      
      # linee di quota
      self.dimLine1Show = True # Mostra o nasconde la prima linea di quota (DIMSD1)
      self.dimLine2Show = True # Mostra o nasconde la seconda linea di quota (DIMSD2)
      self.dimLineLineType = "continuous" # Tipo di linea per le linee di quota (DIMLTYPE)
      self.dimLineColor = "255,255,255,255" # Colore per le linee di quota (DIMCLRD); bianco con opacità totale
      self.dimLineSpaceOffset = 3.75 # Controlla la spaziatura delle linee di quota nelle quote da linea di base (DIMDLI)
   
      # simboli per linee di quota
      # il blocco per la freccia é una freccia verso destra con il punto di inserimento sulla punta della freccia 
      self.block1Name = "triangle2" # nome del simbolo da usare come punta della freccia sulla prima linea di quota (DIMBLK1)
      self.block2Name = "triangle2"  # nome del simbolo da usare come punta della freccia sulla seconda linea di quota (DIMBLK2)
      self.blockLeaderName = "triangle2" # nome del simbolo da usare come punta della freccia sulla linea della direttrice (DIMLDRBLK)
      self.blockWidth = 0.5 # larghezza del simbolo (in orizzontale) quando la dimensione in unità di mappa = 1 (vedi "triangle2")
      self.blockScale = 1.0 # scala della dimensione del simbolo (DIMASZ)
      self.centerMarkSize = 0.0 # disegna o meno il marcatore di centro o le linee d'asse per le quote create con
                                # DIMCENTER, DIMDIAMETER, e DIMRADIUS (DIMCEN).
                                # 0 = niente, > 0 dimensione marcatore di centro, < 0 dimensione linee d'asse
   
      # adattamento del testo e delle frecce
      self.textBlockAdjust = QadDimStyleTextBlocksAdjustEnum.WHICHEVER_FITS_BEST # (DIMATFIT)
      self.blockSuppressionForNoSpace = False # Sopprime le punte della frecce se non c'é spazio sufficiente all'interno delle linee di estensione (DIMSOXD)
      
      # linee di estensione
      self.extLine1Show = True # Mostra o nasconde la prima linea di estensione (DIMSE1)
      self.extLine2Show = True # Mostra o nasconde la seconda linea di estensione (DIMSE2)
      self.extLine1LineType = "continuous" # Tipo di linea per la prima linea di estensione (DIMLTEX1)
      self.extLine2LineType = "continuous" # Tipo di linea per la seconda linea di estensione (DIMLTEX2)
      self.extLineColor = "255,255,255,255" # Colore per le linee di estensione (DIMCLRE); bianco con opacità totale
      self.extLineOffsetDimLine = 0.0 # distanza della linea di estensione oltre la linea di quota (DIMEXE)
      self.extLineOffsetOrigPoints = 0.0 # distanza della linea di estensione dai punti da quotare (DIMEXO)
      self.extLineIsFixedLen = False # Attiva lunghezza fissa delle line di estensione (DIMFXLON)
      self.extLineFixedLen = 1.0 # lunghezza fissa delle line di estensione (DIMFXL) dalla linea di quota 
                                 # al punto da quotare spostato di extLineOffsetOrigPoints
                                 # (la linea di estensione non va oltre il punto da quotare)
      
      # layer e loro caratteristiche
      # devo allocare i campi a livello di classe QadDimStyle perché QgsFeature.setFields usa solo il puntatore alla lista fields
      # che, se allocata privatamente in qualsiasi funzione, all'uscita della funzione verrebbe distrutta 
      self.textualLayerName = None    # nome layer per memorizzare il testo della quota
      self.__textualLayer = None        # layer per memorizzare il testo della quota
      self.__textFields = None
      self.__textualFeaturePrototype = None
   
      self.linearLayerName = None    # nome layer per memorizzare le linee della quota
      self.__linearLayer = None        # layer per memorizzare le linee della quota
      self.__lineFields = None
      self.__linearFeaturePrototype = None
   
      self.symbolLayerName = None  # nome layer per memorizzare i blocchi delle frecce della quota
      self.__symbolLayer = None      # layer per memorizzare i blocchi delle frecce della quota
      self.__symbolFields = None
      self.__symbolFeaturePrototype = None
      
      self.componentFieldName = "type"      # nome del campo che contiene il tipo di componente della quota (vedi QadDimComponentEnum)
      self.lineTypeFieldName = "line_type"  # nome del campo che contiene il tipolinea
      self.colorFieldName = "color"         # nome del campo che contiene il colore 'r,g,b,alpha'; alpha é opzionale (0=trasparente, 255=opaco)
      self.idFieldName = "id"               # nome del campo che contiene il codice del della quota nel layer di tipo testo
      self.idParentFieldName = "id_parent"  # nome del campo che contiene il codice della quota nei layer simbolo e linea 
      self.dimStyleFieldName = "dim_style"  # nome del campo che contiene il nome dello stile di quota
      self.dimTypeFieldName = "dim_type"    # nome del campo che contiene il tipo dello stile di quota   
      self.symbolFieldName = "block"        # nome del campo che contiene il nome del simbolo
      self.scaleFieldName = "scale"         # nome del campo che contiene la dimensione
      self.rotFieldName = "rot"             # nome del campo che contiene rotazione in gradi
      
      if dimStyle is None:
         return
      self.set(dimStyle)


   #============================================================================
   # FUNZIONI GENERICHE - INIZIO
   #============================================================================

   def set(self, dimStyle):
      self.name = dimStyle.name
      self.description = dimStyle.description
      self.path = dimStyle.path
      self.dimType = dimStyle.dimType
      
      # testo di quota
      self.textPrefix = dimStyle.textPrefix
      self.textSuffix = dimStyle.textSuffix
      self.textSuppressLeadingZeros = dimStyle.textSuppressLeadingZeros
      self.textDecimaZerosSuppression = dimStyle.textDecimalZerosSuppression
      self.textHeight = dimStyle.textHeight
      self.textVerticalPos = dimStyle.textVerticalPos
      self.textHorizontalPos = dimStyle.textHorizontalPos
      self.textOffsetDist = dimStyle.textOffsetDist
      self.textRotMode = dimStyle.textRotMode
      self.textForcedRot = dimStyle.textForcedRot
      self.textDecimals = dimStyle.textDecimals
      self.textDecimalSep = dimStyle.textDecimalSep
      self.textFont = dimStyle.textFont
      self.textColor = dimStyle.textColor
      self.textDirection = dimStyle.textDirection
      self.arcSymbPos = dimStyle.arcSymbPos
      
      # linee di quota
      self.dimLine1Show = dimStyle.dimLine1Show
      self.dimLine2Show = dimStyle.dimLine2Show
      self.dimLineLineType = dimStyle.dimLineLineType
      self.dimLineColor = dimStyle.dimLineColor
      self.dimLineSpaceOffset = dimStyle.dimLineSpaceOffset
   
      # simboli per linee di quota
      self.block1Name = dimStyle.block1Name
      self.block2Name = dimStyle.block2Name
      self.blockLeaderName = dimStyle.blockLeaderName
      self.blockWidth = dimStyle.blockWidth
      self.blockScale = dimStyle.blockScale
      self.blockSuppressionForNoSpace = dimStyle.blockSuppressionForNoSpace
      self.centerMarkSize = dimStyle.centerMarkSize
   
      # adattamento del testo e delle frecce
      self.textBlockAdjust = dimStyle.textBlockAdjust
      
      # linee di estensione
      self.extLine1Show = dimStyle.extLine1Show
      self.extLine2Show = dimStyle.extLine2Show
      self.extLine1LineType = dimStyle.extLine1LineType
      self.extLine2LineType = dimStyle.extLine2LineType
      self.extLineColor = dimStyle.extLineColor
      self.extLineOffsetDimLine = dimStyle.extLineOffsetDimLine
      self.extLineOffsetOrigPoints = dimStyle.extLineOffsetOrigPoints
      self.extLineIsFixedLen = dimStyle.extLineIsFixedLen
      self.extLineFixedLen = dimStyle.extLineFixedLen
      
      # layer e loro caratteristiche
      self.textualLayerName = dimStyle.textualLayerName
      self.__textualLayer = dimStyle.__textualLayer
      self.__textFields = dimStyle.__textFields
      self.__textualFeaturePrototype = dimStyle.__textualFeaturePrototype   
      self.linearLayerName = dimStyle.linearLayerName
      self.__linearLayer = dimStyle.__linearLayer
      self.__lineFields = dimStyle.__lineFields
      self.__linearFeaturePrototype = dimStyle.__linearFeaturePrototype   
      self.symbolLayerName = dimStyle.symbolLayerName
      self.__symbolLayer = dimStyle.__symbolLayer
      self.__symbolFields = dimStyle.__symbolFields
      self.__symbolFeaturePrototype = dimStyle.__symbolFeaturePrototype   

      self.componentFieldName = dimStyle.componentFieldName
      self.symbolFieldName = dimStyle.symbolFieldName
      self.lineTypeFieldName = dimStyle.lineTypeFieldName
      self.colorFieldName = dimStyle.colorFieldName
      self.idFieldName = dimStyle.idFieldName
      self.idParentFieldName = dimStyle.idParentFieldName
      self.dimStyleFieldName = dimStyle.dimStyleFieldName
      self.dimTypeFieldName = dimStyle.dimTypeFieldName
      self.scaleFieldName = dimStyle.scaleFieldName
      self.rotFieldName = dimStyle.rotFieldName


   #============================================================================
   # getPropList
   #============================================================================
   def getPropList(self):
      proplist = dict() # dizionario di nome con lista [descrizione, valore]
      propDescr = QadMsg.translate("Dimension", "Name")
      proplist["name"] = [propDescr, self.name]
      propDescr = QadMsg.translate("Dimension", "Description")
      proplist["description"] = [propDescr, self.description]
      propDescr = QadMsg.translate("Dimension", "File path")
      proplist["path"] = [propDescr, self.path]
      
      # testo di quota
      value = self.textPrefix
      if len(self.textPrefix) > 0:
         value += "<>"
      value += self.textSuffix
      propDescr = QadMsg.translate("Dimension", "Text prefix and suffix")
      proplist["textPrefix"] = [propDescr, value]
      propDescr = QadMsg.translate("Dimension", "Leading zero suppression")
      proplist["textSuppressLeadingZeros"] = [propDescr, self.textSuppressLeadingZeros]
      propDescr = QadMsg.translate("Dimension", "Trailing zero suppression")
      proplist["textDecimalZerosSuppression"] = [propDescr, self.textDecimalZerosSuppression]
      propDescr = QadMsg.translate("Dimension", "Text height")
      proplist["textHeight"] = [propDescr, self.textHeight]
      propDescr = QadMsg.translate("Dimension", "Vertical text position")
      proplist["textVerticalPos"] = [propDescr, self.textVerticalPos]
      propDescr = QadMsg.translate("Dimension", "Horizontal text position")
      proplist["textHorizontalPos"] = [propDescr, self.textHorizontalPos]
      propDescr = QadMsg.translate("Dimension", "Text offset")
      proplist["textOffsetDist"] = [propDescr, self.textOffsetDist]
      propDescr = QadMsg.translate("Dimension", "Text alignment")
      proplist["textRotMode"] = [propDescr, self.textRotMode]
      propDescr = QadMsg.translate("Dimension", "Fixed text rotation")
      proplist["textForcedRot"] = [propDescr, self.textForcedRot]
      propDescr = QadMsg.translate("Dimension", "Precision")
      proplist["textDecimals"] = [propDescr, self.textDecimals]
      propDescr = QadMsg.translate("Dimension", "Decimal separator")
      proplist["textDecimalSep"] = [propDescr, self.textDecimalSep]
      propDescr = QadMsg.translate("Dimension", "Text font")
      proplist["textFont"] = [propDescr, self.textFont]
      propDescr = QadMsg.translate("Dimension", "Text color")
      proplist["textColor"] = [propDescr, self.textColor]
      if self.textDirection == QadDimStyleTxtDirectionEnum.SX_TO_DX:
         value = QadMsg.translate("Dimension", "From left to right")
      else:
         value = QadMsg.translate("Dimension", "From right to left")
      propDescr = QadMsg.translate("Dimension", "Text direction")
      proplist["textDirection"] = [propDescr, value]
      propDescr = QadMsg.translate("Dimension", "Arc len. symbol")
      proplist["arcSymbPos"] = [propDescr, self.arcSymbPos]
      
      # linee di quota
      propDescr = QadMsg.translate("Dimension", "Dim line 1 visible")
      proplist["dimLine1Show"] = [propDescr, self.dimLine1Show]
      propDescr = QadMsg.translate("Dimension", "Dim line 2 visible")
      proplist["dimLine2Show"] = [propDescr, self.dimLine2Show]
      propDescr = QadMsg.translate("Dimension", "Dim line linetype")
      proplist["dimLineLineType"] = [propDescr, self.dimLineLineType]
      propDescr = QadMsg.translate("Dimension", "Dim line color")
      proplist["dimLineColor"] = [propDescr, self.dimLineColor]
      propDescr = QadMsg.translate("Dimension", "Offset from origin")
      proplist["dimLineSpaceOffset"] = [propDescr, self.dimLineSpaceOffset]
   
      # simboli per linee di quota
      propDescr = QadMsg.translate("Dimension", "Arrow 1")
      proplist["block1Name"] = [propDescr, self.block1Name]
      propDescr = QadMsg.translate("Dimension", "Arrow 2")
      proplist["block2Name"] = [propDescr, self.block2Name]
      propDescr = QadMsg.translate("Dimension", "Leader arrow")
      proplist["blockLeaderName"] = [propDescr, self.blockLeaderName]
      propDescr = QadMsg.translate("Dimension", "Arrowhead width")
      proplist["blockWidth"] = [propDescr, self.blockWidth]
      propDescr = QadMsg.translate("Dimension", "Arrowhead scale")
      proplist["blockScale"] = [propDescr, self.blockScale]
      propDescr = QadMsg.translate("Dimension", "Center mark size")
      proplist["centerMarkSize"] = [propDescr, self.centerMarkSize]
   
      # adattamento del testo e delle frecce
      propDescr = QadMsg.translate("Dimension", "Fit: arrows and text")
      proplist["textBlockAdjust"] = [propDescr, self.textBlockAdjust]
      propDescr = QadMsg.translate("Dimension", "Suppress arrows for lack of space")
      proplist["blockSuppressionForNoSpace"] = [propDescr, self.blockSuppressionForNoSpace]
      
      # linee di estensione
      propDescr = QadMsg.translate("Dimension", "Ext. line 1 visible")
      proplist["extLine1Show"] = [propDescr, self.extLine1Show]
      propDescr = QadMsg.translate("Dimension", "Ext. line 2 visible")
      proplist["extLine2Show"] = [propDescr, self.extLine2Show]
      propDescr = QadMsg.translate("Dimension", "Ext. line 1 linetype")
      proplist["extLine1LineType"] = [propDescr, self.extLine1LineType]
      propDescr = QadMsg.translate("Dimension", "Ext. line 2 linetype")
      proplist["extLine2LineType"] = [propDescr, self.extLine2LineType]
      propDescr = QadMsg.translate("Dimension", "Ext. line color")
      proplist["extLineColor"] = [propDescr, self.extLineColor]
      propDescr = QadMsg.translate("Dimension", "Ext. line extension")
      proplist["extLineOffsetDimLine"] = [propDescr, self.extLineOffsetDimLine]
      propDescr = QadMsg.translate("Dimension", "Ext. line offset")
      proplist["extLineOffsetOrigPoints"] = [propDescr, self.extLineOffsetOrigPoints]
      propDescr = QadMsg.translate("Dimension", "Fixed length ext. line activated")
      proplist["extLineIsFixedLen"] = [propDescr, self.extLineIsFixedLen]
      propDescr = QadMsg.translate("Dimension", "Fixed length ext. line")
      proplist["extLineFixedLen"] = [propDescr, self.extLineFixedLen]
      
      # layer e loro caratteristiche
      propDescr = QadMsg.translate("Dimension", "Layer for dim texts")
      proplist["textualLayerName"] = [propDescr, self.textualLayerName]
      propDescr = QadMsg.translate("Dimension", "Layer for dim lines")
      proplist["linearLayerName"] = [propDescr, self.linearLayerName]
      propDescr = QadMsg.translate("Dimension", "Layer for dim arrows")
      proplist["symbolLayerName"] = [propDescr, self.symbolLayerName]
     
      propDescr = QadMsg.translate("Dimension", "Field for component type")
      proplist["componentFieldName"] = [propDescr, self.componentFieldName]
      propDescr = QadMsg.translate("Dimension", "Field for linetype")
      proplist["lineTypeFieldName"] = [propDescr, self.lineTypeFieldName]
      propDescr = QadMsg.translate("Dimension", "Field for color")
      proplist["colorFieldName"] = [propDescr, self.colorFieldName]
      propDescr = QadMsg.translate("Dimension", "Field for dim ID in texts")
      proplist["idFieldName"] = [propDescr, self.idFieldName]
      propDescr = QadMsg.translate("Dimension", "Field for dim ID in lines and arrows")
      proplist["idParentFieldName"] = [propDescr, self.idParentFieldName]
      propDescr = QadMsg.translate("Dimension", "Field for dim style name")
      proplist["dimStyleFieldName"] = [propDescr, self.dimStyleFieldName]
      propDescr = QadMsg.translate("Dimension", "Field for dim type")
      proplist["dimTypeFieldName"] = [propDescr, self.dimTypeFieldName]
      propDescr = QadMsg.translate("Dimension", "Field for symbol name")
      proplist["symbolFieldName"] = [propDescr, self.symbolFieldName]
      propDescr = QadMsg.translate("Dimension", "Field for arrows scale")
      proplist["scaleFieldName"] = [propDescr, self.scaleFieldName]
      propDescr = QadMsg.translate("Dimension", "Field for arrows rotation")
      proplist["rotFieldName"] = [propDescr, self.rotFieldName]
      
      return proplist


   #============================================================================
   # getLayer
   #============================================================================
   def getLayer(self, layerName):
      if layerName is not None:
         layerList = qad_layer.getLayersByName(qad_utils.wildCard2regularExpr(layerName))
         if len(layerList) == 1:
            return layerList[0]
      return None


   #============================================================================
   # layer testuale
   def getTextualLayer(self):
      if self.__textualLayer is None:
         self.__textualLayer = self.getLayer(self.textualLayerName)
      return self.__textualLayer
         
   def getTextualLayerFields(self):
      if self.__textFields is None:
         self.__textFields = None if self.getTextualLayer() is None else self.getTextualLayer().pendingFields()
      return self.__textFields

   def getTextualFeaturePrototype(self):
      if self.__textualFeaturePrototype is None:
         if self.getTextualLayerFields() is not None:
            self.__textualFeaturePrototype = QgsFeature(self.getTextualLayerFields())                       
            self.initFeatureToDefautlValues(self.getTextualLayer(), self.__textualFeaturePrototype)
      return self.__textualFeaturePrototype


   #============================================================================
   # layer lineare
   def getLinearLayer(self):
      if self.__linearLayer is None:
         self.__linearLayer = self.getLayer(self.linearLayerName)
      return self.__linearLayer
         
   def getLinearLayerFields(self):
      if self.__lineFields is None:
         self.__lineFields = None if self.getLinearLayer() is None else self.getLinearLayer().pendingFields()
      return self.__lineFields

   def getLinearFeaturePrototype(self):
      if self.__linearFeaturePrototype is None:
         if self.getLinearLayerFields() is not None:
            self.__linearFeaturePrototype = QgsFeature(self.getLinearLayerFields())                       
            self.initFeatureToDefautlValues(self.getLinearLayer(), self.__linearFeaturePrototype)
      return self.__linearFeaturePrototype


   #============================================================================
   # layer simbolo
   def getSymbolLayer(self):
      if self.__symbolLayer is None:
         self.__symbolLayer = self.getLayer(self.symbolLayerName)
      return self.__symbolLayer
         
   def getSymbolLayerFields(self):
      if self.__symbolFields is None:
         self.__symbolFields = None if self.getSymbolLayer() is None else self.getSymbolLayer().pendingFields()
      return self.__symbolFields

   def getSymbolFeaturePrototype(self):
      if self.__symbolFeaturePrototype is None:
         if self.getSymbolLayerFields() is not None:
            self.__symbolFeaturePrototype = QgsFeature(self.getSymbolLayerFields())                       
            self.initFeatureToDefautlValues(self.getSymbolLayer(), self.__symbolFeaturePrototype)
      return self.__symbolFeaturePrototype
      
      
   #============================================================================
   # initFeatureToDefautlValues
   #============================================================================
   def initFeatureToDefautlValues(self, layer, f):
      # assegno i valori di default
      provider = layer.dataProvider()
      fields = f.fields()
      for field in fields.toList():
         i = fields.indexFromName(field.name())
         f[field.name()] = provider.defaultValue(i)
               
   
   #============================================================================
   # save
   #============================================================================
   def save(self, path = "", overwrite = True):
      """
      Salva le impostazioni dello stile di quotatura in un file.
      """
      if path == "" and self.path != "":
         _path = self.path
      else:         
         dir, base = os.path.split(path)
         if dir == "":
            dir = QDir.cleanPath(QgsApplication.qgisSettingsDirPath() + "python/plugins/qad") + "/"
         else:
            dir = QDir.cleanPath(dir) + "/"
         
         name, ext = os.path.splitext(base)
         if name == "":
            name = self.name
         
         if ext == "": # se non c'è estensione la aggiungo
            ext = ".dim"
         
         _path = dir + name + ext
      
      if overwrite == False: # se non si vuole sovrascrivere
         if os.path.exists(_path):
            return False
      
      dir = QFileInfo(_path).absoluteDir() 
      if not dir.exists():
         os.makedirs(dir.absolutePath())

      config = qad_utils.QadRawConfigParser(allow_no_value=True)
      config.add_section("dimension_options")
      config.set("dimension_options", "name", str(self.name))
      config.set("dimension_options", "description", self.description)
      config.set("dimension_options", "dimType", str(self.dimType))
                           
      # testo di quota
      config.set("dimension_options", "textPrefix", str(self.textPrefix))
      config.set("dimension_options", "textSuffix", str(self.textSuffix))
      config.set("dimension_options", "textSuppressLeadingZeros", str(self.textSuppressLeadingZeros))
      config.set("dimension_options", "textDecimalZerosSuppression", str(self.textDecimalZerosSuppression))
      config.set("dimension_options", "textHeight", str(self.textHeight))
      config.set("dimension_options", "textVerticalPos", str(self.textVerticalPos))
      config.set("dimension_options", "textHorizontalPos", str(self.textHorizontalPos))
      config.set("dimension_options", "textOffsetDist", str(self.textOffsetDist))
      config.set("dimension_options", "textRotMode", str(self.textRotMode))
      config.set("dimension_options", "textForcedRot", str(self.textForcedRot))
      config.set("dimension_options", "textDecimals", str(self.textDecimals))
      config.set("dimension_options", "textDecimalSep", str(self.textDecimalSep))
      config.set("dimension_options", "textFont", str(self.textFont))
      config.set("dimension_options", "textColor", str(self.textColor))
      config.set("dimension_options", "textDirection", str(self.textDirection))
      config.set("dimension_options", "arcSymbPos", str(self.arcSymbPos))

      # linee di quota
      config.set("dimension_options", "dimLine1Show", str(self.dimLine1Show))
      config.set("dimension_options", "dimLine2Show", str(self.dimLine2Show))
      config.set("dimension_options", "dimLineLineType", str(self.dimLineLineType))
      config.set("dimension_options", "dimLineColor", str(self.dimLineColor))
      config.set("dimension_options", "dimLineSpaceOffset", str(self.dimLineSpaceOffset))
          
      # simboli per linee di quota
      config.set("dimension_options", "block1Name", str(self.block1Name))
      config.set("dimension_options", "block2Name", str(self.block2Name))
      config.set("dimension_options", "blockLeaderName", str(self.blockLeaderName))
      config.set("dimension_options", "blockWidth", str(self.blockWidth))
      config.set("dimension_options", "blockScale", str(self.blockScale))
      config.set("dimension_options", "blockSuppressionForNoSpace", str(self.blockSuppressionForNoSpace))
      config.set("dimension_options", "centerMarkSize", str(self.centerMarkSize))

      # adattamento del testo e delle frecce
      config.set("dimension_options", "textBlockAdjust", str(self.textBlockAdjust))

      # linee di estensione
      config.set("dimension_options", "extLine1Show", str(self.extLine1Show))
      config.set("dimension_options", "extLine2Show", str(self.extLine2Show))
      config.set("dimension_options", "extLine1LineType", str(self.extLine1LineType))
      config.set("dimension_options", "extLine2LineType", str(self.extLine2LineType))
      config.set("dimension_options", "extLineColor", str(self.extLineColor))
      config.set("dimension_options", "extLineOffsetDimLine", str(self.extLineOffsetDimLine))
      config.set("dimension_options", "extLineOffsetOrigPoints", str(self.extLineOffsetOrigPoints))
      config.set("dimension_options", "extLineIsFixedLen", str(self.extLineIsFixedLen))
      config.set("dimension_options", "extLineFixedLen", str(self.extLineFixedLen))

      # layer e loro caratteristiche
      config.set("dimension_options", "textualLayerName", "" if self.textualLayerName is None else self.textualLayerName)
      config.set("dimension_options", "linearLayerName", "" if self.linearLayerName is None else self.linearLayerName)
      config.set("dimension_options", "symbolLayerName", "" if self.symbolLayerName is None else self.symbolLayerName)
      config.set("dimension_options", "componentFieldName", str(self.componentFieldName))
      config.set("dimension_options", "symbolFieldName", str(self.symbolFieldName))
      config.set("dimension_options", "lineTypeFieldName", str(self.lineTypeFieldName))
      config.set("dimension_options", "colorFieldName", str(self.colorFieldName))
      config.set("dimension_options", "idFieldName", str(self.idFieldName))
      config.set("dimension_options", "idParentFieldName", str(self.idParentFieldName))
      config.set("dimension_options", "dimStyleFieldName", str(self.dimStyleFieldName))
      config.set("dimension_options", "dimTypeFieldName", str(self.dimTypeFieldName))
      config.set("dimension_options", "scaleFieldName", str(self.scaleFieldName))
      config.set("dimension_options", "rotFieldName", str(self.rotFieldName))

      with codecs.open(_path, 'w', 'utf-8') as configFile: 
          config.write(configFile)
          
      self.path = _path
      
      return True


   #============================================================================
   # getDefaultDimFilePath
   #============================================================================
   def getDefaultDimFilePath(self, fileName):
      # ottiene il percorso automatico dove salvare/caricare il file della quotatura
      # se esiste un progetto caricato il percorso è quello del progetto
      prjFileInfo = QFileInfo(QgsProject.instance().fileName())
      path = prjFileInfo.absolutePath()
      if len(path) == 0:
         # se non esiste un progetto caricato uso il percorso di installazione di qad
         path = QDir.cleanPath(QgsApplication.qgisSettingsDirPath() + "python/plugins/qad")
      return path + "/" + fileName

   
   #============================================================================
   # load
   #============================================================================
   def load(self, path):
      """
      Carica le impostazioni dello stile di quotatura da un file.
      """
      if path is None or path == "":
         return False
      
      if os.path.dirname(path) == "": # path contiene solo il nome del file (senza dir)
         _path = self.getDefaultDimFilePath(path)
      else:
         _path = path
         
      if not os.path.exists(_path):
         return False

      config = qad_utils.QadRawConfigParser(allow_no_value=True)
      config.readfp(codecs.open(_path, "r", "utf-8"))
      #config.read(_path)

      self.name = config.get("dimension_options", "name")
      self.description = config.get("dimension_options", "description")
      self.dimType = config.get("dimension_options", "dimType")
                           
      # testo di quota
      self.textPrefix = config.get("dimension_options", "textPrefix")
      self.textSuffix = config.get("dimension_options", "textSuffix")
      self.textSuppressLeadingZeros = config.getboolean("dimension_options", "textSuppressLeadingZeros")
      self.textDecimalZerosSuppression = config.getboolean("dimension_options", "textDecimalZerosSuppression")
      self.textHeight = config.getfloat("dimension_options", "textHeight")
      self.textVerticalPos = config.getint("dimension_options", "textVerticalPos")
      self.textHorizontalPos = config.getint("dimension_options", "textHorizontalPos")
      self.textOffsetDist = config.getfloat("dimension_options", "textOffsetDist")
      self.textRotMode = config.getint("dimension_options", "textRotMode")
      self.textForcedRot = config.getfloat("dimension_options", "textForcedRot")
      self.textDecimals = config.getint("dimension_options", "textDecimals")
      self.textDecimalSep = config.get("dimension_options", "textDecimalSep")
      self.textFont = config.get("dimension_options", "textFont")
      self.textColor = config.get("dimension_options", "textColor")
      self.textDirection = config.getint("dimension_options", "textDirection")
      self.arcSymbPos = config.getint("dimension_options", "arcSymbPos")

      # linee di quota
      self.dimLine1Show = config.getboolean("dimension_options", "dimLine1Show")
      self.dimLine2Show = config.getboolean("dimension_options", "dimLine2Show")
      self.dimLineLineType = config.get("dimension_options", "dimLineLineType")
      self.dimLineColor = config.get("dimension_options", "dimLineColor")
      self.dimLineSpaceOffset = config.getfloat("dimension_options", "dimLineSpaceOffset")
          
      # simboli per linee di quota
      self.block1Name = config.get("dimension_options", "block1Name")
      self.block2Name = config.get("dimension_options", "block2Name")
      self.blockLeaderName = config.get("dimension_options", "blockLeaderName")
      self.blockWidth = config.getfloat("dimension_options", "blockWidth")
      self.blockScale = config.getfloat("dimension_options", "blockScale")
      self.blockSuppressionForNoSpace = config.getboolean("dimension_options", "blockSuppressionForNoSpace")
      self.centerMarkSize = config.getfloat("dimension_options", "centerMarkSize")

      # adattamento del testo e delle frecce
      self.textBlockAdjust = config.getint("dimension_options", "textBlockAdjust")

      # linee di estensione
      self.extLine1Show = config.getboolean("dimension_options", "extLine1Show")
      self.extLine2Show = config.getboolean("dimension_options", "extLine2Show")
      self.extLine1LineType = config.get("dimension_options", "extLine1LineType")
      self.extLine2LineType = config.get("dimension_options", "extLine2LineType")
      self.extLineColor = config.get("dimension_options", "extLineColor")
      self.extLineOffsetDimLine = config.getfloat("dimension_options", "extLineOffsetDimLine")
      self.extLineOffsetOrigPoints = config.getfloat("dimension_options", "extLineOffsetOrigPoints")
      self.extLineIsFixedLen = config.getboolean("dimension_options", "extLineIsFixedLen")
      self.extLineFixedLen = config.getfloat("dimension_options", "extLineFixedLen")

      # layer e loro caratteristiche
      self.textualLayerName = config.get("dimension_options", "textualLayerName")
      self.linearLayerName = config.get("dimension_options", "linearLayerName")
      self.symbolLayerName = config.get("dimension_options", "symbolLayerName")
            
      self.componentFieldName = config.get("dimension_options", "componentFieldName")
      self.symbolFieldName = config.get("dimension_options", "symbolFieldName")
      self.lineTypeFieldName = config.get("dimension_options", "lineTypeFieldName")
      self.colorFieldName = config.get("dimension_options", "colorFieldName")
      self.idFieldName = config.get("dimension_options", "idFieldName")
      self.idParentFieldName = config.get("dimension_options", "idParentFieldName")
      self.dimStyleFieldName = config.get("dimension_options", "dimStyleFieldName")
      self.dimTypeFieldName = config.get("dimension_options", "dimTypeFieldName")
      self.scaleFieldName = config.get("dimension_options", "scaleFieldName")
      self.rotFieldName = config.get("dimension_options", "rotFieldName")
      
      self.path = _path
      
      return True


   #============================================================================
   # remove
   #============================================================================
   def remove(self):
      """
      Cancella il file delle impostazioni dello stile di quotatura.
      """
      currDimStyleName = QadVariables.get(QadMsg.translate("Environment variables", "DIMSTYLE"))
      if self.name == currDimStyleName: # lo stile da cancellare è quello corrente
         return False
      
      if self.path is not None and self.path != "":
         if os.path.exists(self.path):
            try:
               os.remove(self.path)
            except:
               return False
            
      return True

   #============================================================================
   # rename
   #============================================================================
   def rename(self, newName):
      """
      Rinomina il nome dello stile e del file delle impostazioni dello stile di quotatura.
      """
      if newName == self.name: # nome uguale
         return True
      oldName = self.name
      
      if self.path is not None or self.path != "":
         if os.path.exists(self.path):
            try:
               dir, base = os.path.split(self.path)
               dir = QDir.cleanPath(dir) + "/"
               
               name, ext = os.path.splitext(base)
               newPath = dir + "/" + newName + ext
               
               os.rename(self.path, newPath)
               self.path = newPath
               self.name = newName
               self.save()
            except:
               return False
      else:
         self.name = newName

      currDimStyleName = QadVariables.get(QadMsg.translate("Environment variables", "DIMSTYLE"))
      if oldName == currDimStyleName: # lo stile da rinominare è quello corrente
         QadVariables.set(QadMsg.translate("Environment variables", "DIMSTYLE"), newName)

      self.name = newName
      return True


   #============================================================================
   # getInValidErrMsg
   #============================================================================
   def getInValidErrMsg(self):
      """
      Verifica se lo stile di quotatura é invalido e in caso affermativo ritorna il messaggio di errore.
      Se la quotatura é valida ritorna None.
      """
      prefix = QadMsg.translate("Dimension", "\nThe dimension style \"{0}\" ").format(self.name)
      
      if self.getTextualLayer() is None:
         return prefix + QadMsg.translate("Dimension", "has not the textual layer for dimension.\n")
      if qad_layer.isTextLayer(self.getTextualLayer()) == False:
         errMsg = prefix + QadMsg.translate("Dimension", "has the textual layer for dimension which is not a textual layer.")         
         errMsg = errMsg + QadMsg.translate("QAD", "\nA textual layer is a vectorial punctual layer having a label and the symbol transparency no more than 10%.\n")
         return errMsg

      if self.getSymbolLayer() is None:
         return prefix + QadMsg.translate("Dimension", "has not the symbol layer for dimension.\n")
      if qad_layer.isSymbolLayer(self.getSymbolLayer()) == False:
         errMsg = prefix + QadMsg.translate("Dimension", "has the symbol layer for dimension which is not a symbol layer.")         
         errMsg = errMsg + QadMsg.translate("QAD", "\nA symbol layer is a vectorial punctual layer without label.\n")
         return errMsg

      if self.getLinearLayer() is None:
         return prefix + QadMsg.translate("Dimension", "has not the linear layer for dimension.\n")
      # deve essere un VectorLayer di tipo linea
      if (self.getLinearLayer().type() != QgsMapLayer.VectorLayer) or (self.getLinearLayer().geometryType() != QGis.Line):
         errMsg = prefix + QadMsg.translate("Dimension", "has the linear layer for dimension which is not a linear layer.")         
         return errMsg
      # i layer devono avere lo stesso sistema di coordinate
      if not (self.getTextualLayer().crs() == self.getLinearLayer().crs() and self.getLinearLayer().crs() == self.getSymbolLayer().crs()):
         errMsg = prefix + QadMsg.translate("Dimension", "has not the layers with the same coordinate reference system.")         
         return errMsg
         
      return None
   
   
   #===============================================================================
   # getNotGraphEditableErrMsg
   #===============================================================================
   def getNotGraphEditableErrMsg(self):
      """
      Verifica se i layer dello stile di quotatura sono in sola lettura e in caso affermativo ritorna il messaggio di errore.
      Se i layer dello stile di quotatura sono modificabili ritorna None.
      """
      prefix = QadMsg.translate("Dimension", "\nThe dimension style \"{0}\" ").format(self.name)
      
      provider = self.getTextualLayer().dataProvider()
      if not (provider.capabilities() & QgsVectorDataProvider.EditingCapabilities):
         return prefix + QadMsg.translate("Dimension", "has the textual layer not editable.\n")
      if not self.getTextualLayer().isEditable():
         return prefix + QadMsg.translate("Dimension", "has the textual layer not editable.\n")

      provider = self.getSymbolLayer().dataProvider()
      if not (provider.capabilities() & QgsVectorDataProvider.EditingCapabilities):
         return prefix + QadMsg.translate("Dimension", "has the symbol layer not editable.\n")
      if not self.getSymbolLayer().isEditable():
         return prefix + QadMsg.translate("Dimension", "has the symbol layer not editable.\n")
      
      provider = self.getLinearLayer().dataProvider()
      if not (provider.capabilities() & QgsVectorDataProvider.EditingCapabilities):
         return prefix + QadMsg.translate("Dimension", "has the linear layer not editable.\n")
      if not self.getLinearLayer().isEditable():
         return prefix + QadMsg.translate("Dimension", "has the linear layer not editable.\n")
      
      return None
   
    
   #============================================================================
   # adjustLineAccordingTextRect
   #============================================================================
   def adjustLineAccordingTextRect(self, textRect, pt1, pt2, textLinearDimComponentOn):
      """
      Data una linea (pt1-pt2), che tipo di componente di quota rappresenta (textLinearDimComponentOn)
      e un rettangolo che rappresenta l'occupazione del testo di quota, la funzione restituisce
      due linee (possono essere None) in modo che il testo non si sovrapponga alla linea e che le 
      impostazioni di quota siano rispettate (dimLine1Show, dimLine2Show, extLine1Show, extLine2Show)
      """   
      line1 = None
      line2 = None               
      intPts = self.getIntersectionPtsBetweenTextRectAndLine(textRect, pt1, pt2)
      if textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1: # linea di quota ("Dimension line")
         if len(intPts) == 2: # il rettangolo é sulla linea
            if self.dimLine1Show:
               line1 = [pt1, intPts[0]]
            if self.dimLine2Show:
               line2 = [intPts[1], pt2]
         else: # il rettangolo non é sulla linea            
            if self.dimLine1Show and self.dimLine2Show:
               line1 = [pt1, pt2]
            else:
               space1, space2 = self.getSpaceForBlock1AndBlock2(textRect, pt1, pt2)
               rot = qad_utils.getAngleBy2Pts(pt1, pt2) # angolo della linea di quota
               intPt1 = qad_utils.getPolarPointByPtAngle(pt1, rot, space1)   
               intPt2 = qad_utils.getPolarPointByPtAngle(pt2, rot - math.pi, space2)

               if self.dimLine1Show:
                  line1 = [pt1, intPt2]
               elif self.dimLine2Show:
                  line2 = [pt2, intPt1]
      elif textLinearDimComponentOn == QadDimComponentEnum.EXT_LINE1: # prima linea di estensione ("Extension line 1")
         if self.extLine1Show:
            if len(intPts) > 0:
               line1 = [pt1, intPts[0]]
            else:
               line1 = [pt1, pt2]
      elif textLinearDimComponentOn == QadDimComponentEnum.EXT_LINE2: # seconda linea di estensione ("Extension line 2")
         if self.extLine2Show:
            if len(intPts) > 0:
               line1 = [pt1, intPts[0]]
            else:
               line1 = [pt1, pt2]
      elif textLinearDimComponentOn == QadDimComponentEnum.LEADER_LINE: # linea porta quota usata quando il testo é fuori dalla quota ("Leader")
         if len(intPts) > 0:
            line1 = [pt1, intPts[0]]
         else:
            line1 = [pt1, pt2]

      return line1, line2

   
   #============================================================================
   # setDimId
   #============================================================================
   def setDimId(self, dimId, features, parentId = False):
      """
      Setta tutte le feature passate nella lista <features> con il codice della quota.
      """
      fieldName = self.idParentFieldName if parentId else self.idFieldName
         
      if len(fieldName) == 0:
         return True

      i = 0
      tot = len(features)
      while i < tot:
         try:
            f = features[i]
            if f is not None:
               # imposto il codice della quota
               f.setAttribute(fieldName, dimId)
         except:
            return False
         i = i + 1
      return True        


   #============================================================================
   # recodeDimIdOnFeatures
   #============================================================================
   def recodeDimIdOnFeatures(self, oldDimId, newDimId, features, parentId = False):
      """
      Cerca tutte le feature passate nella lista <features> con il codice della 
      quota oldDimId e le ricodifica con newDimId.
      """
      fieldName = self.idParentFieldName if parentId else self.idFieldName
         
      if len(fieldName) == 0:
         return True
      
      i = 0
      tot = len(features)
      while i < tot:
         try:
            f = features[i]
            if f is not None:
               if f.attribute(fieldName) == oldDimId:
                  # imposto il codice della quota
                  f.setAttribute(fieldName, newDimId)
         except:
            return False
         i = i + 1
      return True        


   def textCommitChangesOnSave(self):
      """
      Salva i testi delle quote per ottenere i nuovi ID 
      e richiamare updateTextReferencesOnSave tramite il segnale committedFeaturesAdded.
      """
      # salvo i testi per avere la codifica definitiva
      if self.getTextualLayer() is not None:
         return self.getTextualLayer().commitChanges()
      else:
         return False


   #============================================================================
   # updateTextReferencesOnSave
   #============================================================================
   def updateTextReferencesOnSave(self, plugIn, textAddedFeatures):
      """
      Aggiorna e salva i reference delle features dello stile di quotatura contenuti in textAddedFeatures.
      """
      if self.startEditing() == False:
         return False     
      
      plugIn.beginEditCommand("Dimension recoded", [self.getSymbolLayer(), self.getLinearLayer(), self.getTextualLayer()])
      
      entity = QadEntity()
      for f in textAddedFeatures:
         entity.set(self.getTextualLayer(), f.id())
         oldDimId = entity.getAttribute(self.idFieldName)
         newDimId = f.id()        
         if oldDimId is None or self.recodeDimId(plugIn, oldDimId, newDimId) == False:
            return False

      plugIn.endEditCommand()
     
      return True


   #============================================================================
   # startEditing
   #============================================================================
   def startEditing(self):
      if self.getTextualLayer() is not None and self.getTextualLayer().isEditable() == False:
         if self.getTextualLayer().startEditing() == False:
            return False     
      if self.getLinearLayer() is not None and self.getLinearLayer().isEditable() == False:
         if self.getLinearLayer().startEditing() == False:
            return False         
      if self.getSymbolLayer() is not None and self.getSymbolLayer().isEditable() == False:
         if self.getSymbolLayer().startEditing() == False:
            return False         


   #============================================================================
   # commitChanges
   #============================================================================
   def commitChanges(self, excludedLayer):
      if self.startEditing() == False:
         return False     
      
      if (excludedLayer is None) or excludedLayer.id() != self.getTextualLayer().id():
         # salvo le entità testuali
         self.getTextualLayer().commitChanges()
      if (excludedLayer is None) or excludedLayer.id() != self.getLinearLayer().id():
         # salvo le entità lineari
         self.getLinearLayer().commitChanges()
      if (excludedLayer is None) or excludedLayer.id() != self.getSymbolLayer().id():
         # salvo le entità puntuali
         self.getSymbolLayer().commitChanges()
   

   #============================================================================
   # recodeDimId
   #============================================================================
   def getEntitySet(self, dimId):
      """
      Ricava un QadEntitySet con tutte le feature della quota dimId.
      """
      result = QadEntitySet()
      if len(self.idFieldName) == 0 or len(self.idParentFieldName) == 0:
         return result
      
      layerEntitySet = QadLayerEntitySet()
      
      # ricerco l'entità testo
      expression = "\"" + self.idFieldName + "\"=" + str(dimId)
      featureIter = self.getTextualLayer().getFeatures(QgsFeatureRequest().setFilterExpression(expression))
      layerEntitySet.set(self.getTextualLayer())
      layerEntitySet.addFeatures(featureIter)
      result.addLayerEntitySet(layerEntitySet)

      expression = "\"" + self.idParentFieldName + "\"=" + str(dimId)   

      # ricerco le entità linea
      layerEntitySet.clear()
      featureIter = self.getLinearLayer().getFeatures(QgsFeatureRequest().setFilterExpression(expression))
      layerEntitySet.set(self.getLinearLayer())
      layerEntitySet.addFeatures(featureIter)
      result.addLayerEntitySet(layerEntitySet)

      # ricerco e setto id_parent per le entità puntuali
      layerEntitySet.clear()
      featureIter = self.getSymbolLayer().getFeatures(QgsFeatureRequest().setFilterExpression(expression))      
      layerEntitySet.set(self.getSymbolLayer())
      layerEntitySet.addFeatures(featureIter)
      result.addLayerEntitySet(layerEntitySet)

      return result
   
   
   #============================================================================
   # recodeDimId
   #============================================================================
   def recodeDimId(self, plugIn, oldDimId, newDimId):
      """
      Ricodifica tutte le feature della quota oldDimId con il nuovo codice newDimId.
      """
      if len(self.idFieldName) == 0 or len(self.idParentFieldName) == 0:
         return True
      
      entitySet = self.getEntitySet(oldDimId)

      # setto l'entità testo
      layerEntitySet = entitySet.findLayerEntitySet(self.getTextualLayer())
      if layerEntitySet is not None:
         features = layerEntitySet.getFeatureCollection()
         if self.setDimId(newDimId, features, False) == False:
            return False
         # plugIn, layer, features, refresh, check_validity
         if qad_layer.updateFeaturesToLayer(plugIn, self.getTextualLayer(), features, False, False) == False:
            return False
      
      # setto id_parent per le entità linea
      layerEntitySet = entitySet.findLayerEntitySet(self.getLinearLayer())
      if layerEntitySet is not None:
         features = layerEntitySet.getFeatureCollection()
         if self.setDimId(newDimId, features, True) == False:
            return False
         # plugIn, layer, features, refresh, check_validity
         if qad_layer.updateFeaturesToLayer(plugIn, self.getLinearLayer(), features, False, False) == False:
            return False
      
      # setto id_parent per le entità puntuali
      layerEntitySet = entitySet.findLayerEntitySet(self.getSymbolLayer())
      if layerEntitySet is not None:
         features = layerEntitySet.getFeatureCollection()
         if self.setDimId(newDimId, features, True) == False:
            return False
         # plugIn, layer, features, refresh, check_validity
         if qad_layer.updateFeaturesToLayer(plugIn, self.getSymbolLayer(), features, False, False) == False:
            return False

      return True


   #============================================================================
   # getDimIdByEntity
   #============================================================================
   def getDimIdByEntity(self, entity):
      """
      La funzione, data un'entità, verifica se fa parte dello stile di quotatura e,
      in caso di successo, restituisce il codice della quotatura altrimenti None.
      In più, la funzione, setta il tipo di quotatura se é possibile.
      """
      if entity.layer.name() == self.textualLayerName:
         dimId = entity.getAttribute(self.idFieldName)
         if dimId is None:
            return None
         f = entity.getFeature()
      elif entity.layer.name() == self.linearLayerName or \
           entity.layer.name() == self.symbolLayerName:
         dimId = entity.getAttribute(self.idParentFieldName)
         if dimId is None:
            return None
         # ricerco l'entità testo
         expression = "\"" + self.idFieldName + "\"=" + str(dimId)
         f = QgsFeature()
         if self.getTextualLayer().getFeatures(QgsFeatureRequest().setFilterExpression(expression)).nextFeature(f) == False:
            return None
      else:
         return None

      try:
         # leggo il nome dello stile di quotatura
         dimName = f.attribute(self.dimStyleFieldName)
         if dimName != self.name:
            return None      
      except:
         return None
      
      try:
         # leggo il tipo dello stile di quotatura
         self.dimType = f.attribute(self.dimTypeFieldName)         
      except:
         pass
      
      return dimId
         

   #============================================================================
   # isDimLayer
   #============================================================================
   def isDimLayer(self, layer):
      """
      La funzione, dato un layer, verifica se fa parte dello stile di quotatura.
      """
      if layer.name() == self.textualLayerName or \
         layer.name() == self.linearLayerName or \
         layer.name() == self.symbolLayerName:
         return True
      else:
         return False


   #============================================================================
   # getFilteredFeatureCollection
   #============================================================================
   def getFilteredFeatureCollection(self, layerEntitySet):
      """
      La funzione, dato un QadLayerEntitySet, filtra e restituisce solo quelle appartenenti allo stile di quotatura.
      """
      result = []
      entity = QadEntity()
      for f in layerEntitySet.getFeatureCollection():
         entity.set(layerEntitySet.layer, f.id())
         if self.getDimIdByEntity(entity) is not None:
            result.append(f)
      
      return result


   #============================================================================
   # FUNZIONI PER I BLOCCHI - INIZIO
   #============================================================================

   
   #============================================================================
   # getBlock1Size
   #============================================================================
   def getBlock1Size(self):
      """
      Restituisce la dimensione del blocco 1 delle frecce in unità di mappa.
      """
      return 0 if self.block1Name == "" else self.blockWidth * self.blockScale


   #============================================================================
   # getBlock2Size
   #============================================================================
   def getBlock2Size(self):
      """
      Restituisce la dimensione del blocco 2 delle frecce in unità di mappa.
      """
      # blockWidth = larghezza del simbolo (in orizzontale) quando la dimensione in unità di mappa = 1 (vedi "triangle2")
      # blockScale = scala della dimensione del simbolo (DIMASZ)
      return 0 if self.block2Name == "" else self.blockWidth * self.blockScale
             
             
   #============================================================================
   # getBlocksRot
   #============================================================================
   def getBlocksRot(self, dimLinePt1, dimLinePt2, inside):
      """
      Restituisce una lista di 2 elementi che descrivono le rotazioni dei due blocchi:
      - il primo elemento é la rotazione del blocco 1
      - il secondo elemento é la rotazione del blocco 2
      
      dimLinePt1 = primo punto della linea di quota (QgsPoint)
      dimLinePt2 = secondo punto della linea di quota (QgsPoint)
      inside = flag di modo, se = true le frecce sono interne altrimenti sono esterne
      """
      rot = qad_utils.getAngleBy2Pts(dimLinePt1, dimLinePt2) # angolo della linea di quota
      if inside:
         rot1 = rot + math.pi
         rot2 = rot
      else:
         rot1 = rot
         rot2 = rot + math.pi
         
      return qad_utils.normalizeAngle(rot1), qad_utils.normalizeAngle(rot2)


   #============================================================================
   # getSpaceForBlock1AndBlock2
   #============================================================================
   def getSpaceForBlock1AndBlock2Auxiliary(self, dimLinePt1, dimLinePt2, rectCorner):
      # calcolo la proiezione di un vertice del rettangolo sulla linea dimLinePt1, dimLinePt2
      perpPt = qad_utils.getPerpendicularPointOnInfinityLine(dimLinePt1, dimLinePt2, rectCorner)
      # se la proienzione non é nel segmento
      if qad_utils.isPtOnSegment(dimLinePt1, dimLinePt2, perpPt) == False:
         # se la proiezione ricade oltre il punto dimLinePt1
         if qad_utils.getDistance(dimLinePt1, perpPt) < qad_utils.getDistance(dimLinePt2, perpPt):
            return 0, qad_utils.getDistance(dimLinePt1, dimLinePt2)        
         else: # se la proiezione ricade oltre il punto dimLinePt2
            return qad_utils.getDistance(dimLinePt1, dimLinePt2), 0
      else:
         return qad_utils.getDistance(dimLinePt1, perpPt), qad_utils.getDistance(dimLinePt2, perpPt)
      
   def getSpaceForBlock1AndBlock2(self, txtRect, dimLinePt1, dimLinePt2):
      """
      txtRect = rettangolo di occupazione del testo o None se non c'é il testo
      dimLinePt1 = primo punto della linea di quotatura
      dimLinePt2 = primo punto della linea di quotatura
      Restituisce lo spazio disponibile per i blocchi 1 e 2 considerando il rettangolo (QadLinearObjectList) che rappresenta il testo
      e la linea di quota dimLinePt1-dimLinePt2.
      """
      if txtRect is None: # se non c'é il testo (é stato spostato fuori dalla linea di quota)
         spaceForBlock1 = qad_utils.getDistance(dimLinePt1, dimLinePt2) / 2
         spaceForBlock2 = spaceForBlock1
      else:
         # calcolo la proiezione dei quattro vertici del rettangolo sulla linea dimLinePt1, dimLinePt2
         linearObject = txtRect.getLinearObjectAt(0)
         partial1SpaceForBlock1, partial1SpaceForBlock2 = self.getSpaceForBlock1AndBlock2Auxiliary(dimLinePt1, dimLinePt2, \
                                                                                                   linearObject.getStartPt())
         linearObject = txtRect.getLinearObjectAt(1)
         partial2SpaceForBlock1, partial2SpaceForBlock2 = self.getSpaceForBlock1AndBlock2Auxiliary(dimLinePt1, dimLinePt2, \
                                                                                                   linearObject.getStartPt())
         spaceForBlock1 = partial1SpaceForBlock1 if partial1SpaceForBlock1 < partial2SpaceForBlock1 else partial2SpaceForBlock1
         spaceForBlock2 = partial1SpaceForBlock2 if partial1SpaceForBlock2 < partial2SpaceForBlock2 else partial2SpaceForBlock2
          
         linearObject = txtRect.getLinearObjectAt(2)
         partial3SpaceForBlock1, partial3SpaceForBlock2 = self.getSpaceForBlock1AndBlock2Auxiliary(dimLinePt1, dimLinePt2, \
                                                                                                   linearObject.getStartPt())
         if partial3SpaceForBlock1 < spaceForBlock1:
            spaceForBlock1 = partial3SpaceForBlock1
         if partial3SpaceForBlock2 < spaceForBlock2:
            spaceForBlock2 = partial3SpaceForBlock2
         
         linearObject = txtRect.getLinearObjectAt(3)
         partial4SpaceForBlock1, partial4SpaceForBlock2 = self.getSpaceForBlock1AndBlock2Auxiliary(dimLinePt1, dimLinePt2, \
                                                                                                   linearObject.getStartPt())
         if partial4SpaceForBlock1 < spaceForBlock1:
            spaceForBlock1 = partial4SpaceForBlock1
         if partial4SpaceForBlock2 < spaceForBlock2:
            spaceForBlock2 = partial4SpaceForBlock2

      return spaceForBlock1, spaceForBlock2


   #============================================================================
   # getSymbolFeature
   #============================================================================
   def getSymbolFeature(self, insPt, rot, isBlock1, textLinearDimComponentOn, sourceCrs = None):
      """
      Restituisce la feature per il simbolo delle frecce.
      insPt = punto di inserimento
      rot = rotazione espressa in radianti
      isBlock1 = se True si tratta del blocco1 altrimenti del blocco2
      textLinearDimComponentOn = indica il componente della quota dove é situato il testo di quota (QadDimComponentEnum)
      sourceCrs = sistema di coordinate di insPt
      """            
      # se non c'é il simbolo di quota
      if insPt is None or rot is None:
         return None     
      # se si tratta del simbolo 1
      if isBlock1 == True:
         # se non deve essere mostrata la linea 1 di quota (vale solo se il testo é sulla linea di quota)
         if self.dimLine1Show == False and \
           (textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1 or textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE2):
            return None
      else: # se si tratta del simbolo 2
         # se non deve essere mostrata la linea 2 di quota (vale solo se il testo é sulla linea di quota)
         if self.dimLine2Show == False and \
           (textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1 or textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE2):
            return None
      
      f = QgsFeature(self.getSymbolFeaturePrototype())
      g = QgsGeometry.fromPoint(insPt)
       
      if (sourceCrs is not None) and sourceCrs != self.getSymbolLayer().crs():
         coordTransform = QgsCoordinateTransform(sourceCrs, self.getSymbolLayer().crs()) # trasformo la geometria
         g.transform(coordTransform)                        

      f.setGeometry(g)

      # imposto la scala del blocco
      try:
         if len(self.scaleFieldName) > 0:
            f.setAttribute(self.scaleFieldName, self.blockScale)
      except:
         pass

      # imposto la rotazione
      try:
         if len(self.rotFieldName) > 0:
            f.setAttribute(self.rotFieldName, qad_utils.toDegrees(rot)) # Converte da radianti a gradi
      except:
         pass

      # imposto il colore
      try:
         if len(self.colorFieldName) > 0:
            f.setAttribute(self.colorFieldName, self.dimLineColor)         
      except:
         pass
             
      # imposto il tipo di componente della quotatura
      if self.dimType == QadDimTypeEnum.RADIUS: # se quotatura tipo raggio
         try:
            if len(self.componentFieldName) > 0:
               f.setAttribute(self.componentFieldName, QadDimComponentEnum.LEADER_BLOCK)
         except:
            pass
         
         try:
            if len(self.symbolFieldName) > 0:
               f.setAttribute(self.symbolFieldName, self.blockLeaderName)
         except:
            pass            
      else:
         try:
            if len(self.componentFieldName) > 0:
               f.setAttribute(self.componentFieldName, QadDimComponentEnum.BLOCK1 if isBlock1 else QadDimComponentEnum.BLOCK2)
         except:
            pass            

         try:
            if len(self.symbolFieldName) > 0:
               f.setAttribute(self.symbolFieldName, self.block1Name if isBlock1 else self.block2Name)
         except:
            pass

      return f


   #============================================================================
   # getDimPointFeature
   #============================================================================
   def getDimPointFeature(self, insPt, isDimPt1, sourceCrs):
      """
      Restituisce la feature per il punto di quotatura.
      insPt = punto di inserimento
      isDimPt1 = se True si tratta del punto di quotatura 1 altrimenti del punto di quotatura 2
      sourceCrs = sistema di coordinate di insPt
      """
      symbolFeaturePrototype = self.getSymbolFeaturePrototype()
      if symbolFeaturePrototype is None:
         return None
      f = QgsFeature(symbolFeaturePrototype)
      g = QgsGeometry.fromPoint(insPt)
           
      if (sourceCrs is not None) and sourceCrs != self.getSymbolLayer().crs():
         coordTransform = QgsCoordinateTransform(sourceCrs, self.getSymbolLayer().crs()) # trasformo la geometria
         g.transform(coordTransform)                        
           
      f.setGeometry(g)
        
      # imposto il tipo di componente della quotatura
      try:
         f.setAttribute(self.componentFieldName, QadDimComponentEnum.DIM_PT1 if isDimPt1 else QadDimComponentEnum.DIM_PT2)
      except:
         pass

      try:
         # imposto il colore
         if len(self.colorFieldName) > 0:
            f.setAttribute(self.colorFieldName, self.dimLineColor)         
      except:
         pass

      return f


   #============================================================================
   # FUNZIONI PER I BLOCCHI - FINE
   # FUNZIONI PER IL TESTO - INIZIO
   #============================================================================


   #============================================================================
   # getFormattedText
   #============================================================================
   def getFormattedText(self, measure):
      """
      Restituisce il testo della misura della quota formattato
      """
      if type(measure) == int or type(measure) == float:
         strIntPart, strDecPart = qad_utils.getStrIntDecParts(round(measure, self.textDecimals)) # numero di decimali
         
         if strIntPart == "0" and self.textSuppressLeadingZeros == True: # per sopprimere o meno gli zero all'inizio del testo
            strIntPart = ""
         
         for i in xrange(0, self.textDecimals - len(strDecPart), 1):  # aggiunge "0" per arrivare al numero di decimali
            strDecPart = strDecPart + "0"
            
         if self.textDecimalZerosSuppression == True: # per sopprimere gli zero finali nei decimali
            strDecPart = strDecPart.rstrip("0")
         
         formattedText = "-" if measure < 0 else "" # segno
         formattedText = formattedText + strIntPart # parte intera
         if len(strDecPart) > 0: # parte decimale
            formattedText = formattedText + self.textDecimalSep + strDecPart # Separatore dei decimali
         # aggiungo prefisso e suffisso per il testo della quota
         return self.textPrefix + formattedText + self.textSuffix
      elif type(measure) == unicode or type(measure) == str:
         return measure
      else:
         return ""


   #============================================================================
   # getNumericText
   #============================================================================
   def getNumericText(self, text):
      """
      Restituisce il valore numerico del testo della misura della quota formattato
      """
      textToConvert = text.lstrip(self.textPrefix)
      textToConvert = textToConvert.rstrip(self.textSuffix)
      textToConvert = textToConvert.replace(self.textDecimalSep, ".")

      return qad_utils.str2float(textToConvert)

   
   #============================================================================
   # textRectToQadLinearObjectList
   #============================================================================
   def textRectToQadLinearObjectList(self, ptBottomLeft, textWidth, textHeight, rot):
      """
      Restituisce il rettangolo che rappresenta il testo sotto forma di una QadLinearObjectList.
      <2>----width----<3>
       |               |
     height          height
       |               |
      <1>----width----<4>      
      """
      pt2 = qad_utils.getPolarPointByPtAngle(ptBottomLeft, rot + (math.pi / 2), textHeight)   
      pt3 = qad_utils.getPolarPointByPtAngle(pt2, rot, textWidth)   
      pt4 = qad_utils.getPolarPointByPtAngle(ptBottomLeft, rot , textWidth)
      res = qad_utils.QadLinearObjectList()
      res.fromPolyline([ptBottomLeft, pt2, pt3, pt4, ptBottomLeft])
      return res


   #============================================================================
   # getBoundingPointsTextRectProjectedToLine
   #============================================================================
   def getBoundingPointsTextRectProjectedToLine(self, pt1, pt2, textRect):
      """
      Restituisce una lista di 2 punti che sono i punti estremi della proiezione dei 4 angoli del rettangolo
      sulla linea pt1-pt2.
      """
      rectCorners = textRect.asPolyline()
      # calcolo la proiezione degli angoli del rettangolo sulla linea pt1-pt2
      perpPts = []
      
      qad_utils.appendUniquePointToList(perpPts, qad_utils.getPerpendicularPointOnInfinityLine(pt1, pt2, rectCorners[0]))      
      qad_utils.appendUniquePointToList(perpPts, qad_utils.getPerpendicularPointOnInfinityLine(pt1, pt2, rectCorners[1]))
      qad_utils.appendUniquePointToList(perpPts, qad_utils.getPerpendicularPointOnInfinityLine(pt1, pt2, rectCorners[2]))
      qad_utils.appendUniquePointToList(perpPts, qad_utils.getPerpendicularPointOnInfinityLine(pt1, pt2, rectCorners[3]))
         
      return qad_utils.getBoundingPtsOnOnInfinityLine(pt1, pt2, perpPts)


   #============================================================================
   # getIntersectionPtsBetweenTextRectAndLine
   #============================================================================
   def getIntersectionPtsBetweenTextRectAndLine(self, rect, pt1, pt2):
      """
      Restituisce i punti di intersezione tra il rettangolo (QadLinearObjectList) che rappresenta il testo
      e un segmento pt1-pt2. La lista é ordinata per distanza da pt1.
      """
      segment = qad_utils.QadLinearObject([pt1, pt2])
      return rect.getIntersectionPtsWithLinearObject(segment, True)[0] # orderByStartPtOfPart = True
   

   #============================================================================
   # getTextPositionOnLine
   #============================================================================
   def getTextPositionOnLine(self, pt1, pt2, textWidth, textHeight, horizontalPos, verticalPos, rotMode):
      """
      pt1 = primo punto della linea
      pt2 = secondo punto della linea
      textWidth = larghezza testo
      textHeight = altezza testo
      
      Restituisce il punto di inserimento e la rotazione del testo lungo la linea pt1-pt2 con le modalità:
      horizontalPos = QadDimStyleTxtHorizontalPosEnum.CENTERED_LINE (centrato alla linea)
                      QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE (vicino al punto pt1)
                      QadDimStyleTxtHorizontalPosEnum.SECOND_EXT_LINE (vicino al punto pt2)
      verticalPos = QadDimStyleTxtVerticalPosEnum.CENTERED_LINE (centrato alla linea)
                    QadDimStyleTxtVerticalPosEnum.ABOVE_LINE (sopra alla linea)
                    QadDimStyleTxtVerticalPosEnum.BELOW_LINE (sotto alla linea)
      rotMode = QadDimStyleTxtRotModeEnum.HORIZONTAL (testo orizzontale)
                QadDimStyleTxtRotModeEnum.ALIGNED_LINE (testo allineato con la linea)
                QadDimStyleTxtRotModeEnum.FORCED_ROTATION (testo con rotazione forzata)
      """
      lineRot = qad_utils.getAngleBy2Pts(pt1, pt2) # angolo della linea
      
      if (lineRot > math.pi * 3 / 2 and lineRot <= math.pi * 2) or \
          (lineRot >= 0 and lineRot <= math.pi / 2): # da sx a dx
         textInsPtCloseToPt1 = True
      else: # da dx a sx
         textInsPtCloseToPt1 = False
      
      if rotMode == QadDimStyleTxtRotModeEnum.ALIGNED_LINE: # testo allineato alla linea   
         if lineRot > (math.pi / 2) and lineRot <= math.pi * 3 / 2: # se il testo é capovolto lo giro
            textRot = lineRot - math.pi
         else:
            textRot = lineRot
         
         # allineamento orizzontale
         #=========================
         if horizontalPos == QadDimStyleTxtHorizontalPosEnum.CENTERED_LINE: # testo centrato alla linea
            middlePt = qad_utils.getMiddlePoint(pt1, pt2)
            if textInsPtCloseToPt1: # il punto di inserimento del testo é vicino a pt1
               insPt = qad_utils.getPolarPointByPtAngle(middlePt, lineRot - math.pi, textWidth / 2)                              
            else: # il punto di inserimento del testo é vicino a pt2
               insPt = qad_utils.getPolarPointByPtAngle(middlePt, lineRot, textWidth / 2)
               
         elif horizontalPos == QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE: # testo vicino a pt1
            # uso 2 volte textOffsetDist perché una volta é la distanza dal punto pt1 + un offset intorno al testo
            if textInsPtCloseToPt1: # il punto di inserimento del testo é vicino a pt1
               insPt = qad_utils.getPolarPointByPtAngle(pt1, lineRot, self.textOffsetDist + self.textOffsetDist)
            else: # il punto di inserimento del testo é vicino a pt2
               insPt = qad_utils.getPolarPointByPtAngle(pt1, lineRot, textWidth + self.textOffsetDist + self.textOffsetDist)

         elif horizontalPos == QadDimStyleTxtHorizontalPosEnum.SECOND_EXT_LINE: # testo vicino a pt2
            # uso 2 volte textOffsetDist perché una volta é la distanza dal punto pt1 + un offset intorno al testo
            lineLen = qad_utils.getDistance(pt1, pt2)
            if textInsPtCloseToPt1: # il punto di inserimento del testo é vicino a pt1
               insPt = qad_utils.getPolarPointByPtAngle(pt1, lineRot, lineLen - textWidth - (self.textOffsetDist + self.textOffsetDist))
            else: # il punto di inserimento del testo é vicino a pt2
               insPt = qad_utils.getPolarPointByPtAngle(pt1, lineRot, lineLen - (self.textOffsetDist + self.textOffsetDist))         

         # allineamento verticale
         #=========================
         if verticalPos == QadDimStyleTxtVerticalPosEnum.CENTERED_LINE: # testo centrato alla linea
            if textInsPtCloseToPt1: # il punto di inserimento del testo é vicino a pt1
               insPt = qad_utils.getPolarPointByPtAngle(insPt, lineRot - math.pi / 2, textHeight / 2)
            else: # il punto di inserimento del testo é vicino a pt2
               insPt = qad_utils.getPolarPointByPtAngle(insPt, lineRot + math.pi / 2, textHeight / 2)
         elif verticalPos == QadDimStyleTxtVerticalPosEnum.ABOVE_LINE: # sopra alla linea
            # uso 2 volte textOffsetDist perché una volta é la distanza dalla linea + un offset intorno al testo
            if textInsPtCloseToPt1: # il punto di inserimento del testo é vicino a pt1
               insPt = qad_utils.getPolarPointByPtAngle(insPt, lineRot + math.pi / 2, self.textOffsetDist + self.textOffsetDist)
            else: # il punto di inserimento del testo é vicino a pt2
               insPt = qad_utils.getPolarPointByPtAngle(insPt, lineRot - math.pi / 2, self.textOffsetDist + self.textOffsetDist)
         elif verticalPos == QadDimStyleTxtVerticalPosEnum.BELOW_LINE: # sotto alla linea
            # uso 2 volte textOffsetDist perché una volta é la distanza dalla linea + un offset intorno al testo
            if textInsPtCloseToPt1: # il punto di inserimento del testo é vicino a pt1
               insPt = qad_utils.getPolarPointByPtAngle(insPt, lineRot - math.pi / 2, textHeight + (self.textOffsetDist + self.textOffsetDist))
            else: # il punto di inserimento del testo é vicino a pt2
               insPt = qad_utils.getPolarPointByPtAngle(insPt, lineRot + math.pi / 2, textHeight + (self.textOffsetDist + self.textOffsetDist))
      
      # testo orizzontale o testo con rotazione forzata
      elif rotMode == QadDimStyleTxtRotModeEnum.HORIZONTAL or rotMode == QadDimStyleTxtRotModeEnum.FORCED_ROTATION:
         
         lineLen = qad_utils.getDistance(pt1, pt2) # lunghezza della linea
         textRot = 0.0 if rotMode == QadDimStyleTxtRotModeEnum.HORIZONTAL else self.textForcedRot
         
         # cerco qual'é l'angolo del rettangolo più vicino alla linea
         #  <2>----width----<3>
         #   |               |
         # height          height
         #   |               |
         #  <1>----width----<4>
         # ricavo il rettangolo che racchiude il testo e lo posiziono con il suo angolo in basso a sinistra sul punto pt1
         textRect = self.textRectToQadLinearObjectList(pt1, textWidth, textHeight, textRot)
         # ottengo i punti estremi della proiezione del rettangolo sulla linea
         pts = self.getBoundingPointsTextRectProjectedToLine(pt1, pt2, textRect)
         projectedTextWidth = qad_utils.getDistance(pts[0], pts[1])

         # allineamento orizzontale
         #=========================
         if horizontalPos == QadDimStyleTxtHorizontalPosEnum.CENTERED_LINE: # testo centrato alla linea
            closestPtToPt1 = qad_utils.getPolarPointByPtAngle(pt1, lineRot, (lineLen - projectedTextWidth) / 2)
            
         elif horizontalPos == QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE: # testo vicino a pt1
            closestPtToPt1 = qad_utils.getPolarPointByPtAngle(pt1, lineRot, self.textOffsetDist)
                           
         elif horizontalPos == QadDimStyleTxtHorizontalPosEnum.SECOND_EXT_LINE: # testo vicino a pt2
            closestPtToPt1 = qad_utils.getPolarPointByPtAngle(pt1, lineRot, lineLen - self.textOffsetDist - projectedTextWidth)
         
         # se la linea ha una angolo tra (0-90] gradi (primo quadrante)
         if lineRot > 0 and lineRot <= math.pi / 2:
            # il punto più vicino a pt1 corrisponde all'angolo in basso a sinistra del rettangolo che racchiude il testo
            # mi ricavo il punto di inserimento del testo (angolo in basso a sinistra)            
            insPt = QgsPoint(closestPtToPt1)
            textRect = self.textRectToQadLinearObjectList(insPt, textWidth, textHeight, textRot)
            rectCorners = textRect.asPolyline()
            
            # allineamento verticale
            #=========================
            if verticalPos == QadDimStyleTxtVerticalPosEnum.ABOVE_LINE: # sopra alla linea
               # l'angolo 4 deve essere sopra la linea distante self.textOffsetDist dalla stessa
               rectPt = rectCorners[3]
            elif verticalPos == QadDimStyleTxtVerticalPosEnum.BELOW_LINE: # sotto alla linea
               # l'angolo 2 deve essere sotto la linea distante self.textOffsetDist dalla stessa
               rectPt = rectCorners[1]
           
         # se la linea ha una angolo tra (90-180] gradi (secondo quadrante)
         elif lineRot > math.pi / 2 and lineRot <= math.pi:
            # il punto più vicino a pt1 corrisponde all'angolo in basso a destra del rettangolo che racchiude il testo
            # mi ricavo il punto di inserimento del testo (angolo in basso a sinistra)            
            insPt = QgsPoint(closestPtToPt1.x() - textWidth, closestPtToPt1.y())
            textRect = self.textRectToQadLinearObjectList(insPt, textWidth, textHeight, textRot)
            rectCorners = textRect.asPolyline()
            
            # allineamento verticale
            #=========================
            if verticalPos == QadDimStyleTxtVerticalPosEnum.ABOVE_LINE: # sopra alla linea
               # l'angolo 1 deve essere sopra la linea distante self.textOffsetDist dalla stessa
               rectPt = rectCorners[0]
            elif verticalPos == QadDimStyleTxtVerticalPosEnum.BELOW_LINE: # sotto alla linea
               # l'angolo 3 deve essere sotto la linea distante self.textOffsetDist dalla stessa
               rectPt = rectCorners[2]
               
         # se la linea ha una angolo tra (180-270] gradi (terzo quadrante)
         elif lineRot > math.pi and lineRot <= math.pi * 3 / 2:
            # il punto più vicino a pt1 corrisponde all'angolo in alto a destra del rettangolo che racchiude il testo
            # mi ricavo il punto di inserimento del testo (angolo in basso a sinistra)            
            insPt = QgsPoint(closestPtToPt1.x() - textWidth, closestPtToPt1.y() - textHeight)
            textRect = self.textRectToQadLinearObjectList(insPt, textWidth, textHeight, textRot)
            rectCorners = textRect.asPolyline()

            # allineamento verticale
            #=========================
            if verticalPos == QadDimStyleTxtVerticalPosEnum.ABOVE_LINE: # sopra alla linea
               # l'angolo 4 deve essere sopra la linea distante self.textOffsetDist dalla stessa
               rectPt = rectCorners[3]
            elif verticalPos == QadDimStyleTxtVerticalPosEnum.BELOW_LINE: # sotto alla linea
               # l'angolo 2 deve essere sotto la linea distante self.textOffsetDist dalla stessa
               rectPt = rectCorners[1]
               
         # se la linea ha una angolo tra (270-360] gradi (quarto quadrante)
         elif (lineRot > math.pi * 3 / 2 and lineRot <= 360) or lineRot == 0:
            # il punto più vicino a pt1 corrisponde all'angolo in alto a destra del rettangolo che racchiude il testo
            # mi ricavo il punto di inserimento del testo (angolo in alto a sinistra)            
            insPt = QgsPoint(closestPtToPt1.x(), closestPtToPt1.y() - textHeight)
            textRect = self.textRectToQadLinearObjectList(insPt, textWidth, textHeight, textRot)
            rectCorners = textRect.asPolyline()
            
            # allineamento verticale
            #=========================
            if verticalPos == QadDimStyleTxtVerticalPosEnum.ABOVE_LINE: # sopra alla linea
               # l'angolo 1 deve essere sopra la linea distante self.textOffsetDist dalla stessa
               rectPt = rectCorners[0]
            elif verticalPos == QadDimStyleTxtVerticalPosEnum.BELOW_LINE: # sotto alla linea
               # l'angolo 3 deve essere sotto la linea distante self.textOffsetDist dalla stessa
               rectPt = rectCorners[2]

         # allineamento verticale
         #=========================         
         if verticalPos == QadDimStyleTxtVerticalPosEnum.CENTERED_LINE: # testo centrato alla linea
            # il centro del rettangolo deve essere sulla linea
            centerPt = qad_utils.getPolarPointByPtAngle(rectCorners[0], \
                                                      qad_utils.getAngleBy2Pts(rectCorners[0], rectCorners[2]), \
                                                      qad_utils.getDistance(rectCorners[0], rectCorners[2]) / 2)            
            perpPt = qad_utils.getPerpendicularPointOnInfinityLine(pt1, pt2, centerPt)
            offsetAngle = qad_utils.getAngleBy2Pts(centerPt, perpPt)
            offsetDist = qad_utils.getDistance(centerPt, perpPt)                                                 
         elif verticalPos == QadDimStyleTxtVerticalPosEnum.ABOVE_LINE: # sopra alla linea
            # l'angolo deve essere sopra la linea distante self.textOffsetDist dalla stessa
            perpPt = qad_utils.getPerpendicularPointOnInfinityLine(pt1, pt2, rectPt)
            # se la linea ha una angolo tra (90-270] gradi
            if lineRot > math.pi / 2 and lineRot <= math.pi * 3 / 2:
               offsetAngle = lineRot - math.pi / 2
            else: # se la linea ha una angolo tra (270-90] gradi
               offsetAngle = lineRot + math.pi / 2
            offsetDist = qad_utils.getDistance(rectPt, perpPt) + self.textOffsetDist
         elif verticalPos == QadDimStyleTxtVerticalPosEnum.BELOW_LINE: # sotto alla linea
            # l'angolo deve essere sotto la linea distante self.textOffsetDist dalla stessa
            perpPt = qad_utils.getPerpendicularPointOnInfinityLine(pt1, pt2, rectPt)
            # se la linea ha una angolo tra (90-270] gradi
            if lineRot > math.pi / 2 and lineRot <= math.pi * 3 / 2:
               offsetAngle = lineRot + math.pi / 2
            else: # se la linea ha una angolo tra (270-90] gradi
               offsetAngle = lineRot - math.pi / 2
            offsetDist = qad_utils.getDistance(rectPt, perpPt) + self.textOffsetDist
             
         # traslo il rettangolo
         insPt = qad_utils.getPolarPointByPtAngle(insPt, offsetAngle, offsetDist)
         textRect = self.textRectToQadLinearObjectList(insPt, textWidth, textHeight, textRot)
         
      return insPt, textRot


   #============================================================================
   # getTextPosAndLinesOutOfDimLines
   #============================================================================
   def getTextPosAndLinesOutOfDimLines(self, dimLinePt1, dimLinePt2, textWidth, textHeight):
      """      
      Restituisce una lista di 3 elementi nel caso il testo venga spostato fuori dalle linee 
      di estensione perché era troppo grosso:
      - il primo elemento é il punto di inserimento
      - il secondo elemento é la rotazione del testo 
      - il terzo elemento é una lista di linee da usare come porta quota
      
      La funzione lo posizione a lato della linea di estensione 2. 
      dimLinePt1 = primo punto della linea di quota (QgsPoint)
      dimLinePt2 = secondo punto della linea di quota (QgsPoint)
      textWidth = larghezza testo
      textHeight = altezza testo
      """
      # Ottengo le linee porta quota per il testo esterno
      lines = self.getLeaderLines(dimLinePt1, dimLinePt2, textWidth, textHeight)
      # considero l'ultima che é quella che si riferisce al testo
      line = lines[-1]
      
      if self.textRotMode == QadDimStyleTxtRotModeEnum.FORCED_ROTATION:
         textRotMode = QadDimStyleTxtRotModeEnum.FORCED_ROTATION
      else:
         textRotMode = QadDimStyleTxtRotModeEnum.ALIGNED_LINE
      
      textInsPt, textRot = self.getTextPositionOnLine(line[0], line[1], textWidth, textHeight, \
                                                      QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE, \
                                                      self.textVerticalPos, textRotMode)
      return textInsPt, textRot, lines


   #============================================================================
   # getLinearTextAndBlocksPosition
   #============================================================================
   def getLinearTextAndBlocksPosition(self, dimPt1, dimPt2, dimLinePt1, dimLinePt2, textWidth, textHeight):
      """
      dimPt1 = primo punto da quotare
      dimPt2 = secondo punto da quotare
      dimLinePt1 = primo punto della linea di quota (QgsPoint)
      dimLinePt2 = secondo punto della linea di quota (QgsPoint)
      textWidth  = larghezza testo
      textHeight = altezza testo
      
      Restituisce una lista di 4 elementi:
      - il primo elemento é una lista con il punto di inserimento del testo della quota e la sua rotazione
      - il secondo elemento é una lista con flag che indica il tipo della linea sulla quale é stato messo il testo; vedi QadDimComponentEnum
                            e una lista di linee "leader" nel caso il testo sia all'esterno della quota
      - il terzo elemento é la rotazione del primo blocco delle frecce; può essere None se non visibile
      - il quarto elemento é la rotazione del secondo blocco delle frecce; può essere None se non visibile   
      """      
      textInsPt                = None # punto di inserimento del testo
      textRot                  = None # rotazione del testo
      textLinearDimComponentOn = None # codice del componente lineare sul quale é posizionato il testo
      txtLeaderLines           = None # lista di linee "leader" nel caso il testo sia all'esterno della quota
      block1Rot                = None # rotazione del primo blocco delle frecce
      block2Rot                = None # rotazione del secondo blocco delle frecce
                     
      # se il testo é tra le linee di estensione della quota
      if self.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.CENTERED_LINE or \
         self.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE or \
         self.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.SECOND_EXT_LINE:

         dimLineRot = qad_utils.getAngleBy2Pts(dimLinePt1, dimLinePt2) # angolo della linea di quota
         
         # cambio gli estremi della linea di quota per considerare lo spazio occupato dai blocchi
         dimLinePt1Offset = qad_utils.getPolarPointByPtAngle(dimLinePt1, dimLineRot, self.getBlock1Size())
         dimLinePt2Offset = qad_utils.getPolarPointByPtAngle(dimLinePt2, dimLineRot + math.pi, self.getBlock2Size())
    
         # testo sopra o sotto alla linea di quota nel caso la linea di quota non sia orizzontale 
         # e il testo sia dentro le linee di estensione e forzato orizzontale allora il testo diventa centrato
         if (self.textVerticalPos == QadDimStyleTxtVerticalPosEnum.ABOVE_LINE or self.textVerticalPos == QadDimStyleTxtVerticalPosEnum.BELOW_LINE) and \
            (dimLineRot != 0 and dimLineRot != math.pi) and self.textRotMode == QadDimStyleTxtRotModeEnum.HORIZONTAL:            
            textVerticalPos = QadDimStyleTxtVerticalPosEnum.CENTERED_LINE
         # testo posizionato nella parte opposta ai punti di quotatura
         elif self.textVerticalPos == QadDimStyleTxtVerticalPosEnum.EXTERN_LINE:
            # angolo dal primo punto di quota al primo punto della linea di quota
            dimPtToDimLinePt_rot = qad_utils.getAngleBy2Pts(dimPt1, dimLinePt1)
            if dimPtToDimLinePt_rot > 0 and \
               (dimPtToDimLinePt_rot < math.pi or qad_utils.doubleNear(dimPtToDimLinePt_rot,  math.pi)):
               textVerticalPos = QadDimStyleTxtVerticalPosEnum.ABOVE_LINE
            else:
               textVerticalPos = QadDimStyleTxtVerticalPosEnum.BELOW_LINE
         else:
            textVerticalPos = self.textVerticalPos
         
         if self.textRotMode == QadDimStyleTxtRotModeEnum.ISO:
            textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1Offset, dimLinePt2Offset, textWidth, textHeight, \
                                                            self.textHorizontalPos, textVerticalPos, QadDimStyleTxtRotModeEnum.ALIGNED_LINE)
         else:
            textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1Offset, dimLinePt2Offset, textWidth, textHeight, \
                                                            self.textHorizontalPos, textVerticalPos, self.textRotMode)
         
         rect = self.textRectToQadLinearObjectList(textInsPt, textWidth, textHeight, textRot)
         spaceForBlock1, spaceForBlock2 = self.getSpaceForBlock1AndBlock2(rect, dimLinePt1, dimLinePt2)
                  
         # se lo spazio non é sufficiente per inserire testo e simboli all'interno delle linee di estensione,
         # uso qad_utils.doubleSmaller perché a volte i due numeri sono quasi uguali 
         if spaceForBlock1 == 0 or spaceForBlock2 == 0 or \
            qad_utils.doubleSmaller(spaceForBlock1, self.getBlock1Size() + self.textOffsetDist) or \
            qad_utils.doubleSmaller(spaceForBlock2, self.getBlock2Size() + self.textOffsetDist):
            if self.blockSuppressionForNoSpace: # sopprime i simboli se non c'é spazio sufficiente all'interno delle linee di estensione
               block1Rot = None
               block2Rot = None
               
               # considero il testo senza frecce
               if self.textRotMode == QadDimStyleTxtRotModeEnum.ISO:
                  textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1, dimLinePt2, textWidth, textHeight, \
                                                                  self.textHorizontalPos, textVerticalPos, QadDimStyleTxtRotModeEnum.ALIGNED_LINE)
               else:
                  textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1, dimLinePt2, textWidth, textHeight, \
                                                                  self.textHorizontalPos, textVerticalPos, self.textRotMode)
               
               rect = self.textRectToQadLinearObjectList(textInsPt, textWidth, textHeight, textRot)
               spaceForBlock1, spaceForBlock2 = self.getSpaceForBlock1AndBlock2(rect, dimLinePt1, dimLinePt2)
               # se non c'é spazio neanche per il testo senza le frecce
               if spaceForBlock1 == 0 or spaceForBlock2 == 0 or \
                  spaceForBlock1 < self.textOffsetDist or spaceForBlock2 < self.textOffsetDist:           
                  # sposta testo fuori dalle linee di estensione
                  textInsPt, textRot, txtLeaderLines = self.getTextPosAndLinesOutOfDimLines(dimLinePt1, dimLinePt2, textWidth, textHeight)
                  textLinearDimComponentOn = QadDimComponentEnum.LEADER_LINE
               else:
                  textLinearDimComponentOn = QadDimComponentEnum.DIM_LINE1                
            else: # non devo sopprimere i simboli
               # la prima cosa da spostare all'esterno é :
               if self.textBlockAdjust == QadDimStyleTextBlocksAdjustEnum.BOTH_OUTSIDE_EXT_LINES:
                  # sposta testo e frecce fuori dalle linee di estensione
                  textInsPt, textRot, txtLeaderLines = self.getTextPosAndLinesOutOfDimLines(dimLinePt1, dimLinePt2, textWidth, textHeight)
                  textLinearDimComponentOn = QadDimComponentEnum.LEADER_LINE 
                  block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, False) # frecce esterne 
               # sposta prima le frecce poi, se non basta, anche il testo
               elif self.textBlockAdjust == QadDimStyleTextBlocksAdjustEnum.FIRST_BLOCKS_THEN_TEXT:
                  block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, False) # frecce esterne 
                  # considero il testo senza frecce
                  if self.textRotMode == QadDimStyleTxtRotModeEnum.ISO:
                     textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1, dimLinePt2, textWidth, textHeight, \
                                                                     self.textHorizontalPos, textVerticalPos, QadDimStyleTxtRotModeEnum.ALIGNED_LINE)
                  else:
                     textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1, dimLinePt2, textWidth, textHeight, \
                                                                     self.textHorizontalPos, textVerticalPos, self.textRotMode)
                  
                  rect = self.textRectToQadLinearObjectList(textInsPt, textWidth, textHeight, textRot)
                  spaceForBlock1, spaceForBlock2 = self.getSpaceForBlock1AndBlock2(rect, dimLinePt1, dimLinePt2)
                  # se non c'é spazio neanche per il testo senza le frecce
                  if spaceForBlock1 == 0 or spaceForBlock2 == 0 or \
                     spaceForBlock1 < self.textOffsetDist or spaceForBlock2 < self.textOffsetDist:                
                     # sposta testo fuori dalle linee di estensione
                     textInsPt, textRot, txtLeaderLines = self.getTextPosAndLinesOutOfDimLines(dimLinePt1, dimLinePt2, textWidth, textHeight)
                     textLinearDimComponentOn = QadDimComponentEnum.LEADER_LINE
                  else:
                     textLinearDimComponentOn = QadDimComponentEnum.DIM_LINE1 
               # sposta prima il testo poi, se non basta, anche le frecce
               elif self.textBlockAdjust == QadDimStyleTextBlocksAdjustEnum.FIRST_TEXT_THEN_BLOCKS:
                  # sposto il testo fuori dalle linee di estensione
                  textInsPt, textRot, txtLeaderLines = self.getTextPosAndLinesOutOfDimLines(dimLinePt1, dimLinePt2, textWidth, textHeight)
                  textLinearDimComponentOn = QadDimComponentEnum.LEADER_LINE 
                  # se non ci stanno neanche le frecce
                  if qad_utils.getDistance(dimLinePt1, dimLinePt2) <= self.getBlock1Size() + self.getBlock2Size():
                     block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, False) # frecce esterne 
                  else:
                     block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, True) # frecce interne
               # Sposta indistintamente il testo o le frecce (l'oggetto che si adatta meglio)
               elif self.textBlockAdjust == QadDimStyleTextBlocksAdjustEnum.WHICHEVER_FITS_BEST:
                  # sposto il più ingombrante
                  if self.getBlock1Size() + self.getBlock2Size() > textWidth: # le frecce sono più ingombranti del testo
                     textLinearDimComponentOn = QadDimComponentEnum.DIM_LINE1
                     block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, False) # frecce esterne
                     
                     # considero il testo senza frecce
                     if self.textRotMode == QadDimStyleTxtRotModeEnum.ISO:                     
                        textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1, dimLinePt2, textWidth, textHeight, \
                                                                        self.textHorizontalPos, textVerticalPos, QadDimStyleTxtRotModeEnum.ALIGNED_LINE)
                     else:
                        textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1, dimLinePt2, textWidth, textHeight, \
                                                                        self.textHorizontalPos, textVerticalPos, self.textRotMode)
                     
                     rect = self.textRectToQadLinearObjectList(textInsPt, textWidth, textHeight, textRot)
                     spaceForBlock1, spaceForBlock2 = self.getSpaceForBlock1AndBlock2(rect, dimLinePt1, dimLinePt2)
                     # se non c'é spazio neanche per il testo senza le frecce
                     if spaceForBlock1 == 0 or spaceForBlock2 == 0 or \
                        spaceForBlock1 < self.textOffsetDist or spaceForBlock2 < self.textOffsetDist:                
                        # sposta testo fuori dalle linee di estensione
                        textInsPt, textRot, txtLeaderLines = self.getTextPosAndLinesOutOfDimLines(dimLinePt1, dimLinePt2, textWidth, textHeight)
                        textLinearDimComponentOn = QadDimComponentEnum.LEADER_LINE
                     else:
                        textLinearDimComponentOn = QadDimComponentEnum.DIM_LINE1 
                  else: # il testo é più ingombrante dei simboli
                     # sposto il testo fuori dalle linee di estensione
                     textInsPt, textRot, txtLeaderLines = self.getTextPosAndLinesOutOfDimLines(dimLinePt1, dimLinePt2, textWidth, textHeight)
                     textLinearDimComponentOn = QadDimComponentEnum.LEADER_LINE 
                     # se non ci stanno neanche le frecce
                     if qad_utils.getDistance(dimLinePt1, dimLinePt2) <= self.getBlock1Size() + self.getBlock2Size():
                        block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, False) # frecce esterne 
                     else:
                        block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, True) # frecce interne
         else: # se lo spazio é sufficiente per inserire testo e simboli all'interno delle linee di estensione,
            textLinearDimComponentOn = QadDimComponentEnum.DIM_LINE1
            block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, True) # frecce interne
      
      # il testo é sopra e allineato alla prima linea di estensione         
      elif self.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE_UP:
         # angolo della linea che va dal punto di quota all'inizio della linea di quota
         rotLine = qad_utils.getAngleBy2Pts(dimPt1, dimLinePt1)
         pt = qad_utils.getPolarPointByPtAngle(dimLinePt1, rotLine, self.textOffsetDist + textWidth)
         if self.textVerticalPos == QadDimStyleTxtVerticalPosEnum.EXTERN_LINE:
            textVerticalPos = QadDimStyleTxtVerticalPosEnum.ABOVE_LINE
         else:
            textVerticalPos = self.textVerticalPos
         
         if self.textRotMode == QadDimStyleTxtRotModeEnum.FORCED_ROTATION:
            textRotMode = QadDimStyleTxtRotModeEnum.FORCED_ROTATION
         else:
            textRotMode = QadDimStyleTxtRotModeEnum.ALIGNED_LINE
            
         textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1, pt, textWidth, textHeight, \
                                                         QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE, \
                                                         textVerticalPos, textRotMode)
         textLinearDimComponentOn = QadDimComponentEnum.EXT_LINE1 
         
         # calcolo lo spazio dei blocchi in assenza del testo
         spaceForBlock1, spaceForBlock2 = self.getSpaceForBlock1AndBlock2(None, dimLinePt1, dimLinePt2)
         # se non c'é spazio per i blocchi
         if spaceForBlock1 < self.getBlock1Size() or spaceForBlock2 < self.getBlock2Size():
            if self.blockSuppressionForNoSpace: # i blocchi sono soppressi
               block1Rot = None
               block2Rot = None
            else: # sposto le frecce all'esterno
               block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, False)
         else: # c'é spazio per i blocchi
            block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, True) # frecce interne
               
      # il testo é sopra e allineato alla seconda linea di estensione         
      elif self.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.SECOND_EXT_LINE_UP:
         # angolo della linea che va dal punto di quota all'inizio della linea di quota
         rotLine = qad_utils.getAngleBy2Pts(dimPt2, dimLinePt2)
         pt = qad_utils.getPolarPointByPtAngle(dimLinePt2, rotLine, self.textOffsetDist + textWidth)
         if self.textVerticalPos == QadDimStyleTxtVerticalPosEnum.EXTERN_LINE:
            textVerticalPos = QadDimStyleTxtVerticalPosEnum.ABOVE_LINE
         else:
            textVerticalPos = self.textVerticalPos
            
         if self.textRotMode == QadDimStyleTxtRotModeEnum.FORCED_ROTATION:
            textRotMode = QadDimStyleTxtRotModeEnum.FORCED_ROTATION
         else:
            textRotMode = QadDimStyleTxtRotModeEnum.ALIGNED_LINE
            
         textInsPt, textRot = self.getTextPositionOnLine(dimLinePt2, pt, textWidth, textHeight, \
                                                         QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE, \
                                                         textVerticalPos, textRotMode)
         textLinearDimComponentOn = QadDimComponentEnum.EXT_LINE2 
         
         # calcolo lo spazio dei blocchi in assenza del testo
         spaceForBlock1, spaceForBlock2 = self.getSpaceForBlock1AndBlock2(None, dimLinePt1, dimLinePt2)
         # se non c'é spazio per i blocchi
         if spaceForBlock1 < self.getBlock1Size() or spaceForBlock2 < self.getBlock2Size():
            if self.blockSuppressionForNoSpace: # i blocchi sono soppressi
               block1Rot = None
               block2Rot = None
            else: # sposto le frecce all'esterno
               block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, False)
         else: # c'é spazio per i blocchi
            block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, True) # frecce interne
      
      if self.textDirection == QadDimStyleTxtDirectionEnum.DX_TO_SX:
         # il punto di inserimento diventa l'angolo in alto a destra del rettangolo
         textInsPt = qad_utils.getPolarPointByPtAngle(textInsPt, textRot, textWidth)
         textInsPt = qad_utils.getPolarPointByPtAngle(textInsPt, textRot + math.pi / 2, textHeight)
         # la rotazione viene capovolta
         textRot = qad_utils.normalizeAngle(textRot + math.pi)
   
      return [[textInsPt, textRot], [textLinearDimComponentOn, txtLeaderLines], block1Rot, block2Rot]
            
   
   #============================================================================
   # getTextFeature
   #============================================================================
   def getTextFeature(self, measure, pt = None, rot = None, sourceCrs = None):
      """
      Restituisce la feature per il testo della quota.
      La rotazione é espressa in radianti.
      sourceCrs = sistema di coordinate di pt
      """
      _pt = QgsPoint(0,0) if pt is None else pt
      _rot = 0 if rot is None else rot
      
      textualFeaturePrototype = self.getTextualFeaturePrototype()
      if textualFeaturePrototype is None:
         return None
      f = QgsFeature(textualFeaturePrototype)
      g = QgsGeometry.fromPoint(_pt)
      
      if (sourceCrs is not None) and sourceCrs != self.getTextualLayer().crs():
         coordTransform = QgsCoordinateTransform(sourceCrs, self.getTextualLayer().crs()) # trasformo la geometria
         g.transform(coordTransform)                        
       
      f.setGeometry(g)

      # se il testo dipende da un solo campo 
      labelFieldNames = qad_label.get_labelFieldNames(self.getTextualLayer())
      if len(labelFieldNames) == 1 and len(labelFieldNames[0]) > 0:
         f.setAttribute(labelFieldNames[0], self.getFormattedText(measure))

      # se l'altezza testo dipende da un solo campo 
      sizeFldNames = qad_label.get_labelSizeFieldNames(self.getTextualLayer())
      if len(sizeFldNames) == 1 and len(sizeFldNames[0]) > 0:
         f.setAttribute(sizeFldNames[0], self.textHeight) # altezza testo
         
      # se la rotazione dipende da un solo campo
      rotFldNames = qad_label.get_labelRotationFieldNames(self.getTextualLayer())
      if len(rotFldNames) == 1 and len(rotFldNames[0]) > 0:
         f.setAttribute(rotFldNames[0], qad_utils.toDegrees(_rot)) # Converte da radianti a gradi
   
      # se il font dipende da un solo campo
      fontFamilyFldNames = qad_label.get_labelFontFamilyFieldNames(self.getTextualLayer())
      if len(fontFamilyFldNames) == 1 and len(fontFamilyFldNames[0]) > 0:
         f.setAttribute(fontFamilyFldNames[0], self.textFont) # nome del font di testo      
      
      # imposto il colore
      try:
         if len(self.colorFieldName) > 0:
            f.setAttribute(self.colorFieldName, self.textColor)
      except:
         pass
      
      # imposto lo stile di quotatura
      try:
         if len(self.dimStyleFieldName) > 0:
            f.setAttribute(self.dimStyleFieldName, self.name)         
         if len(self.dimTypeFieldName) > 0:
            f.setAttribute(self.dimTypeFieldName, self.dimType)         
      except:
         pass
      
      return f  

             
   #============================================================================
   # FUNZIONI PER IL TESTO - FINE
   # FUNZIONI PER LA LINEA DI LEADER - INIZIO
   #============================================================================


   #============================================================================
   # getLeaderLines
   #============================================================================
   def getLeaderLines(self, dimLinePt1, dimLinePt2, textWidth, textHeight):
      """
      Restituisce una lista di linee che formano il porta quota nel caso il testo venga spostato
      fuori dalle linee di estensione perché era troppo grosso.
      dimLinePt1 = primo punto della linea di quota (QgsPoint)
      dimLinePt2 = secondo punto della linea di quota (QgsPoint)
      textWidth = larghezza testo
      textHeight = altezza testo
      """
      # le linee sono a lato della linea di estensione 1
      if self.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE:
         rotLine = qad_utils.getAngleBy2Pts(dimLinePt2, dimLinePt1) # angolo della linea porta quota
         pt1 = qad_utils.getPolarPointByPtAngle(dimLinePt1, rotLine, self.getBlock1Size())
         line1 = [dimLinePt1, pt1]
      # le linee sono a lato della linea di estensione 2
      else:
         rotLine = qad_utils.getAngleBy2Pts(dimLinePt1, dimLinePt2) # angolo della linea porta quota
         pt1 = qad_utils.getPolarPointByPtAngle(dimLinePt2, rotLine, self.getBlock1Size())
         line1 = [dimLinePt2, pt1]
         
      # modalità di rotazione del testo orizzontale o
      # testo allineato con la linea di quota se tra le linee di estensione, altrimenti testo orizzontale
      if self.textRotMode == QadDimStyleTxtRotModeEnum.HORIZONTAL or \
         self.textRotMode == QadDimStyleTxtRotModeEnum.ISO:
         if qad_utils.doubleNear(rotLine, math.pi / 2): # verticale dal basso verso l'alto
            pt2 = qad_utils.getPolarPointByPtAngle(pt1, 0, self.textOffsetDist + textWidth)
         elif qad_utils.doubleNear(rotLine, math.pi * 3 / 2): # verticale dall'alto verso il basso 
            pt2 = qad_utils.getPolarPointByPtAngle(pt1, math.pi, self.textOffsetDist + textWidth)
         elif (rotLine > math.pi * 3 / 2 and rotLine <= math.pi * 2) or \
              (rotLine >= 0 and rotLine < math.pi / 2): # da sx a dx
            pt2 = qad_utils.getPolarPointByPtAngle(pt1, 0, self.textOffsetDist + textWidth)
         else: # da dx a sx
            pt2 = qad_utils.getPolarPointByPtAngle(pt1, math.pi, self.textOffsetDist + textWidth)
      elif self.textRotMode == QadDimStyleTxtRotModeEnum.ALIGNED_LINE: # testo allineato con la linea di quota
         pt2 = qad_utils.getPolarPointByPtAngle(pt1, rotLine, self.textOffsetDist + textWidth)
      elif self.textRotMode == QadDimStyleTxtRotModeEnum.FORCED_ROTATION: # testo con rotazione forzata
         pt2 = qad_utils.getPolarPointByPtAngle(pt1, self.textForcedRot, self.textOffsetDist + textWidth)

      line2 = [pt1, pt2]
      return [line1, line2]      


   #============================================================================
   # getExtLineFeature
   #============================================================================
   def getLeaderFeature(self, leaderLines, sourceCrs = None):
      """
      Restituisce la feature per la linea di estensione.
      leaderLines = lista di linee di leader [line1, line2 ...]
      sourceCrs = sistema di coordinate di leaderLines
      """
      if leaderLines is None:
         return None

      linearFeaturePrototype = self.getLinearFeaturePrototype()
      if linearFeaturePrototype is None:
         return None
      f = QgsFeature(linearFeaturePrototype)
       
      pts = []
      first = True
      for line in leaderLines:
         if first:
            pts.append(line[0])
            first = False
         pts.append(line[1])
         
      g = QgsGeometry.fromPolyline(pts)
         
      if (sourceCrs is not None) and sourceCrs != self.getLinearLayer().crs():
         coordTransform = QgsCoordinateTransform(sourceCrs, self.getLinearLayer().crs()) # trasformo la geometria
         g.transform(coordTransform)                        
                
      f.setGeometry(g)
         
      try:
         # imposto il tipo di componente della quotatura
         if len(self.componentFieldName) > 0:
            f.setAttribute(self.componentFieldName, QadDimComponentEnum.LEADER_LINE)
      except:
         pass

      try:
         # imposto il tipo di linea
         if len(self.lineTypeFieldName) > 0:
            f.setAttribute(self.lineTypeFieldName, self.dimLineLineType)         
      except:
         pass

      try:
         # imposto il colore
         if len(self.colorFieldName) > 0:
            f.setAttribute(self.colorFieldName, self.dimLineColor)         
      except:
         pass

      return f
      

   #============================================================================
   # FUNZIONI PER LA LINEA DI LEADER - FINE
   # FUNZIONI PER LE LINEE DI ESTENSIONE - INIZIO
   #============================================================================


   #============================================================================
   # getExtLine
   #============================================================================
   def getExtLine(self, dimPt, dimLinePt):
      """
      dimPt     = punto da quotare
      dimLinePt = corrispondente punto della linea di quotatura
      
      ritorna una linea di estensione modificata secondo lo stile di quotatura
      il primo punto é vicino alla linea di quota, il secondo al punto da quotare
      """

      angle = qad_utils.getAngleBy2Pts(dimPt, dimLinePt)
      # distanza della linea di estensione oltre la linea di quota
      pt1 = qad_utils.getPolarPointByPtAngle(dimLinePt, angle, self.extLineOffsetDimLine)
      # distanza della linea di estensione dai punti da quotare
      pt2 = qad_utils.getPolarPointByPtAngle(dimPt, angle, self.extLineOffsetOrigPoints)        

      if self.extLineIsFixedLen == True: # attivata lunghezza fissa delle line di estensione      
         if qad_utils.getDistance(pt1, pt2) > self.extLineFixedLen:
            # lunghezza fissa delle line di estensione (DIMFXL) dalla linea di quota 
            # al punto da quotare spostato di extLineOffsetOrigPoints
            # (la linea di estensione non va oltre il punto da quotare)
            d = qad_utils.getDistance(dimLinePt, dimPt)
            if d > self.extLineFixedLen:
               d = self.extLineFixedLen
            pt2 = qad_utils.getPolarPointByPtAngle(dimLinePt, angle + math.pi, d)        

      return [pt1, pt2]


   #============================================================================
   # getExtLineFeature
   #============================================================================
   def getExtLineFeature(self, extLine, isExtLine1, sourceCrs = None):
      """
      Restituisce la feature per la linea di estensione.
      extLine = linea di estensione [pt1, pt2]
      isExtLine1 = se True si tratta della linea di estensione 1 altrimenti della linea di estensione 2
      sourceCrs = sistema di coordinate di extLine
      """
      if (isExtLine1 == True and self.extLine1Show == False) or \
         (isExtLine1 == False and self.extLine2Show == False):
         return None
      
      f = QgsFeature(self.getLinearFeaturePrototype())
      g = QgsGeometry.fromPolyline(extLine)
       
      if (sourceCrs is not None) and sourceCrs != self.getLinearLayer().crs():
         coordTransform = QgsCoordinateTransform(sourceCrs, self.getLinearLayer().crs()) # trasformo la geometria
         g.transform(coordTransform)
       
      f.setGeometry(g)
                  
      try:
         # imposto il tipo di componente della quotatura
         if len(self.componentFieldName) > 0:
            f.setAttribute(self.componentFieldName, QadDimComponentEnum.EXT_LINE1 if isExtLine1 else QadDimComponentEnum.EXT_LINE2)
      except:
         pass

      try:
         # imposto il tipo di linea
         if len(self.lineTypeFieldName) > 0:
            f.setAttribute(self.lineTypeFieldName, self.extLine1LineType if isExtLine1 else self.extLine2LineType)         
      except:
         pass

      try:
         # imposto il colore
         if len(self.colorFieldName) > 0:
            f.setAttribute(self.colorFieldName, self.extLineColor) 
      except:
         pass

      return f

             
   #============================================================================
   # FUNZIONI PER LE LINEE DI ESTENSIONE - FINE
   # FUNZIONI PER LA LINEA DI QUOTA - INIZIO
   #============================================================================
      

   #============================================================================
   # getDimLine
   #============================================================================
   def getDimLine(self, dimPt1, dimPt2, linePosPt, preferredAlignment = QadDimStyleAlignmentEnum.HORIZONTAL,
                  dimLineRotation = 0.0):
      """
      Restituisce la linea di quotatura:

      dimPt1 = primo punto da quotare
      dimPt2 = secondo punto da quotare
      linePosPt = punto per indicare dove deve essere posizionata la linea di quota
      preferredAlignment = indica se ci si deve allineare ai punti di quota in modo orizzontale o verticale
                           (se i punti di quota formano una linea obliqua). Usato solo per le quotature lineari 
      dimLineRotation = angolo della linea di quotatura (default = 0). Usato solo per le quotature lineari 
      """      
      if self.dimType == QadDimTypeEnum.ALIGNED:
         # calcolo la proiezione perpendicolare del punto <linePosPt> sulla linea che congiunge <dimPt1> a <dimPt2>
         ptPerp = qad_utils.getPerpendicularPointOnInfinityLine(dimPt1, dimPt2, linePosPt)
         d = qad_utils.getDistance(linePosPt, ptPerp)
   
         angle = qad_utils.getAngleBy2Pts(dimPt1, dimPt2)
         if qad_utils.leftOfLine(linePosPt, dimPt1, dimPt2) < 0: # a sinistra della linea che congiunge <dimPt1> a <dimPt2>
            angle = angle + (math.pi / 2)
         else:
            angle = angle - (math.pi / 2)
   
         return [qad_utils.getPolarPointByPtAngle(dimPt1, angle, d), \
                 qad_utils.getPolarPointByPtAngle(dimPt2, angle, d)]
      elif self.dimType == QadDimTypeEnum.LINEAR:
         if preferredAlignment == QadDimStyleAlignmentEnum.HORIZONTAL:
            ptDummy = qad_utils.getPolarPointByPtAngle(dimPt1, dimLineRotation + math.pi / 2, 1)
            pt1 = qad_utils.getPerpendicularPointOnInfinityLine(dimPt1, ptDummy, linePosPt)
            ptDummy = qad_utils.getPolarPointByPtAngle(dimPt2, dimLineRotation + math.pi / 2, 1)
            pt2 = qad_utils.getPerpendicularPointOnInfinityLine(dimPt2, ptDummy, linePosPt)
 
            return [pt1, pt2]
         elif preferredAlignment == QadDimStyleAlignmentEnum.VERTICAL:
            ptDummy = qad_utils.getPolarPointByPtAngle(dimPt1, dimLineRotation, 1)
            pt1 = qad_utils.getPerpendicularPointOnInfinityLine(dimPt1, ptDummy, linePosPt)
            ptDummy = qad_utils.getPolarPointByPtAngle(dimPt2, dimLineRotation, 1)
            pt2 = qad_utils.getPerpendicularPointOnInfinityLine(dimPt2, ptDummy, linePosPt)
 
            return [pt1, pt2]


   #============================================================================
   # getDimLineFeature
   #============================================================================
   def getDimLineFeature(self, dimLine, isDimLine1, textLinearDimComponentOn, sourceCrs = None):
      """
      Restituisce la feature per la linea di quota.
      dimLine = linea di quota [pt1, pt2]
      isDimLine1 = se True si tratta della linea di quota 1 altrimenti della linea di quota 2
      textLinearDimComponentOn = indica il componente della quota dove é situato il testo di quota (QadDimComponentEnum)
      sourceCrs = sistema di coordinate di dimLine
      """
            
      # se non c'é la linea di quota
      if dimLine is None:
         return None
      if isDimLine1 == True: # se si tratta della linea di quota 1
         # se la linea di quota 1 deve essere invisibile (vale solo se il testo é sulla linea di quota)
         if self.dimLine1Show == False and \
           (textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1 or textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE2):
            return None
      else: # se si tratta della linea di quota 2
         # se la linea di quota 2 deve essere invisibile (vale solo se il testo é sulla linea di quota)
         if self.dimLine2Show == False and \
           (textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1 or textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE2):
            return None
               
      f = QgsFeature(self.getLinearFeaturePrototype())
      g = QgsGeometry.fromPolyline(dimLine)
       
      if (sourceCrs is not None) and sourceCrs != self.getLinearLayer().crs():
         coordTransform = QgsCoordinateTransform(sourceCrs, self.getLinearLayer().crs()) # trasformo la geometria
         g.transform(coordTransform)                        
       
      f.setGeometry(g)
         
      try:
         # imposto il tipo di componente della quotatura
         if len(self.componentFieldName) > 0:
            f.setAttribute(self.componentFieldName, QadDimComponentEnum.DIM_LINE1 if isDimLine1 else QadDimComponentEnum.DIM_LINE2)
      except:
         pass

      try:
         # imposto il tipo di linea
         if len(self.lineTypeFieldName) > 0:
            f.setAttribute(self.lineTypeFieldName, self.dimLineLineType)         
      except:
         pass

      try:
         # imposto il colore
         if len(self.colorFieldName) > 0:
            f.setAttribute(self.colorFieldName, self.dimLineColor)         
      except:
         pass

      return f
         

   #============================================================================
   # FUNZIONI PER LA LINEA DI QUOTA - FINE
   # FUNZIONI PER LA QUOTATURA LINEARE - INIZIO
   #============================================================================
   

   #============================================================================
   # getLinearDimFeatures
   #============================================================================
   def getLinearDimFeatures(self, canvas, dimPt1, dimPt2, linePosPt, measure = None, \
                            preferredAlignment = QadDimStyleAlignmentEnum.HORIZONTAL, \
                            dimLineRotation = 0.0):
      """
      dimPt1 = primo punto da quotare (in unita di mappa)
      dimPt2 = secondo punto da quotare (in unita di mappa)
      linePosPt = punto per indicare dove deve essere posizionata la linea di quota (in unita di mappa)
      measure = indica se la misura é predeterminata oppure (se = None) deve essere calcolata
      preferredAlignment = se lo stile di quota é lineare, indica se ci si deve allienare ai punti di quota
                           in modo orizzontale o verticale (se i punti di quota formano una linea obliqua)      
      dimLineRotation = angolo della linea di quotatura (default = 0) 
      
      # quota lineare con una linea di quota orizzontale o verticale
      # ritorna una lista di elementi che descrivono la geometria della quota:
      # 1 lista = feature del primo e del secondo punto di quota; QgsFeature 1, QgsFeature 2
      # 2 lista = feature della prima e della seconda linea di quota (quest'ultima può essere None); QgsFeature 1, QgsFeature 2
      # 3 lista = feature del punto del testo di quota e geometria del rettangolo di occupazione; QgsFeature, QgsGeometry
      # 4 lista = feature del primo e del secondo simbolo per la linea di quota (possono essere None); QgsFeature 1, QgsFeature 2
      # 5 lista = feature della prima e della seconda linea di estensione (possono essere None); QgsFeature 1, QgsFeature 2
      # 6 elemento = feature della linea di leader (può essere None); QgsFeature
      """
      self.dimType = QadDimTypeEnum.LINEAR
      
      # punti di quotatura
      dimPt1Feature = self.getDimPointFeature(dimPt1, True, \
                                              canvas.mapRenderer().destinationCrs()) # True = primo punto di quotatura
      dimPt2Feature = self.getDimPointFeature(dimPt2, False, \
                                              canvas.mapRenderer().destinationCrs()) # False = secondo punto di quotatura   
               
      # linea di quota
      dimLine1 = self.getDimLine(dimPt1, dimPt2, linePosPt, preferredAlignment, dimLineRotation)
      dimLine2 = None
               
      # testo e blocchi
      if measure is None:
         textValue = qad_utils.getDistance(dimLine1[0], dimLine1[1])
      else:
         textValue = unicode(measure)
         
      textFeature = self.getTextFeature(textValue)      
      textWidth, textHeight = qad_label.calculateLabelSize(self.getTextualLayer(), textFeature, canvas)
               
      # creo un rettangolo intorno al testo con un buffer = self.textOffsetDist
      textWidthOffset  = textWidth + self.textOffsetDist * 2
      textHeightOffset = textHeight + self.textOffsetDist * 2

      # Restituisce una lista di 4 elementi:
      # - il primo elemento é una lista con il punto di inserimento del testo della quota e la sua rotazione
      # - il secondo elemento é una lista con flag che indica il tipo della linea sulla quale é stato messo il testo; vedi QadDimComponentEnum
      #                       e una lista di linee "leader" nel caso il testo sia all'esterno della quota
      # - il terzo elemento é la rotazione del primo blocco delle frecce; può essere None se non visibile
      # - il quarto elemento é la rotazione del secondo blocco delle frecce; può essere None se non visibile      
      dummy1, dummy2, block1Rot, block2Rot = self.getLinearTextAndBlocksPosition(dimPt1, dimPt2, \
                                                                                 dimLine1[0], dimLine1[1], \
                                                                                 textWidthOffset, textHeightOffset)
               
      textOffsetRectInsPt = dummy1[0]
      textRot             = dummy1[1]
      textLinearDimComponentOn = dummy2[0]
      txtLeaderLines           = dummy2[1]

      # trovo il vero punto di inserimento del testo tenendo conto del buffer intorno      
      textInsPt = qad_utils.getPolarPointByPtAngle(textOffsetRectInsPt, textRot, self.textOffsetDist)
      textInsPt = qad_utils.getPolarPointByPtAngle(textInsPt, textRot + math.pi / 2, self.textOffsetDist)
               
      # testo
      textGeom = QgsGeometry.fromPoint(textInsPt)
      textFeature = self.getTextFeature(textValue, textInsPt, textRot, canvas.mapRenderer().destinationCrs())      
               
      # blocchi frecce
      block1Feature = self.getSymbolFeature(dimLine1[0], block1Rot, True, textLinearDimComponentOn, canvas.mapRenderer().destinationCrs()) # True = primo punto di quotatura
      block2Feature = self.getSymbolFeature(dimLine1[1], block2Rot, False, textLinearDimComponentOn, canvas.mapRenderer().destinationCrs()) # False = secondo punto di quotatura   
               
      extLine1 = self.getExtLine(dimPt1, dimLine1[0])
      extLine2 = self.getExtLine(dimPt2, dimLine1[1])
      
      # creo un rettangolo intorno al testo con un offset
      textOffsetRect = self.textRectToQadLinearObjectList(textOffsetRectInsPt, textWidthOffset, textHeightOffset, textRot)
               
      if textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1: # linea di quota ("Dimension line")
         dimLine1, dimLine2 = self.adjustLineAccordingTextRect(textOffsetRect, dimLine1[0], dimLine1[1], QadDimComponentEnum.DIM_LINE1)
      elif textLinearDimComponentOn == QadDimComponentEnum.EXT_LINE1: # prima linea di estensione ("Extension line 1")
         if extLine1 is not None:
            extLineRot = qad_utils.getAngleBy2Pts(dimPt1, dimLine1[0])
            extLine1 = self.getExtLine(dimPt1, qad_utils.getPolarPointByPtAngle(dimLine1[0], extLineRot, textWidth + self.textOffsetDist))
            # passo prima il secondo punto e poi il primo perché getExtLine restituisce una linea dalla linea di quota verso il punto di quotatura       
            extLine1, dummy = self.adjustLineAccordingTextRect(textOffsetRect, extLine1[1], extLine1[0], QadDimComponentEnum.EXT_LINE1)
      elif textLinearDimComponentOn == QadDimComponentEnum.EXT_LINE2: # seconda linea di estensione ("Extension line 2")
         if extLine2 is not None:
            extLineRot = qad_utils.getAngleBy2Pts(dimPt2, dimLine1[1])
            extLine2 = self.getExtLine(dimPt2, qad_utils.getPolarPointByPtAngle(dimLine1[1], extLineRot, textWidth + self.textOffsetDist))            
            # passo prima il secondo punto e poi il primo perché getExtLine restituisce una linea dalla linea di quota verso il punto di quotatura       
            extLine2, dummy = self.adjustLineAccordingTextRect(textOffsetRect, extLine2[1], extLine2[0], QadDimComponentEnum.EXT_LINE2)
      elif textLinearDimComponentOn == QadDimComponentEnum.LEADER_LINE: # linea porta quota usata quando il testo é fuori dalla quota ("Leader")
         lastLine = txtLeaderLines[-1]
         lastLine, dummy = self.adjustLineAccordingTextRect(textOffsetRect, lastLine[0], lastLine[1], QadDimComponentEnum.LEADER_LINE)
         del txtLeaderLines[-1] # sostituisco l'ultimo elemento
         txtLeaderLines.append(lastLine)
               
      # linee di quota
      dimLine1Feature = self.getDimLineFeature(dimLine1, True, textLinearDimComponentOn, canvas.mapRenderer().destinationCrs()) # True = prima linea di quota
      dimLine2Feature = self.getDimLineFeature(dimLine2, False, textLinearDimComponentOn, canvas.mapRenderer().destinationCrs()) # False = seconda linea di quota
   
      # linee di estensione
      extLine1Feature = self.getExtLineFeature(extLine1, True, canvas.mapRenderer().destinationCrs())  # True = prima linea di estensione
      extLine2Feature = self.getExtLineFeature(extLine2, False, canvas.mapRenderer().destinationCrs()) # False = seconda linea di estensione
   
      # linea di leader
      txtLeaderLineFeature = self.getLeaderFeature(txtLeaderLines, canvas.mapRenderer().destinationCrs())

      dimEntity = QadDimEntity()
      dimEntity.dimStyle = self
      # features testuali
      dimEntity.textualFeature = textFeature
      # features lineari
      if dimLine1Feature is not None:
         dimEntity.linearFeatures.append(dimLine1Feature)
      if dimLine2Feature is not None:
         dimEntity.linearFeatures.append(dimLine2Feature)
      if extLine1Feature is not None:
         dimEntity.linearFeatures.append(extLine1Feature)
      if extLine2Feature is not None:
         dimEntity.linearFeatures.append(extLine2Feature)
      if txtLeaderLineFeature is not None:
         dimEntity.linearFeatures.append(txtLeaderLineFeature)
      # features puntuali
      dimEntity.symbolFeatures.extend([dimPt1Feature, dimPt2Feature])
      if block1Feature is not None:
         dimEntity.symbolFeatures.append(block1Feature)
      if block2Feature is not None:
         dimEntity.symbolFeatures.append(block2Feature)
      
      return dimEntity, QgsGeometry.fromPolygon([textOffsetRect.asPolyline()])


   #============================================================================
   # addLinearDimToLayers
   #============================================================================
   def addLinearDimToLayers(self, plugIn, dimPt1, dimPt2, linePosPt, measure = None, \
                            preferredAlignment = QadDimStyleAlignmentEnum.HORIZONTAL, \
                            dimLineRotation = 0.0):
      """
      Aggiunge ai layers le features che compongono una quota lineare.
      """
      self.dimType = QadDimTypeEnum.LINEAR
      
      dimEntity, textOffsetRect = self.getLinearDimFeatures(plugIn.canvas, \
                                                            dimPt1, \
                                                            dimPt2, \
                                                            linePosPt, \
                                                            measure, \
                                                            preferredAlignment, \
                                                            dimLineRotation)
      
      plugIn.beginEditCommand("Linear dimension added", [self.getSymbolLayer(), self.getLinearLayer(), self.getTextualLayer()])
      
      # prima di tutto inserisco il testo di quota
      # plugIn, layer, feature, coordTransform, refresh, check_validity
      if qad_layer.addFeatureToLayer(plugIn, self.getTextualLayer(), dimEntity.textualFeature, None, False, False) == False:
         plugIn.destroyEditCommand()
         return False
      dimId = dimEntity.textualFeature.id()
      if self.setDimId(dimId, [dimEntity.textualFeature], False) == True: # setto id
         # plugIn, layer, feature, refresh, check_validity
         if qad_layer.updateFeatureToLayer(plugIn, self.getTextualLayer(), dimEntity.textualFeature, False, False) == False:
            plugIn.destroyEditCommand()
            return False
         
      # features puntuali
      self.setDimId(dimId, dimEntity.symbolFeatures, True) # setto id_parent
      # plugIn, layer, features, coordTransform, refresh, check_validity
      if qad_layer.addFeaturesToLayer(plugIn, self.getSymbolLayer(), dimEntity.symbolFeatures, None, False, False) == False:
         plugIn.destroyEditCommand()
         return False
      
      # features lineari
      self.setDimId(dimId, dimEntity.linearFeatures, True) # setto id_parent
      # plugIn, layer, features, coordTransform, refresh, check_validity
      if qad_layer.addFeaturesToLayer(plugIn, self.getLinearLayer(), dimEntity.linearFeatures, None, False, False) == False:
         plugIn.destroyEditCommand()
         return False

      plugIn.endEditCommand()
      
      return True


   #============================================================================
   # FUNZIONI PER LA QUOTATURA LINEARE - FINE
   # FUNZIONI PER LA QUOTATURA ALLINEATA - INIZIO
   #============================================================================
   

   #============================================================================
   # getAlignedDimFeatures
   #============================================================================
   def getAlignedDimFeatures(self, canvas, dimPt1, dimPt2, linePosPt, measure = None):
      """
      dimPt1 = primo punto da quotare (in unita di mappa)
      dimPt2 = secondo punto da quotare (in unita di mappa)
      linePosPt = punto per indicare dove deve essere posizionata la linea di quota (in unita di mappa)
      measure = indica se la misura é predeterminata oppure (se = None) deve essere calcolata
      
      # quota lineare con una linea di quota orizzontale o verticale
      # ritorna una lista di elementi che descrivono la geometria della quota:
      # 1 lista = feature del primo e del secondo punto di quota; QgsFeature 1, QgsFeature 2
      # 2 lista = feature della prima e della seconda linea di quota (quest'ultima può essere None); QgsFeature 1, QgsFeature 2
      # 3 lista = feature del punto del testo di quota e geometria del rettangolo di occupazione; QgsFeature, QgsGeometry
      # 4 lista = feature del primo e del secondo simbolo per la linea di quota (possono essere None); QgsFeature 1, QgsFeature 2
      # 5 lista = feature della prima e della seconda linea di estensione (possono essere None); QgsFeature 1, QgsFeature 2
      # 6 elemento = feature della linea di leader (può essere None); QgsFeature
      """
      self.dimType = QadDimTypeEnum.ALIGNED
      
      # punti di quotatura
      dimPt1Feature = self.getDimPointFeature(dimPt1, True, \
                                              canvas.mapRenderer().destinationCrs()) # True = primo punto di quotatura
      dimPt2Feature = self.getDimPointFeature(dimPt2, False, \
                                              canvas.mapRenderer().destinationCrs()) # False = secondo punto di quotatura   
               
      # linea di quota
      dimLine1 = self.getDimLine(dimPt1, dimPt2, linePosPt)
      dimLine2 = None
      
      # testo e blocchi
      if measure is None:
         textValue = qad_utils.getDistance(dimLine1[0], dimLine1[1])
      else:
         textValue = unicode(measure)
         
      textFeature = self.getTextFeature(textValue)      
      textWidth, textHeight = qad_label.calculateLabelSize(self.getTextualLayer(), textFeature, canvas)

      # creo un rettangolo intorno al testo con un buffer = self.textOffsetDist
      textWidthOffset  = textWidth + self.textOffsetDist * 2
      textHeightOffset = textHeight + self.textOffsetDist * 2

      # Restituisce una lista di 4 elementi:
      # - il primo elemento é una lista con il punto di inserimento del testo della quota e la sua rotazione
      # - il secondo elemento é una lista con flag che indica il tipo della linea sulla quale é stato messo il testo; vedi QadDimComponentEnum
      #                       e una lista di linee "leader" nel caso il testo sia all'esterno della quota
      # - il terzo elemento é la rotazione del primo blocco delle frecce; può essere None se non visibile
      # - il quarto elemento é la rotazione del secondo blocco delle frecce; può essere None se non visibile      
      dummy1, dummy2, block1Rot, block2Rot = self.getLinearTextAndBlocksPosition(dimPt1, dimPt2, \
                                                                                 dimLine1[0], dimLine1[1], \
                                                                                 textWidthOffset, textHeightOffset)
      textOffsetRectInsPt = dummy1[0]
      textRot             = dummy1[1]
      textLinearDimComponentOn = dummy2[0]
      txtLeaderLines           = dummy2[1]

      # trovo il vero punto di inserimento del testo tenendo conto del buffer intorno      
      textInsPt = qad_utils.getPolarPointByPtAngle(textOffsetRectInsPt, textRot, self.textOffsetDist)
      textInsPt = qad_utils.getPolarPointByPtAngle(textInsPt, textRot + math.pi / 2, self.textOffsetDist)

      # testo
      textGeom = QgsGeometry.fromPoint(textInsPt)
      textFeature = self.getTextFeature(textValue, textInsPt, textRot, canvas.mapRenderer().destinationCrs())      

      # blocchi frecce
      block1Feature = self.getSymbolFeature(dimLine1[0], block1Rot, True, textLinearDimComponentOn, canvas.mapRenderer().destinationCrs()) # True = primo punto di quotatura
      block2Feature = self.getSymbolFeature(dimLine1[1], block2Rot, False, textLinearDimComponentOn, canvas.mapRenderer().destinationCrs()) # False = secondo punto di quotatura   
            
      extLine1 = self.getExtLine(dimPt1, dimLine1[0])
      extLine2 = self.getExtLine(dimPt2, dimLine1[1])
      
      # creo un rettangolo intorno al testo con un offset
      textOffsetRect = self.textRectToQadLinearObjectList(textOffsetRectInsPt, textWidthOffset, textHeightOffset, textRot)
      
      if textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1: # linea di quota ("Dimension line")
         dimLine1, dimLine2 = self.adjustLineAccordingTextRect(textOffsetRect, dimLine1[0], dimLine1[1], QadDimComponentEnum.DIM_LINE1)
      elif textLinearDimComponentOn == QadDimComponentEnum.EXT_LINE1: # prima linea di estensione ("Extension line 1")
         if extLine1 is not None:
            extLineRot = qad_utils.getAngleBy2Pts(dimPt1, dimLine1[0])
            extLine1 = self.getExtLine(dimPt1, qad_utils.getPolarPointByPtAngle(dimLine1[0], extLineRot, textWidth + self.textOffsetDist))
            # passo prima il secondo punto e poi il primo perché getExtLine restituisce una linea dalla linea di quota verso il punto di quotatura       
            extLine1, dummy = self.adjustLineAccordingTextRect(textOffsetRect, extLine1[1], extLine1[0], QadDimComponentEnum.EXT_LINE1)
      elif textLinearDimComponentOn == QadDimComponentEnum.EXT_LINE2: # seconda linea di estensione ("Extension line 2")
         if extLine2 is not None:
            extLineRot = qad_utils.getAngleBy2Pts(dimPt2, dimLine1[1])
            extLine2 = self.getExtLine(dimPt2, qad_utils.getPolarPointByPtAngle(dimLine1[1], extLineRot, textWidth + self.textOffsetDist))            
            # passo prima il secondo punto e poi il primo perché getExtLine restituisce una linea dalla linea di quota verso il punto di quotatura       
            extLine2, dummy = self.adjustLineAccordingTextRect(textOffsetRect, extLine2[1], extLine2[0], QadDimComponentEnum.EXT_LINE2)
      elif textLinearDimComponentOn == QadDimComponentEnum.LEADER_LINE: # linea porta quota usata quando il testo é fuori dalla quota ("Leader")
         lastLine = txtLeaderLines[-1]
         lastLine, dummy = self.adjustLineAccordingTextRect(textOffsetRect, lastLine[0], lastLine[1], QadDimComponentEnum.LEADER_LINE)
         del txtLeaderLines[-1] # sostituisco l'ultimo elemento
         txtLeaderLines.append(lastLine)
      
      # linee di quota
      dimLine1Feature = self.getDimLineFeature(dimLine1, True, textLinearDimComponentOn, canvas.mapRenderer().destinationCrs()) # True = prima linea di quota
      dimLine2Feature = self.getDimLineFeature(dimLine2, False, textLinearDimComponentOn, canvas.mapRenderer().destinationCrs()) # False = seconda linea di quota

      # linee di estensione
      extLine1Feature = self.getExtLineFeature(extLine1, True, canvas.mapRenderer().destinationCrs())  # True = prima linea di estensione
      extLine2Feature = self.getExtLineFeature(extLine2, False, canvas.mapRenderer().destinationCrs()) # False = seconda linea di estensione

      # linea di leader
      txtLeaderLineFeature = self.getLeaderFeature(txtLeaderLines, canvas.mapRenderer().destinationCrs())
   
      dimEntity = QadDimEntity()
      dimEntity.dimStyle = self
      # features testuali
      dimEntity.textualFeature = textFeature
      # features lineari
      if dimLine1Feature is not None:
         dimEntity.linearFeatures.append(dimLine1Feature)
      if dimLine2Feature is not None:
         dimEntity.linearFeatures.append(dimLine2Feature)
      if extLine1Feature is not None:
         dimEntity.linearFeatures.append(extLine1Feature)
      if extLine2Feature is not None:
         dimEntity.linearFeatures.append(extLine2Feature)
      if txtLeaderLineFeature is not None:
         dimEntity.linearFeatures.append(txtLeaderLineFeature)
      # features puntuali
      dimEntity.symbolFeatures.extend([dimPt1Feature, dimPt2Feature])
      if block1Feature is not None:
         dimEntity.symbolFeatures.append(block1Feature)
      if block2Feature is not None:
         dimEntity.symbolFeatures.append(block2Feature)
      
      return dimEntity, QgsGeometry.fromPolygon([textOffsetRect.asPolyline()])


   #============================================================================
   # addAlignedDimToLayers
   #============================================================================
   def addAlignedDimToLayers(self, plugIn, dimPt1, dimPt2, linePosPt, measure = None, \
                            preferredAlignment = QadDimStyleAlignmentEnum.HORIZONTAL, \
                            dimLineRotation = 0.0):
      """
      dimPt1 = primo punto da quotare (in unita di mappa)
      dimPt2 = secondo punto da quotare (in unita di mappa)
      linePosPt = punto per indicare dove deve essere posizionata la linea di quota (in unita di mappa)
      measure = indica se la misura é predeterminata oppure (se = None) deve essere calcolata
      preferredAlignment = se lo stile di quota é lineare, indica se ci si deve allienare ai punti di quota
                           in modo orizzontale o verticale (se i punti di quota formano una linea obliqua)      
      dimLineRotation = angolo della linea di quotatura (default = 0) 

      Aggiunge ai layers le features che compongono una quota allineata.
      """
      self.dimType = QadDimTypeEnum.ALIGNED
      
      dimEntity, textOffsetRect = self.getAlignedDimFeatures(plugIn.canvas, \
                                                             dimPt1, \
                                                             dimPt2, \
                                                             linePosPt, \
                                                             measure)
      
      plugIn.beginEditCommand("Aligned dimension added", [self.getSymbolLayer(), self.getLinearLayer(), self.getTextualLayer()])

      # prima di tutto inserisco il testo di quota
      # plugIn, layer, feature, coordTransform, refresh, check_validity
      if qad_layer.addFeatureToLayer(plugIn, self.getTextualLayer(), dimEntity.textualFeature, None, False, False) == False:
         plugIn.destroyEditCommand()
         return False
      dimId = dimEntity.textualFeature.id()
      if self.setDimId(dimId, [dimEntity.textualFeature], False) == True: # setto id
         # plugIn, layer, feature, refresh, check_validity
         if qad_layer.updateFeatureToLayer(plugIn, self.getTextualLayer(), dimEntity.textualFeature, False, False) == False:
            plugIn.destroyEditCommand()
            return False
         
      # features puntuali
      self.setDimId(dimId, dimEntity.symbolFeatures, True) # setto id_parent
      # plugIn, layer, features, coordTransform, refresh, check_validity
      if qad_layer.addFeaturesToLayer(plugIn, self.getSymbolLayer(), dimEntity.symbolFeatures, None, False, False) == False:
         plugIn.destroyEditCommand()
         return False
      
      # features lineari
      self.setDimId(dimId, dimEntity.linearFeatures, True) # setto id_parent
      # plugIn, layer, features, coordTransform, refresh, check_validity
      if qad_layer.addFeaturesToLayer(plugIn, self.getLinearLayer(), dimEntity.linearFeatures, None, False, False) == False:
         plugIn.destroyEditCommand()
         return False

      plugIn.endEditCommand()
      
      return True


#===============================================================================
# QadDimStylesClass list of dimension styles
#===============================================================================
class QadDimStylesClass():
   
   def __init__(self, dimStyleList = None):
      if dimStyleList is None:
         self.dimStyleList = []
      else:
         self.set(dimStyleList)


   def __del__(self):
      if dimStyleList is None:
         del self.dimStyleList[:]

         
   def isEmpty(self):
      return True if self.count() == 0 else False

         
   def count(self):
      return len(self.dimStyleList)
   

   def clear(self):
      del self.dimStyleList[:] 


   def findDimStyle(self, dimStyleName):
      """
      La funzione, dato un nome di stile di quotatura, lo cerca nella lista e,
      in caso di successo, restituisce lo stile di quotatura.
      """
      for dimStyle in self.dimStyleList:
         if dimStyle.name == dimStyleName:
            return dimStyle
      return None


   def addDimStyle(self, dimStyle, toFile = False, filePath = ""):
      d = self.findDimStyle(dimStyle)
      if d is None: 
         self.dimStyleList.append(QadDimStyle(dimStyle))
         if toFile:
            if dimStyle.save(filePath, False) == False: # senza sovrascrivere file
               return False
         return True
            
      return False     
         

   #============================================================================
   # removeDimStyle
   #============================================================================
   def removeDimStyle(self, dimStyleName, toFile = False):
      i = 0
      for dimStyle in self.dimStyleList:
         if dimStyle.name == dimStyleName:
            del self.dimStyleList[i]
            if toFile:
               dimStyle.remove()
            return True
         else:
            i = i + 1
            
      return False
      
      
   #============================================================================
   # renameDimStyle
   #============================================================================
   def renameDimStyle(self, dimStyleName, newDimStyleName):
      if dimStyleName == newDimStyleName: # nome uguale
         return True

      if self.findDimStyle(newDimStyleName) is not None:
         return False
      dimStyle = self.findDimStyle(dimStyleName)
      if dimStyle is None:
         return False
      return dimStyle.rename(newDimStyleName)

      
   #============================================================================
   # load
   #============================================================================
   def load(self, dir = None, append = False):
      """
      Carica le impostazioni di tutti gli stili di quotatura presenti nella directory indicata.
      se dir = None se esiste un progetto caricato il percorso è quello del progetto altrimenti + il percorso locale di qad
      """
      if dir is None:
         if append == False:
            self.clear()
        
         # se esiste un progetto caricato il percorso è quello del progetto
         prjFileInfo = QFileInfo(QgsProject.instance().fileName())
         path = prjFileInfo.absolutePath()
         if len(path) > 0:
            path += "/;"
         path += QgsApplication.qgisSettingsDirPath() + "python/plugins/qad/"
        
         # lista di directory separate da ";"
         dirList = path.strip().split(";")
         for _dir in dirList:
            self.load(_dir, True) # in append
      else:
         _dir = QDir.cleanPath(dir)
         if _dir == "":
            return False
            
         if _dir.endswith("/") == False:
            _dir = _dir + "/"
            
         if not os.path.exists(_dir):
            return False
         
         if append == False:
            self.clear()
         dimStyle = QadDimStyle()
               
         fileNames = os.listdir(_dir)
         for fileName in fileNames:
            if fileName.endswith(".dim"):
               path = _dir + fileName            
               if dimStyle.load(path) == True:
                  if self.findDimStyle(dimStyle.name) is None:              
                     self.addDimStyle(dimStyle)
               
      return True


   #============================================================================
   # getDimIdByEntity
   #============================================================================
   def getDimIdByEntity(self, entity):
      """
      La funzione, data un'entità, verifica se fa parte di uno stile di quotatura della lista e,
      in caso di successo, restituisce lo stile di quotatura e il codice della quotatura altrimenti None, None.
      """
      for dimStyle in self.dimStyleList:
         dimId = dimStyle.getDimIdByEntity(entity)
         if dimId is not None:
            return dimStyle, dimId
      return None, None


   #============================================================================
   # getDimEntity
   #============================================================================
   def getDimEntity(self, layer, fid = None):
      """
         la funzione può essere richiamata in 2 modi:
         con un solo parametro di tipo QadEntity
         con due parametri, il primo QgsVectorLayer e il secondo l'id della feature
      """
      # verifico se l'entità appartiene ad uno stile di quotatura
      if type(layer) == QgsVectorLayer:
         entity = QadEntity()
         entity.set(layer, fid)
         dimStyle, dimId = self.getDimIdByEntity(entity)
      else: # il parametro layer puo essere un oggetto QadEntity
         dimStyle, dimId = self.getDimIdByEntity(layer)
      
      if (dimStyle is None) or (dimId is None):
         return None
         
      dimEntity = QadDimEntity()
      if dimEntity.initByDimId(dimStyle, dimId) == False:
         return None

      return dimEntity


   #============================================================================
   # getDimListByLayer
   #============================================================================
   def getDimListByLayer(self, layer):
      """
      La funzione, dato un layer, verifica se fa parte di uno o più stili di quotatura della lista e,
      in caso di successo, restituisce la lista degli stili di quotatura di appartenenza.
      """
      result = []
      for dimStyle in self.dimStyleList:
         if dimStyle.isDimLayer(layer):
            if dimStyle not in result:
               result.append(dimStyle)

      return result


   #============================================================================
   # addAllDimComponentsToEntitySet
   #============================================================================
   def addAllDimComponentsToEntitySet(self, entitySet, onlyEditableLayers):
      """
      La funzione verifica se le entità che fanno parte di un entitySet sono anche parte di quotatura e,
      in caso affermativo, aggiunge tutti i componenti della quotatura all'entitySet.
      """
      elaboratedDimEntitySet = QadEntitySet() # lista delle entità di quota elaborate
      entity = QadEntity()
      for layerEntitySet in entitySet.layerEntitySetList:           
         # verifico se il layer appartiene ad uno o più stili di quotatura
         dimStyleList = self.getDimListByLayer(layerEntitySet.layer)
         for dimStyle in dimStyleList: # per tutti gli stili di quotatura
            if dimStyle is not None:
               remove = False
               if onlyEditableLayers == True:
                  # se anche un solo layer non é modificabile 
                  if dimStyle.getTextualLayer().isEditable() == False or \
                     dimStyle.getSymbolLayer().isEditable() == False or \
                     dimStyle.getLinearLayer().isEditable() == False:
                     remove = True
               features = layerEntitySet.getFeatureCollection()
               for feature in features:
                  entity.set(layerEntitySet.layer, feature.id())
                  if not elaboratedDimEntitySet.containsEntity(entity):                  
                     dimId = dimStyle.getDimIdByEntity(entity)
                     if dimId is not None:
                        dimEntitySet = dimStyle.getEntitySet(dimId)
                        if remove == False:
                           entitySet.unite(dimEntitySet)
                        else:
                           entitySet.subtract(dimEntitySet)
                        
                        elaboratedDimEntitySet.unite(entitySet)


   #============================================================================
   # removeAllDimLayersFromEntitySet
   #============================================================================
   def removeAllDimLayersFromEntitySet(self, entitySet):
      """
      La funzione rimuove tutte le entità che fanno parte di quotature dall'entitySet.
      """
      for dimStyle in self.dimStyleList:
         entitySet.removeLayerEntitySet(dimStyle.getTextualLayer())
         entitySet.removeLayerEntitySet(dimStyle.getSymbolLayer())
         entitySet.removeLayerEntitySet(dimStyle.getLinearLayer())


#===============================================================================
# QadDimEntity dimension entity class
#===============================================================================
class QadDimEntity():

   #============================================================================
   # __init__
   #============================================================================
   def __init__(self, dimEntity = None):
      if dimEntity is not None:
         self.set(dimEntity)
      else:
         self.dimStyle = None
         self.textualFeature = None
         self.linearFeatures = []
         self.symbolFeatures = []

         
   def whatIs(self):
      return "DIMENTITY"


   def isInitialized(self):
      if (self.dimStyle is None) or (self.textualFeature is None):
         return False
      else:
         return True


   def __eq__(self, dimEntity):
      """self == other"""
      if self.isInitialized() == False or dimEntity.isInitialized() == False :
         return False

      if self.getTextualLayer() == dimEntity.getTextualLayer() and self.getDimId() == dimEntity.getDimId():
         return True
      else:
         return False    


   #============================================================================
   # getTextualLayer
   #============================================================================
   def getTextualLayer(self):
      if self.dimStyle is None:
         return None
      return self.dimStyle.getTextualLayer()
         
                  
   #============================================================================
   # getLinearLayer
   #============================================================================
   def getLinearLayer(self):
      if self.dimStyle is None:
         return None
      return self.dimStyle.getLinearLayer()
         
                  
   #============================================================================
   # getSymbolLayer
   #============================================================================
   def getSymbolLayer(self):
      if self.dimStyle is None:
         return None
      return self.dimStyle.getSymbolLayer()
         
      
   #============================================================================
   # set
   #============================================================================
   def set(self, dimEntity):
      self.dimStyle = QadDimStyle(dimEntity.dimStyle)
      
      self.textualFeature = QgsFeature(dimEntity.textualFeature)

      del self.linearFeatures[:]
      for f in dimEntity.linearFeatures:
         self.linearFeatures.append(QgsFeature(f))

      del self.symbolFeatures[:]
      for f in dimEntity.symbolFeatures:
         self.symbolFeatures.append(QgsFeature(f))


   #============================================================================
   # getLinearGeometryCollection
   #============================================================================
   def getLinearGeometryCollection(self):
      result = []
      for f in self.linearFeatures:
         result.append(f.geometry())
      return result

         
   #============================================================================
   # getSymbolGeometryCollection
   #============================================================================
   def getSymbolGeometryCollection(self):
      result = []
      for f in self.symbolFeatures:
         result.append(f.geometry())
      return result


   #============================================================================
   # getDimId
   #============================================================================
   def getDimId(self):
      """
      La funzione restituisce il codice della quotatura altrimenti None.
      """
      try:
         return self.textualFeature.attribute(self.idFieldName)
      except:
         return None      


   def recodeDimIdToFeature(self, newDimId):      
      try:
         # imposto il codice della quota
         self.textualFeature.setAttribute(self.dimStyle.idFieldName, newDimId)
         for f in self.linearFeatures:
            f.setAttribute(self.dimStyle.idParentFieldName, newDimId)
         for f in self.symbolFeatures:
            f.setAttribute(self.dimStyle.idParentFieldName, newDimId)
      except:
         return False

      return True
   
   
   #============================================================================
   # addToLayers
   #============================================================================
   def addToLayers(self, plugIn):
      # prima di tutto inserisco il testo di quota per ricodificare la quotatura
      # plugIn, layer, feature, coordTransform, refresh, check_validity
      if qad_layer.addFeatureToLayer(plugIn, self.getTextualLayer(), self.textualFeature, None, False, False) == False:
         return False
      newDimId = self.textualFeature.id()
         
      if self.recodeDimIdToFeature(newDimId) == False:
         return False

      # plugIn, layer, feature, refresh, check_validity
      if qad_layer.updateFeatureToLayer(plugIn, self.getTextualLayer(), self.textualFeature, False, False) == False:
         return False
      # plugIn, layer, features, coordTransform, refresh, check_validity
      if qad_layer.addFeaturesToLayer(plugIn, self.getLinearLayer(), self.linearFeatures, None, False, False) == False:  
         return False
      # plugIn, layer, features, coordTransform, refresh, check_validity
      if qad_layer.addFeaturesToLayer(plugIn, self.getSymbolLayer(), self.symbolFeatures, None, False, False) == False:  
         return False
      
      return True
   
   
   #============================================================================
   # deleteToLayers
   #============================================================================
   def deleteToLayers(self, plugIn):
      ids =[]

      # plugIn, layer, featureId, refresh
      if qad_layer.deleteFeatureToLayer(plugIn, self.getTextualLayer(), self.textualFeature.id(), False) == False:
         return False
      
      for f in self.linearFeatures:
         ids.append(f.id())
      # plugIn, layer, featureIds, refresh
      if qad_layer.deleteFeaturesToLayer(plugIn, self.getLinearLayer(), ids, False) == False:
         return False
      
      del ids[:]
      for f in self.symbolFeatures:
         ids.append(f.id())
      # plugIn, layer, featureIds, refresh
      if qad_layer.deleteFeaturesToLayer(plugIn, self.getSymbolLayer(), ids, False) == False:
         return False
      
      return True
      
      
   #============================================================================
   # initByEntity
   #============================================================================
   def initByEntity(self, dimStyle, entity):
      dimId = dimStyle.getDimIdByEntity(entity)
      if dimId is None:
         return False
      return self.initByDimId(dimStyle, dimId)


   #============================================================================
   # initByDimId
   #============================================================================
   def initByDimId(self, dimStyle, dimId):
      self.dimStyle = QadDimStyle(dimStyle)
      entitySet = self.dimStyle.getEntitySet(dimId)

      self.textualFeature = None
      layerEntitySet = entitySet.findLayerEntitySet(self.getTextualLayer())
      features = layerEntitySet.getFeatureCollection()
      self.textualFeature = features[0]
      
      # entità lineari
      layerEntitySet = entitySet.findLayerEntitySet(self.getLinearLayer())
      del self.linearFeatures[:] # svuoto la lista
      if layerEntitySet is not None:
         self.linearFeatures = layerEntitySet.getFeatureCollection()
      
      # entità puntuali
      layerEntitySet = entitySet.findLayerEntitySet(self.getSymbolLayer())
      del self.symbolFeatures[:] # svuoto la lista
      if layerEntitySet is not None:
         self.symbolFeatures = layerEntitySet.getFeatureCollection()
   
      return True


   #============================================================================
   # getEntitySet
   #============================================================================
   def getEntitySet(self):      
      result = QadEntitySet()
                  
      layerEntitySet = QadLayerEntitySet()
      layerEntitySet.set(self.getTextualLayer(), [self.textualFeature])
      result.addLayerEntitySet(layerEntitySet)

      layerEntitySet = QadLayerEntitySet()
      layerEntitySet.set(self.getLinearLayer(), self.linearFeatures)
      result.addLayerEntitySet(layerEntitySet)
      
      layerEntitySet = QadLayerEntitySet()
      layerEntitySet.set(self.getSymbolLayer(), self.symbolFeatures)
      result.addLayerEntitySet(layerEntitySet)
      
      return result
   

   #============================================================================
   # selectOnLayer
   #============================================================================
   def selectOnLayer(self, incremental = True):
      self.getEntitySet().selectOnLayer(incremental)
   

   #============================================================================
   # deselectOnLayer
   #============================================================================
   def deselectOnLayer(self):
      self.getEntitySet().deselectOnLayer()

   
   #============================================================================
   # getDimPts
   #============================================================================
   def getDimPts(self, destinationCrs = None):
      """
      destinationCrs = sistema di coordinate in cui verrà restituito il risultato
      """
            
      dimPt1 = None
      dimPt2 = None

      if len(self.dimStyle.componentFieldName) > 0:
         # cerco tra gli elementi puntuali
         for f in self.symbolFeatures:
            try:
               value = f.attribute(self.dimStyle.componentFieldName)
               if value == QadDimComponentEnum.DIM_PT1: # primo punto da quotare ("Dimension point 1")
                  g = f.geometry()
                  if (destinationCrs is not None) and destinationCrs != self.getSymbolLayer().crs():
                     g.transform(QgsCoordinateTransform(self.getSymbolLayer().crs(), destinationCrs)) # trasformo la geometria in map coordinate
                  
                  dimPt1 = g.asPoint()
               elif value == QadDimComponentEnum.DIM_PT2: # secondo punto da quotare ("Dimension point 2")
                  g = f.geometry()
                  if (destinationCrs is not None) and destinationCrs != self.getSymbolLayer().crs():
                     g.transform(QgsCoordinateTransform(self.getSymbolLayer().crs(), destinationCrs)) # trasformo la geometria in map coordinate
                  
                  dimPt2 = g.asPoint()
            except:
               return None, None

      return dimPt1, dimPt2      
         

   #============================================================================
   # getDimLinePosPt
   #============================================================================
   def getDimLinePosPt(self, containerGeom = None, destinationCrs = None):
      """
      Trova fra i vari punti possibili un punto che indichi dove si trova la linea di quota (in destinationCrs tipicamente = map coordinate)
      se containerGeom <> None il punto deve essere contenuto in containerGeom
      containerGeom = può essere una QgsGeometry rappresentante un poligono (in destinationCrs tipicamente = map coordinate) contenente i punti di geom da stirare
                      oppure una lista dei punti da stirare (in destinationCrs tipicamente = map coordinate)
      destinationCrs = sistema di coordinate in cui è espresso containerGeom e in cui verrà restituito il risultato
      """
      
      if len(self.dimStyle.componentFieldName) > 0:
         # prima cerco tra gli elementi lineari
         for f in self.linearFeatures:
            try:
               value = f.attribute(self.dimStyle.componentFieldName)
               # primo punto da quotare ("Dimension point 1") o secondo punto da quotare ("Dimension point 2")
               if value == QadDimComponentEnum.DIM_LINE1 or value == QadDimComponentEnum.DIM_LINE2:
                  g = f.geometry()

                  if (destinationCrs is not None) and destinationCrs != self.getSymbolLayer().crs():
                     g.transform(QgsCoordinateTransform(self.getLinearLayer().crs(), destinationCrs)) # trasformo la geometria in map coordinate

                  pts = g.asPolyline()
                  if containerGeom is not None: # verifico che il punto iniziale sia interno a containerGeom
                     if type(containerGeom) == QgsGeometry: # geometria   
                        if containerGeom.contains(pts[0]) == True:
                           return pts[0]
                        else:
                           # verifico che il punto finale sia interno a containerGeom
                           if containerGeom.contains(pts[-1]) == True:
                              return pts[-1]
                     elif type(containerGeom) == list: # lista di punti
                        for containerPt in containerGeom:
                           if ptNear(containerPt, pts[0]): # se i punti sono sufficientemente vicini
                              return pts[0]
                           else:
                              # verifico il punto finale
                              if ptNear(containerPt,pts[-1]):
                                 return pts[-1]
                  else:
                     return pts[0] # punto iniziale
            except:
               return None
            
         # poi cerco tra gli elementi puntuali
         for f in self.symbolFeatures:
            try:
               value = f.attribute(self.dimStyle.componentFieldName)
               # primo blocco della freccia ("Block 1") o secondo blocco della freccia ("Block 2")
               if value == QadDimComponentEnum.BLOCK1 or value == QadDimComponentEnum.BLOCK2:
                  g = f.geometry()

                  if (destinationCrs is not None) and destinationCrs != self.getSymbolLayer().crs():
                     g.transform(QgsCoordinateTransform(self.getSymbolLayer().crs(), destinationCrs)) # trasformo la geometria in map coordinate
                  
                  dimLinePosPt = g.asPoint()
                  if containerGeom is not None: # verifico che il punto sia interno a containerGeom
                     if type(containerGeom) == QgsGeometry: # geometria   
                        if containerGeom.contains(dimLinePosPt) == True:
                           return dimLinePosPt
                     elif type(containerGeom) == list: # lista di punti
                        for containerPt in containerGeom:
                           if ptNear(containerPt, dimLinePosPt): # se i punti sono sufficientemente vicini
                              return dimLinePosPt
                  else:
                     return dimLinePosPt
            except:
               return None

      return None


   #============================================================================
   # getDimLinearAlignment
   #============================================================================
   def getDimLinearAlignment(self):
      dimLinearAlignment = None
      dimLineRotation = None
      Pts = []
   
      if len(self.dimStyle.componentFieldName) > 0:
         # prima cerco tra gli elementi lineari
         for f in self.linearFeatures:
            try:
               value = f.attribute(self.dimStyle.componentFieldName)
               if value == QadDimComponentEnum.DIM_LINE1: # primo punto da quotare ("Dimension point 1")
                  Pts = f.geometry().asPolyline()
                  break
               elif value == QadDimComponentEnum.DIM_LINE2: # secondo punto da quotare ("Dimension point 2")
                  Pts = f.geometry().asPolyline()
                  break
            except:
               return None, None

         if Pts is None:
            # poi cerco tra gli elementi puntuali
            for f in self.symbolFeatures:
               try:
                  value = f.attribute(self.dimStyle.componentFieldName)
                  if value == QadDimComponentEnum.BLOCK1: # primo blocco della freccia ("Block 1")
                     Pts.append(f.geometry().asPoint())
                  elif value == QadDimComponentEnum.BLOCK2: # secondo blocco della freccia ("Block 1")
                     Pts.append(f.geometry().asPoint())
               except:
                  return None, None
      
      if len(Pts) > 1: # almeno 2 punti     
         if qad_utils.doubleNear(Pts[0].x(), Pts[-1].x()): # linea verticale (stessa x)
            dimLinearAlignment = QadDimStyleAlignmentEnum.VERTICAL
            dimLineRotation = 0
         elif qad_utils.doubleNear(Pts[0].y(), Pts[-1].y()): # linea orizzontale (stessa y)
            dimLinearAlignment = QadDimStyleAlignmentEnum.HORIZONTAL
            dimLineRotation = 0
         else:
            dimLinearAlignment = QadDimStyleAlignmentEnum.HORIZONTAL
            dimLineRotation = qad_utils.getAngleBy2Pts(Pts[0], Pts[-1])
            
      
      return dimLinearAlignment, dimLineRotation


   #============================================================================
   # getTextRot
   #============================================================================
   def getTextRot(self):
      textRot = None
   
      if len(self.dimStyle.rotFieldName) > 0:
         try:
            textRot = self.textualFeature.attribute(self.dimStyle.rotFieldName)
         except:
            return None

      return qad_utils.toRadians(textRot)


   #============================================================================
   # getTextValue
   #============================================================================
   def getTextValue(self):
      textValue = None

      # se il testo dipende da un solo campo 
      labelFieldNames = qad_label.get_labelFieldNames(self.dimStyle.getTextualLayer())
      if len(labelFieldNames) == 1 and len(labelFieldNames[0]) > 0:
         try:
            textValue = self.textualFeature.attribute(labelFieldNames[0])
         except:
            return None

      return textValue


   #============================================================================
   # getTextPt
   #============================================================================
   def getTextPt(self, destinationCrs = None):
      # destinationCrs = sistema di coordinate in cui verrà restituito il risultato
      g = self.textualFeature.geometry()
      if (destinationCrs is not None) and destinationCrs != self.getTextualLayer().crs():
         g.transform(QgsCoordinateTransform(self.getTextualLayer().crs(), destinationCrs)) # trasformo la geometria in map coordinate
      
      return g.asPoint()


   #============================================================================
   # isCalculatedText
   #============================================================================
   def isCalculatedText(self):
      measure = self.getTextValue()
      
      if self.dimStyle.dimType == QadDimTypeEnum.ALIGNED: # quota lineare allineata ai punti di origine delle linee di estensione
         dimPt1, dimPt2 = self.getDimPts()     
         return measure == self.dimStyle.getFormattedText(qad_utils.getDistance(dimPt1, dimPt2))
      elif self.dimStyle.dimType == QadDimTypeEnum.LINEAR: # quota lineare con una linea di quota orizzontale o verticale
         dimPt1, dimPt2 = self.getDimPts()
         linePosPt = self.getDimLinePosPt()
         preferredAlignment, dimLineRotation = self.getDimLinearAlignment()
 
         dimLine = self.dimStyle.getDimLine(dimPt1, dimPt2, linePosPt, preferredAlignment, dimLineRotation)
         return measure == self.dimStyle.getFormattedText(qad_utils.getDistance(dimLine[0], dimLine[1]))

      return True


   #============================================================================
   # move
   #============================================================================
   def move(self, offSetX, offSetY):
      # offSetX = spostamento X in map coordinate
      # offSetY = spostamento Y in map coordinate
      destinationCrs = plugIn.canvas.mapRenderer().destinationCrs()
      
      g = self.textualFeature.geometry()
      
      if (destinationCrs is not None) and destinationCrs != self.getTextualLayer().crs():
         g.transform(QgsCoordinateTransform(self.getTextualLayer().crs(), destinationCrs)) # trasformo la geometria in map coordinate

      g = qad_utils.moveQgsGeometry(g, offSetX, offSetY)

      if (destinationCrs is not None) and destinationCrs != self.getTextualLayer().crs():
         g.transform(QgsCoordinateTransform(destinationCrs, self.getTextualLayer().crs())) # trasformo la geometria in layer coordinate
      
      self.textualFeature.setGeometry(g)


      for f in self.linearFeatures:
         g = f.geometry()
         
         if (destinationCrs is not None) and destinationCrs != self.getLinearLayer().crs():
            g.transform(QgsCoordinateTransform(self.getLinearLayer().crs(), destinationCrs)) # trasformo la geometria in map coordinate

         g = qad_utils.moveQgsGeometry(g, offSetX, offSetY)

         if (destinationCrs is not None) and destinationCrs != self.getLinearLayer().crs():
            g.transform(QgsCoordinateTransform(destinationCrs, self.getLinearLayer().crs())) # trasformo la geometria in layer coordinate
         
         f.setGeometry(g)
      
      for f in self.symbolFeatures:
         g = f.geometry()
         
         if (destinationCrs is not None) and destinationCrs != self.getSymbolLayer().crs():
            g.transform(QgsCoordinateTransform(self.getSymbolLayer().crs(), destinationCrs)) # trasformo la geometria in map coordinate

         g = qad_utils.moveQgsGeometry(g, offSetX, offSetY)

         if (destinationCrs is not None) and destinationCrs != self.getSymbolLayer().crs():
            g.transform(QgsCoordinateTransform(destinationCrs, self.getSymbolLayer().crs())) # trasformo la geometria in layer coordinate
         
         f.setGeometry(g)

      
   #============================================================================
   # rotate
   #============================================================================
   def rotate(self, plugIn, basePt, angle):
      # basePt = punto base espresso in map coordinate
      destinationCrs = plugIn.canvas.mapRenderer().destinationCrs()
      
      measure = self.getTextValue()
      
      if self.dimStyle.dimType == QadDimTypeEnum.ALIGNED: # quota lineare allineata ai punti di origine delle linee di estensione
         dimPt1, dimPt2 = self.getDimPts(destinationCrs)
         linePosPt = self.getDimLinePosPt(None, destinationCrs)
         if (dimPt1 is not None) and (dimPt2 is not None) and \
            (linePosPt is not None):
            dimPt1 = qad_utils.rotatePoint(dimPt1, basePt, angle)
            dimPt2 = qad_utils.rotatePoint(dimPt2, basePt, angle)              
            linePosPt = qad_utils.rotatePoint(linePosPt, basePt, angle)
                          
            dimEntity, textOffsetRect = self.dimStyle.getAlignedDimFeatures(plugIn.canvas, \
                                                                            dimPt1, \
                                                                            dimPt2, \
                                                                            linePosPt, \
                                                                            measure)
            self.set(dimEntity)
      elif self.dimStyle.dimType == QadDimTypeEnum.LINEAR: # quota lineare con una linea di quota orizzontale o verticale
         dimPt1, dimPt2 = self.getDimPts(destinationCrs)
         linePosPt = self.getDimLinePosPt(None, destinationCrs)
         preferredAlignment, dimLineRotation = self.getDimLinearAlignment()
         if (dimPt1 is not None) and (dimPt2 is not None) and \
            (linePosPt is not None) and \
            (preferredAlignment is not None) and (dimLineRotation is not None):
            textForcedRot = self.getTextRot()
            if textForcedRot is not None:
               self.dimStyle.textForcedRot = textForcedRot

            dimPt1 = qad_utils.rotatePoint(dimPt1, basePt, angle)
            dimPt2 = qad_utils.rotatePoint(dimPt2, basePt, angle)              
            linePosPt = qad_utils.rotatePoint(linePosPt, basePt, angle)              
            dimLinearAlignment, dimLineRotation = self.getDimLinearAlignment()

            if dimLinearAlignment == QadDimStyleAlignmentEnum.VERTICAL:
               dimLineRotation = math.pi / 2
            dimLinearAlignment = QadDimStyleAlignmentEnum.HORIZONTAL
            dimLineRotation = dimLineRotation + angle
            
            dimEntity, textOffsetRect = self.dimStyle.getLinearDimFeatures(plugIn.canvas, \
                                                                           dimPt1, \
                                                                           dimPt2, \
                                                                           linePosPt, \
                                                                           measure, \
                                                                           dimLinearAlignment, \
                                                                           dimLineRotation)
            self.set(dimEntity)


   #============================================================================
   # scale
   #============================================================================
   def scale(self, plugIn, basePt, scale):
      # basePt = punto base espresso in map coordinate
      destinationCrs = plugIn.canvas.mapRenderer().destinationCrs()

      measure = None if self.isCalculatedText() else self.getTextValue()
      
      if self.dimStyle.dimType == QadDimTypeEnum.ALIGNED: # quota lineare allineata ai punti di origine delle linee di estensione
         dimPt1, dimPt2 = self.getDimPts(destinationCrs)
         linePosPt = self.getDimLinePosPt(None, destinationCrs)
         if (dimPt1 is not None) and (dimPt2 is not None) and \
            (linePosPt is not None):
            dimPt1 = qad_utils.scalePoint(dimPt1, basePt, scale)
            dimPt2 = qad_utils.scalePoint(dimPt2, basePt, scale)              
            linePosPt = qad_utils.scalePoint(linePosPt, basePt, scale)
                          
            dimEntity, textOffsetRect = self.dimStyle.getAlignedDimFeatures(plugIn.canvas, \
                                                                            dimPt1, \
                                                                            dimPt2, \
                                                                            linePosPt, \
                                                                            measure)
            self.set(dimEntity)
      elif self.dimStyle.dimType == QadDimTypeEnum.LINEAR: # quota lineare con una linea di quota orizzontale o verticale
         dimPt1, dimPt2 = self.getDimPts(destinationCrs)
         linePosPt = self.getDimLinePosPt(None, destinationCrs)
         preferredAlignment, dimLineRotation = self.getDimLinearAlignment()
         if (dimPt1 is not None) and (dimPt2 is not None) and \
            (linePosPt is not None) and \
            (preferredAlignment is not None) and (dimLineRotation is not None):
            textForcedRot = self.getTextRot()
            if textForcedRot is not None:
               self.dimStyle.textForcedRot = textForcedRot

            dimPt1 = qad_utils.scalePoint(dimPt1, basePt, scale)
            dimPt2 = qad_utils.scalePoint(dimPt2, basePt, scale)              
            linePosPt = qad_utils.scalePoint(linePosPt, basePt, scale)              
            dimLinearAlignment, dimLineRotation = self.getDimLinearAlignment()

            if dimLinearAlignment == QadDimStyleAlignmentEnum.VERTICAL:
               dimLineRotation = math.pi / 2
            dimLinearAlignment = QadDimStyleAlignmentEnum.HORIZONTAL

            dimEntity, textOffsetRect = self.dimStyle.getLinearDimFeatures(plugIn.canvas, \
                                                                           dimPt1, \
                                                                           dimPt2, \
                                                                           linePosPt, \
                                                                           measure, \
                                                                           dimLinearAlignment, \
                                                                           dimLineRotation)
            self.set(dimEntity)


   #============================================================================
   # mirror
   #============================================================================
   def mirror(self, plugIn, mirrorPt, mirrorAngle):
      # mirrorPt = punto base espresso in map coordinate
      destinationCrs = plugIn.canvas.mapRenderer().destinationCrs()

      measure = None if self.isCalculatedText() else self.getTextValue()
            
      if self.dimStyle.dimType == QadDimTypeEnum.ALIGNED: # quota lineare allineata ai punti di origine delle linee di estensione
         dimPt1, dimPt2 = self.getDimPts(destinationCrs)
         linePosPt = self.getDimLinePosPt(None, destinationCrs)
         if (dimPt1 is not None) and (dimPt2 is not None) and \
            (linePosPt is not None):
            dimPt1 = qad_utils.mirrorPoint(dimPt1, mirrorPt, mirrorAngle)
            dimPt2 = qad_utils.mirrorPoint(dimPt2, mirrorPt, mirrorAngle)              
            linePosPt = qad_utils.mirrorPoint(linePosPt, mirrorPt, mirrorAngle)
                          
            dimEntity, textOffsetRect = self.dimStyle.getAlignedDimFeatures(plugIn.canvas, \
                                                                            dimPt1, \
                                                                            dimPt2, \
                                                                            linePosPt, \
                                                                            measure)
            self.set(dimEntity)
      elif self.dimStyle.dimType == QadDimTypeEnum.LINEAR: # quota lineare con una linea di quota orizzontale o verticale
         dimPt1, dimPt2 = self.getDimPts(destinationCrs)
         linePosPt = self.getDimLinePosPt(None, destinationCrs)
         preferredAlignment, dimLineRotation = self.getDimLinearAlignment()
         if (dimPt1 is not None) and (dimPt2 is not None) and \
            (linePosPt is not None) and \
            (preferredAlignment is not None) and (dimLineRotation is not None):
            textForcedRot = self.getTextRot()
            if textForcedRot is not None:
               self.dimStyle.textForcedRot = textForcedRot

            dimPt1 = qad_utils.mirrorPoint(dimPt1, mirrorPt, mirrorAngle)
            dimPt2 = qad_utils.mirrorPoint(dimPt2, mirrorPt, mirrorAngle)              
            linePosPt = qad_utils.mirrorPoint(linePosPt, mirrorPt, mirrorAngle)              
            dimLinearAlignment, dimLineRotation = self.getDimLinearAlignment()

            if dimLinearAlignment == QadDimStyleAlignmentEnum.VERTICAL:
               dimLineRotation = math.pi / 2
            dimLinearAlignment = QadDimStyleAlignmentEnum.HORIZONTAL
            
            ptDummy = qad_utils.getPolarPointByPtAngle(mirrorPt, dimLineRotation, 1)
            ptDummy = qad_utils.mirrorPoint(ptDummy, mirrorPt, mirrorAngle)
            dimLineRotation = qad_utils.getAngleBy2Pts(mirrorPt, ptDummy)            

            dimEntity, textOffsetRect = self.dimStyle.getLinearDimFeatures(plugIn.canvas, \
                                                                           dimPt1, \
                                                                           dimPt2, \
                                                                           linePosPt, \
                                                                           measure, \
                                                                           dimLinearAlignment, \
                                                                           dimLineRotation)
            self.set(dimEntity)


   #============================================================================
   # stretch
   #============================================================================
   def stretch(self, plugIn, containerGeom, offSetX, offSetY):
      """
      containerGeom = può essere una QgsGeometry rappresentante un poligono contenente i punti di geom da stirare
                      oppure una lista dei punti da stirare espressi in map coordinate
      offSetX = spostamento X in map coordinate
      offSetY = spostamento Y in map coordinate
      """
      destinationCrs = plugIn.canvas.mapRenderer().destinationCrs()
      
      measure = None if self.isCalculatedText() else self.getTextValue()
            
      if self.dimStyle.dimType == QadDimTypeEnum.ALIGNED: # quota lineare allineata ai punti di origine delle linee di estensione
         dimPt1, dimPt2 = self.getDimPts(destinationCrs)
         linePosPt = self.getDimLinePosPt(containerGeom, destinationCrs)
         
         if dimPt1 is not None:
            newPt = qad_stretch_fun.stretchPoint(dimPt1, containerGeom, offSetX, offSetY)
            if newPt is not None:
               dimPt1 = newPt
         
         if dimPt2 is not None:
            newPt = qad_stretch_fun.stretchPoint(dimPt2, containerGeom, offSetX, offSetY)
            if newPt is not None:
               dimPt2 = newPt

         if linePosPt is not None:
            newPt = qad_stretch_fun.stretchPoint(linePosPt, containerGeom, offSetX, offSetY)
            if newPt is not None:
               linePosPt = newPt
         else:
            linePosPt = self.getDimLinePosPt()
            # verifico se è stato coinvolto il testo della quota
            if qad_stretch_fun.isPtContainedForStretch(self.getTextPt(destinationCrs), containerGeom):
               if linePosPt is not None:
                  linePosPt = qad_utils.movePoint(linePosPt, offSetX, offSetY)
         
         if (dimPt1 is not None) and (dimPt2 is not None) and \
            (linePosPt is not None):
            dimEntity, textOffsetRect = self.dimStyle.getAlignedDimFeatures(plugIn.canvas, \
                                                                            dimPt1, \
                                                                            dimPt2, \
                                                                            linePosPt, \
                                                                            measure)
            self.set(dimEntity)
      elif self.dimStyle.dimType == QadDimTypeEnum.LINEAR: # quota lineare con una linea di quota orizzontale o verticale
         dimPt1, dimPt2 = self.getDimPts(destinationCrs)
         linePosPt = self.getDimLinePosPt(containerGeom, destinationCrs)
         
         dimLinearAlignment, dimLineRotation = self.getDimLinearAlignment()
         
         if dimPt1 is not None:
            newPt = qad_stretch_fun.stretchPoint(dimPt1, containerGeom, offSetX, offSetY)
            if newPt is not None:
               dimPt1 = newPt
               
         if dimPt2 is not None:
            newPt = qad_stretch_fun.stretchPoint(dimPt2, containerGeom, offSetX, offSetY)
            if newPt is not None:
               dimPt2 = newPt

         if linePosPt is not None:
            newPt = qad_stretch_fun.stretchPoint(linePosPt, containerGeom, offSetX, offSetY)
            if newPt is not None:
               linePosPt = newPt
         else:
            linePosPt = self.getDimLinePosPt()
            # verifico se è stato coinvolto il testo della quota
            if qad_stretch_fun.isPtContainedForStretch(self.getTextPt(destinationCrs), containerGeom):
               if linePosPt is not None:
                  linePosPt = qad_utils.movePoint(linePosPt, offSetX, offSetY)

         if (dimPt1 is not None) and (dimPt2 is not None) and \
            (linePosPt is not None) and \
            (dimLinearAlignment is not None) and (dimLineRotation is not None):
            textForcedRot = self.getTextRot()
            if textForcedRot is not None:
               self.dimStyle.textForcedRot = textForcedRot

            if dimLinearAlignment == QadDimStyleAlignmentEnum.VERTICAL:
               dimLineRotation = math.pi / 2
            dimLinearAlignment = QadDimStyleAlignmentEnum.HORIZONTAL
            
            dimEntity, textOffsetRect = self.dimStyle.getLinearDimFeatures(plugIn.canvas, \
                                                                           dimPt1, \
                                                                           dimPt2, \
                                                                           linePosPt, \
                                                                           measure, \
                                                                           dimLinearAlignment, \
                                                                           dimLineRotation)
            self.set(dimEntity)


   #============================================================================
   # getDimComponentByEntity
   #============================================================================
   def getDimComponentByEntity(self, entity):
      """
      La funzione, data un'entità, restituisce il componente della quotatura.
      """
      if entity.layer == self.getTextualLayer():
         return QadDimComponentEnum.TEXT_PT
      elif entity.layer == self.getLinearLayer() or \
           entity.layer == self.getSymbolLayer():
         try:
            return entity.getFeature().attribute(self.dimStyle.componentFieldName)
         except:
            return None
         
      return None


#===============================================================================
#  = variabile globale
#===============================================================================

QadDimStyles = QadDimStylesClass()                 # lista degli stili di quotatura caricati