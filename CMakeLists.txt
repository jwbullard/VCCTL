cmake_minimum_required(VERSION 3.7)

project (VCCTL)

set (VCCTL_VERSION 9.5)
set (VCCTL_VERSION_MAJOR 9)
set (VCCTL_VERSION_MINOR 5.5)

find_library (
    LIBPNG_LIB
    NAMES libpng libpng.a # what to look for
    HINTS "${CMAKE_SOURCE_DIR}/lib" # where to look
)

# check if we found the GEMS3K library
message(STATUS "LIBPNG_LIB: [${LIBPNG_LIB}]")

if (LIBPNG_LIB)
  message ("Found LIBPNG_LIB: [${LIBPNG_LIB}]")
  set (EXTRA_LIBS ${EXTRA_LIBS} ${LIBPNG_LIB})
  message ("EXTRA_LIBS: " ${EXTRA_LIBS})
else ()
    message (FATAL_ERROR "Did not find lib libpng")
endif ()

find_library (
    MATH_LIB
    NAMES m libm # what to look for
    HINTS "/usr/lib" # where to look
)

message(STATUS "MATH_LIB: [${MATH_LIB}]")

if (MATH_LIB)
    message ("Found MATH_LIB: [${MATH_LIB}]")
    set (EXTRA_LIBS ${EXTRA_LIBS} ${MATH_LIB})
else ()
    message (FATAL_ERROR "Did not find MATH lib")
endif ()

find_library (
    Z_LIB
    NAMES z libz libz.a # what to look for
    HINTS "${CMAKE_SOURCE_DIR}/lib" # where to look
)

message(STATUS "Z_LIB: [${Z_LIB}]")

if (Z_LIB)
    message ("Found Z_LIB: [${Z_LIB}]")
    set (EXTRA_LIBS ${EXTRA_LIBS} ${Z_LIB})
else ()
    message (FATAL_ERROR "Did not find Z lib")
endif ()

set (VCCTL_INCLUDE_PATH "-I${CMAKE_SOURCE_DIR}/include -I/usr/local/include")

set (CMAKE_C_FLAGS "-O2 ${VCCTL_INCLUDE_PATH}")

message ("Top level CMAKE_C_FLAGS: " ${CMAKE_C_FLAGS})
message ("Linked libraries are: " ${EXTRA_LIBS})

add_subdirectory (${CMAKE_SOURCE_DIR}/backend/vcctllib)

# file (GLOB SOURCES "${CMAKE_SOURCE_DIR}/backend/*.c")

add_executable (aggvrml ${CMAKE_SOURCE_DIR}/backend/aggvrml.c)
target_link_libraries (aggvrml vcctl ${EXTRA_LIBS})

add_executable (apstats ${CMAKE_SOURCE_DIR}/backend/apstats.c)
target_link_libraries (apstats vcctl ${EXTRA_LIBS})

add_executable (chlorattack3d ${CMAKE_SOURCE_DIR}/backend/chlorattack3d.c)
target_link_libraries (chlorattack3d vcctl ${EXTRA_LIBS})

add_executable (distfapart ${CMAKE_SOURCE_DIR}/backend/distfapart.c)
target_link_libraries (distfapart vcctl ${EXTRA_LIBS})

add_executable (distfarand ${CMAKE_SOURCE_DIR}/backend/distfarand.c)
target_link_libraries (distfarand vcctl ${EXTRA_LIBS})

add_executable (dryout ${CMAKE_SOURCE_DIR}/backend/dryout.c)
target_link_libraries (dryout vcctl ${EXTRA_LIBS})

add_executable (elastic ${CMAKE_SOURCE_DIR}/backend/elastic.c)
target_link_libraries (elastic vcctl ${EXTRA_LIBS})

add_executable (genaggpack ${CMAKE_SOURCE_DIR}/backend/genaggpack.c)
target_link_libraries (genaggpack vcctl ${EXTRA_LIBS})

add_executable (genmic ${CMAKE_SOURCE_DIR}/backend/genmic.c)
target_link_libraries (genmic vcctl ${EXTRA_LIBS})

