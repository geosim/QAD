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
import ConfigParser
import math


import qad_debug
import qad_utils
import qad_layer
import qad_label
from qad_variables import *


"""
La classe quotatura è composta da tre layer: testo, linea, simbolo.

Il layer testo deve avere tutte le caratteristiche del layer testo di QAD ed in più:
- il posizionamento dell'etichetta con modalita "Intorno al punto" con distanza = 0 
  (che vuol dire punto di inserimento in basso a sx)
- la dimensione del testo in unità mappa (la dimensione varia a seconda dello zoom).
- dimStyleFieldName = "dim_style"; nome del campo che contiene il nome dello stile di quota (opzionale)
- l'opzioone "Mostra etichette capovolte" deve essere su "sempre" nel tab "Etichette"->"Visualizzazione"
- rotFieldName = "rot"; nome del campo che contiene la rotazione del simbolo (opzionale)
- la rotazione deve essere letta dal campo indicato da rotFieldName

Il layer simbolo deve avere tutte le caratteristiche del layer simbolo di QAD ed in più:
- il simbolo freccia con rotazione 0 deve essere orizzontale con la freccia rivolta verso destra
  ed il suo punto di inserimento deve essere sulla punta della freccia
- la dimensione del simbolo in unità mappa (la dimensione varia a seconda dello zoom).
- componentFieldName = "type"; nome del campo che contiene il tipo di componente della quota (vedi QadDimComponentEnum) (opzionale)
- symbolFieldName = "block"; nome del campo che contiene il nome del simbolo (opzionale)
- idParentFieldName = "id_parent"; nome del campo che contiene il codice del testo della quota (opzionale)
- scaleFieldName = "scale"; nome del campo che contiene il fattore di sclaa del simbolo (opzionale)
- rotFieldName = "rot"; nome del campo che contiene la rotazione del simbolo (opzionale)

Il layer linea deve avere tutte le caratteristiche del layer linea ed in più:
- componentFieldName = "type"; nome del campo che contiene il tipo di componente della quota (vedi QadDimComponentEnum) (opzionale)
- lineTypeFieldName = "line_type"; nome del campo che contiene il tipolinea (opzionale)
- colorFieldName = "color"; nome del campo che contiene il colore 'r,g,b,alpha'; alpha è opzionale (0=trasparente, 255=opaco) (opzionale)
- idParentFieldName = "id_parent"; nome del campo che contiene il codice del testo della quota (opzionale)

"""

#===============================================================================
# QadDimTypeEnum class.
#===============================================================================
class QadDimTypeEnum():
   ALIGNED    = "AL" # quota lineare allineata ai punti di origine delle linee di estensione
   ANGULAR    = "AN" # quota angolare, misura l'angolo tra i 3 punti o tra gli oggetti selezionati
   BASE_LINE  = "BL" # quota lineare, angolare o coordinata a partire dalla linea di base della quota precedente o di una quota selezionata
   CENTER     = "CE" # crea il centro o le linee d'asse di cerchi e archi
   DIAMETER   = "DI" # quota per il diametro di un cerchio o di un arco
   LEADER     = "LD" # crea una linea che consente di collegare un'annotazione ad una lavorazione
   LINEAR     = "LI" # quota lineare con una linea di quota orizzontale o verticale
   RADIUS     = "RA" # quota radiale, misura il raggio di un cerchio o di un arco selezionato e visualizza il testo di quota con un simbolo di raggio davanti
   ARC_LENTGH = "AR" # quota per la lunghezza di un cerchio o di un arco


#===============================================================================
# QadDimComponentEnum class.
#===============================================================================
class QadDimComponentEnum():
   DIM_LINE1 = "D1" # linea di quota ("Dimension line")
   DIM_LINE2 = "D2" # linea di quota ("Dimension line")
   EXT_LINE1 = "E1" # prima linea di estensione ("Extension line 1")
   EXT_LINE2 = "E2" # seconda linea di estensione ("Extension line 2")
   LEADER_LINE = "L" # linea porta quota usata quando il testo è fuori dalla quota ("Leader")
   BLOCK1 = "B1" # primo blocco della freccia ("Block 1")
   BLOCK2 = "B2" # secondo blocco della freccia ("Block 2")
   LEADER_BLOCK = "LB" # blocco della freccia nel caso leader ("Leader Block")
   ARC_BLOCK = "AB" # simbolo dell'arco ("Arc Block")
   DIM_PT1 = "D1" # primo punto da quotare ("Dimension point 1")
   DIM_PT2 = "D2" # secondo punto da quotare ("Dimension point 2")


