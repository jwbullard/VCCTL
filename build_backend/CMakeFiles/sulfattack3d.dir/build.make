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
include CMakeFiles/sulfattack3d.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/sulfattack3d.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/sulfattack3d.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/sulfattack3d.dir/flags.make

CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.o: CMakeFiles/sulfattack3d.dir/flags.make
CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.o: /Users/jwbullard/Software/MyProjects/VCCTL/backend/sulfattack3d.c
CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.o: CMakeFiles/sulfattack3d.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/Users/jwbullard/Software/MyProjects/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building C object CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.o"
	/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -MD -MT CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.o -MF CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.o.d -o CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.o -c /Users/jwbullard/Software/MyProjects/VCCTL/backend/sulfattack3d.c

CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.i"
	/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /Users/jwbullard/Software/MyProjects/VCCTL/backend/sulfattack3d.c > CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.i

CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.s"
	/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /Users/jwbullard/Software/MyProjects/VCCTL/backend/sulfattack3d.c -o CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.s

# Object files for target sulfattack3d
sulfattack3d_OBJECTS = \
"CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.o"

# External object files for target sulfattack3d
sulfattack3d_EXTERNAL_OBJECTS =

sulfattack3d: CMakeFiles/sulfattack3d.dir/backend/sulfattack3d.c.o
sulfattack3d: CMakeFiles/sulfattack3d.dir/build.make
sulfattack3d: backend/vcctllib/libvcctl.a
sulfattack3d: /Users/jwbullard/Software/MyProjects/VCCTL/lib/libpng.a
sulfattack3d: /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.2.sdk/usr/lib/libm.tbd
sulfattack3d: /Users/jwbullard/Software/MyProjects/VCCTL/lib/libz.dylib
sulfattack3d: CMakeFiles/sulfattack3d.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/Users/jwbullard/Software/MyProjects/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking C executable sulfattack3d"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/sulfattack3d.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/sulfattack3d.dir/build: sulfattack3d
.PHONY : CMakeFiles/sulfattack3d.dir/build

CMakeFiles/sulfattack3d.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/sulfattack3d.dir/cmake_clean.cmake
.PHONY : CMakeFiles/sulfattack3d.dir/clean

CMakeFiles/sulfattack3d.dir/depend:
	cd /Users/jwbullard/Software/MyProjects/VCCTL/build_backend && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/jwbullard/Software/MyProjects/VCCTL /Users/jwbullard/Software/MyProjects/VCCTL /Users/jwbullard/Software/MyProjects/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/VCCTL/build_backend/CMakeFiles/sulfattack3d.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/sulfattack3d.dir/depend

