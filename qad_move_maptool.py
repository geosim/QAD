# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando move
 
                              -------------------
        begin                : 2013-09-27
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
from qad_variables import *
from qad_getpoint import *


#===============================================================================
# Qad_move_maptool_ModeEnum class.
#===============================================================================
class Qad_move_maptool_ModeEnum():
   # noto niente si richiede il punto base
   NONE_KNOWN_ASK_FOR_BASE_PT = 1     
   # noto il punto base si richiede il secondo punto per lo spostamento
   BASE_PT_KNOWN_ASK_FOR_MOVE_PT = 2     

#===============================================================================
# Qad_move_maptool class
#===============================================================================
class Qad_move_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
                        
      self.basePt = None
      self.entitySet = QadEntitySet()
      self.__movedRubberBand = None   
      self.__movedRubberBandPolygon = None   

   def hidePointMapToolMarkers(self):
      QadGetPoint.hidePointMapToolMarkers(self)
      if self.__movedRubberBand is not None:
         self.__movedRubberBand.hide()
      if self.__movedRubberBandPolygon is not None:
         self.__movedRubberBandPolygon.hide()         

   def showPointMapToolMarkers(self):
      QadGetPoint.showPointMapToolMarkers(self)
      if self.__movedRubberBand is not None:
         self.__movedRubberBand.show()
      if self.__movedRubberBandPolygon is not None:
         self.__movedRubberBandPolygon.show()         
                             
   def clear(self):
      QadGetPoint.clear(self)
      if self.__movedRubberBand is not None:
         self.__movedRubberBand.hide()
         del self.__movedRubberBand
         self.__movedRubberBand = None
      if self.__movedRubberBandPolygon is not None:
         self.__movedRubberBandPolygon.hide()
         del self.__movedRubberBandPolygon
         self.__movedRubberBandPolygon = None
      self.mode = None    
   
   def addMovedGeometries(self, newPt):
      #qad_debug.breakPoint()      
      self.__movedRubberBand = QgsRubberBand(self.canvas, False)
      self.__movedRubberBandPolygon = QgsRubberBand(self.canvas, True)
      
      for layerEntitySet in self.entitySet.layerEntitySetList:
         layer = layerEntitySet.layer
         transformedBasePt = self.canvas.mapRenderer().mapToLayerCoordinates(layer, self.basePt)
         transformedNewPt = self.canvas.mapRenderer().mapToLayerCoordinates(layer, newPt)
         offSetX = transformedNewPt.x() - transformedBasePt.x()
         offSetY = transformedNewPt.y() - transformedBasePt.y()
         geoms = layerEntitySet.getGeometryCollection()
         if layer.geometryType() != QGis.Polygon:
            for geom in geoms:
               movedGeom = qad_utils.moveQgsGeometry(geom, offSetX, offSetY)
               self.__movedRubberBand.addGeometry(movedGeom, layer)
         else:
            for geom in geoms:
               movedGeom = qad_utils.moveQgsGeometry(geom, offSetX, offSetY)
               self.__movedRubberBandPolygon.addGeometry(movedGeom, layer)
            
      
   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
      
      if self.__movedRubberBand  is not None:
         self.__movedRubberBand.hide()
         del self.__movedRubberBand
         self.__movedRubberBand = None
      if self.__movedRubberBandPolygon  is not None:
         self.__movedRubberBandPolygon.hide()
         del self.__movedRubberBandPolygon
         self.__movedRubberBandPolygon = None
               
      # noto il punto base si richiede il secondo punto per l'angolo di rotazione
      if self.mode == Qad_move_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_MOVE_PT:
         self.addMovedGeometries(self.tmpPoint)                           
         
    
   def activate(self):
      QadGetPoint.activate(self)            
      if self.__movedRubberBand is not None:
         self.__movedRubberBand.show()
      if self.__movedRubberBandPolygon is not None:
         self.__movedRubberBandPolygon.show()

   def deactivate(self):
      QadGetPoint.deactivate(self)
      if self.__movedRubberBand is not None:
         self.__movedRubberBand.hide()
      if self.__movedRubberBandPolygon is not None:
         self.__movedRubberBandPolygon.hide()

   def setMode(self, mode):
      self.mode = mode
      # noto niente si richiede il punto base
      if self.mode == Qad_move_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_BASE_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il punto base si richiede il secondo punto per l'angolo di rotazione
      elif self.mode == Qad_move_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_MOVE_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.basePt)
