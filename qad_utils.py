# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 funzioni varie di utilità
 
                              -------------------
        begin                : 2013-05-22
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
import math
import sys
import string


import qad_debug
from qad_variables import *
from qad_snapper import *
from qad_msg import QadMsg
from qad_circle import *
from qad_arc import *
from qad_entity import *


# Modulo che gestisce varie funzionalità di Qad


#===============================================================================
# str2float
#===============================================================================
def str2float(s):
   """
   Ritorna la conversione di una stringa in numero reale
   """  
   try:
      n = float(s)
      return n
   except ValueError:
      return None


#===============================================================================
# str2long
#===============================================================================
def str2long(s):
   """
   Ritorna la conversione di una stringa in numero lungo
   """  
   try:
      n = long(s)
      return n
   except ValueError:
      return None


#===============================================================================
# str2int
#===============================================================================
def str2int(s):
   """
   Ritorna la conversione di una stringa in numero intero
   """  
   try:
      n = int(s)
      return n
   except ValueError:
      return None


#===============================================================================
# str2bool
#===============================================================================
def str2bool(s):
   """
   Ritorna la conversione di una stringa in bool
   """  
   try:
      upperS = s.upper()
      # 16 = "N", 17 = "NO"
      # "F" "FALSO" 
      if upperS == "0" or upperS == "N" or upperS == "NO" or \
         upperS == "F" or upperS == "FALSE" or \
         upperS == QadMsg.get(16)[0] or upperS == QadMsg.get(16) or \
         upperS == QadMsg.get(17)[0] or upperS == QadMsg.get(17): 
         return False
      else:
         return True
   except ValueError:
      return None


#===============================================================================
# str2QgsPoint
#===============================================================================
def str2QgsPoint(s, lastPoint = None, currenPoint = None, oneNumberAllowed = True):
   """
   Ritorna la conversione di una stringa in punto QgsPoint
   se <oneNumberAllowed> = False significa che s non può essere un solo numero
   che rappresenterebbe la distanza dall'ultimo punto con angolo in base al punto corrente
   (questo viene vietato quando si vuole accettare un numero o un punto)
   lastPoint viene usato solo per le espressioni tipo @10<45 (dall'ultimo punto, lunghezza 10, angolo 45 gradi)
   o @ (dall'ultimo punto)
   o @10,20 (dall'ultimo punto, + 10 per la X e + 20 per la Y)
   o 100 (dall'ultimo punto, distanza 100, angolo in base al punto corrente)
   """   
   expression = s.strip() # senza spazi iniziali e finali
   if len(expression) == 0:
      return None

   if expression[0] == "@": # coordinate relative a lastpoint
      if lastPoint is None:
         return None
      
      if len(expression) == 1:
         return lastPoint
      
      expression = expression[1:] # scarto il primo carattere "@"
      coords = expression.split(",")
      if len(coords) == 2:
         OffSetX = str2float(coords[0].strip())
         OffSetY = str2float(coords[1].strip())
         if (OffSetX is None) or (OffSetY is None):
            return None
         return QgsPoint(lastPoint.x() + OffSetX, lastPoint.y() + OffSetY)
      else:
         if len(coords) != 1:
            return None
         # verifico se si sta usando la coordinata polare
         expression = coords[0].strip()
         values = expression.split("<")
         if len(values) != 2: 
            return None
         dist = str2float(values[0].strip())
         angle = str2float(values[1].strip())
         if (dist is None) or (angle is None):
            return None     
         coords = getPolarPointByPtAngle(lastPoint, math.radians(angle), dist)     
         return QgsPoint(coords[0], coords[1])
   else:
      coords = expression.split(",")
      if len(coords) == 2:  # coordinate assolute
         x = str2float(coords[0].strip())
         y = str2float(coords[1].strip())
         if (x is None) or (y is None):
            return None
         return QgsPoint(x, y)
      else:
         if oneNumberAllowed == False: # vietato che la stringa sia un solo numero
            return None
         
         dist = str2float(expression)

         if (dist is None) or (lastPoint is None) or (currenPoint is None):
            return None
         
         angle = qad_utils.getAngleBy2Pts(lastPoint, currenPoint)
         coords = getPolarPointByPtAngle(lastPoint, angle, dist)     
         return QgsPoint(coords[0], coords[1])


#===============================================================================
# str2snapTypeEnum
#===============================================================================
def str2snapTypeEnum(s):
   """
   Ritorna la conversione di una stringa in una combinazione di tipi di snap
   """
   snapType = QadSnapTypeEnum.NONE
   snapTypeStrList = s.strip().split(",")
   for snapTypeStr in snapTypeStrList:
      snapTypeStr = snapTypeStr.strip().upper()
      if snapTypeStr == QadMsg.get(19): # "FIN" punto finale  
         snapType = snapType | QadSnapTypeEnum.END
      elif snapTypeStr == QadMsg.get(20): # "MED" punto medio  
         snapType = snapType | QadSnapTypeEnum.MID
      elif snapTypeStr == QadMsg.get(21): # "CEN" centro (centroide)  
         snapType = snapType | QadSnapTypeEnum.CEN
      elif snapTypeStr == QadMsg.get(22): # "NOD" oggetto punto 
         snapType = snapType | QadSnapTypeEnum.NOD
      elif snapTypeStr == QadMsg.get(23): # "QUA" punto quadrante
         snapType = snapType | QadSnapTypeEnum.QUA
      elif snapTypeStr == QadMsg.get(24): # "INT" intersezione
         snapType = snapType | QadSnapTypeEnum.INT
      elif snapTypeStr == QadMsg.get(25): # "INS" punto di inserimento 
         snapType = snapType | QadSnapTypeEnum.INS
      elif snapTypeStr == QadMsg.get(26): # "PER" punto perpendicolare
         snapType = snapType | QadSnapTypeEnum.PER
      elif snapTypeStr == QadMsg.get(27): # "TAN" tangente
         snapType = snapType | QadSnapTypeEnum.TAN
      elif snapTypeStr == QadMsg.get(28): # "VIC" punto più vicino
         snapType = snapType | QadSnapTypeEnum.NEA
      elif snapTypeStr == QadMsg.get(29): # "APP" intersezione apparente
         snapType = snapType | QadSnapTypeEnum.APP
      elif snapTypeStr == QadMsg.get(30): # "EST" Estensione
         snapType = snapType | QadSnapTypeEnum.EXT
      elif snapTypeStr == QadMsg.get(31): # "PAR" Parallelo
         snapType = snapType | QadSnapTypeEnum.PAR         
      elif string.find(snapTypeStr, QadMsg.get(32)) == 0: # se inizia per "PR" distanza progressiva         
         snapType = snapType | QadSnapTypeEnum.PR
      elif snapTypeStr == QadMsg.get(75): # "EST_INT" intersezione su estensione
         snapType = snapType | QadSnapTypeEnum.EXT_INT

   return snapType


#===============================================================================
# str2snapParam
#===============================================================================
def str2snapParams(s):
   """
   Ritorna la conversione di una stringa in una lista di parametri per i tipi di snap
   """
   params = []
   snapTypeStrList = s.strip().split(",")
   for snapTypeStr in snapTypeStrList:
      snapTypeStr = snapTypeStr.strip().upper()
      if string.find(snapTypeStr, QadMsg.get(32)) == 0: # se inizia per "PR" distanza progressiva
         param = str2float(snapTypeStr[len(QadMsg.get(32)):]) # fino alla fine della stringa
         if param is not None:
            params.append([QadSnapTypeEnum.PR, param])         

   return params


#===============================================================================
# strip
#===============================================================================
def strip(s, stripList):
   """
   Rimuove tutte le stringhe in lista che sono all'inizio e alla fine della stringa
   """
   ok = False
   #qad_debug.breakPoint()
   while ok == False:
      ok = True      
      for item in stripList:
         itemLen = len(item)
         
         pos = s.find(item)
         if pos == 0:
            s = s.lstrip(item) # rimuovo prima
            ok = False
            
         pos = s.rfind(item)  
         if pos >= 0 and pos == len(s) - itemLen:
            s = s.rstrip(item) # rimuovo dopo
            ok = False
   return s

#===============================================================================
# toRadians
#===============================================================================
def toRadians(angle):
   """
   Converte da gradi a radianti
   """
   return math.radians(angle)


#===============================================================================
# toRadians
#===============================================================================
def toDegrees(angle):
   """
   Converte da radianti a gradi 
   """
   return math.degrees(angle)


#===============================================================================
# normalizeAngle
#===============================================================================
def normalizeAngle(angle, norm = math.pi * 2):
   """
   Normalizza un angolo a da [0 - 2pi] o da [0 - pi].
   Così, ad esempio, se un angolo è più grande di 2pi viene ridotto all'angolo giusto 
   (il raffronto in gradi sarebbe da 380 a 20 gradi) o se è negativo diventa positivo
   (il raffronto in gradi sarebbe da -90 a 270 gradi)  
   """
   if angle >= 0:
      return angle % norm
   else:
      return norm - ((-angle) % norm)


#===============================================================================
# distMapToLayerCoordinates
#===============================================================================
def distMapToLayerCoordinates(dist, canvas, layer):
   # trovo il punto centrale dello schermo  
   boundBox = canvas.extent()
   x = (boundBox.xMinimum() + boundBox.xMaximum()) / 2
   y = (boundBox.yMinimum() + boundBox.yMaximum()) / 2
   pt1 = QgsPoint(x, y)
   pt2 = QgsPoint(x + dist, y)
   transformedPt1 = canvas.mapRenderer().mapToLayerCoordinates(layer, pt1)
   transformedPt2 = canvas.mapRenderer().mapToLayerCoordinates(layer, pt2)
   return getDistance(transformedPt1, transformedPt2)

 
#===============================================================================
# getCurrLayerEditable
#===============================================================================
def getCurrLayerEditable(canvas, geomType = None):
   """
   Ritorna il layer corrente se è aggiornabile e compatibile con il tipo geomType
   """
   vLayer = canvas.currentLayer()
   if vLayer is None:
      return None
   
   if (vLayer.type() != vLayer.VectorLayer):
      return None

   if geomType is not None:
      if vLayer.geometryType() != geomType:
         return None

   provider = vLayer.dataProvider()
   if not (provider.capabilities() & QgsVectorDataProvider.EditingCapabilities):
      return None

   if not vLayer.isEditable():
      return None

   return vLayer
  

#===============================================================================
# addPointToLayer
#===============================================================================
def addPointToLayer(plugIn, layer, point, transform = True, refresh = True):
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

   if not g.isGeosValid():
      return False
      
   f.setGeometry(g)
   
   # Add attributefields to feature.
   provider = layer.dataProvider()
   fields = layer.pendingFields()
   for field in fields:
      f.addAttribute(field, provider.defaultValue(field))

   layer.beginEditCommand("Feature added")

   if layer.addFeature(f):
      layer.endEditCommand()
      plugIn.setLastEntity(layer, f.id())
      if refresh == True:
         plugIn.canvas.refresh()
      result = True
   else:
      layer.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# addLineToLayer
#===============================================================================
def addLineToLayer(plugIn, layer, points, transform = True, refresh = True):
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

   if not g.isGeosValid():
      return False
      
   f.setGeometry(g)
   
   # Add attributefields to feature.
   provider = layer.dataProvider()
   fields = layer.pendingFields()
   for field in fields:
      f.addAttribute(field, provider.defaultValue(field))

   layer.beginEditCommand("Feature added")

   if layer.addFeature(f):
      layer.endEditCommand()
      plugIn.setLastEntity(layer, f.id())
      if refresh == True:
         plugIn.canvas.refresh()
      result = True
   else:
      layer.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# addPolygonToLayer
#===============================================================================
def addPolygonToLayer(plugIn, layer, points, transform = True, refresh = True):
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

   if not g.isGeosValid():
      return False
         
   f.setGeometry(g)
   
   # Add attributefields to feature.
   provider = layer.dataProvider()
   fields = layer.pendingFields()
   for field in fields:
      f.addAttribute(field, provider.defaultValue(field))

   layer.beginEditCommand("Feature added")

   if layer.addFeature(f):
      layer.endEditCommand()
      plugIn.setLastEntity(layer, f.id())
      if refresh == True:
         plugIn.canvas.refresh()
      result = True
   else:
      layer.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# addGeomToLayer
#===============================================================================
def addGeomToLayer(plugIn, layer, geom, coordTransform = None, refresh = True):
   """
   Aggiunge una geometria ad un layer. Se la geometria è da convertire allora
   deve essere passato il parametro <coordTransform> di tipo QgsCoordinateTransform.
   refresh controlla la transazione del comando e il refresh del canvas
   """     
   f = QgsFeature()
   
   g = QgsGeometry(geom)
   if coordTransform is not None:
      g.transform(coordTransform)            

   if not g.isGeosValid():
      return False
      
   f.setGeometry(g)
   
   # Add attributefields to feature.
   provider = layer.dataProvider()
   fields = layer.pendingFields()
   for field in fields:
      f.addAttribute(field, provider.defaultValue(field))

   if refresh == True:
      layer.beginEditCommand("Feature added")

   if layer.addFeature(f):
      if refresh == True:
         layer.endEditCommand()
         plugIn.canvas.refresh()
      plugIn.setLastEntity(layer, f.id())
      result = True
   else:
      if refresh == True:
         layer.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# addGeomsToLayer
#===============================================================================
def addGeomsToLayer(plugIn, layer, geoms, coordTransform = None, refresh = True):
   """
   Aggiunge le geometrie ad un layer. Se la geometria è da convertire allora
   deve essere passato il parametro <coordTransform> di tipo QgsCoordinateTransform.
   refresh controlla la transazione del comando e il refresh del canvas
   """
   if refresh == True:
      layer.beginEditCommand("Feature added")
      
   for geom in geoms:
      if addGeomToLayer(plugIn, layer, geom, coordTransform, False) == False:
         if refresh == True:
            layer.destroyEditCommand()
            return False
         
   if refresh == True:
      layer.endEditCommand()
      plugIn.canvas.refresh()
   
   return True


#===============================================================================
# addFeatureToLayer
#===============================================================================
def addFeatureToLayer(plugIn, layer, f, coordTransform = None, refresh = True):
   """
   Aggiunge una feature ad un layer. Se la geometria è da convertire allora
   deve essere passato il parametro <coordTransform> di tipo QgsCoordinateTransform.
   <refresh> controlla la transazione del comando e il refresh del canvas
   """     
   
   if coordTransform is not None:
      g = QgsGeometry(f.geometry())
      g.transform(coordTransform)            
      f.setGeometry(g)

   if not f.geometry().isGeosValid():
      return False
         
   if refresh == True:
      layer.beginEditCommand("Feature added")

   if layer.addFeature(f):
      if refresh == True:
         layer.endEditCommand()
         plugIn.canvas.refresh()
      plugIn.setLastEntity(layer, f.id())
      result = True
   else:
      if refresh == True:
         layer.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# addFeaturesToLayer
#===============================================================================
def addFeaturesToLayer(plugIn, layer, features, coordTransform = None, refresh = True):
   """
   Aggiunge le feature ad un layer. Se la geometria è da convertire allora
   deve essere passato il parametro <coordTransform> di tipo QgsCoordinateTransform.
   <refresh> controlla la transazione del comando e il refresh del canvas
   """
   if refresh == True:
      layer.beginEditCommand("Feature added")
      
   for f in features:
      if addFeatureToLayer(plugIn, layer, f, coordTransform, False) == False:
         if refresh == True:
            layer.destroyEditCommand()
            return False
         
   if refresh == True:
      layer.endEditCommand()
      plugIn.canvas.refresh()
   
   return True


#===============================================================================
# updateFeatureToLayer
#===============================================================================
def updateFeatureToLayer(plugIn, layer, f, refresh = True):
   """
   Aggiorna la feature ad un layer.
   refresh controlla la transazione del comando e il refresh del canvas
   """        
   if not f.geometry().isGeosValid():
      return False
      
   if refresh == True:
      layer.beginEditCommand("Feature added")

   if layer.updateFeature(f):
      if refresh == True:
         layer.endEditCommand()
         plugIn.canvas.refresh()
      result = True
   else:
      if refresh == True:
         layer.destroyEditCommand()
      result = False
      
   return result


#===============================================================================
# updateFeaturesToLayer
#===============================================================================
def updateFeaturesToLayer(plugIn, layer, features, refresh = True):
   """
   Aggiorna le features ad un layer.
   refresh controlla la transazione del comando e il refresh del canvas
   """
   if refresh == True:
      layer.beginEditCommand("Feature modified")
      
   for f in features:
      if updateFeatureToLayer(plugIn, layer, f, False) == False:
         if refresh == True:
            layer.destroyEditCommand()
            return False
         
   if refresh == True:
      layer.endEditCommand()
      plugIn.canvas.refresh()
   
   return True
         

