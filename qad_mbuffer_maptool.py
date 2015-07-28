# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando mbuffer
 
                              -------------------
        begin                : 2013-09-19
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


import qad_utils
from qad_snapper import *
from qad_snappointsdisplaymanager import *
from qad_variables import *
from qad_getpoint import *
from qad_rubberband import QadRubberBand


#===============================================================================
# Qad_mbuffer_maptool_ModeEnum class.
#===============================================================================
class Qad_mbuffer_maptool_ModeEnum():
   # noto niente si richiede il primo punto
   NONE_KNOWN_ASK_FOR_FIRST_PT = 1     
   # noto il primo punto si richiede la larghezza del buffer
   FIRST_PT_ASK_FOR_BUFFER_WIDTH = 2     

#===============================================================================
# Qad_mbuffer_maptool class
#===============================================================================
class Qad_mbuffer_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
                        
      self.startPtForBufferWidth = None
      # vedi il numero minimo di punti affinché venga riconosciuto un arco o un cerchio
      # nei files qad_arc.py e qad_circle.py
      self.segments = 12
      self.entitySet = QadEntitySet()
      self.geomType = QGis.Polygon
      self.__rubberBand = QadRubberBand(self.canvas)   

   def hidePointMapToolMarkers(self):
      QadGetPoint.hidePointMapToolMarkers(self)
      self.__rubberBand.hide()

   def showPointMapToolMarkers(self):
      QadGetPoint.showPointMapToolMarkers(self)
      self.__rubberBand.show()
                             
   def clear(self):
      QadGetPoint.clear(self)
      self.__rubberBand.reset()
      self.mode = None    
      
      
   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
      
      self.__rubberBand.reset()
               
      # noto il primo punto si richiede la larghezza del buffer
      if self.mode == Qad_mbuffer_maptool_ModeEnum.FIRST_PT_ASK_FOR_BUFFER_WIDTH:
         for layerEntitySet in self.entitySet.layerEntitySetList:
            transformedPt1 = self.canvas.mapRenderer().mapToLayerCoordinates(layerEntitySet.layer, self.startPtForBufferWidth)
            transformedPt2 = self.canvas.mapRenderer().mapToLayerCoordinates(layerEntitySet.layer, self.tmpPoint)
            width = qad_utils.getDistance(transformedPt1, transformedPt2)
            tolerance = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                            self.canvas,\
                                                            layerEntitySet.layer)
            
            geoms = layerEntitySet.getGeometryCollection()
            for geom in geoms:
               bufferGeom = qad_utils.ApproxCurvesOnGeom(geom.buffer(width, self.segments), \
                                                         self.segments, self.segments, \
                                                         tolerance)
               if bufferGeom:
                  self.__rubberBand.addGeometry(bufferGeom, layerEntitySet.layer)
                           
    
   def activate(self):
      QadGetPoint.activate(self)           
      self.__rubberBand.show() 

   def deactivate(self):
      try: # necessario perché se si chiude QGIS parte questo evento nonostante non ci sia più l'oggetto maptool !
         QadGetPoint.deactivate(self)
         self.__rubberBand.hide()
      except:
         pass

   def setMode(self, mode):
      self.mode = mode
      # noto niente si richiede il primo punto
      if self.mode == Qad_mbuffer_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il primo punto si richiede la larghezza del buffer
      elif self.mode == Qad_mbuffer_maptool_ModeEnum.FIRST_PT_ASK_FOR_BUFFER_WIDTH:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.startPtForBufferWidth)
