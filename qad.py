# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comandi di editazione geometria stile CAD
 
                              -------------------
        begin                : 2014-11-03
        copyright            : 2013-2016
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
# Initialize Qt resources from file qad_rc.py
import qad_rc
import math


import qad_utils
from qad_maptool import QadMapTool
from qad_variables import *
from qad_textwindow import *
from qad_commands import *
from qad_entity import *
from qad_dim import QadDimStyles
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
   lastPolygonConstructionModeByCenter = QadMsg.translate("Command_POLYGON", "Inscribed in circle")
   # ultimo delta usato nel comando lengthen
   lastDelta_lengthen = 0.0
   # ultimo delta angolo usato nel comando lengthen
   lastDeltaAngle_lengthen = 0.0
   # ultima percentuale usata nel comando lengthen
   lastPerc_lengthen = 100.0
   # ultima lunghezza totale usato nel comando lengthen
   lastTotal_lengthen = 1.0
   # ultimo angolo totale usato nel comando lengthen
   lastTotalAngle_lengthen = 0.0
   # ultima modalità operativa del comando lengthen
   lastOpMode_lengthen = "DElta"

   # flag per identificare se un comando di QAD é attivo oppure no
   isQadActive = False
   
   # Quotatura
   dimTextEntitySetRecodeOnSave = QadLayerEntitySet() # entity set dei testi delle quote da riallineare in salvataggio
   beforeCommitChangesDimLayer = None         # layer da cui é scaturito il salvataggio delle quotature
   isSaveControlledByQAD = False

   # comando dsettings - ultimo tab utilizzato
   dsettingsLastUsedTabIndex = -1 # -1 = non inizializzato
   
   # comando options - ultimo tab utilizzato
   optionsLastUsedTabIndex = -1 # -1 = non inizializzato


   #============================================================================
   # version
   #============================================================================
   def version(self):
      return "2.8.009"
   
   
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

   def setLastDelta_lengthen(self, lastDelta_lengthen):
      # ultimo delta usato nel comando lengthen
      self.lastDelta_lengthen = lastDelta_lengthen

   def setLastDeltaAngle_lengthen(self, lastDeltaAngle_lengthen):
      # ultimo delta angolo usato nel comando lengthen
      self.lastDeltaAngle_lengthen = qad_utils.normalizeAngle(lastDeltaAngle_lengthen)

   def setLastPerc_lengthen(self, lastPerc_lengthen):      
      # ultima percentuale usata nel comando lengthen
      if lastPerc_lengthen > 0:
         self.lastPerc_lengthen = lastPerc_lengthen

   def setLastTotal_lengthen(self, lastTotal_lengthen):      
      # ultima lunghezza totale usato nel comando lengthen
      if lastTotal_lengthen > 0:
         self.lastTotal_lengthen = lastTotal_lengthen

   def setLastTotalAngle_lengthen(self, lastTotalAngle_lengthen):      
      # ultimo angolo totale usato nel comando lengthen
      self.lastTotalAngle_lengthen = qad_utils.normalizeAngle(lastTotalAngle_lengthen)

   def setLastOpMode_lengthen(self, opMode):
      # memorizzo modalità operativa del comando lengthen: "DElta" o "Percent" o "Total" o "DYnamic"
      if opMode == "DElta" or opMode == "Percent" or opMode == "Total" or opMode == "DYnamic":
         self.lastOpMode_lengthen = opMode     

   def loadDimStyles(self):
      global QadDimStyles
      # carico gli stili di quotatura
      QadDimStyles.load()
      # questa variabile non avrebbe senso perchè si dovrebbe usare la variabile globale QadDimStyles
      # per un motivo sconosciuto quando si generano gli eventi tipo beforeCommitChanges
      # la variabile globale QadDimStyles risulta essere None anche se QAD non lo hai mai posto a quel valore
      # se invece uso una variabile del plugin che punta a QadDimStyles questa non viene messa a None
      self.mQadDimStyle = QadDimStyles
      
      
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
      # provo a caricare la lingua e la regione selezionate
      if self.__initLocalization(language + "_" + region) == False:
         # provo a caricare la lingua
         self.__initLocalization(language)
                        
      self.canvas = self.iface.mapCanvas()
      self.tool = QadMapTool(self)
      
      # Lista dei comandi
      self.QadCommands = QadCommandsClass(self)
      
      self.TextWindow = None
      
      # inizializzzione sul caricamento del progetto
      self.initOnProjectLoaded()
      
   def initOnProjectLoaded(self):
      # carico le variabili d'ambiente
      QadVariables.load()
      
      if self.TextWindow is not None:
         self.TextWindow.refreshColors()
         
      # carico gli stili di quotatura
      self.loadDimStyles()
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
      self.menu.addAction(self.help_action)

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
      self.toolBar.addAction(self.help_action)

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
      self.toolBar.addAction(self.lengthen_action)
      self.toolBar.addAction(self.break_action)
      self.toolBar.addAction(self.pedit_action)
      self.toolBar.addAction(self.mapmpedit_action)
      self.toolBar.addAction(self.fillet_action)
      self.toolBar.addAction(self.join_action)
      self.toolBar.addAction(self.disjoin_action)
      self.toolBar.addAction(self.dsettings_action)
      self.toolBar.addAction(self.options_action)
      self.enableUndoRedoButtons()

      # aggiunge la toolbar per la quotatura 
      self.dimToolBar = self.createDimToolBar()
      
      # Inizializzo la finestra di testo
      self.TextWindow = QadTextWindow(self)
      self.TextWindow.initGui()

      # aggiungo i segnali di aggiunta e rimozione di layer per collegare ogni layer
      # all'evento <layerModified> per sapere se la modifica fatta su quel layer
      # é stata fatta da QAD o dall'esterno
      QObject.connect(QgsMapLayerRegistry.instance(), SIGNAL("layerWasAdded(QgsMapLayer *)"), self.layerAdded)
      QObject.connect(QgsMapLayerRegistry.instance(), SIGNAL("layerWillBeRemoved(QString)"), self.removeLayer)
      QObject.connect(self.iface, SIGNAL("projectRead()"), self.onProjectLoaded)

      self.showTextWindow(QadVariables.get(QadMsg.translate("Environment variables", "SHOWTEXTWINDOW"), True))
      self.setStandardMapTool()


   def unload(self):
      self.abortCommand()
      # Disconnect to signals
      QObject.disconnect(self.canvas, SIGNAL("mapToolSet(QgsMapTool*)"), self.deactivate)            
      QObject.disconnect(QgsMapLayerRegistry.instance(), SIGNAL("layerWasAdded(QgsMapLayer *)"), self.layerAdded)
      QObject.disconnect(QgsMapLayerRegistry.instance(), SIGNAL("layerWillBeRemoved(QString)"), self.removeLayer)
      QObject.disconnect(self.iface, SIGNAL("projectRead()"), self.onProjectLoaded)
      
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
         if self.canvas.mapTool() == self.tool:
            self.canvas.unsetMapTool(self.tool)
         elif self.QadCommands.actualCommand is not None:
            if self.canvas.mapTool() == self.QadCommands.actualCommand.getPointMapTool():
               self.canvas.unsetMapTool(self.QadCommands.actualCommand.getPointMapTool())
         
         self.tool.removeItems()
         del self.tool


   def onProjectLoaded(self):
      self.initOnProjectLoaded()
      self.showTextWindow(QadVariables.get(QadMsg.translate("Environment variables", "SHOWTEXTWINDOW"), True))
      self.setStandardMapTool()


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
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "PLINE"))
      self.pline_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.pline_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.pline_action)
      
      # SETCURRLAYERBYGRAPH
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "SETCURRLAYERBYGRAPH"))
      self.setCurrLayerByGraph_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.setCurrLayerByGraph_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.setCurrLayerByGraph_action)
      # SETCURRUPDATEABLELAYERBYGRAPH
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "SETCURRUPDATEABLELAYERBYGRAPH"))
      self.setCurrUpdateableLayerByGraph_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.setCurrUpdateableLayerByGraph_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.setCurrUpdateableLayerByGraph_action)
            
      # ARC
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "ARC"))
      self.arc_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.arc_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.arc_action)
      # ARC BY 3 POINTS (MACRO)
      self.arcBy3Points_action = QAction(QIcon(":/plugins/qad/icons/arcBy3Points.png"), \
                                         QadMsg.translate("Command_ARC", "Arc passing through 3 points"), \
                                         self.iface.mainWindow())
      QObject.connect(self.arcBy3Points_action, SIGNAL("triggered()"), self.runARCBY3POINTSCommand)
      # ARC BY START CENTER END POINTS (MACRO)
      self.arcByStartCenterEndPoints_action = QAction(QIcon(":/plugins/qad/icons/arcByStartCenterEndPoints.png"), \
                                                      QadMsg.translate("Command_ARC", "Arc defined by start, central and final points"), \
                                                      self.iface.mainWindow())
      QObject.connect(self.arcByStartCenterEndPoints_action, SIGNAL("triggered()"), self.runARC_BY_START_CENTER_END_Command)
      # ARC BY START CENTER ANGLE (MACRO)
      self.arcByStartCenterAngle_action = QAction(QIcon(":/plugins/qad/icons/arcByStartCenterAngle.png"), \
                                                  QadMsg.translate("Command_ARC", "Arc defined by start, central points and angle"), \
                                                  self.iface.mainWindow())
      QObject.connect(self.arcByStartCenterAngle_action, SIGNAL("triggered()"), self.runARC_BY_START_CENTER_ANGLE_Command)
      # ARC BY START CENTER LENGTH (MACRO)
      self.arcByStartCenterLength_action = QAction(QIcon(":/plugins/qad/icons/arcByStartCenterLength.png"), \
                                                   QadMsg.translate("Command_ARC", "Arc defined by start, central points and cord length"), \
                                                   self.iface.mainWindow())
      QObject.connect(self.arcByStartCenterLength_action, SIGNAL("triggered()"), self.runARC_BY_START_CENTER_LENGTH_Command)
      # ARC BY START END ANGLE (MACRO)
      self.arcByStartEndAngle_action = QAction(QIcon(":/plugins/qad/icons/arcByStartEndAngle.png"), \
                                               QadMsg.translate("Command_ARC", "Arc defined by start, final points and angle"), \
                                               self.iface.mainWindow())
      QObject.connect(self.arcByStartEndAngle_action, SIGNAL("triggered()"), self.runARC_BY_START_END_ANGLE_Command)
      # ARC BY START END TAN (MACRO)
      self.arcByStartEndTan_action = QAction(QIcon(":/plugins/qad/icons/arcByStartEndTan.png"), \
                                               QadMsg.translate("Command_ARC", "Arc defined by start, final points and tangent"), \
                                               self.iface.mainWindow())
      QObject.connect(self.arcByStartEndTan_action, SIGNAL("triggered()"), self.runARC_BY_START_END_TAN_Command)
      # ARC BY START END RADIUS (MACRO)
      self.arcByStartEndRadius_action = QAction(QIcon(":/plugins/qad/icons/arcByStartEndRadius.png"), \
                                               QadMsg.translate("Command_ARC", "Arc defined by start, final points and radius"), \
                                               self.iface.mainWindow())
      QObject.connect(self.arcByStartEndRadius_action, SIGNAL("triggered()"), self.runARC_BY_START_END_RADIUS_Command)
      # ARC BY CENTER START END (MACRO)
      self.arcByCenterStartEnd_action = QAction(QIcon(":/plugins/qad/icons/arcByCenterStartEnd.png"), \
                                                QadMsg.translate("Command_ARC", "Arc defined by central, start and final points"), \
                                                self.iface.mainWindow())
      QObject.connect(self.arcByCenterStartEnd_action, SIGNAL("triggered()"), self.runARC_BY_CENTER_START_END_Command)
      # ARC BY CENTER START ANGLE (MACRO)
      self.arcByCenterStartAngle_action = QAction(QIcon(":/plugins/qad/icons/arcByCenterStartAngle.png"), \
                                                  QadMsg.translate("Command_ARC", "Arc defined by central, start points and angle"), \
                                                  self.iface.mainWindow())
      QObject.connect(self.arcByCenterStartAngle_action, SIGNAL("triggered()"), self.runARC_BY_CENTER_START_ANGLE_Command)
      # ARC BY CENTER START LENGTH (MACRO)
      self.arcByCenterStartLength_action = QAction(QIcon(":/plugins/qad/icons/arcByCenterStartLength.png"), \
                                                   QadMsg.translate("Command_ARC", "Arc defined by central, start points and cord length"), \
                                                   self.iface.mainWindow())
      QObject.connect(self.arcByCenterStartLength_action, SIGNAL("triggered()"), self.runARC_BY_CENTER_START_LENGTH_Command)
      
      # CIRCLE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "CIRCLE"))
      self.circle_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.circle_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.circle_action)
      # CIRCLE BY CENTER RADIUS (MACRO)
      self.circleByCenterRadius_action = QAction(QIcon(":/plugins/qad/icons/circleByCenterRadius.png"), \
                                                 QadMsg.translate("Command_CIRCLE", "Circle defined by central point and radius"), \
                                                 self.iface.mainWindow())
      QObject.connect(self.circleByCenterRadius_action, SIGNAL("triggered()"), self.runCIRCLE_BY_CENTER_RADIUS_Command)
      # CIRCLE BY CENTER DIAMETER (MACRO)
      self.circleByCenterDiameter_action = QAction(QIcon(":/plugins/qad/icons/circleByCenterDiameter.png"), \
                                                   QadMsg.translate("Command_CIRCLE", "Circle defined by central point and diameter"), \
                                                   self.iface.mainWindow())
      QObject.connect(self.circleByCenterDiameter_action, SIGNAL("triggered()"), self.runCIRCLE_BY_CENTER_DIAMETER_Command)
      # CIRCLE BY 2 POINTS (MACRO)
      self.circleBy2Points_action = QAction(QIcon(":/plugins/qad/icons/circleBy2Points.png"), \
                                            QadMsg.translate("Command_CIRCLE", "Circle defined by 2 points"), \
                                            self.iface.mainWindow())
      QObject.connect(self.circleBy2Points_action, SIGNAL("triggered()"), self.runCIRCLE_BY_2POINTS_Command)
      # CIRCLE BY 3 POINTS (MACRO)
      self.circleBy3Points_action = QAction(QIcon(":/plugins/qad/icons/circleBy3Points.png"), \
                                                  QadMsg.translate("Command_CIRCLE", "Circle defined by 3 points"), \
                                                  self.iface.mainWindow())
      QObject.connect(self.circleBy3Points_action, SIGNAL("triggered()"), self.runCIRCLE_BY_3POINTS_Command)
      # CIRCLE BY TANGEN TANGENT RADIUS (MACRO)
      self.circleBy2TansRadius_action = QAction(QIcon(":/plugins/qad/icons/circleBy2TansRadius.png"), \
                                                QadMsg.translate("Command_CIRCLE", "Circle defined by 2 tangent points and radius"), \
                                                self.iface.mainWindow())
      QObject.connect(self.circleBy2TansRadius_action, SIGNAL("triggered()"), self.runCIRCLE_BY_2TANS_RADIUS_Command)
      # CIRCLE BY TANGEN TANGENT TANGENT (MACRO)
      self.circleBy3Tans_action = QAction(QIcon(":/plugins/qad/icons/circleBy3Tans.png"), \
                                                QadMsg.translate("Command_CIRCLE", "Circle defined by 3 tangent points"), \
                                                self.iface.mainWindow())
      QObject.connect(self.circleBy3Tans_action, SIGNAL("triggered()"), self.runCIRCLE_BY_3TANS_Command)
      
      # DSETTINGS
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "DSETTINGS"))
      self.dsettings_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.dsettings_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.dsettings_action)
      
      # LINE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "LINE"))
      self.line_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.line_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.line_action)
      
      # ERASE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "ERASE"))
      self.erase_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.erase_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.erase_action)
      
      # MPOLYGON
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "MPOLYGON"))
      self.mpolygon_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.mpolygon_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.mpolygon_action)
      
      # MBUFFER
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "MBUFFER"))
      self.mbuffer_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.mbuffer_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.mbuffer_action)
      
      # ROTATE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "ROTATE"))
      self.rotate_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.rotate_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.rotate_action)
      
      # MOVE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "MOVE"))
      self.move_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.move_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.move_action)
      
      # SCALE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "SCALE"))
      self.scale_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.scale_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.scale_action)
      
      # COPY
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "COPY"))
      self.copy_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.copy_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.copy_action)
      
      # OFFSET
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "OFFSET"))
      self.offset_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.offset_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.offset_action)
      
      # EXTEND
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "EXTEND"))
      self.extend_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.extend_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.extend_action)
      
      # TRIM
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "TRIM"))
      self.trim_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.trim_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.trim_action)
      
      # RECTANGLE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "RECTANGLE"))
      self.rectangle_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.rectangle_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.rectangle_action)
      
      # POLYGON
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "POLYGON"))
      self.polygon_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.polygon_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.polygon_action)
      
      # MIRROR
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "MIRROR"))
      self.mirror_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.mirror_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.mirror_action)
      
      # UNDO
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "UNDO"))
      self.undo_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.undo_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.undo_action)
      # UNDO OF ONLY ONE OPERATION (MACRO)
      self.u_action = QAction(QIcon(":/plugins/qad/icons/u.png"), \
                                    QadMsg.translate("Command_UNDO", "Undo last operation"), \
                                    self.iface.mainWindow())
      QObject.connect(self.u_action, SIGNAL("triggered()"), self.runU_Command)
      
      # REDO
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "REDO"))
      self.redo_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.redo_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.redo_action)
      
      # INSERT
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "INSERT"))
      self.insert_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.insert_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.insert_action)
      
      # TEXT
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "TEXT"))
      self.text_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.text_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.text_action)
      
      # STRETCH
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "STRETCH"))
      self.stretch_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.stretch_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.stretch_action)
      
      # LENGTHEN
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "LENGTHEN"))
      self.lengthen_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.lengthen_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.lengthen_action)
      
      # BREAK
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "BREAK"))
      self.break_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.break_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.break_action)
      
      # PEDIT
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "PEDIT"))
      self.pedit_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.pedit_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.pedit_action)
      
      # MAPMPEDIT
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "MAPMPEDIT"))
      self.mapmpedit_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.mapmpedit_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.mapmpedit_action)
      
      # FILLET
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "FILLET"))
      self.fillet_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.fillet_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.fillet_action)
      
      # JOIN
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "JOIN"))
      self.join_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.join_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.join_action)
      
      # DISJOIN
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "DISJOIN"))
      self.disjoin_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.disjoin_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.disjoin_action)
      
      # DIMLINEAR
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "DIMLINEAR"))
      self.dimLinear_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.dimLinear_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.dimLinear_action)
      # DIMALIGNED
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "DIMALIGNED"))
      self.dimAligned_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.dimAligned_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.dimAligned_action)
      # DIMSTYLE
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "DIMSTYLE"))
      self.dimStyle_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.dimStyle_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.dimStyle_action)

      # HELP
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "HELP"))
      self.help_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.help_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.help_action)
      
      # OPTIONS
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "OPTIONS"))
      self.options_action = QAction(cmd.getIcon(), cmd.getName(), self.iface.mainWindow())
      self.options_action.setToolTip(cmd.getToolTipText())
      cmd.connectQAction(self.options_action)


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
      arcMenu = QMenu(QadMsg.translate("Command_list", "ARC"))
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "ARC"))
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
      circleMenu = QMenu(QadMsg.translate("Command_list", "CIRCLE"))
      cmd = self.QadCommands.getCommandObj(QadMsg.translate("Command_list", "CIRCLE"))
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
      drawMenu = QMenu(QadMsg.translate("QAD", "Draw"))
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
      editMenu = QMenu(QadMsg.translate("QAD", "Edit"))
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
      editMenu.addAction(self.lengthen_action)
      editMenu.addAction(self.break_action)
      editMenu.addAction(self.pedit_action)
      editMenu.addAction(self.mapmpedit_action)
      editMenu.addAction(self.fillet_action)
      editMenu.addAction(self.join_action)
      editMenu.addAction(self.disjoin_action)
      return editMenu
   
   def createToolsMenu(self):
      # menu Tools            
      toolsMenu = QMenu(QadMsg.translate("QAD", "Tools"))
      toolsMenu.addAction(self.setCurrLayerByGraph_action)
      toolsMenu.addAction(self.setCurrUpdateableLayerByGraph_action)      
      toolsMenu.addAction(self.dsettings_action)
      toolsMenu.addAction(self.options_action)
      return toolsMenu

   def createDimMenu(self):
      # menu Dim            
      dimMenu = QMenu(QadMsg.translate("QAD", "Dimensioning"))
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
      toolBar = self.iface.addToolBar(QadMsg.translate("QAD", "QAD - Dimensioning"))
      toolBar.setObjectName(QadMsg.translate("QAD", "QAD - Dimensioning"))
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

   # se viene salvato per prima un layer di quote testuale:
   # 1) beforeCommitChanges su layer testuale
   # 2) committedFeaturesAdded su layer testuale
   # 3) editingStopped su layer testuale che scatena
   #    1) committedFeaturesAdded su layer linee
   #    2) committedFeaturesAdded su layer simboli

   # se viene salvato per prima un layer di quote simbolo o linea:
   # 1) beforeCommitChanges su layer simbolo o linea
   # 2) committedFeaturesAdded su layer testuale
   # 3) editingStopped su layer testuale che scatena
   #    1) committedFeaturesAdded su layer linea
   #    2) committedFeaturesAdded su layer simboli
   
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
         layer = self.dimTextEntitySetRecodeOnSave.layer
         # ricavo gli stili di quotatura
         dimStyleList = self.mQadDimStyle.getDimListByLayer(layer)
         for dimStyle in dimStyleList:
            if dimStyle.getInValidErrMsg() is None: # stile valido
               # cerco tutte le feature in self.dimTextEntitySetRecodeOnSave che appartengono allo stile
               # di quotatura dimStyle
               textAddedFeatures = dimStyle.getFilteredFeatureCollection(self.dimTextEntitySetRecodeOnSave)
               # salvo gli oggetti di quello stile di quotatura aggiornando i reference
               self.isSaveControlledByQAD = True
               # ricodifica          
               dimStyle.updateTextReferencesOnSave(self, textAddedFeatures)
            
         self.dimTextEntitySetRecodeOnSave.clear()

         for dimStyle in dimStyleList:
            if dimStyle.getInValidErrMsg() is None: # stile valido
               # salvataggio
               dimStyle.commitChanges(self.beforeCommitChangesDimLayer)
               self.beforeCommitChangesDimLayer = None
               self.isSaveControlledByQAD = False
               dimStyle.startEditing()
      elif self.isSaveControlledByQAD == False:
         layer = self.sender()
         # verifico se il layer che si è appena finito di salvare appartiene ad uno o più stili di quotatura
         dimStyleList = self.mQadDimStyle.getDimListByLayer(layer)
         for dimStyle in dimStyleList:
            if dimStyle.getInValidErrMsg() is None: # stile valido
               # salvataggio
               self.isSaveControlledByQAD = True
               dimStyle.commitChanges(self.beforeCommitChangesDimLayer)
               self.beforeCommitChangesDimLayer = None
               self.isSaveControlledByQAD = False
               dimStyle.startEditing()


   def repaintRequested(self):
      # questo segnale arriva alla fine del salvataggio di un layer dalla versione 2.3 di QGIS
      # se bisogna fare la ricodifica delle quote
      if self.dimTextEntitySetRecodeOnSave.isEmpty() == False:
         # ricavo gli stili di quotatura
         dimStyleList = self.mQadDimStyle.getDimListByLayer(self.dimTextEntitySetRecodeOnSave.layer)
         for dimStyle in dimStyleList:
            if dimStyle.getInValidErrMsg() is None: # stile valido
               # cerco tutte le feature in self.dimTextEntitySetRecodeOnSave che appartengono allo stile
               # di quotatura dimStyle
               textAddedFeatures = dimStyle.getFilteredFeatureCollection(self.dimTextEntitySetRecodeOnSave)            
               # salvo gli oggetti di quello stile di quotatura aggiornando i reference
               self.isSaveControlledByQAD = True
               # ricodifica          
               dimStyle.updateTextReferencesOnSave(self, textAddedFeatures)
            
         self.dimTextEntitySetRecodeOnSave.clear()
         
         for dimStyle in dimStyleList:
            if dimStyle.getInValidErrMsg() is None: # stile valido
               # salvataggio
               dimStyle.commitChanges(self.beforeCommitChangesDimLayer)
               self.beforeCommitChangesDimLayer = None
               self.isSaveControlledByQAD = False
               dimStyle.startEditing()

      
   def beforeCommitChanges(self):
      if self.isSaveControlledByQAD == False:
         layer = self.sender()
         # verifico se il layer che si sta per salvare appartiene ad uno o più stili di quotatura
         dimStyleList = self.mQadDimStyle.getDimListByLayer(layer)
         for dimStyle in dimStyleList:
            if dimStyle.getInValidErrMsg() is None: # stile valido
               if dimStyle.getTextualLayer().id() != layer.id(): # se non si tratta del layer dei testi di quota
                  self.beforeCommitChangesDimLayer = layer # memorizzo il layer da cui é scaturito il salvataggio delle quotature
                  self.isSaveControlledByQAD = True
                  dimStyle.textCommitChangesOnSave() # salvo i testi delle quote per ricodifica ID
                  dimStyle.startEditing()
                  self.isSaveControlledByQAD = False

      
   def committedFeaturesAdded(self, layerId, addedFeatures):
      layer = qad_layer.getLayerById(layerId)
      # verifico se il layer che é stato salvato appartiene ad uno o più stili di quotatura
      dimStyleList = self.mQadDimStyle.getDimListByLayer(layer)
      for dimStyle in dimStyleList:
         if dimStyle.getInValidErrMsg() is None: # stile valido
            # se si tratta del layer testuale delle quote
            if dimStyle.getTextualLayer().id() == layerId:
               # mi memorizzo le features testuali da riallineare 
               self.dimTextEntitySetRecodeOnSave.set(dimStyle.getTextualLayer(), addedFeatures)
               return


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
      # pulisco le entità selezionate e i grip points correnti
      self.tool.clearEntitySet()
      self.tool.clearEntityGripPoints()

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
      # pulisco le entità selezionate e i grip points correnti
      self.tool.clearEntitySet()
      self.tool.clearEntityGripPoints()
      
      self.isQadActive = True
      self.undoStack.undoEditCommand(self.canvas, nTimes)
      self.isQadActive = False
      self.enableUndoRedoButtons()


   def redoEditCommand(self, nTimes = 1):      
      # pulisco le entità selezionate e i grip points correnti
      self.tool.clearEntitySet()
      self.tool.clearEntityGripPoints()

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
      # pulisco le entità selezionate e i grip points correnti
      self.tool.clearEntitySet()
      self.tool.clearEntityGripPoints()

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
         inputMsg = QadMsg.translate("QAD", "Command: ")
      
      self.TextWindow.showInputMsg(inputMsg, inputType, default, keyWords, inputMode)

   
   #============================================================================
   # INIZIO - funzioni per comandi 
   #============================================================================
   
   def clearCurrentObjsSelection(self):
      # pulisco le entità selezionate e i grip points correnti
      self.tool.clearEntitySet()
      self.clearEntityGripPoints()

   def clearEntityGripPoints(self):
      # pulisco i grip points correnti
      self.tool.clearEntityGripPoints()
   
   def runCommand(self, command, param = None):
      self.QadCommands.run(command, param)

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
   
   def getMoreUsedCmd(self, filter):
      return self.QadCommands.getMoreUsedCmd(filter)

   def isValidEnvVariable(self, variable):
      return self.QadCommands.isValidEnvVariable(variable)
   
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
         msg = QadMsg.translate("QAD", "<Snap on>")
      else:
         value =  value + QadSnapTypeEnum.DISABLE
         msg = QadMsg.translate("QAD", "<Snap off>")

      QadVariables.set(QadMsg.translate("Environment variables", "OSMODE"), value)
      QadVariables.save()
      self.showMsg(msg, True)        
      self.QadCommands.refreshCommandMapToolSnapType()

   def toggleOrthoMode(self):
      value = QadVariables.get(QadMsg.translate("Environment variables", "ORTHOMODE"))
      if value == 0:
         value = 1
         autosnap = QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAP"))
         if (autosnap & QadAUTOSNAPEnum.POLAR_TRACKING) == True:
            QadVariables.set(QadMsg.translate("Environment variables", "AUTOSNAP"), autosnap - QadAUTOSNAPEnum.POLAR_TRACKING) # disattivo la modalità polare 
         msg = QadMsg.translate("QAD", "<Ortho on>")
      else:
         value = 0
         msg = QadMsg.translate("QAD", "<Ortho off>")

      QadVariables.set(QadMsg.translate("Environment variables", "ORTHOMODE"), value)
      QadVariables.save()
      self.showMsg(msg, True)        
      self.QadCommands.refreshCommandMapToolOrthoMode()


   def togglePolarMode(self):
      value = QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAP"))
      if (value & QadAUTOSNAPEnum.POLAR_TRACKING) == False:
         value = value + QadAUTOSNAPEnum.POLAR_TRACKING
         QadVariables.set(QadMsg.translate("Environment variables", "ORTHOMODE"), 0) # disattivo la modalità orto 
         msg = QadMsg.translate("QAD", "<Polar on>")
      else:
         value = value - QadAUTOSNAPEnum.POLAR_TRACKING
         msg = QadMsg.translate("QAD", "<Polar off>")

      QadVariables.set(QadMsg.translate("Environment variables", "AUTOSNAP"), value)
      QadVariables.save()
      self.showMsg(msg, True)        
      self.QadCommands.refreshCommandMapToolAutoSnap()


   def toggleObjectSnapTracking(self):
      value = QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAP"))
      if (value & QadAUTOSNAPEnum.OBJ_SNAP_TRACKING) == False:
         value = value + QadAUTOSNAPEnum.OBJ_SNAP_TRACKING
         msg = QadMsg.translate("QAD", "<Object Snap Tracking on>")
      else:
         value = value - QadAUTOSNAPEnum.OBJ_SNAP_TRACKING
         msg = QadMsg.translate("QAD", "<Object Snap Tracking off>")

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
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "SETVAR"))

   def runPLINECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "PLINE"))
      
   def runSETCURRLAYERBYGRAPHCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "SETCURRLAYERBYGRAPH"))

   def runSETCURRUPDATEABLELAYERBYGRAPHCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "SETCURRUPDATEABLELAYERBYGRAPH"))
      
   def runARCCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "ARC"))
   def runARCBY3POINTSCommand(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARC"), None, None, None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_CENTER_END_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARC"), \
              None, \
              QadMsg.translate("Command_ARC", "Center"), \
              None,
              None]      
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_CENTER_ANGLE_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARC"), \
              None, \
              QadMsg.translate("Command_ARC", "Center"), \
              None, \
              QadMsg.translate("Command_ARC", "Angle"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_CENTER_LENGTH_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARC"), \
              None, \
              QadMsg.translate("Command_ARC", "Center"), \
              None, \
              QadMsg.translate("Command_ARC", "chord Length"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_END_ANGLE_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARC"), \
              None, \
              QadMsg.translate("Command_ARC", "End"), \
              None, \
              QadMsg.translate("Command_ARC", "Angle"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_END_TAN_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARC"), \
              None, \
              QadMsg.translate("Command_ARC", "End"), \
              None, \
              QadMsg.translate("Command_ARC", "Direction"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_START_END_RADIUS_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARC"), \
              None, \
              QadMsg.translate("Command_ARC", "End"), \
              None, \
              QadMsg.translate("Command_ARC", "Radius"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_CENTER_START_END_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARC"), \
              QadMsg.translate("Command_ARC", "Center"), \
              None, \
              None, \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_CENTER_START_ANGLE_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARC"), \
              QadMsg.translate("Command_ARC", "Center"), \
              None, \
              None, \
              QadMsg.translate("Command_ARC", "Angle"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runARC_BY_CENTER_START_LENGTH_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "ARC"), \
              QadMsg.translate("Command_ARC", "Center"), \
              None, \
              None, \
              QadMsg.translate("Command_ARC", "chord Length"), \
              None]
      self.runMacroAbortingTheCurrent(args)
            
   def runCIRCLECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "CIRCLE"))
   def runCIRCLE_BY_CENTER_RADIUS_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "CIRCLE"), \
              None, \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runCIRCLE_BY_CENTER_DIAMETER_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "CERCHIO"), \
              None, \
              QadMsg.translate("Command_CIRCLE", "Diameter"), \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runCIRCLE_BY_2POINTS_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "CIRCLE"), \
              QadMsg.translate("Command_CIRCLE", "2POints"), \
              None, \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runCIRCLE_BY_3POINTS_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "CIRCLE"), \
              QadMsg.translate("Command_CIRCLE", "3Points"), \
              None, \
              None, \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runCIRCLE_BY_2TANS_RADIUS_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "CIRCLE"), \
              QadMsg.translate("Command_CIRCLE", "Ttr (tangent tangent radius)"), \
              None, \
              None, \
              None]
      self.runMacroAbortingTheCurrent(args)
   def runCIRCLE_BY_3TANS_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "CIRCLE"), \
              QadMsg.translate("Command_CIRCLE", "3Points"), \
              QadMsg.translate("Snap", "TAN"), \
              QadMsg.translate("Snap", "TAN"), \
              QadMsg.translate("Snap", "TAN")]
      self.runMacroAbortingTheCurrent(args)
      
   def runDSETTINGSCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "DSETTINGS"))
      
   def runLINECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "LINE"))
      
   def runERASECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "ERASE"))
      
   def runMPOLYGONCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "MPOLYGON"))
      
   def runMBUFFERCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "MBUFFER"))
      
   def runROTATECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "ROTATE"))
      
   def runMOVECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "MOVE"))
      
   def runSCALECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "SCALE"))
      
   def runCOPYCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "COPY"))
      
   def runOFFSETCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "OFFSET"))
      
   def runEXTENDCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "EXTEND"))
      
   def runTRIMCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "TRIM"))
      
   def runRECTANGLECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "RECTANGLE"))
      
   def runMIRRORCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "MIRROR"))
      
   def runUNDOCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "UNDO"))
   def runU_Command(self): # MACRO
      # nome comando + argomenti
      args = [QadMsg.translate("Command_list", "UNDO"), \
              QadMsg.translate("Command_UNDO", "1")]
      self.runMacroAbortingTheCurrent(args)
      
   def runREDOCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "REDO"))
      
   def runINSERTCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "INSERT"))
            
   def runTEXTCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "TEXT"))
            
   def runSTRETCHCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "STRETCH"))
            
   def runBREAKCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "BREAK"))
            
   def runPEDITCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "PEDIT"))
            
   def runMAPMPEDITCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "MAPMPEDIT"))

   def runFILLETCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "FILLET"))
      
   def runJOINCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "JOIN"))
      
   def runDISJOINCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "DISJOIN"))
      
   def runPOLYGONCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "POLYGON"))
      
   def runDIMLINEARCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "DIMLINEAR"))

   def runDIMALIGNEDCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "DIMALIGNED"))

   def runDIMSTYLECommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "DIMSTYLE"))

   def runHELPCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "HELP"))

   def runLENGTHENCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "LENGTHEN"))

   def runOPTIONSCommand(self):
      self.runCommandAbortingTheCurrent(QadMsg.translate("Command_list", "OPTIONS"))
