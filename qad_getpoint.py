# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool di richiesta di un punto
 
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
import math
import time # profiling


import qad_utils
from qad_snapper import *
from qad_snappointsdisplaymanager import *
from qad_entity import *
from qad_variables import *
from qad_rubberband import *
from qad_cacheareas import QadLayerCacheGeomsDict
from qad_msg import QadMsg


#===============================================================================
# QadGetPointSelectionModeEnum class.
#===============================================================================
class QadGetPointSelectionModeEnum():
   NONE                     = 0  # nessuna selezione (usato quando in un comando si chiede solo la scelta di opzioni)
   POINT_SELECTION          = 1  # selezione di un punto
   ENTITY_SELECTION         = 2  # selezione di una entità in modo statico (cerca l'entità solo con l'evento click)
   ENTITYSET_SELECTION      = 3  # selezione di un gruppo di entità  
   ENTITY_SELECTION_DYNAMIC = 4  # selezione di una entità in modo dinamico (cerca l'entità con l'evento click e 
                                 # con l'evento mouse move)


#===============================================================================
# QadGetPointDrawModeEnum class.
#===============================================================================
class QadGetPointDrawModeEnum():
   NONE              = 0     # nessuno
   ELASTIC_LINE      = 1     # linea elastica dal punto __startPoint
   ELASTIC_RECTANGLE = 2     # rettangolo elastico dal punto __startPoint   


from qad_dsettings_dlg import QadDSETTINGSDialog


