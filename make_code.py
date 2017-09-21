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
MODULE_PREFIX   =   "EDR"


#   if #include or #define there is no need for ; or {}

# all comments are remove during c-file analysis


AllAnalysedVariableTypes_dict = {
    "typedef":      "_t",
    "enum":         "_e",
    "uint8_t":      "_u8",
    "uint8":        "_u8", 
    " int8_t":       '_i8',
    " int8":         '_i8',
    "uint16_t":     "_u16",
    "uint16":     "_u16",
    " int16_t":     "_i16",
    " int16":     "_i16",
    "uint32_t":     "_u32",
    "uint32":     "_u32",
    " int32_t":     "_i32",
    " int32":     "_i32",
    "boolean_t":    "_bo",
    "bool_t":       "_bo",
}
AllEquality_tab = {
    "=",
    "!",
    " "
}

WordWithoutEndingCharacters = (
"#include",
"#define"
)

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
    
        if ".c" in file or ".h" in file:
            filename = file.split(".")[0]
            
        self.tab_c=[]
        self.tab_h=[]
        self.filename = filename
        self.nr_line = 0
        try:    
            self.file_c_p = open(filename+".c","r")
            print("!"*100)
            print(" I opened ",filename+".c") 
            print("!"*100)
            line = self.file_c_p.readline()
           
            while(line):
                self.tab_c.append(line)
                line = self.file_c_p.readline()
                
        except:
            print("X"*100)
            print(" cannot open file ",filename+".c")
            print("X"*100)
            
        try:    
            self.file_h_p = open(filename+".h","r")
            print("!"*100)
            print(" I opened ",filename+".h") 
            print("!"*100)
            
            line = self.file_h_p.readline()
            
            while(line):
                self.tab_h.append(line)
                line = self.file_h_p.readline()
        except:
            print("X"*100)
            print(" cannot open file ",filename+".h")
            print("X"*100)
        
        self.NextLineIsCommented = False
        self.InTypedefBlockDefinition = False
        #self.InTypedefLineDefinition = False
        self.AnalyseThatVariable = False
        
        
        
    def ShowCfile(self,tab_from_c_file):
        for element in tab_from_c_file:
            print(element,end="")
        

        
    def  CheckWhetherLineCommented(self,tab):
        """ this find all comments and return two strings - all line with strings together 
        and line without comments"""
        
        line=tab[self.nr_line]
        line_wc=line
        if (START_COMMENT_BLOCK in line):
        #and ( not END_COMMENT_BLOCK in line):
            #self.NextLineIsCommented = True
            
            while(not END_COMMENT_BLOCK in tab[self.nr_line]):
                self.nr_line +=1
                line +=tab[self.nr_line]
                
            #line +=tab[self.nr_line]    
            
            line_wc=line[:line.find(START_COMMENT_BLOCK)]+line[line.find(END_COMMENT_BLOCK):]
            
        # elif  (START_COMMENT_BLOCK in line) and (  END_COMMENT_BLOCK in line):
            # self.NextLineIsCommented = False
            # line_wc=line[:line.find(START_COMMENT_BLOCK)]+line[line.find(END_COMMENT_BLOCK)+len(END_COMMENT_BLOCK):]
        # elif ( (END_COMMENT_BLOCK in line) and (self.NextLineIsCommented is True)):
            # self.NextLineIsCommented = False
            # line_wc=line[line.find(END_COMMENT_BLOCK)+len(END_COMMENT_BLOCK):]
        elif '#' in line:
            line_wc=line[:line.find('#')]
            
        return line,line_wc
     
     
    def DecodeCline(self,line):
        """ method to decode line """
    
    def MergeLineInDifferentLines(self,tab,nr_line):
        """ method to connect all lines that are one statement, but divided during development for readibility """
        line=tab[nr_line]
        
        if (START_COMMENT_BLOCK in line) and ( not END_COMMENT_BLOCK in line):
            finishMark = END_COMMENT_BLOCK
                        
        # elif not ";" in line and not "{":
                        
        #if not ";"  in line and not "{"
        
    
    def CorrectCLine(self,line):
        """ it is for correct line, change forms of line """
        
        if "=" in line and not "==" in line and not "!=" in line :
            nr = line.find("=")
            if not line[nr+1] in AllEquality_tab:
                line=line.replace("=","= ")
            if not line[nr-1] in AllEquality_tab:
                line=line.replace("="," =")
                
        if ";" in line:
            nr = line.find(";")
            i = nr-1
            while line[i].isspace():
                line = line[:i]+line[i+1:]
                nr = line.find(";")
                i=nr-1
                
        if '(' and ')' in line and not "#define" in line:
            # iaminafunction = True
            for mark in ("(",")","[","]"):
                nr = line.find(mark)
                i = nr-1
                if not line[nr+1].isspace():
                    line=line.replace(mark,mark+" ")
                if not line[nr-1].isspace():
                    line=line.replace(mark," "+mark)
                 
            print(line)
            #input(" key ")
            
        return(line)
    
    
    def DivideLine(self,line):
        line_tab = line.split() 
        return(line_tab)       
    
    def FindVariableinDefinition(self,line):
        """ here I have to give line without any comments """
        # print(line)
        line_tab = self.DivideLine(line)
        # print(line_tab)
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
        
        #wrong prefix:
        
        for pref in AllAnalysedVariableTypes_dict.values():
            if pref is prefix:
                #if same prefix it is ok to be in variable
                continue
            # print(pref)
            if (pref in variable[(len(variable) - len(pref)): len(variable)]) :
                variable = variable.replace(pref,"")
                # input("key")
        
        
        #not real prefix - remove obsolete _xx (two letter max)
        # print("#"*100)
        # print(variable)
        # print("#"*100)
        
        if not (prefix in variable[(len(variable) - len(prefix)): len(variable)]) :
            i=variable[len(variable)-2:].find("_")
            if i is not -1:
                variable = variable[:i]
                
            new_var = variable+prefix
            print(new_var)
            self.dict_of_Variables_to_change[variable]=new_var
            print(" I am adding new variables to dictionary of ")
            line = line.replace(variable,new_var)
            print(" after change ",line)
            #break
