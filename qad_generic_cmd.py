# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe base per un comando
 
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


# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *


from qad_msg import QadMsg
from qad_textwindow import *
from qad_getpoint import *


# Classe che gestisce un comando generico
class QadCommandClass():
   def showMsg(self, msg, displayPromptAfterMsg = False):
      if self.plugIn is not None:
         self.plugIn.showMsg(msg, displayPromptAfterMsg)
         
   def showErr(self, err):
      if self.plugIn is not None:
         self.plugIn.showErr(err)

   def showInputMsg(self, inputMsg, inputType, default = None, keyWords = "", \
                    inputMode = QadInputModeEnum.NONE):
      if self.plugIn is not None:
         self.plugIn.showInputMsg(inputMsg, inputType, default, keyWords, inputMode)

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = QadGetPoint(self.plugIn, drawMode) # per selezione di un punto
         return self.PointMapTool
      else:
         return None

   def hidePointMapToolMarkers(self):
      if self.PointMapTool is not None:
         self.PointMapTool.hidePointMapToolMarkers()

   def setMapTool(self, mapTool):
      if self.plugIn is not None:
         # setto il maptool per l'input via finestra grafica
         self.plugIn.canvas.setMapTool(mapTool)
         self.plugIn.mainAction.setChecked(True)     

   def waitForPoint(self, msg = QadMsg.translate("QAD", "Specify point: "), \
                    default = None, inputMode = QadInputModeEnum.NONE):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.POINT2D, default, "", inputMode)

   def waitForString(self, msg, default = None, inputMode = QadInputModeEnum.NONE):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.STRING, default, "", inputMode)

   def waitForInt(self, msg, default = None, inputMode = QadInputModeEnum.NOT_NULL):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.INT, default, "", inputMode)

   def waitForLong(self, msg, default = None, inputMode = QadInputModeEnum.NONE):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.LONG, default, "", inputMode)

   def waitForFloat(self, msg, default = None, inputMode = QadInputModeEnum.NONE):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.FLOAT, default, "", inputMode)

   def waitForBool(self, msg, default = None, inputMode = QadInputModeEnum.NONE):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.BOOL, default, "", inputMode)

   def waitForSelSet(self, msg = QadMsg.translate("QAD", "Select objects: ")):
      self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_RECTANGLE)
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.POINT2D)

   def waitFor(self, msg, inputType, default = None, keyWords = "", \
               inputMode = QadInputModeEnum.NONE):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, inputType, default, keyWords, inputMode)

   def getCurrMsgFromTxtWindow(self):
      if self.plugIn is not None:
         return self.plugIn.getCurrMsgFromTxtWindow()
      else:
         return None
         
   def showEvaluateMsg(self, msg = None):
      if self.plugIn is not None:
         self.plugIn.showEvaluateMsg(msg)

   def runCommandAbortingTheCurrent(self):
      self.plugIn.runCommandAbortingTheCurrent(self.getName())
      
   def getToolTipText(self):
      text = self.getName()
      if self.getNote() > 0:
         text = text + "\n\n" + self.getNote()
      return text
      
   #============================================================================
   # funzioni da sovrascrivere con le classi ereditate da questa
   #============================================================================
   def getName(self):
      """ impostare il nome del comando in maiuscolo """
      return ""

   def getEnglishName(self):
      """ impostare il nome del comando in inglese maiuscolo """
      return ""

   def connectQAction(self, action):
      pass     
      #QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runPLINECommand)

   def getIcon(self):
      # impostare l'icona  del comando (es. QIcon(":/plugins/qad/icons/pline.png"))
      # ricordarsi di inserire l'icona in resources.qrc e di ricompilare le risorse
      return None

   def getNote(self):
      """ impostare le note esplicative del comando """
      return ""
   
   def __init__(self, plugIn):
      self.plugIn = plugIn
      self.PointMapTool = None
      self.step         = 0      
      self.isValidPreviousInput = True
      
      # inizializzare tutti i maptool necessari al comando
      # esempio di struttura di un comando che richiede
      # 1) un punto
      # self.mapTool = QadGetPoint(self.plugIn) # per selezione di un punto
         
   def __del__(self):
      """ distruttore """
      self.hidePointMapToolMarkers()
      if self.PointMapTool:
         self.PointMapTool.removeItems()
         del self.PointMapTool
         self.PointMapTool = None

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return None
   
   def run(self, msgMapTool = False, msg = None):
      """
      Esegue il comando. 
      - msgMapTool; se True significa che arriva un valore da MapTool del comando
                    se false significa che il valore é nel parametro msg
      - msg;        valore in input al comando (usato quando msgMapTool = False)
      
      ritorna True se il comando é terminato altrimenti False
      """
      # esempio di struttura di un comando che richiede
      # 1) un punto
      if self.step == 0: # inizio del comando
         self.waitForPoint() # si appresta ad attendere un punto
         self.step = self.step + 1
         return False
      elif self.step == 1: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               self.setMapTool(self.getPointMapTool()) # riattivo il maptool
               return False

            pt = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            pt = msg
            
         return True

   def mapToLayerCoordinates(self, layer, point_geom):
      # transform point o geometry coordinates from output CRS to layer's CRS 
      if self.plugIn is None:
         return None
      if type(point_geom) == QgsPoint:
         return self.plugIn.canvas.mapSettings().mapToLayerCoordinates(layer, point_geom)
      elif type(point_geom) == QgsGeometry:
         # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
         coordTransform = QgsCoordinateTransform(self.plugIn.canvas.mapSettings().destinationCrs(), layer.crs())
         g = QgsGeometry(point_geom)
         g.transform(coordTransform)
         return g
      elif (type(point_geom) == list or type(point_geom) == tuple): # lista di punti o di geometrie
         coordTransform = QgsCoordinateTransform(self.plugIn.canvas.mapSettings().destinationCrs(), layer.crs())
         res = []
         for pt in point_geom:
            if type(pt) == QgsPoint:
               res.append(coordTransform.transform(pt))
            elif type(point_geom) == QgsGeometry:
               g = QgsGeometry(point_geom)
               g.transform(coordTransform)
               res.append(g)
         return res
      else:
         return None

   def layerToMapCoordinates(self, layer, point_geom):
      # transform point o geometry coordinates from layer's CRS to output CRS 
      if self.plugIn is None:
         return None
      if type(point_geom) == QgsPoint:
         return self.plugIn.canvas.mapSettings().layerToMapCoordinates(layer, point_geom)
      elif type(point_geom) == QgsGeometry:
         # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
         coordTransform = QgsCoordinateTransform(layer.crs(), self.plugIn.canvas.mapSettings().destinationCrs())
         g = QgsGeometry(point_geom)
         g.transform(coordTransform)
         return g
      elif (type(point_geom) == list or type(point_geom) == tuple): # lista di punti o di geometrie
         coordTransform = QgsCoordinateTransform(self.plugIn.canvas.mapSettings().destinationCrs(), layer.crs())
         res = []
         for pt in point_geom:
            if type(pt) == QgsPoint:
               res.append(coordTransform.transform(pt))
            elif type(point_geom) == QgsGeometry:
               g = QgsGeometry(point_geom)
               g.transform(coordTransform)
               res.append(g)
         return res
      else:
         return None
