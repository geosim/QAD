# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando stretch
 
                              -------------------
        begin                : 2014-01-08
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
from qad_dim import *
import qad_stretch_fun
from qad_rubberband import QadRubberBand


#===============================================================================
# Qad_stretch_maptool_ModeEnum class.
#===============================================================================
class Qad_stretch_maptool_ModeEnum():
   # si richiede la selezione del primo punto del rettangolo per selezionare gli oggetti
   ASK_FOR_FIRST_PT_RECTANGLE = 1
   # noto niente il primo punto del rettangolo si richiede il secondo punto
   FIRST_PT_KNOWN_ASK_FOR_SECOND_PT_RECTANGLE = 2   
   # noto niente si richiede il punto base
   NONE_KNOWN_ASK_FOR_BASE_PT = 3
   # noto il punto base si richiede il secondo punto per lo spostamento
   BASE_PT_KNOWN_ASK_FOR_MOVE_PT = 4     


#===============================================================================
# Qad_stretch_maptool class
#===============================================================================
class Qad_stretch_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
                        
      self.basePt = None
      self.SSGeomList = [] # lista di entità da stirare con geom di selezione
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
   
   
   #============================================================================
   # stretch
   #============================================================================
   def stretch(self, f, containerGeom, offSetX, offSetY, tolerance2ApproxCurve, layerEntitySet, entitySet):
      # verifico se l'entità appartiene ad uno stile di quotatura
      dimEntity = self.plugIn.dimStyles.getDimEntity(layerEntitySet.layer, f.id())

      if dimEntity is None:
         # stiro la feature e la rimuovo da entitySet (é la prima)
         stretchedGeom = qad_stretch_fun.stretchQgsGeometry(f.geometry(), containerGeom, \
                                                            offSetX, offSetY, \
                                                            tolerance2ApproxCurve)
         
         if stretchedGeom is not None:
            f.setGeometry(stretchedGeom)
            self.__rubberBand.addGeometry(f.geometry(), layerEntitySet.layer)
         del layerEntitySet.featureIds[0]
      else:
         # stiro la quota e la rimuovo da entitySet
         dimEntitySet = dimEntity.getEntitySet()
         dimEntity.stretch(self.plugIn, containerGeom, offSetX, offSetY)
         self.__rubberBand.addGeometry(dimEntity.textualFeature.geometry(), dimEntity.getTextualLayer())
         self.__rubberBand.addGeometries(dimEntity.getLinearGeometryCollection(), dimEntity.getLinearLayer())
         self.__rubberBand.addGeometries(dimEntity.getSymbolGeometryCollection(), dimEntity.getSymbolLayer())
         entitySet.subtract(dimEntitySet)

   
   #============================================================================
   # addStretchedGeometries
   #============================================================================
   def addStretchedGeometries(self, newPt):
      self.__rubberBand.reset()            

      for SSGeom in self.SSGeomList:
         # copio entitySet
         entitySet = QadEntitySet(SSGeom[0])
         geomSel = SSGeom[1]

         for layerEntitySet in entitySet.layerEntitySetList:
            layer = layerEntitySet.layer

            tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                        self.canvas,\
                                                                        layer)                              

            g = QgsGeometry(geomSel)
            if self.plugIn.canvas.mapRenderer().destinationCrs() != layer.crs():                     
               # Trasformo la geometria nel sistema di coordinate del layer
               coordTransform = QgsCoordinateTransform(self.canvas.mapRenderer().destinationCrs(), \
                                                       layer.crs())          
               g.transform(coordTransform)

               transformedBasePt = self.canvas.mapRenderer().mapToLayerCoordinates(layer, self.basePt)
               transformedNewPt = self.canvas.mapRenderer().mapToLayerCoordinates(layer, newPt)
               offSetX = transformedNewPt.x() - transformedBasePt.x()
               offSetY = transformedNewPt.y() - transformedBasePt.y()
            else:
               offSetX = newPt.x() - self.basePt.x()
               offSetY = newPt.y() - self.basePt.y()

            while len(layerEntitySet.featureIds) > 0:
               featureId = layerEntitySet.featureIds[0]
               f = layerEntitySet.getFeature(featureId)        
               self.stretch(f, g, offSetX, offSetY, tolerance2ApproxCurve, layerEntitySet, entitySet)
            
      
   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
                     
      # noto il punto base si richiede il secondo punto per l'angolo di rotazione
      if self.mode == Qad_stretch_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_MOVE_PT:
         self.addStretchedGeometries(self.tmpPoint)                           
         
    
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
   
      # si richiede la selezione del primo punto del rettangolo per selezionare gli oggetti
      if self.mode == Qad_stretch_maptool_ModeEnum.ASK_FOR_FIRST_PT_RECTANGLE:
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)         
      # noto niente il primo punto del rettangolo si richiede il secondo punto
      elif self.mode == Qad_stretch_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT_RECTANGLE:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_RECTANGLE)                
      # noto niente si richiede il punto base
      elif self.mode == Qad_stretch_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_BASE_PT:
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il punto base si richiede il secondo punto
      elif self.mode == Qad_stretch_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_MOVE_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.basePt)




