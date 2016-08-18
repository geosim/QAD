# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire gli snap
 
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
import os.path
from qgis.core import *
import math
import sys


import qad_utils
from qad_arc import *
from qad_circle import *


#===============================================================================
# QadSnapTypeEnum class.
#===============================================================================
class QadSnapTypeEnum():
   NONE      = 0       # nessuno
   END       = 1       # punti finali di ogni segmento
   MID       = 2       # punto medio 
   CEN       = 4       # centro (centroide)
   NOD       = 8       # oggetto punto
   QUA       = 16      # punto quadrante
   INT       = 32      # intersezione
   INS       = 64      # punto di inserimento
   PER       = 128     # punto perpendicolare
   TAN       = 256     # tangente
   NEA       = 512     # punto più vicino
   C         = 1024    # pulisci all object snaps
   APP       = 2048    # intersezione apparente
   EXT       = 4096    # estensione
   PAR       = 8192    # parallelo
   DISABLE   = 16384   # osnap off                      
   PR        = 65536   # distanza progressiva
   EXT_INT   = 131072  # intersezione sull'estensione
   PER_DEF   = 262144  # perpendicolare differita (come NEA)
   TAN_DEF   = 524288  # tangente differita (come NEA)
   POLAR     = 1048576 # puntamento polare
   END_PLINE = 2097152 # punti finali dell'intera polilinea

#===============================================================================
# QadSnapModeEnum class.
#===============================================================================
class QadSnapModeEnum():
   ONE_RESULT           = 0 # Viene restituito solo il punto più vicino
   RESULTS_FOR_SAME_POS = 1 # vengono restituiti diversi punti che hanno la stessa posizione.
                            # Questo é utile per l'editing topologico
   ALL_RESULTS          = 2 # Tutti i punti

#===============================================================================
# QadVertexSearchModeEnum class.
#===============================================================================
class QadVertexSearchModeEnum():
   ALL               = 0 # tutti i vertici
   EXCLUDE_START_END = 1 # escludi il punto iniziale e finale
   ONLY_START_END    = 2 # solo il punto iniziale e finale


