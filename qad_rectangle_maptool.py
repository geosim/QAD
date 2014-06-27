# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando rectangle
 
                              -------------------
        begin                : 2013-12-3
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

      self.__rectangleRubberBand = None   
      self.geomType = QGis.Polygon

   def hidePointMapToolMarkers(self):
      QadGetPoint.hidePointMapToolMarkers(self)
      if self.__rectangleRubberBand is not None:
         self.__rectangleRubberBand.hide()

   def showPointMapToolMarkers(self):
      QadGetPoint.showPointMapToolMarkers(self)
      if self.__rectangleRubberBand is not None:
         self.__rectangleRubberBand.show()
                             
   def clear(self):
      QadGetPoint.clear(self)
      if self.__rectangleRubberBand is not None:
         self.__rectangleRubberBand.hide()
         del self.__rectangleRubberBand
         self.__rectangleRubberBand = None
      self.mode = None                
      
   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
      
      if self.__rectangleRubberBand  is not None:
         self.__rectangleRubberBand.hide()
         del self.__rectangleRubberBand
         self.__rectangleRubberBand = None

      result = False
      del self.vertices[:] # svuoto la lista
               
      # noto il primo angolo si richiede l'angolo opposto
      if self.mode == Qad_rectangle_maptool_ModeEnum.FIRST_CORNER_KNOWN_ASK_FOR_SECOND_CORNER:
         self.vertices.extend(qad_utils.getRectByCorners(self.firstCorner, self.tmpPoint, self.rot, \
                                                         self.gapType, self.gapValue1, self.gapValue2))
         result = True

      if result == True:
         self.__rectangleRubberBand = createRubberBand(self.canvas, self.geomType, True)      
         if self.vertices is not None:
            tot = len(self.vertices) - 1
            i = 0
            while i <= tot:
               if i < tot:
                  self.__rectangleRubberBand.addPoint(self.vertices[i], False)
               else:  # ultimo punto
                  self.__rectangleRubberBand.addPoint(self.vertices[i], True)
               i = i + 1
         
   def activate(self):
      QadGetPoint.activate(self)            
      if self.__rectangleRubberBand is not None:
         self.__rectangleRubberBand.show()

   def deactivate(self):
      try: # necessario perchè se si chiude QGIS parte questo evento nonostante non ci sia più l'oggetto maptool !
         QadGetPoint.deactivate(self)
         if self.__rectangleRubberBand is not None:
            self.__rectangleRubberBand.hide()
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
