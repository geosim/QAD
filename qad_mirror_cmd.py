# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando MIRROR per spostare oggetti
 
                              -------------------
        begin                : 2013-12-11
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
   
   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadMIRRORCommandClass(self.plugIn)
   
   def getName(self):
      return QadMsg.translate("Command_list", "MIRROR")

   def getEnglishName(self):
      return "MIRROR"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runMIRRORCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/mirror.png")

   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_MIRROR", "Creates a mirrored copy of selected objects.")
   
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
      if self.step == 0: # quando si é in fase di selezione entità
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
   def mirror(self, f, pt1, pt2, rotFldName, layerEntitySet, entitySet, dimEntity):
      
      if dimEntity is None:
         # scalo la feature e la rimuovo da entitySet (é la prima)
         f.setGeometry(qad_utils.mirrorQgsGeometry(f.geometry(), pt1, pt2))
         if len(rotFldName) > 0:
            rotValue = f.attribute(rotFldName)
            # a volte vale None e a volte null (vai a capire...)
            rotValue = 0 if rotValue is None or isinstance(rotValue, QPyNullVariant) else qad_utils.toRadians(rotValue) # la rotazione é in gradi nel campo della feature
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
         newDimEntity = QadDimEntity(dimEntity) # la copio
         newDimEntity.mirror(pt1, mirrorAngle)
         if newDimEntity.addToLayers(self.plugIn) == False:
            return False             
         entitySet.subtract(dimEntitySet)


   #============================================================================
   # mirrorGeoms
   #============================================================================
   def mirrorGeoms(self):      
      # copio entitySet
      entitySet = QadEntitySet(self.entitySet)

      self.plugIn.beginEditCommand("Feature mirrored", self.entitySet.getLayerList())

      for layerEntitySet in entitySet.layerEntitySetList:
         layer = layerEntitySet.layer        

         transformedBasePt = self.mapToLayerCoordinates(layer, self.firstMirrorPt)
         transformedNewPt = self.mapToLayerCoordinates(layer, self.secondMirrorPt)
         
         rotFldName = ""
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

            entity = QadEntity()
            entity.set(layer, featureId)
            # verifico se l'entità appartiene ad uno stile di quotatura
            dimStyle, dimId = QadDimStyles.getDimIdByEntity(entity)

            if dimStyle is not None:
               dimEntity = QadDimEntity()
               if dimEntity.initByDimId(dimStyle, dimId) == False:
                  dimEntity = None
            else:
               dimEntity = None

            if self.mirror(f, transformedBasePt, transformedNewPt, rotFldName, layerEntitySet, entitySet, dimEntity) == False:  
               self.plugIn.destroyEditCommand()
               return

      self.plugIn.endEditCommand()
   

   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapSettings().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
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
         self.waitForPoint(QadMsg.translate("Command_MIRROR", "Specify first point of mirror line: "))
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
                  # si appresta ad attendere un punto
                  self.waitForPoint(QadMsg.translate("Command_MIRROR", "Specify first point of mirror line: "))
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
         self.waitForPoint(QadMsg.translate("Command_MIRROR", "Specify second point of mirror line: "))
         self.step = 3
         
         return False 
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER SPECCHIO (da step = 2)
      elif self.step == 3: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  # si appresta ad attendere un punto
                  self.waitForPoint(QadMsg.translate("Command_MIRROR", "Specify second point of mirror line: "))
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if qad_utils.ptNear(self.firstMirrorPt, value):
            self.showMsg(QadMsg.translate("Command_MIRROR", "\nThe points must be different."))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_MIRROR", "Specify second point of mirror line: "))
            return False
         
         self.secondMirrorPt.set(value.x(), value.y())
         
         keyWords = QadMsg.translate("QAD", "Yes") + "/" + \
                    QadMsg.translate("QAD", "No")                                       
         if self.copyFeatures == False:
            default = QadMsg.translate("QAD", "Yes")
         else: 
            default = QadMsg.translate("QAD", "No")
         prompt = QadMsg.translate("Command_MIRROR", "Erase source objects ? [{0}] <{1}>: ").format(keyWords, default)
             
         englishKeyWords = "Yes" + "/" + "No"
         keyWords += "_" + englishKeyWords
         # si appresta ad attendere enter o una parola chiave         
         # msg, inputType, default, keyWords, nessun controllo
         self.waitFor(prompt, \
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
            # é stato attivato un altro plugin che ha disattivato Qad
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
            if value == QadMsg.translate("QAD", "Yes") or value == "Yes":
               self.copyFeatures = False
            elif value == QadMsg.translate("QAD", "No") or value == "No":
               self.copyFeatures = True
                     
            self.mirrorGeoms()
            return True # fine comando

         return False




# Classe che gestisce il comando MIRROR per i grip
class QadGRIPMIRRORCommandClass(QadCommandClass):
   
   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadMIRRORCommandClass(self.plugIn)
   

   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.entitySet = QadEntitySet()
      self.basePt = QgsPoint()
      self.secondMirrorPt = QgsPoint()
      self.skipToNextGripCommand = False
      self.copyEntities = False
      self.nOperationsToUndo = 0

   def __del__(self):
      QadCommandClass.__del__(self)
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_mirror_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None


   #============================================================================
   # setSelectedEntityGripPoints
   #============================================================================
   def setSelectedEntityGripPoints(self, entitySetGripPoints):
      # lista delle entityGripPoint con dei grip point selezionati
      self.entitySet.clear()

      for entityGripPoints in entitySetGripPoints.entityGripPoints:
         self.entitySet.addEntity(entityGripPoints.entity)
      self.getPointMapTool().entitySet.set(self.entitySet)


   #============================================================================
   # mirror
   #============================================================================
   def mirror(self, entity, pt1, pt2, rotFldName):
      # entity = entità da specchiare
      # pt1 e pt2 = linea di simmetria
      # rotFldName = campo della tabella che memorizza la rotazione
      # verifico se l'entità appartiene ad uno stile di quotatura
      if entity.whatIs() == "ENTITY":
         f = entity.getFeature()
         # specchio l'entità
         f.setGeometry(qad_utils.mirrorQgsGeometry(entity.getGeometry(), pt1, pt2))
         if len(rotFldName) > 0:
            rotValue = f.attribute(rotFldName)
            # a volte vale None e a volte null (vai a capire...)
            rotValue = 0 if rotValue is None or isinstance(rotValue, QPyNullVariant) else qad_utils.toRadians(rotValue) # la rotazione é in gradi nel campo della feature
            ptDummy = qad_utils.getPolarPointByPtAngle(pt1, rotValue, 1)
            mirrorAngle = qad_utils.getAngleBy2Pts(pt1, pt2)
            ptDummy = qad_utils.mirrorPoint(ptDummy, pt1, mirrorAngle)
            rotValue = qad_utils.getAngleBy2Pts(pt1, ptDummy)
            f.setAttribute(rotFldName, qad_utils.toDegrees(qad_utils.normalizeAngle(rotValue)))               
                  
         if self.copyEntities == False:
            # plugIn, layer, feature, refresh, check_validity
            if qad_layer.updateFeatureToLayer(self.plugIn, entity.layer, f, False, False) == False:
               return False
         else:             
            # plugIn, layer, features, coordTransform, refresh, check_validity
            if qad_layer.addFeatureToLayer(self.plugIn, entity.layer, f, None, False, False) == False:
               return False
      elif entity.whatIs() == "DIMENTITY":
         mirrorAngle = qad_utils.getAngleBy2Pts(pt1, pt2)
         # specchio la quota
         if self.copyEntities == False:
            if entity.deleteToLayers(self.plugIn) == False:
               return False
            
         newDimEntity = QadDimEntity(entity) # la copio
         newDimEntity.mirror(pt1, mirrorAngle)
         if newDimEntity.addToLayers(self.plugIn) == False:
            return False             

      return True


   #============================================================================
   # mirrorGeoms
   #============================================================================
   def mirrorGeoms(self):
      entity = QadEntity()
      self.plugIn.beginEditCommand("Feature mirrored", self.entitySet.getLayerList())

      dimElaboratedList = [] # lista delle quotature già elaborate

      for layerEntitySet in self.entitySet.layerEntitySetList:
         layer = layerEntitySet.layer        

         transformedBasePt = self.mapToLayerCoordinates(layer, self.basePt)
         transformedNewPt = self.mapToLayerCoordinates(layer, self.secondMirrorPt)
         
         rotFldName = ""
         if qad_layer.isTextLayer(layer):
            # se la rotazione dipende da un solo campo
            rotFldNames = qad_label.get_labelRotationFieldNames(layer)
            if len(rotFldNames) == 1 and len(rotFldNames[0]) > 0:
               rotFldName = rotFldNames[0]         
         elif qad_layer.isSymbolLayer(layer):
            rotFldName = qad_layer.get_symbolRotationFieldName(layer)

         for featureId in layerEntitySet.featureIds:
            entity.set(layer, featureId)

            # verifico se l'entità appartiene ad uno stile di quotatura
            dimEntity = QadDimStyles.getDimEntity(entity)  
            if dimEntity is None:
               if self.mirror(entity, transformedBasePt, transformedNewPt, rotFldName) == False:
                  self.plugIn.destroyEditCommand()
                  return
            else:
               found = False
               for dimElaborated in dimElaboratedList:
                  if dimElaborated == dimEntity:
                     found = True
            
               if found == False: # quota non ancora elaborata
                  dimElaboratedList.append(dimEntity)
                  if self.mirror(dimEntity, transformedBasePt, transformedNewPt, rotFldName) == False:
                     self.plugIn.destroyEditCommand()
                     return

      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1
   
   
   #============================================================================
   # waitForMirrorPoint
   #============================================================================
   def waitForMirrorPoint(self):
      self.step = 1
      self.plugIn.setLastPoint(self.basePt)
      # imposto il map tool
      self.getPointMapTool().firstMirrorPt = self.basePt
      self.getPointMapTool().setMode(Qad_mirror_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)                                
         
      keyWords = QadMsg.translate("Command_GRIPMIRROR", "Base point") + "/" + \
                 QadMsg.translate("Command_GRIPMIRROR", "Copy") + "/" + \
                 QadMsg.translate("Command_GRIPMIRROR", "Undo") + "/" + \
                 QadMsg.translate("Command_GRIPMIRROR", "eXit")

      prompt = QadMsg.translate("Command_GRIPMIRROR", "Specify second point or [{0}]: ").format(keyWords)

      englishKeyWords = "Base point" + "/" + "Copy" + "/" + "Undo" + "/" + "eXit"
      keyWords += "_" + englishKeyWords
      # si appresta ad attendere un punto, un numero reale o enter o una parola chiave
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)      
   

   #============================================================================
   # waitForBasePt
   #============================================================================
   def waitForBasePt(self):
      self.step = 2   
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_mirror_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT)
      # si appresta ad attendere un punto
      self.waitForPoint(QadMsg.translate("Command_GRIPROTATE", "Specify base point: "))
   

   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapSettings().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
         return True # fine comando
            
      #=========================================================================
      # RICHIESTA SELEZIONE OGGETTI
      if self.step == 0: # inizio del comando
         if self.entitySet.isEmpty(): # non ci sono oggetti da ruotare
            return True
         self.showMsg(QadMsg.translate("Command_GRIPMIRROR", "\n** MIRROR **\n"))
         # si appresta ad attendere il secondo punto di specchio
         self.waitForMirrorPoint()

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER SPECCHIO
      elif self.step == 1: # dopo aver atteso un punto si riavvia il comando
         ctrlKey = False
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = None
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            ctrlKey = self.getPointMapTool().ctrlKey
            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_GRIPMIRROR", "Base point") or value == "Base point":
               # si appresta ad attendere il punto base
               self.waitForBasePt()
            elif value == QadMsg.translate("Command_GRIPMIRROR", "Copy") or value == "Copy":
               # Copia entità lasciando inalterate le originali
               self.copyEntities = True                     
               # si appresta ad attendere il secondo punto di specchio
               self.waitForMirrorPoint()
            elif value == QadMsg.translate("Command_GRIPMIRROR", "Undo") or value == "Undo":
               if self.nOperationsToUndo > 0: 
                  self.nOperationsToUndo = self.nOperationsToUndo - 1
                  self.plugIn.undoEditCommand()
               else:
                  self.showMsg(QadMsg.translate("QAD", "\nThe command has been canceled."))                  
               # si appresta ad attendere il secondo punto di specchio
               self.waitForMirrorPoint()
            elif value == QadMsg.translate("Command_GRIPMIRROR", "eXit") or value == "eXit":
               return True # fine comando
         elif type(value) == QgsPoint: # se é stato inserito il secondo punto
            if qad_utils.ptNear(self.basePt, value):
               self.showMsg(QadMsg.translate("Command_GRIPMIRROR", "\nThe points must be different."))
               # si appresta ad attendere il secondo punto di specchio
               self.waitForMirrorPoint()
               return False
            
            self.secondMirrorPt.set(value.x(), value.y())

            if ctrlKey:
               self.copyEntities = True

            self.mirrorGeoms()

            if self.copyEntities == False:
               return True

            # si appresta ad attendere il secondo punto di specchio
            self.waitForMirrorPoint()

         else:
            if self.copyEntities == False:
               self.skipToNextGripCommand = True
            return True # fine comando

         return False

              
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO BASE (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto
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

         if type(value) == QgsPoint: # se é stato inserito il punto base
            self.basePt.set(value.x(), value.y())
            
         # si appresta ad attendere il secondo punto di specchio
         self.waitForMirrorPoint()

         return False
