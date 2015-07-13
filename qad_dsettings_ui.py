# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qad_dsettings.ui'
#
# Created: Tue Jul 07 13:52:35 2015
#      by: PyQt4 UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_dSettings_dialog(object):
    def setupUi(self, dSettings_dialog):
        dSettings_dialog.setObjectName(_fromUtf8("dSettings_dialog"))
        dSettings_dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dSettings_dialog.resize(441, 455)
        dSettings_dialog.setMouseTracking(True)
        dSettings_dialog.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        dSettings_dialog.setModal(True)
        self.tabWidget = QtGui.QTabWidget(dSettings_dialog)
        self.tabWidget.setGeometry(QtCore.QRect(10, 10, 421, 401))
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab_1 = QtGui.QWidget()
        self.tab_1.setObjectName(_fromUtf8("tab_1"))
        self.groupBox = QtGui.QGroupBox(self.tab_1)
        self.groupBox.setGeometry(QtCore.QRect(10, 40, 391, 321))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.layoutWidget = QtGui.QWidget(self.groupBox)
        self.layoutWidget.setGeometry(QtCore.QRect(60, 290, 261, 25))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_2.setMargin(0)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.pushButton_SelectALL = QtGui.QPushButton(self.layoutWidget)
        self.pushButton_SelectALL.setObjectName(_fromUtf8("pushButton_SelectALL"))
        self.horizontalLayout_2.addWidget(self.pushButton_SelectALL)
        self.pushButton_DeSelectALL = QtGui.QPushButton(self.layoutWidget)
        self.pushButton_DeSelectALL.setObjectName(_fromUtf8("pushButton_DeSelectALL"))
        self.horizontalLayout_2.addWidget(self.pushButton_DeSelectALL)
        self.layoutWidget1 = QtGui.QWidget(self.groupBox)
        self.layoutWidget1.setGeometry(QtCore.QRect(190, 20, 181, 261))
        self.layoutWidget1.setObjectName(_fromUtf8("layoutWidget1"))
        self.gridLayout = QtGui.QGridLayout(self.layoutWidget1)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_5 = QtGui.QLabel(self.layoutWidget1)
        self.label_5.setText(_fromUtf8(""))
        self.label_5.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_EXTP.png")))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 3, 0, 1, 1)
        self.label_13 = QtGui.QLabel(self.layoutWidget1)
        self.label_13.setText(_fromUtf8(""))
        self.label_13.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_PARP.png")))
        self.label_13.setObjectName(_fromUtf8("label_13"))
        self.gridLayout.addWidget(self.label_13, 4, 0, 1, 1)
        self.label_14 = QtGui.QLabel(self.layoutWidget1)
        self.label_14.setText(_fromUtf8(""))
        self.label_14.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_PROGP.png")))
        self.label_14.setObjectName(_fromUtf8("label_14"))
        self.gridLayout.addWidget(self.label_14, 5, 0, 1, 1)
        self.label_2 = QtGui.QLabel(self.layoutWidget1)
        self.label_2.setText(_fromUtf8(""))
        self.label_2.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_EXTINT.png")))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 6, 0, 1, 1)
        self.label_9 = QtGui.QLabel(self.layoutWidget1)
        self.label_9.setText(_fromUtf8(""))
        self.label_9.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_PERP.png")))
        self.label_9.setObjectName(_fromUtf8("label_9"))
        self.gridLayout.addWidget(self.label_9, 1, 0, 1, 1)
        self.checkBox_PERP = QtGui.QCheckBox(self.layoutWidget1)
        self.checkBox_PERP.setTristate(False)
        self.checkBox_PERP.setObjectName(_fromUtf8("checkBox_PERP"))
        self.gridLayout.addWidget(self.checkBox_PERP, 1, 1, 1, 1)
        self.label_10 = QtGui.QLabel(self.layoutWidget1)
        self.label_10.setText(_fromUtf8(""))
        self.label_10.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_TANP.png")))
        self.label_10.setObjectName(_fromUtf8("label_10"))
        self.gridLayout.addWidget(self.label_10, 2, 0, 1, 1)
        self.checkBox_TANP = QtGui.QCheckBox(self.layoutWidget1)
        self.checkBox_TANP.setTristate(False)
        self.checkBox_TANP.setObjectName(_fromUtf8("checkBox_TANP"))
        self.gridLayout.addWidget(self.checkBox_TANP, 2, 1, 1, 1)
        self.checkBox_EXTP = QtGui.QCheckBox(self.layoutWidget1)
        self.checkBox_EXTP.setTristate(False)
        self.checkBox_EXTP.setObjectName(_fromUtf8("checkBox_EXTP"))
        self.gridLayout.addWidget(self.checkBox_EXTP, 3, 1, 1, 1)
        self.checkBox_PARALP = QtGui.QCheckBox(self.layoutWidget1)
        self.checkBox_PARALP.setTristate(False)
        self.checkBox_PARALP.setObjectName(_fromUtf8("checkBox_PARALP"))
        self.gridLayout.addWidget(self.checkBox_PARALP, 4, 1, 1, 1)
        self.checkBox_PROGRESP = QtGui.QCheckBox(self.layoutWidget1)
        self.checkBox_PROGRESP.setTristate(False)
        self.checkBox_PROGRESP.setObjectName(_fromUtf8("checkBox_PROGRESP"))
        self.gridLayout.addWidget(self.checkBox_PROGRESP, 5, 1, 1, 1)
        self.checkBox_EXT_INT = QtGui.QCheckBox(self.layoutWidget1)
        self.checkBox_EXT_INT.setObjectName(_fromUtf8("checkBox_EXT_INT"))
        self.gridLayout.addWidget(self.checkBox_EXT_INT, 6, 1, 1, 1)
        self.checkBox_QUADP = QtGui.QCheckBox(self.layoutWidget1)
        self.checkBox_QUADP.setTristate(False)
        self.checkBox_QUADP.setObjectName(_fromUtf8("checkBox_QUADP"))
        self.gridLayout.addWidget(self.checkBox_QUADP, 0, 1, 1, 1)
        self.label_3 = QtGui.QLabel(self.layoutWidget1)
        self.label_3.setText(_fromUtf8(""))
        self.label_3.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_QUADP.png")))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)
        self.lineEdit_ProgrDistance = QtGui.QLineEdit(self.groupBox)
        self.lineEdit_ProgrDistance.setGeometry(QtCore.QRect(340, 210, 41, 20))
        self.lineEdit_ProgrDistance.setObjectName(_fromUtf8("lineEdit_ProgrDistance"))
        self.layoutWidget2 = QtGui.QWidget(self.groupBox)
        self.layoutWidget2.setGeometry(QtCore.QRect(10, 20, 154, 261))
        self.layoutWidget2.setObjectName(_fromUtf8("layoutWidget2"))
        self.gridLayout_2 = QtGui.QGridLayout(self.layoutWidget2)
        self.gridLayout_2.setMargin(0)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.label_8 = QtGui.QLabel(self.layoutWidget2)
        self.label_8.setText(_fromUtf8(""))
        self.label_8.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_ENDP.png")))
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.gridLayout_2.addWidget(self.label_8, 0, 0, 1, 1)
        self.checkBox_END_PLINE = QtGui.QCheckBox(self.layoutWidget2)
        self.checkBox_END_PLINE.setObjectName(_fromUtf8("checkBox_END_PLINE"))
        self.gridLayout_2.addWidget(self.checkBox_END_PLINE, 0, 1, 1, 1)
        self.label_ENDP = QtGui.QLabel(self.layoutWidget2)
        self.label_ENDP.setText(_fromUtf8(""))
        self.label_ENDP.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_ENDP.png")))
        self.label_ENDP.setObjectName(_fromUtf8("label_ENDP"))
        self.gridLayout_2.addWidget(self.label_ENDP, 1, 0, 1, 1)
        self.checkBox_ENDP = QtGui.QCheckBox(self.layoutWidget2)
        self.checkBox_ENDP.setTristate(False)
        self.checkBox_ENDP.setObjectName(_fromUtf8("checkBox_ENDP"))
        self.gridLayout_2.addWidget(self.checkBox_ENDP, 1, 1, 1, 1)
        self.label_MIDP = QtGui.QLabel(self.layoutWidget2)
        self.label_MIDP.setText(_fromUtf8(""))
        self.label_MIDP.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_MEDP.png")))
        self.label_MIDP.setObjectName(_fromUtf8("label_MIDP"))
        self.gridLayout_2.addWidget(self.label_MIDP, 2, 0, 1, 1)
        self.checkBox_MIDP = QtGui.QCheckBox(self.layoutWidget2)
        self.checkBox_MIDP.setTristate(False)
        self.checkBox_MIDP.setObjectName(_fromUtf8("checkBox_MIDP"))
        self.gridLayout_2.addWidget(self.checkBox_MIDP, 2, 1, 1, 1)
        self.label_4 = QtGui.QLabel(self.layoutWidget2)
        self.label_4.setText(_fromUtf8(""))
        self.label_4.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_INTP.png")))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout_2.addWidget(self.label_4, 3, 0, 1, 1)
        self.checkBox_INTP = QtGui.QCheckBox(self.layoutWidget2)
        self.checkBox_INTP.setTristate(False)
        self.checkBox_INTP.setObjectName(_fromUtf8("checkBox_INTP"))
        self.gridLayout_2.addWidget(self.checkBox_INTP, 3, 1, 1, 1)
        self.label_6 = QtGui.QLabel(self.layoutWidget2)
        self.label_6.setText(_fromUtf8(""))
        self.label_6.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_CENP.png")))
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout_2.addWidget(self.label_6, 4, 0, 1, 1)
        self.checkBox_CENP = QtGui.QCheckBox(self.layoutWidget2)
        self.checkBox_CENP.setTristate(False)
        self.checkBox_CENP.setObjectName(_fromUtf8("checkBox_CENP"))
        self.gridLayout_2.addWidget(self.checkBox_CENP, 4, 1, 1, 1)
        self.label_7 = QtGui.QLabel(self.layoutWidget2)
        self.label_7.setText(_fromUtf8(""))
        self.label_7.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_NODP.png")))
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.gridLayout_2.addWidget(self.label_7, 5, 0, 1, 1)
        self.checkBox_NODP = QtGui.QCheckBox(self.layoutWidget2)
        self.checkBox_NODP.setTristate(False)
        self.checkBox_NODP.setObjectName(_fromUtf8("checkBox_NODP"))
        self.gridLayout_2.addWidget(self.checkBox_NODP, 5, 1, 1, 1)
        self.label_11 = QtGui.QLabel(self.layoutWidget2)
        self.label_11.setText(_fromUtf8(""))
        self.label_11.setPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/dsettings/OSNAP_NEARP.png")))
        self.label_11.setObjectName(_fromUtf8("label_11"))
        self.gridLayout_2.addWidget(self.label_11, 6, 0, 1, 1)
        self.checkBox_NEARP = QtGui.QCheckBox(self.layoutWidget2)
        self.checkBox_NEARP.setTristate(False)
        self.checkBox_NEARP.setObjectName(_fromUtf8("checkBox_NEARP"))
        self.gridLayout_2.addWidget(self.checkBox_NEARP, 6, 1, 1, 1)
        self.checkBox_IsOsnapON = QtGui.QCheckBox(self.tab_1)
        self.checkBox_IsOsnapON.setGeometry(QtCore.QRect(10, 10, 126, 17))
        self.checkBox_IsOsnapON.setObjectName(_fromUtf8("checkBox_IsOsnapON"))
        self.tabWidget.addTab(self.tab_1, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.checkBox_PolarPickPoint = QtGui.QCheckBox(self.tab_2)
        self.checkBox_PolarPickPoint.setGeometry(QtCore.QRect(10, 10, 171, 17))
        self.checkBox_PolarPickPoint.setObjectName(_fromUtf8("checkBox_PolarPickPoint"))
        self.groupBox_2 = QtGui.QGroupBox(self.tab_2)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 40, 151, 81))
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.label_12 = QtGui.QLabel(self.groupBox_2)
        self.label_12.setGeometry(QtCore.QRect(10, 20, 121, 16))
        self.label_12.setObjectName(_fromUtf8("label_12"))
        self.comboBox_increment_angle = QtGui.QComboBox(self.groupBox_2)
        self.comboBox_increment_angle.setGeometry(QtCore.QRect(10, 40, 131, 22))
        self.comboBox_increment_angle.setEditable(True)
        self.comboBox_increment_angle.setObjectName(_fromUtf8("comboBox_increment_angle"))
        self.tabWidget.addTab(self.tab_2, _fromUtf8(""))
        self.layoutWidget3 = QtGui.QWidget(dSettings_dialog)
        self.layoutWidget3.setGeometry(QtCore.QRect(200, 420, 239, 25))
        self.layoutWidget3.setObjectName(_fromUtf8("layoutWidget3"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.layoutWidget3)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.okButton = QtGui.QPushButton(self.layoutWidget3)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.horizontalLayout.addWidget(self.okButton)
        self.cancelButton = QtGui.QPushButton(self.layoutWidget3)
        self.cancelButton.setObjectName(_fromUtf8("cancelButton"))
        self.horizontalLayout.addWidget(self.cancelButton)
        self.pushButton_HELP = QtGui.QPushButton(self.layoutWidget3)
        self.pushButton_HELP.setObjectName(_fromUtf8("pushButton_HELP"))
        self.horizontalLayout.addWidget(self.pushButton_HELP)

        self.retranslateUi(dSettings_dialog)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QObject.connect(self.pushButton_DeSelectALL, QtCore.SIGNAL(_fromUtf8("pressed()")), dSettings_dialog.ButtonDeselectALL_Pressed)
        QtCore.QObject.connect(self.pushButton_SelectALL, QtCore.SIGNAL(_fromUtf8("pressed()")), dSettings_dialog.ButtonSelectALL_Pressed)
        QtCore.QObject.connect(self.pushButton_HELP, QtCore.SIGNAL(_fromUtf8("clicked()")), dSettings_dialog.ButtonHELP_Pressed)
        QtCore.QObject.connect(self.okButton, QtCore.SIGNAL(_fromUtf8("clicked()")), dSettings_dialog.ButtonBOX_Accepted)
        QtCore.QObject.connect(self.cancelButton, QtCore.SIGNAL(_fromUtf8("clicked()")), dSettings_dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(dSettings_dialog)

    def retranslateUi(self, dSettings_dialog):
        dSettings_dialog.setWindowTitle(_translate("dSettings_dialog", "QAD - Impostazioni disegno", None))
        self.groupBox.setTitle(_translate("dSettings_dialog", "Modalità di snap ad oggetto", None))
        self.pushButton_SelectALL.setText(_translate("dSettings_dialog", "Seleziona tutto", None))
        self.pushButton_DeSelectALL.setText(_translate("dSettings_dialog", "Deseleziona tutto", None))
        self.checkBox_PERP.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">OSnap Perpendicolare: proiezione ortogonale di un punto noto su un segmento.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_PERP.png\" /></p></body></html>", None))
        self.checkBox_PERP.setText(_translate("dSettings_dialog", "Perpendicolare", None))
        self.checkBox_TANP.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">OSnap Tangente: punto di tangenza su una curva della retta passante per un punto noto.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_TANP.png\" /></p></body></html>", None))
        self.checkBox_TANP.setText(_translate("dSettings_dialog", "Tangente", None))
        self.checkBox_EXTP.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">OSnap Estensione di: punto sull’estensione di un segmento fino alla posizione del cursore.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_EXTP.png\" /></p></body></html>", None))
        self.checkBox_EXTP.setText(_translate("dSettings_dialog", "Estensione", None))
        self.checkBox_PARALP.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">OSnap Parallelo a: punto sulla retta, passante per un punto noto, parallela ad un segmento.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_PARLP.png\" /></p></body></html>", None))
        self.checkBox_PARALP.setText(_translate("dSettings_dialog", "Parallelo", None))
        self.checkBox_PROGRESP.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">OSnap Progressivo a: punto ad una distanza nota lungo lo sviluppo di una geometria; da un vertice di una geometria è possibile posizionarsi ad una distanza misurata lungo lo sviluppo della geometria stessa.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_PROGRESP.png\" /></p></body></html>", None))
        self.checkBox_PROGRESP.setText(_translate("dSettings_dialog", "Progressivo", None))
        self.checkBox_EXT_INT.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">OSnap Intersezione su estensione: punto determinato dall\'intersezione delle estensioni di due segmenti.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_EXTINT.png\" /></p></body></html>", None))
        self.checkBox_EXT_INT.setText(_translate("dSettings_dialog", "Intersezione su estensione", None))
        self.checkBox_QUADP.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">OSnap Quadrante: intersezione degli assi cartesiani con la circonferenza o arco (aggancio al punto più prossimo al cursore tra le quattro possibili intersezioni).</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_QUADP.png\" /></p></body></html>", None))
        self.checkBox_QUADP.setText(_translate("dSettings_dialog", "Quadrante", None))
        self.checkBox_END_PLINE.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">OSnap Inizio / Fine entità: vertice iniziale e finale di una geometria lineare.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_END_PLINE.png\" /></p></body></html>", None))
        self.checkBox_END_PLINE.setText(_translate("dSettings_dialog", "Inizio / Fine", None))
        self.checkBox_ENDP.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">OSnap Inizio / Fine segmento: vertice iniziale e finale di ciascun segmento di una geometria.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_ENDP.png\" /></p></body></html>", "aa"))
        self.checkBox_ENDP.setText(_translate("dSettings_dialog", "Inizio / Fine segmento", None))
        self.checkBox_MIDP.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">OSnap Punto Medio: punto medio di ciascun segmento di una geometria.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_MIDP.png\" /></p></body></html>", None))
        self.checkBox_MIDP.setText(_translate("dSettings_dialog", "Punto medio", None))
        self.checkBox_INTP.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">OSnap Intersezione: intersezione tra due segmenti.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_INTP.png\" /></p></body></html>", None))
        self.checkBox_INTP.setText(_translate("dSettings_dialog", "Intersezione", None))
        self.checkBox_CENP.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">OSnap Centro: centro di un cerchio o un arco (si attiva con il cursore posizionato in prossimità della curva) o centroide di una geometria areale.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_CENP.png\" /></p></body></html>", None))
        self.checkBox_CENP.setText(_translate("dSettings_dialog", "Centro", None))
        self.checkBox_NODP.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">OSnap Nodo: coordinate di una geometria puntuale.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_NODP.png\" /></p></body></html>", None))
        self.checkBox_NODP.setText(_translate("dSettings_dialog", "Nodo", None))
        self.checkBox_NEARP.setToolTip(_translate("dSettings_dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">OSnap Vicino: punto di un segmento in prossimità della posizione del cursore.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_NEARP.png\" /></p></body></html>", None))
        self.checkBox_NEARP.setText(_translate("dSettings_dialog", "Vicino", None))
        self.checkBox_IsOsnapON.setText(_translate("dSettings_dialog", "Snap ad oggetto (F3)", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), _translate("dSettings_dialog", "Snap ad oggetto", None))
        self.checkBox_PolarPickPoint.setText(_translate("dSettings_dialog", "Puntamento polare (F10)", None))
        self.groupBox_2.setTitle(_translate("dSettings_dialog", "Impostazioni angoli polari", None))
        self.label_12.setText(_translate("dSettings_dialog", "Angolo incremento:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("dSettings_dialog", "Puntamento polare", None))
        self.okButton.setText(_translate("dSettings_dialog", "OK", None))
        self.cancelButton.setText(_translate("dSettings_dialog", "Annulla", None))
        self.pushButton_HELP.setText(_translate("dSettings_dialog", "?", None))

import qad_dsettings_rc
