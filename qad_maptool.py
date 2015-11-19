# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 map tool per lo stato di quiete
 
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


import qad_utils
from qad_variables import *
from qad_rubberband import *
from qad_getpoint import *
from qad_generic_cmd import QadCommandClass
from qad_ssget_cmd import QadSSGetClass
from qad_grip import *
from qad_stretch_cmd import QadGRIPSTRETCHCommandClass
from qad_move_cmd import QadGRIPMOVECommandClass
from qad_msg import QadMsg


# Main Map Tool class.
class QadMapTool(QgsMapTool):
      
   def __init__(self, plugIn):        
      QgsMapTool.__init__(self, plugIn.iface.mapCanvas())
      self.plugIn = plugIn
      self.iface = self.plugIn.iface
      self.canvas = self.plugIn.iface.mapCanvas()      
      self.cursor = QCursor(Qt.BlankCursor)
      self.__csrRubberBand = QadCursorRubberBand(self.canvas, QadCursorTypeEnum.BOX | QadCursorTypeEnum.CROSS)
      self.entitySet = QadEntitySet()
      self.entitySetGripPoints = QadEntitySetGripPoints(plugIn.iface.mapCanvas())
      
   def __del__(self):
      self.removeItems()


   def removeItems(self):      
      if self.__csrRubberBand is not None:
         self.__csrRubberBand.removeItems() # prima lo stacco dal canvas altrimenti non si rimuove perchè usato da canvas
         del self.__csrRubberBand
         __csrRubberBand = None
      self.entitySet.clear()
      self.entitySetGripPoints.removeItems()


   def UpdatedVariablesEvent(self):
      # aggiorna in base alle nuove impostazioni delle variabili
      self.removeItems() 
      self.__csrRubberBand = QadCursorRubberBand(self.canvas, QadCursorTypeEnum.BOX | QadCursorTypeEnum.CROSS)


   def clearEntitySet(self):
      self.entitySet.deselectOnLayer()
      self.entitySet.clear()


   def clearEntityGripPoints(self):
      self.entitySetGripPoints.removeItems() # svuoto la lista


   def refreshEntityGripPoints(self, entitySet = None):
      if entitySet is None:
         entitySet = self.entitySet
      
      # cancello i grip delle entità che non sono in entitySet o che non sono in layer vettoriali modificabili
      i = self.entitySetGripPoints.count() - 1
      while i >= 0:
         entityGripPoint = self.entitySetGripPoints.entityGripPoints[i]
         if entitySet.containsEntity(entityGripPoint.entity) == False or \
            entityGripPoint.entity.layer.type() != QgsMapLayer.VectorLayer or entityGripPoint.entity.layer.isEditable() == False:
            del self.entitySetGripPoints.entityGripPoints[i]
         i = i - 1
      
      entity = QadEntity()
      for layerEntitySet in entitySet.layerEntitySetList:
         # considero solo i layer vettoriali che sono modificabili
         layer = layerEntitySet.layer
         if layer.type() == QgsMapLayer.VectorLayer and layer.isEditable():
            for featureId in layerEntitySet.featureIds:
               entity.set(layer, featureId)
               self.entitySetGripPoints.addEntity(entity, QadVariables.get(QadMsg.translate("Environment variables", "GRIPS")))
      

   #============================================================================
   # INIZIO - eventi per il mouse
   #============================================================================

   
   def canvasPressEvent(self, event):
      # volevo mettere questo evento nel canvasReleaseEvent
      # ma il tasto destro non genera quel tipo di evento
      if event.button() == Qt.RightButton:
         self.displayPopupMenu(event.pos())
      elif event.button() == Qt.LeftButton:
         # verifico se tasto shift premuto
         shiftKey = True if event.modifiers() & Qt.ShiftModifier else False
         # posizione corrente del mouse
         point = self.toMapCoordinates(event.pos())
         # leggo il punto grip che si interseca alla posizione del mouse
         gripPoint = self.entitySetGripPoints.isIntersecting(point)
         if gripPoint is not None:
            if shiftKey == False: # lancio il comando
               selectedEntityGripPoints = self.entitySetGripPoints.getSelectedEntityGripPoints()
               # se non ci sono già grip selezionati
               if len(selectedEntityGripPoints) == 0:
                  # seleziono il corrente
                  if self.entitySetGripPoints.selectIntersectingGripPoints(gripPoint) > 0:
                     selectedEntityGripPoints = self.entitySetGripPoints.getSelectedEntityGripPoints()

               # lancio il comando
               self.plugIn.runCommand("QadVirtualGripCommandsClass", [self.entitySetGripPoints, gripPoint])
            else: # shift premuto
               # inverto lo stato ai grip che intersecano il punto 
               self.entitySetGripPoints.toggleSelectIntersectingGripPoints(gripPoint)
         else:
            result = qad_utils.getEntSel(event.pos(), self)
            if result is not None:
               feature = result[0]
               layer = result[1]
               tmpEntity = QadEntity()
               tmpEntity.set(layer, feature.id())
               SSGetClass = QadSSGetClass(self.plugIn)
               SSGetClass.entitySet.set(self.entitySet)
               SSGetClass.elaborateEntity(tmpEntity, shiftKey)
               self.entitySet.set(SSGetClass.entitySet)
               del SSGetClass # che deseleziona gli oggetti
               self.entitySet.selectOnLayer(False)
               self.refreshEntityGripPoints(self.entitySet)
            else:
               self.plugIn.runCommand("QadVirtualSelCommandClass", point)
               

   def canvasDoubleClickEvent(self,event):
      pass


   def canvasMoveEvent(self,event):
      point = self.toMapCoordinates(event.pos())
      self.__csrRubberBand.moveEvent(point)
      self.entitySetGripPoints.hoverIntersectingGripPoints(point)

   def canvasReleaseEvent(self, event):
      pass

   
   #============================================================================
   # FINE - eventi per il mouse
   # INIZIO - eventi per la tastiera
   #============================================================================


   def keyPressEvent(self, event):
      self.plugIn.keyPressEvent(event)


   def keyReleaseEvent(self, event):
      pass


   #============================================================================
   # FINE - eventi per la tastiera
   # INIZIO - eventi per la rotella
   #============================================================================


   def wheelEvent(self, event):
      self.__csrRubberBand.moveEvent(self.toMapCoordinates(event.pos()))


   #============================================================================
   # FINE - eventi per la rotella
   #============================================================================

   
   def activate(self):
      self.canvas.setCursor(self.cursor)
      # posizione corrente del mouse
      self.__csrRubberBand.moveEvent(self.toMapCoordinates(self.canvas.mouseLastXY()))
      self.__csrRubberBand.show()
      self.entitySet.initByCurrentQgsSelectedFeatures(self.canvas.layers())
      self.refreshEntityGripPoints(self.entitySet)

      self.plugIn.QadCommands.continueCommandFromMapTool()
   
   def deactivate(self):
      self.__csrRubberBand.hide()
      
   def isTransient(self):
      return False # questo tool non fa zoom o pan

   def isEditTool(self):
      return False # questo tool non fa editing


   #============================================================================
   # displayPopupMenu
   #============================================================================
   def displayPopupMenu(self, pos):
      popupMenu = QMenu(self.canvas)
      history = self.plugIn.getHistoryfromTxtWindow()
      isLastCmdToInsert = True
      isRecentMenuToInsert = True
      
      historyLen = len(history)
      i = historyLen - 1
      cmdInputHistoryMax = QadVariables.get(QadMsg.translate("Environment variables", "CMDINPUTHISTORYMAX"))
      while i >= 0 and (historyLen - i) <= cmdInputHistoryMax:
         cmdName = history[i]
         i = i - 1
         cmd = self.plugIn.QadCommands.getCommandObj(cmdName)
         if cmd is not None:
            if isLastCmdToInsert:
               isLastCmdToInsert = False
               msg = QadMsg.translate("Popup_menu_graph_window", "Repeat ") + cmd.getName()
               icon = cmd.getIcon()
               if icon is None:
                  lastCmdAction = QAction(msg, popupMenu)
               else:
                  lastCmdAction = QAction(icon, msg, popupMenu)
               cmd.connectQAction(lastCmdAction)      
               popupMenu.addAction(lastCmdAction)     
            else:
               if isRecentMenuToInsert:
                  isRecentMenuToInsert = False
                  recentCmdsMenu = popupMenu.addMenu(QadMsg.translate("Popup_menu_graph_window", "Recent commands"))

               icon = cmd.getIcon()
               if icon is None:
                  recentCmdAction = QAction(cmd.getName(), recentCmdsMenu)
               else:
                  recentCmdAction = QAction(icon, cmd.getName(), recentCmdsMenu)                  
               cmd.connectQAction(recentCmdAction)      
               recentCmdsMenu.addAction(recentCmdAction)
      
      if isLastCmdToInsert == False: # menu non vuoto
         popupMenu.popup(self.canvas.mapToGlobal(pos))


