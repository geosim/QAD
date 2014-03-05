# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool di richiesta di un punto in ambito del comando line
 
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
from qad_variables import *
from qad_getpoint import *
from qad_circle import *
from qad_rubberband import createRubberBand


#===============================================================================
# Qad_line_maptool_ModeEnum class.
#===============================================================================
class Qad_line_maptool_ModeEnum():
   # noto niente si richiede il primo punto
   NONE_KNOWN_ASK_FOR_FIRST_PT = 1
   # noto il primo punto si richiede il secondo punto
   FIRST_PT_KNOWN_ASK_FOR_SECOND_PT = 2      
   # nota l'entita del primo punto di tangenza si richiede il secondo punto
   FIRST_TAN_KNOWN_ASK_FOR_SECOND_PT = 3
   # nota l'entita del primo punto di perpendicolarità si richiede il secondo punto
   FIRST_PER_KNOWN_ASK_FOR_SECOND_PT = 4
   

#===============================================================================
# Qad_line_maptool class
#===============================================================================
class Qad_line_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
                        
      self.firstPt = None
      self.tan1 = None
      self.per1 = None
      self.geom1 = None
      self.__lineRubberBand = None   

   def hidePointMapToolMarkers(self):
      QadGetPoint.hidePointMapToolMarkers(self)
      if self.__lineRubberBand is not None:
         self.__lineRubberBand.hide()

   def showPointMapToolMarkers(self):
      QadGetPoint.showPointMapToolMarkers(self)
      if self.__lineRubberBand is not None:
         self.__lineRubberBand.show()
                             
   def clear(self):
      QadGetPoint.clear(self)
      if self.__lineRubberBand is not None:
         self.__lineRubberBand.hide()
         del self.__lineRubberBand
         self.__lineRubberBand = None
      self.mode = None
      
      
   def canvasMoveEvent(self, event):
      #qad_debug.breakPoint()
      QadGetPoint.canvasMoveEvent(self, event)
      
      if self.__lineRubberBand  is not None:
         self.__lineRubberBand.hide()
         del self.__lineRubberBand
         self.__lineRubberBand = None
         
      line = None
      
      # noto il primo punto si richiede il secondo punto
      if self.mode == Qad_line_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT:
         if (self.firstPt is not None):
            line = [self.firstPt, self.tmpPoint]
      # nota l'entita del primo punto di tangenza si richiede il secondo punto
      elif self.mode == Qad_line_maptool_ModeEnum.FIRST_TAN_KNOWN_ASK_FOR_SECOND_PT:
         snapper = QadSnapper()
         snapper.setSnapPointCRS(self.canvas.mapRenderer().destinationCrs())
         snapper.setSnapType(QadSnapTypeEnum.TAN)
         snapper.setStartPoint(self.tmpPoint)
         oSnapPoints = snapper.getSnapPoint(self.geom1, self.tan1, self.canvas.mapRenderer().destinationCrs())
         # memorizzo il punto di snap in point (prendo il primo valido)
         for item in oSnapPoints.items():
            points = item[1]
            if points is not None:
               line = [points[0], self.tmpPoint]
               break
      # nota l'entita del primo punto di perpendicolarità si richiede il secondo punto
      elif self.mode == Qad_line_maptool_ModeEnum.FIRST_PER_KNOWN_ASK_FOR_SECOND_PT:
         snapper = QadSnapper()
         snapper.setSnapPointCRS(self.canvas.mapRenderer().destinationCrs())
         snapper.setSnapType(QadSnapTypeEnum.PER)
         snapper.setStartPoint(self.tmpPoint)
         oSnapPoints = snapper.getSnapPoint(self.geom1, self.per1, self.canvas.mapRenderer().destinationCrs())
         # memorizzo il punto di snap in point (prendo il primo valido)
         for item in oSnapPoints.items():
            points = item[1]
            if points is not None:
               line = [points[0], self.tmpPoint]
               break
      
      if line is not None:
         self.__lineRubberBand = createRubberBand(self.canvas, QGis.Line)
         self.__lineRubberBand.addPoint(line[0], False)
         self.__lineRubberBand.addPoint(line[1], True)
      
    
   def activate(self):
      QadGetPoint.activate(self)            
      if self.__lineRubberBand is not None:
         self.__lineRubberBand.show()

   def deactivate(self):
      QadGetPoint.deactivate(self)
      if self.__lineRubberBand is not None:
         self.__lineRubberBand.hide()

   def setMode(self, mode):
      self.mode = mode
      # noto niente si richiede il primo punto
      if self.mode == Qad_line_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE) 
         self.setStartPoint(None)
      # noto il primo punto si richiede il secondo punto
      elif self.mode == Qad_line_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.firstPt)
      # nota l'entita del primo punto di tangenza si richiede il secondo punto
      elif self.mode == Qad_line_maptool_ModeEnum.FIRST_TAN_KNOWN_ASK_FOR_SECOND_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE) 
      # nota l'entita del primo punto di perpendicolarità si richiede il secondo punto
      elif self.mode == Qad_line_maptool_ModeEnum.FIRST_PER_KNOWN_ASK_FOR_SECOND_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.NONE) 
