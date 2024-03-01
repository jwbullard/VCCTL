# Makefile for Linux and Unix computers with gcc 
# For gcc

MAKE = /usr/bin/make
CMAKE = /opt/local/bin/cmake

BINDIR = ../../bin
VCCTLLIBDIR = ../../lib
VCCTLINCDIR = ../../include

CC= gcc
# For ANSI compilers
#CC= gcc

CFLAGS=  -c -g -IVCCTLINCDIR -I/usr/local/include -I/usr/include -I/opt/local/include -I.
LD_LIBS= -rpath -LVCCTLLIBDIR -L/opt/local/lib -L/usr/local/lib -L/opt/local/lib -L/usr/lib -L. -lm -lpng
VCCTL_LIBNAME= libvcctl.a

CFILES= \
	breakflocs.c \
    calcporedist3d.c \
	checkbc.c \
	complex.c \
	convert_id.c \
    diam2vol.c \
	filehandler.c \
	gtime.c \
	id2phasename.c \
	imageutil.c \
	mediansize.c \
	memutil.c \
	messages.c \
	probe_imgheader.c \
	ran1.c \
	read_imgheader.c \
	read_string.c \
	fread_string.c \
	skip_imgheader.c \
	write_imgheader.c

OBJS= ${CFILES:.c=.o}

INSTALL_LIB= $(VCCTLLIBDIR)
INSTALL_INCLUDE= $(VCCTLINCDIR)

RM= /bin/rm -f
CP= /bin/cp -f
#--- You shouldn't have to edit anything else. ---

all:	${VCCTL_LIBNAME}

${VCCTL_LIBNAME}:	${OBJS}
	ar rc ${VCCTL_LIBNAME} ${OBJS}
	ranlib ${VCCTL_LIBNAME}

%.o: %.c
	${CC} ${CFLAGS} $<

install:	${VCCTL_LIBNAME}
	${CP} ${VCCTL_LIBNAME} ${INSTALL_LIB}
	${CP} vcctl.h ${INSTALL_INCLUDE}
	${CP} vcctlfuncs.h ${INSTALL_INCLUDE}
	${CP} vcctlcomplex.h ${INSTALL_INCLUDE}

cleanobj:
	${RM} ${OBJS}

clean:
	${RM} ${OBJS} ${VCCTL_LIBNAME}
	${RM} ${INSTALL_LIB}/${VCCTL_LIBNAME}
	${RM} ${INSTALL_INCLUDE}/vcctl.h
	${RM} ${INSTALL_INCLUDE}/vcctlfuncs.h
	${RM} ${INSTALL_INCLUDE}/vcctlcomplex.h

