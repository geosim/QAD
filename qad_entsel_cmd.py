# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando da inserire in altri comandi per la selezione di una feature
 
                              -------------------
        begin                : 2013-09-18
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
import qad_utils


#===============================================================================
# QadEntSelClass
#===============================================================================
class QadEntSelClass(QadCommandClass):
      
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.entity = QadEntity()
      self.point = None
      self.onlyEditableLayers = False
      self.msg = QadMsg.get(162) # "Selezionare oggetto: "
            
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.get(128)) # "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate\n"
         return True # fine comando

      #=========================================================================
      # RICHIESTA PUNTO o ENTITA'
      if self.step == 0: # inizio del comando
         # imposto il map tool
         self.getPointMapTool().setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION)
         self.getPointMapTool().onlyEditableLayers = self.onlyEditableLayers
         
         keyWords = QadMsg.get(135) # "Ultimo"
                  
         # si appresta ad attendere un punto o enter o una parola chiave         
         # msg, inputType, default, keyWords, nessun controllo
         self.waitFor(self.msg, \
                      QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                      None, \
                      keyWords, QadInputModeEnum.NONE)
         
         self.step = 1
         return False

      #=========================================================================
      # RISPOSTA ALLA RICHIESTA PUNTO o ENTITA'
      elif self.step == 1: # dopo aver atteso un punto si riavvia il comando
         #qad_debug.breakPoint()
         entity = None
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
            if self.getPointMapTool().entity.isInitialized():
               entity = self.getPointMapTool().entity               
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            return True # fine comando
         
         if type(value) == unicode:
            if value == QadMsg.get(135): # "Ultimo"
               # Seleziona l'ultima entità inserita
               lastEnt = self.plugIn.getLastEntity()
               if lastEnt is not None:
                  self.entity.set(lastEnt.layer, lastEnt.featureId)
         elif type(value) == QgsPoint:
            if entity is None:
               # cerco se ci sono entità nel punto indicato
               result = qad_utils.getEntSel(self.getPointMapTool().toCanvasCoordinates(value),
                                            self.getPointMapTool(), \
                                            None, \
                                            True, True, True, \
                                            True, \
                                            self.onlyEditableLayers)
               if result is not None:
                  feature = result[0]
                  layer = result[1]
                  self.entity.set(layer, feature.id())               
            else:
               self.entity.set(entity.layer, entity.featureId)

            self.point = value
                                   
         return True # fine comando
         
