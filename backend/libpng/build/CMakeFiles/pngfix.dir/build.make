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
include CMakeFiles/pngfix.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/pngfix.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/pngfix.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/pngfix.dir/flags.make

CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.o: CMakeFiles/pngfix.dir/flags.make
CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.o: /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/contrib/tools/pngfix.c
CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.o: CMakeFiles/pngfix.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building C object CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.o"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -MD -MT CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.o -MF CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.o.d -o CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.o -c /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/contrib/tools/pngfix.c

CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.i"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/contrib/tools/pngfix.c > CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.i

CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.s"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/contrib/tools/pngfix.c -o CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.s

# Object files for target pngfix
pngfix_OBJECTS = \
"CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.o"

# External object files for target pngfix
pngfix_EXTERNAL_OBJECTS =

pngfix: CMakeFiles/pngfix.dir/contrib/tools/pngfix.c.o
pngfix: CMakeFiles/pngfix.dir/build.make
pngfix: libpng16.16.44.git.dylib
pngfix: /Users/jwbullard/Software/MyProjects/git/VCCTL/lib/libz.dylib
pngfix: CMakeFiles/pngfix.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking C executable pngfix"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/pngfix.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/pngfix.dir/build: pngfix
.PHONY : CMakeFiles/pngfix.dir/build

CMakeFiles/pngfix.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/pngfix.dir/cmake_clean.cmake
.PHONY : CMakeFiles/pngfix.dir/clean

CMakeFiles/pngfix.dir/depend:
	cd /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/CMakeFiles/pngfix.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/pngfix.dir/depend
