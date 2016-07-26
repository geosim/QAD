# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando offset
 
                              -------------------
        begin                : 2013-10-04
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
from qad_highlight import QadHighlight
from qad_dim import QadDimStyles
from qad_msg import QadMsg


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
      self.__highlight = QadHighlight(self.canvas)

   def hidePointMapToolMarkers(self):
      QadGetPoint.hidePointMapToolMarkers(self)
      self.__highlight.hide()

   def showPointMapToolMarkers(self):
      QadGetPoint.showPointMapToolMarkers(self)
      self.__highlight.show()
                             
   def clear(self):
      QadGetPoint.clear(self)
      self.__highlight.reset()
      self.mode = None    
   
   def addOffSetGeometries(self, newPt):
      self.__highlight.reset()            
      
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      dummy = qad_utils.closestSegmentWithContext(newPt, self.subGeom)
      if self.offSet < 0:
         afterVertex = dummy[2]
         pt = qad_utils.getPerpendicularPointOnInfinityLine(self.subGeom.vertexAt(afterVertex - 1), \
                                                            self.subGeom.vertexAt(afterVertex), \
                                                            newPt)
         offSetDistance = qad_utils.getDistance(newPt, pt)
      else:           
         offSetDistance = self.offSet

         if dummy[3] < 0: # alla sinistra
            offSetDistance = offSetDistance + self.lastOffSetOnLeftSide
         else: # alla destra
            offSetDistance = offSetDistance + self.lastOffSetOnRightSide         
      
      tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
      # uso il crs del canvas per lavorare con coordinate piane xy
      epsg = self.canvas.mapSettings().destinationCrs().authid()
      lines = qad_utils.offSetPolyline(self.subGeom.asPolyline(), epsg, \
                                       offSetDistance, \
                                       "left" if dummy[3] < 0 else "right", \
                                       self.gapType, \
                                       tolerance2ApproxCurve)

      for line in lines:
         if self.layer.geometryType() == QGis.Polygon:
            if line[0] == line[-1]: # se é una linea chiusa
               offsetGeom = QgsGeometry.fromPolygon([line])
            else:
               offsetGeom = QgsGeometry.fromPolyline(line)
         else:
            offsetGeom = QgsGeometry.fromPolyline(line)

         self.__highlight.addGeometry(self.mapToLayerCoordinates(self.layer, offsetGeom), self.layer)
            
      
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
      self.__highlight.show()          

   def deactivate(self):
      try: # necessario perché se si chiude QGIS parte questo evento nonostante non ci sia più l'oggetto maptool !
         QadGetPoint.deactivate(self)
         self.__highlight.hide()
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
         for layer in qad_utils.getVisibleVectorLayers(self.plugIn.canvas): # Tutti i layer vettoriali visibili
            if (layer.geometryType() == QGis.Line or layer.geometryType() == QGis.Polygon) and \
               layer.isEditable():
               if len(QadDimStyles.getDimListByLayer(layer)) == 0:
                  layerList.append(layer)
         
         self.layersToCheck = layerList
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
         self.onlyEditableLayers = True
