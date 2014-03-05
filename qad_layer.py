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
      return None
   
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
   provider = layer.dataProvider()
   fields = layer.pendingFields()
   f.setFields(fields)

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
   provider = layer.dataProvider()
   fields = layer.pendingFields()
   f.setFields(fields)

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
   provider = layer.dataProvider()
   fields = layer.pendingFields()
   f.setFields(fields)

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
   provider = layer.dataProvider()
   fields = layer.pendingFields()
   f.setFields(fields)

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
   layermap = QgsMapLayerRegistry.instance().mapLayers()
   for name, layer in layermap.iteritems():
      if re.match(regExprCompiled, layer.name()):
         if layer.isValid():
            result.append(layer)

   return result


#===============================================================================
# get_symbolRotationFieldName
#===============================================================================
def get_symbolRotationFieldName(layer):
   """
   return rotation field name (or empty string if not set or not supported by renderer) 
   """
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
# get_tokenListFromLblFieldName ausilio di getTokenListFromLblFieldName
#===============================================================================
def getToken(expr, start, endChar = None):
   """
   ritorna una parola dentro la stringa expr che inizia nella posizione start e che termina con il carattere
   endChar. Se endChar <> None allora due endChar consecutivi valgono uno es. 'a''a' = a'a 
   """
   token = ""
   tot = len(expr)
   i = start
   if endChar is None:
      separators = "()+-*/%^=><|, \"'"
      while i < tot:
         ch = expr[i]      
         if separators.find(ch) >= 0:
            return token, i
         token = token + ch
         i = i + 1
   else:
      #qad_debug.breakPoint()
      
      while i < tot:
         ch = expr[i]      
         if ch != endChar:
            token = token + ch
         elif i + 1 < tot: # se c'è un carattere successivo
            if expr[i + 1] == endChar: # se il carattere successivo = endChar
               token = token + ch
               i = i + 1
            else:
               return token, i
         i = i + 1
   
   return token, i
            

#===============================================================================
# getTokenListFromLblFieldName ausilio di get_labelFieldNames
#===============================================================================
def getTokenListFromLblFieldName(expr):
   """
   ritorna una lista di token escluse le stringhe,  dall'espressione passata come parametro 
   """
   result = []
   i = 0
   tot = len(expr)
   while i < tot:
      ch = expr[i]
      if ch == "\"": # se inizia un nome di campo
         token, i = getToken(expr, i + 1, "\"")
         if len(token) > 0:
            result.append(token)
      elif ch == "'": # se inizia una stringa
         token, i = getToken(expr, i + 1, "'")
      else:
         token, i = getToken(expr, i)
         if len(token) > 0:
            result.append(token)
         
      i = i + 1
   
   return result


#===============================================================================
# get_scaleFieldName
#===============================================================================
def get_labelFieldNames(layer):
   """
   return rotation field name (or empty string if not set or not supported by renderer) 
   """
   result = []
      
   if layer.type() == QgsMapLayer.VectorLayer:
      palyr = QgsPalLayerSettings()
      palyr.readFromLayer(layer)
      if palyr.enabled:
         lblFieldName = palyr.fieldName
         if palyr.isExpression: # Is this label made from a expression string eg FieldName || 'mm'.   
            # estraggo i token
            tokenList = getTokenListFromLblFieldName(lblFieldName)
                     
            fields = layer.label().fields()
            for field in fields:
               if field.name() in tokenList:
                  if field.name() not in result: # evito duplicati
                     result.append(field.name())
         else:
            result.append(lblFieldName)         
               
   return result


#===============================================================================
# get_labelRotationFieldName
#===============================================================================
def get_labelRotationFieldName(layer):
   """
   return rotation field name for label (or empty string if not set or not supported by renderer) 
   """
   if layer.type() != QgsMapLayer.VectorLayer:
      return ""
   palyr = QgsPalLayerSettings()
   palyr.readFromLayer(layer)
   dataDefined = palyr.dataDefinedProperty(QgsPalLayerSettings.Rotation)
   if dataDefined.isActive():    
      return dataDefined.field()   
   return ""


#===============================================================================
# get_labelSizeFieldName
#===============================================================================
def get_labelSizeFieldName(layer):
   """
   return size field name for label (or empty string if not set or not supported by renderer) 
   """
   if layer.type() != QgsMapLayer.VectorLayer:
      return ""
   palyr = QgsPalLayerSettings()
   palyr.readFromLayer(layer)
   dataDefined = palyr.dataDefinedProperty(QgsPalLayerSettings.Size)
   if dataDefined.isActive():    
      return dataDefined.field()   
   return ""



