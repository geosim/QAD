# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qad_dimstyle_new.ui'
#
# Created: Mon Jul 04 12:00:43 2016
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

class Ui_DimStyle_New_Dialog(object):
    def setupUi(self, DimStyle_New_Dialog):
        DimStyle_New_Dialog.setObjectName(_fromUtf8("DimStyle_New_Dialog"))
        DimStyle_New_Dialog.resize(372, 142)
        DimStyle_New_Dialog.setMinimumSize(QtCore.QSize(372, 142))
        DimStyle_New_Dialog.setMaximumSize(QtCore.QSize(372, 142))
        self.label = QtGui.QLabel(DimStyle_New_Dialog)
        self.label.setGeometry(QtCore.QRect(10, 10, 221, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.newDimStyleName = QtGui.QLineEdit(DimStyle_New_Dialog)
        self.newDimStyleName.setGeometry(QtCore.QRect(10, 30, 221, 20))
        self.newDimStyleName.setObjectName(_fromUtf8("newDimStyleName"))
        self.label_2 = QtGui.QLabel(DimStyle_New_Dialog)
        self.label_2.setGeometry(QtCore.QRect(10, 90, 221, 16))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.DimStyleNameFrom = QtGui.QComboBox(DimStyle_New_Dialog)
        self.DimStyleNameFrom.setGeometry(QtCore.QRect(10, 110, 221, 22))
        self.DimStyleNameFrom.setObjectName(_fromUtf8("DimStyleNameFrom"))
        self.continueButton = QtGui.QPushButton(DimStyle_New_Dialog)
        self.continueButton.setGeometry(QtCore.QRect(284, 50, 81, 23))
        self.continueButton.setObjectName(_fromUtf8("continueButton"))
        self.cancelButton = QtGui.QPushButton(DimStyle_New_Dialog)
        self.cancelButton.setGeometry(QtCore.QRect(284, 80, 81, 23))
        self.cancelButton.setObjectName(_fromUtf8("cancelButton"))
        self.helpButton = QtGui.QPushButton(DimStyle_New_Dialog)
        self.helpButton.setGeometry(QtCore.QRect(284, 110, 81, 23))
        self.helpButton.setObjectName(_fromUtf8("helpButton"))
        self.label_3 = QtGui.QLabel(DimStyle_New_Dialog)
        self.label_3.setGeometry(QtCore.QRect(10, 50, 221, 16))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.newDimStyleDescr = QtGui.QLineEdit(DimStyle_New_Dialog)
        self.newDimStyleDescr.setGeometry(QtCore.QRect(10, 70, 221, 20))
        self.newDimStyleDescr.setObjectName(_fromUtf8("newDimStyleDescr"))

        self.retranslateUi(DimStyle_New_Dialog)
        QtCore.QObject.connect(self.DimStyleNameFrom, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), DimStyle_New_Dialog.DimStyleNameFromChanged)
        QtCore.QObject.connect(self.newDimStyleName, QtCore.SIGNAL(_fromUtf8("textEdited(QString)")), DimStyle_New_Dialog.newStyleNameChanged)
        QtCore.QObject.connect(self.cancelButton, QtCore.SIGNAL(_fromUtf8("clicked()")), DimStyle_New_Dialog.reject)
        QtCore.QObject.connect(self.helpButton, QtCore.SIGNAL(_fromUtf8("clicked()")), DimStyle_New_Dialog.ButtonHELP_Pressed)
        QtCore.QObject.connect(self.continueButton, QtCore.SIGNAL(_fromUtf8("clicked()")), DimStyle_New_Dialog.ButtonBOX_continue)
        QtCore.QMetaObject.connectSlotsByName(DimStyle_New_Dialog)

    def retranslateUi(self, DimStyle_New_Dialog):
        DimStyle_New_Dialog.setWindowTitle(_translate("DimStyle_New_Dialog", "QAD - Create new dimension style", None))
        self.label.setText(_translate("DimStyle_New_Dialog", "New style name:", None))
        self.label_2.setText(_translate("DimStyle_New_Dialog", "Start with:", None))
        self.continueButton.setText(_translate("DimStyle_New_Dialog", "Continue...", None))
        self.cancelButton.setText(_translate("DimStyle_New_Dialog", "Cancel", None))
        self.helpButton.setText(_translate("DimStyle_New_Dialog", "?", None))
        self.label_3.setText(_translate("DimStyle_New_Dialog", "Description:", None))

