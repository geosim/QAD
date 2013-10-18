# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool di richiesta di un punto
 
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


import qad_debug
import qad_utils
from qad_snapper import *
from qad_snappointsdisplaymanager import *
from qad_entity import *
from qad_variables import *


#===============================================================================
# QadGetPointSelectionModeEnum class.
#===============================================================================
class QadGetPointSelectionModeEnum():
   POINT_SELECTION     = 0     # selezione di un punto
   ENTITY_SELECTION    = 1     # selezione di una entità
   ENTITYSET_SELECTION = 2     # selezione di un gruppo di entità   


#===============================================================================
# QadGetPointDrawModeEnum class.
#===============================================================================
class QadGetPointDrawModeEnum():
   NONE              = 0     # nessuno
   ELASTIC_LINE      = 1     # linea elastica dal punto __startPoint
   ELASTIC_RECTANGLE = 2     # rettangolo elastico dal punto __startPoint   


#===============================================================================
# QadCursorTypeEnum class.
#===============================================================================
class QadCursorTypeEnum():
   BOX   = 0     # un quadratino usato per selezionare entità
   CROSS = 1     # una croce usata per selezionare un punto


#===============================================================================
# QadGetPoint get point class
#===============================================================================
class QadGetPoint(QgsMapTool):
    
   def __init__(self, plugIn, drawMode = QadGetPointDrawModeEnum.NONE):        
      QgsMapTool.__init__(self, plugIn.iface.mapCanvas())
      self.iface = plugIn.iface
      self.canvas = plugIn.iface.mapCanvas()
      self.plugIn = plugIn
      self.__QadSnapper = None
      self.__QadSnapPointsDisplayManager = None
      self.__oldSnapType = None
      self.__oldSnapProgrDist = None
      self.__geometryTypesAccordingToSnapType = (False, False, False)
      self.__startPoint = None
      self.shiftKey = False
      self.rightButton = False
      self.onlyEditableLayers = False
            
      self.__RubberBand = None
      self.__prevGeom = None
      
      self.__timer = QTimer()
      self.__stopTimer = True
      
      # setto la modalità di selezione
      self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)

      self.setDrawMode(drawMode)

      self.__QadSnapper = QadSnapper()
      self.__QadSnapper.setSnapPointCRS(self.canvas.mapRenderer().destinationCrs())
      self.__QadSnapper.setSnapLayers(self.canvas.layers())
      self.__QadSnapper.setProgressDistance(QadVariables.get("OSPROGRDISTANCE"))
      self.setSnapType(QadVariables.get("OSMODE"))
            
      self.setOrthoMode() # setto secondo le variabili d'ambiente
      self.setAutoSnap() # setto secondo le variabili d'ambiente
      
      # leggo la tolleranza in unità di mappa
      ToleranceInMapUnits = QadVariables.get("PICKBOX") * self.canvas.mapRenderer().mapUnitsPerPixel()    
      self.__QadSnapper.setDistToExcludeNea(ToleranceInMapUnits)
      self.__QadSnapper.setToleranceExtParLines(ToleranceInMapUnits)

      self.__QadSnapPointsDisplayManager = QadSnapPointsDisplayManager(self.canvas)
      self.__QadSnapPointsDisplayManager.setIconSize(QadVariables.get("OSSIZE"))
      self.__QadSnapPointsDisplayManager.setColor(QColor(QadVariables.get("OSCOLOR")))
      
      # output
      self.point = None # punto selezionato dal click
      self.tmpPoint = None # punto selezionato dal movimento del mouse
      
      self.entity = QadEntity() # entità selezionata dal click
      self.tmpEntity = QadEntity() # entità selezionata dal movimento del mouse
      
      self.snapTypeOnSelection = None # snap attivo al momento del click

   def setDrawMode(self, drawMode):
      self.__drawMode = drawMode
      #qad_debug.breakPoint()
      if self.__RubberBand is not None:
         self.__RubberBand.hide()
         del self.__RubberBand
         self.__RubberBand = None
         
      if self.__drawMode == QadGetPointDrawModeEnum.ELASTIC_LINE:
         self.refreshOrthoMode() # setto il default
         self.__RubberBand = QgsRubberBand(self.canvas, False)
      elif self.__drawMode == QadGetPointDrawModeEnum.ELASTIC_RECTANGLE:
         self.__RubberBand = QgsRubberBand(self.canvas, True)

   def getDrawMode(self):
      return self.__drawMode


   def setSelectionMode(self, selectionMode):
      #qad_debug.breakPoint()
      self.__selectionMode = selectionMode
      # setto il tipo di cursore
      if selectionMode == QadGetPointSelectionModeEnum.POINT_SELECTION:
         self.setCursorType(QadCursorTypeEnum.CROSS) # una croce usata per selezionare un punto
      elif selectionMode == QadGetPointSelectionModeEnum.ENTITY_SELECTION:
         self.setCursorType(QadCursorTypeEnum.BOX) # un quadratino usato per selezionare entità
      elif selectionMode == QadGetPointSelectionModeEnum.ENTITYSET_SELECTION:
         self.setCursorType(QadCursorTypeEnum.BOX) # un quadratino usato per selezionare un guppo di entità   

   def getSelectionMode(self):
      return self.__selectionMode


   def hidePointMapToolMarkers(self):
      self.__QadSnapPointsDisplayManager.hide()
      if self.__RubberBand is not None:
         self.__RubberBand.hide()

   def showPointMapToolMarkers(self):
      if self.__RubberBand is not None:
         self.__RubberBand.show()

   def getPointMapToolMarkersCount(self):
      if self.__RubberBand is None:
         return 0
      else:
         return self.__RubberBand.numberOfVertices()
                             
   def clear(self):
      self.hidePointMapToolMarkers()
      if self.__RubberBand is not None:
         del self.__RubberBand
         self.__RubberBand = None

      self.__QadSnapper.removeReferenceLines()

      self.point = None # punto selezionato dal click
      self.tmpPoint = None # punto selezionato dal movimento del mouse
      
      self.entity.clear() # entità selezionata dal click
      self.tmpEntity.clear() # entità selezionata dal movimento del mouse
      
      self.snapTypeOnSelection = None # snap attivo al momento del click

      self.shiftKey = False      
      self.rightButton = False
      self.onlyEditableLayers = False

      self.__oldSnapType = None
      self.__oldSnapProgrDist = None
      self.__startPoint = None


   #============================================================================
   # SnapType
   #============================================================================
   def setSnapType(self, snapType = None):
      if snapType is None:      
         self.__QadSnapper.setSnapType(QadVariables.get("OSMODE"))
      else:
         self.__QadSnapper.setSnapType(snapType)
         
      self.__geometryTypesAccordingToSnapType = self.__QadSnapper.getGeometryTypesAccordingToSnapType()

   def getSnapType(self):
      return self.__QadSnapper.getSnapType()

   def forceSnapTypeOnce(self, snapType = None, snapParams = None):
      self.__oldSnapType = self.__QadSnapper.getSnapType()
      self.__oldSnapProgrDist = self.__QadSnapper.getProgressDistance()
      
      #qad_debug.breakPoint()
      # se si vuole impostare lo snap perpendicolare e
      # non è stato impostato un punto di partenza
      if snapType == QadSnapTypeEnum.PER and self.__startPoint is None:
         # imposto lo snap perpendicolare differito
         self.setSnapType(QadSnapTypeEnum.PER_DEF)
         return
      # se si vuole impostare lo snap tangente e
      # non è stato impostato un punto di partenza
      if snapType == QadSnapTypeEnum.TAN and self.__startPoint is None:
         # imposto lo snap tangente differito
         self.setSnapType(QadSnapTypeEnum.TAN_DEF)
         return

      if snapParams is not None:
         for param in snapParams:
            if param[0] == QadSnapTypeEnum.PR:
               # se si vuole impostare una distanza lo snap progressivo
               self.__QadSnapper.setProgressDistance(param[1])
            
      self.setSnapType(snapType)

   def refreshSnapType(self):
      self.setSnapType()


   #============================================================================
   # OrthoMode
   #============================================================================
   def setOrthoMode(self, orthoMode = None):
      if orthoMode is None:      
         self.__OrthoMode = QadVariables.get("ORTHOMODE")
      else:
         self.__OrthoMode = orthoMode

   def getOrthoCoord(self, point):
      if math.fabs(point.x() - self.__startPoint.x()) < \
         math.fabs(point.y() - self.__startPoint.y()):
         return QgsPoint(self.__startPoint.x(), point.y())
      else:
         return QgsPoint(point.x(), self.__startPoint.y())

   def refreshOrthoMode(self):
      self.setOrthoMode()


   #============================================================================
   # AutoSnap
   #============================================================================
   def setAutoSnap(self, autoSnap = None):
      if autoSnap is None:      
         self.__AutoSnap = QadVariables.get("AUTOSNAP")
         self.__PolarAng = math.radians(QadVariables.get("POLARANG"))
      else:
         self.__AutoSnap = autoSnap
         
      if (self.__AutoSnap & 8) == False: # puntamento polare non attivato
         self.__PolarAng = None

   def refreshAutoSnap(self):
      self.setAutoSnap()


   #============================================================================
   # CursorType
   #============================================================================
   def setCursorType(self, cursorType = None):
      if cursorType == QadCursorTypeEnum.BOX:
         # un quadratino usato per selezionare entità
         self.__cursor = qad_utils.getEntSelCursor()
      elif cursorType == QadCursorTypeEnum.CROSS:
         # una croce usata per selezionare un punto
         self.__cursor = qad_utils.getGetPointCursor()
      else:
         return
      
      self.__cursorType = cursorType
      
   def getCursorType(self):
      return self.__cursorType

    
   #============================================================================
   # Elastic
   #============================================================================
   def moveElastic(self, point):
      numberOfVertices = self.__RubberBand.numberOfVertices()
      if numberOfVertices > 0:         
         if numberOfVertices == 2:
            # per un baco non ancora capito: se la linea ha solo 2 vertici e 
            # hanno la stessa x o y (linea orizzontale o verticale) 
            # la linea non viene disegnata perciò sposto un pochino la x o la y         
            adjustedPoint = qad_utils.getAdjustedRubberBandVertex(self.__RubberBand.getPoint(0, 0), point)                     
            self.__RubberBand.movePoint(numberOfVertices - 1, adjustedPoint)
         else:
            p1 = self.__RubberBand.getPoint(0, 0)
            adjustedPoint = qad_utils.getAdjustedRubberBandVertex(p1, point)                     
            self.__RubberBand.movePoint(numberOfVertices - 3, QgsPoint(p1.x(), adjustedPoint.y()))
            self.__RubberBand.movePoint(numberOfVertices - 2, adjustedPoint)
            self.__RubberBand.movePoint(numberOfVertices - 1, QgsPoint(adjustedPoint.x(), p1.y()))            

            
   def setStartPoint(self, startPoint):
      self.__startPoint = startPoint
      self.__QadSnapper.setStartPoint(startPoint)
      
      if self.getDrawMode() == QadGetPointDrawModeEnum.ELASTIC_LINE:
         # previsto uso della linea elastica
         self.__RubberBand.reset(False)
         #numberOfVertices = self.__RubberBand.numberOfVertices()
         #if numberOfVertices == 2:
         #   self.__RubberBand.removeLastPoint()
         #   self.__RubberBand.removeLastPoint()
         self.__RubberBand.addPoint(startPoint, False)
         
         point = self.toMapCoordinates(self.canvas.mouseLastXY())
         # per un baco non ancora capito: se la linea ha solo 2 vertici e 
         # hanno la stessa x o y (linea orizzontale o verticale) 
         # la linea non viene disegnata perciò sposto un pochino la x o la y
         point = qad_utils.getAdjustedRubberBandVertex(startPoint, point)                                          
                
         self.__RubberBand.addPoint(point, True)
      elif self.getDrawMode() == QadGetPointDrawModeEnum.ELASTIC_RECTANGLE:
         # previsto uso del rettangolo elastico
         self.__RubberBand.reset(True)
         self.__RubberBand.addPoint(startPoint, False)
         
         point = self.toMapCoordinates(self.canvas.mouseLastXY())
         # per un baco non ancora capito: se la linea ha solo 2 vertici e 
         # hanno la stessa x o y (linea orizzontale o verticale) 
         # la linea non viene disegnata perciò sposto un pochino la x o la y
         point = qad_utils.getAdjustedRubberBandVertex(startPoint, point)                                          
                
         self.__RubberBand.addPoint(QgsPoint(startPoint.x(), point.y()), False)
         self.__RubberBand.addPoint(point, False)
         self.__RubberBand.addPoint(QgsPoint(point.x(), startPoint.y()), True)
         
      self.__QadSnapPointsDisplayManager.setStartPoint(startPoint)

   def toggleReferenceLines(self, geom, point, crs):
      if self.__stopTimer == False and (geom is not None) and (point is not None):
         self.__QadSnapper.toggleReferenceLines(geom, point, crs)
         self.__QadSnapper.toggleIntExtLine(geom, point, crs)
      
   def canvasMoveEvent(self, event):
      # se l'obiettivo è selezionare un'entità
      #qad_debug.breakPoint()   
      if self.getSelectionMode() == QadGetPointSelectionModeEnum.ENTITY_SELECTION:
         result = qad_utils.getEntSel(event.pos(), self, \
                                      None, True, True, True, True, \
                                      self.onlyEditableLayers)  
      else:
         result = qad_utils.getEntSel(event.pos(), self, \
                                      None, \
                                      self.__geometryTypesAccordingToSnapType[0], \
                                      self.__geometryTypesAccordingToSnapType[1], \
                                      self.__geometryTypesAccordingToSnapType[2], \
                                      True, \
                                      self.onlyEditableLayers)

      if result is not None:
         feature = result[0]
         layer = result[1]
         entity = QadEntity()     
         entity.set(layer, feature.id())
         geometry = feature.geometry()    
         point = self.toLayerCoordinates(layer, event.pos())

         # se è stata selezionata una geometria diversa da quella selezionata precedentemente
         if (self.__prevGeom is None) or not self.__prevGeom.equals(geometry):
            #qad_debug.breakPoint()
            self.__prevGeom = QgsGeometry(geometry)
            runToggleReferenceLines = lambda: self.toggleReferenceLines(self.__prevGeom, point, layer.crs())
            self.__stopTimer = False
            self.__timer.singleShot(500, runToggleReferenceLines)
         
         oSnapPoints = self.__QadSnapper.getSnapPoint(geometry, point, \
                                                      layer.crs(), \
                                                      None, \
                                                      self.__PolarAng)

         self.tmpEntity.set(layer, feature.id())                                  
      else:
         point = self.toMapCoordinates(event.pos())
         
         oSnapPoints = self.__QadSnapper.getSnapPoint(None, point, \
                                                      self.canvas.mapRenderer().destinationCrs(), \
                                                      None, \
                                                      self.__PolarAng)
                                    
         self.__prevGeom = None
         self.__stopTimer = True
         self.tmpEntity.clear()         
                  
      # visualizzo il punto di snap
      self.__QadSnapPointsDisplayManager.show(oSnapPoints, \
                                              self.__QadSnapper.getExtLines(), \
                                              self.__QadSnapper.getExtArcs(), \
                                              self.__QadSnapper.getParLines(), \
                                              self.__QadSnapper.getIntExtLine(), \
                                              self.__QadSnapper.getIntExtArc())
      
      self.point = None
      self.tmpPoint = None
      oSnapPoint = None
      # memorizzo il punto di snap in point (prendo il primo valido)
      for item in oSnapPoints.items():
         points = item[1]
         if points is not None:
            self.tmpPoint = points[0]
            oSnapPoint = points[0]
            break
      
      if self.tmpPoint is None:
         self.tmpPoint = self.toMapCoordinates(event.pos())
      
      if self.__RubberBand is not None:
         if oSnapPoint is None:
            if self.__startPoint is not None: # c'è un punto di partenza
               if self.__OrthoMode == 1: # orto attivato
                  self.tmpPoint = self.getOrthoCoord(self.tmpPoint)
            
         if self.getDrawMode() != QadGetPointDrawModeEnum.NONE:
            # previsto uso della linea elastica o rettangolo elastico
            self.moveElastic(self.tmpPoint)

   def canvasPressEvent(self, event):

      # volevo mettere questo evento nel canvasReleaseEvent
      # ma il tasto destro non genera quel tipo di evento
      if event.button() == Qt.RightButton:
         # self.clear() da rivedere
         self.rightButton = True
      elif event.button() == Qt.LeftButton:
         self.__QadSnapper.removeReferenceLines()
         self.__QadSnapPointsDisplayManager.hide()
   
         self.__setPoint(event)
            
         self.rightButton = False
              
         if self.__oldSnapType is not None:
            self.setSnapType(self.__oldSnapType) # riporto il valore precedente
            self.__QadSnapper.setProgressDistance(self.__oldSnapProgrDist)            
            
      self.shiftKey = True if event.modifiers() & Qt.ShiftModifier else False
      self.plugIn.setStandardMapTool()

   def canvasReleaseEvent(self, event):
      # se l'obiettivo è selezionare un gruppo di entità attraverso un rettangolo
      if self.getSelectionMode() == QadGetPointSelectionModeEnum.ENTITYSET_SELECTION and \
         self.getDrawMode() == QadGetPointDrawModeEnum.ELASTIC_RECTANGLE:                 
         if event.button() == Qt.LeftButton:
            p1 = self.__RubberBand.getPoint(0, 0)
            # se il mouse è in una posizione diversa dal punto iniziale del rettangolo
            if p1 != self.toMapCoordinates(event.pos()):
               self.__QadSnapper.removeReferenceLines()
               self.__QadSnapPointsDisplayManager.hide()
          
               self.__setPoint(event)
                   
               self.rightButton = False
                     
               if self.__oldSnapType is not None:
                  self.setSnapType(self.__oldSnapType) # riporto il valore precedente
                  self.__QadSnapper.setProgressDistance(self.__oldSnapProgrDist)
                   
               self.shiftKey = True if event.modifiers() & Qt.ShiftModifier else False
               self.plugIn.setStandardMapTool()

   def __setPoint(self, event):
      # se non era mai stato mosso il mouse     
      if self.tmpPoint is None:        
         self.canvasMoveEvent(event)

      self.point = self.tmpPoint
      self.snapTypeOnSelection = self.getSnapType() # snap attivo al momento del click     
      self.entity.set(self.tmpEntity.layer, self.tmpEntity.featureId)
    
   def keyPressEvent(self, event):
      self.plugIn.keyPressEvent(event)
    
   def activate(self):
      __QadSnapper = None
      __QadSnapPointsDisplayManager = None
      
      self.point = None
      self.tmpPoint = None

      self.entity = QadEntity() # entità selezionata dal click
      self.tmpEntity = QadEntity() # entità selezionata dal movimento del mouse
      
      self.snapTypeOnSelection = None # snap attivo al momento del click
      
      self.shiftKey = False
      self.rightButton = False
      self.canvas.setCursor(self.__cursor)
      self.showPointMapToolMarkers()

   def deactivate(self):
      self.hidePointMapToolMarkers()

   def isTransient(self):
      return False

   def isEditTool(self):
      return True
      