#===============================================================================
# getEntSelCursor
#===============================================================================
def getEntSelCursor():
   """
   Ritorna l'immagine del cursore per la selezione di un'entità 
   """
   
   size = 1 + QadVariables.get("PICKBOX") * 2
   # <width/cols> <height/rows> <colors> <char on pixel>
   row = str(size) + " " + str(size) + " 2 1"
   xpm = [row]
   # <Colors> 
   xpm.append("  c None")
   xpm.append("+ c " + QadVariables.get("PICKBOXCOLOR"))
   # <Pixels>
   # es . "+++++",
   # es . "+   +",
   # es . "+   +",
   # es . "+   +",
   # es . "+++++",
   xpm.append("+" * size)
   if size > 1:
      row = "+" + " " * (size - 2) + "+"
      for i in range(size - 2): # da 0
         xpm.append(row)
      xpm.append("+" * size)
      
   return QCursor(QPixmap(xpm))


def getGetPointCursor():
   """
   Ritorna l'immagine del cursore per la selezione di un punto 
   """
   
   pickBox = QadVariables.get("CURSORSIZE")
   size = 1 + pickBox * 2
   # <width/cols> <height/rows> <colors> <char on pixel>
   row = str(size) + " " + str(size) + " 2 1"
   xpm = [row]
   # <Colors> 
   xpm.append("  c None")
   xpm.append("+ c " + QadVariables.get("PICKBOXCOLOR"))
   # <Pixels>
   # es . "  +  ",
   # es . "  +  ",
   # es . "+++++",
   # es . "  +  ",
   # es . "  +  ",
   row = (" " * pickBox) + "+" + (" " * pickBox) 
   xpm.append(row)
   if size > 1:
      for i in range(pickBox - 1): # da 0
         xpm.append(row)
      xpm.append("+" * (size))
      for i in range(pickBox - 1): # da 0
         xpm.append(row)
      
   return QCursor(QPixmap(xpm))


def selectFeatures(layer, fetchAttributes, rect, fetchGeometry, useIntersect):
   # select() gives you flexibility in what data will be fetched.
   # It can get 4 arguments, all of them are optional:
   # fetchAttributes: List of attributes which should be fetched. Default: empty list
   # rect: Spatial filter. If empty rect is given (QgsRectangle()), all features are fetched. Default: empty rect
   # fetchGeometry: Whether geometry of the feature should be fetched. Default: True
   # useIntersect: When using spatial filter, this argument says whether accurate test for intersection 
   # should be done or whether test on bounding box suffices.
   # This is needed e.g. for feature identification or selection. Default: False
      
   # Se il rettangolo è schiacciato in verticale o in orizzontale
   # risulta una linea e la funzione fa casino, allora in questo caso sposto un pochino
   # la x massima o la y massima
   if rect is not None:
      r = QgsRectangle(rect)
      if r.xMinimum() == r.xMaximum(): 
         r.setXMaximum(r.xMaximum() + 1.e-6)
      if r.yMinimum() == r.yMaximum(): 
         r.setYMaximum(r.yMaximum() + 1.e-6)      
      return layer.select(fetchAttributes, r, fetchGeometry, useIntersect)
   else:
      return layer.select(fetchAttributes, QgsRectangle(), fetchGeometry, useIntersect)

   
def getEntSel(point, mQgsMapTool, \
              layers = None, checkPointLayer = True, checkLineLayer = True, checkPolygonLayer = True,
              onlyBoundary = True, onlyEditableLayers = False):
   """
   dato un punto (in screen coordinates) e un QgsMapTool, 
   la funzione cerca la prima entità dentro il quadrato
   di dimensioni PICKBOX centrato sul punto
   layer = opzionale, lista dei layer in cui cercare
   checkPointLayer = opzionale, considera i layer di tipo punto
   checkLineLayer = opzionale, considera i layer di tipo linea
   checkPolygonLayer = opzionale, considera i layer di tipo poligono
   onlyBoundary = serve per considerare solo il bordo dei poligoni o anche il loro interno
   Restituisce una lista composta da una QgsFeature e il suo layer e il punto di selezione 
   in caso di successo altrimenti None 
   """           
   
   if checkPointLayer == False and checkLineLayer == False and checkPolygonLayer == False:
      return None
      
   feature = QgsFeature()
   Tolerance = QadVariables.get("PICKBOX") # leggo la tolleranza
   
   #qad_debug.breakPoint()
   #QApplication.setOverrideCursor(Qt.WaitCursor)
   
   if layers is None:
      # Tutti i layer visibili visibili
      _layers = mQgsMapTool.canvas.layers()
   else:
      # solo la lista passata come parametro
      _layers = layers
      
   for layer in _layers: # ciclo sui layer
      # considero solo i layer vettoriali che sono filtrati per tipo
      if (layer.type() == layer.VectorLayer) and \
          ((layer.geometryType() == QGis.Point and checkPointLayer == True) or \
           (layer.geometryType() == QGis.Line and checkLineLayer == True) or \
           (layer.geometryType() == QGis.Polygon and checkPolygonLayer == True)) and \
           (onlyEditableLayers == False or layer.isEditable()):                      
         layerCoords = mQgsMapTool.toLayerCoordinates(layer, point)
         ToleranceInMapUnits = QgsTolerance.toleranceInMapUnits(Tolerance, layer, \
                                                                mQgsMapTool.canvas.mapRenderer(), \
                                                                QgsTolerance.Pixels)

         selectRect = QgsRectangle(layerCoords.x() - ToleranceInMapUnits, layerCoords.y() - ToleranceInMapUnits, \
                                   layerCoords.x() + ToleranceInMapUnits, layerCoords.y() + ToleranceInMapUnits)
                                  
         # Select features in rectangle           
         provider = layer.dataProvider()

         selectFeatures(layer, provider.attributeIndexes(), selectRect, True, True)
         
         # se è un layer contenente poligoni allora verifico se considerare solo i bordi
         if onlyBoundary == False or layer.geometryType() != QGis.Polygon:
            while layer.nextFeature(feature):
               #QApplication.restoreOverrideCursor()
               return feature, layer, point
         else:
            # considero solo i bordi delle geometrie e non lo spazio interno dei poligoni
            while layer.nextFeature(feature):
               # Riduco le geometrie in point o polyline
               geoms = asPointOrPolyline(feature.geometry())
               for g in geoms:
                  if g.intersects(selectRect):
                     return feature, layer, point
   
   #QApplication.restoreOverrideCursor()
   return None


def getActualSingleSelection(layers):
   """
   la funzione cerca se esiste una sola entità selezionata tra i layer
   Restituisce un QgsFeature e il suo layer in caso di successo altrimenti None 
   """
   selFeature = []

   for layer in layers: # ciclo sui layer
      if (layer.type() == layer.VectorLayer):
         selectedFeatureCount = layer.selectedFeaturCount()
         if selectedFeatureCount == 1:
            selFeature = layer.selectedFeatures()
            selLayer = Layer
         elif selectedFeatureCount > 1:
            del selFeature[:] # svuoto la lista
            break
      
   if len(selFeature) == 1: # se c'era solo una entità selezionata
      return selFeature[0], selLayer
  
   return None


def deselectAll(layers):
   """
   la funzione deseleziona tutte le entità selezionate nei layer
   """
   selFeatureIds = []
   for layer in layers: # ciclo sui layer
      if (layer.type() == layer.VectorLayer):
         if layer.selectedFeaturesIds() > 0:
            layer.setSelectedFeatures(selFeatureIds)


def getSelSet(mode, mQgsMapTool, points = None, \
              layers = None, checkPointLayer = True, checkLineLayer = True, checkPolygonLayer = True,
              onlyEditableLayers = False):
   """
   dato un QgsMapTool, una modalità di selezione e una lista opzionale di punti (in map coordinates),
   la funzione cerca le entità.
   mode = "C"  -> Crossing selection (inside and crossing)
          "CP" -> Crossing polygon (inside and crossing)
          "F"  -> Fence selection (crossing)
          "W"  -> Window selection (inside)
          "WP" -> Windows polygon (inside)
          "X"  -> all          
   layer = opzionale, lista dei layer in cui cercare
   checkPointLayer = opzionale, considera i layer di tipo punto
   checkLineLayer = opzionale, considera i layer di tipo linea
   checkPolygonLayer = opzionale, considera i layer di tipo poligono
   onlyEditableLayers = opzionale, considera i layer editabili
   Restituisce un QadEntitySet in caso di successo altrimenti None 
   """
        
   if checkPointLayer == False and checkLineLayer == False and checkPolygonLayer == False:
      return None
   
   entity = QadEntity()
   result = QadEntitySet()
   feature = QgsFeature()
   
   #QApplication.setOverrideCursor(Qt.WaitCursor)
   
   if layers is None:
      # Tutti i layer visibili visibili
      _layers = mQgsMapTool.canvas.layers()
   else:
      # solo la lista passata come parametro
      _layers = layers
      
   for layer in _layers: # ciclo sui layer
      # considero solo i layer vettoriali che sono filtrati per tipo
      if (layer.type() == layer.VectorLayer) and \
          ((layer.geometryType() == QGis.Point and checkPointLayer == True) or \
           (layer.geometryType() == QGis.Line and checkLineLayer == True) or \
           (layer.geometryType() == QGis.Polygon and checkPolygonLayer == True)) and \
           (onlyEditableLayers == False or layer.isEditable()):
         provider = layer.dataProvider()  

         if mode.upper() == "X": # take all features
            #qad_debug.breakPoint()
            selectFeatures(layer, provider.attributeIndexes(), None, True, False)
            while layer.nextFeature(feature):
               entity.set(layer, feature.id())
               result.addEntity(entity)
         elif mode.upper() == "C": # crossing selection
            p1 = mQgsMapTool.toLayerCoordinates(layer, points[0])
            p2 = mQgsMapTool.toLayerCoordinates(layer, points[1])
            selectRect = QgsRectangle(p1, p2)
            # Select features in rectangle           
            selectFeatures(layer, provider.attributeIndexes(), selectRect, True, True)
            while layer.nextFeature(feature):
               entity.set(layer, feature.id())
               result.addEntity(entity)
         elif mode.upper() == "W": # window selection
            p1 = mQgsMapTool.toLayerCoordinates(layer, points[0])
            p2 = mQgsMapTool.toLayerCoordinates(layer, points[1])
            selectRect = QgsRectangle(p1, p2)
            # Select features in rectangle           
            selectFeatures(layer, provider.attributeIndexes(), selectRect, True, True)
            
            g = QgsGeometry.fromRect(selectRect)
            # solo le feature completamente interne al rettangolo
            while layer.nextFeature(feature):               
               if g.contains(feature.geometry()):                     
                  entity.set(layer, feature.id())
                  result.addEntity(entity)
         elif mode.upper() == "CP": # crossing polygon
            polyline = []      
            for point in points:
               polyline.append(mQgsMapTool.toLayerCoordinates(layer, point))
            
            g = QgsGeometry.fromPolygon([polyline])
            # Select features in the polygon bounding box           
            selectFeatures(layer, provider.attributeIndexes(), g.boundingBox(), True, True)
            # solo le feature intersecanti il poligono
            while layer.nextFeature(feature):
               if g.intersects(feature.geometry()):                     
                  entity.set(layer, feature.id())
                  result.addEntity(entity)
         elif mode.upper() == "WP": # windows polygon
            polyline = []      
            for point in points:
               polyline.append(mQgsMapTool.toLayerCoordinates(layer, point))
            
            g = QgsGeometry.fromPolygon([polyline])
            # Select features in the polygon bounding box           
            selectFeatures(layer, provider.attributeIndexes(), g.boundingBox(), True, True)
            # solo le feature completamente interne al poligono
            while layer.nextFeature(feature):
               if g.contains(feature.geometry()):                     
                  entity.set(layer, feature.id())
                  result.addEntity(entity)
         elif mode.upper() == "CO": # crossing object
            #qad_debug.breakPoint()
            # points è in questo caso un QgsGeometry  
            g = QgsGeometry(points)
            if mQgsMapTool.canvas.mapRenderer().destinationCrs() != layer.crs():       
               coordTransform = QgsCoordinateTransform(mQgsMapTool.canvas.mapRenderer().destinationCrs(), \
                                                       layer.crs()) # trasformo la geometria
               g.transform(coordTransform)
                        
            # Select features in the object bounding box
            wkbType = g.wkbType()            
            if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:   
               Tolerance = QadVariables.get("PICKBOX") # leggo la tolleranza
               ToleranceInMapUnits = QgsTolerance.toleranceInMapUnits(Tolerance, layer, \
                                                                      mQgsMapTool.canvas.mapRenderer(), \
                                                                      QgsTolerance.Pixels)
      
               pt = g.asPoint()
               selectRect = QgsRectangle(pt.x() - ToleranceInMapUnits, pt.x() - ToleranceInMapUnits, \
                                         pt.y() + ToleranceInMapUnits, pt.y() + ToleranceInMapUnits)
               selectFeatures(layer, provider.attributeIndexes(), selectRect, True, True)
            else:
               selectFeatures(layer, provider.attributeIndexes(), g.boundingBox(), True, True)
               
            # solo le feature intersecanti l'oggetto
            while layer.nextFeature(feature):
               if g.intersects(feature.geometry()):                     
                  entity.set(layer, feature.id())
                  result.addEntity(entity)
         elif mode.upper() == "WO": # windows object
            # points è in questo caso un QgsGeometry  
            g = QgsGeometry(points)
            if mQgsMapTool.canvas.mapRenderer().destinationCrs() != layer.crs():       
               coordTransform = QgsCoordinateTransform(mQgsMapTool.canvas.mapRenderer().destinationCrs(), \
                                                       layer.crs()) # trasformo la geometria
               g.transform(coordTransform)

            # Select features in the object bounding box
            wkbType = g.wkbType()            
            if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:   
               Tolerance = QadVariables.get("PICKBOX") # leggo la tolleranza
               ToleranceInMapUnits = QgsTolerance.toleranceInMapUnits(Tolerance, layer, \
                                                                      mQgsMapTool.canvas.mapRenderer(), \
                                                                      QgsTolerance.Pixels)
      
               pt = g.asPoint()
               selectRect = QgsRectangle(pt.x() - ToleranceInMapUnits, pt.x() - ToleranceInMapUnits, \
                                         pt.y() + ToleranceInMapUnits, pt.y() + ToleranceInMapUnits)
               selectFeatures(layer, provider.attributeIndexes(), selectRect, True, True)
            else:
               selectFeatures(layer, provider.attributeIndexes(), g.boundingBox(), True, True)
            
            # solo le feature completamente interne all'oggetto
            while layer.nextFeature(feature):
               if g.contains(feature.geometry()):                     
                  entity.set(layer, feature.id())
                  result.addEntity(entity)
         elif mode.upper() == "F": # fence
            polyline = []      
            for point in points:
               polyline.append(mQgsMapTool.toLayerCoordinates(layer, point))
               
            g = QgsGeometry()
            g = QgsGeometry.fromPolyline(polyline)
            # Select features in the polyline bounding box           
            selectFeatures(layer, provider.attributeIndexes(), g.boundingBox(), True, True)
            while layer.nextFeature(feature):
               # solo le feature che intersecano la polyline
               if g.intersects(feature.geometry()):                     
                  entity.set(layer, feature.id())
                  result.addEntity(entity)
            
   #QApplication.restoreOverrideCursor()
   return result
   
   
def getIntersectionPoints(geom1, geom2):
   """
   la funzione ritorna una lista dei punti di intersezione tra le 2 geometrie. 
   """
   result = []
   # Riduco le geometrie in point o polyline
   geoms1 = asPointOrPolyline(geom1)
   geoms2 = asPointOrPolyline(geom2)
            
   for g1 in geoms1:
      for g2 in geoms2:
         p1 = g1.asPolyline()
         p2 = g2.asPolyline()
         intersectionGeoms = g1.intersection(g2)
         if intersectionGeoms is not None:
            for g in intersectionGeoms.asGeometryCollection():
               wkbType = g.wkbType()
               if wkbType == QGis.WKBPoint:
                   result.append(g.asPoint())
               elif wkbType == QGis.WKBLineString:
                  line = g.asPolyline()
                  # primo e ultimo vertice
                  result.append(line[0])
                  result.append(line[len(line) - 1])

   return result


def getNextPolygonVertex(vertex, totalSegment):
   return 0 if vertex == totalSegment - 1 else vertex + 1
def getPrevPolygonVertex(vertex, totalSegment):
   return totalSegment - 1 if vertex == 0 else vertex - 1
   
