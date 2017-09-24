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
    "typedef":          "_t",
    "uint8_t":          "_u8",
    "uint8":            "_u8", 
    " int8_t":          '_i8',
    " int8":            '_i8',
    "uint16_t":         "_u16",
    "uint16":           "_u16",
    " int16_t":         "_i16",
    " int16":           "_i16",
    "uint32_t":         "_u32",
    "uint32":           "_u32",
    " int32_t":         "_i32",
    " int32":           "_i32",
    "boolean_t":        "_bo",
    "bool_t":           "_bo",
}
AllEquality_tab = {
    "=",
    "!",
    " "
}

WordWithoutEndingCharacters = (
    "#include",
    "#define",
    "#pragma",
    "#ifndef",
    "#endif"
    
)

#here I have symbols which are used to know that line is finished
FinishMarkers  = (
    ";",    
    "{",
    "\\"
)

SignNotForWord = (
    ";",
    "{",
    "}",
    "]",
    "[",
    ",",
    "="
    
    
)

AllFunctionArgument = {}


AllIncludes_d={}



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
    
    def __init__(self,tab):
    
        self.tab_c = tab
        
        self.nr_line = 0
        
        self.NextLineIsCommented = False
        self.InTypedefBlockDefinition = False
        #self.InTypedefLineDefinition = False
        self.AnalyseThatVariable = False
        self.FunctionPrototype = False
        self.InFunctionDeclaration = False
        self.dict_of_Variables_to_change={}
        self.tab_after_corrections=[]
        
    def ShowCfile(self):
        for element in self.tab_c:
            print(element,end="")
        
        
        
    def CheckWhetherLineCommented(self,tab):
        """ this find all comments and return two strings - all line with strings together 
        and line without comments"""
        
        line=tab[self.nr_line]
        #print(self.nr_line,"\n",line)
        line_wc=line
        if (START_COMMENT_BLOCK in line):
        #and ( not END_COMMENT_BLOCK in line):
            #self.NextLineIsCommented = True
            
            while(not END_COMMENT_BLOCK in tab[self.nr_line]):
                self.nr_line +=1
                line +=tab[self.nr_line]
                
            line_wc=line[:line.find(START_COMMENT_BLOCK)]+line[line.find(END_COMMENT_BLOCK)+len(END_COMMENT_BLOCK):]
        elif r'//' in line:
        #and not any(element in line for element in WordWithoutEndingCharacters):
            line_wc=line[:line.find('//')]
            
        return line,line_wc
     
    
    
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
        
        if "typedef" in line:
            while line.count("{")>0 and line.count("}")>0:        
                a1 = line.find("{")
                a2 = len(line)-1
                while line[a2] is not "}":
                    a2 -=1
                line = line[:a1]+line[a2+1:]
                
        line_tab = self.DivideLine(line)

        if "=" in line:
            for i in range(0,len(line_tab)):
                if line_tab[i] == "=":
                    variable = line_tab[i-1]
                    break
        else:
            print(" tt ",line_tab)
            for i in range(0,len(line_tab)):
                if ';' in line_tab[i]:
                    if len(line_tab[i])>1:
                        variable = line_tab[i]
                        #print(variable)
                        variable = (variable.split(';'))[0]
                    else:
                        #in case someone gave space between variable name and ;
                        variable = line_tab[i-1]
                    break
        print(line_tab,end="" )
        print(" var = ",variable)
        return( variable)
    
    
    
    def  AddPrefixToVariable(self,variable,prefix,line):
        #wrong prefix:
        new_var = variable
        for pref in AllAnalysedVariableTypes_dict.values():
            if pref is prefix:
                #if same prefix it is ok to be in variable
                continue
            # print(pref)
            if (pref in variable[(len(variable) - len(pref)): len(variable)]):
                variable = variable.replace(pref,"")
                 
        #not real prefix - remove obsolete _xx (two letter max)
        if not (prefix in variable[(len(variable) - len(prefix)): len(variable)]) :
            i=variable[len(variable)-2:].find("_")
            if i is not -1:
                variable = variable[:i]
                
            new_var = variable+prefix
            self.dict_of_Variables_to_change[variable]=new_var
                
            print(" I am adding new variables to dictionary of ")
            
            line = line.replace(variable,new_var)
            print(" after change ",line)
            input(" key ")
        else:
            print(" prefix ", prefix," already in variable ")
            
        if "enum" in line and "typedef" in line:
            AllAnalysedVariableTypes_dict[variable]="_e"
    
        return new_var,line
    
    
    def FunctionPrototypeInLine(self,string):
        """ to find all functions """
        
        function_name =""
        
        string = string.replace("("," ( ")
        string = string.replace(")"," ) ")
        print(string)
        
        temp = string.split()
        i=0
        ArgumentSearch = False
        tab_arg = []
        arg = []
        print(temp)
        while i< len(temp):
            print(temp[i])
            # if ArgumentSearch is True and 
                # break
            
            if ArgumentSearch is True:
                
                print("\t\t",temp[i])
                print(arg)
                #print(" comparing ", temp[i] == 'void' ,temp[i],'void')
                if temp[i] == 'void':
                    print(" exit ")
                    break
                elif temp[i] is not ',' and temp[i] is not ')':    
                    arg.append(  temp[i])
                else:    
                    #print(arg)
                    print(" variable ",arg[len(arg)-1]," of type ",arg[len(arg)-2])
                    
                    tab_arg.append([arg[len(arg)-2], arg[len(arg)-1]])
                    if temp[i] is ")":
                        break
                    
            if temp[i] is "(" :            
                function_name = temp[i-1]
                ArgumentSearch = True
            
            i+=1
        return function_name, tab_arg

    
    
    
    
    def IfPointerAdd_p(self,variable,prefix):
        if "*" in variable[0]:
            prefix = prefix.replace("_","_p")
        return prefix    
    
    
    
    
    def FindAllExternInH(self):
        #fileHandler_tmp = open(self.filename+".c"+"_ch","w")
        self.Dict_of_Extern_Variables_to_change={}
        iter=0
        while iter < len(self.tab_h):
            line=self.tab[iter]
            line = self.CorrectCLine(line)
            iter +=1

            
            
            
            
            
    def  AnalyzeAllIncludes(self):
        self.nr_line = 0
        while self.nr_line<len(self.tab_c):
            
            line,line_without_comment = self.CheckWhetherLineCommented(self.tab_c)
            
            if len(line_without_comment.strip())<2:
                self.nr_line+=1 
                continue
                
            if  "#include" in line:
                filename = line.strip().split(r'"')[1]
                print(filename)
                #input(" key ")
                try:    
                    file_c_p = open(filename,"r")
                    print("!"*100)
                    print(" I opened ",filename) 
                    print("!"*100)
                    tab = []
                    line = file_c_p.readline()

                    while(line):
                        tab.append(line)
                        line = file_c_p.readline()

                    inc = ClassToAnalyseCfile(tab)
                    inc.FindAllTypedefVar()
                    AllIncludes_d[filename]=inc.dict_of_Variables_to_change
                    print(inc.dict_of_Variables_to_change)
                
                    self.dict_of_Variables_to_change.update(inc.dict_of_Variables_to_change)
                
