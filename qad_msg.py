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


import qad_debug


# traduction class.
class QadMsgClass():

   __Messages = dict()


   def __init__(self):
      self.__Messages[0]   = "Comando: "
      self.__Messages[1]   = "Finestra di testo QAD"
      self.__Messages[2]   = "\nComando sconosciuto \"{0}\"."
      self.__Messages[3]   = "ID" # nome di comando
      self.__Messages[4]   = "Specificare punto: "
      self.__Messages[5]   = "\nPunto non valido.\n"
      self.__Messages[6]   = "MODIVAR"      
      self.__Messages[7]   = "\nParola chiave dell'opzione non valida.\n"      
      self.__Messages[8]   = "\n*Annullato*\n"
      self.__Messages[9]   = "\nStringa non valida.\n"
      self.__Messages[10]  = "\nNumero intero non valido.\n"
      self.__Messages[11]  = "\nNumero reale non valido.\n"
      self.__Messages[12]  = "Digitare nome della variabile o [?]: "
      self.__Messages[13]  = "\nNome della variabile sconosciuto. Digitare MODIVAR ? per un elenco delle variabili."
      self.__Messages[14]  = "Digitare variabile/i da elencare <*>: "
      self.__Messages[15]  = "Digitare nuovo valore per {0} <{1}>: "
      self.__Messages[16]  = "NO"
      self.__Messages[17]  = "FALSO"
      self.__Messages[18]  = "\nNumero intero lungo non valido.\n"
      self.__Messages[19]  = "FIN" # punto finale                           
      self.__Messages[20]  = "MED" # punto medio             
      self.__Messages[21]  = "CEN" # centro (centroide)      
      self.__Messages[22]  = "NOD" # oggetto punto           
      self.__Messages[23]  = "QUA" # punto quadrante         
      self.__Messages[24]  = "INT" # intersezione            
      self.__Messages[25]  = "INS" # punto di inserimento    
      self.__Messages[26]  = "PER" # punto perpendicolare    
      self.__Messages[27]  = "TAN" # tangente                
      self.__Messages[28]  = "VIC" # punto più vicino           
      self.__Messages[29]  = "APP" # intersezione apparente
      self.__Messages[30]  = "EST" # Estensione            
      self.__Messages[31]  = "PAR" # Parallelo              
      self.__Messages[32]  = "PR"  # distanza progressiva 
      self.__Messages[33]  = "\n(impostato snap temporaneo)"     
      self.__Messages[34]  = "\nE' richiesto un punto o la parola chiave di un'opzione.\n"          
      self.__Messages[35]  = "PLINEA" # nome di comando       
      self.__Messages[36]  = "Specificare punto iniziale: "
      self.__Messages[37]  = "Specificare punto successivo o [Arco/LUnghezza/ANnulla/Ricalca]: "
      self.__Messages[38]  = "Arco"     
      self.__Messages[39]  = "LUnghezza"
      self.__Messages[40]  = "ANnulla"
      self.__Messages[41]  = "CHiudi"
      self.__Messages[42]  = "Specificare punto successivo o [Arco/Chiudi/LUnghezza/ANnulla/Ricalca]: "
      self.__Messages[43]  = "Specificare lunghezza della linea: "
      self.__Messages[44]  = "\nE' richiesto un punto o un numero reale.\n"
      self.__Messages[45]  = "\n<Snap disattivato>"
      self.__Messages[46]  = "\n<Snap attivato>"
      self.__Messages[47]  = "\n<Modalità  ortogonale attivata>"
      self.__Messages[48]  = "\n<Modalità  ortogonale disattivata>"
      self.__Messages[49]  = "SETCURRLAYERDAGRAFICA" # nome di comando
      self.__Messages[50]  = "Selezionare l'oggetto il cui layer diventerà quello corrente: "
      self.__Messages[51]  = "\nIl layer {0} è attivo"
      self.__Messages[52]  = "\nNon ci sono geometrie in questa posizione."
      self.__Messages[53]  = "\nIl layer corrente non è valido\n"
      self.__Messages[54]  = "ARCO" # nome di comando
      self.__Messages[55]  = "Specificare punto iniziale dell'arco o [Centro]: "
      self.__Messages[56]  = "Specificare secondo punto sull'arco o [Centro/Fine]: "
      self.__Messages[57]  = "Specificare punto finale dell'arco: "
      self.__Messages[58]  = "Specificare centro dell'arco: "
      self.__Messages[59]  = "Specificare punto iniziale dell'arco: " 
      self.__Messages[60]  = "Specificare punto finale dell'arco o [Angolo/Lunghezza corda]: " 
      self.__Messages[61]  = "Specificare angolo inscritto: " 
      self.__Messages[62]  = "Specificare lunghezza della corda: " 
      self.__Messages[63]  = "Specificare centro dell'arco o [Angolo/Direzione/Raggio]: " 
      self.__Messages[64]  = "Specificare direzione tangente per il punto iniziale dell'arco: " 
      self.__Messages[65]  = "Specificare raggio dell'arco: "
      self.__Messages[66]  = "Centro" 
      self.__Messages[67]  = "Fine" 
      self.__Messages[68]  = "Angolo" 
      self.__Messages[69]  = "Lunghezza" 
      self.__Messages[70]  = "Corda" 
      self.__Messages[71]  = "Specificare punto iniziale dell'arco: " 
      self.__Messages[72]  = "Direzione" 
      self.__Messages[73]  = "Raggio" 
      self.__Messages[74]  = "SETCURRMODIFLAYERDAGRAFICA" 
      self.__Messages[75]  = "INT_EST" # Intersezione sull'stensione     
      self.__Messages[76]  = "CERCHIO" # nome di comando
      self.__Messages[77]  = "Specificare punto centrale del cerchio o [3P/2P/Ttr (tangente tangente raggio)]: "
      self.__Messages[78]  = "3P"
      self.__Messages[79]  = "2P"
      self.__Messages[80]  = "Ttr"       
      self.__Messages[81]  = "Specificare raggio del cerchio o [Diametro]: "
      self.__Messages[82]  = "Diametro"              
      self.__Messages[83]  = "Specificare diametro del cerchio: " 
      self.__Messages[84]  = "Specificare primo punto sul cerchio: " 
      self.__Messages[85]  = "Specificare secondo punto sul cerchio: " 
      self.__Messages[86]  = "Specificare terzo punto sul cerchio: " 
      self.__Messages[87]  = "Specificare prima estremità del diametro del cerchio: " 
      self.__Messages[88]  = "Specificare seconda estremità del diametro del cerchio: " 
      self.__Messages[89]  = "Specificare oggetto per la prima tangente del cerchio: " 
      self.__Messages[90]  = "Specificare oggetto per la seconda tangente del cerchio: " 
      self.__Messages[91]  = "Specificare raggio del cerchio <{0}>: " 
      self.__Messages[92]  = "\nIl cerchio non esiste."
      self.__Messages[93]  = "Specificare secondo punto: " 
      self.__Messages[94]  = "\nSelezionare un cerchio, un arco o una linea." 
      self.__Messages[95]  = "Disegna un arco mediante diversi metodi" 
      self.__Messages[96]  = "Disegna un cerchio mediante diversi metodi" 
      self.__Messages[97]  = "Disegna un arco mediante diversi metodi" 
      self.__Messages[98]  = "Disegna una polilinea mediante diversi metodi.\n\nUna polilinea è una sequenza di segmenti retti,\narchi o una combinazione dei due." 
      self.__Messages[99]  = "Visualizza le coordinate di una posizione" 
      self.__Messages[101] = "Seleziona un layer di un oggetto grafico" 
      self.__Messages[102] = "Seleziona un layer di un oggetto grafico e lo rende modificabile" 
      self.__Messages[103] = "Imposta le variabili di ambiente di QAD" 
      self.__Messages[104] = "Specificare punto finale dell'arco o [Angolo/CEntro/CHiudi/Direzione/LInea/Raggio/Secondo punto/ANNulla]: " 
      self.__Messages[105] = "Specificare punto finale dell'arco o [Centro/Raggio]: " 
      self.__Messages[106] = "Specificare direzione della corda per l'arco <{0}>: " 
      self.__Messages[107] = "Specificare secondo punto sull'arco: " 
      self.__Messages[108] = "Linea" 
      self.__Messages[109] = "Secondo" 
      self.__Messages[110] = "ANNulla" 
      self.__Messages[111] = "IMPOSTADIS" # nome di comando 
      self.__Messages[112] = "Imposta il tipo di snap" 
      self.__Messages[113] = "Specificare punto finale dell'arco o [Angolo]: " 
      self.__Messages[114] = "\nE' richiesto un punto, un numero reale o la parola chiave di un'opzione.\n" 
      self.__Messages[115] = "\n<Modalità polare attivata>" 
      self.__Messages[116] = "\n<Modalità polare disattivata>" 
      self.__Messages[117] = "LINEA" 
      self.__Messages[118] = "Crea segmenti di linee rette." 
      self.__Messages[119] = "Specificare primo punto: " 
      self.__Messages[120] = "Specificare punto successivo o [Annulla]: " 
      self.__Messages[121] = "Specificare punto successivo o [Chiudi/Annulla]: " 
      self.__Messages[122] = "Annulla" 
      self.__Messages[123] = "Chiudi" 
      self.__Messages[124] = "\nNessuna tangente possibile" 
      self.__Messages[125] = "\nNessuna perpendicolare possibile" 
      self.__Messages[126] = "Ripeti " 
      self.__Messages[127] = "Comandi recenti" 
      self.__Messages[128] = "\nIl sistema di riferimento del progetto deve essere un sistema di coordinate proiettate\n" 
      self.__Messages[129] = "CANCELLA" # nome di comando 
      self.__Messages[130] = "Cancella oggetti dalla mappa" 
      self.__Messages[131] = "Selezionare oggetti" 
      self.__Messages[132] = "La finestra non è stata specificata correttamente." 
      self.__Messages[133] = "FCerchio"
      self.__Messages[134] = "Finestra"
      self.__Messages[135] = "Ultimo"
      self.__Messages[136] = "Interseca"
      self.__Messages[137] = "Riquadro"
      self.__Messages[138] = "Tutto"
      self.__Messages[139] = "NTercetta" # senza la I iniziale per non sovrapporsi a "Interseca"
      self.__Messages[140] = "FPoligono"
      self.__Messages[141] = "IPoligono"
      self.__Messages[142] = "AGgiungi"
      self.__Messages[143] = "Elimina"
      self.__Messages[144] = "Precedente"
      self.__Messages[145] = "ANnulla"
      self.__Messages[146] = "AUto"
      self.__Messages[147] = "SIngolo"
      self.__Messages[148] = "ICerchio"
      self.__Messages[149] = "Specificare primo angolo: "
      self.__Messages[150] = "Specificare angolo opposto: "
      self.__Messages[151] = "Specificare il primo punto di Intercetta: "
      self.__Messages[152] = "Specificare il punto successivo di Intercetta o [ANnulla]: " 
      self.__Messages[153] = "Primo punto del poligono: " 
      self.__Messages[154] = "Specificare punto finale della linea o [Annulla]: " 
      self.__Messages[155] = "Rimuovere oggetti" 
      self.__Messages[156] = " trovato(i) {0}, totale {1}" 
      self.__Messages[157] = "\nRisposta ambigua: specificare con maggior chiarezza...\n" 
      self.__Messages[158] = " o " 
      self.__Messages[159] = " ?\n" 
      self.__Messages[160] = "FOggetti" 
      self.__Messages[161] = "IOggetti" 
      self.__Messages[162] = "Selezionare oggetto: " 
      self.__Messages[163] = " o [Finestra/Ultimo/Interseca/Riquadro/Tutto/iNTercetta/FPoligono/IPoligono/FCerchio/ICerchio/FOggetti/IOggetti/FBuffer/IBuffer/AGgiungi/Elimina/Precedente/ANnulla/AUto/SIngolo/Help]" 
      self.__Messages[164] = ": " 
      self.__Messages[165] = "Help" 
      self.__Messages[166] = "MPOLYGON" 
      self.__Messages[167] = "Disegna un poligono mediante diversi metodi.\n\nUn poligono è una sequenza chiusa di segmenti retti,\narchi o una combinazione dei due." 
      self.__Messages[168] = "\nPoligono non valido.\n" 
      self.__Messages[169] = "MBUFFER" 
      self.__Messages[170] = "Crea poligoni originati da buffer intorno agli oggetti selezionati." 
      self.__Messages[171] = "Specificare larghezza buffer <{0}>: " 
      self.__Messages[172] = "FBuffer" 
      self.__Messages[173] = "IBuffer" 
      self.__Messages[174] = "Numero di segmenti per approssimazione curve <{0}>: " 
      self.__Messages[175] = "Ricalca"
      self.__Messages[176] = "\nSelezionare gli oggetti i cui layer diventeranno editabili: " 
      self.__Messages[177] = "\nIl layer {0} è editabile." 
      self.__Messages[178] = "Selezionare l'oggetto nel punto finale di ricalco: " 
      self.__Messages[179] = "RUOTA" 
      self.__Messages[180] = "Specificare punto base: " 
      self.__Messages[181] = "Specificare angolo di rotazione o [Copia/Riferimento] <{0}>: " 
      self.__Messages[182] = "\nRotazione di una copia degli oggetti selezionati." 
      self.__Messages[183] = "Specificare angolo di riferimento <{0}>: " 
      self.__Messages[184] = "Specificare nuovo angolo o [Punti] <{0}>: " 
      self.__Messages[185] = "Ruota gli oggetti selezionati rispetto ad un punto base." 
      self.__Messages[186] = "Copia" 
      self.__Messages[187] = "Riferimento" 
      self.__Messages[188] = "Punti" 
      self.__Messages[189] = "SPOSTA" 
      self.__Messages[190] = "Specificare punto base o [Spostamento] <Spostamento>: " 
      self.__Messages[191] = "Specificare lo spostamento <{0}, {1}>: " 
      self.__Messages[192] = "Sposta gli oggetti selezionati." 
      self.__Messages[193] = "Spostamento" 
      self.__Messages[194] = "Specificare secondo punto o <Utilizza primo punto come spostamento>: " 
      self.__Messages[195] = "SCALA" 
      self.__Messages[196] = "Ingrandisce o riduce gli oggetti selezionati." 
      self.__Messages[197] = "Specificare fattore di scala o [Copia/Riferimento] <{0}>: " 
      self.__Messages[198] = "Specificare lunghezza di riferimento <{0}>: " 
      self.__Messages[199] = "Specificare nuova lunghezza o [Punti] <{0}>: " 
      self.__Messages[200] = "\nScala di una copia degli oggetti selezionati." 
      self.__Messages[201] = "\nIl valore deve essere positivo e diverso da zero." 
      self.__Messages[202] = "COPIA" 
      self.__Messages[203] = "Copia gli oggetti selezionati ad una distanza e in una direzione specificate." 
      self.__Messages[204] = "Specificare il punto base o [Spostamento/mOdalità] <Spostamento>: " 
      self.__Messages[205] = "Spostamento" 
      self.__Messages[206] = "mOdalità" 
      self.__Messages[207] = "Digitare un'opzione di modalità di copia [Singola/Multipla] <{0}>: " 
      self.__Messages[208] = "Singola" 
      self.__Messages[209] = "Multipla" 
      self.__Messages[210] = "Specificare il secondo punto o [Serie] <utilizzare il primo punto come spostamento>: " 
      self.__Messages[211] = "Serie" 
      self.__Messages[212] = "Digitare il numero di elementi da disporre in serie <{0}>: " 
      self.__Messages[213] = "Specificare il secondo punto o [{0}]: " 
      self.__Messages[214] = "\nIl valore deve essere un intero compreso tra 2 e 32767." 
      self.__Messages[215] = "Specificare il secondo punto o [Serie/Esci/Annulla] <Esci>: " 
      self.__Messages[216] = "Esci" 
      self.__Messages[217] = "Annulla" 
      self.__Messages[218] = "Adatta" 
      self.__Messages[219] = "Specificare il punto base o [Spostamento/mOdalità /MUltiplo] <Spostamento>: " 
      self.__Messages[220] = "MUltiplo" 
      self.__Messages[221] = "OFFSET" 
      self.__Messages[222] = "Crea cerchi concentrici, linee e curve parallele." 
      self.__Messages[223] = "Specificare distanza di offset o [Punto/Cancella] <{0}>: " 
      self.__Messages[224] = "Punto" 
      self.__Messages[225] = "Cancella" 
      self.__Messages[226] = "Selezionare oggetto di cui eseguire l'offset o [Esci/ANnulla] <Esci>: " 
      self.__Messages[227] = "Esci" 
      self.__Messages[228] = "ANnulla" 
      self.__Messages[229] = "Cancellare l'oggetto sorgente dopo l'offset? [Sì/No] <{0}>: "
      self.__Messages[230] = "Sì"
      self.__Messages[231] = "No"
      self.__Messages[232] = "Specificare punto di passaggio o [Esci/MUltiplo/ANnulla] <Esci>: "
      self.__Messages[233] = "MUltiplo"
      self.__Messages[234] = "Specificare punto di passaggio o [Esci/ANnulla] <oggetto successivo>: "
      self.__Messages[235] = "Specificare punto sul lato di cui eseguire l'offset o [Esci/MUltiplo/ANnulla] <Esci>: "
      self.__Messages[236] = "Specificare punto sul lato di cui eseguire l'offset o [Esci/ANnulla] <oggetto successivo>: "
      self.__Messages[237] = ""
      self.__Messages[238] = ""
      self.__Messages[239] = ""
      
      
   def get(self, MsgNumber):
      if MsgNumber > len(self.__Messages) or MsgNumber < 0:
         return unicode("", encoding="latin1")
      else:
         return unicode(self.__Messages[MsgNumber], encoding="latin1")
      

#===============================================================================
# QadMsg = variabile globale
#===============================================================================

QadMsg = QadMsgClass()
