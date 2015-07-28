# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 funzioni varie di utilità
 
                              -------------------
        begin                : 2013-05-22
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
from qgis.utils import *

import platform
import math
import sys
import string
from ctypes import *
import ConfigParser
import time


from qad_variables import *
from qad_snapper import *
from qad_msg import QadMsg
from qad_circle import *
from qad_arc import *
from qad_entity import *


# Modulo che gestisce varie funzionalità di Qad

#===============================================================================
# isNumericField
#===============================================================================
def isNumericField(field):
   """
   La funzione verifica che il campo di tipo QgsField sia numerico
   """
   fldType = field.type()
   if fldType == QVariant.Double or fldType == QVariant.LongLong or fldType == QVariant.Int or \
      fldType == QVariant.ULongLong or fldType == QVariant.UInt:
      return True
   else:
      return False


#===============================================================================
# checkUniqueNewName
#===============================================================================
def checkUniqueNewName(newName, nameList, prefix = None, suffix = None, caseSensitive = True):
   """
   La funzione verifica che il nuovo nome non esistà già nella lista <nameList>.
   Se nella lista dovesse già esistere allora aggiunge un prefisso (se <> None) o un suffisso (se <> None)
   finchè il nome non è più presnete nella lista
   """
   ok = False
   result = newName 
   while ok == False:
      ok = True
      for name in nameList:
         if caseSensitive == True:
            if name == result:
               ok = False
               break
         else:
            if name.upper() == result.upper():
               ok = False
               break
        
      if ok == True:
         return result
      if prefix is not None:
         result = prefix + result
      else:
         if suffix is not None:
            result = result + suffix
   
   return None

#===============================================================================
# wildCard2regularExpr
#===============================================================================
def wildCard2regularExpr(wildCard, ignoreCase = True):
   """
   Ritorna la conversione di una stringa con wildcards (es. "gas*")
   in forma di regular expression (es. "[g][a][s].*")
   """
   # ? -> .
   # * -> .*
   # altri caratteri -> [carattere]
   regularExpr = "" 
   for ch in wildCard:
      if ch == "?":
         regularExpr = regularExpr + "."
      elif ch == "*":
         regularExpr = regularExpr + ".*"
      else:
         if ignoreCase:
            regularExpr = regularExpr + "[" + ch.upper() + ch.lower() + "]"
         else:
            regularExpr = regularExpr + "[" + ch + "]"         

   return regularExpr


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
      if upperS == "0" or \
         upperS == QadMsg.translate("QAD", "N") or \
         upperS == QadMsg.translate("QAD", "NO") or \
         upperS == QadMsg.translate("QAD", "F") or \
         upperS == QadMsg.translate("QAD", "FALSO"): 
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
         
         angle = getAngleBy2Pts(lastPoint, currenPoint)
         coords = getPolarPointByPtAngle(lastPoint, angle, dist)     
         return QgsPoint(coords[0], coords[1])


#===============================================================================
# str2snapTypeEnum
#===============================================================================
def str2snapTypeEnum(s):
   """
   Ritorna la conversione di una stringa in una combinazione di tipi di snap
   oppure -1 se non ci sono snap indicati.
   """
   snapType = QadSnapTypeEnum.NONE
   snapTypeStrList = s.strip().split(",")
   for snapTypeStr in snapTypeStrList:
      snapTypeStr = snapTypeStr.strip().upper()
      
      # "NES" nessuno snap
      if snapTypeStr == QadMsg.translate("Snap", "NES") or snapTypeStr == "_NON":         
         return QadSnapTypeEnum.NONE
      # "FIN" punti finali di ogni segmento
      elif snapTypeStr == QadMsg.translate("Snap", "FIN") or snapTypeStr == "_END":
         snapType = snapType | QadSnapTypeEnum.END
      # "FIN_PL" punti finali dell'intera polilinea
      elif snapTypeStr == QadMsg.translate("Snap", "FIN_PL") or snapTypeStr == "_END_PL":  
         snapType = snapType | QadSnapTypeEnum.END_PLINE
      # "MED" punto medio
      elif snapTypeStr == QadMsg.translate("Snap", "MED") or snapTypeStr == "_MID":  
         snapType = snapType | QadSnapTypeEnum.MID
      # "CEN" centro (centroide)
      elif snapTypeStr == QadMsg.translate("Snap", "CEN") or snapTypeStr == "_CEN":  
         snapType = snapType | QadSnapTypeEnum.CEN
      # "NOD" oggetto punto
      elif snapTypeStr == QadMsg.translate("Snap", "NOD") or snapTypeStr == "_NOD": 
         snapType = snapType | QadSnapTypeEnum.NOD
      # "QUA" punto quadrante
      elif snapTypeStr == QadMsg.translate("Snap", "QUA") or snapTypeStr == "_QUA":
         snapType = snapType | QadSnapTypeEnum.QUA
      # "INT" intersezione
      elif snapTypeStr == QadMsg.translate("Snap", "INT") or snapTypeStr == "_INT":
         snapType = snapType | QadSnapTypeEnum.INT
      # "INS" punto di inserimento
      elif snapTypeStr == QadMsg.translate("Snap", "INS") or snapTypeStr == "_INS": 
         snapType = snapType | QadSnapTypeEnum.INS
      # "PER" punto perpendicolare
      elif snapTypeStr == QadMsg.translate("Snap", "PER") or snapTypeStr == "_PER":
         snapType = snapType | QadSnapTypeEnum.PER
      # "TAN" tangente
      elif snapTypeStr == QadMsg.translate("Snap", "TAN") or snapTypeStr == "_TAN":
         snapType = snapType | QadSnapTypeEnum.TAN
      # "VIC" punto più vicino
      elif snapTypeStr == QadMsg.translate("Snap", "VIC") or snapTypeStr == "_NEA":
         snapType = snapType | QadSnapTypeEnum.NEA
      # "APP" intersezione apparente
      elif snapTypeStr == QadMsg.translate("Snap", "APP") or snapTypeStr == "_APP":
         snapType = snapType | QadSnapTypeEnum.APP
      # "EST" Estensione
      elif snapTypeStr == QadMsg.translate("Snap", "EST") or snapTypeStr == "_EXT":
         snapType = snapType | QadSnapTypeEnum.EXT
      # "PAR" Parallelo
      elif snapTypeStr == QadMsg.translate("Snap", "PAR") or snapTypeStr == "_PAR":
         snapType = snapType | QadSnapTypeEnum.PAR         
      # se inizia per "PR" distanza progressiva
      elif string.find(snapTypeStr, QadMsg.translate("Snap", "PR")) == 0 or \
           string.find(snapTypeStr, QadMsg.translate("Snap", "_PR")) == 0:
         # la parte successiva PR può essere vuota o numerica
         if string.find(snapTypeStr, QadMsg.translate("Snap", "PR")) == 0:
            param = snapTypeStr[len(QadMsg.translate("Snap", "PR")):]
         else:
            param = snapTypeStr[len(QadMsg.translate("Snap", "_PR")):]
         if len(param) == 0 or str2float(param) is not None:
            snapType = snapType | QadSnapTypeEnum.PR
      # "EST_INT" intersezione su estensione
      elif snapTypeStr == QadMsg.translate("Snap", "EST_INT") or snapTypeStr == "_EXT_INT":
         snapType = snapType | QadSnapTypeEnum.EXT_INT
   
   return snapType if snapType != QadSnapTypeEnum.NONE else -1


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
      # se inizia per "PR" distanza progressiva
      if string.find(snapTypeStr, QadMsg.translate("Snap", "PR")) == 0 or \
         string.find(snapTypeStr, QadMsg.translate("Snap", "_PR")) == 0:
         # la parte successiva PR può essere vuota o numerica
         if string.find(snapTypeStr, QadMsg.translate("Snap", "PR")) == 0:
            param = str2float(snapTypeStr[len(QadMsg.translate("Snap", "PR")):]) # fino alla fine della stringa
         else:
            param = str2float(snapTypeStr[len(QadMsg.translate("Snap", "_PR")):]) # fino alla fine della stringa
         if param is not None:
            params.append([QadSnapTypeEnum.PR, param])         

   return params


#===============================================================================
# strip
#===============================================================================
def strip(s, stripList):
   """
   Rimuove dalla stringa <s> tutte le stringhe nella lista <stripList> che sono 
   all'inizio e anche alla fine della stringa <s>
   """
   for item in stripList:
      s = s.strip(item) # rimuovo prima e dopo
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
# toDegrees
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
   Così, ad esempio, se un angolo é più grande di 2pi viene ridotto all'angolo giusto 
   (il raffronto in gradi sarebbe da 380 a 20 gradi) o se é negativo diventa positivo
   (il raffronto in gradi sarebbe da -90 a 270 gradi)  
   """
   if angle == 0:
      return 0
   if angle > 0:
      return angle % norm
   else:
      return norm - ((-angle) % norm)


#===============================================================================
# getStrIntDecParts
#===============================================================================
def getStrIntDecParts(n):
   """
   Restituisce due stringhe rappresentanti la parte intera senza segno e la parte decimale di un numero
   """
   if type(n) == int or type(n) == float:
      nStr = str(n)
      if "." in nStr:
         parts = nStr.split(".")
         return str(abs(int(parts[0]))), parts[1]
      else:
         return n, 0
   else:
      return None
   



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
# filterFeaturesByType
#===============================================================================
def filterFeaturesByType(features, filterByGeomType):
   """
   Riceve una lista di features e la tipologia di geometria che deve essere filtrata.
   La funzine modifica la lista <features> depurandola dalle geometrie di tipo diverso
   da <filterByGeomType>.   
   Restituisce 3 liste rispettivamente di punti, linee e poligoni.
   La lista del tipo indicato dal parametro <filterByGeomType> sarà vuota, le altre
   due liste conterranno geometrie.
   """
   resultPoint = []
   resultLine = []
   resultPolygon = []

   for i in xrange(len(features) - 1, -1, -1): 
      f = features[i]
      g = f.geometry()
      geomType = g.type()
      if geomType != filterByGeomType:            
         if geomType == QGis.Point:      
            resultPoint.append(QgsGeometry(g))
         elif geomType == QGis.Line:      
            resultLine.append(QgsGeometry(g))
         elif geomType == QGis.Polygon:      
            resultPolygon.append(QgsGeometry(g))
         del features[i]

   return resultPoint, resultLine, resultPolygon
         

#===============================================================================
# filterGeomsByType
#===============================================================================
def filterGeomsByType(geoms, filterByGeomType):
   """
   Riceve una lista di geometrie e la tipologia di geometria che deve essere filtrata.
   La funzine modifica la lista <geoms> depurandola dalle geometrie di tipo diverso
   da <filterByGeomType>.   
   Restituisce 3 liste rispettivamente di punti, linee e poligoni.
   La lista del tipo indicato dal parametro <filterByGeomType> sarà vuota, le altre
   due liste conterranno geometrie.
   """
   resultPoint = []
   resultLine = []
   resultPolygon = []

   for i in xrange(len(geoms) - 1, -1, -1): 
      g = geoms[i]
      geomType = g.type()
      if geomType != filterByGeomType:            
         if geomType == QGis.Point:      
            resultPoint.append(QgsGeometry(g))
         elif geomType == QGis.Line:      
            resultLine.append(QgsGeometry(g))
         elif geomType == QGis.Polygon:      
            resultPolygon.append(QgsGeometry(g))
         del geoms[i]

   return resultPoint, resultLine, resultPolygon


#===============================================================================
# getEntSelCursor
#===============================================================================
def getEntSelCursor():
   """
   Ritorna l'immagine del cursore per la selezione di un'entità
   """
   
   size = 1 + QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")) * 2
   # <width/cols> <height/rows> <colors> <char on pixel>
   row = str(size) + " " + str(size) + " 2 1"
   xpm = [row]
   # <Colors> 
   xpm.append("  c None")
   xpm.append("+ c " + QadVariables.get(QadMsg.translate("Environment variables", "PICKBOXCOLOR")))
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
   #return QCursor(Qt.BlankCursor) roby
    
   pickBox = QadVariables.get(QadMsg.translate("Environment variables", "CURSORSIZE"))
   size = 1 + pickBox * 2
   # <width/cols> <height/rows> <colors> <char on pixel>
   row = str(size) + " " + str(size) + " 2 1"
   xpm = [row]
   # <Colors> 
   xpm.append("  c None")
   xpm.append("+ c " + QadVariables.get(QadMsg.translate("Environment variables", "PICKBOXCOLOR")))
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

   
#===============================================================================
# getFeatureRequest
#===============================================================================
def getFeatureRequest(fetchAttributes = [], fetchGeometry = True, \
                      rect = None, useIntersect = False):
   # PER ORA <fetchGeometry> NON VIENE USATO PERCHE' NON SO FARE IL CAST in QgsFeatureRequest.Flags
   # restituisce un oggetto QgsFeatureRequest per interrogare un layer
   # It can get 4 arguments, all of them are optional:
   # fetchAttributes: List of attributes which should be fetched.
   #                  None = disable fetching attributes, Empty list means that all attributes are used.
   #                  default: empty list
   # fetchGeometry: Whether geometry of the feature should be fetched. Default: True
   # rect: Spatial filter by rectangle.
   #       None = nessuna ricerca spaziale, empty rect means (QgsRectangle()), all features are fetched.
   #       Default: none
   # useIntersect: When using spatial filter, this argument says whether accurate test for intersection 
   # should be done or whether test on bounding box suffices.
   # This is needed e.g. for feature identification or selection. Default: False
      
   request = QgsFeatureRequest()
   
   #flag = QgsFeatureRequest.NoFlags
        
#    if fetchGeometry == False:
#       flag = flag | QgsFeatureRequest.NoGeometry
             
   if rect is not None:
      r = QgsRectangle(rect)
      
      # Se il rettangolo é schiacciato in verticale o in orizzontale
      # risulta una linea e la funzione fa casino, allora in questo caso lo allargo un pochino
      if doubleNear(r.xMinimum(), r.xMaximum(), 1.e-6):
         r.setXMaximum(r.xMaximum() + 1.e-6)
         r.setXMinimum(r.xMinimum() - 1.e-6)
      if doubleNear(r.yMinimum(), r.yMaximum(), 1.e-6):
         r.setYMaximum(r.yMaximum() + 1.e-6)
         r.setYMinimum(r.yMinimum() - 1.e-6)
         
      request.setFilterRect(r)

      if useIntersect == True:
         request.setFlags(QgsFeatureRequest.ExactIntersect)   

   if fetchAttributes is None:
      request.setSubsetOfAttributes([])
   else:
      if len(fetchAttributes) > 0:
         request.setSubsetOfAttributes(fetchAttributes)

   return request

   
#===============================================================================
# getEntSel
#===============================================================================
def getEntSel(point, mQgsMapTool, \
              layersToCheck = None, checkPointLayer = True, checkLineLayer = True, checkPolygonLayer = True,
              onlyBoundary = True, onlyEditableLayers = False):
   """
   dato un punto (in screen coordinates) e un QgsMapTool, 
   la funzione cerca la prima entità dentro il quadrato
   di dimensioni PICKBOX centrato sul punto <point>
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
   Tolerance = QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")) # leggo la tolleranza
   
   #QApplication.setOverrideCursor(Qt.WaitCursor)
   
   if layersToCheck is None:
      # Tutti i layer visibili visibili
      _layers = mQgsMapTool.canvas.layers()
   else:
      # solo la lista passata come parametro
      _layers = layersToCheck
      
   for layer in _layers: # ciclo sui layer
      # considero solo i layer vettoriali che sono filtrati per tipo
      if (layer.type() == QgsMapLayer.VectorLayer) and \
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
         
         featureIterator = layer.getFeatures(getFeatureRequest([], True,  selectRect, True))

         # se é un layer contenente poligoni allora verifico se considerare solo i bordi
         if onlyBoundary == False or layer.geometryType() != QGis.Polygon:
            for feature in featureIterator:
               return feature, layer, point
         else:
            # considero solo i bordi delle geometrie e non lo spazio interno dei poligoni
            for feature in featureIterator:
               # Riduco le geometrie in point o polyline
               geoms = asPointOrPolyline(feature.geometry())
               for g in geoms:
                  if g.intersects(selectRect):
                     return feature, layer, point

#          # test per usare la cache (ancora più lento...)
#          dummy, snappingResults = layer.snapWithContext(layerCoords, ToleranceInMapUnits,
#                                                         QgsSnapper.SnapToVertex if layer.geometryType() == QGis.Point else QgsSnapper.SnapToSegment)
#          if len(snappingResults) > 0:
#             featureId = snappingResults[0][1].snappedAtGeometry()
#             feature = getFeatureById(layer, featureId)
#          
#             # se é un layer contenente poligoni allora verifico se considerare solo i bordi
#             if onlyBoundary == False or layer.geometryType() != QGis.Polygon:
#                return feature, layer, point
#             else:
#                geoms = asPointOrPolyline(feature.geometry())
#                for g in geoms:
#                   if g.intersects(selectRect):
#                      return feature, layer, point
   
   #QApplication.restoreOverrideCursor()
   return None


#===============================================================================
# getFeatureById
#===============================================================================
def getFeatureById(layer, id):
   """
   Ricava una feature dal suo id.
   """
   feature = QgsFeature()
   if layer.getFeatures(QgsFeatureRequest().setFilterFid(id)).nextFeature(feature):
      return feature
   else:
      return None

   
#===============================================================================
# isGeomInPickBox
#===============================================================================
def isGeomInPickBox(point, mQgsMapTool, geom, crs = None, \
                    checkPointLayer = True, checkLineLayer = True, checkPolygonLayer = True,
                    onlyBoundary = True):
   """
   dato un punto (in screen coordinates) e un QgsMapTool, 
   la funzione verifica se la geometria é dentro il quadrato
   di dimensioni PICKBOX centrato sul punto
   geom = geometria da verificare
   crs = sistema di coordinate della geometria (se = NON significa in map coordinates)
   checkPointLayer = opzionale, considera la geometria di tipo punto
   checkLineLayer = opzionale, considera la geometria di tipo linea
   checkPolygonLayer = opzionale, considera la geometria di tipo poligono
   onlyBoundary = serve per considerare solo il bordo dei poligoni o anche il loro interno
   Restituisce True se la geometria é nel quadrato di PickBox altrimenti False 
   """   
   if geom is None:
      return False
   if checkPointLayer == False and checkLineLayer == False and checkPolygonLayer == False:
      return False
      
   Tolerance = QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")) # leggo la tolleranza
   
   # considero solo la geometria filtrata per tipo
   if ((geom.type() == QGis.Point and checkPointLayer == True) or \
       (geom.type() == QGis.Line and checkLineLayer == True) or \
       (geom.type() == QGis.Polygon and checkPolygonLayer == True)):      
      mapPoint = mQgsMapTool.toMapCoordinates(point)
      mapGeom = QgsGeometry(geom)
      if crs is not None and mQgsMapTool.canvas.mapRenderer().destinationCrs() != crs:
         # trasformo le coord della geometria in map coordinates
         coordTransform = QgsCoordinateTransform(crs, mQgsMapTool.canvas.mapRenderer().destinationCrs())          
         mapGeom.transform(coordTransform)      
         
      ToleranceInMapUnits = Tolerance * mQgsMapTool.canvas.mapRenderer().mapUnitsPerPixel()    
      selectRect = QgsRectangle(mapPoint.x() - ToleranceInMapUnits, mapPoint.y() - ToleranceInMapUnits, \
                                mapPoint.x() + ToleranceInMapUnits, mapPoint.y() + ToleranceInMapUnits)
                                           
      # se é una geometria poligono allora verifico se considerare solo i bordi
      if onlyBoundary == False or geom.type() != QGis.Polygon:
         if mapGeom.intersects(selectRect):
            return True
      else:
         # considero solo i bordi della geometria e non lo spazio interno del poligono
         # Riduco la geometria in point o polyline
         geoms = asPointOrPolyline(mapGeom)
         for g in geoms:
            if g.intersects(selectRect):
               return True
   
   return False

   
#===============================================================================
# getGeomInPickBox
#===============================================================================
def getGeomInPickBox(point, mQgsMapTool, geoms, crs = None, \
                    checkPointLayer = True, checkLineLayer = True, checkPolygonLayer = True,
                    onlyBoundary = True):
   """
   dato un punto (in screen coordinates) e un QgsMapTool, 
   la funzione cerca la prima geometria dentro il quadrato
   di dimensioni PICKBOX centrato sul punto
   geoms = lista di geometrie da verificare
   crs = sistema di coordinate della geometria (se = NON significa in map coordinates)
   checkPointLayer = opzionale, considera la geometria di tipo punto
   checkLineLayer = opzionale, considera la geometria di tipo linea
   checkPolygonLayer = opzionale, considera la geometria di tipo poligono
   onlyBoundary = serve per considerare solo il bordo dei poligoni o anche il loro interno
   Restituisce la geometria che é nel quadrato di PickBox altrimenti None 
   """   
   if geoms is None:
      return False
   for geom in geoms:
      if isGeomInPickBox(point, mQgsMapTool, geom, crs, checkPointLayer, checkLineLayer, checkPolygonLayer, onlyBoundary):
         return geom
   return None


#===============================================================================
# getActualSingleSelection
#===============================================================================
def getActualSingleSelection(layers):
   """
   la funzione cerca se esiste una sola entità selezionata tra i layer
   Restituisce un QgsFeature e il suo layer in caso di successo altrimenti None 
   """
   selFeature = []

   for layer in layers: # ciclo sui layer
      if (layer.type() == QgsMapLayer.VectorLayer):
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
      if (layer.type() == QgsMapLayer.VectorLayer):
         if layer.selectedFeaturesIds() > 0:
            layer.setSelectedFeatures(selFeatureIds)


