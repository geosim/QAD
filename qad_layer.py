# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 funzioni per i layer
 
                              -------------------
        begin                : 2013-11-15
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
from qgis.gui import *
import re # regular expression


import qad_debug
from qad_msg import QadMsg
import qad_utils


#===============================================================================
# layerGeometryTypeToStr
#===============================================================================
def layerGeometryTypeToStr(geomType):
   """
   restituisce la stringa corrispondente al tipo di geometria del layer
   """
   msg = ""
   if (type(geomType) == list or type(geomType) == tuple): # se lista di tipi
      for gType in geomType:
         if len(msg) > 0:
            msg = msg + ", " 
         msg = msg + layerGeometryTypeToStr(gType)
   else:
      if geomType == QGis.Point:
         msg = QadMsg.translate("QAD", "punto") 
      elif geomType == QGis.Line:      
         msg = QadMsg.translate("QAD", "linea") 
      elif geomType == QGis.Polygon:      
         msg = QadMsg.translate("QAD", "poligono") 

   return msg


#===============================================================================
# getCurrLayerEditable
#===============================================================================
def getCurrLayerEditable(canvas, geomType = None):
   """
   Ritorna il layer corrente se è aggiornabile e compatibile con il tipo geomType +
   eventuale messaggio di errore.
   Se <geomType> è una lista allora verifica che sia compatibile con almeno un tipo nella lista <geomType>
   altrimenti se <> None verifica che sia compatibile con il tipo <geomType>
   """
   vLayer = canvas.currentLayer()
   if vLayer is None:
      return None, QadMsg.translate("QAD", "\nNessun layer corrente.\n")
   
   if (vLayer.type() != vLayer.VectorLayer):
      return None, QadMsg.translate("QAD", "\nIl layer corrente non è di tipo vettoriale.\n")

   if geomType is not None:
      if (type(geomType) == list or type(geomType) == tuple): # se lista di tipi
         if vLayer.geometryType() not in geomType:
            errMsg = QadMsg.translate("QAD", "\nIl tipo di geometria del layer corrente è {0} e non è valido.\n")
            errMsg = errMsg + QadMsg.translate("QAD", "Ammessi solo layer di tipo {1}.\n")
            errMsg.format(layerGeometryTypeToStr(vLayer.geometryType()), layerGeometryTypeToStr(geomType))
            return None, errMsg.format(layerGeometryTypeToStr(vLayer.geometryType()), layerGeometryTypeToStr(geomType))
      else:
         if vLayer.geometryType() != geomType:
            errMsg = QadMsg.translate("QAD", "\nIl tipo di geometria del layer corrente è {0} e non è valido.\n")
            errMsg = errMsg + QadMsg.translate("QAD", "Ammessi solo layer di tipo {1}.\n")
            errMsg.format(layerGeometryTypeToStr(vLayer.geometryType()), layerGeometryTypeToStr(geomType))
            return None, errMsg.format(layerGeometryTypeToStr(vLayer.geometryType()), layerGeometryTypeToStr(geomType))

   provider = vLayer.dataProvider()
   if not (provider.capabilities() & QgsVectorDataProvider.EditingCapabilities):
      return None, QadMsg.translate("QAD", "\nIl layer corrente non è modificabile.\n")
   
   if not vLayer.isEditable():
      return None, QadMsg.translate("QAD", "\nIl layer corrente non è modificabile.\n")

   return vLayer, None
  

#===============================================================================
# addPointToLayer
#===============================================================================
def addPointToLayer(plugIn, layer, point, transform = True, refresh = True, check_validity = False):
   """
   Aggiunge un punto ad un layer. Se il punto è già
   nel sistema di coordinate del layer allora non va trasformato se invece è nel
   sistema map-coordinate allora transform deve essere = True
   """
   if len(points) < 2:
      return False
     
   f = QgsFeature()
   
   if transform:
      transformedPoint = plugIn.canvas.mapRenderer().mapToLayerCoordinates(layer, point)
      g = QgsGeometry.fromPoint(transformedPoint)
   else:
      g = QgsGeometry.fromPoint(point)

   if check_validity:
      if not g.isGeosValid():
         return False
      
   f.setGeometry(g)
   
   # Add attributefields to feature.
   fields = layer.pendingFields()
   f.setFields(fields)

   # assegno i valori di default
   provider = layer.dataProvider()
   for field in fields.toList():
      i = fields.indexFromName(field.name())
      f[field.name()] = provider.defaultValue(i)

   if refresh == True:
      plugIn.beginEditCommand("Feature added", layer)

   if layer.addFeature(f, False):
      if refresh == True:
         plugIn.endEditCommand()
      plugIn.setLastEntity(layer, f.id())
      result = True
   else:
      if refresh == True:
         plugIn.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# addLineToLayer
