# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire i grip
 
                              -------------------
        begin                : 2015-09-29
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


from qad_arc import *
from qad_circle import *
from qad_variables import *
from qad_entity import *


#===============================================================================
# QadGripStatusEnum class.
#===============================================================================
class QadGripStatusEnum():
   NONE             = 0  # nessuno
   UNSELECTED       = 1  # grip non selezionato
   SELECTED         = 2  # grip selezionato
   HOVER            = 3  # grip non selezionati quando il cursore si ferma su di essi


#===============================================================================
# QadGripIconTypeEnum class.
#===============================================================================
class QadGripIconTypeEnum():
   NONE             = 0  # nessuno
   BOX              = 1  # un quadrato
   CIRCLE           = 2  # cerchio
   RECTANGLE        = 3  # rettangolo


#===============================================================================
# QadGripMarker class.
#===============================================================================
class QadGripMarker(QgsMapCanvasItem):
   """
   Classe che gestisce i marcatori dei grip
   """
      

   #============================================================================
   # __init__
   #============================================================================
   def __init__(self, mapCanvas):
      QgsMapCanvasItem.__init__(self, mapCanvas)
      self.__canvas = mapCanvas
      self.iconType = QadGripIconTypeEnum.BOX # icon to be shown
      self.iconSize = QadVariables.get(QadMsg.translate("Environment variables", "GRIPSIZE"))
      self.borderColor = QadVariables.get(QadMsg.translate("Environment variables", "GRIPCONTOUR")) # color of the border
      self.center = QgsPoint(0, 0) #  coordinates of the point in the center
      self.setGrip(QadGripStatusEnum.UNSELECTED, QadGripIconTypeEnum.BOX)

      
   def __del__(self):     
      self.removeItem()


   def removeItem(self):
      self.__canvas.scene().removeItem(self)
      

   def setCenter(self, point):
      self.center = point
      pt = self.toCanvasCoordinates(self.center)
      self.setPos(pt)
   
   
   def setGrip(self, status, iconType, rot = 0.0):
      # rot in radians counterclockwise (0 = horizontal)
      if status == QadGripStatusEnum.UNSELECTED:
         self.fillColor = QadVariables.get(QadMsg.translate("Environment variables", "GRIPCOLOR"))
      elif status == QadGripStatusEnum.SELECTED:
         self.fillColor = QadVariables.get(QadMsg.translate("Environment variables", "GRIPHOT"))
      elif status == QadGripStatusEnum.HOVER:
         self.fillColor = QadVariables.get(QadMsg.translate("Environment variables", "GRIPHOVER"))
      
      self.status = status
      self.__iconType = iconType
      self.__rot = -qad_utils.toDegrees(rot) # trasformo in gradi in senso orario

      
   def paint(self, painter, option, widget):
      """
      painter é un QPainter
      """

      s = self.iconSize / 2

      pen = QPen(QColor(self.borderColor))
      pen.setWidth(1)
      painter.setPen(pen)
      painter.rotate(self.__rot)

      if self.__iconType == QadGripIconTypeEnum.NONE:
         pass
      elif self.__iconType == QadGripIconTypeEnum.BOX:
         # un quadrato
         painter.fillRect(-s, -s, self.iconSize, self.iconSize, QBrush(QColor(self.fillColor)));
         painter.drawRect(-s, -s, self.iconSize, self.iconSize)
      elif self.__iconType == QadGripIconTypeEnum.CIRCLE:
         # cerchio
         painter.setBrush(QBrush(QColor(self.fillColor)))
         painter.drawEllipse(QPointF(0, 0), s, s)
      elif self.__iconType == QadGripIconTypeEnum.RECTANGLE:
         # un rettangolo
         painter.fillRect(-s, -s / 2, self.iconSize, self.iconSize / 2, QBrush(QColor(self.fillColor)));
         painter.drawRect(-s, -s / 2, self.iconSize, self.iconSize / 2)
         

   def boundingRect(self):
      if self.__rot != 0:
         width = qad_utils.getDistance(QgsPoint(0,0), QgsPoint(self.iconSize, self.iconSize))
         height = width            
      else:
         width = self.iconSize
         height = self.iconSize
         
      return QRectF(-width/2, -height/2, width, height)


   def updatePosition(self):
      self.setCenter(self.center)


