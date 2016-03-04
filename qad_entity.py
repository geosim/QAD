# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per la gestione delle entità
 
                              -------------------
        begin                : 2013-08-22
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


# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from qgis.utils import iface
import sys


import qad_utils
from qad_arc import *
from qad_circle import *
import qad_layer
import qad_stretch_fun


#===============================================================================
# QadEntityGeomTypeEnum class.
#===============================================================================
class QadEntityGeomTypeEnum():
   NONE                = 0
   SYMBOL              = 1
   TEXT                = 2
   ARC                 = 3
   CIRCLE              = 4
   LINESTRING          = 5


#===============================================================================
# QadEntity entity class
#===============================================================================
class QadEntity():
    
   def __init__(self, entity = None):
      self.entityType = QadEntityGeomTypeEnum.NONE
      self.qadGeom = None # in crs del canvas per lavorare con coordinate piane xy
      self.dimStyle = None
      self.dimId = None
      
      if entity is not None:
         self.set(entity.layer, entity.featureId)
      else:    
         self.layer = None
         self.featureId = None


   def whatIs(self):
      return "ENTITY"

   
   def isDimensionComponent(self):
      # se entityType non è già stato inizializzato
      if self.entityType == QadEntityGeomTypeEnum.NONE:
         self.__initQadInfo()

      return (self.dimStyle is not None) and (self.dimId is not None)


   def __fromPoyline(self, pointList): # funzione privata
      # restituisce entityType, qadGeom
      arc = QadArc()
      startEndVertices = arc.fromPolyline(pointList, 0)
      # se la polilinea è composta solo da un arco
      if startEndVertices and startEndVertices[0] == 0 and startEndVertices[1] == len(pointList)-1:
         return QadEntityGeomTypeEnum.ARC, arc # oggetto arco
      else:
         circle = QadCircle()
         startEndVertices = circle.fromPolyline(pointList, 0)
         # se la polilinea è composta solo da un cerchio
         if startEndVertices and startEndVertices[0] == 0 and startEndVertices[1] == len(pointList)-1:
            return QadEntityGeomTypeEnum.CIRCLE, circle # oggetto cerchio
         else:
            linearObjectList = qad_utils.QadLinearObjectList() # oggetto QadLinearObjectList
            linearObjectList.fromPolyline(pointList)
            return QadEntityGeomTypeEnum.LINESTRING, linearObjectList
      
      return QadEntityGeomTypeEnum.NONE, None


   def __initQadInfo(self):
      # inizializza entityType, qadGeom, dimStyle, dimId
      if self.isInitialized() == False:
         return QadEntityGeomTypeEnum.NONE

      self.dimStyle = None
      self.dimId = None

      g = self.getGeometry()
      if g is None:
         return QadEntityGeomTypeEnum.NONE

      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      coordTransform = QgsCoordinateTransform(self.layer.crs(), iface.mapCanvas().mapRenderer().destinationCrs())
      g.transform(coordTransform)

      wkbType = g.wkbType()
      if wkbType == QGis.WKBPoint:
         from qad_dim import QadDimStyles # to avoid cyclic import

         # verifico se l'entità appartiene ad uno stile di quotatura
         dimStyle, dimId = QadDimStyles.getDimIdByEntity(self)
         if (dimStyle is not None) and (dimId is not None):
            self.dimStyle = dimStyle # stile di quotatura di appartenenza
            self.dimId = dimId # codice quotatura di appartenenza
            
         if qad_layer.isTextLayer(self.layer):
            self.entityType = QadEntityGeomTypeEnum.TEXT
         elif qad_layer.isSymbolLayer(self.layer):
            self.entityType = QadEntityGeomTypeEnum.SYMBOL
         self.qadGeom = g.asPoint() # un punto

      if wkbType == QGis.WKBMultiPoint:
         if qad_layer.isTextLayer(self.layer):
            self.entityType = QadEntityGeomTypeEnum.TEXT
         elif qad_layer.isSymbolLayer(self.layer):
            self.entityType = QadEntityGeomTypeEnum.SYMBOL
         self.qadGeom = g.asMultiPoint() # lista di punti

      elif wkbType == QGis.WKBLineString:
         from qad_dim import QadDimStyles # to avoid cyclic import

         # verifico se l'entità appartiene ad uno stile di quotatura
         dimStyle, dimId = QadDimStyles.getDimIdByEntity(self)
         if (dimStyle is not None) and (dimId is not None):
            self.entityType = QadEntityGeomTypeEnum.DIMENSION_COMPONENT
            self.dimStyle = dimStyle # stile di quotatura di appartenenza
            self.dimId = dimId # codice quotatura di appartenenza

         self.entityType, self.qadGeom = self.__fromPoyline(g.asPolyline())

      elif wkbType == QGis.WKBMultiLineString:         
         self.entityType = []
         self.qadGeom = []
         lineList = g.asMultiPolyline() # vettore di linee
         for line in lineList:
            entityType, qadGeom = self.__fromPoyline(g.asPolyline())
            self.entityType.append(entityType)
            self.qadGeom.append(qadGeom)

      elif wkbType == QGis.WKBPolygon:
         self.entityType = []
         self.qadGeom = []
         polygon = g.asPolygon() # vettore di linee
         for line in polygon:
            entityType, qadGeom = self.__fromPoyline(line)
            self.entityType.append(entityType)
            self.qadGeom.append(qadGeom)

      elif wkbType == QGis.WKBMultiPolygon:
         self.entityType = []
         self.qadGeom = []
         polygonList = g.asMultiPolygon() # vettore di poligoni
         for polygon in polygonList:
            partialEntityType = []
            partialQadGeom = []
            for line in polygon:
               entityType, qadGeom = self.__fromPoyline(line)
               partialEntityType.append(entityType)
               partialQadGeom.append(qadGeom)
            self.entityType.append(partialEntityType)
            self.qadGeom.append(partialQadGeom)


   def getEntityType(self, atGeom = 0, atSubGeom = 0):
      # se entityType non è già stato inizializzato
      if self.entityType == QadEntityGeomTypeEnum.NONE:
         self.__initQadInfo()
      
      # se entityType è stato inizializzato
      if self.entityType != QadEntityGeomTypeEnum.NONE:
         if type(self.entityType) == list:
            if atGeom < len(self.entityType):
               if type(self.entityType[atGeom]) == list:
                  if atSubGeom < len(self.entityType[atGeom]):
                     return self.entityType[atGeom][atSubGeom]
                  else:
                     return QadEntityGeomTypeEnum.NONE
               else:
                  return QadEntityGeomTypeEnum.NONE if atSubGeom != 0 else self.entityType[atGeom]
            else:
               return QadEntityGeomTypeEnum.NONE
         else:
            return QadEntityGeomTypeEnum.NONE if atGeom != 0 else self.entityType
      else:
         return QadEntityGeomTypeEnum.NONE


   def getQadGeom(self, atGeom = 0, atSubGeom = 0):
      # se entityType non è già stato inizializzato
      if self.qadGeom is None:
         self.__initQadInfo()
      
      # se qadGeom è stato inizializzato
      if self.qadGeom is not None:
         if type(self.qadGeom) == list:
            if atGeom < len(self.qadGeom):
               if type(self.qadGeom[atGeom]) == list:
                  if atSubGeom < len(self.qadGeom[atGeom]):
                     return self.qadGeom[atGeom][atSubGeom]
                  else:
                     return None
               else:
                  return None if atSubGeom != 0 else self.qadGeom[atGeom]
            else:
               return None
         else:
            return None if atGeom != 0 else self.qadGeom
      else:
         return None


   def isInitialized(self):
      if (self.layer is None) or (self.featureId is None):
         return False
      else:
         return True


   def clear(self):
      self.layer = None
      self.featureId = None
      self.entityType = QadEntityGeomTypeEnum.NONE
      self.qadGeom = None
      self.dimStyle = None
      self.dimId = None
      
      
   def __eq__(self, entity):
      """self == other"""
      if self.isInitialized() == False or entity.isInitialized() == False :
         return False

      if self.layerId() == entity.layerId() and self.featureId == entity.featureId:      
         return True
      else:
         return False    
  
  
   def __ne__(self, entity):
      """self != other"""
      if self.isInitialized() == False or entity.isInitialized() == False:
         return True

      if self.layerId() != entity.layerId() or self.featureId != entity.featureId:      
         return True
      else:
         return False


   def layerId(self):
      if self.isInitialized() == False:
         return None
      return self.layer.id()


   def set(self, layer, featureId):
      self.clear()
      self.layer = layer # il layer non si può copiare
      self.featureId = featureId # copio l'identificativo di feature
      return self


   def getFeature(self):
      if self.isInitialized() == False:
         return None
      
      return qad_utils.getFeatureById(self.layer, self.featureId)
      

   def exists(self):
      if self.getFeature() is None:
         return False
      else:
         return True


   def getGeometry(self):
      feature = self.getFeature()
      if feature is None:
         return None      
      return QgsGeometry(feature.geometry()) # fa una copia


   def __getPtsFromQadGeom(self, qadGeom, tolerance2ApproxCurve):
      if type(qadGeom) == list: # entità composta da più geometrie
         res = []
         for subGeom in qadGeom:
            res.append(self.__getPtsFromQadGeom(subGeom, tolerance2ApproxCurve))
         return res
      else:
         if type(qadGeom) == QgsPoint:
            return qadGeom
         else:
            return qadGeom.asPolyline(tolerance2ApproxCurve)


   def __getGeomFromQadGeom(self, qadGeom, tolerance2ApproxCurve):
      Pts = self.__getPtsFromQadGeom(qadGeom, tolerance2ApproxCurve)
      if Pts is None:
         return None
      if self.layer.geometryType() == QGis.Point:
         if type(Pts) == list:
            g = QgsGeometry.fromMultiPoint(Pts)
         else:
            g = QgsGeometry.fromPoint(Pts)
      if self.layer.geometryType() == QGis.Line:
         if type(Pts[0]) == list:
            g = QgsGeometry.fromMultiPolyline(Pts)
         else:
            g = QgsGeometry.fromPolyline(Pts)
      if self.layer.geometryType() == QGis.Polygon:
         if type(Pts[0][0]) == list:
            g = QgsGeometry.fromMultiPolygon(Pts)
         else:
            g = QgsGeometry.fromPolygon(Pts)

      # trasformo la geometria nel crs del layer
      coordTransform = QgsCoordinateTransform(iface.mapCanvas().mapRenderer().destinationCrs(), self.layer.crs())
      g.transform(coordTransform)
      return g
      

