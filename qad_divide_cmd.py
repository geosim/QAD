# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando DIVIDE per creare oggetti puntuali a distanza uguale lungo il perimetro o la lunghezza di un oggetto
 
                              -------------------
        begin                : 2016-09-09
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


from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_entsel_cmd import QadEntSelClass
from qad_textwindow import *
from qad_entity import *
from qad_variables import *
import qad_utils
import qad_layer
from qad_dim import *


#===============================================================================
# QadDIVIDECommandClassStepEnum class.
#===============================================================================
class QadDIVIDECommandClassStepEnum():
   ASK_FOR_ENT        = 1 # richiede la selezione di un oggetto (0 è l'inizio del comando)
   ASK_FOR_ALIGNMENT  = 2 # richiede l'allineamento
   ASK_SEGMENT_NUMBER = 3 # richiede il numero di segmenti
   


# Classe che gestisce il comando DIVIDE
class QadDIVIDECommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadDIVIDECommandClass(self.plugIn)
   
   def getName(self):
      return QadMsg.translate("Command_list", "DIVIDE")

   def getEnglishName(self):
      return "DIVIDE"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runDIVIDECommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/divide.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_DIVIDE", "Creates evenly spaced punctual objects along the length or perimeter of an object.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.entSelClass = None
      self.objectAlignment = True
      self.nSegments = 1

   def __del__(self):
      QadCommandClass.__del__(self)
      if self.entSelClass is not None:
         self.entSelClass.entity.deselectOnLayer()
         del self.entSelClass
      

   #============================================================================
   # waitForEntsel
   #============================================================================
   def waitForEntsel(self, msgMapTool, msg):
      if self.entSelClass is not None:
         del self.entSelClass
      self.step = QadDIVIDECommandClassStepEnum.ASK_FOR_ENT
      self.entSelClass = QadEntSelClass(self.plugIn)
      self.entSelClass.msg = QadMsg.translate("Command_DIVIDE", "Select object to divide: ")
      # scarto la selezione di punti
      self.entSelClass.checkPointLayer = False
      self.entSelClass.checkLineLayer = True
      self.entSelClass.checkPolygonLayer = True
      self.entSelClass.checkDimLayers = False
      self.entSelClass.onlyEditableLayers = False

      self.entSelClass.run(msgMapTool, msg)


   #============================================================================
   # waitForAlignmentObjs
   #============================================================================
   def waitForAlignmentObjs(self):
      self.step = QadDIVIDECommandClassStepEnum.ASK_FOR_ALIGNMENT

      keyWords = QadMsg.translate("QAD", "Yes") + "/" + QadMsg.translate("QAD", "No")
      self.defaultValue = QadMsg.translate("QAD", "Yes")
      prompt = QadMsg.translate("Command_DIVIDE", "Align with object ? [{0}] <{1}>: ").format(keyWords, self.defaultValue)
      
      englishKeyWords = "Yes" + "/" + "No"
      keyWords += "_" + englishKeyWords

      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.KEYWORDS, \
                   self.defaultValue, \
                   keyWords, QadInputModeEnum.NONE)

   
   #============================================================================
   # waitForSegmentNumber
   #============================================================================
   def waitForSegmentNumber(self):
      self.step = QadDIVIDECommandClassStepEnum.ASK_SEGMENT_NUMBER

      # si appresta ad attendere un numero intero
      msg = QadMsg.translate("Command_DIVIDE", "Enter the number of segments: ")
      # msg, inputType, default, keyWords, valori positivi
      self.waitFor(msg, \
                   QadInputTypeEnum.INT, \
                   None, \
                   "", \
                   QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)


   #============================================================================
   # addFeature
   #============================================================================
   def addFeature(self, layer, insPt, rot):
      transformedPoint = self.mapToLayerCoordinates(layer, insPt)
      g = QgsGeometry.fromPoint(transformedPoint)
      f = QgsFeature()
      f.setGeometry(g)
      # Add attribute fields to feature.
      fields = layer.pendingFields()
      f.setFields(fields)
      
      # assegno i valori di default
      provider = layer.dataProvider()
      for field in fields.toList():
         i = fields.indexFromName(field.name())
         f[field.name()] = provider.defaultValue(i)
      
      # se la scala dipende da un campo 
      scaleFldName = qad_layer.get_symbolScaleFieldName(layer)
      if len(scaleFldName) > 0:
         f.setAttribute(scaleFldName, 1.0)
      
      # se la rotazione dipende da un campo
      rotFldName = qad_layer.get_symbolRotationFieldName(layer)
      if len(rotFldName) > 0:
         f.setAttribute(rotFldName, qad_utils.toDegrees(rot))
      
      return qad_layer.addFeatureToLayer(self.plugIn, layer, f)               


   #============================================================================
   # doDivide
   #============================================================================
   def doDivide(self, dstLayer):
      f = self.entSelClass.entity.getFeature()
      if f is None:
         return
      
      layer = self.entSelClass.entity.layer
      
      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      geom = self.layerToMapCoordinates(layer, f.geometry())
      
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      dummy = qad_utils.closestSegmentWithContext(self.entSelClass.point, geom)
      if dummy[2] is None:
         return False
      
      # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
      subGeom, atSubGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])
      pathLinearObjectList = qad_utils.QadLinearObjectList()
      geomType = subGeom.type()
      pathLinearObjectList.fromPolyline(subGeom.asPolyline())
      distance = pathLinearObjectList.length() / self.nSegments
      
      self.plugIn.beginEditCommand("Feature divided", dstLayer)
      
      i = 1
      distanceFromStart = distance
      while i < self.nSegments:
         pt, rot = pathLinearObjectList.getPointFromStart(distanceFromStart)
         if self.addFeature(dstLayer, pt, rot if self.objectAlignment else 0) == False:
            self.plugIn.destroyEditCommand()
            return False
         i = i + 1
         distanceFromStart = distanceFromStart + distance 

      self.plugIn.endEditCommand()
      return True

   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapSettings().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
         return True # fine comando
      
      currLayer, errMsg = qad_layer.getCurrLayerEditable(self.plugIn.canvas, QGis.Point)
      if currLayer is None:
         self.showErr(errMsg)
         return True # fine comando

      if qad_layer.isSymbolLayer(currLayer) == False :
         errMsg = QadMsg.translate("QAD", "\nCurrent layer is not a symbol layer.")
         errMsg = errMsg + QadMsg.translate("QAD", "\nA symbol layer is a vector punctual layer without label.\n")
         self.showErr(errMsg)
         return True # fine comando
      
      if  len(QadDimStyles.getDimListByLayer(currLayer)) > 0:
         errMsg = QadMsg.translate("QAD", "\nThe current layer belongs to a dimension style.\n")
         self.showErr(errMsg)
         return True # fine comando

      if self.step == 0:     
         self.waitForEntsel(msgMapTool, msg)
         return False # continua


      #=========================================================================
      # RISPOSTA ALLA SELEZIONE DI UN'ENTITA' (da step = 0)
      elif self.step == QadDIVIDECommandClassStepEnum.ASK_FOR_ENT:
         if self.entSelClass.run(msgMapTool, msg) == True:
            if self.entSelClass.entity.isInitialized():
               # se il layer di destinazione è di tipo simbolo
               if qad_layer.isSymbolLayer(currLayer) == True:
                  # se il simbolo può essere ruotato
                  if len(qad_layer.get_symbolRotationFieldName(currLayer)) >0:
                     self.waitForAlignmentObjs()
                  else:
                     self.waitForSegmentNumber()
               return False
            else:
               if self.entSelClass.canceledByUsr == True: # fine comando
                  return True
               self.showMsg(QadMsg.translate("QAD", "No geometries in this position."))
               self.waitForEntsel(msgMapTool, msg)
         return False # continua
      

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI ALLINEARE GLI OGGETTI (da step = ASK_FOR_ENT)
      elif self.step == QadDIVIDECommandClassStepEnum.ASK_FOR_ALIGNMENT: # dopo aver atteso una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
               value = self.defaultValue 
            else:
               self.setMapTool(self.getPointMapTool()) # riattivo il maptool
               return False
         else:
            # la parola chiave arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("QAD", "Yes") or value == "Yes":
               self.objectAlignment = True
            else:
               self.objectAlignment = False

            self.waitForSegmentNumber()
         
         return False 


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL NUMERO DI SEGMENTI (da step = ASK_FOR_ALIGNMENT)
      #=========================================================================
      elif self.step == QadDIVIDECommandClassStepEnum.ASK_SEGMENT_NUMBER: # dopo aver atteso un numero intero si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
               return False
            else:
               self.setMapTool(self.getPointMapTool()) # riattivo il maptool
               return False
         else:
            # il numero di segmenti arriva come parametro della funzione
            self.nSegments = msg
            self.doDivide(currLayer)
            return True # fine comando
         return False