#===============================================================================
# QadGripPointTypeEnum class.
#===============================================================================
class QadGripPointTypeEnum():
   NONE      = 0  # nessuno
   VERTEX    = 1  # vertice di una geometria
   MID_POINT = 2  # punto medio di un segmento/arco
   CENTER    = 3  # centro di un cerchio
   QUA_POINT = 4  # punto quadrante


#===============================================================================
# QadEntityGripPoint class.
#===============================================================================
class QadEntityGripPoint():
   """
   Classe che gestisce un punto di grip per una entità
   """


   #============================================================================
   # __init__
   #============================================================================
   def __init__(self, mapCanvas, point, type, atGeom = 0, atSubGeom = 0, nVertex = 0, rot = 0.0):
      self.atGeom = atGeom # numero di geometria (0-index)
      self.atSubGeom = atSubGeom # numero di sotto-geometria (0-index)
      self.nVertex = nVertex # numero di vertice della QadLinearObjectList della geometria e sotto-geometria (0-index)      
      
      self.gripType = type
         
      self.gripMarker = QadGripMarker(mapCanvas)
      self.gripMarker.setGrip(QadGripStatusEnum.UNSELECTED, self.gripType2IconType(self.gripType), rot)
      self.gripMarker.setCenter(point)
      
   def __del__(self):
      self.removeItem()
      del self.gripMarker

   def removeItem(self):
      self.gripMarker.removeItem()
   
   def isIntersecting(self, point):
      ToleranceInMapUnits = self.gripMarker.iconSize * mQgsMapTool.canvas.mapRenderer().mapUnitsPerPixel()      
      if point.x() >= self.gripMarker.center.x() - ToleranceInMapUnits and \
         point.x() <= self.gripMarker.center.x() + ToleranceInMapUnits and \
         point.y() >= self.gripMarker.center.y() - ToleranceInMapUnits and \
         point.y() <= self.gripMarker.center.y() + ToleranceInMapUnits:
         return True
      else:
         return False
      
   def select(self): # seleziona un grip
      self.gripMarker.setGrip(QadGripStatusEnum.SELECTED, self.gripType2IconType(self.gripType))
      self.gripMarker.show()

   def unselect(self): # deseleziona un grip
      self.gripMarker.setGrip(QadGripStatusEnum.UNSELECTED, self.gripType2IconType(self.gripType))
      self.gripMarker.show()

   def hover(self): # grip non selezionato quando il cursore si ferma su di esso
      if self.getStatus() == QadGripStatusEnum.UNSELECTED:
         self.gripMarker.setGrip(QadGripStatusEnum.HOVER, self.gripType2IconType(self.gripType))
         self.gripMarker.show()
   
   def getStatus(self):
      return self.gripMarker.status
   
   def gripType2IconType(self, gripType):
      if gripType == QadGripPointTypeEnum.VERTEX:
         return QadGripIconTypeEnum.BOX
      elif gripType == QadGripPointTypeEnum.MID_POINT:
         return QadGripIconTypeEnum.RECTANGLE
      elif gripType == QadGripPointTypeEnum.CENTER:
         return QadGripIconTypeEnum.CIRCLE
      elif gripType == QadGripPointTypeEnum.QUA_POINT:
         return QadGripIconTypeEnum.BOX
      else:
         return None

   