#    questa funzione non ha senso perchè feature è una variabile locale temporanea a cui viene settata la geometria
#    ma poi, a fine funzione, viene distrutta.
#    def setGeometry(self, geom):
#       feature = self.getFeature()
#       if feature is None:
#          return None      
#       return feature.setGeometry(geom)


   def getAttribute(self, attribName):
      feature = self.getFeature()
      if feature is None:
         return None
      try:
         return feature.attribute(attribName)
      except:
         return None

   
   def getAttributes(self):
      feature = self.getFeature()
      if feature is None:
         return None

      return feature.attributes()[:] # fa una copia


   def selectOnLayer(self, incremental = True):
      if self.isInitialized() == True:
         if incremental == False:
            self.layer.removeSelection()

         self.layer.select(self.featureId) # aaaaaaaaaaaaaaaaaaaaaaaaaa qui parte l'evento activate di qad_maptool


   def deselectOnLayer(self):
      if self.isInitialized() == False:
         return False

      self.layer.deselect(self.featureId)


   #===============================================================================
   # operazioni geometriche - inizio
   
   def gripStretch(self, basePt, ptListToStretch, offSetX, offSetY, tolerance2ApproxCurve):
      # se entityType è già stato inizializzato
      if self.entityType == QadEntityGeomTypeEnum.NONE:
         self.__initQadInfo()
   
      return qad_stretch_fun.gripStretchQadGeometry(self.qadGeom, basePt, ptListToStretch, offSetX, offSetY, tolerance2ApproxCurve)

   def gripGeomStretch(self, basePt, ptListToStretch, offSetX, offSetY, tolerance2ApproxCurve):
      newQadGeom = self.gripStretch(basePt, ptListToStretch, offSetX, offSetY, tolerance2ApproxCurve)
      if newQadGeom is None:
         return None
      return self.__getGeomFromQadGeom(newQadGeom, tolerance2ApproxCurve)


