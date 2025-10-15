cmake_minimum_required(VERSION 3.26)

project (VCCTL)

set (VCCTL_VERSION 10.0.0)
set (VCCTL_VERSION_MAJOR 10)
set (VCCTL_VERSION_MINOR 0.0)

# Use find_package for vcpkg-managed libraries
find_package(PNG REQUIRED)
find_package(ZLIB REQUIRED)

# getopt library - MSVC only (Unix and MinGW have it built-in)
if(MSVC)
    find_package(unofficial-getopt-win32 REQUIRED)
    set(EXTRA_LIBS ${EXTRA_LIBS} unofficial::getopt-win32::getopt)
endif()

# Math library handling - not needed on MSVC, required on Unix and MinGW
if(NOT MSVC)
    find_library(MATH_LIB NAMES m libm HINTS "/usr/lib" "/c/msys64/mingw64/lib")
    if(MATH_LIB)
        message("Found MATH_LIB: [${MATH_LIB}]")
        set(EXTRA_LIBS ${EXTRA_LIBS} ${MATH_LIB})
    else()
        message(WARNING "Did not find MATH lib - continuing without it")
    endif()
endif()

# Set up library list
set(EXTRA_LIBS ${EXTRA_LIBS} PNG::PNG ZLIB::ZLIB)
message("EXTRA_LIBS: " ${EXTRA_LIBS})

# Use include_directories instead of manual -I flags to handle special characters in paths
# Note: PNG/ZLIB headers come from vcpkg on MSVC, MinGW and Unix need custom include paths
if(NOT MSVC)
    include_directories("${CMAKE_SOURCE_DIR}/include")
    include_directories("${CMAKE_SOURCE_DIR}/src/include")
    if(UNIX)
        include_directories("/usr/local/include")
    endif()
endif()

# Platform-specific compiler flags
if(MSVC)
    set(CMAKE_C_FLAGS "/O2")
else()
    set(CMAKE_C_FLAGS "-O2")
endif()

message ("Top level CMAKE_C_FLAGS: " ${CMAKE_C_FLAGS})
message ("Linked libraries are: " ${EXTRA_LIBS})

add_subdirectory (${CMAKE_SOURCE_DIR}/src/vcctllib)

# file (GLOB SOURCES "${CMAKE_SOURCE_DIR}/src/*.c")

add_executable (aggvrml ${CMAKE_SOURCE_DIR}/src/aggvrml.c)
target_link_libraries (aggvrml vcctl ${EXTRA_LIBS})

add_executable (apstats ${CMAKE_SOURCE_DIR}/src/apstats.c)
target_link_libraries (apstats vcctl ${EXTRA_LIBS})

add_executable (chlorattack3d ${CMAKE_SOURCE_DIR}/src/chlorattack3d.c)
target_link_libraries (chlorattack3d vcctl ${EXTRA_LIBS})

add_executable (distfapart ${CMAKE_SOURCE_DIR}/src/distfapart.c)
target_link_libraries (distfapart vcctl ${EXTRA_LIBS})

add_executable (distfarand ${CMAKE_SOURCE_DIR}/src/distfarand.c)
target_link_libraries (distfarand vcctl ${EXTRA_LIBS})

add_executable (dryout ${CMAKE_SOURCE_DIR}/src/dryout.c)
target_link_libraries (dryout vcctl ${EXTRA_LIBS})

add_executable (elastic ${CMAKE_SOURCE_DIR}/src/elastic.c)
target_link_libraries (elastic vcctl ${EXTRA_LIBS})

add_executable (genaggpack ${CMAKE_SOURCE_DIR}/src/genaggpack.c)
target_link_libraries (genaggpack vcctl ${EXTRA_LIBS})

add_executable (genmic ${CMAKE_SOURCE_DIR}/src/genmic.c)
target_link_libraries (genmic vcctl ${EXTRA_LIBS})

