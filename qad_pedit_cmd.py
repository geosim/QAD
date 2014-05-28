# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando PEDIT per editare una polilinea o un poligono esistente
 
                              -------------------
        begin                : 2014-01-13
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


import qad_debug
from qad_generic_cmd import QadCommandClass
from qad_snapper import *
from qad_pedit_maptool import *
from qad_ssget_cmd import QadSSGetClass
from qad_msg import QadMsg
from qad_textwindow import *
import qad_utils
import qad_layer
from qad_variables import *
from qad_snappointsdisplaymanager import *


# Classe che gestisce il comando PEDIT
class QadPEDITCommandClass(QadCommandClass):

   def getName(self):
      return QadMsg.translate("Command_list", "EDITPL")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runPEDITCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/pedit.png")
   
   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_PEDIT", "Modifica polilinee o poligoni esistenti.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.SSGetClass = QadSSGetClass(plugIn)
      self.SSGetClass.onlyEditableLayers = True
      self.SSGetClass.checkPointLayer = False # scarto i punto
      self.SSGetClass.checkLineLayer = True
      
      self.entitySet = QadEntitySet()
      self.entity = QadEntity()
      self.atSubGeom = None
      self.linearObjectList = qad_utils.QadLinearObjectList()
      self.joinToleranceDist = plugIn.joinToleranceDist
      self.joinMode = plugIn.joinMode

      self.editVertexMode = None
      self.nOperationsToUndo = 0
         
      self.firstPt = QgsPoint()
      self.vertexAt = 0
      self.secondVertexAt = 0
      self.after = True
      self.snapPointsDisplayManager = QadSnapPointsDisplayManager(self.plugIn.canvas)
      self.snapPointsDisplayManager.setIconSize(QadVariables.get(QadMsg.translate("Environment variables", "OSSIZE")))
      self.snapPointsDisplayManager.setColor(QColor(QadVariables.get(QadMsg.translate("Environment variables", "OSCOLOR"))))
   
   def __del__(self):
      QadCommandClass.__del__(self)
      del self.SSGetClass
      self.entity.deselectOnLayer()
      self.entitySet.deselectOnLayer()
      del self.snapPointsDisplayManager
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 2: # quando si è in fase di selezione entità
         return self.SSGetClass.getPointMapTool()           
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_pedit_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None


   #============================================================================
   # setEntityInfo
   #============================================================================
   def setEntityInfo(self, layer, featureId, point):
      """
      Setta self.entity, self.atSubGeom, self.linearObjectList
      """
      transformedPt = self.mapToLayerCoordinates(layer, point)
      
      self.entity.set(layer, featureId)
      geom = self.entity.getGeometry()
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      dummy = qad_utils.closestSegmentWithContext(transformedPt, geom)
      if dummy[2] is not None:
         # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
         subGeom, self.atSubGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])
         #qad_debug.breakPoint()               
         self.linearObjectList.fromPolyline(subGeom.asPolyline())
         if self.linearObjectList.getCircle() is not None:
            self.entity.deselectOnLayer()
            return False
         else:
            self.entity.selectOnLayer(False) # non incrementale
            return True
      else:
         self.entity.deselectOnLayer()
         return False


   #============================================================================
   # getNextVertex
   #============================================================================
   def getNextVertex(self, vertexAt):
      """
      Ritorna la posizione del vertice successivo rispetto vertexAt
      """
      tot = self.linearObjectList.qty()
      if vertexAt == tot - 1: # se penultimo punto
         return 0 if self.linearObjectList.isClosed() else vertexAt + 1
      elif vertexAt < tot: # se non è ultimo punto
         return vertexAt + 1
      else:
         return vertexAt


   #============================================================================
   # getPrevVertex
   #============================================================================
   def getPrevVertex(self, vertexAt):
      """
      Ritorna la posizione del vertice precedente rispetto vertexAt
      """
      if vertexAt == 0: # se primo punto
         if self.linearObjectList.isClosed():
            return self.linearObjectList.qty() - 1
         else:
            return vertexAt
      else:
         return vertexAt - 1


   #============================================================================
   # displayVertexMarker
   #============================================================================
   def displayVertexMarker(self, vertexAt):
      if vertexAt == self.linearObjectList.qty():
         pt = self.linearObjectList.getLinearObjectAt(-1).getEndPt()
      else:
         pt = self.linearObjectList.getLinearObjectAt(vertexAt).getStartPt()
         
      # visualizzo il punto di snap
      transformedPt = self.plugIn.canvas.mapRenderer().layerToMapCoordinates(self.entity.layer, pt)
      snapPoint = dict()
      snapPoint[QadSnapTypeEnum.END] = [transformedPt]
      self.snapPointsDisplayManager.show(snapPoint)
         

   #============================================================================
   # setClose
   #============================================================================
   def setClose(self, toClose):
      #qad_debug.breakPoint()

      if self.entity.isInitialized(): # selezionato solo un oggetto
         layer = self.entity.layer
         self.plugIn.beginEditCommand("Feature edited", layer)
         
         tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                     self.plugIn.canvas,\
                                                                     layer)                              
         f = self.entity.getFeature()
         geom = f.geometry() 
         
         self.linearObjectList.setClose(toClose)
         pts = self.linearObjectList.asPolyline(tolerance2ApproxCurve)
         
         if layer.geometryType() == QGis.Line:
            updGeom = qad_utils.setSubGeom(geom, QgsGeometry.fromPolyline(pts), self.atSubGeom)
            f.setGeometry(updGeom)   
            # plugIn, layer, feature, refresh, check_validity
            if qad_layer.updateFeatureToLayer(self.plugIn, layer, f, False, False) == False:
               self.plugIn.destroyEditCommand()
               return
         else: # layer di tipo poligono
            if toClose == False: # apri
               # aggiungo le linee nei layer temporanei di QAD
               LineTempLayer = qad_layer.createQADTempLayer(self.plugIn, QGis.Line)
               self.plugIn.addLayerToLastEditCommand("Feature edited", LineTempLayer)
                       
               lineGeoms = [QgsGeometry.fromPolyline(pts)]
               
               # trasformo la geometria in quella dei layer temporanei
               # plugIn, pointGeoms, lineGeoms, polygonGeoms, coord, refresh
               if qad_layer.addGeometriesToQADTempLayers(self.plugIn, None, lineGeoms, None, \
                                                         layer.crs(), False) == False:
                  self.plugIn.destroyEditCommand()
                  return
               
               updGeom = qad_utils.delSubGeom(f.geometry(), atSubGeom)         

               if updGeom is None or updGeom.isGeosEmpty(): # da cancellare
                  # plugIn, layer, feature id, refresh
                  if qad_layer.deleteFeatureToLayer(self.plugIn, layer, f.id(), False) == False:
                     self.plugIn.destroyEditCommand()
                     return
               else:
                  editedFeature = QgsFeature(f)
                  editedFeature.setGeometry(updGeom)
                  # plugIn, layer, feature, refresh, check_validity
                  if qad_layer.updateFeatureToLayer(self.plugIn, layer, editedFeature, False, False) == False:
                     self.plugIn.destroyEditCommand()
                     return
      else:         
         self.plugIn.beginEditCommand("Feature edited", self.entitySet.getLayerList())
         for layerEntitySet in self.entitySet.layerEntitySetList:
            layer = layerEntitySet.layer
            tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                        self.plugIn.canvas,\
                                                                        layer)                              
            
            updObjects = []
            for featureId in layerEntitySet.featureIds:
               f = layerEntitySet.getFeature(featureId)               
               updGeom = qad_utils.closeQgsGeometry(f.geometry(), toClose, tolerance2ApproxCurve)
               if updGeom is not None:
                  updFeature = QgsFeature(f)
                  updFeature.setGeometry(updGeom)
                  updObjects.append(updFeature)  
         
            # plugIn, layer, features, refresh, check_validity
            if qad_layer.updateFeaturesToLayer(self.plugIn, layer, updObjects, False, False) == False:
               self.plugIn.destroyEditCommand()
               return
   
      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1
      

   #============================================================================
   # reverse
   #============================================================================
   def reverse(self):
      #qad_debug.breakPoint()      
      if self.entity.isInitialized(): # selezionato solo un oggetto
         layer = self.entity.layer
         self.plugIn.beginEditCommand("Feature edited", layer)

         tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                     self.plugIn.canvas,\
                                                                     self.entity.layer)                              
         f = self.entity.getFeature()
         geom = f.geometry() 

         self.linearObjectList.reverse()
         updSubGeom = QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve))
         updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
         if updGeom is not None:
            f.setGeometry(updGeom)   
            # plugIn, layer, feature, refresh, check_validity
            if qad_layer.updateFeatureToLayer(self.plugIn, self.entity.layer, f, False, False) == False:
               self.plugIn.destroyEditCommand()
               return
      else:
         self.plugIn.beginEditCommand("Feature edited", self.entitySet.getLayerList())

         for layerEntitySet in self.entitySet.layerEntitySetList:
            tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                        self.plugIn.canvas,\
                                                                        layerEntitySet.layer)                              
            
            updObjects = []
            for featureId in layerEntitySet.featureIds:
               f = layerEntitySet.getFeature(featureId)               
               updGeom = qad_utils.reverseQgsGeometry(f.geometry(), tolerance2ApproxCurve)
               if updGeom is not None:
                  updFeature = QgsFeature(f)
                  updFeature.setGeometry(updGeom)
                  updObjects.append(updFeature)      
         
            # plugIn, layer, features, refresh, check_validity
            if qad_layer.updateFeaturesToLayer(self.plugIn, layerEntitySet.layer, updObjects, False, False) == False:
               self.plugIn.destroyEditCommand()
               return
   
      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1
      

   #============================================================================
   # join
   #============================================================================
   def join(self):
      #qad_debug.breakPoint()
      tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
      epsg = self.plugIn.canvas.currentLayer().crs().authid()
      # creo un layer temporaneo in memoria con campo numerico per 
      # contenere la posizione dell'entità originale nella lista newIdFeatureList
      vectorLayer = QgsVectorLayer("LineString?crs=%s&index=yes" % epsg, "QAD_SelfJoinLines", "memory")
      
      provider = vectorLayer.dataProvider()
      provider.addAttributes([QgsField('index', QVariant.Int, 'Int')])
      vectorLayer.updateFields()

      if vectorLayer.startEditing() == False:
         return

      # inserisco nel layer i vari oggetti lineari (WKBLineString)
      layerList = []
      newIdFeatureList = [] # lista ((newId - layer - feature) ...)
      i = 0
      
      if self.entity.isInitialized(): # selezionato solo un oggetto
         self.entitySet.removeEntity(self.entity) # elimino dal gruppo l'entità da unire
         
         # aggiungo l'entità a cui unirsi
         layer = self.entity.layer
         
         if layer.geometryType() != QGis.Line:
            return

         if layer.crs() != self.plugIn.canvas.currentLayer().crs():
            coordTransform = QgsCoordinateTransform(layer.crs(),\
                                                    self.plugIn.canvas.currentLayer().crs()) # trasformo la geometria
         else:
            coordTransform = None

         tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                     self.plugIn.canvas,\
                                                                     self.entity.layer)                              
         
         f = self.entity.getFeature()
         if f.geometry().wkbType() != QGis.WKBLineString:
            return
         newFeature = QgsFeature()
         newFeature.initAttributes(1)
         newFeature.setAttribute(0, 0)
         newFeature.setGeometry(QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve)))
         i = i + 1
         if coordTransform is not None:
            newFeature.geometry().transform(coordTransform)            
         
         if vectorLayer.addFeature(newFeature) == False:
            vectorLayer.destroyEditCommand()
            return
         newIdFeatureList.append([newFeature.id(), layer, f])
      
      
      for layerEntitySet in self.entitySet.layerEntitySetList:
         layer = layerEntitySet.layer
         
         if layer.geometryType() != QGis.Line:
            continue
         
         if layer.crs() != self.plugIn.canvas.currentLayer().crs():
            coordTransform = QgsCoordinateTransform(layer.crs(),\
                                                    self.plugIn.canvas.currentLayer().crs()) # trasformo la geometria
         else:
            coordTransform = None
         
         for f in layerEntitySet.getFeatureCollection():
            if f.geometry().wkbType() != QGis.WKBLineString:
               continue
            newFeature = QgsFeature()
            newFeature.initAttributes(1)
            newFeature.setAttribute(0, i)
            newFeature.setGeometry(f.geometry())
            i = i + 1
            if coordTransform is not None:
               newFeature.geometry().transform(coordTransform)            
            
            if vectorLayer.addFeature(newFeature) == False:
               vectorLayer.destroyEditCommand()
               return
            newIdFeatureList.append([newFeature.id(), layer, f])
               
      vectorLayer.endEditCommand();
      vectorLayer.updateExtents()
        
      if provider.capabilities() & QgsVectorDataProvider.CreateSpatialIndex:
         provider.createSpatialIndex()

      deleteFeatures = []
      if self.entity.isInitialized(): # selezionato solo un oggetto
         featureIdToJoin = newIdFeatureList[0][0]
         #                         featureIdToJoin, vectorLayer, tolerance2ApproxCurve, toleranceDist, mode     
         deleteFeatures.extend(qad_utils.joinFeatureInVectorLayer(featureIdToJoin, vectorLayer, \
                                                                  tolerance2ApproxCurve, \
                                                                  self.joinToleranceDist, self.joinMode))
      else:         
         i = 0 
         tot = len(newIdFeatureList)
         while i < tot:
            #qad_debug.breakPoint()
            featureIdToJoin = newIdFeatureList[i][0]
            #                         featureIdToJoin, vectorLayer, tolerance2ApproxCurve, toleranceDist, mode     
            deleteFeatures.extend(qad_utils.joinFeatureInVectorLayer(featureIdToJoin, vectorLayer, \
                                                                     tolerance2ApproxCurve, \
                                                                     self.joinToleranceDist, self.joinMode))
            i = i + 1
                       
      self.plugIn.beginEditCommand("Feature edited", self.entitySet.getLayerList())

      if self.entity.isInitialized(): # selezionato solo un oggetto
         newFeature = qad_utils.getFeatureById(vectorLayer, newIdFeatureList[0][0])         
         layer = newIdFeatureList[0][1]
         f = newIdFeatureList[0][2]         
         f.setGeometry(qad_utils.setSubGeom(f.geometry(), newFeature.geometry(), self.atSubGeom))
         # plugIn, layer, feature, refresh, check_validity
         if qad_layer.updateFeatureToLayer(self.plugIn, layer, f, False, False) == False:
            self.plugIn.destroyEditCommand()
            return
      else:      
         # aggiorno la geometria delle features rimaste nel layer temporaneo
         # fetchAttributes, fetchGeometry, rectangle, useIntersect             
         for newFeature in vectorLayer.getFeatures(qad_utils.getFeatureRequest([], True, None, False)):
            layer = newIdFeatureList[newFeature['index']][1]
            f = newIdFeatureList[newFeature['index']][2]
            f.setGeometry(newFeature.geometry())
               
            # plugIn, layer, feature, refresh, check_validity
            if qad_layer.updateFeatureToLayer(self.plugIn, layer, f, False, False) == False:
               self.plugIn.destroyEditCommand()
               return
                          
      # cancello le features rimosse dal layer temporaneo
      for newFeature in deleteFeatures:
         layer = newIdFeatureList[newFeature['index']][1]
         f = newIdFeatureList[newFeature['index']][2]                          
         # plugIn, layer, feature id, refresh
         if qad_layer.deleteFeatureToLayer(self.plugIn, layer, f.id(), False) == False:
            self.plugIn.destroyEditCommand()
            return      
   
      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1


   #============================================================================
   # curve
   #============================================================================
   def curve(self, toCurve):
      #qad_debug.breakPoint()      
      if self.entity.isInitialized(): # selezionato solo un oggetto
         layer = self.entity.layer
         self.plugIn.beginEditCommand("Feature edited", layer)

         tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                     self.plugIn.canvas,\
                                                                     self.entity.layer)                              
         f = self.entity.getFeature()
         geom = f.geometry() 

         self.linearObjectList.curve(toCurve)
         updSubGeom = QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve))
         updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
         if updGeom is not None:
            f.setGeometry(updGeom)   
            # plugIn, layer, feature, refresh, check_validity
            if qad_layer.updateFeatureToLayer(self.plugIn, self.entity.layer, f, False, False) == False:
               self.plugIn.destroyEditCommand()
               return
      else:
         self.plugIn.beginEditCommand("Feature edited", self.entitySet.getLayerList())

         for layerEntitySet in self.entitySet.layerEntitySetList:
            tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                        self.plugIn.canvas,\
                                                                        layerEntitySet.layer)                              
            
            updObjects = []
            for featureId in layerEntitySet.featureIds:
               f = layerEntitySet.getFeature(featureId)               
               updGeom = qad_utils.curveQgsGeometry(f.geometry(), toCurve, tolerance2ApproxCurve)
               if updGeom is not None:
                  updFeature = QgsFeature(f)
                  updFeature.setGeometry(updGeom)
                  updObjects.append(updFeature)      
         
            # plugIn, layer, features, refresh, check_validity
            if qad_layer.updateFeaturesToLayer(self.plugIn, layerEntitySet.layer, updObjects, False, False) == False:
               self.plugIn.destroyEditCommand()
               return
   
      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1


   #============================================================================
   # insertVertexAt
   #============================================================================
   def insertVertexAt(self, pt):         
      layer = self.entity.layer

      tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                  self.plugIn.canvas,\
                                                                  self.entity.layer)                              
      #qad_debug.breakPoint()
      f = self.entity.getFeature()
      geom = f.geometry() 

      newPt = self.mapToLayerCoordinates(layer, pt)

      if self.after: # dopo
         if self.vertexAt == self.linearObjectList.qty() and self.linearObjectList.isClosed():            
            self.linearObjectList.insertPoint(0, newPt)
         else:
            self.linearObjectList.insertPoint(self.vertexAt, newPt)
      else: # prima
         if self.vertexAt == 0 and self.linearObjectList.isClosed():
            self.linearObjectList.insertPoint(self.linearObjectList.qty() - 1, newPt)
         else:
            self.linearObjectList.insertPoint(self.vertexAt - 1, newPt)
               
      updSubGeom = QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve))
      updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
      if updGeom is None:
         return
      f.setGeometry(updGeom)
      
      self.plugIn.beginEditCommand("Feature edited", layer)
   
      # plugIn, layer, feature, refresh, check_validity
      if qad_layer.updateFeatureToLayer(self.plugIn, layer, f, False, False) == False:
         self.plugIn.destroyEditCommand()
         return

      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1


   #============================================================================
   # moveVertexAt
   #============================================================================
   def moveVertexAt(self, pt):         
      layer = self.entity.layer

      tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                  self.plugIn.canvas,\
                                                                  self.entity.layer)                              
      f = self.entity.getFeature()
      geom = f.geometry() 

      newPt = self.mapToLayerCoordinates(layer, pt)

      #qad_debug.breakPoint()
      self.linearObjectList.movePoint(self.vertexAt, newPt)
               
      updSubGeom = QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve))
      updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
      if updGeom is None:
         return
      f.setGeometry(updGeom)
         
      self.plugIn.beginEditCommand("Feature edited", layer)
      
      # plugIn, layer, feature, refresh, check_validity
      if qad_layer.updateFeatureToLayer(self.plugIn, layer, f, False, False) == False:
         self.plugIn.destroyEditCommand()
         return

      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1


   #============================================================================
   # straightenFromVertexAtToSecondVertexAt
   #============================================================================
   def straightenFromVertexAtToSecondVertexAt(self):
      if self.vertexAt == self.secondVertexAt:
         return
               
      layer = self.entity.layer
      tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                  self.plugIn.canvas,\
                                                                  self.entity.layer)                              
      f = self.entity.getFeature()
      geom = f.geometry() 

      #qad_debug.breakPoint()     
      if self.vertexAt < self.secondVertexAt:
         firstPt = self.linearObjectList.getPointAtVertex(self.vertexAt)
         secondPt = self.linearObjectList.getPointAtVertex(self.secondVertexAt)
         for i in xrange(self.vertexAt, self.secondVertexAt, 1):
            self.linearObjectList.remove(self.vertexAt)
         self.linearObjectList.insert(self.vertexAt, [firstPt, secondPt])
      elif self.vertexAt > self.secondVertexAt:
         if self.linearObjectList.isClosed():
            firstPt = self.linearObjectList.getPointAtVertex(self.vertexAt)
            secondPt = self.linearObjectList.getPointAtVertex(self.secondVertexAt)
            for i in xrange(self.vertexAt, self.linearObjectList.qty(), 1):
               self.linearObjectList.remove(self.vertexAt)
            for i in xrange(0, self.secondVertexAt, 1):
               self.linearObjectList.remove(0)
            
            self.linearObjectList.insert(self.vertexAt, [firstPt, secondPt])
         else:
            firstPt = self.linearObjectList.getPointAtVertex(self.secondVertexAt)
            secondPt = self.linearObjectList.getPointAtVertex(self.vertexAt)
            for i in xrange(self.secondVertexAt, self.vertexAt, 1):
               self.linearObjectList.remove(self.secondVertexAt)
            self.linearObjectList.insert(self.secondVertexAt, [firstPt, secondPt])
                       
      updSubGeom = QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve))
      updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
      if updGeom is None:
         return
      f.setGeometry(updGeom)   
      
      self.plugIn.beginEditCommand("Feature edited", layer)
            
      # plugIn, layer, feature, refresh, check_validity
      if qad_layer.updateFeatureToLayer(self.plugIn, layer, f, False, False) == False:
         self.plugIn.destroyEditCommand()
         return

      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1


   #============================================================================
   # breakFromVertexAtToSecondVertexAt
   #============================================================================
   def breakFromVertexAtToSecondVertexAt(self):
      layer = self.entity.layer

      tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                  self.plugIn.canvas,\
                                                                  self.entity.layer)                              
      f = self.entity.getFeature()
      geom = f.geometry() 

      #qad_debug.breakPoint()
      firstPt = self.linearObjectList.getPointAtVertex(self.vertexAt)
      secondPt = self.linearObjectList.getPointAtVertex(self.secondVertexAt)

      result = qad_utils.breakQgsGeometry(layer, QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve)), \
                                          firstPt, secondPt, \
                                          tolerance2ApproxCurve)                  
      if result is None:
         return
      
      line1 = result[0]
      line2 = result[1]
      atSubGeom = result[2]
      
      updGeom = qad_utils.setSubGeom(geom, line1, self.atSubGeom)
      if updGeom is None:
         return
      f.setGeometry(updGeom)   

      self.plugIn.beginEditCommand("Feature edited", layer)
      
      # plugIn, layer, feature, refresh, check_validity
      if qad_layer.updateFeatureToLayer(self.plugIn, self.entity.layer, f, False, False) == False:
         self.plugIn.destroyEditCommand()
         return
      
      if line2 is not None:
         brokenFeature2 = QgsFeature(f)      
         brokenFeature2.setGeometry(line2)
         # plugIn, layer, feature, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(self.plugIn, layer, brokenFeature2, None, False, False) == False:
            self.plugIn.destroyEditCommand()
            return            

      self.linearObjectList.fromPolyline(line1.asPolyline())
      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1


   #============================================================================
   # waitForEntsel
   #============================================================================
   def waitForEntsel(self):      
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_ENTITY_SEL)
                        
      keyWords = QadMsg.translate("Command_PEDIT", "Ultimo") + " " + \
                 QadMsg.translate("Command_PEDIT", "Multiplo")
               
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valore nullo non permesso
      self.waitFor(QadMsg.translate("Command_PEDIT", "Selezionare polilinea o [Multiplo]: "), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NOT_NULL)      
      self.step = 1
      

   #============================================================================
   # WaitForMainMenu
   #============================================================================
   def WaitForMainMenu(self):
      #qad_debug.breakPoint()
      # verifico se ci sono layer di tipo linea
      line = False
      if self.entity.isInitialized(): # selezionato solo un oggetto
         if self.entity.layer.geometryType() == QGis.Line:
            line = True
      else:            
         layerList = self.entitySet.getLayerList()
         for layer in layerList:
            if layer.geometryType() == QGis.Line:
               line = True
               break

      if line == True: # se ci sono dei layer linea
         if self.entity.isInitialized(): # selezionato solo un oggetto
            if self.linearObjectList.isClosed(): # se è chiusa
               keyWords = QadMsg.translate("Command_PEDIT", "Apri") + " "
               msg = QadMsg.translate("Command_PEDIT", "Apri") + "/"
            else:
               keyWords = QadMsg.translate("Command_PEDIT", "Chiudi") + " "
               msg = QadMsg.translate("Command_PEDIT", "Chiudi") + "/"
         else: # selezionati più oggetti
            keyWords = QadMsg.translate("Command_PEDIT", "Chiudi") + " " + \
                       QadMsg.translate("Command_PEDIT", "Apri") + " "
            msg = QadMsg.translate("Command_PEDIT", "Chiudi") + "/" + \
                  QadMsg.translate("Command_PEDIT", "Apri") + "/"
                  
         keyWords = keyWords + QadMsg.translate("Command_PEDIT", "Unisci") + " "
         msg = msg + QadMsg.translate("Command_PEDIT", "Unisci") + "/"
      else: # se non ci sono dei layer linea
         keyWords = ""
         msg = ""

      if self.entity.isInitialized(): # selezionato solo un oggetto
         keyWords = keyWords + QadMsg.translate("Command_PEDIT", "Edita") + " "
         msg = msg + QadMsg.translate("Command_PEDIT", "Edita vertici") + "/"
         
      keyWords = keyWords + QadMsg.translate("Command_PEDIT", "ADatta") + " " + \
                            QadMsg.translate("Command_PEDIT", "Rettifica") + " " + \
                            QadMsg.translate("Command_PEDIT", "Inverti") + " " + \
                            QadMsg.translate("Command_PEDIT", "ANnulla")
      msg = msg + QadMsg.translate("Command_PEDIT", "ADatta") + "/" + \
                  QadMsg.translate("Command_PEDIT", "Rettifica") + "/" + \
                  QadMsg.translate("Command_PEDIT", "Inverti") + "/" + \
                  QadMsg.translate("Command_PEDIT", "ANnulla")
      
      self.step = 3
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.NONE)
      # si appresta ad attendere enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(QadMsg.translate("Command_PEDIT", "Digitare un'opzione [{0}]: ").format(msg), \
                   QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)
      return False
      

   #============================================================================
   # WaitForJoin
   #============================================================================
   def WaitForJoin(self):
      CurrSettingsMsg = QadMsg.translate("QAD", "\nImpostazioni correnti: ")
      CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_PEDIT", "Tipo di unione = ")                        
      if self.joinMode == 1:
         CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_PEDIT", "estende i segmenti")         
      elif self.joinMode == 2:
         CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_PEDIT", "aggiunge segmenti")         
      elif self.joinMode == 3:
         CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_PEDIT", "estende e aggiunge segmenti")         
      
      self.showMsg(CurrSettingsMsg)
      self.waitForDistance()       
        

   #============================================================================
   # waitForDistance
   #============================================================================
   def waitForDistance(self):      
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_FIRST_TOLERANCE_PT)

      keyWords = QadMsg.translate("Command_PEDIT", "Tipo")                 
      msg = QadMsg.translate("Command_PEDIT", "Specificare distanza di approssimazione o [Tipo unione] <{0}>: ")

      # si appresta ad attendere un punto o enter o una parola chiave o un numero reale     
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg.format(str(self.joinToleranceDist)), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT | QadInputTypeEnum.KEYWORDS, \
                   self.joinToleranceDist, \
                   keyWords, \
                   QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_NEGATIVE)      
      self.step = 4      
      
        
   #============================================================================
   # waitForJoinType
   #============================================================================
   def waitForJoinType(self):      
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.NONE)

      keyWords = QadMsg.translate("Command_PEDIT", "Estendi") + " " + \
                 QadMsg.translate("Command_PEDIT", "Aggiungi") + " " + \
                 QadMsg.translate("Command_PEDIT", "ENtrambe")
      msg = QadMsg.translate("Command_PEDIT", "Specificare tipo di unione [Estendi/Aggiungi/ENtrambe] <{0}>: ")
      if self.joinMode == 1:
         default = QadMsg.translate("Command_PEDIT", "Estendi")
      elif self.joinMode == 2:
         default = QadMsg.translate("Command_PEDIT", "Aggiungi")
      elif self.joinMode == 3:
         default = QadMsg.translate("Command_PEDIT", "ENtrambe")

      # si appresta ad attendere un punto o enter o una parola chiave o un numero reale     
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg.format(default), QadInputTypeEnum.KEYWORDS, default, \
                   keyWords, QadInputModeEnum.NOT_NULL)      
      self.step = 6


   #============================================================================
   # WaitForVertexEditingMenu
   #============================================================================
   def WaitForVertexEditingMenu(self):
      #qad_debug.breakPoint()
      self.getPointMapTool().setLinearObjectList(self.linearObjectList, self.entity.layer)            
      
      self.displayVertexMarker(self.vertexAt)
      
      keyWords = QadMsg.translate("Command_PEDIT", "Seguente") + " " + \
                 QadMsg.translate("Command_PEDIT", "Precedente")
      msg = QadMsg.translate("Command_PEDIT", "Seguente") + "/" + \
            QadMsg.translate("Command_PEDIT", "Precedente")
      
      if self.entity.layer.geometryType() == QGis.Line:
         keyWords = keyWords + " "  + QadMsg.translate("Command_PEDIT", "Dividi")
         msg = msg + "/" + QadMsg.translate("Command_PEDIT", "Dividi")

      keyWords = keyWords + " "  + QadMsg.translate("Command_PEDIT", "Inserisci") + \
                            " "  + QadMsg.translate("Command_PEDIT", "INserisci_prima") + \
                            " "  + QadMsg.translate("Command_PEDIT", "SPosta") + \
                            " "  + QadMsg.translate("Command_PEDIT", "Raddrizza") + \
                            " "  + QadMsg.translate("Command_PEDIT", "esCi")
      msg = msg + "/" + QadMsg.translate("Command_PEDIT", "Inserisci") + \
                  "/" + QadMsg.translate("Command_PEDIT", "INserisci prima") + \
                  "/" + QadMsg.translate("Command_PEDIT", "SPosta") + \
                  "/" + QadMsg.translate("Command_PEDIT", "Raddrizza") + \
                  "/" + QadMsg.translate("Command_PEDIT", "esCi")
               
      self.step = 8
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_VERTEX)
      # si appresta ad attendere enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(QadMsg.translate("Command_PEDIT", "Digitare un'opzione di modifica vertici [{0}] <{1}>: ").format(msg, self.default), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   self.default, \
                   keyWords, QadInputModeEnum.NONE)
      return False


   #============================================================================
   # waitForNewVertex
   #============================================================================
   def waitForNewVertex(self):      
      # imposto il map tool
      #qad_debug.breakPoint()
      self.getPointMapTool().setVertexAt(self.vertexAt, self.after)            
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_NEW_VERTEX)

      # si appresta ad attendere un punto
      self.waitForPoint(QadMsg.translate("Command_PEDIT", "Specificare la posizione del nuovo vertice: "))
      self.step = 9   


   #============================================================================
   # waitForMoveVertex
   #============================================================================
   def waitForMoveVertex(self):      
      # imposto il map tool
      self.getPointMapTool().setVertexAt(self.vertexAt)            
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_MOVE_VERTEX)

      # si appresta ad attendere un punto
      self.waitForPoint(QadMsg.translate("Command_PEDIT", "Specificare la nuova posizione del vertice: "))
      self.step = 10   


   #============================================================================
   # WaitForVertexEditingMenu
   #============================================================================
   def WaitForSecondVertex(self):
      #qad_debug.breakPoint()     
      self.displayVertexMarker(self.secondVertexAt)
      
      keyWords = QadMsg.translate("Command_PEDIT", "Seguente") + " "  + \
                 QadMsg.translate("Command_PEDIT", "Precedente") + " "  + \
                 QadMsg.translate("Command_PEDIT", "Esegui") + " "  + \
                 QadMsg.translate("Command_PEDIT", "esCi")
      msg = QadMsg.translate("Command_PEDIT", "Seguente") + "/" + \
            QadMsg.translate("Command_PEDIT", "Precedente") + "/" + \
            QadMsg.translate("Command_PEDIT", "Esegui") + "/" + \
            QadMsg.translate("Command_PEDIT", "esCi")
               
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_VERTEX)
      # si appresta ad attendere enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(QadMsg.translate("Command_PEDIT", "Digitare un'opzione di selezione del secondo vertice [{0}] <{1}>: ").format(msg, self.default1), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   self.default1, \
                   keyWords, QadInputModeEnum.NONE)
      self.step = 11
      
      return False

        
   def run(self, msgMapTool = False, msg = None):
      if self.step == 0:     
         self.waitForEntsel()
         return False # continua
      
      #=========================================================================
      # RISPOSTA ALLA SELEZIONE OGGETTI
      elif self.step == 1:
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
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         #qad_debug.breakPoint()

         if type(value) == unicode:
            if value == QadMsg.translate("Command_PEDIT", "Multiplo"):
               self.SSGetClass.checkPolygonLayer = True               
               self.SSGetClass.run(msgMapTool, msg)
               self.step = 2
               return False               
         elif type(value) == QgsPoint: # se è stato selezionato un punto
            self.entity.clear()
            self.linearObjectList.removeAll()            
            #qad_debug.breakPoint()
            if self.getPointMapTool().entity.isInitialized():
               if self.setEntityInfo(self.getPointMapTool().entity.layer, \
                                     self.getPointMapTool().entity.featureId, value) == True:
                  self.WaitForMainMenu()
                  return False
            else:
               # cerco se ci sono entità nel punto indicato saltando i layer punto
               # e considerando solo layer editabili       
               result = qad_utils.getEntSel(self.getPointMapTool().toCanvasCoordinates(value),
                                            self.getPointMapTool(), \
                                            None, \
                                            False, True, True, \
                                            True, \
                                            True)
               if result is not None:
                  # result[0] = feature, result[1] = layer, result[0] = point
                  if self.setEntityInfo(result[1], result[0].id(), result[2]) == True:
                     self.WaitForMainMenu()
                     return False                  
         else:
            return True # fine comando
         
         # si appresta ad attendere la selezione degli oggetti
         self.waitForEntsel()
         return False 

      #=========================================================================
      # RISPOSTA ALLA SELEZIONE DI UN GRUPPO OGGETTI
      elif self.step == 2:
         if self.SSGetClass.run(msgMapTool, msg) == True:         
            self.entitySet.set(self.SSGetClass.entitySet)
            
            if self.entitySet.count() == 0:
               self.waitForEntsel()
            else:
               self.WaitForMainMenu()
            self.getPointMapTool().refreshSnapType() # aggiorno lo snapType che può essere variato dal maptool di selezione entità                     
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL MENU PRINCIPALE (da step = 1 e 2)
      elif self.step == 3: # dopo aver atteso una opzione si riavvia il comando
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

            self.WaitForMainMenu()
            return False 
         else: # il punto arriva come parametro della funzione
            value = msg

         if value == QadMsg.translate("Command_PEDIT", "Chiudi"):
            self.setClose(True) 
         elif value == QadMsg.translate("Command_PEDIT", "Apri"):
            self.setClose(False) 
         elif value == QadMsg.translate("Command_PEDIT", "Edita"):
            self.vertexAt = 0
            self.default = QadMsg.translate("Command_PEDIT", "Seguente")
            self.WaitForVertexEditingMenu()
            return False
         elif value == QadMsg.translate("Command_PEDIT", "Unisci"):
            if self.entity.isInitialized(): # selezionato solo un oggetto
               self.SSGetClass.checkPolygonLayer = False # scarto i poligoni
               self.SSGetClass.run(msgMapTool, msg)
               self.step = 7
               return False               
            else:
               self.WaitForJoin()
               return False
         elif value == QadMsg.translate("Command_PEDIT", "ADatta"):
            self.curve(True)
         elif value == QadMsg.translate("Command_PEDIT", "Rettifica"):
            self.curve(False)
         elif value == QadMsg.translate("Command_PEDIT", "Inverti"):
            self.reverse()
         elif value == QadMsg.translate("Command_PEDIT", "ANnulla"):
            if self.nOperationsToUndo > 0: 
               self.nOperationsToUndo = self.nOperationsToUndo - 1           
               self.plugIn.undoEditCommand()
            else:
               self.showMsg(QadMsg.translate("QAD", "\nIl comando è stato completamente annullato."))                  
            
            if self.entity.isInitialized(): # selezionato solo un oggetto
               if self.atSubGeom is not None:
                  # ricarico la geometria ripristinata dall'annulla
                  geom = self.entity.getGeometry()
                  # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
                  subGeom = qad_utils.getSubGeomAt(geom, self.atSubGeom)
                  self.linearObjectList.fromPolyline(subGeom.asPolyline())
         else:
            return True # fine comando
            
         self.entity.deselectOnLayer()
         self.entitySet.deselectOnLayer()
         self.WaitForMainMenu()
         return False      
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA DISTANZA DI APPROSSIMAZIONE (da step = 3)
      elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = self.joinToleranceDist
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
         
         if type(value) == unicode:
            if value == QadMsg.translate("Command_PEDIT", "Tipo"):
               # si appresta ad attendere il tipo di unione
               self.waitForJoinType()
         elif type(value) == QgsPoint: # se è stato inserito il primo punto per il calcolo della distanza
            # imposto il map tool
            self.firstPt.set(value.x(), value.y())
            self.getPointMapTool().firstPt = self.firstPt
            self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.FIRST_TOLERANCE_PT_KNOWN_ASK_FOR_SECOND_PT)

            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_PEDIT", "Specificare secondo punto: "))           
            self.step = 5
         elif type(value) == float:
            self.joinToleranceDist = value
            self.plugIn.setJoinToleranceDist(self.joinToleranceDist)
            self.join()
            self.entity.deselectOnLayer()
            self.entitySet.deselectOnLayer()
            self.WaitForMainMenu()
         
         return False 
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER DISTANZA DI APPROSSIMAZIONE (da step = 4)
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

         if value == self.firstPt:
            self.showMsg(QadMsg.translate("QAD", "\nIl valore deve essere positivo e diverso da zero."))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_PEDIT", "Specificare secondo punto: "))
            return False
         
         self.joinToleranceDist = qad_utils.getDistance(self.firstPt, value)
         self.plugIn.setJoinToleranceDist(self.joinToleranceDist)
         self.join()
         self.entity.deselectOnLayer()
         self.entitySet.deselectOnLayer()
         self.WaitForMainMenu()

         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA MODALITA' DI UNIONE (da step = 4)
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

         if type(value) == unicode:
            if value == QadMsg.translate("Command_PEDIT", "Estendi"):
               self.joinMode = 1
               self.plugIn.setJoinMode(self.joinMode)
            elif value == QadMsg.translate("Command_PEDIT", "Aggiungi"):
               self.joinMode = 2
               self.plugIn.setJoinMode(self.joinMode)
            elif value == QadMsg.translate("Command_PEDIT", "ENtrambe"):
               self.joinMode = 3
               self.plugIn.setJoinMode(self.joinMode)
            
         self.WaitForJoin()
         return False
      
      #=========================================================================
      # RISPOSTA ALLA SELEZIONE DI UN GRUPPO OGGETTI DA UNIRE (da step = 3)
      elif self.step == 7:
         if self.SSGetClass.run(msgMapTool, msg) == True:         
            self.entitySet.set(self.SSGetClass.entitySet)
            
            if self.entitySet.count() > 0:
               self.joinToleranceDist = 0.0
               self.join()

            self.entity.deselectOnLayer()
            self.entitySet.deselectOnLayer()
            self.WaitForMainMenu()
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI OPZIONI EDITAZIONE VERTICI (da step = 3)
      elif self.step == 8: # dopo aver atteso un punto o una opzione si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = self.default
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto o l'opzione arriva come parametro della funzione
            value = msg
         
         if type(value) == unicode:
            if value == QadMsg.translate("Command_PEDIT", "Seguente"):
               self.default = value
               self.vertexAt = self.getNextVertex(self.vertexAt)                                 
               self.WaitForVertexEditingMenu()
            elif value == QadMsg.translate("Command_PEDIT", "Precedente"):
               self.default = value
               self.vertexAt = self.getPrevVertex(self.vertexAt)
               self.WaitForVertexEditingMenu()
            elif value == QadMsg.translate("Command_PEDIT", "Dividi"):
               self.editVertexMode = QadMsg.translate("Command_PEDIT", "Dividi")
               self.secondVertexAt = self.vertexAt
               self.default1 = QadMsg.translate("Command_PEDIT", "Seguente")
               self.WaitForSecondVertex()
               return False
            elif value == QadMsg.translate("Command_PEDIT", "Inserisci"):
               self.after = True
               self.waitForNewVertex()      
            elif value == QadMsg.translate("Command_PEDIT", "INserisci_prima"):
               self.after = False
               self.waitForNewVertex()
            elif value == QadMsg.translate("Command_PEDIT", "SPosta"):
               self.waitForMoveVertex()
            elif value == QadMsg.translate("Command_PEDIT", "Raddrizza"):
               self.editVertexMode = QadMsg.translate("Command_PEDIT", "Raddrizza")
               self.secondVertexAt = self.vertexAt
               self.default1 = QadMsg.translate("Command_PEDIT", "Seguente")
               self.WaitForSecondVertex()
               return False
            elif value == QadMsg.translate("Command_PEDIT", "esCi"):
               self.WaitForMainMenu()
         elif type(value) == QgsPoint: # se è stato inserito il primo punto
            #qad_debug.breakPoint()         
            # la funzione ritorna una lista con (<minima distanza al quadrato>,
            #                                    <punto più vicino>
            #                                    <indice della parte più vicina>       
            #                                    <"a sinistra di">)
            dummy = self.linearObjectList.closestPartWithContext(value)
            partAt = dummy[2]
            linearObject = self.linearObjectList.getLinearObjectAt(partAt)            
            # punto iniziale della parte
            if qad_utils.getDistance(linearObject.getStartPt(), value) < \
               qad_utils.getDistance(linearObject.getEndPt(), value):            
               self.vertexAt = partAt
            else: # punto finale della parte
               if partAt == self.linearObjectList.qty() - 1: # se ultima parte                  
                  self.vertexAt = 0 if self.linearObjectList.isClosed() else partAt + 1
               else:
                  self.vertexAt = partAt + 1
            self.WaitForVertexEditingMenu()
                                 
         return False 


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL NUOVO VERTICE DA INSERIRE (da step = 8)
      elif self.step == 9: # dopo aver atteso un punto o un numero reale si riavvia il comando
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
         
         #qad_debug.breakPoint()
         self.insertVertexAt(value)
         self.vertexAt = self.vertexAt + (1 if self.after else -1)
         self.WaitForVertexEditingMenu()

         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA POSIZIONE DEL VERTICE DA SPOSTARE (da step = 8)
      elif self.step == 10: # dopo aver atteso un punto o un numero reale si riavvia il comando
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
         
         self.moveVertexAt(value)
         self.WaitForVertexEditingMenu()

         return False

      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL SECONDO VERTICE (da step = 8)
      elif self.step == 11: # dopo aver atteso un punto o una opzione si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = self.default
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto o l'opzione arriva come parametro della funzione
            value = msg
         
         if type(value) == unicode:
            if value == QadMsg.translate("Command_PEDIT", "Seguente"):
               self.default1 = value
               self.secondVertexAt = self.getNextVertex(self.secondVertexAt)                                 
               self.WaitForSecondVertex()
            elif value == QadMsg.translate("Command_PEDIT", "Precedente"):
               self.default1 = value
               self.secondVertexAt = self.getPrevVertex(self.secondVertexAt)
               self.WaitForSecondVertex()
            elif value == QadMsg.translate("Command_PEDIT", "Esegui"):
               pt = self.linearObjectList.getPointAtVertex(self.vertexAt)
               
               if self.editVertexMode == QadMsg.translate("Command_PEDIT", "Dividi"):
                  self.breakFromVertexAtToSecondVertexAt()
               elif self.editVertexMode == QadMsg.translate("Command_PEDIT", "Raddrizza"):
                  self.straightenFromVertexAtToSecondVertexAt()
                  
               self.vertexAt = self.linearObjectList.getVertexPosAtPt(pt)
               self.WaitForVertexEditingMenu()
            elif value == QadMsg.translate("Command_PEDIT", "esCi"):
               self.WaitForVertexEditingMenu()
         elif type(value) == QgsPoint: # se è stato inserito il primo punto
            #qad_debug.breakPoint()         
            # la funzione ritorna una lista con (<minima distanza al quadrato>,
            #                                    <punto più vicino>
            #                                    <indice della parte più vicina>       
            #                                    <"a sinistra di">)
            dummy = self.linearObjectList.closestPartWithContext(value)
            partAt = dummy[2]
            linearObject = self.linearObjectList.getLinearObjectAt(partAt)            
            # punto iniziale della parte
            if qad_utils.getDistance(linearObject.getStartPt(), value) < \
               qad_utils.getDistance(linearObject.getEndPt(), value):            
               self.secondVertexAt = partAt
            else: # punto finale della parte
               if partAt == self.linearObjectList.qty() - 1: # se ultima parte                  
                  self.secondVertexAt = 0 if self.linearObjectList.isClosed() else partAt + 1
               else:
                  self.secondVertexAt = partAt + 1
            self.WaitForSecondVertex()
                                 
         return False 
