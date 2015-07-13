# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando DSETTINGS per impostazione stili di quotatura
 
                              -------------------
        begin                : 2015-05-19
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
from qgis.core import QgsApplication


from qad_dimstyle_dlg import QadDIMSTYLEDialog


from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg


# Classe che gestisce il comando DIMSTYLE
class QadDIMSTYLECommandClass(QadCommandClass):
   
   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadDIMSTYLECommandClass(self.plugIn)
   
   def getName(self):
      return QadMsg.translate("Command_list", "DIMSTILE")

   def getEnglishName(self):
      return "DIMSTYLE"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runDIMSTYLECommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/dimStyle.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_DIMSTYLE", "Crea e modifica gli stili di quota.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
            
   def run(self, msgMapTool = False, msg = None):
      Form = QadDIMSTYLEDialog(self.plugIn)
      Form.exec_()
      return True