#===============================================================================
# QadDimStyleAlignmentEnum class.
#===============================================================================
class QadDimStyleAlignmentEnum():
   HORIZONTAL = 0 # orizzontale
   VERTICAL   = 1 # verticale
   ALIGNED    = 2 # allineata


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
   name = "standard" # nome dello stile
   dimType = QadDimTypeEnum.ALIGNED # tipo di quotatura
   
   # testo di quota
   textPrefix = "" # prefisso per il testo della quota
   textSuffix = "" # suffisso per il testo della quota
   textSuppressLeadingZeros = False # per sopprimere o meno gli zero all'inizio del testo
   textDecimaZerosSuppression = True # per sopprimere gli zero finali nei decimali
   textHeight = 1.0 # altezza testo (DIMTXT) in unità di mappa
   textVerticalPos = QadDimStyleTxtVerticalPosEnum.ABOVE_LINE # posizione verticale del testo rispetto la linea di quota (DIMTAD)
   textHorizontalPos = QadDimStyleTxtHorizontalPosEnum.CENTERED_LINE # posizione orizzontale del testo rispetto la linea di quota (DIMTAD)
   textOffsetDist = 0.5 # distanza aggiunta intorno al testo quando per inserirlo viene spezzata la linea di quota
   textRotMode = QadDimStyleTxtRotModeEnum.ALIGNED_LINE # modalità di rotazione del testo
   textDecimals = 2 # numero di decimali
   textDecimalSep = "." # Separatore dei decimali
   textFont = "Arial" # nome del font di testo (DIMTXSTY)
   textDirection = QadDimStyleTxtDirectionEnum.SX_TO_DX # specifica la direzione del testo di quota (DIMTXTDIRECTION) 0 = da sx a dx, 1 = da dx a sx
   arcSymbPos = QadDimStyleArcSymbolPosEnum.BEFORE_TEXT # disegna o meno il simbolo dell'arco con DIMARC (DIMARCSYM). 
   
   # linee di quota
   dimLine1Show = True # Mostra o nasconde la prima linea di quota (DIMSD1)
   dimLine2Show = True # Mostra o nasconde la seconda linea di quota (DIMSD2)
   dimLineLineType = "continuous" # Tipo di linea per le linee di quota (DIMLTYPE)
   dimLineColor = "255,255,255,255" # Colore per le linee di quota (DIMCLRD); bianco con opacità totale
   dimLineSpaceOffset = 3.75 # Controlla la spaziatura delle linee di quota nelle quote da linea di base (DIMDLI)

   # simboli per linee di quota
   # il blocco per la freccia è una freccia verso destra con il punto di inserimento sulla punta della freccia 
   block1Name = "triangle2" # nome del simbolo da usare come punta della freccia sulla prima linea di quota (DIMBLK1)
   block2Name = "triangle2"  # nome del simbolo da usare come punta della freccia sulla seconda linea di quota (DIMBLK2)
   blockLeaderName = "triangle2" # nome del simbolo da usare come punta della freccia sulla linea della direttrice (DIMLDRBLK)
   blockWidth = 0.5 # larghezza del simbolo (in orizzontale) quando la dimensione in unità di mappa = 1 (vedi "triangle2")
   blockScale = 1.0 # scala della dimensione del simbolo (DIMASZ)
   blockSuppressionForNoSpace = False # Sopprime le punte della frecce se non c'è spazio sufficiente all'interno delle linee di estensione (DIMSOXD)
   centerMarkSize = 0.0 # disegna o meno il marcatore di centro o le linee d'asse per le quote create con
                        # DIMCENTER, DIMDIAMETER, e DIMRADIUS (DIMCEN).
                        # 0 = niente, > 0 dimensione marcatore di centro, < 0 dimensione linee d'asse

   # adattamento del testo e delle frecce
   textBlockAdjust = QadDimStyleTextBlocksAdjustEnum.WHICHEVER_FITS_BEST
   
   # linee di estensione
   extLine1Show = True # Mostra o nasconde la prima linea di estensione (DIMSE1)
   extLine2Show = True # Mostra o nasconde la seconda linea di estensione (DIMSE2)
   extLine1LineType = "continuous" # Tipo di linea per la prima linea di estensione (DIMLTEX1)
   extLine2LineType = "continuous" # Tipo di linea per la seconda linea di estensione (DIMLTEX2)
   extLineColor = "255,255,255,255" # Colore per le linee di estensione (DIMCLRE); bianco con opacità totale
   extLineOffsetDimLine = 0.0 # distanza della linea di estensione oltre la linea di quota (DIMEXE)
   extLineOffsetOrigPoints = 0.0 # distanza della linea di estensione dai punti da quotare (DIMEXO)
   extLineIsFixedLen = False # Attiva lunghezza fissa delle line di estensione (DIMFXLON)
   extLineFixedLen = 1.0 # lunghezza fissa delle line di estensione (DIMFXL) dalla linea di quota 
                         # al punto da quotare spostato di extLineOffsetOrigPoints
                         # (la linea di estensione non va oltre il punto da quotare)
   
   # layer e loro caratteristiche
   textLayer = None     # layer per memorizzare il testo della quota
   lineLayer = None     # layer per memorizzare le linee della quota
   symbolLayer = None   # layer per memorizzare i blocchi delle frecce della quota
   # devo allocare i campi a livello di classe QadDimStyle perchè QgsFeature.setFields usa solo il puntatore alla lista fields
   # che, se allocata privatamente in qualsiasi funzione, all'uscita della funzione verrebbe distrutta 
   textFields = None
   dimLine1Fields = None
   dimLine2Fields = None
   extLine1Fields = None
   extLine2Fields = None
   leaderFields = None
   symbol1Fields = None
   symbol2Fields = None
   dimPoint1Fields = None
   dimPoint2Fields = None
   
   componentFieldName = "type" # nome del campo che contiene il tipo di componente della quota (vedi QadDimComponentEnum)
   symbolFieldName = "block" # nome del campo che contiene il nome del simbolo
   lineTypeFieldName = "line_type" # nome del campo che contiene il tipolinea
   colorFieldName = "color" # nome del campo che contiene il colore 'r,g,b,alpha'; alpha è opzionale (0=trasparente, 255=opaco)
   idParentFieldName = "id_parent" # nome del campo che contiene il codice del testo della quota
   dimStyleFieldName = "dim_style" # nome del campo che contiene il nome dello stile di quota
   scaleFieldName = "scale" # nome del campo che contiene la dimensione
   rotFieldName = "rot" # nome del campo che contiene rotazione in gradi
   
          
   def __init__(self, dim = None):
      if dim is None:
         return


   #============================================================================
   # FUNZIONI GENERICHE - INIZIO
   #============================================================================


   #============================================================================
   # setLayers
   #============================================================================
   def setLayers(self, textLayer, lineLayer, symbolLayer):
      # devo allocare i campi a livello di classe QadDimStyle perchè QgsFeature.setFields usa solo il puntatore alla lista fields
      # che, se allocata privatamente in qualsiasi funzione, all'uscita della funzione verrebbe distrutta 
      self.textLayer = textLayer
      self.textFields = None if self.textLayer is None else self.textLayer.pendingFields()
      
      self.lineLayer = lineLayer
      self.dimLine1Fields = None if self.lineLayer is None else self.lineLayer.pendingFields()
      self.dimLine2Fields = None if self.lineLayer is None else self.lineLayer.pendingFields()
      self.extLine1Fields = None if self.lineLayer is None else self.lineLayer.pendingFields()
      self.extLine2Fields = None if self.lineLayer is None else self.lineLayer.pendingFields()
      self.leaderFields = None if self.lineLayer is None else self.lineLayer.pendingFields()
      
      self.symbolLayer = symbolLayer
      self.symbol1Fields = None if self.symbolLayer is None else self.symbolLayer.pendingFields()
      self.symbol2Fields = None if self.symbolLayer is None else self.symbolLayer.pendingFields()      
      self.dimPoint1Fields = None if self.symbolLayer is None else self.symbolLayer.pendingFields()      
      self.dimPoint2Fields = None if self.symbolLayer is None else self.symbolLayer.pendingFields()           
      
   
   #============================================================================
   # save
   #============================================================================
   def save(self, path):
      """
      Salva le impostazioni dello stile di quotatura in un file.
      """
      if path == "":
         return False

      if os.path.dirname(path) == "":
         _path = QDir.cleanPath(QgsApplication.qgisSettingsDirPath() + "/python/plugins/qad/" + path)
      else:
         _path = path
         
      dir = QFileInfo(_path).absoluteDir() 
      if not dir.exists():
         os.makedirs(dir.absolutePath())

      config = ConfigParser.RawConfigParser(allow_no_value=True)
      config.add_section("dimension_options")
      config.set("dimension_options", "name", str(self.name))
      config.set("dimension_options", "dimType", str(self.dimType))
                           
      # testo di quota
      config.set("dimension_options", "textPrefix", str(self.textPrefix))
      config.set("dimension_options", "textSuffix", str(self.textSuffix))
      config.set("dimension_options", "textSuppressLeadingZeros", str(self.textSuppressLeadingZeros))
      config.set("dimension_options", "textDecimaZerosSuppression", str(self.textDecimaZerosSuppression))
      config.set("dimension_options", "textHeight", str(self.textHeight))
      config.set("dimension_options", "textVerticalPos", str(self.textVerticalPos))
      config.set("dimension_options", "textHorizontalPos", str(self.textHorizontalPos))
      config.set("dimension_options", "textOffsetDist", str(self.textOffsetDist))
      config.set("dimension_options", "textRotMode", str(self.textRotMode))
      config.set("dimension_options", "textDecimals", str(self.textDecimals))
      config.set("dimension_options", "textDecimalSep", str(self.textDecimalSep))
      config.set("dimension_options", "textFont", str(self.textFont))
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
      config.set("dimension_options", "textLayer", "" if self.textLayer is None else self.textLayer.name())
      config.set("dimension_options", "lineLayer", "" if self.lineLayer is None else self.lineLayer.name())
      config.set("dimension_options", "symbolLayer", "" if self.symbolLayer is None else self.symbolLayer.name())
      config.set("dimension_options", "componentFieldName", str(self.componentFieldName))
      config.set("dimension_options", "symbolFieldName", str(self.symbolFieldName))
      config.set("dimension_options", "lineTypeFieldName", str(self.lineTypeFieldName))
      config.set("dimension_options", "colorFieldName", str(self.colorFieldName))
      config.set("dimension_options", "idParentFieldName", str(self.idParentFieldName))
      config.set("dimension_options", "dimStyleFieldName", str(self.dimStyleFieldName))

      with open(_path, 'wb') as configfile:
          config.write(configfile)
      return True

   
   #============================================================================
   # load
   #============================================================================
   def load(self, path):
      """
      Carica le impostazioni dello stile di quotatura da un file.
      """
      #qad_debug.breakPoint()

      if path == "":
         return False
      
      if os.path.dirname(path) == "":
         _path = QDir.cleanPath(QgsApplication.qgisSettingsDirPath() + "/python/plugins/qad/" + path)
      else:
         _path = path
         
      if not os.path.exists(_path):
         return False

      config = ConfigParser.RawConfigParser(allow_no_value=True)
      config.read(_path)

      self.name = config.get("dimension_options", "name")
      self.dimType = config.get("dimension_options", "dimType")
                           
      # testo di quota
      self.textPrefix = config.get("dimension_options", "textPrefix")
      self.textSuffix = config.get("dimension_options", "textSuffix")
      self.textSuppressLeadingZeros = config.getboolean("dimension_options", "textSuppressLeadingZeros")
      self.textDecimaZerosSuppression = config.getboolean("dimension_options", "textDecimaZerosSuppression")
      self.textHeight = config.getfloat("dimension_options", "textHeight")
      self.textVerticalPos = config.getint("dimension_options", "textVerticalPos")
      self.textHorizontalPos = config.getint("dimension_options", "textHorizontalPos")
      self.textOffsetDist = config.getfloat("dimension_options", "textOffsetDist")
      self.textRotMode = config.getint("dimension_options", "textRotMode")
      self.textDecimals = config.getint("dimension_options", "textDecimals")
      self.textDecimalSep = config.get("dimension_options", "textDecimalSep")
      self.textFont = config.get("dimension_options", "textFont")
      self.textDirection = config.getint("dimension_options", "textDirection")
      self.textFont = config.get("dimension_options", "textFont")
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
      textLayer = None
      layerName = config.get("dimension_options", "textLayer")
      if layerName != "":
         layerList = qad_layer.getLayersByName(qad_utils.wildCard2regularExpr(layerName))
         if len(layerList) == 1:
            textLayer = layerList[0]
      lineLayer = None
      layerName = config.get("dimension_options", "lineLayer")
      if layerName != "":
         layerList = qad_layer.getLayersByName(qad_utils.wildCard2regularExpr(layerName))
         if len(layerList) == 1:
            lineLayer = layerList[0]
      symbolLayer = None
      layerName = config.get("dimension_options", "symbolLayer")
      if layerName != "":
         layerList = qad_layer.getLayersByName(qad_utils.wildCard2regularExpr(layerName))
         if len(layerList) == 1:
            symbolLayer = layerList[0]
      self.setLayers(textLayer, lineLayer, symbolLayer)
            
      self.componentFieldName = config.get("dimension_options", "componentFieldName")
      self.symbolFieldName = config.get("dimension_options", "symbolFieldName")
      self.lineTypeFieldName = config.get("dimension_options", "lineTypeFieldName")
      self.colorFieldName = config.get("dimension_options", "colorFieldName")
      self.idParentFieldName = config.get("dimension_options", "idParentFieldName")
      self.dimStyleFieldName = config.get("dimension_options", "dimStyleFieldName")
            
      return True
   
      
   #============================================================================
   # getInValidErrMsg
   #============================================================================
   def getInValidErrMsg(self):
      """
      Verifica se lo stile di quotatura è invalido e in caso affermativo ritorna il messaggio di errore.
      Se la quotatura è valida ritorna None.
      """
      prefix = QadMsg.translate("Dimension", "\nLo stile di quotatura \"{0}\" ").format(self.name)
      
      if self.textLayer is None:
         return prefix + QadMsg.translate("Dimension", "non ha impostato il layer per i testi delle quote.\n")
      if qad_layer.isTextLayer(self.textLayer) == False:
         errMsg = prefix + QadMsg.translate("Dimension", "ha il layer per i testi delle quote che non è di tipo testo.")         
         errMsg = errMsg + QadMsg.translate("QAD", "\nUn layer testo è un layer vettoriale di tipo punto con trasparenza del simbolo non superiore al 10% con una etichetta.\n")
         return errMsg

      if self.symbolLayer is None:
         return prefix + QadMsg.translate("Dimension", "non ha impostato il layer per i simboli delle quote.\n")
      if qad_layer.isSymbolLayer(self.symbolLayer) == False:
         errMsg = prefix + QadMsg.translate("Dimension", "ha il layer per i simboli delle quote che non è di tipo simbolo.")         
         errMsg = errMsg + QadMsg.translate("QAD", "\nUn layer simbolo è un layer vettoriale di tipo punto senza etichetta.\n")
         return errMsg

      if self.lineLayer is None:
         return prefix + QadMsg.translate("Dimension", "non ha impostato il layer per le linee delle quote.\n")
      # deve essere un VectorLayer di tipo linea
      if (self.lineLayer.type() != QgsMapLayer.VectorLayer) or (self.lineLayer.geometryType() != QGis.Line):
         errMsg = prefix + QadMsg.translate("Dimension", "ha il layer per le linee delle quote che non è di tipo linea.")         
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
      prefix = QadMsg.translate("Dimension", "\nLo stile di quotatura \"{0}\" ").format(self.name)
      
      provider = self.textLayer.dataProvider()
      if not (provider.capabilities() & QgsVectorDataProvider.EditingCapabilities):
         return prefix + QadMsg.translate("Dimension", "ha il layer per i testi delle quote non modificabile.\n")
      if not self.textLayer.isEditable():
         return prefix + QadMsg.translate("Dimension", "ha il layer per i testi delle quote non modificabile.\n")

      provider = self.symbolLayer.dataProvider()
      if not (provider.capabilities() & QgsVectorDataProvider.EditingCapabilities):
         return prefix + QadMsg.translate("Dimension", "ha il layer per i simboli delle quote non modificabile.\n")
      if not self.symbolLayer.isEditable():
         return prefix + QadMsg.translate("Dimension", "ha il layer per i simboli delle quote non modificabile.\n")
      
      provider = self.lineLayer.dataProvider()
      if not (provider.capabilities() & QgsVectorDataProvider.EditingCapabilities):
         return prefix + QadMsg.translate("Dimension", "ha il layer per le linee delle quote non modificabile.\n")
      if not self.lineLayer.isEditable():
         return prefix + QadMsg.translate("Dimension", "ha il layer per le linee delle quote non modificabile.\n")
      
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
      #qad_debug.breakPoint()
      line1 = None
      line2 = None               
      intPts = self.getIntersectionPtsBetweenTextRectAndLine(textRect, pt1, pt2)
      if textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1: # linea di quota ("Dimension line")
         if len(intPts) == 2: # il rettangolo è sulla linea
            if self.dimLine1Show:
               line1 = [pt1, intPts[0]]
            if self.dimLine2Show:
               line2 = [intPts[1], pt2]
         else: # il rettangolo non è sulla linea            
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
      elif textLinearDimComponentOn == QadDimComponentEnum.LEADER_LINE: # linea porta quota usata quando il testo è fuori dalla quota ("Leader")
         if len(intPts) > 0:
            line1 = [pt1, intPts[0]]
         else:
            line1 = [pt1, pt2]

      return line1, line2

   
   #============================================================================
   # setDimId
   #============================================================================
   def setDimId(self, dimId, features):
      """
      Setta tutte le feature passate nella lista <features> con il codice della quota <dimIdZ.
      """
      if len(self.idParentFieldName) == 0:
         return True

      for f in features:
         try:
            if f is not None:
               # imposto il codice della quota
               f.setAttribute(self.idParentFieldName, dimId)
         except:
            return False
      return True        


   #============================================================================
   # setDimId
   #============================================================================
   def recodeDimId(self, oldDimId, newDimId):
      """
      Ricodifica tutte le feature della quota oldDimId con il nuovo codice newDimId.
      """
      if len(self.idParentFieldName) == 0:
         return True
      
      # ricerco e setto l'entità testo
      f = qad_utils.getFeatureById(self.textLayer, oldDimId)
      if f is not None:
         if self.setDimId(newDimId, [f]) == False:
            return False
      
      feature = QgsFeature()
      expression = "\"" + self.idParentFieldName + "\"=" + str(oldDimId)   

      # ricerco e setto le entità linea
      if self.setDimId(newDimId, self.linelayer.getFeatures(QgsFeatureRequest().setFilterExpression(expression))) == False:
         return False
      
      # ricerco e setto le entità punto
      if self.setDimId(newDimId, self.pointlayer.getFeatures(QgsFeatureRequest().setFilterExpression(expression))) == False:
         return False

      return True


   #============================================================================
   # addLinearDimToLayers
   #============================================================================
   def addLinearDimToLayers(self, plugIn, dimPt1, dimPt2, linePosPt, measure = None, preferredAlignment = QadDimStyleAlignmentEnum.HORIZONTAL):
      """
      Aggiunge ai layers le features che compongono una quota lineare.
      """
      #qad_debug.breakPoint()
      plugIn.beginEditCommand("Aligned dimension added", [self.symbolLayer, self.lineLayer, self.textLayer])

      dimPtFeatures, dimLineFeatures, textFeatureGeom, \
      blockFeatures, extLineFeatures, txtLeaderLineFeature = self.getLinearDimFeatures(plugIn.canvas, \
                                                                                       dimPt1, \
                                                                                       dimPt2, \
                                                                                       linePosPt, \
                                                                                       measure, \
                                                                                       preferredAlignment)
      textFeature = textFeatureGeom[0]
      
      # prima di tutto inserisco il testo di quota
      if textFeature is not None:
         # plugIn, layer, feature, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(plugIn, self.textLayer, textFeature, None, False, False) == False:
            self.plugIn.destroyEditCommand()
            return False
      dimId = textFeature.id()
         
      # punti di quotatura
      self.setDimId(dimId, dimPtFeatures)
      if dimPtFeatures[0] is not None:
         # plugIn, layer, feature, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(plugIn, self.symbolLayer, dimPtFeatures[0], None, False, False) == False:
            plugIn.destroyEditCommand()
            return False
      if dimPtFeatures[1] is not None:
         # plugIn, layer, feature, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(plugIn, self.symbolLayer, dimPtFeatures[1], None, False, False) == False:
            plugIn.destroyEditCommand()
            return False
      # linee di quota
      self.setDimId(dimId, dimLineFeatures)
      if dimLineFeatures[0] is not None:
         # plugIn, layer, feature, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(plugIn, self.lineLayer, dimLineFeatures[0], None, False, False) == False:
            plugIn.destroyEditCommand()
            return False
      if dimLineFeatures[1] is not None:
         # plugIn, layer, feature, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(plugIn, self.lineLayer, dimLineFeatures[1], None, False, False) == False:
            plugIn.destroyEditCommand()
            return False
      # simboli di quota
      self.setDimId(dimId, blockFeatures)
      if blockFeatures[0] is not None:
         # plugIn, layer, feature, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(plugIn, self.symbolLayer, blockFeatures[0], None, False, False) == False:
            plugIn.destroyEditCommand()
            return False
      if blockFeatures[1] is not None:
         # plugIn, layer, feature, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(plugIn, self.symbolLayer, blockFeatures[1], None, False, False) == False:
            plugIn.destroyEditCommand()
            return False
      # linee di estensione della quota
      self.setDimId(dimId, extLineFeatures)
      if extLineFeatures[0] is not None:
         # plugIn, layer, feature, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(plugIn, self.lineLayer, extLineFeatures[0], None, False, False) == False:
            plugIn.destroyEditCommand()
            return False
      if extLineFeatures[1] is not None:
         # plugIn, layer, feature, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(plugIn, self.lineLayer, extLineFeatures[1], None, False, False) == False:
            plugIn.destroyEditCommand()
            return False
      # linea leader del testo di quota   
      self.setDimId(dimId, [txtLeaderLineFeature])
      if txtLeaderLineFeature is not None:
         # plugIn, layer, feature, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(plugIn, self.lineLayer, txtLeaderLineFeature, None, False, False) == False:
            plugIn.destroyEditCommand()
            return False

      plugIn.endEditCommand()
      return True

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
      - il primo elemento è la rotazione del blocco 1
      - il secondo elemento è la rotazione del blocco 2
      
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
      # se la proienzione non è nel segmento
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
      txtRect = rettangolo di occupazione del testo o None se non c'è il testo
      dimLinePt1 = primo punto della linea di quotatura
      dimLinePt2 = primo punto della linea di quotatura
      Restituisce lo spazio disponibile per i blocchi 1 e 2 considerando il rettangolo (QadLinearObjectList) che rappresenta il testo
      e la linea di quota dimLinePt1-dimLinePt2.
      """
      if txtRect is None: # se non c'è il testo (è stato spostato fuori dalla linea di quota)
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
      textLinearDimComponentOn = indica il componente della quota dove è situato il testo di quota (QadDimComponentEnum)
      sourceCrs = sistema di coordinate di insPt
      """
      
      # se non c'è il simbolo di quota
      if insPt is None or rot is None:
         return None     
      # se si tratta del simbolo 1
      if isBlock1 == True:
         # se non deve essere mostrata la linea 1 di quota (vale solo se il testo è sulla linea di quota)
         if self.dimLine1Show == False and \
           (textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1 or textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE2):
            return None
      else: # se si tratta del simbolo 2
         # se non deve essere mostrata la linea 2 di quota (vale solo se il testo è sulla linea di quota)
         if self.dimLine2Show == False and \
           (textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1 or textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE2):
            return None
      
      f = QgsFeature()
      g = QgsGeometry.fromPoint(insPt)
       
      if (sourceCrs is not None) and sourceCrs != self.symbolLayer.crs():
         coordTransform = QgsCoordinateTransform(sourceCRS, self.symbolLayer.crs()) # trasformo la geometria
         g.transform(coordTransform)                        

      f.setGeometry(g)
      # Add attribute fields to feature.
      fields = self.symbol1Fields if isBlock1 else self.symbol2Fields
      f.setFields(fields)

      # assegno i valori di default
      provider = self.symbolLayer.dataProvider()
      for field in fields.toList():
         i = fields.indexFromName(field.name())
         f[field.name()] = provider.defaultValue(i)

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
      f = QgsFeature()
      g = QgsGeometry.fromPoint(insPt)
      
      if (sourceCrs is not None) and sourceCrs != self.symbolLayer.crs():
         coordTransform = QgsCoordinateTransform(sourceCRS, self.symbolLayer.crs()) # trasformo la geometria
         g.transform(coordTransform)                        
       
      f.setGeometry(g)
      # Add attribute fields to feature.
      fields = self.dimPoint1Fields if isDimPt1 else self.dimPoint2Fields
      f.setFields(fields)

      # assegno i valori di default
      provider = self.symbolLayer.dataProvider()
      for field in fields.toList():
         i = fields.indexFromName(field.name())
         f[field.name()] = provider.defaultValue(i)         
         
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
      Restituisce il testo formattato della misura della quota
      """
      if type(measure) == int or type(measure) == float:
         intPart, decPart = qad_utils.getIntDecParts(round(measure, self.textDecimals)) # numero di decimali
         
         if intPart == 0 and self.textSuppressLeadingZeros == True: # per sopprimere o meno gli zero all'inizio del testo
            intStrPart = ""
         else:
            intStrPart = str(intPart)
         
         decStrPart = str(decPart)
         for i in xrange(0, self.textDecimals - len(decStrPart), 1):  # aggiunge "0" per arrivare al numero di decimali
            decStrPart = decStrPart + "0"
            
         if self.textDecimaZerosSuppression == True: # per sopprimere gli zero finali nei decimali
            decStrPart = decStrPart.rstrip("0")
         
         formattedText = "-" if measure < 0 else "" # segno
         formattedText = formattedText + intStrPart # parte intera
         if len(decStrPart) > 0: # parte decimale
            formattedText = formattedText + self.textDecimalSep + decStrPart # Separatore dei decimali
         # aggiungo prefisso e suffisso per il testo della quota
         return self.textPrefix + formattedText + self.textSuffix
      elif type(measure) == unicode:
         return measure
      else:
         return ""

   
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
      e un segmento pt1-pt2. La lista è ordinata per distanza da pt1.
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
      """
      lineRot = qad_utils.getAngleBy2Pts(pt1, pt2) # angolo della linea
      
      if (lineRot > math.pi * 3 / 2 and lineRot <= math.pi * 2) or \
          (lineRot >= 0 and lineRot <= math.pi / 2): # da sx a dx
         textInsPtCloseToPt1 = True
      else: # da dx a sx
         textInsPtCloseToPt1 = False
      
      if rotMode == QadDimStyleTxtRotModeEnum.ALIGNED_LINE: # testo allineato alla linea   
         if lineRot > (math.pi / 2) and lineRot <= math.pi * 3 / 2: # se il testo è capovolto lo giro
            textRot = lineRot - math.pi
         else:
            textRot = lineRot
         
         # allineamento orizzontale
         #=========================
         if horizontalPos == QadDimStyleTxtHorizontalPosEnum.CENTERED_LINE: # testo centrato alla linea
            middlePt = qad_utils.getMiddlePoint(pt1, pt2)
            if textInsPtCloseToPt1: # il punto di inserimento del testo è vicino a pt1
               insPt = qad_utils.getPolarPointByPtAngle(middlePt, lineRot - math.pi, textWidth / 2)                              
            else: # il punto di inserimento del testo è vicino a pt2
               insPt = qad_utils.getPolarPointByPtAngle(middlePt, lineRot, textWidth / 2)
               
         elif horizontalPos == QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE: # testo vicino a pt1
            # uso 2 volte textOffsetDist perchè una volta è la distanza dal punto pt1 + un offset intorno al testo
            if textInsPtCloseToPt1: # il punto di inserimento del testo è vicino a pt1
               insPt = qad_utils.getPolarPointByPtAngle(pt1, lineRot, self.textOffsetDist + self.textOffsetDist)
            else: # il punto di inserimento del testo è vicino a pt2
               insPt = qad_utils.getPolarPointByPtAngle(pt1, lineRot, textWidth + self.textOffsetDist + self.textOffsetDist)

         elif horizontalPos == QadDimStyleTxtHorizontalPosEnum.SECOND_EXT_LINE: # testo vicino a pt2
            # uso 2 volte textOffsetDist perchè una volta è la distanza dal punto pt1 + un offset intorno al testo
            lineLen = qad_utils.getDistance(pt1, pt2)
            if textInsPtCloseToPt1: # il punto di inserimento del testo è vicino a pt1
               insPt = qad_utils.getPolarPointByPtAngle(pt1, lineRot, lineLen - textWidth - (self.textOffsetDist + self.textOffsetDist))
            else: # il punto di inserimento del testo è vicino a pt2
               insPt = qad_utils.getPolarPointByPtAngle(pt1, lineRot, lineLen - (self.textOffsetDist + self.textOffsetDist))         

         # allineamento verticale
         #=========================
         if verticalPos == QadDimStyleTxtVerticalPosEnum.CENTERED_LINE: # testo centrato alla linea
            if textInsPtCloseToPt1: # il punto di inserimento del testo è vicino a pt1
               insPt = qad_utils.getPolarPointByPtAngle(insPt, lineRot - math.pi / 2, textHeight / 2)
            else: # il punto di inserimento del testo è vicino a pt2
               insPt = qad_utils.getPolarPointByPtAngle(insPt, lineRot + math.pi / 2, textHeight / 2)
         elif verticalPos == QadDimStyleTxtVerticalPosEnum.ABOVE_LINE: # sopra alla linea
            # uso 2 volte textOffsetDist perchè una volta è la distanza dalla linea + un offset intorno al testo
            if textInsPtCloseToPt1: # il punto di inserimento del testo è vicino a pt1
               insPt = qad_utils.getPolarPointByPtAngle(insPt, lineRot + math.pi / 2, self.textOffsetDist + self.textOffsetDist)
            else: # il punto di inserimento del testo è vicino a pt2
               insPt = qad_utils.getPolarPointByPtAngle(insPt, lineRot - math.pi / 2, self.textOffsetDist + self.textOffsetDist)
         elif verticalPos == QadDimStyleTxtVerticalPosEnum.BELOW_LINE: # sotto alla linea
            # uso 2 volte textOffsetDist perchè una volta è la distanza dalla linea + un offset intorno al testo
            if textInsPtCloseToPt1: # il punto di inserimento del testo è vicino a pt1
               insPt = qad_utils.getPolarPointByPtAngle(insPt, lineRot - math.pi / 2, textHeight + (self.textOffsetDist + self.textOffsetDist))
            else: # il punto di inserimento del testo è vicino a pt2
               insPt = qad_utils.getPolarPointByPtAngle(insPt, lineRot + math.pi / 2, textHeight + (self.textOffsetDist + self.textOffsetDist))
         
      elif rotMode == QadDimStyleTxtRotModeEnum.HORIZONTAL: # testo orizzontale
         qad_debug.breakPoint()
         lineLen = qad_utils.getDistance(pt1, pt2) # lunghezza della linea
         textRot = 0
         # cerco qual'è l'angolo del rettangolo più vicino alla linea
         #  <2>----width----<3>
         #   |               |
         # height          height
         #   |               |
         #  <1>----width----<4>
         # ricavo il rettangolo che racchiude il testo e lo posiziono con il suo angolo in basso a sinistra sul punto pt1
         textRect = self.textRectToQadLinearObjectList(pt1, textWidth, textHeight, textRot)
         # ottengo i punti estremi della proiezione del rettangolo sulla linea
         #qad_debug.breakPoint()
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
      di estensione perchè era troppo grosso:
      - il primo elemento è il punto di inserimento
      - il secondo elemento è la rotazione del testo 
      - il terzo elemento è una lista di linee da usare come porta quota
      
      La funzione lo posizione a lato della linea di estensione 2. 
      dimLinePt1 = primo punto della linea di quota (QgsPoint)
      dimLinePt2 = secondo punto della linea di quota (QgsPoint)
      textWidth = larghezza testo
      textHeight = altezza testo
      """
      #qad_debug.breakPoint()
      # Ottengo le linee porta quota per il testo esterno
      lines = self.getLeaderLines(dimLinePt1, dimLinePt2, textWidth, textHeight)
      # considero l'ultima che è quella che si riferisce al testo
      line = lines[-1]
      
      textInsPt, textRot = self.getTextPositionOnLine(line[0], line[1], textWidth, textHeight, \
                                                      QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE, \
                                                      self.textVerticalPos, \
                                                      QadDimStyleTxtRotModeEnum.ALIGNED_LINE)
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
      - il primo elemento è una lista con il punto di inserimento del testo della quota e la sua rotazione
      - il secondo elemento è una lista con flag che indica il tipo della linea sulla quale è stato messo il testo; vedi QadDimComponentEnum
                            e una lista di linee "leader" nel caso il testo sia all'esterno della quota
      - il terzo elemento è la rotazione del primo blocco delle frecce; può essere None se non visibile
      - il quarto elemento è la rotazione del secondo blocco delle frecce; può essere None se non visibile   
      """      
      textInsPt                = None # punto di inserimento del testo
      textRot                  = None # rotazione del testo
      textLinearDimComponentOn = None # codice del componente lineare sul quale è posizionato il testo
      txtLeaderLines           = None # lista di linee "leader" nel caso il testo sia all'esterno della quota
      block1Rot                = None # rotazione del primo blocco delle frecce
      block2Rot                = None # rotazione del secondo blocco delle frecce
      
      #qad_debug.breakPoint()
               
      # se il testo è tra le linee di estensione della quota
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
            #qad_debug.breakPoint()
            textVerticalPos = QadDimStyleTxtVerticalPosEnum.ABOVE_LINE
            # la linea di quota ha la stessa Y dei punti di quotatura
            if qad_utils.doubleNear(dimLinePt1.y(), dimPt1.y()) and qad_utils.doubleNear(dimLinePt2.y(), dimPt2.y()):
               # la linea di quota è a destra dei punti di quotatura
               if dimLinePt1.x() > dimPt1.x() and dimLinePt2.x() > dimPt2.x():
                  textVerticalPos = QadDimStyleTxtVerticalPosEnum.BELOW_LINE            
            # la linea di quota è sotto i punti di quotatura
            elif dimLinePt1.y() < dimPt1.x() and dimLinePt2.y() < dimPt2.x():
               textVerticalPos = QadDimStyleTxtVerticalPosEnum.BELOW_LINE
         else:
            textVerticalPos = self.textVerticalPos
            
         textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1Offset, dimLinePt2Offset, textWidth, textHeight, \
                                                         self.textHorizontalPos, textVerticalPos, self.textRotMode)
         
         #qad_debug.breakPoint()
         rect = self.textRectToQadLinearObjectList(textInsPt, textWidth, textHeight, textRot)
         spaceForBlock1, spaceForBlock2 = self.getSpaceForBlock1AndBlock2(rect, dimLinePt1, dimLinePt2)
                  
         # se lo spazio non è sufficiente per inserire testo e simboli all'interno delle linee di estensione,
         if spaceForBlock1 == 0 or spaceForBlock2 == 0 or \
            spaceForBlock1 < self.getBlock1Size() + self.textOffsetDist or spaceForBlock2 < self.getBlock2Size() + self.textOffsetDist:
            if self.blockSuppressionForNoSpace: # sopprime i simboli se non c'è spazio sufficiente all'interno delle linee di estensione
               block1Rot = None
               block2Rot = None
               
               # considero il testo senza frecce 
               textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1, dimLinePt2, textWidth, textHeight, \
                                                               self.textHorizontalPos, textVerticalPos, self.textRotMode)
               
               rect = self.textRectToQadLinearObjectList(textInsPt, textWidth, textHeight, textRot)
               spaceForBlock1, spaceForBlock2 = self.getSpaceForBlock1AndBlock2(rect, dimLinePt1, dimLinePt2)
               # se non c'è spazio neanche per il testo senza le frecce
               if spaceForBlock1 == 0 or spaceForBlock2 == 0 or \
                  spaceForBlock1 < self.textOffsetDist or spaceForBlock2 < self.textOffsetDist:           
                  # sposta testo fuori dalle linee di estensione
                  textInsPt, textRot, txtLeaderLines = self.getTextPosAndLinesOutOfDimLines(dimLinePt1, dimLinePt2, textWidth, textHeight)
                  textLinearDimComponentOn = QadDimComponentEnum.LEADER_LINE
               else:
                  textLinearDimComponentOn = QadDimComponentEnum.DIM_LINE1                
            else: # non devo sopprimere i simboli
               # la prima cosa da spostare all'esterno è:
               if self.textBlockAdjust == QadDimStyleTextBlocksAdjustEnum.BOTH_OUTSIDE_EXT_LINES:
                  # sposta testo e frecce fuori dalle linee di estensione
                  textInsPt, textRot, txtLeaderLines = self.getTextPosAndLinesOutOfDimLines(dimLinePt1, dimLinePt2, textWidth, textHeight)
                  textLinearDimComponentOn = QadDimComponentEnum.LEADER_LINE 
                  block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, False) # frecce esterne 
               # sposta prima le frecce poi, se non basta, anche il testo
               elif self.textBlockAdjust == QadDimStyleTextBlocksAdjustEnum.FIRST_BLOCKS_THEN_TEXT:
                  block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, False) # frecce esterne 
                  # considero il testo senza frecce 
                  textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1, dimLinePt2, textWidth, textHeight, \
                                                                  self.textHorizontalPos, textVerticalPos, self.textRotMode)
                  
                  rect = self.textRectToQadLinearObjectList(textInsPt, textWidth, textHeight, textRot)
                  spaceForBlock1, spaceForBlock2 = self.getSpaceForBlock1AndBlock2(rect, dimLinePt1, dimLinePt2)
                  # se non c'è spazio neanche per il testo senza le frecce
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
                     textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1, dimLinePt2, textWidth, textHeight, \
                                                                     self.textHorizontalPos, textVerticalPos, self.textRotMode)
                     
                     rect = self.textRectToQadLinearObjectList(textInsPt, textWidth, textHeight, textRot)
                     spaceForBlock1, spaceForBlock2 = self.getSpaceForBlock1AndBlock2(rect, dimLinePt1, dimLinePt2)
                     # se non c'è spazio neanche per il testo senza le frecce
                     if spaceForBlock1 == 0 or spaceForBlock2 == 0 or \
                        spaceForBlock1 < self.textOffsetDist or spaceForBlock2 < self.textOffsetDist:                
                        # sposta testo fuori dalle linee di estensione
                        textInsPt, textRot, txtLeaderLines = self.getTextPosAndLinesOutOfDimLines(dimLinePt1, dimLinePt2, textWidth, textHeight)
                        textLinearDimComponentOn = QadDimComponentEnum.LEADER_LINE
                     else:
                        textLinearDimComponentOn = QadDimComponentEnum.DIM_LINE1 
                  else: # il testo è più ingombrante dei simboli
                     # sposto il testo fuori dalle linee di estensione
                     #qad_debug.breakPoint()
                     textInsPt, textRot, txtLeaderLines = self.getTextPosAndLinesOutOfDimLines(dimLinePt1, dimLinePt2, textWidth, textHeight)
                     textLinearDimComponentOn = QadDimComponentEnum.LEADER_LINE 
                     # se non ci stanno neanche le frecce
                     if qad_utils.getDistance(dimLinePt1, dimLinePt2) <= self.getBlock1Size() + self.getBlock2Size():
                        block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, False) # frecce esterne 
                     else:
                        block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, True) # frecce interne
         else: # se lo spazio è sufficiente per inserire testo e simboli all'interno delle linee di estensione,
            textLinearDimComponentOn = QadDimComponentEnum.DIM_LINE1
            block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, True) # frecce interne
      
      # il testo è sopra e allineato alla prima linea di estensione         
      elif self.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE_UP:
         # angolo della linea che va dal punto di quota all'inizio della linea di quota
         rotLine = qad_utils.getAngleBy2Pts(dimPt1, dimLinePt1)
         pt = qad_utils.getPolarPointByPtAngle(dimLinePt1, rotLine, self.textOffsetDist + textWidth)
         if self.textVerticalPos == QadDimStyleTxtVerticalPosEnum.EXTERN_LINE:
            textVerticalPos = QadDimStyleTxtVerticalPosEnum.ABOVE_LINE
         else:
            textVerticalPos = self.textVerticalPos
            
         textInsPt, textRot = self.getTextPositionOnLine(dimLinePt1, pt, textWidth, textHeight, \
                                                         QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE, \
                                                         textVerticalPos, \
                                                         QadDimStyleTxtRotModeEnum.ALIGNED_LINE)
         textLinearDimComponentOn = QadDimComponentEnum.EXT_LINE1 
         
         # calcolo lo spazio dei blocchi in assenza del testo
         spaceForBlock1, spaceForBlock2 = self.getSpaceForBlock1AndBlock2(None, dimLinePt1, dimLinePt2)
         # se non c'è spazio per i blocchi
         if spaceForBlock1 < self.getBlock1Size() or spaceForBlock2 < self.getBlock2Size():
            if self.blockSuppressionForNoSpace: # i blocchi sono soppressi
               block1Rot = None
               block2Rot = None
            else: # sposto le frecce all'esterno
               block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, False)
         else: # c'è spazio per i blocchi
            block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, True) # frecce interne
               
      # il testo è sopra e allineato alla prima linea di estensione         
      elif self.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.SECOND_EXT_LINE_UP:
         # angolo della linea che va dal punto di quota all'inizio della linea di quota
         rotLine = qad_utils.getAngleBy2Pts(dimPt2, dimLinePt2)
         pt = qad_utils.getPolarPointByPtAngle(dimLinePt2, rotLine, self.textOffsetDist + textWidth)
         if self.textVerticalPos == QadDimStyleTxtVerticalPosEnum.EXTERN_LINE:
            textVerticalPos = QadDimStyleTxtVerticalPosEnum.ABOVE_LINE
         else:
            textVerticalPos = self.textVerticalPos
            
         textInsPt, textRot = self.getTextPositionOnLine(dimLinePt2, pt, textWidth, textHeight, \
                                                         QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE, \
                                                         textVerticalPos, \
                                                         QadDimStyleTxtRotModeEnum.ALIGNED_LINE)
         textLinearDimComponentOn = QadDimComponentEnum.EXT_LINE2 
         
         # calcolo lo spazio dei blocchi in assenza del testo
         spaceForBlock1, spaceForBlock2 = self.getSpaceForBlock1AndBlock2(None, dimLinePt1, dimLinePt2)
         # se non c'è spazio per i blocchi
         if spaceForBlock1 < self.getBlock1Size() or spaceForBlock2 < self.getBlock2Size():
            if self.blockSuppressionForNoSpace: # i blocchi sono soppressi
               block1Rot = None
               block2Rot = None
            else: # sposto le frecce all'esterno
               block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, False)
         else: # c'è spazio per i blocchi
            block1Rot, block2Rot = self.getBlocksRot(dimLinePt1, dimLinePt2, True) # frecce interne
      
      if self.textDirection == QadDimStyleTxtDirectionEnum.DX_TO_SX:
         qad_debug.breakPoint()
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
      La rotazione è espressa in radianti.
      sourceCrs = sistema di coordinate di pt
      """
      _pt = QgsPoint(0,0) if pt is None else pt
      _rot = 0 if rot is None else rot
      
      f = QgsFeature()
      g = QgsGeometry.fromPoint(_pt)
      
      if (sourceCrs is not None) and sourceCrs != self.textLayer.crs():
         coordTransform = QgsCoordinateTransform(sourceCRS, self.textLayer.crs()) # trasformo la geometria
         g.transform(coordTransform)                        
       
      f.setGeometry(g)
      # Add attribute fields to feature.
      f.setFields(self.textFields)

      # assegno i valori di default
      provider = self.textLayer.dataProvider()
      for field in self.textFields.toList():
         i = self.textFields.indexFromName(field.name())
         f[field.name()] = provider.defaultValue(i)

      # se il testo dipende da un solo campo 
      labelFieldNames = qad_label.get_labelFieldNames(self.textLayer)
      if len(labelFieldNames) == 1 and len(labelFieldNames[0]) > 0:
         f.setAttribute(labelFieldNames[0], self.getFormattedText(measure))

      # se l'altezza testo dipende da un solo campo 
      sizeFldNames = qad_label.get_labelSizeFieldNames(self.textLayer)
      if len(sizeFldNames) == 1 and len(sizeFldNames[0]) > 0:
         f.setAttribute(sizeFldNames[0], self.textHeight) # altezza testo
         
      # se la rotazione dipende da un solo campo
      rotFldNames = qad_label.get_labelRotationFieldNames(self.textLayer)
      if len(rotFldNames) == 1 and len(rotFldNames[0]) > 0:
         f.setAttribute(rotFldNames[0], qad_utils.toDegrees(_rot)) # Converte da radianti a gradi
   
      # se il font dipende da un solo campo
      fontFamilyFldNames = qad_label.get_labelFontFamilyFieldNames(self.textLayer)
      if len(fontFamilyFldNames) == 1 and len(fontFamilyFldNames[0]) > 0:
         f.setAttribute(fontFamilyFldNames[0], self.textFont) # nome del font di testo      
      
      # imposto il colore
      try:
         if len(self.colorFieldName) > 0:
            f.setAttribute(self.colorFieldName, self.dimLineColor)         
      except:
         pass
      
      # imposto lo stile di quotatura
      try:
         if len(self.dimStyleFieldName) > 0:
            f.setAttribute(self.dimStyleFieldName, self.dimType)         
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
      fuori dalle linee di estensione perchè era troppo grosso.
      dimLinePt1 = primo punto della linea di quota (QgsPoint)
      dimLinePt2 = secondo punto della linea di quota (QgsPoint)
      textWidth = larghezza testo
      textHeight = altezza testo
      """
      #qad_debug.breakPoint()
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

      #qad_debug.breakPoint()         
      f = QgsFeature()
       
      pts = []
      first = True
      for line in leaderLines:
         if first:
            pts.append(line[0])
            first = False
         pts.append(line[1])
         
      g = QgsGeometry.fromPolyline(pts)
         
      if (sourceCrs is not None) and sourceCrs != self.lineLayer.crs():
         coordTransform = QgsCoordinateTransform(sourceCRS, self.lineLayer.crs()) # trasformo la geometria
         g.transform(coordTransform)                        
                
      f.setGeometry(g)
      # Add attribute fields to feature.
      f.setFields(self.leaderFields)
         
      # assegno i valori di default
      provider = self.lineLayer.dataProvider()
      for field in self.leaderFields.toList():
         i = self.leaderFields.indexFromName(field.name())
         f[field.name()] = provider.defaultValue(i)
         
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
      il primo punto è vicino alla linea di quota, il secondo al punto da quotare
      """

      angle = qad_utils.getAngleBy2Pts(dimPt, dimLinePt)
      # distanza della linea di estensione oltre la linea di quota
      pt1 = qad_utils.getPolarPointByPtAngle(dimLinePt, angle, self.extLineOffsetDimLine)
      # distanza della linea di estensione dai punti da quotare
      pt2 = qad_utils.getPolarPointByPtAngle(dimPt, angle, self.extLineOffsetOrigPoints)        

      #qad_debug.breakPoint()
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
      
      f = QgsFeature()
      g = QgsGeometry.fromPolyline(extLine)
       
      if (sourceCrs is not None) and sourceCrs != self.lineLayer.crs():
         coordTransform = QgsCoordinateTransform(sourceCRS, self.lineLayer.crs()) # trasformo la geometria
         g.transform(coordTransform)                        
       
      f.setGeometry(g)
      # Add attribute fields to feature.
      fields = self.extLine1Fields if isExtLine1 else self.extLine2Fields      
      f.setFields(fields)
         
      # assegno i valori di default
      provider = self.lineLayer.dataProvider()
      for field in fields.toList():
         i = fields.indexFromName(field.name())
         f[field.name()] = provider.defaultValue(i)
         
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
   def getDimLine(self, dimPt1, dimPt2, linePosPt, preferredAlignment = QadDimStyleAlignmentEnum.HORIZONTAL):
      """
      Restituisce la linea di quotatura:

      dimPt1 = primo punto da quotare
      dimPt2 = secondo punto da quotare
      linePosPt = punto per indicare dove deve essere posizionata la linea di quota
      preferredAlignment = se lo stile di quota è lineare, indica se ci si deve allineare ai punti di quota
                           in modo orizzontale o verticale (se i punti di quota formano una linea obliqua)      
      """      
      if self.dimType == QadDimTypeEnum.ALIGNED:
         # calcolo la proiezione perpendicolare del punto <linePosPt> sulla linea che congiunge <dimPt1> a <dimPt2>
         ptPerp = qad_utils.getPerpendicularPointOnInfinityLine(dimPt1, dimPt2, linePosPt)
         d = qad_utils.getDistance(linePosPt, ptPerp)
   
         angle = qad_utils.getAngleBy2Pts(dimPt1, dimPt2)
         if qad_utils.leftOfLine(LinePosPt, dimPt1, dimPt2) < 0: # a sinistra della linea che congiunge <dimPt1> a <dimPt2>
            angle = angle + (math.pi / 2)
         else:
            angle = angle - (math.pi / 2)
   
         # linea di quota
         return [qad_utils.getPolarPointByPtAngle(dimPt1, angle, d), \
                 qad_utils.getPolarPointByPtAngle(dimPt2, angle, d)]
      elif self.dimType == QadDimTypeEnum.LINEAR:
         if preferredAlignment == QadDimStyleAlignmentEnum.HORIZONTAL:
            return [QgsPoint(dimPt1.x(), linePosPt.y()), \
                    QgsPoint(dimPt2.x(), linePosPt.y())]         
         elif preferredAlignment == QadDimStyleAlignmentEnum.VERTICAL:
            return [QgsPoint(linePosPt.x(), dimPt1.y()), \
                    QgsPoint(linePosPt.x(), dimPt2.y())]


   #============================================================================
   # getDimLineFeature
   #============================================================================
   def getDimLineFeature(self, dimLine, isDimLine1, textLinearDimComponentOn, sourceCrs = None):
      """
      Restituisce la feature per la linea di quota.
      dimLine = linea di quota [pt1, pt2]
      isDimLine1 = se True si tratta della linea di quota 1 altrimenti della linea di quota 2
      textLinearDimComponentOn = indica il componente della quota dove è situato il testo di quota (QadDimComponentEnum)
      sourceCrs = sistema di coordinate di dimLine
      """
            
      # se non c'è la linea di quota
      if dimLine is None:
         return None
      if isDimLine1 == True: # se si tratta della linea di quota 1
         # se la linea di quota 1 deve essere invisibile (vale solo se il testo è sulla linea di quota)
         if self.dimLine1Show == False and \
           (textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1 or textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE2):
            return None
      else: # se si tratta della linea di quota 2
         # se la linea di quota 2 deve essere invisibile (vale solo se il testo è sulla linea di quota)
         if self.dimLine2Show == False and \
           (textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1 or textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE2):
            return None
               
      f = QgsFeature()
      #qad_debug.breakPoint()      
      g = QgsGeometry.fromPolyline(dimLine)
       
      if (sourceCrs is not None) and sourceCrs != self.lineLayer.crs():
         coordTransform = QgsCoordinateTransform(sourceCRS, self.lineLayer.crs()) # trasformo la geometria
         g.transform(coordTransform)                        
       
      f.setGeometry(g)
      # Add attribute fields to feature.
      fields = self.dimLine1Fields if isDimLine1 else self.dimLine2Fields      
      f.setFields(fields)

      # assegno i valori di default
      provider = self.lineLayer.dataProvider()
      for field in fields.toList():
         i = fields.indexFromName(field.name())
         f[field.name()] = provider.defaultValue(i)
         
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
   def getLinearDimFeatures(self, canvas, dimPt1, dimPt2, linePosPt, measure = None, preferredAlignment = QadDimStyleAlignmentEnum.HORIZONTAL):
      """
      dimPt1 = primo punto da quotare (in unita di mappa)
      dimPt2 = secondo punto da quotare (in unita di mappa)
      linePosPt = punto per indicare dove deve essere posizionata la linea di quota (in unita di mappa)
      measure = indica se la misura è predeterminata oppure (se = None) deve essere calcolata
      preferredAlignment = se lo stile di quota è lineare, indica se ci si deve allienare ai punti di quota
                           in modo orizzontale o verticale (se i punti di quota formano una linea obliqua)      
      
      # quota lineare con una linea di quota orizzontale o verticale
      # ritorna una lista di elementi che descrivono la geometria della quota:
      # 1 lista = feature del primo e del secondo punto di quota; QgsFeature 1, QgsFeature 2
      # 2 lista = feature della prima e della seconda linea di quota (quest'ultima può essere None); QgsFeature 1, QgsFeature 2
      # 3 lista = feature del punto del testo di quota e geometria del rettangolo di occupazione; QgsFeature, QgsGeometry
      # 4 lista = feature del primo e del secondo simbolo per la linea di quota (possono essere None); QgsFeature 1, QgsFeature 2
      # 5 lista = feature della prima e della seconda linea di estensione (possono essere None); QgsFeature 1, QgsFeature 2
      # 6 elemento = feature della linea di leader (può essere None); QgsFeature
      """
      # punti di quotatura
      dimPt1Feature = self.getDimPointFeature(dimPt1, True, \
                                              canvas.mapRenderer().destinationCrs()) # True = primo punto di quotatura
      dimPt2Feature = self.getDimPointFeature(dimPt2, False, \
                                              canvas.mapRenderer().destinationCrs()) # False = secondo punto di quotatura   
               
      # linea di quota
      #qad_debug.breakPoint()
      dimLine1 = self.getDimLine(dimPt1, dimPt2, linePosPt, preferredAlignment)
      dimLine2 = None
      
      # testo e blocchi
      if measure is None:
         if preferredAlignment == QadDimStyleAlignmentEnum.HORIZONTAL:
            textValue = max(dimPt1.x(), dimPt2.x()) - min(dimPt1.x(), dimPt2.x())
         else:
            textValue = max(dimPt1.y(), dimPt2.y()) - min(dimPt1.y(), dimPt2.y())
      else:
         textValue = str(measure)
         
      textFeature = self.getTextFeature(textValue)      
      textWidth, textHeight = qad_label.calculateLabelSize(self.textLayer, textFeature, canvas)

      # creo un rettangolo intorno al testo con un buffer = self.textOffsetDist
      textWidthOffset  = textWidth + self.textOffsetDist * 2
      textHeightOffset = textHeight + self.textOffsetDist * 2

      #qad_debug.breakPoint()      
      # Restituisce una lista di 4 elementi:
      # - il primo elemento è una lista con il punto di inserimento del testo della quota e la sua rotazione
      # - il secondo elemento è una lista con flag che indica il tipo della linea sulla quale è stato messo il testo; vedi QadDimComponentEnum
      #                       e una lista di linee "leader" nel caso il testo sia all'esterno della quota
      # - il terzo elemento è la rotazione del primo blocco delle frecce; può essere None se non visibile
      # - il quarto elemento è la rotazione del secondo blocco delle frecce; può essere None se non visibile      
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
      
      #qad_debug.breakPoint()
      if textLinearDimComponentOn == QadDimComponentEnum.DIM_LINE1: # linea di quota ("Dimension line")
         dimLine1, dimLine2 = self.adjustLineAccordingTextRect(textOffsetRect, dimLine1[0], dimLine1[1], QadDimComponentEnum.DIM_LINE1)
      elif textLinearDimComponentOn == QadDimComponentEnum.EXT_LINE1: # prima linea di estensione ("Extension line 1")
         if extLine1 is not None:
            extLineRot = qad_utils.getAngleBy2Pts(dimPt1, dimLine1[0])
            extLine1 = self.getExtLine(dimPt1, qad_utils.getPolarPointByPtAngle(dimLine1[0], extLineRot, textWidth + self.textOffsetDist))
            # passo prima il secondo punto e poi il primo perchè getExtLine restituisce una linea dalla linea di quota verso il punto di quotatura       
            extLine1, dummy = self.adjustLineAccordingTextRect(textOffsetRect, extLine1[1], extLine1[0], QadDimComponentEnum.EXT_LINE1)
      elif textLinearDimComponentOn == QadDimComponentEnum.EXT_LINE2: # seconda linea di estensione ("Extension line 2")
         if extLine2 is not None:
            extLineRot = qad_utils.getAngleBy2Pts(dimPt2, dimLine1[1])
            extLine2 = self.getExtLine(dimPt2, qad_utils.getPolarPointByPtAngle(dimLine1[1], extLineRot, textWidth + self.textOffsetDist))            
            # passo prima il secondo punto e poi il primo perchè getExtLine restituisce una linea dalla linea di quota verso il punto di quotatura       
            extLine2, dummy = self.adjustLineAccordingTextRect(textOffsetRect, extLine2[1], extLine2[0], QadDimComponentEnum.EXT_LINE2)
      elif textLinearDimComponentOn == QadDimComponentEnum.LEADER_LINE: # linea porta quota usata quando il testo è fuori dalla quota ("Leader")
         #qad_debug.breakPoint()
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
            
      return [dimPt1Feature, dimPt2Feature], \
             [dimLine1Feature, dimLine2Feature], \
             [textFeature, QgsGeometry.fromPolygon([textOffsetRect.asPolyline()])], \
             [block1Feature, block2Feature], \
             [extLine1Feature, extLine2Feature], \
             txtLeaderLineFeature
