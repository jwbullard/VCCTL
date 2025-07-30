/******************************************************
 *
 * Program apstats.c
 *
 * Reads in a 3-D aggregate packing and outputs
 *
 * 	(1) phase volumes
 * 	(2) volume fractions
 * 	(3) binder-exposed surface area fractions
 *
 *	Only processes the phase values 0-3
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
#include <string.h>

#define BINDER 0
#define AGG 1
#define ITZ 2

/***
 *	Global variables
 ***/
float Version;

int main(void) {
  int ***mic;
  int valin, ovalin, ix, iy, iz, ix1, iy1, iz1, k, syssize, flag;
  int xsyssize, ysyssize, zsyssize;
  int voltot, surftot, totalvol;
  int volume[3], surface[3], surfpix[3];
  float res;
  char filen[MAXSTRING], fileout[MAXSTRING], buff[MAXSTRING];
  char instring[MAXSTRING];
  FILE *infile, *statfile;

  printf("Enter name of file to open \n");
  read_string(filen, sizeof(filen));
  printf("%s \n", filen);
  printf("Enter name of file to write statistics to \n");
  read_string(fileout, sizeof(fileout));
  printf("%s \n", fileout);

  /* Initialize local arrays */

  for (ix = 0; ix < 3; ix++) {
    volume[ix] = surface[ix] = surfpix[ix] = 0;
  }

  /***
   *	Open input and output files.  Output file
   *	will be ultimately read by aggpackstats for
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
    fscanf(infile, "%s", instring);
    Version = atof(instring);
    fscanf(infile, "%s", buff); /* Desc. of system size */
    if (!strcmp(buff, XSIZESTRING)) {
      fscanf(infile, "%s", instring);
      xsyssize = atoi(instring);
      fscanf(infile, "%s %s", buff, instring);
      ysyssize = atoi(instring);
      fscanf(infile, "%s %s", buff, instring);
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

  totalvol = 0;
  for (iz = 0; iz < zsyssize; iz++) {
    for (iy = 0; iy < ysyssize; iy++) {
      for (ix = 0; ix < xsyssize; ix++) {

        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valin = convert_id(ovalin, Version);
        mic[ix][iy][iz] = valin;

        volume[valin]++;
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

        if (mic[ix][iy][iz] == AGG) {

          valin = mic[ix][iy][iz];

          /* Check six neighboring pixels for binder or ITZ*/

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

            if ((mic[ix1][iy1][iz1] == BINDER) || (mic[ix1][iy1][iz1] == ITZ)) {

              surface[valin]++;
              flag = 1;
            }
          }
        }
        if (flag)
          surfpix[valin]++;
      }
    }
  }

  printf("Component    Volume      Surface     Volume    Surface\n");
  printf("  ID         count        count      fraction  fraction\n");
  fprintf(statfile, "Component    Volume      Surface     Volume    Surface\n");
  fprintf(statfile,
          "   ID        count        count      fraction  fraction\n");

  surftot = surface[AGG];

  voltot = volume[BINDER] + volume[AGG] + volume[ITZ];

  /***
   *	Print information about binder, aggregate and ITZ
   ***/

  for (k = BINDER; k <= ITZ; k++) {
    printf("  %d    %8d     %8d", k, volume[k], surface[k]);
    printf("     %.5f", (double)volume[k] / (double)voltot);
    printf("   %.5f\n", (double)surface[k] / (double)surftot);
    fprintf(statfile, "  %d    %8d     %8d", k, volume[k], surface[k]);
    fprintf(statfile, "     %.5f", (double)volume[k] / (double)voltot);
    fprintf(statfile, "   %.5f\n", (double)surface[k] / (double)surftot);
  }

  printf("Total  %8d     %8d\n", voltot, surftot);
  fprintf(statfile, "Total  %8d     %8d\n", voltot, surftot);

  fclose(statfile);

  /***
   *	Free the allocated memory
   ***/

  free_ibox(mic, xsyssize, ysyssize);

  return (0);
}
