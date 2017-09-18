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
        
    def ShowCfile(self):
                  
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
    
    
    def CorrectCLine(self,line):
        """ it is for correct line, change forms of line """
        
        if "=" in line:
            nr = line.find("=")
            if not line[nr+1].isspace():
                line=line.replace("=","= ")
            if not line[nr-1].isspace():
                line=line.replace("="," =")
                
        if ";" in line:
            nr = line.find(";")
            i = nr-1
            while line[i].isspace():
                line = line[:i]+line[i+1:]
                nr = line.find(";")
                i=nr-1
                
        print(line)
        return(line)
    
    
    def DivideLine(self,line):
        print(line)
            
        line_tab = line.split() 
        
#        for elem in line_tab:
#            if "=" in elem and len(elem)>1:
#                temp = elem.split("=")
#                line_tab.remove(elem)
#                for i in temp:
#                    line_tab.append(i)
                    
        print(line_tab)         
        if '(' and ')' in line:
            iaminafunction = True
        return(line_tab)     
    
    def FindVariableinDefinition(self,line):
        """ here I have to give line without any comments """
        print(line)
        line_tab = self.DivideLine(line)
        print(line_tab)
        if "=" in line:
            for i in range(0,len(line_tab)):
            
                if line_tab[i] == "=":
                    variable = line_tab[i-1]
                    break
        else:                   
            for i in range(0,len(line_tab)):
                if ';' in line_tab[i]:
                    if len(line_tab[i])>1:
                        variable = line_tab[i]
                        variable = (variable.split(';'))[0]
                    else:
                        #in case someone gave space between variable name and ;
                        variable = line_tab[i-1]
                    break

        print(line_tab, " var = ",variable)
        return( variable)
    
    
    def  AddPrefixToVariable(self,variable,prefix,line):
        #for var_type in AllAnalysedVariableTypes_dict.keys():
        #    if var_type in line: 
                
        if not (prefix in variable[(len(variable) - len(prefix)): len(variable)]) :
            new_var = variable+prefix
            print(new_var)
            self.dict_of_Variables_to_change[variable]=new_var
            print(" I am adding new variables to dictionary of ")
            line = line.replace(variable,new_var)
            print(" after change ",line,end='')
            #break
#                        line_tab[i] = new_var
#                        line=""
#                        for i in line_tab:
#                            line = line+i
#                        line=line+"\n"  
        else:
            print(" prefix already in variable ")
        return(line)
    
    def CorrectAllNames(self):
        fileHandler_tmp = open(self.filename+"_ch","w")
        self.dict_of_Variables_to_change={}
        iter=0
        while iter < len(self.tab):
            NextValue = False
            line=self.tab[iter]      
            self.InTypedefLineDefinition = False  
            #print("comment ",line)
            #if self.NextLineIsCommented is False:    
            #    print(" before commented \n",line)
            line = self.CorrectCLine(line)
            print(line)
            line_without_comment = self.CheckWhetherLineCommented(line)
            line_tab = self.DivideLine(line)
            #line_without_comment.split()
            
            #print(line,end='')
            #print(" line ",iter)
            #if self.NextLineIsCommented is False:    
            #    print("after commented \n",line)
                
            if self.NextLineIsCommented is True:
                #print(line,end='')
                line_without_comment = self.CheckWhetherLineCommented(line)
                #print(" i Am still in commented block")
                fileHandler_tmp.write(line)
                iter+=1 
                continue
            if "}" in line and self.InTypedefBlockDefinition is True:
                self.InTypedefBlockDefinition = False  
                  
                  
            if "typedef" in line and not ';' in line:
                #self.InTypedefBlockDefinition = True
                fileHandler_tmp.write(line)
                while '}' not in line:
                    iter +=1
                    line=self.tab[iter] 
                    if '}' not in line:
                        fileHandler_tmp.write(line)
                
                line_without_comment = self.CheckWhetherLineCommented(line)
                print(line_without_comment) 
                line_tmp = line_without_comment.strip()+" "
                while not ';' in line:
                    iter +=1
                    line=self.tab[iter]  
                    
                    line_without_comment = self.CheckWhetherLineCommented(line)
                    line_tmp += line_without_comment.strip()+" "
                  #only one line definition
                
                line_tab = line_tmp.split()
                line_without_comment = line_tab[0]
                for i in line_tab[1:]:
                    if i is not ";":
                        line_without_comment += " "
                    line_without_comment +=i
                    
                variable = self.FindVariableinDefinition(line_without_comment)
                line = self.AddPrefixToVariable(variable,AllAnalysedVariableTypes_dict["typedef"],line_without_comment)
                #print(line_without_comment)
                #line = line_without_comment  
                fileHandler_tmp.write(line)
                iter +=1
                continue
                #input(" typedef ")
                
            elif "typedef" in line and ';' in line:
                var = self.FindVariableinDefinition(line_without_comment)
                line = self.AddPrefixToVariable(var,AllAnalysedVariableTypes_dict["typedef"],line_without_comment)
                #print(line_without_comment)
                #line = line_without_comment  
                fileHandler_tmp.write(line)
                iter +=1
                continue
                input("key")
            
            if "#include" in line:
                #print(line,end='')
                fileHandler_tmp.write(line)
                iter+=1 
                continue
            
            if len(line_without_comment.strip())<1:
                #print("empty line")
                fileHandler_tmp.write(line)
                iter+=1 
                continue
            
            #if normal coding line
            if (';' in line_without_comment)  and not "(" in line_without_comment and not ")" in line_without_comment and not '[' in line_without_comment and not ']' in line_without_comment:
                
                
                print(" SPLITED : ",line_tab,end='')
                
                
                
                for var_is_already in self.dict_of_Variables_to_change.keys():
                    if var_is_already in line_tab:
                        print(" var is already in dict ",var_is_already)
                        NextValue = True
                        line = line.replace(var_is_already, self.dict_of_Variables_to_change[var_is_already] )
                        break
