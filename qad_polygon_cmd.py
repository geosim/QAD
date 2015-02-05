# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando POLYGON per disegnare un poligono regolare
 
                              -------------------
        begin                : 2014-11-17
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


from qad_polygon_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_textwindow import *
import qad_utils
import qad_layer


# Classe che gestisce il comando POLYGON
class QadPOLYGONCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "POLIGONO")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runPOLYGONCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/polygon.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_POLYGON", "Crea un poligono regolare.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      # se questo flag = True il comando serve all'interno di un altro comando per disegnare un rettangolo
      # che non verrà salvato su un layer
      self.virtualCmd = False
      self.centerPt = None
      self.firstEdgePt = None
      self.vertices = []
      self.sideNumber = self.plugIn.lastPolygonSideNumber
      self.constructionModeByCenter = self.plugIn.lastPolygonConstructionModeByCenter
      self.area = 100

   def __del__(self):
      QadCommandClass.__del__(self)

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_polygon_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None       

      
   def addPolygonToLayer(self, layer):
      if layer.geometryType() == QGis.Line:
         qad_layer.addLineToLayer(self.plugIn, layer, self.vertices)
      elif layer.geometryType() == QGis.Polygon:                          
         qad_layer.addPolygonToLayer(self.plugIn, layer, self.vertices)
      

   #============================================================================
   # WaitForSideNumber
   #============================================================================
   def WaitForSideNumber(self):
      self.step = 1
      prompt = QadMsg.translate("Command_POLYGON", "Digitare il numero dei lati <{0}>: ")
      self.waitForInt(prompt.format(str(self.sideNumber)), self.sideNumber, \
                      QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
         
   #============================================================================
   # WaitForCenter
   #============================================================================
   def WaitForCenter(self):
      self.step = 2
      self.getPointMapTool().setMode(Qad_polygon_maptool_ModeEnum.ASK_FOR_CENTER_PT)
      
      keyWords = QadMsg.translate("Command_POLYGON", "Spigolo")
      prompt = QadMsg.translate("Command_POLYGON", "Specificare centro del poligono [{0}]: ").format(keyWords)
     
      # si appresta ad attendere un punto o enter
      #                        msg, inputType,              default, keyWords, nessun controllo         
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, keyWords, QadInputModeEnum.NONE)
         
   #============================================================================
   # WaitForInscribedCircumscribedOption
   #============================================================================
   def WaitForInscribedCircumscribedOption(self):
      self.step = 3      
      keyWords = QadMsg.translate("Command_POLYGON", "Inscritto nel cerchio") + "/" + \
                 QadMsg.translate("Command_POLYGON", "Circoscritto intorno al cerchio") + "/" + \
                 QadMsg.translate("Command_POLYGON", "Area")
      prompt = QadMsg.translate("Command_POLYGON", "Digitare un'opzione [{0}] <{1}>: ").format(keyWords, \
                                                                                               self.constructionModeByCenter)

      # si appresta ad attendere una parola chiave         
      # msg, inputType, default, keyWords, valori positivi
      self.waitFor(prompt, QadInputTypeEnum.KEYWORDS, \
                   self.constructionModeByCenter, \
                   keyWords, QadInputModeEnum.NONE)                  

   #============================================================================
   # WaitForRadius
   #============================================================================
   def WaitForRadius(self, layer):
      self.step = 4
      if layer is not None:
         self.getPointMapTool().geomType = layer.geometryType()
      self.getPointMapTool().setMode(Qad_polygon_maptool_ModeEnum.CENTER_PT_KNOWN_ASK_FOR_RADIUS)
      
      # si appresta ad attendere un punto o un numero reale         
      # msg, inputType, default, keyWords, valori positivi
      prompt = QadMsg.translate("Command_CIRCLE", "Specificare raggio del cerchio <{0}>: ")
      self.waitFor(prompt.format(str(self.plugIn.lastRadius)), \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                   self.plugIn.lastRadius, "", \
                   QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)

   #============================================================================
   # WaitForFirstEdgePt
   #============================================================================
   def WaitForFirstEdgePt(self):
      self.step = 5
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_polygon_maptool_ModeEnum.ASK_FOR_FIRST_EDGE_PT)
      # si appresta ad attendere un punto
      self.waitForPoint(QadMsg.translate("Command_POLYGON", "Specificare primo punto dello spigolo: "))

   #============================================================================
   # WaitForSecondEdgePt
   #============================================================================
   def WaitForSecondEdgePt(self, layer):
      self.step = 6
      self.getPointMapTool().firstEdgePt = self.firstEdgePt

      if layer is not None:
         self.getPointMapTool().geomType = layer.geometryType()

      # imposto il map tool
      self.getPointMapTool().setMode(Qad_polygon_maptool_ModeEnum.FIRST_EDGE_PT_KNOWN_ASK_FOR_SECOND_EDGE_PT)
      # si appresta ad attendere un punto
      self.waitForPoint(QadMsg.translate("Command_POLYGON", "Specificare secondo punto dello spigolo: "))       

   #============================================================================
   # WaitForArea
   #============================================================================
   def WaitForArea(self):
      self.step = 7
         
      msg = QadMsg.translate("Command_POLYGON", "Digitare l'area del poligono in unità correnti <{0}>: ")
      # si appresta ad attendere un numero reale         
      # msg, inputType, default, keyWords, valori positivi
      self.waitFor(msg.format(str(self.area)), QadInputTypeEnum.FLOAT, \
                   self.area, "", \
                   QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)

         
   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando

      currLayer = None
      if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
         # il layer corrente deve essere editabile e di tipo linea o poligono
         currLayer, errMsg = qad_layer.getCurrLayerEditable(self.plugIn.canvas, [QGis.Line, QGis.Polygon])
         if currLayer is None:
            self.showErr(errMsg)
            return True # fine comando
      
      #=========================================================================
      # RICHIESTA NUMERO DI LATI DEL POLIGONO 
      if self.step == 0: # inizio del comando
         self.WaitForSideNumber()
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL NUMERO DI LATI DEL POLIGONO (da step = 0) 
      elif self.step == 1: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
               value = self.sideNumber
            else:
               return False
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == int:
            if value < 3:
               self.showErr(QadMsg.translate("Command_POLYGON", "\né richiesto un valore intero maggiore di 2."))
            else:
               self.sideNumber = value
               self.getPointMapTool().sideNumber = self.sideNumber
               self.plugIn.setLastPolygonSideNumber(self.sideNumber)
               self.WaitForCenter()
         else:
            self.WaitForSideNumber()    

         return False # continua


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL CENTRO DEL POLIGONO (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  self.WaitForCenter()
                  return False
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_POLYGON", "Spigolo"):
               self.WaitForFirstEdgePt()
         elif type(value) == QgsPoint:
            self.centerPt = value
            self.getPointMapTool().centerPt = self.centerPt
            self.WaitForInscribedCircumscribedOption() 
                       
         return False # continua

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI POLIGONO INSCRITTO O CIRCOSCRITTO (da step = 2)
      elif self.step == 3:
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = self.constructionModeByCenter
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # la parola chiave arriva come parametro della funzione
            value = msg        
         
         if type(value) == unicode:        
            self.constructionModeByCenter = value
            self.plugIn.setLastPolygonConstructionModeByCenter(self.constructionModeByCenter)        
            self.getPointMapTool().constructionModeByCenter = self.constructionModeByCenter
            if self.constructionModeByCenter == QadMsg.translate("Command_POLYGON", "Area"):
               self.WaitForArea()
            else:
               self.WaitForRadius(currLayer)
               
         return False # fine comando

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL RAGGIO (da step = 3)
      elif self.step == 4:
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

         if type(value) == QgsPoint or type(value) == float: # se é stato inserito il raggio del cerchio            
            if type(value) == QgsPoint: # se é stato inserito il raggio del cerchio con un punto                        
               self.radius = qad_utils.getDistance(self.centerPt, value)
               ptStart = value
            else:
               self.radius = value
               ptStart = None
               
            self.plugIn.setLastRadius(self.radius)     

            mode = True if self.constructionModeByCenter == QadMsg.translate("Command_POLYGON", "Inscritto nel cerchio") else False
            self.vertices.extend(qad_utils.getPolygonByNsidesCenterRadius(self.sideNumber, self.centerPt, self.radius, \
                                                                          mode, ptStart))

            if self.virtualCmd == False: # se si vuole veramente salvare i buffer in un layer
               self.addPolygonToLayer(currLayer)
            return True       
         
         return False # fine comando
 
 
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL PRIMO PUNTO DELLO SPIGOLO (da step = 2)
      elif self.step == 5: # dopo aver atteso un punto si riavvia il comando
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

         if type(value) == QgsPoint:
            self.firstEdgePt = value
            self.WaitForSecondEdgePt(currLayer)

         return False
            
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL SECONDO PUNTO DELLO SPIGOLO (da step = 5)
      elif self.step == 6: # dopo aver atteso un punto o un numero reale si riavvia il comando
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

         if type(value) == QgsPoint:
            self.vertices.extend(qad_utils.getPolygonByNsidesEdgePts(self.sideNumber, self.firstEdgePt, value))

            if self.virtualCmd == False: # se si vuole veramente salvare i buffer in un layer
               self.addPolygonToLayer(currLayer)
            return True       

         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA AREA POLIGONO (da step = 3)
      elif self.step == 7: # dopo aver atteso un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = self.area
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               return False
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == float: # é stata inserita l'area
            self.vertices.extend(qad_utils.getPolygonByNsidesArea(self.sideNumber, self.centerPt, value))

            if self.virtualCmd == False: # se si vuole veramente salvare i buffer in un layer
               self.addPolygonToLayer(currLayer)
            return True       
            
         return False
