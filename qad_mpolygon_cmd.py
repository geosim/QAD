# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando MPOLYGON per disegnare un poligono
 
                              -------------------
        begin                : 2013-09-18
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


from qad_generic_cmd import QadCommandClass
from qad_pline_cmd import QadPLINECommandClass
from qad_msg import QadMsg
from qad_textwindow import *
from qad_getpoint import *
import qad_utils
import qad_layer


# Classe che gestisce il comando MPOLYGON
class QadMPOLYGONCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadMPOLYGONCommandClass(self.plugIn)
   
   def getName(self):
      return QadMsg.translate("Command_list", "MPOLYGON")

   def getEnglishName(self):
      return "MPOLYGON"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runMPOLYGONCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/mpolygon.png")

   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_MPOLYGON", "Draws a polygon by many methods.\nA Polygon is a closed sequence of straight line segments,\narcs or a combination of two.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.vertices = []
      # se questo flag = True il comando serve all'interno di un altro comando per disegnare un poligono
      # che non verrà salvato su un layer
      self.virtualCmd = False
      self.rubberBandBorderColor = None
      self.rubberBandFillColor = None
      self.PLINECommand = None

   def __del__(self):
      QadCommandClass.__del__(self)
      if self.PLINECommand is not None:
         del self.PLINECommand

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.PLINECommand is not None:
         return self.PLINECommand.getPointMapTool(drawMode)
      else:
         return QadCommandClass.getPointMapTool(self, drawMode)


   def setRubberBandColor(self, rubberBandBorderColor, rubberBandFillColor):
      self.rubberBandBorderColor = rubberBandBorderColor
      self.rubberBandFillColor = rubberBandFillColor
      if self.PLINECommand is not None:
         self.PLINECommand.setRubberBandColor(rubberBandBorderColor, rubberBandFillColor)


   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapSettings().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
         return True # fine comando

      if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
         currLayer, errMsg = qad_layer.getCurrLayerEditable(self.plugIn.canvas, QGis.Polygon)
         if currLayer is None:
            self.showErr(errMsg)
            return True # fine comando

      #=========================================================================
      # RICHIESTA PRIMO PUNTO PER SELEZIONE OGGETTI
      if self.step == 0:
         self.PLINECommand = QadPLINECommandClass(self.plugIn, True)
         self.PLINECommand.setRubberBandColor(self.rubberBandBorderColor, self.rubberBandFillColor)
         # se questo flag = True il comando serve all'interno di un altro comando per disegnare una linea
         # che non verrà salvata su un layer
         self.PLINECommand.virtualCmd = True   
         self.PLINECommand.asToolForMPolygon = True # per rubberband tipo poligono
         self.PLINECommand.run(msgMapTool, msg)
         self.step = 1
         return False # continua     

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO (da step = 0 o 1)
      elif self.step == 1: # dopo aver atteso un punto si riavvia il comando
         if self.PLINECommand.run(msgMapTool, msg) == True:
            verticesLen = len(self.PLINECommand.vertices)
            if verticesLen >= 3:
               self.vertices = self.PLINECommand.vertices[:] # copio la lista
               firstVertex = self.vertices[0]
               # se l'ultimo vertice non é uguale al primo
               if self.vertices[verticesLen - 1] != firstVertex:
                  # aggiungo un vertice con le stesse coordinate del primo
                  self.vertices.append(firstVertex)
               if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
                  if qad_layer.addPolygonToLayer(self.plugIn, currLayer, self.vertices) == False:                     
                     self.showMsg(QadMsg.translate("Command_MPOLYGON", "\nPolygon not valid.\n"))
                     del self.vertices[:] # svuoto la lista
            else:
               self.showMsg(QadMsg.translate("Command_MPOLYGON", "\nPolygon not valid.\n"))
                               
            del self.PLINECommand
            self.PLINECommand = None
         
            return True # fine
            
         return False
