/******************************************************
 *
 * Program genaggpack.c to generate three-dimensional packing
 * of aggregate particles, sampling from the aggregate database
 *
 * Programmer:    Jeffrey W. Bullard
 *                 Building and Fire Research Laboratory
 *                NIST
 *                100 Bureau Drive Mail Stop 8621
 *                Gaithersburg, MD  20899-8621   USA
 *                (301) 975-5725      FAX: (301) 990-6891
 *                E-mail: bullard@nist.gov
 *
 * October 2004
 *******************************************************/
#include "include/vcctl.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
#define DEBUG
#define CHOOSE_BASED_ON_SIZE
*/

#define MAXSP 10000

#define MAXLINES 3500
#define NNN 14

#define AGG INERTAGG /* phase identifiers, just for this program */
#define ITZ 2

#define COARSE 0
#define FINE 1

/***
 *    Number of grid points used in theta and phi directions
 *    to reconstruct particle surface. You can use down to
 *    about 100 for each and still get particles that are decent
 *    looking. The number of lines in the VRML files scale like
 *    NTHETA*NPHI. NOTE: Better to have odd number.
 *    Allow three different levels of resolution, depending on
 *    the value of resval in the main program (0=low, 1=med, 2=high)
 ***/
#define NTHETAPTS 1000

/* maximum number of random tries for particle placement */
#define MAXTRIES 150000

/* Error flag for memory violation */
#define MEMERR -1

#define MAXSIZECLASSES 74

/***
 *    Note that each particle must have a separate ID
 *    to allow for flocculation
 ***/

#define SPHERES 0
#define REALSHAPE 1

#define CEM 100

/* max. number of particles allowed in box */
#define NPARTC 2400000

/* Default for burned id must be at least 100 greater than NPARTC */
#define BURNT 2440000
#define FCHECK BURNT /* Temporary flag for preventing particle touching */

#define MAXBURNING 2390000

/* maximum number of different particle sizes */
#define NUMSOURCES                                                             \
  2 /* number of different sources allowed for each aggregate type */
#define NUMAGGBINS 148 /* MAXSIZECLASSES * NUMAGGBINS */

/***
 *    Defines for main menu choice
 ***/

#define EXIT 1
#define SPECSIZE EXIT + 1
#define ADDCOARSEPART SPECSIZE + 1
#define ADDFINEPART ADDCOARSEPART + 1
#define MEASURE ADDFINEPART + 1
#define CONNECTIVITY MEASURE + 1
#define OUTPUTMIC CONNECTIVITY + 1
#define EMAIL OUTPUTMIC + 1

/***
 *    Parameter for comparing the difference between
 *    two floats
 ***/

#define TINY 1.0e-6

#define STAY 0
#define MOVE 1
#define ERASE 2

/***
 *    Home-made max function to return the maximum of two integers
 ***/

#define max(a, b) (((a) > (b)) ? (a) : (b))
#define min(a, b) (((a) < (b)) ? (a) : (b))

/***
 *    FINEAGGRES is the cutoff resolution at or above which the ITZ
 *    will not be resolved
 ***/
const float FINEAGGRES = 0.10;

/***
 *    Data structure for linked list of surface pixels
 *    to be used in adjusting volume of real-shape particles
 ***/

struct Surfpix {
  int x, y, z; /* position of surface pixel in bounding box */
};

/***
 *    Global variable declarations:
 *
 *        Agg stores the 3-D particle structure
 *        (each particle with its own ID)
 *
 *        Aggreal stores the phase id of each particle,
 *        signifying coarse or fine aggregate source
 *
 *        Bbox stores the local aggregate particle
 ***/

int Verbose;
int ***Agg, ***Aggreal, ***Bbox;

/***
 *    System size (pixels per edge), number of
 *    particles, and size of aggregate
 ***/
int Syspix = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
int Mindimen = DEFAULTSYSTEMSIZE;
const float Size_safety_coeff = 0.40;
int Isizemag = 1;
float Sizemag = 1.0;
int Npart, Aggsize, Shape;
const int Shapesperbin = 4;
int Npartc, Burnt, Maxburning;
int Allocated = 0;

int N_total = 0;
int N_target = 0;

int Volpartmin[NUMSOURCES][MAXSIZECLASSES],
    Volpartmax[NUMSOURCES][MAXSIZECLASSES];

int Dispdist = 1;

/***
 *    System resolution (micrometers per pixel edge)
 ***/
float Resolution = DEFAULTRESOLUTION;
const float Resolution_safety_coeff = 2.0;

/* VCCTL software version used to create input file */
float Version;

/* Random number seed */
int *Seed;

/* Itz thickness in pixels */
int Itz;

double Pi;

fcomplex **Y, **A, **AA;
int Ntheta, Nphi;
int Nnn = NNN;

/* Flags for checkpart */
static int Check = 1;
static int Place = 2;

/* File root for real shape anm files */
char Pathroot[MAXSTRING], Shapeset[MAXSTRING];
char Filesep;

/* Gaussian quadrature points for real shape particles */
float *Xg, *Wg;

struct lineitem {
  char name[MAXSTRING];
  float xlow;
  float xhi;
  float ylow;
  float yhi;
  float zlow;
  float zhi;
  float volume;
  float surfarea;
  float nsurfarea;
  float diam;
  float Itrace;
  int Nnn;   /* Number terms to get within
                             5% of Gaussian curvature */
  float NGC; /* normalized Gaussian curvature */
  float length;
  float width;
  float thickness;
  float nlength;
  float nwidth;
};

/***
 *    Function declarations
 ***/

void checkargs(int argc, char *argv[]);
int getsystemsize(void);
void genparticles(int type, int numsources, int vol[NUMSOURCES][MAXSIZECLASSES],
                  float sizeeachmin[NUMSOURCES][MAXSIZECLASSES],
                  float sizeeachmax[NUMSOURCES][MAXSIZECLASSES], FILE *fpout);
int checksphere(int xin, int yin, int zin, int radd, int wflg, int phase2);
int checkpart(int xin, int yin, int zin, int nxp, int nyp, int nzp, int volume,
              int phasein, int phase2, int wflg);
int image(int *nxp, int *nyp, int *nzp);
int adjustvol(int diff, int nxp, int nyp, int nzp);
void create(int type, int numtimes);
void addlayer(int nxp, int nyp, int nzp);
void striplayer(int nxp, int nyp, int nzp);
void additz(int nxp, int nyp, int nzp);
void measure(void);
void connect(void);
void outmic(void);
void harm(double theta, double phi);
double fac(int j);
void freeallmem(void);

int main(int argc, char *argv[]) {
  int userc; /* User choice from menu */
  int nseed, numtimes;
  char instring[MAXSTRING];
  register int ig, jg, kg;

  /* Initialize global arrays */
  for (jg = 0; jg < NUMSOURCES; jg++) {
    for (ig = 0; ig < MAXSIZECLASSES; ig++) {
      Volpartmin[jg][ig] = Volpartmax[jg][ig] = 0;
    }
  }

  numtimes = 0;

  A = NULL;
  AA = NULL;
  Y = NULL;
  Bbox = NULL;
  Agg = NULL;
  Aggreal = NULL;
  Xg = NULL;
  Wg = NULL;

  Pi = 4.0 * atan(1.0);

  Ntheta = Nphi = 0;

  /* Check command-line arguments */
  checkargs(argc, argv);

  printf("Enter random number seed value (a negative integer) \n");
  read_string(instring, sizeof(instring));
  nseed = atoi(instring);
  if (nseed > 0)
    nseed = (-1 * nseed);
  printf("%d \n", nseed);
  Seed = (&nseed);

  /* Initialize counters and system parameters */

  Npart = 0;

  /***
   *    Present menu and execute user choice
   ***/

  do {
    printf(" \n Input User Choice \n");
    printf("%d) Exit \n", EXIT);
    printf("%d) Specify system size \n", SPECSIZE);
    printf("%d) Add coarse aggregate particles \n", ADDCOARSEPART);
    printf("%d) Add fine aggregate particles \n", ADDFINEPART);
    printf("%d) Measure global phase fractions \n", MEASURE);
    printf("%d) Measure single phase connectivity ", CONNECTIVITY);
    printf("(pores or solids) \n");
    printf("%d) Output current packing to file \n", OUTPUTMIC);
    printf("%d) Email user status of program \n", EMAIL);

    read_string(instring, sizeof(instring));
    userc = atoi(instring);
    printf("%d \n", userc);
    fflush(stdout);

    switch (userc) {
    case SPECSIZE:
      if (getsystemsize() == MEMERR) {
        freeallmem();
        bailout("genaggpack", "Memory allocation error");
        exit(1);
      }

      /* Clear the 3-D system to all porosity to start */

      for (kg = 0; kg < Zsyssize; kg++) {
        for (jg = 0; jg < Ysyssize; jg++) {
          for (ig = 0; ig < Xsyssize; ig++) {
            Agg[ig][jg][kg] = POROSITY;
            Aggreal[ig][jg][kg] = POROSITY;
          }
        }
      }
      break;
    case ADDCOARSEPART:
      create((int)COARSE, numtimes);
      numtimes++;
      break;
    case ADDFINEPART:
      create((int)FINE, numtimes);
      numtimes++;
      break;
    case MEASURE:
      measure();
      break;
    case CONNECTIVITY:
      connect();
      break;
    case OUTPUTMIC:
      outmic();
      break;
    default:
      break;
    }

  } while (userc != EXIT);

  freeallmem();
  return (0);
}

/***
 *   checkargs
 *
 *     Checks command-line arguments
 *
 *     Arguments:    int argc, char *argv[]
 *     Returns:    nothing
 *
 *    Calls:        no routines
 *    Called by:    main program
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

/***
 *    getsystemsize
 *
 *     Gets the dimension, in pixels, of the system per edge
 *
 *     Arguments:    none
 *     Returns:    status flag (0 if okay, -1 if memory allocation error)
 *
 *    Calls:        no routines
 *    Called by:    main program
 ***/
int getsystemsize(void) {
  char instring[MAXSTRING];

  Xsyssize = Ysyssize = Zsyssize = 0;
  Resolution = 0.0;

  printf("Enter X dimension of system \n");
  read_string(instring, sizeof(instring));
  Xsyssize = atoi(instring);
  printf("%d\n", Xsyssize);
  printf("Enter Y dimension of system \n");
  read_string(instring, sizeof(instring));
  Ysyssize = atoi(instring);
  printf("%d\n", Ysyssize);
  printf("Enter Z dimension of system \n");
  read_string(instring, sizeof(instring));
  Zsyssize = atoi(instring);
  printf("%d\n", Zsyssize);

  if ((Xsyssize <= 0) || (Xsyssize > MAXSIZE) || (Ysyssize <= 0) ||
      (Ysyssize > MAXSIZE) || (Zsyssize <= 0) || (Zsyssize > MAXSIZE)) {

    bailout("genaggpack", "Bad system size specification");
    exit(1);
  }

  printf("Enter system resolution (millimeters per pixel) \n");
  read_string(instring, sizeof(instring));
  Resolution = atof(instring);
  printf("%4.2f\n", Resolution);

  /*
  if ((Resolution < HIGHRES - TINY) && (Resolution > LOWRES + TINY)) {
      bailout("genaggpack","Bad value for system resolution");
      exit(1);
  }
  */

  /***
   *    Now dynamically allocate the memory for the Agg array
   ***/

  Syspix = (int)(Xsyssize * Ysyssize * Zsyssize);
  Sizemag = ((float)Syspix) / (pow(((double)DEFAULTSYSTEMSIZE), 3.0));
  Isizemag = (int)(Sizemag + 0.5);
  if (Isizemag < 1)
    Isizemag = 1;
  Npartc = (NPARTC * Isizemag);
  Burnt = (BURNT * Isizemag);
  Maxburning = (MAXBURNING * Isizemag);

  Agg = NULL;

  Agg = ibox(Xsyssize, Ysyssize, Zsyssize);
  if (!Agg) {
    return (MEMERR);
  }

  Aggreal = NULL;

  Aggreal = ibox(Xsyssize, Ysyssize, Zsyssize);
  if (!Aggreal) {
    return (MEMERR);
  }

  Allocated = 1;

  return (0);
}

/***
 *    checksphere
 *
 *    routine to check or perform placement of sphere of ID phasein,
 *    centered at location (xin,yin,zin) of radius radd.
 *
 *     Arguments:
 *         int xin,yin,zin is the centroid of the sphere to add
 *         int radd is the radius of the sphere to add
 *        int wflg (1=check for fit of sphere, 2=place the sphere)
 *        int phase2 phase to assign to sphere
 *
 *     Returns:    integer flag telling whether sphere will fit
 *
 *    Calls:        checkbc
 *    Called by:    genparticles
 ***/
