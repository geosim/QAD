# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando ALLUNGA per allungare un oggetto 
 
                              -------------------
        begin                : 2015-10-05
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


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *


import qad_utils
from qad_generic_cmd import QadCommandClass
from qad_getdist_cmd import QadGetDistClass
from qad_getangle_cmd import QadGetAngleClass
from qad_snapper import *
from qad_getpoint import *
from qad_lengthen_maptool import *
from qad_textwindow import *
from qad_msg import QadMsg
import qad_layer
from qad_arc import *
from qad_circle import *
from qad_dim import QadDimStyles
import qad_grip


# Classe che gestisce il comando LENGTHEN
class QadLENGTHENCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadLENGTHENCommandClass(self.plugIn)

   def getName(self):
      return QadMsg.translate("Command_list", "LENGTHEN")

   def getEnglishName(self):
      return "LENGTHEN"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runLENGTHENCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/lengthen.png")
   
   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_LENGTHEN", "Lengthen an object.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.OpMode = plugIn.lastOpMode_lengthen # "DElta" o "Percent" o "Total" o "DYnamic"
      self.OpType = None # "length" o "Angle"
      self.value = None 

      self.startPt = None
      self.GetDistClass = None
      self.GetAngleClass = None
      self.entity = QadEntity()
      self.linearObjectList = None
      self.atSubGeom = None
      self.move_startPt = None
      
      self.nOperationsToUndo = 0


   def __del__(self):
      QadCommandClass.__del__(self)
      if self.GetDistClass is not None:
         del self.GetDistClass      
      if self.GetAngleClass is not None:
         del self.GetAngleClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):      
      if self.step == 3: # quando si é in fase di richiesta distanza
         return self.GetDistClass.getPointMapTool()
      if self.step == 4: # quando si é in fase di richiesta angolo
         return self.GetAngleClass.getPointMapTool()
      elif (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_lengthen_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None

   def setInfo(self, entity, point):
      # setta: self.entity, self.linearObjectList, self.atSubGeom e self.move_startPt
      if self.linearObjectList is not None:
         del self.linearObjectList
         self.linearObjectList = None
      
      self.entity.set(entity.layer, entity.featureId)
      transformedPt = self.mapToLayerCoordinates(self.entity.layer, point)
      f = self.entity.getFeature()
      geom = self.entity.getGeometry()
                  
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      res = False
      dummy = qad_utils.closestSegmentWithContext(transformedPt, geom)
      if dummy[2] is None:
         return False
      # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
      subGeom, self.atSubGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])               
      self.linearObjectList = qad_utils.QadLinearObjectList()               
      self.linearObjectList.fromPolyline(subGeom.asPolyline())
      
      if qad_utils.getDistance(self.linearObjectList.getStartPt(), transformedPt) <= \
         qad_utils.getDistance(self.linearObjectList.getEndPt(), transformedPt):
         # si allunga dal punto iniziale
         self.move_startPt = True
      else:
         # si allunga dal punto finale
         self.move_startPt = False
         
      return True
   

   #============================================================================
   # lengthen
   #============================================================================
   def lengthen(self, point):
      layer = self.entity.layer
      f = self.entity.getFeature()
      if f is None: # non c'è più la feature
         return False
      geom = self.entity.getGeometry()
                  
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      res = False
      if self.OpMode == "DElta":
         newLinearObjectList = qad_utils.QadLinearObjectList(self.linearObjectList)
         if self.OpType == "length":
            res = newLinearObjectList.lengthen_delta(self.move_startPt, self.value)
         elif self.OpType == "Angle":
            res = newLinearObjectList.lengthen_deltaAngle(self.move_startPt, self.value)
      elif self.OpMode == "Percent":
         newLinearObjectList = qad_utils.QadLinearObjectList(self.linearObjectList)
         value = newLinearObjectList.length() * self.value / 100
         value = value - newLinearObjectList.length()
         res = newLinearObjectList.lengthen_delta(self.move_startPt, value)
      elif self.OpMode == "Total":
         newLinearObjectList = qad_utils.QadLinearObjectList(self.linearObjectList)
         if self.OpType == "length":
            value = self.value - newLinearObjectList.length()
            res = newLinearObjectList.lengthen_delta(self.move_startPt, value)
         elif self.OpType == "Angle":                     
            if newLinearObjectList.qty() == 1:
               linearObject = newLinearObjectList.getLinearObjectAt(0)
               if linearObject.isArc() == True: # se è un arco
                  value = self.value - linearObject.getArc().totalAngle()
                  res = newLinearObjectList.lengthen_deltaAngle(self.move_startPt, value)
      elif self.OpMode == "DYnamic":
         newLinearObjectList = qad_utils.QadLinearObjectList(self.linearObjectList)
         transformedPt = self.mapToLayerCoordinates(layer, point)
            
         if self.move_startPt:
            linearObject = newLinearObjectList.getLinearObjectAt(0)
         else:
            linearObject = newLinearObjectList.getLinearObjectAt(-1)
            
         if linearObject.isSegment():
            newPt = qad_utils.getPerpendicularPointOnInfinityLine(linearObject.getStartPt(), linearObject.getEndPt(), transformedPt)
         else: # arco
            newPt = qad_utils.getPolarPointByPtAngle(linearObject.getArc().center, \
                                                     qad_utils.getAngleBy2Pts(linearObject.getArc().center, transformedPt), \
                                                     linearObject.getArc().radius)                  

         if newLinearObjectList.qty() > 1 and linearObject.isSegment():
            ang = linearObject.getTanDirectionOnStartPt()

         if self.move_startPt:
            linearObject.setStartPt(newPt)
         else:
            linearObject.setEndPt(newPt)
            
         if newLinearObjectList.qty() > 1 and linearObject.isSegment() and \
            qad_utils.TanDirectionNear(ang, linearObject.getTanDirectionOnStartPt()) == False:
            res = False
         else:
            res = True

      if res == False: # allungamento impossibile
         return False
               
      pts = newLinearObjectList.asPolyline() 
      updSubGeom = QgsGeometry.fromPolyline(pts)
               
      updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
      if updGeom is None:
         return False
      f.setGeometry(updGeom)
         
      self.plugIn.beginEditCommand("Feature edited", layer)
      
      # plugIn, layer, feature, refresh, check_validity
      if qad_layer.updateFeatureToLayer(self.plugIn, layer, f, False, False) == False:
         self.plugIn.destroyEditCommand()
         return False

      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1
      
      return True


   
   def showLength(self, entity, pt):
      # visualizza la lunghezza dell'entità in unità di mappa
      geom = entity.getGeometry()
      if geom is None:         
         errMsg = QadMsg.translate("QAD", "Invalid object.")
         self.showErr("\n" + errMsg)
         return None
   
      # Trasformo il punto nel sistema di coordinate del layer
      convPt = self.mapToLayerCoordinates(entity.layer, pt)

      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      dummy = qad_utils.closestSegmentWithContext(pt, geom)
      if dummy[2] is None:
         errMsg = QadMsg.translate("QAD", "Invalid object.")
         self.showErr("\n" + errMsg)
         return None
      # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
      subGeom, atSubGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])
      
      LinearObjectListToMisure = qad_utils.QadLinearObjectList()
      pointList = subGeom.asPolyline()
      LinearObjectListToMisure.fromPolyline(pointList)
      # la trasformo in unità di mappa
      LinearObjectListToMisure.transformFromCRSToCRS(entity.layer.crs(), self.plugIn.canvas.mapSettings().destinationCrs())      
      
      msg = QadMsg.translate("Command_LENGTHEN", "\nCurrent length: {0}")
      msg = msg.format(str(LinearObjectListToMisure.length()))

      arc = QadArc()
      startEndVertices = arc.fromPolyline(pointList, 0)
      # se la polilinea è composta solo da un arco
      if startEndVertices and startEndVertices[0] == 0 and startEndVertices[1] == len(pointList)-1:
         msg = msg + QadMsg.translate("Command_LENGTHEN", ", included angle: {0}")
         msg = msg.format(str(qad_utils.toDegrees(arc.totalAngle())))
         
      self.showMsg(msg)


   def waitForObjectSelToMisure(self):
      self.step = 1      
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_lengthen_maptool_ModeEnum.ASK_FOR_OBJ_TO_MISURE)

      if self.plugIn.lastOpMode_lengthen == "DElta":
         self.defaultValue = QadMsg.translate("Command_LENGTHEN", "DElta")
      elif self.plugIn.lastOpMode_lengthen == "Percent":
         self.defaultValue = QadMsg.translate("Command_LENGTHEN", "Percent")
      elif self.plugIn.lastOpMode_lengthen == "Total":
         self.defaultValue = QadMsg.translate("Command_LENGTHEN", "Total")
      elif self.plugIn.lastOpMode_lengthen == "DYnamic":
         self.defaultValue = QadMsg.translate("Command_LENGTHEN", "DYnamic")
      else:
         self.defaultValue = None
      
      keyWords = QadMsg.translate("Command_LENGTHEN", "DElta") + "/" + \
                 QadMsg.translate("Command_LENGTHEN", "Percent") + "/" + \
                 QadMsg.translate("Command_LENGTHEN", "Total") + "/" + \
                 QadMsg.translate("Command_LENGTHEN", "DYnamic")
      if self.defaultValue is None:
         prompt = QadMsg.translate("Command_LENGTHEN", "Select an object or [{0}] <{1}>:  ").format(keyWords, self.defaultValue)
      else:
         prompt = QadMsg.translate("Command_LENGTHEN", "Select an object or [{0}] <{1}>:  ").format(keyWords, self.defaultValue)

      englishKeyWords = "DElta" + "/" + "Percent" + "/" + "Total" + "/" + "DYnamic"
      keyWords += "_" + englishKeyWords
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   self.defaultValue, \
                   keyWords, QadInputModeEnum.NONE)


   def waitForDelta(self):
      self.step = 2
      self.OpMode = "DElta"
      self.plugIn.setLastOpMode_lengthen(self.OpMode)
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_lengthen_maptool_ModeEnum.ASK_FOR_DELTA)

      keyWords = QadMsg.translate("Command_LENGTHEN", "Angle")
      prompt = QadMsg.translate("Command_LENGTHEN", "Enter delta length or [{0}] <{1}>: ").format(keyWords, str(self.plugIn.lastDelta_lengthen))

      englishKeyWords = "Angle"
      keyWords += "_" + englishKeyWords
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS | QadInputTypeEnum.FLOAT, \
                   self.plugIn.lastDelta_lengthen, \
                   keyWords, QadInputModeEnum.NONE)
      

   def waitForDeltaLength(self, msgMapTool, msg):
      self.step = 3
      self.OpType = "length"

      # si appresta ad attendere una distanza                     
      if self.GetDistClass is not None:
         del self.GetDistClass
      self.GetDistClass = QadGetDistClass(self.plugIn)     
      prompt = QadMsg.translate("Command_LENGTHEN", "Enter delta length <{0}>: ")
      self.GetDistClass.msg = prompt.format(str(self.plugIn.lastDelta_lengthen))
      self.GetDistClass.startPt = self.startPt
      self.GetDistClass.dist = self.plugIn.lastDelta_lengthen
      self.GetDistClass.inputMode = QadInputModeEnum.NONE
      self.GetDistClass.run(msgMapTool, msg)


   def waitForDeltaAngle(self, msgMapTool, msg):
      self.step = 4
      self.OpType = "Angle"

      # si appresta ad attendere l'angolo di rotazione                      
      if self.GetAngleClass is not None:
         del self.GetAngleClass                  
      self.GetAngleClass = QadGetAngleClass(self.plugIn)
      prompt = QadMsg.translate("Command_LENGTHEN", "Enter delta angle <{0}>: ")
      self.GetAngleClass.msg = prompt.format(str(qad_utils.toDegrees(self.plugIn.lastDeltaAngle_lengthen)))
      self.GetAngleClass.angle = self.plugIn.lastDeltaAngle_lengthen
      self.GetAngleClass.run(msgMapTool, msg)         


   def waitForObjectSel(self):
      self.step = 5
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_lengthen_maptool_ModeEnum.ASK_FOR_OBJ_TO_LENGTHEN)
      self.getPointMapTool().refreshSnapType() # aggiorno lo snapType che può essere variato dal maptool di distanza o angolo
      self.getPointMapTool().OpType = self.OpType 
      self.getPointMapTool().value = self.value

      keyWords = QadMsg.translate("Command_LENGTHEN", "Undo")
      prompt = QadMsg.translate("Command_LENGTHEN", "Select an object to change or [{0}]: ").format(QadMsg.translate("Command_LENGTHEN", "Undo"))

      englishKeyWords = "Undo"
      keyWords += "_" + englishKeyWords
      # si appresta ad attendere un punto o enter o una parola chiave
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)


   def waitForPercent(self):
      self.step = 6
      self.OpMode = "Percent"
      self.plugIn.setLastOpMode_lengthen(self.OpMode)

      # imposto il map tool
      self.getPointMapTool().setMode(Qad_lengthen_maptool_ModeEnum.ASK_FOR_PERCENT)

      prompt = QadMsg.translate("Command_LENGTHEN", "Enter percentage length <{0}>: ")
      prompt = prompt.format(str(self.plugIn.lastPerc_lengthen))
      # si appresta ad attendere un numero reale         
      # msg, inputType, default, keyWords, valori positivi
      self.waitFor(prompt, QadInputTypeEnum.FLOAT, \
                   self.plugIn.lastPerc_lengthen, "", \
                   QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)

 
   def waitForTotal(self):
      self.step = 7
      self.OpMode = "Total"
      self.plugIn.setLastOpMode_lengthen(self.OpMode)
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_lengthen_maptool_ModeEnum.ASK_FOR_TOTAL)

      keyWords = QadMsg.translate("Command_LENGTHEN", "Angle")
      prompt = QadMsg.translate("Command_LENGTHEN", "Specify total length or [{0}] <{1}>: ").format(keyWords, str(self.plugIn.lastTotal_lengthen))

      englishKeyWords = "Angle"
      keyWords += "_" + englishKeyWords
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS | QadInputTypeEnum.FLOAT, \
                   self.plugIn.lastTotal_lengthen, \
                   keyWords, QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
      

   def waitForTotalLength(self, msgMapTool, msg):
      self.step = 8
      self.OpType = "length"

      # si appresta ad attendere una distanza                     
      if self.GetDistClass is not None:
         del self.GetDistClass
      self.GetDistClass = QadGetDistClass(self.plugIn)     
      prompt = QadMsg.translate("Command_LENGTHEN", "Enter total length <{0}>: ")
      self.GetDistClass.msg = prompt.format(str(self.plugIn.lastTotal_lengthen))
      self.GetDistClass.startPt = self.startPt
      self.GetDistClass.dist = self.plugIn.lastTotal_lengthen
      self.GetDistClass.inputMode = QadInputModeEnum.NONE
      self.GetDistClass.run(msgMapTool, msg)


   def waitForTotalAngle(self, msgMapTool, msg):
      self.step = 9
      self.OpType = "Angle"

      # si appresta ad attendere l'angolo di rotazione                      
      if self.GetAngleClass is not None:
         del self.GetAngleClass                  
      self.GetAngleClass = QadGetAngleClass(self.plugIn)
      prompt = QadMsg.translate("Command_LENGTHEN", "Enter total angle <{0}>: ")
      self.GetAngleClass.msg = prompt.format(str(qad_utils.toDegrees(self.plugIn.lastTotalAngle_lengthen)))
      self.GetAngleClass.angle = self.plugIn.lastTotalAngle_lengthen
      self.GetAngleClass.run(msgMapTool, msg)         


   def waitForDynamicPt(self):
      self.step = 10
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_lengthen_maptool_ModeEnum.ASK_FOR_DYNAMIC_POINT)

      prompt = QadMsg.translate("Command_LENGTHEN", "Specify new endpoint: ")

      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D, \
                   None, \
                   "", QadInputModeEnum.NONE)


   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapSettings().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
         return True # fine comando

      #=========================================================================
      # RICHIESTA SELEZIONE OGGETTO
      if self.step == 0: # inizio del comando
         # si appresta ad attendere la selezione degli oggetti da estendere/tagliare
         self.waitForObjectSelToMisure()
         return False

      #=========================================================================
      # RISPOSTA ALLA SELEZIONE OGGETTI DA MISURARE
      elif self.step == 1:
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = self.defaultValue
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_LENGTHEN", "DElta") or value == "DElta":
               self.waitForDelta()
               return False
            elif value == QadMsg.translate("Command_LENGTHEN", "Percent") or value == "Percent":
               self.waitForPercent()
               return False
            elif value == QadMsg.translate("Command_LENGTHEN", "Total") or value == "Total":
               self.waitForTotal()
               return False
            elif value == QadMsg.translate("Command_LENGTHEN", "DYnamic") or value == "DYnamic":
               self.OpMode = "DYnamic"
               self.plugIn.setLastOpMode_lengthen(self.OpMode)
               # si appresta ad attendere la selezione degli oggetti da allungare
               self.waitForObjectSel()
               return False

         elif type(value) == QgsPoint: # se é stato selezionato un punto
            if self.getPointMapTool().entity.isInitialized():
               self.showLength(self.getPointMapTool().entity, value)
            else:
               # cerco se ci sono entità nel punto indicato considerando
               # solo layer di tipo lineari che non appartengano a quote o di tipo poligono 
               layerList = []
               for layer in qad_utils.getVisibleVectorLayers(self.plugIn.canvas): # Tutti i layer vettoriali visibili
                  if layer.geometryType() == QGis.Line or layer.geometryType() == QGis.Polygon:
                     if len(QadDimStyles.getDimListByLayer(layer)) == 0:
                        layerList.append(layer)
                                     
               result = qad_utils.getEntSel(self.getPointMapTool().toCanvasCoordinates(value), \
                                            self.getPointMapTool(), \
                                            QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")), \
                                            layerList)
               if result is not None:
                  feature = result[0]
                  layer = result[1]
                  self.showLength(QadEntity().set(layer, feature.id()), value)
         else:
            return True # fine comando
         
         # si appresta ad attendere la selezione degli oggetti da misurare
         self.waitForObjectSelToMisure()
                                          
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL DELTA (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = self.plugIn.lastDelta_lengthen # opzione di default "spostamento"
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_LENGTHEN", "Angle") or value == "Angle":
               self.waitForDeltaAngle(msgMapTool, msg)
         elif type(value) == QgsPoint: # se é stato inserito un punto
            self.startPt = value
            self.waitForDeltaLength(msgMapTool, msg)
         elif type(value) == float: # se é stato inserito il delta
            self.plugIn.setLastDelta_lengthen(value)
            self.OpType = "length"
            self.value = value
            # si appresta ad attendere la selezione degli oggetti da allungare
            self.waitForObjectSel()

         return False 


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA LUNGHEZZA DEL DELTA (da step = 2)
      elif self.step == 3: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if self.GetDistClass.run(msgMapTool, msg) == True:
            if self.GetDistClass.dist is not None:
               self.plugIn.setLastDelta_lengthen(self.GetDistClass.dist)
               self.value = self.GetDistClass.dist
               # si appresta ad attendere la selezione degli oggetti da allungare
               self.waitForObjectSel()
               

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELL'ANGOLO DEL DELTA (da step = 2)
      elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if self.GetAngleClass.run(msgMapTool, msg) == True:
            if self.GetAngleClass.angle is not None:
               self.plugIn.setLastDeltaAngle_lengthen(self.GetAngleClass.angle)
               self.value = self.GetAngleClass.angle
               # si appresta ad attendere la selezione degli oggetti da allungare
               self.waitForObjectSel()


      #=========================================================================
      # RISPOSTA ALLA SELEZIONE OGGETTI DA ALLUNGARE
      elif self.step == 5:
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
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_LENGTHEN", "Undo") or value == "Undo":
               if self.nOperationsToUndo > 0: 
                  self.nOperationsToUndo = self.nOperationsToUndo - 1
                  self.plugIn.undoEditCommand()
               else:
                  self.showMsg(QadMsg.translate("QAD", "\nThe command has been canceled."))                  
         elif type(value) == QgsPoint: # se é stato selezionato un punto
            if self.getPointMapTool().entity.isInitialized():
               self.setInfo(self.getPointMapTool().entity, value)
               if self.OpMode != "DYnamic":
                  self.lengthen(value)
               else:
                  self.waitForDynamicPt()
                  return False
            else:
               # cerco se ci sono entità nel punto indicato considerando
               # solo layer lineari editabili che non appartengano a quote
               layerList = []
               for layer in qad_utils.getVisibleVectorLayers(self.plugIn.canvas): # Tutti i layer vettoriali visibili
                  if layer.geometryType() == QGis.Line and layer.isEditable():
                     if len(QadDimStyles.getDimListByLayer(layer)) == 0:
                        layerList.append(layer)
                                     
               result = qad_utils.getEntSel(self.getPointMapTool().toCanvasCoordinates(value), \
                                            self.getPointMapTool(), \
                                            QadVariables.get(QadMsg.translate("Environment variables", "PICKBOX")), \
                                            layerList)
               if result is not None:
                  feature = result[0]
                  layer = result[1]
                  self.setInfo(QadEntity().set(layer, feature.id()), value)

                  if self.OpMode != "DYnamic":
                     self.lengthen(value)
                  else:
                     self.waitForDynamicPt()
                     return False
         else:
            return True # fine comando

         # si appresta ad attendere la selezione degli oggetti da allungare
         self.waitForObjectSel()
                           
         return False 

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PERCENTUALE (da step = 1)
      elif self.step == 6: # dopo aver atteso un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = self.plugIn.lastPerc_lengthen
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               return False
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == float: # é stata inserita la percentuale
            self.plugIn.setLastPerc_lengthen(value)
            self.value = value
            # si appresta ad attendere la selezione degli oggetti da allungare
            self.waitForObjectSel()
            
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL TOTALE (da step = 1)
      elif self.step == 7: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = self.plugIn.lastTotal_lengthen
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_LENGTHEN", "Angle") or value == "Angle":
               self.waitForTotalAngle(msgMapTool, msg)
         elif type(value) == QgsPoint: # se é stato inserito un punto
            self.startPt = value
            self.waitForTotalLength(msgMapTool, msg)
         elif type(value) == float: # se é stato inserito il delta
            self.plugIn.setLastTotal_lengthen(value)
            self.OpType = "length"
            self.value = value
            # si appresta ad attendere la selezione degli oggetti da allungare
            self.waitForObjectSel()

         return False 


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA LUNGHEZZA DEL TOTALE (da step = 7)
      elif self.step == 8: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if self.GetDistClass.run(msgMapTool, msg) == True:
            if self.GetDistClass.dist is not None:
               self.plugIn.setLastTotal_lengthen(self.GetDistClass.dist)
               self.value = self.GetDistClass.dist
               # si appresta ad attendere la selezione degli oggetti da allungare
               self.waitForObjectSel()
               return False
            

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELL'ANGOLO DEL DELTA (da step = 7)
      elif self.step == 9: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if self.GetAngleClass.run(msgMapTool, msg) == True:
            if self.GetAngleClass.angle is not None:
               self.plugIn.setLastTotalAngle_lengthen(self.GetAngleClass.angle)
               self.value = self.GetAngleClass.angle
               # si appresta ad attendere la selezione degli oggetti da allungare
               self.waitForObjectSel()
               return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA NUOVA ESTREMITA' IN MODO DINAMICO (da step = 5)
      elif self.step == 10: # dopo aver atteso un punto
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               self.setMapTool(self.getPointMapTool()) # riattivo il maptool
               return False

            value = self.getPointMapTool().point            
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == QgsPoint: # se é stato inserito un punto
            self.lengthen(value)
            
         # si appresta ad attendere la selezione degli oggetti da allungare
         self.waitForObjectSel()
            
         return False




#============================================================================
# Classe che gestisce il comando LENGTHEN per i grip
#============================================================================
class QadGRIPLENGTHENCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadGRIPLENGTHENCommandClass(self.plugIn)
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.entity = None
      self.skipToNextGripCommand = False
      self.copyEntities = False
      self.basePt = QgsPoint()
      self.nOperationsToUndo = 0
      
      self.linearObjectList = None
      self.atSubGeom = None
      self.move_startPt = None


   def __del__(self):
      QadCommandClass.__del__(self)
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):      
      if (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_lengthen_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None


   #============================================================================
   # setSelectedEntityGripPoints
   #============================================================================
   def setSelectedEntityGripPoints(self, entitySetGripPoints):
      # lista delle entityGripPoint con dei grip point selezionati
      # setta la prima entità con un grip selezionato
      self.entity = None
      for entityGripPoints in entitySetGripPoints.entityGripPoints:
         for gripPoint in entityGripPoints.gripPoints:
            # grip point selezionato
            if gripPoint.getStatus() == qad_grip.QadGripStatusEnum.SELECTED:
               # verifico se l'entità appartiene ad uno stile di quotatura
               if entityGripPoints.entity.isDimensionComponent():
                  return False
               if entityGripPoints.entity.getEntityType() != QadEntityGeomTypeEnum.ARC and \
                  entityGripPoints.entity.getEntityType() != QadEntityGeomTypeEnum.LINESTRING:
                  return False
               
               # setta: self.entity, self.linearObjectList, self.atSubGeom e self.move_startPt
               self.entity = entityGripPoints.entity
               
               if self.linearObjectList is not None:
                  del self.linearObjectList
                  self.linearObjectList = None

               # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
               geom = self.layerToMapCoordinates(self.entity.layer, self.entity.getGeometry())
               
               # ritorna una tupla (<The squared cartesian distance>,
               #                    <minDistPoint>
               #                    <afterVertex>
               #                    <leftOf>)
               res = False
               dummy = qad_utils.closestSegmentWithContext(gripPoint.getPoint(), geom)
               if dummy[2] is None:
                  return False
               # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
               subGeom, self.atSubGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])               
               self.linearObjectList = qad_utils.QadLinearObjectList()

               self.linearObjectList.fromPolyline(subGeom.asPolyline())
               
               if qad_utils.getDistance(self.linearObjectList.getStartPt(), gripPoint.getPoint()) <= \
                  qad_utils.getDistance(self.linearObjectList.getEndPt(), gripPoint.getPoint()):
                  # si allunga dal punto iniziale
                  self.move_startPt = True
               else:
                  # si allunga dal punto finale
                  self.move_startPt = False

               # imposto il map tool
               if self.getPointMapTool().setInfo(self.entity, gripPoint.getPoint()) == False:
                  return False
               
               return True
      return False


   #============================================================================
   # lengthen
   #============================================================================
   def lengthen(self, point):
      layer = self.entity.layer
      f = self.entity.getFeature()
      if f is None: # non c'è più la feature
         return False
      # trasformo la geometria nel crs del canvas per lavorare con coordinate piane xy
      geom = self.layerToMapCoordinates(layer, self.entity.getGeometry())
                  
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      res = False
      newLinearObjectList = qad_utils.QadLinearObjectList(self.linearObjectList)
         
      if self.move_startPt:
         linearObject = newLinearObjectList.getLinearObjectAt(0)
      else:
         linearObject = newLinearObjectList.getLinearObjectAt(-1)
         
      if linearObject.isSegment():
         newPt = qad_utils.getPerpendicularPointOnInfinityLine(linearObject.getStartPt(), linearObject.getEndPt(), point)
      else: # arco
         newPt = qad_utils.getPolarPointByPtAngle(linearObject.getArc().center, \
                                                  qad_utils.getAngleBy2Pts(linearObject.getArc().center, point), \
                                                  linearObject.getArc().radius)                  

      if newLinearObjectList.qty() > 1 and linearObject.isSegment():
         ang = linearObject.getTanDirectionOnStartPt()

      if self.move_startPt:
         linearObject.setStartPt(newPt)
      else:
         linearObject.setEndPt(newPt)
         
      if newLinearObjectList.qty() > 1 and linearObject.isSegment() and \
         qad_utils.TanDirectionNear(ang, linearObject.getTanDirectionOnStartPt()) == False:
         res = False
      else:
         res = True

      if res == False: # allungamento impossibile
         return False
               
      pts = newLinearObjectList.asPolyline() 
      updSubGeom = QgsGeometry.fromPolyline(pts)
               
      updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom)
      if updGeom is None:
         return False
      # trasformo la geometria nel crs del layer
      f.setGeometry(self.mapToLayerCoordinates(layer, updGeom))
         
      self.plugIn.beginEditCommand("Feature edited", layer)
      
      if self.copyEntities == False:
         # plugIn, layer, feature, refresh, check_validity
         if qad_layer.updateFeatureToLayer(self.plugIn, layer, f, False, False) == False:
            self.plugIn.destroyEditCommand()
            return False
      else:
         # plugIn, layer, features, coordTransform, refresh, check_validity
         if qad_layer.addFeatureToLayer(self.plugIn, layer, f, None, False, False) == False:
            self.plugIn.destroyEditCommand()
            return False
      
      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1
      
      return True


   def waitForDynamicPt(self):
      keyWords = QadMsg.translate("Command_GRIP", "Copy") + "/" + \
                 QadMsg.translate("Command_GRIP", "Undo") + "/" + \
                 QadMsg.translate("Command_GRIP", "eXit")
      prompt = QadMsg.translate("Command_GRIPLENGTHEN", "Specify new endpoint or [{0}]: ").format(keyWords)

      englishKeyWords = "Copy" + "/" + "Undo" + "/" "eXit"
      keyWords += "_" + englishKeyWords

      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)
      self.step = 1
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_lengthen_maptool_ModeEnum.ASK_FOR_DYNAMIC_POINT)


   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapSettings().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
         return True # fine comando

      #=========================================================================
      # RICHIESTA SELEZIONE OGGETTO
      if self.step == 0: # inizio del comando
         self.waitForDynamicPt()
         return False

      #=========================================================================
      # RISPOSTA ALLA SELEZIONE OGGETTI DA MISURARE
      elif self.step == 1:
         ctrlKey = False
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.copyEntities == False:
                     self.skipToNextGripCommand = True
                  return True # fine comando
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
            ctrlKey = self.getPointMapTool().ctrlKey
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_GRIP", "Copy") or value == "Copy":
               # Copia entità lasciando inalterate le originali
               self.copyEntities = True                     

               self.waitForDynamicPt()
            elif value == QadMsg.translate("Command_GRIP", "Undo") or value == "Undo":
               if self.nOperationsToUndo > 0: 
                  self.nOperationsToUndo = self.nOperationsToUndo - 1
                  self.plugIn.undoEditCommand()
               else:
                  self.showMsg(QadMsg.translate("QAD", "\nThe command has been canceled."))                  

               self.waitForDynamicPt()
            elif value == QadMsg.translate("Command_GRIP", "eXit") or value == "eXit":
               return True # fine comando
         elif type(value) == QgsPoint: # se é stato selezionato un punto
            if ctrlKey:
               self.copyEntities = True
   
            self.lengthen(value)

            if self.copyEntities == False:
               return True

            self.waitForDynamicPt()
         else:
            if self.copyEntities == False:
               self.skipToNextGripCommand = True
            return True # fine comando
                                          
         return False