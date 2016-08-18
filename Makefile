
###### EDIT ##################### 
 
 
#UI files to compile
#UI_FILES = qad.ui qad_dsettings.ui qad_dimstyle.ui
#Qt resource files to compile
RESOURCES = qad.qrc qad_dsettings.qrc 
 
 
#################################
# DO NOT EDIT FOLLOWING
 
#COMPILED_UI = $(UI_FILES:%.ui=%_ui.py)
COMPILED_RESOURCES = $(RESOURCES:%.qrc=%_rc.py)
 
all : resources
#all : resources ui 
 
resources : $(COMPILED_RESOURCES) 
 
#ui : $(COMPILED_UI)
 
#%_ui.py : %.ui
#	pyuic4 $< -o $@
 
%_rc.py : %.qrc
	pyrcc4 $< -o $@
 
clean : 
	#$(RM) $(COMPILED_UI) $(COMPILED_RESOURCES) $(COMPILED_UI:.py=.pyc) $(COMPILED_RESOURCES:.py=.pyc)  
	$(RM) $(COMPILED_RESOURCES)  $(COMPILED_RESOURCES:.py=.pyc)  