# Classe che gestisce il comando di selezione quando QAD è in stato di quiete
class QadVirtualSelCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadVirtualSelCommandClass(self.plugIn)
   
   def getName(self):
      return "QadVirtualSelCommandClass"

   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.SSGetClass = QadSSGetClass(plugIn)
      self.SSGetClass.entitySet.set(plugIn.tool.entitySet) # da usare solo con QadMapTool
      self.SSGetClass.exitAfterSelection = True
      self.SSGetClass.step = 1
   
   def __del__(self):
      QadCommandClass.__del__(self)
      del self.SSGetClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      return self.SSGetClass.getPointMapTool(drawMode)

   def run(self, msgMapTool = False, msg = None):
      res = self.SSGetClass.run(msgMapTool, msg)
      if res == True:
         self.plugIn.tool.entitySet.set(self.SSGetClass.entitySet) # da usare solo con QadMapTool
         self.plugIn.tool.entitySet.selectOnLayer()
      return res


#===============================================================================
# QadVirtualGripCommandsEnum class.   
#===============================================================================
class QadVirtualGripCommandsEnum():
   STRECTH = 1
   MOVE    = 2
   ROTATE  = 3
   SCALE   = 4
   MIRROR  = 5


# Classe che gestisce i comando disponibili sui grip quando QAD è in stato di quiete
class QadVirtualGripCommandsClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadVirtualGripCommandsClass(self.plugIn)
   
   def getName(self):
      return "QadVirtualGripCommandsClass"

   def __init__(self, plugIn):      
      QadCommandClass.__init__(self, plugIn)
      self.commandNum = -1
      self.currentCommand = None
      self.entitySetGripPoints = None
      self.basePt = QgsPoint()
   
   def __del__(self):
      QadCommandClass.__del__(self)
      del self.currentCommand

      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.currentCommand is not None:      
         return self.currentCommand.getPointMapTool(drawMode)
      else:
         return None


   def initNextCommand(self):
      if self.currentCommand is not None:
         del self.currentCommand
         self.currentCommand = None
         
      if self.commandNum == QadVirtualGripCommandsEnum.STRECTH:
         self.commandNum = QadVirtualGripCommandsEnum.MOVE
         self.currentCommand = QadGRIPMOVECommandClass(self.plugIn)
      elif self.commandNum == QadVirtualGripCommandsEnum.MOVE:
         self.commandNum = QadVirtualGripCommandsEnum.ROTATE
      elif self.commandNum == QadVirtualGripCommandsEnum.ROTATE:
         self.commandNum = QadVirtualGripCommandsEnum.SCALE
      elif self.commandNum == QadVirtualGripCommandsEnum.SCALE:
         self.commandNum = QadVirtualGripCommandsEnum.MIRROR
      elif self.commandNum == QadVirtualGripCommandsEnum.MIRROR or self.commandNum == -1:
         self.commandNum = QadVirtualGripCommandsEnum.STRECTH
         self.currentCommand = QadGRIPSTRETCHCommandClass(self.plugIn)
      
      if self.currentCommand is not None:
         self.currentCommand.basePt = self.basePt
         self.currentCommand.setSelectedEntityGripPoints(self.entitySetGripPoints)
         return True
      else:
         return False
         
         
   def run(self, msgMapTool = False, msg = None):
      if self.currentCommand is None:
         return True
      res = self.currentCommand.run(msgMapTool, msg)
      if res == True:
         if self.currentCommand.skipToNextGripCommand == True:
            if self.initNextCommand(): # attivo comando successivo
               return self.currentCommand.run(msgMapTool, msg)
         else:
            # ridisegno i grip point nelle nuove posizioni resettando quelli selezionati
            self.plugIn.tool.clearEntityGripPoints()
            self.plugIn.tool.refreshEntityGripPoints()

      return res

