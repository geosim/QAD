# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per la gestione delle entit�
 
                              -------------------
        begin                : 2013-08-22
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
from qgis.gui import *


import qad_debug
import qad_utils


#===============================================================================
# QadEntity entity class
#===============================================================================
class QadEntity():
    
   def __init__(self, entity = None):
      if entity is not None:
         self.set(entity.layer, entity.featureId)
      else:    
         self.layer = None
         self.featureId = None


   def whatIs(self):
      return "ENTITY"


   def isInitialized(self):
      if (self.layer is None) or (self.featureId is None):
         return False
      else:
         return True


   def clear(self):
      self.layer = None
      self.featureId = None
       
      
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
      #qad_debug.breakPoint()  
      self.layer = layer # il layer non si pu� copiare
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

   def setGeometry(self, geom):
      feature = self.getFeature()
      if feature is None:
         return None      
      return feature.setGeometry(geom)


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

         self.layer.select(self.featureId)


   def deselectOnLayer(self):
      if self.isInitialized() == False:
         return False

      self.layer.deselect(self.featureId)
   
      
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
         self.layer = layer # il layer non si pu� copiare
         self.featureIds = []       
         if features is not None:
            self.addFeatures(features)
      else:
         return self.set(layer.layer, layer.featureIds)
     
      
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

               # roby
               # Per un baco sconosciuto quando trasformo la geometria se poi ne faccio un buffer
               # il calcolo d� un risultato sbagliato quando la geometria � nuova o modificata
               # (in cache del layer) e il sistema di coordinate � diverso de quello della mappa corrente 
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
         return
      
      if type(feature) == QgsFeature:
         if self.containsFeature(feature.id()) == False:    
            self.featureIds.append(feature.id())
      else:
         if self.containsFeature(feature) == False:    
            self.featureIds.append(feature)


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
         #qad_debug.breakPoint()
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
      if entitySet is None:
         self.layerEntitySetList = []
      else:
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
      self.layerEntitySetList = []
      for layerEntitySet in entitySet.layerEntitySetList:
         self.addLayerEntitySet(layerEntitySet)


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
      #qad_debug.breakPoint()
      for layerEntitySet in self.layerEntitySetList:
         layerEntitySet.deselectOnLayer()


   def containsEntity(self, entity):
      layerEntitySet = self.findLayerEntitySet(entity.layer)
      if layerEntitySet is None: 
         return False
      return layerEntitySet.containsFeature(entity.featureId)
      

   def addEntity(self, entity):
      layerEntitySet = self.findLayerEntitySet(entity.layer)
      if layerEntitySet is None: 
         layerEntitySet = QadLayerEntitySet()
         layerEntitySet.set(entity.layer)
         self.layerEntitySetList.append(layerEntitySet)
      layerEntitySet.addFeature(entity.featureId)
         

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
                  
