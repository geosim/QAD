# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando rotate
 
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
# Qad_rotate_maptool_ModeEnum class.
#===============================================================================
class Qad_rotate_maptool_ModeEnum():
   # noto niente si richiede il punto base
   NONE_KNOWN_ASK_FOR_BASE_PT = 1     
   # noto il punto base si richiede il secondo punto per l'angolo di rotazione
   BASE_PT_KNOWN_ASK_FOR_ROTATION_PT = 2     
   # si richiede il primo punto per l'angolo di riferimento
   ASK_FOR_FIRST_PT_REFERENCE_ANG = 3     
   # noto il primo punto si richiede il secondo punto per l'angolo di riferimento
   FIRST_PT_KNOWN_ASK_FOR_SECOND_PT_REFERENCE_ANG = 4     
   # noto il punto base si richiede il secondo punto per il nuovo angolo
   BASE_PT_KNOWN_ASK_FOR_NEW_ROTATION_PT = 5
   # si richiede il primo punto per il nuovo angolo
   ASK_FOR_FIRST_NEW_ROTATION_PT = 6
   # noto il primo punto si richiede il secondo punto per il nuovo angolo
   FIRST_PT_KNOWN_ASK_FOR_SECOND_NEW_ROTATION_PT = 7     

#===============================================================================
# Qad_rotate_maptool class
#===============================================================================
class Qad_rotate_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
                        
      self.basePt = None
      self.Pt1ReferenceAng = None
      self.ReferenceAng = 0
      self.Pt1NewAng = None
      self.entitySet = QadEntitySet()
      self.__rotatedRubberBand = None   
      self.__rotatedRubberBandPolygon = None   

   def hidePointMapToolMarkers(self):
      QadGetPoint.hidePointMapToolMarkers(self)
      if self.__rotatedRubberBand is not None:
         self.__rotatedRubberBand.hide()
      if self.__rotatedRubberBandPolygon is not None:
         self.__rotatedRubberBandPolygon.hide()         

   def showPointMapToolMarkers(self):
      QadGetPoint.showPointMapToolMarkers(self)
      if self.__rotatedRubberBand is not None:
         self.__rotatedRubberBand.show()
      if self.__rotatedRubberBandPolygon is not None:
         self.__rotatedRubberBandPolygon.show()         
                             
   def clear(self):
      QadGetPoint.clear(self)
      if self.__rotatedRubberBand is not None:
         self.__rotatedRubberBand.hide()
         del self.__rotatedRubberBand
         self.__rotatedRubberBand = None
      if self.__rotatedRubberBandPolygon is not None:
         self.__rotatedRubberBandPolygon.hide()
         del self.__rotatedRubberBandPolygon
         self.__rotatedRubberBandPolygon = None
      self.mode = None    
   
   def addRotatedGeometries(self, angle):
      #qad_debug.breakPoint()      
      self.__rotatedRubberBand = QgsRubberBand(self.canvas, False)
      self.__rotatedRubberBandPolygon = QgsRubberBand(self.canvas, True)
      
      for layerEntitySet in self.entitySet.layerEntitySetList:
         layer = layerEntitySet.layer
         transformedBasePt = self.canvas.mapRenderer().mapToLayerCoordinates(layer, self.basePt)
         geoms = layerEntitySet.getGeometryCollection()
         if layer.geometryType() != QGis.Polygon:
            for geom in geoms:
               rotatedGeom = qad_utils.rotateQgsGeometry(geom, transformedBasePt, angle)
               self.__rotatedRubberBand.addGeometry(rotatedGeom, layer)
         else:
            for geom in geoms:
               rotatedGeom = qad_utils.rotateQgsGeometry(geom, transformedBasePt, angle)
               self.__rotatedRubberBandPolygon.addGeometry(rotatedGeom, layer)
            
      
   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
      
      if self.__rotatedRubberBand  is not None:
         self.__rotatedRubberBand.hide()
         del self.__rotatedRubberBand
         self.__rotatedRubberBand = None
      if self.__rotatedRubberBandPolygon  is not None:
         self.__rotatedRubberBandPolygon.hide()
         del self.__rotatedRubberBandPolygon
         self.__rotatedRubberBandPolygon = None
               
      # noto il punto base si richiede il secondo punto per l'angolo di rotazione
      if self.mode == Qad_rotate_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_ROTATION_PT:
         angle = qad_utils.getAngleBy2Pts(self.basePt, self.tmpPoint)
         self.addRotatedGeometries(angle)                           
      # noto il punto base si richiede il secondo punto per il nuovo angolo
      elif self.mode == Qad_rotate_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_NEW_ROTATION_PT:
         #qad_debug.breakPoint()
         angle = qad_utils.getAngleBy2Pts(self.basePt, self.tmpPoint)
         diffAngle = angle - self.ReferenceAng
         self.addRotatedGeometries(diffAngle)                           
      # noto il primo punto si richiede il secondo punto per il nuovo angolo
      elif self.mode == Qad_rotate_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_NEW_ROTATION_PT:
         angle = qad_utils.getAngleBy2Pts(self.Pt1NewAng, self.tmpPoint)
         diffAngle = angle - self.ReferenceAng
         self.addRotatedGeometries(diffAngle)                           
         
    
   def activate(self):
      QadGetPoint.activate(self)            
      if self.__rotatedRubberBand is not None:
         self.__rotatedRubberBand.show()
      if self.__rotatedRubberBandPolygon is not None:
         self.__rotatedRubberBandPolygon.show()

   def deactivate(self):
      QadGetPoint.deactivate(self)
      if self.__rotatedRubberBand is not None:
         self.__rotatedRubberBand.hide()
      if self.__rotatedRubberBandPolygon is not None:
         self.__rotatedRubberBandPolygon.hide()

   def setMode(self, mode):
      self.mode = mode
      # noto niente si richiede il punto base
      if self.mode == Qad_rotate_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_BASE_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il punto base si richiede il secondo punto per l'angolo di rotazione
      elif self.mode == Qad_rotate_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_ROTATION_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.basePt)
      # si richiede il primo punto per l'angolo di riferimento
      elif self.mode == Qad_rotate_maptool_ModeEnum.ASK_FOR_FIRST_PT_REFERENCE_ANG:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il primo punto si richiede il secondo punto per l'angolo di riferimento
      elif self.mode == Qad_rotate_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT_REFERENCE_ANG:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.Pt1ReferenceAng)
      # noto il punto base si richiede il secondo punto per il nuovo angolo
      elif self.mode == Qad_rotate_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_NEW_ROTATION_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.basePt)
      # si richiede il primo punto per il nuovo angolo
      elif self.mode == Qad_rotate_maptool_ModeEnum.ASK_FOR_FIRST_NEW_ROTATION_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il primo punto si richiede il secondo punto per il nuovo angolo
      elif self.mode == Qad_rotate_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_NEW_ROTATION_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.Pt1NewAng)
