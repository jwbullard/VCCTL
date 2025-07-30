/****************************************************************
 *
 * Program poredist3d-Hg.c
 * To measure the pore size distribution by simulating mercury intrusion
 *
 * This version is periodic in all three directions
 *
 * Programmer:	Jeffrey W. Bullard
 * 				Building and Fire Research Laboratory
 * 				NIST
 * 				100 Bureau Drive Mail Stop 8615
 * 				Gaithersburg, MD  20899-8615
 * 				Phone:  (301) 975-5725
 * 				FAX:	(301) 990-6891
 * 				E-mail: bullard@nist.gov
 *
 * Date: Summer 2007
 *
 ****************************************************************/
#include "include/vcctl.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/***
 *	Menu selections
 ***/

#define EXIT 1
#define READMIC EXIT + 1
#define MEASURE READMIC + 1

#define NUMSEL MEASURE

/***
 *	Global variable declarations
 *
 *	Array Phase stores the microstructure representation
 *	Array Curvature stores the local mean curvature values
 *	Vectors Xsph, Ysph, and Zsph store the x, y, and z
 *		positions of the template sphere pixels
 *	Vectors Nsolid and Nair store the histogram information
 *	Nsph is the number of pixels in the template
 *	Tradius is the radius of the template sphere
 *
 ***/

int ***Mic;
int *Seed;

/***
 *	System size (pixels per edge), and
 *	resolution (micrometers per pixel)
 ***/

int Syspix = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
float Res = DEFAULTRESOLUTION;
float Sizemag = 1.0;
int Isizemag = 1;
float Resmag = 1.0;
int Iresmag = 1;

/* VCCTL software version used to create input file */
float Version;

/* Verbose output flag */
int Verbose = 0;

/***
 *	Function declarations
 ***/

void checkargs(int argc, char *argv[]);
int maketemp(int size, int *xsph, int *ysph, int *zsph);
int poredist(char *filename);
int xyz2pix(int xpos, int ypos, int zpos);
int pix2x(int pid);
int pix2y(int pid);
int pix2z(int pid);
void readmic(char *filen);

int main(int argc, char *argv[]) {
  int nseed, menuch, status;
  char instring[MAXSTRING], filename[MAXSTRING];

  checkargs(argc, argv);

  sprintf(filename, " ");
  printf("Enter random number seed (integer < 0): \n");
  read_string(instring, sizeof(instring));
  nseed = atoi(instring);
  if (nseed > 0)
    nseed = (-1 * nseed);
  printf("%d \n", nseed);
  Seed = &nseed;

  menuch = NUMSEL + 1;

  /* Present menu and obtain user choice */

  while (menuch != EXIT) {
    printf("Enter choice: \n");
    printf("%d) Exit program \n", EXIT);
    printf("%d) Read in microstructure from file \n", READMIC);
    printf("%d) Measure poresize distribution \n", MEASURE);
    read_string(instring, sizeof(instring));
    menuch = atoi(instring);
    printf("%d \n", menuch);

    switch (menuch) {
    case READMIC:
      readmic(filename);
      break;
    case MEASURE:
      status = poredist(filename);
      break;
    default:
      break;
    }
  }

  return (0);
}

/***
 *	maketemp
 *
 *	Routine to create a template for the sphere of
 *	interest of radius size to be used in
 *	curvature evaluation
 *
 * 	Arguments:	int size (the radius of the sphere)
 * 	            int pointer to xsph vector
 * 	            int pointer to ysph vector
 * 	            int pointer to zsph vector
 * 	Returns:	int number of pixels in sphere
 *
 *	Calls:		no other routines
 *	Called by:	runsint
 ***/
int maketemp(int size, int *xsph, int *ysph, int *zsph) {
  int icirc, xval, yval, zval;
  float xtmp, ytmp, dist;

  /***
   *	Determine and store the locations of all
   *	pixels in the 3-D sphere
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
   *	Return the number of pixels contained in
   *	sphere of radius (size+0.5)
   ***/

  return (icirc);
}

/***
 *	xyz2pix
 *
 *	Convert x,y,z coordinates to pixel number
 *
 * 	Arguments:	int xpos, int ypos, int zpos coordinates
 * 	Returns:	int pixel id number
 *
 *	Calls:		no other routines
 *	Called by:	readmic
 ***/
