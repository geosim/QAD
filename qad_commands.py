# -*- coding: utf-8 -*-

"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire i comandi
 
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
from qgis.gui import *

import sys, traceback

from qad_maptool import QadMapTool, QadVirtualSelCommandClass, QadVirtualGripCommandsClass
from qad_msg import QadMsg
from qad_cmd_aliases import *
from qad_variables import QadVariables

from qad_getpoint import *
from qad_generic_cmd import QadCommandClass
from qad_id_cmd import QadIDCommandClass
from qad_setcurrlayerbygraph_cmd import QadSETCURRLAYERBYGRAPHCommandClass, QadSETCURRUPDATEABLELAYERBYGRAPHCommandClass
from qad_setvar_cmd import QadSETVARCommandClass
from qad_pline_cmd import QadPLINECommandClass
from qad_arc_cmd import QadARCCommandClass
from qad_circle_cmd import QadCIRCLECommandClass
from qad_dsettings_cmd import QadDSETTINGSCommandClass
from qad_line_cmd import QadLINECommandClass
from qad_erase_cmd import QadERASECommandClass
from qad_mpolygon_cmd import QadMPOLYGONCommandClass
from qad_mbuffer_cmd import QadMBUFFERCommandClass
from qad_rotate_cmd import QadROTATECommandClass
from qad_move_cmd import QadMOVECommandClass
from qad_scale_cmd import QadSCALECommandClass
from qad_copy_cmd import QadCOPYCommandClass
from qad_offset_cmd import QadOFFSETCommandClass
from qad_extend_cmd import QadEXTENDCommandClass
from qad_trim_cmd import QadTRIMCommandClass
from qad_rectangle_cmd import QadRECTANGLECommandClass
from qad_mirror_cmd import QadMIRRORCommandClass
from qad_undoredo_cmd import QadUNDOCommandClass, QadREDOCommandClass
from qad_insert_cmd import QadINSERTCommandClass
from qad_text_cmd import QadTEXTCommandClass
from qad_stretch_cmd import QadSTRETCHCommandClass
from qad_break_cmd import QadBREAKCommandClass
from qad_pedit_cmd import QadPEDITCommandClass
from qad_fillet_cmd import QadFILLETCommandClass
from qad_polygon_cmd import QadPOLYGONCommandClass
from qad_dim_cmd import QadDIMLINEARCommandClass, QadDIMALIGNEDCommandClass, QadDIMARCCommandClass
from qad_dimstyle_cmd import QadDIMSTYLECommandClass
from qad_lengthen_cmd import QadLENGTHENCommandClass
from qad_help_cmd import QadHELPCommandClass
from qad_options_cmd import QadOPTIONSCommandClass
from qad_mapmpedit_cmd import QadMAPMPEDITCommandClass
from qad_joindisjoin_cmd import QadJOINCommandClass, QadDISJOINCommandClass
from qad_array_cmd import QadARRAYCommandClass, QadARRAYRECTCommandClass, QadARRAYPATHCommandClass, QadARRAYPOLARCommandClass