#===============================================================================
# isTextLayer
#===============================================================================
def isTextLayer(layer):
   """
   return True se il layer è di tipo testo 
   """   
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


#===============================================================================
# QadUndoRecordTypeEnum class.
#===============================================================================
class QadUndoRecordTypeEnum():
   NONE     = 0     # nessuno
   COMMAND  = 1     # singolo comando
   BEGIN    = 2     # inizio di un gruppo di comandi
   END      = 3     # fine di un gruppo di comandi
   BOOKMARK = 4     # flag di segnalibro, significa che si tratta di un segno a cui
                     # si può ritornare


#===============================================================================
# QadUndoRecord classe x gestire un registrazione di UNDO
#===============================================================================
class QadUndoRecord():


   def __init__(self):
      self.text = "" # descrizione operazione
      self.undoType = QadUndoRecordTypeEnum.NONE # tipo di undo (vedi QadUndoRecordTypeEnum)
      self.layerList = None # lista di layer coinvolti nel comando di editazione

      
   def setUndoType(self, text = "", undoType = QadUndoRecordTypeEnum.NONE):
      # si sta impostando una tipologia di marcatore di undo
      self.text = text
      self.layerList = None # lista di layer coinvolti nel comando di editazione
      self.undoType = undoType


   def layerAt(self, layerId):
      # ritorna la posizione nella lista 0-based), -1 se non trovato
      if self.layerList is not None and self.undoType == QadUndoRecordTypeEnum.COMMAND:
         for j in xrange(0, len(self.layerList), 1):
            if self.layerList[j].id() == layerId:
               return j
      return -1


   def clearByLayer(self, layerId):
      # elimino dalla lista il layer <layerId>
      pos = self.layerAt(layerId)
      if pos >= 0:
         del self.layerList[pos]


   def beginEditCommand(self, text, layerList):
      # si sta iniziando un comando che coinvolge una lista di layer
      self.text = text # descrizione operazione     
      self.undoType = QadUndoRecordTypeEnum.COMMAND
      # <parameter> contiene la lista dei layer coinvolti nel comando di editazione
      self.layerList = []
      for layer in layerList: # copio la lista
         if self.layerAt(layer.id()) == -1: # non ammetto duplicazioni di layer
            layer.beginEditCommand(text)
            self.layerList.append(layer)
               
               
   def destroyEditCommand(self):
      # si sta distruggendo un comando che coinvolge una lista di layer
      if self.layerList is not None and self.undoType == QadUndoRecordTypeEnum.COMMAND:
         for layer in self.layerList:
            layer.destroyEditCommand()
         return True
      else:
         return False


   def endEditCommand(self, canvas):
      # si sta concludendo un comando che coinvolge una lista di layer
      if self.layerList is not None and self.undoType == QadUndoRecordTypeEnum.COMMAND:
         for layer in self.layerList:
            layer.endEditCommand()
            #layer.updateExtents() # non serve
         canvas.refresh()
  
      
   def undoEditCommand(self, canvas = None):
      # si sta facendo un UNDO di un comando che coinvolge una lista di layer
      if self.layerList is not None and self.undoType == QadUndoRecordTypeEnum.COMMAND:
         for layer in self.layerList:
            layer.undoStack().undo()
         if canvas is not None:
            canvas.refresh()
 
      
   def redoEditCommand(self, canvas = None):
      # si sta facendo un REDO di un comando che coinvolge una lista di layer
      if self.layerList is not None and self.undoType == QadUndoRecordTypeEnum.COMMAND:
         for layer in self.layerList:
            layer.undoStack().redo()
         if canvas is not None:
            canvas.refresh()

     
   def addLayer(self, layer):
      # si sta aggiungendo un layer al comando corrente
      if self.undoType != QadUndoRecordTypeEnum.COMMAND: # si deve trattare di un comando
         return False
      if self.layerAt(layer.id()) == -1: # non ammetto duplicazioni di layer
         layer.beginEditCommand(self.text)
         self.layerList.append(layer)


