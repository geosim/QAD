# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire la finestra testuale
 
                              -------------------
        begin                : 2013-05-22
        copyright            : (C) 2013 IREN Acqua Gas SpA
        email                : geosim.dev@irenacquagas.it
        developers           : roberto poltini (roberto.poltini@irenacquagas.it)
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import sys
import string

import qad_debug
from qad_ui_textwindow import Ui_QadTextWindow, Ui_QadCmdSuggestWindow
from qad_msg import QadMsg
import qad_utils
from qad_snapper import *


#===============================================================================
# QadInputTypeEnum class.
#===============================================================================
class QadInputTypeEnum():
   NONE     = 0    # nessuno
   COMMAND  = 1    # nome di un comando
   POINT2D  = 2    # punto 
   POINT3D  = 4    # punto 
   KEYWORDS = 8    # una parola chiave
   STRING   = 16   # una stringa
   INT      = 32   # un numero intero
   LONG     = 64   # un numero intero
   FLOAT    = 128  # un numero reale
   BOOL     = 256  # un valore booleano
   ANGLE    = 512  # un valore reale in gradi


#===============================================================================
# QadInputModeEnum class.
#===============================================================================
class QadInputModeEnum():
   NONE         = 0
   NOT_NULL     = 1   # inserimento nullo non permesso
   NOT_ZERO     = 2   # valore zero non permesso 
   NOT_NEGATIVE = 4   # valore negativo non permesso 
   NOT_POSITIVE = 8   # valore positivo non permesso  

        
