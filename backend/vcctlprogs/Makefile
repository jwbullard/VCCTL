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

BINDIR= ../../bin

MATHLIB = -lm
PNGLIB = -lpng
VCCTLLIBDIR= ../../lib
VCCTLLIBNAME= libvcctl.a
VCCTLLIB= -lvcctl

VCCTLINCDIR= ../../include
VCCTLINC= vcctl.h

# For gcc
CC= gcc
# For ANSI compilers
#CC= cc

CFLAGS= -c -Wall -g -O2 -I../../include -I/usr/local/include -I/usr/include -I/opt/local/include -I.
LD_LIBS= -Wl, -rpath /opt/local/lib -L../../lib -L/usr/local/lib -L/opt/local/lib -L/usr/lib -L.
CLINKFLAGS= ${LD_LIBS} ${MATHLIB} ${PNGLIB} ${VCCTLLIB}

RM= /bin/rm -f
CP= /bin/cp -f
#--- You shouldn't have to edit anything else. ---

all:	$(EXECS) $(HYDEXEC)

%.o:	%.c
	$(CC) $(CFLAGS) $<

#${EXECS}:	$$@.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
#	$(CC) -o $@ $@.o ${CLINKFLAGS}
#
#${HYDEXEC}:	$$@.o ${HYDIFILES} ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
#	$(CC) -o $@ $@.o ${CLINKFLAGS}

apstats:	apstats.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ apstats.o ${CLINKFLAGS}

aggvrml:	aggvrml.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ aggvrml.o ${CLINKFLAGS}

chlorattack3d:	chlorattack3d.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ chlorattack3d.o ${CLINKFLAGS}

disrealnew:	disrealnew.o ${HYDIFILES} ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ disrealnew.o ${CLINKFLAGS}

distfapart:	distfapart.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ distfapart.o ${CLINKFLAGS}

distfarand:	distfarand.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ distfarand.o ${CLINKFLAGS}

dryout:	dryout.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ dryout.o ${CLINKFLAGS}

elastic:	elastic.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ elastic.o ${CLINKFLAGS}

genaggpack:	genaggpack.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ genaggpack.o ${CLINKFLAGS}

genmic:	genmic.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ genmic.o ${CLINKFLAGS}

hydmovie:	hydmovie.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ hydmovie.o ${CLINKFLAGS}

image100:	image100.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ image100.o ${CLINKFLAGS}

leach3d:	leach3d.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ leach3d.o ${CLINKFLAGS}

measagg:	measagg.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ measagg.o ${CLINKFLAGS}

oneimage:	oneimage.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ oneimage.o ${CLINKFLAGS}

onepimage:	onepimage.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ onepimage.o ${CLINKFLAGS}

perc3d:	perc3d.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ perc3d.o ${CLINKFLAGS}

perc3d-leach:	perc3d-leach.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ perc3d-leach.o ${CLINKFLAGS}

poredist3d:	poredist3d.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ poredist3d.o ${CLINKFLAGS}

rand3d:	rand3d.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ rand3d.o ${CLINKFLAGS}

stat3d:	stat3d.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ stat3d.o ${CLINKFLAGS}

totsurf:	totsurf.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ totsurf.o ${CLINKFLAGS}

sulfattack3d:	sulfattack3d.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ sulfattack3d.o ${CLINKFLAGS}

transport:	transport.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ transport.o ${CLINKFLAGS}

transport_for_jason:	transport_for_jason.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ transport_for_jason.o ${CLINKFLAGS}

vcctl2thames:	vcctl2thames.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ vcctl2thames.o ${CLINKFLAGS}

thames2vcctl:	thames2vcctl.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ thames2vcctl.o ${CLINKFLAGS}

thames2vcctlcorr:	thames2vcctlcorr.o ${VCCTLLIBDIR}/${VCCTLLIBNAME} ${VCCTLINCDIR}/${VCCTLINC}
	$(CC) -o $@ thames2vcctlcorr.o ${CLINKFLAGS}

install:	${EXECS} ${HYDEXEC}
	mkdir -p $(BINDIR)
	${CP} ${EXECS} ${BINDIR}/.
	${CP} ${HYDEXEC} ${BINDIR}/.

clean:
	${RM} -r -R ${OBJFILES} ${EXECS} ${HYDEXEC} ${BINDIR}/${EXECS} ${BINDIR}/${HYDEXEC}

cleanobj:
	${RM} -R ${OBJFILES}
