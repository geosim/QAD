# -*- coding: utf-8 -*-

"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire gli alias dei comandi
 
                              -------------------
        begin                : 2013-05-22
        copyright            : (C) 2013 IREN Acqua Gas SpA
        email                : geosim.dev@gruppoiren.it
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


# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
import os.path
from qgis.core import *


import qad_utils


# Classe che gestisce gli alias dei comandi di Qad
class QadCommandAliasesClass():
   
   def __init__(self):   
      self.__commandAliases = dict()  # dizionario degli alias dei comandi
   
   def getCommandAliasDict(self,):
      """
      Restituisce il dizionario degli alias 
      """
      return self.__commandAliases

   #============================================================================
   # getCommandName
   #============================================================================
   def getCommandName(self, alias):
      """
      Dato l'alias restituisce il nome del comando 
      """
      if type(alias) == str or type(alias) == unicode: 
         return self.__commandAliases.get(alias.upper())
      else:
         return self.__commandAliases.get(alias.toUpper())


   #============================================================================
   # load
   #============================================================================
   def load(self, Path=""):
      """
      Carica la lista degli alias dei comandi da file
      Ritorna True in caso di successo, false in caso di errore
      """
      # svuoto il dizionario e lo reimposto con i valori di default
      self.__commandAliases.clear()
      if Path == "":
         # Se la path non é indicata uso il file "qad.pgp" in 
         Path = QDir.cleanPath(QgsApplication.qgisSettingsDirPath()) + "python/plugins/qad/"
         Path = Path + "qad.pgp"

      if not os.path.exists(Path):
         return True
         
      file = open(Path, "r") # apre il file in lettura
      
      for line in file:
         line = qad_utils.strip(line, [" ", "\t", "\r\n"]) # rimuovo gli spazi e i tab prima e dopo
         if len(line) == 0:
            continue
         # se la riga inizia per ; allora é una riga commentata
         if line[0] == ";":
            continue

         # leggo il nome dell'alias + il nome del comando (es "alias, *comando")
         sep = line.find(",")
         if sep <= 0:
            continue
         alias = line[0:sep]
         alias = qad_utils.strip(alias, [" ", "\t", "\r\n"]) # rimuovo gli spazi e i tab prima e dopo
         if len(alias) == 0:
            continue
         
         command = line[sep+1:]
         command = qad_utils.strip(command, [" ", "\t", "\r\n"]) # rimuovo gli spazi e i tab prima e dopo
         if len(command) <= 1:
            continue
         # se il comando non inizia per * allora non é un alias
         if command[0] != "*":
            continue
         command = command[1:]
         # il comando non può contenere spazi
         sep = command.find(" ")
         if sep > 0:
            continue

         self.__commandAliases[alias.upper()] = command.upper()
           
      file.close()
      
      return True
