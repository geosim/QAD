set OSGEO4W_ROOT=C:\Program Files\QGIS 3.22.6

call "%OSGEO4W_ROOT%\bin\o4w_env.bat"

path %OSGEO4W_ROOT%\apps\qgis-ltr\bin;%OSGEO4W_ROOT%\apps\grass\grass78\lib;%OSGEO4W_ROOT%\apps\grass\grass78\bin;%PATH%

cd /d %~dp0

@ECHO ON
call pyrcc5 -o qad_rc.py qad.qrc
call pyrcc5 -o qad_dsettings_rc.py qad_dsettings.qrc
rem call pyrcc5 -o incrementalSum_rc.py incrementalSum.qrc