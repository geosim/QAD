# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qad_dimstyle.ui'
#
# Created: Tue Jul 07 13:52:36 2015
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

class Ui_dimStyle_dialog(object):
    def setupUi(self, dimStyle_dialog):
        dimStyle_dialog.setObjectName(_fromUtf8("dimStyle_dialog"))
        dimStyle_dialog.resize(481, 315)
        self.label = QtGui.QLabel(dimStyle_dialog)
        self.label.setGeometry(QtCore.QRect(20, 10, 121, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.currentDimStyle = QtGui.QLabel(dimStyle_dialog)
        self.currentDimStyle.setGeometry(QtCore.QRect(140, 10, 331, 16))
        self.currentDimStyle.setObjectName(_fromUtf8("currentDimStyle"))
        self.label_2 = QtGui.QLabel(dimStyle_dialog)
        self.label_2.setGeometry(QtCore.QRect(20, 40, 47, 16))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.dimStyleList = QtGui.QListView(dimStyle_dialog)
        self.dimStyleList.setGeometry(QtCore.QRect(10, 60, 171, 141))
        self.dimStyleList.setObjectName(_fromUtf8("dimStyleList"))
        self.SetCurrent = QtGui.QPushButton(dimStyle_dialog)
        self.SetCurrent.setGeometry(QtCore.QRect(370, 60, 101, 23))
        self.SetCurrent.setObjectName(_fromUtf8("SetCurrent"))
        self.new_2 = QtGui.QPushButton(dimStyle_dialog)
        self.new_2.setGeometry(QtCore.QRect(370, 90, 101, 23))
        self.new_2.setObjectName(_fromUtf8("new_2"))
        self.Mod = QtGui.QPushButton(dimStyle_dialog)
        self.Mod.setGeometry(QtCore.QRect(370, 120, 101, 23))
        self.Mod.setObjectName(_fromUtf8("Mod"))
        self.TempMod = QtGui.QPushButton(dimStyle_dialog)
        self.TempMod.setGeometry(QtCore.QRect(370, 150, 101, 23))
        self.TempMod.setObjectName(_fromUtf8("TempMod"))
        self.Diff = QtGui.QPushButton(dimStyle_dialog)
        self.Diff.setGeometry(QtCore.QRect(370, 180, 101, 23))
        self.Diff.setObjectName(_fromUtf8("Diff"))
        self.groupBox = QtGui.QGroupBox(dimStyle_dialog)
        self.groupBox.setGeometry(QtCore.QRect(10, 210, 461, 61))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.descriptionSelectedStyle = QtGui.QLabel(self.groupBox)
        self.descriptionSelectedStyle.setGeometry(QtCore.QRect(10, 10, 441, 41))
        self.descriptionSelectedStyle.setObjectName(_fromUtf8("descriptionSelectedStyle"))
        self.Preview = QtGui.QWidget(dimStyle_dialog)
        self.Preview.setGeometry(QtCore.QRect(190, 60, 171, 141))
        self.Preview.setObjectName(_fromUtf8("Preview"))
        self.label_3 = QtGui.QLabel(dimStyle_dialog)
        self.label_3.setGeometry(QtCore.QRect(190, 40, 71, 16))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.selectedStyle = QtGui.QLabel(dimStyle_dialog)
        self.selectedStyle.setGeometry(QtCore.QRect(270, 40, 201, 16))
        self.selectedStyle.setObjectName(_fromUtf8("selectedStyle"))
        self.layoutWidget = QtGui.QWidget(dimStyle_dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(317, 280, 151, 25))
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

        self.retranslateUi(dimStyle_dialog)
        QtCore.QObject.connect(self.SetCurrent, QtCore.SIGNAL(_fromUtf8("clicked()")), dimStyle_dialog.setCurrentStyle)
        QtCore.QObject.connect(self.new_2, QtCore.SIGNAL(_fromUtf8("clicked()")), dimStyle_dialog.createNewStyle)
        QtCore.QObject.connect(self.Mod, QtCore.SIGNAL(_fromUtf8("clicked()")), dimStyle_dialog.modStyle)
        QtCore.QObject.connect(self.dimStyleList, QtCore.SIGNAL(_fromUtf8("customContextMenuRequested(QPoint)")), dimStyle_dialog.displayPopupMenu)
        QtCore.QObject.connect(self.TempMod, QtCore.SIGNAL(_fromUtf8("clicked()")), dimStyle_dialog.temporaryModStyle)
        QtCore.QObject.connect(self.helpButton, QtCore.SIGNAL(_fromUtf8("clicked()")), dimStyle_dialog.ButtonHELP_Pressed)
        QtCore.QObject.connect(self.Diff, QtCore.SIGNAL(_fromUtf8("clicked()")), dimStyle_dialog.showDiffBetweenStyles)
        QtCore.QObject.connect(self.closeButton, QtCore.SIGNAL(_fromUtf8("clicked()")), dimStyle_dialog.accept)
        QtCore.QMetaObject.connectSlotsByName(dimStyle_dialog)

    def retranslateUi(self, dimStyle_dialog):
        dimStyle_dialog.setWindowTitle(_translate("dimStyle_dialog", "QAD - Gestione stili di quota", None))
        self.label.setText(_translate("dimStyle_dialog", "Stile di quota corrente:", None))
        self.currentDimStyle.setText(_translate("dimStyle_dialog", "nessuno", None))
        self.label_2.setText(_translate("dimStyle_dialog", "Stili", None))
        self.SetCurrent.setToolTip(_translate("dimStyle_dialog", "Rende corrente lo stile selezionato nella\'area Stili. Lo stile corrente è applicato alle quota create dall\'uente.", None))
        self.SetCurrent.setText(_translate("dimStyle_dialog", "Imposta corrente", None))
        self.new_2.setToolTip(_translate("dimStyle_dialog", "Definisce un nuovo stile di quota.", None))
        self.new_2.setText(_translate("dimStyle_dialog", "Nuovo...", None))
        self.Mod.setToolTip(_translate("dimStyle_dialog", "Modifica lo stile di quota selezionato nella\'area Stili.", None))
        self.Mod.setText(_translate("dimStyle_dialog", "Modifica...", None))
        self.TempMod.setToolTip(_translate("dimStyle_dialog", "Imposta modifiche locali per lo stile selezionato nella\'area Stili. Le modifiche locali sono modifiche che non verranno salvate.", None))
        self.TempMod.setText(_translate("dimStyle_dialog", "Sostituisci...", None))
        self.Diff.setToolTip(_translate("dimStyle_dialog", "Confronta due stili di quota o elenca tutte le proprietà di un stile di quota.", None))
        self.Diff.setText(_translate("dimStyle_dialog", "Confronta...", None))
        self.groupBox.setTitle(_translate("dimStyle_dialog", "Descrizione", None))
        self.descriptionSelectedStyle.setText(_translate("dimStyle_dialog", "nessuna", None))
        self.label_3.setText(_translate("dimStyle_dialog", "Anteprima di:", None))
        self.selectedStyle.setText(_translate("dimStyle_dialog", "nessuna", None))
        self.closeButton.setText(_translate("dimStyle_dialog", "Chiudi", None))
        self.helpButton.setText(_translate("dimStyle_dialog", "?", None))

