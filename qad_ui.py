# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qad.ui'
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

class Ui_QAD(object):
    def setupUi(self, QAD):
        QAD.setObjectName(_fromUtf8("QAD"))
        QAD.resize(400, 300)
        self.buttonBox = QtGui.QDialogButtonBox(QAD)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))

        self.retranslateUi(QAD)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), QAD.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), QAD.reject)
        QtCore.QMetaObject.connectSlotsByName(QAD)

    def retranslateUi(self, QAD):
        QAD.setWindowTitle(_translate("QAD", "QAD", None))

