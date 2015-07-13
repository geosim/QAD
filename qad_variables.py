# -*- coding: utf-8 -*-
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

import qad_utils
from qad_msg import QadMsg


#===============================================================================
# Qad variable class.
#===============================================================================
class QadVariableTypeEnum():
   UNKNOWN = 0 # sconosciuto (non gestito da QAD)
   STRING  = 1 # caratteri
   COLOR   = 2 # colore espresso in caratteri (es. rosso = "#FF0000")
   INT     = 3 # numero intero
   FLOAT   = 4 # nmer con decimali
   BOOL    = 5 # booleano (True o False)


#===============================================================================
# Qad variable class.
#===============================================================================
class QadVariable():
   """
   Classe che gestisce le variabili di ambiente di Qad
   """

   def __init__(self, name, value, typeValue, minNum = None, maxNum = None, descr = ""):
      self.name = name
      self.value = value
      self.typeValue = typeValue
      self.default = value
      self.minNum = minNum
      self.maxNum = maxNum
      self.descr = descr


#===============================================================================
# Qad variables class.
#===============================================================================
class QadVariablesClass():
   """
   Classe che gestisce le variabuili di ambiente di Qad
   """    
    
   def __init__(self):
      """
      Inizializza un dizionario con le variabili e i loro valori di default 
      """
      self.__VariableValuesDict = dict() # variabile privata <nome variabile>-<valore variabile>

      # ARCMINSEGMENTQTY (int): numero minimo di segmenti perché venga riconosciuto un arco
      VariableName = QadMsg.translate("Environment variables", "ARCMINSEGMENTQTY") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Numero minimo di segmenti per approssimare un arco." + \
                                       "\nTipo intero.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, int(12), \
                                                            QadVariableTypeEnum.INT, \
                                                            4, 999, \
                                                            VariableDescr)
      
      # AUTOSNAP (int): attiva il puntamento polare (somma di bit):
      # 8 = Attiva il puntamento polare
      VariableName = QadMsg.translate("Environment variables", "AUTOSNAP")
      VariableDescr = QadMsg.translate("Environment variables", "Controlla la visualizzazione del contrassegno, della descrizione e della calamita di AutoSnap." + \
                                       "\nInoltre, attiva il puntamento polare e con snap ad oggetto e controlla la visualizzazione delle descrizioni corrispondenti, " + \
                                       "nonché quella della modalità orto.\nL'impostazione è memorizzata come codice binario che utilizza la somma dei seguenti valori:" + \
                                       "\n0 = Disattiva il contrassegno, le descrizioni dei comandi e la calamita di AutoSnap. Inoltre, disattiva il puntamento polare e con snap ad oggetto, nonché la visualizzazione delle descrizioni corrispondenti e della modalità orto." + \
                                       "\n1 = Attiva il contrassegno di AutoSnap." + \
                                       "\n2 = Attiva le descrizioni dei comandi di AutoSnap." + \
                                       "\n4 = Attiva la calamita di AutoSnap." + \
                                       "\n8 = Attiva il puntamento polare." + \
                                       "\n16 = Attiva il puntamento con snap ad oggetto." + \
                                       "\n32 = Attiva la visualizzazione delle descrizioni del puntamento polare e con snap ad oggetto, nonché della modalità orto." + \
                                       "\nTipo intero.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, int(63), \
                                                            QadVariableTypeEnum.INT, \
                                                            0, None, \
                                                            VariableDescr)
      
      # CIRCLEMINSEGMENTQTY (int): numero minimo di segmenti perché venga riconosciuto un cerchio
      VariableName = QadMsg.translate("Environment variables", "CIRCLEMINSEGMENTQTY") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Numero minimo di segmenti per approssimare un cerchio." + \
                                       "\nTipo intero.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, int(12), \
                                                            QadVariableTypeEnum.INT, \
                                                            6, 999, \
                                                            VariableDescr)
      
      # CMDINPUTHISTORYMAX (int): Imposta il numero massimo di comandi nella lista di storicizzazione
      VariableName = QadMsg.translate("Environment variables", "CMDINPUTHISTORYMAX") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Imposta il numero massimo di comandi precedenti." + \
                                       "\nTipo intero.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, int(20), \
                                                            QadVariableTypeEnum.INT, \
                                                            1, 999, \
                                                            VariableDescr)
      
      # COPYMODE (int):
      # 0 = Imposta il comando COPIA in modo che venga ripetuto automaticamente
      # 1 = Imposta il comando COPIA in modo da creare una singola copia
      VariableName = QadMsg.translate("Environment variables", "COPYMODE") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Verifica se il comando COPIA viene ripetuto automaticamente:" + \
                                       "\n0 = Imposta il comando COPIA in modo che venga ripetuto automaticamente." + \
                                       "\n1 = Imposta il comando COPIA in modo da creare una singola copia." + \
                                       "\nTipo intero.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, int(0), \
                                                            QadVariableTypeEnum.INT, \
                                                            0, 1, \
                                                            VariableDescr)
      
      # CURSORCOLOR (str): Imposta il colore (RGB) del cursore (la croce)
      VariableName = QadMsg.translate("Environment variables", "CURSORCOLOR") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Colore (RGB) del puntatore a croce (es. #FF0000 = rosso)." + \
                                       "\nTipo carattere.") # x lupdate                                       
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, unicode("#FF0000"), \
                                                            QadVariableTypeEnum.COLOR, \
                                                            None, None, \
                                                            VariableDescr) # rosso 
      
      # CURSORSIZE (int): Imposta la dimensione in pixel del cursore (la croce)
      VariableName = QadMsg.translate("Environment variables", "CURSORSIZE") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Determina le dimensioni del puntatore a croce come percentuale della dimensione dello schermo."
                                       "\nTipo intero.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, int(5), \
                                                            QadVariableTypeEnum.INT, \
                                                            1, 100, \
                                                            VariableDescr)
      
      # DIMSTYLE (str): Imposta il nome dello stile di quotatura corrente
      VariableName = QadMsg.translate("Environment variables", "DIMSTYLE") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Nome dello stile di quotatura corrente." + \
                                       "\nTipo carattere.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, unicode(""), \
                                                            QadVariableTypeEnum.STRING, \
                                                            None, None, \
                                                            VariableDescr)
      
      # EDGEMODE (int): Controlla i comandi ESTENDI e TAGLIA.
      # O = Vengono usate le dimensioni reali degli oggetti di riferimento
      # 1 = Vengono usate le estensioni  degli oggetti di riferimento (es. un arco viene considerato cerchio)
      VariableName = QadMsg.translate("Environment variables", "EDGEMODE") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Controlla la modalità in cui i comandi TAGLIA ed ESTENDI determinano i limiti di taglio e di estensione:" + \
                                       "\n0 = Utilizza lo spigolo selezionato senza estensioni." + \
                                       "\n1 = Estende o taglia l'oggetto selezionato fino ad un'estensione immaginaria del limite di taglio o di estensione." + \
                                       "\nTipo intero.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, int(0), \
                                                            QadVariableTypeEnum.INT, \
                                                            0, 1, \
                                                            VariableDescr)
      
      # FILLETRAD (float): raggio applicato per raccordare (gradi)
      VariableName = QadMsg.translate("Environment variables", "FILLETRAD") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Memorizza il raggio di raccordo corrente." + \
                                       "Se si utilizza il comando RACCORDO per modificare il raggio di un raccordo, il valore di questa variabile di sistema cambia di conseguenza." + \
                                       "\nTipo reale.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, float(0.0), \
                                                            QadVariableTypeEnum.FLOAT, \
                                                            0.000001, None, \
                                                            VariableDescr)

      # OFFSETDIST(float): Setta la distanza di default per l'offset
      # < 0  offset di un oggetto attraverso un punto
      # >= 0 offset di un oggetto attraverso la distanza
      VariableName = QadMsg.translate("Environment variables", "OFFSETDIST") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Distanza di offset di default:" + \
                                       "\n<0 = Esegue l'offset di un oggetto attraverso un punto specificato." + \
                                       "\n>=0 = Imposta la distanza di offset di default." + \
                                       "\nTipo reale.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, float(-1.0), \
                                                            QadVariableTypeEnum.FLOAT, \
                                                            None, None, \
                                                            VariableDescr)

      # OFFSETGAPTYPE (int):
      # 0 = Estende i segmenti di linea alle relative intersezioni proiettate
      # 1 = Raccorda i segmenti di linea in corrispondenza delle relative intersezioni proiettate.
      #     Il raggio di ciascun segmento di arco é uguale alla distanza di offset
      # 2 = Cima i segmenti di linea in corrispondenza delle intersezioni proiettate.
      #     La distanza perpendicolare da ciascuna cima al rispettivo vertice
      #     sull'oggetto originale é uguale alla distanza di offset.
      VariableName = QadMsg.translate("Environment variables", "OFFSETGAPTYPE") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Controlla la gestione dei potenziali spazi tra segmenti quando viene eseguito l'offset delle polilinee:" + \
                                       "\n0 = Estende i segmenti di linea alle relative intersezioni proiettate." + \
                                       "\n1 = Raccorda i segmenti di linea in corrispondenza delle relative intersezioni proiettate. Il raggio di ciascun segmento di arco è uguale alla distanza di offset." + \
                                       "\n2 = Cima i segmenti di linea in corrispondenza delle intersezioni proiettate. La distanza perpendicolare da ciascuna cima al rispettivo vertice sull'oggetto originale è uguale alla distanza di offset." + \
                                       "\nTipo intero.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, int(0), \
                                                            QadVariableTypeEnum.INT, \
                                                            0, 2, \
                                                            VariableDescr)     
      
      # ORTHOMODE (int):
      # 0 = modalità di movimento ortogonale cursore disabilitata
      # 1 = modalità di movimento ortogonale cursore abilitata
      VariableName = QadMsg.translate("Environment variables", "ORTHOMODE") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Limita il movimento del cursore alla direzione perpendicolare." + \
                                       "\nQuando ORTHOMODE è attivata, il cursore può essere spostato solo verticalmente oppure orizzontalmente:" + \
                                       "\n0 = Disattiva la modalità orto." + \
                                       "\n1 = Attiva la modalità orto." + \
                                       "\nTipo intero.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, int(0), \
                                                            QadVariableTypeEnum.INT, \
                                                            0, 1, \
                                                            VariableDescr)     
      
      # OSCOLOR (str): Imposta il colore (RGB) dei simboli di osnap
      VariableName = QadMsg.translate("Environment variables", "OSCOLOR") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Colore (RGB) dei simboli di osnap (es. #FF0000 = rosso)." + \
                                       "\nTipo carattere.") # x lupdate                                       
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, unicode("#FF0000"), \
                                                            QadVariableTypeEnum.COLOR, \
                                                            None, None, \
                                                            VariableDescr) # rosso
      
      # OSMODE (int): Imposta lo snap ad oggetto (somma di bit):
      # 0 = (NON) nessuno
      # 1 = (FIN) punti finali di ogni segmento
      # 2 = (MED) punto medio   
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
      # 4096 = (EST) Estensione : Visualizza una linea o un arco di estensione temporaneo quando si sposta il cursore sul punto finale degli oggetti, 
      #        in modo che sia possibile specificare punti sull'estensione
      # 8192 = (PAR) Parallelo: Vincola un segmento di linea, un segmento di polilinea, un raggio o una xlinea ad essere parallela ad un altro oggetto lineare
      # 16384 = osnap off
      # 65536 = (PR) Distanza progressiva
      # 131072 = intersezione sull'estensione
      # 262144 = perpendicolare differita
      # 524288 = tangente differita
      # 1048576 = puntamento polare
      # 2097152 = punti finali dell'intera polilinea
      VariableName = QadMsg.translate("Environment variables", "OSMODE") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Modalità degli snap ad oggetto." + \
                                       "\nL'impostazione è memorizzata come codice binario che utilizza la somma dei seguenti valori:" + \
                                       "\n0 = Nessuno." + \
                                       "\n1 = Punti finali (FIN)." + \
                                       "\n2 = Punto medio (MED)." + \
                                       "\n4 = Centro-centroide (CEN)." + \
                                       "\n8 = Inserimento di un oggetto puntuale (NOD)." + \
                                       "\n16 = Punto quadrante (QUA)." + \
                                       "\n32 = Intersezione (INT)." + \
                                       "\n64 = Inserimento di un oggetto puntuale (INS)." + \
                                       "\n128 = Perpendicolare (PER)." + \
                                       "\n256 = Tangente (TAN)." + \
                                       "\n512 = Vicino (NEA)." + \
                                       "\n1024 = Cancella tutti gli snap ad oggetto (C)." + \
                                       "\n2048 = Intersezione apparente (APP)." + \
                                       "\n4096 = Estensione (EST)." + \
                                       "\n8192 = Parallelo (PAR)." + \
                                       "\n65536 = Distanza progressiva (PR[dist])." + \
                                       "\n131072 = Intersezione sull'estensione (EXT_INT)." + \
                                       "\n2097152 = Punti finali dell'intera polilinea (FIN_PL)." + \
                                       "\nTipo intero.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, int(0), \
                                                            QadVariableTypeEnum.INT, \
                                                            0, None, \
                                                            VariableDescr)
      
      # OSPROGRDISTANCE (float): Distanza progressiva per snap PR
      VariableName = QadMsg.translate("Environment variables", "OSPROGRDISTANCE") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Distanza progressiva per snap <Distanza progressiva>." + \
                                       "\nTipo reale.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, float(0.0), \
                                                            QadVariableTypeEnum.FLOAT, \
                                                            None, None, \
                                                            VariableDescr)
      
      # OSSIZE (int): Imposta la dimensione in pixel dei simboli di osnap
      VariableName = QadMsg.translate("Environment variables", "OSSIZE") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Dimensione in pixel dei simboli di osnap" + \
                                       "\nTipo intero.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, int(13), \
                                                            QadVariableTypeEnum.INT, \
                                                            1, 999, \
                                                            VariableDescr)
      
      # PICKBOX (int): Imposta la dimensione in pixel della distanza di selezione degli oggetti
      # dalla posizione corrente del puntatore
      VariableName = QadMsg.translate("Environment variables", "PICKBOX") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Altezza in pixel del quadratino di selezione degli oggetti." + \
                                       "\nTipo intero.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, int(5), \
                                                            QadVariableTypeEnum.INT, \
                                                            1, 999, \
                                                            VariableDescr)
      
      # PICKBOXCOLOR (str): Imposta il colore (RGB) del quadratino di selezione degli oggetti
      VariableName = QadMsg.translate("Environment variables", "PICKBOXCOLOR") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Colore (RGB) del quadratino di selezione degli oggetti (es. #FF0000 = rosso)." + \
                                       "\nTipo carattere.") # x lupdate                                       
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, unicode("#FF0000"), \
                                                            QadVariableTypeEnum.COLOR, \
                                                            None, None, \
                                                            VariableDescr) # rosso 

      # POLARANG (float): incremento dell'angolo polare per il puntamento polare (gradi)
      VariableName = QadMsg.translate("Environment variables", "POLARANG") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Incremento dell'angolo polare per il puntamento polare (gradi)." + \
                                       "\nTipo reale.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, float(90.0), \
                                                            QadVariableTypeEnum.INT, \
                                                            0.000001, 359.999999, \
                                                            VariableDescr)

      # SUPPORTPATH (str): Path di ricerca per i files di supporto
      VariableName = QadMsg.translate("Environment variables", "SUPPORTPATH") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Path di ricerca per i files di supporto." + \
                                       "\nTipo carattere.") # x lupdate                                       
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, unicode(""), \
                                                            QadVariableTypeEnum.STRING, \
                                                            None, None, \
                                                            VariableDescr)
      
      # SHOWTEXTWINDOW (bool): Visualizza la finestra di testo all'avvio
      VariableName = QadMsg.translate("Environment variables", "SHOWTEXTWINDOW") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Visualizza la finestra di testo all'avvio." + \
                                       "\nTipo booleano.") # x lupdate                                       
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, True, \
                                                            QadVariableTypeEnum.BOOL, \
                                                            None, None, \
                                                            VariableDescr)
      
      # TOLERANCE2APPROXCURVE (float):
      # massimo errore tollerato tra una vera curva e quella approssimata dai segmenti retti
      # (nel sistema map-coordinate)
      VariableName = QadMsg.translate("Environment variables", "TOLERANCE2APPROXCURVE") # x lupdate
      VariableDescr = QadMsg.translate("Environment variables", "Massimo errore tollerato tra una vera curva e quella approssimata dai segmenti retti." + \
                                       "\nTipo reale.") # x lupdate
      self.__VariableValuesDict[VariableName] = QadVariable(VariableName, float(0.1), \
                                                            QadVariableTypeEnum.FLOAT, \
                                                            0.000001, None, \
                                                            VariableDescr)
      

   def getVarNames(self):
      """
      Ritorna la lista dei nomi delle variabili 
      """
      return self.__VariableValuesDict.keys()
          
   def set(self, VarName, VarValue):
      """
      Modifica il valore di una variabile 
      """
      UpperVarName = VarName.upper()
      variable = self.getVariable(VarName)
      
      if variable is None: # se non c'è la variablie
         self.__VariableValuesDict[VariableName] = QadVariable(UpperVarName, VarValue, \
                                                               QadVariableTypeEnum.UNKNOWN, \
                                                               None, None, \
                                                               "")
      else:
         if type(variable.value) != type(VarValue):
            if not((type(variable.value) == unicode or type(variable.value) == str) and
                   (type(VarValue) == unicode or type(VarValue) == str)):
               return False
         if variable.typeValue == QadVariableTypeEnum.COLOR:
            if len(VarValue) == 7: # es. "#FF0000"
               if VarValue[0] != "#":
                  return False
            else:
               return False
         elif variable.typeValue == QadVariableTypeEnum.FLOAT or \
              variable.typeValue == QadVariableTypeEnum.INT:
            if variable.minNum is not None:
               if VarValue < variable.minNum:
                  return False 
            if variable.maxNum is not None:
               if VarValue > variable.maxNum:
                  return False 
         
         self.__VariableValuesDict[UpperVarName].value = VarValue

      return True
       
   def get(self, VarName, defaultValue = None):
      """
      Restituisce il valore di una variabile 
      """
      variable = self.getVariable(VarName)
      if variable is None:
         result = defaultValue
      else:
         result = variable.value
      
      return result

   def getVariable(self, VarName):
      UpperVarName = VarName
      return self.__VariableValuesDict.get(UpperVarName.upper())
        
   def save(self, Path=""):
      """
      Salva il dizionario delle variabili su file 
      """
      if Path == "":
         # Se la path non é indicata uso il file "qad.ini" in 
         Path = QDir.cleanPath(QgsApplication.qgisSettingsDirPath()) + "python/plugins/qad/"
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
         # Se la path non é indicata uso il file "qad.ini" in 
         Path = QDir.cleanPath(QgsApplication.qgisSettingsDirPath()) + "python/plugins/qad/"
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
#  = variabile globale
#===============================================================================

QadVariables = QadVariablesClass()