def getLinePart(geom, ptStart, ptEnd):
   """
   la funzione ritorna una lista dei punti che rappresenta una linea che va dal
   punto ptStart al punto ptEnd passando per il contorno di geom.
   """
   if ptStart == ptEnd:
      return None
   
   geomPtStart = QgsGeometry.fromPoint(ptStart)       
   geomPtEnd = QgsGeometry.fromPoint(ptEnd)
   
   isPolygon = True if geom.wkbType() == QGis.WKBPolygon else False
   
   # Riduco le geometrie in point o polyline
   geoms = asPointOrPolyline(geom)
            
   for g in geoms:
      if g.wkbType() == QGis.WKBPoint:
         continue
      points = g.asPolyline()
      totalSegment = len(points) - 1

      # cerco il segmento che contiene il punto iniziale
      found = False
      for segmentStart in xrange(0, totalSegment, 1):
         geomSegment = QgsGeometry.fromPolyline([points[segmentStart], points[segmentStart + 1]])
         if geomSegment.intersects(geomPtStart):
            found = True
            break            
      if found == False:
         continue        

      # cerco il segmento che contiene il punto finale
      found = False
      for segmentEnd in xrange(0, totalSegment, 1):
         geomSegment = QgsGeometry.fromPolyline([points[segmentEnd], points[segmentEnd + 1]])
         if geomSegment.intersects(geomPtEnd):
            found = True
            break            
      if found == False:
         continue        
      
      #qad_debug.breakPoint()
      
      if isPolygon == False:
         # trovata la polilinea che contiene il punto iniziale e finale
         result = [ptStart]
         if segmentStart < segmentEnd:
            # se il punto ptStart è uguale al punto iniziale del segmento successivo            
            if ptStart == points[segmentStart + 1]:
               segmentStart = segmentStart + 1
            
            for i in xrange(segmentStart + 1, segmentEnd + 1, 1):
               result.append(points[i])
                  
         elif segmentStart > segmentEnd:
            # se il punto ptEnd è uguale al punto finale del segmento            
            if ptEnd == points[segmentEnd + 1]:
               segmentEnd = segmentEnd + 1
            
            for i in xrange(segmentStart, segmentEnd, -1):
               result.append(points[i])
               
         result.append(ptEnd)     
      else:
         # do il senso di circolarità
         if ptStart == points[0]:
            segmentStart = totalSegment - 1
            
         if segmentStart == segmentEnd:
            return [ptStart, ptEnd]
         # Se è un poligono devo verificare il percorso più corto da ptStart e ptEnd
         
         # seguo il senso dei vertici
         result1 = [ptStart]         
         # se il punto ptStart è uguale al punto iniziale del segmento successivo
         i = segmentStart
         nextSegment = getNextPolygonVertex(segmentStart, totalSegment)          
         if ptStart == points[nextSegment]:
            i = nextSegment
         
         i = getNextPolygonVertex(i, totalSegment)
         nextSegment = getNextPolygonVertex(segmentEnd, totalSegment)
         while i != nextSegment:
            result1.append(points[i])
            i = getNextPolygonVertex(i, totalSegment)   
               
         result1.append(ptEnd)     
         
         # seguo il senso inverso dei vertici
         result2 = [ptStart]
         # se il punto ptEnd è uguale al punto finale del segmento 
         nextSegment = getNextPolygonVertex(segmentEnd, totalSegment)
         if ptEnd == points[nextSegment]:
            segmentEnd = nextSegment
         
         i = segmentStart
         segmentPrevEnd = getNextPolygonVertex(segmentEnd, totalSegment)
         while i != segmentEnd:
            result2.append(points[i])
            i = getPrevPolygonVertex(i, totalSegment)   
               
         result2.append(ptEnd)
         
         g1 = QgsGeometry.fromPolyline(result1)
         g2 = QgsGeometry.fromPolyline(result2)
         
         result = result1 if g1.length() < g2.length() else result2
      
      return result

   return None


def getPerpendicularPointOnInfinityLine(p1, p2, pt):
   """
   la funzione ritorna il punto di proiezione perpendicolare di pt 
   alla linea passante per p1-p2.
   """
   
   diffX = p2.x() - p1.x()
   diffY = p2.y() - p1.y()
                          
   if diffX == 0: # se la retta passante per p1 e p2 è verticale
      return QgsPoint(p1.x(), pt.y())
   elif diffY == 0: # se la retta passante per p1 e p2 è orizzontale
      return QgsPoint(pt.x(), p1.y())
   else:
      coeff = diffY / diffX
      x = (coeff * p1.x() - p1.y() + pt.x() / coeff + pt.y()) / (coeff + 1 / coeff)
      y = coeff * (x - p1.x()) + p1.y()
      
      return QgsPoint(x, y)


#===============================================================================
# getInfinityLinePerpOnMiddle
#===============================================================================
def getInfinityLinePerpOnMiddle(pt1, pt2):
   """
   dato un segmento pt1-pt2, la funzione trova una linea perpendicolare al segmento
   che passa per il suo punto medio. La funzione restituisce 2 punti della linea.
   """
   ptMiddle = qad_utils.getMiddlePoint(pt1, pt2)
   dist = getDistance(pt1, ptMiddle)
   if dist == 0:
      return None
   angle = getAngleBy2Pts(pt1, pt2) + math.pi / 2
   pt2Middle = getPolarPointByPtAngle(ptMiddle, angle, dist)
   return ptMiddle, pt2Middle


#===============================================================================
# getBisectorInfinityLine
#===============================================================================
def getBisectorInfinityLine(pt1, pt2, pt3, acuteMode = True):
   """
   dato un angolo definito da 3 punti il cui secondo punto è vertice dell'angolo,
   la funzione restituisce la linea bisettrice dell'angolo attraverso 2 punti 
   della linea (il vertice dell'angolo e un altro punto calcolato distante quanto
   la distanza di pt1 da pt2).
   acuteMode = True considera l'angolo acuto, acuteMode = False l'angolo ottuso 
   """   
   angle1 = getAngleBy2Pts(pt2, pt1)
   angle2 = getAngleBy2Pts(pt2, pt3)
   angle = (angle1 + angle2) / 2 # angolo medio
#   return pt2, getPolarPointByPtAngle(pt2, angle, 10)
   
   dist = getDistance(pt1, pt2)
   ptProj = getPolarPointByPtAngle(pt2, angle, dist)
   ptInverseProj = getPolarPointByPtAngle(pt2, angle - math.pi, dist)
   if getDistance(pt1, ptProj) < getDistance(pt1, ptInverseProj):
      if acuteMode == True:
         return pt2, ptProj
      else:
         return pt2, ptInverseProj
   else:
      if acuteMode == True:
         return pt2, ptInverseProj
      else:
         return pt2, ptProj

#===============================================================================
# getXOnInfinityLine
#===============================================================================
def getXOnInfinityLine(p1, p2, y):
   """
   data la coordinata Y di un punto la funzione ritorna la coordinata X dello stesso
   sulla linea passante per p1-p2 
   """
   
   diffX = p2.x() - p1.x()
   diffY = p2.y() - p1.y()
                          
   if diffX == 0: # se la retta passante per p1 e p2 è verticale
      return p1.x()
   elif diffY == 0: # se la retta passante per p1 e p2 è orizzontale
      return None # infiniti punti
   else:
      coeff = diffY / diffX
      return p1.x() + (y - p1.y()) / coeff


#===============================================================================
# getYOnInfinityLine
#===============================================================================
def getYOnInfinityLine(p1, p2, x):
   """
   data la coordinata Y di un punto la funzione ritorna la coordinata X dello stesso
   sulla linea passante per p1-p2 
   """
   
   diffX = p2.x() - p1.x()
   diffY = p2.y() - p1.y()
                          
   if diffX == 0: # se la retta passante per p1 e p2 è verticale
      return None # infiniti punti
   elif diffY == 0: # se la retta passante per p1 e p2 è orizzontale
      return p1.y()
   else:
      coeff = diffY / diffX
      return p1.y() + (x - p1.x()) * coeff


#===============================================================================
# getDistance
#===============================================================================
def getDistance(p1, p2):
   """
   la funzione ritorna la distanza tra 2 punti (QgsPoint)
   """
   dx = p2.x() - p1.x()
   dy = p2.y() - p1.y()
   
   return math.sqrt(dx * dx + dy * dy)


#===============================================================================
# getMiddlePoint
#===============================================================================
def getMiddlePoint(p1, p2):
   """
   la funzione ritorna il punto medio tra 2 punti (QgsPoint)
   """
   x = (p1.x() + p2.x()) / 2
   y = (p1.y() + p2.y()) / 2
   
   return QgsPoint(x, y)


#===============================================================================
# getAngleBy2Pts
#===============================================================================
def getAngleBy2Pts(p1, p2):
   """
   la funzione ritorna l'angolo in radianti della retta passante per p1 e p2
   """
   diffX = p2.x() - p1.x()
   diffY = p2.y() - p1.y()
   if diffX == 0: # se la retta passante per p1 e p2 è verticale
      if p1.y() < p2.y():
         angle = math.pi / 2
      else :
         angle = math.pi * 3 / 2
   elif diffY == 0: # se la retta passante per p1 e p2 è orizzontale
      if p1.x() <= p2.x():
         angle = 0.0
      else:
         angle = math.pi
   else:
      angle = math.atan(diffY / diffX)
      if diffX < 0:
         angle = math.pi + angle
      else:
         if diffY < 0:
            angle = 2 * math.pi + angle

   return angle


#===============================================================================
# isAngleBetweenAngles
#===============================================================================
def isAngleBetweenAngles(startAngle, endAngle, angle):
   """endAngle
   la funzione ritorna True se l'angolo si trova entro l'angolo di partenza e quello finale
   estremi compresi
   """
   _angle = angle % (math.pi * 2) # modulo
   if _angle < 0:
      _angle = (math.pi * 2) - _angle
      
   if startAngle < endAngle:
      if (_angle > startAngle or doubleNear(_angle, startAngle, 1.e-9)) and \
         (_angle < endAngle or doubleNear(_angle, endAngle, 1.e-9)):
         return True      
   else:
      if (_angle > 0 or doubleNear(_angle, 0, 1.e-9)) and \
         (_angle < endAngle or doubleNear(_angle, endAngle, 1.e-9)):
         return True      

      if (_angle < (math.pi * 2) or doubleNear(_angle, (math.pi * 2), 1.e-9)) and \
         (_angle > startAngle or doubleNear(_angle, startAngle, 1.e-9)):
         return True      
   
   return False


def getPolarPointBy2Pts(p1, p2, dist):
   """
   la funzione ritorna il punto sulla retta passante per p1 e p2 che
   dista da p1 verso p2 <dist>.
   """
   angle = getAngleBy2Pts(p1, p2)
         
   return getPolarPointByPtAngle(p1, angle, dist)


#===============================================================================
# isPtOnSegment
#===============================================================================
def isPtOnSegment(p1, p2, point):
   """
   la funzione ritorna true se il punto è sul segmento (estremi compresi).
   """
   if p1[0] < p2[0]:
      xMin = p1[0]
      xMax = p2[0]
   else:
      xMax = p1[0]
      xMin = p2[0]
      
   if p1[1] < p2[1]:
      yMin = p1[1]
      yMax = p2[1]
   else:
      yMax = p1[1]
      yMin = p2[1]
            
   if (point[0] > xMin or doubleNear(point[0], xMin, 1.e-9)) and \
      (point[0] < xMax or doubleNear(point[0], xMax, 1.e-9)) and \
      (point[1] > yMin or doubleNear(point[1], yMin, 1.e-9)) and \
      (point[1] < yMax or doubleNear(point[1], yMax, 1.e-9)):
      return True
   else:
      return False  


#===============================================================================
# getIntersectionPointOn2InfinityLines
#===============================================================================
def getIntersectionPointOn2InfinityLines(line1P1, line1P2, line2P1, line2P2):
   """
   la funzione ritorna il punto di intersezione tra la linea passante per line1P1-line1P2 e
   la linea passante per line2P1-line2P2.
   """
   line1DiffX = line1P2.x() - line1P1.x()
   line1DiffY = line1P2.y() - line1P1.y()

   line2DiffX = line2P2.x() - line2P1.x()
   line2DiffY = line2P2.y() - line2P1.y()
   
   if line1DiffX == 0 and line2DiffX == 0: # se la retta1 e la retta2 sono verticale
      return None # sono parallele
   elif line1DiffY == 0 and line2DiffY == 0: # se la retta1 e la retta2 sono orizzonatali
      return None # sono parallele

   if line1DiffX == 0: # se la retta1 è verticale
      return QgsPoint(line1P2.x(), getYOnInfinityLine(line2P1, line2P2, line1P2.x()))
   if line1DiffY == 0: # se la retta1 è orizzontale
      return QgsPoint(getXOnInfinityLine(line2P1, line2P2, line1P2.y()), line1P2.y())
   if line2DiffX == 0: # se la retta2 è verticale
      return QgsPoint(line2P2.x(), getYOnInfinityLine(line1P1, line1P2, line2P2.x()))
   if line2DiffY == 0: # se la retta2 è orizzontale
      return QgsPoint(getXOnInfinityLine(line1P1, line1P2, line2P2.y()), line2P2.y())

   line1Coeff = line1DiffY / line1DiffX
   line2Coeff = line2DiffY / line2DiffX

   if line1Coeff == line2Coeff: # sono parallele
      return None
   
   x = line1P1.x() * line1Coeff - line1P1.y() - line2P1.x() * line2Coeff + line2P1.y()
   x = x / (line1Coeff - line2Coeff)
   y = (x - line1P1.x()) * line1Coeff + line1P1.y()
   
   return QgsPoint(x, y)


def getNearestPoints(point, points, tolerance = 0):
   """
   Ritorna una lista di punti più vicino a point.
   """   
   result = []   
   minDist = sys.float_info.max
   
   if tolerance == 0: # solo il punti più vicino
      for pt in points:
         dist = getDistance(point, pt)
         if dist < minDist:
            minDist = dist
            nearestPoint = pt

      if minDist != sys.float_info.max: # trovato
         result.append(nearestPoint)
   else:
      nearest = __getNearestPoints(point, points) # punto più vicino
      nearestPoint = nearest[0]
      
      for pt in points:
         dist = getDistance(nearestPoint, pt)
         if dist <= tolerance:
            result.append(pt)

   return result


def getPolarPointByPtAngle(p1, angle, dist):
   """
   la funzione ritorna il punto sulla retta passante per p1 con angolo <angle> che
   dista da p1 <dist>.
   """
   y = dist * math.sin(angle)
   x = dist * math.cos(angle)
   return QgsPoint(p1.x() + x, p1.y() + y)


def asPointOrPolyline(geom):
   """
   la funzione ritorna una lista di geometrie di punti e/o polilinee in cui viene ridotta la geometria. 
   """
   # Riduco le geometrie in point o polyline
   result = []
   for g in geom.asGeometryCollection():
      wkbType = g.wkbType()
      if wkbType == QGis.WKBPoint or wkbType == QGis.WKBLineString:
         result.append(g)
      elif wkbType == QGis.WKBMultiPoint:
         pointList = g.asMultiPoint() # vettore di punti
         for point in pointList:
            _g = QgsGeometry.fromPoint(point)
            result.append(_g)            
      elif wkbType == QGis.WKBMultiLineString:
         lineList = g.asMultiPolyline() # vettore di linee
         for line in lineList:
            _g = QgsGeometry.fromPolyline(line)
            result.append(_g)
      elif wkbType == QGis.WKBPolygon:
         lineList = g.asPolygon() # vettore di linee    
         for line in lineList:
            _g = QgsGeometry.fromPolyline(line)
            result.append(_g)
      elif wkbType == QGis.WKBMultiPolygon:
         polygonList = g.asMultiPolygon() # vettore di poligoni
         for polygon in polygonList:
            for line in polygon:
               _g = QgsGeometry.fromPolyline(line)
               result.append(_g)
               
   return result


def leftOfLineCoords(x, y, x1, y1, x2, y2):
   """
   la funzione ritorna una numero < 0 se il punto x,y è alla sinistra della linea x1,y1 -> x2,y2
   """
   f1 = x - x1
   f2 = y2 - y1
   f3 = y - y1
   f4 = x2 - x1
   return f1*f2 - f3*f4

def leftOfLine(pt, pt1, pt2):
   return leftOfLineCoords(pt.x(), pt.y(), pt1.x(), pt1.y(), pt2.x(), pt2.y())


def ptNear(pt1, pt2, epsilon):
   """
   la funzione compara 2 punti (ma permette una differenza)
   """
   return doubleNear(pt1.x(), pt2.x(), epsilon) and doubleNear(pt1.y(), pt2.y(), epsilon)


def doubleNear(a, b, epsilon):
   """
   la funzione compara 2 float (ma permette una differenza)
   """
   diff = a - b
   return diff > -epsilon and diff <= epsilon


