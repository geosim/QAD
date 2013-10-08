# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando da inserire in altri comandi per la selezione di un gruppo di feature
 
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
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_textwindow import *
from qad_entity import *
from qad_getpoint import *
from qad_pline_cmd import QadPLINECommandClass
from qad_circle_cmd import QadCIRCLECommandClass
from qad_mpolygon_cmd import QadMPOLYGONCommandClass
# ho dovuto spostare in fondo questo import perchè qad_mbuffer_cmd fa l'import di qad_ssget_cmd
#from qad_mbuffer_cmd import QadMBUFFERCommandClass
import qad_utils


#===============================================================================
# QadSSGetClass
#===============================================================================
class QadSSGetClass(QadCommandClass):
# Classe che gestisce la selezione di oggetti geometrici
      
   def __init__(self, plugIn):
      self.init(plugIn)

   def __del__(self):
      QadCommandClass.__del__(self)
      self.entitySet.deselectOnLayer(True) # emit signal = True

   def init(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.AddOnSelection = True # se = False significa remove
      self.entitySet = QadEntitySet()
      self.points = []
      self.currSelectionMode = ""
      self.onlyEditableLayers = False
      self.help = False
      # se SingleSelection = True viene selezionato il primo oggetto o gruppo di oggetti indicato,
      # senza che vengano richieste altre selezioni.      
      self.SingleSelection = False
      #  selezione degli oggetti aggiunti più recentemente al gruppo di selezione (x opzione annulla)
      self.lastEntitySet = QadEntitySet()
      self.PLINECommand = None
      self.CIRCLECommand = None
      self.MPOLYGONCommand = None
      self.MBUFFERCommand = None
      self.SSGetClass = None

   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 4: # quando si è in fase di disegno linea
         return self.PLINECommand.getPointMapTool(drawMode)
      elif self.step == 5: # quando si è in fase di disegno cerchio
         return self.CIRCLECommand.getPointMapTool(drawMode)
      elif self.step == 6: # quando si è in fase di selezione entità
         return self.SSGetClass.getPointMapTool(drawMode)
      elif self.step == 7: # quando si è in fase di disegno polygono
         return self.MPOLYGONCommand.getPointMapTool(drawMode)
      elif self.step == 8: # quando si è in fase di disegno buffer 
         return self.MBUFFERCommand.getPointMapTool(drawMode)      
      else:
         ptMapTool = QadCommandClass.getPointMapTool(self, drawMode)
         ptMapTool.setOrthoMode(0)
         return ptMapTool

   #============================================================================
   # showMsgOnAddRemove
   #============================================================================
   def showMsgOnAddRemove(self, found):
      msg = QadMsg.get(156) # " trovato(i) {0}, totale {1}"
      self.showMsg(msg.format(found, self.entitySet.count()))         

   #============================================================================
   # SetEntity
   #============================================================================
   def SetEntity(self, entity):
      if self.onlyEditableLayers == True and entity.layer.isEditable() == False:
         self.showMsgOnAddRemove(0)
         return
      
      for layerEntitySet in self.entitySet.layerEntitySetList:
         # se il layer non è quello di entity
         if entity.layerId() != layerEntitySet.layerId():            
            layerEntitySet.deselectOnLayer(True) # emit signal = True
         else:
            layerEntitySet.deselectOnLayer(False) # emit signal = False
      
      self.entitySet.deselectOnLayer(False) # emit signal = False
      self.entitySet.clear()
      self.entitySet.addEntity(entity)
      self.showMsgOnAddRemove(1)
      self.entitySet.selectOnLayer(True, False) # emit signal = True, incremental = False
      self.lastEntitySet.clear()
      self.lastEntitySet.addEntity(entity)
    
   #============================================================================
   # SetSelSet
   #============================================================================
   def SetSelSet(self, selSet):
      for layerEntitySet in self.entitySet.layerEntitySetList:
         # se il layer non è presente in selSet
         if selSet.findLayerEntitySet(layerEntitySet) is None:            
            layerEntitySet.deselectOnLayer(True) # emit signal = True
         else:
            layerEntitySet.deselectOnLayer(False) # emit signal = False
            
      self.entitySet.set(selSet)
      self.showMsgOnAddRemove(selSet.count())
      self.entitySet.selectOnLayer(True, False) # emit signal = True, incremental = False
      self.lastEntitySet.set(selSet)

   #============================================================================
   # AddRemoveEntity
   #============================================================================
   def AddRemoveEntity(self, entity):
      if self.onlyEditableLayers == True and entity.layer.isEditable() == False:
         self.showMsgOnAddRemove(0)
         return
      
      self.entitySet.deselectOnLayer(False) # emit signal = False
      if self.AddOnSelection == True: # aggiungi al gruppo di selezione
         self.entitySet.addEntity(entity)
      else: # rimuovi dal gruppo di selezione
         self.entitySet.removeEntity(entity)
         
      self.showMsgOnAddRemove(1)
      self.entitySet.selectOnLayer(True, False) # emit signal = True, incremental = False
      self.lastEntitySet.clear()
      self.lastEntitySet.addEntity(entity)

   #============================================================================
   # AddRemoveSelSet
   #============================================================================
   def AddRemoveSelSet(self, selSet):
      self.entitySet.deselectOnLayer(False) # emit signal = False
      if self.AddOnSelection == True: # aggiungi al gruppo di selezione
         self.entitySet.unite(selSet)
      else: # rimuovi dal gruppo di selezione
         self.entitySet.subtract(selSet)

      self.showMsgOnAddRemove(selSet.count())
      self.entitySet.selectOnLayer(True, False) # emit signal = True, incremental = False
      self.lastEntitySet.set(selSet)

   #============================================================================
   # AddRemoveSelSetByFence
   #============================================================================
   def AddRemoveSelSetByFence(self, points):
      if len(points) > 1:
         selSet = qad_utils.getSelSet("F", self.getPointMapTool(), points, \
                                      None, True, True, True, \
                                      self.onlyEditableLayers)
         self.AddRemoveSelSet(selSet)

   #============================================================================
   # AddRemoveSelSetByPolygon
   #============================================================================
   def AddRemoveSelSetByPolygon(self, mode, points):
      if len(points) > 2:
         selSet = qad_utils.getSelSet(mode, self.getPointMapTool(), points, \
                                      None, True, True, True, \
                                      self.onlyEditableLayers)
         self.AddRemoveSelSet(selSet)

   #============================================================================
   # AddRemoveSelSetByGeometry
   #============================================================================
   def AddRemoveSelSetByGeometry(self, mode, geom):
      if type(geom) == QgsGeometry: # singola geometria
         selSet = qad_utils.getSelSet(mode, self.getPointMapTool(), geom, \
                                      None, True, True, True, \
                                      self.onlyEditableLayers)
         self.AddRemoveSelSet(selSet)
      else: # lista di geometrie
         selSet = QadEntitySet()
         for g in geom:
            #qad_debug.breakPoint()
            partial = qad_utils.getSelSet(mode, self.getPointMapTool(), g, \
                                         None, True, True, True, \
                                         self.onlyEditableLayers)
            selSet.unite(partial)
         self.AddRemoveSelSet(selSet)

      
   #============================================================================
   # WaitForFirstPoint
   #============================================================================
   def WaitForFirstPoint(self):
      self.step = 1

      # "Finestra" "Ultimo" "Interseca"
      # "Riquadro" "Tutto" "iNTercetta"
      # "FPoligono" "IPoligono"
      # "FCerchio" "ICerchio"
      # "FOggetti" "IOggetti"
      # "FBuffer" "IBuffer"
      # "AGgiungi" "Elimina"
      # "Precedente" "Annulla"
      # "AUto" "SIngolo" "Help"
      keyWords = QadMsg.get(134) + " " + QadMsg.get(135) + " " + QadMsg.get(136) + " " + \
                 QadMsg.get(137) + " " + QadMsg.get(138) + " " + QadMsg.get(139) + " " + \
                 QadMsg.get(140) + " " + QadMsg.get(141) + " " + \
                 QadMsg.get(133) + " " + QadMsg.get(148) + " " + \
                 QadMsg.get(160) + " " + QadMsg.get(161) + " " + \
                 QadMsg.get(172) + " " + QadMsg.get(173) + " " + \
                 QadMsg.get(142) + " " + QadMsg.get(143) + " " + \
                 QadMsg.get(144) + " " + QadMsg.get(145) + " " + \
                 QadMsg.get(146) + " " + QadMsg.get(147) + " " + QadMsg.get(165)
                 
      if self.AddOnSelection == True:        
         # "Selezionare oggetti"
         msg = QadMsg.get(131)
      else:
         # "Rimuovere oggetti"
         msg = QadMsg.get(155)
                           
      if self.help == True:
         # " o [Finestra/Ultimo/Interseca/Riquadro/Tutto/iNTercetta/FPoligono/IPoligono/FCerchio/ICerchio/FOggetti/IOggetti/AGgiungi/Elimina/Precedente/ANnulla/AUto/SIngolo/Help]"
         msg = msg + QadMsg.get(163)
         
      msg = msg + QadMsg.get(164) # ": "
            
      # imposto il map tool
      self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION)
      self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.NONE)
      self.getPointMapTool().onlyEditableLayers = self.onlyEditableLayers
      self.points = []
           
      # si appresta ad attendere un punto o enter o una parola chiave         
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   keyWords, QadInputModeEnum.NONE)
      return

   def run(self, msgMapTool = False, msg = None):
      # ritorna:
      # True per selezione non terminata
      # False per selezione terminata
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.get(128)) # "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate\n"
         return True # errore
            
      #=========================================================================
      # RICHIESTA PRIMO PUNTO PER SELEZIONE OGGETTI
      if self.step == 0:
         self.WaitForFirstPoint()
         return False # continua
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PRIMO PUNTO PER SELEZIONE OGGETTI
      elif self.step == 1: # dopo aver atteso un punto o enter o una parola chiave si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  if self.entitySet.count() > 0:
                     self.plugIn.setLastEntitySet(self.entitySet)
                  return True # fine
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False # continua
            
            shiftKey = self.getPointMapTool().shiftKey

            # se è stata selezionata un'entità
            if self.getPointMapTool().entity.isInitialized():
               value = self.getPointMapTool().entity
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            shiftKey = False
            value = msg

         #qad_debug.breakPoint()

         if value is None:
            if self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
            return True # fine

         if type(value) == unicode:
            self.currSelectionMode = value
            if value == QadMsg.get(134) or value == QadMsg.get(136): # "Finestra" "Interseca"
               # "Finestra" = Seleziona tutti gli oggetti che si trovano completamente all'interno di un rettangolo definito da due punti
               # "Interseca" = Seleziona gli oggetti che intersecano o si trovano all'interno di un'area definita da due punti
               # imposto il map tool
               self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
               self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.NONE)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.get(149)) # "Specificare primo angolo: "
               self.step = 2
            if value == QadMsg.get(135): # "Ultimo" 
               # Seleziona l'ultima entità inserita
               if self.plugIn.getLastEntity() is None:
                  self.showMsgOnAddRemove(0)
               else:
                  self.AddRemoveEntity(self.plugIn.getLastEntity())              
                  if self.SingleSelection == True and self.entitySet.count() > 0:
                     self.plugIn.setLastEntitySet(self.entitySet)
                     return True # fine               
               self.WaitForFirstPoint()                          
            elif value == QadMsg.get(137): # "Riquadro"
               # Seleziona tutti gli oggetti che intersecano o si trovano all'interno di un rettangolo specificato da due punti.
               # Se i punti del rettangolo sono specificati da destra a sinistra, Riquadro equivale ad Interseca,
               # altrimenti è equivalente a Finestra
               # imposto il map tool
               self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
               self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.NONE)
               # si appresta ad attendere un punto
               self.waitForPoint(QadMsg.get(149)) # "Specificare primo angolo: "
               self.step = 2           
            elif value == QadMsg.get(138): # "Tutto"
               # Seleziona tutti gli oggetti 
               selSet = qad_utils.getSelSet("X", self.getPointMapTool(), None, \
                                            None, True, True, True, \
                                            self.onlyEditableLayers)
               self.SetSelSet(selSet)
               if self.SingleSelection == True and self.entitySet.count() > 0:
                  self.plugIn.setLastEntitySet(self.entitySet)
                  return True # fine         
               self.WaitForFirstPoint()
            elif value == QadMsg.get(139): # "iNTercetta"
               # Seleziona tutti gli oggetti che intersecano una polilinea
               self.PLINECommand = QadPLINECommandClass(self.plugIn)
               # se questo flag = True il comando serve all'interno di un altro comando per disegnare una linea
               # che non verrà salvata su un layer
               self.PLINECommand.virtualCmd = True   
               self.PLINECommand.run(msgMapTool, msg)
               self.step = 4
            elif value == QadMsg.get(140) or value == QadMsg.get(141): # "FPoligono" "IPoligono"
               # "FPoligono" = Seleziona oggetti che si trovano completamente all'interno di un poligono definito da punti
               # "IPoligono" = Seleziona gli oggetti che intersecano o si trovano all'interno di un poligono definito specificando dei punti
               self.MPOLYGONCommand = QadMPOLYGONCommandClass(self.plugIn)
               # se questo flag = True il comando serve all'interno di un altro comando per disegnare una linea
               # che non verrà salvata su un layer
               self.MPOLYGONCommand.virtualCmd = True   
               self.MPOLYGONCommand.run(msgMapTool, msg)
               self.step = 7
            elif value == QadMsg.get(133) or value == QadMsg.get(148): # "FCerchio" "ICerchio"
               # "FCerchio" = Seleziona oggetti che si trovano completamente all'interno di un cerchio
               # "ICerchio" = Seleziona oggetti che intersecano o si trovano all'interno di un cerchio
               self.CIRCLECommand = QadCIRCLECommandClass(self.plugIn)
               # se questo flag = True il comando serve all'interno di un altro comando per disegnare un cerchio
               # che non verrà salvata su un layer
               self.CIRCLECommand.virtualCmd = True   
               self.CIRCLECommand.run(msgMapTool, msg)
               self.step = 5
            elif value == QadMsg.get(160) or value == QadMsg.get(161): # "FOggetti" "IOggetti"
               # "FOggetti" = Seleziona oggetti che si trovano completamente all'interno di oggetti da selezionare
               # "IOggetti" = Seleziona oggetti che intersecano o si trovano all'interno di oggetti da selezionare
               #qad_debug.breakPoint()
               self.SSGetClass = QadSSGetClass(self.plugIn)
               self.SSGetClass.run(msgMapTool, msg)
               self.step = 6
            elif value == QadMsg.get(172) or value == QadMsg.get(173): # "FBuffer" "IBuffer"
               # "FBuffer" = Seleziona oggetti che si trovano completamente all'interno di buffer intorno ad oggetti da selezionare
               # "IBuffer" = Seleziona oggetti che intersecano o si trovano all'interno di buffer intorno ad oggetti da selezionare
               self.MBUFFERCommand = QadMBUFFERCommandClass(self.plugIn)
               # se questo flag = True il comando serve all'interno di un altro comando per disegnare un cerchio
               # che non verrà salvata su un layer
               self.MBUFFERCommand.virtualCmd = True   
               self.MBUFFERCommand.run(msgMapTool, msg)
               self.step = 8
            elif value == QadMsg.get(142): # "AGgiungi"
               # Passa al metodo Aggiungi: gli oggetti selezionati possono essere aggiunti al gruppo di selezione 
               self.AddOnSelection = True
               self.WaitForFirstPoint()
            elif value == QadMsg.get(143): # "Elimina"
               # Passa al metodo Rimuovi: gli oggetti possono essere rimossi dal gruppo di selezione
               self.AddOnSelection = False
               self.WaitForFirstPoint()
            elif value == QadMsg.get(144): # "Precedente"
               # Seleziona il gruppo di selezione più recente
               if self.plugIn.lastEntitySet is None:
                  self.showMsgOnAddRemove(0)
               else:
                  entitySet = QadEntitySet()
                  entitySet.set(self.plugIn.lastEntitySet)
                  if self.onlyEditableLayers == True:
                     entitySet.removeNotEditable()
                  entitySet.removeNotExisting()
                  self.AddRemoveSelSet(entitySet)            
                  if self.SingleSelection == True and self.entitySet.count() > 0:
                     self.plugIn.setLastEntitySet(self.entitySet)
                     return True # fine                                   
               self.WaitForFirstPoint()
            elif value == QadMsg.get(145): # "Annulla"
               # Annulla la selezione dell'oggetto aggiunto più recentemente al gruppo di selezione.
               # Inverto il tipo di selezione
               prevAddOnSelection = self.AddOnSelection
               self.AddOnSelection = not self.AddOnSelection
               self.AddRemoveSelSet(self.lastEntitySet)               
               # Ripristino il tipo di selezione
               self.AddOnSelection = prevAddOnSelection
               if self.SingleSelection == True and self.entitySet.count() > 0:
                  self.plugIn.setLastEntitySet(self.entitySet)
                  return True # fine               
               self.WaitForFirstPoint()
            elif value == QadMsg.get(146): # "AUto"
               # Passa alla selezione automatica: vengono selezionati gli oggetti sui quali si posiziona il puntatore.
               # Facendo clic su un'area vuota all'interno o all'esterno di un oggetto, 
               # si crea il primo angolo di un rettangolo di selezione, come per il metodo Riquadro
               self.SingleSelection = False
               self.WaitForFirstPoint()
            elif value == QadMsg.get(147): # "SIngolo"
               # Passa al metodo Singolo: viene selezionato il primo oggetto o gruppo di oggetti indicato,
               # senza che vengano richieste altre selezioni.
               self.SingleSelection = True
               if self.entitySet.count() > 0:
                  self.plugIn.setLastEntitySet(self.entitySet)
                  return True # fine               
               self.WaitForFirstPoint()
            elif value == QadMsg.get(165): # "Help"
               self.help = True
               self.WaitForFirstPoint()
         elif type(value) == QgsPoint: # se è stato inserito il punto iniziale del rettangolo
            self.currSelectionMode = QadMsg.get(137) # "Riquadro"
            self.points.append(value)           
            self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.ENTITYSET_SELECTION)
            self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_RECTANGLE)        
            self.getPointMapTool().setStartPoint(value)
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.get(150)) # "Specificare angolo opposto: "
            self.step = 3
         else: # se è stata selezionata un'entità
            # se la selezione è avvenuta con shift premuto o se si deve rimuovere l'entità dal gruppo
            if shiftKey or self.AddOnSelection == False:
               self.AddRemoveEntity(value)
            else:
               self.SetEntity(value)
               
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine               

            self.WaitForFirstPoint()
          
         return False # continua

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL PRIMO PUNTO DEL RETTANGOLO DA OPZIONE 
      # FINESTRA, INTERSECA, RIQUADRO (da step = 1)
      elif self.step == 2: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  self.showMsg(QadMsg.get(132)) # "La finestra non è stata specificata correttamente."
                  self.WaitForFirstPoint()
                  return False
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg
                        
         if type(value) == QgsPoint:
            self.points.append(value)           
            self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.ENTITYSET_SELECTION)
            self.getPointMapTool().setDrawMode(QadGetPointDrawModeEnum.ELASTIC_RECTANGLE)        
            self.getPointMapTool().setStartPoint(value)
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.get(150)) # "Specificare angolo opposto: "
            self.step = 3
         else:
            self.showMsg(QadMsg.get(132)) # "La finestra non è stata specificata correttamente."
            self.WaitForFirstPoint()

         return False # continua


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DEL SECONDO PUNTO DEL RETTANGOLO (da step = 1)
      elif self.step == 3: # dopo aver atteso un punto si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  self.showMsg(QadMsg.get(132)) # "La finestra non è stata specificata correttamente."
                  # si appresta ad attendere un punto
                  self.waitForPoint(QadMsg.get(150)) # "Specificare angolo opposto: "
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
            
            if self.currSelectionMode == QadMsg.get(137): # "Riquadro"
               if self.points[0].x() < value.x():
                  mode = "W"
               else:
                  mode = "C"
            elif self.currSelectionMode == QadMsg.get(134): # "Finestra" 
               mode = "W"
            else: # "Interseca"
               mode = "C"
               
            selSet = qad_utils.getSelSet(mode, self.getPointMapTool(), self.points, \
                                         None, True, True, True, \
                                         self.onlyEditableLayers)
            #qad_debug.breakPoint()
            # se la selezione è avvenuta con shift premuto o se si deve rimuovere il gruppo selSet dal gruppo
            if shiftKey or self.AddOnSelection == False:
               self.AddRemoveSelSet(selSet)
            else:
               self.SetSelSet(selSet)
         
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine
            
            self.WaitForFirstPoint()
         else:
            self.showMsg(QadMsg.get(132)) # "La finestra non è stata specificata correttamente."
            # si appresta ad attendere un punto
            self.waitForPoint(QadMsg.get(150)) # "Specificare angolo opposto: "

         return False # continua


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO PER MODALITA' INTERCETTA (da step = 1 o 4)
      elif self.step == 4: # dopo aver atteso un punto si riavvia il comando
         if self.PLINECommand.run(msgMapTool, msg) == True:
            self.showMsg("\n")
            self.AddRemoveSelSetByFence(self.PLINECommand.vertices)
            del self.PLINECommand
            self.PLINECommand = None
         
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine
            
            self.WaitForFirstPoint()
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PER MODALITA' FCERCHIO e ICERCHIO (da step = 1 o 5)
      elif self.step == 5: # dopo aver atteso un punto si riavvia il comando
         if self.CIRCLECommand.run(msgMapTool, msg) == True:
            self.showMsg("\n")
            if (self.CIRCLECommand.centerPt is not None) and \
               (self.CIRCLECommand.radius is not None):
               circle = QadCircle()
               circle.set(self.CIRCLECommand.centerPt, self.CIRCLECommand.radius)
               points = circle.asPolyline()
               if self.currSelectionMode == QadMsg.get(133): # "FCerchio"
                  self.AddRemoveSelSetByPolygon("WP", points)
               elif self.currSelectionMode == QadMsg.get(148): # "ICerchio"
                  self.AddRemoveSelSetByPolygon("CP", points)               
            
            del self.CIRCLECommand
            self.CIRCLECommand = None
         
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine
            
            self.WaitForFirstPoint()
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI SELEZIONE DI OGGETTI PER MODALITA' FOGGETTI e IOGGETTI (da step = 1 o 6)
      elif self.step == 6: # dopo aver atteso un punto si riavvia il comando
         if self.SSGetClass.run(msgMapTool, msg) == True:
            self.showMsg("\n")
            destCRS = self.SSGetClass.getPointMapTool().canvas.mapRenderer().destinationCrs()
            geoms = self.SSGetClass.entitySet.getGeometryCollection(destCRS) # trasformo la geometria
            
            if self.currSelectionMode == QadMsg.get(160): # "FOggetti"
               self.AddRemoveSelSetByGeometry("WO", geoms)
            elif self.currSelectionMode == QadMsg.get(161): # "IOggetti"
               self.AddRemoveSelSetByGeometry("CO", geoms)
                                 
            del self.SSGetClass
            self.SSGetClass = None
         
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine
            
            self.WaitForFirstPoint()
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PER MODALITA' FPOLIGONO e IPOLIGONO (da step = 1 o 7)
      elif self.step == 7: # dopo aver atteso un punto si riavvia il comando
         if self.MPOLYGONCommand.run(msgMapTool, msg) == True:
            self.showMsg("\n")              
            if self.currSelectionMode == QadMsg.get(140): # "FPoligono"
               self.AddRemoveSelSetByPolygon("WP", self.MPOLYGONCommand.vertices)
            elif self.currSelectionMode == QadMsg.get(141): # "IPoligono"
               self.AddRemoveSelSetByPolygon("CP", self.MPOLYGONCommand.vertices)               
            
            del self.MPOLYGONCommand
            self.MPOLYGONCommand = None
         
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine
            
            self.WaitForFirstPoint()
         return False


      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DI SELEZIONE DI OGGETTI PER MODALITA' FBUFFER e IBUFFER (da step = 1 o 8)
      elif self.step == 8: # dopo aver atteso un punto si riavvia il comando
         if self.MBUFFERCommand.run(msgMapTool, msg) == True:
            self.showMsg("\n")

            bufferGeoms = []
            for layerEntitySet in self.MBUFFERCommand.entitySet.layerEntitySetList:
               geoms = layerEntitySet.getGeometryCollection()
               width = qad_utils.distMapToLayerCoordinates(self.MBUFFERCommand.width, \
                                                           self.MBUFFERCommand.getPointMapTool().canvas,\
                                                           layerEntitySet.layer)
               for geom in geoms:
                  bufferGeoms.append(geom.buffer(width, self.MBUFFERCommand.segments))
                        
            if self.currSelectionMode == QadMsg.get(172): # "FBuffer"
               self.AddRemoveSelSetByGeometry("WO", bufferGeoms)
            elif self.currSelectionMode == QadMsg.get(173): # "IBuffer"
               self.AddRemoveSelSetByGeometry("CO", bufferGeoms)
                                 
            del self.MBUFFERCommand
            self.MBUFFERCommand = None
         
            if self.SingleSelection == True and self.entitySet.count() > 0:
               self.plugIn.setLastEntitySet(self.entitySet)
               return True # fine
            
            self.WaitForFirstPoint()
         return False


# ho dovuto spostare in fondo questo import perchè qad_mbuffer_cmd fa l'import di qad_ssget_cmd
from qad_mbuffer_cmd import QadMBUFFERCommandClass
