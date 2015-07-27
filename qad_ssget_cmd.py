# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando da inserire in altri comandi per la selezione di un gruppo di feature
 
                              -------------------
        begin                : 2013-05-22
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
from qad_textwindow import *
from qad_entity import *
from qad_dim import *
from qad_getpoint import *
from qad_pline_cmd import QadPLINECommandClass
from qad_circle_cmd import QadCIRCLECommandClass
from qad_mpolygon_cmd import QadMPOLYGONCommandClass
# ho dovuto spostare in fondo questo import perché qad_mbuffer_cmd fa l'import di qad_ssget_cmd
#from qad_mbuffer_cmd import QadMBUFFERCommandClass
import qad_utils


#===============================================================================
# QadSSGetClass
#===============================================================================
class QadSSGetClass(QadCommandClass):
# Classe che gestisce la selezione di oggetti geometrici

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadSSGetClass(self.plugIn)
      
   def __init__(self, plugIn):
      self.init(plugIn)

   def __del__(self):
      QadCommandClass.__del__(self)
      self.entitySet.deselectOnLayer()

   def init(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.AddOnSelection = True # se = False significa remove
      self.entitySet = QadEntitySet()
      self.points = []
      self.currSelectionMode = ""
      # opzioni per limitare gli oggetti da selezionare
      self.onlyEditableLayers = False
      self.checkPointLayer = True
      self.checkLineLayer = True
      self.checkPolygonLayer = True
      self.checkDimLayers = True # include tutte le features che compongono le quotature selezionate
      
      self.help = False
      # se SingleSelection = True viene selezionato il primo oggetto o gruppo di oggetti indicato,
      # senza che vengano richieste altre selezioni.      
      self.SingleSelection = False
      # selezione degli oggetti aggiunti più recentemente al gruppo di selezione (x opzione annulla)
      self.lastEntitySet = QadEntitySet()
      self.PLINECommand = None
      self.CIRCLECommand = None
      self.MPOLYGONCommand = None
      self.MBUFFERCommand = None
      self.SSGetClass = None

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 4: # quando si é in fase di disegno linea
         return self.PLINECommand.getPointMapTool(drawMode)
      elif self.step == 5: # quando si é in fase di disegno cerchio
         return self.CIRCLECommand.getPointMapTool(drawMode)
      elif self.step == 6: # quando si é in fase di selezione entità
         return self.SSGetClass.getPointMapTool(drawMode)
      elif self.step == 7: # quando si é in fase di disegno polygono
         return self.MPOLYGONCommand.getPointMapTool(drawMode)
      elif self.step == 8: # quando si é in fase di disegno buffer 
         return self.MBUFFERCommand.getPointMapTool(drawMode)      
      else:
         ptMapTool = QadCommandClass.getPointMapTool(self, drawMode)
         ptMapTool.setSnapType(QadSnapTypeEnum.DISABLE)
         ptMapTool.setOrthoMode(0)
         return ptMapTool

   
   #============================================================================
   # getLayersToCheck
   #============================================================================
   def getLayersToCheck(self):     
      layerList = []
      for layer in self.plugIn.canvas.layers(): # Tutti i layer visibili visibili
         # considero solo i layer vettoriali che sono filtrati per tipo
         if (layer.type() == QgsMapLayer.VectorLayer) and \
             ((layer.geometryType() == QGis.Point and self.checkPointLayer == True) or \
              (layer.geometryType() == QGis.Line and self.checkLineLayer == True) or \
              (layer.geometryType() == QGis.Polygon and self.checkPolygonLayer == True)) and \
              (self.onlyEditableLayers == False or layer.isEditable()):
            # se devo includere i layers delle quotature
            if self.checkDimLayers == True or \
               len(self.plugIn.dimStyles.getDimListByLayer(layer)) == 0:
               layerList.append(layer)
         
      return layerList


   #============================================================================
   # showMsgOnAddRemove
   #============================================================================
   def showMsgOnAddRemove(self, found):
      msg = QadMsg.translate("Command_SSGET", " trovato(i) {0}, totale {1}")
      self.showMsg(msg.format(found, self.entitySet.count()), True) # ripete il prompt         

   #============================================================================
   # SetEntity
   #============================================================================
   def SetEntity(self, entity):
      # controllo sul layer
      if self.onlyEditableLayers == True and entity.layer.isEditable() == False:
         self.showMsgOnAddRemove(0)
         return
      # controllo sul tipo
      if (self.checkPointLayer == False and entity.layer.geometryType() == QGis.Point) or \
         (self.checkLineLayer == False and entity.layer.geometryType() == QGis.Line) or \
         (self.checkPolygonLayer == False and entity.layer.geometryType() == QGis.Polygon):
         self.showMsgOnAddRemove(0)
         return
      
      # controllo su layer delle quotature
      dimStyle, dimId = self.plugIn.dimStyles.getDimIdByEntity(entity)
      if self.checkDimLayers == False and dimStyle is not None:
         self.showMsgOnAddRemove(0)
         return
      
      for layerEntitySet in self.entitySet.layerEntitySetList:
         # se il layer non é quello di entity
         if entity.layerId() != layerEntitySet.layerId():            
            layerEntitySet.deselectOnLayer()
         else:
            layerEntitySet.deselectOnLayer()
      
      self.entitySet.deselectOnLayer()
      self.entitySet.clear()
      self.entitySet.addEntity(entity)

      if self.checkDimLayers == True and dimStyle is not None:
         # Mi ricavo tutti i componenti della quotatura
         dimEntity = QadDimEntity()
         dimEntity.initByDimId(dimStyle, dimId)
         # Aggiungo i componenenti della quotatura a set <entitySet>
         self.entitySet.unite(dimEntity.getEntitySet())

      self.showMsgOnAddRemove(self.entitySet.count())
      self.entitySet.selectOnLayer(False) # incremental = False
      self.lastEntitySet.clear()
      self.lastEntitySet.addEntity(entity)
    
   #============================================================================
   # SetSelSet
   #============================================================================
   def SetSelSet(self, selSet):
      for layerEntitySet in self.entitySet.layerEntitySetList:
         # se il layer non é presente in selSet
         if selSet.findLayerEntitySet(layerEntitySet) is None:            
            layerEntitySet.deselectOnLayer()
         else:
            layerEntitySet.deselectOnLayer()
            
      self.entitySet.set(selSet)

      if self.checkDimLayers == True:
         dimEntitySet = QadEntitySet(selSet)
         # La funzione verifica se le entità che fanno parte di un entitySet sono anche parte di quotatura e,
         # in caso affermativo, aggiunge tutti i componenti delle quotature all'entitySet.
         self.plugIn.dimStyles.addAllDimComponentsToEntitySet(dimEntitySet, self.onlyEditableLayers)
         self.entitySet.unite(dimEntitySet)

      self.showMsgOnAddRemove(self.entitySet.count())
      self.entitySet.selectOnLayer(False) # incremental = False
      self.lastEntitySet.set(selSet)

   #============================================================================
   # AddRemoveEntity
   #============================================================================
   def AddRemoveEntity(self, entity):
      # controllo sul layer
      if self.onlyEditableLayers == True and entity.layer.isEditable() == False:
         self.showMsgOnAddRemove(0)
         return
      # controllo sul tipo
      if (self.checkPointLayer == False and entity.layer.geometryType() == QGis.Point) or \
         (self.checkLineLayer == False and entity.layer.geometryType() == QGis.Line) or \
         (self.checkPolygonLayer == False and entity.layer.geometryType() == QGis.Polygon):
         self.showMsgOnAddRemove(0)
         return
      # controllo su layer delle quotature
      if self.checkDimLayers == False and len(self.plugIn.dimStyles.getDimListByLayer(entity.layer)) > 0:
         self.showMsgOnAddRemove(0)
         return
      
      self.entitySet.deselectOnLayer()
      if self.AddOnSelection == True: # aggiungi al gruppo di selezione
         self.entitySet.addEntity(entity)
      else: # rimuovi dal gruppo di selezione
         self.entitySet.removeEntity(entity)

      if self.checkDimLayers == True:
         dimEntitySet = QadEntitySet()
         dimEntitySet.addEntity(entity)
         # La funzione verifica se le entità che fanno parte di un entitySet sono anche parte di quotatura e,
         # in caso affermativo, aggiunge/rimuove tutti i componenti delle quotature all'entitySet.
         self.plugIn.dimStyles.addAllDimComponentsToEntitySet(dimEntitySet, self.onlyEditableLayers)
         if self.AddOnSelection == True: # aggiungi al gruppo di selezione
            self.entitySet.unite(dimEntitySet)
         else: # rimuovi dal gruppo di selezione
            self.entitySet.subtract(dimEntitySet)
         self.showMsgOnAddRemove(dimEntitySet.count())
      else:
         self.showMsgOnAddRemove(1)
         
      self.entitySet.selectOnLayer(False) # incremental = False
      self.lastEntitySet.clear()
      self.lastEntitySet.addEntity(entity)

   #============================================================================
   # AddRemoveSelSet
   #============================================================================
   def AddRemoveSelSet(self, selSet):
      self.entitySet.deselectOnLayer()
      if self.AddOnSelection == True: # aggiungi al gruppo di selezione
         self.entitySet.unite(selSet)
      else: # rimuovi dal gruppo di selezione
         self.entitySet.subtract(selSet)

      self.showMsgOnAddRemove(selSet.count())

      self.entitySet.selectOnLayer(False) # incremental = False
      self.lastEntitySet.set(selSet)

   #============================================================================
   # AddRemoveSelSetByFence
   #============================================================================
   def AddRemoveSelSetByFence(self, points):
      if len(points) > 1:
         selSet = qad_utils.getSelSet("F", self.getPointMapTool(), points, \
                                      self.getLayersToCheck())
         self.AddRemoveSelSet(selSet)

   #============================================================================
   # AddRemoveSelSetByPolygon
   #============================================================================
   def AddRemoveSelSetByPolygon(self, mode, points):
      if len(points) > 2:
         selSet = qad_utils.getSelSet(mode, self.getPointMapTool(), points, \
                                      self.getLayersToCheck())
         self.AddRemoveSelSet(selSet)

   #============================================================================
   # AddRemoveSelSetByGeometry
   #============================================================================
   def AddRemoveSelSetByGeometry(self, mode, geom):
      if type(geom) == QgsGeometry: # singola geometria
         selSet = qad_utils.getSelSet(mode, self.getPointMapTool(), geom, \
                                      self.getLayersToCheck())
         self.AddRemoveSelSet(selSet)
      else: # lista di geometrie
         selSet = QadEntitySet()
         for g in geom:
            partial = qad_utils.getSelSet(mode, self.getPointMapTool(), g, \
                                          self.getLayersToCheck())
            selSet.unite(partial)
         self.AddRemoveSelSet(selSet)

      
   #============================================================================
   # WaitForFirstPoint
   #============================================================================
   def WaitForFirstPoint(self):
      self.step = 1

      # "Finestra" "Ultimo" "Interseca"
      # "Riquadro" "Tutto" "iNTercetta"
      # "FPoligono" "IPoligono"
      # "FCerchio" "ICerchio"
      # "FOggetti" "IOggetti"
      # "FBuffer" "IBuffer"
      # "AGgiungi" "Elimina"
      # "Precedente" "Annulla"
      # "AUto" "SIngolo" "Help"
      keyWords = QadMsg.translate("Command_SSGET", "Finestra") + "/" + \
                 QadMsg.translate("Command_SSGET", "Ultimo") + "/" + \
                 QadMsg.translate("Command_SSGET", "Interseca") + "/" + \
                 QadMsg.translate("Command_SSGET", "Riquadro") + "/" + \
                 QadMsg.translate("Command_SSGET", "Tutto") + "/" + \
                 QadMsg.translate("Command_SSGET", "iNTercetta") + "/" + \
                 QadMsg.translate("Command_SSGET", "FPoligono") + "/" + \
                 QadMsg.translate("Command_SSGET", "IPoligono") + "/" + \
                 QadMsg.translate("Command_SSGET", "FCerchio") + "/" + \
                 QadMsg.translate("Command_SSGET", "ICerchio") + "/" + \
                 QadMsg.translate("Command_SSGET", "FOggetti") + "/" + \
                 QadMsg.translate("Command_SSGET", "IOggetti") + "/" + \
                 QadMsg.translate("Command_SSGET", "FBuffer") + "/" + \
                 QadMsg.translate("Command_SSGET", "IBuffer") + "/" + \
                 QadMsg.translate("Command_SSGET", "AGgiungi") + "/" + \
                 QadMsg.translate("Command_SSGET", "Elimina") + "/" + \
                 QadMsg.translate("Command_SSGET", "Precedente") + "/" + \
                 QadMsg.translate("Command_SSGET", "Annulla") + "/" + \
                 QadMsg.translate("Command_SSGET", "AUto") + "/" + \
                 QadMsg.translate("Command_SSGET", "SIngolo") + "/" + \
                 QadMsg.translate("Command_SSGET", "Help")
      englishKeyWords = "Window" + "/" + "Last" + "/" + "Crossing" + "/" + "Box" + "/" \
                         + "All" + "/" + "Fence" + "/" + "WPolygon" + "/" + "CPolygon" + "/" \
                         + "WCircle" + "/" + "CCircle" + "/" + "WObjects" + "/" + "CObjects" + "/" \
                         + "WBuffer" + "/" + "CBuffer" + "/" + "Add" + "/" + "Remove" + "/" \
                         + "Previous" + "/" + "Undo" + "/" + "AUto" + "/" + "SIngle" + "/" + "Help"
                 
      if self.AddOnSelection == True:
         prompt = QadMsg.translate("Command_SSGET", "Selezionare oggetti")
      else:
         prompt = QadMsg.translate("Command_SSGET", "Rimuovere oggetti")
                           
      if self.help == True:         
         prompt = prompt + QadMsg.translate("Command_SSGET", " o [{0}]").format(keyWords)                        
         
      prompt = prompt + QadMsg.translate("Command_SSGET", ": ")
            
      # imposto il map tool
      self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION)
      self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.NONE)
      # imposto i layer da controllare sul maptool
      self.getPointMapTool().layersToCheck = self.getLayersToCheck()
      self.points = []
           
      keyWords += "_" + englishKeyWords
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)
      return

   def run(self, msgMapTool = False, msg = None):
      # ritorna:
      # True per selezione non terminata
      # False per selezione terminata
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # errore
            
      #=========================================================================
      # RICHIESTA PRIMO PUNTO PER SELEZIONE OGGETTI
      if self.step == 0:
         self.WaitForFirstPoint()
         return False # continua
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PRIMO PUNTO PER SELEZIONE OGGETTI
      elif self.step == 1: # dopo aver atteso un punto o enter o una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.entitySet.count() > 0:
                     self.plugIn.setLastEntitySet(self.entitySet)
                  return True # fine
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False # continua
            
            shiftKey = self.getPointMapTool().shiftKey

            # se é stata selezionata un'entità
            if self.getPointMapTool().entity.isInitialized():
               value = self.getPointMapTool().entity
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            shiftKey = False
            value = msg

         if value is None:
            if self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
            return True # fine

         if type(value) == unicode:
            self.currSelectionMode = value
            
            if value == QadMsg.translate("Command_SSGET", "Finestra") or value == "Window" or \
               value == QadMsg.translate("Command_SSGET", "Interseca") or value == "Crossing":
               # "Finestra" = Seleziona tutti gli oggetti che si trovano completamente all'interno di un rettangolo definito da due punti
               # "Interseca" = Seleziona gli oggetti che intersecano o si trovano all'interno di un'area definita da due punti
               # imposto il map tool
               self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
               self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.NONE)
               # si appresta ad attendere un punto
               self.waitForPoint(value == QadMsg.translate("Command_SSGET", "Specificare primo angolo: "))
               self.step = 2
            if value == QadMsg.translate("Command_SSGET", "Ultimo") or value == "Last": 
               # Seleziona l'ultima entità inserita
               if self.plugIn.getLastEntity() is None:
                  self.showMsgOnAddRemove(0)
               else:
                  self.AddRemoveEntity(self.plugIn.getLastEntity())              
                  if self.SingleSelection == True and self.entitySet.count() > 0:
                     self.plugIn.setLastEntitySet(self.entitySet)
                     return True # fine               
               self.WaitForFirstPoint()                          
            elif value == QadMsg.translate("Command_SSGET", "Riquadro") or value == "Box":
               # Seleziona tutti gli oggetti che intersecano o si trovano all'interno di un rettangolo specificato da due punti.
               # Se i punti del rettangolo sono specificati da destra a sinistra, Riquadro equivale ad Interseca,
               # altrimenti é equivalente a Finestra
               # imposto il map tool
               self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
               self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.NONE)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.translate("Command_SSGET", "Specificare primo angolo: "))
               self.step = 2           
            elif value == QadMsg.translate("Command_SSGET", "Tutto") or value == "All":
               # Seleziona tutti gli oggetti 
               selSet = qad_utils.getSelSet("X", self.getPointMapTool(), None, \
                                            self.getLayersToCheck())
               self.SetSelSet(selSet)
               if self.SingleSelection == True and self.entitySet.count() > 0:
                  self.plugIn.setLastEntitySet(self.entitySet)
                  return True # fine         
               self.WaitForFirstPoint()
            elif value == QadMsg.translate("Command_SSGET", "iNTercetta") or value == "Fence":
               # Seleziona tutti gli oggetti che intersecano una polilinea
               self.PLINECommand = QadPLINECommandClass(self.plugIn)
               # se questo flag = True il comando serve all'interno di un altro comando per disegnare una linea
               # che non verrà salvata su un layer
               self.PLINECommand.virtualCmd = True   
               self.PLINECommand.run(msgMapTool, msg)
               self.step = 4
            elif value == QadMsg.translate("Command_SSGET", "FPoligono") or value == "WPolygon" or \
                 value == QadMsg.translate("Command_SSGET", "IPoligono") or value == "CPolygon":
               # "FPoligono" = Seleziona oggetti che si trovano completamente all'interno di un poligono definito da punti
               # "IPoligono" = Seleziona gli oggetti che intersecano o si trovano all'interno di un poligono definito specificando dei punti
               self.MPOLYGONCommand = QadMPOLYGONCommandClass(self.plugIn)
               # se questo flag = True il comando serve all'interno di un altro comando per disegnare una linea
               # che non verrà salvata su un layer
               self.MPOLYGONCommand.virtualCmd = True   
               self.MPOLYGONCommand.run(msgMapTool, msg)
               self.step = 7
            elif value == QadMsg.translate("Command_SSGET", "FCerchio") or value == "WCircle" or \
                 value == QadMsg.translate("Command_SSGET", "ICerchio") or value == "CCircle":
               # "FCerchio" = Seleziona oggetti che si trovano completamente all'interno di un cerchio
               # "ICerchio" = Seleziona oggetti che intersecano o si trovano all'interno di un cerchio
               self.CIRCLECommand = QadCIRCLECommandClass(self.plugIn)
               # se questo flag = True il comando serve all'interno di un altro comando per disegnare un cerchio
               # che non verrà salvata su un layer
               self.CIRCLECommand.virtualCmd = True   
               self.CIRCLECommand.run(msgMapTool, msg)
               self.step = 5
            elif value == QadMsg.translate("Command_SSGET", "FOggetti") or value == "WObjects" or \
                 value == QadMsg.translate("Command_SSGET", "IOggetti") or value == "CObjects":
               # "FOggetti" = Seleziona oggetti che si trovano completamente all'interno di oggetti da selezionare
               # "IOggetti" = Seleziona oggetti che intersecano o si trovano all'interno di oggetti da selezionare
               self.SSGetClass = QadSSGetClass(self.plugIn)
               self.SSGetClass.run(msgMapTool, msg)
               self.step = 6
            elif value == QadMsg.translate("Command_SSGET", "FBuffer") or value == "WBuffer" or \
                 value == QadMsg.translate("Command_SSGET", "IBuffer") or value == "CBuffer":
               # "FBuffer" = Seleziona oggetti che si trovano completamente all'interno di buffer intorno ad oggetti da selezionare
               # "IBuffer" = Seleziona oggetti che intersecano o si trovano all'interno di buffer intorno ad oggetti da selezionare
               self.MBUFFERCommand = QadMBUFFERCommandClass(self.plugIn)
               # se questo flag = True il comando serve all'interno di un altro comando per disegnare un cerchio
               # che non verrà salvata su un layer
               self.MBUFFERCommand.virtualCmd = True   
               self.MBUFFERCommand.run(msgMapTool, msg)
               self.step = 8
            elif value == QadMsg.translate("Command_SSGET", "AGgiungi") or value == "Add":
               # Passa al metodo Aggiungi: gli oggetti selezionati possono essere aggiunti al gruppo di selezione 
               self.AddOnSelection = True
               self.WaitForFirstPoint()
            elif value == QadMsg.translate("Command_SSGET", "Elimina") or value == "Remove":
               # Passa al metodo Rimuovi: gli oggetti possono essere rimossi dal gruppo di selezione
               self.AddOnSelection = False
               self.WaitForFirstPoint()
            elif value == QadMsg.translate("Command_SSGET", "Precedente") or value == "Previous":
               # Seleziona il gruppo di selezione più recente
               if self.plugIn.lastEntitySet is None:
                  self.showMsgOnAddRemove(0)
               else:
                  entitySet = QadEntitySet()
                  entitySet.set(self.plugIn.lastEntitySet)
                  # controllo sul layer                  
                  if self.onlyEditableLayers == True:
                     entitySet.removeNotEditable()
                  # controllo sul tipo
                  if self.checkPointLayer == False:
                     entitySet.removeGeomType(QGis.Point)
                  if self.checkLineLayer == False:
                     entitySet.removeGeomType(QGis.Line)
                  if self.checkPolygonLayer == False:
                     entitySet.removeGeomType(QGis.Polygon)
                  # controllo sulle quotature
                  if self.checkDimLayers == False:
                     self.plugIn.dimStyles.removeAllDimLayersFromEntitySet(entitySet)
                     
                  entitySet.removeNotExisting()
                  self.AddRemoveSelSet(entitySet)            
                  if self.SingleSelection == True and self.entitySet.count() > 0:
                     self.plugIn.setLastEntitySet(self.entitySet)
                     return True # fine                                   
               self.WaitForFirstPoint()
            elif value == QadMsg.translate("Command_SSGET", "Annulla") or value == "Undo":
               # Annulla la selezione dell'oggetto aggiunto più recentemente al gruppo di selezione.
               # Inverto il tipo di selezione
               prevAddOnSelection = self.AddOnSelection
               self.AddOnSelection = not self.AddOnSelection
               self.AddRemoveSelSet(self.lastEntitySet)               
               # Ripristino il tipo di selezione
               self.AddOnSelection = prevAddOnSelection
               if self.SingleSelection == True and self.entitySet.count() > 0:
                  self.plugIn.setLastEntitySet(self.entitySet)
                  return True # fine               
               self.WaitForFirstPoint()
            elif value == QadMsg.translate("Command_SSGET", "AUto") or value == "AUto":
               # Passa alla selezione automatica: vengono selezionati gli oggetti sui quali si posiziona il puntatore.
               # Facendo clic su un'area vuota all'interno o all'esterno di un oggetto, 
               # si crea il primo angolo di un rettangolo di selezione, come per il metodo Riquadro
               self.SingleSelection = False
               self.WaitForFirstPoint()
            elif value == QadMsg.translate("Command_SSGET", "SIngolo") or value == "SIngle":
               # Passa al metodo Singolo: viene selezionato il primo oggetto o gruppo di oggetti indicato,
               # senza che vengano richieste altre selezioni.
               self.SingleSelection = True
               if self.entitySet.count() > 0:
                  self.plugIn.setLastEntitySet(self.entitySet)
                  return True # fine               
               self.WaitForFirstPoint()
            elif value == QadMsg.translate("Command_SSGET", "Help") or value == "Help":
               self.help = True
               self.WaitForFirstPoint()
         elif type(value) == QgsPoint: # se é stato inserito il punto iniziale del rettangolo
            self.currSelectionMode = QadMsg.translate("Command_SSGET", "Riquadro")
            self.points.append(value)           
            self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.ENTITYSET_SELECTION)
            self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_RECTANGLE)        
            self.getPointMapTool().setStartPoint(value)
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_SSGET", "Specificare angolo opposto: "))
            self.step = 3
         else: # se é stata selezionata un'entità
            # se la selezione é avvenuta con shift premuto o se si deve rimuovere l'entità dal gruppo
            if shiftKey or self.AddOnSelection == False:
               self.AddRemoveEntity(value)
            else:
               self.SetEntity(value)
               
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine               

            self.WaitForFirstPoint()
          
         return False # continua

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL PRIMO PUNTO DEL RETTANGOLO DA OPZIONE 
      # FINESTRA, INTERSECA, RIQUADRO (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  self.showMsg(QadMsg.translate("Command_SSGET", "La finestra non é stata specificata correttamente."))
                  self.WaitForFirstPoint()
                  return False
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
                        
         if type(value) == QgsPoint:
            self.points.append(value)           
            self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.ENTITYSET_SELECTION)
            self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_RECTANGLE)        
            self.getPointMapTool().setStartPoint(value)
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_SSGET", "Specificare angolo opposto: "))
            self.step = 3
         else:
            self.showMsg(QadMsg.translate("Command_SSGET", "La finestra non é stata specificata correttamente."))
            self.WaitForFirstPoint()

         return False # continua


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL SECONDO PUNTO DEL RETTANGOLO (da step = 1)
      elif self.step == 3: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  self.showMsg(QadMsg.translate("Command_SSGET", "La finestra non é stata specificata correttamente."))
                  # si appresta ad attendere un punto
                  self.waitForPoint(QadMsg.translate("Command_SSGET", "Specificare angolo opposto: "))
                  return False
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            shiftKey = self.getPointMapTool().shiftKey
            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            shiftKey = False
            value = msg
                        
         if type(value) == QgsPoint:
            self.points.append(value)
            
            if self.currSelectionMode == QadMsg.translate("Command_SSGET", "Riquadro") or \
               self.currSelectionMode == "Box":
               if self.points[0].x() < value.x():
                  mode = "W"
               else:
                  mode = "C"
            elif self.currSelectionMode == QadMsg.translate("Command_SSGET", "Finestra") or \
               self.currSelectionMode == "Window": 
               mode = "W"
            else: # "Interseca"
               mode = "C"
               
            selSet = qad_utils.getSelSet(mode, self.getPointMapTool(), self.points, \
                                         self.getLayersToCheck())
            # se la selezione é avvenuta con shift premuto o se si deve rimuovere il gruppo selSet dal gruppo
            if shiftKey or self.AddOnSelection == False:
               self.AddRemoveSelSet(selSet)
            else:
               self.SetSelSet(selSet)
         
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine
            
            self.WaitForFirstPoint()
         else:
            self.showMsg(QadMsg.translate("Command_SSGET", "La finestra non é stata specificata correttamente."))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_SSGET", "Specificare angolo opposto: "))

         return False # continua


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO PER MODALITA' INTERCETTA (da step = 1 o 4)
      elif self.step == 4: # dopo aver atteso un punto si riavvia il comando
         if self.PLINECommand.run(msgMapTool, msg) == True:
            self.showMsg("\n")
            self.AddRemoveSelSetByFence(self.PLINECommand.vertices)
            del self.PLINECommand
            self.PLINECommand = None
         
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine
            
            self.WaitForFirstPoint()
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PER MODALITA' FCERCHIO e ICERCHIO (da step = 1 o 5)
      elif self.step == 5: # dopo aver atteso un punto si riavvia il comando
         if self.CIRCLECommand.run(msgMapTool, msg) == True:
            self.showMsg("\n")
            if (self.CIRCLECommand.centerPt is not None) and \
               (self.CIRCLECommand.radius is not None):
               circle = QadCircle()
               circle.set(self.CIRCLECommand.centerPt, self.CIRCLECommand.radius)
               points = circle.asPolyline()
               if self.currSelectionMode == QadMsg.translate("Command_SSGET", "FCerchio") or \
                  self.currSelectionMode == "WCircle":
                  self.AddRemoveSelSetByPolygon("WP", points)
               elif self.currSelectionMode == QadMsg.translate("Command_SSGET", "ICerchio") or \
                  self.currSelectionMode == "CCircle":
                  self.AddRemoveSelSetByPolygon("CP", points)               
            
            del self.CIRCLECommand
            self.CIRCLECommand = None
         
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine
            
            self.WaitForFirstPoint()
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI SELEZIONE DI OGGETTI PER MODALITA' FOGGETTI e IOGGETTI (da step = 1 o 6)
      elif self.step == 6: # dopo aver atteso un punto si riavvia il comando
         if self.SSGetClass.run(msgMapTool, msg) == True:
            self.showMsg("\n")
            destCRS = self.SSGetClass.getPointMapTool().canvas.mapRenderer().destinationCrs()
            geoms = self.SSGetClass.entitySet.getGeometryCollection(destCRS) # trasformo la geometria
            
            if self.currSelectionMode == QadMsg.translate("Command_SSGET", "FOggetti") or \
               self.currSelectionMode == "WObjects":
               self.AddRemoveSelSetByGeometry("WO", geoms)
            elif self.currSelectionMode == QadMsg.translate("Command_SSGET", "IOggetti") or \
               self.currSelectionMode == "CObjects":
               self.AddRemoveSelSetByGeometry("CO", geoms)
                                 
            del self.SSGetClass
            self.SSGetClass = None
         
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine
            
            self.WaitForFirstPoint()
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PER MODALITA' FPOLIGONO e IPOLIGONO (da step = 1 o 7)
      elif self.step == 7: # dopo aver atteso un punto si riavvia il comando
         if self.MPOLYGONCommand.run(msgMapTool, msg) == True:
            self.showMsg("\n")              
            if self.currSelectionMode == QadMsg.translate("Command_SSGET", "FPoligono") or \
               self.currSelectionMode == "WPolygon":
               self.AddRemoveSelSetByPolygon("WP", self.MPOLYGONCommand.vertices)
            elif self.currSelectionMode == QadMsg.translate("Command_SSGET", "IPoligono") or \
               self.currSelectionMode == "CPolygon":
               self.AddRemoveSelSetByPolygon("CP", self.MPOLYGONCommand.vertices)               
            
            del self.MPOLYGONCommand
            self.MPOLYGONCommand = None
         
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine
            
            self.WaitForFirstPoint()
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI SELEZIONE DI OGGETTI PER MODALITA' FBUFFER e IBUFFER (da step = 1 o 8)
      elif self.step == 8: # dopo aver atteso un punto si riavvia il comando
         if self.MBUFFERCommand.run(msgMapTool, msg) == True:
            self.showMsg("\n")

            bufferGeoms = []
            for layerEntitySet in self.MBUFFERCommand.entitySet.layerEntitySetList:
               geoms = layerEntitySet.getGeometryCollection()
               width = qad_utils.distMapToLayerCoordinates(self.MBUFFERCommand.width, \
                                                           self.MBUFFERCommand.getPointMapTool().canvas,\
                                                           layerEntitySet.layer)
               for geom in geoms:
                  bufferGeoms.append(geom.buffer(width, self.MBUFFERCommand.segments))
                        
            if self.currSelectionMode == QadMsg.translate("Command_SSGET", "FBuffer") or \
               self.currSelectionMode == "WBuffer":
               self.AddRemoveSelSetByGeometry("WO", bufferGeoms)
            elif self.currSelectionMode == QadMsg.translate("Command_SSGET", "IBuffer") or \
               self.currSelectionMode == "CBuffer":
               self.AddRemoveSelSetByGeometry("CO", bufferGeoms) or \
               self.currSelectionMode == "CPolygon"
                                 
            del self.MBUFFERCommand
            self.MBUFFERCommand = None
         
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine
            
            self.WaitForFirstPoint()
         return False


# ho dovuto spostare in fondo questo import perché qad_mbuffer_cmd fa l'import di qad_ssget_cmd
from qad_mbuffer_cmd import QadMBUFFERCommandClass