#===============================================================================
# QadTextWindow
#===============================================================================
class QadTextWindow(QDockWidget, Ui_QadTextWindow, object):
   """This class 
   """
    
   def __init__(self, plugin):
      """The constructor."""

      QDockWidget.__init__(self, None)
      self.setupUi(self)
      self.setAllowedAreas(Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
      self.plugin = plugin
                
   def initGui(self):
      self.edit = QadEdit(self)
      self.edit.setObjectName("QadTextEdit")
      self.vboxlayout.addWidget(self.edit)

      # Inizializzo la finestra per il suggerimento dei comandi
      self.edit.cmdSuggestWindow.initGui()
      self.edit.cmdSuggestWindow.show(False)
                  
   def setFocus(self):
      self.edit.setFocus()
      
   def keyPressEvent(self, e):
      self.edit.keyPressEvent(e)
        
   def toggleShow(self):
      if self.isVisible():          
         self.hide()
      else:
         self.show()
         
   def showMsg(self, msg, displayPrompt = False):
      self.edit.insertPlainText(msg)
      if displayPrompt:
         self.edit.displayPrompt() # ripete il prompt      

   def showInputMsg(self, inputMsg = None, inputType = QadInputTypeEnum.COMMAND, \
                    default = None, keyWords = "", inputMode = QadInputModeEnum.NOT_NULL):
      # il valore di default del parametro di una funzione non può essere una traduzione
      # perchè lupdate.exe non lo riesce ad interpretare
      if inputMsg is None: 
         inputMsg = QadMsg.translate("QAD", "Comando: ")
         
      self.edit.displayPrompt(inputMsg)
      self.edit.inputType = inputType
      self.edit.default = default
      if inputType & QadInputTypeEnum.KEYWORDS and (keyWords is not None):         
         self.edit.keyWords = keyWords.split(" ")
      self.edit.inputMode = inputMode

   def showErr(self, err):
      self.showMsg(err, True) # ripete il prompt
  
   def showEvaluateMsg(self, msg = None):
      self.edit.showEvaluateMsg(msg)

   def getCurrMsg(self):
      return self.edit.getCurrMsg()

   def getHistory(self):
      return self.edit.history # list

   def updateHistory(self, command):
      return self.edit.updateHistory(command)
               
   def runCommand(self, cmd):
      self.plugin.runCommand(cmd)      
      
   def continueCommand(self, cmd):
      self.plugin.continueCommandFromTextWindow(cmd)      
      
   def abortCommand(self):
      self.plugin.abortCommand()      

   def isValidCommand(self, cmd):
      return self.plugin.isValidCommand(cmd)      

   def getCommandNames(self):
      return self.plugin.getCommandNames()

   def getCommandObj(self, cmdName):
      return self.plugin.getCommandObj(cmdName)

   def forceCommandMapToolSnapTypeOnce(self, snapType, snapParams = None):
      return self.plugin.forceCommandMapToolSnapTypeOnce(snapType, snapParams)      

   def toggleOsMode(self):
      return self.plugin.toggleOsMode()      

   def toggleOrthoMode(self):
      return self.plugin.toggleOrthoMode()      

   def togglePolarMode(self):
      return self.plugin.togglePolarMode()      

   def getLastPoint(self):
      return self.plugin.lastPoint

   def getCurrenPointFromCommandMapTool(self):
      return self.plugin.getCurrenPointFromCommandMapTool()
   
     
#===============================================================================
# QadEdit
#===============================================================================
class QadEdit(QTextEdit):

   parent = None # plug in parente
   inputType = QadInputTypeEnum.COMMAND
   keyWords = []
   default = None
   inputMode = QadInputModeEnum.NONE
   
   def __init__(self, parent):
      QTextEdit.__init__(self)

      self.parent = parent

      self.setTextInteractionFlags(Qt.TextEditorInteraction)
      self.setAcceptDrops(False) # non accetta drag & drop
      self.setMinimumSize(30, 30)
      self.setUndoRedoEnabled(False)
      self.setAcceptRichText(False)
   
      self.buffer = []
   
      self.displayPrompt(QadMsg.translate("QAD", "Comando: "))

      self.history = []
      self.historyIndex = 0
   
      # Creo la finestra per il suggerimento dei comandi
      # lista composta da elementi con <nome comando>, <icona>, <note>
      infoCmds = []   
      for cmdName in parent.getCommandNames():
         cmd = parent.getCommandObj(cmdName)
         if cmd is not None:
            infoCmds.append([cmdName, cmd.getIcon(), cmd.getNote()])
      self.cmdSuggestWindow = QadCmdSuggestWindow(self, infoCmds)      
   
   def isCursorInEditionZone(self):
      cursor = self.textCursor()
      pos = cursor.position()
      block = self.document().lastBlock()
      last = block.position() + self.currentPromptLength
      return pos >= last

   def currentCommand(self):
      block = self.cursor.block()
      text = block.text()
      return text[self.currentPromptLength:]

   def showPrevious(self):
      if self.historyIndex < len(self.history) and len(self.history) > 0:
         self.historyIndex += 1
         if self.historyIndex == len(self.history):
            self.substituteText("")
         else:
            self.substituteText(self.history[self.historyIndex])
         
#          self.cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.MoveAnchor)
#          self.cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
#          self.cursor.removeSelectedText()
#          self.cursor.insertText(self.currentPrompt)
#          self.historyIndex += 1
#          if self.historyIndex == len(self.history):
#             self.insertPlainText("")
#          else:
#             self.insertPlainText(self.history[self.historyIndex])
                
   def showNext(self):
      if  self.historyIndex > 0 and len(self.history) > 0:
         self.historyIndex -= 1
         if self.historyIndex == len(self.history):
            self.substituteText("")
         else:
            self.substituteText(self.history[self.historyIndex])

#          self.cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.MoveAnchor)
#          self.cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
#          self.cursor.removeSelectedText()
#          self.cursor.insertText(self.currentPrompt)
#          self.historyIndex -= 1
#          if self.historyIndex == len(self.history):
#             self.insertPlainText("")
#          else:
#             self.insertPlainText(self.history[self.historyIndex])
               
   def showLast(self):
      if len(self.history) > 0:
         self.substituteText(self.history[len(self.history) - 1])
#          self.cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.MoveAnchor)
#          self.cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
#          self.cursor.removeSelectedText()
#          self.cursor.insertText(self.currentPrompt)
#          self.insertPlainText(self.history[len(self.history) - 1])
         return self.history[len(self.history) - 1]
      else:
         return ""
      
   def substituteText(self, text):
      self.cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.MoveAnchor)
      self.cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
      self.cursor.removeSelectedText()
      self.cursor.insertText(self.currentPrompt)
      self.insertPlainText(text)      

   def updateHistory(self, command):
      # Se command è una lista di comandi
      if isinstance(command, list):
         for line in command:
            self.updateHistory(line)
      elif not command == "":
         # se lo storico è vuoto o se il comando da inserire è diverso dall'ultimo
         if len(self.history) <= 0 or command != self.history[-1]: 
            self.history.append(command)
            
         self.historyIndex = len(self.history)
       
   def keyPressEvent(self, e):
      #qad_debug.breakPoint()
      self.cursor = self.textCursor()

      if self.inputType & QadInputTypeEnum.COMMAND:
         self.cmdSuggestWindow.show(False)

      #QMessageBox.warning(self.plugIn.TextWindow, "titolo" , 'msg')      

      # Se è stato premuto il tasto CTRL (o META) + 9
      if ((e.modifiers() & Qt.ControlModifier) or (e.modifiers() & Qt.MetaModifier)) and \
         e.key() == Qt.Key_9:
         # Accendo o spengo la finestra di testo
         self.parent.toggleShow()
         return

      # Se è stato premuto il tasto F10
      if e.key() == Qt.Key_F10:
         # Attivo o disattivo lo snap
         self.parent.togglePolarMode()
         return

      # Se è stato premuto il tasto F3
      if e.key() == Qt.Key_F3:
         # Attivo o disattivo lo snap
         self.parent.toggleOsMode()
         return

      # Se è stato premuto il tasto F8
      if e.key() == Qt.Key_F8:
         # Attivo o disattivo la modalità ortogonale
         self.parent.toggleOrthoMode()
         return
      
      if e.key() == Qt.Key_Escape:
         self.parent.abortCommand()
         return
      
      # if the cursor isn't in the edition zone, don't do anything except Ctrl+C
      if not self.isCursorInEditionZone():
         if e.modifiers() & Qt.ControlModifier or e.modifiers() & Qt.MetaModifier:
            if e.key() == Qt.Key_C or e.key() == Qt.Key_A:
               QTextEdit.keyPressEvent(self, e)
         else:
            # all other keystrokes get sent to the input line
            self.cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
                                    
         self.setTextCursor(self.cursor)
         self.ensureCursorVisible()
      else:
         # if Return is pressed, then perform the commands
         if e.key() == Qt.Key_Return:
            self.entered()
         elif e.key() == Qt.Key_Space and self.inputType & QadInputTypeEnum.COMMAND:            
            self.entered()          
         # if Up or Down is pressed
         elif e.key() == Qt.Key_Down:
            self.showPrevious()
         elif e.key() == Qt.Key_Up:
            self.showNext()
         # if backspace is pressed, delete until we get to the prompt
         elif e.key() == Qt.Key_Backspace:
            if not self.cursor.hasSelection() and self.cursor.columnNumber() == self.currentPromptLength:
               return
            QTextEdit.keyPressEvent(self, e)
         # if the left key is pressed, move left until we get to the prompt
         elif e.key() == Qt.Key_Left and self.cursor.position() > self.document().lastBlock().position() + self.currentPromptLength:
            anchor = QTextCursor.KeepAnchor if e.modifiers() & Qt.ShiftModifier else QTextCursor.MoveAnchor
            move = QTextCursor.WordLeft if e.modifiers() & Qt.ControlModifier or e.modifiers() & Qt.MetaModifier else QTextCursor.Left
            self.cursor.movePosition(move, anchor)
         # use normal operation for right key
         elif e.key() == Qt.Key_Right:
            anchor = QTextCursor.KeepAnchor if e.modifiers() & Qt.ShiftModifier else QTextCursor.MoveAnchor
            move = QTextCursor.WordRight if e.modifiers() & Qt.ControlModifier or e.modifiers() & Qt.MetaModifier else QTextCursor.Right
            self.cursor.movePosition(move, anchor)
         # if home is pressed, move cursor to right of prompt
         elif e.key() == Qt.Key_Home:
            anchor = QTextCursor.KeepAnchor if e.modifiers() & Qt.ShiftModifier else QTextCursor.MoveAnchor
            self.cursor.movePosition(QTextCursor.StartOfBlock, anchor, 1)
            self.cursor.movePosition(QTextCursor.Right, anchor, self.currentPromptLength)
         # use normal operation for end key
         elif e.key() == Qt.Key_End:
            anchor = QTextCursor.KeepAnchor if e.modifiers() & Qt.ShiftModifier else QTextCursor.MoveAnchor
            self.cursor.movePosition(QTextCursor.EndOfBlock, anchor, 1)
         # use normal operation for all remaining keys
         else:
            QTextEdit.keyPressEvent(self, e)

         self.setTextCursor(self.cursor)
         self.ensureCursorVisible()
   
         if self.inputType & QadInputTypeEnum.COMMAND:
            self.cmdSuggestWindow.show(True, self.getCurrMsg())
      
   def entered(self):
      if self.inputType & QadInputTypeEnum.COMMAND:
         self.cmdSuggestWindow.show(False)
      self.cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
      self.setTextCursor(self.cursor)
      self.evaluate( unicode(self.currentCommand()) )
      
   def displayPrompt(self, prompt = None):
      self.insertPlainText("\n")
      if prompt is not None:
         self.currentPrompt = prompt
      self.currentPromptLength = len(self.currentPrompt)
      self.insertTaggedLine(self.currentPrompt, ConsoleHighlighter.EDIT_LINE)
      self.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)

   def insertTaggedText(self, txt, tag):
      if len(txt) > 0 and txt[-1] == '\n': # remove trailing newline to avoid one more empty line
         txt = txt[0:-1]

      c = self.textCursor()
      for line in txt.split('\n'):
         b = c.block()
         b.setUserState(tag)
         c.insertText(line)
         c.insertBlock()

   def insertTaggedLine(self, txt, tag):
      c = self.textCursor()
      b = c.block()
      b.setUserState(tag)
      c.insertText(txt)

   def showEvaluateMsg(self, msg = None):
      """
      mostra e valuta il messaggio msg se diverso da None altrimenti usa il messaggio corrente
      """
      self.cursor = self.textCursor()
      if msg is not None:
         self.substituteText(msg)         
      self.entered()

   def getCurrMsg(self):
      """
      restituisce il messaggio già presente nella finestra di testo
      """
      self.cursor = self.textCursor()
      prevPos = self.cursor.position()
      self.cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
      self.setTextCursor(self.cursor)
      msg = unicode(self.currentCommand())
      self.cursor.setPosition(prevPos)
      return msg


   def getInvalidInputMsg(self):
      """
      restituisce il messaggio di input non valido
      """
      if self.inputType & QadInputTypeEnum.POINT2D or \
         self.inputType & QadInputTypeEnum.POINT3D:
         if self.inputType & QadInputTypeEnum.KEYWORDS and \
            (self.inputType & QadInputTypeEnum.FLOAT or self.inputType & QadInputTypeEnum.ANGLE):
            return QadMsg.translate("QAD", "\nÈ richiesto un punto, un numero reale o la parola chiave di un'opzione.\n")
         elif self.inputType & QadInputTypeEnum.KEYWORDS:
            return QadMsg.translate("QAD", "\nÈ richiesto un punto o la parola chiave di un'opzione.\n")
         elif self.inputType & QadInputTypeEnum.FLOAT or self.inputType & QadInputTypeEnum.ANGLE:
            return QadMsg.translate("QAD", "\nÈ richiesto un punto o un numero reale.\n")
         else:
            return QadMsg.translate("QAD", "\nPunto non valido.\n")         
      elif self.inputType & QadInputTypeEnum.KEYWORDS:
         return QadMsg.translate("QAD", "\nParola chiave dell'opzione non valida.\n")
      elif self.inputType & QadInputTypeEnum.STRING:
         return QadMsg.translate("QAD", "\nStringa non valida.\n")
      elif self.inputType & QadInputTypeEnum.INT:
         return QadMsg.translate("QAD", "\nNumero intero non valido.\n")
      elif self.inputType & QadInputTypeEnum.LONG:
         return QadMsg.translate("QAD", "\nNumero intero lungo non valido.\n")
      elif self.inputType & QadInputTypeEnum.FLOAT or self.inputType & QadInputTypeEnum.ANGLE:
         return QadMsg.translate("QAD", "\nNumero reale non valido.\n")
      elif self.inputType & QadInputTypeEnum.BOOL:
         return QadMsg.translate("QAD", "\nValore booleano non valido.\n")
      else:
         return ""
      

   def evaluateKeyWords(self, cmd):
      #qad_debug.breakPoint()
      # The required portion of the keyword is specified in uppercase characters, 
      # and the remainder of the keyword is specified in lowercase characters.
      # The uppercase abbreviation can be anywhere in the keyword
      if cmd == "": # se cmd = "" la funzione find ritorna 0 (no comment)
         return None
      upperCmd = cmd.upper()
      selectedKeyWords = []
      for keyWord in self.keyWords:
         #qad_debug.breakPoint()
         # estraggo la parte maiuscola della paola chiave
         upperPart = ""
         for letter in keyWord:
            if letter.isupper():
               upperPart = upperPart + letter
            elif len(upperPart) > 0:
               break
         
         if upperPart.find(upperCmd) == 0: # se la parte maiuscola della parola chiave inizia per upperCmd
            if upperPart == upperCmd: # Se uguale
               return keyWord
            else:
               selectedKeyWords.append(keyWord)
         elif keyWord.upper().find(upperCmd) == 0: # se la parola chiave inizia per cmd (insensitive)
            if keyWord.upper() == upperCmd: # Se uguale
               return keyWord
            else:
               selectedKeyWords.append(keyWord)

      selectedKeyWordsLen = len(selectedKeyWords)
      if selectedKeyWordsLen == 0:
         return None
      elif selectedKeyWordsLen == 1:
         return selectedKeyWords[0]
      else:
         self.insertPlainText(QadMsg.translate("QAD", "\nRisposta ambigua: specificare con maggior chiarezza...\n"))            
         Msg = ""         
         for keyWord in selectedKeyWords:
            if Msg == "":
               Msg = keyWord
            else:
               Msg = Msg + QadMsg.translate("QAD", " o ") + keyWord

         Msg = Msg + QadMsg.translate("QAD", " ?\n")
         self.insertPlainText(Msg)            
         
      return None
   
   def evaluate(self, cmd):      
      #------------------------------------------------------------------------------
      # nome di un comando
      #------------------------------------------------------------------------------ 
      if self.inputType & QadInputTypeEnum.COMMAND:
         if cmd == "":
            cmd = unicode(self.showLast()) # ripeto ultimo comando
         
         if self.parent.isValidCommand(cmd):
            self.updateHistory(cmd)
            self.parent.runCommand(cmd)
         else:
            msg = QadMsg.translate("QAD", "\nComando sconosciuto \"{0}\".")
            self.insertPlainText(msg.format(cmd.encode('ascii','ignore')))
            self.displayPrompt() # ripete il prompt
         return

      if cmd == "":
         if self.default is not None:
            if type(self.default) == QgsPoint:
               cmd = self.default.toString()
            else:
               cmd = unicode(self.default)              
               
         if cmd == "" and \
            not (self.inputMode & QadInputModeEnum.NOT_NULL): # permesso input nullo              
            self.parent.continueCommand(None)         
            return
                       
      #------------------------------------------------------------------------------
      # punto 2D
      #------------------------------------------------------------------------------ 
      if self.inputType & QadInputTypeEnum.POINT2D:
         snapType = qad_utils.str2snapTypeEnum(cmd)
         if snapType != QadSnapTypeEnum.NONE:
            # se è stato forzato uno snap
            snapParams = qad_utils.str2snapParams(cmd)
            self.parent.forceCommandMapToolSnapTypeOnce(snapType, snapParams)
            self.insertPlainText(QadMsg.translate("QAD", "\n(impostato snap temporaneo)\n"))
            self.displayPrompt()          
            return
         if (self.inputType & QadInputTypeEnum.INT) or \
            (self.inputType & QadInputTypeEnum.LONG) or \
            (self.inputType & QadInputTypeEnum.FLOAT) or \
            (self.inputType & QadInputTypeEnum.ANGLE) or \
            (self.inputType & QadInputTypeEnum.BOOL):
            oneNumberAllowed = False
         else:
            oneNumberAllowed = True
            
         pt = qad_utils.str2QgsPoint(cmd, \
                                     self.parent.getLastPoint(), \
                                     self.parent.getCurrenPointFromCommandMapTool(), \
                                     oneNumberAllowed)
                      
         if pt is not None:
            self.parent.continueCommand(pt)
            return
            
      #------------------------------------------------------------------------------
      # punto 3D
      #------------------------------------------------------------------------------ 
      if self.inputType & QadInputTypeEnum.POINT3D: # punto
         pass
      
      #------------------------------------------------------------------------------
      # una parola chiave
      #------------------------------------------------------------------------------ 
      if self.inputType & QadInputTypeEnum.KEYWORDS:
         keyWord = self.evaluateKeyWords(cmd)
               
         if keyWord is not None:
            self.parent.continueCommand(keyWord)
            return       
                      
      #------------------------------------------------------------------------------
      # una stringa
      #------------------------------------------------------------------------------ 
      if self.inputType & QadInputTypeEnum.STRING:            
         if cmd is not None:            
            self.parent.continueCommand(cmd)
            return       
                     
      #------------------------------------------------------------------------------
      # un numero intero
      #------------------------------------------------------------------------------ 
      if self.inputType & QadInputTypeEnum.INT:
         num = qad_utils.str2int(cmd)
         if num == 0 and (self.inputMode & QadInputModeEnum.NOT_ZERO): # non permesso valore = 0              
            num = None
         elif num < 0 and (self.inputMode & QadInputModeEnum.NOT_NEGATIVE): # non permesso valore < 0              
            num = None
         elif num > 0 and (self.inputMode & QadInputModeEnum.NOT_POSITIVE): # non permesso valore > 0              
            num = None
               
         if num is not None:
            self.parent.continueCommand(int(num))
            return       
                     
      #------------------------------------------------------------------------------
      # un numero lungo
      #------------------------------------------------------------------------------ 
      if self.inputType & QadInputTypeEnum.LONG:
         num = qad_utils.str2long(cmd)
         if num == 0 and (self.inputMode & QadInputModeEnum.NOT_ZERO): # non permesso valore = 0              
            num = None
         elif num < 0 and (self.inputMode & QadInputModeEnum.NOT_NEGATIVE): # non permesso valore < 0              
            num = None
         elif num > 0 and (self.inputMode & QadInputModeEnum.NOT_POSITIVE): # non permesso valore > 0              
            num = None
            
         if num is not None:
            self.parent.continueCommand(long(num))
            return       
                     
      #------------------------------------------------------------------------------
      # un numero reale
      #------------------------------------------------------------------------------ 
      if self.inputType & QadInputTypeEnum.FLOAT or self.inputType & QadInputTypeEnum.ANGLE:
         num = qad_utils.str2float(cmd)
         if num == 0 and (self.inputMode & QadInputModeEnum.NOT_ZERO): # non permesso valore = 0              
            num = None
         elif num < 0 and (self.inputMode & QadInputModeEnum.NOT_NEGATIVE): # non permesso valore < 0              
            num = None
         elif num > 0 and (self.inputMode & QadInputModeEnum.NOT_POSITIVE): # non permesso valore > 0              
            num = None
            
         if num is not None:
            if self.inputType & QadInputTypeEnum.ANGLE: # se è un angolo in gradi
               # i gradi vanno convertiti in radianti
               num = qad_utils.toRadians(num)            
            self.parent.continueCommand(float(num))         
            return       

      #------------------------------------------------------------------------------
      # un valore booleano
      #------------------------------------------------------------------------------ 
      elif self.inputType & QadInputTypeEnum.BOOL:
         value = qad_utils.str2bool(cmd)
            
         if value is not None:
            self.parent.continueCommand(value)
            return       

      self.insertPlainText(self.getInvalidInputMsg())
      self.displayPrompt()
         
      return
   
   
   def resizeEvent(self, e):
      QTextEdit.resizeEvent(self, e)
      self.cmdSuggestWindow.resizeEvent(e)

    
