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

# Utility rule file for pnglibconf_c.

# Include any custom commands dependencies for this target.
include CMakeFiles/pnglibconf_c.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/pnglibconf_c.dir/progress.make

CMakeFiles/pnglibconf_c: pnglibconf.c

pnglibconf.c: /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/scripts/pnglibconf.dfa
pnglibconf.c: scripts/options.awk
pnglibconf.c: /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/pngconf.h
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --blue --bold --progress-dir=/Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Generating pnglibconf.c"
	/opt/local/bin/cmake -DOUTPUT=pnglibconf.c -P /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/scripts/cmake/gensrc.cmake

pnglibconf_c: CMakeFiles/pnglibconf_c
pnglibconf_c: pnglibconf.c
pnglibconf_c: CMakeFiles/pnglibconf_c.dir/build.make
.PHONY : pnglibconf_c

# Rule to build all files generated by this target.
CMakeFiles/pnglibconf_c.dir/build: pnglibconf_c
.PHONY : CMakeFiles/pnglibconf_c.dir/build

CMakeFiles/pnglibconf_c.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/pnglibconf_c.dir/cmake_clean.cmake
.PHONY : CMakeFiles/pnglibconf_c.dir/clean

CMakeFiles/pnglibconf_c.dir/depend:
	cd /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/CMakeFiles/pnglibconf_c.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/pnglibconf_c.dir/depend

