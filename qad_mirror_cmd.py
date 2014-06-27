# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando MIRROR per spostare oggetti
 
                              -------------------
        begin                : 2013-12-11
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


import qad_debug
from qad_mirror_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_textwindow import *
from qad_ssget_cmd import QadSSGetClass
from qad_entity import *
import qad_utils
import qad_layer
import qad_label


# Classe che gestisce il comando MIRROR
class QadMIRRORCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "SPECCHIO")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runMIRRORCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/mirror.png")

   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_MIRROR", "Crea una copia speculare degli oggetti selezionati.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.SSGetClass = QadSSGetClass(plugIn)
      self.SSGetClass.onlyEditableLayers = True
      self.entitySet = QadEntitySet()
      self.firstMirrorPt = QgsPoint()
      self.secondMirrorPt = QgsPoint()
      self.copyFeatures = True

   def __del__(self):
      QadCommandClass.__del__(self)
      del self.SSGetClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 0: # quando si è in fase di selezione entità
         return self.SSGetClass.getPointMapTool()
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_mirror_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None


   #============================================================================
   # scale
   #============================================================================
   def mirror(self, f, pt1, pt2, rotFldName, layerEntitySet, entitySet, dimStyle):
      if dimStyle is not None:
         entity = QadEntity()
         entity.set(layerEntitySet.layer, f.id())
         dimEntity = QadDimEntity()
         if dimEntity.initByEntity(dimStyle, entity) == False:
            dimEntity = None
      else:
         dimEntity = None
      
      if dimEntity is None:
         # scalo la feature e la rimuovo da entitySet (è la prima)
         f.setGeometry(qad_utils.mirrorQgsGeometry(f.geometry(), pt1, pt2))
         if rotFldName is not None:
            #qad_debug.breakPoint()
            rotValue = f.attribute(rotFldName)
            rotValue = 0 if rotValue is None else qad_utils.toRadians(rotValue) # la rotazione è in gradi nel campo della feature
            ptDummy = qad_utils.getPolarPointByPtAngle(pt1, rotValue, 1)
            mirrorAngle = qad_utils.getAngleBy2Pts(pt1, pt2)
            ptDummy = qad_utils.mirrorPoint(ptDummy, pt1, mirrorAngle)
            rotValue = qad_utils.getAngleBy2Pts(pt1, ptDummy)
            f.setAttribute(rotFldName, qad_utils.toDegrees(qad_utils.normalizeAngle(rotValue)))               
                  
         if self.copyFeatures == False:
            # plugIn, layer, feature, refresh, check_validity
            if qad_layer.updateFeatureToLayer(self.plugIn, layerEntitySet.layer, f, False, False) == False:
               self.plugIn.destroyEditCommand()
               return False
         else:             
            # plugIn, layer, features, coordTransform, refresh, check_validity
            if qad_layer.addFeatureToLayer(self.plugIn, layerEntitySet.layer, f, None, False, False) == False:
               self.plugIn.destroyEditCommand()
               return False

         del layerEntitySet.featureIds[0]
      else:
         # scalo la quota e la rimuovo da entitySet
         mirrorAngle = qad_utils.getAngleBy2Pts(pt1, pt2)
         dimEntitySet = dimEntity.getEntitySet()
         if self.copyFeatures == False:
            if dimEntity.deleteToLayers(self.plugIn) == False:
               return False                      
         dimEntity.mirror(self.plugIn, pt1, mirrorAngle)
         if dimEntity.addToLayers(self.plugIn) == False:
            return False             
         entitySet.subtract(dimEntitySet)


   #============================================================================
   # mirrorGeoms
   #============================================================================
   def mirrorGeoms(self):      
      # copio entitySet
      entitySet = QadEntitySet(self.entitySet)

      self.plugIn.beginEditCommand("Feature mirrored", self.entitySet.getLayerList())
      #qad_debug.breakPoint()
      for layerEntitySet in entitySet.layerEntitySetList:
         layer = layerEntitySet.layer
         
         # verifico se il layer appartiene ad uno stile di quotatura
         dimStyle = self.plugIn.dimStyles.getDimByLayer(layer)

         transformedBasePt = self.mapToLayerCoordinates(layer, self.firstMirrorPt)
         transformedNewPt = self.mapToLayerCoordinates(layer, self.secondMirrorPt)
         
         rotFldName = None
         if qad_layer.isTextLayer(layer):
            # se la rotazione dipende da un solo campo
            rotFldNames = qad_label.get_labelRotationFieldNames(layer)
            if len(rotFldNames) == 1 and len(rotFldNames[0]) > 0:
               rotFldName = rotFldNames[0]         
         elif qad_layer.isSymbolLayer(layer):
            rotFldName = qad_layer.get_symbolRotationFieldName(layer)
         
         while len(layerEntitySet.featureIds) > 0:
            featureId = layerEntitySet.featureIds[0]
            f = layerEntitySet.getFeature(featureId)

            if self.mirror(f, transformedBasePt, transformedNewPt, rotFldName, layerEntitySet, entitySet, dimStyle) == False:  
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
      # SPECCHIA OGGETTI
      elif self.step == 1:
         self.entitySet.set(self.SSGetClass.entitySet)
         
         if self.entitySet.count() == 0:
            return True # fine comando

         # imposto il map tool
         self.getPointMapTool().entitySet.set(self.entitySet)
         self.getPointMapTool().setMode(Qad_mirror_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT)                                
   
         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.translate("Command_MIRROR", "Specificare primo punto della linea speculare: "))
         self.step = 2      
         return False
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO BASE (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  # si appresta ad attendere un punto
                  self.waitForPoint(QadMsg.translate("Command_MIRROR", "Specificare primo punto della linea speculare: "))
                  return False
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         self.firstMirrorPt.set(value.x(), value.y())

         # imposto il map tool
         self.getPointMapTool().firstMirrorPt = self.firstMirrorPt
         self.getPointMapTool().setMode(Qad_mirror_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)                                
         
         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.translate("Command_MIRROR", "Specificare secondo punto della linea speculare: "))
         self.step = 3
         
         return False 
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER SPECCHIO (da step = 2)
      elif self.step == 3: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  # si appresta ad attendere un punto
                  self.waitForPoint(QadMsg.translate("Command_MIRROR", "Specificare secondo punto della linea speculare: "))
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if qad_utils.ptNear(self.firstMirrorPt, value):
            self.showMsg(QadMsg.translate("Command_MIRROR", "\nI punti devono essere distinti."))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_MIRROR", "Specificare secondo punto della linea speculare: "))
            return False
         
         self.secondMirrorPt.set(value.x(), value.y())
         
         keyWords = QadMsg.translate("QAD", "Sì") + " " + \
                    QadMsg.translate("QAD", "No")                                       
         msg = QadMsg.translate("Command_MIRROR", "Cancellare gli oggetti sorgente? [Sì/No] <{0}>: ")
         if self.copyFeatures == False:
            default = QadMsg.translate("QAD", "Sì")
         else: 
            default = QadMsg.translate("QAD", "No")
             
         # si appresta ad attendere enter o una parola chiave         
         # msg, inputType, default, keyWords, nessun controllo
         self.waitFor(msg.format(default), \
                      QadInputTypeEnum.KEYWORDS, \
                      default, \
                      keyWords, QadInputModeEnum.NONE)
         self.getPointMapTool().setMode(Qad_mirror_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT)                                         
         self.step = 4

         return False
            

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI CANCELLAZIONE OGGETTO SORGENTE (da step = 3)
      elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
               value = QadMsg.translate("QAD", "No")   
            else:
               self.setMapTool(self.getPointMapTool()) # riattivo il maptool
               return False
         else: # il valore arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("QAD", "Sì"):
               self.copyFeatures = False
            elif value == QadMsg.translate("QAD", "No"):
               self.copyFeatures = True
                     
            self.mirrorGeoms()
            return True # fine comando

         return False
