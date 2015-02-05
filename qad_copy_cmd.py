# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando COPY per copiare oggetti
 
                              -------------------
        begin                : 2013-10-02
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


from qad_copy_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_textwindow import *
from qad_ssget_cmd import QadSSGetClass
from qad_entity import *
from qad_variables import *
import qad_utils
import qad_layer
from qad_dim import *


# Classe che gestisce il comando COPY
class QadCOPYCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "COPIA")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runCOPYCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/copy.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_COPY", "Copia gli oggetti selezionati ad una distanza e in una direzione specificate.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.SSGetClass = QadSSGetClass(plugIn)
      self.SSGetClass.onlyEditableLayers = True
      self.entitySet = QadEntitySet()
      self.basePt = QgsPoint()
      self.series = False
      self.seriesLen = 2
      self.adjust = False
      self.copyMode = QadVariables.get(QadMsg.translate("Environment variables", "COPYMODE"))
      
      self.featureCache = [] # lista di (layer, feature)
      self.nOperationsToUndo = 0

   def __del__(self):
      QadCommandClass.__del__(self)
      del self.SSGetClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 0: # quando si é in fase di selezione entità
         return self.SSGetClass.getPointMapTool()
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_copy_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None


   #============================================================================
   # move
   #============================================================================
   def move(self, f, offSetX, offSetY, layerEntitySet, entitySet, dimStyle):
      if dimStyle is not None:
         entity = QadEntity()
         entity.set(layerEntitySet.layer, f.id())
         dimEntity = QadDimEntity()
         if dimEntity.initByEntity(dimStyle, entity) == False:
            dimEntity = None
      else:
         dimEntity = None
      
      if dimEntity is None:
         # sposto la feature e la rimuovo da entitySet (é la prima)
         f.setGeometry(qad_utils.moveQgsGeometry(f.geometry(), offSetX, offSetY))
         # plugIn, layer, feature, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(self.plugIn, layerEntitySet.layer, f, None, False, False) == False:  
            return False
         del layerEntitySet.featureIds[0]
      else:
         # sposto la quota e la rimuovo da entitySet
         dimEntitySet = dimEntity.getEntitySet()
         dimEntity.move(offSetX, offSetY)                               
         if dimEntity.addToLayers(self.plugIn) == False:
            return False             
         entitySet.subtract(dimEntitySet)
            
      return True


   #============================================================================
   # copyGeoms
   #============================================================================
   def copyGeoms(self, newPt):
      # copio entitySet
      entitySet = QadEntitySet(self.entitySet)
      
      self.plugIn.beginEditCommand("Feature copied", entitySet.getLayerList())

      for layerEntitySet in entitySet.layerEntitySetList:
         layer = layerEntitySet.layer
         
         # verifico se il layer appartiene ad uno stile di quotatura
         dimStyle = self.plugIn.dimStyles.getDimByLayer(layer)
         
         transformedBasePt = self.mapToLayerCoordinates(layer, self.basePt)
         transformedNewPt = self.mapToLayerCoordinates(layer, newPt)
         offSetX = transformedNewPt.x() - transformedBasePt.x()
         offSetY = transformedNewPt.y() - transformedBasePt.y()
         
         while len(layerEntitySet.featureIds) > 0:
            featureId = layerEntitySet.featureIds[0]
            f = layerEntitySet.getFeature(featureId)
            
            if self.series and self.seriesLen > 0: # devo fare una serie
               if self.adjust == True:
                  offSetX = offSetX / (self.seriesLen - 1)
                  offSetY = offSetY / (self.seriesLen - 1)
   
               deltaX = offSetX
               deltaY = offSetY
                              
               for i in xrange(1, self.seriesLen, 1):
                  if self.move(f, deltaX, deltaY, layerEntitySet, entitySet, dimStyle) == False:  
                     self.plugIn.destroyEditCommand()
                     return
                  deltaX = deltaX + offSetX
                  deltaY = deltaY + offSetY     
            else:
               if self.move(f, offSetX, offSetY, layerEntitySet, entitySet, dimStyle) == False:  
                  self.plugIn.destroyEditCommand()
                  return
               
      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1


   #============================================================================
   # waitForBasePt
   #============================================================================
   def waitForBasePt(self):
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_copy_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_BASE_PT)                                

      if self.copyMode == 0: # Imposta il comando COPIA in modo che venga ripetuto automaticamente
         keyWords = QadMsg.translate("Command_COPY", "Spostamento") + "/" + \
                    QadMsg.translate("Command_COPY", "mOdalità")
      else:
         keyWords = QadMsg.translate("Command_COPY", "Spostamento") + "/" + \
                    QadMsg.translate("Command_COPY", "mOdalità") + "/" + \
                    QadMsg.translate("Command_COPY", "MUltiplo")
      default = QadMsg.translate("Command_COPY", "Spostamento")                   
      prompt = QadMsg.translate("Command_COPY", "Specificare il punto base o [{0}] <{1}>: ").format(keyWords, default)
      
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   default, \
                   keyWords, QadInputModeEnum.NONE)      
      self.step = 2      
   
   #============================================================================
   # waitForSeries
   #============================================================================
   def waitForSeries(self):
      # si appresta ad attendere un numero intero
      msg = QadMsg.translate("Command_COPY", "Digitare il numero di elementi da disporre in serie <{0}>: ")
      # msg, inputType, default, keyWords, valori positivi
      self.waitFor(msg.format(str(self.seriesLen)), \
                   QadInputTypeEnum.INT, \
                   self.seriesLen, \
                   "", \
                   QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)                                      
      self.step = 6        
      
   #============================================================================
   # waitForSecondPt
   #============================================================================
   def waitForSecondPt(self):
      self.series = False
      self.adjust = False
      self.getPointMapTool().seriesLen = 0
      self.getPointMapTool().setMode(Qad_copy_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_COPY_PT)
                                      
      if len(self.featureCache) > 0:
         keyWords = QadMsg.translate("Command_COPY", "Serie") + "/" + \
                    QadMsg.translate("Command_COPY", "Esci") + "/" + \
                    QadMsg.translate("Command_COPY", "Annulla")
         default = QadMsg.translate("Command_COPY", "Esci")
         prompt = QadMsg.translate("Command_COPY", "Specificare il secondo punto o [{0}] <{1}>: ").format(keyWords, default)
   
         # si appresta ad attendere un punto o enter o una parola chiave         
         # msg, inputType, default, keyWords, nessun controllo
         self.waitFor(prompt, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      default, \
                      keyWords, QadInputModeEnum.NONE)
      else:
         keyWords = QadMsg.translate("Command_COPY", "Serie")
         prompt = QadMsg.translate("Command_COPY", "Specificare il secondo punto o [{0}] <utilizzare il primo punto come spostamento dal punto di origine 0,0>: ").format(keyWords)
                   
         # si appresta ad attendere un punto o enter o una parola chiave         
         # msg, inputType, default, keyWords, nessun controllo
         self.waitFor(prompt, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NONE)      
            
      self.step = 3           

   #============================================================================
   # waitForSecondPtBySeries
   #============================================================================
   def waitForSecondPtBySeries(self):
      if self.adjust == False:
         keyWords = QadMsg.translate("Command_COPY", "Adatta")
      else:
         keyWords = QadMsg.translate("Command_COPY", "Serie")
      prompt = QadMsg.translate("Command_COPY", "Specificare il secondo punto o [{0}]: ").format(keyWords)

      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valore nullo non permesso
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   "", \
                   keyWords, QadInputModeEnum.NOT_NULL)      
      self.step = 7

   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando
            
      #=========================================================================
      # RICHIESTA SELEZIONE OGGETTI
      if self.step == 0: # inizio del comando
         if self.SSGetClass.run(msgMapTool, msg) == True:
            # selezione terminata
            self.step = 1
            return self.run(msgMapTool, msg)
      
      #=========================================================================
      # COPIA OGGETTI
      elif self.step == 1:
         self.entitySet.set(self.SSGetClass.entitySet)
         
         if self.entitySet.count() == 0:
            return True # fine comando

         CurrSettingsMsg = QadMsg.translate("QAD", "\nImpostazioni correnti: ")
         if self.copyMode == 0: # 0 = multipla 
            CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_COPY", "Copia modalità = Multipla")         
         else: # 1 = singola
            CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_COPY", "Copia modalità = Singola")         
         self.showMsg(CurrSettingsMsg)         

         self.getPointMapTool().entitySet.set(self.entitySet)
         self.waitForBasePt()
         self.getPointMapTool().refreshSnapType() # riagggiorno lo snapType che può essere variato dal maptool di selezione entità                    
         return False
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO BASE (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  pass # opzione di default "spostamento"
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            value = QadMsg.translate("Command_COPY", "Spostamento")

         if type(value) == unicode:
            if value == QadMsg.translate("Command_COPY", "Spostamento"):
               self.basePt.set(0, 0)
               self.getPointMapTool().basePt = self.basePt
               self.getPointMapTool().setMode(Qad_copy_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_COPY_PT)                                
               # si appresta ad attendere un punto
               msg = QadMsg.translate("Command_COPY", "Specificare lo spostamento dal punto di origine 0,0 <{0}, {1}>: ")
               # msg, inputType, default, keyWords, nessun controllo
               self.waitFor(msg.format(str(self.plugIn.lastOffsetPt.x()), str(self.plugIn.lastOffsetPt.y())), \
                            QadInputTypeEnum.POINT2D, \
                            self.plugIn.lastOffsetPt, \
                            "", QadInputModeEnum.NONE)                                      
               self.step = 4
            elif value == QadMsg.translate("Command_COPY", "mOdalità"):
               keyWords = QadMsg.translate("Command_COPY", "Singola") + "/" + \
                          QadMsg.translate("Command_COPY", "Multipla")
               if self.copyMode == 0: # Imposta il comando COPIA in modo che venga ripetuto automaticamente
                  default = QadMsg.translate("Command_COPY", "Multipla")
               else:
                  default = QadMsg.translate("Command_COPY", "Singola")               
               prompt = QadMsg.translate("Command_COPY", "Digitare un'opzione di modalità di copia [{0}] <{1}>: ").format(keyWords, default)

               # si appresta ad attendere enter o una parola chiave         
               # msg, inputType, default, keyWords, nessun controllo
               self.waitFor(prompt, \
                            QadInputTypeEnum.KEYWORDS, \
                            default, \
                            keyWords, QadInputModeEnum.NONE)
               self.step = 5      
            elif value == QadMsg.translate("Command_COPY", "MUltiplo"):
               self.copyMode = 0 # Imposta il comando COPIA in modo che venga ripetuto automaticamente
               self.waitForBasePt()                         
         elif type(value) == QgsPoint: # se é stato inserito il punto base
            self.basePt.set(value.x(), value.y())

            # imposto il map tool
            self.getPointMapTool().basePt = self.basePt           
            self.waitForSecondPt()
         
         return False 
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER COPIA (da step = 2)
      elif self.step == 3: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if len(self.featureCache) > 0:
                     value = QadMsg.translate("Command_COPY", "Esci")
                  else:
                     value = None
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            if len(self.featureCache) > 0:
               value = QadMsg.translate("Command_COPY", "Esci")
            else:               
               # utilizzare il primo punto come spostamento
               value = QgsPoint(self.basePt)
               self.basePt.set(0, 0)
               self.copyGeoms(value)
               return True # fine comando
         
         if type(value) == unicode:
            if value == QadMsg.translate("Command_COPY", "Serie"):
               self.waitForSeries()               
            elif value == QadMsg.translate("Command_COPY", "Esci"):
               return True # fine comando
            elif value == QadMsg.translate("Command_COPY", "Annulla"):
               if self.nOperationsToUndo > 0: 
                  self.nOperationsToUndo = self.nOperationsToUndo - 1
                  self.plugIn.undoEditCommand()
               else:
                  self.showMsg(QadMsg.translate("QAD", "Il comando é stato completamente annullato."))                  
               self.waitForSecondPt()
         elif type(value) == QgsPoint: # se é stato inserito lo spostamento con un punto
            self.copyGeoms(value)
            if self.copyMode == 1: # "Singola" 
               return True # fine comando
            self.waitForSecondPt()
         
         return False
               
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL PUNTO DI SPOSTAMENTO (da step = 2)
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

         self.plugIn.setLastOffsetPt(value)
         self.copyGeoms(value)
         return True # fine comando


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA MODALITA' (SINGOLA / MULTIPLA) (da step = 2)
      elif self.step == 5: # dopo aver atteso un punto o un numero reale si riavvia il comando
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
         else: # la parola chiave arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_COPY", "Singola"):
               self.copyMode = 1
               QadVariables.set(QadMsg.translate("Environment variables", "COPYMODE"), 1)
               QadVariables.save()
            elif value == QadMsg.translate("Command_COPY", "Multipla"):
               self.copyMode = 0
               QadVariables.set(QadMsg.translate("Environment variables", "COPYMODE"), 0)
               QadVariables.save()
            
         self.waitForBasePt()
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA SERIE (da step = 3)
      elif self.step == 6: # dopo aver atteso un numero intero si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
               value = self.seriesLen
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value < 2:
            self.showMsg(QadMsg.translate("Command_COPY", "\nIl valore deve essere un intero compreso tra 2 e 32767."))
            self.waitForSeries()
         else:
            self.series = True
            self.seriesLen = value
            self.getPointMapTool().seriesLen = self.seriesLen

            self.waitForSecondPtBySeries()
            
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER COPIA DA SERIE (da step = 6)
      elif self.step == 7: # dopo aver atteso un punto o una parola chiave
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
            if value == QadMsg.translate("Command_COPY", "Serie"):
               self.adjust = False
               self.getPointMapTool().adjust = self.adjust
               self.waitForSecondPtBySeries()
            elif value == QadMsg.translate("Command_COPY", "Adatta"):
               self.adjust = True
               self.getPointMapTool().adjust = self.adjust
               self.waitForSecondPtBySeries()
         elif type(value) == QgsPoint: # se é stato inserito lo spostamento con un punto
            self.copyGeoms(value)
            if self.copyMode == 1: # "Singola" 
               return True # fine comando            
            self.waitForSecondPt()
          
         return False