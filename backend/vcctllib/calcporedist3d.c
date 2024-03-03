/******************************************************************************
 *	Function calcporedist3d calculates the pore size distribution of
 *       a microstructure, writes the information to a file, and then returns
 *       control to calling function
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
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/***
 *    Function declarations
 ***/

int maketemp(int size, int *xsph, int *ysph, int *zsph);
int pix2x(int pid, int xsize, int ysize);
int pix2y(int pid, int xsize, int ysize);
int pix2z(int pid, int xsize, int ysize);

int calcporedist3d(char *name) {
  register int i1, i2, i3;
  int iout, oiout, status;
  char instring[MAXSTRING];
  int syspix = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
  int xsize = DEFAULTSYSTEMSIZE;
  int ysize = DEFAULTSYSTEMSIZE;
  int zsize = DEFAULTSYSTEMSIZE;
  float res = 1.0;
  float sizemag = 1.0;
  int isizemag = 1;
  float resmag = 1.0;
  int iresmag = 1;
  char filename[MAXSTRING];
  int i, *pores, *ndiam, porecnt, index, ns, maxsph, nsph;
  int ix, iy, iz, max_allowed_diam, mindim, nd, failed, nrad;
  int xc, yc, zc;
  int ***tmic, ***mic;
  int *xsph, *ysph, *zsph;
  FILE *infile, *outfile;

  /* VCCTL software version used to create input file */
  float version;

  sprintf(filename, "%s", name);

  infile = filehandler("calcporedist3d", filename, "READ");
  if (!infile) {
    printf("\n==>Could not open file for reading.");
    fflush(stdout);
    return (1);
  }

  /***
   *    Determine whether system size and resolution
   *    are specified in the image file
   ***/

  if (read_imgheader(infile, &version, &xsize, &ysize, &zsize, &res)) {
    fclose(infile);
    bailout("calcporedist3d", "Error reading image header");
    return (1);
  }

  /***
   *    Define the number of histogram bins
   ***/

  syspix = xsize * ysize * zsize;
  sizemag =
      pow(((float)syspix) / (pow(((float)DEFAULTSYSTEMSIZE), 3.0)), (1. / 3.));
  isizemag = (int)(sizemag + 0.5);
  resmag = ((float)DEFAULTRESOLUTION) / res;
  iresmag = (int)(resmag + 0.5);

  /***
   *    Allocate memory for all global variables
   ***/

  mic = NULL;
  mic = ibox(xsize + 1, ysize + 1, zsize + 1);

  if (!mic) {
    bailout("calcporedist3d", "Memory allocation failure");
    fflush(stdout);
    return (1);
  }

  /***
   *    Read the microstructure file
   ***/

  for (i3 = 0; i3 < zsize; i3++) {
    for (i2 = 0; i2 < ysize; i2++) {
      for (i1 = 0; i1 < xsize; i1++) {
        fscanf(infile, "%s", instring);
        oiout = atoi(instring);
        iout = convert_id(oiout, version);
        mic[i1][i2][i3] = iout;
      }
    }
  }

  fclose(infile);

  /* Allocate memory for temporary microstructure image */

  tmic = NULL;

  tmic = ibox(xsize + 1, ysize + 1, zsize + 1);
  if (!tmic) {
    warning("calcporedist3d", "Could not allocate required memory for "
                              "temporary microstructure image");
    return (1);
  }

  porecnt = 0;
  for (iz = 0; iz < zsize; iz++) {
    for (iy = 0; iy < ysize; iy++) {
      for (ix = 0; ix < xsize; ix++) {
        if (mic[ix][iy][iz] == POROSITY || mic[ix][iy][iz] == EMPTYP ||
            mic[ix][iy][iz] == EMPTYDP || mic[ix][iy][iz] == CRACKP) {
          tmic[ix][iy][iz] = POROSITY;
          porecnt++;
        } else {
          tmic[ix][iy][iz] = 10000;
        }
      }
    }
  }

  mindim = xsize;
  if (ysize < mindim)
    mindim = ysize;
  if (zsize < mindim)
    mindim = zsize;

  max_allowed_diam = (int)(0.2 * mindim);

  /* Allocate memory for ndiam vector */
  ndiam = NULL;
  ndiam = ivector(max_allowed_diam + 1);
  if (!ndiam) {
    warning("calcporedist3d", "Could not allocate required memory");
    free_ibox(tmic, xsize + 1, ysize + 1);
    free_ibox(mic, xsize + 1, ysize + 1);
    return (1);
  }

  /* Ensure that diameter is odd */
  if (max_allowed_diam % 2 == 0)
    max_allowed_diam++;
  maxsph = diam2vol((float)max_allowed_diam);

  /* Allocate memory for xsph,ysph, and zsph vectors */
  xsph = NULL;
  xsph = ivector(maxsph);
  if (!xsph) {
    warning("calcporedist3d", "Could not allocate required memory");
    free_ivector(ndiam);
    free_ibox(tmic, xsize + 1, ysize + 1);
    free_ibox(mic, xsize + 1, ysize + 1);
    return (1);
  }

  ysph = NULL;
  ysph = ivector(maxsph);
  if (!ysph) {
    warning("calcporedist3d", "Could not allocate required memory");
    free_ivector(xsph);
    free_ivector(ndiam);
    free_ibox(tmic, xsize + 1, ysize + 1);
    free_ibox(mic, xsize + 1, ysize + 1);
    return (1);
  }

  zsph = NULL;
  zsph = ivector(maxsph);
  if (!zsph) {
    warning("calcporedist3d", "Could not allocate required memory");
    free_ivector(ysph);
    free_ivector(xsph);
    free_ivector(ndiam);
    free_ibox(tmic, xsize + 1, ysize + 1);
    free_ibox(mic, xsize + 1, ysize + 1);
    return (1);
  }

  /* Allocate memory for porosity locator vector */

  pores = NULL;
  pores = ivector(porecnt);
  if (!pores) {
    warning("poredist3d", "Could not allocate required memory");
    fflush(stdout);
    free_ivector(zsph);
    free_ivector(ysph);
    free_ivector(xsph);
    free_ivector(ndiam);
    free_ibox(tmic, xsize + 1, ysize + 1);
    free_ibox(mic, xsize + 1, ysize + 1);
    return (1);
  }

  /* Load up the locator vector */

  index = 0;
  ns = 0;
  for (iz = 0; iz < zsize && index < porecnt; iz++) {
    for (iy = 0; iy < ysize && index < porecnt; iy++) {
      for (ix = 0; ix < xsize && index < porecnt; ix++) {
        if (mic[ix][iy][iz] == POROSITY || mic[ix][iy][iz] == EMPTYP ||
            mic[ix][iy][iz] == EMPTYDP || mic[ix][iy][iz] == CRACKP) {
          pores[index] = ns;
          index++;
        }
        ns++;
      }
    }
  }

  /* Initialize the ndiam vector */

  for (i = 0; i <= max_allowed_diam; i++)
    ndiam[i] = 0;

  /* Start with largest allowed pore diameter */

  for (nd = max_allowed_diam; nd >= 1; nd -= 2) {
    nrad = nd / 2;
    nsph = maketemp(nrad, xsph, ysph, zsph);

    /* Check all pore pixels in the 3-D system */

    for (index = 0; index < porecnt; index++) {
      xc = pix2x(pores[index], xsize, ysize);
      yc = pix2y(pores[index], xsize, ysize);
      zc = pix2z(pores[index], xsize, ysize);
      if (tmic[xc][yc][zc] == POROSITY) {
        failed = 0;
        for (i = 0; (i < nsph) && (!failed); i++) {
          ix = xc + xsph[i];
          iy = yc + ysph[i];
          iz = zc + zsph[i];
          ix += checkbc(ix, xsize);
          iy += checkbc(iy, ysize);
          iz += checkbc(iz, zsize);
          if (tmic[ix][iy][iz] > max_allowed_diam)
            failed = 1;
        }
        if (!failed) {
          for (i = 0; i < nsph; i++) {
            ix = xc + xsph[i];
            iy = yc + ysph[i];
            iz = zc + zsph[i];
            ix += checkbc(ix, xsize);
            iy += checkbc(iy, ysize);
            iz += checkbc(iz, zsize);
            if (tmic[ix][iy][iz] < nd) {
              tmic[ix][iy][iz] = nd;
              ndiam[nd]++;
            }
          }
        }
      }
    }
  }

  strcat(filename, ".poredist");
  outfile = filehandler("poredist3d", filename, "WRITE");
  if (!outfile) {
    warning("poredist3d", "Could not open output file");
    fflush(stdout);
    free_ivector(zsph);
    free_ivector(ysph);
    free_ivector(xsph);
    free_ivector(ndiam);
    free_ibox(tmic, xsize + 1, ysize + 1);
    free_ibox(mic, xsize + 1, ysize + 1);
    return (1);
  }

  fprintf(outfile, "Total pore volume = %f um^3", ((float)porecnt));
  fprintf(outfile, "\n\nDiameter_(um)\tNumber\tFraction");
  for (i = 1; i <= max_allowed_diam; i += 2) {
    fprintf(outfile, "\n%f\t%d\t%f", ((float)i), ndiam[i],
            (((float)ndiam[i]) / ((float)porecnt)));
  }

  fclose(outfile);

  free_ivector(pores);
  free_ivector(zsph);
  free_ivector(ysph);
  free_ivector(xsph);
  free_ivector(ndiam);
  free_ibox(tmic, xsize + 1, ysize + 1);
  free_ibox(mic, xsize + 1, ysize + 1);

  return (0);
}

