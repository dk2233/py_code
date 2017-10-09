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

VERSION = "1.10.8"
DIRECTORY=""
START_COMMENT_BLOCK = "/*"
END_COMMENT_BLOCK= "*/"
MODULE_PREFIX   =   "Edr"
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
    "void":             "",
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

global AllTypedefs
AllTypedefs = []

AllFunctionsToAddExtern = []

AllFunctionsToCorrectPrefix = {}

AllPointers_d = {}

AllArrays = []

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
    """class to analyze c file"""
    
    def __init__(self,filename):    
        self.CantOpenFile = False
        self.StringAllLinesWithoutComment =""
        self.StringAllLines=""
        
        self.tab_c = []      
        self.nr_line = 0     
        
        self.FunctionPrototype =        False
        self.InFunctionDeclaration =    False
        
        self.dict_of_Variables_to_change=   {}
        
        self.tab_after_corrections=         []
        self.tab_if_equality            =   []
        self.tab_all_comments           =   []
        
        self.AllTypeDefArray   =   []
        self.AllPointers = {}
        self.AllArrays = {}
        
        try:    
            file_c_p = open(filename,"r")
            
        
        except:
            print("X"*100)
            print(" cannot open file ",filename)
            print("X"*100)
            self.CantOpenFile = True
        
        
        if self.CantOpenFile != True: 
            print("!"*100)
            print(" I opened ",filename, " for analyzis") 
            print("!"*100)   
            line = file_c_p.readline()
            while(line):
                self.tab_c.append(line)
                line = file_c_p.readline()
            file_c_p.close()
            
            self.StringAllLines = self.ChangeArrayToString(self.tab_c) 
            self.StringAllLinesWithoutComment = self.RemoveAllCommentsFromString(self.StringAllLines)
               
            
            
            string_WC2 = self.FindAllTypedef_enum_nonstruct(self.StringAllLinesWithoutComment)
            string_WC3 = self.FindAllTypedefStruct_regexp(string_WC2)
            
            self.FindAllPointers(self.StringAllLinesWithoutComment)
            self.FindAllArrays(self.StringAllLinesWithoutComment)
            
            
            
            self.FindAllInstancesOfTypes(string_WC2)
            self.FindAllFunctionPrototype(string_WC2,filename)
            
            
            self.tab_all_comments = self.FindAllComments(self.StringAllLines)
            self.FindAllIfStatement(self.tab_c,"==")
            self.FindAllIfStatement(self.tab_c,"!=")
        #print(" heelllo ")
        
        
        
        
    def ChangeArrayToString(self,tab):        
        self.nr_line = 0
        string_all_lines = ""
        while self.nr_line<len(tab):
            string_all_lines +=tab[ self.nr_line ]
            self.nr_line +=1        
        return(string_all_lines)
            
            
    def ChangeStringToArray(self,string):
        tab=[]
        print(" changin string to array ")
        # print(string)
        # print(string.find("\n"))
        while string.find("\n") > -1:
            temp = string.partition("\n")
            tab.append(temp[0])
