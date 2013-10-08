# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando OFFSET per fare l'offset di un oggetto
 
                              -------------------
        begin                : 2013-10-04
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
from qad_offset_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_textwindow import *
from qad_entity import *
from qad_variables import *
import qad_utils

# Classe che gestisce il comando OFFSET
class QadOFFSETCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.get(221) # "OFFSET"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runOFFSETCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/offset.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.get(222)
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.entity = QadEntity()
      self.offSet = QadVariables.get("OFFSETDIST")
      self.firstPt = QgsPoint()
      self.eraseEntity = False
      self.multi = False
      self.gapType = QadVariables.get("OFFSETGAPTYPE")
      
      self.featureCache = [] # lista di (layer, feature)
      self.undoFeatureCacheIndexes = [] # posizioni in featureCache dei punti di undo
      self.rubberBand = QgsRubberBand(self.plugIn.canvas, False)
      self.rubberBandPolygon = QgsRubberBand(self.plugIn.canvas, True)

   def __del__(self):
      QadCommandClass.__del__(self)
      self.rubberBand.hide()
      self.rubberBandPolygon.hide()
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_offset_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None

   #============================================================================
   # addFeatureCache
   #============================================================================
   def addFeatureCache(self, newPt):      
      featureCacheLen = len(self.featureCache)
      layer = self.entity.layer
      feature = self.entity.getFeature()
      transformedNewPt = self.plugIn.canvas.mapRenderer().mapToLayerCoordinates(layer, newPt)
      subGeom = qad_utils.getSubGeom(feature.geometry(), newPt)

      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      dummy = qad_utils.closestSegmentWithContext(transformedPt, subGeom)
      if self.offSet < 0:
         afterVertex = dummy[2]
         pt = qad_utils.getPerpendicularPointOnInfinityLine(subGeom.vertexAt(afterVertex - 1), \
                                                            subGeom.vertexAt(afterVertex), \
                                                            newPt)
         offSetDistance = qad_utils.getDistance(newPt, pt)
      else:
         offSetDistance = self.offSet
      
      lines = qad_utils.offSetPolyline(subGeom.asPolyline(), \
                                       offSetDistance, \
                                       "left" if dummy[2] < 0 else "right", \
                                       self.gapType)
      for line in lines:
         if layer.geometryType() == QGis.Polygon:
            offsetGeom = QgsGeometry.fromPolygon([line])
         else:
            offsetGeom = QgsGeometry.fromPolyline(line)

         if g.isGeosValid():           
            offsetFeature = QgsFeature(f)                              
            offsetFeature.setGeometry(offsetGeom)
            self.featureCache.append([layer, offsetFeature])
            self.addFeatureToRubberBand(layer, offsetFeature)            
      
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

   def offsetGeoms(self):
      featuresLayers = [] # lista di (layer, features)
      
      qad_debug.breakPoint()   
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
   # waitForDistance
   #============================================================================
   def waitForDistance(self):      
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_offset_maptool_ModeEnum.ASK_FOR_FIRST_OFFSET_PT)                                

      # "Punto" "Cancella"
      keyWords = QadMsg.get(224) + " " + QadMsg.get(225)
      msg = QadMsg.get(223) # "Specificare distanza di offset o [Punto/Cancella] <{0}>: "
      if self.offSet < 0:
         msg = msg.format(QadMsg.get(224)) # "Punto"
         default = QadMsg.get(224) # "Punto"
      else:
         msg = msg.format(str(self.offSet))
         default = self.offSet

      # si appresta ad attendere un punto o enter o una parola chiave o un numero reale     
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT | QadInputTypeEnum.KEYWORDS, \
                   default, \
                   keyWords, \
                   QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)      
      self.step = 1      
   
   #============================================================================
   # waitForObjectSel
   #============================================================================
   def waitForObjectSel(self):      
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_offset_maptool_ModeEnum.ASK_FOR_ENTITY_SELECTION)                                

      # "Esci" "ANnulla"
      keyWords = QadMsg.get(227) + " " + QadMsg.get(228)
      
      # 226 = "Selezionare oggetto di cui eseguire l'offset o [Esci/ANnulla] <Esci>: "
      # 227 = "Esci"
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(QadMsg.get(226), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   QadMsg.get(227), \
                   keyWords, QadInputModeEnum.NONE)      
      self.step = 2      
        
   #============================================================================
   # waitForSidePt
   #============================================================================
   def waitForSidePt(self):      
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_offset_maptool_ModeEnum.OFFSET_KNOWN_ASK_FOR_SIDE_PT)                                

      if self.multi == False:
         # "Esci" "MUltiplo" "ANnulla"    
         keyWords = QadMsg.get(227) + " " + QadMsg.get(233) + " " + QadMsg.get(228)
         msg = QadMsg.get(235) # ""Specificare punto sul lato di cui eseguire l'offset o [Esci/MUltiplo/ANnulla] <Esci>: "
         default = QadMsg.get(227) # "Esci"
      else:
         # "Esci" "ANnulla"
         keyWords = QadMsg.get(227) + " " + QadMsg.get(228)
         msg = QadMsg.get(236) # "Specificare punto sul lato di cui eseguire l'offset o [Esci/ANnulla] <oggetto successivo>: "
         default = None

      # 227 = "Esci"
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valore nullo non permesso
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   default, \
                   keyWords, QadInputModeEnum.NONE)      
      self.step = 3
        
   #============================================================================
   # waitForPassagePt
   #============================================================================
   def waitForPassagePt(self):
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_offset_maptool_ModeEnum.ASK_FOR_PASSAGE_PT)                                

      if self.multi == False:
         # "Esci" "MUltiplo" "ANnulla"    
         keyWords = QadMsg.get(227) + " " + QadMsg.get(233) + " " + QadMsg.get(228)
         msg = QadMsg.get(232) # "Specificare punto di passaggio o [Esci/MUltiplo/ANnulla] <Esci>: "
         default = QadMsg.get(227) # "Esci"
      else:
         # "Esci" "ANnulla"    
         keyWords = QadMsg.get(227) + " " + QadMsg.get(228)
         msg = QadMsg.get(234) # "Specificare punto di passaggio o [Esci/ANnulla] <oggetto successivo>: "
         default = None

      # 227 = "Esci"
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valore nullo non permesso
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   default, \
                   keyWords, QadInputModeEnum.NONE)      
      self.step = 4

   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.get(128)) # "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate\n"
         return True # fine comando

      #=========================================================================
      # RICHIESTA DISTANZA DI OFFSET
      if self.step == 0: # inizio del comando
         self.waitForDistance()
            
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA DISTANZA DI OFFSET (da step = 0)
      elif self.step == 1: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.offSet < 0:
                     value = QadMsg.get(224) # "Punto"
                  else:
                     value = self.offSet
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.get(224): # "Punto"
               self.offSet = -1
               self.getPointMapTool().offSet = self.offSet
               QadVariables.set("OFFSETDIST", self.offSet)
               QadVariables.save()               
               # si appresta ad attendere la selezione di un oggetto
               self.waitForObjectSel()
            elif value == QadMsg.get(225): # "Cancella"
               keyWords = QadMsg.get(230) + " " + QadMsg.get(231) # "Sì" "No"                               
              
               # "Cancellare l'oggetto sorgente dopo l'offset? [Sì/No] <{0}>: "
               msg = QadMsg.get(229)
               if self.eraseEntity == True:
                  default = QadMsg.get(230) # "Sì"
               else: 
                  default = QadMsg.get(231) # "No"
                   
               # si appresta ad attendere un punto o enter o una parola chiave         
               # msg, inputType, default, keyWords, nessun controllo
               self.waitFor(msg.format(default), \
                            QadInputTypeEnum.KEYWORDS, \
                            default, \
                            keyWords, QadInputModeEnum.NONE)
               self.step = 5
            elif value == QadMsg.get(220): # "MUltiplo"
               self.multi = True
               self.waitForBasePt()                         
         elif type(value) == QgsPoint: # se è stato inserito il primo punto per il calcolo della distanza
            self.firstPt.set(value.x(), value.y())
            # imposto il map tool
            self.getPointMapTool().firstPt = self.firstPt           
            self.getPointMapTool().setMode(Qad_offset_maptool_ModeEnum.FIRST_OFFSET_PT_KNOWN_ASK_FOR_SECOND_PT)
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.get(93)) # "Specificare secondo punto: "           
            self.step = 6
         elif type(value) == float:
            self.offSet = value
            self.getPointMapTool().offSet = self.offSet
            QadVariables.set("OFFSETDIST", self.offSet)
            QadVariables.save()
            # si appresta ad attendere la selezione di un oggetto
            self.waitForObjectSel()
         
         return False 

      #=========================================================================
      # RISPOSTA ALLA SELEZIONE DI UN OGGETTO
      elif self.step == 2:
         entity = None
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = QadMsg.get(227) # "Esci"
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               entity = self.getPointMapTool().entity
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
         
         if type(value) == unicode:
            if value == QadMsg.get(227): # "Esci"
               self.offsetGeoms()
               return True
            elif value == QadMsg.get(228): # "ANnulla"
               self.undoGeomsInCache()
         elif type(value) == QgsPoint: # se è stato selezionato un punto
            if entity is not None and entity.isInitialized(): # se è stata selezionata una entità
               self.entity.set(entity.layer, entity.featureId)
               self.getPointMapTool().layer = self.entity.layer
               geom = entity.getGeometry()
               transformedPt = self.plugIn.canvas.mapRenderer().mapToLayerCoordinates(self.entity.layer, value)
               #qad_debug.breakPoint()             
               # ritorna una tupla (<The squared cartesian distance>,
               #                    <minDistPoint>
               #                    <afterVertex>
               #                    <leftOf>)
               dummy = qad_utils.closestSegmentWithContext(transformedPt, geom)
               if dummy[2] is not None:
                  self.getPointMapTool().subGeom = qad_utils.getSubGeom(geom, dummy[2])
                  if self.offSet < 0: # richiesta di punto di passaggio
                     self.waitForPassagePt()
                  else:  # richiesta la parte dell'oggetto
                     self.waitForSidePt()
            else:
               # si appresta ad attendere la selezione di un oggetto
               self.waitForObjectSel()

         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI UN PUNTO PER STABILIRE LA PARTE DI OFFSET  (da step = 2)
      elif self.step == 3:
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.multi == False: # default = esci                     
                     self.offsetGeoms()
                     return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None: # oggetto successivo
            # si appresta ad attendere la selezione di un oggetto
            self.waitForObjectSel()
         else:
            if type(value) == unicode:
               if value == QadMsg.get(227): # "Esci"
                  self.offsetGeoms()
                  return True # fine comando
               elif value == QadMsg.get(233): # "MUltiplo"
                  self.multi = True
                  self.waitForSidePt()               
               elif value == QadMsg.get(228): # "ANnulla"
                  self.undoGeomsInCache()               
            elif type(value) == QgsPoint: # se è stato selezionato un punto            
               self.addFeatureCache(value)       

         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI UN PUNTO DI PASSAGGIO DI OFFSET  (da step = 2)
      elif self.step == 4:
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.multi == False: # default = esci                     
                     self.offsetGeoms()
                     return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None: # oggetto successivo
            # si appresta ad attendere la selezione di un oggetto
            self.waitForObjectSel()
         else:
            if type(value) == unicode:
               if value == QadMsg.get(227): # "Esci"
                  self.offsetGeoms()
                  return True # fine comando
               elif value == QadMsg.get(233): # "MUltiplo"
                  self.multi = True
                  self.waitForPassagePt()               
               elif value == QadMsg.get(228): # "ANnulla"
                  self.undoGeomsInCache()               
            elif type(value) == QgsPoint: # se è stato selezionato un punto            
               self.addFeatureCache(value)       

         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI CANCELLAZIONE OGGETTO SORGENTE (da step = 1)
      elif self.step == 5: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
               value = QadMsg.get(231) # "No"   
            else:
               self.setMapTool(self.getPointMapTool()) # riattivo il maptool
               return False
         else: # il valore arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.get(230): # "Sì"
               self.eraseEntity = True
               self.waitForDistance()
            elif value == QadMsg.get(231): # "No"
               self.eraseEntity = False
               self.waitForDistance()
         
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER LUNGHEZZA OFFSET (da step = 1)
      elif self.step == 6: # dopo aver atteso un punto o un numero reale si riavvia il comando
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

         if value == self.firstPt:
            # "\nIl valore deve essere positivo e diverso da zero."
            self.showMsg(QadMsg.get(201))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.get(93)) # "Specificare secondo punto: "
            return False
               
         self.offSet = qad_utils.getDistance(self.firstPt, value)
         self.getPointMapTool().offSet = self.offSet
         QadVariables.set("OFFSETDIST", self.offSet)
         QadVariables.save()
         # si appresta ad attendere la selezione di un oggetto
         self.waitForObjectSel()

         return False
                  
               