# -*- coding: latin1 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per il debug
 
                              -------------------
        begin                : 2013-04-17
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

DEBUG = False # True

if DEBUG == True:
   import sys
   sys.path.append("C:/software/python/eclipse-SDK-4.2.2-win32/eclipse/plugins/org.python.pydev_2.7.3.2013031601/pysrc/")
   from pydevd import *


# Import the PyQt library
from PyQt4.QtCore import *
from PyQt4.QtGui import *


def isDebug():
   return DEBUG

def displayMsg(msg):
   if isDebug():
      QMessageBox.information(None, "Qad Debug Window", msg)

def displayList(values):
   if isDebug():
      msg = ""
      for value in Values:
         msg = msg + str(value) + "\n"
      displayMsg(msg)
      
def breakPoint():
   if isDebug():
      # Premi F5 per continuare il debug...
      settrace()