# operazioni geometriche - fine
#===============================================================================


#===============================================================================
# QadLayerEntitySet entities of a layer class
#===============================================================================
class QadLayerEntitySet():
    
   def __init__(self, layerEntitySet = None):
      if layerEntitySet is not None:
         self.set(layerEntitySet.layer, layerEntitySet.featureIds)
      else:    
         self.layer = None
         self.featureIds = []


   def whatIs(self):
      return "LAYERENTITYSET"


   def isInitialized(self):
      if self.layer is None:
         return False
      else:
         return True


   def isEmpty(self):
      if self.isInitialized() == False:
         return True
      return not self.featureIds


   def count(self):
      if self.isInitialized() == False:
         return 0
      return len(self.featureIds)


   def clear(self):
      if self.isInitialized() == False:
         return 0
      self.layer = None
      del self.featureIds[:] 


   def layerId(self):
      if self.isInitialized() == False:
         return None
      return self.layer.id()


   def set(self, layer, features = None):
      if type(layer) == QgsVectorLayer:
         self.layer = layer # il layer non si può copiare
         self.featureIds = []       
         if features is not None:
            self.addFeatures(features)
      else: # layer è una entità
         return self.set(layer.layer, layer.featureIds)


   def initByCurrentQgsSelectedFeatures(self, layer):
      self.clear()
      self.layer = layer
      self.featureIds = self.layer.selectedFeaturesIds()


   def getFeature(self, featureId):
      if self.isInitialized() == False:
         return None
      return qad_utils.getFeatureById(self.layer, featureId)
   

   def getGeometry(self, featureId):
      feature = self.getFeature(featureId)
      if feature is None:
         return None      
      return QgsGeometry(feature.geometry()) # fa una copia

   def setGeometry(self, featureId, geom):
      feature = self.getFeature(featureId)
      if feature is None:
         return None
      return feature.setGeometry(geom)


   def getGeometryCollection(self, destCRS = None):
      result = []
      if destCRS is not None:
         coordTransform = QgsCoordinateTransform(self.layer.crs(), destCRS) # trasformo la geometria
      for featureId in self.featureIds:
         g = self.getGeometry(featureId)
         if g is not None:
            if destCRS is not None:
               g.transform(coordTransform)

               # Per un baco sconosciuto quando trasformo la geometria se poi ne faccio un buffer
               # il calcolo dà un risultato sbagliato quando la geometria é nuova o modificata
               # (in cache del layer) e il sistema di coordinate é diverso de quello della mappa corrente 
               wkbType = g.wkbType()
               if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:               
                  g = QgsGeometry().fromPoint(g.asPoint())
               elif wkbType == QGis.WKBMultiPoint or wkbType == QGis.WKBMultiPoint25D:
                  g = QgsGeometry().fromMultiPoint(g.asMultiPoint())
               elif wkbType == QGis.WKBLineString or wkbType == QGis.WKBLineString25D:
                  g = QgsGeometry().fromPolyline(g.asPolyline())
               elif wkbType == QGis.WKBMultiLineString or wkbType == QGis.WKBMultiLineString25D:
                  g = QgsGeometry().fromMultiPolyline(g.asMultiPolyline())
               elif wkbType == QGis.WKBPolygon or wkbType == QGis.WKBPolygon25D:
                  g = QgsGeometry().fromPolygon(g.asPolygon())
               elif wkbType == QGis.WKBMultiPolygon or wkbType == QGis.WKBMultiPolygon25D:
                  g = QgsGeometry().fromMultiPolygon(g.asMultiPolygon())
                    
            result.append(g)
      return result


   def getFeatureCollection(self):
      result = []
      for featureId in self.featureIds:
         f = self.getFeature(featureId)
         if f is not None:                    
            result.append(f)
      return result

   
   def selectOnLayer(self, incremental = True):
      if self.isInitialized() == True:            
         if len(self.featureIds) > 0:
            if incremental == False:
               self.layer.removeSelection()
            
            self.layer.select(self.featureIds)
         else:
            if incremental == False:
               self.layer.removeSelection()
               

   def deselectOnLayer(self):
      if self.isInitialized() == True:
         if len(self.featureIds) > 0:
            self.layer.deselect(self.featureIds)

   
   def containsFeature(self, feature):
      if self.isInitialized() == False:
         return False

      if type(feature) == QgsFeature:     
         return feature.id() in self.featureIds
      else:
         return feature in self.featureIds
           

   def containsEntity(self, entity):
      if self.isInitialized() == False:
         return False
      
      if self.layerId() != entity.layerId(): 
         return False
      return containsFeature(entity.featureId)
   
                                      
   def addFeature(self, feature):
      if self.isInitialized() == False:
         return False
      
      if type(feature) == QgsFeature:
         if self.containsFeature(feature.id()) == False:    
            self.featureIds.append(feature.id())
            return True
         else:
            return False
      else:
         if self.containsFeature(feature) == False:    
            self.featureIds.append(feature)
            return True
         else:
            return False


   def removeFeature(self, feature):
      if self.isInitialized() == False:
         return False
      
      try:
         if type(feature) == QgsFeature:     
            return self.featureIds.remove(feature.id())
         else:
            return self.featureIds.remove(feature)
      except:
         return None


   def addEntity(self, entity):
      if self.isInitialized() == False:
         self.set(entity.layer)
      else:
         if self.layerId() != entity.layerId(): 
            return
      
      self.addFeature(entity.featureId)


   def removeEntity(self, entity):
      if self.isInitialized() == False:
         return False

      if self.layerId() != entity.layerId(): 
         return False
         
      return self.removeFeature(entity.featureId)


   def addFeatures(self, features):
      if self.isInitialized() == False:
         return None
      for feature in features:
         if type(feature) == QgsFeature:
            self.addFeature(feature.id())
         else:
            self.addFeature(feature) # featureId


   def addLayerEntitySet(self, layerEntitySet):
      if self.isInitialized() == False:
         self.set(layerEntitySet.layer)
      else:
         if self.layerId() != layerEntitySet.layerId():
            return
      self.addFeatures(layerEntitySet.featureIds)
      
      
   def unite(self, layerEntitySet):
      if self.isInitialized() == False:
         return
      
      if self.layerId() == layerEntitySet.layerId():
         self.featureIds = list(set.union(set(self.featureIds), set(layerEntitySet.featureIds)))


   def intersect(self, layerEntitySet):
      if self.isInitialized() == False:
         return
      
      if self.layerId() == layerEntitySet.layerId():
         self.featureIds = list(set(self.featureIds) & set(layerEntitySet.featureIds))    


   def subtract(self, layerEntitySet):
      if self.isInitialized() == False:
         return
      
      if self.layerId() == layerEntitySet.layerId():      
         self.featureIds = list(set(self.featureIds) - set(layerEntitySet.featureIds)) 


   def getNotExistingFeaturedIds(self):
      featureIds = []
      if self.isInitialized() == True:
         feature = QadEntity()
         for featureId in self.featureIds:
            feature.set(self.layer, featureId)
            if not feature.exists():
               featureIds.append(featureId)
      return featureIds
      

   def removeNotExisting(self):
      featureIds = self.getNotExistingFeaturedIds()
      self.featureIds = list(set(self.featureIds) - set(featureIds))    
      

