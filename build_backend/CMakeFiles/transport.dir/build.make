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
include CMakeFiles/transport.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/transport.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/transport.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/transport.dir/flags.make

CMakeFiles/transport.dir/backend/transport.c.o: CMakeFiles/transport.dir/flags.make
CMakeFiles/transport.dir/backend/transport.c.o: /Users/jwbullard/Software/MyProjects/VCCTL/backend/transport.c
CMakeFiles/transport.dir/backend/transport.c.o: CMakeFiles/transport.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/Users/jwbullard/Software/MyProjects/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building C object CMakeFiles/transport.dir/backend/transport.c.o"
	/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -MD -MT CMakeFiles/transport.dir/backend/transport.c.o -MF CMakeFiles/transport.dir/backend/transport.c.o.d -o CMakeFiles/transport.dir/backend/transport.c.o -c /Users/jwbullard/Software/MyProjects/VCCTL/backend/transport.c

CMakeFiles/transport.dir/backend/transport.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/transport.dir/backend/transport.c.i"
	/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /Users/jwbullard/Software/MyProjects/VCCTL/backend/transport.c > CMakeFiles/transport.dir/backend/transport.c.i

CMakeFiles/transport.dir/backend/transport.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/transport.dir/backend/transport.c.s"
	/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /Users/jwbullard/Software/MyProjects/VCCTL/backend/transport.c -o CMakeFiles/transport.dir/backend/transport.c.s

# Object files for target transport
transport_OBJECTS = \
"CMakeFiles/transport.dir/backend/transport.c.o"

# External object files for target transport
transport_EXTERNAL_OBJECTS =

transport: CMakeFiles/transport.dir/backend/transport.c.o
transport: CMakeFiles/transport.dir/build.make
transport: backend/vcctllib/libvcctl.a
transport: /Users/jwbullard/Software/MyProjects/VCCTL/lib/libpng.a
transport: /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.2.sdk/usr/lib/libm.tbd
transport: /Users/jwbullard/Software/MyProjects/VCCTL/lib/libz.dylib
transport: CMakeFiles/transport.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/Users/jwbullard/Software/MyProjects/VCCTL/build_backend/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking C executable transport"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/transport.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/transport.dir/build: transport
.PHONY : CMakeFiles/transport.dir/build

CMakeFiles/transport.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/transport.dir/cmake_clean.cmake
.PHONY : CMakeFiles/transport.dir/clean

CMakeFiles/transport.dir/depend:
	cd /Users/jwbullard/Software/MyProjects/VCCTL/build_backend && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/jwbullard/Software/MyProjects/VCCTL /Users/jwbullard/Software/MyProjects/VCCTL /Users/jwbullard/Software/MyProjects/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/VCCTL/build_backend /Users/jwbullard/Software/MyProjects/VCCTL/build_backend/CMakeFiles/transport.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/transport.dir/depend

