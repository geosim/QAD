# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando SETVAR per settare le variabili di ambiente di QAD
 
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
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_variables import *


# Classe che gestisce il comando SETVAR
class QadSETVARCommandClass(QadCommandClass):

   varName = ""
   
   def getName(self):
      return QadMsg.translate("Command_list", "MODIVAR")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runSETVARCommand)
   
   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_SETVAR", "Imposta le variabili di ambiente di QAD.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
         
   def run(self, msgMapTool = False, msg = None):
      if self.step == 0: # inizio del comando
         # si appresta ad attendere una stringa
         self.waitForString(QadMsg.translate("Command_SETVAR", "Digitare nome della variabile o [?]: "), \
                            QadMsg.translate("Command_SETVAR", "?"))
         self.step = 1
         return False
      elif self.step == 1: # dopo aver atteso il nome della variabile si riavvia il comando
         if msgMapTool == True: # niente può arrivare da grafica
            return False
         #  il nome della variabile arriva come parametro della funzione
         self.varName = msg
         if self.varName == QadMsg.translate("Command_SETVAR", "?"): # lista delle variabili            
            # si appresta ad attendere una stringa            
            self.waitForString(QadMsg.translate("Command_SETVAR", "Digitare variabile/i da elencare <*>: "), \
                               QadMsg.translate("Command_SETVAR", "*"))
            self.step = 3
            return False
         else:
            varValue = QadVariables.get(self.varName)
            if varValue is None:
               
               msg = QadMsg.translate("Command_SETVAR", "\nNome della variabile sconosciuto. Digitare {0} ? per un elenco delle variabili.")
               self.showErr(msg.format(QadMsg.translate("Command_list", "MODIVAR")))
               return False
            else:
               msg = QadMsg.translate("Command_SETVAR", "Digitare nuovo valore per {0} <{1}>: ")
               vartype = str(type(varValue))
               if vartype == "<type 'str'>":
                  # si appresta ad attendere una stringa
                  self.waitForString(msg.format(self.varName, varValue), varValue)
               elif vartype == "<type 'int'>":
                  # si appresta ad attendere un numero intero
                  self.waitForInt(msg.format(self.varName, varValue), varValue)
               elif vartype == "<type 'float'>":
                  # si appresta ad attendere un numero reale
                  self.waitForFloat(msg.format(self.varName, varValue), varValue)
               elif vartype == "<type 'bool'>":
                  # si appresta ad attendere un numero reale
                  self.waitForBool(msg.format(self.varName, varValue), varValue)
               self.step = 2
               return False
      elif self.step == 2: # dopo aver atteso il valore della variabile si riavvia il comando
         if msgMapTool == True: # niente può arrivare da grafica
            return False
         # il valore della variabile arriva come parametro della funzione
         QadVariables.set(self.varName, msg)
         QadVariables.save()
         return True
      elif self.step == 3: # dopo aver atteso il nome della variabile si riavvia il comando
         if msgMapTool == True: # niente può arrivare da grafica
            return False

         if msg == "*":
            varNames = QadVariables.getVarNames()
         else:
            #  il nome della variabile arriva come parametro della funzione
            varNames = msg.strip().split(",")
            
         varNames.sort()
         for self.varName in varNames:
            self.varName = self.varName.strip()
            varValue = QadVariables.get(self.varName)
            if varValue is not None:
               msg = "\n" + self.varName + "=" + str(varValue)
               self.showMsg(msg)
         return True