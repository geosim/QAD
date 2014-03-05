# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando stretch
 
                              -------------------
        begin                : 2014-01-08
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
   
   def addStretchedGeometries(self, newPt):
      self.__rubberBand.reset()            

      for SSGeom in self.SSGeomList:
         entitySet = SSGeom[0]
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
                              
            geoms = layerEntitySet.getGeometryCollection()
            
            for geom in geoms:
               stretchedGeom = qad_utils.stretchQgsGeometry(geom, g, \
                                                            offSetX, offSetY, \
                                                            tolerance2ApproxCurve)
               if stretchedGeom is not None:       
                  self.__rubberBand.addGeometry(stretchedGeom, layer)
            
      
   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
                     
      # noto il punto base si richiede il secondo punto per l'angolo di rotazione
      if self.mode == Qad_stretch_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_MOVE_PT:
         self.addStretchedGeometries(self.tmpPoint)                           
         
    
   def activate(self):
      QadGetPoint.activate(self)            
      self.__rubberBand.show()          

   def deactivate(self):
      QadGetPoint.deactivate(self)
      self.__rubberBand.hide()

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
