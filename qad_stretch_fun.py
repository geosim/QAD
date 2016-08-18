# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 funzioni per stirare oggetti grafici
 
                              -------------------
        begin                : 2013-11-11
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


import qad_utils
import qad_arc
import qad_circle
from qad_snapper import *


#===============================================================================
# isPtContainedForStretch
#===============================================================================
def isPtContainedForStretch(point, containerGeom, tolerance=None):
   """
   Funzione di ausilio per le funzioni di stretch (stretchPoint e stretchQgsLineStringGeometry).
   Se containerGeom è un oggetto QgsGeometry allora ritorna True se il punto è contenuto a livello spaziale
   dalla geometria containerGeom.
   Se containerGeom è una lista di punti allora ritorna True se il punto è fra quelli della lista.
   """
   if tolerance is None:
      tolerance = qad_utils.TOLERANCE
   if type(containerGeom) == QgsGeometry: # geometria   
      return containerGeom.contains(point)
   elif type(containerGeom) == list: # lista di punti
      for containerPt in containerGeom:
         if qad_utils.ptNear(containerPt, point, tolerance): # se i punti sono sufficientemente vicini
            return True
   return False 


#===============================================================================
# stretchPoint
#===============================================================================
def stretchPoint(point, containerGeom, offSetX, offSetY):
   """
   Stira il punto se è contenuto in containerGeom
   point = punto da stirare
   containerGeom = può essere una QgsGeometry rappresentante un poligono contenente i punti di geom da stirare
                   oppure una lista dei punti da stirare
   offSetX = spostamento X
   offSetY = spostamento Y
   """
   if isPtContainedForStretch(point, containerGeom): # se il punto è contenuto in containerGeom
      return qad_utils.movePoint(point, offSetX, offSetY)

   return None


