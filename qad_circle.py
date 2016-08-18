# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per la gestione dei cerchi
 
                              -------------------
        begin                : 2013-05-22
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
import sys

import qad_utils
from qad_variables import *
from qad_arc import *
from qad_msg import QadMsg


#===============================================================================
# QadArc arc class
#===============================================================================
class QadCircle():
    
   def __init__(self, circle = None):
      if circle is not None:
         self.set(circle.center, circle.radius)
      else:    
         self.center = None
         self.radius = None

   def whatIs(self):
      return "CIRCLE"

   def set(self, center, radius):
      if radius <=0:
         return False
      self.center = QgsPoint(center)
      self.radius = radius
      return True

   def transform(self, ct):
      """Transform this geometry as described by CoordinateTranasform ct."""
      self.center = coordTransform.transform(self.center)      

   def transformFromCRSToCRS(self, sourceCRS, destCRS):
      """Transform this geometry as described by CRS."""
      if (sourceCRS is not None) and (destCRS is not None) and sourceCRS != destCRS:       
         coordTransform = QgsCoordinateTransform(sourceCRS, destCRS) # trasformo le coord
         self.center =  coordTransform.transform(self.center)
   
   def __eq__(self, circle):
      """self == other"""
      if self.center != circle.center or self.radius != circle.radius:
         return False
      else:
         return True    
  
   def __ne__(self, circle):
      """self != other"""
      if self.center != circle.center or self.radius != circle.radius:
         return True     
      else:
         return False             
   
   def length(self):
      return 2 * math.pi * self.radius

   def lengthBetween2Points(self, pt1, pt2, leftOfPt1):
      """
      Calcola la distanza tra 2 punti sulla circonferenza. L'arco considerato può essere
      quello a sinistra o a destra di <pt1> (vedi <leftOfPt1>)
      se <leftOfPt1> é boolean allora se = True viene considerato l'arco a sin di pt1
      se <leftOfPt1> é float allora significa che si tratta della direzione della tangente su pt1
                     e se la direzione è a sin viene considerato l'arco a sin di pt1
      """
      if qad_utils.ptNear(pt1, pt2): # se i punti sono così vicini da essere considerati uguali
         return 0
      
      if type(leftOfPt1) == float: # direzione della tangente su pt1 
         startAngle = qad_utils.getAngleBy2Pts(self.center, pt1)         
         if qad_utils.doubleNear(qad_utils.normalizeAngle(startAngle + math.pi / 2), 
                                 qad_utils.normalizeAngle(leftOfPt1)):
            _leftOfPt1 = True
         else:
            _leftOfPt1 = False
      else: # booolean
         _leftOfPt1 = leftOfPt1
      
      if _leftOfPt1: # arco a sinistra di pt1
         startAngle = qad_utils.getAngleBy2Pts(self.center, pt1)         
         endAngle = qad_utils.getAngleBy2Pts(self.center, pt2)
      else: # arco a destra di pt1
         startAngle = qad_utils.getAngleBy2Pts(self.center, pt2)
         endAngle = qad_utils.getAngleBy2Pts(self.center, pt1)         

      if startAngle < endAngle:
         totalAngle = endAngle - startAngle
      else:
         totalAngle =  (2 * math.pi - startAngle) + endAngle
      
      return self.radius * totalAngle

   def area(self):
      return math.pi * self.radius * self.radius

   def isPtOnCircle(self, point):
      dist = qad_utils.getDistance(self.center, point)
      return qad_utils.doubleNear(self.radius, dist)

   def getQuadrantPoints(self):
      # ritorna i punti quadranti: pt in alto, pt in basso, a destra, a sinistra del centro
      pt1 = QgsPoint(self.center.x(), self.center.y() + self.radius)
      pt2 = QgsPoint(self.center.x(), self.center.y()- self.radius)
      pt3 = QgsPoint(self.center.x() + self.radius, self.center.y())
      pt4 = QgsPoint(self.center.x() - self.radius, self.center.y())
      return [pt1, pt2, pt3, pt4]

   
   def getTanPoints(self, point):
      dist = qad_utils.getDistance(self.center, point)
      if dist < self.radius:
         return []
      if dist == self.radius:
         return [point]
      
      angleOffSet = math.asin(self.radius / dist)
      angleOffSet = (math.pi / 2) - angleOffSet
      angle = qad_utils.getAngleBy2Pts(self.center, point)
      
      pt1 = qad_utils.getPolarPointByPtAngle(self.center, angle + angleOffSet, self.radius)
      pt2 = qad_utils.getPolarPointByPtAngle(self.center, angle - angleOffSet, self.radius)     
      return [pt1, pt2]
   

   def getPerpendicularPoints(self, point):
      angle = qad_utils.getAngleBy2Pts(self.center, point)     
      pt1 = qad_utils.getPolarPointByPtAngle(self.center, angle, self.radius)     
      pt2 = qad_utils.getPolarPointByPtAngle(self.center, angle + math.pi, self.radius)
      return [pt1, pt2]      


   def getIntersectionPointsWithCircle(self, circle):
      result = []
      # se i punti sono così vicini da essere considerati uguali 
      if qad_utils.ptNear(self.center, circle.center): # stesso centro
         return result
      distFromCenters = qad_utils.getDistance(self.center, circle.center)
      distFromCirc = distFromCenters - self.radius - circle.radius

      # se è così vicino allo zero da considerarlo = 0
      if qad_utils.doubleNear(distFromCirc, 0):
         angle = qad_utils.getAngleBy2Pts(self.center, circle.center)
         result.append(qad_utils.getPolarPointByPtAngle(self.center, angle, self.radius))
         return result
         
      if distFromCirc > 0: # i cerchi sono troppo distanti
         return result

      x2_self = self.center.x() * self.center.x() # X del centro del cerchio <self> al quadrato
      x2_circle = circle.center.x() * circle.center.x() # Y del centro del cerchio <circle> al quadrato
      radius2_self = self.radius * self.radius # raggio del cerchio <self> al quadrato
      radius2_circle = circle.radius * circle.radius # raggio del cerchio <circle> al quadrato
      
      if qad_utils.doubleNear(self.center.y(), circle.center.y()):
         x1 = x2_circle - x2_self + radius2_self - radius2_circle
         x1 = x1 / (2 * (circle.center.x() - self.center.x()))
         x2 = x1         
         D = radius2_self - ((x1 - self.center.x()) * (x1 - self.center.x()))
         # se D è così vicino a zero 
         if qad_utils.doubleNear(D, 0.0):
            D = 0
         elif D < 0: # non si può fare la radice quadrata di un numero negativo
            return result
         E = math.sqrt(D)
         
         y1 = self.center.y() + E
         y2 = self.center.y() - E
      else:
         y2_self = self.center.y() * self.center.y() # Y del centro del cerchio <self> al quadrato
         y2_circle = circle.center.y() * circle.center.y() # Y del centro del cerchio <circle> al quadrato
         
         a = (self.center.x() - circle.center.x()) / (circle.center.y() - self.center.y())
         b = x2_circle - x2_self + y2_circle - y2_self + radius2_self - radius2_circle 
         b = b / (2 * (circle.center.y() - self.center.y()))
         
         A = 1 + (a * a)
         B = (2 * a * b) - (2 * self.center.x()) - (2 * a * self.center.y())
         C = (b * b) - (2 * self.center.y() * b) + x2_self + y2_self - radius2_self
         D = (B * B) - (4 * A * C)
         # se D è così vicino a zero 
         if qad_utils.doubleNear(D, 0.0):
            D = 0
         elif D < 0: # non si può fare la radice quadrata di un numero negativo
            return result
         E = math.sqrt(D)
         
         x1 = (-B + E) / (2 * A)
         y1 = a * x1 + b
   
         x2 = (-B - E) / (2 * A)           
         y2 = a * x2 + b
      
      result.append(QgsPoint(x1, y1))
      if x1 != x2 or y1 != y2: # i punti non sono coincidenti
         result.append(QgsPoint(x2, y2))
      
      return result


   def getIntersectionPointsWithInfinityLine(self, p1, p2):
      result = []
      if p1 == p2:
         return result

      x2_self = self.center.x() * self.center.x() # X del centro del cerchio <self> al quadrato
      y2_self = self.center.y() * self.center.y() # Y del centro del cerchio <self> al quadrato
      radius2_self = self.radius * self.radius # raggio del cerchio <self> al quadrato
      
      diffX = p2.x() - p1.x()
      # se diffX è così vicino a zero 
      if qad_utils.doubleNear(diffX, 0.0): # se la retta passante per p1 e p2 é verticale
         B = -2 * self.center.y()
         C = x2_self + y2_self + (p1.x() * p1.x()) - (2* p1.x() * self.center.x()) - radius2_self
         D = (B * B) - (4 * C) 
         # se D è così vicino a zero 
         if qad_utils.doubleNear(D, 0.0):
            D = 0
         elif D < 0: # non si può fare la radice quadrata di un numero negativo
            return result
         E = math.sqrt(D)
         
         y1 = (-B + E) / 2        
         x1 = p1.x()
         
         y2 = (-B - E) / 2        
         x2 = p1.x()
      else:
         m = (p2.y() - p1.y()) / diffX
         q = p1.y() - (m * p1.x())
         A = 1 + (m * m)
         B = (2 * m * q) - (2 * self.center.x()) - (2 * m * self.center.y())
         C = x2_self + (q * q) + y2_self - (2 * q * self.center.y()) - radius2_self
              
         D = (B * B) - 4 * A * C
         # se D è così vicino a zero 
         if qad_utils.doubleNear(D, 0.0):
            D = 0
         elif D < 0: # non si può fare la radice quadrata di un numero negativo
            return result
         E = math.sqrt(D)
      
         x1 = (-B + E) / (2 * A)
         y1 = p1.y() + m * x1 - m * p1.x()
   
         x2 = (-B - E) / (2 * A)
         y2 = p1.y() + m * x2 - m * p1.x()
      
      result.append(QgsPoint(x1, y1))
      if x1 != x2 or y1 != y2: # i punti non sono coincidenti
         result.append(QgsPoint(x2, y2))
      
      return result


   #============================================================================
   # getIntersectionPointsWithSegment
   #============================================================================
   def getIntersectionPointsWithSegment(self, p1, p2):
      result = []
      intPtList = self.getIntersectionPointsWithInfinityLine(p1, p2)
      for intPt in intPtList:
         if qad_utils.isPtOnSegment(p1, p2, intPt):
            result.append(intPt)
      return result


   #============================================================================
   # getTangentsWithCircle
   #============================================================================
   def getTangentsWithCircle(self, circle):
      """
      la funzione ritorna una lista di linee che sono le tangenti ai due cerchi
      """
      tangents = []
      
      x1 = self.center[0]
      y1 = self.center[1]
      r1 = self.radius
      x2 = circle.center[0]
      y2 = circle.center[1]
      r2 = circle.radius

      d_sq = (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2)
      if (d_sq <= (r1-r2)*(r1-r2)):
          return tangents
 
      d = math.sqrt(d_sq);
      vx = (x2 - x1) / d;
      vy = (y2 - y1) / d;
 
      # Let A, B be the centers, and C, D be points at which the tangent
      # touches first and second circle, and n be the normal vector to it.
      #
      # We have the system:
      #   n * n = 1          (n is a unit vector)          
      #   C = A + r1 * n
      #   D = B +/- r2 * n
      #   n * CD = 0         (common orthogonality)
      #
      # n * CD = n * (AB +/- r2*n - r1*n) = AB*n - (r1 -/+ r2) = 0,  <=>
      # AB * n = (r1 -/+ r2), <=>
      # v * n = (r1 -/+ r2) / d,  where v = AB/|AB| = AB/d
      # This is a linear equation in unknown vector n.
      sign1 = +1
      while sign1 >= -1:
         c = (r1 - sign1 * r2) / d;
 
         # Now we're just intersecting a line with a circle: v*n=c, n*n=1
 
         if (c*c > 1.0):
            sign1 = sign1 - 2
            continue
         
         h = math.sqrt(max(0.0, 1.0 - c*c));

         sign2 = +1
         while sign2 >= -1:
            nx = vx * c - sign2 * h * vy;
            ny = vy * c + sign2 * h * vx;

            tangent = []
            tangent.append(QgsPoint(x1 + r1 * nx, y1 + r1 * ny))
            tangent.append(QgsPoint(x2 + sign1 * r2 * nx, y2 + sign1 * r2 * ny))
            tangents.append(tangent)
            sign2 = sign2 - 2
            
         sign1 = sign1 - 2
 
      return tangents    


   #============================================================================
   # asPolyline
   #============================================================================
   def asPolyline(self, tolerance2ApproxCurve = None, atLeastNSegment = None):
      """
      ritorna una lista di punti che definisce il cerchio
      """
      
      if tolerance2ApproxCurve is None:
         tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
      else:
         tolerance = tolerance2ApproxCurve

      if atLeastNSegment is None:
         _atLeastNSegment = QadVariables.get(QadMsg.translate("Environment variables", "CIRCLEMINSEGMENTQTY"), 12)
      else:
         _atLeastNSegment = atLeastNSegment
      
      # Calcolo la lunghezza del segmento con pitagora
      dummy      = self.radius - tolerance
      if dummy <= 0: # se la tolleranza è troppo bassa rispetto al raggio
         SegmentLen = self.radius
      else:
         dummy      = (self.radius * self.radius) - (dummy * dummy)
         SegmentLen = math.sqrt(dummy) # radice quadrata
         SegmentLen = SegmentLen * 2

      if SegmentLen == 0: # se la tolleranza è troppo bassa la lunghezza del segmento diventa zero  
         return None

      # calcolo quanti segmenti ci vogliono (non meno di _atLeastNSegment)
      SegmentTot = math.ceil(self.length() / SegmentLen)
      if SegmentTot < _atLeastNSegment:
         SegmentTot = _atLeastNSegment
      
      points = []
      # primo punto
      firsPt = qad_utils.getPolarPointByPtAngle(self.center, 0, self.radius)
      points.append(firsPt)

      i = 1
      angle = 0
      offSetAngle = 2 * math.pi / SegmentTot
      while i < SegmentTot:
         angle = angle + offSetAngle
         pt = qad_utils.getPolarPointByPtAngle(self.center, angle, self.radius)
         points.append(pt)         
         i = i + 1

      # ultimo punto (come il primo)
      points.append(firsPt)
      return points


   #============================================================================
   # fromPolyline
   #============================================================================
   def fromPolyline(self, points, atLeastNSegment = None):
      """
      setta le caratteristiche del cerchio incontrato nella lista di punti
      ritorna True se é stato trovato un cerchio altrimenti False.
      N.B. in punti NON devono essere in coordinate geografiche
      """
      totPoints = len(points)

      # il primo e l'ultimo punto devono coincidere
      if qad_utils.ptNear(points[0], points[totPoints-1]) == False: return False
      
      if atLeastNSegment is None:
         _atLeastNSegment = QadVariables.get(QadMsg.translate("Environment variables", "CIRCLEMINSEGMENTQTY"), 12)
      else:
         _atLeastNSegment = atLeastNSegment
      
      # perché sia un cerchio ci vogliono almeno _atLeastNSegment segmenti
      if (totPoints - 1) < _atLeastNSegment or _atLeastNSegment < 2:
         return False

      # per problemi di approssimazione dei calcoli
      epsilon = 1.e-4 # percentuale del raggio per ottenere max diff. di una distanza con il raggio

      InfinityLinePerpOnMiddle1 = None
      InfinityLinePerpOnMiddle2 = None
                 
      nSegment = 0
      i = 0
      while i < totPoints - 1:
         if InfinityLinePerpOnMiddle1 is None:
            InfinityLinePerpOnMiddle1 = qad_utils.getInfinityLinePerpOnMiddle(points[i], points[i + 1])
            nSegment = 1
            i = i + 1
            continue
         elif InfinityLinePerpOnMiddle2 is None:     
            InfinityLinePerpOnMiddle2 = qad_utils.getInfinityLinePerpOnMiddle(points[i], points[i + 1])
            if InfinityLinePerpOnMiddle2 is None:       
               InfinityLinePerpOnMiddle1 = None
               nSegment = 0
            else:
               # calcolo il presunto centro con 2 segmenti
               center = qad_utils.getIntersectionPointOn2InfinityLines(InfinityLinePerpOnMiddle1[0], \
                                                                       InfinityLinePerpOnMiddle1[1], \
                                                                       InfinityLinePerpOnMiddle2[0], \
                                                                       InfinityLinePerpOnMiddle2[1])
               if center is None: # linee parallele
                  InfinityLinePerpOnMiddle1 = InfinityLinePerpOnMiddle2
                  InfinityLinePerpOnMiddle2 = None
                  nSegment = 1
               else:
                  nSegment = nSegment + 1
                  radius = qad_utils.getDistance(center, points[i + 1]) # calcolo il presunto raggio
                  tolerance = radius * epsilon
                  
                  # calcolo il verso dell'arco e l'angolo dell'arco
                  # se un punto intermedio dell'arco è a sinistra del
                  # segmento che unisce i due punti allora il verso è antiorario
                  startClockWise = True if qad_utils.leftOfLine(points[i], points[i - 1], points[i + 1]) < 0 else False
                  angle = qad_utils.getAngleBy3Pts(points[i - 1], center, points[i + 1], startClockWise)                                    
                  prevInfinityLinePerpOnMiddle = InfinityLinePerpOnMiddle2
         else: # e sono già stati valutati almeno 2 segmenti
            notInCircle = False
            currInfinityLinePerpOnMiddle = qad_utils.getInfinityLinePerpOnMiddle(points[i], points[i + 1])
            if currInfinityLinePerpOnMiddle is None:
               notInCircle = True
            else:
               # calcolo il presunto centro con 2 segmenti
               currCenter = qad_utils.getIntersectionPointOn2InfinityLines(prevInfinityLinePerpOnMiddle[0], \
                                                                           prevInfinityLinePerpOnMiddle[1], \
                                                                           currInfinityLinePerpOnMiddle[0], \
                                                                           currInfinityLinePerpOnMiddle[1])
               if currCenter is None: # linee parallele
                  return False
               else:
                  # calcolo il verso dell'arco e l'angolo                 
                  clockWise = True if qad_utils.leftOfLine(points[i], points[i - 1], points[i + 1]) < 0 else False           
                  angle = angle + qad_utils.getAngleBy3Pts(points[i], center, points[i + 1], startClockWise) 
                             
                  # se la distanza è così vicina a quella del raggio
                  # il verso dell'arco deve essere quello iniziale
                  # l'angolo dell'arco non può essere >= 360 gradi
                  if qad_utils.ptNear(center, currCenter, tolerance) and \
                     startClockWise == clockWise and \
                     (angle < 2 * math.pi or qad_utils.doubleNear(angle, 2 * math.pi)):
                     nSegment = nSegment + 1 # anche questo segmento fa parte dell'arco
                     prevInfinityLinePerpOnMiddle = currInfinityLinePerpOnMiddle
                  else:
                     return False

         i = i + 1

      # se sono stati trovati un numero sufficiente di segmenti successivi
      if nSegment >= _atLeastNSegment:
         self.center = center
         self.radius = radius               
         return True

      return False


   #============================================================================
   # fromCenterPtArea
   #============================================================================
   def fromCenterArea(self, centerPt, area):
      """
      setta le caratteristiche del cerchio attraverso:
      il punto centrale
      area
      """
      if centerPt is None or area <= 0:
         return False
      self.center = centerPt
      self.radius = math.sqrt(area / math.pi)
      return True


   #============================================================================
   # from3Pts
   #============================================================================
   def from3Pts(self, firstPt, secondPt, thirdPt):
      """
      setta le caratteristiche del cerchio attraverso:
      punto iniziale
      secondo punto (intermedio)
      punto finale
      """
      InfinityLinePerpOnMiddle1 = qad_utils.getInfinityLinePerpOnMiddle(firstPt, secondPt)
      InfinityLinePerpOnMiddle2 = qad_utils.getInfinityLinePerpOnMiddle(secondPt, thirdPt)
      if InfinityLinePerpOnMiddle1 is None or InfinityLinePerpOnMiddle2 is None:
         return False
      self.center = qad_utils.getIntersectionPointOn2InfinityLines(InfinityLinePerpOnMiddle1[0], \
                                                                   InfinityLinePerpOnMiddle1[1], \
                                                                   InfinityLinePerpOnMiddle2[0], \
                                                                   InfinityLinePerpOnMiddle2[1])
      if self.center is None: # linee parallele
         return False
      self.radius = qad_utils.getDistance(self.center, firstPt)
      return True


   #============================================================================
   # from3TanPts
   #============================================================================
   def from3TanPts(self, geom1, pt1, geom2, pt2, geom3, pt3):
      """
      setta le caratteristiche del cerchio attraverso
      tre oggetti di tangenza per le estremità del diametro:
      geometria 1 di tangenza (linea, arco o cerchio)
      punto di selezione geometria 1
      geometria 2 di tangenza (linea, arco o cerchio)
      punto di selezione geometria 2
      """
      obj1 = qad_utils.whatGeomIs(pt1, geom1)
      obj2 = qad_utils.whatGeomIs(pt2, geom2)
      obj3 = qad_utils.whatGeomIs(pt3, geom3)
      
      if (obj1 is None) or (obj2 is None) or (obj3 is None):
         return False

      if (type(obj1) == list or type(obj1) == tuple):
         obj1Type = "LINE"
      else:
         obj1Type = obj1.whatIs()
         if obj1Type == "ARC": # se è arco lo trasformo in cerchio
            circle = QadCircle()
            circle.set(obj1.center, obj1.radius)
            obj1 = circle
            obj1Type = "CIRCLE"         

      if (type(obj2) == list or type(obj2) == tuple):
         obj2Type = "LINE"
      else:
         obj2Type = obj2.whatIs()
         if obj2Type == "ARC": # se è arco lo trasformo in cerchio
            circle = QadCircle()
            circle.set(obj2.center, obj2.radius)
            obj2 = circle
            obj2Type = "CIRCLE"         

      if (type(obj3) == list or type(obj3) == tuple):
         obj3Type = "LINE"
      else:
         obj3Type = obj3.whatIs()
         if obj3Type == "ARC": # se è arco lo trasformo in cerchio
            circle = QadCircle()
            circle.set(obj3.center, obj3.radius)
            obj3 = circle
            obj3Type = "CIRCLE"         
      
      if obj1Type == "LINE":
         if obj2Type == "LINE":
            if obj3Type == "LINE":
               return self.fromLineLineLineTanPts(obj1, pt1, obj2, pt2, obj3, pt3)
            elif obj3Type == "CIRCLE":
               return self.fromLineLineCircleTanPts(obj1, pt1, obj2, pt2, obj3, pt3)
         elif obj2Type == "CIRCLE":
            if obj3Type == "LINE":
               return self.fromLineLineCircleTanPts(obj1, pt1, obj3, pt3, obj2, pt2)
            elif obj3Type == "CIRCLE":
               return self.fromLineCircleCircleTanPts(obj1, pt1, obj2, pt2, obj3, pt3)
      elif obj1Type == "CIRCLE":
         if obj2Type == "LINE":
            if obj3Type == "LINE":
               return self.fromLineLineCircleTanPts(obj2, pt2, obj3, pt3, obj1, pt1)
            elif obj3Type == "CIRCLE":
               return self.fromLineCircleCircleTanPts(obj2, pt2, obj1, pt1, obj3, pt3)
         elif obj2Type == "CIRCLE":
            if obj3Type == "LINE":
               return self.fromLineCircleCircleTanPts(obj3, pt3, obj1, pt1, obj2, pt2)
            elif obj3Type == "CIRCLE":
               return self.fromCircleCircleCircleTanPts(obj1, pt1, obj2, pt2, obj3, pt3)
               
      return False
            

   #============================================================================
   # fromLineLineLineTanPts
   #============================================================================
   def fromLineLineLineTanPts(self, line1, pt1, line2, pt2, line3, pt3):
      """
      setta le caratteristiche del cerchio attraverso tre linee:
      linea1 di tangenza (lista di 2 punti)
      punto di selezione linea1
      linea2 di tangenza (lista di 2 punti)
      punto di selezione linea2
      linea3 di tangenza (lista di 2 punti)
      punto di selezione linea3
      """
      circleList = []
      
      # Punti di intersezione delle rette (line1, line2, line3)
      ptInt1 = qad_utils.getIntersectionPointOn2InfinityLines(line1[0], line1[1], \
                                                              line2[0], line2[1])         
      ptInt2 = qad_utils.getIntersectionPointOn2InfinityLines(line2[0], line2[1], \
                                                              line3[0], line3[1])         
      ptInt3 = qad_utils.getIntersectionPointOn2InfinityLines(line3[0], line3[1], \
                                                              line1[0], line1[1])
      # tre rette parallele
      if (ptInt1 is None) and (ptInt2 is None):
         return circleList
         
      if (ptInt1 is None): # la linea1 e linea2 sono parallele
         circleList.extend(self.from2ParLinesLineTanPts(line1, line2, line3))        
      elif (ptInt2 is None): # la linea2 e linea3 sono parallele
         circleList.extend(self.from2ParLinesLineTanPts(line2, line3, line1))        
      elif (ptInt3 is None): # la linea3 e linea1 sono parallele
         circleList.extend(self.from2ParLinesLineTanPts(line3, line1, line2))        
      else:
         # Bisettrici degli angoli interni del triangolo avente come vertici i punti di intersezione delle rette
         Bisector123 = qad_utils.getBisectorInfinityLine(ptInt1, ptInt2, ptInt3)
         Bisector231 = qad_utils.getBisectorInfinityLine(ptInt2, ptInt3, ptInt1)
         Bisector312 = qad_utils.getBisectorInfinityLine(ptInt3, ptInt1, ptInt2)
         # Punto di intersezione delle bisettrici = centro delle circonferenza inscritta al triangolo
         center = qad_utils.getIntersectionPointOn2InfinityLines(Bisector123[0], Bisector123[1], \
                                                                 Bisector231[0], Bisector231[1])
         # Perpendicolari alle rette line1 passanti per il centro della circonferenza inscritta
         ptPer = qad_utils.getPerpendicularPointOnInfinityLine(line1[0], line1[1], center)
         radius = qad_utils.getDistance(center, ptPer)
         circle = QadCircle()
         circle.set(center, radius)
         circleList.append(circle)
         
         # Bisettrici degli angoli esterni del triangolo
         angle = qad_utils.getAngleBy2Pts(Bisector123[0], Bisector123[1]) + math.pi / 2
         Bisector123 = [ptInt2, qad_utils.getPolarPointByPtAngle(ptInt2, angle, 10)]
         
         angle = qad_utils.getAngleBy2Pts(Bisector231[0], Bisector231[1]) + math.pi / 2
         Bisector231 = [ptInt3, qad_utils.getPolarPointByPtAngle(ptInt3, angle, 10)]

         angle = qad_utils.getAngleBy2Pts(Bisector312[0], Bisector312[1]) + math.pi / 2
         Bisector312 = [ptInt1, qad_utils.getPolarPointByPtAngle(ptInt1, angle, 10)]
         # Punti di intersezione delle bisettrici = centro delle circonferenze ex-inscritte
         center = qad_utils.getIntersectionPointOn2InfinityLines(Bisector123[0], Bisector123[1], \
                                                                 Bisector231[0], Bisector231[1])
         ptPer = qad_utils.getPerpendicularPointOnInfinityLine(ptInt2, ptInt3, center)
         radius = qad_utils.getDistance(center, ptPer)
         circle = QadCircle()
         circle.set(center, radius)
         circleList.append(circle)
         
         center = qad_utils.getIntersectionPointOn2InfinityLines(Bisector231[0], Bisector231[1], \
                                                                 Bisector312[0], Bisector312[1])
         ptPer = qad_utils.getPerpendicularPointOnInfinityLine(ptInt3, ptInt1, center)
         radius = qad_utils.getDistance(center, ptPer)
         circle = QadCircle()
         circle.set(center, radius)
         circleList.append(circle)
   
         center = qad_utils.getIntersectionPointOn2InfinityLines(Bisector312[0], Bisector312[1], \
                                                                 Bisector123[0], Bisector123[1])
         ptPer = qad_utils.getPerpendicularPointOnInfinityLine(ptInt1, ptInt2, center)
         radius = qad_utils.getDistance(center, ptPer)
         circle = QadCircle()
         circle.set(center, radius)
         circleList.append(circle)
      
      if len(circleList) == 0:
         return False
      
      AvgList = []
      Avg = sys.float_info.max
      for circleTan in circleList:
         del AvgList[:] # svuoto la lista
         
         ptInt = qad_utils.getPerpendicularPointOnInfinityLine(line1[0], line1[1], circleTan.center)
         AvgList.append(qad_utils.getDistance(ptInt, pt1))

         ptInt = qad_utils.getPerpendicularPointOnInfinityLine(line2[0], line2[1], circleTan.center)
         AvgList.append(qad_utils.getDistance(ptInt, pt2))

         ptInt = qad_utils.getPerpendicularPointOnInfinityLine(line3[0], line3[1], circleTan.center)
         AvgList.append(qad_utils.getDistance(ptInt, pt3))

         currAvg = qad_utils.numericListAvg(AvgList)           
         if currAvg < Avg: # mediamente più vicino
            Avg = currAvg
            self.center = circleTan.center
            self.radius = circleTan.radius
            
      return True


   #===========================================================================
   # from2ParLinesLineTanPts
   #===========================================================================
   def from2ParLinesLineTanPts(self, parLine1, parLine2, line3):
      """
      setta le caratteristiche del cerchio attraverso 2 linee parallele e una terza linea non parallela:
      linea1 di tangenza (lista di 2 punti) parallela a linea2
      linea2 di tangenza (lista di 2 punti) parallela a linea1
      linea3 di tangenza (lista di 2 punti)
      """
      circleList = []
      
      ptInt2 = qad_utils.getIntersectionPointOn2InfinityLines(parLine2[0], parLine2[1], \
                                                              line3[0], line3[1])         
      ptInt3 = qad_utils.getIntersectionPointOn2InfinityLines(line3[0], line3[1], \
                                                              parLine1[0], parLine1[1])

      if parLine1[0] == ptInt3:
         pt = parLine1[1]
      else:
         pt = parLine1[0]        
      Bisector123 = qad_utils.getBisectorInfinityLine(pt, ptInt2, ptInt3)
      
      if parLine2[0] == ptInt2:
         pt = parLine2[1]
      else:
         pt = parLine2[0]
      Bisector312 = qad_utils.getBisectorInfinityLine(pt, ptInt3, ptInt2)
      
      # Punto di intersezione delle bisettrici = centro delle circonferenza
      center = qad_utils.getIntersectionPointOn2InfinityLines(Bisector123[0], Bisector123[1], \
                                                              Bisector312[0], Bisector312[1])
      ptPer = qad_utils.getPerpendicularPointOnInfinityLine(parLine1[0], parLine1[1], center)
      radius = qad_utils.getDistance(center, ptPer)
      circle = QadCircle()
      circle.set(center, radius)
      circleList.append(circle)
         
      # Bisettrici degli angoli esterni
      Bisector123 = Bisector123 + math.pi / 2
      Bisector312 = Bisector312 + math.pi / 2        
      # Punto di intersezione delle bisettrici = centro delle circonferenza
      center = qad_utils.getIntersectionPointOn2InfinityLines(Bisector123[0], Bisector123[1], \
                                                              Bisector312[0], Bisector312[1])
      ptPer = qad_utils.getPerpendicularPointOnInfinityLine(parLine1[0], parLine1[1], center)
      radius = qad_utils.getDistance(center, ptPer)
      circle = QadCircle()
      circle.set(center, radius)
      circleList.append(circle)

      return circleList
   
   
   #============================================================================
   # fromLineLineCircleTanPts
   #============================================================================
   def fromLineLineCircleTanPts(self, line1, pt1, line2, pt2, circle, pt3):
      """
      setta le caratteristiche del cerchio attraverso tre linee:
      linea1 di tangenza (lista di 2 punti)
      punto di selezione linea1
      linea2 di tangenza (lista di 2 punti)
      punto di selezione linea2
      cerchio di tangenza (oggetto QadCircle)
      punto di selezione cerchio
      """
      circleList = []
      
      circleList.extend(qad_utils.solveCircleTangentTo2LinesAndCircle(line1, line2, circle, -1, -1))         
      circleList.extend(qad_utils.solveCircleTangentTo2LinesAndCircle(line1, line2, circle, -1,  1))
      circleList.extend(qad_utils.solveCircleTangentTo2LinesAndCircle(line1, line2, circle,  1, -1))
      circleList.extend(qad_utils.solveCircleTangentTo2LinesAndCircle(line1, line2, circle,  1,  1))

      if len(circleList) == 0:
         return False

      AvgList = []
      Avg = sys.float_info.max
      for circleTan in circleList:
         del AvgList[:] # svuoto la lista
                  
         ptInt = qad_utils.getPerpendicularPointOnInfinityLine(line1[0], line1[1], circleTan.center)
         AvgList.append(qad_utils.getDistance(ptInt, pt1))

         ptInt = qad_utils.getPerpendicularPointOnInfinityLine(line2[0], line2[1], circleTan.center)
         AvgList.append(qad_utils.getDistance(ptInt, pt2))
         
         angle = qad_utils.getAngleBy2Pts(circleTan.center, circle.center)
         if qad_utils.getDistance(circleTan.center, circle.center) < circle.radius: # cerchio interno
            angle = angle + math.pi / 2
         ptInt = qad_utils.getPolarPointByPtAngle(circleTan.center, angle, circleTan.radius)
         AvgList.append(qad_utils.getDistance(ptInt, pt3))
                  
         currAvg = qad_utils.numericListAvg(AvgList)           
         if currAvg < Avg: # mediamente più vicino
            Avg = currAvg
            self.center = circleTan.center
            self.radius = circleTan.radius
            
      return True
            

   #============================================================================
   # fromLineCircleCircleTanPts
   #============================================================================
   def fromLineCircleCircleTanPts(self, line, pt, circle1, pt1, circle2, pt2):
      """
      setta le caratteristiche del cerchio attraverso tre linee:
      linea di tangenza (lista di 2 punti)
      punto di selezione linea
      cerchio1 di tangenza (oggetto QadCircle)
      punto di selezione cerchio1
      cerchio2 di tangenza (oggetto QadCircle)
      punto di selezione cerchio2
      """
      circleList = []
      
      circleList.extend(qad_utils.solveCircleTangentToLineAnd2Circles(line, circle1, circle2, -1, -1))         
      circleList.extend(qad_utils.solveCircleTangentToLineAnd2Circles(line, circle1, circle2, -1,  1))
      circleList.extend(qad_utils.solveCircleTangentToLineAnd2Circles(line, circle1, circle2,  1, -1))
      circleList.extend(qad_utils.solveCircleTangentToLineAnd2Circles(line, circle1, circle2,  1,  1))

      if len(circleList) == 0:
         return False

      AvgList = []
      Avg = sys.float_info.max
      for circleTan in circleList:
         del AvgList[:] # svuoto la lista
                  
         ptInt = qad_utils.getPerpendicularPointOnInfinityLine(line[0], line[1], circleTan.center)
         AvgList.append(qad_utils.getDistance(ptInt, pt))

         angle = qad_utils.getAngleBy2Pts(circleTan.center, circle1.center)
         if qad_utils.getDistance(circleTan.center, circle1.center) < circle1.radius: # cerchio interno
            angle = angle + math.pi / 2
         ptInt = qad_utils.getPolarPointByPtAngle(circleTan.center, angle, circleTan.radius)
         AvgList.append(qad_utils.getDistance(ptInt, pt1))
         
         angle = qad_utils.getAngleBy2Pts(circleTan.center, circle2.center)
         if qad_utils.getDistance(circleTan.center, circle2.center) < circle2.radius: # cerchio interno
            angle = angle + math.pi / 2
         ptInt = qad_utils.getPolarPointByPtAngle(circleTan.center, angle, circleTan.radius)
         AvgList.append(qad_utils.getDistance(ptInt, pt2))
                  
         currAvg = qad_utils.numericListAvg(AvgList)           
         if currAvg < Avg: # mediamente più vicino
            Avg = currAvg
            self.center = circleTan.center
            self.radius = circleTan.radius
            
      return True
            

   #============================================================================
   # fromCircleCircleCircleTanPts
   #============================================================================
   def fromCircleCircleCircleTanPts(self, circle1, pt1, circle2, pt2, circle3, pt3):
      """
      setta le caratteristiche dei cerchi attraverso tre linee:
      cerchio1 di tangenza (oggetto QadCircle)
      punto di selezione cerchio1
      cerchio2 di tangenza (oggetto QadCircle)
      punto di selezione cerchio2
      cerchio3 di tangenza (oggetto QadCircle)
      punto di selezione cerchio3
      """
      circleList = []
      circle = qad_utils.solveApollonius(circle1, circle2, circle3, -1, -1, -1)
      if circle is not None:
         circleList.append(circle)
      circle = qad_utils.solveApollonius(circle1, circle2, circle3, -1, -1,  1)
      if circle is not None:
         circleList.append(circle)
      circle = qad_utils.solveApollonius(circle1, circle2, circle3, -1,  1, -1)
      if circle is not None:
         circleList.append(circle)
      circle = qad_utils.solveApollonius(circle1, circle2, circle3, -1,  1,  1)
      if circle is not None:
         circleList.append(circle)
      circle = qad_utils.solveApollonius(circle1, circle2, circle3,  1, -1, -1)
      if circle is not None:
         circleList.append(circle)
      circle = qad_utils.solveApollonius(circle1, circle2, circle3,  1, -1,  1)
      if circle is not None:
         circleList.append(circle)
      circle = qad_utils.solveApollonius(circle1, circle2, circle3,  1,  1, -1)
      if circle is not None:
         circleList.append(circle)
      circle = qad_utils.solveApollonius(circle1, circle2, circle3,  1,  1,  1)
      if circle is not None:
         circleList.append(circle)

      if len(circleList) == 0:
         return False

      AvgList = []
      Avg = sys.float_info.max
      for circleTan in circleList:
         del AvgList[:] # svuoto la lista
                  
         angle = qad_utils.getAngleBy2Pts(circleTan.center, circle1.center)
         if qad_utils.getDistance(circleTan.center, circle1.center) < circle1.radius: # cerchio interno
            angle = angle + math.pi / 2
         ptInt = qad_utils.getPolarPointByPtAngle(circleTan.center, angle, circleTan.radius)
         AvgList.append(qad_utils.getDistance(ptInt, pt1))

         angle = qad_utils.getAngleBy2Pts(circleTan.center, circle2.center)
         if qad_utils.getDistance(circleTan.center, circle2.center) < circle2.radius: # cerchio interno
            angle = angle + math.pi / 2
         ptInt = qad_utils.getPolarPointByPtAngle(circleTan.center, angle, circleTan.radius)
         AvgList.append(qad_utils.getDistance(ptInt, pt2))

         angle = qad_utils.getAngleBy2Pts(circleTan.center, circle3.center)
         if qad_utils.getDistance(circleTan.center, circle3.center) < circle3.radius: # cerchio interno
            angle = angle + math.pi / 2
         ptInt = qad_utils.getPolarPointByPtAngle(circleTan.center, angle, circleTan.radius)
         AvgList.append(qad_utils.getDistance(ptInt, pt3))
         
         currAvg = qad_utils.numericListAvg(AvgList)           
         if currAvg < Avg: # mediamente più vicino
            Avg = currAvg
            self.center = circleTan.center
            self.radius = circleTan.radius
            
      return True


   #============================================================================
   # from2IntPts1TanPt
   #============================================================================
   def from2IntPts1TanPt(self, pt1, pt2, geom, pt):
      """
      setta le caratteristiche del cerchio attraverso
      2 punti di intersezione ed un oggetto di tangenza:
      punto1 di intersezione
      punto2 di intersezione
      geometria di tangenza (linea, arco o cerchio)
      punto di selezione geometria
      """
      obj = qad_utils.whatGeomIs(pt, geom)
      
      if obj is None:
         return False

      if (type(obj) == list or type(obj) == tuple):
         objType = "LINE"
      else:
         objType = obj.whatIs()
         if objType == "ARC": # se è arco lo trasformo in cerchio
            circle = QadCircle()
            circle.set(obj.center, obj.radius)
            obj = circle
            objType = "CIRCLE"         
      
      if objType == "LINE":
         return self.from2IntPtsLineTanPts(pt1, pt2, obj, pt)
      elif objType == "CIRCLE":
         return self.from2IntPtsCircleTanPts(pt1, pt2, obj, pt)
               
      return False

   
   #===========================================================================
   # from2IntPtsLineTanPts
   #===========================================================================
   def from2IntPtsLineTanPts(self, pt1, pt2, line, pt, AllCircles = False):
      """
      setta le caratteristiche dei cerchi attraverso 2 punti di intersezione e una linea tangente:
      punto1 di intersezione
      punto2 di intersezione
      linea di tangenza (lista di 2 punti)
      punto di selezione linea
      il parametro AllCircles se = True fa restituire tutti i cerchi e non sono quello più vicino a pt1 e pt2
      """
      circleList = []
      
      pt1Line = line[0]
      pt2Line = line[1]

      A = (pt1[0] * pt1[0]) + (pt1[1] * pt1[1])
      B = (pt2[0] * pt2[0]) + (pt2[1] * pt2[1])

      E = - pt1[0] + pt2[0]
      F = pt1[1] - pt2[1]
      if F == 0:
         if AllCircles == True:
            return circleList
         else:
            return False

      G = (-A + B) / F 
      H = E / F
      
      if pt1Line[0] - pt2Line[0] == 0:
         # la linea é verticale
         e = pt1Line[0]        
         I = H * H
         if I == 0:
            if AllCircles == True:
               return circleList
            else:
               return False
         J = (2 * G * H) - (4 * e) + (4 * pt2[0]) + (4 * H * pt2[1])
         K = (G * G) - (4 * e * e) + (4 * B) + (4 * G * pt2[1])
      else:
         # equazione della retta line -> y = dx + e
         d = (pt2Line[1] - pt1Line[1]) / (pt2Line[0] - pt1Line[0])
         e = - d * pt1Line[0] + pt1Line[1]        
         C = 4 * (1 + d * d)
         D = 2 * d * e
         d2 = d * d
         I = 1 + (H * H * d2) + 2 * H * d
         if I == 0:
            if AllCircles == True:
               return circleList
            else:
               return False
         J = (2 * d2 * G * H) + (2 * D) + (2 * D * H * d) + (2 * G * d) - (e * C * H) + (pt2[0] * C) + H * pt2[1] * C
         K = (G * G * d2) + (2 * D * G * d) + (D * D) - (C * e * e) - (C * G * e) + (B * C) + (G * pt2[1] * C)
             
      L = (J * J) - (4 * I * K)
      if L < 0:
         if AllCircles == True:
            return circleList
         else:
            return False
            
      a1 = (-J + math.sqrt(L)) / (2 * I)
      b1 = (a1 * H) + G
      c1 = - B - (a1 * pt2[0]) - (b1 * pt2[1])
      center = QgsPoint()
      center.setX(- (a1 / 2))
      center.setY(- (b1 / 2))
      radius = math.sqrt((a1 * a1 / 4) + (b1 * b1 / 4) - c1)
      circle = QadCircle()
      circle.set(center, radius)
      circleList.append(circle)
      
      a2 = (-J - math.sqrt(L)) / (2 * I) 
      b2 = (a2 * H) + G
      c2 = - B - (a2 * pt2[0]) - (b2 * pt2[1])
      center.setX(- (a2 / 2))
      center.setY(- (b2 / 2))
      radius = math.sqrt((a2 * a2 / 4) + (b2 * b2 / 4) - c2)
      circle = QadCircle()
      circle.set(center, radius)
      circleList.append(circle)
      
      if AllCircles == True:
         return circleList
      
      if len(circleList) == 0:
         return False

      minDist = sys.float_info.max
      for circle in circleList:                  
         ptInt = qad_utils.getPerpendicularPointOnInfinityLine(line[0], line[1], circle.center)
         dist = qad_utils.getDistance(ptInt, pt)
         
         if dist < minDist: # mediamente più vicino
            minDist = dist
            self.center = circle.center
            self.radius = circle.radius
            
      return True

   
   #===========================================================================
   # from2IntPtsCircleTanPts
   #===========================================================================
   def from2IntPtsCircleTanPts(self, pt1, pt2, circle, pt):
      """
      setta le caratteristiche dei cerchi attraverso 2 punti di intersezione e una cerchio tangente:
      punto1 di intersezione
      punto2 di intersezione
      cerchio di tangenza (oggetto QadCircle)
      punto di selezione cerchio
      """
      # http://www.batmath.it/matematica/a_apollonio/ppc.htm
      circleList = []
      
      if pt1 == pt2:
         return False
         
      dist1 = qad_utils.getDistance(pt1, circle.center) # distanza del punto 1 dal centro
      dist2 = qad_utils.getDistance(pt2, circle.center) # distanza del punto 2 dal centro

      # entrambi i punti devono essere esterni o interni a circle
      if (dist1 > circle.radius and dist2 < circle.radius) or \
         (dist1 < circle.radius and dist2 > circle.radius):
         return False 
      
      if dist1 == dist2: # l'asse di pt1 e pt2 passa per il centro di circle
         if dist1 == circle.radius: # entrambi i punti sono sulla circonferenza di circle
            return False 
         axis = qad_utils.getInfinityLinePerpOnMiddle(pt1, pt2) # asse di pt1 e pt2
         intPts = circle.getIntersectionPointsWithInfinityLine(axis) # punti di intersezione tra l'asse e circle
         for intPt in intPts:
            circleTan = QadCircle()
            if circleTan.from3Pts(pt1, pt2, intPt) == True:
               circleList.append(circleTan)         
      elif dist1 > circle.radius and dist2 > circle.radius : # entrambi i punti sono esterni a circle
         # mi ricavo una qualunque circonferenza passante per p1 e p2 ed intersecante circle
         circleInt = QadCircle()
         if circleInt.from3Pts(pt1, pt2, circle.center) == False:
            return False               
         intPts = circle.getIntersectionPointsWithCircle(circleInt)
         intPt = qad_utils.getIntersectionPointOn2InfinityLines(pt1, pt2, intPts[0], intPts[1])
         tanPts = circle.getTanPoints(intPt)
         for tanPt in tanPts:
            circleTan = QadCircle()
            if circleTan.from3Pts(pt1, pt2, tanPt) == True:
               circleList.append(circleTan)         
      elif dist1 < circle.radius and dist2 < circle.radius : # entrambi i punti sono interni a circle
         # mi ricavo una qualunque circonferenza passante per p1 e p2 ed intersecante circle
         ptMiddle = qad_utils.getMiddlePoint(pt1, pt2)
         angle = qad_utils.getAngleBy2Pts(pt1, pt2) + math.pi / 2
         pt3 = qad_utils.getPolarPointByPtAngle(ptMiddle, angle, 2 * circle.radius)
         circleInt = QadCircle()
         if circleInt.from3Pts(pt1, pt2, pt3) == False:
            return False               
         intPts = circle.getIntersectionPointsWithCircle(circleInt)
         intPt = qad_utils.getIntersectionPointOn2InfinityLines(pt1, pt2, intPts[0], intPts[1])
         tanPts = circle.getTanPoints(intPt)
         for tanPt in tanPts:
            circleTan = QadCircle()
            if circleTan.from3Pts(pt1, pt2, tanPt) == True:
               circleList.append(circleTan)
      elif dist1 == radius: # il punto1 sulla circonferenza di circle
         # una sola circonferenza avente come centro l'intersezione tra l'asse pt1 e pt2 e la retta
         # passante per il centro di circle e pt1
         axis = qad_utils.getInfinityLinePerpOnMiddle(pt1, pt2) # asse di pt1 e pt2        
         intPt = qad_utils.getIntersectionPointOn2InfinityLines(axis[0], axis[1], circle.center, pt1)
         circleTan = QadCircle()
         circleTan.set(intPt, qad_utils.getDistance(pt1, intPt))
         circleList.append(circleTan)
      elif dist2 == radius: # il punto3 é sulla circonferenza di circle
         # una sola circonferenza avente come centro l'intersezione tra l'asse pt1 e pt2 e la retta
         # passante per il centro di circle e pt2
         axis = qad_utils.getInfinityLinePerpOnMiddle(pt1, pt2) # asse di pt1 e pt2        
         intPt = qad_utils.getIntersectionPointOn2InfinityLines(axis[0], axis[1], circle.center, pt2)
         circleTan = QadCircle()
         circleTan.set(intPt, qad_utils.getDistance(pt2, intPt))
         circleList.append(circleTan)       
                  
      if len(circleList) == 0:
         return False

      minDist = sys.float_info.max
      for circleTan in circleList:        
         angle = qad_utils.getAngleBy2Pts(circleTan.center, circle.center)
         if qad_utils.getDistance(circleTan.center, circle.center) < circle.radius: # cerchio interno
            angle = angle + math.pi / 2
         ptInt = qad_utils.getPolarPointByPtAngle(circleTan.center, angle, circleTan.radius)
         dist = qad_utils.getDistance(ptInt, pt)
         
         if dist < minDist: # mediamente più vicino
            minDist = dist
            self.center = circleTan.center
            self.radius = circleTan.radius
            
      return True
   

   #============================================================================
   # from1IntPt2TanPts
   #============================================================================
   def from1IntPt2TanPts(self, pt, geom1, pt1, geom2, pt2):
      """
      setta le caratteristiche del cerchio attraverso
      1 punti di intersezione e 2 oggetti di tangenza:
      punto di intersezione
      geometria1 di tangenza (linea, arco o cerchio)
      punto di selezione geometria1
      geometria2 di tangenza (linea, arco o cerchio)
      punto di selezione geometria2     
      """
      obj1 = qad_utils.whatGeomIs(pt1, geom1)
      obj2 = qad_utils.whatGeomIs(pt2, geom2)
      
      if (obj1 is None) or (obj2 is None):
         return False

      if (type(obj1) == list or type(obj1) == tuple):
         obj1Type = "LINE"
      else:
         obj1Type = obj1.whatIs()
         if obj1Type == "ARC": # se è arco lo trasformo in cerchio
            circle = QadCircle()
            circle.set(obj1.center, obj1.radius)
            obj1 = circle
            obj1Type = "CIRCLE"         

      if (type(obj2) == list or type(obj2) == tuple):
         obj2Type = "LINE"
      else:
         obj2Type = obj2.whatIs()
         if obj2Type == "ARC": # se è arco lo trasformo in cerchio
            circle = QadCircle()
            circle.set(obj1.center, obj1.radius)
            obj2 = circle
            obj2Type = "CIRCLE"         
      
      if obj1Type == "LINE":
         if obj2Type == "LINE":
            return self.from1IntPtLineLineTanPts(pt, obj1, pt1, obj2, pt2)
         elif obj2Type == "CIRCLE":
            return self.from1IntPtLineCircleTanPts(pt, obj1, pt1, obj2, pt2)
      elif obj1Type == "CIRCLE":
         if obj2Type == "LINE":
            return self.from1IntPtLineCircleTanPts(pt, obj2, pt2, obj1, pt1)
         elif obj2Type == "CIRCLE":
            return self.from1IntPtCircleCircleTanPts(pt, obj1, pt1, obj2, pt2)
               
      return False

   
   #===========================================================================
   # from1IntPtLineLineTanPts
   #===========================================================================
   def from1IntPtLineLineTanPts(self, pt, line1, pt1, line2, pt2, AllCircles = False):
      """
      setta le caratteristiche dei cerchi attraverso 1 punti di intersezione e due linee tangenti:
      punto di intersezione     
      linea1 di tangenza (lista di 2 punti)
      punto di selezione linea1
      linea2 di tangenza (lista di 2 punti)
      punto di selezione linea2
      il parametro AllCircles se = True fa restituire tutti i cerchi e non sono quello più vicino a pt1 e pt2
      """
      # http://www.batmath.it/matematica/a_apollonio/prr.htm
      circleList = []
            
      # verifico se le rette sono parallele
      ptInt = qad_utils.getIntersectionPointOn2InfinityLines(line1[0], line1[1], \
                                                             line2[0], line2[1])
      if ptInt is None: # le rette sono parallele
         # Se le rette sono parallele il problema ha soluzioni solo se il punto 
         # é non esterno alla striscia individuata dalle due rette e basta considerare 
         # il simmetrico di A rispetto alla bisettrice della striscia.
         ptPerp = qad_utils.getPerpendicularPointOnInfinityLine(line1[0], line1[1], line2[0])
         angle = qad_utils.getAngleBy2Pts(line2[0], ptPerp)
         dist = qad_utils.getDistance(line2[0], ptPerp)
         pt1ParLine = qad_utils.getPolarPointByPtAngle(line2[0], angle, dist / 2)
         angle = angle + math.pi / 2
         pt2ParLine = qad_utils.getPolarPointByPtAngle(pt1ParLine, angle, dist)

         ptPerp = qad_utils.getPerpendicularPointOnInfinityLine(pt1ParLine, pt2ParLine, pt)
         dist = qad_utils.getDistance(pt, ptPerp)
         
         # trovo il punto simmetrico
         angle = qad_utils.getAngleBy2Pts(pt, ptPerp)
         ptSymmetric = qad_utils.getPolarPointByPtAngle(pt, angle, dist * 2)
         return self.from2IntPtsLineTanPts(pt, ptSymmetric, line1, pt1, AllCircles)
      else: # le rette non sono parallele
         if ptInt == pt:
            return False
         # se il punto é sulla linea1 o sulla linea2
         ptPerp1 = qad_utils.getPerpendicularPointOnInfinityLine(line1[0], line1[1], pt)
         ptPerp2 = qad_utils.getPerpendicularPointOnInfinityLine(line2[0], line2[1], pt)
         if ptPerp1 == pt or ptPerp2 == pt:
            # Se le rette sono incidenti ed il punto appartiene ad una delle due la costruzione
            # é quasi immediata: basta tracciare le bisettrici dei due angoli individuati dalle rette 
            # e la perpendicolare per pt alla retta cui appartiene pt stesso. Si avranno due circonferenze.            
            
            if ptPerp1 == pt: # se il punto é sulla linea1
               angle = qad_utils.getAngleBy2Pts(line2[0], line2[1])
               ptLine = qad_utils.getPolarPointByPtAngle(ptInt, angle, 10)
               Bisector1 = qad_utils.getBisectorInfinityLine(pt, ptInt, ptLine)
               ptLine = qad_utils.getPolarPointByPtAngle(ptInt, angle + math.pi, 10)
               Bisector2 = qad_utils.getBisectorInfinityLine(pt, ptInt, ptLine)
               angle = qad_utils.getAngleBy2Pts(line1[0], line1[1])
               ptPerp = qad_utils.getPolarPointByPtAngle(pt, angle + math.pi / 2, 10)               
            else: # se il punto é sulla linea2
               angle = qad_utils.getAngleBy2Pts(line1[0], line1[1])
               ptLine = qad_utils.getPolarPointByPtAngle(ptInt, angle, 10)
               Bisector1 = qad_utils.getBisectorInfinityLine(pt, ptInt, ptLine)
               ptLine = qad_utils.getPolarPointByPtAngle(ptInt, angle + math.pi, 10)
               Bisector2 = qad_utils.getBisectorInfinityLine(pt, ptInt, ptLine)
               angle = qad_utils.getAngleBy2Pts(line2[0], line2[1])
               ptPerp = qad_utils.getPolarPointByPtAngle(pt, angle + math.pi / 2, 10)
            
            center = qad_utils.getIntersectionPointOn2InfinityLines(Bisector1[0], Bisector1[1], \
                                                                    pt, ptPerp)
            radius = qad_utils.getDistance(pt, center)
            circleTan = QadCircle()
            circleTan.set(center, radius)
            circleList.append(circleTan)       

            center = qad_utils.getIntersectionPointOn2InfinityLines(Bisector2[0], Bisector2[1], \
                                                                    pt, ptPerp)
            radius = qad_utils.getDistance(pt, center)
            circleTan = QadCircle()
            circleTan.set(center, radius)
            circleList.append(circleTan)            
         else:         
            # Bisettrice dell'angolo interno del triangolo avente come vertice i punti di intersezione delle rette
            Bisector = qad_utils.getBisectorInfinityLine(ptPerp1, ptInt, ptPerp2)
   
            ptPerp = qad_utils.getPerpendicularPointOnInfinityLine(Bisector[0], Bisector[1], pt)
            dist = qad_utils.getDistance(pt, ptPerp)
            
            # trovo il punto simmetrico
            angle = qad_utils.getAngleBy2Pts(pt, ptPerp)
            ptSymmetric = qad_utils.getPolarPointByPtAngle(pt, angle, dist * 2)
            return self.from2IntPtsLineTanPts(pt, ptSymmetric, line1, pt1, AllCircles)

      if AllCircles == True:
         return circleList
                  
      if len(circleList) == 0:
         return False

      AvgList = []
      Avg = sys.float_info.max
      for circleTan in circleList:
         del AvgList[:] # svuoto la lista
                  
         ptInt = qad_utils.getPerpendicularPointOnInfinityLine(line1[0], line1[1], circleTan.center)
         AvgList.append(qad_utils.getDistance(ptInt, pt1))

         ptInt = qad_utils.getPerpendicularPointOnInfinityLine(line2[0], line2[1], circleTan.center)
         AvgList.append(qad_utils.getDistance(ptInt, pt2))
                  
         currAvg = qad_utils.numericListAvg(AvgList)           
         if currAvg < Avg: # mediamente più vicino
            Avg = currAvg
            self.center = circleTan.center
            self.radius = circleTan.radius
            
      return True
   
   
   #============7===============================================================
   # from1IntPtLineCircleTanPts
   #===========================================================================
   def from1IntPtLineCircleTanPts(self, pt, line1, pt1, circle2, pt2, AllCircles = False):
      """
      setta le caratteristiche dei cerchi attraverso 1 punto di intersezione, 1 linea e 1 cerchio tangenti:
      punto di intersezione     
      linea di tangenza (lista di 2 punti)
      punto di selezione linea
      cerchio di tangenza (oggetto QadCircle)
      punto di selezione cerchio
      il parametro AllCircles se = True fa restituire tutti i cerchi e non sono quello più vicino a pt1 e pt2
      """
      # http://www.batmath.it/matematica/a_apollonio/prc.htm
      circleList = []
      
      # Sono dati un cerchio circle2, un punto pt ed una retta line1 nell'ipotesi che pt
      # non stia nè sulla retta line1 nè sul circolo.
      # Si vogliono trovare le circonferenze passanti per il punto e tangenti alla retta e al cerchio dato.
      # Il problema si può risolvere facilmente utilizzando un'inversione di centro pt e raggio qualunque.
      # Trovate le circonferenze inverse della retta data e del circolo dato, se ne trovano le tangenti comuni.
      # Le inverse di queste tangenti comuni sono le circonferenze cercate. 

      if qad_utils.getYOnInfinityLine(line1[0], line1[1], pt.x()) == pt.y() or \
         qad_utils.getDistance(pt, circle2.center) == circle2.radius:
         if AllCircles == True:
            return circleList
         else:
            return False
      
      c = QadCircle()
      c.set(pt, 10)
      
      circularInvLine = qad_utils.getCircularInversionOfLine(c, line1)
      circularInvCircle = qad_utils.getCircularInversionOfCircle(c, circle2)
      tangents = circularInvCircle.getTangentsWithCircle(circularInvLine)
      for tangent in tangents:
         circleList.append(qad_utils.getCircularInversionOfLine(c, tangent))
         
      if AllCircles == True:
         return circleList

      if len(circleList) == 0:
         return False

      AvgList = []
      Avg = sys.float_info.max
      for circleTan in circleList:
         del AvgList[:] # svuoto la lista
                  
         ptInt = qad_utils.getPerpendicularPointOnInfinityLine(line1[0], line1[1], circleTan.center)
         AvgList.append(qad_utils.getDistance(ptInt, pt1))

         angle = qad_utils.getAngleBy2Pts(circleTan.center, circle2.center)
         if qad_utils.getDistance(circleTan.center, circle2.center) < circle2.radius: # cerchio interno
            angle = angle + math.pi / 2
         ptInt = qad_utils.getPolarPointByPtAngle(circleTan.center, angle, circleTan.radius)
         AvgList.append(qad_utils.getDistance(ptInt, pt2))
                  
         currAvg = qad_utils.numericListAvg(AvgList)           
         if currAvg < Avg: # mediamente più vicino
            Avg = currAvg
            self.center = circleTan.center
            self.radius = circleTan.radius
            
      if AllCircles == True:
         return circleList
      else:
         return True


   #===========================================================================
   # from1IntPtCircleCircleTanPts
   #===========================================================================
   def from1IntPtCircleCircleTanPts(self, pt, circle1, pt1, circle2, pt2):
      """
      setta le caratteristiche dei cerchi attraverso 1 punto di intersezione, 2 cerchi tangenti:
      punto di intersezione     
      cerchio1 di tangenza (oggetto QadCircle)
      punto di selezione cerchio1
      cerchio2 di tangenza (oggetto QadCircle)
      punto di selezione cerchio2
      """
      # http://www.batmath.it/matematica/a_apollonio/prc.htm
      circleList = []

      # Sono dati un punto pt e due circonferenze circle1 e circle2;
      # si devono determinare le circonferenze passanti per pt e tangenti alle due circonferenze.
      # Proponiamo una costruzione che utilizza l'inversione, in quanto ci pare la più elegante.
      # In realtà si potrebbe anche fare una costruzione utilizzando i centri di omotetia dei due cerchi dati
      # ma, nella sostanza, é solo un modo per mascherare l'uso dell'inversione.
      # Si considera un circolo di inversione di centro pt e raggio qualunque.
      # Si determinano i circoli inversi dei due circoli dati e le loro tangenti comuni.
      # Le circonferenze inverse di queste tangenti comuni sono quelle che soddisfano il problema. 

      c = QadCircle()
      c.set(pt, 10)
      
      circularInvCircle1 = qad_utils.getCircularInversionOfCircle(c, circle1)
      circularInvCircle2 = qad_utils.getCircularInversionOfCircle(c, circle2)
      tangents = circularInvCircle1.getTangentsWithCircle(circularInvCircle2)
      for tangent in tangents:
         circleList.append(qad_utils.getCircularInversionOfLine(c, tangent))

      if len(circleList) == 0:
         return False

      AvgList = []
      Avg = sys.float_info.max
      for circleTan in circleList:
         del AvgList[:] # svuoto la lista
                  
         angle = qad_utils.getAngleBy2Pts(circleTan.center, circle1.center)
         if qad_utils.getDistance(circleTan.center, circle1.center) < circle1.radius: # cerchio interno
            angle = angle + math.pi / 2
         ptInt = qad_utils.getPolarPointByPtAngle(circleTan.center, angle, circleTan.radius)
         AvgList.append(qad_utils.getDistance(ptInt, pt1))

         angle = qad_utils.getAngleBy2Pts(circleTan.center, circle2.center)
         if qad_utils.getDistance(circleTan.center, circle2.center) < circle2.radius: # cerchio interno
            angle = angle + math.pi / 2
         ptInt = qad_utils.getPolarPointByPtAngle(circleTan.center, angle, circleTan.radius)
         AvgList.append(qad_utils.getDistance(ptInt, pt2))
                  
         currAvg = qad_utils.numericListAvg(AvgList)           
         if currAvg < Avg: # mediamente più vicino
            Avg = currAvg
            self.center = circleTan.center
            self.radius = circleTan.radius
            
      return True

   
   #============================================================================
   # fromDiamEnds
   #============================================================================
   def fromDiamEnds(self, startPt, endPt):
      """
      setta le caratteristiche del cerchio attraverso i punti estremità del diametro:
      punto iniziale
      punto finale
      """
      self.radius = qad_utils.getDistance(startPt, endPt) / 2
      if self.radius == 0:
         return False
      self.center = qad_utils.getMiddlePoint(startPt, endPt)
      return True
   

   #============================================================================
   # fromDiamEndsPtTanPt
   #============================================================================
   def fromDiamEndsPtTanPt(self, startPt, geom, pt):
      """
      setta le caratteristiche del cerchio attraverso un punto di estremità del diametro e
      un oggetto di tangenza per l'altra estremità :
      punto iniziale
      geometria 1 di tangenza (linea, arco o cerchio)
      punto di selezione geometria 1
      """
      obj = qad_utils.whatGeomIs(pt, geom)
      
      if (type(obj) == list or type(obj) == tuple):
         objType = "LINE"
      else:
         objType = obj.whatIs()
         if objType == "ARC": # se è arco lo trasformo in cerchio
            circle = QadCircle()
            circle.set(obj.center, obj.radius)
            obj = circle
            objType = "CIRCLE"
      
      if objType == "LINE":
         ptPer = qad_utils.getPerpendicularPointOnInfinityLine(obj[0], obj[1], startPt)
         return self.fromDiamEnds(startPt, ptPer)
      elif objType == "CIRCLE":        
         ptIntList = obj.getIntersectionPointsWithInfinityLine(startPt, obj.center)     
         # scelgo il punto più vicino al punto pt
         ptTan = qad_utils.getNearestPoints(pt, ptIntList)[0]
         return self.fromDiamEnds(startPt, ptTan)
   

   #============================================================================
   # fromDiamEnds2TanPts
   #============================================================================
   def fromDiamEnds2TanPts(self, geom1, pt1, geom2, pt2):
      """
      setta le caratteristiche del cerchio attraverso
      due oggetto di tangenza per le estremità del diametro:
      geometria1 di tangenza (linea, arco o cerchio)
      punto di selezione geometria1
      geometria2 di tangenza (linea, arco o cerchio)
      punto di selezione geometria2
      """
      obj1 = qad_utils.whatGeomIs(pt1, geom1)
      obj2 = qad_utils.whatGeomIs(pt2, geom2)
      
      if (obj1 is None) or (obj2 is None):
         return False

      if (type(obj1) == list or type(obj1) == tuple):
         obj1Type = "LINE"
      else:
         obj1Type = obj1.whatIs()
         if obj1Type == "ARC": # se è arco lo trasformo in cerchio
            circle = QadCircle()
            circle.set(obj1.center, obj1.radius)
            obj1 = circle
            obj1Type = "CIRCLE"         

      if (type(obj2) == list or type(obj2) == tuple):
         obj2Type = "LINE"
      else:
         obj2Type = obj2.whatIs()
         if obj2Type == "ARC": # se è arco lo trasformo in cerchio
            circle = QadCircle()
            circle.set(obj1.center, obj1.radius)
            obj2 = circle
            obj2Type = "CIRCLE"         
      
      if obj1Type == "LINE":
         if obj2Type == "LINE":
            return False # Il diametro non può essere tangente a due linee
         elif obj2Type == "CIRCLE":
            return self.fromLineCircleTanPts(obj1, pt1, obj2, pt2)
      elif obj1Type == "CIRCLE":
         if obj2Type == "LINE":
            return self.fromLineCircleTanPts(obj2, pt2, obj1, pt1)
         elif obj2Type == "CIRCLE":
            return self.fromCircleCircleTanPts(obj1, pt1, obj2, pt2)
               
      return False
            

   #============================================================================
   # fromLineCircleTanPts
   #============================================================================
   def fromLineCircleTanPts(self, line, ptLine, circle, ptCircle):
      """
      setta le caratteristiche del cerchio attraverso una linea, un cerchio di tangenza:
      linea di tangenza (lista di 2 punti)
      punto di selezione linea
      cerchio di tangenza (oggetto QadCircle)
      punto di selezione cerchio
      """

      ptPer = qad_utils.getPerpendicularPointOnInfinityLine(line[0], line[1], circle.center)
      
      ptIntList = obj.getIntersectionPointsWithInfinityLine(ptPer, circle.center)     
      # scelgo il punto più vicino al punto pt
      ptTan = qad_utils.getNearestPoints(pt, ptIntList)[0]
      return self.fromDiamEnds(ptPer, ptTan)
   

   #============================================================================
   # fromCircleCircleTanPts
   #============================================================================
   def fromCircleCircleTanPts(self, circle1, pt1, circle2, pt2):
      """
      setta le caratteristiche del cerchio attraverso due cerchi di tangenza:
      cerchio1 di tangenza (oggetto QadCircle)
      punto di selezione cerchio1
      cerchio2 di tangenza (oggetto QadCircle)
      punto di selezione cerchio2
      """

      ptIntList = circle1.getIntersectionPointsWithInfinityLine(circle1.center, circle2.center)     
      # scelgo il punto più vicino al punto pt1
      ptTan1 = qad_utils.getNearestPoints(pt1, ptIntList)[0]
      
      ptIntList = circle2.getIntersectionPointsWithInfinityLine(circle1.center, circle2.center)     
      # scelgo il punto più vicino al punto pt2
      ptTan2 = qad_utils.getNearestPoints(pt2, ptIntList)[0]
      
      return self.fromDiamEnds(ptTan1, ptTan2)
   
   
   #============================================================================
   # from2TanPtsRadius
   #============================================================================
   def from2TanPtsRadius(self, geom1, pt1, geom2, pt2, radius):
      """
      setta le caratteristiche del cerchio attraverso 2 oggetti di tangenza e un raggio:
      geometria1 di tangenza (linea, arco o cerchio)
      punto di selezione geometria1
      oggetto2 di tangenza (linea, arco o cerchio)
      punto di selezione geometria2
      raggio
      """
      obj1 = qad_utils.whatGeomIs(pt1, geom1)
      obj2 = qad_utils.whatGeomIs(pt2, geom2)
      
      if (obj1 is None) or (obj2 is None):
         return False

      if (type(obj1) == list or type(obj1) == tuple):
         obj1Type = "LINE"
      else:
         obj1Type = obj1.whatIs()
         if obj1Type == "ARC": # se è arco lo trasformo in cerchio
            circle = QadCircle()
            circle.set(obj1.center, obj1.radius)
            obj1 = circle
            obj1Type = "CIRCLE"         

      if (type(obj2) == list or type(obj2) == tuple):
         obj2Type = "LINE"
      else:
         obj2Type = obj2.whatIs()
         if obj1Type == "ARC": # se è arco lo trasformo in cerchio
            circle = QadCircle()
            circle.set(obj2.center, obj2.radius)
            obj2 = circle
            obj2Type = "CIRCLE"         
      
      if obj1Type == "LINE":
         if obj2Type == "LINE":
            return self.fromLineLineTanPtsRadius(obj1, pt1, obj2, pt2, radius)
         elif obj2Type == "CIRCLE":
            return self.fromLineCircleTanPtsRadius(obj1, pt1, obj2, pt2, radius)
      elif obj1Type == "CIRCLE":
         if obj2Type == "LINE":
            return self.fromLineCircleTanPtsRadius(obj2, pt2, obj1, pt1, radius)
         elif obj2Type == "CIRCLE":
            return self.fromCircleCircleTanPtsRadius(obj1, pt1, obj2, pt2, radius)
               
      return False


   #============================================================================
   # fromLineLineTanPtsRadius
   #============================================================================
   def fromLineLineTanPtsRadius(self, line1, pt1, line2, pt2, radius):
      """
      setta le caratteristiche del cerchio attraverso due linee di tangenza e un raggio:
      linea1 di tangenza (lista di 2 punti)
      punto di selezione linea1
      linea2 di tangenza (lista di 2 punti)
      punto di selezione linea2
      raggio
      """
      
      # calcolo il punto medio tra i due punti di selezione
      ptMiddle = qad_utils.getMiddlePoint(pt1, pt2)

      # verifico se le rette sono parallele
      ptInt = qad_utils.getIntersectionPointOn2InfinityLines(line1[0], line1[1], \
                                                             line2[0], line2[1])
      if ptInt is None: # le rette sono parallele
         ptPer = qad_utils.getPerpendicularPointOnInfinityLine(line1[0], line1[1], ptMiddle)
         if qad_utils.doubleNear(radius, qad_utils.getDistance(ptPer, ptMiddle)):                                 
            self.center = ptMiddle
            self.radius = radius
            return True
         else:
            return False
      
      # angolo linea1
      angle = qad_utils.getAngleBy2Pts(line1[0], line1[1])
      # retta parallela da un lato della linea1 distante radius
      angle = angle + math.pi / 2
      pt1Par1Line1 = qad_utils.getPolarPointByPtAngle(line1[0], angle, radius)
      pt2Par1Line1 = qad_utils.getPolarPointByPtAngle(line1[1], angle, radius)
      # retta parallela dall'altro lato della linea1 distante radius
      angle = angle - math.pi
      pt1Par2Line1 = qad_utils.getPolarPointByPtAngle(line1[0], angle, radius)
      pt2Par2Line1 = qad_utils.getPolarPointByPtAngle(line1[1], angle, radius)

      # angolo linea2
      angle = qad_utils.getAngleBy2Pts(line2[0], line2[1])
      # retta parallela da un lato della linea2 distante radius
      angle = angle + math.pi / 2
      pt1Par1Line2 = qad_utils.getPolarPointByPtAngle(line2[0], angle, radius)
      pt2Par1Line2 = qad_utils.getPolarPointByPtAngle(line2[1], angle, radius)
      # retta parallela dall'altro lato della linea2 distante radius
      angle = angle - math.pi
      pt1Par2Line2 = qad_utils.getPolarPointByPtAngle(line2[0], angle, radius)
      pt2Par2Line2 = qad_utils.getPolarPointByPtAngle(line2[1], angle, radius)

      # calcolo le intersezioni
      ptIntList = []
      ptInt = qad_utils.getIntersectionPointOn2InfinityLines(pt1Par1Line1, pt2Par1Line1, \
                                                             pt1Par1Line2, pt2Par1Line2)
      ptIntList.append(ptInt)
      
      ptInt = qad_utils.getIntersectionPointOn2InfinityLines(pt1Par1Line1, pt2Par1Line1, \
                                                             pt1Par2Line2, pt2Par2Line2)
      ptIntList.append(ptInt)

      ptInt = qad_utils.getIntersectionPointOn2InfinityLines(pt1Par2Line1, pt2Par2Line1, \
                                                             pt1Par1Line2, pt2Par1Line2)
      ptIntList.append(ptInt)

      ptInt = qad_utils.getIntersectionPointOn2InfinityLines(pt1Par2Line1, pt2Par2Line1, \
                                                             pt1Par2Line2, pt2Par2Line2)
      ptIntList.append(ptInt)

      # scelgo il punto più vicino al punto medio
      self.center = qad_utils.getNearestPoints(ptMiddle, ptIntList)[0]
      self.radius = radius
      return True
            

   #============================================================================
   # fromLineCircleTanPtsRadius
   #============================================================================
   def fromLineCircleTanPtsRadius(self, line, ptLine, circle, ptCircle, radius):
      """
      setta le caratteristiche del cerchio attraverso una linea, un cerchio di tangenza e un raggio:
      linea di tangenza (lista di 2 punti)
      punto di selezione linea
      cerchio di tangenza (oggetto QadCircle)
      punto di selezione cerchio
      raggio
      """

      # calcolo il punto medio tra i due punti di selezione
      ptMiddle = qad_utils.getMiddlePoint(ptLine, ptCircle)

      # angolo linea1
      angle = qad_utils.getAngleBy2Pts(line[0], line[1])
      # retta parallela da un lato della linea1 distante radius
      angle = angle + math.pi / 2
      pt1Par1Line = qad_utils.getPolarPointByPtAngle(line[0], angle, radius)
      pt2Par1Line = qad_utils.getPolarPointByPtAngle(line[1], angle, radius)
      # retta parallela dall'altro lato della linea1 distante radius
      angle = angle - math.pi
      pt1Par2Line = qad_utils.getPolarPointByPtAngle(line[0], angle, radius)
      pt2Par2Line = qad_utils.getPolarPointByPtAngle(line[1], angle, radius)
      
      # creo un cerchio con un raggio + grande
      circleTan = QadCircle()
      circleTan.set(circle.center, circle.radius + radius)
      ptIntList = circleTan.getIntersectionPointsWithInfinityLine(pt1Par1Line, pt2Par1Line)
      ptIntList2 = circleTan.getIntersectionPointsWithInfinityLine(pt1Par2Line, pt2Par2Line)
      ptIntList.extend(ptIntList2)

      if len(ptIntList) == 0: # nessuna intersezione
         return False
      
      # scelgo il punto più vicino al punto medio
      self.center = qad_utils.getNearestPoints(ptMiddle, ptIntList)[0]
      self.radius = radius
      return True


   #============================================================================
   # fromCircleCircleTanPtsRadius
   #============================================================================
   def fromCircleCircleTanPtsRadius(self, circle1, pt1, circle2, pt2, radius):
      """
      setta le caratteristiche del cerchio attraverso due cerchi di tangenza e un raggio:
      cerchio1 di tangenza (oggetto QadCircle)
      punto di selezione cerchio1
      cerchio2 di tangenza (oggetto QadCircle)
      punto di selezione cerchio2
      raggio
      """

      # calcolo il punto medio tra i due punti di selezione
      ptMiddle = qad_utils.getMiddlePoint(pt1, pt2)
      
      # creo due cerchi con un raggio + grande
      circle1Tan = QadCircle()
      circle1Tan.set(circle1.center, circle1.radius + radius)
      circle2Tan = QadCircle()
      circle2Tan.set(circle2.center, circle2.radius + radius)
      ptIntList = circle1Tan.getIntersectionPointsWithCircle(circle2Tan)

      if len(ptIntList) == 0: # nessuna intersezione
         return False
      
      # scelgo il punto più vicino al punto medio
      self.center = qad_utils.getNearestPoints(ptMiddle, ptIntList)[0]
      self.radius = radius
      return True