int checksphere(int xin, int yin, int zin, int radd, int wflg, int phase2) {
  int nofits, xp, yp, zp, i, j, k, nump;
  float dist, xdist, ydist, zdist, ftmp;

  nofits = nump = 0; /* Flag indicating if placement is possible */

  /***
   *    Check all pixels within the digitized sphere volume
   ***/

  if (wflg == Check) {
    for (i = xin - radd; ((i <= xin + radd) && (!nofits)); i++) {
      xp = i;

      /***
       *    Adjust for periodic BCs if necessary
       ***/

      xp += checkbc(xp, Xsyssize);

      ftmp = (float)(i - xin);
      xdist = ftmp * ftmp;
      for (j = yin - radd; ((j <= yin + radd) && (!nofits)); j++) {
        yp = j;

        /***
         *    Adjust for periodic BCs if necessary
         ***/

        yp += checkbc(yp, Ysyssize);

        ftmp = (float)(j - yin);
        ydist = ftmp * ftmp;
        for (k = zin - radd; ((k <= zin + radd) && (!nofits)); k++) {
          zp = k;

          /***
           *    Adjust for periodic BCs if necessary
           ***/

          zp += checkbc(zp, Zsyssize);

          ftmp = (float)(k - zin);
          zdist = ftmp * ftmp;

          /***
           *    Compute distance from center of
           *    sphere to this pixel
           ***/

          dist = sqrt(xdist + ydist + zdist);
          if ((dist - 0.5) <= (float)radd) {

            if ((Agg[xp][yp][zp] != POROSITY) && (Agg[xp][yp][zp] != ITZ))
              nofits = 1;
          }
        }
      }
    }

    /* return flag indicating if sphere will fit */

    return (nofits);

  } else {

    /* We are placing the particle */

    for (i = xin - radd; (i <= xin + radd); i++) {
      xp = i;

      /***
       *    Adjust for periodic BCs if necessary
       ***/

      xp += checkbc(xp, Xsyssize);

      ftmp = (float)(i - xin);
      xdist = ftmp * ftmp;
      for (j = yin - radd; (j <= yin + radd); j++) {
        yp = j;

        /***
         *    Adjust for periodic BCs if necessary
         ***/

        yp += checkbc(yp, Ysyssize);

        ftmp = (float)(j - yin);
        ydist = ftmp * ftmp;
        for (k = zin - radd; (k <= zin + radd); k++) {
          zp = k;

          /***
           *    Adjust for periodic BCs if necessary
           ***/

          zp += checkbc(zp, Zsyssize);

          ftmp = (float)(k - zin);
          zdist = ftmp * ftmp;

          /***
           *    Compute distance from center of
           *    sphere to this pixel
           ***/

          dist = sqrt(xdist + ydist + zdist);
          if ((dist - 0.5) <= (float)radd) {
            Agg[xp][yp][zp] = phase2;
            nump++;
          }
        }
      }
    }

    /* Particle is placed.  Add ITZ layer if required */

    if (Itz > 0) {
      radd += Itz;
      for (i = xin - radd; (i <= xin + radd); i++) {
        xp = i;

        /***
         *    Adjust for periodic BCs if necessary
         ***/

        xp += checkbc(xp, Xsyssize);

        ftmp = (float)(i - xin);
        xdist = ftmp * ftmp;
        for (j = yin - radd; (j <= yin + radd); j++) {
          yp = j;

          /***
           *    Adjust for periodic BCs if necessary
           ***/

          yp += checkbc(yp, Ysyssize);

          ftmp = (float)(j - yin);
          ydist = ftmp * ftmp;
          for (k = zin - radd; (k <= zin + radd); k++) {
            zp = k;

            /***
             *    Adjust for periodic BCs if necessary
             ***/

            zp += checkbc(zp, Zsyssize);

            ftmp = (float)(k - zin);
            zdist = ftmp * ftmp;

            /***
             *    Compute distance from center of
             *    sphere to this pixel
             ***/

            dist = sqrt(xdist + ydist + zdist);
            if ((dist - 0.5) <= (float)radd && Agg[xp][yp][zp] == POROSITY) {
              Agg[xp][yp][zp] = ITZ;
            }
          }
        }
      }
    }

    return (nump);
  }
}

/***
 *    checkpart
 *
 *    routine to check or perform placement of real-shaped particle
 *    of ID phasein, centered at location (xin,yin,zin) of volume vol
 *
 *     Arguments:
 *         int xin,yin,zin is the centroid of the sphere to add
 *         int nxp,nyp,nzp is the lower left front corner of bounding box
 *             for real particles
 *         int vol is the number of pixels
 *         int phasein is phase to assign to aggregate image (particle id)
 *         int phase2 phase to assign to aggreal image (phase id)
 *         int wflg (1=check for fit, 2=place the particle)
 *
 *     Returns:    integer flag telling whether sphere will fit
 *
 *    Calls:        checkbc
 *    Called by:    genparticles
 ***/
int checkpart(int xin, int yin, int zin, int nxp, int nyp, int nzp, int volume,
              int phasein, int phase2, int wflg) {
  int nofits, i, j, k;
  int i1, j1, k1, nump, xc, yc, zc;

  nofits = 0; /* Flag indicating if placement is possible */

  if (Verbose)
    printf("\nIn Checkpart, Vol = %d, wflg = %d, phase = %d", volume, wflg,
           phase2);

  xc = (0.50 * nxp) + 0.01;
  yc = (0.50 * nyp) + 0.01;
  zc = (0.50 * nzp) + 0.01;

  if (wflg == Check) {
    k = j = i = 1;
    nofits = 0;
    while (k <= nzp && !nofits) {
      j = 1;
      while (j <= nyp && !nofits) {
        i = 1;
        while (i <= nxp && !nofits) {
          i1 = xin + i;
          i1 += checkbc(i1, Xsyssize);
          j1 = yin + j;
          j1 += checkbc(j1, Ysyssize);
          k1 = zin + k;
          k1 += checkbc(k1, Zsyssize);
          if (Agg[i1][j1][k1] != POROSITY && Agg[i1][j1][k1] != ITZ &&
              Bbox[i][j][k] != POROSITY && Bbox[i][j][k] != ITZ) {

            nofits = 1;
          }
          i++;
        }
        j++;
      }
      k++;
    }

    return (nofits);

  } else {

    k = j = i = 1;
    nump = 0;
    while (k <= nzp) {
      j = 1;
      while (j <= nyp) {
        i = 1;
        while (i <= nxp) {
          i1 = xin + i;
          i1 += checkbc(i1, Xsyssize);
          j1 = yin + j;
          j1 += checkbc(j1, Ysyssize);
          k1 = zin + k;
          k1 += checkbc(k1, Zsyssize);
          if (Bbox[i][j][k] != POROSITY && Bbox[i][j][k] < FCHECK) {
            Agg[i1][j1][k1] = phasein;
            Aggreal[i1][j1][k1] = phase2;
            nump++;
          }
          i++;
        }
        j++;
      }
      k++;
    }

    return (nump);
  }

  /***
   *    Should not be able to get to here in this function, but
   *    provide a default return value just in case
   ***/

  return (1);
}

/***
 *    image
 *
 *     For real shape particles, populates the Bbox matrix with the
 *     particle shape, placing 1's everywhere
 *
 *     Arguments:
 *         fcomplex a is the array of spherical harmonic coefficients
 *         int nxp,nyp,nzp is the dimension of the bounding box
 *
 *     Returns:    integer flag telling number of solid pixels in the particle
 *
 *    Calls:        checkbc
 *    Called by:    genparticles
 ***/
int image(int *nxp, int *nyp, int *nzp) {
  int partc = 0;
  int n, m, i, j, k, count;
  fcomplex rr;
  double xc, yc, zc, x1, y1, z1, r;
  double theta, phi;

  xc = (0.50 * (*nxp)) + 0.01;
  yc = (0.50 * (*nyp)) + 0.01;
  zc = (0.50 * (*nzp)) + 0.01;

#ifdef DEBUG
  printf("\nEntering first image loop: nxp = %d, nyp= %d, nzp = %d, Nnn = %d",
         *nxp, *nyp, *nzp, Nnn);
  fflush(stdout);
#endif

  for (k = 1; k <= *nzp; k++) {
    for (j = 1; j <= *nyp; j++) {
      for (i = 1; i <= *nxp; i++) {
        Bbox[i][j][k] = POROSITY;
      }
    }
  }

  /***
   *    Assigning solid pixels within Bbox, with id AGG
   ***/

  count = 0;
  for (k = 1; k <= *nzp && (*nzp < (int)(0.8 * Zsyssize)) &&
              (*nyp < (int)(0.8 * Ysyssize)) && (*nxp < (int)(0.8 * Xsyssize));
       k++) {
    for (j = 1; j <= *nyp; j++) {
      for (i = 1; i <= *nxp; i++) {

        x1 = (double)i;
        y1 = (double)j;
        z1 = (double)k;

        r = sqrt(((x1 - xc) * (x1 - xc)) + ((y1 - yc) * (y1 - yc)) +
                 ((z1 - zc) * (z1 - zc)));
        if (r == 0.0) {
          count++;
          Bbox[i][j][k] = AGG;
          break;
        }

        theta = acos((z1 - zc) / r);
        phi = atan((y1 - yc) / (x1 - xc));

        if ((y1 - yc) < 0.0 && (x1 - xc) < 0.0)
          phi += Pi;
        if ((y1 - yc) > 0.0 && (x1 - xc) < 0.0)
          phi += Pi;
        if ((y1 - yc) < 0.0 && (x1 - xc) > 0.0)
          phi += 2.0 * Pi;
        harm(theta, phi);
        rr = Complex(0.0, 0.0);
        rr = Cmul(AA[0][0], Y[0][0]);
        for (n = 1; n <= Nnn; n++) {
          for (m = -n; m <= n; m++) {
            rr = Cadd(rr, Cmul(AA[n][m], Y[n][m]));
          }
        }

        if (r <= (rr.r)) {
          Bbox[i][j][k] = AGG;
          count++;
        }
      }
    }
  }

  partc = count;

  return (partc);
}

/***
 *    smallimage
 *
 *     Special case of digitizing images for real-shaped
 *     particles when their volume is less than four pixels.
 *     In this case, we bypass SH reconstruction, volume
 *     adjustment, etc., and just manually place the particles
 *     in Bbox
 *
 *     Arguments:
 *         int nxp,nyp,nzp are the dimensions of the bounding box
 *         int vol is the number of pixels comprising the particle
 *
 *     Returns:    integer flag telling number of solid pixels in the particle
 *
 *    Calls:        checkbc
 *    Called by:    genparticles
 ***/
int smallimage(int *nxp, int *nyp, int *nzp, int vol) {
  int min, maxdim = 10;
  int orient;
  int i, j, k, v;
  float choice, dist, di2, dj2, dk2;

  min = Itz + 1;

  /***
   *    Initialize Bbox array to porosity.  We initialize out to a cube
   *    having edge length equal to the maximum edge length of the
   *    bounding box, because later we may do a rigid body rotation,
   *    reflection, or inversion of the entire contents in place.
   ***/

  for (k = 1; k < maxdim; k++) {
    for (j = 1; j < maxdim; j++) {
      for (i = 1; i < maxdim; i++) {
        Bbox[i][j][k] = POROSITY;
      }
    }
  }

  /***
   *    Assigning solid pixels within Bbox, with id SANDINCONCRETE
   ***/

  if (vol <= 4) {

    *nxp = 6;
    *nyp = 6;
    *nzp = 6;

    if (vol == 4) {
      orient = 1 + (int)(3.0 * ran1(Seed));
      switch (orient) {
      case 1:
        Bbox[min][min][min] = SANDINCONCRETE;
        Bbox[min + 1][min][min] = SANDINCONCRETE;
        Bbox[min][min + 1][min] = SANDINCONCRETE;
        Bbox[min + 1][min + 1][min] = SANDINCONCRETE;
        *nzp = 5;
        break;
      case 2:
        Bbox[min][min][min] = SANDINCONCRETE;
        Bbox[min][min][min + 1] = SANDINCONCRETE;
        Bbox[min][min + 1][min] = SANDINCONCRETE;
        Bbox[min][min + 1][min + 1] = SANDINCONCRETE;
        *nxp = 5;
        break;
      case 3:
        Bbox[min][min][min] = SANDINCONCRETE;
        Bbox[min + 1][min][min] = SANDINCONCRETE;
        Bbox[min][min][min + 1] = SANDINCONCRETE;
        Bbox[min + 1][min][min + 1] = SANDINCONCRETE;
        *nyp = 5;
        break;
      default:
        Bbox[min][min][min] = SANDINCONCRETE;
        Bbox[min + 1][min][min] = SANDINCONCRETE;
        Bbox[min][min + 1][min] = SANDINCONCRETE;
        Bbox[min + 1][min + 1][min] = SANDINCONCRETE;
        *nzp = 5;
        break;
      }
      return (4);
    } else if (vol == 3) {
      orient = 1 + (int)(3.0 * ran1(Seed));
      switch (orient) {
      case 1:
        Bbox[min][min][min] = SANDINCONCRETE;
        Bbox[min + 1][min][min] = SANDINCONCRETE;
        Bbox[min][min + 1][min] = SANDINCONCRETE;
        *nzp = 5;
        break;
      case 2:
        Bbox[min][min][min] = SANDINCONCRETE;
        Bbox[min][min][min + 1] = SANDINCONCRETE;
        Bbox[min][min + 1][min] = SANDINCONCRETE;
        *nxp = 5;
        break;
      case 3:
        Bbox[min][min][min] = SANDINCONCRETE;
        Bbox[min][min][min + 1] = SANDINCONCRETE;
        Bbox[min + 1][min][min] = SANDINCONCRETE;
        *nyp = 5;
        break;
      default:
        Bbox[min][min][min] = SANDINCONCRETE;
        Bbox[min + 1][min][min] = SANDINCONCRETE;
        Bbox[min][min + 1][min] = SANDINCONCRETE;
        *nzp = 5;
        break;
      }
      return (3);
    } else {
      orient = 1 + (int)(3.0 * ran1(Seed));
      switch (orient) {
      case 1:
        Bbox[min][min][min] = SANDINCONCRETE;
        Bbox[min + 1][min][min] = SANDINCONCRETE;
        *nyp = 5;
        *nzp = 5;
        break;
      case 2:
        Bbox[min][min][min] = SANDINCONCRETE;
        Bbox[min][min + 1][min] = SANDINCONCRETE;
        *nxp = 5;
        *nzp = 5;
        break;
      case 3:
        Bbox[min][min][min] = SANDINCONCRETE;
        Bbox[min][min][min + 1] = SANDINCONCRETE;
        *nxp = 5;
        *nyp = 5;
        break;
      default:
        Bbox[min][min][min] = SANDINCONCRETE;
        Bbox[min + 1][min][min] = SANDINCONCRETE;
        *nyp = 5;
        *nzp = 5;
        break;
      }
      return (2);
    }

  } else { /*  Volume is greater than 4.  Use a corroded sphere of diameter 3 */

    *nxp = 5;
    *nyp = 5;
    *nzp = 5;

    for (k = -1; k < 2; k++) {
      dk2 = (float)(k * k);
      for (j = -1; j < 2; j++) {
        dj2 = (float)(j * j);
        for (i = -1; i < 2; i++) {
          di2 = (float)(i * i);
          dist = sqrt(di2 + dj2 + dk2);
          if ((dist - 0.5) <= 1.5) {
            Bbox[3 + i][3 + j][3 + k] = SANDINCONCRETE;
          }
        }
      }
    }

    /* Sphere is placed, now corrode it to get volume right */

    v = 19;
    while (v > vol) {
      i = -1 + (int)(3.0 * ran1(Seed));
      j = -1 + (int)(3.0 * ran1(Seed));
      if (i == 0 && j == 0) {
        choice = ran1(Seed);
        k = (choice > 0.5) ? 1 : -1;
      } else if (i == 0 || j == 0) {
        k = -1 + (int)(3.0 * ran1(Seed));
      } else {
        k = 0;
      }
      if (Bbox[3 + i][3 + j][3 + k] == SANDINCONCRETE) {
        Bbox[3 + i][3 + j][3 + k] = POROSITY;
        v -= 1;
      }
    }
    return (vol);
  }
}

