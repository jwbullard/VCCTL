MAKE = make
all:	lib_obj \
		pub_obj

lib_obj:
	cd lib; ${MAKE} all install

pub_obj:	lib_obj
	cd pub; ${MAKE} all install

clean:
	cd lib; ${MAKE} clean
	cd pub; ${MAKE} clean

cleanobj:
	cd lib; ${MAKE} cleanobj
	cd pub; ${MAKE} cleanobj