add_executable (hydmovie ${CMAKE_SOURCE_DIR}/src/hydmovie.c)
target_link_libraries (hydmovie vcctl ${EXTRA_LIBS})

add_executable (image100 ${CMAKE_SOURCE_DIR}/src/image100.c)
target_link_libraries (image100 vcctl ${EXTRA_LIBS})

add_executable (leach3d ${CMAKE_SOURCE_DIR}/src/leach3d.c)
target_link_libraries (leach3d vcctl ${EXTRA_LIBS})

add_executable (measagg ${CMAKE_SOURCE_DIR}/src/measagg.c)
target_link_libraries (measagg vcctl ${EXTRA_LIBS})

add_executable (oneimage ${CMAKE_SOURCE_DIR}/src/oneimage.c)
target_link_libraries (oneimage vcctl ${EXTRA_LIBS})

add_executable (onepimage ${CMAKE_SOURCE_DIR}/src/onepimage.c)
target_link_libraries (onepimage vcctl ${EXTRA_LIBS})

add_executable (perc3d ${CMAKE_SOURCE_DIR}/src/perc3d.c)
target_link_libraries (perc3d vcctl ${EXTRA_LIBS})

add_executable (perc3d-leach ${CMAKE_SOURCE_DIR}/src/perc3d-leach.c)
target_link_libraries (perc3d-leach vcctl ${EXTRA_LIBS})

add_executable (poredist3d ${CMAKE_SOURCE_DIR}/src/poredist3d.c)
target_link_libraries (poredist3d vcctl ${EXTRA_LIBS})

add_executable (rand3d ${CMAKE_SOURCE_DIR}/src/rand3d.c)
target_link_libraries (rand3d vcctl ${EXTRA_LIBS})

add_executable (stat3d ${CMAKE_SOURCE_DIR}/src/stat3d.c)
target_link_libraries (stat3d vcctl ${EXTRA_LIBS})

add_executable (totsurf ${CMAKE_SOURCE_DIR}/src/totsurf.c)
target_link_libraries (totsurf vcctl ${EXTRA_LIBS})

add_executable (sulfattack3d ${CMAKE_SOURCE_DIR}/src/sulfattack3d.c)
target_link_libraries (sulfattack3d vcctl ${EXTRA_LIBS})

add_executable (transport ${CMAKE_SOURCE_DIR}/src/transport.c)
target_link_libraries (transport vcctl ${EXTRA_LIBS})

add_executable (thames2vcctl ${CMAKE_SOURCE_DIR}/src/thames2vcctl.c)
target_link_libraries (thames2vcctl vcctl ${EXTRA_LIBS})

add_executable (thames2vcctlcorr ${CMAKE_SOURCE_DIR}/src/thames2vcctlcorr.c)
target_link_libraries (thames2vcctlcorr vcctl ${EXTRA_LIBS})

set (DISREALNEWSOURCES "${CMAKE_SOURCE_DIR}/src/disrealnew.c")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/src/disrealnew.h")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/src/include/properties.h")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/src/include/burn3d.h")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/src/include/burnset.h")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/src/include/parthyd.h")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/src/include/hydrealnew.h")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/src/include/pHpred.h")

add_executable (disrealnew ${DISREALNEWSOURCES})
target_link_libraries (disrealnew vcctl ${EXTRA_LIBS})

set (EXECS "apstats aggvrml chlorattack3d distfapart distfarand ")
set (EXECS ${EXECS} "dryout elastic genaggpack genmic hydmovie ")
set (EXECS ${EXECS} "image100 leach3d measagg oneimage onepimage ")
set (EXECS ${EXECS} "perc3d perc3d-leach poredist3d rand3d ")
set (EXECS ${EXECS} "stat3d totsurf sulfattack3d transport ")
set (EXECS ${EXECS} "thames2vcctl thames2vcctlcorr")

#install (TARGETS ${EXECS} DESTINATION ${CMAKE_SOURCE_DIR}/bin)
