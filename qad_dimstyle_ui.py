# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qad_dimstyle.ui'
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

class Ui_DimStyle_Dialog(object):
    def setupUi(self, DimStyle_Dialog):
        DimStyle_Dialog.setObjectName(_fromUtf8("DimStyle_Dialog"))
        DimStyle_Dialog.setWindowModality(QtCore.Qt.WindowModal)
        DimStyle_Dialog.resize(533, 341)
        DimStyle_Dialog.setMinimumSize(QtCore.QSize(533, 341))
        DimStyle_Dialog.setMaximumSize(QtCore.QSize(533, 341))
        self.label = QtGui.QLabel(DimStyle_Dialog)
        self.label.setGeometry(QtCore.QRect(20, 10, 151, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.currentDimStyle = QtGui.QLabel(DimStyle_Dialog)
        self.currentDimStyle.setGeometry(QtCore.QRect(180, 10, 341, 16))
        self.currentDimStyle.setObjectName(_fromUtf8("currentDimStyle"))
        self.label_2 = QtGui.QLabel(DimStyle_Dialog)
        self.label_2.setGeometry(QtCore.QRect(10, 40, 171, 20))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.dimStyleList = QtGui.QListView(DimStyle_Dialog)
        self.dimStyleList.setGeometry(QtCore.QRect(10, 60, 171, 171))
        self.dimStyleList.setObjectName(_fromUtf8("dimStyleList"))
        self.SetCurrent = QtGui.QPushButton(DimStyle_Dialog)
        self.SetCurrent.setGeometry(QtCore.QRect(410, 60, 111, 23))
        self.SetCurrent.setObjectName(_fromUtf8("SetCurrent"))
        self.new_2 = QtGui.QPushButton(DimStyle_Dialog)
        self.new_2.setGeometry(QtCore.QRect(410, 90, 111, 23))
        self.new_2.setObjectName(_fromUtf8("new_2"))
        self.Mod = QtGui.QPushButton(DimStyle_Dialog)
        self.Mod.setGeometry(QtCore.QRect(410, 120, 111, 23))
        self.Mod.setObjectName(_fromUtf8("Mod"))
        self.TempMod = QtGui.QPushButton(DimStyle_Dialog)
        self.TempMod.setGeometry(QtCore.QRect(410, 150, 111, 23))
        self.TempMod.setObjectName(_fromUtf8("TempMod"))
        self.Diff = QtGui.QPushButton(DimStyle_Dialog)
        self.Diff.setGeometry(QtCore.QRect(410, 180, 111, 23))
        self.Diff.setObjectName(_fromUtf8("Diff"))
        self.groupBox = QtGui.QGroupBox(DimStyle_Dialog)
        self.groupBox.setGeometry(QtCore.QRect(10, 240, 511, 61))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.descriptionSelectedStyle = QtGui.QLabel(self.groupBox)
        self.descriptionSelectedStyle.setGeometry(QtCore.QRect(10, 10, 481, 41))
        self.descriptionSelectedStyle.setObjectName(_fromUtf8("descriptionSelectedStyle"))
        self.label_3 = QtGui.QLabel(DimStyle_Dialog)
        self.label_3.setGeometry(QtCore.QRect(190, 40, 81, 16))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.selectedStyle = QtGui.QLabel(DimStyle_Dialog)
        self.selectedStyle.setGeometry(QtCore.QRect(280, 40, 241, 20))
        self.selectedStyle.setObjectName(_fromUtf8("selectedStyle"))
        self.layoutWidget = QtGui.QWidget(DimStyle_Dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(360, 310, 158, 25))
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
        self.previewDummy = QtGui.QPushButton(DimStyle_Dialog)
        self.previewDummy.setGeometry(QtCore.QRect(190, 60, 211, 171))
        self.previewDummy.setText(_fromUtf8(""))
        self.previewDummy.setObjectName(_fromUtf8("previewDummy"))

        self.retranslateUi(DimStyle_Dialog)
        QtCore.QObject.connect(self.SetCurrent, QtCore.SIGNAL(_fromUtf8("clicked()")), DimStyle_Dialog.setCurrentStyle)
        QtCore.QObject.connect(self.new_2, QtCore.SIGNAL(_fromUtf8("clicked()")), DimStyle_Dialog.createNewStyle)
        QtCore.QObject.connect(self.Mod, QtCore.SIGNAL(_fromUtf8("clicked()")), DimStyle_Dialog.modStyle)
        QtCore.QObject.connect(self.dimStyleList, QtCore.SIGNAL(_fromUtf8("customContextMenuRequested(QPoint)")), DimStyle_Dialog.displayPopupMenu)
        QtCore.QObject.connect(self.TempMod, QtCore.SIGNAL(_fromUtf8("clicked()")), DimStyle_Dialog.temporaryModStyle)
        QtCore.QObject.connect(self.helpButton, QtCore.SIGNAL(_fromUtf8("clicked()")), DimStyle_Dialog.ButtonHELP_Pressed)
        QtCore.QObject.connect(self.Diff, QtCore.SIGNAL(_fromUtf8("clicked()")), DimStyle_Dialog.showDiffBetweenStyles)
        QtCore.QObject.connect(self.closeButton, QtCore.SIGNAL(_fromUtf8("clicked()")), DimStyle_Dialog.accept)
        QtCore.QMetaObject.connectSlotsByName(DimStyle_Dialog)

    def retranslateUi(self, DimStyle_Dialog):
        DimStyle_Dialog.setWindowTitle(_translate("DimStyle_Dialog", "QAD - Dimension style manager", None))
        self.label.setText(_translate("DimStyle_Dialog", "Current dimension style:", None))
        self.currentDimStyle.setText(_translate("DimStyle_Dialog", "none", None))
        self.label_2.setText(_translate("DimStyle_Dialog", "Styles", None))
        self.SetCurrent.setToolTip(_translate("DimStyle_Dialog", "Sets the style selected under Styles to current. The current style is applied to dimensions you create.", None))
        self.SetCurrent.setText(_translate("DimStyle_Dialog", "Set current", None))
        self.new_2.setToolTip(_translate("DimStyle_Dialog", "Define a new dimension style.", None))
        self.new_2.setText(_translate("DimStyle_Dialog", "New...", None))
        self.Mod.setToolTip(_translate("DimStyle_Dialog", "Modify the selected dimension style.", None))
        self.Mod.setText(_translate("DimStyle_Dialog", "Modify...", None))
        self.TempMod.setToolTip(_translate("DimStyle_Dialog", "Set temporary modifications for the selected style. The temporary modifications will not saved.", None))
        self.TempMod.setText(_translate("DimStyle_Dialog", "Override...", None))
        self.Diff.setToolTip(_translate("DimStyle_Dialog", "Compare two dimension styles or list all the properties of one dimension style.", None))
        self.Diff.setText(_translate("DimStyle_Dialog", "Compare...", None))
        self.groupBox.setTitle(_translate("DimStyle_Dialog", "Description", None))
        self.descriptionSelectedStyle.setText(_translate("DimStyle_Dialog", "none", None))
        self.label_3.setText(_translate("DimStyle_Dialog", "Preview of:", None))
        self.selectedStyle.setText(_translate("DimStyle_Dialog", "none", None))
        self.closeButton.setText(_translate("DimStyle_Dialog", "Close", None))
        self.helpButton.setText(_translate("DimStyle_Dialog", "?", None))

