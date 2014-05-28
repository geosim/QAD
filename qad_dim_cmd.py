# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando COPY per copiare oggetti
 
                              -------------------
        begin                : 2014-02-19
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
from qad_dim import *
from qad_dim_maptool import *
from qad_generic_cmd import QadCommandClass
from qad_msg import QadMsg
from qad_getpoint import *
from qad_textwindow import *
from qad_entsel_cmd import QadEntSelClass
from qad_variables import *
import qad_utils
import qad_layer


# Classe che gestisce il comando DIMLINEAR
class QadDIMLINEARCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "DIMLINEARE")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runDIMLINEARCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/dimLinear.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_DIM", "Crea una quota lineare orizzontale o verticale.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.EntSelClass = None      
      self.dimPt1 = QgsPoint()
      self.dimPt2 = QgsPoint()
      self.textRot = 0.0
      self.measure = None
      self.preferredAlignment = QadDimStyleAlignmentEnum.HORIZONTAL
      # leggo lo stile di quotatura corrente (path completa del file di stile)
      dimStyleName = QadVariables.get(QadMsg.translate("Environment variables", "DIMSTYLE"))
      self.dimStyle = QadDimStyle()
      if self.dimStyle.load(dimStyleName) == False:
         self.dimStyle = None
      else:
         self.dimStyle.dimType = QadDimTypeEnum.LINEAR
      

   def __del__(self):
      QadCommandClass.__del__(self)
      if self.EntSelClass is not None:
         self.EntSelClass.entity.deselectOnLayer()
         del self.EntSelClass
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 2: # quando si è in fase di selezione entità
         return self.EntSelClass.getPointMapTool(drawMode)
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_dim_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None


   #============================================================================
   # getStartEndPointClosestPartWithContext
   #============================================================================
   def getStartEndPointClosestPartWithContext(self, entity, point):
      # legge il punto iniziale e finale della parte più vicina al punto di selezione (in map coordinate)
      transformedPt = self.mapToLayerCoordinates(entity.layer, point)
      geom = entity.getGeometry()
      
      # ritorna una tupla (<The squared cartesian distance>,
      #                    <minDistPoint>
      #                    <afterVertex>
      #                    <leftOf>)
      dummy = qad_utils.closestSegmentWithContext(transformedPt, geom)
      # ritorna la sotto-geometria al vertice <atVertex> e la sua posizione nella geometria (0-based)
      subGeom, atSubGeom = qad_utils.getSubGeomAtVertex(geom, dummy[2])
          
      #qad_debug.breakPoint()               
      linearObjectList = qad_utils.QadLinearObjectList()
      linearObjectList.fromPolyline(subGeom.asPolyline())
      
      # la funzione ritorna una lista con (<minima distanza al quadrato>,
      #                                    <punto più vicino>
      #                                    <indice della parte più vicina>       
      #                                    <"a sinistra di">)
      dummy = linearObjectList.closestPartWithContext(transformedPt)
      part = poly1.getLinearObjectAt(dummy[2])
      return part.getStartPt(), part.getEndPt()

   
   #============================================================================
   # addDimToLayers
   #============================================================================
   def addDimToLayers(self, linePosPt):
      return self.dimStyle.addLinearDimToLayers(self.plugIn, self.dimPt1, self.dimPt2, \
                                                linePosPt, self.measure, self.preferredAlignment)
   
   
   #============================================================================
   # waitForFirstPt
   #============================================================================
   def waitForFirstPt(self):
      #qad_debug.breakPoint()
      self.step = 1
      # imposto il map tool
      self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_FIRST_PT)                                

      msg = QadMsg.translate("Command_DIM", "Specificare l'origine della prima linea di estensione o <seleziona oggetto>: ")
      
      # si appresta ad attendere un punto o enter      
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D, \
                   None, \
                   "", QadInputModeEnum.NONE)

   
   #============================================================================
   # waitForSecondPt
   #============================================================================
   def waitForSecondPt(self):
      self.step = 3
      # imposto il map tool
      self.getPointMapTool().dimPt1 = self.dimPt1
      self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.FIRST_PT_KNOWN_ASK_FOR_SECOND_PT)                                
      # si appresta ad attendere un punto
      self.waitForPoint(QadMsg.translate("Command_DIM", "Specificare l'origine della seconda linea di estensione: "))

   
   #============================================================================
   # waitForEntsel
   #============================================================================
   def waitForEntsel(self, msgMapTool, msg):
      if self.EntSelClass is not None:
         del self.EntSelClass
      self.step = 2         
      self.EntSelClass = QadEntSelClass(self.plugIn)
      self.EntSelClass.msg = QadMsg.translate("Command_DIM", "Selezionare l'oggetto da quotare: ")
      # scarto la selezione di punti
      self.EntSelClass.checkPointLayer = False
      self.EntSelClass.checkLineLayer = True
      self.EntSelClass.checkPolygonLayer = True         
      self.EntSelClass.run(msgMapTool, msg)

   
   #============================================================================
   # waitForDimensionLinePos
   #============================================================================
   def waitForDimensionLinePos(self):
      self.step = 4
      # imposto il map tool
      self.getPointMapTool().dimPt2 = self.dimPt2
      self.getPointMapTool().preferredAlignment = self.preferredAlignment
      self.getPointMapTool().dimStyle = self.dimStyle      
      self.getPointMapTool().setMode(Qad_dim_maptool_ModeEnum.FIRST_SECOND_PT_KNOWN_ASK_FOR_LINEAR_DIM_LINE_POS)                                
      
      # si appresta ad attendere un punto o una parola chiave
      keyWords = QadMsg.translate("Command_DIM", "Testo") + " " + \
                 QadMsg.translate("Command_DIM", "Angolo") + " " + \
                 QadMsg.translate("Command_DIM", "Orizzontale") + " " + \
                 QadMsg.translate("Command_DIM", "Verticale") + " " + \
                 QadMsg.translate("Command_DIM", "Ruotato")      
      msg = QadMsg.translate("Command_DIM", "Specificare la posizione della linea di quota o [Testo/Angolo/Orizzontale/Verticale/Ruotato]: ")
      # msg, inputType, default, keyWords, nessun controllo
      self.waitFor(msg, \
                   QadInputTypeEnum.POINT2D | QadInputTypeEnum.KEYWORDS, \
                   None, \
                   "", \
                   QadInputModeEnum.NONE)                                      
      


   #============================================================================
   # run
   #============================================================================
   def run(self, msgMapTool = False, msg = None):
      if self.plugIn.canvas.mapRenderer().destinationCrs().geographicFlag():
         self.showMsg(QadMsg.translate("QAD", "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate.\n"))
         return True # fine comando

      if self.dimStyle is None:
         self.showMsg(QadMsg.translate("QAD", "\nStile di quotatura corrente non valido.\nVerificare il valore della variabile DIMSTYLE.\n"))
         return True # fine comando
         
      errMsg = self.dimStyle.getInValidErrMsg()
      if errMsg is not None:
         self.showMsg(errMsg)
         return True # fine comando
      
      errMsg = self.dimStyle.getNotGraphEditableErrMsg()
      if errMsg is not None:
         self.showMsg(errMsg)
         return True # fine comando
            
                  
      #=========================================================================
      # RICHIESTA SELEZIONE ORIGINE PRIMA LINEA DI ESTENSIONE
      if self.step == 0: # inizio del comando
