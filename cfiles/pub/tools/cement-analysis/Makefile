# For gcc
CC= gcc
# For ANSI compilers
#CC= cc

MATHLIB = -lm
PNGLIB = -lpng
VCCTL_LIBDIR= .
VCCTL_LIBNAME= libvcctl.a
VCCTL_LIB= -lvcctl

VCCTL_INCDIR= .
VCCTL_INC= vcctl.h

CFLAGS= -c -Wall -O2 -I"${VCCTL_INCDIR}"
CLINKFLAGS= -L"${VCCTL_LIBDIR}" ${MATHLIB} ${PNGLIB} ${VCCTL_LIB}

RM= /bin/rm -f
CP= /bin/cp -f

CFILES= \
	rgbimage.c \
	statsimp.c \
	genpsdfile.c \
	geninffile.c \
	genpfcfile.c \
	genreadmehtml.c \
	genxrdfile.c \
	corrcalc.c \
	corrcalchyd.c \
	corrxy2r.c \
	combineall.c \
	convertImageJ.c \
	processImageJ.c \
	pnm2stats.c \
	mistats.c \
	modpsd.c \
	vol2mass.c \

OBJS= ${CFILES:.c=.o}
EXECS= ${CFILES:.c=}

BINDIR= ${HOME}/vcctl/bin
RM= /bin/rm -f
#--- You shouldn't have to edit anything else. ---

all:	${EXECS}

%.o: %.c
	$(CC) $(CFLAGS) $<

${EXECS}:	${OBJS}
	$(CC) $@.o -o $@ $(CLINKFLAGS)

#statsimp: statsimp.o 
#	$(CC) statsimp.o -o statsimp -lm -I/usr/include
#
#rgbimage: rgbimage.o 
#	$(CC) rgbimage.o -o $(BINDIR)/rgbimage -lm -I/usr/include
#
#corrcalc: corrcalc.o 
#	$(CC) corrcalc.o -o $(BINDIR)/corrcalc -lm -I/usr/include
#
#corrxy2r: corrxy2r.o 
#	$(CC) corrxy2r.o -o $(BINDIR)/corrxy2r -lm -I/usr/include
#
#combineall: combineall.o 
#	$(CC) combineall.o -o $(BINDIR)/combineall -lm -I/usr/include
#
#convertImageJ: convertImageJ.o
#	$(CC) convertImageJ.o -o $(BINDIR)/$@ -lm -I/usr/include
#
#pnm2stats: pnm2stats.o 
#	$(CC) pnm2stats.o -o $(BINDIR)/pnm2stats -lm -I/usr/include
#
#geninffile: geninffile.o 
#	$(CC) geninffile.o -o $(BINDIR)/geninffile -lm -I/usr/include
#
#genxrdfile: genxrdfile.o 
#	$(CC) genxrdfile.o -o $(BINDIR)/genxrdfile -lm -I/usr/include
#
#genpfcfile: genpfcfile.o 
#	$(CC) genpfcfile.o -o $(BINDIR)/genpfcfile -lm -I/usr/include
#
#genpsdfile: genpsdfile.o 
#	$(CC) genpsdfile.o -o $(BINDIR)/genpsdfile -lm -I/usr/include
#
#genreadmehtml: genreadmehtml.o 
#	$(CC) genreadmehtml.o -o $(BINDIR)/genreadmehtml -lm -I/usr/include
#
#mistats: mistats.o 
#	$(CC) mistats.o -o $(BINDIR)/mistats -lm -I/usr/include
#
#modpsd: modpsd.o 
#	$(CC) modpsd.o -o $(BINDIR)/modpsd -lm -I/usr/include
#
#vol2mass: vol2mass.o 
#	$(CC) vol2mass.o -o $(BINDIR)/vol2mass -lm -I/usr/include
#
install: ${EXECS}

cleanobj:
	rm -f ${OBJS}

clean:
	rm -f ${OBJS}  ${EXECS}
	rm -f ${BINDIR}/${EXECS}

cleanall:
	rm -f ${OBJS}  ${EXECS}
	rm -f ${BINDIR}/${EXECS}