# Classe che gestisce i comandi di Qad
class QadCommandsClass():
   # quando si aggiunge un nuovo comando bisogna
   # 1) aggiungerlo nella lista __cmdObjs nella funzione __init__ 
   # 2) se il comando può essere richiamato da menu o da toolbar vedere la funzione Qad::initGui (qad.py)
   #    e ricordarsi di inserire l'icona in resources.qrc e di ricompilare le risorse
   # 3) aggiungere funzione per l'avvio del comando "run<nome_comando>Command"
   
   def __init__(self, plugIn):   
      self.plugIn = plugIn
      
      self.__cmdObjs = [] # lista interna degli oggetti comandi
      self.__cmdObjs.append(QadIDCommandClass(self.plugIn)) # ID
      self.__cmdObjs.append(QadSETVARCommandClass(self.plugIn)) # SETVAR
      self.__cmdObjs.append(QadPLINECommandClass(self.plugIn)) # PLINE
      self.__cmdObjs.append(QadSETCURRLAYERBYGRAPHCommandClass(self.plugIn))# SETCURRLAYERBYGRAPH
      self.__cmdObjs.append(QadSETCURRUPDATEABLELAYERBYGRAPHCommandClass(self.plugIn)) # SETCURRUPDATEABLELAYERBYGRAPH
      self.__cmdObjs.append(QadARCCommandClass(self.plugIn)) # ARC
      self.__cmdObjs.append(QadCIRCLECommandClass(self.plugIn)) # CIRCLE
      self.__cmdObjs.append(QadDSETTINGSCommandClass(self.plugIn)) # DSETTINGS
      self.__cmdObjs.append(QadLINECommandClass(self.plugIn)) # LINE
      self.__cmdObjs.append(QadERASECommandClass(self.plugIn)) # ERASE
      self.__cmdObjs.append(QadMPOLYGONCommandClass(self.plugIn)) # MPOLYGON
      self.__cmdObjs.append(QadMBUFFERCommandClass(self.plugIn)) # MBUFFER
      self.__cmdObjs.append(QadROTATECommandClass(self.plugIn)) # ROTATE
      self.__cmdObjs.append(QadMOVECommandClass(self.plugIn)) # MOVE
      self.__cmdObjs.append(QadSCALECommandClass(self.plugIn)) # SCALE
      self.__cmdObjs.append(QadCOPYCommandClass(self.plugIn)) # COPY
      self.__cmdObjs.append(QadOFFSETCommandClass(self.plugIn)) # OFFSET
      self.__cmdObjs.append(QadEXTENDCommandClass(self.plugIn)) # EXTEND
      self.__cmdObjs.append(QadTRIMCommandClass(self.plugIn)) # TRIM
      self.__cmdObjs.append(QadRECTANGLECommandClass(self.plugIn)) # RECTANGLE
      self.__cmdObjs.append(QadMIRRORCommandClass(self.plugIn)) # MIRROR
      self.__cmdObjs.append(QadUNDOCommandClass(self.plugIn)) # UNDO
      self.__cmdObjs.append(QadREDOCommandClass(self.plugIn)) # REDO
      self.__cmdObjs.append(QadINSERTCommandClass(self.plugIn)) # INSERT
      self.__cmdObjs.append(QadTEXTCommandClass(self.plugIn)) # TEXT
      self.__cmdObjs.append(QadSTRETCHCommandClass(self.plugIn)) # STRETCH
      self.__cmdObjs.append(QadBREAKCommandClass(self.plugIn)) # BREAK
      self.__cmdObjs.append(QadPEDITCommandClass(self.plugIn)) # PEDIT
      self.__cmdObjs.append(QadFILLETCommandClass(self.plugIn)) # FILLET
      self.__cmdObjs.append(QadPOLYGONCommandClass(self.plugIn)) # POLYGON
      self.__cmdObjs.append(QadDIMLINEARCommandClass(self.plugIn)) # DIMLINEAR
      self.__cmdObjs.append(QadDIMALIGNEDCommandClass(self.plugIn)) # DIMALIGNED
      self.__cmdObjs.append(QadDIMARCCommandClass(self.plugIn)) # DIMALIGNED
      self.__cmdObjs.append(QadDIMSTYLECommandClass(self.plugIn)) # DIMSTYLE
      self.__cmdObjs.append(QadHELPCommandClass(self.plugIn)) # HELP
      self.__cmdObjs.append(QadLENGTHENCommandClass(self.plugIn)) # LENGTHEN
      self.__cmdObjs.append(QadOPTIONSCommandClass(self.plugIn)) # OPTIONS
      self.__cmdObjs.append(QadMAPMPEDITCommandClass(self.plugIn)) # MAPMEDIT
      self.__cmdObjs.append(QadJOINCommandClass(self.plugIn)) # JOIN
      self.__cmdObjs.append(QadDISJOINCommandClass(self.plugIn)) # DISJOIN
      self.__cmdObjs.append(QadARRAYCommandClass(self.plugIn)) # ARRAY
      self.__cmdObjs.append(QadARRAYRECTCommandClass(self.plugIn)) # ARRAYRECT
      self.__cmdObjs.append(QadARRAYPATHCommandClass(self.plugIn)) # ARRAYPATH
      self.__cmdObjs.append(QadARRAYPOLARCommandClass(self.plugIn)) # ARRAYPOLAR
      
      self.actualCommand = None  # Comando in corso di esecuzione
   
      # scarto gli alias che hanno lo stesso nome dei comandi
      exceptionList = []
      for cmdObj in self.__cmdObjs:
         exceptionList.append(cmdObj.getName())
         exceptionList.append("_" + cmdObj.getEnglishName())
         
      # carico alias dei comandi
      self.commandAliases = QadCommandAliasesClass()
      self.commandAliases.load("", exceptionList)
      
      self.usedCmdNames = QadUsedCmdNamesClass()
      
      
   def isValidCommand(self, command):
      cmd = self.getCommandObj(command)
      if cmd:
         del cmd
         return True
      else:
         return False


   def isValidEnvVariable(self, variable):
      # verifico se è una variabile di sistema
      if QadVariables.get(variable) is not None:
         return True
      else:
         return False
   
   
   def showCommandPrompt(self):
      if self.plugIn is not None:
         self.plugIn.showInputMsg() # visualizza prompt standard per richiesta comando 
   
   def showMsg(self, msg, displayPromptAfterMsg = False):
      if self.plugIn is not None:
         self.plugIn.showMsg(msg, displayPromptAfterMsg)

   def showErr(self, err):
      if self.plugIn is not None:
         self.plugIn.showErr(err)


   #============================================================================
   # getCommandObj
   #============================================================================
   def getCommandObj(self, cmdName, useAlias = True):
      if cmdName is None:
         return None
      if cmdName == "":
         return None
      upperCommand = cmdName.upper()
      if upperCommand[0] == "_":
         englishName = True
         upperCommand = upperCommand[1:] # salto il primo carattere di "_"
      else:
         englishName = False 
      
      for cmd in self.__cmdObjs:
         if englishName:
            if upperCommand == cmd.getEnglishName(): # in inglese
               return cmd.instantiateNewCmd()
         else:
            if upperCommand == cmd.getName(): # in lingua locale
               return cmd.instantiateNewCmd()
      
      if cmdName == "MACRO_RUNNER":
         return QadMacroRunnerCommandClass(self.plugIn)
      else:
         if useAlias:
            command = self.commandAliases.getCommandName(cmdName)
            return self.getCommandObj(command, False)
         else:
            return None
      
      
   #============================================================================
   # getCommandNames
   #============================================================================
   def getCommandNames(self):
      """ Return a list of pairs : [(<local cmd name>, <english cmd name>)...]"""     
      cmdNames = []
      # ricavo la lista dei nomi dei comandi
      for cmd in self.__cmdObjs:
         cmdNames.append([cmd.getName(), cmd.getEnglishName]) # in lingua locale, in inglese
      # aggiungo gli alias
      for alias in self.commandAliases.getCommandAliasDict().keys():
         cmdNames.append([alias, alias])
         
      return cmdNames
         
   
   #============================================================================
   # run
   #============================================================================
   def run(self, command, param = None):
      try:
         # se c'é un comando attivo
         if self.actualCommand is not None:
            return
   
         # eccezione per comando virtuale "QadVirtualSelCommandClass" che in realtà non è un comando
         # ma è usato per selezionare oggetti quando nessun comando è attivo
         if command == "QadVirtualSelCommandClass":
            self.actualCommand = QadVirtualSelCommandClass(self.plugIn)
            # param è la posizione corrente del mouse
            if self.actualCommand.run(False, param) == True: # comando terminato
               self.clearCommand()
            return
   
         # eccezione per comando virtuale "QadVirtualGripCommandsClass" che in realtà non è un comando
         # ma è usato per modificare gli oggetti selezionati da grip points
         if command == "QadVirtualGripCommandsClass":
            self.actualCommand = QadVirtualGripCommandsClass(self.plugIn)
            # param è una lista in cui:
            # il primo elemento è il codice del comando da eseguire
            # il secondo elemento è entitySetGripPoints
            # il terzo elemento è il punto del grip corrente
            self.actualCommand.entitySetGripPoints = param[1]
            self.actualCommand.basePt = param[2]
            self.actualCommand.initStartCommand(param[0])
            if self.actualCommand.run(False) == True: # comando terminato
               self.clearCommand()
            return
         
         self.actualCommand = self.getCommandObj(command)
         if self.actualCommand is None:
            # verifico se è una variabile di sistema
            if QadVariables.get(command) is not None:
               self.showMsg("\n")
               # lancio comando SETVAR per settare la variabile
               args = [QadMsg.translate("Command_list", "SETVAR"), command]
               return self.runMacro(args)
               
            msg = QadMsg.translate("QAD", "\nInvalid command \"{0}\".")
            self.showErr(msg.format(command))
            return
   
         self.usedCmdNames.setUsed(command)
         self.plugIn.clearEntityGripPoints() # pulisco i grip points correnti
         if self.actualCommand.run() == True: # comando terminato
            self.clearCommand()

      except Exception as e:
         self.abortCommand()
         displayError(e)
          
         
   #============================================================================
   # runMacro
   #============================================================================
   def runMacro(self, args):
      try:
         # se non c'é alcun comando attivo
         if self.actualCommand is not None:
            return
         
         self.actualCommand = self.getCommandObj("MACRO_RUNNER")
         if self.actualCommand is None:
            msg = QadMsg.translate("QAD", "\nInvalid command \"{0}\".")
            self.showErr(msg.format(command))
            return
   
         self.plugIn.clearEntityGripPoints() # pulisco i grip points correnti
         self.actualCommand.setCmdAndOptionsToRun(args)
         
         self.showMsg(args[0]) # visualizzo il nome del comando in macro
         if self.actualCommand.run() == True: # comando terminato
            self.clearCommand()

      except Exception as e:
         self.abortCommand()
         displayError(e)


   #============================================================================
   # continueCommandFromMapTool
   #============================================================================
   def continueCommandFromMapTool(self):
      try:
         # se non c'é alcun comando attivo
         if self.actualCommand is None:
            return
         msg = None
         # se é stato premuto il tasto destro del mouse valuto cosa é stato inserito nella finestra di testo
         if self.actualCommand.getPointMapTool().rightButton == True:
            msg = self.actualCommand.getCurrMsgFromTxtWindow()
            if (msg is not None) and len(msg) > 0:
               self.actualCommand.showEvaluateMsg()
            else:
               if self.actualCommand.run(True) == True: # comando terminato
                  self.clearCommand()
         else:
            if self.actualCommand.run(True) == True: # comando terminato
               self.clearCommand()

      except Exception as e:
         self.abortCommand()
         displayError(e)


   #============================================================================
   # continueCommandFromTextWindow
   #============================================================================
   def continueCommandFromTextWindow(self, msg):
      try:
         # se non c'é alcun comando attivo
         if self.actualCommand is None:
            return
         if self.actualCommand.run(False, msg) == True: # comando terminato
            self.clearCommand()

      except Exception as e:
         self.abortCommand()
         displayError(e)

            
   #============================================================================
   # abortCommand
   #============================================================================
   def abortCommand(self):
      # se non c'é alcun comando attivo
      if self.actualCommand is None:
         self.showCommandPrompt() # visualizza prompt standard per richiesta comando 
         self.plugIn.setStandardMapTool()               
      else:
         self.showMsg(QadMsg.translate("QAD", "*Canceled*"))
         self.clearCommand()
         # pulisco le entità selezionate e i grip points correnti
         self.plugIn.clearCurrentObjsSelection()


   #============================================================================
   # clearCommand
   #============================================================================
   def clearCommand(self):
      if self.actualCommand is None:
         return
      
      # eccezione per comando virtuale "QadVirtualGripCommandsClass" che in realtà non è un comando
      # ma è usato per modificare gli oggetti selezionati da grip points
      if self.actualCommand.getName() == "QadVirtualGripCommandsClass":
         # ridisegno i grip point nelle nuove posizioni resettando quelli selezionati
         self.plugIn.tool.clearEntityGripPoints()
         self.plugIn.tool.refreshEntityGripPoints()
      else:
         # eccezione per comando virtuale "QadVirtualSelCommandClass" che in realtà non è un comando
         # ma è usato per selezionare oggetti quando nessun comando è attivo
         if self.actualCommand.getName() != "QadVirtualSelCommandClass":
            qad_utils.deselectAll(self.plugIn.canvas.layers())
         
      del self.actualCommand
      self.actualCommand = None
      self.plugIn.setStandardMapTool()
      self.showCommandPrompt() # visualizza prompt standard per richiesta comando 


   #============================================================================
   # forceCommandMapToolSnapTypeOnce
   #============================================================================
   def forceCommandMapToolSnapTypeOnce(self, snapType, snapParams = None):
      # se non c'é alcun comando attivo
      if self.actualCommand is None:
         return
      # se non c'é un maptool del comando attuale
      if self.actualCommand.getPointMapTool() is None:
         return
      # se il maptool del comando attuale se non é attivo
      if self.plugIn.canvas.mapTool() != self.actualCommand.getPointMapTool():
         self.actualCommand.setMapTool(self.actualCommand.getPointMapTool())
      self.actualCommand.getPointMapTool().forceSnapTypeOnce(snapType, snapParams)


   #============================================================================
   # getCurrenPointFromCommandMapTool
   #============================================================================
   def getCurrenPointFromCommandMapTool(self):
      # se non c'é alcun comando attivo
      if self.actualCommand is None:
         return None
      # se non c'é un maptool del comando attuale
      if self.actualCommand.getPointMapTool() is None:
         return None
      # se il maptool del comando attuale se non é attivo
      if self.plugIn.canvas.mapTool() != self.actualCommand.getPointMapTool():
         self.actualCommand.setMapTool(self.actualCommand.getPointMapTool())
      return self.actualCommand.getPointMapTool().tmpPoint
      

   #============================================================================
   # refreshCommandMapToolSnapType
   #============================================================================
   def refreshCommandMapToolSnapType(self):
      # se non c'é alcun comando attivo
      if self.actualCommand is None:
         return
      # se non c'é un maptool attivo del comando attuale
      if self.actualCommand.getPointMapTool() is None:
         return
      self.actualCommand.getPointMapTool().refreshSnapType()
      
      
   #============================================================================
   # refreshCommandMapToolOrthoMode
   #============================================================================
   def refreshCommandMapToolOrthoMode(self):
      # se non c'é alcun comando attivo
      if self.actualCommand is None:
         return
      # se non c'é un maptool attivo del comando attuale
      if self.actualCommand.getPointMapTool() is None:
         return
      self.actualCommand.getPointMapTool().refreshOrthoMode()
      
      
   #============================================================================
   # refreshCommandMapToolAutoSnap
   #============================================================================
   def refreshCommandMapToolAutoSnap(self):
      # se non c'é alcun comando attivo
      if self.actualCommand is None:
         return
      # se non c'é un maptool attivo del comando attuale
      if self.actualCommand.getPointMapTool() is None:
         return
      self.actualCommand.getPointMapTool().refreshAutoSnap()



   #============================================================================
   # getMoreUsedCmd
   #============================================================================
   def getMoreUsedCmd(self, filter):
      upperFilter = filter.upper()
      cmdName, qty = self.usedCmdNames.getMoreUsed(upperFilter)
      if cmdName == "": # nessun comando
         if upperFilter[0] == "_":
            englishName = True
            upperFilter = upperFilter[1:] # salto il primo carattere di "_"
         else:
            englishName = False 
         
         for cmd in self.__cmdObjs:
            if englishName:
               if cmd.getEnglishName().startswith(upperFilter): # in inglese
                  return cmd.getEnglishName(), 0
            else:
               if cmd.getName().startswith(upperFilter): # in lingua locale
                  return cmd.getName(), 0
      return cmdName, 0