#===============================================================================
# ConsoleHighlighter
#===============================================================================
class ConsoleHighlighter(QSyntaxHighlighter):
   EDIT_LINE, ERROR, OUTPUT, INIT = range(4)
   
   def __init__(self, doc):
      QSyntaxHighlighter.__init__(self,doc)
      formats = { self.OUTPUT : Qt.black, self.ERROR : Qt.red, self.EDIT_LINE : Qt.darkGreen, self.INIT : Qt.gray }
      self.f = {}
      for tag, color in formats.iteritems():
         self.f[tag] = QTextCharFormat()
         self.f[tag].setForeground(color)

   def highlightBlock(self, txt):
      size = len(txt)
      state = self.currentBlockState()
      if state == self.OUTPUT or state == self.ERROR or state == self.INIT:
         self.setFormat(0,size, self.f[state])
      # highlight prompt only
      if state == self.EDIT_LINE:
         self.setFormat(0,3, self.f[self.EDIT_LINE]) 
         
         
#===============================================================================
# Ui_QadCmdSuggestWindow
#===============================================================================
class QadCmdSuggestWindow(QWidget, Ui_QadCmdSuggestWindow, object):
         
   def __init__(self, parent, infoCmds):
      # lista composta da elementi con <nome comando>, <icona>, <note>     
      QWidget.__init__(self, parent)
      self.setupUi(self)
      self.parent = parent
      self.infoCmds = infoCmds[:] # copio la lista
                 
   def initGui(self):
      self.cmdNamesListView = QadCmdSuggestListView(self)
      self.cmdNamesListView.setObjectName("QadCmdNamesListView")
      self.vboxlayout.addWidget(self.cmdNamesListView)
      
   def setFocus(self):
      self.cmdNamesListView.setFocus()
      
   def keyPressEvent(self, e):
      self.cmdNamesListView.keyPressEvent(e)
         
   def show(self, mode = True, filter = ""):
      if mode == True:
         filteredInfoCmds = []
         upperFilter = filter.strip().upper()
         if len(upperFilter) > 0:               
            # lista composta da elementi con <nome comando>, <icona>, <note>     
            for infoCmd in self.infoCmds:
               if string.find(infoCmd[0].upper(), upperFilter) == 0 or filter == "*": # se incomincia per
                  filteredInfoCmds.append(infoCmd)
                  
         if len(filteredInfoCmds) == 0:
            self.setVisible(False)
         else:
            self.cmdNamesListView.set(filteredInfoCmds)
            self.setVisible(True)
            self.move(self.parent.width() - self.width() - 15, 0)
      else:
         self.setVisible(False)

   def resizeEvent(self, e):
      h = self.parent.height()
      self.resize(200, self.parent.height())
      self.move(self.parent.width() - self.width() - 15, 0)

   def substituteText(self, cmd):
      self.show(False)
      self.parent.setFocus()
      self.parent.showEvaluateMsg(cmd)
         