/***
 *    adjustvol
 *
 *     For real shape particles, adjusts by several pixels the
 *     volume of the particle.  Needed to get exact match of pixel
 *     volume to target value.
 *
 *   Only fool-proof way to do this seems to be to find the surface
 *   of the particle, make a linked list of the surface pixels and
 *   then select one at random
 *
 *     Arguments:
 *         int number to add (negative if subtracting)
 *         int x,y,and z dimensions of the bounding box
 *
 *     Returns:    integer flag telling number of solid pixels added
 *
 *    Calls:        no functions
 *    Called by:    genparticles
 ***/
int adjustvol(int diff, int nxp, int nyp, int nzp) {
  int i, j, k, count, absdiff, n;
  int choice, numsp;
  struct Surfpix sp[MAXSP];

  /* Initialize local sp array */

  for (i = 0; i < MAXSP; i++) {
    sp[i].x = 0;
    sp[i].y = 0;
    sp[i].z = 0;
  }

  absdiff = abs(diff);

  /* Populate list of surface pixels */

  numsp = 0;
  if (diff > 0) {
    /* add solid pixels to surface */
    for (i = 2; i < nxp; i++) {
      for (j = 2; j < nyp; j++) {
        for (k = 2; k < nzp; k++) {
          if (Bbox[i][j][k] == POROSITY &&
              ((Bbox[i + 1][j][k] == AGG) || (Bbox[i - 1][j][k] == AGG) ||
               (Bbox[i][j + 1][k] == AGG) || (Bbox[i][j - 1][k] == AGG) ||
               (Bbox[i][j][k + 1] == AGG) || (Bbox[i][j][k - 1] == AGG))) {
            /* add i,j,k to surface pixels */
            sp[numsp].x = i;
            sp[numsp].y = j;
            sp[numsp].z = k;
            numsp++;
          }
        }
      }
    }
  } else {
    /* remove solid pixels from surface */
    for (i = 1; i <= nxp; i++) {
      for (j = 1; j <= nyp; j++) {
        for (k = 1; k <= nzp; k++) {
          if (Bbox[i][j][k] == AGG && ((Bbox[i + 1][j][k] == POROSITY) ||
                                       (Bbox[i - 1][j][k] == POROSITY) ||
                                       (Bbox[i][j + 1][k] == POROSITY) ||
                                       (Bbox[i][j - 1][k] == POROSITY) ||
                                       (Bbox[i][j][k + 1] == POROSITY) ||
                                       (Bbox[i][j][k - 1] == POROSITY))) {
            /* add i,j,k to surface pixels */

            sp[numsp].x = i;
            sp[numsp].y = j;
            sp[numsp].z = k;
            numsp++;
          }
        }
      }
    }
  }

#ifdef DEBUG
  printf("\nIn adjustvol, diff = %d and num surf pix = %d", diff, numsp);
  fflush(stdout);
#endif

  count = 0;
  for (n = 1; n <= absdiff; n++) {

    /***
     *    randomly select a surface pixel from the list
     ***/

    choice = (int)(numsp * ran1(Seed));
#ifdef DEBUG
    printf("\n\tIn adjustvol random choice = %d", choice);
    fflush(stdout);
#endif

    if (choice > numsp)
      break;
    if (Bbox[sp[choice].x][sp[choice].y][sp[choice].z] == AGG) {
      Bbox[sp[choice].x][sp[choice].y][sp[choice].z] = POROSITY;
      count--;
    } else {
      Bbox[sp[choice].x][sp[choice].y][sp[choice].z] = AGG;
      count++;
    }
    for (i = choice; i < numsp - 1; i++) {
      sp[i].x = sp[i + 1].x;
      sp[i].y = sp[i + 1].y;
      sp[i].z = sp[i + 1].z;
    }
    sp[numsp - 1].x = 0;
    sp[numsp - 1].y = 0;
    sp[numsp - 1].z = 0;
    numsp--;
#ifdef DEBUG
    printf("\n\t\tcount = %d and numsp = %d", count, numsp);
    fflush(stdout);
#endif
  }

  return (count);
}

/***
 *    addlayer
 *
 *     For real shape particles, adds a layer of id FCHECK
 *     around the periphery of the particle.  This layer will
 *     be stripped when the particle is placed, but serves as
 *     a guarantee of dispersion distance if Dispdist > 0.
 *
 *     Arguments:    Dimensions nxp,nyp,nzp of bounding box Bbox
 *     Returns:    Nothing
 *
 *    Calls:        no functions
 *    Called by:    genparticles
 ***/
void addlayer(int nxp, int nyp, int nzp) {
  int i, j, k;

  for (k = 1; k < nzp; k++) {
    for (j = 1; j < nyp; j++) {
      for (i = 1; i < nxp; i++) {
        if (Bbox[i][j][k] == AGG) {
          if (Bbox[i + 1][j][k] == POROSITY)
            Bbox[i + 1][j][k] = FCHECK;
          if (Bbox[i - 1][j][k] == POROSITY)
            Bbox[i - 1][j][k] = FCHECK;
          if (Bbox[i][j + 1][k] == POROSITY)
            Bbox[i][j + 1][k] = FCHECK;
          if (Bbox[i][j - 1][k] == POROSITY)
            Bbox[i][j - 1][k] = FCHECK;
          if (Bbox[i][j][k + 1] == POROSITY)
            Bbox[i][j][k + 1] = FCHECK;
          if (Bbox[i][j][k - 1] == POROSITY)
            Bbox[i][j][k - 1] = FCHECK;
          if (Bbox[i + 1][j + 1][k] == POROSITY)
            Bbox[i + 1][j + 1][k] = FCHECK;
          if (Bbox[i + 1][j - 1][k] == POROSITY)
            Bbox[i + 1][j - 1][k] = FCHECK;
          if (Bbox[i - 1][j + 1][k] == POROSITY)
            Bbox[i - 1][j + 1][k] = FCHECK;
          if (Bbox[i - 1][j - 1][k] == POROSITY)
            Bbox[i - 1][j - 1][k] = FCHECK;
          if (Bbox[i + 1][j][k + 1] == POROSITY)
            Bbox[i + 1][j][k + 1] = FCHECK;
          if (Bbox[i + 1][j][k - 1] == POROSITY)
            Bbox[i + 1][j][k - 1] = FCHECK;
          if (Bbox[i - 1][j][k + 1] == POROSITY)
            Bbox[i - 1][j][k + 1] = FCHECK;
          if (Bbox[i - 1][j][k - 1] == POROSITY)
            Bbox[i - 1][j][k - 1] = FCHECK;
          if (Bbox[i][j + 1][k + 1] == POROSITY)
            Bbox[i][j + 1][k + 1] = FCHECK;
          if (Bbox[i][j + 1][k - 1] == POROSITY)
            Bbox[i][j + 1][k - 1] = FCHECK;
          if (Bbox[i][j - 1][k + 1] == POROSITY)
            Bbox[i][j - 1][k + 1] = FCHECK;
          if (Bbox[i][j - 1][k - 1] == POROSITY)
            Bbox[i][j - 1][k - 1] = FCHECK;
          if (Bbox[i + 1][j + 1][k + 1] == POROSITY)
            Bbox[i + 1][j + 1][k + 1] = FCHECK;
          if (Bbox[i + 1][j + 1][k - 1] == POROSITY)
            Bbox[i + 1][j + 1][k - 1] = FCHECK;
          if (Bbox[i + 1][j - 1][k + 1] == POROSITY)
            Bbox[i + 1][j - 1][k + 1] = FCHECK;
          if (Bbox[i + 1][j - 1][k - 1] == POROSITY)
            Bbox[i + 1][j - 1][k - 1] = FCHECK;
          if (Bbox[i + 1][j + 1][k + 1] == POROSITY)
            Bbox[i - 1][j + 1][k + 1] = FCHECK;
          if (Bbox[i + 1][j + 1][k - 1] == POROSITY)
            Bbox[i - 1][j + 1][k - 1] = FCHECK;
          if (Bbox[i + 1][j - 1][k + 1] == POROSITY)
            Bbox[i - 1][j - 1][k + 1] = FCHECK;
          if (Bbox[i + 1][j - 1][k - 1] == POROSITY)
            Bbox[i - 1][j - 1][k - 1] = FCHECK;
        }
      }
    }
  }

  if (Dispdist == 2) {
    for (k = 1; k < nzp; k++) {
      for (j = 1; j < nyp; j++) {
        for (i = 1; i < nxp; i++) {
          if (Bbox[i][j][k] == FCHECK) {
            if (Bbox[i + 1][j][k] == POROSITY)
              Bbox[i + 1][j][k] = FCHECK + 1;
            if (Bbox[i - 1][j][k] == POROSITY)
              Bbox[i - 1][j][k] = FCHECK + 1;
            if (Bbox[i][j + 1][k] == POROSITY)
              Bbox[i][j + 1][k] = FCHECK + 1;
            if (Bbox[i][j - 1][k] == POROSITY)
              Bbox[i][j - 1][k] = FCHECK + 1;
            if (Bbox[i][j][k + 1] == POROSITY)
              Bbox[i][j][k + 1] = FCHECK + 1;
            if (Bbox[i][j][k - 1] == POROSITY)
              Bbox[i][j][k - 1] = FCHECK + 1;
            if (Bbox[i + 1][j + 1][k] == POROSITY)
              Bbox[i + 1][j + 1][k] = FCHECK + 1;
            if (Bbox[i + 1][j - 1][k] == POROSITY)
              Bbox[i + 1][j - 1][k] = FCHECK + 1;
            if (Bbox[i - 1][j + 1][k] == POROSITY)
              Bbox[i - 1][j + 1][k] = FCHECK + 1;
            if (Bbox[i - 1][j - 1][k] == POROSITY)
              Bbox[i - 1][j - 1][k] = FCHECK + 1;
            if (Bbox[i + 1][j][k + 1] == POROSITY)
              Bbox[i + 1][j][k + 1] = FCHECK + 1;
            if (Bbox[i + 1][j][k - 1] == POROSITY)
              Bbox[i + 1][j][k - 1] = FCHECK + 1;
            if (Bbox[i - 1][j][k + 1] == POROSITY)
              Bbox[i - 1][j][k + 1] = FCHECK + 1;
            if (Bbox[i - 1][j][k - 1] == POROSITY)
              Bbox[i - 1][j][k - 1] = FCHECK + 1;
            if (Bbox[i][j + 1][k + 1] == POROSITY)
              Bbox[i][j + 1][k + 1] = FCHECK + 1;
            if (Bbox[i][j + 1][k - 1] == POROSITY)
              Bbox[i][j + 1][k - 1] = FCHECK + 1;
            if (Bbox[i][j - 1][k + 1] == POROSITY)
              Bbox[i][j - 1][k + 1] = FCHECK + 1;
            if (Bbox[i][j - 1][k - 1] == POROSITY)
              Bbox[i][j - 1][k - 1] = FCHECK + 1;
            if (Bbox[i + 1][j + 1][k + 1] == POROSITY)
              Bbox[i + 1][j + 1][k + 1] = FCHECK + 1;
            if (Bbox[i + 1][j + 1][k - 1] == POROSITY)
              Bbox[i + 1][j + 1][k - 1] = FCHECK + 1;
            if (Bbox[i + 1][j - 1][k + 1] == POROSITY)
              Bbox[i + 1][j - 1][k + 1] = FCHECK + 1;
            if (Bbox[i + 1][j - 1][k - 1] == POROSITY)
              Bbox[i + 1][j - 1][k - 1] = FCHECK + 1;
            if (Bbox[i + 1][j + 1][k + 1] == POROSITY)
              Bbox[i - 1][j + 1][k + 1] = FCHECK + 1;
            if (Bbox[i + 1][j + 1][k - 1] == POROSITY)
              Bbox[i - 1][j + 1][k - 1] = FCHECK + 1;
            if (Bbox[i + 1][j - 1][k + 1] == POROSITY)
              Bbox[i - 1][j - 1][k + 1] = FCHECK + 1;
            if (Bbox[i + 1][j - 1][k - 1] == POROSITY)
              Bbox[i - 1][j - 1][k - 1] = FCHECK + 1;
          }
        }
      }
    }
  }

  return;
}

