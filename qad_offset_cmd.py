# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando OFFSET per fare l'offset di un oggetto
 
                              -------------------
        begin                : 2013-10-04
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


import qad_debug
from qad_offset_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_textwindow import *
from qad_entity import *
from qad_variables import *
import qad_utils
import qad_layer
from qad_rubberband import createRubberBand


# Classe che gestisce il comando OFFSET
class QadOFFSETCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "OFFSET")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runOFFSETCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/offset.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_OFFSET", "Crea cerchi concentrici, linee e curve parallele.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.entity = QadEntity()
      self.subGeom = None
      self.subGeomSelectedPt = None
      self.offSet = QadVariables.get(QadMsg.translate("Environment variables", "OFFSETDIST"))
      self.lastOffSetOnLeftSide = 0
      self.lastOffSetOnRightSide = 0
      self.firstPt = QgsPoint()
      self.eraseEntity = False
      self.multi = False
      self.OnlySegment = False
      self.gapType = QadVariables.get(QadMsg.translate("Environment variables", "OFFSETGAPTYPE"))
      
      self.featureCache = [] # lista di (layer, feature)
      self.undoFeatureCacheIndexes = [] # posizioni in featureCache dei punti di undo
      self.rubberBand = createRubberBand(self.plugIn.canvas, QGis.Line)
      self.rubberBandPolygon = createRubberBand(self.plugIn.canvas, QGis.Polygon)

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
      f = self.entity.getFeature()
      transformedPt = self.mapToLayerCoordinates(layer, newPt)

      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      dummy = qad_utils.closestSegmentWithContext(transformedPt, self.subGeom)
      if self.offSet < 0:
         afterVertex = dummy[2]
         pt = qad_utils.getPerpendicularPointOnInfinityLine(self.subGeom.vertexAt(afterVertex - 1), \
                                                            self.subGeom.vertexAt(afterVertex), \
                                                            transformedPt)
         offSetDistance = qad_utils.getDistance(transformedPt, pt)
      else:        
         offSetDistance = qad_utils.distMapToLayerCoordinates(self.offSet, \
                                                              self.plugIn.canvas,\
                                                              layer)                     
         if self.multi == True:
            if dummy[3] < 0: # alla sinistra
               offSetDistance = offSetDistance + self.lastOffSetOnLeftSide
               self.lastOffSetOnLeftSide = offSetDistance
               self.getPointMapTool().lastOffSetOnLeftSide = self.lastOffSetOnLeftSide                     
            else: # alla destra
               offSetDistance = offSetDistance + self.lastOffSetOnRightSide
               self.lastOffSetOnRightSide = offSetDistance            
               self.getPointMapTool().lastOffSetOnRightSide = self.lastOffSetOnRightSide

      #qad_debug.breakPoint()
      tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                  self.plugIn.canvas,\
                                                                  layer)
      epsg = layer.crs().authid()      
      lines = qad_utils.offSetPolyline(self.subGeom.asPolyline(), epsg, \
                                       offSetDistance, \
                                       "left" if dummy[3] < 0 else "right", \
                                       self.gapType, \
                                       tolerance2ApproxCurve)
      added = False
      for line in lines:        
         if layer.geometryType() == QGis.Polygon:
            if line[0] == line[-1]: # se � una linea chiusa
               offsetGeom = QgsGeometry.fromPolygon([line])
            else:
               offsetGeom = QgsGeometry.fromPolyline(line)
         else:
            offsetGeom = QgsGeometry.fromPolyline(line)

         if offsetGeom.type() == QGis.Line or offsetGeom.type() == QGis.Polygon:           
            offsetFeature = QgsFeature(f)                              
            offsetFeature.setGeometry(offsetGeom)
            self.featureCache.append([layer, offsetFeature])
            self.addFeatureToRubberBand(layer, offsetFeature)            
            added = True           

      if added:      
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
      qad_debug.breakPoint()

      if layer.geometryType() == QGis.Polygon:
         if feature.geometry().type() == QGis.Polygon:
            self.rubberBandPolygon.addGeometry(feature.geometry(), layer)
         else:
            self.rubberBand.addGeometry(feature.geometry(), layer)
      else:
         self.rubberBand.addGeometry(feature.geometry(), layer)
      
      
   #============================================================================
   # refreshRubberBand
   #============================================================================
   def refreshRubberBand(self):
      self.rubberBand.reset(QGis.Line)
      self.rubberBandPolygon.reset(QGis.Polygon)
      for f in self.featureCache:
         layer = f[0]
         feature = f[1]
         if layer.geometryType() == QGis.Polygon:
            #qad_debug.breakPoint()
            if feature.geometry().type() == QGis.Polygon:
               self.rubberBandPolygon.addGeometry(feature.geometry(), layer)
            else:
               self.rubberBand.addGeometry(feature.geometry(), layer)            
         else:
            self.rubberBand.addGeometry(feature.geometry(), layer)            


   #============================================================================
   # offsetGeoms
   #============================================================================
   def offsetGeoms(self, currLayer):
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

      layerList = []
      for featuresLayer in featuresLayers:
         layerList.append(featuresLayer[0])

      PointTempLayer = None
      LineTempLayer = None
      PolygonTempLayer = None
      self.plugIn.beginEditCommand("Feature offseted", layerList)

      for featuresLayer in featuresLayers:
         #qad_debug.breakPoint()
         if featuresLayer[0].crs() != currLayer.crs():
            coordTransform = QgsCoordinateTransform(featuresLayer[0].crs(),\
                                                    currLayer.crs()) # trasformo la geometria
         else:
            coordTransform = None
         
         # filtro le features per tipo
         pointGeoms, lineGeoms, polygonGeoms = qad_utils.filterFeaturesByType(featuresLayer[1], \
                                                                              currLayer.geometryType())
         # aggiungo le features con geometria del tipo corretto
         if currLayer.geometryType() == QGis.Line:
            polygonToLines = []
            # Riduco le geometrie in linee
            for g in polygonGeoms:
               lines = qad_utils.asPointOrPolyline(g)
               for l in lines:
                  if l.type() == QGis.Line:
                      polygonToLines.append(l)
            # plugIn, layer, geoms, coordTransform , refresh, check_validity
            if qad_layer.addGeomsToLayer(self.plugIn, currLayer, polygonToLines, coordTransform, False, False) == False:
               self.plugIn.destroyEditCommand()
               return
               
            del polygonGeoms[:] # svuoto la lista

         # plugIn, layer, features, coordTransform, refresh, check_validity
         if qad_layer.addFeaturesToLayer(self.plugIn, currLayer, featuresLayer[1], coordTransform, False, False) == False:  
            self.plugIn.destroyEditCommand()
            return

         if pointGeoms is not None and len(pointGeoms) > 0 and PointTempLayer is None:
            PointTempLayer = qad_layer.createQADTempLayer(self.plugIn, QGis.Point)
            self.plugIn.addLayerToLastEditCommand("Feature offseted", PointTempLayer)
         
         if lineGeoms is not None and len(lineGeoms) > 0 and LineTempLayer is None:
            LineTempLayer = qad_layer.createQADTempLayer(self.plugIn, QGis.Line)
            self.plugIn.addLayerToLastEditCommand("Feature offseted", LineTempLayer)
            
         if polygonGeoms is not None and len(polygonGeoms) > 0 and PolygonTempLayer is None:
            PolygonTempLayer = qad_layer.createQADTempLayer(self.plugIn, QGis.Polygon)
            self.plugIn.addLayerToLastEditCommand("Feature offseted", PolygonTempLayer)
         
         # aggiungo gli scarti nei layer temporanei di QAD
         # trasformo la geometria in quella dei layer temporanei 
         # plugIn, pointGeoms, lineGeoms, polygonGeoms, coord, refresh
         if qad_layer.addGeometriesToQADTempLayers(self.plugIn, pointGeoms, lineGeoms, polygonGeoms, \
                                                 featuresLayer[0].crs(), False) == False:
            self.plugIn.destroyEditCommand()
            return

      self.plugIn.endEditCommand()

 
   #============================================================================
   # waitForDistance
   #============================================================================
   def waitForDistance(self):      
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_offset_maptool_ModeEnum.ASK_FOR_FIRST_OFFSET_PT)
      self.getPointMapTool().gapType = self.gapType                        

      keyWords = QadMsg.translate("Command_OFFSET", "Punto") + "/" + \
                 QadMsg.translate("Command_OFFSET", "Cancella")                
      if self.offSet < 0:
         default = QadMsg.translate("Command_OFFSET", "Punto")
      else:
         default = self.offSet
      prompt = QadMsg.translate("Command_OFFSET", "Specificare distanza di offset o [{0}] <{1}>: ").format(keyWords, str(default))

      # si appresta ad attendere un punto o enter o una parola chiave o un numero reale     
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT | QadInputTypeEnum.KEYWORDS, \
                   default, \
                   keyWords, \
                   QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)      
      self.step = 1      
   
   #============================================================================
   # waitForObjectSel
   #============================================================================
   def waitForObjectSel(self):      
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_offset_maptool_ModeEnum.ASK_FOR_ENTITY_SELECTION)                                      
      self.lastOffSetOnLeftSide = 0
      self.getPointMapTool().lastOffSetOnLeftSide = self.lastOffSetOnLeftSide
      self.lastOffSetOnRightSide = 0
      self.getPointMapTool().lastOffSetOnRightSide = self.lastOffSetOnRightSide
      
      # "Esci" "ANnulla"      
      keyWords = QadMsg.translate("Command_OFFSET", "Esci") + "/" + \
                 QadMsg.translate("Command_OFFSET", "ANnulla")
      default = QadMsg.translate("Command_OFFSET", "Esci")
      prompt = QadMsg.translate("Command_OFFSET", "Selezionare oggetto di cui eseguire l'offset o [{0}] <{1}>: ").format(keyWords, default)
      
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   default, \
                   keyWords, QadInputModeEnum.NONE)      
      self.step = 2      
        
   #============================================================================
   # waitForSidePt
   #============================================================================
   def waitForSidePt(self):      
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_offset_maptool_ModeEnum.OFFSET_KNOWN_ASK_FOR_SIDE_PT)                                

      if self.multi == False:
         keyWords = QadMsg.translate("Command_OFFSET", "Esci") + "/" + \
                    QadMsg.translate("Command_OFFSET", "MUltiplo") + "/" + \
                    QadMsg.translate("Command_OFFSET", "ANnulla")
         defaultMsg = QadMsg.translate("Command_OFFSET", "Esci")        
         default = QadMsg.translate("Command_OFFSET", "Esci")
      else:
         keyWords = QadMsg.translate("Command_OFFSET", "Esci") + "/" + \
                    QadMsg.translate("Command_OFFSET", "ANnulla")
         defaultMsg = QadMsg.translate("Command_OFFSET", "oggetto successivo")
         default = None

      if self.OnlySegment == False:
         keyWords = keyWords + "/" + \
                    QadMsg.translate("Command_OFFSET", "Segmento")

      prompt = QadMsg.translate("Command_OFFSET", "Specificare punto sul lato di cui eseguire l'offset o [{0}] <{1}>: ")

      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valore nullo non permesso
      self.waitFor(prompt.format(keyWords, defaultMsg), \
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
         keyWords = QadMsg.translate("Command_OFFSET", "Esci") + "/" + \
                    QadMsg.translate("Command_OFFSET", "MUltiplo") + "/" + \
                    QadMsg.translate("Command_OFFSET", "ANnulla")
         defaultMsg = QadMsg.translate("Command_OFFSET", "Esci")        
         default = QadMsg.translate("Command_OFFSET", "Esci")
      else:
         keyWords = QadMsg.translate("Command_OFFSET", "Esci") + "/" + \
                    QadMsg.translate("Command_OFFSET", "ANnulla")
         defaultMsg = QadMsg.translate("Command_OFFSET", "oggetto successivo")
         default = None

      if self.OnlySegment == False:
         keyWords = keyWords + "/" + \
                    QadMsg.translate("Command_OFFSET", "Segmento")

      prompt = QadMsg.translate("Command_OFFSET", "Specificare punto di passaggio o [{0}] <{1}>: ")

      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valore nullo non permesso
      self.waitFor(prompt.format(keyWords, defaultMsg), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   default, \
                   keyWords, QadInputModeEnum.NONE)      
      self.step = 4

   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando

      # il layer corrente deve essere editabile e di tipo linea o poligono
      currLayer, errMsg = qad_layer.getCurrLayerEditable(self.plugIn.canvas, [QGis.Line, QGis.Polygon])
      if currLayer is None:
         self.showErr(errMsg)
         return True # fine comando

      #=========================================================================
      # RICHIESTA DISTANZA DI OFFSET
      if self.step == 0: # inizio del comando
         CurrSettingsMsg = QadMsg.translate("QAD", "\nImpostazioni correnti: ")
         CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_OFFSET", "OFFSETGAPTYPE = ") + str(self.gapType)                        
         if self.gapType == 0:
            CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_OFFSET", " (estende i segmenti)")         
         elif self.gapType == 1:
            CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_OFFSET", " (raccorda i segmenti)")         
         elif self.gapType == 2:
            CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_OFFSET", " (cima i segmenti)")         
         
         self.showMsg(CurrSettingsMsg)         

         self.waitForDistance()
            
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA DISTANZA DI OFFSET (da step = 0)
      elif self.step == 1: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool � stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.offSet < 0:
                     value = QadMsg.translate("Command_OFFSET", "Punto")
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
            if value == QadMsg.translate("Command_OFFSET", "Punto"):
               self.offSet = -1
               self.getPointMapTool().offSet = self.offSet
               QadVariables.set(QadMsg.translate("Environment variables", "OFFSETDIST"), self.offSet)
               QadVariables.save()               
               # si appresta ad attendere la selezione di un oggetto
               self.waitForObjectSel()
            elif value == QadMsg.translate("Command_OFFSET", "Cancella"):
               keyWords = QadMsg.translate("QAD", "S�") + "/" + \
                          QadMsg.translate("QAD", "No")                               
              
               if self.eraseEntity == True:
                  default = QadMsg.translate("QAD", "S�")
               else: 
                  default = QadMsg.translate("QAD", "No")
               prompt = QadMsg.translate("Command_OFFSET", "Cancellare l'oggetto sorgente dopo l'offset ? [{0}] <{1}>: ").format(keyWords, default)
                   
               # si appresta ad attendere enter o una parola chiave         
               # msg, inputType, default, keyWords, nessun controllo
               self.waitFor(prompt, \
                            QadInputTypeEnum.KEYWORDS, \
                            default, \
                            keyWords, QadInputModeEnum.NONE)
               self.step = 5
            elif value == QadMsg.translate("Command_OFFSET", "MUltiplo"):
               self.multi = True
               self.waitForBasePt()                         
         elif type(value) == QgsPoint: # se � stato inserito il primo punto per il calcolo della distanza
            self.firstPt.set(value.x(), value.y())
            # imposto il map tool
            self.getPointMapTool().firstPt = self.firstPt           
            self.getPointMapTool().setMode(Qad_offset_maptool_ModeEnum.FIRST_OFFSET_PT_KNOWN_ASK_FOR_SECOND_PT)
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_OFFSET", "Specificare secondo punto: "))           
            self.step = 6
         elif type(value) == float:
            self.offSet = value
            self.getPointMapTool().offSet = self.offSet
            QadVariables.set(QadMsg.translate("Environment variables", "OFFSETDIST"), self.offSet)
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
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool � stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = QadMsg.translate("Command_OFFSET", "Esci")
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               entity = self.getPointMapTool().entity
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
         
         if type(value) == unicode:
            if value == QadMsg.translate("Command_OFFSET", "Esci"):
               self.offsetGeoms(currLayer)
               return True
            elif value == QadMsg.translate("Command_OFFSET", "ANnulla"):
               self.undoGeomsInCache()
               # si appresta ad attendere la selezione di un oggetto
               self.waitForObjectSel()
         elif type(value) == QgsPoint: # se � stato selezionato un punto
            if entity is not None and entity.isInitialized(): # se � stata selezionata una entit�
               self.entity.set(entity.layer, entity.featureId)
               self.getPointMapTool().layer = self.entity.layer
               geom = entity.getGeometry()
               transformedPt = self.mapToLayerCoordinates(self.entity.layer, value)

               # ritorna una tupla (<The squared cartesian distance>,
               #                    <minDistPoint>
               #                    <afterVertex>
               #                    <leftOf>)
               dummy = qad_utils.closestSegmentWithContext(transformedPt, geom)
               if dummy[2] is not None:
                  # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
                  # la posizione � espressa con una lista (<index ogg. princ> [<index ogg. sec.>])
                  self.subGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])[0]
                  self.subGeomSelectedPt = QgsPoint(transformedPt)
                  
                  self.getPointMapTool().subGeom = self.subGeom
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
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool � stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.multi == False: # default = esci                     
                     self.offsetGeoms(currLayer)
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
               if value == QadMsg.translate("Command_OFFSET", "Esci"):
                  self.offsetGeoms(currLayer)
                  return True # fine comando
               elif value == QadMsg.translate("Command_OFFSET", "MUltiplo"):
                  self.multi = True
                  self.waitForSidePt()               
               elif value == QadMsg.translate("Command_OFFSET", "ANnulla"):
                  self.undoGeomsInCache()               
                  # si appresta ad attendere la selezione di un oggetto
                  self.waitForObjectSel()
               elif value == QadMsg.translate("Command_OFFSET", "Segmento"):
                  self.OnlySegment = True   
                  linearObject = qad_utils.QadLinearObject()
                  if linearObject.setByClosestSegmentOfGeom(self.subGeomSelectedPt, self.subGeom) == True:
                     self.subGeom = QgsGeometry.fromPolyline(linearObject.asPolyline())
                     self.getPointMapTool().subGeom = self.subGeom
                  
                  self.waitForSidePt()                  
            elif type(value) == QgsPoint: # se � stato selezionato un punto            
               self.addFeatureCache(value) 
               if self.multi == False:
                  # si appresta ad attendere la selezione di un oggetto
                  self.waitForObjectSel()
               else:
                  # richiesta la parte dell'oggetto
                  self.waitForSidePt()

         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI UN PUNTO DI PASSAGGIO DI OFFSET  (da step = 2)
      elif self.step == 4:
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool � stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.multi == False: # default = esci                     
                     self.offsetGeoms(currLayer)
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
               if value == QadMsg.translate("Command_OFFSET", "Esci"):
                  self.offsetGeoms(currLayer)
                  return True # fine comando
               elif value == QadMsg.translate("Command_OFFSET", "MUltiplo"):
                  self.multi = True
                  self.waitForPassagePt()     
               elif value == QadMsg.translate("Command_OFFSET", "ANnulla"):
                  self.undoGeomsInCache()               
                  # si appresta ad attendere la selezione di un oggetto
                  self.waitForObjectSel()
               elif value == QadMsg.translate("Command_OFFSET", "Segmento"):
                  self.OnlySegment = True                  
                  linearObject = qad_utils.QadLinearObject()
                  if linearObject.setByClosestSegmentOfGeom(self.subGeomSelectedPt, self.subGeom) == True:
                     self.subGeom = QgsGeometry.fromPolyline(linearObject.asPolyline())
                     self.getPointMapTool().subGeom = self.subGeom
                  
                  self.waitForPassagePt()     
            elif type(value) == QgsPoint: # se � stato selezionato un punto            
               self.addFeatureCache(value)       
               if self.multi == False:
                  # si appresta ad attendere la selezione di un oggetto
                  self.waitForObjectSel()
               else:
                  # richiesta di punto di passaggio
                  self.waitForPassagePt()

         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI CANCELLAZIONE OGGETTO SORGENTE (da step = 1)
      elif self.step == 5: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
               value = QadMsg.translate("QAD", "No")   
            else:
               self.setMapTool(self.getPointMapTool()) # riattivo il maptool
               return False
         else: # il valore arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("QAD", "S�"):
               self.eraseEntity = True
               self.waitForDistance()
            elif value == QadMsg.translate("QAD", "No"):
               self.eraseEntity = False
               self.waitForDistance()
         
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER LUNGHEZZA OFFSET (da step = 1)
      elif self.step == 6: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool � stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value == self.firstPt:
            self.showMsg(QadMsg.translate("QAD", "\nIl valore deve essere positivo e diverso da zero."))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_OFFSET", "Specificare secondo punto: "))
            return False
               
         self.offSet = qad_utils.getDistance(self.firstPt, value)
         self.getPointMapTool().offSet = self.offSet
         QadVariables.set(QadMsg.translate("Environment variables", "OFFSETDIST"), self.offSet)
         QadVariables.save()
         # si appresta ad attendere la selezione di un oggetto
         self.waitForObjectSel()

         return False
                  
               