# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comandi di editazione geometria stile CAD
 
                              -------------------
        begin                : 2014-11-03
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
# Initialize Qt resources from file qad_rc.py
import qad_rc
import math


import qad_utils
from qad_maptool import QadMapTool
from qad_variables import *
from qad_dim import *
from qad_textwindow import *
from qad_commands import *
from qad_entity import *
import qad_layer
import qad_undoredo

class Qad(QObject):
   """
   Classe plug in di Qad
   """

   # UI
   toolBar = None
   dimToolBar = None
   menu = None
   translator = None

   
   # Map Tool attivo. Quando non ci sono comandi che necessitano di input dalla finestra grafica
   # QadMapTool é quello attivo 
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
   # ultima altezza testo
   lastHText = 1.0
   # ultimo angolo di riferimento (es. comando ruota)
   lastReferenceRot = 0.0
   # ultimo nuovo angolo di riferimento (es. comando ruota)
   lastNewReferenceRot = 0.0
   # ultimo raggio
   lastRadius = 1.0
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
   # tipo di unione (es. editpl->unione)
   joinMode = 1 # 1=Estendi, 2=Aggiungi, 3=Entrambi
   # distanza di approssimazione nell'unione (es. editpl->unione)
   joinToleranceDist = 0.0
   # modalità di raccordo in comando raccordo
   filletMode = 1 # 1=Taglia-estendi, 2=Non taglia-estendi
   # ultimo numero di lati per poligono
   lastPolygonSideNumber = 4
   # ultima opzione di costruzione del poligono conoscendo il centro
   # "Inscritto nel cerchio", Circoscritto intorno al cerchio", "Area"
   lastPolygonConstructionModeByCenter = QadMsg.translate("Command_POLYGON", "Inscritto nel cerchio")


   # flag per identificare se un comando di QAD é attivo oppure no
   isQadActive = False
   
   # Quotatura
   dimStyles = QadDimStyles()                 # lista degli stili di quotatura caricati
   dimTextEntitySetRecodeOnSave = QadLayerEntitySet() # entity set dei testi delle quote da riallineare in salvataggio
   beforeCommitChangesDimLayer = None         # layer da cui é scaturito il salvataggio delle quotature
   isSaveControlledByQAD = False
   
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
   
   def setLastHText(self, hText):
      # memorizzo l'ultima altezza testo
      if hText > 0:
         self.lastHText = hText

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

   def setJoinMode(self, joinMode):
      # memorizzo tipo di unione (es. editpl->unione); 1=Estendi, 2=Aggiungi, 3=Entrambi
      if joinMode == 1 or joinMode == 2 or joinMode == 3:
         self.joinMode = int(joinMode)     

   def setJoinToleranceDist(self, joinToleranceDist):
      # memorizzo la distanza di approssimazione nell'unione (es. editpl->unione)
      if joinToleranceDist >= 0:
         self.joinToleranceDist = joinToleranceDist      

   def setFilletMode(self, filletMode):
      # memorizzo modalità di raccordo in comando raccordo; 1=Taglia-estendi, 2=Non taglia-estendi
      if filletMode == 1 or filletMode == 2:
         self.filletMode = int(filletMode)     

   def setLastPolygonSideNumber(self, polygonSideNumber):
      # memorizzo l'ultimo numero di lati del poligono
      if polygonSideNumber > 2:
         self.lastPolygonSideNumber = polygonSideNumber

   def setLastPolygonConstructionModeByCenter(self, mode):
      # memorizzo ultima opzione di costruzione del poligono conoscendo il centro
      # "Inscritto nel cerchio", Circoscritto intorno al cerchio", "Area"
      self.lastPolygonConstructionModeByCenter = mode


   def loadDimStyles(self):
      # carico gli stili di quotatura
      self.dimStyles.load()
      
   #============================================================================
   # __initLocalization
   #============================================================================
   # inizializza la localizzazione delle traduzioni e dell'help in linea
   def __initLocalization(self, locale):     
      localePath = os.path.join(self.plugin_dir, 'i18n', 'qad_{}.qm'.format(locale))

      if os.path.exists(localePath):
         self.translator = QTranslator()
         self.translator.load(localePath)
         if qVersion() > '4.3.3':
            QCoreApplication.installTranslator(self.translator)
         return True
      else:
         return False
      
   
   #============================================================================
   # __init__
   #============================================================================
   def __init__(self, iface):
      
      QObject.__init__(self)      
      
      # Save reference to the QGIS interface
      self.iface = iface
      
      # initialize plugin directory
      self.plugin_dir = os.path.dirname(__file__)
      
      # initialize locale
      userLocaleList = QSettings().value("locale/userLocale").split("_")
      language = userLocaleList[0]
      region = userLocaleList[1] if len(userLocaleList) > 1 else ""
      # if not italian
      if language.upper() != "IT":
         # provo a caricare la lingua e la regione selezionate
         if self.__initLocalization(language + "_" + region) == False:
            # provo a caricare la lingua
            if self.__initLocalization(language) == False:            
               # provo a caricare la lingua inglese
               self.__initLocalization("en")
                        
      # carico le variabili d'ambiente
      QadVariables.load()
      # carico gli stili di quotatura
      self.loadDimStyles()

      self.canvas = self.iface.mapCanvas()
      self.tool = QadMapTool(self)
      
      # Lista dei comandi
      self.QadCommands = QadCommandsClass(self)
      # Gestore di Undo/Redo
      self.undoStack = qad_undoredo.QadUndoStack()

   def initGui(self):
      # creo tutte le azioni e le collego ai comandi
      self.initActions()

      # Connect to signals
      QObject.connect(self.canvas, SIGNAL("mapToolSet(QgsMapTool*)"), self.deactivate)            
      
      # Add menu    
      self.menu = QMenu(QadMsg.translate("QAD", "QAD"))
      self.menu.addAction(self.mainAction)

      self.menu.addAction(self.u_action)
      self.menu.addAction(self.undo_action)
      self.menu.addAction(self.redo_action)

      # crea il menu Draw
      self.drawMenu = self.createDrawMenu()
      self.menu.addMenu(self.drawMenu)

      # menu Edit            
      self.editMenu = self.createEditMenu()
      self.menu.addMenu(self.editMenu)

      # menu Tools            
      self.toolsMenu = self.createToolsMenu()
      self.menu.addMenu(self.toolsMenu)

      # menu Dim            
      self.dimMenu = self.createDimMenu()
      self.menu.addMenu(self.dimMenu)
      
      # aggiunge il menu al menu vector di QGIS
      self.iface.vectorMenu().addMenu(self.menu)
      
