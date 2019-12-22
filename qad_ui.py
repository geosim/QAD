# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qad.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_QAD(object):
    def setupUi(self, QAD):
        QAD.setObjectName("QAD")
        QAD.resize(400, 300)
        self.buttonBox = QtWidgets.QDialogButtonBox(QAD)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")

        self.retranslateUi(QAD)
        self.buttonBox.accepted.connect(QAD.accept)
        self.buttonBox.rejected.connect(QAD.reject)
        QtCore.QMetaObject.connectSlotsByName(QAD)

    def retranslateUi(self, QAD):
        _translate = QtCore.QCoreApplication.translate
        QAD.setWindowTitle(_translate("QAD", "QAD"))