#            tab.append(temp[0]+temp[1])
            string = temp[2]                
        return tab
        
        
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
     
    def RemoveAllConfusingWords(self,fileString):
        ''' this is to remove unnecessary words like const from all file'''
        
        fileString = re.sub(r'\b'+'const'+r'\b',"",fileString)
        return fileString
   
    def CheckIfPrefixInInstanceChange(self,var_name):
        ''' it checks if prefix in variable has correct name '''
        # regexp for variable definitions it wont find with = 
        # (?<!return)\w*\s*\w*\s*\w+\s+\w+\s*\;
        new_var_name = var_name
        tab_prefix = re.findall(r'\b'+MODULE_PREFIX+r'\w*',var_name,re.I)
        if len(tab_prefix) > 0:
            
            #there is module prefix but it maybe with wrong letter case
            tab_prefix_not_ignorecase = re.findall(MODULE_PREFIX,var_name)
            if len(tab_prefix_not_ignorecase)==0:
                #it has wrong case remove that prefix and replace with good one
                funcname1 = re.sub(r'\b'+MODULE_PREFIX,"",var_name,1,re.I)
                new_var_name = MODULE_PREFIX+funcname1
    
    
        return new_var_name, var_name
    
    
    
    def CheckIfPrefixInInstance(self,var_name):
        ''' it checks if prefix in variable has correct name '''
        # regexp for variable definitions it wont find with = 
        # (?<!return)\w*\s*\w*\s*\w+\s+\w+\s*\;
        new_var_name = var_name
        tab_prefix = re.findall(r'\b'+MODULE_PREFIX+r'\w*',var_name,re.I)
        if len(tab_prefix) == 0:
            #there is no EDR at all it has to be add in the beginning of function name
            #only if it has global scope
            print(" adding prefix ",MODULE_PREFIX," to name ",var_name)
            new_var_name = MODULE_PREFIX+var_name
        
        else:
            #there is module prefix but it maybe with wrong letter case
            tab_prefix_not_ignorecase = re.findall(MODULE_PREFIX,var_name)
            if len(tab_prefix_not_ignorecase)==0:
                #it has wrong case remove that prefix and replace with good one
                funcname1 = re.sub(r'\b'+MODULE_PREFIX,"",var_name,1,re.I)
                new_var_name = MODULE_PREFIX+funcname1
        #😅
    
        return new_var_name, var_name
    
    def DivideLine(self,line):
        line_tab = line.split() 
        return(line_tab)       
    
    
    def FindAllFunctionPrototype(self,string_WC,filename):
        '''it finds all function prototypes 
        Prototype function that 
        check if they has correct prefix => if not, add to table to change
        '''
        print(" Finding all prototypes ")
        tab_functions = re.findall(r'\w*\s*\w+\s+\**\s*(\w+)\s*\(([\w+\s*\,\*]+)\)\s*\;',string_WC)
        for i in tab_functions:
            print(i)
            tab_arg = i[1].split(',')            
            func_name = i[0]
            
            if isVerbose == True:
                print(" !I found prototype! ",func_name)
                print(" arguments :",tab_arg)
                
            AllFunctionArgument[func_name]={}
            for arg in tab_arg:
                if isVerbose == True:
                    print("^arg^ ",arg)                    
                if "void" in arg:
                    continue

                var_new, var_old = self.CheckDataSuffixforVariable(arg)
                print(var_new, var_old)
                #checking wrong prefix in variable
                var_new, aaa= self.CheckIfPrefixInInstanceChange(var_new)
                
                if "_t" in var_new[-len("_t"):]:
                    variable_name = var_new[:(-len("_t"))]
                    var2 = var_new.replace(var_new,variable_name)
                    self.dict_of_Variables_to_change[var_new]=var2
                    if isVerbose == True:
                        print(" added ",var_new," to ",self.dict_of_Variables_to_change)
                    
                
                if var_new != var_old:
                    AllFunctionArgument[func_name].update({var_old:var_new})
        tab_functions = re.findall(r'(\w*\s*\w+\s+\**\s*(\w+)\s*\([\w+\s*\,\*]+\)\s*\;)',string_WC) 
        if ".h" in filename:
            for ii in tab_functions:
                
                if not 'extern' in ii[0]:
                    if isVerbose == True:
                        print("not extern  in ",ii)
                    AllFunctionsToAddExtern.append(ii[1])

                else:
                    if isVerbose == True:
                        print("  extern  in ",ii)
                    
                    # AllFunctionsToAddExtern.append(ii[1])
                    
        #checking for correct function name            
        for ii in tab_functions:
            #ignorecase search
            tab_prefix = re.findall(r'\b'+MODULE_PREFIX+r'\w*',ii[1],re.I)
            if len(tab_prefix) == 0:
                #there is no EDR at all it has to be add in the beginning of function name
                #only if it has global scope
                if ".h" in filename:
                    print(" adding prefix ",MODULE_PREFIX," to function name ",ii[1])
                    AllFunctionsToCorrectPrefix[ii[1]] = MODULE_PREFIX+ii[1]
            
            else:
                print(" %^%There is wrong prefix in ",ii[0],ii[1])
                #there is module prefix but it maybe with wrong letter case
                tab_prefix_not_ignorecase = re.findall(r'\b'+MODULE_PREFIX+r'\w*',ii[1])
                print(tab_prefix_not_ignorecase)
                if len(tab_prefix_not_ignorecase)==0:
                    #it has wrong case remove that prefix and replace with good one
                    
                    funcname1 = re.sub(r'\b'+MODULE_PREFIX,"",ii[1],1,re.I)
                    print(" %++++%Adding new prefix ",funcname1)
                    AllFunctionsToCorrectPrefix[ii[1]] = MODULE_PREFIX+funcname1
                
        return tab_functions
        
        
        
    def FindAllTypedef_enum_nonstruct(self,string):
        ''' this method find in string all typedef enum and non struct simple one '''
        tab_typedef_enum = re.findall(r'(typedef[\s]+enum\s*\{[\s\S]+?\}\s*([\w]+)\s*;)',string)
        #print(" typedef enum types ",tab_typedef_enum)
              
        for type_enum in tab_typedef_enum:    
            new_type_name, old_name = self.AddPrefixToVariable(type_enum[1],"_t")
            new_type_name, var= self.CheckIfPrefixInInstance(new_type_name)
            
            if new_type_name!= type_enum[1]:
            # if new_type_name!= type_name:
                self.dict_of_Variables_to_change[type_enum[1]]=new_type_name
            AllAnalysedVariableTypes_dict[type_enum[1]]="_e"
            string = string.replace(type_enum[0],"")
            self.AllTypeDefArray.append(type_enum[1])  
        
        
        tab_typedef_simple= re.findall(r'(typedef[\s]+[\s\w\*\(\)\[\]]+?([\w]+)\s*\;)',string)
        # print(" typedef non-struct types ",tab_typedef_simple)
        for type_nons in tab_typedef_simple:
            new_type_name, older = self.AddPrefixToVariable(type_nons[1],"_t")
            new_type_name, var= self.CheckIfPrefixInInstance(new_type_name)            
            print( new_type_name, " = > ",type_name)
            # input(" key ")
            if new_type_name!= type_nons[1]:
            # if new_type_name!= type_name:
                self.dict_of_Variables_to_change[type_name]=new_type_name
            string = string.replace(type_nons[0],"")
            self.AllTypeDefArray.append(tab_typedef_simple[1])
        
        return string
    
    
    
    
    
    def FindAllTypedefStruct_regexp(self,string):
        
        typedef_for_farther_analysis = []        
        typedef_reg_struct = r'typedef\s+struct\s*\{[\s\S]+?\}\s*[\w]+\s*\;'        
        tab_typedef= re.findall(r'(typedef\s+struct\s*\{[\s\S]+?\}\s*([\w]+)\s*\;)',string)        
        print(" searching with regexp for structured typedefs ")
        for i in tab_typedef:
            #print(i[0])
            print(i[1])
            
            if i[0].count("{") != i[0].count("}"):
                print(i[0])
                print(" not ok \{ not enclosed with \} ")
                typedef_for_farther_analysis.append(i[0])
                #input(" key ")
            else:
                new_type_name, previous1 = self.AddPrefixToVariable(i[1],"_t")
                new_type_name, type_name= self.CheckIfPrefixInInstance(new_type_name)
                
                if new_type_name!= i[1]:
                    self.dict_of_Variables_to_change[i[1]]=new_type_name
                string = string.replace(i[0],"")
        #for i in tab_typedef:    
                
        for typedef_string1 in typedef_for_farther_analysis:
            starting_in_string = string.find(typedef_string1)
            end_in_string = string.find(typedef_string1)+len(typedef_string1)
            # print("starting_in_string:",starting_in_string)
            # print("end_in_string:",end_in_string)
            
            string_for_analysis = string[end_in_string:]
            