def doubleListAvg(dblList):
   """
   la funzione compara 2 float (ma permette una differenza)
   """
   if (dblList is None) or len(dblList) == 0:
      return None
   sum = 0
   for num in dblList:
      sum = sum + num
      
   return sum / len(dblList)


def sqrDistToSegment(point, x1, y1, x2, y2, epsilon):
   """
   la funzione ritorna una lista con 
   (<minima distanza al quadrato>
    <punto più vicino>)
   """
   minDistPoint = QgsPoint()
   
   if x1 == x2 and y1 == y2:
      minDistPoint.setX(x1)
      minDistPoint.setY(y1)
   else:
      nx = y2 - y1
      ny = -( x2 - x1 )
   
      t = (point.x() * ny - point.y() * nx - x1 * ny + y1 * nx ) / (( x2 - x1 ) * ny - ( y2 - y1 ) * nx )
   
      if t < 0.0:
         minDistPoint.setX(x1)
         minDistPoint.setY(y1)
      elif t > 1.0:
         minDistPoint.setX(x2)
         minDistPoint.setY(y2)
      else:
         minDistPoint.setX( x1 + t *( x2 - x1 ) )
         minDistPoint.setY( y1 + t *( y2 - y1 ) )

   dist = point.sqrDist(minDistPoint)
   # prevent rounding errors if the point is directly on the segment 
   if doubleNear( dist, 0.0, epsilon ):
      minDistPoint.setX( point.x() )
      minDistPoint.setY( point.y() )
      return (0.0, minDistPoint)
  
   return (dist, minDistPoint)


#===============================================================================
# closestSegmentWithContext
#===============================================================================
def closestSegmentWithContext(point, geom, epsilon = 1.e-15):
   """
   la funzione ritorna una lista con 
   (<minima distanza al quadrato>
    <punto più vicino>
    <indice vertice successivo del segmento più vicino (nel caso la geom fosse linea o poligono)>
    <"a sinistra di" se il punto è alla sinista del segmento (< 0 -> sinistrat, > 0 -> destra)
   """
   minDistPoint = QgsPoint()
   closestSegmentIndex = 0
   wkbType = geom.wkbType()
   sqrDist = sys.float_info.max

   if wkbType == QGis.WKBPoint:
      minDistPoint = geom.asPoint()
      point.sqrDist(minDistPoint)
      return (point.sqrDist(minDistPoint), minDistPoint, None, None)
 
   if wkbType == QGis.WKBMultiPoint:
      minDistPoint = getNearestPoints(point, geom.asMultiPoint())[0] # vettore di punti
      return (point.sqrDist(minDistPoint), minDistPoint, None, None)

   if wkbType == QGis.WKBLineString:
      points = geom.asPolyline() # vettore di punti
      index = 0
      for pt in points:
         if index > 0:
            prevX = thisX
            prevY = thisY
           
         thisX = pt.x()
         thisY = pt.y()

         if index > 0:
            result = sqrDistToSegment(point, prevX, prevY, thisX, thisY, epsilon)
            testdist = result[0]
            distPoint = result[1] 
                      
            if testdist < sqrDist:
               closestSegmentIndex = index
               sqrDist = testdist
               minDistPoint = distPoint
               
         index = index + 1

      leftOf = leftOfLine(point, geom.vertexAt(closestSegmentIndex - 1), geom.vertexAt(closestSegmentIndex))
      return (sqrDist, minDistPoint, closestSegmentIndex, leftOf)

   if wkbType == QGis.WKBMultiLineString:
      lines = geom.asMultiPolyline() # lista di linee
      pointindex = 0
      for line in lines:
         prevX = 0
         prevY = 0
        
         for pt in line: # lista di punti
            thisX = pt.x()
            thisY = pt.y()
          
            if prevX and prevY:
               result = sqrDistToSegment(point, prevX, prevY, thisX, thisY, epsilon)
               testdist = result[0]
               distPoint = result[1] 

               if testdist < sqrDist:
                  closestSegmentIndex = index
                  sqrDist = testdist
                  minDistPoint = distPoint

            prevX = thisX
            prevY = thisY
            pointindex = pointindex + 1
         
      leftOf = leftOfLine(point, geom.vertexAt(closestSegmentIndex - 1), geom.vertexAt(closestSegmentIndex))         
      return (sqrDist, minDistPoint, closestSegmentIndex, leftOf)

   if wkbType == QGis.WKBPolygon:
      lines = geom.asPolygon() # lista di linee    
      index = 0
      for line in lines:
         prevX = 0
         prevY = 0

         for pt in line: # lista di punti
            thisX = pt.x()
            thisY = pt.y()

            if prevX and prevY:
               result = sqrDistToSegment(point, prevX, prevY, thisX, thisY, epsilon)
               testdist = result[0]
               distPoint = result[1] 

               if testdist < sqrDist:
                  closestSegmentIndex = index
                  sqrDist = testdist
                  minDistPoint = distPoint

            prevX = thisX
            prevY = thisY
            index = index + 1
            
      leftOf = leftOfLine(point, geom.vertexAt(closestSegmentIndex - 1), geom.vertexAt(closestSegmentIndex))
      return (sqrDist, minDistPoint, closestSegmentIndex, leftOf)

   if wkbType == QGis.WKBMultiPolygon:
      polygons = geom.asMultiPolygon() # vettore di poligoni
      pointindex = 0
      for polygon in polygons:
         for line in polygon: # lista di linee
            prevX = 0
            prevY = 0
         
            for pt in line: # lista di punti
               thisX = pt.x()
               thisY = pt.y()
   
               if prevX and prevY:
                  result = sqrDistToSegment(point, prevX, prevY, thisX, thisY, epsilon)
                  testdist = result[0]
                  distPoint = result[1] 
   
                  if testdist < sqrDist:
                     closestSegmentIndex = pointindex
                     sqrDist = testdist
                     minDistPoint = distPoint
   
               prevX = thisX
               prevY = thisY
               pointindex = pointindex + 1
      
      leftOf = leftOfLine(point, geom.vertexAt(closestSegmentIndex - 1), geom.vertexAt(closestSegmentIndex))
      return (sqrDist, minDistPoint, closestSegmentIndex, leftOf)

   return (-1, None, None, None)


#===============================================================================
# rotatePoint
#===============================================================================
def rotatePoint(point, basePt, angle):
   """
   la funzione ruota un punto QgsPoint secondo un punto base <basePt> e un angolo <angle> in radianti 
   """
   return getPolarPointByPtAngle(basePt, getAngleBy2Pts(basePt, point) + angle, getDistance(basePt, point))


#===============================================================================
# rotateQgsGeometry
#===============================================================================
def rotateQgsGeometry(geom, basePt, angle):
   """
   la funzione ruota la geometria secondo un punto base <basePt> e un angolo <angle> in radianti
   """
   if geom is None:
      return None

   wkbType = geom.wkbType()
   
   if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:
      pt = geom.asPoint() # un punto
      newPt = rotatePoint(pt, basePt, angle)
      return QgsGeometry.fromPoint(newPt)

   if wkbType == QGis.WKBMultiPoint:
      points = geom.asMultiPoint() # vettore di punti
      for pt in points:
         newPt = rotatePoint(pt, basePt, angle)
         pt.set(newPt.x(), newPt.y())
      return QgsGeometry.fromMultiPoint(points)
   
   if wkbType == QGis.WKBLineString:
      points = geom.asPolyline() # vettore di punti
      for pt in points:
         newPt = rotatePoint(pt, basePt, angle)
         pt.set(newPt.x(), newPt.y())
         
      return QgsGeometry.fromPolyline(points)
   
   if wkbType == QGis.WKBMultiLineString:
      lines = geom.asMultiPolyline() # lista di linee
      for line in lines:        
         for pt in line: # lista di punti
            newPt = rotatePoint(pt, basePt, angle)
            pt.set(newPt.x(), newPt.y())

      return QgsGeometry.fromMultiPolyline(lines)
   
   if wkbType == QGis.WKBPolygon:
      lines = geom.asPolygon() # lista di linee    
      for line in lines:
         for pt in line: # lista di punti
            newPt = rotatePoint(pt, basePt, angle)
            pt.set(newPt.x(), newPt.y())
            
      return QgsGeometry.fromPolygon(lines)

   if wkbType == QGis.WKBMultiPolygon:
      polygons = geom.asMultiPolygon() # vettore di poligoni
      for polygon in polygons:
         for line in polygon: # lista di linee
            for pt in line: # lista di punti
               newPt = rotatePoint(pt, basePt, angle)
               pt.set(newPt.x(), newPt.y())
               
      return QgsGeometry.fromPolygon(polygons)

   return None


#===============================================================================
# scalePoint
#===============================================================================
def scalePoint(point, basePt, scale):
   """
   la funzione scala un punto QgsPoint secondo un punto base <basePt> e un fattore di scala
   """
   return getPolarPointByPtAngle(basePt, getAngleBy2Pts(basePt, point), getDistance(basePt, point) * scale)


#===============================================================================
# scaleQgsGeometry
#===============================================================================
def scaleQgsGeometry(geom, basePt, scale):
   """
   la funzione scala la geometria secondo un punto base <basePt> e un fattore di scala
   """
   if geom is None:
      return None

   wkbType = geom.wkbType()
   
   if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:
      pt = geom.asPoint() # un punto
      newPt = scalePoint(pt, basePt, scale)
      return QgsGeometry.fromPoint(newPt)

   if wkbType == QGis.WKBMultiPoint:
      points = geom.asMultiPoint() # vettore di punti
      for pt in points:
         newPt = scalePoint(pt, basePt, scale)
         pt.set(newPt.x(), newPt.y())
      return QgsGeometry.fromMultiPoint(points)
   
   if wkbType == QGis.WKBLineString:
      points = geom.asPolyline() # vettore di punti
      for pt in points:
         newPt = scalePoint(pt, basePt, scale)
         pt.set(newPt.x(), newPt.y())
            
      return ApproxCurvesOnGeom(QgsGeometry.fromPolyline(points))   
   
   if wkbType == QGis.WKBMultiLineString:
      lines = geom.asMultiPolyline() # lista di linee
      for line in lines:        
         for pt in line: # lista di punti
            newPt = scalePoint(pt, basePt, scale)
            pt.set(newPt.x(), newPt.y())

      return ApproxCurvesOnGeom(QgsGeometry.fromMultiPolyline(lines))   

   
   if wkbType == QGis.WKBPolygon:
      lines = geom.asPolygon() # lista di linee    
      for line in lines:
         for pt in line: # lista di punti
            newPt = scalePoint(pt, basePt, scale)
            pt.set(newPt.x(), newPt.y())
            
      return ApproxCurvesOnGeom(QgsGeometry.fromPolygon(lines))   

   if wkbType == QGis.WKBMultiPolygon:
      polygons = geom.asMultiPolygon() # vettore di poligoni
      for polygon in polygons:
         for line in polygon: # lista di linee
            for pt in line: # lista di punti
               newPt = scalePoint(pt, basePt, scale)
               pt.set(newPt.x(), newPt.y())
               
      return ApproxCurvesOnGeom(QgsGeometry.fromPolygon(polygons))   

   return None


#===============================================================================
# movePoint
#===============================================================================
def movePoint(point, offSetX, offSetY):
   """
   la funzione sposta un punto QgsPoint secondo un offset X uno Y
   """
   return QgsPoint(point.x() + offSetX, point.y() + offSetY)


#===============================================================================
# moveQgsGeometry
#===============================================================================
def moveQgsGeometry(geom, offSetX, offSetY):
   """
   la funzione sposta la geometria secondo un offset X uno Y
   """
   if geom is None:
      return None

   wkbType = geom.wkbType()
   
   if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:
      pt = geom.asPoint() # un punto
      newPt = movePoint(pt, offSetX, offSetY)
      return QgsGeometry.fromPoint(newPt)

   if wkbType == QGis.WKBMultiPoint:
      points = geom.asMultiPoint() # vettore di punti
      for pt in points:
         newPt = movePoint(pt, offSetX, offSetY)
         pt.set(newPt.x(), newPt.y())
      return QgsGeometry.fromMultiPoint(points)
   
   if wkbType == QGis.WKBLineString:
      points = geom.asPolyline() # vettore di punti
      for pt in points:
         newPt = movePoint(pt, offSetX, offSetY)
         pt.set(newPt.x(), newPt.y())
         
      return QgsGeometry.fromPolyline(points)
   
   if wkbType == QGis.WKBMultiLineString:
      lines = geom.asMultiPolyline() # lista di linee
      for line in lines:        
         for pt in line: # lista di punti
            newPt = movePoint(pt, offSetX, offSetY)
            pt.set(newPt.x(), newPt.y())

      return QgsGeometry.fromMultiPolyline(lines)
   
   if wkbType == QGis.WKBPolygon:
      lines = geom.asPolygon() # lista di linee    
      for line in lines:
         for pt in line: # lista di punti
            newPt = movePoint(pt, offSetX, offSetY)
            pt.set(newPt.x(), newPt.y())
            
      return QgsGeometry.fromPolygon(lines)

   if wkbType == QGis.WKBMultiPolygon:
      polygons = geom.asMultiPolygon() # vettore di poligoni
      for polygon in polygons:
         for line in polygon: # lista di linee
            for pt in line: # lista di punti
               newPt = movePoint(pt, offSetX, offSetY)
               pt.set(newPt.x(), newPt.y())
               
      return QgsGeometry.fromPolygon(polygons)

   return None


#===============================================================================
# getSubGeom
#===============================================================================
def getSubGeom(geom, atVertex):
   wkbType = geom.wkbType()
   
   if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D or wkbType == QGis.WKBMultiPoint or \
      wkbType == QGis.WKBLineString:
      return QgsGeometry(geom)
      
   if wkbType == QGis.WKBMultiLineString:
      # cerco in quale linea è il vertice <atVertex>
      i = 0
      lines = geom.asMultiPolyline()
      for line in lines:
         lineLen = len(line)
         if atVertex >= i and atVertex < i + lineLen:
            return QgsGeometry.fromPolyline(line)
         i = lineLen 
      return None
   
   if wkbType == QGis.WKBPolygon:
      i = 0
      lines = geom.asPolygon() # lista di linee    
      for line in lines:
         lineLen = len(line)
         if atVertex >= i and atVertex < i + lineLen:
            return QgsGeometry.fromPolyline(line)
         i = lineLen 
      return None

   if wkbType == QGis.WKBMultiPolygon:
      i = 0
      polygons = geom.asMultiPolygon() # vettore di poligoni
      for polygon in polygons:
         for line in lines:
            lineLen = len(line)
            if atVertex >= i and atVertex < i + lineLen:
               return QgsGeometry.fromPolyline(line)
            i = lineLen 
         return None
   
   return None


#===============================================================================
# getOffSetCircle
#===============================================================================
def getOffSetCircle(circle, offSetDist, offSetSide):
   """
   la funzione ritorna l'offset di un cerchio
   secondo una distanza e un lato di offset ("internal" o "external")        
   """
   if offSetSide == "internal":
      # offset verso l'interno del cerchio
      radius = circle.radius - offSetDist
      if radius <= 0:
         return None
   else:
      # offset verso l'esterno del cerchio
      radius = circle.radius + offSetDist

   result = QadCircle(circle)
   result.radius = radius
       
   return result


#===============================================================================
# getOffSetArc
#===============================================================================
def getOffSetArc(arc, offSetDist, offSetSide):
   """
   la funzione ritorna l'offset di un arco
   secondo una distanza e un lato di offset ("internal" o "external")        
   """
   if offSetSide == "internal":
      # offset verso l'interno del cerchio
      radius = arc.radius - offSetDist
      if radius <= 0:
         return None
   else:
      # offset verso l'esterno del cerchio
      radius = arc.radius + offSetDist

   result = QadArc(arc)
   result.radius = radius
       
   return result


#===============================================================================
# getOffSetLine
#===============================================================================
def getOffSetLine(pt1, pt2, offSetDist, offSetSide):
   """
   la funzione ritorna l'offset di una linea (lista di 2 punti)
   secondo una distanza e un lato di offset ("right" o "left")        
   """
   if offSetSide == "right":
      AngleProjected = getAngleBy2Pts(pt1, pt2) - (math.pi / 2)
   else:
      AngleProjected = getAngleBy2Pts(pt1, pt2) + (math.pi / 2)
   # calcolo il punto proiettato
   pt1Proj = getPolarPointByPtAngle(pt1, AngleProjected, offSetDist)
   pt2Proj = getPolarPointByPtAngle(pt2, AngleProjected, offSetDist)
       
   return [pt1Proj, pt2Proj]