int xyz2pix(int xpos, int ypos, int zpos) {
  int ns = (Xsyssize * Ysyssize * zpos) + (Xsyssize * ypos) + xpos;
  return (ns);
}

/***
 *	pix2x
 *
 *	Convert pixel id number to x coordinate
 *
 * 	Arguments:	int pixel id number
 * 	Returns:	int x coordinate
 *
 *	Calls:		no other routines
 *	Called by:	readmic
 ***/
int pix2x(int pid) {
  int x, y, z;
  z = pid / (Xsyssize * Ysyssize);
  y = (pid - (z * Xsyssize * Ysyssize)) / Xsyssize;
  x = (pid - (z * Xsyssize * Ysyssize) - (y * Xsyssize));
  return (x);
}

/***
 *	pix2y
 *
 *	Convert pixel id number to y coordinate
 *
 * 	Arguments:	int pixel id number
 * 	Returns:	int x coordinate
 *
 *	Calls:		no other routines
 *	Called by:	readmic
 ***/
int pix2y(int pid) {
  int y, z;
  z = pid / (Xsyssize * Ysyssize);
  y = (pid - (z * Xsyssize * Ysyssize)) / Xsyssize;
  return (y);
}

/***
 *	pix2z
 *
 *	Convert pixel id number to z coordinate
 *
 * 	Arguments:	int pixel id number
 * 	Returns:	int x coordinate
 *
 *	Calls:		no other routines
 *	Called by:	readmic
 ***/
int pix2z(int pid) {
  int z = pid / (Xsyssize * Ysyssize);
  return (z);
}

/***
 *   poredist
 *
 *	Routine to simulate mercury intrusion
 *
 * 	Arguments:	Filename root for data output
 * 	Returns:	status
 *
 *	Calls:		no other routines
 *	Called by:	main program
 ***/
