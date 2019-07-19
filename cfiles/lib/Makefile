# Makefile for Linux and Unix computers with gcc 
# For gcc

MAKE = /usr/bin/make
CMAKE = /opt/local/bin/cmake
PREFIX = /Users/bullard/Software/MyProjects/vcctl

BINDIR = $(PREFIX)/bin
LIBDIR = $(PREFIX)/cfiles/lib
PUBDIR = $(PREFIX)/cfiles/pub

CC= gcc
# For ANSI compilers
#CC= gcc

CFLAGS=  -c -g -I/usr/local/include -I/usr/include -I/opt/local/include -I.
LD_LIBS= -rpath /opt/local/lib -L/usr/local/lib -L/opt/local/lib -L/usr/lib -L. -lm -lpng
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

INSTALL_LIB= $(PUBDIR)
INSTALL_INCLUDE= $(PUBDIR)

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
	${CP} ${VCCTL_LIBNAME} ${INSTALL_LIB}/tools/cement-analysis
	${CP} ${LIBDIR}/vcctl.h ${INSTALL_INCLUDE}
	${CP} ${LIBDIR}/vcctl.h ${INSTALL_INCLUDE}/tools/cement-analysis
	${CP} ${LIBDIR}/vcctlfuncs.h ${INSTALL_INCLUDE}
	${CP} ${LIBDIR}/vcctlfuncs.h ${INSTALL_INCLUDE}/tools/cement-analysis
	${CP} ${LIBDIR}/vcctlcomplex.h ${INSTALL_INCLUDE}
	${CP} ${LIBDIR}/vcctlcomplex.h ${INSTALL_INCLUDE}/tools/cement-analysis

cleanobj:
	${RM} ${OBJS}

clean:
	${RM} ${OBJS} ${VCCTL_LIBNAME}
	${RM} ${INSTALL_LIB}/${VCCTL_LIBNAME}
	${RM} ${INSTALL_LIB}/tools/cement-analysis/${VCCTL_LIBNAME}
	${RM} ${INSTALL_INCLUDE}/vcctl.h
	${RM} ${INSTALL_INCLUDE}/tools/cement-analysis/vcctl.h
	${RM} ${INSTALL_INCLUDE}/vcctlfuncs.h
	${RM} ${INSTALL_INCLUDE}/tools/cement-analysis/vcctlfuncs.h
	${RM} ${INSTALL_INCLUDE}/vcctlcomplex.h
	${RM} ${INSTALL_INCLUDE}/tools/cement-analysis/vcctlcomplex.h
	${RM} /usr/lib/libvcctl*
	${RM} -r /usr/lib/vcctl
	${RM} /usr/local/lib/libvcctl*
	${RM} -r /usr/local/lib/vcctl