#            tab = re.findall(r'([\s]*struct[\s]*\{[\s\S]+?\})',type1)
            # print("$"*100)
            # print(string_for_analysis)
            # print("$"*100)
            # print(type1)
            # tab = re.findall(r'('+typedef_reg_struct+r'\s*\w*\s*\{[\s\S]+?\}\s*([\w]+)\s*\;'+r')',string)
            # print("tab = ",tab[0][0])
            AllDefinition = False
            ISAllBracetClosed = False
            tab = self.ChangeStringToArray(string_for_analysis)
            while (ISAllBracetClosed is False) and (AllDefinition is False) :
                
                typedef_string1 = typedef_string1+tab[0]+"\n"
                tab.remove(tab[0])
                
                ISAllBracetClosed = typedef_string1.count("{") == typedef_string1.count("}")
                # print(typedef_string1)
                # print(ISAllBracetClosed)
                if ISAllBracetClosed is True:
                    # 
                    checking_whole_struct = re.findall(r'(typedef\s+struct\s*\{[\s\S]+\}\s*([\w]+)\s*\;)',typedef_string1)
                    if len(checking_whole_struct)>0:
                        
                        AllDefinition = True
                # input( " searching ")       
            # print(" all typedef ",checking_whole_struct.group(0))
            # print(" all typedef ",checking_whole_struct)
            string = string.replace(checking_whole_struct[0][0],"")
            
            # type_name = re.search(r'typedef\s+struct\s*\{[\s\S]+\}\s*([\w]+)\s*\;',typedef_string1)
            print(" typedef name :",checking_whole_struct[0][1])
            
            # input(" after finding 1")
            
            new_type_name, older = self.AddPrefixToVariable(checking_whole_struct[0][1],"_t")
            new_type_name, type_name= self.CheckIfPrefixInInstance(new_type_name)
            if new_type_name!= checking_whole_struct[0][1]:
                self.dict_of_Variables_to_change[checking_whole_struct[0][1]]=new_type_name
            
            
        return string
        
        
        
    def FindAllTypedefEvenWithPlentyBracets(self,tab):
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
                if isVerbose == True:
                    print(" searching variable of typedef ")
                var = self.FindVariableinDefinition(line)
                if isVerbose == True:
                    print(" var ",var)
                
                new_var,older  = self.AddPrefixToVariable(var,"_t")
                new_var, type_name= self.CheckIfPrefixInInstance(new_var)
                if new_var != var:
                    self.dict_of_Variables_to_change[var]=new_var
            
                self.nr_line +=1
                continue
            
            self.nr_line +=1
            
    
    
    
    
    
        
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
    
    
    
    
    def  RemoveAllCommentsFromString(self,string_with_c_code):
        tab_comments = self.FindAllComments(string_with_c_code)
        for block_to_remove in tab_comments:
            # print(block_to_remove)
            #string_with_c_code = re.sub(block_to_remove,"",string_with_c_code)
            string_with_c_code = string_with_c_code.replace(block_to_remove,"")
        return string_with_c_code
    
    
    
    
    def FindAllInstancesOfKnownTypesWithRegexp(self,stringWC):
        ''' I find here all types and also types arguments in function 
        but using regexp parsing whole c or h file''' 
            
        if isVerbose == True:
            print("\n"*5,"&"*100)
            print(" Here I am in all variables finding")
            print("&"*100,"\n"*5)
        
        
        for type in AllAnalysedVariableTypes_dict:
        
            tab_all_known = re.findall(type+r'\s+\w+\s*[\;|\=]',stringWC)
            
            
            
            
    def  FindAllWrongSuffix(self,string_WC):
        ''' this should check whether variable doesnt has wrong suffix and remove it '''
        #this is to remove all additional _t from variables
        tab_variable_name = re.findall(r'\w*\s*\**\s*\w+\s+(\w+_t)\s*\;',string_WC)
        #print(tab_variable_name)
        if len(tab_variable_name)>0:
            if isVerbose == True:
                print(tab_variable_name)
            #input(" key ")
            for line in tab_variable_name:
                if "_t" in line[-len("_t"):]:
                    variable_name = line[:(-len("_t"))]
                    var2 = line.replace(line,variable_name)
                    self.dict_of_Variables_to_change[line]=var2
                    if isVerbose == True:
                        print(" added ",line," to ",self.dict_of_Variables_to_change)
                        print(line)
    
    def CorrectAllBitfield(self,string_WC):
        tab_bitfields = re.findall(r'\w+\s+(\w+)\s*\:\s*(\d)\;',string_WC)
        if len(tab_bitfields)>0:
            if isVerbose == True:
                print(tab_bitfields)
                
            for line in tab_bitfields:
                suffix = "_b"+str(line[1])
                #print(suffix, suffix not in line[-len(suffix):])
                if suffix not in line[0][-len(suffix):]:
                    tab_checks = ["_a","_t","_b","_p"] 
                    for i in AllAnalysedVariableTypes_dict.values():
                        #print(i)
                        tab_checks.append(i)
                    #print(tab_checks)
                    
                    var = line[0]
                    #print(line[0])
                    for checks in tab_checks:
                        if line[0].find(checks)>(len(line[0])-len(checks)):
                            var = line[0].replace(checks,"")
                            #print(var)
                    ttt = re.findall(r'\w+(_b\d*)',var)
                    if len(ttt)>0:
                        var = var.replace(ttt[0],"")
                    var = var+suffix
                    self.dict_of_Variables_to_change[line[0]]=var
                    if isVerbose == True:
                        print(" added ",line[0]," to ",self.dict_of_Variables_to_change)
                        print(line)
    
    def FindAllPointers(self,string_WC):
        print("*-poniters-*"*5)
        string_WC = self.RemoveAllConfusingWords(string_WC)
        
        regexp_pointer = r'(\w+)\s*[\*]+\s*(\w+)\s*[\;|\=]'
        #regexp_pointer2 = r'(\w+\s*[\*]+\s*\w+\s*)[\;|\=]'
        temp_var = re.findall(regexp_pointer,string_WC)
        
        for ii in temp_var:
            if isVerbose == True:
                print(" here is $pointer$ ",ii[1]," of type ",ii[0])
            variable_type = ii[0]
            #tab_pointers.append(ii)
            self.AllPointers[ii[1]] = ii[0]
            #new_var, old = self.CheckDataSuffixforVariable(ii[0]+" *"+ii[1])
            
            if variable_type  in AllAnalysedVariableTypes_dict.keys():
                prefix_proposed = AllAnalysedVariableTypes_dict[variable_type]
            else:
                prefix_proposed =""
                
            if isVerbose == True:
                print(variable_type, "-> &&&&& prefix &&&& proposed :",prefix_proposed)    
                
            #print("\n"*2," - > ",new_var, old,"\n"*2)
            
        print("*-poniters-*"*5)
        #input(" key ")
    
    def FindAllArrays(self,string_WC):
        print("*-Arrays-*"*5)
        string_WC = self.RemoveAllConfusingWords(string_WC)
        regexp_array = r'(\w+)\s+(\w+)\[[\w+\s*]+\]\s*[\;|\=]'
        temp_array = re.findall(regexp_array,string_WC)
        for ii in temp_array:
            if isVerbose == True:
                print(" here is $ARRAY$ ",ii[1])
            
            self.AllArrays[ii[1]] = ii[0]
            #print(line)
        print("*-Arrays-*"*5)
    
        
            
    def  FindAllInstancesOfTypes(self,string_WC):
        ''' I find here all types and also types arguments in function ''' 
        if isVerbose == True:
            print("\n"*5,"&"*100)
            print(" Here I am in all variables finding")
            print("&"*100,"\n"*5)
        
        self.FindAllWrongSuffix(string_WC)
        
        self.CorrectAllBitfield(string_WC)
        
        tab = self.ChangeStringToArray(string_WC)
               
        self.nr_line=0  
        while self.nr_line < len(tab):
            line = tab[self.nr_line]  
            if len(line.strip())<2:
                self.nr_line+=1 
                continue
                
            if any(element in line for element in WordWithoutEndingCharacters):
                self.tab_after_corrections.append(line)
                if  "#define" in line:
                    while line.strip()[len(line.strip())-1] is ("\\"):
                        self.nr_line+=1 
                        line=tab[self.nr_line] 

                self.nr_line+=1
                continue  
                
            line = self.MergeLineInDifferentLines(tab)
        
            print(" function declaration or prototype ",self.InFunctionDeclaration,self.FunctionPrototype )
            
            if self.InFunctionDeclaration == True or self.FunctionPrototype == True:
                self.nr_line +=1 
                continue
        
            #check if here is array
            # tab_array_var =[]