add_executable (hydmovie ${CMAKE_SOURCE_DIR}/backend/hydmovie.c)
target_link_libraries (hydmovie vcctl ${EXTRA_LIBS})

add_executable (image100 ${CMAKE_SOURCE_DIR}/backend/image100.c)
target_link_libraries (image100 vcctl ${EXTRA_LIBS})

add_executable (leach3d ${CMAKE_SOURCE_DIR}/backend/leach3d.c)
target_link_libraries (leach3d vcctl ${EXTRA_LIBS})

add_executable (measagg ${CMAKE_SOURCE_DIR}/backend/measagg.c)
target_link_libraries (measagg vcctl ${EXTRA_LIBS})

add_executable (oneimage ${CMAKE_SOURCE_DIR}/backend/oneimage.c)
target_link_libraries (oneimage vcctl ${EXTRA_LIBS})

add_executable (onepimage ${CMAKE_SOURCE_DIR}/backend/onepimage.c)
target_link_libraries (onepimage vcctl ${EXTRA_LIBS})

add_executable (perc3d ${CMAKE_SOURCE_DIR}/backend/perc3d.c)
target_link_libraries (perc3d vcctl ${EXTRA_LIBS})

add_executable (perc3d-leach ${CMAKE_SOURCE_DIR}/backend/perc3d-leach.c)
target_link_libraries (perc3d-leach vcctl ${EXTRA_LIBS})

add_executable (poredist3d ${CMAKE_SOURCE_DIR}/backend/poredist3d.c)
target_link_libraries (poredist3d vcctl ${EXTRA_LIBS})

add_executable (rand3d ${CMAKE_SOURCE_DIR}/backend/rand3d.c)
target_link_libraries (rand3d vcctl ${EXTRA_LIBS})

add_executable (stat3d ${CMAKE_SOURCE_DIR}/backend/stat3d.c)
target_link_libraries (stat3d vcctl ${EXTRA_LIBS})

add_executable (totsurf ${CMAKE_SOURCE_DIR}/backend/totsurf.c)
target_link_libraries (totsurf vcctl ${EXTRA_LIBS})

add_executable (sulfattack3d ${CMAKE_SOURCE_DIR}/backend/sulfattack3d.c)
target_link_libraries (sulfattack3d vcctl ${EXTRA_LIBS})

add_executable (transport ${CMAKE_SOURCE_DIR}/backend/transport.c)
target_link_libraries (transport vcctl ${EXTRA_LIBS})

add_executable (thames2vcctl ${CMAKE_SOURCE_DIR}/backend/thames2vcctl.c)
target_link_libraries (thames2vcctl vcctl ${EXTRA_LIBS})

add_executable (thames2vcctlcorr ${CMAKE_SOURCE_DIR}/backend/thames2vcctlcorr.c)
target_link_libraries (thames2vcctlcorr vcctl ${EXTRA_LIBS})

set (DISREALNEWSOURCES "${CMAKE_SOURCE_DIR}/backend/disrealnew.c")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/backend/disrealnew.h")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/backend/include/properties.h")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/backend/include/burn3d.h")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/backend/include/burnset.h")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/backend/include/parthyd.h")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/backend/include/hydrealnew.h")
set (DISREALNEWSOURCES ${DISREALNEWSOURCES} "${CMAKE_SOURCE_DIR}/backend/include/pHpred.h")

add_executable (disrealnew ${DISREALNEWSOURCES})
target_link_libraries (disrealnew vcctl ${EXTRA_LIBS})

set (EXECS "apstats aggvrml chlorattack3d distfapart distfarand ")
set (EXECS ${EXECS} "dryout elastic genaggpack genmic hydmovie ")
set (EXECS ${EXECS} "image100 leach3d measagg oneimage onepimage ")
set (EXECS ${EXECS} "perc3d perc3d-leach poredist3d rand3d ")
set (EXECS ${EXECS} "stat3d totsurf sulfattack3d transport ")
set (EXECS ${EXECS} "thames2vcctl thames2vcctlcorr")

#install (TARGETS ${EXECS} DESTINATION ${CMAKE_SOURCE_DIR}/bin)