#       menu_bar = self.iface.mainWindow().menuBar()
#       actions = menu_bar.actions()
#       lastAction = actions[ len( actions ) - 1 ]
#       menu_bar.insertMenu(lastAction, self.menu )
      
      # aggiunge le toolbar
      self.toolBar = self.iface.addToolBar("QAD")
      self.toolBar.setObjectName("QAD")
      self.toolBar.addAction(self.mainAction)

      # aggiunge le toolbar per i comandi 
      self.toolBar.addAction(self.setCurrLayerByGraph_action)
      self.toolBar.addAction(self.setCurrUpdateableLayerByGraph_action)
      self.toolBar.addAction(self.u_action)
      self.toolBar.addAction(self.redo_action)
      self.toolBar.addAction(self.line_action)
      self.toolBar.addAction(self.pline_action)
      # arco
      self.arcToolButton = self.createArcToolButton()
      self.toolBar.addWidget(self.arcToolButton)
      # cerchio
      self.circleToolButton = self.createCircleToolButton()
      self.toolBar.addWidget(self.circleToolButton)

      self.toolBar.addAction(self.rectangle_action)
      self.toolBar.addAction(self.polygon_action)
      self.toolBar.addAction(self.mpolygon_action)
      self.toolBar.addAction(self.mbuffer_action)
      self.toolBar.addAction(self.insert_action)
      self.toolBar.addAction(self.text_action)
            
      self.toolBar.addAction(self.erase_action)
      self.toolBar.addAction(self.rotate_action)
      self.toolBar.addAction(self.move_action)
      self.toolBar.addAction(self.scale_action)
      self.toolBar.addAction(self.copy_action)
      self.toolBar.addAction(self.offset_action)
      self.toolBar.addAction(self.extend_action)
      self.toolBar.addAction(self.trim_action)
      self.toolBar.addAction(self.mirror_action)
      self.toolBar.addAction(self.stretch_action)
      self.toolBar.addAction(self.break_action)
      self.toolBar.addAction(self.pedit_action)
      self.toolBar.addAction(self.fillet_action)
      self.toolBar.addAction(self.dsettings_action)
      self.enableUndoRedoButtons()

      # aggiunge la toolbar per la quotatura 
      self.dimToolBar = self.createDimToolBar()
      
      # Inizializzo la finestra di testo
      self.TextWindow = QadTextWindow(self)
      self.TextWindow.initGui()
      self.showTextWindow(QadVariables.get(QadMsg.translate("Environment variables", "SHOWTEXTWINDOW"), True))
            
      self.setStandardMapTool()

      # aggiungo i segnali di aggiunta e rimozione di layer per collegare ogni layer
      # all'evento <layerModified> per sapere se la modifica fatta su quel layer
      # é stata fatta da QAD o dall'esterno
      QObject.connect(QgsMapLayerRegistry.instance(), SIGNAL("layerWasAdded(QgsMapLayer *)"), self.layerAdded)
      QObject.connect(QgsMapLayerRegistry.instance(), SIGNAL("layerWillBeRemoved(QString)"), self.removeLayer)


   def unload(self):
      # Disconnect to signals
      QObject.disconnect(self.canvas, SIGNAL("mapToolSet(QgsMapTool*)"), self.deactivate)            
      QObject.disconnect(QgsMapLayerRegistry.instance(), SIGNAL("layerWasAdded(QgsMapLayer *)"), self.layerAdded)
      QObject.disconnect(QgsMapLayerRegistry.instance(), SIGNAL("layerWillBeRemoved(QString)"), self.removeLayer)
      
      # Remove the plugin menu item and icon
      self.iface.removePluginVectorMenu("&QAD", self.mainAction)
      self.iface.removeToolBarIcon(self.mainAction)
      
      # remove toolbars and menubars
      if self.toolBar is not None:
         del self.toolBar
      if self.dimToolBar is not None:
         del self.dimToolBar
      if self.menu is not None:
         del self.menu
      if self.TextWindow is not None:
         self.TextWindow.close()
      if self.tool:
         del self.tool


   #============================================================================
   # INIZIO - Gestione ACTION (da chiamare prima di creare MENU e TOOLBAR) 
   #============================================================================
   def initActions(self):
      # Creo le azioni e le collego ai comandi
      
      self.mainAction = QAction(QIcon(":/plugins/qad/icons/qad.png"), \
                                QadMsg.translate("QAD", "QAD"), self.iface.mainWindow())      
      self.mainAction.setCheckable(True)
      QObject.connect(self.mainAction, SIGNAL("triggered()"), self.run)
      
      # PLINE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "PLINEA"))
      self.pline_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.pline_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.pline_action)
      
      # SETCURRLAYERBYGRAPH
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "SETCURRLAYERDAGRAFICA"))
      self.setCurrLayerByGraph_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.setCurrLayerByGraph_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.setCurrLayerByGraph_action)
      # SETCURRUPDATEABLELAYERBYGRAPH
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "SETCURRMODIFLAYERDAGRAFICA"))
      self.setCurrUpdateableLayerByGraph_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.setCurrUpdateableLayerByGraph_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.setCurrUpdateableLayerByGraph_action)
            
      # ARC
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "ARCO"))
      self.arc_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.arc_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.arc_action)
      # ARC BY 3 POINTS (MACRO)
      self.arcBy3Points_action = QAction(QIcon(":/plugins/qad/icons/arcBy3Points.png"), \
                                         QadMsg.translate("Command_ARC", "Arco passante per 3 punti"), \
                                         self.iface.mainWindow())
      QObject.connect(self.arcBy3Points_action, SIGNAL("triggered()"), self.runARCBY3POINTSCommand)
      # ARC BY START CENTER END POINTS (MACRO)
      self.arcByStartCenterEndPoints_action = QAction(QIcon(":/plugins/qad/icons/arcByStartCenterEndPoints.png"), \
                                                      QadMsg.translate("Command_ARC", "Arco definito da un punto iniziale, centrale e finale"), \
                                                      self.iface.mainWindow())
      QObject.connect(self.arcByStartCenterEndPoints_action, SIGNAL("triggered()"), self.runARC_BY_START_CENTER_END_Command)
      # ARC BY START CENTER ANGLE (MACRO)
      self.arcByStartCenterAngle_action = QAction(QIcon(":/plugins/qad/icons/arcByStartCenterAngle.png"), \
                                                  QadMsg.translate("Command_ARC", "Arco definito da un punto iniziale, centrale e angolo"), \
                                                  self.iface.mainWindow())
      QObject.connect(self.arcByStartCenterAngle_action, SIGNAL("triggered()"), self.runARC_BY_START_CENTER_ANGLE_Command)
      # ARC BY START CENTER LENGTH (MACRO)
      self.arcByStartCenterLength_action = QAction(QIcon(":/plugins/qad/icons/arcByStartCenterLength.png"), \
                                                   QadMsg.translate("Command_ARC", "Arco definito da un punto iniziale, centrale e lunghezza corda"), \
                                                   self.iface.mainWindow())
      QObject.connect(self.arcByStartCenterLength_action, SIGNAL("triggered()"), self.runARC_BY_START_CENTER_LENGTH_Command)
      # ARC BY START END ANGLE (MACRO)
      self.arcByStartEndAngle_action = QAction(QIcon(":/plugins/qad/icons/arcByStartEndAngle.png"), \
                                               QadMsg.translate("Command_ARC", "Arco definito da un punto iniziale, finale e angolo"), \
                                               self.iface.mainWindow())
      QObject.connect(self.arcByStartEndAngle_action, SIGNAL("triggered()"), self.runARC_BY_START_END_ANGLE_Command)
      # ARC BY START END TAN (MACRO)
      self.arcByStartEndTan_action = QAction(QIcon(":/plugins/qad/icons/arcByStartEndTan.png"), \
                                               QadMsg.translate("Command_ARC", "Arco definito da un punto iniziale, finale e direzione tangente"), \
                                               self.iface.mainWindow())
      QObject.connect(self.arcByStartEndTan_action, SIGNAL("triggered()"), self.runARC_BY_START_END_TAN_Command)
      # ARC BY START END RADIUS (MACRO)
      self.arcByStartEndRadius_action = QAction(QIcon(":/plugins/qad/icons/arcByStartEndRadius.png"), \
                                               QadMsg.translate("Command_ARC", "Arco definito da un punto iniziale, finale e raggio"), \
                                               self.iface.mainWindow())
      QObject.connect(self.arcByStartEndRadius_action, SIGNAL("triggered()"), self.runARC_BY_START_END_RADIUS_Command)
      # ARC BY CENTER START END (MACRO)
      self.arcByCenterStartEnd_action = QAction(QIcon(":/plugins/qad/icons/arcByCenterStartEnd.png"), \
                                                QadMsg.translate("Command_ARC", "Arco definito da un punto centrale, iniziale e finale"), \
                                                self.iface.mainWindow())
      QObject.connect(self.arcByCenterStartEnd_action, SIGNAL("triggered()"), self.runARC_BY_CENTER_START_END_Command)
      # ARC BY CENTER START ANGLE (MACRO)
      self.arcByCenterStartAngle_action = QAction(QIcon(":/plugins/qad/icons/arcByCenterStartAngle.png"), \
                                                  QadMsg.translate("Command_ARC", "Arco definito da un punto centrale, iniziale e angolo"), \
                                                  self.iface.mainWindow())
      QObject.connect(self.arcByCenterStartAngle_action, SIGNAL("triggered()"), self.runARC_BY_CENTER_START_ANGLE_Command)
      # ARC BY CENTER START LENGTH (MACRO)
      self.arcByCenterStartLength_action = QAction(QIcon(":/plugins/qad/icons/arcByCenterStartLength.png"), \
                                                   QadMsg.translate("Command_ARC", "Arco definito da un punto centrale, iniziale e lunghezza corda"), \
                                                   self.iface.mainWindow())
      QObject.connect(self.arcByCenterStartLength_action, SIGNAL("triggered()"), self.runARC_BY_CENTER_START_LENGTH_Command)
      
      # CIRCLE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "CERCHIO"))
      self.circle_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.circle_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.circle_action)
      # CIRCLE BY CENTER RADIUS (MACRO)
      self.circleByCenterRadius_action = QAction(QIcon(":/plugins/qad/icons/circleByCenterRadius.png"), \
                                                 QadMsg.translate("Command_CIRCLE", "Cerchio definito da un punto centrale e un raggio"), \
                                                 self.iface.mainWindow())
      QObject.connect(self.circleByCenterRadius_action, SIGNAL("triggered()"), self.runCIRCLE_BY_CENTER_RADIUS_Command)
      # CIRCLE BY CENTER DIAMETER (MACRO)
      self.circleByCenterDiameter_action = QAction(QIcon(":/plugins/qad/icons/circleByCenterDiameter.png"), \
                                                   QadMsg.translate("Command_CIRCLE", "Cerchio definito da un punto centrale e un diametro"), \
                                                   self.iface.mainWindow())
      QObject.connect(self.circleByCenterDiameter_action, SIGNAL("triggered()"), self.runCIRCLE_BY_CENTER_DIAMETER_Command)
      # CIRCLE BY 2 POINTS (MACRO)
      self.circleBy2Points_action = QAction(QIcon(":/plugins/qad/icons/circleBy2Points.png"), \
                                            QadMsg.translate("Command_CIRCLE", "Cerchio definito da 2 punti"), \
                                            self.iface.mainWindow())
      QObject.connect(self.circleBy2Points_action, SIGNAL("triggered()"), self.runCIRCLE_BY_2POINTS_Command)
      # CIRCLE BY 3 POINTS (MACRO)
      self.circleBy3Points_action = QAction(QIcon(":/plugins/qad/icons/circleBy3Points.png"), \
                                                  QadMsg.translate("Command_CIRCLE", "Cerchio definito da 3 punti"), \
                                                  self.iface.mainWindow())
      QObject.connect(self.circleBy3Points_action, SIGNAL("triggered()"), self.runCIRCLE_BY_3POINTS_Command)
      # CIRCLE BY TANGEN TANGENT RADIUS (MACRO)
      self.circleBy2TansRadius_action = QAction(QIcon(":/plugins/qad/icons/circleBy2TansRadius.png"), \
                                                QadMsg.translate("Command_CIRCLE", "Cerchio definito da 2 punti di tangenza e un raggio"), \
                                                self.iface.mainWindow())
      QObject.connect(self.circleBy2TansRadius_action, SIGNAL("triggered()"), self.runCIRCLE_BY_2TANS_RADIUS_Command)
      # CIRCLE BY TANGEN TANGENT TANGENT (MACRO)
      self.circleBy3Tans_action = QAction(QIcon(":/plugins/qad/icons/circleBy3Tans.png"), \
                                                QadMsg.translate("Command_CIRCLE", "Cerchio definito da 3 punti di tangenza"), \
                                                self.iface.mainWindow())
      QObject.connect(self.circleBy3Tans_action, SIGNAL("triggered()"), self.runCIRCLE_BY_3TANS_Command)
      
      # DSETTINGS
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "IMPOSTADIS"))
      self.dsettings_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.dsettings_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.dsettings_action)
      
      # LINE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "LINEA"))
      self.line_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.line_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.line_action)
      
      # ERASE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "CANCELLA"))
      self.erase_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.erase_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.erase_action)
      
      # MPOLYGON
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "MPOLIGONO"))
      self.mpolygon_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.mpolygon_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.mpolygon_action)
      
      # MBUFFER
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "MBUFFER"))
      self.mbuffer_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.mbuffer_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.mbuffer_action)
      
      # ROTATE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "RUOTA"))
      self.rotate_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.rotate_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.rotate_action)
      
      # MOVE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "SPOSTA"))
      self.move_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.move_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.move_action)
      
      # SCALE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "SCALA"))
      self.scale_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.scale_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.scale_action)
      
      # COPY
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "COPIA"))
      self.copy_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.copy_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.copy_action)
      
      # OFFSET
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "OFFSET"))
      self.offset_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.offset_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.offset_action)
      
      # EXTEND
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "ESTENDI"))
      self.extend_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.extend_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.extend_action)
      
      # TRIM
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "TAGLIA"))
      self.trim_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.trim_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.trim_action)
      
      # RECTANGLE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "RETTANGOLO"))
      self.rectangle_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.rectangle_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.rectangle_action)
      
      # POLYGON
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "POLIGONO"))
      self.polygon_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.polygon_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.polygon_action)
      
      # MIRRROR
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "SPECCHIO"))
      self.mirror_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.mirror_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.mirror_action)
      
      # UNDO
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "ANNULLA"))
      self.undo_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.undo_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.undo_action)
      # UNDO OF ONLY ONE OPERATION (MACRO)
      self.u_action = QAction(QIcon(":/plugins/qad/icons/u.png"), \
                                    QadMsg.translate("Command_UNDO", "Annulla l'ultima operazione eseguita"), \
                                    self.iface.mainWindow())
      QObject.connect(self.u_action, SIGNAL("triggered()"), self.runU_Command)
      
      # REDO
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "RIPRISTINA"))
      self.redo_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.redo_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.redo_action)
      
      # INSERT
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "INSER"))
      self.insert_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.insert_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.insert_action)
      
      # TEXT
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "TESTO"))
      self.text_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.text_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.text_action)
      
      # STRETCH
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "STIRA"))
      self.stretch_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.stretch_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.stretch_action)
      
      # BREAK
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "SPEZZA"))
      self.break_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.break_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.break_action)
      
      # PEDIT
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "EDITPL"))
      self.pedit_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.pedit_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.pedit_action)
      
      # FILLET
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "RACCORDO"))
      self.fillet_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.fillet_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.fillet_action)
      
      # DIMLINEAR
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "DIMLINEARE"))
      self.dimLinear_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.dimLinear_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.dimLinear_action)
      # DIMALIGNED
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "DIMALLINEATA"))
      self.dimAligned_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.dimAligned_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.dimAligned_action)
      # DIMSTYLE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "DIMSTILE"))
      self.dimStyle_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.dimStyle_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.dimStyle_action)


   #============================================================================
   # FINE - Gestione ACTION
   #============================================================================


   def UpdatedVariablesEvent(self):
      # aggiorna in base alle nuove impostazioni delle variabili
      self.tool.UpdatedVariablesEvent()
      
      
   #============================================================================
   # INIZIO - Gestione MENU (da chiamare prima di creare TOOLBAR)
   #============================================================================
   def createArcMenu(self):
      # menu Draw            
      arcMenu = QMenu(QadMsg.translate("Command_list", "ARCO"))
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "ARCO"))
      arcMenu.setIcon(cmd.getIcon())
      arcMenu.addAction(self.arcBy3Points_action)
      arcMenu.addSeparator()      
      arcMenu.addAction(self.arcByStartCenterEndPoints_action)      
      arcMenu.addAction(self.arcByStartCenterAngle_action)      
      arcMenu.addAction(self.arcByStartCenterLength_action)      
      arcMenu.addSeparator()      
      arcMenu.addAction(self.arcByStartEndAngle_action)      
      arcMenu.addAction(self.arcByStartEndTan_action)      
      arcMenu.addAction(self.arcByStartEndRadius_action)      
      arcMenu.addSeparator()      
      arcMenu.addAction(self.arcByCenterStartEnd_action)      
      arcMenu.addAction(self.arcByCenterStartAngle_action)      
      arcMenu.addAction(self.arcByCenterStartLength_action)      
      return arcMenu

   def createCircleMenu(self):
      # menu Draw            
      circleMenu = QMenu(QadMsg.translate("Command_list", "CERCHIO"))
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "CERCHIO"))
      circleMenu.setIcon(cmd.getIcon())
      circleMenu.addAction(self.circleByCenterRadius_action)
      circleMenu.addAction(self.circleByCenterDiameter_action)
      circleMenu.addSeparator()      
      circleMenu.addAction(self.circleBy2Points_action)
      circleMenu.addAction(self.circleBy3Points_action)
      circleMenu.addSeparator()  
      circleMenu.addAction(self.circleBy2TansRadius_action)
      circleMenu.addAction(self.circleBy3Tans_action)
      return circleMenu

   def createDrawMenu(self):
      # menu Draw            
      drawMenu = QMenu(QadMsg.translate("QAD", "Disegna"))
      drawMenu.addAction(self.line_action)
      drawMenu.addAction(self.pline_action)      
      
      # menu arco
      self.arcMenu = self.createArcMenu()
      drawMenu.addMenu(self.arcMenu)
      # menu cerchio
      self.circleMenu = self.createCircleMenu()
      drawMenu.addMenu(self.circleMenu)
      
      drawMenu.addAction(self.rectangle_action)
      drawMenu.addAction(self.polygon_action)
      drawMenu.addAction(self.mpolygon_action)
      drawMenu.addAction(self.mbuffer_action)
      drawMenu.addSeparator()  
      drawMenu.addAction(self.insert_action)
      drawMenu.addAction(self.text_action)      
      return drawMenu

   def createEditMenu(self):
      # menu Edit
      editMenu = QMenu(QadMsg.translate("QAD", "Edita"))
      editMenu.addAction(self.erase_action)
      editMenu.addAction(self.rotate_action)
      editMenu.addAction(self.move_action)
      editMenu.addAction(self.scale_action)
      editMenu.addAction(self.copy_action)
      editMenu.addAction(self.offset_action)
      editMenu.addAction(self.extend_action)
      editMenu.addAction(self.trim_action)
      editMenu.addAction(self.mirror_action)
      editMenu.addAction(self.stretch_action)
      editMenu.addAction(self.break_action)
      editMenu.addAction(self.pedit_action)
      editMenu.addAction(self.fillet_action)
      return editMenu
   
   def createToolsMenu(self):
      # menu Tools            
      toolsMenu = QMenu(QadMsg.translate("QAD", "Strumenti"))
      toolsMenu.addAction(self.setCurrLayerByGraph_action)
      toolsMenu.addAction(self.setCurrUpdateableLayerByGraph_action)      
      toolsMenu.addAction(self.dsettings_action)
      return toolsMenu

   def createDimMenu(self):
      # menu Dim            
      dimMenu = QMenu(QadMsg.translate("QAD", "Quotatura"))
      dimMenu.addAction(self.dimLinear_action)
      dimMenu.addAction(self.dimAligned_action)
      dimMenu.addAction(self.dimStyle_action)
      return dimMenu
      
   #============================================================================
   # FINE - Gestione MENU
   #============================================================================


   #============================================================================
   # INIZIO - Gestione TOOLBAR
   #============================================================================
   def createArcToolButton(self):
      arcToolButton = QToolButton(self.toolBar)
      arcToolButton.setPopupMode(QToolButton.MenuButtonPopup)
      arcToolButton.setMenu(self.arcMenu)
      arcToolButton.setDefaultAction(self.arcMenu.actions()[0]) # prima voce di menu
      arcToolButton.triggered.connect(self.arcToolButtonTriggered)
      return arcToolButton
   def arcToolButtonTriggered(self, action):
      self.arcToolButton.setDefaultAction(action)
   
   def createCircleToolButton(self):
      circleToolButton = QToolButton(self.toolBar)
      circleToolButton.setPopupMode(QToolButton.MenuButtonPopup)
      circleToolButton.setMenu(self.circleMenu)
      circleToolButton.setDefaultAction(self.circleMenu.actions()[0]) # prima voce di menu
      circleToolButton.triggered.connect(self.circleToolButtonTriggered)
      return circleToolButton
   def circleToolButtonTriggered(self, action):
      self.circleToolButton.setDefaultAction(action)

   def createDimToolBar(self):
      # aggiunge la toolbar per la quotatura
      toolBar = self.iface.addToolBar(QadMsg.translate("QAD", "QAD - Quotatura"))
      toolBar.setObjectName(QadMsg.translate("QAD", "QAD - Quotatura"))
      toolBar.addAction(self.dimLinear_action)
      toolBar.addAction(self.dimAligned_action)
      toolBar.addAction(self.dimStyle_action)
      return toolBar


   #============================================================================
   # FINE - Gestione TOOLBAR
   #============================================================================


   #============================================================================
   # INIZIO - Gestione Layer
   #============================================================================


   def layerAdded(self, layer):
      QObject.connect(layer, SIGNAL("layerModified()"), self.layerModified)
      QObject.connect(layer, SIGNAL("beforeCommitChanges()"), self.beforeCommitChanges)
      QObject.connect(layer, SIGNAL("committedFeaturesAdded(QString, QgsFeatureList)"), self.committedFeaturesAdded)
      # vedi qgsvectorlayer.cpp funzione QgsVectorLayer::commitChanges()
      # devo predere l'ultimo segnale vhe viene emesso dal salvataggio QGIS
      # questo segnale arriva alla fine del salvataggio di un layer dalla versione 2.3 di QGIS
      #QObject.connect(layer, SIGNAL("repaintRequested()"), self.repaintRequested)
      # questo segnale arriva alla fine del salvataggio di un layer alla versione 2.2 di QGIS
      QObject.connect(layer, SIGNAL("editingStopped()"), self.editingStopped)      
     
      
   def removeLayer(self, layerId):
      # viene rimosso un layer quindi lo tolgo dallo stack
      self.undoStack.clearByLayer(layerId)
      self.enableUndoRedoButtons()


   def editingStopped(self):
      # questo segnale arriva alla fine del salvataggio di un layer alla versione 2.2 di QGIS
      # se bisogna fare la ricodifica delle quote
      if self.dimTextEntitySetRecodeOnSave.isEmpty() == False:
         # ricavo gli stili di quotatura
         dimStyleList = self.dimStyles.getDimListByLayer(self.dimTextEntitySetRecodeOnSave.layer)
         for dimStyle in dimStyleList:
            # salvo gli oggetti di quello stile di quotatura aggiornando i reference
            self.isSaveControlledByQAD = True
            # ricodifica          
            dimStyle.updateTextReferencesOnSave(self, self.dimTextEntitySetRecodeOnSave.getFeatureCollection())
            self.dimTextEntitySetRecodeOnSave.clear()
            # salvataggio
            dimStyle.commitChanges(self.beforeCommitChangesDimLayer)
            self.beforeCommitChangesDimLayer = None
            self.isSaveControlledByQAD = False
            dimStyle.startEditing()


   def repaintRequested(self):
      # questo segnale arriva alla fine del salvataggio di un layer dalla versione 2.3 di QGIS
      # se bisogna fare la ricodifica delle quote
      if self.dimTextEntitySetRecodeOnSave.isEmpty() == False:
         # ricavo gli stili di quotatura
         dimStyleList = self.dimStyles.getDimListByLayer(self.dimTextEntitySetRecodeOnSave.layer)
         for dimStyle in dimStyleList:
            # salvo gli oggetti di quello stile di quotatura aggiornando i reference
            self.isSaveControlledByQAD = True
            # ricodifica          
            dimStyle.updateTextReferencesOnSave(self, self.dimTextEntitySetRecodeOnSave.getFeatureCollection())
            self.dimTextEntitySetRecodeOnSave.clear()
            # salvataggio
            dimStyle.commitChanges(self.beforeCommitChangesDimLayer)
            self.beforeCommitChangesDimLayer = None
            self.isSaveControlledByQAD = False
            dimStyle.startEditing()

      
   def beforeCommitChanges(self):
      if self.isSaveControlledByQAD == False:      
         layer = self.sender()
         # verifico se il layer che si sta per salvare appartiene ad uno o più stili di quotatura
         dimStyleList = self.dimStyles.getDimListByLayer(layer)
         for dimStyle in dimStyleList:
            if dimStyle.getTextualLayer().id() != layer.id(): # se non si tratta del layer dei testi di quota
               self.beforeCommitChangesDimLayer = layer # memorizzo il layer da cui é scaturito il salvataggio delle quotature
               self.isSaveControlledByQAD = True
               dimStyle.textCommitChangesOnSave() # salvo i testi delle quote per ricodifica ID
               dimStyle.startEditing()
               self.isSaveControlledByQAD = False

      
   def committedFeaturesAdded(self, layerId, addedFeatures):
      layer = qad_layer.getLayerById(layerId)    
      # verifico se il layer che é stato salvato appartiene ad uno o più stili di quotatura
      dimStyleList = self.dimStyles.getDimListByLayer(layer)
      for dimStyle in dimStyleList:
         # se si tratta del layer testuale delle quote
         if dimStyle.getTextualLayer().id() == layerId:
            # mi memorizzo le features testuali da riallineare 
            self.dimTextEntitySetRecodeOnSave.set(dimStyle.getTextualLayer(), addedFeatures)


   def layerModified(self):
      if self.isQadActive == False:
         # la modifica fatta su quel layer é stata fatta dall'esterno di QAD
         # quindi ho perso la sincronizzazione con lo stack di undo di QAD che
         # viene svuotato perché ormai inutilizzabile
         self.undoStack.clear()
         self.enableUndoRedoButtons()
   

   #============================================================================
   # INIZIO - Gestione UNDO e REDO
   #============================================================================

   
   def enableUndoRedoButtons(self):
      self.undo_action.setEnabled(self.undoStack.isUndoAble())
      self.u_action.setEnabled(self.undoStack.isUndoAble())
      self.redo_action.setEnabled(self.undoStack.isRedoAble())

   def beginEditCommand(self, text, layerList):
      if type(layerList) == list or type(layerList) == tuple:
         # layerList é una lista di layer
         self.undoStack.beginEditCommand(text, layerList)
      else:
         # layerList é un solo layer
         self.undoStack.beginEditCommand(text, [layerList])
         
   def destroyEditCommand(self):
      self.isQadActive = True
      self.undoStack.destroyEditCommand()
      self.isQadActive = False
      self.enableUndoRedoButtons()
      
   def endEditCommand(self):
      self.isQadActive = True
      self.undoStack.endEditCommand(self.canvas)
      self.isQadActive = False
      self.enableUndoRedoButtons()
      
   def undoEditCommand(self, nTimes = 1):      
      self.isQadActive = True
      self.undoStack.undoEditCommand(self.canvas, nTimes)
      self.isQadActive = False
      self.enableUndoRedoButtons()
      
   def redoEditCommand(self, nTimes = 1):      
      self.isQadActive = True
      self.undoStack.redoEditCommand(self.canvas, nTimes)
      self.isQadActive = False
      self.enableUndoRedoButtons()

   def addLayerToLastEditCommand(self, text, layer):
      self.undoStack.addLayerToLastEditCommand(text, layer)
      
   def insertBeginGroup(self, text = "Group"):
      self.undoStack.insertBeginGroup(text)
      
   def insertEndGroup(self):
      return self.undoStack.insertEndGroup()

   def insertBookmark(self, text = "Bookmark"):
      return self.undoStack.insertBookmark(text)
      
   def getPrevBookmarkPos(self):
      return self.undoStack.getPrevBookmarkPos(self.undoStack.index)
   
   def undoUntilBookmark(self):
      self.isQadActive = True
      self.undoStack.undoUntilBookmark(self.canvas)
      self.isQadActive = False
      self.enableUndoRedoButtons()

      
   #============================================================================
   # FINE - Gestione UNDO e REDO
   #============================================================================

   def run(self):
      self.setStandardMapTool()
      self.showTextWindow()

   def deactivate(self):
      self.mainAction.setChecked(False)

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

   def showMsg(self, msg, displayPromptAfterMsg = False):
      self.TextWindow.showMsg(msg, displayPromptAfterMsg)
      
   def showErr(self, err):
      self.TextWindow.showErr(err)

   def showInputMsg(self, inputMsg = None, inputType = QadInputTypeEnum.COMMAND, \
                    default = None, keyWords = "", inputMode = QadInputModeEnum.NONE):
      # il valore di default del parametro di una funzione non può essere una traduzione
      # perché lupdate.exe non lo riesce ad interpretare
      if inputMsg is None: 
         inputMsg = QadMsg.translate("QAD", "Comando: ")
      
      self.TextWindow.showInputMsg(inputMsg, inputType, default, keyWords, inputMode)

   
   #============================================================================
   # INIZIO - funzioni per comandi 
   #============================================================================
   def runCommand(self, command):
      self.QadCommands.run(command)

   def runMacro(self, args):
      self.QadCommands.runMacro(args)
   
   def continueCommandFromMapTool(self):
      self.QadCommands.continueCommandFromMapTool()

   def continueCommandFromTextWindow(self, msg):
      self.QadCommands.continueCommandFromTextWindow(msg)

   def abortCommand(self):
      self.QadCommands.abortCommand()
      
   def isValidCommand(self, command):
      return self.QadCommands.isValidCommand(command)
      
   def getCommandNames(self):
      return self.QadCommands.getCommandNames()
   
   def getCommandObj(self, cmdName):
      return self.QadCommands.getCommandObj(cmdName)
   
   def forceCommandMapToolSnapTypeOnce(self, snapType, snapParams = None):
      self.QadCommands.forceCommandMapToolSnapTypeOnce(snapType, snapParams)
   
   def refreshCommandMapToolSnapType(self):
      self.QadCommands.refreshCommandMapToolSnapType()
   
   def getCurrenPointFromCommandMapTool(self):
      return self.QadCommands.getCurrenPointFromCommandMapTool()
   
   def toggleOsMode(self):
      value = QadVariables.get(QadMsg.translate("Environment variables", "OSMODE"))
      if value & QadSnapTypeEnum.DISABLE:
         value =  value - QadSnapTypeEnum.DISABLE
         msg = QadMsg.translate("QAD", "\n<Snap attivato>")
      else:
         value =  value + QadSnapTypeEnum.DISABLE
         msg = QadMsg.translate("QAD", "\n<Snap disattivato>")

      QadVariables.set(QadMsg.translate("Environment variables", "OSMODE"), value)
      QadVariables.save()
      self.showMsg(msg, True)        
      self.QadCommands.refreshCommandMapToolSnapType()

   def toggleOrthoMode(self):
      value = QadVariables.get(QadMsg.translate("Environment variables", "ORTHOMODE"))
      if value == 0:
         value = 1
         autosnap = QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAP"))
         if (autosnap & 8) == True:
            QadVariables.set(QadMsg.translate("Environment variables", "AUTOSNAP"), autosnap - 8) # disattivo la modalità polare 
         msg = QadMsg.translate("QAD", "\n<Modalità ortogonale attivata>")
      else:
         value = 0
         msg = QadMsg.translate("QAD", "\n<Modalità ortogonale disattivata>")

      QadVariables.set(QadMsg.translate("Environment variables", "ORTHOMODE"), value)
      QadVariables.save()
      self.showMsg(msg, True)        
      self.QadCommands.refreshCommandMapToolOrthoMode()

   def togglePolarMode(self):
      value = QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAP"))
      if (value & 8) == False:
         value = value + 8
         QadVariables.set(QadMsg.translate("Environment variables", "ORTHOMODE"), 0) # disattivo la modalità orto 
         msg = QadMsg.translate("QAD", "\n<Modalità polare attivata>")
      else:
         value = value - 8
         msg = QadMsg.translate("QAD", "\n<Modalità polare disattivata>")

      QadVariables.set(QadMsg.translate("Environment variables", "AUTOSNAP"), value)
      QadVariables.save()
      self.showMsg(msg, True)        
      self.QadCommands.refreshCommandMapToolAutoSnap()
   
   def getCurrMsgFromTxtWindow(self):
      return self.TextWindow.getCurrMsg()

   def getHistoryfromTxtWindow(self):
      return self.TextWindow.getHistory() # list

   def updateHistoryfromTxtWindow(self, command):
      return self.TextWindow.updateHistory(command)

   def showEvaluateMsg(self, msg = None):
      self.TextWindow.showEvaluateMsg(msg)
      
   #============================================================================
   # funzioni per l'avvio di un comando
   #============================================================================
   def runCommandAbortingTheCurrent(self, cmdName):
      self.mainAction.setChecked(True)
      self.canvas.setFocus()
      self.abortCommand()
      self.showEvaluateMsg(cmdName)

   def runMacroAbortingTheCurrent(self, args):
      self.mainAction.setChecked(True)
      self.canvas.setFocus()
      self.abortCommand()      
      self.runMacro(args)
      
   def runIDCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "ID"))
   
   def runSETVARCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "MODIVAR"))

   def runPLINECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "PLINEA"))
      
   def runSETCURRLAYERBYGRAPHCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "SETCURRLAYERDAGRAFICA"))

   def runSETCURRUPDATEABLELAYERBYGRAPHCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "SETCURRMODIFLAYERDAGRAFICA"))
      
   def runARCCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "ARCO"))       
   def runARCBY3POINTSCommand(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARCO"), None, None, None]      
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_CENTER_END_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARCO"), \
              None, \
              QadMsg.translate("Command_ARC", "Centro"), \
              None,
              None]      
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_CENTER_ANGLE_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARCO"), \
              None, \
              QadMsg.translate("Command_ARC", "Centro"), \
              None, \
              QadMsg.translate("Command_ARC", "Angolo"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_CENTER_LENGTH_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARCO"), \
              None, \
              QadMsg.translate("Command_ARC", "Centro"), \
              None, \
              QadMsg.translate("Command_ARC", "Lunghezza"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_CENTER_LENGTH_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARCO"), \
              None, \
              QadMsg.translate("Command_ARC", "Centro"), \
              None, \
              QadMsg.translate("Command_ARC", "Lunghezza"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_END_ANGLE_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARCO"), \
              None, \
              QadMsg.translate("Command_ARC", "Fine"), \
              None, \
              QadMsg.translate("Command_ARC", "Angolo"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_END_TAN_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARCO"), \
              None, \
              QadMsg.translate("Command_ARC", "Fine"), \
              None, \
              QadMsg.translate("Command_ARC", "Direzione"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_END_RADIUS_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARCO"), \
              None, \
              QadMsg.translate("Command_ARC", "Fine"), \
              None, \
              QadMsg.translate("Command_ARC", "Raggio"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_CENTER_START_END_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARCO"), \
              QadMsg.translate("Command_ARC", "Centro"), \
              None, \
              None, \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_CENTER_START_ANGLE_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARCO"), \
              QadMsg.translate("Command_ARC", "Centro"), \
              None, \
              None, \
              QadMsg.translate("Command_ARC", "Angolo"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_CENTER_START_LENGTH_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARCO"), \
              QadMsg.translate("Command_ARC", "Centro"), \
              None, \
              None, \
              QadMsg.translate("Command_ARC", "Lunghezza"), \
              None]
      self.runMacroAbortingTheCurrent(args)
            
   def runCIRCLECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "CERCHIO"))
   def runCIRCLE_BY_CENTER_RADIUS_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "CERCHIO"), \
              None, \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runCIRCLE_BY_CENTER_DIAMETER_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "CERCHIO"), \
              None, \
              QadMsg.translate("Command_CIRCLE", "Diametro"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runCIRCLE_BY_2POINTS_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "CERCHIO"), \
              QadMsg.translate("Command_CIRCLE", "2PUnti"), \
              None, \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runCIRCLE_BY_3POINTS_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "CERCHIO"), \
              QadMsg.translate("Command_CIRCLE", "3Punti"), \
              None, \
              None, \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runCIRCLE_BY_2TANS_RADIUS_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "CERCHIO"), \
              QadMsg.translate("Command_CIRCLE", "Ttr"), \
              None, \
              None, \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runCIRCLE_BY_3TANS_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "CERCHIO"), \
              QadMsg.translate("Command_CIRCLE", "3Punti"), \
              QadMsg.translate("Snap", "TAN"), \
              QadMsg.translate("Snap", "TAN"), \
              QadMsg.translate("Snap", "TAN")]
      self.runMacroAbortingTheCurrent(args)
      
   def runDSETTINGSCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "IMPOSTADIS"))
      
   def runLINECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "LINEA"))
      
   def runERASECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "CANCELLA"))
      
   def runMPOLYGONCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "MPOLIGONO"))
      
   def runMBUFFERCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "MBUFFER"))
      
   def runROTATECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "RUOTA"))
      
   def runMOVECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "SPOSTA"))
      
   def runSCALECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "SCALA"))
      
   def runCOPYCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "COPIA"))
      
   def runOFFSETCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "OFFSET"))
      
   def runEXTENDCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "ESTENDI"))
      
   def runTRIMCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "TAGLIA"))
      
   def runRECTANGLECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "RETTANGOLO"))
      
   def runMIRRORCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "SPECCHIO"))
      
   def runUNDOCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "ANNULLA"))
   def runU_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ANNULLA"), \
              QadMsg.translate("Command_UNDO", "1")]
      self.runMacroAbortingTheCurrent(args)
      
   def runREDOCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "RIPRISTINA"))
      
   def runINSERTCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "INSER"))
            
   def runTEXTCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "TESTO"))
            
   def runSTRETCHCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "STIRA"))
            
   def runBREAKCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "SPEZZA"))
            
   def runPEDITCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "EDITPL"))

   def runFILLETCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "RACCORDO"))
      
   def runPOLYGONCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "POLIGONO"))      
      
   def runDIMLINEARCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "DIMLINEARE"))

   def runDIMALIGNEDCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "DIMALLINEATA"))

   def runDIMSTYLECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "DIMSTILE"))