/***
 *    striplayer
 *
 *     For real shape particles, strips one layer of id FCHECK
 *     around the periphery of the particle.  This function
 *     is invoked only if user specified Dispdist = 2 and
 *     the particles are no longer fitting.
 *
 *     Arguments:    Dimensions nxp,nyp,nzp of bounding box Bbox
 *     Returns:    Nothing
 *
 *    Calls:        no functions
 *    Called by:    genparticles
 ***/
void striplayer(int nxp, int nyp, int nzp) {
  int i, j, k;

  for (k = 1; k < nzp; k++) {
    for (j = 1; j < nyp; j++) {
      for (i = 1; i < nxp; i++) {
        if (Bbox[i][j][k] > FCHECK)
          Bbox[i][j][k] = POROSITY;
      }
    }
  }

  return;
}

/***
 *    additz
 *
 *     Probes the final microstructure and adds an ITZ layer
 *     of a given thickness (soft shell model)
 *
 *     Arguments:    Dimensions nxp,nyp,nzp of bounding box Bbox
 *     Returns:    Nothing
 *
 *    Calls:        no functions
 *    Called by:    genparticles
 ***/
void additz(int nxp, int nyp, int nzp) {
  int i, j, k;
  int ii, jj, kk, iii, jjj, kkk;

  for (k = 1; k < Zsyssize; k++) {
    for (j = 1; j < Ysyssize; j++) {
      for (i = 1; i < Xsyssize; i++) {
        if (Aggreal[i][j][k] != POROSITY && Aggreal[i][j][k] != ITZ) {
          for (kkk = -1; kkk < 2; kkk++) {
            kk = k + kkk;
            kk += checkbc(kk, Zsyssize);
            for (jjj = -1; jjj < 2; jjj++) {
              jj = j + jjj;
              jj += checkbc(jj, Ysyssize);
              for (iii = -1; iii < 2; iii++) {
                ii = i + iii;
                ii += checkbc(ii, Xsyssize);
                if (Aggreal[ii][jj][kk] == POROSITY)
                  Aggreal[ii][jj][kk] = ITZ;
              }
            }
          }
        }
      }
    }
  }

  return;
}

/***
 *    genparticles
 *
 *    Routine to place spheres of various sizes and phases at random
 *    locations in 3-D microstructure.
 *
 *     Arguments:
 *        int type is the type of aggregate (FINE or COARSE)
 *        int numsources is the number of sources of this type of aggregate
 *        int pvol holds the volume in voxels of each size class
 *        float minsize holds the minimum radius in pixels of each size class
 *        float maxsize holds the maximum radius in pixels of each size class
 *    Returns:
 *        nothing
 *
 *    Calls:        makesph, ran1
 *    Called by:    create
 ***/