#                    input(" key ")
                        
                except:
                    print("X"*100)
                    print(" cannot open file ",filename)
                    print("X"*100)
                    AllIncludes_d[filename] = " not found "
                    
                
            self.nr_line +=1
        
        
        
        
        
    def IsThisWord(self,string):
        isWord = False
        if len(string)>2:
            if not any(mark in string for mark in SignNotForWord):
                isWord = True
        return isWord  
                

        
        
        
        
    def FindAllTypedefVar(self):
        self.nr_line = 0
        while self.nr_line<len(self.tab_c):
            
            line,line_without_comment = self.CheckWhetherLineCommented(self.tab_c)
            if len(line_without_comment.strip())<2:
                self.nr_line+=1 
                continue
            
            if any(element in line_without_comment for element in WordWithoutEndingCharacters):
                if  "#define" in line:
                    while line.strip()[len(line.strip())-1] is ("\\"):
                        self.nr_line+=1 
                        line=self.tab_c[self.nr_line]
                self.nr_line+=1
                continue   
                
            line = self.MergeLineInDifferentLines(self.tab_c)
            line_tab = self.DivideLine(line)
                
            if "typedef" in line and ';' in line:
                print(" searching variable of typedef ")
                var = self.FindVariableinDefinition(line)
                print(" var ",var)
                
                new_var,line  = self.AddPrefixToVariable(var,AllAnalysedVariableTypes_dict["typedef"],line)
                print(" var ",new_var)
                self.nr_line +=1
                continue
        
            if (';' in line)  and not "(" in line and not ")" in line and not '[' in line and not ']' in line:
                
                for var_is_already in self.dict_of_Variables_to_change.keys():
                    if var_is_already in line_tab:
                        print(" var is already in dict ",var_is_already)
                        line = line.replace(var_is_already, self.dict_of_Variables_to_change[var_is_already] )
                        break

                for var_type in AllAnalysedVariableTypes_dict.keys():

                    if var_type in line:
                        #   if variable was defined  
                        print(var_type," line = ",line_without_comment)
                        variable = self.FindVariableinDefinition(line_without_comment)
                        prefix = AllAnalysedVariableTypes_dict[var_type]
                        prefix = self.IfPointerAdd_p(variable,prefix)
                        # if '*' in line:
                            # print(prefix,end='')
                            # prefix = prefix.replace('_','_p')
                            # print(" new :",prefix)

                        print(" prefix for variable ",prefix)
                        #i am checking if this prefix is not already in variable
                        #print(variable)
                        if not (prefix in variable[(len(variable) - len(prefix)): len(variable)]) :
                            new_var = variable+prefix
                            print(new_var)
                            self.dict_of_Variables_to_change[variable]=new_var
                            print(" I am adding new variables to dictionary of ")
                            line = line.replace(variable,new_var)
                            print(" after change ",line,end='')
                            break
                        else:
                            print(" prefix already in variable ")
            
            self.nr_line +=1
            
            
            
            
    def MergeLineInDifferentLines(self,tab):
        """ method to connect all lines that are one statement, but divided during development for readibility 
        
        it sees that:
        - line has ';' that is simple statement but couple of lines can be one statemen
        - line can has function prototype it has () and ;
        - line can start function definitions in that case we have more then two words + ()+ { and ending }
        """
        
        #line=tab[self.nr_line]
        
        temp = ""
        self.tab_func = []
        level_of_para = 0
        level_of_para_func = 0
        #while not any(element in line_without_comment for element in FinishMarkers ):
        self.FunctionPrototype = False
        wordCountBeforeParanthesis = 0
        #wordNumber = 0
        LineFinish = False
        self.InFunctionDeclaration = False