#===============================================================================
# QadEntityGripPoints class.
#===============================================================================
class QadEntityGripPoints(QgsMapCanvasItem):
   """
   Classe che gestisce i punti di grip per una entità
   """
      

   #============================================================================
   # __init__
   #============================================================================
   def __init__(self, mapCanvas, entity = None):
      self.mapCanvas = mapCanvas
      if entity is not None:
         self.entity = QadEntity(entity)      
         self.entityGripPoints = self.initGripPoints()


   def __del__(self):
      self.removeItems()
      del self.entityGripPoints[:]


   def set(self, layer, featureId):
      self.entity = QadEntity()
      self.entity.set(layer, featureId)
      self.entityGripPoints = self.initGripPoints()


   def removeItems(self, gripList = None):
      if gripList is None:
         for entityGripPoint in self.entityGripPoints:
            if type(entityGripPoint) == list:
               self.removeItems(entityGripPoint)
            else:
               entityGripPoint.removeItem()
         del self.entityGripPoints[:]
      else:         
         for entityGripPoint in gripList:
            if type(entityGripPoint) == list:
               self.removeItems(entityGripPoint)
            else:
               entityGripPoint.removeItem()


   def selectIntersectingGripPoints(self, point):
      # seleziona i grip che intersecano un punto in map coordinate
      # lo trasformo nelle coordinate del layer
      pt = self.mapCanvas.mapRenderer().mapToLayerCoordinates(self.entity.layer, point)
      
      for entityGripPoint in self.entityGripPoints:
         if entityGripPoint.isIntersecting(pt):
            entityGripPoint.select()

      
   def unselectIntersectingGripPoints(self, point):
      # deseleziona i grip che intersecano un punto in map coordinate
      # lo trasformo nelle coordinate del layer
      pt = self.mapCanvas.mapRenderer().mapToLayerCoordinates(self.entity.layer, point)
      
      for entityGripPoint in self.entityGripPoints:
         if entityGripPoint.isIntersecting(pt):
            entityGripPoint.unselect()


   def hoverIntersectingGripPoints(self, point):
      # seleziono in modo hover i grip che intersecano un punto (in map coordinate)
      # non selezionati quando il cursore si ferma su di esso
      # lo trasformo nelle coordinate del layer
      pt = self.mapCanvas.mapRenderer().mapToLayerCoordinates(self.entity.layer, point)
      
      for entityGripPoint in self.entityGripPoints:
         if entityGripPoint.isIntersecting(pt):
            entityGripPoint.hover()


   def getSelectedGripPoints(self):
      # restituisce una lista di punti in cui i grip sono selezionati
      result = []
      
      for gripPoint in self.entityGripPoints:
         if gripPoint.getStatus() == QadGripStatusEnum.SELECTED:
            result.append(gripPoint)
      
      return result
         

   def initGripPoints(self):
      atGeom = 0
      atSubGeom = 0
      result = []
      g = self.entity.getGeometry()
      wkbType = g.wkbType()
      if wkbType == QGis.WKBPoint:
         gp = QadEntityGripPoint(self.mapCanvas, g.asPoint(), QadGripPointTypeEnum.VERTEX)
         result.append(gp)
      elif wkbType == QGis.WKBMultiPoint:
         pointList = g.asMultiPoint() # vettore di punti
         atGeom = 0
         for point in pointList:
            gp = QadEntityGripPoint(self.mapCanvas, point, QadGripPointTypeEnum.VERTEX, atGeom)
            atGeom = atGeom + 1
            result.append(gp)
      elif wkbType == QGis.WKBLineString:
         result.extend(self.getGripPointsFromPolyline(g.asPolyline()))
      elif wkbType == QGis.WKBMultiLineString:
         lineList = g.asMultiPolyline() # vettore di linee
         atGeom = 0
         for line in lineList:
            result.extend(self.getGripPointsFromPolyline(line, atGeom))
            atGeom = atGeom + 1
      elif wkbType == QGis.WKBPolygon:
         lineList = g.asPolygon() # vettore di linee    
         atGeom = 0
         for line in lineList:
            result.extend(self.getGripPointsFromPolyline(line, atGeom))
            atGeom = atGeom + 1
      elif wkbType == QGis.WKBMultiPolygon:
         polygonList = g.asMultiPolygon() # vettore di poligoni
         atGeom = 0
         for polygon in polygonList:
            atSubGeom = 0
            result1 = []
            for line in polygon:
               result.extend(self.getGripPointsFromPolyline(line, atGeom, atSubGeom))
               atSubGeom = atSubGeom + 1
            atGeom = atGeom + 1
   
      return result
   
   def getGripPointsFromPolyline(self, pointList, atGeom = 0, atSubGeom = 0):
      arc = QadArc()
      startEndVertices = arc.fromPolyline(pointList, 0)
      # se la polilinea è composta solo da un arco
      if startEndVertices and startEndVertices[0] == 0 and startEndVertices[1] == len(pointList)-1:
         return self.getGripPointsFromQadArc(arc, atGeom, atSubGeom)
      else:
         circle = QadCircle()
         startEndVertices = circle.fromPolyline(pointList, 0)
         # se la polilinea è composta solo da un cerchio
         if startEndVertices and startEndVertices[0] == 0 and startEndVertices[1] == len(pointList)-1:
            return self.getGripPointsFromQadCircle(circle, atGeom, atSubGeom)
         else:
            linearObjectList = qad_utils.QadLinearObjectList()
            linearObjectList.fromPolyline(pointList)
            return self.getGripPointsFromQadLinearObjectList(linearObjectList, atGeom, atSubGeom)
      
   
   def getGripPointsFromQadLinearObjectList(self, linearObjectList, atGeom = 0, atSubGeom = 0):
      """
      Ottiene una lista di punti di grip da una QadLinearObjectList (vertici e punti medi con rotaz)
      """
      result = []
      nVertex = 0
      while nVertex < linearObjectList.qty():
         linearObject = linearObjectList.getLinearObjectAt(nVertex)
         startPt = linearObject.getStartPt()
         gp = QadEntityGripPoint(self.mapCanvas, startPt, QadGripPointTypeEnum.VERTEX, atGeom, atSubGeom, nVertex)
         result.append(gp)
         middlePt = linearObject.getMiddlePt()
         rot = linearObject.getTanDirectionOnMiddlePt()
         gp = QadEntityGripPoint(self.mapCanvas, middlePt, QadGripPointTypeEnum.MID_POINT, atGeom, atSubGeom, nVertex, rot)
         result.append(gp)
         nVertex = nVertex + 1
      
      if linearObjectList.isClosed() == False:
         linearObject = linearObjectList.getLinearObjectAt(-1) # ultima parte
         endPt = linearObject.getEndPt()
         gp = QadEntityGripPoint(self.mapCanvas, endPt, QadGripPointTypeEnum.VERTEX, atGeom, atSubGeom, nVertex)
         result.append(gp)
         
      return result


   def getGripPointsFromQadCircle(self, circle, atGeom = 0, atSubGeom = 0):
      """
      Ottiene una lista di punti di grip da un QadCircle (centro e punti quadrante)
      """
      result = []
      gp = QadEntityGripPoint(self.mapCanvas, circle.center, QadGripPointTypeEnum.CENTER, atGeom, atSubGeom, -1)
      result.append(gp)
      qua_points = circle.getQuadrantPoints()
      for pt in qua_points:
         gp = QadEntityGripPoint(self.mapCanvas, pt, QadGripPointTypeEnum.QUA_POINT, atGeom, atSubGeom, -1)
         result.append(gp)
         
      return result


   def getGripPointsFromQadArc(self, arc, atGeom = 0, atSubGeom = 0):
      """
      Ottiene una lista di punti di grip da un QadArc (punto centrale, iniziale, finale, medio)
      """
      result = []
      gp = QadEntityGripPoint(self.mapCanvas, arc.center, QadGripPointTypeEnum.CENTER, atGeom, atSubGeom, -1)
      result.append(gp)
      gp = QadEntityGripPoint(self.mapCanvas, arc.getStartPt(), QadGripPointTypeEnum.VERTEX, atGeom, atSubGeom, 0)
      result.append(gp)
      gp = QadEntityGripPoint(self.mapCanvas, arc.getEndPt(), QadGripPointTypeEnum.VERTEX, atGeom, atSubGeom, 1)
      result.append(gp)
      middlePt = arc.getMiddlePt()
      rot = arc.getTanDirectionOnPt(middlePt)
      gp = QadEntityGripPoint(self.mapCanvas, middlePt, QadGripPointTypeEnum.MID_POINT, atGeom, atSubGeom, 1)
      result.append(gp)
         
      return result



#===============================================================================
# QadEntitySetGripPoints class.
#===============================================================================
class QadEntitySetGripPoints(QgsMapCanvasItem):
   """
   Classe che gestisce i punti di grip per una gruppo di selezione di entità
   """
      

   #============================================================================
   # __init__
   #============================================================================
   def __init__(self, mapCanvas, entitySet):
      self.mapCanvas = mapCanvas
      self.entitySet = QadEntitySet(entitySet)

      self.entityGripPoints = []
      # for each layer
      for layerEntitySet in self.entitySet.layerEntitySetList:
         for featureId in layerEntitySet.featureIds:
            entityGripPoints = QadEntityGripPoints()
            entityGripPoints.set(layerEntitySet.layer, featureId)
            self.entityGripPoints.appen(entityGripPoints)


   def __del__(self):
      self.removeItems()
      del self.entityGripPoints[:]


   def removeItems(self):
      for entityGripPoint in self.entityGripPoints:
         entityGripPoint.removeItems()
      del self.entityGripPoints[:]
