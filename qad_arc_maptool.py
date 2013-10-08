# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool di richiesta di un punto in ambito del comando arco
 
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
from qad_arc import *


#===============================================================================
# Qad_arc_maptool_ModeEnum class.
#===============================================================================
class Qad_arc_maptool_ModeEnum():
   # noto niente si richiede il primo punto
   NONE_KNOWN_ASK_FOR_START_PT = 1     
   # noto il punto iniziale dell'arco si richiede il secondo punto
   START_PT_KNOWN_ASK_FOR_SECOND_PT = 2     
   # noti il punto iniziale e il secondo punto dell'arco si richiede il punto finale
   START_SECOND_PT_KNOWN_ASK_FOR_END_PT = 3     
   # noto il punto iniziale dell'arco si richiede il centro
   START_PT_KNOWN_ASK_FOR_CENTER_PT = 4     
   # noti il punto iniziale e il centro dell'arco si richiede il punto finale
   START_CENTER_PT_KNOWN_ASK_FOR_END_PT = 5     
   # noti il punto iniziale e il centro dell'arco si richiede l'angolo inscritto
   START_CENTER_PT_KNOWN_ASK_FOR_ANGLE = 6     
   # noti il punto iniziale e il centro dell'arco si richiede la lunghezza della corda
   START_CENTER_PT_KNOWN_ASK_FOR_CHORD = 7
   # noto il punto iniziale dell'arco si richiede il punto finale
   START_PT_KNOWN_ASK_FOR_END_PT = 8     
   # noti il punto iniziale e finale dell'arco si richiede il centro
   START_END_PT_KNOWN_ASK_FOR_CENTER = 9
   # noti il punto iniziale e finale dell'arco si richiede l'angolo inscritto
   START_END_PT_KNOWN_ASK_FOR_ANGLE = 10
   # noti il punto iniziale e finale dell'arco si richiede la direzione della tangente al punto iniziale
   START_END_PT_KNOWN_ASK_FOR_TAN = 11
   # noti il punto iniziale e finale dell'arco si richiede il raggio
   START_END_PT_KNOWN_ASK_FOR_RADIUS = 12        
   # noto niente si richiede il centro
   NONE_KNOWN_ASK_FOR_CENTER_PT = 13
   # noto il centro dell'arco si richiede il punto iniziale
   CENTER_PT_KNOWN_ASK_FOR_START_PT = 14      
   # noti il punto iniziale e la tangente al punto iniziale si richiede il punto finale
   START_PT_TAN_KNOWN_ASK_FOR_END_PT = 15
   # noto il punto iniziale dell'arco si richiede l'angolo inscritto
   START_PT_KNOWN_ASK_FOR_ANGLE = 16     
   # noti il punto iniziale e l'angolo inscritto dell'arco si richiede il punto finale
   START_PT_ANGLE_KNOWN_ASK_FOR_END_PT = 17     
   # noti il punto iniziale e l'angolo inscritto dell'arco si richiede il centro
   START_PT_ANGLE_KNOWN_ASK_FOR_CENTER_PT = 18
   # noti il punto iniziale e l'angolo inscritto dell'arco si richiede il raggio
   START_PT_ANGLE_KNOWN_ASK_FOR_RADIUS = 19
   # noti il punto iniziale e l'angolo inscritto dell'arco si richiede il secondo punto per misurare il raggio
   START_PT_ANGLE_KNOWN_ASK_FOR_SECONDPTRADIUS = 20
   # noti il punto iniziale, l'angolo inscritto e il raggio dell'arco si richiede la direzione della corda
   START_PT_ANGLE_RADIUS_KNOWN_ASK_FOR_CHORDDIRECTION = 21
   # noti il punto iniziale e il raggio dell'arco si richiede il punto finale
   START_PT_RADIUS_KNOWN_ASK_FOR_END_PT = 22        


