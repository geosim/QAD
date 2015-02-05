# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando ERASE per cancellare oggetti
 
                              -------------------
        begin                : 2013-08-01
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
from qad_getpoint import *
from qad_ssget_cmd import QadSSGetClass
import qad_layer


# Classe che gestisce il comando ERASE
class QadERASECommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "CANCELLA")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runERASECommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/erase.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_ERASE", "Cancella oggetti dalla mappa.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.SSGetClass = QadSSGetClass(plugIn)
      self.SSGetClass.onlyEditableLayers = True

   def __del__(self):
      QadCommandClass.__del__(self)
      del self.SSGetClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 0: # quando si é in fase di selezione entità
         return self.SSGetClass.getPointMapTool(drawMode)
      else:
         return QadCommandClass.getPointMapTool(self, drawMode)

   def run(self, msgMapTool = False, msg = None):
            
      #=========================================================================
      # RICHIESTA PRIMO PUNTO PER SELEZIONE OGGETTI
      if self.step == 0: # inizio del comando
         if self.SSGetClass.run(msgMapTool, msg) == True:
            # selezione terminata
            self.step = 1
            return self.run(msgMapTool, msg)
         else:
            return False
      
      #=========================================================================
      # CANCELLAZIONE OGGETTI
      elif self.step == 1:
         self.plugIn.beginEditCommand("Feature deleted", self.SSGetClass.entitySet.getLayerList())
              
         for layerEntitySet in self.SSGetClass.entitySet.layerEntitySetList:
            # plugIn, layer, featureIds, refresh
            if qad_layer.deleteFeaturesToLayer(self.plugIn, layerEntitySet.layer, \
                                               layerEntitySet.featureIds, False) == False:
               self.plugIn.destroyEditCommand()
               return
            
         self.plugIn.endEditCommand()
            
         return True # fine comando