#===============================================================================
# QadMacroRunnerCommandClass
#===============================================================================
class QadMacroRunnerCommandClass(QadCommandClass):
   # Classe che gestisce l'esecuzione di altri comandi

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadMacroRunnerCommandClass(self.plugIn)

   def getName(self):
      if self.command is None:
         return "MACRO_RUNNER"
      else:
         return self.command.getName()

   def getEnglishName(self):
      return "MACRO_RUNNER"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runREDOCommand)
      
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.command = None
      self.args = [] # lista degli argomenti
      self.argsIndex = -1

   def __del__(self):
      QadCommandClass.__del__(self)
      if self.command is not None:
         del self.command

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.command is not None:
         return self.command.getPointMapTool(drawMode)
      else:
         return QadCommandClass.getPointMapTool(self, drawMode)


   def setCmdAndOptionsToRun(self, CmdAndArglist):
      # primo elemento della lista = nome comando
      # gli altri elementi sono gli argomenti del comando None = input dell'utente
      cmdName = CmdAndArglist[0]
      self.args = CmdAndArglist[1:] # copio la lista saltando il primo elemento
      
      self.command = self.plugIn.getCommandObj(cmdName)

      if self.command is None:
         msg = QadMsg.translate("QAD", "\nInvalid command \"{0}\".")
         self.showErr(msg.format(command))
         return False
      self.plugIn.updateHistoryfromTxtWindow(cmdName)
      return True

            
   def run(self, msgMapTool = False, msg = None):
      
      if self.command.run(msgMapTool, msg) == True:
         return True
      
      # se l'input precedente era valido
      if self.command.isValidPreviousInput == True:
         # al comando passo la prossima opzione
         self.argsIndex = self.argsIndex + 1
         if self.argsIndex < len(self.args):
            arg = self.args[self.argsIndex]
            if arg is not None:
               self.showEvaluateMsg(arg)

      return False


