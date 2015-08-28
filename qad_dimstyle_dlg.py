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

import qad_dimstyle_ui

from qad_variables import *
from qad_dim import *
from qad_msg import QadMsg
from qad_dimstyle_new_dlg import QadDIMSTYLE_NEW_Dialog
from qad_dimstyle_details_dlg import QadDIMSTYLE_DETAILS_Dialog, QadPreviewDim
from qad_dimstyle_diff_dlg import QadDIMSTYLE_DIFF_Dialog
import qad_utils


#######################################################################################
# Classe che gestisce l'interfaccia grafica del comando DIMSTYLE
class QadDIMSTYLEDialog(QDialog, QObject, qad_dimstyle_ui.Ui_DimStyle_Dialog):
   def __init__(self, plugIn):
      self.plugIn = plugIn
      self.iface = self.plugIn.iface.mainWindow()
      QDialog.__init__(self, self.iface)
      
      self.selectedDimStyle = None
      
      self.setupUi(self)
      self.dimStyleList.setContextMenuPolicy(Qt.CustomContextMenu)
      
      # aggiungo il canvans di preview della quota chiamato QadPreviewDim 
      # che eredita la posizione di previewDummy (che viene nascosto)      
      self.previewDummy.setHidden(True)
      self.previewDim = QadPreviewDim(self.previewDummy.parent(), self.plugIn)
      self.previewDim.setGeometry(self.previewDummy.geometry())
      self.previewDim.setObjectName("previewDim")
      
      self.init()


   def closeEvent(self, event):
      del self.previewDim # cancello il canvans di preview della quota chiamato QadPreviewDim 
      return QDialog.closeEvent(self, event)

   def init(self):
      # Inizializzazione dello stile corrente
      currDimStyleName = QadVariables.get(QadMsg.translate("Environment variables", "DIMSTYLE"))
      self.currentDimStyle.setText("" if currDimStyleName is None else currDimStyleName)
      
      # Inizializzazione della lista degli stili
      model = QStandardItemModel(self.dimStyleList)      
      for dimStyle in self.plugIn.dimStyles.dimStyleList: # lista degli stili di quotatura caricati
         # Create an item with a caption
         item = QStandardItem(dimStyle.name)
         item.setEditable(True)
         item.setData(dimStyle)
         model.appendRow(item)

      self.dimStyleList.setModel(model)
      # sort
      self.dimStyleList.model().sort(0)
      # collego l'evento "cambio di selezione" alla funzione dimStyleListCurrentChanged
      self.dimStyleList.selectionModel().selectionChanged.connect(self.dimStyleListCurrentChanged)
      
      self.dimStyleList.itemDelegate().closeEditor.connect(self.dimStyleListcloseEditor)
      
      # seleziono il primo elemento della lista
      index = self.dimStyleList.model().index(0,0)
      if self.selectedDimStyle is not None:
         # seleziono l'elemento precedentemente selezionato
         item = self.dimStyleList.model().findItems(self.selectedDimStyle.name)[0]
         index = self.dimStyleList.model().indexFromItem(item)
      elif len(currDimStyleName) > 0:
         item = self.dimStyleList.model().findItems(currDimStyleName)[0]
         if item is not None:
            index = self.dimStyleList.model().indexFromItem(item)
         
      self.dimStyleList.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectCurrent)
      
   def dimStyleListCurrentChanged(self, current, previous):
      # leggo l'elemento selezionato
      index = current.indexes()[0]
      item = self.dimStyleList.model().itemFromIndex(index)
      self.selectedDimStyle = item.data()
      self.selectedStyle.setText(self.selectedDimStyle.name)
      self.descriptionSelectedStyle.setText(self.selectedDimStyle.description)
      
      self.previewDim.drawDim(self.selectedDimStyle)

   def dimStyleListcloseEditor(self, editor, hint):
      self.renSelectedDimStyle(editor.text())

   def setCurrentStyle(self):
      if self.selectedDimStyle is None:
         return
      QadVariables.set(QadMsg.translate("Environment variables", "DIMSTYLE"), self.selectedDimStyle.name)
      QadVariables.save()
      self.currentDimStyle.setText(self.selectedDimStyle.name)

   def renSelectedDimStyle(self, newName):
      if self.selectedDimStyle is None:
         return
      if self.plugIn.dimStyles.renameDimStyle(self.selectedDimStyle.name, newName) == False:
         QMessageBox.critical(self, QadMsg.translate("QAD", "QAD"), \
                              QadMsg.translate("DimStyle_Dialog", "Lo stile di quotatura non è stato rinominato."))
      else:
         self.init()

   def updDescrSelectedDimStyle(self):
      if self.selectedDimStyle is None:
         return
      Title = QadMsg.translate("DimStyle_Dialog", "QAD - Modifica descrizione per lo stile di quota: ") + self.selectedDimStyle.name
      inputDlg = QInputDialog(self)
      inputDlg.setWindowTitle(Title)                 
      inputDlg.setInputMode(QInputDialog.TextInput) 
      inputDlg.setLabelText(QadMsg.translate("DimStyle_Dialog", "Nuova descrizione:"))
      inputDlg.setTextValue(self.selectedDimStyle.description)
      inputDlg.resize(600,100)                             
      if inputDlg.exec_():                         
         self.selectedDimStyle.description = inputDlg.textValue()      
         self.selectedDimStyle.save()
         self.init()
         
   def delSelectedDimStyle(self):
      if self.selectedDimStyle is None:
         return
      res = QMessageBox.question(self, QadMsg.translate("QAD", "QAD"), \
                                 QadMsg.translate("DimStyle_Dialog", "Eliminare lo stile di quotatura ") + self.selectedDimStyle.name + " ?", \
                                 QMessageBox.Yes | QMessageBox.No)
      if res == QMessageBox.Yes:
         if self.plugIn.dimStyles.removeDimStyle(self.selectedDimStyle.name, True) == False:
            QMessageBox.critical(self, QadMsg.translate("QAD", "QAD"), \
                                 QadMsg.translate("DimStyle_Dialog", "Lo stile di quotatura non è stato cancellato."))
         else:
            self.selectedDimStyle = None
            self.init()

   def createNewStyle(self):
      self.previewDim.eraseDim()

      Form = QadDIMSTYLE_NEW_Dialog(self.plugIn, self.selectedDimStyle.name if self.selectedDimStyle is not None else None)
      if Form.exec_() == QDialog.Accepted:
         Form.dimStyle.path = ""
         self.plugIn.dimStyles.addDimStyle(Form.dimStyle, True)
         self.selectedDimStyle = self.plugIn.dimStyles.findDimStyle(Form.dimStyle.name)
         # setto lo stile corrente
         QadVariables.set(QadMsg.translate("Environment variables", "DIMSTYLE"), self.selectedDimStyle.name)
         self.init()      
      
      self.previewDim.drawDim(self.selectedDimStyle)

   def modStyle(self):
      if self.selectedDimStyle is None:
         return
      self.previewDim.eraseDim()
      
      Form = QadDIMSTYLE_DETAILS_Dialog(self.plugIn, self.selectedDimStyle)
      title = QadMsg.translate("DimStyle_Dialog", "Modifica stile di quota: ") + self.selectedDimStyle.name
      Form.setWindowTitle(title)
      if Form.exec_() == QDialog.Accepted:
         self.selectedDimStyle.set(Form.dimStyle)
         self.selectedDimStyle.save()
         self.init()
      del Form # forzo la chiamata al distruttore per rimuovere il preview della quota
      
      self.previewDim.drawDim(self.selectedDimStyle)


   def temporaryModStyle(self):
      if self.selectedDimStyle is None:
         return
      self.previewDim.eraseDim()

      Form = QadDIMSTYLE_DETAILS_Dialog(self.plugIn, self.selectedDimStyle)
      title = QadMsg.translate("DimStyle_Dialog", "Modifica locale allo stile corrente: ") + self.selectedDimStyle.name
      Form.setWindowTitle(title)
      if Form.exec_() == QDialog.Accepted:
         self.selectedDimStyle.set(Form.dimStyle)
         self.init()
         
      self.previewDim.drawDim(self.selectedDimStyle)


   def showDiffBetweenStyles(self):
      Form = QadDIMSTYLE_DIFF_Dialog(self.plugIn, self.selectedDimStyle.name)
      Form.exec_()

   def startEditingItem(self):
      if self.selectedDimStyle is None:
         return
      item = self.dimStyleList.model().findItems(self.selectedDimStyle.name)[0]
      index = self.dimStyleList.model().indexFromItem(item)
      self.dimStyleList.edit(index)
            
   def ButtonBOX_Accepted(self):     
      self.close()
      return True


   def ButtonHELP_Pressed(self):
      # per conoscere la sezione/pagina del file html usare internet explorer,
      # selezionare nella finestra di destra la voce di interesse e leggerne l'indirizzo dalla casella in alto.
      # Questo perché internet explorer inserisce tutti i caratteri di spaziatura e tab che gli altri browser non fanno.
      qad_utils.qadShowPluginHelp("7%C2%A0%C2%A0%C2%A0%C2%A0%C2%A0%20%C2%A0GESTIONE%20DEI%20PROGETTI")

   #============================================================================
   # displayPopupMenu
   #============================================================================
   def displayPopupMenu(self, pos):
      if self.selectedDimStyle is None:
         return
      
      popupMenu = QMenu(self)
      action = QAction(QadMsg.translate("DimStyle_Dialog", "Imposta corrente"), popupMenu)
      popupMenu.addAction(action)
      QObject.connect(action, SIGNAL("triggered()"), self.setCurrentStyle)

      action = QAction(QadMsg.translate("DimStyle_Dialog", "Rinomina"), popupMenu)
      popupMenu.addAction(action)
      QObject.connect(action, SIGNAL("triggered()"), self.startEditingItem)

      action = QAction(QadMsg.translate("DimStyle_Dialog", "Modifica descrizione"), popupMenu)
      popupMenu.addAction(action)
      QObject.connect(action, SIGNAL("triggered()"), self.updDescrSelectedDimStyle)

      action = QAction(QadMsg.translate("DimStyle_Dialog", "Elimina"), popupMenu)
      currDimStyleName = QadVariables.get(QadMsg.translate("Environment variables", "DIMSTYLE"))
      if self.selectedDimStyle.name == currDimStyleName:
         action.setDisabled(True)
      popupMenu.addAction(action)
      QObject.connect(action, SIGNAL("triggered()"), self.delSelectedDimStyle)

      popupMenu.popup(self.dimStyleList.mapToGlobal(pos))

      