#        if ';' in line:
#            LineFinish = True
       
        while not LineFinish:
            line,line_without_comment = self.CheckWhetherLineCommented(self.tab_c)
            #print(line, "\t",AllFunctionArgument)
        
            if  any(func in line for func in AllFunctionArgument):
                print(" that function ",func, " is in tab functions ")
                #IamInFunction = True
                #input(" func ")
            
            temp +=line
            self.tab_func.append(line)
            line_without_comment = line_without_comment.replace("("," ( ")
            line_without_comment = line_without_comment.replace(")"," ) ")
            
            t1  = ( line_without_comment.strip() ).split()
            for word in t1:
                if self.InFunctionDeclaration == True:
                    wordCountBeforeParanthesis = 0
                    break
                    
                if "{" in word and "(" in temp and ")" in temp:
                    if wordCountBeforeParanthesis >=2 :
                        self.InFunctionDeclaration = True
                        #print(temp)
                        #LineFinish = True
#                        input(" i am in the function ")
                
                if self.IsThisWord(word) == True:
                    wordCountBeforeParanthesis +=1
#                elif "(" in word:
#                    wordCountBeforeParanthesis = 0
#            
            
            level_of_para += line_without_comment.count("{")
            level_of_para -= line_without_comment.count("}")
            
            # level_of_para_func += line_without_comment.count("(")
            # level_of_para_func -= line_without_comment.count(")")
                
            if ';' in line and (level_of_para == 0) and self.InFunctionDeclaration == False:
                LineFinish = True
                break
            
            if self.InFunctionDeclaration == True and (level_of_para == 0) and "}" in line:
                LineFinish = True
                break
                
            self.nr_line +=1
                      
                #LineFinish = True
        print("*"*100)                    
        print(" merge :",temp)
        print("^"*100)
        if "(" in temp and ";" in temp and not '{' in temp:
            self.FunctionPrototype = True
            #print(temp)
            print(temp.replace("\n"," "))
            temp = temp.replace("\n"," ")
            temp +="\n"
            #input(" func ")
            # line=tab[self.nr_line]
        # print(self.nr_line,"\n",line)
        #input(" after merging ")
        return(temp)    
    
    
    
    def CorrectAllTypedefVariable(self,tab_c):
        line_nr = 0
        tab_temp = []
        while line_nr<len(tab_c):
            line,line_without_comment = self.CheckWhetherLineCommented(self.tab_c)
            if len(line_without_comment.strip())<2:
                #fileHandler_tmp.write(line)
                self.tab_after_corrections.append(line)
                self.nr_line+=1 
                continue
            if any(element in line_without_comment for element in WordWithoutEndingCharacters):
                #fileHandler_tmp.write(line)
                self.tab_after_corrections.append(line)
                #print(" ending marker ",line_without_comment.strip()[len(line_without_comment.strip())-1])

                if  "#define" in line:
                    while line.strip()[len(line.strip())-1] is ("\\"):
                        self.nr_line+=1 
                        line=self.tab_c[self.nr_line]
                        #fileHandler_tmp.write(line)
                        self.tab_after_corrections.append(line)
                        print(line)
                    #input("WordWithoutEndingCharacters  key ")

                self.nr_line+=1
                continue        
    
        
    def  CorrectAllVariablesNames(self):
        self.nr_line=0
        self.tab_after_corrections=[]
        while self.nr_line < len(self.tab_c):
            
            line,line_without_comment = self.CheckWhetherLineCommented(self.tab_c)
            #print(self.nr_line,"\n wc ->:",line_without_comment,"\n\t",line,end='')

            if len(line_without_comment.strip())<2:
                #fileHandler_tmp.write(line)
                self.tab_after_corrections.append(line)
                self.nr_line+=1 
                continue
            
            if any(element in line_without_comment for element in WordWithoutEndingCharacters):
                #fileHandler_tmp.write(line)
                self.tab_after_corrections.append(line)
                #input(" key ")
                
                #print(" ending marker ",line_without_comment.strip()[len(line_without_comment.strip())-1])
                
                if  "#define" in line:
                    while line.strip()[len(line.strip())-1] is ("\\"):
                        self.nr_line+=1 
                        line=self.tab_c[self.nr_line]
                        #fileHandler_tmp.write(line)
                        self.tab_after_corrections.append(line)
                        print(line)
                    #input("WordWithoutEndingCharacters  key ")
                    
                #else:
                self.nr_line+=1
                    
                continue        
            
            line = self.MergeLineInDifferentLines(self.tab_c)
            
            for searchedVar   in self.dict_of_Variables_to_change.keys():
                #print(searchedVar)
                if searchedVar in line:
                    line=line.replace(searchedVar,self.dict_of_Variables_to_change[searchedVar])
                
            self.tab_after_corrections.append(line)
            self.nr_line+=1
            
            
        
    def CorrectAllNames(self):
        self.nr_line=0
        self.tab_after_corrections=[]
        while self.nr_line < len(self.tab_c):
            
            line,line_without_comment = self.CheckWhetherLineCommented(self.tab_c)
            #print(self.nr_line,"\n wc ->:",line_without_comment,"\n\t",line,end='')

            if len(line_without_comment.strip())<2:
                #fileHandler_tmp.write(line)
                self.tab_after_corrections.append(line)
                self.nr_line+=1 
                continue
            
            if any(element in line_without_comment for element in WordWithoutEndingCharacters):
                #fileHandler_tmp.write(line)
                self.tab_after_corrections.append(line)
                #input(" key ")
                
                #print(" ending marker ",line_without_comment.strip()[len(line_without_comment.strip())-1])
                
                if  "#define" in line:
                    while line.strip()[len(line.strip())-1] is ("\\"):
                        self.nr_line+=1 
                        line=self.tab_c[self.nr_line]
                        #fileHandler_tmp.write(line)
                        self.tab_after_corrections.append(line)
                        print(line)
                    #input("WordWithoutEndingCharacters  key ")
                    
                #else:
                self.nr_line+=1
                    
                continue        
            
            line = self.MergeLineInDifferentLines(self.tab_c)
            
            if self.FunctionPrototype is True:
                func_name,tab_arg = self.FunctionPrototypeInLine(line)
                for arg in tab_arg:
                    print("arg ",arg)
                    
                    print(AllAnalysedVariableTypes_dict)
                    
                    if arg[0] in AllAnalysedVariableTypes_dict:
                        prefix = AllAnalysedVariableTypes_dict[arg[0]]
                    
                        new_var, line  = self.AddPrefixToVariable(arg[1],prefix,line)
                        #print(new_var)
                        AllFunctionArgument[func_name]={arg[1]:new_var}
                print(func_name)
                print(AllFunctionArgument)
                #fileHandler_tmp.write(line)
                self.tab_after_corrections.append(line)
                self.nr_line+=1 
                continue
                input( " func ")
            
            if self.InFunctionDeclaration == True:
                
                func_temp = ClassToAnalyseCfile(self.tab_func)
                #func_temp.ShowCfile()
                func_temp.CorrectAllNames()
                
                print(" dict ",func_temp.dict_of_Variables_to_change)
                self.nr_line+=1 
                continue
                input(" key ")
            
            line_tab = self.DivideLine(line)
                
            #if normal coding line
            if (';' in line)  and not "(" in line and not ")" in line and not '[' in line and not ']' in line:
                
                for var_is_already in self.dict_of_Variables_to_change.keys():
                    if var_is_already in line_tab:
                        print(" var is already in dict ",var_is_already)
                        line = line.replace(var_is_already, self.dict_of_Variables_to_change[var_is_already] )
                        break
                
                for var_type in AllAnalysedVariableTypes_dict.keys():
                    
                    if var_type in line: 
                        #   if variable was defined  
                        print(var_type," line = ",line_without_comment)
                        variable = self.FindVariableinDefinition(line_without_comment)
                        prefix = AllAnalysedVariableTypes_dict[var_type]
                        prefix = self.IfPointerAdd_p(variable,prefix)
                        # if '*' in line:
                            # print(prefix,end='')
                            # prefix = prefix.replace('_','_p')
                            # print(" new :",prefix)
                    
                        print(" prefix for variable ",prefix)
                        #i am checking if this prefix is not already in variable
                        #print(variable)
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
            #fileHandler_tmp.write(line)  
            
        
    def  SaveAllTab(self,filename):
        line_nr = 0
        
        file=open(filename,"w")
        
        while line_nr<len(self.tab_after_corrections):
            
            file.write(self.tab_after_corrections[line_nr])
            
            line_nr +=1
        
        file.close()
    
    
    
