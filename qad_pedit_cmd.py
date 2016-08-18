# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando PEDIT per editare una polilinea o un poligono esistente
 
                              -------------------
        begin                : 2014-01-13
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


from qad_generic_cmd import QadCommandClass
from qad_getdist_cmd import QadGetDistClass
from qad_snapper import *
from qad_pedit_maptool import *
from qad_ssget_cmd import QadSSGetClass
from qad_msg import QadMsg
from qad_textwindow import *
import qad_utils
import qad_layer
from qad_variables import *
from qad_snappointsdisplaymanager import *
from qad_dim import QadDimStyles
import qad_grip


# Classe che gestisce il comando PEDIT
class QadPEDITCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadPEDITCommandClass(self.plugIn)

   def getName(self):
      return QadMsg.translate("Command_list", "PEDIT")
   
   def getEnglishName(self):
      return "PEDIT"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runPEDITCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/pedit.png")
   
   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_PEDIT", "Modifies existing polylines or polygon.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.SSGetClass = QadSSGetClass(plugIn)
      self.SSGetClass.onlyEditableLayers = True
      self.SSGetClass.checkPointLayer = False # scarto i punto
      self.SSGetClass.checkLineLayer = True
      self.SSGetClass.checkDimLayers = False # scarto le quote
      
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
      self.snapPointsDisplayManager.setIconSize(QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAPSIZE")))
      self.snapPointsDisplayManager.setColor(QColor(QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAPCOLOR"))))

      self.GetDistClass = None
      self.simplifyTolerance = None
   
   def __del__(self):
      QadCommandClass.__del__(self)
      del self.SSGetClass
      self.entity.deselectOnLayer()
      self.entitySet.deselectOnLayer()
      del self.snapPointsDisplayManager
      if self.GetDistClass is not None: del self.GetDistClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 2: # quando si é in fase di selezione entità
         return self.SSGetClass.getPointMapTool()           
      # quando si é in fase di richiesta distanza
      elif self.step == 12:
         return self.GetDistClass.getPointMapTool()
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
      self.entity.set(layer, featureId)
      geom = self.layerToMapCoordinates(layer, self.entity.getGeometry())
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      dummy = qad_utils.closestSegmentWithContext(point, geom)
      if dummy[2] is not None:
         # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
         subGeom, self.atSubGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])
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
      elif vertexAt < tot: # se non é ultimo punto
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
      snapPoint = dict()
      snapPoint[QadSnapTypeEnum.END] = [pt]
      self.snapPointsDisplayManager.show(snapPoint)
         

   #============================================================================
   # setClose
   #============================================================================
   def setClose(self, toClose):
      if self.entity.isInitialized(): # selezionato solo un oggetto
         layer = self.entity.layer
         self.plugIn.beginEditCommand("Feature edited", layer)
         
         tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
         f = self.entity.getFeature()
         # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
         geom = self.layerToMapCoordinates(layer, self.entity.getGeometry())
         geom = f.geometry()
         
         self.linearObjectList.setClose(toClose)
         pts = self.linearObjectList.asPolyline(tolerance2ApproxCurve)
         
         # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
         geom = self.layerToMapCoordinates(layer, self.entity.getGeometry())
         
         if layer.geometryType() == QGis.Line:
            updGeom = qad_utils.setSubGeom(geom, QgsGeometry.fromPolyline(pts), self.atSubGeom)
            # trasformo la geometria nel crs del layer
            f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
               
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
                                                         None, False) == False:
                  self.plugIn.destroyEditCommand()
                  return
               
               updGeom = qad_utils.delSubGeom(geom, atSubGeom)

               if updGeom is None or updGeom.isGeosEmpty(): # da cancellare
                  # plugIn, layer, feature id, refresh
                  if qad_layer.deleteFeatureToLayer(self.plugIn, layer, f.id(), False) == False:
                     self.plugIn.destroyEditCommand()
                     return
               else:
                  editedFeature = QgsFeature(f)
                  # trasformo la geometria nel crs del layer
                  editedFeature.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
                  
                  # plugIn, layer, feature, refresh, check_validity
                  if qad_layer.updateFeatureToLayer(self.plugIn, layer, editedFeature, False, False) == False:
                     self.plugIn.destroyEditCommand()
                     return
      else:         
         self.plugIn.beginEditCommand("Feature edited", self.entitySet.getLayerList())
         for layerEntitySet in self.entitySet.layerEntitySetList:
            layer = layerEntitySet.layer
            tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
            
            updObjects = []
            for featureId in layerEntitySet.featureIds:
               f = layerEntitySet.getFeature(featureId)
               # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
               updGeom = qad_utils.closeQgsGeometry(self.mapToLayerCoordinates(layer, f.geometry()), toClose, tolerance2ApproxCurve)
               if updGeom is not None:
                  updFeature = QgsFeature(f)
                  # trasformo la geometria nel crs del layer
                  updFeature.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
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
      if self.entity.isInitialized(): # selezionato solo un oggetto
         layer = self.entity.layer
         self.plugIn.beginEditCommand("Feature edited", layer)

         tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
         f = self.entity.getFeature()
         # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
         geom = self.layerToMapCoordinates(layer, self.entity.getGeometry())

         self.linearObjectList.reverse()
         updSubGeom = QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve))
         updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
         if updGeom is not None:
            # trasformo la geometria nel crs del layer
            f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
            # plugIn, layer, feature, refresh, check_validity
            if qad_layer.updateFeatureToLayer(self.plugIn, self.entity.layer, f, False, False) == False:
               self.plugIn.destroyEditCommand()
               return
      else:
         self.plugIn.beginEditCommand("Feature edited", self.entitySet.getLayerList())

         for layerEntitySet in self.entitySet.layerEntitySetList:
            tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))                       
            
            updObjects = []
            for featureId in layerEntitySet.featureIds:
               f = layerEntitySet.getFeature(featureId)
               # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
               geom = self.layerToMapCoordinates(layerEntitySet.layer, f.geometry())               
               updGeom = qad_utils.reverseQgsGeometry(geom, tolerance2ApproxCurve)
               if updGeom is not None:
                  updFeature = QgsFeature(f)
                  # trasformo la geometria nel crs del layer
                  updFeature.setGeometry(self.mapToLayerCoordinates(layerEntitySet.layer, updGeom))
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

         tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
         
         f = self.entity.getFeature()
         if f.geometry().wkbType() != QGis.WKBLineString:
            return
         newFeature = QgsFeature()
         newFeature.initAttributes(1)
         newFeature.setAttribute(0, 0)
         
         geom = QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve))
         newFeature.setGeometry(geom)
         i = i + 1
         
         if vectorLayer.addFeature(newFeature) == False:
            vectorLayer.destroyEditCommand()
            return
         newIdFeatureList.append([newFeature.id(), layer, f])
      
      
      for layerEntitySet in self.entitySet.layerEntitySetList:
         layer = layerEntitySet.layer
         
         if layer.geometryType() != QGis.Line:
            continue
                  
         for f in layerEntitySet.getFeatureCollection():
            if f.geometry().wkbType() != QGis.WKBLineString:
               continue
            newFeature = QgsFeature()
            newFeature.initAttributes(1)
            newFeature.setAttribute(0, i)

            # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
            geom = self.layerToMapCoordinates(layerEntitySet.layer, f.geometry())
            newFeature.setGeometry(geom)
            i = i + 1
            
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
            featureIdToJoin = newIdFeatureList[i][0]
            #                         featureIdToJoin, vectorLayer, tolerance2ApproxCurve, toleranceDist, mode     
            deleteFeatures.extend(qad_utils.joinFeatureInVectorLayer(featureIdToJoin, vectorLayer, \
                                                                     tolerance2ApproxCurve, \
                                                                     self.joinToleranceDist, self.joinMode))
            i = i + 1
                       
      self.plugIn.beginEditCommand("Feature edited", self.entitySet.getLayerList())

      if self.entity.isInitialized(): # selezionato solo un oggetto
         newFeature = qad_utils.getFeatureById(vectorLayer, newIdFeatureList[0][0])
         if newFeature is None:
            self.plugIn.destroyEditCommand()
            return
         
         layer = newIdFeatureList[0][1]
         f = newIdFeatureList[0][2]

         # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
         geom = self.layerToMapCoordinates(self.entity.layer, f.geometry())

         updGeom = qad_utils.setSubGeom(geom, newFeature.geometry(), self.atSubGeom)

         # trasformo la geometria nel crs del layer
         f.setGeometry(self.mapToLayerCoordinates(self.entity.layer, updGeom))
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
      if self.entity.isInitialized(): # selezionato solo un oggetto
         layer = self.entity.layer
         self.plugIn.beginEditCommand("Feature edited", layer)

         tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
         f = self.entity.getFeature()
         # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
         geom = self.layerToMapCoordinates(layer, f.geometry())

         self.linearObjectList.curve(toCurve)
         updSubGeom = QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve))
         updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
         if updGeom is not None:
            # trasformo la geometria nel crs del layer
            f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
            # plugIn, layer, feature, refresh, check_validity
            if qad_layer.updateFeatureToLayer(self.plugIn, self.entity.layer, f, False, False) == False:
               self.plugIn.destroyEditCommand()
               return
      else:
         self.plugIn.beginEditCommand("Feature edited", self.entitySet.getLayerList())

         for layerEntitySet in self.entitySet.layerEntitySetList:
            tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))  
            
            updObjects = []
            for featureId in layerEntitySet.featureIds:
               f = layerEntitySet.getFeature(featureId)
               # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
               geom = self.layerToMapCoordinates(layerEntitySet.layer, f.geometry())
               
               updGeom = qad_utils.curveQgsGeometry(geom, toCurve, tolerance2ApproxCurve)
               if updGeom is not None:
                  updFeature = QgsFeature(f)
                  # trasformo la geometria nel crs del layer
                  updFeature.setGeometry(self.mapToLayerCoordinates(layerEntitySet.layer, updGeom))
                  updObjects.append(updFeature)      
         
            # plugIn, layer, features, refresh, check_validity
            if qad_layer.updateFeaturesToLayer(self.plugIn, layerEntitySet.layer, updObjects, False, False) == False:
               self.plugIn.destroyEditCommand()
               return
   
      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1


   #============================================================================
   # simplify
   #============================================================================
   def simplify(self):
      tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
                             
      if self.entity.isInitialized(): # selezionato solo un oggetto
         layer = self.entity.layer
         self.plugIn.beginEditCommand("Feature edited", layer)
         
         f = self.entity.getFeature()
         # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
         geom = self.layerToMapCoordinates(layer, f.geometry())

         updSubGeom = QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve)).simplify(self.simplifyTolerance)        
         updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
         if updGeom is not None:
            # trasformo la geometria nel crs del layer
            f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
            # plugIn, layer, feature, refresh, check_validity
            if qad_layer.updateFeatureToLayer(self.plugIn, self.entity.layer, f, False, False) == False:
               self.plugIn.destroyEditCommand()
               return
      else:
         self.plugIn.beginEditCommand("Feature edited", self.entitySet.getLayerList())

         for layerEntitySet in self.entitySet.layerEntitySetList:
            updObjects = []
            for featureId in layerEntitySet.featureIds:
               f = layerEntitySet.getFeature(featureId)
               # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
               geom = self.layerToMapCoordinates(layerEntitySet.layer, f.geometry())               
               updGeom = geom.simplify(self.simplifyTolerance)
               if updGeom is not None:
                  updFeature = QgsFeature(f)
                  # trasformo la geometria nel crs del layer
                  updFeature.setGeometry(self.mapToLayerCoordinates(layerEntitySet.layer, updGeom))
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

      tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
      f = self.entity.getFeature()
      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      geom = self.layerToMapCoordinates(layer, f.geometry())

      if self.after: # dopo
         if self.vertexAt == self.linearObjectList.qty() and self.linearObjectList.isClosed():
            self.linearObjectList.insertPoint(0, pt)
         else:
            self.linearObjectList.insertPoint(self.vertexAt, pt)
      else: # prima
         if self.vertexAt == 0 and self.linearObjectList.isClosed():
            self.linearObjectList.insertPoint(self.linearObjectList.qty() - 1, pt)
         else:
            self.linearObjectList.insertPoint(self.vertexAt - 1, pt)
               
      updSubGeom = QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve))
      updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
      if updGeom is None:
         return
      # trasformo la geometria nel crs del layer
      f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
      
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

      tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
      f = self.entity.getFeature()
      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      geom = self.layerToMapCoordinates(layer, f.geometry())

      self.linearObjectList.movePoint(self.vertexAt, pt)
               
      updSubGeom = QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve))
      updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
      if updGeom is None:
         return
      # trasformo la geometria nel crs del layer
      f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
         
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
      tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))     
      f = self.entity.getFeature()
      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      geom = self.layerToMapCoordinates(layer, f.geometry())

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
      # trasformo la geometria nel crs del layer
      f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
      
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

      tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
      f = self.entity.getFeature()
      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      geom = self.layerToMapCoordinates(layer, f.geometry())

      firstPt = self.linearObjectList.getPointAtVertex(self.vertexAt)
      secondPt = self.linearObjectList.getPointAtVertex(self.secondVertexAt)

      result = qad_utils.breakQgsGeometry(QgsGeometry.fromPolyline(self.linearObjectList.asPolyline(tolerance2ApproxCurve)), \
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
      # trasformo la geometria nel crs del layer
      f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))

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
      self.step = 1
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_ENTITY_SEL)
                        
      keyWords = QadMsg.translate("Command_PEDIT", "Last") + "/" + \
                 QadMsg.translate("Command_PEDIT", "Multiple")
      prompt = QadMsg.translate("Command_PEDIT", "Select polyline or [{0}]: ").format(QadMsg.translate("Command_PEDIT", "Multiple"))
               
      englishKeyWords = "Last" + "/" + "Multiple"
      keyWords += "_" + englishKeyWords
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valore nullo non permesso
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NOT_NULL)      
      

   #============================================================================
   # WaitForMainMenu
   #============================================================================
   def WaitForMainMenu(self):
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
            if self.linearObjectList.isClosed(): # se é chiusa
               keyWords = QadMsg.translate("Command_PEDIT", "Open") + "/"
               englishKeyWords = "Open"
            else:
               keyWords = QadMsg.translate("Command_PEDIT", "Close") + "/"
               englishKeyWords = "Close"
         else: # selezionati più oggetti
            keyWords = QadMsg.translate("Command_PEDIT", "Close") + "/" + \
                       QadMsg.translate("Command_PEDIT", "Open") + "/"
            englishKeyWords = "Close" + "/" + "Open"
                  
         keyWords = keyWords + QadMsg.translate("Command_PEDIT", "Join") + "/"
         englishKeyWords = englishKeyWords + "Join"
      else: # se non ci sono dei layer linea
         keyWords = ""
         msg = ""
         englishKeyWords = ""

      if self.entity.isInitialized(): # selezionato solo un oggetto
         keyWords = keyWords + QadMsg.translate("Command_PEDIT", "Edit vertex") + "/"
         englishKeyWords = englishKeyWords + "Edit vertex"
         
      keyWords = keyWords + QadMsg.translate("Command_PEDIT", "Fit") + "/" + \
                            QadMsg.translate("Command_PEDIT", "Decurve") + "/" + \
                            QadMsg.translate("Command_PEDIT", "Reverse") + "/" + \
                            QadMsg.translate("Command_PEDIT", "Simplify") + "/" + \
                            QadMsg.translate("Command_PEDIT", "Undo")      
      englishKeyWords = englishKeyWords + "Fit" + "/" + "Decurve" + "/" + "Reverse" + "/" + "Simplify" + "/" + "Undo"
      prompt = QadMsg.translate("Command_PEDIT", "Enter an option [{0}]: ").format(keyWords)
      
      self.step = 3
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.NONE)

      keyWords += "_" + englishKeyWords
      # si appresta ad attendere enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)
      return False
      

   #============================================================================
   # WaitForJoin
   #============================================================================
   def WaitForJoin(self):
      CurrSettingsMsg = QadMsg.translate("QAD", "\nCurrent settings: ")
      CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_PEDIT", "Join type = ")
      if self.joinMode == 1:
         CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_PEDIT", "extends the segments")
      elif self.joinMode == 2:
         CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_PEDIT", "adds segments")
      elif self.joinMode == 3:
         CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_PEDIT", "extends and adds segments")
      
      self.showMsg(CurrSettingsMsg)
      self.waitForDistance()       
        

   #============================================================================
   # waitForDistance
   #============================================================================
   def waitForDistance(self):      
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_FIRST_TOLERANCE_PT)

      keyWords = QadMsg.translate("Command_PEDIT", "Join type")                 
      prompt = QadMsg.translate("Command_PEDIT", "Specify gap tolerance or [{0}] <{1}>: ").format(keyWords, str(self.joinToleranceDist))

      englishKeyWords = "Join type"
      keyWords += "_" + englishKeyWords
      # si appresta ad attendere un punto o enter o una parola chiave o un numero reale     
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT | QadInputTypeEnum.KEYWORDS, \
                   self.joinToleranceDist, \
                   keyWords, \
                   QadInputModeEnum.NOT_NEGATIVE)      
      self.step = 4      
      
        
   #============================================================================
   # waitForJoinType
   #============================================================================
   def waitForJoinType(self):      
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.NONE)

      keyWords = QadMsg.translate("Command_PEDIT", "Extend") + "/" + \
                 QadMsg.translate("Command_PEDIT", "Add") + "/" + \
                 QadMsg.translate("Command_PEDIT", "Both")
      englishKeyWords = "Extend" + "/" + "Add" + "/" + "Both"
      if self.joinMode == 1:
         default = QadMsg.translate("Command_PEDIT", "Extend")
      elif self.joinMode == 2:
         default = QadMsg.translate("Command_PEDIT", "Add")
      elif self.joinMode == 3:
         default = QadMsg.translate("Command_PEDIT", "Both")
      prompt = QadMsg.translate("Command_PEDIT", "Specify join type [{0}] <{1}>: ").format(keyWords, default)

      keyWords += "_" + englishKeyWords
      # si appresta ad attendere un punto o enter o una parola chiave o un numero reale     
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, QadInputTypeEnum.KEYWORDS, default, \
                   keyWords)      
      self.step = 6


   #============================================================================
   # WaitForVertexEditingMenu
   #============================================================================
   def WaitForVertexEditingMenu(self):
      self.getPointMapTool().setLinearObjectList(self.linearObjectList, self.entity.layer)
      
      self.displayVertexMarker(self.vertexAt)
      
      keyWords = QadMsg.translate("Command_PEDIT", "Next") + "/" + \
                 QadMsg.translate("Command_PEDIT", "Previous")
      englishKeyWords = "Next" + "/" + "Previous"
      
      if self.entity.layer.geometryType() == QGis.Line:
         keyWords = keyWords + "/"  + QadMsg.translate("Command_PEDIT", "Break")
         englishKeyWords = englishKeyWords + "/" + "Break"

      keyWords = keyWords + "/" + QadMsg.translate("Command_PEDIT", "Insert") + "/" + \
                                  QadMsg.translate("Command_PEDIT", "INsert before") + "/" + \
                                  QadMsg.translate("Command_PEDIT", "Move") + "/" + \
                                  QadMsg.translate("Command_PEDIT", "Straighten") + "/" + \
                                  QadMsg.translate("Command_PEDIT", "eXit")
      englishKeyWords = englishKeyWords + "/" + "Insert" + "/" + "INsert before" + "/" + \
                                          "Move" + "/" + "Straighten" + "/" + "eXit"

      prompt = QadMsg.translate("Command_PEDIT", "Enter a vertex editing option [{0}] <{1}>: ").format(keyWords, self.default)
               
      self.step = 8
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_VERTEX)

      keyWords += "_" + englishKeyWords
      # si appresta ad attendere enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   self.default, \
                   keyWords, QadInputModeEnum.NONE)
      return False


   #============================================================================
   # waitForNewVertex
   #============================================================================
   def waitForNewVertex(self):      
      # imposto il map tool
      self.getPointMapTool().setVertexAt(self.vertexAt, self.after)
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_NEW_VERTEX)

      # si appresta ad attendere un punto
      self.waitForPoint(QadMsg.translate("Command_PEDIT", "Specify the position of the new vertex: "))
      self.step = 9   


   #============================================================================
   # waitForMoveVertex
   #============================================================================
   def waitForMoveVertex(self):      
      # imposto il map tool
      self.getPointMapTool().setVertexAt(self.vertexAt)            
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_MOVE_VERTEX)

      # si appresta ad attendere un punto
      self.waitForPoint(QadMsg.translate("Command_PEDIT", "Specify the new vertex position: "))
      self.step = 10   


   #============================================================================
   # WaitForVertexEditingMenu
   #============================================================================
   def WaitForSecondVertex(self):
      self.displayVertexMarker(self.secondVertexAt)
      
      keyWords = QadMsg.translate("Command_PEDIT", "Next") + "/"  + \
                 QadMsg.translate("Command_PEDIT", "Previous") + "/"  + \
                 QadMsg.translate("Command_PEDIT", "Go") + "/"  + \
                 QadMsg.translate("Command_PEDIT", "eXit")
      englishKeyWords = "Next" + "/" + "Previous" + "/" + "Go" + "/" + "eXit"
      prompt = QadMsg.translate("Command_PEDIT", "Enter a selection option for the second vertex [{0}] <{1}>: ").format(keyWords, self.default1)
               
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_VERTEX)
      
      keyWords += "_" + englishKeyWords
      # si appresta ad attendere enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   self.default1, \
                   keyWords, QadInputModeEnum.NONE)
      self.step = 11
      
      return False


   #============================================================================
   # WaitForSimplifyTolerance
   #============================================================================
   def WaitForSimplifyTolerance(self, msgMapTool, msg):
      if self.GetDistClass is not None:
         del self.GetDistClass
      self.GetDistClass = QadGetDistClass(self.plugIn)
      if self.simplifyTolerance is None:
         prompt = QadMsg.translate("Command_PEDIT", "Specify tolerance: ")
      else:
         prompt = QadMsg.translate("Command_PEDIT", "Specify tolerance <{0}>: ")
         self.GetDistClass.msg = prompt.format(str(self.simplifyTolerance))
         self.GetDistClass.dist = self.simplifyTolerance
      self.GetDistClass.inputMode = QadInputModeEnum.NOT_NEGATIVE
      self.step = 12
      self.GetDistClass.run(msgMapTool, msg)


   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapSettings().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
         return True # fine comando
      
      if self.step == 0:     
         self.waitForEntsel()
         return False # continua
      
      #=========================================================================
      # RISPOSTA ALLA SELEZIONE OGGETTI
      elif self.step == 1:
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
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_PEDIT", "Multiple") or value == "Multiple":
               self.SSGetClass.checkPolygonLayer = True               
               self.SSGetClass.run(msgMapTool, msg)
               self.step = 2
               return False               
         elif type(value) == QgsPoint: # se é stato selezionato un punto
            self.entity.clear()
            self.linearObjectList.removeAll()            

            if self.getPointMapTool().entity.isInitialized():
               if self.setEntityInfo(self.getPointMapTool().entity.layer, \
                                     self.getPointMapTool().entity.featureId, value) == True:
                  self.WaitForMainMenu()
                  return False
            else:               
               # cerco se ci sono entità nel punto indicato considerando
               # solo layer lineari o poligono editabili che non appartengano a quote
               layerList = []
               for layer in qad_utils.getVisibleVectorLayers(self.plugIn.canvas): # Tutti i layer vettoriali visibili
                  if (layer.geometryType() == QGis.Line or layer.geometryType() == QGis.Polygon) and \
                     layer.isEditable():
                     if len(QadDimStyles.getDimListByLayer(layer)) == 0:
                        layerList.append(layer)
               
               result = qad_utils.getEntSel(self.getPointMapTool().toCanvasCoordinates(value),
                                            self.getPointMapTool(), \
                                            QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")), \
                                            layerList)
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
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            self.WaitForMainMenu()
            return False 
         else: # il punto arriva come parametro della funzione
            value = msg

         if value == QadMsg.translate("Command_PEDIT", "Close") or value == "Close":
            self.setClose(True) 
         elif value == QadMsg.translate("Command_PEDIT", "Open") or value == "Open":
            self.setClose(False) 
         elif value == QadMsg.translate("Command_PEDIT", "Edit vertex") or value == "Edit vertex":
            self.vertexAt = 0
            self.default = QadMsg.translate("Command_PEDIT", "Next")
            self.WaitForVertexEditingMenu()
            return False
         elif value == QadMsg.translate("Command_PEDIT", "Join") or value == "Join":
            if self.entity.isInitialized(): # selezionato solo un oggetto
               self.SSGetClass.checkPolygonLayer = False # scarto i poligoni
               self.SSGetClass.run(msgMapTool, msg)
               self.step = 7
               return False               
            else:
               self.WaitForJoin()
               return False
         elif value == QadMsg.translate("Command_PEDIT", "Fit") or value == "Fit":
            self.curve(True)
         elif value == QadMsg.translate("Command_PEDIT", "Decurve") or value == "Decurve":
            self.curve(False)
         elif value == QadMsg.translate("Command_PEDIT", "Reverse") or value == "Reverse":
            self.reverse()
         elif value == QadMsg.translate("Command_PEDIT", "Simplify") or value == "Simplify":
            self.WaitForSimplifyTolerance(msgMapTool, msg)
            return False
         elif value == QadMsg.translate("Command_PEDIT", "Undo") or value == "Undo":
            if self.nOperationsToUndo > 0: 
               self.nOperationsToUndo = self.nOperationsToUndo - 1           
               self.plugIn.undoEditCommand()
            else:
               self.showMsg(QadMsg.translate("QAD", "\nThe command has been canceled."))                  
            
            if self.entity.isInitialized(): # selezionato solo un oggetto
               if self.atSubGeom is not None:
                  # ricarico la geometria ripristinata dall'annulla
                  geom = self.entity.getGeometry()
                  # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
                  subGeom = qad_utils.getSubGeomAt(geom, self.atSubGeom)
                  # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
                  subGeom = self.layerToMapCoordinates(self.entity.layer, subGeom)
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
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
            if value == QadMsg.translate("Command_PEDIT", "Join type") or value == "Join type":
               # si appresta ad attendere il tipo di unione
               self.waitForJoinType()
         elif type(value) == QgsPoint: # se é stato inserito il primo punto per il calcolo della distanza
            # imposto il map tool
            self.firstPt.set(value.x(), value.y())
            self.getPointMapTool().firstPt = self.firstPt
            self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.FIRST_TOLERANCE_PT_KNOWN_ASK_FOR_SECOND_PT)

            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_PEDIT", "Specify second point: "))
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

         if value == self.firstPt:
            self.showMsg(QadMsg.translate("QAD", "\nThe value must be positive and not zero."))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_PEDIT", "Specify second point: "))
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
            if value == QadMsg.translate("Command_PEDIT", "Extend") or value == "Extend":
               self.joinMode = 1
               self.plugIn.setJoinMode(self.joinMode)
            elif value == QadMsg.translate("Command_PEDIT", "Add") or value == "Add":
               self.joinMode = 2
               self.plugIn.setJoinMode(self.joinMode)
            elif value == QadMsg.translate("Command_PEDIT", "Both") or value == "Both":
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
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
            if value == QadMsg.translate("Command_PEDIT", "Next") or value == "Next":
               self.default = value
               self.vertexAt = self.getNextVertex(self.vertexAt)                                 
               self.WaitForVertexEditingMenu()
            elif value == QadMsg.translate("Command_PEDIT", "Previous") or value == "Previous":
               self.default = value
               self.vertexAt = self.getPrevVertex(self.vertexAt)
               self.WaitForVertexEditingMenu()
            elif value == QadMsg.translate("Command_PEDIT", "Break") or value == "Break":
               self.editVertexMode = QadMsg.translate("Command_PEDIT", "Break")
               self.secondVertexAt = self.vertexAt
               self.default1 = QadMsg.translate("Command_PEDIT", "Next")
               self.WaitForSecondVertex()
               return False
            elif value == QadMsg.translate("Command_PEDIT", "Insert") or value == "Insert":
               self.after = True
               self.waitForNewVertex()      
            elif value == QadMsg.translate("Command_PEDIT", "INsert before") or value == "INsert before":
               self.after = False
               self.waitForNewVertex()
            elif value == QadMsg.translate("Command_PEDIT", "Move") or value == "Move":
               self.waitForMoveVertex()
            elif value == QadMsg.translate("Command_PEDIT", "Straighten") or value == "Straighten":
               self.editVertexMode = QadMsg.translate("Command_PEDIT", "Straighten")
               self.secondVertexAt = self.vertexAt
               self.default1 = QadMsg.translate("Command_PEDIT", "Next")
               self.WaitForSecondVertex()
               return False
            elif value == QadMsg.translate("Command_PEDIT", "eXit") or value == "eXit":
               self.WaitForMainMenu()
         elif type(value) == QgsPoint: # se é stato inserito un punto
            # cerco il vertice più vicino al punto
            self.vertexAt = self.linearObjectList.closestVertexWithContext(value)
            self.WaitForVertexEditingMenu()
                                 
         return False 


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL NUOVO VERTICE DA INSERIRE (da step = 8)
      elif self.step == 9: # dopo aver atteso un punto o un numero reale si riavvia il comando
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
         
         self.insertVertexAt(value)
         self.vertexAt = self.vertexAt + (1 if self.after else -1)
         self.WaitForVertexEditingMenu()

         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA POSIZIONE DEL VERTICE DA SPOSTARE (da step = 8)
      elif self.step == 10: # dopo aver atteso un punto o un numero reale si riavvia il comando
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
         
         self.moveVertexAt(value)
         self.WaitForVertexEditingMenu()

         return False

      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL SECONDO VERTICE (da step = 8)
      elif self.step == 11: # dopo aver atteso un punto o una opzione si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
            if value == QadMsg.translate("Command_PEDIT", "Next") or value == "Next":
               self.default1 = value
               self.secondVertexAt = self.getNextVertex(self.secondVertexAt)                                 
               self.WaitForSecondVertex()
            elif value == QadMsg.translate("Command_PEDIT", "Previous") or value == "Previous":
               self.default1 = value
               self.secondVertexAt = self.getPrevVertex(self.secondVertexAt)
               self.WaitForSecondVertex()
            elif value == QadMsg.translate("Command_PEDIT", "Go") or value == "Go":
               pt = self.linearObjectList.getPointAtVertex(self.vertexAt)
               
               if self.editVertexMode == QadMsg.translate("Command_PEDIT", "Break"):
                  self.breakFromVertexAtToSecondVertexAt()
               elif self.editVertexMode == QadMsg.translate("Command_PEDIT", "Straighten"):
                  self.straightenFromVertexAtToSecondVertexAt()
                  
               self.vertexAt = self.linearObjectList.getVertexPosAtPt(pt)
               self.WaitForVertexEditingMenu()
            elif value == QadMsg.translate("Command_PEDIT", "eXit") or value == "eXit":
               self.WaitForVertexEditingMenu()
         elif type(value) == QgsPoint: # se é stato inserito il primo punto
            # cerco il vertice più vicino al punto            
            self.secondVertexAt = self.linearObjectList.closestVertexWithContext(value)
            self.WaitForSecondVertex()
                                 
         return False 
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA TOLLERANZE PER SEMPLIFICAZIONE (da step = 3)
      elif self.step == 12:
         if self.GetDistClass.run(msgMapTool, msg) == True:
            if self.GetDistClass.dist is not None:
               self.simplifyTolerance = self.GetDistClass.dist
               self.simplify()
               self.entity.deselectOnLayer()
               self.entitySet.deselectOnLayer()
               self.WaitForMainMenu()
         return False # fine comando