#                        line_tab[i] = new_var
#                        line=""
#                        for i in line_tab:
#                            line = line+i
#                        line=line+"\n"  
        else:
            print(" prefix ", prefix," already in variable ")
        # print("#"*100)
        # print(variable)
        # print("#"*100)
        return(line)
    
    
    def IsFunctionInLine(self,line):
        """ to find all functions """
        
    def  RemoveAllCommentForAnalysis(self,tab):
        """ it is needed for analysing pure code without commented blocks 
        TBD
        TBD
        """
        # tab_without_comment = []
        # iter=0
        
        # while iter < len(tab):
            # line=tab[iter]
            # line_without_comment = self.CheckWhetherLineCommented(line)
            # tab_without_comment.append(line_without_comment)
            # iter +=1
        # return(tab_without_comment)
    
    def FindAllExternInH(self):
        #fileHandler_tmp = open(self.filename+".c"+"_ch","w")
        self.Dict_of_Extern_Variables_to_change={}
        iter=0
        while iter < len(self.tab_h):
            line=self.tab[iter]
            line = self.CorrectCLine(line)
            
            iter +=1
        
    def CorrectAllNames(self):
        fileHandler_tmp = open(self.filename+".c"+"_ch","w")
        self.dict_of_Variables_to_change={}
        self.nr_line=0
        while self.nr_line < len(self.tab_c):
            line=self.tab_c[self.nr_line]      
            line,line_without_comment = self.CheckWhetherLineCommented(self.tab_c)
            
            if len(line_without_comment.strip())<1:
                #print("empty line")
                fileHandler_tmp.write(line)
                self.nr_line+=1 
                continue
            
            #MergeLineInDifferentLines(tab_c,iter)
            
            # if any(word in line for word in WordWithoutEndingCharacters):
                
                # fileHandler_tmp.write(line)
            
            #line = self.CorrectCLine(line)
            # print(line)
            
            # print(line)
            # input( " key ")
            # print(line_without_comment)
            # input( " key ")
            line_tab = self.DivideLine(line)
            
            
                  
            if "typedef" in line and not ';' in line:
                #self.InTypedefBlockDefinition = True
                fileHandler_tmp.write(line)
                
                while '}' not in line:
                    self.nr_line +=1
                    line=self.tab_c[self.nr_line] 
                    if '}' not in line:
                        fileHandler_tmp.write(line)
                
                print(line_without_comment) 
                line_tmp = line_without_comment.strip()+" "
                while not ';' in line:
                    self.nr_line +=1
                    line=self.tab_c[self.nr_line]  
                    
                    #line_without_comment = self.CheckWhetherLineCommented(line)
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
                line = line+"\n"
                #print(line_without_comment)
                #line = line_without_comment  
                fileHandler_tmp.write(line)
                self.nr_line +=1
                continue
                #input(" typedef ")
                
            elif "typedef" in line and ';' in line:
                var = self.FindVariableinDefinition(line_without_comment)
                line = self.AddPrefixToVariable(var,AllAnalysedVariableTypes_dict["typedef"],line_without_comment)
                #print(line_without_comment)
                #line = line_without_comment  
                fileHandler_tmp.write(line)
                self.nr_line +=1
                continue
                #input("key")
                        
            #if normal coding line
            if (';' in line_without_comment)  and not "(" in line_without_comment and not ")" in line_without_comment and not '[' in line_without_comment and not ']' in line_without_comment:
                
                print(" SPLITED : ",line_tab,end='')
                
                for var_is_already in self.dict_of_Variables_to_change.keys():
                    if var_is_already in line_tab:
                        print(" var is already in dict ",var_is_already)
                        NextValue = True
                        line = line.replace(var_is_already, self.dict_of_Variables_to_change[var_is_already] )
                        break

                if NextValue is True:
                    fileHandler_tmp.write(line)
                    self.nr_line+=1 
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
#                print(self.nr_line)
            self.nr_line+=1            
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
        
            
            analyze = ClassToAnalyseCfile(file)
            
            
            #tab = analyze.RemoveAllCommentForAnalysis(analyze.tab_c)
            #analyze.ShowCfile(tab)
            #analyze.ShowHfile()
            
            analyze.CorrectAllNames()
            
            # try:
                                
                # print(" opened file : ",file)
                # print(" to write I opened file ", file+"_ch")
            # except:
                # print(" cannot open file ",file)
                # ClosingApp(startTime)
            #AnalyseFileZFCoding(fileHandler,fileHandler_tmp)
    
    
if __name__ == '__main__':
    main()