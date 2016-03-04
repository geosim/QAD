# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando DSETTINGS per impostazione disegno
 
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
from qgis.core import QgsApplication


from qad_dsettings_dlg import QadDSETTINGSDialog


from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg


# Classe che gestisce il comando DSETTINGS
class QadDSETTINGSCommandClass(QadCommandClass):
   
   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadDSETTINGSCommandClass(self.plugIn)
   
   def getName(self):
      return QadMsg.translate("Command_list", "DSETTINGS")

   def getEnglishName(self):
      return "DSETTINGS"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runDSETTINGSCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/dsettings.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_DSETTINGS", "Drafting Settings (snaps, etc.).")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
            
   def run(self, msgMapTool = False, msg = None):
      Form = QadDSETTINGSDialog(self.plugIn)
      Form.exec_()
      return True