void genparticles(int type, int numsources,
                  int pvol[NUMSOURCES][MAXSIZECLASSES],
                  float minsize[NUMSOURCES][MAXSIZECLASSES],
                  float maxsize[NUMSOURCES][MAXSIZECLASSES], FILE *fpout) {
  int m, n, i, j, k, ii, jj, x, y, z, ig, tries, na, foundpart;
  int srad, nofit, n1, nxp, nyp, nzp, nnxp, nnyp, nnzp, partc, pcount[10];
  int numpershape, orient, nump, numitems, toobig, numgen;
  int klow, khigh, mp, numlines, begin, end;
  int oldabsdiff, absdiff, pixfrac, cx, cy, cz;
  int typeeach[NUMAGGBINS], ival, phaseid;
  int numpartplaced, vol, volmin, volmax, volcrit, ntotal;
  int voleach[NUMAGGBINS], vpmin[NUMAGGBINS], vpmax[NUMAGGBINS], lval;
  float sizeeachmin[NUMAGGBINS], sizeeachmax[NUMAGGBINS], fval;
  float rx, ry, rz, fdmin, fdmax, aa1, aa2;
  float maxrx, maxry, maxrz, critdiam, frad;
  float length, width, vol1, volume, volumecalc, v1;
  float volfractoplace;
  double factor, theta, phi, cosbeta, sinbeta, alpha, gamma, beta, total, abc;
  double realnum, saveratio, ratio[10];
  fcomplex r1, ddd, icmplx;
  char buff[MAXSTRING], filename[MAXSTRING];
  char typestring[10], shapestring[MAXSTRING];
  struct lineitem line[MAXLINES];
  FILE *anmfile, *geomfile;

  /* First thing to do is to sort the particles by maximum size */

  k = 0;
  for (i = 0; i < NUMSOURCES; i++) {
    for (j = 0; j < MAXSIZECLASSES; j++) {
      voleach[k] = pvol[i][j];
      sizeeachmin[k] = minsize[i][j];
      sizeeachmax[k] = maxsize[i][j];
      vpmin[k] = Volpartmin[i][j];
      vpmax[k] = Volpartmax[i][j];
      typeeach[k] = i;
      k++;
    }
  }

  if (Verbose) {
    printf("\nBubble sorting arrays... ");
    fflush(stdout);
  }
  for (i = 0; i < NUMAGGBINS; i++) {
    for (j = (i + 1); j < NUMAGGBINS; j++) {
      if (sizeeachmax[i] < sizeeachmax[j]) {

        ival = typeeach[i];
        typeeach[i] = typeeach[j];
        typeeach[j] = ival;

        lval = voleach[i];
        voleach[i] = voleach[j];
        voleach[j] = lval;

        fval = sizeeachmin[i];
        sizeeachmin[i] = sizeeachmin[j];
        sizeeachmin[j] = fval;

        fval = sizeeachmax[i];
        sizeeachmax[i] = sizeeachmax[j];
        sizeeachmax[j] = fval;

        lval = vpmin[i];
        vpmin[i] = vpmin[j];
        vpmin[j] = lval;

        lval = vpmax[i];
        vpmax[i] = vpmax[j];
        vpmax[j] = lval;
      }
    }
  }

  if (Verbose) {
    printf("Done!");
    printf("\nDetermining numgen = ");
    fflush(stdout);
  }

  /* Determine how many non-zero elements are in sizeeachmax */
  numgen = 0;
  for (i = 0; i < NUMAGGBINS; i++) {
    if (sizeeachmax[i] > 0.0)
      numgen = i;
  }

  if (Verbose) {
    printf("%d", numgen);
    fflush(stdout);
  }

  /* Initialize local arrays */

  saveratio = 1.0;

  for (m = 0; m < 10; m++) {
    pcount[m] = 0;
    ratio[m] = 0.0;
  }

  /***
   *    Generate spheres of each size class
   *    in turn (largest first)
   ***/

  if (type == (int)COARSE)
    strcpy(typestring, "coarse");
  if (type == (int)FINE)
    strcpy(typestring, "fine");
  if (Shape == SPHERES)
    strcpy(shapestring, "spherical");
  if (Shape != SPHERES)
    strcpy(shapestring, "real-shape");

  if (Verbose) {
    printf("\nPlacing %s %s aggregate particles now...", shapestring,
           typestring);
    fflush(stdout);
  }

  n1 = 1;
  switch (Shape) {

  case SPHERES:

    for (ig = 0; ig < numgen; ig++) {

      /* Choose the correct pixel id for this aggregate */

      switch (typeeach[ig]) {
      case 0:
        phaseid = FINEAGG01INCONCRETE;
        if (type == (int)COARSE)
          phaseid = COARSEAGG01INCONCRETE;
        break;
      case 1:
        phaseid = FINEAGG02INCONCRETE;
        if (type == (int)COARSE)
          phaseid = COARSEAGG02INCONCRETE;
        break;
      default:
        phaseid = FINEAGG01INCONCRETE;
        if (type == (int)COARSE)
          phaseid = COARSEAGG01INCONCRETE;
        break;
      }

      numpartplaced = 0;
      ntotal = 0;
      fdmin = sizeeachmin[ig]; /* min RADIUS in pixel edge lengths */
      fdmax = sizeeachmax[ig]; /* max RADIUS in pixel edge lengths */

      if ((2.0 * fdmin) > (float)(Size_safety_coeff * Mindimen)) {
        /* entire class is too big for system */
        ntotal = voleach[ig];
      } else if ((2.0 * fdmax) > (float)(Size_safety_coeff * Mindimen)) {
        /* largest size in this class is too large */
        /* we scale the total pixels to place proportionately */
        volmin = vpmin[ig];
        volmax = vpmax[ig];
        if (volmax <= volmin)
          volmax = volmin + 1;
        critdiam = (float)(Size_safety_coeff * Mindimen);
        fdmax = critdiam / 2.0;
        volcrit = diam2vol(critdiam);
        if (volcrit > volmax)
          volcrit = volmax;
        if (volcrit < volmin)
          volcrit = volmin;
        volfractoplace =
            (float)(((float)(volcrit - volmin)) / ((float)(volmax - volmin)));
        ntotal = ((1.0 - volfractoplace) * voleach[ig]);
      }

      if ((2.0 * fdmax) < (Resolution_safety_coeff * Resolution)) {
        /* entire class is too small for system */
        ntotal = voleach[ig];
      } else if ((2.0 * fdmin) <
                 (float)(Resolution_safety_coeff * Resolution)) {
        /* smallest size in this class is too small */
        /* we scale the total pixels to place proportionately */
        volmin = vpmin[ig];
        volmax = vpmax[ig];
        if (volmax <= volmin)
          volmax = volmin + 1;
        critdiam = (float)(Resolution_safety_coeff * Resolution);
        fdmin = critdiam / 2.0;
        volcrit = diam2vol(critdiam);
        if (volcrit < volmin)
          volcrit = volmin;
        if (volcrit > volmax)
          volcrit = volmax;
        volfractoplace =
            (float)(((float)(volmax - volcrit)) / ((float)(volmax - volmin)));
        ntotal += ((1.0 - volfractoplace) * voleach[ig]);
      }

      /* loop for each sphere in this size class */

      while (ntotal < voleach[ig]) {
        frad = fdmin;
        frad += ((fdmax - fdmin) * ran1(Seed));
        srad = (int)(frad + 0.5);
        tries = 0;

        /* Stop after MAXTRIES random tries */
        do {
          tries++;

          /* generate a random center location for the sphere */

          x = (int)((float)Xsyssize * ran1(Seed));
          y = (int)((float)Ysyssize * ran1(Seed));
          z = (int)((float)Zsyssize * ran1(Seed));

          /***
           *    See if the sphere will fit at x,y,z
           *    Include dispersion distance when checking
           *    to ensure requested separation between spheres
           ***/

          nofit = checksphere(x, y, z, srad, Check, 0);

          if (tries > MAXTRIES) {
            printf("Could not place sphere %d\n", Npart);
            printf("\tafter %d random attempts\n\n", MAXTRIES);
            printf("\nTotal volume desired in this bin was %d", voleach[ig]);
            printf("\nActual volume _placed  in this bin was %d", ntotal);
            printf("\nWas working on bin %d out of %d\n", ig, numgen);
            warning("genaggpack", "Could not place a sphere");
            fflush(stdout);
            return;
          }
        } while (nofit);

        /* Place the sphere at x,y,z */

        Npart++;
        if (Npart > Npartc) {
          printf("Too many spheres being generated \n");
          printf("\tUser needs to increase value of NPARTC\n");
          printf("\tat top of C-code\n\n");
          printf("\nTotal volume desired in this bin was %d", voleach[ig]);
          printf("\nActual volume _placed  in this bin was %d", ntotal);
          printf("\nWas working on bin %d out of %d\n", ig, numgen);
          warning("genaggpack", "Too many spheres");
          fflush(stdout);
          return;
        }
        nump = checksphere(x, y, z, srad, Place, phaseid);
        ntotal += nump;
        N_total += nump;
        numpartplaced++;

        /***************  PUT NICK'S STUFF RIGHT HERE ***********************/
        /*
             Centroid:  X-coord = x + ((0.5*nnxp)+0.01);
             Centroid:  Y-coord = y + ((0.5*nnyp)+0.01);
             Centroid:  Z-coord = z + ((0.5*nnzp)+0.01);
             Need to output the AA[n][m] matrix one row at a time
        */
        fprintf(fpout, "%d %d %d 0\n", x, y, z);
        fprintf(fpout, "0 0 %.10f 0.0000000000\n", ((float)(srad)));
      }
    }

    break;

  default:

    /* Place real shapes instead of spheres */

    sprintf(filename, "%s%s%c%s-geom.dat", Pathroot, Shapeset, Filesep,
            Shapeset);
    geomfile = filehandler("genaggpack", filename, "READ");
    if (!geomfile) {
      freeallmem();
      exit(1);
    } else if (Verbose) {
      printf("Successfully opened geom file\n");
      fflush(stdout);
    }

    /* Scan header and discard */
    fread_string(geomfile, buff);

    /* Read the rest of the geom file one line at a time */
    i = 0;
    while (!feof(geomfile) && i < MAXLINES) {
      fscanf(geomfile, "%s", buff);
      if (!feof(geomfile)) {
        strcpy(line[i].name, buff);
        fscanf(geomfile, "%s", buff);
        line[i].xlow = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].xhi = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].ylow = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].yhi = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].zlow = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].zhi = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].volume = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].surfarea = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].nsurfarea = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].diam = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].Itrace = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].Nnn = atoi(buff);
        fscanf(geomfile, "%s", buff);
        line[i].NGC = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].length = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].width = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].thickness = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].nlength = atof(buff);
        fscanf(geomfile, "%s", buff);
        line[i].nwidth = atof(buff);
        i++;
      }

      /* Line scanned in now */
    }

    /* Close geomfile */
    fclose(geomfile);

    numitems = i; /* Will skip the header */
    numlines = numitems - 2;

    for (ig = 0; ig < numgen; ig++) {

      /* Choose the correct pixel id for this aggregate */
      printf("\n\tig = %d of %d", ig, numgen);
      fflush(stdout);

      switch (typeeach[ig]) {
      case 0:
        phaseid = FINEAGG01INCONCRETE;
        if (type == (int)COARSE)
          phaseid = COARSEAGG01INCONCRETE;
        break;
      case 1:
        phaseid = FINEAGG02INCONCRETE;
        if (type == (int)COARSE)
          phaseid = COARSEAGG02INCONCRETE;
        break;
      default:
        phaseid = FINEAGG01INCONCRETE;
        if (type == (int)COARSE)
          phaseid = COARSEAGG01INCONCRETE;
        break;
      }

      foundpart = 1;
      toobig = 0;
      ntotal = 0;

      fdmin = 2.0 * sizeeachmin[ig]; /* min diam in pixel edge lengths */
      fdmax = 2.0 * sizeeachmax[ig]; /* max diam in pixel edge lengths */
      volmin = vpmin[ig];            /* minimum volume in pixels */
      volmax = vpmax[ig];            /* maximum volume in pixels */
      if (fdmin > (float)(Size_safety_coeff * Mindimen)) {
        /* entire class is too big for system */
        ntotal = voleach[ig];
      } else if (fdmax > (float)(Size_safety_coeff * Mindimen)) {
        /* largest size in this class is too large */
        /* we scale the total pixels to place proportionately */
        volmin = vpmin[ig];
        volmax = vpmax[ig];
        if (volmax <= volmin)
          volmax = volmin + 1;
        critdiam = (float)(Size_safety_coeff * Mindimen);
        fdmax = critdiam;
        volcrit = diam2vol(critdiam);
        if (volcrit > volmax)
          volcrit = volmax;
        if (volcrit < volmin)
          volcrit = volmin;
        volfractoplace =
            (float)(((float)(volcrit - volmin)) / ((float)(volmax - volmin)));
        ntotal = ((1.0 - volfractoplace) * voleach[ig]);
        volmax = volcrit;
      }

      if (fdmax < (Resolution_safety_coeff * Resolution)) {
        /* entire class is too small for system */
        ntotal = voleach[ig];
      } else if (fdmin < (float)(Resolution_safety_coeff * Resolution)) {
        /* smallest size in this class is too small */
        /* we scale the total pixels to place proportionately */
        volmin = vpmin[ig];
        volmax = vpmax[ig];
        if (volmax <= volmin)
          volmax = volmin + 1;
        critdiam = (float)(Resolution_safety_coeff * Resolution);
        fdmin = critdiam;
        volcrit = diam2vol(critdiam);
        if (volcrit < volmin)
          volcrit = volmin;
        if (volcrit > volmax)
          volcrit = volmax;
        volfractoplace =
            (float)(((float)(volmax - volcrit)) / ((float)(volmax - volmin)));
        ntotal += ((1.0 - volfractoplace) * voleach[ig]);
        volmin = volcrit;
      }

      if (Verbose) {
        printf("\nMindiam = %f Maxdiam = %f pixels", fdmin, fdmax);
        printf("\nMinvol = %d Maxvol = %d pixels", (int)volmin, (int)volmax);
      }

      begin = 2;
      end = numlines;

      numpershape = max(((int)(((float)(voleach[ig] - ntotal) / (float)volmin) /
                               (float)Shapesperbin)),
                        1);

      numpartplaced = 0;

      while (ntotal < voleach[ig]) {
#ifdef DEBUG
        printf("\n\n**Placed %d of %d total pixels in size range %d",
               (int)ntotal, (int)voleach[ig], ig);
        fflush(stdout);
#endif

        /* First choose a size at random from within size class */

        vol = volmin;
        vol += (int)((volmax - volmin) * ran1(Seed));

        pixfrac = (int)(0.03 * vol);

        N_target += vol;
        foundpart = 1;
        toobig = 0;

#ifdef DEBUG
        printf("\nEntering do loop, vol = %d pixels...", vol);
        fflush(stdout);
#endif
        do {
          if (vol > 19) {
            if (ntotal == 0 || (!(numpartplaced % numpershape)) || toobig ||
                !foundpart) {

#ifdef DEBUG
              printf("\nGetting new shape file...");
              fflush(stdout);
#endif

              toobig = 0;
              foundpart = 1;

              /***
               *    Generate the shape by selecting randomly
               *    from collection of anm files in the
               *    directory of interest
               ***/

              /***
               *    Choose a line in the geom file at random
               ***/

              n1 = begin + (int)((end - begin) * ran1(Seed));

              sprintf(filename, "%s%s%c%s", Pathroot, Shapeset, Filesep,
                      line[n1].name);
              anmfile = filehandler("genaggpack", filename, "READ");
              if (!anmfile) {
                freeallmem();
                exit(1);
              }

              /***
               *    Nnn is how many y's are to be used
               *    in series
               *
               *    Read in stored coefficients for
               *    particle of interest
               *
               *    Compute volume and scale anm by
               *    cube root of vol/(volume of particle)
               ***/

              for (n = 0; n <= Nnn; n++) {
                for (m = n; m >= -n; m--) {
                  fscanf(anmfile, "%d %d %f %f", &ii, &jj, &aa1, &aa2);
                  A[n][m] = Complex(aa1, aa2);
                  /* A[n][m] = RCmul((1.0/Resolution),A[n][m]); */
                }
              }
              if (Verbose)
                printf("\nRead and scaled anms");
              fclose(anmfile);

              width = line[n1].width / Resolution;   /* in pixels */
              length = line[n1].length / Resolution; /* in pixels */

              volume = line[n1].volume / (Resolution * Resolution * Resolution);
              saveratio = pow((1.003 * (double)vol / volume), (1. / 3.));

              /*
               * Compute volume once from SH coefficients to see how
               * it compares with the reported volume
               */

              factor = 0.5 * Pi * Pi;
              volumecalc = 0.0;

              maxrx = maxry = maxrz = 0.0;
              for (i = 1; i <= Ntheta; i++) {
                theta = 0.5 * Pi * (Xg[i] + 1.0);
                for (j = 1; j <= Nphi; j++) {
                  phi = Pi * (Xg[j] + 1.0);
                  harm(theta, phi);
                  r1 = Complex(0.0, 0.0);
                  r1 = Cmul(A[0][0], Y[0][0]);
                  for (n = 1; n <= Nnn; n++) {
                    for (m = n; m >= -n; m--) {
                      r1 = Cadd(r1, Cmul(A[n][m], Y[n][m]));
                    }
                  }
                  rx = (r1.r * sin(theta) * cos(phi));
                  ry = (r1.r * sin(theta) * sin(phi));
                  rz = (r1.r * cos(theta));

                  if (fabs(rx) > maxrx)
                    maxrx = fabs(rx);
                  if (fabs(ry) > maxry)
                    maxry = fabs(ry);
                  if (fabs(rz) > maxrz)
                    maxrz = fabs(rz);

                  v1 = sin(theta) / 3.0;
                  v1 *= (r1.r * r1.r * r1.r);
                  v1 *= (Wg[i] * Wg[j]);
                  volumecalc += v1;
                }
              }
              volumecalc *= factor;

              saveratio = pow((1.003 * (double)vol / volumecalc), (1. / 3.));

              /***
               *    Will multiply all SH coefficients by the following
               *    ratio to dilate the size to the correct amount
               ***/

#ifdef DEBUG
              printf("\nOpened %s ; width = %f length = %f pixels\n",
                     line[n1].name, width, length);
              printf("volmin = %d volmax = %d vol = %d pixels", volmin, volmax,
                     vol);
              printf(
                  "\nTabulated volume from anm file before scaling = %f pixels",
                  volume);
              printf("\nCalculated volume from SH coefficients before scaling "
                     "= %f pixels",
                     volumecalc);
              printf("\nCalculated length scaling ratio = %f", saveratio);
              fflush(stdout);
#endif
            }

            /***
             *    Rotate coefficients A[n][m] by a random amount
             *    Store in AA[n][m] matrix, then reassign into A
             *    We remember the ratio from the last particle
             *    provided we haven't used a new shape file
             ***/

            beta = Pi * ran1(Seed);

            cosbeta = cos(beta / 2.0);
            sinbeta = sin(beta / 2.0);

            /* Must not have cosbeta or sinbeta exactly zero */

            if (cosbeta == 0.0) {
              beta += 1.0e-10;
              cosbeta = cos(beta / 2.0);
            }
            if (sinbeta == 0.0) {
              beta += 1.0e-10;
              sinbeta = sin(beta / 2.0);
            }

            alpha = 2.0 * Pi * ran1(Seed);
            gamma = 2.0 * Pi * ran1(Seed);

            for (n = 0; n <= Nnn; n++) {
              for (m = -n; m <= n; m++) {
                AA[n][m] = Complex(0.0, 0.0);
                for (mp = -n; mp <= n; mp++) {
                  realnum =
                      sqrt(fac(n + mp) * fac(n - mp) / fac(n + m) / fac(n - m));
                  ddd = Complex(realnum, 0.0);
                  klow = max(0, m - mp);
                  khigh = min(n - mp, n + m);
                  total = 0.0;
                  for (k = klow; k <= khigh; k++) {
                    abc = pow(-1.0, k + mp - m);
                    abc *= (fac(n + m) / fac(k) / fac(n + m - k));
                    abc *= (fac(n - m) / fac(n - mp - k) / fac(mp + k - m));
                    total += abc * (pow(cosbeta, 2 * n + m - mp - 2 * k)) *
                             (pow(sinbeta, 2 * k + mp - m));
                  }
                  icmplx = Complex(total * cos(mp * alpha),
                                   total * (-sin(mp * alpha)));
                  ddd = Cmul(ddd, icmplx);
                  icmplx = Complex(cos(m * gamma), (-sin(m * gamma)));
                  ddd = Cmul(ddd, icmplx);
                  icmplx = Cmul(A[n][mp], ddd);
                  AA[n][m] = Cadd(AA[n][m], icmplx);
                }

                /***
                 *    All SH coefficients multiplied by ratio to
                 *    dilate the thickness to be in range of the
                 *    bounding sieve openings
                 ***/

                AA[n][m] = RCmul(saveratio, AA[n][m]);
              }
            }

            /***
             *    Compute volume of real particle
             ***/

            factor = 0.5 * Pi * Pi;
            volume = 0.0;

            maxrx = maxry = maxrz = 0.0;
            for (i = 1; i <= Ntheta; i++) {
              theta = 0.5 * Pi * (Xg[i] + 1.0);
              for (j = 1; j <= Nphi; j++) {
                phi = Pi * (Xg[j] + 1.0);
                harm(theta, phi);
                r1 = Complex(0.0, 0.0);
                r1 = Cmul(AA[0][0], Y[0][0]);
                for (n = 1; n <= Nnn; n++) {
                  for (m = n; m >= -n; m--) {
                    r1 = Cadd(r1, Cmul(AA[n][m], Y[n][m]));
                  }
                }
                rx = (r1.r * sin(theta) * cos(phi));
                ry = (r1.r * sin(theta) * sin(phi));
                rz = (r1.r * cos(theta));

                if (fabs(rx) > maxrx)
                  maxrx = fabs(rx);
                if (fabs(ry) > maxry)
                  maxry = fabs(ry);
                if (fabs(rz) > maxrz)
                  maxrz = fabs(rz);

                v1 = sin(theta) / 3.0;
                v1 *= (r1.r * r1.r * r1.r);
                v1 *= (Wg[i] * Wg[j]);
                volume += v1;
              }
            }

            volume *= factor;
            vol1 = volume;
#ifdef DEBUG
            printf("\nComputed volume after scaling = %f pixels", volume);
            printf("\nMaxrx = %f Maxry = %f Maxrz = %f", maxrx, maxry, maxrz);
            fflush(stdout);
#endif

            na = 0;
            partc = 0;
            oldabsdiff = vol;
            absdiff = 0;
            pcount[0] = (int)vol1;
            do {
              if (na == 0) {
                ratio[na] = saveratio;
                pcount[na] = (int)vol1;
#ifdef DEBUG
                printf("\nratio[%d] = %f, pcount[%d] = %d", na, ratio[na], na,
                       pcount[na]);
                fflush(stdout);
#endif
              } else if (na == 1) {
                pcount[na] = partc;
                /*
                ratio[na] = ratio[na-1] * pow(0.5 *
                ((float)pcount[na])/((float)pcount[na-1]),(1./3.));
                */
                ratio[na] = ratio[na - 1] *
                            pow((((float)vol) / (float)pcount[na]), (1. / 3.));
                for (n = 0; n <= Nnn; n++) {
                  for (m = n; m >= -n; m--) {
                    AA[n][m] = RCmul(ratio[na] / ratio[na - 1], AA[n][m]);
                  }
                }
                maxrx *= (ratio[na] / ratio[na - 1]);
                maxry *= (ratio[na] / ratio[na - 1]);
                maxrz *= (ratio[na] / ratio[na - 1]);
#ifdef DEBUG
                printf("\nratio[%d] = %f, pcount[%d] = %d", na, ratio[na], na,
                       pcount[na]);
                fflush(stdout);
#endif
              } else {
                oldabsdiff = abs(pcount[na - 2] - vol);
                absdiff = abs(pcount[na - 1] - vol);
#ifdef DEBUG
                printf("\noldabsdiff = %d, absdiff = %d", oldabsdiff, absdiff);
                fflush(stdout);
#endif
                if (absdiff <= oldabsdiff) {
                  pcount[na] = partc;
                  /*
                  ratio[na] = ratio[na-1] * pow(0.5 *
                  ((float)pcount[na])/((float)pcount[na-1]),(1./3.));
                  */
                  ratio[na] =
                      ratio[na - 1] *
                      pow((((float)vol) / (float)pcount[na]), (1. / 3.));
                  for (n = 0; n <= Nnn; n++) {
                    for (m = n; m >= -n; m--) {
                      AA[n][m] = RCmul(ratio[na] / ratio[na - 1], AA[n][m]);
                    }
                  }
                  maxrx *= (ratio[na] / ratio[na - 1]);
                  maxry *= (ratio[na] / ratio[na - 1]);
                  maxrz *= (ratio[na] / ratio[na - 1]);
#ifdef DEBUG
                  printf("\nratio[%d] = %f, pcount[%d] = %d", na, ratio[na], na,
                         pcount[na]);
                  fflush(stdout);
#endif
                } else {
                  /*
                  ratio[na] = ratio[na - 2];
                  */
                  pcount[na] = partc;
                  ratio[na] =
                      ratio[na - 1] *
                      pow((((float)vol) / (float)pcount[na]), (1. / 3.));
                  for (n = 0; n <= Nnn; n++) {
                    for (m = n; m >= -n; m--) {
                      AA[n][m] = RCmul(ratio[na] / ratio[na - 1], AA[n][m]);
                    }
                  }
                  maxrx *= (ratio[na] / ratio[na - 1]);
                  maxry *= (ratio[na] / ratio[na - 1]);
                  maxrz *= (ratio[na] / ratio[na - 1]);
#ifdef DEBUG
                  printf("\nratio[%d] = %f, pcount[%d] = %d", na, ratio[na], na,
                         pcount[na]);
                  fflush(stdout);
#endif
                }
              }

#ifdef DEBUG
              printf("\nna = %d", na);
              printf("\ntarget volume = %d", vol);
              printf("\ncomputed volume = %f", vol1);
              printf("\nNew scaling ratio = %f", ratio[na]);
              fflush(stdout);
#endif

              /* Digitize the particles all over again */

              /*  Estimate dimensions of bounding box */

              nxp = 3 + ((int)(2.0 * maxrx));
              nyp = 3 + ((int)(2.0 * maxry));
              nzp = 3 + ((int)(2.0 * maxrz));

#ifdef DEBUG
              printf("\nnxp = %d nyp = %d nzp = %d", nxp, nyp, nzp);
#endif

              /*
              if (Itz > 0) {
                  nxp += Itz + 1;
                  nyp += Itz + 1;
                  nzp += Itz + 1;
              }
              */

              if ((nxp < (int)(0.8 * Xsyssize)) &&
                  (nyp < (int)(0.8 * Ysyssize)) &&
                  (nzp < (int)(0.8 * Zsyssize))) {
                foundpart = 1;
                partc = image(&nxp, &nyp, &nzp);
                if (partc == 0) {
                  if (Verbose)
                    printf("\nCurrent particle too big for system.");
                  toobig = 1;
                  foundpart = 0;
                } else {
#ifdef DEBUG
                  printf("\nAfter image function, nominal particle volume %d, "
                         "actual %d pixels",
                         (int)vol, (int)partc);
                  fflush(stdout);
#endif
                  toobig = 0;
                  foundpart = 1;
                }
              } else {
                if (Verbose)
                  printf("\nCurrent particle too big for system.");
                toobig = 1;
                foundpart = 0;
              }
              saveratio = ratio[na];
              na++;

            } while (abs(partc - vol) > max(4, pixfrac) && na < 3 && !toobig);

#ifdef DEBUG
            printf("\nConverged? partc = %d and vol = %d, na = %d", partc, vol,
                   na);
            fflush(stdout);
#endif

            if (!toobig && foundpart) {
#ifdef DEBUG
              printf("\nDone scaling the anms");
              fflush(stdout);
#endif

              /*
              if (partc != vol) {
                  #ifdef DEBUG
                  printf("\nAdditional adjustment needed to match volume, partc
              = %d",partc); fflush(stdout); #endif extpix = adjustvol(vol -
              partc,nxp,nyp,nzp); partc += extpix; #ifdef DEBUG printf("\nAfter
              adjustment, partc = %d",partc); fflush(stdout); #endif
              }
              */

              /***
               *    If dispersion is desired, add false layer around
               *    the particle now (will be stripped when particle
               *    is actually placed)
               ***/

              if (Dispdist > 0) {
                addlayer(nxp, nyp, nzp);
              }

              if (Itz > 0) {
                additz(nxp, nyp, nzp);
              }

              /***
               *    Done generating the shape image for the particle
               ***/

              nnxp = nxp;
              nnyp = nyp;
              nnzp = nzp;

            } else {
              toobig = 1;
              foundpart = 0;
            }

          } else {
            if (vol > 1) {
              partc = smallimage(&nxp, &nyp, &nzp, vol);
              orient = 1 + (int)(14.0 * ran1(Seed));
            } else {
              partc = orient = 1;
            }
            if (Dispdist > 0) {
              nxp += Dispdist + 1;
              nyp += Dispdist + 1;
              nzp += Dispdist + 1;
              addlayer(nxp, nyp, nzp);
            }
            if (Itz > 0) {
              nxp += Itz + 1;
              nyp += Itz + 1;
              nzp += Itz + 1;
              additz(nxp, nyp, nzp);
            }
            nnxp = nxp;
            nnyp = nyp;
            nnzp = nzp;
            foundpart = 1;
          }
        } while (!foundpart);

        tries = 0;

        /* Stop after MAXTRIES random tries */

        do {

          tries++;

          /***
           *    Generate a random location for the lower
           *    corner of the bounding box on the particle
           ***/

          x = (int)((float)Xsyssize * ran1(Seed));
          y = (int)((float)Ysyssize * ran1(Seed));
          z = (int)((float)Zsyssize * ran1(Seed));

          /***
           *    See if the particle will fit at x,y,z
           *    Include dispersion distance when checking
           *    to ensure requested separation between spheres
           ***/

#ifdef DEBUG
          printf("\nAbout to go into checkpart...");
          printf("\n\tx = %d y = %d z = %d", x, y, z);
          printf("\n\tnnxp = %d nnyp = %d nnzp = %d", nnxp, nnyp, nnzp);
          printf("\n\tvol = %d", (int)vol);
          fflush(stdout);
#endif

          nofit =
              checkpart(x, y, z, nnxp, nnyp, nnzp, vol, Npart + 1, 0, Check);

          if ((tries > MAXTRIES) && (Dispdist == 2)) {
            tries = 0;
            Dispdist--;
            striplayer(nnxp, nnyp, nnzp);
          }

          if (tries > MAXTRIES) {
            printf("Could not place particle %d\n", Npart);
            printf("\tafter %d random attempts\n\n", MAXTRIES);
            printf("\nTotal volume desired in this bin was %d", voleach[ig]);
            printf("\nActual volume _placed  in this bin was %d", ntotal);
            printf("\nWas working on bin %d out of %d\n", ig, numgen);
            warning("genaggpack", "Could not place a particle");
            fflush(stdout);
            return;
          }

        } while (nofit);

        /***
         *    Place the particle with lower corner of bounding
         *    box at x,y,z
         ***/

        Npart++;
        if (Npart > Npartc) {
          printf("Too many particles being generated \n");
          printf("\tUser needs to increase value of NPARTC\n");
          printf("\tat top of C-code\n\n");
          printf("\nTotal volume desired in this bin was %d", voleach[ig]);
          printf("\nActual volume _placed  in this bin was %d", ntotal);
          printf("\nWas working on bin %d out of %d\n", ig, numgen);
          warning("genaggpack", "Too many particles");
          printf("\nWas working on bin %d out of %d\n", ig, numgen);
          fflush(stdout);
          return;
        }

#ifdef DEBUG
        printf("\n\t\tAbout to place an aggregate particle...");
        printf("\n\t\t\tx = %d y = %d z = %d", x, y, z);
        printf("\n\t\t\tnnxp = %d nnyp = %d nnzp = %d", nnxp, nnyp, nnzp);
        printf("\n\t\t\tvol = %d", (int)vol);
#endif
        nump = checkpart(x, y, z, nnxp, nnyp, nnzp, vol, Npart + 1, phaseid,
                         Place);
        ntotal += nump;
        N_total += nump;
        numpartplaced++;
        if (Verbose)
          printf("\n\t\t\tntotal = %d out of %d", ntotal, voleach[ig]);
        if (Verbose)
          printf("\n\t\t\tN_total = %d N_target = %d", N_total, N_target);

        /***************  PUT NICK'S STUFF RIGHT HERE ***********************/
        /*
                     Centroid:  X-coord = x + ((0.5*nnxp)+0.01);
                     Centroid:  Y-coord = y + ((0.5*nnyp)+0.01);
                     Centroid:  Z-coord = z + ((0.5*nnzp)+0.01);
                     Need to output the AA[n][m] matrix one row at a time
        */
        cx = (int)(x + ((0.5 * nnxp) + 0.01));
        if (cx >= Xsyssize)
          cx -= Xsyssize;
        if (cx < 0)
          cx += Xsyssize;
        cy = (int)(y + ((0.5 * nnyp) + 0.01));
        if (cy >= Ysyssize)
          cy -= Ysyssize;
        if (cy < 0)
          cy += Ysyssize;
        cz = (int)(z + ((0.5 * nnzp) + 0.01));
        if (cz >= Zsyssize)
          cz -= Zsyssize;
        if (cz < 0)
          cz += Zsyssize;

        fprintf(fpout, "%d %d %d %d\n", cx, cy, cz, (int)Nnn);
        for (n = 0; n <= Nnn; n++) {
          for (m = n; m >= -n; m--) {
            fprintf(fpout, "%d %d %.10f %.10f\n", n, m, AA[n][m].r, AA[n][m].i);
          }
        }
      }

      if (Verbose) {
        printf("\nTotal volume desired in this bin was %d", voleach[ig]);
        printf("\nActual volume _placed  in this bin was %d", ntotal);
        fflush(stdout);
      }
    }

    break;

  } /* Thus ends the ginormous switch statement */

  return;
}