#===============================================================================
# QadGetPoint get point class
#===============================================================================
class QadGetPoint(QgsMapTool):
    
   def __init__(self, plugIn, drawMode = QadGetPointDrawModeEnum.NONE):        
      QgsMapTool.__init__(self, plugIn.iface.mapCanvas())
      self.iface = plugIn.iface
      self.canvas = plugIn.iface.mapCanvas()
      self.plugIn = plugIn
      
      # cursore
      self.__csrRubberBand = None
      
      self.__QadSnapper = None
      self.__QadSnapPointsDisplayManager = None
      self.__oldSnapType = None
      self.__oldSnapProgrDist = None
      self.__geometryTypesAccordingToSnapType = (False, False, False)
      self.__startPoint = None
      self.tmpGeometries = [] # lista di geometria non ancora esistenti ma da contare per i punti di osnap (in map coordinates)
      # opzioni per limitare l'oggetto da selezionare
      self.onlyEditableLayers = False
      self.checkPointLayer = True
      self.checkLineLayer = True
      self.checkPolygonLayer = True
      self.layersToCheck = None
            
      self.__RubberBand = None
      self.__prevGeom = None
      
      self.__stopTimer = True

      # ottimizzazione per la ricerca degli oggetti
      # cache per selezione oggetti
      self.layerCacheGeomsDict = QadLayerCacheGeomsDict(self.canvas)
      self.lastLayerFound = None # layer ultimo oggetto trovato
      
      # setto la modalità di selezione
      self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)

      self.setDrawMode(drawMode)

      self.__QadSnapper = QadSnapper()
      self.__QadSnapper.setSnapMode(QadSnapModeEnum.ONE_RESULT) # Viene restituito solo il punto più vicino
      self.__QadSnapper.setSnapPointCRS(self.canvas.mapSettings().destinationCrs())
      self.__QadSnapper.setSnapLayers(qad_utils.getVisibleVectorLayers(self.canvas)) # Tutti i layer vettoriali visibili
      self.__QadSnapper.setProgressDistance(QadVariables.get(QadMsg.translate("Environment variables", "OSPROGRDISTANCE")))
      self.setSnapType(QadVariables.get(QadMsg.translate("Environment variables", "OSMODE")))
            
      self.setOrthoMode() # setto secondo le variabili d'ambiente
      self.setAutoSnap() # setto secondo le variabili d'ambiente
      
      # leggo la tolleranza in unità di mappa
      ToleranceInMapUnits = QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")) * self.canvas.mapSettings().mapUnitsPerPixel()    
      self.__QadSnapper.setDistToExcludeNea(ToleranceInMapUnits)
      self.__QadSnapper.setToleranceExtParLines(ToleranceInMapUnits)

      self.__QadSnapPointsDisplayManager = QadSnapPointsDisplayManager(self.canvas)
      self.__QadSnapPointsDisplayManager.setIconSize(QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAPSIZE")))
      self.__QadSnapPointsDisplayManager.setColor(QColor(QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAPCOLOR"))))
      
      # output
      self.rightButton = False
      # tasto shift
      self.shiftKey = False
      self.tmpShiftKey = False
      # tasto ctrl
      self.ctrlKey = False
      self.tmpCtrlKey = False

      self.point = None # punto selezionato dal click
      self.tmpPoint = None # punto selezionato dal movimento del mouse
      
      self.entity = QadEntity() # entità selezionata dal click
      self.tmpEntity = QadEntity() # entità selezionata dal movimento del mouse
      
      self.snapTypeOnSelection = None # snap attivo al momento del click
      
      # profiling
      self.tempo_tot = 0
      self.tempo1 = 0
      self.tempo2 = 0
      self.tempo3 = 0
      self.tempo4 = 0
      self.tempo5 = 0
      

   def __del__(self):
      self.removeItems()

 
   def removeItems(self):
      if self.__csrRubberBand is not None:
         self.__csrRubberBand.removeItems() # prima lo stacco dal canvas altrimenti non si rimuove perchè usato da canvas
         del self.__csrRubberBand
         self.__csrRubberBand = None
      
      if self.__RubberBand is not None:
         self.canvas.scene().removeItem(self.__RubberBand) # prima lo stacco dal canvas altrimenti non si rimuove perchè usato da canvas
         del self.__RubberBand
         self.__RubberBand = None

      if self.__QadSnapper is not None:
         del self.__QadSnapper
         self.__QadSnapper = None
      
      if self.__QadSnapPointsDisplayManager is not None:
         self.__QadSnapPointsDisplayManager.removeItems() # prima lo stacco dal canvas altrimenti non si rimuove perchè usato da canvas
         del self.__QadSnapPointsDisplayManager
         self.__QadSnapPointsDisplayManager = None
         
      if self.layerCacheGeomsDict is not None: # prima lo stacco dal canvas altrimenti non si rimuove perchè usato da canvas (eventi)
         del self.layerCacheGeomsDict
         
   
   def setDrawMode(self, drawMode):
      self.__drawMode = drawMode
      if self.__RubberBand is not None:
         self.__RubberBand.hide()
         self.canvas.scene().removeItem(self.__RubberBand) # prima lo stacco dal canvas altrimenti non si rimuove perchè usato da canvas
         del self.__RubberBand
         self.__RubberBand = None
         
      if self.__drawMode == QadGetPointDrawModeEnum.ELASTIC_LINE:
         self.refreshOrthoMode() # setto il default
         self.__RubberBand = createRubberBand(self.canvas, QGis.Line)
         self.__RubberBand.setLineStyle(Qt.DotLine)
      elif self.__drawMode == QadGetPointDrawModeEnum.ELASTIC_RECTANGLE:
         self.rectangleCrossingSelectionColor = getColorForCrossingSelectionArea()
         self.rectangleWindowSelectionColor = getColorForWindowSelectionArea()
            
         self.__RubberBand = createRubberBand(self.canvas, QGis.Polygon, False, None, self.rectangleCrossingSelectionColor)
         self.__RubberBand.setLineStyle(Qt.DotLine)
         

   def getDrawMode(self):
      return self.__drawMode


   def setSelectionMode(self, selectionMode):
      self.__selectionMode = selectionMode
      # setto il tipo di cursore
      if selectionMode == QadGetPointSelectionModeEnum.POINT_SELECTION:
         if QadVariables.get(QadMsg.translate("Environment variables", "APBOX")) == 0:
            self.setCursorType(QadCursorTypeEnum.CROSS) # una croce usata per selezionare un punto
         else:
            self.setCursorType(QadCursorTypeEnum.CROSS | QadCursorTypeEnum.APERTURE) # una croce + un quadratino usati per selezionare un punto
      elif selectionMode == QadGetPointSelectionModeEnum.ENTITY_SELECTION or \
           selectionMode == QadGetPointSelectionModeEnum.ENTITY_SELECTION_DYNAMIC:
         self.entity.clear() # entità selezionata 
         self.setCursorType(QadCursorTypeEnum.BOX) # un quadratino usato per selezionare entità
      elif selectionMode == QadGetPointSelectionModeEnum.ENTITYSET_SELECTION:
         if QadVariables.get(QadMsg.translate("Environment variables", "APBOX")) == 0:
            self.setCursorType(QadCursorTypeEnum.CROSS) # una croce usata per selezionare un punto
         else:
            self.setCursorType(QadCursorTypeEnum.CROSS | QadCursorTypeEnum.APERTURE) # una croce + un quadratino usati per selezionare un punto
      elif selectionMode == QadGetPointSelectionModeEnum.NONE:
         self.setCursorType(QadCursorTypeEnum.NONE) # nessun cursore


   def getSelectionMode(self):
      return self.__selectionMode


   def hidePointMapToolMarkers(self):
      if self.__QadSnapPointsDisplayManager is not None:
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
         self.canvas.scene().removeItem(self.__RubberBand) # prima lo stacco dal canvas altrimenti non si rimuove perchè usato da canvas
         del self.__RubberBand
         self.__RubberBand = None

      self.__QadSnapper.removeReferenceLines()
      self.__QadSnapper.setStartPoint(None)

      self.point = None # punto selezionato dal click
      self.tmpPoint = None # punto selezionato dal movimento del mouse
      
      self.entity.clear() # entità selezionata dal click
      self.tmpEntity.clear() # entità selezionata dal movimento del mouse
      
      self.snapTypeOnSelection = None # snap attivo al momento del click

      self.shiftKey = False
      self.tmpShiftKey = False # tasto shift premuto durante il movimento del mouse

      self.ctrlKey = False
      self.tmpCtrlKey = False # tasto ctrl premuto durante il movimento del mouse
       
      self.rightButton = False      
      # opzioni per limitare l'oggetto da selezionare
      self.onlyEditableLayers = False
      self.checkPointLayer = True # usato solo per ENTITY_SELECTION
      self.checkLineLayer = True # usato solo per ENTITY_SELECTION
      self.checkPolygonLayer = True # usato solo per ENTITY_SELECTION
      self.layersToCheck = None
      
      self.__oldSnapType = None
      self.__oldSnapProgrDist = None
      self.__startPoint = None
      self.clearTmpGeometries()


   #============================================================================
   # cache
   #============================================================================
   def updateLayerCacheOnMapCanvasExtent(self):
      if self.layerCacheGeomsDict is None:
         return
      # se l'obiettivo é selezionare un'entità in modo dinamico
      if self.getSelectionMode() == QadGetPointSelectionModeEnum.ENTITY_SELECTION_DYNAMIC:
         self.layerCacheGeomsDict.refreshOnMapCanvasExtent(self.layersToCheck, \
                                                           self.checkPointLayer, \
                                                           self.checkLineLayer, \
                                                           self.checkPolygonLayer, \
                                                           self.onlyEditableLayers)
      # se l'obiettivo é selezionare un punto
      elif self.getSelectionMode() == QadGetPointSelectionModeEnum.POINT_SELECTION:
         self.layerCacheGeomsDict.refreshOnMapCanvasExtent(None, \
                                                           self.__geometryTypesAccordingToSnapType[0], \
                                                           self.__geometryTypesAccordingToSnapType[1], \
                                                           self.__geometryTypesAccordingToSnapType[2], \
                                                           False)


   #============================================================================
   # tmpGeometries
   #============================================================================
   def clearTmpGeometries(self):
      del self.tmpGeometries[:] # svuoto la lista
      self.__QadSnapper.clearTmpGeometries()

   def setTmpGeometry(self, geom, CRS = None):
      self.clearTmpGeometries()
      self.appendTmpGeometry(geom, CRS)
            
   def appendTmpGeometry(self, geom, CRS = None):
      if geom is None:
         return
      if CRS is not None and CRS != self.canvas.mapSettings().destinationCrs():
         g = QgsGeometry(geom)
         coordTransform = QgsCoordinateTransform(CRS, self.canvas.mapSettings().destinationCrs()) # trasformo la geometria
         g.transform(coordTransform)
         self.tmpGeometries.append(g)
      else:
         self.tmpGeometries.append(geom)

      self.__QadSnapper.appendTmpGeometry(geom)
      

   def setTmpGeometries(self, geoms, CRS = None):      
      self.clearTmpGeometries()
      for g in geoms:
         self.appendTmpGeometry(g, CRS)
      

   #============================================================================
   # SnapType
   #============================================================================
   def setSnapType(self, snapType = None):
      if snapType is None:      
         self.__QadSnapper.setSnapType(QadVariables.get(QadMsg.translate("Environment variables", "OSMODE")))
      else:
         self.__QadSnapper.setSnapType(snapType)
         
      self.__geometryTypesAccordingToSnapType = self.__QadSnapper.getGeometryTypesAccordingToSnapType()
      self.updateLayerCacheOnMapCanvasExtent()
      

   def getSnapType(self):
      return self.__QadSnapper.getSnapType()

   def forceSnapTypeOnce(self, snapType = None, snapParams = None):
      self.__oldSnapType = self.__QadSnapper.getSnapType()
      self.__oldSnapProgrDist = self.__QadSnapper.getProgressDistance()
      
      # se si vuole impostare lo snap perpendicolare e
      # non é stato impostato un punto di partenza
      if snapType == QadSnapTypeEnum.PER and self.__startPoint is None:
         # imposto lo snap perpendicolare differito
         self.setSnapType(QadSnapTypeEnum.PER_DEF)
         return
      # se si vuole impostare lo snap tangente e
      # non é stato impostato un punto di partenza
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
      self.__oldSnapType = None
      self.__oldSnapProgrDist = None
      self.__QadSnapper.setProgressDistance(QadVariables.get(QadMsg.translate("Environment variables", "OSPROGRDISTANCE")))
      self.setSnapType(QadVariables.get(QadMsg.translate("Environment variables", "OSMODE")))


   #============================================================================
   # OrthoMode
   #============================================================================
   def setOrthoMode(self, orthoMode = None):
      if orthoMode is None:      
         self.__OrthoMode = QadVariables.get(QadMsg.translate("Environment variables", "ORTHOMODE"))
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
      # setta le variabili:
      # self.__AutoSnap, self.__PolarAng, self.__PolarMode, self.__PolarAngOffset, self.__snapMarkerSizeInMapUnits
      # self.__QadSnapper viene svuotato dai punti polari se "Object Snap Tracking off"
      
      if autoSnap is None:
         self.__AutoSnap = QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAP"))
      else:
         self.__AutoSnap = autoSnap
         
      if (self.__AutoSnap & QadAUTOSNAPEnum.POLAR_TRACKING) == False: # puntamento polare non attivato
         self.__PolarAng = None
         self.__PolarMode = None
         self.__PolarAngOffset = None
      else:
         self.__PolarAng = math.radians(QadVariables.get(QadMsg.translate("Environment variables", "POLARANG")))
         self.__PolarMode = QadVariables.get(QadMsg.translate("Environment variables", "POLARMODE"))
         self.__PolarAngOffset = 0
         
      if (self.__AutoSnap & QadAUTOSNAPEnum.OBJ_SNAP_TRACKING) == False: # Object Snap Tracking off
         if self.__QadSnapper is not None:
            self.__QadSnapper.removeOSnapPointsForPolar()

      # calcolo la dimensione dei simboli di snap in map unit
      self.__snapMarkerSizeInMapUnits = QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAPSIZE")) * \
                                        self.canvas.mapSettings().mapUnitsPerPixel()


   def refreshAutoSnap(self):
      self.setAutoSnap()


   #============================================================================
   # AutoSnap
   #============================================================================
   def setPolarAngOffset(self, polarAngOffset):
      self.__PolarAngOffset = polarAngOffset
      
      
   def getRealPolarAng(self):
      # ritorna l'angolo polare che veramente deve essere usato tenendo conto delle variabili di sistema
      if (self.__PolarMode & QadPOLARMODEnum.POLAR_TRACKING): # usa POLARANG
         return self.__PolarAng
      else:
         return math.pi / 2 # 90 gradi (ortogonale)
      
   def getRealPolarAngOffset(self):
      # ritorna l'angolo polare di offset che veramente deve essere usato tenendo conto delle variabili di sistema
      if (self.__PolarMode & QadPOLARMODEnum.MEASURE_RELATIVE_ANGLE): # (relativo al coeff angolare dell'ultimo segmento)
         return self.__PolarAngOffset 
      else:
         return 0 # 0 gradi (assoluto)
      

   #============================================================================
   # CursorType
   #============================================================================
   def setCursorType(self, cursorType):
      if self.__csrRubberBand is not None:
         self.__csrRubberBand.removeItems() # prima lo stacco dal canvas altrimenti non si rimuove perchè usato da canvas
         del self.__csrRubberBand
      self.__csrRubberBand = QadCursorRubberBand(self.canvas, cursorType)
      
      if cursorType == QadCursorTypeEnum.NONE:
         self.__cursor = QCursor(Qt.ArrowCursor)
      else:
         self.__cursor = QCursor(Qt.BlankCursor)
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

            # se l'obiettivo é selezionare un gruppo di selezione
            if self.getSelectionMode() == QadGetPointSelectionModeEnum.ENTITYSET_SELECTION:
               if point.x() > p1.x(): # se il punto è a destra di p1 (punto iniziale)
                  self.__RubberBand.setFillColor(self.rectangleWindowSelectionColor)
               else:
                  self.__RubberBand.setFillColor(self.rectangleCrossingSelectionColor)
            
            adjustedPoint = qad_utils.getAdjustedRubberBandVertex(p1, point)                     
            self.__RubberBand.movePoint(numberOfVertices - 3, QgsPoint(p1.x(), adjustedPoint.y()))
            self.__RubberBand.movePoint(numberOfVertices - 2, adjustedPoint)
            self.__RubberBand.movePoint(numberOfVertices - 1, QgsPoint(adjustedPoint.x(), p1.y()))            

            
   #============================================================================
   # setStartPoint
   #============================================================================
   def getStartPoint(self):
      return None if self.__startPoint is None else QgsPoint(self.__startPoint) # alloca
   def setStartPoint(self, startPoint):
      self.__startPoint = startPoint
      self.__QadSnapper.setStartPoint(startPoint)
      
      if self.getDrawMode() == QadGetPointDrawModeEnum.ELASTIC_LINE:
         # previsto uso della linea elastica
         self.__RubberBand.reset(QGis.Line)
         #numberOfVertices = self.__RubberBand.numberOfVertices()
         #if numberOfVertices == 2:
         #   self.__RubberBand.removeLastPoint()
         #   self.__RubberBand.removeLastPoint()
         self.__RubberBand.addPoint(startPoint, False)
         
         point = self.toMapCoordinates(self.canvas.mouseLastXY()) # posizione
         # per un baco non ancora capito: se la linea ha solo 2 vertici e 
         # hanno la stessa x o y (linea orizzontale o verticale) 
         # la linea non viene disegnata perciò sposto un pochino la x o la y
         point = qad_utils.getAdjustedRubberBandVertex(startPoint, point)
                
         self.__RubberBand.addPoint(point, True)
      elif self.getDrawMode() == QadGetPointDrawModeEnum.ELASTIC_RECTANGLE:
         # previsto uso del rettangolo elastico
         point = self.toMapCoordinates(self.canvas.mouseLastXY())

         self.__RubberBand.reset(QGis.Polygon)
         self.__RubberBand.addPoint(startPoint, False)
         
         # per un baco non ancora capito: se la linea ha solo 2 vertici e 
         # hanno la stessa x o y (linea orizzontale o verticale) 
         # la linea non viene disegnata perciò sposto un pochino la x o la y
         point = qad_utils.getAdjustedRubberBandVertex(startPoint, point)
                
         self.__RubberBand.addPoint(QgsPoint(startPoint.x(), point.y()), False)
         self.__RubberBand.addPoint(point, False)
         self.__RubberBand.addPoint(QgsPoint(point.x(), startPoint.y()), True)
         
      self.__QadSnapPointsDisplayManager.setStartPoint(startPoint)


   #============================================================================
   # toggleReferenceLines
   #============================================================================
   def toggleReferenceLines(self, geom, crs, oSnapPointsForPolar = None, shiftKey = None):
      if self.__stopTimer == False and (geom is not None):
         if self.__QadSnapper is not None:
            if self.__AutoSnap & QadAUTOSNAPEnum.OBJ_SNAP_TRACKING: # se abilitato l'utilizzo del modo i punti di snap per l'uso polare
               if self.__PolarMode & QadPOLARMODEnum.SHIFT_TO_ACQUIRE: # acquisisce i punti di snap per l'uso polare solo se premuto shift
                  useOSnapPointsForPolar = True if shiftKey else False
               else: # acquisisce i punti di snap per l'uso polare automaticamente               
                  useOSnapPointsForPolar = True
            else: # se NON abilitato l'utilizzo del modo i punti di snap per l'uso polare
               useOSnapPointsForPolar = False
            
            # prendo la posizione attuale del mouse perchè per attivare o disattivare i punti di snap per l'uso polare
            # devo essere dentro il simbolo di snap invece questa funzione viene attivata non appena sono in prossimità della geometria
            # (vedi variabile di sistema APERTURE) e quindi quando il mouse può essere ancora lontano dal punto di snap
            point = self.toMapCoordinates(self.canvas.mouseLastXY())
            if useOSnapPointsForPolar:
               self.__QadSnapper.toggleReferenceLines(geom, point, crs, oSnapPointsForPolar, self.__snapMarkerSizeInMapUnits)
            else:
               self.__QadSnapper.toggleReferenceLines(geom, point, crs)
               
            self.__QadSnapper.toggleIntExtLine(geom, point, crs)
      

   #============================================================================
   # magneticCursor
   #============================================================================
   def magneticCursor(self, oSnapPoints):
      if len(oSnapPoints) > 0:               
         for item in oSnapPoints.items():
            for pt in item[1]:
               # il punto <point> deve essere dentro il punto di snap che ha dimensioni snapMarkerSizeInMapUnits
               if self.tmpPoint.x() >= pt.x() - self.__snapMarkerSizeInMapUnits and self.tmpPoint.x() <= pt.x() + self.__snapMarkerSizeInMapUnits and \
                  self.tmpPoint.y() >= pt.y() - self.__snapMarkerSizeInMapUnits and self.tmpPoint.y() <= pt.y() + self.__snapMarkerSizeInMapUnits:
                     self.tmpPoint.set(pt.x(), pt.y()) 
                     self.__csrRubberBand.moveEvent(self.tmpPoint)


   #============================================================================
   # canvasMoveEvent
   #============================================================================
   def canvasMoveEvent(self, event):
      self.tmpPoint = self.toMapCoordinates(event.pos())
      self.__csrRubberBand.moveEvent(self.tmpPoint)

      # tasto shift premuto durante il movimento del mouse
      self.tmpShiftKey = True if event.modifiers() & Qt.ShiftModifier else False
      # tasto ctrl premuto durante il movimento del mouse
      self.tmpCtrlKey = True if event.modifiers() & Qt.ControlModifier else False
      
      # se l'obiettivo é selezionare un punto
      if self.getSelectionMode() == QadGetPointSelectionModeEnum.POINT_SELECTION:
         return self.canvasMoveEventOnPointSel(event)
      elif self.getSelectionMode() == QadGetPointSelectionModeEnum.NONE:
         pass
      # se l'obiettivo é selezionare una o più entità
      else: 
         return self.canvasMoveEventOnEntitySel(event)


   #============================================================================
   # canvasMoveEventOnEntitySel
   #============================================================================
   def canvasMoveEventOnEntitySel(self, event):
      # start = time.time() # test
      self.tmpEntity.clear()

      # start1 = time.time() # test
      
      # se l'obiettivo é selezionare un'entità in modo dinamico
      if self.getSelectionMode() == QadGetPointSelectionModeEnum.ENTITY_SELECTION_DYNAMIC:
         result = qad_utils.getEntSel(event.pos(), self, \
                                      QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")), \
                                      self.layersToCheck, \
                                      self.checkPointLayer, \
                                      self.checkLineLayer, \
                                      self.checkPolygonLayer, \
                                      True, self.onlyEditableLayers, \
                                      self.lastLayerFound, self.layerCacheGeomsDict)
      else:
         result = None
         
      #self.tempo1 += ((time.time() - start1) * 1000) # test
              
      # se è stata trovata una geometria
      if result is not None:         
         feature = result[0]
         layer = result[1]
         self.lastLayerFound = layer
         self.tmpEntity.set(layer, feature.id())
                  
      if self.getDrawMode() != QadGetPointDrawModeEnum.NONE:
         # previsto uso della linea elastica o rettangolo elastico
         self.moveElastic(self.tmpPoint)

      # self.tempo_tot += ((time.time() - start) * 1000) # test


   #============================================================================
   # canvasMoveEventOnPointSel
   #============================================================================
   def canvasMoveEventOnPointSel(self, event):
      # start = time.time() # test     
      result = qad_utils.getEntSel(event.pos(), self, \
                                   QadVariables.get(QadMsg.translate("Environment variables", "APERTURE")), \
                                   None, \
                                   self.__geometryTypesAccordingToSnapType[0], \
                                   self.__geometryTypesAccordingToSnapType[1], \
                                   self.__geometryTypesAccordingToSnapType[2], \
                                   True, False, \
                                   self.lastLayerFound, self.layerCacheGeomsDict, True)
         
      #self.tempo1 += ((time.time() - start1) * 1000) # test

      # se è stata trovata una geometria
      if result is not None:
         feature = result[0]
         layer = result[1]
         self.lastLayerFound = layer
         geometry = feature.geometry()
         point = self.toLayerCoordinates(layer, event.pos())
         
         allSnapPoints = self.__QadSnapper.getSnapPoint(geometry, point, \
                                                        layer.crs(), \
                                                        None, \
                                                        self.getRealPolarAng(), \
                                                        self.getRealPolarAngOffset())
         # Cerco solo il punto più vicino
         oSnapPoints = self.__QadSnapper.getNearestPoints(self.tmpPoint, allSnapPoints)

         if self.__AutoSnap & QadAUTOSNAPEnum.MAGNET: # Turns on the AutoSnap magnet
            self.magneticCursor(oSnapPoints)
         
         # se é stata selezionata una geometria diversa da quella selezionata precedentemente
         if (self.__prevGeom is None) or not self.__prevGeom.equals(geometry):
            self.__prevGeom = QgsGeometry(geometry)
            runToggleReferenceLines = lambda: self.toggleReferenceLines(self.__prevGeom, layer.crs(), allSnapPoints, self.tmpShiftKey)
            self.__stopTimer = False
            QTimer.singleShot(500, runToggleReferenceLines)
      # se NON è stata trovata una geometria
      else:        
         # start1 = time.time() # test
         
         # se non é stata trovato alcun oggetto allora verifico se una geometria di tmpGeometries rientra nella casella aperture
         boxSize = QadVariables.get(QadMsg.translate("Environment variables", "APERTURE")) # leggo la dimensione del quadrato (in pixel)
         tmpGeometry = qad_utils.getGeomInBox(event.pos(),
                                              self, \
                                              self.tmpGeometries, \
                                              boxSize, \
                                              None, \
                                              self.__geometryTypesAccordingToSnapType[0], \
                                              self.__geometryTypesAccordingToSnapType[1], \
                                              self.__geometryTypesAccordingToSnapType[2], \
                                              True)
         
         #self.tempo2 += ((time.time() - start1) * 1000) # test
         
         if tmpGeometry is not None:
            self.__QadSnapper.clearCacheSnapPoints() # pulisco la cache perché tmpGeometry può essere variato
            allSnapPoints = self.__QadSnapper.getSnapPoint(tmpGeometry, self.tmpPoint, \
                                                         self.canvas.mapSettings().destinationCrs(), \
                                                         None, \
                                                         self.getRealPolarAng(), \
                                                         self.getRealPolarAngOffset(), \
                                                         True)            
            # Cerco solo il punto più vicino
            oSnapPoints = self.__QadSnapper.getNearestPoints(self.tmpPoint, allSnapPoints)

            if self.__AutoSnap & QadAUTOSNAPEnum.MAGNET: # Turns on the AutoSnap magnet
               self.magneticCursor(oSnapPoints)

            # se é stata selezionata una geometria diversa da quella selezionata precedentemente
            if (self.__prevGeom is None) or not self.__prevGeom.equals(tmpGeometry):
               self.__prevGeom = QgsGeometry(tmpGeometry)
               runToggleReferenceLines = lambda: self.toggleReferenceLines(self.__prevGeom, \
                                                                           self.canvas.mapSettings().destinationCrs(), \
                                                                           allSnapPoints, self.tmpShiftKey)
               self.__stopTimer = False
               QTimer.singleShot(500, runToggleReferenceLines)
         else:
            allSnapPoints = self.__QadSnapper.getSnapPoint(None, self.tmpPoint, \
                                                           self.canvas.mapSettings().destinationCrs(), \
                                                           None, \
                                                           self.getRealPolarAng(), \
                                                           self.getRealPolarAngOffset())
            # Cerco solo il punto più vicino
            oSnapPoints = self.__QadSnapper.getNearestPoints(self.tmpPoint, allSnapPoints)

            if self.__AutoSnap & QadAUTOSNAPEnum.MAGNET: # Turns on the AutoSnap magnet
               self.magneticCursor(oSnapPoints)

            self.__prevGeom = None
            self.__stopTimer = True

      oSnapPoint = None

      # visualizzo il punto di snap
      self.__QadSnapPointsDisplayManager.show(oSnapPoints, \
                                              self.__QadSnapper.getExtLines(), \
                                              self.__QadSnapper.getExtArcs(), \
                                              self.__QadSnapper.getParLines(), \
                                              self.__QadSnapper.getIntExtLine(), \
                                              self.__QadSnapper.getIntExtArc(), \
                                              self.__QadSnapper.getOSnapPointsForPolar(), \
                                              self.__QadSnapper.getOSnapLinesForPolar())
      
      self.point = None
      self.tmpPoint = None
      # memorizzo il punto di snap in point (prendo il primo valido)
      for item in oSnapPoints.items():
         points = item[1]
         if points is not None:
            self.tmpPoint = points[0]
            oSnapPoint = points[0]
            break
      
      if self.tmpPoint is None:
         self.tmpPoint = self.toMapCoordinates(event.pos())

      if oSnapPoint is None: # se non c'è un punto di osnap
         if self.__startPoint is not None: # se c'é un punto di partenza
            if self.tmpShiftKey == False: # se non è premuto shift
               if self.__OrthoMode == 1: # orto attivato
                  self.tmpPoint = self.getOrthoCoord(self.tmpPoint)
            else: # se non è premuto shift devo fare il toggle di ortho
               if self.__OrthoMode == 0: # se orto disattivato lo attivo temporaneamente
                  self.tmpPoint = self.getOrthoCoord(self.tmpPoint)
                  
      if self.getDrawMode() != QadGetPointDrawModeEnum.NONE:
         # previsto uso della linea elastica o rettangolo elastico
         self.moveElastic(self.tmpPoint)

      # self.tempo_tot += ((time.time() - start) * 1000) # test


   def canvasPressEvent(self, event):
      # volevo mettere questo evento nel canvasReleaseEvent
      # ma il tasto destro non genera quel tipo di evento
      if event.button() == Qt.RightButton:
         # Se é stato premuto il tasto CTRL (o META)
         if ((event.modifiers() & Qt.ControlModifier) or (event.modifiers() & Qt.MetaModifier)):
            self.displayPopupMenu(event.pos())
         else:
            # self.clear() da rivedere
            self.rightButton = True
      elif event.button() == Qt.LeftButton:
         if self.getSelectionMode() == QadGetPointSelectionModeEnum.ENTITY_SELECTION_DYNAMIC or \
            self.getSelectionMode() == QadGetPointSelectionModeEnum.ENTITY_SELECTION:
            self.tmpPoint = self.toMapCoordinates(event.pos())
            result = qad_utils.getEntSel(event.pos(), self, \
                                         QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")), \
                                         self.layersToCheck, \
                                         self.checkPointLayer, \
                                         self.checkLineLayer, \
                                         self.checkPolygonLayer, \
                                         True, self.onlyEditableLayers, \
                                         self.lastLayerFound) # non uso self.layerCacheGeomsDict perchè se ho gli snap disattivati self.layerCacheGeomsDict è vuota
            if result is not None:
               feature = result[0]
               layer = result[1]
               self.tmpEntity.set(layer, feature.id())
         
         self.__QadSnapper.removeReferenceLines()
         self.__QadSnapPointsDisplayManager.hide()
   
         self.__setPoint(event)
            
         self.rightButton = False
              
         if self.__oldSnapType is not None:
            self.setSnapType(self.__oldSnapType) # riporto il valore precedente
            self.__QadSnapper.setProgressDistance(self.__oldSnapProgrDist)
            
      # tasto shift premuto durante il click del mouse
      self.shiftKey = True if event.modifiers() & Qt.ShiftModifier else False

      # tasto ctrl premuto durante il click del mouse
      self.ctrlKey = True if event.modifiers() & Qt.ControlModifier else False

      self.plugIn.QadCommands.continueCommandFromMapTool()
      #self.plugIn.setStandardMapTool()

   def canvasReleaseEvent(self, event):
      # se l'obiettivo é selezionare un rettangolo
      if self.getDrawMode() == QadGetPointDrawModeEnum.ELASTIC_RECTANGLE:                 
         if event.button() == Qt.LeftButton:
            p1 = self.__RubberBand.getPoint(0, 0)
            # se il mouse é in una posizione diversa dal punto iniziale del rettangolo
            if p1 != self.toMapCoordinates(event.pos()):
               self.__QadSnapper.removeReferenceLines()
               self.__QadSnapPointsDisplayManager.hide()
          
               self.__setPoint(event)
                   
               self.rightButton = False
                     
               if self.__oldSnapType is not None:
                  self.setSnapType(self.__oldSnapType) # riporto il valore precedente
                  self.__QadSnapper.setProgressDistance(self.__oldSnapProgrDist)
                   
               # tasto shift premuto durante il click del mouse
               self.shiftKey = True if event.modifiers() & Qt.ShiftModifier else False
         
               # tasto ctrl premuto durante il click del mouse
               self.ctrlKey = True if event.modifiers() & Qt.ControlModifier else False
               
               self.plugIn.QadCommands.continueCommandFromMapTool()
               #self.plugIn.setStandardMapTool()

   def __setPoint(self, event):
      # se non era mai stato mosso il mouse     
      if self.tmpPoint is None:        
         self.canvasMoveEvent(event)

      self.point = self.tmpPoint
      self.plugIn.setLastPoint(self.point)
      self.snapTypeOnSelection = self.getSnapType() # snap attivo al momento del click     
      self.entity.set(self.tmpEntity.layer, self.tmpEntity.featureId)
    
   def keyPressEvent(self, event):
      self.plugIn.keyPressEvent(event)
    
   def activate(self):
      self.canvas.setToolTip("")

      if self.__csrRubberBand is not None:
         # posizione corrente del mouse
         self.__csrRubberBand.moveEvent(self.toMapCoordinates(self.canvas.mouseLastXY()))
         self.__csrRubberBand.show()
            
      self.point = None
      self.tmpPoint = None

      self.entity = QadEntity() # entità selezionata dal click
      self.tmpEntity = QadEntity() # entità selezionata dal movimento del mouse
      
      self.snapTypeOnSelection = None # snap attivo al momento del click
      
      self.shiftKey = False
      self.tmpShiftKey = False # tasto shift premuto durante il movimento del mouse      

      self.ctrlKey = False
      self.tmpCtrlKey = False # tasto ctrl premuto durante il movimento del mouse      

      self.rightButton = False
      self.canvas.setCursor(self.__cursor)
      self.showPointMapToolMarkers()

   def deactivate(self):
      try: # necessario perché se si chiude QGIS parte questo evento nonostante non ci sia più l'oggetto maptool !
         if self.__csrRubberBand is not None:
            self.__csrRubberBand.hide()
         self.hidePointMapToolMarkers()
      except:
         pass

   def isTransient(self):
      return False

   def isEditTool(self):
      # benchè questo tool faccia editing ritorno False perchè ogni volta che seleziono una feature
      # con la funzione QgsVectorLayer::select(QgsFeatureId featureId)
      # parte in sequenza la chiamata a isEditTool del tool corrente che se ritorna true viene disattivato
      # e poi riattivato QadMapTool che riprende il comando interrotto creando casino
      #return True 2016
      return False
      

   #============================================================================
   # dispalyPopupMenu
   #============================================================================
   def displayPopupMenu(self, pos):
      popupMenu = QMenu(self.canvas)
      
      msg = QadMsg.translate("DSettings_Dialog", "Start / End")
      icon = QIcon(":/plugins/qad/icons/osnap_endLine.png")
      if icon is None:
         addEndLineSnapTypeAction = QAction(msg, popupMenu)
      else:
         addEndLineSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addEndLineSnapTypeAction, SIGNAL("triggered()"), self.addEndLineSnapTypeByPopupMenu)      
      popupMenu.addAction(addEndLineSnapTypeAction)
      
      msg = QadMsg.translate("DSettings_Dialog", "Segment Start / End")
      icon = QIcon(":/plugins/qad/icons/osnap_end.png")
      if icon is None:
         addEndSnapTypeAction = QAction(msg, popupMenu)
      else:
         addEndSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addEndSnapTypeAction, SIGNAL("triggered()"), self.addEndSnapTypeByPopupMenu)      
      popupMenu.addAction(addEndSnapTypeAction)
      
      msg = QadMsg.translate("DSettings_Dialog", "Middle point")
      icon = QIcon(":/plugins/qad/icons/osnap_mid.png")
      if icon is None:
         addMidSnapTypeAction = QAction(msg, popupMenu)
      else:
         addMidSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addMidSnapTypeAction, SIGNAL("triggered()"), self.addMidSnapTypeByPopupMenu)      
      popupMenu.addAction(addMidSnapTypeAction)
      
      msg = QadMsg.translate("DSettings_Dialog", "Intersection")
      icon = QIcon(":/plugins/qad/icons/osnap_int.png")
      if icon is None:
         addIntSnapTypeAction = QAction(msg, popupMenu)
      else:
         addIntSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addIntSnapTypeAction, SIGNAL("triggered()"), self.addIntSnapTypeByPopupMenu)      
      popupMenu.addAction(addIntSnapTypeAction)
      
      msg = QadMsg.translate("DSettings_Dialog", "Intersection on extension")
      icon = QIcon(":/plugins/qad/icons/osnap_extInt.png")
      if icon is None:
         addExtIntSnapTypeAction = QAction(msg, popupMenu)
      else:
         addExtIntSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addExtIntSnapTypeAction, SIGNAL("triggered()"), self.addExtIntSnapTypeByPopupMenu)      
      popupMenu.addAction(addExtIntSnapTypeAction)
      
      msg = QadMsg.translate("DSettings_Dialog", "Extend")
      icon = QIcon(":/plugins/qad/icons/osnap_ext.png")
      if icon is None:
         addExtSnapTypeAction = QAction(msg, popupMenu)
      else:
         addExtSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addExtSnapTypeAction, SIGNAL("triggered()"), self.addExtSnapTypeByPopupMenu)      
      popupMenu.addAction(addExtSnapTypeAction)

      popupMenu.addSeparator()
     
      msg = QadMsg.translate("DSettings_Dialog", "Center")
      icon = QIcon(":/plugins/qad/icons/osnap_cen.png")
      if icon is None:
         addCenSnapTypeAction = QAction(msg, popupMenu)
      else:
         addCenSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addCenSnapTypeAction, SIGNAL("triggered()"), self.addCenSnapTypeByPopupMenu)      
      popupMenu.addAction(addCenSnapTypeAction)
     
      msg = QadMsg.translate("DSettings_Dialog", "Quadrant")
      icon = QIcon(":/plugins/qad/icons/osnap_qua.png")
      if icon is None:
         addQuaSnapTypeAction = QAction(msg, popupMenu)
      else:
         addQuaSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addQuaSnapTypeAction, SIGNAL("triggered()"), self.addQuaSnapTypeByPopupMenu)      
      popupMenu.addAction(addQuaSnapTypeAction)
     
      msg = QadMsg.translate("DSettings_Dialog", "Tangent")
      icon = QIcon(":/plugins/qad/icons/osnap_tan.png")
      if icon is None:
         addTanSnapTypeAction = QAction(msg, popupMenu)
      else:
         addTanSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addTanSnapTypeAction, SIGNAL("triggered()"), self.addTanSnapTypeByPopupMenu)      
      popupMenu.addAction(addTanSnapTypeAction)

      popupMenu.addSeparator()

      msg = QadMsg.translate("DSettings_Dialog", "Perpendicular")
      icon = QIcon(":/plugins/qad/icons/osnap_per.png")
      if icon is None:
         addPerSnapTypeAction = QAction(msg, popupMenu)
      else:
         addPerSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addPerSnapTypeAction, SIGNAL("triggered()"), self.addPerSnapTypeByPopupMenu)      
      popupMenu.addAction(addPerSnapTypeAction)     

      msg = QadMsg.translate("DSettings_Dialog", "Parallel")
      icon = QIcon(":/plugins/qad/icons/osnap_par.png")
      if icon is None:
         addParSnapTypeAction = QAction(msg, popupMenu)
      else:
         addParSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addParSnapTypeAction, SIGNAL("triggered()"), self.addParSnapTypeByPopupMenu)      
      popupMenu.addAction(addParSnapTypeAction)     

      msg = QadMsg.translate("DSettings_Dialog", "Node")
      icon = QIcon(":/plugins/qad/icons/osnap_nod.png")
      if icon is None:
         addNodSnapTypeAction = QAction(msg, popupMenu)
      else:
         addNodSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addNodSnapTypeAction, SIGNAL("triggered()"), self.addNodSnapTypeByPopupMenu)      
      popupMenu.addAction(addNodSnapTypeAction)     

      msg = QadMsg.translate("DSettings_Dialog", "Near")
      icon = QIcon(":/plugins/qad/icons/osnap_nea.png")
      if icon is None:
         addNeaSnapTypeAction = QAction(msg, popupMenu)
      else:
         addNeaSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addNeaSnapTypeAction, SIGNAL("triggered()"), self.addNeaSnapTypeByPopupMenu)      
      popupMenu.addAction(addNeaSnapTypeAction)     

      msg = QadMsg.translate("DSettings_Dialog", "Progressive")
      icon = QIcon(":/plugins/qad/icons/osnap_pr.png")
      if icon is None:
         addPrSnapTypeAction = QAction(msg, popupMenu)
      else:
         addPrSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addPrSnapTypeAction, SIGNAL("triggered()"), self.addPrSnapTypeByPopupMenu)      
      popupMenu.addAction(addPrSnapTypeAction)     

      msg = QadMsg.translate("DSettings_Dialog", "None")
      icon = QIcon(":/plugins/qad/icons/osnap_disable.png")
      if icon is None:
         setSnapTypeToDisableAction = QAction(msg, popupMenu)
      else:
         setSnapTypeToDisableAction = QAction(icon, msg, popupMenu)        
      QObject.connect(setSnapTypeToDisableAction, SIGNAL("triggered()"), self.setSnapTypeToDisableByPopupMenu)      
      popupMenu.addAction(setSnapTypeToDisableAction)     

      popupMenu.addSeparator()

      msg = QadMsg.translate("DSettings_Dialog", "Object snap settings...")
      icon = QIcon(":/plugins/qad/icons/dsettings.png")
      if icon is None:
         DSettingsAction = QAction(msg, popupMenu)
      else:
         DSettingsAction = QAction(icon, msg, popupMenu)        
      QObject.connect(DSettingsAction, SIGNAL("triggered()"), self.showDSettingsByPopUpMenu)      
      popupMenu.addAction(DSettingsAction)     
            
      popupMenu.popup(self.canvas.mapToGlobal(pos))
         

   #============================================================================
   # addSnapTypeByPopupMenu
   #============================================================================
   def addSnapTypeByPopupMenu(self, _snapType):
      value = QadVariables.get(QadMsg.translate("Environment variables", "OSMODE"))
      if value & QadSnapTypeEnum.DISABLE:
         value =  value - QadSnapTypeEnum.DISABLE      
      QadVariables.set(QadMsg.translate("Environment variables", "OSMODE"), value | _snapType)
      QadVariables.save()      
      self.refreshSnapType()
         
   def addEndLineSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.END_PLINE)
   def addEndSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.END)
   def addMidSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.MID)
   def addIntSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.INT)      
   def addExtIntSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.EXT_INT)
   def addExtSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.EXT)   
   def addCenSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.CEN)      
   def addQuaSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.QUA)
   def addTanSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.TAN)
   def addPerSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.PER)
   def addParSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.PAR)
   def addNodSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.NOD)
   def addNeaSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.NEA)
   def addPrSnapTypeByPopupMenu(self):
      self.addSnapTypeByPopupMenu(QadSnapTypeEnum.PR)

   def setSnapTypeToDisableByPopupMenu(self):
      value = QadVariables.get(QadMsg.translate("Environment variables", "OSMODE"))
      QadVariables.set(QadMsg.translate("Environment variables", "OSMODE"), value | QadSnapTypeEnum.DISABLE)
      QadVariables.save()      
      self.refreshSnapType()

   def showDSettingsByPopUpMenu(self):
      d = QadDSETTINGSDialog(self.plugIn)
      d.exec_()
      self.refreshSnapType()
      self.refreshAutoSnap()
      self.setPolarAngOffset(self.plugIn.lastSegmentAng)


   def mapToLayerCoordinates(self, layer, point_geom):
      # transform point o geometry coordinates from output CRS to layer's CRS 
      if self.canvas is None:
         return None
      if type(point_geom) == QgsPoint:
         return self.canvas.mapSettings().mapToLayerCoordinates(layer, point_geom)
      elif type(point_geom) == QgsGeometry:
         # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
         coordTransform = QgsCoordinateTransform(self.canvas.mapSettings().destinationCrs(), layer.crs())
         g = QgsGeometry(point_geom)
         g.transform(coordTransform)
         return g
      else:
         return None

   def layerToMapCoordinates(self, layer, point_geom):
      # transform point o geometry coordinates from layer's CRS to output CRS 
      if self.canvas is None:
         return None
      if type(point_geom) == QgsPoint:
         return self.canvas.mapSettings().layerToMapCoordinates(layer, point_geom)
      elif type(point_geom) == QgsGeometry:
         # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
         coordTransform = QgsCoordinateTransform(layer.crs(), self.canvas.mapSettings().destinationCrs())
         g = QgsGeometry(point_geom)
         g.transform(coordTransform)
         return g
      else:
         return None





