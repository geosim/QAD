# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando ARC per disegnare un arco
 
                              -------------------
        begin                : 2013-05-22
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
import math


import qad_debug
from qad_getpoint import *
from qad_arc_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_textwindow import *
import qad_utils
import qad_layer


# Classe che gestisce il comando PLINE
class QadARCCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "ARCO")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runARCCommand)
   
   def getIcon(self):
      return QIcon(":/plugins/qad/icons/arc.png")

   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_ARC", "Disegna un arco mediante diversi metodi.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.vertices = []

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_arc_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None
         
   def run(self, msgMapTool = False, msg = None):
      self.isValidPreviousInput = True # per gestire il comando anche in macro
           
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando
      
      currLayer, errMsg = qad_layer.getCurrLayerEditable(self.plugIn.canvas, QGis.Line)
      if currLayer is None:
         self.showMsg(errMsg)
         return True # fine comando

      #=========================================================================
      # RICHIESTA PRIMO PUNTO o CENTRO
      if self.step == 0: # inizio del comando
         # imposto il map tool
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_START_PT)        
         keyWords = QadMsg.translate("Command_ARC", "Centro")
         prompt = QadMsg.translate("Command_ARC", "Specificare punto iniziale dell'arco o [Centro]: ")            
         
         # si appresta ad attendere un punto o enter o una parola chiave         
         # msg, inputType, default, keyWords, nessun controllo di modo
         self.waitFor(prompt, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NONE)         
         self.step = 1
         
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PRIMO PUNTO o CENTRO
      elif self.step == 1: # dopo aver atteso un punto o enter o una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               #qad_debug.breakPoint()
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            if self.plugIn.lastPoint is not None:
               value = self.plugIn.lastPoint
            else:
               return True # fine comando

         if type(value) == QgsPoint: # se è stato inserito il punto iniziale dell'arco           
            self.startPt = value
            self.plugIn.setLastPoint(value)
            
            # imposto il map tool
            self.getPointMapTool().arcStartPt = self.startPt
            self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_SECOND_PT)
                                
            keyWords = QadMsg.translate("Command_ARC", "Centro") + " " + \
                       QadMsg.translate("Command_ARC", "Fine")
            msg = QadMsg.translate("Command_ARC", "Specificare secondo punto dell'arco [Centro/Fine]: ")          
            
            # si appresta ad attendere un punto o una parola chiave         
            # msg, inputType, default, keyWords
            self.waitFor(msg, \
                         QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                         None, \
                         keyWords, QadInputModeEnum.NONE)
            
            self.step = 2
            return False
         else: # si vuole inserire il centro dell'arco
            # imposto il map tool
            self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_CENTER_PT)
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_ARC", "Specificare centro dell'arco: "))
            
            self.step = 13
            return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO o CENTRO o FINE
      elif self.step == 2: # dopo aver atteso un punto o una parola chiave si riavvia il comando
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
            if value == QadMsg.translate("Command_ARC", "Centro"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_CENTER_PT)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.translate("Command_ARC", "Specificare centro dell'arco: "))
               self.step = 4           
            elif value == QadMsg.translate("Command_ARC", "Fine"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_PT_KNOWN_ASK_FOR_END_PT)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.translate("Command_ARC", "Specificare punto finale dell'arco: "))
               self.step = 8     
         elif type(value) == QgsPoint: # se è stato inserito il secondo punto dell'arco            
            self.secondPt = value
            # imposto il map tool
            self.getPointMapTool().arcSecondPt = self.secondPt
            self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_SECOND_PT_KNOWN_ASK_FOR_END_PT)

            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_ARC", "Specificare punto finale dell'arco: "))
            self.step = 3
                  
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO FINALE DELL'ARCO (da step = 2)
      elif self.step == 3: # dopo aver atteso un punto si riavvia il comando
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

         self.endPt = value
         self.plugIn.setLastPoint(value)
         
         arc = QadArc()         
         if arc.fromStartSecondEndPts(self.startPt, self.secondPt, self.endPt) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.startPt, arc.getStartPt()):
                  self.plugIn.setLastSegmentAng(arc.getTanDirectionOnEndPt())
               else:
                  self.plugIn.setLastSegmentAng(arc.getTanDirectionOnStartPt() + math.pi)
                  
               qad_layer.addLineToLayer(self.plugIn, currLayer, points)               
               return True # fine comando
      
         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.translate("Command_ARC", "Specificare punto finale dell'arco: "))
         self.isValidPreviousInput = False # per gestire il comando anche in macro     
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA CENTRO DELL'ARCO (da step = 2)
      elif self.step == 4: # dopo aver atteso un punto si riavvia il comando
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

         self.centerPt = value
         self.plugIn.setLastPoint(value)
         
         # imposto il map tool
         self.getPointMapTool().arcCenterPt = self.centerPt
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_END_PT)
         
         keyWords = QadMsg.translate("Command_ARC", "Angolo") + " " + \
                    QadMsg.translate("Command_ARC", "Lunghezza")         
         msg = QadMsg.translate("Command_ARC", "Specificare punto finale dell'arco o [Angolo/Lunghezza corda]: ")                  
         # si appresta ad attendere un punto o una parola chiave         
         # msg, inputType, default, keyWords, valori nulli non ammessi
         self.waitFor(msg, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NOT_NULL)
         
         self.step = 5
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare punto finale dell'arco o [Angolo/Lunghezza corda]: " (da step = 4)
      elif self.step == 5: # dopo aver atteso un punto o una parola chiave si riavvia il comando
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
            if value == QadMsg.translate("Command_ARC", "Angolo"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_ANGLE)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, valori nulli non ammessi
               self.waitFor(QadMsg.translate("Command_ARC", "Specificare angolo inscritto: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO)
               self.step = 6
               return False                              
            elif value == QadMsg.translate("Command_ARC", "Lunghezza"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_CHORD)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, valori positivi
               self.waitFor(QadMsg.translate("Command_ARC", "Specificare lunghezza della corda: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
               self.step = 7
               return False                              
         elif type(value) == QgsPoint: # se è stato inserito il punto finale dell'arco
            self.endPt = value
            self.plugIn.setLastPoint(value)
                     
            arc = QadArc()         
            if arc.fromStartCenterEndPts(self.startPt, self.centerPt, self.endPt) == True:
               points = arc.asPolyline()
               if points is not None:
                  # se i punti sono così vicini da essere considerati uguali
                  if qad_utils.ptNear(self.startPt, arc.getStartPt()):
                     self.plugIn.setLastSegmentAng(arc.getTanDirectionOnEndPt())
                  else:
                     self.plugIn.setLastSegmentAng(arc.getTanDirectionOnStartPt() + math.pi)
                  
                  qad_layer.addLineToLayer(self.plugIn, currLayer, points)               
                  return True # fine comando
            
            keyWords = QadMsg.translate("Command_ARC", "Angolo") + " " + \
                       QadMsg.translate("Command_ARC", "Lunghezza")
            msg = QadMsg.translate("Command_ARC", "Specificare punto finale dell'arco o [Angolo/Lunghezza corda]: ")                   
            # si appresta ad attendere un punto o una parola chiave         
            # msg, inputType, default, keyWords, valori nulli non ammessi
            self.waitFor(msg, \
                         QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                         None, \
                         keyWords, QadInputModeEnum.NOT_NULL)
            self.isValidPreviousInput = False # per gestire il comando anche in macro
            return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare angolo inscritto: " (da step = 5)
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

         if type(value) == QgsPoint:
            self.angle = qad_utils.getAngleBy2Pts(self.centerPt, value)             
         else:
            self.angle = value

         arc = QadArc()         
         if arc.fromStartCenterPtsAngle(self.startPt, self.centerPt, self.angle) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.startPt, arc.getStartPt()):
                  self.plugIn.setLastSegmentAng(arc.getTanDirectionOnEndPt())
               else:
                  self.plugIn.setLastSegmentAng(arc.getTanDirectionOnStartPt() + math.pi)
               
               qad_layer.addLineToLayer(self.plugIn, currLayer, points)               
               return True # fine comando

         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, valori nulli non ammessi
         self.waitFor(QadMsg.translate("Command_ARC", "Specificare angolo inscritto: "), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                      None, "", \
                      QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO)
         self.isValidPreviousInput = False # per gestire il comando anche in macro         
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare lunghezza della corda: " (da step = 5)
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

         if type(value) == QgsPoint:
            self.chord = qad_utils.getDistance(self.startPt, value)             
         else:
            self.chord = value

         arc = QadArc()         
         if arc.fromStartCenterPtsChord(self.startPt, self.centerPt, self.chord) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.startPt, arc.getStartPt()):
                  self.plugIn.setLastSegmentAng(arc.getTanDirectionOnEndPt())
               else:
                  self.plugIn.setLastSegmentAng(arc.getTanDirectionOnStartPt() + math.pi)
               
               qad_layer.addLineToLayer(self.plugIn, currLayer, points)               
               return True # fine comando

         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, valori positivi ammessi
         self.waitFor(QadMsg.translate("Command_ARC", "Specificare lunghezza della corda: "), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                      None, "", \
                      QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
         self.isValidPreviousInput = False # per gestire il comando anche in macro         
         return False
                 
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare punto finale dell'arco: " (da step = 1)
      elif self.step == 8: # dopo aver atteso un punto si riavvia il comando
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

         self.endPt = value
         self.plugIn.setLastPoint(self.endPt)

         # imposto il map tool
         self.getPointMapTool().arcEndPt = self.endPt
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_CENTER)
      
         keyWords = QadMsg.translate("Command_ARC", "Angolo") + " " + \
                    QadMsg.translate("Command_ARC", "Direzione") + " " + \
                    QadMsg.translate("Command_ARC", "Raggio")
         msg = QadMsg.translate("Command_ARC", "Specificare centro dell'arco o [Angolo/Direzione/Raggio]: ")          
         # si appresta ad attendere un punto o una parola chiave         
         # msg, inputType, default, keyWords, valori nulli non ammessi
         self.waitFor(msg, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NOT_NULL)
         
         self.step = 9
         return False
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare centro dell'arco o [Angolo/Direzione/Raggio]: " (da step = 8)
      elif self.step == 9: # dopo aver atteso un punto o una parola chiave si riavvia il comando
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
            if value == QadMsg.translate("Command_ARC", "Angolo"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_ANGLE)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, isNullable
               self.waitFor(QadMsg.translate("Command_ARC", "Specificare angolo inscritto: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                            None, "", QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO)
               self.step = 10
               return False                              
            elif value == QadMsg.translate("Command_ARC", "Direzione"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_TAN)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, isNullable
               self.waitFor(QadMsg.translate("Command_ARC", "Specificare direzione tangente per il punto iniziale dell'arco: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                            None, "", QadInputModeEnum.NOT_NULL)
               self.step = 11
               return False            
            elif value == QadMsg.translate("Command_ARC", "Raggio"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_END_PT_KNOWN_ASK_FOR_RADIUS)
               # si appresta ad attendere un punto o un numero reale         
               # msg, inputType, default, keyWords, isNullable
               self.waitFor(QadMsg.translate("Command_ARC", "Specificare raggio dell'arco: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                            None, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
               self.step = 12
               return False                              
         elif type(value) == QgsPoint: # se è stato inserito il centro dell'arco
            self.centerPt = value
            self.plugIn.setLastPoint(value)

            arc = QadArc()         
            if arc.fromStartCenterEndPts(self.startPt, self.centerPt, self.endPt) == True:
               points = arc.asPolyline()
               if points is not None:
                  # se i punti sono così vicini da essere considerati uguali
                  if qad_utils.ptNear(self.startPt, arc.getStartPt()):
                     self.plugIn.setLastSegmentAng(arc.getTanDirectionOnEndPt())
                  else:
                     self.plugIn.setLastSegmentAng(arc.getTanDirectionOnStartPt() + math.pi)
                  
                  qad_layer.addLineToLayer(self.plugIn, currLayer, points)               
                  return True # fine comando
            
            keyWords = QadMsg.translate("Command_ARC", "Angolo") + " " + \
                       QadMsg.translate("Command_ARC", "Direzione") + " " + \
                       QadMsg.translate("Command_ARC", "Raggio")
            msg = QadMsg.translate("Command_ARC", "Specificare centro dell'arco o [Angolo/Direzione/Raggio]: ")          
            # si appresta ad attendere un punto o una parola chiave         
            # msg, inputType, default, keyWords, isNullable
            self.waitFor(msg, \
                         QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                         None, \
                         keyWords, QadInputModeEnum.NOT_NULL)
            self.isValidPreviousInput = False # per gestire il comando anche in macro                     
            return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare angolo inscritto: " (da step = 9)
      elif self.step == 10: # dopo aver atteso un punto o un numero reale si riavvia il comando
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

         if type(value) == QgsPoint:
            self.angle = qad_utils.getAngleBy2Pts(self.startPt, value)             
         else:
            self.angle = value
            
         arc = QadArc()         
         if arc.fromStartEndPtsAngle(self.startPt, self.endPt, self.angle) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.startPt, arc.getStartPt()):
                  self.plugIn.setLastSegmentAng(arc.getTanDirectionOnEndPt())
               else:
                  self.plugIn.setLastSegmentAng(arc.getTanDirectionOnStartPt() + math.pi)
               
               qad_layer.addLineToLayer(self.plugIn, currLayer, points)               
               return True # fine comando

         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, valori non nulli
         self.waitFor(QadMsg.translate("Command_ARC", "Specificare angolo inscritto: "), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                      None, "", \
                      QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO)
         self.isValidPreviousInput = False # per gestire il comando anche in macro         
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare direzione tangente per il punto iniziale dell'arco: " (da step = 9)
      elif self.step == 11: # dopo aver atteso un punto o un numero reale si riavvia il comando
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

         if type(value) == QgsPoint:
            self.angleTan = qad_utils.getAngleBy2Pts(self.startPt, value)             
         else:
            self.angleTan = value

         arc = QadArc()         
         if arc.fromStartEndPtsTan(self.startPt, self.endPt, self.angleTan) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.startPt, arc.getStartPt()):
                  self.plugIn.setLastSegmentAng(arc.getTanDirectionOnEndPt())
               else:
                  self.plugIn.setLastSegmentAng(arc.getTanDirectionOnStartPt() + math.pi)
               
               qad_layer.addLineToLayer(self.plugIn, currLayer, points)               
               return True # fine comando

         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, isNullable
         self.waitFor(QadMsg.translate("Command_ARC", "Specificare direzione tangente per il punto iniziale dell'arco: "), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.ANGLE, \
                      None, "", QadInputModeEnum.NOT_NULL)
         self.isValidPreviousInput = False # per gestire il comando anche in macro
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA "Specificare raggio dell'arco: " (da step = 9)
      elif self.step == 12: # dopo aver atteso un punto o un numero reale si riavvia il comando
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

         if type(value) == QgsPoint:
            self.radius = qad_utils.getDistance(self.endPt, value)             
         else:
            self.radius = value

         self.plugIn.setLastRadius(self.radius)
         
         arc = QadArc()
         if arc.fromStartEndPtsRadius(self.startPt, self.endPt, self.radius) == True:
            points = arc.asPolyline()
            if points is not None:
               # se i punti sono così vicini da essere considerati uguali
               if qad_utils.ptNear(self.startPt, arc.getStartPt()):
                  self.plugIn.setLastSegmentAng(arc.getTanDirectionOnEndPt())
               else:
                  self.plugIn.setLastSegmentAng(arc.getTanDirectionOnStartPt() + math.pi)
               
               qad_layer.addLineToLayer(self.plugIn, currLayer, points)               
               return True # fine comando

         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, valori positivi
         self.waitFor(QadMsg.translate("Command_ARC", "Specificare raggio dell'arco: "), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                      None, "", \
                      QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
         self.isValidPreviousInput = False # per gestire il comando anche in macro
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA CENTRO DELL'ARCO (da step = 1)
      elif self.step == 13: # dopo aver atteso un punto si riavvia il comando
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

         self.centerPt = value
         self.plugIn.setLastPoint(value)

         # imposto il map tool
         self.getPointMapTool().arcCenterPt = self.centerPt
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.CENTER_PT_KNOWN_ASK_FOR_START_PT)

         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.translate("Command_ARC", "Specificare punto iniziale dell'arco: "))
         self.step = 14
         
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO INIZIALE DELL'ARCO (da step = 13)
      elif self.step == 14: # dopo aver atteso un punto si riavvia il comando
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

         self.startPt = value
         self.plugIn.setLastPoint(value)

         # imposto il map tool
         self.getPointMapTool().arcStartPt = self.startPt
         self.getPointMapTool().setMode(Qad_arc_maptool_ModeEnum.START_CENTER_PT_KNOWN_ASK_FOR_END_PT)
         
         keyWords = QadMsg.translate("Command_ARC", "Angolo") + " " + \
                    QadMsg.translate("Command_ARC", "Lunghezza")
         msg = QadMsg.translate("Command_ARC", "Specificare punto finale dell'arco o [Angolo/Lunghezza corda]: ")                   
         # si appresta ad attendere un punto o una parola chiave         
         # msg, inputType, default, keyWords, isNullable
         self.waitFor(msg, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NOT_NULL)
         
         self.step = 5
         return False
