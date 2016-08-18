# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qad_gripcolor.ui'
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

class Ui_GripColor_Dialog(object):
    def setupUi(self, GripColor_Dialog):
        GripColor_Dialog.setObjectName(_fromUtf8("GripColor_Dialog"))
        GripColor_Dialog.resize(351, 208)
        GripColor_Dialog.setMinimumSize(QtCore.QSize(351, 208))
        GripColor_Dialog.setMaximumSize(QtCore.QSize(351, 208))
        self.buttonBox = QtGui.QDialogButtonBox(GripColor_Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(10, 170, 331, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Help|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.groupBox = QtGui.QGroupBox(GripColor_Dialog)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 331, 141))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(10, 30, 151, 21))
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(180, 30, 151, 21))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(10, 80, 151, 21))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setGeometry(QtCore.QRect(180, 80, 151, 21))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.unselectedGripColorDummy = QtGui.QPushButton(self.groupBox)
        self.unselectedGripColorDummy.setGeometry(QtCore.QRect(10, 50, 141, 23))
        self.unselectedGripColorDummy.setText(_fromUtf8(""))
        self.unselectedGripColorDummy.setObjectName(_fromUtf8("unselectedGripColorDummy"))
        self.selectedGripColorDummy = QtGui.QPushButton(self.groupBox)
        self.selectedGripColorDummy.setGeometry(QtCore.QRect(10, 100, 141, 23))
        self.selectedGripColorDummy.setText(_fromUtf8(""))
        self.selectedGripColorDummy.setObjectName(_fromUtf8("selectedGripColorDummy"))
        self.hoverGripColorDummy = QtGui.QPushButton(self.groupBox)
        self.hoverGripColorDummy.setGeometry(QtCore.QRect(180, 50, 141, 23))
        self.hoverGripColorDummy.setText(_fromUtf8(""))
        self.hoverGripColorDummy.setObjectName(_fromUtf8("hoverGripColorDummy"))
        self.contourGripColorDummy = QtGui.QPushButton(self.groupBox)
        self.contourGripColorDummy.setGeometry(QtCore.QRect(180, 100, 141, 23))
        self.contourGripColorDummy.setText(_fromUtf8(""))
        self.contourGripColorDummy.setObjectName(_fromUtf8("contourGripColorDummy"))

        self.retranslateUi(GripColor_Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), GripColor_Dialog.reject)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("helpRequested()")), GripColor_Dialog.ButtonHELP_Pressed)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), GripColor_Dialog.ButtonBOX_Accepted)
        QtCore.QMetaObject.connectSlotsByName(GripColor_Dialog)

    def retranslateUi(self, GripColor_Dialog):
        GripColor_Dialog.setWindowTitle(_translate("GripColor_Dialog", "QAD - Grip colors", None))
        self.groupBox.setTitle(_translate("GripColor_Dialog", "Settings", None))
        self.label.setText(_translate("GripColor_Dialog", "Unselected grip color:", None))
        self.label_2.setText(_translate("GripColor_Dialog", "Hover grip color:", None))
        self.label_3.setText(_translate("GripColor_Dialog", "Selected grip color:", None))
        self.label_4.setText(_translate("GripColor_Dialog", "Grip contour color:", None))