#===============================================================================
# bridgeTheGapBetweenLines_offset
#===============================================================================
def bridgeTheGapBetweenLines_offset(line1, line2, offSetDist, gapType, tolerance2ApproxCurve = None):
   """
   la funzione colma il vuoto tra 2 linee di cui si è fatto l'offset.  
   secondo una distanza ed un modo <gapType>:
   0 = Estende i segmenti di linea alle relative intersezioni proiettate
   1 = Raccorda i segmenti di linea in corrispondenza delle relative intersezioni proiettate.
       Il raggio di ciascun segmento di arco è uguale alla distanza di offset
   2 = Cima i segmenti di linea in corrispondenza delle intersezioni proiettate.
       La distanza perpendicolare da ciascuna cima al rispettivo vertice
       sull'oggetto originale è uguale alla distanza di offset.
   tolerance2ApproxCurve = errore minimo di tolleranza
   
   Ritorna una lista di 3 elementi (None in caso di errore):   
   una linea che sostituisce <line1>, se = None <line1> va rimossa
   un arco, se = None non c'è arco di raccordo tra le due linee
   una linea che sostituisce <line2>, se = None <line2> va rimossa
   """
   # cerco il punto di intersezione tra le due linee
   ptInt = getIntersectionPointOn2InfinityLines(line1[0], line1[1], line2[0], line2[1])
   if ptInt is None: # linee parallele
      return None
   distBetweenLine1Pt1AndPtInt = getDistance(line1[0], ptInt)
   distBetweenLine1Pt2AndPtInt = getDistance(line1[1], ptInt)
   distBetweenLine2Pt1AndPtInt = getDistance(line2[0], ptInt)
   distBetweenLine2Pt2AndPtInt = getDistance(line2[1], ptInt)
   
   if gapType == 0: # Estende i segmenti     
      if distBetweenLine1Pt1AndPtInt > distBetweenLine1Pt2AndPtInt:
         # secondo punto di line1 più vicino al punto di intersezione
         newLine1 = [line1[0], ptInt]
      else:
         # primo punto di line1 più vicino al punto di intersezione
         newLine1 = [ptInt, line1[1]]
         
      if distBetweenLine2Pt1AndPtInt > distBetweenLine2Pt2AndPtInt:
         # secondo punto di line2 più vicino al punto di intersezione
         newLine2 = [line2[0], ptInt]
      else:
         # primo punto di line2 più vicino al punto di intersezione
         newLine2 = [ptInt, line2[1]]
      
      return [newLine1, None, newLine2]
   elif gapType == 1: # Raccorda i segmenti      
      angleLine1 = getAngleBy2Pts(ptInt, line1[0])   
      angleLine2 = getAngleBy2Pts(ptInt, line2[0])   

      bisectorLine = getBisectorInfinityLine(line1[1], ptInt, line2[1], True)
      angleBisectorLine = getAngleBy2Pts(bisectorLine[0], bisectorLine[1])

      # calcolo l'angolo (valore assoluto) tra un lato e la bisettrice            
      alfa = angleLine1 - angleBisectorLine
      if alfa < 0:
         alfa = angleBisectorLine - angleLine1      
      if alfa > math.pi:
         alfa = (2 * math.pi) - alfa 

      distFromPtInt = offSetDist / math.sin(alfa)
      pt1Proj = getPolarPointByPtAngle(ptInt, angleLine1, distFromPtInt)
      pt2Proj = getPolarPointByPtAngle(ptInt, angleLine2, distFromPtInt)
      # Pitagora
      distFromPtInt = math.sqrt((distFromPtInt * distFromPtInt) + (offSetDist * offSetDist))      
      secondPt = getPolarPointByPtAngle(ptInt, angleBisectorLine, distFromPtInt - offSetDist)
      arc = QadArc()
      arc.fromStartSecondEndPts(pt1Proj, secondPt, pt2Proj)
      
      if distBetweenLine1Pt1AndPtInt > distBetweenLine1Pt2AndPtInt:
         # secondo punto di line1 più vicino al punto di intersezione
         newLine1 = [line1[0], pt1Proj]
      else:
         # primo punto di line1 più vicino al punto di intersezione
         newLine1 = [pt1Proj, line1[1]]      

      if distBetweenLine2Pt1AndPtInt > distBetweenLine2Pt2AndPtInt:
         # secondo punto di line2 più vicino al punto di intersezione
         newLine2 = [line2[0], pt2Proj]
      else:
         # primo punto di line2 più vicino al punto di intersezione
         newLine2 = [pt2Proj, line2[1]]
      
      # se i punti sono così vicini da essere considerati uguali         
      inverse = False if ptNear(newLine1[1], arc.getStartPt(), 1.e-9) else True
      return [newLine1, [arc, inverse], newLine2]
   elif gapType == 2: # Cima i segmenti
      bisectorLine = getBisectorInfinityLine(line1[1], ptInt, line2[1], True)
      angleBisectorLine = getAngleBy2Pts(bisectorLine[0], bisectorLine[1])
      ptProj = getPolarPointByPtAngle(ptInt, angleBisectorLine, offSetDist)

      pt1Proj = getPerpendicularPointOnInfinityLine(line1[0], line1[1], ptProj)
      if distBetweenLine1Pt1AndPtInt > distBetweenLine1Pt2AndPtInt:
         # secondo punto di line1 più vicino al punto di intersezione
         newLine1 = [line1[0], pt1Proj]
      else:
         # primo punto di line1 più vicino al punto di intersezione
         newLine1 = [pt1Proj, line1[1]]      

      pt2Proj = getPerpendicularPointOnInfinityLine(line2[0], line2[1], ptProj)
      if distBetweenLine2Pt1AndPtInt > distBetweenLine2Pt2AndPtInt:
         # secondo punto di line2 più vicino al punto di intersezione
         newLine2 = [line2[0], pt2Proj]
      else:
         # primo punto di line2 più vicino al punto di intersezione
         newLine2 = [pt2Proj, line2[1]]

      return [newLine1, [pt1Proj, pt2Proj], newLine2]

   return None

#===============================================================================
# getPartListFromPolylinePts
#===============================================================================
def getPartListFromPolylinePts(points):
   """
   la funzione ritorna una lista di segmenti e archi che compone la polilinea
   es. (<segmento> <arco> ...).
   Se una parte ha punto iniziale e finale coincidenti 
   (es. 2 vertici consecutivi che si sovrappongono o arco con angolo totale = 0 oppure = 360)
   la parte viene rimossa dalla lista.
   
   dove:
    segmento = (<pt1> <pt2>)
   arco = (<QadArc> <inverse>)
   <inverse> = se True significa che il punto iniziale dell'arco deve essere 
               considerato finale nel senso dei vert6ici della polilinea  
   """
   pointsLen = len(points)
   arcList = QadArcList()
   arcList.fromPoints(points)

   # creo una lista dei segmenti e archi che formano la polilinea
   parts = []
   i = 0
   while i < pointsLen - 1:   
      # verifico il punto i + 1 fa parte di un arco
      arcInfo = arcList.arcAt(i + 1)
      if arcInfo is not None:
         arc = arcInfo[0]
         if arc.getStartPt() != arc.getEndPt():
            # se i punti sono così vicini da essere considerati uguali         
            inverse = False if ptNear(points[i], arc.getStartPt(), 1.e-9) else True
            parts.append([arc, inverse])
         startEndVertices = arcInfo[1]
         endVertex = startEndVertices[1]
         i = endVertex
      else:
         pt1 = points[i]
         pt2 = points[i + 1]
         if pt1 != pt2: # solo se il punto iniziale è diverso da quello finale
            parts.append([pt1, pt2])
         i = i + 1

   return parts

#===============================================================================
# getPolylinePtsFromPartList
#===============================================================================
def getPolylinePtsFromPartList(parts):
   """
   la funzione ritorna una lista di punti che compone la polilinea formata da una lista di
   parti di segmenti e archi
   es. (<segmento> <arco> ...)
   dove:
   segmento = (<pt1> <pt2>)
   arco = (<QadArc> <inverse>)
   <inverse> = se True significa che il punto iniziale dell'arco deve essere 
               considerato finale nel senso dei vertici della polilinea  
   """
   # ottengo una lista di punti delle nuove polilinee
   result = []
   firstPt = True
   for part in parts:
      if type(part[0]) == QgsPoint: # segmento
         if firstPt == True:
            result.append(part[0]) 
            firstPt = False
         result.append(part[1])
      else: # arco
         arcPoints = part[0].asPolyline()
         arcPointsLen = len(arcPoints)
         if part[1] == False: # l'arco non è in senso inverso 
            if firstPt == True: 
               i = 0 
               firstPt = False
            else:
               i = 1
            while i < arcPointsLen:
               result.append(arcPoints[i])
               i = i + 1
         else: # l'arco è in senso inverso
            if firstPt == True: 
               i = arcPointsLen - 1 
               firstPt = False
            else:
               i = arcPointsLen - 2
            while i >= 0:
               result.append(arcPoints[i])
               i = i - 1
                  
   return result

#===============================================================================
# getIntersectionPtsBetweenParts_offset
#===============================================================================
def getIntersectionPtsBetweenParts_offset(part, nextPart):
   """
   la funzione calcola i punti di intersezione tra 2 parti.
   Ritorna una lista di punti di intersezione
   """
   if type(part[0]) == QgsPoint: # segmento
      if type(nextPart[0]) == QgsPoint: # segmento
         ptInt = getIntersectionPointOn2InfinityLines(part[0], part[1], nextPart[0], nextPart[1])
         if ptInt is not None: # se non sono parallele
            if isPtOnSegment(part[0], part[1], ptInt) == True:
               return [QgsPoint(ptInt)]
         else:
            # il segmento nextPart si sovrappone a part
            if isPtOnSegment(part[0], part[1], nextPart[0]) == True and \
               isPtOnSegment(part[0], part[1], nextPart[1]) == True:
               return []
            # il segmento part si sovrappone a nextPart
            if isPtOnSegment(nextPart[0], nextPart[1], part[0]) == True and \
               isPtOnSegment(nextPart[0], nextPart[1], part[1]) == True:
               return []
            if part[1] == nextPart[0] or part[1] == nextPart[1]:
               return [QgsPoint(part[1])]
            if part[0] == nextPart[0] or part[0] == nextPart[1]:
               return [QgsPoint(part[0])]            
      else: # arco
         result = []
         circle = QadCircle()
         circle.set(nextPart[0].center, nextPart[0].radius)
         ptIntList = circle.getIntersectionPointsWithline(part[0], part[1])
         for ptInt in ptIntList:
            if nextPart[0].isPtOnArc(ptInt) and isPtOnSegment(part[0], part[1], ptInt):
               result.append(QgsPoint(ptInt))      
         return result
   else: # arco
      if type(nextPart[0]) == QgsPoint: # segmento
         result = []
         circle = QadCircle()
         circle.set(part[0].center, part[0].radius)
         ptIntList = circle.getIntersectionPointsWithline(nextPart[0], nextPart[1])
         for ptInt in ptIntList:
            if part[0].isPtOnArc(ptInt) and isPtOnSegment(nextPart[0], nextPart[1], ptInt):
               result.append(QgsPoint(ptInt))      
         return result
      else: # arco
         result = []
         circle1 = QadCircle()
         circle1.set(part[0].center, part[0].radius)
         circle2 = QadCircle()
         circle2.set(nextPart[0].center, nextPart[0].radius)
         ptIntList = circle1.getIntersectionPointsWithCircle(circle2)
         for ptInt in ptIntList:
            if part[0].isPtOnArc(ptInt) and nextPart[0].isPtOnArc(ptInt):
               result.append(QgsPoint(ptInt))      
         return result
      
   return []

#===============================================================================
# getIntersectionPtsBetweenExtendedParts_offset
#===============================================================================
def getIntersectionPtsBetweenExtendedParts_offset(part, nextPart):
   """
   la funzione calcola i punti di intersezione tra 2 parti prolungate.
   Ritorna una lista di punti di intersezione
   """
   if type(part[0]) == QgsPoint: # segmento
      if type(nextPart[0]) == QgsPoint: # segmento
         ptInt = getIntersectionPointOn2InfinityLines(part[0], part[1], nextPart[0], nextPart[1])
         if ptInt is not None: # se non sono parallele
            return [QgsPoint(ptInt)]
         else:
            # il segmento nextPart si sovrappone a part
            if isPtOnSegment(part[0], part[1], nextPart[0]) == True and \
               isPtOnSegment(part[0], part[1], nextPart[1]) == True:
               return []
            # il segmento part si sovrappone a nextPart
            if isPtOnSegment(nextPart[0], nextPart[1], part[0]) == True and \
               (nextPart[0], nextPart[1], part[1]) == True:
               return []
            if part[1] == nextPart[0] or part[1] == nextPart[1]:
               return [QgsPoint(part[1])]
            if part[0] == nextPart[0] or part[0] == nextPart[1]:
               return [QgsPoint(part[0])]            
      else: # arco
         result = []
         circle = QadCircle()
         circle.set(nextPart[0].center, nextPart[0].radius)
         return circle.getIntersectionPointsWithline(part[0], part[1])
   else: # arco
      if type(nextPart[0]) == QgsPoint: # segmento
         result = []
         circle = QadCircle()
         circle.set(part[0].center, part[0].radius)
         return circle.getIntersectionPointsWithline(nextPart[0], nextPart[1])
      else: # arco
         result = []
         circle1 = QadCircle()
         circle1.set(part[0].center, part[0].radius)
         circle2 = QadCircle()
         circle2.set(nextPart[0].center, nextPart[0].radius)
         return circle1.getIntersectionPointsWithCircle(circle2)
      
   return []

#===============================================================================
# pretreatment_offset
#===============================================================================
def pretreatment_offset(partList, isClosedPolyline):
   """
   la funzione controlla le "local self intersection"> :
   se il segmento (o arco) i-esimo e il successivo hanno 2 intersezioni allora si inserisce un vertice
   nel segmento (o arco) i-esimo tra i 2 punti di intersezione.
   La funzione riceve una lista di segmenti ed archi e ritorna una nuova lista di parti
   """
   # verifico se polilinea chiusa  
   i = -1 if isClosedPolyline == True else 0   
   
   result = []
   while i < len(partList) - 1:
      if i == -1: # polilinea chiusa quindi prendo in esame l'ultimo segmento e il primo
         part = partList[len(partList) - 1]
         nextPart = partList[0]
      else:                  
         part = partList[i]
         nextPart = partList[i + 1]

      ptIntList = getIntersectionPtsBetweenParts_offset(part, nextPart)
      if len(ptIntList) == 2: # 2 punti di intersezione
         # calcolo il punto medio tra i 2 punti di intersezione in part
         if type(part[0]) == QgsPoint: # segmento
            ptMiddle = getMiddlePoint(ptIntList[0], ptIntList[1])
            result.append([part[0], ptMiddle])
            result.append([ptMiddle, part[1]])
         else: # arco
            arc1 = QadArc(part[0])
            arc2 = QadArc(part[0])
            # se i punti sono così vicini da essere considerati uguali
            if qad_utils.ptNear(part[0].getEndPt(), ptIntList[0], 1.e-9):
               ptInt = part[0].getEndPt()
            else:
               ptInt = part[0].getStartPt()
            
            angleInt = getAngleBy2Pts(part[0].center, ptInt)
            arc1.endAngle = angleInt
            arc2.startAngle = angleInt            
            result.append([arc1, part[1]])
            result.append([arc2, part[1]])
      else: # un solo punto di intersezione
         result.append(part)
      
      i = i + 1
   
   if isClosedPolyline == False: # se non è chiusa aggiungo l'ultima parte
      if len(partList) > 1:
         result.append(nextPart)   
      else:
         result.append(partList[0])   
   
   return result

