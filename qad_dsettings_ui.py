# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qad_dsettings.ui'
#
# Created: Mon Jul 04 12:00:42 2016
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

class Ui_DSettings_Dialog(object):
    def setupUi(self, DSettings_Dialog):
        DSettings_Dialog.setObjectName(_fromUtf8("DSettings_Dialog"))
        DSettings_Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        DSettings_Dialog.resize(471, 455)
        DSettings_Dialog.setMinimumSize(QtCore.QSize(471, 455))
        DSettings_Dialog.setMaximumSize(QtCore.QSize(471, 455))
        DSettings_Dialog.setMouseTracking(True)
        DSettings_Dialog.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        DSettings_Dialog.setModal(True)
        self.tabWidget = QtGui.QTabWidget(DSettings_Dialog)
        self.tabWidget.setGeometry(QtCore.QRect(10, 10, 451, 401))
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab_1 = QtGui.QWidget()
        self.tab_1.setObjectName(_fromUtf8("tab_1"))
        self.groupBox = QtGui.QGroupBox(self.tab_1)
        self.groupBox.setGeometry(QtCore.QRect(30, 40, 381, 321))
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
        self.lineEdit_ProgrDistance.setGeometry(QtCore.QRect(330, 210, 41, 20))
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
        self.checkBox_IsOsnapON.setGeometry(QtCore.QRect(10, 10, 181, 17))
        self.checkBox_IsOsnapON.setObjectName(_fromUtf8("checkBox_IsOsnapON"))
        self.checkBox_ObjectSnapTracking = QtGui.QCheckBox(self.tab_1)
        self.checkBox_ObjectSnapTracking.setGeometry(QtCore.QRect(200, 10, 231, 20))
        self.checkBox_ObjectSnapTracking.setObjectName(_fromUtf8("checkBox_ObjectSnapTracking"))
        self.tabWidget.addTab(self.tab_1, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.checkBox_PolarPickPoint = QtGui.QCheckBox(self.tab_2)
        self.checkBox_PolarPickPoint.setGeometry(QtCore.QRect(10, 10, 171, 17))
        self.checkBox_PolarPickPoint.setObjectName(_fromUtf8("checkBox_PolarPickPoint"))
        self.groupBox_PolarAngleSettings = QtGui.QGroupBox(self.tab_2)
        self.groupBox_PolarAngleSettings.setGeometry(QtCore.QRect(10, 40, 151, 71))
        self.groupBox_PolarAngleSettings.setObjectName(_fromUtf8("groupBox_PolarAngleSettings"))
        self.label_12 = QtGui.QLabel(self.groupBox_PolarAngleSettings)
        self.label_12.setGeometry(QtCore.QRect(10, 20, 121, 16))
        self.label_12.setObjectName(_fromUtf8("label_12"))
        self.comboBox_increment_angle = QtGui.QComboBox(self.groupBox_PolarAngleSettings)
        self.comboBox_increment_angle.setGeometry(QtCore.QRect(10, 40, 131, 22))
        self.comboBox_increment_angle.setEditable(True)
        self.comboBox_increment_angle.setObjectName(_fromUtf8("comboBox_increment_angle"))
        self.groupBox_OsnapPolarOrtho = QtGui.QGroupBox(self.tab_2)
        self.groupBox_OsnapPolarOrtho.setGeometry(QtCore.QRect(170, 40, 271, 71))
        self.groupBox_OsnapPolarOrtho.setObjectName(_fromUtf8("groupBox_OsnapPolarOrtho"))
        self.radioButton_OsnapOrtho = QtGui.QRadioButton(self.groupBox_OsnapPolarOrtho)
        self.radioButton_OsnapOrtho.setGeometry(QtCore.QRect(10, 30, 251, 17))
        self.radioButton_OsnapOrtho.setObjectName(_fromUtf8("radioButton_OsnapOrtho"))
        self.radioButton_OsnapPolarAngle = QtGui.QRadioButton(self.groupBox_OsnapPolarOrtho)
        self.radioButton_OsnapPolarAngle.setGeometry(QtCore.QRect(10, 50, 251, 16))
        self.radioButton_OsnapPolarAngle.setObjectName(_fromUtf8("radioButton_OsnapPolarAngle"))
        self.groupBox_OsnapPolarMeasurement = QtGui.QGroupBox(self.tab_2)
        self.groupBox_OsnapPolarMeasurement.setGeometry(QtCore.QRect(170, 120, 271, 71))
        self.groupBox_OsnapPolarMeasurement.setObjectName(_fromUtf8("groupBox_OsnapPolarMeasurement"))
        self.radioButton_OsnapPolarAbolute = QtGui.QRadioButton(self.groupBox_OsnapPolarMeasurement)
        self.radioButton_OsnapPolarAbolute.setGeometry(QtCore.QRect(10, 30, 251, 17))
        self.radioButton_OsnapPolarAbolute.setObjectName(_fromUtf8("radioButton_OsnapPolarAbolute"))
        self.radioButton_OsnapPolarRelative = QtGui.QRadioButton(self.groupBox_OsnapPolarMeasurement)
        self.radioButton_OsnapPolarRelative.setGeometry(QtCore.QRect(10, 50, 251, 17))
        self.radioButton_OsnapPolarRelative.setObjectName(_fromUtf8("radioButton_OsnapPolarRelative"))
        self.tabWidget.addTab(self.tab_2, _fromUtf8(""))
        self.layoutWidget3 = QtGui.QWidget(DSettings_Dialog)
        self.layoutWidget3.setGeometry(QtCore.QRect(220, 420, 239, 25))
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

        self.retranslateUi(DSettings_Dialog)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QObject.connect(self.pushButton_DeSelectALL, QtCore.SIGNAL(_fromUtf8("pressed()")), DSettings_Dialog.ButtonDeselectALL_Pressed)
        QtCore.QObject.connect(self.pushButton_SelectALL, QtCore.SIGNAL(_fromUtf8("pressed()")), DSettings_Dialog.ButtonSelectALL_Pressed)
        QtCore.QObject.connect(self.pushButton_HELP, QtCore.SIGNAL(_fromUtf8("clicked()")), DSettings_Dialog.ButtonHELP_Pressed)
        QtCore.QObject.connect(self.okButton, QtCore.SIGNAL(_fromUtf8("clicked()")), DSettings_Dialog.ButtonBOX_Accepted)
        QtCore.QObject.connect(self.cancelButton, QtCore.SIGNAL(_fromUtf8("clicked()")), DSettings_Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(DSettings_Dialog)

    def retranslateUi(self, DSettings_Dialog):
        DSettings_Dialog.setWindowTitle(_translate("DSettings_Dialog", "QAD - Drawing settings", None))
        self.groupBox.setTitle(_translate("DSettings_Dialog", "Object Snap modes", None))
        self.pushButton_SelectALL.setText(_translate("DSettings_Dialog", "Select All", None))
        self.pushButton_DeSelectALL.setText(_translate("DSettings_Dialog", "Deselect All", None))
        self.checkBox_PERP.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Perpendicular OSnap: orthogonal projection of a given point on a segment.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_PERP.png\" /></p></body></html>", None))
        self.checkBox_PERP.setText(_translate("DSettings_Dialog", "Perpendicular", None))
        self.checkBox_TANP.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">tangent point on a curve of a line passing through a given point.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_TANP.png\" /></p></body></html>", None))
        self.checkBox_TANP.setText(_translate("DSettings_Dialog", "Tangent", None))
        self.checkBox_EXTP.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Extension OSnap: point on the segment extension until the cursor position.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_EXTP.png\" /></p></body></html>", None))
        self.checkBox_EXTP.setText(_translate("DSettings_Dialog", "Extend", None))
        self.checkBox_PARALP.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Parallel OSnap: point on a line, passing through a given point, parallel to a segment.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_PARLP.png\" /></p></body></html>", None))
        self.checkBox_PARALP.setText(_translate("DSettings_Dialog", "Parallel", None))
        self.checkBox_PROGRESP.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Progressive OSnap: point at a given distance along a geometry line: from a vertex we can set a point at a distance measured along the geometry line.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_PROGRESP.png\" /></p></body></html>", None))
        self.checkBox_PROGRESP.setText(_translate("DSettings_Dialog", "Progressive", None))
        self.checkBox_EXT_INT.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Intersection on extension OSnap: intersection point of the extensions of two segments.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_EXTINT.png\" /></p></body></html>", None))
        self.checkBox_EXT_INT.setText(_translate("DSettings_Dialog", "Intersection on extension", None))
        self.checkBox_QUADP.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Quadrant OSnap: intersections of the cartesian axis with a circumference of a circle or an arc.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_QUADP.png\" /></p></body></html>", None))
        self.checkBox_QUADP.setText(_translate("DSettings_Dialog", "Quadrant", None))
        self.checkBox_END_PLINE.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Start / End OSnap: starting and ending vertices of a linear geometry.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_END_PLINE.png\" /></p></body></html>", None))
        self.checkBox_END_PLINE.setText(_translate("DSettings_Dialog", "Start / End", None))
        self.checkBox_ENDP.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Start / End segment OSnap: starting and ending vertices of each segment of a geometry.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_ENDP.png\" /></p></body></html>", "aa"))
        self.checkBox_ENDP.setText(_translate("DSettings_Dialog", "Segment Start / End", None))
        self.checkBox_MIDP.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Middle point OSnap: middle point of each segment of a geometry.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_MIDP.png\" /></p></body></html>", None))
        self.checkBox_MIDP.setText(_translate("DSettings_Dialog", "Middle point", None))
        self.checkBox_INTP.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Intersection OSnap: intersection between two segments.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_INTP.png\" /></p></body></html>", None))
        self.checkBox_INTP.setText(_translate("DSettings_Dialog", "Intersection", None))
        self.checkBox_CENP.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Center OSnap: center of a circle or arc or centroid of an areal geometry.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_CENP.png\" /></p></body></html>", None))
        self.checkBox_CENP.setText(_translate("DSettings_Dialog", "Center", None))
        self.checkBox_NODP.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Node OSnap: coordinate of a punctual geometry.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_NODP.png\" /></p></body></html>", None))
        self.checkBox_NODP.setText(_translate("DSettings_Dialog", "Node", None))
        self.checkBox_NEARP.setToolTip(_translate("DSettings_Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Near OSnap: point of a segment close to the cursor position.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/plugins/qad/icons/dsettings/OSNAP_ToolTIP_NEARP.png\" /></p></body></html>", None))
        self.checkBox_NEARP.setText(_translate("DSettings_Dialog", "Near", None))
        self.checkBox_IsOsnapON.setToolTip(_translate("DSettings_Dialog", "<html><head/><body><p>Turns object snap on and off. The selected object snap modes are active when the object snap is activated (system variable OSMODE).</p></body></html>", None))
        self.checkBox_IsOsnapON.setText(_translate("DSettings_Dialog", "Object Snap (F3)", None))
        self.checkBox_ObjectSnapTracking.setToolTip(_translate("DSettings_Dialog", "<html><head/><body><p>Turns object snap tracking on and off. Using the object snap tracking, the cursor can track along alignment paths that are based on object snap points. To use the object snap tracking, select one or more object snap (system variable AUTOSNAP).</p></body></html>", None))
        self.checkBox_ObjectSnapTracking.setText(_translate("DSettings_Dialog", "Object Snap Tracking (F11)", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), _translate("DSettings_Dialog", "Object Snap", None))
        self.checkBox_PolarPickPoint.setToolTip(_translate("DSettings_Dialog", "Turns polar tracking on and off (system variable AUTOSNAP).", None))
        self.checkBox_PolarPickPoint.setText(_translate("DSettings_Dialog", "Polar Tracking (F10)", None))
        self.groupBox_PolarAngleSettings.setTitle(_translate("DSettings_Dialog", "Polar angle settings", None))
        self.label_12.setText(_translate("DSettings_Dialog", "Increment angle:", None))
        self.groupBox_OsnapPolarOrtho.setTitle(_translate("DSettings_Dialog", "Object Snap Tracking Settings", None))
        self.radioButton_OsnapOrtho.setToolTip(_translate("DSettings_Dialog", "Displays only orthogonal (horizontal/vertical) object snap tracking paths for acquired object snap points when object snap tracking is on (POLARMODE system variable).", None))
        self.radioButton_OsnapOrtho.setText(_translate("DSettings_Dialog", "Track orthogonally only", None))
        self.radioButton_OsnapPolarAngle.setToolTip(_translate("DSettings_Dialog", "Applies polar tracking settings to object snap tracking. When you use object snap tracking, the cursor tracks along polar alignment angles from acquired object snap points (POLARMODE system variable).", None))
        self.radioButton_OsnapPolarAngle.setText(_translate("DSettings_Dialog", "Track using polar angle settings", None))
        self.groupBox_OsnapPolarMeasurement.setTitle(_translate("DSettings_Dialog", "Polar Angle measurement", None))
        self.radioButton_OsnapPolarAbolute.setToolTip(_translate("DSettings_Dialog", "Bases polar tracking angles on the current user coordinate system.", None))
        self.radioButton_OsnapPolarAbolute.setText(_translate("DSettings_Dialog", "Absolute", None))
        self.radioButton_OsnapPolarRelative.setToolTip(_translate("DSettings_Dialog", "Bases polar tracking angles on the last segment drawn.", None))
        self.radioButton_OsnapPolarRelative.setText(_translate("DSettings_Dialog", "Relative to last segment", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("DSettings_Dialog", "Polar Tracking", None))
        self.okButton.setText(_translate("DSettings_Dialog", "OK", None))
        self.cancelButton.setText(_translate("DSettings_Dialog", "Cancel", None))
        self.pushButton_HELP.setText(_translate("DSettings_Dialog", "?", None))

import qad_dsettings_rc