#                        
                if NextValue is True:
                    fileHandler_tmp.write(line)
                    iter+=1 
                    continue 
                
                for var_type in AllAnalysedVariableTypes_dict.keys():
                    
                    if var_type in line: 
                        #   if variable was defined  
                        print(var_type," line = ",line_without_comment)
                        variable = self.FindVariableinDefinition(line_without_comment)
                        prefix = AllAnalysedVariableTypes_dict[var_type]
                        if '*' in line:
                            print(prefix,end='')
                            #check if this is pointer variable
                            prefix = prefix.replace('_','_p')
                            print(" new :",prefix)
                            #input(" pointer ")
                        print(" prefix for variable ",prefix)
                        #i am checking if this prefix is not already in variable
                        print(variable)
                        if not (prefix in variable[(len(variable) - len(prefix)): len(variable)]) :
                            new_var = variable+prefix
                            print(new_var)
                            self.dict_of_Variables_to_change[variable]=new_var
                            print(" I am adding new variables to dictionary of ")
                            line = line.replace(variable,new_var)
                            print(" after change ",line,end='')
                            break
#                        line_tab[i] = new_var
#                        line=""
#                        for i in line_tab:
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
        for key in self.dict_of_Variables_to_change.keys():
            print(key," = ",self.dict_of_Variables_to_change[key])
    
    def AnalyzeCfileObjects(self):
        pass
    
def MarkersHASH():
    
    print("#"*100)
    
    
    
def AnalyseFileZFCoding(file_handler, temp):
    line=file_handler.readline()
    
    dict_of_Variables_to_change={}
    line_tab = []
    while line:
        print(line)
        #line=line.strip();
        #if '//' in line  or '/*' in line:
            #remove all sign after that marker
            
        if (';' in line) and ("#" not in line) :
            line_tab = line.split()
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
                        for i in range(0,len(line_tab)):
                            if line_tab[i] == "=":
                                variable = line_tab[i-1]
                                break
                    else:
                        for i in line_tab:
                            if ';' in i:
                                variable = i
                                variable = (variable.split(';'))[0]
                        
                    print(line_tab, " var = ",variable)
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
            line_tab = arguments.split("=")
            DIRECTORY = line_tab[1]
        elif "file=" in arguments:
            line_tab = arguments.split("=")
           
            tabOfAnalyzedFiles.append(line_tab[1])
    
    
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