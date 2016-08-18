# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando DSETTINGS per impostazione disegno
 
                              -------------------
        begin                : 2013-05-22
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


import qad_dsettings_ui


from qad_variables import *
from qad_snapper import *
from qad_msg import QadMsg, qadShowPluginHelp
import qad_utils


#===============================================================================
# QadDSETTINGSTabIndexEnum class.
#===============================================================================
class QadDSETTINGSTabIndexEnum():
   OBJECT_SNAP    = 0
   POLAR_TRACKING = 1


#######################################################################################
# Classe che gestisce l'interfaccia grafica del comando DSETTINGS
class QadDSETTINGSDialog(QDialog, QObject, qad_dsettings_ui.Ui_DSettings_Dialog):
   def __init__(self, plugIn, dsettingsTabIndex = None):
      self.plugIn = plugIn
      self.iface = self.plugIn.iface.mainWindow()

      QDialog.__init__(self)
      # non passo il parent perchè altrimenti il font e la sua dimensione verrebbero ereditati dalla dialog scombinando tutto 
      #QDialog.__init__(self, self.iface)

      self.setupUi(self)
      
      # Inizializzazione del TAB che riguarda gli SNAP ad oggetto
      self.init_osnap_tab()
      
      # Inizializzazione del TAB che riguarda il puntamento polare
      self.init_polar_tab()
      
      if dsettingsTabIndex is not None:
         self.tabWidget.setCurrentIndex(dsettingsTabIndex)
      else:
         if self.plugIn.dsettingsLastUsedTabIndex == -1: # non inizializzato
            self.plugIn.dsettingsLastUsedTabIndex = QadDSETTINGSTabIndexEnum.OBJECT_SNAP
         self.tabWidget.setCurrentIndex(self.plugIn.dsettingsLastUsedTabIndex)
            

   ######################################
   # TAB che riguarda gli SNAP ad oggetto
   def init_osnap_tab(self):
      # Inizializzazione del TAB che riguarda gli SNAP ad oggetto
      
      # Memorizzo il valore dell'OSMODE per determinare gli osnap impostati
      OsMode = QadVariables.get(QadMsg.translate("Environment variables", "OSMODE"))
      self.checkBox_CENP.setChecked(OsMode & QadSnapTypeEnum.CEN)
      self.checkBox_ENDP.setChecked(OsMode & QadSnapTypeEnum.END)
      self.checkBox_END_PLINE.setChecked(OsMode & QadSnapTypeEnum.END_PLINE)
      self.checkBox_EXTP.setChecked(OsMode & QadSnapTypeEnum.EXT)
      self.checkBox_INTP.setChecked(OsMode & QadSnapTypeEnum.INT)
      self.checkBox_MIDP.setChecked(OsMode & QadSnapTypeEnum.MID)
      self.checkBox_NODP.setChecked(OsMode & QadSnapTypeEnum.NOD)
      self.checkBox_QUADP.setChecked(OsMode & QadSnapTypeEnum.QUA)
      #self.checkBox_INSP.setChecked(OsMode & QadSnapTypeEnum.INS)
      #self.checkBox_INTAPP.setChecked(OsMode & QadSnapTypeEnum.APP)
      self.checkBox_NEARP.setChecked(OsMode & QadSnapTypeEnum.NEA)
      self.checkBox_PERP.setChecked(OsMode & QadSnapTypeEnum.PER)
      self.checkBox_PARALP.setChecked(OsMode & QadSnapTypeEnum.PAR)
      self.checkBox_PROGRESP.setChecked(OsMode & QadSnapTypeEnum.PR)
      self.checkBox_TANP.setChecked(OsMode & QadSnapTypeEnum.TAN)
      self.checkBox_EXT_INT.setChecked(OsMode & QadSnapTypeEnum.EXT_INT)
      self.checkBox_TANP.setChecked(OsMode & QadSnapTypeEnum.TAN)
      
      self.checkBox_IsOsnapON.setChecked(not(OsMode & QadSnapTypeEnum.DISABLE))

      AutoSnap = QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAP"))
      self.checkBox_ObjectSnapTracking.setChecked(AutoSnap & QadAUTOSNAPEnum.OBJ_SNAP_TRACKING)

      ProgrDistance = QadVariables.get(QadMsg.translate("Environment variables", "OSPROGRDISTANCE"))
      stringA = str(ProgrDistance)
      self.lineEdit_ProgrDistance.setText(stringA)
      self.lineEdit_ProgrDistance.setValidator(QDoubleValidator(self.lineEdit_ProgrDistance))
      self.lineEdit_ProgrDistance.installEventFilter(self)
      

   def accept_osnap_tab(self):
      # Memorizzo il valore di OSMODE
      newOSMODE = 0
      if self.checkBox_CENP.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.CEN
      if self.checkBox_ENDP.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.END
      if self.checkBox_END_PLINE.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.END_PLINE
      if self.checkBox_EXTP.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.EXT
      if self.checkBox_INTP.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.INT
      if self.checkBox_MIDP.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.MID
      if self.checkBox_NODP.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.NOD
      if self.checkBox_QUADP.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.QUA
      #if self.checkBox_INSP.checkState() == Qt.Checked:
      #   newOSMODE = newOSMODE | QadSnapTypeEnum.INS
      #if self.checkBox_INTAPP.checkState() == Qt.Checked:
      #   newOSMODE = newOSMODE | QadSnapTypeEnum.APP
      if self.checkBox_NEARP.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.NEA
      if self.checkBox_PARALP.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.PAR
      if self.checkBox_PERP.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.PER
      if self.checkBox_PROGRESP.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.PR
      if self.checkBox_TANP.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.TAN
      if self.checkBox_EXT_INT.checkState() == Qt.Checked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.EXT_INT
      if self.checkBox_IsOsnapON.checkState() == Qt.Unchecked:
         newOSMODE = newOSMODE | QadSnapTypeEnum.DISABLE
      QadVariables.set(QadMsg.translate("Environment variables", "OSMODE"), newOSMODE)

      # Memorizzo il valore di OSPROGRDISTANCE
      SProgrDist = self.lineEdit_ProgrDistance.text()
      ProgrDist = qad_utils.str2float(SProgrDist)
      QadVariables.set(QadMsg.translate("Environment variables", "OSPROGRDISTANCE"), ProgrDist)
      
      # Memorizzo il valore di AUTOSNAP
      AutoSnap = QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAP"))      
      if self.checkBox_ObjectSnapTracking.checkState() == Qt.Checked:
         AutoSnap = AutoSnap | QadAUTOSNAPEnum.OBJ_SNAP_TRACKING
      elif AutoSnap & QadAUTOSNAPEnum.OBJ_SNAP_TRACKING:
         AutoSnap = AutoSnap - QadAUTOSNAPEnum.OBJ_SNAP_TRACKING
      QadVariables.set(QadMsg.translate("Environment variables", "AUTOSNAP"), AutoSnap)


   def ButtonSelectALL_Pressed(self):
      self.checkBox_CENP.setChecked(True)
      self.checkBox_ENDP.setChecked(True)
      self.checkBox_END_PLINE.setChecked(True)
      self.checkBox_EXTP.setChecked(True)
      self.checkBox_INTP.setChecked(True)
      self.checkBox_MIDP.setChecked(True)
      self.checkBox_NODP.setChecked(True)
      self.checkBox_QUADP.setChecked(True)
      #self.checkBox_INSP.setChecked(True)
      #self.checkBox_INTAPP.setChecked(True)
      self.checkBox_NEARP.setChecked(True)
      self.checkBox_PARALP.setChecked(True)
      self.checkBox_PERP.setChecked(True)
      self.checkBox_PROGRESP.setChecked(True)
      self.checkBox_TANP.setChecked(True)
      self.checkBox_EXT_INT.setChecked(True)
      return True
  

   def ButtonDeselectALL_Pressed(self):
      self.checkBox_CENP.setChecked(False)
      self.checkBox_ENDP.setChecked(False)
      self.checkBox_END_PLINE.setChecked(False)
      self.checkBox_EXTP.setChecked(False)
      self.checkBox_INTP.setChecked(False)
      self.checkBox_MIDP.setChecked(False)
      self.checkBox_NODP.setChecked(False)
      self.checkBox_QUADP.setChecked(False)
      #self.checkBox_INSP.setChecked(False)
      #self.checkBox_INTAPP.setChecked(False)
      self.checkBox_NEARP.setChecked(False)
      self.checkBox_PARALP.setChecked(False)
      self.checkBox_PERP.setChecked(False)
      self.checkBox_PROGRESP.setChecked(False)
      self.checkBox_TANP.setChecked(False)
      self.checkBox_EXT_INT.setChecked(False)
      return True


   def lineEdit_ProgrDistance_Validation(self):
      string = self.lineEdit_ProgrDistance.text()
      if qad_utils.str2float(string) is None or qad_utils.str2float(string) == 0:
         msg = QadMsg.translate("DSettings_Dialog", "Invalid progressive distance object snap: enter a number not zero.")
         QMessageBox.critical(self, "QAD", msg)
         self.lineEdit_ProgrDistance.setFocus()
         self.lineEdit_ProgrDistance.selectAll()
         return False
      return True


   ######################################
   # TAB che riguarda il puntamento polare
   def init_polar_tab(self):
      # Inizializzazione del TAB che riguarda il puntamento polare
      UserAngle = QadVariables.get(QadMsg.translate("Environment variables", "POLARANG"))
      angoliDef = ["90", "45", "30", "22.5", "18", "15", "10", "5"]
      self.comboBox_increment_angle.addItems(angoliDef)
      stringA = str(UserAngle)
      self.comboBox_increment_angle.lineEdit().setText(stringA)
      self.comboBox_increment_angle.installEventFilter(self)
      
      AutoSnap = QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAP"))
      self.checkBox_PolarPickPoint.setChecked(AutoSnap & QadAUTOSNAPEnum.POLAR_TRACKING)

      PolarMode = QadVariables.get(QadMsg.translate("Environment variables", "POLARMODE"))
      if PolarMode & QadPOLARMODEnum.POLAR_TRACKING:
         self.radioButton_OsnapPolarAngle.setChecked(True)
      else:
         self.radioButton_OsnapOrtho.setChecked(True)

      if PolarMode & QadPOLARMODEnum.MEASURE_RELATIVE_ANGLE:
         self.radioButton_OsnapPolarRelative.setChecked(True)
      else:
         self.radioButton_OsnapPolarAbolute.setChecked(True)


   def accept_polar_tab(self):
      # Memorizzo il valore di AUTOSNAP
      AutoSnap = QadVariables.get(QadMsg.translate("Environment variables", "AUTOSNAP"))
      if self.checkBox_PolarPickPoint.checkState() == Qt.Checked:
         AutoSnap = AutoSnap | QadAUTOSNAPEnum.POLAR_TRACKING
      elif AutoSnap & QadAUTOSNAPEnum.POLAR_TRACKING:
         AutoSnap = AutoSnap - QadAUTOSNAPEnum.POLAR_TRACKING
      QadVariables.set(QadMsg.translate("Environment variables", "AUTOSNAP"), AutoSnap)
      
      # Memorizzo il valore di POLARANG
      SUserAngle = self.comboBox_increment_angle.currentText()
      UserAngle = qad_utils.str2float(SUserAngle)
      QadVariables.set(QadMsg.translate("Environment variables", "POLARANG"), UserAngle)

      # Memorizzo il valore di POLARMODE
      PolarMode = 0
      if self.radioButton_OsnapPolarAngle.isChecked():
         PolarMode = PolarMode | QadPOLARMODEnum.POLAR_TRACKING
      if self.radioButton_OsnapPolarRelative.isChecked():
         PolarMode = PolarMode | QadPOLARMODEnum.MEASURE_RELATIVE_ANGLE
      QadVariables.set(QadMsg.translate("Environment variables", "POLARMODE"), PolarMode)
    
    
   def comboBox_increment_angle_Validation(self):
      string = self.comboBox_increment_angle.lineEdit().text()
      if qad_utils.str2float(string) is None or qad_utils.str2float(string) <= 0 or qad_utils.str2float(string) >= 360:
         msg = QadMsg.translate("DSettings_Dialog", "Invalid increment angle: enter a number greater than zero and less than 360 degree.")
         QMessageBox.critical(self, "QAD", msg) 
         self.comboBox_increment_angle.lineEdit().setFocus()
         self.comboBox_increment_angle.lineEdit().selectAll()
         return False
      return True


   ######################################
   # Funzioni generiche
   def eventFilter(self, obj, event):
      if event is not None:
         if event.type() == QEvent.FocusOut:
            if obj == self.lineEdit_ProgrDistance:
               return not self.lineEdit_ProgrDistance_Validation()
            elif obj == self.comboBox_increment_angle:
               return not self.comboBox_increment_angle_Validation()            

      # standard event processing
      return QObject.eventFilter(self, obj, event);


   def ButtonBOX_Accepted(self):
      self.accept_osnap_tab() # salvo i valori del tab "object snap"
      self.accept_polar_tab() # salvo i valori del tab "polar tracking"
      
      QadVariables.save()

      self.plugIn.dsettingsLastUsedTabIndex = self.tabWidget.currentIndex()
      
      self.close()
      return True


   def ButtonHELP_Pressed(self):
      qadShowPluginHelp(QadMsg.translate("Help", "DSETTINGS"))
