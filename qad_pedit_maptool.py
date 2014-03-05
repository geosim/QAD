# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando pedit
 
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
from qad_variables import *
from qad_getpoint import *
from qad_rubberband import QadRubberBand


#===============================================================================
# Qad_pedit_maptool_ModeEnum class.
#===============================================================================
class Qad_pedit_maptool_ModeEnum():
   # si richiede la selezione di un'entità
   ASK_FOR_ENTITY_SEL = 1     
   # non si richiede niente
   NONE = 2     
   # si richiede il primo punto per calcolo distanza di approssimazione 
   ASK_FOR_FIRST_TOLERANCE_PT = 3     
   # noto il primo punto per calcolo distanza di approssimazione si richiede il secondo punto
   FIRST_TOLERANCE_PT_KNOWN_ASK_FOR_SECOND_PT = 4
   # si richiede un nuovo vertice da inserire
   ASK_FOR_NEW_VERTEX = 5   
   # si richiede la nuova posizione di un vertice da spostare
   ASK_FOR_MOVE_VERTEX = 6     
   # si richiede la posizione più vicina ad un vertice
   ASK_FOR_VERTEX = 7     


#===============================================================================
# Qad_pedit_maptool class
#===============================================================================
class Qad_pedit_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)

      self.firstPt = None
                       
      self.layer = None 
      self.linearObjectList = qad_utils.QadLinearObjectList()
      self.tolerance2ApproxCurve = None
      self.vertexAt = 0
      self.after = True 
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

   def setLinearObjectList(self, linearObjectList, layer):
      self.linearObjectList.set(linearObjectList)
      self.layer = layer
      self.tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                       self.canvas,\
                                                                       self.layer)                              

   def setVertexAt(self, vertexAt, after = None):
      #qad_debug.breakPoint()
      if vertexAt == self.linearObjectList.qty():
         pt = self.linearObjectList.getLinearObjectAt(-1).getEndPt()
      else:
         pt = self.linearObjectList.getLinearObjectAt(vertexAt).getStartPt()
      
      self.firstPt = self.canvas.mapRenderer().layerToMapCoordinates(self.layer, pt)         
      self.vertexAt = vertexAt
      self.after = after      
    
      
   def canvasMoveEvent(self, event):
      #qad_debug.breakPoint()
      QadGetPoint.canvasMoveEvent(self, event)
      
      self.__rubberBand.reset()
      tmpLinearObjectList = None           
       
      # noti il primo punto e il centro dell'arco si richiede il punto finale
      if self.mode == Qad_pedit_maptool_ModeEnum.ASK_FOR_NEW_VERTEX:
         #qad_debug.breakPoint()
         newPt = self.canvas.mapRenderer().mapToLayerCoordinates(self.layer, self.tmpPoint)
         tmpLinearObjectList = qad_utils.QadLinearObjectList()
         tmpLinearObjectList.set(self.linearObjectList)
         if self.after: # dopo
            if self.vertexAt == tmpLinearObjectList.qty() and tmpLinearObjectList.isClosed():
               tmpLinearObjectList.insertPoint(0, newPt)
            else:
               tmpLinearObjectList.insertPoint(self.vertexAt, newPt)
         else: # prima
            if self.vertexAt == 0 and tmpLinearObjectList.isClosed():
               tmpLinearObjectList.insertPoint(tmpLinearObjectList.qty() - 1, newPt)
            else:
               tmpLinearObjectList.insertPoint(self.vertexAt - 1, newPt)
      elif self.mode == Qad_pedit_maptool_ModeEnum.ASK_FOR_MOVE_VERTEX:
         newPt = self.canvas.mapRenderer().mapToLayerCoordinates(self.layer, self.tmpPoint)
         tmpLinearObjectList = qad_utils.QadLinearObjectList()
         tmpLinearObjectList.set(self.linearObjectList)         
         tmpLinearObjectList.movePoint(self.vertexAt, newPt)
      
      if tmpLinearObjectList is not None:
         pts = tmpLinearObjectList.asPolyline(self.tolerance2ApproxCurve) 
         if self.layer.geometryType() == QGis.Polygon:
            geom = QgsGeometry.fromPolygon([pts])
         else:
            geom = QgsGeometry.fromPolyline(pts)
         self.__rubberBand.addGeometry(geom, self.layer)
      
    
   def activate(self):
      QadGetPoint.activate(self)            
      self.__rubberBand.show()          

   def deactivate(self):
      QadGetPoint.deactivate(self)
      self.__rubberBand.hide()

   def setMode(self, mode):
      self.mode = mode
      # si richiede la selezione di un'entità
      if self.mode == Qad_pedit_maptool_ModeEnum.ASK_FOR_ENTITY_SEL:
         self.setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION)
         self.onlyEditableLayers = True
         self.checkPointLayer = False
         self.checkLineLayer = True
         self.checkPolygonLayer = True
         self.setSnapType(QadSnapTypeEnum.DISABLE)
      # non si richiede niente
      elif self.mode == Qad_pedit_maptool_ModeEnum.NONE:
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)   
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # si richiede il primo punto per calcolo distanza di approssimazione
      # si richiede la posizione più vicina ad un vertice
      elif self.mode == Qad_pedit_maptool_ModeEnum.ASK_FOR_FIRST_TOLERANCE_PT:
         self.onlyEditableLayers = False
         self.checkPointLayer = True
         self.checkLineLayer = True
         self.checkPolygonLayer = True
         self.setSnapType()
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)   
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il primo punto per calcolo distanza di approssimazione si richiede il secondo punto
      # noto il primo punto per calcolo distanza di approssimazione si richiede il secondo punto
      elif self.mode == Qad_pedit_maptool_ModeEnum.FIRST_TOLERANCE_PT_KNOWN_ASK_FOR_SECOND_PT or \
           self.mode == Qad_pedit_maptool_ModeEnum.ASK_FOR_NEW_VERTEX or \
           self.mode == Qad_pedit_maptool_ModeEnum.ASK_FOR_MOVE_VERTEX:         
         self.onlyEditableLayers = False
         self.checkPointLayer = True
         self.checkLineLayer = True
         self.checkPolygonLayer = True
         self.setSnapType()
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)   
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.firstPt)
      # si richiede la posizione più vicina ad un vertice
      elif self.mode == Qad_pedit_maptool_ModeEnum.ASK_FOR_VERTEX:
         self.setSnapType(QadSnapTypeEnum.DISABLE)
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)   
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
