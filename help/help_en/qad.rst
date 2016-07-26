QAD (Quantum Aided Design)
==========================

Introduction
------------

The idea of QAD is to add QGIS of all CAD commands for editing
geometries in an professional way.

Work philosophy
---------------

QAD has a different logic by QGIS and closer to popular CAD software.

To reduce learning time, QAD is inspired to the most popular CAD. This
manual assumes that you have already the knowledge of the most popular
CAD environment and commands. Otherwise use the appropriate
documentation (there is a large amount of manuals) or search the command
on internet.

QAD commands haven’t the same options as those of the most popular CAD
since QGIS context is different (usually graphical options), some
commands have more options. This manual describes only the options not
present in the corresponding most popular CAD commands.

The current reference system of the project must be a projected
coordinate system and not a geographic system.

Layer
-----

QAD supports all types of vector layers of QGIS with a distinction
regarding the point layer. In fact, QAD manage layers of QGIS
distinguishing between symbols layers and text layers. The first display
symbols while the second display texts.

The text layer is a layer that displays labels only. It is a QGIS point
layer with the following characteristics:

1. the symbol must have a minimum of 90% transparency

2. must have a label

Layers that are not textual will be considered as symbol layers.

Text layer model:
~~~~~~~~~~~~~~~~~

The text layer must have the following fields:

-  a character field to store text

Optional fields:

-  a real number field to store the text height (map unit)

-  a real number field to store text rotation (degree counterclockwise
   where zero = horizontal to the right)

The textual layer must be defined with labels set as follows:

-  the size can be read from a real number field that stores the text
   height (in map units, tab <Labels>-<Text>, if set than the TEXT
   command will ask for it)

-  the rotation can be read from a real number field that stores text
   rotation (degree counterclockwise where zero = horizontal to the
   right), <Preserve data rotation values> option enabled (tab
   <Labels>-<Placement>, if set than the TEXT command will ask for it)

Symbol layer model:
~~~~~~~~~~~~~~~~~~~

The symbol layers may have the following optional fields:

-  a real number field to store the symbol rotation (degree
   counterclockwise where zero = horizontal to the right)

-  a real number field to store the symbol scale

The symbol layer can be defined with a style set as follows:

-  If you decide to handle the rotation or scale of symbols then the
   <Style>-<Single Symbol> option and <Style>-<map units> option must be
   enabled

-  The rotation could be read by a real number field that stores the
   symbol rotation through the formula "360-<field that stores the
   rotation>" (degree counterclockwise where zero = horizontal to the
   right, <Style>-<Advanced> option "rotation field name"-<Espressione>,
   if set than the INSERT command will ask for it)

-  The scale can be read by a real number field that stores the scale of
   the symbol (<Style>-<Advanced>-<Size scale field>-“ field that stores
   the scale” and <Style>-< Advanced >-<Size scale field >-<Scale
   diameter>, if set than the INSERT command will ask for it)

Arcs and circles
~~~~~~~~~~~~~~~~

QAD supports approximating arcs and circles in small segments.

-  For arcs the number of these segments depends on
   TOLERANCE2APPROXCURVE and ARCMINSEGMENTQTY variables (minimum number
   of segments to be used for the approximation)

-  For circles the number of these segments depends on
   TOLERANCE2APPROXCURVE and CIRCLEMINSEGMENTQTY variables (minimum
   number of segments to be used for the approximation)

|image0|

Maximum approximation error

OSNAP
-----

The F3 key activates/deactivates the osnap mode.

To change the osnap mode:

1. When a command ask for a point press CTRL + right mouse button to
   choose a different snap mode.

2. | When a command ask for a point type in the text window:
   | "NONE" = no snap
   | "END" = endpoints of each segment
   | "END\_PL" = endpoint of the entire polyline
   | "MID" = midpoint
   | "CEN" = center (centroid)
   | "NOD" = point object
   | "QUA" = quadrant point
   | "INT" = intersection
   | "INS" = insertion point
   | "PER" = perpendicular point
   | "TAN" = tangent
   | "NEA" = closest point
   | "APP" = apparent intersection
   | "EXT" = Extension
   | "PAR" = Parallel
   | "INT\_EXT" = intersection on extension
   | "PR" = progressive distance (may be followed by a number to set a
     progressive distance different from default)