#===============================================================================
def addLineToLayer(plugIn, layer, points, transform = True, refresh = True, check_validity = False):
   """
   Aggiunge una linea (lista di punti) ad un layer. Se la lista di punti è già
   nel sistema di coordinate del layer allora non va trasformata se invece è nel
   sistema  map-coordinate allora transform deve essere = True
   """
   if len(points) < 2: # almeno 2 punti
      return False
     
   f = QgsFeature()
   
   if transform:
      layerPoints = []
      for point in points:
         transformedPoint = plugIn.canvas.mapRenderer().mapToLayerCoordinates(layer, point)
         layerPoints.append(transformedPoint)    
      g = QgsGeometry.fromPolyline(layerPoints)
   else:
      g = QgsGeometry.fromPolyline(points)

   if check_validity:
      if not g.isGeosValid():
         return False
      
   f.setGeometry(g)
   
   # Add attributefields to feature.
   fields = layer.pendingFields()
   f.setFields(fields)

   # assegno i valori di default
   provider = layer.dataProvider()
   for field in fields.toList():
      i = fields.indexFromName(field.name())
      f[field.name()] = provider.defaultValue(i)

   if refresh == True:
      plugIn.beginEditCommand("Feature added", layer)

   if layer.addFeature(f, False):
      if refresh == True:
         plugIn.endEditCommand()
      plugIn.setLastEntity(layer, f.id())
      result = True
   else:
      if refresh == True:
         plugIn.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# addPolygonToLayer
#===============================================================================
def addPolygonToLayer(plugIn, layer, points, transform = True, refresh = True, check_validity = False):
   """
   Aggiunge un poligono (lista di punti) ad un layer. Se la lista di punti è già
   nel sistema di coordinate del layer allora non va trasformata se invece è nel
   sistema  map-coordinate allora transform deve essere = True
   """
   if len(points) < 3: # almeno 4 punti (il primo e l'ultimo sono uguali)
      return False
     
   f = QgsFeature()
   
   if transform:
      layerPoints = []
      for point in points:
         transformedPoint = plugIn.canvas.mapRenderer().mapToLayerCoordinates(layer, point)
         layerPoints.append(transformedPoint)      
      g = QgsGeometry.fromPolygon([layerPoints])
   else:
      g = QgsGeometry.fromPolygon([points])

   if check_validity:
      if not g.isGeosValid():
         return False
         
   f.setGeometry(g)
   
   # Add attributefields to feature.
   fields = layer.pendingFields()
   f.setFields(fields)

   # assegno i valori di default
   provider = layer.dataProvider()
   for field in fields.toList():
      i = fields.indexFromName(field.name())
      f[field.name()] = provider.defaultValue(i)

   if refresh == True:
      plugIn.beginEditCommand("Feature added", layer)

   if layer.addFeature(f, False):
      if refresh == True:
         plugIn.endEditCommand()
      plugIn.setLastEntity(layer, f.id())
      result = True
   else:
      if refresh == True:
         plugIn.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# addGeomToLayer
#===============================================================================
def addGeomToLayer(plugIn, layer, geom, coordTransform = None, refresh = True, check_validity = False):
   """
   Aggiunge una geometria ad un layer. Se la geometria è da convertire allora
   deve essere passato il parametro <coordTransform> di tipo QgsCoordinateTransform.
   refresh controlla la transazione del comando e il refresh del canvas
   """     
   f = QgsFeature()
   
   g = QgsGeometry(geom)
   if coordTransform is not None:
      g.transform(coordTransform)            

   if check_validity:
      if not g.isGeosValid():
         return False
      
   f.setGeometry(g)
   
   # Add attributefields to feature.
   fields = layer.pendingFields()
   f.setFields(fields)

   # assegno i valori di default
   provider = layer.dataProvider()
   for field in fields.toList():
      i = fields.indexFromName(field.name())
      f[field.name()] = provider.defaultValue(i)

   if refresh == True:
      plugIn.beginEditCommand("Feature added", layer)

   if layer.addFeature(f, False):
      if refresh == True:
         plugIn.endEditCommand()
      plugIn.setLastEntity(layer, f.id())
      result = True
   else:
      if refresh == True:
         plugIn.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# addGeomsToLayer
