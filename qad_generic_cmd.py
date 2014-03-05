# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe base per un comando
 
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
from qad_msg import QadMsg
from qad_textwindow import *
from qad_getpoint import *


# Classe che gestisce un comando generico
class QadCommandClass():
   plugIn               = None
   PointMapTool         = None
   step                 = 0
   isValidPreviousInput = True

   def showMsg(self, msg, displayPrompt = False):
      if self.plugIn is not None:
         self.plugIn.showMsg(msg, displayPrompt)
         
   def showErr(self, err):
      if self.plugIn is not None:
         self.plugIn.showErr(err)

   def showInputMsg(self, inputMsg, inputType, default = None, keyWords = "", \
                    inputMode = QadInputModeEnum.NOT_NULL):
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

   def waitForPoint(self, msg = QadMsg.translate("QAD", "Specificare punto: "), \
                    default = None, inputMode = QadInputModeEnum.NOT_NULL):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.POINT2D, default, "", inputMode)

   def waitForString(self, msg, default = None, inputMode = QadInputModeEnum.NOT_NULL):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.STRING, default, "", inputMode)

   def waitForInt(self, msg, default = None, inputMode = QadInputModeEnum.NOT_NULL):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.INT, default, "", inputMode)

   def waitForlong(self, msg, default = None, inputMode = QadInputModeEnum.NOT_NULL):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.LONG, default, "", inputMode)

   def waitForFloat(self, msg, default = None, inputMode = QadInputModeEnum.NOT_NULL):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.FLOAT, default, "", inputMode)

   def waitForBool(self, msg, default = None, inputMode = QadInputModeEnum.NOT_NULL):
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.BOOL, default, "", inputMode)

   def waitForSelSet(self, msg = QadMsg.translate("QAD", "Selezionare oggetti: ")):
      self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_RECTANGLE)
      self.setMapTool(self.getPointMapTool())
      # setto l'input via finestra di testo
      self.showInputMsg(msg, QadInputTypeEnum.POINT2D)

   def waitFor(self, msg, inputType, default = None, keyWords = "", \
               inputMode = QadInputModeEnum.NOT_NULL):
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
      
      
   #============================================================================
   # funzioni da sovrascrivere con le classi ereditate da questa
   #============================================================================
   def getName(self):
      # impostare il nome del comando in maiuscolo
      return ""

   def connectQAction(self, action):
      pass     
      #QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runPLINECommand)

   def getIcon(self):
      # impostare l'icona  del comando (es. QIcon(":/plugins/qad/icons/pline.png"))
      # ricordarsi di inserire l'icona in resources.qrc e di ricompilare le risorse
      return None

   def getNote(self):
      # impostare le note esplicative del comando
      return ""
   
   def __init__(self, plugIn):
      self.plugIn = plugIn
      self.PointMapTool = None
      self.step         = 0
      
      # inizializzare tutti i maptool necessari al comando
      # esempio di struttura di un comando che richiede
      # 1) un punto
      # self.mapTool = QadGetPoint(self.plugIn) # per selezione di un punto
         
   def __del__(self):
      # distruttore
      self.hidePointMapToolMarkers()
   
   def run(self, msgMapTool = False, msg = None):
      """
      Esegue il comando. 
      - msgMapTool; se True significa che arriva un valore da MapTool del comando
                    se false significa che il valore è nel parametro msg
      - msg;        valore in input al comando (usato quando msgMapTool = False)
      
      ritorna True se il comando è terminato altrimenti False
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
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               self.setMapTool(self.getPointMapTool()) # riattivo il maptool
               return False

            pt = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            pt = msg
            
         return True

   def mapToLayerCoordinates(self, layer, point):
      # transform point coordinates from output CRS to layer's CRS 
      if self.plugIn is None:
         return None
      return self.plugIn.canvas.mapRenderer().mapToLayerCoordinates(layer, point)
