# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comandi di editazione geometria stile CAD
 
                              -------------------
        begin                : 2013-04-17
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
# Initialize Qt resources from file resources.py
import resources
import math

import qad_debug
import qad_utils
from qad_maptool import QadMapTool
from qad_variables import *
from qad_textwindow import *
from qad_commands import *
from qad_entity import *

class Qad:
   """
   Classe plug in di Qad
   """

   # Map Tool attivo. Quando non ci sono comandi che necessitano di input dalla finestra grafica
   # QadMapTool è quello attivo 
   tool = None
   # Finestra grafica
   canvas = None
   # Finestra testuale
   TextWindow = None
   # Classe che gestisce i comandi
   QadCommands = None
   # Azione corrente
   currentAction = None
   # Finestra testuale già collegata
   __alreadyDockedTextWindow = False
   # ultimo punto selezionato
   lastPoint = None
   # coeff angolare ultimo segmento
   lastSegmentAng = 0.0
   # ultima rotazione
   lastRot = 0.0
   # ultimo angolo di riferimento (es. comando ruota)
   lastReferenceRot = 0.0
   # ultimo nuovo angolo di riferimento (es. comando ruota)
   lastNewReferenceRot = 0.0
   # ultimo raggio
   lastRadius = 0.0
   # ultimo punto di offset
   lastOffsetPt = QgsPoint(0, 0)
   # ultima lunghezza di riferimento (es. comando scala)
   lastReferenceLen = 1.0
   # ultima lunghezza di riferimento (es. comando scala)
   lastNewReferenceLen = 1.0
   # ultimo fattore di scala (es. comando scala)
   lastScale = 1.0
   # numero di segmenti per l'approssimazione delle curve (es. buffer)
   segments = 10
   # ultima entità inserita
   lastEntity = None
   # ultimo set di entità
   lastEntitySet = None
   
   def setLastPointAndSegmentAng(self, point, segmentAng = None):
      # memorizzo il coeff angolare ultimo segmento e l'ultimo punto selezionato
      if segmentAng is None:         
         if self.lastPoint is not None:         
            self.setLastSegmentAng(qad_utils.getAngleBy2Pts(self.lastPoint, point))
      else:
         self.setLastSegmentAng(segmentAng)         
      self.setLastPoint(point)

   def setLastPoint(self, point):
      # memorizzo l'ultimo punto selezionato         
      self.lastPoint = point

   def setLastSegmentAng(self, segmentAng):
      # memorizzo il coeff angolare ultimo segmento
      self.lastSegmentAng = qad_utils.normalizeAngle(segmentAng)         
   
   def setLastRot(self, rot):
      # memorizzo l'ultima rotazione in radianti
      self.lastRot = qad_utils.normalizeAngle(rot)

   def setLastReferenceRot(self, rot):
      # memorizzo l'ultimo angolo di riferimento (es. comando ruota) in radianti
      self.lastReferenceRot = qad_utils.normalizeAngle(rot)

   def setLastNewReferenceRot(self, rot):
      # memorizzo l'ultimo nuovo angolo di riferimento (es. comando ruota) in radianti
      self.lastNewReferenceRot = qad_utils.normalizeAngle(rot)
   
   def setLastRadius(self, radius):
      # memorizzo l'ultimo raggio
      if radius > 0:
         self.lastRadius = radius      

   def setLastOffsetPt(self, offSetPt):
      # memorizzo l'ultimo punto di offset
      # la x del punto rappresenta l'offset X
      # la y del punto rappresenta l'offset Y
      self.lastOffsetPt.set(offSetPt.x(), offSetPt.y())

   def setLastReferenceLen(self, length):
      # memorizzo l'ultima lunghezza di riferimento (es. comando scale)
      self.lastReferenceLen = length

   def setLastNewReferenceRot(self, length):
      # memorizzo l'ultima nuova lunghezza di riferimento (es. comando scale)
      self.lastNewReferenceLen = length
   
   def setLastScale(self, scale):
      # memorizzo l'ultimo fattore di scala
      if scale > 0:
         self.lastScale = scale      

   def setNSegmentsToApproxCurve(self, segments):
      # memorizzo il numero di segmenti per l'approssimazione delle curve (es. buffer)
      if segments > 1:
         self.segments = int(segments)      

   def setLastEntity(self, layer, featureId):
      # memorizzo l'ultimo entità creata
      if self.lastEntity is None:
         self.lastEntity = QadEntity()
      self.lastEntity.set(layer, featureId)
   
   def getLastEntity(self):
      if self.lastEntity is None:
         return None
      else:
         if self.lastEntity.exists() == False: # non esiste più
            return None
         else:
            return self.lastEntity
      
   def setLastEntitySet(self, entitySet):
      # memorizzo l'ultimo set di entità
      if self.lastEntitySet is None:
         self.lastEntitySet = QadEntitySet()
      self.lastEntitySet.set(entitySet)
      
   def __init__(self, iface):
      QadVariables.load()

      # Save reference to the QGIS interface
      self.iface = iface
      self.canvas = self.iface.mapCanvas()
      self.tool = QadMapTool(self)

      self.QadCommands = QadCommandsClass(self)

   def initGui(self):
      
      # Create action that will start plugin configuration
      self.mainAction = QAction(QIcon(":/plugins/qad/icons/qad.png"), \
                                "QAD", self.iface.mainWindow())
      self.mainAction.setCheckable(True)
      
      # Creo le azioni per i comandi e le collego ai segnali che arrivano dai bottoni
      # PLINE
      cmd = self.QadCommands.getCommandObj(QadMsg.get(35)) # "PLINEA"
      self.pline_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow()) 
      cmd.connectQAction(self.pline_action)
      # SETCURRLAYERBYGRAPH
      cmd = self.QadCommands.getCommandObj(QadMsg.get(49)) # "SETCURRLAYERDAGRAFICA"
      self.setCurrLayerByGraph_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.setCurrLayerByGraph_action)
      # SETCURRUPDATEABLELAYERBYGRAPH
      cmd = self.QadCommands.getCommandObj(QadMsg.get(74)) # "SETCURRMODIFLAYERDAGRAFICA"
      self.setCurrUpdateableLayerByGraph_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.setCurrUpdateableLayerByGraph_action)
      # ARC
      cmd = self.QadCommands.getCommandObj(QadMsg.get(54)) # "ARCO"
      self.arc_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.arc_action)
      # CIRCLE
      cmd = self.QadCommands.getCommandObj(QadMsg.get(76)) # "CERCHIO"
      self.circle_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.circle_action)
      # DSETTINGS
      cmd = self.QadCommands.getCommandObj(QadMsg.get(111)) # "IMPOSTADIS"
      self.dsettings_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.dsettings_action)
      # LINE
      cmd = self.QadCommands.getCommandObj(QadMsg.get(117)) # "LINEA"
      self.line_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.line_action)
      # ERASE
      cmd = self.QadCommands.getCommandObj(QadMsg.get(129)) # "CANCELLA"
      self.erase_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.erase_action)
      # MPOLYGON
      cmd = self.QadCommands.getCommandObj(QadMsg.get(166)) # "MPOLYGON"
      self.mpolygon_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.mpolygon_action)
      # MBUFFER
      cmd = self.QadCommands.getCommandObj(QadMsg.get(169)) # "MBUFFER"
      self.mbuffer_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.mbuffer_action)
      # ROTATE
      cmd = self.QadCommands.getCommandObj(QadMsg.get(179)) # "ROTATE"
      self.rotate_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.rotate_action)
      # MOVE
      cmd = self.QadCommands.getCommandObj(QadMsg.get(189)) # "SPOSTA"
      self.move_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.move_action)
      # SCALE
      cmd = self.QadCommands.getCommandObj(QadMsg.get(195)) # "SCALA"
      self.scale_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.scale_action)
      # COPY
      cmd = self.QadCommands.getCommandObj(QadMsg.get(202)) # "COPIA"
      self.copy_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.copy_action)
      # OFFSET
      cmd = self.QadCommands.getCommandObj(QadMsg.get(221)) # "OFFSET"
      self.offset_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      cmd.connectQAction(self.offset_action)

      # Connect to signals for button behaviour.
      QObject.connect(self.mainAction, SIGNAL("triggered()"), self.run)
      QObject.connect(self.canvas, SIGNAL("mapToolSet(QgsMapTool*)"), self.deactivate)
            
      
      # Add menu         
      self.menu = QMenu()
      self.menu.setTitle("QAD")

      self.menu.addAction(self.mainAction)
            
      self.menu.addAction(self.pline_action)
      self.menu.addAction(self.setCurrLayerByGraph_action)
      self.menu.addAction(self.setCurrUpdateableLayerByGraph_action)
      self.menu.addAction(self.arc_action)
      self.menu.addAction(self.circle_action)
      self.menu.addAction(self.dsettings_action)
      self.menu.addAction(self.line_action)
      self.menu.addAction(self.erase_action)
      self.menu.addAction(self.mpolygon_action)
      self.menu.addAction(self.mbuffer_action)
      self.menu.addAction(self.rotate_action)
      self.menu.addAction(self.move_action)
      self.menu.addAction(self.scale_action)
      self.menu.addAction(self.copy_action)
      self.menu.addAction(self.offset_action)

      menu_bar = self.iface.mainWindow().menuBar()
      actions = menu_bar.actions()
      lastAction = actions[ len( actions ) - 1 ]
      menu_bar.insertMenu(lastAction, self.menu )
      
      # aggiunge le toolbar 
      self.toolBar = self.iface.addToolBar("QAD")
      self.toolBar.setObjectName("QAD")
      self.toolBar.addAction(self.mainAction)

      # aggiunge le toolbar per i comandi 
      self.toolBar.addAction(self.pline_action)
      self.toolBar.addAction(self.setCurrLayerByGraph_action)
      self.toolBar.addAction(self.setCurrUpdateableLayerByGraph_action)
      self.toolBar.addAction(self.arc_action)
      self.toolBar.addAction(self.circle_action)
      self.toolBar.addAction(self.dsettings_action)
      self.toolBar.addAction(self.line_action)
      self.toolBar.addAction(self.erase_action)
      self.toolBar.addAction(self.mpolygon_action)      
      self.toolBar.addAction(self.mbuffer_action)      
      self.toolBar.addAction(self.rotate_action)      
      self.toolBar.addAction(self.move_action)      
      self.toolBar.addAction(self.scale_action)      
      self.toolBar.addAction(self.copy_action)      
      self.toolBar.addAction(self.offset_action)

      # Inizializzo la finestra di testo
      self.TextWindow = QadTextWindow(self)
      self.TextWindow.initGui()
      self.showTextWindow(QadVariables.get("SHOWTEXTWINDOW", False))
            
      self.setStandardMapTool()

   def run(self):
      self.setStandardMapTool()
      self.showTextWindow()

   def deactivate(self):
      self.mainAction.setChecked(False)

   def unload(self):
      # Remove the plugin menu item and icon
      self.iface.removePluginMenu("&QAD", self.mainAction)
      self.iface.removeToolBarIcon(self.mainAction)
      # remove toolbar and menubar
      del self.toolBar
      del self.menu

   def setStandardMapTool(self):
      mc = self.canvas
      mc.setMapTool(self.tool)
      self.mainAction.setChecked(True)

   def keyPressEvent(self, event):
      self.TextWindow.keyPressEvent(event)
      pass

      
   #============================================================================
   # INIZIO - funzioni per visualizzare messaggi nella finestra di testo 
   #============================================================================
   def showTextWindow(self, mode = True):
      if mode == True:
         if self.__alreadyDockedTextWindow == False:
            self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.TextWindow)
            self.__alreadyDockedTextWindow = True

      self.TextWindow.setVisible(mode)
      if mode == True:
         self.TextWindow.setFocus()

   def showMsg(self, msg, displayPrompt = False):
      self.TextWindow.showMsg(msg, displayPrompt)
      
   def showErr(self, err):
      self.TextWindow.showErr(err)

   def showInputMsg(self, inputMsg = QadMsg.get(0), inputType = QadInputTypeEnum.COMMAND, \
                    default = None, keyWords = "", inputMode = QadInputModeEnum.NOT_NULL):
      
      self.TextWindow.showInputMsg(inputMsg, inputType, default, keyWords, inputMode)

   
   #============================================================================
   # INIZIO - funzioni per comandi 
   #============================================================================
   def runCommand(self, command):
      self.QadCommands.run(command)
   
   def continueCommandFromMapTool(self):
      self.QadCommands.continueCommandFromMapTool()

   def continueCommandFromTextWindow(self, msg):
      self.QadCommands.continueCommandFromTextWindow(msg)

   def abortCommand(self):
      self.QadCommands.abortCommand()
      
   def isValidCommand(self, command):
      upperCommand = command.upper()
      return upperCommand in self.QadCommands.commands

   def getCommandNames(self):
      return self.QadCommands.commands
   
   def getCommandObj(self, cmdName):
      return self.QadCommands.getCommandObj(cmdName)
   
   def forceCommandMapToolSnapTypeOnce(self, snapType, snapParams = None):
      self.QadCommands.forceCommandMapToolSnapTypeOnce(snapType, snapParams)
   
   def getCurrenPointFromCommandMapTool(self):
      return self.QadCommands.getCurrenPointFromCommandMapTool()
   
   def toggleOsMode(self):
      value = QadVariables.get("OSMODE")
      if value & QadSnapTypeEnum.DISABLE:
         value =  value - QadSnapTypeEnum.DISABLE
         msg = QadMsg.get(46) # "\n<Snap attivato>"
      else:
         value =  value + QadSnapTypeEnum.DISABLE
         msg = QadMsg.get(45) # "\n<Snap disattivato>"

      QadVariables.set("OSMODE", value)
      QadVariables.save()
      self.showMsg(msg, True)        
      self.QadCommands.refreshCommandMapToolSnapType()

   def toggleOrthoMode(self):
      value = QadVariables.get("ORTHOMODE")
      if value == 0:
         value = 1
         autosnap = QadVariables.get("AUTOSNAP")
         if (autosnap & 8) == True:
            QadVariables.set("AUTOSNAP", autosnap - 8) # disattivo la modalità polare 
         msg = QadMsg.get(47) # "\n<Modalità ortogonale attivata>"
      else:
         value = 0
         msg = QadMsg.get(48) # "\n<Modalità ortogonale disattivata>"

      QadVariables.set("ORTHOMODE", value)
      QadVariables.save()
      self.showMsg(msg, True)        
      self.QadCommands.refreshCommandMapToolOrthoMode()

   def togglePolarMode(self):
      value = QadVariables.get("AUTOSNAP")
      if (value & 8) == False:
         value = value + 8
         QadVariables.set("ORTHOMODE", 0) # disattivo la modalità orto 
         msg = QadMsg.get(115) # "\n<Modalità polare attivata>"
      else:
         value = value - 8
         msg = QadMsg.get(116) # "\n<Modalità polare disattivata>"

      QadVariables.set("AUTOSNAP", value)
      QadVariables.save()
      self.showMsg(msg, True)        
      self.QadCommands.refreshCommandMapToolAutoSnap()
   
   def getCurrMsgFromTxtWindow(self):
      return self.TextWindow.getCurrMsg()

   def getHistoryfromTxtWindow(self):
      return self.TextWindow.getHistory() # QStringList

   def showEvaluateMsg(self, msg = None):
      self.TextWindow.showEvaluateMsg(msg)
      
   #============================================================================
   # funzioni per l'avvio di un comando
   #============================================================================
   def runCommandAbortingTheCurrent(self, cmdName):
      #qad_debug.breakPoint()
      self.canvas.setFocus()
      self.abortCommand()
      self.showEvaluateMsg(cmdName)
      
   def runIDCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(3)) # "ID"
   
   def runSETVARCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(6)) # "MODIVAR"

   def runPLINECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(35)) # "PLINEA"
      
   def runSETCURRLAYERBYGRAPHCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(49)) # "SETCURRLAYERDAGRAFICA"

   def runSETCURRUPDATEABLELAYERBYGRAPHCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(74)) # "SETCURRMODIFLAYERDAGRAFICA"
      
   def runARCCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(54)) # "ARCO"
      
   def runCIRCLECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(76)) # "CERCHIO"
      
   def runDSETTINGSCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(111)) # "IMPOSTADIS"
      
   def runLINECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(117)) # "LINEA"
      
   def runERASECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(129)) # "CANCELLA"
      
   def runMPOLYGONCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(166)) # "MPOLYGON"
      
   def runMBUFFERCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(169)) # "MBUFFER"
      
   def runROTATECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(179)) # "ROTATE"
      
   def runMOVECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(189)) # "SPOSTA"
      
   def runSCALECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(195)) # "SCALA"
      
   def runCOPYCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(202)) # "COPIA"
      
   def runOFFSETCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.get(221)) # "OFFSET"
      