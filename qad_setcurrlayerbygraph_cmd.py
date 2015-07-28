# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando SETCURRLAYERBYGRAPH per settare il layer corrente tramite selezione grafica
 comando SETCURRUPDATEABLELAYERBYGRAPH per settare il layer corrente e porlo in modifica 
                                       tramite selezione grafica
 
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


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *


from qad_generic_cmd import QadCommandClass
from qad_snapper import *
from qad_getpoint import *
from qad_entsel_cmd import QadEntSelClass
from qad_ssget_cmd import QadSSGetClass
from qad_msg import QadMsg


# Classe che gestisce il comando SETCURRLAYERBYGRAPH
class QadSETCURRLAYERBYGRAPHCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadSETCURRLAYERBYGRAPHCommandClass(self.plugIn)

   def getName(self):
      return QadMsg.translate("Command_list", "SETCURRLAYERDAGRAFICA")

   def getEnglishName(self):
      return "SETCURRLAYERBYGRAPH"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runSETCURRLAYERBYGRAPHCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/setcurrlayerbygraph.png")
   
   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_SETCURRLAYERBYGRAPH", "Seleziona un layer di un oggetto grafico.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.EntSelClass = None

   def __del__(self):
      QadCommandClass.__del__(self)
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 0 or self.step == 1: # quando si é in fase di selezione entità
         return self.EntSelClass.getPointMapTool(drawMode)
      else:
         return QadCommandClass.getPointMapTool(self, drawMode)
   
   def waitForEntsel(self, msgMapTool, msg):
      if self.EntSelClass is not None:
         del self.EntSelClass            
      self.EntSelClass = QadEntSelClass(self.plugIn)
      self.EntSelClass.msg = QadMsg.translate("Command_SETCURRLAYERBYGRAPH", "Selezionare l'oggetto il cui layer diventerà quello corrente: ")
      self.getPointMapTool().setSnapType(QadSnapTypeEnum.DISABLE)
      self.EntSelClass.run(msgMapTool, msg)
        
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando
      
      if self.step == 0:     
         self.waitForEntsel(msgMapTool, msg)
         self.step = 1
         return False # continua
      
      elif self.step == 1:
         if self.EntSelClass.run(msgMapTool, msg) == True:
            if self.EntSelClass.entity.isInitialized():
               layer = self.EntSelClass.entity.layer
               if self.plugIn.canvas.currentLayer() is None or \
                  self.plugIn.canvas.currentLayer() != layer:                              
                  self.plugIn.canvas.setCurrentLayer(layer)
                  self.plugIn.iface.setActiveLayer(layer) # lancia evento di deactivate e activate dei plugin
                  self.plugIn.iface.legendInterface().refreshLayerSymbology(layer)
                  msg = QadMsg.translate("Command_SETCURRLAYERBYGRAPH", "\nIl layer corrente é {0}.")
                  self.showMsg(msg.format(layer.name()))
               del self.EntSelClass
               return True
            else:               
               self.showMsg(QadMsg.translate("Command_SETCURRLAYERBYGRAPH", "Non ci sono geometrie in questa posizione."))
               self.waitForEntsel(msgMapTool, msg)
         return False # continua
         

# Classe che gestisce il comando SETCURRUPDATEABLELAYERBYGRAPH
class QadSETCURRUPDATEABLELAYERBYGRAPHCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadSETCURRUPDATEABLELAYERBYGRAPHCommandClass(self.plugIn)

   def getName(self):
      return QadMsg.translate("Command_list", "SETCURRMODIFLAYERDAGRAFICA")

   def getEnglishName(self):
      return "SETCURRUPDATEABLELAYERBYGRAPH"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runSETCURRUPDATEABLELAYERBYGRAPHCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/setcurrupdateablelayerbygraph.png")
   
   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_SETCURRUPDATEABLELAYERBYGRAPH", "Seleziona un layer di un oggetto grafico e lo rende modificabile.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.SSGetClass = QadSSGetClass(plugIn)
      self.firstTime = True

   def __del__(self):
      QadCommandClass.__del__(self)
      del self.SSGetClass
        
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 0: # quando si é in fase di selezione entità
         return self.SSGetClass.getPointMapTool(drawMode)
      else:
         return QadCommandClass.getPointMapTool(self, drawMode)
        
   def run(self, msgMapTool = False, msg = None):     
      if self.step == 0: # inizio del comando   
         if self.firstTime == True:
            self.showMsg(QadMsg.translate("Command_SETCURRUPDATEABLELAYERBYGRAPH", "\nSelezionare gli oggetti i cui layer diventeranno editabili: "))
            self.firstTime = False
            
         if self.SSGetClass.run(msgMapTool, msg) == True:
            # selezione terminata
            self.step = 1
            return self.run(msgMapTool, msg)
         else:
            return False # continua

      elif self.step == 1: # dopo aver atteso la selezione di oggetti
         message = ""    
         for layerEntitySet in self.SSGetClass.entitySet.layerEntitySetList:
            layer = layerEntitySet.layer       
            if layer.isEditable() == False:
               if layer.startEditing() == True:
                  self.plugIn.iface.legendInterface().refreshLayerSymbology(layer)
                  self.showMsg(QadMsg.translate("Command_SETCURRUPDATEABLELAYERBYGRAPH", "\nIl layer {0} é editabile.").format(layer.name()))

         if len(self.SSGetClass.entitySet.layerEntitySetList) == 1:
            layer = self.SSGetClass.entitySet.layerEntitySetList[0].layer
            if self.plugIn.canvas.currentLayer() is None or \
               self.plugIn.canvas.currentLayer() != layer:               
               self.plugIn.canvas.setCurrentLayer(layer)
               self.plugIn.iface.setActiveLayer(layer) # lancia evento di deactivate e activate dei plugin
               self.plugIn.iface.legendInterface().refreshLayerSymbology(layer)
               self.showMsg(QadMsg.translate("Command_SETCURRUPDATEABLELAYERBYGRAPH", "\nIl layer corrente é {0}.").format(layer.name()))
         
         return True
