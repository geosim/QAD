# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando COPY per copiare oggetti
 
                              -------------------
        begin                : 2014-02-19
        copyright            : (C) 2013 IREN Acqua Gas SpA
        email                : geosim.dev@gruppoiren.it
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


# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *


from qad_dim import *
from qad_dim_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_textwindow import *
from qad_entsel_cmd import QadEntSelClass
from qad_getangle_cmd import QadGetAngleClass
from qad_variables import *
import qad_utils
import qad_layer


#============================================================================
# FUNZIONI GENERICHE - INIZIO
#============================================================================


#============================================================================
# getStartEndPointClosestPartWithContext
#============================================================================
def getStartEndPointClosestPartWithContext(entity, point, destCrs):
   # legge il punto iniziale e finale della parte più vicina al punto di selezione
   # se non si tratta di cerchio altrimenti ritorna l'oggetto QadCircle
   geom = entity.getGeometry()

   # trasformo la geometria in screen coordinate
   coordTransform = QgsCoordinateTransform(entity.layer.crs(), destCrs) # trasformo la geometria
   geom.transform(coordTransform)         

   return qad_utils.whatGeomIs(point, geom)


#============================================================================
# FUNZIONI GENERICHE - FINE
#============================================================================


# Classe che gestisce il comando DIMLINEAR
class QadDIMLINEARCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "DIMLINEARE")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runDIMLINEARCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/dimLinear.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_DIM", "Crea una quota lineare orizzontale o verticale.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.EntSelClass = None
      self.GetAngleClass = None
            
      self.dimPt1 = QgsPoint() # primo punto di quotatura esplicito
      self.dimPt2 = QgsPoint() # secondo punto di quotatura esplicito
      self.dimCircle = None    # oggetto cerchio da quotare
      
      self.measure = None # misura della quota (se None viene calcolato)
      self.preferredAlignment = QadDimStyleAlignmentEnum.HORIZONTAL # allineamento della linea di quota
      # leggo lo stile di quotatura corrente
      dimStyleName = QadVariables.get(QadMsg.translate("Environment variables", "DIMSTYLE"))
      self.forcedDimLineAlignment = None # allineamento della linea di quota forzato
      self.forcedDimLineRot = 0.0 # rotazione della linea di quota forzato
      
      _dimStyle = self.plugIn.dimStyles.findDimStyle(dimStyleName)      
      if _dimStyle is not None:
         self.dimStyle = QadDimStyle(_dimStyle) # ne faccio una copia perché può venire modificato dal comando
         self.dimStyle.dimType = QadDimTypeEnum.LINEAR
      else:
         self.dimStyle = None
      

   def __del__(self):
      QadCommandClass.__del__(self)
      if self.EntSelClass is not None:
         self.EntSelClass.entity.deselectOnLayer()
         del self.EntSelClass
      if self.GetAngleClass is not None:
         del self.GetAngleClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 2: # quando si é in fase di selezione entità
         return self.EntSelClass.getPointMapTool(drawMode)
      # quando si é in fase di richiesta rotazione
      elif self.step == 6 or self.step == 7:
         return self.GetAngleClass.getPointMapTool()
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_dim_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None

   
   #============================================================================
   # addDimToLayers
   #============================================================================
   def addDimToLayers(self, linePosPt):
      return self.dimStyle.addLinearDimToLayers(self.plugIn, self.dimPt1, self.dimPt2, \
                                                linePosPt, self.measure, self.preferredAlignment, \
                                                self.forcedDimLineRot)
   
   
   #============================================================================
   # waitForFirstPt
   #============================================================================
   def waitForFirstPt(self):
      self.step = 1
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT)                                

      msg = QadMsg.translate("Command_DIM", "Specificare l'origine della prima linea di estensione o <seleziona oggetto>: ")
      
      # si appresta ad attendere un punto o enter      
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D, \
                   None, \
                   "", QadInputModeEnum.NONE)

   
   #============================================================================
   # waitForSecondPt
   #============================================================================
   def waitForSecondPt(self):
      self.step = 3
      # imposto il map tool
      self.getPointMapTool().dimPt1 = self.dimPt1
      self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)                                
      # si appresta ad attendere un punto
      self.waitForPoint(QadMsg.translate("Command_DIM", "Specificare l'origine della seconda linea di estensione: "))

   
   #============================================================================
   # waitForEntsel
   #============================================================================
   def waitForEntsel(self, msgMapTool, msg):
      if self.EntSelClass is not None:
         del self.EntSelClass
      self.step = 2         
      self.EntSelClass = QadEntSelClass(self.plugIn)
      self.EntSelClass.msg = QadMsg.translate("Command_DIM", "Selezionare l'oggetto da quotare: ")
      # scarto la selezione di punti
      self.EntSelClass.checkPointLayer = False
      self.EntSelClass.checkLineLayer = True
      self.EntSelClass.checkPolygonLayer = True
      self.EntSelClass.getPointMapTool().setSnapType(QadSnapTypeEnum.DISABLE)         
      self.EntSelClass.run(msgMapTool, msg)

   
   #============================================================================
   # waitForDimensionLinePos
   #============================================================================
   def waitForDimensionLinePos(self):
      self.step = 4
      # imposto il map tool      
      self.getPointMapTool().dimPt2 = self.dimPt2
      if self.getPointMapTool().dimPt1 is None: # in caso di selezione oggetto dimPt1 non era stato inizializzato
         self.getPointMapTool().dimPt1 = self.dimPt1
         self.getPointMapTool().dimCircle = self.dimCircle
      self.getPointMapTool().preferredAlignment = self.preferredAlignment
      self.getPointMapTool().forcedDimLineAlignment = self.forcedDimLineAlignment
      self.getPointMapTool().forcedDimLineRot = self.forcedDimLineRot      
      self.getPointMapTool().dimStyle = self.dimStyle      
      self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.FIRST_SECOND_PT_KNOWN_ASK_FOR_LINEAR_DIM_LINE_POS)                                
      
      # si appresta ad attendere un punto o una parola chiave
      keyWords = QadMsg.translate("Command_DIM", "Testo") + "/" + \
                 QadMsg.translate("Command_DIM", "Angolo") + "/" + \
                 QadMsg.translate("Command_DIM", "Orizzontale") + "/" + \
                 QadMsg.translate("Command_DIM", "Verticale") + "/" + \
                 QadMsg.translate("Command_DIM", "Ruotato")      
      prompt = QadMsg.translate("Command_DIM", "Specificare la posizione della linea di quota o [{0}]: ").format(keyWords)
      
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, \
                   QadInputModeEnum.NONE)                                      
      

   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando

      if self.dimStyle is None:
         self.showMsg(QadMsg.translate("QAD", "\nStile di quotatura corrente non valido.\nVerificare il valore della variabile DIMSTYLE.\n"))
         return True # fine comando
         
      errMsg = self.dimStyle.getInValidErrMsg()
      if errMsg is not None:
         self.showMsg(errMsg)
         return True # fine comando
      
      errMsg = self.dimStyle.getNotGraphEditableErrMsg()
      if errMsg is not None:
         self.showMsg(errMsg)
         return True # fine comando


      #=========================================================================
      # RICHIESTA SELEZIONE ORIGINE PRIMA LINEA DI ESTENSIONE
      if self.step == 0: # inizio del comando         
         self.waitForFirstPt()
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA ORIGINE PRIMA LINEA DI ESTENSIONE (da step = 0)
      elif self.step == 1:
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = None # opzione di default None
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            self.waitForEntsel(msgMapTool, msg)
         else:
            self.dimPt1.set(value.x(), value.y())
            self.waitForSecondPt()

         return False

      #=========================================================================
      # RISPOSTA ALLA SELEZIONE DI UN'ENTITA' (da step = 1)
      elif self.step == 2:
         if self.EntSelClass.run(msgMapTool, msg) == True:
            if self.EntSelClass.entity.isInitialized():
               result = getStartEndPointClosestPartWithContext(self.EntSelClass.entity, \
                                                               self.EntSelClass.point, \
                                                               self.plugIn.canvas.mapRenderer().destinationCrs())
               if result is not None:                   
                  if (type(result) == list or type(result) == tuple): # se é una lista di 2 punti
                     self.dimPt1 = result[0]                    
                     self.dimPt2 = result[1]
                  else:
                     objType = result.whatIs()
                     if objType == "ARC": # se é arco
                        self.dimPt1 = result.getStartPt()                 
                        self.dimPt2 = result.getEndPt()
                     elif objType == "CIRCLE": # se é cerchio
                        self.dimCircle = result
                  
               self.waitForDimensionLinePos()
               return False
            else:               
               self.showMsg(QadMsg.translate("Command_DIM", "Non ci sono geometrie in questa posizione."))
               self.waitForEntsel(msgMapTool, msg)
         return False # continua

         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA ORIGINE SECONDA LINEA DI ESTENSIONE (da step = 1)
      elif self.step == 3: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            return True

         if type(value) == QgsPoint: # se é stato inserito il secondo punto
            self.dimPt2.set(value.x(), value.y())
            self.waitForDimensionLinePos()
         
         return False 
         
               
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA POSIZIONE DELLA LINEA DI QUOTA (da step = 2 e 3)
      elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_DIM", "Testo"):
               prompt = QadMsg.translate("Command_DIM", "Digitare il testo di quota <{0}>: ")
               dist = qad_utils.getDistance(self.dimPt1, self.dimPt2)
               self.waitForString(prompt.format(str(dist)), dist)
               self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.ASK_FOR_TEXT)
               self.step = 5         
            elif value == QadMsg.translate("Command_DIM", "Angolo"):
               # si appresta ad attendere l'angolo di rotazione del testo
               if self.GetAngleClass is not None:
                  del self.GetAngleClass                                   
               self.GetAngleClass = QadGetAngleClass(self.plugIn)
               prompt = QadMsg.translate("Command_DIM", "Specificare l'angolo del testo di quota <{0}>: ")
               self.GetAngleClass.msg = prompt.format(str(qad_utils.toDegrees(self.dimStyle.textForcedRot)))
               self.GetAngleClass.angle = self.dimStyle.textForcedRot
               self.step = 6
               self.GetAngleClass.run(msgMapTool, msg)               
            elif value == QadMsg.translate("Command_DIM", "Orizzontale"):
               # allineamento della linea di quota orizzontale
               self.forcedDimLineAlignment = QadDimStyleAlignmentEnum.HORIZONTAL # allineamento della linea di quota forzato               
               self.forcedDimLineRot = 0.0             
               self.waitForDimensionLinePos()
            elif value == QadMsg.translate("Command_DIM", "Verticale"):
               # allineamento della linea di quota verticale               
               self.forcedDimLineAlignment = QadDimStyleAlignmentEnum.VERTICAL # allineamento della linea di quota forzato
               self.forcedDimLineRot = 0.0             
               self.waitForDimensionLinePos()
            elif value == QadMsg.translate("Command_DIM", "Ruotato"):
               # si appresta ad attendere l'angolo di rotazionedella linea di quotatura
               if self.GetAngleClass is not None:
                  del self.GetAngleClass                                   
               self.GetAngleClass = QadGetAngleClass(self.plugIn)
               prompt = QadMsg.translate("Command_DIM", "Specificare l'angolo della linea di quota <{0}>: ")
               self.GetAngleClass.msg = prompt.format(str(qad_utils.toDegrees(self.forcedDimLineRot)))
               self.GetAngleClass.angle = self.forcedDimLineRot
               self.step = 7
               self.GetAngleClass.run(msgMapTool, msg)               
               pass
         elif type(value) == QgsPoint: # se é stato inserito il punto di posizionamento linea quota
            self.preferredAlignment = self.getPointMapTool().preferredAlignment
            self.dimPt1 = self.getPointMapTool().dimPt1
            self.dimPt2 = self.getPointMapTool().dimPt2
            self.addDimToLayers(value)
            return True # fine comando
            
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL TESTO (da step = 4)
      elif self.step == 5: # dopo aver atteso una stringa si riavvia il comando
         if type(msg) == unicode:
            text = msg.strip()
            if len(text) > 0:
               self.measure = text
               self.getPointMapTool().measure = self.measure
         self.waitForDimensionLinePos()
            
         return False
      
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA ROTAZIONE DEL TESTO DI QUOTA (da step = 4)
      elif self.step == 6:
         if self.GetAngleClass.run(msgMapTool, msg) == True:
            if self.GetAngleClass.angle is not None:
               self.dimStyle.textRotMode = QadDimStyleTxtRotModeEnum.FORCED_ROTATION
               self.dimStyle.textForcedRot = self.GetAngleClass.angle 
            self.waitForDimensionLinePos()

         return False
      
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA ROTAZIONE DELLA LINEA DI QUOTA (da step = 4)
      elif self.step == 7:
         if self.GetAngleClass.run(msgMapTool, msg) == True:
            if self.GetAngleClass.angle is not None:
               self.forcedDimLineRot = self.GetAngleClass.angle 
            self.waitForDimensionLinePos()

         return False

      
