# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando copy
 
                              -------------------
        begin                : 2013-10-02
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
from qad_dim import *
from qad_entity import *


#===============================================================================
# Qad_copy_maptool_ModeEnum class.
#===============================================================================
class Qad_copy_maptool_ModeEnum():
   # noto niente si richiede il punto base
   NONE_KNOWN_ASK_FOR_BASE_PT = 1     
   # noto il punto base si richiede il secondo punto per la copia
   BASE_PT_KNOWN_ASK_FOR_COPY_PT = 2     

#===============================================================================
# Qad_copy_maptool class
#===============================================================================
class Qad_copy_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
                        
      self.basePt = None
      self.entitySet = QadEntitySet()
      self.seriesLen = 0
      self.adjust = False
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

   
   #============================================================================
   # move
   #============================================================================
   def move(self, f, offSetX, offSetY, layerEntitySet, entitySet, dimEntity):
      if dimEntity is None:
         # sposto la feature 
         f.setGeometry(qad_utils.moveQgsGeometry(f.geometry(), offSetX, offSetY))
         self.__highlight.addGeometry(f.geometry(), layerEntitySet.layer)
      else:
         newDimEntity = QadDimEntity(dimEntity) # la copio
         # sposto la quota
         newDimEntity.move(offSetX, offSetY)
         self.__highlight.addGeometry(newDimEntity.textualFeature.geometry(), newDimEntity.getTextualLayer())
         self.__highlight.addGeometries(newDimEntity.getLinearGeometryCollection(), newDimEntity.getLinearLayer())
         self.__highlight.addGeometries(newDimEntity.getSymbolGeometryCollection(), newDimEntity.getSymbolLayer())
   
   
   def setCopiedGeometries(self, newPt):
      self.__highlight.reset()            
      
      # copio entitySet
      entitySet = QadEntitySet(self.entitySet)
      
      for layerEntitySet in entitySet.layerEntitySetList:
         layer = layerEntitySet.layer

         transformedBasePt = self.canvas.mapSettings().mapToLayerCoordinates(layer, self.basePt)
         transformedNewPt = self.canvas.mapSettings().mapToLayerCoordinates(layer, newPt)
         offSetX = transformedNewPt.x() - transformedBasePt.x()
         offSetY = transformedNewPt.y() - transformedBasePt.y()
         entity = QadEntity()

         while len(layerEntitySet.featureIds) > 0:
            featureId = layerEntitySet.featureIds[0]
            f = layerEntitySet.getFeature(featureId)
            if f is None:
               del layerEntitySet.featureIds[0]
               continue

            # verifico se l'entità appartiene ad uno stile di quotatura
            dimEntity = QadDimStyles.getDimEntity(layer, f.id())

            if self.seriesLen > 0: # devo fare una serie              
               if self.adjust == True:
                  offSetX = offSetX / (self.seriesLen - 1)
                  offSetY = offSetY / (self.seriesLen - 1)
   
               deltaX = offSetX
               deltaY = offSetY
                  
               for i in xrange(1, self.seriesLen, 1):
                  self.move(f, deltaX, deltaY, layerEntitySet, entitySet, dimEntity)
                  deltaX = deltaX + offSetX
                  deltaY = deltaY + offSetY     
            else:
               self.move(f, offSetX, offSetY, layerEntitySet, entitySet, dimEntity)
            
            # la rimuovo da entitySet
            if dimEntity is None:
               del layerEntitySet.featureIds[0]
            else:
               dimEntitySet = dimEntity.getEntitySet()
               entitySet.subtract(dimEntitySet)
      
   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
      
      # noto il punto base si richiede il secondo punto
      if self.mode == Qad_copy_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_COPY_PT:
         self.setCopiedGeometries(self.tmpPoint)                           
         
    
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
      self.mode = mode
      # noto niente si richiede il punto base
      if self.mode == Qad_copy_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_BASE_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      # noto il punto base si richiede il secondo punto per l'angolo di rotazione
      elif self.mode == Qad_copy_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_COPY_PT:
         self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.setStartPoint(self.basePt)
