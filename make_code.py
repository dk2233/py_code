import sys
import os
import shutil 
import time



global SCRIPT_FOLDER
global VERSION



VERSION = "1.09.08"

DIRECTORY=""


START_COMMENT_BLOCK = "/*"
END_COMMENT_BLOCK= "*/"

AllAnalysedVariableTypes_dict = {
    "typedef":      "_t",
    "uint8_t":      "_u8",
    "uint8":        "_u8", 
    " int8_t":       '_i8',
    " int8":         '_i8',
    "uint16_t":     "_u16",
    "uint16":     "_u16",
    " int16_t":     "_i16",
    " int16":     "_i16",
    "boolean_t":    "_bo",
    "bool_t":       "_bo",
    
}

######################################################
# DEFINITIONS
#####################################################	

######################################################
# Function to search for all variable definitions
#
# - need to add to differentiate simple variable from arrays
# - need to understand function name
#
#####################################################	

class ClassToAnalyseCfile:
    """class to understand c file"""
    
    
    
    def __init__(self,file):
        self.file_p = open(file,"r")
        self.filename = file
        line = self.file_p.readline()
        self.tab=[]
        while(line):
            self.tab.append(line)
            line = self.file_p.readline()
            
            
        self.NextLineIsCommented = False
        self.InTypedefBlockDefinition = False
        self.InTypedefLineDefinition = False
        self.AnalyseThatVariable = False
        
    def ShowCfile(self
                  
        for i in self.tab:
            print(i)
            
    def Stop(self):
        input(" key ")
        
    def  CheckWhetherLineCommented(self,line):
        if (START_COMMENT_BLOCK in line) and ( not END_COMMENT_BLOCK in line):
            self.NextLineIsCommented = True
            line=line[:line.find(START_COMMENT_BLOCK)]
            #print(" i am in //* section ")
        elif  (START_COMMENT_BLOCK in line) and (  END_COMMENT_BLOCK in line):
            self.NextLineIsCommented = False
            line=line[:line.find(START_COMMENT_BLOCK)]+line[line.find(END_COMMENT_BLOCK)+len(END_COMMENT_BLOCK):]
        elif ( (END_COMMENT_BLOCK in line) and (self.NextLineIsCommented is True)):
            self.NextLineIsCommented = False
            line=line[line.find(END_COMMENT_BLOCK)+len(END_COMMENT_BLOCK):]
        elif '#' in line:
            line=line[:line.find('#')]
        return(line)    
     
        
    def DecodeCline(self,line):
        """ method to decode line """
        
        
    def CorrectAllNames(self):
        fileHandler_tmp = open(self.filename+"_ch","w")
        dict_of_Variables_to_change={}
        iter=0
        for line in self.tab:
            NextValue = False
            self.InTypedefLineDefinition = False  
            #print("comment ",line)
            #if self.NextLineIsCommented is False:    
            #    print(" before commented \n",line)
                
            line_without_comment = self.CheckWhetherLineCommented(line)
            print(line,end='')
            #print(" line ",iter)
            #if self.NextLineIsCommented is False:    
            #    print("after commented \n",line)
                
            if self.NextLineIsCommented is True:
                #print(line,end='')
                line_without_comment = self.CheckWhetherLineCommented(line)
                #print(" i Am still in commented block")
                fileHandler_tmp.write(line)
                continue
            if "}" in line and self.InTypedefBlockDefinition is True:
                self.InTypedefBlockDefinition = False  
                  
                  
            if "typedef" in line and not ';' in line:
                self.InTypedefBlockDefinition = True
                  #only one line definition
                  
            
            if "#include" in line:
                #print(line,end='')
                fileHandler_tmp.write(line)
                continue
            
            if len(line_without_comment.strip())<1:
                #print("empty line")
                fileHandler_tmp.write(line)
                continue
            
            #if normal coding line
            if (';' in line_without_comment)  and not "(" in line_without_comment and not ")" in line_without_comment and not '[' in line_without_comment and not ']' in line:
                tab1 = line_without_comment.split()
                
                print(" SPLITED : ",tab1,end='')
                
                for var_is_already in dict_of_Variables_to_change.keys():
                    if var_is_already in tab1:
                        print(" var is already in dict ",var_is_already)
                        NextValue = True
                        line = line.replace(var_is_already, dict_of_Variables_to_change[var_is_already] )
                        break
#                        
                if NextValue is True:
                    fileHandler_tmp.write(line)
                    continue 
                
                for var_type in AllAnalysedVariableTypes_dict.keys():
                    
                    if var_type in line: 
                        #   if variable was defined  
                        print(var_type," line = ",line_without_comment)
                        if "=" in line:
                            for i in range(0,len(tab1)):
                                if tab1[i] == "=":
                                    variable = tab1[i-1]
                                    break
                        else:
                            for i in range(0,len(tab1)):
                                if ';' in tab1[i]:
                                    variable = tab1[i]
                                    variable = (variable.split(';'))[0]
                                    break
                                    
                        print(tab1, " var = ",variable)
                        prefix = AllAnalysedVariableTypes_dict[var_type]
                        if '*' in line:
                            print(prefix,end='')
                            #check if this is pointer variable
                            prefix = prefix.replace('_','_p')
                            print(" new :",prefix)
                            #input(" pointer ")
                        print(" prefix for variable ",prefix)
                        #i am checking if this prefix is not already in variable
                        if not (prefix in variable[(len(variable) - len(prefix)): len(variable)]) :
                            new_var = variable+prefix
                            print(new_var)
                            dict_of_Variables_to_change[variable]=new_var
                            print(" I am adding new variables to dictionary of ")
                            line = line.replace(variable,new_var)
                            print(" after change ",line,end='')
                            break
#                        tab1[i] = new_var
#                        line=""
#                        for i in tab1:
#                            line = line+i
#                        line=line+"\n"  
                        else:
                            print(" prefix already in variable ")
                        #input("key")
#                print(iter)
            iter+=1            
            #input("key")
            fileHandler_tmp.write(line)  
            #print("\n" , line, "\n")
            
        
        #file_handler.close()    
        fileHandler_tmp.close()
        print("\n\n dict:")
        for key in dict_of_Variables_to_change.keys():
            print(key," = ",dict_of_Variables_to_change[key])
    
    def AnalyzeCfileObjects(self):
        pass
    
def MarkersHASH():
    
    print("#"*100)
    
    
    
def AnalyseFileZFCoding(file_handler, temp):
    line=file_handler.readline()
    
    dict_of_Variables_to_change={}
    tab1 = []
    while line:
        print(line)
        #line=line.strip();
        #if '//' in line  or '/*' in line:
            #remove all sign after that marker
            
            
        if (';' in line) and ("#" not in line) :
            tab1 = line.split()
            #print(line)
                  #AllAnalysedVariableTypes_dict.keys())
            for key in AllAnalysedVariableTypes_dict.keys():
                # print(dict_of_Variables_to_change)
                for var_is_already in dict_of_Variables_to_change:
                    #print(var_is_already)
                    if var_is_already in line:
                        print(" line ",line)
                        #if not ending variable name type
                        if not (dict_of_Variables_to_change[var_is_already] in line[(len(line) - len(dict_of_Variables_to_change[var_is_already])): len(line)]):
                            print(" changing name : ",line.replace(var_is_already, var_is_already+dict_of_Variables_to_change[var_is_already] ) )
                            
                        break
                
                if key in line: 
                    #   if variable was defined              
                    if "=" in line:
                        for i in range(0,len(tab1)):
                            if tab1[i] == "=":
                                variable = tab1[i-1]
                                break
                    else:
                        for i in tab1:
                            if ';' in i:
                                variable = i
                                variable = (variable.split(';'))[0]
                        
                    print(tab1, " var = ",variable)
                    strr = variable+AllAnalysedVariableTypes_dict[key] 
                    print(strr)
                    dict_of_Variables_to_change[variable]=strr
                
        temp.write(line)  
        #print("\n" , line, "\n")
        line=file_handler.readline()
        
    file_handler.close()    
    temp.close()
    print("\n\n\ dict:")
    for key in dict_of_Variables_to_change.keys():
        print(key," = ",dict_of_Variables_to_change[key])
    
    #return(tab_t)		
def   HelpInfo():
    tab = " You must give direcory: \n"
    tab+= " dir=<Folder name>"
    
    print(tab)
    
    
    
    
def  DecodeArguments():
    global DIRECTORY
    global tabOfAnalyzedFiles 
    
    SCRIPT_FOLDER = sys.argv[0]
    i=sys.argv[0].find(os.path.basename(__file__))
    
    SCRIPT_FOLDER = SCRIPT_FOLDER[0:i]
    
    print("\n")
    MarkersHASH()
    print("The script is in ",SCRIPT_FOLDER)
    print("\n Script version  ",VERSION," \n")
    print(" python version ",sys.version_info)
    MarkersHASH()
    
    
    tabOfAnalyzedFiles = []
    for arguments in sys.argv:
        arguments = arguments.strip()
        
        if "dir=" in arguments:
            tab1 = arguments.split("=")
            DIRECTORY = tab1[1]
        elif "file=" in arguments:
            tab1 = arguments.split("=")
           
            tabOfAnalyzedFiles.append(tab1[1])
    
    
    if (len(DIRECTORY)<1) and (len(tabOfAnalyzedFiles)<1):
        HelpInfo()
        sys.exit()
    
    
# def ListAllFolder():
def ClosingApp(startTime):
    print(" All work took ",(time.time() - startTime)/60., " min ")
    sys.exit()
   
def main():
    startTime = time.time()		
    
    
    #have to give  folder to look into
    # DIRECTORY = sys.argv[1]
    DecodeArguments()
    if (DIRECTORY is not "" ):
        tab_files = os.listdir(Directory+"\\out")
        # print(tab_files)
        for file in tab_files:	
            if (".c" in file ) or (".h" in file):
                try:
                    fileHandler = open(file,"r")
                    print(" opened file : ",file)
                except:
                    print(" cannot open file ",file)
                    ClosingApp()
                
                AnalyseFileZFCoding(fileHandler)
    elif len(tabOfAnalyzedFiles)>0:
    
        for file in tabOfAnalyzedFiles:
            kk = ClassToAnalyseCfile(file)
            #kk.ShowCfile()
            #kk.Stop()
            kk.CorrectAllNames()
            
            try:
                #fileHandler = open(file,"r")
                #fileHandler_tmp = open(file+"_ch","w")
                
                print(" opened file : ",file)
                print(" to write I opened file ", file+"_ch")
            except:
                print(" cannot open file ",file)
                ClosingApp(startTime)
            #AnalyseFileZFCoding(fileHandler,fileHandler_tmp)
    
    
if __name__ == '__main__':
    main()