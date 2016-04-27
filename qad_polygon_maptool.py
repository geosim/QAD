# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando Ppolygon
 
                              -------------------
        begin                : 2014-11-17
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
from qad_msg import QadMsg


#===============================================================================
# Qad_polygon_maptool_ModeEnum class.
#===============================================================================
class Qad_polygon_maptool_ModeEnum():
   # si richiede il centro
   ASK_FOR_CENTER_PT = 1     
   # noto il centro si richiede il raggio
   CENTER_PT_KNOWN_ASK_FOR_RADIUS = 2
   # si richiede il primo punto dello spigolo
   ASK_FOR_FIRST_EDGE_PT = 3
   # si richiede il secondo punto dello spigolo
   FIRST_EDGE_PT_KNOWN_ASK_FOR_SECOND_EDGE_PT = 4

#===============================================================================
# Qad_polygon_maptool class
#===============================================================================
class Qad_polygon_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
      self.mode = None    
                        
      self.sideNumber = None
      self.centerPt = None
      self.constructionModeByCenter = None   
      self.firstEdgePt = None
      self.vertices = []

      self.__rubberBand = QadRubberBand(self.canvas, True)   
      self.geomType = QGis.Polygon

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

      result = False
      del self.vertices[:] # svuoto la lista
      
      if self.mode is not None:
         # noto il centro si richiede il raggio
         if self.mode == Qad_polygon_maptool_ModeEnum.CENTER_PT_KNOWN_ASK_FOR_RADIUS:
            radius = qad_utils.getDistance(self.centerPt, self.tmpPoint)
      
            InscribedOption = True if self.constructionModeByCenter == QadMsg.translate("Command_POLYGON", "Inscribed in circle") else False            
            self.vertices.extend(qad_utils.getPolygonByNsidesCenterRadius(self.sideNumber, self.centerPt, radius, \
                                                                          InscribedOption, self.tmpPoint))
            result = True
         # si richiede il secondo punto dello spigolo
         elif self.mode == Qad_polygon_maptool_ModeEnum.FIRST_EDGE_PT_KNOWN_ASK_FOR_SECOND_EDGE_PT:
            self.vertices.extend(qad_utils.getPolygonByNsidesEdgePts(self.sideNumber, self.firstEdgePt, \
                                                                     self.tmpPoint))
            result = True
            
      if result == True:         
         if self.vertices is not None:
            if self.geomType == QGis.Polygon:
               self.__rubberBand.setPolygon(self.vertices)
            else:
               self.__rubberBand.setLine(self.vertices)            
         
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
      # si richiede il centro
      if self.mode == Qad_polygon_maptool_ModeEnum.ASK_FOR_CENTER_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il centro si richiede il raggio
      if self.mode == Qad_polygon_maptool_ModeEnum.CENTER_PT_KNOWN_ASK_FOR_RADIUS:         
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.centerPt)
      # si richiede il primo punto dello spigolo
      if self.mode == Qad_polygon_maptool_ModeEnum.ASK_FOR_FIRST_EDGE_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # si richiede il secondo punto dello spigolo
      if self.mode == Qad_polygon_maptool_ModeEnum.FIRST_EDGE_PT_KNOWN_ASK_FOR_SECOND_EDGE_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.firstEdgePt)