#===============================================================================
# getSelSet
#===============================================================================
def getSelSet(mode, mQgsMapTool, points = None, \
              layersToCheck = None, checkPointLayer = True, checkLineLayer = True, checkPolygonLayer = True,
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
   
   if layersToCheck is None:
      # Tutti i layer visibili visibili
      _layers = mQgsMapTool.canvas.layers()
   else:
      # solo la lista passata come parametro
      _layers = layersToCheck
      
   for layer in _layers: # ciclo sui layer
      # considero solo i layer vettoriali che sono filtrati per tipo
      if (layer.type() == QgsMapLayer.VectorLayer) and \
          ((layer.geometryType() == QGis.Point and checkPointLayer == True) or \
           (layer.geometryType() == QGis.Line and checkLineLayer == True) or \
           (layer.geometryType() == QGis.Polygon and checkPolygonLayer == True)) and \
           (onlyEditableLayers == False or layer.isEditable()):
         provider = layer.dataProvider()  

         if mode.upper() == "X": # take all features
            # fetchAttributes, fetchGeometry, rectangle, useIntersect             
            for feature in layer.getFeatures(getFeatureRequest([], True,  None, False)):
               entity.set(layer, feature.id())
               result.addEntity(entity)
         elif mode.upper() == "C": # crossing selection
            p1 = mQgsMapTool.toLayerCoordinates(layer, points[0])
            p2 = mQgsMapTool.toLayerCoordinates(layer, points[1])
            selectRect = QgsRectangle(p1, p2)
            # Select features in rectangle
            # fetchAttributes, fetchGeometry, rectangle, useIntersect             
            for feature in layer.getFeatures(getFeatureRequest([], True, selectRect, True)):
               entity.set(layer, feature.id())
               result.addEntity(entity)
         elif mode.upper() == "W": # window selection
            p1 = mQgsMapTool.toLayerCoordinates(layer, points[0])
            p2 = mQgsMapTool.toLayerCoordinates(layer, points[1])
            selectRect = QgsRectangle(p1, p2)
            g = QgsGeometry.fromRect(selectRect)
            # Select features in rectangle
            # fetchAttributes, fetchGeometry, rectangle, useIntersect             
            for feature in layer.getFeatures(getFeatureRequest([], True, selectRect, True)):            
               # solo le feature completamente interne al rettangolo
               if g.contains(feature.geometry()):
                  entity.set(layer, feature.id())
                  result.addEntity(entity)
         elif mode.upper() == "CP": # crossing polygon
            polyline = []      
            for point in points:
               polyline.append(mQgsMapTool.toLayerCoordinates(layer, point))
            
            g = QgsGeometry.fromPolygon([polyline])
            # Select features in the polygon bounding box
            # fetchAttributes, fetchGeometry, rectangle, useIntersect             
            for feature in layer.getFeatures(getFeatureRequest([], True, g.boundingBox(), True)):            
               # solo le feature intersecanti il poligono
               if g.intersects(feature.geometry()):                     
                  entity.set(layer, feature.id())
                  result.addEntity(entity)
         elif mode.upper() == "WP": # windows polygon
            polyline = []      
            for point in points:
               polyline.append(mQgsMapTool.toLayerCoordinates(layer, point))
            
            g = QgsGeometry.fromPolygon([polyline])
            # Select features in the polygon bounding box
            # fetchAttributes, fetchGeometry, rectangle, useIntersect             
            for feature in layer.getFeatures(getFeatureRequest([], True, g.boundingBox(), True)):                       
               # solo le feature completamente interne al poligono
               if g.contains(feature.geometry()):                     
                  entity.set(layer, feature.id())
                  result.addEntity(entity)
         elif mode.upper() == "CO": # crossing object
            # points é in questo caso un QgsGeometry  
            g = QgsGeometry(points)
            if mQgsMapTool.canvas.mapRenderer().destinationCrs() != layer.crs():       
               coordTransform = QgsCoordinateTransform(mQgsMapTool.canvas.mapRenderer().destinationCrs(), \
                                                       layer.crs()) # trasformo la geometria
               g.transform(coordTransform)
                        
            # Select features in the object bounding box
            wkbType = g.wkbType()            
            if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:   
               Tolerance = QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")) # leggo la tolleranza
               ToleranceInMapUnits = QgsTolerance.toleranceInMapUnits(Tolerance, layer, \
                                                                      mQgsMapTool.canvas.mapRenderer(), \
                                                                      QgsTolerance.Pixels)
      
               pt = g.asPoint()
               selectRect = QgsRectangle(pt.x() - ToleranceInMapUnits, pt.x() - ToleranceInMapUnits, \
                                         pt.y() + ToleranceInMapUnits, pt.y() + ToleranceInMapUnits)
               # fetchAttributes, fetchGeometry, rectangle, useIntersect             
               request = getFeatureRequest([], True, selectRect, True)
            else:
               # fetchAttributes, fetchGeometry, rectangle, useIntersect             
               request = getFeatureRequest([], True, g.boundingBox(), True)
               
            # fetchAttributes, fetchGeometry, rectangle, useIntersect             
            for feature in layer.getFeatures(request):                           
               # solo le feature intersecanti l'oggetto
               if g.intersects(feature.geometry()):                     
                  entity.set(layer, feature.id())
                  result.addEntity(entity)
         elif mode.upper() == "WO": # windows object
            # points é in questo caso un QgsGeometry  
            g = QgsGeometry(points)
            if mQgsMapTool.canvas.mapRenderer().destinationCrs() != layer.crs():       
               coordTransform = QgsCoordinateTransform(mQgsMapTool.canvas.mapRenderer().destinationCrs(), \
                                                       layer.crs()) # trasformo la geometria
               g.transform(coordTransform)

            # Select features in the object bounding box
            wkbType = g.wkbType()            
            if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:   
               Tolerance = QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")) # leggo la tolleranza
               ToleranceInMapUnits = QgsTolerance.toleranceInMapUnits(Tolerance, layer, \
                                                                      mQgsMapTool.canvas.mapRenderer(), \
                                                                      QgsTolerance.Pixels)
      
               pt = g.asPoint()
               selectRect = QgsRectangle(pt.x() - ToleranceInMapUnits, pt.x() - ToleranceInMapUnits, \
                                         pt.y() + ToleranceInMapUnits, pt.y() + ToleranceInMapUnits)
               # fetchAttributes, fetchGeometry, rectangle, useIntersect             
               request = getFeatureRequest([], True, selectRect, True)
            else:
               # fetchAttributes, fetchGeometry, rectangle, useIntersect             
               request = getFeatureRequest([], True, g.boundingBox(), True)
            
            # solo le feature completamente interne all'oggetto
            for feature in layer.getFeatures(request):                           
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
            # fetchAttributes, fetchGeometry, rectangle, useIntersect             
            for feature in layer.getFeatures(getFeatureRequest([], True, g.boundingBox(), True)):                       
               # solo le feature che intersecano la polyline
               if g.intersects(feature.geometry()):                     
                  entity.set(layer, feature.id())
                  result.addEntity(entity)
            
   #QApplication.restoreOverrideCursor()
   return result
   
   
#===============================================================================
# appendUniquePointToList
#===============================================================================
def appendUniquePointToList(pointList, point):
   """
   Aggiunge un punto alla lista verificando che non sia già presente.
   Resituisce True se l'inserimento é avvenuto False se il punto c'era già.
   """
   for iPoint in pointList:
      if ptNear(iPoint, point):
         return False

   pointList.append(point)
   return True


#===============================================================================
# getIntersectionPoints
#===============================================================================
def getIntersectionPoints(geom1, geom2, checkForCurves = False):
   """
   la funzione ritorna una lista dei punti di intersezione tra le 2 geometrie.
   Purtroppo non posso usare QgsGeometry.intersection perché non usa una tolleranza
   (le geometrie spesso vengono convertite in un'altro crs 
   e poi riconvertite in quello originale perdendo precisione)
   """
   result = []
   # Riduco le geometrie in point o polyline
   geoms1 = asPointOrPolyline(geom1)
   geoms2 = asPointOrPolyline(geom2)
            
   for g1 in geoms1:
      wkbType1 = g1.wkbType()
      if wkbType1 == QGis.WKBPoint:
         pt1 = g1.asPoint()
         for g2 in geoms2:
            wkbType2 = g2.wkbType()
            if wkbType2 == QGis.WKBPoint:
               if ptNear(pt1, g2.asPoint()):
                  appendUniquePointToList(result, pt1)
            elif wkbType2 == QGis.WKBLineString:
               points2 = g2.asPolyline()
               p2Start = points2[0]
               for i in xrange(1, len(points2), 1):
                  p2End = points2[i]                  
                  if isPtOnSegment(p2Start, p2End, pt1):
                     appendUniquePointToList(result, pt1)
                     break
                  p2Start = p2End
      elif wkbType1 == QGis.WKBLineString:
         points1 = g1.asPolyline()
         p1Start = points1[0]
         for i in xrange(1, len(points1), 1):
            p1End = points1[i]            
            for g2 in geoms2:
               wkbType2 = g2.wkbType()
               if wkbType2 == QGis.WKBPoint:
                  pt2 = g2.asPoint()
                  if isPtOnSegment(p1Start, p1End, pt2):
                     appendUniquePointToList(result, pt2)
               elif wkbType2 == QGis.WKBLineString:
                  points2 = g2.asPolyline()
                  p2Start = points2[0]
                  for i in xrange(1, len(points2), 1):
                     p2End = points2[i]                  
                     intPt = getIntersectionPointOn2Segments(p1Start, p1End,p2Start, p2End)                     
                     if intPt is not None:
                        appendUniquePointToList(result, intPt)
                     p2Start = p2End
                     
            p1Start = p1End            
            
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
         # se ci sono punti di intersezione
         if len(getIntersectionPoints(geomSegment, geomPtStart)) > 0:
            found = True
            break            
      if found == False:
         continue        

      # cerco il segmento che contiene il punto finale
      found = False
      for segmentEnd in xrange(0, totalSegment, 1):
         geomSegment = QgsGeometry.fromPolyline([points[segmentEnd], points[segmentEnd + 1]])
         # se ci sono punti di intersezione
         if len(getIntersectionPoints(geomSegment, geomPtEnd)) > 0:
            found = True
            break            
      if found == False:
         continue        
            
      if isPolygon == False:
         # trovata la polilinea che contiene il punto iniziale e finale
         result = [ptStart]
         if segmentStart < segmentEnd:
            # se il punto ptStart é uguale al punto iniziale del segmento successivo            
            if ptStart == points[segmentStart + 1]:
               segmentStart = segmentStart + 1
            
            for i in xrange(segmentStart + 1, segmentEnd + 1, 1):
               result.append(points[i])
                  
         elif segmentStart > segmentEnd:
            # se il punto ptEnd é uguale al punto finale del segmento            
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
         # Se é un poligono devo verificare il percorso più corto da ptStart e ptEnd
         
         # seguo il senso dei vertici
         result1 = [ptStart]         
         # se il punto ptStart é uguale al punto iniziale del segmento successivo
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
         # se il punto ptEnd é uguale al punto finale del segmento 
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


#===============================================================================
# getPerpendicularPointOnInfinityLine
#===============================================================================
def getPerpendicularPointOnInfinityLine(p1, p2, pt):
   """
   la funzione ritorna il punto di proiezione perpendicolare di pt 
   alla linea passante per p1-p2.
   """
   
   diffX = p2.x() - p1.x()
   diffY = p2.y() - p1.y()
                          
   if doubleNear(diffX, 0): # se la retta passante per p1 e p2 é verticale
      return QgsPoint(p1.x(), pt.y())
   elif doubleNear(diffY, 0): # se la retta passante per p1 e p2 é orizzontale
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
   ptMiddle = getMiddlePoint(pt1, pt2)
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
   dato un angolo definito da 3 punti il cui secondo punto é vertice dell'angolo,
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
                          
   if doubleNear(diffX, 0): # se la retta passante per p1 e p2 é verticale
      return p1.x()
   elif doubleNear(diffY, 0): # se la retta passante per p1 e p2 é orizzontale
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
                          
   if doubleNear(diffX, 0): # se la retta passante per p1 e p2 é verticale
      return None # infiniti punti
   elif doubleNear(diffY, 0): # se la retta passante per p1 e p2 é orizzontale
      return p1.y()
   else:
      coeff = diffY / diffX
      return p1.y() + (x - p1.x()) * coeff


#===============================================================================
# getSqrDistance
#===============================================================================
def getSqrDistance(p1, p2):
   """
   la funzione ritorna la distanza al quadrato tra 2 punti (QgsPoint)
   """
   dx = p2.x() - p1.x()
   dy = p2.y() - p1.y()
   
   return dx * dx + dy * dy


#===============================================================================
# getDistance
#===============================================================================
def getDistance(p1, p2):
   """
   la funzione ritorna la distanza tra 2 punti (QgsPoint)
   """
   return math.sqrt(getSqrDistance(p1, p2))


#===============================================================================
# getMinDistancePtBetweenSegmentAndPt
#===============================================================================
def getMinDistancePtBetweenSegmentAndPt(p1, p2, pt):
   """
   la funzione ritorna il punto di distanza minima e la distanza minima tra un segmento ed un punto
   (<punto di distanza minima><distanza minima>)
   """
   if isPtOnSegment(p1, p2, pt) == True:
      return [pt, 0]
   perpPt = getPerpendicularPointOnInfinityLine(p1, p2, pt)
   if perpPt is not None:
      if isPtOnSegment(p1, p2, perpPt) == True:
         return [perpPt, getDistance(perpPt, pt)]

   distFromP1 = getDistance(p1, pt)
   distFromP2 = getDistance(p2, pt)
   if distFromP1 < distFromP2:
      return [p1, distFromP1]
   else:
      return [p2, distFromP2]


#===============================================================================
# getMinDistancePtBetweenArcAndPt
#===============================================================================
def getMinDistancePtBetweenArcAndPt(arc, pt):
   """
   la funzione ritorna il punto di distanza minima e la distanza minima tra un arco ed un punto
   (<punto di distanza minima><distanza minima>)
   """
   angle = getAngleBy2Pts(arc.center, pt)
   if isAngleBetweenAngles(arc.startAngle, arc.endAngle, angle) == True:
      return [getPolarPointByPtAngle(arc.center, angle, arc.radius), \
              math.fabs(getDistance(arc.center, pt) - arc.radius)]

   ptStart = arc.getStartPt()
   ptEnd = arc.getEndPt()
   distFromStartPt = getDistance(ptStart, pt)
   distFromEndPt = getDistance(ptEnd, pt)
   if distFromStartPt < distFromEndPt:
      return [ptStart, distFromStartPt]
   else:
      return [ptEnd, distFromEndPt]


#===============================================================================
# getMinDistancePtsBetween2Segments
#===============================================================================
def getMinDistancePtsBetween2Segments(line1P1, line1P2, line2P1, line2P2):
   """
   la funzione ritorna i punti di distanza minima e la distanza minima tra due segmenti
   (<punto di distanza minima sul segmento1><punto di distanza minima sul segmento2><distanza minima>)
   """
   intPt = getIntersectionPointOn2Segments(line1P1, line1P2, line2P1, line2P2)
   if intPt is not None:
      return [intPt, intPt, 0]

   # ritorna una lista: (<punto di distanza minima><distanza minima>)
   bestResult = getMinDistancePtBetweenSegmentAndPt(line2P1, line2P2, line1P1)
   bestResult.insert(0, line1P1)
   resultLine1P2 = getMinDistancePtBetweenSegmentAndPt(line2P1, line2P2, line1P2)
   resultLine1P2.insert(0, line1P2)
   if bestResult[2] > resultLine1P2[2]:
      bestResult = resultLine1P2   
   resultLine2P1 = getMinDistancePtBetweenSegmentAndPt(line1P1, line1P2, line2P1)
   resultLine2P1.insert(1, line2P1)
   if bestResult[2] > resultLine2P1[2]:
      bestResult = resultLine2P1   
   resultLine2P2 = getMinDistancePtBetweenSegmentAndPt(line1P1, line1P2, line2P2)
   resultLine2P2.insert(1, line2P2)
   if bestResult[2] > resultLine2P2[2]:
      bestResult = resultLine2P2
   return bestResult
   

#===============================================================================
# getMinDistancePtsBetweenSegmentAndArc
#===============================================================================
def getMinDistancePtsBetweenSegmentAndArc(p1, p2, arc):
   """
   la funzione ritorna i punti di distanza minima e la distanza minima tra un segmento ed un arco
   (<punto di distanza minima sul segmento><punto di distanza minima sull'arco><distanza minima>)
   """  
   intPtList = arc.getIntersectionPointsWithSegment(p1, p2)
   if len(intPtList) > 0:
      return [intPtList[0], intPtList[0], 0]

   # ritorna una lista: (<punto di distanza minima><distanza minima>)
   resultP1 = getMinDistancePtBetweenArcAndPt(arc, p1)   
   resultP2 = getMinDistancePtBetweenArcAndPt(arc, p2)
   # se il segmento é interno al cerchio orginato dall'estensione dell'arco
   if getDistance(p1, arc.center) < arc.radius and \
      getDistance(p2, arc.center) < arc.radius:
      if resultP1[1] < resultP2[1]:
         return [p1, resultP1[0], resultP1[1]]
      else:
         return [p2, resultP2[0], resultP2[1]]
   # se il segmento é esterno al cerchio orginato dall'estensione dell'arco
   else:
      perpPt = getPerpendicularPointOnInfinityLine(p1, p2, arc.center)
      angle = getAngleBy2Pts(arc.center, perpPt)
      # il punto di perpendicolare alla linea infinita p1,p2 é sul segmento e sull'arco
      if isPtOnSegment(p1, p2, perpPt) == True and \
         isAngleBetweenAngles(arc.startAngle, arc.endAngle, angle) == True:
         ptOnArc = getPolarPointByPtAngle(arc.center, angle, arc.radius)
         return [perpPt, ptOnArc, getDistance(perpPt, ptOnArc)]
      
      bestResult = resultP1
      bestResult.insert(0, p1)
      resultP2.insert(0, p2)
      if bestResult[2] > resultP2[2]:
         bestResult = resultP2   

      ptStart = arc.getStartPt()
      ptEnd = arc.getEndPt()     
      
      # ritorna una lista: (<punto di distanza minima><distanza minima>)      
      resultStartPt = getMinDistancePtBetweenSegmentAndPt(p1, p2, ptStart)
      resultStartPt.insert(1, ptStart)   
      if bestResult[2] > resultStartPt[2]:
         bestResult = resultStartPt   
      resultEndPt = getMinDistancePtBetweenSegmentAndPt(p1, p2, ptEnd)
      resultEndPt.insert(1, ptEnd)
      if bestResult[2] > resultEndPt[2]:
         bestResult = resultEndPt   
      return bestResult
   

#===============================================================================
# getMinDistancePtsBetween2Arcs
#===============================================================================
def getMinDistancePtsBetween2Arcs(arc1, arc2):
   """
   la funzione ritorna i punti di distanza minima e la distanza minima tra due archi
   (<punto di distanza minima sull'arco1><punto di distanza minima sull'arco2><distanza minima>)
   """  
   intPtList = arc1.getIntersectionPointsWithArc(arc2)
   if len(intPtList) > 0:
      return [intPtList[0], intPtList[0], 0]
   
   StartPtArc1 = arc1.getStartPt()
   EndPtArc1 = arc1.getEndPt()     
   StartPtArc2 = arc2.getStartPt()
   EndPtArc2 = arc2.getEndPt()     
   
   # calcolo la minima distanza tra gli estremi di un arco e l'altro arco e 
   # scelgo la migliore tra le quattro distanze
   # ritorna una lista: (<punto di distanza minima><distanza minima>)
   bestResult = getMinDistancePtBetweenArcAndPt(arc2, StartPtArc1)   
   bestResult.insert(0, StartPtArc1)
   
   resultArc2_EndPtArc1 = getMinDistancePtBetweenArcAndPt(arc2, EndPtArc1)
   resultArc2_EndPtArc1.insert(0, EndPtArc1)
   if bestResult[2] > resultArc2_EndPtArc1[2]:
      bestResult = resultArc2_EndPtArc1
         
   resultArc1_StartPtArc2 = getMinDistancePtBetweenArcAndPt(arc1, StartPtArc2)
   resultArc1_StartPtArc2.insert(0, EndPtArc2)
   if bestResult[2] > resultArc1_StartPtArc2[2]:
      bestResult = resultArc1_StartPtArc2
         
   resultArc1_EndPtArc2 = getMinDistancePtBetweenArcAndPt(arc1, EndPtArc2)
   resultArc1_EndPtArc2.insert(0, EndPtArc2)
   if bestResult[2] > resultArc1_EndPtArc2[2]:
      bestResult = resultArc1_EndPtArc2   

   # il cerchio1 e il cerchio 2 sono derivati rispettivamente dall'estensione dell'arco1 e arco2.
   circle1 = QadCircle()
   circle1.set(arc1.center, arc1.radius)
   circle2 = QadCircle()
   circle2.set(arc2.center, arc2.radius)
   distanceBetweenCenters = getDistance(circle1.center, circle2.center)
   
   # considero i seguenti 2 casi:
   # i cerchi sono esterni
   if distanceBetweenCenters - circle1.radius - circle2.radius > 0:
      # creo un segmento che unisce i due centri e lo interseco con l'arco 1
      intPtListArc1 = arc1.getIntersectionPointsWithSegment(arc1.center, arc2.center)
      if len(intPtListArc1) > 0:
         intPtArc1 = intPtListArc1[0]
      
         # creo un segmento che unisce i due centri e lo interseco con l'arco 2
         intPtListArc2 = arc2.getIntersectionPointsWithSegment(arc1.center, arc2.center)
         if len(intPtListArc2) > 0:
            intPtArc2 = intPtListArc2[0]
            
            distanceIntPts = getDistance(intPtArc1, intPtArc2)
            if bestResult[2] > distanceIntPts:
               bestResult = [intPtArc1, intPtArc2, distanceIntPts]                    
   # il cerchio1 é interno al cerchio2 oppure
   # il cerchio2 é interno al cerchio1
   elif distanceBetweenCenters + circle1.radius < circle2.radius or \
        distanceBetweenCenters + circle2.radius < circle1.radius:
      # creo un segmento che unisce i due centri e lo interseco con l'arco 2
      intPtListArc2 = arc2.getIntersectionPointsWithInfinityLine(arc1.center, arc2.center)
      if len(intPtListArc2) > 0:
         # creo un segmento che unisce i due centri e lo interseco con l'arco 1
         intPtListArc1 = arc1.getIntersectionPointsWithInfinityLine(arc1.center, arc2.center)

         for intPtArc2 in intPtListArc2:
            for intPtArc1 in intPtListArc1:
               distanceIntPts = getDistance(intPtArc2, intPtArc1)
               if bestResult[2] > distanceIntPts:
                  bestResult = [intPtArc1, intPtArc2, distanceIntPts]                                         

   return bestResult


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
   if doubleNear(diffX, 0): # se la retta passante per p1 e p2 é verticale
      if p1.y() < p2.y():
         angle = math.pi / 2
      else :
         angle = math.pi * 3 / 2
   elif doubleNear(diffY, 0): # se la retta passante per p1 e p2 é orizzontale
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
# getAngleBy3Pts
#===============================================================================
def getAngleBy3Pts(p1, vertex, p2, clockWise):
   """
   la funzione ritorna l'angolo in radianti dell'angolo che parte da <p1> 
   per arrivare a <p2> con vertice <vertex> nella direzione <clockWise> (oraria o antioraria)
   """
   angle1 = getAngleBy2Pts(p1, vertex)   
   angle2 = getAngleBy2Pts(p2, vertex)
   if clockWise: # senso orario
      if angle2 > angle1:
         return (2 * math.pi) - (angle2 - angle1)      
      else:
         return angle1 - angle2      
   else: # senso anti-orario
      if angle2 < angle1:
         return (2 * math.pi) - (angle1 - angle2)      
      else:
         return angle2 - angle1


#===============================================================================
# isAngleBetweenAngles
#===============================================================================
def isAngleBetweenAngles(startAngle, endAngle, angle):
   """
   la funzione ritorna True se l'angolo si trova entro l'angolo di partenza e quello finale
   estremi compresi
   """
   _angle = angle % (math.pi * 2) # modulo
   if _angle < 0:
      _angle = (math.pi * 2) - _angle
      
   if startAngle < endAngle:
      if (_angle > startAngle or doubleNear(_angle, startAngle)) and \
         (_angle < endAngle or doubleNear(_angle, endAngle)):
         return True      
   else:
      if (_angle > 0 or doubleNear(_angle, 0)) and \
         (_angle < endAngle or doubleNear(_angle, endAngle)):
         return True      

      if (_angle < (math.pi * 2) or doubleNear(_angle, (math.pi * 2))) and \
         (_angle > startAngle or doubleNear(_angle, startAngle)):
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
   la funzione ritorna true se il punto é sul segmento (estremi compresi).
   p1, p2 e point sono QgsPoint.
   """
   if p1.x() < p2.x():
      xMin = p1.x()
      xMax = p2.x()
   else:
      xMax = p1.x()
      xMin = p2.x()
      
   if p1.y() < p2.y():
      yMin = p1.y()
      yMax = p2.y()
   else:
      yMax = p1.y()
      yMin = p2.y()

   y = getYOnInfinityLine(p1, p2, point.x())
   if y is None: # il segmento p1-p2 é verticale
      if (doubleNear(point.x(), xMin)) and \
         (point.y() < yMax or doubleNear(point.y(), yMax)) and \
         (point.y() > yMin or doubleNear(point.y(), yMin)):
         return True
   else:
      # se il punto é sulla linea infinita che passa da p1-p2
      if doubleNear(point.y(), y):
         # se la coordinata x é compresa nel segmento
         if (point.x() > xMin or doubleNear(point.x(), xMin)) and \
            (point.x() < xMax or doubleNear(point.x(), xMax)):
            return True
         
   return False  


#===============================================================================
# isPtOnInfinityLine
#===============================================================================
def isPtOnInfinityLine(lineP1, lineP2, point):
   """
   la funzione ritorna true se il punto é sul segmento (estremi compresi).
   p1, p2 e point sono QgsPoint.
   """
   y = getYOnInfinityLine(lineP1, lineP2, point.x())
   if y is None: # la linea infinita lineP1-lineP2 é verticale
      if doubleNear(point.x(), lineP1.x()):
         return True
   else:
      # se il punto é sulla linea infinita che passa da p1-p2
      if doubleNear(point.y(), y):
         return True
         
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
   
   if doubleNear(line1DiffX, 0) and doubleNear(line2DiffX, 0): # se la retta1 e la retta2 sono verticale
      return None # sono parallele
   elif doubleNear(line1DiffY, 0) and doubleNear(line2DiffY, 0): # se la retta1 e la retta2 sono orizzonatali
      return None # sono parallele

   if doubleNear(line1DiffX, 0): # se la retta1 é verticale
      return QgsPoint(line1P2.x(), getYOnInfinityLine(line2P1, line2P2, line1P2.x()))
   if doubleNear(line1DiffY, 0): # se la retta1 é orizzontale
      return QgsPoint(getXOnInfinityLine(line2P1, line2P2, line1P2.y()), line1P2.y())
   if doubleNear(line2DiffX, 0): # se la retta2 é verticale
      return QgsPoint(line2P2.x(), getYOnInfinityLine(line1P1, line1P2, line2P2.x()))
   if doubleNear(line2DiffY, 0): # se la retta2 é orizzontale
      return QgsPoint(getXOnInfinityLine(line1P1, line1P2, line2P2.y()), line2P2.y())

   line1Coeff = line1DiffY / line1DiffX
   line2Coeff = line2DiffY / line2DiffX

   if line1Coeff == line2Coeff: # sono parallele
      return None
     
   D = line1Coeff - line2Coeff
   # se D é così vicino a zero 
   if doubleNear(D, 0.0):
      return None   
   x = line1P1.x() * line1Coeff - line1P1.y() - line2P1.x() * line2Coeff + line2P1.y()
   x = x / D
   y = (x - line1P1.x()) * line1Coeff + line1P1.y()
   
   return QgsPoint(x, y)


#===============================================================================
# getIntersectionPointOn2Segments
#===============================================================================
def getIntersectionPointOn2Segments(line1P1, line1P2, line2P1, line2P2):
   """
   la funzione ritorna il punto di intersezione tra il segmento1 avente come estremi line1P1-line1P2 e
    il segmento2 avente come estremi line2P1-line2P2.
   """
   ptInt = getIntersectionPointOn2InfinityLines(line1P1, line1P2, line2P1, line2P2)
   if ptInt is not None: # se non sono parallele
      # se il punto di intersezione é sui segmenti
      if isPtOnSegment(line1P1, line1P2, ptInt) and isPtOnSegment(line2P1, line2P2, ptInt):
         return QgsPoint(ptInt)
   else:
      # il segmento line2 si sovrappone a line1
      if isPtOnSegment(line1P1, line1P2, line2P1) == True and \
         isPtOnSegment(line1P1, line1P2, line2P2) == True:
         return None
      # il segmento line1 si sovrappone a line2
      if isPtOnSegment(line2P1, line2P2, line1P1) == True and \
         isPtOnSegment(line2P1, line2P2, line1P2) == True:
         return None
      # se il punto iniziale di line1 coincide con il punto iniziale o finale di line2
      if line1P1 == line2P1 or line1P1 == line2P2:
         return QgsPoint(line1P1)            
      # se il punto finale di line1 coincide con il punto iniziale o finale di line2
      if line1P2 == line2P1 or line1P2 == line2P2:
         return QgsPoint(line1P2)

   return None


#===============================================================================
# getNearestPoints
#===============================================================================
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


#===============================================================================
# getPolarPointByPtAngle
#===============================================================================
def getPolarPointByPtAngle(p1, angle, dist):
   """
   la funzione ritorna il punto sulla retta passante per p1 con angolo <angle> che
   dista da p1 <dist>.
   """
   y = dist * math.sin(angle)
   x = dist * math.cos(angle)
   return QgsPoint(p1.x() + x, p1.y() + y)


#===============================================================================
# asPointOrPolyline
#===============================================================================
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


#===============================================================================
# leftOfLineCoords
#===============================================================================
def leftOfLineCoords(x, y, x1, y1, x2, y2):
   """
   la funzione ritorna una numero < 0 se il punto x,y é alla sinistra della linea x1,y1 -> x2,y2
   """
   f1 = x - x1
   f2 = y2 - y1
   f3 = y - y1
   f4 = x2 - x1
   return f1*f2 - f3*f4

def leftOfLine(pt, pt1, pt2):
   return leftOfLineCoords(pt.x(), pt.y(), pt1.x(), pt1.y(), pt2.x(), pt2.y())


#===============================================================================
# ptNear
#===============================================================================
def ptNear(pt1, pt2, tolerance = 1.e-9):
   """
   la funzione compara 2 punti (ma permette una tolleranza)
   """
   return getDistance(pt1, pt2) <= tolerance


#===============================================================================
# doubleNear
#===============================================================================
def doubleNear(a, b, tolerance = 1.e-9):
   """
   la funzione compara 2 float (ma permette una tolleranza)
   """
   diff = a - b
   return diff > -tolerance and diff <= tolerance


#===============================================================================
# doubleGreater
#===============================================================================
def doubleGreater(a, b, tolerance = 1.e-9):
   """
   la funzione compara 2 float (ma permette una tolleranza)
   """
   return a > b and not doubleNear(a, b, tolerance)


#===============================================================================
# doubleSmaller
#===============================================================================
def doubleSmaller(a, b, tolerance = 1.e-9):
   """
   la funzione compara 2 float (ma permette una tolleranza)
   """
   return a < b and not doubleNear(a, b, tolerance)


#===============================================================================
# TanDirectionNear
#===============================================================================
def TanDirectionNear(a, b, tolerance = 1.e-9):
   """
   la funzione compara 2 direzini di tangenti (ma permette una tolleranza)
   """
   if doubleNear(a, b):
      return True
   arc = QadArc()
   arc.set(QgsPoint(0,0), 1, a, b)
   if arc.totalAngle() <= tolerance:
      return True
   else:
      arc.set(QgsPoint(0,0), 1, b, a)
      return arc.totalAngle() <= tolerance


#===============================================================================
# numericListAvg
#===============================================================================
def numericListAvg(dblList):
   """
   la funzione calcola la media di una lista di numeri
   """
   if (dblList is None) or len(dblList) == 0:
      return None
   sum = 0
   for num in dblList:
      sum = sum + num
      
   return sum / len(dblList)


#===============================================================================
# sqrDistToSegment
#===============================================================================
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
# sqrDistToArc
#===============================================================================
def sqrDistToArc(point, arc):
   """
   la funzione ritorna una lista con 
   (<minima distanza al quadrato>
    <punto più vicino>)
   """   
   minDistPoint = QgsPoint()
   angle = getAngleBy2Pts(arc.center, point)
   if isAngleBetweenAngles(arc.startAngle, arc.endAngle, angle):
      distFromArc = getDistance(arc.center, point) - arc.radius
      return (distFromArc * distFromArc, getPolarPointByPtAngle(arc.center, angle, arc.radius))
   else:      
      startPt = arc.getStartPt()
      endPt = arc.getEndPt()
      distFromStartPt = getSqrDistance(startPt, point)
      distFromEndPt = getSqrDistance(endPt, point)
      if distFromStartPt < distFromEndPt:
         return (distFromStartPt, startPt)
      else:
         return (distFromEndPt, endPt)


#===============================================================================
# closestSegmentWithContext
#===============================================================================
def closestSegmentWithContext(point, geom, epsilon = 1.e-15):
   """
   la funzione ritorna una lista con 
   (<minima distanza al quadrato>
    <punto più vicino>
    <indice vertice successivo del segmento più vicino (nel caso la geom fosse linea o poligono)>
    <"a sinistra di" se il punto é alla sinista del segmento (< 0 -> sinistra, > 0 -> destra)
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
# getBoundingPtsOnOnInfinityLine
#===============================================================================
def getBoundingPtsOnOnInfinityLine(linePt1, linePt2, pts):
   """
   Data una linea infinita passante per <linePt1> e <linePt2> e una lista di punti <pts> non ordinati sulla linea,
   la funzione ritorna i due punti estremi al fascio di punti (i due punti più lontani tra di loro).
   """
   tot = len(pts)
   if tot < 3:
      return pts[:] # copio la lista
   
   result = []  
   # elaboro i tratti intermedi
   # calcolo la direzione dal primo punto al secondo punto  
   angle = getAngleBy2Pts(pts[0], pts[1]) 
   # ciclo su tutti i punti considerando solo quelli che hanno la stessa direzione con il punto precedente (boundingPt1)
   i = 2
   boundingPt1 = pts[1]
   while i < tot:
      pt2 = pts[i]
      if TanDirectionNear(angle, getAngleBy2Pts(boundingPt1, pt2)):
         boundingPt1 = pt2
      i = i + 1

   # calcolo la direzione dal secondo punto al primo punto  
   angle = getAngleBy2Pts(pts[1], pts[0]) 
   # ciclo su tutti i punti considerando solo quelli che hanno la stessa direzione con il punto precedente (boundingPt2)
   i = 2
   boundingPt2 = pts[0]
   while i < tot:
      pt2 = pts[i]
      if TanDirectionNear(angle, getAngleBy2Pts(boundingPt2, pt2)):
         boundingPt2 = pt2
      i = i + 1

   return [QgsPoint(boundingPt1), QgsPoint(boundingPt2)]


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
   la funzione sposta un punto QgsPoint secondo un offset X e uno Y
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
# extendQgsGeometry
#===============================================================================
def extendQgsGeometry(layer, geom, pt, limitEntitySet, edgeMode, tolerance2ApproxCurve):
   """
   la funzione estende la geometria (lineare) nella parte iniziale o finale fino ad
   incontrare l'oggetto più vicino nel gruppo <limitEntitySet> secondo la modalità <edgeMode>.
   <layer> = layer della geometria da estendere
   <geom> = geometria da estendere
   <pt> = punto che indica il sotto-oggetto grafico (se si tratta di WKBMultiLineString)
          e la parte di quell'oggetto che deve essere estesa
   <QadEntitySet> = gruppo di entità che serve da limite di estensione
   <edgeMode> se = 0 si deve estendere la geometria fino ad incontrare l'oggetto più vicino
              se = 1 si deve estendere la geometria fino ad incontrare l'oggetto più vicino o 
              anche il suo prolungamento
   <tolerance2ApproxCurve> = tolleranza di approssimazione per le curve
   """
   if geom is None:
      return None

   wkbType = geom.wkbType()
   
   if wkbType != QGis.WKBLineString and wkbType != QGis.WKBMultiLineString:
      return None

   # ritorna una tupla (<The squared cartesian distance>,
   #                    <minDistPoint>
   #                    <afterVertex>
   #                    <leftOf>)
   dummy = closestSegmentWithContext(pt, geom)
   if dummy[2] is None:
      return None
   # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
   subGeom, atSubGeom = getSubGeomAtVertex(geom, dummy[2])
   
   LinearObjectListToExtend = QadLinearObjectList()
   LinearObjectListToExtend.fromPolyline(subGeom.asPolyline())
   
   if LinearObjectListToExtend.isClosed(): # non si può fare con polilinea chiusa
      return None
   
   # stabilisco se devo considerare l'inizio o la fine della polilinea
   if subGeom.vertexAt(0) == pt:
      distFromStart = 0
   else:
      distFromStart = QgsGeometry.fromPolyline(getLinePart(subGeom, \
                                                           subGeom.vertexAt(0), \
                                                           pt)).length()
   if distFromStart > (subGeom.length() / 2):
      # parte finale
      LinearObjectToExtend = LinearObjectListToExtend.getLinearObjectAt(-1)
   else:
      # parte iniziale
      LinearObjectToExtend = QadLinearObject(LinearObjectListToExtend.getLinearObjectAt(0))
      LinearObjectToExtend.reverse()

   minDist = sys.float_info.max
   newPt = None
   ExtendedLinearObject = QadLinearObject()
   gTransformed = QgsGeometry()
                                                                
   # per ciascun layer                                                         
   for limitLayerEntitySet in limitEntitySet.layerEntitySetList:
      limitLayer = limitLayerEntitySet.layer
      
      if limitLayer.crs() != layer.crs():
         coordTransform = QgsCoordinateTransform(limitLayer.crs(), layer.crs())          
      ExtendedLinearObject.set(LinearObjectToExtend)
            
      # per ciascuna entità del layer
      for featureId in limitLayerEntitySet.featureIds:
         f = getFeatureById(limitLayer, featureId)
         # Trasformo la geometria limite nel sistema di coordinate del <layer>     
         gTransformed = f.geometry()
         if limitLayer.crs() != layer.crs():
            gTransformed.transform(coordTransform)
         
         intPt = getIntersectionPtExtendQgsGeometry(LinearObjectToExtend, gTransformed, edgeMode)
         if intPt is not None:
            # cerco il punto di intersezione più vicino al punto finale di linearObject
            ExtendedLinearObject.setEndPt(intPt)
            if ExtendedLinearObject.length() < minDist:
               minDist = ExtendedLinearObject.length()
               newPt = intPt
         
   if newPt is None:
      return None
   
   if distFromStart > (subGeom.length() / 2):
      # modifico la parte finale
      LinearObjectListToExtend.getLinearObjectAt(-1).setEndPt(newPt)
   else:
      # modifico la parte iniziale
      LinearObjectListToExtend.getLinearObjectAt(0).setStartPt(newPt)
   
   pts = LinearObjectListToExtend.asPolyline(tolerance2ApproxCurve)
   
   return setSubGeom(geom, QgsGeometry.fromPolyline(pts), atSubGeom)    


#===============================================================================
# getIntersectionPtExtendQgsGeometry
#===============================================================================
def getIntersectionPtExtendQgsGeometry(linearObject, limitGeom, edgeMode):
   """
   la funzione calcola il punto di intersezione tra il prolungamento della parte lineare
   oltre il punto finale fino ad incontrare la geometria <limitGeom> secondo la modalità <edgeMode>.
   Viene restituito il punto più vicino al punto finale di <linearObject>.
   <linearObject> = parte lineare da estendere
   <limitGeom> = geometria da usare come limite di estensione
   <edgeMode> se = 0 si deve estendere la geometria fino ad incontrare l'oggetto più vicino
              se = 1 si deve estendere la geometria fino ad incontrare l'oggetto più vicino o 
              anche il suo prolungamento
   """
   intPts = []
   limitLinearObjectParts = QadLinearObjectList()
   
   # riduco in polilinee
   limitGeoms = asPointOrPolyline(limitGeom)
   for limitGeom in limitGeoms:         
      Found = False
      wkbType = limitGeom.wkbType()
      if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:
         pt = limitGeom.asPoint()
         if linearObject.isSegment():
            if isPtOnInfinityLine(linearObject.getStartPt(), linearObject.getEndPt(), pt):
               intPts.append(pt)
         else: # arco
            circle = QadCircle()
            circle.set(linearObject.getArc().center, linearObject.getArc().radius)
            if circle.isPtOnCircle(pt):
               intPts.append(pt)                  
      else: # Linestring
         limitLinearObjectParts.fromPolyline(limitGeom.asPolyline())
         
         # primo tratto
         LimitLinearObject = limitLinearObjectParts.getLinearObjectAt(0)
         pts = linearObject.getIntersectionPtsOnExtensionWithLinearObject(LimitLinearObject)               
         if edgeMode == 0: # senza estendere
            # considero solo i punti sulla parte <LimitLinearObject>
            for i in xrange(len(pts) - 1, -1, -1):
               pt = pts[i]
               if LimitLinearObject.containsPt(pt) == False:
                  del pts[i]
         else:
            if LimitLinearObject.isSegment():
               # considero solo i punti sulla parte <LimitLinearObject> o oltre l'inizio
               for i in xrange(len(pts) - 1, -1, -1):
                  pt = pts[i]
                  if LimitLinearObject.containsPt(pt) == False:
                     if getDistance(LimitLinearObject.getStartPt(), pt) > \
                        getDistance(LimitLinearObject.getEndPt(), pt):
                        del pts[i]
         intPts.extend(pts)
         
         # elaboro i tratti intermedi
         i = 1
         while i < limitLinearObjectParts.qty() - 1:
            LimitLinearObject = limitLinearObjectParts.getLinearObjectAt(i)
            pts = linearObject.getIntersectionPtsOnExtensionWithLinearObject(LimitLinearObject)               
            # considero solo i punti sulla parte <LimitLinearObject>
            for j in xrange(len(pts) - 1, -1, -1):
               pt = pts[j]
               if LimitLinearObject.containsPt(pt) == False:
                  del pts[j]
            
            intPts.extend(pts)
            i = i + 1

         # ultimo tratto
         LimitLinearObject = limitLinearObjectParts.getLinearObjectAt(-1)
         pts = linearObject.getIntersectionPtsOnExtensionWithLinearObject(LimitLinearObject)               
         if edgeMode == 0: # senza estendere
            # considero solo i punti sulla parte <LimitLinearObject>
            for i in xrange(len(pts) - 1, -1, -1):
               pt = pts[i]
               if LimitLinearObject.containsPt(pt) == False:
                  del pts[i]
         else:
            if LimitLinearObject.isSegment():
               # considero solo i punti sulla parte <LimitLinearObject> o oltre la fine
               for i in xrange(len(pts) - 1, -1, -1):
                  pt = pts[i]
                  if LimitLinearObject.containsPt(pt) == False:
                     if getDistance(LimitLinearObject.getStartPt(), pt) < \
                        getDistance(LimitLinearObject.getEndPt(), pt):
                        del pts[i]
         intPts.extend(pts)

   # cancello i punti di intersezione che non sono oltre la fine di linearObject
   for i in xrange(len(intPts) - 1, -1, -1):
      if linearObject.containsPt(intPts[i]) == True:
         del intPts[i]
      else:
         if linearObject.isSegment():
            if getDistance(linearObject.getStartPt(), intPts[i]) < \
               getDistance(linearObject.getEndPt(), intPts[i]):
               del intPts[i]

   if len(intPts) == 0:
      return None
   
   # cerco il punto di intersezione più vicino al punto finale di linearObject
   minDist = sys.float_info.max
   LimitLinearObject.set(linearObject)
   for intPt in intPts:
      LimitLinearObject.setEndPt(intPt)      
      if LimitLinearObject.length() < minDist:
         minDist = LimitLinearObject.length()
         pt = intPt
   
   return pt
         

#===============================================================================
# trimQgsGeometry
#===============================================================================
def trimQgsGeometry(layer, geom, pt, limitEntitySet, edgeMode, tolerance2ApproxCurve):
   """
   la funzione taglia la geometria (lineare) in una parte i cui limiti sono le intersezioni più
   vicine a pt con gli oggetti del gruppo <limitEntitySet> secondo la modalità <edgeMode>.
   <layer> = layer della geometria da tagliare
   <geom> = geometria da tagliare
   <pt> = punto che indica il sotto-oggetto grafico (se si tratta di WKBMultiLineString)
          e la parte di quell'oggetto che deve essere tagliata
   <QadEntitySet> = gruppo di entità che serve da limite di taglio
   <edgeMode> se = 0 si deve estendere la geometria fino ad incontrare l'oggetto più vicino
              se = 1 si deve estendere la geometria fino ad incontrare l'oggetto più vicino o 
              anche il suo prolungamento
   <tolerance2ApproxCurve> = tolleranza di approssimazione per le curve
   """
   if geom is None:
      return None

   wkbType = geom.wkbType()
   
   if wkbType != QGis.WKBLineString and wkbType != QGis.WKBMultiLineString and \
      wkbType != QGis.WKBPolygon and wkbType != QGis.WKBMultiPolygon:
      return None

   # ritorna una tupla (<The squared cartesian distance>,
   #                    <minDistPoint>
   #                    <afterVertex>
   #                    <leftOf>)
   dummy = closestSegmentWithContext(pt, geom)
   if dummy[2] is None:
      return None
   # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
   subGeom, atSubGeom = getSubGeomAtVertex(geom, dummy[2])
   
   LinearObjectListToCut = QadLinearObjectList()
   LinearObjectListToCut.fromPolyline(subGeom.asPolyline())
      
   # divido la polilinea in 2
   dummy = LinearObjectListToCut.breakOnPt(pt)
   partList1ToTrim = dummy[0]
   partList2ToTrim = dummy[1]

   trimmedLinearObject = QadLinearObject()
   gTransformed = QgsGeometry()
  
   # cerco intersezione più vicina a pt nella prima parte
   newPt1 = None
   geom1 = None
   if partList1ToTrim is not None:
      partList1ToTrim.reverse()
      newPt1, partNumberAtpartList1 = partList1ToTrim.getIntPtNearestToStartPt(layer.crs(), limitEntitySet, edgeMode)
      if newPt1 is None: # nessuna intersezione
         if LinearObjectListToCut.isClosed(): # se é chiusa
            if partList2ToTrim is None:
               return None               
            partList2ToTrim.reverse()
            newPt, partNumberAtpartList = partList2ToTrim.getIntPtNearestToStartPt(layer.crs(), limitEntitySet, edgeMode)
            if newPt is None:
               return None
            for i in xrange(0, partNumberAtpartList, 1):
               partList2ToTrim.remove(0)
            # modifico la parte iniziale della prima parte
            partList2ToTrim.getLinearObjectAt(0).setStartPt(newPt)
            partList2ToTrim.reverse()
      else:
         for i in xrange(0, partNumberAtpartList1, 1):
            partList1ToTrim.remove(0)
         # modifico la parte iniziale della prima parte
         partList1ToTrim.getLinearObjectAt(0).setStartPt(newPt1)
         geom1 = QgsGeometry.fromPolyline(partList1ToTrim.asPolyline(tolerance2ApproxCurve))

      partList1ToTrim.reverse()
      
   # cerco intersezione più vicina a pt nella seconda parte
   newPt2 = None  
   if partList2ToTrim is not None:
      newPt2, partNumberAtpartList2 = partList2ToTrim.getIntPtNearestToStartPt(layer.crs(), limitEntitySet, edgeMode)
      if newPt2 is None: # nessuna intersezione
         if LinearObjectListToCut.isClosed(): # se é chiusa
            if partList1ToTrim is None:
               return None               
            newPt, partNumberAtpartList = partList1ToTrim.getIntPtNearestToStartPt(layer.crs(), limitEntitySet, edgeMode)
            if newPt is None:
               return None
            for i in xrange(0, partNumberAtpartList, 1):
               partList1ToTrim.remove(0)
            # modifico la parte iniziale della prima parte
            partList1ToTrim.getLinearObjectAt(0).setStartPt(newPt)

   if newPt1 is None and newPt2 is None: # non ci sono punti di intersezione
      return None
   if newPt1 is not None and newPt2 is not None:
      if ptNear(newPt1, newPt2): # i due punti di intersezione coincidono
         return None
   
   if newPt2 is not None:
      for i in xrange(0, partNumberAtpartList2, 1):
         partList2ToTrim.remove(0)
      # modifico la parte iniziale della seconda parte
      partList2ToTrim.getLinearObjectAt(0).setStartPt(newPt2)
      geom2 = QgsGeometry.fromPolyline(partList2ToTrim.asPolyline(tolerance2ApproxCurve))
      if geom1 is None:
         return [geom2, None, atSubGeom]    
   else:
      geom2 = None
      
   return [geom1, geom2, atSubGeom]    


#===============================================================================
# getIntersectionPtTrimQgsGeometry
#===============================================================================
def getIntersectionPtTrimQgsGeometry(linearObject, limitGeom, edgeMode):
   """
   la funzione calcola il punto di intersezione tra la parte lineare
   e la geometria <limitGeom> secondo la modalità <edgeMode>.
   Viene restituito il punto più vicino al punto iniziale di <linearObject>.
   <linearObject> = parte lineare da estendere
   <limitGeom> = geometria da usare come limite di estensione
   <edgeMode> se = 0 si deve estendere la geometria fino ad incontrare l'oggetto più vicino
              se = 1 si deve estendere la geometria fino ad incontrare l'oggetto più vicino o 
              anche il suo prolungamento
   """
   intPts = []
   limitLinearObjectParts = QadLinearObjectList()
   
   # riduco in polilinee
   limitGeoms = asPointOrPolyline(limitGeom)
   for limitGeom in limitGeoms:         
      Found = False
      wkbType = limitGeom.wkbType()
      if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:
         pt = limitGeom.asPoint()
         if linearObject.containsPt(pt):
            intPts.append(pt)
      else: # Linestring
         limitLinearObjectParts.fromPolyline(limitGeom.asPolyline())
         
         # primo tratto
         LimitLinearObject = limitLinearObjectParts.getLinearObjectAt(0)
         pts = linearObject.getIntersectionPtsOnExtensionWithLinearObject(LimitLinearObject)               
         if edgeMode == 0: # senza estendere
            # considero solo i punti sulla parte <LimitLinearObject>
            for i in xrange(len(pts) - 1, -1, -1):
               pt = pts[i]
               if LimitLinearObject.containsPt(pt) == False:
                  del pts[i]
         else:
            if LimitLinearObject.isSegment():
               # considero solo i punti sulla parte <LimitLinearObject> o oltre l'inizio
               for i in xrange(len(pts) - 1, -1, -1):
                  pt = pts[i]
                  if LimitLinearObject.containsPt(pt) == False:
                     if getDistance(LimitLinearObject.getStartPt(), pt) > \
                        getDistance(LimitLinearObject.getEndPt(), pt):
                        del pts[i]
                        
         # considero solo i punti sulla parte <linearObject>
         for i in xrange(len(pts) - 1, -1, -1):
            pt = pts[i]
            if linearObject.containsPt(pt) == False:
               del pts[i]

         intPts.extend(pts)
         
         # elaboro i tratti intermedi
         i = 1
         while i < limitLinearObjectParts.qty() - 1:
            LimitLinearObject = limitLinearObjectParts.getLinearObjectAt(i)
            pts = linearObject.getIntersectionPtsOnExtensionWithLinearObject(LimitLinearObject)               
            # considero solo i punti sulla parte <LimitLinearObject> e <linearObject>
            for j in xrange(len(pts) - 1, -1, -1):
               pt = pts[j]
               if LimitLinearObject.containsPt(pt) == False or linearObject.containsPt(pt) == False:
                  del pts[j]
            
            intPts.extend(pts)
            i = i + 1

         # ultimo tratto
         LimitLinearObject = limitLinearObjectParts.getLinearObjectAt(-1)
         pts = linearObject.getIntersectionPtsOnExtensionWithLinearObject(LimitLinearObject)               
         if edgeMode == 0: # senza estendere
            # considero solo i punti sulla parte <LimitLinearObject>
            for i in xrange(len(pts) - 1, -1, -1):
               pt = pts[i]
               if LimitLinearObject.containsPt(pt) == False:
                  del pts[i]
         else:
            if LimitLinearObject.isSegment():
               # considero solo i punti sulla parte <LimitLinearObject> o oltre la fine
               for i in xrange(len(pts) - 1, -1, -1):
                  pt = pts[i]
                  if LimitLinearObject.containsPt(pt) == False:
                     if getDistance(LimitLinearObject.getStartPt(), pt) < \
                        getDistance(LimitLinearObject.getEndPt(), pt):
                        del pts[i]
                        
         # considero solo i punti sulla parte <linearObject>
         for i in xrange(len(pts) - 1, -1, -1):
            pt = pts[i]
            if linearObject.containsPt(pt) == False:
               del pts[i]
                        
         intPts.extend(pts)

   if len(intPts) == 0:
      return None
   
   # cerco il punto di intersezione più vicino al punto iniziale di linearObject
   minDist = sys.float_info.max
   LimitLinearObject.set(linearObject)
   for intPt in intPts:
      LimitLinearObject.setEndPt(intPt)      
      if LimitLinearObject.length() < minDist:
         minDist = LimitLinearObject.length()
         pt = intPt
   
   return pt


#===============================================================================
# stretchQgsGeometry
#===============================================================================
def stretchPoint(point, containerGeom, offSetX, offSetY):   
   if containerGeom.contains(point):
      return movePoint(point, offSetX, offSetY)
   
   return None


#===============================================================================
# stretchQgsGeometry
#===============================================================================
def stretchQgsGeometry(geom, containerGeom, offSetX, offSetY, tolerance2ApproxCurve):   
   wkbType = geom.wkbType()
   if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:
      pt = stretchPoint(geom.asPoint(), containerGeom, offSetX, offSetY)
      if pt is not None:
         return QgsGeometry.fromPoint(pt)
            
   if wkbType == QGis.WKBMultiPoint:
      stretchedGeom = QgsGeometry(geom)
      points = stretchedGeom.asMultiPoint() # vettore di punti
      atSubGeom = 0
      for pt in points:
         subGeom = QgsGeometry.fromPoint(pt)
         stretchedSubGeom = stretchQgsGeometry(subGeom, containerGeom, offSetX, offSetY, tolerance2ApproxCurve)
         stretchedGeom = setSubGeom(stretchedGeom, stretchedSubGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return stretchedGeom

   if wkbType == QGis.WKBLineString:
      return stretchQgsLineStringGeometry(geom, containerGeom, offSetX, offSetY, tolerance2ApproxCurve)
   
   if wkbType == QGis.WKBMultiLineString:
      stretchedGeom = QgsGeometry(geom)
      lines = stretchedGeom.asMultiPolyline() # lista di linee
      atSubGeom = 0
      for line in lines:        
         subGeom = QgsGeometry.fromPolyline(line)
         stretchedSubGeom = stretchQgsGeometry(subGeom, containerGeom, offSetX, offSetY, tolerance2ApproxCurve)
         stretchedGeom = setSubGeom(stretchedGeom, stretchedSubGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return stretchedGeom
         
   if wkbType == QGis.WKBPolygon:
      stretchedGeom = QgsGeometry(geom)
      lines = stretchedGeom.asPolygon() # lista di linee
      atSubGeom = 0
      for line in lines:        
         subGeom = QgsGeometry.fromPolyline(line)
         stretchedSubGeom = stretchQgsGeometry(subGeom, containerGeom, offSetX, offSetY, tolerance2ApproxCurve)
         stretchedGeom = setSubGeom(stretchedGeom, stretchedSubGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return stretchedGeom
      
   if wkbType == QGis.WKBMultiPolygon:
      stretchedGeom = QgsGeometry(geom)
      polygons = geom.asMultiPolygon() # vettore di poligoni
      atSubGeom = 0
      for polygon in polygons:
         subGeom = QgsGeometry.fromPolygon(polygon)
         stretchedSubGeom = stretchQgsGeometry(subGeom, containerGeom, offSetX, offSetY, tolerance2ApproxCurve)
         stretchedGeom = setSubGeom(stretchedGeom, stretchedSubGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return stretchedGeom
   
   return None
   
   
#===============================================================================
# stretchQgsLineStringGeometry
#===============================================================================
def stretchQgsLineStringGeometry(geom, containerGeom, offSetX, offSetY, tolerance2ApproxCurve):
   obj = whatGeomIs(0, geom)
   if (type(obj) != list and type(obj) != tuple):
      objType = obj.whatIs()
      if objType == "CIRCLE": # se é cerchio
         if containerGeom.contains(obj.center): # punto interno a containerGeom
            obj.center.setX(obj.center.x() + offSetX)
            obj.center.setY(obj.center.y() + offSetY)
            return QgsGeometry.fromPolyline(obj.asPolyline(tolerance2ApproxCurve))

   stretchedGeom = QgsGeometry(geom)
   snapper = QadSnapper()
   points = snapper.getEndPoints(stretchedGeom)
   del snapper

   linearObjectListToStretch = QadLinearObjectList()
   linearObjectListToStretch.fromPolyline(geom.asPolyline())
   
   for point in points:
      if containerGeom.contains(point): # punto interno a containerGeom                  
         atPart = linearObjectListToStretch.containsPt(point)
         while atPart >= 0:
            linearObject = linearObjectListToStretch.getLinearObjectAt(atPart)
            pt = linearObject.getStartPt()        
            if ptNear(pt, point): # cambio punto iniziale
               pt.setX(pt.x() + offSetX)
               pt.setY(pt.y() + offSetY)
               if linearObject.isSegment():
                  linearObject.setStartPt(pt)
               else:
                  oldArc = linearObject.getArc()
                  middlePt = oldArc.getMiddlePt()
                  distFromMiddleChord = getDistance(middlePt, getPerpendicularPointOnInfinityLine(oldArc.getStartPt(), oldArc.getEndPt(), middlePt))
                  
                  newArc = QadArc()
                  if linearObject.isInverseArc():                  
                     middlePt = getMiddlePoint(pt, oldArc.getStartPt())
                     middlePt = getPolarPointByPtAngle(middlePt, \
                                                       getAngleBy2Pts(pt, oldArc.getStartPt()) + math.pi / 2, \
                                                       distFromMiddleChord)                  
                     if newArc.fromStartSecondEndPts(oldArc.getStartPt(), middlePt, pt) == False:
                        return None
                  else:
                     middlePt = getMiddlePoint(pt, oldArc.getEndPt())
                     middlePt = getPolarPointByPtAngle(middlePt, \
                                                       getAngleBy2Pts(pt, oldArc.getEndPt()) - math.pi / 2, \
                                                       distFromMiddleChord)                  
                     if newArc.fromStartSecondEndPts(pt, middlePt, oldArc.getEndPt()) == False:
                        return None
                  linearObject.setArc(newArc, linearObject.isInverseArc())         
            else:
               pt = linearObject.getEndPt()
               if ptNear(pt, point): # cambio punto finale
                  pt.setX(pt.x() + offSetX)
                  pt.setY(pt.y() + offSetY)
                  if linearObject.isSegment():
                     linearObject.setEndPt(pt)
                  else:
                     oldArc = linearObject.getArc()
                     middlePt = oldArc.getMiddlePt()
                     distFromMiddleChord = getDistance(middlePt, getPerpendicularPointOnInfinityLine(oldArc.getStartPt(), oldArc.getEndPt(), middlePt))
                     
                     newArc = QadArc()
                     if linearObject.isInverseArc():
                        middlePt = getMiddlePoint(pt, oldArc.getEndPt())
                        middlePt = getPolarPointByPtAngle(middlePt, \
                                                          getAngleBy2Pts(pt, oldArc.getEndPt()) - math.pi / 2, \
                                                          distFromMiddleChord)                  
                        if newArc.fromStartSecondEndPts(pt, middlePt, oldArc.getEndPt()) == False:
                           return None
                     else:
                        middlePt = getMiddlePoint(pt, oldArc.getStartPt())
                        middlePt = getPolarPointByPtAngle(middlePt, \
                                                          getAngleBy2Pts(pt, oldArc.getStartPt()) + math.pi / 2, \
                                                          distFromMiddleChord)                  
                        if newArc.fromStartSecondEndPts(oldArc.getStartPt(), middlePt, pt) == False:
                           return None
                     linearObject.setArc(newArc, linearObject.isInverseArc())            
                  
            atPart = linearObjectListToStretch.containsPt(point, atPart + 1)
            
   pts = linearObjectListToStretch.asPolyline(tolerance2ApproxCurve)
   stretchedGeom = QgsGeometry.fromPolyline(pts)    
      
   return stretchedGeom   
           

#===============================================================================
# breakQgsGeometry
#===============================================================================
def breakQgsGeometry(layer, geom, firstPt, secondPt, tolerance2ApproxCurve):
   """
   la funzione spezza la geometria in un punto (se <secondPt> = None) o in due punti 
   come fa il trim.
   <layer> = layer della geometria da tagliare
   <geom> = geometria da tagliare
   <firstPt> = primo punto di divisione
   <secondPt> = secondo punto di divisione
   <tolerance2ApproxCurve> = tolleranza di approssimazione per le curve
   """
   if geom is None:
      return None

   wkbType = geom.wkbType()
   
   if wkbType != QGis.WKBLineString and wkbType != QGis.WKBMultiLineString and \
      wkbType != QGis.WKBPolygon and wkbType != QGis.WKBMultiPolygon:
      return None

   # ritorna una tupla (<The squared cartesian distance>,
   #                    <minDistPoint>
   #                    <afterVertex>
   #                    <leftOf>)
   dummy = closestSegmentWithContext(firstPt, geom)
   myFirstPt = dummy[1]
   if dummy[2] is None:
      return None
   # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
   subGeom, atSubGeom = getSubGeomAtVertex(geom, dummy[2])

   mySecondPt = None
   if secondPt is not None:
      dummy = closestSegmentWithContext(secondPt, geom)
      mySecondPt = dummy[1]
      # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
      subGeomSeconPt, atSubGeomSecondPt = getSubGeomAtVertex(geom, dummy[2])
      # se le sottogeometrie sono diverse
      if len(atSubGeom) != len(atSubGeomSecondPt):
         return None
      i = 0
      while i < len(atSubGeom):
         if atSubGeom[i] != atSubGeomSecondPt[i]:
            return None
         i = i + 1
   
   LinearObjectListToCut = QadLinearObjectList()
   LinearObjectListToCut.fromPolyline(subGeom.asPolyline())

   geom1 = None
   geom2 = None
   
   if mySecondPt is None or myFirstPt == mySecondPt:
      # divido la polilinea in 2
      dummy = LinearObjectListToCut.breakOnPt(myFirstPt)
      partList1ToTrim = dummy[0]
      partList2ToTrim = dummy[1]
      if LinearObjectListToCut.isClosed(): # se é chiusa
         return None
      else:
         if partList1ToTrim is not None:
            geom1 = QgsGeometry.fromPolyline(partList1ToTrim.asPolyline(tolerance2ApproxCurve))
         if partList2ToTrim is not None:
            geom2 = QgsGeometry.fromPolyline(partList2ToTrim.asPolyline(tolerance2ApproxCurve))
         
         return [geom1, geom2, atSubGeom]
   else: # c'é anche il secondo punto di divisione
      dist1 = LinearObjectListToCut.getDistanceFromStart(myFirstPt)
      dist2 = LinearObjectListToCut.getDistanceFromStart(mySecondPt)
      if dist1 < dist2:
         p1 = myFirstPt
         p2 = mySecondPt
      else:
         p1 = mySecondPt
         p2 = myFirstPt
         
      # divido la polilinea in 2
      dummy = LinearObjectListToCut.breakOnPt(p1)
      partList1ToTrim = dummy[0]
      partList2ToTrim = dummy[1]
      if partList2ToTrim is not None:
         # divido la polilinea in 2
         dummy = partList2ToTrim.breakOnPt(p2)
         partList2ToTrim = dummy[1]
      
      if LinearObjectListToCut.isClosed(): # se é chiusa
         if partList2ToTrim is None:
            partList2ToTrim = QadLinearObjectList()   
         if partList1ToTrim is not None:
            for linearObject in partList1ToTrim.defList:
               partList2ToTrim.append(linearObject)
               
         if partList2ToTrim.qty() > 0:
            circle = LinearObjectListToCut.getCircle()            
            if circle is not None: # se era una cerchio
               arc = QadArc()
               linearObject = partList2ToTrim.getLinearObjectAt(0)
               arc.fromStartSecondEndPts(linearObject.getStartPt(), linearObject.getEndPt(), partList2ToTrim.getEndPt())                         
               geom1 = QgsGeometry.fromPolyline(arc.asPolyline(tolerance2ApproxCurve))            
            else:
               geom1 = QgsGeometry.fromPolyline(partList2ToTrim.asPolyline(tolerance2ApproxCurve))            
      else: # se é aperta
         if partList1ToTrim is not None:
            geom1 = QgsGeometry.fromPolyline(partList1ToTrim.asPolyline(tolerance2ApproxCurve))      
         if partList2ToTrim is not None:
            geom2 = QgsGeometry.fromPolyline(partList2ToTrim.asPolyline(tolerance2ApproxCurve))
      if geom1 is None and geom2 is None:
         return None

      return [geom1, geom2, atSubGeom]
      

#===============================================================================
# mirrorPoint
#===============================================================================
def mirrorPoint(point, mirrorPt, mirrorAngle):
   """
   la funzione sposta un punto QgsPoint secondo una linea speculare passante per un 
   un punto <mirrorPt> ed avente angolo <mirrorAngle>
   """
   pointAngle = getAngleBy2Pts(mirrorPt, point)
   dist = getDistance(mirrorPt, point)
    
   return getPolarPointByPtAngle(mirrorPt, mirrorAngle + (mirrorAngle - pointAngle), dist)

#===============================================================================
# mirrorQgsGeometry
#===============================================================================
def mirrorQgsGeometry(geom, pt1, pt2):
   """
   la funzione crea copia speculare della geometria secondo una linea <pt1> <pt2>
   """
   if geom is None:
      return None

   mirrorAngle = getAngleBy2Pts(pt1, pt2)
   wkbType = geom.wkbType()   
   
   if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:
      pt = geom.asPoint() # un punto
      newPt = mirrorPoint(pt, pt1, mirrorAngle)
      return QgsGeometry.fromPoint(newPt)

   if wkbType == QGis.WKBMultiPoint:
      points = geom.asMultiPoint() # vettore di punti
      for pt in points:
         newPt = mirrorPoint(pt, pt1, mirrorAngle)
         pt.set(newPt.x(), newPt.y())
      return QgsGeometry.fromMultiPoint(points)
   
   if wkbType == QGis.WKBLineString:
      points = geom.asPolyline() # vettore di punti
      for pt in points:
         newPt = mirrorPoint(pt, pt1, mirrorAngle)
         pt.set(newPt.x(), newPt.y())
         
      return QgsGeometry.fromPolyline(points)
   
   if wkbType == QGis.WKBMultiLineString:
      lines = geom.asMultiPolyline() # lista di linee
      for line in lines:        
         for pt in line: # lista di punti
            newPt = mirrorPoint(pt, pt1, mirrorAngle)
            pt.set(newPt.x(), newPt.y())

      return QgsGeometry.fromMultiPolyline(lines)
   
   if wkbType == QGis.WKBPolygon:
      lines = geom.asPolygon() # lista di linee    
      for line in lines:
         for pt in line: # lista di punti
            newPt = mirrorPoint(pt, pt1, mirrorAngle)
            pt.set(newPt.x(), newPt.y())
            
      return QgsGeometry.fromPolygon(lines)

   if wkbType == QGis.WKBMultiPolygon:
      polygons = geom.asMultiPolygon() # vettore di poligoni
      for polygon in polygons:
         for line in polygon: # lista di linee
            for pt in line: # lista di punti
               newPt = mirrorPoint(pt, pt1, mirrorAngle)
               pt.set(newPt.x(), newPt.y())
               
      return QgsGeometry.fromPolygon(polygons)

   return None


#===============================================================================
# closeQgsGeometry
#===============================================================================
def closeQgsGeometry(geom, toClose, tolerance2ApproxCurve):
   """
   la funzione chiude o apre la geometria
   """
   if geom is None:
      return None

   wkbType = geom.wkbType()   
   
   if wkbType == QGis.WKBLineString:
      linearObjectList = QadLinearObjectList()
      linearObjectList.fromPolyline(geom.asPolyline())
      linearObjectList.setClose(toClose)
      return QgsGeometry.fromPolyline(linearObjectList.asPolyline(tolerance2ApproxCurve))
   
   if wkbType == QGis.WKBMultiLineString:
      newGeom = QgsGeometry(geom)
      lines = geom.asMultiPolyline() # lista di linee
      atSubGeom = 0
      for line in lines:        
         subGeom = closeQgsGeometry(QgsGeometry.fromPolyline(line), toClose, tolerance2ApproxCurve)
         newGeom = setSubGeom(newGeom, subGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return newGeom      

   return None


#===============================================================================
# reverseQgsGeometry
#===============================================================================
def reverseQgsGeometry(geom, tolerance2ApproxCurve):
   """
   la funzione inverte l'ordine dei punti della geometria
   """
   if geom is None:
      return None

   wkbType = geom.wkbType()   
   
   if wkbType == QGis.WKBLineString:
      linearObjectList = QadLinearObjectList()
      linearObjectList.fromPolyline(geom.asPolyline())
      linearObjectList.reverse()
      return QgsGeometry.fromPolyline(linearObjectList.asPolyline(tolerance2ApproxCurve))
   
   if wkbType == QGis.WKBMultiLineString:
      newGeom = QgsGeometry(geom)
      lines = geom.asMultiPolyline() # lista di linee
      atSubGeom = 0
      for line in lines:        
         subGeom = reverseQgsGeometry(QgsGeometry.fromPolyline(line), tolerance2ApproxCurve)
         newGeom = setSubGeom(newGeom, subGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return newGeom      

   if wkbType == QGis.WKBPolygon:
      newGeom = QgsGeometry(geom)
      lines = geom.asPolygon() # lista di linee
      atSubGeom = 0
      for line in lines:        
         subGeom = reverseQgsGeometry(QgsGeometry.fromPolyline(line), tolerance2ApproxCurve)
         newGeom = setSubGeom(newGeom, subGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return newGeom
      
   if wkbType == QGis.WKBMultiPolygon:
      newGeom = QgsGeometry(geom)
      polygons = geom.asMultiPolygon() # vettore di poligoni
      atSubGeom = 0
      for polygon in polygons:
         subGeom = reverseQgsGeometry(QgsGeometry.fromPolygon(polygon), tolerance2ApproxCurve)
         newGeom = setSubGeom(newGeom, subGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return newGeom

   return None


#===============================================================================
# curveQgsGeometry
#===============================================================================
def curveQgsGeometry(geom, toCurve, tolerance2ApproxCurve):
   """
   se toCurve = True:
   la funzione curva ogni segmento per adattarlo alla polilinea (lista di parti segmenti-archi).
   se toCurve = False:
   la funzione trasforma in segmento retto ogni arco della polilinea (lista di parti segmenti-archi).
   """
   if geom is None:
      return None

   wkbType = geom.wkbType()   
   
   if wkbType == QGis.WKBLineString:
      linearObjectList = QadLinearObjectList()
      linearObjectList.fromPolyline(geom.asPolyline())
      linearObjectList.curve(toCurve)

      return QgsGeometry.fromPolyline(linearObjectList.asPolyline(tolerance2ApproxCurve))
   
   if wkbType == QGis.WKBMultiLineString:
      newGeom = QgsGeometry(geom)
      lines = geom.asMultiPolyline() # lista di linee
      atSubGeom = 0
      for line in lines:        
         subGeom = curveQgsGeometry(QgsGeometry.fromPolyline(line), toCurve, tolerance2ApproxCurve)
         newGeom = setSubGeom(newGeom, subGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return newGeom      

   if wkbType == QGis.WKBPolygon:
      newGeom = QgsGeometry(geom)
      lines = geom.asPolygon() # lista di linee
      atSubGeom = 0
      for line in lines:        
         subGeom = curveQgsGeometry(QgsGeometry.fromPolyline(line), toCurve, tolerance2ApproxCurve)
         newGeom = setSubGeom(newGeom, subGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return newGeom
      
   if wkbType == QGis.WKBMultiPolygon:
      newGeom = QgsGeometry(geom)
      polygons = geom.asMultiPolygon() # vettore di poligoni
      atSubGeom = 0
      for polygon in polygons:
         subGeom = curveQgsGeometry(QgsGeometry.fromPolygon(polygon), toCurve, tolerance2ApproxCurve)
         newGeom = setSubGeom(newGeom, subGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return newGeom

   return None


#===============================================================================
# funzioni di creazione rettangoli
# getRectByCorners
#===============================================================================
def getRectByCorners(firstCorner, secondCorner, rot, gapType, \
                     gapValue1 = None, gapValue2 = None, tolerance2ApproxCurve = None):
   """
   ritorna una lista di punti che definisce il rettangolo costruito mediante 
   i due spigoli opposti firstCorner e secondCorner, la rotazione con punto base firstCorner e gapType 
   0 = gli spigoli del rettangolo hanno angoli retti
   1 = raccorda gli spigoli del rettangolo con un raggio di curvatura gapValue1
   2 = smussa gli spigoli del rettangolo con 2 distanze di cimatura gapValue1, gapValue2
   tolerance2ApproxCurve = errore minimo di tolleranza per rappresentare le curve
   """
   # creo un rettangolo ruotato con con angoli retti
   secondCornerProj = getPolarPointByPtAngle(firstCorner, rot, 10)
   pt2 = getPerpendicularPointOnInfinityLine(firstCorner, secondCornerProj, secondCorner)
   angle = getAngleBy2Pts(firstCorner, pt2)
   pt4 = getPolarPointByPtAngle(secondCorner, angle + math.pi, \
                                getDistance(firstCorner, pt2))
   
   if gapType == 0: # gli spigoli del rettangolo hanno angoli retti
      return [QgsPoint(firstCorner), pt2, QgsPoint(secondCorner), pt4, QgsPoint(firstCorner)]
   else:
      length = getDistance(firstCorner, pt2)
      width = getDistance(pt2, secondCorner)
                  
      if gapType == 1: # raccorda gli spigoli del rettangolo con un raggio di curvatura gapValue1
         if (gapValue1 * 2) > length or (gapValue1 * 2) > width: # il rettangolo é troppo piccolo
            return [QgsPoint(firstCorner), pt2, QgsPoint(secondCorner), pt4, QgsPoint(firstCorner)]
         
         if tolerance2ApproxCurve is None:
            tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
         else:
            tolerance = tolerance2ApproxCurve
         
         diagonal = math.sqrt((gapValue1 * gapValue1) * 2)
         diagonal = gapValue1 - (diagonal / 2)
         LinearObjectList = QadLinearObjectList()
         
         # lato
         p1 = getPolarPointByPtAngle(firstCorner, angle, gapValue1)
         p2 = getPolarPointByPtAngle(pt2, angle + math.pi, gapValue1)        
         LinearObjectList.append([p1, p2])
         # arco
         angle = getAngleBy2Pts(pt2, secondCorner)
         p3 = getPolarPointByPtAngle(pt2, angle, gapValue1)
         pMiddle = getMiddlePoint(p2, p3)
         pMiddle = getPolarPointByPtAngle(pMiddle, getAngleBy2Pts(pMiddle, pt2), diagonal) 
         arc = QadArc()
         arc.fromStartSecondEndPts(p2, pMiddle, p3)
         Inverse = False if ptNear(arc.getStartPt(), p2) else True
         LinearObjectList.append([arc, Inverse])
         # lato
         p4 = getPolarPointByPtAngle(secondCorner, angle + math.pi, gapValue1)
         LinearObjectList.append([p3, p4])
         # arco        
         angle = getAngleBy2Pts(secondCorner, pt4)
         p5 = getPolarPointByPtAngle(secondCorner, angle, gapValue1)
         pMiddle = getMiddlePoint(p4, p5)
         pMiddle = getPolarPointByPtAngle(pMiddle, getAngleBy2Pts(pMiddle, secondCorner), diagonal) 
         arc = QadArc()
         arc.fromStartSecondEndPts(p4, pMiddle, p5)
         Inverse = False if ptNear(arc.getStartPt(), p4) else True
         LinearObjectList.append([arc, Inverse])         
         # lato
         p6 = getPolarPointByPtAngle(pt4, angle + math.pi, gapValue1)
         LinearObjectList.append([p5, p6])
         # arco
         angle = getAngleBy2Pts(pt4, firstCorner)
         p7 = getPolarPointByPtAngle(pt4, angle, gapValue1)
         pMiddle = getMiddlePoint(p6, p7)
         pMiddle = getPolarPointByPtAngle(pMiddle, getAngleBy2Pts(pMiddle, pt4), diagonal) 
         arc = QadArc()
         arc.fromStartSecondEndPts(p6, pMiddle, p7)
         Inverse = False if ptNear(arc.getStartPt(), p6) else True
         LinearObjectList.append([arc, Inverse])         
         # lato
         p8 = getPolarPointByPtAngle(firstCorner, angle + math.pi, gapValue1)
         LinearObjectList.append([p7, p8])
         # arco
         pMiddle = getMiddlePoint(p8, p1)
         pMiddle = getPolarPointByPtAngle(pMiddle, getAngleBy2Pts(pMiddle, firstCorner), diagonal) 
         arc = QadArc()
         arc.fromStartSecondEndPts(p8, pMiddle, p1)
         Inverse = False if ptNear(arc.getStartPt(), p8) else True
         LinearObjectList.append([arc, Inverse])
         return LinearObjectList.asPolyline(tolerance)
      elif gapType == 2: # smussa gli spigoli del rettangolo con 2 distanze di cimatura gapValue1, gapValue2
         if (gapValue1 + gapValue2) > length or (gapValue1 + gapValue2) > width: # il rettangolo é troppo piccolo
            return [QgsPoint(firstCorner), pt2, QgsPoint(secondCorner), pt4, QgsPoint(firstCorner)]

         p1 = getPolarPointByPtAngle(firstCorner, angle, gapValue2)
         p2 = getPolarPointByPtAngle(pt2, angle + math.pi, gapValue1)
         angle = getAngleBy2Pts(pt2, secondCorner)
         p3 = getPolarPointByPtAngle(pt2, angle, gapValue2)
         p4 = getPolarPointByPtAngle(secondCorner, angle + math.pi, gapValue1)
         angle = getAngleBy2Pts(secondCorner, pt4)
         p5 = getPolarPointByPtAngle(secondCorner, angle, gapValue2)
         p6 = getPolarPointByPtAngle(pt4, angle+ math.pi, gapValue1)
         angle = getAngleBy2Pts(pt4, firstCorner)
         p7 = getPolarPointByPtAngle(pt4, angle, gapValue2)
         p8 = getPolarPointByPtAngle(firstCorner, angle + math.pi, gapValue1)
         return [p1, p2, p3, p4, p5, p6, p7, p8, p1]
      
   return []
  
#===============================================================================
# getRectByCornerAndDims
#===============================================================================
def getRectByCornerAndDims(firstCorner, lengthDim, widthDim, rot, gapType, \
                           gapValue1 = None, gapValue2 = None, tolerance2ApproxCurve = None):
   """
   ritorna una lista di punti che definisce il rettangolo costruito mediante 
   uno spigolo , la lunghezza, la larghezza, la rotazione con punto base firstCorner e gapType 
   0 = gli spigoli del rettangolo hanno angoli retti
   1 = raccorda gli spigoli del rettangolo con un raggio di curvatura gapValue1
   2 = smussa gli spigoli del rettangolo con 2 distanze di cimatura gapValue1, gapValue2 
   tolerance2ApproxCurve = errore minimo di tolleranza per rappresentare le curve
   """
   pt2 = getPolarPointByPtAngle(firstCorner, rot, lengthDim)
   secondCorner = getPolarPointByPtAngle(pt2, rot + (math.pi / 2), widthDim)
   return getRectByCorners(firstCorner, secondCorner, rot, gapType, gapValue1, gapValue2)

#===============================================================================
# getRectByAreaAndLength
#===============================================================================
def getRectByAreaAndLength(firstCorner, area, lengthDim, rot, gapType, \
                           gapValue1 = None, gapValue2 = None, tolerance2ApproxCurve = None):
   """
   ritorna una lista di punti che definisce il rettangolo costruito mediante 
   uno spigolo , l'area, la larghezza, la rotazione con punto base firstCorner e gapType 
   0 = gli spigoli del rettangolo hanno angoli retti
   1 = raccorda gli spigoli del rettangolo con un raggio di curvatura gapValue1
   2 = smussa gli spigoli del rettangolo con 2 distanze di cimatura gapValue1, gapValue2 
   tolerance2ApproxCurve = errore minimo di tolleranza per rappresentare le curve
   """   
   if gapType == 0: # gli spigoli del rettangolo hanno angoli retti
      widthDim = area / lengthDim
      return getRectByCornerAndDims(firstCorner, lengthDim, widthDim, rot, gapType, \
                                    gapValue1, gapValue2, tolerance2ApproxCurve)
   else:
      if gapType == 1: # raccorda gli spigoli del rettangolo con un raggio di curvatura gapValue1
         angleArea = ((2 * gapValue1) * (2 * gapValue1)) - (math.pi * gapValue1 * gapValue1)
         widthDim = (area + angleArea) / lengthDim
         if (gapValue1 * 2) > lengthDim or (gapValue1 * 2) > widthDim: # il rettangolo é troppo piccolo
            widthDim = area / lengthDim
         return getRectByCornerAndDims(firstCorner, lengthDim, widthDim, rot, gapType, \
                                       gapValue1, gapValue2, tolerance2ApproxCurve)
      elif gapType == 2: # smussa gli spigoli del rettangolo con 2 distanze di cimatura gapValue1, gapValue2
         angleArea = 2 * (gapValue1 * gapValue2)
         widthDim = (area + angleArea) / lengthDim
         if (gapValue1 + gapValue2) > lengthDim or (gapValue1 + gapValue2) > widthDim: # il rettangolo é troppo piccolo
            widthDim = area / lengthDim
         return getRectByCornerAndDims(firstCorner, lengthDim, widthDim, rot, gapType, \
                                       gapValue1, gapValue2, tolerance2ApproxCurve)

#===============================================================================
# getRectByAreaAndWidth
#===============================================================================
def getRectByAreaAndWidth(firstCorner, area, widthDim, rot, gapType, \
                           gapValue1 = None, gapValue2 = None, tolerance2ApproxCurve = None):
   """
   ritorna una lista di punti che definisce il rettangolo costruito mediante 
   uno spigolo , l'area, la larghezza, la rotazione con punto base firstCorner e gapType 
   0 = gli spigoli del rettangolo hanno angoli retti
   1 = raccorda gli spigoli del rettangolo con un raggio di curvatura gapValue1
   2 = smussa gli spigoli del rettangolo con 2 distanze di cimatura gapValue1, gapValue2 
   tolerance2ApproxCurve = errore minimo di tolleranza per rappresentare le curve
   """   
   if gapType == 0: # gli spigoli del rettangolo hanno angoli retti
      lengthDim = area / widthDim
      return getRectByCornerAndDims(firstCorner, lengthDim, widthDim, rot, gapType, \
                                    gapValue1, gapValue2, tolerance2ApproxCurve)
   else:                  
      if gapType == 1: # raccorda gli spigoli del rettangolo con un raggio di curvatura gapValue1
         angleArea = math.pi * gapValue1 * gapValue1
         lengthDim = (area + angleArea) / widthDim
         if (gapValue1 * 2) > lengthDim or (gapValue1 * 2) > widthDim: # il rettangolo é troppo piccolo
            lengthDim = area / widthDim
         return getRectByCornerAndDims(firstCorner, lengthDim, widthDim, rot, gapType, \
                                       gapValue1, gapValue2, tolerance2ApproxCurve)
      elif gapType == 2: # smussa gli spigoli del rettangolo con 2 distanze di cimatura gapValue1, gapValue2
         angleArea = 2 * (gapValue1 * gapValue2)
         lengthDim = (area + angleArea) / widthDim
         if (gapValue1 + gapValue2) > lengthDim or (gapValue1 + gapValue2) > widthDim: # il rettangolo é troppo piccolo
            lengthDim = area / widthDim
         return getRectByCornerAndDims(firstCorner, lengthDim, widthDim, rot, gapType, \
                                       gapValue1, gapValue2, tolerance2ApproxCurve)


#===============================================================================
# funzioni di creazione poligoni
# getPolygonByNsidesCenterRadius
#===============================================================================
def getPolygonByNsidesCenterRadius(sideNumber, centerPt, radius, Inscribed, ptStart = None):
   """
   ritorna una lista di punti che definisce il poligono costruito mediante 
   sideNumber = numero di lati 
   centerPt = centro del poligono
   radius = raggio del cerchio
   Inscribed = se True significa poligono inscritto altrimento circoscritto
   ptStart = punto da cui partire
   """
   result = []      
   angleIncrement = 2 * math.pi / sideNumber
   # poligono circoscritto
   if Inscribed == False:
      # calcolo il nuovo raggio 
      myRadius = radius / math.cos(angleIncrement / 2)

      if ptStart is None:
         myPtStart = getPolarPointByPtAngle(centerPt, math.pi / 2 * 3 + (angleIncrement / 2), myRadius)
         angle = getAngleBy2Pts(centerPt, myPtStart)
      else:
         angle = getAngleBy2Pts(centerPt, ptStart)      
         myPtStart = getPolarPointByPtAngle(centerPt, angle + (angleIncrement / 2), myRadius)
         angle = getAngleBy2Pts(centerPt, myPtStart)      
   else: # poligono inscritto
      myRadius = radius
      
      if ptStart is None:
         myPtStart = getPolarPointByPtAngle(centerPt, math.pi / 2 * 3 + (angleIncrement / 2), myRadius)
         angle = getAngleBy2Pts(centerPt, myPtStart)
      else:
         myPtStart = ptStart
         angle = getAngleBy2Pts(centerPt, ptStart)      
      
   result.append(myPtStart)
   for i in xrange(1, sideNumber, 1):
      angle = angle + angleIncrement
      result.append(getPolarPointByPtAngle(centerPt, angle, myRadius))  
   result.append(myPtStart)
   
   return result

#===============================================================================
# getPolygonByNsidesEdgePts
#===============================================================================
def getPolygonByNsidesEdgePts(sideNumber, firstEdgePt, secondEdgePt):
   """
   ritorna una lista di punti che definisce il poligono costruito mediante 
   sideNumber = numero di lati 
   firstEdgePt = primo punto di un lato
   secondEdgePt = secondo punto di un lato
   """
   result = []      
   angleIncrement = 2 * math.pi / sideNumber
   angle = getAngleBy2Pts(firstEdgePt, secondEdgePt)
   sideLength = getDistance(firstEdgePt, secondEdgePt)
         
   result.append(firstEdgePt)
   result.append(secondEdgePt)
   lastPoint = secondEdgePt
   for i in xrange(1, sideNumber - 1, 1):
      angle = angle + angleIncrement
      lastPoint = getPolarPointByPtAngle(lastPoint, angle, sideLength)
      result.append(lastPoint)  
   result.append(firstEdgePt)
   
   return result

#===============================================================================
# getPolygonByNsidesArea
#===============================================================================
def getPolygonByNsidesArea(sideNumber, centerPt, area):
   """
   ritorna una lista di punti che definisce il poligono costruito mediante 
   sideNumber = numero di lati 
   centerPt = centro del poligono
   area = area del poligono
   """
   angle = 2 * math.pi / sideNumber
   triangleArea = area / sideNumber / 2
   # divido il poligono in sideNumber triangoli
   # ogni trinagolo viene diviso in 2 generando 2 trinagoli rettangoli in cui
   # "(base * altezza) / 2 = Area" che equivale a "base = 2 * Area / altezza"
   # "tan(alfa) = base / altezza" che equivale a "tan(alfa) * altezza = base
   # per sostituzione si ha
   # "tan(alfa) * altezza = 2 * Area / altezza" quindi
   # "altezza = sqrt(2 * Area / tan(alfa))"
   h = math.sqrt(2 * triangleArea / math.tan(angle / 2))
   
   return getPolygonByNsidesCenterRadius(sideNumber, centerPt, h, False)


#===============================================================================
# getSubGeomAtVertex
#===============================================================================
def getSubGeomAtVertex(geom, atVertex):
   # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
   # la posizione é espressa con una lista (<index ogg. princ> [<index ogg. sec.>])
   wkbType = geom.wkbType()
   
   if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:
      if atVertex != 0:
         return None
      else:
         return QgsGeometry(geom), [0]

   if wkbType == QGis.WKBMultiPoint:
      pts = geom.asMultiPoint() # lista di punti
      if atVertex > len(pts) - 1:
         return None, None
      else:
         return QgsGeometry.fromPoint(pts[atVertex]), [atVertex]

   if wkbType == QGis.WKBLineString:
      pts = geom.asPolyline() # lista di punti
      if atVertex > len(pts) - 1:
         return None, None
      else:
         return QgsGeometry(geom), [0]
         
   if wkbType == QGis.WKBMultiLineString:
      # cerco in quale linea é il vertice <atVertex>
      i = 0
      iLine = 0
      lines = geom.asMultiPolyline() # lista di linee   
      for line in lines:
         lineLen = len(line)
         if atVertex >= i and atVertex < i + lineLen:
            return QgsGeometry.fromPolyline(line), [iLine]
         i = lineLen 
         iLine = iLine + 1
      return None, None
   
   if wkbType == QGis.WKBPolygon:
      i = 0
      iLine = 0
      lines = geom.asPolygon() # lista di linee    
      for line in lines:
         lineLen = len(line)
         if atVertex >= i and atVertex < i + lineLen:
            return QgsGeometry.fromPolyline(line), [iLine]
         i = lineLen 
         iLine = iLine + 1
      return None, None

   if wkbType == QGis.WKBMultiPolygon:
      i = 0
      iPolygon = 0
      polygons = geom.asMultiPolygon() # lista di poligoni
      for polygon in polygons:
         iLine = 0
         for line in lines:
            lineLen = len(line)
            if atVertex >= i and atVertex < i + lineLen:
               return QgsGeometry.fromPolyline(line), [iPolygon, iLine]
            i = lineLen 
            iLine = iLine + 1
         iPolygon = iPolygon + 1
   
   return None


#===============================================================================
# setSubGeomAt
#===============================================================================
def getSubGeomAt(geom, atSubGeom):
   # ritorna la sotto-geometria la cui posizione
   # é espressa con una lista (<index ogg. princ> [<index ogg. sec.>])
   wkbType = geom.wkbType()
   
   ndx = 0
   if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D or wkbType == QGis.WKBLineString:
      if atSubGeom[0] == 0:
         return QgsGeometry(geom)
            
   if wkbType == QGis.WKBMultiPoint:
      nPoint = atSubGeom[0]
      return QgsGeometry(geom.vertexAt(nPoint))
      
   if wkbType == QGis.WKBMultiLineString:
      nLine = atSubGeom[0]
      lines = geom.asMultiPolyline() # lista di linee
      if nLine < len(lines) and nLine >= -len(lines):
         return QgsGeometry.fromPolyline(lines[nLine])
   
   if wkbType == QGis.WKBPolygon:
      nLine = atSubGeom[0]
      lines = geom.asPolygon() # lista di linee
      if nLine < len(lines) and nLine >= -len(lines):
         return QgsGeometry.fromPolyline(lines[nLine])

   if wkbType == QGis.WKBMultiPolygon:
      nPolygon = atSubGeom[0]
      nLine = atSubGeom[1]
      polygons = geom.asMultiPolygon() # lista di poligoni
      if nPolygon < len(polygons) and nPolygon >= -len(polygons):
         lines = polygons[nPolygon]            
         if nLine < len(lines) and nLine >= -len(lines):
            return QgsGeometry.fromPolyline(lines[nLine])
         
   return None


#===============================================================================
# setSubGeom
#===============================================================================
def setSubGeom(geom, SubGeom, atSubGeom):
   # restituisce una geometria con la sotto-geometria alla posizione <atSubGeom> 
   # la posizione é espressa con una lista (<index ogg. princ> [<index ogg. sec.>])
   wkbType = geom.wkbType()
   subWkbType = SubGeom.wkbType()
   
   ndx = 0
   if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D or wkbType == QGis.WKBLineString:
      if atSubGeom[0] == 0 and \
         (subWkbType == QGis.WKBPoint or subWkbType == QGis.WKBPoint25D or subWkbType == QGis.WKBLineString):
         return QgsGeometry(SubGeom)
            
   if wkbType == QGis.WKBMultiPoint:
      nPoint = atSubGeom[0]
      if subWkbType == QGis.WKBPoint or subWkbType == QGis.WKBPoint25D:
         result = QgsGeometry(geom)
         pt = SubGeom.asPoint()
         if result.moveVertex(pt.x, pt.y(), nPoint) == True:
            return result
      
   if wkbType == QGis.WKBMultiLineString:
      if subWkbType == QGis.WKBLineString:
         nLine = atSubGeom[0]
         lines = geom.asMultiPolyline() # lista di linee
         if nLine < len(lines) and nLine >= -len(lines):
            del lines[nLine]
            lines.insert(nLine, SubGeom.asPolyline())
            return QgsGeometry.fromMultiPolyline(lines)
   
   if wkbType == QGis.WKBPolygon:
      if subWkbType == QGis.WKBLineString:
         nLine = atSubGeom[0]
         lines = geom.asPolygon() # lista di linee
         if nLine < len(lines) and nLine >= -len(lines):
            del lines[nLine]
            lines.insert(nLine, SubGeom.asPolyline())
            return QgsGeometry.fromPolygon(lines)

   if wkbType == QGis.WKBMultiPolygon:
      if subWkbType == QGis.WKBLineString:
         nPolygon = atSubGeom[0]
         nLine = atSubGeom[1]
         polygons = geom.asMultiPolygon() # lista di poligoni
         if nPolygon < len(polygons) and nPolygon >= -len(polygons):
            lines = polygons[nPolygon]            
            if nLine < len(lines) and nLine >= -len(lines):
               del lines[nLine]
               lines.insert(nLine, SubGeom.asPolyline())
               return QgsGeometry.fromMultiPolygon(polygons)
      elif subWkbType == QGis.WKBPolygon:
         nPolygon = atSubGeom[0]
         polygons = geom.asMultiPolygon() # lista di poligoni
         if nPolygon < len(polygons) and nPolygon >= -len(polygons):
            del polygons[nPolygon]
            polygons.insert(nPolygon, SubGeom.asPolygon())
            return QgsGeometry.fromMultiPolygon(polygons)
         
   return None


#===============================================================================
# delSubGeom
#===============================================================================
def delSubGeom(geom, atSubGeom):
   # restituisce una geometria con la sotto-geometria alla posizione <atSubGeom> cancellata
   # la posizione é espressa con una lista (<index ogg. princ> [<index ogg. sec.>])
   wkbType = geom.wkbType()
   
   ndx = 0
   if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D or wkbType == QGis.WKBLineString:
      return None
            
   if wkbType == QGis.WKBMultiPoint:
      nPoint = atSubGeom[0]
      result = QgsGeometry(geom)
      pt = SubGeom.asPoint()
      if result.deleteVertex(nPoint) == True:
         return result
      
   if wkbType == QGis.WKBMultiLineString:
      nLine = atSubGeom[0]
      lines = geom.asMultiPolyline() # lista di linee
      if nLine < len(lines) and nLine >= -len(lines):
         del lines[nLine]
         return QgsGeometry.fromMultiPolyline(lines)
   
   if wkbType == QGis.WKBPolygon:
      nLine = atSubGeom[0]
      lines = geom.asPolygon() # lista di linee
      if nLine < len(lines) and nLine >= -len(lines):
         del lines[nLine]
         return QgsGeometry.fromPolygon(lines)

   if wkbType == QGis.WKBMultiPolygon:
      nPolygon = atSubGeom[0]
      nLine = atSubGeom[1] if len(atSubGeom) > 1 else None
      polygons = geom.asMultiPolygon() # lista di poligoni
      if nPolygon < len(polygons) and nPolygon >= -len(polygons):
         if nLine is not None:
            lines = polygons[nPolygon]            
            if nLine < len(lines) and nLine >= -len(lines):
               del lines[nLine]
               return QgsGeometry.fromMultiPolygon(polygons)
         else:
            del polygons[nPolygon]
            return QgsGeometry.fromMultiPolygon(polygons)            
         
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
# offsetBridgeTheGapBetweenLines
#===============================================================================
def offsetBridgeTheGapBetweenLines(line1, line2, offset, gapType):
   """   
   la funzione colma il vuoto tra 2 segmenti retti (QadLinearObject) nel comando offset  
   secondo una distanza <offset> (che corrisponde alla distanza di offset s 
   chiamata da tale comando) ed un modo <gapType>:
   0 = Estende i segmenti alle relative intersezioni proiettate
   1 = Raccorda i segmenti attraverso un arco di raccordo di raggio <offset>
   2 = Cima i segmenti di linea in corrispondenza delle intersezioni proiettate.
       La distanza perpendicolare da ciascuna cima al rispettivo vertice
       sull'oggetto originale é uguale alla distanza <offset>.
   
   Se 
   Ritorna una lista di 3 elementi (None in caso di errore):   
   una linea che sostituisce <line1>, se = None <line1> va rimossa
   un arco, se = None non c'é arco di raccordo tra le due linee
   una linea che sostituisce <line2>, se = None <line2> va rimossa
   """
   # cerco il punto di intersezione tra le due linee
   ptInt = getIntersectionPointOn2InfinityLines(line1.getStartPt(), line1.getEndPt(), \
                                                line2.getStartPt(), line2.getEndPt())
   if ptInt is None: # linee parallele
      return None
   distBetweenLine1Pt1AndPtInt = getDistance(line1.getStartPt(), ptInt)
   distBetweenLine1Pt2AndPtInt = getDistance(line1.getEndPt(), ptInt)
   distBetweenLine2Pt1AndPtInt = getDistance(line2.getStartPt(), ptInt)
   distBetweenLine2Pt2AndPtInt = getDistance(line2.getEndPt(), ptInt)
   
   if gapType == 0: # Estende i segmenti     
      if distBetweenLine1Pt1AndPtInt > distBetweenLine1Pt2AndPtInt:
         # secondo punto di line1 più vicino al punto di intersezione
         newLine1 = QadLinearObject([line1.getStartPt(), ptInt])
      else:
         # primo punto di line1 più vicino al punto di intersezione
         newLine1 = QadLinearObject([ptInt, line1.getEndPt()])
         
      if distBetweenLine2Pt1AndPtInt > distBetweenLine2Pt2AndPtInt:
         # secondo punto di line2 più vicino al punto di intersezione
         newLine2 = QadLinearObject([line2.getStartPt(), ptInt])
      else:
         # primo punto di line2 più vicino al punto di intersezione
         newLine2 = QadLinearObject([ptInt, line2.getEndPt()])
      
      return [newLine1, None, newLine2]
   elif gapType == 1: # Raccorda i segmenti
      pt1Distant = line1.getStartPt() if distBetweenLine1Pt1AndPtInt > distBetweenLine1Pt2AndPtInt else line1.getEndPt()
      angleLine1 = getAngleBy2Pts(ptInt, pt1Distant)
         
      pt2Distant = line2.getStartPt() if distBetweenLine2Pt1AndPtInt > distBetweenLine2Pt2AndPtInt else line2.getEndPt()
      angleLine2 = getAngleBy2Pts(ptInt, pt2Distant)

      bisectorLine = getBisectorInfinityLine(pt1Distant, ptInt, pt2Distant, True)
      # cerco il punto di intersezione tra la bisettrice e 
      # la retta che congiunge i punti più distanti delle due linee
      pt = getIntersectionPointOn2InfinityLines(bisectorLine[0], bisectorLine[1], \
                                                pt1Distant, pt2Distant)
      angleBisectorLine = getAngleBy2Pts(ptInt, pt)
      #angleBisectorLine = getAngleBy2Pts(bisectorLine[0], bisectorLine[1])

      # calcolo l'angolo (valore assoluto) tra un lato e la bisettrice            
      alfa = angleLine1 - angleBisectorLine
      if alfa < 0:
         alfa = angleBisectorLine - angleLine1      
      if alfa > math.pi:
         alfa = (2 * math.pi) - alfa 

      # calcolo l'angolo del triangolo rettangolo sapendo che la somma degli angoli interni = 180
      # - alfa - 90 gradi (angolo retto)
      distFromPtInt = math.tan(math.pi - alfa - (math.pi / 2)) * offset
      pt1Proj = getPolarPointByPtAngle(ptInt, angleLine1, distFromPtInt)
      pt2Proj = getPolarPointByPtAngle(ptInt, angleLine2, distFromPtInt)
      # Pitagora
      distFromPtInt = math.sqrt((distFromPtInt * distFromPtInt) + (offset * offset))      
      secondPt = getPolarPointByPtAngle(ptInt, angleBisectorLine, distFromPtInt - offset)
      arc = QadArc()
      arc.fromStartSecondEndPts(pt1Proj, secondPt, pt2Proj)
      
      if distBetweenLine1Pt1AndPtInt > distBetweenLine1Pt2AndPtInt:
         # secondo punto di line1 più vicino al punto di intersezione
         newLine1 = QadLinearObject([pt1Distant, pt1Proj])
      else:
         # primo punto di line1 più vicino al punto di intersezione
         newLine1 = QadLinearObject([pt1Proj, pt1Distant])   

      if distBetweenLine2Pt1AndPtInt > distBetweenLine2Pt2AndPtInt:
         # secondo punto di line2 più vicino al punto di intersezione
         newLine2 = QadLinearObject([pt2Distant, pt2Proj])
      else:
         # primo punto di line2 più vicino al punto di intersezione
         newLine2 = QadLinearObject([pt2Proj, pt2Distant])
      
      # se i punti sono così vicini da essere considerati uguali         
      inverse = False if ptNear(newLine1.getEndPt(), arc.getStartPt()) else True
      return [newLine1, QadLinearObject([arc, inverse]), newLine2]   
   elif gapType == 2: # Cima i segmenti
      bisectorLine = getBisectorInfinityLine(line1.getEndPt(), ptInt, line2.getEndPt(), True)
      angleBisectorLine = getAngleBy2Pts(bisectorLine[0], bisectorLine[1])
      ptProj = getPolarPointByPtAngle(ptInt, angleBisectorLine, offset)

      pt1Proj = getPerpendicularPointOnInfinityLine(line1.getStartPt(), line1.getEndPt(), ptProj)
      if distBetweenLine1Pt1AndPtInt > distBetweenLine1Pt2AndPtInt:
         # secondo punto di line1 più vicino al punto di intersezione
         newLine1 = QadLinearObject([line1.getStartPt(), pt1Proj])
      else:
         # primo punto di line1 più vicino al punto di intersezione
         newLine1 = QadLinearObject([pt1Proj, line1.getEndPt()])      

      pt2Proj = getPerpendicularPointOnInfinityLine(line2.getStartPt(), line2.getEndPt(), ptProj)
      if distBetweenLine2Pt1AndPtInt > distBetweenLine2Pt2AndPtInt:
         # secondo punto di line2 più vicino al punto di intersezione
         newLine2 = QadLinearObject([line2.getStartPt(), pt2Proj])
      else:
         # primo punto di line2 più vicino al punto di intersezione
         newLine2 = QadLinearObject([pt2Proj, line2.getEndPt()])

      return [newLine1, QadLinearObject([pt1Proj, pt2Proj]), newLine2]

   return None


#===============================================================================
# bridgeTheGapBetweenLines
#===============================================================================
def bridgeTheGapBetweenLines(line1, ptOnLine1, line2, ptOnLine2, radius, filletMode):
   """   
   la funzione raccorda 2 segmenti retti (QadLinearObject) attraverso 
   un arco di raccordo di raggio <radius> che più si avvicinza ai punti di selezione
   sul segmento 1 <ptOnLine1> e sul segmento 2 <ptOnLine2>.
   <filletMode> modalità di raccordo; 1=Taglia-estendi, 2=Non taglia-estendi
   
   Ritorna una lista di 3 elementi (None in caso di errore):   
   una linea che sostituisce <line1>, se = None <line1> va rimossa
   un arco, se = None non c'é arco di raccordo tra le due linee
   una linea che sostituisce <line2>, se = None <line2> va rimossa
   """   
   if radius == 0: # Estende i segmenti     
      # cerco il punto di intersezione tra le due linee
      ptInt = getIntersectionPointOn2InfinityLines(line1.getStartPt(), line1.getEndPt(), \
                                                   line2.getStartPt(), line2.getEndPt())
      if ptInt is None: # linee parallele
         return None
      
      if distBetweenLine1Pt1AndPtInt > distBetweenLine1Pt2AndPtInt:
         # secondo punto di line1 più vicino al punto di intersezione
         resLine1 = QadLinearObject([line1.getStartPt(), ptInt])
      else:
         # primo punto di line1 più vicino al punto di intersezione
         resLine1 = QadLinearObject([ptInt, line1.getEndPt()])
         
      if distBetweenLine2Pt1AndPtInt > distBetweenLine2Pt2AndPtInt:
         # secondo punto di line2 più vicino al punto di intersezione
         resLine2 = QadLinearObject([line2.getStartPt(), ptInt])
      else:
         # primo punto di line2 più vicino al punto di intersezione
         resLine2 = QadLinearObject([ptInt, line2.getEndPt()])
      
      return [resLine1, None, resLine2]
   else: # Raccorda i segmenti
      filletArcs = getFilletArcsBetweenLines(line1, line2, radius)

      # cerco l'arco valido più vicino a ptOnLine1 e ptOnLine2
      AvgList = []
      Avg = sys.float_info.max   
   
      resLine1 = QadLinearObject()
      resFilletArc = QadLinearObject()
      resLine2 = QadLinearObject()
      for filletArc in filletArcs:
         # ricavo il nuovo segmento in modo che sia tangente con l'arco di raccordo       
         newLine1, distFromPtOnLine1 = getNewLineAccordingFilletArc(line1, filletArc, ptOnLine1)
         if newLine1 is None:
            continue           
         # ricavo il nuovo segmento in modo che sia tangente con l'arco di raccordo       
         newLine2, distFromPtOnLine2 = getNewLineAccordingFilletArc(line2, filletArc, ptOnLine2)
         if newLine2 is None:
            continue           
   
         del AvgList[:]              
         AvgList.append(distFromPtOnLine1)
         AvgList.append(distFromPtOnLine2)
   
         currAvg = numericListAvg(AvgList)           
         if currAvg < Avg: # mediamente più vicino
            Avg = currAvg
            resLine1.set(newLine1)
            resFilletArc.setArc(filletArc, False)
            resLine2.set(newLine2)
         
      if Avg == sys.float_info.max:
         return None   
   
      if filletMode == 1: # 1=Taglia-estendi
         return [resLine1, resFilletArc, resLine2]
      else:
         return [None, resFilletArc, None]


#===============================================================================
# getNewLineAccordingFilletArc
#===============================================================================
def getNewLineAccordingFilletArc(line, filletArc, ptOnLine):
   """
   dato un segmento retto (line di tipo <QadLinearObject>) e un arco che si 
   raccorda ad esso (<filleArc>), la funzione restituisce un nuovo segmento retto
   modificando <line> in modo che sia tangente all'arco di raccordo. 
   Inoltre, usando un punto indicato sul segmento <ptOnLine> restituisce 
   la distanza di quel punto dal punto di tangenza con l'arco di raccordo.
   """
   newLine = QadLinearObject()

   # determino quale punto (iniziale o finale) dell'arco di raccordo 
   # si interseca sul prolugamento del segmento retto
   if isPtOnInfinityLine(line.getStartPt(), line.getEndPt(), filletArc.getStartPt()):
      filletPtOnLine = filletArc.getStartPt()
      isStartFilletPtOnLine = True
   else:
      filletPtOnLine = filletArc.getEndPt()
      isStartFilletPtOnLine = False

   if line.containsPt(filletPtOnLine) == True: # se il punto é all'interno del segmento  
      newLine.set([filletPtOnLine, line.getEndPt()])
      
      if isStartFilletPtOnLine: # se il punto iniziale dell'arco di raccordo é sulla linea
         # se il nuovo segmento non é un segmento valido
         if ptNear(newLine.getStartPt(), newLine.getEndPt()):          
            # se l'arco di raccordo é tangente sul punto finale del nuovo segmento
            if TanDirectionNear(line.getTanDirectionOnEndPt(), \
                                normalizeAngle(filletArc.getTanDirectionOnStartPt())) == True:
               newLine.set(line) # ripristino il segmento originale
         else:
            # se l'arco di raccordo non é tangente sul punto iniziale del nuovo segmento            
            if TanDirectionNear(newLine.getTanDirectionOnStartPt(), \
                                normalizeAngle(filletArc.getTanDirectionOnStartPt() + math.pi)) == False:
               newLine.set([line.getStartPt(), filletPtOnLine])
            
         # se il nuovo segmento non é un segmento valido
         if ptNear(newLine.getStartPt(), newLine.getEndPt()) or \
            newLine.containsPt(ptOnLine) == False:
            return None, None          
         
         # calcolo la distanza dal punto ptOnLine
         distFromPtOnLine = getDistance(ptOnLine, filletPtOnLine)
      else: # se il punto finale dell'arco di raccordo é sulla linea
         # se il nuovo segmento non é un segmento valido
         if ptNear(newLine.getStartPt(), newLine.getEndPt()):          
            # se l'arco di raccordo é tangente sul punto finale del nuovo segmento
            if TanDirectionNear(line.getTanDirectionOnEndPt(), \
                                normalizeAngle(filletArc.getTanDirectionOnEndPt() + math.pi)) == True:
               newLine.set(line) # ripristino il segmento originale
         else:
            # se l'arco di raccordo non é tangente sul punto iniziale del nuovo segmento            
            if TanDirectionNear(newLine.getTanDirectionOnStartPt(), \
                                filletArc.getTanDirectionOnEndPt()) == False:
               newLine.set([line.getStartPt(), filletPtOnLine])
            
         # se il nuovo segmento non é un segmento valido
         if ptNear(newLine.getStartPt(), newLine.getEndPt()) or \
            newLine.containsPt(ptOnLine) == False:
            return None, None          
         
         # calcolo la distanza dal punto ptOnLine
         distFromPtOnLine = getDistance(ptOnLine, filletPtOnLine)
         
      return newLine, distFromPtOnLine
   else: # se il punto é all'esterno del segmento 
      if getDistance(line.getStartPt(), filletPtOnLine) < getDistance(line.getEndPt(), filletPtOnLine):
         newLine.set([filletPtOnLine, line.getEndPt()])
      else:
         newLine.set([line.getStartPt(), filletPtOnLine])

      return getNewLineAccordingFilletArc(newLine, filletArc, ptOnLine)
   

#===============================================================================
# auxFilletArcsBetweenLines
#===============================================================================
def auxFilletArcsBetweenLines(ptLine1, ptLine2, intPt, radius, both = True):
   """
   la funzione di ausilio a getFilletArcsBetweenLines
   Ritorna una lista dei possibili archi di raccordo tra la 
   linea 1 che va da <ptLine1> fino al punto di intersezione con la linea 2 <intPt>
   e 
   linea2 che va da <ptLine2> fino al punto di intersezione con la linea 1 <intPt>
   """
   res = []

   angleLine1 = getAngleBy2Pts(intPt, ptLine1)
   angleLine2 = getAngleBy2Pts(intPt, ptLine2)

   bisectorLine = getBisectorInfinityLine(ptLine1, intPt, ptLine2, True)
   # cerco il punto di intersezione tra la bisettrice e 
   # la retta che congiunge i punti più distanti delle due linee
   pt = getIntersectionPointOn2InfinityLines(bisectorLine[0], bisectorLine[1], \
                                             ptLine1, ptLine2)
   angleBisectorLine = getAngleBy2Pts(intPt, pt)

   # calcolo l'angolo (valore assoluto) tra un lato e la bisettrice            
   alfa = angleLine1 - angleBisectorLine
   if alfa < 0:
      alfa = angleBisectorLine - angleLine1      
   if alfa > math.pi:
      alfa = (2 * math.pi) - alfa 

   # calcolo l'angolo del triangolo rettangolo sapendo che la somma degli angoli interni = 180
   # - alfa - 90 gradi (angolo retto)
   distFromIntPt = math.tan(math.pi - alfa - (math.pi / 2)) * radius
   pt1Proj = getPolarPointByPtAngle(intPt, angleLine1, distFromIntPt)
   pt2Proj = getPolarPointByPtAngle(intPt, angleLine2, distFromIntPt)
   # Pitagora
   distFromIntPt = math.sqrt((distFromIntPt * distFromIntPt) + (radius * radius))      
   secondPt = getPolarPointByPtAngle(intPt, angleBisectorLine, distFromIntPt - radius)
   filletArc = QadArc()
   if filletArc.fromStartSecondEndPts(pt1Proj, secondPt, pt2Proj) == True:
      res.append(filletArc)
   if both:
      # stesso arco con il punto iniziale e finale invertiti
      filletArc = QadArc(filletArc)
      filletArc.inverse()
      res.append(filletArc)

   return res

#===============================================================================
# getFilletArcsBetweenCircleLine
#===============================================================================
def getFilletArcsBetweenLines(line1, line2, radius):
   """
   la funzione raccorda due linee rette (QadLinearObject) attraverso 
   un arco di raccordo di raggio <radius>.
   
   Ritorna una lista dei possibili archi
   """
   res = []
   
   # cerco il punto di intersezione tra le due linee
   intPt = getIntersectionPointOn2InfinityLines(line1.getStartPt(), line1.getEndPt(), \
                                                line2.getStartPt(), line2.getEndPt())
   if intPt is None: # linee parallele
      # calcolo la proiezione perpendicolare del punto iniziale di <line1> su <line2> 
      ptPerp = getPerpendicularPointOnInfinityLine(line2.getStartPt(), line2.getEndPt(), line1.getStartPt())
      d = getDistance(line1.getStartPt(), ptPerp)
      # d deve essere 2 volte <radius>
      if doubleNear(radius * 2, d):
         angle = getAngleBy2Pts(line1.getStartPt(), ptPerp)
         ptCenter = getPolarPointByPtAngle(line1.getStartPt(), angle, radius)
         filletArc = QadArc()
         if filletArc.fromStartCenterEndPts(line1.getStartPt(), ptCenter, ptPerp) == True:
            res.append(filletArc)
         # stesso arco con il punto iniziale e finale invertiti
         filletArc = QadArc()
         if filletArc.fromStartCenterEndPts(ptPerp, ptCenter, line1.getStartPt()) == True:
            res.append(filletArc)
      
         ptPerp = getPolarPointByPtAngle(line1.getEndPt(), angle, d)
         ptCenter = getPolarPointByPtAngle(line1.getEndPt(), angle, radius)
         filletArc = QadArc()
         if filletArc.fromStartCenterEndPts(line1.getEndPt(), ptCenter, ptPerp) == True:
            res.append(filletArc)
         # stesso arco con il punto iniziale e finale invertiti
         filletArc = QadArc()
         if filletArc.fromStartCenterEndPts(ptPerp, ptCenter, line1.getEndPt()) == True:
            res.append(filletArc)      
   else: # linee non parallele
      angleLine1 = getAngleBy2Pts(line1.getStartPt(), line1.getEndPt())
      angleLine2 = getAngleBy2Pts(line2.getStartPt(), line2.getEndPt())

      ptLine1 = getPolarPointByPtAngle(intPt, angleLine1, 1)
      ptLine2 = getPolarPointByPtAngle(intPt, angleLine2, 1)
      res.extend(auxFilletArcsBetweenLines(ptLine1, ptLine2, intPt, radius))

      ptLine2 = getPolarPointByPtAngle(intPt, angleLine2, -1)
      res.extend(auxFilletArcsBetweenLines(ptLine1, ptLine2, intPt, radius))
      
      ptLine1 = getPolarPointByPtAngle(intPt, angleLine1, -1)
      res.extend(auxFilletArcsBetweenLines(ptLine1, ptLine2, intPt, radius))

      ptLine2 = getPolarPointByPtAngle(intPt, angleLine2, 1)
      res.extend(auxFilletArcsBetweenLines(ptLine1, ptLine2, intPt, radius))

   return res


#===============================================================================
# bridgeTheGapBetweenCircleLine
#===============================================================================
def bridgeTheGapBetweenCircleLine(circle, ptOnCircle, line, ptOnLine, radius, filletMode):
   """
   la funzione raccorda un cerchio e un segmento retto (QadLinearObject) attraverso 
   un arco di raccordo di raggio <radius> che più si avvicinza ai punti di selezione
   sul cerchio <ptOnCircle> e sul segmento retto <ptOnLine>.
   <filletMode> modalità di raccordo; 1=Taglia-estendi, 2=Non taglia-estendi
   
   Ritorna una lista di 3 elementi (None in caso di errore):   
   None
   un arco, se = None non c'é arco di raccordo tra le due linee
   una linea che sostituisce <line>
   """
   # ricavo i possibili archi di raccordo
   _circle = circle.getCircle()  
   filletArcs = getFilletArcsBetweenCircleLine(_circle, line, radius)
   
   # cerco l'arco valido più vicino a ptOnArc e ptOnLine
   AvgList = []
   Avg = sys.float_info.max   

   resFilletArc = QadLinearObject()
   resLine = QadLinearObject()
   for filletArc in filletArcs:
      # ricavo il nuovo segmento in modo che sia tangente con l'arco di raccordo       
      newLine, distFromPtOnLine = getNewLineAccordingFilletArc(line, filletArc, ptOnLine)
      if newLine is None:
         continue           

      if _circle.isPtOnCircle(filletArc.getStartPt()):
         distFromPtOnCircle = _circle.lengthBetween2Points(filletArc.getStartPt(), \
                                                           ptOnCircle, \
                                                           filletArc.getTanDirectionOnStartPt() + math.pi)
      else:
         distFromPtOnCircle = _circle.lengthBetween2Points(filletArc.getEndPt(), \
                                                           ptOnCircle, \
                                                           filletArc.getTanDirectionOnEndPt())

      del AvgList[:]              
      AvgList.append(distFromPtOnLine)
      AvgList.append(distFromPtOnCircle)

      currAvg = numericListAvg(AvgList)           
      if currAvg < Avg: # mediamente piùvicino
         Avg = currAvg
         resLine.set(newLine)
         resFilletArc.setArc(filletArc, False)
      
   if Avg == sys.float_info.max:
      return None   

   if filletMode == 1: # 1=Taglia-estendi
      return [None, resFilletArc, resLine]
   else:
      return [None, resFilletArc, None]


#===============================================================================
# auxFilletArcsBetweenCircleLine
#===============================================================================
def auxFilletArcsBetweenCircleLine(circle, line, origCircle, origLine, both = True):
   """
   la funzione di ausilio a getFilletArcsBetweenArcLine
   Ritorna una lista dei possibili archi di raccordo tra <circle> e <line>
   """
   res = []
   # calcolo le intersezioni tra la circonferenza del cerchio e la retta parallela a <line> 
   # che daranno origine ai centri degli archi di raccordo
   intPts = circle.getIntersectionPointsWithInfinityLine(line[0], line[1])
   if len(intPts) > 0:
      # un punto di tangenza é dato dal punto a distanza radius dal centro di <origCircle> 
      # in direzione centro dell'arco di raccordo
      angle = getAngleBy2Pts(origCircle.center, intPts[0])
      tanCirclePt = getPolarPointByPtAngle(origCircle.center, angle, origCircle.radius)      
      # un punto di tangenza é la proiezione perpendicolare del centro dell'arco di raccordo
      # con <origLine> 
      ptPerp = getPerpendicularPointOnInfinityLine(origLine.getStartPt(), origLine.getEndPt(), intPts[0])
      filletArc = QadArc()
      if filletArc.fromStartCenterEndPts(tanCirclePt, \
                                         intPts[0], \
                                         ptPerp) == True:
         res.append(filletArc)
      if both:
         # stesso arco con il punto iniziale e finale invertiti
         filletArc = QadArc(filletArc)
         filletArc.inverse()
         res.append(filletArc)

      if len(intPts) > 1: # # due centri per i due archi di raccordo
         # un punto di tangenza é dato dal punto a distanza arc.radius dal centro di <arc> 
         # in direzione centro dell'arco di raccordo
         angle = getAngleBy2Pts(origCircle.center, intPts[1])
         tanCirclePt = getPolarPointByPtAngle(origCircle.center, angle, origCircle.radius)      
         # un punto di tangenza é la proiezione perpendicolare del centro dell'arco di raccordo
         # con <line> 
         ptPerp = getPerpendicularPointOnInfinityLine(origLine.getStartPt(), origLine.getEndPt(), intPts[1])
         filletArc = QadArc()
         if filletArc.fromStartCenterEndPts(tanCirclePt, \
                                            intPts[1], \
                                            ptPerp) == True:
            res.append(filletArc)
         if both:
            # stesso arco con il punto iniziale e finale invertiti
            filletArc = QadArc(filletArc)
            filletArc.inverse()
            res.append(filletArc)
               
   return res

#===============================================================================
# getFilletArcsBetweenCircleLine
#===============================================================================
def getFilletArcsBetweenCircleLine(circle, line, radius):
   """
   la funzione raccorda un arco e una linea retta (QadLinearObject) attraverso 
   un arco di raccordo di raggio <radius>.
   
   Ritorna una lista dei possibili archi
   """
   res = []
   
   offsetCircle = QadCircle(circle)

   intPts = circle.getIntersectionPointsWithInfinityLine(line.getStartPt(), line.getEndPt())
   if len(intPts) == 0:
      # se il cerchio e la retta generata dall'estensione di line
      # non hanno punti in comune
      leftOfLine = line.leftOf(circle.center)
      # creo una retta parallela a <line> ad una distanza <radius> verso il centro di <circle>  
      linePar = []
      angle = line.getTanDirectionOnStartPt()
      if leftOfLine < 0: # a sinistra
         linePar.append(getPolarPointByPtAngle(line.getStartPt(), angle + math.pi / 2, radius))
         linePar.append(getPolarPointByPtAngle(line.getEndPt(), angle + math.pi / 2, radius))
      else :# a destra
         linePar.append(getPolarPointByPtAngle(line.getStartPt(), angle - math.pi / 2, radius))
         linePar.append(getPolarPointByPtAngle(line.getEndPt(), angle - math.pi / 2, radius))
         
      # Calcolo la distanza dal centro di <circle> a <line>
      ptPerp = getPerpendicularPointOnInfinityLine(line.getStartPt(), line.getEndPt(), circle.center)
      d = getDistance(circle.center, ptPerp)
      # <radius> deve essere >= (d - raggio cerchio) / 2
      if radius >= (d - circle.radius) / 2:
         
         # caso 1: raccordo tra <circle> e <line> formando un flesso con <circle>
         
         # creo un cerchio con raggio aumentato di <radius> 
         offsetCircle.radius = circle.radius + radius
         res.extend(auxFilletArcsBetweenCircleLine(offsetCircle, linePar, circle, line))
         
         # caso 2: raccordo tra <circle> e <line> senza formare un flesso con <circle>
         
         # <radius> deve essere > raggio cerchio
         if radius > circle.radius:         
            # creo un cerchio con raggio = <radius> - circle.radius
            offsetCircle.radius = radius - circle.radius
            res.extend(auxFilletArcsBetweenCircleLine(offsetCircle, linePar, circle, line))
   else:
      # se il cerchio e la retta generata dall'estensione di line
      # hanno punti in comune
      # creo una retta parallela a <line> ad una distanza <radius> verso sinistra  
      linePar = []
      angle = line.getTanDirectionOnStartPt()
      linePar.append(getPolarPointByPtAngle(line.getStartPt(), angle + math.pi / 2, radius))
      linePar.append(getPolarPointByPtAngle(line.getEndPt(), angle + math.pi / 2, radius))

      # creo un cerchio con raggio aumentato di <radius> 
      offsetCircle.radius = circle.radius + radius
      res.extend(auxFilletArcsBetweenCircleLine(offsetCircle, linePar, circle, line))
      
      if circle.radius > radius: 
         # creo un cerchio con raggio diminuito di <radius>
         offsetCircle.radius = circle.radius - radius
         res.extend(auxFilletArcsBetweenCircleLine(offsetCircle, linePar, circle, line))

      # creo una retta parallela a <line> ad una distanza <radius> verso destra
      del linePar[:] # svuoto la lista
      linePar.append(getPolarPointByPtAngle(line.getStartPt(), angle - math.pi / 2, radius))
      linePar.append(getPolarPointByPtAngle(line.getEndPt(), angle - math.pi / 2, radius))

      # creo un cerchio con raggio aumentato di <radius> 
      offsetCircle.radius = circle.radius + radius
      res.extend(auxFilletArcsBetweenCircleLine(offsetCircle, linePar, circle, line))
      # calcolo le intersezioni tra la circonferenza del cerchio e la retta parallela a <line> 

      if circle.radius > radius: 
         # creo un cerchio con raggio diminuito di <radius>
         offsetCircle.radius = circle.radius - radius
         res.extend(auxFilletArcsBetweenCircleLine(offsetCircle, linePar, circle, line))

   return res


#===============================================================================
# getNewArcAccordingFilletArc
#===============================================================================
def getNewArcAccordingFilletArc(arc, filletArc, ptOnArc):
   """
   dato un arco (<arc>) e un altro arco che si raccorda ad esso (<filleArc>),
   la funzione restituisce un nuovo arco modificando <arc> in modo che sia 
   tangente all'arco di raccordo. Inoltre, usando un punto indicato sull'arco
   <ptOnArc> restituisce la distanza di quel punto dal punto di tangenza con l'arco
   di raccordo usando la direzione della tangente dell'arco di raccordo.
   """
   circle = QadCircle()    
   circle.set(arc.center, arc.radius)  

   newArc = QadArc(arc)

   # determino quale punto (iniziale o finale) dell'arco di raccordo 
   # si interseca sul prolugamento dell'arco 
   if circle.isPtOnCircle(filletArc.getStartPt()):
      filletPtOnArc = filletArc.getStartPt()
      isStartFilletPtOnArc = True
   else:
      filletPtOnArc = filletArc.getEndPt()
      isStartFilletPtOnArc = False

   # verifico che l'arco di raccordo sia tangente con l'arco
   newArc.setStartAngleByPt(filletPtOnArc)
      
   if isStartFilletPtOnArc: # se il punto iniziale dell'arco di raccordo é sull'arco
      # se il nuovo arco non é un arco valido
      if doubleNear(newArc.startAngle, newArc.endAngle):
         # se l'arco di raccordo é tangente sul punto finale dell'arco
         if TanDirectionNear(arc.getTanDirectionOnEndPt(), \
                             normalizeAngle(filletArc.getTanDirectionOnStartPt())) == True:
            newArc.startAngle = arc.startAngle # ripristino l'arco originale
      else:
         # se l'arco di raccordo non é tangente sul punto iniziale del nuovo arco            
         if TanDirectionNear(newArc.getTanDirectionOnStartPt(), \
                             normalizeAngle(filletArc.getTanDirectionOnStartPt() + math.pi)) == False:
            newArc.startAngle = arc.startAngle # ripristino l'arco originale
            newArc.setEndAngleByPt(filletPtOnArc)
         
      # se il nuovo arco non é un arco valido
      if doubleNear(newArc.startAngle, newArc.endAngle):
         return None, None
                   
      # calcolo la distanza dal punto ptOnArc
      distFromPtOnArc = circle.lengthBetween2Points(filletArc.getStartPt(), \
                                                    ptOnArc, \
                                                    filletArc.getTanDirectionOnStartPt() + math.pi)
   else: # se il punto finale dell'arco di raccordo é sull'arco
      # se il nuovo arco non é un arco valido
      if doubleNear(newArc.startAngle, newArc.endAngle):
         # se l'arco di raccordo é tangente sul punto finale dell'arco
         if TanDirectionNear(arc.getTanDirectionOnEndPt(), \
                             normalizeAngle(filletArc.getTanDirectionOnEndPt() + math.pi)) == True:
            newArc.startAngle = arc.startAngle # ripristino l'arco originale
      else:
         # se l'arco di raccordo non é tangente sul punto iniziale del nuovo arco            
         if TanDirectionNear(newArc.getTanDirectionOnStartPt(), \
                             filletArc.getTanDirectionOnEndPt()) == False:
            newArc.startAngle = arc.startAngle # ripristino l'arco originale
            newArc.setEndAngleByPt(filletPtOnArc)

      # se il nuovo arco non é un arco valido
      if doubleNear(newArc.startAngle, newArc.endAngle):
         return None, None

      # calcolo la distanza dal punto ptOnArc
      distFromPtOnArc = circle.lengthBetween2Points(filletArc.getEndPt(), \
                                                    ptOnArc, \
                                                    filletArc.getTanDirectionOnEndPt())

   return newArc, distFromPtOnArc


#===============================================================================
# bridgeTheGapBetweenArcLine
#===============================================================================
def bridgeTheGapBetweenArcLine(arc, ptOnArc, line, ptOnLine, radius, filletMode):
   """
   la funzione raccorda un arco e un segmento retto (QadLinearObject) attraverso 
   un arco di raccordo di raggio <radius> che piùsi avvicinza ai punti di selezione
   sull'arco <ptOnArc> e sul segmento retto <ptOnLine>.
   <filletMode> modalità di raccordo; 1=Taglia-estendi, 2=Non taglia-estendi
   
   Ritorna una lista di 3 elementi (None in caso di errore):   
   una arco che sostituisce <arc>
   un arco, se = None non c'é arco di raccordo tra le due linee
   una linea che sostituisce <line>
   """
   # ricavo i possibili archi di raccordo
   filletArcs = getFilletArcsBetweenArcLine(arc, line, radius)
   
   # cerco l'arco valido più vicino a ptOnArc e ptOnLine
   AvgList = []
   Avg = sys.float_info.max   

   resArc = QadLinearObject()
   resFilletArc = QadLinearObject()
   resLine = QadLinearObject()
   for filletArc in filletArcs:
      # ricavo il nuovo segmento in modo che sia tangente con l'arco di raccordo       
      newLine, distFromPtOnLine = getNewLineAccordingFilletArc(line, filletArc, ptOnLine)
      if newLine is None:
         continue        
            
      # ricavo il nuovo arco in modo che sia tangente con l'arco di raccordo       
      newArc, distFromPtOnArc = getNewArcAccordingFilletArc(arc.getArc(), filletArc, ptOnArc)
      if newArc is None:
         continue        

      del AvgList[:]              
      AvgList.append(distFromPtOnLine)
      AvgList.append(distFromPtOnArc)

      currAvg = numericListAvg(AvgList)           
      if currAvg < Avg: # mediamente più vicino
         Avg = currAvg
         resLine.set(newLine)
         resFilletArc.setArc(filletArc, False)
         resArc.setArc(newArc, False) 
      
   if Avg == sys.float_info.max:
      return None   

   if filletMode == 1: # 1=Taglia-estendi
      return [resLine, resFilletArc, resArc]
   else:
      return [None, resFilletArc, None]

#===============================================================================
# getFilletArcsBetweenArcLine
#===============================================================================
def getFilletArcsBetweenArcLine(arc, line, radius):
   """
   la funzione raccorda un arco e una linea retta (QadLinearObject) attraverso 
   un arco di raccordo di raggio <radius>.
   
   Ritorna una lista dei possibili archi
   """
   circle = QadCircle()
   circle.set(arc.getArc().center, arc.getArc().radius)
   
   return getFilletArcsBetweenCircleLine(circle, line, radius)


#===============================================================================
# bridgeTheGapBetweenCircles
#===============================================================================
def bridgeTheGapBetweenCircles(circle1, ptOnCircle1, circle2, ptOnCircle2, radius):
   """
   la funzione raccorda due cerchi (QadLinearObject) attraverso 
   un arco di raccordo di raggio <radius> che più si avvicinza ai punti di selezione
   sui cerchi.
   
   Ritorna una lista di 3 elementi (None in caso di errore):   
   None
   un arco, se = None non c'é arco di raccordo tra le due linee
   None
   """
   # ricavo i possibili archi di raccordo
   _circle1 = circle1.getCircle()
   _circle2 = circle2.getCircle()
   filletArcs = getFilletArcsBetweenCircles(_circle1, _circle2, radius)
   
   # cerco l'arco valido più vicino a ptOnCircle1 e ptOnCircle2
   AvgList = []
   Avg = sys.float_info.max   

   resFilletArc = QadLinearObject()
   for filletArc in filletArcs:
      if _circle1.isPtOnCircle(filletArc.getStartPt()):
         distFromPtOnCircle1 = _circle1.lengthBetween2Points(filletArc.getStartPt(), \
                                                             ptOnCircle1, \
                                                             filletArc.getTanDirectionOnStartPt() + math.pi)
         distFromPtOnCircle2 = _circle2.lengthBetween2Points(filletArc.getEndPt(), \
                                                             ptOnCircle2, \
                                                             filletArc.getTanDirectionOnEndPt())
      else:
         distFromPtOnCircle1 = _circle1.lengthBetween2Points(filletArc.getEndPt(), \
                                                             ptOnCircle1, \
                                                             filletArc.getTanDirectionOnEndPt())
         distFromPtOnCircle2 = _circle2.lengthBetween2Points(filletArc.getStartPt(), \
                                                             ptOnCircle2, \
                                                             filletArc.getTanDirectionOnStartPt()+ math.pi)

      del AvgList[:]              
      AvgList.append(distFromPtOnCircle1)
      AvgList.append(distFromPtOnCircle2)

      currAvg = numericListAvg(AvgList)           
      if currAvg < Avg: # mediamente più vicino
         Avg = currAvg
         resFilletArc.setArc(filletArc, False)
      
   if Avg == sys.float_info.max:
      return None   

   return [None, resFilletArc, None]


#===============================================================================
# auxFilletArcsBetweenCircles
#===============================================================================
def auxFilletArcsBetweenCircles(circle1, circle2, radius, both = True):
   """
   la funzione di ausilio a getFilletArcsBetweenCircles   
   Ritorna una lista dei possibili archi di raccordo tra i cerchi <circle1> e <circle2>
   """
   res = []
   # calcolo le intersezioni tra le due circonferenze 
   # che daranno origine ai centri degli archi di raccordo
   intPts = circle1.getIntersectionPointsWithCircle(circle2)

   if len(intPts) > 0:
      # un punto di tangenza é dato dal punto a distanza radius dal centro dell'arco di raccordo
      # in direzione centro dell'arco <circle1>
      angle = getAngleBy2Pts(intPts[0], circle1.center)
      tanC1Pt = getPolarPointByPtAngle(intPts[0], angle, radius)
      # un punto di tangenza é dato dal punto a distanza radius dal centro dell'arco di raccordo
      # in direzione centro dell'arco <circle2>
      angle = getAngleBy2Pts(intPts[0], circle2.center)
      tanC2Pt = getPolarPointByPtAngle(intPts[0], angle, radius)
      filletArc = QadArc()
      if filletArc.fromStartCenterEndPts(tanC1Pt, intPts[0], tanC2Pt) == True:
         res.append(filletArc)
      if both:
         # stesso arco con il punto iniziale e finale invertiti
         filletArc = QadArc(filletArc)
         filletArc.inverse()
         res.append(filletArc)

      if len(intPts) > 1:
         # un punto di tangenza é dato dal punto a distanza radius dal centro dell'arco di raccordo
         # in direzione centro dell'arco <circle1>
         angle = getAngleBy2Pts(intPts[1], circle1.center)
         tanC1Pt = getPolarPointByPtAngle(intPts[1], angle, radius)
         # un punto di tangenza é dato dal punto a distanza radius dal centro dell'arco di raccordo
         # in direzione centro dell'arco <circle2>
         angle = getAngleBy2Pts(intPts[1], circle2.center)
         tanC2Pt = getPolarPointByPtAngle(intPts[1], angle, radius)
         filletArc = QadArc()
         if filletArc.fromStartCenterEndPts(tanC1Pt, intPts[1], tanC2Pt) == True:
            res.append(filletArc)
         if both:
            # stesso arco con il punto iniziale e finale invertiti
            filletArc = QadArc(filletArc)
            filletArc.inverse()
            res.append(filletArc)
            
   return res
   
#===============================================================================
# getFilletArcsBetweenCircles
#===============================================================================
def getFilletArcsBetweenCircles(circle1, circle2, radius):
   """
   la funzione raccorda due cerchi attraverso un arco di raccordo di raggio <radius>.
   
   Ritorna una lista dei possibili archi
   """
   res = []
        
   # caso 1: raccordo tra <circle1> e <circle2> formando un flesso con ciascuno dei cerchi
   # creo un nuovo cerchio concentrico a circle1 con raggio aumentato di <radius>
   newCircle1 = QadCircle(circle1)
   newCircle1.radius = newCircle1.radius + radius
   # creo un nuovo cerchio concentrico a circle2 con raggio aumentato di <radius>
   newCircle2 = QadCircle(circle2)
   newCircle2.radius = newCircle2.radius + radius
  
   res.extend(auxFilletArcsBetweenCircles(newCircle1, newCircle2, radius))
   
   # caso 2: raccordo tra <circle1> e <circle2> senza formare un flesso con ciascuno dei cerchi      
   if radius - circle1.radius > 0 and radius - circle2.radius > 0: 
      # creo un nuovo cerchio concentrico a circle1 con raggio = <radius> - raggio di circle1
      newCircle1 = QadCircle(circle1)
      newCircle1.radius = radius - newCircle1.radius
      # creo un nuovo cerchio concentrico a circle2 con raggio = <radius> - raggio di circle2
      newCircle2 = QadCircle(circle2)
      newCircle2.radius = radius - newCircle2.radius
       
      res.extend(auxFilletArcsBetweenCircles(newCircle1, newCircle2, radius))

   # caso 3: raccordo tra <circle1> e <circle2> formando un flesso solo con circle1
   if radius - circle2.radius > 0: 
      # creo un nuovo cerchio concentrico a circle1 con raggio aumentato di <radius>
      newCircle1 = QadCircle(circle1)
      newCircle1.radius = newCircle1.radius + radius
      # creo un nuovo cerchio concentrico a circle2 con raggio = <radius> - raggio di circle2
      newCircle2 = QadCircle(circle2)
      newCircle2.radius = radius - newCircle2.radius
 
      res.extend(auxFilletArcsBetweenCircles(newCircle1, newCircle2, radius))
                  
   # caso 4: raccordo tra <circle1> e <circle2> formando un flesso solo con circle2
   if radius - circle1.radius > 0: 
      # creo un nuovo cerchio concentrico a circle1 con raggio aumentato di <radius>
      newCircle1 = QadCircle(circle1)
      newCircle1.radius = radius - newCircle1.radius
      # creo un nuovo cerchio concentrico a circle2 con raggio = <radius> - raggio di circle2
      newCircle2 = QadCircle(circle2)
      newCircle2.radius = newCircle2.radius + radius
 
      res.extend(auxFilletArcsBetweenCircles(newCircle1, newCircle2, radius))
                  
   # caso 5: raccordo tra <circle1> e <circle2> interno a <circle1> formando un flesso solo con circle2
   if getDistance(circle1.center, circle2.center) + circle2.radius <= circle1.radius and \
      circle1.radius - radius > 0: 
      # creo un nuovo cerchio concentrico a circle1 con raggio diminuito di <radius>
      newCircle1 = QadCircle(circle1)
      newCircle1.radius = newCircle1.radius - radius
      # creo un nuovo cerchio concentrico a circle2 con raggio aumentato di <radius>
      newCircle2 = QadCircle(circle2)
      newCircle2.radius = newCircle2.radius + radius
 
      res.extend(auxFilletArcsBetweenCircles(newCircle1, newCircle2, radius))
                  
   # caso 6: raccordo tra <circle1> interno a <circle2> e <circle2> formando un flesso solo con circle1
   if getDistance(circle1.center, circle2.center) + circle1.radius <= circle2.radius and \
      circle2.radius - radius > 0: 
      # creo un nuovo cerchio concentrico a circle1 con raggio aumentato di <radius>
      newCircle1 = QadCircle(circle1)
      newCircle1.radius = newCircle1.radius + radius
      # creo un nuovo cerchio concentrico a circle2 con raggio diminuito di <radius>
      newCircle2 = QadCircle(circle2)
      newCircle2.radius = newCircle2.radius - radius
 
      res.extend(auxFilletArcsBetweenCircles(newCircle1, newCircle2, radius))

   # caso 7: raccordo tra <circle1> e <circle2> interno a <circle1> senza formare alcun flesso
   if getDistance(circle1.center, circle2.center) + circle2.radius <= circle1.radius and \
      circle1.radius - radius > 0 and radius - circle2.radius: 
      # creo un nuovo cerchio concentrico a circle1 con raggio diminuito di <radius>
      newCircle1 = QadCircle(circle1)
      newCircle1.radius = newCircle1.radius - radius
      # creo un nuovo cerchio concentrico a circle2 con raggio = <radius> - raggio di circle2
      newCircle2 = QadCircle(circle2)
      newCircle2.radius = radius - newCircle2.radius
 
      res.extend(auxFilletArcsBetweenCircles(newCircle1, newCircle2, radius))

   return res


#===============================================================================
# bridgeTheGapBetweenArcs
#===============================================================================
def bridgeTheGapBetweenArcs(arc1, ptOnArc1, arc2, ptOnArc2, radius, filletMode):
   """
   la funzione raccorda due archi (QadLinearObject) attraverso 
   un arco di raccordo di raggio <radius> che più si avvicinza ai punti di selezione
   sull'arco1 <ptOnArc1> e sull'arco2 <ptOnArc2>.
   <filletMode> modalità di raccordo; 1=Taglia-estendi, 2=Non taglia-estendi
   
   Ritorna una lista di 3 elementi (None in caso di errore):   
   una arco che sostituisce <arc1>
   un arco, se = None non c'é arco di raccordo tra le due linee
   una arco che sostituisce <arc2>
   """
   # ricavo i possibili archi di raccordo
   filletArcs = getFilletArcsBetweenArcs(arc1, arc2, radius)
   
   # cerco l'arco valido più vicino a ptOnArc1 e ptOnArc2
   AvgList = []
   Avg = sys.float_info.max   

   resFilletArc = QadLinearObject()
   resArc1 = QadLinearObject()
   resArc2 = QadLinearObject()
   for filletArc in filletArcs:
      # ricavo il nuovo arco1 in modo che sia tangente con l'arco di raccordo       
      newArc1, distFromPtOnArc1 = getNewArcAccordingFilletArc(arc1.getArc(), filletArc, ptOnArc1)
      if newArc1 is None:
         continue
      # ricavo il nuovo arco in modo che sia tangente con l'arco di raccordo       
      newArc2, distFromPtOnArc2 = getNewArcAccordingFilletArc(arc2.getArc(), filletArc, ptOnArc2)
      if newArc2 is None:
         continue

      del AvgList[:]              
      AvgList.append(distFromPtOnArc1)
      AvgList.append(distFromPtOnArc2)

      currAvg = numericListAvg(AvgList)           
      if currAvg < Avg: # mediamente più vicino
         Avg = currAvg
         resArc1.setArc(newArc1, False) 
         resFilletArc.setArc(filletArc, False)
         resArc2.setArc(newArc2, False) 
      
   if Avg == sys.float_info.max:
      return None   

   if filletMode == 1: # 1=Taglia-estendi
      return [resArc1, resFilletArc, resArc2]
   else:
      return [None, resFilletArc, None]

#===============================================================================
# getFilletArcsBetweenArcs
#===============================================================================
def getFilletArcsBetweenArcs(arc1, arc2, radius):
   """
   la funzione raccorda due archi (QadLinearObject) attraverso 
   un arco di raccordo di raggio <radius>.
   
   Ritorna una lista dei possibili archi
   """  
   circle1 = QadCircle()
   circle1.set(arc1.getArc().center, arc1.getArc().radius)
   circle2 = QadCircle()
   circle2.set(arc2.getArc().center, arc2.getArc().radius)

   return getFilletArcsBetweenCircles(circle1, circle2, radius)


#===============================================================================
# bridgeTheGapBetweenArcCircle
#===============================================================================
def bridgeTheGapBetweenArcCircle(arc, ptOnArc, circle, ptOnCircle, radius, filletMode):
   """
   la funzione raccorda un arco e un cerchio (QadLinearObject) attraverso 
   un arco di raccordo di raggio <radius> che più si avvicinza ai punti di selezione
   sull'arco <ptOnArc> e sul cerchio <ptCircle>.
   <filletMode> modalità di raccordo; 1=Taglia-estendi, 2=Non taglia-estendi
   
   Ritorna una lista di 3 elementi (None in caso di errore):   
   una arco che sostituisce <arc>
   un arco, se = None non c'é arco di raccordo tra le due linee
   None
   """
   # ricavo i possibili archi di raccordo
   _circle = circle.getCircle()
   filletArcs = getFilletArcsBetweenArcCircle(arc, _circle, radius)
   
   # cerco l'arco valido più vicino a ptOnArc e ptOnCircle
   AvgList = []
   Avg = sys.float_info.max   

   resFilletArc = QadLinearObject()
   resArc = QadLinearObject()
   for filletArc in filletArcs:
      # ricavo il nuovo arco in modo che sia tangente con l'arco di raccordo       
      newArc, distFromPtOnArc = getNewArcAccordingFilletArc(arc.getArc(), filletArc, ptOnArc)
      if newArc is None:
         continue
         
      # calcolo la distanza dal punto ptOnCircle
      if _circle.isPtOnCircle(filletArc.getStartPt()): # se il punto iniziale dell'arco di raccordo é sul cerchio
         distFromPtOnCircle = _circle.lengthBetween2Points(filletArc.getStartPt(), \
                                                           ptOnCircle, \
                                                           filletArc.getTanDirectionOnStartPt() + math.pi)
      else: # se il punto finale dell'arco di raccordo é sul cerchio
         distFromPtOnCircle = _circle.lengthBetween2Points(filletArc.getEndPt(), \
                                                           ptOnCircle, \
                                                           filletArc.getTanDirectionOnEndPt())

      del AvgList[:]              
      AvgList.append(distFromPtOnArc)
      AvgList.append(distFromPtOnCircle)

      currAvg = numericListAvg(AvgList)           
      if currAvg < Avg: # mediamente più vicino
         Avg = currAvg
         resArc.setArc(newArc, False) 
         resFilletArc.setArc(filletArc, False)
      
   if Avg == sys.float_info.max:
      return None   

   if filletMode == 1: # 1=Taglia-estendi
      return [resArc, resFilletArc, None]
   else:
      return [None, resFilletArc, None]

#===============================================================================
# getFilletArcsBetweenArcCircle
#===============================================================================
def getFilletArcsBetweenArcCircle(arc, circle, radius):
   """
   la funzione raccorda un arco (QadLinearObject) e un cerchio attraverso 
   un arco di raccordo di raggio <radius>.
   
   Ritorna una lista dei possibili archi
   """  
   circle1 = QadCircle()
   circle1.set(arc.getArc().center, arc.getArc().radius)

   return getFilletArcsBetweenCircles(circle1, circle, radius)


#===============================================================================
# pretreatment_offset
#===============================================================================
def pretreatment_offset(partList):
   """
   la funzione controlla le "local self intersection"> :
   se il segmento (o arco) i-esimo e il successivo hanno 2 intersezioni allora si inserisce un vertice
   nel segmento (o arco) i-esimo tra i 2 punti di intersezione.
   La funzione riceve una lista di segmenti ed archi e ritorna una nuova lista di parti
   """
   # verifico se polilinea chiusa
   i = -1 if partList.isClosed() else 0   
   
   result = QadLinearObjectList()
   while i < partList.qty() - 1:
      if i == -1: # polilinea chiusa quindi prendo in esame l'ultimo segmento e il primo
         part = partList.getLinearObjectAt(-1)
         nextPart = partList.getLinearObjectAt(0)
      else:                  
         part = partList.getLinearObjectAt(i)
         nextPart = partList.getLinearObjectAt(i + 1)

      ptIntList = part.getIntersectionPtsWithLinearObject(nextPart)
      if len(ptIntList) == 2: # 2 punti di intersezione
         # calcolo il punto medio tra i 2 punti di intersezione in part
         if part.isSegment(): # segmento
            ptMiddle = getMiddlePoint(ptIntList[0], ptIntList[1])
            result.append([part.getStartPt(), ptMiddle])
            result.append([ptMiddle, part.getEndPt()])
         else: # arco
            arc1 = QadArc(part.getArc())
            arc2 = QadArc(part.getArc())
            # se i punti sono così vicini da essere considerati uguali
            if ptNear(part.getArc().getEndPt(), ptIntList[0]):
               ptInt = part.getArc().getEndPt()
            else:
               ptInt = part.getArc().getStartPt()
            
            angleInt = getAngleBy2Pts(part.getArc().center, ptInt)
            arc1.endAngle = angleInt
            arc2.startAngle = angleInt            
            result.append([arc1, part.isInverseArc()])
            result.append([arc2, part.isInverseArc()])
      else: # un solo punto di intersezione
         result.append(part)
      
      i = i + 1
   
   if partList.isClosed() == False: # se non é chiusa aggiungo l'ultima parte
      if partList.qty() > 1:
         result.append(nextPart)   
      else:
         result.append(partList.getLinearObjectAt(0))   
   
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
   3 = PFIP (Positive FIP) se il punto di intersezione é nella stessa direzione di part

   4 = NFIP (Negative FIP) se il punto di intersezione é nella direzione opposta di part
   """

   ptIntList = part.getIntersectionPtsOnExtensionWithLinearObject(nextPart)

   if len(ptIntList) == 0:
      if part.getEndPt() == nextPart.getStartPt(): # <nextPart> inizia dove finisce <part>
         return [part.getEndPt(), 1, 1] # TIP-TIP
      else:
         return None
   elif len(ptIntList) == 1:
      if part.isSegment(): # segmento
         if part.containsPt(ptIntList[0]):
            intTypePart = 1 # TIP
         else: # l'intersezione non é sul segmento (FIP)
            # se la direzione é la stessa del segmento
            if doubleNear(getAngleBy2Pts(part.getStartPt(), part.getEndPt()), \
                          getAngleBy2Pts(part.getStartPt(), ptIntList[0])):
               intTypePart = 3 # PFIP
            else:
               intTypePart = 4 # NFIP
      else: # arco
         if part.containsPt(ptIntList[0]):
            intTypePart = 1 # TIP
         else:
            intTypePart = 2 # FIP

      if nextPart.isSegment(): # segmento      
         if nextPart.containsPt(ptIntList[0]):
            intTypeNextPart = 1 # TIP
         else: # l'intersezione non é sul segmento (FIP)
            # se la direzione é la stessa del segmento
            if doubleNear(getAngleBy2Pts(nextPart.getStartPt(), nextPart.getEndPt()), \
                          getAngleBy2Pts(nextPart.getStartPt(), ptIntList[0])):
               intTypeNextPart = 3 # PFIP
            else:
               intTypeNextPart = 4 # NFIP
      else: # arco
         if nextPart.containsPt(ptIntList[0]):
            intTypeNextPart = 1 # TIP
         else:
            intTypeNextPart = 2 # FIP

      return [ptIntList[0], intTypePart, intTypeNextPart]
   else: # 2 punti di intersezione
      # scelgo il punto più vicino al punto finale di part     
      if part.isSegment(): # segmento
         if getDistance(ptIntList[0], part.getEndPt()) < getDistance(ptIntList[1], part.getEndPt()):
            ptInt = ptIntList[0]
         else:
            ptInt = ptIntList[1]

         if part.containsPt(ptInt):
            intTypePart = 1 # TIP
         else: # l'intersezione non é sul segmento (FIP)
            # se la direzione é la stessa del segmento
            if doubleNear(getAngleBy2Pts(part.getStartPt(), part.getEndPt()), \
                          getAngleBy2Pts(part.getStartPt(), ptInt)):
               intTypePart = 3 # PFIP
            else:
               intTypePart = 4 # NFIP

         # la seconda parte é sicuramente un'arco
         if nextPart.containsPt(ptInt):
            intTypeNextPart = 1 # TIP
         else: # l'intersezione non é sull'arco (FIP)
            intTypeNextPart = 2 # FIP         

         return [ptInt, intTypePart, intTypeNextPart]
      else: # arco
         finalPt = part.getEndPt()

         if getDistance(ptIntList[0], finalPt) < getDistance(ptIntList[1], finalPt):
            ptInt = ptIntList[0]
         else:
            ptInt = ptIntList[1]

         if part.containsPt(ptInt):
            intTypePart = 1 # TIP
         else: # l'intersezione non é sull'arco (FIP)
           intTypePart = 2 # FIP         

         if nextPart.isSegment(): # segmento
            if nextPart.containsPt(ptInt):
               intTypeNextPart = 1 # TIP
            else: # l'intersezione non é sul segmento (FIP)
               # se la direzione é la stessa del segmento
               if doubleNear(getAngleBy2Pts(nextPart.getStartPt(), nextPart.getEndPt()), \
                             getAngleBy2Pts(nextPart.getStartPt(), ptInt)):
                  intTypeNextPart = 3 # PFIP
               else:
                  intTypeNextPart = 4 # NFIP
         else : # arco
            if nextPart.containsPt(ptInt):
               intTypeNextPart = 1 # TIP
            else: # l'intersezione non é sull'arco (FIP)
               intTypeNextPart = 2 # FIP
                        
         return [ptInt, intTypePart, intTypeNextPart]
   
   
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
   # se la prima parte é un segmento e la seconda é un arco
   if part.isSegment():
      newNextPart = QadLinearObject(part)
      newNextPart.reverse() # rovescio la direzione
      newPart = QadLinearObject(nextPart)
      newPart.reverse() # rovescio la direzione
      newOffSetSide = "left" if offSetSide == "right" else "right"
      result = fillet2Parts_offset(newPart, newNextPart, newOffSetSide, offSetDist)
      result.setInverseArc(not result.isInverseArc()) # cambio verso
      return result
   else: # se la prima parte é un arco
      arc = part.getArc()
      inverse = part.isInverseArc()
      AngleProjected = getAngleBy2Pts(arc.center, part.getEndPt())
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
   # se il centro dell'arco di raccordo é interno all'arco di offset
   if getDistance(arc.center, center) < arc.radius:                           
      newArcInverse = inverse
      if inverse == False:
         newArc.fromStartCenterEndPts(arc.getEndPt(), \
                                      center, \
                                      nextPart.getStartPt())
      else:
         newArc.fromStartCenterEndPts(nextPart.getStartPt(), \
                                      center, \
                                      arc.getStartPt())                        
   else: # se il centro dell'arco di raccordo é esterno all'arco di offset
      newArcInverse = not inverse
      if inverse == False:
         newArc.fromStartCenterEndPts(nextPart.getStartPt(), \
                                      center, \
                                      arc.getEndPt())
      else:
         newArc.fromStartCenterEndPts(arc.getStartPt(), \
                                      center, \
                                      nextPart.getStartPt())
                                                            
   return QadLinearObject([newArc, newArcInverse])                     


#===============================================================================
# getUntrimmedOffSetPartList
#===============================================================================
def getUntrimmedOffSetPartList(partList, offSetDist, offSetSide, gapType, tolerance2ApproxCurve = None):
   """
   la funzione fa l'offset non pulito da eventuali tagli da apportare (vedi
   getTrimmedOffSetPartList") di una polilinea (lista di parti <partList> é QadLinearObjectList)
   secondo una distanza e un lato di offset ("right" o "left") 
   ed un modo <gapType>:
   0 = Estende i segmenti di linea alle relative intersezioni proiettate
   1 = Raccorda i segmenti di linea in corrispondenza delle relative intersezioni proiettate.
       Il raggio di ciascun segmento di arco é uguale alla distanza di offset
   2 = Cima i segmenti di linea in corrispondenza delle intersezioni proiettate.
       La distanza perpendicolare da ciascuna cima al rispettivo vertice
       sull'oggetto originale é uguale alla distanza di offset.
   tolerance2ApproxCurve = errore minimo di tolleranza
       
   La funzione ritorna una lista di parti della polilinee (lista di segmenti o archi) 
   """
   # verifico se polilinea chiusa
   isClosedPolyline = partList.isClosed()

   # creo una lista dei segmenti e archi che formano la polilinea
   partList = pretreatment_offset(partList)
     
   # faccio l'offset di ogni parte della polilinea
   newPartList = QadLinearObjectList()
   for part in partList.defList:
      if part.isSegment(): # segmento
         newPart = QadLinearObject(getOffSetLine(part.getStartPt(), part.getEndPt(), offSetDist, offSetSide))
         newPartList.append(newPart)
      else: # arco
         if part.isInverseArc(): # l'arco gira verso destra
            arcOffSetSide = "internal" if offSetSide == "right" else "external"         
         else: # l'arco gira verso sin
            arcOffSetSide = "external" if offSetSide == "right" else "internal"
         
         newArc = getOffSetArc(part.getArc(), offSetDist, arcOffSetSide)
         if newArc is not None:
            newPart = QadLinearObject([newArc, part.isInverseArc()]) # <arco> e <inverse>
            newPartList.append(newPart)

      # calcolo i punti di intersezione tra parti adiacenti
   # per ottenere una linea di offset non tagliata
   if isClosedPolyline == True:
      i = -1
   else:
      i = 0   

   untrimmedOffsetPartList = QadLinearObjectList()
   virtualPartPositionList = []
   while i < newPartList.qty() - 1:
      if i == -1: # polylinea chiusa quindi prendo in esame l'ultimo segmento e il primo
         part = newPartList.getLinearObjectAt(-1) # ultima parte
         nextPart = newPartList.getLinearObjectAt(0) # prima parte
      else:                  
         part = newPartList.getLinearObjectAt(i)
         nextPart = newPartList.getLinearObjectAt(i + 1)

      if untrimmedOffsetPartList.qty() == 0:
         lastUntrimmedOffsetPt = part.getStartPt()
      else:
         lastUntrimmedOffsetPt = untrimmedOffsetPartList.getLinearObjectAt(-1).getEndPt() # ultima parte
      
      IntPointInfo = getIntersectionPointInfo_offset(part, nextPart)
      if IntPointInfo is not None: # se c'é  un'intersezione
         IntPoint = IntPointInfo[0]
         IntPointTypeForPart = IntPointInfo[1]
         IntPointTypeForNextPart = IntPointInfo[2]

      if part.isSegment(): # segmento
         if nextPart.isSegment(): # segmento-segmento
            if IntPointInfo is not None: # se esiste un punto di intersezione
               if IntPointTypeForPart == 1: # TIP
                  if IntPointTypeForNextPart == 1: # TIP
                     untrimmedOffsetPartList.append([lastUntrimmedOffsetPt, IntPoint])
                  else: # FIP
                     untrimmedOffsetPartList.append([lastUntrimmedOffsetPt, part.getEndPt()])                  
                     untrimmedOffsetPartList.append([part.getEndPt(), nextPart.getStartPt()])
                     # aggiungo la posizione di questa parte virtuale
                     virtualPartPositionList.append(untrimmedOffsetPartList.qty() - 1)
               else: # FIP
                  if IntPointTypeForPart == 3: # PFIP
                     if gapType != 0:
                        newLines = offsetBridgeTheGapBetweenLines(part, nextPart, offSetDist, gapType)
                        untrimmedOffsetPartList.append(newLines[0])                
                        untrimmedOffsetPartList.append(newLines[1]) # arco o linea di raccordo
                     else:                    
                        untrimmedOffsetPartList.append([lastUntrimmedOffsetPt, IntPoint])
                  else: # NFIP
                     untrimmedOffsetPartList.append([lastUntrimmedOffsetPt, part.getEndPt()])
                     untrimmedOffsetPartList.append([part.getEndPt(), nextPart.getStartPt()])
                     # aggiungo la posizione di questa parte virtuale
                     virtualPartPositionList.append(untrimmedOffsetPartList.qty() - 1)
         else: # segmento-arco
            if IntPointInfo is not None: # se esiste un punto di intersezione
               if IntPointTypeForPart == 1: # TIP
                  if IntPointTypeForNextPart == 1: # TIP
                     untrimmedOffsetPartList.append([lastUntrimmedOffsetPt, IntPoint])
                  else: # FIP
                     untrimmedOffsetPartList.append([lastUntrimmedOffsetPt, part.getEndPt()])
                     untrimmedOffsetPartList.append([part.getEndPt(), nextPart.getStartPt()])
                     # aggiungo la posizione di questa parte virtuale
                     virtualPartPositionList.append(untrimmedOffsetPartList.qty() - 1)
               else: # FIP
                  if IntPointTypeForPart == 3: # PFIP
                     if IntPointTypeForNextPart == 2: # FIP
                        untrimmedOffsetPartList.append([lastUntrimmedOffsetPt, part.getEndPt()])
                        untrimmedOffsetPartList.append(fillet2Parts_offset(part, nextPart, offSetSide, offSetDist))               
                  else: # NFIP
                     if IntPointTypeForNextPart == 1: # TIP
                        untrimmedOffsetPartList.append([lastUntrimmedOffsetPt, part.getEndPt()])
                        untrimmedOffsetPartList.append([part.getEndPt(), nextPart.getStartPt()])
                        # aggiungo la posizione di questa parte virtuale
                        virtualPartPositionList.append(untrimmedOffsetPartList.qty() - 1)
            else: # non esiste un punto di intersezione
               untrimmedOffsetPartList.append([lastUntrimmedOffsetPt, part.getEndPt()])
               untrimmedOffsetPartList.append(fillet2Parts_offset(part, nextPart, offSetSide, offSetDist))               
      else: # arco
         if nextPart.isSegment(): # arco-segmento         
            if IntPointInfo is not None: # se esiste un punto di intersezione
               if IntPointTypeForPart == 1: # TIP
                  if IntPointTypeForNextPart == 1: # TIP
                     newPart = QadLinearObject(part)
                     newPart.setStartEndPts(lastUntrimmedOffsetPt, IntPoint) # modifico l'arco
                     untrimmedOffsetPartList.append(newPart)
                  else: # FIP
                     if IntPointTypeForNextPart == 3: # PFIP
                        newPart = QadLinearObject(part)
                        newPart.setStartPt(lastUntrimmedOffsetPt) # modifico l'arco
                        untrimmedOffsetPartList.append(newPart)
                        untrimmedOffsetPartList.append([part.getEndPt(), nextPart.getStartPt()])
                        # aggiungo la posizione di questa parte virtuale
                        virtualPartPositionList.append(untrimmedOffsetPartList.qty() - 1)
               else: # FIP
                  if IntPointTypeForNextPart == 4: # NFIP
                     newPart = QadLinearObject(part)
                     newPart.setStartPt(lastUntrimmedOffsetPt) # modifico l'arco
                     untrimmedOffsetPartList.append(newPart)
                     untrimmedOffsetPartList.append(fillet2Parts_offset(part, nextPart, offSetSide, offSetDist))               
                  elif IntPointTypeForNextPart == 1: # TIP
                     newPart = QadLinearObject(part)
                     newPart.setStartPt(lastUntrimmedOffsetPt) # modifico l'arco
                     untrimmedOffsetPartList.append(newPart)
                     untrimmedOffsetPartList.append([part.getEndPt(), nextPart.getStartPt()])
                     # aggiungo la posizione di questa parte virtuale
                     virtualPartPositionList.append(untrimmedOffsetPartList.qty() - 1)
            else: # non esiste un punto di intersezione
               newPart = QadLinearObject(part)
               newPart.setStartPt(lastUntrimmedOffsetPt) # modifico l'arco
               untrimmedOffsetPartList.append(newPart)
               untrimmedOffsetPartList.append(fillet2Parts_offset(part, nextPart, offSetSide, offSetDist))               
         else: # arco-arco
            arc = part.getArc()
            inverse = part.isInverseArc()
            nextArc = nextPart.getArc()
            nextInverse = nextPart.isInverseArc()

            if IntPointInfo is not None: # se esiste un punto di intersezione
               if IntPointTypeForPart == 1: # TIP
                  if IntPointTypeForNextPart == 1: # TIP
                     newPart = QadLinearObject(part)
                     newPart.setStartEndPts(lastUntrimmedOffsetPt, IntPoint) # modifico l'arco
                     untrimmedOffsetPartList.append(newPart)
                  else : # FIP
                     newPart = QadLinearObject(part)
                     newPart.setStartPt(lastUntrimmedOffsetPt) # modifico l'arco
                     untrimmedOffsetPartList.append(newPart)
                     
                     if inverse == False:
                        center = getPolarPointByPtAngle(arc.center, arc.endAngle, arc.radius - offSetDist)
                     else:
                        center = getPolarPointByPtAngle(arc.center, arc.startAngle, arc.radius - offSetDist)
                        
                     secondPtNewArc = getPolarPointByPtAngle(center, \
                                                             getAngleBy2Pts(center, IntPoint), \
                                                             offSetDist)                     
                     newArc = QadArc()
                     newArc.fromStartSecondEndPts(part.getEndPt(), \
                                                  secondPtNewArc, \
                                                  nextPart.getStartPt())

                     if ptNear(newArc.getStartPt(), part.getEndPt()):
                        untrimmedOffsetPartList.append([newArc, False])
                     else:
                        untrimmedOffsetPartList.append([newArc, True])
                     # aggiungo la posizione di questa parte virtuale
                     virtualPartPositionList.append(untrimmedOffsetPartList.qty() - 1)
               else: # FIP
                  if IntPointTypeForNextPart == 1: # TIP
                     newPart = QadLinearObject(part)
                     newPart.setStartPt(lastUntrimmedOffsetPt) # modifico l'arco
                     untrimmedOffsetPartList.append(newPart)
                     
                     if inverse == False:
                        center = getPolarPointByPtAngle(arc.center, arc.endAngle, arc.radius - offSetDist)
                     else:
                        center = getPolarPointByPtAngle(arc.center, arc.startAngle, arc.radius - offSetDist)
                        
                     secondPtNewArc = getPolarPointByPtAngle(center, \
                                                             getAngleBy2Pts(center, IntPoint), \
                                                             offSetDist)                     
                     newArc = QadArc()
                     newArc.fromStartSecondEndPts(part.getEndPt(), \
                                                  secondPtNewArc, \
                                                  nextPart.getStartPt())
                     if ptNear(newArc.getStartPt(), part.getEndPt()):
                        untrimmedOffsetPartList.append([newArc, False])
                     else:
                        untrimmedOffsetPartList.append([newArc, True])                    
                     # aggiungo la posizione di questa parte virtuale
                     virtualPartPositionList.append(untrimmedOffsetPartList.qty() - 1)
                  else: # FIP
                     newPart = QadLinearObject(part)
                     newPart.setStartEndPts(lastUntrimmedOffsetPt, IntPoint) # modifico l'arco
                     untrimmedOffsetPartList.append(newPart)                     
            else: # non esiste un punto di intersezione
               newPart = QadLinearObject(part)
               newPart.setStartPt(lastUntrimmedOffsetPt) # modifico l'arco
               untrimmedOffsetPartList.append(newPart)
               
               # prima di raccordare verifico se l'arco <part> si trova interamente dentro la zona di offset
               # dell'arco <nextPart> e viceversa. 
               # Per replicare questa eccezione fare una polilinea composta da 2 archi:
               # il primo con centro in ..., raggio..., angolo iniziale ... angolo finale ...
               # il secondo con centro in ..., raggio..., angolo iniziale ... angolo finale ...
               # offset a destra = 8
               arc = part.getArc()
               nextArc = nextPart.getArc()
               dist = getDistance(arc.center, nextArc.center)               
               minDistArc, maxDistArc = getOffsetDistancesFromCenterOnOffsetedArc(arc, inverse, offSetDist, offSetSide)
               minDistNextArc, maxDistNextArc = getOffsetDistancesFromCenterOnOffsetedArc(nextArc, nextInverse, offSetDist, offSetSide)
               
               if (dist + nextArc.radius <= maxDistArc and dist - nextArc.radius >= minDistArc) or \
                  (dist + arc.radius <= maxDistNextArc and dist - arc.radius >= minDistNextArc):
                  untrimmedOffsetPartList.append([newPart.getEndPt(), nextPart.getStartPt()])                  
               else:              
                  untrimmedOffsetPartList.append(fillet2Parts_offset(part, nextPart, offSetSide, offSetDist))
               
      i = i + 1

   if newPartList.qty() > 0:
      if isClosedPolyline == False:
         if untrimmedOffsetPartList.qty() == 0:
            # primo punto della prima parte di newPartList
            lastUntrimmedOffsetPt = newPartList.getLinearObjectAt(0).getStartPt()
         else:
            # ultimo punto dell'ultima parte di untrimmedOffsetPartList
            lastUntrimmedOffsetPt = untrimmedOffsetPartList.getLinearObjectAt(-1).getEndPt()
            
         newPart = QadLinearObject(newPartList.getLinearObjectAt(-1))
         newPart.setStartPt(lastUntrimmedOffsetPt) # modifico l'inizio
         untrimmedOffsetPartList.append(newPart)
      else:
         # primo punto = ultimo punto
         untrimmedOffsetPartList.getLinearObjectAt(0).setStartPt(untrimmedOffsetPartList.getLinearObjectAt(-1).getEndPt()) # modifico l'inizio

   # faccio un pre-clipping sulle parti virtuali
   return virtualPartClipping(untrimmedOffsetPartList, virtualPartPositionList)
   # test
   #return untrimmedOffsetPartList


#===============================================================================
# getOffsetDistancesFromCenterOnOffsetedArc
#===============================================================================
def getOffsetDistancesFromCenterOnOffsetedArc(arc, isInverseArc, offSetDist, offSetSide):
   """
   la funzione restituisce la distanza minima e massima dal centro dell'arco su cui è già stato fatto un offset.
   Queste distanze generano un'area di offset intorno all'arco originale.
   <arc> arco a cui è già stato fatto un offset
   <isInverseArc> come gira l'arco, se true gira verso destra altrimento gira verso sinistra
   <offSetDist> distanza di offset
   <offSetSide> parte in cui si vuole l'offset "right" o "left"
   """               
   if isInverseArc: # l'arco gira verso destra
      if offSetSide == "right": # offset sulla parte interna dell'arco
         minDist = arc.radius                     
         maxDist = arc.radius + 2 * offSetDist               
      else: # offset sulla parte esterna dell'arco
         maxDist = arc.radius                     
         minDist = arc.radius - 2 * offSetDist
   else: # l'arco gira verso sin
      if offSetSide == "right": # offset sulla parte esterna dell'arco
         maxDist = arc.radius                     
         minDist = arc.radius - 2 * offSetDist
      else: # offset sulla parte interna dell'arco
         minDist = arc.radius                     
         maxDist = arc.radius + 2 * offSetDist
                                    
   if minDist < 0: minDist = 0                                       

   return minDist, maxDist


#===============================================================================
# virtualPartClipping
#===============================================================================
def virtualPartClipping(untrimmedOffsetPartList, virtualPartPositionList):
   """
   la funzione restituisce una lista di parti in cui vengono tagliate le isole generate
   da parti virtuali (che invertono il senso della linea).
   Per ogni parte virtuale, si verifica se le parti che precedono e che seguono formano un'isola.
   In caso affermativo, se possibile (vedi casi specifici), l'sola viene rimossa.
   <untrimmedOffsetPartList> lista delle parti
   <virtualPartPositionList> lista delle posizioni delle parti virtuali (viene modificata)
   """
   result = QadLinearObjectList(untrimmedOffsetPartList)
   
   # per prima cosa elimino tutte le isole con parti virtuali che hanno le parti 
   # direttamente adiacenti intersecanti
   i = len(virtualPartPositionList) - 1
   while i >= 0:
      virtualPartPosition = virtualPartPositionList[i]
      # parte successiva a quella virtuale
      nextPos = result.getNextPos(virtualPartPosition)
      # parte precedente
      prevPos = result.getPrevPos(virtualPartPosition)
      
      if (prevPos is not None) and (nextPos is not None):
         nextPart = result.getLinearObjectAt(nextPos)
         prevPart = result.getLinearObjectAt(prevPos)
         # verifico se hanno un solo punto di intersezione
         ptIntList = prevPart.getIntersectionPtsWithLinearObject(nextPart)        
         if len(ptIntList) == 1:
            nextPart.setStartPt(ptIntList[0]) # modifico l'inizio
            prevPart.setEndPt(ptIntList[0]) # modifico la fine
            result.remove(virtualPartPosition)
            del virtualPartPositionList[i]
            
      i = i - 1
          
   prevPart_1 = QadLinearObject()
   prevPart_2 = QadLinearObject()
   nextPart_1 = QadLinearObject()
   nextPart_2 = QadLinearObject()

   # elimino tutte le isole con parti virtuali che hanno le parti adiacenti intersecanti
   # ma che non formino con il resto della linea altre isole.
   # quando considero un lato adiacente alla parte virtuale da un lato devo considerare le intersezioni 
   # partendo dal lato successivo quello adicente nella parte opposta di quello virtuale 
   for i in xrange(len(virtualPartPositionList) - 1, -1, -1):      
      virtualPartPosition = virtualPartPositionList[i]
      # finché non trovo l'intersezione
      nPrevPartsToRemove = -1
      prevPos = virtualPartPosition
      ptIntList = []      
      while len(ptIntList) == 0:
         virtualPart = result.getLinearObjectAt(virtualPartPosition)
         # parte successiva a quella virtuale
         nextPos = result.getNextPos(virtualPartPosition)
         nNextPartsToRemove = 0
         # parte precedente
         prevPos = result.getPrevPos(prevPos)
         # se trovo una parte virtuale mi fermo
         if virtualPartPositionList.count(prevPos) > 0:
            break 
          
         # l'ultima condizione é nel caso la polilinea sia chiusa
         if (prevPos is None) or (nextPos is None) or prevPos == nextPos:
            break

         nPrevPartsToRemove = nPrevPartsToRemove + 1
         prevPart = result.getLinearObjectAt(prevPos)
 
         # ciclo finche non ci sono più parti successive
         while (nextPos is not None) and (prevPos != nextPos):
            # se trovo una parte virtuale mi fermo
            if virtualPartPositionList.count(nextPos) > 0:
               break 
            nextPart = result.getLinearObjectAt(nextPos)
            ptIntList = prevPart.getIntersectionPtsWithLinearObject(nextPart)
            if len(ptIntList) > 0:
               break
            nextPos = result.getNextPos(nextPos) # parte successiva
            nNextPartsToRemove = nNextPartsToRemove + 1
    
      if len(ptIntList) == 1 and \
         not ptNear(ptIntList[0], virtualPart.getStartPt()) and \
         not ptNear(ptIntList[0], virtualPart.getEndPt()):
         prevPart_1.set(prevPart)            
         # se il punto iniziale della parte non coincide con quella del punto di intersezione
         if not ptNear(ptIntList[0], prevPart.getStartPt()):
            prevPart_1.setEndPt(ptIntList[0]) # modifico la fine 
            prevPart_2.set(prevPart)            
            prevPart_2.setStartPt(ptIntList[0]) # modifico l'inizio 
         else:
            prevPart_2.clear()
            
         nextPart_1.set(nextPart)            
         # se il punto finale della parte non coincide con quella del punto di intersezione
         if not ptNear(ptIntList[0], nextPart.getEndPt()):
            nextPart_1.setEndPt(ptIntList[0]) # modifico la fine 
            nextPart_2.set(nextPart)            
            nextPart_2.setStartPt(ptIntList[0]) # modifico l'inizio 
         else:
            nextPart_2.clear()                       
         
         ########################################################
         # Creo una lista di parti che definisce l'isola - inizio
         islandPartList = QadLinearObjectList()         
          
         islandPart = QadLinearObject(prevPart_2 if prevPart_2.isInitialized() else prevPart_1)
         islandPartList.append(islandPart)
         
         pos = virtualPartPosition        
         for j in xrange(nPrevPartsToRemove, 0, - 1):
            pos = result.getPrevPos(pos) # parte precedente        
            islandPartList.append(QadLinearObject(result.getLinearObjectAt(pos)))

         islandPartList.append(virtualPart)

         pos = virtualPartPosition        
         for j in xrange(1, nNextPartsToRemove + 1, 1):
            pos = result.getNextPos(pos) # parte successiva        
            islandPartList.append(QadLinearObject(result.getLinearObjectAt(pos)))

         islandPart = QadLinearObject(nextPart_1)
         islandPartList.append(islandPart)
            
         # Creo una lista di parti che definisce l'isola - fine
         ########################################################

         # verifico se le parti seguenti formano con islandPartList delle aree (più di 2 intersezioni)         
         if nextPart_2.isInitialized():
            nIntersections = 1
         else:
            nIntersections = 0

         for j in xrange(nextPos + 1, result.qty(), 1):            
            dummy = islandPartList.getIntersectionPtsWithLinearObject(result.getLinearObjectAt(j))
            intPtList = dummy[0]                               
            nIntersections = nIntersections + len(intPtList)

         # se é positivo e minore o uguale a 2 verifico anche dall'altra parte
         if nIntersections > 0 and nIntersections <= 2:
            # verifico se le parti precedenti formano con islandPartList delle aree (almeno 2 intersezioni)
            if prevPart_2.isInitialized():
               nIntersections = 1
            else:
               nIntersections = 0

            for j in xrange(prevPos - 1, -1, -1):            
               dummy = islandPartList.getIntersectionPtsWithLinearObject(result.getLinearObjectAt(j))
               intPtList = dummy[0]                    
               nIntersections = nIntersections + len(intPtList)

            # se é positivo e minore o uguale a 2 verifico anche dall'altra parte
            if nIntersections > 0 and nIntersections <= 2:
               # rimuovo island da result
               if nextPart_2.isInitialized():
                  nextPart.setStartPt(nextPart_2.getStartPt()) # modifico l'inizio
               else:
                  result.remove(nextPos)

               # cancello le parti inutili
               for j in xrange(0, nNextPartsToRemove, 1):
                  result.remove(virtualPartPosition + 1)
                   
               # cancello la parte virtuale
               result.remove(virtualPartPosition)
       
               # cancello le parti inutili
               for j in xrange(0, nPrevPartsToRemove, 1):
                  result.remove(virtualPartPosition - nPrevPartsToRemove)

               if prevPart_2.isInitialized():
                  prevPart.setEndPt(nextPart_2.getStartPt()) # modifico la fine 
               else:
                  result.remove(prevPos)

               del virtualPartPositionList[i]

   return result


#===============================================================================
# getIntPtListBetweenPartAndPartList_offset
#===============================================================================
def getIntPtListBetweenPartAndPartList_offset(part, partList):
   """
   la funzione restituisce due liste:
   la prima é una lista di punti di intersezione tra la parte <part>
   e una lista di parti <partList ordinata per distanza dal punto iniziale
   di part (scarta i doppioni e i punti iniziale-finale di part)
   la seconda é una lista che  contiene, rispettivamente per ogni punto di intersezione,
   il numero della parte (0-based) di <partList> in cui si trova quel punto.
   <part>: un segmento o arco 
   <partList>: lista delle parti di una polilinea 
   """
   startPtOfPart = part.getStartPt()
   endPtOfPart = part.getEndPt()
   intPtSortedList = [] # lista di ((punto, distanza dall'inizio della parte) ...)
   partNumber = -1
   # per ogni parte di partList
   for part2 in partList.defList:
      partNumber = partNumber + 1
      partialIntPtList = part.getIntersectionPtsWithLinearObject(part2)
      for partialIntPt in partialIntPtList:
         # escludo i punti che sono all'inizio-fine di part
         
         # se i punti sono così vicini da essere considerati uguali         
         if ptNear(startPtOfPart, partialIntPt) == False and \
            ptNear(endPtOfPart, partialIntPt) == False:
            # escludo i punti che sono già in intPtSortedList
            found = False
            for intPt in intPtSortedList:
               if ptNear(intPt[0], partialIntPt):
                  found = True
                  break
               
            if found == False:
               # inserisco il punto ordinato per distanza dal inizio di part
               distFromStart = part.getDistanceFromStart(partialIntPt)
               insertAt = 0
               for intPt in intPtSortedList:
                  if intPt[1] < distFromStart:
                     insertAt = insertAt + 1
                  else:
                     break                     
               intPtSortedList.insert(insertAt, [partialIntPt, distFromStart, partNumber])
   resultIntPt = []
   resultPartNumber = []
   for intPt in intPtSortedList:
      resultIntPt.append(intPt[0])
      resultPartNumber.append(intPt[2])

   return resultIntPt, resultPartNumber


#===============================================================================
# dualClipping
#===============================================================================
def dualClipping(partList, untrimmedOffsetPartList, untrimmedReversedOffsetPartList, offSetDist):
   """
   la funzione effettua il dual clipping su untrimmedOffsetPartList.
   <partList>: lista delle parti originali della polilinea 
   <untrimmedOffsetPartList>: lista delle parti non tagliate derivate dall'offset
   <untrimmedReversedOffsetPartList>: lista delle parti non tagliate derivate dall'offset in senso inverso
       
   La funzione ritorna una lista di parti risultato del dual clipping 
   """
   
   # inizio Dual Clipping
   dualClippedPartList = QadLinearObjectList()
      
   # linea spezzata sui self intersection points e 
   # sui punti di intersezione con untrimmedReversedOffsetPartList
   
   # per ogni parte di untrimmedOffsetPartList
   for part in untrimmedOffsetPartList.defList:
      # calcola i punti di intersezione di part con untrimmedOffsetPartList ordinati x distanza
      # (self intersection points)     
      dummy = getIntPtListBetweenPartAndPartList_offset(part, untrimmedOffsetPartList)
      intPtList = dummy[0]

      if len(intPtList) > 0:
         # inserisco dividendo part
         intPt = intPtList[0]
         newPart = QadLinearObject(part)      
         newPart.setEndPt(intPt)
         dualClippedPartList.append(newPart)
         i = 1
         while i < len(intPtList):
            newPart = QadLinearObject(part)      
            newPart.setStartPt(intPt)
            intPt = intPtList[i]
            newPart.setEndPt(intPt)
            dualClippedPartList.append(newPart)
            i = i + 1
         newPart = QadLinearObject(part)      
         newPart.setStartPt(intPt)
         dualClippedPartList.append(newPart)            
      else: # inserisco part intera
         dualClippedPartList.append(part)
   
   # ciclo per spezzare dualClippedPartList 
   # sui punti di intersezione con untrimmedReversedOffsetPartList
   i = 0
   while i < dualClippedPartList.qty():
      part = dualClippedPartList.getLinearObjectAt(i)
      # calcola i punti di intersezione di part con untrimmedReversedOffsetPartList ordinati x distanza      
      dummy = getIntPtListBetweenPartAndPartList_offset(part, untrimmedReversedOffsetPartList)   
      intPtList = dummy[0]

      for intPt in intPtList:
         newPart = QadLinearObject(part)
         newPart.setEndPt(intPt)
         dualClippedPartList.insert(i + 1, newPart)           
         newPart = QadLinearObject(part)
         newPart.setStartPt(intPt)
         dualClippedPartList.insert(i + 2, newPart)
         dualClippedPartList.remove(i)
         i = i + 1
            
      i = i + 1

   isClosedPolyline = dualClippedPartList.isClosed() # verifico se polilinea chiusa
   splittedParts = QadLinearObjectList()
   circle = QadCircle()
   i = 0
   # per ogni parte
   while i < dualClippedPartList.qty():
      part = dualClippedPartList.getLinearObjectAt(i)
      # calcola i punti di intersezione con partList      
      dummy = getIntPtListBetweenPartAndPartList_offset(part, partList)
      intPtList = dummy[0]
      partNumberList = dummy[1]
      
      if len(intPtList) > 0:
         if isClosedPolyline:
            firstOrLastPart = False
         else:
            # verifico se tutti i punti di intersezione sono sul primo o sull'ultimo segmento di partList
            firstOrLastPart = True
            for partNumber in partNumberList:
               if partNumber != 0 and partNumber != partList.qty() -1:
                  firstOrLastPart = False
                  break
         
         # se tutti i punti di intersezione sono sul primo o sull'ultimo segmento di partList
         if firstOrLastPart:
            splittedParts.removeAll() # pulisco la lista
            splittedParts.append(QadLinearObject(part))
            for intPt in intPtList:
               j = 0
               while j < splittedParts.qty():
                  splittedPart = splittedParts.getLinearObjectAt(j)               
                  # creo un cerchio nel punto di intersezione
                  circle.set(intPt, offSetDist)
                  # ottengo le parti esterne al cerchio 
                  externalPartsOfIntPt = splittedPart.getPartsExternalToCircle(circle)
                  if externalPartsOfIntPt.qty() > 0:
                     for externalPartOfIntPt in externalPartsOfIntPt.defList:
                        splittedParts.insert(j, externalPartOfIntPt)
                        j = j + 1
                  splittedParts.remove(j)
                            
            # le sostituisco a part
            for splittedPart in splittedParts.defList:
               dualClippedPartList.insert(i, splittedPart)
               i = i + 1
            dualClippedPartList.remove(i)
         else: # se tutti i punti di intersezione non sono sul primo o sull'ultimo segmento di partList
            dualClippedPartList.remove(i)
      else:
         i = i + 1
   
   return dualClippedPartList


#===============================================================================
# generalClosedPointPairClipping
#===============================================================================
def generalClosedPointPairClipping(partList, dualClippedPartList, offSetDist):
   """
   la funzione effettua il general closed point pair clipping su dualClippedPartList.
   <partList>: lista delle parti originali della polilinea 
   <dualClippedPartList>: lista delle parti risultato del dual clipping
   <offSetDist> distanza di offset
       
   La funzione ritorna una lista di parti risultato del dual clipping 
   """
   # inizio di General Closed Point Pair clipping
   GCPPCList = QadLinearObjectList(dualClippedPartList) # duplico la lista di parti      
   circle = QadCircle()
  
   # per ogni parte di partList
   for part in partList.defList:
      # per ogni parte di GCPPCList
      i = 0
      while i < GCPPCList.qty():
         # ripeto finché viene fatto lo split        
         splitted = True
         while splitted:
            splitted = False
            GCPPCPart = GCPPCList.getLinearObjectAt(i)
            # verifico quale é il punto di part più vicino a GCPPCPart
            # (<punto di distanza minima sulla parte 1><punto di distanza minima sulla parte 2><distanza minima>)
            MinDistancePts = part.getMinDistancePtsWithLinearObject(GCPPCPart)
            # se la distanza é inferiore a offSetDist (e non così vicina da essere considerata uguale)
            if MinDistancePts[2] < offSetDist and not doubleNear(MinDistancePts[2], offSetDist):
               # creo un cerchio nel punto di part più vicino a GCPPCPart
               circle.set(MinDistancePts[0], offSetDist)
               # ottengo le parti di GCPPCPart esterne al cerchio 
               splittedParts = GCPPCPart.getPartsExternalToCircle(circle)
               # se la splittedParts è composta da una sola parte che è uguale a GCPPCPart
               # ad es. se GCPPCPart è tangente al cerchio allora non faccio niente
               if splittedParts.qty() == 0 or \
                  splittedParts.qty() == 1 and splittedParts.getLinearObjectAt(0) == GCPPCPart:
                  i = i + 1
               else:
                  # le sostituisco a GCPPCPart
                  for splittedPart in splittedParts.defList:
                     GCPPCList.insert(i, splittedPart)
                     i = i + 1
                  GCPPCList.remove(i)
                  if splittedParts.qty() > 0:
                     splitted = True
                     i = i - splittedParts.qty() # torno alla prima parte risultato dello split
            else:
               i = i + 1
                       
   return GCPPCList


#===============================================================================
# getTrimmedOffSetPartList
#===============================================================================
def getTrimmedOffSetPartList(partList, epsg, untrimmedOffsetPartList, untrimmedReversedOffsetPartList, \
                             offSetDist):
   """
   la funzione taglia la polilinea dove necessario.
   <partList>: lista delle parti originali della polilinea 
   <epsg> = the authority identifier for this srs 
   <untrimmedOffsetPartList>: lista delle parti non tagliate derivate dall'offset
   <untrimmedReversedOffsetPartList>: lista delle partinon tagliate derivate dall'offset in senso inverso
   <offSetDist> distanza di offset
       
   La funzione ritorna una lista di parti della polilinee (lista di segmenti o archi) 
   """
   
   # faccio il dual clipping
   dualClippedPartList = dualClipping(partList, untrimmedOffsetPartList, untrimmedReversedOffsetPartList, offSetDist)
   # test
   #GCPPCList = untrimmedOffsetPartList
   #GCPPCList = dualClipping(partList, untrimmedOffsetPartList, untrimmedReversedOffsetPartList, offSetDist)
     
   # faccio il general closed point pair clipping
   # test
   GCPPCList = generalClosedPointPairClipping(partList, dualClippedPartList, offSetDist)

   # faccio il join tra le parti
   return GCPPCList.selfJoin(epsg)
      
#===============================================================================
# offSetPolyline
#===============================================================================
def offSetPolyline(points, epsg, offSetDist, offSetSide, gapType, tolerance2ApproxCurve = None):
   """
   la funzione fa l'offset di una polilinea (lista di punti = <points>)
   secondo una distanza e un lato di offset ("right" o "left") 
   ed un modo <gapType>:
   0 = Estende i segmenti di linea alle relative intersezioni proiettate
   1 = Raccorda i segmenti di linea in corrispondenza delle relative intersezioni proiettate.
       Il raggio di ciascun segmento di arco é uguale alla distanza di offset
   2 = Cima i segmenti di linea in corrispondenza delle intersezioni proiettate.
       La distanza perpendicolare da ciascuna cima al rispettivo vertice
       sull'oggetto originale é uguale alla distanza di offset.
   <epsg> = the authority identifier for this srs 
   <tolerance2ApproxCurve> = errore minimo di tolleranza
       
   La funzione ritorna una lista di polilinee (lista di liste di punti) 
   """
   if tolerance2ApproxCurve is None:
      tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
   else:
      tolerance = tolerance2ApproxCurve
   
   result = []
   
   pointsLen = len(points)

   # verifico se é un cerchio
   circle = QadCircle()
   startEndVertices = circle.fromPolyline(points, 0)
   if startEndVertices is not None and \
      startEndVertices[0] == 0 and startEndVertices[1] == (pointsLen - 1):
      # siccome i punti del cerchio sono disegnati in senso antiorario
      # se offSetSide = "right" significa verso l'esterno del cerchio
      # se offSetSide = "left" significa verso l'interno del cerchio
      if offSetSide == "left":
         # offset verso l'interno del cerchio
         offSetCircle = getOffSetCircle(circle, offSetDist, "internal")
      else:
         # offset verso l'esterno del cerchio
         offSetCircle = getOffSetCircle(circle, offSetDist, "external")      
      
      if offSetCircle is not None:
         result.append(offSetCircle.asPolyline(tolerance))
         
      return result
   
   # creo una lista dei segmenti e archi che formano la polilinea
   partList = QadLinearObjectList()
   partList.fromPolyline(points)
   # ottengo la polilinea di offset non tagliata
   untrimmedOffsetPartList = getUntrimmedOffSetPartList(partList, offSetDist, offSetSide, gapType, tolerance)
   # inverto il senso dei punti x ottenere la polilinea di offset non tagliata invertita
   reversedPoints = list(points) # duplico la lista
   reversedPoints.reverse()
   reversedPartList = QadLinearObjectList()
   reversedPartList.fromPolyline(reversedPoints)

   untrimmedReversedOffsetPartList = getUntrimmedOffSetPartList(reversedPartList, offSetDist, offSetSide, gapType, tolerance)
   # taglio la polilinea dove necessario
   trimmedOffsetPartList = getTrimmedOffSetPartList(partList, epsg, \
                                                    untrimmedOffsetPartList, \
                                                    untrimmedReversedOffsetPartList, \
                                                    offSetDist)
      
   # ottengo una lista di punti delle nuove polilinee
   result = []
   for trimmedOffsetPart in trimmedOffsetPartList:
      result.append(trimmedOffsetPart.asPolyline())
                  
   return result

#===============================================================================
# getAdjustedRubberBandVertex
#===============================================================================
def getAdjustedRubberBandVertex(vertexBefore, vertex):
   adjustedVertex = QgsPoint(vertex)
         
   # per un baco non ancora capito in QGIS: se la linea ha solo 2 vertici e 
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
def ApproxCurvesOnGeom(geom, atLeastNSegmentForArc = None, atLeastNSegmentForCircle = None,
                       tolerance2ApproxCurve = None):
   """
   ritorna una geometria le cui curve sono approssimate secondo una tolleranza di errore
   atLeastNSegment = numero minimo di segmenti per riconoscere una curva
   tolerance2ApproxCurve = errore minimo di tolleranza
   """   
   if tolerance2ApproxCurve is None:
      tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
   else:
      tolerance = tolerance2ApproxCurve
   
   if atLeastNSegmentForArc is None:
      _atLeastNSegmentForArc = QadVariables.get(QadMsg.translate("Environment variables", "ARCMINSEGMENTQTY"), 12)
   else:
      _atLeastNSegmentForArc = atLeastNSegmentForArc
   
   if atLeastNSegmentForCircle is None:
      _atLeastNSegmentForCircle = QadVariables.get(QadMsg.translate("Environment variables", "CIRCLEMINSEGMENTQTY"), 12)
   else:
      _atLeastNSegmentForCircle = atLeastNSegmentForCircle
   
   g = QgsGeometry(geom) # copio la geometria
   
   # verifico se ci sono archi
   arcList = QadArcList()
   arcList.fromGeom(g, _atLeastNSegmentForArc)
         
   # verifico se ci sono cerchi
   circleList = QadCircleList()
   circleList.fromGeom(g, _atLeastNSegmentForCircle)

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
   if type(pt) == int: # pt é il numero del vertice
      afterVertex = pt
   else:      
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>)
      dummy = closestSegmentWithContext(pt, geom)
      afterVertex = dummy[2]
      if afterVertex is None:
         return None

   arcList = QadArcList()
   circleList = QadCircleList()

   # verifico se pt si riferisce ad un arco
   if arcList.fromGeom(geom) > 0:
      info = arcList.arcAt(afterVertex)
      if info is not None:
         return info[0]
      
   # verifico se pt si riferisce ad un cerchio
   if circleList.fromGeom(geom) > 0:
      info = circleList.circleAt(afterVertex)
      if info is not None:
         return info[0]
      
   # se non é un cerchio é una linea
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
   
   # se D é così vicino a zero 
   if doubleNear(D, 0.0):
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

   # Questa costruzione utilizza una particolare trasformazione geometrica, che alcuni chiamano dilatazione parallela:
   # si immagina che il raggio r del cerchio dato c si riduca a zero (il cerchio é ridotto al suo centro),
   # mentre le rette rimangono parallele con distanze dal centro del cerchio che si é ridotto a zero aumentate o
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
      ptPerp = getPerpendicularPointOnInfinityLine(line1[0], line1[1], circleTan.center)
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

   # Il modo più semplice per risolvere questo problema é quello di utilizzare una particolare 
   # trasformazione geometrica, che alcuni chiamano dilatazione parallela: si immagina che il raggio r 
   # del più piccolo dei cerchi in questione si riduca a zero (il cerchio é ridotto al suo centro), 
   # mentre le rette (risp. gli altri cerchi) rimangono parallele (risp. concentrici) con distanze
   # dal centro del cerchio che si é ridotto a zero (rispettivamente con raggi dei cerchi) aumentati o 
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
      ptPerp = getPerpendicularPointOnInfinityLine(line[0], line[1], circleTan.center)
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
   la funzione ritorna l'inversione circolare di una linea (che é un cerchio)
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
   la funzione ritorna l'inversione circolare di un cerchio (che é un cerchio)
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
   obj1 = whatGeomIs(pt1, geom1)
   obj2 = whatGeomIs(pt2, geom2)

   if (type(obj1) == list or type(obj1) == tuple): # se linea esco
      return None
   obj1Type = obj1.whatIs()
   if obj1Type == "ARC": # se é arco lo trasformo in cerchio
      circle1 = QadCircle()
      circle1.set(obj1.center, obj1.radius)
   else:
      circle1 = QadCircle(obj1)

   if (type(obj2) == list or type(obj2) == tuple): # se linea esco
      return None
   obj2Type = obj2.whatIs()
   if obj2Type == "ARC": # se é arco lo trasformo in cerchio
      circle2 = QadCircle()
      circle2.set(obj2.center, obj2.radius)
   else:
      circle2 = QadCircle(obj2)

   tangents = circle1.getTangentsWithCircle(circle2)
   
   if obj1Type == "ARC" or obj2Type == "ARC":
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
      AvgList.append(getDistance(ptInt, pt2))

      currAvg = numericListAvg(AvgList)           
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
   obj1 = whatGeomIs(tanPt1, tanGeom1)
   obj2 = whatGeomIs(perPt2, perGeom2)

   if (type(obj1) == list or type(obj1) == tuple): # se linea esco
      return None
   obj1Type = obj1.whatIs()
   if obj1Type == "ARC": # se é arco lo trasformo in cerchio
      circle1 = QadCircle()
      circle1.set(obj1.center, obj1.radius)
   else:
      circle1 = QadCircle(obj1)

   if (type(obj2) == list or type(obj2) == tuple):
      obj2Type = "LINE"
   else:
      obj2Type = obj2.whatIs()
      if obj2Type == "ARC": # se é arco lo trasformo in cerchio
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
         pt1 = getPolarPointByPtAngle(circle1.center, angle, -1 * circle1.radius)
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
         
      currAvg = numericListAvg(AvgList)           
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
      if obj1Type == "ARC": # se é arco lo trasformo in cerchio
         circle1 = QadCircle()
         circle1.set(obj1.center, obj1.radius)
      else:
         circle1 = QadCircle(obj1)

   if (type(obj2) == list or type(obj2) == tuple):
      obj2Type = "LINE"
   else:
      obj2Type = obj2.whatIs()
      if obj2Type == "ARC": # se é arco lo trasformo in cerchio
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
         angle = getAngleBy2Pts(circle2.center, ptPer1)
         ptPer2 = getPolarPointByPtAngle(circle2.center, angle, circle2.radius)
         if ptPer1 != ptPer2: # se la linea non é tangente nel punto ptPer2
            lines.append([ptPer1, ptPer2]) 
         ptPer2 = getPolarPointByPtAngle(circle2.center, angle, -1 * circle2.radius)
         if ptPer1 != ptPer2: # se la linea non é tangente nel punto ptPer2
            lines.append([ptPer1, ptPer2]) 
   else:
      if obj2Type == "LINE":
         # linea perpendicolare ad un cerchio e ad una linea 
         ptPer2 = getPerpendicularPointOnInfinityLine(obj2[0], obj2[1], circle1.center)
         angle = getAngleBy2Pts(circle1.center, ptPer2)
         ptPer1 = getPolarPointByPtAngle(circle1.center, angle, circle1.radius)
         if ptPer1 != ptPer2: # se la linea non é tangente nel punto ptPer1
            lines.append([ptPer1, ptPer2]) 
         ptPer1 = getPolarPointByPtAngle(circle1.center, angle, -1 * circle1.radius)
         if ptPer1 != ptPer2: # se la linea non é tangente nel punto ptPer1
            lines.append([ptPer1, ptPer2]) 
      else:
         perPoints1 = circle1.getIntersectionPointsWithInfinityLine(circle1.center, circle2.center)
         perPoints2 = circle2.getIntersectionPointsWithInfinityLine(circle1.center, circle2.center)
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
         
      currAvg = numericListAvg(AvgList)           
      if currAvg < Avg: # mediamente più vicino
         Avg = currAvg
         result = line       
               
   return result


#===============================================================================
# QadLinearObject class
# Classe che definisce un oggetto lineare che può essere un segmento o un arco
#===============================================================================
class QadLinearObject():

   
   def __init__(self, linearObject = None):
      # deflist = (<QgsPoint1> <QgsPoint2>) se si tratta di segmento
      #           (<QadArc> <inverse>) se si tratta di arco
      #           dove <inverse> = True significa che il punto iniziale dell'arco deve essere 
      #           considerato finale nel senso del verso dell'arco
      self.defList = None
      if linearObject is not None:
         self.set(linearObject)

   
   #============================================================================
   # isInitialized
   #============================================================================
   def isInitialized(self):
      """
      la funzione ritorna True se l'oggetto é inizializzato.
      """
      return False if self.defList is None else True


   #============================================================================
   # __eq__
   #============================================================================
   def __eq__(self, other):
      """
      la funzione ritorna True se l'oggetto é uguale a other.
      """
      if self.isInitialized() == False and other.isInitialized() == False:
         return True
      if self.isInitialized() and other.isInitialized():
         if self.isSegment() and other.isSegment():
            return self.getStartPt() == other.getStartPt() and self.getEndPt() == other.getEndPt() 
         elif self.isArc() and other.isArc():
            return self.getArc() == other.getArc()
         else:
            return False
      else:
         return False     
   
   
   #============================================================================
   # clear
   #============================================================================
   def clear(self):
      """
      la funzione pulisce l'oggetto.
      """
      if self.defList is not None:
         del self.defList[:]
         self.defList = None
   
    
   #============================================================================
   # isSegment
   #============================================================================
   def isSegment(self):
      """
      la funzione ritorna True se l'oggetto é  un segmento.
      """
      if self.isInitialized() == False:
         return False
      return True if type(self.defList[0]) == QgsPoint else False


   #============================================================================
   # isArc
   #============================================================================
   def isArc(self):
      """
      la funzione ritorna True se l'oggetto é  un arco.
      """
      if self.isInitialized() == False:
         return False
      return False if type(self.defList[0]) == QgsPoint else True


   #============================================================================
   # isInverseArc
   #============================================================================
   def isInverseArc(self):
      """
      la funzione ritorna True se il punto iniziale dell'arco é da considerare come finale
      nel verso impostato all'arco.
      """
      if self.isArc() == False:
         return False
      return self.defList[1]
   
   
   #============================================================================
   # setInverseArc
   #============================================================================
   def setInverseArc(self, inverse):
      """
      la funzione imposta il verso dell'arco.
      """
      if self.isArc() == False:
         return False
      self.defList[1] = inverse

   
   #============================================================================
   # getArc
   #============================================================================
   def getArc(self):
      """
      la funzione ritorna l'oggetto QadArc.
      """
      if self.isArc() == False:
         return None
      return self.defList[0]

   
   #============================================================================
   # setArc
   #============================================================================
   def setArc(self, arc, inverse):
      """
      la funzione ritorna l'oggetto arco.
      """
      if self.isInitialized():
         del self.defList[:] # svuoto la lista
      self.defList = [QadArc(arc), inverse]

   
   #============================================================================
   # setSegment
   #============================================================================
   def setSegment(self, p1, p2):
      """
      la funzione imposta il segmento.
      """
      if self.isInitialized():
         del self.defList[:] # svuoto la lista
      self.defList = [QgsPoint(p1), QgsPoint(p2)]

   
   #============================================================================
   # set
   #============================================================================
   def set(self, linearObject):
      """
      la funzione imposta l'oggetto come <linearObject>.
      """
      if self.isInitialized():
         del self.defList[:] # svuoto la lista
         
      if type(linearObject) == list or type(linearObject) == tuple: # é una lista
         if type(linearObject[0]) == QgsPoint: # é un segmento
            self.defList = [QgsPoint(linearObject[0]), QgsPoint(linearObject[1])]
         else: # é un arco
            self.defList = [QadArc(linearObject[0]), linearObject[1]]
      else: # é un oggetto QadLinearObject
         if linearObject.isSegment():
            self.defList = [QgsPoint(linearObject.defList[0]), QgsPoint(linearObject.defList[1])]
         else:
            self.defList = [QadArc(linearObject.defList[0]), linearObject.defList[1]]
      
   
   #============================================================================
   # setByGeom
   #============================================================================
   def setByClosestSegmentOfGeom(self, pt, geom):
      """
      la funzione imposta l'oggetto attraverso una geometria di cui si conosce un punto
      nelle vicinanze.
      """
      if self.isInitialized():
         del self.defList[:] # svuoto la lista
   
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      dummy = closestSegmentWithContext(pt, geom)
      if dummy is None or dummy[2] is None:
         return False

      afterVertex = dummy[2]
      # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
      subGeom = getSubGeomAtVertex(geom, afterVertex)[0]
      dummy = closestSegmentWithContext(pt, subGeom)
      afterVertex = dummy[2]
      points = subGeom.asPolyline()

      arcList = QadArcList()
      arcList.fromPoints(points)
            
      # verifico se il punto afterVertex fa parte di un arco
      arcInfo = arcList.arcAt(afterVertex)
      if arcInfo is not None:
         arc = arcInfo[0]
         startEndVertices = arcInfo[1]
         # verifico il verso
         if points[startEndVertices[0]] == arc.getStartPt():
            inverse = False
         else:
            inverse = True
         self.setArc(arc, inverse)
      else:   
         pt1 = points[afterVertex - 1 ]
         pt2 = points[afterVertex]
         if pt1 != pt2: # solo se il punto iniziale é diverso da quello finale
            self.setSegment(pt1, pt2)
   
      return True
   

   #============================================================================
   # getStartPt
   #============================================================================
   def getStartPt(self):
      """
      la funzione ritorna il punto iniziale dell'oggetto.
      """
      if self.isInitialized() == False:
         return None
      if self.isSegment(): # segmento
         return self.defList[0]
      else: # arco
         if self.isInverseArc():
            return self.defList[0].getEndPt()
         else:
            return self.defList[0].getStartPt()
      
   
   #============================================================================
   # setStartPt
   #============================================================================
   def setStartPt(self, pt):
      """
      la funzione imposta il punto iniziale dell'oggetto.
      """
      if self.isInitialized() == False:
         return None
      if self.isSegment(): # segmento
         return self.defList[0].set(pt.x(), pt.y())
      else: # arco
         if self.isInverseArc():
            return self.defList[0].setEndAngleByPt(pt)
         else:
            return self.defList[0].setStartAngleByPt(pt)
      
   
   #============================================================================
   # getEndPt
   #============================================================================
   def getEndPt(self):
      """
      la funzione ritorna il punto finale dell'oggetto.
      """
      if self.isInitialized() == False:
         return None
      if self.isSegment(): # segmento
         return self.defList[1]
      else: # arco
         if self.isInverseArc():
            return self.defList[0].getStartPt()
         else:
            return self.defList[0].getEndPt()    
      
   
   #============================================================================
   # setEndPt
   #============================================================================
   def setEndPt(self, pt):
      """
      la funzione imposta il punto finale dell'oggetto.
      """
      if self.isInitialized() == False:
         return None
      if self.isSegment(): # segmento
         return self.defList[1].set(pt.x(), pt.y())
      else: # arco
         if self.isInverseArc():
            return self.defList[0].setStartAngleByPt(pt)
         else:
            return self.defList[0].setEndAngleByPt(pt)

   
   #============================================================================
   # getStartEndPts
   #============================================================================
   def getStartEndPts(self):
      """
      la funzione ritorna il punto iniziale e finale dell'oggetto.
      """
      return [self.getStartPt(), self.getEndPt()]

   
   #============================================================================
   # setStartEndPts
   #============================================================================
   def setStartEndPts(self, startPt, endPt):
      """
      la funzione imposta il punto iniziale e finale dell'oggetto.
      """
      self.setStartPt(startPt)
      self.setEndPt(endPt)

   
   #============================================================================
   # getTanDirectionOnStartPt
   #============================================================================
   def getTanDirectionOnStartPt(self):
      """
      la funzione ritorna la direzione della tangente al punto iniziale dell'oggetto.
      """
      if self.isSegment(): # segmento
         return getAngleBy2Pts(self.getStartPt(), self.getEndPt())
      else: # se é un arco
         arc = QadArc()
         if self.isInverseArc():
            return self.getArc().getTanDirectionOnEndPt() + math.pi
         else:
            return self.getArc().getTanDirectionOnStartPt()

   
   #============================================================================
   # getTanDirectionOnEndPt
   #============================================================================
   def getTanDirectionOnEndPt(self):
      """
      la funzione ritorna la direzione della tangente al punto finale dell'oggetto.
      """
      if self.isSegment(): # segmento
         return getAngleBy2Pts(self.getStartPt(), self.getEndPt())
      else: # se é un arco
         arc = QadArc()
         if self.isInverseArc():
            return self.getArc().getTanDirectionOnStartPt() + math.pi
         else:
            return self.getArc().getTanDirectionOnEndPt()
            
   
   #============================================================================
   # length
   #============================================================================
   def length(self):
      """
      la funzione restituisce la lunghezza della parte.
      """
      if self.isInitialized() == False:
         return None      
      if self.isSegment(): # segmento
         return getDistance(self.getStartPt(), self.getEndPt())
      else: # arco
         return self.getArc().length()
      

   #============================================================================
   # move
   #============================================================================
   def move(self, offSetX, offSetY):
      """
      la funzione sposta le parti secondo un offset X e uno Y
      """
      if self.isInitialized():
         if self.isSegment(): # segmento
            self.defList[0].set(self.defList[0].x() + offSetX, self.defList[0].y() + offSetY)
            self.defList[1].set(self.defList[1].x() + offSetX, self.defList[1].y() + offSetY)
         else: # arco
            self.getArc().center.set(self.getArc().center.x() + offSetX, self.getArc().center.y() + offSetY)
            
            
   #============================================================================
   # getIntersectionPtsWithLinearObject
   #============================================================================
   def getIntersectionPtsWithLinearObject(self, linearObject):
      """
      la funzione calcola i punti di intersezione tra 2 oggetti lineari.
      Ritorna una lista di punti di intersezione
      """
      if self.isInitialized() == False:
         return None
      if self.isSegment(): # segmento
         if linearObject.isSegment(): # segmento
            ptInt = getIntersectionPointOn2Segments(self.getStartPt(), self.getEndPt(), \
                                                    linearObject.getStartPt(), linearObject.getEndPt())
            if ptInt is not None: # se non sono parallele
               return [ptInt]
            else:
               return []         
         else: # arco
            return linearObject.getArc().getIntersectionPointsWithSegment(self.getStartPt(), self.getEndPt())
      else: # arco
         if linearObject.isSegment(): # segmento
            return self.getArc().getIntersectionPointsWithSegment(linearObject.getStartPt(), linearObject.getEndPt())
         else: # arco
            return self.getArc().getIntersectionPointsWithArc(linearObject.getArc())
      
      return []
                  
   
   #============================================================================
   # getIntersectionPtsOnExtensionWithLinearObject
   #============================================================================
   def getIntersectionPtsOnExtensionWithLinearObject(self, linearObject):
      """
      la funzione calcola i punti di intersezione tra le estensioni di 2 oggetti lineari.
      Un arco diventa un cerchio e un segmento diventa una linea infinita.
      Ritorna una lista di punti di intersezione
      """
      if self.isInitialized() == False:
         return None
      if self.isSegment(): # segmento
         if linearObject.isSegment(): # segmento
            ptInt = getIntersectionPointOn2InfinityLines(self.getStartPt(), self.getEndPt(), \
                                                         linearObject.getStartPt(), linearObject.getEndPt())
            if ptInt is not None: # se non sono parallele
               return [ptInt]
            else:
               return []         
         else: # arco
            circle = QadCircle()
            circle.set(linearObject.getArc().center, linearObject.getArc().radius)
            return circle.getIntersectionPointsWithInfinityLine(self.getStartPt(), self.getEndPt())
      else: # arco
         if linearObject.isSegment(): # segmento
            circle = QadCircle()
            circle.set(self.getArc().center, self.getArc().radius)
            return circle.getIntersectionPointsWithInfinityLine(linearObject.getStartPt(), linearObject.getEndPt())
         else: # arco
            circle1 = QadCircle()
            circle1.set(self.getArc().center, self.getArc().radius)
            circle2 = QadCircle()
            circle2.set(linearObject.getArc().center, linearObject.getArc().radius)
            return circle1.getIntersectionPointsWithCircle(circle2)
      
      return []

   
   #============================================================================
   # getMinDistancePtsWithLinearObject
   #============================================================================
   def getMinDistancePtsWithLinearObject(self, linearObject):
      """
      la funzione ritorna i punti di distanza minima e la distanza minima tra due parti
      (<punto di distanza minima su self><punto di distanza minima su linearObject><distanza minima>)
      """
      if self.isInitialized() == False:
         return None
      if self.isSegment(): # segmento
         if linearObject.isSegment(): # segmento-segmento
            return getMinDistancePtsBetween2Segments(self.getStartPt(), self.getEndPt(), \
                                                     linearObject.getStartPt(), linearObject.getEndPt())
         else: # segmento-arco
            return getMinDistancePtsBetweenSegmentAndArc(self.getStartPt(), self.getEndPt(), \
                                                         linearObject.getArc())            
      else: # arco
         if linearObject.isSegment(): # arco-segmento
            return getMinDistancePtsBetweenSegmentAndArc(linearObject.getStartPt(), linearObject.getEndPt(), \
                                                         self.getArc())
         else: # arco-arco
            return getMinDistancePtsBetween2Arcs(self.getArc(), linearObject.getArc())

   
   #============================================================================
   # getDistanceFromStart
   #============================================================================
   def getDistanceFromStart(self, pt):
      """
      la funzione restituisce la distanza di <pt> (che deve essere sull'oggetto o sua estensione)
      dal punto iniziale.
      """
      if self.isInitialized() == False:
         return None
      
      dummy = QadLinearObject(self)
      dummy.setEndPt(pt)

      # se il punto é sull'estensione dalla parte del punto iniziale      
      if self.containsPt(pt) == False and \
         getDistance(self.getStartPt(), pt) < getDistance(self.getEndPt(), pt):
         return -dummy.length()
         
      return dummy.length()
      

   #============================================================================
   # getPartsExternalToCircle
   #============================================================================
   def getPartsExternalToCircle(self, circle):
      """
      la funzione usa un cerchio per dividere l'oggetto lineare.
      Le parti esterne al cerchio vengono restituite
      nell'ordine dal punto iniziale a quello finale dell'oggetto linear.
      """
      if self.isInitialized() == False:
         return None
      result = QadLinearObjectList()

      startPt = self.getStartPt()
      endPt = self.getEndPt()
      
      if self.isSegment(): # segmento
         intPtList = circle.getIntersectionPointsWithSegment(startPt, endPt)
      else: # arco
         intPtList = self.getArc().getIntersectionPointsWithCircle(circle)
      
      intPtSortedList = []
      for pt in intPtList:
         # inserisco il punto ordinato per distanza dall'inizio di part
         distFromStart = self.getDistanceFromStart(pt)
         insertAt = 0
         for intPt in intPtSortedList:
            if intPt[1] < distFromStart:
               insertAt = insertAt + 1
            else:
               break                     
         intPtSortedList.insert(insertAt, [pt, distFromStart])
   
      del intPtList[:] # svuoto la lista
      for intPt in intPtSortedList:
         intPtList.append(intPt[0])
   
      startPtFromCenter = getDistance(circle.center, startPt) 
      endPtFromCenter = getDistance(circle.center, endPt)
      intPtListLen = len(intPtList)
      if intPtListLen == 0: # se non ci sono punti di intersezione
         # se entrambi i punti terminali della parte sono esterni al cerchio
         if startPtFromCenter >= circle.radius and endPtFromCenter >= circle.radius:
            result.append(QadLinearObject(self))      
      elif intPtListLen == 1: # se c'é un solo punto di intersezione
         # se entrambi i punti terminali della parte sono esterni al cerchio
         if startPtFromCenter >= circle.radius and endPtFromCenter >= circle.radius:
            result.append(QadLinearObject(self))      
         # se il primo punto della parte é interno e il secondo esterno al cerchio
         elif startPtFromCenter < circle.radius and endPtFromCenter > circle.radius:
            newLinearobj = QadLinearObject(self)
            newLinearobj.setStartPt(intPtList[0]) 
            result.append(newLinearobj)      
         # se il primo punto della parte é esterno e il secondo interno al cerchio
         elif startPtFromCenter > circle.radius and endPtFromCenter < circle.radius:
            newLinearobj = QadLinearObject(self)
            newLinearobj.setEndPt(intPtList[0]) 
            result.append(newLinearobj)      
      else : # se ci sono due punti di intersezione
         # se il primo punto della parte é esterno al cerchio
         if startPtFromCenter > circle.radius:
            newLinearobj = QadLinearObject(self)
            newLinearobj.setEndPt(intPtList[0]) 
            result.append(newLinearobj)      
         # se il secondo punto della parte é esterno al cerchio
         if endPtFromCenter > circle.radius:
            newLinearobj = QadLinearObject(self)
            newLinearobj.setStartPt(intPtList[1]) 
            result.append(newLinearobj)      
   
      return result


   #============================================================================
   # reverse
   #============================================================================
   def reverse(self):
      """
      la funzione rovescia il verso dell'oggetto lineare.
      """
      if self.isInitialized() == False:
         return self      
      if self.isSegment(): # segmento
         ptStart = QgsPoint(self.getStartPt())
         ptEnd = QgsPoint(self.getEndPt())
         self.setStartEndPts(ptEnd, ptStart)
      else: # arco
         self.setInverseArc(not self.isInverseArc())
      return self
      

   #============================================================================
   # containsPt
   #============================================================================
   def containsPt(self, pt):
      """
      la funzione ritorna True se il punto si trova sull'oggetto lineare.
      """
      if self.isInitialized() == False:
         return False      
      if self.isSegment(): # segmento
         return isPtOnSegment(self.getStartPt(), self.getEndPt(), pt)
      else: # arco
         return self.getArc().isPtOnArc(pt)
      

   #============================================================================
   # join
   #============================================================================
   def join(self, linearObject):
      """
      la funzione restituisce una lista QadLinearObjectList che contiene la polilinea
      generata dall'unione di questo oggetto lineare con <linearObject> se possibile
      altrimenti None.
      """
      if self.getEndPt() == linearObject.getStartPt():
         result = QadLinearObjectList()
         result.append(QadLinearObject(self))
         result.append(QadLinearObject(linearObject))
         return result
      elif self.getStartPt() == linearObject.getEndPt():
         result = QadLinearObjectList()
         result.append(QadLinearObject(linearObject))
         result.append(QadLinearObject(self))
         return result
      else:
          return None

      
   #===============================================================================
   # asPolyline
   #===============================================================================
   def asPolyline(self, tolerance2ApproxCurve = None):
      """
      la funzione ritorna una lista di punti che compone l'oggetto lineare.
      """
      if self.isSegment(): # segmento
         result = [self.getStartPt(), self.getEndPt()]
      else: # arco
         result = self.getArc().asPolyline(tolerance2ApproxCurve)
         if self.isInverseArc(): # l'arco é in senso inverso
            result.reverse()
                     
      return result


   #===============================================================================
   # transform
   #===============================================================================
   def transform(self, coordTransform):
      """
      la funzione trasforma le coordinate dei punti che compone l'oggetto lineare.
      """
      result = QadLinearObject(self)
      if result.isSegment(): # segmento
         result.setStartPt(coordTransform.transform(result.getStartPt()))
         result.setEndPt(coordTransform.transform(result.setEndPt()))
      else: # arco
         result.getArc().transform(coordTransform)
          
      return result
      

   #===============================================================================
   # transformFromCRSToCRS
   #===============================================================================
   def transformFromCRSToCRS(self, sourceCRS, destCRS):
      """
      la funzione trasforma le coordinate dei punti che compone l'oggetto lineare.
      """
      return transform(QgsCoordinateTransform(sourceCRS, destCRS))

   
   #============================================================================
   # leftOf
   #============================================================================
   def leftOf(self, point):
      """
      la funzione ritorna una numero < 0 se il punto é alla sinistra della parte lineare
      """
      if self.isSegment(): # segmento
         return leftOfLine(point, self.getStartPt(), self.getEndPt())
      else:
         if getDistance(self.getArc().center, point) - self.getArc().radius > 0:
            # esterno all'arco
            if self.isInverseArc(): # l'arco é in senso inverso
               return -1 # a sinistra
            else:
               return 1 # a destra
         else: 
            # interno all'arco
            if self.isInverseArc(): # l'arco é in senso inverso
               return 1 # a destra
            else:
               return -1 # a sinistra


   #===============================================================================
   # closestPtWithContext
   #===============================================================================
   def closestPtWithContext(self, point, epsilon = 1.e-15):
      """
      la funzione ritorna una lista con 
      (<minima distanza al quadrato>
       <punto più vicino>
       <"a sinistra di" se il punto é alla sinista della parte (< 0 -> sinistra, > 0 -> destra)
      """
      if self.isSegment(): # segmento
         startPt = self.getStartPt()
         endPt = self.getEndPt()
         result = sqrDistToSegment(point, startPt.x(), startPt.y(), endPt.x(), endPt.y(), epsilon)
      else: # arco
         result = sqrDistToArc(point, self.getArc())

      return result[0], result[1], self.leftOf(point)
   
   
   #===============================================================================
   # breakOnPt
   #===============================================================================
   def breakOnPt(self, point):
      """
      la funzione spezza in due la parte nel punto <point>.
      Ritorna una lista di due parti: la prima parte (che può essere
      nulla se <point> conicide con il punto iniziale) e la seconda parte (che può essere
      nulla se <point> conicide con il punto finale)
      """
      dummy = self.closestPtWithContext(point)
      nearestPt = dummy[1]
      if nearestPt is None:
         return [None, None]
      
      if ptNear(nearestPt, self.getStartPt()):
         part1 = None
      else:
         part1 = QadLinearObject(self)
         part1.setEndPt(nearestPt)

      if ptNear(nearestPt, self.getEndPt()):
         part2 = None
      else:
         part2 = QadLinearObject(self)
         part2.setStartPt(nearestPt)

      return [part1, part2]


#===============================================================================
# QadLinearObjectList class
# Classe che definisce una lista di oggetti lineari che può essere una polilinea
#===============================================================================
class QadLinearObjectList():

   
   def __init__(self, linearObjectList = None):
      self.defList = []
      # deflist = (<QadLinearObject1><QadLinearObject2>...)
      if linearObjectList is not None:
         self.set(linearObjectList)

   
   #============================================================================
   # set
   #============================================================================
   def set(self, linearObjectList):
      self.removeAll()
      for linearObject in linearObjectList.defList:            
         self.append(linearObject)


   #============================================================================
   # append
   #============================================================================
   def append(self, linearObject):
      """
      la funzione aggiunge un oggetto lineare in fondo alla lista.
      """
      return self.defList.append(QadLinearObject(linearObject))


   #============================================================================
   # appendList
   #============================================================================
   def appendList(self, linearObjectList, start = None, qty = None):
      """
      la funzione aggiunge una lista di oggetti lineari in fondo alla lista.
      Se start diverso da None significa numero della parte di <linearObjectList> da cui iniziare. 
      Se <qty> diverso da None significa numero delle parti di <linearObjectList> da aggiungere,
      se = None significa fino alla fine di <linearObjectList>.
      """
      if start is None:
         for linearObject in linearObjectList.defList:
            self.append(linearObject)
      else:
         i = start
         if qty is None:
            tot = linearObjectList.qty()
         else:
            tot = linearObjectList.qty() if qty > linearObjectList.qty() else qty

         while i < tot:
            self.append(linearObjectList.defList[i])
            i = i + 1

   
   #============================================================================
   # insert
   #============================================================================
   def insert(self, partAt, linearObject):
      """
      la funzione aggiunge un oggetto lineare nella posizione i-esima della lista.
      """
      if partAt >= self.qty():
         return self.append(linearObject)
      else:         
         return self.defList.insert(partAt, QadLinearObject(linearObject))


   #============================================================================
   # insertList
   #============================================================================
   def insertList(self, i, linearObjectList):
      """
      la funzione aggiunge una lista di oggetti lineari nella posizione i-esima della lista.
      """
      ndx = i 
      for linearObject in linearObjectList.defList:
         self.insert(ndx, linearObject)
         ndx = ndx + 1


   #============================================================================
   # insertPoint
   #============================================================================
   def insertPoint(self, partAt, pt):
      """
      la funzione aggiunge un punto tra il punto iniziale e finale della parte i-esima della lista.
      se i < 0 aggiunge il punto all'inizio della polilinea
      se i >= qty() aggiunge il punto alla fine della polilinea
      """
      if partAt < 0: # inserisco parte all'inizio
         self.insert(0, [pt, self.getStartPt()])
      elif partAt >= self.qty(): # inserisco parte in fondo
         self.append([self.getEndPt(), pt])
      else:
         linearObject = self.getLinearObjectAt(partAt)

         if linearObject.isArc():
            arc = QadArc()
            if linearObject.isInverseArc():
               if arc.fromStartEndPtsAngle(pt, linearObject.getArc().getEndPt(), \
                                           linearObject.getArc().totalAngle()) == False:
                  return
            else:
               if arc.fromStartEndPtsAngle(linearObject.getArc().getStartPt(), pt, \
                                           linearObject.getArc().totalAngle()) == False:
                  return
               
            self.insert(partAt, [arc, linearObject.isInverseArc()])               
         else:
            self.insert(partAt, [linearObject.getStartPt(), pt])
            
         linearObject = self.getLinearObjectAt(partAt + 1)
         linearObject.set([pt, linearObject.getEndPt()])


   #============================================================================
   # movePoint
   #============================================================================
   def movePoint(self, vertexAt, pt):
      """
      la funzione sposta un punto tra il punto iniziale e finale della parte i-esima della lista.
      se i < 0 aggiunge il punto all'inizio della polilinea
      se i >= qty() aggiunge il punto alla fine della polilinea
      """
      prevLinearObject, nextLinearObject = self.getPrevNextLinearObjectsAtVertex(vertexAt)
      
      if prevLinearObject is not None:
         if prevLinearObject.isArc():
            if ptNear(prevLinearObject.getArc().getStartPt(), prevLinearObject.getEndPt()):
               # sposto il punto iniziale dell'arco
               if prevLinearObject.getArc().fromStartEndPtsAngle(pt, \
                                                                 prevLinearObject.getArc().getEndPt(), \
                                                                 prevLinearObject.getArc().totalAngle()) == False:
                  return
            else:
               # sposto il punto finale dell'arco
               if prevLinearObject.getArc().fromStartEndPtsAngle(prevLinearObject.getArc().getStartPt(), \
                                                                 pt, \
                                                                 prevLinearObject.getArc().totalAngle()) == False:
                  return
         else:
            prevLinearObject.setEndPt(pt)
            
      if nextLinearObject is not None:
         if nextLinearObject.isArc():
            if ptNear(nextLinearObject.getArc().getStartPt(), nextLinearObject.getStartPt()):
               # sposto il punto iniziale dell'arco
               if nextLinearObject.getArc().fromStartEndPtsAngle(pt, \
                                                                 nextLinearObject.getArc().getEndPt(), \
                                                                 nextLinearObject.getArc().totalAngle()) == False:
                  return
            else:
               # sposto il punto finale dell'arco
               if nextLinearObject.getArc().fromStartEndPtsAngle(nextLinearObject.getArc().getStartPt(), \
                                                                 pt, \
                                                                 nextLinearObject.getArc().totalAngle()) == False:
                  return
         else:
            nextLinearObject.setStartPt(pt)

   
   #============================================================================
   # remove
   #============================================================================
   def remove(self, i):
      """
      la funzione cancella un oggetto lineare nella posizione i-esima della lista.
      """
      del self.defList[i]

   
   #============================================================================
   # removeAll
   #============================================================================
   def removeAll(self):
      """
      la funzione cancella gli oggetti della lista.
      """
      del self.defList[:]


   #============================================================================
   # getLinearObjectAt
   #============================================================================
   def getLinearObjectAt(self, i):
      """
      la funzione restituisce l'oggetto lineare alla posizione i-esima 
      con numeri negativi parte dal fondo (es. -1 = ultima posizione)
      """
      if self.qty() == 0 or i > self.qty() - 1:
         return None
      return self.defList[i]


   #============================================================================
   # getVertexPosAtPt
   #============================================================================
   def getVertexPosAtPt(self, pt):
      """
      la funzione restituisce la posizione del vertice con coordinate <pt> (0-based),
      None se non trovato.
      """
      vertexAt = 0
      for linearObject in self.defList:
         if ptNear(linearObject.getStartPt(), pt):
            return vertexAt
         vertexAt = vertexAt + 1
      if self.isClosed() == False: # se non é chiusa verifico ultimo vertice dell'ultima parte
         if ptNear(self.defList[-1].getEndPt(), pt):
            return vertexAt
         
      return None


   #============================================================================
   # getPrevNextLinearObjectsAtVertex
   #============================================================================
   def getPrevNextLinearObjectsAtVertex(self, vertexAt):
      """
      la funzione restituisce l'oggetto lineare precedente e successivo al vertice vertexAt-esimo
      """
      prevLinearObject = None
      nextLinearObject = None
      
      if vertexAt == 0: # primo vertice
         nextLinearObject = self.getLinearObjectAt(0)          
         if self.isClosed():
            prevLinearObject = self.getLinearObjectAt(-1)
      elif vertexAt == self.qty(): # ultimo vertice
         prevLinearObject = self.getLinearObjectAt(-1)          
         if self.isClosed():
            nextLinearObject = self.getLinearObjectAt(0)
      else:
         nextLinearObject = self.getLinearObjectAt(vertexAt)
         prevLinearObject = self.getLinearObjectAt(vertexAt - 1)

      return prevLinearObject, nextLinearObject


   #============================================================================
   # getPointAtVertex
   #============================================================================
   def getPointAtVertex(self, vertexAt):
      """
      la funzione restituisce il punto del vertice vertexAt-esimo che compone la polilinea.
      """
      if vertexAt == self.qty(): # ultimo vertice
         return self.getLinearObjectAt(-1).getEndPt()          
      else:
         return self.getLinearObjectAt(vertexAt).getStartPt()


   #============================================================================
   # getNextPos
   #============================================================================
   def getNextPos(self, i):
      """
      la funzione restituisce la posizione della parte successiva all' i-esima (0-based) 
      """      
      if i == self.qty() - 1 or i == -1: # sono alla fine
         if self.isClosed(): # se é chiusa torno all'inizio
            return 0
         else:
            return None
      else:
         return i + 1


   #============================================================================
   # getPrevPos
   #============================================================================
   def getPrevPos(self, i):
      """
      la funzione restituisce la posizione della parte precedente all' i-esima (0-based) 
      """      
      if i == 0: # sono all'inizio
         if self.isClosed(): # se é chiusa torno alla fine
            return self.qty() - 1
         else:
            return None
      else:
         return i - 1


   #============================================================================
   # fromPolyline
   #============================================================================
   def fromPolyline(self, points):
      """
      la funzione inizializza una lista di segmenti e archi (QadLinearObject) 
      che compone la polilinea.
      Se una parte ha punto iniziale e finale coincidenti (es. 2 vertici consecutivi 
      che si sovrappongono o arco con angolo totale = 0 oppure = 360)
      la parte viene rimossa dalla lista.
      """
      pointsLen = len(points)
      arcList = QadArcList()
      arcList.fromPoints(points)
   
      # creo una lista dei segmenti e archi che formano la polilinea
      del self.defList[:] # svuoto la lista
         
      i = 0
      while i < pointsLen - 1:   
         # verifico il punto i + 1 fa parte di un arco
         arcInfo = arcList.arcAt(i + 1)
         if arcInfo is not None:
            arc = arcInfo[0]
            if arc.getStartPt() != arc.getEndPt():
               # se i punti sono così vicini da essere considerati uguali         
               inverse = False if ptNear(points[i], arc.getStartPt()) else True
               self.append([arc, inverse])
            startEndVertices = arcInfo[1]
            endVertex = startEndVertices[1]
            i = endVertex
         else:
            pt1 = points[i]
            pt2 = points[i + 1]
            self.append([pt1, pt2])
            i = i + 1
   
      return
      

   #===============================================================================
   # asPolyline
   #===============================================================================
   def asPolyline(self, tolerance2ApproxCurve = None):
      """
      la funzione ritorna una lista di punti che compone la polilinea formata da una lista di
      parti di segmenti e archi (QadLinearObject) consecutive.
      """
      result = []
      firstPt = True
      for linearObject in self.defList:
         pts = linearObject.asPolyline(tolerance2ApproxCurve)
         ptsLen = len(pts)
         if firstPt:
            i = 0
            firstPt = False
         else:
             i = 1
         while i < ptsLen:
            result.append(pts[i])
            i = i + 1
                     
      return result
      

   #===============================================================================
   # reverse
   #===============================================================================
   def reverse(self):
      """
      la funzione rovescia il verso di una lista di
      parti di segmenti e archi (QadLinearObject) consecutive.
      """
      self.defList.reverse()
      for linearObject in self.defList:
         linearObject.reverse()
      return   
 

   #============================================================================
   # length
   #============================================================================
   def length(self):
      """
      la funzione restituisce la somma delle lunghezze della parti.
      """
      tot = 0
      for linearObject in self.defList:
         tot = tot + linearObject.length()
      return tot


   #============================================================================
   # move
   #============================================================================
   def move(self, offSetX, offSetY):
      """
      la funzione sposta le parti secondo un offset X e uno Y
      """
      for linearObject in self.defList:
         linearObject.move(offSetX, offSetY)


   #============================================================================
   # qty
   #============================================================================
   def qty(self):
      """
      la funzione restituisce la quantità di parti nella lista.
      """
      return len(self.defList)
   

   #============================================================================
   # getStartPt
   #============================================================================
   def getStartPt(self):
      """
      la funzione restituisce il punto iniziale della polilinea.
      """
      linearObject = self.getLinearObjectAt(0) # primo oggetto lineare
      return None if linearObject is None else linearObject.getStartPt()


   #============================================================================
   # getEndPt
   #============================================================================
   def getEndPt(self):
      """
      la funzione restituisce il punto finale della polilinea.
      """
      linearObject = self.getLinearObjectAt(-1) # ultimo oggetto lineare
      return None if linearObject is None else linearObject.getEndPt()


   #============================================================================
   # isClosed
   #============================================================================
   def isClosed(self):
      """
      la funzione restituisce True se la polilinea (lista di parti segmenti-archi) é chiusa.
      """
      if len(self.defList) == 0:
         return False
      else:
         return True if ptNear(self.getStartPt(), self.getEndPt()) else False


   #============================================================================
   # setClose
   #============================================================================
   def setClose(self, toClose = True):
      """
      la funzione chiude o apre la polilinea (lista di parti segmenti-archi).
      """
      if toClose: # da chiudere
         if self.isClosed() == False:
            linearObject = self.getLinearObjectAt(-1)
            if linearObject.isArc(): # se é un arco
               arc = QadArc()
               if linearObject.isInverseArc():
                  if arc.fromStartEndPtsTan(linearObject.getArc().getStartPt(), \
                                            self.getStartPt(), \
                                            linearObject.getArc().getTanDirectionOnStartPt() + math.pi) == False:
                     return
               else:
                  if arc.fromStartEndPtsTan(linearObject.getArc().getEndPt(), \
                                            self.getStartPt(), \
                                            linearObject.getArc().getTanDirectionOnEndPt()) == False:
                     return
                  
               newLinearObject = QadLinearObject()
               newLinearObject.setArc(arc, linearObject.isInverseArc())
               self.append(newLinearObject)
            else: # non é un arco
               if self.qty() > 1:
                  self.append([self.getEndPt(), self.getStartPt()])               
      else: # da aprire
         if self.isClosed() == True:
            if self.qty() > 1:
               self.remove(-1)


   #============================================================================
   # curve
   #============================================================================
   def curve(self, toCurve = True):
      """
      se toCurve = True:
      la funzione curva ogni segmento per adattarlo alla polilinea (lista di parti segmenti-archi)
      facendo passare la nuova polilinea per i vertici.
      se toCurve = False:
      la funzione trasforma in segmento retto ogni arco della polilinea (lista di parti segmenti-archi).
      """
      if toCurve == False:
         if self.getCircle() is not None: # se é un cerchio
            return
   
         for linearObject in self.defList:
            if linearObject.isArc():
               linearObject.set([linearObject.getStartPt(), linearObject.getEndPt()])
         return
            
      tot = self.qty()
      if tot < 2:
         return
      isClosed = self.isClosed()
      if isClosed:
         if self.getCircle() is not None: # se é un cerchio
            return

      newLinearObjectList = QadLinearObjectList()

      # primo oggetto lineare
      current = self.getLinearObjectAt(0)         
      prev = None 
      tanDirectionOnStartPt = None
      if isClosed:
         prev = self.getLinearObjectAt(-1)
         arc = QadArc()
         if arc.fromStartSecondEndPts(prev.getStartPt(), current.getStartPt(), current.getEndPt()):
            if ptNear(prev.getStartPt(), arc.getStartPt()): # arco non é inverso                  
               arc.setStartAngleByPt(current.getStartPt())
               tanDirectionOnStartPt = arc.getTanDirectionOnStartPt()
            else: # arco é inverso
               arc.setEndAngleByPt(current.getStartPt())
               tanDirectionOnStartPt = arc.getTanDirectionOnEndPt() + math.pi
            
      next = self.getLinearObjectAt(1)
      newLinearObjectList.defList.extend(getCurveLinearObjects(tanDirectionOnStartPt, prev, current, next))
         
      i = 1
      while i < tot - 1:
         tanDirectionOnStartPt = newLinearObjectList.getLinearObjectAt(-1).getTanDirectionOnEndPt()
         prev = current
         current = next         
         next = self.getLinearObjectAt(i + 1)
         newLinearObjectList.defList.extend(getCurveLinearObjects(tanDirectionOnStartPt, prev, current, next))
         i = i + 1

      # ultimo oggetto lineare
      tanDirectionOnStartPt = newLinearObjectList.getLinearObjectAt(-1).getTanDirectionOnEndPt()
      prev = current
      current = next         
      next = self.getLinearObjectAt(0) if isClosed else None
      newLinearObjectList.defList.extend(getCurveLinearObjects(tanDirectionOnStartPt, prev, current, next))
          
      self.set(newLinearObjectList)  


   #============================================================================
   # fillet
   #============================================================================
   def fillet(self, radius):
      """
      la funzione raccorda ogni segmento al successivo con un raggio di curvatura noto,
      la nuova polilinea avrà i vertici cambiati.
      """
      if radius <= 0:
         return
      newLinearObjectList = QadLinearObjectList()

      part = self.getLinearObjectAt(0)
      i = 1
      tot = self.qty()
      while i <= tot - 1:
         nextPart = self.getLinearObjectAt(i)
         if part.isSegment() and nextPart.isSegment():
            # Ritorna una lista di 3 elementi (None in caso di errore):   
            # - una linea che sostituisce <line1>, se = None <line1> va rimossa
            # - un arco, se = None non c'é arco di raccordo tra le due linee
            # - una linea che sostituisce <line2>, se = None <line2> va rimossa
            res = offsetBridgeTheGapBetweenLines(part, nextPart, radius, 1)
            if res is None:
               return
            if res[0] is not None:
               part = res[0]
               newLinearObjectList.append(part)
            if res[1] is not None:
               part = res[1]
               newLinearObjectList.append(part)
            if res[2] is not None:
               part = res[2]
         else:
            # offSetSide = "left" or "right"
            res = fillet2Parts_offset(part, nextPart, offSetSide, radius)
         i = i + 1

      if self.isClosed():
         nextPart = newLinearObjectList.getLinearObjectAt(0)
         if part.isSegment() and nextPart.isSegment():
            # Ritorna una lista di 3 elementi (None in caso di errore):   
            # - una linea che sostituisce <line1>, se = None <line1> va rimossa
            # - un arco, se = None non c'é arco di raccordo tra le due linee
            # - una linea che sostituisce <line2>, se = None <line2> va rimossa
            res = offsetBridgeTheGapBetweenLines(part, nextPart, radius, 1)
            if res is None:
               return
            if res[0] is not None:
               part = res[0]
               newLinearObjectList.append(part)
            if res[1] is not None:
               part = res[1]
               newLinearObjectList.append(part)
            if res[2] is not None:
               part = res[2]
            self.remove(0)         
      else:
         newLinearObjectList.append(part)         
           
      self.set(newLinearObjectList)  
     

   #============================================================================
   # getCircle
   #============================================================================
   def getCircle(self):
      """
      la funzione ritorna l'oggetto cerchio.
      """
      points = self.asPolyline() # vettore di punti
      circle = QadCircle()
      return circle if circle.fromPolyline(points, 0) is not None else None


   #============================================================================
   # getDistanceFromStart
   #============================================================================
   def getDistanceFromStart(self, pt):
      """
      la funzione restituisce la distanza di <pt> (che deve essere sull'oggetto) dal punto iniziale.
      Da usarsi solo se le parti rappresentano una polilinea.
      """
      tot = 0      
      for linearObject in self.defList:
         if linearObject.containsPt(pt) == True:
            return tot + linearObject.getDistanceFromStart(pt)
         else:
            tot = tot + linearObject.length()
         
      return -1


   #============================================================================
   # asQgsFeatureList
   #============================================================================
   def asQgsFeatureList(self, polylineMode):
      """
      la funzione restituisce una lista di feature.
      Se polylineMode = True allora la lista degli oggetti lineari sarà considerata un'unica polilinea
      """
      fList = []
      if polylineMode == False:
         for linearObject in self.defList:
           f = QgsFeature()
           f.setGeometry(QgsGeometry.fromPolyline(linearObject.asPolyline()))
           fList.append(f)
      else:
         f = QgsFeature()
         f.setGeometry(QgsGeometry.fromPolyline(self.asPolyline()))
         fList.append(f)
      
      return fList


   #============================================================================
   # appendToTempQgsVectorLayer
   #============================================================================
   def appendToTempQgsVectorLayer(self, vectorLayer, polylineMode, updateExtents = True):
      """
      la funzione inserisce gli oggetti lineari in lista in un QgsVectorLayer temporaneo già creato.
      Se polylineMode = True allora la lista degli oggetti lineari sarà considerata un'unica polilinea
      Ritorna la lista dei corrispettivi id di feature oppure None in caso di errore
      """
      fList = self.asQgsFeatureList(polylineMode)
      
      idList = []
      result = True
      if vectorLayer.startEditing() == False:
         return None
         
      vectorLayer.beginEditCommand("Feature added")
      
      for f in fList:
         if vectorLayer.addFeature(f):
            idList.append(f.id())
         else:
            result = False
            break

      if result == True:
         vectorLayer.endEditCommand();
         if updateExtents:
            vectorLayer.updateExtents()
         return idList
      else:
         vectorLayer.destroyEditCommand()
         return None


   #===============================================================================
   # getIntersectionPtsWithLinearObject
   #===============================================================================
   def getIntersectionPtsWithLinearObject(self, part, orderByStartPtOfPart = False):
      """
      la funzione restituisce diverse liste:
      - la prima é una lista di punti di intersezione tra la parte <part> e
      la lista di parti ordinata per distanza dal punto iniziale di <part> se
      <orderByStartPtOfPart> = True altrimenti ordinata per distanza dal punto iniziale
      della lista di parti.
      - la seconda é una lista che contiene, rispettivamente per ogni punto di intersezione,
      il numero della parte (0-based) della lista di parti in cui si trova quel punto.
      - la terza é una lista che contiene, rispettivamente per ogni punto di intersezione,
      la distanza dal punto iniziale di <part> o dal punto iniziale della lista di parti
      (vedi <orderByStartPtOfPart>)
      <part>: un segmento o arco 
      """      
      intPtSortedList = [] # lista di ((punto, distanza dall'inizio della parte) ...)
      partNumber = -1
      if orderByStartPtOfPart == False:
         distFromStartPrevParts = 0
         
      # per ogni parte della lista
      for part2 in self.defList:
         partNumber = partNumber + 1
         partialIntPtList = part.getIntersectionPtsWithLinearObject(part2)
         for partialIntPt in partialIntPtList:
            # escludo i punti che sono già in intPtSortedList
            found = False
            for intPt in intPtSortedList:
               if ptNear(intPt[0], partialIntPt):
                  found = True
                  break
               
            if found == False:
               if orderByStartPtOfPart:
                  # inserisco il punto ordinato per distanza dall'inizio di part
                  distFromStart = part.getDistanceFromStart(partialIntPt)
               else:
                  distFromStart = distFromStartPrevParts + part2.getDistanceFromStart(partialIntPt)
                  
               insertAt = 0
               for intPt in intPtSortedList:
                  if intPt[1] < distFromStart:
                     insertAt = insertAt + 1
                  else:
                     break                     
               intPtSortedList.insert(insertAt, [partialIntPt, distFromStart, partNumber])
            
         if orderByStartPtOfPart == False:
            distFromStartPrevParts = distFromStartPrevParts + part2.length()
         
      resultIntPt = []
      resultPartNumber = []
      resultDistanceFromStart = []
      for intPt in intPtSortedList:
         resultIntPt.append(intPt[0])
         resultPartNumber.append(intPt[2])
         resultDistanceFromStart.append(intPt[1])
   
      return resultIntPt, resultPartNumber, resultDistanceFromStart


   #===============================================================================
   # getIntersectionPtsWithLinearObjectlist
   #===============================================================================
   def getIntersectionPtsWithLinearObjectList(self, partList):
      """
      la funzione restituisce diverse liste:
      - la prima é una lista di punti di intersezione tra le 2 liste di parti
      ordinata per distanza dal punto iniziale della lista.
      - la seconda é una lista che contiene, rispettivamente per ogni punto di intersezione,
      il numero della parte (0-based) della lista di parti in cui si trova quel punto.
      - la terza é una lista che contiene, rispettivamente per ogni punto di intersezione,
      la distanza dal punto iniziale della lista.
      <partList>: lista di parti       
      """
      resultIntPt = []
      resultPartNumber = []
      resultDistanceFromStart = []
      
      # per ogni parte della lista
      for part in self.defList:
         # lista di punti di intersezione ordinata per distanza dal punto iniziale di <part>
         partialResult = partList.getIntersectionPtsWithLinearObject(part, True)
         resultIntPt.extend(partialResult[0])
         resultPartNumber.extend(partialResult[2])
         resultDistanceFromStart.extend(partialResult[1])
         
      return resultIntPt, resultPartNumber, resultDistanceFromStart


   #============================================================================
   # join
   #============================================================================
   def join(self, linearObjectListToJoinTo, toleranceDist = 1.e-9, mode = 1):
      """
      la funzione unisce la polilinea con un'altra polilinea secondo la modalità <mode>.
      In caso di successo ritorna True altrimenti False.
      <linearObjectListToJoinTo> = polilinea con cui unirsi
      <toleranceDist> = distanza di tolleranza perché 2 punti siano considerati coincidenti  
      <mode> = Imposta il metodo di unione (usato se toleranceDist > 0):
               1 -> Estendi;  Consente di unire polilinee selezionate estendendo o tagliando 
                              i segmenti nei punti finali più vicini.
               2 -> Aggiungi; Consente di unire polilinee selezionate aggiungendo un segmento 
                              retto tra i punti finali più vicini.
               3 -> Entrambi;Consente di unire polilinee selezionate estendendo o tagliando, se possibile.
                    In caso contrario, consente di unire polilinee selezionate aggiungendo 
                    un segmento retto tra i punti finali più vicini. 
      """
      myToleranceDist = 1.e-9 if toleranceDist == 0 else toleranceDist
      # cerco il punto più vicino al punto iniziale della polilinea
      ptToJoin = self.getStartPt()
      isStartPt = True
      minDist = sys.float_info.max
      # considero il punto iniziale della polilinea a cui unirsi
      if linearObjectListToJoinTo.getStartPt() is None: # roby test
         fermati = True
      dist = getDistance(ptToJoin, linearObjectListToJoinTo.getStartPt())
      if dist < minDist:
         isStartPtToJoinTo = True
         minDist = dist
      # considero il punto finale della polilinea a cui unirsi
      dist = getDistance(ptToJoin, linearObjectListToJoinTo.getEndPt())
      if dist < minDist:
         isStartPtToJoinTo = False
         minDist = dist

      # cerco il punto più vicino al punto finale della polilinea
      ptToJoin = self.getEndPt()
      # considero il punto iniziale della polilinea a cui unirsi
      dist = getDistance(ptToJoin, linearObjectListToJoinTo.getStartPt())
      if dist < minDist:
         isStartPt = False
         isStartPtToJoinTo = True
         minDist = dist
      # considero il punto finale della polilinea a cui unirsi
      dist = getDistance(ptToJoin, linearObjectListToJoinTo.getEndPt())
      if dist < minDist:
         isStartPt = False
         isStartPtToJoinTo = False
         minDist = dist

      if minDist <= myToleranceDist: # trovato un punto
         # se il punto iniziale della polilinea da unire é uguale a quello iniziale della polilinea a cui unirsi
         if isStartPt == True and isStartPtToJoinTo == True:            
            part1 = qad_utils.QadLinearObject(self.getLinearObjectAt(0))
            part1.reverse()
            part2 = qad_utils.QadLinearObject(linearObjectListToJoinTo.getLinearObjectAt(0))
            part2.reverse()
                        
            res = joinEndPtsLinearParts(part1, part2, mode)
            if res is not None:
               # elimino la prima parte
               self.remove(0)
               res.reverse()
               self.insertList(0, res)
               
               # aggiungo le parti di <linearObjectListToJoinTo> tranne la prima
               i = 1
               tot = linearObjectListToJoinTo.qty()
               while i < tot:
                  self.insert(0, linearObjectListToJoinTo.getLinearObjectAt(i).reverse())
                  i = i + 1
               return True
            
         # se il punto iniziale della polilinea da unire é uguale a quello finale della polilinea a cui unirsi
         elif isStartPt == True and isStartPtToJoinTo == False:
            part1 = qad_utils.QadLinearObject(self.getLinearObjectAt(0))
            part1.reverse()
            part2 = linearObjectListToJoinTo.getLinearObjectAt(-1)
            
            res = joinEndPtsLinearParts(part1, part2, mode)
            if res is not None:
               # elimino la prima parte
               self.remove(0)
               res.reverse()
               self.insertList(0, res)
               
               # aggiungo le parti di <linearObjectListToJoinTo> tranne l'ultima
               i = linearObjectListToJoinTo.qty() - 2
               while i >= 0:
                  self.insert(0, linearObjectListToJoinTo.getLinearObjectAt(i))
                  i = i - 1
               return True

         # se il punto finale della polilinea da unire é uguale a quello iniziale della polilinea a cui unirsi
         elif isStartPt == False and isStartPtToJoinTo == True:
            part1 = self.getLinearObjectAt(-1)
            part2 = qad_utils.QadLinearObject(linearObjectListToJoinTo.getLinearObjectAt(0))
            part2.reverse()
            
            res = joinEndPtsLinearParts(part1, part2, mode)
            if res is not None:              
               # elimino l'ultima parte
               self.remove(-1)
               self.appendList(res)

               # aggiungo le parti di <linearObjectListToJoinTo> tranne la prima
               i = 1
               tot = linearObjectListToJoinTo.qty()
               while i < tot:
                  self.append(linearObjectListToJoinTo.getLinearObjectAt(i))
                  i = i + 1
               return True
            
         # se il punto finale della polilinea da unire é uguale a quello finale della polilinea a cui unirsi         
         elif isStartPt == False and isStartPtToJoinTo == False:
            part1 = self.getLinearObjectAt(-1)
            part2 = linearObjectListToJoinTo.getLinearObjectAt(-1)
            
            res = joinEndPtsLinearParts(part1, part2, mode)
            if res is not None:            
               # elimino l'ultima parte
               self.remove(-1)
               self.appendList(res)

               # aggiungo le parti di <linearObjectListToJoinTo> tranne l'ultima
               i = linearObjectListToJoinTo.qty() - 2
               while i >= 0:
                  self.append(linearObjectListToJoinTo.getLinearObjectAt(i).reverse())
                  i = i - 1
               return True

      return False
                 

   #============================================================================
   # selfJoin
   #============================================================================
   def selfJoin(self, epsg):
      """
      la funzione restituisce una lista QadLinearObjectList che contiene le polilinee
      generate dall'unione degli oggetti lineari (lista di parti segmenti-archi).
      <epsg> = the authority identifier for this srs 
      """
      # creo un layer temporaneo in memoria
      vectorLayer = QgsVectorLayer("LineString?crs=%s&index=yes" % epsg, "QAD_SelfJoinLines", "memory")
      provider = vectorLayer.dataProvider()
                 
      # unisco le parti nella lista di self
      # inserisco nel layer i vari oggetti lineari
      idList = self.appendToTempQgsVectorLayer(vectorLayer, False)
      if idList is None:
         return []
      if provider.capabilities() & QgsVectorDataProvider.CreateSpatialIndex:
         provider.createSpatialIndex()
      
      vectorLayer.beginEditCommand("selfJoin")     
      
      for featureIdToJoin in idList:
         #                         featureIdToJoin, vectorLayer, tolerance2ApproxCurve, tomyToleranceDist   
         joinFeatureInVectorLayer(featureIdToJoin, vectorLayer, QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")))        
           
      vectorLayer.endEditCommand()
      vectorLayer.commitChanges()
      
      result = []
      feature = QgsFeature()
      
      # fetchAttributes, fetchGeometry, rectangle, useIntersect             
      for feature in vectorLayer.getFeatures(getFeatureRequest([], True, None, False)):                       
         linearObjectList = QadLinearObjectList()
         linearObjectList.fromPolyline(feature.geometry().asPolyline())
         result.append(linearObjectList)
    
      return result  
   
   #===============================================================================
   # transform
   #===============================================================================
   def transform(self, coordTransform):
      """
      la funzione restituisce una nuova lista di parti con le coordinate trasformate.
      """
      result = QadLinearObjectList()
      for linearObject in self.defList:
         result.append(linearObject.transform(coordTransform))
      return result
   

   #===============================================================================
   # transformFromCRSToCRS
   #===============================================================================
   def transformFromCRSToCRS(self, sourceCRS, destCRS):
      """
      la funzione trasforma le coordinate dei punti che compone l'oggetto lineare.
      """
      return transform(QgsCoordinateTransform(sourceCRS, destCRS))
         
         
   #============================================================================
   # containsPt
   #============================================================================
   def containsPt(self, pt, startAt = 0):
      """
      la funzione ritorna la posizione della parte che contiene il punto oppure -1.
      Il controllo inizia dalla parte <startAt> (0-based)
      """
      tot = len(self.defList)
      if startAt < 0 or startAt >= tot:
         return -1
      i = startAt      
      while i < tot:
         linearObject = self.defList[i]
         if linearObject.containsPt(pt):
            return i
         i = i + 1
      return -1


   #===============================================================================
   # closestPartWithContext
   #===============================================================================
   def closestPartWithContext(self, pt, epsilon = 1.e-15):
      """
      la funzione ritorna una lista con 
      (<minima distanza al quadrato>
       <punto più vicino>
       <indice della parte più vicina>       
       <"a sinistra di" se il punto é alla sinista della parte (< 0 -> sinistra, > 0 -> destra)
      """
      minDistPoint = QgsPoint()
      closestPartIndex = 0
      sqrDist = sys.float_info.max
      leftOf = None
      index = 0
      for linearObject in self.defList:
         result = linearObject.closestPtWithContext(pt)
         testdist = result[0]
         if testdist < sqrDist:
            closestPartIndex = index
            sqrDist = testdist
            minDistPoint = result[1]
            leftOf = result[2]
         
         index = index + 1 
      
      return (sqrDist, minDistPoint, closestPartIndex, leftOf)


   #===============================================================================
   # breakOnPt
   #===============================================================================
   def breakOnPt(self, point):
      """
      la funzione spezza in due la lista di parti nel punto <point>.
      Ritorna una lista di due parti: la prima parte (che può essere
      nulla se <point> conicide con il punto iniziale) e la seconda parte (che può essere
      nulla se <point> conicide con il punto finale)
      """
      dummy = self.closestPartWithContext(point)
      nearestPt = dummy[1]
      partAt = dummy[2]
      if nearestPt is None or partAt is None:
         return [None, None]

      partToCut = self.getLinearObjectAt(partAt)
      cuttedParts = partToCut.breakOnPt(point)
      
      if ptNear(nearestPt, self.getStartPt()):
         partList1 = None
         partList2 = QadLinearObjectList(self)
         return [partList1, partList2]
      else:
         partList1 = QadLinearObjectList()
         for i in xrange(0, partAt, 1):
            partList1.append(QadLinearObject(self.getLinearObjectAt(i)))
            
         if cuttedParts[0] is not None:
            partList1.append(cuttedParts[0])
            
      if ptNear(nearestPt, self.getEndPt()):
         partList1 = QadLinearObjectList(self)
         partList2 = None
         return [partList1, partList2]
      else:
         partList2 = QadLinearObjectList()

         if cuttedParts[1] is not None:
            partList2.append(cuttedParts[1])
         
         for i in xrange(partAt + 1, self.qty(), 1):
            partList2.append(QadLinearObject(self.getLinearObjectAt(i)))
            
      return [partList1, partList2]


   #============================================================================
   # getIntPtNearestToStartPt
   #============================================================================
   def getIntPtNearestToStartPt(self, crs, entitySet, edgeMode):
      """
      La funzione cerca il punto di intersezione tra la polilinea e un gruppo di entità
      che é più vicino al punto iniziale della polilinea.
      La funzione riceve:
      <crs> sistema di coordinate in cui é espressa la polilinea 
      <entitySet> gruppo di entità
      La funzione restituisce:
      punto di intersezione, numero della parte
      """   
      newPt = None
      partNumber = -1
      distFromStart = 0
      trimmedLinearObject = QadLinearObject()
      gTransformed = QgsGeometry()
      
      # scorro i segmenti
      for i in xrange(0, self.qty(), 1):
         minDist = sys.float_info.max
         LinearObject = self.getLinearObjectAt(i)                                       
      
         # per ciascun layer                                                         
         for layerEntitySet in entitySet.layerEntitySetList:
            layer = layerEntitySet.layer
            
            if layer.crs() != crs:
               coordTransform = QgsCoordinateTransform(layer.crs(), crs)          
            trimmedLinearObject.set(LinearObject)
                  
            # per ciascuna entità del layer
            for featureId in layerEntitySet.featureIds:
               f = getFeatureById(layer, featureId)
               # Trasformo la geometria nel sistema di coordinate del <layer> 
               gTransformed = f.geometry()
               if layer.crs() != crs:
                  gTransformed.transform(coordTransform)
               
               intPt = getIntersectionPtTrimQgsGeometry(LinearObject, gTransformed, edgeMode)
               if intPt is not None:
                  # cerco il punto di intersezione più vicino al punto iniziale
                  trimmedLinearObject.setEndPt(intPt)
                  if trimmedLinearObject.length() < minDist:
                     minDist = trimmedLinearObject.length()
                     newPt = intPt
                     partNumber = i
            
         if newPt is not None:
            break
         
         distFromStart = distFromStart + LinearObject.length()
         
      if newPt is None:
         return None, -1
      else:
         return newPt, partNumber


#===============================================================================
# FINE - QadLinearObjectList class
#===============================================================================
   
   
#============================================================================
# joinFeatureInVectorLayer
#============================================================================
def joinFeatureInVectorLayer(featureIdToJoin, vectorLayer, tolerance2ApproxCurve, toleranceDist = 1.e-9, \
                             mode = 2):
   """
   la funzione effettua il join (unione) di una polilinea con un gruppo di altre polilinee.
   Non sono ammesse geometrie multiLineString.
   Il layer deve essere in modifica (startEditing) e in una transazione (beginEditCommand)
   La funzione riceve:
   <featureIdToJoin> = un ID della feature da unire 
   <vectorLayer> = un QgsVectorLayer che deve contenere le feature da unire
                   (si usano gli indici spaziali del vettore x essere più veloci).
   <toleranceDist> = distanza di tolleranza perché 2 punti siano considerati coincidenti  
   <tolerance2ApproxCurve> = tolleranza di approssimazione per le curve (usato se toleranceDist > 0)
   <mode> = Imposta il metodo di unione (usato se toleranceDist > 0):
            1 -> Estendi;  Consente di unire polilinee selezionate estendendo o tagliando 
                           i segmenti nei punti finali più vicini.
            2 -> Aggiungi; Consente di unire polilinee selezionate aggiungendo un segmento 
                           retto tra i punti finali più vicini.
            3 -> Entrambi;Consente di unire polilinee selezionate estendendo o tagliando, se possibile.
                 In caso contrario, consente di unire polilinee selezionate aggiungendo 
                 un segmento retto tra i punti finali più vicini. 
   La funzione modifica il <vectorLayer> modificando la feature da unire e cancellando 
   quelle unite a featureIdToJoin . Ritorna la lista di features cancellate.
   """   
   featureToJoin = getFeatureById(vectorLayer, featureIdToJoin)
   if featureToJoin is None:
      return []
   
   g = QgsGeometry(featureToJoin.geometry())
   linearObjectList = qad_utils.QadLinearObjectList()
   linearObjectList.fromPolyline(g.asPolyline())
   
   linearObjectListToJoinTo = qad_utils.QadLinearObjectList()
   
   deleteFeatures = []
   feature = QgsFeature()
   
   # Unisco usando il punto iniziale finché trovo feature da unire
   ptToJoin = linearObjectList.getStartPt()
   found = True
   while found == True:
      found = False
      if ptToJoin is None: # test roby
         fermati = True
      # cerco le features nel punto iniziale usando un micro rettangolo secondo <toleranceDist>
      selectRect = QgsRectangle(ptToJoin.x() - toleranceDist, ptToJoin.y() - toleranceDist, \
                                ptToJoin.x() + toleranceDist, ptToJoin.y() + toleranceDist)
      # cerco il punto più vicino al punto iniziale della polilinea
      minDist = sys.float_info.max
      # fetchAttributes, fetchGeometry, rectangle, useIntersect             
      for feature in vectorLayer.getFeatures(getFeatureRequest([], True, selectRect, True)):                       
         if feature.id() != featureIdToJoin: # salto la feature da unire
            linearObjectListToJoinTo.fromPolyline(feature.geometry().asPolyline())
            
            if linearObjectList.join(linearObjectListToJoinTo, toleranceDist, mode) == True:
               found = True
               
               deleteFeatures.append(QgsFeature(feature))
               if vectorLayer.deleteFeature(feature.id()) == False:
                  return []
               
               ptToJoin = linearObjectList.getStartPt()
               pts = linearObjectList.asPolyline(tolerance2ApproxCurve)
               featureToJoin.setGeometry(QgsGeometry.fromPolyline(pts))
               if vectorLayer.updateFeature(featureToJoin) == False:
                  return []
               break
            
   # Unisco usando il punto finale finché trovo feature da unire
   ptToJoin = linearObjectList.getEndPt()
   found = True
   while found == True:
      found = False
      # cerco le features nel punto finale usando un micro rettangolo secondo <toleranceDist>
      selectRect = QgsRectangle(ptToJoin.x() - toleranceDist, ptToJoin.y() - toleranceDist, \
                                ptToJoin.x() + toleranceDist, ptToJoin.y() + toleranceDist)
      # fetchAttributes, fetchGeometry, rectangle, useIntersect             
      for feature in vectorLayer.getFeatures(getFeatureRequest([], True, selectRect, True)):                       
         if feature.id() != featureIdToJoin: # salto la feature da unire
            linearObjectListToJoinTo.fromPolyline(feature.geometry().asPolyline())

            if linearObjectList.join(linearObjectListToJoinTo, toleranceDist, mode) == True:
               found = True
               
               deleteFeatures.append(QgsFeature(feature))
               if vectorLayer.deleteFeature(feature.id()) == False:
                  return []
               
               ptToJoin = linearObjectList.getEndPt()
               pts = linearObjectList.asPolyline(tolerance2ApproxCurve)
               featureToJoin.setGeometry(QgsGeometry.fromPolyline(pts))
               if vectorLayer.updateFeature(featureToJoin) == False:
                  return []
               break
   
   return deleteFeatures


#===============================================================================
# joinEndPtsLinearParts
#===============================================================================
def joinEndPtsLinearParts(part1, part2, mode):
   """
   la funzione effettua il join (unione) tra 2 parti lineari considerando il punto finale di part1
   e il punto iniziale di part2.
   La funzione riceve:
   <part1> = prima parte lineare  
   <part2> = seconda parte parte lineare  
   <mode> = Imposta il metodo di unione:
            1 -> Estendi;  Consente di unire polilinee selezionate estendendo o tagliando 
                           i segmenti nei punti finali più vicini.
            2 -> Aggiungi; Consente di unire polilinee selezionate aggiungendo un segmento 
                           retto tra i punti finali più vicini.
            3 -> Entrambi; Consente di unire polilinee selezionate estendendo o tagliando, se possibile.
                           In caso contrario, consente di unire polilinee selezionate aggiungendo 
                           un segmento retto tra i punti finali più vicini. 
   La funzione restituisce una QadLinearObjectList che comprende:
   part1 (eventualmente modificata nel punto finale) + 
   eventuale segmento + 
   part2 (eventualmente modificata nel punto finale)
   oppure restituisce None se non é possibile l'unione delle parti
   """
   linearObjectList = qad_utils.QadLinearObjectList()
   endPt1 = part1.getEndPt()
   endPt2 = part2.getEndPt()
   
   if ptNear(endPt1, endPt2): # le 2 parti sono già  unite
      linearObjectList.append(QadLinearObject(part1))
      linearObjectList.append(QadLinearObject(part2).reverse())
      return linearObjectList

   if mode == 1: # Estendi/Taglia
      IntPtList = part1.getIntersectionPtsWithLinearObject(part2)
      if len(IntPtList) > 0: # Taglia
         linearObjectList.append(QadLinearObject(part1))
         linearObjectList.getLinearObjectAt(-1).setEndPt(IntPtList[0])
         linearObjectList.append(QadLinearObject(part2).reverse())
         linearObjectList.getLinearObjectAt(-1).setStartPt(IntPtList[0])
         return linearObjectList
      else: # estendi
         IntPtList = part1.getIntersectionPtsOnExtensionWithLinearObject(part2)
         # considero solo i punti oltre l'inizio delle parti
         for i in xrange(len(IntPtList) - 1, -1, -1):
            if part1.getDistanceFromStart(IntPtList[i]) < 0 or \
               part2.getDistanceFromStart(IntPtList[i]) < 0:
               del IntPtList[i]               
               
         if len(IntPtList) > 0:
            IntPt = IntPtList[0]   
            linearObjectList.append(QadLinearObject(part1))
            linearObjectList.getLinearObjectAt(-1).setEndPt(IntPtList[0])
            linearObjectList.append(QadLinearObject(part2.reverse()))
            linearObjectList.getLinearObjectAt(-1).setStartPt(IntPtList[0])
            return linearObjectList
   
   if mode == 2 or mode == 3: # Aggiungi
      linearObjectList.append(QadLinearObject(part1))
      linearObjectList.append([endPt1, endPt2])
      linearObjectList.append(QadLinearObject(part2).reverse())
      return linearObjectList

   return None


#===============================================================================
# getCurveLinearObjects
#===============================================================================
def getCurveLinearObjects(tanDirectionOnStartPt, prev, current, next):
   """
   Data la direzione della tangente nel punto iniziale della parte corrente e 
   una successione di 3 parti lineari,
   la funzione ritorna una lista di parti lineari
   da sostituire alla parte <current> per curvare la polilinea
   """
   if current.isArc():
      return [QadLinearObject(current)]

   # se non ci sono né la parte precedente né la parte successiva 
   if prev is None and next is None:
      return QadLinearObject(current)

   arc = QadArc()
   if prev is None: # non c'é una parte precedente
      if arc.fromStartSecondEndPts(current.getStartPt(), current.getEndPt(), next.getEndPt()) == False:
         return [QadLinearObject(current)]
      if ptNear(current.getStartPt(), arc.getStartPt()): # arco non é inverso                  
         arc.setEndAngleByPt(current.getEndPt())
         return [QadLinearObject([arc, False])]
      else: # arco é inverso
         arc.setStartAngleByPt(current.getEndPt())
         return [QadLinearObject([arc, True])]
   else:
      t = prev.getTanDirectionOnEndPt() if tanDirectionOnStartPt is None else tanDirectionOnStartPt
       
      if next is None: # non c'é una parte successiva          
         if arc.fromStartEndPtsTan(current.getStartPt(), current.getEndPt(), t) == False:
            return [QadLinearObject(current)]
         if ptNear(current.getStartPt(), arc.getStartPt()): # arco non é inverso                  
            return [QadLinearObject([arc, False])]
         else: # arco é inverso
            return [QadLinearObject([arc, True])]
      else: # c'é una parte precedente e successiva
         # calcolo il punto medio tra i 2 archi di raccordo
#          if arc.fromStartEndPtsTan(current.getStartPt(), current.getEndPt(), \
#                                    prev.getTanDirectionOnEndPt()) == False:
#             return [QadLinearObject(current)]
#          tanDirectionOnEndPt = next.getTanDirectionOnStartPt() + math.pi
#          arc2 = QadArc()
#          if arc2.fromStartEndPtsTan(current.getEndPt(), current.getStartPt(), \
#                                     tanDirectionOnEndPt) == False:
#             return [QadLinearObject(current)]

         if arc.fromStartSecondEndPts(prev.getStartPt(), current.getStartPt(), current.getEndPt()) == False:
            return [QadLinearObject(current)]
         if ptNear(prev.getStartPt(), arc.getStartPt()): # arco non é inverso                  
            arc.setStartAngleByPt(current.getStartPt())
         else: # arco é inverso
            arc.setEndAngleByPt(current.getStartPt())
         arc2 = QadArc()
         if arc2.fromStartSecondEndPts(current.getStartPt(), current.getEndPt(), next.getEndPt()) == False:
            return [QadLinearObject(current)]
         if ptNear(current.getStartPt(), arc2.getStartPt()): # arco non é inverso                  
            arc2.setEndAngleByPt(current.getEndPt())
         else: # arco é inverso
            arc2.setStartAngleByPt(current.getEndPt())

         midPt = getMiddlePoint(arc.getMiddlePt(), arc2.getMiddlePt())
         
         if arc.fromStartEndPtsTan(current.getStartPt(), midPt, t) == False:
            return [QadLinearObject(current)]
         if ptNear(current.getStartPt(), arc.getStartPt()): # arco non é inverso                  
            linearObject1 = QadLinearObject([arc, False])
         else: # arco é inverso
            linearObject1 = QadLinearObject([arc, True])
         
         if arc2.fromStartEndPtsTan(linearObject1.getEndPt(), current.getEndPt(), \
                                    linearObject1.getTanDirectionOnEndPt()) == False:
            return [QadLinearObject(current)]
         if ptNear(current.getEndPt(), arc2.getEndPt()): # arco non é inverso                  
            linearObject2 = QadLinearObject([arc2, False])
         else: # arco é inverso
            linearObject2 = QadLinearObject([arc2, True])

         return [linearObject1, linearObject2]


#============================================================================
# TrimExtend
#============================================================================
def getFilletLinearObjectList(poly1, partAt1, pointAt1, poly2, partAt2, pointAt2, filletMode, radius, epsg):
   """
   Date due polilinee, la parte e il punto in cui bisogna fare il raccordo tra le due
   polilinee, la funzione ritorna una polilinea risultato del raccordo e due flag che
   danno indicazioni su ciò che deve essere fatto alle polilinee originali:
   (0=niente, 1=modificare, 2=cancellare)
   <filletMode> modalità di raccordo; 1=Taglia-estendi, 2=Non taglia-estendi
   <radius> raggio di raccordo
   """
   circle1 = poly1.getCircle()
   circle2 = poly2.getCircle()
   
   if circle1 is None: # se poly1 non era un cerchio
      part = QadLinearObject(poly1.getLinearObjectAt(partAt1))
      if circle2 is None: # se poly2 non era un cerchio
         nextPart = QadLinearObject(poly2.getLinearObjectAt(partAt2))         
         if part.isSegment():
            if nextPart.isSegment(): # part e nextPart sono segmenti retti
               if radius == 0:         
                  res = bridgeTheGapBetweenLines(part, pointAt1, nextPart, pointAt2, radius, 0)
               else:
                  res = bridgeTheGapBetweenLines(part, pointAt1, nextPart, pointAt2, radius, 1)
            else: # part é un segmento retto, nextPart é un arco
               res = bridgeTheGapBetweenArcLine(nextPart, pointAt2, part, pointAt1, radius, filletMode)
               if res is not None:
                  dummy = res[0] # inverto il primo e il terzo elemento
                  res[0] = res[2]
                  res[2] = dummy
         else:
            if nextPart.isSegment(): # part é un arco, nextPart é un segmento retto
               res = bridgeTheGapBetweenArcLine(part, pointAt1, nextPart, pointAt2, radius, filletMode)
            else: # part é un arco, nextPart é un arco
               res = bridgeTheGapBetweenArcs(part, pointAt1, nextPart, pointAt2, radius, filletMode)
      else:
         if part.isSegment(): # part é un segmento retto, poly2 é un cerchio
            res = bridgeTheGapBetweenCircleLine(poly2, pointAt2, part, pointAt1, radius, filletMode)
            if res is not None:
               dummy = res[0] # inverto il primo e il terzo elemento
               res[0] = res[2]
               res[2] = dummy
         else: # part é un arco, poly2 é un cerchio
            res = bridgeTheGapBetweenArcCircle(part, pointAt1, poly2, pointAt2, radius, filletMode)
   else:
      if circle2 is None: # se poly2 non era un cerchio
         nextPart = QadLinearObject(poly2.getLinearObjectAt(partAt2))         
         if nextPart.isSegment(): # poly1 é un cerchio, nextPart é un segmento retto
            res = bridgeTheGapBetweenCircleLine(poly1, pointAt1, nextPart, pointAt2, radius, filletMode)
         else: # poly1 é un cerchio, nextPart é un arco
            res = bridgeTheGapBetweenArcCircle(nextPart, pointAt2, poly1, pointAt1, radius, filletMode)
            if res is not None:
               dummy = res[0] # inverto il primo e il terzo elemento
               res[0] = res[2]
               res[2] = dummy
      else: # poly1 e poly2 sono cerchi
         res = bridgeTheGapBetweenCircles(poly1, pointAt1, poly2, pointAt2, radius)

   if res is None: # raccordo non possibile
      return None
   
   filletLinearObjectList = QadLinearObjectList()
   whatToDoPoly1 = 0 # 0=niente, 1=modificare, 2=cancellare
   whatToDoPoly2 = 0 # 0=niente, 1=modificare, 2=cancellare
   
   if filletMode == 1 or radius == 0: # modalità di raccordo "Taglia-estendi"
      if circle1 is None: # se poly1 non era un cerchio
         if res[0] is not None:
            part.set(res[0]) # modifico part
      if circle2 is None: # se poly2 non era un cerchio
         if res[2] is not None:
            nextPart.set(res[2]) # modifico nextPart

   filletArc = res[1] # arco di raccordo

   if filletArc is None:
      if circle1 is None and circle2 is None:
         # se il punto iniziale di part tocca nextPart
         if ptNear(part.getStartPt(), nextPart.getStartPt()) or \
            ptNear(part.getStartPt(), nextPart.getEndPt()):
            whatToDoPoly1 = 1 # 1=modificare
            # aggiungo part e le parti successive di part
            filletLinearObjectList.append(part)
            filletLinearObjectList.appendList(poly1, partAt1 + 1)
         # se il punto finale di part tocca nextPart
         elif ptNear(part.getEndPt(), nextPart.getStartPt()) or \
            ptNear(part.getEndPt(), nextPart.getEndPt()):
            whatToDoPoly1 = 1 # 1=modificare
            # aggiungo part e le parti precedenti di part
            filletLinearObjectList.append(part)
            filletLinearObjectList.appendList(poly1, 0, partAt1)
   
         # se il punto iniziale di nextPart tocca part
         if ptNear(nextPart.getStartPt(), part.getStartPt()) or \
            ptNear(nextPart.getStartPt(), part.getEndPt()):
            if whatToDoPoly1 == 1: # se la poly1 era da modificare (1=modificare)
               whatToDoPoly2 = 2 # 2=cancellare
            else:
               whatToDoPoly2 = 1 # 1=modificare
            # aggiungo nextPart e le parti successive di nextPart
            filletLinearObjectList.append(nextPart)
            filletLinearObjectList.appendList(poly2, partAt2 + 1)
         # se il punto finale di nextPart tocca part
         elif ptNear(nextPart.getEndPt(), part.getStartPt()) or \
            ptNear(nextPart.getEndPt(), part.getEndPt()):
            if whatToDoPoly1 == 1: # se la poly1 era da modificare (1=modificare)
               whatToDoPoly2 = 2 # 2=cancellare
            else:
               whatToDoPoly2 = 1 # 1=modificare
            # aggiungo nextPart e le parti precedenti di nextPart
            filletLinearObjectList.append(nextPart)
            filletLinearObjectList.appendList(poly2, 0, partAt2)            
   else: # esiste un arco di raccordo
      filletLinearObjectList.append(filletArc)
      if circle1 is None:
         # se l'arco di raccordo tocca il punto iniziale di part
         if ptNear(filletArc.getStartPt(), part.getStartPt()) or \
            ptNear(filletArc.getEndPt(), part.getStartPt()):
            whatToDoPoly1 = 1 # 1=modificare
            # aggiungo part e le parti successive di part
            filletLinearObjectList.append(part)
            filletLinearObjectList.appendList(poly1, partAt1 + 1)
         # se l'arco di raccordo tocca il punto finale di part
         elif ptNear(filletArc.getStartPt(), part.getEndPt()) or \
              ptNear(filletArc.getEndPt(), part.getEndPt()):
            whatToDoPoly1 = 1 # 1=modificare
            # aggiungo part e le parti precedenti di part
            filletLinearObjectList.append(part)
            filletLinearObjectList.appendList(poly1, 0, partAt1)
         
      if circle2 is None:
         # se l'arco di raccordo tocca il punto iniziale di nextPart
         if ptNear(filletArc.getStartPt(), nextPart.getStartPt()) or \
            ptNear(filletArc.getEndPt(), nextPart.getStartPt()):
            if whatToDoPoly1 == 1: # se la poly1 era da modificare (1=modificare)
               whatToDoPoly2 = 2 # 2=cancellare
            else:
               whatToDoPoly2 = 1 # 1=modificare
            # aggiungo nextPart e le parti successive di nextPart
            filletLinearObjectList.append(nextPart)
            filletLinearObjectList.appendList(poly2, partAt2 + 1)
         # se l'arco di raccordo tocca il punto finale di nextPart
         elif ptNear(filletArc.getStartPt(), nextPart.getEndPt()) or \
              ptNear(filletArc.getEndPt(), nextPart.getEndPt()):
            if whatToDoPoly1 == 1: # se la poly1 era da modificare (1=modificare)
               whatToDoPoly2 = 2 # 2=cancellare
            else:
               whatToDoPoly2 = 1 # 1=modificare
            # aggiungo nextPart e le parti precedenti di nextPart
            filletLinearObjectList.append(nextPart)
            filletLinearObjectList.appendList(poly2, 0, partAt2)
   
   res = filletLinearObjectList.selfJoin(epsg)
   if len(res) != 1:
      return None
   
   return res[0], whatToDoPoly1, whatToDoPoly2


#============================================================================
# QadRawConfigParser class suppporting unicode
#============================================================================
class QadRawConfigParser(ConfigParser.RawConfigParser):

   def __init__(self, defaults=None, dict_type=ConfigParser._default_dict,
                 allow_no_value=False):
      ConfigParser.RawConfigParser.__init__(self, defaults, dict_type, allow_no_value)
      
   def get(self, section, option, default = None):
      try:
         return ConfigParser.RawConfigParser.get(self, section, option)
      except:
         return default

   def getint(self, section, option, default = None):
      try:
         return ConfigParser.RawConfigParser.getint(self, section, option)
      except:
         return default

   def getfloat(self, section, option, default = None):
      try:
         return ConfigParser.RawConfigParser.getfloat(self, section, option)
      except:
         return default

   def getboolean(self, section, option, default = None):
      try:
         return ConfigParser.RawConfigParser.getboolean(self, section, option)
      except:
         return default

   def write(self, fp):
      """Fixed for Unicode output"""
      if self._defaults:
         fp.write("[%s]\n" % DEFAULTSECT)
         for (key, value) in self._defaults.items():
            fp.write("%s = %s\n" % (key, unicode(value).replace('\n', '\n\t')))
         fp.write("\n")
      for section in self._sections:
         fp.write("[%s]\n" % section)
         for (key, value) in self._sections[section].items():
            if key != "__name__":
               fp.write("%s = %s\n" % (key, unicode(value).replace('\n','\n\t')))
         fp.write("\n")
 

#===============================================================================
# Timer class for profiling
#===============================================================================
class Timer(object):
   # da usare:
   # with qad_utils.Timer() as t:
   #    ...
   # elasped = t.secs
   def __init__(self, verbose=False):
      self.verbose = verbose

   def __enter__(self):
      self.start = time.time()
      return self

   def __exit__(self, *args):
      self.end = time.time()
      self.secs = self.end - self.start
      self.msecs = self.secs * 1000  # millisecs
      if self.verbose:
         print 'elapsed time: %f ms' % self.msecs


#===============================================================================
# qadShowPluginHelp
#===============================================================================
def qadShowPluginHelp(section = "", filename = "index", packageName = None):
   """
   show a help in the user's html browser.
   per conoscere la sezione/pagina del file html usare internet explorer,
   selezionare nella finestra di destra la voce di interesse e leggerne l'indirizzo dalla casella in alto.
   Questo perché internet explorer inserisce tutti i caratteri di spaziatura e tab che gli altri browser non fanno.
   """   
   try:
      source = ""
      if packageName is None:
         import inspect
         source = inspect.currentframe().f_back.f_code.co_filename
      else:
         source = sys.modules[packageName].__file__
   except:
      return

   path = os.path.dirname(source) + "/help/help"
   locale = str(QLocale().name())
   helpPath = path + "_" + locale # provo a caricare la lingua e la regione selezionate
   if not os.path.exists(helpPath):
      helpPath = path + "_" + locale.split("_")[0] # provo a caricare la lingua
      if not os.path.exists(helpPath):
         helpPath = path + "_en" # provo a caricare la lingua inglese
         if not os.path.exists(helpPath):
            return
      
   helpfile = os.path.join(helpPath, filename + ".html")
   if os.path.exists(helpfile):
      url = "file:///"+helpfile

      if section != "":
         url = url + "#" + section

      # la funzione QDesktopServices.openUrl in windows non apre la sezione
      if platform.system() == "Windows":
         import subprocess
         from _winreg import HKEY_CURRENT_USER, OpenKey, QueryValue
         # In Py3, this module is called winreg without the underscore
         
         with OpenKey(HKEY_CURRENT_USER, r"Software\Classes\http\shell\open\command") as key:
            cmd = QueryValue(key, None)
   
         if cmd.find("\"%1\"") >= 0:
            subprocess.Popen(cmd.replace("%1", url))
         else:    
            if cmd.find("%1") >= 0:
               subprocess.Popen(cmd.replace("%1", "\"" + url + "\""))       
            else:
               subprocess.Popen(cmd + " \"" + url + "\"")
      else:
         QDesktopServices.openUrl(QUrl(url))           
