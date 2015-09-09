# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire la finestra testuale
 
                              -------------------
        begin                : 2014-09-21
        copyright            : iiiii
        email                : hhhhh
        developers           : bbbbb aaaaa ggggg
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
# QadCmdOptionPos
#===============================================================================
class QadCmdOptionPos():      
   def __init__(self, name = "", initialPos = 0, finalPos = 0):
      self.name = name
      self.initialPos = initialPos
      self.finalPos = finalPos
   
   def isSelected(self, pos):
      return True if pos >= self.initialPos and pos <= self.finalPos else False


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
      self.cmdSuggestWindow = None
      self.connect(self, SIGNAL("topLevelChanged(bool)"), self.topLevelChanged)
                
   def initGui(self):
      self.chronologyEdit = QadChronologyEdit(self)
      self.chronologyEdit.setObjectName("QadChronologyEdit")
     
      self.edit = QadEdit(self, self.chronologyEdit)
      self.edit.setObjectName("QadTextEdit")
 
      self.edit.displayPrompt(QadMsg.translate("QAD", "Command: "))
      
      # Creo la finestra per il suggerimento dei comandi
      # lista composta da elementi con:
      # <nome locale comando>, <nome inglese comando>, <icona>, <note>
      infoCmds = []   
      for cmdName in self.getCommandNames():
         cmd = self.getCommandObj(cmdName[0])
         if cmd is not None:
            infoCmds.append([cmd.getName(), cmd.getEnglishName(), cmd.getIcon(), cmd.getNote()])
      self.cmdSuggestWindow = QadCmdSuggestWindow(self, infoCmds)      
      self.cmdSuggestWindow.initGui()
      self.cmdSuggestWindow.show(False)
                  
   def setFocus(self):
      self.edit.setFocus()
      
   def keyPressEvent(self, e):
      self.edit.keyPressEvent(e)

   def topLevelChanged(self, topLevel):
      self.resizeEdits
      self.setFocus()
      
   def toggleShow(self):
      if self.isVisible():          
         self.hide()
      else:
         self.show()
         
   def showMsg(self, msg, displayPromptAfterMsg = False):
      self.edit.showMsg(msg, displayPromptAfterMsg)

   def showInputMsg(self, inputMsg = None, inputType = QadInputTypeEnum.COMMAND, \
                    default = None, keyWords = "", inputMode = QadInputModeEnum.NONE):
      # il valore di default del parametro di una funzione non può essere una traduzione
      # perché lupdate.exe non lo riesce ad interpretare
      self.edit.showInputMsg(inputMsg, inputType, default, keyWords, inputMode)

   def showErr(self, err):
      self.showMsg(err, True) # ripete il prompt

   def showMsgOnChronologyEdit(self, msg):
      if self.chronologyEdit is not None:
         self.chronologyEdit.insertText(msg)

   def showCmdSuggestWindow(self, mode = True, filter = ""):
      if self.cmdSuggestWindow is not None:
         self.cmdSuggestWindow.show(mode, filter)
  
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

   def setLastPoint(self, pt):
      return self.plugin.setLastPoint(pt)

   def getCurrenPointFromCommandMapTool(self):
      return self.plugin.getCurrenPointFromCommandMapTool()

   def resizeEdits(self):
      if self.edit is None or self.chronologyEdit is None:
         return
            
      rect = self.rect()
      h = rect.height()
      w = rect.width()
   
      editHeight = self.edit.getOptimalHeight()
      if editHeight > h:
         editHeight = h
      chronologyEditHeight = h - editHeight
      if not self.isFloating():
         offsetY = 20
         chronologyEditHeight = chronologyEditHeight - offsetY
      else:            
         offsetY = 0
                  
      if chronologyEditHeight < 0:
         chronologyEditHeight = 0
      
      self.chronologyEdit.move(0, offsetY)
      self.chronologyEdit.resize(w, chronologyEditHeight)     
      self.chronologyEdit.ensureCursorVisible()
      
      self.edit.resize(w, editHeight)
      self.edit.move(0, chronologyEditHeight + offsetY)
      self.edit.ensureCursorVisible()
      

   def resizeEvent(self, e):
      if self:
         self.resizeEdits()
         self.cmdSuggestWindow.resizeEvent(e)
        
