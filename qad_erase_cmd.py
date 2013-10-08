# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando ERASE per cancellare oggetti
 
                              -------------------
        begin                : 2013-08-01
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
from qad_getpoint import *
from qad_ssget_cmd import QadSSGetClass


# Classe che gestisce il comando ERASE
class QadERASECommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.get(129) # "CANCELLA"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runERASECommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/erase.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.get(130)
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.SSGetClass = QadSSGetClass(plugIn)
      self.SSGetClass.onlyEditableLayers = True

   def __del__(self):
      QadCommandClass.__del__(self)
      del self.SSGetClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 0: # quando si è in fase di selezione entità
         return self.SSGetClass.getPointMapTool(drawMode)
      else:
         return QadCommandClass.getPointMapTool(self, drawMode)

   def run(self, msgMapTool = False, msg = None):
            
      #=========================================================================
      # RICHIESTA PRIMO PUNTO PER SELEZIONE OGGETTI
      if self.step == 0: # inizio del comando
         #qad_debug.breakPoint()
         if self.SSGetClass.run(msgMapTool, msg) == True:
            # selezione terminata
            self.step = 1
            return self.run(msgMapTool, msg)
         else:
            return False
      
      #=========================================================================
      # CANCELLAZIONE OGGETTI
      elif self.step == 1:
         i = 0
         #qad_debug.breakPoint()
         for layerEntitySet in self.SSGetClass.entitySet.layerEntitySetList:
            if not layerEntitySet.layer.isEditable():
               layerEntitySet.layer.startEditing()

            layerEntitySet.layer.beginEditCommand("Feature deleted")     
            for featureId in layerEntitySet.featureIds:
               if layerEntitySet.layer.deleteFeature(featureId) == False:
                  i = i + 1
            layerEntitySet.layer.endEditCommand()
            
         self.plugIn.canvas.refresh()
            
         return True # fine comando

