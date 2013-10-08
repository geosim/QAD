# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando MBUFFER per creare oggetti originati da buffer su altri oggetti
 
                              -------------------
        begin                : 2013-09-19
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
from qad_mbuffer_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_textwindow import *
from qad_ssget_cmd import QadSSGetClass
from qad_entity import *
import qad_utils

# Classe che gestisce il comando MBUFFER
class QadMBUFFERCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.get(169) # "MBUFFER"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runMBUFFERCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/mbuffer.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.get(170)
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      # se questo flag = True il comando serve all'interno di un altro comando per disegnare una linea
      # che non verrà salvata su un layer
      self.virtualCmd = False
      self.SSGetClass = QadSSGetClass(plugIn)
      self.entitySet = QadEntitySet()
      self.width = 0
      self.segments = self.plugIn.segments
      self.segments = 3 # roby

   def __del__(self):
      QadCommandClass.__del__(self)
      del SSGetClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 0: # quando si è in fase di selezione entità
         return self.SSGetClass.getPointMapTool()
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_mbuffer_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None

   def AddGeoms(self, currLayer):
      bufferGeoms = []
      
      for layerEntitySet in self.entitySet.layerEntitySetList:
         geoms = layerEntitySet.getGeometryCollection()
         width = qad_utils.distMapToLayerCoordinates(self.width, \
                                                     self.SSGetClass.getPointMapTool().canvas,\
                                                     layerEntitySet.layer)
         tolerance = qad_utils.distMapToLayerCoordinates(QadVariables.get("TOLERANCE2APPROXCURVE"), \
                                                         self.SSGetClass.getPointMapTool().canvas,\
                                                         layerEntitySet.layer)
         coordTransform = QgsCoordinateTransform(layerEntitySet.layer.crs(),\
                                                 currLayer.crs()) # trasformo la geometria
         
         for geom in geoms:
            g = qad_utils.ApproxCurvesOnGeom(geom.buffer(width, self.segments), self.segments, tolerance)
            g.transform(coordTransform)            
            bufferGeoms.append(g)

      return qad_utils.addGeomsToLayer(self.plugIn, currLayer, bufferGeoms)               
            
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.get(128)) # "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate\n"
         return True # fine comando

      if self.virtualCmd == False: # se si vuole veramente salvare la polylinea in un layer   
         currLayer = qad_utils.getCurrLayerEditable(self.plugIn.canvas, QGis.Polygon)
         if currLayer is None:
            self.showMsg(QadMsg.get(53)) # "\nIl layer corrente non è valido\n"
            return True # fine comando
            
      #=========================================================================
      # RICHIESTA SELEZIONE OGGETTI
      if self.step == 0: # inizio del comando
         if self.SSGetClass.run(msgMapTool, msg) == True:
            # selezione terminata
            self.step = 1
            return self.run(msgMapTool, msg)
      
      #=========================================================================
      # BUFFER OGGETTI
      elif self.step == 1:
         self.entitySet.set(self.SSGetClass.entitySet)
         
         if self.entitySet.count() == 0:
            return True # fine comando

         # imposto il map tool
         self.getPointMapTool().setMode(Qad_mbuffer_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT)                                
        
         # si appresta ad attendere un punto o un numero reale         
         # msg, inputType, default, keyWords, valori positivi
         # "Specificare larghezza buffer <{0}>:  "
         msg = QadMsg.get(171)
         
         self.waitFor(msg.format(str(self.plugIn.lastRadius)), \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT, \
                      self.plugIn.lastRadius, "", \
                      QadInputModeEnum.NOT_NULL | QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
                  
         self.step = 2     
         return False
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA LARGHEZZA (da step = 1)
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

         if type(value) == QgsPoint:
            self.startPtForBufferWidth = value
            
            # imposto il map tool
            self.getPointMapTool().startPtForBufferWidth = self.startPtForBufferWidth
            self.getPointMapTool().entitySet.set(self.entitySet)
            self.getPointMapTool().segments = self.segments
            self.getPointMapTool().setMode(Qad_mbuffer_maptool_ModeEnum.FIRST_PT_ASK_FOR_BUFFER_WIDTH)
         
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.get(93)) # "Specificare secondo punto: "
            self.step = 3
            return False            
         else:
            self.width = value
            self.plugIn.setLastRadius(self.width)

            if self.virtualCmd == False: # se si vuole veramente salvare i buffer in un layer
               self.AddGeoms(currLayer)           

            return True # fine comando

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO DELLA LARGHEZZA BUFFER (da step = 2)
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

         self.width = qad_utils.getDistance(self.startPtForBufferWidth, value)
         self.plugIn.setLastRadius(self.width)     

         if self.virtualCmd == False: # se si vuole veramente salvare i buffer in un layer
            self.AddGeoms(currLayer)               

         return True # fine comando