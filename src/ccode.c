// TODO
//1.  Add method to check if function return same type variable as in declaration
//2.  Add method to check function header and creating one if no existing
//3. 


//to find all function declaration
//[\w]+[\s]+([\w])+[\s]*[(][\w\s,\*\[\]]+[)][\s]*;{1,}$

//to find definition
//[\w]+[\s]+([\w])+[\s]*[(][\w\s,\*\[\]]+[)][\s]*{{1,}$


#include <stdio.h>

char * VERSION = "1.10.8";
char * DIRECTORY="";
char * START_COMMENT_BLOCK = "/*";
char * END_COMMENT_BLOCK= "*/";
// Options_d = {}
// Options_d["prefix"]   =   "Edr"
// Options_d["function"] =   "global"

//   if #include or #define there is no need for ; or {}
// all comments are remove during c-file analysis

int HOW_MANY_LETTERS_FROM_WORD_END = 4;
char * POINTER_PREFIX="_p";
char * ARRAY_PREFIX = "_a";



typedef struct _AllAnanlyzedVariable_t 
{
    char * keyword;
    char * type_suffix;

} AllAnalyzedVariable_t;

AllAnalyzedVariable_t  AllAnalysedVariableTypes_dict[] = {
    {"typedef",          "_t"},
    {"uint8_t",          "_u8"},
    {"uint8",            "_u8"}, 
    {" int8_t",          "_i8"},
    {" int8",            "_i8"},
    {"uint16_t",         "_u16"},
    {"uint16",           "_u16"},
    {" int16_t",         "_i16"},
    {" int16",           "_i16"},
    {"uint32_t",         "_u32"},
    {"uint32",           "_u32"},
    {" int32_t",         "_i32"},
    {" int32",           "_i32"},
    {"boolean_t",        "_bo"},
    {"bool_t",           "_bo"},
    {"void",             ""},
};


char * AllEquality_tab[] = {
    "=",
    "!",
    " "
};

char * WordWithoutEndingCharacters[] = {
    "#include",
    "#define",
    "#pragma",
    "#ifndef",
    "#endif",
    "#if",
    "#error",
    "#elif",
    
};

//here I have symbols which are used to know that line is finished
char * FinishMarkers[]  = {
    ";",    
    "{",
    "\\"
};

char * SignNotForWord[] = {
    ";",
    "{",
    "}",
    "]",
    "[",
    ",",
    "="
};



int main(int argc, char ** argv)
{

    return 0;
}