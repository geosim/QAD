QAD (Quantum Aided Design)
==========================

Introduzione
------------

L’dea di QAD nasce per arricchire QGIS di tutte le funzionalità CAD
necessarie per l’editazione professionale delle geometrie.

Filosofia di lavoro
-------------------

QAD ha una logica di lavoro diversa da QGIS e più vicina ai più diffusi
software CAD.

Per abbassare i tempi di apprendimento QAD si inspira alla logica del
CAD più diffuso al mondo. Il presente manuale dà per scontato che
l’utente abbia già conoscenza dell’ambiente e dei comandi del CAD più
diffuso al mondo. In caso contrario avvalersi di documentazione
appropriata (esiste una grande quantità di manuali) oppure ricercare il
comando su internet.

I comandi di QAD non hanno le stesse opzioni di quelli di del CAD più
diffuso al mondo in quanto il contesto di QGIS è differente (solitamente
opzioni relative all’aspetto grafico) inoltre alcuni comandi hanno delle
opzioni in più. In questo manuale saranno descritte solo le opzioni non
presenti nel corrispondente comando del CAD più diffuso al mondo.

Il sistema di riferimento corrente del progetto deve essere un sistema
di coordinate proiettate e non un sistema geografico.

Layer
-----

QAD supporta tutti i tipi di layer vettoriali di QGIS con una
distinzione per quanto riguarda i layer puntuali. Infatti QAD tratta i
layer puntuali di QGIS distinguendoli tra layer simboli e layer testi. I
primi hanno lo scopo di visualizzare dei simboli mentre i secondi hanno
lo scopo di visualizzare dei testi.

Il layer testo è un layer che visualizza esclusivamente delle etichette.
Si tratta di un layer QGIS puntuale con le seguenti caratteristiche:

1. il simbolo deve avere una trasparenza di almeno il 90%

2. deve avere una etichetta

I layer puntuali che non sono testuali, verranno considerati dei layer
simboli.

Modello del layer testuale:
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Il layer testuale deve avere i seguenti campi:

-  un campo carattere per memorizzare il testo

Campi opzionali:

-  un campo numerico reale per memorizzare l’altezza del testo (in unità
   di mappa)

-  un campo numerico reale per memorizzare la rotazione del testo (gradi
   in senso antiorario dove lo zero = orizzontale a dx)

Il layer testuale deve essere definito con le etichette impostate come
segue:

-  Ia dimensione può essere letta da un campo numerico reale che
   memorizza l’altezza del testo (in unità di mappa, scheda
   <Etichette>-<Testo>, se impostata verrà richiesta dal comando TESTO)

-  Ia rotazione può essere letta da un campo numerico reale che
   memorizza la rotazione del testo (gradi in senso antiorario dove lo
   zero = orizzontale a dx), opzione <Mantieni i valori di rotazione>
   attivata (scheda <Etichette >-<Posizionamento>, se impostata verrà
   richiesta dal comando TESTO)

Modello del layer simbolo:
~~~~~~~~~~~~~~~~~~~~~~~~~~

Il layer simbolo può avere i seguenti campi opzionali:

-  un campo numerico reale per memorizzare la rotazione del simbolo
   (gradi in senso antiorario dove lo zero = orizzontale a dx)

-  un campo numerico reale per memorizzare la scala del simbolo

Il layer simboli può essere definito con lo stile impostato come segue:

-  Se si decide di gestire rotazione o scala dei simboli allora
   l’opzione <Stile>-<Simbolo singolo> va attivata, l’opzione
   <Stile>-<Unità di mappa> va attivata

-  La rotazione può essere letta da un campo numerico reale che
   memorizza la rotazione del simbolo attraverso la formula “360 -
   <campo che memorizza la rotazione>” (gradi in senso antiorario dove
   lo zero = orizzontale a dx, opzione <Stile>-<Avanzato>-"Nome del
   campo di rotazione”-<Espressione>, se impostata verrà richiesta dal
   comando INSER)

-  La scala può essere letta da un campo numerico reale che memorizza la
   scala del simbolo (opzioni <Stile>-< Avanzato>-<Campo di dimensione
   della scala >-“nome del campo di dimensione della scala” e l’opzione
   < Avanzato>-<Campo di dimensione della scala>-<Diametro scala>, se
   impostata verrà richiesto dal comanda INSER)

Archi e cerchi
~~~~~~~~~~~~~~

QAD supporta archi e cerchi approssimandoli in piccoli segmenti.

-  Per l’arco il numero di questi segmenti dipende dalla variabile
   TOLERANCE2APPROXCURVE e ARCMINSEGMENTQTY (numero minimo di segmenti
   da usare per l‘approssimazione)

-  Per il cerchio Il numero di questi segmenti dipende dalla variabile
   TOLERANCE2APPROXCURVE e CIRCLEMINSEGMENTQTY (numero minimo di
   segmenti da usare per l‘approssimazione)