#             regexp_array = r'\w*[\s]*(\w*)\['
#             temp_var = re.findall(regexp_array,line)
#             for ii in temp_var:
#                 tab_array_var.append(ii)
#                 AllArrays.append(ii)
#                 if isVerbose == True:
#                     print(" ->ARRAY this is array ",ii)
#                 new_var = ii
#                 if "_a" not in ii[-HOW_MANY_LETTERS_FROM_WORD_END:]:
#                     new_var = ii+"_a"
#                 if ii != new_var:
#                     self.dict_of_Variables_to_change[ii]=new_var
#                     if isVerbose == True:
#                         print(" new ",ii)
                    
            
            #line analysing to find all types    
            for searchedType in AllAnalysedVariableTypes_dict.keys():
                #print(" i am searching in all types ")
                tab_pointers=[]
                regexp_const = searchedType+r'[\s\S]*const'+r'\s*\w*'
                temp_var = re.findall(regexp_const,line)
                if len(temp_var)>0:
                    if isVerbose == True:
                        print(" all found regexp ",temp_var)
                for ii in temp_var:
                    if isVerbose == True:
                        print(" here is $const$ ",ii)
                        print(" before change ",line)
                    ii2 = ii.replace('const','')
                    line=line.replace(ii,ii2)
                    if isVerbose == True:
                        print(" after change ",line)
                        
                regexp1 = searchedType+r'\s*\w*'
                regexp_func = searchedType+r'\s*\w*[\s\S][(]'
                
                temp_var_func =re.findall(regexp_func,line)                
                temp_var =re.findall(regexp1,line)
                
                for res_re in temp_var:
                    temp_tab=res_re.split()
                    if len(temp_tab)>1:
                        if isVerbose == True:
                            print(temp_var)
                        variable_name = temp_tab[1]
                        variable_type=temp_tab[0]
                        
                        if any(variable_name in func1 for func1 in temp_var_func):
                            if isVerbose == True:
                                print( variable_name, " this is function name do not correct like variables ")
                            continue
                        if isVerbose == True:                        
                            print(" type ",variable_type,", var =:",variable_name)                 
                        
                        prefix = AllAnalysedVariableTypes_dict[variable_type]
                        
                        if isVerbose == True:
                            print("^ARRAY^ is ",variable_name," in ",variable_name in tab_array_var)
                            
                        if  variable_name in tab_array_var:
                            if isVerbose == True:
                                print("new prefix ",prefix)
                            prefix = prefix.replace("_",ARRAY_PREFIX)
                            #input(" key ")
                            
                        for ii in tab_pointers:                            
                            if variable_name in ii:
                                if isVerbose == True:
                                    print("@@@new prefix ",prefix)
                                prefix = prefix.replace("_",POINTER_PREFIX)
                        

