# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 Classe per gestire rubber band di oggetti geometricamente non omogenei
 
                              -------------------
        begin                : 2013-12-12
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


from qad_entity import *
from qad_variables import *


#===============================================================================
# QadCursorTypeEnum class.
#===============================================================================
class QadCursorTypeEnum():
   BOX   = 1     # un quadratino usato per selezionare entità
   CROSS = 2     # una croce usata per selezionare un punto


#===============================================================================
# createCursorRubberBand
#===============================================================================
# Classe che gestisce rubber band per disegnare il cursore a croce e il quadratino di pickbox
class QadCursorRubberBand():
   def __init__(self, mapCanvas, cursorType):
      self.mapCanvas = mapCanvas
      self.cursorType = cursorType
      
      if cursorType & QadCursorTypeEnum.BOX:
         self.__boxRubberBand = QgsRubberBand(mapCanvas, QGis.Line)
         self.__boxRubberBand.setColor(QColor(QadVariables.get(QadMsg.translate("Environment variables", "PICKBOXCOLOR"))))
         self.__pickSize = QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX"))
      else:
         self.__boxRubberBand = None
     
      if cursorType & QadCursorTypeEnum.CROSS:
         csrColor = QColor(QadVariables.get(QadMsg.translate("Environment variables", "CURSORCOLOR")))
         csrSize = QadVariables.get(QadMsg.translate("Environment variables", "CURSORSIZE"))
         self.__crosshairRubberBandSx = QgsRubberBand(mapCanvas, QGis.Line)
         self.__crosshairRubberBandSx.setColor(csrColor)
         self.__crosshairRubberBandDx = QgsRubberBand(mapCanvas, QGis.Line)
         self.__crosshairRubberBandDx.setColor(csrColor)
         self.__crosshairRubberBandDw = QgsRubberBand(mapCanvas, QGis.Line)
         self.__crosshairRubberBandDw.setColor(csrColor)
         self.__crosshairRubberBandUp = QgsRubberBand(mapCanvas, QGis.Line)
         self.__crosshairRubberBandUp.setColor(csrColor)
         screenRect = QApplication.desktop().screenGeometry(mapCanvas)
         self.__halfScreenSize = max(screenRect.height(), screenRect.width())
         if csrSize < 100:
            self.__halfScreenSize = self.__halfScreenSize / 2
         self.__halfScreenSize = self.__halfScreenSize * QadVariables.get(QadMsg.translate("Environment variables", "CURSORSIZE")) / 100
      else:
         self.__crosshairRubberBandSx = None
         self.__crosshairRubberBandDx = None
         self.__crosshairRubberBandDw = None
         self.__crosshairRubberBandUp = None

   def __del__(self):     
      if self.__boxRubberBand is not None:
         self.mapCanvas.scene().removeItem(self.__boxRubberBand)
         del self.__boxRubberBand
         
      if self.__crosshairRubberBandSx is not None:
         self.mapCanvas.scene().removeItem(self.__crosshairRubberBandSx)
         self.mapCanvas.scene().removeItem(self.__crosshairRubberBandDx)
         self.mapCanvas.scene().removeItem(self.__crosshairRubberBandDw)
         self.mapCanvas.scene().removeItem(self.__crosshairRubberBandUp)
         del self.__crosshairRubberBandSx
         del self.__crosshairRubberBandDx
         del self.__crosshairRubberBandDw
         del self.__crosshairRubberBandUp

   def moveEvent(self, point):
      # point è risultato di toMapCoordinates      
      if self.cursorType & QadCursorTypeEnum.BOX:
         pickSize = self.__pickSize * self.mapCanvas.mapUnitsPerPixel()

         self.__boxRubberBand.reset(QGis.Line)
         
         point1 = QgsPoint(point.x() - pickSize / 2, point.y() - pickSize / 2)
         self.__boxRubberBand.addPoint(point1, False)
         point1.setX(point1.x() + pickSize)
         self.__boxRubberBand.addPoint(point1, False)
         point1.setY(point1.y() + pickSize)
         self.__boxRubberBand.addPoint(point1, False)
         point1.setX(point1.x() - pickSize)
         self.__boxRubberBand.addPoint(point1, False)
         point1.setY(point1.y() - pickSize)
         self.__boxRubberBand.addPoint(point1, True)

      if self.cursorType & QadCursorTypeEnum.CROSS:
         halfScreenSize = self.__halfScreenSize * self.mapCanvas.mapUnitsPerPixel()
         
         self.__crosshairRubberBandSx.reset(QGis.Line)
         self.__crosshairRubberBandDx.reset(QGis.Line)
         self.__crosshairRubberBandDw.reset(QGis.Line)
         self.__crosshairRubberBandUp.reset(QGis.Line)
         
         if self.cursorType & QadCursorTypeEnum.BOX:
            halfPickSize = pickSize / 2
            point1 = QgsPoint(point.x() - halfScreenSize, point.y())
            point2 = QgsPoint(point.x() - halfPickSize, point.y())
            self.__crosshairRubberBandSx.addPoint(point1, False)
            self.__crosshairRubberBandSx.addPoint(point2, True)

            point1.setX(point.x() + halfScreenSize)
            point2.setX(point.x() + halfPickSize)
            self.__crosshairRubberBandDx.addPoint(point1, False)
            self.__crosshairRubberBandDx.addPoint(point2, True)
            
            point1.set(point.x(), point.y() - halfScreenSize)
            point2.set(point.x(), point.y() - halfPickSize)
            self.__crosshairRubberBandDw.addPoint(point1, False)
            self.__crosshairRubberBandDw.addPoint(point2, True)
            
            point1.setY(point.y() + halfScreenSize)
            point2.setY(point.y() + halfPickSize)           
            self.__crosshairRubberBandUp.addPoint(point1, False)
            self.__crosshairRubberBandUp.addPoint(point2, True)            
         else:
            point1 = QgsPoint(point.x() - halfScreenSize, point.y())
            self.__crosshairRubberBandSx.addPoint(point, False)
            self.__crosshairRubberBandSx.addPoint(point1, True)
            
            point1.setX(point.x() + halfScreenSize)
            self.__crosshairRubberBandDx.addPoint(point, False)
            self.__crosshairRubberBandDx.addPoint(point1, True)
            
            point1.set(point.x(), point.y() - halfScreenSize)
            self.__crosshairRubberBandDw.addPoint(point, False)
            self.__crosshairRubberBandDw.addPoint(point1, True)
            
            point1.setY(point.y() + halfScreenSize)
            self.__crosshairRubberBandUp.addPoint(point, False)
            self.__crosshairRubberBandUp.addPoint(point1, True)

   def hide(self):
      if self.__boxRubberBand is not None:
         self.__boxRubberBand.hide()
         
      if self.__crosshairRubberBandSx is not None:
         self.__crosshairRubberBandSx.hide()
         self.__crosshairRubberBandDx.hide()
         self.__crosshairRubberBandDw.hide()
         self.__crosshairRubberBandUp.hide()
      
   def show(self):
      if self.__boxRubberBand is not None:
         self.__boxRubberBand.show()
         
      if self.__crosshairRubberBandSx is not None:
         self.__crosshairRubberBandSx.show()
         self.__crosshairRubberBandDx.show()
         self.__crosshairRubberBandDw.show()
         self.__crosshairRubberBandUp.show()


