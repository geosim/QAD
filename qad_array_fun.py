# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 funzioni per fare serie di oggetti grafici
 
                              -------------------
        begin                : 2016-05-26
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


# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import qgis.utils


import qad_utils
import qad_arc
import qad_circle
from qad_snapper import *
import qad_layer
from qad_highlight import QadHighlight
from qad_entity import *
from qad_dim import *
import qad_label


#===============================================================================
# doMoveAndRotateGeom
#===============================================================================
def doMoveAndRotateGeom(plugIn, f, g, layer, offSetX, offSetY, angle, rotFldName, basePt, coordTransform, addToLayer, highlightObj):
   # funzione di ausilio
   newGeom = qad_utils.moveQgsGeometry(g, offSetX, offSetY)
   if angle is not None:
      newGeom = qad_utils.rotateQgsGeometry(newGeom, basePt, angle)

   newGeom.transform(coordTransform)

   if addToLayer:
      newF = QgsFeature(f) # la copio perchè altrimenti qgis si incarta
      newF.setGeometry(newGeom)
      
      if len(rotFldName) > 0:
         rotValue = newF.attribute(rotFldName)
         # a volte vale None e a volte null (vai a capire...)
         rotValue = 0 if rotValue is None or isinstance(rotValue, QPyNullVariant) else qad_utils.toRadians(rotValue) # la rotazione é in gradi nel campo della feature
         rotValue = rotValue + angle
         newF.setAttribute(rotFldName, qad_utils.toDegrees(qad_utils.normalizeAngle(rotValue)))               
      
      # plugIn, layer, feature, coordTransform, refresh, check_validity
      if qad_layer.addFeatureToLayer(plugIn, layer, newF, None, False, False) == False:
         return False

   if highlightObj is not None:
      highlightObj.addGeometry(newGeom, layer)
   
   del newGeom
   
   return True
   
   
#===============================================================================
# doMoveAndRotateDimEntity
#===============================================================================
def doMoveAndRotateDimEntity(plugIn, dimEntity, offSetX, offSetY, angle, basePt, addToLayer, highlightObj):
   # funzione di ausilio
   newDimEntity = QadDimEntity(dimEntity)
   newDimEntity.move(offSetX, offSetY)
   if angle is not None:
      newDimEntity.rotate(basePt, angle)
   
   if addToLayer:
      if newDimEntity.addToLayers(plugIn) == False:
         return False             

   if highlightObj is not None:
      highlightObj.addGeometry(newDimEntity.textualFeature.geometry(), newDimEntity.getTextualLayer())
      highlightObj.addGeometries(newDimEntity.getLinearGeometryCollection(), newDimEntity.getLinearLayer())
      highlightObj.addGeometries(newDimEntity.getSymbolGeometryCollection(), newDimEntity.getSymbolLayer())
   
   del newDimEntity
   
   return True