/***
 *    create
 *
 *    Routine to obtain user input and create a starting
 *    microstructure.
 *
 *     Arguments:    0 for coarse aggregates, 1 for fine aggregates
 *    Returns:    Nothing
 *
 *    Calls:        genparticles
 *    Called by:    main program
 ***/
void create(int type, int numtimes) {
  int i, j, numsize[NUMSOURCES];
  int num_sources, ns;
  int vol[NUMSOURCES][MAXSIZECLASSES], inval1;
  int ip, diam, radmin[NUMSOURCES][MAXSIZECLASSES],
      radmax[NUMSOURCES][MAXSIZECLASSES];
  float rvalmin, rvalmax, val1, val2;
  char buff[MAXSTRING], gaussname[MAXSTRING];
  char typestring[10], scratchname[MAXSTRING], instring[MAXSTRING];
  float fradmin[NUMSOURCES][MAXSIZECLASSES],
      fradmax[NUMSOURCES][MAXSIZECLASSES];
  FILE *fgauss, *fscratch;

  /* Initialize local arrays */

  num_sources = 1;

  for (i = 0; i < NUMSOURCES; i++) {
    numsize[i] = 0;
    for (j = 0; j < MAXSIZECLASSES; j++) {
      vol[i][j] = 0;
      radmin[i][j] = radmax[i][j] = 0;
      fradmin[i][j] = fradmax[i][j] = 0.0;
    }
  }

  if (type == (int)COARSE)
    strcpy(typestring, "coarse");
  if (type == (int)FINE)
    strcpy(typestring, "fine");

  printf("\nAdd SPHERES (0) or REAL-SHAPE (1) particles? ");
  read_string(instring, sizeof(instring));
  Shape = atoi(instring);
  printf("%d\n", Shape);

  if (numtimes == 0) {
    sprintf(scratchname, "scratchaggfile.dat");
    fscratch = filehandler("genaggpack", scratchname, "WRITE");
    if (!fscratch) {
      freeallmem();
      bailout("genaggpack", "Could not open aggregate structure file");
    }
    fprintf(fscratch, "%d %d %d\n", Xsyssize, Ysyssize, Zsyssize);
    Mindimen = Xsyssize;
    if (Ysyssize < Mindimen)
      Mindimen = Ysyssize;
    if (Zsyssize < Mindimen)
      Mindimen = Zsyssize;
    Itz = 0;
    if (Resolution < FINEAGGRES)
      Itz = 1;
  } else {
    sprintf(scratchname, "scratchaggfile.dat");
    fscratch = filehandler("genaggpack", scratchname, "APPEND");
    if (!fscratch) {
      freeallmem();
      bailout("genaggpack", "Could not open aggregate structure file");
    }
  }

  printf("Where is the %s aggregate shape database?", typestring);
  printf("\n(Include final separator in path) ");
  read_string(buff, sizeof(buff));
  Filesep = buff[strlen(buff) - 1];
  if ((Filesep != '/') && (Filesep != '\\')) {
    printf("\nNo final file separator detected.  Using /");
    Filesep = '/';
  }
  printf("%s\n", buff);
  sprintf(Pathroot, "%s", buff);

  printf("\nHow many %s aggregate sources (1 - %d)? ", typestring,
         (int)NUMSOURCES);
  read_string(buff, sizeof(buff));
  num_sources = atoi(buff);
  if (num_sources < 1 || num_sources > (int)NUMSOURCES) {
    freeallmem();
    bailout("genaggpack", "Illegal number of aggregate sources");
  }

  if (Shape != SPHERES) {

    /* Determine number of Gaussian quadrature points from file */

    if (Ntheta == 0) {
      sprintf(gaussname, "%sgauss120.dat", Pathroot);
      if (Verbose)
        printf("\nGauss file name is %s", gaussname);
      fgauss = filehandler("genaggpack", gaussname, "READ");
      if (!fgauss) {
        freeallmem();
        exit(1);
      }

      while (!feof(fgauss)) {
        fscanf(fgauss, "%f %f", &val1, &val2);
        if (!feof(fgauss))
          Ntheta++;
      }
      fclose(fgauss);
      Nphi = Ntheta;
    }

    /* Allocate memory for Gaussian quadrature points */

    if (!Xg) {
      Xg = fvector(Ntheta + 1);
      if (!Xg) {
        freeallmem();
        bailout("genaggpack", "Could not allocate memory for Xg");
        exit(1);
      }
    }

    if (!Wg) {
      Wg = fvector(Nphi + 1);
      if (!Wg) {
        freeallmem();
        bailout("genaggpack", "Could not allocate memory for Wg");
        exit(1);
      }
    }

    /* Read Gaussian quadrature points from file */

    sprintf(gaussname, "%sgauss120.dat", Pathroot);
    if (Verbose)
      printf("\nGauss file name is %s", gaussname);
    fgauss = filehandler("genaggpack", gaussname, "READ");
    if (!fgauss) {
      freeallmem();
      exit(1);
    }

    for (i = 1; i <= Ntheta; i++) {
      fscanf(fgauss, "%f %f", &Xg[i], &Wg[i]);
    }
    fclose(fgauss);

    /***
     *    Allocate memory for the spherical harmonic arrays and
     *    for the Bbox array (only needed for real shapes)
     ***/

    if (!A)
      A = complexmatrix(0, Nnn, -Nnn, Nnn);
    if (!AA)
      AA = complexmatrix(0, Nnn, -Nnn, Nnn);
    if (!Y)
      Y = complexmatrix(0, Nnn, -Nnn, Nnn);
    if (!Bbox)
      Bbox = ibox(Xsyssize, Ysyssize, Zsyssize);

    if (!A || !AA || !Y || !Bbox) {
      freeallmem();
      bailout("genaggpack", "Memory allocation error");
      fflush(stdout);
      exit(1);
    }
  }

  for (ns = 0; ns < num_sources; ns++) {
    printf("Source %d:  Take %s aggregate shapes from what data set?", ns + 1,
           typestring);
    printf("\n(No separator at the beginning or end) ");
    read_string(Shapeset, sizeof(Shapeset));
    printf("%s\n", Shapeset);
    if ((Shapeset[strlen(Shapeset) - 1] == '/') ||
        (Shapeset[strlen(Shapeset) - 1] == '\\')) {
      Shapeset[strlen(Shapeset) - 1] = '\0';
    }

    printf("Enter number of different size particles ");
    printf("to use(max. is %d)\n", MAXSIZECLASSES);
    read_string(instring, sizeof(instring));
    numsize[ns] = atoi(instring);
    printf("%d \n", numsize[ns]);

    if (numsize[ns] > MAXSIZECLASSES || numsize[ns] < 0) {
      freeallmem();
      bailout("genaggpack", "Bad value for numsize");
      exit(1);
    } else {
      printf("Enter information for ");
      printf("each particle class (largest size 1st)\n");

      /***
       *    Obtain input for each size class of particles
       ***/

      for (ip = 0; ip < numsize[ns]; ip++) {

        printf("Enter total volume of particles of class %d in voxels\n",
               ip + 1);
        read_string(instring, sizeof(instring));
        inval1 = atoi(instring);
        printf("%d \n", inval1);
        vol[ns][ip] = inval1;
        printf("Enter smallest effective radius (in mm) ");
        printf("of particles in size class %d \n", ip + 1);
        printf("(Real number <= %f please) \n", (float)(Mindimen / 2));
        read_string(buff, sizeof(buff));
        printf("%s\n", buff);
        rvalmin = atof(buff);
        printf("Enter largest effective radius (in mm) ");
        printf("of particles in size class %d \n", ip + 1);
        printf("(Real number <= %f please) \n", (float)(Mindimen / 2));
        read_string(buff, sizeof(buff));
        printf("%s\n", buff);
        rvalmax = atof(buff);
        if ((2.0 * rvalmin) < (float)(Resolution_safety_coeff * Resolution)) {
          printf("WARNING:  Minimum particle radius is too small for the\n");
          printf("          resolution of the system.  Some small particles\n");
          printf("          may not be resolved in the image.\n");
          /* rvalmin = (Resolution_safety_coeff * Resolution); */
        }
        if ((2.0 * rvalmin) > (float)(Size_safety_coeff * Mindimen)) {
          printf("WARNING:  Entire size class is too large for the\n");
          printf("          size of the system.  This class will not\n");
          printf("          be resolved in the image.\n");
          /*
          freeallmem();
          bailout("genaggpack","Entire size class too large for system size");
          exit(1);
          */
        }
        if ((2.0 * rvalmax) < (Resolution_safety_coeff * Resolution)) {
          printf("WARNING:  Entire size class is too small for the\n");
          printf("          resolution of the system.  This class will not\n");
          printf("          be resolved in the image.\n");
          /*
          freeallmem();
          bailout("genaggpack","Entire size class too fine for system
          resolution"); exit(1);
          */
        }
        if ((2.0 * rvalmax) > (float)(Size_safety_coeff * Mindimen)) {
          printf("WARNING:  Maximum particle radius is too large for the\n");
          printf("          size of the system.  Some large particles\n");
          printf("          may not be resolved in the image.\n");
          /* rvalmax = (float)(Size_safety_coeff * Mindimen); */
        }

        fradmin[ns][ip] = rvalmin / Resolution;       /* pixel units now */
        fradmax[ns][ip] = rvalmax / Resolution;       /* pixel units now */
        radmin[ns][ip] = (int)(rvalmin / Resolution); /* pixel units now */
        radmax[ns][ip] = (int)(rvalmax / Resolution); /* pixel units now */
        diam = 1 + (2 * radmin[ns][ip]);
        Volpartmin[ns][ip] = diam2vol((float)diam);
        diam = 1 + (2 * radmax[ns][ip]);
        Volpartmax[ns][ip] = diam2vol((float)diam);
      }

      /***
       *    Place particles at random
       ***/
    }
  }

  /***
   *    Place particles at random
   ***/

  genparticles(type, num_sources, vol, fradmin, fradmax, fscratch);
  fclose(fscratch);
  return;
}