#===============================================================================
# getIntersectionPointInfo_offset
#===============================================================================
def getIntersectionPointInfo_offset(part, nextPart):
   """
   la funzione restituisce il punto di intersezione tra le 2 parti e
   e il tipo di intersezione per <part> e per <nextPart>.
   Alle parti deve essere già stato fatto l'offset singolarmente:
   
   1 = TIP (True Intersection Point) se il punto di intersezione ottenuto estendendo 
   le 2 parti si trova su <part>
   
   2  = FIP  (False Intersection Point) se il punto di intersezione ottenuto estendendo
    
   le 2 parti non si trova su <part>
   3 = PFIP (Positive FIP) se il punto di intersezione è nella stessa direzione di part

   4 = NFIP (Negative FIP) se il punto di intersezione è nella direzione opposta di part
   """

   ptIntList = getIntersectionPtsBetweenExtendedParts_offset(part, nextPart)
   if len(ptIntList) == 0:
      return None
   elif len(ptIntList) == 1:
      if type(part[0]) == QgsPoint: # segmento      
         if isPtOnSegment(part[0], part[1], ptIntList[0]) == True:
            intTypePart = 1 # TIP
         else: # l'intersezione non è sul segmento (FIP)
            # se la direzione è la stessa del segmento
            if doubleNear(getAngleBy2Pts(part[0], part[1]), getAngleBy2Pts(part[0], ptIntList[0]), 1.e-9):
               intTypePart = 3 # PFIP
            else:
               intTypePart = 4 # NFIP
      else: # arco
         if part[0].isPtOnArc(ptIntList[0]) == True:
            intTypePart = 1 # TIP
         else:
            intTypePart = 2 # FIP

      if type(nextPart[0]) == QgsPoint: # segmento      
         if isPtOnSegment(nextPart[0], nextPart[1], ptIntList[0]) == True:
            intTypeNextPart = 1 # TIP
         else: # l'intersezione non è sul segmento (FIP)
            # se la direzione è la stessa del segmento
            if doubleNear(getAngleBy2Pts(nextPart[0], nextPart[1]), getAngleBy2Pts(nextPart[0], ptIntList[0]), 1.e-9):
               intTypeNextPart = 3 # PFIP
            else:
               intTypeNextPart = 4 # NFIP
      else: # arco
         if nextPart[0].isPtOnArc(ptIntList[0]) == True:
            intTypeNextPart = 1 # TIP
         else:
            intTypeNextPart = 2 # FIP

      return [ptIntList[0], intTypePart, intTypeNextPart]
   else: # 2 punti di intersezione
      # scelgo il punto più vicino al punto finale di part     
      if type(part[0]) == QgsPoint: # segmento
         if getDistance(ptIntList[0], part[1]) < getDistance(ptIntList[1], part[1]):
            ptInt = ptIntList[0]
         else:
            ptInt = ptIntList[1]

         if isPtOnSegment(part[0], part[1], ptInt) == True:
            intTypePart = 1 # TIP
         else: # l'intersezione non è sul segmento (FIP)
            # se la direzione è la stessa del segmento
            if doubleNear(getAngleBy2Pts(part[0], part[1]), getAngleBy2Pts(part[0], ptInt), 1.e-9):
               intTypePart = 3 # PFIP
            else:
               intTypePart = 4 # NFIP

         # la seconda parte è sicuramente un'arco
         if nextPart[0].isPtOnArc(ptInt) == True:
            intTypeNextPart = 1 # TIP
         else: # l'intersezione non è sull'arco (FIP)
            intTypeNextPart = 2 # FIP         

         return [ptInt, intTypePart, intTypeNextPart]
      else: # arco
         if part[1] == False: # inverse
            finalPt = part[0].getEndPt()
         else:
            finalPt = part[0].getStartPt()

         if getDistance(ptIntList[0], finalPt) < getDistance(ptIntList[1], finalPt):
            ptInt = ptIntList[0]
         else:
            ptInt = ptIntList[1]

         if part[0].isPtOnArc(ptInt) == True:
            intTypePart = 1 # TIP
         else: # l'intersezione non è sull'arco (FIP)
           intTypePart = 2 # FIP         

         if type(nextPart[0]) == QgsPoint: # segmento
            if isPtOnSegment(nextPart[0], nextPart[1], ptInt) == True:
               intTypeNextPart = 1 # TIP
            else: # l'intersezione non è sul segmento (FIP)
               # se la direzione è la stessa del segmento
               if doubleNear(getAngleBy2Pts(nextPart[0], nextPart[1]), getAngleBy2Pts(nextPart[0], ptInt), 1.e-9):
                  intTypeNextPart = 3 # PFIP
               else:
                  intTypeNextPart = 4 # NFIP
         else : # arco
            if nextPart[0].isPtOnArc(ptInt) == True:
               intTypeNextPart = 1 # TIP
            else: # l'intersezione non è sull'arco (FIP)
               intTypeNextPart = 2 # FIP
                        
         return [ptInt, intTypePart, intTypeNextPart]

#===============================================================================
# getStartPtOfPart_offset
#===============================================================================
def getStartPtOfPart_offset(part):
   """
   la funzione restituisce il punto di partenza della parte.
   dove parte può essere:
   segmento = (<pt1> <pt2>)
   oppure
   arco = (<QadArc> <inverse>)
   <inverse> = se True significa che il punto iniziale dell'arco deve essere 
               considerato finale nel senso dei vertici della polilinea     
   """
   if type(part[0]) == QgsPoint: # segmento
      return part[0]
   else: # arco
      if part[1] == False:
         return part[0].getStartPt()
      else:
         return part[0].getEndPt()

#===============================================================================
# setStartPtOfPart_offset
#===============================================================================
def setStartPtOfPart_offset(part, pt):
   """
   la funzione restituisce una nuova parte con il punto di partenza variato.
   dove parte può essere:
   segmento = (<pt1> <pt2>)
   oppure
   arco = (<QadArc> <inverse>)
   <inverse> = se True significa che il punto iniziale dell'arco deve essere 
               considerato finale nel senso dei vertici della polilinea     
   """
   if type(part[0]) == QgsPoint: # segmento
      return [pt, part[1]]
   else: # arco
      arc = QadArc(part[0])
      if part[1] == False: # inverse
         arc.setStartAngleByPt(pt)
      else:
         arc.setEndAngleByPt(pt)
      return [arc, part[1]]

#===============================================================================
# getEndPtOfPart_offset
#===============================================================================
def getEndPtOfPart_offset(part):
   """
   la funzione restituisce il punto finale della parte.
   dove parte può essere:
   segmento = (<pt1> <pt2>)
   oppure
   arco = (<QadArc> <inverse>)
   <inverse> = se True significa che il punto iniziale dell'arco deve essere 
               considerato finale nel senso dei vertici della polilinea     
   """
   if type(part[0]) == QgsPoint: # segmento
      return part[1]
   else: # arco
      if part[1] == False:
         return part[0].getEndPt()
      else:
         return part[0].getStartPt()

#===============================================================================
# setEndPtOfPart_offset
#===============================================================================
def setEndPtOfPart_offset(part, pt):
   """
   la funzione restituisce una nuova parte con il punto finale variato.
   dove parte può essere:
   segmento = (<pt1> <pt2>)
   oppure
   arco = (<QadArc> <inverse>)
   <inverse> = se True significa che il punto iniziale dell'arco deve essere 
               considerato finale nel senso dei vertici della polilinea     
   """
   if type(part[0]) == QgsPoint: # segmento
      return [part[0], pt]
   else: # arco
      arc = QadArc(part[0])
      if part[1] == False: # inverse
         arc.setEndAngleByPt(pt)
      else:
         arc.setStartAngleByPt(pt)
      return [arc, part[1]]
   

#===============================================================================
# setStartEndPtOfPart_offset
#===============================================================================
def setStartEndPtOfPart_offset(part, startPt, endPt):
   """
   la funzione restituisce una nuova parte con il punto iniziale e finale variati.
   dove parte può essere:
   segmento = (<pt1> <pt2>)
   oppure
   arco = (<QadArc> <inverse>)
   <inverse> = se True significa che il punto iniziale dell'arco deve essere 
               considerato finale nel senso dei vertici della polilinea     
   """
   if type(part[0]) == QgsPoint: # segmento
      return [startPt, endPt]
   else: # arco
      arc = QadArc(part[0])
      if part[1] == False: # inverse
         arc.setStartAngleByPt(startPt)
         arc.setEndAngleByPt(endPt)
      else:
         arc.setStartAngleByPt(endPt)
         arc.setEndAngleByPt(startPt)
      return [arc, part[1]]
   
   
#===============================================================================
# fillet2Parts_offset
#===============================================================================
def fillet2Parts_offset(part, nextPart, offSetSide, offSetDist):
   """
   la funzione raccorda 2 parti nei seguenti casi:   
   1) segmento-arco (PFIP-FIP, nessuna intersezione)
   2) arco-segmento (FIP-NFIP, nessuna intersezione)
   3) arco-arco (nessuna intersezione)
   """
   #qad_debug.breakPoint()
   # se la prima parte è un segmento      
   if type(part[0]) == QgsPoint:
      newNextPart = [part[1], part[0]]
      newPart = [nextPart[0], not nextPart[1]]
      newOffSetSide = "left" if offSetSide == "right" else "right"
      result = fillet2Parts_offset(newPart, newNextPart, newOffSetSide, offSetDist)
      return [result[0], not result[1]]
   else: # se la prima parte è un arco
      arc = part[0]
      inverse = part[1]         
      AngleProjected = getAngleBy2Pts(arc.center, getEndPtOfPart_offset(part))
      if inverse == False: # l'arco gira verso sin
         if offSetSide == "right": # l'offset era verso l'esterno
            # calcolo il punto proiettato per ri-ottenere quello originale 
            center = getPolarPointByPtAngle(arc.center, AngleProjected, arc.radius - offSetDist)
         else: # l'offset era verso l'interno
            center = getPolarPointByPtAngle(arc.center, AngleProjected, arc.radius + offSetDist)         
      else: # l'arco gira verso destra
         if offSetSide == "right": # l'offset era verso l'interno
            center = getPolarPointByPtAngle(arc.center, AngleProjected, arc.radius + offSetDist)         
         else: # l'offset era verso l'esterno
            center = getPolarPointByPtAngle(arc.center, AngleProjected, arc.radius - offSetDist)
      
   newArc = QadArc()                                                                                        
   # se il centro dell'arco di raccordo è interno all'arco di offset
   if getDistance(arc.center, center) < arc.radius:                           
      newArcInverse = inverse
      if inverse == False:
         newArc.fromStartCenterEndPts(arc.getEndPt(), \
                                      center, \
                                      getStartPtOfPart_offset(nextPart))
      else:
         newArc.fromStartCenterEndPts(getStartPtOfPart_offset(nextPart), \
                                      center, \
                                      arc.getStartPt())                        
   else: # se il centro dell'arco di raccordo è esterno all'arco di offset
      newArcInverse = not inverse
      if inverse == False:
         newArc.fromStartCenterEndPts(getStartPtOfPart_offset(nextPart), \
                                      center, \
                                      arc.getEndPt())
      else:
         newArc.fromStartCenterEndPts(arc.getStartPt(), \
                                      center, \
                                      getStartPtOfPart_offset(nextPart))
                                                            
   return [newArc, newArcInverse]                     

#===============================================================================
# getUntrimmedOffSetPartList
#===============================================================================
def getUntrimmedOffSetPartList(points, offSetDist, offSetSide, gapType, tolerance2ApproxCurve = None):
   """
   la funzione fa l'offset non pulito da eventuali tagli da apportare (vedi
   getClippedOffsetPartList") di una polilinea (lista di punti = <points>)
   secondo una distanza e un lato di offset ("right" o "left") 
   ed un modo <gapType>:
   0 = Estende i segmenti di linea alle relative intersezioni proiettate
   1 = Raccorda i segmenti di linea in corrispondenza delle relative intersezioni proiettate.
       Il raggio di ciascun segmento di arco è uguale alla distanza di offset
   2 = Cima i segmenti di linea in corrispondenza delle intersezioni proiettate.
       La distanza perpendicolare da ciascuna cima al rispettivo vertice
       sull'oggetto originale è uguale alla distanza di offset.
   tolerance2ApproxCurve = errore minimo di tolleranza
       
   La funzione ritorna una lista di parti della polilinee (lista di segmenti o archi) 
   """
   # verifico se polilinea chiusa
   isClosedPolyline = True if points[0] == points[-1] else False
   # creo una lista dei segmenti e archi che formano la polilinea
   partList = pretreatment_offset(getPartListFromPolylinePts(points), isClosedPolyline)
     
   # faccio l'offset di ogni parte della polilinea
   newPartList = []
   for part in partList:
      if type(part[0]) == QgsPoint: # segmento
         newPart = getOffSetLine(part[0], part[1], offSetDist, offSetSide)
         newPartList.append(newPart)
      else: # arco
         if part[1] == False: # l'arco gira verso sin
            arcOffSetSide = "external" if offSetSide == "right" else "internal"
         else: # l'arco gira verso destra
            arcOffSetSide = "internal" if offSetSide == "right" else "external"         
         
         newArc = getOffSetArc(part[0], offSetDist, arcOffSetSide)
         if newArc is not None:
            newPart = [newArc, part[1]] # <arco> e <inverse>
            newPartList.append(newPart)

   #qad_debug.breakPoint()

   # calcolo i punti di intersezione tra parti adiacenti
   # per ottenere una linea di offset non tagliata
   if isClosedPolyline == True:
      i = -1
   else:
      i = 0   

   untrimmedOffsetPartList = []
   while i < len(newPartList) - 1:
      if i == -1: # polylinea chiusa quindi prendo in esame l'ultimo segmento e il primo
         part = newPartList[-1] # ultima parte
         nextPart = newPartList[0]
      else:                  
         part = newPartList[i]
         nextPart = newPartList[i + 1]

      if len(untrimmedOffsetPartList) == 0:
         lastUntrimmedOffsetPt = getStartPtOfPart_offset(part)
      else:
         lastUntrimmedOffsetPt = getEndPtOfPart_offset(untrimmedOffsetPartList[-1]) # ultima parte
      
      #qad_debug.breakPoint()
      IntPointInfo = getIntersectionPointInfo_offset(part, nextPart)
      if IntPointInfo is not None: # se c'è un'intersezione
         IntPoint = IntPointInfo[0]
         IntPointTypeForPart = IntPointInfo[1]
         IntPointTypeForNextPart = IntPointInfo[2]

      if type(part[0]) == QgsPoint: # segmento
         if type(nextPart[0]) == QgsPoint: # segmento-segmento         
            if IntPointTypeForPart == 1: # TIP
               if IntPointTypeForNextPart == 1: # TIP
                  untrimmedOffsetPartList.append(setStartEndPtOfPart_offset(part, lastUntrimmedOffsetPt, IntPoint))
               else: # FIP
                  untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
                  untrimmedOffsetPartList.append([getEndPtOfPart_offset(part), \
                                                  getStartPtOfPart_offset(nextPart)])
            else: # FIP
               if IntPointTypeForPart == 3: # PFIP
                  if gapType != 0:
                     newLines = bridgeTheGapBetweenLines_offset(part, nextPart, offSetDist, gapType, tolerance2ApproxCurve)
                     # secondo punto del primo segmento                     
                     untrimmedOffsetPartList.append(setStartEndPtOfPart_offset(part, lastUntrimmedOffsetPt, newLines[0][1]))
                     untrimmedOffsetPartList.append(newLines[1]) # arco o linea di raccordo
                  else:
                     untrimmedOffsetPartList.append(setStartEndPtOfPart_offset(part, lastUntrimmedOffsetPt, IntPoint))
               else: # NFIP
                  untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
                  untrimmedOffsetPartList.append([getEndPtOfPart_offset(part), \
                                                  getStartPtOfPart_offset(nextPart)])
         else: # segmento-arco
            arc = nextPart[0]
            inverse = nextPart[1]
            if IntPointInfo is not None: # se esiste un punto di intersezione
               if IntPointTypeForPart == 1: # TIP
                  if IntPointTypeForNextPart == 1: # TIP
                     untrimmedOffsetPartList.append(setStartEndPtOfPart_offset(part, lastUntrimmedOffsetPt, IntPoint))
                  else: # FIP
                     untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
                     untrimmedOffsetPartList.append([getEndPtOfPart_offset(part), \
                                                     getStartPtOfPart_offset(nextPart)])
               else: # FIP
                  if IntPointTypeForPart == 3: # PFIP
                     if IntPointTypeForNextPart == 2: # FIP
                        #qad_debug.breakPoint()                        
                        untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
                        untrimmedOffsetPartList.append(fillet2Parts_offset(part, nextPart, offSetSide, offSetDist))               
                  else: # NFIP
                     if IntPointTypeForNextPart == 1: # TIP
                        untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
                        untrimmedOffsetPartList.append([getEndPtOfPart_offset(part), \
                                                        getStartPtOfPart_offset(nextPart)])
            else: # non esiste un punto di intersezione               
               untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
               untrimmedOffsetPartList.append(fillet2Parts_offset(part, nextPart, offSetSide, offSetDist))               
      else: # arco
         if type(nextPart[0]) == QgsPoint: # arco-segmento         
            arc = part[0]
            inverse = part[1]
            #qad_debug.breakPoint() 
            if IntPointInfo is not None: # se esiste un punto di intersezione
               if IntPointTypeForPart == 1: # TIP
                  if IntPointTypeForNextPart == 1: # TIP
                     untrimmedOffsetPartList.append(setStartEndPtOfPart_offset(part, lastUntrimmedOffsetPt, IntPoint))
                  else: # FIP
                     if IntPointTypeForNextPart == 3: # PFIP                     
                        untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
                        untrimmedOffsetPartList.append([getEndPtOfPart_offset(part), \
                                                        getStartPtOfPart_offset(nextPart)])
               else: # FIP
                  if IntPointTypeForNextPart == 4: # NFIP
                     #qad_debug.breakPoint()                        
                     untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
                     untrimmedOffsetPartList.append(fillet2Parts_offset(part, nextPart, offSetSide, offSetDist))               
                  elif IntPointTypeForNextPart == 1: # TIP
                     untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
                     untrimmedOffsetPartList.append([getEndPtOfPart_offset(part), \
                                                     getStartPtOfPart_offset(nextPart)])
            else: # non esiste un punto di intersezione
               untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
               untrimmedOffsetPartList.append(fillet2Parts_offset(part, nextPart, offSetSide, offSetDist))               
         else: # arco-arco
            arc = part[0]
            inverse = part[1]
            nextArc = nextPart[0]
            nextInverse = nextPart[1]
            #qad_debug.breakPoint() 
            if IntPointInfo is not None: # se esiste un punto di intersezione
               if IntPointTypeForPart == 1: # TIP
                  if IntPointTypeForNextPart == 1: # TIP
                     untrimmedOffsetPartList.append(setStartEndPtOfPart_offset(part, lastUntrimmedOffsetPt, IntPoint))
                  else : # FIP
                     untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
                     if inverse == False:
                        center = getPolarPointByPtAngle(arc.center, arc.endAngle, arc.radius - offSetDist)
                     else:
                        center = getPolarPointByPtAngle(arc.center, arc.startAngle, arc.radius - offSetDist)
                        
                     secondPtNewArc = getPolarPointByPtAngle(center, \
                                                             getAngleBy2Pts(center, IntPoint), \
                                                             offSetDist)                     
                     newArc = QadArc()
                     newArc.fromStartSecondEndPts(getEndPtOfPart_offset(part), \
                                                  secondPtNewArc, \
                                                  getStartPtOfPart_offset(nextPart))

                     if ptNear(newArc.getStartPt(), getEndPtOfPart_offset(part), 1.e-9):
                        untrimmedOffsetPartList.append([newArc, False])
                     else:
                        untrimmedOffsetPartList.append([newArc, True])                     
               else: # FIP
                  if IntPointTypeForNextPart == 1: # TIP
                     untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
                     if inverse == False:
                        center = getPolarPointByPtAngle(arc.center, arc.endAngle, arc.radius - offSetDist)
                     else:
                        center = getPolarPointByPtAngle(arc.center, arc.startAngle, arc.radius - offSetDist)
                        
                     secondPtNewArc = getPolarPointByPtAngle(center, \
                                                             getAngleBy2Pts(center, IntPoint), \
                                                             offSetDist)                     
                     newArc = QadArc()
                     newArc.fromStartSecondEndPts(getEndPtOfPart_offset(part), \
                                                  secondPtNewArc, \
                                                  getStartPtOfPart_offset(nextPart))
                     if ptNear(newArc.getStartPt(), getEndPtOfPart_offset(part), 1.e-9):
                        untrimmedOffsetPartList.append([newArc, False])
                     else:
                        untrimmedOffsetPartList.append([newArc, True])                     
                  else: # FIP
                     untrimmedOffsetPartList.append(setStartEndPtOfPart_offset(part, lastUntrimmedOffsetPt, IntPoint))
            else: # non esiste un punto di intersezione
               untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
               untrimmedOffsetPartList.append(fillet2Parts_offset(part, nextPart, offSetSide, offSetDist))
               
      i = i + 1

   #qad_debug.breakPoint()
   if len(newPartList) > 0:
      if isClosedPolyline == False:
         if len(untrimmedOffsetPartList) == 0:
            lastUntrimmedOffsetPt = getStartPtOfPart_offset(newPartList[0])
         else:
            lastUntrimmedOffsetPt = getEndPtOfPart_offset(untrimmedOffsetPartList[-1]) # ultima parte
            
         part = newPartList[-1]
         untrimmedOffsetPartList.append(setStartPtOfPart_offset(part, lastUntrimmedOffsetPt))
      else:
         # primo punto = ultimo punto
         newPart = setStartPtOfPart_offset(untrimmedOffsetPartList[0], getEndPtOfPart_offset(untrimmedOffsetPartList[-1]))
         del untrimmedOffsetPartList[0]
         untrimmedOffsetPartList.insert(0, newPart)

   return untrimmedOffsetPartList
   