#===============================================================================
# QadUndoStack classe x gestire lo stack delle operazioni
#===============================================================================
class QadUndoStack():

    
   def __init__(self):
      self.UndoRecordList = [] # lista di record di undo
      self.index = -1
 
   
   def clear(self):
      del self.UndoRecordList[:] # svuoto la lista
      self.index = -1


   def clearByLayer(self, layerId):
      # elimino il layer <layerId> dalla lista dei record di undo
      for i in xrange(len(self.UndoRecordList) - 1, -1, -1):
         UndoRecord = self.UndoRecordList[i]
         if UndoRecord.undoType == QadUndoRecordTypeEnum.COMMAND:
            UndoRecord.clearByLayer(layerId)      
            if len(UndoRecord.layerList) == 0:
               # elimino la lista dei layer (vuota) coinvolta nel comando di editazione
               del self.UndoRecordList[i]
               if self.index >= i: # aggiorno il puntatore
                  self.index = self.index - 1


   def insertBeginGroup(self, text):
      UndoRecord = QadUndoRecord()
      UndoRecord.setUndoType(text, QadUndoRecordTypeEnum.BEGIN)
      self.UndoRecordList.append(UndoRecord)
      self.index = len(self.UndoRecordList) - 1
      return True


   def getOpenGroupPos(self, endGroupPos):
      # dalla posizione di fine gruppo <endgroupPos> cerca la posizione di inizio gruppo
      # -1 se non trovato
      openFlag = 0
      for i in xrange(endGroupPos, -1, -1):
         UndoRecord = self.UndoRecordList[i]
         if UndoRecord.undoType == QadUndoRecordTypeEnum.BEGIN:
            openFlag = openFlag + 1
            if openFlag >= 0:
               return i
         elif UndoRecord.undoType == QadUndoRecordTypeEnum.END:
            openFlag = openFlag - 1
      return -1


   def getEndGroupPos(self, beginGroupPos):
      # dalla posizione di inizio gruppo <endgroupPos> cerca la posizione di inizio gruppo
      # -1 se non trovato
      closeFlag = 0
      for i in xrange(beginGroupPos, len(self.UndoRecordList), 1):
         UndoRecord = self.UndoRecordList[i]
         if UndoRecord.undoType == QadUndoRecordTypeEnum.BEGIN:
            closeFlag = closeFlag - 1
         elif UndoRecord.undoType == QadUndoRecordTypeEnum.END:
            closeFlag = closeFlag + 1
            if closeFlag >= 0:
               return i
      return -1
   

   def insertEndGroup(self):
      # non si può inserire un end gruppo se non si è rimasto aperto un gruppo
      openGroupPos = self.getOpenGroupPos(len(self.UndoRecordList) - 1)
      if openGroupPos == -1:
         return False

      UndoRecord = QadUndoRecord()
      UndoRecord.setUndoType(self.UndoRecordList[openGroupPos].text, QadUndoRecordTypeEnum.END)
      self.UndoRecordList.append(UndoRecord)
      self.index = len(self.UndoRecordList) - 1
      return True

      
   def beginEditCommand(self, text, layerList):
      #qad_debug.breakPoint()
      tot = len(self.UndoRecordList)
      if tot > 0 and self.index < tot - 1:
         del self.UndoRecordList[self.index + 1 :] # cancello fino alla fine
         
      UndoRecord = QadUndoRecord()
      UndoRecord.beginEditCommand(text, layerList)
      self.UndoRecordList.append(UndoRecord)
      self.index = len(self.UndoRecordList) - 1

      
   def destroyEditCommand(self):
      if len(self.UndoRecordList) > 0:
         UndoRecord = self.UndoRecordList[-1]
         if UndoRecord.destroyEditCommand():
            del self.UndoRecordList[-1]
            #qad_debug.breakPoint()
            self.index = self.index - 1


   def endEditCommand(self, canvas):
      #qad_debug.breakPoint()
      if len(self.UndoRecordList) > 0:
         UndoRecord = self.UndoRecordList[-1]
         UndoRecord.endEditCommand(canvas)


   def moveOnFirstUndoRecord(self):
      # sposta il cursore dalla posizione attuale fino l'inizio
      # e si ferma quando trova un record di tipo END o COMMAND
      while self.index >= 0:
         UndoRecord = self.UndoRecordList[self.index]
         if UndoRecord.undoType == QadUndoRecordTypeEnum.END or \
            UndoRecord.undoType == QadUndoRecordTypeEnum.COMMAND:
            return True
         self.index = self.index - 1
      return False 
         
   def undoEditCommand(self, canvas = None, nTimes = 1):
      #qad_debug.breakPoint()
      for i in xrange(0, nTimes, 1):
         # cerco il primo record in cui ha senso fare UNDO
         if self.moveOnFirstUndoRecord() == False:
            break
         UndoRecord = self.UndoRecordList[self.index]
         # se incontro un end-group devo andare fino al begin-group
         if UndoRecord.undoType == QadUndoRecordTypeEnum.END:
            openGroupPos = self.getOpenGroupPos(self.index)           
            while self.index >= openGroupPos:
               UndoRecord.undoEditCommand(None) # senza fare refresh
               self.index = self.index - 1
               if self.moveOnFirstUndoRecord() == False:
                  break
               UndoRecord = self.UndoRecordList[self.index]
         else:
            UndoRecord.undoEditCommand(None)
            #qad_debug.breakPoint()
            self.index = self.index - 1
      
      if canvas is not None:   
         canvas.refresh()


   def moveOnFirstRedoRecord(self):
      # sposta il cursore dalla posizione attuale fino alla fine
      # e si ferma quando trova un record di tipo BEGIN o COMMAND
      tot = len(self.UndoRecordList) - 1 
      while self.index < tot:
         self.index = self.index + 1                  
         UndoRecord = self.UndoRecordList[self.index]
         if UndoRecord.undoType == QadUndoRecordTypeEnum.BEGIN or \
            UndoRecord.undoType == QadUndoRecordTypeEnum.COMMAND:
            return True
      return False     
      
   def redoEditCommand(self, canvas = None, nTimes = 1):
      #qad_debug.breakPoint()
      for i in xrange(0, nTimes, 1):         
         # cerco il primo record in cui ha senso fare REDO
         if self.moveOnFirstRedoRecord() == False:
            break
         UndoRecord = self.UndoRecordList[self.index]
         # se incontro un begin-group devo andare fino al end-group
         if UndoRecord.undoType == QadUndoRecordTypeEnum.BEGIN:
            endGroupPos = self.getEndGroupPos(self.index)           
            while self.index <= endGroupPos:
               UndoRecord.redoEditCommand(None) # senza refresh
               if self.moveOnFirstRedoRecord() == False:
                  break
               UndoRecord = self.UndoRecordList[self.index]
         else:            
            UndoRecord.redoEditCommand(None)

      if canvas is not None:   
         canvas.refresh()

     
   def addLayerToLastEditCommand(self, text, layer):
      if len(self.UndoRecordList) > 0:     
         self.UndoRecordList[-1].addLayer(layer)


   def isUndoAble(self):
      # cerca un record di tipo COMMAND dalla posizione attuale fino l'inizio
      i = self.index
      while i >= 0:
         UndoRecord = self.UndoRecordList[i]
         if UndoRecord.undoType == QadUndoRecordTypeEnum.COMMAND:
            return True
         i = i - 1
      return False


   def isRedoAble(self):
      # cerca un record di tipo COMMAND dalla posizione attuale fino alla fine
      i = self.index + 1
      tot = len(self.UndoRecordList)
      while i < tot:
         UndoRecord = self.UndoRecordList[i]
         if UndoRecord.undoType == QadUndoRecordTypeEnum.COMMAND:
            return True
         i = i + 1
      return False

   #===============================================================================
   # BOOKMARK - INIZIO
   #===============================================================================
   
   def undoUntilBookmark(self, canvas):
      #qad_debug.breakPoint()
      if self.index == -1:
         return
      for i in xrange(self.index, -1, -1):
         UndoRecord = self.UndoRecordList[i]
         if UndoRecord.undoType == QadUndoRecordTypeEnum.BOOKMARK:
            break
         
         UndoRecord.undoEditCommand(None) # senza refresh         
      self.index = i - 1        
      
      canvas.refresh()


   def redoUntilBookmark(self, canvas):
      #qad_debug.breakPoint()
      for i in xrange(self.index + 1, len(self.UndoRecordList), 1):
         UndoRecord = self.UndoRecordList[i]
         if UndoRecord.undoType == QadUndoRecordTypeEnum.BOOKMARK:
            break
         UndoRecord.redoEditCommand(None) # senza refresh         
      self.index = i         
      
      canvas.refresh()


   def getPrevBookmarkPos(self, pos):
      # dalla posizione <pos> cerca la posizione di bookmark precedente
      # -1 se non trovato
      for i in xrange(pos - 1, -1, -1):
         UndoRecord = self.UndoRecordList[i]
         if UndoRecord.undoType == QadUndoRecordTypeEnum.BOOKMARK:
            return i
      return -1
 
      
   def insertBookmark(self, text):
      #qad_debug.breakPoint()
      # non si può inserire un bookmark all'interno di un gruppo begin-end
      if self.getOpenGroupPos(self.index) >= 0:
         return False  
      
      tot = len(self.UndoRecordList)
      if tot > 0 and self.index < tot - 1:
         del self.UndoRecordList[self.index + 1 :] # cancello fino alla fine
      
      UndoRecord = QadUndoRecord()
      UndoRecord.setUndoType(text, QadUndoRecordTypeEnum.BOOKMARK)
      self.UndoRecordList.append(UndoRecord)
      self.index = len(self.UndoRecordList) - 1
      return True

   #===============================================================================
   # BOOKMARK - FINE
   #===============================================================================       