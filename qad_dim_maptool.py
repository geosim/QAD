# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito dei comandi di quotatura
 
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
from qad_dim import *
from qad_rubberband import QadRubberBand


#===============================================================================
# Qad_dim_maptool_ModeEnum class.
#===============================================================================
class Qad_dim_maptool_ModeEnum():
   # noto niente si richiede il primo punto di quotatura
   NONE_KNOWN_ASK_FOR_FIRST_PT = 1     
   # noto il primo punto si richiede il secondo punto di quotatura
   FIRST_PT_KNOWN_ASK_FOR_SECOND_PT = 2     
   # noto i punti di quotatura si richiede la posizione della linea di quota
   FIRST_SECOND_PT_KNOWN_ASK_FOR_LINEAR_DIM_LINE_POS = 3     
   # noto il primo e il secondo punto si richiede il terzo punto
   FIRST_SECOND_PT_KNOWN_ASK_FOR_THIRD_PT = 6
   # noto niente si richiede il primo punto di estremità diam
   NONE_KNOWN_ASK_FOR_FIRST_DIAM_PT = 7
   # noto il primo punto di estremità diam si richiede il secondo punto di estremità diam
   FIRST_DIAM_PT_KNOWN_ASK_FOR_SECOND_DIAM_PT = 8
   # noto niente si richiede l'entita del primo punto di tangenza
   NONE_KNOWN_ASK_FOR_FIRST_TAN = 9
   # nota l'entita del primo punto di tangenza si richiede quella del secondo punto di tangenza
   FIRST_TAN_KNOWN_ASK_FOR_SECOND_TAN = 10
   # note la prima e la seconda entita dei punti di tangenza si richiede il raggio
   FIRST_SECOND_TAN_KNOWN_ASK_FOR_RADIUS = 11
   # noto note la prima, la seconda entita dei punti di tangenza e il primo punto per misurare il raggio
   # si richiede il secondo punto per misurare il raggio
   FIRST_SECOND_TAN_FIRSTPTRADIUS_KNOWN_ASK_FOR_SECONDPTRADIUS = 12