#===============================================================================
# Qad_arc_maptool class
#===============================================================================
class Qad_arc_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
                        
      self.arcStartPt = None
      self.arcSecondPt = None
      self.arcEndPt = None
      self.arcCenterPt = None
      self.arcTanOnStartPt = None
      self.arcAngle = None
      self.arcStartPtForRadius = None
      self.arcRadius = None
      self.__arcRubberBand = None   

   def hidePointMapToolMarkers(self):
      QadGetPoint.hidePointMapToolMarkers(self)
      if self.__arcRubberBand is not None:
         self.__arcRubberBand.hide()

   def showPointMapToolMarkers(self):
      QadGetPoint.showPointMapToolMarkers(self)
      if self.__arcRubberBand is not None:
         self.__arcRubberBand.show()
                             
   def clear(self):
      QadGetPoint.clear(self)
      if self.__arcRubberBand is not None:
         self.__arcRubberBand.hide()
         del self.__arcRubberBand
         self.__arcRubberBand = None
      self.mode = None
      
      
   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
      
      if self.__arcRubberBand is not None:
         self.__arcRubberBand.hide()
         del self.__arcRubberBand
         self.__arcRubberBand = None
         
      result = False
      arc = QadArc()    
       
      # noti il primo e il secondo punto dell'arco si richiede il terzo punto
      if self.mode == Qad_arc_maptool_ModeEnum.START_SECOND_PT_KNOWN_ASK_FOR_END_PT:
         result = arc.fromStartSecondEndPts(self.arcStartPt, self.arcSecondPt, self.tmpPoint)
      # noti il primo punto e il centro dell'arco si richiede il punto finale
      elif self.mode == Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_END_PT:
         result = arc.fromStartCenterEndPts(self.arcStartPt, self.arcCenterPt, self.tmpPoint)
      # noti il primo punto e il centro dell'arco si richiede l'angolo inscritto
      elif self.mode == Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_ANGLE:
         angle = qad_utils.getAngleBy2Pts(self.arcCenterPt, self.tmpPoint)
         result = arc.fromStartCenterPtsAngle(self.arcStartPt, self.arcCenterPt, angle)
      # noti il primo punto e il centro dell'arco si richiede la lunghezza della corda
      elif self.mode == Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_CHORD:     
         chord = qad_utils.getDistance(self.arcStartPt, self.tmpPoint)
         result = arc.fromStartCenterPtsChord(self.arcStartPt, self.arcCenterPt, chord)
      # noti il punto iniziale e finale dell'arco si richiede il centro
      elif self.mode == Qad_arc_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_CENTER:     
         result = arc.fromStartCenterEndPts(self.arcStartPt, self.tmpPoint, self.arcEndPt)
      # noti il punto iniziale e finale dell'arco si richiede l'angolo inscritto
      elif self.mode == Qad_arc_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_ANGLE:     
         angle = qad_utils.getAngleBy2Pts(self.arcStartPt, self.tmpPoint)
         result = arc.fromStartEndPtsAngle(self.arcStartPt, self.arcEndPt, angle)
      # noti il punto iniziale e finale dell'arco si richiede la direzione della tangente
      elif self.mode == Qad_arc_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_TAN:     
         tan = qad_utils.getAngleBy2Pts(self.arcStartPt, self.tmpPoint)
         result = arc.fromStartEndPtsTan(self.arcStartPt, self.arcEndPt, tan)
      # noti il punto iniziale e finale dell'arco si richiede il raggio
      elif self.mode == Qad_arc_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_RADIUS:     
         radius = qad_utils.getDistance(self.arcEndPt, self.tmpPoint)
         result = arc.fromStartEndPtsRadius(self.arcStartPt, self.arcEndPt, radius)
      # noti il punto iniziale e la tangente al punto iniziale si richiede il punto finale
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_TAN_KNOWN_ASK_FOR_END_PT:     
         result = arc.fromStartEndPtsTan(self.arcStartPt, self.tmpPoint, self.arcTanOnStartPt)         
      # noti il punto iniziale e l'angolo inscritto dell'arco si richiede il punto finale
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_END_PT:     
         result = arc.fromStartEndPtsAngle(self.arcStartPt, self.tmpPoint, self.arcAngle)
      # noti il punto iniziale e l'angolo inscritto dell'arco si richiede il centro
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_CENTER_PT:     
         result = arc.fromStartCenterPtsAngle(self.arcStartPt, self.tmpPoint, self.arcAngle)
      # noti il punto iniziale, l'angolo inscritto e il raggio dell'arco si richiede la direzione della corda
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_ANGLE_RADIUS_KNOWN_ASK_FOR_CHORDDIRECTION:     
         chordDirection = qad_utils.getAngleBy2Pts(self.arcStartPt, self.tmpPoint)
         result = arc.fromStartPtAngleRadiusChordDirection(self.arcStartPt, self.arcAngle, \
                                                           self.arcRadius, chordDirection)
      # noti il punto iniziale e il raggio dell'arco si richiede il punto finale
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_RADIUS_KNOWN_ASK_FOR_END_PT:     
         result = arc.fromStartEndPtsRadius(self.arcStartPt, self.tmpPoint, self.arcRadius)
      
      if result == True:
         self.__arcRubberBand = QgsRubberBand(self.canvas, False)
         points = arc.asPolyline()
      
         if points is not None:
            tot = len(points) - 1
            i = 0
            while i <= tot:
               if i < tot:
                  self.__arcRubberBand.addPoint(points[i], False)
               else: # ultimo punto
                  self.__arcRubberBand.addPoint(points[i], True)
               i = i + 1
      
    
   def activate(self):
      QadGetPoint.activate(self)            
      if self.__arcRubberBand is not None:
         self.__arcRubberBand.show()

   def deactivate(self):
      QadGetPoint.deactivate(self)
      if self.__arcRubberBand is not None:
         self.__arcRubberBand.hide()

   def setMode(self, mode):
      self.mode = mode
      # noto niente si richiede il primo punto
      if self.mode == Qad_arc_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_START_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il primo punto dell'arco si richiede il secondo punto
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_SECOND_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcStartPt)
      # noti il primo e il secondo punto dell'arco si richiede il terzo punto
      elif self.mode == Qad_arc_maptool_ModeEnum.START_SECOND_PT_KNOWN_ASK_FOR_END_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il primo punto dell'arco si richiede il centro         
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_CENTER_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcStartPt)
      # noti il primo punto e il centro dell'arco si richiede il punto finale
      elif self.mode == Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_END_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcCenterPt)
      # noti il primo punto e il centro dell'arco si richiede l'angolo inscritto
      elif self.mode == Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_ANGLE:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcCenterPt)
      # noti il primo punto e il centro dell'arco si richiede la lunghezza della corda
      elif self.mode == Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_CHORD:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcStartPt)
      # noto il punto iniziale dell'arco si richiede il punto finale
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_END_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcStartPt)
      # noti il punto iniziale e finale dell'arco si richiede il centro
      elif self.mode == Qad_arc_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_CENTER:     
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noti il punto iniziale e finale dell'arco si richiede l'angolo inscritto
      elif self.mode == Qad_arc_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_ANGLE:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcStartPt)
      # noti il punto iniziale e finale dell'arco si richiede la direzione della tangente
      elif self.mode == Qad_arc_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_TAN:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcStartPt)
      # noti il punto iniziale e finale dell'arco si richiede il raggio
      elif self.mode == Qad_arc_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_RADIUS:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)                  
         self.setStartPoint(self.arcEndPt)
      # noto niente si richiede il centro
      elif self.mode == Qad_arc_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_CENTER_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il centro dell'arco si richiede il punto iniziale
      elif self.mode == Qad_arc_maptool_ModeEnum.CENTER_PT_KNOWN_ASK_FOR_START_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)                  
         self.setStartPoint(self.arcCenterPt)
      # noti il punto iniziale e la tangente al punto iniziale si richiede il punto finale
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_TAN_KNOWN_ASK_FOR_END_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)                  
         self.setStartPoint(self.arcStartPt)
      # noto il punto iniziale dell'arco si richiede l'angolo inscritto
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_ANGLE:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcStartPt)
      # noti il punto iniziale e l'angolo inscritto dell'arco si richiede il punto finale
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_END_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcStartPt)
      # noti il punto iniziale e l'angolo inscritto dell'arco si richiede il centro
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_CENTER_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noti il punto iniziale e l'angolo inscritto dell'arco si richiede il raggio
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_RADIUS:     
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noti il punto iniziale e l'angolo inscritto dell'arco si richiede il secondo punto per misurare il raggio
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_SECONDPTRADIUS:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcStartPtForRadius)
      # noti il punto iniziale, l'angolo inscritto e il raggio dell'arco si richiede la direzione della corda
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_ANGLE_RADIUS_KNOWN_ASK_FOR_CHORDDIRECTION:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcStartPt)
      # noti il punto iniziale e il raggio dell'arco si richiede il punto finale
      elif self.mode == Qad_arc_maptool_ModeEnum.START_PT_RADIUS_KNOWN_ASK_FOR_END_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.arcStartPt)
         