/***
 *    measure
 *
 *    Routine to assess global phase fractions present
 *    in 3-D system
 *
 *     Arguments:    None
 *     Returns:    Nothing
 *
 *    Calls:        No other routines
 *    Called by:    main program
 ***/
void measure(void) {
  int npor, nagg, nitz;
  register int i, j, k;
  char filen[MAXSTRING];
  int valph;
  FILE *outfile;

  /* Counters for the various phase fractions */

  npor = nagg = nitz = 0;
  ;

  /* Check all pixels in 3-D microstructure */

  printf("\nEnter full path and name of file for writing statistics: ");
  read_string(filen, sizeof(filen));
  printf("\n%s\n", filen);
  outfile = filehandler("genaggpack", filen, "WRITE");
  if (!outfile) {
    freeallmem();
    exit(1);
  }

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        valph = Aggreal[i][j][k];
        switch (valph) {
        case POROSITY:
          npor++;
          break;
        case ITZ:
          nitz++;
          break;
        default:
          nagg++;
          break;
        }
      }
    }
  }

  /* Output results */

  fprintf(outfile, "\nPhase counts are: \n");
  fprintf(outfile, "\tPorosity = %d \n", npor);
  fprintf(outfile, "\tAggregate = %d \n", nagg);
  fprintf(outfile, "\tITZ = %d \n", nitz);
  fclose(outfile);

  return;
}

/***
 *    connect
 *
 *    Routine to assess the connectivity (percolation)
 *    of a single phase.  Two matrices are used here:
 *
 *                (1) for the current burnt locations
 *                (2) for the other to store the newly found
 *                    burnt locations
 *
 *     Arguments:    None
 *     Returns:    Nothing
 *
 *    Calls:        No other routines
 *    Called by:    main program
 ***/
void connect(void) {
  register int i, j, k;
  int inew, ntop, nthrough, ncur, nnew, ntot;
  int *nmatx, *nmaty, *nmatz, *nnewx, *nnewy, *nnewz;
  int xcn, ycn, zcn, npix, x1, y1, z1, igood;
  int jnew, icur;
  char instring[MAXSTRING];

  nmatx = nmaty = nmatz = NULL;
  nnewx = nnewy = nnewz = NULL;

  nmatx = ivector(Maxburning);
  nmaty = ivector(Maxburning);
  nmatz = ivector(Maxburning);
  nnewx = ivector(Maxburning);
  nnewy = ivector(Maxburning);
  nnewz = ivector(Maxburning);

  if (!nmatx || !nmaty || !nmatz || !nnewx || !nnewy || !nnewz) {

    freeallmem();
    bailout("genaggpack", "Memory allocation failure");
    fflush(stdout);
    exit(1);
  }

  printf("Enter phase to analyze 0) pores 1) Aggregate 2) ITZ  \n");
  read_string(instring, sizeof(instring));
  npix = atoi(instring);
  printf("%d \n", npix);
  if ((npix != POROSITY) && (npix != AGG) && (npix != ITZ)) {
    freeallmem();
    bailout("connect", "Bad ID to analyze connectivity");
    exit(1);
  }

  /***
   *    Counters for number of pixels of phase
   *    accessible from top surface and number which
   *    are part of a percolated pathway
   ***/

  ntop = 0;
  nthrough = 0;

  /***
   *    Percolation is assessed from top to
   *    bottom ONLY, and burning algorithm is
   *    periodic in x and y directions
   ***/

  k = 0;
  for (i = 0; i < Xsyssize; i++) {
    for (j = 0; j < Ysyssize; j++) {

      ncur = 0;
      ntot = 0;
      igood = 0; /* Indicates if bottom has been reached */

      if (((Aggreal[i][j][k] == npix) &&
           ((Aggreal[i][j][Zsyssize - 1] == npix) ||
            (Aggreal[i][j][Zsyssize - 1] == (npix + Burnt)))) ||
          ((Aggreal[i][j][Zsyssize - 1] > 0) && (Aggreal[i][j][k] > 0) &&
           (Aggreal[i][j][k] < Burnt) && (npix == AGG || npix == ITZ))) {

        /* Start a burn front */

        Aggreal[i][j][k] += Burnt;
        ntot++;
        ncur++;

        /***
         *    Burn front is stored in matrices
         *    nmat* and nnew*
         ***/

        nmatx[ncur] = i;
        nmaty[ncur] = j;
        nmatz[ncur] = 0;

        /* Burn as long as new (fuel) pixels are found */

        do {
          nnew = 0;
          for (inew = 1; inew <= ncur; inew++) {

            xcn = nmatx[inew];
            ycn = nmaty[inew];
            zcn = nmatz[inew];

            /* Check all six neighbors */

            for (jnew = 1; jnew <= 6; jnew++) {
              x1 = xcn;
              y1 = ycn;
              z1 = zcn;
              switch (jnew) {
              case 1:
                x1--;
                if (x1 < 0)
                  x1 += Xsyssize;
                break;
              case 2:
                x1++;
                if (x1 >= Xsyssize)
                  x1 -= Xsyssize;
                break;
              case 3:
                y1--;
                if (y1 < 0)
                  y1 += Ysyssize;
                break;
              case 4:
                y1++;
                if (y1 >= Ysyssize)
                  y1 -= Ysyssize;
                break;
              case 5:
                z1--;
                if (z1 < 0)
                  z1 += Zsyssize;
                break;
              case 6:
                z1++;
                if (z1 >= Zsyssize)
                  z1 -= Zsyssize;
                break;
              default:
                break;
              }

              /***
               *    Nonperiodic in z direction so
               *    be sure to remain in the 3-D box
               ****/

              if ((z1 >= 0) && (z1 < Zsyssize)) {
                if ((Aggreal[x1][y1][z1] == npix) ||
                    ((Aggreal[x1][y1][z1] > 0) &&
                     (Aggreal[x1][y1][z1] < Burnt) &&
                     (npix == AGG || npix == ITZ))) {

                  ntot++;
                  Aggreal[x1][y1][z1] += Burnt;
                  nnew++;

                  if (nnew >= Maxburning) {
                    printf("error in size of nnew \n");
                  }

                  nnewx[nnew] = x1;
                  nnewy[nnew] = y1;
                  nnewz[nnew] = z1;

                  /***
                   *    See if bottom of system
                   *    has been reached
                   ***/

                  if (z1 == Zsyssize - 1)
                    igood = 1;
                }
              }
            }
          }

          if (nnew > 0) {

            ncur = nnew;

            /* update the burn front matrices */

            for (icur = 1; icur <= ncur; icur++) {
              nmatx[icur] = nnewx[icur];
              nmaty[icur] = nnewy[icur];
              nmatz[icur] = nnewz[icur];
            }
          }

        } while (nnew > 0);

        ntop += ntot;
        if (igood)
          nthrough += ntot;
      }
    }
  }

  printf("Phase ID= %d \n", npix);
  printf("Number accessible from top= %d \n", ntop);
  printf("Number contained in through pathways= %d \n", nthrough);

  /***
   *    Return the burnt sites to their original
   *    phase values
   ***/

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {
        if (Aggreal[i][j][k] >= Burnt) {
          Aggreal[i][j][k] -= Burnt;
        }
      }
    }
  }

  free(nmatx);
  free(nmaty);
  free(nmatz);
  free(nnewx);
  free(nnewy);
  free(nnewz);

  return;
}

