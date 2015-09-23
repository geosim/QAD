# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire la dialog per DIMSTYLE
 
                              -------------------
        begin                : 2015-05-19
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
from qgis.core import QgsApplication
from qgis.utils import *
from qgis.gui import *

import qad_dimstyle_details_ui

from qad_variables import *
from qad_dim import *
from qad_msg import QadMsg, qadShowPluginHelp
import qad_layer
import qad_utils


#######################################################################################
# Classe che gestisce l'interfaccia grafica della funzione di creazione nuovo stile
class QadDIMSTYLE_DETAILS_Dialog(QDialog, QObject, qad_dimstyle_details_ui.Ui_DimStyle_Details_Dialog):
   def __init__(self, plugIn, dimStyle):
      self.plugIn = plugIn
      self.dimStyle = QadDimStyle(dimStyle) # copio lo stile di quotatura
      self.iface = self.plugIn.iface.mainWindow()
      QDialog.__init__(self, self.iface)

      self.onInit = False # vero se si è in fase di inizializzazione
      
      self.setupUi(self)
      
      self.init_db_tab()
      self.init_lines_tab()
      self.init_symbols_tab()
      self.init_text_tab()
      self.init_adjust_tab()
      self.init_primaryUnits_tab()
      self.previewDim.drawDim(self.dimStyle)

   def closeEvent(self, event):
      del self.previewDim # cancello il canvans di preview della quota chiamato QadPreviewDim 
      return QDialog.closeEvent(self, event)
        
   def setupUi(self, Dialog):
      qad_dimstyle_details_ui.Ui_DimStyle_Details_Dialog.setupUi(self, self)
      # aggiungo il bottone di qgis QgsColorButtonV2 chiamato dimLineColor 
      # che eredita la posizione di dimLineColorDummy (che viene nascosto)
      self.dimLineColorDummy.setHidden(True)
      self.dimLineColor = QgsColorButtonV2(self.dimLineColorDummy.parent())      
      self.dimLineColor.setGeometry(self.dimLineColorDummy.geometry())
      self.dimLineColor.setObjectName("dimLineColor")
      QObject.connect(self.dimLineColor, SIGNAL("colorChanged(QColor)"), self.dimLineColorChanged)
      
      # aggiungo il bottone di qgis QgsColorButtonV2 chiamato extLineColor 
      # che eredita la posizione di extLineColorDummy (che viene nascosto)      
      self.extLineColorDummy.setHidden(True)
      self.extLineColor = QgsColorButtonV2(self.extLineColorDummy.parent())      
      self.extLineColor.setGeometry(self.extLineColorDummy.geometry())
      self.extLineColor.setObjectName("extLineColor")
      QObject.connect(self.extLineColor, SIGNAL("colorChanged(QColor)"), self.extLineColorChanged)
      
      # aggiungo il bottone di qgis QgsColorButtonV2 chiamato textColor 
      # che eredita la posizione di textColorDummy (che viene nascosto)      
      self.textColorDummy.setHidden(True)
      self.textColor = QgsColorButtonV2(self.textColorDummy.parent())      
      self.textColor.setGeometry(self.textColorDummy.geometry())
      self.textColor.setObjectName("textColor")
      QObject.connect(self.textColor, SIGNAL("colorChanged(QColor)"), self.textColorChanged)

      # aggiungo il canvans di preview della quota chiamato QadPreviewDim 
      # che eredita la posizione di previewDummy (che viene nascosto)      
      self.previewDummy.setHidden(True)
      self.previewDim = QadPreviewDim(self.previewDummy.parent(), self.plugIn)
      self.previewDim.setGeometry(self.previewDummy.geometry())
      self.previewDim.setObjectName("previewDim")

      self.tabWidget.setCurrentIndex(0)

   def currentTabChanged(self, index):
      self.previewDim.setParent(self.tabWidget.widget(index))
      self.previewDim.show()
      

   ####################################################################
   # Inizializzazione del TAB che riguarda i campi di database - inizio
   ####################################################################

   def init_db_tab(self):
      self.onInit = True 
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
      self.onInit = False 

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

   def redrawDimOnDBTabChanged(self):
      if self.onInit == True: # esco se sono in fase di inizializzazione
         return 
      self.accept_db_tab()
      self.previewDim.drawDim(self.dimStyle)

   def colorFieldNameChanged(self, index):
      self.redrawDimOnDBTabChanged()

   def componentFieldNameChanged(self, index):
      self.redrawDimOnDBTabChanged()

   def dimStyleFieldNameChanged(self, index):
      self.redrawDimOnDBTabChanged()

   def dimTypeFieldNameChanged(self, index):
      self.redrawDimOnDBTabChanged()

   def idFieldNameChanged(self, index):
      self.redrawDimOnDBTabChanged()

   def idParentFieldNameChanged(self, index):
      self.redrawDimOnDBTabChanged()

   def linetypeFieldNameChanged(self, index):
      self.redrawDimOnDBTabChanged()

   def linearLayerNameChanged(self, index):
      if index == -1:
         return
      # leggo l'elemento selezionato
      legendIndex = self.linearLayerName.itemData(index)
      layer = iface.legendInterface().layers()[legendIndex]
      if layer is not None:
         self.lineTypeFieldName.clear() # remove all items and add an empty row (optional parameter)
         self.lineTypeFieldName.addItem("")

         for field in layer.pendingFields():
            if field.type() == QVariant.String:
               self.lineTypeFieldName.addItem(field.name(), field)

         # seleziono un elemento della lista
         if self.dimStyle.lineTypeFieldName is not None:
            index = self.lineTypeFieldName.findText(self.dimStyle.lineTypeFieldName)
            self.lineTypeFieldName.setCurrentIndex(index)
      self.redrawDimOnDBTabChanged()

   def rotFieldNameChanged(self, index):
      self.redrawDimOnDBTabChanged()

   def scaleFieldNameChanged(self, index):
      self.redrawDimOnDBTabChanged()

   def symbolFieldNameChanged(self, index):
      self.redrawDimOnDBTabChanged()

   def symbolLayerNameChanged(self, index):
      if index == -1:
         return
      # leggo l'elemento selezionato
      legendIndex = self.symbolLayerName.itemData(index)
      layer = iface.legendInterface().layers()[legendIndex]
      if layer is not None:
         self.symbolFieldName.clear() # remove all items and add an empty row (optional parameter)
         self.symbolFieldName.addItem("")
         self.scaleFieldName.clear() # remove all items and add an empty row (optional parameter)
         self.scaleFieldName.addItem("")

         self.rotFieldName.clear() # remove all items
         self.componentFieldName.clear() # remove all items and add an empty row (optional parameter)
         self.componentFieldName.addItem("")
         self.idParentFieldName.clear() # remove all items and add an empty row (optional parameter)
         self.idParentFieldName.addItem("")
         
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
      self.redrawDimOnDBTabChanged()

   def textualLayerNameChanged(self, index):
      if index == -1:
         return
      # leggo l'elemento selezionato
      legendIndex = self.textualLayerName.itemData(index)
      layer = iface.legendInterface().layers()[legendIndex]
      if layer is not None:
         self.idFieldName.clear() # remove all items and add an empty row (optional parameter)
         self.idFieldName.addItem("")
         self.dimStyleFieldName.clear() # remove all items and add an empty row (optional parameter)
         self.dimStyleFieldName.addItem("")
         self.dimTypeFieldName.clear() # remove all items and add an empty row (optional parameter)
         self.dimTypeFieldName.addItem("")
         self.colorFieldName.clear() # remove all items and add an empty row (optional parameter)
         self.colorFieldName.addItem("")
         
         for field in layer.pendingFields():
            if field.type() == QVariant.String:
               self.dimStyleFieldName.addItem(field.name(), field)
               self.dimTypeFieldName.addItem(field.name(), field)
               self.colorFieldName.addItem(field.name(), field)
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
         if self.dimStyle.colorFieldName is not None:
            index = self.colorFieldName.findText(self.dimStyle.colorFieldName)
            self.colorFieldName.setCurrentIndex(index)
      self.redrawDimOnDBTabChanged()


   ####################################################################
   # Inizializzazione del TAB che riguarda i campi di database - fine
   # Inizializzazione del TAB che riguarda le linee di quotatura - inizio
   ####################################################################
   
   def init_lines_tab(self):
      self.onInit = True 
      self.dimLineColor.setColor(QColor(self.dimStyle.dimLineColor))
      self.dimLineLineType.setText(self.dimStyle.dimLineLineType)
      self.dimLine1Hide.setChecked(not self.dimStyle.dimLine1Show)
      self.dimLine2Hide.setChecked(not self.dimStyle.dimLine2Show)
      
      self.extLineColor.setColor(QColor(self.dimStyle.extLineColor))
      self.extLine1LineType.setText(self.dimStyle.extLine1LineType)
      self.extLine2LineType.setText(self.dimStyle.extLine2LineType)
      self.extLine1Hide.setChecked(not self.dimStyle.extLine1Show)
      self.extLine2Hide.setChecked(not self.dimStyle.extLine2Show)
      self.extLineOffsetDimLine.setValue(self.dimStyle.extLineOffsetDimLine)
      self.extLineOffsetOrigPoints.setValue(self.dimStyle.extLineOffsetOrigPoints)
      self.extLineIsFixedLen.setChecked(self.dimStyle.extLineIsFixedLen)
      self.extLineFixedLen.setValue(self.dimStyle.extLineFixedLen)
      self.extLineIsFixedLenToggled(self.dimStyle.extLineIsFixedLen)
      self.onInit = False 

   def accept_lines_tab(self):     
      self.dimStyle.dimLineColor = self.dimLineColor.color().name()
      self.dimStyle.dimLineLineType = self.dimLineLineType.text()
      self.dimStyle.dimLine1Show = not self.dimLine1Hide.isChecked()
      self.dimStyle.dimLine2Show = not self.dimLine2Hide.isChecked()

      self.dimStyle.extLineColor = self.extLineColor.color().name()
      self.dimStyle.extLine1LineType = self.extLine1LineType.text()
      self.dimStyle.extLine2LineType = self.extLine2LineType.text()
      self.dimStyle.extLine1Show = not self.extLine1Hide.isChecked()
      self.dimStyle.extLine2Show = not self.extLine2Hide.isChecked()
      self.dimStyle.extLineOffsetDimLine = self.extLineOffsetDimLine.value()
      self.dimStyle.extLineOffsetOrigPoints = self.extLineOffsetOrigPoints.value()
      self.dimStyle.extLineIsFixedLen = self.extLineIsFixedLen.isChecked()
      self.dimStyle.extLineFixedLen = self.extLineFixedLen.value()

   def redrawDimOnLinesTabChanged(self):
      if self.onInit == True: # esco se sono in fase di inizializzazione
         return 
      self.accept_lines_tab()
      self.previewDim.drawDim(self.dimStyle)

   def dimLine1HideToggled(self, value):
      self.redrawDimOnLinesTabChanged()

   def dimLine2HideToggled(self, value):
      self.redrawDimOnLinesTabChanged()

   def dimLineColorChanged(self, value):
      self.redrawDimOnLinesTabChanged()

   def dimLineLineTypeChanged(self, value):
      self.redrawDimOnLinesTabChanged()

   def extLineColorChanged(self, value):
      self.redrawDimOnLinesTabChanged()

   def extLineFixedLenChanged(self, value):
      self.redrawDimOnLinesTabChanged()

   def extLineIsFixedLenToggled(self, value):
      self.redrawDimOnLinesTabChanged()

   def extLineOffsetDimLineChanged(self, value):
      self.redrawDimOnLinesTabChanged()

   def extLineOffsetOrigPointsChanged(self, value):
      self.redrawDimOnLinesTabChanged()

   def extLine1HideToggled(self, value):
      self.redrawDimOnLinesTabChanged()

   def extLine1LineTypeChanged(self, value):
      self.redrawDimOnLinesTabChanged()

   def extLine2HideToggled(self, value):
      self.redrawDimOnLinesTabChanged()

   def extLine2LineTypeChanged(self, value):
      self.redrawDimOnLinesTabChanged()
   
   def extLineIsFixedLenToggled(self, value):
      self.extLineFixedLen.setEnabled(value)
      self.redrawDimOnLinesTabChanged()


   ####################################################################
   # Inizializzazione del TAB che riguarda le linee di quotatura - fine
   # Inizializzazione del TAB che riguarda i simboli di quotatura - inizio
   ####################################################################
   
   def init_symbols_tab(self):
      self.onInit = True 
      self.block1Name.setText(self.dimStyle.block1Name)
      self.block2Name.setText(self.dimStyle.block2Name)
      self.blockLeaderName.setText(self.dimStyle.blockLeaderName)
      self.blockWidth.setValue(self.dimStyle.blockWidth)
      self.blockScale.setValue(self.dimStyle.blockScale)
      self.onInit = False 

   def accept_symbols_tab(self):
      self.dimStyle.block1Name = self.block1Name.text()
      self.dimStyle.block2Name = self.block2Name.text()
      self.dimStyle.blockLeaderName = self.blockLeaderName.text()
      self.dimStyle.blockWidth = self.blockWidth.value()      
      self.dimStyle.blockScale = self.blockScale.value()      

   def redrawDimOnSymbolsTabChanged(self):
      if self.onInit == True: # esco se sono in fase di inizializzazione
         return 
      self.accept_symbols_tab()
      self.previewDim.drawDim(self.dimStyle)

   def block1NameChanged(self, value):
      self.redrawDimOnSymbolsTabChanged()

   def block2NameChanged(self, value):
      self.redrawDimOnSymbolsTabChanged()

   def blockLeaderNameChanged(self, value):
      self.redrawDimOnSymbolsTabChanged()

   def blockScaleNameChanged(self, value):
      self.redrawDimOnSymbolsTabChanged()

   def blockWidthChanged(self, value):
      self.redrawDimOnSymbolsTabChanged()

   def blockScaleChanged(self, value):
      self.redrawDimOnSymbolsTabChanged()

   
   ####################################################################
   # Inizializzazione del TAB che riguarda i simboli di quotatura - fine
   # Inizializzazione del TAB che riguarda i testi di quotatura - inizio
   ####################################################################

   def init_text_tab(self):
      self.onInit = True 
      index = self.textFont.findText(self.dimStyle.textFont)
      self.textFont.setCurrentIndex(index)
      self.textColor.setColor(QColor(self.dimStyle.textColor))
      self.textHeight.setValue(self.dimStyle.textHeight)
      
      # textVerticalPos
      self.textVerticalPos.addItem(QadMsg.translate("DimStyle_Details_Dialog", "Centered"))
      self.textVerticalPos.addItem(QadMsg.translate("DimStyle_Details_Dialog", "Above"))
      self.textVerticalPos.addItem(QadMsg.translate("DimStyle_Details_Dialog", "Outside"))
      self.textVerticalPos.addItem(QadMsg.translate("DimStyle_Details_Dialog", "Below"))
      if self.dimStyle.textVerticalPos == QadDimStyleTxtVerticalPosEnum.CENTERED_LINE:
         self.textVerticalPos.setCurrentIndex(0)
      elif self.dimStyle.textVerticalPos == QadDimStyleTxtVerticalPosEnum.ABOVE_LINE:
         self.textVerticalPos.setCurrentIndex(1)
      elif self.dimStyle.textVerticalPos == QadDimStyleTxtVerticalPosEnum.EXTERN_LINE:
         self.textVerticalPos.setCurrentIndex(2)
      elif self.dimStyle.textVerticalPos == QadDimStyleTxtVerticalPosEnum.BELOW_LINE:
         self.textVerticalPos.setCurrentIndex(3)
   
      # textHorizontalPos
      self.textHorizontalPos.addItem(QadMsg.translate("DimStyle_Details_Dialog", "Centered"))
      self.textHorizontalPos.addItem(QadMsg.translate("DimStyle_Details_Dialog", "At Ext Line 1"))
      self.textHorizontalPos.addItem(QadMsg.translate("DimStyle_Details_Dialog", "At Ext Line 2"))
      self.textHorizontalPos.addItem(QadMsg.translate("DimStyle_Details_Dialog", "Over Ext Line 1"))
      self.textHorizontalPos.addItem(QadMsg.translate("DimStyle_Details_Dialog", "Over Ext Line 2"))
      if self.dimStyle.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.CENTERED_LINE:
         self.textHorizontalPos.setCurrentIndex(0)
      elif self.dimStyle.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE:
         self.textHorizontalPos.setCurrentIndex(1)
      elif self.dimStyle.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.SECOND_EXT_LINE:
         self.textHorizontalPos.setCurrentIndex(2)         
      elif self.dimStyle.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.FIRST_EXT_LINE_UP:
         self.textHorizontalPos.setCurrentIndex(3)         
      elif self.dimStyle.textHorizontalPos == QadDimStyleTxtHorizontalPosEnum.SECOND_EXT_LINE_UP:
         self.textHorizontalPos.setCurrentIndex(4)         
      
      # textDirection
      self.textDirection.addItem(QadMsg.translate("DimStyle_Details_Dialog", "Left-to-Right"))
      self.textDirection.addItem(QadMsg.translate("DimStyle_Details_Dialog", "Right-to-Left"))
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
      self.onInit = False 

   def accept_text_tab(self):
      self.dimStyle.textFont = self.textFont.currentText()
      self.dimStyle.textColor = self.textColor.color().name()
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

   def redrawDimOnTextTabChanged(self):
      if self.onInit == True: # esco se sono in fase di inizializzazione
         return 
      self.accept_text_tab()
      self.previewDim.drawDim(self.dimStyle)


   def textColorChanged(self, value):
      self.redrawDimOnTextTabChanged()

   def textDirectionChanged(self, value):
      self.redrawDimOnTextTabChanged()

   def textFontChanged(self, value):
      self.redrawDimOnTextTabChanged()

   def textForcedRotChanged(self, value):
      self.redrawDimOnTextTabChanged()

   def textHeightChanged(self, value):
      self.redrawDimOnTextTabChanged()

   def textHorizontalPosChanged(self, value):
      self.redrawDimOnTextTabChanged()

   def textOffsetDistChanged(self, value):
      self.redrawDimOnTextTabChanged()

   def textRotModeHorizontalToggled(self, value):
      self.redrawDimOnTextTabChanged()

   def textRotModeAlignedToggled(self, value):
      self.redrawDimOnTextTabChanged()

   def textRotModeISOToggled(self, value):
      self.redrawDimOnTextTabChanged()

   def textRotModeFixedRotToggled(self, value):
      self.textForcedRot.setEnabled(value)
      self.redrawDimOnTextTabChanged()

   def textVerticalPosChanged(self, value):
      self.redrawDimOnTextTabChanged()


   ####################################################################
   # Inizializzazione del TAB che riguarda i testi di quotatura - fine
   # Inizializzazione del TAB che riguarda l'adattamento dei componenti di quotatura - inizio
   ####################################################################

   def init_adjust_tab(self):
      self.onInit = True 
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
      self.onInit = False 

   def accept_adjust_tab(self):
      if self.textBlockAdjustWhicheverFitsBestOutside.isChecked():
         self.dimStyle.textBlockAdjust = QadDimStyleTextBlocksAdjustEnum.WHICHEVER_FITS_BEST
      elif self.textBlockAdjustFirstSymbolOutside.isChecked():
         self.dimStyle.textBlockAdjust = QadDimStyleTextBlocksAdjustEnum.FIRST_BLOCKS_THEN_TEXT
      elif self.textBlockAdjustFirstTextOutside.isChecked():
         self.dimStyle.textBlockAdjust = QadDimStyleTextBlocksAdjustEnum.FIRST_TEXT_THEN_BLOCKS
      elif self.textBlockAdjustBothOutside.isChecked():
         self.dimStyle.textBlockAdjust = QadDimStyleTextBlocksAdjustEnum.BOTH_OUTSIDE_EXT_LINES

      self.dimStyle.blockSuppressionForNoSpace = self.blockSuppressionForNoSpace.isChecked()

   def redrawDimOnAdjustTabChanged(self):
      if self.onInit == True: # esco se sono in fase di inizializzazione
         return 
      self.accept_adjust_tab()
      self.previewDim.drawDim(self.dimStyle)

   def blockSuppressionForNoSpaceToggled(self, value):
      self.redrawDimOnAdjustTabChanged()
      
   def textBlockAdjustWhicheverFitsBestOutsideToggled(self, value):
      self.redrawDimOnAdjustTabChanged()

   def textBlockAdjustFirstSymbolOutsideToggled(self, value):
      self.redrawDimOnAdjustTabChanged()

   def textBlockAdjustFirstTextOutsideToggled(self, value):
      self.redrawDimOnAdjustTabChanged()

   def textBlockAdjustBothOutsideToggled(self, value):
      self.redrawDimOnAdjustTabChanged()


   ####################################################################
   # Inizializzazione del TAB che riguarda l'adattamento dei componenti di quotatura - fine
   # Inizializzazione del TAB che riguarda le unità primarie di quotatura - inizio
   ####################################################################

   def init_primaryUnits_tab(self):
      self.onInit = True 
      # textDecimals
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Details_Dialog", "0"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Details_Dialog", "0.0"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Details_Dialog", "0.00"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Details_Dialog", "0.000"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Details_Dialog", "0.0000"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Details_Dialog", "0.00000"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Details_Dialog", "0.000000"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Details_Dialog", "0.0000000"))
      self.textDecimals.addItem(QadMsg.translate("DimStyle_Details_Dialog", "0.00000000"))
      self.textDecimals.setCurrentIndex(self.dimStyle.textDecimals)
      
      # textDecimalSep
      self.textDecimalSep.addItem(QadMsg.translate("DimStyle_Details_Dialog", "'.' Period"))
      self.textDecimalSep.addItem(QadMsg.translate("DimStyle_Details_Dialog", "',' Comma"))
      self.textDecimalSep.addItem(QadMsg.translate("DimStyle_Details_Dialog", "' ' Space"))
      if self.dimStyle.textDecimalSep == ".": # punto
         self.textDecimalSep.setCurrentIndex(0)
      elif self.dimStyle.textDecimalSep == ",": # virgola
         self.textDecimalSep.setCurrentIndex(1)
      elif self.dimStyle.textDecimalSep == " ": # spazio
         self.textDecimalSep.setCurrentIndex(2)
      
      self.textPrefix.setText(self.dimStyle.textPrefix)
      self.textSuffix.setText(self.dimStyle.textSuffix)
      
      self.textSuppressLeadingZeros.setChecked(self.dimStyle.textSuppressLeadingZeros)
      self.textDecimalZerosSuppression.setChecked(self.dimStyle.textDecimalZerosSuppression)
      self.onInit = False 

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
      self.dimStyle.textDecimalZerosSuppression = self.textDecimalZerosSuppression.isChecked()

   def redrawDimOnPrimaryUnitsTabChanged(self):
      if self.onInit == True: # esco se sono in fase di inizializzazione
         return 
      self.accept_primaryUnits_tab()
      self.previewDim.drawDim(self.dimStyle)

   def textDecimalsChanged(self, index):
      self.redrawDimOnPrimaryUnitsTabChanged()

   def textDecimalSepChanged(self, index):
      self.redrawDimOnPrimaryUnitsTabChanged()

   def textDecimalZerosSuppressionToggled(self, value):
      self.redrawDimOnPrimaryUnitsTabChanged()

   def textPrefixChanged(self, value):
      self.redrawDimOnPrimaryUnitsTabChanged()

   def textSuffixChanged(self, value):
      self.redrawDimOnPrimaryUnitsTabChanged()

   def textSuppressLeadingZerosToggled(self, value):
      self.redrawDimOnPrimaryUnitsTabChanged()


   ####################################################################
   # Inizializzazione del TAB che riguarda le unità primarie di quotatura - fine
   ####################################################################

   def ButtonHELP_Pressed(self):
      qadShowPluginHelp(QadMsg.translate("Help", "Dimensioning"))

   def accept(self):
      self.accept_db_tab()
      self.accept_lines_tab()
      self.accept_symbols_tab()
      self.accept_text_tab()
      self.accept_adjust_tab()
      self.accept_primaryUnits_tab()
      errMsg = self.dimStyle.getInValidErrMsg()
      if errMsg is not None:
         errMsg += QadMsg.translate("DimStyle_Details_Dialog", "\nDo you want to accepts these settings ?")
         res = QMessageBox.question(self, QadMsg.translate("QAD", "QAD"), errMsg, \
                                 QMessageBox.Yes | QMessageBox.No)
         if res == QMessageBox.No:
            return
      QDialog.accept(self)
      
      