/***
 *    maketemp
 *
 *    Routine to create a template for the sphere of
 *    interest of radius size to be used in
 *    curvature evaluation
 *
 *    Arguments:  int size (the radius of the sphere)
 *                int pointer to xsph vector
 *                int pointer to ysph vector
 *                int pointer to zsph vector
 *    Returns:    int number of pixels in sphere
 *
 *    Calls:		no other routines
 *    Called by:	runsint
 ***/
int maketemp(int size, int *xsph, int *ysph, int *zsph) {
  int icirc, xval, yval, zval;
  float xtmp, ytmp, dist;

  /***
   *   Determine and store the locations of all
   *   pixels in the 3-D sphere
   ***/

  icirc = 0;
  for (xval = (-size); xval <= size; xval++) {

    xtmp = (float)(xval * xval);
    for (yval = (-size); yval <= size; yval++) {

      ytmp = (float)(yval * yval);
      for (zval = (-size); zval <= size; zval++) {

        dist = sqrt(xtmp + ytmp + (float)(zval * zval));

        if (dist <= ((float)size + 0.5)) {

          xsph[icirc] = xval;
          ysph[icirc] = yval;
          zsph[icirc] = zval;
          icirc++;
        }
      }
    }
  }

  /***
   *   Return the number of pixels contained in
   *   sphere of radius (size+0.5)
   ***/

  return (icirc);
}