#===============================================================================
# QadChronologyEdit
#===============================================================================
class QadChronologyEdit(QTextEdit):
   
   def __init__(self, parent):
      QTextEdit.__init__(self, parent)
      
      self.set_Colors()
      self.setReadOnly(True)
      self.setMinimumSize(0, 1)
   
   def set_Colors(self, foregroundColor = Qt.black, backGroundColor = Qt.lightGray):
      p = self.palette()
      p.setColor(QPalette.Base, backGroundColor)
      self.setPalette(p)
      self.setTextColor(foregroundColor)
      self.setTextBackgroundColor(backGroundColor) 

   def insertText(self, txt):
      cursor = self.textCursor()
      for line in txt.split('\n'):
         if len(line) > 0: # to avoid one more empty line         
            cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor) # fine documento
            self.setTextCursor(cursor)
            self.insertPlainText('\n' + line)
      cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor) # fine documento
      self.setTextCursor(cursor)
      self.ensureCursorVisible()
  
           
#===============================================================================
# QadEdit
#===============================================================================
class QadEdit(QTextEdit):
   PROMPT, KEY_WORDS = range(2)
   
   def __init__(self, parent, chronologyEdit):
      QTextEdit.__init__(self, parent)

      self.currentPrompt = ""
      self.currentPromptLength = 0

      self.inputType = QadInputTypeEnum.COMMAND
      self.default = None 
      self.inputMode = QadInputModeEnum.NONE

      self.setTextInteractionFlags(Qt.TextEditorInteraction)
      self.setMinimumSize(30, 21)
      self.setUndoRedoEnabled(False)
      self.setAcceptRichText(False)
      self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
      self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
   
      self.buffer = []
   
      self.history = []
      self.historyIndex = 0

      # stringa contenente le parole chiave separate da "/".
      # la stringa può contenere il carattere speciale "_" per separare le parole chiave
      # in lingua locale da quelle in inglese (es. "Si/No/Altra opzione_Yes/No/Other option")
      self.englishKeyWords = [] # parole chiave in inglese
      self.cmdOptionPosList = [] # lista delle posizioni delle opzioni del comando corrente
      self.currentCmdOptionPos = None

      self.upperKeyWordForegroundColor = Qt.blue
      self.keyWordBackGroundColor = QColor(210, 210, 210)
      self.keyWordHighlightBackGroundColor = Qt.gray
      
      self.tcf_normal = QTextCharFormat()
      self.tcf_history = QTextCharFormat()
      self.tcf_keyWord = QTextCharFormat()
      self.tcf_upperKeyWord = QTextCharFormat()
      self.tcf_highlightKeyWord = QTextCharFormat()
      self.tcf_highlightUpperKeyWord = QTextCharFormat()
      self.set_Colors()
      self.set_keyWordColors()

      self.setMouseTracking(True)
      QObject.connect(self, SIGNAL("textChanged()"), self.onTextChanged)

   def set_Colors(self, foregroundColor = Qt.black, backGroundColor = Qt.white, history_ForegroundColor = Qt.blue, \
                  history_BackGroundColor = Qt.gray):
      self.tcf_normal.setForeground(foregroundColor)     
      self.tcf_normal.setBackground(backGroundColor)
      self.tcf_normal.setFontWeight(QFont.Normal)
      
      self.tcf_history.setForeground(history_ForegroundColor)     
      self.tcf_history.setBackground(history_BackGroundColor)
      self.tcf_history.setFontWeight(QFont.Normal)

   def set_keyWordColors(self, backGroundColor = QColor(210, 210, 210), upperKeyWord_ForegroundColor = Qt.blue, \
                         highlightKeyWord_BackGroundColor = Qt.gray):
      self.tcf_keyWord.setBackground(backGroundColor)
      self.tcf_upperKeyWord.setForeground(upperKeyWord_ForegroundColor)
      self.tcf_upperKeyWord.setBackground(backGroundColor)
      self.tcf_upperKeyWord.setFontWeight(QFont.Bold)
               
      self.tcf_highlightKeyWord.setBackground(highlightKeyWord_BackGroundColor)         
      self.tcf_highlightUpperKeyWord.setForeground(upperKeyWord_ForegroundColor)
      self.tcf_highlightUpperKeyWord.setBackground(highlightKeyWord_BackGroundColor)
      self.tcf_highlightUpperKeyWord.setFontWeight(QFont.Bold)
   
   def setFormat(self, start, count, fmt): # 1-indexed
      if count == 0:
         return
      cursor = QTextCursor(self.textCursor())
      cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor) # inizio documento
      cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, start)
      cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, count)
      cursor.setCharFormat(fmt);
      self.setCurrentCharFormat(self.tcf_normal)
      
   def highlightKeyWords(self):
      lastBlock = self.document().lastBlock()
      txt = lastBlock.text()
      size = len(txt)
            
      # messaggio + "[" + opz1 + "/" + opz2 + "]"
      i = txt.find("[")
      final = txt.rfind("]")
      if i >= 0 and final > i: # se ci sono opzioni
         i = i + 1
         pos = lastBlock.position() + i
         while i < final:
            if txt[i] != "/":
               # se c'é un'opzione corrente deve essere evidenziata in modo diverso
               if self.currentCmdOptionPos is not None and \
                  pos >= self.currentCmdOptionPos.initialPos and \
                  pos <= self.currentCmdOptionPos.finalPos :                  
                  if txt[i].isupper():
                     self.setFormat(pos, 1, self.tcf_highlightUpperKeyWord)
                  else:
                     self.setFormat(pos, 1, self.tcf_highlightKeyWord)            
               else:
                  if txt[i].isupper():
                     self.setFormat(pos, 1, self.tcf_upperKeyWord)
                  else:
                     self.setFormat(pos, 1, self.tcf_keyWord)            
            i = i + 1
            pos = pos + 1
   
   
   def isCursorInEditionZone(self, newPos = None):
      cursor = self.textCursor()
      if newPos is None:
         pos = cursor.position()
      else:
         pos = newPos
      block = self.document().lastBlock()
      last = block.position() + self.currentPromptLength
      return pos >= last

   def currentCommand(self):
      block = self.textCursor().block()
      text = block.text()
      return text[self.currentPromptLength:]
      
   def showMsgOnChronologyEdit(self, msg):
      self.parentWidget().showMsgOnChronologyEdit(msg)           

   def showCmdSuggestWindow(self, mode = True, filter = ""):
      self.parentWidget().showCmdSuggestWindow(mode, filter)

   def showMsg(self, msg, displayPromptAfterMsg = False, append = True):      
      if len(msg) > 0:
         cursor = self.textCursor()
         sep = msg.rfind("\n")
         if sep >= 0:
            self.showMsgOnChronologyEdit(self.toPlainText() + msg[0:sep])
            newMsg = msg[sep + 1:]
            cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
         else:
            if append == True:
               cursor = self.textCursor()
               cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor) # fine documento
               newMsg = msg
            else:
               cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
               cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
               newMsg = self.currentPrompt + msg

         self.setTextCursor(cursor)
         self.insertPlainText(newMsg)         

         if self.inputType & QadInputTypeEnum.KEYWORDS:         
            self.textCursor().block().setUserState(QadEdit.KEY_WORDS)
            self.setCmdOptionPosList() # inizializzo la lista delle posizioni delle keyWords
            self.highlightKeyWords()
         else:            
            self.textCursor().block().setUserState(QadEdit.PROMPT)
            del self.cmdOptionPosList[:] # svuoto la lista delle posizioni delle keyWords
            
      if displayPromptAfterMsg:
         self.displayPrompt() # ripete il prompt


   def displayPrompt(self, prompt = None):
      if prompt is not None:
         self.currentPrompt = prompt        
      self.currentPromptLength = len(self.currentPrompt)     
      self.showMsg("\n" + self.currentPrompt)

   def displayKeyWordsPrompt(self, prompt = None):
      if prompt is not None:
         self.currentPrompt = prompt
      self.currentPromptLength = len(self.currentPrompt)
      self.showMsg("\n" + self.currentPrompt)
      
   def showNext(self):
      if self.historyIndex < len(self.history) and len(self.history) > 0:
         self.historyIndex += 1
         if self.historyIndex < len(self.history):
            # displayPromptAfterMsg = False, append = True
            self.showMsg(self.history[self.historyIndex], False, False) # sostituisce il testo dopo il prompt
                         
   def showPrevious(self):
      if self.historyIndex > 0 and len(self.history) > 0:
         self.historyIndex -= 1
         if self.historyIndex < len(self.history):
            # displayPromptAfterMsg = False, append = True
            self.showMsg(self.history[self.historyIndex], False, False) # sostituisce il testo dopo il prompt
               
   def showLast(self):
      if len(self.history) > 0:
         self.showMsg(self.history[len(self.history) - 1])
         return self.history[len(self.history) - 1]
      else:
         return ""

   def showInputMsg(self, inputMsg = None, inputType = QadInputTypeEnum.COMMAND, \
                    default = None, keyWords = "", inputMode = QadInputModeEnum.NONE):      
      # il valore di default del parametro di una funzione non può essere una traduzione
      # perché lupdate.exe non lo riesce ad interpretare
      if inputMsg is None: 
         inputMsg = QadMsg.translate("QAD", "Command: ")

      cursor = self.textCursor()
      actualPos = cursor.position()
         
      self.inputType = inputType
      self.default = default
      self.inputMode = inputMode
      if inputType & QadInputTypeEnum.KEYWORDS and (keyWords is not None):
         # carattere separatore tra le parole chiave in lingua locale e quelle in inglese 
         localEnglishKeyWords = keyWords.split("_")
         self.keyWords = localEnglishKeyWords[0].split("/") # carattere separatore delle parole chiave
         if len(localEnglishKeyWords) > 1:
            self.englishKeyWords = localEnglishKeyWords[1].split("/") # carattere separatore delle parole chiave
         else:
            del self.englishKeyWords[:]
         self.displayKeyWordsPrompt(inputMsg)
      else:
        self.displayPrompt(inputMsg)
                  
      return

   def setCmdOptionPosList(self):
      del self.cmdOptionPosList[:] # svuoto la lista
      lenKeyWords = len(self.keyWords)
      if lenKeyWords == 0 or len(self.currentPrompt) == 0:
         return
      # le opzioni sono racchiuse in parentesi quadre e separate tra loro da /
      prompt = self.currentPrompt
      initialPos = prompt.find("[", 0)
      finalDelimiter = prompt.find("]", initialPos)
      if initialPos == -1 or finalDelimiter == -1:
         return
      i = 0
      while i < lenKeyWords:
         keyWord = self.keyWords[i]
         initialPos = prompt.find(keyWord, initialPos + 1, finalDelimiter)
         if initialPos >= 0:
            finalPos = initialPos + len(keyWord)
            self.cmdOptionPosList.append(QadCmdOptionPos(keyWord, initialPos, finalPos))         
            initialPos = prompt.find("/", finalPos)
            if initialPos == -1:
               return
         
         i = i + 1

   def getCmdOptionPosUnderMouse(self, pos):
      cursor = self.cursorForPosition(pos)
      pos = cursor.position()
      for cmdOptionPos in self.cmdOptionPosList:
         if cmdOptionPos.isSelected(pos):
            return cmdOptionPos
      return None

   def mouseMoveEvent(self, event):
      self.currentCmdOptionPos = self.getCmdOptionPosUnderMouse(event.pos())
      self.highlightKeyWords()
      self.currentCmdOptionPos = None
   
   def mouseDoubleClickEvent(self, event):
      cursor = self.cursorForPosition(event.pos())
      pos = cursor.position()
      if self.isCursorInEditionZone(pos):
         QTextEdit.mouseDoubleClickEvent(self, event)
      
   def mousePressEvent(self, event):
      cursor = self.cursorForPosition(event.pos())
      pos = cursor.position()
      if self.isCursorInEditionZone(pos):
         QTextEdit.mousePressEvent(self, event)
   
   def mouseReleaseEvent(self, event):
      # se sono sull'ultima riga     
      if self.textCursor().position() >= self.document().lastBlock().position():
         if event.button() == Qt.LeftButton:
            cmdOptionPos = self.getCmdOptionPosUnderMouse(event.pos())
            if cmdOptionPos is not None:
               self.showEvaluateMsg(cmdOptionPos.name)
                           
   def updateHistory(self, command):
      # Se command é una lista di comandi
      if isinstance(command, list):
         for line in command:
            self.updateHistory(line)
      elif not command == "":
         # se lo storico é vuoto o se il comando da inserire é diverso dall'ultimo
         if len(self.history) <= 0 or command != self.history[-1]: 
            self.history.append(command)
            
         self.historyIndex = len(self.history)
       
   def keyPressEvent(self, e):
      cursor = self.textCursor()

      if self.inputType & QadInputTypeEnum.COMMAND:
         self.showCmdSuggestWindow(False)

      #QMessageBox.warning(self.plugIn.TextWindow, "titolo" , 'msg')      

      # Se é stato premuto il tasto CTRL (o META) + 9
      if ((e.modifiers() & Qt.ControlModifier) or (e.modifiers() & Qt.MetaModifier)) and \
         e.key() == Qt.Key_9:
         # Accendo o spengo la finestra di testo
         self.parentWidget().toggleShow()
         return

      # Se é stato premuto il tasto F10
      if e.key() == Qt.Key_F10:
         # Attivo o disattivo lo snap
         self.parentWidget().togglePolarMode()
         return

      # Se é stato premuto il tasto F3
      if e.key() == Qt.Key_F3:
         # Attivo o disattivo lo snap
         self.parentWidget().toggleOsMode()
         return

      # Se é stato premuto il tasto F8
      if e.key() == Qt.Key_F8:
         # Attivo o disattivo la modalità ortogonale
         self.parentWidget().toggleOrthoMode()
         return
      
      if e.key() == Qt.Key_Escape:
         self.parentWidget().abortCommand()
         return
      
      # if the cursor isn't in the edit zone, don't do anything except Ctrl+C
      if not self.isCursorInEditionZone():
         if e.modifiers() & Qt.ControlModifier or e.modifiers() & Qt.MetaModifier:
            if e.key() == Qt.Key_C or e.key() == Qt.Key_A:
               QTextEdit.keyPressEvent(self, e)
         else:
            # all other keystrokes get sent to the input line
            cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
            self.setTextCursor(cursor)
            QTextEdit.keyPressEvent(self, e)
                                    
         self.setTextCursor(cursor)
         self.ensureCursorVisible()
      else:
         # if Return is pressed, then perform the commands
         if e.key() == Qt.Key_Return:
            self.entered()
         elif e.key() == Qt.Key_Space and self.inputType & QadInputTypeEnum.COMMAND:            
            self.entered()          
         # if Up or Down is pressed
         elif e.key() == Qt.Key_Down:
            self.showNext()
         elif e.key() == Qt.Key_Up:
            self.showPrevious()
         # if backspace is pressed, delete until we get to the prompt
         elif e.key() == Qt.Key_Backspace:
            if not cursor.hasSelection() and cursor.columnNumber() == self.currentPromptLength:
               return
            QTextEdit.keyPressEvent(self, e)
         # if the left key is pressed, move left until we get to the prompt
         elif e.key() == Qt.Key_Left and cursor.position() > self.document().lastBlock().position() + self.currentPromptLength:
            anchor = QTextCursor.KeepAnchor if e.modifiers() & Qt.ShiftModifier else QTextCursor.MoveAnchor
            move = QTextCursor.WordLeft if e.modifiers() & Qt.ControlModifier or e.modifiers() & Qt.MetaModifier else QTextCursor.Left
            cursor.movePosition(move, anchor)
         # use normal operation for right key
         elif e.key() == Qt.Key_Right:
            anchor = QTextCursor.KeepAnchor if e.modifiers() & Qt.ShiftModifier else QTextCursor.MoveAnchor
            move = QTextCursor.WordRight if e.modifiers() & Qt.ControlModifier or e.modifiers() & Qt.MetaModifier else QTextCursor.Right
            cursor.movePosition(move, anchor)
         # if home is pressed, move cursor to right of prompt
         elif e.key() == Qt.Key_Home:
            anchor = QTextCursor.KeepAnchor if e.modifiers() & Qt.ShiftModifier else QTextCursor.MoveAnchor
            cursor.movePosition(QTextCursor.StartOfBlock, anchor, 1)
            cursor.movePosition(QTextCursor.Right, anchor, self.currentPromptLength)
         # use normal operation for end key
         elif e.key() == Qt.Key_End:
            anchor = QTextCursor.KeepAnchor if e.modifiers() & Qt.ShiftModifier else QTextCursor.MoveAnchor
            cursor.movePosition(QTextCursor.EndOfBlock, anchor, 1)
         # use normal operation for all remaining keys
         else:
            QTextEdit.keyPressEvent(self, e)

         self.setTextCursor(cursor)
         self.ensureCursorVisible()
   
         if self.inputType & QadInputTypeEnum.COMMAND:
            self.showCmdSuggestWindow(True, self.getCurrMsg())
      
   def entered(self):
      if self.inputType & QadInputTypeEnum.COMMAND:
         self.showCmdSuggestWindow(False)
      
      cursor = self.textCursor()
      cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
      self.setTextCursor(cursor)
      self.evaluate(unicode(self.currentCommand()))
      
   def showEvaluateMsg(self, msg = None):
      """
      mostra e valuta il messaggio msg se diverso da None altrimenti usa il messaggio corrente
      """
      if msg is not None:
         self.showMsg(msg)         
      self.entered()

   def getCurrMsg(self):
      """
      restituisce il messaggio già presente nella finestra di testo
      """
      cursor = self.textCursor()
      prevPos = cursor.position()
      cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
      self.setTextCursor(cursor)
      msg = unicode(self.currentCommand())
      cursor.setPosition(prevPos)
      self.setTextCursor(cursor)
      return msg


   def getInvalidInputMsg(self):
      """
      restituisce il messaggio di input non valido
      """
      if self.inputType & QadInputTypeEnum.POINT2D or \
         self.inputType & QadInputTypeEnum.POINT3D:
         if self.inputType & QadInputTypeEnum.KEYWORDS and \
            (self.inputType & QadInputTypeEnum.FLOAT or self.inputType & QadInputTypeEnum.ANGLE):
            return QadMsg.translate("QAD", "\nEnter a point, a real number or a keyword.\n")
         elif self.inputType & QadInputTypeEnum.KEYWORDS:
            return QadMsg.translate("QAD", "\nEnter a point or a keyword.\n")
         elif self.inputType & QadInputTypeEnum.FLOAT or self.inputType & QadInputTypeEnum.ANGLE:
            return QadMsg.translate("QAD", "\nEnter a point or a real number.\n")
         else:
            return QadMsg.translate("QAD", "\nPoint not valid.\n")         
      elif self.inputType & QadInputTypeEnum.KEYWORDS:
         return QadMsg.translate("QAD", "\nKeyword not valid.\n")
      elif self.inputType & QadInputTypeEnum.STRING:
         return QadMsg.translate("QAD", "\nString not valid.\n")
      elif self.inputType & QadInputTypeEnum.INT:
         return QadMsg.translate("QAD", "\nInteger number not valid.\n")
      elif self.inputType & QadInputTypeEnum.LONG:
         return QadMsg.translate("QAD", "\nLong integer number not valid.\n")
      elif self.inputType & QadInputTypeEnum.FLOAT or self.inputType & QadInputTypeEnum.ANGLE:
         return QadMsg.translate("QAD", "\nReal number not valid.\n")
      elif self.inputType & QadInputTypeEnum.BOOL:
         return QadMsg.translate("QAD", "\nBoolean not valid.\n")
      else:
         return ""
      

   def __evaluateKeyWords(self, cmd, keyWordList):
      # The required portion of the keyword is specified in uppercase characters, 
      # and the remainder of the keyword is specified in lowercase characters.
      # The uppercase abbreviation can be anywhere in the keyword
      if cmd == "": # se cmd = "" la funzione find ritorna 0 (no comment)
         return None
      upperCmd = cmd.upper()
      selectedKeyWords = []
      for keyWord in keyWordList:
         # estraggo la parte maiuscola della parola chiave
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
         self.showMsg(QadMsg.translate("QAD", "\nAmbiguous answer: specify with greater clarity...\n"))
         Msg = ""         
         for keyWord in selectedKeyWords:
            if Msg == "":
               Msg = keyWord
            else:
               Msg = Msg + QadMsg.translate("QAD", " or ") + keyWord

         Msg = Msg + QadMsg.translate("QAD", " ?\n")
         self.showMsg(Msg)            
         
      return None

   def evaluateKeyWords(self, cmd):
      # The required portion of the keyword is specified in uppercase characters, 
      # and the remainder of the keyword is specified in lowercase characters.
      # The uppercase abbreviation can be anywhere in the keyword
      if cmd == "": # se cmd = "" la funzione find ritorna 0 (no comment)
         return None
      
      if cmd[0] == "_": # versione inglese
         keyWord = self.__evaluateKeyWords(cmd[1:], self.englishKeyWords)
         if keyWord is None:
            return None
         # cerco la corrispondente parola chiave in lingua locale
         i = 0
         for k in self.englishKeyWords:
            if k == keyWord:
               return self.keyWords[i]
            i = i + 1
         return None
      else:
         return self.__evaluateKeyWords(cmd, self.keyWords)
      
   
   def evaluate(self, cmd):      
      #------------------------------------------------------------------------------
      # nome di un comando
      #------------------------------------------------------------------------------ 
      if self.inputType & QadInputTypeEnum.COMMAND:
         if cmd == "":
            cmd = unicode(self.showLast()) # ripeto ultimo comando
         
         if self.parentWidget().isValidCommand(cmd):
            self.updateHistory(cmd)
            self.parentWidget().runCommand(cmd)
         else:
            msg = QadMsg.translate("QAD", "\nInvalid command \"{0}\".")
            self.showMsg(msg.format(cmd.encode('ascii','ignore')), True) # ripete il prompt
         return

      if cmd == "":
         if self.default is not None:
            if type(self.default) == QgsPoint:
               cmd = self.default.toString()
            else:
               cmd = unicode(self.default)              
               
         if cmd == "" and \
            not (self.inputMode & QadInputModeEnum.NOT_NULL): # permesso input nullo              
            self.parentWidget().continueCommand(None)         
            return
                       
      #------------------------------------------------------------------------------
      # punto 2D
      #------------------------------------------------------------------------------ 
      if self.inputType & QadInputTypeEnum.POINT2D:
         snapType = qad_utils.str2snapTypeEnum(cmd)
         if snapType != -1:
            # se é stato forzato uno snap
            snapParams = qad_utils.str2snapParams(cmd)
            self.parentWidget().forceCommandMapToolSnapTypeOnce(snapType, snapParams)
            self.showMsg(QadMsg.translate("QAD", "\n(temporary snap)\n"), True) # ripeti il prompt
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
                                     self.parentWidget().getLastPoint(), \
                                     self.parentWidget().getCurrenPointFromCommandMapTool(), \
                                     oneNumberAllowed)
                      
         if pt is not None:
            self.parentWidget().setLastPoint(pt)
            self.parentWidget().continueCommand(pt)
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
            self.parentWidget().continueCommand(keyWord)
            return
                      
      #------------------------------------------------------------------------------
      # una stringa
      #------------------------------------------------------------------------------ 
      if self.inputType & QadInputTypeEnum.STRING:            
         if cmd is not None:            
            self.parentWidget().continueCommand(cmd)
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
            self.parentWidget().continueCommand(int(num))
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
            self.parentWidget().continueCommand(long(num))
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
            if self.inputType & QadInputTypeEnum.ANGLE: # se é un angolo in gradi
               # i gradi vanno convertiti in radianti
               num = qad_utils.toRadians(num)            
            self.parentWidget().continueCommand(float(num))         
            return       

      #------------------------------------------------------------------------------
      # un valore booleano
      #------------------------------------------------------------------------------ 
      elif self.inputType & QadInputTypeEnum.BOOL:
         value = qad_utils.str2bool(cmd)
            
         if value is not None:
            self.parentWidget().continueCommand(value)
            return       

      self.showMsg(self.getInvalidInputMsg())
      
      if self.inputType & QadInputTypeEnum.KEYWORDS:
         self.displayKeyWordsPrompt()
      else:
         self.displayPrompt()
         
      return
      
   def getOptimalHeight(self):
      fm = QFontMetrics(self.currentFont())
      pixelsWidth = fm.width(QadMsg.translate("QAD", "Command: "))
      pixelsHeight = fm.height()
      # + 8 perché la QTextEdit ha un offset verticale sopra e sotto il testo
      return max(self.document().size().height(), pixelsHeight + 8)
      
   def onTextChanged(self):
      self.parentWidget().resizeEdits()

         