#                        new_var, var = self.CheckDataSuffixforVariable(line)
                        
                        
                        
                        new_var, older = self.AddPrefixToVariable(variable_name,prefix)
                        new_var, aaa= self.CheckIfPrefixInInstanceChange(new_var)
                        if new_var != variable_name:
                            self.dict_of_Variables_to_change[variable_name]=new_var
                        if isVerbose == True:
                            print(" prefix for variable ",prefix, " new name ",new_var,"\n")
                        
                        # input( " key")
                        # newvar=re.sub()
                        # line= re.sub(r'\b'+searchedVar+r'\b',self.dict_of_Variables_to_change[searchedVar],line)
            self.nr_line +=1        
                    
    
    
    
    def  CheckDataSuffixforVariable(self,string):
        print("$$ ",string," $$")
        string = re.sub(r'[\s]*const[\s]+'," ",string)    
        # print(string)    
        #WHAT IS name
        #t_name = re.findall(r'[const[\s]*]?[\w]+[\s]+[\*]*[\s]*([\w]+)',string)
        t_name = re.findall(r'\w+\s+\**\s*([\w]+)',string)
        variable_name = t_name[0]
        
        t_name = re.findall(r'[const[\s]*]?([\w]+)[\s]+[\*]*[\s]*'+variable_name, string)
        variable_type = t_name[0]
        if isVerbose == True:
            print("CheckDataSuffixforVariable regexp resul :",t_name)
            print("CheckDataSuffixforVariable var name ",variable_name, " var type ",variable_type)
        
        #checking if array
        tab_array_var =[]
        regexp_array = variable_name+r'[[]'
        temp_var = re.findall(regexp_array,string)        
        for ii in temp_var:
            tab_array_var.append(ii)
            if isVerbose == True:
                print("CheckDataSuffixforVariable this is array ",ii)
            
        if variable_type  in AllAnalysedVariableTypes_dict.keys():
            prefix_proposed = AllAnalysedVariableTypes_dict[variable_type]
        else:
            prefix_proposed =""
                #string analysing to find all types    
         
        tab_pointers=[]        
            
        regexp_pointer = variable_type+r'[\s]*[*]{1,4}[\s\S]\w*'
        temp_var = re.findall(regexp_pointer,string)
        for ii in temp_var:
            #here I remove * from string but know already that it is pointer
            string=string.replace('*','')
            tab_pointers.append(ii)
            #print(string)
            
        # if isVerbose == True:
#print(" prefix proposed ",prefix_proposed)
                            
        prefix =prefix_proposed
        if isVerbose == True:
            print("^ARRAY^ is ",variable_name," in ",variable_name in tab_array_var)

        if  variable_name in tab_array_var:
            #print("new prefix ",prefix_proposed)
            prefix = prefix_proposed.replace("_",ARRAY_PREFIX)

        for ii in tab_pointers:
            # print(variable_name,ii)
            if variable_name in ii:
                if isVerbose == True:
                    print("new prefix ",prefix)
                prefix = prefix.replace("_",POINTER_PREFIX)

        new_var, aaa = self.AddPrefixToVariable(variable_name,prefix)
#        if new_var != variable_name:
#            self.dict_of_Variables_to_change[variable_name]=new_var
        if isVerbose == True:
            print(" $prefix$ for variable ",prefix, " new name ",new_var,"\n",aaa)

                # input( " key")
                # newvar=re.sub()
                # line= re.sub(r'\b'+searchedVar+r'\b',self.dict_of_Variables_to_change[searchedVar],line)

        return new_var,variable_name
    
    
    
    
    
    
    def  AddPrefixToVariable(self,variable,prefix):
        #wrong prefix:
        new_var = variable   
        Marker = False
        #not real prefix - remove obsolete _xx (two letter max)
        if not (prefix in variable[(len(variable) - len(prefix)): len(variable)]):
            
            i=variable[len(variable)-HOW_MANY_LETTERS_FROM_WORD_END:].find("_")
            if i is not -1:
                i = i + len(variable)-HOW_MANY_LETTERS_FROM_WORD_END
                
                #if prefix == "_ae":
                if variable[i:] in prefix:
                    if isVerbose == True:
                        print(variable[i:] , "  ", prefix)
                    new_var = variable.replace(variable[i:],"")
#                    input(" key array ")
                    Marker = True
                    
        
                for pref in AllAnalysedVariableTypes_dict.values():
                    if Marker == True:
                        break
                        # input(" True ")
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
            
            if isVerbose == True:    
                print(" I am adding new variables to dictionary of ",new_var)
            
            # line = line.replace(variable,new_var)
            #print("Line after change ",line)
            # input(" key ")
        else:
            if isVerbose == True:
                print(" prefix ", prefix," already in variable ")
        

        
        
        # if "enum" in line and "typedef" in line:
            # AllAnalysedVariableTypes_dict[var]="_e"
    
        return new_var,variable
    
    
    
    
    
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

    
            
            
            
    def  AnalyzeAllIncludes(self,string):
        
        tab_includes = re.findall(r'\#include[\s]*\"([\w\.]+)\"',string)
        print(tab_includes)
        #input(" key ")
               
        for filename in    tab_includes: 
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
                continue

            tab = []
            
            inc = ClassToAnalyseCfile(filename)

            #string_all = inc.ChangeArrayToString(inc.tab_c)
            
            # string_WC2 = inc.FindAllTypedef_enum_nonstruct(string_WC)
            #string_WC3 = inc.FindAllTypedefStruct_regexp(string_WC2)
            #   inc.FindAllFunctionPrototype(string_WC2,filename)
            
            print("X"*100,"\n"*5)
            print(" Searching for all instances in :",filename)
            print("X"*100,"\n"*5)
            
            self.AllTypeDefArray += inc.AllTypeDefArray
            self.AllPointers.update(inc.AllPointers) 
            self.AllArrays.update(inc.AllArrays) 
            
            AllIncludes_d[filename]=inc.dict_of_Variables_to_change
            print(inc.dict_of_Variables_to_change)            
            self.dict_of_Variables_to_change.update(inc.dict_of_Variables_to_change)
            
            print(" extern : ",AllFunctionsToAddExtern)
            
            tab = inc.CorrectAllVariablesNames(inc.tab_c)
            tab = inc.CorrectAllFunctions(tab,filename)
            string_all = inc.ChangeArrayToString(tab)
            string1 = inc.CorrectAllPrefix(string_all)
            # inc.SaveAllTab(filename+"_ch", tab)
            inc.SaveString(filename+"_ch",string1)
            

        
        
        
    def IsThisWord(self,string):
        isWord = False
        if len(string)>2:
            if not any(mark in string for mark in SignNotForWord):
                isWord = True
        return isWord  
                

    def MergeLineInDifferentLinesWC(self,tab_wc):
        """ method to connect all lines that are one statement, but divided during development for readibility 
        
        it sees that:
        - line has ';' that is simple statement but couple of lines can be one statemen
        - line can has function prototype it has () and ;
        - line can start function definitions in that case we have more then two words + ()+ { and ending }
        
        this method use tabe that was created from removing all comments line from code
        
        """                       
        temp = ""
        self.tab_func = []
        level_of_para = 0
        level_of_para_func = 0
        self.FunctionPrototype = False
        wordCountBeforeParanthesis = 0
        LineFinish = False
        self.InFunctionDeclaration = False
        
        while not LineFinish and (self.nr_line< len(tab_wc)):
            line_without_comment = tab_wc[self.nr_line]
            #line_without_comment = line_without_comment.replace("("," ( ")
            #line_without_comment = line_without_comment.replace(")"," ) ")
            temp +=line_without_comment
            self.tab_func.append(line_without_comment)
        
            if self.InFunctionDeclaration is False:
                tab_func = re.findall(r'[\w]+[\s]+([\w]+)[\s]*[(][\s]*[\w\s,\*\[\]]+[\s]*[)][\s]*\;{1}',temp)
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
                        
                if self.IsThisWord(word) == True:
                    wordCountBeforeParanthesis +=1
