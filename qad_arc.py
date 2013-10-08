# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per la gestione degli archi
 
                              -------------------
        begin                : 2013-05-22
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


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import math


import qad_debug
import qad_utils
from qad_circle import *
from qad_variables import *


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

   def transform(self, ct):
      """Transform this geometry as described by CoordinateTranasform ct."""
      self.center = coordTransform.transform(self.center)      

   def transformFromCRSToCRS(self, sourceCRS, destCRS):
      """Transform this geometry as described by CRS."""
      if (sourceCRS is not None) and (destCRS is not None) and sourceCRS != destCRS:       
         coordTransform = QgsCoordinateTransform(sourceCRS, destCRS) # trasformo le coord
         self.center =  coordTransform.transform(self.center)
      
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

   def getEndPt(self):
      return qad_utils.getPolarPointByPtAngle(self.center,
                                              self.endAngle,
                                              self.radius)

   def isPtOnArc(self, point):
      dist =  qad_utils.getDistance(self.center, point)
      if qad_utils.doubleNear(self.radius, dist, 1.e-9):
         angle = qad_utils.getAngleBy2Pts(self.center, point)
         return qad_utils.isAngleBetweenAngles(self.startAngle, self.endAngle, angle)
      else:
         return False

   def getMiddlePt(self):
      #qad_debug.breakPoint()      
      
      halfAngle = self.totalAngle() / 2
      return qad_utils.getPolarPointByPtAngle(self.center,
                                              self.startAngle + halfAngle,
                                              self.radius)

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
   # getTanDirectionOnStartPt
   #============================================================================
   def getTanDirectionOnStartPt(self):
      angle = qad_utils.getAngleBy2Pts(self.center, self.getStartPt())
      return angle + math.pi / 2


   #============================================================================
   # getTanDirectionOnEndPt
   #============================================================================
   def getTanDirectionOnEndPt(self):
      angle = qad_utils.getAngleBy2Pts(self.center, self.getEndPt())
      return angle + math.pi / 2


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
   # asPolyline
   #============================================================================
   def asPolyline(self, tolerance2ApproxCurve = None):
      """
      ritorna una lista di punti che definisce l'arco
      """
      #qad_debug.breakPoint()
      
      if tolerance2ApproxCurve is None:
         tolerance = QadVariables.get("TOLERANCE2APPROXCURVE")
      else:
         tolerance = tolerance2ApproxCurve
      
      # Calcolo la lunghezza del segmento con pitagora
      dummy      = self.radius - tolerance
      SegmentLen = math.sqrt((self.radius * self.radius) - (dummy * dummy)) # radice quadrata
      SegmentLen = SegmentLen * 2
      
      if SegmentLen == 0: # se la tolleranza è troppo bassa la lunghezza del segmento diventa zero  
         return None
         
      # calcolo quanti segmenti ci vogliono (non meno di 3)
      SegmentTot = math.ceil(self.length() / SegmentLen)
      if SegmentTot < 3:
         SegmentTot = 3
      
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

      #qad_debug.breakPoint()
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
      
      #qad_debug.breakPoint()
                
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
      #qad_debug.breakPoint()
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
   def fromPolyline(self, points, startVertex, atLeastNSegment = 3):
      """
      setta le caratteristiche del primo arco incontrato nella lista di punti
      partendo dalla posizione startVertex (0-indexed)
      ritorna la posizione nella lista del punto iniziale e finale se è stato trovato un arco
      altrimenti None
      """      
      totPoints = len(points)
      # perchè sia un arco ci vogliono almeno atLeastNSegment segmenti
      if (totPoints - 1) - startVertex < atLeastNSegment or atLeastNSegment < 2:
         return None

      epsilon = 1.e-2
            
      InfinityLinePerpOnMiddle1 = None
      InfinityLinePerpOnMiddle2 = None
                 
      #qad_debug.breakPoint()
      
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
                  InfinityLinePerpOnMiddle1 = InfinityLinePerpOnMiddle2[:] # copio la lista dei 2 punti
                  nStartVertex = i
                  nSegment = 1
               else:
                  nSegment = nSegment + 1
                  radius = qad_utils.getDistance(center, points[i + 1]) # calcolo il presunto raggio
         else: # e sono già stati valutati almeno 2 segmenti
            # calcolo la distanza del punto dal presunto centro
            dist = qad_utils.getDistance(center, points[i + 1])
            if qad_utils.doubleNear(radius, dist, epsilon):
               nSegment = nSegment + 1 # anche questo segmento fa parte dell'arco
            else: # questo segmento non fa parte del cerchio
               #qad_debug.breakPoint()
               # se sono stati trovati un numero sufficiente di segmenti successivi
               if nSegment >= atLeastNSegment:
                  break
               else:
                  i = i - 2
                  InfinityLinePerpOnMiddle1 = None
                  InfinityLinePerpOnMiddle2 = None
               
         i = i + 1
         
      # se sono stati trovati un numero sufficiente di segmenti successivi
      if nSegment >= atLeastNSegment:
         nEndVertex = nStartVertex + nSegment
         # se il punto iniziale e quello finale non coincidono è un arco         
         if points[nStartVertex] != points[nEndVertex]:
            self.center = center
            self.radius = radius
                           
            # se un punto intermedio da quello iniziale e finale dell'arco è a sinistra del
            # segmento che unisce i due punti
            if qad_utils.leftOfLine(points[nStartVertex + 1], \
                                    points[nStartVertex], \
                                    points[nEndVertex]) < 0:
               # inverto l'angolo iniziale con quello finale
               self.endAngle = qad_utils.getAngleBy2Pts(center, points[nStartVertex])
               self.startAngle = qad_utils.getAngleBy2Pts(center, points[nEndVertex])
            else:
               self.startAngle = qad_utils.getAngleBy2Pts(center, points[nStartVertex])
               self.endAngle = qad_utils.getAngleBy2Pts(center, points[nEndVertex])                    

            return nStartVertex, nEndVertex
         
      return None
   

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
   def fromPoints(self, points, atLeastNSegment = 3):
      """
      setta la lista degli archi e degli estremi leggendo una sequenza di punti
      ritorna il numero di archi trovati
      """
      self.clear()
      startVertex = 0
      arc = QadArc()
      startEndVertices = arc.fromPolyline(points, startVertex, atLeastNSegment)
      while startEndVertices is not None:
         _arc = QadArc(arc) # ne faccio una copia
         self.arcList.append(_arc)
         self.startEndVerticesList.append(startEndVertices)
         startVertex = startEndVertices[1] # l'ultimo punto dell'arco
         startEndVertices = arc.fromPolyline(points, startVertex, atLeastNSegment)               

      return len(self.arcList)


   #============================================================================
   # fromGeom
   #============================================================================
   def fromGeom(self, geom, atLeastNSegment = 3):
      """
      setta la lista degli archi e degli estremi leggendo una geometria
      ritorna il numero di archi trovati
      """
      self.clear()
      arc = QadArc()
      incremental = 0 
      # riduco in polilinee
      geoms = qad_utils.asPointOrPolyline(geom)
      for g in geoms:
         points = g.asPolyline() # vettore di punti
         startVertex = 0
         startEndVertices = arc.fromPolyline(points, startVertex, atLeastNSegment)
         while startEndVertices is not None:
            _arc = QadArc(arc) # ne faccio una copia
            self.arcList.append(_arc)
            self.startEndVerticesList.append([startEndVertices[0] + incremental, startEndVertices[1] + incremental])
            startVertex = startEndVertices[1] # l'ultimo punto dell'arco
            startEndVertices = arc.fromPolyline(points, startVertex, atLeastNSegment)
                           
         incremental = len(points) - 1

      return len(self.arcList)

   #============================================================================
   # fromGeom
   #============================================================================
   def arcAt(self, afterVertex):
      """
      cerca se esiste un arco al segmento il cui secondo vertice è <afterVertex>
      restituisce una lista con <arco>, <lista con punto iniziale e finale>
      oppure None se arco non trovato
      """
      i = 0
      for startEndVertices in self.startEndVerticesList:
         if afterVertex > startEndVertices[0] and afterVertex <= startEndVertices[1]:
            return self.arcList[i], startEndVertices
         i = i + 1
      
      return None