#===============================================================================
def addGeomsToLayer(plugIn, layer, geoms, coordTransform = None, refresh = True, check_validity = False):
   """
   Aggiunge le geometrie ad un layer. Se la geometria è da convertire allora
   deve essere passato il parametro <coordTransform> di tipo QgsCoordinateTransform.
   refresh controlla la transazione del comando e il refresh del canvas
   """
   if refresh == True:
      plugIn.beginEditCommand("Feature added", layer)
      
   for geom in geoms:
      if addGeomToLayer(plugIn, layer, geom, coordTransform, False, check_validity) == False:
         if refresh == True:
            plugIn.destroyEditCommand()
            return False
         
   if refresh == True:
      plugIn.endEditCommand()

   return True


#===============================================================================
# addFeatureToLayer
#===============================================================================
def addFeatureToLayer(plugIn, layer, f, coordTransform = None, refresh = True, check_validity = False):
   """
   Aggiunge una feature ad un layer. Se la geometria è da convertire allora
   deve essere passato il parametro <coordTransform> di tipo QgsCoordinateTransform.
   <refresh> controlla la transazione del comando e il refresh del canvas
   """     
   
   if coordTransform is not None:
      g = QgsGeometry(f.geometry())
      g.transform(coordTransform)            
      f.setGeometry(g)

   if check_validity:
      if not f.geometry().isGeosValid():
         return False
         
   if refresh == True:
      plugIn.beginEditCommand("Feature added", layer)

   if layer.addFeature(f, False):
      if refresh == True:
         plugIn.endEditCommand()
         
      plugIn.setLastEntity(layer, f.id())
      result = True
   else:
      if refresh == True:
         plugIn.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# addFeaturesToLayer
#===============================================================================
def addFeaturesToLayer(plugIn, layer, features, coordTransform = None, refresh = True, check_validity = False):
   """
   Aggiunge le feature ad un layer. Se la geometria è da convertire allora
   deve essere passato il parametro <coordTransform> di tipo QgsCoordinateTransform.
   <refresh> controlla la transazione del comando e il refresh del canvas
   """
   if refresh == True:
      plugIn.beginEditCommand("Feature added", layer)
      
   for f in features:
      if addFeatureToLayer(plugIn, layer, f, coordTransform, False, check_validity) == False:
         if refresh == True:
            plugIn.destroyEditCommand()
            return False
         
   if refresh == True:
      plugIn.endEditCommand()
   
   return True


#===============================================================================
# updateFeatureToLayer
#===============================================================================
def updateFeatureToLayer(plugIn, layer, f, refresh = True, check_validity = False):
   """
   Aggiorna la feature ad un layer.
   refresh controlla la transazione del comando e il refresh del canvas
   """        
   if check_validity:
      if not f.geometry().isGeosValid():
         return False
      
   if refresh == True:
      plugIn.beginEditCommand("Feature modified", layer)

   if layer.updateFeature(f):
      if refresh == True:
         plugIn.endEditCommand()
         
      result = True
   else:
      if refresh == True:
         plugIn.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# updateFeaturesToLayer
#===============================================================================
def updateFeaturesToLayer(plugIn, layer, features, refresh = True, check_validity = False):
   """
   Aggiorna le features ad un layer.
   refresh controlla la transazione del comando e il refresh del canvas
   """
   if refresh == True:
      plugIn.beginEditCommand("Feature modified", layer)
      
   for f in features:
      if updateFeatureToLayer(plugIn, layer, f, False, check_validity) == False:
         if refresh == True:
            plugIn.destroyEditCommand()
            return False
         
   if refresh == True:
      plugIn.endEditCommand()
   
   return True


