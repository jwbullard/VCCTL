/******************************************************
 *
 * Program distrib3d.c to distribute cement clinker
 * phases in agreement with experimentally obtained
 * 2-point correlation functions for each phase.
 *
 * Particles are composed of either cement clinker or gypsum,
 * follow a user-specified size distribution, and can be
 * either flocculated, random, or dispersed.  Phase
 * distribution occurs only within the cement clinker particles
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
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Default resolution of correlation function file */
#define DEFAULTCORRRES 1.00

/* string delineating resolution in correlation file */
#define CORRRESSTRING "Resolution:"

/* Default size of cubic filter template */
#define FILTERSIZE 31

/* maximum number of phases possible */
#define MAXNUMPHASES OFFSET

/* Default number of histogram bins */
#define HISTSIZE 500

/***
 *	Parameter for comparing the difference
 *	between two floats
 ***/

#define EPS 1.0e-6

/***
 *	Mathematical parameters/definitions
 ***/

#define PI 3.1415926

/***
 *	Global variable declarations:
 ***/
int *Seed;
int Fsize = FILTERSIZE;
int Syspix = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
int Hsize = HISTSIZE;
float Res = DEFAULTRESOLUTION;
float Sizemag = 1.0;
float Isizemag = 1;
int *R, ***Mask;
float *S, *Xr, *Sum, ***Filter, ***Normm, ***Rres;
float Vcrit;

/* VCCTL software version used to create input file */
float Version;

/***
 *	Function declarations
 ***/

int runrand3d(int phasein, int phaseout, char filecorr[MAXSTRING], float xpt,
              int *r, float ***filter, float *s, float *xr);
void freeallmem(void);