#===============================================================================
# arrayRectangleEntity
#===============================================================================
def arrayRectangleEntity(plugIn, ent, basePt, rows, cols, distanceBetweenRows, distanceBetweenCols, angle, itemsRotation,
                         addToLayer, highlightObj):
   """
   serie rettangolare
   ent = entità QAD di cui fare la serie (QadEntity o QadDimEntity)
   basePt = punto base in map coordinate (QgsPoint)
   rows = numero di righe
   cols = numero di colonne
   distanceBetweenRows = distanza tra le righe in map coordinate
   distanceBetweenCols = distanza tra le colonne in map coordinate
   angle = angolo della serie (radianti)
   itemsRotation = True se si vuole ruotare gli elementi come l'angolo della serie
   addToLayer = se è True aggiunge le nuove entità al layer
   highlightObj = se è diverso da None vengono aggiunge le geometrie all'oggetto QadHighlight
                
   la funzione restituisce True in caso di successo e Falso in caso di errore
   """

   g = None
   coordTransform = None
   f = None
   if ent.whatIs() == "ENTITY":
      f = ent.getFeature()
      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      CRS = qgis.utils.iface.mapCanvas().mapSettings().destinationCrs() # CRS corrente
      coordTransform = QgsCoordinateTransform(ent.crs(), CRS)
      g = f.geometry()
      g.transform(coordTransform)
      coordTransform = QgsCoordinateTransform(CRS, ent.crs())
   
      rotFldName = ""
      if ent.getEntityType() == QadEntityGeomTypeEnum.TEXT:
         # se la rotazione dipende da un solo campo
         rotFldNames = qad_label.get_labelRotationFieldNames(ent.layer)
         if len(rotFldNames) == 1 and len(rotFldNames[0]) > 0:
            rotFldName = rotFldNames[0]         
      elif ent.getEntityType() == QadEntityGeomTypeEnum.SYMBOL:
         rotFldName = qad_layer.get_symbolRotationFieldName(ent.layer)
   
   for row in range(0, rows):
      firstBasePt = qad_utils.getPolarPointByPtAngle(basePt, angle + math.pi / 2, distanceBetweenRows * row)
      distX = 0
      for col in range(0, cols):
         newBasePt = qad_utils.getPolarPointByPtAngle(firstBasePt, angle, distanceBetweenCols * col)
         offSetX = newBasePt.x() - basePt.x()
         offSetY = newBasePt.y() - basePt.y()
         
         if g is not None: # se l'entità non è una quotatura
            if doMoveAndRotateGeom(plugIn, f, g, ent.layer, offSetX, offSetY, \
                                   angle if itemsRotation else None, rotFldName, \
                                   newBasePt, coordTransform, addToLayer, highlightObj) == False:
               return False
         else: # se l'entità è una quotatura
            if doMoveAndRotateDimEntity(plugIn, ent, offSetX, offSetY, \
                                        angle if itemsRotation else None, \
                                        newBasePt, addToLayer, highlightObj) == False:
               return False

         distX = distX + distanceBetweenCols

   return True


#===============================================================================
# arrayPathEntity
#===============================================================================
def arrayPathEntity(plugIn, ent, basePt, rows, cols, distanceBetweenRows, distanceBetweenCols, tangentDirection, itemsRotation, \
                    pathLinearObjectList, distanceFromStartPt, addToLayer, highlightObj):
   """
   serie traiettoria
   ent = entità QAD di cui fare la serie (QadEntity o QadDimEntity)
   basePt = punto base in map coordinate (QgsPoint)
   rows = numero di righe
   cols = numero di colonne
   distanceBetweenRows = distanza tra le righe in map coordinate
   distanceBetweenCols = distanza tra le colonne in map coordinate
   tangentDirection = specifica il modo in cui gli elementi disposti in serie sono allineati rispetto alla direzione iniziale della traiettoria 
   itemsRotation = True se si vuole ruotare gli elementi come l'angolo della serie
   pathLinearObjectList = traiettoria da seguire (QadLinearObjectList) in map coordinate
   distanceFromStartPt = distanza dal punto iniziale della traccia
   addToLayer = se è True aggiunge le nuove entità al layer
   highlightObj = se è diverso da None vengono aggiunge le geometrie all'oggetto QadHighlight
   
   la funzione restituisce True in caso di successo e Falso in caso di errore
   """
   g = None
   coordTransform = None
   f = None
   if ent.whatIs() == "ENTITY":
      f = ent.getFeature()
      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      CRS = qgis.utils.iface.mapCanvas().mapSettings().destinationCrs() # CRS corrente
      coordTransform = QgsCoordinateTransform(ent.crs(), CRS)
      g = f.geometry()
      g.transform(coordTransform)
      coordTransform = QgsCoordinateTransform(CRS, ent.crs())

      rotFldName = ""
      if ent.getEntityType() == QadEntityGeomTypeEnum.TEXT:
         # se la rotazione dipende da un solo campo
         rotFldNames = qad_label.get_labelRotationFieldNames(ent.layer)
         if len(rotFldNames) == 1 and len(rotFldNames[0]) > 0:
            rotFldName = rotFldNames[0]         
      elif ent.getEntityType() == QadEntityGeomTypeEnum.SYMBOL:
         rotFldName = qad_layer.get_symbolRotationFieldName(ent.layer)

   firstBasePt = basePt
   firstTanDirection = pathLinearObjectList.getTanDirectionOnStartPt()
   for col in range(0, cols):
      distX = (distanceBetweenCols * col) + distanceFromStartPt
      firstBasePt, angle = pathLinearObjectList.getPointFromStart(distX) # ritorna il punto e la direzione della tang in quel punto
      if firstBasePt is not None:
         for row in range(0, rows):
            newBasePt = qad_utils.getPolarPointByPtAngle(firstBasePt, angle + math.pi/2, distanceBetweenRows * row)
            offSetX = newBasePt.x() - basePt.x()
            offSetY = newBasePt.y() - basePt.y()
            
            if g is not None: # se l'entità non è una quotatura
               if doMoveAndRotateGeom(plugIn, f, g, ent.layer, offSetX, offSetY, \
                                      angle - tangentDirection if itemsRotation else -tangentDirection, rotFldName, \
                                      newBasePt, coordTransform, addToLayer, highlightObj) == False:
                  return False
            else: # se l'entità è una quotatura
               if doMoveAndRotateDimEntity(plugIn, ent, offSetX, offSetY, \
                                           angle - tangentDirection if itemsRotation else -tangentDirection, \
                                           newBasePt, addToLayer, highlightObj) == False:
                  return False
      
      distX = distX + distanceBetweenCols
         

   return True


