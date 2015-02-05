# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando da inserire in altri comandi per la selezione di una feature
 
                              -------------------
        begin                : 2013-09-18
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
from qad_getpoint import *
import qad_utils


#===============================================================================
# QadEntSelClass
#===============================================================================
class QadEntSelClass(QadCommandClass):
      
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.entity = QadEntity()
      self.point = None
      # opzioni per limitare gli oggetti da selezionare
      self.onlyEditableLayers = False     
      self.checkPointLayer = True
      self.checkLineLayer = True
      self.checkPolygonLayer = True
      self.checkDimLayers = True # include tutte le features che compongono le quotature selezionate      
      self.msg = QadMsg.translate("QAD", "Selezionare oggetto: ")
      
   def __del__(self):
      QadCommandClass.__del__(self)
      if self.entity.isInitialized():
         self.entity.deselectOnLayer()      


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
               self.plugIn.dimStyles.getDimByLayer(layer) is None:
               layerList.append(layer)
         
      return layerList

            
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando

      #=========================================================================
      # RICHIESTA PUNTO o ENTITA'
      if self.step == 0: # inizio del comando
         # imposto il map tool
         self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION)
         # imposto i layer da controllare sul maptool
         self.getPointMapTool().layersToCheck = self.getLayersToCheck()
                  
         keyWords = QadMsg.translate("Command_ENTSEL", "Ultimo")
                  
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
            if value == QadMsg.translate("Command_ENTSEL", "Ultimo"):
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
                        if self.checkDimLayers == True or self.plugIn.dimStyles.getDimByLayer(layer) is None:
                           self.entity.set(lastEnt.layer, lastEnt.featureId)
                           self.entity.selectOnLayer()
         elif type(value) == QgsPoint:
            if entity is None:
               # cerco se ci sono entità nel punto indicato
               result = qad_utils.getEntSel(self.getPointMapTool().toCanvasCoordinates(value),
                                            self.getPointMapTool(), \
                                            self.getLayersToCheck())
               if result is not None:
                  feature = result[0]
                  layer = result[1]
                  self.entity.set(layer, feature.id())               
                  self.entity.selectOnLayer()
            else:
               self.entity.set(entity.layer, entity.featureId)
               self.entity.selectOnLayer()

            self.point = value
                                   
         return True # fine comando
         
