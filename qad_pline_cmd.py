# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando PLINE per disegnare una polilinea
 
                              -------------------
        begin                : 2013-05-22
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


from qad_entsel_cmd import QadEntSelClass
from qad_getpoint import *
from qad_arc_maptool import *
from qad_arc import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_textwindow import *
import qad_utils
import qad_layer
from qad_rubberband import createRubberBand


# Classe che gestisce il comando PLINE
class QadPLINECommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "PLINEA")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runPLINECommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/pline.png")

   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_PLINE", "Disegna una polilinea mediante diversi metodi.\n\nUna polilinea é una sequenza di segmenti retti,\narchi o una combinazione dei due.")
   
   def __init__(self, plugIn, asToolForMPolygon = False):
      QadCommandClass.__init__(self, plugIn)
      self.vertices = []
      self.realVerticesIndexes = [] # posizioni in vertices dei vertici reali 
                                    # (l'arco è approssimato a tanti segmenti)
      self.firstVertex = True
      
      self.asToolForMPolygon = asToolForMPolygon
      if self.asToolForMPolygon:
         self.rubberBand = createRubberBand(self.plugIn.canvas, QGis.Polygon)
      else:
         self.rubberBand = createRubberBand(self.plugIn.canvas, QGis.Line)
         
      self.ArcPointMapTool = None
      self.mode = "LINE"
      self.EntSelClass = None
      # se questo flag = True il comando serve all'interno di un altro comando per disegnare una linea
      # che non verrà salvata su un layer
      self.virtualCmd = False

   def __del__(self):
      QadCommandClass.__del__(self)
      self.rubberBand.hide()
      self.plugIn.canvas.scene().removeItem(self.rubberBand)

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 3: # quando si é in fase di selezione entità
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
      self.EntSelClass.msg = QadMsg.translate("Command_PLINE", "Selezionare l'oggetto nel punto finale di ricalco: ")
      # scarto la selezione di punti
      self.EntSelClass.checkPointLayer = False
      self.EntSelClass.checkLineLayer = True
      self.EntSelClass.checkPolygonLayer = True
      self.EntSelClass.onlyEditableLayers = False         
      
      self.EntSelClass.getPointMapTool().setSnapType(QadSnapTypeEnum.END)
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
               if qad_utils.ptNear(lastVertex, arc.getStartPt()):
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
      keyWords = QadMsg.translate("Command_PLINE", "Angolo") + "/" + \
                 QadMsg.translate("Command_PLINE", "CEntro") + "/" + \
                 QadMsg.translate("Command_PLINE", "CHiudi") +  "/" + \
                 QadMsg.translate("Command_PLINE", "Direzione") + "/" + \
                 QadMsg.translate("Command_PLINE", "LInea") + "/" + \
                 QadMsg.translate("Command_PLINE", "Raggio") +  "/" + \
                 QadMsg.translate("Command_PLINE", "Secondo punto") + "/" + \
                 QadMsg.translate("Command_PLINE", "ANNulla")
      prompt = QadMsg.translate("Command_PLINE", "Specificare punto finale dell'arco o [{0}]: ").format(keyWords)

      self.arcStartPt = self.vertices[-1] # ultimo vertice
      self.arcTanOnStartPt = self.getLastSegmentAng()
   
      # Il segmento di arco é tangente al precedente segmento della polilinea
      # uso il map tool per l'arco
      self.mode = "ARC"
      self.getPointMapTool().arcStartPt = self.arcStartPt
      self.getPointMapTool().arcTanOnStartPt = self.arcTanOnStartPt
      self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_TAN_KNOWN_ASK_FOR_END_PT)
      
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
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
         keyWords = QadMsg.translate("Command_PLINE", "Arco") + "/" + \
                    QadMsg.translate("Command_PLINE", "LUnghezza") + "/" + \
                    QadMsg.translate("Command_PLINE", "ANnulla") + "/" + \
                    QadMsg.translate("Command_PLINE", "Ricalca")
      else:            
         keyWords = QadMsg.translate("Command_PLINE", "Arco") + "/" + \
                    QadMsg.translate("Command_PLINE", "CHiudi") + "/" + \
                    QadMsg.translate("Command_PLINE", "LUnghezza") + "/" + \
                    QadMsg.translate("Command_PLINE", "ANnulla") + "/" + \
                    QadMsg.translate("Command_PLINE", "Ricalca")
      prompt = QadMsg.translate("Command_PLINE", "Specificare punto successivo o [{0}]: ").format(keyWords)
         
      self.step = 1 # MENU PRINCIPLE
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
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
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando

      if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
         currLayer, errMsg = qad_layer.getCurrLayerEditable(self.plugIn.canvas, QGis.Line)
         if currLayer is None:
            self.showErr(errMsg)
            return True # fine comando
      
      # RICHIESTA PRIMO PUNTO 
      if self.step == 0: # inizio del comando
         # imposto la linea elastica
         self.getPointMapTool(QadGetPointDrawModeEnum.ELASTIC_LINE)
         # si appresta ad attendere un punto o enter
         #                        msg, inputType,              default, keyWords, nessun controllo
         self.waitFor(QadMsg.translate("Command_PLINE", "Specificare punto iniziale: "), \
                      QadInputTypeEnum.POINT2D, None, "", QadInputModeEnum.NONE)
         self.step = 1
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO OPPURE MENU PRINCIPALE
      elif self.step == 1: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
                     qad_layer.addLineToLayer(self.plugIn, currLayer, self.vertices)
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
                  qad_layer.addLineToLayer(self.plugIn, currLayer, self.vertices)
               return True # fine comando
            
         
         if type(value) == unicode:
            if value == QadMsg.translate("Command_PLINE", "Arco"):
               self.WaitForArcMenu()
               return False                              
            elif value == QadMsg.translate("Command_PLINE", "LUnghezza"):
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, valori positivi
               # "Specificare lunghezza della linea: " 
               self.waitFor(QadMsg.translate("Command_PLINE", "Specificare lunghezza della linea: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
               self.step = 2
               return False                              
            elif value == QadMsg.translate("Command_PLINE", "ANnulla"):
               if len(self.vertices) >= 2:
                  self.delLastRealVertex() # cancello ultimo vertice reale
                  self.getPointMapTool().clear()
                  self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
                  self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
                  self.getPointMapTool().setStartPoint(self.vertices[-1])
            elif value == QadMsg.translate("Command_PLINE", "CHiudi"):
               newPt = self.vertices[0]
               self.addRealVertex(newPt) # aggiungo un nuovo vertice reale
               if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
                  qad_layer.addLineToLayer(self.plugIn, currLayer, self.vertices)
               return True # fine comando
            elif value == QadMsg.translate("Command_PLINE", "Ricalca"): # "Ricalca"
               self.step = 3
               self.waitForEntsel(msgMapTool, msg)
               return False # continua

         elif type(value) == QgsPoint:
            self.addRealVertex(value) # aggiungo un nuovo vertice reale
            self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
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
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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

         self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
         self.getPointMapTool().setStartPoint(newPt)
         
         self.WaitForLineMenu()        
         
         self.step = 1 # torno al MENU PRINCIPLE
         
         return False

      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Selezionare l'oggetto nel punto finale di ricalco: " (da step = 1)
      elif self.step == 3:
         entSelected = False
         if self.EntSelClass.run(msgMapTool, msg) == True:
            if self.EntSelClass.entity.isInitialized() and self.EntSelClass.point is not None:
               entSelected = True
               ptEnd = self.EntSelClass.point
               # cerco tutte le geometrie passanti per quel punto saltando i layer puntuali
               ptGeom = QgsGeometry.fromPoint(ptEnd)
               selSet = qad_utils.getSelSet("CO", self.getPointMapTool(), ptGeom, \
                                            None, False, True, True)
               mapRenderer = self.EntSelClass.getPointMapTool().canvas.mapRenderer()

               for layerEntitySet in selSet.layerEntitySetList:
                  layer = layerEntitySet.layer
                  geoms = layerEntitySet.getGeometryCollection()                  
                  transformedPt1 = self.mapToLayerCoordinates(layer, self.vertices[-1])
                  transformedPt2 = self.mapToLayerCoordinates(layer, ptEnd)                 
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
               
               del self.EntSelClass
               self.EntSelClass = None

         self.WaitForLineMenu()
         if entSelected:
            self.getPointMapTool().refreshSnapType() # aggiorno lo snapType che può essere variato dal maptool di selezione entità                             
         self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
         self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
         self.getPointMapTool().setStartPoint(self.vertices[-1])
         
         return False

      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare punto finale dell'arco o [Angolo/CEntro/CHiudi/Direzione/LInea/Raggio/Secondo punto/ANNulla]: " (da step = 1)
      elif self.step == 101: # dopo aver atteso un punto o una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
                     qad_layer.addLineToLayer(self.plugIn, currLayer, self.vertices)
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
               qad_layer.addLineToLayer(self.plugIn, currLayer, self.vertices)
            return True # fine comando
         
         if type(value) == unicode:
            if value == QadMsg.translate("Command_PLINE", "Angolo"):
               self.arcStartPt = self.vertices[-1]
               
               # imposto il map tool
               self.getPointMapTool().arcStartPt = self.arcStartPt
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_ANGLE)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, isNullable
               self.waitFor(QadMsg.translate("Command_PLINE", "Specificare angolo inscritto: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO)
               self.step = 102
            elif value == QadMsg.translate("Command_PLINE", "CEntro"):
               self.arcStartPt = self.vertices[-1]
               
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_CENTER_PT)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.translate("Command_PLINE", "Specificare centro dell'arco: "))               
               self.step = 108
            elif value == QadMsg.translate("Command_PLINE", "CHiudi"):
               arc = QadArc()

               if arc.fromStartEndPtsTan(self.arcStartPt, self.vertices[0], self.arcTanOnStartPt) == True:
                  points = arc.asPolyline()
                  if points is not None:
                     # se i punti sono così vicini da essere considerati uguali
                     if qad_utils.ptNear(self.arcStartPt, arc.getStartPt()):
                        self.addArcVertices(points, False) # aggiungo i punti in ordine
                     else:
                        self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                     if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
                        qad_layer.addLineToLayer(self.plugIn, currLayer, self.vertices)

                     return True # fine comando
            elif value == QadMsg.translate("Command_PLINE", "Direzione"):
               self.arcStartPt = self.vertices[-1]
               
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_SECOND_PT)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, isNullable
               self.waitFor(QadMsg.translate("Command_PLINE", "Specificare direzione tangente per il punto iniziale dell'arco: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                            None, "", QadInputModeEnum.NOT_NULL)
               self.step = 112
            elif value == QadMsg.translate("Command_PLINE", "LInea"):
               self.mode = "LINE"
               self.getPointMapTool().refreshSnapType() # riagggiorno lo snapType che può essere variato dal maptool dell'arco
               self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
               self.getPointMapTool().setStartPoint(self.vertices[-1])      
               self.WaitForLineMenu()              
            elif value == QadMsg.translate("Command_PLINE", "Raggio"): # "Raggio"
               self.arcStartPt = self.vertices[-1]
               
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_RADIUS)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, valori positivi
               self.waitFor(QadMsg.translate("Command_PLINE", "Specificare raggio dell'arco: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
               self.step = 114
            elif value == QadMsg.translate("Command_PLINE", "Secondo punto"):
               self.arcStartPt = self.vertices[-1]
               
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_SECOND_PT)
               # si appresta ad attendere un punto               
               self.waitForPoint(QadMsg.translate("Command_PLINE", "Specificare secondo punto sull'arco: "))
               self.step = 119
            elif value == QadMsg.translate("Command_PLINE", "ANNulla"):
               if len(self.vertices) >= 2:
                  self.delLastRealVertex() # cancello ultimo vertice reale
                  self.getPointMapTool().clear()
                  self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
                  self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
                  self.WaitForArcMenu()
         elif type(value) == QgsPoint: # é stato inserito il punto finale dell'arco
            arc = QadArc()         
            if arc.fromStartEndPtsTan(self.arcStartPt, value, self.arcTanOnStartPt) == True:
               points = arc.asPolyline()
               if points is not None:
                  # se i punti sono così vicini da essere considerati uguali
                  if qad_utils.ptNear(self.arcStartPt, arc.getStartPt()):
                     self.addArcVertices(points, False) # aggiungo i punti in ordine
                  else:
                     self.addArcVertices(points, True) # aggiungo i punti in ordine inverso
                  self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea 
                                       
            self.WaitForArcMenu()
                       
         return False                              


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare angolo inscritto: " (da step = 101)
      elif self.step == 102: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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

         keyWords = QadMsg.translate("Command_PLINE", "Centro") + "/" + \
                    QadMsg.translate("Command_PLINE", "Raggio")
         prompt = QadMsg.translate("Command_PLINE", "Specificare punto finale dell'arco o [{0}]: ").format(keyWords)
                    
         # si appresta ad attendere un punto o una parola chiave         
         # msg, inputType, default, keyWords, isNullable
         self.waitFor(prompt, \
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
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_PLINE", "Centro"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_CENTER_PT)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.translate("Command_PLINE", "Specificare centro dell'arco: "))
               self.step = 104
            elif value == QadMsg.translate("Command_PLINE", "Raggio"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_KNOWN_ASK_FOR_RADIUS)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, valori positivi
               self.waitFor(QadMsg.translate("Command_PLINE", "Specificare raggio dell'arco: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
               self.step = 105
         elif type(value) == QgsPoint: # é stato inserito il punto finale dell'arco
            arc = QadArc()         
            if arc.fromStartEndPtsAngle(self.arcStartPt, value, self.arcAngle) == True:
               points = arc.asPolyline()
               if points is not None:
                  # se i punti sono così vicini da essere considerati uguali
                  if qad_utils.ptNear(self.arcStartPt, arc.getStartPt()):
                     self.addArcVertices(points, False) # aggiungo i punti in ordine
                  else:
                     self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                  self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
                      
                  self.WaitForArcMenu()
                  return False
               
            keyWords = QadMsg.translate("Command_PLINE", "Centro") + "/" + \
                       QadMsg.translate("Command_PLINE", "Raggio")
            prompt = QadMsg.translate("Command_PLINE", "Specificare punto finale dell'arco o [{0}]: ").format(keyWords)
            # si appresta ad attendere un punto o una parola chiave         
            # msg, inputType, default, keyWords, isNullable
            self.waitFor(prompt, \
                         QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                         None, \
                         keyWords, QadInputModeEnum.NOT_NULL)
            
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA CENTRO DELL'ARCO (da step = 103)
      elif self.step == 104: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt()):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
               self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
                  
               self.WaitForArcMenu()
               return False      

         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.translate("Command_PLINE", "Specificare centro dell'arco: "))
                 
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA RAGGIO (da step = 103)
      elif self.step == 105: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
            self.waitForPoint(QadMsg.translate("Command_PLINE", "Specificare secondo punto: "))
            self.step = 106
         else:
            self.arcRadius = value
            self.plugIn.setLastRadius(self.arcRadius)

            # imposto il map tool
            self.getPointMapTool().arcRadius = self.arcRadius
            self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_RADIUS_KNOWN_ASK_FOR_CHORDDIRECTION)
            # si appresta ad attendere un punto o un numero reale         
            # msg, inputType, default, keyWords, isNullable
            msg = QadMsg.translate("Command_PLINE", "Specificare direzione della corda per l'arco <{0}>: ")
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
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
         msg = QadMsg.translate("Command_PLINE", "Specificare direzione della corda per l'arco <{0}>: ")
         self.waitFor(msg.format(str(self.getLastSegmentAng())), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                      None, "", QadInputModeEnum.NOT_NULL)
         self.step = 107


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DIREZIONE DELLA CORDA DELL'ARCO (da step = 106 e 107)
      elif self.step == 107: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt()):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
               self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
                  
               self.WaitForArcMenu()
               return False      

         # imposto il map tool
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_RADIUS_KNOWN_ASK_FOR_CHORDDIRECTION)
         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, isNullable
         msg = QadMsg.translate("Command_PLINE", "Specificare direzione della corda per l'arco <{0}>: ")
         self.waitFor(msg.format(str(self.getLastSegmentAng())), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                      None, "", QadInputModeEnum.NOT_NULL)
                 
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA CENTRO DELL'ARCO (da step = 101)
      elif self.step == 108: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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

         keyWords = QadMsg.translate("Command_PLINE", "Angolo") + "/" + \
                    QadMsg.translate("Command_PLINE", "Lunghezza corda")
         prompt = QadMsg.translate("Command_PLINE", "Specificare punto finale dell'arco o [{0}]: ").format(keyWords)
         # si appresta ad attendere un punto o una parola chiave         
         # msg, inputType, default, keyWords, isNullable
         self.waitFor(prompt, \
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
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:  
            if value == QadMsg.translate("Command_PLINE", "Angolo"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_ANGLE)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, valori <> 0
               self.waitFor(QadMsg.translate("Command_PLINE", "Specificare angolo inscritto: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO)
               self.step = 110
               return False                              
            elif value == QadMsg.translate("Command_PLINE", "Lunghezza"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_CHORD)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, valori positivi
               self.waitFor(QadMsg.translate("Command_PLINE", "Specificare lunghezza della corda: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
               self.step = 111
               return False                              
         elif type(value) == QgsPoint: # se é stato inserito il punto finale dell'arco
            self.arcEndPt = value
                     
            arc = QadArc()         
            if arc.fromStartCenterEndPts(self.arcStartPt, self.arcCenterPt, self.arcEndPt) == True:
               points = arc.asPolyline()
               if points is not None:
                  # se i punti sono così vicini da essere considerati uguali
                  if qad_utils.ptNear(self.arcStartPt, arc.getStartPt()):
                     self.addArcVertices(points, False) # aggiungo i punti in ordine
                  else:
                     self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                  self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
                     
                  self.WaitForArcMenu()
                  return False      
            
         keyWords = QadMsg.translate("Command_PLINE", "Angolo") + "/" + \
                    QadMsg.translate("Command_PLINE", "Lunghezza corda")
         prompt = QadMsg.translate("Command_PLINE", "Specificare punto finale dell'arco o [{0}]: ").format(keyWords)
         # si appresta ad attendere un punto o una parola chiave         
         # msg, inputType, default, keyWords, isNullable
         self.waitFor(prompt, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NOT_NULL)
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare angolo inscritto: " (da step = 109)
      elif self.step == 110: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt()):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
               self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
                  
               self.WaitForArcMenu()
               return False      

         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, isNullable
         self.waitFor(QadMsg.translate("Command_PLINE", "Specificare angolo inscritto: "), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                      None, "", \
                      QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO)

         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare lunghezza della corda: " (da step = 109)
      elif self.step == 111: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt()):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
               self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
                  
               self.WaitForArcMenu()
               return False      

         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, valori positivi
         self.waitFor(QadMsg.translate("Command_PLINE", "Specificare lunghezza della corda: "), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                      None, "", \
                      QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)

         return False

     
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare direzione tangente per il punto iniziale dell'arco: " (da step = 101)
      elif self.step == 112: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
         self.waitForPoint(QadMsg.translate("Command_PLINE", "Specificare punto finale dell'arco: "))
         self.step = 113
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO FINALE DELL'ARCO (da step = 112)
      elif self.step == 113: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt()):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
               self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
                  
               self.WaitForArcMenu()
               return False      

         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.translate("Command_PLINE", "Specificare punto finale dell'arco: "))
                 
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA RAGGIO (da step = 101)
      elif self.step == 114: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
            self.waitForPoint(QadMsg.translate("Command_PLINE", "Specificare secondo punto: "))
            self.step = 115
         else:
            self.arcRadius = value
            self.plugIn.setLastRadius(self.arcRadius)

            # imposto il map tool
            self.getPointMapTool().arcRadius = self.arcRadius
            self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_RADIUS_KNOWN_ASK_FOR_END_PT)
            # si appresta ad attendere un punto o un numero reale         
            # msg, inputType, default, keyWords, isNullable
            self.waitFor(QadMsg.translate("Command_PLINE", "Specificare punto finale dell'arco o [Angolo]: "), \
                         QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                         None, QadMsg.translate("Command_PLINE", "Angolo"), QadInputModeEnum.NOT_NULL)
            self.step = 116
            
         return False                                          


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO DEL RAGGIO (da step = 114)
      elif self.step == 115: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
         self.waitFor(QadMsg.translate("Command_PLINE", "Specificare punto finale dell'arco o [Angolo]: "), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, QadMsg.translate("Command_PLINE", "Angolo"), QadInputModeEnum.NOT_NULL)
         self.step = 116
      
         return False
      
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare punto finale dell'arco o [Angolo]: " (da step = 114 o 115)
      elif self.step == 116: # dopo aver atteso un punto o una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
         
         if type(value) == unicode:
            if value == QadMsg.translate("Command_PLINE", "Angolo"):
               
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_ANGLE)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, isNullable
               self.waitFor(QadMsg.translate("Command_PLINE", "Specificare angolo inscritto: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO)
               self.step = 117
         elif type(value) == QgsPoint: # é stato inserito il punto finale dell'arco
            arc = QadArc()         
            if arc.fromStartEndPtsRadius(self.arcStartPt, value, self.arcRadius) == True:
               points = arc.asPolyline()
               if points is not None:
                  # se i punti sono così vicini da essere considerati uguali
                  if qad_utils.ptNear(self.arcStartPt, arc.getStartPt()):
                     self.addArcVertices(points, False) # aggiungo i punti in ordine
                  else:
                     self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
                  self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
                     
            self.WaitForArcMenu()
                       
         return False                              
      

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare angolo inscritto: " (da step = 116)
      elif self.step == 117: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
         msg = QadMsg.translate("Command_PLINE", "Specificare direzione della corda per l'arco <{0}>: ")
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
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt()):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
               self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
               
               self.WaitForArcMenu()
               return False      

         # imposto il map tool
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_ANGLE_RADIUS_KNOWN_ASK_FOR_CHORDDIRECTION)
         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, isNullable
         msg = QadMsg.translate("Command_PLINE", "Specificare direzione della corda per l'arco <{0}>: ")
         self.waitFor(msg.format(str(self.getLastSegmentAng())), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                      None, "", QadInputModeEnum.NOT_NULL)
                 
         return False
      
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO (da step = 101)
      elif self.step == 119: # dopo aver atteso un punto o una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
         self.waitForPoint(QadMsg.translate("Command_PLINE", "Specificare punto finale dell'arco: "))
         self.step = 120
                  
         return False
      
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO FINALE DELL'ARCO (da step = 119)
      elif self.step == 120: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
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
               if qad_utils.ptNear(self.arcStartPt, arc.getStartPt()):
                  self.addArcVertices(points, False) # aggiungo i punti in ordine
               else:
                  self.addArcVertices(points, True) # aggiungo i punti in ordine inverso 
               self.getPointMapTool().setTmpGeometry(QgsGeometry.fromPolyline(self.vertices)) # per lo snap aggiungo questa geometria temporanea
                  
               self.WaitForArcMenu()
               return False      
      
         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.translate("Command_PLINE", "Specificare punto finale dell'arco: "))     
         return False      