# Classe che gestisce il comando DIMALIGNED
class QadDIMALIGNEDCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "DIMALLINEATA")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runDIMALIGNEDCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/dimAligned.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_DIM", "Crea una quota allineata.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.EntSelClass = None
      self.GetAngleClass = None
      
      self.dimPt1 = QgsPoint()
      self.dimPt2 = QgsPoint()
      self.dimCircle = None    # oggetto cerchio da quotare
      
      self.measure = None # misura della quota (se None viene calcolato)
      # leggo lo stile di quotatura corrente
      dimStyleName = QadVariables.get(QadMsg.translate("Environment variables", "DIMSTYLE"))
      _dimStyle = self.plugIn.dimStyles.findDimStyle(dimStyleName)      
      if _dimStyle is not None:
         self.dimStyle = QadDimStyle(_dimStyle) # ne faccio una copia perché può venire modificato dal comando
         self.dimStyle.dimType = QadDimTypeEnum.ALIGNED
      else:
         self.dimStyle = None
      

   def __del__(self):
      QadCommandClass.__del__(self)
      if self.EntSelClass is not None:
         self.EntSelClass.entity.deselectOnLayer()
         del self.EntSelClass
      if self.GetAngleClass is not None:
         del self.GetAngleClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 2: # quando si é in fase di selezione entità
         return self.EntSelClass.getPointMapTool(drawMode)
      # quando si é in fase di richiesta rotazione
      elif self.step == 6:
         return self.GetAngleClass.getPointMapTool()
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_dim_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None

   
   #============================================================================
   # addDimToLayers
   #============================================================================
   def addDimToLayers(self, linePosPt):
      return self.dimStyle.addAlignedDimToLayers(self.plugIn, self.dimPt1, self.dimPt2, \
                                                 linePosPt, self.measure)

      
   #============================================================================
   # waitForFirstPt
   #============================================================================
   def waitForFirstPt(self):
      self.step = 1
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT)                                

      msg = QadMsg.translate("Command_DIM", "Specificare l'origine della prima linea di estensione o <seleziona oggetto>: ")
      
      # si appresta ad attendere un punto o enter      
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D, \
                   None, \
                   "", QadInputModeEnum.NONE)

   
   #============================================================================
   # waitForSecondPt
   #============================================================================
   def waitForSecondPt(self):
      self.step = 3
      # imposto il map tool
      self.getPointMapTool().dimPt1 = self.dimPt1
      self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)                                
      # si appresta ad attendere un punto
      self.waitForPoint(QadMsg.translate("Command_DIM", "Specificare l'origine della seconda linea di estensione: "))

   
   #============================================================================
   # waitForEntsel
   #============================================================================
   def waitForEntsel(self, msgMapTool, msg):
      if self.EntSelClass is not None:
         del self.EntSelClass
      self.step = 2         
      self.EntSelClass = QadEntSelClass(self.plugIn)
      self.EntSelClass.msg = QadMsg.translate("Command_DIM", "Selezionare l'oggetto da quotare: ")
      # scarto la selezione di punti
      self.EntSelClass.checkPointLayer = False
      self.EntSelClass.checkLineLayer = True
      self.EntSelClass.checkPolygonLayer = True
      self.EntSelClass.getPointMapTool().setSnapType(QadSnapTypeEnum.DISABLE)         
      self.EntSelClass.run(msgMapTool, msg)

   
   #============================================================================
   # waitForDimensionLinePos
   #============================================================================
   def waitForDimensionLinePos(self):
      self.step = 4
      # imposto il map tool      
      self.getPointMapTool().dimPt2 = self.dimPt2
      if self.getPointMapTool().dimPt1 is None: # in caso di selezione oggetto dimPt1 non era stato inizializzato
         self.getPointMapTool().dimPt1 = self.dimPt1
         self.getPointMapTool().dimCircle = self.dimCircle
      self.getPointMapTool().dimStyle = self.dimStyle      
      self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.FIRST_SECOND_PT_KNOWN_ASK_FOR_ALIGNED_DIM_LINE_POS)                                
      
      # si appresta ad attendere un punto o una parola chiave
      keyWords = QadMsg.translate("Command_DIM", "Testo") + "/" + \
                 QadMsg.translate("Command_DIM", "Angolo")      
      prompt = QadMsg.translate("Command_DIM", "Specificare la posizione della linea di quota o [{0}]: ").format(keyWords)
      
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, \
                   QadInputModeEnum.NONE)                                      
      

   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando

      if self.dimStyle is None:
         self.showMsg(QadMsg.translate("QAD", "\nStile di quotatura corrente non valido.\nVerificare il valore della variabile DIMSTYLE.\n"))
         return True # fine comando
         
      errMsg = self.dimStyle.getInValidErrMsg()
      if errMsg is not None:
         self.showMsg(errMsg)
         return True # fine comando
      
      errMsg = self.dimStyle.getNotGraphEditableErrMsg()
      if errMsg is not None:
         self.showMsg(errMsg)
         return True # fine comando


      #=========================================================================
      # RICHIESTA SELEZIONE ORIGINE PRIMA LINEA DI ESTENSIONE
      if self.step == 0: # inizio del comando         
         self.waitForFirstPt()
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA ORIGINE PRIMA LINEA DI ESTENSIONE (da step = 0)
      elif self.step == 1:
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = None # opzione di default None
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            self.waitForEntsel(msgMapTool, msg)
         else:
            self.dimPt1.set(value.x(), value.y())
            self.waitForSecondPt()

         return False

      #=========================================================================
      # RISPOSTA ALLA SELEZIONE DI UN'ENTITA' (da step = 1)
      elif self.step == 2:
         if self.EntSelClass.run(msgMapTool, msg) == True:
            if self.EntSelClass.entity.isInitialized():
               result = getStartEndPointClosestPartWithContext(self.EntSelClass.entity, \
                                                               self.EntSelClass.point, \
                                                               self.plugIn.canvas.mapRenderer().destinationCrs())
               if result is not None:
                  if (type(result) == list or type(result) == tuple): # se é una lista di 2 punti
                     self.dimPt1 = result[0]                    
                     self.dimPt2 = result[1]
                  else:
                     objType = result.whatIs()
                     if objType == "ARC": # se é arco
                        self.dimPt1 = result.getStartPt()                 
                        self.dimPt2 = result.getEndPt()
                     elif objType == "CIRCLE": # se é cerchio
                        self.dimCircle = result
                        intPts = self.dimCircle.getIntersectionPointsWithInfinityLine(self.dimCircle.center, self.EntSelClass.point)
                        if len(intPts) == 2:
                           self.dimPt1 = intPts[0]
                           self.dimPt2 = intPts[1]                     
                  
               self.waitForDimensionLinePos()
               return False
            else:               
               self.showMsg(QadMsg.translate("Command_DIM", "Non ci sono geometrie in questa posizione."))
               self.waitForEntsel(msgMapTool, msg)
         return False # continua


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA ORIGINE SECONDA LINEA DI ESTENSIONE (da step = 1)
      elif self.step == 3: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            return True

         if type(value) == QgsPoint: # se é stato inserito il secondo punto
            self.dimPt2.set(value.x(), value.y())
            self.waitForDimensionLinePos()
         
         return False 
         
               
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA POSIZIONE DELLA LINEA DI QUOTA (da step = 2 e 3)
      elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_DIM", "Testo"):
               prompt = QadMsg.translate("Command_DIM", "Digitare il testo di quota <{0}>: ")
               dist = qad_utils.getDistance(self.dimPt1, self.dimPt2)
               self.waitForString(prompt.format(str(dist)), dist)
               self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.ASK_FOR_TEXT)
               self.step = 5         
            elif value == QadMsg.translate("Command_DIM", "Angolo"):
               # si appresta ad attendere l'angolo di rotazione del testo
               if self.GetAngleClass is not None:
                  del self.GetAngleClass                                   
               self.GetAngleClass = QadGetAngleClass(self.plugIn)
               prompt = QadMsg.translate("Command_DIM", "Specificare l'angolo del testo di quota <{0}>: ")
               self.GetAngleClass.msg = prompt.format(str(qad_utils.toDegrees(self.dimStyle.textForcedRot)))
               self.GetAngleClass.angle = self.dimStyle.textForcedRot
               self.step = 6
               self.GetAngleClass.run(msgMapTool, msg)               
         elif type(value) == QgsPoint: # se é stato inserito il punto di posizionamento linea quota
            self.dimPt1 = self.getPointMapTool().dimPt1
            self.dimPt2 = self.getPointMapTool().dimPt2
            self.addDimToLayers(value)
            return True # fine comando
            
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL TESTO (da step = 4)
      elif self.step == 5: # dopo aver atteso una stringa si riavvia il comando
         if type(msg) == unicode:
            text = msg.strip()
            if len(text) > 0:
               self.measure = text
               self.getPointMapTool().measure = self.measure
         self.waitForDimensionLinePos()
            
         return False

      