int main(void) {
  register int i, j, k;
  int iseed, ires, valin, ovalin, phasein, phaseout;
  float volin;
  char filen[MAXSTRING], filem[MAXSTRING], instring[MAXSTRING];
  char filecorr[MAXSTRING];
  FILE *infile, *outfile;

  /* Get user input */

  printf("Enter random number seed (negative integer) \n");
  read_string(instring, sizeof(instring));
  iseed = atoi(instring);
  if (iseed > 0)
    iseed = (-1 * iseed);
  printf("%d\n", iseed);
  Seed = &iseed;

  printf("Enter existing phase assignment for matching\n");
  read_string(instring, sizeof(instring));
  phasein = atoi(instring);
  printf("%d\n", phasein);
  printf("Enter phase assignment to be created by program\n");
  read_string(instring, sizeof(instring));
  phaseout = atoi(instring);
  printf("%d\n", phaseout);

  printf("Enter name of cement microstructure image file\n");
  read_string(filen, sizeof(filen));
  printf("%s\n", filen);

  printf("Enter filename to read in autocorrelation from\n");
  read_string(filecorr, sizeof(filecorr));
  printf("%s\n", filecorr);

  printf("Input desired threshold phase fraction\n");
  read_string(instring, sizeof(instring));
  volin = atof(instring);
  printf("%f\n", volin);

  printf("Enter name of new cement microstructure image file\n");
  read_string(filem, sizeof(filem));
  printf("%s\n", filem);

  /* Read in the original microstructure image file */

  infile = filehandler("rand3d", filen, "READ");
  if (!infile) {
    exit(1);
  }

  /***
   *	Determine whether version number, system size
   *	and resolution are specified in the image file
   ***/

  if (read_imgheader(infile, &Version, &Xsyssize, &Ysyssize, &Zsyssize, &Res)) {
    fclose(infile);
    bailout("rand3d", "Error reading image header");
    freeallmem();
    exit(1);
  }

  printf("\nXsyssize is %d", Xsyssize);
  printf("\nYsyssize is %d", Ysyssize);
  printf("\nZsyssize is %d\n", Zsyssize);
  printf("Res is %f\n", Res);
  fflush(stdout);

  /***
   *	Define the filter size now.  For standard resolution
   *	the filter size is 31.  Scale the standard size by
   *	the actual resolution
   *
   *	Also define the number of histogram bins
   ***/

  Syspix = Xsyssize * Ysyssize * Zsyssize;
  Sizemag =
      pow(((float)Syspix) / (pow(((float)DEFAULTSYSTEMSIZE), 3.0)), (1. / 3.));
  Isizemag = (int)(Sizemag + 0.5);
  Fsize = (int)(((float)FILTERSIZE) / Res);
  Hsize = HISTSIZE;

  /***
   *	Allocate memory for all global variables
   ***/

  R = ivector(2 * Fsize);
  S = fvector(2 * Fsize);
  Xr = fvector(2 * Fsize);
  Filter = fcube(Fsize + 1);
  Mask = ibox(Xsyssize + 1, Ysyssize + 1, Zsyssize + 1);
  Sum = fvector(Hsize + 2);
  Normm = fbox(Xsyssize + 1, Ysyssize + 1, Zsyssize + 1);
  Rres = fbox(Xsyssize + 1, Ysyssize + 1, Zsyssize + 1);

  if (!R || !S || !Xr || !Filter || !Mask || !Sum || !Normm || !Rres) {

    freeallmem();
    bailout("rand3d", "Memory allocation error");
    fflush(stdout);
    exit(1);
  }

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {
        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valin = convert_id(ovalin, Version);
        Mask[i][j][k] = valin;
      }
    }
  }

  fclose(infile);

  if (runrand3d(phasein, phaseout, filecorr, volin, R, Filter, S, Xr)) {
    freeallmem();
    bailout("rand3d", "Problem with runrand3d");
    exit(1);
  }

  outfile = filehandler("rand3d", filem, "WRITE");
  if (!outfile) {
    freeallmem();
    exit(1);
  }

  /***
   *	Output the software version to the final
   *	microstructure
   ***/

  if (write_imgheader(outfile, Xsyssize, Ysyssize, Zsyssize, Res)) {
    fclose(outfile);
    freeallmem();
    bailout("rand3d", "Error writing image header");
    exit(1);
  }

  ires = 0;

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 1; i < Xsyssize; i++) {

        if (Mask[i][j][k] == phasein) {

          if (Rres[i][j][k] > Vcrit) {
            Rres[i][j][k] = (float)phaseout;
          } else {
            Rres[i][j][k] = (float)phasein;
            ires++;
          }

        } else {
          Rres[i][j][k] = (float)Mask[i][j][k];
        }

        fprintf(outfile, "%2d\n", (int)Rres[i][j][k]);
      }
    }
  }

  fclose(outfile);
  freeallmem();

  return (0);
}