#===============================================================================
# arrayPolarEntity
#===============================================================================
def arrayPolarEntity(plugIn, ent, basePt, centerPt, itemsNumber, angleBetween, rows, distanceBetweenRows, itemsRotation, \
                     addToLayer, highlightObj):
   """
   serie polare
   ent = entità QAD di cui fare la serie (QadEntity o QadDimEntity)
   basePt = punto base in map coordinate (QgsPoint)
   centerPt = punto centrale in map coordinate (QgsPoint)
   itemsNumber = numero di copie da fare
   angleBetween = angolo tra un elemento e l'altro (radianti)
   rows = numero di righe
   distanceBetweenRows = distanza tra le righe in map coordinate
   itemsRotation = True se si vuole ruotare gli elementi intorno al cerchio
   addToLayer = se è True aggiunge le nuove entità al layer
   highlightObj = se è diverso da None vengono aggiunge le geometrie all'oggetto QadHighlight
   """
   g = None
   coordTransform = None
   f = None
   if ent.whatIs() == "ENTITY":
      f = ent.getFeature()
      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      CRS = qgis.utils.iface.mapCanvas().mapSettings().destinationCrs() # CRS corrente
      coordTransform = QgsCoordinateTransform(ent.crs(), CRS)
      g = f.geometry()
      g.transform(coordTransform)
      coordTransform = QgsCoordinateTransform(CRS, ent.crs())

      rotFldName = ""
      if ent.getEntityType() == QadEntityGeomTypeEnum.TEXT:
         # se la rotazione dipende da un solo campo
         rotFldNames = qad_label.get_labelRotationFieldNames(ent.layer)
         if len(rotFldNames) == 1 and len(rotFldNames[0]) > 0:
            rotFldName = rotFldNames[0]         
      elif ent.getEntityType() == QadEntityGeomTypeEnum.SYMBOL:
         rotFldName = qad_layer.get_symbolRotationFieldName(ent.layer)

   firstAngle = qad_utils.getAngleBy2Pts(centerPt, basePt)
   dist = qad_utils.getDistance(centerPt, basePt)
   for row in range(0, rows):
      angle = firstAngle
      for i in range(0, itemsNumber):
         newBasePt = qad_utils.getPolarPointByPtAngle(centerPt, angle, dist)
         offSetX = newBasePt.x() - basePt.x()
         offSetY = newBasePt.y() - basePt.y()
      
         if g is not None: # se l'entità non è una quotatura
            if doMoveAndRotateGeom(plugIn, f, g, ent.layer, offSetX, offSetY, \
                                   i * angleBetween if itemsRotation else None, rotFldName, \
                                   newBasePt, coordTransform, addToLayer, highlightObj) == False:
               return False
         else: # se l'entità è una quotatura
            if doMoveAndRotateDimEntity(plugIn, ent, offSetX, offSetY, \
                                        i * angleBetween if itemsRotation else None, \
                                        newBasePt, addToLayer, highlightObj) == False:
               return False
         angle = angle + angleBetween 

      dist = dist + distanceBetweenRows

   return True
                 
                 
