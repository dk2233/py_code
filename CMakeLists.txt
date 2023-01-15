cmake_minimum_required(VERSION 3.16.3)

project(ccode)

set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

set(CMAKE_CXX_COMPILER gcc)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_BUILD_TYPE Debug)

include(GNUInstallDirs)

include_directories(
    c_arg_parse
    )

#add_subdirectory(arrays)


add_executable(ccode  
    deps/console-colors/console-colors.c
    c_arg_parse/arg_parse.c
    src/arg_config.c
    src/ccode.c
    src/tools.c
   )
    
#target_include_directories(ctests 
#    $(CMAKE_CURRENT_LIST_DIR))

target_link_libraries(ccode -Wall -Wextra)
 

