# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando rectangle
 
                              -------------------
        begin                : 2013-12-3
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
# Qad_rectangle_maptool_ModeEnum class.
#===============================================================================
class Qad_rectangle_maptool_ModeEnum():
   # noto niente si richiede il primo angolo
   NONE_KNOWN_ASK_FOR_FIRST_CORNER = 1     
   # noto il primo angolo si richiede l'angolo opposto
   FIRST_CORNER_KNOWN_ASK_FOR_SECOND_CORNER = 2     

#===============================================================================
# Qad_rotate_maptool class
#===============================================================================
class Qad_rectangle_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
                        
      self.firstCorner = None
      self.secondCorner = None
      self.basePt = None
      self.gapType = 0 # 0 = Angoli retti; 1 = Raccorda i segmenti; 2 = Cima i segmenti
      self.gapValue1 = 0 # se gapType = 1 -> raggio di curvatura; se gapType = 2 -> prima distanza di cimatura
      self.gapValue2 = 0 # se gapType = 2 -> seconda distanza di cimatura
      self.rot = 0
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
               
      # noto il primo angolo si richiede l'angolo opposto
      if self.mode == Qad_rectangle_maptool_ModeEnum.FIRST_CORNER_KNOWN_ASK_FOR_SECOND_CORNER:
         self.vertices.extend(qad_utils.getRectByCorners(self.firstCorner, self.tmpPoint, self.rot, \
                                                         self.gapType, self.gapValue1, self.gapValue2))
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
      # noto niente si richiede il primo angolo
      if self.mode == Qad_rectangle_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_CORNER:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il primo angolo si richiede l'angolo opposto
      elif self.mode == Qad_rectangle_maptool_ModeEnum.FIRST_CORNER_KNOWN_ASK_FOR_SECOND_CORNER:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