/***
 *	runrand3d
 *
 *	Routine to generate a Gaussian random noise image and
 *	then filter it according to the 2-point correlation function
 *	for the phase of interest
 *
 *	Arguments:	Phase ID in, Phase ID out, correlation filename,
 *				int number of strings to skip (due to possible
 *				header line for resolution information),
 *				float xpt=volume fraction, r[] is the array of
 *				radius values in corr file, filter[][][] is the
 *				3D filter array, s[] is the value of the
 *correlation function at a given (radial) position, xr[] is the float version
 *of r[]
 *
 *	Returns:	0 if normal execution, non-zero if error occurred
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
int runrand3d(int phasein, int phaseout, char filecorr[MAXSTRING], float xpt,
              int *r, float ***filter, float *s, float *xr) {
  register int i, j, k, ix, iy, iz;
  int done, step, ilo, ihi;
  int valin, pvalin, r1, r2, i1, i2, i3, j1, k1;
  int ido, iii, jjj, index;
  int xtot;
  float s2, ss, sdiff, xtmp, ytmp, slope, intercept, diff;
  float val2, t1, t2, x1, x2, u1, u2, xrad, resmax, resmin;
  float filval, radius, sect, sumtot, corr_res;
  char buff[MAXSTRING], instring[MAXSTRING];
  FILE *corrfile;

  /***
   *	Create the Gaussian noise image
   ***/

  i1 = i2 = i3 = 0;

  for (i = 0; i < Xsyssize * Ysyssize * Zsyssize / 2; i++) {

    u1 = ran1(Seed);
    u2 = ran1(Seed);
    t1 = 2.0 * PI * u2;
    t2 = sqrt(-2.0 * log(u1));
    x1 = cos(t1) * t2;
    x2 = sin(t1) * t2;
    Normm[i1][i2][i3] = x1;

    i1++;
    if (i1 >= Xsyssize) {
      i1 = 0;
      i2++;
      if (i2 >= Ysyssize) {
        i2 = 0;
        i3++;
      }
    }

    Normm[i1][i2][i3] = x2;

    i1++;
    if (i1 >= Xsyssize) {
      i1 = 0;
      i2++;
      if (i2 >= Ysyssize) {
        i2 = 0;
        i3++;
      }
    }
  }

  /* Now perform the convolution */

  corrfile = filehandler("rand3d", filecorr, "READ");
  if (!corrfile) {
    return (1);
  }

  /*** Skip over resolution information if it is given ***/

  fscanf(corrfile, "%s", buff);
  if (!strcmp(buff, CORRRESSTRING)) {
    fscanf(corrfile, "%s", instring);
    corr_res = atof(instring);
  } else {

    /***
     *	No resolution was specified.  Default the resolution
     *	to DEFAULTCORRRES to be backwards compatible with
     *	VCCTL Ver 2.0
     ***/

    corr_res = DEFAULTCORRRES;
    rewind(corrfile);
  }

  fscanf(corrfile, "%s", instring);
  ido = atoi(instring);
  printf("\n\tNumber of points in correlation file is %d \n", ido);
  fflush(stdout);

  /***
   *	When reading in the correlation file, must make
   *	the resolution of the correlation function
   *	compatible with the resolution of the system
   *	as specified by global variable Res
   ***/

  for (i = 0; i < ido; i++) {
    fscanf(corrfile, "%d %f", &valin, &val2);

    /***
     *	valin is the radial distance in micrometers.
     *	Convert it to pixels using Res and corr_res
     ***/

    pvalin = (int)((((float)valin) * (corr_res / Res)) + 0.40);
    /* r[pvalin] = (int)(((float)valin)*corr_res); */
    r[pvalin] = pvalin;
    s[pvalin] = val2;
    xr[pvalin] = (float)r[pvalin];
  }

  fclose(corrfile);

  /***
   *	Now linearly interpolate the other values,
   *	depending on the value of Res
   ***/

  step = (int)(corr_res / Res);
  diff = (float)step;
  if (Res < LOWRES - 0.05 && step > 0) {
    for (j = 0; j < ido; j++) {
      ilo = step * j;
      ihi = step * (j + 1);
      slope = (s[ihi] - s[ilo]) / diff;
      intercept = s[ilo];
      for (i = 1; i < step; i++) {
        s[ilo + i] = intercept;
        s[ilo + i] += slope * ((float)i);
        xr[i + ilo] = xr[ilo] + ((float)i);
        r[i + ilo] = r[ilo] + i;
      }
    }
  }

  /* Load up the convolution matrix */

  ss = s[0];
  s2 = ss * ss;
  sdiff = ss - s2;
  printf("\n\tss = %f  s2 = %f  sdiff = %f", ss, s2, sdiff);
  fflush(stdout);
  for (i = 0; i < Fsize; i++) {
    iii = i * i;
    for (j = 0; j < Fsize; j++) {
      jjj = j * j;
      for (k = 0; k < Fsize; k++) {
        xtmp = (float)(iii + jjj + k * k);
        radius = sqrt(xtmp);
        r1 = (int)(radius);
        r2 = r1 + 1;
        if (s[r1] < 0.0) {
          printf("ERROR in distrib3d, fn. rand3d:\n");
          printf("\t%d and %d, %f and ", r1, r2, s[r1]);
          printf("%f with xtmp of %f\n", s[r2], xtmp);
          fflush(stdout);
          return (3);
        }

        xrad = radius - r1;

        /***
         *	Interpolate the correlation function
         *	between the two values at r2 and r1, for
         *	which it is known, to estimate its value
         *	at some r for which r1 <= r <= r2
         *
         *	We also normalize the value of filter to
         *	the value of the correlation file at 0.
         ***/

        filval = s[r1] + (s[r2] - s[r1]) * xrad;
        filter[i][j][k] = (filval - s2) / sdiff;
      }
    }
  }

  /* Now filter the image, maintaining periodic boundaries */

  printf("\n\tDone loading up the convolution matrix.");
  fflush(stdout);
  resmax = 0.0;
  resmin = 1.0;

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        Rres[i][j][k] = 0.0;

        /***
         *	Only perform the filtering within regions
         *	that are candidates for this phase
         ***/

        if (Mask[i][j][k] == phasein) {

          for (ix = 0; ix < Fsize; ix++) {

            i1 = i + ix;
            i1 += checkbc(i1, Xsyssize);

            for (iy = 0; iy < Fsize; iy++) {

              j1 = j + iy;
              j1 += checkbc(j1, Ysyssize);

              for (iz = 0; iz < Fsize; iz++) {

                k1 = k + iz;
                k1 += checkbc(k1, Zsyssize);

                Rres[i][j][k] += Normm[i1][j1][k1] * filter[ix][iy][iz];
              }
            }
          }

          if (Rres[i][j][k] > resmax)
            resmax = Rres[i][j][k];
          if (Rres[i][j][k] < resmin)
            resmin = Rres[i][j][k];
        }
      }
    }
  }

  printf("\n\tDone filtering image.");
  fflush(stdout);

  /***
   *	Now threshold the image by creating a histogram
   *	of the values of Rres[i][j][k] and determining
   *	a cutoff bin to define the phase
   **/

  sect = (resmax - resmin) / ((float)Hsize);
  printf("\n\tSect is %f", sect);
  fflush(stdout);

  for (i = 1; i <= Hsize; i++) {
    Sum[i] = 0.0;
  }

  xtot = 0.0;
  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        /***
         *	Only examine within regions
         *	that are candidates for this phase
         ***/

        if (Mask[i][j][k] == phasein) {
          xtot++;

          /***
           *	Find the bin number for this pixel and add
           *	the pixel to the statistics
           ***/

          index = 1 + (int)((Rres[i][j][k] - resmin) / sect);

          if (index > Hsize)
            index = Hsize;
          Sum[index] += 1.0;
        }
      }
    }
  }

  printf("\n\tDone thresholding first pass.");

  /* Determine which bin to choose for correct thresholding */

  sumtot = Vcrit = 0.0;
  done = 0;

  printf("\n\tResmin = %f  Resmax = %f", resmin, resmax);
  fflush(stdout);

  for (i = 1; ((i <= Hsize) && (!done)); i++) {

    sumtot += (float)(((double)Sum[i]) / ((double)xtot));

    if (sumtot > xpt) { /* xpt is input to the function */

      ytmp = (float)i;
      Vcrit = resmin + (resmax - resmin) * (ytmp - 0.5) / ((float)Hsize);
      done = 1;
    }
  }

  printf("Critical volume fraction is %f\n", Vcrit);
  fflush(stdout);

  return (0);
}

/***
 *	freeallmem
 *
 *	Releases all dynamically allocated memory for this
 *	program.
 *
 *	SHOULD ONLY BE CALLED IF ALL MEMORY HAS ALREADY BEEN
 *	DYNAMICALLY ALLOCATED
 *
 *	Arguments:	None
 *	Returns:	Nothing
 *
 *	Calls:		free_ivector, free_fvector, free_fcube
 *	Called by:	main
 *
 ***/
void freeallmem(void) {
  if (R)
    free_ivector(R);
  if (S)
    free_fvector(S);
  if (Xr)
    free_fvector(Xr);
  if (Filter)
    free_fcube(Filter, Fsize + 1);
  if (Mask)
    free_ibox(Mask, Xsyssize + 1, Ysyssize + 1);
  if (Sum)
    free_fvector(Sum);
  if (Normm)
    free_fbox(Normm, Xsyssize + 1, Ysyssize + 1);
  if (Rres)
    free_fbox(Rres, Xsyssize + 1, Ysyssize + 1);

  return;
}