#############################################################################    
    
    
def MarkersHASH():
    
    print("#"*100)
    
    
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
                
                #AnalyseFileZFCoding(fileHandler)
    elif len(tabOfAnalyzedFiles)>0:
    
        for filename in tabOfAnalyzedFiles:
            #if ".c" in file or ".h" in file:
            #    filename = file.split(".")[0]
            print("$"*100)
            print(filename)
            try:    
                file_c_p = open(filename,"r")
                print("!"*100)
                print(" I opened ",filename) 
                print("!"*100)
                tab_c = []
                line = file_c_p.readline()

                while(line):
                    tab_c.append(line)
                    line = file_c_p.readline()

            except:
                print("X"*100)
                print(" cannot open file ",filename)
                print("X"*100)
                sys.exit()
                
            analyze = ClassToAnalyseCfile(tab_c)
            #analyze.FindAllTypedefVar()
            
            
            #tab = analyze.RemoveAllCommentForAnalysis(analyze.tab_c)
            #analyze.ShowCfile()
            analyze.AnalyzeAllIncludes()
#            print(analyze.dict_of_Variables_to_change)
#            print("\n"*10)
#            input(" key ")
            analyze.FindAllTypedefVar()
            
            print(analyze.dict_of_Variables_to_change)
            
            analyze.CorrectAllVariablesNames()
            
            analyze.SaveAllTab(filename+"_ch")
            #input(" key ")
            
            #analyze.tab_c = 
    
    for key in AllIncludes_d.keys():
        print(key,"\t -> ",AllIncludes_d[key])
    
if __name__ == '__main__':
    main()