# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire la dialog per DIMSTYLE
 
                              -------------------
        begin                : 2015-05-19
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
from qgis.core import QgsApplication
from qgis.utils import *
from qgis.gui import *

import qad_dimstyle_details_ui

from qad_variables import *
from qad_dim import *
from qad_msg import QadMsg
import qad_layer
import qad_utils


#######################################################################################
# Classe che gestisce l'interfaccia grafica della funzione di creazione nuovo stile
class QadDIMSTYLE_DETAILS_Dialog(QDialog, QObject, qad_dimstyle_details_ui.Ui_dimStyle_details_dialog):
   def __init__(self, plugIn, dimStyle):
      self.plugIn = plugIn
      self.dimStyle = QadDimStyle(dimStyle) # copio lo stile di quotatura
      self.iface = self.plugIn.iface.mainWindow()
      QDialog.__init__(self, self.iface)
      
      self.setupUi(self)
      
      self.init_db_tab()
      self.init_lines_tab()
      self.init_symbols_tab()
      self.init_text_tab()
      self.init_adjust_tab()
      self.init_primaryUnits_tab()
        
   def setupUi(self, Dialog):
      qad_dimstyle_details_ui.Ui_dimStyle_details_dialog.setupUi(self, self)
      # aggiungo il bottone di qgis QgsColorButtonV2 chiamato dimLineColor 
      # che eredita la posizione di dimLineColorDummy (che viene nascosto)
      self.dimLineColorDummy.setHidden(True)
      self.dimLineColor = QgsColorButtonV2(self.dimLineColorDummy.parent())      
      self.dimLineColor.setGeometry(self.dimLineColorDummy.geometry())
      self.dimLineColor.setObjectName("dimLineColor")
      # aggiungo il bottone di qgis QgsColorButtonV2 chiamato extLineColor 
      # che eredita la posizione di extLineColorDummy (che viene nascosto)      
      self.extLineColorDummy.setHidden(True)
      self.extLineColor = QgsColorButtonV2(self.extLineColorDummy.parent())      
      self.extLineColor.setGeometry(self.extLineColorDummy.geometry())
      self.extLineColor.setObjectName("extLineColor")
            
      self.tabWidget.setCurrentIndex(0)
      # retranslateUi
      #self.dimLineColor.setText(_translate("Dialog", "PushButton", None))

   ####################################################################
   # Inizializzazione del TAB che riguarda i campi di database - inizio
   ####################################################################

   def init_db_tab(self):     
      # layer linee
      for index, layer in enumerate(self.plugIn.iface.legendInterface().layers()):      
         if (layer.type() == QgsMapLayer.VectorLayer) and layer.geometryType() == QGis.Line:
            self.linearLayerName.addItem(layer.name(), index)      
      # seleziono un elemento della lista
      if self.dimStyle.linearLayerName is not None:
         index = self.linearLayerName.findText(self.dimStyle.linearLayerName)
         self.linearLayerName.setCurrentIndex(index)
         self.linearLayerNameChanged(index)
      
      # layer simboli
      for index, layer in enumerate(self.plugIn.iface.legendInterface().layers()):      
         if qad_layer.isSymbolLayer(layer):
            self.symbolLayerName.addItem(layer.name(), index)
      # seleziono un elemento della lista
      if self.dimStyle.symbolLayerName is not None:
         index = self.symbolLayerName.findText(self.dimStyle.symbolLayerName)
         self.symbolLayerName.setCurrentIndex(index)
         self.symbolLayerNameChanged(index)
      
      # layer testi
      for index, layer in enumerate(self.plugIn.iface.legendInterface().layers()):      
         if qad_layer.isTextLayer(layer):
            self.textualLayerName.addItem(layer.name(), index)
      # seleziono un elemento della lista
      if self.dimStyle.textualLayerName is not None:
         index = self.textualLayerName.findText(self.dimStyle.textualLayerName)
         self.textualLayerName.setCurrentIndex(index)
         self.textualLayerNameChanged(index)

   def accept_db_tab(self):     
      # layer linee
      self.dimStyle.linearLayerName = self.linearLayerName.currentText()
      self.dimStyle.lineTypeFieldName = self.lineTypeFieldName.currentText()
      
      # layer simboli
      self.dimStyle.symbolLayerName = self.symbolLayerName.currentText()
      self.dimStyle.symbolFieldName = self.symbolFieldName.currentText() 
      self.dimStyle.scaleFieldName = self.scaleFieldName.currentText()

      self.dimStyle.colorFieldName = self.colorFieldName.currentText()
      self.dimStyle.rotFieldName = self.rotFieldName.currentText()
      self.dimStyle.componentFieldName = self.componentFieldName.currentText()
      self.dimStyle.idParentFieldName = self.idParentFieldName.currentText()
      
      # layer testi
      self.dimStyle.textualLayerName = self.textualLayerName.currentText()
      self.dimStyle.idFieldName = self.idFieldName.currentText()
      self.dimStyle.dimStyleFieldName = self.dimStyleFieldName.currentText()
      self.dimStyle.dimTypeFieldName = self.dimTypeFieldName.currentText()

   def linearLayerNameChanged(self, index):
      if index == -1:
         return
      # leggo l'elemento selezionato
      legendIndex = self.linearLayerName.itemData(index)
      layer = iface.legendInterface().layers()[legendIndex]
      if layer is not None:
         self.lineTypeFieldName.clear() # remove all items
         self.colorFieldName.clear() # remove all items

         for field in layer.pendingFields():
            if field.type() == QVariant.String:
               self.lineTypeFieldName.addItem(field.name(), field)
               self.colorFieldName.addItem(field.name(), field)

         # seleziono un elemento della lista
         if self.dimStyle.lineTypeFieldName is not None:
            index = self.lineTypeFieldName.findText(self.dimStyle.lineTypeFieldName)
            self.lineTypeFieldName.setCurrentIndex(index)

         if self.dimStyle.colorFieldName is not None:
            index = self.colorFieldName.findText(self.dimStyle.colorFieldName)
            self.colorFieldName.setCurrentIndex(index)
               
   def symbolLayerNameChanged(self, index):
      if index == -1:
         return
      # leggo l'elemento selezionato
      legendIndex = self.symbolLayerName.itemData(index)
      layer = iface.legendInterface().layers()[legendIndex]
      if layer is not None:
         self.symbolFieldName.clear() # remove all items
         self.scaleFieldName.clear() # remove all items

         self.rotFieldName.clear() # remove all items
         self.componentFieldName.clear() # remove all items
         self.idParentFieldName.clear() # remove all items
         
         for field in layer.pendingFields():
            if field.type() == QVariant.String:
               self.symbolFieldName.addItem(field.name(), field)               
               self.componentFieldName.addItem(field.name(), field)
            elif qad_utils.isNumericField(field):
               self.scaleFieldName.addItem(field.name(), field)
               self.rotFieldName.addItem(field.name(), field)
               self.idParentFieldName.addItem(field.name(), field)
               
         # seleziono un elemento della lista
         if self.dimStyle.symbolFieldName is not None:
            index = self.symbolFieldName.findText(self.dimStyle.symbolFieldName)
            self.symbolFieldName.setCurrentIndex(index)
         if self.dimStyle.scaleFieldName is not None:
            index = self.scaleFieldName.findText(self.dimStyle.scaleFieldName)
            self.scaleFieldName.setCurrentIndex(index)
            
         if self.dimStyle.rotFieldName is not None:
            index = self.rotFieldName.findText(self.dimStyle.rotFieldName)
            self.rotFieldName.setCurrentIndex(index)
         if self.dimStyle.componentFieldName is not None:
            index = self.componentFieldName.findText(self.dimStyle.componentFieldName)
            self.componentFieldName.setCurrentIndex(index)
         if self.dimStyle.idParentFieldName is not None:
            index = self.idParentFieldName.findText(self.dimStyle.idParentFieldName)
            self.idParentFieldName.setCurrentIndex(index)

   def textualLayerNameChanged(self, index):
      if index == -1:
         return
      # leggo l'elemento selezionato
      legendIndex = self.textualLayerName.itemData(index)
      layer = iface.legendInterface().layers()[legendIndex]
      if layer is not None:
         self.idFieldName.clear() # remove all items
         self.dimStyleFieldName.clear() # remove all items
         self.dimTypeFieldName.clear() # remove all items
         for field in layer.pendingFields():
            if field.type() == QVariant.String:
               self.dimStyleFieldName.addItem(field.name(), field)
               self.dimTypeFieldName.addItem(field.name(), field)
            elif qad_utils.isNumericField(field):
               self.idFieldName.addItem(field.name(), field)

         # seleziono un elemento della lista
         if self.dimStyle.idFieldName is not None:
            index = self.idFieldName.findText(self.dimStyle.idFieldName)
            self.idFieldName.setCurrentIndex(index)
         if self.dimStyle.dimStyleFieldName is not None:
            index = self.dimStyleFieldName.findText(self.dimStyle.dimStyleFieldName)
            self.dimStyleFieldName.setCurrentIndex(index)
         if self.dimStyle.dimTypeFieldName is not None:
            index = self.dimTypeFieldName.findText(self.dimStyle.dimTypeFieldName)
            self.dimTypeFieldName.setCurrentIndex(index)

   ####################################################################
   # Inizializzazione del TAB che riguarda i campi di database - fine
   # Inizializzazione del TAB che riguarda le linee di quotatura - inizio
   ####################################################################
   
   def init_lines_tab(self):
      self.dimLineColor.setColor(QColor(self.dimStyle.dimLineColor))
      self.dimLineLineType.setText(self.dimStyle.dimLineLineType)
      self.dimLine1Show.setChecked(self.dimStyle.dimLine1Show)
      self.dimLine2Show.setChecked(self.dimStyle.dimLine2Show)
      
      self.extLineColor.setColor(QColor(self.dimStyle.extLineColor))
      self.extLine1LineType.setText(self.dimStyle.extLine1LineType)
      self.extLine2LineType.setText(self.dimStyle.extLine2LineType)
      self.extLine1Show.setChecked(self.dimStyle.extLine1Show)
      self.extLine2Show.setChecked(self.dimStyle.extLine2Show)
      self.extLineOffsetDimLine.setValue(self.dimStyle.extLineOffsetDimLine)
      self.extLineOffsetOrigPoints.setValue(self.dimStyle.extLineOffsetOrigPoints)
      self.extLineIsFixedLen.setChecked(self.dimStyle.extLineIsFixedLen)
      self.extLineFixedLen.setValue(self.dimStyle.extLineFixedLen)
      self.extLineIsFixedLenToggled(self.dimStyle.extLineIsFixedLen)

   def accept_lines_tab(self):     
      self.dimStyle.dimLineColor = self.dimLineColor.color().name()
      self.dimStyle.dimLineLineType = self.dimLineLineType.text()
      self.dimStyle.dimLine1Show = self.dimLine1Show.isChecked()
      self.dimStyle.dimLine2Show = self.dimLine2Show.isChecked()

      self.dimStyle.extLineColor = self.extLineColor.color().name()
      self.dimStyle.extLine1LineType = self.extLine1LineType.text()
      self.dimStyle.extLine2LineType = self.extLine2LineType.text()
      self.dimStyle.extLine1Show = self.extLine1Show.isChecked()
      self.dimStyle.extLine2Show = self.extLine2Show.isChecked()
      self.dimStyle.extLineOffsetDimLine = self.extLineOffsetDimLine.value()
      self.dimStyle.extLineOffsetOrigPoints = self.extLineOffsetOrigPoints.value()
      self.dimStyle.extLineIsFixedLen = self.extLineIsFixedLen.isChecked()
      self.dimStyle.extLineFixedLen = self.extLineFixedLen.value()

   def extLineIsFixedLenToggled(self, value):
      self.extLineFixedLen.setEnabled(value)

   ####################################################################
   # Inizializzazione del TAB che riguarda le linee di quotatura - fine
   # Inizializzazione del TAB che riguarda i simboli di quotatura - inizio
   ####################################################################
   
   def init_symbols_tab(self):
      self.block1Name.setText(self.dimStyle.block1Name)
      self.block2Name.setText(self.dimStyle.block2Name)
      self.blockLeaderName.setText(self.dimStyle.blockLeaderName)
      self.blockWidth.setValue(self.dimStyle.blockWidth)
      self.blockScale.setValue(self.dimStyle.blockScale)

   def accept_symbols_tab(self):
      self.dimStyle.block1Name = self.block1Name.text()
      self.dimStyle.block2Name = self.block2Name.text()
      self.dimStyle.blockLeaderName = self.blockLeaderName.text()
      self.dimStyle.blockWidth = self.blockWidth.value()      
      self.dimStyle.blockScale = self.blockScale.value()      

   
   ####################################################################
   # Inizializzazione del TAB che riguarda i simboli di quotatura - fine
   # Inizializzazione del TAB che riguarda i testi di quotatura - inizio
   ####################################################################

   def init_text_tab(self):
      index = self.textFont.findText(self.dimStyle.textFont)
      self.textFont.setCurrentIndex(index)
      self.textHeight.setValue(self.dimStyle.textHeight)
      
      # textVerticalPos
      self.textVerticalPos.addItem(QadMsg.translate("DimStyle_Dialog", "Centrato"))
      self.textVerticalPos.addItem(QadMsg.translate("DimStyle_Dialog", "Sopra"))
      self.textVerticalPos.addItem(QadMsg.translate("DimStyle_Dialog", "Esterno"))
      self.textVerticalPos.addItem(QadMsg.translate("DimStyle_Dialog", "Sotto"))
      if self.dimStyle.textVerticalPos == QadDimStyleTxtVerticalPosEnum.CENTERED_LINE:
         self.textVerticalPos.setCurrentIndex(0)
      elif self.dimStyle.textVerticalPos == QadDimStyleTxtVerticalPosEnum.ABOVE_LINE:
         self.textVerticalPos.setCurrentIndex(1)
      elif self.dimStyle.textVerticalPos == QadDimStyleTxtVerticalPosEnum.EXTERN_LINE:
         self.textVerticalPos.setCurrentIndex(2)
      elif self.dimStyle.textVerticalPos == QadDimStyleTxtVerticalPosEnum.BELOW_LINE:
         self.textVerticalPos.setCurrentIndex(3)
   
      # textHorizontalPos
      self.textHorizontalPos.addItem(QadMsg.translate("DimStyle_Dialog", "Centrato"))
      self.textHorizontalPos.addItem(QadMsg.translate("DimStyle_Dialog", "Alla linea di estensione 1"))
      self.textHorizontalPos.addItem(QadMsg.translate("DimStyle_Dialog", "Alla linea di estensione 2"))
      self.textHorizontalPos.addItem(QadMsg.translate("DimStyle_Dialog", "Sopra linea di estensione 1"))
      self.textHorizontalPos.addItem(QadMsg.translate("DimStyle_Dialog", "Sopra linea di estensione 2"))      
      if self.dimStyle.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.CENTERED_LINE:
         self.textHorizontalPos.setCurrentIndex(0)
      elif self.dimStyle.textHorizontalPos == QadDimStyleTxtVerticalPosEnum.FIRST_EXT_LINE:
         self.textHorizontalPos.setCurrentIndex(1)
      elif self.dimStyle.textHorizontalPos == QadDimStyleTxtVerticalPosEnum.SECOND_EXT_LINE:
         self.textHorizontalPos.setCurrentIndex(2)         
      elif self.dimStyle.textHorizontalPos == QadDimStyleTxtVerticalPosEnum.FIRST_EXT_LINE_UP:
         self.textHorizontalPos.setCurrentIndex(3)         
      elif self.dimStyle.textHorizontalPos == QadDimStyleTxtVerticalPosEnum.SECOND_EXT_LINE_UP:
         self.textHorizontalPos.setCurrentIndex(4)         
      
      # textDirection
      self.textDirection.addItem(QadMsg.translate("DimStyle_Dialog", "Da sinistra a destra"))
      self.textDirection.addItem(QadMsg.translate("DimStyle_Dialog", "Da destra a sinistra"))
      if self.dimStyle.textDirection == QadDimStyleTxtDirectionEnum.SX_TO_DX:
         self.textDirection.setCurrentIndex(0)
      elif self.dimStyle.textDirection == QadDimStyleTxtDirectionEnum.DX_TO_SX:
         self.textDirection.setCurrentIndex(1)
      
      self.textOffsetDist.setValue(self.dimStyle.textOffsetDist)
      
      # textForcedRot
      if self.dimStyle.textRotMode == QadDimStyleTxtRotModeEnum.HORIZONTAL:
         self.textRotModeHorizontal.setChecked(True)         
      elif self.dimStyle.textRotMode == QadDimStyleTxtRotModeEnum.ALIGNED_LINE:
         self.textRotModeAligned.setChecked(True)
      elif self.dimStyle.textRotMode == QadDimStyleTxtRotModeEnum.ISO:
         self.textRotModeISO.setChecked(True)
      elif self.dimStyle.textRotMode == QadDimStyleTxtRotModeEnum.FORCED_ROTATION:
         self.textRotModeFixedRot.setChecked(True)
      
      self.textForcedRot.setValue(self.dimStyle.textForcedRot)
      self.textRotModeFixedRotToggled(self.textRotModeFixedRot.isChecked())

   def accept_text_tab(self):
      self.dimStyle.textFont = self.textFont.currentText()
      self.dimStyle.textHeight = self.textHeight.value()
      
      # textVerticalPos
      if self.textVerticalPos.currentIndex() == 0:
         self.dimStyle.textVerticalPos = QadDimStyleTxtVerticalPosEnum.CENTERED_LINE
      elif self.textVerticalPos.currentIndex() == 1:
         self.dimStyle.textVerticalPos = QadDimStyleTxtVerticalPosEnum.ABOVE_LINE
      elif self.textVerticalPos.currentIndex() == 2:
         self.dimStyle.textVerticalPos = QadDimStyleTxtVerticalPosEnum.EXTERN_LINE
      elif self.textVerticalPos.currentIndex() == 3:
         self.dimStyle.textVerticalPos = QadDimStyleTxtVerticalPosEnum.BELOW_LINE
   
      # textHorizontalPos
      if self.textHorizontalPos.currentIndex() == 0:
         self.dimStyle.textHorizontalPos = QadDimStyleTxtHorizontalPosEnum.CENTERED_LINE
      elif self.textHorizontalPos.currentIndex() == 1:
         self.dimStyle.textHorizontalPos = QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE
      elif self.textHorizontalPos.currentIndex() == 2:
         self.dimStyle.textHorizontalPos = QadDimStyleTxtHorizontalPosEnum.SECOND_EXT_LINE
      elif self.textHorizontalPos.currentIndex() == 3:
         self.dimStyle.textHorizontalPos = QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE_UP
      elif self.textHorizontalPos.currentIndex() == 4:
         self.dimStyle.textHorizontalPos = QadDimStyleTxtHorizontalPosEnum.SECOND_EXT_LINE_UP
      
      # textDirection
      if self.textDirection.currentIndex() == 0:
         self.dimStyle.textDirection = QadDimStyleTxtDirectionEnum.SX_TO_DX
      elif self.textDirection.currentIndex() == 1:
         self.dimStyle.textDirection = QadDimStyleTxtDirectionEnum.DX_TO_SX
      
      self.dimStyle.textOffsetDist = self.textOffsetDist.value()
      
      # textForcedRot
      if self.textRotModeHorizontal.isChecked():
         self.dimStyle.textRotMode = QadDimStyleTxtRotModeEnum.HORIZONTAL
      elif self.textRotModeAligned.isChecked():
         self.dimStyle.textRotMode = QadDimStyleTxtRotModeEnum.ALIGNED_LINE
      elif self.textRotModeISO.isChecked():
         self.dimStyle.textRotMode = QadDimStyleTxtRotModeEnum.ISO
      elif self.textRotModeFixedRot.isChecked():
         self.dimStyle.textRotMode = QadDimStyleTxtRotModeEnum.FORCED_ROTATION
     
      self.dimStyle.textForcedRot = self.textForcedRot.value()

   def textRotModeFixedRotToggled(self, value):
      self.textForcedRot.setEnabled(value)
      

   ####################################################################
   # Inizializzazione del TAB che riguarda i testi di quotatura - fine
   # Inizializzazione del TAB che riguarda l'adattamento dei componenti di quotatura - inizio
   ####################################################################

   def init_adjust_tab(self):
      # self.textAdjustAlwaysInside in futuro
      
      if self.dimStyle.textBlockAdjust == QadDimStyleTextBlocksAdjustEnum.WHICHEVER_FITS_BEST:        
         self.textBlockAdjustWhicheverFitsBestOutside.setChecked(True)
      elif self.dimStyle.textBlockAdjust == QadDimStyleTextBlocksAdjustEnum.FIRST_BLOCKS_THEN_TEXT:        
         self.textBlockAdjustFirstSymbolOutside.setChecked(True)
      elif self.dimStyle.textBlockAdjust == QadDimStyleTextBlocksAdjustEnum.FIRST_TEXT_THEN_BLOCKS:        
         self.textBlockAdjustFirstTextOutside.setChecked(True)
      elif self.dimStyle.textBlockAdjust == QadDimStyleTextBlocksAdjustEnum.BOTH_OUTSIDE_EXT_LINES:        
         self.textBlockAdjustBothtOutside.setChecked(True)

      self.blockSuppressionForNoSpace.setChecked(self.dimStyle.blockSuppressionForNoSpace)

   def accept_adjust_tab(self):
      if self.textBlockAdjustWhicheverFitsBestOutside.isChecked():
         self.dimStyle.textBlockAdjust = QadDimStyleTextBlocksAdjustEnum.WHICHEVER_FITS_BEST
      elif self.textBlockAdjustFirstSymbolOutside.isChecked():
         self.dimStyle.textBlockAdjust = QadDimStyleTextBlocksAdjustEnum.FIRST_BLOCKS_THEN_TEXT
      elif self.textBlockAdjustFirstTextOutside.isChecked():
         self.dimStyle.textBlockAdjust = QadDimStyleTextBlocksAdjustEnum.FIRST_TEXT_THEN_BLOCKS
      elif self.textBlockAdjustBothtOutside.isChecked():
         self.dimStyle.textBlockAdjust = QadDimStyleTextBlocksAdjustEnum.BOTH_OUTSIDE_EXT_LINES

      self.dimStyle.blockSuppressionForNoSpace = self.blockSuppressionForNoSpace.isChecked()

   ####################################################################
   # Inizializzazione del TAB che riguarda l'adattamento dei componenti di quotatura - fine
   # Inizializzazione del TAB che riguarda le unità primarie di quotatura - inizio
   ####################################################################

   def init_primaryUnits_tab(self):
      # textDecimals
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Dialog", "0"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Dialog", "0.0"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Dialog", "0.00"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Dialog", "0.000"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Dialog", "0.0000"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Dialog", "0.00000"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Dialog", "0.000000"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Dialog", "0.0000000"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Dialog", "0.00000000"))
      self.textDecimals.setCurrentIndex(self.dimStyle.textDecimals)
      
      # textDecimalSep
      self.textDecimalSep.addItem(QadMsg.translate("DimStyle_Dialog", "',' Virgola"))
      self.textDecimalSep.addItem(QadMsg.translate("DimStyle_Dialog", "'.' Punto"))
      self.textDecimalSep.addItem(QadMsg.translate("DimStyle_Dialog", "' ' Spazio"))
      if self.dimStyle.textDecimalSep == ".": # punto
         self.textDecimalSep.setCurrentIndex(0)
      elif self.dimStyle.textDecimalSep == ",": # virgola
         self.textDecimalSep.setCurrentIndex(1)
      elif self.dimStyle.textDecimalSep == " ": # spazio
         self.textDecimalSep.setCurrentIndex(2)
      
      self.textPrefix.setText(self.dimStyle.textPrefix)
      self.textSuffix.setText(self.dimStyle.textSuffix)
      
      self.textSuppressLeadingZeros.setChecked(self.dimStyle.textSuppressLeadingZeros)
      self.textDecimaZerosSuppression.setChecked(self.dimStyle.textDecimaZerosSuppression)

   def accept_primaryUnits_tab(self):
      # textDecimals
      self.dimStyle.textDecimals = self.textDecimals.currentIndex()
      
      # textDecimalSep
      if self.textDecimalSep.currentIndex() == 0: # punto
         self.dimStyle.textDecimalSep = "."
      elif self.textDecimalSep.currentIndex() == 1: # virgola 
         self.dimStyle.textDecimalSep = ","
      elif self.textDecimalSep.currentIndex() == 2: # spazio 
         self.dimStyle.textDecimalSep = " "
      
      self.dimStyle.textPrefix = self.textPrefix.text()
      self.dimStyle.textSuffix = self.textSuffix.text() 
      
      self.dimStyle.textSuppressLeadingZeros = self.textSuppressLeadingZeros.isChecked()
      self.dimStyle.textDecimaZerosSuppression = self.textDecimaZerosSuppression.isChecked()


   ####################################################################
   # Inizializzazione del TAB che riguarda le unità primarie di quotatura - fine
   ####################################################################

   def ButtonHELP_Pressed(self):
      # per conoscere la sezione/pagina del file html usare internet explorer,
      # selezionare nella finestra di destra la voce di interesse e leggerne l'indirizzo dalla casella in alto.
      # Questo perché internet explorer inserisce tutti i caratteri di spaziatura e tab che gli altri browser non fanno.
      qad_utils.qadShowPluginHelp("7%C2%A0%C2%A0%C2%A0%C2%A0%C2%A0%20%C2%A0GESTIONE%20DEI%20PROGETTI")

   def accept(self):
      self.accept_db_tab()
      self.accept_lines_tab()
      self.accept_symbols_tab()
      self.accept_text_tab()
      self.accept_adjust_tab()
      self.accept_primaryUnits_tab()
      errMsg = self.dimStyle.getInValidErrMsg()
      if errMsg is not None:
         errMsg += "\nMantenere queste impostazioni ?"
         res = QMessageBox.question(self, QadMsg.translate("QAD", "QAD"), errMsg, \
                                 QMessageBox.Yes | QMessageBox.No)
         if res == QMessageBox.No:
            return
      QDialog.accept(self)