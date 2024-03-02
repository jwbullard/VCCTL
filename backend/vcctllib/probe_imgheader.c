/******************************************************************************
 *	Function probe_imgheader opens a microstructure file only to read
 *	all the header information, then closes the file and returns control
 *	to calling function
 *
 * 	Arguments:	pointer to char array file name to open
 * 				pointer to float version
 * 				pointer to int xsize
 * 				pointer to int ysize
 * 				pointer to int zsize
 * 				pointer to float resolution
 *
 *	Returns:	int status flag (0 if okay, 1 if otherwise)
 *
 *	Programmer:	Jeffrey W. Bullard
 *				NIST
 *				100 Bureau Drive, Stop 8615
 *				Gaithersburg, Maryland  20899-8615
 *				USA
 *
 *				Phone:	301.975.5725
 *				Fax:	301.990.6891
 *				bullard@nist.gov
 *
 *	16 March 2004
 ******************************************************************************/
#include "../include/vcctl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int probe_imgheader(char *name, float *ver, int *xsize, int *ysize, int *zsize,
                    float *res) {
  register int i;
  int done, status = 0;
  char buff[MAXSTRING], buff1[MAXSTRING];
  FILE *fpin;

  if ((fpin = fopen(name, "r")) == NULL) {
    status = 1;
    return (status);
  }

  done = 0;
  i = 0;
  fscanf(fpin, "%s", buff);
  if (!strcmp(buff, VERSIONSTRING)) {
    fscanf(fpin, "%s", buff);
    *ver = atof(buff);
    fscanf(fpin, "%s", buff);
    if (!strcmp(buff, XSIZESTRING)) {
      fscanf(fpin, "%s", buff);
      *xsize = atoi(buff);
      fscanf(fpin, "%s %s", buff, buff1);
      *ysize = atoi(buff1);
      fscanf(fpin, "%s %s", buff, buff1);
      *zsize = atoi(buff1);
    } else if (!strcmp(buff, IMGSIZESTRING)) {
      fscanf(fpin, "%s", buff);
      *xsize = atoi(buff);
      *ysize = *xsize;
      *zsize = *xsize;
    }
    fscanf(fpin, "%s", buff);
    if (!strcmp(buff, IMGRESSTRING)) {
      fscanf(fpin, "%s", buff);
      *res = atof(buff);
      done = 1;
    }

  } else {

    /***
     *	This image file was generated prior to
     *	Version 3.0.  Allow backward compatibility
     *	by defaulting system size to 100 and
     *	system resolution to 1.0
     ***/

    *ver = 2.0;
    *res = DEFAULTRESOLUTION;
    *xsize = DEFAULTSYSTEMSIZE;
    *ysize = DEFAULTSYSTEMSIZE;
    *zsize = DEFAULTSYSTEMSIZE;

    fclose(fpin);
    if ((fpin = fopen(name, "r")) == NULL) {
      status = 1;
      return (status);
    }
  }

  return (status);
}
