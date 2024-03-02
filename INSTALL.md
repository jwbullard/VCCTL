# INSTALL

## INTRODUCTION

For further information, or in case of problems, please contact the author,
Jeff Bullard (jwbullard@tamu.edu).

## PREREQUISITES
Compiling C programs requires cmake > 3.0

Development activities for the user interface currently requires NetBeans and may require
some modifications to work on a given platform.

## INSTALLING

* `cd backend/zlib-1.3.1/build`
* `cmake -DCMAKE_INSTALL_PREFIX="../../.." ..`
* `make install`
* `cd ../../libpng/build`
* `cmake -DCMAKE_INSTALL_PREFIX="../../.." -DZLIB-ROOT="../../.." ..`
* `make install`
* `cd ../../../build_backend`
* `cmake ..`
* `make`

## UNINSTALLING

To uninstall everything, simply delete the directory.
