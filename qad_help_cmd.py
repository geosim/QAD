# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando HELP che apre la guida di QAD
 
                              -------------------
        begin                : 2015-08-31
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
from qad_msg import QadMsg, qadShowPluginHelp


# Classe che gestisce il comando HELP
class QadHELPCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadHELPCommandClass(self.plugIn)

   def getName(self):
      return QadMsg.translate("Command_list", "HELP")

   def getEnglishName(self):
      return "HELP"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runHELPCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/help.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_HELP", "The QAD manual will be showed.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
        
   def run(self, msgMapTool = False, msg = None):
      qadShowPluginHelp()       
      return True
