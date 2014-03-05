# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 map tool per lo stato di quiete
 
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


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *


import qad_debug
import qad_utils
from qad_variables import *
from qad_msg import QadMsg


# Main Map Tool class.
class QadMapTool(QgsMapTool):
      
   def __init__(self, plugIn):        
      QgsMapTool.__init__(self, plugIn.iface.mapCanvas())
      self.plugIn = plugIn
      self.iface = self.plugIn.iface
      self.canvas = self.plugIn.iface.mapCanvas()      
      self.cursor = qad_utils.getGetPointCursor()
      self.popupMenu = None


   #============================================================================
   # INIZIO - eventi per il mouse
   #============================================================================

   
   def canvasPressEvent(self, event):
      # volevo mettere questo evento nel canvasReleaseEvent
      # ma il tasto destro non genera quel tipo di evento
      if event.button() == Qt.RightButton:
         self.displayPopupMenu(event.pos())                  


   def canvasDoubleClickEvent(self,event):
      pass


   def canvasMoveEvent(self,event):
      pass


   def canvasReleaseEvent(self,event):
      pass

   
   #============================================================================
   # FINE - eventi per il mouse
   # INIZIO - eventi per la tastiera
   #============================================================================


   def keyPressEvent(self, event):
      #qad_debug.breakPoint() 
      self.plugIn.keyPressEvent(event)


   def keyReleaseEvent(self,event):
      pass


   #============================================================================
   # FINE - eventi per la tastiera
   # INIZIO - eventi per la rotella
   #============================================================================


   def wheelEvent(self,event):
      pass


   #============================================================================
   # FINE - eventi per la rotella
   #============================================================================

   
   def activate(self):
      self.canvas.setCursor(self.cursor)
      self.plugIn.QadCommands.continueCommandFromMapTool()
   
   def deactivate(self):
      if self.popupMenu is not None:
         #qad_debug.breakPoint()
         self.popupMenu.clear()
         del self.popupMenu
         self.popupMenu = None
      pass
      
   def isTransient(self):
      return False

   def isEditTool(self):
      return True


   #============================================================================
   # dispalyPopupMenu
   #============================================================================
   def displayPopupMenu(self, pos):
      #qad_debug.breakPoint()
      self.popupMenu = QMenu()
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
               msg = QadMsg.translate("Popup_menu_graph_window", "Ripeti ") + cmd.getName() # "Ripeti "
               icon = cmd.getIcon()
               if icon is None:
                  lastCmdAction = QAction(msg, self.popupMenu)
               else:
                  lastCmdAction = QAction(cmd.getIcon(), msg, self.popupMenu)
               cmd.connectQAction(lastCmdAction)      
               self.popupMenu.addAction(lastCmdAction)     
            else:
               if isRecentMenuToInsert:
                  isRecentMenuToInsert = False
                  recentCmdsMenu = self.popupMenu.addMenu(QadMsg.translate("Popup_menu_graph_window", "Comandi recenti "))

               icon = cmd.getIcon()
               if icon is None:
                  recentCmdAction = QAction(cmd.getName(), recentCmdsMenu)
               else:
                  recentCmdAction = QAction(cmd.getIcon(), cmd.getName(), recentCmdsMenu)                  
               cmd.connectQAction(recentCmdAction)      
               recentCmdsMenu.addAction(recentCmdAction)
      
      if isLastCmdToInsert == False: # menu non vuoto
         self.popupMenu.popup(self.plugIn.iface.mapCanvas().mapToGlobal(pos))
         
