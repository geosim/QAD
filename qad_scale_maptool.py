# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando scale
 
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
# Qad_scale_maptool_ModeEnum class.
#===============================================================================
class Qad_scale_maptool_ModeEnum():
   # noto niente si richiede il punto base
   NONE_KNOWN_ASK_FOR_BASE_PT = 1     
   # noto il punto base si richiede il secondo punto per la scala
   BASE_PT_KNOWN_ASK_FOR_SCALE_PT = 2     
   # si richiede il primo punto per la lunghezza di riferimento
   ASK_FOR_FIRST_PT_REFERENCE_LEN = 3     
   # noto il primo punto si richiede il secondo punto per la lunghezza di riferimento
   FIRST_PT_KNOWN_ASK_FOR_SECOND_PT_REFERENCE_LEN = 4     
   # noto il punto base si richiede il secondo punto per la nuova lunghezza
   BASE_PT_KNOWN_ASK_FOR_NEW_LEN_PT = 5
   # si richiede il primo punto per la nuova lunghezza
   ASK_FOR_FIRST_NEW_LEN_PT = 6
   # noto il primo punto si richiede il secondo punto per la nuova lunghezza
   FIRST_PT_KNOWN_ASK_FOR_SECOND_NEW_LEN_PT = 7     

#===============================================================================
# Qad_scale_maptool class
#===============================================================================
class Qad_scale_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
                        
      self.basePt = None
      self.Pt1ReferenceLen = None
      self.ReferenceLen = 0
      self.Pt1NewLen = None
      self.entitySet = QadEntitySet()
      self.__scaledRubberBand = None   
      self.__scaledRubberBandPolygon = None   

   def hidePointMapToolMarkers(self):
      QadGetPoint.hidePointMapToolMarkers(self)
      if self.__scaledRubberBand is not None:
         self.__scaledRubberBand.hide()
      if self.__scaledRubberBandPolygon is not None:
         self.__scaledRubberBandPolygon.hide()         

   def showPointMapToolMarkers(self):
      QadGetPoint.showPointMapToolMarkers(self)
      if self.__scaledRubberBand is not None:
         self.__scaledRubberBand.show()
      if self.__scaledRubberBandPolygon is not None:
         self.__scaledRubberBandPolygon.show()         
                             
   def clear(self):
      QadGetPoint.clear(self)
      if self.__scaledRubberBand is not None:
         self.__scaledRubberBand.hide()
         del self.__scaledRubberBand
         self.__scaledRubberBand = None
      if self.__scaledRubberBandPolygon is not None:
         self.__scaledRubberBandPolygon.hide()
         del self.__scaledRubberBandPolygon
         self.__scaledRubberBandPolygon = None
      self.mode = None    

   def addScaledGeometries(self, scale):
      #qad_debug.breakPoint()      
      self.__scaledRubberBand = QgsRubberBand(self.canvas, False)
      self.__scaledRubberBandPolygon = QgsRubberBand(self.canvas, True)
      
      if scale <= 0:
         return
      
      for layerEntitySet in self.entitySet.layerEntitySetList:
         layer = layerEntitySet.layer
         transformedBasePt = self.canvas.mapRenderer().mapToLayerCoordinates(layer, self.basePt)
         geoms = layerEntitySet.getGeometryCollection()
         if layer.geometryType() != QGis.Polygon:
            for geom in geoms:
               scaledGeom = qad_utils.scaleQgsGeometry(geom, transformedBasePt, scale)
               self.__scaledRubberBand.addGeometry(scaledGeom, layer)
         else:
            for geom in geoms:
               scaledGeom = qad_utils.scaleQgsGeometry(geom, transformedBasePt, scale)
               self.__scaledRubberBandPolygon.addGeometry(scaledGeom, layer)
            
      
   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
      
      if self.__scaledRubberBand  is not None:
         self.__scaledRubberBand.hide()
         del self.__scaledRubberBand
         self.__scaledRubberBand = None
      if self.__scaledRubberBandPolygon  is not None:
         self.__scaledRubberBandPolygon.hide()
         del self.__scaledRubberBandPolygon
         self.__scaledRubberBandPolygon = None
               
      # noto il punto base si richiede il secondo punto per la scala
      if self.mode == Qad_scale_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_SCALE_PT:
         scale = qad_utils.getDistance(self.basePt, self.tmpPoint)
         self.addScaledGeometries(scale)                           
      # noto il primo punto si richiede il secondo punto per la lunghezza di riferimento
      elif self.mode == Qad_scale_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_NEW_LEN_PT:
         #qad_debug.breakPoint()
         len = qad_utils.getDistance(self.basePt, self.tmpPoint)
         scale = len / self.ReferenceLen
         self.addScaledGeometries(scale)                           
      # noto il primo punto si richiede il secondo punto per la nuova lunghezza
      elif self.mode == Qad_scale_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_NEW_LEN_PT:
         len = qad_utils.getDistance(self.Pt1NewLen, self.tmpPoint)
         scale = len / self.ReferenceLen
         self.addScaledGeometries(scale)                           
         
    
   def activate(self):
      QadGetPoint.activate(self)            
      if self.__scaledRubberBand is not None:
         self.__scaledRubberBand.show()
      if self.__scaledRubberBandPolygon is not None:
         self.__scaledRubberBandPolygon.show()

   def deactivate(self):
      QadGetPoint.deactivate(self)
      if self.__scaledRubberBand is not None:
         self.__scaledRubberBand.hide()
      if self.__scaledRubberBandPolygon is not None:
         self.__scaledRubberBandPolygon.hide()

   def setMode(self, mode):
      self.mode = mode
      # noto niente si richiede il punto base
      if self.mode == Qad_scale_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_BASE_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il punto base si richiede il secondo punto per la scala
      elif self.mode == Qad_scale_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_SCALE_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.basePt)
      # si richiede il primo punto per la lunghezza di riferimento
      elif self.mode == Qad_scale_maptool_ModeEnum.ASK_FOR_FIRST_PT_REFERENCE_LEN:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il primo punto si richiede il secondo punto per la lunghezza di riferimento
      elif self.mode == Qad_scale_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT_REFERENCE_LEN:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.Pt1ReferenceLen)
      # noto il punto base si richiede il secondo punto per la nuova lunghezza
      elif self.mode == Qad_scale_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_NEW_LEN_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.basePt)
      # si richiede il primo punto per la nuova lunghezza
      elif self.mode == Qad_scale_maptool_ModeEnum.ASK_FOR_FIRST_NEW_LEN_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il primo punto si richiede il secondo punto per la nuova lunghezza
      elif self.mode == Qad_scale_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_NEW_LEN_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.Pt1NewLen)
