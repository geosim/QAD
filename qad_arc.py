# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per la gestione degli archi
 
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


import qad_utils
from qad_circle import *
from qad_variables import *
from qad_msg import QadMsg


#===============================================================================
# QadArc arc class
#===============================================================================
class QadArc():
    
   def __init__(self, arc = None):
      if arc is not None:
         self.set(arc.center, arc.radius, arc.startAngle, arc.endAngle)
      else:    
         self.center = None
         self.radius = None
         self.startAngle = None
         self.endAngle = None     

   def whatIs(self):
      return "ARC"
   
   def set(self, center, radius, startAngle, endAngle):
      self.center = QgsPoint(center)
      self.radius = radius
      self.startAngle = startAngle
      self.endAngle = endAngle     

   def transform(self, coordTransform):
      """Transform this geometry as described by CoordinateTranasform ct."""
      self.center = coordTransform.transform(self.center)      

   def transformFromCRSToCRS(self, sourceCRS, destCRS):
      """Transform this geometry as described by CRS."""
      if (sourceCRS is not None) and (destCRS is not None) and sourceCRS != destCRS:       
         coordTransform = QgsCoordinateTransform(sourceCRS, destCRS) # trasformo le coord
         self.center = coordTransform.transform(self.center)
      
   def __eq__(self, arc):
      """self == other"""
      if self.center != arc.center or self.radius != arc.radius or \
         self.startAngle != arc.startAngle or self.endAngle != arc.endAngle:
         return False
      else:
         return True    
  
   def __ne__(self, arc):
      """self != other"""
      if self.center != arc.center or self.radius != arc.radius or \
         self.startAngle != arc.startAngle or self.endAngle != arc.endAngle:
         return True     
      else:
         return False    

   def totalAngle(self):
      if self.startAngle < self.endAngle:
         return self.endAngle - self.startAngle
      else:
         return (2 * math.pi - self.startAngle) + self.endAngle

   def length(self):
      return self.radius * self.totalAngle()     

   def getStartPt(self):
      return qad_utils.getPolarPointByPtAngle(self.center,
                                              self.startAngle,
                                              self.radius)
   def setStartAngleByPt(self, pt):
      # da usare per modificare un arco già definito
      angle = qad_utils.getAngleBy2Pts(self.center, pt)
      if angle == self.endAngle:
         return False
      else:
         self.startAngle = angle
         return True

   def getEndPt(self):
      return qad_utils.getPolarPointByPtAngle(self.center,
                                              self.endAngle,
                                              self.radius)
   def setEndAngleByPt(self, pt):
      # da usare per modificare un arco già definito
      angle = qad_utils.getAngleBy2Pts(self.center, pt)
      if angle == self.startAngle:
         return False
      else:
         self.endAngle = angle
         return True

   def isPtOnArc(self, point):
      dist =  qad_utils.getDistance(self.center, point)
      if qad_utils.doubleNear(self.radius, dist):
         angle = qad_utils.getAngleBy2Pts(self.center, point)
         return qad_utils.isAngleBetweenAngles(self.startAngle, self.endAngle, angle)
      else:
         return False


   def inverse(self):
      dummy = self.endAngle
      self.endAngle = self.startAngle 
      self.startAngle = dummy


   def getMiddlePt(self):
      halfAngle = self.totalAngle() / 2
      return qad_utils.getPolarPointByPtAngle(self.center,
                                              self.startAngle + halfAngle,
                                              self.radius)


   def getPtFromStart(self, distance):
      # la funzione restituisce un punto sull'arco ad una distanza nota da punto iniziale
      # (2*pi) : (2*pi*r) = angle : distance
      angle = distance / self.radius
      angle = self.startAngle + angle
      return qad_utils.getPolarPointByPtAngle(self.center, angle, self.radius)


   def getQuadrantPoints(self):
      result = []      

      angle = 0
      if qad_utils.isAngleBetweenAngles(self.startAngle, self.endAngle, angle) == True:
         result.append(QgsPoint(self.center.x() + self.radius, self.center.y()))
         
      angle = math.pi / 2
      if qad_utils.isAngleBetweenAngles(self.startAngle, self.endAngle, angle) == True:
         result.append(QgsPoint(self.center.x(), self.center.y() + self.radius))
         
      angle = math.pi
      if qad_utils.isAngleBetweenAngles(self.startAngle, self.endAngle, angle) == True:
         result.append(QgsPoint(self.center.x() - self.radius, self.center.y()))

      angle = math.pi * 3 / 2
      if qad_utils.isAngleBetweenAngles(self.startAngle, self.endAngle, angle) == True:
         result.append(QgsPoint(self.center.x(), self.center.y() - self.radius))

      return result


   #============================================================================
   # getTanPoints
   #============================================================================
   def getTanPoints(self, point):
      result = []
      
      circle = QadCircle()
      circle.set(self.center, self.radius)
      points = circle.getTanPoints(point)
      tot = len(points)
      for p in points:
         angle = qad_utils.getAngleBy2Pts(self.center, p)
         if qad_utils.isAngleBetweenAngles(self.startAngle, self.endAngle, angle) == True:
            result.append(p)
            
      return result


   #============================================================================
   # getTanDirectionOnPt
   #============================================================================
   def getTanDirectionOnPt(self, pt):
      angle = qad_utils.getAngleBy2Pts(self.center, pt)
      return qad_utils.normalizeAngle(angle + math.pi / 2) 

   
   #============================================================================
   # getTanDirectionOnStartPt
   #============================================================================
   def getTanDirectionOnStartPt(self):
      return self.getTanDirectionOnPt(self.getStartPt()) 


   #============================================================================
   # getTanDirectionOnEndPt
   #============================================================================
   def getTanDirectionOnEndPt(self):
      return self.getTanDirectionOnPt(self.getEndPt()) 


   #============================================================================
   # getPerpendicularPoints
   #============================================================================
   def getPerpendicularPoints(self, point):
      result = []
      angle = qad_utils.getAngleBy2Pts(self.center, point)
      if qad_utils.isAngleBetweenAngles(self.startAngle, self.endAngle, angle) == True:
         result.append( qad_utils.getPolarPointByPtAngle(self.center,
                                                         angle,
                                                         self.radius))

      angle = angle + math.pi         
      if qad_utils.isAngleBetweenAngles(self.startAngle, self.endAngle, angle) == True:
         result.append( qad_utils.getPolarPointByPtAngle(self.center,
                                                         angle,
                                                         self.radius))
         
      return result

   #============================================================================
   # getIntersectionPointsWithInfinityLine
   #============================================================================
   def getIntersectionPointsWithInfinityLine(self, p1, p2):
      result = []
      circle = QadCircle()
      circle.set(self.center, self.radius)
      intPtList = circle.getIntersectionPointsWithInfinityLine(p1, p2)
      for intPt in intPtList:
         if self.isPtOnArc(intPt):
            result.append(intPt)      
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
   # getIntersectionPointsWithCircle
   #============================================================================
   def getIntersectionPointsWithCircle(self, circle):
      result = []
      circle1 = QadCircle()
      circle1.set(self.center, self.radius)
      intPtList = circle1.getIntersectionPointsWithCircle(circle)
      for intPt in intPtList:
         if self.isPtOnArc(intPt):
            result.append(intPt)      
      return result


   #============================================================================
   # getIntersectionPointsWithArc
   #============================================================================
   def getIntersectionPointsWithArc(self, arc):
      result = []
      circle = QadCircle()
      circle.set(arc.center, arc.radius)
      intPtList = self.getIntersectionPointsWithCircle(circle)
      for intPt in intPtList:
         if arc.isPtOnArc(intPt):
            result.append(intPt)      
      return result

      
   #============================================================================
   # asPolyline
   #============================================================================
   def asPolyline(self, tolerance2ApproxCurve = None, atLeastNSegment = None):
      """
      ritorna una lista di punti che definisce l'arco
      """
      if tolerance2ApproxCurve is None:
         tolerance = QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE"))
      else:
         tolerance = tolerance2ApproxCurve
      
      if atLeastNSegment is None:
         _atLeastNSegment = QadVariables.get(QadMsg.translate("Environment variables", "ARCMINSEGMENTQTY"), 12)
      else:
         _atLeastNSegment = atLeastNSegment
      
      # Calcolo la lunghezza del segmento con pitagora
      dummy      = self.radius - tolerance
      if dummy <= 0: # se la tolleranza é troppo bassa rispetto al raggio
         SegmentLen = self.radius
      else:
         dummy      = (self.radius * self.radius) - (dummy * dummy)
         SegmentLen = math.sqrt(dummy) # radice quadrata
         SegmentLen = SegmentLen * 2
      
      if SegmentLen == 0: # se la tolleranza é troppo bassa la lunghezza del segmento diventa zero  
         return None
         
      # calcolo quanti segmenti ci vogliono (non meno di _atLeastNSegment)
      SegmentTot = math.ceil(self.length() / SegmentLen)
      if SegmentTot < _atLeastNSegment:
         SegmentTot = _atLeastNSegment
      
      points = []
      # primo punto
      pt = qad_utils.getPolarPointByPtAngle(self.center, self.startAngle, self.radius)
      points.append(pt)

      i = 1
      angle = self.startAngle
      offSetAngle = self.totalAngle() / SegmentTot
      while i < SegmentTot:
         angle = angle + offSetAngle
         pt = qad_utils.getPolarPointByPtAngle(self.center, angle, self.radius)
         points.append(pt)         
         i = i + 1

      # ultimo punto
      pt = qad_utils.getPolarPointByPtAngle(self.center, self.endAngle, self.radius)
      points.append(pt)
      return points
   
   
   #============================================================================
   # fromStartSecondEndPts
   #============================================================================
   def fromStartSecondEndPts(self, startPt, secondPt, endPt):
      """
      setta le caratteristiche dell'arco attraverso:
      punto iniziale
      secondo punto (intermedio)
      punto finale
      """
      points = [startPt, secondPt, endPt]
      # lista di punti, parte dal punto 0, almeno 2 segmenti
      if self.fromPolyline(points, 0, 2) is None:
         return False
      else:
         return True


   #============================================================================
   # fromStartCenterEndPts
   #============================================================================
   def fromStartCenterEndPts(self, startPt, centerPt, endPt):
      """
      setta le caratteristiche dell'arco attraverso:
      punto iniziale
      centro
      punto finale
      """
      if startPt == centerPt or startPt == endPt or endPt == centerPt:
         return False
      
      self.center = centerPt
      self.radius = qad_utils.getDistance(centerPt, startPt)
      self.startAngle = qad_utils.getAngleBy2Pts(centerPt, startPt)
      self.endAngle = qad_utils.getAngleBy2Pts(centerPt, endPt)
      return True
   

   #============================================================================
   # fromStartCenterPtsAngle
   #============================================================================
   def fromStartCenterPtsAngle(self, startPt, centerPt, angle):
      """
      setta le caratteristiche dell'arco attraverso:
      punto iniziale
      centro
      angolo inscritto
      """
      if startPt == centerPt or angle == 0:
         return False
      
      self.center = centerPt
      self.radius = qad_utils.getDistance(centerPt, startPt)
      self.startAngle = qad_utils.getAngleBy2Pts(centerPt, startPt)      
      self.endAngle = self.startAngle + angle
      if self.endAngle > math.pi * 2:
         self.endAngle = self.endAngle % (math.pi * 2) # modulo
      return True
   

   #============================================================================
   # fromStartCenterPtsChord
   #============================================================================
   def fromStartCenterPtsChord(self, startPt, centerPt, chord):
      """
      setta le caratteristiche dell'arco attraverso:
      punto iniziale
      centro
      lunghezza dela corda tra punto iniziale e finale
      """
      if startPt == centerPt or chord == 0:
         return False

      self.center = centerPt
      self.radius = qad_utils.getDistance(centerPt, startPt)
      if chord > 2 * self.radius:
         return False
      self.startAngle = qad_utils.getAngleBy2Pts(centerPt, startPt)
      # Teorema della corda
      angle = 2 * math.asin(chord / (2 * self.radius))
      self.endAngle = self.startAngle + angle
      return True
   

   #============================================================================
   # fromStartCenterPtsLength
   #============================================================================
   def fromStartCenterPtsLength(self, startPt, centerPt, length):
      """
      setta le caratteristiche dell'arco attraverso:
      punto iniziale
      centro
      lunghezza dela corda tra punto iniziale e finale
      """
      if startPt == centerPt or chord == 0:
         return False

      self.center = centerPt
      self.radius = qad_utils.getDistance(centerPt, startPt)
      circumference = 2 * math.pi * self.radius
      if length >= circumference:
         return False
      self.startAngle = qad_utils.getAngleBy2Pts(centerPt, startPt)
      
      #circumference : math.pi * 2 = length : angle
      angle = (math.pi * 2) * length / circumference
      self.endAngle = self.startAngle + angle
      return True


   #============================================================================
   # fromStartEndPtsAngle
   #============================================================================
   def fromStartEndPtsAngle(self, startPt, endPt, angle):
      """
      setta le caratteristiche dell'arco attraverso:
      punto iniziale
      punto finale
      angolo inscritto
      """
      if startPt == endPt or angle == 0:
         return False

      chord = qad_utils.getDistance(startPt, endPt)
      half_chord = chord / 2   
      # Teorema della corda
      self.radius = half_chord / math.sin(angle / 2)
      
      angleSegment = qad_utils.getAngleBy2Pts(startPt, endPt)
      ptMiddle = qad_utils.getMiddlePoint(startPt, endPt)
            
      # Pitagora
      distFromCenter = math.sqrt((self.radius * self.radius) - (half_chord * half_chord))
      if angle < math.pi: # se angolo < 180 gradi
         # aggiungo 90 gradi per cercare il centro a sinistra del segmento
         self.center = qad_utils.getPolarPointByPtAngle(ptMiddle, 
                                                        angleSegment + (math.pi / 2),
                                                        distFromCenter)
      else:
         # sottraggo 90 gradi per cercare il centro a destra del segmento
         self.center = qad_utils.getPolarPointByPtAngle(ptMiddle, 
                                                        angleSegment - (math.pi / 2),
                                                        distFromCenter)
      self.startAngle = qad_utils.getAngleBy2Pts(self.center, startPt)
      self.endAngle = qad_utils.getAngleBy2Pts(self.center, endPt)      
      return True


   #============================================================================
   # fromStartEndPtsTan
   #============================================================================
   def fromStartEndPtsTan(self, startPt, endPt, tan):
      """
      setta le caratteristiche dell'arco attraverso:
      punto iniziale
      punto finale
      direzione della tangente sul punto iniziale
      """
      if startPt == endPt:
         return False
      
      angleSegment = qad_utils.getAngleBy2Pts(startPt, endPt)
      if tan == angleSegment or tan == angleSegment - math.pi:
         return False
               
      chord = qad_utils.getDistance(startPt, endPt)
      half_chord = chord / 2
      ptMiddle = qad_utils.getMiddlePoint(startPt, endPt)

      angle = tan + (math.pi / 2)
      angle = angleSegment - angle
      distFromCenter = math.tan(angle) * half_chord
      self.center = qad_utils.getPolarPointByPtAngle(ptMiddle, 
                                                     angleSegment - (math.pi / 2),
                                                     distFromCenter)
      pt = qad_utils.getPolarPointByPtAngle(startPt, tan, chord)
      
      if qad_utils.leftOfLine(endPt, startPt, pt) < 0:
         # arco si sviluppa a sinistra della tangente
         self.startAngle = qad_utils.getAngleBy2Pts(self.center, startPt)
         self.endAngle = qad_utils.getAngleBy2Pts(self.center, endPt)
      else:
         # arco si sviluppa a destra della tangente
         self.startAngle = qad_utils.getAngleBy2Pts(self.center, endPt)
         self.endAngle = qad_utils.getAngleBy2Pts(self.center, startPt)
         
      self.radius = qad_utils.getDistance(startPt, self.center)
      return True


   #============================================================================
   # fromStartEndPtsRadius
   #============================================================================
   def fromStartEndPtsRadius(self, startPt, endPt, radius):
      """
      setta le caratteristiche dell'arco attraverso:
      punto iniziale
      punto finale
      raggio
      """
      if startPt == endPt or radius <= 0:
         return False

      chord = qad_utils.getDistance(startPt, endPt)
      half_chord = chord / 2
      if radius < half_chord:
         return False

      self.radius = radius
      angleSegment = qad_utils.getAngleBy2Pts(startPt, endPt)
      ptMiddle = qad_utils.getMiddlePoint(startPt, endPt)
            
      # Pitagora
      distFromCenter = math.sqrt((self.radius * self.radius) - (half_chord * half_chord))
      # aggiungo 90 gradi
      self.center = qad_utils.getPolarPointByPtAngle(ptMiddle, 
                                                     angleSegment + (math.pi / 2),
                                                     distFromCenter)
      self.startAngle = qad_utils.getAngleBy2Pts(self.center, startPt)
      self.endAngle = qad_utils.getAngleBy2Pts(self.center, endPt)
      return True


   #============================================================================
   # fromStartPtAngleRadiusChordDirection
   #============================================================================
   def fromStartPtAngleRadiusChordDirection(self, startPt, angle, radius, chordDirection):
      """
      setta le caratteristiche dell'arco attraverso:
      punto iniziale
      angolo inscritto
      raggio
      direzione della corda
      """
      if angle == 0 or angle == 2 * math.pi or radius <= 0:
         return False

      a = chordDirection + (math.pi / 2) - (angle / 2) 
      self.radius = radius
      self.center = qad_utils.getPolarPointByPtAngle(startPt, a, radius)
      endPt = qad_utils.getPolarPointByPtAngle(self.center, a + math.pi + angle, radius)
                 
      self.startAngle = qad_utils.getAngleBy2Pts(self.center, startPt)
      self.endAngle = qad_utils.getAngleBy2Pts(self.center, endPt)
      return True
   

   #============================================================================
   # fromPolyline
   #============================================================================
   def fromPolyline(self, points, startVertex, atLeastNSegment = None):
      """
      setta le caratteristiche del primo arco incontrato nella lista di punti
      partendo dalla posizione startVertex (0-indexed)
      ritorna la posizione nella lista del punto iniziale e finale se é stato trovato un arco
      altrimenti None
      N.B. in punti NON devono essere in coordinate geografiche
      """
      if atLeastNSegment is None:
         _atLeastNSegment = QadVariables.get(QadMsg.translate("Environment variables", "ARCMINSEGMENTQTY"), 12)
      else:
         _atLeastNSegment = atLeastNSegment
      
      totPoints = len(points)
      # perché sia un    arco ci vogliono almeno _atLeastNSegment segmenti
      if (totPoints - 1) - startVertex < _atLeastNSegment or _atLeastNSegment < 2:
         return None
      
      # per problemi di approssimazione dei calcoli
      epsilon = 1.e-4 # percentuale del raggio per ottenere max diff. di una distanza con il raggio

      InfinityLinePerpOnMiddle1 = None
      InfinityLinePerpOnMiddle2 = None
                                  
      nSegment = 0
      i = startVertex
      while i < totPoints - 1:
         if InfinityLinePerpOnMiddle1 is None:
            InfinityLinePerpOnMiddle1 = qad_utils.getInfinityLinePerpOnMiddle(points[i], points[i + 1])
            nStartVertex = i
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
                  nStartVertex = i
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
            notInArc = False
            currInfinityLinePerpOnMiddle = qad_utils.getInfinityLinePerpOnMiddle(points[i], points[i + 1])
            if currInfinityLinePerpOnMiddle is None:
               notInArc = True
            else:
               # calcolo il presunto centro con 2 segmenti
               currCenter = qad_utils.getIntersectionPointOn2InfinityLines(prevInfinityLinePerpOnMiddle[0], \
                                                                           prevInfinityLinePerpOnMiddle[1], \
                                                                           currInfinityLinePerpOnMiddle[0], \
                                                                           currInfinityLinePerpOnMiddle[1])
               if currCenter is None: # linee parallele
                  notInArc = True
               else:
                  # calcolo il verso dell'arco e l'angolo                 
                  clockWise = True if qad_utils.leftOfLine(points[i], points[i - 1], points[i + 1]) < 0 else False           
                  angle = angle + qad_utils.getAngleBy3Pts(points[i], center, points[i + 1], startClockWise) 
                             
                  # se la distanza è così vicina a quella del raggio
                  # il verso dell'arco deve essere quello iniziale
                  # l'angolo dell'arco non può essere >= 360 gradi
                  if qad_utils.ptNear(center, currCenter, tolerance) and \
                     startClockWise == clockWise and \
                     angle < 2 * math.pi:                              
                     nSegment = nSegment + 1 # anche questo segmento fa parte dell'arco
                     prevInfinityLinePerpOnMiddle = currInfinityLinePerpOnMiddle
                  else:
                     notInArc = True

            # questo segmento non fa parte del cerchio
            if notInArc:
               # se sono stati trovati un numero sufficiente di segmenti successivi
               if nSegment >= _atLeastNSegment:
                  # se é un angolo giro e il primo punto = ultimo punto allora points é un cerchio
                  if qad_utils.doubleNear(angle, 2 * math.pi) and points[0] == points[-1]: 
                     return None
                  break
               else:
                  i = i - 2
                  InfinityLinePerpOnMiddle1 = None
                  InfinityLinePerpOnMiddle2 = None

         i = i + 1
                        
      # se sono stati trovati un numero sufficiente di segmenti successivi
      if nSegment >= _atLeastNSegment:
         nEndVertex = nStartVertex + nSegment
         # se il punto iniziale e quello finale non coincidono é un arco         
         if points[nStartVertex] != points[nEndVertex]:
            self.center = center
            self.radius = radius
                           
            # se il verso é orario
            if startClockWise:
               # inverto l'angolo iniziale con quello finale
               self.endAngle = qad_utils.getAngleBy2Pts(center, points[nStartVertex])
               self.startAngle = qad_utils.getAngleBy2Pts(center, points[nEndVertex])
            else:
               self.startAngle = qad_utils.getAngleBy2Pts(center, points[nStartVertex])
               self.endAngle = qad_utils.getAngleBy2Pts(center, points[nEndVertex])                    

            return nStartVertex, nEndVertex
         
      return None
   

   #============================================================================
   # rotate
   #============================================================================
   def rotate(self, basePt, angle):
      self.center = qad_utils.rotatePoint(self.center, basePt, angle)
      newStartPt = qad_utils.rotatePoint(self.getStartPt(), basePt, angle)
      newEndPt = qad_utils.rotatePoint(self.getEndPt(), basePt, angle)
      self.startAngle = qad_utils.getAngleBy2Pts(self.center, newStartPt)
      self.endAngle = qad_utils.getAngleBy2Pts(self.center, newEndPt)
   

   #============================================================================
   # scale
   #============================================================================
   def scale(self, basePt, scale):
      self.center = qad_utils.scalePoint(self.center, basePt, scale)
      newStartPt = qad_utils.scalePoint(self.getStartPt(), basePt, scale)
      newEndPt = qad_utils.scalePoint(self.getEndPt(), basePt, scale)
      self.startAngle = qad_utils.getAngleBy2Pts(self.center, newStartPt)
      self.endAngle = qad_utils.getAngleBy2Pts(self.center, newEndPt)
   

   #============================================================================
   # mirror
   #============================================================================
   def mirror(self, mirrorPt, mirrorAngle):
      startPt = qad_utils.mirrorPoint(self.getStartPt(), mirrorPt, mirrorAngle)
      secondPt = qad_utils.mirrorPoint(self.getMiddlePt(), mirrorPt, mirrorAngle)
      endPt = qad_utils.mirrorPoint(self.getEndPt(), mirrorPt, mirrorAngle)
      self.fromStartSecondEndPts(startPt, secondPt, endPt)


