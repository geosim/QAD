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

      
   def __del__(self):
      self.removeItems()

   def removeItems(self):      
      if self.__csrRubberBand is not None:
         self.__csrRubberBand.removeItems() # prima lo stacco dal canvas altrimenti non si rimuove perchè usato da canvas
         del self.__csrRubberBand
         __csrRubberBand = None

         
   def UpdatedVariablesEvent(self):
      # aggiorna in base alle nuove impostazioni delle variabili
      self.removeItems() 
      self.__csrRubberBand = QadCursorRubberBand(self.canvas, QadCursorTypeEnum.BOX | QadCursorTypeEnum.CROSS)
      

   #============================================================================
   # INIZIO - eventi per il mouse
   #============================================================================

   
   def canvasPressEvent(self, event):
      # volevo mettere questo evento nel canvasReleaseEvent
      # ma il tasto destro non genera quel tipo di evento
      if event.button() == Qt.RightButton:
         self.displayPopupMenu(event.pos())
      elif event.button() == Qt.LeftButton:
         pass

   def canvasDoubleClickEvent(self,event):
      pass


   def canvasMoveEvent(self,event):
      self.__csrRubberBand.moveEvent(self.toMapCoordinates(event.pos()))


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
      self.__csrRubberBand.show()
      self.plugIn.QadCommands.continueCommandFromMapTool()
   
   def deactivate(self):
      self.__csrRubberBand.hide()
      
   def isTransient(self):
      return False

   def isEditTool(self):
      return True


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
         