# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando SCALE per scalare oggetti
 
                              -------------------
        begin                : 2013-10-01
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
from qad_scale_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_textwindow import *
from qad_ssget_cmd import QadSSGetClass
from qad_entity import *
import qad_utils

# Classe che gestisce il comando SCALA
class QadSCALECommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.get(195) # "SCALA"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runSCALECommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/scale.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.get(196)
   
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
      if self.step == 0: # quando si è in fase di selezione entità
         return self.SSGetClass.getPointMapTool()
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_scale_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None

   def scaleGeoms(self, scale):      
      #qad_debug.breakPoint()
      for layerEntitySet in self.entitySet.layerEntitySetList:                        
         scaledObjects = []
         transformedBasePt = self.plugIn.canvas.mapRenderer().mapToLayerCoordinates(layerEntitySet.layer, self.basePt)
         
         for featureId in layerEntitySet.featureIds:
            f = layerEntitySet.getFeature(featureId)
            f.setGeometry(qad_utils.scaleQgsGeometry(f.geometry(), transformedBasePt, scale))
            scaledObjects.append(f)

         if self.copyFeatures == False:
            qad_utils.updateFeaturesToLayer(self.plugIn, layerEntitySet.layer, scaledObjects)
         else:             
            qad_utils.addFeaturesToLayer(self.plugIn, layerEntitySet.layer, scaledObjects)


   def waitForScale(self):
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_scale_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_SCALE_PT)

      keyWords = QadMsg.get(186) + " " + QadMsg.get(187) # "Copia" "Riferimento"
      # "Specificare fattore di scala o [Copia/Riferimento]: "
      msg = QadMsg.get(197)            
      
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valori positivi
      self.waitFor(msg.format(str(self.plugIn.lastScale)), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT | QadInputTypeEnum.KEYWORDS, \
                   self.plugIn.lastScale, \
                   keyWords, QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)      
      self.step = 3      


   def waitForReferenceLen(self):
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_scale_maptool_ModeEnum.ASK_FOR_FIRST_PT_REFERENCE_LEN)
      
      # "Specificare lunghezza di riferimento <{0}>: "
      msg = QadMsg.get(198)                           
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
      
      keyWords = QadMsg.get(188) # "Punti"
      # "Specificare nuova lunghezza o [Punti] <{0}>: "
      msg = QadMsg.get(199)                           
      
      if self.plugIn.lastNewReferenceLen == 0:
         length = self.plugIn.lastScale
      else:
         length = self.plugIn.lastNewReferenceLen
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valori positivi
      self.waitFor(msg.format(str(length)), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT | QadInputTypeEnum.KEYWORDS, \
                   length, \
                   keyWords, QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
      self.step = 6
   

   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.get(128)) # "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate\n"
         return True # fine comando
            
      #=========================================================================
      # RICHIESTA SELEZIONE OGGETTI
      if self.step == 0: # inizio del comando
         if self.SSGetClass.run(msgMapTool, msg) == True:
            # selezione terminata
            self.step = 1
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
         self.waitForPoint(QadMsg.get(180)) # "Specificare punto base: "
                  
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
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.get(186): # "Copia"
               self.copyFeatures = True
               # "\nScala di una copia degli oggetti selezionati."
               self.showMsg(QadMsg.get(200))
               # si appresta ad attendere la scala               
               self.waitForScale()                
            elif value == QadMsg.get(187): # "Riferimento"
               # si appresta ad attendere la lunghezza di riferimento                      
               self.waitForReferenceLen()
         elif type(value) == QgsPoint or type(value) == float: # se è stato inserita la scala
            if type(value) == QgsPoint: # se è stato inserita la scala con un punto
               if value == self.basePt:
                  # "\nIl valore deve essere positivo e diverso da zero."
                  self.showMsg(QadMsg.get(201))
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
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == float: # se è stato inserita la lunghezza
            self.ReferenceLen = value
            self.getPointMapTool().ReferenceLen = self.ReferenceLen 
            # si appresta ad attendere la nuova lunghezza                    
            self.waitForNewReferenceLen()

         elif type(value) == QgsPoint: # se è stato inserito la scala con un punto                                 
            self.Pt1ReferenceLen = QgsPoint(value)
            self.getPointMapTool().Pt1ReferenceLen = self.Pt1ReferenceLen 
            # imposto il map tool
            self.getPointMapTool().setMode(Qad_scale_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT_REFERENCE_LEN)
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.get(93)) # "Specificare secondo punto: "
            self.step = 5           
            
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER LUNGHEZZA DI RIFERIMENTO (da step = 4)
      elif self.step == 5: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if self.Pt1ReferenceLen == value:
            # "\nIl valore deve essere positivo e diverso da zero."
            self.showMsg(QadMsg.get(201))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.get(93)) # "Specificare secondo punto: "
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
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.get(188): # "Punti"
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_scale_maptool_ModeEnum.ASK_FOR_FIRST_NEW_LEN_PT)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.get(119)) # "Specificare primo punto: "
               self.step = 7
         elif type(value) == QgsPoint or type(value) == float: # se è stato inserita la lunghezza
            if type(value) == QgsPoint: # se è stato inserito la lunghezza con un punto
               if value == self.basePt:
                  # "\nIl valore deve essere positivo e diverso da zero."
                  self.showMsg(QadMsg.get(201))
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
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
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
         self.waitForPoint(QadMsg.get(93)) # "Specificare secondo punto: "
         self.step = 8
            
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER NUOVA LUNGHEZZA (da step = 7)
      elif self.step == 8: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value == self.Pt1NewLen:
            # "\nIl valore deve essere positivo e diverso da zero."
            self.showMsg(QadMsg.get(201))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.get(93)) # "Specificare secondo punto: "
            return False
               
         length = qad_utils.getDistance(self.Pt1NewLen, value)
         
         scale = length / self.ReferenceLen
         self.plugIn.setLastScale(scale)
         self.scaleGeoms(scale)
         return True # fine comando
            