int poredist(char *filename) {
  int i, *nrad, porecnt, maxsph, nsph, l, ntot, nact, naccessible;
  int ix, iy, iz, max_allowed_rad, mindim, nr, failed;
  int xl, yl, zl, diam;
  int ***tmic;
  int *xsph, *ysph, *zsph;
  int klh, xkl[7], xkh[7], ykl[7], ykh[7], zkl[7], zkh[7];
  size_t ssize;
  FILE *outfile;

  for (ix = 0; ix < 7; ix++) {
    xkl[ix] = xkh[ix] = ykl[ix] = ykh[ix] = zkl[ix] = zkh[ix] = 0;
  }

  nrad = NULL;

  /* Linked list data structure for set of intrudable elements */

  struct sitelist {
    short int xp, yp, zp;
    struct sitelist *nextsite;
  };
  struct sitelist *oldsite, *newsite, *newlist, *oldlist;

  ssize = (size_t)(sizeof(struct sitelist));

  /* Allocate memory for temporary microstructure image */

  tmic = ibox(Xsyssize + 1, Ysyssize + 1, Zsyssize + 1);
  if (!tmic) {
    warning("poredist3d", "Could not allocate required memory for temporary "
                          "microstructure image");
    return (1);
  }

  porecnt = 0;
  naccessible = 0;
  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {
        if (Mic[ix][iy][iz] == POROSITY || Mic[ix][iy][iz] == EMPTYP ||
            Mic[ix][iy][iz] == EMPTYDP || Mic[ix][iy][iz] == CRACKP) {
          tmic[ix][iy][iz] = POROSITY;
          porecnt++;
        } else {
          tmic[ix][iy][iz] = 10000;
        }
      }
    }
  }

  if (Verbose) {
    printf("\nScanned microstructure:  total pore count = %d", porecnt);
    fflush(stdout);
  }

  mindim = Xsyssize;
  if (Ysyssize < mindim)
    mindim = Ysyssize;
  if (Zsyssize < mindim)
    mindim = Zsyssize;

  if (Verbose) {
    printf("\nMinimum dimension of system is %d", mindim);
    fflush(stdout);
  }

  max_allowed_rad = (int)(0.1 * mindim);

  if (Verbose) {
    printf("\nMaximum probed pore diameter will be %d", max_allowed_rad);
    fflush(stdout);
  }

  /* Allocate memory for nrad vector */
  nrad = ivector(max_allowed_rad + 1);
  if (!nrad) {
    warning("poredist3d", "Could not allocate required memory");
    free_ibox(tmic, Xsyssize + 1, Ysyssize + 1);
    return (1);
  }

  /* Ensure that diameter is odd */
  maxsph = diam2vol((float)(2 * max_allowed_rad + 1));

  if (Verbose) {
    printf("\nMaximum number allowed template elements will be %d", maxsph);
    fflush(stdout);
  }

  /* Allocate memory for xsph,ysph, and zsph vectors */
  xsph = ivector(maxsph);
  if (!xsph) {
    warning("poredist3d", "Could not allocate required memory");
    free_ivector(nrad);
    free_ibox(tmic, Xsyssize + 1, Ysyssize + 1);
    return (1);
  }
  ysph = ivector(maxsph);
  if (!ysph) {
    warning("poredist3d", "Could not allocate required memory");
    free_ivector(xsph);
    free_ivector(nrad);
    free_ibox(tmic, Xsyssize + 1, Ysyssize + 1);
    return (1);
  }
  zsph = ivector(maxsph);
  if (!zsph) {
    warning("poredist3d", "Could not allocate required memory");
    free_ivector(ysph);
    free_ivector(xsph);
    free_ivector(nrad);
    free_ibox(tmic, Xsyssize + 1, Ysyssize + 1);
    return (1);
  }

  if (Verbose) {
    printf("\nDone allocating xsph, ysph, and zsph vectors");
    fflush(stdout);
  }

  /* Initialize the nrad vector */

  for (i = 0; i <= max_allowed_rad; i++)
    nrad[i] = 0;

  /* Start with smallest allowed pore radius */

  if (Verbose) {
    printf("\nStarting pore distribution scan...");
    fflush(stdout);
  }

  for (nr = max_allowed_rad; nr >= 0; nr--) {

    nsph = maketemp(nr, xsph, ysph, zsph);
    if (Verbose) {
      printf("\n\tRadius = %d, Nsph = %d", nr, nsph);
      fflush(stdout);
    }

    /* Define boundary coordinates of six faces of cube */

    xkl[1] = (-nr - 1);
    xkh[1] = Xsyssize + nr;
    ykl[1] = (-nr - 1);
    ykh[1] = Ysyssize + nr;
    zkl[1] = (-nr - 1);
    zkh[1] = (-1);
    xkl[2] = (-nr - 1);
    xkh[2] = Xsyssize + nr;
    ykl[2] = (-nr - 1);
    ykh[2] = Ysyssize + nr;
    zkl[2] = Zsyssize;
    zkh[2] = Zsyssize + nr;
    xkl[3] = (-nr - 1);
    xkh[3] = Xsyssize + nr;
    ykl[3] = (-nr - 1);
    ykh[3] = (-1);
    zkl[3] = 0;
    zkh[3] = (Zsyssize - 1);
    xkl[4] = (-nr - 1);
    xkh[4] = Xsyssize + nr;
    ykl[4] = Ysyssize;
    ykh[4] = Ysyssize + nr;
    zkl[4] = 0;
    zkh[4] = (Zsyssize - 1);
    xkl[5] = (-nr - 1);
    xkh[5] = (-1);
    ykl[5] = 0;
    ykh[5] = (Ysyssize - 1);
    zkl[5] = 0;
    zkh[5] = (Zsyssize - 1);
    xkl[6] = Xsyssize;
    xkh[6] = Xsyssize + nr;
    ykl[6] = 0;
    ykh[6] = (Ysyssize - 1);
    zkl[6] = 0;
    zkh[6] = (Zsyssize - 1);

    ntot = 0;

    newlist = (struct sitelist *)malloc(ssize);
    newlist->xp = (-1);
    newlist->yp = (-1);
    newlist->zp = (-1);
    newlist->nextsite = NULL;

    nact = 0;

    /* Intrude from one face only */

    for (klh = 1; klh <= 1; klh++) {
      for (ix = xkl[klh]; ix <= xkh[klh]; ix++) {
        for (iy = ykl[klh]; iy <= ykh[klh]; iy++) {
          for (iz = zkl[klh]; iz <= zkh[klh]; iz++) {
            failed = 0;
            /* check if intrusion is possible at this size */
            for (l = 1; ((l <= nsph) && (!failed)); l++) {
              xl = ix + xsph[l];
              yl = iy + ysph[l];
              zl = iz + zsph[l];
              xl += checkbc(xl, Xsyssize);
              yl += checkbc(yl, Ysyssize);
              zl += checkbc(zl, Zsyssize);
              if (tmic[xl][yl][zl] > OFFSET)
                failed = 1;
            }

            if (!failed) {
              for (l = 1; ((l <= nsph) && (!failed)); l++) {
                xl = ix + xsph[l];
                yl = iy + ysph[l];
                zl = iz + zsph[l];
                xl += checkbc(xl, Xsyssize);
                yl += checkbc(yl, Ysyssize);
                zl += checkbc(zl, Zsyssize);
                if (tmic[xl][yl][zl] == POROSITY) {
                  ntot++;
                  nact++;
                  tmic[xl][yl][zl] = POROSITY + 1;
                  /* add this location to the linked list of initial sites */
                  newsite = (struct sitelist *)malloc(ssize);
                  newsite->xp = xl;
                  newsite->yp = yl;
                  newsite->zp = zl;
                  newsite->nextsite = newlist;
                  newlist = newsite;
                }
              }
            }
          }
        }
      }
    }

    /* Intrude active sets as long as they are not empty */

    while (newlist->xp != (-1)) {

      /* Copy the active set to oldlist */

      oldlist = newlist;

      /* Initialize a new linked list to hold new sites */
      newlist = (struct sitelist *)malloc(ssize);
      newlist->xp = (-1);
      newlist->yp = (-1);
      newlist->zp = (-1);
      newlist->nextsite = NULL;
      while (oldlist->xp != (-1)) {

        /* remove the next location to be checked from the old list */

        ix = oldlist->xp;
        iy = oldlist->yp;
        iz = oldlist->zp;
        oldsite = oldlist;
        oldlist = oldlist->nextsite;
        free(oldsite);
        failed = 0;

        /* check for further intrusion */

        for (l = 1; ((l <= nsph) && (!failed)); l++) {
          xl = ix + xsph[l];
          yl = iy + ysph[l];
          zl = iz + zsph[l];
          xl += checkbc(xl, Xsyssize);
          yl += checkbc(yl, Ysyssize);
          zl += checkbc(zl, Zsyssize);
          if (tmic[xl][yl][zl] != POROSITY)
            failed = 1;
        }

        if (!failed) {
          for (l = 1; ((l <= nsph) && (!failed)); l++) {
            xl = ix + xsph[l];
            yl = iy + ysph[l];
            zl = iz + zsph[l];
            xl += checkbc(xl, Xsyssize);
            yl += checkbc(yl, Ysyssize);
            zl += checkbc(zl, Zsyssize);
            if (tmic[xl][yl][zl] == POROSITY) {
              ntot++;
              nact++;
              tmic[xl][yl][zl] = POROSITY + 1;
              /* add this location to the linked list of initial sites */
              newsite = (struct sitelist *)malloc(ssize);
              newsite->xp = xl;
              newsite->yp = yl;
              newsite->zp = zl;
              newsite->nextsite = newlist;
              newlist = newsite;
            }
          }
        }
      }

      free(oldlist);
    }

    nrad[nr] = ntot;
    naccessible += ntot;
    if (Verbose) {
      printf("\nRadius is %d and nrad[%d] = %d", nr, nr, ntot);
      fflush(stdout);
    }
  }

  if (Verbose) {
    printf("\nDone with scan.");
    fflush(stdout);
  }

  strcat(filename, ".poredist");
  outfile = filehandler("poredist3d", filename, "WRITE");
  if (!outfile) {
    warning("poredist3d", "Could not open output file");
    fflush(stdout);
    free_ivector(zsph);
    free_ivector(ysph);
    free_ivector(xsph);
    free_ivector(nrad);
    free_ibox(tmic, Xsyssize + 1, Ysyssize + 1);
    return (1);
  }

  fprintf(outfile, "Total pore volume = %f um^3", ((float)porecnt));
  fprintf(outfile, "\nAccessible pore volume = %f um^3", ((float)naccessible));
  fprintf(outfile, "\n\nDiameter_(um)\tNumber\tFraction");
  if (Verbose) {
    printf("\n\nTotal pore volume = %f um^3", ((float)porecnt));
    printf("\nAccessible pore volume = %f um^3", ((float)naccessible));
    printf("\n\nDiameter_(um)\tNumber\tFraction");
    fflush(stdout);
  }
  for (i = 0; i <= max_allowed_rad; i++) {
    diam = 2 * i + 1;
    fprintf(outfile, "\n%f\t%d\t%f", ((float)diam), nrad[i],
            (((float)nrad[i]) / ((float)naccessible)));
    if (Verbose) {
      printf("\n%f\t%d\t%f", ((float)diam), nrad[i],
             (((float)nrad[i]) / ((float)naccessible)));
      fflush(stdout);
    }
  }

  fclose(outfile);

  free_ivector(zsph);
  free_ivector(ysph);
  free_ivector(xsph);
  free_ivector(nrad);
  free_ibox(tmic, Xsyssize + 1, Ysyssize + 1);

  return (0);
}