#===============================================================================
# Ui_QadCmdSuggestWindow
#===============================================================================
class QadCmdSuggestWindow(QWidget, Ui_QadCmdSuggestWindow, object):
         
   def __init__(self, parent, infoCmds):
      # lista composta da elementi con:
      # <nome locale comando>, <nome inglese comando>, <icona>, <note>
      QWidget.__init__(self, parent)
      self.setupUi(self)
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
            if upperFilter[0] == "_": # versione inglese 
               upperFilter = upperFilter[1:]
               # lista composta da elementi con:
               # <nome locale comando>, <nome inglese comando>, <icona>, <note>
               for infoCmd in self.infoCmds:
                  if string.find(infoCmd[1].upper(), upperFilter) == 0 or filter == "*": # se incomincia per
                     filteredInfoCmds.append(["_" + infoCmd[1], infoCmd[2], infoCmd[3]])
            else: # versione italiana
               # lista composta da elementi con:
               # <nome locale comando>, <nome inglese comando>, <icona>, <note>
               for infoCmd in self.infoCmds:
                  if string.find(infoCmd[0].upper(), upperFilter) == 0 or filter == "*": # se incomincia per
                     filteredInfoCmds.append([infoCmd[0], infoCmd[2], infoCmd[3]])
                  
         if len(filteredInfoCmds) == 0:
            self.setVisible(False)
         else:
            self.move(self.parentWidget().width() - self.width() - 15, 0)
            self.cmdNamesListView.set(filteredInfoCmds)
            self.setVisible(True)
      else:
         self.setVisible(False)

   def resizeEvent(self, e):
      self.resize(200, self.parentWidget().height())
      self.move(self.parentWidget().width() - self.width() - 15, 0)

   def showEvaluateMsg(self, cmd):
      self.show(False)
      self.parentWidget().setFocus()
      self.parentWidget().abortCommand()
      self.parentWidget().showEvaluateMsg(cmd)
         
#===============================================================================
# QadCmdListView
#===============================================================================
class QadCmdSuggestListView(QListView):

   def __init__(self, parent):
      QListView.__init__(self, parent)

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
         self.parentWidget().showEvaluateMsg(cmd)
      
   def mouseReleaseEvent(self, e):
      cmd = self.selectionModel().currentIndex().data()
      self.parentWidget().showEvaluateMsg(cmd)
      