#===============================================================================
# Qad snapper class.
#===============================================================================
class QadSnapper():
   """
   Classe che gestisce i punti di snap
   """
      
   
   #============================================================================
   # __init__
   #============================================================================
   def __init__(self):
      self.__snapType = QadSnapTypeEnum.NONE
      self.__snapLayers = None      
      self.__snapMode = QadSnapModeEnum.ONE_RESULT
      self.__snapPointCRS = None # sistema di coordinate in cui memorizzare i punti di snap      
      self.__startPoint = None
      self.__toleranceExtParlines = 0
      self.__extLines = [] # lista delle linee da estendere (ogni elemento é una lista di 2 punti = linea)
      self.__extArcs = [] # lista degli archi da estendere (ogni elemento é un arco)
      self.__parLines = [] # lista delle linee per modo parallelo (ogni elemento é una lista di 2 punti = linea)
      self.__intExtLine = [] # linea per intersezione su estensione (lista di 2 punti = linea)      
      self.__intExtArc = [] # arco per intersezione su estensione
      self.__cacheSnapPoints = []      
      self.__progressDistance = 0.0 # distanza progressiva dall'inizio della linea
      self.__distToExcludeNea = 0.0 # distanza entro la quale se ci sono dei punti di snap
                                    # diversi da nearest questi hanno priorità su nearest
                                    # altrimenti nearest vincerebbe sempre
      self.tmpGeometries = [] # lista di geometria non ancora esistenti ma da contare per i punti di osnap (in map coordinates)


   #============================================================================
   # SnapType
   #============================================================================
   def setSnapType(self, snapType):
      """
      Imposta il tipo di snapping
      """            
      if self.__snapType != snapType:
         self.__snapType = snapType
         self.clearCacheSnapPoints()
         self.removeReferenceLines()         
   def getSnapType(self):
      """
      Restituisce il tipo di snapping
      """
      return self.__snapType


   #============================================================================
   # SnapType
   #============================================================================
   def getGeometryTypesAccordingToSnapType(self):
      """
      Verifica quali geometrie vengono coinvolte dal tipo di snap impostato
      Ritorna una lista di 3 elementi: (point, line, polygon)
      - se il primo elemento é vero il tipo punto é coinvolto altrimenti falso
      - se il secondo elemento é vero il tipo linea é coinvolto altrimenti falso
      - se il terzo elemento é vero il tipo poligono é coinvolto altrimenti falso
      """
      if self.getSnapType() == QadSnapTypeEnum.NONE or \
         self.getSnapType() & QadSnapTypeEnum.DISABLE:
         return False, False, False
      
      point = False
      line = False
      polygon = False

      # <oggetto punto> o <punto di inserimento> o <punto più vicino>
      if self.getSnapType() & QadSnapTypeEnum.NOD or \
         self.getSnapType() & QadSnapTypeEnum.INS or \
         self.getSnapType() & QadSnapTypeEnum.NEA:
         point = True
      
      # <punto finale> o <punto medio> o <centro (centroide o centro arco)> o 
      # <intersezione> o <punto perpendicolare> o <tangente> o
      # <punto più vicino> o <intersezione apparente> o <estensione>
      # <parallelo> o <distanza progressiva> o <intersezione sull'estensione>
      if self.getSnapType() & QadSnapTypeEnum.END or \
         self.getSnapType() & QadSnapTypeEnum.END_PLINE or \
         self.getSnapType() & QadSnapTypeEnum.MID or \
         self.getSnapType() & QadSnapTypeEnum.CEN or \
         self.getSnapType() & QadSnapTypeEnum.QUA or \
         self.getSnapType() & QadSnapTypeEnum.INT or \
         self.getSnapType() & QadSnapTypeEnum.PER or \
         self.getSnapType() & QadSnapTypeEnum.TAN or \
         self.getSnapType() & QadSnapTypeEnum.NEA or \
         self.getSnapType() & QadSnapTypeEnum.APP or \
         self.getSnapType() & QadSnapTypeEnum.EXT or \
         self.getSnapType() & QadSnapTypeEnum.PAR or \
         self.getSnapType() & QadSnapTypeEnum.PR or \
         self.getSnapType() & QadSnapTypeEnum.EXT_INT or \
         self.getSnapType() & QadSnapTypeEnum.PER_DEF or \
         self.getSnapType() & QadSnapTypeEnum.TAN_DEF:
         line = True
         
      # <punto finale> o <punto medio> o <centro (centroide o centro arco)> o 
      # <punto quadrante> o <intersezione> o <punto perpendicolare> o <tangente> o
      # <punto più vicino> o <intersezione apparente> o <estensione>
      # <parallelo> o <distanza progressiva> o <intersezione sull'estensione>
      if self.getSnapType() & QadSnapTypeEnum.END or \
         self.getSnapType() & QadSnapTypeEnum.MID or \
         self.getSnapType() & QadSnapTypeEnum.CEN or \
         self.getSnapType() & QadSnapTypeEnum.QUA or \
         self.getSnapType() & QadSnapTypeEnum.INT or \
         self.getSnapType() & QadSnapTypeEnum.PER or \
         self.getSnapType() & QadSnapTypeEnum.TAN or \
         self.getSnapType() & QadSnapTypeEnum.NEA or \
         self.getSnapType() & QadSnapTypeEnum.APP or \
         self.getSnapType() & QadSnapTypeEnum.EXT or \
         self.getSnapType() & QadSnapTypeEnum.PAR or \
         self.getSnapType() & QadSnapTypeEnum.PR or \
         self.getSnapType() & QadSnapTypeEnum.EXT_INT or \
         self.getSnapType() & QadSnapTypeEnum.PER_DEF or \
         self.getSnapType() & QadSnapTypeEnum.TAN_DEF:
         polygon = True

      return point, line, polygon


   #============================================================================
   # Snapmode
   #============================================================================
   def setSnapMode(self, snapMode):
      """
      Imposta la modalità di snapping
      """      
      self.__snapMode = snapMode
   def getSnapMode(self):
      """
      Restituisce il modo di snapping
      """
      return self.__snapMode


   #============================================================================
   # SnapLayers
   #============================================================================
   def setSnapLayers(self, snapLayers):
      """
      Imposta i layer da considerare nello snapping
      """      
      self.__snapLayers = snapLayers
      self.clearCacheSnapPoints()
   def getSnapLayers(self):
      """
      Restituisce la lista dei layer da considerare per lo snapping
      """
      return self.__snapLayers


   #============================================================================
   # SnapPointCRS
   #============================================================================
   def setSnapPointCRS(self, snapPointCRS):
      """
      Imposta il sistema di coordinate in cui memorizzare i punti di snap
      CRS é QgsCoordinateReferenceSystem
      """      
      if self.__snapPointCRS != snapPointCRS:
         self.__snapPointCRS = snapPointCRS
         self.clearCacheSnapPoints()
   def getSnapPointCRS(self):
      """
      Restituisce il sistema di coordinate in cui memorizzare i punti di snap
      """
      return self.__snapPointCRS


   #============================================================================
   # setStartPoint
   #============================================================================
   def setStartPoint(self, startPoint, CRS = None):
      """
      il punto é espresso in __snapPointCRS se CRS = None
      """
      if startPoint is not None and CRS is not None:
         self.__startPoint = self.__transformPoint(startPoint, CRS, self.getSnapPointCRS()) # trasformo il punto
      else:
         self.__startPoint = startPoint     


   #============================================================================
   # setDistToExcludeNea
   #============================================================================
   def setDistToExcludeNea(self, distToExcludeNea):
      """
      setta la distanza entro la quale se ci sono dei punti di snap diversi da nearest 
      questi hanno priorità su nearest altrimenti nearest vincerebbe sempre
      """
      self.__distToExcludeNea = distToExcludeNea


   #===========================================================================
   # ReferenceLines
   #===========================================================================
   def toggleReferenceLines(self, geom, point, CRS = None):
      # usato solo per snap EXT o PAR
      if not(self.__snapType & QadSnapTypeEnum.EXT) and \
         not(self.__snapType & QadSnapTypeEnum.PAR):
         return
      
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>)
      dummy = qad_utils.closestSegmentWithContext(point, geom)
      afterVertex = dummy[2]
      if afterVertex is None:
         return

      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap
         
      # verifico se ci sono archi
      arc = None
      arcList = QadArcList()
      if arcList.fromGeom(g) > 0:
         info = arcList.arcAt(afterVertex)
         if info is not None:
            arc = info[0]
            
      # verifico se ci sono cerchi
      circle = None
      circleList = QadCircleList()
      if circleList.fromGeom(g) > 0:
         info = circleList.circleAt(afterVertex)
         if info is not None:
            circle = info[0]

      pt1 = g.vertexAt(afterVertex - 1)   
      pt2 = g.vertexAt(afterVertex)   
      
      if self.__snapType & QadSnapTypeEnum.EXT:
         if arc is not None: # se fa parte di un arco
            self.toggleExtArc(arc, CRS)
         elif circle is None: # se non fa parte di un cerchio
            self.toggleExtLine(pt1, pt2)
      if self.__snapType & QadSnapTypeEnum.PAR:
         if (arc is None) and (circle is None): # solo se non fa parte di un arco o di un cerchio
            self.toggleParLine(pt1, pt2)

   def removeReferenceLines(self):
      self.removeExtLines()
      self.removeExtArcs()
      self.removeParLines()
      self.removeIntExtLine()
      self.removeIntExtArc()
      

   #============================================================================
   # setToleranceExtParLines
   #============================================================================
   def setToleranceExtParLines(self, tolerance):
      self.__toleranceExtParlines = tolerance
      

   #============================================================================
   # tmpGeometries
   #============================================================================
   def clearTmpGeometries(self):      
      del self.tmpGeometries[:] # svuoto la lista

   def setTmpGeometry(self, geom, CRS = None):      
      self.clearTmpGeometries()
      self.appendTmpGeometry(geom)

   def appendTmpGeometry(self, geom, CRS = None):
      if geom is None:
         return
      if CRS is not None:
         g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap
         self.tmpGeometries.append(g)
      else:
         self.tmpGeometries.append(geom)

   def setTmpGeometries(self, geoms, CRS = None):      
      self.clearTmpGeometries()
      for g in geoms:
         self.appendTmpGeometry(g, CRS)


   #===========================================================================
   # getSnapPoint
   #===========================================================================
   def getSnapPoint(self, geom, point, CRS, excludePoints = None, polarAng = None, isTemporaryGeom = False):
      """
      Data una geometria ed un punto (posizione del cursore) nel sistema di coordinate CRS 
      ottiene i punti di snap (con esclusione dei punti in excludePoints).
      Resituisce un dizionario di liste di punti di snap
      suddivisi per tipi di snap (es. {END : [pt1 .. ptn] MID : [pt1 .. ptn]})
      - CRS = sistema di coordinate in cui é espressa la geom e il punto (QgsCoordinateReferenceSystem)
      - excludePoints = lista di punti da escludere espressa in __snapPointCRS
      - polarAng angolo in radianti per il puntamento polare
      - isTemporaryGeom flag che indica se geom é  un oggetto temporaneo che ancora non esiste
      """

      p = self.__transformPoint(point, CRS, self.getSnapPointCRS()) # trasformo il punto in coord dei punti di snap
      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap

      # cerca nella cache i punti di snap statici per una geometria
      if geom is not None:
         staticSnapPoints = self.__getCacheSnapPoints(g)
         if staticSnapPoints is None:
            staticSnapPoints = self.getStaticSnapPoints(g, None, isTemporaryGeom)
            self.__setCacheSnapPoints(g, staticSnapPoints)
      else:
         staticSnapPoints = dict()
      
      # snap dinamici  
      dynamicSnapPoints = self.getDynamicSnapPoints(g, p)

      allSnapPoints = staticSnapPoints
      for item in dynamicSnapPoints.items():
         allSnapPoints[item[0]] = item[1]
         
      # puntamento polare
      if (self.__startPoint is not None) and (polarAng is not None):
         allSnapPoints[QadSnapTypeEnum.POLAR] = self.getPolarCoord(point, polarAng)

      if self.__snapMode == QadSnapModeEnum.ONE_RESULT:
         # Viene restituito solo il punto più vicino
         result = self.__getNearestPoints(p, allSnapPoints)
      elif self.__snapMode == QadSnapModeEnum.RESULTS_FOR_SAME_POS:
         # take all snapping Results within a certain tolerance because rounding differences may occur     
         result = self.__getNearestPoints(p, allSnapPoints, 0.000001)
      else:
         result = allSnapPoints # Vengono restituiti tutti i punti
      
      if excludePoints is not None:         
         for p in excludePoints:
            self.__delPoint(p, result)
            
      return result

   #============================================================================
   # CacheSnapPoints
   #============================================================================
   def clearCacheSnapPoints(self):  
      del self.__cacheSnapPoints[:] # svuota la cache
   def __getCacheSnapPoints(self, geom):      
       # cerca i punti di snap per una geometria
      for item in self.__cacheSnapPoints:
         if geom.equals(item[0]) == True:
            return item[1]
      return None
   def __setCacheSnapPoints(self, geom, snapPoints):
      g = QgsGeometry(geom) # copy constructor will prompt a deep copy of the object
      self.__cacheSnapPoints.append([g, snapPoints])


   #============================================================================
   # getStaticSnapPoints
   #============================================================================
   def getStaticSnapPoints(self, geom, CRS = None, isTemporaryGeom = False):
      """
      Data una geometria ottiene i punti di snap statici che non dipendono dalla 
      posizione del cursore.
      Resituisce un dizionario di liste di punti di snap
      suddivisi per tipi di snap (es. {END : [pt1 .. ptn] MID : [pt1 .. ptn]})
      - CRS = sistema di coordinate in cui é espressa la geom  (QgsCoordinateReferenceSystem)
      - isTemporaryGeom flag che indica se geom é  un oggetto temporaneo che ancora non esiste      
      """
     
      result = dict()

      if (self.__snapType & QadSnapTypeEnum.DISABLE):
         return result
      
      if self.__snapType & QadSnapTypeEnum.END:
         result[QadSnapTypeEnum.END] = self.getEndPoints(geom, CRS)
      if self.__snapType & QadSnapTypeEnum.END_PLINE:
         result[QadSnapTypeEnum.END_PLINE] = self.getEndPoints(geom, CRS, QadVertexSearchModeEnum.ONLY_START_END)
      if self.__snapType & QadSnapTypeEnum.MID:
         result[QadSnapTypeEnum.MID] = self.getMidPoints(geom, CRS)
      if self.__snapType & QadSnapTypeEnum.NOD:
         result[QadSnapTypeEnum.NOD] = self.getNodPoint(geom, CRS)      
      if self.__snapType & QadSnapTypeEnum.QUA:
         result[QadSnapTypeEnum.QUA] = self.getQuaPoints(geom, CRS)
      if self.__snapType & QadSnapTypeEnum.INT:
         result[QadSnapTypeEnum.INT] = self.getIntPoints(geom, CRS, isTemporaryGeom)
      if self.__snapType & QadSnapTypeEnum.INS:
         result[QadSnapTypeEnum.INS] = self.getNodPoint(geom, CRS)
      if self.__snapType & QadSnapTypeEnum.APP:
         result[QadSnapTypeEnum.APP] = self.getIntPoints(geom, CRS, isTemporaryGeom)
      if self.__snapType & QadSnapTypeEnum.CEN:
         result[QadSnapTypeEnum.CEN] = self.getCenPoint(geom, CRS)
               
      return result
 
 
   #============================================================================
   # getDynamicSnapPoints
   #============================================================================
   def getDynamicSnapPoints(self, geom, point, CRS = None):
      """
      Data una geometria ottiene i punti di snap dinamici che dipendono dalla 
      posizione del cursore (nel sistema di coordinate di geomLayer) o
      da __startPoint (nel sistema di coordinate __snapPointCRS).
      Resituisce un dizionario di liste di punti di snap
      suddivisi per tipi di snap (es. {END : [pt1 .. ptn] MID : [pt1 .. ptn]})
      - CRS = sistema di coordinate in cui sono espressi geom e point (QgsCoordinateReferenceSystem)
      """
           
      result = dict()

      if (self.__snapType & QadSnapTypeEnum.DISABLE):
         return result
      
      if self.__snapType & QadSnapTypeEnum.PER:
         result[QadSnapTypeEnum.PER] = self.getPerPoints(geom, point, CRS)
      if self.__snapType & QadSnapTypeEnum.TAN:
         result[QadSnapTypeEnum.TAN] = self.getTanPoints(geom, CRS)
      if self.__snapType & QadSnapTypeEnum.NEA:
         result[QadSnapTypeEnum.NEA] = self.getNeaPoints(geom, point, CRS)
      if self.__snapType & QadSnapTypeEnum.EXT:
         result[QadSnapTypeEnum.EXT] = self.getExtPoints(point, CRS)
      if self.__snapType & QadSnapTypeEnum.PAR:
         result[QadSnapTypeEnum.PAR] = self.getParPoints(point, CRS)
      if self.__snapType & QadSnapTypeEnum.PR:
         result[QadSnapTypeEnum.PR] = self.getProgressPoint(geom, point, CRS)[0]
      if self.__snapType & QadSnapTypeEnum.EXT_INT:
         result[QadSnapTypeEnum.EXT_INT] = self.getIntExtPoint(geom, point, CRS)         
      if self.__snapType & QadSnapTypeEnum.PER_DEF:
         result[QadSnapTypeEnum.PER_DEF] = self.getNeaPoints(geom, point, CRS)
      if self.__snapType & QadSnapTypeEnum.TAN_DEF:
         if geom is not None:
            whatIs = qad_utils.whatGeomIs(point, geom)
            if (type(whatIs) != list and type(whatIs) != tuple): # se non é una linea
               result[QadSnapTypeEnum.TAN_DEF] = self.getNeaPoints(geom, point, CRS)
         
      return result


   #============================================================================
   # getEndPoints
   #============================================================================
   def getEndPoints(self, geom, CRS = None, VertexSearchMode = QadVertexSearchModeEnum.ALL):
      """
      Cerca i punti iniziali e finali dei segmenti di una linea o di una multi-linea.
      - CRS = sistema di coordinate in cui é espressa la geom (QgsCoordinateReferenceSystem)
      Ritorna una lista di punti QgsPoint
      """
      result = []

      if geom is None:
         return result
      
      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap
      
      geoms = qad_utils.asPointOrPolyline(g)
      for igeom in geoms:
         if (igeom.wkbType() == QGis.WKBLineString):
            # verifico se ci sono archi
            arcList = QadArcList()
            arcList.fromGeom(igeom)

            # verifico se ci sono cerchi
            circleList = QadCircleList()
            circleList.fromGeom(igeom)                          
            
            points = igeom.asPolyline() # vettore di punti
            i = 1
            vertexCount = len(points)
            for ipoint in points:
               _arc = arcList.arcAt(i - 1)
               _circle = circleList.circleAt(i - 1)
               
               if _arc is not None: # se questo punto appartiene ad un arco
                  startEnd = _arc[1]
                  # se il punto corrisponde al punto iniziale o finale dell'arco
                  # (i - 1) perché arcAt vuole il secondo punto del segmento 
                  if i - 1 == startEnd[0] or i - 1 == startEnd[1]:
                     inser = True
                  else:
                     inser = False                                
               elif _circle is not None: # se questo punto appartiene ad un cerchio
                  inser = False
               else: # se questo punto non appartiene né ad un arco ne ad un cerchio 
                  inser = True
               
               if inser == True:
                  if (VertexSearchMode == QadVertexSearchModeEnum.EXCLUDE_START_END):
                     if (i != 1 and i != vertexCount):
                        self.__appendUniquePoint(result, ipoint, CRS) # aggiungo senza duplicazione
                  elif (VertexSearchMode == QadVertexSearchModeEnum.ONLY_START_END):
                     if (i == 1 or i == vertexCount):
                        self.__appendUniquePoint(result, ipoint) # aggiungo senza duplicazione
                  else:
                     self.__appendUniquePoint(result, ipoint) # aggiungo senza duplicazione
                  
               i = i + 1            
      
      return result


   #============================================================================
   # getMidPoints
   #============================================================================
   def getMidPoints(self, geom, CRS = None):
      """
      Cerca i punti medi dei segmenti di una linea o di una multi-linea.
      - CRS = sistema di coordinate in cui é espressa la geom (QgsCoordinateReferenceSystem)
      Ritorna una lista di punti QgsPoint
      """
      result = []

      if geom is None:
         return result
      
      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap
      
      geoms = qad_utils.asPointOrPolyline(g)
      for igeom in geoms:
         if (igeom.wkbType() == QGis.WKBLineString):
            # verifico se ci sono archi
            arcList = QadArcList()
            if arcList.fromGeom(igeom) > 0:
               for arc in arcList.arcList:
                  self.__appendUniquePoint(result, arc.getMiddlePt()) # senza duplicazione                 
            
            # verifico se ci sono cerchi
            circleList = QadCircleList()
            circleList.fromGeom(igeom)                          
            
            points = igeom.asPolyline() # vettore di punti
            first = True
            i = 0
            for ipoint in points:
               if first == True:
                  first = False
               else:
                  # se questo punto non appartiene ad un arco né ad un cerchio
                  if (arcList.arcAt(i) is None) and (circleList.circleAt(i) is None):                  
                     point = qad_utils.getMiddlePoint(prevPoint, ipoint)
                     self.__appendUniquePoint(result, point) # senza duplicazione
               prevPoint = ipoint
               i = i + 1
               
      return result


   #============================================================================
   # getCenPoint
   #============================================================================
   def getCenPoint(self, geom, CRS = None):
      """
      Cerca i punti centrali di archi, cerchi e centroidi presenti nella geometria.
      - CRS = sistema di coordinate in cui é espressa la geom (QgsCoordinateReferenceSystem)
      Ritorna una lista di punti QgsPoint
      """
      result = []

      if geom is None:
         return result

      wkbType = geom.wkbType()
      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap

      # se si tratta di poligono o multipoligono
      if wkbType == QGis.WKBPolygon or wkbType == QGis.WKBMultiPolygon:
         # leggo il/i centroidi
         centroidGeom = g.centroid()
         wkbType = centroidGeom.wkbType()
         if wkbType == QGis.WKBPoint:
            self.__appendUniquePoint(result, centroidGeom.asPoint()) # senza duplicazione
         elif wkbType == QGis.WKBMultiPoint:
            for centroidPt in centroidGeom.asMultiPoint(): # vettore di punti
               self.__appendUniquePoint(result, centroidGeom.asPoint()) # senza duplicazione         

      # cerco i cerchi e gli archi presenti in geom
      geoms = qad_utils.asPointOrPolyline(g)
      for igeom in geoms:
         if (igeom.wkbType() == QGis.WKBLineString):
            # verifico se ci sono archi
            arcList = QadArcList()
            if arcList.fromGeom(igeom) > 0:
               for arc in arcList.arcList:
                  self.__appendUniquePoint(result, arc.center) # senza duplicazione
            
            # verifico se ci sono cerchi
            circleList = QadCircleList()
            if circleList.fromGeom(igeom) > 0:
               for circle in circleList.circleList:
                  self.__appendUniquePoint(result, circle.center) # senza duplicazione

      return result







      wkbType = geom.wkbType()

      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>)
      dummy = qad_utils.closestSegmentWithContext(point, geom)
      afterVertex = dummy[2]
      if afterVertex is None:
         return result

      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap
      
      # verifico se ci sono cerchi
      circleList = QadCircleList()
      if circleList.fromGeom(g) > 0:
         info = circleList.circleAt(afterVertex)
         if info is not None:
            circle = info[0]
            self.__appendUniquePoint(result, circle.center) # senza duplicazione                 

      # verifico se ci sono archi         
      arcList = QadArcList()
      if arcList.fromGeom(g) > 0:        
         info = arcList.arcAt(afterVertex)
         if info is not None:
            arc = info[0]
            self.__appendUniquePoint(result, arc.center) # senza duplicazione                 
               
      return result


   #============================================================================
   # getNodPoint
   #============================================================================
   def getNodPoint(self, geom, CRS = None):
      """
      Cerca il punto di inserimento di un punto.
      - CRS = sistema di coordinate in cui é espressa la geom (QgsCoordinateReferenceSystem)
      Ritorna una lista di punti QgsPoint
      """
      result = []

      if geom is None:
         return result
      
      wkbType = geom.wkbType()
      if wkbType != QGis.WKBPoint and wkbType != QGis.WKBMultiPoint:
         return result
      
      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap
      
      if wkbType == QGis.WKBPoint:
         self.__appendUniquePoint(result, g.asPoint()) # senza duplicazione
      elif wkbType == QGis.WKBMultiPoint:
         for point in g.asMultiPoint(): # vettore di punti 
            self.__appendUniquePoint(result, point) # senza duplicazione
      return result 


   #============================================================================
   # getQuaPoints
   #============================================================================
   def getQuaPoints(self, geom, CRS = None):
      """
      Cerca i punti quadrante.
      - CRS = sistema di coordinate in cui é espressa la geom (QgsCoordinateReferenceSystem)
      Ritorna una lista di punti QgsPoint
      """
      result = []
      
      if geom is None:
         return result
      
      wkbType = geom.wkbType()
      if wkbType == QGis.WKBPoint or wkbType == QGis.WKBMultiPoint:
         return result
      
      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap

      if wkbType == QGis.WKBLineString or wkbType == QGis.WKBMultiLineString:
         # verifico se ci sono archi
         arcList = QadArcList()
         if arcList.fromGeom(g) > 0:
            for arc in arcList.arcList:
               points = arc.getQuadrantPoints()
               for point in points:
                  self.__appendUniquePoint(result, point) # senza duplicazione
      else:
         # verifico se ci sono cerchi
         circleList = QadCircleList()
         if circleList.fromGeom(g) > 0:                          
            for circle in circleList.circleList:
               points = circle.getQuadrantPoints()
               for point in points:
                  self.__appendUniquePoint(result, point) # senza duplicazione
      
      return result


   #============================================================================
   # getIntPoints
   #============================================================================
   def getIntPoints(self, geom, CRS = None, isTemporaryGeom = False):
      """
      Cerca i punti di intersezione di un oggetto.
      - CRS = sistema di coordinate in cui é espressa la geom (QgsCoordinateReferenceSystem)
      - isTemporaryGeom flag che indica se geom é un oggetto temporaneo che ancora non esiste
      Ritorna una lista di punti QgsPoint
      """
      result = []

      if geom is None:
         return result

      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap
      
      for iLayer in self.__snapLayers: # ciclo sui layer da controllare
         if (iLayer.type() == QgsMapLayer.VectorLayer):
            iLayerCRS = iLayer.crs()
            geom_iLayerCoords = QgsGeometry(g)
            if CRS is None: # se non c'é CRS la geom si intende nel sistema di coord dei punti di snap
               coordTransform = QgsCoordinateTransform(self.getSnapPointCRS(), iLayerCRS) # trasformo in coord ilayer
               geom_iLayerCoords.transform(coordTransform)
            else:
               coordTransform = QgsCoordinateTransform(CRS, iLayerCRS) # trasformo in coord ilayer
               geom_iLayerCoords.transform(coordTransform)

            feature = QgsFeature()
            # cerco le entità che intersecano il rettangolo
            # fetchAttributes, fetchGeometry, rectangle, useIntersect             
            for feature in iLayer.getFeatures(qad_utils.getFeatureRequest([], True, geom_iLayerCoords.boundingBox(), True)):
               g2 = self.__transformGeomToSnapPointCRS(feature.geometry(), iLayerCRS) # trasformo la geometria in coord dei punti di snap
               intersectionPoints = qad_utils.getIntersectionPoints(g, g2)
               if intersectionPoints is not None:
                  for point in intersectionPoints:
                     # trasformo il punto in coord layer
                     self.__appendUniquePoint(result, point) # senza duplicazione
                     
      if isTemporaryGeom:
         intersectionPoints = qad_utils.getIntersectionPoints(g, g)
         if intersectionPoints is not None:
            for point in intersectionPoints:
               # trasformo il punto in coord layer
               self.__appendUniquePoint(result, point) # senza duplicazione

      # lista di geometria non ancora esistenti ma da contare per i punti di osnap (in map coordinates)
      for tmpGeometry in self.tmpGeometries:
         intersectionPoints = qad_utils.getIntersectionPoints(g, tmpGeometry)
         if intersectionPoints is not None:
            for point in intersectionPoints:
               # trasformo il punto in coord layer
               self.__appendUniquePoint(result, point) # senza duplicazione
         
      return result
            

   #============================================================================
   # Inizio punti dinamici
   #============================================================================

            
   #============================================================================
   # getPerPoints
   #============================================================================
   def getPerPoints(self, geom, point, CRS = None):
      """
      Cerca il punto proiezione perpendicolare di self.__startPoint 
      (espresso in __snapPointCRS) sul lato di geom più vicino a point.
      - CRS = sistema di coordinate in cui sono espressi geom e point (QgsCoordinateReferenceSystem)
      Ritorna una lista di punti QgsPoint 
      """         
      result = []
      
      if geom is None:
         return result
      
      if self.__startPoint is None:
         return result
      
      # trasformo il self.__startPoint dal sistema __snapPointCRS a quello della geometria
      startPointCRS = self.__transformPoint(self.__startPoint, self.getSnapPointCRS(), CRS)
      
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>)
      dummy = qad_utils.closestSegmentWithContext(point, geom)
      afterVertex = dummy[2]
      if afterVertex is None:
         return result

      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap

      # verifico se ci sono archi
      arcList = QadArcList()
      if arcList.fromGeom(g) > 0:
         info = arcList.arcAt(afterVertex)
         if info is not None:
            arc = info[0]
            PerpendicularPoints = arc.getPerpendicularPoints(startPointCRS)
            if PerpendicularPoints is not None:
               for PerpendicularPoint in PerpendicularPoints:
                  # trasformo il punto in coord layer
                  self.__appendUniquePoint(result, PerpendicularPoint) # senza duplicazione
               return result

      # verifico se ci sono cerchi
      circleList = QadCircleList()
      if circleList.fromGeom(g) > 0:                          
         info = circleList.circleAt(afterVertex)
         if info is not None:
            circle = info[0]
            PerpendicularPoints = circle.getPerpendicularPoints(startPointCRS)
            if PerpendicularPoints is not None:
               for PerpendicularPoint in PerpendicularPoints:
                  # trasformo il punto in coord layer
                  self.__appendUniquePoint(result, PerpendicularPoint) # senza duplicazione
               return result

      pt1 = g.vertexAt(afterVertex - 1)   
      pt2 = g.vertexAt(afterVertex)   
      PerpendicularPoint = qad_utils.getPerpendicularPointOnInfinityLine(pt1, pt2, startPointCRS)
      self.__appendUniquePoint(result, PerpendicularPoint) # senza duplicazione

      return result


   #============================================================================
   # getTanPoints
   #============================================================================
   def getTanPoints(self, geom, CRS = None):
      """
      Cerca i punti di un oggetto che sono tangenti alla retta passante per self.__startPoint 
      (espresso in __snapPointCRS).
      - CRS = sistema di coordinate in cui sono espressi geom e point (QgsCoordinateReferenceSystem)
      Ritorna una lista di punti QgsPoint
      """
      result = []
      
      if geom is None:
         return result
      
      if self.__startPoint is None:
         return result

      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap

      # verifico se ci sono archi
      arcList = QadArcList()
      if arcList.fromGeom(g) > 0:
         for arc in arcList.arcList:
            points = arc.getTanPoints(self.__startPoint)
            for point in points:
               self.__appendUniquePoint(result, point) # senza duplicazione

      # verifico se ci sono cerchi
      circleList = QadCircleList()
      if circleList.fromGeom(g) > 0:
         for circle in circleList.circleList:
            points = circle.getTanPoints(self.__startPoint)
            for point in points:
               self.__appendUniquePoint(result, point) # senza duplicazione

      return result


   #============================================================================
   # getNeaPoints
   #============================================================================
   def getNeaPoints(self, geom, point, CRS = None):
      """
      Cerca il punto di un oggetto che é più vicino a point.
      - CRS = sistema di coordinate in cui sono espressi geom e point (QgsCoordinateReferenceSystem)
      Ritorna una lista di punti QgsPoint
      """
      result = []

      if geom is None:
         return result     
      
      p = self.__transformPoint(point, CRS, self.getSnapPointCRS()) # trasformo il punto in coord dei punti di snap
      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap
      
      # Riduco le geometrie in point o polyline
      geoms = qad_utils.asPointOrPolyline(g)

      first = True               
      for g in geoms:     
         if g.wkbType() == QGis.WKBPoint:
            pt = g.asPoint()
         else:
            # ritorna una tupla (<The squared cartesian distance>,
            #                    <minDistPoint>
            #                    <afterVertex>)
            dummy = qad_utils.closestSegmentWithContext(p, g)
            pt = dummy[1]

         dist = qad_utils.getDistance(p, pt)
         if first == True:
            first = False
            minDist = dist
            closestPoint = pt
         elif dist < minDist:
            minDist = dist
            closestPoint = pt
         
      self.__appendUniquePoint(result, closestPoint) # senza duplicazione
      
      return result


   #============================================================================
   # toggleExtLine
   #============================================================================
   def toggleExtLine(self, pt1, pt2, CRS = None):
      """
      Aggiunge una linea per la ricerca di punti con modalità EXT (estensione)
      se non ancora inserita in lista altrimenti la rimuove dalla lista
      pt1 e pt2 sono QgsPoint
      sourceCRS é QgsCoordinateReferenceSystem opzionale
      """
      self.toggleLine(QadSnapTypeEnum.EXT, pt1, pt2, CRS)

   def removeExtLines(self):
      """
      Elimina tutte le linee per la ricerca di punti con modalità EXT (estensione)
      """
      del self.__extLines[:] # svuoto la lista

   def getExtLines(self):
      return self.__extLines

   def toggleExtArc(self, arc, CRS = None):
      """
      Aggiunge un arco per la ricerca di punti con modalità EXT (estensione)
      se non ancora inserito in lista altrimenti lo rimuove dalla lista
      sourceCRS é QgsCoordinateReferenceSystem opzionale
      """
      self.toggleArc(QadSnapTypeEnum.EXT, arc, CRS)   

   def removeExtArcs(self):
      """
      Elimina tutte gli archi per la ricerca di punti con modalità EXT (estensione)
      """
      del self.__extArcs[:] # svuoto la lista

   def getExtArcs(self):
      return self.__extArcs

   def getExtPoints(self, point, CRS):
      """
      Cerca i punti sui prolungamenti delle linee memorizzate nella lista __extLines e __extArcs.
      N.B. __extLines e point vanno espressi nello stesso sistema di coordinate
      - point é un QgsPoint
      - CRS = sistema di coordinate in cui é espresso point (QgsCoordinateReferenceSystem)
      Ritorna una lista di punti QgsPoint
      """
      result = []
      pt = self.__transformPoint(point, CRS, self.getSnapPointCRS()) # trasformo il punto
      
      if len(self.__extLines) > 0:         
         for line in self.__extLines:
            ExtPoint = qad_utils.getPerpendicularPointOnInfinityLine(line[0], line[1], pt)
            if qad_utils.getDistance(pt, ExtPoint) <= self.__toleranceExtParlines:
               self.__appendUniquePoint(result, ExtPoint) # senza duplicazione

      if len(self.__extArcs) > 0:
         circle = QadCircle()
         for arc in self.__extArcs:
            circle.set(arc.center,arc.radius)
            ExtPoints = circle.getPerpendicularPoints(pt)
            if ExtPoints is not None:
               for ExtPoint in ExtPoints:
                  if qad_utils.getDistance(pt, ExtPoint) <= self.__toleranceExtParlines:
                     self.__appendUniquePoint(result, ExtPoint) # senza duplicazione
            
      return result

      
   #============================================================================
   # getParPoints
   #============================================================================      
   def toggleParLine(self, pt1, pt2, CRS = None):
      """
      Aggiunge una linea per la ricerca di punti con modalità PAR (parallela)
      se non ancora inserita in lista altrimenti la rimuove dalla lista
      pt1 e pt2 sono QgsPoint
      sourceCRS é QgsCoordinateReferenceSystem opzionale
      """
      self.toggleLine(QadSnapTypeEnum.PAR, pt1, pt2, CRS)   

   def removeParLines(self):
      """
      Elimina tutte le linee per la ricerca di punti con modalità PAR (parallela)
      """
      del self.__parLines[:] # svuoto la lista

   def getParLines(self):
      return self.__parLines
   
   def getParPoints(self, point, CRS):
      """
      Cerca i punti sulle rette parallele alle linee memorizzate nella lista __partLines
      che passano per __startPoint e che sono più vicino a point.
      N.B. __parLines, __startPoint e point vanno espressi nello stesso sistema di coordinate
      - line é una lista di 2 punti
      - point é un QgsPoint
      - CRS = sistema di coordinate in cui é espresso point (QgsCoordinateReferenceSystem)
      Ritorna una lista di punti QgsPoint
      """
      result = []
      
      if (self.__startPoint is None) or len(self.__parLines) == 0:
         return result
            
      p2 = QgsPoint(0, 0)
      pt = self.__transformPoint(point, CRS, self.getSnapPointCRS()) # trasformo il punto
     
      for line in self.__parLines:
         pt1 = line[0]
         pt2 = line[1]
         diffX = pt2.x() - pt1.x()
         diffY = pt2.y() - pt1.y()
                                                  
         if diffX == 0: # se la retta passante per pt1 e pt2 é verticale
            parPoint = QgsPoint(self.__startPoint.x(), pt.y())
         elif diffY == 0: # se la retta passante per pt1 e pt2 é orizzontle
            parPoint = QgsPoint(pt.x(), self.__startPoint.y())
         else:
            # Calcolo l'equazione della retta passante per __startPoint con coefficente angolare noto
            p2.setX(self.__startPoint.x() + diffX)
            p2.setY(self.__startPoint.y() + diffY)
            parPoint = qad_utils.getPerpendicularPointOnInfinityLine(self.__startPoint, p2, pt)

         if qad_utils.getDistance(pt, parPoint) <= self.__toleranceExtParlines:
            self.__appendUniquePoint(result, parPoint, CRS) # senza duplicazione

      return result


   #============================================================================
   # getProgressPoint
   #============================================================================
   def setProgressDistance(self, progressDistance):
      """
      Setta la distanza progressiva dall'inizio nel sistema __snapPointCRS 
      per la ricerca con modalità PR (progressiva)
      """
      self.__progressDistance = progressDistance
      
   def getProgressDistance(self,):
      return self.__progressDistance


   def __getOverPoint(self, geom, points, pt1, pt2, dist):
      """
      Cerca il punto sulla geometria che si estende oltre il punto pt2
      Ritorna il punto e il coeff. angolare in quel punto. usato da <getProgressPoint>
      """
      # verifico se ci sono archi
      arc = None
      arcList = QadArcList()
      if arcList.fromGeom(geom) > 0:
         info = arcList.arcAt(len(points) - 1)
         if info is not None:
            arc = info[0]

      if arc is None: # se questo punto non appartiene ad un arco
         overPoint = qad_utils.getPolarPointBy2Pts(pt1, pt2, dist)
         overAngle = qad_utils.getAngleBy2Pts(pt1, pt2)                                     
      else:  # se questo punto appartiene ad un arco
         angle = dist / arc.radius
         if arc.getStartPt() == pt2:
            overPoint = qad_utils.getPolarPointByPtAngle(arc.center,
                                                         arc.startAngle - angle,
                                                         arc.radius)
            overAngle = angle - (math.pi / 2)               
         else:
            overPoint = qad_utils.getPolarPointByPtAngle(arc.center,
                                                         arc.endAngle + angle,
                                                         arc.radius)
            overAngle = angle + (math.pi / 2)               
      
      return [overPoint, overAngle]


   def getProgressPoint(self, geom, point, CRS = None):
      """
      Cerca il punto sulla geometria ad un certa distanza dal vertice più vicino al punto
      (se la distanza >=0 significa verso dall'inizio alla fine della linea,
      se la distanza < 0 significa verso dalla fine all'inizio della linea.
      - CRS = sistema di coordinate in cui sono espressi geom e point (QgsCoordinateReferenceSystem)
      Ritorna una lista di punti QgsPoint + una lista di coefficienti angolari dei segmenti
      su cui ricadono i punti
      """
      result = [[],[]]
      if geom is None:
         return result     

      if geom.wkbType() != QGis.WKBLineString:
         return result
      
      ProgressPoints = []
      segmentAngles = []
     
      p = self.__transformPoint(point, CRS, self.getSnapPointCRS()) # trasformo il punto in coord dei punti di snap
      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap
      
      # Cerca i punti iniziali e finali dei segmenti di una linea.
      Vertexes = self.getEndPoints(g, CRS)     
      
      # Cerco il vertice più vicino
      points = qad_utils.getNearestPoints(p, Vertexes)
      if len(points) == 0:
         return result
      nearestPoint = points[0]
      points = g.asPolyline() # vettore di punti
      i = 0
      for iPoint in points:
         if iPoint == nearestPoint:
            break
         i = i + 1
         
      if self.__progressDistance == 0:
         ProgressPoints.append(iPoint)
         if i == (len(points) - 1): # ultimo punto
            segmentAngles.append(qad_utils.getAngleBy2Pts(points[i - 1], points[i]))
         else:
            segmentAngles.append(qad_utils.getAngleBy2Pts(points[i], points[i + 1]))

      elif self.__progressDistance > 0:
         # dall'inizio della linea verso la fine
         remain = self.__progressDistance
         if i == len(points) - 1: # selezionato ultimo vertice
            pt1 = points[i - 1]
            pt2 = points[i]
            
            info = self.__getOverPoint(geom, points, pt1, pt2, remain)
            ProgressPoints.append(info[0])
            segmentAngles.append(info[1])               
         else:         
            while remain > 0 and i < len(points) - 1:
               pt1 = points[i]
               pt2 = points[i + 1]
               segmentLength = qad_utils.getDistance(pt1, pt2)
               if segmentLength < remain:
                  # vado al segmento successivo
                  i = i + 1
                  remain = remain - segmentLength
                  if i == len(points) - 1: # ultimo segmento quindi vado oltre
                     info = self.__getOverPoint(geom, points, pt1, pt2, remain)
                     ProgressPoints.append(info[0])
                     segmentAngles.append(info[1])                           
                     break
               elif segmentLength > remain:
                  # é in questo segmento
                  ProgressPoints.append(qad_utils.getPolarPointBy2Pts(pt1, pt2, remain))
                  segmentAngles.append(qad_utils.getAngleBy2Pts(pt1, pt2))               
                  break
               else: # era esattamente il punto p2
                  ProgressPoints.append(p2)
                  segmentAngles.append(qad_utils.getAngleBy2Pts(pt1, pt2))               
                  break         
      else:         
         # dalla fine della linea verso l'inizio
         remain = self.__progressDistance * -1
                 
         if i == 0: # selezionato primo vertice
            pt1 = points[1]
            pt2 = points[0]
            ProgressPoints.append(qad_utils.getPolarPointBy2Pts(pt2, pt1, -1 * remain))
            segmentAngles.append(qad_utils.getAngleBy2Pts(pt2, pt1))               
         else:         
            while remain > 0 and i > 0:
               pt1 = points[i]
               pt2 = points[i - 1]
               segmentLength = qad_utils.getDistance(pt1, pt2)
               if segmentLength < remain:
                  # vado al segmento precedente
                  i = i - 1
                  remain = remain - segmentLength
                  if i == 0: # primo segmento quindi vado oltre
                     info = self.__getOverPoint(geom, points, pt1, pt2, remain)
                     ProgressPoints.append(info[0])
                     segmentAngles.append(info[1])                                                              
                     break               
               elif segmentLength > remain:
                  # cerco nel segmento corrente
                  ProgressPoints.append(qad_utils.getPolarPointBy2Pts(pt1, pt2, remain))
                  segmentAngles.append(qad_utils.getAngleBy2Pts(pt2, pt1))               
                  break
               else: # era esattamente il punto p2
                  ProgressPoints.append(p2)
                  segmentAngles.append(qad_utils.getAngleBy2Pts(pt2, pt1))               
                  break
      
      return (ProgressPoints, segmentAngles)
         
      
   #============================================================================
   # toggleIntExtLine
   #============================================================================      
   def toggleIntExtLine(self, geom, point, CRS = None):
      """
      Aggiunge una linea per la ricerca di punti con modalità EXT_INT (intersezione su estensione)
      se non ancora inserita altrimenti la rimuove dalla lista
      CRS é QgsCoordinateReferenceSystem opzionale
      """
      # usato solo per snap EXT_INT
      if not (self.__snapType & QadSnapTypeEnum.EXT_INT):
         return
      
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>)
      dummy = qad_utils.closestSegmentWithContext(point, geom)
      afterVertex = dummy[2]
      if afterVertex is None:
         return result

      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap

      # verifico se ci sono archi
      arc = None
      arcList = QadArcList()
      if arcList.fromGeom(g) > 0:
         info = arcList.arcAt(afterVertex)
         if info is not None:
            arc = info[0]
            
      circle = None

      if arc is not None: # se fa parte di un arco
         _arc = QadArc(arc)
         _arc.transformFromCRSToCRS(CRS, self.getSnapPointCRS()) # trasformo l'arco in coord layer

         # se non é stato selezionato alcun arco o alcuna linea lo aggiungo 
         if len(self.__intExtArc) == 0 and len(self.__intExtLine) == 0:
            self.__intExtArc.append(_arc)
         elif len(self.__intExtArc) > 0:
            # se era già stato selezionato lo rimuovo
            if (_arc == self.__intExtArc[0]):
               self.removeIntExtArc()
      elif circle is None: # se non fa parte di un cerchio
         pt1 = g.vertexAt(afterVertex - 1)   
         pt2 = g.vertexAt(afterVertex)   
                     
         if CRS is not None:
            __pt1 = self.__transformPoint(pt1, CRS, self.getSnapPointCRS()) # trasformo il punto in coord layer
            __pt2 = self.__transformPoint(pt2, CRS, self.getSnapPointCRS()) # trasformo il punto in coord layer
         else:
            __pt1 = pt1
            __pt2 = pt2
                  
         # se non é stato selezionato alcun arco o alcuna linea la aggiungo 
         if len(self.__intExtArc) == 0 and len(self.__intExtLine) == 0:
            self.__intExtLine.append(__pt1)
            self.__intExtLine.append(__pt2)
         elif len(self.__intExtLine) > 0:
            # se era già stata selezionata la rimuovo
            if (__pt1 == self.__intExtLine[0] or __pt1 == self.__intExtLine[1]) and \
               (__pt2 == self.__intExtLine[0] or __pt2 == self.__intExtLine[1]):
               self.removeIntExtLine()


   def removeIntExtLine(self):
      """
      Elimina la linea per la ricerca di punti con modalità EXT_INT (intersezione su estensione)
      """
      del self.__intExtLine[:] # svuoto la lista

   def getIntExtLine(self):
      return self.__intExtLine

   def removeIntExtArc(self):
      """
      Elimina l'arco per la ricerca di punti con modalità EXT_INT (intersezione su estensione)
      """
      del self.__intExtArc[:] # svuoto la lista

   def getIntExtArc(self):
      return self.__intExtArc
   
   def getIntExtPoint(self, geom, point, CRS = None):
      """
      Cerca il punto di intersezione tra la geometria e una linea memorizzata in __intExtLine
      - __intExtLine é lista di 2 punti = linea, > 2 punti = arco
      - CRS = sistema di coordinate in cui é espressa geom (QgsCoordinateReferenceSystem)
      Ritorna una lista di punti QgsPoint
      """
      result = []

      if geom is None:
         return result     
      
      # se non é stato selezionato alcun arco o alcuna linea
      if len(self.__intExtArc) == 0 and len(self.__intExtLine) == 0:
         return result

      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>)
      dummy = qad_utils.closestSegmentWithContext(point, geom)
      afterVertex = dummy[2]
      if afterVertex is None:
         return result
      g = self.__transformGeomToSnapPointCRS(geom, CRS) # trasformo la geometria in coord dei punti di snap
     
      # verifico se ci sono archi
      arc = None
      arcList = QadArcList()
      if arcList.fromGeom(g) > 0:
         info = arcList.arcAt(afterVertex)
         if info is not None:
            arc = info[0]

      if arc is None:
         # verifico se ci sono cerchi
         circle = None
         circleList = QadCircleList()
         if circleList.fromGeom(g) > 0:
            info = circleList.circleAt(afterVertex)
            if info is not None:
               circle = info[0]

      if (arc is None) and (circle is None): # nessun arco e cerchio
         p1 = self.__transformPoint(g.vertexAt(afterVertex - 1), CRS, self.getSnapPointCRS()) # trasformo il punto
         p2 = self.__transformPoint(g.vertexAt(afterVertex), CRS, self.getSnapPointCRS()) # trasformo il punto
          
      if len(self.__intExtArc) > 0:
         circle1 = QadCircle()
         circle1.set(self.__intExtArc[0].center, self.__intExtArc[0].radius)
         
         if arc is not None:  # intersezione tra arco ed arco           
            circle2 = QadCircle()
            circle2.set(arc.center, arc.radius)                        
            intExtPoints = circle1.getIntersectionPointsWithCircle(circle2)
         elif circle is not None: # intersezione tra cerchio ed arco
            intExtPoints = circle1.getIntersectionPointsWithCircle(circle)
         else: # intersezione tra linea ed arco
            intExtPoints = circle1.getIntersectionPointsWithInfinityLine(p1, p2)               
      else:
         if arc is not None:  # intersezione tra arco e linea    
            circle1 = QadCircle()
            circle1.set(arc.center, arc.radius)
            intExtPoints = circle1.getIntersectionPointsWithInfinityLine(self.__intExtLine[0], self.__intExtLine[1])
         elif circle is not None: # intersezione tra cerchio e linea
            intExtPoints = circle.getIntersectionPointsWithInfinityLine(self.__intExtLine[0], self.__intExtLine[1])
         else: # intersezione tra linea e linea
            intExtPoints = []
            intExtPoint = qad_utils.getIntersectionPointOn2InfinityLines(self.__intExtLine[0], \
                                                                         self.__intExtLine[1], \
                                                                         p1, p2)
            if intExtPoint is not None:
               intExtPoints.append(intExtPoint)
               
      for intExtPoint in intExtPoints:
         self.__appendUniquePoint(result, intExtPoint, CRS) # senza duplicazione         

      return result


   #============================================================================
   # utiliy functions
   #============================================================================
   def __appendUniquePoint(self, pointList, point, CRS = None):
      """
      Aggiunge un punto alla lista verificando che non sia già presente.
      Resituisce True se l'inserimento é avvenuto False se il punto c'era già.
      """
      _point = self.__transformPoint(point, CRS, self.getSnapPointCRS()) # trasformo il punto
      return qad_utils.appendUniquePointToList(pointList, _point)


   def __layerToMapCoordinatesPointList(self, pointList, layer, mQgsMapRenderer):
      """
      Trasforma una lista punti da coordinate layer a coordinate map.
      """
      i = 0
      for point in pointList:
         pointList[i] = mQgsMapRenderer.layerToMapCoordinates(layer, point)
         i = i + 1

                        
   def __layerToMapCoordinatesRect(self, rect, layer, mQgsMapRenderer):
      """
      Trasforma un rettangolo da coordinate layer a coordinate map.
      """
      point = QgsPoint()
      point.set(rect.xMinimum(), rect.yMinimum())
      point = mQgsMapRenderer.layerToMapCoordinates(layer, point)
      rect.setXMinimum(point.x())
      rect.setYMinimum(point.y())
      point.set(rect.xMaximum(), rect.yMaximum())
      rect.setXMaximum(point.x())
      rect.setYMaximum(point.y())
      return rect

   def __transformPoint(self, point, sourceCRS, destCRS):
      """
      Trasforma un punto dal sistema di coordinate sorgente a quello di destinazione.
      sourceCRS e destCRS sono QgsCoordinateReferenceSystem
      """      
      if (sourceCRS is not None) and (destCRS is not None) and sourceCRS != destCRS:       
         coordTransform = QgsCoordinateTransform(sourceCRS, destCRS) # trasformo le coord
         return coordTransform.transform(point)
      else:
         return point

   def __transformGeomToSnapPointCRS(self, geom, CRS = None):
      """
      Trasformala geometria nel sistema di coordinate dei punti di snap
      CRS é QgsCoordinateReferenceSystem della geometria
      """
      if geom is None:
         return None
      
      g = QgsGeometry(geom)
      if (CRS is not None) and (self.getSnapPointCRS() is not None) and CRS != self.getSnapPointCRS():       
         coordTransform = QgsCoordinateTransform(CRS, self.getSnapPointCRS()) # trasformo la geometria
         g.transform(coordTransform)
      return g
      
   def __getNearestPoints(self, point, SnapPoints, tolerance = 0):
      """
      Ritorna una lista con il primo elemento che é il tipo di snap e 
      il secondo elemento é il punto più vicino a point.
      SnapPoints é un dizionario di liste di punti di snap
      suddivisi per tipi di snap (es. {END : [pt1 .. ptn] MID : [pt1 .. ptn]})
      """   
      result = dict()   
      minDist = sys.float_info.max
      
      if tolerance == 0: # solo il punto più vicino
         for item in SnapPoints.items():
            # escludo NEA che tratto dopo
            if (item[0] != QadSnapTypeEnum.NEA) and (item[1] is not None):
               for pt in item[1]:
                  dist = qad_utils.getDistance(point, pt)
                  if dist < minDist:
                     minDist = dist
                     snapType = item[0]
                     NearestPoint = pt

         # se il punto trovato é più distante di <__distToExcludeNea> allora considero anche
         # eventuali punti NEA
         if minDist > self.__distToExcludeNea:            
            # se é stato selezionato lo snap di tipo NEA
            if QadSnapTypeEnum.NEA in SnapPoints.keys():
               items = SnapPoints[QadSnapTypeEnum.NEA]
               if (items is not None):
                  for pt in items:
                     dist = qad_utils.getDistance(point, pt)
                     if dist < minDist:
                        minDist = dist
                        snapType = QadSnapTypeEnum.NEA
                        NearestPoint = pt

         if minDist != sys.float_info.max: # trovato
            result[snapType] = [NearestPoint]

      else:
         nearest = self.__getNearestPoints(point, SnapPoints) # punto più vicino
         dummy = nearest.items()
         dummy = dummy[0]
         NearestPoint = dummy[1]
         
         for item in SnapPoints.items():
            NearestPoints = []
            for pt in item[1]:
               dist = qad_utils.getDistance(NearestPoint, pt)
               if dist <= tolerance:
                  NearestPoints.append(pt)

            if len(NearestPoints) > 0:
               snapType = item[0]             
               result[snapType] = NearestPoint
      
      return result

   def __delPoint(self, point, SnapPoints):
      """
      Cancella dalla lista SnapPoints il punto point (se esiste) 
      SnapPoints é un dizionario di liste di punti di snap
      suddivisi per tipi di snap (es. {END : [pt1 .. ptn] MID : [pt1 .. ptn]})
      """   
      for item in SnapPoints.items():
         i = 0
         for pt in item[1]:            
            if pt == point:
               del item[1][i]
            i = i + 1

   def toggleLine(self, snapType, pt1, pt2, CRS = None):
      """
      Aggiunge una linea per la ricerca di punti con modalità EXT p PAR
      se non ancora inserita in lista altrimenti la rimuove dalla lista
      pt1 e pt2 sono QgsPoint
      CRS é QgsCoordinateReferenceSystem opzionale
      """
      __pt1 = QgsPoint(0, 0)
      __pt2 = QgsPoint(0, 0)
      
      if snapType == QadSnapTypeEnum.EXT:
         lines = self.__extLines
      elif snapType == QadSnapTypeEnum.PAR:
         lines = self.__parLines
      else:
         return
      
      if CRS is not None:
         __pt1 = self.__transformPoint(pt1, CRS, self.getSnapPointCRS()) # trasformo il punto in coord layer
         __pt2 = self.__transformPoint(pt2, CRS, self.getSnapPointCRS()) # trasformo il punto in coord layer
      else:
         __pt1 = pt1
         __pt2 = pt2
      
      # verifico che non ci sia già
      exist = False
      for line in lines:
         if (__pt1 == line[0] or __pt1 == line[1]) and (__pt2 == line[0] or __pt2 == line[1]):
            exist = True
            if __pt1 != line[0]:
               invertPoints = True
            else:
               invertPoints = False
            break
         
      if exist == False:
         # se non esiste ancora la aggiungo
         line = [__pt1, __pt2]
         lines.append(line)
      else:
         # se esiste di già la rimuovo
         if invertPoints == True:
            line = [__pt2, __pt1]
         else:
            line = [__pt1, __pt2]
         lines.remove(line)     
              
   def toggleArc(self, snapType, arc, CRS = None):
      """
      Aggiunge una linea per la ricerca di punti con modalità EXT p PAR
      se non ancora inserita in lista altrimenti la rimuove dalla lista
      pt1 e pt2 sono QgsPoint
      CRS é QgsCoordinateReferenceSystem opzionale
      """
      if snapType == QadSnapTypeEnum.EXT:
         arcs = self.__extArcs
      else:
         return

      _arc = QadArc(arc)
      _arc.transformFromCRSToCRS(CRS, self.getSnapPointCRS()) # trasformo l'arco in coord layer
      
      # verifico che non ci sia già
      exist = False
      i = 0
      for iArc in arcs:
         if _arc == iArc:
            # se esiste di già lo rimuovo
            del arcs[i] 
            return
         i = i + 1
         
      # se non esiste ancora lo aggiungo
      arcs.append(_arc)
      

   #============================================================================
   # getPolarCoord
   #============================================================================
   def getPolarCoord(self, point, polarAng):
      result = []

      angle = qad_utils.getAngleBy2Pts(self.__startPoint, point)
      value = math.modf(angle / polarAng) # ritorna una lista -> (<parte decimale> <parte intera>)
      if value[0] >= 0.5: # prendo intervallo successivo
         angle = (value[1] + 1) * polarAng
      else:
         angle = value[1] * polarAng

      dist = qad_utils.getDistance(self.__startPoint, point)
      pt2 = qad_utils.getPolarPointByPtAngle(self.__startPoint, angle, dist)

      polarPt = qad_utils.getPerpendicularPointOnInfinityLine(self.__startPoint, pt2, point)
      if qad_utils.getDistance(polarPt, point) <= self.__toleranceExtParlines:
         self.__appendUniquePoint(result, polarPt) # senza duplicazione

      return result
