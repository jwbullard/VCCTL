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

# Utility rule file for png_scripts_symbols_out.

# Include any custom commands dependencies for this target.
include CMakeFiles/png_scripts_symbols_out.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/png_scripts_symbols_out.dir/progress.make

CMakeFiles/png_scripts_symbols_out: scripts/symbols.out

scripts/symbols.out: /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/scripts/symbols.c
scripts/symbols.out: /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/png.h
scripts/symbols.out: /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/pngconf.h
scripts/symbols.out: /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/scripts/pnglibconf.h.prebuilt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --blue --bold --progress-dir=/Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Generating scripts/symbols.out"
	/opt/local/bin/cmake -DINPUT=/Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/scripts/symbols.c -DOUTPUT=/Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/scripts/symbols.out -P /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/scripts/cmake/genout.cmake

png_scripts_symbols_out: CMakeFiles/png_scripts_symbols_out
png_scripts_symbols_out: scripts/symbols.out
png_scripts_symbols_out: CMakeFiles/png_scripts_symbols_out.dir/build.make
.PHONY : png_scripts_symbols_out

# Rule to build all files generated by this target.
CMakeFiles/png_scripts_symbols_out.dir/build: png_scripts_symbols_out
.PHONY : CMakeFiles/png_scripts_symbols_out.dir/build

CMakeFiles/png_scripts_symbols_out.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/png_scripts_symbols_out.dir/cmake_clean.cmake
.PHONY : CMakeFiles/png_scripts_symbols_out.dir/clean

CMakeFiles/png_scripts_symbols_out.dir/depend:
	cd /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build /Users/jwbullard/Software/MyProjects/git/VCCTL/backend/libpng/build/CMakeFiles/png_scripts_symbols_out.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/png_scripts_symbols_out.dir/depend