#===============================================================================
# QadArcList lista di archi class
#===============================================================================
class QadArcList():
   def __init__(self):
      self.arcList = [] # lista di archi
      self.startEndVerticesList = [] # lista degli estremi (posizioni dei vertici iniziali e finali)

   def clear(self):
      del self.arcList[:] # svuoto la lista
      del self.startEndVerticesList[:] # svuoto la lista


   #============================================================================
   # fromPoints
   #============================================================================
   def fromPoints(self, points, atLeastNSegment = None):
      """
      setta la lista degli archi e degli estremi leggendo una sequenza di punti
      ritorna il numero di archi trovati
      """      
      if atLeastNSegment is None:
         _atLeastNSegment = QadVariables.get(QadMsg.translate("Environment variables", "ARCMINSEGMENTQTY"), 12)
      else:
         _atLeastNSegment = atLeastNSegment
      
      self.clear()
      startVertex = 0
      arc = QadArc()
      startEndVertices = arc.fromPolyline(points, startVertex, _atLeastNSegment)
      while startEndVertices is not None:
         _arc = QadArc(arc) # ne faccio una copia
         self.arcList.append(_arc)
         self.startEndVerticesList.append(startEndVertices)
         startVertex = startEndVertices[1] # l'ultimo punto dell'arco
         startEndVertices = arc.fromPolyline(points, startVertex, _atLeastNSegment)               

      return len(self.arcList)


   #============================================================================
   # fromGeom
   #============================================================================
   def fromGeom(self, geom, atLeastNSegment = None):
      """
      setta la lista degli archi e degli estremi leggendo una geometria
      ritorna il numero di archi trovati
      """
      if atLeastNSegment is None:
         _atLeastNSegment = QadVariables.get(QadMsg.translate("Environment variables", "ARCMINSEGMENTQTY"), 12)
      else:
         _atLeastNSegment = atLeastNSegment
      
      self.clear()
      arc = QadArc()
      incremental = 0 
      # riduco in polilinee
      geoms = qad_utils.asPointOrPolyline(geom)
      for g in geoms:
         points = g.asPolyline() # vettore di punti
         startVertex = 0
         startEndVertices = arc.fromPolyline(points, startVertex, _atLeastNSegment)
         while startEndVertices is not None:
            _arc = QadArc(arc) # ne faccio una copia
            self.arcList.append(_arc)
            self.startEndVerticesList.append([startEndVertices[0] + incremental, startEndVertices[1] + incremental])
            startVertex = startEndVertices[1] # l'ultimo punto dell'arco
            startEndVertices = arc.fromPolyline(points, startVertex, _atLeastNSegment)
                           
         incremental = len(points) - 1

      return len(self.arcList)

   #============================================================================
   # fromGeom
   #============================================================================
   def arcAt(self, afterVertex):
      """
      cerca se esiste un arco al segmento il cui secondo vertice é <afterVertex>
      restituisce una lista con <arco>, <lista con indice del punto iniziale e finale>
      oppure None se arco non trovato
      """
      i = 0
      for startEndVertices in self.startEndVerticesList:
         if afterVertex > startEndVertices[0] and afterVertex <= startEndVertices[1]:
            return self.arcList[i], startEndVertices
         i = i + 1
      
      return None