#===============================================================================
# offSetPolyline
#===============================================================================
def offSetPolyline(points, offSetDist, offSetSide, gapType, tolerance2ApproxCurve = None):
   """
   la funzione fa l'offset di una polilinea (lista di punti = <points>)
   secondo una distanza e un lato di offset ("right" o "left") 
   ed un modo <gapType>:
   0 = Estende i segmenti di linea alle relative intersezioni proiettate
   1 = Raccorda i segmenti di linea in corrispondenza delle relative intersezioni proiettate.
       Il raggio di ciascun segmento di arco è uguale alla distanza di offset
   2 = Cima i segmenti di linea in corrispondenza delle intersezioni proiettate.
       La distanza perpendicolare da ciascuna cima al rispettivo vertice
       sull'oggetto originale è uguale alla distanza di offset.
   tolerance2ApproxCurve = errore minimo di tolleranza
       
   La funzione ritorna una lista di polilinee (lista di liste di punti) 
   """
   if tolerance2ApproxCurve is None:
      tolerance = QadVariables.get("TOLERANCE2APPROXCURVE")
   else:
      tolerance = tolerance2ApproxCurve
   
   result = []
   
   AngleToAdd = (-math.pi / 2) if offSetSide == "right" else (math.pi / 2)
   pointsLen = len(points)

   # verifico se è un cerchio
   circle = QadCircle()
   startEndVertices = circle.fromPolyline(points, 0)
   if startEndVertices is not None and \
      startEndVertices[0] == 0 and startEndVertices[1] == (pointsLen - 1):
      points = circle.asPolyline()         
      pt1 = points[0]
      angleLine = getAngleBy2Pts(pt1, points[1])

      # calcolo il primo punto proiettato
      pt1Proj = getPolarPointByPtAngle(pt1, angleLine + AngleToAdd, offSetDist)
      pt1InverseProj = getPolarPointByPtAngle(pt1, angleLine - AngleToAdd, offSetDist)
      if getDistance(pt1Proj, circle.center) > getDistance(pt1InverseProj, circle.center):
         # offset verso l'interno del cerchio
         offSetCircle = getOffSetCircle(circle, offSetDist, "internal")
      else:
         # offset verso l'esterno del cerchio
         offSetCircle = getOffSetCircle(circle, offSetDist, "external")      
      
      if offSetCircle is not None:
         result.append(offSetCircle.asPolyline(tolerance))
         
      return result
   
   #qad_debug.breakPoint()

   untrimmedOffsetPartList = getUntrimmedOffSetPartList(points, offSetDist, offSetSide, gapType, tolerance)
              
   #qad_debug.breakPoint()
      

                  
   #newLines = bridgeTheGapBetweenLines_offset(line1, line2, offSetDist, gapType, tolerance2ApproxCurve = None):
   
   # taglio gli oggetti che necessitano di essere tagliati con le parti adiacenti
   # taglio gli oggetti che necessitano di essere tagliati con altre parti (non adiacenti) in offset
   # accorpo gli oggetti che hanno punti terminali in comune
   
   newPartLists = [untrimmedOffsetPartList] # test
   # ottengo una lista di punti delle nuove polilinee
   result = []
   firstPt = True
   for newPartList in newPartLists:
      result.append(getPolylinePtsFromPartList(newPartList))
                  
   return result

#===============================================================================
# getAdjustedRubberBandVertex
#===============================================================================
def getAdjustedRubberBandVertex(vertexBefore, vertex):
   adjustedVertex = QgsPoint(vertex)
         
   # per un baco non ancora capito: se la linea ha solo 2 vertici e 
   # hanno la stessa x o y (linea orizzontale o verticale) 
   # la linea non viene disegnata perciò sposto un pochino la x o la y
   # del secondo vertice         
   if vertexBefore.x() == vertex.x():
      adjustedVertex.setX(vertex.x() + 1.e-9)
   if vertexBefore.y() == vertex.y():
      adjustedVertex.setY(vertex.y() + 1.e-9)
      
   return adjustedVertex


#===============================================================================
# ApproxCurvesOnGeom
#===============================================================================
def ApproxCurvesOnGeom(geom, atLeastNSegment = 3, tolerance2ApproxCurve = None):
   """
   ritorna una geometria le cui curve sono approssimate secondo una tolleranza di errore
   atLeastNSegment = numero minimo di segmenti per riconoscere una curva
   tolerance2ApproxCurve = errore minimo di tolleranza
   """   
   if tolerance2ApproxCurve is None:
      tolerance = QadVariables.get("TOLERANCE2APPROXCURVE")
   else:
      tolerance = tolerance2ApproxCurve
   
   g = QgsGeometry(geom) # copio la geometria
   
   #qad_debug.breakPoint()

   # verifico se ci sono archi
   arcList = QadArcList()
   arcList.fromGeom(g, atLeastNSegment)
         
   # verifico se ci sono cerchi
   circleList = QadCircleList()
   circleList.fromGeom(g, atLeastNSegment)

   beforeVertex = 1
   
   # dall'ultimo arco al primo
   for i in xrange(len(arcList.arcList) - 1, -1, -1): 
      arc = arcList.arcList[i]
      startVertex = arcList.startEndVerticesList[i][0]
      endVertex = arcList.startEndVerticesList[i][1]
      points = arc.asPolyline(tolerance)
      # inserisco i nuovi vertici saltando il primo e l'ultimo
      if arc.getStartPt() == g.vertexAt(startVertex):
         for i in xrange(len(points) - 2, 0, -1): 
            if g.insertVertex(points[i].x(), points[i].y(), endVertex) == False:
               return None
      else:
         for i in xrange(1, len(points), 1): 
            if g.insertVertex(points[i].x(), points[i].y(), endVertex) == False:
               return None
      # cancello i vecchi vertici
      for i in range(0, endVertex - startVertex - 1):
         if g.deleteVertex(startVertex + 1) == False:
            return None

   # dall'ultimo cerchio al primo
   for i in xrange(len(circleList.circleList) - 1, -1, -1): 
      circle = circleList.circleList[i]
      startVertex = circleList.startEndVerticesList[i][0]
      endVertex = circleList.startEndVerticesList[i][1]
      points = circle.asPolyline(tolerance)
      # inserisco i nuovi vertici saltando il primo e l'ultimo
      for i in xrange(len(points) - 2, 0, -1): 
         if g.insertVertex(points[i].x(), points[i].y(), endVertex) == False:
            return None
      # cancello i vecchi vertici
      for i in range(0, endVertex - startVertex - 1):
         if g.deleteVertex(startVertex + 1) == False:
            return None

   return g

#===============================================================================
# whatGeomIs
#===============================================================================
def whatGeomIs(pt, geom):
   # ritorna una tupla (<The squared cartesian distance>,
   #                    <minDistPoint>
   #                    <afterVertex>)
   dummy = qad_utils.closestSegmentWithContext(pt, geom)
   afterVertex = dummy[2]
   if afterVertex is None:
      return

   arcList = QadArcList()
   circleList = QadCircleList()

   # verifico se pt1 si riferisce ad un arco
   if arcList.fromGeom(geom) > 0:
      info = arcList.arcAt(afterVertex)
      if info is not None:
         return info[0]
      
   # verifico se pt1 si riferisce ad un cerchio
   if circleList.fromGeom(geom) > 0:
      info = circleList.circleAt(afterVertex)
      if info is not None:
         return info[0]
      
   # se non è un cerchio è una linea
   pt1 = geom.vertexAt(afterVertex - 1)
   pt2 = geom.vertexAt(afterVertex)
   return pt1, pt2


#===============================================================================
# solveApollonius
#===============================================================================
def solveApollonius(c1, c2, c3, s1, s2, s3):
   '''
   >>> solveApollonius((0, 0, 1), (4, 0, 1), (2, 4, 2), 1,1,1)
   Circle(x=2.0, y=2.1, r=3.9)
   >>> solveApollonius((0, 0, 1), (4, 0, 1), (2, 4, 2), -1,-1,-1)
   Circle(x=2.0, y=0.8333333333333333, r=1.1666666666666667) 
   Trova il cerchio tangente a tre cerchi (sarebbero 8 cerchi che si trovano con le 
   8 combinazioni di s1, s2, s3 che assumo valore -1 o 1)
   '''
   x1 = c1.center.x()
   y1 = c1.center.y()
   r1 = c1.radius
   x2 = c2.center.x()
   y2 = c2.center.y()
   r2 = c2.radius
   x3 = c3.center.x()
   y3 = c3.center.y()
   r3 = c3.radius
   
   v11 = 2*x2 - 2*x1
   v12 = 2*y2 - 2*y1
   v13 = x1*x1 - x2*x2 + y1*y1 - y2*y2 - r1*r1 + r2*r2
   v14 = 2*s2*r2 - 2*s1*r1
   
   v21 = 2*x3 - 2*x2
   v22 = 2*y3 - 2*y2
   v23 = x2*x2 - x3*x3 + y2*y2 - y3*y3 - r2*r2 + r3*r3
   v24 = 2*s3*r3 - 2*s2*r2
   
   if v11 == 0:
      return None
   
   w12 = v12/v11
   w13 = v13/v11
   w14 = v14/v11
   
   if v21-w12 == 0 or v21-w13 == 0 or v21-w14 == 0:
      return None
   
   w22 = v22/v21-w12
   w23 = v23/v21-w13
   w24 = v24/v21-w14
   
   if w22 == 0:
      return None
   
   P = -w23/w22
   Q = w24/w22
   M = -w12*P-w13
   N = w14 - w12*Q
   
   a = N*N + Q*Q - 1
   b = 2*M*N - 2*N*x1 + 2*P*Q - 2*Q*y1 + 2*s1*r1
   c = x1*x1 + M*M - 2*M*x1 + P*P + y1*y1 - 2*P*y1 - r1*r1
   
   # Find a root of a quadratic equation. This requires the circle centers not to be e.g. colinear
   if a == 0:
      return None
   D = (b * b) - (4 * a * c)
   
   # se D è così vicino a zero 
   if qad_utils.doubleNear(D, 0.0, 1.e-9):
      D = 0
   elif D < 0: # non si può fare la radice quadrata di un numero negativo
      return None
   
   rs = (-b-math.sqrt(D))/(2*a)
   
   xs = M+N*rs
   ys = P+Q*rs
   
   center = QgsPoint(xs, ys)
   circle = QadCircle()    
   circle.set(center, rs)
   return circle


#===============================================================================
# solveCircleTangentTo2LinesAndCircle
#===============================================================================
def solveCircleTangentTo2LinesAndCircle(line1, line2, circle, s1, s2):
   '''
   Trova i due cerchi tangenti a due rette e un cerchio (sarebbero 8 cerchi che si trovano con le 
   4 combinazioni di s1, s2 che assumo valore -1 o 1)
   e restituisce quello più vicino a pt
   '''
   circleList = []
   # http://www.batmath.it/matematica/a_apollonio/rrc.htm
   #qad_debug.breakPoint()

   # Questa costruzione utilizza una particolare trasformazione geometrica, che alcuni chiamano dilatazione parallela:
   # si immagina che il raggio r del cerchio dato c si riduca a zero (il cerchio è ridotto al suo centro),
   # mentre le rette rimangono parallele con distanze dal centro del cerchio che si è ridotto a zero aumentate o
   # diminuite di r. Si é così ricondotti al caso di un punto e due rette e si può applicare una delle tecniche viste
   # in quel caso.  

   line1Par = []
   angle = getAngleBy2Pts(line1[0], line1[1])
   line1Par.append(getPolarPointByPtAngle(line1[0], angle + math.pi / 2, circle.radius * s1))
   line1Par.append(getPolarPointByPtAngle(line1[1], angle + math.pi / 2, circle.radius * s1))

   line2Par = []
   angle = getAngleBy2Pts(line2[0], line2[1])
   line2Par.append(getPolarPointByPtAngle(line2[0], angle + math.pi / 2, circle.radius * s2))
   line2Par.append(getPolarPointByPtAngle(line2[1], angle + math.pi / 2, circle.radius * s2))
   
   circleTan = QadCircle()    
   circleList = circleTan.from1IntPtLineLineTanPts(circle.center, line1Par, None, line2Par, None, True)

   for circleTan in circleList:
      ptPerp = qad_utils.getPerpendicularPointOnInfinityLine(line1[0], line1[1], circleTan.center)
      circleTan.radius = getDistance(ptPerp, circleTan.center)
   
   return circleList
   

