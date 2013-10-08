# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando PLINE per disegnare una polilinea
 
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


# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *


import qad_debug
from qad_entsel_cmd import QadEntSelClass
from qad_getpoint import *
from qad_arc_maptool import *
from qad_arc import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_textwindow import *
import qad_utils


# Classe che gestisce il comando PLINE
class QadPLINECommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.get(35) # "PLINEA"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runPLINECommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/pline.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.get(98)
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.vertices = []
      self.realVerticesIndexes = [] # posizioni in vertices dei vertici reali 
                                    # (l'arco è approssimato a tanti segmenti)
      self.firstVertex = True
      self.rubberBand = QgsRubberBand(self.plugIn.canvas, False)
      self.ArcPointMapTool = None
      self.mode = "LINE"
      self.EntSelClass = None
      # se questo flag = True il comando serve all'interno di un altro comando per disegnare una linea
      # che non verrà salvata su un layer
      self.virtualCmd = False

   def __del__(self):
      QadCommandClass.__del__(self)
      self.rubberBand.hide()

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 3: # quando si è in fase di selezione entità
         return self.EntSelClass.getPointMapTool(drawMode)
      else:
         if self.mode == "LINE":
            return QadCommandClass.getPointMapTool(self, drawMode)
         elif self.mode == "ARC":
            return self.getArcPointMapTool()

   def waitForEntsel(self, msgMapTool, msg):
      if self.EntSelClass is not None:
         del self.EntSelClass            
      self.EntSelClass = QadEntSelClass(self.plugIn)
      # "Selezionare l'oggetto nel punto finale di ricalco: "
      self.EntSelClass.msg = QadMsg.get(178)
      self.getPointMapTool().setSnapType(QadSnapTypeEnum.END)
      self.EntSelClass.run(msgMapTool, msg)
         
   def getArcPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if (self.plugIn is not None):
         if self.ArcPointMapTool is None:
            self.ArcPointMapTool = Qad_arc_maptool(self.plugIn)
         return self.ArcPointMapTool
      else:
         return None

   def addRealVertex(self, point):
      self.realVerticesIndexes.append(len(self.vertices))
      self.vertices.append(point)     
      self.addPointToRubberBand(point)            
      self.plugIn.setLastPoint(self.vertices[-1])            
      self.plugIn.setLastSegmentAng(self.getLastSegmentAng())

   def delLastRealVertex(self):
      tot = len(self.realVerticesIndexes)
      if tot > 0:
         i = self.realVerticesIndexes[tot - 1]
         if tot > 1:
            iEnd = self.realVerticesIndexes[tot - 2]
         else:
            iEnd = -1
         
         del self.realVerticesIndexes[-1] # cancello ultimo vertice reale
         while i > iEnd:
            del self.vertices[-1] # cancello ultimo vertice
            self.removeLastPointToRubberBand()
            i = i - 1

         self.plugIn.setLastPoint(self.vertices[-1])            
         self.plugIn.setLastSegmentAng(self.getLastSegmentAng())

   def addArcVertices(self, points, inverse):
      tot = len(points)
      if inverse == False:
         i = 1 # salto il primo punto dell'arco che coincide con l'ultimo punto precedente
         while i < tot:
            self.vertices.append(points[i])     
            self.addPointToRubberBand(points[i])
            i = i + 1
      else:
         i = tot - 2 # salto l'ultimo punto dell'arco che coincide con l'ultimo punto precedente
         while i >= 0:
            self.vertices.append(points[i])     
            self.addPointToRubberBand(points[i])
            i = i - 1
                                    
      self.realVerticesIndexes.append(len(self.vertices) - 1)
      self.plugIn.setLastPoint(self.vertices[-1])            
      self.plugIn.setLastSegmentAng(self.getLastSegmentAng())


   def getLastSegmentAng(self):
      if len(self.vertices) < 2:
         result = self.plugIn.lastSegmentAng
      else:
         result = None
         lastVertex = self.vertices[-1] # ultimo vertice
         # verifico se ci sono archi
         arc = None
         arcList = QadArcList()
         if arcList.fromPoints(self.vertices) > 0:
            info = arcList.arcAt(len(self.vertices) - 1)
            if info is not None:
               arc = info[0]
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(lastVertex, arc.getStartPt(), 1.e-9):
                  result = arc.getTanDirectionOnStartPt() + math.pi
               else:
                  result = arc.getTanDirectionOnEndPt()
            
         if result is None:
            secondLastVertex = self.vertices[-2] # penultimo vertice
            result = qad_utils.getAngleBy2Pts(secondLastVertex, lastVertex)
      
      return result

   #============================================================================
   # WaitForArcMenu
   #============================================================================
   def WaitForArcMenu(self):
      # "Angolo" "Centro" "CHiudi"
      # "Direzione" "Linea" "Raggio"
      # "Secondo" "ANNulla"
      keyWords = QadMsg.get(68) + " " + QadMsg.get(66) + " " + QadMsg.get(41) +  " " + \
                 QadMsg.get(72) + " " + QadMsg.get(108) + " " + QadMsg.get(73) +  " " + \
                 QadMsg.get(109) + " " + QadMsg.get(110)
      # "Specificare punto finale dell'arco o [Angolo/CEntro/CHiudi/Direzione/LInea/Raggio/Secondo punto/ANNulla]: "
      msg = QadMsg.get(104)                

      #qad_debug.breakPoint()      
      self.arcStartPt = self.vertices[-1] # ultimo vertice
      self.arcTanOnStartPt = self.getLastSegmentAng()
   
      # Il segmento di arco è tangente al precedente segmento della polilinea
      # uso il map tool per l'arco
      self.mode = "ARC"
      self.getPointMapTool().arcStartPt = self.arcStartPt
      self.getPointMapTool().arcTanOnStartPt = self.arcTanOnStartPt
      self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_TAN_KNOWN_ASK_FOR_END_PT)
      
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)
      self.step = 101
      return

   #============================================================================
   # WaitForLineMenu
   #============================================================================
   def WaitForLineMenu(self):
      if self.firstVertex:
         # "Arco" "LUnghezza"
         # "ANnulla" "Ricalca"
         keyWords = QadMsg.get(38) + " " + QadMsg.get(39) + " " + \
                    QadMsg.get(40) + " " + QadMsg.get(175)
         # "Specificare punto successivo o [Arco/LUnghezza/ANnulla/Ricalca]: "
         msg = QadMsg.get(37)
      else:            
         # "Arco" "LUnghezza"
         # "ANnulla" "CHiudi" "Ricalca"
         keyWords = QadMsg.get(38) + " " + QadMsg.get(41) + " " + \
                    QadMsg.get(39) + " " + QadMsg.get(40) + " " + QadMsg.get(175)
         # "Specificare punto successivo o [Arco/CHiudi/LUnghezza/ANnulla/Ricalca]: "
         msg = QadMsg.get(42)            
         
      self.step = 1 # MENU PRINCIPLE
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)

   #============================================================================
   # addPointToRubberBand
   #============================================================================
   def addPointToRubberBand(self, point, doUpdate = True):
      numberOfVertices = self.rubberBand.numberOfVertices()
         
      if numberOfVertices == 2:
         # per un baco non ancora capito: se la linea ha solo 2 vertici e 
         # hanno la stessa x o y (linea orizzontale o verticale) 
         # la linea non viene disegnata perciò sposto un pochino la x o la y                 
         adjustedPoint = qad_utils.getAdjustedRubberBandVertex(self.rubberBand.getPoint(0, 0), point)                                                               
         self.rubberBand.addPoint(adjustedPoint, doUpdate)
      else:
         self.rubberBand.addPoint(point, doUpdate)
      
      
   #============================================================================
   # removeLastPointToRubberBand
   #============================================================================
   def removeLastPointToRubberBand(self):
      self.rubberBand.removeLastPoint()
         
         
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.get(128)) # "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate\n"
         return True # fine comando

      if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
         currLayer = qad_utils.getCurrLayerEditable(self.plugIn.canvas, QGis.Line)
         if currLayer is None:
            self.showMsg(QadMsg.get(53)) # "\nIl layer corrente non è valido\n"
            return True # fine comando
      
      # RICHIESTA PRIMO PUNTO 
      if self.step == 0: # inizio del comando
         # imposto la linea elastica
         self.getPointMapTool(QadGetPointDrawModeEnum.ELASTIC_LINE)
         # "Specificare punto: "
         # si appresta ad attendere un punto o enter
         #                        msg, inputType,              default, keyWords, nessun controllo
         self.waitFor(QadMsg.get(36), QadInputTypeEnum.POINT2D, None, "", \
                      QadInputModeEnum.NONE)
         self.step = 1
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO OPPURE MENU PRINCIPALE
      elif self.step == 1: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
                     qad_utils.addLineToLayer(self.plugIn, currLayer, self.vertices)
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
         
         if value is None:
            if self.firstVertex:
               if self.plugIn.lastPoint is not None:
                  value = self.plugIn.lastPoint
               else:
                  return True # fine comando
            else:
               if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
                  qad_utils.addLineToLayer(self.plugIn, currLayer, self.vertices)
               return True # fine comando
            
         
         if type(value) == unicode:
            if value == QadMsg.get(38): # "Arco"
               self.WaitForArcMenu()
               return False                              
            elif value == QadMsg.get(39): # "LUnghezza"
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, valori positivi
               # "Specificare lunghezza della linea:" 
               self.waitFor(QadMsg.get(43), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
               self.step = 2
               return False                              
            elif value == QadMsg.get(40): # "ANnulla"
               if len(self.vertices) >= 2:
                  self.delLastRealVertex() # cancello ultimo vertice reale
                  self.getPointMapTool().clear()
                  self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
                  self.getPointMapTool().setStartPoint(self.vertices[-1])
            elif value == QadMsg.get(41): # "CHiudi"
               newPt = self.vertices[0]
               self.addRealVertex(newPt) # aggiungo un nuovo vertice reale
               if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
                  qad_utils.addLineToLayer(self.plugIn, currLayer, self.vertices)
               return True # fine comando
            elif value == QadMsg.get(175): # "Ricalca"
               self.step = 3
               self.waitForEntsel(msgMapTool, msg)
               return False # continua

         elif type(value) == QgsPoint:
            self.addRealVertex(value) # aggiungo un nuovo vertice reale
            self.getPointMapTool().setStartPoint(value)        
         
         self.WaitForLineMenu()        
         if self.firstVertex:
            self.firstVertex = False
         
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Lunghezza" (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == QgsPoint:
            dist = qad_utils.getDistance(self.vertices[-1], value)             
         else:
            dist = value

         newPt = qad_utils.getPolarPointByPtAngle(self.vertices[-1], self.getLastSegmentAng(), dist)
         self.addRealVertex(newPt) # aggiungo un nuovo vertice reale

         self.getPointMapTool().setStartPoint(newPt)
         
         self.WaitForLineMenu()        
         
         self.step = 1 # torno al MENU PRINCIPLE
         
         return False

      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Selezionare l'oggetto nel punto finale di ricalco: " (da step = 1)
      elif self.step == 3:
         if self.EntSelClass.run(msgMapTool, msg) == True:
            if self.EntSelClass.entity.isInitialized() and self.EntSelClass.point is not None:
               # qad_debug.breakPoint()
               ptEnd = self.EntSelClass.point
               # cerco tutte le geometrie passanti per quel punto saltando i layer puntuali
               ptGeom = QgsGeometry.fromPoint(ptEnd)
               selSet = qad_utils.getSelSet("CO", self.getPointMapTool(), ptGeom, \
                                            None, False, True, True)
               mapRenderer = self.EntSelClass.getPointMapTool().canvas.mapRenderer()

               for layerEntitySet in selSet.layerEntitySetList:
                  layer = layerEntitySet.layer
                  geoms = layerEntitySet.getGeometryCollection()                  
                  transformedPt1 = mapRenderer.mapToLayerCoordinates(layer, self.vertices[-1])
                  transformedPt2 = mapRenderer.mapToLayerCoordinates(layer, ptEnd)                 
                  for geom in geoms:
                     # leggo la parte di linea tra transformedPt1 e transformedPt2
                     points = qad_utils.getLinePart(geom, transformedPt1, transformedPt2)                     
                     if points is not None:
                        # converto i punti della linea in map coordinates
                        transformedPoints = []
                        for point in points:
                           transformedPoints.append(mapRenderer.layerToMapCoordinates(layer, point))
                        
                        self.addArcVertices(transformedPoints, False) # aggiungo i punti in ordine
                        break

         self.WaitForLineMenu()
         self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.getPointMapTool().setStartPoint(self.vertices[-1])
         
         return False

      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare punto finale dell'arco o [Angolo/CEntro/CHiudi/Direzione/LInea/Raggio/Secondo punto/ANNulla]: " (da step = 1)
      elif self.step == 101: # dopo aver atteso un punto o una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
                     qad_utils.addLineToLayer(self.plugIn, currLayer, self.vertices)
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
               qad_utils.addLineToLayer(self.plugIn, currLayer, self.vertices)
            return True # fine comando
         
         #qad_debug.breakPoint()
         if type(value) == unicode:
            if value == QadMsg.get(68): # "Angolo"
               self.arcStartPt = self.vertices[-1]
               
               # imposto il map tool
               self.getPointMapTool().arcStartPt = self.arcStartPt
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_ANGLE)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, isNullable
               # "Specificare angolo inscritto: " 
               self.waitFor(QadMsg.get(61), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO)
               self.step = 102
            elif value == QadMsg.get(66): # "Centro"
               self.arcStartPt = self.vertices[-1]
               
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_CENTER_PT)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.get(58)) # "Specificare centro dell'arco: "               
               self.step = 108
            elif value == QadMsg.get(72): # "Direzione"
               self.arcStartPt = self.vertices[-1]
               
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_SECOND_PT)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, isNullable
               # "Specificare direzione tangente per il punto iniziale dell'arco: " 
               self.waitFor(QadMsg.get(64), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                            None, "", QadInputModeEnum.NOT_NULL)
               self.step = 112
            elif value == QadMsg.get(108): # "Linea"
               self.mode = "LINE"
               #qad_debug.breakPoint()
               self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
               self.getPointMapTool().setStartPoint(self.vertices[-1])      
               self.WaitForLineMenu()              
            elif value == QadMsg.get(73): # "Raggio"
               self.arcStartPt = self.vertices[-1]
               
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_RADIUS)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, valori positivi
               # "Specificare raggio dell'arco: " 
               self.waitFor(QadMsg.get(65), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
               self.step = 114
            elif value == QadMsg.get(109): # "Secondo"
               self.arcStartPt = self.vertices[-1]
               
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_SECOND_PT)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.get(107)) # "Specificare secondo punto sull'arco: "
               self.step = 119
            elif value == QadMsg.get(110): # "ANNulla"
               if len(self.vertices) >= 2:
                  self.delLastRealVertex() # cancello ultimo vertice reale
                  self.getPointMapTool().clear()
                  self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
                  self.WaitForArcMenu()
         elif type(value) == QgsPoint: # è stato inserito il punto finale dell'arco
            arc = QadArc()         
            if arc.fromStartEndPtsTan(self.arcStartPt, value, self.arcTanOnStartPt) == True:
               points = arc.asPolyline()
               if points is not None:
                  # se i punti sono così vicini da essere considerati uguali
                  if qad_utils.ptNear(self.arcStartPt, arc.getStartPt(), 1.e-9):
                     self.addArcVertices(points, False) # aggiungo i punti in ordine
                  else:
                     self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                                       
            self.WaitForArcMenu()
                       
         return False                              


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare angolo inscritto: " (da step = 101)
      elif self.step == 102: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == QgsPoint:
            self.arcAngle = qad_utils.getAngleBy2Pts(self.arcStartPt, value)             
         else:
            self.arcAngle = value

         # imposto il map tool
         self.getPointMapTool().arcAngle = self.arcAngle
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_END_PT)

         # "Centro" "Raggio"
         keyWords = QadMsg.get(66) + " " + QadMsg.get(73)
         msg = QadMsg.get(105) # "Specificare punto finale dell'arco o [Centro/Raggio]: "         
         # si appresta ad attendere un punto o una parola chiave         
         # msg, inputType, default, keyWords, isNullable
         self.waitFor(msg, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NOT_NULL)
         self.step = 103

         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare punto finale dell'arco o [Centro/Raggio]: : " (da step = 102)
      elif self.step == 103: # dopo aver atteso un punto o una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.get(66): # "Centro"
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_CENTER_PT)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.get(58)) # "Specificare centro dell'arco: "
               self.step = 104
            elif value == QadMsg.get(73): # "Raggio"
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_RADIUS)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, valori positivi
               # "Specificare raggio dell'arco: " 
               self.waitFor(QadMsg.get(65), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
               self.step = 105
         elif type(value) == QgsPoint: # è stato inserito il punto finale dell'arco
            arc = QadArc()         
            if arc.fromStartEndPtsAngle(self.arcStartPt, value, self.arcAngle) == True:
               points = arc.asPolyline()
               if points is not None:
                  # se i punti sono così vicini da essere considerati uguali
                  if qad_utils.ptNear(self.arcStartPt, arc.getStartPt(), 1.e-9):
                     self.addArcVertices(points, False) # aggiungo i punti in ordine
                  else:
                     self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                      
                  self.WaitForArcMenu()
                  return False
               
            # "Centro" "Raggio"
            keyWords = QadMsg.get(66) + " " + QadMsg.get(73)
            msg = QadMsg.get(105) # "Specificare punto finale dell'arco o [Centro/Raggio]: "         
            # si appresta ad attendere un punto o una parola chiave         
            # msg, inputType, default, keyWords, isNullable
            self.waitFor(msg, \
                         QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                         None, \
                         keyWords, QadInputModeEnum.NOT_NULL)
            
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA CENTRO DELL'ARCO (da step = 103)
      elif self.step == 104: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
         
         arc = QadArc()         
         if arc.fromStartCenterPtsAngle(self.arcStartPt, value, self.arcAngle) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt(), 1.e-9):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                  
               self.WaitForArcMenu()
               return False      

         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.get(58)) # "Specificare centro dell'arco: "
                 
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA RAGGIO (da step = 103)
      elif self.step == 105: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == QgsPoint:
            self.arcStartPtForRadius = value
            
            # imposto il map tool
            self.getPointMapTool().arcStartPtForRadius = self.arcStartPtForRadius
            self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_SECONDPTRADIUS)
         
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.get(93)) # "Specificare secondo punto: "
            self.step = 106
         else:
            self.arcRadius = value
            self.plugIn.setLastRadius(self.arcRadius)

            # imposto il map tool
            self.getPointMapTool().arcRadius = self.arcRadius
            self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_RADIUS_KNOWN_ASK_FOR_CHORDDIRECTION)
            # si appresta ad attendere un punto o un numero reale         
            # msg, inputType, default, keyWords, isNullable
            # "Specificare direzione della corda per l'arco <{0}>: "
            msg = QadMsg.get(106)
            self.waitFor(msg.format(str(self.getLastSegmentAng())), \
                         QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                         None, "", QadInputModeEnum.NOT_NULL)
            self.step = 107
            
         return False                                          


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO DEL RAGGIO (da step = 105)
      elif self.step == 106: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         self.arcRadius = qad_utils.getDistance(self.arcStartPtForRadius, value)
         self.plugIn.setLastRadius(self.arcRadius)     

         # imposto il map tool
         self.getPointMapTool().arcRadius = self.arcRadius
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_RADIUS_KNOWN_ASK_FOR_CHORDDIRECTION)
         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, isNullable
         # "Specificare direzione della corda per l'arco <{0}>: "
         msg = QadMsg.get(106)
         self.waitFor(msg.format(str(self.getLastSegmentAng())), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                      None, "", QadInputModeEnum.NOT_NULL)
         self.step = 107


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DIREZIONE DELLA CORDA DELL'ARCO (da step = 106 e 107)
      elif self.step == 107: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
         
         if type(value) == QgsPoint:
            self.arcChordDirection = qad_utils.getAngleBy2Pts(self.arcStartPt, value)             
         else:
            self.arcChordDirection = value
         
         arc = QadArc()
         if arc.fromStartPtAngleRadiusChordDirection(self.arcStartPt, self.arcAngle, \
                                                     self.arcRadius, self.arcChordDirection) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt(), 1.e-9):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                  
               self.WaitForArcMenu()
               return False      

         # imposto il map tool
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_RADIUS_KNOWN_ASK_FOR_CHORDDIRECTION)
         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, isNullable
         # "Specificare direzione della corda per l'arco <{0}>: "
         msg = QadMsg.get(106)
         self.waitFor(msg.format(str(self.getLastSegmentAng())), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                      None, "", QadInputModeEnum.NOT_NULL)
                 
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA CENTRO DELL'ARCO (da step = 101)
      elif self.step == 108: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         self.arcCenterPt = value

         # imposto il map tool
         self.getPointMapTool().arcCenterPt = self.arcCenterPt
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_END_PT)

         # "Angolo" "Lunghezza"
         keyWords = QadMsg.get(68) + " " + QadMsg.get(69)
         msg = QadMsg.get(60) # "Specificare punto finale dell'arco o [Angolo/Lunghezza corda]: "                   
         # si appresta ad attendere un punto o una parola chiave         
         # msg, inputType, default, keyWords, isNullable
         self.waitFor(msg, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NOT_NULL)
         self.step = 109      
         
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare punto finale dell'arco o [Angolo/Lunghezza corda]: " (da step = 108)
      elif self.step == 109: # dopo aver atteso un punto o una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:  
            if value == QadMsg.get(68): # "Angolo"
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_ANGLE)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, valori <> 0
               # "Specificare angolo inscritto: " 
               self.waitFor(QadMsg.get(61), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO)
               self.step = 110
               return False                              
            elif value == QadMsg.get(69): # "Lunghezza"
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_CHORD)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, valori positivi
               # "Specificare lunghezza della corda: " 
               self.waitFor(QadMsg.get(62), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
               self.step = 111
               return False                              
         elif type(value) == QgsPoint: # se è stato inserito il punto finale dell'arco
            self.arcEndPt = value
                     
            arc = QadArc()         
            if arc.fromStartCenterEndPts(self.arcStartPt, self.arcCenterPt, self.arcEndPt) == True:
               points = arc.asPolyline()
               if points is not None:
                  # se i punti sono così vicini da essere considerati uguali
                  if qad_utils.ptNear(self.arcStartPt, arc.getStartPt(), 1.e-9):
                     self.addArcVertices(points, False) # aggiungo i punti in ordine
                  else:
                     self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                     
                  self.WaitForArcMenu()
                  return False      
            
         # "Angolo" "Lunghezza"
         keyWords = QadMsg.get(68) + " " + QadMsg.get(69)
         msg = QadMsg.get(60) # "Specificare punto finale dell'arco o [Angolo/Lunghezza corda]: "                   
         # si appresta ad attendere un punto o una parola chiave         
         # msg, inputType, default, keyWords, isNullable
         self.waitFor(msg, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NOT_NULL)
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare angolo inscritto: " (da step = 109)
      elif self.step == 110: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == QgsPoint:
            self.arcAngle = qad_utils.getAngleBy2Pts(self.arcCenterPt, value)             
         else:
            self.arcAngle = value

         arc = QadArc()         
         if arc.fromStartCenterPtsAngle(self.arcStartPt, self.arcCenterPt, self.arcAngle) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt(), 1.e-9):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                  
               self.WaitForArcMenu()
               return False      

         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, isNullable
         # "Specificare angolo inscritto: " 
         self.waitFor(QadMsg.get(61), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                      None, "", \
                      QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO)

         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare lunghezza della corda: " (da step = 109)
      elif self.step == 111: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == QgsPoint:
            self.arcChord = qad_utils.getDistance(self.arcStartPt, value)             
         else:
            self.arcChord = value

         arc = QadArc()         
         if arc.fromStartCenterPtsChord(self.arcStartPt, self.arcCenterPt, self.arcChord) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt(), 1.e-9):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                  
               self.WaitForArcMenu()
               return False      

         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, valori positivi
         # "Specificare lunghezza della corda: " 
         self.waitFor(QadMsg.get(62), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                      None, "", \
                      QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)

         return False

     
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare direzione tangente per il punto iniziale dell'arco: " (da step = 101)
      elif self.step == 112: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == QgsPoint:
            self.arcTanOnStartPt = qad_utils.getAngleBy2Pts(self.arcStartPt, value)             
         else:
            self.arcTanOnStartPt = value

         # imposto il map tool
         self.getPointMapTool().arcTanOnStartPt = self.arcTanOnStartPt
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_TAN_KNOWN_ASK_FOR_END_PT)

         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.get(57)) # "Specificare punto finale dell'arco: "
         self.step = 113
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO FINALE DELL'ARCO (da step = 112)
      elif self.step == 113: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
         
         arc = QadArc()
         if arc.fromStartEndPtsTan(self.arcStartPt, value, self.arcTanOnStartPt) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt(), 1.e-9):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                  
               self.WaitForArcMenu()
               return False      

         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.get(57)) # "Specificare punto finale dell'arco: "
                 
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA RAGGIO (da step = 101)
      elif self.step == 114: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == QgsPoint:
            self.arcStartPtForRadius = value
            
            # imposto il map tool
            self.getPointMapTool().arcStartPtForRadius = self.arcStartPtForRadius
            self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_SECONDPTRADIUS)
         
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.get(93)) # "Specificare secondo punto: "
            self.step = 115
         else:
            self.arcRadius = value
            self.plugIn.setLastRadius(self.arcRadius)

            # imposto il map tool
            self.getPointMapTool().arcRadius = self.arcRadius
            self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_RADIUS_KNOWN_ASK_FOR_END_PT)
            # si appresta ad attendere un punto o un numero reale         
            # msg, inputType, default, keyWords, isNullable
            # "Specificare punto finale dell'arco o [Angolo]: "
            msg = QadMsg.get(113)
            # "Angolo"
            self.waitFor(msg.format(str(self.getLastSegmentAng())), \
                         QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                         None, QadMsg.get(68), QadInputModeEnum.NOT_NULL)
            self.step = 116
            
         return False                                          


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO DEL RAGGIO (da step = 114)
      elif self.step == 115: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         self.arcRadius = qad_utils.getDistance(self.arcStartPtForRadius, value)
         self.plugIn.setLastRadius(self.arcRadius)     

         # imposto il map tool
         self.getPointMapTool().arcRadius = self.arcRadius
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_RADIUS_KNOWN_ASK_FOR_END_PT)
         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, isNullable
         # "Specificare punto finale dell'arco o [Angolo]: "
         msg = QadMsg.get(113)
         # "Angolo"
         self.waitFor(msg, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, QadMsg.get(68), QadInputModeEnum.NOT_NULL)
         self.step = 116
      
         return False
      
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare punto finale dell'arco o [Angolo]: " (da step = 114 o 115)
      elif self.step == 116: # dopo aver atteso un punto o una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
         
         #qad_debug.breakPoint()
         if type(value) == unicode:
            if value == QadMsg.get(68): # "Angolo"
               
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_ANGLE)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, isNullable
               # "Specificare angolo inscritto: " 
               self.waitFor(QadMsg.get(61), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO)
               self.step = 117
         elif type(value) == QgsPoint: # è stato inserito il punto finale dell'arco
            arc = QadArc()         
            if arc.fromStartEndPtsRadius(self.arcStartPt, value, self.arcRadius) == True:
               points = arc.asPolyline()
               if points is not None:
                  # se i punti sono così vicini da essere considerati uguali
                  if qad_utils.ptNear(self.arcStartPt, arc.getStartPt(), 1.e-9):
                     self.addArcVertices(points, False) # aggiungo i punti in ordine
                  else:
                     self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                     
            self.WaitForArcMenu()
                       
         return False                              
      

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare angolo inscritto: " (da step = 116)
      elif self.step == 117: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == QgsPoint:
            self.arcAngle = qad_utils.getAngleBy2Pts(self.arcStartPt, value)             
         else:
            self.arcAngle = value

         # imposto il map tool
         self.getPointMapTool().arcAngle = self.arcAngle
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_RADIUS_KNOWN_ASK_FOR_CHORDDIRECTION)
         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, isNullable
         # "Specificare direzione della corda per l'arco <{0}>: "
         msg = QadMsg.get(106)
         self.waitFor(msg.format(str(self.getLastSegmentAng())), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                      None, "", QadInputModeEnum.NOT_NULL)
         self.step = 118

         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DIREZIONE DELLA CORDA DELL'ARCO (da step = 117)
      elif self.step == 118: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
         
         if type(value) == QgsPoint:
            self.arcChordDirection = qad_utils.getAngleBy2Pts(self.arcStartPt, value)             
         else:
            self.arcChordDirection = value
         
         arc = QadArc()
         if arc.fromStartPtAngleRadiusChordDirection(self.arcStartPt, self.arcAngle, \
                                                     self.arcRadius, self.arcChordDirection) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt(), 1.e-9):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
               
               self.WaitForArcMenu()
               return False      

         # imposto il map tool
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_RADIUS_KNOWN_ASK_FOR_CHORDDIRECTION)
         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, isNullable
         # "Specificare direzione della corda per l'arco <{0}>: "
         msg = QadMsg.get(106)
         self.waitFor(msg.format(str(self.getLastSegmentAng())), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                      None, "", QadInputModeEnum.NOT_NULL)
                 
         return False
      
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO (da step = 101)
      elif self.step == 119: # dopo aver atteso un punto o una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         self.arcSecondPt = value
         # imposto il map tool
         self.getPointMapTool().arcSecondPt = self.arcSecondPt
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_SECOND_PT_KNOWN_ASK_FOR_END_PT)

         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.get(57)) # "Specificare punto finale dell'arco: "
         self.step = 120
                  
         return False
      
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO FINALE DELL'ARCO (da step = 119)
      elif self.step == 120: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         self.arcEndPt = value
         
         arc = QadArc()         
         if arc.fromStartSecondEndPts(self.arcStartPt, self.arcSecondPt, self.arcEndPt) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt(), 1.e-9):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                  
               self.WaitForArcMenu()
               return False      
      
         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.get(57)) # "Specificare punto finale dell'arco: "     
         return False      