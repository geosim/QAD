# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando MOVE per spostare oggetti
 
                              -------------------
        begin                : 2013-09-27
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


from qad_move_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_textwindow import *
from qad_ssget_cmd import QadSSGetClass
from qad_entity import *
import qad_utils
import qad_layer
from qad_dim import *


# Classe che gestisce il comando MOVE
class QadMOVECommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "SPOSTA")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runMOVECommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/move.png")

   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_MOVE", "Sposta gli oggetti selezionati.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.SSGetClass = QadSSGetClass(plugIn)
      self.SSGetClass.onlyEditableLayers = True
      self.entitySet = QadEntitySet()
      self.basePt = QgsPoint()

   def __del__(self):
      QadCommandClass.__del__(self)
      del self.SSGetClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 0: # quando si é in fase di selezione entità
         return self.SSGetClass.getPointMapTool()
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_move_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None



   #============================================================================
   # move
   #============================================================================
   def move(self, f, offSetX, offSetY, layerEntitySet, entitySet, dimStyle):
      if dimStyle is not None:
         entity = QadEntity()
         entity.set(layerEntitySet.layer, f.id())
         dimEntity = QadDimEntity()
         if dimEntity.initByEntity(dimStyle, entity) == False:
            dimEntity = None
      else:
         dimEntity = None
      
      if dimEntity is None:
         # sposto la feature e la rimuovo da entitySet (é la prima)
         f.setGeometry(qad_utils.moveQgsGeometry(f.geometry(), offSetX, offSetY))
         # plugIn, layer, feature, refresh, check_validity
         if qad_layer.updateFeatureToLayer(self.plugIn, layerEntitySet.layer, f, False, False) == False:
            return False
         del layerEntitySet.featureIds[0]
      else:
         # sposto la quota e la rimuovo da entitySet
         dimEntitySet = dimEntity.getEntitySet()
         if dimEntity.deleteToLayers(self.plugIn) == False:
            return False                     
         if dimEntity.move(offSetX, offSetY) == False:
            return False             
         if dimEntity.addToLayers(self.plugIn) == False:
            return False             
         entitySet.subtract(dimEntitySet)
            
      return True


   #============================================================================
   # moveGeoms
   #============================================================================
   def moveGeoms(self, newPt):      
      # copio entitySet
      entitySet = QadEntitySet(self.entitySet)
      
      self.plugIn.beginEditCommand("Feature moved", entitySet.getLayerList())
      
      for layerEntitySet in entitySet.layerEntitySetList:                        
         layer = layerEntitySet.layer
         
         # verifico se il layer appartiene ad uno stile di quotatura
         dimStyle = self.plugIn.dimStyles.getDimByLayer(layer)

         movedObjects = []
         transformedBasePt = self.mapToLayerCoordinates(layerEntitySet.layer, self.basePt)
         transformedNewPt = self.mapToLayerCoordinates(layerEntitySet.layer, newPt)
         offSetX = transformedNewPt.x() - transformedBasePt.x()
         offSetY = transformedNewPt.y() - transformedBasePt.y()
         
         while len(layerEntitySet.featureIds) > 0:
            featureId = layerEntitySet.featureIds[0]
            f = layerEntitySet.getFeature(featureId)
            
            if self.move(f, offSetX, offSetY, layerEntitySet, entitySet, dimStyle) == False:  
               self.plugIn.destroyEditCommand()
               return
   
      self.plugIn.endEditCommand()

   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando
            
      #=========================================================================
      # RICHIESTA SELEZIONE OGGETTI
      if self.step == 0: # inizio del comando
         if self.SSGetClass.run(msgMapTool, msg) == True:
            # selezione terminata
            self.step = 1
            self.getPointMapTool().refreshSnapType() # aggiorno lo snapType che può essere variato dal maptool di selezione entità                    
            return self.run(msgMapTool, msg)
      
      #=========================================================================
      # SPOSTA OGGETTI
      elif self.step == 1:
         self.entitySet.set(self.SSGetClass.entitySet)
         
         if self.entitySet.count() == 0:
            return True # fine comando

         # imposto il map tool
         self.getPointMapTool().entitySet.set(self.entitySet)
         self.getPointMapTool().setMode(Qad_move_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_BASE_PT)                                
   
         keyWords = QadMsg.translate("Command_MOVE", "Spostamento")
         prompt = QadMsg.translate("Command_MOVE", "Specificare punto base o [{0}] <{0}>: ").format(keyWords)
         
         # si appresta ad attendere un punto o enter o una parola chiave         
         # msg, inputType, default, keyWords, nessun controllo
         self.waitFor(prompt, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NONE)      
         self.step = 2      
         return False
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO BASE (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  pass # opzione di default "spostamento"
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None or type(value) == unicode:
            self.basePt.set(0, 0)
            self.getPointMapTool().basePt = self.basePt
            self.getPointMapTool().setMode(Qad_move_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_MOVE_PT)                                
            # si appresta ad attendere un punto
            msg = QadMsg.translate("Command_MOVE", "Specificare lo spostamento dal punto di origine 0,0 <{0}, {1}>: ")
            # msg, inputType, default, keyWords, nessun controllo
            self.waitFor(msg.format(str(self.plugIn.lastOffsetPt.x()), str(self.plugIn.lastOffsetPt.y())), \
                         QadInputTypeEnum.POINT2D, \
                         self.plugIn.lastOffsetPt, \
                         "", QadInputModeEnum.NONE)                                      
            self.step = 4           
         elif type(value) == QgsPoint: # se é stato inserito il punto base
            self.basePt.set(value.x(), value.y())

            # imposto il map tool
            self.getPointMapTool().basePt = self.basePt
            self.getPointMapTool().setMode(Qad_move_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_MOVE_PT)                                
            
            # si appresta ad attendere un punto o enter o una parola chiave         
            # msg, inputType, default, keyWords, nessun controllo
            self.waitFor(QadMsg.translate("Command_MOVE", "Specificare secondo punto oppure <Utilizza primo punto come spostamento dal punto di origine 0,0>: "), \
                         QadInputTypeEnum.POINT2D, \
                         None, \
                         "", QadInputModeEnum.NONE)      
            self.step = 3      
         
         return False 
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER SPOSTAMENTO (da step = 2)
      elif self.step == 3: # dopo aver atteso un punto o un numero reale si riavvia il comando
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
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            newPt = QgsPoint(self.basePt.x() * 2, self.basePt.y() * 2)
            self.moveGeoms(newPt)
         elif type(value) == QgsPoint: # se é stato inserito lo spostamento con un punto
            self.moveGeoms(value)
            
         return True # fine comando
               
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL PUNTO DI SPOSTAMENTO (da step = 2)
      elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
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
         else: # il punto arriva come parametro della funzione
            value = msg

         self.plugIn.setLastOffsetPt(value)
         self.moveGeoms(value)
         return True