#===============================================================================
# Qad_dim_maptool class
#===============================================================================
class Qad_dim_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)

      dimStyle = None
      self.dimPt1 = None
      self.dimPt2 = None
      self.preferredAlignment = QadDimStyleAlignmentEnum.HORIZONTAL
      self.measure = None # calcolato dalla grafica
      
      self.__rubberBand = QadRubberBand(self.canvas)      
                              
      
      self.centerPt = None
      self.radius = None
      self.dimPt1 = None
      self.dimPt2 = None
      self.firstDiamPt = None
      self.tan1 = None
      self.tan2 = None
      self.startPtForRadius = None
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
      #qad_debug.breakPoint()
      QadGetPoint.canvasMoveEvent(self, event)
      
      self.__rubberBand.reset()            
         
      items = []
      dimPtFeatures = [None, None]
      dimLineFeatures = [None, None]
      textFeature = None
      blockFeatures = [None, None]
      extLineFeatures = [None, None]
      txtLeaderLineFeature = None
      
      # noto i punti di quotatura si richiede la posizione della linea di quota
      if self.mode == Qad_dim_maptool_ModeEnum.FIRST_SECOND_PT_KNOWN_ASK_FOR_LINEAR_DIM_LINE_POS:
         if self.dimPt1.x() < self.dimPt2.x():
            minX = self.dimPt1.x()
            maxX = self.dimPt2.x()
         else:
            maxX = self.dimPt1.x()
            minX = self.dimPt2.x()
            
         if self.dimPt1.y() < self.dimPt2.y():
            minY = self.dimPt1.y()
            maxY = self.dimPt2.y()
         else:
            maxY = self.dimPt1.y()
            minY = self.dimPt2.y()

         #qad_debug.breakPoint()
         if (self.tmpPoint.x() > minX and self.tmpPoint.x() < maxX) and \
            (self.tmpPoint.y() > maxY or self.tmpPoint.y() < minY):
            self.preferredAlignment = QadDimStyleAlignmentEnum.HORIZONTAL
         elif (self.tmpPoint.x() > maxX or self.tmpPoint.x() < minX) and \
              (self.tmpPoint.y() > minY and self.tmpPoint.y() < maxY):
            self.preferredAlignment = QadDimStyleAlignmentEnum.VERTICAL
         elif minY == maxY: # linea di quota orizzontale
            self.preferredAlignment = QadDimStyleAlignmentEnum.HORIZONTAL
         elif minX == maxX: # linea di quota verticale
            self.preferredAlignment = QadDimStyleAlignmentEnum.VERTICAL
         
         dimPtFeatures, dimLineFeatures, textFeatureGeom, \
         blockFeatures, extLineFeatures, txtLeaderLineFeature = self.dimStyle.getLinearDimFeatures(self.canvas, \
                                                                                                   self.dimPt1, \
                                                                                                   self.dimPt2, \
                                                                                                   self.tmpPoint, \
                                                                                                   self.measure, \
                                                                                                   self.preferredAlignment)
         textFeature = textFeatureGeom[0]
         textRectGeom = textFeatureGeom[1]
      # punti di quotatura
      if dimPtFeatures[0] is not None:
         items.append([dimPtFeatures[0].geometry(), self.dimStyle.symbolLayer])
      if dimPtFeatures[1] is not None:
         items.append([dimPtFeatures[1].geometry(), self.dimStyle.symbolLayer])
      # linee di quota
      if dimLineFeatures[0] is not None:
         items.append([dimLineFeatures[0].geometry(), self.dimStyle.lineLayer])
      if dimLineFeatures[1] is not None:
         items.append([dimLineFeatures[1].geometry(), self.dimStyle.lineLayer])
      # testo di quota
      if textFeature is not None:
         items.append([textFeature.geometry(), self.dimStyle.textLayer])
         items.append([textRectGeom, self.dimStyle.textLayer])
      # simboli di quota
      if blockFeatures[0] is not None:
         items.append([blockFeatures[0].geometry(), self.dimStyle.symbolLayer])
      if blockFeatures[1] is not None:
         items.append([blockFeatures[1].geometry(), self.dimStyle.symbolLayer])
      # linee di estensione della quota
      if extLineFeatures[0] is not None:
         items.append([extLineFeatures[0].geometry(), self.dimStyle.lineLayer])
      if extLineFeatures[1] is not None:
         items.append([extLineFeatures[1].geometry(), self.dimStyle.lineLayer])
      # linea leader del testo di quota   
      if txtLeaderLineFeature is not None:
         items.append([txtLeaderLineFeature.geometry(), self.dimStyle.lineLayer])
         
      # noto il centro del cerchio si richiede il diametro
      #elif self.mode == Qad_dim_maptool_ModeEnum.CENTER_PT_KNOWN_ASK_FOR_DIAM:
      #   pass
      
      for item in items:         
         self.__rubberBand.addGeometry(item[0], item[1]) # geom e layer
    
   def activate(self):
      QadGetPoint.activate(self)            
      if self.__rubberBand is not None:
         self.__rubberBand.show()

   def deactivate(self):
      QadGetPoint.deactivate(self)
      if self.__rubberBand is not None:
         self.__rubberBand.hide()

   def setMode(self, mode):
      self.mode = mode
      # noto niente si richiede il primo punto di quotatura
      if self.mode == Qad_dim_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il primo punto si richiede il secondo punto di quotatura
      elif self.mode == Qad_dim_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.dimPt1)
      # noto i punti di quotatura si richiede la posizione della linea di quota
      elif self.mode == Qad_dim_maptool_ModeEnum.FIRST_SECOND_PT_KNOWN_ASK_FOR_LINEAR_DIM_LINE_POS:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)         
      # noto il primo e il secondo punto si richiede il terzo punto
      elif self.mode == Qad_dim_maptool_ModeEnum.FIRST_SECOND_PT_KNOWN_ASK_FOR_THIRD_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)         
      # noto niente si richiede il primo punto di estremità diam
      elif self.mode == Qad_dim_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_DIAM_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)                 
      # noto il primo punto di estremità diam si richiede il secondo punto di estremità diam
      elif self.mode == Qad_dim_maptool_ModeEnum.FIRST_DIAM_PT_KNOWN_ASK_FOR_SECOND_DIAM_PT:     
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto niente si richiede l'entita del primo punto di tangenza
      elif self.mode == Qad_dim_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_TAN:     
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
         self.setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION)
         self.forceSnapTypeOnce(QadSnapTypeEnum.TAN_DEF)         
      # nota l'entita del primo punto di tangenza si richiede quella del secondo punto di tangenza
      elif self.mode == Qad_dim_maptool_ModeEnum.FIRST_TAN_KNOWN_ASK_FOR_SECOND_TAN:     
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
         self.setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION)
         self.forceSnapTypeOnce(QadSnapTypeEnum.TAN_DEF)         
      # note la prima e la seconda entita dei punti di tangenza si richiede il raggio
      elif self.mode == Qad_dim_maptool_ModeEnum.FIRST_SECOND_TAN_KNOWN_ASK_FOR_RADIUS:     
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
         # siccome il puntatore era stato variato in ENTITY_SELECTION dalla selez precedente
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)         
      # noto note la prima, la seconda entita dei punti di tangenza e il primo punto per misurare il raggio
      # si richiede il secondo punto per misurare il raggio
      elif self.mode == Qad_dim_maptool_ModeEnum.FIRST_SECOND_TAN_FIRSTPTRADIUS_KNOWN_ASK_FOR_SECONDPTRADIUS:     
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.startPtForRadius)
