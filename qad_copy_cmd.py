# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando COPY per copiare oggetti
 
                              -------------------
        begin                : 2013-10-02
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


# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *


import qad_debug
from qad_copy_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_textwindow import *
from qad_ssget_cmd import QadSSGetClass
from qad_entity import *
from qad_variables import *
import qad_utils

# Classe che gestisce il comando COPY
class QadCOPYCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.get(202) # "COPIA"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runCOPYCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/copy.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.get(203)
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.SSGetClass = QadSSGetClass(plugIn)
      self.SSGetClass.onlyEditableLayers = True
      self.entitySet = QadEntitySet()
      self.basePt = QgsPoint()
      self.series = False
      self.seriesLen = 2
      self.adjust = False
      self.copyMode = QadVariables.get("COPYMODE")
      
      self.featureCache = [] # lista di (layer, feature)
      self.undoFeatureCacheIndexes = [] # posizioni in featureCache dei punti di undo
      self.rubberBand = QgsRubberBand(self.plugIn.canvas, False)
      self.rubberBandPolygon = QgsRubberBand(self.plugIn.canvas, True)

   def __del__(self):
      QadCommandClass.__del__(self)
      del self.SSGetClass
      self.rubberBand.hide()
      self.rubberBandPolygon.hide()
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 0: # quando si è in fase di selezione entità
         return self.SSGetClass.getPointMapTool()
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_copy_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None

   #============================================================================
   # addFeatureCache
   #============================================================================
   def addFeatureCache(self, newPt):      
      featureCacheLen = len(self.featureCache)
      for layerEntitySet in self.entitySet.layerEntitySetList:
         layer = layerEntitySet.layer
         transformedBasePt = self.plugIn.canvas.mapRenderer().mapToLayerCoordinates(layer, self.basePt)
         transformedNewPt = self.plugIn.canvas.mapRenderer().mapToLayerCoordinates(layer, newPt)
         offSetX = transformedNewPt.x() - transformedBasePt.x()
         offSetY = transformedNewPt.y() - transformedBasePt.y()
         
         for featureId in layerEntitySet.featureIds:
            f = layerEntitySet.getFeature(featureId)
            
            if self.series and self.seriesLen > 0: # devo fare una serie
               if self.adjust == True:
                  offSetX = offSetX / (self.seriesLen - 1)
                  offSetY = offSetY / (self.seriesLen - 1)
   
               deltaX = offSetX
               deltaY = offSetY
                              
               for i in xrange(1, self.seriesLen, 1):
                  copiedFeature = QgsFeature(f)
                  copiedFeature.setGeometry(qad_utils.moveQgsGeometry(copiedFeature.geometry(), deltaX, deltaY))
                  self.featureCache.append([layer, copiedFeature])
                  self.addFeatureToRubberBand(layer, copiedFeature)            
                  deltaX = deltaX + offSetX
                  deltaY = deltaY + offSetY     
            else:
               copiedFeature = QgsFeature(f)
               copiedFeature.setGeometry(qad_utils.moveQgsGeometry(copiedFeature.geometry(), offSetX, offSetY))
               self.featureCache.append([layer, copiedFeature])
               self.addFeatureToRubberBand(layerEntitySet.layer, copiedFeature)            
      
      self.undoFeatureCacheIndexes.append(featureCacheLen)

   #============================================================================
   # undoGeomsInCache
   #============================================================================
   def undoGeomsInCache(self):
      #qad_debug.breakPoint()
      tot = len(self.featureCache)
      if tot > 0:
         iEnd = self.undoFeatureCacheIndexes[-1]
         i = tot - 1
         
         del self.undoFeatureCacheIndexes[-1] # cancello ultimo undo
         while i >= iEnd:
            del self.featureCache[-1] # cancello feature
            i = i - 1
         self.refreshRubberBand()
            
   #============================================================================
   # addFeatureToRubberBand
   #============================================================================
   def addFeatureToRubberBand(self, layer, feature):
      if layer.geometryType() == QGis.Polygon:
         self.rubberBandPolygon.addGeometry(feature.geometry(), layer)
      else:
         self.rubberBand.addGeometry(feature.geometry(), layer)
      
      
   #============================================================================
   # refreshRubberBand
   #============================================================================
   def refreshRubberBand(self):
      self.rubberBand.reset(False)
      self.rubberBandPolygon.reset(True)
      for f in self.featureCache:
         layer = f[0]
         feature = f[1]
         if layer.geometryType() == QGis.Polygon:
            self.rubberBandPolygon.addGeometry(feature.geometry(), layer)
         else:
            self.rubberBand.addGeometry(feature.geometry(), layer)            

   def copyGeoms(self):
      featuresLayers = [] # lista di (layer, features)
      
      #qad_debug.breakPoint()   
      for f in self.featureCache:
         layer = f[0]
         feature = f[1]
         found = False
         for featuresLayer in featuresLayers:
            if featuresLayer[0].id() == layer.id():
               found = True
               featuresLayer[1].append(feature)
               break
         # se non c'era ancora il layer
         if not found:
            featuresLayers.append([layer, [feature]])

      for featuresLayer in featuresLayers:
         qad_utils.addFeaturesToLayer(self.plugIn, featuresLayer[0], featuresLayer[1])  
   
   #============================================================================
   # waitForBasePt
   #============================================================================
   def waitForBasePt(self):
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_copy_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_BASE_PT)                                

      if self.copyMode == 0: # Imposta il comando COPIA in modo che venga ripetuto automaticamente
         # "Spostamento" "mOdalità"
         keyWords = QadMsg.get(205) + " " + QadMsg.get(206)
         msg = QadMsg.get(204) # "Specificare il punto base o [Spostamento/mOdalità] <Spostamento>: "
      else:
         # "Spostamento" "mOdalità" "MUltiplo"
         keyWords = QadMsg.get(205) + " " + QadMsg.get(206) + " " + QadMsg.get(220)
         msg = QadMsg.get(219) # "Specificare il punto base o [Spostamento/mOdalità/MUltiplo] <Spostamento>: "
      
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   QadMsg.get(205), \
                   keyWords, QadInputModeEnum.NONE)      
      self.step = 2      
   
   #============================================================================
   # waitForSeries
   #============================================================================
   def waitForSeries(self):
      # si appresta ad attendere un numero intero
      msg = QadMsg.get(212) # "Digitare il numero di elementi da disporre in serie <{0}>: "
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
         # "Serie" "Esci" "Annulla"
         keyWords = QadMsg.get(211) + " " + QadMsg.get(216) + " " + QadMsg.get(217)
         msg = QadMsg.get(215) # "Specificare il secondo punto o [Serie/Esci/Annulla] <Esci>: "
   
         # si appresta ad attendere un punto o enter o una parola chiave         
         # msg, inputType, default, keyWords, nessun controllo
         self.waitFor(msg, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      QadMsg.get(216), \
                      keyWords, QadInputModeEnum.NONE)
      else:
         keyWords = QadMsg.get(211) # "Serie"
         # "Specificare il secondo punto o [Serie] <utilizzare il primo punto come spostamento>: "
         
         # si appresta ad attendere un punto o enter o una parola chiave         
         # msg, inputType, default, keyWords, nessun controllo
         self.waitFor(QadMsg.get(210), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NONE)      
            
      self.step = 3           

   #============================================================================
   # waitForSecondPtBySeries
   #============================================================================
   def waitForSecondPtBySeries(self):
      if self.adjust == False:
         keyWords = QadMsg.get(218) # "Adatta"
      else:
         keyWords = QadMsg.get(211) # "Serie"
      msg = QadMsg.get(213) # "Specificare il secondo punto o [{0}]: "

      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valore nullo non permesso
      self.waitFor(msg.format(keyWords), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   "", \
                   keyWords, QadInputModeEnum.NOT_NULL)      
      self.step = 7

   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.get(128)) # "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate\n"
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

         self.getPointMapTool().entitySet.set(self.entitySet)
         self.waitForBasePt()
         return False
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO BASE (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  pass # opzione di default "spostamento"
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            value = QadMsg.get(205) # "Spostamento"

         if type(value) == unicode:
            if value == QadMsg.get(205): # "Spostamento"
               self.basePt.set(0, 0)
               self.getPointMapTool().basePt = self.basePt
               self.getPointMapTool().setMode(Qad_copy_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_COPY_PT)                                
               # si appresta ad attendere un punto
               msg = QadMsg.get(191) # "Specificare lo spostamento <{0}, {1}>: "
               # msg, inputType, default, keyWords, nessun controllo
               self.waitFor(msg.format(str(self.plugIn.lastOffsetPt.x()), str(self.plugIn.lastOffsetPt.y())), \
                            QadInputTypeEnum.POINT2D, \
                            self.plugIn.lastOffsetPt, \
                            "", QadInputModeEnum.NONE)                                      
               self.step = 4
            elif value == QadMsg.get(206): # "mOdalità"
               keyWords = QadMsg.get(208) + " " + QadMsg.get(209) # "Singola" "Multipla"
               msg = QadMsg.get(207) # "Digitare un'opzione di modalità di copia [Singola/Multipla] <{0}>: "
               if self.copyMode == 0: # Imposta il comando COPIA in modo che venga ripetuto automaticamente
                  default = QadMsg.get(209) # "Multipla"
               else:
                  default = QadMsg.get(208) # "Singola"               
                             
               # si appresta ad attendere un punto o enter o una parola chiave         
               # msg, inputType, default, keyWords, nessun controllo
               self.waitFor(msg.format(default), \
                            QadInputTypeEnum.KEYWORDS, \
                            default, \
                            keyWords, QadInputModeEnum.NONE)
               self.step = 5      
            elif value == QadMsg.get(220): # "MUltiplo"
               self.copyMode = 0 # Imposta il comando COPIA in modo che venga ripetuto automaticamente
               self.waitForBasePt()                         
         elif type(value) == QgsPoint: # se è stato inserito il punto base
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
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if len(self.featureCache) > 0:
                     value = QadMsg.get(216) # "Esci"
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
               value = QadMsg.get(216) # "Esci"
            else:               
               # utilizzare il primo punto come spostamento
               value = QgsPoint(self.basePt)
               self.basePt.set(0, 0)
               self.addFeatureCache(value)
               self.copyGeoms()
               return True # fine comando
         
         if type(value) == unicode:
            if value == QadMsg.get(211): # "Serie"
               self.waitForSeries()               
            elif value == QadMsg.get(216): # "Esci"
               self.copyGeoms()
               return True # fine comando
            elif value == QadMsg.get(217): # "Annulla"
               self.undoGeomsInCache()
               self.waitForSecondPt()
         elif type(value) == QgsPoint: # se è stato inserito lo spostamento con un punto
            self.addFeatureCache(value)
            if self.copyMode == 1: # "Singola" 
               self.copyGeoms()
               return True # fine comando
            self.waitForSecondPt()
         
         return False
               
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL PUNTO DI SPOSTAMENTO (da step = 2)
      elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         self.plugIn.setLastOffsetPt(value)
         self.addFeatureCache(value)
         self.copyGeoms()
         return True # fine comando


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA MODALITA' (SINGOLA / MULTIPLA) (da step = 2)
      elif self.step == 5: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value == QadMsg.get(208): # "Singola"
            self.copyMode = 1
            QadVariables.set("COPYMODE", 1)
            QadVariables.save()
         elif value == QadMsg.get(209): # "Multipla"
            self.copyMode = 0
            QadVariables.set("COPYMODE", 0)
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
            # "\nIl valore deve essere un intero compreso tra 2 e 32767."
            self.showMsg(QadMsg.get(214))
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
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.get(211): # "Serie"
               self.adjust = False
               self.getPointMapTool().adjust = self.adjust
               self.waitForSecondPtBySeries()
            elif value == QadMsg.get(218): # "Adatta"
               self.adjust = True
               self.getPointMapTool().adjust = self.adjust
               self.waitForSecondPtBySeries()
         elif type(value) == QgsPoint: # se è stato inserito lo spostamento con un punto
            self.addFeatureCache(value)
            if self.copyMode == 1: # "Singola" 
               self.copyGeoms()
               return True # fine comando            
            self.waitForSecondPt()
          
         return False