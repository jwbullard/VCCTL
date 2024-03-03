# INSTALL

## INTRODUCTION

For further information, or in case of problems, please contact the author,
Jeff Bullard (jwbullard@tamu.edu).

## PREREQUISITES
### Mac OS and Linux:
* Cmake > 3.0
* Gnu C compiler

### Windows
Windows does not come prebuilt with any kind of system for compiling C/C++ code.  You must first install **MinGW** and **MSYS** to get an imitation Linux operating system working, and it comes with the needed compilers.

## INSTALLING
### Linux and Mac OS
Using a terminal window (command line prompt), navigate to the folder containing this INSTALL.md (we will call this folder WORKDIR), then follow these instructions:

* `cd backend/zlib-1.3.1`
* `mkdir build; cd build`
* `cmake -DCMAKE_INSTALL_PREFIX="../../.." ..`
* `make install`
* `cd ../../libpng`
* `mkdir build; cd build`
* `cmake -DCMAKE_INSTALL_PREFIX="../../.." -DZLIB-ROOT="../../.." ..`
* `make install`
* `cd ../../../build_backend`
* `cmake ..`
* `make`

If all goes well, the executables will be located in the folder `WORKDIR/build_backend`

### Windows
* Open a mingw64 shell, `C:\msys64\mingw64.exe`
* Change folders to the folder containing this INSTALL.md file (we will call this folder WORKDIR), then follow these instructions inside the shell window at the command line:

* `cd backend/zlib-1.3.1`
* `mkdir build; cd build`
* `cmake -DCMAKE_INSTALL_PREFIX="../../.." ..`
* `make install`
* `cd ../../libpng`
* `mkdir build; cd build`
* `cmake -DCMAKE_INSTALL_PREFIX="../../.." -DZLIB-ROOT="../../.." ..`
* `make install`
* `cd ../../../build_backend`
* `cmake ..`
* `make`

If all goes well, the executables will be located in the folder `WORKDIR/build_backend`

## UNINSTALLING

To uninstall everything, simply delete the directory.
