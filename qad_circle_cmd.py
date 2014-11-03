# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando CIRCLE per disegnare un cerchio
 
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


import qad_debug
from qad_getpoint import *
from qad_circle_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_textwindow import *
from qad_entity import *
import qad_utils
import qad_layer


# Classe che gestisce il comando PLINE
class QadCIRCLECommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "CERCHIO")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runCIRCLECommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/circle.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_CIRCLE", "Disegna un cerchio mediante diversi metodi.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      # se questo flag = True il comando serve all'interno di un altro comando per disegnare un cerchio
      # che non verrà salvato su un layer
      self.virtualCmd = False
      self.centerPt = None
      self.radius = None
      self.area = 100      

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_circle_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None
         
   def run(self, msgMapTool = False, msg = None):
      self.isValidPreviousInput = True # per gestire il comando anche in macro

      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando

      currLayer = None
      if self.virtualCmd == False: # se si vuole veramente salvare il cerchio in un layer   
         # il layer corrente deve essere editabile e di tipo linea o poligono
         currLayer, errMsg = qad_layer.getCurrLayerEditable(self.plugIn.canvas, [QGis.Line, QGis.Polygon])
         if currLayer is None:
            self.showErr(errMsg)
            return True # fine comando
         self.getPointMapTool().geomType = QGis.Line if currLayer.geometryType() == QGis.Line else QGis.Polygon                                   

      #=========================================================================
      # RICHIESTA PRIMO PUNTO o CENTRO
      if self.step == 0: # inizio del comando
         # imposto il map tool
         self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_CENTER_PT)        
         keyWords = QadMsg.translate("Command_CIRCLE", "3P") + "/" + \
                    QadMsg.translate("Command_CIRCLE", "2P") + "/" + \
                    QadMsg.translate("Command_CIRCLE", "Ttr (tangente tangente raggio)")
         prompt = QadMsg.translate("Command_CIRCLE", "Specificare punto centrale del cerchio o [{0}]: ").format(keyWords)

         # si appresta ad attendere un punto o enter o una parola chiave         
         # msg, inputType, default, keyWords, nessun controllo
         self.waitFor(prompt, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NONE)
         
         self.step = 1
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA CENTRO
      elif self.step == 1: # dopo aver atteso un punto o enter o una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi è stato riattivato il comando che torna qui senza che il maptool
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

         if value is None:
            if self.plugIn.lastPoint is not None:
               value = self.plugIn.lastPoint
            else:
               return True # fine comando

         if type(value) == unicode:
            if value == QadMsg.translate("Command_CIRCLE", "3P"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare primo punto sul cerchio: "))
               self.step = 4           
            elif value == QadMsg.translate("Command_CIRCLE", "2P"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_DIAM_PT)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare prima estremità del diametro del cerchio: "))
               self.step = 7     
            elif value == QadMsg.translate("Command_CIRCLE", "Ttr"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_TAN)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare oggetto per la prima tangente del cerchio: "))
               self.step = 9     
         elif type(value) == QgsPoint: # se è stato inserito il centro del cerchio           
            self.centerPt = value
            self.plugIn.setLastPoint(value)
            
            # imposto il map tool
            self.getPointMapTool().centerPt = self.centerPt
            self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.CENTER_PT_KNOWN_ASK_FOR_RADIUS)                                
           
            keyWords = QadMsg.translate("Command_CIRCLE", "Diametro") + "/" + \
                       QadMsg.translate("Command_CIRCLE", "Area")
            prompt = QadMsg.translate("Command_CIRCLE", "Specificare raggio del cerchio o [{0}]: ").format(keyWords)
            
            # si appresta ad attendere un punto o una parola chiave         
            # msg, inputType, default, keyWords, valori positivi
            self.waitFor(prompt, \
                         QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT | QadInputTypeEnum.KEYWORDS, \
                         None, \
                         keyWords, \
                         QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
            
            self.step = 2
         
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA RAGGIO O DIAMETRO O AREA
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
            if value == QadMsg.translate("Command_CIRCLE", "Diametro"):
               # imposto il map tool
               self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.CENTER_PT_KNOWN_ASK_FOR_DIAM)
               # si appresta ad attendere un punto o un numero reale   
               # msg, inputType, default, keyWords, valori positivi
               self.waitFor(QadMsg.translate("Command_CIRCLE", "Specificare diametro del cerchio: "), \
                            QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                            None, \
                            "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
               self.step = 3           
            elif value == QadMsg.translate("Command_CIRCLE", "Area"):
               msg = QadMsg.translate("Command_CIRCLE", "Digitare l'area del cerchio in unità correnti <{0}>: ")
               # si appresta ad attendere un numero reale         
               # msg, inputType, default, keyWords, valori positivi
               self.waitFor(msg.format(str(self.area)), QadInputTypeEnum.FLOAT, \
                            self.area, "", \
                            QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
               self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_CENTER_PT)
               self.step = 13         
         elif type(value) == QgsPoint or type(value) == float: # se è stato inserito il raggio del cerchio            
            if type(value) == QgsPoint: # se è stato inserito il raggio del cerchio con un punto                        
               self.radius = qad_utils.getDistance(self.centerPt, value)
            else:
               self.radius = value
               
            self.plugIn.setLastRadius(self.radius)     

            circle = QadCircle()
            circle.set(self.centerPt, self.radius)
            points = circle.asPolyline()
            if points is not None:
               if self.virtualCmd == False: # se si vuole veramente salvare il cerchio in un layer
                  if currLayer.geometryType() == QGis.Line:
                     qad_layer.addLineToLayer(self.plugIn, currLayer, points)
                  else:
                     qad_layer.addPolygonToLayer(self.plugIn, currLayer, points)               
               return True # fine comando
            
            keyWords = QadMsg.translate("Command_CIRCLE", "Diametro") + "/" + \
                       QadMsg.translate("Command_CIRCLE", "Area")
            prompt = QadMsg.translate("Command_CIRCLE", "Specificare raggio del cerchio o [{0}]: ").format(keyWords)
                                 
            # si appresta ad attendere un punto o una parola chiave         
            # msg, inputType, default, keyWords, valori positivi
            self.waitFor(prompt, \
                         QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                         None, \
                         keyWords, QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
            self.isValidPreviousInput = False # per gestire il comando anche in macro                       
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DIAMETRO DEL CERCHIO (da step = 2)
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

         if type(value) == QgsPoint: # se è stato inserito un punto          
            self.radius = qad_utils.getDistance(self.centerPt, value) / 2
         elif type(value) == float: # se è stato inserito unnumero reale
            self.radius = value

         self.plugIn.setLastRadius(self.radius)     
      
         circle = QadCircle()         
         circle.set(self.centerPt, self.radius)
         points = circle.asPolyline()
         if points is not None:
            if self.virtualCmd == False: # se si vuole veramente salvare il cerchio in un layer   
               if currLayer.geometryType() == QGis.Line:
                  qad_layer.addLineToLayer(self.plugIn, currLayer, points)
               else:
                  qad_layer.addPolygonToLayer(self.plugIn, currLayer, points)               
            return True # fine comando
      
         # si appresta ad attendere un punto o un numero reale   
         # msg, inputType, default, keyWords, valori positivi
         self.waitFor(QadMsg.translate("Command_CIRCLE", "Specificare diametro del cerchio: "), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                      None, \
                      "", \
                      QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
         self.isValidPreviousInput = False # per gestire il comando anche in macro     
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL PRIMO PUNTO DEL CERCHIO (da step = 1)
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
               
            snapTypeOnSel = self.getPointMapTool().snapTypeOnSelection
            value = self.getPointMapTool().point
            entity = self.getPointMapTool().entity
         else: # il punto arriva come parametro della funzione
            value = msg
            snapTypeOnSel = QadSnapTypeEnum.NONE

         # se è stato selezionato un punto con la modalità TAN_DEF è un punto differito
         if snapTypeOnSel == QadSnapTypeEnum.TAN_DEF and entity.isInitialized():
            self.firstPt = None
            self.firstPtTan = value
            self.firstGeomTan = QgsGeometry(entity.getGeometry()) # duplico la geometria         
            coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapRenderer().destinationCrs()) # trasformo la geometria
            self.firstGeomTan.transform(coordTransform)         
            # imposto il map tool
            self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)
         else: # altrimenti è un punto esplicito 
            self.firstPt = value
            self.plugIn.setLastPoint(value)    
            # imposto il map tool
            self.getPointMapTool().firstPt = self.firstPt
            self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)
   
         # si appresta ad attendere un punto         
         self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare secondo punto sul cerchio: "))
         
         self.step = 5
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL SECONDO PUNTO DEL CERCHIO (da step = 4)
      elif self.step == 5:  # dopo aver atteso un punto si riavvia il comando
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

            snapTypeOnSel = self.getPointMapTool().snapTypeOnSelection
            value = self.getPointMapTool().point
            entity = self.getPointMapTool().entity
         else: # il punto arriva come parametro della funzione
            value = msg
            snapTypeOnSel = QadSnapTypeEnum.NONE

         # se è stato selezionato un punto con la modalità TAN_DEF è un punto differito
         if snapTypeOnSel == QadSnapTypeEnum.TAN_DEF and entity.isInitialized():
            self.secondPt = None
            self.secondPtTan = value
            self.secondGeomTan = QgsGeometry(entity.getGeometry()) # duplico la geometria         
            coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapRenderer().destinationCrs()) # trasformo la geometria
            self.secondGeomTan.transform(coordTransform)         
            # imposto il map tool
            self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.FIRST_SECOND_PT_KNOWN_ASK_FOR_THIRD_PT)
         else: # altrimenti è un punto esplicito 
            self.secondPt = value
            self.plugIn.setLastPoint(value)    
            # imposto il map tool
            self.getPointMapTool().secondPt = self.secondPt
            self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.FIRST_SECOND_PT_KNOWN_ASK_FOR_THIRD_PT)
   
         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare terzo punto sul cerchio: "))
         
         self.step = 6
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL TERZO PUNTO DEL CERCHIO (da step = 5)
      elif self.step == 6:  # dopo aver atteso un punto si riavvia il comando
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

            snapTypeOnSel = self.getPointMapTool().snapTypeOnSelection
            value = self.getPointMapTool().point
            entity = self.getPointMapTool().entity
         else: # il punto arriva come parametro della funzione
            value = msg
            snapTypeOnSel = QadSnapTypeEnum.NONE

         # se è stato selezionato un punto con la modalità TAN_DEF è un punto differito
         if snapTypeOnSel == QadSnapTypeEnum.TAN_DEF and entity.isInitialized():
            self.thirdPt = None
            self.thirdPtTan = value
            self.thirdGeomTan = QgsGeometry(entity.getGeometry()) # duplico la geometria         
            coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapRenderer().destinationCrs()) # trasformo la geometria
            self.thirdGeomTan.transform(coordTransform)         
         else: # altrimenti è un punto esplicito 
            self.thirdPt = value
            self.plugIn.setLastPoint(value)    

         #qad_debug.breakPoint()
         circle = QadCircle()                  
         points = None
         if self.firstPt is None: # se il primo punto è definito con un punto differito
            if self.secondPt is None: # se il secondo punto è definito con un punto differito
               if self.thirdPt is None: # se il terzo punto è definito con un punto differito
                  if circle.from3TanPts(self.firstGeomTan, self.firstPtTan, \
                                        self.secondGeomTan, self.secondPtTan, \
                                        self.thirdGeomTan, self.thirdPtTan) == True:
                     points = circle.asPolyline()
               else: # se il terzo punto è definito con un punto esplicito
                  if circle.from1IntPt2TanPts(self.thirdPt, self.firstGeomTan, self.firstPtTan,
                                              self.secondGeomTan, self.secondPtTan) == True:
                     points = circle.asPolyline()
            else: # se il secondo punto è definito con un punto esplicito
               if self.thirdPt is None: # se il terzo punto è definito con un punto differito
                  if circle.from1IntPt2TanPts(self.secondPt, self.firstGeomTan, self.firstPtTan,
                                              self.thirdGeomTan, self.thirdPtTan) == True:
                     points = circle.asPolyline()
               else: # se il terzo punto è definito con un punto esplicito
                  if circle.from2IntPts1TanPt(self.secondPt, self.thirdPt, \
                                              self.firstGeomTan, self.firstPtTan) == True:
                     points = circle.asPolyline()
         else: # se il primo punto è definito con un punto esplicito
            if self.secondPt is None: # se il secondo punto è definito con un punto differito
               if self.thirdPt is None: # se il terzo punto è definito con un punto differito
                  if circle.from1IntPt2TanPts(self.firstPt, self.secondGeomTan, self.secondPtTan,
                                              self.thirdGeomTan, self.thirdPtTan) == True:
                     points = circle.asPolyline()
               else: # se il terzo punto è definito con un punto esplicito
                  if circle.from2IntPts1TanPt(self.firstPt, self.thirdPt, \
                                              self.secondGeomTan, self.secondPtTan) == True:
                     points = circle.asPolyline()
            else: # se il secondo punto è definito con un punto esplicito
               if self.thirdPt is None: # se il terzo punto è definito con un punto differito
                  if circle.from2IntPts1TanPt(self.firstPt, self.secondPt, \
                                              self.thirdGeomTan, self.thirdPtTan) == True:
                     points = circle.asPolyline()
               else: # se il terzo punto è definito con un punto esplicito
                  if circle.from3Pts(self.firstPt, self.secondPt, value) == True:
                     points = circle.asPolyline()
                     
         if points is not None:
            self.centerPt = circle.center
            self.radius = circle.radius           
            if self.virtualCmd == False: # se si vuole veramente salvare il cerchio in un layer   
               if currLayer.geometryType() == QGis.Line:
                  qad_layer.addLineToLayer(self.plugIn, currLayer, points)
               else:
                  qad_layer.addPolygonToLayer(self.plugIn, currLayer, points)               
            return True # fine comando
         
         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare terzo punto sul cerchio: "))
         self.isValidPreviousInput = False # per gestire il comando anche in macro     
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA PRIMA ESTREMITA' DIAM DEL CERCHIO (da step = 1)
      elif self.step == 7:  # dopo aver atteso un punto si riavvia il comando
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

            snapTypeOnSel = self.getPointMapTool().snapTypeOnSelection
            value = self.getPointMapTool().point
            entity = self.getPointMapTool().entity
         else: # il punto arriva come parametro della funzione
            value = msg
            snapTypeOnSel = QadSnapTypeEnum.NONE

         # se è stato selezionato un punto con la modalità TAN_DEF è un punto differito
         if snapTypeOnSel == QadSnapTypeEnum.TAN_DEF and entity.isInitialized():
            self.firstDiamPt = None
            self.firstDiamPtTan = value
            self.firstDiamGeomTan = QgsGeometry(entity.getGeometry()) # duplico la geometria         
            coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapRenderer().destinationCrs()) # trasformo la geometria
            self.firstDiamGeomTan.transform(coordTransform)         
            # imposto il map tool
            self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.FIRST_DIAM_PT_KNOWN_ASK_FOR_SECOND_DIAM_PT)
         else: # altrimenti è un punto esplicito 
            self.firstDiamPt = value        
            # imposto il map tool
            self.getPointMapTool().firstDiamPt = self.firstDiamPt
            self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.FIRST_DIAM_PT_KNOWN_ASK_FOR_SECOND_DIAM_PT)
   
         # si appresta ad attendere un punto         
         self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare seconda estremità del diametro del cerchio: "))
         
         self.step = 8
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA SECONDA ESTREMITA' DIAM DEL CERCHIO (da step = 7)
      elif self.step == 8:  # dopo aver atteso un punto si riavvia il comando
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

            snapTypeOnSel = self.getPointMapTool().snapTypeOnSelection
            value = self.getPointMapTool().point
            entity = self.getPointMapTool().entity
         else: # il punto arriva come parametro della funzione
            value = msg
            snapTypeOnSel = QadSnapTypeEnum.NONE

         # se è stato selezionato un punto con la modalità TAN_DEF è un punto differito
         if snapTypeOnSel == QadSnapTypeEnum.TAN_DEF and entity.isInitialized():
            self.secondDiamPt = None
            self.secondDiamPtTan = value
            self.secondDiamGeomTan = QgsGeometry(entity.getGeometry()) # duplico la geometria
            coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapRenderer().destinationCrs()) # trasformo la geometria
            self.secondDiamGeomTan.transform(coordTransform)            
         else: # altrimenti è un punto esplicito 
            self.secondDiamPt = value  
         
         circle = QadCircle()                  
         points = None
         if self.firstDiamPt is None: # se il diametro è definito con il primo punto differito
            if self.secondDiamPt is None: # il diametro è definito con il secondo punto differito
               if circle.fromDiamEnds2TanPts(self.firstDiamGeomTan, self.firstDiamPtTan, \
                                             self.secondDiamGeomTan, self.secondDiamPtTan) == True:
                  points = circle.asPolyline()
            else: # se il diametro è definito con il secondo punto esplicito
               if circle.fromDiamEndsPtTanPt(self.secondDiamPt, self.firstDiamGeomTan, self.firstDiamPtTan) == True:
                  points = circle.asPolyline()
         else: # se il diametro è definito con il primo punto esplicito
            if self.secondDiamPt is None: # il diametro è definito con il secondo punto differito
               if circle.fromDiamEndsPtTanPt(self.firstDiamPt, self.secondDiamGeomTan, self.secondDiamPtTan) == True:
                  points = circle.asPolyline()
            else: # se il diametro è definito con il secondo punto esplicito
               if circle.fromDiamEnds(self.firstDiamPt, self.secondDiamPt) == True:
                  points = circle.asPolyline()
                  
         if points is not None:
            self.centerPt = circle.center
            self.radius = circle.radius
            if self.virtualCmd == False: # se si vuole veramente salvare il cerchio in un layer   
               if currLayer.geometryType() == QGis.Line:
                  qad_layer.addLineToLayer(self.plugIn, currLayer, points)
               else:
                  qad_layer.addPolygonToLayer(self.plugIn, currLayer, points)             
            return True # fine comand         
         
         # si appresta ad attendere un punto
         self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare seconda estremità del diametro del cerchio: "))
         self.isValidPreviousInput = False # per gestire il comando anche in macro     
         return False

                 
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PRIMA TANGENTE (da step = 1)
      elif self.step == 9: # dopo aver atteso un punto si riavvia il comando
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

            entity = self.getPointMapTool().entity
         else: # il punto arriva come parametro della funzione
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare oggetto per la prima tangente del cerchio: "))
            self.isValidPreviousInput = False # per gestire il comando anche in macro     
            return False

         if not entity.isInitialized(): # se non è stata selezionata una entità
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare oggetto per la prima tangente del cerchio: "))
            self.isValidPreviousInput = False # per gestire il comando anche in macro     
            return False
         
         wkbType = entity.getGeometry().wkbType()
         if wkbType == QGis.WKBPoint or wkbType == QGis.WKBMultiPoint:     
            self.showErr(QadMsg.translate("Command_CIRCLE", "\nSelezionare un cerchio, un arco o una linea."))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare oggetto per la prima tangente del cerchio: "))
            self.isValidPreviousInput = False # per gestire il comando anche in macro
            return False
         
         self.tanGeom1 = QgsGeometry(entity.getGeometry())         
         coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapRenderer().destinationCrs()) # trasformo la geometria
         self.tanGeom1.transform(coordTransform)         
         self.tanPt1 = self.getPointMapTool().point

         # imposto il map tool
         self.getPointMapTool().tanGeom1 = self.tanGeom1
         self.getPointMapTool().tanPt1 = self.tanPt1
         self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.FIRST_TAN_KNOWN_ASK_FOR_SECOND_TAN)
      
         # si appresta ad attendere un punto         
         self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare oggetto per la seconda tangente del cerchio: "))
         self.step = 10
         return False
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDA TANGENTE (da step = 9)
      elif self.step == 10: # dopo aver atteso un punto si riavvia il comando
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

            entity = self.getPointMapTool().entity
         else: # il punto arriva come parametro della funzione
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare oggetto per la seconda tangente del cerchio: "))
            self.isValidPreviousInput = False # per gestire il comando anche in macro
            return False

         if not entity.isInitialized(): # se non è stata selezionata una entità
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare oggetto per la seconda tangente del cerchio: "))
            self.isValidPreviousInput = False # per gestire il comando anche in macro
            return False

         wkbType = entity.getGeometry().wkbType()
         if wkbType == QGis.WKBPoint or wkbType == QGis.WKBMultiPoint:     
            self.showErr(QadMsg.translate("Command_CIRCLE", "\nSelezionare un cerchio, un arco o una linea."))
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare oggetto per la seconda tangente del cerchio: "))
            self.isValidPreviousInput = False # per gestire il comando anche in macro
            return False
         
         self.tanGeom2 = QgsGeometry(entity.getGeometry())
         coordTransform = QgsCoordinateTransform(entity.layer.crs(), self.plugIn.canvas.mapRenderer().destinationCrs()) # trasformo la geometria
         self.tanGeom2.transform(coordTransform)                  
         self.tanPt2 = self.getPointMapTool().point

         # imposto il map tool
         self.getPointMapTool().tanGeom2 = self.tanGeom2
         self.getPointMapTool().tanPt2 = self.tanPt2
         self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.FIRST_SECOND_TAN_KNOWN_ASK_FOR_RADIUS)
      
         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, valori positivi
         msg = QadMsg.translate("Command_CIRCLE", "Specificare raggio del cerchio <{0}>: ")
         self.waitFor(msg.format(str(self.plugIn.lastRadius)), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                      self.plugIn.lastRadius, "", \
                      QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
         self.step = 11
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA RAGGIO (da step = 10)
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
            self.startPtForRadius = value
            
            # imposto il map tool
            self.getPointMapTool().startPtForRadius = self.startPtForRadius
            self.getPointMapTool().setMode(Qad_circle_maptool_ModeEnum.FIRST_SECOND_TAN_FIRSTPTRADIUS_KNOWN_ASK_FOR_SECONDPTRADIUS)
         
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_CIRCLE", "Specificare secondo punto: "))
            self.step = 12
            return False            
         else:
            self.plugIn.setLastRadius(value)

            circle = QadCircle()
            if circle.from2TanPtsRadius(self.tanGeom1, self.tanPt1, \
                                        self.tanGeom2, self.tanPt2, value) == True:
               points = circle.asPolyline()
               if points is not None:
                  self.centerPt = circle.center
                  self.radius = circle.radius
                  if self.virtualCmd == False: # se si vuole veramente salvare il cerchio in un layer   
                     if currLayer.geometryType() == QGis.Line:
                        qad_layer.addLineToLayer(self.plugIn, currLayer, points)
                     else:
                        qad_layer.addPolygonToLayer(self.plugIn, currLayer, points)               
               else:
                  self.showMsg(QadMsg.translate("Command_CIRCLE", "\nIl cerchio non esiste."))
            else:
               self.showMsg(QadMsg.translate("Command_CIRCLE", "\nIl cerchio non esiste."))
                  
            return True # fine comando

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO DEL RAGGIO (da step = 11)
      elif self.step == 12: # dopo aver atteso un punto si riavvia il comando
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

         self.radius = qad_utils.getDistance(self.startPtForRadius, value)
         self.plugIn.setLastRadius(self.radius)     

         circle = QadCircle()                  
         if circle.from2TanPtsRadius(self.tanGeom1, self.tanPt1, \
                                     self.tanGeom2, self.tanPt2, self.radius) == True:
            points = circle.asPolyline()
            if points is not None:
               self.centerPt = circle.center
               self.radius = circle.radius
               if self.virtualCmd == False: # se si vuole veramente salvare il cerchio in un layer   
                  if currLayer.geometryType() == QGis.Line:
                     qad_layer.addLineToLayer(self.plugIn, currLayer, points)
                  else:
                     qad_layer.addPolygonToLayer(self.plugIn, currLayer, points)               
            else:
               self.showMsg(QadMsg.translate("Command_CIRCLE", "\nIl cerchio non esiste."))
         else:
            self.showMsg(QadMsg.translate("Command_CIRCLE", "\nIl cerchio non esiste."))
         return True # fine comando

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA AREA DEL CERCHIO (da step = 2)
      elif self.step == 13: # dopo aver atteso un numero si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton != True: # se NON usato il tasto destro del mouse
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == float: # è stata inserita l'area
            self.area = value
      
            circle = QadCircle()         
            circle.fromCenterArea(self.centerPt, self.area)
            self.radius = circle.radius 
            self.plugIn.setLastRadius(self.radius)     
            points = circle.asPolyline()
            if points is not None:
               if self.virtualCmd == False: # se si vuole veramente salvare il cerchio in un layer   
                  if currLayer.geometryType() == QGis.Line:
                     qad_layer.addLineToLayer(self.plugIn, currLayer, points)
                  else:
                     qad_layer.addPolygonToLayer(self.plugIn, currLayer, points)               
               return True # fine comando

         self.isValidPreviousInput = False # per gestire il comando anche in macro      
         return False
