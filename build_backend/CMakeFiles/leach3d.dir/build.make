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
CMAKE_SOURCE_DIR = /Users/jwbullard/Software/MyProjects/VCCTL

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /Users/jwbullard/Software/MyProjects/VCCTL/build_backend

# Include any dependencies generated for this target.
include CMakeFiles/leach3d.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/leach3d.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/leach3d.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/leach3d.dir/flags.make

CMakeFiles/leach3d.dir/backend/leach3d.c.o: CMakeFiles/leach3d.dir/flags.make
CMakeFiles/leach3d.dir/backend/leach3d.c.o: /Users/jwbullard/Software/MyProjects/VCCTL/backend/leach3d.c
CMakeFiles/leach3d.dir/backend/leach3d.c.o: CMakeFiles/leach3d.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/Users/jwbullard/Software/MyProjects/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building C object CMakeFiles/leach3d.dir/backend/leach3d.c.o"
	/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -MD -MT CMakeFiles/leach3d.dir/backend/leach3d.c.o -MF CMakeFiles/leach3d.dir/backend/leach3d.c.o.d -o CMakeFiles/leach3d.dir/backend/leach3d.c.o -c /Users/jwbullard/Software/MyProjects/VCCTL/backend/leach3d.c

CMakeFiles/leach3d.dir/backend/leach3d.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/leach3d.dir/backend/leach3d.c.i"
	/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /Users/jwbullard/Software/MyProjects/VCCTL/backend/leach3d.c > CMakeFiles/leach3d.dir/backend/leach3d.c.i

CMakeFiles/leach3d.dir/backend/leach3d.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/leach3d.dir/backend/leach3d.c.s"
	/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /Users/jwbullard/Software/MyProjects/VCCTL/backend/leach3d.c -o CMakeFiles/leach3d.dir/backend/leach3d.c.s

# Object files for target leach3d
leach3d_OBJECTS = \
"CMakeFiles/leach3d.dir/backend/leach3d.c.o"

# External object files for target leach3d
leach3d_EXTERNAL_OBJECTS =

leach3d: CMakeFiles/leach3d.dir/backend/leach3d.c.o
leach3d: CMakeFiles/leach3d.dir/build.make
leach3d: backend/vcctllib/libvcctl.a
leach3d: /Users/jwbullard/Software/MyProjects/VCCTL/lib/libpng.a
leach3d: /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.2.sdk/usr/lib/libm.tbd
leach3d: /Users/jwbullard/Software/MyProjects/VCCTL/lib/libz.dylib
leach3d: CMakeFiles/leach3d.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/Users/jwbullard/Software/MyProjects/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking C executable leach3d"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/leach3d.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/leach3d.dir/build: leach3d
.PHONY : CMakeFiles/leach3d.dir/build

CMakeFiles/leach3d.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/leach3d.dir/cmake_clean.cmake
.PHONY : CMakeFiles/leach3d.dir/clean

CMakeFiles/leach3d.dir/depend:
	cd /Users/jwbullard/Software/MyProjects/VCCTL/build_backend && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/jwbullard/Software/MyProjects/VCCTL /Users/jwbullard/Software/MyProjects/VCCTL /Users/jwbullard/Software/MyProjects/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/VCCTL/build_backend/CMakeFiles/leach3d.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/leach3d.dir/depend