#######################################################################################
# Classe che gestisce il widget per visualizzare il preview della quota
class QadPreviewDim(QgsMapCanvas):

   def __init__(self, parent, plugIn):
      QgsMapCanvas.__init__(self, parent)
      self.plugIn = plugIn
      self.setAttribute(Qt.WA_DeleteOnClose)

      self.iface = self.plugIn.iface
      self.layerId2canvasLayer = {}
      self.canvasLayers = []

      self.setupUi()
      self.bookmark = False
      self.dimStyle = None
            

   def __del__(self):
      self.eraseDim()

 
   def setupUi(self):
      self.setObjectName("QadPreviewCanvas")

      settings = QSettings()
      red = settings.value("/qgis/default_canvas_color_red", 255, type=int)
      green = settings.value("/qgis/default_canvas_color_green", 255, type=int)
      blue = settings.value("/qgis/default_canvas_color_blue", 255, type=int)
      self.setCanvasColor(QColor(red, green, blue))
      self.enableAntiAliasing( settings.value( "/qgis/enable_anti_aliasing", False, type=bool ))
      self.useImageToRender( settings.value( "/qgis/use_qimage_to_render", False, type=bool ))
      action = settings.value( "/qgis/wheel_action", 0, type=int)
      zoomFactor = settings.value( "/qgis/zoom_factor", 2.0, type=float )
      self.setWheelAction( QgsMapCanvas.WheelAction(action), zoomFactor )

      self.onExtentsChanged()
      self.onCrsChanged()
      self.onCrsTransformEnabled( self.iface.mapCanvas().hasCrsTransformEnabled() )

   def onExtentsChanged(self):
      prevFlag = self.renderFlag()
      self.setRenderFlag(False)

      self.setExtent(self.iface.mapCanvas().extent())
 
      self.setRenderFlag( prevFlag )

   def onCrsChanged(self):
      prevFlag = self.renderFlag()
      self.setRenderFlag( False )

      renderer = self.iface.mapCanvas().mapRenderer()
      self._setRendererCrs( self.mapRenderer(), self._rendererCrs(renderer) )
      self.mapRenderer().setMapUnits( renderer.mapUnits() )

      self.setRenderFlag( prevFlag )

   def onCrsTransformEnabled(self, enabled):
      prevFlag = self.renderFlag()
      self.setRenderFlag( False )

      self.mapRenderer().setProjectionsEnabled( enabled )

      self.setRenderFlag( prevFlag )


   def getLayerSet(self):
      return map(lambda x: self._layerId(x.layer()), self.canvasLayers)

   def setLayerSet(self, layerIds=None):
      prevFlag = self.renderFlag()
      self.setRenderFlag( False )

      if layerIds == None:
         self.layerId2canvasLayer = {}
         self.canvasLayers = []
         QgsMapCanvas.setLayerSet(self, [])

      else:
         for lid in layerIds:
            self.addLayer( lid )

      self.onExtentsChanged()
      self.setRenderFlag( prevFlag )


   def addLayer(self, layerId=None):
      if layerId == None:
         layer = self.iface.activeLayer()
      else:
         layer = QgsMapLayerRegistry.instance().mapLayer( layerId )

      if layer == None:
         return

      prevFlag = self.renderFlag()
      self.setRenderFlag( False )
      
      # add the layer to the map canvas layer set
      self.canvasLayers = []
      id2cl_dict = {}
      for l in self.iface.legendInterface().layers():
         lid = self._layerId(l)
         if self.layerId2canvasLayer.has_key( lid ):   # previously added
            cl = self.layerId2canvasLayer[ lid ]
         elif l == layer:   # selected layer
            cl = QgsMapCanvasLayer( layer )
         else:
            continue

         id2cl_dict[ lid ] = cl
         self.canvasLayers.append( cl )

      self.layerId2canvasLayer = id2cl_dict
      QgsMapCanvas.setLayerSet(self, self.canvasLayers )

      self.onExtentsChanged()
      self.setRenderFlag( prevFlag )

   def delLayer(self, layerId=None):
      if layerId == None:
         layer = self.iface.activeLayer()
         if layer == None:
            return
         layerId = self._layerId(layer)

      # remove the layer from the map canvas layer set
      if not self.layerId2canvasLayer.has_key( layerId ):
         return

      prevFlag = self.renderFlag()
      self.setRenderFlag( False )

      cl = self.layerId2canvasLayer[ layerId ]
      del self.layerId2canvasLayer[ layerId ]
      self.canvasLayers.remove( cl )
      QgsMapCanvas.setLayerSet(self, self.canvasLayers )
      del cl

      self.onExtentsChanged()
      self.setRenderFlag( prevFlag )


   def _layerId(self, layer):
      if hasattr(layer, 'id'):
         return layer.id()
      return layer.getLayerID() 

   def _rendererCrs(self, renderer):
      if hasattr(renderer, 'destinationCrs'):
         return renderer.destinationCrs()
      return renderer.destinationSrs()

   def _setRendererCrs(self, renderer, crs):
      if hasattr(renderer, 'setDestinationCrs'):
         return renderer.setDestinationCrs( crs )
      return renderer.setDestinationSrs( crs )

   def zoomOnRect(self, zoomRect):
      mapSettings = self.mapSettings()
      canvasSize = mapSettings.outputSize()
      sfx = zoomRect.width() / canvasSize.width()
      sfy = zoomRect.height() / canvasSize.height()
      sf = max(sfx, sfy)

      prevFlag = self.renderFlag()
      self.setRenderFlag(False)

      self.setExtent(zoomRect)
      self.setCenter(zoomRect.center())

      self.setRenderFlag( prevFlag )
      
   def drawDim(self, dimStyle):
      if dimStyle is None:
         return

      self.dimStyle = dimStyle
      self.eraseDim()
         
      if self.plugIn.insertBookmark() == True:
         self.bookmark = True

      for layerId in self.getLayerSet(): # tolgo tutti i layer
         self.delLayer(layerId)
      # inserisco i layer della quotatura
      self.isEditableTextualLayer = None
      layer = self.dimStyle.getTextualLayer()
      if layer is not None:
         self.isEditableTextualLayer = layer.isEditable()
         if self.isEditableTextualLayer == False:
            layer.startEditing()
         self.addLayer(layer.id())
         
      self.isEditableSymbolLayer = None
      layer = self.dimStyle.getSymbolLayer()
      if layer is not None:
         self.isEditableSymbolLayer = layer.isEditable()
         if self.isEditableSymbolLayer == False:
            layer.startEditing()
         self.addLayer(layer.id())
         
      self.isEditableLinearLayer = None
      layer = self.dimStyle.getLinearLayer()
      if layer is not None:
         self.isEditableLinearLayer = layer.isEditable()
         if self.isEditableLinearLayer == False:
            layer.startEditing()
         self.addLayer(layer.id())

      if self.dimStyle.getInValidErrMsg() is not None:
         return


      ###########################
      # quota lineare orizzontale
      dimPt1 = QgsPoint(0, 0)
      dimPt2 = QgsPoint(13.45, 0)
      linePosPt = QgsPoint(0, 10)
      
      # calcolo il rettangolo di occupazione della quota
      dimEntity, textOffsetRectGeom = self.dimStyle.getLinearDimFeatures(self.plugIn.canvas, \
                                                                         dimPt1, dimPt2, linePosPt)
      rect = textOffsetRectGeom.boundingBox()
      for g in dimEntity.getLinearGeometryCollection():
         rect.combineExtentWith(g.boundingBox())
      for g in dimEntity.getSymbolGeometryCollection():
         rect.combineExtentWith(g.boundingBox())
      
      self.dimStyle.addLinearDimToLayers(self.plugIn, dimPt1, dimPt2, linePosPt)
      
      ###########################
      # quota lineare verticale
      dimPt1 = QgsPoint(0, 0)
      dimPt2 = QgsPoint(0, -15.7)
      linePosPt = QgsPoint(-9, 0)
      
      # calcolo il rettangolo di occupazione della quota
      dimEntity, textOffsetRectGeom = self.dimStyle.getLinearDimFeatures(self.plugIn.canvas, \
                                                                         dimPt1, dimPt2, linePosPt, None, \
                                                                         QadDimStyleAlignmentEnum.VERTICAL)
      rect.combineExtentWith(textOffsetRectGeom.boundingBox())
      for g in dimEntity.getLinearGeometryCollection():
         rect.combineExtentWith(g.boundingBox())
      for g in dimEntity.getSymbolGeometryCollection():
         rect.combineExtentWith(g.boundingBox())
      
      self.dimStyle.addLinearDimToLayers(self.plugIn, dimPt1, dimPt2, linePosPt, None, \
                                         QadDimStyleAlignmentEnum.VERTICAL)

      ###########################
      # quota allineata obliqua
      dimPt1 = QgsPoint(13.45, 0)
      dimPt2 = QgsPoint(23, -20)
      linePosPt = QgsPoint(23, 0)
      
      # calcolo il rettangolo di occupazione della quota
      dimEntity, textOffsetRectGeom = self.dimStyle.getAlignedDimFeatures(self.plugIn.canvas, \
                                                                          dimPt1, dimPt2, linePosPt)
      rect.combineExtentWith(textOffsetRectGeom.boundingBox())
      for g in dimEntity.getLinearGeometryCollection():
         rect.combineExtentWith(g.boundingBox())
      for g in dimEntity.getSymbolGeometryCollection():
         rect.combineExtentWith(g.boundingBox())
      
      self.dimStyle.addAlignedDimToLayers(self.plugIn, dimPt1, dimPt2, linePosPt, None)

      self.zoomOnRect(rect)

   def eraseDim(self):
      if self.bookmark == True:
         self.plugIn.undoUntilBookmark()
         self.bookmark = False
      
      for layerId in self.getLayerSet(): # tolgo tutti i layer
         self.delLayer(layerId)