#===============================================================================
# deleteFeatureToLayer
#===============================================================================
def deleteFeatureToLayer(plugIn, layer, featureId, refresh = True):
   """
   Cancella la feature da un layer.
   refresh controlla la transazione del comando e il refresh del canvas
   """        
   if refresh == True:
      plugIn.beginEditCommand("Feature deleted", layer)

   if layer.deleteFeature(featureId):
      if refresh == True:
         plugIn.endEditCommand()
         
      result = True
   else:
      if refresh == True:
         plugIn.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# deleteFeaturesToLayer
#===============================================================================
def deleteFeaturesToLayer(plugIn, layer, featureIds, refresh = True):
   """
   Aggiorna le features ad un layer.
   refresh controlla la transazione del comando e il refresh del canvas
   """
   if refresh == True:
      plugIn.beginEditCommand("Feature deleted", layer)
      
   for featureId in featureIds:
      if deleteFeatureToLayer(plugIn, layer, featureId, False) == False:
         if refresh == True:
            plugIn.destroyEditCommand()
            return False
         
   if refresh == True:
      plugIn.endEditCommand()
   
   return True


#===============================================================================
# getLayersByName
#===============================================================================
def getLayersByName(regularExprName):
   """
   Ritorna la lista dei layer il cui nome soddisfa la regular expression di ricerca
   (per conversione da wildcards vedi la funzione wildCard2regularExpr)
   """
   #qad_debug.breakPoint()
   result = []
   regExprCompiled = re.compile(regularExprName)
   for layer in QgsMapLayerRegistry.instance().mapLayers().values():
      if re.match(regExprCompiled, layer.name()):
         if layer.isValid():
            result.append(layer)

   return result


#===============================================================================
# getLayerById
#===============================================================================
def getLayerById(id):
   """
   Ritorna il layer con id noto
   """
   for layer in QgsMapLayerRegistry.instance().mapLayers().values():
      if layer.id() == id:
         return layer
   return None


#===============================================================================
# get_symbolRotationFieldName
#===============================================================================
def get_symbolRotationFieldName(layer):
   """
   return rotation field name (or empty string if not set or not supported by renderer) 
   """
   #qad_debug.breakPoint()
   if (layer.type() != QgsMapLayer.VectorLayer) or (layer.geometryType() != QGis.Point):
      return ""
   
   return layer.rendererV2().rotationField()


#===============================================================================
# get_symbolScaleFieldName
#===============================================================================
def get_symbolScaleFieldName(layer):
   """
   return rotation field name (or empty string if not set or not supported by renderer) 
   """
   if (layer.type() != QgsMapLayer.VectorLayer) or (layer.geometryType() != QGis.Point):
      return ""
   
   return layer.rendererV2().sizeScaleField()


#===============================================================================
# isTextLayer
#===============================================================================
def isTextLayer(layer):
   """
   return True se il layer è di tipo testo 
   """
   #qad_debug.breakPoint()
   # deve essere un VectorLayer di tipo puntuale
   if (layer.type() != QgsMapLayer.VectorLayer) or (layer.geometryType() != QGis.Point):
      return False
   # deve avere il-i simbolo-i trasparenti almeno entro il 10% 
   for symbol in layer.rendererV2().symbols():
      if symbol.alpha() > 0.1: # Get alpha transparency 1 for opaque, 0 for invisible
         return False
   # deve avere etichette
   palyr = QgsPalLayerSettings()
   palyr.readFromLayer(layer)
   if palyr.enabled == False:
      return False
         
   return True


#===============================================================================
# isSymbolLayer
#===============================================================================
def isSymbolLayer(layer):
   """
   return True se il layer è di tipo simbolo 
   """   
   # deve essere un VectorLayer di tipo puntuale
   if (layer.type() != QgsMapLayer.VectorLayer) or (layer.geometryType() != QGis.Point):
      return False
   # se non è un layer di tipo testo è di tipo simbolo
   return False if isTextLayer(layer) else True 


#============================================================================
# INIZIO - Gestione layer temporanei di QAD
#============================================================================


