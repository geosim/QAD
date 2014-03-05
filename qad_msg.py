# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per le traduzioni dei messaggi
 
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


import qad_debug


# traduction class.
class QadMsgClass():


   def __init__(self):
      pass
      

   #============================================================================
   # translate
   #============================================================================
   def translate(self, context, sourceText, disambiguation = None, encoding = QCoreApplication.CodecForTr, n = -1):
      # contesti:
      # "QAD" per traduzioni generali
      # "Popup_menu_graph_window" per il menu popup nella finestra grafica
      # "Text_window" per la finestra testuale
      # "Command_list" per nomi di comandi
      # "Command_<nome comando in inglese>" per traduzioni di un comando specifico (es. "Command_PLINE")
      # "Snap" per i tipi di snap
      # finestre varie (es. "dsettings")
      # "Environment variables" per i nomi delle variabili di ambiente
      return QCoreApplication.translate(context, sourceText, disambiguation, encoding, n)
   
   
#===============================================================================
# QadMsg = variabile globale
#===============================================================================

QadMsg = QadMsgClass()
