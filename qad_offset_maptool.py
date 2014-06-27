# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando offset
 
                              -------------------
        begin                : 2013-10-04
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
from qad_rubberband import QadRubberBand


#===============================================================================
# Qad_offset_maptool_ModeEnum class.
#===============================================================================
class Qad_offset_maptool_ModeEnum():
   # si richiede il primo punto per calcolo offset 
   ASK_FOR_FIRST_OFFSET_PT = 1     
   # noto il primo punto per calcolo offset si richiede il secondo punto
   FIRST_OFFSET_PT_KNOWN_ASK_FOR_SECOND_PT = 2     
   # nota la distanza di offset si richiede il punto per stabilire da che parte
   OFFSET_KNOWN_ASK_FOR_SIDE_PT = 3
   # si richiede il punto di passaggio per stabilire da che parte e a quale offset
   ASK_FOR_PASSAGE_PT = 4  
   # si richiede la selezione di un oggetto
   ASK_FOR_ENTITY_SELECTION = 5  

#===============================================================================
# Qad_offset_maptool class
#===============================================================================
class Qad_offset_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
                        
      self.firstPt = None
      self.layer = None
      self.subGeom = None
      self.offSet = 0
      self.lastOffSetOnLeftSide = 0
      self.lastOffSetOnRightSide = 0
      self.gapType = 0     
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
   
   def addOffSetGeometries(self, newPt):
      self.__rubberBand.reset()            
            
      transformedPt = self.plugIn.canvas.mapRenderer().mapToLayerCoordinates(self.layer, newPt)
      
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      dummy = qad_utils.closestSegmentWithContext(transformedPt, self.subGeom)
      if self.offSet < 0:
         afterVertex = dummy[2]
         pt = qad_utils.getPerpendicularPointOnInfinityLine(self.subGeom.vertexAt(afterVertex - 1), \
                                                            self.subGeom.vertexAt(afterVertex), \
                                                            transformedPt)
         offSetDistance = qad_utils.getDistance(transformedPt, pt)
      else:           
         offSetDistance = qad_utils.distMapToLayerCoordinates(self.offSet, \
                                                              self.plugIn.canvas,\
                                                              self.layer)
         if dummy[3] < 0: # alla sinistra
            offSetDistance = offSetDistance + self.lastOffSetOnLeftSide
         else: # alla destra
            offSetDistance = offSetDistance + self.lastOffSetOnRightSide         
      
      #qad_debug.breakPoint() 
      tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                  self.plugIn.canvas,\
                                                                  self.layer)
      epsg = self.layer.crs().authid()      
      lines = qad_utils.offSetPolyline(self.subGeom.asPolyline(), epsg, \
                                       offSetDistance, \
                                       "left" if dummy[3] < 0 else "right", \
                                       self.gapType, \
                                       tolerance2ApproxCurve)

      for line in lines:
         if self.layer.geometryType() == QGis.Polygon:
            if line[0] == line[-1]: # se è una linea chiusa
               offsetGeom = QgsGeometry.fromPolygon([line])
            else:
               offsetGeom = QgsGeometry.fromPolyline(line)
         else:
            offsetGeom = QgsGeometry.fromPolyline(line)

         self.__rubberBand.addGeometry(offsetGeom, self.layer)
            
      
   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
      
      # nota la distanza di offset si richiede il punto per stabilire da che parte
      if self.mode == Qad_offset_maptool_ModeEnum.OFFSET_KNOWN_ASK_FOR_SIDE_PT:
         self.addOffSetGeometries(self.tmpPoint)                           
      # si richiede il punto di passaggio per stabilire da che parte e a quale offset
      elif self.mode == Qad_offset_maptool_ModeEnum.ASK_FOR_PASSAGE_PT:
         self.addOffSetGeometries(self.tmpPoint)                           
         
    
   def activate(self):
      QadGetPoint.activate(self)            
      self.__rubberBand.show()          

   def deactivate(self):
      try: # necessario perchè se si chiude QGIS parte questo evento nonostante non ci sia più l'oggetto maptool !
         QadGetPoint.deactivate(self)
         self.__rubberBand.hide()
      except:
         pass

   def setMode(self, mode):
      self.clear()
      self.mode = mode
      # si richiede il primo punto per calcolo offset
      if self.mode == Qad_offset_maptool_ModeEnum.ASK_FOR_FIRST_OFFSET_PT:
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
         self.onlyEditableLayers = False
      # noto il primo punto per calcolo offset si richiede il secondo punto
      if self.mode == Qad_offset_maptool_ModeEnum.FIRST_OFFSET_PT_KNOWN_ASK_FOR_SECOND_PT:
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.firstPt)
         self.onlyEditableLayers = False
      # nota la distanza di offset si richiede il punto per stabilire da che parte
      elif self.mode == Qad_offset_maptool_ModeEnum.OFFSET_KNOWN_ASK_FOR_SIDE_PT:
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
         self.onlyEditableLayers = False
      # si richiede il punto di passaggio per stabilire da che parte e a quale offset
      elif self.mode == Qad_offset_maptool_ModeEnum.ASK_FOR_PASSAGE_PT:
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
         self.onlyEditableLayers = False
      # si richiede la selezione di un oggetto
      elif self.mode == Qad_offset_maptool_ModeEnum.ASK_FOR_ENTITY_SELECTION:
         self.setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION)
         # solo layer lineari o poligono editabili che non appartengano a quote
         layerList = []
         for layer in self.plugIn.canvas.layers():
            if layer.type() == QgsMapLayer.VectorLayer and \
               (layer.geometryType() == QGis.Line or layer.geometryType() == QGis.Polygon) and \
               layer.isEditable():
               if self.plugIn.dimStyles.getDimByLayer(layer) is None:
                  layerList.append(layer)
         
         self.layersToCheck = layerList
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
         self.onlyEditableLayers = True
