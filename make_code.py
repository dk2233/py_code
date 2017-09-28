import sys
import os
import shutil 
import time
import re

global SCRIPT_FOLDER
global VERSION

#to find all function declaration
#[\w]+[\s]+([\w])+[\s]*[(][\w\s,\*\[\]]+[)][\s]*;{1,}$

#to find definition
#[\w]+[\s]+([\w])+[\s]*[(][\w\s,\*\[\]]+[)][\s]*{{1,}$

VERSION = "1.09.27"
DIRECTORY=""
START_COMMENT_BLOCK = "/*"
END_COMMENT_BLOCK= "*/"
MODULE_PREFIX   =   "EDR"
#   if #include or #define there is no need for ; or {}
# all comments are remove during c-file analysis

HOW_MANY_LETTERS_FROM_WORD_END = 4
POINTER_PREFIX="_p"
ARRAY_PREFIX = "_a"

AllAnalysedVariableTypes_dict = {
    #"typedef":          "_t",
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
    "#endif",
    "#if",
    "#error",
    "#elif",
    
    
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
        self.NextLineIsCommented =      False
        # self.InTypedefBlockDefinition = False
        #self.InTypedefLineDefinition = False
        self.AnalyseThatVariable =      False
        self.FunctionPrototype =        False
        self.InFunctionDeclaration =    False
        self.dict_of_Variables_to_change=   {}
        self.tab_after_corrections=         []
        self.tab_if_equality            =   []
        
        
        
    def ShowCfile(self):
        for element in self.tab_c:
            print(element,end="")
        
    def ShowAllVariablesToChange(self):    
        print("\n"*5," all variable to change \n")
        
        for key in self.dict_of_Variables_to_change.keys():        
            print(key," -> ",self.dict_of_Variables_to_change[key])    
        
    def CheckWhetherLineCommented(self,tab):
        """ this find all comments and return two strings - all line with strings together 
        and line without comments"""
        
        line=tab[self.nr_line]        
        line_wc=line
        if (START_COMMENT_BLOCK in line):        
            while(not END_COMMENT_BLOCK in tab[self.nr_line]):
                self.nr_line +=1
                line +=tab[self.nr_line]                
            line_wc=line[:line.find(START_COMMENT_BLOCK)]+line[line.find(END_COMMENT_BLOCK)+len(END_COMMENT_BLOCK):]
        elif r'//' in line:
        #and not any(element in line for element in WordWithoutEndingCharacters):
            line_wc=line[:line.find('//')]
            
        return line,line_wc
     
    
    
    
    
    def DivideLine(self,line):
        line_tab = line.split() 
        return(line_tab)       
    
    
    def FindVariableinDefinition(self,line):
        """ here I have to give line without any comments """
        
        if "typedef" in line:
            while line.count("{")>0 and line.count("}")>0:        
                a1 = line.find("{")
                a2 = len(line)-1
                #here I remove everything between defining brackets
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
        # print(line_tab,end="" )
        print(" var = ",variable)
        return( variable)
    
    
    
    
    
        
        
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
                
                new_var,line  = self.AddPrefixToVariable(var,"_t",line)
                if new_var != var:
                    self.dict_of_Variables_to_change[var]=new_var
                    
                #AllAnalysedVariableTypes_dict["typedef"],line)
                # print(" var ",new_var)
                # input(" key ")
                self.nr_line +=1
                continue
            
            self.nr_line +=1
            
            
    
    def  FindAllInstancesOfTypes(self):
        ''' I find here all types and also types arguments in function '''    
        print("\n"*5,"&"*100)
        print(" Here I am in all variables finding")
        print("&"*100,"\n"*5)
        self.nr_line=0  
        while self.nr_line < len(self.tab_c):
            line,line_without_comment = self.CheckWhetherLineCommented(self.tab_c)
            if len(line_without_comment.strip())<2:
                self.nr_line+=1 
                continue
                
            if any(element in line_without_comment for element in WordWithoutEndingCharacters):
                self.tab_after_corrections.append(line)
                if  "#define" in line:
                    while line.strip()[len(line.strip())-1] is ("\\"):
                        self.nr_line+=1 
                        line=self.tab_c[self.nr_line]                
                self.nr_line+=1
                continue  
                
            line = self.MergeLineInDifferentLines(self.tab_c)
            # print("\t"*10,self.nr_line,"\n","$"*100,"\n"*2,line,"\n"*2,"$"*100, "\n\nself.InFunctionDeclaration ",self.FunctionPrototype )
            
            if self.FunctionPrototype is True:
                
                func_name,tab_arg = self.PrototypeFuncAnalysis(line)
                print(" !I found prototype! ",func_name)
                print(" arguments :",tab_arg)
                AllFunctionArgument[func_name]={}
                for arg in tab_arg:
                    print("^arg^ ",arg)                    
                    if "void" in arg:
                        continue
                    
                    var_new, var_old = self.CheckPrefixforVariable(arg)
                    
                    if var_new != var_old:
                        AllFunctionArgument[func_name].update({var_old:var_new})
#                
#                print(AllFunctionArgument)
            
            if self.InFunctionDeclaration == True or self.FunctionPrototype == True:
                self.nr_line +=1 
                continue
            
            
            # print("\t"*10,self.nr_line,"\n","$"*100,"\n"*2,line,"\n"*2,"$"*100)
            
            #check if here is array
            tab_array_var =[]
            regexp_array = r'[\w]*[\s]*(\w*)[[]'
            temp_var = re.findall(regexp_array,line)
            # if temp_var:
            for ii in temp_var:
                tab_array_var.append(ii)
                print(" this is array ",ii)
                # input(" key ")
            
            #line analysing to find all types    
            for searchedType in AllAnalysedVariableTypes_dict.keys():
                tab_pointers=[]
                regexp_const = searchedType+r'[\s\S]*const'+r'\s*\w*'
                temp_var = re.findall(regexp_const,line)
                if len(temp_var)>0:
                    print(" all found regexp ",temp_var)
                for ii in temp_var:
                    print(" here is $const$ ",ii)
                    print(" before change ",line)
                    ii2 = ii.replace('const','')
                    line=line.replace(ii,ii2)
                    print(" after change ",line)
                
                regexp_pointer = searchedType+r'\s*[*]{1,4}[\s\S]\w*'
                temp_var = re.findall(regexp_pointer,line)
                for ii in temp_var:
                    print(" here is $pointer$ ",ii)
                    #here I remove * from line but know already that it is pointer
                    line=line.replace('*','')
                    print(" here is $pointer$ ",ii, line)
                    tab_pointers.append(ii)
                    #print(line)
                                
                regexp1 = searchedType+r'\s*\w*'
                regexp_func = searchedType+r'\s*\w*[\s\S][(]'
                # regexp3 = searchedType+' *'+r'\s*\w*'
                
                temp_var_func =re.findall(regexp_func,line)                
                
                temp_var =re.findall(regexp1,line)
                
                for res_re in temp_var:
                    temp_tab=res_re.split()
                    if len(temp_tab)>1:
                        print(temp_var)
                        variable_name = temp_tab[1]
                        variable_type=temp_tab[0]
                        if any(variable_name in func1 for func1 in temp_var_func):
                            # print(temp_var_func," check ",variable_name in func1) 
                            print( variable_name, " this is function name do not correct like variables ")
                            continue
                                                
                        print(" type ",variable_type,", var =:",variable_name)                 

                        prefix = AllAnalysedVariableTypes_dict[variable_type]  
                        
                        print("^ARRAY^ is ",variable_name," in ",variable_name in tab_array_var)
                            
                        if  variable_name in tab_array_var:
                            print("new prefix ",prefix)
                            prefix = prefix.replace("_",ARRAY_PREFIX)
                        
                        for ii in tab_pointers:
                            print(variable_name,ii)
                            
                            
                            
                            if variable_name in ii:
                                print("@@@new prefix ",prefix)
                                prefix = prefix.replace("_",POINTER_PREFIX)
                            
                        new_var, aaa = self.AddPrefixToVariable(variable_name,prefix,res_re)
                        if new_var != variable_name:
                            self.dict_of_Variables_to_change[variable_name]=new_var
                        
                        print(" prefix for variable ",prefix, " new name ",new_var,"\n",aaa)
                        
                        # input( " key")
                        # newvar=re.sub()
                        # line= re.sub(r'\b'+searchedVar+r'\b',self.dict_of_Variables_to_change[searchedVar],line)
            self.nr_line +=1        
                    
    
    
    
    def  CheckPrefixforVariable(self,string):
        print(string)
        string = re.sub(r'[\s]*const[\s]+'," ",string)    
        print(string)    
        #WHAT IS name
        #t_name = re.findall(r'[const[\s]*]?[\w]+[\s]+[\*]*[\s]*([\w]+)',string)
        t_name = re.findall(r'[\w]+[\s]+[\*]*[\s]*([\w]+)',string)
        variable_name = t_name[0]
        
        t_name = re.findall(r'[const[\s]*]?([\w]+)[\s]+[\*]*[\s]*'+variable_name, string)
        variable_type = t_name[0]
        print(" regexp resul :",t_name)
        print(" var name ",variable_name, " var type ",variable_type)
        
        #checking if array
        tab_array_var =[]
        regexp_array = variable_name+r'[[]'
        temp_var = re.findall(regexp_array,string)        
        for ii in temp_var:
            tab_array_var.append(ii)
            print(" this is array ",ii)
            
        if variable_type  in AllAnalysedVariableTypes_dict.keys():
            prefix_proposed = AllAnalysedVariableTypes_dict[variable_type]
        else:
            prefix_proposed =""
        
        #string analysing to find all types    
         
        tab_pointers=[]        
            
        regexp_pointer = variable_type+r'[\s]*[*]{1,4}[\s\S]\w*'
        temp_var = re.findall(regexp_pointer,string)
        for ii in temp_var:
            # print(" here is $pointer$ ",ii)
            #here I remove * from string but know already that it is pointer
            string=string.replace('*','')
            # print(" here is $pointer$ ",ii, string)
            tab_pointers.append(ii)
            #print(string)
                            
        prefix =prefix_proposed
        
        print("^ARRAY^ is ",variable_name," in ",variable_name in tab_array_var)

        if  variable_name in tab_array_var:
            #print("new prefix ",prefix_proposed)
            prefix = prefix_proposed.replace("_",ARRAY_PREFIX)

        for ii in tab_pointers:
            print(variable_name,ii)
            if variable_name in ii:
                print("new prefix ",prefix)
                prefix = prefix.replace("_",POINTER_PREFIX)

        new_var, aaa = self.AddPrefixToVariable(variable_name,prefix,string)
#        if new_var != variable_name:
#            self.dict_of_Variables_to_change[variable_name]=new_var

        print(" $prefix$ for variable ",prefix, " new name ",new_var,"\n",aaa)

                # input( " key")
                # newvar=re.sub()
                # line= re.sub(r'\b'+searchedVar+r'\b',self.dict_of_Variables_to_change[searchedVar],line)

    
    
        return new_var,variable_name
    
    
    def  AddPrefixToVariable(self,variable,prefix,line):
        #wrong prefix:
        new_var = variable        
        #not real prefix - remove obsolete _xx (two letter max)
        if not (prefix in variable[(len(variable) - len(prefix)): len(variable)]):
            
            i=variable[len(variable)-HOW_MANY_LETTERS_FROM_WORD_END:].find("_")
            if i is not -1:
                i = i + len(variable)-HOW_MANY_LETTERS_FROM_WORD_END
                for pref in AllAnalysedVariableTypes_dict.values():
                    # print(pref)
                    if pref == prefix:
                        continue
                    for pref2 in [pref,pref.replace("_","_p"),  pref.replace("_","_a") ]:
                        if pref2 in variable[i:]:                        
                            new_var = variable.replace(pref2,"")
                            break
                    if   new_var != variable:
                        break
            #print("..",variable)    
            new_var = new_var+prefix
            
                
            print(" I am adding new variables to dictionary of ",new_var)
            
            line = line.replace(variable,new_var)
            print("Line after change ",line)
            # input(" key ")
        else:
            print(" prefix ", prefix," already in variable ")
            
        if "enum" in line and "typedef" in line:
            AllAnalysedVariableTypes_dict[variable]="_e"
    
        return new_var,line
    
    
    def PrototypeFuncAnalysis(self,string):
        """ to find all functions """
        
        #finding function name
        # tab_func = re.findall(r'([\w]*)[\s]*[(][\w]+[\s*]+[\w]+[)][\s]*;{1,}$',temp)   
        # tab_func = re.findall(r'[\w]+[\s]+([\w]+)[\s]*[(][\w\s,*]+[)][\s]*;{1,}$',temp)
        tab_func = re.findall(r'[\w]+[\s]+([\w]+)[\s]*[(][\w\s,\*\[\]]+[)][\s]*;{1,}$',string)        
        function_name = tab_func[0]
        print( " &Function name :",function_name)
                
        allArgument_tab = re.findall(r'[(]([\w\s\,\*\[\]\(\)]+)[)]',string)
        
        tab_arg = allArgument_tab[0].split(',')
        
        return function_name, tab_arg

    
            
            
            
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
                
                try:    
                    file_c_p = open(filename,"r")
                    print("!"*100)
                    print(" I opened ",filename) 
                    print("!"*100)
                    # input(" key ")
                except:
                    print("X"*100)
                    print(" cannot open file :",filename,":")
                    print("X"*100)
                    AllIncludes_d[filename] = " not found "
                    # input(" key ")
                    self.nr_line +=1                    
                    continue
                    
                tab = []
                line = file_c_p.readline()

                while(line):
                    tab.append(line)
                    line = file_c_p.readline()
                file_c_p.close()
                
                inc = ClassToAnalyseCfile(tab)
                inc.FindAllTypedefVar()
                inc.FindAllInstancesOfTypes() 
                tab = inc.CorrectAllVariablesNames(inc.tab_c)
                tab = inc.CorrectAllFunctions(tab)            
                inc.SaveAllTab(filename+"_ch", tab)
            
                AllIncludes_d[filename]=inc.dict_of_Variables_to_change
                print(inc.dict_of_Variables_to_change)
            
                self.dict_of_Variables_to_change.update(inc.dict_of_Variables_to_change)
                
#                    input(" key ")
                        
                
                
            self.nr_line +=1
        
        
        
        
        
    def IsThisWord(self,string):
        isWord = False
        if len(string)>2:
            if not any(mark in string for mark in SignNotForWord):
                isWord = True
        return isWord  
                

        
        
    
            
            
    def MergeLineInDifferentLines(self,tab):
        """ method to connect all lines that are one statement, but divided during development for readibility 
        
        it sees that:
        - line has ';' that is simple statement but couple of lines can be one statemen
        - line can has function prototype it has () and ;
        - line can start function definitions in that case we have more then two words + ()+ { and ending }
        """                       
        temp = ""
        temp_wc = ""
        self.tab_func = []
        level_of_para = 0
        level_of_para_func = 0
        
        self.FunctionPrototype = False
        wordCountBeforeParanthesis = 0
        
        LineFinish = False
        self.InFunctionDeclaration = False

        while not LineFinish:
            line,line_without_comment = self.CheckWhetherLineCommented(tab)
                    
            # if  any(func in line for func in AllFunctionArgument):
                # print(" that function ",func, " is in tab functions ")
                
            line_without_comment = line_without_comment.replace("("," ( ")
            line_without_comment = line_without_comment.replace(")"," ) ")
            temp +=line
            temp_wc +=line_without_comment
            self.tab_func.append(line)
            
            # print(self.InFunctionDeclaration,temp)
            #try to find function prototype
            if self.InFunctionDeclaration is False:
                tab_func = re.findall(r'[\w]+[\s]+([\w]+)[\s]*[(][\s]*[\w\s,\*\[\]]+[\s]*[)][\s]*\;{1}',temp_wc)
                if len(tab_func)>0:
                    print(temp)
                    print(" ##tab func ",tab_func)                
                    self.FunctionPrototype = True
                    # input(" prototype ")
                    break
                    
            
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
            
                
            if ';' in line and (level_of_para == 0) and self.InFunctionDeclaration == False:
                LineFinish = True
                break
            
            if self.InFunctionDeclaration == True and (level_of_para == 0) and "}" in line:
                LineFinish = True
                break
                
            self.nr_line +=1
                      
        print("*"*100)                    
        print(" merge :",temp[0:100])
        print("^"*100)
        # if "(" in temp and ";" in temp and not '{' in temp:
            # self.FunctionPrototype = True            
            # print(temp.replace("\n"," "))
            # temp = temp.replace("\n"," ")
            # temp +="\n"
            
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
                        # print(line)
                    #input("WordWithoutEndingCharacters  key ")

                self.nr_line+=1
                continue        
    
    
    
        
    def  CorrectAllVariablesNames(self,tab):
        self.nr_line=0
        self.tab_after_corrections=[]
        while self.nr_line < len(tab):
            
            line,line_without_comment = self.CheckWhetherLineCommented(tab)
            if len(line_without_comment.strip())<2:                
                self.tab_after_corrections.append(line)
                self.nr_line+=1 
                continue            
            # print(line)
            # print(self.dict_of_Variables_to_change.keys())
            for searchedVar   in self.dict_of_Variables_to_change.keys():
                
                line2= re.sub(r'\b'+searchedVar+r'\b',self.dict_of_Variables_to_change[searchedVar],line)
                if line != line2:    
                    print(searchedVar)
                    # print("\t\t I have changed ",searchedVar," in ",line2)
                    line = line2    
                
                # print(" new value ",self.dict_of_Variables_to_change[searchedVar])
            
                
            self.tab_after_corrections.append(line)
            self.nr_line+=1
            
        return     self.tab_after_corrections 
        
        
        
        
        
    def CorrectAllFunctions(self,tab):
        self.nr_line=0
        self.tab_after_corrections=[]
        while self.nr_line < len(tab):
            
            line,line_without_comment = self.CheckWhetherLineCommented(tab)
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
                        line=tab[self.nr_line]
                        #fileHandler_tmp.write(line)
                        self.tab_after_corrections.append(line)
                #else:
                self.nr_line+=1        
                continue 
                
            line = self.MergeLineInDifferentLines(tab)
            #print(self.nr_line,"\n",line[0:250],"\n......")
            # print("$"*100,self.nr_line,"\n",line,"\n"*2)
            
            
            #tab_func =       re.findall(r'[\w]+[\s]+([\w]+)[\s]*[(][\w\s,\*\[\]]+[)][\s]*;{1,}$',string)        
            # tab_func_proto = re.findall(r'[\w]+[\s]+([\w]+)[\s]*[(][\w\s,\*\[\]]+[)][\s]*;{1}$',line)
            tab_func_proto = re.findall(r'[\w]+[\s]+([\w]+)[\s]*[(][\s]*[\w\s,\*\[\]]+[\s]*[)][\s]*\;{1}',line)                            
            if len(tab_func_proto)>0:
                print("^Correction in ^prototype ",tab_func_proto)
                            
                #input(" func ")
                #print(self.nr_line,"\n",line)
                if tab_func_proto[0] in AllFunctionArgument.keys():
                    dict_toChange = AllFunctionArgument[tab_func_proto[0]]
                    # print(" ifffem ",dict_toChange)
                    
                    for key in dict_toChange:
                        #print(key)
#                        line=re.sub(r'[\s]*'+key+r'[\s]*',dict_toChange[key],line)
                        line=re.sub(r'\b'+key+r'\b',dict_toChange[key],line)
                        # print(line)
                        #input(" arg ")
            
            tab_func_declaration = re.findall(r'[\w]+[\s]+([\w]+)[\s]*[(][\s]*[\w\s,\*\[\]]+[\s]*[)][\s]*[\{]{1}[\s\S\{\}]*[\}]{1}',line)
            if len(tab_func_declaration)>0:
                print("^Correction in ^declaration ",tab_func_declaration)
                # print(line)
                local_var_tab_dict ={}
                tab_potential_local_var = re.findall(r'([\w]+[\s]+[\*]*[\s]*[\w]+)[\s]*[\=\;]{1}',line)
                print("^*^ ", tab_potential_local_var )
                for possible in tab_potential_local_var:  
                    for typet in AllAnalysedVariableTypes_dict.keys():
                        if typet in possible:
                            print(typet, " in ",possible)
                            #var = self.FindVariableinDefinition(possible)
                            new_var, var = self.CheckPrefixforVariable(possible)
                            local_var_tab_dict[var] = new_var
                            
                            print(" &&new var ",new_var," var ",var)
                            line=re.sub(r'\b'+var+r'\b',new_var,line)            
                            #input(" key ")
                            break
                            
                
                        
                        
                if tab_func_declaration[0] in AllFunctionArgument.keys():
                    dict_toChange = AllFunctionArgument[tab_func_declaration[0]]
                    
                    for key in dict_toChange:
                        print(" ^var to change^ ",key)
#                        line=re.sub(r'[\s]*'+key+r'[\s]*',dict_toChange[key],line)
                        # line=re.sub(key+r'[\s]*',dict_toChange[key],line)
                        line=re.sub(r'\b'+key+r'\b',dict_toChange[key],line)
        
                
                    
                    
                        #print(line)
                        #input(" arg ")
                #input(" func ")
            
                       
            self.tab_after_corrections.append(line)
            self.nr_line+=1   
        return self.tab_after_corrections
            #input("key")
            #fileHandler_tmp.write(line)  
            
        
    def  SaveAllTab(self,filename, tab):
        line_nr = 0
        
        file=open(filename,"w")
        
        while line_nr<len(tab):
            
            file.write(tab[line_nr])
            
            line_nr +=1
        
        file.close()
    
    def   FindAllIfStatement(self,tab,comparising):
        self.nr_line = 0
        
        while self.nr_line<len(tab):
            
            line,line_without_comment = self.CheckWhetherLineCommented(tab)
            if len(line_without_comment.strip())<2:
                self.nr_line+=1 
                continue
            
            if any(element in line_without_comment for element in WordWithoutEndingCharacters):
                if  "#define" in line:
                    while line.strip()[len(line.strip())-1] is ("\\"):
                        self.nr_line+=1 
                        line=tab[self.nr_line]
                self.nr_line+=1
                continue   
            
            # tab_statement = re.findall(r'if[\s]*\([\w\s]*==[\w\s]*',line)
            tab_statement = re.findall(r'if[\s]*[\(\s]*(?:[\&\|\w\s\[\]\(\)\*\,]+'+comparising+'[\s\w\[\]\(\)\*\&\|\,]+)+[\s]*[\)]+[\s]*\{',line)
            if len(tab_statement)>0:
                for word in tab_statement:                
                    self.tab_if_equality.append(word+"\n")                
            self.nr_line +=1
            
        self.tab_if_equality.append("\n\n how many if statements :"+str(len(self.tab_if_equality)) )   
            
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
                file_c_p.close()
                
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
            print("\n"*10)
            print("$"*100)
            print("$"*100)
            print("\t"*10," ANALYSIS of ",filename)
            print("$"*100)
            print("$"*100,"\n"*2)
#            input(" key ")
            
            analyze.FindAllTypedefVar()
            
            analyze.ShowAllVariablesToChange()
            
            analyze.FindAllInstancesOfTypes() 
            
            analyze.ShowAllVariablesToChange()
            
            tab = analyze.CorrectAllVariablesNames(analyze.tab_c)
            
            
            tab = analyze.CorrectAllFunctions(tab)  
            analyze.FindAllIfStatement(tab,"==")
            analyze.FindAllIfStatement(tab,"!=")
            
            analyze.SaveAllTab(filename+"_ch", tab)
            analyze.SaveAllTab(filename+"_if", analyze.tab_if_equality)
            
            
            
            
            
#Lists all tables
    analyze.ShowAllVariablesToChange()
        
    print("\n"*10," all includes files ")
    for key in AllIncludes_d.keys():
        print(key,"\t -> ",AllIncludes_d[key])
        
    print("\n"*10," all analyzed types ")    
    for key in AllAnalysedVariableTypes_dict.keys():
        print(key,"\t -> ",AllAnalysedVariableTypes_dict[key])
    
    
    print("\n"*10," all analyzed function variables ")    
    for key in AllFunctionArgument.keys():
        print(key,"\t -> ",AllFunctionArgument[key])
    
    
if __name__ == '__main__':
    main()