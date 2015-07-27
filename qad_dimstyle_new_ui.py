# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qad_dimstyle_new.ui'
#
# Created: Mon Jul 20 07:49:13 2015
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(372, 142)
        self.label = QtGui.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(10, 10, 221, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.newDimStyleName = QtGui.QLineEdit(Dialog)
        self.newDimStyleName.setGeometry(QtCore.QRect(10, 30, 221, 20))
        self.newDimStyleName.setObjectName(_fromUtf8("newDimStyleName"))
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(10, 90, 221, 16))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.DimStyleNameFrom = QtGui.QComboBox(Dialog)
        self.DimStyleNameFrom.setGeometry(QtCore.QRect(10, 110, 221, 22))
        self.DimStyleNameFrom.setObjectName(_fromUtf8("DimStyleNameFrom"))
        self.continueButton = QtGui.QPushButton(Dialog)
        self.continueButton.setGeometry(QtCore.QRect(290, 50, 75, 23))
        self.continueButton.setObjectName(_fromUtf8("continueButton"))
        self.cancelButton = QtGui.QPushButton(Dialog)
        self.cancelButton.setGeometry(QtCore.QRect(290, 80, 75, 23))
        self.cancelButton.setObjectName(_fromUtf8("cancelButton"))
        self.helpButton = QtGui.QPushButton(Dialog)
        self.helpButton.setGeometry(QtCore.QRect(290, 110, 75, 23))
        self.helpButton.setObjectName(_fromUtf8("helpButton"))
        self.label_3 = QtGui.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(10, 50, 221, 16))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.newDimStyleDescr = QtGui.QLineEdit(Dialog)
        self.newDimStyleDescr.setGeometry(QtCore.QRect(10, 70, 221, 20))
        self.newDimStyleDescr.setObjectName(_fromUtf8("newDimStyleDescr"))

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.DimStyleNameFrom, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), Dialog.DimStyleNameFromChanged)
        QtCore.QObject.connect(self.newDimStyleName, QtCore.SIGNAL(_fromUtf8("textEdited(QString)")), Dialog.newStyleNameChanged)
        QtCore.QObject.connect(self.cancelButton, QtCore.SIGNAL(_fromUtf8("clicked()")), Dialog.reject)
        QtCore.QObject.connect(self.helpButton, QtCore.SIGNAL(_fromUtf8("clicked()")), Dialog.ButtonHELP_Pressed)
        QtCore.QObject.connect(self.continueButton, QtCore.SIGNAL(_fromUtf8("clicked()")), Dialog.ButtonBOX_continue)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.label.setText(_translate("Dialog", "Nome del nuovo stile:", None))
        self.label_2.setText(_translate("Dialog", "Copia i parametri dallo stile:", None))
        self.continueButton.setText(_translate("Dialog", "Continua...", None))
        self.cancelButton.setText(_translate("Dialog", "Annulla", None))
        self.helpButton.setText(_translate("Dialog", "?", None))
        self.label_3.setText(_translate("Dialog", "Descrizione:", None))