#                elif "(" in word:
#                    wordCountBeforeParanthesis = 0
#            
            level_of_para += line_without_comment.count("{")
            level_of_para -= line_without_comment.count("}")
            print(level_of_para)
            if ';' in line_without_comment and (level_of_para == 0) and self.InFunctionDeclaration == False:
                LineFinish = True
                break
            if self.InFunctionDeclaration == True and (level_of_para == 0) and "}" in line_without_comment:
                LineFinish = True
                break        
            self.nr_line +=1
             
        if isVerbose == True:
            print("*"*100)                    
            print(" merge :",temp[0:100])
            print("^"*100)
        # if "(" in temp and ";" in temp and not '{' in temp:
            # self.FunctionPrototype = True            
            # print(temp.replace("\n"," "))
            # temp = temp.replace("\n"," ")
            # temp +="\n"
            
        return(temp)    
        
        
    
            
            
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
                    if isVerbose == True:
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
            
        if isVerbose == True:              
            print("*"*100)                    
            print(" merge :",temp[0:100])
            print("^"*100,"\n"*4)
        # if "(" in temp and ";" in temp and not '{' in temp:
            # self.FunctionPrototype = True            
            # print(temp.replace("\n"," "))
            # temp = temp.replace("\n"," ")
            # temp +="\n"
            
        return(temp)    
    
    
    
        
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
                    if isVerbose == True:
                        print(searchedVar)
                    # print("\t\t I have changed ",searchedVar," in ",line2)
                    line = line2    
                
                # print(" new value ",self.dict_of_Variables_to_change[searchedVar])
            
                
            self.tab_after_corrections.append(line)
            self.nr_line+=1
            
        return     self.tab_after_corrections 
        
        
    def CorrectAllPrefix(self,stringFile):
        print("$"*100)
        print(" Correcting prefix ","\n"*10)
        # print(stringFile)
        print("$"*100)
        for func in AllFunctionsToCorrectPrefix.keys():
            print(func," -> ",AllFunctionsToCorrectPrefix[func])
            stringFile = re.sub(func,AllFunctionsToCorrectPrefix[func],stringFile)
             
        return stringFile
        
    def CorrectAllFunctions(self,tab,filename):
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
            #tab_func_proto = re.findall(r'\w*\s*\w+\s+(\w+)\s*\(\s*[\w\s,\*\[\]]+[\s]*[)][\s]*\;{1}',line)      
            tab_func_proto = re.findall(r'\w*\s*\w+\s+\**\s*(\w+)\s*\([\w+\s*\,\*\[\]]+\)\s*\;',line)      
            
            if len(tab_func_proto)>0:
                if isVerbose == True:
                    print("^Correction in ^prototype ",tab_func_proto)
                
                
                
                if ".h" in filename:
                    if tab_func_proto[0] in AllFunctionsToAddExtern:
                        print("\t--------------->>>>>> adding extern in h to ",tab_func_proto[0])
                        line = "extern "+line
                    
                
                
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
                if isVerbose == True:
                    print("^Correction in ^declaration ",tab_func_declaration)
                # print(line)
                local_var_tab_dict ={}
                tab_potential_local_var = re.findall(r'([\w]+[\s]+[\*]*[\s]*[\w]+)[\s]*[\=\;]{1}',line)
                if isVerbose == True:
                    print("^*^ ", tab_potential_local_var )
                for possible in tab_potential_local_var:  
                    for typet in AllAnalysedVariableTypes_dict.keys():
                        if typet in possible:
                            if isVerbose == True:
                                print(typet, " in ",possible)
                            #var = self.FindVariableinDefinition(possible)
                            new_var, var = self.CheckDataSuffixforVariable(possible)
                            new_var, aaa= self.CheckIfPrefixInInstanceChange(new_var)
                            local_var_tab_dict[var] = new_var
                            if isVerbose == True:
                                print(" &&new var ",new_var," var ",var)
                            line=re.sub(r'\b'+var+r'\b',new_var,line)            
                            #input(" key ")
                            break
                            
                
                        
                        
                if tab_func_declaration[0] in AllFunctionArgument.keys():
                    dict_toChange = AllFunctionArgument[tab_func_declaration[0]]
                    
                    for key in dict_toChange:
                        if isVerbose == True:
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
    
    def  SaveString(self,filename, string):
        file=open(filename,"w")
        
        file.write(string)
        
        file.close()
    
    
    def FindAllIfStatement(self,tab,comparising):
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

    def FindAllComments(self,string):       
        tab_statement = re.findall(r'(?:(?:\/\/){1}[\S\s]+?\n)|(?:(?:\/\*){1}[\s\w\d\S]+?(?:\*\/){1})',string)    
            
        return tab_statement 
        
        
    def  AddNewLineToAllArray(self, tab ):
        for i in range(0,len(tab)):
            tab[i] +="\n"
        return tab
            
            
        

