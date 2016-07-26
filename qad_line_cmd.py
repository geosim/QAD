# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando PLINE per disegnare una linea
 
                              -------------------
        begin                : 2013-07-15
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


from qad_getpoint import *
from qad_line_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_textwindow import *
from qad_snapper import *
import qad_utils
import qad_layer
from qad_rubberband import createRubberBand


# Classe che gestisce il comando LINE
class QadLINECommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadLINECommandClass(self.plugIn)
   
   def getName(self):
      return QadMsg.translate("Command_list", "LINE")

   def getEnglishName(self):
      return "LINE"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runLINECommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/line.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_LINE", "Creates straight line segments.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.vertices = []
      self.rubberBand = createRubberBand(self.plugIn.canvas, QGis.Line)
      self.firstPtTan = None
      self.firstPtPer = None      
      # se questo flag = True il comando serve all'interno di un altro comando per disegnare una linea
      # che non verrà salvata su un layer
      self.virtualCmd = False

   def __del__(self):
      QadCommandClass.__del__(self)
      self.rubberBand.hide()
      self.plugIn.canvas.scene().removeItem(self.rubberBand)

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_line_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None       

   def addVertex(self, point):
      self.vertices.append(point)     
      self.addPointToRubberBand(point)            
      self.plugIn.setLastPointAndSegmentAng(self.vertices[-1])            
      self.setTmpGeometriesToMapTool()
      
   def delLastVertex(self):
      if len(self.vertices) > 0:
         del self.vertices[-1] # cancello ultimo vertice
         self.removeLastPointToRubberBand()
         if len(self.vertices) > 0:
            self.plugIn.setLastPointAndSegmentAng(self.vertices[-1])
         self.setTmpGeometriesToMapTool()      
         

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

   def addLinesToLayer(self, layer):
      i = 1
      while i < len(self.vertices):                     
         qad_layer.addLineToLayer(self.plugIn, layer,
                                  [self.vertices[i - 1], self.vertices[i]])
         i = i + 1


   #============================================================================
   # setTmpGeometriesToMapTool
   #============================================================================
   def setTmpGeometriesToMapTool(self):
      self.getPointMapTool().clearTmpGeometries()
      i = 1
      while i < len(self.vertices):                     
         # per lo snap aggiungo questa geometria temporanea
         self.getPointMapTool().appendTmpGeometry(QgsGeometry.fromPolyline([self.vertices[i - 1], self.vertices[i]]))
         i = i + 1

            
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapSettings().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
         return True # fine comando

      if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
         currLayer, errMsg = qad_layer.getCurrLayerEditable(self.plugIn.canvas, QGis.Line)
         if currLayer is None:
            self.showErr(errMsg)
            return True # fine comando
      
      # RICHIESTA PRIMO PUNTO 
      if self.step == 0: # inizio del comando
         # imposto il map tool
         self.getPointMapTool().setMode(Qad_line_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT)
         # si appresta ad attendere un punto o enter
         #                        msg, inputType,              default, keyWords, nessun controllo         
         self.waitFor(QadMsg.translate("Command_LINE", "Specify first point: "), \
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
                  if self.virtualCmd == False: # se si vuole veramente salvare in un layer   
                     self.addLinesToLayer(currLayer)
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            snapTypeOnSel = self.getPointMapTool().snapTypeOnSelection
            value = self.getPointMapTool().point
            entity = self.getPointMapTool().entity
         else: # il punto arriva come parametro della funzione
            value = msg
            snapTypeOnSel = QadSnapTypeEnum.NONE

         if type(value) == unicode:
            if value == QadMsg.translate("Command_LINE", "Undo") or value == "Undo":               
               self.delLastVertex() # cancello ultimo vertice
               # imposto il map tool
               if len(self.vertices) == 0:
                  self.getPointMapTool().setMode(Qad_line_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT)
                  # si appresta ad attendere un punto o enter
                  #                        msg, inputType,              default, keyWords, nessun controllo
                  self.waitFor(QadMsg.translate("Command_LINE", "Specify first point: "), \
                               QadInputTypeEnum.POINT2D, None, "", QadInputModeEnum.NONE)
                  return False                  
               else:
                  self.getPointMapTool().firstPt = self.vertices[-1]
                  self.getPointMapTool().setMode(Qad_line_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)        
            elif value == QadMsg.translate("Command_LINE", "Close") or value == "Close":
               newPt = self.vertices[0]
               self.addVertex(newPt) # aggiungo un nuovo vertice
               if self.virtualCmd == False: # se si vuole veramente salvare in un layer   
                  self.addLinesToLayer(currLayer)
               return True # fine comando
         else:
            if len(self.vertices) == 0: # primo punto
               if value is None:
                  if self.plugIn.lastPoint is not None:
                     value = self.plugIn.lastPoint
                  else:
                     return True # fine comando
   
               # se é stato selezionato un punto con la modalità TAN_DEF é un punto differito
               if snapTypeOnSel == QadSnapTypeEnum.TAN_DEF and entity.isInitialized():
                  # se era stato selezionato un punto esplicito
                  if (self.firstPtTan is None) and (self.firstPtPer is None):                     
                     self.firstPtPer = None
                     self.firstPtTan = value
                     self.firstGeom = QgsGeometry(entity.getGeometry()) # duplico la geometria         
                     coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapSettings().destinationCrs()) # trasformo la geometria
                     self.firstGeom.transform(coordTransform)
                     # imposto il map tool
                     self.getPointMapTool().tan1 = self.firstPtTan
                     self.getPointMapTool().geom1 = self.firstGeom
                     self.getPointMapTool().setMode(Qad_line_maptool_ModeEnum.FIRST_TAN_KNOWN_ASK_FOR_SECOND_PT)
                  # se era stato selezionato un punto con la modalità TAN_DEF   
                  elif self.firstPtTan is not None:
                     secondGeom = QgsGeometry(entity.getGeometry()) # duplico la geometria         
                     coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapSettings().destinationCrs()) # trasformo la geometria
                     secondGeom.transform(coordTransform)
                     tangent = qad_utils.lineFrom2TanPts(self.firstGeom, self.firstPtTan, secondGeom, value)
                     if tangent is not None:
                        # prendo il punto più vicino a value
                        if qad_utils.getDistance(tangent[0], value) < qad_utils.getDistance(tangent[1], value):                              
                           self.addVertex(tangent[1]) # aggiungo un nuovo vertice
                           self.addVertex(tangent[0]) # aggiungo un nuovo vertice
                           self.getPointMapTool().firstPt = tangent[0]
                        else:
                           self.addVertex(tangent[0]) # aggiungo un nuovo vertice
                           self.addVertex(tangent[1]) # aggiungo un nuovo vertice
                           self.getPointMapTool().firstPt = tangent[1]
                        # imposto il map tool
                        self.getPointMapTool().setMode(Qad_line_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)         
                     else:
                        self.showMsg(QadMsg.translate("Command_LINE", "\nNo tangent possible"))
                  # se era stato selezionato un punto con la modalità PER_DEF              
                  elif self.firstPtPer is not None:
                     secondGeom = QgsGeometry(entity.getGeometry()) # duplico la geometria         
                     coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapSettings().destinationCrs()) # trasformo la geometria
                     secondGeom.transform(coordTransform)
                     tangent = qad_utils.lineFromTanPerPts(secondGeom, value, self.firstGeom, self.firstPtPer)
                     if tangent is not None:
                        # prendo il punto più vicino a value
                        if qad_utils.getDistance(tangent[0], value) < qad_utils.getDistance(tangent[1], value):                              
                           self.addVertex(tangent[1]) # aggiungo un nuovo vertice
                           self.addVertex(tangent[0]) # aggiungo un nuovo vertice
                           self.getPointMapTool().firstPt = tangent[0]
                        else:
                           self.addVertex(tangent[0]) # aggiungo un nuovo vertice
                           self.addVertex(tangent[1]) # aggiungo un nuovo vertice
                           self.getPointMapTool().firstPt = tangent[1]
                        # imposto il map tool
                        self.getPointMapTool().setMode(Qad_line_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)         
                     else:
                        self.showMsg(QadMsg.translate("Command_LINE", "\nNo tangent possible"))                        
                        
               # se é stato selezionato un punto con la modalità PER_DEF é un punto differito
               elif snapTypeOnSel == QadSnapTypeEnum.PER_DEF and entity.isInitialized():
                  # se era stato selezionato un punto esplicito
                  if (self.firstPtTan is None) and (self.firstPtPer is None):
                     self.firstPtTan = None
                     self.firstPtPer = value
                     self.firstGeom = QgsGeometry(entity.getGeometry()) # duplico la geometria         
                     coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapSettings().destinationCrs()) # trasformo la geometria
                     self.firstGeom.transform(coordTransform)         
                     # imposto il map tool
                     self.getPointMapTool().per1 = self.firstPtPer
                     self.getPointMapTool().geom1 = self.firstGeom
                     self.getPointMapTool().setMode(Qad_line_maptool_ModeEnum.FIRST_PER_KNOWN_ASK_FOR_SECOND_PT)               
                  # se era stato selezionato un punto con la modalità TAN_DEF   
                  elif self.firstPtTan is not None:
                     secondGeom = QgsGeometry(entity.getGeometry()) # duplico la geometria         
                     coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapSettings().destinationCrs()) # trasformo la geometria
                     secondGeom.transform(coordTransform)
                     tangent = qad_utils.lineFromTanPerPts(self.firstGeom, self.firstPtTan, secondGeom, value)
                     if tangent is not None:
                        # prendo il punto più vicino a value
                        if qad_utils.getDistance(tangent[0], value) < qad_utils.getDistance(tangent[1], value):                              
                           self.addVertex(tangent[1]) # aggiungo un nuovo vertice
                           self.addVertex(tangent[0]) # aggiungo un nuovo vertice
                           self.getPointMapTool().firstPt = tangent[0]
                        else:
                           self.addVertex(tangent[0]) # aggiungo un nuovo vertice
                           self.addVertex(tangent[1]) # aggiungo un nuovo vertice
                           self.getPointMapTool().firstPt = tangent[1]
                        # imposto il map tool
                        self.getPointMapTool().setMode(Qad_line_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)         
                     else:
                        self.showMsg(QadMsg.translate("Command_LINE", "\nNo perpendicular possible"))
                  # se era stato selezionato un punto con la modalità PER_DEF              
                  elif self.firstPtPer is not None:
                     secondGeom = QgsGeometry(entity.getGeometry()) # duplico la geometria         
                     coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapSettings().destinationCrs()) # trasformo la geometria
                     secondGeom.transform(coordTransform)
                     line = qad_utils.lineFrom2PerPts(self.firstGeom, self.firstPtPer, secondGeom, value)
                     if line is not None:
                        # prendo il punto più vicino a value
                        if qad_utils.getDistance(line[0], value) < qad_utils.getDistance(line[1], value):                              
                           self.addVertex(line[1]) # aggiungo un nuovo vertice
                           self.addVertex(line[0]) # aggiungo un nuovo vertice
                           self.getPointMapTool().firstPt = line[0]
                        else:
                           self.addVertex(line[0]) # aggiungo un nuovo vertice
                           self.addVertex(line[1]) # aggiungo un nuovo vertice
                           self.getPointMapTool().firstPt = line[1]
                        # imposto il map tool
                        self.getPointMapTool().setMode(Qad_line_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)         
                     else:
                        self.showMsg(QadMsg.translate("Command_LINE", "\nNo perpendicular possible"))
               else: # altrimenti é un punto esplicito
                  # se era stato selezionato un punto con la modalità TAN_DEF
                  if self.firstPtTan is not None:
                     snapper = QadSnapper()
                     snapper.setSnapPointCRS(self.plugIn.canvas.mapSettings().destinationCrs())
                     snapper.setSnapType(QadSnapTypeEnum.TAN)
                     snapper.setStartPoint(value)
                     oSnapPoints = snapper.getSnapPoint(self.firstGeom, self.firstPtTan, 
                                                        self.plugIn.canvas.mapSettings().destinationCrs())
                     # memorizzo il punto di snap in point (prendo il primo valido)
                     for item in oSnapPoints.items():
                        points = item[1]
                        if points is not None:
                           self.addVertex(points[0]) # aggiungo un nuovo vertice
                           self.addVertex(value) # aggiungo un nuovo vertice
                           break

                     if len(self.vertices) == 0:
                        self.showMsg(QadMsg.translate("Command_LINE", "\nNo tangent possible"))                                          
                  # se era stato selezionato un punto con la modalità PER_DEF
                  elif self.firstPtPer is not None:
                     snapper = QadSnapper()
                     snapper.setSnapPointCRS(self.plugIn.canvas.mapSettings().destinationCrs())
                     snapper.setSnapType(QadSnapTypeEnum.PER)
                     snapper.setStartPoint(value)
                     oSnapPoints = snapper.getSnapPoint(self.firstGeom, self.firstPtPer, 
                                                        self.plugIn.canvas.mapSettings().destinationCrs())
                     # memorizzo il punto di snap in point (prendo il primo valido)
                     for item in oSnapPoints.items():
                        points = item[1]
                        if points is not None:
                           self.addVertex(points[0]) # aggiungo un nuovo vertice
                           self.addVertex(value) # aggiungo un nuovo vertice
                           break

                     if len(self.vertices) == 0:                        
                        self.showMsg(QadMsg.translate("Command_LINE", "\nNo perpendicular possible"))
                  else:
                     self.addVertex(value) # aggiungo un nuovo vertice

                  if len(self.vertices) > 0:                         
                     # imposto il map tool
                     self.getPointMapTool().firstPt = value
                     self.getPointMapTool().setMode(Qad_line_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)         
            else: # secondo punto
               if value is None:
                  if self.virtualCmd == False: # se si vuole veramente salvare in un layer   
                     self.addLinesToLayer(currLayer)
                  return True # fine comando
               # se il primo punto é esplicito
               if len(self.vertices) > 0 is not None:
                  self.addVertex(value) # aggiungo un nuovo vertice    
                  # imposto il map tool
                  self.getPointMapTool().firstPt = value
                  self.getPointMapTool().setMode(Qad_line_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)         

         if len(self.vertices) > 2:
            keyWords = QadMsg.translate("Command_LINE", "Close") + "/" + \
                       QadMsg.translate("Command_LINE", "Undo")
         else:
            keyWords = QadMsg.translate("Command_LINE", "Undo")
         prompt = QadMsg.translate("Command_LINE", "Specify next point or [{0}]: ").format(keyWords)
            
         englishKeyWords = "Close" + "/" + "Undo"
         keyWords += "_" + englishKeyWords
         # si appresta ad attendere un punto o enter o una parola chiave         
         # msg, inputType, default, keyWords, nessun controllo
         self.waitFor(prompt, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NONE)
         
         return False
      