#============================================================================
# Classe che gestisce il comando per inserire/cancellare un vertice per i grip
#============================================================================
class QadGRIPINSERTREMOVEVERTEXCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadGRIPINSERTREMOVEVERTEXCommandClass(self.plugIn)

   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.entity = None
      self.skipToNextGripCommand = False
      self.copyEntities = False
      self.basePt = QgsPoint()
      self.nOperationsToUndo = 0

      self.after = True
      self.insert_mode = True
      self.vertexAt = 0
      self.firstPt = QgsPoint()
      self.linearObjectList = qad_utils.QadLinearObjectList()

   def __del__(self):
      QadCommandClass.__del__(self)


   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_pedit_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None


   def setInsertVertexAfter_Mode(self):
      self.after = True
      self.insert_mode = True
      
   def setInsertVertexBefore_Mode(self):
      self.after = False
      self.insert_mode = True

   def setRemoveVertex_mode(self):
      self.insert_mode = False
      
      
   #============================================================================
   # setSelectedEntityGripPoints
   #============================================================================
   def setSelectedEntityGripPoints(self, entitySetGripPoints):
      # lista delle entityGripPoint con dei grip point selezionati
      # setta la prima entità con un grip selezionato
      self.entity = None
      for entityGripPoints in entitySetGripPoints.entityGripPoints:
         for gripPoint in entityGripPoints.gripPoints:
            # grip point selezionato
            if gripPoint.getStatus() == qad_grip.QadGripStatusEnum.SELECTED:
               # verifico se l'entità appartiene ad uno stile di quotatura
               if entityGripPoints.entity.isDimensionComponent():
                  return False
               if entityGripPoints.entity.getEntityType() != QadEntityGeomTypeEnum.LINESTRING:
                  return False
               
               # setta: self.entity, self.linearObjectList, self.atSubGeom
               self.entity = entityGripPoints.entity

               self.firstPt.set(gripPoint.getPoint().x(), gripPoint.getPoint().y())
               
               # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
               geom = self.layerToMapCoordinates(self.entity.layer, self.entity.getGeometry())
               # ritorna una tupla (<The squared cartesian distance>,
               #                    <minDistPoint>
               #                    <afterVertex>
               #                    <leftOf>)
               dummy = qad_utils.closestSegmentWithContext(self.firstPt, geom)
               if dummy[2] is not None:
                  # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
                  subGeom, self.atSubGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])
                  self.linearObjectList.fromPolyline(subGeom.asPolyline())
                  # setto il n. di vertice
                  self.vertexAt = gripPoint.nVertex
                  
                  self.getPointMapTool().setLinearObjectList(self.linearObjectList, self.entity.layer)
                  return True

      return False


   #============================================================================
   # insertVertexAt
   #============================================================================
   def insertVertexAt(self, pt):
      layer = self.entity.layer
      f = self.entity.getFeature()
      if f is None: # non c'è più la feature
         return False
      
      # faccio una copia locale
      linearObjectList = qad_utils.QadLinearObjectList(self.linearObjectList)

      tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))

      if self.after: # dopo
         if self.vertexAt == linearObjectList.qty() and linearObjectList.isClosed():
            linearObjectList.insertPoint(0, pt)
         else:
            linearObjectList.insertPoint(self.vertexAt, pt)
      else: # prima
         if self.vertexAt == 0 and linearObjectList.isClosed():
            linearObjectList.insertPoint(self.linearObjectList.qty() - 1, pt)
         else:
            linearObjectList.insertPoint(self.vertexAt - 1, pt)

      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      geom = self.layerToMapCoordinates(layer, self.entity.getGeometry())
               
      updSubGeom = QgsGeometry.fromPolyline(linearObjectList.asPolyline(tolerance2ApproxCurve))
      updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
      if updGeom is None:
         return
      # trasformo la geometria nel crs del layer
      f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
      
      self.plugIn.beginEditCommand("Feature edited", layer)
   
      if self.copyEntities == False:
         # plugIn, layer, feature, refresh, check_validity
         if qad_layer.updateFeatureToLayer(self.plugIn, layer, f, False, False) == False:
            self.plugIn.destroyEditCommand()
            return False
      else:
         # plugIn, layer, features, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(self.plugIn, layer, f, None, False, False) == False:
            self.plugIn.destroyEditCommand()
            return False

      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1


   #============================================================================
   # removeVertexAt
   #============================================================================
   def removeVertexAt(self):
      layer = self.entity.layer
      f = self.entity.getFeature()
      if f is None: # non c'è più la feature
         return False

      # faccio una copia locale
      linearObjectList = qad_utils.QadLinearObjectList(self.linearObjectList)
            
      prevLinearObject, nextLinearObject = linearObjectList.getPrevNextLinearObjectsAtVertex(self.vertexAt)
      if prevLinearObject:
         firstPt = prevLinearObject.getStartPt()
         linearObjectList.remove(self.vertexAt - 1) # rimuovo la parte precedente
         
      if nextLinearObject:
         if prevLinearObject:
            # modifico la parte successiva
            secondPt = nextLinearObject.getEndPt()
            nextLinearObject.setSegment(firstPt, secondPt)
         else:
            linearObjectList.remove(self.vertexAt) # rimuovo la parte
      
      
      tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))

      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      geom = self.layerToMapCoordinates(layer, self.entity.getGeometry())

      updSubGeom = QgsGeometry.fromPolyline(linearObjectList.asPolyline(tolerance2ApproxCurve))
      updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
      if updGeom is None:
         return
      # trasformo la geometria nel crs del layer
      f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
      
      self.plugIn.beginEditCommand("Feature edited", layer)

      # plugIn, layer, feature, refresh, check_validity
      if qad_layer.updateFeatureToLayer(self.plugIn, layer, f, False, False) == False:
         self.plugIn.destroyEditCommand()
         return False

      self.plugIn.endEditCommand()


   #============================================================================
   # waitForBasePt
   #============================================================================
   def waitForBasePt(self):
      self.step = 2   
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_BASE_PT)

      # si appresta ad attendere un punto
      self.waitForPoint(QadMsg.translate("Command_GRIP", "Specify base point: "))


   #============================================================================
   # waitForNewVertex
   #============================================================================
   def waitForNewVertex(self):
      # imposto il map tool
      self.getPointMapTool().setVertexAt(self.vertexAt, self.after)
      if self.basePt is not None:
         self.getPointMapTool().firstPt = self.basePt
      self.getPointMapTool().setMode(Qad_pedit_maptool_ModeEnum.ASK_FOR_NEW_VERTEX)

      keyWords = QadMsg.translate("Command_GRIP", "Base point") + "/" + \
                 QadMsg.translate("Command_GRIP", "Copy") + "/" + \
                 QadMsg.translate("Command_GRIP", "Undo") + "/" + \
                 QadMsg.translate("Command_GRIP", "eXit")
      prompt = QadMsg.translate("Command_GRIPINSERTREMOVEVERTEX", "Specify the position of the new vertex or [{0}]: ").format(keyWords)

      englishKeyWords = "Base point" + "/" + "Copy" + "/" + "Undo" + "/" "eXit"
      keyWords += "_" + englishKeyWords

      # si appresta ad attendere un punto o enter o una parola chiave
      # msg, inputType, default, keyWords, valori positivi
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)
      self.step = 1


   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapSettings().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
         return True # fine comando
     
      #=========================================================================
      # RICHIESTA SELEZIONE OGGETTI
      if self.step == 0: # inizio del comando
         if self.entity is None: # non ci sono oggetti da stirare
            return True

         if self.insert_mode:
            self.showMsg(QadMsg.translate("Command_GRIPINSERTREMOVEVERTEX", "\n** ADD VERTEX **\n"))
            # si appresta ad attendere un nuovo punto
            self.waitForNewVertex()
         else:
            self.showMsg(QadMsg.translate("Command_GRIPINSERTREMOVEVERTEX", "\n** REMOVE VERTEX **\n"))
            self.removeVertexAt()
            return True
         
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL NUOVO VERTICE DA INSERIRE (da step = 1)
      elif self.step == 1:
         ctrlKey = False
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.copyEntities == False:
                     self.skipToNextGripCommand = True
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
            ctrlKey = self.getPointMapTool().ctrlKey
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_GRIP", "Base point") or value == "Base point":
               # si appresta ad attendere il punto base
               self.waitForBasePt()
            elif value == QadMsg.translate("Command_GRIP", "Copy") or value == "Copy":
               # Copia entità lasciando inalterate le originali
               self.copyEntities = True                     
               # si appresta ad attendere un nuovo punto
               self.waitForNewVertex()
            elif value == QadMsg.translate("Command_GRIP", "Undo") or value == "Undo":
               if self.nOperationsToUndo > 0: 
                  self.nOperationsToUndo = self.nOperationsToUndo - 1
                  self.plugIn.undoEditCommand()
               else:
                  self.showMsg(QadMsg.translate("QAD", "\nThe command has been canceled."))                  
               # si appresta ad attendere un nuovo punto
               self.waitForNewVertex()
            elif value == QadMsg.translate("Command_GRIP", "eXit") or value == "eXit":
               return True # fine comando
         elif type(value) == QgsPoint:
            if ctrlKey:
               self.copyEntities = True
   
            offsetX = value.x() - self.basePt.x()
            offsetY = value.y() - self.basePt.y()
            value.set(self.firstPt.x() + offsetX, self.firstPt.y() + offsetY)
            self.insertVertexAt(value)

            if self.copyEntities == False:
               return True
            # si appresta ad attendere un nuovo punto
            self.waitForNewVertex()
         else:
            if self.copyEntities == False:
               self.skipToNextGripCommand = True
            return True # fine comando

         return False
              
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO BASE (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  pass # opzione di default
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == QgsPoint: # se é stato inserito il punto base
            self.basePt.set(value.x(), value.y())
            # imposto il map tool
            self.getPointMapTool().basePt = self.basePt
            self.getPointMapTool().firstPt = self.basePt
            
         # si appresta ad attendere un nuovo punto
         self.waitForNewVertex()

         return False
      

#============================================================================
# Classe che gestisce il comando per convertire in arco o in linea un segmento per i grip
#============================================================================
class QadGRIPARCLINECONVERTCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadGRIPARCLINECONVERTCommandClass(self.plugIn)

   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.entity = None
      self.skipToNextGripCommand = False
      self.copyEntities = False
      self.nOperationsToUndo = 0
      self.basePt = QgsPoint()

      self.lineToArc = True
      self.partAt = 0
      self.linearObjectList = qad_utils.QadLinearObjectList() # in map coordinate

   def __del__(self):
      QadCommandClass.__del__(self)


   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_gripLineToArcConvert_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None


   def setLineToArcConvert_Mode(self):
      self.lineToArc = True
      
   def setArcToLineConvert_Mode(self):
      self.lineToArc = False


   #============================================================================
   # setSelectedEntityGripPoints
   #============================================================================
   def setSelectedEntityGripPoints(self, entitySetGripPoints):
      # lista delle entityGripPoint con dei grip point selezionati
      # setta la prima entità con un grip selezionato
      self.entity = None
      for entityGripPoints in entitySetGripPoints.entityGripPoints:
         for gripPoint in entityGripPoints.gripPoints:
            # grip point selezionato
            if gripPoint.getStatus() == qad_grip.QadGripStatusEnum.SELECTED and \
               (gripPoint.gripType == qad_grip.QadGripPointTypeEnum.LINE_MID_POINT or \
                gripPoint.gripType == qad_grip.QadGripPointTypeEnum.ARC_MID_POINT):
               # verifico se l'entità appartiene ad uno stile di quotatura
               if entityGripPoints.entity.isDimensionComponent():
                  return False
               if entityGripPoints.entity.getEntityType() != QadEntityGeomTypeEnum.LINESTRING and \
                  entityGripPoints.entity.getEntityType() != QadEntityGeomTypeEnum.ARC:
                  return False
               
               # setta: self.entity, self.linearObjectList, self.atSubGeom
               self.entity = entityGripPoints.entity

               firstPt = QgsPoint(gripPoint.getPoint())
               # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
               geom = self.layerToMapCoordinates(self.entity.layer, self.entity.getGeometry())
               # ritorna una tupla (<The squared cartesian distance>,
               #                    <minDistPoint>
               #                    <afterVertex>
               #                    <leftOf>)
               dummy = qad_utils.closestSegmentWithContext(firstPt, geom)
               if dummy[2] is not None:
                  # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
                  subGeom, self.atSubGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])
                  self.linearObjectList.fromPolyline(subGeom.asPolyline())
                  # setto il n. della parte
                  self.partAt = gripPoint.nVertex
                  
                  self.getPointMapTool().setLinearObjectList(self.linearObjectList, self.entity.layer, self.partAt)
                  
                  return True

      return False


   #============================================================================
   # convertLineToArc
   #============================================================================
   def convertLineToArc(self, pt):
      layer = self.entity.layer
      f = self.entity.getFeature()
      if f is None: # non c'è più la feature
         return False
      
      # faccio una copia locale
      linearObjectList = qad_utils.QadLinearObjectList(self.linearObjectList)

      tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
      linearObject = linearObjectList.getLinearObjectAt(self.partAt)
      if linearObject.isArc(): # se è già arco
         return False
      
      startPt = linearObject.getStartPt()
      endPt = linearObject.getEndPt()
      arc = QadArc()
      if arc.fromStartSecondEndPts(startPt, pt, endPt) == False:
         return
      if qad_utils.ptNear(startPt, arc.getStartPt()):
         linearObject.setArc(arc, False) # arco non inverso
      else:
         linearObject.setArc(arc, True) # arco inverso
         
      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      geom = self.layerToMapCoordinates(layer, self.entity.getGeometry())

      updSubGeom = QgsGeometry.fromPolyline(linearObjectList.asPolyline(tolerance2ApproxCurve))
      updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
      if updGeom is None:
         return
      # trasformo la geometria nel crs del layer
      f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
      
      self.plugIn.beginEditCommand("Feature edited", layer)
   
      if self.copyEntities == False:
         # plugIn, layer, feature, refresh, check_validity
         if qad_layer.updateFeatureToLayer(self.plugIn, layer, f, False, False) == False:
            self.plugIn.destroyEditCommand()
            return False
      else:
         # plugIn, layer, features, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(self.plugIn, layer, f, None, False, False) == False:
            self.plugIn.destroyEditCommand()
            return False

      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1


   #============================================================================
   # convertArcToLine
   #============================================================================
   def convertArcToLine(self):
      layer = self.entity.layer
      f = self.entity.getFeature()
      if f is None: # non c'è più la feature
         return False
      
      # faccio una copia locale
      linearObjectList = qad_utils.QadLinearObjectList(self.linearObjectList)

      tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))

      linearObject = linearObjectList.getLinearObjectAt(self.partAt)
      if linearObject.isSegment(): # se è già segmento retto
         return False
      
      linearObject.setSegment(linearObject.getStartPt(), linearObject.getEndPt())
         
      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      geom = self.layerToMapCoordinates(layer, self.entity.getGeometry())
               
      updSubGeom = QgsGeometry.fromPolyline(linearObjectList.asPolyline(tolerance2ApproxCurve))
      updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
      if updGeom is None:
         return
      # trasformo la geometria nel crs del layer
      f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
      
      self.plugIn.beginEditCommand("Feature edited", layer)
   
      if self.copyEntities == False:
         # plugIn, layer, feature, refresh, check_validity
         if qad_layer.updateFeatureToLayer(self.plugIn, layer, f, False, False) == False:
            self.plugIn.destroyEditCommand()
            return False
      else:
         # plugIn, layer, features, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(self.plugIn, layer, f, None, False, False) == False:
            self.plugIn.destroyEditCommand()
            return False

      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1


   #============================================================================
   # waitForConvertToArc
   #============================================================================
   def waitForConvertToArc(self):
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_gripLineToArcConvert_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_SECOND_PT)

      keyWords = QadMsg.translate("Command_GRIP", "Copy") + "/" + \
                 QadMsg.translate("Command_GRIP", "Undo") + "/" + \
                 QadMsg.translate("Command_GRIP", "eXit")
      prompt = QadMsg.translate("Command_GRIPARCLINECONVERT", "Specify the arc middle point or [{0}]: ").format(keyWords)

      englishKeyWords = "Copy" + "/" + "Undo" + "/" "eXit"
      keyWords += "_" + englishKeyWords

      # si appresta ad attendere un punto o enter o una parola chiave
      # msg, inputType, default, keyWords, valori positivi
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)
      self.step = 1


   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapSettings().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
         return True # fine comando
     
      #=========================================================================
      # RICHIESTA SELEZIONE OGGETTI
      if self.step == 0: # inizio del comando
         if self.entity is None: # non ci sono oggetti da stirare
            return True

         if self.lineToArc:
            self.showMsg(QadMsg.translate("Command_GRIPINSERTREMOVEVERTEX", "\n** CONVERT TO ARC **\n"))
            # si appresta ad attendere un punto per definire l'arco
            self.waitForConvertToArc()
         else:
            self.showMsg(QadMsg.translate("Command_GRIPINSERTREMOVEVERTEX", "\n** CONVERT TO LINE **\n"))
            self.convertArcToLine()
            return True
         
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL NUOVO PUNTO PER DEFINIRE UN ARCO (da step = 1)
      elif self.step == 1:
         ctrlKey = False
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.copyEntities == False:
                     self.skipToNextGripCommand = True
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
            ctrlKey = self.getPointMapTool().ctrlKey
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_GRIP", "Copy") or value == "Copy":
               # Copia entità lasciando inalterate le originali
               self.copyEntities = True                     
               # si appresta ad attendere un punto per definire l'arco
               self.waitForConvertToArc()
            elif value == QadMsg.translate("Command_GRIP", "Undo") or value == "Undo":
               if self.nOperationsToUndo > 0: 
                  self.nOperationsToUndo = self.nOperationsToUndo - 1
                  self.plugIn.undoEditCommand()
               else:
                  self.showMsg(QadMsg.translate("QAD", "\nThe command has been canceled."))                  
               # si appresta ad attendere un punto per definire l'arco
               self.waitForConvertToArc()
            elif value == QadMsg.translate("Command_GRIP", "eXit") or value == "eXit":
               return True # fine comando
         elif type(value) == QgsPoint:
            if ctrlKey:
               self.copyEntities = True
   
            self.convertLineToArc(value)

            if self.copyEntities == False:
               return True
            # si appresta ad attendere un punto per definire l'arco
            self.waitForConvertToArc()
         else:
            if self.copyEntities == False:
               self.skipToNextGripCommand = True
            return True # fine comando

         return False