#===============================================================================
# QadUsedCmdNamesClass usata per contare quante volte sono stati usati i comandi
#===============================================================================


class QadUsedCmdNamesClass():
   def __init__(self):
      self.__nUsedCmdNames = [] # lista interna di item composti da (nome comando o alias, n. di volte che è stato usato)

   def __del__(self):
      del self.__nUsedCmdNames[:]


   def setUsed(self, cmdName):
      uName = cmdName.upper()
      for _cmdName in self.__nUsedCmdNames:
         if _cmdName[0] == uName:
            _cmdName[1] = _cmdName[1] + 1
            return _cmdName[1]

      self.__nUsedCmdNames.append([uName, 1])
      return 1


   def getUsed(self, cmdName):
      uName = cmdName.upper()
      for _cmdName in self.__nUsedCmdNames:
         if _cmdName[0] == uName:
            return _cmdName[1]

      return 0
   
   def getMoreUsed(self, filter):
      moreUsedCmd = ""
      nUsedCmd = 0
      for _cmdName in self.__nUsedCmdNames:
         if _cmdName[0].startswith(filter):
            if _cmdName[1] > nUsedCmd:
               moreUsedCmd = _cmdName[0]
               nUsedCmd = _cmdName[1]

      return moreUsedCmd, nUsedCmd
   

def displayError(exception = None):
   exc_type, exc_value, exc_traceback = sys.exc_info()
   format_exception = traceback.format_exception(exc_type, exc_value, exc_traceback)
   stk = QadMsg.translate("QAD", "Well, this is embarrassing message...\n\n")
   for s in format_exception:
      stk += s
   if exception is not None: stk += "\n" + exception.__doc__
   QMessageBox.critical(None, "QAD", stk)