TOLERANCE2APPROXCURVE determina l’errore massimo in unità di mappa
corrente tra la curva teorica e la linea segmentata usata per
l’approssimazione

|image0|

Massimo errore di approssimazione

OSNAP
-----

Con il tasto F3 si attiva/disattiva la modalità di osnap.

Per modificare la modalità di osnap:

1. Durante la richiesta di un punto premere CTRL+tasto dx del mouse per
   scegliere una modalità di snap diversa dalla corrente.

2. | Durante la richiesta di un punto digitare nella riga di testo:
   | "NES" = nessuno snap
   | "FIN" = punti finali di ogni segmento
   | "FIN\_PL" = punti finali dell'intera polilinea
   | "MED" = punto medio
   | "CEN" = centro (centroide)
   | "NOD" = oggetto punto
   | "QUA" = punto quadrante
   | "INT" = intersezione
   | "INS" = punto di inserimento
   | "PER" = punto perpendicolare
   | "TAN" = tangente
   | "VIC" = punto più vicino
   | "APP" = intersezione apparente
   | "EST" = Estensione
   | "PAR" = Parallelo
   | "EST\_INT" = intersezione su estensione
   | "PR" = distanza progressiva (può essere seguito da un numero per
     impostare una distanza progressiva diversa dal default)

3. | Con il comando MODIVAR impostare la variabile OSMODE con una
     combinazione a bit usando lo schema seguente:
   | 0 = nessuno
   | 1 = punto finale
   | 2 = punto medio
   | 4 = centro (centroide)
   | 8 = oggetto punto
   | 16 = punto quadrante
   | 32 = intersezione
   | 64 = punto di inserimento
   | 128 = punto perpendicolare
   | 256 = tangente
   | 512 = punto più vicino
   | 1024 = pulisci all object snaps
   | 2048 = intersezione apparente
   | 4096 = Estensione
   | 8192 = Parallelo
   | 16384 = osnap disattivato
   | 65536 = distanza progressiva
   | 131072 = intersezione sull'estensione
   | 2097152 = punti finali dell'intera polilinea

4. Lanciare il comando IMPOSTADIS

Come specificare un punto
-------------------------

Le coordinate di un punto possono essere espresse nelle seguenti forme:

1) x,y

2) @lunghezza<angolo (dal punto precedente ci si sposta di una distanza
   usando un angolo)

3) @ x,y (dal punto precedente ci si sposta di una distanza sull’asse
   delle ascisse e una sull’asse delle ordinate)

4) @ (punto precedente)

5) Lunghezza (dal punto precedente ci si sposta di una distanza usando
   la posizione corrente del puntatore)

6) Coordinate espresse in un sistema di coordinate diverso da quello
   corrente

Coordinate espresse in un sistema di coordinate diverso da quello corrente
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Se il sistema di coordinate è proiettato:

digitare x,y (SRID). Ad esempio 1491621.64817, 4915622.63154 (EPSG:3003)
è un punto con coordinata X=1491621.64817 e Y=4915622.63154 nel sistema
proiettato EPSG:3003

Se il sistema di coordinate è geografico:

digitare la latitudine, longitudine (SRID). Ad esempio 44º 24' 48N/ 08º
50' 15E (EPSG:4326) è un punto con latitudine 44 gradi 24 minuti 48
secondi e longitudine 6 gradi 50 primi 15 secondi nel sistema geografico
EPSG:4326.

I valori di latitudine e longitudine possono essere impostati nei
seguenti formati:

-  Gradi decimali (DDD). In questa notazione la precisione decimale è
   impostata nella coordinata dei gradi, ad esempio, 49.11675953666N

-  Gradi, minuti e secondi (DMS). In questa notazione la precisione
   decimale è impostata nella coordinata dei secondi, ad esempio, 49
   7'20.06"N.

-  Gradi e minuti con secondi decimali (DMM). In questa notazione la
   precisione decimale è impostata nella coordinata dei minuti, ad
   esempio, 49 7.0055722"N. In questo caso, il valore precedente di
   20,06 secondi viene diviso per 3600 per ottenere il valore in minuti
   decimali per 20,06 secondi.

La sintassi della latitudine e della longitudine è la seguente:

-  | Valori numerici. Separa semplicemente ogni notazione di coordinata
     con uno spazio; il valore verrà riconosciuto correttamente. Ad
     esempio, puoi indicare una notazione DMS come 37 24 23.3, oppure
     potresti indicare una notazione DMM come 49 7.0055722
   | Puoi anche utilizzare il carattere (°) per i gradi, virgolette
     singole (') per i minuti e virgolette doppie (") per i secondi,
     come segue: 49°7'20.06"

-  | Notazione di direzione (Nord/Sud, Est/Ovest)
   | Utilizza "N", "S", "E" o "W" per indicare la direzione. La lettera
     può essere immessa in maiuscolo e minuscolo e può comparire prima o
     dopo il valore della coordinata. Ad esempio: N 37 24 23.3 è
     identico a 37 24 23.3 N
   | Puoi anche utilizzare il segno meno (-) per indicare una direzione
     a ovest o a sud. Se utilizzi questo tipo di notazione, non devi
     specificare un simbolo a lettera. In questo caso, non è neanche
     necessario aggiungere il segno più (+) per indicare una direzione a
     nord o a est. Questo è ad esempio un valore valido: 37 25 19.07,
     -122 05 08.40

-  | Immissione di coppie di latitudini e longitudini
   | Quando immetti le coppie di valori di latitudine e longitudine, la
     prima coordinata viene interpretata come latitudine a meno che
     specifichi una lettera di direzione (E o W). Ad esempio, puoi
     indicare la longitudine come: 122 05 08.40 W 37 25 19.07 N
   | Non puoi però utilizzare il segno meno per immettere prima la
     longitudine:-122 05 08.40 37 25 19.07
   | Puoi utilizzare uno spazio, una virgola o una barra per delimitare
     le coppie di valori: 37.7 N 122.2 W oppure 37.7 N,122.2 W oppure
     37.7 N/122.2 W

Selezione degli oggetti
-----------------------

Quando un comando richiede di selezionare degli oggetti (normalmente con
il messaggio “selezionare oggetti:”) è possibile digitare la lettera “H”
di Help per mostrare tutte le opzioni di selezione.

Le opzioni <FCerchio> e <ICerchio> selezionano rispettivamente gli
oggetti interni/intersecanti un cerchio e gli oggetti solo interni ad un
cerchio.

Le opzioni <FOggetti> e <IOggetti> selezionano rispettivamente gli
oggetti interni/intersecanti uno o più oggetti esistenti e gli oggetti
solo interni ad uno o più oggetti esistenti.

Le opzioni <FBuffer> e <IBuffer> selezionano rispettivamente gli oggetti
interni/intersecanti un buffer e gli oggetti solo interni ad un buffer.

Quotatura
---------

Uno stile di quotatura è un insieme di proprietà che determinano
l’aspetto delle quote. Tali proprietà vengono archiviate in file con
estensione .dim e sono caricati all’avvio di QAD o al caricamento di un
progetto. I files di quotatura devono essere salvati nella cartella del
progetto corrente oppure nella cartella personale del plugin QAD (ad
esempio in windows 8 “C:\\Users\\\ *utente
corrente*\\.qgis2\\python\\plugins\\qad”).

QAD memorizza gli elementi costituenti una quotatura in 3 layer
distinti:

-  Layer testuale per memorizzare i testi delle quote

-  Layer simbolo per memorizzare gli elementi puntuali delle quote
   (punti di quotatura, simboli freccia…)

-  Layer lineare per memorizzare gli elementi lineari delle quote(linea
   di quota, linee di estensione…)

Modello del layer testuale per la quotatura:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L’elemento principale di una quota è il testo il cui layer testuale deve
avere i seguenti campi:

-  un campo carattere per memorizzare il testo della quota

-  un campo carattere per memorizzare il font del testo della quota

-  un campo numerico reale per memorizzare l’altezza del testo della
   quota (in unità di mappa)

-  un campo numerico reale per memorizzare la rotazione del testo della
   quota (gradi in senso antiorario dove lo zero = orizzontale a dx)

Campi opzionali:

-  | un campo numerico intero per memorizzare il codice identificativo
     univoco della quota.
   | Questo campo è necessario se si desidera raggruppare gli elementi
     di una stessa quotatura e quindi usare le funzioni di cancellazione
     e modifica di una quota esistente. Poiché deve essere un campo con
     valori univoci, attualmente è supportato solo per tabelle in
     PostGIS in cui deve essere stato creato un campo di tipo serial non
     nullo che deve essere chiave primaria della tabella (es.”id”).
     Oltre a questo campo deve esistere un altro campo di tipo bigint
     gestito da QAD allo scopo di memorizzare il codice identificativo
     della quota (es. dim\_id”). I files shape non consentono il
     raggruppamento degli oggetti di una stessa quota quindi, dopo aver
     disegnato una quota, ogni oggetto sarà indipendente dagli altri.

-  un campo carattere per memorizzare il colore del testo della quota

-  un campo carattere per memorizzare il nome dello stile di quotatura
   (necessario se si desidera usare le funzioni di modifica di una quota
   esistente)

-  | un campo carattere (2 caratteri) per memorizzare il tipo dello
     stile di quotatura (allineata, lineare …) secondo il seguente
     schema:
   | "AL" = quota lineare allineata ai punti di origine delle linee di
     estensione
   | "AN" = quota angolare, misura l'angolo tra i 3 punti o tra gli
     oggetti selezionati
   | "BL" = quota lineare, angolare o coordinata a partire dalla linea
     di base della quota precedente o di una quota selezionata
   | "DI" = quota per il diametro di un cerchio o di un arco
   | "LD" = crea una linea che consente di collegare un'annotazione ad
     una lavorazione
   | "LI" = quota lineare con una linea di quota orizzontale o verticale
   | "RA" = quota radiale, misura il raggio di un cerchio o di un arco
     selezionato e visualizza il testo di quota con un simbolo di raggio
     davanti
   | "AR" = quota per la lunghezza di un cerchio o di un arco
   | (necessario se si desidera usare le funzioni di modifica di una
     quota esistente)

Un esempio di SQL per generare la tabella PostGIS e i relativi indici
per i testi delle quotature:

CREATE TABLE qad\_dimension.dim\_text

(

id serial NOT NULL,

text character varying(50) NOT NULL,

font character varying(50) NOT NULL,

h\_text double precision NOT NULL,

rot double precision NOT NULL,

color character varying(10) NOT NULL,

dim\_style character varying(50) NOT NULL,

dim\_type character varying(2) NOT NULL,

geom geometry(Point,3003),

dim\_id bigint NOT NULL,

CONSTRAINT dim\_text\_pkey PRIMARY KEY (id)

)

WITH (

OIDS=FALSE

);

CREATE INDEX dim\_text\_dim\_id

ON qad\_dimension.dim\_text

USING btree

(dim\_id);

CREATE INDEX sidx\_dim\_text\_geom

ON qad\_dimension.dim\_text

USING gist

(geom);

Il layer testuale deve essere definito con le etichette impostate come
segue:

-  Il font deve essere letto da un apposito campo carattere che
   memorizza il font del testo della quota (scheda
   <etichette>-<testo>-<Carattere>)

-  Ia dimensione deve essere letta da un campo numerico reale che
   memorizza l’altezza del testo della quota (in unità di mappa, scheda
   <etichette>-<testo>)

-  Ia rotazione deve essere letta da un campo numerico reale che
   memorizza la rotazione del testo della quota (gradi in senso
   antiorario dove lo zero = orizzontale a dx), opzione <Mantieni i
   valori di rotazione> attivata (scheda <etichette>-<Posizionamento>)

-  Posizionamento <Intorno al punto> con distanza = 0 (scheda <
   etichette >-<Posizionamento>)

-  Opzione <Mostra tutte le etichette> attivata (scheda
   <etichette>-<Visualizzazione>)

-  Opzione <Mostra le etichette capovolte> con valore <sempre> (scheda <
   etichette >-<Visualizzazione>)

-  Opzione <Evita che le etichette si sovrappongano alle geometrie>
   disattivata (scheda < Etichette >-<Visualizzazione>)

Impostazioni opzionali:

-  Il colore può essere letto da un campo carattere che memorizza il
   colore del testo della quota (scheda <Etichette>-<testo>)

Modello del layer simboli per la quotatura:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

I simboli di una quota (frecce…) devono essere memorizzati in un layer
simboli con i seguenti campi:

-  un campo numerico reale per memorizzare la rotazione del simbolo
   della quota (gradi in senso antiorario dove lo zero = orizzontale a
   dx, usare espressione “360-campo\_rotazione”)

Campi opzionali:

-  un campo carattere per memorizzare il nome del simbolo

-  un campo numerico reale per memorizzare la scala del simbolo

-  | un campo carattere (2 caratteri) per memorizzare il tipo di oggetto
     puntuale che compone la quota secondo il seguente schema:
   | "B1" = primo blocco della freccia ("Block 1")
   | "B2" = secondo blocco della freccia ("Block 2")
   | "LB" = blocco della freccia nel caso leader ("Leader Block")
   | "AB" = simbolo dell'arco ("Arc Block")
   | "D1" = primo punto da quotare ("Dimension point 1")
   | "D2" = secondo punto da quotare ("Dimension point 2")
   | (necessario se si desidera usare le funzioni di modifica di una
     quota esistente)

-  un campo numerico intero per memorizzare il codice parente del testo
   che identifica la quota di appartenenza (necessario se si desidera
   raggruppare gli elementi di una stessa quotatura e quindi usare le
   funzioni di cancellazione e modifica di una quota esistente)

Un esempio di SQL per generare la tabella PostGIS e i relativi indici
per i simboli delle quotature:

CREATE TABLE qad\_dimension.dim\_symbol

(

name character varying(50),

scale double precision,

rot double precision,

color character varying(10),

type character varying(2) NOT NULL,

id\_parent bigint NOT NULL,

geom geometry(Point,3003),

id serial NOT NULL,

CONSTRAINT dim\_symbol\_pkey PRIMARY KEY (id)

)

WITH (

OIDS=FALSE

);

CREATE INDEX dim\_symbol\_id\_parent

ON qad\_dimension.dim\_symbol

USING btree

(id\_parent);

CREATE INDEX sidx\_dim\_symbol\_geom

ON qad\_dimension.dim\_symbol

USING gist

(geom);

Il layer simboli deve essere definito con lo stile impostato come segue:

-  Opzione <Simbolo singolo> attivata (scheda <Stile>)

-  Opzione <Unità di mappa> attivata (scheda <Stile>)

-  Impostare la dimensione del simbolo in modo che la larghezza della
   freccia sia 1 unità di mappa (scheda <Stile>)

-  La rotazione deve essere letta da un campo numerico reale che
   memorizza la rotazione del simbolo attraverso la formula “360 -
   <campo che memorizza la rotazione>” (gradi in senso antiorario dove
   lo zero = orizzontale a dx, scheda <Stile>-< Avanzato>-"Nome del
   campo di rotazione”-<Espressione>)

-  La scala deve essere letta da un campo numerico reale che memorizza
   la scala del simbolo (opzioni <Stile>-<Avanzato>-<Campo di dimensione
   della scala >-“nome del campo di dimensione della scala” e l’opzione
   <Stile>-<Avanzato>-<Campo di dimensione della scala>-<Diametro
   scala>)

Il simbolo della freccia quando inserito con rotazione = 0 deve essere
orizzontale con la freccia rivolta verso destra ed il suo punto di
inserimento deve essere sulla punta della freccia.

Modello del layer lineare per la quotatura:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Gli elementi lineari di una quota (linea di quota, linee di estensione
…) devono essere memorizzati in un layer lineare con i seguenti campi:

-  Nessun campo obbligatorio

Campi opzionali:

-  un campo carattere per memorizzare il colore delle linee di quota

-  un campo carattere per memorizzare il tipolinea delle linee di quota

-  | un campo carattere (2 caratteri) per memorizzare il tipo di oggetto
     lineare che compone la quota secondo il seguente schema:
   | "D1" = linea di quota 1 ("Dimension line 1")
   | "D2" = linea di quota 2 ("Dimension line 2")
   | "E1" = prima linea di estensione ("Extension line 1")
   | "E2" = seconda linea di estensione ("Extension line 2")
   | "L" = linea porta quota usata quando il testo é fuori dalla quota
     ("Leader")
   | (necessario se si desidera usare le funzioni di modifica di una
     quota esistente)

-  un campo numerico intero per memorizzare il codice identificativo
   univoco della quota (necessario se si desidera raggruppare gli
   elementi di una stessa quotatura e quindi usare le funzioni di
   cancellazione e modifica di una quota esistente)

Un esempio di SQL per generare la tabella PostGIS e i relativi indici
per le linee delle quotature:

CREATE TABLE qad\_dimension.dim\_line

(

line\_type character varying(50),

color character varying(10),

type character varying(2) NOT NULL,

id\_parent bigint NOT NULL,

geom geometry(LineString,3003),

id serial NOT NULL,

CONSTRAINT dim\_line\_pkey PRIMARY KEY (id)

)

WITH (

OIDS=FALSE

);

CREATE INDEX dim\_line\_id\_parent

ON qad\_dimension.dim\_line

USING btree

(id\_parent);

CREATE INDEX sidx\_dim\_line\_geom

ON qad\_dimension.dim\_line

USING gist

(geom);

Il layer lineare deve essere definito con lo stile impostato come segue:

Impostazioni opzionali:

-  Il colore può essere letto da un campo carattere che memorizza il
   colore delle linee della quota

-  Il tipolinea può essere letto da un campo carattere che memorizza il
   tipolinea delle linee della quota

I comandi di quotatura (DIMLINEARE, DIMALLINEATA) fanno riferimento allo
stile di quotatura corrente. Per impostare lo stile di quotatura
corrente lanciare il comando DIMSTILE.

Personalizzazione dei comandi
-----------------------------

La personalizzazione dei comandi da tastiera (*shortcuts*) avviene
attraverso il file qad\_<lingua>\_<regione>.pgp (utf-8).

<lingua> rappresenta il linguaggio corrente di QGIS (obbligatorio) e
<regione> rappresenta la regione linguistica corrente (opzionale). Ad
esempio qad\_pt\_br.pgp rappresenta il file in lingua portoghese della
regione del brasile, qad\_en.pgp è il file pgp per la lingua inglese. Il
file è ricercato da QAD seguendo i percorsi indicati dalla variabile di
sistema SUPPORTPATH.

Comandi
-------

I comandi sono attivabili da menu VETTORE->QAD oppure da toolbar o da
linea di comando. I comandi e le relative opzioni possono essere
specificati in inglese anteponendo il carattere “\_” al nome (es.
\_LINE) indipendentemente dalla lingua usata in QGIS.

Un comando di QAD può essere interrotto in qualsiasi momento
dall’attivazione di un altro tool. Per riprendere l’esecuzione del
comando precedentemente interrotto e rendere attivo l’ambiente QAD usare
la voce di menu QAD nel menu di QAD oppure premere il bottone |image1|
nella toolbar.

Durante la digitazione del nome di un comando verrà visualizzata una
lista di comandi che inizia per ciò che è stato scritto. Digitando “\*”
comparirà la lista di tutti i comandi di QAD.

Per scegliere un’opzione di comando digitare le lettere in maiuscolo
relative all’opzione oppure fare click sull’opzione desiderata.

ANNULLA
~~~~~~~

Annulla le modifiche effettuate tramite QAD.

I comandi di QAD che creano modificano o cancellano oggetti, agiscono su
tutti i layer visibili e modificabili e non solo sul layer corrente come
QGIS. Per questo motivo QAD utilizza un suo sistema di undo/redo che
agisce su tutti i layer coinvolti dai comandi di QAD.

*Se l’utente utilizzerà il comando di annulla/ripristina di QGIS, QAD
perderà l’allineamento con la storia delle modifiche fatte con i suoi
comandi e quindi verrà svuotato lo stack annulla/ripristina di QAD.*

ARCO
~~~~

Disegna un arco.

ARCOQUOTA
~~~~~~~~~

Disegna una quota di lunghezza arco.

ALLUNGA
~~~~~~~

Allunga un oggetto.

CANCELLA
~~~~~~~~

Cancella uno o più oggetti.

CERCHIO
~~~~~~~

Disegna un cerchio.

COPIA
~~~~~

Copia uno o più oggetti.

DIMALLINEATA
~~~~~~~~~~~~

Disegna una quota allineata.

DIMLINEARE
~~~~~~~~~~

Disegna una quota lineare.

DIMSTILE
~~~~~~~~

Crea, modifica, compara gli stili di quota. Setta lo stile di quota
corrente.

EDITPL
~~~~~~

Modifica una polilinea. L’opzione <Semplifica> richiede di specificare
il valore di una tolleranza usata per semplificare la geometria.

ESTENDI
~~~~~~~

Estende uno o più oggetti.

GUIDA
~~~~~

Visualizza la guida di QAD.

ID
~~

Visualizza le coordinate della posizione specificata.

IMPOSTADIS
~~~~~~~~~~

Imposta alcune proprietà per disegnare.

INSER
~~~~~

Inserisce un simbolo. Se la scala del simbolo è derivata da un campo
allora il comando chiederà di indicare il fattore di scala. Se la
rotazione del simbolo è derivata da un campo allora il comando chiederà
di indicare la rotazione (in gradi). Valido solo per layer simboli.

LINEA
~~~~~

Disegna una linea.

MAPMPEDIT
~~~~~~~~~

Modifica la geometria di un poligono selezionato.

-  L’opzione <Aggiungi> aggiunge una geometria esistente al poligono
   selezionato (es. un’isola).

-  L’opzione <Cancella> cancella una geometria al poligono selezionato
   (es. un’isola).

-  L’opzione <Unisci> modifica la geometria del poligono selezionato con
   il risultato dell’unione della stessa con un gruppo di poligoni.

-  L’opzione <Sottrai> modifica la geometria del poligono selezionato
   con il risultato della sottrazione della stessa con un gruppo di
   poligoni.

-  L’opzione <Interseca> modifica la geometria del poligono selezionato
   con il risultato dell’intersezione della stessa con un gruppo di
   poligoni.

-  L’opzione <includi Oggetti> modifica la geometria del poligono
   selezionato affinche possa includere le geometrie di un gruppo di
   oggetti.

-  L’opzione <aNnulla> annulla l’ultima operazione.

MBUFFER
~~~~~~~

Disegna un buffer intorno agli oggetti selezionati. Selezionare gli
oggetti quindi specificare la larghezza del buffer.

MODIVAR
~~~~~~~

Elenca o modifica i valori delle variabili di QAD. Una volta indicato il
nome di una variabile di QAD, viene mostrata una spiegazione sintetica e
il tipo della variabile (reale, intero, carattere, logico)

MPOLIGONO
~~~~~~~~~

Disegna un poligono usando le stesse opzioni del comando PLINEA.

OFFSET
~~~~~~

Disegna cerchi concentrici, linee ed archi paralleli ad oggetti
esistenti.

OPZIONI
~~~~~~~

Personalizza le impostazioni di QAD.

PLINEA
~~~~~~

Disegna una polilinea. L’opzione <Ricalca> è usata per ricalcare un
oggetto esistente. Durante il disegno della polilinea, posizionarsi su
un punto qualsiasi di un oggetto da ricalcare, selezionare l’opzione
<Ricalca> e selezionare l’oggetto nel punto finale di ricalco.

POLIGONO
~~~~~~~~

Disegna un poligono regolare. Dopo aver indicato il centro, l’opzione
<Area> consente di calcolare il poligono.

RACCORDO
~~~~~~~~

Disegna un raccordo tra oggetti esistenti.

RETTANGOLO
~~~~~~~~~~

Disegna un rettangolo.

RIPRISTINA
~~~~~~~~~~

Ripristina le modifiche annullate tramite il comando ANNULLA.

RUOTA
~~~~~

Ruota gli oggetti selezionati.

SCALA
~~~~~

Scala gli oggetti selezionati.

SERIE
~~~~~

Crea copie di oggetti disposti in un modello.

SERIEPOLARE
~~~~~~~~~~~

Distribuisce uniformemente copie di oggetti in un modello circolare
attorno a un punto centrale.

SERIERETTANG
~~~~~~~~~~~~

Distribuisce copie di oggetti in qualsiasi combinazione di righe e
colonne.

SERIETRAIETT
~~~~~~~~~~~~

Distribuisce uniformemente copie di oggetti lungo una traiettoria o
porzione di una traiettoria.

SETCURRLAYERDAGRAFICA
~~~~~~~~~~~~~~~~~~~~~

Rende corrente il layer dell’oggetto selezionato.

SETCURRMODIFLAYERDAGRAFICA
~~~~~~~~~~~~~~~~~~~~~~~~~~

Rende editabili i layer degli oggetti selezionati. Se si tratta di un
solo layer questo diventa anche quello corrente.

SPECCHIO
~~~~~~~~

Crea una copia speculare degli oggetti selezionati.

SPEZZA
~~~~~~

Divide l’oggetto selezionato.

SPOSTA
~~~~~~

Sposta gli oggetti selezionati.

STIRA
~~~~~

Stira gli oggetti selezionati.

TAGLIA
~~~~~~

Accorcia o allunga gli oggetti selezionati.

TESTO
~~~~~

Inserisce un testo. Se l’altezza testo è derivata da un campo allora il
comando chiederà di indicare l’altezza testo. Se la rotazione del testo
è derivata da un campo allora il comando chiederà di indicare la
rotazione (in gradi). Il comando infine chiederà il valore dei campi che
concorrono a formare il testo. Valido solo per layer testuali.

Modalità Grip
-------------

E’ possibile spostare I punti di grip per attivare i comandi stira,
sposta, ruota, scala o specchio.

L’operazione richiesta in questo modo è chiamata modalità grip.

I grip sono piccoli quadratini colorati che sono visualizzati in punti
strategici degli oggetti precedentemente selezionati con il dispositivo
di puntamento.

Quando i grip sono attivati, si possono selezionare gli oggetti che si
vogliono usare prima di indicare il comando, quindi manipolare gli
oggetti con il dispositivo di puntamento.

Nota: I *Grip non sono visualizzati per gli oggetti su layer non
editabili.*

Per copiare l’oggetto selezionato, mantenere premuto il tasto Ctrl
durante la sua manipolazione.

Per modificare gli oggetti usando i punti di grip:

1. Selezionare l’oggetto da editare.

2. | Selezionare e muovere i punti di grip per stirare l’oggetto.
   | Nota: Nel caso di alcuni oggetti per esempio, simboli o testi,
     l’operazione di stiramento muoverà l’oggetto invece di stirarlo.

3. Premere Invio, la barra di spazio o click destroy per ciclare le
   operazioni di sposta, ruota, scala o specchio in modalità grip.

4. Puntare su un punto di grip per vedere ed accedere al menu di grip
   multifunzionale (se disponibile).

Variabili di sistema
--------------------

Le variabili di Sistema sono delle impostazioni che controllano il
comportamento di alcuni comandi. Possono essere di tipo intero, reale,
carattere, booleano or colori RGB (es. “#FF0000”). **Se esiste un
progetto corrent**\ e, sono salvate e caricate nel file <nome progetto
corrente>\_QAD.INI della cartella del progetto corrente altrimenti verrà
usato il file QAD.INI situato nella cartella di installazione.

APBOX
~~~~~

Come i CAD più popolari.

APERTURE
~~~~~~~~

Come i CAD più popolari.

ARCMINSEGMENTQTY
~~~~~~~~~~~~~~~~

Numero minimo di segmenti per approssimare un arco. Valori validi da 4 a
999, tipo intero, valore predefinito 12.

AUTOSNAP
~~~~~~~~

Come i CAD più popolari.

AUTOSNAPCOLOR
~~~~~~~~~~~~~

Colore dei simboli di snap.

AUTOSNAPSIZE
~~~~~~~~~~~~

Dimensione dei simboli di autosnap in pixel.

AUTOTRACKINGVECTORCOLOR
~~~~~~~~~~~~~~~~~~~~~~~

Imposta il colore del vettore autotrack (linee polari, linee di
estensione).

CIRCLEMINSEGMENTQTY
~~~~~~~~~~~~~~~~~~~

Numero minimo di segmenti per approssimare un cerchio. Valori validi da
6 to 999, tipo intero, valore predefinito 12.

CMDHISTORYBACKCOLOR
~~~~~~~~~~~~~~~~~~~

Imposta il colore di sfondo della finestra di cronologia dei comandi.

CMDHISTORYFORECOLOR
~~~~~~~~~~~~~~~~~~~

Imposta il colore del testo della finestra di cronologia dei comandi.

CMDINPUTHISTORYMAX
~~~~~~~~~~~~~~~~~~

Come i CAD più popolari.

CMDLINEBACKCOLOR
~~~~~~~~~~~~~~~~

Imposta il colore di sfondo della finestra dei comandi.

CMDLINEFORECOLOR
~~~~~~~~~~~~~~~~

Imposta il colore del testo della finestra dei comandi.

CMDLINEOPTBACKCOLOR
~~~~~~~~~~~~~~~~~~~

Imposta il colore di sfondo della parola chiave opzione di comando.

CMDLINEOPTCOLOR
~~~~~~~~~~~~~~~

Imposta il colore della parola chiave opzione di comando.

CMDLINEOPTHIGHLIGHTEDCOLOR
~~~~~~~~~~~~~~~~~~~~~~~~~~

Imposta il colore della opzione di comando evidenziata.

COPYMODE
~~~~~~~~

Come i CAD più popolari.

CROSSINGAREACOLOR
~~~~~~~~~~~~~~~~~

Come i CAD più popolari.

CURSORCOLOR
~~~~~~~~~~~

Colore del puntatore a croce. Valori validi colori RGB, tipo colore,
valore predefinito rosso =“#FF0000”.

CURSORSIZE
~~~~~~~~~~

Come i CAD più popolari.

DELOBJ
~~~~~~

| Controlla se la geometria utilizzata per creare altri oggetti viene
  mantenuta o eliminata.
| 0 = Viene mantenuta l'intera geometria di definizione. Questa
  impostazione prevede la conservazione degli oggetti di origine per
  tutti i comandi di serie.
| 1 = Elimina tutta la geometria di definizione.
| -1 = Viene visualizzato un messaggio di richiesta per l'eliminazione
  di tutta la geometria di definizione.

DIMSTYLE
~~~~~~~~

Come i CAD più popolari.

EDGEMODE
~~~~~~~~

Come i CAD più popolari.

FILLETRAD
~~~~~~~~~

Come i CAD più popolari.

GRIPCOLOR
~~~~~~~~~

Come i CAD più popolari.

GRIPCONTOUR
~~~~~~~~~~~

Come i CAD più popolari.

GRIPHOT
~~~~~~~

Come i CAD più popolari.

GRIPHOVER
~~~~~~~~~

Come i CAD più popolari.

GRIPMULTIFUNCTIONAL
~~~~~~~~~~~~~~~~~~~

| Specifica i metodi di accesso per le opzioni dei grip multifunzionali.
| 0 = Le opzioni dei grip multifunzionali non sono disponibili
| 2 = È possibile accedere alle opzioni dei grip multifunzionali tramite
  il menu dei grip visualizzato quando si passa con il mouse su un grip.

GRIPOBJLIMIT
~~~~~~~~~~~~

Come i CAD più popolari.

GRIPS
~~~~~

Come i CAD più popolari.

GRIPSIZE
~~~~~~~~

Come i CAD più popolari.

INPUTSEARCHDELAY
~~~~~~~~~~~~~~~~

Come i CAD più popolari.

INPUTSEARCHOPTIONS
~~~~~~~~~~~~~~~~~~

Come la variabile di Sistema AUTOCOMPLETEMODE dei CAD più popolari.

MAXARRAY
~~~~~~~~

Come i CAD più popolari.

OFFSETDIST
~~~~~~~~~~

Come i CAD più popolari.

OFFSETGAPTYPE
~~~~~~~~~~~~~

Come i CAD più popolari.

ORTHOMODE
~~~~~~~~~

Come i CAD più popolari.

OSMODE
~~~~~~

Come i CAD più popolari.

OSPROGRDISTANCE
~~~~~~~~~~~~~~~

Distanza progressiva per la modalità di snap <Distanza progressiva>.
Tipo reale, valore predefinito 0.

PICKADD
~~~~~~~

Come i CAD più popolari.

PICKBOX
~~~~~~~

Come i CAD più popolari.

PICKBOXCOLOR
~~~~~~~~~~~~

Imposta il colore del quadratino di selezione degli oggetti.

PICKFIRST
~~~~~~~~~

Come i CAD più popolari.

POLARANG
~~~~~~~~

Come i CAD più popolari.

POLARMODE
~~~~~~~~~

Come i CAD più popolari. Il valore 4 non è supportato (uso degli angoli
polari aggiuntivi).

SELECTIONAREA
~~~~~~~~~~~~~

Come i CAD più popolari.

SELECTIONAREAOPACITY
~~~~~~~~~~~~~~~~~~~~

Come i CAD più popolari.

SUPPORTPATH
~~~~~~~~~~~

Path di ricerca per i files di supporto. Tipo carattere.

SHOWTEXTWINDOW
~~~~~~~~~~~~~~

Visualizza la finestra di testo all'avvio. Tipo booleano, valore
predefinito vero.

TOLERANCE2APPROXCURVE
~~~~~~~~~~~~~~~~~~~~~

Massimo errore tollerato tra una vera curva e quella approssimata dai
segmenti retti. Valori validi da 0.000001, tipo reale, valore
predefinito 0.1.

WINDOWAREACOLOR
~~~~~~~~~~~~~~~

Come i CAD più popolari.

.. |image0| image:: media/image1.emf
   :width: 3.45139in
   :height: 1.86806in
.. |image1| image:: media/image2.png
   :width: 0.27083in
   :height: 0.27083in