/***
*    pix2x
*
*    Convert pixel id number to x coordinate
*
*    Arguments:    int pixel id number
                   int xsize,ysize are the x,y dimensions of the system
*    Returns:      int x coordinate
*
*    Calls:        no other routines
*    Called by:    calcporedist3d
***/
int pix2x(int pid, int xsize, int ysize) {
  int x, y, z;
  z = pid / (xsize * ysize);
  y = (pid - (z * xsize * ysize)) / xsize;
  x = (pid - (z * xsize * ysize) - (y * xsize));
  return (x);
}

/***
*    pix2y
*
*    Convert pixel id number to y coordinate
*
*    Arguments:    int pixel id number
                   int xsize,ysize are the x,y dimensions of the system
*    Returns:      int x coordinate
*
*    Calls:        no other routines
*    Called by:    calcporedist3d
***/
int pix2y(int pid, int xsize, int ysize) {
  int y, z;
  z = pid / (xsize * ysize);
  y = (pid - (z * xsize * ysize)) / xsize;
  return (y);
}

/***
*    pix2z
*
*    Convert pixel id number to z coordinate
*
*    Arguments:    int pixel id number
                   int xsize,ysize are the x,y dimensions of the system
*    Returns:      int x coordinate
*
*    Calls:        no other routines
*    Called by:    calcporedist3d
***/
int pix2z(int pid, int xsize, int ysize) {
  int z = pid / (xsize * ysize);
  return (z);
}
