/******************************************************
 *
 * Program totsurf.c
 *
 * Reads in a 3-D image and outputs
 *
 * 	(1) phase volumes
 * 	(2) volume fractions
 * 	(3) pore-exposed surface area fractions
 * 	(4) mass fractions
 *
 *	Only processes the phase values 0-10, 24 and 25
 *
 * Programmer:	Dale P. Bentz
 * 				Building and Fire Research Laboratory
 *				NIST
 *				100 Bureau Drive Mail Stop 8621
 *				Gaithersburg, MD  20899-8621   USA
 *				(301) 975-5865      FAX: (301) 990-6891
 *				E-mail: dale.bentz@nist.gov
 *
 * Contact:		Jeffrey W. Bullard
 * 				Building and Fire Research Laboratory
 *				NIST
 *				100 Bureau Drive Mail Stop 8621
 *				Gaithersburg, MD  20899-8621   USA
 *				(301) 975-5725      FAX: (301) 990-6891
 *				E-mail: bullard@nist.gov
 *
 *******************************************************/
#include "include/vcctl.h"
#include <stdio.h>
#include <stdlib.h>

/***
 *	Global variables
 ***/
float Version;

#include "include/properties.h"

int main(void) {
  int ***mic;
  int valin, ovalin, ix, iy, iz, ix1, iy1, iz1, k, syssize, flag;
  int xsyssize, ysyssize, zsyssize;
  int totalvol, surface, surfpix;
  double totalmass;
  float res;
  char filen[MAXSTRING], fileout[MAXSTRING], buff[MAXSTRING];
  char instring[MAXSTRING];
  FILE *infile, *statfile;

  surface = surfpix = 0;

  /***
   *	Assign physical and chemical properties of
   *	phases.  Function comes from properties.c
   ***/

  assign_properties();

  printf("Enter name of file to open \n");
  read_string(filen, sizeof(filen));
  printf("%s \n", filen);
  printf("Enter name of file to write statistics to \n");
  read_string(fileout, sizeof(fileout));
  printf("%s \n", fileout);

  /***
   *	Open input and output files.  Output file
   *	will be ultimately read by statcalc for
   *	displaying in web page format
   ***/

  infile = fopen(filen, "r");
  statfile = fopen(fileout, "w");

  /***
   *	Determine whether software version, system
   *	size and resolution are specified in the image file
   ***/

  fscanf(infile, "%s", buff);
  if (!strcmp(buff, VERSIONSTRING)) {
    fscanf(infile, "%f", &Version);
    fscanf(infile, "%s", buff); /* Desc. of system size */
    if (!strcmp(buff, XSIZESTRING)) {
      fscanf(infile, "%s", instring);
      xsyssize = atoi(instring);
      fscanf(infile, "%s", buff);
      fscanf(infile, "%s", instring);
      ysyssize = atoi(instring);
      fscanf(infile, "%s", buff);
      fscanf(infile, "%s", instring);
      zsyssize = atoi(instring);
    } else {
      fscanf(infile, "%s", instring);
      syssize = atoi(instring);
      xsyssize = syssize;
      ysyssize = syssize;
      zsyssize = syssize;
    }
    fscanf(infile, "%s", buff); /* Desc. of resolution */
    fscanf(infile, "%s", instring);
    res = atof(instring);
  } else {

    /***
     *	This image file was generated prior to
     *	Version 3.0.  Allow backward compatibility
     *	by defaulting system size to 100 and
     *	system resolution to 1.0
     ***/

    Version = 2.0;
    syssize = DEFAULTSYSTEMSIZE;
    xsyssize = syssize;
    ysyssize = syssize;
    zsyssize = syssize;
    res = DEFAULTRESOLUTION;
    rewind(infile);
  }

  /***
   *	Dynamically allocate the memory for mic array
   ***/

  mic = ibox(xsyssize, ysyssize, zsyssize);

  /* Read in image and accumulate volume totals */

  totalmass = 0.0;
  totalvol = 0;
  for (iz = 0; iz < zsyssize; iz++) {
    for (iy = 0; iy < ysyssize; iy++) {
      for (ix = 0; ix < xsyssize; ix++) {

        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valin = ovalin;
        mic[ix][iy][iz] = valin;

        if (valin != POROSITY)
          totalvol++;
      }
    }
  }

  fclose(infile);

  ix1 = iy1 = iz1 = 0;
  for (iz = 0; iz < zsyssize; iz++) {
    for (iy = 0; iy < ysyssize; iy++) {
      for (ix = 0; ix < xsyssize; ix++) {

        flag = 0;

        if (mic[ix][iy][iz] != POROSITY) {

          valin = mic[ix][iy][iz];

          /* Check six neighboring pixels for porosity */

          for (k = 1; k <= 6; k++) {

            switch (k) {
            case 1:
              ix1 = ix - 1;
              if (ix1 < 0)
                ix1 += xsyssize;
              iy1 = iy;
              iz1 = iz;
              break;
            case 2:
              ix1 = ix + 1;
              if (ix1 >= xsyssize)
                ix1 -= xsyssize;
              iy1 = iy;
              iz1 = iz;
              break;
            case 3:
              iy1 = iy - 1;
              if (iy1 < 0)
                iy1 += ysyssize;
              ix1 = ix;
              iz1 = iz;
              break;
            case 4:
              iy1 = iy + 1;
              if (iy1 >= ysyssize)
                iy1 -= ysyssize;
              ix1 = ix;
              iz1 = iz;
              break;
            case 5:
              iz1 = iz - 1;
              if (iz1 < 0)
                iz1 += zsyssize;
              iy1 = iy;
              ix1 = ix;
              break;
            case 6:
              iz1 = iz + 1;
              if (iz1 >= zsyssize)
                iz1 -= zsyssize;
              iy1 = iy;
              ix1 = ix;
              break;
            default:
              break;
            }

            if (mic[ix1][iy1][iz1] != valin) {
              surface++;
              flag = 1;
            }
          }
        }
        if (flag)
          surfpix++;
      }
    }
  }

  /***
   *	Only include clinker phases in surface
   *	area fraction calculation
   ***/

  printf("Total volume of solids is: %8d\n", totalvol);
  printf("Total surface area of solids is: %8d\n", surface);
  printf("Number of surface pixels: %8d\n", surfpix);

  free_ibox(mic, xsyssize, ysyssize);

  return (0);
}
