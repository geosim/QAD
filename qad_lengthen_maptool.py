# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando lengthen
 
                              -------------------
        begin                : 2015-10-06
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
# Qad_lengthen_maptool_ModeEnum class.
#===============================================================================
class Qad_lengthen_maptool_ModeEnum():
   # si richiede la selezione dell'oggetto da misurare
   ASK_FOR_OBJ_TO_MISURE = 1
   # si richiede il delta
   ASK_FOR_DELTA = 2
   # non si richiede niente
   NONE = 3
   # si richiede la selezione dell'oggetto da allungare
   ASK_FOR_OBJ_TO_LENGTHEN = 4
   # si richiede la percentuale 
   ASK_FOR_PERCENT = 5
   # si richiede il totale
   ASK_FOR_TOTAL = 6
   # si richiede il nuovo punto dell'estremità in modalità dinamica
   ASK_FOR_DYNAMIC_POINT = 7

#===============================================================================
# Qad_lengthen_maptool class
#===============================================================================
class Qad_lengthen_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)

      self.OpMode = None # "DElta" o "Percent" o "Total" o "DYnamic"
      self.OpType = None # "length" o "Angle"
      self.value = None
      self.tmpLinearObjectList = None

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

   def setInfo(self, entity, point):
      # setta: self.layer, self.tmpLinearObjectList e self.move_startPt

      if self.tmpLinearObjectList is not None:
         del self.tmpLinearObjectList
         self.tmpLinearObjectList = None
      
      if entity.isInitialized() == False:
         return False
         
      self.layer = entity.layer
      transformedPt = self.canvas.mapSettings().mapToLayerCoordinates(self.layer, point)
      geom = entity.getGeometry()
                  
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      dummy = qad_utils.closestSegmentWithContext(transformedPt, geom)
      if dummy[2] is None:
         return False
      # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
      subGeom, atSubGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])               
      self.tmpLinearObjectList = qad_utils.QadLinearObjectList()               
      self.tmpLinearObjectList.fromPolyline(subGeom.asPolyline())
      
      if qad_utils.getDistance(self.tmpLinearObjectList.getStartPt(), transformedPt) <= \
         qad_utils.getDistance(self.tmpLinearObjectList.getEndPt(), transformedPt):
         # si allunga/accorcia dal punto iniziale                 
         self.move_startPt = True
      else:
         # si allunga dal punto finale
         self.move_startPt = False
      return True


   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
      
      self.__rubberBand.reset()
      res = False
       
      # si richiede la selezione dell'oggetto da allungare
      if self.mode == Qad_lengthen_maptool_ModeEnum.ASK_FOR_OBJ_TO_LENGTHEN:
         if self.tmpEntity.isInitialized():
            if self.setInfo(self.tmpEntity, self.tmpPoint) == False:
               return

            if self.OpMode == "DElta":
               newTmpLinearObjectList = qad_utils.QadLinearObjectList(self.tmpLinearObjectList)
               if self.OpType == "length":
                  res = newTmpLinearObjectList.lengthen_delta(self.move_startPt, self.value)
               elif self.OpType == "Angle":
                  res = newTmpLinearObjectList.lengthen_deltaAngle(self.move_startPt, self.value)
            elif self.OpMode == "Percent":
               newTmpLinearObjectList = qad_utils.QadLinearObjectList(self.tmpLinearObjectList)
               value = newTmpLinearObjectList.length() * self.value / 100
               value = value - newTmpLinearObjectList.length()
               res = newTmpLinearObjectList.lengthen_delta(self.move_startPt, value)
            elif self.OpMode == "Total":
               newTmpLinearObjectList = qad_utils.QadLinearObjectList(self.tmpLinearObjectList)
               if self.OpType == "length":
                  value = self.value - self.tmpLinearObjectList.length()
                  res = newTmpLinearObjectList.lengthen_delta(self.move_startPt, value)
               elif self.OpType == "Angle":                     
                  if newTmpLinearObjectList.qty() == 1:
                     linearObject = newTmpLinearObjectList.getLinearObjectAt(0)
                     if linearObject.isArc() == True: # se è un arco
                        value = self.value - linearObject.getArc().totalAngle()
                        res = newTmpLinearObjectList.lengthen_deltaAngle(self.move_startPt, value)
               
      # si richiede un punto per la nuova estremità
      elif self.mode == Qad_lengthen_maptool_ModeEnum.ASK_FOR_DYNAMIC_POINT:
         newTmpLinearObjectList = qad_utils.QadLinearObjectList(self.tmpLinearObjectList)
         transformedPt = self.canvas.mapSettings().mapToLayerCoordinates(self.layer, self.tmpPoint)
         
         if self.move_startPt:
            linearObject = newTmpLinearObjectList.getLinearObjectAt(0)
         else:
            linearObject = newTmpLinearObjectList.getLinearObjectAt(-1)
            
         if linearObject.isSegment():
            newPt = qad_utils.getPerpendicularPointOnInfinityLine(linearObject.getStartPt(), linearObject.getEndPt(), transformedPt)
         else: # arco
            newPt = qad_utils.getPolarPointByPtAngle(linearObject.getArc().center, \
                                                     qad_utils.getAngleBy2Pts(linearObject.getArc().center, transformedPt), \
                                                     linearObject.getArc().radius)                  

         if newTmpLinearObjectList.qty() > 1 and linearObject.isSegment():
            ang = linearObject.getTanDirectionOnStartPt()

         if self.move_startPt:
            linearObject.setStartPt(newPt)
         else:
            linearObject.setEndPt(newPt)

         if newTmpLinearObjectList.qty() > 1 and linearObject.isSegment() and \
            qad_utils.TanDirectionNear(ang, linearObject.getTanDirectionOnStartPt()) == False:
            res = False
         else:
            res = True
      
      if res == False: # allungamento impossibile
         return
      pts = newTmpLinearObjectList.asPolyline()
      geom = QgsGeometry.fromPolyline(pts)
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

      # si richiede la selezione dell'oggetto da misurare
      if self.mode == Qad_lengthen_maptool_ModeEnum.ASK_FOR_OBJ_TO_MISURE:
         self.setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION)

         # solo layer di tipo lineari che non appartengano a quote o di tipo poligono 
         layerList = []
         for layer in qad_utils.getVisibleVectorLayers(self.plugIn.canvas): # Tutti i layer vettoriali visibili
            if layer.geometryType() == QGis.Line or layer.geometryType() == QGis.Polygon:
               if len(QadDimStyles.getDimListByLayer(layer)) == 0:
                  layerList.append(layer)
         
         self.layersToCheck = layerList
         self.onlyEditableLayers = False
         self.setSnapType(QadSnapTypeEnum.DISABLE)
      # si richiede il delta
      elif self.mode == Qad_lengthen_maptool_ModeEnum.ASK_FOR_DELTA:
         self.OpMode = "DElta"
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
      # non si richiede niente
      elif self.mode == Qad_lengthen_maptool_ModeEnum.NONE:
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)   
      # si richiede la selezione dell'oggetto da allungare
      elif self.mode == Qad_lengthen_maptool_ModeEnum.ASK_FOR_OBJ_TO_LENGTHEN:
         self.setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION_DYNAMIC)

         # solo layer lineari editabili che non appartengano a quote
         layerList = []
         for layer in qad_utils.getVisibleVectorLayers(self.plugIn.canvas): # Tutti i layer vettoriali visibili
            if layer.geometryType() == QGis.Line and layer.isEditable():
               if len(QadDimStyles.getDimListByLayer(layer)) == 0:
                  layerList.append(layer)
         
         self.layersToCheck = layerList
         self.onlyEditableLayers = True
         self.setSnapType(QadSnapTypeEnum.DISABLE)
      # si richiede la percentuale
      elif self.mode == Qad_lengthen_maptool_ModeEnum.ASK_FOR_PERCENT:
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION) 
         self.OpMode = "Percent"
      # si richiede il totale
      elif self.mode == Qad_lengthen_maptool_ModeEnum.ASK_FOR_TOTAL:
         self.OpMode = "Total"
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
      # si richiede il nuovo punto dell'estremità in modalità dinamica
      elif self.mode == Qad_lengthen_maptool_ModeEnum.ASK_FOR_DYNAMIC_POINT:
         self.OpMode = "DYnamic"
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
