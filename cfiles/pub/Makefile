# Makefile for Linux and Unix with gcc compiler

MAKE= make
HYDIFILES= \
	disrealnew.h \
	properties.c \
	burn3d.c \
	burnset.c \
	parthyd.c \
	hydrealnew.c \
	pHpred.c

HYDCFILES = \
	disrealnew.c

CFILES = \
	apstats.c \
	aggvrml.c \
	chlorattack3d.c \
	distfapart.c \
	distfarand.c \
        dryout.c \
	elastic.c \
	genaggpack.c \
 	genmic.c \
        hydmovie.c \
	image100.c \
	leach3d.c \
	measagg.c \
	oneimage.c \
	onepimage.c \
	perc3d.c \
	perc3d-leach.c \
	poredist3d.c \
	rand3d.c \
	stat3d.c \
	totsurf.c \
	sulfattack3d.c \
        transport.c \
        transport_for_jason.c \
        vcctl2thames.c \
        thames2vcctl.c \
        thames2vcctlcorr.c \

OBJFILES= ${CFILES:.c=.o} ${HYDCFILES:.c=.o}

EXECS= ${CFILES:.c=}
HYDEXEC= ${HYDCFILES:.c=}

BINDIR= $(HOME)/bin
HOMEDIR=$(BINDIR)

MATHLIB = -lm
PNGLIB = -lpng
VCCTL_LIBDIR= .
VCCTL_LIBNAME= libvcctl.a
VCCTL_LIB= -lvcctl

VCCTL_INCDIR= .
VCCTL_INC= vcctl.h

# For gcc
CC= gcc
# For ANSI compilers
#CC= cc

CFLAGS= -c -Wall -g -O2 -I/usr/local/include -I/usr/include -I/opt/local/include -I.
LD_LIBS= -Wl, -rpath /opt/local/lib -L/usr/local/lib -L/opt/local/lib -L/usr/lib -L.
CLINKFLAGS= ${LD_LIBS} ${MATHLIB} ${PNGLIB} ${VCCTL_LIB}

RM= /bin/rm -f
CP= /bin/cp -f
#--- You shouldn't have to edit anything else. ---

all:	$(EXECS) $(HYDEXEC)

%.o:	%.c
	$(CC) $(CFLAGS) $<

#${EXECS}:	$$@.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
#	$(CC) -o $@ $@.o ${CLINKFLAGS}
#
#${HYDEXEC}:	$$@.o ${HYDIFILES} ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
#	$(CC) -o $@ $@.o ${CLINKFLAGS}

apstats:	apstats.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ apstats.o ${CLINKFLAGS}

aggvrml:	aggvrml.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ aggvrml.o ${CLINKFLAGS}

chlorattack3d:	chlorattack3d.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ chlorattack3d.o ${CLINKFLAGS}

disrealnew:	disrealnew.o ${HYDIFILES} ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ disrealnew.o ${CLINKFLAGS}

distfapart:	distfapart.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ distfapart.o ${CLINKFLAGS}

distfarand:	distfarand.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ distfarand.o ${CLINKFLAGS}

dryout:	dryout.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ dryout.o ${CLINKFLAGS}

elastic:	elastic.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ elastic.o ${CLINKFLAGS}

genaggpack:	genaggpack.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ genaggpack.o ${CLINKFLAGS}

genmic:	genmic.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ genmic.o ${CLINKFLAGS}

hydmovie:	hydmovie.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ hydmovie.o ${CLINKFLAGS}

image100:	image100.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ image100.o ${CLINKFLAGS}

leach3d:	leach3d.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ leach3d.o ${CLINKFLAGS}

measagg:	measagg.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ measagg.o ${CLINKFLAGS}

oneimage:	oneimage.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ oneimage.o ${CLINKFLAGS}

onepimage:	onepimage.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ onepimage.o ${CLINKFLAGS}

perc3d:	perc3d.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ perc3d.o ${CLINKFLAGS}

perc3d-leach:	perc3d-leach.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ perc3d-leach.o ${CLINKFLAGS}

poredist3d:	poredist3d.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ poredist3d.o ${CLINKFLAGS}

rand3d:	rand3d.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ rand3d.o ${CLINKFLAGS}

stat3d:	stat3d.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ stat3d.o ${CLINKFLAGS}

totsurf:	totsurf.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ totsurf.o ${CLINKFLAGS}

sulfattack3d:	sulfattack3d.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ sulfattack3d.o ${CLINKFLAGS}

transport:	transport.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ transport.o ${CLINKFLAGS}

transport_for_jason:	transport_for_jason.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ transport_for_jason.o ${CLINKFLAGS}

vcctl2thames:	vcctl2thames.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ vcctl2thames.o ${CLINKFLAGS}

thames2vcctl:	thames2vcctl.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ thames2vcctl.o ${CLINKFLAGS}

thames2vcctlcorr:	thames2vcctlcorr.o ${VCCTL_LIBDIR}/${VCCTL_LIBNAME} ${VCCTL_INCDIR}/${VCCTL_INC}
	$(CC) -o $@ thames2vcctlcorr.o ${CLINKFLAGS}

tools_objs:
	cd tools; ${MAKE} all

install:	${EXECS} ${HYDEXEC}
	mkdir -p $(BINDIR)
	${CP} ${EXECS} ${BINDIR}/.
	${CP} ${HYDEXEC} ${BINDIR}/.

clean:
	${RM} -r -R ${OBJFILES} ${EXECS} ${HYDEXEC} ${BINDIR}/${EXECS} ${BINDIR}/${HYDEXEC}
	cd tools; ${MAKE} clean

cleanobj:
	${RM} -R ${OBJFILES}
	cd tools; ${MAKE} cleanobj
