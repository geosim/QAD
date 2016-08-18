# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qad_windowcolor.ui'
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

class Ui_WindowColor_Dialog(object):
    def setupUi(self, WindowColor_Dialog):
        WindowColor_Dialog.setObjectName(_fromUtf8("WindowColor_Dialog"))
        WindowColor_Dialog.resize(592, 424)
        WindowColor_Dialog.setMinimumSize(QtCore.QSize(592, 424))
        WindowColor_Dialog.setMaximumSize(QtCore.QSize(592, 424))
        self.Button_Cancel = QtGui.QPushButton(WindowColor_Dialog)
        self.Button_Cancel.setGeometry(QtCore.QRect(430, 390, 75, 23))
        self.Button_Cancel.setObjectName(_fromUtf8("Button_Cancel"))
        self.Button_Help = QtGui.QPushButton(WindowColor_Dialog)
        self.Button_Help.setGeometry(QtCore.QRect(510, 390, 75, 23))
        self.Button_Help.setObjectName(_fromUtf8("Button_Help"))
        self.Button_ApplyClose = QtGui.QPushButton(WindowColor_Dialog)
        self.Button_ApplyClose.setGeometry(QtCore.QRect(334, 390, 91, 23))
        self.Button_ApplyClose.setObjectName(_fromUtf8("Button_ApplyClose"))
        self.label = QtGui.QLabel(WindowColor_Dialog)
        self.label.setGeometry(QtCore.QRect(10, 10, 161, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.listView_Context = QtGui.QListView(WindowColor_Dialog)
        self.listView_Context.setGeometry(QtCore.QRect(10, 30, 161, 81))
        self.listView_Context.setObjectName(_fromUtf8("listView_Context"))
        self.listView_Element = QtGui.QListView(WindowColor_Dialog)
        self.listView_Element.setGeometry(QtCore.QRect(180, 30, 231, 171))
        self.listView_Element.setObjectName(_fromUtf8("listView_Element"))
        self.label_2 = QtGui.QLabel(WindowColor_Dialog)
        self.label_2.setGeometry(QtCore.QRect(180, 10, 161, 16))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.Button_ColorDummy = QtGui.QPushButton(WindowColor_Dialog)
        self.Button_ColorDummy.setGeometry(QtCore.QRect(420, 30, 161, 23))
        self.Button_ColorDummy.setText(_fromUtf8(""))
        self.Button_ColorDummy.setObjectName(_fromUtf8("Button_ColorDummy"))
        self.Button_RestoreCurrElement = QtGui.QPushButton(WindowColor_Dialog)
        self.Button_RestoreCurrElement.setGeometry(QtCore.QRect(420, 120, 161, 23))
        self.Button_RestoreCurrElement.setObjectName(_fromUtf8("Button_RestoreCurrElement"))
        self.Button_RestoreCurrContext = QtGui.QPushButton(WindowColor_Dialog)
        self.Button_RestoreCurrContext.setGeometry(QtCore.QRect(420, 150, 161, 23))
        self.Button_RestoreCurrContext.setObjectName(_fromUtf8("Button_RestoreCurrContext"))
        self.Button_RestoreAllContext = QtGui.QPushButton(WindowColor_Dialog)
        self.Button_RestoreAllContext.setGeometry(QtCore.QRect(420, 180, 161, 23))
        self.Button_RestoreAllContext.setObjectName(_fromUtf8("Button_RestoreAllContext"))
        self.widget_Preview = QtGui.QWidget(WindowColor_Dialog)
        self.widget_Preview.setGeometry(QtCore.QRect(10, 210, 401, 171))
        self.widget_Preview.setObjectName(_fromUtf8("widget_Preview"))
        self.label_3 = QtGui.QLabel(WindowColor_Dialog)
        self.label_3.setGeometry(QtCore.QRect(10, 190, 161, 16))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.label_4 = QtGui.QLabel(WindowColor_Dialog)
        self.label_4.setGeometry(QtCore.QRect(420, 10, 161, 16))
        self.label_4.setObjectName(_fromUtf8("label_4"))

        self.retranslateUi(WindowColor_Dialog)
        QtCore.QObject.connect(self.Button_ApplyClose, QtCore.SIGNAL(_fromUtf8("clicked()")), WindowColor_Dialog.Button_ApplyClose_Pressed)
        QtCore.QObject.connect(self.Button_Cancel, QtCore.SIGNAL(_fromUtf8("clicked()")), WindowColor_Dialog.Button_Cancel_Pressed)
        QtCore.QObject.connect(self.Button_Help, QtCore.SIGNAL(_fromUtf8("clicked()")), WindowColor_Dialog.ButtonHELP_Pressed)
        QtCore.QObject.connect(self.Button_RestoreCurrElement, QtCore.SIGNAL(_fromUtf8("clicked()")), WindowColor_Dialog.Button_RestoreCurrElement_clicked)
        QtCore.QObject.connect(self.Button_RestoreCurrContext, QtCore.SIGNAL(_fromUtf8("clicked()")), WindowColor_Dialog.Button_RestoreCurrContext_clicked)
        QtCore.QObject.connect(self.Button_RestoreAllContext, QtCore.SIGNAL(_fromUtf8("clicked()")), WindowColor_Dialog.Button_RestoreAllContext_clicked)
        QtCore.QMetaObject.connectSlotsByName(WindowColor_Dialog)

    def retranslateUi(self, WindowColor_Dialog):
        WindowColor_Dialog.setWindowTitle(_translate("WindowColor_Dialog", "Drawing window Colors", None))
        self.Button_Cancel.setText(_translate("WindowColor_Dialog", "Cancel", None))
        self.Button_Help.setText(_translate("WindowColor_Dialog", "Help", None))
        self.Button_ApplyClose.setText(_translate("WindowColor_Dialog", "Apply && Close", None))
        self.label.setText(_translate("WindowColor_Dialog", "Context:", None))
        self.label_2.setText(_translate("WindowColor_Dialog", "Interface element:", None))
        self.Button_RestoreCurrElement.setText(_translate("WindowColor_Dialog", "Restore current element", None))
        self.Button_RestoreCurrContext.setText(_translate("WindowColor_Dialog", "Restore current context", None))
        self.Button_RestoreAllContext.setText(_translate("WindowColor_Dialog", "Restore all context", None))
        self.label_3.setText(_translate("WindowColor_Dialog", "Preview:", None))
        self.label_4.setText(_translate("WindowColor_Dialog", "Color:", None))

