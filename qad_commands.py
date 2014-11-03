# -*- coding: latin1 -*-

"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire i comandi
 
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
from qgis.gui import *


import qad_debug
from qad_maptool import QadMapTool
from qad_msg import QadMsg
from qad_cmd_aliases import *

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
from qad_dim_cmd import QadDIMLINEARCommandClass, QadDIMALIGNEDCommandClass


# Classe che gestisce i comandi di Qad
class QadCommandsClass():
   # quando si aggiunge un nuovo comando bisogna
   # 1) aggiungerlo nella lista commands nella funzione __init__ 
   # 2) aggiungere la sua chiamata nella funzione getCommandObj
   # 3) se il comando può essere richiamato da menu o da toolbar vedere la funzione Qad::initGui (qad.py)
   #    e ricordarsi di inserire l'icona in resources.qrc e di ricompilare le risorse
   # 4) aggiungere funzione per l'avvio del comando "run<nome_comando>Command"
   
   def __init__(self, plugIn):   
      self.plugIn = plugIn
      self.commands = []  # lista dei comandi
      self.actualCommand = None  # Comando in corso di esecuzione

      self.commands.append(QadMsg.translate("Command_list", "ID"))
      self.commands.append(QadMsg.translate("Command_list", "MODIVAR"))
      self.commands.append(QadMsg.translate("Command_list", "PLINEA"))
      self.commands.append(QadMsg.translate("Command_list", "SETCURRLAYERDAGRAFICA"))
      self.commands.append(QadMsg.translate("Command_list", "SETCURRMODIFLAYERDAGRAFICA"))
      self.commands.append(QadMsg.translate("Command_list", "ARCO"))
      self.commands.append(QadMsg.translate("Command_list", "CERCHIO"))
      self.commands.append(QadMsg.translate("Command_list", "IMPOSTADIS"))
      self.commands.append(QadMsg.translate("Command_list", "LINEA"))
      self.commands.append(QadMsg.translate("Command_list", "CANCELLA"))
      self.commands.append(QadMsg.translate("Command_list", "MPOLIGONO"))
      self.commands.append(QadMsg.translate("Command_list", "MBUFFER"))
      self.commands.append(QadMsg.translate("Command_list", "RUOTA"))
      self.commands.append(QadMsg.translate("Command_list", "SPOSTA"))
      self.commands.append(QadMsg.translate("Command_list", "SCALA"))
      self.commands.append(QadMsg.translate("Command_list", "COPIA"))
      self.commands.append(QadMsg.translate("Command_list", "OFFSET"))
      self.commands.append(QadMsg.translate("Command_list", "ESTENDI"))
      self.commands.append(QadMsg.translate("Command_list", "TAGLIA"))
      self.commands.append(QadMsg.translate("Command_list", "RETTANGOLO"))
      self.commands.append(QadMsg.translate("Command_list", "SPECCHIO"))
      self.commands.append(QadMsg.translate("Command_list", "ANNULLA"))
      self.commands.append(QadMsg.translate("Command_list", "RIPRISTINA"))
      self.commands.append(QadMsg.translate("Command_list", "INSER"))
      self.commands.append(QadMsg.translate("Command_list", "TESTO"))
      self.commands.append(QadMsg.translate("Command_list", "STIRA"))
      self.commands.append(QadMsg.translate("Command_list", "SPEZZA"))
      self.commands.append(QadMsg.translate("Command_list", "EDITPL"))
      self.commands.append(QadMsg.translate("Command_list", "RACCORDO"))
      self.commands.append(QadMsg.translate("Command_list", "DIMLINEARE"))
      self.commands.append(QadMsg.translate("Command_list", "DIMALLINEATA"))
   
      # carico alias dei comandi
      self.commandAliases = QadCommandAliasesClass()
      self.commandAliases.load()
      for alias in self.commandAliases.getCommandAliasDict().keys():
         self.commands.append(alias)
      
   
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
      command = cmdName.upper()
         
      if command == QadMsg.translate("Command_list", "ID"):
         return QadIDCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "MODIVAR"):
         return QadSETVARCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "PLINEA"):
         return QadPLINECommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "SETCURRLAYERDAGRAFICA"):
         return QadSETCURRLAYERBYGRAPHCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "SETCURRMODIFLAYERDAGRAFICA"):
         return QadSETCURRUPDATEABLELAYERBYGRAPHCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "ARCO"):
         return QadARCCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "CERCHIO"):
         return QadCIRCLECommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "IMPOSTADIS"):
         return QadDSETTINGSCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "LINEA"):
         return QadLINECommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "CANCELLA"):
         return QadERASECommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "MPOLIGONO"):
         return QadMPOLYGONCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "MBUFFER"):
         return QadMBUFFERCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "RUOTA"):
         return QadROTATECommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "SPOSTA"):
         return QadMOVECommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "SCALA"):
         return QadSCALECommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "COPIA"):
         return QadCOPYCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "OFFSET"):
         return QadOFFSETCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "ESTENDI"):
         return QadEXTENDCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "TAGLIA"):
         return QadTRIMCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "RETTANGOLO"):
         return QadRECTANGLECommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "SPECCHIO"):
         return QadMIRRORCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "ANNULLA"):
         return QadUNDOCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "RIPRISTINA"):
         return QadREDOCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "INSER"):
         return QadINSERTCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "TESTO"):
         return QadTEXTCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "STIRA"):
         return QadSTRETCHCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "SPEZZA"):
         return QadBREAKCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "EDITPL"):
         return QadPEDITCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "RACCORDO"):
         return QadFILLETCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "DIMLINEARE"):
         return QadDIMLINEARCommandClass(self.plugIn)
      elif command == QadMsg.translate("Command_list", "DIMALLINEATA"):
         return QadDIMALIGNEDCommandClass(self.plugIn)      
      
      elif command == "MACRO_RUNNER":
         return QadMacroRunnerCommandClass(self.plugIn)
      else:
         if useAlias:
            command = self.commandAliases.getCommandName(command)
            return self.getCommandObj(command, False)
         else:
            return None
   
   #============================================================================
   # run
   #============================================================================
   def run(self, command):
      # se non c'è alcun comando attivo
      if self.actualCommand is not None:
         return
      
      self.actualCommand = self.getCommandObj(command)
      if self.actualCommand is None:
         msg = QadMsg.translate("QAD", "\nComando sconosciuto \"{0}\".")
         self.showErr(msg.format(command))
         return
         
      if self.actualCommand.run() == True: # comando terminato
         self.clearCommand()
         
         
   #============================================================================
   # runMacro
   #============================================================================
   def runMacro(self, args):
      # se non c'è alcun comando attivo
      if self.actualCommand is not None:
         return
      
      self.actualCommand = self.getCommandObj("MACRO_RUNNER")
      if self.actualCommand is None:
         msg = QadMsg.translate("QAD", "\nComando sconosciuto \"{0}\".")
         self.showErr(msg.format(command))
         return
      self.actualCommand.setCmdAndOptionsToRun(args)
      
      self.showMsg(args[0]) # visualizzo il nome del comando in macro
      if self.actualCommand.run() == True: # comando terminato
         self.clearCommand()


   #============================================================================
   # continueCommandFromMapTool
   #============================================================================
   def continueCommandFromMapTool(self):
      # se non c'è alcun comando attivo
      if self.actualCommand is None:
         return
      msg = None
      # se è stato premuto il tasto destro del mouse valuto cosa è stato inserito nella finestra di testo
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


   #============================================================================
   # continueCommandFromTextWindow
   #============================================================================
   def continueCommandFromTextWindow(self, msg):
      # se non c'è alcun comando attivo
      if self.actualCommand is None:
         return
      if self.actualCommand.run(False, msg) == True: # comando terminato
         self.clearCommand()

            
   #============================================================================
   # abortCommand
   #============================================================================
   def abortCommand(self):
      # se non c'è alcun comando attivo
      if self.actualCommand is None:
         self.showCommandPrompt() # visualizza prompt standard per richiesta comando 
         self.plugIn.setStandardMapTool()               
      else:
         self.showErr(QadMsg.translate("QAD", "*Annullato*"))
         self.clearCommand()


   #============================================================================
   # clearCommand
   #============================================================================
   def clearCommand(self):
      if self.actualCommand is None:
         return
      del self.actualCommand
      self.actualCommand = None    
      self.showCommandPrompt() # visualizza prompt standard per richiesta comando 
      self.plugIn.setStandardMapTool()      


   #============================================================================
   # forceCommandMapToolSnapTypeOnce
   #============================================================================
   def forceCommandMapToolSnapTypeOnce(self, snapType, snapParams = None):
      # se non c'è alcun comando attivo
      if self.actualCommand is None:
         return
      # se non c'è un maptool del comando attuale
      if self.actualCommand.getPointMapTool() is None:
         return
      # se il maptool del comando attuale se non è attivo
      if self.plugIn.canvas.mapTool() != self.actualCommand.getPointMapTool():
         self.actualCommand.setMapTool(self.actualCommand.getPointMapTool())
      self.actualCommand.getPointMapTool().forceSnapTypeOnce(snapType, snapParams)


   #============================================================================
   # getCurrenPointFromCommandMapTool
   #============================================================================
   def getCurrenPointFromCommandMapTool(self):
      # se non c'è alcun comando attivo
      if self.actualCommand is None:
         return None
      # se non c'è un maptool del comando attuale
      if self.actualCommand.PointMapTool is None:
         return None
      # se il maptool del comando attuale se non è attivo
      if self.plugIn.canvas.mapTool() != self.actualCommand.getPointMapTool():
         self.actualCommand.setMapTool(self.actualCommand.getPointMapTool())
      return self.actualCommand.PointMapTool.tmpPoint
      

   #============================================================================
   # refreshCommandMapToolSnapType
   #============================================================================
   def refreshCommandMapToolSnapType(self):
      # se non c'è alcun comando attivo
      if self.actualCommand is None:
         return
      # se non c'è un maptool attivo del comando attuale
      if self.actualCommand.getPointMapTool() is None:
         return
      self.actualCommand.getPointMapTool().refreshSnapType()
      
      
   #============================================================================
   # refreshCommandMapToolOrthoMode
   #============================================================================
   def refreshCommandMapToolOrthoMode(self):
      # se non c'è alcun comando attivo
      if self.actualCommand is None:
         return
      # se non c'è un maptool attivo del comando attuale
      if self.actualCommand.PointMapTool is None:
         return
      self.actualCommand.PointMapTool.refreshOrthoMode()
      
      
   #============================================================================
   # refreshCommandMapToolAutoSnap
   #============================================================================
   def refreshCommandMapToolAutoSnap(self):
      # se non c'è alcun comando attivo
      if self.actualCommand is None:
         return
      # se non c'è un maptool attivo del comando attuale
      if self.actualCommand.PointMapTool is None:
         return
      self.actualCommand.PointMapTool.refreshAutoSnap()
            
            
#===============================================================================
# QadMacroRunnerCommandClass
#===============================================================================
class QadMacroRunnerCommandClass(QadCommandClass):
   # Classe che gestisce l'esecuzione di altri comandi

   def getName(self):
      if self.command is None:
         return "MACRO_RUNNER"
      else:
         return self.command.getName()

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
      # primo eleemto della lista = nome comando
      # gli altri elementi sono gli argomenti del comando None = input dell'utente
      #qad_debug.breakPoint()
      cmdName = CmdAndArglist[0]
      self.args = CmdAndArglist[1:] # copio la lista saltando il primo elemento
      
      self.command = self.plugIn.getCommandObj(cmdName)

      if self.command is None:
         msg = QadMsg.translate("QAD", "\nComando sconosciuto \"{0}\".")
         self.showErr(msg.format(command))
         return False
      self.plugIn.updateHistoryfromTxtWindow(cmdName)
      return True
            
   def run(self, msgMapTool = False, msg = None):
      #qad_debug.breakPoint()
      
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
               #qad_debug.breakPoint()

      return False
