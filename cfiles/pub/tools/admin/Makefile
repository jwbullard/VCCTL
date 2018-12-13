# For gcc
CC= gcc
# For ANSI compilers
#CC = cc

#For Optimization
#CFLAGS= -O2
#For debugging
#CFLAGS= -g

BINDIR=/usr/bin
INSTALLDIR=$(BINDIR)
RM= /bin/rm -f

#--- You shouldn't have to edit anything else. ---

CPPFILES = snr.cpp

OBJS=${CPPFILES:.cpp=.o}

EXECS= snr

all:	${EXECS}

snr:	snr.cpp
	${CXX} -o ${INSTALLDIR}/snr snr.cpp
	/bin/cp snr.scr ${INSTALLDIR}/snr.scr
	chmod 775 ${INSTALLDIR}/snr.scr

cleanobj:
	rm -f ${OBJS}

clean:
	rm -f ${OBJS} ${EXECS}