/***
 *	readmic
 *
 *	Routine to read microstructure from a file
 *
 *	Also allocates memory for global arrays
 *
 * 	Arguments:	File name to open
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main
 ***/
void readmic(char *filen) {
  register int i1, i2, i3;
  int iout, oiout;
  char instring[MAXSTRING];
  FILE *infile;

  printf("Enter name of file to read in \n");
  read_string(filen, sizeof(filen));
  infile = filehandler("poredist3d", filen, "READ");
  if (!infile) {
    exit(1);
  }

  /***
   *	Determine whether system size and resolution
   *	are specified in the image file
   ***/

  if (read_imgheader(infile, &Version, &Xsyssize, &Ysyssize, &Zsyssize, &Res)) {
    fclose(infile);
    bailout("poredist3d", "Error reading image header");
    exit(1);
  }

  if (Verbose) {
    printf("\nXsyssize is %d", Xsyssize);
    printf("\nYsyssize is %d", Ysyssize);
    printf("\nZsyssize is %d\n", Zsyssize);
    printf("Res is %f\n", Res);
    fflush(stdout);
  }

  /***
   *	Define the number of histogram bins
   ***/

  Syspix = Xsyssize * Ysyssize * Zsyssize;
  Sizemag =
      pow(((float)Syspix) / (pow(((float)DEFAULTSYSTEMSIZE), 3.0)), (1. / 3.));
  Isizemag = (int)(Sizemag + 0.5);
  Resmag = ((float)DEFAULTRESOLUTION) / Res;
  Iresmag = (int)(Resmag + 0.5);

  /***
   *	Allocate memory for all global variables
   ***/

  Mic = ibox(Xsyssize + 1, Ysyssize + 1, Zsyssize + 1);

  if (!Mic) {
    bailout("poredist3d", "Memory allocation failure");
    fflush(stdout);
    exit(1);
  }

  /***
   *	Read the microstructure file
   ***/

  for (i3 = 0; i3 < Zsyssize; i3++) {
    for (i2 = 0; i2 < Ysyssize; i2++) {
      for (i1 = 0; i1 < Xsyssize; i1++) {
        fscanf(infile, "%s", instring);
        oiout = atoi(instring);
        iout = convert_id(oiout, Version);
        Mic[i1][i2][i3] = iout;
      }
    }
  }

  fclose(infile);

  return;
}

/***
 *   checkargs
 *
 * 	Checks command-line arguments
 *
 * 	Arguments:	int argc, char *argv[]
 * 	Returns:	nothing
 *
 *	Calls:		no routines
 *	Called by:	main program
 ***/
void checkargs(int argc, char *argv[]) {
  register unsigned int i;

  /* Is verbose output requested? */

  Verbose = 0;
  for (i = 1; i < argc; i++) {
    if ((!strcmp(argv[i], "-v")) || (!strcmp(argv[i], "--verbose")))
      Verbose = 1;
  }
}
