/****************************************************************
 *
 * Program poredist3d.c
 * To measure the pore size distribution of a
 * 3D VCCTL microstructure
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
char Filename[MAXSTRING];

/* VCCTL software version used to create input file */
float Version;

/* Verbose output flag */
int Verbose = 0;

/***
 *	Function declarations
 ***/

void checkargs(int argc, char *argv[]);
int maketemp(int size, int *xsph, int *ysph, int *zsph);
int poredist(void);
int xyz2pix(int xpos, int ypos, int zpos);
int pix2x(int pid);
int pix2y(int pid);
int pix2z(int pid);
void readmic(void);

int main(int argc, char *argv[]) {
  int nseed, menuch, status;
  char instring[MAXSTRING];

  checkargs(argc, argv);

  sprintf(Filename, " ");
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
      readmic();
      break;
    case MEASURE:
      status = poredist();
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
 *	Routine to count phase fractions (porosity
 *	and solids)
 *
 * 	Arguments:	Filename root for data output
 * 	Returns:	status
 *
 *	Calls:		no other routines
 *	Called by:	main program
 ***/
int poredist(void) {
  int i, *pores, *ndiam, porecnt, index, ns, maxsph, nsph;
  int ix, iy, iz, max_allowed_diam, mindim, nd, failed, nrad;
  int xc, yc, zc;
  int ***tmic;
  int *xsph, *ysph, *zsph;
  FILE *outfile;

  /* Allocate memory for temporary microstructure image */

  pores = NULL;
  ndiam = NULL;
  tmic = NULL;
  xsph = NULL;
  ysph = NULL;
  zsph = NULL;
  tmic = ibox(Xsyssize + 1, Ysyssize + 1, Zsyssize + 1);
  if (!tmic) {
    warning("poredist3d", "Could not allocate required memory for temporary "
                          "microstructure image");
    return (1);
  }

  porecnt = 0;
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

  max_allowed_diam = (int)(0.2 * mindim);

  if (Verbose) {
    printf("\nMaximum probed pore diameter will be %d", max_allowed_diam);
    fflush(stdout);
  }

  /* Allocate memory for ndiam vector */
  ndiam = ivector(max_allowed_diam + 1);
  if (!ndiam) {
    warning("poredist3d", "Could not allocate required memory");
    free_ibox(tmic, Xsyssize + 1, Ysyssize + 1);
    return (1);
  }

  /* Ensure that diameter is odd */
  if (max_allowed_diam % 2 == 0)
    max_allowed_diam++;
  maxsph = diam2vol((float)max_allowed_diam);

  if (Verbose) {
    printf("\nMaximum number allowed template elements will be %d", maxsph);
    fflush(stdout);
  }

  /* Allocate memory for xsph,ysph, and zsph vectors */
  xsph = ivector(maxsph);
  if (!xsph) {
    warning("poredist3d", "Could not allocate required memory");
    free_ivector(ndiam);
    free_ibox(tmic, Xsyssize + 1, Ysyssize + 1);
    return (1);
  }
  ysph = ivector(maxsph);
  if (!ysph) {
    warning("poredist3d", "Could not allocate required memory");
    free_ivector(xsph);
    free_ivector(ndiam);
    free_ibox(tmic, Xsyssize + 1, Ysyssize + 1);
    return (1);
  }
  zsph = ivector(maxsph);
  if (!zsph) {
    warning("poredist3d", "Could not allocate required memory");
    free_ivector(ysph);
    free_ivector(xsph);
    free_ivector(ndiam);
    free_ibox(tmic, Xsyssize + 1, Ysyssize + 1);
    return (1);
  }

  if (Verbose) {
    printf("\nDone allocating xsph, ysph, and zsph vectors");
    fflush(stdout);
  }

  /* Allocate memory for porosity locator vector */

  pores = ivector(porecnt);
  if (!pores) {
    warning("poredist3d", "Could not allocate required memory");
    fflush(stdout);
    free_ivector(zsph);
    free_ivector(ysph);
    free_ivector(xsph);
    free_ivector(ndiam);
    free_ibox(tmic, Xsyssize + 1, Ysyssize + 1);
    return (1);
  }

  /* Load up the locator vector */

  index = 0;
  ns = 0;
  for (iz = 0; iz < Zsyssize && index < porecnt; iz++) {
    for (iy = 0; iy < Ysyssize && index < porecnt; iy++) {
      for (ix = 0; ix < Xsyssize && index < porecnt; ix++) {
        if (Mic[ix][iy][iz] == POROSITY || Mic[ix][iy][iz] == EMPTYP ||
            Mic[ix][iy][iz] == EMPTYDP || Mic[ix][iy][iz] == CRACKP) {
          pores[index] = ns;
          index++;
        }
        ns++;
      }
    }
  }

  if (Verbose) {
    printf("\nIndex = %d", index);
    fflush(stdout);
  }

  /* Initialize the ndiam vector */

  for (i = 0; i <= max_allowed_diam; i++)
    ndiam[i] = 0;

  /* Start with largest allowed pore diameter */

  if (Verbose) {
    printf("\nStarting pore distribution scan...");
    fflush(stdout);
  }

  for (nd = max_allowed_diam; nd >= 1; nd -= 2) {

    nrad = nd / 2;
    nsph = maketemp(nrad, xsph, ysph, zsph);
    if (Verbose) {
      printf("\n\tDiam = %d, Nsph = %d", nd, nsph);
      fflush(stdout);
    }

    /* Check all pore pixels in the 3-D system */

    for (index = 0; index < porecnt; index++) {
      xc = pix2x(pores[index]);
      yc = pix2y(pores[index]);
      zc = pix2z(pores[index]);
      if (tmic[xc][yc][zc] == POROSITY) {
        failed = 0;
        for (i = 0; (i < nsph) && (!failed); i++) {
          ix = xc + xsph[i];
          iy = yc + ysph[i];
          iz = zc + zsph[i];
          ix += checkbc(ix, Xsyssize);
          iy += checkbc(iy, Ysyssize);
          iz += checkbc(iz, Zsyssize);
          if (tmic[ix][iy][iz] > max_allowed_diam)
            failed = 1;
        }
        if (!failed) {
          for (i = 0; i < nsph; i++) {
            ix = xc + xsph[i];
            iy = yc + ysph[i];
            iz = zc + zsph[i];
            ix += checkbc(ix, Xsyssize);
            iy += checkbc(iy, Ysyssize);
            iz += checkbc(iz, Zsyssize);
            if (tmic[ix][iy][iz] < nd) {
              tmic[ix][iy][iz] = nd;
              ndiam[nd]++;
            }
          }
        }
      }
    }
  }

  if (Verbose) {
    printf("\nDone with scan.");
    fflush(stdout);
  }

  strcat(Filename, ".poredist");
  outfile = filehandler("poredist3d", Filename, "WRITE");
  if (!outfile) {
    warning("poredist3d", "Could not open output file");
    fflush(stdout);
    free_ivector(zsph);
    free_ivector(ysph);
    free_ivector(xsph);
    free_ivector(ndiam);
    free_ibox(tmic, Xsyssize + 1, Ysyssize + 1);
    return (1);
  }

  fprintf(outfile, "Total pore volume = %f um^3", ((float)porecnt));
  fprintf(outfile, "\n\nDiameter_(um)\tNumber\tFraction");
  if (Verbose) {
    printf("\n\nTotal pore volume = %f um^3", ((float)porecnt));
    printf("\n\nDiameter_(um)\tNumber\tFraction");
    fflush(stdout);
  }
  for (i = 1; i <= max_allowed_diam; i += 2) {
    fprintf(outfile, "\n%f\t%d\t%f", ((float)i), ndiam[i],
            (((float)ndiam[i]) / ((float)porecnt)));
    if (Verbose) {
      printf("\n%f\t%d\t%f", ((float)i), ndiam[i],
             (((float)ndiam[i]) / ((float)porecnt)));
      fflush(stdout);
    }
  }

  fclose(outfile);

  free_ivector(pores);
  free_ivector(zsph);
  free_ivector(ysph);
  free_ivector(xsph);
  free_ivector(ndiam);
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
void readmic(void) {
  register int i1, i2, i3;
  int iout, oiout;
  char instring[MAXSTRING];
  FILE *infile;

  printf("Enter name of file to read in \n");
  read_string(Filename, sizeof(Filename));
  infile = filehandler("poredist3d", Filename, "READ");
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
