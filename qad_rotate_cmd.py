# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando ROTATE per ruotare oggetti
 
                              -------------------
        begin                : 2013-09-27
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
from qad_rotate_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_textwindow import *
from qad_ssget_cmd import QadSSGetClass
from qad_entity import *
import qad_utils

# Classe che gestisce il comando RUOTA
class QadROTATECommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.get(179) # "RUOTA"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runROTATECommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/rotate.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.get(185)
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.SSGetClass = QadSSGetClass(plugIn)
      self.SSGetClass.onlyEditableLayers = True
      self.entitySet = QadEntitySet()
      self.basePt = None
      self.copyFeatures = False
      self.Pt1ReferenceAng = None
      self.ReferenceAng = 0
      self.Pt1NewAng = None

   def __del__(self):
      QadCommandClass.__del__(self)
      del self.SSGetClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 0: # quando si è in fase di selezione entità
         return self.SSGetClass.getPointMapTool()
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_rotate_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None

   def RotateGeoms(self, angle):      
      #qad_debug.breakPoint()
      for layerEntitySet in self.entitySet.layerEntitySetList:                        
         rotatedObjects = []
         transformedBasePt = self.plugIn.canvas.mapRenderer().mapToLayerCoordinates(layerEntitySet.layer, self.basePt)
         
         for featureId in layerEntitySet.featureIds:
            f = layerEntitySet.getFeature(featureId)
            f.setGeometry(qad_utils.rotateQgsGeometry(f.geometry(), transformedBasePt, angle))
            rotatedObjects.append(f)

         if self.copyFeatures == False:
            qad_utils.updateFeaturesToLayer(self.plugIn, layerEntitySet.layer, rotatedObjects)
         else:             
            qad_utils.addFeaturesToLayer(self.plugIn, layerEntitySet.layer, rotatedObjects)


   def waitForRotation(self):
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_rotate_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_ROTATION_PT)

      keyWords = QadMsg.get(186) + " " + QadMsg.get(187) # "Copia" "Riferimento"
      # "Specificare angolo di rotazione o [Copia/Riferimento] <{0}>: "
      msg = QadMsg.get(181)            
      
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg.format(str(qad_utils.toDegrees(self.plugIn.lastRot))), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT | QadInputTypeEnum.KEYWORDS, \
                   self.plugIn.lastRot, \
                   keyWords, QadInputModeEnum.NONE)      
      self.step = 3      


   def waitForReferenceRot(self):
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_rotate_maptool_ModeEnum.ASK_FOR_FIRST_PT_REFERENCE_ANG)
      
      # "Specificare angolo di riferimento <{0}>: "
      msg = QadMsg.get(183)                           
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg.format(str(qad_utils.toDegrees(self.plugIn.lastReferenceRot))), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                   self.plugIn.lastReferenceRot, \
                   "", QadInputModeEnum.NOT_NULL)               
      self.step = 4


   def waitForNewReferenceRot(self):
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_rotate_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_NEW_ROTATION_PT)
      
      keyWords = QadMsg.get(188) # "Punti"
      # "Specificare nuovo angolo o [Punti] <{0}>: "
      msg = QadMsg.get(184)                           
      
      if self.plugIn.lastNewReferenceRot == 0:
         angle = self.plugIn.lastRot
      else:
         angle = self.plugIn.lastNewReferenceRot
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg.format(str(qad_utils.toDegrees(angle))), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT | QadInputTypeEnum.KEYWORDS, \
                   angle, \
                   keyWords, QadInputModeEnum.NOT_NULL)
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
         self.getPointMapTool().setMode(Qad_rotate_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_BASE_PT)                                

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
         # si appresta ad attendere l'angolo di rotazione                      
         self.waitForRotation()
         
         return False 
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER ANGOLO ROTAZIONE (da step = 2)
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
               # "\nRotazione di una copia degli oggetti selezionati.\n"
               self.showMsg(QadMsg.get(182))
               # si appresta ad attendere l'angolo di rotazione               
               self.waitForRotation()                
            elif value == QadMsg.get(187): # "Riferimento"
               # si appresta ad attendere l'angolo di riferimento                      
               self.waitForReferenceRot()
         elif type(value) == QgsPoint or type(value) == float: # se è stato inserito l'angolo di rotazione
            if type(value) == QgsPoint: # se è stato inserito l'angolo di rotazione con un punto                        
               angle = qad_utils.getAngleBy2Pts(self.basePt, value)
            else:
               angle = qad_utils.toRadians(value)
            self.plugIn.setLastRot(angle)

            self.RotateGeoms(angle)
            return True # fine comando
         
         return False
               
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PRIMO PUNTO PER ANGOLO ROTAZIONE DI RIFERIMENTO (da step = 3)
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

         if type(value) == float: # se è stato inserito l'angolo di rotazione
            self.ReferenceAng = qad_utils.toRadians(value)
            self.getPointMapTool().ReferenceAng = self.ReferenceAng 
            # si appresta ad attendere il nuovo angolo                    
            self.waitForNewReferenceRot()

         elif type(value) == QgsPoint: # se è stato inserito l'angolo di rotazione con un punto                                 
            self.Pt1ReferenceAng = QgsPoint(value)
            self.getPointMapTool().Pt1ReferenceAng = self.Pt1ReferenceAng 
            # imposto il map tool
            self.getPointMapTool().setMode(Qad_rotate_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT_REFERENCE_ANG)
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.get(93)) # "Specificare secondo punto: "
            self.step = 5           
            
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER ANGOLO ROTAZIONE DI RIFERIMENTO (da step = 4)
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

         angle = qad_utils.getAngleBy2Pts(self.Pt1ReferenceAng, value)
         self.ReferenceAng = angle
         self.getPointMapTool().ReferenceAng = self.ReferenceAng 
         # si appresta ad attendere il nuovo angolo                    
         self.waitForNewReferenceRot()
            
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER NUOVO ANGOLO ROTAZIONE (da step = 4 e 5)
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
               self.getPointMapTool().setMode(Qad_rotate_maptool_ModeEnum.ASK_FOR_FIRST_NEW_ROTATION_PT)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.get(119)) # "Specificare primo punto: "
               self.step = 7
         elif type(value) == QgsPoint or type(value) == float: # se è stato inserito l'angolo di rotazione
            if type(value) == QgsPoint: # se è stato inserito l'angolo di rotazione con un punto                        
               angle = qad_utils.getAngleBy2Pts(self.basePt, value)
            else:
               angle = qad_utils.toRadians(value)
            
            angle = angle - self.ReferenceAng
            self.plugIn.setLastRot(angle)
            self.RotateGeoms(angle)
            return True # fine comando

         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PRIMO PUNTO PER NUOVO ANGOLO ROTAZIONE (da step = 6)
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
      
         self.Pt1NewAng = value
         # imposto il map tool
         self.getPointMapTool().Pt1NewAng = self.Pt1NewAng
         self.getPointMapTool().setMode(Qad_rotate_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_NEW_ROTATION_PT)
         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.get(93)) # "Specificare secondo punto: "
         self.step = 8
            
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER NUOVO ANGOLO ROTAZIONE (da step = 7)
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
               
         angle = qad_utils.getAngleBy2Pts(self.Pt1NewAng, value)
         
         angle = angle - self.ReferenceAng
         self.plugIn.setLastRot(angle)
         self.RotateGeoms(angle)
         return True # fine comando
            