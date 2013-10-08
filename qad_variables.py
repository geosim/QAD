# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire le variabili di ambiente
 
                              -------------------
        begin                : 2013-05-22
        copyright            : (C) 2013 by Roberto Poltini
        email                : roberto.poltini@irenacquagas.it
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
      # AUTOSNAP (int): attiva il puntamento polare (somma di bit):
      # 8 = Attiva il puntamento polare
      self.__VariableValuesDict["AUTOSNAP"] = int(63)
      # CMDINPUTHISTORYMAX (int): Imposta il numero massimo di comandi nella lista di storicizzazione
      self.__VariableValuesDict["CMDINPUTHISTORYMAX"] = int(20)
      # COPYMODE (int):
      # 0 = Imposta il comando COPIA in modo che venga ripetuto automaticamente
      # 1 = Imposta il comando COPIA in modo da creare una singola copia
      self.__VariableValuesDict["COPYMODE"] = int(0)     
      # CURSORSIZE (int): Imposta la dimensione in pixel del cursore (la croce)
      self.__VariableValuesDict["CURSORSIZE"] = int(5)
      # OFFSETDIST(float): Setta la distanza di default per l'offset
      # < 0  offset di un oggetto attraverso un punto
      # >= 0 offset di un oggetto attraverso la distanza
      self.__VariableValuesDict["OFFSETDIST"] = float(-1.0)
      # OFFSETGAPTYPE (int):
      # 0 = Estende i segmenti di linea alle relative intersezioni proiettate
      # 1 = Raccorda i segmenti di linea in corrispondenza delle relative intersezioni proiettate.
      #     Il raggio di ciascun segmento di arco è uguale alla distanza di offset
      # 2 = Cima i segmenti di linea in corrispondenza delle intersezioni proiettate.
      #     La distanza perpendicolare da ciascuna cima al rispettivo vertice
      #     sull'oggetto originale è uguale alla distanza di offset. 
      self.__VariableValuesDict["OFFSETGAPTYPE"] = int(0)     
      # ORTHOMODE (int):
      # 0 = modalità di movimento ortogonale cursore disabilitata
      # 1 = modalità di movimento ortogonale cursore abilitata
      self.__VariableValuesDict["ORTHOMODE"] = int(0)
      # OSCOLOR (str): Imposta il colore (RGB) dei simboli di osnap
      self.__VariableValuesDict["OSCOLOR"] = "#FF0000" # rosso
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
      # 512 = (NEA) punto più vicino di un oggetto
      # 1024 = (C) Cancella tutti gli snap ad oggetto
      # 2048 = (APP) intersezione apparente di due oggetti che non si intersecano nello spazio 3D 
      #        ma che possono apparire intersecanti nella vista corrente
      # 4096 = (EXT) Estensione : Visualizza una linea o un arco di estensione temporaneo quando si sposta il cursore sul punto finale degli oggetti, 
      #        in modo che sia possibile specificare punti sull'estensione
      # 8192 = (PAR) Parallelo: Vincola un segmento di linea, un segmento di polilinea, un raggio o una xlinea ad essere parallela ad un altro oggetto lineare
      # 16384 = osnap off  
      self.__VariableValuesDict["OSMODE"] = int(0)
      # OSPROGRDISTANCE (float): Distanza progressima per snap PR
      self.__VariableValuesDict["OSPROGRDISTANCE"] = float(0.0)
      # OSSIZE (int): Imposta la dimensione in pixel dei simboli di osnap
      self.__VariableValuesDict["OSSIZE"] = int(13)
      # PICKBOX (int): Imposta la dimensione in pixel della distanza di selezione degli oggetti
      # dalla posizione corrente del puntatore
      self.__VariableValuesDict["PICKBOX"] = int(5)
      # PICKBOXCOLOR (str): Imposta il colore (RGB) del quadratino di selezione degli oggetti
      self.__VariableValuesDict["PICKBOXCOLOR"] = "#FF0000" # rosso 
      # POLARANG (float): incremento dell'angolo polare per il puntamento polare (gradi)
      self.__VariableValuesDict["POLARANG"] = float(90.0)
      # SHOWTEXTWINDOW (bool): Visualizza la finestra di testo all'avvio
      self.__VariableValuesDict["SHOWTEXTWINDOW"] = True 
      # TOLERANCE2APPROXCURVE (float):
      # massimo errore tollerato tra una vera curva e quella approssimata dai segmenti retti
      # (nel sistema map-coordinate) 
      self.__VariableValuesDict["TOLERANCE2APPROXCURVE"] = float(0.1)
      

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
      if Path == "":
         # Se la path non è indicata uso il file "qad.ini" in 
         Path = QDir.cleanPath(QgsApplication.qgisSettingsDirPath()) + "/python/plugins/qad/"
         if not QDir(Path).exists():
            os.makedirs(Path.toAscii())
         Path = Path + "qad.ini"
       
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
         # Se la path non è indicata uso il file "qad.ini" in 
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