#############################################################################    

#NOT USED

    def FindAllTypedef_regexp(self,string):
        tab_typedef_enum = re.findall(r'typedef[\s]+enum[\s]*\{[\s\S]+?\}\s*([\w]+);',string)
        print(" typedef enum types ",tab_typedef_enum)
        
        for type_enum in tab_typedef_enum:
            new_type_name, old = self.AddPrefixToVariable(type_enum,"_t")
            if new_type_name!= type_enum:
                self.dict_of_Variables_to_change[type_enum]=new_type_name
            AllAnalysedVariableTypes_dict[type_enum]="_e"
        
        for type1 in tab:
            new_type_name, string = self.AddPrefixToVariable(type1,"_t")
            if new_type_name!= type1:
                self.dict_of_Variables_to_change[type1]=new_type_name        
        #this doesnt work too good bc if we have struct inside of typedef it will finish on that definition        
        tab_typedef= re.findall(r'typedef[\s]+(?:(?!enum)\w+)[\s]+\{[\s\S]+?\}\s*([\w]+)\;',string)        
        print(" typedef struct types ",tab_typedef)
        tab_typedef_simple= re.findall(r'typedef[\s]+[\s\w\*\(\)\[\]]+?([\w]+)\s*\;',string)
        print(" typedef non-struct types ",tab_typedef_simple)        
        tab = tab_typedef_enum + tab_typedef_simple + tab_typedef
        self.AllTypeDefArray += tab
        
#############################################################################    

#NOT USED
  
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
                
                new_var,old_name  = self.AddPrefixToVariable(var,"_t")
                if new_var != var:
                    self.dict_of_Variables_to_change[var]=new_var
            
                self.nr_line +=1
                continue
            
            self.nr_line +=1
            
    
  
  
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
    global isVerbose
    global MODULE_PREFIX
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
    isVerbose = False
    
    for arguments in sys.argv:
        arguments = arguments.strip()
        
        if "dir=" in arguments:
            line_tab = arguments.split("=")
            DIRECTORY = line_tab[1]
        elif "file=" in arguments:
            line_tab = arguments.split("=")
            tabOfAnalyzedFiles.append(line_tab[1])
            
        elif "-v" == arguments:
            isVerbose = True
        
        elif "prefix=" in arguments:
            line_tab = arguments.split("=")
            MODULE_PREFIX = line_tab[1]
    
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
            
            
            analyze = ClassToAnalyseCfile(filename)  
            
            print("$"*100)
            print("$"*100)
            print("$"*100)
            print("\n"," "*15," ALL INCLUDES ANALYSiS ")
            
            analyze.AnalyzeAllIncludes(analyze.StringAllLinesWithoutComment)    
            #analyze.ShowAllVariablesToChange()
            #input(" key ")
            
            print("$"*100)
            print("$"*100)
            print("\n"," "*15,"END  ALL INCLUDES ANALYSiS ")
            print("$"*100)
            print("\n"*10)
            print("$"*100)
            print("$"*100)
            print(" "*10," ANALYSIS of ",filename)
            print("$"*100)
            print("$"*100,"\n"*2)
            
            
            analyze.SaveString(filename+"_WC",analyze.StringAllLinesWithoutComment)
            
            #string_WC2 = analyze.FindAllTypedef_enum_nonstruct(string_WC)
            #string_WC2 = analyze.FindAllTypedefStruct_regexp(string_WC2)    
            #analyze.FindAllFunctionPrototype(string_WC2,filename)
            
            print(" all typedef ",analyze.AllTypeDefArray)
            
            analyze.ShowAllVariablesToChange()
            #input(" key ")
            
            
            #analyze.FindAllTypedefVar()            
    
            #analyze.FindAllInstancesOfTypes(string_WC)            
            analyze.ShowAllVariablesToChange()

            
            tab = analyze.CorrectAllVariablesNames(analyze.tab_c)
            tab = analyze.CorrectAllFunctions(tab,filename)
            
            string_all = analyze.ChangeArrayToString(tab)
            string1 = analyze.CorrectAllPrefix(string_all)
            # inc.SaveAllTab(filename+"_ch", tab)
            analyze.SaveString(filename+"_ch",string1)
            
            
            analyze.FindAllIfStatement(tab,"==")
            analyze.FindAllIfStatement(tab,"!=")            
            
            
            
            
            #tab_comments = analyze.AddNewLineToAllArray(analyze.tab_all_comments)
            #print(tab_comments)
            tab_comments = analyze.AddNewLineToAllArray(analyze.tab_all_comments)
            
            analyze.SaveAllTab(filename+"_comments", tab_comments)
            
            # analyze.SaveAllTab(filename+"_ch", tab)            
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
    
    
    print("\n"*10," all analyzed pointers variables ")    
    for key in analyze.AllPointers.keys():
        print(key,"\t -> ",analyze.AllPointers[key])
    
    print("\n"*10," all analyzed ARRAYS variables ")    
    for key in analyze.AllArrays.keys():
        print(key,"\t -> ",analyze.AllArrays[key])
    
    print(AllArrays)
if __name__ == '__main__':
    main()