/***
 *    outmic
 *
 *    Routine to output final microstructure to file
 *
 *     Arguments:    None
 *     Returns:    Nothing
 *
 *    Calls:        No other routines
 *    Called by:    main program
 ***/
void outmic(void) {
  int ix, iy, iz, valout;
  int transparent;
  char filen[MAXSTRING], buff[MAXSTRING], filestruct[MAXSTRING];
  char filepart[MAXSTRING], ch;
  char *x;
  FILE *outfile, *partfile, *infile;

  printf("Enter name of file for final packing image\n");
  read_string(filen, sizeof(filen));
  printf("%s\n", filen);

  transparent = 1;
  printf("Show cement binder as opaque (0) or transparent (1)?\n");
  read_string(buff, sizeof(buff));
  printf("%s\n", buff);
  transparent = atoi(buff);

  outfile = filehandler("genaggpack", filen, "WRITE");
  if (!outfile) {
    freeallmem();
    exit(1);
  }

  /* Create particle id file name */
  strcpy(filepart, filen);
  x = strrchr(filepart, '.');
  strcpy(x, ".pimg");

  partfile = filehandler("genaggpack", filepart, "WRITE");
  if (!outfile) {
    freeallmem();
    exit(1);
  }

  /***
   *    Images must carry along information about the
   *    VCCTL software version used to create the file, the system
   *    size, and the image resolution.
   ***/

  if (write_imgheader(outfile, Xsyssize, Ysyssize, Zsyssize, Resolution)) {
    fclose(outfile);
    freeallmem();
    bailout("genaggpack", "Error writing image header");
    exit(1);
  }

  if (write_imgheader(partfile, Xsyssize, Ysyssize, Zsyssize, Resolution)) {
    fclose(outfile);
    fclose(partfile);
    freeallmem();
    bailout("genaggpack", "Error writing particle image header");
    exit(1);
  }

  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {
        valout = Agg[ix][iy][iz];
        fprintf(partfile, "%d\n", valout);
        valout = Aggreal[ix][iy][iz];
        /*
        if ((transparent != 1) && valout == POROSITY)
          valout = C3A;
        */
        fprintf(outfile, "%d\n", valout);
      }
    }
  }

  fclose(outfile);

  sprintf(filestruct, "%s.struct", filen);
  outfile = filehandler("genaggpack", filestruct, "WRITE");
  infile = filehandler("genaggpack", "scratchaggfile.dat", "READ");

  fprintf(outfile, "%d\n", Npart);
  while (!feof(infile)) {
    ch = getc(infile);
    if (!feof(infile))
      putc(ch, outfile);
  }

  fclose(infile);
  fclose(outfile);
  return;
}

/******************************************************
 *
 *    harm
 *
 *     Compute spherical harmonics (complex) for a value
 *     of x = cos(theta), phi = angle phi so
 *     -1 < x < 1, P(n,m), -n < m < n, 0 < n
 *
 *     Uses two recursion relations plus exact formulas for
 *     the associated Legendre functions up to n=8
 *
 *    Arguments:    double theta and phi coordinates
 *    Returns:    Nothing
 *
 *    Calls:         fac
 *    Called by:  main
 *
 ******************************************************/
void harm(double theta, double phi) {
  int i, m, n, mm, nn;
  double x, s, xn, xm;
  double realnum;
  double p[NNN + 1][2 * (NNN + 1)];
  fcomplex fc1, fc2, fc3;

  x = cos(theta);
  s = (double)(sqrt((double)(1.0 - (x * x))));

  for (n = 0; n <= Nnn; n++) {
    for (m = 0; m <= 2 * (Nnn); m++) {
      p[n][m] = 0.0;
    }
  }

  p[0][0] = 1.0;
  p[1][0] = x;
  p[1][1] = s;
  p[2][0] = 0.5 * (3. * x * x - 1.);
  p[2][1] = 3. * x * s;
  p[2][2] = 3. * (1. - x * x);
  p[3][0] = 0.5 * x * (5. * x * x - 3.);
  p[3][1] = 1.5 * (5. * x * x - 1.) * s;
  p[3][2] = 15. * x * (1. - x * x);
  p[3][3] = 15. * (pow(s, 3));
  p[4][0] = 0.125 * (35. * (pow(x, 4)) - 30. * x * x + 3.);
  p[4][1] = 2.5 * (7. * x * x * x - 3. * x) * s;
  p[4][2] = 7.5 * (7. * x * x - 1.) * (1. - x * x);
  p[4][3] = 105. * x * (pow(s, 3));
  p[4][4] = 105. * (pow((1. - x * x), 2));
  p[5][0] = 0.125 * x * (63. * (pow(x, 4)) - 70. * x * x + 15.);
  p[5][1] = 0.125 * 15. * s * (21. * (pow(x, 4)) - 14. * x * x + 1.);
  p[5][2] = 0.5 * 105. * x * (1. - x * x) * (3. * x * x - 1.);
  p[5][3] = 0.5 * 105. * (pow(s, 3)) * (9. * x * x - 1.);
  p[5][4] = 945. * x * (pow((1. - x * x), 2));
  p[5][5] = 945. * (pow(s, 5));
  p[6][0] =
      0.0625 * (231. * (pow(x, 6)) - 315. * (pow(x, 4)) + 105. * x * x - 5.);
  p[6][1] = 0.125 * 21. * x * (33. * (pow(x, 4)) - 30. * x * x + 5.) * s;
  p[6][2] =
      0.125 * 105. * (1. - x * x) * (33. * (pow(x, 4)) - 18. * x * x + 1.);
  p[6][3] = 0.5 * 315. * (11. * x * x - 3.) * x * (pow(s, 3));
  p[6][4] = 0.5 * 945. * (1. - x * x) * (1. - x * x) * (11. * x * x - 1.);
  p[6][6] = 10395. * pow((1. - x * x), 3);
  p[7][0] = 0.0625 * x *
            (429. * (pow(x, 6)) - 693. * (pow(x, 4)) + 315. * x * x - 35.);
  p[7][1] = 0.0625 * 7. * s *
            (429. * (pow(x, 6)) - 495. * (pow(x, 4)) + 135. * x * x - 5.);
  p[7][2] = 0.125 * 63. * x * (1. - x * x) *
            (143. * (pow(x, 4)) - 110. * x * x + 15.);
  p[7][3] =
      0.125 * 315. * (pow(s, 3)) * (143. * (pow(x, 4)) - 66. * x * x + 3.);
  p[7][4] = 0.5 * 3465. * x * (1. - x * x) * (1. - x * x) * (13. * x * x - 3.);
  p[7][5] = 0.5 * 10395. * (pow(s, 5)) * (13. * x * x - 1.);
  p[7][6] = 135135. * x * (1. - x * x) * (1. - x * x) * (1. - x * x);
  p[7][7] = 135135. * (pow(s, 7));
  p[8][0] = (1. / 128.) * (6435. * (pow(x, 8)) - 12012. * (pow(x, 6)) +
                           6930. * (pow(x, 4)) - 1260. * x * x + 35.);
  p[8][1] = 0.0625 * 9. * x * s *
            (715. * (pow(x, 6)) - 1001. * (pow(x, 4)) + 385. * x * x - 35.);
  p[8][2] = 0.0625 * 315. * (1. - x * x) *
            (143. * (pow(x, 6)) - 143. * (pow(x, 4)) + 33. * x * x - 1.);
  p[8][3] =
      0.125 * 3465. * x * (pow(s, 3)) * (39. * (pow(x, 4)) - 26. * x * x + 3.);
  p[8][4] = 0.125 * 10395. * (1. - x * x) * (1. - x * x) *
            (65. * (pow(x, 4)) - 26. * x * x + 1.);
  p[8][5] = 0.5 * 135135. * x * (pow(s, 5)) * (5. * x * x - 1.);
  p[8][6] = 0.5 * 135135. * (pow((1. - x * x), 3)) * (15. * x * x - 1.);
  p[8][7] = 2027025. * x * (pow(s, 7));
  p[8][8] = 2027025. * (pow((1. - x * x), 4));

  /* Now generate spherical harmonics for n = 0,8 (follows Arfken) */

  for (n = 0; n <= 8; n++) {

    /* does n = 0 separately */

    if (n == 0) {
      Y[0][0].r = 1.0 / (sqrt(4.0 * Pi));
      Y[0][0].i = 0.0;
    } else {
      for (m = n; m >= -n; m--) {
        if (m >= 0) {
          fc1 = Complex(cos(m * phi), sin(m * phi));
          realnum = (pow(-1., m)) *
                    sqrt(((2 * n + 1) / 4. / Pi) * fac(n - m) / fac(n + m)) *
                    p[n][m];
          Y[n][m] = RCmul(realnum, fc1);

        } else if (m < 0) {
          mm = -m;
          fc1 = Conjg(Y[n][m]);
          realnum = pow(-1.0, mm);
          Y[n][m] = RCmul(realnum, fc1);
        }
      }
    }
  }

  /***
   *    Use recursion relations for n >= 9
   *    Do recursion on spherical harmonics, because they are
   *    better behaved numerically
   ***/

  for (n = 9; n <= Nnn; n++) {
    for (m = 0; m <= n - 2; m++) {
      xn = (double)(n - 1);
      xm = (double)m;
      realnum = (2. * xn + 1.) * x;
      Y[n][m] = RCmul(realnum, Y[n - 1][m]);
      realnum =
          -sqrt((2. * xn + 1.) * ((xn * xn) - (xm * xm)) / (2. * xn - 1.));
      fc1 = RCmul(realnum, Y[n - 2][m]);
      Y[n][m] = Cadd(Y[n][m], fc1);
      realnum = (sqrt((2. * xn + 1.) * (pow((xn + 1.), 2) - (xm * xm)) /
                      (2. * xn + 3.)));
      Y[n][m] = RCmul((1.0 / realnum), Y[n][m]);
    }

    nn = (2 * n) - 1;
    p[n][n] = pow(s, n);
    for (i = 1; i <= nn; i += 2) {
      p[n][n] *= (double)i;
    }

    fc1 = Complex(cos(n * phi), sin(n * phi));
    realnum = (pow(-1., n)) *
              sqrt(((2 * n + 1) / 4. / Pi) * fac(n - n) / fac(n + n)) * p[n][n];
    Y[n][n] = RCmul(realnum, fc1);

    /***
     *    Now do second to the top m=n-1 using the exact m=n,
     *    and the recursive m=n-2 found previously
     ***/

    xm = (double)(n - 1);
    xn = (double)n;

    realnum = -1.0;
    fc1 = Complex(cos(phi), sin(phi));
    fc2 = Cmul(fc1, Y[n][n - 2]);
    Y[n][n - 1] = RCmul(realnum, fc2);
    realnum =
        (xn * (xn + 1.) - xm * (xm - 1.)) / sqrt((xn + xm) * (xn - xm + 1.));
    Y[n][n - 1] = RCmul(realnum, Y[n][n - 1]);

    realnum = sqrt((xn - xm) * (xn + xm + 1.));
    fc1 = Complex(cos(phi), -sin(phi));
    fc2 = Cmul(fc1, Y[n][n]);
    fc3 = RCmul(realnum, fc2);
    Y[n][n - 1] = Csub(Y[n][n - 1], fc3);

    realnum = (s / 2.0 / xm / x);
    Y[n][n - 1] = RCmul(realnum, Y[n][n - 1]);
  }

  /* now fill in -m terms */

  for (n = 0; n <= Nnn; n++) {
    for (m = -1; m >= -n; m--) {
      mm = -m;
      realnum = pow(-1.0, mm);
      fc1 = Conjg(Y[n][mm]);
      Y[n][m] = RCmul(realnum, fc1);
    }
  }

  return;
}

/******************************************************
 *
 *    fac
 *
 *    This is the factorial function, as used in function harm
 *
 *    Arguments:    int n
 *    Returns:    double fact;
 *
 *    Calls: No other routines
 *    Called by:  harm
 *
 ******************************************************/
double fac(int j) {
  int i;
  double fact;

  if (j <= 1) {
    fact = 1.0;
  } else {
    fact = 1.0;
    for (i = 1; i <= j; i++) {
      fact *= (double)i;
    }
  }

  return fact;
}

/***
 *    freeallmem
 *
 *    Releases all dynamically allocated memory for this
 *    program.
 *
 *    SHOULD ONLY BE CALLED IF ALL MEMORY HAS ALREADY BEEN
 *    DYNAMICALLY ALLOCATED
 *
 *    Arguments:    None
 *    Returns:    Nothing
 *
 *    Calls:        free_ivector, free_fvector, free_fcube
 *    Called by:    main,dissolve
 *
 ***/
void freeallmem(void) {

  if (Agg)
    free_ibox(Agg, Xsyssize, Ysyssize);
  if (Aggreal)
    free_ibox(Aggreal, Xsyssize, Ysyssize);
  if (Bbox)
    free_ibox(Bbox, Xsyssize, Ysyssize);
  if (Xg)
    free_fvector(Xg);
  if (Wg)
    free_fvector(Wg);
  if (Y)
    free_complexmatrix(Y, 0, Nnn, -Nnn, Nnn);
  if (A)
    free_complexmatrix(A, 0, Nnn, -Nnn, Nnn);

  return;
}
