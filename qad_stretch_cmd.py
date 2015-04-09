# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando STRETCH per stirare oggetti grafici
 
                              -------------------
        begin                : 2013-07-15
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


from qad_stretch_maptool import *
from qad_getpoint import *
from qad_textwindow import *
from qad_mpolygon_cmd import QadMPOLYGONCommandClass
from qad_rectangle_cmd import QadRECTANGLECommandClass
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
import qad_utils
import qad_layer


# Classe che gestisce il comando STRETCH
class QadSTRETCHCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadSTRETCHCommandClass(self.plugIn)
   
   def getName(self):
      return QadMsg.translate("Command_list", "STIRA")

   def getEnglishName(self):
      return "STRETCH"

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runSTRETCHCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/stretch.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_STRETCH", "Stira gli oggetti.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.AddOnSelection = True # se = False significa remove
      self.points = []
      self.MPOLYGONCommand = None
      self.SSGeomList = [] # lista di entità da stirare con geom di selezione
      self.basePt = QgsPoint()
   
   def __del__(self):
      QadCommandClass.__del__(self)
      if self.MPOLYGONCommand is not None:
         del self.MPOLYGONCommand      
      for SSGeom in self.SSGeomList:
         SSGeom[0].deselectOnLayer()

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 2: # quando si é in fase di disegno linea
         return self.MPOLYGONCommand.getPointMapTool(drawMode)
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_stretch_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None




   #============================================================================
   # rotate
   #============================================================================
   def stretch(self, f, containerGeom, offSetX, offSetY, tolerance2ApproxCurve, layerEntitySet, entitySet, dimStyle):
      if dimStyle is not None:
         entity = QadEntity()
         entity.set(layerEntitySet.layer, f.id())
         dimEntity = QadDimEntity()
         if dimEntity.initByEntity(dimStyle, entity) == False:
            dimEntity = None
      else:
         dimEntity = None
      
      if dimEntity is None:
         # stiro la feature e la rimuovo da entitySet (é la prima)
         stretchedGeom = qad_utils.stretchQgsGeometry(f.geometry(), containerGeom, \
                                                      offSetX, offSetY, \
                                                      tolerance2ApproxCurve)
         
         if stretchedGeom is not None:
            f.setGeometry(stretchedGeom)
            # plugIn, layer, feature, refresh, check_validity
            if qad_layer.updateFeatureToLayer(self.plugIn, layerEntitySet.layer, f, False, False) == False:
               self.plugIn.destroyEditCommand()
               return False
         del layerEntitySet.featureIds[0]
      else:
         # ruoto la quota e la rimuovo da entitySet
         dimEntitySet = dimEntity.getEntitySet()
         if dimEntity.deleteToLayers(self.plugIn) == False:
            return False                      
         dimEntity.stretch(self.plugIn, containerGeom, offSetX, offSetY)
         if dimEntity.addToLayers(self.plugIn) == False:
            return False             
         entitySet.subtract(dimEntitySet)
            
      return True


   #============================================================================
   # stretchFeatures
   #============================================================================
   def stretchFeatures(self, newPt):
      # mi ricavo un unico QadEntitySet con le entità selezionate
      entitySet = QadEntitySet()
      for SSGeom in self.SSGeomList:
         entitySet.unite(SSGeom[0])
      self.plugIn.beginEditCommand("Feature stretched", entitySet.getLayerList())
      del entitySet
      
      for SSGeom in self.SSGeomList:
         # copio entitySet
         entitySet = QadEntitySet(SSGeom[0])
         geomSel = SSGeom[1]
         for layerEntitySet in entitySet.layerEntitySetList:
            layer = layerEntitySet.layer
         
            # verifico se il layer appartiene ad uno stile di quotatura
            dimStyle = self.plugIn.dimStyles.getDimByLayer(layer)
            
            tolerance2ApproxCurve = qad_utils.distMapToLayerCoordinates(QadVariables.get(QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")), \
                                                                        self.plugIn.canvas,\
                                                                        layer)                              
                  
            g = QgsGeometry(geomSel)
            if self.plugIn.canvas.mapRenderer().destinationCrs() != layer.crs():         
               # Trasformo la geometria nel sistema di coordinate del layer
               coordTransform = QgsCoordinateTransform(self.plugIn.canvas.mapRenderer().destinationCrs(), \
                                                       layer.crs())          
               g.transform(coordTransform)
               transformedBasePt = self.mapToLayerCoordinates(layer, self.basePt)
               transformedNewPt = self.mapToLayerCoordinates(layer, newPt)
               offSetX = transformedNewPt.x() - transformedBasePt.x()
               offSetY = transformedNewPt.y() - transformedBasePt.y()
            else:
               offSetX = newPt.x() - self.basePt.x()
               offSetY = newPt.y() - self.basePt.y()
                           
            while len(layerEntitySet.featureIds) > 0:
               featureId = layerEntitySet.featureIds[0]
               f = layerEntitySet.getFeature(featureId)        
               if self.stretch(f, g, offSetX, offSetY, tolerance2ApproxCurve, layerEntitySet, entitySet, dimStyle) == False:
                  self.plugIn.destroyEditCommand()
                  return

      self.plugIn.endEditCommand()
                           
                           
   #============================================================================
   # setEntitySetGeom
   #============================================================================
   def setEntitySetGeom(self, entitySet, selGeom):
      for SSGeom in self.SSGeomList:
         SSGeom[0].deselectOnLayer()
      del self.SSGeomList[:] # svuoto la lista  
      # aggiuge il gruppo di selezione con la geometria usata per la selezione
      self.SSGeomList.append([entitySet, selGeom])
      entitySet.selectOnLayer(False) # incremental = False

   #============================================================================
   # addEntitySetGeom
   #============================================================================
   def addEntitySetGeom(self, entitySet, selGeom):      
      # elimino dai gruppi precedenti gli oggetti presenti in entitySet
      self.removeEntitySet(entitySet)
      # aggiuge il gruppo di selezione con la geometria usata per la selezione
      self.SSGeomList.append([entitySet, selGeom])
      entitySet.selectOnLayer(True) # incremental = True
                                                      

   #============================================================================
   # removeEntitySet
   #============================================================================
   def removeEntitySet(self, entitySet):
      # elimino dai gruppi precedenti gli oggetti presenti in entitySet
      for SSGeom in self.SSGeomList:
         SSGeom[0].subtract(entitySet)
      for SSGeom in self.SSGeomList:
         SSGeom[0].selectOnLayer(False) # incremental = False


   #============================================================================
   # SSGeomListIsEmpty
   #============================================================================
   def SSGeomListIsEmpty(self):
      if len(self.SSGeomList) == 0:
         return True      
      for SSGeom in self.SSGeomList:
         if SSGeom[0].isEmpty() == False:
            return False
      return True

      
   #============================================================================
   # waitForObjectSel
   #============================================================================
   def waitForObjectSel(self):      
      self.step = 1     
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_stretch_maptool_ModeEnum.ASK_FOR_FIRST_PT_RECTANGLE)                                
      
      keyWords = QadMsg.translate("Command_STRETCH", "Poligono") + "/" + \
                 QadMsg.translate("Command_STRETCH", "AGgiungi") + "/" + \
                 QadMsg.translate("Command_STRETCH", "Elimina")

      if self.AddOnSelection == True:
         prompt = QadMsg.translate("Command_STRETCH", "Selezionare i vertici")
      else:
         prompt = QadMsg.translate("Command_STRETCH", "Rimuovere i vertici")
      prompt = prompt + QadMsg.translate("Command_STRETCH", " da stirare tramite una finestra o [{0}]: ").format(keyWords)                        

      englishKeyWords = "Polygon" + "/" + "Add" + "/" + "Remove"
      keyWords += "_" + englishKeyWords
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)      


   #============================================================================
   # waitForBasePt
   #============================================================================
   def waitForBasePt(self):      
      self.step = 4   
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_stretch_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_BASE_PT)                                
      
      keyWords = QadMsg.translate("Command_STRETCH", "Spostamento")
      prompt = QadMsg.translate("Command_STRETCH", "Specificare punto base o [{0}] <{0}>: ").format(keyWords)                        
         
      englishKeyWords = "Displacement"
      keyWords += "_" + englishKeyWords
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(prompt, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)      


   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando
     
      #=========================================================================
      # RICHIESTA SELEZIONE OGGETTI
      if self.step == 0: # inizio del comando
         # si appresta ad attendere la selezione degli oggetti da stirare
         self.waitForObjectSel()
         return False
      
      #=========================================================================
      # RISPOSTA ALLA SELEZIONE OGGETTI DA STIRARE
      elif self.step == 1:
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = None
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if type(value) == unicode:
            if value == QadMsg.translate("Command_STRETCH", "Poligono") or value == "Polygon":
               # Seleziona tutti gli oggetti che sono interni al poligono
               self.MPOLYGONCommand = QadMPOLYGONCommandClass(self.plugIn)
               # se questo flag = True il comando serve all'interno di un altro comando per disegnare una linea
               # che non verrà salvata su un layer
               self.MPOLYGONCommand.virtualCmd = True   
               self.MPOLYGONCommand.run(msgMapTool, msg)
               self.step = 2
               return False               
            elif value == QadMsg.translate("Command_SSGET", "AGgiungi") or value == "Add":
               # Passa al metodo Aggiungi: gli oggetti selezionati possono essere aggiunti al gruppo di selezione 
               self.AddOnSelection = True
            elif value == QadMsg.translate("Command_SSGET", "Elimina") or value == "Remove":
               # Passa al metodo Rimuovi: gli oggetti possono essere rimossi dal gruppo di selezione
               self.AddOnSelection = False                        
         elif type(value) == QgsPoint: # se é stato selezionato un punto
            del self.points[:] # svuoto la lista
            self.points.append(value)
            # imposto il map tool
            self.getPointMapTool().setMode(Qad_stretch_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT_RECTANGLE)                                            
            self.getPointMapTool().setStartPoint(value)
            
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.translate("Command_STRETCH", "Specificare angolo opposto: "))
            self.step = 3
            return False                  
         else:
            if self.SSGeomListIsEmpty():
               return True
            # si appresta ad attendere il punto base o lo spostamento
            self.waitForBasePt()
            return False                  
         
         # si appresta ad attendere la selezione degli oggetti da stirare
         self.waitForObjectSel()
                                          
         return False 

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO PER MODALITA' POLIGONO (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto si riavvia il comando
         if self.MPOLYGONCommand.run(msgMapTool, msg) == True:
            if len(self.MPOLYGONCommand.vertices) > 1:
               # cerco tutte le geometrie intersecanti il poligono
               # e considerando solo layer editabili       
               selSet = qad_utils.getSelSet("CP", self.getPointMapTool(), self.MPOLYGONCommand.vertices, \
                                                 None, True, True, True, \
                                                 True)
               # se la selezione é avvenuta con shift premuto o se si deve rimuovere il gruppo selSet dal gruppo
               if self.AddOnSelection == False:
                  self.removeEntitySet(selSet)
               else:
                  self.setEntitySetGeom(selSet, QgsGeometry.fromPolygon([self.MPOLYGONCommand.vertices]))
                              
            del self.MPOLYGONCommand
            self.MPOLYGONCommand = None

            # si appresta ad attendere la selezione degli oggetti da stirare
            self.waitForObjectSel()                                 
            self.getPointMapTool().refreshSnapType() # aggiorno lo snapType che può essere variato dal maptool di mpolygon                     
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO PER MODALITA' FINESTRA (da step = 1)
      elif self.step == 3: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  self.showMsg(QadMsg.translate("Command_STRETCH", "La finestra non é stata specificata correttamente."))
                  # si appresta ad attendere un punto
                  self.waitForPoint(QadMsg.translate("Command_STRETCH", "Specificare angolo opposto: "))
                  return False
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            shiftKey = self.getPointMapTool().shiftKey
            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            shiftKey = False
            value = msg


         if type(value) == QgsPoint:
            self.points.append(value)   
            # cerco tutte le geometrie intersecanti il rettangolo
            # e considerando solo layer editabili
            selSet = qad_utils.getSelSet("C", self.getPointMapTool(), self.points, \
                                         None, True, True, True, \
                                         True)            
            # se si deve rimuovere il gruppo entitySet dal gruppo
            if self.AddOnSelection == False:
               self.removeEntitySet(selSet)
            else:
               if shiftKey: # se la selezione é avvenuta con shift premuto
                  self.addEntitySetGeom(selSet, QgsGeometry.fromRect(QgsRectangle(self.points[0], self.points[1])))
               else:
                  self.setEntitySetGeom(selSet, QgsGeometry.fromRect(QgsRectangle(self.points[0], self.points[1])))
            # si appresta ad attendere la selezione degli oggetti da stirare
            self.waitForObjectSel()                                 
         return False
              
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO BASE (da step = 1)
      elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # é stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  pass # opzione di default "spostamento"
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         # imposto il map tool
         self.getPointMapTool().SSGeomList = self.SSGeomList                                

         if value is None or type(value) == unicode:
            self.basePt.set(0, 0)
            self.getPointMapTool().basePt = self.basePt
            self.getPointMapTool().setMode(Qad_stretch_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_MOVE_PT)                                
            # si appresta ad attendere un punto
            msg = QadMsg.translate("Command_STRETCH", "Specificare lo spostamento dal punto di origine 0,0 <{0}, {1}>: ")
            # msg, inputType, default, keyWords, nessun controllo
            self.waitFor(msg.format(str(self.plugIn.lastOffsetPt.x()), str(self.plugIn.lastOffsetPt.y())), \
                         QadInputTypeEnum.POINT2D, \
                         self.plugIn.lastOffsetPt, \
                         "", QadInputModeEnum.NONE)                                      
            self.step = 5      
         elif type(value) == QgsPoint: # se é stato inserito il punto base
            self.basePt.set(value.x(), value.y())

            # imposto il map tool
            self.getPointMapTool().basePt = self.basePt
            self.getPointMapTool().setMode(Qad_stretch_maptool_ModeEnum.BASE_PT_KNOWN_ASK_FOR_MOVE_PT)                                
            
            # si appresta ad attendere un punto o enter o una parola chiave         
            # msg, inputType, default, keyWords, nessun controllo
            self.waitFor(QadMsg.translate("Command_STRETCH", "Specificare secondo punto oppure <Utilizza primo punto come spostamento dal punto di origine 0,0>: "), \
                         QadInputTypeEnum.POINT2D, \
                         None, \
                         "", QadInputModeEnum.NONE)      
            self.step = 6      
         
         return False 

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL PUNTO DI SPOSTAMENTO (da step = 2)
      elif self.step == 5: # dopo aver atteso un punto o un numero reale si riavvia il comando
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

         self.plugIn.setLastOffsetPt(value)
         self.stretchFeatures(value)
         return True # fine comando     
         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER SPOSTAMENTO (da step = 2)
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

         if value is None:
            newPt = QgsPoint(self.basePt.x() * 2, self.basePt.y() * 2)
            self.stretchFeatures(newPt)
         elif type(value) == QgsPoint: # se é stato inserito lo spostamento con un punto
            self.stretchFeatures(value)
            
         return True # fine comando
