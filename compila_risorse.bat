set OSGEO4W_ROOT=C:\Program Files\QGIS 3.10

call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
call "%OSGEO4W_ROOT%\bin\qt5_env.bat"
call "%OSGEO4W_ROOT%\bin\py3_env.bat"

path %OSGEO4W_ROOT%\apps\bin;%OSGEO4W_ROOT%\apps\grass\grass76\lib;%OSGEO4W_ROOT%\apps\grass\grass76\bin;%PATH%

cd /d %~dp0

@ECHO ON
call pyrcc5 -o qad_rc.py qad.qrc
call pyrcc5 -o qad_dsettings_rc.py qad_dsettings.qrc
rem call pyrcc5 -o incrementalSum_rc.py incrementalSum.qrc