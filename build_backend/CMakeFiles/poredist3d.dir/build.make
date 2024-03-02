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
include CMakeFiles/poredist3d.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/poredist3d.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/poredist3d.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/poredist3d.dir/flags.make

CMakeFiles/poredist3d.dir/backend/poredist3d.c.o: CMakeFiles/poredist3d.dir/flags.make
CMakeFiles/poredist3d.dir/backend/poredist3d.c.o: /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/poredist3d.c
CMakeFiles/poredist3d.dir/backend/poredist3d.c.o: CMakeFiles/poredist3d.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building C object CMakeFiles/poredist3d.dir/backend/poredist3d.c.o"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -MD -MT CMakeFiles/poredist3d.dir/backend/poredist3d.c.o -MF CMakeFiles/poredist3d.dir/backend/poredist3d.c.o.d -o CMakeFiles/poredist3d.dir/backend/poredist3d.c.o -c /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/poredist3d.c

CMakeFiles/poredist3d.dir/backend/poredist3d.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/poredist3d.dir/backend/poredist3d.c.i"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/poredist3d.c > CMakeFiles/poredist3d.dir/backend/poredist3d.c.i

CMakeFiles/poredist3d.dir/backend/poredist3d.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/poredist3d.dir/backend/poredist3d.c.s"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/poredist3d.c -o CMakeFiles/poredist3d.dir/backend/poredist3d.c.s

# Object files for target poredist3d
poredist3d_OBJECTS = \
"CMakeFiles/poredist3d.dir/backend/poredist3d.c.o"

# External object files for target poredist3d
poredist3d_EXTERNAL_OBJECTS =

poredist3d: CMakeFiles/poredist3d.dir/backend/poredist3d.c.o
poredist3d: CMakeFiles/poredist3d.dir/build.make
poredist3d: backend/vcctllib/libvcctl.a
poredist3d: /Users/jwbullard/Software/MyProjects/git/VCCTL/lib/libpng.a
poredist3d: /Library/Developer/CommandLineTools/SDKs/MacOSX14.2.sdk/usr/lib/libm.tbd
poredist3d: /Users/jwbullard/Software/MyProjects/git/VCCTL/lib/libz.dylib
poredist3d: CMakeFiles/poredist3d.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking C executable poredist3d"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/poredist3d.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/poredist3d.dir/build: poredist3d
.PHONY : CMakeFiles/poredist3d.dir/build

CMakeFiles/poredist3d.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/poredist3d.dir/cmake_clean.cmake
.PHONY : CMakeFiles/poredist3d.dir/clean

CMakeFiles/poredist3d.dir/depend:
	cd /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/jwbullard/Software/MyProjects/git/VCCTL /Users/jwbullard/Software/MyProjects/git/VCCTL /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend/CMakeFiles/poredist3d.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/poredist3d.dir/depend

