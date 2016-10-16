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
from PyQt4.QtGui import * # for QDesktopServices
import os.path

import urllib
import platform


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
      # "Help" per i titoli dei capitoli del manuale che servono da section nel file html di help
      return QCoreApplication.translate(context, sourceText, disambiguation, encoding, n)


#===============================================================================
# qadShowPluginHelp
#===============================================================================
def qadShowPluginHelp(section = "", filename = "index", packageName = None):
   """
   show a help in the user's html browser.
   per conoscere la sezione/pagina del file html usare internet explorer,
   selezionare nella finestra di destra la voce di interesse e leggerne l'indirizzo dalla casella in alto.
   Questo perché internet explorer inserisce tutti i caratteri di spaziatura e tab che gli altri browser non fanno.
   """   
   try:
      source = ""
      if packageName is None:
         import inspect
         source = inspect.currentframe().f_back.f_code.co_filename
      else:
         source = sys.modules[packageName].__file__
   except:
      return

   # initialize locale
   userLocaleList = QSettings().value("locale/userLocale").split("_")
   language = userLocaleList[0]
   region = userLocaleList[1] if len(userLocaleList) > 1 else ""

   path = QDir.cleanPath(os.path.dirname(source) + "/help/help")
   helpPath = path + "_" + language + "_" + region # provo a caricare la lingua e la regione selezionate
   
   if not os.path.exists(helpPath):
      helpPath = path + "_" + language # provo a caricare la lingua
      if not os.path.exists(helpPath):
         helpPath = path + "_en" # provo a caricare la lingua inglese
         if not os.path.exists(helpPath):
            return
      
   helpfile = os.path.join(helpPath, filename + ".html")
   if os.path.exists(helpfile):
      url = "file:///"+helpfile

      if section != "":
         url = url + "#" + urllib.quote(section.encode('utf-8'))

      # la funzione QDesktopServices.openUrl in windows non apre la sezione
      if platform.system() == "Windows":
         import subprocess
         from _winreg import HKEY_CURRENT_USER, OpenKey, QueryValue
         # In Py3, this module is called winreg without the underscore
         
         with OpenKey(HKEY_CURRENT_USER, r"Software\Classes\http\shell\open\command") as key:
            cmd = QueryValue(key, None)
   
         if cmd.find("\"%1\"") >= 0:
            subprocess.Popen(cmd.replace("%1", url))
         else:    
            if cmd.find("%1") >= 0:
               subprocess.Popen(cmd.replace("%1", "\"" + url + "\""))       
            else:
               subprocess.Popen(cmd + " \"" + url + "\"")
      else:
         QDesktopServices.openUrl(QUrl(url))           
   
   
#===============================================================================
# QadMsg = variabile globale
#===============================================================================

QadMsg = QadMsgClass()
