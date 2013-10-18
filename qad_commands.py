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


# Classe che gestisce i comandi di Qad
class QadCommandsClass():
   # quando si aggiunge un nuovo comando bisogna
   # 1) aggiungerlo nella lista commands nella funzione __init__ 
   # 2) aggiungere la sua chiamata nella funzione getCommandObj
   # 3) se il comando può essere richiamato da menu o da toolbar vedere la funzione Qad::initGui
   #    e ricordarsi di inserire l'icona in resources.qrc e di ricompilare le risorse
   
   def __init__(self, plugIn):   
      self.plugIn = plugIn
      self.commands = []  # lista dei comandi
      self.actualCommand = None  # Comando in corso di esecuzione

      self.commands.append(QadMsg.get(3))   # "ID"
      self.commands.append(QadMsg.get(6))   # "MODIVAR"
      self.commands.append(QadMsg.get(35))  # "PLINEA"
      self.commands.append(QadMsg.get(49))  # "SETCURRLAYERDAGRAFICA"
      self.commands.append(QadMsg.get(74))  # "SETCURRMODIFLAYERDAGRAFICA"
      self.commands.append(QadMsg.get(54))  # "ARCO"
      self.commands.append(QadMsg.get(76))  # "CERCHIO"
      self.commands.append(QadMsg.get(111)) # "IMPOSTADIS"
      self.commands.append(QadMsg.get(117)) # "LINEA"
      self.commands.append(QadMsg.get(129)) # "CANCELLA"
      self.commands.append(QadMsg.get(166)) # "MPOLYGON"
      self.commands.append(QadMsg.get(169)) # "MBUFFER"
      self.commands.append(QadMsg.get(179)) # "ROTATE"
      self.commands.append(QadMsg.get(189)) # "SPOSTA"
      self.commands.append(QadMsg.get(195)) # "SCALA"
      self.commands.append(QadMsg.get(202)) # "COPIA"
      self.commands.append(QadMsg.get(221)) # "OFFSET"
   
      # carico alias dei comandi
      self.commandAliases = QadCommandAliasesClass()
      self.commandAliases.load()
      for alias in self.commandAliases.getCommandAliasDict().keys():
         self.commands.append(alias)
      
   
   def showCommandPrompt(self):
      if self.plugIn is not None:
         self.plugIn.showInputMsg() # visualizza prompt standard per richiesta comando 
   
   def showMsg(self, msg):
      if self.plugIn is not None:
         self.plugIn.showMsg(msg)

   def showErr(self, err):
      if self.plugIn is not None:
         self.plugIn.showErr(err)


   #============================================================================
   # getCommandObj
   #============================================================================
   def getCommandObj(self, cmdName, useAlias = True):
      if cmdName is None:
         return None
      
      if type(cmdName) == QString:
         command = cmdName.toUpper()
      else:
         command = cmdName.upper()
         
      if command == QadMsg.get(3): # "ID"
         return QadIDCommandClass(self.plugIn)
      elif command == QadMsg.get(6): # "MODIVAR"
         return QadSETVARCommandClass(self.plugIn)
      elif command == QadMsg.get(35): # "PLINEA"
         return QadPLINECommandClass(self.plugIn)
      elif command == QadMsg.get(49): # "SETCURRLAYERDAGRAFICA"
         return QadSETCURRLAYERBYGRAPHCommandClass(self.plugIn)
      elif command == QadMsg.get(74): # "SETCURRMODIFLAYERDAGRAFICA"
         return QadSETCURRUPDATEABLELAYERBYGRAPHCommandClass(self.plugIn)
      elif command == QadMsg.get(54): # "ARCO"
         return QadARCCommandClass(self.plugIn)
      elif command == QadMsg.get(76): # "CERCHIO"
         return QadCIRCLECommandClass(self.plugIn)
      elif command == QadMsg.get(111): # "IMPOSTADIS"
         return QadDSETTINGSCommandClass(self.plugIn)
      elif command == QadMsg.get(117): # "LINEA"
         return QadLINECommandClass(self.plugIn)
      elif command == QadMsg.get(129): # "CANCELLA"
         return QadERASECommandClass(self.plugIn)
      elif command == QadMsg.get(166): # "MPOLYGON"
         return QadMPOLYGONCommandClass(self.plugIn)
      elif command == QadMsg.get(169): # "MBUFFER"
         return QadMBUFFERCommandClass(self.plugIn)
      elif command == QadMsg.get(179): # "ROTATE"
         return QadROTATECommandClass(self.plugIn)
      elif command == QadMsg.get(189): # "SPOSTA"
         return QadMOVECommandClass(self.plugIn)
      elif command == QadMsg.get(195): # "SCALA"
         return QadSCALECommandClass(self.plugIn)
      elif command == QadMsg.get(202): # "COPIA"
         return QadCOPYCommandClass(self.plugIn)
      elif command == QadMsg.get(221): # "OFFSET"
         return QadOFFSETCommandClass(self.plugIn)
      else:
         if useAlias:
            command = self.commandAliases.getCommandName(command)
            return self.getCommandObj(command, False)
         else:
            return None
   
   def run(self, command):
      # se non c'è alcun comando attivo
      if self.actualCommand is not None:
         return
      
      self.actualCommand = self.getCommandObj(command)
      if self.actualCommand is None:
         msg = QadMsg.get(2) # "\nComando sconosciuto \"{0}\"."
         self.showErr(msg.format(command))
         return
               
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
         if (msg is not None) and (len(msg) > 0):
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
         return
      self.showMsg(QadMsg.get(8)) # \n*Annullato*\n"
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
      if self.actualCommand.PointMapTool is None:
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
      if self.actualCommand.PointMapTool is None:
         return
      self.actualCommand.PointMapTool.refreshSnapType()
      
      
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
            