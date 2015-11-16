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
      self.canvas = mapCanvas
      self.iconType = QadGripIconTypeEnum.BOX # icon to be shown
      self.iconSize = QadVariables.get(QadMsg.translate("Environment variables", "GRIPSIZE"))
      self.borderColor = QadVariables.get(QadMsg.translate("Environment variables", "GRIPCONTOUR")) # color of the border
      self.center = QgsPoint(0, 0) #  coordinates of the point in the center
      self.setGrip(QadGripStatusEnum.UNSELECTED, QadGripIconTypeEnum.BOX)

      
   def __del__(self):     
      self.removeItem()


   def removeItem(self):
      self.canvas.scene().removeItem(self)
      

   def setCenter(self, point):
      # point è in map coordinates
      self.center = point
      pt = self.toCanvasCoordinates(self.center)
      self.setPos(pt)
   
   
   def setGrip(self, status, iconType, rot = None):
      # rot in radians counterclockwise (0 = horizontal)
      if status == QadGripStatusEnum.UNSELECTED:
         self.fillColor = QadVariables.get(QadMsg.translate("Environment variables", "GRIPCOLOR"))
      elif status == QadGripStatusEnum.SELECTED:
         self.fillColor = QadVariables.get(QadMsg.translate("Environment variables", "GRIPHOT"))
      elif status == QadGripStatusEnum.HOVER:
         self.fillColor = QadVariables.get(QadMsg.translate("Environment variables", "GRIPHOVER"))
      
      self.status = status
      self.__iconType = iconType
      if rot is not None:
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
   NONE           = 0  # nessuno
   VERTEX         = 1  # vertice di una geometria
   LINE_MID_POINT = 2  # punto medio di un segmento
   CENTER         = 3  # centro di un cerchio o di un arco
   QUA_POINT      = 4  # punto quadrante
   ARC_MID_POINT  = 5  # punto medio di un arco


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
   
   def getPoint(self):
      return self.gripMarker.center
   
   def isIntersecting(self, point):
      # point è in map coordinate
      ToleranceInMapUnits = self.gripMarker.iconSize * self.gripMarker.canvas.mapRenderer().mapUnitsPerPixel()
      if point.x() >= self.getPoint().x() - ToleranceInMapUnits and \
         point.x() <= self.getPoint().x() + ToleranceInMapUnits and \
         point.y() >= self.getPoint().y() - ToleranceInMapUnits and \
         point.y() <= self.getPoint().y() + ToleranceInMapUnits:
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
      elif gripType == QadGripPointTypeEnum.LINE_MID_POINT or gripType == QadGripPointTypeEnum.ARC_MID_POINT:
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
   def __init__(self, mapCanvas, entity = None, grips = 2):
      self.mapCanvas = mapCanvas
      self.gripPoints = [] # lista dei punti di grip in map coordinate
      self.layerGripPoints = [] # lista di QgsPoint che rappresentano i punti di grip in layer coordinate
                                # sono costretto a usare questa lista perchè se prendo un punto geometrico dell'entità che è in coordinate lat. long. 
                                # e lo trasformo in map coordinate, quando lo dovrò ritraformare in layer coordinate si cambia il 5° decimale 
                                # che equivale a più di 1 metro di errore. 
      if entity is not None:
         self.entity = QadEntity(entity)      
         self.gripPoints, self.layerGripPoints = self.initGripPoints(grips)


   def __del__(self):
      self.removeItems()


   def set(self, layer, featureId, grips = 2):
      self.entity = QadEntity()
      self.entity.set(layer, featureId)
      self.gripPoints, self.layerGripPoints = self.initGripPoints(grips)


   def removeItems(self):
      for gripPoint in self.gripPoints:
         gripPoint.removeItem()
      del self.gripPoints[:]
      del self.layerGripPoints[:]


   def selectIntersectingGripPoints(self, point):
      # seleziona i grip che intersecano un punto in map coordinate     
      res = 0
      for gripPoint in self.gripPoints:
         if gripPoint.isIntersecting(point):
            gripPoint.select()
            res = res + 1
      return res

      
   def unselectIntersectingGripPoints(self, point):
      # deseleziona i grip che intersecano un punto in map coordinate
      res = 0
      for gripPoint in self.gripPoints:
         if gripPoint.isIntersecting(point):
            gripPoint.unselect()
            res = res + 1
      return res


   def toggleSelectIntersectingGripPoints(self, point):
      # seleziona i grip deselezionati e deseleziona i grip selezionati
      # che intersecano un punto in map coordinate      
      for gripPoint in self.gripPoints:
         if gripPoint.isIntersecting(point):
            if gripPoint.getStatus() == QadGripStatusEnum.SELECTED:
               gripPoint.unselect()
            else:
               gripPoint.select()
      

   def hoverIntersectingGripPoints(self, point):
      # seleziono in modo hover i grip che intersecano un punto (in map coordinate)
      # non selezionati quando il cursore si ferma su di esso
      res = 0
      for gripPoint in self.gripPoints:
         if gripPoint.isIntersecting(point):
            gripPoint.hover()
            res = res + 1
         else:
            status = gripPoint.getStatus()
            if status == QadGripStatusEnum.SELECTED:
               gripPoint.select()
            else:
               gripPoint.unselect()
      return res


   def isIntersecting(self, point):
      # ritorna il punto di intersezione in map coordinate      
      for gripPoint in self.gripPoints:
         if gripPoint.isIntersecting(point):
            return gripPoint.getPoint()
      return None


   def getSelectedGripPoints(self):
      # restituisce una lista di punti in cui i grip sono selezionati
      result = []
      
      for gripPoint in self.gripPoints:
         if gripPoint.getStatus() == QadGripStatusEnum.SELECTED:
            result.append(gripPoint)
      
      return result
         

   def initGripPoints(self, grips = 2):
      atGeom = 0
      atSubGeom = 0
      result = []
      layerPoints = [] # lista di QgsPoint che rappresentano i punti di grip in layer coordinate

      g = self.entity.getGeometry()
      if g is None:
         return result, layerPoints
      wkbType = g.wkbType()
      if wkbType == QGis.WKBPoint:
         layerPt = g.asPoint()
         layerPoints.append(layerPt)
         # converto il punto dal layer coordinate in map coordinates
         pt = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, layerPt)
         gp = QadEntityGripPoint(self.mapCanvas, pt, QadGripPointTypeEnum.VERTEX)
         result.append(gp)
         
      elif wkbType == QGis.WKBMultiPoint:
         pointList = g.asMultiPoint() # vettore di punti
         atGeom = 0
         for point in pointList:
            layerPoints.append(point)
            # converto il punto dal layer coordinate in map coordinates
            pt = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, point)
            gp = QadEntityGripPoint(self.mapCanvas, pt, QadGripPointTypeEnum.VERTEX, atGeom)
            atGeom = atGeom + 1
            result.append(gp)
            
      elif wkbType == QGis.WKBLineString:
         result, layerPoints = self.getGripPointsFromPolyline(g.asPolyline(), 0, 0, grips)
         
      elif wkbType == QGis.WKBMultiLineString:
         lineList = g.asMultiPolyline() # vettore di linee
         atGeom = 0
         for line in lineList:
            partial1, partial2 = self.getGripPointsFromPolyline(line, atGeom, 0, grips)
            result.extend(partial1)
            layerPoints.extend(partial2)
            atGeom = atGeom + 1
                        
      elif wkbType == QGis.WKBPolygon:
         lineList = g.asPolygon() # vettore di linee    
         atGeom = 0
         for line in lineList:
            partial1, partial2 = self.getGripPointsFromPolyline(line, atGeom, 0, grips)
            result.extend(partial1)
            layerPoints.extend(partial2)
            # aggiungo il centroide
            layerPt = g.centroid().asPoint()
            layerPoints.append(layerPt)
            # converto il punto dal layer coordinate in map coordinates
            pt = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, layerPt)
            gp = QadEntityGripPoint(self.mapCanvas, pt, QadGripPointTypeEnum.CENTER, atGeom, 0)
            result.append(gp)
            atGeom = atGeom + 1         
         
      elif wkbType == QGis.WKBMultiPolygon:
         polygonList = g.asMultiPolygon() # vettore di poligoni
         atGeom = 0
         for polygon in polygonList:
            atSubGeom = 0
            result1 = []
            for line in polygon:
               partial1, partial2 = self.getGripPointsFromPolyline(line, atGeom, atSubGeom, grips)
               result.extend(partial1)
               layerPoints.extend(partial2)
               # aggiungo il centroide
               sub_g =  QgsGeometry.fromPolygon(line)
               layerPt = sub_g.centroid().asPoint()
               layerPoints.append(layerPt)
               # converto il punto dal layer coordinate in map coordinates
               pt = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, layerPt)
               gp = QadEntityGripPoint(self.mapCanvas, pt, QadGripPointTypeEnum.CENTER, atGeom, atSubGeom)
               result.append(gp)
               
               atSubGeom = atSubGeom + 1
            atGeom = atGeom + 1
   
      return result, layerPoints
   
   
   def getGripPointsFromPolyline(self, pointList, atGeom = 0, atSubGeom = 0, grips = 2):
      arc = QadArc()
      startEndVertices = arc.fromPolyline(pointList, 0)
      # se la polilinea è composta solo da un arco
      if startEndVertices and startEndVertices[0] == 0 and startEndVertices[1] == len(pointList)-1:
         return self.getGripPointsFromQadArc(arc, atGeom, atSubGeom, grips)
      else:
         circle = QadCircle()
         startEndVertices = circle.fromPolyline(pointList, 0)
         # se la polilinea è composta solo da un cerchio
         if startEndVertices and startEndVertices[0] == 0 and startEndVertices[1] == len(pointList)-1:
            return self.getGripPointsFromQadCircle(circle, atGeom, atSubGeom)
         else:
            linearObjectList = qad_utils.QadLinearObjectList()
            linearObjectList.fromPolyline(pointList)
            return self.getGripPointsFromQadLinearObjectList(linearObjectList, atGeom, atSubGeom, grips)
      
   
   def getGripPointsFromQadLinearObjectList(self, linearObjectList, atGeom = 0, atSubGeom = 0, grips = 2):
      """
      Ottiene una lista di punti di grip da una QadLinearObjectList (vertici e punti medi con rotaz)
      grips = 1 Displays grips
      grips = 2 Displays additional midpoint grips on polyline segments
      """
      result = []
      layerPoints = [] # lista di QgsPoint che rappresentano i punti di grip in layer coordinate
     
      nVertex = 0
      while nVertex < linearObjectList.qty():
         linearObject = linearObjectList.getLinearObjectAt(nVertex)
         startPt = linearObject.getStartPt()
         layerPoints.append(startPt)         
         # converto il punto dal layer coordinate in map coordinates
         startPt = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, startPt);         
         gp = QadEntityGripPoint(self.mapCanvas, startPt, QadGripPointTypeEnum.VERTEX, atGeom, atSubGeom, nVertex)
         result.append(gp)
         if grips == 2:
            middlePt = linearObject.getMiddlePt()
            layerPoints.append(middlePt)
            rot = linearObject.getTanDirectionOnMiddlePt()
            # converto il punto dal layer coordinate in map coordinates
            middlePt = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, middlePt);
            if linearObject.isSegment(): # linea
               gp = QadEntityGripPoint(self.mapCanvas, middlePt, QadGripPointTypeEnum.LINE_MID_POINT, atGeom, atSubGeom, nVertex, rot)
            else: # arco
               gp = QadEntityGripPoint(self.mapCanvas, middlePt, QadGripPointTypeEnum.ARC_MID_POINT, atGeom, atSubGeom, nVertex, rot)
            result.append(gp)
         nVertex = nVertex + 1
      
      linearObject = linearObjectList.getLinearObjectAt(-1) # ultima parte
      endPt = linearObject.getEndPt()
      layerPoints.append(endPt)
      # converto il punto dal layer coordinate in map coordinates
      endPt = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, endPt);
      gp = QadEntityGripPoint(self.mapCanvas, endPt, QadGripPointTypeEnum.VERTEX, atGeom, atSubGeom, nVertex)
      result.append(gp)
         
      return result, layerPoints


   def getGripPointsFromQadCircle(self, circle, atGeom = 0, atSubGeom = 0):
      """
      Ottiene una lista di punti di grip da un QadCircle (centro e punti quadrante)
      """
      result = []
      layerPoints = [] # lista di QgsPoint che rappresentano i punti di grip in layer coordinate
      layerPoints.append(QgsPoint(circle.center))
      # converto il punto dal layer coordinate in map coordinates
      center = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, circle.center);
      gp = QadEntityGripPoint(self.mapCanvas, center, QadGripPointTypeEnum.CENTER, atGeom, atSubGeom, -1)
      result.append(gp)
      qua_points = circle.getQuadrantPoints()
      for pt in qua_points:
         layerPoints.append(pt)
         # converto il punto dal layer coordinate in map coordinates
         pt = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, pt);
         gp = QadEntityGripPoint(self.mapCanvas, pt, QadGripPointTypeEnum.QUA_POINT, atGeom, atSubGeom, -1)
         result.append(gp)
         
      return result, layerPoints


   def getGripPointsFromQadArc(self, arc, atGeom = 0, atSubGeom = 0, grips = 2):
      """
      Ottiene una lista di punti di grip da un QadArc (punto centrale, iniziale, finale, medio)
      """
      result = []
      layerPoints = [] # lista di QgsPoint che rappresentano i punti di grip in layer coordinate
      layerPoints.append(QgsPoint(arc.center))
      # converto il punto dal layer coordinate in map coordinates
      pt = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, arc.center);
      gp = QadEntityGripPoint(self.mapCanvas, pt, QadGripPointTypeEnum.CENTER, atGeom, atSubGeom, -1)
      result.append(gp)
      # converto il punto dal layer coordinate in map coordinates
      layerPt = arc.getStartPt()
      layerPoints.append(layerPt)
      pt = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, layerPt);
      gp = QadEntityGripPoint(self.mapCanvas, pt, QadGripPointTypeEnum.VERTEX, atGeom, atSubGeom, 0)
      result.append(gp)
      # converto il punto dal layer coordinate in map coordinates
      layerPt = arc.getEndPt()
      layerPoints.append(layerPt)
      pt = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, layerPt);
      gp = QadEntityGripPoint(self.mapCanvas, pt, QadGripPointTypeEnum.VERTEX, atGeom, atSubGeom, 1)
      result.append(gp)
      if grips == 2:
         layerPt = arc.getMiddlePt()
         layerPoints.append(layerPt)
         rot = arc.getTanDirectionOnPt(layerPt)
         # converto il punto dal layer coordinate in map coordinates
         pt = self.mapCanvas.mapSettings().layerToMapCoordinates(self.entity.layer, layerPt);
         gp = QadEntityGripPoint(self.mapCanvas, pt, QadGripPointTypeEnum.ARC_MID_POINT, atGeom, atSubGeom, 1)
         result.append(gp)
         
      return result, layerPoints



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
   def __init__(self, mapCanvas):
      self.mapCanvas = mapCanvas
      self.entityGripPoints = []


   def __del__(self):
      self.removeItems()


   def removeItems(self):
      for entityGripPoint in self.entityGripPoints:
         entityGripPoint.removeItems()
      del self.entityGripPoints[:]


   def set(self, entitySet, grips = 2):
      """
         grips = 0 Hides grips
         grips = 1 Displays grips
         grips = 2 Displays additional midpoint grips on polyline segments
      """
      self.removeItems()
      
      if grips == 0: # nasconde i grip
         return

      # for each layer
      for layerEntitySet in entitySet.layerEntitySetList:
         for featureId in layerEntitySet.featureIds:
            entityGripPoints = QadEntityGripPoints(self.mapCanvas)
            entityGripPoints.set(layerEntitySet.layer, featureId, grips)
            self.entityGripPoints.append(entityGripPoints)


   def addEntity(self, entity, grips = 2):
      """
         grips = 0 Hides grips
         grips = 1 Displays grips
         grips = 2 Displays additional midpoint grips on polyline segments
      """
      if grips == 0: # nasconde i grip
         return      
      if self.containsEntity(entity) == False:
         entityGripPoints = QadEntityGripPoints(self.mapCanvas)
         entityGripPoints.set(entity.layer, entity.featureId, grips)
         self.entityGripPoints.append(entityGripPoints)


   def hoverIntersectingGripPoints(self, point):
      res = 0
      for entityGripPoint in self.entityGripPoints:
         res = res + entityGripPoint.hoverIntersectingGripPoints(point)
      return res


   def selectIntersectingGripPoints(self, point):
      res = 0
      for entityGripPoint in self.entityGripPoints:
         res = res + entityGripPoint.selectIntersectingGripPoints(point)
      return res


   def unselectIntersectingGripPoints(self, point):
      res = 0
      for entityGripPoint in self.entityGripPoints:
         res = res + entityGripPoint.unselectIntersectingGripPoints(point)
      return res


   def toggleSelectIntersectingGripPoints(self, point):
      for entityGripPoint in self.entityGripPoints:
         entityGripPoint.toggleSelectIntersectingGripPoints(point)


   def isIntersecting(self, point):
      for entityGripPoint in self.entityGripPoints:
         res = entityGripPoint.isIntersecting(point)
         if res is not None:
            return res 
      return None

      
   def getSelectedEntityGripPoints(self):
      # ritorna una lista delle entityGripPoint con dei grip point selezionati
      # la funzione non fa copie delle entityGripPoint
      result = []
      for entityGripPoint in self.entityGripPoints:
         for gripPoint in entityGripPoint.gripPoints:
            if gripPoint.getStatus() == QadGripStatusEnum.SELECTED:
               result.append(entityGripPoint)
      
      return result


   def containsEntity(self, entity):
      for entityGripPoint in self.entityGripPoints:
         if entityGripPoint.entity == entity:
            return True
      return False
   
   
   def count(self):
      return len(self.entityGripPoints)

