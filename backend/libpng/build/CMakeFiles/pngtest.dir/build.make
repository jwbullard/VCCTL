# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.24

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:

#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:

# Disable VCS-based implicit rules.
% : %,v

# Disable VCS-based implicit rules.
% : RCS/%

# Disable VCS-based implicit rules.
% : RCS/%,v

# Disable VCS-based implicit rules.
% : SCCS/s.%

# Disable VCS-based implicit rules.
% : s.%

.SUFFIXES: .hpux_make_needs_suffix_list

# Command-line flag to silence nested $(MAKE).
$(VERBOSE)MAKESILENT = -s

#Suppress display of executed commands.
$(VERBOSE).SILENT:

# A target that is always out of date.
cmake_force:
.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /opt/local/bin/cmake

# The command to remove a file.
RM = /opt/local/bin/cmake -E rm -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build

# Include any dependencies generated for this target.
include CMakeFiles/pngtest.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/pngtest.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/pngtest.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/pngtest.dir/flags.make

CMakeFiles/pngtest.dir/pngtest.c.o: CMakeFiles/pngtest.dir/flags.make
CMakeFiles/pngtest.dir/pngtest.c.o: /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/pngtest.c
CMakeFiles/pngtest.dir/pngtest.c.o: CMakeFiles/pngtest.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building C object CMakeFiles/pngtest.dir/pngtest.c.o"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -MD -MT CMakeFiles/pngtest.dir/pngtest.c.o -MF CMakeFiles/pngtest.dir/pngtest.c.o.d -o CMakeFiles/pngtest.dir/pngtest.c.o -c /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/pngtest.c

CMakeFiles/pngtest.dir/pngtest.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/pngtest.dir/pngtest.c.i"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/pngtest.c > CMakeFiles/pngtest.dir/pngtest.c.i

CMakeFiles/pngtest.dir/pngtest.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/pngtest.dir/pngtest.c.s"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/pngtest.c -o CMakeFiles/pngtest.dir/pngtest.c.s

# Object files for target pngtest
pngtest_OBJECTS = \
"CMakeFiles/pngtest.dir/pngtest.c.o"

# External object files for target pngtest
pngtest_EXTERNAL_OBJECTS =

pngtest: CMakeFiles/pngtest.dir/pngtest.c.o
pngtest: CMakeFiles/pngtest.dir/build.make
pngtest: libpng16.16.44.git.dylib
pngtest: /Users/jwbullard/Software/MyProjects/git/VCCTL/lib/libz.dylib
pngtest: CMakeFiles/pngtest.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking C executable pngtest"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/pngtest.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/pngtest.dir/build: pngtest
.PHONY : CMakeFiles/pngtest.dir/build

CMakeFiles/pngtest.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/pngtest.dir/cmake_clean.cmake
.PHONY : CMakeFiles/pngtest.dir/clean

CMakeFiles/pngtest.dir/depend:
	cd /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/CMakeFiles/pngtest.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/pngtest.dir/depend
