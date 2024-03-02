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
CMAKE_SOURCE_DIR = /Users/jwbullard/Software/MyProjects/git/VCCTL

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend

# Include any dependencies generated for this target.
include CMakeFiles/measagg.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/measagg.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/measagg.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/measagg.dir/flags.make

CMakeFiles/measagg.dir/backend/measagg.c.o: CMakeFiles/measagg.dir/flags.make
CMakeFiles/measagg.dir/backend/measagg.c.o: /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/measagg.c
CMakeFiles/measagg.dir/backend/measagg.c.o: CMakeFiles/measagg.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building C object CMakeFiles/measagg.dir/backend/measagg.c.o"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -MD -MT CMakeFiles/measagg.dir/backend/measagg.c.o -MF CMakeFiles/measagg.dir/backend/measagg.c.o.d -o CMakeFiles/measagg.dir/backend/measagg.c.o -c /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/measagg.c

CMakeFiles/measagg.dir/backend/measagg.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/measagg.dir/backend/measagg.c.i"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/measagg.c > CMakeFiles/measagg.dir/backend/measagg.c.i

CMakeFiles/measagg.dir/backend/measagg.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/measagg.dir/backend/measagg.c.s"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/measagg.c -o CMakeFiles/measagg.dir/backend/measagg.c.s

# Object files for target measagg
measagg_OBJECTS = \
"CMakeFiles/measagg.dir/backend/measagg.c.o"

# External object files for target measagg
measagg_EXTERNAL_OBJECTS =

measagg: CMakeFiles/measagg.dir/backend/measagg.c.o
measagg: CMakeFiles/measagg.dir/build.make
measagg: backend/vcctllib/libvcctl.a
measagg: /Users/jwbullard/Software/MyProjects/git/VCCTL/lib/libpng.a
measagg: /Library/Developer/CommandLineTools/SDKs/MacOSX14.2.sdk/usr/lib/libm.tbd
measagg: /Users/jwbullard/Software/MyProjects/git/VCCTL/lib/libz.dylib
measagg: CMakeFiles/measagg.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking C executable measagg"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/measagg.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/measagg.dir/build: measagg
.PHONY : CMakeFiles/measagg.dir/build

CMakeFiles/measagg.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/measagg.dir/cmake_clean.cmake
.PHONY : CMakeFiles/measagg.dir/clean

CMakeFiles/measagg.dir/depend:
	cd /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/jwbullard/Software/MyProjects/git/VCCTL /Users/jwbullard/Software/MyProjects/git/VCCTL /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend/CMakeFiles/measagg.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/measagg.dir/depend

