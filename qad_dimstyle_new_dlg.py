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

import qad_dimstyle_new_ui
from qad_dimstyle_details_dlg import QadDIMSTYLE_DETAILS_Dialog

from qad_variables import *
from qad_dim import *
from qad_msg import QadMsg
import qad_utils


#######################################################################################
# Classe che gestisce l'interfaccia grafica della funzione di creazione nuovo stile
class QadDIMSTYLE_NEW_Dialog(QDialog, QObject, qad_dimstyle_new_ui.Ui_Dialog):
   def __init__(self, plugIn, fromDimStyleName = None):
      self.plugIn = plugIn
      self.iface = self.plugIn.iface.mainWindow()
      QDialog.__init__(self, self.iface)
      
      self.newDimStyle = QadDimStyle()
      self.newDimStyleNameChanged = False
      
      self.setupUi(self)
                 
      self.dimNameList = []
      for dimStyle in self.plugIn.dimStyles.dimStyleList: # lista degli stili di quotatura caricati
         self.DimStyleNameFrom.addItem(dimStyle.name, dimStyle)
         self.dimNameList.append(dimStyle.name)
      
      # sort
      self.DimStyleNameFrom.model().sort(0)

      # seleziono un elemento della lista
      if fromDimStyleName is not None:
         index = self.DimStyleNameFrom.findText(fromDimStyleName)
         self.DimStyleNameFrom.setCurrentIndex(index)
         self.DimStyleNameFromChanged(index)
      
   def DimStyleNameFromChanged(self, index):
      # leggo l'elemento selezionato
      dimStyle = self.DimStyleNameFrom.itemData(index)
      if dimStyle is not None:
         self.newDimStyle.set(dimStyle)
         if self.newDimStyleNameChanged == False:
            newName = qad_utils.checkUniqueNewName(dimStyle.name, self.dimNameList, QadMsg.translate("QAD", "Copia di "))
            if newName is not None:
               self.newDimStyleName.setText(newName)

   def newStyleNameChanged(self, text):
      self.newDimStyleNameChanged = True
         
   def ButtonBOX_continue(self):
      if self.newDimStyleName.text() in self.dimNameList:
         QMessageBox.critical(self, QadMsg.translate("QAD", "QAD"), \
                              QadMsg.translate("DimStyle_Dialog", "Nome dello stile di quotatura già esistente. Specificare un altro nome."))
         return False
      self.newDimStyle.name = self.newDimStyleName.text()
      self.newDimStyle.description = self.newDimStyleDescr.text()
      Form = QadDIMSTYLE_DETAILS_Dialog(self.plugIn, self.newDimStyle)
      title = QadMsg.translate("DimStyle_Dialog", "Nuovo stile di quota: ") + self.newDimStyle.name
      Form.setWindowTitle(title)
      
      if Form.exec_() == QDialog.Accepted:
         self.dimStyle = Form.dimStyle
         QDialog.accept(self)
      else:
         self.dimStyle = None
         QDialog.reject(self)      

   def ButtonHELP_Pressed(self):
      # per conoscere la sezione/pagina del file html usare internet explorer,
      # selezionare nella finestra di destra la voce di interesse e leggerne l'indirizzo dalla casella in alto.
      # Questo perché internet explorer inserisce tutti i caratteri di spaziatura e tab che gli altri browser non fanno.
      qad_utils.qadShowPluginHelp("7%C2%A0%C2%A0%C2%A0%C2%A0%C2%A0%20%C2%A0GESTIONE%20DEI%20PROGETTI")
