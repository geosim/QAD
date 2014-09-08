# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando FILLET per raccordare due oggetti grafici
 
                              -------------------
        begin                : 2014-01-30
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


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *


import qad_debug
from qad_generic_cmd import QadCommandClass
from qad_getdist_cmd import QadGetDistClass
from qad_snapper import *
from qad_fillet_maptool import *
from qad_msg import QadMsg
from qad_textwindow import *
import qad_utils
import qad_layer
from qad_variables import *


# Classe che gestisce il comando FILLET
class QadFILLETCommandClass(QadCommandClass):

   def getName(self):
      return QadMsg.translate("Command_list", "RACCORDO")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runFILLETCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/fillet.png")
   
   def getNote(self):
      # impostare le note esplicative del comando      
      return QadMsg.translate("Command_FILLET", "Arrotonda e raccorda gli spigoli.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)      
      self.GetDistClass = None

      self.entity1 = QadEntity()
      self.atSubGeom1 = None
      self.linearObjectList1 = qad_utils.QadLinearObjectList()
      self.partAt1 = 0
      self.pointAt1 = None
      
      self.entity2 = QadEntity()
      self.atSubGeom2 = None
      self.linearObjectList2 = qad_utils.QadLinearObjectList()
      self.partAt2 = 0
      self.pointAt2 = None

      self.filletMode = plugIn.filletMode # modalità di raccordo; 1=Taglia-estendi, 2=Non taglia-estendi
      self.radius = QadVariables.get(QadMsg.translate("Environment variables", "FILLETRAD"))
      self.multi = False
      self.nOperationsToUndo = 0
            
   
   def __del__(self):
      QadCommandClass.__del__(self)
      if self.GetDistClass is not None:
         del self.GetDistClass
      self.entity1.deselectOnLayer()
      self.entity2.deselectOnLayer()

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      # quando si è in fase di richiesta distanza
      if self.step == 3 or self.step == 5 or self.step == 7:
         return self.GetDistClass.getPointMapTool()
      elif (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_fillet_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None


   #============================================================================
   # setEntityInfo
   #============================================================================
   def setEntityInfo(self, firstObj, layer, featureId, point):
      """
      Setta self.entity, self.atSubGeom, self.linearObjectList, self.partAt, self.pointAt
      di primo o del secondo oggetto da raccordare (vedi <firstObj>)
      """
      transformedPt = self.mapToLayerCoordinates(layer, point)
      
      if firstObj:
         e = self.entity1
         l = self.linearObjectList1
      else:
         e = self.entity2
         l = self.linearObjectList2
         
      e.set(layer, featureId)
      geom = e.getGeometry()
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      dummy = qad_utils.closestSegmentWithContext(transformedPt, geom)
      if dummy[2] is not None:
         # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
         if firstObj:
            subGeom, self.atSubGeom1 = qad_utils.getSubGeomAtVertex(geom, dummy[2])
         else:
            subGeom, self.atSubGeom2 = qad_utils.getSubGeomAtVertex(geom, dummy[2])
             
         #qad_debug.breakPoint()               
         l.fromPolyline(subGeom.asPolyline())
         e.selectOnLayer(False) # non incrementale        
         
         # la funzione ritorna una lista con (<minima distanza al quadrato>,
         #                                    <punto più vicino>
         #                                    <indice della parte più vicina>       
         #                                    <"a sinistra di">)
         dummy = l.closestPartWithContext(transformedPt)
         
         if firstObj:           
            self.partAt1 = dummy[2]
            self.pointAt1 = dummy[1]
         else:
            self.partAt2 = dummy[2]
            self.pointAt2 = dummy[1]

         return True
      else:
         e.deselectOnLayer()
         return False


   #============================================================================
   # filletPolyline
   #============================================================================
   def filletPolyline(self):         
      layer = self.entity1.layer

      transformedRadius = qad_utils.distMapToLayerCoordinates(self.radius, self.plugIn.canvas, layer)
      tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                  self.plugIn.canvas,\
                                                                  layer)                              
      f = self.entity1.getFeature()
      geom = f.geometry() 

      #qad_debug.breakPoint()
      self.linearObjectList1.fillet(transformedRadius)
               
      updSubGeom = QgsGeometry.fromPolyline(self.linearObjectList1.asPolyline(tolerance2ApproxCurve))
      updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom1)
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
   

   #============================================================================
   # fillet
   #============================================================================
   def fillet(self):
      #qad_debug.breakPoint()     
      transformedRadius = qad_utils.distMapToLayerCoordinates(self.radius, self.plugIn.canvas, self.entity1.layer)
      tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                  self.plugIn.canvas,\
                                                                  self.entity1.layer)                              
      
      if self.entity1.layer.crs() != self.entity2.layer.crs():
         coordTransform = QgsCoordinateTransform(self.entity1.layer.crs(),\
                                                 self.entity2.layer.crs()) # trasformo la geometria
         transformedLinearObjectList2 = self.linearObjectList2.transform(coordTransform)
         transformedPointAt2 = coordTransform.transform(self.pointAt2)         
      else:
         # stessa entità e stessa parte
         if self.entity1.layer.id() == self.entity2.layer.id() and \
            self.entity1.featureId == self.entity2.featureId and \
            self.partAt1 == self.partAt2:
            return False
         
         transformedLinearObjectList2 = qad_utils.QadLinearObjectList(self.linearObjectList2)
         transformedPointAt2 = self.pointAt2
   
      epsg = self.entity1.layer.crs().authid()      
      res = qad_utils.getFilletLinearObjectList(self.linearObjectList1, self.partAt1, self.pointAt1, \
                                                transformedLinearObjectList2, self.partAt2, transformedPointAt2,\
                                                self.filletMode, transformedRadius, epsg)      
      if res is None: # raccordo non possibile
         msg = QadMsg.translate("Command_FILLET", "\nIl raccordo con raggio {0} non esiste.")
         #showMsg
         self.showMsg(msg.format(str(self.radius)))
         return False
      
      filletLinearObjectList = res[0]
      whatToDoPoly1 = res[1]
      whatToDoPoly2 = res[2]

      self.plugIn.beginEditCommand("Feature edited", [self.entity1.layer, self.entity2.layer])

      if whatToDoPoly1 == 1: # 1=modificare       
         f = self.entity1.getFeature()
         geom = f.geometry() 
         updSubGeom = QgsGeometry.fromPolyline(filletLinearObjectList.asPolyline(tolerance2ApproxCurve))
         updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom1)
         if updGeom is None:
            self.plugIn.destroyEditCommand()
            return False
         f.setGeometry(updGeom)
         
         # plugIn, layer, feature, refresh, check_validity
         if qad_layer.updateFeatureToLayer(self.plugIn, self.entity1.layer, f, False, False) == False:
            self.plugIn.destroyEditCommand()
            return False
      elif whatToDoPoly1 == 2: # 2=cancellare 
         # plugIn, layer, featureId, refresh
         if qad_layer.deleteFeatureToLayer(self.plugIn, self.entity1.layer, \
                                           self.entity1.featureId, False) == False:
            self.plugIn.destroyEditCommand()
            return False

      if whatToDoPoly2 == 1: # 1=modificare
         
         if self.entity1.layer.crs() != self.entity2.layer.crs():
            coordTransform = QgsCoordinateTransform(self.entity2.layer.crs(),\
                                                    self.entity1.layer.crs()) # trasformo la geometria
            transformedLinearObjectList2 = self.filletLinearObjectList.transform(coordTransform)
         else:
            transformedLinearObjectList2 = filletLinearObjectList
         
         tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                     self.plugIn.canvas,\
                                                                     self.entity2.layer)                              

         f = self.entity2.getFeature()
         geom = f.geometry() 
         updSubGeom = QgsGeometry.fromPolyline(transformedLinearObjectList2.asPolyline(tolerance2ApproxCurve))
         updGeom = qad_utils.setSubGeom(geom, updSubGeom, self.atSubGeom2)
         if updGeom is None:
            self.plugIn.destroyEditCommand()
            return False
         f.setGeometry(updGeom)
         
         # plugIn, layer, feature, refresh, check_validity
         if qad_layer.updateFeatureToLayer(self.plugIn, self.entity2.layer, f, False, False) == False:
            self.plugIn.destroyEditCommand()
            return False
      elif whatToDoPoly2 == 2: # 2=cancellare 
         # plugIn, layer, featureId, refresh
         if qad_layer.deleteFeatureToLayer(self.plugIn, self.entity2.layer, \
                                           self.entity2.featureId, False) == False:
            self.plugIn.destroyEditCommand()
            return False

      if whatToDoPoly1 == 0 and whatToDoPoly2 == 0: # 0=niente      
         geom = QgsGeometry.fromPolyline(filletLinearObjectList.asPolyline(tolerance2ApproxCurve))
         # plugIn, layer, geom, coordTransform, refresh, check_validity
         if qad_layer.addGeomToLayer(self.plugIn, self.entity1.layer, geom, None, False, False) == False:
            self.plugIn.destroyEditCommand()
            return False

      self.plugIn.endEditCommand()
      self.nOperationsToUndo = self.nOperationsToUndo + 1

      return True
      

   #============================================================================
   # waitForFirstEntSel
   #============================================================================
   def waitForFirstEntSel(self):      
      self.step = 1
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_fillet_maptool_ModeEnum.ASK_FOR_FIRST_LINESTRING)

      keyWords = QadMsg.translate("Command_FILLET", "aNnulla") + "/" + \
                 QadMsg.translate("Command_FILLET", "Polilinea") + "/" + \
                 QadMsg.translate("Command_FILLET", "RAggio") + "/" + \
                 QadMsg.translate("Command_FILLET", "Taglia") + "/" + \
                 QadMsg.translate("Command_FILLET", "Multiplo")
      prompt = QadMsg.translate("Command_FILLET", "Selezionare il primo oggetto o [{0}]: ").format(keyWords)
               
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valore nullo non permesso
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NOT_NULL)      
      

   #============================================================================
   # WaitForPolyline
   #============================================================================
   def WaitForPolyline(self):
      self.step = 2
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_fillet_maptool_ModeEnum.ASK_FOR_POLYLINE)
      self.getPointMapTool().radius = self.radius      

      msg = QadMsg.translate("Command_FILLET", "Selezionare la polilinea o [Raggio]: ")                        
               
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valore nullo non permesso
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   QadMsg.translate("Command_FILLET", "Raggio"), QadInputModeEnum.NOT_NULL)      
            
        
   #============================================================================
   # waitForFilletMode
   #============================================================================
   def waitForFilletMode(self):      
      self.step = 4
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_fillet_maptool_ModeEnum.NONE)

      keyWords = QadMsg.translate("Command_FILLET", "Taglia-estendi") + "/" + \
                 QadMsg.translate("Command_FILLET", "Non taglia-estendi")
      if self.filletMode == 1:
         default = QadMsg.translate("Command_FILLET", "Taglia-estendi")
      elif self.filletMode == 2:
         default = QadMsg.translate("Command_FILLET", "Non taglia-estendi")                 
      prompt = QadMsg.translate("Command_FILLET", "Specificare modalità di taglio [{0}] <{1}>: ").format(keyWords, default)

      # si appresta ad attendere un punto o enter o una parola chiave o un numero reale     
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, QadInputTypeEnum.KEYWORDS, default, \
                   keyWords, QadInputModeEnum.NOT_NULL)      


   #============================================================================
   # waitForSecondEntSel
   #============================================================================
   def waitForSecondEntSel(self):      
      self.step = 6      
      # imposto il map tool
      self.getPointMapTool().filletMode = self.filletMode
      self.getPointMapTool().radius = self.radius
      self.getPointMapTool().setEntityInfo(self.entity1.layer, self.entity1.featureId, self.linearObjectList1, \
                                           self.partAt1, self.pointAt1)      
      self.getPointMapTool().setMode(Qad_fillet_maptool_ModeEnum.ASK_FOR_SECOND_LINESTRING)

      msg = QadMsg.translate("Command_FILLET", "Selezionare il secondo oggetto o selezionare l'oggetto tenendo premuto il tasto Maiusc per applicare l'angolo o [RAggio]: ")                        
               
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, valore nullo non permesso
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   QadMsg.translate("Command_FILLET", "RAggio"), QadInputModeEnum.NOT_NULL)      

        
   def run(self, msgMapTool = False, msg = None):
      if self.step == 0:
         CurrSettingsMsg = QadMsg.translate("QAD", "\nImpostazioni correnti: ")
         if self.filletMode == 1:
            CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_FILLET", "Modalità = Taglia-estendi")
         else:
            CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_FILLET", "Modalità = Non taglia-estendi")
               
         CurrSettingsMsg = CurrSettingsMsg + QadMsg.translate("Command_FILLET", ", Raggio = ") + str(self.radius)   
         self.showMsg(CurrSettingsMsg)         
            
         self.waitForFirstEntSel()
         return False # continua
      
      #=========================================================================
      # RISPOSTA ALLA SELEZIONE PRIMO OGGETTO
      elif self.step == 1:
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
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_FILLET", "aNnulla"):
               if self.nOperationsToUndo > 0: 
                  self.nOperationsToUndo = self.nOperationsToUndo - 1
                  self.plugIn.undoEditCommand()
               else:
                  self.showMsg(QadMsg.translate("QAD", "\nIl comando è stato completamente annullato."))                  
                  
               self.waitForFirstEntSel() # si appresta ad attendere la selezione del primo oggetto
            elif value == QadMsg.translate("Command_FILLET", "Polilinea"):
               self.WaitForPolyline()
            elif value == QadMsg.translate("Command_FILLET", "RAggio"):
               if self.GetDistClass is not None:
                  del self.GetDistClass
               self.GetDistClass = QadGetDistClass(self.plugIn)
               prompt = QadMsg.translate("Command_FILLET", "Specificare raggio di raccordo <{0}>: ")
               self.GetDistClass.msg = prompt.format(str(self.radius))
               self.GetDistClass.dist = self.radius
               self.GetDistClass.inputMode = QadInputModeEnum.NOT_NEGATIVE
               self.step = 3
               self.GetDistClass.run(msgMapTool, msg)
            elif value == QadMsg.translate("Command_FILLET", "Taglia"):
               self.waitForFilletMode()
            elif value == QadMsg.translate("Command_FILLET", "Multiplo"):
               self.multi = True
               self.waitForFirstEntSel() # si appresta ad attendere la selezione del primo oggetto
                           
         elif type(value) == QgsPoint: # se è stato selezionato un punto
            self.entity1.clear()
            self.linearObjectList1.removeAll()            
            #qad_debug.breakPoint()
            if self.getPointMapTool().entity.isInitialized():
               if self.setEntityInfo(True, self.getPointMapTool().entity.layer, \
                                     self.getPointMapTool().entity.featureId, value) == True:
                  self.waitForSecondEntSel() # si appresta ad attendere la selezione del secondo oggetto
                  return False
            else:
               # cerco se ci sono entità nel punto indicato considerando
               # solo layer lineari o poligono editabili che non appartengano a quote
               layerList = []
               for layer in self.plugIn.canvas.layers():
                  if layer.type() == QgsMapLayer.VectorLayer and \
                     (layer.geometryType() == QGis.Line or layer.geometryType() == QGis.Polygon) and \
                     layer.isEditable():
                     if self.plugIn.dimStyles.getDimByLayer(layer) is None:
                        layerList.append(layer)
               
               result = qad_utils.getEntSel(self.getPointMapTool().toCanvasCoordinates(value),
                                            self.getPointMapTool(), \
                                            layerList)
               if result is not None:
                  # result[0] = feature, result[1] = layer, result[0] = point
                  if self.setEntityInfo(True, result[1], result[0].id(), result[2]) == True:
                     self.waitForSecondEntSel() # si appresta ad attendere la selezione del secondo oggetto
                     return False
            self.waitForFirstEntSel() # si appresta ad attendere la selezione del primo oggetto                                    
         else:
            return True # fine comando
         
         return False 

      #=========================================================================
      # RISPOSTA ALLA SELEZIONE DI UNA POLILINEA (da step = 1)
      elif self.step == 2:
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
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_FILLET", "Raggio"):
               if self.GetDistClass is not None:
                  del self.GetDistClass
               self.GetDistClass = QadGetDistClass(self.plugIn)
               prompt = QadMsg.translate("Command_FILLET", "Specificare raggio di raccordo <{0}>: ")
               self.GetDistClass.msg = prompt.format(str(self.radius))
               self.GetDistClass.dist = self.radius
               self.GetDistClass.inputMode = QadInputModeEnum.NOT_NEGATIVE
               self.step = 5
               self.GetDistClass.run(msgMapTool, msg)                           
               return False
         elif type(value) == QgsPoint: # se è stato selezionato un punto
            self.entity1.clear()
            self.linearObjectList1.removeAll()            
            #qad_debug.breakPoint()
            if self.getPointMapTool().entity.isInitialized():
               if self.setEntityInfo(True, self.getPointMapTool().entity.layer, \
                                     self.getPointMapTool().entity.featureId, value) == True:
                  if self.filletPolyline() == False or self.multi:
                     self.waitForFirstEntSel() # si appresta ad attendere la selezione del primo oggetto
                     return False
                  else:
                     return True
            else:
               # cerco se ci sono entità nel punto indicato considerando
               # solo layer lineari o poligono editabili che non appartengano a quote
               layerList = []
               for layer in self.plugIn.canvas.layers():
                  if layer.type() == QgsMapLayer.VectorLayer and \
                     (layer.geometryType() == QGis.Line or layer.geometryType() == QGis.Polygon) and \
                     layer.isEditable():
                     if self.plugIn.dimStyles.getDimByLayer(layer) is None:
                        layerList.append(layer)

               result = qad_utils.getEntSel(self.getPointMapTool().toCanvasCoordinates(value),
                                            self.getPointMapTool(), \
                                            layerList)
               if result is not None:
                  # result[0] = feature, result[1] = layer, result[0] = point
                  if self.setEntityInfo(True, result[1], result[0].id(), result[2]) == True:
                     if self.filletPolyline() == False or self.multi:
                        self.waitForFirstEntSel() # si appresta ad attendere la selezione del primo oggetto
                        return False
                     else:
                        return True
         else:
            return True # fine comando

         self.WaitForPolyline()
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL RAGGIO DI RACCORDO (da step = 1)
      elif self.step == 3:
         if self.GetDistClass.run(msgMapTool, msg) == True:
            if self.GetDistClass.dist is not None:
               self.radius = self.GetDistClass.dist
               QadVariables.set(QadMsg.translate("Environment variables", "FILLETRAD"), self.radius)
               QadVariables.save()
            self.waitForFirstEntSel() # si appresta ad attendere la selezione del primo oggetto
            self.getPointMapTool().refreshSnapType() # aggiorno lo snapType che può essere variato dal maptool di distanza                     
         return False # fine comando
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA MODALITA' DI TAGLIO (da step = 1)
      elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = self.filletMode
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_FILLET", "Taglia"):
               self.filletMode = 1
            elif value == QadMsg.translate("Command_FILLET", "NonTaglia"):
               self.filletMode = 2
            self.plugIn.setFilletMode(self.filletMode)
            
         self.waitForFirstEntSel() # si appresta ad attendere la selezione del primo oggetto
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL RAGGIO DI RACCORDO (da step = 3)
      elif self.step == 5:
         if self.GetDistClass.run(msgMapTool, msg) == True:
            if self.GetDistClass.dist is not None:
               self.radius = self.GetDistClass.dist
               QadVariables.set(QadMsg.translate("Environment variables", "FILLETRAD"), self.radius)
               QadVariables.save()
            self.WaitForPolyline()
            self.getPointMapTool().refreshSnapType() # aggiorno lo snapType che può essere variato dal maptool di distanza                     
         return False # fine comando
      
      #=========================================================================
      # RISPOSTA ALLA SELEZIONE SECONDO OGGETTO
      elif self.step == 6:
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
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         #qad_debug.breakPoint()

         if type(value) == unicode:
            if value == QadMsg.translate("Command_FILLET", "RAggio"):
               if self.GetDistClass is not None:
                  del self.GetDistClass
               self.GetDistClass = QadGetDistClass(self.plugIn)
               prompt = QadMsg.translate("Command_FILLET", "Specificare raggio di raccordo <{0}>: ")
               self.GetDistClass.msg = prompt.format(str(self.radius))
               self.GetDistClass.dist = self.radius
               self.GetDistClass.inputMode = QadInputModeEnum.NOT_NEGATIVE
               self.step = 7
               self.GetDistClass.run(msgMapTool, msg)
               return False
                           
         elif type(value) == QgsPoint: # se è stato selezionato un punto
            self.entity2.clear()
            self.linearObjectList2.removeAll()            
            #qad_debug.breakPoint()
            if self.getPointMapTool().entity.isInitialized():
               if self.setEntityInfo(False, self.getPointMapTool().entity.layer, \
                                     self.getPointMapTool().entity.featureId, value) == True:
                  if self.getPointMapTool().shiftKey == True:
                     dummyRadius = self.radius
                     self.radius = 0
                     dummyFilletMode = self.filletMode
                     self.filletMode = 1 # modalità di raccordo; 1=Taglia-estendi
                     result = self.fillet()
                     self.radius = dummyRadius
                     self.filletMode = dummyFilletMode
                  else:
                     result = self.fillet()
                  
                  if result == False:
                     self.waitForSecondEntSel() # si appresta ad attendere la selezione del secondo oggetto         
                     return False 
                     
                  if self.multi:
                     self.waitForFirstEntSel() # si appresta ad attendere la selezione del primo oggetto
                     return False
                  else:
                     return True
            else:
               # cerco se ci sono entità nel punto indicato considerando
               # solo layer lineari o poligono editabili che non appartengano a quote
               layerList = []
               for layer in self.plugIn.canvas.layers():
                  if layer.type() == QgsMapLayer.VectorLayer and \
                     (layer.geometryType() == QGis.Line or layer.geometryType() == QGis.Polygon) and \
                     layer.isEditable():
                     if self.plugIn.dimStyles.getDimByLayer(layer) is None:
                        layerList.append(layer)

               result = qad_utils.getEntSel(self.getPointMapTool().toCanvasCoordinates(value),
                                            self.getPointMapTool(), \
                                            layerList)
               if result is not None:
                  # result[0] = feature, result[1] = layer, result[0] = point
                  if self.setEntityInfo(False, result[1], result[0].id(), result[2]) == True:
                     if self.fillet() == False:
                        self.waitForSecondEntSel() # si appresta ad attendere la selezione del secondo oggetto         
                        return False 
               
                     if self.multi:
                        self.waitForFirstEntSel() # si appresta ad attendere la selezione del primo oggetto
                        return False
                     else:
                        return True
         else:
            return True # fine comando
         
         self.waitForSecondEntSel() # si appresta ad attendere la selezione del secondo oggetto         
         return False 

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL RAGGIO DI RACCORDO (da step = 6)
      elif self.step == 7:
         if self.GetDistClass.run(msgMapTool, msg) == True:
            if self.GetDistClass.dist is not None:
               self.radius = self.GetDistClass.dist
               QadVariables.set(QadMsg.translate("Environment variables", "FILLETRAD"), self.radius)
               QadVariables.save()      
            self.waitForSecondEntSel() # si appresta ad attendere la selezione del secondo oggetto
            self.getPointMapTool().refreshSnapType() # aggiorno lo snapType che può essere variato dal maptool di distanza                     
         return False # fine comando