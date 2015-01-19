# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando SCALE per scalare oggetti
 
                              -------------------
        begin                : 2013-10-01
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


import qad_debug
from qad_scale_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_textwindow import *
from qad_ssget_cmd import QadSSGetClass
from qad_entity import *
import qad_utils
import qad_layer
import qad_label
from qad_dim import *


# Classe che gestisce il comando SCALA
class QadSCALECommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "SCALA")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runSCALECommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/scale.png")

   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_SCALE", "Ingrandisce o riduce gli oggetti selezionati.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.SSGetClass = QadSSGetClass(plugIn)
      self.SSGetClass.onlyEditableLayers = True
      self.entitySet = QadEntitySet()
      self.basePt = None
      self.copyFeatures = False
      self.Pt1ReferenceLen = None
      self.ReferenceLen = 1
      self.Pt1NewLen = None

   def __del__(self):
      QadCommandClass.__del__(self)
      del self.SSGetClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 0: # quando si � in fase di selezione entit�
         return self.SSGetClass.getPointMapTool()
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_scale_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None


   #============================================================================
   # scale
   #============================================================================
   def scale(self, f, basePt, scale, sizeFldName, layerEntitySet, entitySet, dimStyle):
      #qad_debug.breakPoint()
      if dimStyle is not None:
         entity = QadEntity()
         entity.set(layerEntitySet.layer, f.id())
         dimEntity = QadDimEntity()
         if dimEntity.initByEntity(dimStyle, entity) == False:
            dimEntity = None
      else:
         dimEntity = None
      
      if dimEntity is None:
         # scalo la feature e la rimuovo da entitySet (� la prima)
         f.setGeometry(qad_utils.scaleQgsGeometry(f.geometry(), basePt, scale))
         if sizeFldName is not None:
            sizeValue = f.attribute(sizeFldName)
            if sizeValue is None:
               sizeValue = 1
            sizeValue = sizeValue * scale
            f.setAttribute(sizeFldName, sizeValue)                           
         
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
         dimEntitySet = dimEntity.getEntitySet()
         if self.copyFeatures == False:
            if dimEntity.deleteToLayers(self.plugIn) == False:
               return False                      
         dimEntity.scale(self.plugIn,basePt, scale)
         if dimEntity.addToLayers(self.plugIn) == False:
            return False             
         entitySet.subtract(dimEntitySet)


   def scaleGeoms(self, scale):      
      #qad_debug.breakPoint()
      # copio entitySet
      entitySet = QadEntitySet(self.entitySet)
      
      self.plugIn.beginEditCommand("Feature scaled", self.entitySet.getLayerList())
      
      for layerEntitySet in entitySet.layerEntitySetList:
         layer = layerEntitySet.layer
         
         # verifico se il layer appartiene ad uno stile di quotatura
         dimStyle = self.plugIn.dimStyles.getDimByLayer(layer)
                              
         transformedBasePt = self.mapToLayerCoordinates(layer, self.basePt)
         
         sizeFldName = None
         if qad_layer.isTextLayer(layer):
            # se l'altezza testo dipende da un solo campo 
            sizeFldNames = qad_label.get_labelSizeFieldNames(layer)
            if len(sizeFldNames) == 1 and len(sizeFldNames[0]) > 0:
                sizeFldName = sizeFldNames[0]
         elif qad_layer.isSymbolLayer(layer):
            # se la scala dipende da un campo 
            sizeFldName = qad_layer.get_symbolScaleFieldName(layer)
            if len(sizeFldName) == 0:
               sizeFldName = None

         while len(layerEntitySet.featureIds) > 0:
            featureId = layerEntitySet.featureIds[0]
            f = layerEntitySet.getFeature(featureId)

            if self.scale(f, transformedBasePt, scale, sizeFldName, layerEntitySet, entitySet, dimStyle) == False:  
               self.plugIn.destroyEditCommand()
               return

      self.plugIn.endEditCommand()


   def waitForScale(self):
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_scale_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_SCALE_PT)

      keyWords = QadMsg.translate("Command_SCALE", "Copia") + "/" + \
                 QadMsg.translate("Command_SCALE", "Riferimento")
      default = self.plugIn.lastScale
      prompt = QadMsg.translate("Command_SCALE", "Specificare fattore di scala o [{0}] <{1}>: ").format(keyWords, str(default))                        
      
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valori positivi
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT | QadInputTypeEnum.KEYWORDS, \
                   default, \
                   keyWords, QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)      
      self.step = 3      


   def waitForReferenceLen(self):
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_scale_maptool_ModeEnum.ASK_FOR_FIRST_PT_REFERENCE_LEN)
      
      msg = QadMsg.translate("Command_SCALE", "Specificare lunghezza di riferimento <{0}>: ")                          
      # si appresta ad attendere un punto o enter     
      # msg, inputType, default, keyWords, valori positivi
      self.waitFor(msg.format(str(self.plugIn.lastReferenceLen)), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                   self.plugIn.lastReferenceLen, \
                   "", QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)               
      self.step = 4


   def waitForNewReferenceLen(self):
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_scale_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_NEW_LEN_PT)
      
      keyWords = QadMsg.translate("Command_SCALE", "Punti")
      if self.plugIn.lastNewReferenceLen == 0:
         default = self.plugIn.lastScale
      else:
         default = self.plugIn.lastNewReferenceLen
      prompt = QadMsg.translate("Command_SCALE", "Specificare nuova lunghezza o [{0}] <{1}>: ").format(keyWords, str(default))                        
         
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valori positivi
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT | QadInputTypeEnum.KEYWORDS, \
                   default, \
                   keyWords, QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
      self.step = 6
   

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
            self.getPointMapTool().refreshSnapType() # aggiorno lo snapType che pu� essere variato dal maptool di selezione entit�                     
            return self.run(msgMapTool, msg)
      
      #=========================================================================
      # RUOTA OGGETTI
      elif self.step == 1:
         self.entitySet.set(self.SSGetClass.entitySet)
         
         if self.entitySet.count() == 0:
            return True # fine comando

         # imposto il map tool
         self.getPointMapTool().setMode(Qad_scale_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_BASE_PT)                                

         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.translate("Command_SCALE", "Specificare punto base: "))
                  
         self.step = 2     
         return False
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO BASE (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool � stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         self.basePt = QgsPoint(value)

         self.getPointMapTool().basePt = self.basePt
         self.getPointMapTool().entitySet.set(self.entitySet)
         # si appresta ad attendere la scala                      
         self.waitForScale()
         
         return False 
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER SCALA (da step = 2)
      elif self.step == 3: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool � stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_SCALE", "Copia"):
               self.copyFeatures = True
               self.showMsg(QadMsg.translate("Command_SCALE", "\nScala di una copia degli oggetti selezionati."))
               # si appresta ad attendere la scala               
               self.waitForScale()                
            elif value == QadMsg.translate("Command_SCALE", "Riferimento"):
               # si appresta ad attendere la lunghezza di riferimento                      
               self.waitForReferenceLen()
         elif type(value) == QgsPoint or type(value) == float: # se � stato inserita la scala
            if type(value) == QgsPoint: # se � stato inserita la scala con un punto
               if value == self.basePt:
                  self.showMsg(QadMsg.translate("QAD", "\nIl valore deve essere positivo e diverso da zero."))
                  # si appresta ad attendere un punto
                  self.waitForScale()
                  return False
                                      
               scale = qad_utils.getDistance(self.basePt, value)
            else:
               scale = value
            self.plugIn.setLastScale(scale)

            self.scaleGeoms(scale)
            return True # fine comando
         
         return False
               
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PRIMO PUNTO PER LUNGHEZZA DI RIFERIMENTO (da step = 3)
      elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool � stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == float: # se � stato inserita la lunghezza
            self.ReferenceLen = value
            self.getPointMapTool().ReferenceLen = self.ReferenceLen 
            # si appresta ad attendere la nuova lunghezza                    
            self.waitForNewReferenceLen()

         elif type(value) == QgsPoint: # se � stato inserito la scala con un punto                                 
            self.Pt1ReferenceLen = QgsPoint(value)
            self.getPointMapTool().Pt1ReferenceLen = self.Pt1ReferenceLen 
            # imposto il map tool
            self.getPointMapTool().setMode(Qad_scale_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT_REFERENCE_LEN)
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_SCALE", "Specificare secondo punto: "))
            self.step = 5           
            
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER LUNGHEZZA DI RIFERIMENTO (da step = 4)
      elif self.step == 5: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool � stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if self.Pt1ReferenceLen == value:
            self.showMsg(QadMsg.translate("QAD", "\nIl valore deve essere positivo e diverso da zero."))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_SCALE", "Specificare secondo punto: "))
            return False
            
         length = qad_utils.getDistance(self.Pt1ReferenceLen, value)
         self.ReferenceLen = length
         self.getPointMapTool().ReferenceLen = self.ReferenceLen
         # si appresta ad attendere la nuova lunghezza                    
         self.waitForNewReferenceLen()
            
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER NUOVA LUNGHEZZA (da step = 4 e 5)
      elif self.step == 6: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool � stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_SCALE", "Punti"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_scale_maptool_ModeEnum.ASK_FOR_FIRST_NEW_LEN_PT)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.translate("Command_SCALE", "Specificare primo punto: "))
               self.step = 7
         elif type(value) == QgsPoint or type(value) == float: # se � stato inserita la lunghezza
            if type(value) == QgsPoint: # se � stato inserito la lunghezza con un punto
               if value == self.basePt:
                  self.showMsg(QadMsg.translate("QAD", "\nIl valore deve essere positivo e diverso da zero."))
                  # si appresta ad attendere un punto
                  self.waitForNewReferenceLen()
                  return False
                                       
               length = qad_utils.getDistance(self.basePt, value)
            else:
               length = value
            
            scale = length / self.ReferenceLen
            self.plugIn.setLastScale(scale)
            self.scaleGeoms(scale)
            return True # fine comando

         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PRIMO PUNTO PER NUOVA LUNGHEZZA (da step = 6)
      elif self.step == 7: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool � stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
      
         self.Pt1NewLen = value
         # imposto il map tool
         self.getPointMapTool().Pt1NewLen = self.Pt1NewLen
         self.getPointMapTool().setMode(Qad_scale_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_NEW_LEN_PT)
         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.translate("Command_SCALE", "Specificare secondo punto: "))
         self.step = 8
            
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER NUOVA LUNGHEZZA (da step = 7)
      elif self.step == 8: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # � stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool � stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value == self.Pt1NewLen:
            self.showMsg(QadMsg.translate("QAD", "\nIl valore deve essere positivo e diverso da zero."))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_SCALE", "Specificare secondo punto: "))
            return False
               
         length = qad_utils.getDistance(self.Pt1NewLen, value)
         
         scale = length / self.ReferenceLen
         self.plugIn.setLastScale(scale)
         self.scaleGeoms(scale)
         return True # fine comando
            