#===============================================================================
# solveCircleTangentToLineAnd2Circles
#===============================================================================
def solveCircleTangentToLineAnd2Circles(line, circle1, circle2, s1, s2):
   '''
   Trova i due cerchi tangenti a una retta e due cerchi (sarebbero 8 cerchi che si trovano con le 
   4 combinazioni di s1, s2 che assumo valore -1 o 1)
   e restituisce quello più vicino a pt
   '''
   # http://www.batmath.it/matematica/a_apollonio/rcc.htm
   #qad_debug.breakPoint()

   # Il modo più semplice per risolvere questo problema è quello di utilizzare una particolare 
   # trasformazione geometrica, che alcuni chiamano dilatazione parallela: si immagina che il raggio r 
   # del più piccolo dei cerchi in questione si riduca a zero (il cerchio è ridotto al suo centro), 
   # mentre le rette (risp. gli altri cerchi) rimangono parallele (risp. concentrici) con distanze
   # dal centro del cerchio che si è ridotto a zero (rispettivamente con raggi dei cerchi) aumentati o 
   # diminuiti di r. 
   # Se applichiamo questa trasformazione al nostro caso, riducendo a zero il raggio del cerchio più piccolo
   # (o di uno dei due se hanno lo stesso raggio) ci ritroveremo con un punto, un cerchio e una retta:
   # trovate le circonferenze passanti per il punto e tangenti alla retta e al cerchio (nel modo già noto)
   # potremo applicare la trasformazione inversa della dilatazione parallela precedente per determinare
   # le circonferenze richieste.
   if circle1.radius <= circle2.radius:
      smallerCircle = circle1
      greaterCircle = circle2
   else:
      smallerCircle = circle2
      greaterCircle = circle1
   
   linePar = []
   angle = getAngleBy2Pts(line[0], line[1])
   linePar.append(getPolarPointByPtAngle(line[0], angle + math.pi / 2, smallerCircle.radius * s1))
   linePar.append(getPolarPointByPtAngle(line[1], angle + math.pi / 2, smallerCircle.radius * s1))

   circlePar = QadCircle(greaterCircle)
   circlePar.radius = circlePar.radius + smallerCircle.radius * s1
   
   circleTan = QadCircle()
   circleList = circleTan.from1IntPtLineCircleTanPts(smallerCircle.center, linePar, None, circlePar, None, True)

   for circleTan in circleList:
      ptPerp = qad_utils.getPerpendicularPointOnInfinityLine(line[0], line[1], circleTan.center)
      circleTan.radius = getDistance(ptPerp, circleTan.center)
   
   return circleList


def getCircularInversionOfpoint(circleRef, pt):
   """
   la funzione ritorna l'inversione circolare di un punto
   """
   dist = getDistance(circleRef.center, pt)
   angle = getAngleBy2Pts(circleRef.center, pt)
   circInvDist = circleRef.radius * circleRef.radius / dist
   return getPolarPointByPtAngle(circleRef.center, angle, circInvDist)

   
def getCircularInversionOfLine(circleRef, line):
   """
   la funzione ritorna l'inversione circolare di una linea (che è un cerchio)
   """
   angleLine = getAngleBy2Pts(line[0], line[1])
   ptNearestLine = getPerpendicularPointOnInfinityLine(line[0], line[1], circleRef.center)
   dist = getDistance(circleRef.center, ptNearestLine)

   pt1 = getCircularInversionOfpoint(circleRef, ptNearestLine)

   pt = getPolarPointByPtAngle(ptNearestLine, angleLine, dist)
   pt2 = getCircularInversionOfpoint(circleRef, pt)

   pt = getPolarPointByPtAngle(ptNearestLine, angleLine + math.pi, dist)
   pt3 = getCircularInversionOfpoint(circleRef, pt)
   
   result = QadCircle()
   if result.from3Pts(pt1, pt2, pt3) == False:
      return None
   
   return result


def getCircularInversionOfCircle(circleRef, circle):
   """
   la funzione ritorna l'inversione circolare di un cerchio (che è un cerchio)
   """

   angleLine = getAngleBy2Pts(circle.center, circleRef.center)
   ptNearestLine = getPolarPointByPtAngle(circle.center, angleLine, circle.radius)
   dist = getDistance(circleRef.center, circle.center)

   pt1 = getCircularInversionOfpoint(circleRef, ptNearestLine)

   pt = getPolarPointByPtAngle(circle.center, angleLine + math.pi / 2, circle.radius)
   pt2 = getCircularInversionOfpoint(circleRef, pt)

   pt = getPolarPointByPtAngle(circle.center, angleLine - math.pi / 2, circle.radius)
   pt3 = getCircularInversionOfpoint(circleRef, pt)
   
   result = QadCircle()
   if result.from3Pts(pt1, pt2, pt3) == False:
      return None
   
   return result


#===============================================================================
# lineFrom2TanPts
#===============================================================================
def lineFrom2TanPts(geom1, pt1, geom2, pt2):
   '''
   Trova la linea tangente a 2 oggetti 
   geometria 1 di tangenza (arco o cerchio)
   punto di selezione geometria 1
   geometria 2 di tangenza (arco o cerchio)
   punto di selezione geometria 2
   '''
   #qad_debug.breakPoint()
   obj1 = whatGeomIs(pt1, geom1)
   obj2 = whatGeomIs(pt2, geom2)

   if (type(obj1) == list or type(obj1) == tuple): # se linea esco
      return None
   obj1Type = obj1.whatIs()
   if obj1Type == "ARC": # se è arco lo trasformo in cerchio
      circle1 = QadCircle()
      circle1.set(obj1.center, obj1.radius)
   else:
      circle1 = QadCircle(obj1)

   if (type(obj2) == list or type(obj2) == tuple): # se linea esco
      return None
   obj2Type = obj2.whatIs()
   if obj2Type == "ARC": # se è arco lo trasformo in cerchio
      circle2 = QadCircle()
      circle2.set(obj2.center, obj2.radius)
   else:
      circle2 = QadCircle(obj2)

   tangents = circle1.getTangentsWithCircle(circle2)
   
   if obj1Type == "ARC" or obj2Type == "ARC":
      qad_debug.breakPoint()
      # cancello le linee di tangenza che non abbiano un punto di tangenza nell'arco
      for i in xrange(len(tangents) - 1, -1, -1):         
         toDelete1 = False         
         toDelete2 = False         
         if obj1Type == "ARC":
            toDelete1 = True         
            for point in tangents[i]:
               if obj1.isPtOnArc(point) == True:
                  toDelete1 = False
         if obj2Type == "ARC":
            toDelete2 = True         
            for point in tangents[i]:
               if obj2.isPtOnArc(point) == True:
                  toDelete2 = False
                  
         if toDelete1 == True or toDelete2 == True:
            del tangents[i]      

   if len(tangents) == 0:
      return None
          
   AvgList = []
   Avg = sys.float_info.max
   for tangent in tangents:
      del AvgList[:] # svuoto la lista
      
      ptInt = getPerpendicularPointOnInfinityLine(tangent[0], tangent[1], obj1.center)
      AvgList.append(getDistance(ptInt, pt1))

      ptInt = getPerpendicularPointOnInfinityLine(tangent[0], tangent[1], obj2.center)
      AvgList.append(qad_utils.getDistance(ptInt, pt2))

      currAvg = doubleListAvg(AvgList)           
      if currAvg < Avg: # mediamente più vicino
         Avg = currAvg
         result = tangent       
               
   return result


#===============================================================================
# lineFromTanPerPts
#===============================================================================
def lineFromTanPerPts(tanGeom1, tanPt1, perGeom2, perPt2):
   '''
   Trova la linea tangente a 1 oggetto e perpendicolare ad un altro 
   geometria di tangenza (arco o cerchio)
   punto di selezione geometria di tangenza
   geometria di perpendicolarità (linea, arco o cerchio)
   punto di selezione geometria di perpendicolarità
   '''
   #qad_debug.breakPoint()
   obj1 = whatGeomIs(tanPt1, tanGeom1)
   obj2 = whatGeomIs(perPt2, perGeom2)

   if (type(obj1) == list or type(obj1) == tuple): # se linea esco
      return None
   obj1Type = obj1.whatIs()
   if obj1Type == "ARC": # se è arco lo trasformo in cerchio
      circle1 = QadCircle()
      circle1.set(obj1.center, obj1.radius)
   else:
      circle1 = QadCircle(obj1)

   if (type(obj2) == list or type(obj2) == tuple):
      obj2Type = "LINE"
   else:
      obj2Type = obj2.whatIs()
      if obj2Type == "ARC": # se è arco lo trasformo in cerchio
         circle2 = QadCircle()
         circle2.set(obj2.center, obj2.radius)
      else:
         circle2 = QadCircle(obj2)

   lines = []
   if obj2Type == "LINE":
      # linee tangenti ad un cerchio e perpendicolari ad una linea
      angle = getAngleBy2Pts(obj2[0], obj2[1])
      pt1 = getPolarPointByPtAngle(circle1.center, angle, circle1.radius)
      pt2 = getPerpendicularPointOnInfinityLine(obj2[0], obj2[1], pt1)
      if pt1 != pt2: # se la linea non passa per il centro del cerchio
         lines.append([pt1, pt2]) # primo punto tangente e secondo punto perpendicolare 
         pt1 = qad_utils.getPolarPointByPtAngle(circle1.center, angle, -1 * circle1.radius)
         pt2 = getPerpendicularPointOnInfinityLine(obj2[0], obj2[1], pt1)
         lines.append([pt1, pt2]) # primo punto tangente e secondo punto perpendicolare 
   elif obj2Type == "CIRCLE" or obj2Type == "ARC":
      # linee tangenti ad un cerchio e perpendicolari ad un cerchio
      points = circle1.getTanPoints(circle2.center)
      for point in points:
         angle = getAngleBy2Pts(circle2.center, point)
         pt1 = getPolarPointByPtAngle(circle2.center, angle, circle2.radius)         
         lines.append([point, pt1]) # primo punto tangente e secondo punto perpendicolare 
         pt1 = getPolarPointByPtAngle(circle2.center, angle, -1 * circle2.radius)         
         lines.append([point, pt1]) # primo punto tangente e secondo punto perpendicolare 

   if obj1Type == "ARC" or obj2Type == "ARC":
      # cancello le linee che non abbiano un punto nell'arco
      for i in xrange(len(lines) - 1, -1, -1):         
         toDelete1 = False         
         toDelete2 = False         
         if obj1Type == "ARC":
            toDelete1 = True         
            for point in lines[i]:
               if obj1.isPtOnArc(point) == True:
                  toDelete1 = False
         if obj2Type == "ARC":
            toDelete2 = True         
            for point in lines[i]:
               if obj2.isPtOnArc(point) == True:
                  toDelete2 = False
                  
         if toDelete1 == True or toDelete2 == True:
            del lines[i]      

   if obj2Type == "LINE":
      # cancello le linee che non abbiano un punto nel segmento
      for i in xrange(len(lines) - 1, -1, -1):         
         line = lines[i]
         # primo punto tangente e secondo punto perpendicolare 
         if isPtOnSegment(obj2[0], obj2[1], line[1]) == False:
            del lines[i]

   if len(lines) == 0:
      return None

   AvgList = []
   Avg = sys.float_info.max
   for line in lines:
      del AvgList[:] # svuoto la lista
      # primo punto tangente e secondo punto perpendicolare
      # tangente
      AvgList.append(getDistance(line[0], tanPt1))
      # perpendicolare
      AvgList.append(getDistance(line[1], perPt2))
         
      currAvg = doubleListAvg(AvgList)           
      if currAvg < Avg: # mediamente più vicino
         Avg = currAvg
         result = line       
               
   return result


#===============================================================================
# lineFrom2PerPts
#===============================================================================
def lineFrom2PerPts(geom1, pt1, geom2, pt2):
   '''
   Trova la linea perpendicolare a 2 oggetti: 
   geometria di perpendicolarità (linea, arco o cerchio)
   punto di selezione geometria di perpendicolarità
   geometria di perpendicolarità (linea, arco o cerchio)
   punto di selezione geometria di perpendicolarità
   '''
   obj1 = whatGeomIs(pt1, geom1)
   obj2 = whatGeomIs(pt2, geom2)
   
   if (type(obj1) == list or type(obj1) == tuple):
      obj1Type = "LINE"
   else:
      obj1Type = obj1.whatIs()
      if obj1Type == "ARC": # se è arco lo trasformo in cerchio
         circle1 = QadCircle()
         circle1.set(obj1.center, obj1.radius)
      else:
         circle1 = QadCircle(obj1)

   if (type(obj2) == list or type(obj2) == tuple):
      obj2Type = "LINE"
   else:
      obj2Type = obj2.whatIs()
      if obj2Type == "ARC": # se è arco lo trasformo in cerchio
         circle2 = QadCircle()
         circle2.set(obj2.center, obj2.radius)
      else:
         circle2 = QadCircle(obj2)
   
   lines = []
   if obj1Type == "LINE":
      if obj2Type == "LINE":
         # linea perpendicolare a due linee
         return None
      else:
         # linea perpendicolare ad una linea e ad un cerchio
         ptPer1 = getPerpendicularPointOnInfinityLine(obj1[0], obj1[1], circle2.center)
         angle = qad_utils.getAngleBy2Pts(circle2.center, ptPer1)
         ptPer2 = getPolarPointByPtAngle(circle2.center, angle, circle2.radius)
         if ptPer1 != ptPer2: # se la linea non è tangente nel punto ptPer2
            lines.append([ptPer1, ptPer2]) 
         ptPer2 = getPolarPointByPtAngle(circle2.center, angle, -1 * circle2.radius)
         if ptPer1 != ptPer2: # se la linea non è tangente nel punto ptPer2
            lines.append([ptPer1, ptPer2]) 
   else:
      if obj2Type == "LINE":
         # linea perpendicolare ad un cerchio e ad una linea 
         ptPer2 = getPerpendicularPointOnInfinityLine(obj2[0], obj2[1], circle1.center)
         angle = qad_utils.getAngleBy2Pts(circle1.center, ptPer2)
         ptPer1 = getPolarPointByPtAngle(circle1.center, angle, circle1.radius)
         if ptPer1 != ptPer2: # se la linea non è tangente nel punto ptPer1
            lines.append([ptPer1, ptPer2]) 
         ptPer1 = getPolarPointByPtAngle(circle1.center, angle, -1 * circle1.radius)
         if ptPer1 != ptPer2: # se la linea non è tangente nel punto ptPer1
            lines.append([ptPer1, ptPer2]) 
      else:
         perPoints1 = circle1.getIntersectionPointsWithline(circle1.center, circle2.center)
         perPoints2 = circle2.getIntersectionPointsWithline(circle1.center, circle2.center)
         for ptPer1 in perPoints1:
            for ptPer2 in perPoints2:
               if ptPer1 != ptPer2:
                  lines.append([ptPer1, ptPer2])                        

   if obj1Type == "ARC" or obj2Type == "ARC":
      # cancello le linee che non abbiano un punto nell'arco
      for i in xrange(len(lines) - 1, -1, -1):         
         toDelete1 = False         
         toDelete2 = False         
         if obj1Type == "ARC":
            toDelete1 = True         
            for point in lines[i]:
               if obj1.isPtOnArc(point) == True:
                  toDelete1 = False
         if obj2Type == "ARC":
            toDelete2 = True         
            for point in lines[i]:
               if obj2.isPtOnArc(point) == True:
                  toDelete2 = False
                  
         if toDelete1 == True or toDelete2 == True:
            del lines[i]      

   if obj1Type == "LINE" or obj2Type == "LINE":
      # cancello le linee che non abbiano un punto nell'arco
      for i in xrange(len(lines) - 1, -1, -1):         
         toDelete1 = False         
         toDelete2 = False         
         if obj1Type == "LINE":
            toDelete1 = True         
            for point in lines[i]:
               if isPtOnSegment(obj1[0], obj1[1], point) == True:
                  toDelete1 = False
         if obj2Type == "LINE":
            toDelete2 = True         
            for point in lines[i]:
               if isPtOnSegment(obj2[0], obj2[1], point) == True:
                  toDelete2 = False
                  
         if toDelete1 == True or toDelete2 == True:
            del lines[i]      
         
   if len(lines) == 0:
      return None

   AvgList = []
   Avg = sys.float_info.max
   for line in lines:
      del AvgList[:] # svuoto la lista
      AvgList.append(getDistance(line[0], pt1))
      AvgList.append(getDistance(line[1], pt2))
         
      currAvg = doubleListAvg(AvgList)           
      if currAvg < Avg: # mediamente più vicino
         Avg = currAvg
         result = line       
               
   return result