#===============================================================================
# stretchQgsGeometry
#===============================================================================
def stretchQgsGeometry(geom, containerGeom, offSetX, offSetY, tolerance2ApproxCurve = None):
   """
   Stira una geometria
   geom = geometria da tirare
   containerGeom = può essere una QgsGeometry rappresentante un poligono contenente i punti di geom da stirare
                   oppure una lista dei punti di geom da stirare
   offSetX = spostamento X
   offSetY = spostamento Y
   tolerance2ApproxCurve = tolleranza per rigenerare le curve
   """   
   if tolerance2ApproxCurve == None:
      tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
   else:
      tolerance = tolerance2ApproxCurve

   wkbType = geom.wkbType()
   if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:
      pt = stretchPoint(geom.asPoint(), containerGeom, offSetX, offSetY)
      if pt is not None:
         return QgsGeometry.fromPoint(pt)
            
   if wkbType == QGis.WKBMultiPoint:
      stretchedGeom = QgsGeometry(geom)
      points = stretchedGeom.asMultiPoint() # vettore di punti
      atSubGeom = 0
      for pt in points:
         subGeom = QgsGeometry.fromPoint(pt)
         stretchedSubGeom = stretchQgsGeometry(subGeom, containerGeom, offSetX, offSetY, tolerance)
         stretchedGeom = qad_utils.setSubGeom(stretchedGeom, stretchedSubGeom, [atSubGeom])
         atSubGeom = atSubGeom + 1
      return stretchedGeom

   if wkbType == QGis.WKBLineString:
      return stretchQgsLineStringGeometry(geom, containerGeom, offSetX, offSetY, tolerance)
   
   if wkbType == QGis.WKBMultiLineString:
      stretchedGeom = QgsGeometry(geom)
      lines = stretchedGeom.asMultiPolyline() # lista di linee
      atSubGeom = 0
      for line in lines:        
         subGeom = QgsGeometry.fromPolyline(line)
         stretchedSubGeom = stretchQgsGeometry(subGeom, containerGeom, offSetX, offSetY, tolerance)
         stretchedGeom = qad_utils.setSubGeom(stretchedGeom, stretchedSubGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return stretchedGeom
         
   if wkbType == QGis.WKBPolygon:
      stretchedGeom = QgsGeometry(geom)
      lines = stretchedGeom.asPolygon() # lista di linee
      iRing = -1
      for line in lines:        
         subGeom = QgsGeometry.fromPolyline(line)
         stretchedSubGeom = gripStretchQgsGeometry(subGeom, basePt, ptListToStretch, offSetX, offSetY, tolerance)
         if iRing == -1: # si tratta della parte più esterna
            stretchedGeom = qad_utils.setSubGeom(stretchedGeom, stretchedSubGeom, [0])
         else:
            stretchedGeom = qad_utils.setSubGeom(stretchedGeom, stretchedSubGeom, [0, iRing])
         iRing = iRing + 1
      return stretchedGeom

   if wkbType == QGis.WKBMultiPolygon:
      stretchedGeom = QgsGeometry(geom)
      polygons = geom.asMultiPolygon() # vettore di poligoni
      iPart = 0
      for polygon in polygons:
         iRing = -1
         for line in polygon:
            subGeom = QgsGeometry.fromPolyline(line)
            stretchedSubGeom = gripStretchQgsGeometry(subGeom, basePt, ptListToStretch, offSetX, offSetY, tolerance)
            if iRing == -1: # si tratta della parte più esterna
               stretchedGeom = qad_utils.setSubGeom(stretchedGeom, stretchedSubGeom, [iPart])
            else:
               stretchedGeom = qad_utils.setSubGeom(stretchedGeom, stretchedSubGeom, [iPart, iRing])
            iRing = iRing + 1
         iPart = iPart + 1
      return stretchedGeom
   
   return None


#===============================================================================
# stretchQgsLineStringGeometry
#===============================================================================
def stretchQgsLineStringGeometry(geom, containerGeom, offSetX, offSetY, tolerance2ApproxCurve = None):
   """
   Stira i punti di una linestring che sono contenuti in containerGeom
   point = punto da tirare
   containerGeom = può essere una QgsGeometry rappresentante un poligono contenente i punti di geom da stirare
                   oppure una lista dei punti da stirare
   offSetX = spostamento X
   offSetY = spostamento Y
   """
   if tolerance2ApproxCurve == None:
      tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
   else:
      tolerance = tolerance2ApproxCurve

   obj = qad_utils.whatGeomIs(0, geom)
   if (type(obj) != list and type(obj) != tuple):
      objType = obj.whatIs()
      if objType == "CIRCLE": # se é cerchio
         if isPtContainedForStretch(obj.center, containerGeom): # se il punto è contenuto in containerGeom
            obj.center.setX(obj.center.x() + offSetX)
            obj.center.setY(obj.center.y() + offSetY)
         return QgsGeometry.fromPolyline(obj.asPolyline(tolerance))

   stretchedGeom = QgsGeometry(geom)
   snapper = QadSnapper()
   points = snapper.getEndPoints(stretchedGeom)
   del snapper

   linearObjectListToStretch = qad_utils.QadLinearObjectList()
   linearObjectListToStretch.fromPolyline(geom.asPolyline())
   
   for point in points:
      if isPtContainedForStretch(point, containerGeom): # se il punto è contenuto in containerGeom
         atPart = linearObjectListToStretch.containsPt(point)
         while atPart >= 0:
            linearObject = linearObjectListToStretch.getLinearObjectAt(atPart)
            pt = linearObject.getStartPt()        
            if qad_utils.ptNear(pt, point): # cambio punto iniziale
               pt.setX(pt.x() + offSetX)
               pt.setY(pt.y() + offSetY)
               if linearObject.isSegment():
                  linearObject.setStartPt(pt)
               else:
                  oldArc = linearObject.getArc()
                  middlePt = oldArc.getMiddlePt()
                  distFromMiddleChord = qad_utils.getDistance(middlePt, qad_utils.getPerpendicularPointOnInfinityLine(oldArc.getStartPt(), oldArc.getEndPt(), middlePt))
                  
                  newArc = QadArc()
                  if linearObject.isInverseArc():                  
                     middlePt = qad_utils.getMiddlePoint(pt, oldArc.getStartPt())
                     middlePt = qad_utils.getPolarPointByPtAngle(middlePt, \
                                                                 qad_utils.getAngleBy2Pts(pt, oldArc.getStartPt()) + math.pi / 2, \
                                                                 distFromMiddleChord)                  
                     if newArc.fromStartSecondEndPts(oldArc.getStartPt(), middlePt, pt) == False:
                        return None
                  else:
                     middlePt = qad_utils.getMiddlePoint(pt, oldArc.getEndPt())
                     middlePt = qad_utils.getPolarPointByPtAngle(middlePt, \
                                                                 qad_utils.getAngleBy2Pts(pt, oldArc.getEndPt()) - math.pi / 2, \
                                                                 distFromMiddleChord)                  
                     if newArc.fromStartSecondEndPts(pt, middlePt, oldArc.getEndPt()) == False:
                        return None
                  linearObject.setArc(newArc, linearObject.isInverseArc())         
            else:
               pt = linearObject.getEndPt()
               if qad_utils.ptNear(pt, point): # cambio punto finale
                  pt.setX(pt.x() + offSetX)
                  pt.setY(pt.y() + offSetY)
                  if linearObject.isSegment():
                     linearObject.setEndPt(pt)
                  else:
                     oldArc = linearObject.getArc()
                     middlePt = oldArc.getMiddlePt()
                     distFromMiddleChord = qad_utils.getDistance(middlePt, qad_utils.getPerpendicularPointOnInfinityLine(oldArc.getStartPt(), oldArc.getEndPt(), middlePt))
                     
                     newArc = QadArc()
                     if linearObject.isInverseArc():
                        middlePt = qad_utils.getMiddlePoint(pt, oldArc.getEndPt())
                        middlePt = qad_utils.getPolarPointByPtAngle(middlePt, \
                                                                    qad_utils.getAngleBy2Pts(pt, oldArc.getEndPt()) - math.pi / 2, \
                                                                    distFromMiddleChord)                  
                        if newArc.fromStartSecondEndPts(pt, middlePt, oldArc.getEndPt()) == False:
                           return None
                     else:
                        middlePt = qad_utils.getMiddlePoint(pt, oldArc.getStartPt())
                        middlePt = qad_utils.getPolarPointByPtAngle(middlePt, \
                                                                    qad_utils.getAngleBy2Pts(pt, oldArc.getStartPt()) + math.pi / 2, \
                                                                    distFromMiddleChord)                  
                        if newArc.fromStartSecondEndPts(oldArc.getStartPt(), middlePt, pt) == False:
                           return None
                     linearObject.setArc(newArc, linearObject.isInverseArc())            
                  
            atPart = linearObjectListToStretch.containsPt(point, atPart + 1)
            
   pts = linearObjectListToStretch.asPolyline(tolerance)
   stretchedGeom = QgsGeometry.fromPolyline(pts)    
      
   return stretchedGeom   


####################################################################
# Funzioni di stretch per grip point
####################################################################


#===============================================================================
# gripStretchQgsGeometry
#===============================================================================
def gripStretchQgsGeometry(geom, basePt, ptListToStretch, offSetX, offSetY, tolerance2ApproxCurve = None):
   """
   Stira una geometria in coordinate piane mediante grip point
   geom = geometria da stirare
   ptListToStretch = lista dei punti di geom da stirare
   offSetX = spostamento X
   offSetY = spostamento Y
   tolerance2ApproxCurve = tolleranza per rigenerare le curve
   """
   if tolerance2ApproxCurve == None:
      tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
   else:
      tolerance = tolerance2ApproxCurve
   
   wkbType = geom.wkbType()
   if wkbType == QGis.WKBPoint or wkbType == QGis.WKBPoint25D:
      pt = stretchPoint(geom.asPoint(), ptListToStretch, offSetX, offSetY)
      if pt is not None:
         return QgsGeometry.fromPoint(pt)
            
   if wkbType == QGis.WKBMultiPoint:
      stretchedGeom = QgsGeometry(geom)
      points = stretchedGeom.asMultiPoint() # vettore di punti
      atSubGeom = 0
      for pt in points:
         subGeom = QgsGeometry.fromPoint(pt)
         stretchedSubGeom = gripStretchQgsGeometry(subGeom, basePt, ptListToStretch, offSetX, offSetY, tolerance)
         stretchedGeom = qad_utils.setSubGeom(stretchedGeom, stretchedSubGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return stretchedGeom

   if wkbType == QGis.WKBLineString:
      return gripStretchQgsLineStringGeometry(geom, basePt, ptListToStretch, offSetX, offSetY, tolerance)
   
   if wkbType == QGis.WKBMultiLineString:
      stretchedGeom = QgsGeometry(geom)
      lines = stretchedGeom.asMultiPolyline() # lista di linee
      atSubGeom = 0
      for line in lines:        
         subGeom = QgsGeometry.fromPolyline(line)
         stretchedSubGeom = gripStretchQgsGeometry(subGeom, basePt, ptListToStretch, offSetX, offSetY, tolerance)
         stretchedGeom = qad_utils.setSubGeom(stretchedGeom, stretchedSubGeom, [atSubGeom])    
         atSubGeom = atSubGeom + 1
      return stretchedGeom
         
   if wkbType == QGis.WKBPolygon:
      stretchedGeom = QgsGeometry(geom)
      lines = stretchedGeom.asPolygon() # lista di linee
      iRing = -1
      for line in lines:        
         subGeom = QgsGeometry.fromPolyline(line)
         stretchedSubGeom = gripStretchQgsGeometry(subGeom, basePt, ptListToStretch, offSetX, offSetY, tolerance)
         if iRing == -1: # si tratta della parte più esterna
            stretchedGeom = qad_utils.setSubGeom(stretchedGeom, stretchedSubGeom, [0])
         else:
            stretchedGeom = qad_utils.setSubGeom(stretchedGeom, stretchedSubGeom, [0, iRing])
         iRing = iRing + 1
      return stretchedGeom
      
   if wkbType == QGis.WKBMultiPolygon:
      stretchedGeom = QgsGeometry(geom)
      polygons = geom.asMultiPolygon() # vettore di poligoni
      iPart = 0
      for polygon in polygons:
         iRing = -1
         for line in polygon:
            subGeom = QgsGeometry.fromPolyline(line)
            stretchedSubGeom = gripStretchQgsGeometry(subGeom, basePt, ptListToStretch, offSetX, offSetY, tolerance)
            if iRing == -1: # si tratta della parte più esterna
               stretchedGeom = qad_utils.setSubGeom(stretchedGeom, stretchedSubGeom, [iPart])
            else:
               stretchedGeom = qad_utils.setSubGeom(stretchedGeom, stretchedSubGeom, [iPart, iRing])
            iRing = iRing + 1
         iPart = iPart + 1
      return stretchedGeom
   
   return None


#===============================================================================
# gripStretchQadGeometry
#===============================================================================
def gripStretchQadGeometry(geom, basePt, ptListToStretch, offSetX, offSetY, tolerance2ApproxCurve = None):
   """
   Stira una entità qad in coordinate piane mediante grip point
   geom = entità qad da stirare
   ptListToStretch = lista dei punti di geom da stirare
   offSetX = spostamento X
   offSetY = spostamento Y
   tolerance2ApproxCurve = tolleranza per rigenerare le curve
   """
   if tolerance2ApproxCurve == None:
      tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
   else:
      tolerance = tolerance2ApproxCurve

   if type(geom) == list: # entità composta da più geometrie
      res = []
      for subGeom in geom:
         res.append(gripStretchQadGeometry(subGeom, basePt, ptListToStretch, offSetX, offSetY, tolerance))
      return res
   else:
      if type(geom) == QgsPoint:
         return stretchPoint(geom, ptListToStretch, offSetX, offSetY)
      elif geom.whatIs() == "ARC":
         return gripStretchArc(geom, ptListToStretch, offSetX, offSetY, tolerance)
      elif geom.whatIs() == "CIRCLE":
         return gripStretchCircle(geom, basePt, ptListToStretch, offSetX, offSetY, tolerance)
      elif geom.whatIs() == "LINEAROBJS":
         return gripStretchQgsLinearObjectList(geom, ptListToStretch, offSetX, offSetY, tolerance)

   return None


#===============================================================================
# gripStretchCircle
#===============================================================================
def gripStretchCircle(circle, basePt, ptListToStretch, offSetX, offSetY, tolerance2ApproxCurve):
   """
   Stira i punti di grip di un cerchio che sono contenuti in ptListToStretch
   circle = cerchio da stirare
   basePt = punto base
   ptListToStretch = lista dei punti da stirare
   offSetX = spostamento X
   offSetY = spostamento Y
   """
   if tolerance2ApproxCurve == None:
      tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
   else:
      tolerance = tolerance2ApproxCurve
   
   newCenter = QgsPoint(circle.center)
   newRadius = circle.radius
   
   for ptToStretch in ptListToStretch:
      if qad_utils.ptNear(ptToStretch, circle.center): # se i punti sono sufficientemente vicini
         newCenter.set(circle.center.x() + offSetX, circle.center.y() + offSetY)
      elif circle.isPtOnCircle(ptToStretch):
         newPt = QgsPoint(basePt.x() + offSetX, basePt.y() + offSetY)
         newRadius = qad_utils.getDistance(circle.center, newPt)

   newCircle = qad_circle.QadCircle()
   if newCircle.set(newCenter, newRadius) == False:
      return None
   
   return newCircle


#===============================================================================
# gripStretchArc
#===============================================================================
def gripStretchArc(arc, ptListToStretch, offSetX, offSetY, tolerance2ApproxCurve, inverseArc = None):
   """
   Stira i punti di grip di un arco che sono contenuti in ptListToStretch
   arc = arco da stirare
   ptListToStretch = lista dei punti da stirare
   offSetX = spostamento X
   offSetY = spostamento Y
   """
   if tolerance2ApproxCurve == None:
      tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
   else:
      tolerance = tolerance2ApproxCurve
   
   startPt = arc.getStartPt()
   endPt = arc.getEndPt()
   middlePt = arc.getMiddlePt()
   newStartPt = QgsPoint(startPt)
   newEndPt = QgsPoint(endPt)
   newMiddlePt = QgsPoint(middlePt)
   newCenter = None
   startPtChanged = endPtChanged = middlePtPtChanged = False
   for ptToStretch in ptListToStretch:
      if qad_utils.ptNear(ptToStretch, arc.center): # se i punti sono sufficientemente vicini
         newCenter = QgsPoint(arc.center.x() + offSetX, arc.center.y() + offSetY)
      else:
         if qad_utils.ptNear(startPt, ptToStretch):
            newStartPt.set(startPt.x() + offSetX, startPt.y() + offSetY)
            startPtChanged = True
         elif qad_utils.ptNear(endPt, ptToStretch):
            newEndPt.set(endPt.x() + offSetX, endPt.y() + offSetY)
            endPtChanged = True
         elif qad_utils.ptNear(middlePt, ptToStretch):
            newMiddlePt.set(middlePt.x() + offSetX, middlePt.y() + offSetY)
            middlePtPtChanged = True
   
   newArc = qad_arc.QadArc()
   if newArc.fromStartSecondEndPts(newStartPt, newMiddlePt, newEndPt) == False:
      return None
   
   # se il centro era nei punti di grip
   if newCenter is not None:
      # se i tre punti dell'arco erano nei punti di grip oppure
      # allora non cambio il centro
      if (startPtChanged and endPtChanged and middlePtPtChanged):
         pass
      else:
         newArc.center.set(newCenter.x(), newCenter.y())
      
   if inverseArc is not None: # se l'arco faceva parte di una linestring
      # verifico il verso del nuovo arco
      if qad_utils.ptNear(newStartPt, newArc.getStartPt()):
         # stesso verso del vecchio arco
         return newArc, inverseArc
      else:
         return newArc, not inverseArc
      
   return newArc


#===============================================================================
# gripStretchQgsLineStringGeometry
#===============================================================================
def gripStretchQgsLineStringGeometry(geom, basePt, ptListToStretch, offSetX, offSetY, tolerance2ApproxCurve):
   """
   Stira i punti di grip di una linestring che sono contenuti in ptListToStretch
   geom = geometria da stirare
   basePt = punto base
   ptListToStretch = lista dei punti da stirare
   offSetX = spostamento X
   offSetY = spostamento Y
   """
   if tolerance2ApproxCurve == None:
      tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
   else:
      tolerance = tolerance2ApproxCurve
   
   obj = qad_utils.whatGeomIs(0, geom)
   if (type(obj) != list and type(obj) != tuple):
      objType = obj.whatIs()
      if objType == "CIRCLE": # se é cerchio
         newCircle = gripStretchCircle(obj, basePt, ptListToStretch, offSetX, offSetY, tolerance)
         if newCircle is not None:
            return QgsGeometry.fromPolyline(newCircle.asPolyline(tolerance))
      elif objType == "ARC": # se é arco
         newArc = gripStretchArc(obj, ptListToStretch, offSetX, offSetY, tolerance)
         if newArc is not None:
            return QgsGeometry.fromPolyline(newArc.asPolyline(tolerance))
      return None
   
   linearObjectListToStretch = qad_utils.QadLinearObjectList()
   linearObjectListToStretch.fromPolyline(geom.asPolyline())
   
   atPart = 0
   while atPart < linearObjectListToStretch.qty():
      linearObject = linearObjectListToStretch.getLinearObjectAt(atPart)
      if linearObject.isSegment():
         pt = linearObject.getStartPt()
         if isPtContainedForStretch(pt, ptListToStretch): # se il punto è contenuto in ptListToStretch
            # cambio punto iniziale        
            pt.setX(pt.x() + offSetX)
            pt.setY(pt.y() + offSetY)
            linearObject.setStartPt(pt)
            
         pt = linearObject.getEndPt()
         if isPtContainedForStretch(pt, ptListToStretch): # se il punto è contenuto in ptListToStretch
            # cambio punto finale
            pt.setX(pt.x() + offSetX)
            pt.setY(pt.y() + offSetY)
            linearObject.setEndPt(pt)
      else: # se è arco
         newArc, newInverseFlag = gripStretchArc(linearObject.getArc(), ptListToStretch, offSetX, offSetY, tolerance, linearObject.isInverseArc())
         if newArc is None:
            return None
         linearObject.setArc(newArc, newInverseFlag)

      atPart = atPart + 1
   
   pt = linearObjectListToStretch.getCentroid(tolerance) # verifico se polilinea ha un centroide
   if pt is not None:
      if isPtContainedForStretch(pt, ptListToStretch): # se il punto è contenuto in ptListToStretch
         linearObjectListToStretch.move(offSetX, offSetY)
   
   pts = linearObjectListToStretch.asPolyline(tolerance)
   stretchedGeom = QgsGeometry.fromPolyline(pts)    
      
   return stretchedGeom   


#===============================================================================
# gripStretchQgsLinearObjectList
#===============================================================================
def gripStretchQgsLinearObjectList(linearObjectList, ptListToStretch, offSetX, offSetY, tolerance2ApproxCurve):
   """
   Stira i punti di grip di una linestring che sono contenuti in ptListToStretch
   linearObjectListToStretch = geometria da stirare
   ptListToStretch = lista dei punti da stirare
   offSetX = spostamento X
   offSetY = spostamento Y
   """
   if tolerance2ApproxCurve == None:
      tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
   else:
      tolerance = tolerance2ApproxCurve
   
   linearObjectListToStretch = qad_utils.QadLinearObjectList(linearObjectList)
   
   atPart = 0
   while atPart < linearObjectListToStretch.qty():
      linearObject = linearObjectListToStretch.getLinearObjectAt(atPart)      
      if linearObject.isSegment():
         pt = linearObject.getStartPt()
         if isPtContainedForStretch(pt, ptListToStretch): # se il punto è contenuto in ptListToStretch
            # cambio punto iniziale        
            pt.setX(pt.x() + offSetX)
            pt.setY(pt.y() + offSetY)
            linearObject.setStartPt(pt)
            
         pt = linearObject.getEndPt()
         if isPtContainedForStretch(pt, ptListToStretch): # se il punto è contenuto in ptListToStretch
            # cambio punto finale
            pt.setX(pt.x() + offSetX)
            pt.setY(pt.y() + offSetY)
            linearObject.setEndPt(pt)
      else: # se è arco
         newArc, newInverseFlag = gripStretchArc(linearObject.getArc(), ptListToStretch, offSetX, offSetY, tolerance, linearObject.isInverseArc())
         if newArc is None:
            return None
         linearObject.setArc(newArc, newInverseFlag)

      atPart = atPart + 1
   
   pt = linearObjectListToStretch.getCentroid(tolerance) # verifico se polilinea ha un centroide
   if pt is not None:
      if isPtContainedForStretch(pt, ptListToStretch): # se il punto è contenuto in ptListToStretch
         linearObjectListToStretch.move(offSetX, offSetY)

   return linearObjectListToStretch