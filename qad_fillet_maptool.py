# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando fillet
 
                              -------------------
        begin                : 2014-01-31
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
from qad_variables import *
from qad_getpoint import *
from qad_rubberband import QadRubberBand
from qad_dim import QadDimStyles


#===============================================================================
# Qad_fillet_maptool_ModeEnum class.
#===============================================================================
class Qad_fillet_maptool_ModeEnum():
   # si richiede la selezione del primo oggetto
   ASK_FOR_FIRST_LINESTRING = 1     
   # si richiede la selezione del secondo oggetto
   ASK_FOR_SECOND_LINESTRING = 2    
   # non si richiede niente
   NONE = 3
   # si richiede la selezione della polilinea
   ASK_FOR_POLYLINE = 4     


#===============================================================================
# Qad_fillet_maptool class
#===============================================================================
class Qad_fillet_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)

      self.filletMode = 1 # modalità di raccordo; 1=Taglia-estendi, 2=Non taglia-estendi
      self.radius = 0.0
      
      self.layer = None 
      self.linearObjectList = qad_utils.QadLinearObjectList()
      self.partAt1 = 0
      self.vertexAt1 = 0
                       
      self.tolerance2ApproxCurve = None

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

   def setEntityInfo(self, layer, featureId, linearObjectList, partAt, pointAt):
      """
      Setta self.entity, self.atSubGeom, self.linearObjectList, self.partAt, self.pointAt
      di primo o del secondo oggetto da raccordare (vedi <firstObj>)
      """
      self.layer = layer
      self.featureId = featureId
      self.linearObjectList.set(linearObjectList)
      self.partAt = partAt
      self.pointAt = pointAt

      self.tolerance2ApproxCurve = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))

   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
      
      self.__rubberBand.reset()
      tmpLinearObjectList = None
       
      # si richiede la selezione del secondo oggetto
      if self.mode == Qad_fillet_maptool_ModeEnum.ASK_FOR_SECOND_LINESTRING:
         if self.tmpEntity.isInitialized():
            # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
            geom = self.layerToMapCoordinates(self.tmpEntity.layer, self.tmpEntity.getGeometry())
            
            # ritorna una tupla (<The squared cartesian distance>,
            #                    <minDistPoint>
            #                    <afterVertex>
            #                    <leftOf>)
            dummy = qad_utils.closestSegmentWithContext(self.tmpPoint, geom)
            if dummy[2] is not None:
               # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
               subGeom, atSubGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])               
               tmpLinearObjectList = qad_utils.QadLinearObjectList()               
               tmpLinearObjectList.fromPolyline(subGeom.asPolyline())
               
               # la funzione ritorna una lista con (<minima distanza al quadrato>,
               #                                    <punto più vicino>
               #                                    <indice della parte più vicina>       
               #                                    <"a sinistra di">)
               dummy = tmpLinearObjectList.closestPartWithContext(self.tmpPoint)
               tmpPartAt = dummy[2]
               tmpPointAt = dummy[1]
               
               # stessa entità e stessa parte
               if self.layer.id() == self.tmpEntity.layer.id() and \
                  self.featureId == self.tmpEntity.featureId and \
                  self.partAt == tmpPartAt:
                  return

               # uso il crs del canvas per lavorare con coordinate piane xy
               epsg = self.canvas.mapSettings().destinationCrs().authid()
               
               if self.tmpShiftKey == True: # tasto shift premuto durante il movimento del mouse
                  # filletMode = 1 # modalità di raccordo; 1=Taglia-estendi
                  # raggio = 0
                  res = qad_utils.getFilletLinearObjectList(self.linearObjectList, self.partAt, self.pointAt, \
                                                            tmpLinearObjectList, tmpPartAt, tmpPointAt,\
                                                            1, 0, epsg)
               else:               
                  res = qad_utils.getFilletLinearObjectList(self.linearObjectList, self.partAt, self.pointAt, \
                                                            tmpLinearObjectList, tmpPartAt, tmpPointAt,\
                                                            self.filletMode, self.radius, epsg)
               if res is None: # raccordo non possibile
                  return
               tmpLinearObjectList = res[0]
                        
      # si richiede la selezione della polilinea
      elif self.mode == Qad_fillet_maptool_ModeEnum.ASK_FOR_POLYLINE:
         if self.tmpEntity.isInitialized():
            # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
            geom = self.layerToMapCoordinates(self.tmpEntity.layer, self.tmpEntity.getGeometry())
            # ritorna una tupla (<The squared cartesian distance>,
            #                    <minDistPoint>
            #                    <afterVertex>
            #                    <leftOf>)
            dummy = qad_utils.closestSegmentWithContext(self.tmpPoint, geom)
            if dummy[2] is not None:
               # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
               subGeom, atSubGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])               
               tmpLinearObjectList = qad_utils.QadLinearObjectList()
               tmpLinearObjectList.fromPolyline(subGeom.asPolyline())
               tmpLinearObjectList.fillet(self.radius)
      
      if tmpLinearObjectList is not None:
         pts = tmpLinearObjectList.asPolyline(self.tolerance2ApproxCurve)
         if self.layer.geometryType() == QGis.Polygon:
            geom = QgsGeometry.fromPolygon([pts])
         else:
            geom = QgsGeometry.fromPolyline(pts)
            
         # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
         geom = self.layerToMapCoordinates(self.layer, geom)            
         self.__rubberBand.addGeometry(geom, self.layer)
      
    
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

      # si richiede la selezione del primo oggetto
      # si richiede la selezione del secondo oggetto
      if self.mode == Qad_fillet_maptool_ModeEnum.ASK_FOR_FIRST_LINESTRING or \
         self.mode == Qad_fillet_maptool_ModeEnum.ASK_FOR_SECOND_LINESTRING:
         
         if self.mode == Qad_fillet_maptool_ModeEnum.ASK_FOR_FIRST_LINESTRING:
            self.setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION)
         else:
            self.setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION_DYNAMIC)

         # solo layer lineari editabili che non appartengano a quote
         layerList = []
         for layer in qad_utils.getVisibleVectorLayers(self.plugIn.canvas): # Tutti i layer vettoriali visibili
            if layer.geometryType() == QGis.Line and layer.isEditable():
               if len(QadDimStyles.getDimListByLayer(layer)) == 0:
                  layerList.append(layer)
         
         self.layersToCheck = layerList
         self.setSnapType(QadSnapTypeEnum.DISABLE)
      # non si richiede niente
      elif self.mode == Qad_fillet_maptool_ModeEnum.NONE:
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)   
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # si richiede la selezione della polilinea
      elif self.mode == Qad_fillet_maptool_ModeEnum.ASK_FOR_POLYLINE:
         self.setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION_DYNAMIC)

         # solo layer lineari o poligono editabili che non appartengano a quote
         layerList = []
         for layer in qad_utils.getVisibleVectorLayers(self.plugIn.canvas): # Tutti i layer vettoriali visibili
            if (layer.geometryType() == QGis.Line or layer.geometryType() == QGis.Polygon) and \
               layer.isEditable():
               if len(QadDimStyles.getDimListByLayer(layer)) == 0:
                  layerList.append(layer)
         
         self.layersToCheck = layerList
         self.setSnapType(QadSnapTypeEnum.DISABLE)