#===============================================================================
# createQADTempLayer
#===============================================================================
def createQADTempLayer(plugIn, GeomType):
   """
   Aggiunge tre liste di geometrie rispettivamente a tre layer temporanei di QAD (uno per tipologia di
   geometria). Se le geometrie sono da convertire allora
   deve essere passato il parametro <coordTransform> di tipo QgsCoordinateTransform.
   <epsg> = the authority identifier for this srs    
   """
   layer = None
   epsg = plugIn.iface.mapCanvas().mapRenderer().destinationCrs().authid()
   
   if GeomType == QGis.Point:
      layerName = QadMsg.translate("QAD", "QAD - Punti temporanei")
      layerList = getLayersByName(qad_utils.wildCard2regularExpr(layerName))
      if len(layerList) == 0:
         layer = QgsVectorLayer("Point?crs=%s&index=yes" % epsg, layerName, "memory")
         QgsMapLayerRegistry().instance().addMapLayers([layer], True)
      else:
         layer = layerList[0]
   elif GeomType == QGis.Line:
      layerName = QadMsg.translate("QAD", "QAD - Linee temporanee") 
      layerList = getLayersByName(qad_utils.wildCard2regularExpr(layerName))
      if len(layerList) == 0:
         layer = QgsVectorLayer("LineString?crs=%s&index=yes" % epsg, layerName, "memory")
         QgsMapLayerRegistry().instance().addMapLayers([layer], True)
      else:
         layer = layerList[0]
   elif GeomType == QGis.Polygon:
      layerName = QadMsg.translate("QAD", "QAD - Poligoni temporanei") 
      layerList = getLayersByName(qad_utils.wildCard2regularExpr(layerName))
      if len(layerList) == 0:
         layer = QgsVectorLayer("Polygon?crs=%s&index=yes" % epsg, layerName, "memory")
         QgsMapLayerRegistry().instance().addMapLayers([layer], True)
      else:
         layer = layerList[0]

   layer.startEditing()
   return layer

   
#===============================================================================
# addGeometriesToQADTempLayers
#===============================================================================
def addGeometriesToQADTempLayers(plugIn, pointGeoms = None, lineGeoms = None, polygonGeoms = None, \
                               crs = None, refresh = True):
   """
   Aggiunge tre liste di geometrie rispettivamente a tre layer temporanei di QAD (uno per tipologia di
   geometria). Se le geometrie sono da convertire allora
   deve essere passato il parametro <csr> che definisce il sistema di coordinate delle geometrie.
   """   
   if pointGeoms is not None and len(pointGeoms) > 0:
      layer = createQADTempLayer(plugIn, QGis.Point)
      if layer is None:
         return False
      if crs is None:
         # plugIn, layer, geoms, coordTransform , refresh, check_validity
         if addGeomsToLayer(plugIn, layer, pointGeoms, None, refresh, False) == False:
            return False
      else:
         # plugIn, layer, geoms, coordTransform , refresh, check_validity
         if addGeomsToLayer(plugIn, layer, pointGeoms, QgsCoordinateTransform(crs, layer.crs()), \
                            refresh, False) == False:
            return False
      
   if lineGeoms is not None and len(lineGeoms) > 0:
      layer = createQADTempLayer(plugIn, QGis.Line)
      if layer is None:
         return False
      if crs is None:
         # plugIn, layer, geoms, coordTransform , refresh, check_validity
         if addGeomsToLayer(plugIn, layer, lineGeoms, None, refresh, False) == False:
            return False
      else:
         # plugIn, layer, geoms, coordTransform , refresh, check_validity
         if addGeomsToLayer(plugIn, layer, lineGeoms, QgsCoordinateTransform(crs, layer.crs()), \
                            refresh, False) == False:
            return False
      
   if polygonGeoms is not None and len(polygonGeoms) > 0:
      layer = createQADTempLayer(plugIn, QGis.Polygon)
      if layer is None:
         return False
      if crs is None:
         # plugIn, layer, geoms, coordTransform , refresh, check_validity
         if addGeomsToLayer(plugIn, layer, polygonGeoms, None, refresh, False) == False:
            return False
      else:
         # plugIn, layer, geoms, coordTransform , refresh, check_validity
         if addGeomsToLayer(plugIn, layer, polygonGeoms, QgsCoordinateTransform(crs, layer.crs()), \
                            refresh, False) == False:
            return False
        
   return True
      
          