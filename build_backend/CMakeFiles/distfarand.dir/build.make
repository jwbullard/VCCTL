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
include CMakeFiles/distfarand.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/distfarand.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/distfarand.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/distfarand.dir/flags.make

CMakeFiles/distfarand.dir/backend/distfarand.c.o: CMakeFiles/distfarand.dir/flags.make
CMakeFiles/distfarand.dir/backend/distfarand.c.o: /Users/jwbullard/Software/MyProjects/VCCTL/backend/distfarand.c
CMakeFiles/distfarand.dir/backend/distfarand.c.o: CMakeFiles/distfarand.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/Users/jwbullard/Software/MyProjects/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building C object CMakeFiles/distfarand.dir/backend/distfarand.c.o"
	/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -MD -MT CMakeFiles/distfarand.dir/backend/distfarand.c.o -MF CMakeFiles/distfarand.dir/backend/distfarand.c.o.d -o CMakeFiles/distfarand.dir/backend/distfarand.c.o -c /Users/jwbullard/Software/MyProjects/VCCTL/backend/distfarand.c

CMakeFiles/distfarand.dir/backend/distfarand.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/distfarand.dir/backend/distfarand.c.i"
	/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /Users/jwbullard/Software/MyProjects/VCCTL/backend/distfarand.c > CMakeFiles/distfarand.dir/backend/distfarand.c.i

CMakeFiles/distfarand.dir/backend/distfarand.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/distfarand.dir/backend/distfarand.c.s"
	/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /Users/jwbullard/Software/MyProjects/VCCTL/backend/distfarand.c -o CMakeFiles/distfarand.dir/backend/distfarand.c.s

# Object files for target distfarand
distfarand_OBJECTS = \
"CMakeFiles/distfarand.dir/backend/distfarand.c.o"

# External object files for target distfarand
distfarand_EXTERNAL_OBJECTS =

distfarand: CMakeFiles/distfarand.dir/backend/distfarand.c.o
distfarand: CMakeFiles/distfarand.dir/build.make
distfarand: backend/vcctllib/libvcctl.a
distfarand: /Users/jwbullard/Software/MyProjects/VCCTL/lib/libpng.a
distfarand: /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.2.sdk/usr/lib/libm.tbd
distfarand: /Users/jwbullard/Software/MyProjects/VCCTL/lib/libz.dylib
distfarand: CMakeFiles/distfarand.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/Users/jwbullard/Software/MyProjects/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking C executable distfarand"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/distfarand.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/distfarand.dir/build: distfarand
.PHONY : CMakeFiles/distfarand.dir/build

CMakeFiles/distfarand.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/distfarand.dir/cmake_clean.cmake
.PHONY : CMakeFiles/distfarand.dir/clean

CMakeFiles/distfarand.dir/depend:
	cd /Users/jwbullard/Software/MyProjects/VCCTL/build_backend && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/jwbullard/Software/MyProjects/VCCTL /Users/jwbullard/Software/MyProjects/VCCTL /Users/jwbullard/Software/MyProjects/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/VCCTL/build_backend/CMakeFiles/distfarand.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/distfarand.dir/depend