3. | Using the setvar command to set the OSMODE variable with a
     combination a bit using the following schema:
   | 0 = None
   | 1 = endpoint
   | 2 = midpoint
   | 4 = center (centroid)
   | 8 = point object
   | 16 = quadrant point
   | 32 = intersection
   | 64 = insertion point
   | 128 = perpendicular point
   | 256 = tangent
   | 512 = closest point
   | 1024 = clear all object snaps
   | 2048 = apparent intersection
   | 4096 = extension
   | 8192 = parallel
   | 16384 = osnap disabled
   | 65536 = progressive distance
   | 131072 = intersection on extension
   | 2097152 = endpoints of the entire polyline

4. Run DSETTING command

How to specify a point
----------------------

The coordinates of a point can be expressed using the following syntax:

1) x,y

2) @length<angle (from the previous point you move to a distance using
   an angle)

3) @ x,y (from the previous point you move to a distance in the X axis
   and to another distance in the Y axis)

4) @ (previous point)

5) length (from the previous point you move to a distance using the
   current mouse position)

6) Coordinate specified in a coordinate reference system different from
   the current one

Coordinate specified in a coordinate reference system different from the current one
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the coordinate reference system is projected:

enter x,y (SRID). For example 1491621.64817, 4915622.63154 (EPSG:3003)
is a point with coordinate X=1491621.64817 and Y=4915622.63154 in the
projected coordinate reference system EPSG:3003

If the coordinate reference system is geographic:

enter latitude, longitude (SRID). For example 44º 24' 48N/ 08º 50' 15E
(EPSG:4326) is a point with latitude 44 degrees 24 minutes 48 seconds
and longitude 6 degrees 50 minutes 15 seconds in the geographic
coordinate reference system EPSG:4326.

Latitude and Longitude values can be set using the following notations:

-  Decimal Degrees (DDD) - In this notation, decimal precision is set in
   the 'degree' coordinate. For example, 49.11675953666N

-  Degrees, Minutes, and Seconds (DMS) - In this notation, decimal
   precision is set in the 'seconds' coordinate. For example, 49
   7'20.06"N

-  Degrees, Minutes with Decimal Seconds (DMM) - In this notation,
   decimal precision is set in the 'minutes' coordinate. For example, 49
   7.0055722"N. (Here, 20.06 seconds above is divided by 3600 to get the
   decimal minute value for 20.06 seconds.)

Latitude and Longitude syntax is specified as follows:

-  | Numeric Values - Simply separate each coordinate notation with a
     white space and the entry will be recognized correctly. For
     example, you can indicate a DMS notation as: 37 24 23.3. You could
     indicate a DMM notation as 49 7.0055722.
   | You can also use the character (°) for degrees, the single quote
     mark (') for minutes and the double quote mark (") for seconds, as
     follows: 49°7'20.06"

-  | Direction Notation (North/South, East/West)
   | Use 'N', 'S', 'E', or 'W' to indicate direction. The letter can be
     entered either upper or lower case and it can be placed before or
     after the coordinate value. For example: N 37 24 23.3 is the same
     as 37 24 23.3 N
   | You can also use the minus sign (-) to indicate a westerly or
     southerly position. When you use this kind of notation, do not
     specify a letter symbol. Additionally, you do not need to use a
     plus sign (+) to indicate northerly/easterly directions. So, for
     example this is a valid entry: 37 25 19.07, -122 05 08.40

-  | Entering Latitude, Longitude Pairs
   | When entering latitudinal or longitudinal pairs, the first
     coordinate is interpreted as latitude unless you use a direction
     letter to clarify (E or W). For example, you can enter longitude
     first as: 122 05 08.40 W 37 25 19.07 N
   | However, you cannot use the minus sign to enter longitude
     first:-122 05 08.40 37 25 19.07
   | You can separate pair entries with a space, a comma, or a slash:
     37.7 N 122.2 W or 37.7 N,122.2 W or 37.7 N/122.2 W

Selecting objects
-----------------

When a command ask to select the objects (usually with the message
"select objects") you can type the letter "H" for Help to show all
options.

The <WCircle> and <CCerchio> options select respectively objects that
are Inside/intersecting a circle and objects only inside a circle.

The <WObjectsi> e <Cobjectsi> options select respectively objects that
are Inside/intersecting existing objects and objects only inside
existing objects.

The <FBuffer> e <IBuffer> options select respectively objects that are
Inside/intersecting a buffer and objects only inside a buffer.

Dimensioning
------------

Dimension style is a set of properties that determine the appearance of
dimensions. These properties are stored in files with the extension .dim
and are loaded on QAD startup or on loading a project. Dimension files
must be saved in the current project folder or in the QAD installation
folder (i.e. in windows 8 "C:\\users\\*current
user\\*.qgis2\\python\\plugins\\qad ").

QAD stores the elements constituting a dimension in 3 different layers::

-  Text layer for storing dimension text

-  Symbol layers to store punctual dimension objects (dimension points,
   arrow symbols ...)

-  Linear layers to store linear dimension objects (dimension line,
   extension lines ...)

Text layer model for dimensioning:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The main element of a dimension is the text. Its textual layer must have
the following fields:

-  a character field to store the dimension text

-  a character field to store the font Of the dimension text

-  a real number field to store the dimension text height (in map unit)

-  a real number field to store text rotation (degree counterclockwise
   where zero = horizontal to the right)

Optional fields:

-  | an integer number field to store the unique ID of the dimension
   | This field is required if you want to group the objects of the same
     dimension and implement the erasing and editing features of an
     existing dimension. Because it must be a unique value field,
     actually, it is supported for PostGIS table only where you have to
     create a serial type not null field which is the primary key of the
     table. (i.e. “id”). In addition to this you have to create another
     bigint type field which will be managed by QAD to store the
     dimension ID (i.e. “dim\_id”). Shape files don’t let QAD group
     objects of the same dimension so, after drawing a dimension, every
     objects will be independent each one from the other.

-  a character field to store the color of the dimension text

-  a character field to store the dimension style name (required if you
   want to use the editing features of an existing dimension)

-  | a character field (2 characters) to store the dimension style
     (linear, aligned ...) according to the following scheme:
   | "AL" = linear aligned dimension
   | "AN" = angular dimension
   | "BL" = baseline and continued dimension
   | "DI" = diameters of arcs and circles dimension
   | "LD" = creates a line that connects annotation to a feature
   | "LI" = dimensions using only the horizontal or vertical components
     of the locations
   | "RA" = radial dimension
   | "AR" = measure the length along a circle or arc
   | (required if you want to use the editing features of an existing
     dimension)

An SQL example to create a PostGIS table and indexes for dimension text:

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

The textual layer must be defined with labels as follows:

-  The font must be read from a field that stores the font character of
   the dimension text (tab <Labels>-<Text>)

-  The size must be read by a real number field that stores the
   dimension text height (in map units, tab <Labels>-<Text>)

-  The rotation must be read by a real number field that stores the
   dimension text rotation (degree counterclockwise where zero =
   horizontal to the right), option <Preserve data rotation values>
   activated, (tab <Labels>-<Placement>)

-  Placement <Around point> with distance = 0 (tab <Labels>-<Placement>)

-  <Show all label for this layer> option enabled (tab
   <Labels>-<Rendering>)

-  <Show upside-down labels> option with value <always> (tab
   <Labels>-<Rendering>)

-  <Discourage labels from covering features> option disabled (tab
   <Labels>-<Rendering>)

Optional settings:

-  The color can be read from a character field that stores the
   dimension text color (tab <Labels>-<Text>)

Symbol layer model for dimensioning:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The dimension symbols (arrows, etc.) should be stored in a layer with
the following fields:

-  a real number field to store dimension text rotation (degree
   counterclockwise where zero = horizontal to the right, use expression
   “360-rotation\_field”)

Optional fields:

-  a character field to store the symbol name

-  a real number field to store the symbol scale

-  | a character field (2 characters) field to store the punctual object
     type according to the following scheme:
   | "B1" = first arrow block ("Block 1")
   | "B2" = second arrow block ("Block 2")
   | "LB" = leader arrow block ("Leader Block")
   | "AB" = arc symbol ("Arc Block")
   | "D1" = dimension point 1
   | "D2" = dimension point 2
   | (required if you want to use the editing features of an existing
     dimension)

-  an integer number field to store the unique ID of the dimension
   (necessary if you want to group the objects of a dimension, and
   implement the erasing and editing features of an existing dimension)

An SQL example to create a PostGIS table and indexes for dimension
symbol:

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

The symbol layer must be defined with a style set as follows:

-  <Style>-<Single Symbol> option enabled

-  <Style>-<map units> option enabled

-  Set the size of the symbol so that the width of the arrow is 1 map
   unit (tab <Style>)

-  The rotation must be read by a real number field that stores the
   symbol rotation through the formula "360-<field that stores the
   rotation>" (degree counterclockwise where zero = horizontal to the
   right, <Style>-<Advanced> option "rotation field name"-<Espressione>)

-  The scale can be read by a real number field that stores the scale of
   the symbol (<Style>-<Advanced>-<Size scale field>-“ field that stores
   the scale” and <Style>-< Advanced >-<Size scale field >-<Scale
   diameter>)

The arrow symbol when inserted with rotation = 0 must be horizontal with
the arrow pointing to the right and its insertion point should be on the
tip of the arrow.

Linear layer model for dimensioning:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Linear elements of a dimension (dimension line, extension lines ...)
must be stored in a linear layer with the following fields:

-  No mandatory fields

Optional fields:

-  a character field to store the color of the dimension lines

-  a character field to store the linetype of the dimension lines

-  | a character field (2 characters) field to store the linear object
     type according to the following scheme:
   | "D1" = Dimension line 1
   | "D2" = Dimension line 2
   | "E1" = Extension line 1"
   | "E2" = Extension line 2
   | "L" = leader line when the text is outside the dimension
   | (required if you want to use the editing features of an existing
     dimension)

-  an integer number field to store the unique ID of the dimension
   (necessary if you want to group the objects of a dimension, and
   implement the erasing and editing features of an existing dimension)

An SQL example to create a PostGIS table and indexes for dimension
lines:

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

The linear layer must be defined with the style set as follows:

Optional settings:

-  The color can be read from a character field that stores the
   dimension line color

-  The linetype can be read from a character field that stores the
   linetype of dimension lines

Dimension commands (DIMLINEAR, DIMALIGNED) refer to the current
dimension style. To set the current dimension style run DIMSTYLE
command.

Commands customization
----------------------

It is possible customize the commands (*shortcuts*) by a file named
qad\_<language>\_<region>.pgp (utf-8).

<language> is the current QGIS language (mandatory) and <region> is the
current linguistic region (optional). For example qad\_pt\_br.pgp is the
file in portuguese language of region Brazil, qad\_en.pgp is the English
version of the pgp file. The file is searched by QAD following the paths
in the system variable SUPPORTPATH.

Commands
--------

The commands are activated by menu VECTOR->QAD or toolbar or command
line. The commands and their options can be specified in English by
prefixing the character "\_" to the name (e.g. \_ LINE) regardless of
the language used in QGIS.

QAD command can be interrupted at any moment by the activation of
another tool. To resume the paused command and make active the QAD
environment use the QAD item in the QAD menu or press the button
|image1| in the toolbar.

As you type the name of a command QAD will display a list of commands
that begin with what has been written Typing "\*" the list of all QAD
commands will appear.

To choose an option, type the capital letters for this option or click
on the option that you want.

ARC
~~~

Draw an arc.

ARRAY
~~~~~

Creates copies of objects arranged in a pattern.

ARRAYPATH
~~~~~~~~~

Evenly distributes object copies along a path or a portion of a path.

ARRAYPOLAR
~~~~~~~~~~

Evenly distributes object copies in a circular pattern around a center
point.

ARRAYRECT
~~~~~~~~~

Distributes object copies into any combination of rows and columns.

BREAK
~~~~~

Breaks the selected object.

CIRCLE
~~~~~~

Draws a circle.

COPY
~~~~

Copies one or more objects.

DIMALIGNED
~~~~~~~~~~

Draws an aligned dimension.

DIMARC
~~~~~~

Draws a length arc dimension.

DIMLINEAR
~~~~~~~~~

Draws a linear dimension.

DIMSTYLE
~~~~~~~~

Creates, modifies, compare dimensioning styles. It sets the current
dimensioning style.

DSETTINGS
~~~~~~~~~

Set some properties to draw.

ERASE
~~~~~

Erases one or more objects.

EXTEND
~~~~~~

Extends one or more objects.

FILLET
~~~~~~

Rounds and fillets the edges of existing object.

HELP
~~~~

Displays the QAD manual.

ID
~~

It shows the coordinate of the specified position.

INSERT
~~~~~~

Inserts a symbol. If the symbol scale is derived from a field then the
command will ask the factor scale. If the symbol rotation is derived
from a field than the command will ask the rotation (degree). Only for
symbol layer.

LENGTHEN
~~~~~~~~

Lengthen an object.

LINE
~~~~

Draws a line.

MAPMPEDIT
~~~~~~~~~

It modifies the selected polygon geometry.

-  The <Add> option adds an existing geometry to the selected polygon
   (e.g. a ring).

-  The <Delete> option deletes a geometry to the selected polygon (e.g.
   a ring).

-  The <Union> option modifies the geometry of the selected polygon with
   the result of the union of the same geometry with a group of polygon.

-  The <Subtract> option modifies the geometry of the selected polygon
   with the result of the subtraction of the same geometry with a group
   of polygon.

-  The <Intersect> option modifies the geometry of the selected polygon
   with the result of the intersection of the same geometry with a group
   of polygon.

-  The <include Objs> option modifies the geometry of the selected
   polygon to include the geometries of a group of objects.

-  The <Undo> option undoes the last operation.

MBUFFER
~~~~~~~

Draws a buffer around the selected objects. Select the objects and
specify the buffer width.

MIRROR
~~~~~~

Creates a mirrored copy of selected objects.

MOVE
~~~~

Moves the selected objects.

MPOLYGON
~~~~~~~~

Draws a polygon using the same options of the PLINE command.

OFFSET
~~~~~~

Draws concentric circles, parallel lines and arcs.

OPTIONS
~~~~~~~

Customizes the program settings.

PEDIT
~~~~~

Modifies a polyline. The <Simplify> option asks for a tolerance value
used to simplify the geometry.

PLINE
~~~~~

Draws a polyline. The <Trace> option is used to trace an existing
object. During the digitizing, point to any point of an existing object
to trace, select the <Trace> option and select the same object in the
final trace point.

POLYGON
~~~~~~~

Draws a regular polygon. After specifing the center, the <Area> option
calculate the polygon.

RECTANGLE
~~~~~~~~~

Draws a rectangle.

REDO
~~~~

Redo the changes undone by the UNDO command.

ROTATE
~~~~~~

Rotate the selected objects.

SCALE
~~~~~

Scale the selected objects.

SETCURRLAYERBYGRAPH
~~~~~~~~~~~~~~~~~~~

Sets the current layer selecting an object.

SETCURRUPDATEABLELAYERBYGRAPH
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sets edit mode to the layers of the selected objects. If you specify
only one layer it becomes the current one.

SETVAR
~~~~~~

Lists or modifies the values of QAD variables. Once specified the QAD
variable name, a short decription and the type of the variable value
(real, integer, character, boolean) is shown.

STRETCH
~~~~~~~

Stetches the selected objects.

TEXT
~~~~

Inser a text. If the height text is derived from a field then the
command will ask the text height. If the text rotation is derived from a
field then the command will ask the rotation (degree). At the end the
command will ask the value of the text. Only for textual layer.

TRIM
~~~~

Trims the selected objects.

UNDO
~~~~

Undo changes made by QAD.

QAD commands that create, modify or erase objects affect all visible and
editable layers, and not only the current layer as QGIS does. That's why
QAD uses its undo/redo system that operates on all layers involved into
QAD commands

*If the user will run the Undo/Redo command of QGIS, QAD will lose
alignment with the history of the changes made by its commands and then
the undo/redo stack will be cleared.*

Grip mode
---------

You can drag grips to perform any stretch, move, rotate, scale, or
mirror operations.

The editing operation you choose to perform is called a grip mode.

Grips are small, solid-filled squares that are displayed at strategic
points on objects that you have selected with a pointing device. You can
drag these grips to stretch, move, rotate, scale, or mirror objects
quickly.

When grips are turned on, you can select the objects you want to
manipulate before entering a command, and then you can manipulate the
objects with the pointing device.

Note: *Grips are not displayed on objects that are on locked layers.*

To copy the selected object, press and hold the Ctrl key while you’re
manipulating it.

To Edit Objects Using Grips:

1. Select the object to edit.

2. | Select and move grips to stretch the object.
   | Note: In the case of some object grips, for example, symbol or text
     reference grips, stretch will move the object rather than stretch
     it.

3. Press Enter, Spacebar or right-click to cycle to the move, rotate,
   scale, or mirror grip modes.

4. Hover over a grip to view and access the multifunctional grip menu
   (if available).

System variables
----------------

System variables are settings that control how certain commands work.
They can be integer, real, char, bool or RGB color type (i.e.
“#FF0000”). If a current project exist, they are saved and loaded into
<current project name>\_QAD.INI file of the current QGIS project folder
else in the QAD.INI file located in the installation folder.

APBOX
~~~~~

Come i CAD più popolari.

APERTURE
~~~~~~~~

Come i CAD più popolari.

ARCMINSEGMENTQTY
~~~~~~~~~~~~~~~~

Minimum number of segments to approximate an arc. Valid values from 4 to
999, integer type, default value 12.

AUTOSNAP
~~~~~~~~

The same as the most popular CAD.

AUTOSNAPCOLOR
~~~~~~~~~~~~~

Color of the snap markers.

AUTOSNAPSIZE
~~~~~~~~~~~~

Dimension of the snap markers in pixel.

AUTOTRACKINGVECTORCOLOR
~~~~~~~~~~~~~~~~~~~~~~~

Color of the autotrack vector.

CIRCLEMINSEGMENTQTY
~~~~~~~~~~~~~~~~~~~

Minimum number of segments to approximate a circle. Valid values from 6
to 999, integer type, default value 12.

CMDHISTORYBACKCOLOR
~~~~~~~~~~~~~~~~~~~

Command history background color.

CMDHISTORYFORECOLOR
~~~~~~~~~~~~~~~~~~~

Command history text color.

CMDINPUTHISTORYMAX
~~~~~~~~~~~~~~~~~~

The same as the most popular CAD.

CMDLINEBACKCOLOR
~~~~~~~~~~~~~~~~

Active prompt background color.

CMDLINEFORECOLOR
~~~~~~~~~~~~~~~~

Active prompt color.

CMDLINEOPTBACKCOLOR
~~~~~~~~~~~~~~~~~~~

Command option keyword background color.

CMDLINEOPTCOLOR
~~~~~~~~~~~~~~~

Command option keyword color.

CMDLINEOPTHIGHLIGHTEDCOLOR
~~~~~~~~~~~~~~~~~~~~~~~~~~

Command option highlighted color.

COPYMODE
~~~~~~~~

The same as the most popular CAD.

CROSSINGAREACOLOR
~~~~~~~~~~~~~~~~~

The same as the most popular CAD.

CURSORCOLOR
~~~~~~~~~~~

Cross pointer color. Valid values are valid RGB colors, color type,
default value red =“#FF0000”.

CURSORSIZE
~~~~~~~~~~

The same as the most popular CAD.

DELOBJ
~~~~~~

| It controls whether the original geometry is retained or removed.
| 0 = All defining geometry is retained.
| 1 = Deletes all defining geometry.
| -1 = Displays prompts to delete all defining geometry.

DIMSTYLE
~~~~~~~~

The same as the most popular CAD.

EDGEMODE
~~~~~~~~

The same as the most popular CAD.

FILLETRAD
~~~~~~~~~

The same as the most popular CAD.

GRIPCOLOR
~~~~~~~~~

The same as the most popular CAD.

GRIPCONTOUR
~~~~~~~~~~~

The same as the most popular CAD.

GRIPHOT
~~~~~~~

The same as the most popular CAD.

GRIPOVER
~~~~~~~~

The same as the most popular CAD.

GRIPMULTIFUNCTIONAL
~~~~~~~~~~~~~~~~~~~

| Specifies the access methods to multi-functional grips.
| 0 = Access to multi-functional grips is disabled.
| 2 = Access multi-functional grips with the dynamic menu and the Hot
  Grip shortcut menu.

GRIPOBJLIMIT
~~~~~~~~~~~~

Come i CAD più popolari.

GRIPS
~~~~~

The same as the most popular CAD.

GRIPSIZE
~~~~~~~~

The same as the most popular CAD.

INPUTSEARCHDELAY
~~~~~~~~~~~~~~~~

The same as the most popular CAD.

INPUTSEARCHOPTIONS
~~~~~~~~~~~~~~~~~~

The same as AUTOCOMPLETEMODE system variable of the most popular CAD.

MAXARRAY
~~~~~~~~

The same as the most popular CAD.

OFFSETDIST
~~~~~~~~~~

The same as the most popular CAD.

OFFSETGAPTYPE
~~~~~~~~~~~~~

The same as the most popular CAD.

ORTHOMODE
~~~~~~~~~

The same as the most popular CAD.

OSMODE
~~~~~~

The same as the most popular CAD.

OSPROGRDISTANCE
~~~~~~~~~~~~~~~

Progressive distance for <Progressive distance> snap mode. Real type,
default value 0.

PICKADD
~~~~~~~

The same as the most popular CAD.

PICKBOX
~~~~~~~

The same as the most popular CAD.

PICKBOXCOLOR
~~~~~~~~~~~~

Sets the object selection target color.

PICKFIRST 
~~~~~~~~~~

The same as the most popular CAD.

POLARANG
~~~~~~~~

The same as the most popular CAD.

POLARMODE
~~~~~~~~~

The same as the most popular CAD. The value 4 is not supported (use
additional polar tracking angles).

SELECTIONAREA
~~~~~~~~~~~~~

The same as the most popular CAD.

SELECTIONAREAOPACITY
~~~~~~~~~~~~~~~~~~~~

The same as the most popular CAD.

SUPPORTPATH
~~~~~~~~~~~

Searching path for support files. Character type.

SHOWTEXTWINDOW
~~~~~~~~~~~~~~

Show the text window at startup. Bool type, default value true.

TOLERANCE2APPROXCURVE
~~~~~~~~~~~~~~~~~~~~~

Maximum error approximating a curve to segments. Valid values from
0.000001, real type, default value 0.1.

WINDOWAREACOLOR
~~~~~~~~~~~~~~~

The same as the most popular CAD.

.. |image0| image:: media/image1.emf
   :width: 3.45278in
   :height: 1.86806in
.. |image1| image:: media/image2.png
   :width: 0.27361in
   :height: 0.27361in
