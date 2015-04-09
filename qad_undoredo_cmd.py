# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando UNDO e REDO di QAD
 
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


from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_textwindow import *


# Classe che gestisce il comando UNDO
class QadUNDOCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadUNDOCommandClass(self.plugIn)

   def getName(self):
      return QadMsg.translate("Command_list", "ANNULLA")

   def getEnglishName(self):
      return "UNDO"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runUNDOCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/undo.png")
   
   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_UNDO", "Annulla le ultime operazioni eseguite.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
         
   def run(self, msgMapTool = False, msg = None):
      self.isValidPreviousInput = True # per gestire il comando anche in macro

      if self.step == 0: # inizio del comando
         keyWords = QadMsg.translate("Command_UNDO", "INIzio") + "/" + \
                    QadMsg.translate("Command_UNDO", "Fine") + "/" + \
                    QadMsg.translate("Command_UNDO", "Segno") + "/" + \
                    QadMsg.translate("Command_UNDO", "INDietro")
         default = 1
         prompt = QadMsg.translate("Command_UNDO", "Digitare il numero di operazioni da annullare o [{0}] <{1}>: ").format(keyWords, str(default))
         
         englishKeyWords = "BEgin" + "/" + "End" + "/" + "Mark" + "/" + "Back"
         keyWords += "_" + englishKeyWords
         # si appresta ad attendere un numero intero positivo o enter o una parola chiave         
         # msg, inputType, default, keyWords, valori positivi
         self.waitFor(prompt, \
                      QadInputTypeEnum.INT | QadInputTypeEnum.KEYWORDS, \
                      default, \
                      keyWords, QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)      
         self.step = 1
         return False
   
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA NUMERO INTERO (da step = 0)
      elif self.step == 1: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  self.plugIn.undoEditCommand()
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_UNDO", "INIzio") or value == "BEgin":
               self.plugIn.insertBeginGroup()
            elif value == QadMsg.translate("Command_UNDO", "Fine") or value == "End":
               if self.plugIn.insertEndGroup() == False:
                  self.showMsg(QadMsg.translate("Command_UNDO", "\nNessun gruppo é rimasto aperto."))                  
            elif value == QadMsg.translate("Command_UNDO", "Segno") or value == "Mark":
               if self.plugIn.insertBookmark() == False:
                  self.showMsg(QadMsg.translate("Command_UNDO", "\nNon é possibile inserire un segno dentro un gruppo."))                  
            elif value == QadMsg.translate("Command_UNDO", "INDietro") or value == "Back":
               if self.plugIn.getPrevBookmarkPos() == -1: # non ci sono bookmark precedenti
                  keyWords = QadMsg.translate("QAD", "Sì") + "/" + \
                             QadMsg.translate("QAD", "No")                                                 
                  default = QadMsg.translate("QAD", "Sì")
                  prompt = QadMsg.translate("Command_UNDO", "Questa operazione annullerà tutto. OK ? <{0}>: ").format(default)
                  
                  englishKeyWords = "Yes" + "/" + "No"
                  keyWords += "_" + englishKeyWords
                  # si appresta ad attendere enter o una parola chiave         
                  # msg, inputType, default, keyWords, nessun controllo
                  self.waitFor(prompt, \
                               QadInputTypeEnum.KEYWORDS, \
                               default, \
                               keyWords, QadInputModeEnum.NONE)
                  self.step = 2
                  return False                                       
               else:
                  self.plugIn.undoUntilBookmark()
         elif type(value) == int:
            self.plugIn.undoEditCommand(value)

         return True
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI ANNULLARE TUTTO (da step = 1)
      elif self.step == 2: # dopo aver atteso una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  self.plugIn.undoUntilBookmark()
                  self.showMsg(QadMsg.translate("Command_UNDO", "é stato annullato tutto."))
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("QAD", "Sì") or value == "Yes":
               self.showMsg(QadMsg.translate("Command_UNDO", "é stato annullato tutto."))
               self.plugIn.undoUntilBookmark()

         return True # fine comando

   
# Classe che gestisce il comando REDO
class QadREDOCommandClass(QadCommandClass):
   
   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadREDOCommandClass(self.plugIn)

   def getName(self):
      return QadMsg.translate("Command_list", "RIPRISTINA")

   def getEnglishName(self):
      return "REDO"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runREDOCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/redo.png")
   
   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_UNDO", "Ripristina le ultime operazioni eseguite.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
         
   def run(self, msgMapTool = False, msg = None):
      self.plugIn.redoEditCommand()
      return True   