#    #============================================================================
#    # canvasMoveEvent
#    #============================================================================
#    def canvasMoveEvent(self, event):
#       # se l'obiettivo é selezionare un punto
#       if self.getSelectionMode() == QadGetPointSelectionModeEnum.POINT_SELECTION:
#          return self.canvasMoveEventOnPointSel(event)
#       
#       # start = time.time() # test
#       
#       self.tmpPoint = self.toMapCoordinates(event.pos())
#       self.tmpEntity.clear()
#       
#       self.__csrRubberBand.moveEvent(self.tmpPoint)
# 
#       # tasto shift premuto durante il movimento del mouse
#       self.tmpShiftKey = True if event.modifiers() & Qt.ShiftModifier else False
# 
#       # tasto ctrl premuto durante il movimento del mouse
#       self.tmpCtrlKey = True if event.modifiers() & Qt.ControlModifier else False
# 
#       # start1 = time.time() # test
#       
#       # se l'obiettivo é selezionare un'entità in modo dinamico
#       if self.getSelectionMode() == QadGetPointSelectionModeEnum.ENTITY_SELECTION_DYNAMIC:
#          result = qad_utils.getEntSel(event.pos(), self, \
#                                       QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")), \
#                                       self.layersToCheck, \
#                                       self.checkPointLayer, \
#                                       self.checkLineLayer, \
#                                       self.checkPolygonLayer, \
#                                       True, self.onlyEditableLayers, \
#                                       self.lastLayerFound, self.layerCacheGeomsDict)
#       # se l'obiettivo é selezionare un punto
#       elif self.getSelectionMode() == QadGetPointSelectionModeEnum.POINT_SELECTION:
#          result = qad_utils.getEntSel(event.pos(), self, \
#                                       QadVariables.get(QadMsg.translate("Environment variables", "APERTURE")), \
#                                       None, \
#                                       self.__geometryTypesAccordingToSnapType[0], \
#                                       self.__geometryTypesAccordingToSnapType[1], \
#                                       self.__geometryTypesAccordingToSnapType[2], \
#                                       True, False, \
#                                       self.lastLayerFound, self.layerCacheGeomsDict)
#       else:
#          result = None
#          
#       #self.tempo1 += ((time.time() - start1) * 1000) # test
#               
#       # se è stata trovata una geometria
#       if result is not None:         
#          feature = result[0]
#          layer = result[1]
#          self.lastLayerFound = layer
#          self.tmpEntity.set(layer, feature.id())
#          geometry = feature.geometry()
#          point = self.toLayerCoordinates(layer, event.pos())
#          
#          allSnapPoints = self.__QadSnapper.getSnapPoint(geometry, point, \
#                                                         layer.crs(), \
#                                                         None, \
#                                                         self.getRealPolarAng(), \
#                                                         self.getRealPolarAngOffset())
#          # Cerco solo il punto più vicino
#          oSnapPoints = self.__QadSnapper.getNearestPoints(self.tmpPoint, allSnapPoints)
# 
#          # se l'obiettivo é selezionare un punto
#          if self.getSelectionMode() == QadGetPointSelectionModeEnum.POINT_SELECTION:
#             if self.__AutoSnap & QadAUTOSNAPEnum.MAGNET: # Turns on the AutoSnap magnet
#                self.magneticCursor(oSnapPoints)
#             
#             # se é stata selezionata una geometria diversa da quella selezionata precedentemente
#             if (self.__prevGeom is None) or not self.__prevGeom.equals(geometry):
#                self.__prevGeom = QgsGeometry(geometry)
#                runToggleReferenceLines = lambda: self.toggleReferenceLines(self.__prevGeom, layer.crs(), allSnapPoints, self.tmpShiftKey)
#                self.__stopTimer = False
#                QTimer.singleShot(500, runToggleReferenceLines)
#       # se NON è stata trovata una geometria
#       # se l'obiettivo é selezionare un punto
#       elif self.getSelectionMode() == QadGetPointSelectionModeEnum.POINT_SELECTION:
#          
#          # start1 = time.time() # test
#          
#          # se non é stata trovato alcun oggetto allora verifico se una geometria di tmpGeometries rientra nella casella aperture
#          boxSize = QadVariables.get(QadMsg.translate("Environment variables", "APERTURE")) # leggo la dimensione del quadrato (in pixel)
#          tmpGeometry = qad_utils.getGeomInBox(event.pos(),
#                                               self, \
#                                               self.tmpGeometries, \
#                                               boxSize, \
#                                               None, \
#                                               self.__geometryTypesAccordingToSnapType[0], \
#                                               self.__geometryTypesAccordingToSnapType[1], \
#                                               self.__geometryTypesAccordingToSnapType[2], \
#                                               True)
#          
#          #self.tempo2 += ((time.time() - start1) * 1000) # test
#          
#          if tmpGeometry is not None:
#             self.__QadSnapper.clearCacheSnapPoints() # pulisco la cache perché tmpGeometry può essere variato
#             allSnapPoints = self.__QadSnapper.getSnapPoint(tmpGeometry, self.tmpPoint, \
#                                                          self.canvas.mapSettings().destinationCrs(), \
#                                                          None, \
#                                                          self.getRealPolarAng(), \
#                                                          self.getRealPolarAngOffset(), \
#                                                          True)            
#             # Cerco solo il punto più vicino
#             oSnapPoints = self.__QadSnapper.getNearestPoints(self.tmpPoint, allSnapPoints)
# 
#             if self.__AutoSnap & QadAUTOSNAPEnum.MAGNET: # Turns on the AutoSnap magnet
#                self.magneticCursor(oSnapPoints)
# 
#             # se é stata selezionata una geometria diversa da quella selezionata precedentemente
#             if (self.__prevGeom is None) or not self.__prevGeom.equals(tmpGeometry):
#                self.__prevGeom = QgsGeometry(tmpGeometry)
#                runToggleReferenceLines = lambda: self.toggleReferenceLines(self.__prevGeom, \
#                                                                            self.canvas.mapSettings().destinationCrs(), \
#                                                                            allSnapPoints, self.tmpShiftKey)
#                self.__stopTimer = False
#                QTimer.singleShot(500, runToggleReferenceLines)
#          else:
#             allSnapPoints = self.__QadSnapper.getSnapPoint(None, self.tmpPoint, \
#                                                            self.canvas.mapSettings().destinationCrs(), \
#                                                            None, \
#                                                            self.getRealPolarAng(), \
#                                                            self.getRealPolarAngOffset())
#             # Cerco solo il punto più vicino
#             oSnapPoints = self.__QadSnapper.getNearestPoints(self.tmpPoint, allSnapPoints)
# 
#             if self.__AutoSnap & QadAUTOSNAPEnum.MAGNET: # Turns on the AutoSnap magnet
#                self.magneticCursor(oSnapPoints)
# 
#             self.__prevGeom = None
#             self.__stopTimer = True
# 
#       oSnapPoint = None
# 
#       # se l'obiettivo é selezionare un punto
#       if self.getSelectionMode() == QadGetPointSelectionModeEnum.POINT_SELECTION:
#          # visualizzo il punto di snap
#          self.__QadSnapPointsDisplayManager.show(oSnapPoints, \
#                                                  self.__QadSnapper.getExtLines(), \
#                                                  self.__QadSnapper.getExtArcs(), \
#                                                  self.__QadSnapper.getParLines(), \
#                                                  self.__QadSnapper.getIntExtLine(), \
#                                                  self.__QadSnapper.getIntExtArc(), \
#                                                  self.__QadSnapper.getOSnapPointsForPolar(), \
#                                                  self.__QadSnapper.getOSnapLinesForPolar())
#          
#          self.point = None
#          self.tmpPoint = None
#          # memorizzo il punto di snap in point (prendo il primo valido)
#          for item in oSnapPoints.items():
#             points = item[1]
#             if points is not None:
#                self.tmpPoint = points[0]
#                oSnapPoint = points[0]
#                break
#          
#          if self.tmpPoint is None:
#             self.tmpPoint = self.toMapCoordinates(event.pos())
# 
#       # se l'obiettivo é selezionare un punto
#       if self.getSelectionMode() == QadGetPointSelectionModeEnum.POINT_SELECTION:
#          if oSnapPoint is None: # se non c'è un punto di osnap
#             if self.__startPoint is not None: # se c'é un punto di partenza
#                if self.tmpShiftKey == False: # se non è premuto shift
#                   if self.__OrthoMode == 1: # orto attivato
#                      self.tmpPoint = self.getOrthoCoord(self.tmpPoint)
#                else: # se non è premuto shift devo fare il toggle di ortho
#                   if self.__OrthoMode == 0: # se orto disattivato lo attivo temporaneamente
#                      self.tmpPoint = self.getOrthoCoord(self.tmpPoint)
#                   
#       if self.getDrawMode() != QadGetPointDrawModeEnum.NONE:
#          # previsto uso della linea elastica o rettangolo elastico
#          self.moveElastic(self.tmpPoint)
# 
#       # self.tempo_tot += ((time.time() - start) * 1000) # test