#          layerList = qad_layer.getLayersByName(qad_utils.wildCard2regularExpr("quote_testi"))
#          
#          g = QgsGeometry.fromPoint(QgsPoint(0,0))
#          f = QgsFeature()
#          f.setGeometry(g)
#          # Add attribute fields to feature.
#          provider = layerList[0].dataProvider()
#          fields = layerList[0].pendingFields()
#          f.setFields(fields)
# 
#          f.setAttribute("text", "abc")
#          f.setAttribute("htext", 10)
#          f.setAttribute("rot", 1)
#          
#          w, h = qad_label.calculateLabelSize(layerList[0], f, self.plugIn.canvas)
         
         self.waitForFirstPt()
         return False
      
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA ORIGINE PRIMA LINEA DI ESTENSIONE (da step = 0)
      elif self.step == 1:
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  value = None # opzione di default None
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False
            else:
               value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            self.waitForEntsel(msgMapTool, msg)
         else:
            self.dimPt1.set(value.x(), value.y())
            self.waitForSecondPt()

         return False

      #=========================================================================
      # RISPOSTA ALLA SELEZIONE DI UN'ENTITA' (da step = 1)
      elif self.step == 2:
         #qad_debug.breakPoint()         
         if self.EntSelClass.run(msgMapTool, msg) == True:
            if self.EntSelClass.entity.isInitialized():
               self.dimPt1, self.dimPt2 = getStartEndPointClosestPartWithContext(self.EntSelClass.entity, \
                                                                                    self.EntSelClass.point)
               self.waitForDimensionLinePos()
               return False
            else:               
               self.showMsg(QadMsg.translate("Command_DIM", "Non ci sono geometrie in questa posizione."))
               self.waitForEntsel(msgMapTool, msg)
         return False # continua

         
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA ORIGINE SECONDA LINEA DI ESTENSIONE (da step = 1)
      elif self.step == 3: # dopo aver atteso un punto o un numero reale si riavvia il comando
         if msgMapTool == True: # il punto arriva da una selezione grafica
            # la condizione seguente si verifica se durante la selezione di un punto
            # è stato attivato un altro plugin che ha disattivato Qad
            # quindi stato riattivato il comando che torna qui senza che il maptool
            # abbia selezionato un punto            
            if self.getPointMapTool().point is None: # il maptool è stato attivato senza un punto
               if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                  return True
               else:
                  self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                  return False

            value = self.getPointMapTool().point
         else: # il punto arriva come parametro della funzione
            value = msg

         if value is None:
            return True

         if type(value) == QgsPoint: # se è stato inserito il secondo punto
            self.dimPt2.set(value.x(), value.y())
            self.waitForDimensionLinePos()
         
         return False 
         
               
      #=========================================================================
      # RISPOSTA ALLA RICHIESTA DELLA POSIZIONE DELLA LINEA DI QUOTA (da step = 2 e 3)
      elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
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
            if value == QadMsg.translate("Command_DIM", "Testo"):
               pass
            elif value == QadMsg.translate("Command_DIM", "Angolo"):
               pass
            elif value == QadMsg.translate("Command_DIM", "Orizzontale"):
               pass
            elif value == QadMsg.translate("Command_DIM", "Verticale"):
               pass
            elif value == QadMsg.translate("Command_DIM", "Ruotato"):
               pass
         elif type(value) == QgsPoint: # se è stato inserito il punto di posizionamento linea quota
            self.preferredAlignment = self.getPointMapTool().preferredAlignment
            self.addDimToLayers(value)
            return True # fine comando
            
         return False
      
      
# Classe che gestisce il comando DIMALIGNED
class QadDIMALIGNEDCommandClass(QadCommandClass):
   
   def getName(self):
      return QadMsg.translate("Command_list", "DIMALLINEATA")

   def connectQAction(self, action):
      QObject.connect(action, SIGNAL("triggered()"), self.plugIn.runDIMALIGNEDCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/dimAligned.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_DIM", "Crea una quota allineata.")
   
   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)
      self.dimPt1 = QgsPoint()
      self.dimPt2 = QgsPoint()
      

   def __del__(self):
      QadCommandClass.__del__(self)
      
   def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_dim_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None
      
      
def aaa(f):
   layerList = qad_layer.getLayersByName(qad_utils.wildCard2regularExpr("quote_testi"))   
   g = QgsGeometry.fromPoint(QgsPoint(0,0))
   f.setGeometry(g)

   f.setAttribute("text", "abc")
   f.setAttribute("htext", 10)
   f.setAttribute("rot", 1)
   return