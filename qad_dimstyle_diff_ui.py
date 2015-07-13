# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qad_dimstyle_diff.ui'
#
# Created: Tue Jul 07 13:52:39 2015
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

class Ui_dimStyle_diff_dialog(object):
    def setupUi(self, dimStyle_diff_dialog):
        dimStyle_diff_dialog.setObjectName(_fromUtf8("dimStyle_diff_dialog"))
        dimStyle_diff_dialog.resize(443, 526)
        self.label = QtGui.QLabel(dimStyle_diff_dialog)
        self.label.setGeometry(QtCore.QRect(10, 10, 101, 21))
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(dimStyle_diff_dialog)
        self.label_2.setGeometry(QtCore.QRect(10, 40, 101, 21))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.dimStyle1 = QtGui.QComboBox(dimStyle_diff_dialog)
        self.dimStyle1.setGeometry(QtCore.QRect(80, 10, 211, 22))
        self.dimStyle1.setObjectName(_fromUtf8("dimStyle1"))
        self.dimStyle2 = QtGui.QComboBox(dimStyle_diff_dialog)
        self.dimStyle2.setGeometry(QtCore.QRect(80, 40, 211, 22))
        self.dimStyle2.setObjectName(_fromUtf8("dimStyle2"))
        self.line = QtGui.QFrame(dimStyle_diff_dialog)
        self.line.setGeometry(QtCore.QRect(10, 70, 421, 16))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.msg = QtGui.QLabel(dimStyle_diff_dialog)
        self.msg.setGeometry(QtCore.QRect(10, 80, 321, 21))
        self.msg.setObjectName(_fromUtf8("msg"))
        self.layoutWidget = QtGui.QWidget(dimStyle_diff_dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(277, 490, 158, 25))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.closeButton = QtGui.QPushButton(self.layoutWidget)
        self.closeButton.setObjectName(_fromUtf8("closeButton"))
        self.horizontalLayout.addWidget(self.closeButton)
        self.helpButton = QtGui.QPushButton(self.layoutWidget)
        self.helpButton.setObjectName(_fromUtf8("helpButton"))
        self.horizontalLayout.addWidget(self.helpButton)
        self.tableWidget = QtGui.QTableWidget(dimStyle_diff_dialog)
        self.tableWidget.setGeometry(QtCore.QRect(10, 110, 421, 371))
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.copyButton = QtGui.QPushButton(dimStyle_diff_dialog)
        self.copyButton.setGeometry(QtCore.QRect(404, 80, 31, 23))
        self.copyButton.setText(_fromUtf8(""))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/qad/icons/copy.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.copyButton.setIcon(icon)
        self.copyButton.setObjectName(_fromUtf8("copyButton"))

        self.retranslateUi(dimStyle_diff_dialog)
        QtCore.QObject.connect(self.helpButton, QtCore.SIGNAL(_fromUtf8("clicked()")), dimStyle_diff_dialog.ButtonHELP_Pressed)
        QtCore.QObject.connect(self.dimStyle1, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), dimStyle_diff_dialog.DimStyleName1Changed)
        QtCore.QObject.connect(self.dimStyle2, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), dimStyle_diff_dialog.DimStyleName2Changed)
        QtCore.QObject.connect(self.copyButton, QtCore.SIGNAL(_fromUtf8("clicked()")), dimStyle_diff_dialog.copyToClipboard)
        QtCore.QObject.connect(self.closeButton, QtCore.SIGNAL(_fromUtf8("clicked()")), dimStyle_diff_dialog.accept)
        QtCore.QMetaObject.connectSlotsByName(dimStyle_diff_dialog)

    def retranslateUi(self, dimStyle_diff_dialog):
        dimStyle_diff_dialog.setWindowTitle(_translate("dimStyle_diff_dialog", "Confronta stili di quota", None))
        self.label.setText(_translate("dimStyle_diff_dialog", "Confronta:", None))
        self.label_2.setText(_translate("dimStyle_diff_dialog", "Con:", None))
        self.dimStyle1.setToolTip(_translate("dimStyle_diff_dialog", "Specifica il primo stile di quota per il confronto.", None))
        self.dimStyle2.setToolTip(_translate("dimStyle_diff_dialog", "Specifica il secondo stile di quota per il confronto.Se si imposta il secondo stile come il primo stile, verranno visualizzate tutte le proprietà dello stile di quota.", None))
        self.msg.setText(_translate("dimStyle_diff_dialog", "TextLabel", None))
        self.closeButton.setText(_translate("dimStyle_diff_dialog", "Chiudi", None))
        self.helpButton.setText(_translate("dimStyle_diff_dialog", "?", None))
        self.tableWidget.setToolTip(_translate("dimStyle_diff_dialog", "<html><head/><body><p>Visualizza i risultati dl confronto degl istili di quota. Se si confrontano due stili diversi, verranno mostrate le proprietà con valore differente. Se si imposta il secondo stile come il primo stile, verranno visualizzate tutte le proprietà dello stile di quota.</p></body></html>", None))
        self.copyButton.setToolTip(_translate("dimStyle_diff_dialog", "Copia il risultato del confronto negli Appunti.", None))

