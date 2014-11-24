# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando Ppolygon
 
                              -------------------
        begin                : 2014-11-17
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
from qad_rubberband import createRubberBand


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

      self.__polygonRubberBand = None   
      self.geomType = QGis.Polygon

   def hidePointMapToolMarkers(self):
      QadGetPoint.hidePointMapToolMarkers(self)
      if self.__polygonRubberBand is not None:
         self.__polygonRubberBand.hide()

   def showPointMapToolMarkers(self):
      QadGetPoint.showPointMapToolMarkers(self)
      if self.__polygonRubberBand is not None:
         self.__polygonRubberBand.show()
                             
   def clear(self):
      QadGetPoint.clear(self)
      if self.__polygonRubberBand is not None:
         self.__polygonRubberBand.hide()
         del self.__polygonRubberBand
         self.__polygonRubberBand = None
      self.mode = None                
      
   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
      
      if self.__polygonRubberBand  is not None:
         self.__polygonRubberBand.hide()
         del self.__polygonRubberBand
         self.__polygonRubberBand = None

      result = False
      del self.vertices[:] # svuoto la lista
      
      if self.mode is not None:
         #qad_debug.breakPoint()
         # noto il centro si richiede il raggio
         if self.mode == Qad_polygon_maptool_ModeEnum.CENTER_PT_KNOWN_ASK_FOR_RADIUS:
            radius = qad_utils.getDistance(self.centerPt, self.tmpPoint)
      
            InscribedOption = True if self.constructionModeByCenter == QadMsg.translate("Command_POLYGON", "Inscritto nel cerchio") else False            
            self.vertices.extend(qad_utils.getPolygonByNsidesCenterRadius(self.sideNumber, self.centerPt, radius, \
                                                                          InscribedOption, self.tmpPoint))
            result = True
         # si richiede il secondo punto dello spigolo
         elif self.mode == Qad_polygon_maptool_ModeEnum.FIRST_EDGE_PT_KNOWN_ASK_FOR_SECOND_EDGE_PT:
            self.vertices.extend(qad_utils.getPolygonByNsidesEdgePts(self.sideNumber, self.firstEdgePt, \
                                                                     self.tmpPoint))
            result = True
            
      if result == True:
         self.__polygonRubberBand = createRubberBand(self.canvas, self.geomType, True)      
         if self.vertices is not None:
            tot = len(self.vertices) - 1
            i = 0
            while i <= tot:
               if i < tot:
                  self.__polygonRubberBand.addPoint(self.vertices[i], False)
               else:  # ultimo punto
                  self.__polygonRubberBand.addPoint(self.vertices[i], True)
               i = i + 1
         
   def activate(self):
      QadGetPoint.activate(self)            
      if self.__polygonRubberBand is not None:
         self.__polygonRubberBand.show()

   def deactivate(self):
      try: # necessario perchè se si chiude QGIS parte questo evento nonostante non ci sia più l'oggetto maptool !
         QadGetPoint.deactivate(self)
         if self.__polygonRubberBand is not None:
            self.__polygonRubberBand.hide()
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