#===============================================================================
# getQGISColorForRubberBand
#===============================================================================
def getQGISColorForRubberBand(geometryType = QGis.Line, alternativeBand = False):
   """
   La funzione legge il colore impostato da QGIS per il rubber band di tipo <geometryType>.
   Se <alternativeBand> = True, il rubber band sarà impostato con più trasparenza
   """
   settings = QSettings()
   color = QColor(int(settings.value( "/qgis/digitizing/line_color_red", 1)), \
                  int(settings.value( "/qgis/digitizing/line_color_green", 1)), \
                  int(settings.value( "/qgis/digitizing/line_color_blue", 1)))
   alpha = float(int(settings.value( "/qgis/digitizing/line_color_alpha", 200)) / 255.0)
  
   if alternativeBand:
      alpha = alpha * float(settings.value( "/qgis/digitizing/line_color_alpha_scale", 0.75))
 
   if geometryType == QGis.Polygon:
      color.setAlphaF(alpha)

   color.setAlphaF(alpha)
   return color


#===============================================================================
# createRubberBand
#===============================================================================
def createRubberBand(mapCanvas, geometryType = QGis.Line, alternativeBand = False, color = None):
   """
   la funzione crea un rubber band di tipo <geometryType> con le impostazioni di QGIS.
   Se <alternativeBand> = True, il rubber band sarà impostato con più trasparenza e tipolinea punteggiato   
   """
   if color is None:
      color = getQGISColorForRubberBand(geometryType, alternativeBand)

   settings = QSettings()
   width = int(settings.value( "/qgis/digitizing/line_width", 1))

   rb = QgsRubberBand(mapCanvas, geometryType)
   
   if alternativeBand:
      rb.setLineStyle(Qt.DotLine)
 
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
      
      