# Classe che gestisce il comando DIMARC da finire
class QadDIMARCCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "ARCOQUOTA")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runDIMARCCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/dimArc.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_DIM", "Crea una quota per la lunghezza di un arco.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.EntSelClass = None
      self.GetAngleClass = None
      
      self.dimPt1 = QgsPoint()
      self.dimPt2 = QgsPoint()
      self.dimArc = None    # oggetto arco da quotare
      
      self.measure = None # misura della quota (se None viene calcolato)
      self.leader = False
      # leggo lo stile di quotatura corrente
      dimStyleName = QadVariables.get(QadMsg.translate("Environment variables", "DIMSTYLE"))
      self.dimStyle = self.plugIn.dimStyles.findDimStyle(dimStyleName)
      if self.dimStyle is not None:
         self.dimStyle.dimType = QadDimTypeEnum.ALIGNED
      

   def __del__(self):
      QadCommandClass.__del__(self)
      if self.EntSelClass is not None:
         self.EntSelClass.entity.deselectOnLayer()
         del self.EntSelClass
      if self.GetAngleClass is not None:
         del self.GetAngleClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 1: # quando si é in fase di selezione entità
         return self.EntSelClass.getPointMapTool(drawMode)
      # quando si é in fase di richiesta rotazione
      elif self.step == 6:
         return self.GetAngleClass.getPointMapTool()
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_dim_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None

   
   #============================================================================
   # addDimToLayers
   #============================================================================
   def addDimToLayers(self, linePosPt):
      return self.dimStyle.addAlignedDimToLayers(self.plugIn, self.dimPt1, self.dimPt2, \
                                                 linePosPt, self.measure)

   
   #============================================================================
   # waitForEntsel
   #============================================================================
   def waitForEntsel(self, msgMapTool, msg):
      if self.EntSelClass is not None:
         del self.EntSelClass
      self.step = 1     
      self.EntSelClass = QadEntSelClass(self.plugIn)
      self.EntSelClass.msg = QadMsg.translate("Command_DIM", "Selezionare l'arco da quotare: ")
      # scarto la selezione di punti
      self.EntSelClass.checkPointLayer = False
      self.EntSelClass.checkLineLayer = True
      self.EntSelClass.checkPolygonLayer = True
      self.EntSelClass.getPointMapTool().setSnapType(QadSnapTypeEnum.DISABLE)         
      self.EntSelClass.run(msgMapTool, msg)

   
   #============================================================================
   # waitForDimensionLinePos
   #============================================================================
   def waitForDimensionLinePos(self):
      self.step = 4
      # imposto il map tool      
      self.getPointMapTool().dimPt2 = self.dimPt2
      if self.getPointMapTool().dimPt1 is None: # in caso di selezione oggetto dimPt1 non era stato inizializzato
         self.getPointMapTool().dimPt1 = self.dimPt1
         self.getPointMapTool().dimCircle = self.dimCircle
      self.getPointMapTool().dimStyle = self.dimStyle      
      self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.FIRST_SECOND_PT_KNOWN_ASK_FOR_ALIGNED_DIM_LINE_POS)                                
      
      # si appresta ad attendere un punto o una parola chiave
      # si appresta ad attendere un punto o una parola chiave
      keyWords = QadMsg.translate("Command_DIM", "Testo") + "/" + \
                 QadMsg.translate("Command_DIM", "Angolo") + "/" + \
                 QadMsg.translate("Command_DIM", "Parziale") + "/"
      if self.leader:
         keyWords = keyWords + QadMsg.translate("Command_DIM", "Direttrice")
      else:
         keyWords = keyWords + QadMsg.translate("Command_DIM", "Nessuna direttrice")
      prompt = QadMsg.translate("Command_DIM", "Specificare la posizione della quota o [{0}]: ").format(keyWords)

      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, \
                   QadInputModeEnum.NONE)                                      
      

   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando

      if self.dimStyle is None:
         self.showMsg(QadMsg.translate("QAD", "\nStile di quotatura corrente non valido.\nVerificare il valore della variabile DIMSTYLE.\n"))
         return True # fine comando
         
      errMsg = self.dimStyle.getInValidErrMsg()
      if errMsg is not None:
         self.showMsg(errMsg)
         return True # fine comando
      
      errMsg = self.dimStyle.getNotGraphEditableErrMsg()
      if errMsg is not None:
         self.showMsg(errMsg)
         return True # fine comando


      #=========================================================================
      # RICHIESTA SELEZIONE ARCO DA QUOTARE
      if self.step == 0: # inizio del comando         
         self.waitForEntsel(msgMapTool, msg)
         return False
      

      #=========================================================================
      # RISPOSTA ALLA SELEZIONE DI UN'ENTITA' (da step = 0)
      elif self.step == 1:
         if self.EntSelClass.run(msgMapTool, msg) == True:
            if self.EntSelClass.entity.isInitialized():
               result = getStartEndPointClosestPartWithContext(self.EntSelClass.entity, \
                                                               self.EntSelClass.point, \
                                                               self.plugIn.canvas.mapRenderer().destinationCrs())
               if result is not None:
                  if (type(result) != list and type(result) != tuple): # se non é una lista di 2 punti
                     objType = result.whatIs()
                     if objType == "ARC": # se é arco
                        self.dimArc = result
                        return False
                     
               self.showMsg(QadMsg.translate("Command_DIM", "Selezionare un arco."))
               self.waitForEntsel(msgMapTool, msg)        
            else:               
               self.showMsg(QadMsg.translate("Command_DIM", "Non ci sono geometrie in questa posizione."))
               self.waitForEntsel(msgMapTool, msg)
         return False # continua


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA ORIGINE SECONDA LINEA DI ESTENSIONE (da step = 1)
      elif self.step == 3: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            return True

         if type(value) == QgsPoint: # se é stato inserito il secondo punto
            self.dimPt2.set(value.x(), value.y())
            self.waitForDimensionLinePos()
         
         return False 
         
               
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA POSIZIONE DELLA LINEA DI QUOTA (da step = 2 e 3)
      elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_DIM", "Testo"):
               prompt = QadMsg.translate("Command_DIM", "Digitare il testo di quota <{0}>: ")
               dist = qad_utils.getDistance(self.dimPt1, self.dimPt2)
               self.waitForString(prompt.format(str(dist)), dist)
               self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.ASK_FOR_TEXT)
               self.step = 5         
            elif value == QadMsg.translate("Command_DIM", "Angolo"):
               # si appresta ad attendere l'angolo di rotazione del testo
               if self.GetAngleClass is not None:
                  del self.GetAngleClass                                   
               self.GetAngleClass = QadGetAngleClass(self.plugIn)
               prompt = QadMsg.translate("Command_DIM", "Specificare l'angolo del testo di quota <{0}>: ")
               self.GetAngleClass.msg = prompt.format(str(qad_utils.toDegrees(self.dimStyle.textForcedRot)))
               self.GetAngleClass.angle = self.dimStyle.textForcedRot
               self.step = 6
               self.GetAngleClass.run(msgMapTool, msg)               
         elif type(value) == QgsPoint: # se é stato inserito il punto di posizionamento linea quota
            self.dimPt1 = self.getPointMapTool().dimPt1
            self.dimPt2 = self.getPointMapTool().dimPt2
            self.addDimToLayers(value)
            return True # fine comando
            
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL TESTO (da step = 4)
      elif self.step == 5: # dopo aver atteso una stringa si riavvia il comando
         if type(msg) == unicode:
            text = msg.strip()
            if len(text) > 0:
               self.measure = text
               self.getPointMapTool().measure = self.measure
         self.waitForDimensionLinePos()
            
         return False
