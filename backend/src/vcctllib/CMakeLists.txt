cmake_minimum_required(VERSION 3.30)

project (VcctlLibrary_project)

file (GLOB SOURCES "${CMAKE_SOURCE_DIR}/src/vcctllib/*.c")

#find_package (LibXml2)
#if (LIBXML2_FOUND)
#    include_directories(${LIBXML2_INCLUDE_DIR})
#    message ("Found libxml2 include files at " ${LIBXML2_INCLUDE_DIR})
#    message ("libxml2 libraries are " ${LIBXML2_LIBRARIES})
#    set (EXTRA_LIBS ${EXTRA_LIBS} ${LIBXML2_LIBRARIES})
#    set (XML_INCLUDE_PATH "-I${LIBXML2_INCLUDE_DIR}")
#else (LIBXML2_FOUND)
#    message (FATAL_ERROR "Library libxml not installed on system.  Please install it first.")
#endif (LIBXML2_FOUND)

#set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${XML_INCLUDE_PATH}")

message ("VCCTL lib directory, CMAKE_C_FLAGS: " ${CMAKE_C_FLAGS})

add_library (vcctl STATIC ${SOURCES})

# target_link_libraries(vcctl ${EXTRA_LIBS})
target_link_libraries(vcctl)

install (TARGETS vcctl DESTINATION ${CMAKE_SOURCE_DIR}/lib)

