
#include "arg_parse.h"
/*
such include may have function definitions*/
//#include "arg_functions.h"
#include <stdio.h>

extern void argument_cmdline(char * argv_parameter);



/* 
such specific array is needed to be created

name is important
also always leave one empty line*/
argument_config_t arg_config[] = {
    {"-o" , .function_to_parse.function_arg_array = argument_cmdline, "give an array size to be listed"},
    {"-o" , .function_to_parse.function_arg_array = argument_cmdline, "give an array size to be listed"},
    {"", NULL, NULL}, /* this line is a marker of last element*/

};