#===============================================================================
# QadCmdListView
#===============================================================================
class QadCmdSuggestListView(QListView):

   parent = None # plug in parente
   
   def __init__(self, parent):
      QListView.__init__(self)

      self.parent = parent

      self.setViewMode(QListView.ListMode)
      self.setSelectionBehavior(QAbstractItemView.SelectItems)
      self.setUniformItemSizes(True)
      self.model = QStandardItemModel()
      self.setModel(self.model)
            
   def set(self, filteredCmdNames):
      # lista composta da elementi con <nome comando>, <icona>, <note>     
      self.model.clear()

      for infoCmd in filteredCmdNames:
         cmdName = infoCmd[0]
         cmdIcon = infoCmd[1]
         cmdNote = infoCmd[2]
         if cmdIcon is None:        
            item = QStandardItem(cmdName)
         else:
            item = QStandardItem(cmdIcon, cmdName)
         
         if cmdNote is not None and len(cmdNote) > 0:
            item.setToolTip(cmdNote)
            
         item.setEditable(False)
         self.model.appendRow(item)
                     
   def keyPressEvent(self, e):
      # if Return is pressed, then perform the commands
      if e.key() == Qt.Key_Return:
         cmd = self.selectionModel().currentIndex().data()
         self.parent.substituteText(cmd)
      
   def mouseReleaseEvent(self, e):
      cmd = self.selectionModel().currentIndex().data()
      self.parent.substituteText(cmd)
      