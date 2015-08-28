# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per le traduzioni dei messaggi
 
                              -------------------
        begin                : 2013-05-22
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


# traduction class.
class QadMsgClass():


   def __init__(self):
      pass
      

   #============================================================================
   # translate
   #============================================================================
   def translate(self, context, sourceText, disambiguation = None, encoding = QCoreApplication.UnicodeUTF8, n = -1):
      # da usare in una riga senza accoppiarla ad altre chiamate ad esempio (per lupdate.exe che altrimenti non le trova):
      # NON VA BENE
      #     proplist["blockScale"] = [QadMsg.translate("Dimension", "Scala frecce"), \
      #                               self.blockScale]
      # VA BENE
      #     msg = QadMsg.translate("Dimension", "Scala frecce")
      #     proplist["blockScale"] = [msg, self.blockScale]
 
      # contesti:
      # "QAD" per traduzioni generali
      # "Popup_menu_graph_window" per il menu popup nella finestra grafica
      # "Text_window" per la finestra testuale
      # "Command_list" per nomi di comandi
      # "Command_<nome comando in inglese>" per traduzioni di un comando specifico (es. "Command_PLINE")
      # "Snap" per i tipi di snap
      # finestre varie (es. "DSettings_Dialog", DimStyle_Dialog, ...)
      # "Dimension" per le quotature
      # "Environment variables" per i nomi delle variabili di ambiente
      return QCoreApplication.translate(context, sourceText, disambiguation, encoding, n)
   
   
#===============================================================================
# QadMsg = variabile globale
#===============================================================================

QadMsg = QadMsgClass()
