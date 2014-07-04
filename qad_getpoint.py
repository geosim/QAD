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
from qad_rubberband import createRubberBand


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
      
      self.__timer = QTimer()
      self.__stopTimer = True
      
      # setto la modalità di selezione
      self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)

      self.setDrawMode(drawMode)

      self.__QadSnapper = QadSnapper()
      self.__QadSnapper.setSnapPointCRS(self.canvas.mapRenderer().destinationCrs())
      self.__QadSnapper.setSnapLayers(self.canvas.layers())
      self.__QadSnapper.setProgressDistance(QadVariables.get(QadMsg.translate("Environment variables", "OSPROGRDISTANCE")))
      self.setSnapType(QadVariables.get(QadMsg.translate("Environment variables", "OSMODE")))
            
      self.setOrthoMode() # setto secondo le variabili d'ambiente
      self.setAutoSnap() # setto secondo le variabili d'ambiente
      
      # leggo la tolleranza in unità di mappa
      ToleranceInMapUnits = QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")) * self.canvas.mapRenderer().mapUnitsPerPixel()    
      self.__QadSnapper.setDistToExcludeNea(ToleranceInMapUnits)
      self.__QadSnapper.setToleranceExtParLines(ToleranceInMapUnits)

      self.__QadSnapPointsDisplayManager = QadSnapPointsDisplayManager(self.canvas)
      self.__QadSnapPointsDisplayManager.setIconSize(QadVariables.get(QadMsg.translate("Environment variables", "OSSIZE")))
      self.__QadSnapPointsDisplayManager.setColor(QColor(QadVariables.get(QadMsg.translate("Environment variables", "OSCOLOR"))))
      
      # output
      self.rightButton = False

      self.shiftKey = False
      self.tmpShiftKey = False

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
         self.__RubberBand = createRubberBand(self.canvas, QGis.Line)
         self.__RubberBand.setLineStyle(Qt.DotLine)
      elif self.__drawMode == QadGetPointDrawModeEnum.ELASTIC_RECTANGLE:
         self.__RubberBand = createRubberBand(self.canvas, QGis.Polygon)
         self.__RubberBand.setLineStyle(Qt.DotLine)
         

   def getDrawMode(self):
      return self.__drawMode


   def setSelectionMode(self, selectionMode):
      #qad_debug.breakPoint()
      self.__selectionMode = selectionMode
      # setto il tipo di cursore
      if selectionMode == QadGetPointSelectionModeEnum.POINT_SELECTION:
         self.setCursorType(QadCursorTypeEnum.CROSS) # una croce usata per selezionare un punto
      elif selectionMode == QadGetPointSelectionModeEnum.ENTITY_SELECTION:
         self.entity.clear() # entità selezionata 
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
      
      self.tmpShiftKey = False # tasto shift premuto durante il movimento del mouse      
      self.snapTypeOnSelection = None # snap attivo al momento del click

      self.shiftKey = False
      self.tmpShiftKey = False # tasto shift premuto durante il movimento del mouse      
       
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
   # tmpGeometries
   #============================================================================
   def clearTmpGeometries(self):
      #qad_debug.breakPoint()
      del self.tmpGeometries[:] # svuoto la lista
      self.__QadSnapper.clearTmpGeometries()

   def setTmpGeometry(self, geom, CRS = None):
      #qad_debug.breakPoint()      
      self.clearTmpGeometries()
      self.appendTmpGeometry(geom, CRS)
            
   def appendTmpGeometry(self, geom, CRS = None):
      if geom is None:
         return
      if CRS is not None and CRS != self.canvas.mapRenderer().destinationCrs():
         g = QgsGeometry(geom)
         coordTransform = QgsCoordinateTransform(CRS, self.canvas.mapRenderer().destinationCrs()) # trasformo la geometria
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
      if autoSnap is None:      
         self.__AutoSnap = QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAP"))
         self.__PolarAng = math.radians(QadVariables.get(QadMsg.translate("Environment variables", "POLARANG")))
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
      #qad_debug.breakPoint()
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

            
   #============================================================================
   # setStartPoint
   #============================================================================
   def setStartPoint(self, startPoint):
      #qad_debug.breakPoint()
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
         
         point = self.toMapCoordinates(self.canvas.mouseLastXY())
         # per un baco non ancora capito: se la linea ha solo 2 vertici e 
         # hanno la stessa x o y (linea orizzontale o verticale) 
         # la linea non viene disegnata perciò sposto un pochino la x o la y
         point = qad_utils.getAdjustedRubberBandVertex(startPoint, point)                                          
                
         self.__RubberBand.addPoint(point, True)
      elif self.getDrawMode() == QadGetPointDrawModeEnum.ELASTIC_RECTANGLE:
         # previsto uso del rettangolo elastico
         self.__RubberBand.reset(QGis.Polygon)
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
                                      self.layersToCheck, \
                                      self.checkPointLayer, \
                                      self.checkLineLayer, \
                                      self.checkPolygonLayer, \
                                      True, self.onlyEditableLayers)  
      else:
         result = qad_utils.getEntSel(event.pos(), self, \
                                      None, \
                                      self.__geometryTypesAccordingToSnapType[0], \
                                      self.__geometryTypesAccordingToSnapType[1], \
                                      self.__geometryTypesAccordingToSnapType[2], \
                                      True, \
                                      self.onlyEditableLayers)
      
      if result is not None:
         #qad_debug.breakPoint()
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
         #qad_debug.breakPoint()
         # se non è stata trovato alcun oggetto allora verifico se una geometria di tmpGeometries rientra nel pickbox
         tmpGeometry = qad_utils.getGeomInPickBox(event.pos(),
                                                  self, \
                                                  self.tmpGeometries, \
                                                  None, \
                                                  self.__geometryTypesAccordingToSnapType[0], \
                                                  self.__geometryTypesAccordingToSnapType[1], \
                                                  self.__geometryTypesAccordingToSnapType[2], \
                                                  True)
         if tmpGeometry is not None:
            # se è stata selezionata una geometria diversa da quella selezionata precedentemente
            if (self.__prevGeom is None) or not self.__prevGeom.equals(tmpGeometry):
               self.__prevGeom = QgsGeometry(tmpGeometry)
               runToggleReferenceLines = lambda: self.toggleReferenceLines(self.__prevGeom, point, self.canvas.mapRenderer().destinationCrs())
               self.__stopTimer = False
               self.__timer.singleShot(500, runToggleReferenceLines)
            #qad_debug.breakPoint()
            self.__QadSnapper.clearCacheSnapPoints() # pulisco la cache perchè tmpGeometry può essere variato
            oSnapPoints = self.__QadSnapper.getSnapPoint(tmpGeometry, point, \
                                                         self.canvas.mapRenderer().destinationCrs(), \
                                                         None, \
                                                         self.__PolarAng,
                                                         True)            
         else:         
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

      # tasto shift premuto durante il movimento del mouse      
      self.tmpShiftKey = True if event.modifiers() & Qt.ShiftModifier else False 
      
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
         # Se è stato premuto il tasto CTRL (o META)
         if ((event.modifiers() & Qt.ControlModifier) or (event.modifiers() & Qt.MetaModifier)):
            self.displayPopupMenu(event.pos())                  
         else:
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
      self.plugIn.QadCommands.continueCommandFromMapTool()     
      #self.plugIn.setStandardMapTool()

   def canvasReleaseEvent(self, event):
      # se l'obiettivo è selezionare un gruppo di entità attraverso un rettangolo
      #if self.getSelectionMode() == QadGetPointSelectionModeEnum.ENTITYSET_SELECTION and \
      #   self.getDrawMode() == QadGetPointDrawModeEnum.ELASTIC_RECTANGLE:                 
      # se l'obiettivo è selezionare un rettangolo
      if self.getDrawMode() == QadGetPointDrawModeEnum.ELASTIC_RECTANGLE:                 
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
               self.plugIn.QadCommands.continueCommandFromMapTool()
               #self.plugIn.setStandardMapTool()

   def __setPoint(self, event):
      # se non era mai stato mosso il mouse     
      if self.tmpPoint is None:        
         self.canvasMoveEvent(event)

      self.point = self.tmpPoint
      self.snapTypeOnSelection = self.getSnapType() # snap attivo al momento del click     
      self.entity.set(self.tmpEntity.layer, self.tmpEntity.featureId)
    
   def keyPressEvent(self, event):
      #qad_debug.breakPoint()
      self.plugIn.keyPressEvent(event)    
    
   def activate(self):
      #qad_debug.breakPoint()
      __QadSnapper = None
      __QadSnapPointsDisplayManager = None
      
      self.point = None
      self.tmpPoint = None

      self.entity = QadEntity() # entità selezionata dal click
      self.tmpEntity = QadEntity() # entità selezionata dal movimento del mouse
      
      self.snapTypeOnSelection = None # snap attivo al momento del click
      
      self.shiftKey = False
      self.tmpShiftKey = False # tasto shift premuto durante il movimento del mouse      
      
      self.rightButton = False
      self.canvas.setCursor(self.__cursor)
      self.showPointMapToolMarkers()

   def deactivate(self):
      try: # necessario perchè se si chiude QGIS parte questo evento nonostante non ci sia più l'oggetto maptool !
         #qad_debug.breakPoint()
         self.hidePointMapToolMarkers()
      except:
         pass

   def isTransient(self):
      return False

   def isEditTool(self):
      return True
      

   #============================================================================
   # dispalyPopupMenu
   #============================================================================
   def displayPopupMenu(self, pos):
      #qad_debug.breakPoint()
      popupMenu = QMenu(self.canvas)
      
      msg = QadMsg.translate("DSettings_Dialog", "Inizio / Fine")
      icon = QIcon(":/plugins/qad/icons/osnap_endLine.png")
      if icon is None:
         addEndLineSnapTypeAction = QAction(msg, popupMenu)
      else:
         addEndLineSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addEndLineSnapTypeAction, SIGNAL("triggered()"), self.addEndLineSnapTypeByPopupMenu)      
      popupMenu.addAction(addEndLineSnapTypeAction)
      
      msg = QadMsg.translate("DSettings_Dialog", "Inizio / Fine segmento")
      icon = QIcon(":/plugins/qad/icons/osnap_end.png")
      if icon is None:
         addEndSnapTypeAction = QAction(msg, popupMenu)
      else:
         addEndSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addEndSnapTypeAction, SIGNAL("triggered()"), self.addEndSnapTypeByPopupMenu)      
      popupMenu.addAction(addEndSnapTypeAction)
      
      msg = QadMsg.translate("DSettings_Dialog", "Punto medio")
      icon = QIcon(":/plugins/qad/icons/osnap_mid.png")
      if icon is None:
         addMidSnapTypeAction = QAction(msg, popupMenu)
      else:
         addMidSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addMidSnapTypeAction, SIGNAL("triggered()"), self.addMidSnapTypeByPopupMenu)      
      popupMenu.addAction(addMidSnapTypeAction)
      
      msg = QadMsg.translate("DSettings_Dialog", "Intersezione")
      icon = QIcon(":/plugins/qad/icons/osnap_int.png")
      if icon is None:
         addIntSnapTypeAction = QAction(msg, popupMenu)
      else:
         addIntSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addIntSnapTypeAction, SIGNAL("triggered()"), self.addIntSnapTypeByPopupMenu)      
      popupMenu.addAction(addIntSnapTypeAction)
      
      msg = QadMsg.translate("DSettings_Dialog", "Intersezione su estensione")
      icon = QIcon(":/plugins/qad/icons/osnap_extInt.png")
      if icon is None:
         addExtIntSnapTypeAction = QAction(msg, popupMenu)
      else:
         addExtIntSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addExtIntSnapTypeAction, SIGNAL("triggered()"), self.addExtIntSnapTypeByPopupMenu)      
      popupMenu.addAction(addExtIntSnapTypeAction)
      
      msg = QadMsg.translate("DSettings_Dialog", "Estensione")
      icon = QIcon(":/plugins/qad/icons/osnap_ext.png")
      if icon is None:
         addExtSnapTypeAction = QAction(msg, popupMenu)
      else:
         addExtSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addExtSnapTypeAction, SIGNAL("triggered()"), self.addExtSnapTypeByPopupMenu)      
      popupMenu.addAction(addExtSnapTypeAction)

      popupMenu.addSeparator()
     
      msg = QadMsg.translate("DSettings_Dialog", "Centro")
      icon = QIcon(":/plugins/qad/icons/osnap_cen.png")
      if icon is None:
         addCenSnapTypeAction = QAction(msg, popupMenu)
      else:
         addCenSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addCenSnapTypeAction, SIGNAL("triggered()"), self.addCenSnapTypeByPopupMenu)      
      popupMenu.addAction(addCenSnapTypeAction)
     
      msg = QadMsg.translate("DSettings_Dialog", "Quadrante")
      icon = QIcon(":/plugins/qad/icons/osnap_qua.png")
      if icon is None:
         addQuaSnapTypeAction = QAction(msg, popupMenu)
      else:
         addQuaSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addQuaSnapTypeAction, SIGNAL("triggered()"), self.addQuaSnapTypeByPopupMenu)      
      popupMenu.addAction(addQuaSnapTypeAction)
     
      msg = QadMsg.translate("DSettings_Dialog", "Tangente")
      icon = QIcon(":/plugins/qad/icons/osnap_tan.png")
      if icon is None:
         addTanSnapTypeAction = QAction(msg, popupMenu)
      else:
         addTanSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addTanSnapTypeAction, SIGNAL("triggered()"), self.addTanSnapTypeByPopupMenu)      
      popupMenu.addAction(addTanSnapTypeAction)

      popupMenu.addSeparator()

      msg = QadMsg.translate("DSettings_Dialog", "Perpendicolare")
      icon = QIcon(":/plugins/qad/icons/osnap_per.png")
      if icon is None:
         addPerSnapTypeAction = QAction(msg, popupMenu)
      else:
         addPerSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addPerSnapTypeAction, SIGNAL("triggered()"), self.addPerSnapTypeByPopupMenu)      
      popupMenu.addAction(addPerSnapTypeAction)     

      msg = QadMsg.translate("DSettings_Dialog", "Parallelo")
      icon = QIcon(":/plugins/qad/icons/osnap_par.png")
      if icon is None:
         addParSnapTypeAction = QAction(msg, popupMenu)
      else:
         addParSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addParSnapTypeAction, SIGNAL("triggered()"), self.addParSnapTypeByPopupMenu)      
      popupMenu.addAction(addParSnapTypeAction)     

      msg = QadMsg.translate("DSettings_Dialog", "Nodo")
      icon = QIcon(":/plugins/qad/icons/osnap_nod.png")
      if icon is None:
         addNodSnapTypeAction = QAction(msg, popupMenu)
      else:
         addNodSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addNodSnapTypeAction, SIGNAL("triggered()"), self.addNodSnapTypeByPopupMenu)      
      popupMenu.addAction(addNodSnapTypeAction)     

      msg = QadMsg.translate("DSettings_Dialog", "Vicino")
      icon = QIcon(":/plugins/qad/icons/osnap_nea.png")
      if icon is None:
         addNeaSnapTypeAction = QAction(msg, popupMenu)
      else:
         addNeaSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addNeaSnapTypeAction, SIGNAL("triggered()"), self.addNeaSnapTypeByPopupMenu)      
      popupMenu.addAction(addNeaSnapTypeAction)     

      msg = QadMsg.translate("DSettings_Dialog", "Progressivo")
      icon = QIcon(":/plugins/qad/icons/osnap_pr.png")
      if icon is None:
         addPrSnapTypeAction = QAction(msg, popupMenu)
      else:
         addPrSnapTypeAction = QAction(icon, msg, popupMenu)        
      QObject.connect(addPrSnapTypeAction, SIGNAL("triggered()"), self.addPrSnapTypeByPopupMenu)      
      popupMenu.addAction(addPrSnapTypeAction)     

      msg = QadMsg.translate("DSettings_Dialog", "Nessuno")
      icon = QIcon(":/plugins/qad/icons/osnap_disable.png")
      if icon is None:
         setSnapTypeToDisableAction = QAction(msg, popupMenu)
      else:
         setSnapTypeToDisableAction = QAction(icon, msg, popupMenu)        
      QObject.connect(setSnapTypeToDisableAction, SIGNAL("triggered()"), self.setSnapTypeToDisableByPopupMenu)      
      popupMenu.addAction(setSnapTypeToDisableAction)     

      popupMenu.addSeparator()

      msg = QadMsg.translate("DSettings_Dialog", "Impostazioni snap ad oggetto...")
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
