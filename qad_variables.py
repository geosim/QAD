# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire le variabili di ambiente
 
                              -------------------
        begin                : 2013-05-22
        copyright            : (C) 2013 by bbbbb aaaaa
        email                : bbbbb.aaaaa@gruppoiren.it
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
import os.path
from qgis.core import *

import qad_debug
import qad_utils
from qad_msg import QadMsg

#===============================================================================
# Qad variables class.
#===============================================================================
class QadVariablesClass():
   """
   Classe che gestisce le variabuili di ambiente di Qad
   """
    
   __VariableValuesDict = dict() # variabile privata <nome variabile>-<valore variabile>
    
   def __init__(self):
      """
      Inizializza un dizionario con le variabili e i loro valori di default 
      """
      # ARCMINSEGMENTQTY (int): numero minimo di segmenti perch� venga riconosciuto un arco
      VariableName = QadMsg.translate("Environment variables", "ARCMINSEGMENTQTY") # x lupdate
      self.__VariableValuesDict[VariableName] = int(12)
      # AUTOSNAP (int): attiva il puntamento polare (somma di bit):
      # 8 = Attiva il puntamento polare
      VariableName = QadMsg.translate("Environment variables", "AUTOSNAP")
      self.__VariableValuesDict[VariableName] = int(63)
      # CIRCLEMINSEGMENTQTY (int): numero minimo di segmenti perch� venga riconosciuto un cerchio
      VariableName = QadMsg.translate("Environment variables", "CIRCLEMINSEGMENTQTY")
      self.__VariableValuesDict[VariableName] = int(12)
      # CMDINPUTHISTORYMAX (int): Imposta il numero massimo di comandi nella lista di storicizzazione
      VariableName = QadMsg.translate("Environment variables", "CMDINPUTHISTORYMAX")
      self.__VariableValuesDict[VariableName] = int(20)
      # COPYMODE (int):
      # 0 = Imposta il comando COPIA in modo che venga ripetuto automaticamente
      # 1 = Imposta il comando COPIA in modo da creare una singola copia
      VariableName = QadMsg.translate("Environment variables", "COPYMODE")
      self.__VariableValuesDict[VariableName] = int(0)     
      # CURSORSIZE (int): Imposta la dimensione in pixel del cursore (la croce)
      VariableName = QadMsg.translate("Environment variables", "CURSORSIZE")
      self.__VariableValuesDict[VariableName] = int(5)      
      # DIMSTYLE (str): Imposta il nome dello stile di quotatura corrente
      VariableName = QadMsg.translate("Environment variables", "DIMSTYLE")
      self.__VariableValuesDict[VariableName] = ""      
      # EDGEMODE (int): Controlla i comandi ESTENDI e TAGLIA.
      # O = Vengono usate le dimensioni reali degli oggetti di riferimento
      # 1 = Vengono usate le estensioni  degli oggetti di riferimento (es. un arco viene considerato cerchio)
      VariableName = QadMsg.translate("Environment variables", "EDGEMODE")
      self.__VariableValuesDict[VariableName] = int(0)
      # FILLETRAD (float): raggio applicato per raccordare (gradi)
      VariableName = QadMsg.translate("Environment variables", "FILLETRAD")
      self.__VariableValuesDict[VariableName] = float(0.0)
      # OFFSETDIST(float): Setta la distanza di default per l'offset
      # < 0  offset di un oggetto attraverso un punto
      # >= 0 offset di un oggetto attraverso la distanza
      VariableName = QadMsg.translate("Environment variables", "OFFSETDIST")
      self.__VariableValuesDict[VariableName] = float(-1.0)
      # OFFSETGAPTYPE (int):
      # 0 = Estende i segmenti di linea alle relative intersezioni proiettate
      # 1 = Raccorda i segmenti di linea in corrispondenza delle relative intersezioni proiettate.
      #     Il raggio di ciascun segmento di arco � uguale alla distanza di offset
      # 2 = Cima i segmenti di linea in corrispondenza delle intersezioni proiettate.
      #     La distanza perpendicolare da ciascuna cima al rispettivo vertice
      #     sull'oggetto originale � uguale alla distanza di offset.
      VariableName = QadMsg.translate("Environment variables", "OFFSETGAPTYPE")
      self.__VariableValuesDict[VariableName] = int(0)     
      # ORTHOMODE (int):
      # 0 = modalit� di movimento ortogonale cursore disabilitata
      # 1 = modalit� di movimento ortogonale cursore abilitata
      VariableName = QadMsg.translate("Environment variables", "ORTHOMODE")
      self.__VariableValuesDict[VariableName] = int(0)
      # OSCOLOR (str): Imposta il colore (RGB) dei simboli di osnap
      VariableName = QadMsg.translate("Environment variables", "OSCOLOR")
      self.__VariableValuesDict[VariableName] = "#FF0000" # rosso
      # OSMODE (int): Imposta lo snap ad oggetto (somma di bit):
      # 0 = (NON) nessuno
      # 1 = (END) punto finale
      # 2 = (MID)punto medio   
      # 4 = (CEN) centroide di un poligono   
      # 8 = (NOD) ad oggetto punto
      # 16 = (QUA) punto quadrante di un poligono
      # 32 = (INT) intersezione di un oggetto (anche i vertici intermedi di una linestring o polygon)
      # 64 = (INS) punto di inserimento di oggetti (come 8)
      # 128 = (PER) punto perpendicolare a un oggetto
      # 256 = (TAN) tangente di un arco, di un cerchio, di un'ellisse, di un arco ellittico o di una spline
      # 512 = (NEA) punto pi� vicino di un oggetto
      # 1024 = (C) Cancella tutti gli snap ad oggetto
      # 2048 = (APP) intersezione apparente di due oggetti che non si intersecano nello spazio 3D 
      #        ma che possono apparire intersecanti nella vista corrente
      # 4096 = (EXT) Estensione : Visualizza una linea o un arco di estensione temporaneo quando si sposta il cursore sul punto finale degli oggetti, 
      #        in modo che sia possibile specificare punti sull'estensione
      # 8192 = (PAR) Parallelo: Vincola un segmento di linea, un segmento di polilinea, un raggio o una xlinea ad essere parallela ad un altro oggetto lineare
      # 16384 = osnap off
      # 65536 = (PR) Distanza progressiva
      # 131072 = intersezione sull'estensione
      # 262144 = perpendicolare differita
      # 524288 = tangente differita
      # 1048576 = puntamento polare
      VariableName = QadMsg.translate("Environment variables", "OSMODE")
      self.__VariableValuesDict[VariableName] = int(0)
      # OSPROGRDISTANCE (float): Distanza progressima per snap PR
      VariableName = QadMsg.translate("Environment variables", "OSPROGRDISTANCE")
      self.__VariableValuesDict[VariableName] = float(0.0)
      # OSSIZE (int): Imposta la dimensione in pixel dei simboli di osnap
      VariableName = QadMsg.translate("Environment variables", "OSSIZE")
      self.__VariableValuesDict[VariableName] = int(13)
      # PICKBOX (int): Imposta la dimensione in pixel della distanza di selezione degli oggetti
      # dalla posizione corrente del puntatore
      VariableName = QadMsg.translate("Environment variables", "PICKBOX")
      self.__VariableValuesDict[VariableName] = int(5)
      # PICKBOXCOLOR (str): Imposta il colore (RGB) del quadratino di selezione degli oggetti
      VariableName = QadMsg.translate("Environment variables", "PICKBOXCOLOR")
      self.__VariableValuesDict[VariableName] = "#FF0000" # rosso 
      # POLARANG (float): incremento dell'angolo polare per il puntamento polare (gradi)
      VariableName = QadMsg.translate("Environment variables", "POLARANG")
      self.__VariableValuesDict[VariableName] = float(90.0)
      # SUPPORTPATH (str): Path di ricerca per i files di supporto
      VariableName = QadMsg.translate("Environment variables", "SUPPORTPATH")
      self.__VariableValuesDict[VariableName] = "" # rosso
      # SHOWTEXTWINDOW (bool): Visualizza la finestra di testo all'avvio
      VariableName = QadMsg.translate("Environment variables", "SHOWTEXTWINDOW")
      self.__VariableValuesDict[VariableName] = True 
      # TOLERANCE2APPROXCURVE (float):
      # massimo errore tollerato tra una vera curva e quella approssimata dai segmenti retti
      # (nel sistema map-coordinate)
      VariableName = QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE")
      self.__VariableValuesDict[VariableName] = float(0.1)
      

   def getVarNames(self):
      """
      Ritorna la lista dei nomi delle variabili 
      """
      return self.__VariableValuesDict.keys()
          
   def set(self, VarName, VarValue):
      """
      Modifica il valore di una variabile 
      """
      UpperVarName = VarName
      self.__VariableValuesDict[UpperVarName.upper()] = VarValue
       
   def get(self, VarName, defaultValue = None):
      """
      Restituisce il valore di una variabile 
      """
      UpperVarName = VarName
      result = self.__VariableValuesDict.get(UpperVarName.upper())
      if result is None:
         result = defaultValue
      
      return result
        
   def save(self, Path=""):
      """
      Salva il dizionario delle variabili su file 
      """
      #qad_debug.breakPoint()
      if Path == "":
         # Se la path non � indicata uso il file "qad.ini" in 
         Path = QDir.cleanPath(QgsApplication.qgisSettingsDirPath()) + "/python/plugins/qad/"
         Path = Path + "qad.ini"
      
      dir = QFileInfo(Path).absoluteDir()
      if not dir.exists():
         os.makedirs(dir.absolutePath())
       
      file = open(Path, "w") # apre il file in scrittura
      for VarName in self.__VariableValuesDict.keys():
         VarValue = self.get(VarName)
         # scrivo il valore + il tipo (es var = 5 <type 'int'>)
         VarValue = str(VarValue) + " " + str(type(VarValue))
         Item = "%s = %s\n" % (VarName, VarValue)
         file.write(Item)
          
      file.close()
 
   def load(self, Path=""):
      """
      Carica il dizionario delle variabili da file
      Ritorna True in caso di successo, false in caso di errore
      """
      # svuoto il dizionario e lo reimposto con i valori di default
      self.__VariableValuesDict.clear()
      self.__init__()
      if Path == "":
         # Se la path non � indicata uso il file "qad.ini" in 
         Path = QDir.cleanPath(QgsApplication.qgisSettingsDirPath()) + "/python/plugins/qad/"
         Path = Path + "qad.ini"

      if not os.path.exists(Path):
         return False
                    
      file = open(Path, "r") # apre il file in lettura
      for line in file:
         # leggo il valore + il tipo (es var = 5 <type 'int'>)
         sep = line.rfind(" = ")
         VarName = line[0:sep]
         VarName = VarName.strip(" ") # rimuovo gli spazi prima e dopo
         VarValue = line[sep+3:]
         sep = VarValue.rfind(" <type '")
         sep2 = VarValue.rfind("'>")
         VarType = VarValue[sep+8:sep2]
         VarValue = VarValue[:sep]
         if VarType == "int":
            VarValue = qad_utils.str2int(VarValue)
            if VarValue is None:
               self.set(VarName, int(0))
            else:
               self.set(VarName, VarValue)
         elif VarType == "long":
            VarValue = qad_utils.str2long(VarValue)
            if VarValue is None:
               self.set(VarName, long(0))
            else:
               self.set(VarName, VarValue)
         elif VarType == "float":
            VarValue = qad_utils.str2float(VarValue)
            if VarValue is None:
               self.set(VarName, float(0))
            else:
               self.set(VarName, VarValue)
         elif VarType == "bool":
            VarValue = qad_utils.str2bool(VarValue)
            if VarValue is None:
               self.set(VarName, False)
            else:
               self.set(VarName, VarValue)
         else:
            self.set(VarName, str(VarValue))
            
      file.close()
      
      return True


#===============================================================================
# QadVariables = variabile globale
#===============================================================================

QadVariables = QadVariablesClass()