#===============================================================================
# QadCircleList lista di cerchi class
#===============================================================================
class QadCircleList():
   def __init__(self):
      self.circleList = [] # lista dei cerchi
      self.ndxGeomList = [] # lista degli indici delle geometrie cerchio
                            # la posizione é espressa con una lista (<index ogg. princ> [<index ogg. sec.>])


   def clear(self):
      del self.circleList[:] # svuoto la lista
      del self.ndxGeomList[:] # svuoto la lista 0-based


   #============================================================================
   # fromGeom
   #============================================================================
   def fromGeom(self, geom, atLeastNSegment = None):
      """
      setta la lista dei cerchi e degli estremi leggendo una geometria
      ritorna il numero di cerchi trovati
      """
      if atLeastNSegment is None:
         _atLeastNSegment = QadVariables.get(QadMsg.translate("Environment variables", "CIRCLEMINSEGMENTQTY"), 12)
      else:
         _atLeastNSegment = atLeastNSegment
      
      self.clear()
      circle = QadCircle()
      ndxGeom = 0
      # riduco in polilinee
      wkbType = geom.wkbType()
      if wkbType == QGis.WKBLineString:
         points = geom.asPolyline() # vettore di punti
         if circle.fromPolyline(points, _atLeastNSegment):
            self.circleList.append(circle)
            self.ndxGeomList.append([ndxGeom])
            return 1
      elif wkbType == QGis.WKBMultiLineString:
         lineList = geom.asMultiPolyline() # vettore di linee
         for points in lineList:
            if circle.fromPolyline(points, _atLeastNSegment):
               self.circleList.append(QadCircle(circle)) # ne faccio una copia
               self.ndxGeomList.append([ndxGeom])
            ndxGeom = ndxGeom + 1
      elif wkbType == QGis.WKBPolygon:
         iRing = -1
         lineList = geom.asPolygon() # vettore di linee
         for points in lineList:
            if circle.fromPolyline(points, _atLeastNSegment):
               self.circleList.append(QadCircle(circle)) # ne faccio una copia
               if iRing == -1: # si tratta della parte più esterna
                  self.ndxGeomList.append([ndxGeom])
               else:
                  self.ndxGeomList.append([ndxGeom, iRing])
            iRing = iRing + 1
      elif wkbType == QGis.WKBMultiPolygon:
         polygonList = geom.asMultiPolygon() # vettore di poligoni
         for polygon in polygonList:
            iRing = -1
            for points in polygon:
               if circle.fromPolyline(points, _atLeastNSegment):
                  self.circleList.append(QadCircle(circle)) # ne faccio una copia
                  if iRing == -1: # si tratta della parte più esterna
                     self.ndxGeomList.append([ndxGeom])
                  else:
                     self.ndxGeomList.append([ndxGeom, iRing])
               iRing = iRing + 1
            ndxGeom = ndxGeom + 1

      return len(self.circleList)


   #============================================================================
   # circleAt
   #============================================================================
   def circleAt(self, iGeomSubGeom):
      """
      cerca se esiste un cerchio alla geometria in posizione <iGeomSubGeom>.
      La posizione é espressa con una lista (<index ogg. princ> [<index ogg. sec.>]).
      Restituisce il cerchio oppure None se cerchio non trovato
      """
      if iGeomSubGeom is None: return None
      iGeom = iGeomSubGeom[0]
      iSubGeom = 0 if len(iGeomSubGeom) < 2 else iGeomSubGeom[1]
      
      i = 0
      for ndxGeom in self.ndxGeomList:
         if ndxGeom[0] == iGeom:
            if len(ndxGeom) > 1: # c'è anche la sottogeometria
               if ndxGeom[1] == iSubGeom: return self.circleList[i]
            else:
               return self.circleList[i]
         i = i + 1
      
      return None