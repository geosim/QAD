# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 Classe per gestire rubber band di oggetti geometricamente non omogenei
 
                              -------------------
        begin                : 2013-12-12
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


# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *


import qad_debug
from qad_entity import *


#===============================================================================
# createRubberBand
#===============================================================================
def createRubberBand(mapCanvas, geometryType = QGis.Line, alternativeBand = False):
   """
   la funzione crea un rubber band di tipo <geometryType> con le impostazioni di QGIS.
   Se <alternativeBand> = True, il rubber band sarà impostato con più trasparenza e tipolinea punteggiato   
   """
   #qad_debug.breakPoint()
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
   def __init__(self, mapCanvas):
      self.__rubberBandPoint = createRubberBand(mapCanvas, QGis.Point)
      self.__rubberBandLine = createRubberBand(mapCanvas, QGis.Line)
      self.__rubberBandPolygon = createRubberBand(mapCanvas, QGis.Polygon)
   
   def hide(self):
      self.__rubberBandPoint.hide()
      self.__rubberBandLine.hide()
      self.__rubberBandPolygon.hide()         

   def show(self):
      self.__rubberBandPoint.show()
      self.__rubberBandLine.show()
      self.__rubberBandPolygon.show()
      
   def addGeometry(self, geom, layer):
      geomType = geom.type()
      if geomType == QGis.Point:      
         self.__rubberBandPoint.addGeometry(geom, layer)
      elif geomType == QGis.Line:      
         self.__rubberBandLine.addGeometry(geom, layer)
      elif geomType == QGis.Polygon:      
         self.__rubberBandPolygon.addGeometry(geom, layer)
      
   def addGeometries(self, geoms, layer):
      for g in geoms:
         self.addGeometry(g, layer)
         
         
   def setLine(self, points, layer):
      self.__rubberBandLine.reset(QGis.Line)
      tot = len(points) - 1
      i = 0
      while i <= tot:
         if i < tot:
            self.__rubberBandLine.addPoint(points[i], False)
         else: # ultimo punto
            self.__rubberBandLine.addPoint(points[i], True)
         i = i + 1


   def reset(self):
      self.__rubberBandPoint.reset(QGis.Point)
      self.__rubberBandLine.reset(QGis.Line)
      self.__rubberBandPolygon.reset(QGis.Polygon)
      
   def __del__(self):
      self.hide()
      del self.__rubberBandPoint
      del self.__rubberBandLine
      del self.__rubberBandPolygon         
      
      
      
      
      
      