#===============================================================================
# QadEntitySet entities of a layers class
#===============================================================================
class QadEntitySet():
    
   def __init__(self, entitySet = None):
      self.layerEntitySetList = []
      if entitySet is not None:
         self.set(entitySet)


   def whatIs(self):
      return "ENTITYSET"


   def isEmpty(self):
      for layerEntitySet in self.layerEntitySetList:
         if layerEntitySet.isEmpty() == False:
            return False
      return True


   def count(self):
      tot = 0
      for layerEntitySet in self.layerEntitySetList:
         tot = tot + layerEntitySet.count()
      return tot


   def clear(self):
      del self.layerEntitySetList[:] 


   def set(self, entitySet):      
      self.clear()
      for layerEntitySet in entitySet.layerEntitySetList:
         self.addLayerEntitySet(layerEntitySet)


   def initByCurrentQgsSelectedFeatures(self, layers):
      self.clear()

      for layer in layers:
         if layer.selectedFeatureCount() > 0:
            layerEntitySet = QadLayerEntitySet()
            layerEntitySet.initByCurrentQgsSelectedFeatures(layer)
            self.layerEntitySetList.append(layerEntitySet)


   def findLayerEntitySet(self, layer):
      if layer is None:
         return None
      if type(layer) == QgsVectorLayer: # layer
         return self.findLayerEntitySet(layer.id())     
      elif type(layer) == unicode: # id del layer
         for layerEntitySet in self.layerEntitySetList:
            if layerEntitySet.layerId() == layer:
               return layerEntitySet
         return None
      else: # QadLayerEntitySet
         return self.findLayerEntitySet(layer.layer)     


   def getLayerList(self):
      layerList = []
      for layerEntitySet in self.layerEntitySetList:
         layerList.append(layerEntitySet.layer)
      return layerList
   

   def getGeometryCollection(self, destCRS = None):
      result = []
      for layerEntitySet in self.layerEntitySetList:
         partial = layerEntitySet.getGeometryCollection(destCRS)
         if partial is not None:
            result.extend(partial)
      return result
   

   def getFeatureCollection(self):
      result = []
      for layerEntitySet in self.layerEntitySetList:
         partial = layerEntitySet.getFeatureCollection()
         if partial is not None:
            result.extend(partial)
      return result


   def selectOnLayer(self, incremental = True):
      for layerEntitySet in self.layerEntitySetList:
         layerEntitySet.selectOnLayer(incremental)


   def deselectOnLayer(self):
      for layerEntitySet in self.layerEntitySetList:
         layerEntitySet.deselectOnLayer()


   def containsEntity(self, entity):
      layerEntitySet = self.findLayerEntitySet(entity.layer)
      if layerEntitySet is None: 
         return False
      return layerEntitySet.containsFeature(entity.featureId)
      

   def addEntity(self, entity):
      if entity is None or entity.isInitialized() == False:
         return False
      layerEntitySet = self.findLayerEntitySet(entity.layer)
      if layerEntitySet is None: 
         layerEntitySet = QadLayerEntitySet()
         layerEntitySet.set(entity.layer)
         self.layerEntitySetList.append(layerEntitySet)
      return layerEntitySet.addFeature(entity.featureId)
         

   def removeEntity(self, entity):
      layerEntitySet = self.findLayerEntitySet(entity.layer)
      if layerEntitySet is None:
         return False
      return layerEntitySet.removeFeature(entity.featureId)
      
      
   def removeLayerEntitySet(self, layer):
      i = 0
      for layerEntitySet in self.layerEntitySetList:
         if layerEntitySet.id() == layer.id():
            del layerEntitySet[i]
            return True
         i = i + 1
      return False


   def addLayerEntitySet(self, layerEntitySet):      
      _layerEntitySet = self.findLayerEntitySet(layerEntitySet)
      if _layerEntitySet is None:
         _layerEntitySet = QadLayerEntitySet()
         _layerEntitySet.set(layerEntitySet.layer)
         self.layerEntitySetList.append(_layerEntitySet)
      _layerEntitySet.addFeatures(layerEntitySet.featureIds)
     
      
   def unite(self, entitySet):
      if entitySet is None:
         return
      for layerEntitySet in entitySet.layerEntitySetList:
         _layerEntitySet = self.findLayerEntitySet(layerEntitySet)
         if _layerEntitySet is None:
            _layerEntitySet = QadLayerEntitySet()
            _layerEntitySet.set(layerEntitySet.layer)
            self.layerEntitySetList.append(_layerEntitySet)
         _layerEntitySet.unite(layerEntitySet)
       

   def intersect(self, entitySet):
      if entitySet is None:
         return
      for i in xrange(len(self.layerEntitySetList) - 1, -1, -1):
         _layerEntitySet = self.layerEntitySetList[i]
         layerEntitySet = entitySet.findLayerEntitySet(_layerEntitySet)
         if layerEntitySet is None:
            del self.layerEntitySetList[i]
         else:
            _layerEntitySet.intersect(layerEntitySet)


   def subtract(self, entitySet):
      if entitySet is None:
         return
      for _layerEntitySet in self.layerEntitySetList:         
         layerEntitySet = entitySet.findLayerEntitySet(_layerEntitySet)
         if layerEntitySet is not None:
            _layerEntitySet.subtract(layerEntitySet)


   def removeNotExisting(self):
      for layerEntitySet in self.layerEntitySetList:         
         layerEntitySet.removeNotExisting()


   def removeNotEditable(self):
      for i in xrange(len(self.layerEntitySetList) - 1, -1, -1):    
         layerEntitySet = self.layerEntitySetList[i]
         if layerEntitySet.layer.isEditable() == False:
            del self.layerEntitySetList[i]
                  

   def removeGeomType(self, type):
      for i in xrange(len(self.layerEntitySetList) - 1, -1, -1):    
         layerEntitySet = self.layerEntitySetList[i]
         if layerEntitySet.layer.geometryType() == type:
            del self.layerEntitySetList[i]


   def purge(self):
      # rimuove i layer con zero oggetti
      for i in xrange(len(self.layerEntitySetList) - 1, -1, -1):    
         layerEntitySet = self.layerEntitySetList[i]
         if layerEntitySet.count() == 0:
            del self.layerEntitySetList[i]
                  
