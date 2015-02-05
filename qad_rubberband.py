# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 Classe per gestire rubber band di oggetti geometricamente non omogenei
 
                              -------------------
        begin                : 2013-12-12
        copyright            : (C) 2013 IREN Acqua Gas SpA
        email                : geosim.dev@gruppoiren.it
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


from qad_entity import *


#===============================================================================
# createRubberBand
#===============================================================================
def createRubberBand(mapCanvas, geometryType = QGis.Line, alternativeBand = False):
   """
   la funzione crea un rubber band di tipo <geometryType> con le impostazioni di QGIS.
   Se <alternativeBand> = True, il rubber band sarà impostato con più trasparenza e tipolinea punteggiato   
   """
   settings = QSettings()
   width = int(settings.value( "/qgis/digitizing/line_width", 1))
   color = QColor(int(settings.value( "/qgis/digitizing/line_color_red", 1)), \
                  int(settings.value( "/qgis/digitizing/line_color_green", 1)), \
                  int(settings.value( "/qgis/digitizing/line_color_blue", 1)))
   alpha = float(int(settings.value( "/qgis/digitizing/line_color_alpha", 200)) / 255.0)

   rb = QgsRubberBand(mapCanvas, geometryType)
   
   if alternativeBand:
      alpha = alpha * float(settings.value( "/qgis/digitizing/line_color_alpha_scale", 0.75))
      rb.setLineStyle(Qt.DotLine)
 
   if geometryType == QGis.Polygon:
      color.setAlphaF(alpha)

   color.setAlphaF(alpha)
   rb.setColor(color)
   rb.setWidth(width)
   return rb


# Classe che gestisce rubber band di oggetti geometricamente non omogenei
class QadRubberBand():
   def __init__(self, mapCanvas, alternativeBand = False):
      """
      Se <alternativeBand> = True, il rubber band sarà impostato con più trasparenza e tipolinea punteggiato   
      """
      self.mapCanvas = mapCanvas
      self.__rubberBandPoint = createRubberBand(self.mapCanvas, QGis.Point, alternativeBand)
      self.__rubberBandLine = createRubberBand(self.mapCanvas, QGis.Line, alternativeBand)
      self.__rubberBandPolygon = createRubberBand(self.mapCanvas, QGis.Polygon, alternativeBand)

   def __del__(self):
      self.hide()
      
      self.mapCanvas.scene().removeItem(self.__rubberBandPoint)
      del self.__rubberBandPoint
      
      self.mapCanvas.scene().removeItem(self.__rubberBandLine)
      del self.__rubberBandLine
      
      self.mapCanvas.scene().removeItem(self.__rubberBandPolygon)
      del self.__rubberBandPolygon         
   
   def hide(self):
      self.__rubberBandPoint.hide()
      self.__rubberBandLine.hide()
      self.__rubberBandPolygon.hide()         

   def show(self):
      self.__rubberBandPoint.show()
      self.__rubberBandLine.show()
      self.__rubberBandPolygon.show()
      
   def addGeometry(self, geom, layer):
      # uso la geometria del layer per risolvere il caso ambiguo in cui
      # si vuole inserire una linea chiusa in un layer poligono 
      geomType = layer.geometryType()
      #geomType = geom.type()
      if geomType == QGis.Point:      
         self.__rubberBandPoint.addGeometry(geom, layer)
      elif geomType == QGis.Line:      
         self.__rubberBandLine.addGeometry(geom, layer)
      elif geomType == QGis.Polygon:      
         self.__rubberBandPolygon.addGeometry(geom, layer)
      
   def addGeometries(self, geoms, layer):
      for g in geoms:
         self.addGeometry(g, layer)
         
         
   def setLine(self, points):
      self.__rubberBandLine.reset(QGis.Line)
      tot = len(points) - 1
      i = 0
      while i <= tot:
         if i < tot:
            self.__rubberBandLine.addPoint(points[i], False)
         else: # ultimo punto
            self.__rubberBandLine.addPoint(points[i], True)
         i = i + 1

   def setPolygon(self, points):
      self.__rubberBandPolygon.reset(QGis.Polygon)
      tot = len(points) - 1
      i = 0
      while i <= tot:
         if i < tot:
            self.__rubberBandPolygon.addPoint(points[i], False)
         else: # ultimo punto
            self.__rubberBandPolygon.addPoint(points[i], True)
         i = i + 1

   def addLinePoint(self, point, doUpdate = True, geometryIndex = 0):
      self.__rubberBandLine.addPoint(point, doUpdate, geometryIndex)

   def addPolygonPoint(self, point, doUpdate = True, geometryIndex = 0):
      self.__rubberBandPolygon.addPoint(point, doUpdate, geometryIndex)

   def reset(self):
      self.__rubberBandPoint.reset(QGis.Point)
      self.__rubberBandLine.reset(QGis.Line)
      self.__rubberBandPolygon.reset(QGis.Polygon)
      
      
   def setLineStyle(self, penStyle):      
      self.__rubberBandLine.setLineStyle(penStyle)
      self.__rubberBandPolygon.setLineStyle(penStyle)
      
      
