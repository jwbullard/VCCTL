MAKE = make
all:	zlib_obj \
		lpng_obj \
		lib_obj \
		pub_obj

zlib_obj:
	cd zlib-1.3.1/build; cmake -DCMAKE_INSTALL_PREFIX="../../.." ..; make install

lpng_obj:
	cd libpng/build; cmake -DCMAKE_INSTALL_PREFIX="../../.." -DZLIB_ROOT="../../.." ..; make install

lib_obj:
	cd vcctllib; ${MAKE} all install

progs_obj:	lib_obj
	cd vcctlprogs; ${MAKE} all install

clean:
	cd vcctllib; ${MAKE} clean
	cd vcctlprogs; ${MAKE} clean

cleanobj:
	cd vcctllib; ${MAKE} cleanobj
	cd vcctlprogs; ${MAKE} cleanobj
