# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando da inserire in altri comandi per la selezione di una feature
 
                              -------------------
        begin                : 2013-09-18
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


# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *


from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_textwindow import *
from qad_entity import *
from qad_getpoint import *
import qad_utils


#===============================================================================
# QadEntSelClass
#===============================================================================
class QadEntSelClass(QadCommandClass):
   """
      Questa classe seleziona un'entità. Non è in grado di selezionare una quotatura ma solo un componente di una quotatura.
   """

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadEntSelClass(self.plugIn)
      
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.entity = QadEntity()
      self.point = None
      # opzioni per limitare gli oggetti da selezionare
      self.onlyEditableLayers = False     
      self.checkPointLayer = True
      self.checkLineLayer = True
      self.checkPolygonLayer = True
      self.checkDimLayers = True
      self.selDimEntity = False # per restituire o meno un oggetto QadDimEntity
      self.msg = QadMsg.translate("QAD", "Select object: ")
      
   def __del__(self):
      QadCommandClass.__del__(self)
      if self.entity.isInitialized():
         self.entity.deselectOnLayer()


   #============================================================================
   # setEntity
   #============================================================================
   def setEntity(self, layer, fid):
      del self.entity
      if self.selDimEntity: # se è possibile restituire un oggetto QadDimEntity
         # verifico se l'entità appartiene ad uno stile di quotatura
         self.entity = self.plugIn.dimStyles.getDimEntity(layer, fid)
         if self.entity is None: # se non è una quota
            self.entity = QadEntity()
            self.entity.set(layer, fid)
      else:
         self.entity = QadEntity()
         self.entity.set(layer, fid)
      
      self.entity.selectOnLayer()


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

            
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
         return True # fine comando

      #=========================================================================
      # RICHIESTA PUNTO o ENTITA'
      if self.step == 0: # inizio del comando
         # imposto il map tool
         self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION)
         # imposto i layer da controllare sul maptool
         self.getPointMapTool().layersToCheck = self.getLayersToCheck()
                  
         keyWords = QadMsg.translate("Command_ENTSEL", "Last")
                  
         englishKeyWords = "Last"
         keyWords += "_" + englishKeyWords
         # si appresta ad attendere un punto o enter o una parola chiave         
         # msg, inputType, default, keyWords, nessun controllo
         self.waitFor(self.msg, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NONE)
         
         self.step = 1
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO o ENTITA'
      elif self.step == 1: # dopo aver atteso un punto si riavvia il comando
         entity = None
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
               
            value = self.getPointMapTool().point
            if self.getPointMapTool().entity.isInitialized():
               entity = self.getPointMapTool().entity               
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            return True # fine comando
         
         if type(value) == unicode:
            if value == QadMsg.translate("Command_ENTSEL", "Last") or value == "Last":
               # Seleziona l'ultima entità inserita
               lastEnt = self.plugIn.getLastEntity()
               if lastEnt is not None:
                  # controllo sul layer
                  if self.onlyEditableLayers == False or lastEnt.layer.isEditable() == True:
                     # controllo sul tipo
                     if (self.checkPointLayer == True and entity.layer.geometryType() == QGis.Point) or \
                        (self.checkLineLayer == True and entity.layer.geometryType() == QGis.Line) or \
                        (self.checkPolygonLayer == True and entity.layer.geometryType() == QGis.Polygon):
                        # controllo su layer delle quotature
                        if self.checkDimLayers == True or len(self.plugIn.dimStyles.getDimListByLayer(layer)) == 0:
                           self.setEntity(lastEnt.layer, lastEnt.featureId)
         elif type(value) == QgsPoint:
            if entity is None:
               # cerco se ci sono entità nel punto indicato
               result = qad_utils.getEntSel(self.getPointMapTool().toCanvasCoordinates(value),
                                            self.getPointMapTool(), \
                                            self.getLayersToCheck())
               if result is not None:
                  feature = result[0]
                  layer = result[1]
                  self.setEntity(layer, feature.id())               
            else:
               self.setEntity(entity.layer, entity.featureId)

            self.point = value
                                   
         return True # fine comando
         
