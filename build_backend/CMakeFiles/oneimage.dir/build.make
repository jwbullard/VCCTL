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
include CMakeFiles/oneimage.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/oneimage.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/oneimage.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/oneimage.dir/flags.make

CMakeFiles/oneimage.dir/backend/oneimage.c.o: CMakeFiles/oneimage.dir/flags.make
CMakeFiles/oneimage.dir/backend/oneimage.c.o: /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/oneimage.c
CMakeFiles/oneimage.dir/backend/oneimage.c.o: CMakeFiles/oneimage.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building C object CMakeFiles/oneimage.dir/backend/oneimage.c.o"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -MD -MT CMakeFiles/oneimage.dir/backend/oneimage.c.o -MF CMakeFiles/oneimage.dir/backend/oneimage.c.o.d -o CMakeFiles/oneimage.dir/backend/oneimage.c.o -c /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/oneimage.c

CMakeFiles/oneimage.dir/backend/oneimage.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/oneimage.dir/backend/oneimage.c.i"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/oneimage.c > CMakeFiles/oneimage.dir/backend/oneimage.c.i

CMakeFiles/oneimage.dir/backend/oneimage.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/oneimage.dir/backend/oneimage.c.s"
	/Library/Developer/CommandLineTools/usr/bin/gcc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/oneimage.c -o CMakeFiles/oneimage.dir/backend/oneimage.c.s

# Object files for target oneimage
oneimage_OBJECTS = \
"CMakeFiles/oneimage.dir/backend/oneimage.c.o"

# External object files for target oneimage
oneimage_EXTERNAL_OBJECTS =

oneimage: CMakeFiles/oneimage.dir/backend/oneimage.c.o
oneimage: CMakeFiles/oneimage.dir/build.make
oneimage: backend/vcctllib/libvcctl.a
oneimage: /Users/jwbullard/Software/MyProjects/git/VCCTL/lib/libpng.a
oneimage: /Library/Developer/CommandLineTools/SDKs/MacOSX14.2.sdk/usr/lib/libm.tbd
oneimage: /Users/jwbullard/Software/MyProjects/git/VCCTL/lib/libz.dylib
oneimage: CMakeFiles/oneimage.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking C executable oneimage"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/oneimage.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/oneimage.dir/build: oneimage
.PHONY : CMakeFiles/oneimage.dir/build

CMakeFiles/oneimage.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/oneimage.dir/cmake_clean.cmake
.PHONY : CMakeFiles/oneimage.dir/clean

CMakeFiles/oneimage.dir/depend:
	cd /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/jwbullard/Software/MyProjects/git/VCCTL /Users/jwbullard/Software/MyProjects/git/VCCTL /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/git/VCCTL/build_backend/CMakeFiles/oneimage.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/oneimage.dir/depend

