# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_qad.ui'
#
# Created: Fri Jun 28 09:17:52 2013
#      by: PyQt4 UI code generator 4.8.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Qad(object):
    def setupUi(self, Qad):
        Qad.setObjectName(_fromUtf8("Qad"))
        Qad.resize(400, 300)
        self.buttonBox = QtGui.QDialogButtonBox(Qad)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))

        self.retranslateUi(Qad)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Qad.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Qad.reject)
        QtCore.QMetaObject.connectSlotsByName(Qad)

    def retranslateUi(self, Qad):
        Qad.setWindowTitle(QtGui.QApplication.translate("Qad", "Qad", None, QtGui.QApplication.UnicodeUTF8))