#===============================================================================
# Qad_gripStretch_maptool class
#===============================================================================
class Qad_gripStretch_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
                        
      self.basePt = None
      self.selectedEntityGripPoints = [] # lista in cui ogni elemento è una entità + una lista di punti da stirare
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


   #============================================================================
   # getSelectedEntityGripPointNdx
   #============================================================================
   def getSelectedEntityGripPointNdx(self, entity):
      # lista delle entityGripPoint con dei grip point selezionati
      # cerca la posizione di un'entità nella lista in cui ogni elemento è una entità + una lista di punti da stirare
      i = 0
      tot = len(self.selectedEntityGripPoints)
      while i < tot:
         selectedEntityGripPoint = self.selectedEntityGripPoints[i]
         if selectedEntityGripPoint[0] == entity:
            return i
         i = i + 1
      return -1
   
   
   #============================================================================
   # stretch
   #============================================================================
   def stretch(self, entity, ptList, offSetX, offSetY, tolerance2ApproxCurve):
      # entity = entità da stirare
      # ptList = lista dei punti da stirare
      # offSetX, offSetY = spostamento da fare
      # tolerance2ApproxCurve = tolleranza per ricreare le curve
      # entitySet = gruppo di selezione delle entità da stirare
      # verifico se l'entità appartiene ad uno stile di quotatura
      if entity.whatIs() == "ENTITY":
         transformedBasePt = self.canvas.mapRenderer().mapToLayerCoordinates(entity.layer, self.basePt)
         # stiro la feature 
         stretchedGeom = qad_stretch_fun.gripStretchQgsGeometry(entity.getGeometry(), self.basePt, ptList, \
                                                      offSetX, offSetY, \
                                                      tolerance2ApproxCurve)
         
         if stretchedGeom is not None:
            self.__rubberBand.addGeometry(stretchedGeom, entity.layer)
      elif entity.whatIs() == "DIMENTITY":
         # stiro la quota
         dimEntity.stretch(self.plugIn, ptList, offSetX, offSetY)
         self.__rubberBand.addGeometry(dimEntity.textualFeature.geometry(), dimEntity.getTextualLayer())
         self.__rubberBand.addGeometries(dimEntity.getLinearGeometryCollection(), dimEntity.getLinearLayer())
         self.__rubberBand.addGeometries(dimEntity.getSymbolGeometryCollection(), dimEntity.getSymbolLayer())

   
   #============================================================================
   # addStretchedGeometries
   #============================================================================
   def addStretchedGeometries(self, newPt):
      self.__rubberBand.reset()            

      dimElaboratedList = [] # lista delle quotature già elaborate

      for selectedEntity in self.selectedEntityGripPoints:
         entity = selectedEntity[0]
         ptList = selectedEntity[1]
         layer = entity.layer

         tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                     self.canvas,\
                                                                     layer)                              

         if self.plugIn.canvas.mapRenderer().destinationCrs() != layer.crs():                     
            transformedBasePt = self.canvas.mapRenderer().mapToLayerCoordinates(layer, self.basePt)
            transformedNewPt = self.canvas.mapRenderer().mapToLayerCoordinates(layer, newPt)
            offSetX = transformedNewPt.x() - transformedBasePt.x()
            offSetY = transformedNewPt.y() - transformedBasePt.y()
         else:
            offSetX = newPt.x() - self.basePt.x()
            offSetY = newPt.y() - self.basePt.y()

         # verifico se l'entità appartiene ad uno stile di quotatura
         dimEntity = self.plugIn.dimStyles.getDimEntity(entity.layer, entity.featureId)  
         if dimEntity is None:                        
            self.stretch(entity, ptList, offSetX, offSetY, tolerance2ApproxCurve)
         else:
            found = False
            for dimElaborated in dimElaboratedList:
               if dimElaborated == dimEntity:
                  found = True
            if found == False: # quota non ancora elaborata
               dimEntitySet = dimEntity.getEntitySet()
               # creo un'unica lista contenente i grip points di tutti i componenti della quota
               dimPtlist = []
               for dimComponent in dimEntitySet:
                  i = self.getSelectedEntityGripPointNdx(dimComponent)
                  if i >= 0:
                     dimPtlist.extend(self.selectedEntityGripPoints[i][1])

               dimElaboratedList.append(dimEntity)
               self.stretch(dimEntity, dimPtlist, offSetX, offSetY, tolerance2ApproxCurve)
            
      
   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
                     
      # noto il punto base si richiede il secondo punto per l'angolo di rotazione
      if self.mode == Qad_stretch_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_MOVE_PT:
         self.addStretchedGeometries(self.tmpPoint)                           
         
    
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
   
      # noto niente si richiede il punto base
      if self.mode == Qad_stretch_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_BASE_PT:
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
         self.__rubberBand.reset()            
      # noto il punto base si richiede il secondo punto
      elif self.mode == Qad_stretch_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_MOVE_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.basePt)
