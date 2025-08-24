/******************************************************
 *
 * Program genmic.c to generate three-dimensional cement
 * and gypsum particles in a 3-D box with periodic boundaries,
 * and optionally to distribute clinker phases within the
 * generic cement particles
 *
 * Particles are composed of either cement clinker or gypsum,
 * follow a user-specified size distribution, and can be
 * either flocculated, random, or dispersed.
 *
 * Programmer:    Jeffrey W. Bullard
 *                Zachry Department of Civil and Environmental Engineering
 *                Department of Materials Science and Engineering
 *                Texas A&M University
 *                3136 TAMU
 *                College Station, TX  77843   USA
 *                (979) 458-6482
 *                E-mail: jwbullard@tamu.edu
 *
 *******************************************************/
#include "include/vcctl.h"
#include <math.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* Global variables for distrib3d return address workaround */
jmp_buf distrib3d_jmpbuf;
int distrib3d_success = 0;

/* #define DEBUG */

#define NNN 10

#define MAXSPH 100000
#define MAXLINES 3000

/***
 *    Number of grid points used in theta and phi directions
 *    to reconstruct particle surface. You can use down to
 *    about 100 for each and still get particles that are decent
 *    looking. The number of lines in the VRML files scale like
 *    NTHETA*NPHI. NOTE: Better to have odd number.
 *
 *    Allow three different levels of resolution, depending on
 *    the value of resval in the main program (0=low, 1=med, 2=high)
 ***/
#define NTHETAPTS 1000

/* maximum number of random tries for sphere placement */
#define MAXTRIES 1500000

/* Error flag for memory violation */
#define MEMERR -1

/***
 *    Note that each particle must have a separate ID
 *    to allow for flocculation
 ***/

#define SPHERES 0
#define REALSHAPE 1
#define MIXEDSHAPE 2

#define TMPAGGID -100

/* max. number of particles allowed in box */
#define NPARTC 1000000

/* Default for burned id must be at least 100 greater than NPARTC */
#define BURNT 34000
#define FCHECK                                                                 \
  BURNT /* Temporary flag for checking                                         \
         floc collisions */

#define MAXBURNING 33900

/* maximum number of different particle sizes for each phase */
#define NUMSIZES 500

/***
 *    Defines for main menu choice
 ***/

#define EXIT 1
#define SPECSIZE EXIT + 1
#define ADDPART SPECSIZE + 1
#define FLOCC ADDPART + 1
#define MEASURE FLOCC + 1
#define ADDAGG MEASURE + 1
#define CONNECTIVITY ADDAGG + 1
#define DISTFROMAGG CONNECTIVITY + 1
#define DISTRIB DISTFROMAGG + 1
#define OUTPUTMIC DISTRIB + 1
#define ONEPIX OUTPUTMIC + 1
#define DISTFA ONEPIX + 1

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

/*** the following are defines used by the distrib3d function */

/* default resolution of correlation function file */

#define DEFAULTCORRRES 1.00

/* string delineating resolution in correlation file */

#define CORRRESSTRING "Resolution:"

/***
 *    If the following define, LIMITFILTER, is zero, the
 *    program will use a filter size that depends on the system
 *    resolution.  Higher resolution causes a larger filter to be
 *    loaded and can increase run time SIGNIFICANTLY.  If LIMITFILTER
 *    is nonzero, then the filter size is set to
 *    FILTERSIZE regardless of resolution.  This can cause the
 *    filter to truncate longer-range correlations, but seems to have
 *    little effect on the results
 ***/

#define LIMITFILTER 1

#define FILTERSIZE 31 /* size of cubic filter template */

#define HISTSIZE 500 /* bins in histograms */

#define MAXCYC 1000 /* maximum sintering cycles to use */

#define MAX2MOVE                                                               \
  200 /* maximum number of sintering                                           \
       pixels that can move                                                    \
       simultaneously */

#define TEMPLATE_RADIUS                                                        \
  3 /* default radius of template sphere for                                   \
    sintering algorithm */

#define MAXNUMPHASES OFFSET /* maximum number of phases possible */

/***
 *    Parameter for comparing the difference
 *    between two floats
 ***/

#define EPS 1.0e-6

/***
 *    Mathematical parameters/definitions
 ***/

#define PI 3.1415926
#define PI2 6.2831852

/***
 *   Number of tasks to complete
 ***/
#define START_TASK 0
#define AGGPLACE_TASK 1
#define PLACEPARTICLE_TASK 2
#define DIST_SILICATES_TASK 3
#define DIST_C3S_TASK 4
#define DIST_ALUMINATES_TASK 5
#define DIST_C3A_TASK 6
#define DIST_C4AF_TASK 6
#define NUMTASKS 7

/***
 *    Data structure for linked list of surface pixels
 *    to be used in adjusting volume of real-shape particles
 ***/

struct Surfpix {
  int x, y, z; /* position of surface pixel in bounding box */
};

/***
 *    Data structure for real shape information
 ***/

struct pshape {
  int shapetype;            /* SPHERE OR REALSHAPE */
  int ntheta, nphi;         /* Max. number of theta angles sampled */
  char pathroot[MAXSTRING]; /* Path to shape set directory */
  char shapeset[MAXSTRING]; /* Directory with shape information */
  float *xg, *wg;
};

/***
 *    Data structure for particles
 ***/

struct particle {
  int partid;                /* index for particle */
  int partphase;             /* phase identifier for this
                                 particle (C3S or GYPSUM, etc) */
  int flocid;                /* id of floc to which particle belongs */
  int numpix;                /* number of pixels in particle */
  int xc, yc, zc;            /* center of bounding box */
  int xd, yd, zd;            /* dimensions of bounding box */
  int *xi, *yi, *zi;         /* list of pixel locations */
  struct particle *nextpart; /* for floc structures */
};

/***
 *    Global variable declarations:
 *
 *        Cement stores the 3-D particle structure
 *        (each particle with its own ID)
 *
 *        Cemreal stores the 3-D microstructure
 ***/

int Verbose;
Int3d Cement, Cemreal, Bbox;

/***
 *    System size (pixels per edge), number of
 *    particles, and size of aggregate
 ***/
int Syspix = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
int Binderpix = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
int BoxXsize = DEFAULTSYSTEMSIZE;
int BoxYsize = DEFAULTSYSTEMSIZE;
int BoxZsize = DEFAULTSYSTEMSIZE;
int Minsyssize = DEFAULTSYSTEMSIZE;
float Maxadjustxsize = 1.25;
int Isizemag = 1;
float Sizemag = 1.0;
int Npart, Aggsize;
int Npartc, Burnt, Maxburning;
int Allocated = 0;
int Shape = 0;

/***
 *  Set the number of distinct shapes to use within a size class
 *  Negative number indicates a new shape for every particle
 ***/

int Shapesperbin = 25;

const int Erase = 0;
const int Draw = 1;

/***
 * Number of one-pixel particles of each phase
 ***/
int Onepixnum[NPHASES];

/***
 *    Volume fraction and surface area fractions for distrib3d
 ***/
float Volf[NPHASES], Surff[NPHASES];

/***
 *    System resolution (micrometers per pixel edge)
 ***/
float Res = DEFAULTRESOLUTION;

/* VCCTL software version used to create input file */
float Version;

/* Random number seed */
int *Seed;

/* Dispersion distance in pixels */
int Dispdist;
int NumberOfFlocs;

/***
 *    Parameters to aid in obtaining correct
 *    sulfate content
 ***/
int N_sulfate = 0, Target_sulfate = 0, N_total = 0, N_target = 0,
    Target_total = 0, Volpart[NUMSIZES];
int N_anhydrite = 0, Target_anhydrite = 0, N_hemi = 0, Target_hemi = 0,
    Target_total_lt15 = 0;

/* Probability of gypsum particle instead of cement */
float Probgyp;

/* Probabilities of anhydrite and hemihydrate */
float Probhem, Probanh;

/* Mixture proportions are global because they are shared by addagg() and
 * create() */
float Vol_frac[NPHASES];
float Dinput[NPHASES][NUMSIZES];
int Size_classes[NPHASES];
float Pdf[NPHASES][NUMSIZES];

/* Pointer to a 1D list of pointers to particle structures */
struct particle **Particle;

/* Structure of shape information.  Allocate one for each solid phase */

struct pshape Phase_shape[NSPHASES];

double Pi;

fcomplex **Y, **A, **AA;
int Ntheta, Nphi;
int Nnn = NNN;

/* Flags for checksphere and checkpart */
static int Check = 1;
static int Place = 2;

/* File root for real shape anm files */
char Pathroot[MAXSTRING], Shapeset[MAXSTRING];
char Filesep;

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
 *    Global variable declarations for distrib3d function:
 ***/

int Tradius;
unsigned short int ***Curvature;
int Volume[MAXNUMPHASES], Surface[MAXNUMPHASES];
static int Nsph, Xsph[MAXSPH], Ysph[MAXSPH], Zsph[MAXSPH];
int *Nsolid, *Nair;
int *Sum;
float ***Normm, ***Rres;

/***
 *    Pointers for filter variables, which will be dynamically
 *    allocated depending on the system resolution
 ***/

int Fsize, Hsize_r, Hsize_s, *R;
float ***Filter, *S, *Xr;
float Corr_res;

float Resmag = 1.0;
int Iresmag = 1;

/***
 *   Whether or not to simulate a fictious wall in the middle (to create an ITZ
 *effect)
 ***/
int Simwall = 0;
int Wallpos = 50;

/***
 *   File pointer for progress file
 ***/
char LogFileName[MAXSTRING];
FILE *Logfile;

/***
 *    Function declarations
 ***/

int getsystemsize(void);
int checksphere(int xin, int yin, int zin, int diam, int wflg, int phasein,
                int phase2);
int genparticles(int numgen, int *numeach, float *sizeeach, int *pheach);
int genonevoxparticles(int numeach, int pheach);
int checkpart(int xin, int yin, int zin, int nxp, int nyp, int nzp, int volume,
              int phasein, int phase2, int wflg);
int image(int *nxp, int *nyp, int *nzp);
int adjustvol(int diff, int nxp, int nyp, int nzp);
void create(void);
void drawfloc(struct particle *partpoint, const int mode);
int checkfloc(struct particle *partpoint, int dx, int dy, int dz);
void addlayer(int nxp, int nyp, int nzp);
void striplayer(int nxp, int nyp, int nzp);
void makefloc(void);
void measure(void);
void measagg(void);
void connect(void);
int distrib3d(void);
int distfa(int fadchoice);
int addonepixels(void);
void addrand(int randid, int nneed, int onepixfloc, int assignpartnum);
void outmic(void);
struct particle *particlevector(int size);
void free_particlevector(struct particle *ps);
void harm(double theta, double phi);
double fac(int j);
struct particle **particlepointervector(int size);
void free_particlepointervector(struct particle **ps);
void freegenmic(void);
void freedistrib3d(void);
char *rfc8601_timespec(struct timespec *tv);

/***
 *    Function declarations for distrib3d function
 ***/

void checkargs(int argc, char *argv[]);
int maketemp(int size);
void phcount(void);
int surfpix(int xin, int yin, int zin);
float rhcalc(int phin);
int countem(int xp, int yp, int zp, int phin);
void sysinit(int ph1, int ph2);
void sysscan(int ph1, int ph2);
int procsol(int nsearch);
int procair(int nsearch);
int movepix(int ntomove, int ph1, int ph2);
void sinter3d(int ph1id, int ph2id, float rhtarget);
void stat3d(void);
int rand3d(int phasein, int phaseout, char filecorr[MAXSTRING], int nskip,
           float xpt, int *r, float ***filter, float *s, float *xr);
void allmem(void);

int main(int argc, char *argv[]) {
  register int i, j;
  int userc; /* User choice from menu */
  int fadchoice;
  int nseed;
  char instring[MAXSTRING];
  char *rfc8601;
  struct tm *local_time;
  time_t current_time;
  clock_t begin, end;
  double time_spent = 0.0;
  int ig, jg, kg;

  /* Get the simulation start time */

  begin = clock();
  current_time = time(NULL);

  A = NULL;
  AA = NULL;
  Y = NULL;
  Particle = NULL;

  Pi = 4.0 * atan(1.0);

  /* Initialize all volume fractions and size classes */

  for (i = 0; i < NPHASES; i++) {
    Vol_frac[i] = 0.0;
    Size_classes[i] = 0;
    for (j = 0; j < NUMSIZES; j++) {
      Dinput[i][j] = 0.0;
      Pdf[i][j] = 0.0;
    }
  }

  /* Check command-line arguments */
  checkargs(argc, argv);

  /* Create log file and keep it open throughout */
  sprintf(LogFileName, "genmic.log");
  if ((Logfile = fopen(LogFileName, "w")) == NULL) {
    fprintf(stderr, "\nERROR line 490:  Could not open %s\n\n", LogFileName);
    fflush(stderr);
    exit(1);
  }

  local_time = localtime(&current_time);

  /* Display the local time in the log */
  fprintf(Logfile, "=== BEGIN GENMIC SIMULATION ===");
  fprintf(Logfile, "\nStart time: %s", asctime(local_time));
  fflush(Logfile);

  fprintf(Logfile, "\nEnter random number seed value (a negative integer)");
  fflush(Logfile);
  read_string(instring, sizeof(instring));
  nseed = atoi(instring);
  if (nseed > 0)
    nseed = (-1 * nseed);
  fprintf(Logfile, "%d", nseed);
  fflush(Logfile);
  Seed = (&nseed);

  /* Initialize counters and system parameters */

  Npart = 0;
  Aggsize = 0;
  NumberOfFlocs = 0;

  /***
   *    Present menu and execute user choice
   ***/

  do {
    fprintf(Logfile, "\nInput User Choice");
    fprintf(Logfile, "\n  %d) Exit", EXIT);
    fprintf(Logfile, "\n  %d) Specify system size", SPECSIZE);
    fprintf(Logfile, "\n  %d) Add particles (cement,gypsum, ", ADDPART);
    fprintf(Logfile, "pozzolans, etc.) to microstructure");
    fprintf(Logfile, "\n  %d) Flocculate system by reducing number ", FLOCC);
    fprintf(Logfile, "of particle clusters");
    fprintf(Logfile, "\n  %d) Measure global phase fractions", MEASURE);
    fprintf(Logfile, "\n  %d) Add an aggregate to the microstructure", ADDAGG);
    fprintf(Logfile, "\n  %d) Measure single phase connectivity ",
            CONNECTIVITY);
    fprintf(Logfile, "(pores or solids)");
    fprintf(Logfile, "\n  %d) Measure phase fractions vs. ", DISTFROMAGG);
    fprintf(Logfile, "distance from aggregate surface");
    fprintf(Logfile, "\n  %d) Distribute clinker phases", DISTRIB);
    fprintf(Logfile, "\n  %d) Output current microstructure to file",
            OUTPUTMIC);
    fprintf(Logfile, "\n %d) Add one-pixel particles to microstructure",
            ONEPIX);
    fprintf(Logfile, "\n %d) Distribute Fly Ash Phases", DISTFA);
    fflush(Logfile);

    read_string(instring, sizeof(instring));
    userc = atoi(instring);
    fprintf(Logfile, "\n%d", userc);
    fflush(Logfile);

    switch (userc) {
    case SPECSIZE:
      if (getsystemsize() == MEMERR) {
        freegenmic();
        bailout("genmic", "Memory allocation error");
        exit(1);
      }

      /* Clear the 3-D system to all porosity to start */

      for (ig = 0; ig < Xsyssize; ig++) {
        for (jg = 0; jg < Ysyssize; jg++) {
          for (kg = 0; kg < Zsyssize; kg++) {
            Cement.val[getInt3dindex(Cement, ig, jg, kg)] = POROSITY;
            Cemreal.val[getInt3dindex(Cemreal, ig, jg, kg)] = POROSITY;
          }
        }
      }

      fprintf(stdout, "GENMIC_PROGRESS: stage=initialization progress=0.05 "
                      "message=System size configured");
      fflush(stdout);
      break;
    case ADDPART:
      create();
      break;
    case FLOCC:
      if (Shape) {
        fprintf(Logfile, "\nFloccing real shapes...\n");
      } else {
        fprintf(Logfile, "\nFloccing spheres...\n");
      }
      fflush(Logfile);
      makefloc();
      break;
    case MEASURE:
      measure();
      break;
    case ADDAGG:
      Simwall = 1;
      Wallpos = (int)(Xsyssize / 2);
      for (kg = 0; kg < Zsyssize; kg++) {
        for (jg = 0; jg < Ysyssize; jg++) {
          Cement.val[getInt3dindex(Cement, Wallpos, jg, kg)] = TMPAGGID;
          Cemreal.val[getInt3dindex(Cemreal, Wallpos, jg, kg)] = INERTAGG;
          Cement.val[getInt3dindex(Cement, Wallpos - 1, jg, kg)] = TMPAGGID;
          Cemreal.val[getInt3dindex(Cemreal, Wallpos - 1, jg, kg)] = INERTAGG;
          if (Xsyssize % 2 != 0) {
            Cement.val[getInt3dindex(Cement, Wallpos + 1, jg, kg)] = TMPAGGID;
            Cemreal.val[getInt3dindex(Cemreal, Wallpos + 1, jg, kg)] = INERTAGG;
          }
        }
      }
      Binderpix = (Xsyssize - 1) * Ysyssize * Zsyssize;
      break;
    case CONNECTIVITY:
      connect();
      break;
    case DISTFROMAGG:
      if (Aggsize != 0) {
        measagg();
      } else {
        fprintf(Logfile, "No aggregate present. \n");
      }
      break;
    case DISTRIB:
      /* Set up longjmp target for distrib3d return address workaround */
      fprintf(stdout, "\nGENMIC_PROGRESS: stage=correlation_analysis "
                      "progress=0.65 message=Distributing phases");
      fflush(stdout);
      distrib3d_success = 0;
      if (setjmp(distrib3d_jmpbuf) == 0) {
        /* First time - call distrib3d normally */
        if (distrib3d()) {
          fprintf(Logfile, "\nFailure in function distrib3d.  Exiting.\n\n");
          freegenmic();
          exit(1);
        }
        /* Normal return path (should not reach here due to return address
         * corruption) */
        fprintf(Logfile,
                "\n=== DEBUG: Reached normal return path (unexpected) ===");
        fflush(Logfile);
      } else {
        /* longjmp target - distrib3d used longjmp to return */
        fprintf(Logfile, "\n=== DEBUG: Returned via longjmp, success = %d ===",
                distrib3d_success);
        fflush(Logfile);
        if (!distrib3d_success) {
          fprintf(
              Logfile,
              "\nFailure in function distrib3d (via longjmp).  Exiting.\n\n");
          freegenmic();
          exit(1);
        }
      }
      /* distrib3d() already called freedistrib3d() internally before longjmp */
      fprintf(
          Logfile,
          "\n=== DEBUG: DISTRIB case completed, continuing to next menu ===");
      fflush(Logfile);
      /* Check to see that the correct number of C3S pixels is there */
      break;
    case DISTFA:
      fprintf(
          Logfile,
          "\nDistribute fly ash on particle basis (0) or pixel basis (1)?  ");
      read_string(instring, sizeof(instring));
      fadchoice = atoi(instring);
      fprintf(Logfile, "%d\n", fadchoice);
      if (distfa(fadchoice)) {
        fprintf(Logfile, "\nFailure in function distfa.  Exiting.\n\n");
        freedistrib3d();
        freegenmic();
        exit(1);
      }
      /* Check to see that the correct number of C3S pixels is there */
      break;
    case OUTPUTMIC:
      fprintf(stdout, "\nGENMIC_PROGRESS: stage=output_generation "
                      "progress=0.85 message=Writing output files");
      fflush(stdout);
      outmic();
      break;
    case ONEPIX:
      if (addonepixels()) {
        fprintf(Logfile,
                "\nFailure in adding one-pixel particles.  Exiting.\n\n");
        freedistrib3d();
        freegenmic();
        exit(1);
      }
      break;
    default:
      break;
    }

  } while (userc != EXIT);

  /* Write finish time to the log file */
  /* Get the local time using the current time */
  end = clock();
  current_time = time(NULL);
  time_spent = (double)(end - begin) / CLOCKS_PER_SEC;
  local_time = localtime(&current_time);

  /* Display the local time */
  fprintf(Logfile, "\nEnd time: %s", asctime(local_time));
  fprintf(Logfile, "\nElapsed time: %.3f", time_spent);
  fprintf(Logfile, "\n\n=== END GENMIC SIMULATION ===");
  fflush(Logfile);
  fclose(Logfile);

  fprintf(stdout, "\nGENMIC_PROGRESS: stage=complete progress=1.00 "
                  "message=Generation complete");
  fflush(stdout);
  freegenmic();
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
  Res = 0.0;

  fprintf(Logfile, "Enter X dimension of system \n");
  read_string(instring, sizeof(instring));
  Xsyssize = atoi(instring);
  BoxXsize = (int)(0.75 * Xsyssize);
  fprintf(Logfile, "%d\n", Xsyssize);
  fprintf(Logfile, "Enter Y dimension of system \n");
  read_string(instring, sizeof(instring));
  Ysyssize = atoi(instring);
  BoxYsize = (int)(0.75 * Ysyssize);
  fprintf(Logfile, "%d\n", Ysyssize);
  fprintf(Logfile, "Enter Z dimension of system \n");
  read_string(instring, sizeof(instring));
  Zsyssize = atoi(instring);
  BoxZsize = (int)(0.75 * Zsyssize);
  fprintf(Logfile, "%d\n", Zsyssize);

  if ((Xsyssize <= 0) || (Xsyssize > MAXSIZE) || (Ysyssize <= 0) ||
      (Ysyssize > MAXSIZE) || (Zsyssize <= 0) || (Zsyssize > MAXSIZE)) {

    bailout("genmic", "Bad system size specification");
    exit(1);
  }

  fprintf(Logfile, "Enter system resolution (micrometers per pixel) \n");
  read_string(instring, sizeof(instring));
  Res = atof(instring);
  fprintf(Logfile, "%4.2f\n", Res);
  if ((Res < HIGHRES - TINY) && (Res > LOWRES + TINY)) {
    bailout("genmic", "Bad value for system resolution");
    exit(1);
  }

  Npartc = NPARTC;
  Burnt = BURNT;
  Maxburning = MAXBURNING;

  /***
   *    Now dynamically allocate the memory for the Particle
   *    structure array, as well as the Cement and Cemreal
   *    arrays
   ***/

  Syspix = Xsyssize * Ysyssize * Zsyssize;
  Binderpix = Syspix;
  Sizemag = ((float)Syspix) / (pow(((double)DEFAULTSYSTEMSIZE), 3.0));
  Isizemag = (int)(Sizemag + 0.5);
  if (Isizemag > 1) {
    Npartc = NPARTC * Isizemag;
    Burnt = BURNT * Isizemag;
    Maxburning = MAXBURNING * Isizemag;
  }

  Particle = NULL;

  /* Allocate memory for Cement and Cemreal arrays */

  if (Int3darray(&Cement, Xsyssize, Ysyssize, Zsyssize)) {
    return (MEMERR);
  }
  if (Int3darray(&Cemreal, Xsyssize, Ysyssize, Zsyssize)) {
    return (MEMERR);
  }

  Particle = particlepointervector(Npartc);
  if (!Particle) {
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
 *         int diam is the diameter of the sphere to add
 *        int wflg (1=check for fit of sphere, 2=place the sphere)
 *        int phasein is phase to assign to cement image
 *        int phase2 phase to assign to cemreal image
 *
 *     Returns:    integer flag telling whether sphere will fit
 *
 *    Calls:        checkbc
 *    Called by:    genparticles
 ***/
int checksphere(int xin, int yin, int zin, int diam, int wflg, int phasein,
                int phase2) {
  float offset;
  int pnum, nofits, xp, yp, zp, i, j, k, irad, numpix;
  float dist, xdist, ydist, zdist, ftmp;

  if ((Simwall) && (wflg == Check) && (xin == Wallpos)) {
    if (Verbose) {
      fprintf(Logfile, "\nCannot place a particle with center at %d\n",
              Wallpos);
    }
    return (1);
  }

  pnum = Npart;

  nofits = 0; /* Flag indicating if placement is possible */
  if ((diam % 2) == 0) {
    offset = -0.5;
    irad = diam / 2;
  } else {
    offset = 0.0;
    irad = (diam - 1) / 2;
  }

  /***
   *    Check all pixels within the digitized sphere volume
   ***/

  numpix = 0;
  for (i = xin - irad; ((i <= xin + irad) && (!nofits)); i++) {
    xp = i;

    /***
     *    Adjust for periodic BCs if necessary
     ***/

    /* Quick check that particle does not straddle fictitious wall if one is
     * wanted */
    if ((Simwall) && (wflg == Check) && ((xin - Wallpos) * (xp - Wallpos) < 0))
      nofits = 1;

    xp += checkbc(xp, Xsyssize);

    ftmp = (float)(i - xin - offset);
    xdist = ftmp * ftmp;

    for (j = yin - irad; ((j <= yin + irad) && (!nofits)); j++) {
      yp = j;

      /***
       *    Adjust for periodic BCs if necessary
       ***/

      yp += checkbc(yp, Ysyssize);

      ftmp = (float)(j - yin - offset);
      ydist = ftmp * ftmp;
      for (k = zin - irad; ((k <= zin + irad) && (!nofits)); k++) {
        zp = k;

        /***
         *    Adjust for periodic BCs if necessary
         ***/

        zp += checkbc(zp, Zsyssize);

        ftmp = (float)(k - zin - offset);
        zdist = ftmp * ftmp;

        /***
         *    Compute distance from center of
         *    sphere to this pixel
         ***/

        dist = sqrt(xdist + ydist + zdist);
        if ((dist - 0.5) <= ((float)irad)) {

          if (wflg == Place) {
            /* Perform placement ... */
            Cement.val[getInt3dindex(Cement, xp, yp, zp)] = phasein;
            Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] = phase2;
            Particle[pnum]->xi[numpix] = xp;
            Particle[pnum]->yi[numpix] = yp;
            Particle[pnum]->zi[numpix] = zp;
            numpix++;
          } else if ((wflg == Check) &&
                     (Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] !=
                      POROSITY)) {
            /* or check placement */
            nofits = 1;
          }
        }

        /* Check for overlap with aggregate */
        /*
        agglo = ((Xsyssize/2) - ((Aggsize - 2)/2)) - 1;
        agghi = ((Xsyssize/2) + (Aggsize/2)) - 1;
        if ((wflg == Check) && (xp >= agglo && xp <= agghi)) {

            nofits = 1;
        }
        */
      }
    }
  }

  /* return flag indicating if sphere will fit */

  return (nofits);
}
/***
 *    checkpart
 *
 *    routine to check or perform placement of real-shaped particle
 *    of ID phasein, centered at location (xin,yin,zin) of volume vol
 *
 *     Arguments:
 *         int xin,yin,zin is the lower left front corner of the bounding box
 *         int nxp,nyp,nzp is the x, y, and z dimensions of the bounding box
 *         int vol is the number of pixels
 *        int phasein is phase to assign to cement image
 *        int phase2 phase to assign to cemreal image
 *        int wflg (1=check for fit, 2=place the particle)
 *
 *     Returns:    integer flag telling whether sphere will fit
 *
 *    Calls:        checkbc
 *    Called by:    genparticles
 ***/
int checkpart(int xin, int yin, int zin, int nxp, int nyp, int nzp, int vol,
              int phasein, int phase2, int wflg) {
  int pnum, numpix, nofits, i, j, k;
  int i1, i2, j1, k1, xc, yc, zc, found;
  int xmark;

  pnum = Npart;

  nofits = 0; /* Flag indicating if placement is possible */

  if (Verbose) {
    fprintf(Logfile, "\nIn Checkpart, Vol = %d, wflg = %d, phase = %d", vol,
            wflg, phase2);
    fflush(Logfile);
  }

  if ((Simwall) && (wflg == Check) && (xin == Wallpos)) {
    fprintf(Logfile, "\nCannot place a particle with center at %d\n", Wallpos);
    fflush(Logfile);
    return (1);
  }

  /* (xc,yc,zc) is the center of volume of the bounding box */

  xc = (0.50 * nxp) + 0.01;
  yc = (0.50 * nyp) + 0.01;
  zc = (0.50 * nzp) + 0.01;

  xmark = (int)(xc);

  if (wflg == Check) {
    if (Simwall) {
      /* Mark x position of a solid pixel somewhere in particle against which to
         check all others for straddling a fictitious wall if one is wanted */
      k = (int)(zc); /* Searching near center should help find a solid pixel
                        faster */
      j = (int)(yc);
      i = (int)(xc);
      found = 0;
      for (i = (int)(xc); (i <= nxp && !found); i++) {
        for (j = (int)(yc); (j <= nyp && !found); j++) {
          for (k = (int)(zc); (k <= nzp && !found); k++) {
            if (Bbox.val[getInt3dindex(Bbox, i, j, k)] != POROSITY) {
              xmark = xin + i;
              xmark += checkbc(xmark, Xsyssize);
              found = 1;
            }
          }
        }
      }
    }

    k = j = i = 1;
    nofits = 0;
    while (k <= nzp && !nofits) {
      k1 = zin + k;
      k1 += checkbc(k1, Zsyssize);
      j = 1;
      while (j <= nyp && !nofits) {
        j1 = yin + j;
        j1 += checkbc(j1, Ysyssize);
        i = 1;
        while (i <= nxp && !nofits) {
          i1 = xin + i;
          i2 = i1;
          i1 += checkbc(i1, Xsyssize);
          if (Bbox.val[getInt3dindex(Bbox, i, j, k)] != POROSITY) {
            if (Cemreal.val[getInt3dindex(Cemreal, i1, j1, k1)] != POROSITY) {
              nofits = 1;
            } else if ((Simwall) && ((i2 - Wallpos) * (xmark - Wallpos) < 0)) {
              nofits = 1;
            }
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
    numpix = 0;
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
          if (Bbox.val[getInt3dindex(Bbox, i, j, k)] != POROSITY &&
              Bbox.val[getInt3dindex(Bbox, i, j, k)] < FCHECK) {
            Cemreal.val[getInt3dindex(Cemreal, i1, j1, k1)] = phase2;
            Cement.val[getInt3dindex(Cement, i1, j1, k1)] = phasein;
            Particle[pnum]->xi[numpix] = i1;
            Particle[pnum]->yi[numpix] = j1;
            Particle[pnum]->zi[numpix] = k1;
            numpix++;
          }
          i++;
        }
        j++;
      }
      k++;
    }

    return (numpix);
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

  if (Verbose)
    fprintf(
        Logfile,
        "\nEntering first image loop: nxp = %d, nyp= %d, nzp = %d, Nnn = %d",
        *nxp, *nyp, *nzp, Nnn);

  for (k = 1; k <= *nzp; k++) {
    for (j = 1; j <= *nyp; j++) {
      for (i = 1; i <= *nxp; i++) {
        Bbox.val[getInt3dindex(Bbox, i, j, k)] = POROSITY;
      }
    }
  }

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
          Bbox.val[getInt3dindex(Bbox, i, j, k)] = C3S;
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
          Bbox.val[getInt3dindex(Bbox, i, j, k)] = C3S;
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
  int i, j, k;

  min = Dispdist + 1;

  /***
   *    Initialize Bbox array to porosity.  We initialize out to a cube
   *    having edge length equal to the maximum edge length of the
   *    bounding box, because later we may do a rigid body rotation,
   *    reflection, or inversion of the entire contents in place.
   ***/

  for (k = 1; k < maxdim; k++) {
    for (j = 1; j < maxdim; j++) {
      for (i = 1; i < maxdim; i++) {
        Bbox.val[getInt3dindex(Bbox, i, j, k)] = POROSITY;
      }
    }
  }

  /***
   *    When assigning solid pixels within Bbox, just arbitrarily
   *    assign them to be of type C3S.  Later, when the image is
   *    actually placed (in function checkpart),
   *    the correct phase is used
   ***/

  *nxp = 6;
  *nyp = 6;
  *nzp = 6;

  if (vol == 4) {
    orient = 1 + (int)(3.0 * ran1(Seed));
    switch (orient) {
    case 1:
      Bbox.val[getInt3dindex(Bbox, min, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min + 1, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min + 1, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min + 1, min + 1, min)] = C3S;
      *nzp = 5;
      break;
    case 2:
      Bbox.val[getInt3dindex(Bbox, min, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min, min + 1)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min + 1, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min + 1, min + 1)] = C3S;
      *nxp = 5;
      break;
    case 3:
      Bbox.val[getInt3dindex(Bbox, min, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min + 1, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min, min + 1)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min + 1, min, min + 1)] = C3S;
      *nyp = 5;
      break;
    default:
      Bbox.val[getInt3dindex(Bbox, min, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min + 1, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min + 1, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min + 1, min + 1, min)] = C3S;
      *nzp = 5;
      break;
    }
    return (4);
  } else if (vol == 3) {
    orient = 1 + (int)(3.0 * ran1(Seed));
    switch (orient) {
    case 1:
      Bbox.val[getInt3dindex(Bbox, min, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min + 1, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min + 1, min)] = C3S;
      *nzp = 5;
      break;
    case 2:
      Bbox.val[getInt3dindex(Bbox, min, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min, min + 1)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min + 1, min)] = C3S;
      *nxp = 5;
      break;
    case 3:
      Bbox.val[getInt3dindex(Bbox, min, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min, min + 1)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min + 1, min, min)] = C3S;
      *nyp = 5;
      break;
    default:
      Bbox.val[getInt3dindex(Bbox, min, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min + 1, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min + 1, min)] = C3S;
      *nzp = 5;
      break;
    }
    return (3);
  } else {
    orient = 1 + (int)(3.0 * ran1(Seed));
    switch (orient) {
    case 1:
      Bbox.val[getInt3dindex(Bbox, min, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min + 1, min, min)] = C3S;
      *nyp = 5;
      *nzp = 5;
      break;
    case 2:
      Bbox.val[getInt3dindex(Bbox, min, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min + 1, min)] = C3S;
      *nxp = 5;
      *nzp = 5;
      break;
    case 3:
      Bbox.val[getInt3dindex(Bbox, min, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min, min, min + 1)] = C3S;
      *nxp = 5;
      *nyp = 5;
      break;
    default:
      Bbox.val[getInt3dindex(Bbox, min, min, min)] = C3S;
      Bbox.val[getInt3dindex(Bbox, min + 1, min, min)] = C3S;
      *nyp = 5;
      *nzp = 5;
      break;
    }
    return (2);
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
  static struct Surfpix sp[MAXSPH];

  absdiff = abs(diff);

  /* Populate list of surface pixels */

  numsp = 0;
  if (diff > 0) {
    /* add solid pixels to surface */
    for (i = 2; i < nxp - 1; i++) {
      for (j = 2; j < nyp - 1; j++) {
        for (k = 2; k < nzp - 1; k++) {
          if (Bbox.val[getInt3dindex(Bbox, i, j, k)] == POROSITY &&
              ((Bbox.val[getInt3dindex(Bbox, i + 1, j, k)] == C3S) ||
               (Bbox.val[getInt3dindex(Bbox, i - 1, j, k)] == C3S) ||
               (Bbox.val[getInt3dindex(Bbox, i, j + 1, k)] == C3S) ||
               (Bbox.val[getInt3dindex(Bbox, i, j - 1, k)] == C3S) ||
               (Bbox.val[getInt3dindex(Bbox, i, j, k + 1)] == C3S) ||
               (Bbox.val[getInt3dindex(Bbox, i, j, k - 1)] == C3S))) {
            /* add i,j,k to surface pixels */
            sp[numsp].x = i;
            sp[numsp].y = j;
            sp[numsp].z = k;
            numsp++;
#ifdef DEBUG
            if (numsp == 9999) {
              fprintf(Logfile, "\nThis is why... numsp = 9999");
              fflush(Logfile);
            }
#endif
          }
        }
      }
    }
  } else {
    /* remove solid pixels from surface */
    for (i = 1; i <= nxp - 1; i++) {
      for (j = 1; j <= nyp - 1; j++) {
        for (k = 1; k <= nzp - 1; k++) {
          if (Bbox.val[getInt3dindex(Bbox, i, j, k)] == C3S &&
              ((Bbox.val[getInt3dindex(Bbox, i + 1, j, k)] == POROSITY) ||
               (Bbox.val[getInt3dindex(Bbox, i - 1, j, k)] == POROSITY) ||
               (Bbox.val[getInt3dindex(Bbox, i, j + 1, k)] == POROSITY) ||
               (Bbox.val[getInt3dindex(Bbox, i, j - 1, k)] == POROSITY) ||
               (Bbox.val[getInt3dindex(Bbox, i, j, k + 1)] == POROSITY) ||
               (Bbox.val[getInt3dindex(Bbox, i, j, k - 1)] == POROSITY))) {
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
  fprintf(Logfile, "\nIn adjustvol, diff = %d and num surf pix = %d", diff,
          numsp);
  fflush(Logfile);
#endif

  count = 0;
  for (n = 1; n <= absdiff; n++) {

    /***
     *    randomly select a surface pixel from the list
     ***/

    choice = (int)(numsp * ran1(Seed));
#ifdef DEBUG
    fprintf(Logfile, "\n\tIn adjustvol random choice = %d", choice);
    fflush(Logfile);
#endif

    if (choice > numsp)
      break;
    if (Bbox.val[getInt3dindex(Bbox, sp[choice].x, sp[choice].y,
                               sp[choice].z)] == C3S) {
      Bbox.val[getInt3dindex(Bbox, sp[choice].x, sp[choice].y, sp[choice].z)] =
          POROSITY;
      count--;
    } else {
      Bbox.val[getInt3dindex(Bbox, sp[choice].x, sp[choice].y, sp[choice].z)] =
          C3S;
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
    fprintf(Logfile, "\n\t\tcount = %d and numsp = %d", count, numsp);
    fflush(Logfile);
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
        if (Bbox.val[getInt3dindex(Bbox, i, j, k)] == C3S) {
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j, k)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i + 1, j, k)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i - 1, j, k)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i - 1, j, k)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i, j + 1, k)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i, j + 1, k)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i, j - 1, k)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i, j - 1, k)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i, j, k + 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i, j, k + 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i, j, k - 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i, j, k - 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i - 1, j + 1, k)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i - 1, j + 1, k)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i - 1, j - 1, k)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i - 1, j - 1, k)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j, k + 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i + 1, j, k + 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j, k - 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i + 1, j, k - 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i - 1, j, k + 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i - 1, j, k + 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i - 1, j, k - 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i - 1, j, k - 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i, j + 1, k + 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i, j + 1, k + 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i, j + 1, k - 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i, j + 1, k - 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i, j - 1, k + 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i, j - 1, k + 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i, j - 1, k - 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i, j - 1, k - 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k + 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k + 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k - 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k - 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k + 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k + 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k - 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k - 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k + 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i - 1, j + 1, k + 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k - 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i - 1, j + 1, k - 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k + 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i - 1, j - 1, k + 1)] = FCHECK;
          if (Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k - 1)] == POROSITY)
            Bbox.val[getInt3dindex(Bbox, i - 1, j - 1, k - 1)] = FCHECK;
        }
      }
    }
  }

  if (Dispdist == 2) {
    for (k = 1; k < nzp; k++) {
      for (j = 1; j < nyp; j++) {
        for (i = 1; i < nxp; i++) {
          if (Bbox.val[getInt3dindex(Bbox, i, j, k)] == FCHECK) {
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j, k)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i + 1, j, k)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i - 1, j, k)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i - 1, j, k)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i, j + 1, k)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i, j + 1, k)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i, j - 1, k)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i, j - 1, k)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i, j, k + 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i, j, k + 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i, j, k - 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i, j, k - 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i - 1, j + 1, k)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i - 1, j + 1, k)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i - 1, j - 1, k)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i - 1, j - 1, k)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j, k + 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i + 1, j, k + 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j, k - 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i + 1, j, k - 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i - 1, j, k + 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i - 1, j, k + 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i - 1, j, k - 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i - 1, j, k - 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i, j + 1, k + 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i, j + 1, k + 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i, j + 1, k - 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i, j + 1, k - 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i, j - 1, k + 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i, j - 1, k + 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i, j - 1, k - 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i, j - 1, k - 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k + 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k + 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k - 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k - 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k + 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k + 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k - 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k - 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k + 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i - 1, j + 1, k + 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j + 1, k - 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i - 1, j + 1, k - 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k + 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i - 1, j - 1, k + 1)] = FCHECK + 1;
            if (Bbox.val[getInt3dindex(Bbox, i + 1, j - 1, k - 1)] == POROSITY)
              Bbox.val[getInt3dindex(Bbox, i - 1, j - 1, k - 1)] = FCHECK + 1;
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
        if (Bbox.val[getInt3dindex(Bbox, i, j, k)] > FCHECK)
          Bbox.val[getInt3dindex(Bbox, i, j, k)] = POROSITY;
      }
    }
  }

  return;
}

/***
 *    genparticles
 *
 *    Routine to place particles of various sizes and phases at random
 *    locations in 3-D microstructure.
 *
 *     Arguments:
 *        int numgen is number of different size spheres to place
 *        int numeach holds the number of each size class
 *        float sizeeach holds the radius of each size class
 *        int pheach holds the phase of each size class
 *        int shape is 0 if sphere or 1 if real shapes
 *    Returns:
 *        Number of particles placed of last kind tried
 *
 *    Calls:        makesph, ran1
 *    Called by:    create
 ***/
int genparticles(int numgen, int *numeach, float *sizeeach, int *pheach) {
  int m, n, i, j, k, ii, jj, x, y, z, ig, tries, na, foundpart;
  int phnow, nofit, n1, nxp, nyp, nzp, nnxp, nnyp, nnzp, partc, extpix,
      pcount[10];
  int numpershape, nump, done, total_particles_to_place, numchunk;
  int klow, khigh, mp, pixfrac, numlines, numitems, toobig;
  int absdiff, oldabsdiff, diam, darg, numpix, shapetype, dispdist;
  int cx, cy, cz;
  int jg, numpartplaced, vol;
  float rx, ry, rz, testgyp, typegyp, frad, aa1, aa2;
  float vol1, ratio[10], saveratio, volume, volumecalc, v1;
  float fraction_progress = 0.10;
  float maxrx, maxry, maxrz;
  /* float length,width; */
  double factor, theta, phi, cosbeta, sinbeta, alpha, gamma, beta, total, abc;
  double realnum;
  fcomplex r1, ddd, icmplx;
  char buff[MAXSTRING], filename[MAXSTRING], scratchname[MAXSTRING];
  char *name, *newstring;
  struct lineitem line[MAXLINES];
  FILE *anmfile, *geomfile, *fscratch;

  /* Determine how many total particles should be placed */
  total_particles_to_place = 0;
  for (ig = 0; ig < numgen; ig++) {
    total_particles_to_place += numeach[ig];
  }

  /* Divide the total number to place into five chunks */
  numchunk = total_particles_to_place / 100;

  /* Print progress message */
  fprintf(stdout,
          "\nGENMIC_PROGRESS: stage=particle_placement progress=%.2f "
          "message=Placing particles",
          fraction_progress);
  fflush(stdout);

  nnxp = nnyp = nnzp = n1 = 0;
  x = y = z = 0;
  partc = nump = 0;
  saveratio = 0.0;

  sprintf(scratchname, "scratchaggfile.dat");
  fscratch = filehandler("genmic", scratchname, "WRITE");
  if (!fscratch) {
    freegenmic();
    bailout("genmic", "Could not open aggregate structure file");
  }
  fprintf(fscratch, "%d %d %d\n", Xsyssize, Ysyssize, Zsyssize);

  for (ig = 0; ig < numgen; ig++) {

    dispdist = Dispdist;
    phnow = pheach[ig]; /* phase for this class */
    fprintf(Logfile, "Going to place %d particles of phase %d, radius %f\n",
            numeach[ig], phnow, sizeeach[ig]);

    if (Phase_shape[phnow].shapetype == SPHERES || sizeeach[ig] < 1.0) {
      shapetype = SPHERES;
    } else {
      shapetype = REALSHAPE;
    }

    switch (shapetype) {

    case SPHERES:

      frad = sizeeach[ig];              /* float radius for this class */
      diam = (int)((2.0 * frad) + 0.5); /* nearest integer diameter */
      numpix = diam2vol((float)diam);

      /* loop for each sphere in this size class */

      for (jg = 0; jg < numeach[ig]; jg++) {

        tries = 0;
        if (((numpartplaced + 1) % numchunk) == 0) {
          fraction_progress =
              0.1 + (0.55 * ((float)(numpartplaced) /
                             (float)(total_particles_to_place)));
          fprintf(stdout,
                  "\nGENMIC_PROGRESS: stage=particle_placement progress=%.2f "
                  "message=Placing particles",
                  fraction_progress);
          fflush(stdout);
        }

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

          darg = diam + (2 * dispdist);
          nofit = checksphere(x, y, z, darg, Check, Npart + 1, 0);
          if ((tries > MAXTRIES) && (dispdist > 0)) {
            fprintf(Logfile, "\nAble to place %d particles ", jg);
            fprintf(Logfile,
                    "out of %d needed before reducing dispersion distance ",
                    numeach[ig]);
            tries = 0;
            dispdist--;
            fprintf(Logfile, "to %d\n", dispdist);
          }

          if (tries > MAXTRIES) {
            fprintf(Logfile, "Could not place sphere %d\n", Npart);
            fprintf(Logfile, "\tafter %d random attempts\n\n", MAXTRIES);
            fprintf(Logfile,
                    "\nTotal number spheres desired in this bin was %d",
                    numeach[ig]);
            fprintf(Logfile, "\nActual number _placed  in this bin was %d", jg);
            fprintf(Logfile, "\nWas working on bin %d out of %d\n", ig, numgen);

            warning("genmic", "Could not place a sphere");
            fflush(Logfile);
            return (jg);
          }
        } while (nofit);

        /* Place the sphere at x,y,z */

        Npart++;
        if (Npart > Npartc) {
          fprintf(Logfile, "Too many spheres being generated \n");
          fprintf(Logfile, "\tUser needs to increase value of NPARTC\n");
          fprintf(Logfile, "\tat top of C-code\n\n");
          fprintf(Logfile, "\nTotal number spheres desired in this bin was %d",
                  numeach[ig]);
          fprintf(Logfile, "\nActual number _placed  in this bin was %d", jg);
          fprintf(Logfile, "\nWas working on bin %d out of %d\n", ig, numgen);
          warning("genmic", "Too many spheres");
          fflush(Logfile);
          return (jg);
        }

        /* Allocate space for new particle info */

        Particle[Npart] = particlevector(numpix);
        if (!Particle[Npart]) {
          freegenmic();
          bailout("genmic", "Memory allocation error");
          fflush(Logfile);
          exit(1);
        }

        Particle[Npart]->partid = Npart;
        Particle[Npart]->flocid = Npart;
        NumberOfFlocs++;

        /* Default to cement placement */

        Particle[Npart]->partphase = C3S;
        Particle[Npart]->xc = x;
        Particle[Npart]->yc = y;
        Particle[Npart]->zc = z;
        Particle[Npart]->xd = (int)((2.0 * frad) + 0.5);
        Particle[Npart]->yd = (int)((2.0 * frad) + 0.5);
        Particle[Npart]->zd = (int)((2.0 * frad) + 0.5);

        if (phnow == C3S) {

          /***
           *    Determine whether to try to place as clinker or sulfate
           ***/

          testgyp = ran1(Seed);

          /***
           *    Do not use dispersion distance
           *    when placing particle
           ***/

          if (((testgyp > Probgyp) &&
               ((Target_sulfate - N_sulfate) < (Target_total - N_total))) ||
              (N_sulfate > Target_sulfate) ||
              (Volpart[ig] > (Target_sulfate - N_sulfate)) ||
              (Volpart[ig] > diam2vol(15.0))) {

            nofit = checksphere(x, y, z, diam, Place, Npart + 1, C3S);
            N_total += Volpart[ig];
          } else {

            /* Place particle as gypsum */

            typegyp = ran1(Seed);
            N_total += Volpart[ig];
            N_sulfate += Volpart[ig];

            if ((fabs(Probanh - 1.0) < TINY) ||
                ((typegyp < Probanh) && (N_anhydrite < Target_anhydrite) &&
                 (Volpart[ig] <= (Target_anhydrite - N_anhydrite)))) {

              N_anhydrite += Volpart[ig];
              nofit = checksphere(x, y, z, diam, Place, Npart + 1, ANHYDRITE);
              Particle[Npart]->partphase = ANHYDRITE;

            } else if ((fabs(Probanh + Probhem - 1.0) < TINY) ||
                       ((typegyp < (Probanh + Probhem)) &&
                        (N_hemi < Target_hemi) &&
                        (Volpart[ig] <= (Target_hemi - N_hemi)))) {

              N_hemi += Volpart[ig];
              nofit = checksphere(x, y, z, diam, Place, Npart + 1, HEMIHYD);
              Particle[Npart]->partphase = HEMIHYD;

            } else {

              nofit = checksphere(x, y, z, diam, Place, Npart + 1, GYPSUM);

              /* Correct phase ID of particle */
              Particle[Npart]->partphase = GYPSUM;
            }
          }

        } else {

          /***
           *    Place as inert, CaCO3, C2S, slag,
           *    or pozzolanic material
           ***/

          nofit = checksphere(x, y, z, diam, Place, Npart + 1, phnow);

          /* Correct phase ID of particle */
          Particle[Npart]->partphase = phnow;
        }

        /*** PUT NICK'S STUFF RIGHT HERE ***/
        fprintf(fscratch, "%d %d %d 0\n", x, y, z);
        fprintf(fscratch, "0 0 %.10f 0.0000000000\n", sizeeach[ig]);
      }

      break;

    case REALSHAPE:

      if (Verbose)
        fprintf(Logfile, "\nPlacing REAL shapes now...");

      sprintf(filename, "%s%s%c%s-geom.csv", Phase_shape[phnow].pathroot,
              Phase_shape[phnow].shapeset, Filesep,
              Phase_shape[phnow].shapeset);

      geomfile = filehandler("genmic", filename, "READ");
      if (!geomfile) {
        freegenmic();
        exit(1);
      }

      /* Scan header and discard */
      fread_string(geomfile, buff);

      if (Verbose)
        fprintf(Logfile, "\nReading each line of the geom file...");
      fflush(Logfile);

      i = done = 0;
      while ((!feof(geomfile)) && (i < MAXLINES) && (done == 0)) {
        fread_string(geomfile, buff);
        name = strtok(buff, ",");
        fprintf(Logfile, "\ni = %d, name = %s", i, name);
        fflush(Logfile);
        strcpy(line[i].name, name);
        newstring = strtok(NULL, ",");
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].xlow = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].xhi = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].ylow = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].yhi = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].zlow = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].zhi = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].volume = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].surfarea = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].nsurfarea = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].diam = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].Itrace = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].Nnn = atoi(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].NGC = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].length = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].width = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].thickness = atof(newstring);
          newstring = strtok(NULL, ",");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].nlength = atof(newstring);
          newstring = strtok(NULL, ",\n");
        } else {
          done = 1;
        }
        if (newstring != NULL) {
          fprintf(Logfile, "\ni = %d, newstring = %s", i, newstring);
          fflush(Logfile);
          line[i].nwidth = atof(newstring);
        } else {
          done = 1;
        }
        i++;

        /* Line scanned in now */
      }

      if (Verbose)
        fprintf(Logfile, " Done!\n");
      fflush(Logfile);

      /* All lines scanned */

      numitems = i - 1;
      numlines = numitems - 1;
      fclose(geomfile);

      frad = sizeeach[ig]; /* radius in pixel edge lengths */
      vol = Volpart[ig];   /* target volume in pixels */

      pixfrac = (int)(0.03 * vol);

      if (phnow == C3S)
        N_target += (numeach[ig] * vol);

      numpershape = max((numeach[ig] / Shapesperbin), 1);

      numpartplaced = 0;

      if (Verbose)
        fprintf(Logfile,
                "Entering main loop for size class %d, need %d of them...", ig,
                numeach[ig]);
      fflush(Logfile);
      for (jg = 0; jg < numeach[ig]; jg++) {

        if (Verbose)
          fprintf(Logfile, "\n\t%d of %d", jg, numeach[ig]);
        fflush(Logfile);

        foundpart = 1;
        toobig = 0;

        do {
          if (vol > 4) {

            if (jg == 0 || (!(jg % numpershape)) || toobig || !foundpart) {

              toobig = 0;
              foundpart = 1;

              if (Verbose) {
                fprintf(Logfile, "\n\tNeed to choose a new shape...");
                fflush(Logfile);
              }

              /***
               *    Generate the shape by selecting randomly
               *    from collection of anm files in the
               *    directory of interest
               ***/

              /***
               *    Choose a line in the geom file at random
               ***/

              n1 = (int)(numlines * ran1(Seed));

              sprintf(filename, "%s%s%c%s", Phase_shape[phnow].pathroot,
                      Phase_shape[phnow].shapeset, Filesep, line[n1].name);
              if (Verbose)
                fprintf(Logfile, " %s", filename);
              fflush(Logfile);

              anmfile = filehandler("genmic", filename, "READ");

              if (Verbose)
                fprintf(Logfile, " !!");
              fflush(Logfile);

              if (!anmfile) {
                freegenmic();
                exit(1);
              }

              if (Verbose)
                fprintf(Logfile, "Opened %s ; size = %d\n", line[n1].name, vol);
              fprintf(Logfile, "Using particle shape %s; size = %d\n",
                      line[n1].name, vol);
              fflush(Logfile);

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
                }
              }

              if (Verbose)
                fprintf(Logfile, "\nRead anms");
              fflush(Logfile);
              fclose(anmfile);

              /***
               *    Compute volume of real particle
               ***/

              factor = 0.5 * Pi * Pi;
              volumecalc = 0.0;

              maxrx = maxry = maxrz = 0.0;
              for (i = 1; i <= Phase_shape[phnow].ntheta; i++) {
                theta = 0.5 * Pi * (Phase_shape[phnow].xg[i] + 1.0);
                for (j = 1; j <= Phase_shape[phnow].nphi; j++) {
                  phi = Pi * (Phase_shape[phnow].xg[j] + 1.0);
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
                  v1 *= (Phase_shape[phnow].wg[i] * Phase_shape[phnow].wg[j]);
                  volumecalc += v1;
                }
              }

              volumecalc *= factor;

              /* width = line[n1].width / Res; */ /* in pixels */
              /* length = line[n1].length / Res; */

              saveratio = pow((1.003 * (double)vol / volumecalc), (1. / 3.));
            }

            /***
             *    Rotate coefficients A[n][m] by a random amount
             *    Store in AA[n][m] matrix.
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

                AA[n][m] = RCmul(saveratio, AA[n][m]);
              }
            }

            /***
             *    Compute volume of real particle
             ***/

            factor = 0.5 * Pi * Pi;
            volume = 0.0;

            maxrx = maxry = maxrz = 0.0;
            for (i = 1; i <= Phase_shape[phnow].ntheta; i++) {
              theta = 0.5 * Pi * (Phase_shape[phnow].xg[i] + 1.0);
              for (j = 1; j <= Phase_shape[phnow].nphi; j++) {
                phi = Pi * (Phase_shape[phnow].xg[j] + 1.0);
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
                v1 *= (Phase_shape[phnow].wg[i] * Phase_shape[phnow].wg[j]);
                volume += v1;
              }
            }

            volume *= factor;
            vol1 = volume;
#ifdef DEBUG
            fprintf(Logfile, "\nComputed volume = %f ", vol1);
            fprintf(Logfile, "Tabulated = %f ", line[n1].volume);
            fprintf(Logfile, "saveratio = %f ", saveratio);
            fprintf(Logfile, "partc = %d", partc);
            fflush(Logfile);
#endif

            na = 0;
            oldabsdiff = vol;
            absdiff = 0;
            pcount[0] = (int)vol1;
            do {
              if (na == 0) {
                ratio[na] = saveratio;
                pcount[na] = (int)vol1;
              } else if (na == 1) {
                pcount[na] = partc;
                ratio[na] = ratio[na - 1] * pow(0.5 * ((float)pcount[na]) /
                                                    ((float)pcount[na - 1]),
                                                (1. / 3.));
                for (n = 0; n <= Nnn; n++) {
                  for (m = n; m >= -n; m--) {
                    AA[n][m] = RCmul(ratio[na] / ratio[na - 1], AA[n][m]);
                  }
                }
                maxrx *= (ratio[na] / ratio[na - 1]);
                maxry *= (ratio[na] / ratio[na - 1]);
                maxrz *= (ratio[na] / ratio[na - 1]);
              } else {
                oldabsdiff = labs(pcount[na - 2] - vol);
                absdiff = labs(pcount[na - 1] - vol);
                if (absdiff <= oldabsdiff) {
                  pcount[na] = partc;
                  ratio[na] = ratio[na - 1] * pow(0.5 * ((float)pcount[na]) /
                                                      ((float)pcount[na - 1]),
                                                  (1. / 3.));
                  for (n = 0; n <= Nnn; n++) {
                    for (m = n; m >= -n; m--) {
                      AA[n][m] = RCmul(ratio[na] / ratio[na - 1], AA[n][m]);
                    }
                  }
                  maxrx *= (ratio[na] / ratio[na - 1]);
                  maxry *= (ratio[na] / ratio[na - 1]);
                  maxrz *= (ratio[na] / ratio[na - 1]);
                } else {
                  ratio[na] = ratio[na - 2];
                  for (n = 0; n <= Nnn; n++) {
                    for (m = n; m >= -n; m--) {
                      AA[n][m] = RCmul(ratio[na] / ratio[na - 1], AA[n][m]);
                    }
                  }
                  maxrx *= (ratio[na] / ratio[na - 1]);
                  maxry *= (ratio[na] / ratio[na - 1]);
                  maxrz *= (ratio[na] / ratio[na - 1]);
                }
              }

#ifdef DEBUG
              fprintf(Logfile, "\nna = %d", na);
              fprintf(Logfile, "\ntarget volume = %d", vol);
              fprintf(Logfile, "\ncomputed volume = %f", vol1);
              fprintf(Logfile, "\nratio = %f", ratio[na]);
              fflush(Logfile);
#endif

              /* Digitize the particles all over again */

              /*  Estimate dimensions of bounding box */

              nxp = 3 + ((int)(2.0 * maxrx));
              nyp = 3 + ((int)(2.0 * maxry));
              nzp = 3 + ((int)(2.0 * maxrz));

              /* Make the box a little bigger if dispersion is required */

              if (dispdist > 0) {
                nxp += dispdist + 1;
                nyp += dispdist + 1;
                nzp += dispdist + 1;
              }

              /* Do the digitization */

              if ((nxp < (int)(0.8 * Xsyssize)) &&
                  (nyp < (int)(0.8 * Ysyssize)) &&
                  (nzp < (int)(0.8 * Zsyssize))) {
                foundpart = 1;
                partc = image(&nxp, &nyp, &nzp);
                if (partc == 0) {
                  if (Verbose)
                    fprintf(Logfile, "\nCurrent particle too big.");
                  toobig = 1;
                  foundpart = 0;
                } else {
                  toobig = 0;
                  foundpart = 1;
                }
              } else {
                toobig = 1;
                foundpart = 0;
              }
#ifdef DEBUG
              fprintf(Logfile, "\nAfter image function, nominal particle ");
              fprintf(Logfile, "size %d, actual %d", vol, partc);
              fflush(Logfile);
#endif
              saveratio = ratio[na];
              na++;
            } while ((labs(partc - vol) > max(4, pixfrac)) && na < 1 &&
                     !toobig);

            if (!toobig && foundpart) {
#ifdef DEBUG
              fprintf(Logfile, "\nDone scaling the anms");
              fflush(Logfile);
#endif

              /***
               *    After scaling, may still be off by one or several
               *    pixels from target volume.  Adjust by simply adding
               *    a pixel here and there to the particle surface
               ***/

              if (partc != vol) {
#ifdef DEBUG
                fprintf(Logfile,
                        "\nAdditional adjustment needed to match volume, partc "
                        "= %d",
                        partc);
                fflush(Logfile);
#endif
                extpix = adjustvol(vol - partc, nxp, nyp, nzp);
                partc += extpix;
#ifdef DEBUG
                fprintf(Logfile, "\nAfter adjustment, partc = %d", partc);
                fflush(Logfile);
#endif
              }

              /***
               *    If dispersion is desired, add false layer around
               *    the particle now (will be stripped when particle
               *    is actually placed)
               ***/

              if (dispdist > 0) {
                addlayer(nxp, nyp, nzp);
              }

              /***
               *    Done generating the shape image for the particle
               ***/

              nnxp = nxp;
              nnyp = nyp;
              nnzp = nzp;

            } else {

#ifdef DEBUG
              fprintf(Logfile, "\nSomething wrong with this particle");
              fflush(Logfile);
#endif
              foundpart = 0;
            }

          } else {
            partc = smallimage(&nxp, &nyp, &nzp, vol);
            if (dispdist > 0) {
              addlayer(nnxp, nnyp, nnzp);
            }
            /* orient = 1 + (int)(14.0 * ran1(Seed)); */
            nnxp = nxp;
            nnyp = nyp;
            nnzp = nzp;
            foundpart = 1;
            toobig = 0;
          }

        } while (!foundpart || toobig);

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

          /*
          x = (int)(0.5*((float)(Xsyssize - nnxp)));
          y = (int)(0.5*((float)(Ysyssize - nnyp)));
          z = (int)(0.5*((float)(Zsyssize - nnzp)));
          */

          /***
           *    See if the particle will fit at x,y,z
           *    Include dispersion distance when checking
           *    to ensure requested separation between spheres
           ***/

#ifdef DEBUG
          fprintf(Logfile, "\nAbout to go into checkpart...");
          fprintf(Logfile, "\n\tx = %d y = %d z = %d", x, y, z);
          fprintf(Logfile, "\n\tnnxp = %d nnyp = %d nnzp = %d", nnxp, nnyp,
                  nnzp);
          fprintf(Logfile, "\n\tvol = %d", vol);
          fflush(Logfile);
#endif

          nofit =
              checkpart(x, y, z, nnxp, nnyp, nnzp, vol, Npart + 1, 0, Check);

          if ((tries > MAXTRIES) && (dispdist > 0)) {
            tries = 0;
            dispdist--;
            striplayer(nnxp, nnyp, nnzp);
          }

          if (tries > MAXTRIES) {
            fprintf(Logfile, "Could not place particle %d\n", Npart);
            fprintf(Logfile, "\tafter %d random attempts\n\n", MAXTRIES);
            fprintf(Logfile,
                    "\nTotal number spheres desired in this bin was %d",
                    numeach[ig]);
            fprintf(Logfile, "\nActual number _placed  in this bin was %d", jg);
            fprintf(Logfile, "\nWas working on bin %d out of %d\n", ig, numgen);
            warning("genmic", "Could not place a particle");
            fflush(Logfile);
            return (jg);
          }

        } while (nofit);

        /***
         *    Place the particle with lower corner of bounding
         *    box at x,y,z
         ***/

        Npart++;
        if (Npart > Npartc) {
          fprintf(Logfile, "Too many particles being generated \n");
          fprintf(Logfile, "\tUser needs to increase value of NPARTC\n");
          fprintf(Logfile, "\tat top of C-code\n\n");
          fprintf(Logfile,
                  "\nNumber real-shape particles desired in this bin was %d",
                  numeach[ig]);
          fprintf(Logfile, "\nActual number _placed  in this bin was %d", jg);
          fprintf(Logfile, "\nWas working on bin %d out of %d\n", ig, numgen);
          warning("genmic", "Too many particles");
          fflush(Logfile);
          return (jg);
        }

        /* Allocate space for new particle info */

        Particle[Npart] = particlevector(vol);
        if (!Particle[Npart]) {
          freegenmic();
          bailout("genmic", "Memory allocation error");
          fflush(Logfile);
          exit(1);
        }
        Particle[Npart]->partid = Npart;
        Particle[Npart]->flocid = Npart;
        NumberOfFlocs++;

        /* Default to cement placement */

        Particle[Npart]->partphase = C3S;
        Particle[Npart]->xd = nnxp;
        Particle[Npart]->yd = nnyp;
        Particle[Npart]->zd = nnzp;
        Particle[Npart]->xc = x + (int)(0.5 * Particle[Npart]->xd + 0.5);
        Particle[Npart]->xc += checkbc(Particle[Npart]->xc, Xsyssize);
        Particle[Npart]->yc = y + (int)(0.5 * Particle[Npart]->yd + 0.5);
        Particle[Npart]->yc += checkbc(Particle[Npart]->yc, Ysyssize);
        Particle[Npart]->zc = z + (int)(0.5 * Particle[Npart]->zd + 0.5);
        Particle[Npart]->zc += checkbc(Particle[Npart]->zc, Zsyssize);

        if (phnow == C3S) {

          /***
           *     Decide whether to try to place as clinker or as
           *     sulfate
           ***/

          testgyp = ran1(Seed);

          /***
           *    Do not use dispersion distance
           *    when placing particle
           ***/

          if (((testgyp > Probgyp) &&
               ((Target_sulfate - N_sulfate) < (Target_total - N_total))) ||
              (N_sulfate > Target_sulfate) ||
              (vol > (Target_sulfate - N_sulfate)) || (vol > diam2vol(15.0))) {

#ifdef DEBUG
            fprintf(Logfile, "\nAbout to place a C3S particle...");
            fprintf(Logfile, "\n\tx = %d y = %d z = %d", x, y, z);
            fprintf(Logfile, "\n\tnnxp = %d nnyp = %d nnzp = %d", nnxp, nnyp,
                    nnzp);
            fprintf(Logfile, "\n\tvol = %d", vol);
            fflush(Logfile);
#endif
            nump = checkpart(x, y, z, nnxp, nnyp, nnzp, vol, Npart + 1, C3S,
                             Place);
            N_total += nump;
            numpartplaced++;

          } else {

            /* Place particle as gypsum */

            typegyp = ran1(Seed);
            N_sulfate += vol;
            N_total += nump;

            if ((fabs(Probanh - 1.0) < TINY) ||
                ((typegyp < Probanh) && (N_anhydrite < Target_anhydrite) &&
                 (vol <= (Target_anhydrite - N_anhydrite)))) {

              N_anhydrite += vol;
#ifdef DEBUG
              fprintf(Logfile, "\nAbout to place a GYPSUM particle...");
              fprintf(Logfile, "\n\tx = %d y = %d z = %d", x, y, z);
              fprintf(Logfile, "\n\tnnxp = %d nnyp = %d nnzp = %d", nnxp, nnyp,
                      nnzp);
              fprintf(Logfile, "\n\tvol = %d", vol);
              fflush(Logfile);
#endif
              nump = checkpart(x, y, z, nnxp, nnyp, nnzp, vol, Npart + 1,
                               ANHYDRITE, Place);
              numpartplaced++;
              Particle[Npart]->partphase = ANHYDRITE;

            } else if ((fabs(Probanh + Probhem - 1.0) < TINY) ||
                       ((typegyp < (Probanh + Probhem)) &&
                        (N_hemi < Target_hemi) &&
                        (vol <= (Target_hemi - N_hemi)))) {

              N_hemi += vol;
              nump = checkpart(x, y, z, nnxp, nnyp, nnzp, vol, Npart + 1,
                               HEMIHYD, Place);
              numpartplaced++;
              Particle[Npart]->partphase = HEMIHYD;

            } else {

              nump = checkpart(x, y, z, nnxp, nnyp, nnzp, vol, Npart + 1,
                               GYPSUM, Place);
              numpartplaced++;

              /* Correct phase ID of particle */
              Particle[Npart]->partphase = GYPSUM;
            }
          }

          if (Verbose)
            fprintf(Logfile, "\nN_total = %d and N_target = %d", N_total,
                    N_target);

        } else {

          /***
           *    Place as inert, CaCO3, slag, free lime,
           *    or pozzolanic material (fly ash or fumed silica)
           ***/

          nump = checkpart(x, y, z, nnxp, nnyp, nnzp, vol, Npart + 1, phnow,
                           Place);

          /* Correct phase ID of particle */

          Particle[Npart]->partphase = phnow;
        }

        /**** PUT NICK'S STUFF RIGHT HERE ****/
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

        fprintf(fscratch, "%d %d %d %d\n", cx, cy, cz, (int)Nnn);
        for (n = 0; n <= Nnn; n++) {
          for (m = n; m >= -n; m--) {
            fprintf(fscratch, "%d %d %.10f %.10f\n", n, m, AA[n][m].r,
                    AA[n][m].i);
          }
        }
      }
      if (Verbose) {
        fprintf(Logfile,
                "\nNumber real-shape particles desired in this bin was %d",
                numeach[ig]);
        fprintf(Logfile,
                "\nNumber real-shape particles _placed  in this bin was %d\n",
                numpartplaced);
      }

      break;

    default:

      /* Neither REALSHAPE nor SPHERES... What to do? */
      break;
    }

    /*** Sanity check on placed pixels ***/
    /*
    totpix = 0;
    for (kkk = 0; kkk < Zsyssize; ++kkk) {
        for (jjj = 0; jjj < Ysyssize; ++jjj) {
            for (iii = 0; iii < Xsyssize; ++iii) {
                if (Cemreal.val[getInt3dindex(Cemreal,iii,jjj,kkk)] == phnow)
    totpix++;
            }
        }
    }
   fprintf(Logfile,"... Total pixels of %d is now %d\n",phnow,totpix);
    fflush(Logfile);
    */
  }

  fflush(fscratch);
  fclose(fscratch);

  return (jg);
}

/***
 *    genonevoxparticles
 *
 *    Routine to place one-voxel particles of various sizes and phases at random
 *    locations in 3-D microstructure.
 *
 *     Arguments:
 *        int numeach holds the number of particles to add
 *        int pheach holds the phase of each size class
 *    Returns:
 *        Number of particles placed of last kind tried
 *
 *    Calls:        makesph, ran1
 *    Called by:    create
 ***/
int genonevoxparticles(int numeach, int pheach) {
  int m, n, i, j, k, ii, jj, x, y, z, ig, tries, na, foundpart;
  int phnow, nofit, n1, nxp, nyp, nzp, nnxp, nnyp, nnzp, partc, extpix,
      pcount[10];
  int numpershape, nump, done, total_particles_to_place, numchunk;
  int klow, khigh, mp, pixfrac, numlines, numitems, toobig;
  int absdiff, oldabsdiff, diam, darg, numpix, dispdist;
  int cx, cy, cz;
  int jg, numpartplaced, vol;
  float rx, ry, rz, testgyp, typegyp, frad, aa1, aa2;
  float sizeeach = 0.5;
  float vol1, ratio[10], saveratio, volume, volumecalc, v1;
  float fraction_progress = 0.10;
  float maxrx, maxry, maxrz;
  /* float length,width; */
  double factor, theta, phi, cosbeta, sinbeta, alpha, gamma, beta, total, abc;
  double realnum;
  fcomplex r1, ddd, icmplx;
  char buff[MAXSTRING], filename[MAXSTRING], scratchname[MAXSTRING];
  char *name, *newstring;
  struct lineitem line[MAXLINES];
  FILE *anmfile, *geomfile;

  nnxp = nnyp = nnzp = n1 = 0;
  x = y = z = 0;
  partc = nump = 0;
  saveratio = 0.0;

  dispdist = Dispdist;
  phnow = pheach; /* phase for this class */
  fprintf(Logfile, "Going to place %d particles of phase %d, radius 0.5\n",
          numeach, phnow);

  frad = sizeeach; /* float radius for this class */
  diam = 1;
  numpix = 1;

  /* loop for each sphere in this size class */

  for (jg = 0; jg < numeach; jg++) {

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

      darg = diam + (2 * dispdist);
      nofit = checksphere(x, y, z, darg, Check, Npart + 1, 0);
      if ((tries > MAXTRIES) && (dispdist > 0)) {
        fprintf(Logfile, "\nAble to place %d particles ", jg);
        fprintf(Logfile,
                "out of %d needed before reducing dispersion distance ",
                numeach);
        tries = 0;
        dispdist--;
        fprintf(Logfile, "to %d\n", dispdist);
      }

      if (tries > MAXTRIES) {
        fprintf(Logfile, "Could not place sphere %d\n", Npart);
        fprintf(Logfile, "\tafter %d random attempts\n\n", MAXTRIES);
        fprintf(Logfile, "\nTotal number spheres desired in this bin was %d",
                numeach);
        fprintf(Logfile, "\nActual number _placed  in this bin was %d", jg);

        warning("genmic", "Could not place a one-voxel particle");
        fflush(Logfile);
        return (jg);
      }
    } while (nofit);

    /* Place the voxel at x,y,z */

    Npart++;
    if (Npart > Npartc) {
      fprintf(Logfile, "Too many one-voxel particles being generated \n");
      fprintf(Logfile, "\tUser needs to increase value of NPARTC\n");
      fprintf(Logfile, "\tat top of C-code\n\n");
      fprintf(Logfile,
              "\nTotal number one-voxel particles desired in this bin was %d",
              numeach);
      fprintf(Logfile, "\nActual number _placed  in this bin was %d", jg);
      warning("genmic", "Too many one-voxel particles");
      fflush(Logfile);
      return (jg);
    }

    /* Allocate space for new particle info */

    Particle[Npart] = particlevector(numpix);
    if (!Particle[Npart]) {
      freegenmic();
      bailout("genmic", "Memory allocation error");
      fflush(Logfile);
      exit(1);
    }

    Particle[Npart]->partid = Npart;
    Particle[Npart]->flocid = Npart;
    NumberOfFlocs++;

    /* Default to cement placement */

    Particle[Npart]->partphase = C3S;
    Particle[Npart]->xc = x;
    Particle[Npart]->yc = y;
    Particle[Npart]->zc = z;
    Particle[Npart]->xd = (int)((2.0 * frad) + 0.5);
    Particle[Npart]->yd = (int)((2.0 * frad) + 0.5);
    Particle[Npart]->zd = (int)((2.0 * frad) + 0.5);

    if (phnow == C3S) {

      /***
       *    Determine whether to try to place as clinker or sulfate
       ***/

      testgyp = ran1(Seed);

      /***
       *    Do not use dispersion distance
       *    when placing particle
       ***/

      if (((testgyp > Probgyp) &&
           ((Target_sulfate - N_sulfate) < (Target_total - N_total))) ||
          (N_sulfate > Target_sulfate) ||
          (Volpart[ig] > (Target_sulfate - N_sulfate)) ||
          (Volpart[ig] > diam2vol(15.0))) {

        nofit = checksphere(x, y, z, diam, Place, Npart + 1, C3S);
        N_total += Volpart[ig];
      } else {

        /* Place particle as gypsum */

        typegyp = ran1(Seed);
        N_total += Volpart[ig];
        N_sulfate += Volpart[ig];

        if ((fabs(Probanh - 1.0) < TINY) ||
            ((typegyp < Probanh) && (N_anhydrite < Target_anhydrite) &&
             (Volpart[ig] <= (Target_anhydrite - N_anhydrite)))) {

          N_anhydrite += Volpart[ig];
          nofit = checksphere(x, y, z, diam, Place, Npart + 1, ANHYDRITE);
          Particle[Npart]->partphase = ANHYDRITE;

        } else if ((fabs(Probanh + Probhem - 1.0) < TINY) ||
                   ((typegyp < (Probanh + Probhem)) && (N_hemi < Target_hemi) &&
                    (Volpart[ig] <= (Target_hemi - N_hemi)))) {

          N_hemi += Volpart[ig];
          nofit = checksphere(x, y, z, diam, Place, Npart + 1, HEMIHYD);
          Particle[Npart]->partphase = HEMIHYD;

        } else {

          nofit = checksphere(x, y, z, diam, Place, Npart + 1, GYPSUM);

          /* Correct phase ID of particle */
          Particle[Npart]->partphase = GYPSUM;
        }
      }

    } else {

      /***
       *    Place as inert, CaCO3, C2S, slag,
       *    or pozzolanic material
       ***/

      nofit = checksphere(x, y, z, diam, Place, Npart + 1, phnow);

      /* Correct phase ID of particle */
      Particle[Npart]->partphase = phnow;
    }
  }

  return (jg);
}

/***
 *    create
 *
 *    Routine to obtain user input and create a starting
 *    microstructure.
 *
 *     Arguments:    Nothing
 *
 *    Calls:        genparticles
 *    Called by:    main program
 ***/
void create(void) {
  int i, j, k, numsize, phase[NUMSIZES], phase_id, num_phases_to_add, nplaced;
  int num[NUMSIZES], target_phase_vox;
  int extra_pixels, target_vox_i, linval;
  int delta_particles, total_phase_vox;
  int ip, inval, shapevar;
  int numparts[NPHASES][NUMSIZES];
  float frad[NUMSIZES], tval, val1, val2, binder_vfrac, water_vfrac;
  float diam[NUMSIZES];
  float *xgvec, *wgvec;
  char buff[MAXSTRING], buff1[MAXSTRING], gaussname[MAXSTRING];
  char buff2[MAXSTRING], buff3[MAXSTRING], instring[MAXSTRING];
  FILE *fgauss;

  /* initialize local arrays */

  xgvec = NULL;
  wgvec = NULL;
  fgauss = NULL;

  for (i = 0; i < NUMSIZES; i++) {
    num[i] = 0;
    phase[i] = 0;
    diam[i] = 0.0;
    frad[i] = 0.0;
  }

  for (i = 0; i < NPHASES; i++) {
    for (j = 0; j < NUMSIZES; j++) {
      numparts[i][j] = 0;
    }
  }

  Minsyssize = Xsyssize;
  if (Ysyssize < Minsyssize)
    Minsyssize = Ysyssize;
  if (Zsyssize < Minsyssize)
    Minsyssize = Zsyssize;

  fprintf(Logfile,
          "Add all SPHERES (0), all REAL-SHAPE (1), or MIXED (2)  particles? ");
  read_string(instring, sizeof(instring));
  Shape = atoi(instring);
  fprintf(Logfile, "%d\n", Shape);

  /***
   *       We must zero all the shapetype values (assume all are spheres).  We
   *       must do this because a test is made on these values whether or not
   *       the structure is mixed
   ***/

  for (i = 0; i < NSPHASES; i++) {
    Phase_shape[i].shapetype = 0;
    Phase_shape[i].ntheta = 0;
    Phase_shape[i].nphi = 0;
    Onepixnum[i] = 0;
  }

  /***
   *    Comment out this next block if/when we enable users
   *    to specify a different shape set for each phase
   ***/

  if (Shape != SPHERES) {

    /* At least some particles will have non-spherical shapes */

    fprintf(Logfile, "Where is the default shape database directory? ");
    fprintf(Logfile, "\n(Include final separator in path) ");
    read_string(buff, sizeof(buff));
    Filesep = buff[strlen(buff) - 1];
    if (Filesep != '/' && Filesep != '\\') {
      fprintf(Logfile, "\nNo final file separator detected.  Using /");
      Filesep = '/';
    }
    fprintf(Logfile, "%s\n", buff);
    sprintf(Pathroot, "%s", buff);
    fprintf(Logfile,
            "Take cement shapes from what data set in this directory? ");
    fprintf(Logfile, "\n(No file separator at beginning or end)");
    read_string(Shapeset, sizeof(Shapeset));
    fprintf(Logfile, "%s\n", Shapeset);
    if ((Shapeset[strlen(Shapeset) - 1] == '/') ||
        (Shapeset[strlen(Shapeset) - 1] == '\\')) {
      Shapeset[strlen(Shapeset) - 1] = '\0';
    }

    /***
     *    At least some particles will be real shape
     *    Allocate memory for the spherical harmonic arrays and
     *    for the Bbox array (only needed for real shapes)
     ***/

    A = complexmatrix(0, Nnn, -Nnn, Nnn);
    AA = complexmatrix(0, Nnn, -Nnn, Nnn);
    Y = complexmatrix(0, Nnn, -Nnn, Nnn);
    Int3darray(&Bbox, BoxXsize, BoxYsize, BoxZsize);

    if (!A || !Y || (Bbox.val == NULL)) {
      freegenmic();
      bailout("genmic", "Memory allocation error");
      fflush(stdout);
      exit(1);
    }

    /* Determine number of Gaussian quadrature points from file */

    sprintf(gaussname, "%s%s%cgauss120.dat", Pathroot, Shapeset, Filesep);
    fgauss = filehandler("genmic", gaussname, "READ");
    if (!fgauss) {
      freegenmic();
      exit(1);
    }

    Nphi = Ntheta = 0;
    while (!feof(fgauss)) {
      fscanf(fgauss, "%f %f", &val1, &val2);
      if (!feof(fgauss)) {
        Ntheta++;
      }
    }

    Nphi = Ntheta;

    fclose(fgauss);

    /* Allocate memory for Gaussian quadrature points */

    xgvec = fvector(Ntheta + 1);
    if (!xgvec) {
      freegenmic();
      bailout("genmic", "Could not allocate memory for xgvec");
      exit(1);
    }
    wgvec = fvector(Nphi + 1);
    if (!wgvec) {
      freegenmic();
      bailout("genmic", "Could not allocate memory for wgvec");
      exit(1);
    }

    /* Read Gaussian quadrature points from file */

    fgauss = filehandler("genmic", gaussname, "READ");
    if (!fgauss) {
      freegenmic();
      exit(1);
    }

    for (i = 1; i <= Ntheta; i++) {
      fscanf(fgauss, "%s %s", buff2, buff3);
      xgvec[i] = atof(buff2);
      wgvec[i] = atof(buff3);
    }
    fclose(fgauss);

  } else {

    /* All the particles will be spheres */

    Int3darray(&Bbox, BoxXsize, BoxYsize, BoxZsize);

    if (Bbox.val == NULL) {
      freegenmic();
      bailout("genmic", "Memory allocation error");
      fflush(stdout);
      exit(1);
    }

    for (i = 0; i < NUMSIZES; i++)
      Volpart[i] = 0;
  }

  fprintf(Logfile, "Enter the binder SOLID volume fraction: ");
  read_string(instring, sizeof(instring));
  binder_vfrac = atof(instring);
  fprintf(Logfile, "\n%f\n", binder_vfrac);
  fprintf(Logfile, "Enter the binder WATER volume fraction: ");
  read_string(instring, sizeof(instring));
  water_vfrac = atof(instring);
  fprintf(Logfile, "\n%f\n", water_vfrac);

  binder_vfrac = (binder_vfrac) / (binder_vfrac + water_vfrac);

  fprintf(Logfile, "Enter number of solid binder phases to add: ");
  read_string(instring, sizeof(instring));
  num_phases_to_add = atoi(instring);
  fprintf(Logfile, "\n%d\n", num_phases_to_add);
  for (k = 0; k < num_phases_to_add; k++) {
    fprintf(Logfile, "Enter phase id to add: ");
    read_string(instring, sizeof(instring));
    phase_id = atoi(instring);
    fprintf(Logfile, "\n%d\n", phase_id);
    fprintf(Logfile,
            "Enter volume fraction of this phase (total BINDER SOLID basis): ");
    read_string(instring, sizeof(instring));
    Vol_frac[phase_id] = atof(instring);
    fprintf(Logfile, "\n%f\n", Vol_frac[phase_id]);

    /* Convert to total VOLUME basis, binder + water system */
    Vol_frac[phase_id] *= binder_vfrac;

    target_phase_vox = (Vol_frac[phase_id] * (float)Binderpix) + 0.5;
    fprintf(Logfile, "Will need to enter %d pixels of this phase...\n",
            target_phase_vox);
    fprintf(
        Logfile,
        "Enter number of size classes for this phase (max is %d): ", NUMSIZES);
    read_string(instring, sizeof(instring));
    Size_classes[phase_id] = atoi(instring);
    if (Size_classes[phase_id] >= NUMSIZES) {
      fprintf(stderr,
              "\nERROR line 2990:  Number of size classes cannot exceed %d.  "
              "Exiting.\n\n",
              NUMSIZES);
      freegenmic();
      bailout("genmic", "Bad value for number of size classes");
      exit(1);
    }
    fprintf(Logfile, "\n%d\n", Size_classes[phase_id]);
    for (j = 0; j < Size_classes[phase_id]; j++) {
      fprintf(Logfile,
              "Enter diameter of size class %d in micrometers (integer values "
              "only): ",
              j);
      read_string(instring, sizeof(instring));
      Dinput[phase_id][j] = atof(instring);
      fprintf(Logfile, "\n%d\n", (int)(Dinput[phase_id][j]));
      /* Convert diameter to pixel units */
      Dinput[phase_id][j] *= (1.0 / Res);
      /* Round to nearest integer */
      Dinput[phase_id][j] = (float)((int)(Dinput[phase_id][j] + 0.5));
      fprintf(Logfile,
              "Enter volume fraction of phase %d particles in size class %d: ",
              phase_id, j);
      read_string(instring, sizeof(instring));
      Pdf[phase_id][j] = atof(instring);
      fprintf(Logfile, "\n%f\n", Pdf[phase_id][j]);
    }

    if (Shape == REALSHAPE) {
      /* All particles are real shape */
      if (phase_id != FLYASH && phase_id != SFUME) {
        shapevar = REALSHAPE;
        Phase_shape[phase_id].shapetype = REALSHAPE;
        strcpy(Phase_shape[phase_id].pathroot, Pathroot);
        strcpy(Phase_shape[phase_id].shapeset, Shapeset);
        strcpy(buff, Pathroot);
        strcpy(buff1, Shapeset);
      }
    } else if (Shape != SPHERES) {
      /* Some particles are real shape here */
      fprintf(Logfile, "Spheres (0) or Real shapes (1)? ");
      read_string(instring, sizeof(instring));
      shapevar = atoi(instring);
      if (shapevar == REALSHAPE) {
        Phase_shape[phase_id].shapetype = REALSHAPE;
        fprintf(Logfile, "What is the shape path? ");
        read_string(buff, sizeof(buff));
        Filesep = buff[strlen(buff) - 1];
        fprintf(Logfile, "%s\n", buff);
        strcpy(Phase_shape[phase_id].pathroot, buff);
        fprintf(Logfile,
                "Take cement shapes from what data set in this directory? ");
        read_string(buff1, sizeof(buff1));
        fprintf(Logfile, "%s\n", buff1);
        strcpy(Phase_shape[phase_id].shapeset, buff1);
      }
    }

    if (Phase_shape[phase_id].shapetype == REALSHAPE) {

      Phase_shape[phase_id].ntheta = Ntheta;
      Phase_shape[phase_id].nphi = Nphi;

      /* Allocate memory for Gaussian quadrature points */

      Phase_shape[phase_id].xg = fvector(Ntheta + 1);
      if (!Phase_shape[phase_id].xg) {
        freegenmic();
        bailout("genmic", "Could not allocate memory for xg");
        exit(1);
      }
      Phase_shape[phase_id].wg = fvector(Nphi + 1);
      if (!Phase_shape[phase_id].wg) {
        freegenmic();
        bailout("genmic", "Could not allocate memory for wg");
        exit(1);
      }

      for (i = 1; i <= Ntheta; i++) {
        Phase_shape[phase_id].xg[i] = xgvec[i];
        Phase_shape[phase_id].wg[i] = wgvec[i];
      }
    }

    /***
     * Now bubble sort the diameters in descending order
     ***/

    for (i = 0; i < Size_classes[phase_id]; i++) {
      for (j = (i + 1); j < Size_classes[phase_id]; j++) {
        if (Dinput[phase_id][i] < Dinput[phase_id][j]) {
          tval = Dinput[phase_id][i];
          Dinput[phase_id][i] = Dinput[phase_id][j];
          Dinput[phase_id][j] = tval;
          tval = Pdf[phase_id][i];
          Pdf[phase_id][i] = Pdf[phase_id][j];
          Pdf[phase_id][j] = tval;
        }
      }
    }

    /***
     * Determine number of particles of each diameter to add, assuming
     *spheres. Try to get the actual overall volume fraction closer to the
     *target while maintaining fidelity to the PSD
     *
     * The approach below starts with the largest size particles, and tries
     * to stay close to the desired fraction of particles this diameter
     * and larger
     *
     * Remember, target_phase_vox and total_phase_vox refer only to the phase
     * in question, not the combination of all the phases.
     ***/

    total_phase_vox = 0;
    for (i = 0; i < Size_classes[phase_id]; i++) {
      Volpart[i] = diam2vol(Dinput[phase_id][i]);
      numparts[phase_id][i] =
          (int)(((float)(target_phase_vox)*Pdf[phase_id][i] /
                 (float)(Volpart[i])) +
                0.5);
      total_phase_vox += numparts[phase_id][i] * Volpart[i];
      fprintf(Logfile, "Number of particles of diameter %f = %d\n",
              Dinput[phase_id][i], numparts[phase_id][i]);
      fprintf(Logfile, "Volume of each particle of diameter %f = %d\n",
              Dinput[phase_id][i], Volpart[i]);
    }
    fprintf(Logfile, "Total pixels based on PDF is %d\n", total_phase_vox);
    fprintf(Logfile, "Making adjustments of particle numbers now...\n");

    extra_pixels = 0;
    for (i = 0; i < Size_classes[phase_id] - 1; i++) {
      target_vox_i = (int)(((float)(target_phase_vox)*Pdf[phase_id][i]) + 0.5);
      fprintf(Logfile, "Target pixels in size class %d = %d\n", i,
              target_vox_i);
      extra_pixels += (target_vox_i - (numparts[phase_id][i] * Volpart[i]));
      fprintf(Logfile, "Extra pixels (cumulative) = %d\n", extra_pixels);
      if (Volpart[i] < (int)(fabs((float)extra_pixels))) {
        delta_particles = (float)(extra_pixels) / (float)(Volpart[i]);
        numparts[phase_id][i] += delta_particles;
        total_phase_vox += (delta_particles * Volpart[i]);
        extra_pixels -= (delta_particles * Volpart[i]);
        fprintf(Logfile, "Reduced number of particles in size class %d by %d\n",
                i, delta_particles);
      }
    }

    /***
     * Finally, adjust the number of the smallest size class to
     * make the overall volume fraction exact
     ***/

    if (Dinput[phase_id][Size_classes[phase_id] - 1] <= 1.0) {
      numparts[phase_id][Size_classes[phase_id] - 1] +=
          (target_phase_vox - total_phase_vox);
    }

    /***
     * Done with this phase.  Sanity check on PDF and total voxels of this
     *phase to be added.
     ***/

    /*
    total_phase_vox = 0;
    for (i = 0; i < Size_classes[phase_id]; i++) {
        total_phase_vox += (Volpart[i] * numparts[phase_id][i]);
    }

   fprintf(Logfile,"\n***************************************************************\n");
   fprintf(Logfile,"    Targeted %d vox of phase %d, and will be adding %d
   vox\n", target_phase_vox,phase_id,total_phase_vox);
   fprintf(Logfile,"\n***************************************************************\n");

    target_vox_i = 0;
    for (i = 0; i < Size_classes[phase_id]; i++) {
        target_vox_i = (float)(Volpart[i] * numparts[phase_id][i]);
       fprintf(Logfile,"    Size class %2d, diam = %2d, target pdf = %.4f,
   target_vox_i = %d\n", i,
   (int)(Dinput[phase_id][i]),Pdf[phase_id][i],target_vox_i);
    }
   fprintf(Logfile,"\n***************************************************************\n");
    */

    fflush(Logfile);
  }

  /*  All phases are done, except possibly the fine portion of the aggregate
   * grading */

  if (Size_classes[INERTAGG] > 0) {
    Vol_frac[INERTAGG] *= binder_vfrac; /* Converts to total VOLUME basis,
                                           binder + water system */
    target_phase_vox = (Vol_frac[INERTAGG] * (float)Binderpix) + 0.5;
    fprintf(Logfile,
            "Will need to enter %d pixels of INERT AGGREGATE to binder...\n",
            target_phase_vox);
    fprintf(Logfile, "Number of size classes for INERTAGG phase is %d\n",
            Size_classes[INERTAGG]);
    fflush(Logfile);

    if (Shape == REALSHAPE) {
      /* All particles are real shape */
      shapevar = REALSHAPE;
      Phase_shape[INERTAGG].shapetype = REALSHAPE;
      strcpy(Phase_shape[INERTAGG].pathroot, Pathroot);
      strcpy(Phase_shape[INERTAGG].shapeset, Shapeset);
      strcpy(buff, Pathroot);
      strcpy(buff1, Shapeset);

      Phase_shape[INERTAGG].ntheta = Ntheta;
      Phase_shape[INERTAGG].nphi = Nphi;

      /* Allocate memory for Gaussian quadrature points */

      Phase_shape[INERTAGG].xg = fvector(Ntheta + 1);
      if (!Phase_shape[INERTAGG].xg) {
        freegenmic();
        bailout("genmic", "Could not allocate memory for xg");
        exit(1);
      }
      Phase_shape[INERTAGG].wg = fvector(Nphi + 1);
      if (!Phase_shape[INERTAGG].wg) {
        freegenmic();
        bailout("genmic", "Could not allocate memory for wg");
        exit(1);
      }

      for (i = 1; i <= Ntheta; i++) {
        Phase_shape[INERTAGG].xg[i] = xgvec[i];
        Phase_shape[INERTAGG].wg[i] = wgvec[i];
      }
    }

    /***
     * Now bubble sort the diameters in descending order
     ***/

    for (i = 0; i < Size_classes[INERTAGG]; i++) {
      for (j = (i + 1); j < Size_classes[INERTAGG]; j++) {
        if (Dinput[INERTAGG][i] < Dinput[INERTAGG][j]) {
          tval = Dinput[INERTAGG][i];
          Dinput[INERTAGG][i] = Dinput[INERTAGG][j];
          Dinput[INERTAGG][j] = tval;
          tval = Pdf[INERTAGG][i];
          Pdf[INERTAGG][i] = Pdf[INERTAGG][j];
          Pdf[INERTAGG][j] = tval;
        }
      }
    }

    /***
     * Determine number of particles of each diameter to add, assuming
     *spheres. Try to get the actual overall volume fraction closer to the
     *target while maintaining fidelity to the PSD
     *
     * The approach below starts with the largest size particles, and tries
     * to stay close to the desired fraction of particles this diameter
     * and larger
     *
     * Remember, target_phase_vox and total_phase_vox refer only to the phase
     * in question, not the combination of all the phases.
     ***/

    /*  MUST NORMALIZE PDF OF AGGREGATE TO 1 */

    total_phase_vox = 0;
    for (i = 0; i < Size_classes[INERTAGG]; i++) {
      Volpart[i] = diam2vol(Dinput[INERTAGG][i]);
      numparts[INERTAGG][i] =
          (int)(((float)(target_phase_vox)*Pdf[INERTAGG][i] /
                 (float)(Volpart[i])) +
                0.5);
      total_phase_vox += numparts[INERTAGG][i] * Volpart[i];
      fprintf(Logfile, "Number of particles of diameter %f = %d\n",
              Dinput[INERTAGG][i], numparts[INERTAGG][i]);
      fprintf(Logfile, "Volume of each particle of diameter %f = %d\n",
              Dinput[INERTAGG][i], Volpart[i]);
    }
    fprintf(Logfile, "Total pixels based on PDF is %d\n", total_phase_vox);
    fprintf(Logfile, "Making adjustments of particle numbers now...\n");

    extra_pixels = 0;
    for (i = 0; i < Size_classes[INERTAGG] - 1; i++) {
      target_vox_i = (int)(((float)(target_phase_vox)*Pdf[INERTAGG][i]) + 0.5);
      fprintf(Logfile, "Target pixels in size class %d = %d\n", i,
              target_vox_i);
      extra_pixels += (target_vox_i - (numparts[INERTAGG][i] * Volpart[i]));
      fprintf(Logfile, "Extra pixels (cumulative) = %d\n", extra_pixels);
      if (Volpart[i] < (int)(fabs((float)extra_pixels))) {
        delta_particles = (float)(extra_pixels) / (float)(Volpart[i]);
        numparts[INERTAGG][i] += delta_particles;
        total_phase_vox += (delta_particles * Volpart[i]);
        extra_pixels -= (delta_particles * Volpart[i]);
        fprintf(Logfile, "Reduced number of particles in size class %d by %d\n",
                i, delta_particles);
      }
    }

    /***
     * Finally, adjust the number of the smallest size class to
     * make the overall volume fraction exact
     ***/

    if (Dinput[INERTAGG][Size_classes[INERTAGG] - 1] <= 1.0) {
      numparts[INERTAGG][Size_classes[INERTAGG] - 1] +=
          (target_phase_vox - total_phase_vox);
    }
  }

  /* ADDITION OF AGGREGATE TO BINDER FINISHED */

  /***
   *  All PSD information is now settled.  Must lump all the information
   *  by diameter across phases
   ***/

  /***
   * Determine numsize by scanning through the numparts array and counting
   * all nonzero entries
   ***/

  numsize = 0;
  for (i = 1; i < NPHASES; i++) {
    for (j = 0; j < Size_classes[i]; j++) {
      if (numparts[i][j] > 0) {
        if (Dinput[i][j] > 1.0) {
          diam[numsize] = Dinput[i][j];
          frad[numsize] = (float)(diam[numsize] / 2.0);
          num[numsize] = numparts[i][j];
          phase[numsize] = i;
          numsize++;
        } else {
          Onepixnum[i] = numparts[i][j];
          if (Verbose)
            fprintf(Logfile, "\nOne-pix particles of phase %d = %d", i,
                    Onepixnum[i]);
        }
      }
    }
  }

  if (numsize > NUMSIZES || numsize < 0) {
    freegenmic();
    bailout("genmic", "Bad value for numsize");
    exit(1);
  }

  /* Now sort on diam in descending order */

  for (i = 0; i < numsize; i++) {
    for (j = (i + 1); j < numsize; j++) {
      if (diam[i] < diam[j]) {
        tval = diam[i];
        diam[i] = diam[j];
        diam[j] = tval;
        tval = frad[i];
        frad[i] = frad[j];
        frad[j] = tval;
        linval = num[i];
        num[i] = num[j];
        num[j] = linval;
        inval = phase[i];
        phase[i] = phase[j];
        phase[j] = inval;
      }
    }
  }

  fprintf(Logfile, "Enter dispersion factor (separation distance ");
  fprintf(Logfile, "in pixels) for spheres (0-2)\n");
  fprintf(Logfile, "0 corresponds to totally random placement\n");
  read_string(instring, sizeof(instring));
  Dispdist = atoi(instring);
  fprintf(Logfile, "%d \n", Dispdist);
  if ((Dispdist < 0) || (Dispdist > 2)) {
    freegenmic();
    bailout("genmic", "Bad value for dispersion distance");
    exit(1);
  }

  fprintf(Logfile, "Enter probability for gypsum particles ");
  fprintf(Logfile, "on a random particle basis (0.0-1.0) \n");
  read_string(instring, sizeof(instring));
  Probgyp = atof(instring);
  fprintf(Logfile, "%f \n", Probgyp);
  if ((Probgyp < -TINY) || (Probgyp > 1.0 + TINY)) {
    freegenmic();
    bailout("genmic", "Bad value for total gypsum probability");
    exit(1);
  }

  fprintf(Logfile,
          "Enter probability for hemihydrate form of gypsum (0.0-1.0)\n");
  read_string(instring, sizeof(instring));
  Probhem = atof(instring);
  fprintf(Logfile, "%f\n", Probhem);
  fprintf(Logfile,
          "Enter probability for anhydrite form of gypsum (0.0-1.0)\n");
  read_string(instring, sizeof(instring));
  Probanh = atof(instring);
  fprintf(Logfile, "%f\n", Probanh);
  if ((Probhem < -TINY) || (Probhem > 1.0 + TINY) || (Probanh < -TINY) ||
      (Probanh > 1.0 + TINY) || ((Probanh + Probhem) > 1.0 + TINY + TINY)) {

    freegenmic();
    bailout("genmic", "Bad value for hemihyd or anhydrite probs");
    exit(1);
  }

  if ((numsize > 0) && (numsize < (NUMSIZES + 1))) {

    if (Verbose) {
      fprintf(Logfile, "Calculated information for ");
      fprintf(Logfile, "each particle class (largest size 1st)\n");
      fprintf(Logfile, "Phases are %d- Cement and (random) calcium ", C3S);
      fprintf(Logfile, "sulfate, %d- C2S, %d- Gypsum, ", C2S, GYPSUM);
      fprintf(Logfile, "%d- hemihydrate %d- anhydrite ", HEMIHYD, ANHYDRITE);
      fprintf(Logfile, "%d- Silica fume, %d- Inert, ", SFUME, INERT);
      fprintf(Logfile, "%d- Slag, %d- CaCO3 %d- Fly Ash, ", SLAG, CACO3,
              FLYASH);
      fprintf(Logfile, "%d- Lime\n", FREELIME);
    }

    Ntheta = Nphi = 0;

    for (ip = 0; ip < numsize; ip++) {

      /* Convert sphere diameter to volume in pixels */

      if (Verbose) {
        fprintf(Logfile, "Adding particles of effective diameter %d\n",
                (int)diam[ip]);
        fprintf(Logfile, "Phase of these particles is %d \n", phase[ip]);
        fprintf(Logfile, "Calculated number of these particles is %d\n",
                num[ip]);
        fflush(Logfile);
      }
      Volpart[ip] = diam2vol(diam[ip]);

      if (phase[ip] == C3S) {
        Target_total += num[ip] * Volpart[ip];
        if (Volpart[ip] <= 1767) {
          /* Particle diameter less than 15 micrometers */
          Target_total_lt15 += num[ip] * Volpart[ip];
        }
      }
    }

    Target_sulfate = (double)Target_total * Probgyp;
    Target_anhydrite = (double)Target_total * Probgyp * Probanh;
    Target_hemi = (double)Target_total * Probgyp * Probhem;

    /* Modify probability of calcium sulfate so that all calcium sulfates
        are placed at diameters less than 15 micrometers */

    if (Target_total_lt15 > 0)
      Probgyp = (Target_sulfate / Target_total_lt15);
    if (Verbose) {
      fprintf(Logfile, "\nTarget_sulfate = %d", Target_sulfate);
      fprintf(Logfile, "\nTarget_anhydrite = %d", Target_anhydrite);
      fprintf(Logfile, "\nTarget_hemi = %d", Target_hemi);
      fflush(Logfile);
    }

    /***
     *    Place particles at random
     ***/

    if (Verbose) {
      fprintf(Logfile, "\nGoing into genparticles now...");
      fflush(Logfile);
    }

    /* We don't need the return value in this case */
    nplaced = genparticles(numsize, num, frad, phase);
    if (Verbose) {
      fprintf(Logfile, "\nBack Out of genparticles now...");
      fflush(Logfile);
    }

    /*** Sanity check on pore voxels ***/
    /*
    totpix = 0;
    for (kkk = 0; kkk < Zsyssize; ++kkk) {
        for (jjj = 0; jjj < Ysyssize; ++jjj) {
            for (iii = 0; iii < Xsyssize; ++iii) {
                if (Cemreal.val[getInt3dindex(Cemreal,iii,jjj,kkk)] == 0)
    totpix++;
            }
        }
    }
   fprintf(Logfile,"\nTotal pore voxels now is %d",totpix);
    */
  }

  free_Int3darray(&Bbox);
  if (Y)
    free_complexmatrix(Y, 0, Nnn, -Nnn, Nnn);
  if (AA)
    free_complexmatrix(AA, 0, Nnn, -Nnn, Nnn);
  if (A)
    free_complexmatrix(A, 0, Nnn, -Nnn, Nnn);
  if (xgvec)
    free_fvector(xgvec);
  if (wgvec)
    free_fvector(wgvec);

  return;
}

/***
 *    drawfloc
 *
 *    Routine to draw a particle during flocculation routine
 *
 *     Arguments:
 *        struct particle *partpoint is the pointer to this particle structure
 *        const int mode is set to Erase or Draw
 *
 *     Returns:    integer flag telling whether sphere will fit
 *
 *    Calls:        No other routines
 *    Called by:    makefloc
 ***/
void drawfloc(struct particle *partpoint, const int mode) {
  int xp, yp, zp, i;
  int pid, phid;
  char strmode[10];

  pid = phid = POROSITY;
  sprintf(strmode, "Erasing");
  if (mode == Draw) {
    sprintf(strmode, "Drawing");
    pid = partpoint->partid + 1;
    phid = partpoint->partphase;
  }

  /* Check all pixels belonging to the particle */

  for (i = 0; i < partpoint->numpix; i++) {
    xp = partpoint->xi[i];
    yp = partpoint->yi[i];
    zp = partpoint->zi[i];
    Cement.val[getInt3dindex(Cement, xp, yp, zp)] = pid;
    Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] = phid;
  }
  return;
}

/***
 *    checkfloc
 *
 *    Routine to check spherical particle placement during flocculation
 *
 *     Arguments:
 *        struct particle *partpoint points to the current particle structure
 *        int dx,dy,dz is the direction of movement of this particle
 *
 *     Returns:    int flag indicating if placement is possible
 *
 *    Calls:        No other routines
 *    Called by:    makefloc
 ***/
int checkfloc(struct particle *partpoint, int dx, int dy, int dz) {
  int blocked_by, xp, yp, zp, i, xmark;

  blocked_by = 0; /* Flag indicating if placement is possible */

  /* Check all pixels belonging to the particle */

  xmark = partpoint->xi[0] + dx;
  for (i = 0; (i < partpoint->numpix) && (!blocked_by); i++) {

    xp = partpoint->xi[i] + dx;
    yp = partpoint->yi[i] + dy;
    zp = partpoint->zi[i] + dz;
    xp += checkbc(xp, Xsyssize);
    yp += checkbc(yp, Ysyssize);
    zp += checkbc(zp, Zsyssize);

    /* Check for overlap with aggregate */

    if ((Simwall) && ((xmark - Wallpos) * (xp - Wallpos)))
      blocked_by = ((int)TMPAGGID);

    if ((Cement.val[getInt3dindex(Cement, xp, yp, zp)] > POROSITY) &&
        (!blocked_by)) {

      /* Particle hit; record its ID */

      blocked_by = Cement.val[getInt3dindex(Cement, xp, yp, zp)] - 1;
    }
  }

  /***
   *    Return flag indicating if sphere will fit (=0)
   *    or not (=ID of particle preventing the fit)
   ***/

  return (blocked_by);
}

/***
 *    makefloc
 *
 *    New routine to perform flocculation of particles
 *
 *     Arguments:    None
 *     Returns:    Nothing
 *
 *    Calls:        drawfloc, checkfloc, ran1
 *    Called by:    main program
 **/
void makefloc(void) {
  register int i, j, ipart;
  float degfloc;
  int targetnumflocs, numflocs, numdeleted;
  int blocked_by, dx, dy, dz, moveran, flochit;
  char instring[MAXSTRING];
  struct particle *partpoint, *partkeep, *parttmp;
  int *index;

  dx = dy = dz = 0;
  partpoint = NULL;
  partkeep = NULL;
  parttmp = NULL;

  /***
   *    Allocate memory for index table
   ***/

  index = ivector(Npart + 1);
  if (!index) {
    freegenmic();
    bailout("makefloc", "Memory allocation error");
    exit(1);
  }

  for (i = 1; i <= Npart; i++) {
    index[i] = Particle[i]->partid;
  }

  /*  This routine asks for the degree of flocculation.  A value of 0 */
  /*  means that no intentional flocs will be made, while a value of 1 */
  /*  means that the routine will continue until every particle is */
  /*  attached to a floc */

  fprintf(Logfile, "\nEnter the degree of flocculation desired (0.0 to 1.0): ");
  fflush(Logfile);
  read_string(instring, sizeof(instring));
  degfloc = atof(instring);
  fprintf(Logfile, "%f\n", degfloc);
  fflush(Logfile);
  targetnumflocs = Npart;
  if (degfloc > 0.0) {
    targetnumflocs = (int)(((float)(Npart)) * (1.0 - degfloc));
    if (targetnumflocs > Npart)
      targetnumflocs = Npart;
    if (targetnumflocs < 1)
      targetnumflocs = 1;
  }
  fprintf(Logfile, "Target number of flocs is %d\n", targetnumflocs);
  fflush(Logfile);

  numflocs = Npart;
  while (numflocs > targetnumflocs) {

    numdeleted = 0;
    /* Try to move each floc in turn */

    for (ipart = 1; ipart <= Npart; ipart++) {
      if (Particle[ipart] == NULL) {
        numdeleted++;
      } else {

        /* Move this particle in a randomly chosen Cartesian direction */

        moveran = 6.0 * ran1(Seed);

        dx = dy = dz = 0;

        switch (moveran) {
        case 0:
          dx = 1;
          break;
        case 1:
          dx = (-1);
          break;
        case 2:
          dy = 1;
          break;
        case 3:
          dy = (-1);
          break;
        case 4:
          dz = 1;
          break;
        case 5:
          dz = (-1);
          break;
        default:
          break;
        }

        /* First erase all particles in the floc */

        partpoint = Particle[ipart];
        while (partpoint != NULL) {
          drawfloc(partpoint, Erase); /* set to porosity */
          partkeep = partpoint;
          partpoint = partpoint->nextpart;
        }

        /* Now try to draw the floc at new location */

        partpoint = Particle[ipart];
        blocked_by = 0;
        while ((partpoint != NULL) && (!blocked_by)) {
          blocked_by =
              checkfloc(partpoint, dx, dy, dz); /* zero if not blocked */
          partkeep = partpoint;
          partpoint = partpoint->nextpart;
        }

        if (!blocked_by) {

          /* Floc fits at new location, so draw it there */
          partpoint = Particle[ipart];
          while (partpoint != NULL) {
            /* Update pixel locations for particle */
            for (j = 0; j < partpoint->numpix; j++) {
              partpoint->xi[j] += dx;
              partpoint->yi[j] += dy;
              partpoint->zi[j] += dz;
              partpoint->xi[j] += checkbc(partpoint->xi[j], Xsyssize);
              partpoint->yi[j] += checkbc(partpoint->yi[j], Ysyssize);
              partpoint->zi[j] += checkbc(partpoint->zi[j], Zsyssize);
            }
            drawfloc(partpoint, Draw);
            partpoint = partpoint->nextpart;
          }

        } else {

          /* Floc does not fit at this location. */
          /* First of all, put the floc in its most recent unblocked location
           */
          partpoint = Particle[ipart];
          while (partpoint != NULL) {
            drawfloc(partpoint, Draw);
            partkeep = partpoint;
            partpoint = partpoint->nextpart;
          }

          /* At this point, partkeep should point to the last particle in the
           * moving floc */

          /* Now, what did the floc hit? */

          if (blocked_by != TMPAGGID) {
            flochit = index[blocked_by];
            partpoint = Particle[ipart];
            /* Floc hit another particle.  Add that particle to the floc */
            /* Move all of the particles from the blocking cluster to the
             * moving cluster */
            parttmp = Particle[flochit];
            /* parttmp is the floc containing the blocking particle */
            /* so point the last particle in the moving floc (partkeep) to the
               first particle in the blocking floc, which is pointed to by
               parttmp */
            partkeep->nextpart = parttmp;
            while (parttmp != NULL) {
              index[parttmp->partid] = ipart;
              parttmp->flocid = partpoint->flocid;
              parttmp = parttmp->nextpart;
            }

            /* Now we no longer need the blocking floc structure because it
               has been merged with the moving floc */
            Particle[flochit] = NULL;
            /*
            free_particlevector(Particle[index[blocked_by]]);
           fprintf(Logfile,"\nMemory freeing was successful");
            fflush(Logfile);
            */
            if (Particle[flochit] != NULL) {
              fprintf(stderr, "\nWARNING line 3775: Hit floc was not erased "
                              "from memory.");
              fflush(stderr);
              Particle[flochit] = NULL;
            }
            numflocs--;
          }
        }
      }
    }
    fprintf(Logfile,
            "\nNumber flocs deleted so far is %d and number of flocs is %d\n",
            numdeleted, numflocs);
    fflush(Logfile);
  }

  if (index)
    free_ivector(index);

  NumberOfFlocs = numflocs;
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
  int npor, nc2s, ngyp, ncem, nagg, nsfume, ninert, nfreelime;
  int nflyash, nanh, nhem, ncaco3, nslag;
  int nc3a, nc4af, nk2so4, nna2so4;
  int i, j, k, valph;

  /* Counters for the various phase fractions */

  npor = ngyp = ncem = nagg = ninert = 0;
  nfreelime = nflyash = nanh = ncaco3 = 0;
  nslag = nc3a = nfreelime = nhem = nc4af = 0;
  nk2so4 = nna2so4 = 0;
  ;
  nslag = nc2s = nsfume = nflyash = nanh = 0;
  nhem = ncaco3 = nfreelime = 0;

  /* Check all pixels in 3-D microstructure */

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        valph = Cemreal.val[getInt3dindex(Cemreal, i, j, k)];
        switch (valph) {
        case POROSITY:
          npor++;
          break;
        case C3S:
          ncem++;
          break;
        case C2S:
          nc2s++;
          break;
        case C3A:
          nc3a++;
          break;
        case C4AF:
          nc4af++;
          break;
        case K2SO4:
          nk2so4++;
          break;
        case NA2SO4:
          nna2so4++;
          break;
        case GYPSUM:
          ngyp++;
          break;
        case HEMIHYD:
          nhem++;
          break;
        case ANHYDRITE:
          nanh++;
          break;
        case INERTAGG:
          nagg++;
          break;
        case SFUME:
          nsfume++;
          break;
        case INERT:
          ninert++;
          break;
        case SLAG:
          nslag++;
          break;
        case FLYASH:
          nflyash++;
          break;
        case CACO3:
          ncaco3++;
          break;
        case FREELIME:
          nfreelime++;
          break;
        default:
          fprintf(stderr, "\nWARNING line 3885:  Unidentifiable phase ID (%d) ",
                  valph);
          fprintf(stderr, "encountered.\nPixel at location ");
          fprintf(stderr, "(%d,%d,%d)\n", i, j, k);
          fflush(stderr);
          break;
        }
      }
    }
  }

  /* Output results */

  if (Verbose) {
    fprintf(Logfile, "\nPhase counts are: \n");
    fprintf(Logfile, "\tPorosity = %d \n", npor);
    fprintf(Logfile, "\tCement = %d \n", ncem);
    fprintf(Logfile, "\tC2S = %d \n", nc2s);
    fprintf(Logfile, "\tGypsum = %d \n", ngyp);
    fprintf(Logfile, "\tAnhydrite = %d \n", nanh);
    fprintf(Logfile, "\tHemihydrate = %d \n", nhem);
    fprintf(Logfile, "\tSilica fume = %d \n", nsfume);
    fprintf(Logfile, "\tInert = %d \n", ninert);
    fprintf(Logfile, "\tSlag = %d \n", nslag);
    fprintf(Logfile, "\tCaCO3 = %d \n", ncaco3);
    fprintf(Logfile, "\tFly Ash = %d \n", nflyash);
    fprintf(Logfile, "\tAggregate = %d \n", nagg);
  }

  return;
}

/***
 *    measagg
 *
 *    Routine to measure phase fractions as a
 *    function of distance from aggregate surface
 *
 *     Arguments:    None
 *     Returns:    Nothing
 *
 *    Calls:        No other routines
 *    Called by:    main program
 ***/
void measagg(void) {
  int phase[NPHASES], ptot, icnt, ixlo, ixhi, iy, iz, phid, idist;

  fprintf(Logfile, "Distance  Porosity  Cement  C2S  Gypsum  Anhydrite ");
  fprintf(Logfile, "Hemihydrate Pozzolan  Inert   Slag  CaCO3   Fly Ash\n");

  /* Increase distance from aggregate in increments of one */

  for (idist = 1; idist <= Wallpos; idist++) {

    /* Pixel to the left of aggregate surface */

    ixlo = Wallpos - idist;

    /* Pixel to the right of aggregate surface */

    ixhi = Wallpos + idist;

    /* Initialize phase counts for this distance */

    for (icnt = 0; icnt < NPHASES; icnt++) {
      phase[icnt] = 0;
    }

    ptot = 0;

    /***
     *    Check all pixels which are this distance
     *    from aggregate surface
     ***/

    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 0; iz < Zsyssize; iz++) {

        phid = Cemreal.val[getInt3dindex(Cemreal, ixlo, iy, iz)];
        ptot++;
        if (phid <= FLYASH) {
          phase[phid]++;
        }

        phid = Cemreal.val[getInt3dindex(Cemreal, ixhi, iy, iz)];
        ptot++;
        if (phid <= FLYASH) {
          phase[phid]++;
        }
      }
    }

    /* Output results for this distance from surface */

    fprintf(Logfile, "%d   ", idist);
    fprintf(Logfile, "%d   ", phase[POROSITY]);
    fprintf(Logfile, "%d    ", phase[C3S]);
    fprintf(Logfile, "%d  ", phase[C2S]);
    fprintf(Logfile, "%d  ", phase[GYPSUM]);
    fprintf(Logfile, "%d ", phase[ANHYDRITE]);
    fprintf(Logfile, "%d ", phase[HEMIHYD]);
    fprintf(Logfile, "%d  ", phase[SFUME]);
    fprintf(Logfile, "%d ", phase[INERT]);
    fprintf(Logfile, "%d ", phase[SLAG]);
    fprintf(Logfile, "%d ", phase[CACO3]);
    fprintf(Logfile, "%d\n", phase[FLYASH]);
  }

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

    freegenmic();
    bailout("genmic", "Memory allocation failure");
    fflush(Logfile);
    exit(1);
  }

  fprintf(Logfile, "Enter phase to analyze 0) pores 1) Cement  \n");
  read_string(instring, sizeof(instring));
  npix = atoi(instring);
  fprintf(Logfile, "%d \n", npix);
  if ((npix != POROSITY) && (npix != C3S)) {
    freegenmic();
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

      if (((Cement.val[getInt3dindex(Cement, i, j, k)] == npix) &&
           ((Cement.val[getInt3dindex(Cement, i, j, Zsyssize - 1)] == npix) ||
            (Cement.val[getInt3dindex(Cement, i, j, Zsyssize - 1)] ==
             (npix + Burnt)))) ||
          ((Cement.val[getInt3dindex(Cement, i, j, Zsyssize - 1)] > 0) &&
           (Cement.val[getInt3dindex(Cement, i, j, k)] > 0) &&
           (Cement.val[getInt3dindex(Cement, i, j, k)] < Burnt) &&
           (npix == C3S))) {

        /* Start a burn front */

        Cement.val[getInt3dindex(Cement, i, j, k)] += Burnt;
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
                if ((Cement.val[getInt3dindex(Cement, x1, y1, z1)] == npix) ||
                    ((Cement.val[getInt3dindex(Cement, x1, y1, z1)] > 0) &&
                     (Cement.val[getInt3dindex(Cement, x1, y1, z1)] < Burnt) &&
                     (npix == C3S))) {

                  ntot++;
                  Cement.val[getInt3dindex(Cement, x1, y1, z1)] += Burnt;
                  nnew++;

                  if (nnew >= Maxburning) {
                    fprintf(Logfile, "error in size of nnew \n");
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

  fprintf(Logfile, "Phase ID= %d \n", npix);
  fprintf(Logfile, "Number accessible from top= %d \n", ntop);
  fprintf(Logfile, "Number contained in through pathways= %d \n", nthrough);

  /***
   *    Return the burnt sites to their original
   *    phase values
   ***/

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {
        if (Cement.val[getInt3dindex(Cement, i, j, k)] >= Burnt) {
          Cement.val[getInt3dindex(Cement, i, j, k)] -= Burnt;
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
  int totpix, iii, jjj, kkk;
  char filen[MAXSTRING], filepart[MAXSTRING], filestruct[MAXSTRING], ch;
  FILE *outfile, *partfile, *infile;

  /*** Sanity check on placed pixels ***/
  totpix = 0;
  for (kkk = 0; kkk < Zsyssize; ++kkk) {
    for (jjj = 0; jjj < Ysyssize; ++jjj) {
      for (iii = 0; iii < Xsyssize; ++iii) {
        if (Cemreal.val[getInt3dindex(Cemreal, iii, jjj, kkk)] == 0)
          totpix++;
      }
    }
  }
  fprintf(Logfile, "... Total pore voxels is now %d\n", totpix);
  fflush(Logfile);

  fprintf(Logfile, "Enter name of file for final microstructure image\n");
  read_string(filen, sizeof(filen));
  fprintf(Logfile, "%s\n", filen);

  outfile = filehandler("genmic", filen, "WRITE");
  if (!outfile) {
    freegenmic();
    exit(1);
  }

  fprintf(Logfile, "Enter name of file to save particle IDs to \n");
  read_string(filepart, sizeof(filepart));
  fprintf(Logfile, "%s\n", filepart);

  partfile = filehandler("genmic", filepart, "WRITE");
  if (!partfile) {
    freegenmic();
    exit(1);
  }

  /***
   *    Images must carry along information about the
   *    VCCTL software version used to create the file, the system
   *    size, and the image resolution.
   ***/

  if (write_imgheader(outfile, Xsyssize, Ysyssize, Zsyssize, Res)) {
    fclose(outfile);
    fclose(partfile);
    freegenmic();
    bailout("genmic", "Error writing microstructure image header");
    exit(1);
  }

  if (write_imgheader(partfile, Xsyssize, Ysyssize, Zsyssize, Res)) {
    fclose(outfile);
    fclose(partfile);
    freegenmic();
    bailout("genmic", "Error writing particle image header");
    exit(1);
  }

  /***
   *  2025 August 04
   *  New convention is to write microstructures in C-order, where Z varies
   *the fastest, then Y, then X.
   ***/
  for (ix = 0; ix < Xsyssize; ix++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 0; iz < Zsyssize; iz++) {
        valout = Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
        /*
        if (valout == (int)(INERTAGG)) {
          valout = (int)(POROSITY);
        }
        */
        fprintf(outfile, "%d\n", valout);
        valout = Cement.val[getInt3dindex(Cement, ix, iy, iz)];
        if (valout == (int)(TMPAGGID)) {
          valout = (int)(POROSITY);
        } else if (valout < 0) {
          valout = (int)(POROSITY);
        }

        fprintf(partfile, "%d\n", valout);
      }
    }
  }

  fclose(outfile);
  fclose(partfile);

  /*** PUT NICK's STUFF RIGHT HERE ***/

  sprintf(filestruct, "%s.struct", filen);
  outfile = filehandler("genmic", filestruct, "WRITE");
  infile = filehandler("genmic", "scratchaggfile.dat", "READ");
  fprintf(outfile, "%d\n", Npart);
  while (!feof(infile)) {
    ch = getc(infile);
    if (!feof(infile))
      putc(ch, outfile);
  }

  fclose(infile);
  fflush(outfile);
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
    for (m = 0; m <= 2 * n; m++) {
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
 *    particlevector
 *
 *    Routine to allocate memory for a 1D vector of pointers to particle
 *structures. All array indices are assumed to start with zero.
 *
 *    Arguments:    int number of pixels in the particle
 *    Returns:    Pointer to memory location of first element
 *
 *    Calls:        no other routines
 *    Called by:    main routine
 *
 ***/
struct particle *particlevector(int numpix) {
  struct particle *ps;
  /* Allocate space for new particle info */

  ps = (struct particle *)malloc(sizeof(struct particle));
  if (ps != NULL) {
    ps->xi = (int *)malloc(numpix * sizeof(int));
    if (ps->xi != NULL) {
      ps->yi = (int *)malloc(numpix * sizeof(int));
      if (ps->yi != NULL) {
        ps->zi = (int *)malloc(numpix * sizeof(int));
        if (ps->zi != NULL) {
          ps->numpix = numpix;
          ps->nextpart = NULL;
          return (ps);
        } else {
          free(ps->yi);
          free(ps->xi);
          free(ps);
        }
      } else {
        free(ps->xi);
        free(ps);
      }
    } else {
      free(ps);
    }
  }

  return (ps);
}

void free_particlevector(struct particle *ps) {
  if (ps != NULL) {
    fprintf(Logfile, "\n\t\tFreeing floc ps now...");
    fflush(Logfile);
    if (ps->xi != NULL) {
      fprintf(Logfile, "\n\t\t\tFreeing floc ps->xi now... ");
      fflush(Logfile);
      free(ps->xi);
      fprintf(Logfile, "Done ");
      fflush(Logfile);
    }
    if (ps->yi != NULL) {
      fprintf(Logfile, "\n\t\t\tFreeing floc ps->yi now... ");
      fflush(Logfile);
      free(ps->yi);
      fprintf(Logfile, "Done ");
      fflush(Logfile);
    }
    if (ps->zi != NULL) {
      fprintf(Logfile, "\n\t\t\tFreeing floc ps->zi now... ");
      fflush(Logfile);
      free(ps->zi);
      fprintf(Logfile, "Done ");
      fflush(Logfile);
    }
    if (ps != NULL) {
      fprintf(Logfile, "\n\t\t\tFreeing floc ps now... ");
      fflush(Logfile);
      free(ps);
      fprintf(Logfile, "Done ");
      fflush(Logfile);
    }
  }
  ps = NULL;
  return;
}

/***
 *    particlepointervector
 *
 *    Routine to allocate memory for a 1D vector of pointers to particle
 *structures. All array indices are assumed to start with zero.
 *
 *    Arguments:    int number of elements in each dimension
 *    Returns:    Pointer to memory location of first element
 *
 *    Calls:        no other routines
 *    Called by:    main routine
 *
 ***/
struct particle **particlepointervector(int size) {
  struct particle **ps;
  size_t oneparticlesize, particlesize;

  oneparticlesize = sizeof(struct particle *);
  particlesize = size * oneparticlesize;
  ps = (struct particle **)malloc(particlesize);
  if (!ps) {
    fprintf(Logfile, "\n\nCould not allocate space for particlepointervector.");
    return (NULL);
  }

  return (ps);
}

/***
 *    free_particlepointervector
 *
 *    Routine to free the allocated memory for a 1D array of
 *    pointers to particle structures
 *
 *    All array indices are assumed to start with zero.
 *
 *    Arguments:    Pointer to memory location of first element
 *
 *     Returns:    Nothing
 *
 *    Calls:        no other routines
 *    Called by:    main routine
 *
 ***/
void free_particlepointervector(struct particle **ps) {
  int i = 0;
  for (i = 0; i < Npartc; i++) {
    if (ps[i] != NULL) {
      if (ps[i]->xi != NULL)
        free((char *)(ps[i]->xi));
      if (ps[i]->yi != NULL)
        free((char *)(ps[i]->yi));
      if (ps[i]->zi != NULL)
        free((char *)(ps[i]->zi));
    }
  }
  free((char *)(ps[0]));
  free((char *)(ps));

  return;
}

/******************************************************
 *
 * Function distrib3d.c to distribute cement clinker
 * phases in agreement with experimentally obtained
 * 2-point correlation functions for each phase.
 *
 * Particles are composed of either cement clinker or gypsum,
 * follow a user-specified size distribution, and can be
 * either flocculated, random, or dispersed.  Phase
 * distribution occurs only within the cement clinker particles
 *
 * Programmer:    Dale P. Bentz
 *                 Building and Fire Research Laboratory
 *                NIST
 *                100 Bureau Drive Mail Stop 8621
 *                Gaithersburg, MD  20899-8621   USA
 *                (301) 975-5865      FAX: (301) 990-6891
 *                E-mail: dale.bentz@nist.gov
 *
 *******************************************************/

int distrib3d(void) {
  fprintf(Logfile, "\n=== DEBUG: Entering distrib3d() ===");
  fflush(Logfile);

  /* Stack canary to detect corruption */
  const unsigned long stack_canary = 0xDEADBEEF;
  fprintf(Logfile, "\n=== DEBUG: Stack canary set to 0x%lx ===", stack_canary);
  fflush(Logfile);

  int nskip[6]; /* number of lines to skip as header in corr. files */
  register int i, j, k;
  int fileSizeInBytes = 0;
  int alumval, alum2;
  int alumdo = 1, k2so4do = 1;
  float volin, rhtest, eps, corr_res, sumarea, sumvol;
  double rdesire;
  char filecem[MAXSTRING];
  char filec3s[MAXSTRING], filesil[MAXSTRING], filealum[MAXSTRING];
  char filek2so4[MAXSTRING], filec34a[MAXSTRING];
  char filena2so4[MAXSTRING];
  char buff[MAXSTRING], instring[MAXSTRING];
  FILE *testfile;

  corr_res = 0.0;
  eps = 1.0e-5;

  /* Initialize global variables before using them */

  for (i = 0; i < MAXNUMPHASES; i++) {
    Volume[i] = 0;
    Surface[i] = 0;
  }

  for (i = 0; i < MAXSPH; i++) {
    Xsph[i] = 0;
    Ysph[i] = 0;
    Zsph[i] = 0;
  }

  /* Initialize local variables before using them */

  for (i = 0; i < 6; i++)
    nskip[i] = 0;

  fprintf(Logfile, "\n=== DEBUG: Variable initialization completed ===");
  fflush(Logfile);

  /* Set up the correlation filenames */

  fprintf(Logfile, "Enter path/root name of cement correlation files\n");
  read_string(filecem, sizeof(filecem));
  fprintf(Logfile, "%s\n", filecem);
  fflush(Logfile);

  /* Use root names to build names of correlation files */

  sprintf(filesil, "%s", filecem);
  strcat(filesil, ".sil");
  if (Verbose)
    fprintf(Logfile, "\n%s", filesil);

  sprintf(filec3s, "%s", filecem);
  strcat(filec3s, ".c3s");
  if (Verbose)
    fprintf(Logfile, "\n%s", filec3s);
  fflush(Logfile);

  sprintf(filealum, "%s", filecem);
  strcat(filealum, ".alu");
  if (Verbose)
    fprintf(Logfile, "\n%s", filealum);
  fflush(Logfile);

  sprintf(filek2so4, "%s", filecem);
  strcat(filek2so4, ".k2o");
  if (Verbose)
    fprintf(Logfile, "\n%s", filek2so4);
  fflush(Logfile);
  Verbose = 1;
  sprintf(filena2so4, "%s", filecem);
  strcat(filena2so4, ".n2o");
  if (Verbose)
    fprintf(Logfile, "\n%s", filena2so4);
  fflush(Logfile);

  /***
   *    Test to see whether we have the c3a correlation file
   *    or the c4af correlation file.  Test it by assuming the
   *    c4af file and attempting to open it.  If it does not
   *    exist, or if its size is less than 100 bytes (that is,
   *    functionally empty or corrupted) then we can assume
   *    that the c3a file is the correct one.
   ***/

  alumval = C4AF;
  sprintf(filec34a, "%s", filecem);
  strcat(filec34a, ".c4f");
  testfile = filehandler("distrib3d", filec34a, "READ_NOFAIL");
  if (!testfile) {
    /* c4af correlation kernel does not exist */
    sprintf(filec34a, "%s", filecem);
    strcat(filec34a, ".c3a");
    alumval = C3A;
  } else {
    /* testfile exists and is open; check its size */
    fseek(testfile, 0, SEEK_END);
    fileSizeInBytes = ftell(testfile);
    if (fileSizeInBytes < 100) {
      /* c4af correlation kernel exists but is empty or corrupted */
      sprintf(filec34a, "%s", filecem);
      strcat(filec34a, ".c3a");
      alumval = C3A;
    }
    fclose(testfile);
  }

  /***
   *    Attempt to read resolution of each correlation file and
   *    check them all for consistency
   ***/

  if (Verbose)
    fprintf(Logfile, "\nReading each correlation function file now... ");
  fflush(Logfile);
  for (i = 1; i <= 6; i++) {
    if (Verbose)
      fprintf(Logfile, "\n%d: ", i);
    switch (i) {
    case 1:
      strcpy(buff, filesil);
      break;
    case 2:
      strcpy(buff, filec3s);
      break;
    case 3:
      strcpy(buff, filealum);
      break;
    case 4:
      strcpy(buff, filek2so4);
      break;
    case 5:
      strcpy(buff, filena2so4);
      break;
    case 6:
      strcpy(buff, filec34a);
      break;
    }

    if (Verbose)
      fprintf(Logfile, "Trying to open file %s \n", buff);
    testfile = filehandler("distrib3d", buff, "READ_NOFAIL");
    if (!testfile) {
      if (i < 3) {
        freedistrib3d();
        bailout("distrib3d", "Could not open file");
        exit(1);
      } else if (i == 3) {
        alumdo = 0;
        fprintf(Logfile, "=== No alu file detected, set alumdo = 0 \n");
        fflush(Logfile);
      } else if (i == 4) {
        fprintf(Logfile, "=== No k2o file detected, set k2so4do = 0 \n");
        k2so4do = 0;
      }
    } else {
      fscanf(testfile, "%s", buff);
      if (!strcmp(buff, CORRRESSTRING)) {
        fscanf(testfile, "%s", instring);
        corr_res = atof(instring);
        nskip[i] = 2;
      } else {

        /***
         *    No resolution was specified.  Default the resolution
         *    to DEFAULTCORRRES to be backwards compatible with
         *    VCCTL Ver. 2.0
         ***/

        corr_res = DEFAULTCORRRES;
        nskip[i] = 0;
      }

      fclose(testfile);
    }
    if (i == 1) {

      /*** This is the first correlation file to be opened ***/

      Corr_res = corr_res;

    } else if (fabs(corr_res - Corr_res) > eps) {

      /*** Incompatible resolutions between corr files ***/

      bailout("distrib3d", "Incompatible resolutions");
      exit(1);
    }
  }
  if (Verbose)
    fprintf(Logfile, "Done.\n");

  /***
   *    Scan in the volume fractions and surface fractions
   *    of the four cement clinker phases
   *    and the two alkali sulfates when present
   ***/

  sumvol = sumarea = 0.0;
  for (i = C3S; i <= NA2SO4; i++) {
    Volf[i] = Surff[i] = 0.0;
    read_string(instring, sizeof(instring));
    volin = atof(instring);
    Volf[i] = volin;
    sumvol += volin;
    if (Verbose)
      fprintf(Logfile, "%f\n", Volf[i]);
    read_string(instring, sizeof(instring));
    volin = atof(instring);
    Surff[i] = volin;
    sumarea += volin;
    if (Verbose)
      fprintf(Logfile, "%f\n", Surff[i]);
    fflush(Logfile);
  }

  /* Normalize Volf and Surff */

  for (i = C3S; i <= NA2SO4; i++) {
    Volf[i] *= (1.0 / sumvol);
    Surff[i] *= (1.0 / sumarea);
  }

#if LIMITFILTER > 0
  Fsize = FILTERSIZE;
#else
  Fsize = (int)(((float)FILTERSIZE) * Resmag);
#endif

  Hsize_r = HISTSIZE;
  Hsize_s = HISTSIZE * (Iresmag * Iresmag * Iresmag);

  if (Fsize > (Minsyssize / 3))
    Fsize = Minsyssize / 3;

  /***
   *    Define the template radius for sintering now.
   *    It must be an odd number
   ***/

  Tradius = (int)(((float)TEMPLATE_RADIUS) * Resmag);
  if ((Tradius % 2) == 0)
    Tradius++;

  /***
   *    Allocate memory for all global variables
   ***/

  allmem();

  fprintf(Logfile, "\n=== DEBUG: Memory allocation completed ===");
  fflush(Logfile);

  /* Initialize curvature to zero */
  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {
        Curvature[i][j][k] = 0;
      }
    }
  }

  fprintf(Logfile, "\n=== DEBUG: Curvature initialization completed ===");
  fflush(Logfile);

  /***
   *    First filtering between silicates and
   *    aluminates/ferrites/alkali sulfates
   ***/

  volin = Volf[C3S] + Volf[C2S];

  /***
   *    No need to go through with this if the
   *    cement clinker is composed solely of
   *    silicate phases
   ***/

  if (Verbose)
    fprintf(Logfile, "Volin is %f", volin);

  if (volin < 1.0) {

    fprintf(Logfile, "\n=== DEBUG: About to call first rand3d() ===");
    fflush(Logfile);

    if (rand3d(C3S, alumval, filesil, nskip[1], volin, R, Filter, S, Xr)) {
      freedistrib3d();
      bailout("distrib3d", "Problem with rand3d");
      exit(1);
    }

    fprintf(Logfile, "\n=== DEBUG: First rand3d() completed successfully ===");
    fflush(Logfile);

    /* Check stack canary after first rand3d */
    if (stack_canary != 0xDEADBEEF) {
      fprintf(Logfile,
              "\n!!! STACK CORRUPTION DETECTED after first rand3d: canary = "
              "0x%lx !!!",
              stack_canary);
      fflush(Logfile);
    } else {
      fprintf(Logfile,
              "\n=== DEBUG: Stack canary still intact after first rand3d ===");
      fflush(Logfile);
    }

    if (Verbose)
      fprintf(Logfile, "\nOut of rand3d first time.");

    /***
     *    First sintering.  Arrays volume and surface are defined
     *    in stat3d
     ***/

    stat3d();
    if (Verbose)
      fprintf(Logfile, "\nOut of stat3d first time.");

    rdesire = (double)((Surff[C3S] + Surff[C2S]) *
                       (double)(Surface[C3S] + Surface[alumval]));

    /***
     *    Only perform sintering on the interface between
     *    the combined C3S/C2S domains and the combined
     *    C3A/C4AF/alkali sulfate domains if the desired hydraulic
     *    radius for the C3S/C2S domains is positive
     *    (this will almost certainly be the case every time)
     ***/

    if (Verbose)
      fprintf(Logfile, "\nRdesire is %g\n", rdesire);
    if (rdesire > 0.0) {

      /***
       *    Sinter the C3S (silicate) phase if the desired
       *    hydraulic radius for C3S is LESS than the
       *    current hydraulic radius for C3S ...
       ***/

      if ((int)rdesire < Surface[C3S]) {

        rhtest = (6.0 / 4.0) * (float)(Volume[C3S]) / rdesire;
        sinter3d(C3S, alumval, rhtest);

        /***
         *    ... Otherwise, the hydraulic radius for C3S is
         *    already less than or equal to the desired value.
         *    Therefore, treat the aluminate/ferrite/alkali sulfate  domains
         *as the solid and sinter them instead.  This effectively increases
         *the hydraulic radius of the C3S/C2S domains
         ***/

      } else {

        rdesire = (Surff[C3A] + Surff[C4AF] + Surff[K2SO4] + Surff[NA2SO4]) *
                  (float)(Surface[C3S] + Surface[alumval]);

        if (Verbose)
          fprintf(Logfile, "\nRdesire is %f\n", rdesire);
        if (rdesire > 0.0) {
          rhtest = (6.0 / 4.0) * (float)(Volume[alumval]) / rdesire;
          sinter3d(alumval, C3S, rhtest);
          if (Verbose)
            fprintf(Logfile, "\nOut of sinter3d: alumval,C3S\n");
        }
      }
    }
  }

  if (Verbose) {
    fprintf(Logfile, "\nOut of sinter3d.  Checking phase stats...");
    stat3d();
    fprintf(Logfile, "\nGetting ready to filter C2S from C3S.");
    fflush(Logfile);
  }

  /***
   *    Second filtering between C3S and C2S; defines
   *    the boundaries between C3S and C2S phases
   *    But only need to go through this if there
   *    are some silicates in the cement clinker
   ***/

  if ((Volf[C3S] + Volf[C2S]) > 0.0) {

    /***
     *    volin is fraction of silicates composed of C3S.
     *    Only need to do this if both types of silicate
     *    are present in the clinker
     ***/

    volin = Volf[C3S] / (Volf[C3S] + Volf[C2S]);

    if (Verbose)
      fprintf(Logfile, "\nVolin is %f", volin);
    fflush(Logfile);

    if (volin < 1.0 && volin > 0.0) {

      if (rand3d(C3S, C2S, filec3s, nskip[2], volin, R, Filter, S, Xr)) {
        freedistrib3d();
        bailout("distrib3d", "Problem with rand3d");
        exit(1);
      }

      /***
       *    Second sintering.  Arrays volume and surface
       *    are defined in stat3d, and need to be refreshed
       *    because of prior sintering.
       ***/

      stat3d();
      rdesire = (Surff[C3S] / (Surff[C3S] + Surff[C2S])) *
                (float)(Surface[C3S] + Surface[C2S]);

      /***
       *    Only perform sintering on the interface between
       *    the C3S and C2S domains if the desired hydraulic
       *    radius for the C3S domains is positive
       *    (this will almost certainly be the case every time)
       ***/

      if (Verbose)
        fprintf(Logfile, "\nRdesire is %f\n", rdesire);
      if (rdesire > 0.0) {

        /***
         *    Sinter the C3S phase if the desired
         *    hydraulic radius for C3S is LESS than the
         *    current hydraulic radius for C3S ...
         ***/

        if ((int)rdesire < Surface[C3S]) {

          rhtest = (6.0 / 4.0) * (float)(Volume[C3S]) / rdesire;
          sinter3d(C3S, C2S, rhtest);
          if (Verbose)
            fprintf(Logfile, "\nOut of sinter3d: C3S,C2S");

          /***
           *    ... Otherwise, the hydraulic radius for C3S is
           *    already less than or equal to the desired value.
           *    Therefore, treat the C2S domains as
           *    the solid and sinter them instead.  This effectively
           *    increases the hydraulic radius of the C3S
           *    domains
           ***/

        } else {

          rdesire = (Surff[C2S] / (Surff[C3S] + Surff[C2S])) *
                    (float)(Surface[C3S] + Surface[C2S]);

          if (Verbose)
            fprintf(Logfile, "\nRdesire is %f\n", rdesire);
          if (rdesire > 0.0) {
            rhtest = (6.0 / 4.0) * (float)(Volume[C2S]) / rdesire;
            sinter3d(C2S, C3S, rhtest);
            if (Verbose)
              fprintf(Logfile, "\nOut of sinter3d: C2S,C3S");
          }
        }
      }
    }
  }

  /***
   *    Third filtering between aluminates and alkali sulfates defines
   *    the boundaries between aluminates and alkali sulfate phases
   *    But only need to go through this if there
   *    are some alkali sulfates in the cement clinker
   ***/

  if ((alumdo == 1) && ((Volf[K2SO4] + Volf[NA2SO4]) > 0.0)) {

    /***
     *    volin is fraction of aluminates composed of C3A and C4AF.
     ***/

    volin = (Volf[C3A] + Volf[C4AF]) /
            (Volf[C3A] + Volf[C4AF] + Volf[K2SO4] + Volf[NA2SO4]);

    if (Verbose)
      fprintf(Logfile, "\nVolin is %f", volin);

    if (volin < 1.0 && volin > 0.0) {

      if (rand3d(alumval, K2SO4, filealum, nskip[3], volin, R, Filter, S, Xr)) {
        freedistrib3d();
        bailout("distrib3d", "Problem with rand3d");
        exit(1);
      }

      /***
       *    Second sintering.  Arrays volume and surface
       *    are defined in stat3d, and need to be refreshed
       *    because of prior sintering.
       ***/

      stat3d();
      rdesire = ((Surff[C3A] + Surff[C4AF]) /
                 (Surff[C3A] + Surff[C4AF] + Surff[K2SO4] + Surff[NA2SO4])) *
                (float)(Surface[alumval] + Surface[K2SO4]);

      /***
       *    Only perform sintering on the interface between
       *    the aluminate and alkali sulfate domains if the desired hydraulic
       *    radius for the aluminate domains is positive
       *    (this will almost certainly be the case every time)
       ***/

      if (Verbose)
        fprintf(Logfile, "\nRdesire is %f\n", rdesire);
      if (rdesire > 0.0) {

        /***
         *    Sinter the aluminate phases if the desired
         *    hydraulic radius for the aluminates is LESS than the
         *    current hydraulic radius for the aluminates ...
         ***/

        if ((int)rdesire < Surface[alumval]) {

          rhtest = (6.0 / 4.0) * (float)(Volume[alumval]) / rdesire;
          sinter3d(alumval, K2SO4, rhtest);
          if (Verbose)
            fprintf(Logfile, "\nOut of sinter3d: alumval,K2SO4");

          /***
           *    ... Otherwise, the hydraulic radius for aluminates is
           *    already less than or equal to the desired value.
           *    Therefore, treat the alkali sulfate domains as
           *    the solid and sinter them instead.  This effectively
           *    increases the hydraulic radius of the aluminate
           *    domains
           ***/

        } else {

          rdesire =
              ((Surff[K2SO4] + Surff[NA2SO4]) /
               (Surff[C3A] + Surff[C4AF] + Surff[K2SO4] + Surff[NA2SO4])) *
              (float)(Surface[alumval] + Surface[K2SO4]);

          if (Verbose)
            fprintf(Logfile, "\nRdesire is %f\n", rdesire);
          if (rdesire > 0.0) {
            rhtest = (6.0 / 4.0) * (float)(Volume[K2SO4]) / rdesire;
            sinter3d(K2SO4, alumval, rhtest);
            if (Verbose)
              fprintf(Logfile, "\nOut of sinter3d: K2SO4,alumval");
          }
        }
      }
    }
  }

  /***
   *    Fourth filtering to define the
   *    boundaries between K2SO4 and NA2SO4
   *    But only need to go through this if there
   *    is NA2SO4 in the cement clinker
   ***/

  if ((k2so4do == 1) && (Volf[NA2SO4] > 0.0)) {

    /* volin is fraction of K2SO4 in alkali sulfates */

    volin = Volf[K2SO4] / (Volf[K2SO4] + Volf[NA2SO4]);

    /***
     *    Only need to do this if both K2SO4 and
     *    NA2SO4 phases are in the clinker
     ***/

    if (Verbose)
      fprintf(Logfile, "\nVolin is %f", volin);
    if (volin < 1.0 && volin > 0.0) {

      if (rand3d(K2SO4, NA2SO4, filek2so4, nskip[4], volin, R, Filter, S, Xr)) {
        freedistrib3d();
        bailout("distrib3d", "Problem with rand3d");
        exit(1);
      }

      /***
       *    Fourth sintering, this time on the
       *    interface between K2SO4 and NA2SO4 domains.
       *    Arrays volume and surface are defined in stat3d,
       *    and need to be refreshed from prior sintering.
       ***/

      stat3d();
      if (Verbose)
        fprintf(Logfile, "\nOut of stat3d");
      rdesire = (Surff[K2SO4] / (Surff[K2SO4] + Surff[NA2SO4])) *
                (float)(Surface[K2SO4] + Surface[NA2SO4]);

      /***
       *    Only perform sintering on the interface between
       *    the K2SO4 and NA2SO$ domains if the desired hydraulic
       *    radius for the K2SO4 domains is positive
       *    (this will almost certainly be the case every time)
       ***/

      if (Verbose)
        fprintf(Logfile, "\nRdesire is %f\n", rdesire);
      if (rdesire > 0.0) {

        /***
         *    Sinter the K2SO4 phases if the desired
         *    hydraulic radius for the K2SO4 is LESS than the
         *    current hydraulic radius for the K2SO4 ...
         ***/

        if ((int)rdesire < Surface[K2SO4]) {

          rhtest = (6.0 / 4.0) * (float)(Volume[K2SO4]) / rdesire;
          sinter3d(K2SO4, NA2SO4, rhtest);
          if (Verbose)
            fprintf(Logfile, "\nOut of sinter3d: K2SO4,NA2SO4");

          /***
           *    ... Otherwise, the hydraulic radius for K2SO4 is
           *    already less than or equal to the desired value.
           *    Therefore, treat the NA2SO4 domains as
           *    the solid and sinter them instead.  This effectively
           *    increases the hydraulic radius of the K2SO4
           *    domains
           ***/

        } else {

          rdesire = (Surff[NA2SO4] / (Surff[K2SO4] + Surff[NA2SO4])) *
                    (float)(Surface[NA2SO4] + Surface[K2SO4]);

          if (Verbose)
            fprintf(Logfile, "\nRdesire is %f\n", rdesire);
          if (rdesire > 0.0) {
            rhtest = (6.0 / 4.0) * (float)(Volume[NA2SO4]) / rdesire;
            sinter3d(NA2SO4, K2SO4, rhtest);
            if (Verbose)
              fprintf(Logfile, "\nOut of sinter3d: NA2SO4,K2SO4");
            fflush(Logfile);
          }
        }
      }
    }
  }

  /***
   *    Fifth (final) filtering to define the
   *    boundaries between C3A and C4AF
   ***/

  /* volin is fraction of aluminates composed of phase alumval */

  volin = Volf[alumval] / (Volf[C4AF] + Volf[C3A]);
  alum2 = C3A;
  if (alumval == C3A)
    alum2 = C4AF;

  /***
   *    Only need to do this if both aluminate and
   *    ferrite phases are in the clinker
   ***/

  if (Verbose)
    fprintf(Logfile, "\nVolin is %f", volin);
  if (volin < 1.0 && volin > 0.0) {

    if (rand3d(alumval, alum2, filec34a, nskip[5], volin, R, Filter, S, Xr)) {
      freedistrib3d();
      bailout("distrib3d", "Problem with rand3d");
      exit(1);
    }

    /***
     *    Fifth (final) sintering, this time on the
     *    interface between aluminate and ferrite domains.
     *    Arrays volume and surface are defined in stat3d,
     *    and need to be refreshed from prior sintering.
     ***/

    stat3d();
    if (Verbose)
      fprintf(Logfile, "\nOut of stat3d");

    if (alumval == C4AF) {

      rdesire = (Surff[C4AF] / (Surff[C3A] + Surff[C4AF])) *
                (float)(Surface[C3A] + Surface[C4AF]);

      /***
       *    Only perform sintering on the interface between
       *    the C3A and C4AF domains if the desired hydraulic
       *    radius for the C4AF domains is positive
       *    (this will almost certainly be the case every time)
       ***/

      if (rdesire > 0.0) {

        /***
         *    Sinter the C4AF phase if the desired
         *    hydraulic radius for C4AF is LESS than the
         *    current hydraulic radius for C4AF ...
         ***/

        if ((int)rdesire < Surface[C4AF]) {

          rhtest = (6.0 / 4.0) * (float)(Volume[C4AF]) / rdesire;
          sinter3d(C4AF, C3A, rhtest);

          /***
           *    ... Otherwise, the hydraulic radius for C4AF is
           *    already less than or equal to the desired value.
           *    Therefore, treat the C3A domains as
           *    the solid and sinter them instead.  This effectively
           *    increases the hydraulic radius of the C4AF
           *    domains
           ***/

        } else {

          rdesire = (Surff[C3A] / (Surff[C3A] + Surff[C4AF])) *
                    (float)(Surface[C3A] + Surface[C4AF]);

          if (rdesire > 0.0) {
            rhtest = (6.0 / 4.0) * (float)(Volume[C3A]) / rdesire;
            sinter3d(C3A, C4AF, rhtest);
          }
        }
      }

    } else {

      /***
       *    The majority Al-containing phase is C3A instead
       *    of C4AF
       ***/

      rdesire = (Surff[C3A] / (Surff[C3A] + Surff[C4AF])) *
                (float)(Surface[C3A] + Surface[C4AF]);

      /***
       *    Only perform sintering on the interface between
       *    the C3A and C4AF domains if the desired hydraulic
       *    radius for the C3A domains is positive
       *    (this will almost certainly be the case every time)
       ***/

      if (rdesire > 0.0) {

        /***
         *    Sinter the C3A phase if the desired
         *    hydraulic radius for C3A is LESS than the
         *    current hydraulic radius for C3A ...
         ***/

        if ((int)rdesire < Surface[C3A]) {

          rhtest = (6.0 / 4.0) * (float)(Volume[C3A]) / rdesire;
          sinter3d(C3A, C4AF, rhtest);

          /***
           *    ... Otherwise, the hydraulic radius for C3A is
           *    already less than or equal to the desired value.
           *    Therefore, treat the C4AF domains as
           *    the solid and sinter them instead.  This effectively
           *    increases the hydraulic radius of the C3A
           *    domains
           ***/

        } else {

          rdesire = (Surff[C4AF] / (Surff[C3A] + Surff[C4AF])) *
                    (float)(Surface[C3A] + Surface[C4AF]);

          if (rdesire > 0.0) {
            rhtest = (6.0 / 4.0) * (float)(Volume[C4AF]) / rdesire;
            sinter3d(C4AF, C3A, rhtest);
          }
        }
      }
    }
  }

  fprintf(Logfile,
          "\nDone with distributing clinker phases.  Freeing memory now.");
  fflush(Logfile);

  /* Free up the dynamically allocated memory */

  freedistrib3d();

  fprintf(Logfile, "\n=== DEBUG: About to return from distrib3d() ===");
  fflush(Logfile);

  /* Check stack canary before return */
  if (stack_canary != 0xDEADBEEF) {
    fprintf(Logfile,
            "\n!!! STACK CORRUPTION DETECTED: canary = 0x%lx (expected "
            "0xDEADBEEF) !!!",
            stack_canary);
    fflush(Logfile);
  } else {
    fprintf(Logfile, "\n=== DEBUG: Stack canary intact, safe to return ===");
    fflush(Logfile);
  }

  /* WORKAROUND: Use longjmp instead of return to bypass corrupted return
   * address */
  fprintf(Logfile,
          "\n=== DEBUG: Using longjmp to bypass return address corruption ===");
  fflush(Logfile);

  /* Set global success flag and jump back to main */
  distrib3d_success = 1;
  longjmp(distrib3d_jmpbuf, 1);

  /* This line should never be reached */
  fprintf(stderr,
          "\n!!! ERROR line 5568: longjmp failed, trying normal return !!!");
  fflush(stderr);
  return (0);
}

/***
 *    maketemp
 *
 *    Routine to create a template for the sphere of
 *    interest of radius size to be used in
 *    curvature evaluation
 *
 *     Arguments:    int size (the radius of the sphere)
 *     Returns:    int number of pixels in sphere
 *
 *    Calls:        no other routines
 *    Called by:    runsint
 ***/
int maketemp(int size) {
  int icirc, xval, yval, zval;
  float xtmp, ytmp, dist;

  /***
   *    Determine and store the locations of all
   *    pixels in the 3-D sphere
   ***/

  icirc = 0;
  for (xval = (-size); xval <= size; xval++) {

    xtmp = (float)(xval * xval);
    for (yval = (-size); yval <= size; yval++) {

      ytmp = (float)(yval * yval);
      for (zval = (-size); zval <= size; zval++) {

        dist = sqrt(xtmp + ytmp + (float)(zval * zval));

        if (dist <= ((float)size + 0.5)) {

          Xsph[icirc] = xval;
          Ysph[icirc] = yval;
          Zsph[icirc] = zval;
          icirc++;

          if (icirc >= MAXSPH) {
            freedistrib3d();
            bailout("distrib3d", "Too many elements in template");
            exit(1);
          }
        }
      }
    }
  }

  /***
   *    Return the number of pixels contained in
   *    sphere of radius (size+0.5)
   ***/

  return (icirc);
}

/***
 *    phcount
 *
 *    Routine to count phase fractions (porosity
 *    and solids)
 *
 *     Arguments:    None
 *     Returns:    Nothing
 *
 *    Calls:        no other routines
 *    Called by:    main program
 ***/
void phcount(void) {
  int npore, nsolid[MAXNUMPHASES];
  int ix, iy, iz;

  npore = 0;
  for (ix = 1; ix < MAXNUMPHASES; ix++) {
    nsolid[ix] = 0;
  }

  /* Check all pixels in the 3-D system */

  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {

        if (Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] == 0) {
          npore++;
        } else {
          nsolid[Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)]]++;
        }
      }
    }
  }

  fprintf(Logfile, "Pores are: %d \n", npore);
  fprintf(Logfile, "Solids are: %d %d %d %d %d %d\n", nsolid[1], nsolid[2],
          nsolid[3], nsolid[4], nsolid[5], nsolid[6]);
}

/***
 *    surfpix
 *
 *    Routine to return number of surface faces
 *    exposed to porosity for pixel located at
 *    coordinates (xin,yin,zin)
 *
 *     Arguments:    int coordinates (xin,yin,zin)
 *     Returns:    number of faces exposed to porosity
 *
 *    Calls:        no other routines
 *    Called by:    rhcalc
 ***/
int surfpix(int xin, int yin, int zin) {
  int npix, ix1, iy1, iz1;

  npix = 0;

  /***
   *    Check each of the six immediate neighbors
   *    using periodic boundary conditions
   ***/

  ix1 = xin - 1;
  if (ix1 < 0)
    ix1 += Xsyssize;
  if (Cemreal.val[getInt3dindex(Cemreal, ix1, yin, zin)] == POROSITY)
    npix++;

  ix1 = xin + 1;
  if (ix1 >= Xsyssize)
    ix1 -= Xsyssize;
  if (Cemreal.val[getInt3dindex(Cemreal, ix1, yin, zin)] == POROSITY)
    npix++;

  iy1 = yin - 1;
  if (iy1 < 0)
    iy1 += Ysyssize;
  if (Cemreal.val[getInt3dindex(Cemreal, xin, iy1, zin)] == POROSITY)
    npix++;

  iy1 = yin + 1;
  if (iy1 >= Ysyssize)
    iy1 -= Ysyssize;
  if (Cemreal.val[getInt3dindex(Cemreal, xin, iy1, zin)] == POROSITY)
    npix++;

  iz1 = zin - 1;
  if (iz1 < 0)
    iz1 += Zsyssize;
  if (Cemreal.val[getInt3dindex(Cemreal, xin, yin, iz1)] == POROSITY)
    npix++;

  iz1 = zin + 1;
  if (iz1 >= Zsyssize)
    iz1 -= Zsyssize;
  if (Cemreal.val[getInt3dindex(Cemreal, xin, yin, iz1)] == POROSITY)
    npix++;

  return (npix);
}

/***
 *    rhcalc
 *
 *    Routine to return the current hydraulic radius
 *    for phase phin
 *
 *    Arguments:    Integer phase id
 *    Returns:    Float hydraulic radius
 *
 *    Calls:        surfpix
 *    Called by:    runsint
 ***/
float rhcalc(int phin) {
  int ix, iy, iz;
  int porc, surfc;
  float rhval;

  porc = surfc = 0;

  /* Check all pixels in the 3-D volume */

  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {

        if (Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] == phin) {
          porc++;
          surfc += surfpix(ix, iy, iz);
        }
      }
    }
  }

  rhval = (float)(porc * 6.0 / (4.0 * (float)surfc));
  if (Verbose) {
    fprintf(Logfile, "Phase area count is %d \n", porc);
    fprintf(Logfile, "Phase surface count is %d \n", surfc);
    fprintf(Logfile, "Hydraulic radius is %f \n", rhval);
  }

  return (rhval);
}

/***
 *    countem
 *
 *    Routine to return the count of pixels, within
 *    a spherical template, that are of phase phin
 *    or porosity (phase POROSITY)
 *
 *    Arguments:    Integer pixel coordinates and phase id
 *    Returns:    Integer count of pixels within template that
 *                    are phase phin
 *
 *    Calls:        checkbc
 *    Called by:    sysinit
 ***/
int countem(int xp, int yp, int zp, int phin) {
  int xc, yc, zc;
  int cumnum, ic;

  cumnum = 0;

  for (ic = 0; ic < Nsph; ic++) {

    xc = xp + Xsph[ic];
    yc = yp + Ysph[ic];
    zc = zp + Zsph[ic];

    /* Use periodic boundaries */

    xc += checkbc(xc, Xsyssize);
    yc += checkbc(yc, Ysyssize);
    zc += checkbc(zc, Zsyssize);

    if ((xc != xp) || (yc != yp) || (zc != zp)) {

      if ((Cemreal.val[getInt3dindex(Cemreal, xc, yc, zc)] == phin) ||
          (Cemreal.val[getInt3dindex(Cemreal, xc, yc, zc)] == POROSITY)) {

        cumnum++;
      }
    }
  }

  return (cumnum);
}

/***
 *    sysinit
 *
 *    Routine to initialize system by determining the
 *    local curvature of all phase ph1 and ph2 pixels
 *
 *    Arguments:    Phase ids of phase 1 and phase 2
 *    Returns:    Nothing
 *
 *    Calls:        countem
 *    Called by:    runsint
 *
 ***/
void sysinit(int ph1, int ph2) {
  int count, xl, yl, zl;
  char buff[MAXSTRING];

  count = 0;

  /* Process all pixels in the 3-D box */

  for (zl = 0; zl < Zsyssize; zl++) {
    for (yl = 0; yl < Ysyssize; yl++) {
      for (xl = 0; xl < Xsyssize; xl++) {

        /***
         *    Determine local curvature.  For phase 1,
         *    want to determine number of porosity
         *    pixels (phase = POROSITY) in
         *    immediate neighborhood
         ***/

        if (Cemreal.val[getInt3dindex(Cemreal, xl, yl, zl)] == ph1) {
          count = countem(xl, yl, zl, POROSITY);
        }

        /***
         *    For phase 2, want to determine number
         *    of either porosity OR phase 2 pixels in
         *    immediate neighborhood
         ***/

        if (Cemreal.val[getInt3dindex(Cemreal, xl, yl, zl)] == ph2) {
          count = countem(xl, yl, zl, ph2);
        }

        if ((count < 0) || (count >= Nsph)) {
          freedistrib3d();
          sprintf(buff, "Curvature count = %d, Nsph = %d", count, Nsph);
          bailout("distrib3d", buff);
          exit(1);
        }

        /***
         *    Case where we have a ph1 surface pixel
         *    with non-zero local curvature
         ***/

        if ((count >= 0) &&
            (Cemreal.val[getInt3dindex(Cemreal, xl, yl, zl)] == ph1)) {

          Curvature[xl][yl][zl] = count;

          /* Update solid curvature histogram */

          Nsolid[count]++;
        }

        /***
         *    Case where we have a ph2 surface pixel
         ***/

        if ((count >= 0) &&
            (Cemreal.val[getInt3dindex(Cemreal, xl, yl, zl)] == ph2)) {

          Curvature[xl][yl][zl] = count;

          /* Update air curvature histogram */

          Nair[count]++;
        }
      }
    }

    /* end of xl loop */
  }

  return;
}

/***
 *    sysscan
 *
 *    Routine to scan system and determine Nsolid (ph2)
 *    and Nair (ph1) histograms based on the values in
 *    phase and curvature arrays
 *
 *    Arguments:    Phase ids of phase 1 (solid) and
 *                    phase 2 ("air")
 *    Returns:    Nothing
 *
 *    Calls:        no other routines
 *    Called by:    runsint
 *
 ***/
void sysscan(int ph1, int ph2) {
  int xd, yd, zd, curvval;
  char buff[MAXSTRING];

  /* Scan all pixels in 3-D system */

  for (zd = 0; zd < Zsyssize; zd++) {
    for (yd = 0; yd < Ysyssize; yd++) {
      for (xd = 0; xd < Xsyssize; xd++) {

        curvval = Curvature[xd][yd][zd];

        if ((curvval < 0) || (curvval >= Nsph)) {
          sprintf(buff, "Curvature = %d, Nsph = %d", curvval, Nsph);
          freedistrib3d();
          bailout("distrib3d", buff);
          exit(1);
        }

        if (Cemreal.val[getInt3dindex(Cemreal, xd, yd, zd)] == ph2) {
          Nair[curvval]++;
        } else if (Cemreal.val[getInt3dindex(Cemreal, xd, yd, zd)] == ph1) {
          Nsolid[curvval]++;
        }
      }
    }
  }

  return;
}

/***
 *    procsol
 *
 *    Routine to return how many bins of the solid
 *    curvature histogram to use to accommodate
 *    nsearch pixels moving.  Want to use highest
 *    values first.
 *
 *    Arguments:    Int number of pixels to move
 *    Returns:    Top valfound bins of histogram to use
 *
 *    Calls:        no other routines
 *    Called by:    movepix
 *
 ***/
int procsol(int nsearch) {
  int valfound, i, stop;
  int nsofar;

  /* search histogram from top down until cumulative count */
  /* exceeds nsearch */

  if (Verbose)
    fprintf(Logfile, "\nIn procsol now...");
  valfound = Nsph - 1;
  nsofar = stop = 0;

  for (i = (Nsph - 1); ((i >= 0) && (!stop)); i--) {

    nsofar += Nsolid[i];
    if (nsofar > nsearch) {
      valfound = i;
      stop = 1;
    }
  }

  return (valfound);
}

/***
 *    procair
 *
 *    Routine to return how many bins of the "air"
 *    curvature histogram to use to accommodate
 *    nsearch pixels moving.  Want to use lowest
 *    values first.
 *
 *    Arguments:    Int number of pixels to move
 *    Returns:    Top valfound bins of histogram to use
 *
 *    Calls:        no other routines
 *    Called by:    movepix
 *
 ***/
int procair(int nsearch) {
  int valfound, i, stop;
  int nsofar;

  /* search histogram from top down until cumulative count */
  /* exceeds nsearch */

  if (Verbose)
    fprintf(Logfile, "\nIn procair now...");
  valfound = nsofar = stop = 0;

  for (i = 0; ((i < Nsph) && (!stop)); i++) {

    nsofar += Nair[i];
    if (nsofar > nsearch) {
      valfound = i;
      stop = 1;
    }
  }

  return (valfound);
}

/***
 *    movepix
 *
 *    Routine to move requested number of pixels (ntomove)
 *    from highest curvature ph1 sites to lowest curvature
 *    ph2 sites
 *
 *    Arguments:    Int phase id for phases 1 and 2
 *            Long Int number of pixels to move
 *
 *    Returns:    Int flag indicating function is done
 *                    = 1 if desired Rh achieved
 *                    = 0 if equilibrium was reached
 *                        before Rh could be reached
 *
 *    Calls:        procsol and procair
 *    Called by:    runsint
 *
 ***/
int movepix(int ntomove, int ph1, int ph2) {
  register int xp, yp, zp;
  int count1, count2, ntot, countc, i;
  int cmin, cmax, cfg, alldone;
  int nsolc, nairc, nsum, nsolm, nairm, nst1, nst2, next1, next2;
  float pck, plsol, plair;

  if (Verbose)
    fprintf(Logfile, "\nIn Movepix now...");
  alldone = 0;

  /***
   *    Determine critical bin values for removal
   *    of ph2 pixels
   ***/

  count1 = procsol(ntomove);
  nsum = cfg = 0;
  cmax = count1;

  for (i = Nsph - 1; i > count1; i--) {

    if ((Nsolid[i] > 0) && (!cfg)) {
      cfg = 1;
      cmax = i;
    }

    nsum += Nsolid[i];
  }

  /***
   *    Don't need to move all the ph1 pixels with
   *    this value of curvature, so determine
   *    movement probability for all ph1 pixels having
   *    curvature in this bin of the Nsolid histogram
   ***/

  plsol = (float)(ntomove - nsum) / (float)Nsolid[count1];
  next1 = ntomove - nsum;
  nst1 = Nsolid[count1];

  /***
   *    Determine critical bin values for removal
   *    of ph2 pixels
   ***/

  count2 = procair(ntomove);
  nsum = cfg = 0;
  cmin = count2;

  for (i = 0; i < count2; i++) {
    if ((Nair[i] > 0) && (!cfg)) {
      cfg = 1;
      cmin = i;
    }

    nsum += Nair[i];
  }

  /***
   *    Don't need to move all the ph2 pixels with
   *    this value of curvature, so determine
   *    movement probability for all ph2 pixels having
   *    curvature in this bin of the Nsolid histogram
   ***/

  plair = (float)(ntomove - nsum) / (float)Nair[count2];
  next2 = ntomove - nsum;
  nst2 = Nair[count2];

  /***
   *    Check to see if equilibrium has been reached ---
   *    if so, then no further increase in hydraulic
   *    radius is possible
   ***/

  if (cmin >= cmax) {
    alldone = 1;
    if (Verbose)
      fprintf(Logfile, "Stopping - at equilibrium \ncmin- %d  cmax- %d \n",
              cmin, cmax);
    return (alldone);
  }

  /* Initialize counters for performing sintering */

  ntot = nsolc = nairc = nsolm = nairm = 0;

  /* Now process each pixel in turn */

  for (zp = 0; zp < Zsyssize; zp++) {
    for (yp = 0; yp < Ysyssize; yp++) {
      for (xp = 0; xp < Xsyssize; xp++) {

        countc = Curvature[xp][yp][zp];

        /* Handle ph1 case first */

        if (Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] == ph1) {

          if (countc > count1) {

            /***
             *    Definitely convert from ph1 to ph2
             ***/

            Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] = ph2;

            /* Update appropriate histogram cells */

            Nsolid[countc]--;
            Nair[countc]++;
            ntot++;

            /* Store the location of the modified pixel */

          } else if (countc == count1) {

            /***
             *    Borderline curvature... move based on
             *    probability
             ***/

            nsolm++;

            /***
             *    Generate probability for pixel
             *    being removed
             ***/

            pck = ran1(Seed);
            if ((pck < 0) || (pck > 1.0))
              pck = 1.0;

            if (((pck < plsol) && (nsolc < next1)) ||
                ((nst1 - nsolm) < (next1 - nsolc))) {

              nsolc++;

              /* Convert ph1 pixel to ph2 */

              Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] = ph2;

              /* Update appropriate histogram cells */

              Nsolid[count1]--;
              Nair[count1]++;

              /* Store the location of the modified pixel */

              ntot++;
            }
          }

          /* Handle phase 2 case here */

        } else if (Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] == ph2) {

          if (countc < count2) {

            /***
             *    Definitely convert ph2 pixel to ph1
             ***/

            Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] = ph1;

            /* Update appropriate histogram cells */

            Nsolid[countc]++;
            Nair[countc]--;

            /* Store the location of the modified pixel */

            ntot++;

          } else if (countc == count2) {

            /***
             *    Borderline curvature... move based on
             *    probability
             ***/

            nairm++;

            /***
             *    Generate probability for pixel
             *    being placed
             ***/

            pck = ran1(Seed);
            if ((pck < 0) || (pck > 1.0))
              pck = 1.0;

            if (((pck < plair) && (nairc < next2)) ||
                ((nst2 - nairm) < (next2 - nairc))) {

              nairc++;

              /* Convert ph2 to ph1 */

              Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] = ph1;

              /* Update appropriate histogram cells */

              Nsolid[count2]++;
              Nair[count2]--;

              /* Store the location of the modified pixel */

              ntot++;
            }
          }
        }

      } /* end of zp loop */
    } /* end of yp loop */
  } /* end of xloop */

  if (Verbose)
    fprintf(Logfile, "ntot is %d \n", ntot);
  return (alldone);
}

/***
 *    sinter3d
 *
 *    Routine to execute user-input number of cycles
 *    of sintering algorithm
 *
 *    Arguments:    Int phase id for phases 1 and 2
 *                Float target value of hydraulic radius
 *
 *    Returns:    Nothing
 *
 *    Calls:        maketemp, rhcalc, sysinit, sysscan, and movepix
 *    Called by:    main routine
 *
 ***/
void sinter3d(int ph1id, int ph2id, float rhtarget) {
  int natonce, i, j, rflag, equilibrated;
  int curvsum1, curvsum2, pixsum1, pixsum2;
  float rhnow, avecurv1, avecurv2;

  /***
   *    Initialize the solid and air count histograms
   ***/

  for (i = 0; i < Hsize_s; i++) {
    Nsolid[i] = 0;
    Nair[i] = 0;
  }

  /* Obtain needed user input */

  natonce = MAX2MOVE * Isizemag;

  Nsph = maketemp(Tradius);

  if (Verbose) {
    fprintf(Logfile, "Nsph is %d \n", Nsph);
    fprintf(Logfile, "Checking stats for C3S...");
    stat3d();
    fflush(Logfile);
  }

  rflag = 0; /* always initialize system */
  if (!rflag) {
    if (Verbose)
      fprintf(Logfile, "Entering sysinit now...");
    sysinit(ph1id, ph2id);
    if (Verbose)
      fprintf(Logfile, "\nOut of sysinit now...");
  } else {
    sysscan(ph1id, ph2id);
  }

  i = 0;
  if (Verbose) {
    fprintf(Logfile, "Entering rhcalc now...");
    fprintf(Logfile, "Checking stats for C3S...");
    stat3d();
    fflush(Logfile);
  }

  rhnow = rhcalc(ph1id);
  if (Verbose)
    fprintf(Logfile, "\nOut of rhcalc now...\nRhnow = %f, Rhtarget = %f\n",
            rhnow, rhtarget);
  while ((rhnow < rhtarget) && (i < MAXCYC)) {

    i++;
    if (Verbose)
      fprintf(Logfile, "Now: %f  Target: %f \nCycle: %d \n", rhnow, rhtarget,
              i);
    equilibrated = movepix(natonce, ph1id, ph2id);

    if (Verbose) {
      fprintf(Logfile, "Out of movepix.");
      fprintf(Logfile, "Checking stats for C3S...");
      stat3d();
      fflush(Logfile);
    }

    /***
     *    If equilibrium is reached, then return
     *    to calling routine
     ***/

    if (equilibrated)
      return;

    curvsum1 = curvsum2 = pixsum1 = pixsum2 = 0;

    /* Determine average curvatures for phid1 and phid2 */

    for (j = 0; j <= Nsph; j++) {
      pixsum1 += Nsolid[j];
      curvsum1 += (j * Nsolid[j]);
      pixsum2 += Nair[j];
      curvsum2 += (j * Nair[j]);
    }

    avecurv1 = ((float)curvsum1) / ((float)pixsum1);
    avecurv2 = ((float)curvsum2) / ((float)pixsum2);
    if (Verbose)
      fprintf(Logfile, "Ave. solid curvature: %f \nAve. air curvature: %f \n",
              avecurv1, avecurv2);

    rhnow = rhcalc(ph1id);
    if (Verbose) {
      fprintf(Logfile, "Out of rhcalc.");
      fprintf(Logfile, "Checking stats for C3S...");
      stat3d();
      fflush(Logfile);
    }
  }

  return;
}

/***
 *    stat3d
 *
 *    Routine to compute spatial statistics on the
 *    3D microstructure
 *
 *    Arguments:    None
 *    Returns:    Nothing
 *
 *    Calls:        no other routines
 *    Called by:    main routine
 *
 ***/
void stat3d(void) {
  int valin, ix, iy, iz, ix1, iy1, iz1, k;
  int voltot, surftot;

  for (ix = POROSITY; ix <= MAXNUMPHASES - 8; ix++) {
    Volume[ix] = Surface[ix] = 0;
  }

  /* Read in image and accumulate volume totals */

  ix1 = iy1 = iz1 = 0;
  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {
        valin = Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
        Volume[valin]++;
        if (valin != POROSITY && valin != EMPTYP && valin != EMPTYDP &&
            valin != CRACKP && valin != DRIEDP) {

          /***
           *    Check six neighboring pixels
           *    for porosity
           ***/

          for (k = 1; k <= 6; k++) {

            switch (k) {
            case 1:
              ix1 = ix - 1;
              if (ix1 < 0)
                ix1 += Xsyssize;
              iy1 = iy;
              iz1 = iz;
              break;
            case 2:
              ix1 = ix + 1;
              if (ix1 >= Xsyssize)
                ix1 -= Xsyssize;
              iy1 = iy;
              iz1 = iz;
              break;
            case 3:
              iy1 = iy - 1;
              if (iy1 < 0)
                iy1 += Ysyssize;
              ix1 = ix;
              iz1 = iz;
              break;
            case 4:
              iy1 = iy + 1;
              if (iy1 >= Ysyssize)
                iy1 -= Ysyssize;
              ix1 = ix;
              iz1 = iz;
              break;
            case 5:
              iz1 = iz - 1;
              if (iz1 < 0)
                iz1 += Zsyssize;
              iy1 = iy;
              ix1 = ix;
              break;
            case 6:
              iz1 = iz + 1;
              if (iz1 >= Zsyssize)
                iz1 -= Zsyssize;
              iy1 = iy;
              ix1 = ix;
              break;
            default:
              break;
            }

            if (Cemreal.val[getInt3dindex(Cemreal, ix1, iy1, iz1)] ==
                POROSITY) {
              Surface[valin]++;
            }
          }
        }
      }
    }
  }

  if (Verbose) {
    fprintf(Logfile, "Phase    Volume      Surface     Volume    Surface \n");
    fprintf(Logfile, " ID      count        count      fraction  fraction \n");

    /* Only include clinker phases in surface area fraction calculation */

    surftot = Surface[C3S] + Surface[C2S] + Surface[C3A] + Surface[C4AF] +
              Surface[K2SO4] + Surface[NA2SO4];
    voltot = Volume[C3S] + Volume[C2S] + Volume[C3A] + Volume[C4AF] +
             Volume[K2SO4] + Volume[NA2SO4];

    fprintf(Logfile, "  %d    %8d     %8d  \n", POROSITY, Volume[POROSITY],
            Surface[POROSITY]);

    for (k = C3S; k <= NA2SO4; k++) {
      fprintf(Logfile, "  %d    %8d     %8d     %.5f   %.5f\n", k, Volume[k],
              Surface[k], (double)Volume[k] / (double)voltot,
              (double)Surface[k] / (double)surftot);
    }

    fprintf(Logfile, "Total  %8d     %8d\n\n\n", voltot, surftot);
  }

  return;
}

/***
 *    rand3d
 *
 *    Routine to generate a Gaussian random noise image and
 *    then filter it according to the 2-point correlation function
 *    for the phase of interest
 *
 *    Arguments:    Phase ID in, Phase ID out, correlation filename,
 *                int number of strings to skip (due to possible
 *                header line for resolution information),
 *                float xpt=volume fraction, r[] is the array of
 *                radius values in corr file, filter[][][] is the
 *                3D filter array, s[] is the value of the correlation
 *                function at a given (radial) position, xr[] is
 *                the float version of r[]
 *
 *    Returns:    0 if normal execution, non-zero if error occurred
 *
 *    Calls:        no other routines
 *    Called by:    main routine
 *
 ***/
int rand3d(int phasein, int phaseout, char filecorr[MAXSTRING], int nskip,
           float xpt, int *r, float ***filter, float *s, float *xr) {
  register int i, j, k, ix, iy, iz;
  int done, step, ilo, ihi;
  int valin, pvalin, r1, r2, i1, i2, i3, j1, k1;
  int ido, iii, jjj, index;
  float s2, ss, sdiff, xtmp, ytmp, slope, intercept, diff;
  float val2, t1, t2, x1, x2, u1, xrad, resmax, resmin;
  float filval, radius, sect, sumtot, vcrit;
  int xtot;
  char buff[MAXSTRING], instring[MAXSTRING];
  FILE *corrfile;

  /***
   *    Create the Gaussian noise image
   ***/

  if (Verbose)
    fprintf(Logfile, "\nEntering rand3d...\nVolin = %f", xpt);

  i1 = i2 = i3 = 0;

  for (i = 0; i < Xsyssize * Ysyssize * Zsyssize / 2; i++) {

    u1 = ran1(Seed);
    t1 = PI2 * ran1(Seed);
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

  if ((corrfile = fopen(filecorr, "r")) == NULL) {
    fprintf(stderr, "ERROR line 6595 in distrib3d, fn. rand3d:\n");
    fprintf(stderr, "\n\tCannot open correlation function file");
    fprintf(stderr, "\n\tcalled %s.  Exiting now.", filecorr);
    fflush(stderr);
    return (1);
  }

  /*** Skip over resolution information if it is given ***/

  fprintf(Logfile, "\nIn rand3d, line 6032:  filecorr = %s, nskip = %d\n",
          filecorr, nskip);

  for (i = 1; i <= nskip; i++) {
    fscanf(corrfile, "%s", buff);
  }

  fscanf(corrfile, "%s", instring);
  fprintf(Logfile, "In rand3d, line 5969:  instring = %s\n", instring);
  ido = atoi(instring);
  fprintf(Logfile, "In rand3d, line 5971:  ido = %d\n", ido);

  if (Verbose)
    fprintf(Logfile,
            "\n\tNumber of points in correlation file is %d \n\tVolin %f\n",
            ido, xpt);

  /***
   *    When reading in the correlation file, must make
   *    the resolution of the correlation function
   *    compatible with the resolution of the system
   *    as specified by global variable Res
   ***/

  fprintf(Logfile, "In rand3d, line 5982, Fsize = %d\n", Fsize);
  for (i = 0; i < ido; i++) {
    fscanf(corrfile, "%s", instring);
    fprintf(Logfile, "In rand3d, line 5985, i = %d of %d:  instring = %s\n", i,
            ido, instring);
    valin = atoi(instring);
    fprintf(Logfile, "In rand3d, line 5987:  valin = %d\n", valin);
    fscanf(corrfile, "%s", instring);
    fprintf(Logfile, "In rand3d, line 5989, i = %d of %d:  instring = %s\n", i,
            ido, instring);
    val2 = atof(instring);
    fprintf(Logfile, "In rand3d, line 5991:  val2 = %f\n", val2);

    /***
     *    valin is the radial distance in micrometers.
     *    Convert it to pixels using Res and Corr_res
     ***/

    pvalin = (int)((((float)valin) * (Corr_res / Res)) + 0.40);
    /* r[pvalin] = (int)(((float)valin)*Corr_res); */
    if (pvalin >= 2 * Fsize)
      break;
    r[pvalin] = pvalin;
    s[pvalin] = val2;
    xr[pvalin] = (float)r[pvalin];
  }

  ido = i;
  fclose(corrfile);

  /***
   *    Now linearly interpolate the other values,
   *    depending on the value of Res
   ***/

  step = (int)(Corr_res / Res);
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
  if (Verbose)
    fprintf(Logfile, "\n\tss = %f  s2 = %f  sdiff = %f", ss, s2, sdiff);
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
          fprintf(stderr, "ERROR line 6697 in distrib3d, fn. rand3d:\n");
          fprintf(stderr, "\t%d and %d, %f and ", r1, r2, s[r1]);
          fprintf(stderr, "%f with xtmp of %f\n", s[r2], xtmp);
          fflush(stderr);
          return (3);
        }

        xrad = radius - r1;

        /***
         *    Interpolate the correlation function
         *    between the two values at r2 and r1, for
         *    which it is known, to estimate its value
         *    at some r for which r1 <= r <= r2
         *
         *    We also normalize the value of filter to
         *    the value of the correlation file at 0.
         ***/

        filval = s[r1] + (s[r2] - s[r1]) * xrad;
        filter[i][j][k] = (filval - s2) / sdiff;
      }
    }
  }

  /* Now filter the image, maintaining periodic boundaries */

  if (Verbose)
    fprintf(Logfile,
            "\n\tDone loading up the convolution matrix.\n\tVolin = %f", xpt);
  resmax = 0.0;
  resmin = 1.0;

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        Rres[i][j][k] = 0.0;

        /***
         *    Only perform the filtering within regions
         *    that are candidates for this phase
         ***/

        if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == phasein) {

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

  sect = (resmax - resmin) / ((float)Hsize_r);
  if (Verbose)
    fprintf(Logfile, "\n\tDone filtering image.\n\tVolin = %f\n\tSect is %f",
            xpt, sect);

  /***
   *    Now threshold the image by creating a histogram
   *    of the values of Rres[i][j][k] and determining
   *    a cutoff bin to define the phase
   **/

  for (i = 1; i <= Hsize_r; i++) {
    Sum[i] = 0;
  }

  xtot = 0;
  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        /***
         *    Only examine within regions
         *    that are candidates for this phase
         ***/

        if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == phasein) {
          xtot++;

          /***
           *    Find the bin number for this pixel and add
           *    the pixel to the statistics
           ***/

          index = 1 + (int)((Rres[i][j][k] - resmin) / sect);

          if (index > Hsize_r)
            index = Hsize_r;
          Sum[index]++;
        }
      }
    }
  }

  sumtot = vcrit = 0.0;
  done = 0;

  if (Verbose) {
    fprintf(Logfile,
            "\n\tDone thresholding first pass.\n\tVolin = %f, xtot = %d", xpt,
            xtot);
    fprintf(Logfile, "\n\tResmin = %f  Resmax = %f", resmin, resmax);
  }

  /* Determine which bin to choose for correct thresholding */

  for (i = 1; ((i <= Hsize_r) && (!done)); i++) {

    sumtot += (float)(((double)Sum[i]) / ((double)xtot));

    if (sumtot > xpt) { /* xpt is input to the function */

      ytmp = (float)i;
      vcrit = resmin + (resmax - resmin) * (ytmp - 0.5) / ((float)Hsize_r);
      done = 1;
    }
  }

  if (Verbose)
    fprintf(Logfile, "Critical volume fraction is %f\n\tVolin = %f", vcrit,
            xpt);

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == phasein) {

          if (Rres[i][j][k] > vcrit) {
            Cemreal.val[getInt3dindex(Cemreal, i, j, k)] = phaseout;
          }
        }
      }
    }
  }

  if (Verbose)
    fprintf(Logfile, "\n\tVolin = %f", xpt);
  return (0);
}

/***
 *    addonepixels
 *
 *     Function to manage the addition of one-pixel particles
 *    to the microstructure
 *
 *     Arguments:    None
 *
 *     Returns:    Exit status (0 is okay, 1 otherwise)
 *
 *    Calls:        addrand
 *    Called by:    main program
 ***/
int addonepixels(void) {
  register int i, j, k;
  int phtodo, onepixfloc, pheach, assignpartnum, numsizes, nplaced;
  int nadd, totclinkpix, totfapix, tot[NPHASES], target[NPHASES];
  int nleft, tottarget, numeach;
  float sizeeach;

  /***
   * One-pixel particles are assigned a particle number of zero
   ***/
  /* assignpartnum = 0; */

  /***
   * One-pixel particles are assigned a unique particle number
   ***/
  assignpartnum = 1;

  i = j = 1;

  /***
   *    Allow user to iteratively add one-pixel
   *    particles of various phases.  Typical application
   *    would be for addition of silica fume
   ***/

  for (phtodo = 0; phtodo < NPHASES; phtodo++) {

    /*
   fprintf(Logfile,"Should these particles flocculate to surfaces? No (0) or
   Yes (1):
    "); read_string(instring,sizeof(instring)); onepixfloc = atoi(instring);
    */
    onepixfloc = 0;

    nadd = Onepixnum[phtodo];
    fprintf(Logfile, "\nAdding %d of phase %d", nadd, phtodo);

    if (nadd > 0) {

      switch (phtodo) {
      case C3S:

        /****
         * Get total number of clinker pixels
         ****/
        totclinkpix = 0;
        for (i = 0; i < NPHASES; i++) {
          tot[i] = 0;
          target[i] = 0;
        }

        for (k = 0; k < Zsyssize; k++) {
          for (j = 0; j < Ysyssize; j++) {
            for (i = 0; i < Xsyssize; i++) {
              if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == C3S) {
                totclinkpix++;
                tot[C3S]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == C2S) {
                totclinkpix++;
                tot[C2S]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == C3A) {
                totclinkpix++;
                tot[C3A]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == C4AF) {
                totclinkpix++;
                tot[C4AF]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] ==
                         K2SO4) {
                totclinkpix++;
                tot[K2SO4]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] ==
                         NA2SO4) {
                totclinkpix++;
                tot[NA2SO4]++;
              }
            }
          }
        }

        /***
         * After adding one-pixel particles, there will
         * be this many cement pixels
         ***/

        totclinkpix += nadd;
        nleft = nadd;
        tottarget = 0;
        for (i = C3S; i <= NA2SO4; i++) {
          target[i] = (Volf[i] * nadd) + 0.5;
          /*
          target[i] = (int)((Volf[i]*(float)totclinkpix)
                         - (float)tot[i] + 0.5);
                         */
          if (target[i] < 0)
            target[i] = 0;
          tottarget += target[i];
        }

        /***
         * Normalize the targets
         ***/

        /*
        for (i = C3S; (i <= NA2SO4); i++) {

            target[i] = (int)(0.5 +
        ((float)(target[i]*nadd)/(float)tottarget));
        }

        tottarget = 0;
        for (i = C3S; (i <= NA2SO4); i++) {
            tottarget += target[i];
        }
        */

        for (i = C3S; (i <= NA2SO4) && (nleft > 0); i++) {

          if (Verbose) {
            fprintf(Logfile, "\t%d pixels of ", target[i]);
            switch (i) {
            case C3S:
              fprintf(Logfile, "C3S\n");
              break;
            case C2S:
              fprintf(Logfile, "C2S\n");
              break;
            case C3A:
              fprintf(Logfile, "C3A\n");
              break;
            case C4AF:
              fprintf(Logfile, "C4AF\n");
              break;
            case K2SO4:
              fprintf(Logfile, "K2SO4\n");
              break;
            case NA2SO4:
              fprintf(Logfile, "NA2SO4\n");
              break;
            default:
              fprintf(Logfile, "unrecognized phase\n");
              break;
            }
          }

          if (Dispdist == 1) {
            numeach = target[i];
            pheach = i;
            nplaced = genonevoxparticles(numeach, pheach);
            if (nplaced < numeach) {
              numeach -= (nplaced);
              fprintf(Logfile,
                      "\nCould not add all one-pixel particles dispersed.");
              fprintf(Logfile,
                      "\nAdding %d extra random locations to make up...",
                      numeach);
              addrand(i, numeach, onepixfloc, assignpartnum);
            }
          } else {
            addrand(i, target[i], onepixfloc, assignpartnum);
          }
        }

        break;

      case FLYASH:

        /****
         * Get total number of fly ash particles
         ****/

        totfapix = 0;
        for (i = 0; i < NPHASES; i++) {
          tot[i] = 0;
          target[i] = 0;
        }

        for (k = 0; k < Zsyssize; k++) {
          for (j = 0; j < Ysyssize; j++) {
            for (i = 0; i < Xsyssize; i++) {
              if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == ASG) {
                totfapix++;
                tot[ASG]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == CAS2) {
                totfapix++;
                tot[CAS2]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] ==
                         FAC3A) {
                totfapix++;
                tot[FAC3A]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] ==
                         CACL2) {
                totfapix++;
                tot[CACL2]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] ==
                         AMSIL) {
                totfapix++;
                tot[AMSIL]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] ==
                         ANHYDRITE) {
                totfapix++;
                tot[ANHYDRITE]++;
              }
            }
          }
        }

        /***
         * After adding one-pixel particles, there will
         * be this many fly ash one-pixel particles
         ***/

        totfapix += nadd;
        nleft = nadd;
        tottarget = 0;
        for (i = 0; i < 6; i++) {
          switch (i) {
          case 0:
            j = ASG;
            break;
          case 1:
            j = CAS2;
            break;
          case 2:
            j = FAC3A;
            break;
          case 3:
            j = CACL2;
            break;
          case 4:
            j = AMSIL;
            break;
          case 5:
            j = ANHYDRITE;
            break;
          default:
            break;
          }
          target[j] = (int)((Volf[j] * (float)totfapix) - (float)tot[j] + 0.5);
          tottarget += target[j];
        }

        /***
         * Normalize the targets
         ***/

        for (i = 0; i < 6; i++) {
          switch (i) {
          case 0:
            j = ASG;
            break;
          case 1:
            j = CAS2;
            break;
          case 2:
            j = FAC3A;
            break;
          case 3:
            j = CACL2;
            break;
          case 4:
            j = AMSIL;
            break;
          case 5:
            j = ANHYDRITE;
            break;
          default:
            break;
          }

          target[j] =
              (int)(0.5 + ((float)(target[j] * nadd) / (float)tottarget));
        }

        tottarget = 0;
        for (i = 0; i < 6; i++) {
          switch (i) {
          case 0:
            j = ASG;
            break;
          case 1:
            j = CAS2;
            break;
          case 2:
            j = FAC3A;
            break;
          case 3:
            j = CACL2;
            break;
          case 4:
            j = AMSIL;
            break;
          case 5:
            j = ANHYDRITE;
            break;
          default:
            break;
          }

          tottarget += target[j];
        }

        if (Verbose)
          fprintf(Logfile, "\nAdding %d fly ash pixels now...\n", tottarget);
        for (i = 0; (i < 6) && (nleft > 0); i++) {

          if (Verbose)
            fprintf(Logfile, "\t%d pixels of ", target[i]);
          switch (i) {
          case 0:
            if (Verbose)
              fprintf(Logfile, "ASG\n");
            j = ASG;
            break;
          case 1:
            if (Verbose)
              fprintf(Logfile, "CAS2\n");
            j = CAS2;
            break;
          case 2:
            if (Verbose)
              fprintf(Logfile, "FAC3A\n");
            j = FAC3A;
            break;
          case 3:
            if (Verbose)
              fprintf(Logfile, "CACL2\n");
            j = CACL2;
            break;
          case 4:
            if (Verbose)
              fprintf(Logfile, "AMSIL\n");
            j = AMSIL;
            break;
          case 5:
            if (Verbose)
              fprintf(Logfile, "ANHYDRITE\n");
            j = ANHYDRITE;
            break;
          default:
            break;
          }

          if (Dispdist == 1) {
            numeach = target[j];
            pheach = j;
            nplaced = genonevoxparticles(numeach, pheach);
            if (nplaced < numeach) {
              numeach -= (nplaced);
              fprintf(Logfile,
                      "\nCould not add all one-pixel particles dispersed.");
              fprintf(Logfile,
                      "\nAdding %d extra random locations to make up...",
                      numeach);
              addrand(j, numeach, onepixfloc, assignpartnum);
            }
          } else {
            addrand(j, target[j], onepixfloc, assignpartnum);
          }
        }

        break;

      default:
        if (Dispdist == 1) {
          numeach = nadd;
          pheach = phtodo;
          nplaced = genonevoxparticles(numeach, pheach);
          if (nplaced < numeach) {
            numeach -= (nplaced);
            fprintf(Logfile,
                    "\nCould not add all one-pixel particles dispersed.");
            fprintf(Logfile, "\nAdding %d extra random locations to make up...",
                    numeach);
            addrand(phtodo, numeach, 0, assignpartnum);
          }
        } else {
          addrand(phtodo, nadd, 0, assignpartnum);
        }
        break;
      }
    }
  }

  return (0);
}

/***
 *    addrand
 *
 *     Add nneed one-pixel elements of phase randid at random
 *     locations in the microstructure
 *
 *     Arguments:    int phase id
 *                 int number to place
 *                 int flocculate (1) or not (0)
 *                 int whether or not to assign a particle number
 *
 *     Returns:    nothing
 *
 *    Calls:        no other routines
 *    Called by:    main program
 ***/
void addrand(int randid, int nneed, int onepixfloc, int assignpartnum) {
  int inc, ic, success, ix, iy, iz, dim, dir, newsite, oldval;

  /***
   *    Add number of requested phase pixels at
   *    random pore locations
   ***/

  for (ic = 1; ic <= nneed; ic++) {
    success = 0;

    while (!success) {

      ix = (int)((float)Xsyssize * ran1(Seed));
      iy = (int)((float)Ysyssize * ran1(Seed));
      iz = (int)((float)Zsyssize * ran1(Seed));

      if (ix == Xsyssize)
        ix = 0;
      if (iy == Ysyssize)
        iy = 0;
      if (iz == Zsyssize)
        iz = 0;

      if (Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] == POROSITY ||
          Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] == CRACKP) {
        oldval = Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
        Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] = randid;
        if (assignpartnum) {
          Npart++;
          Cement.val[getInt3dindex(Cement, ix, iy, iz)] = Npart;
        }
        success = 1;
        if (onepixfloc == 1) {
          /***
           * Flocculate this particle to a nearby surface
           * Pic a random direction to fly
           ***/
          dim = (int)(3.0 * ran1(Seed));
          dir = (int)(2.0 * ran1(Seed));
          inc = (dir == 0) ? 1 : -1;

          switch (dim) {
          case 0: /* X-direction flight */
            newsite = ix + inc;
            newsite += checkbc(newsite, Xsyssize);
            while ((newsite != ix) &&
                   ((Cemreal.val[getInt3dindex(Cemreal, newsite, iy, iz)] ==
                     POROSITY) ||
                    (Cemreal.val[getInt3dindex(Cemreal, newsite, iy, iz)] ==
                     CRACKP))) {
              newsite += inc;
              newsite += checkbc(newsite, Xsyssize);
            }
            if (newsite != ix) {
              newsite -= inc;
              newsite += checkbc(newsite, Xsyssize);
              Cemreal.val[getInt3dindex(Cemreal, newsite, iy, iz)] =
                  Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
              Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] = oldval;
              if (assignpartnum) {
                Cement.val[getInt3dindex(Cement, newsite, iy, iz)] =
                    Cement.val[getInt3dindex(Cement, ix, iy, iz)];
                Cement.val[getInt3dindex(Cement, ix, iy, iz)] = 0;
              }
            }
            break;
          case 1: /* Y-direction flight */
            newsite = iy + inc;
            newsite += checkbc(newsite, Ysyssize);
            while ((newsite != iy) &&
                   ((Cemreal.val[getInt3dindex(Cemreal, ix, newsite, iz)] ==
                     POROSITY) ||
                    (Cemreal.val[getInt3dindex(Cemreal, ix, newsite, iz)] ==
                     CRACKP))) {
              newsite += inc;
              newsite += checkbc(newsite, Ysyssize);
            }
            if (newsite != iy) {
              newsite -= inc;
              newsite += checkbc(newsite, Ysyssize);
              Cemreal.val[getInt3dindex(Cemreal, ix, newsite, iz)] =
                  Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
              Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] = oldval;
              if (assignpartnum) {
                Cement.val[getInt3dindex(Cement, ix, newsite, iz)] =
                    Cement.val[getInt3dindex(Cement, ix, iy, iz)];
                Cement.val[getInt3dindex(Cement, ix, iy, iz)] = 0;
              }
            }
            break;
          case 2: /* Z-direction flight */
            newsite = iz + inc;
            newsite += checkbc(newsite, Zsyssize);
            while ((newsite != iz) &&
                   ((Cemreal.val[getInt3dindex(Cemreal, ix, iy, newsite)] ==
                     POROSITY) ||
                    (Cemreal.val[getInt3dindex(Cemreal, ix, iy, newsite)] ==
                     CRACKP))) {
              newsite += inc;
              newsite += checkbc(newsite, Zsyssize);
            }
            if (newsite != iz) {
              newsite -= inc;
              newsite += checkbc(newsite, Zsyssize);
              Cemreal.val[getInt3dindex(Cemreal, ix, iy, newsite)] =
                  Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
              Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] = oldval;
              if (assignpartnum) {
                Cement.val[getInt3dindex(Cement, ix, iy, newsite)] =
                    Cement.val[getInt3dindex(Cement, ix, iy, iz)];
                Cement.val[getInt3dindex(Cement, ix, iy, iz)] = 0;
              }
            }
            break;
          case 3: /* Do nothing */
            break;
          }
        }
      }
    }
  }
  return;
}

/***
 *    freegenmic
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
void freegenmic(void) {
  register int i;

  if (Cement.val)
    free_Int3darray(&Cement);

  if (Cemreal.val)
    free_Int3darray(&Cemreal);

  if (Bbox.val)
    free_Int3darray(&Bbox);

  if (Particle)
    free_particlepointervector(Particle);

  for (i = 0; i < NSPHASES; i++) {
    if (Verbose) {
      if (Phase_shape[i].xg) {
        fprintf(Logfile, "\nFreeing Phase_shape[%d].xg vector...", i);
      } else {
        fprintf(Logfile, "\nPhase_shape[%d].xg vector is freed already", i);
      }
      fflush(Logfile);
    }
    if (Phase_shape[i].xg)
      free_fvector(Phase_shape[i].xg);

    if (Verbose) {
      if (Phase_shape[i].wg) {
        fprintf(Logfile, "\nFreeing Phase_shape[%d].wg vector...", i);
      } else {
        fprintf(Logfile, "\nPhase_shape[%d].wg vector is freed already", i);
      }
      fflush(Logfile);
    }
    if (Phase_shape[i].wg)
      free_fvector(Phase_shape[i].wg);
  }

  if (Verbose) {
    if (Y) {
      fprintf(Logfile, "\nFreeing Y complexmatrix...");
    } else {
      fprintf(Logfile, "\nY complexmatrix is freed already");
    }
    fflush(Logfile);
  }
  if (Y)
    free_complexmatrix(Y, 0, Nnn, -Nnn, Nnn);

  if (Verbose) {
    if (A) {
      fprintf(Logfile, "\nFreeing A complexmatrix...");
    } else {
      fprintf(Logfile, "\nA complexmatrix is freed already");
    }
    fflush(Logfile);
  }
  if (A)
    free_complexmatrix(A, 0, Nnn, -Nnn, Nnn);

  if (Verbose) {
    fprintf(Logfile, "\nDone freeing all the memory I know about");
    fflush(Logfile);
  }

  return;
}

/***
 *    freedistrib3d
 *
 *    Releases all dynamically allocated memory for the
 *    distrib3d function
 *
 *    SHOULD ONLY BE CALLED IF ALL MEMORY HAS ALREADY BEEN
 *    DYNAMICALLY ALLOCATED
 *
 *    Arguments:    None
 *    Returns:    Nothing
 *
 *    Calls:        free_ivector, free_fvector, free_fcube
 *    Called by:    distrib3d
 *
 ***/
void freedistrib3d(void) {
  if (R)
    free_ivector(R);
  if (S)
    free_fvector(S);
  if (Xr)
    free_fvector(Xr);
  if (Filter)
    free_fcube(Filter, Fsize + 1);
  if (Nsolid)
    free_ivector(Nsolid);
  if (Nair)
    free_ivector(Nair);
  if (Curvature)
    free_usibox(Curvature, Xsyssize + 1, Ysyssize + 1);
  if (Sum)
    free_ivector(Sum);
  if (Normm)
    free_fbox(Normm, Xsyssize + 1, Ysyssize + 1);
  if (Rres)
    free_fbox(Rres, Xsyssize + 1, Ysyssize + 1);

  return;
}

/***
 *    allmem
 *
 *    Attempts to dynamically allocate memory for this
 *    program.
 *
 *    Arguments:    None
 *    Returns:    Nothing
 *
 *    Calls:        ivector, fvector, fcube
 *    Called by:    main
 *
 ***/
void allmem(void) {

  R = NULL;
  S = NULL;
  Xr = NULL;
  Filter = NULL;
  Nsolid = NULL;
  Nair = NULL;
  Curvature = NULL;
  Sum = NULL;
  Normm = NULL;
  Rres = NULL;

  R = ivector(2 * Fsize);
  S = fvector(2 * Fsize);
  Xr = fvector(2 * Fsize);
  Filter = fcube(Fsize + 1);
  Nsolid = ivector(Hsize_s);
  Nair = ivector(Hsize_s);
  Curvature = usibox(Xsyssize + 1, Ysyssize + 1, Zsyssize + 1);
  Sum = ivector(Hsize_r + 2);
  Normm = fbox(Xsyssize + 1, Ysyssize + 1, Zsyssize + 1);
  Rres = fbox(Xsyssize + 1, Ysyssize + 1, Zsyssize + 1);

  if (!R || !S || !Xr || !Filter || !Nsolid || !Nair || !Curvature || !Sum ||
      !Normm || !Rres) {

    freedistrib3d();
    bailout("distrib3d", "Memory allocation failure");
    fflush(stdout);
    exit(1);
  }

  return;
}

/******************************************************
 *
 * Function distfa to distribute fly ash phases
 * randomly amongst monophase particles or on
 * a pixel basis.  This is a combination of the
 * standalone programs distfapart and distfarand,
 * originally programmed by Dale Bentz (May 1997)
 *
 *******************************************************/
int distfa(int fadchoice) {
  int *phase, *partid;
  int ix, iy, iz, valin, valout, partin;
  int count, c1, phnew, mult;
  int totcnt, ascnt, cacl2cnt, amsilcnt, inertcnt;
  int anhcnt, cas2cnt, c3acnt;
  int markc3a, markas, markcacl2, markamsil, markinert, markanh, markcas2;
  float probasg, probcacl2, probsio2;
  float probc3a, prph, probcas2, probanh;
  char instring[MAXSTRING];

  totcnt = 0;
  cas2cnt = anhcnt = c3acnt = ascnt = cacl2cnt = amsilcnt = inertcnt = 0;
  mult = 0;
  partid = NULL;
  phase = NULL;

  if (fadchoice == 0) {

    /***
     *    This block prepares for distributing among
     *    monophase particles.  Not needed if distributing
     *    randomly pixel by pixel
     ***/

    phase = NULL;
    partid = NULL;
    mult = 1;

    /***
     *    Initial allocation of memory for phase
     *    and partid arrays
     ***/

    phase = (int *)calloc((size_t)Npartc, sizeof(int));
    if (!phase) {
      bailout("distfapart", "Could not allocate memory for phase");
      exit(1);
    }

    partid = (int *)calloc((size_t)Npartc, sizeof(int));
    if (!partid) {
      free(phase);
      bailout("distfapart", "Could not allocate memory for partid");
      exit(1);
    }

    ascnt = cacl2cnt = amsilcnt = inertcnt = 0;
    cas2cnt = anhcnt = c3acnt = 0;

    /* Determine total number of fly ash pixels in image */
    totcnt = 0;
    for (iz = 0; iz < Zsyssize; iz++) {
      for (iy = 0; iy < Ysyssize; iy++) {
        for (ix = 0; ix < Xsyssize; ix++) {
          if (Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] == FLYASH)
            totcnt++;
        }
      }
    }
  }

  /* Get user input for phase probabilities (volume fractions)     */
  /* This is needed whether distributing among monophase particles */
  /*     or randomly on a pixel by pixel basis                     */

  fprintf(Logfile,
          "Enter probability for fly ash to be aluminosilicate glass \n");
  read_string(instring, sizeof(instring));
  probasg = atof(instring);
  fprintf(Logfile, "%f\n", probasg);
  Volf[ASG] = probasg;
  fprintf(Logfile,
          "Enter probability for fly ash to be calcium aluminodisilicate \n");
  read_string(instring, sizeof(instring));
  probcas2 = atof(instring);
  fprintf(Logfile, "%f\n", probcas2);
  Volf[CAS2] = probcas2;
  fprintf(Logfile,
          "Enter probability for fly ash to be tricalcium aluminate \n");
  read_string(instring, sizeof(instring));
  probc3a = atof(instring);
  fprintf(Logfile, "%f\n", probc3a);
  Volf[FAC3A] = probc3a;
  fprintf(Logfile, "Enter probability for fly ash to be calcium chloride \n");
  read_string(instring, sizeof(instring));
  probcacl2 = atof(instring);
  fprintf(Logfile, "%f\n", probcacl2);
  Volf[CACL2] = probcacl2;
  fprintf(Logfile, "Enter probability for fly ash to be silica \n");
  read_string(instring, sizeof(instring));
  probsio2 = atof(instring);
  fprintf(Logfile, "%f\n", probsio2);
  Volf[AMSIL] = probsio2;
  fprintf(Logfile, "Enter probability for fly ash to be anhydrite \n");
  read_string(instring, sizeof(instring));
  probanh = atof(instring);
  fprintf(Logfile, "%f\n", probanh);
  Volf[ANHYDRITE] = probanh;

  /* Determine goal counts for each phase */

  markas = probasg * (float)totcnt;
  markamsil = probsio2 * (float)totcnt;
  markcacl2 = probcacl2 * (float)totcnt;
  markanh = probanh * (float)totcnt;
  markcas2 = probcas2 * (float)totcnt;
  markc3a = probc3a * (float)totcnt;
  markinert =
      (1.0 - probasg - probsio2 - probcacl2 - probanh - probcas2 - probc3a) *
      (float)totcnt;

  /***
   *    Convert probabilities to cumulative
   *
   *    Order must be the same as in for loop below
   ***/

  probcacl2 += probasg;
  probsio2 += probcacl2;
  probanh += probsio2;
  probcas2 += probanh;
  probc3a += probcas2;

  if (fadchoice == 0) {
    for (ix = 0; ix < Npartc; ix++) {
      phase[ix] = partid[ix] = 0;
    }

    count = 0;

    /* First scan-- find each particle and assign phases */

    for (iz = 0; iz < Zsyssize; iz++) {
      for (iy = 0; iy < Ysyssize; iy++) {
        for (ix = 0; ix < Xsyssize; ix++) {

          valin = Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
          partin = Cement.val[getInt3dindex(Cement, ix, iy, iz)];

          if ((valin == FLYASH) && (partid[partin] == 0)) {

            count++;

            /* Check if we have run out of allocated memory */

            if (count >= mult * Npartc) {
              mult++;
              partid = (int *)realloc((int *)partid, (size_t)(mult * Npartc));
              if (!partid) {
                free(phase);
                bailout("distfa", "Could not reallocate partid");
                exit(1);
              }

              phase = (int *)realloc((int *)phase, (size_t)(mult * Npartc));
              if (!phase) {
                free(partid);
                bailout("distfapart", "Could not reallocate partid");
                exit(1);
              }
            }

            partid[partin] = count;

            valout = INERT;
            do {
              prph = ran1(Seed);

              if ((prph < probasg) && (ascnt < markas)) {

                valout = ASG;

              } else if ((prph < probcacl2) && (cacl2cnt < markcacl2)) {

                valout = CACL2;

              } else if ((prph < probsio2) && (amsilcnt < markamsil)) {

                valout = AMSIL;

              } else if ((prph < probanh) && (anhcnt < markanh)) {

                valout = ANHYDRITE;

              } else if ((prph < probcas2) && (cas2cnt < markcas2)) {

                valout = CAS2;

              } else if ((prph < probc3a) && (c3acnt < markc3a)) {

                valout = FAC3A;
              }
            } while ((valout == INERT) && (inertcnt > markinert));

            phase[count] = valout;
          }

          if (valin == FLYASH) {

            c1 = partid[partin];
            phnew = phase[c1];

            switch (phnew) {
            case ASG:
              ascnt++;
              break;
            case CACL2:
              cacl2cnt++;
              break;
            case AMSIL:
              amsilcnt++;
              break;
            case ANHYDRITE:
              anhcnt++;
              break;
            case CAS2:
              cas2cnt++;
              break;
            case C3A:
              c3acnt++;
              break;
            case INERT:
              inertcnt++;
              break;
            default:
              break;
            }
          }

        } /* End of iz loop */
      } /* End of iy loop */
    } /* End of ix loop */
  }

  /* Above scan is needed only if distributing among */
  /* monophase particles.  The scane below is needed */
  /* either way                                      */

  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {

        partin = Cement.val[getInt3dindex(Cement, ix, iy, iz)];
        valin = Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];

        if (valin == FLYASH) {
          if (fadchoice == 0) {
            count = partid[partin];
            Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] = phase[count];
          } else {
            valout = INERT;
            prph = ran1(Seed);
            if (prph < probasg) {

              valout = ASG;

            } else if (prph < probcacl2) {

              valout = CACL2;

            } else if (prph < probsio2) {

              valout = AMSIL;

            } else if (prph < probanh) {

              valout = ANHYDRITE;

            } else if (prph < probcas2) {

              valout = CAS2;

            } else if (prph < probc3a) {

              valout = FAC3A;
            }

            Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] = valout;
          }
        }
      }
    }
  }

  if (fadchoice == 0) {
    free(partid);
    free(phase);
  }
  return (0);
  /* GODZILLA */
}

char *rfc8601_timespec(struct timespec *tv) {
  char time_str[127];
  double fractional_seconds;
  int milliseconds;
  struct tm tm; // our "broken down time"
  char *rfc8601;

  rfc8601 = malloc(256);

  memset(&tm, 0, sizeof(struct tm));
  sprintf(time_str, "%ld UTC", tv->tv_sec);

  // convert our timespec into broken down time
  strptime(time_str, "%s %U", &tm);

  // do the math to convert nanoseconds to integer milliseconds
  fractional_seconds = (double)tv->tv_nsec;
  fractional_seconds /= 1e6;
  fractional_seconds = round(fractional_seconds);
  milliseconds = (int)fractional_seconds;

  // print date and time without milliseconds
  strftime(time_str, sizeof(time_str), "%Y-%m-%dT%H:%M:%S", &tm);

  // add on the fractional seconds and Z for the UTC Timezone
  sprintf(rfc8601, "%s.%dZ", time_str, milliseconds);

  return rfc8601;
}
/***
 *    create
 *
 *    Routine to obtain user input and create a starting
 *    microstructure.
 *
 *     Arguments:    Nothing
 *
 *    Calls:        genparticles
 *    Called by:    main program
 ***/
void create(void) {
  int i, j, k, numsize, phase[NUMSIZES], phase_id, num_phases_to_add, nplaced;
  int num[NUMSIZES], target_phase_vox;
  int extra_pixels, target_vox_i, linval;
  int delta_particles, total_phase_vox;
  int ip, inval, shapevar;
  int numparts[NPHASES][NUMSIZES];
  float frad[NUMSIZES], tval, val1, val2, binder_vfrac, water_vfrac;
  float diam[NUMSIZES];
  float *xgvec, *wgvec;
  char buff[MAXSTRING], buff1[MAXSTRING], gaussname[MAXSTRING];
  char buff2[MAXSTRING], buff3[MAXSTRING], instring[MAXSTRING];
  FILE *fgauss;

  /* initialize local arrays */

  xgvec = NULL;
  wgvec = NULL;
  fgauss = NULL;

  for (i = 0; i < NUMSIZES; i++) {
    num[i] = 0;
    phase[i] = 0;
    diam[i] = 0.0;
    frad[i] = 0.0;
  }

  for (i = 0; i < NPHASES; i++) {
    for (j = 0; j < NUMSIZES; j++) {
      numparts[i][j] = 0;
    }
  }

  Minsyssize = Xsyssize;
  if (Ysyssize < Minsyssize)
    Minsyssize = Ysyssize;
  if (Zsyssize < Minsyssize)
    Minsyssize = Zsyssize;

  fprintf(Logfile,
          "Add all SPHERES (0), all REAL-SHAPE (1), or MIXED (2)  particles? ");
  read_string(instring, sizeof(instring));
  Shape = atoi(instring);
  fprintf(Logfile, "%d\n", Shape);

  /***
   *       We must zero all the shapetype values (assume all are spheres).  We
   *       must do this because a test is made on these values whether or not
   *       the structure is mixed
   ***/

  for (i = 0; i < NSPHASES; i++) {
    Phase_shape[i].shapetype = 0;
    Phase_shape[i].ntheta = 0;
    Phase_shape[i].nphi = 0;
    Onepixnum[i] = 0;
  }

  /***
   *    Comment out this next block if/when we enable users
   *    to specify a different shape set for each phase
   ***/

  if (Shape != SPHERES) {

    /* At least some particles will have non-spherical shapes */

    fprintf(Logfile, "Where is the default shape database directory? ");
    fprintf(Logfile, "\n(Include final separator in path) ");
    read_string(buff, sizeof(buff));
    Filesep = buff[strlen(buff) - 1];
    if (Filesep != '/' && Filesep != '\\') {
      fprintf(Logfile, "\nNo final file separator detected.  Using /");
      Filesep = '/';
    }
    fprintf(Logfile, "%s\n", buff);
    sprintf(Pathroot, "%s", buff);
    fprintf(Logfile,
            "Take cement shapes from what data set in this directory? ");
    fprintf(Logfile, "\n(No file separator at beginning or end)");
    read_string(Shapeset, sizeof(Shapeset));
    fprintf(Logfile, "%s\n", Shapeset);
    if ((Shapeset[strlen(Shapeset) - 1] == '/') ||
        (Shapeset[strlen(Shapeset) - 1] == '\\')) {
      Shapeset[strlen(Shapeset) - 1] = '\0';
    }

    /***
     *    At least some particles will be real shape
     *    Allocate memory for the spherical harmonic arrays and
     *    for the Bbox array (only needed for real shapes)
     ***/

    A = complexmatrix(0, Nnn, -Nnn, Nnn);
    AA = complexmatrix(0, Nnn, -Nnn, Nnn);
    Y = complexmatrix(0, Nnn, -Nnn, Nnn);
    Int3darray(&Bbox, BoxXsize, BoxYsize, BoxZsize);

    if (!A || !Y || (Bbox.val == NULL)) {
      freegenmic();
      bailout("genmic", "Memory allocation error");
      fflush(stdout);
      exit(1);
    }

    /* Determine number of Gaussian quadrature points from file */

    sprintf(gaussname, "%s%s%cgauss120.dat", Pathroot, Shapeset, Filesep);
    fgauss = filehandler("genmic", gaussname, "READ");
    if (!fgauss) {
      freegenmic();
      exit(1);
    }

    Nphi = Ntheta = 0;
    while (!feof(fgauss)) {
      fscanf(fgauss, "%f %f", &val1, &val2);
      if (!feof(fgauss)) {
        Ntheta++;
      }
    }

    Nphi = Ntheta;

    fclose(fgauss);

    /* Allocate memory for Gaussian quadrature points */

    xgvec = fvector(Ntheta + 1);
    if (!xgvec) {
      freegenmic();
      bailout("genmic", "Could not allocate memory for xgvec");
      exit(1);
    }
    wgvec = fvector(Nphi + 1);
    if (!wgvec) {
      freegenmic();
      bailout("genmic", "Could not allocate memory for wgvec");
      exit(1);
    }

    /* Read Gaussian quadrature points from file */

    fgauss = filehandler("genmic", gaussname, "READ");
    if (!fgauss) {
      freegenmic();
      exit(1);
    }

    for (i = 1; i <= Ntheta; i++) {
      fscanf(fgauss, "%s %s", buff2, buff3);
      xgvec[i] = atof(buff2);
      wgvec[i] = atof(buff3);
    }
    fclose(fgauss);

  } else {

    /* All the particles will be spheres */

    Int3darray(&Bbox, BoxXsize, BoxYsize, BoxZsize);

    if (Bbox.val == NULL) {
      freegenmic();
      bailout("genmic", "Memory allocation error");
      fflush(stdout);
      exit(1);
    }

    for (i = 0; i < NUMSIZES; i++)
      Volpart[i] = 0;
  }

  fprintf(Logfile, "Enter the binder SOLID volume fraction: ");
  read_string(instring, sizeof(instring));
  binder_vfrac = atof(instring);
  fprintf(Logfile, "\n%f\n", binder_vfrac);
  fprintf(Logfile, "Enter the binder WATER volume fraction: ");
  read_string(instring, sizeof(instring));
  water_vfrac = atof(instring);
  fprintf(Logfile, "\n%f\n", water_vfrac);

  binder_vfrac = (binder_vfrac) / (binder_vfrac + water_vfrac);

  fprintf(Logfile, "Enter number of solid binder phases to add: ");
  read_string(instring, sizeof(instring));
  num_phases_to_add = atoi(instring);
  fprintf(Logfile, "\n%d\n", num_phases_to_add);
  for (k = 0; k < num_phases_to_add; k++) {
    fprintf(Logfile, "Enter phase id to add: ");
    read_string(instring, sizeof(instring));
    phase_id = atoi(instring);
    fprintf(Logfile, "\n%d\n", phase_id);
    fprintf(Logfile,
            "Enter volume fraction of this phase (total BINDER SOLID basis): ");
    read_string(instring, sizeof(instring));
    Vol_frac[phase_id] = atof(instring);
    fprintf(Logfile, "\n%f\n", Vol_frac[phase_id]);

    /* Convert to total VOLUME basis, binder + water system */
    Vol_frac[phase_id] *= binder_vfrac;

    target_phase_vox = (Vol_frac[phase_id] * (float)Binderpix) + 0.5;
    fprintf(Logfile, "Will need to enter %d pixels of this phase...\n",
            target_phase_vox);
    fprintf(
        Logfile,
        "Enter number of size classes for this phase (max is %d): ", NUMSIZES);
    read_string(instring, sizeof(instring));
    Size_classes[phase_id] = atoi(instring);
    if (Size_classes[phase_id] >= NUMSIZES) {
      fprintf(stderr,
              "\nERROR line 2990:  Number of size classes cannot exceed %d.  "
              "Exiting.\n\n",
              NUMSIZES);
      freegenmic();
      bailout("genmic", "Bad value for number of size classes");
      exit(1);
    }
    fprintf(Logfile, "\n%d\n", Size_classes[phase_id]);
    for (j = 0; j < Size_classes[phase_id]; j++) {
      fprintf(Logfile,
              "Enter diameter of size class %d in micrometers (integer values "
              "only): ",
              j);
      read_string(instring, sizeof(instring));
      Dinput[phase_id][j] = atof(instring);
      fprintf(Logfile, "\n%d\n", (int)(Dinput[phase_id][j]));
      /* Convert diameter to pixel units */
      Dinput[phase_id][j] *= (1.0 / Res);
      /* Round to nearest integer */
      Dinput[phase_id][j] = (float)((int)(Dinput[phase_id][j] + 0.5));
      fprintf(Logfile,
              "Enter volume fraction of phase %d particles in size class %d: ",
              phase_id, j);
      read_string(instring, sizeof(instring));
      Pdf[phase_id][j] = atof(instring);
      fprintf(Logfile, "\n%f\n", Pdf[phase_id][j]);
    }

    if (Shape == REALSHAPE) {
      /* All particles are real shape */
      if (phase_id != FLYASH && phase_id != SFUME) {
        shapevar = REALSHAPE;
        Phase_shape[phase_id].shapetype = REALSHAPE;
        strcpy(Phase_shape[phase_id].pathroot, Pathroot);
        strcpy(Phase_shape[phase_id].shapeset, Shapeset);
        strcpy(buff, Pathroot);
        strcpy(buff1, Shapeset);
      }
    } else if (Shape != SPHERES) {
      /* Some particles are real shape here */
      fprintf(Logfile, "Spheres (0) or Real shapes (1)? ");
      read_string(instring, sizeof(instring));
      shapevar = atoi(instring);
      if (shapevar == REALSHAPE) {
        Phase_shape[phase_id].shapetype = REALSHAPE;
        fprintf(Logfile, "What is the shape path? ");
        read_string(buff, sizeof(buff));
        Filesep = buff[strlen(buff) - 1];
        fprintf(Logfile, "%s\n", buff);
        strcpy(Phase_shape[phase_id].pathroot, buff);
        fprintf(Logfile,
                "Take cement shapes from what data set in this directory? ");
        read_string(buff1, sizeof(buff1));
        fprintf(Logfile, "%s\n", buff1);
        strcpy(Phase_shape[phase_id].shapeset, buff1);
      }
    }

    if (Phase_shape[phase_id].shapetype == REALSHAPE) {

      Phase_shape[phase_id].ntheta = Ntheta;
      Phase_shape[phase_id].nphi = Nphi;

      /* Allocate memory for Gaussian quadrature points */

      Phase_shape[phase_id].xg = fvector(Ntheta + 1);
      if (!Phase_shape[phase_id].xg) {
        freegenmic();
        bailout("genmic", "Could not allocate memory for xg");
        exit(1);
      }
      Phase_shape[phase_id].wg = fvector(Nphi + 1);
      if (!Phase_shape[phase_id].wg) {
        freegenmic();
        bailout("genmic", "Could not allocate memory for wg");
        exit(1);
      }

      for (i = 1; i <= Ntheta; i++) {
        Phase_shape[phase_id].xg[i] = xgvec[i];
        Phase_shape[phase_id].wg[i] = wgvec[i];
      }
    }

    /***
     * Now bubble sort the diameters in descending order
     ***/

    for (i = 0; i < Size_classes[phase_id]; i++) {
      for (j = (i + 1); j < Size_classes[phase_id]; j++) {
        if (Dinput[phase_id][i] < Dinput[phase_id][j]) {
          tval = Dinput[phase_id][i];
          Dinput[phase_id][i] = Dinput[phase_id][j];
          Dinput[phase_id][j] = tval;
          tval = Pdf[phase_id][i];
          Pdf[phase_id][i] = Pdf[phase_id][j];
          Pdf[phase_id][j] = tval;
        }
      }
    }

    /***
     * Determine number of particles of each diameter to add, assuming
     *spheres. Try to get the actual overall volume fraction closer to the
     *target while maintaining fidelity to the PSD
     *
     * The approach below starts with the largest size particles, and tries
     * to stay close to the desired fraction of particles this diameter
     * and larger
     *
     * Remember, target_phase_vox and total_phase_vox refer only to the phase
     * in question, not the combination of all the phases.
     ***/

    total_phase_vox = 0;
    for (i = 0; i < Size_classes[phase_id]; i++) {
      Volpart[i] = diam2vol(Dinput[phase_id][i]);
      numparts[phase_id][i] =
          (int)(((float)(target_phase_vox)*Pdf[phase_id][i] /
                 (float)(Volpart[i])) +
                0.5);
      total_phase_vox += numparts[phase_id][i] * Volpart[i];
      fprintf(Logfile, "Number of particles of diameter %f = %d\n",
              Dinput[phase_id][i], numparts[phase_id][i]);
      fprintf(Logfile, "Volume of each particle of diameter %f = %d\n",
              Dinput[phase_id][i], Volpart[i]);
    }
    fprintf(Logfile, "Total pixels based on PDF is %d\n", total_phase_vox);
    fprintf(Logfile, "Making adjustments of particle numbers now...\n");

    extra_pixels = 0;
    for (i = 0; i < Size_classes[phase_id] - 1; i++) {
      target_vox_i = (int)(((float)(target_phase_vox)*Pdf[phase_id][i]) + 0.5);
      fprintf(Logfile, "Target pixels in size class %d = %d\n", i,
              target_vox_i);
      extra_pixels += (target_vox_i - (numparts[phase_id][i] * Volpart[i]));
      fprintf(Logfile, "Extra pixels (cumulative) = %d\n", extra_pixels);
      if (Volpart[i] < (int)(fabs((float)extra_pixels))) {
        delta_particles = (float)(extra_pixels) / (float)(Volpart[i]);
        numparts[phase_id][i] += delta_particles;
        total_phase_vox += (delta_particles * Volpart[i]);
        extra_pixels -= (delta_particles * Volpart[i]);
        fprintf(Logfile, "Reduced number of particles in size class %d by %d\n",
                i, delta_particles);
      }
    }

    /***
     * Finally, adjust the number of the smallest size class to
     * make the overall volume fraction exact
     ***/

    if (Dinput[phase_id][Size_classes[phase_id] - 1] <= 1.0) {
      numparts[phase_id][Size_classes[phase_id] - 1] +=
          (target_phase_vox - total_phase_vox);
    }

    /***
     * Done with this phase.  Sanity check on PDF and total voxels of this
     *phase to be added.
     ***/

    /*
    total_phase_vox = 0;
    for (i = 0; i < Size_classes[phase_id]; i++) {
        total_phase_vox += (Volpart[i] * numparts[phase_id][i]);
    }

   fprintf(Logfile,"\n***************************************************************\n");
   fprintf(Logfile,"    Targeted %d vox of phase %d, and will be adding %d
   vox\n", target_phase_vox,phase_id,total_phase_vox);
   fprintf(Logfile,"\n***************************************************************\n");

    target_vox_i = 0;
    for (i = 0; i < Size_classes[phase_id]; i++) {
        target_vox_i = (float)(Volpart[i] * numparts[phase_id][i]);
       fprintf(Logfile,"    Size class %2d, diam = %2d, target pdf = %.4f,
   target_vox_i = %d\n", i,
   (int)(Dinput[phase_id][i]),Pdf[phase_id][i],target_vox_i);
    }
   fprintf(Logfile,"\n***************************************************************\n");
    */

    fflush(Logfile);
  }

  /*  All phases are done, except possibly the fine portion of the aggregate
   * grading */

  if (Size_classes[INERTAGG] > 0) {
    Vol_frac[INERTAGG] *= binder_vfrac; /* Converts to total VOLUME basis,
                                           binder + water system */
    target_phase_vox = (Vol_frac[INERTAGG] * (float)Binderpix) + 0.5;
    fprintf(Logfile,
            "Will need to enter %d pixels of INERT AGGREGATE to binder...\n",
            target_phase_vox);
    fprintf(Logfile, "Number of size classes for INERTAGG phase is %d\n",
            Size_classes[INERTAGG]);
    fflush(Logfile);

    if (Shape == REALSHAPE) {
      /* All particles are real shape */
      shapevar = REALSHAPE;
      Phase_shape[INERTAGG].shapetype = REALSHAPE;
      strcpy(Phase_shape[INERTAGG].pathroot, Pathroot);
      strcpy(Phase_shape[INERTAGG].shapeset, Shapeset);
      strcpy(buff, Pathroot);
      strcpy(buff1, Shapeset);

      Phase_shape[INERTAGG].ntheta = Ntheta;
      Phase_shape[INERTAGG].nphi = Nphi;

      /* Allocate memory for Gaussian quadrature points */

      Phase_shape[INERTAGG].xg = fvector(Ntheta + 1);
      if (!Phase_shape[INERTAGG].xg) {
        freegenmic();
        bailout("genmic", "Could not allocate memory for xg");
        exit(1);
      }
      Phase_shape[INERTAGG].wg = fvector(Nphi + 1);
      if (!Phase_shape[INERTAGG].wg) {
        freegenmic();
        bailout("genmic", "Could not allocate memory for wg");
        exit(1);
      }

      for (i = 1; i <= Ntheta; i++) {
        Phase_shape[INERTAGG].xg[i] = xgvec[i];
        Phase_shape[INERTAGG].wg[i] = wgvec[i];
      }
    }

    /***
     * Now bubble sort the diameters in descending order
     ***/

    for (i = 0; i < Size_classes[INERTAGG]; i++) {
      for (j = (i + 1); j < Size_classes[INERTAGG]; j++) {
        if (Dinput[INERTAGG][i] < Dinput[INERTAGG][j]) {
          tval = Dinput[INERTAGG][i];
          Dinput[INERTAGG][i] = Dinput[INERTAGG][j];
          Dinput[INERTAGG][j] = tval;
          tval = Pdf[INERTAGG][i];
          Pdf[INERTAGG][i] = Pdf[INERTAGG][j];
          Pdf[INERTAGG][j] = tval;
        }
      }
    }

    /***
     * Determine number of particles of each diameter to add, assuming
     *spheres. Try to get the actual overall volume fraction closer to the
     *target while maintaining fidelity to the PSD
     *
     * The approach below starts with the largest size particles, and tries
     * to stay close to the desired fraction of particles this diameter
     * and larger
     *
     * Remember, target_phase_vox and total_phase_vox refer only to the phase
     * in question, not the combination of all the phases.
     ***/

    /*  MUST NORMALIZE PDF OF AGGREGATE TO 1 */

    total_phase_vox = 0;
    for (i = 0; i < Size_classes[INERTAGG]; i++) {
      Volpart[i] = diam2vol(Dinput[INERTAGG][i]);
      numparts[INERTAGG][i] =
          (int)(((float)(target_phase_vox)*Pdf[INERTAGG][i] /
                 (float)(Volpart[i])) +
                0.5);
      total_phase_vox += numparts[INERTAGG][i] * Volpart[i];
      fprintf(Logfile, "Number of particles of diameter %f = %d\n",
              Dinput[INERTAGG][i], numparts[INERTAGG][i]);
      fprintf(Logfile, "Volume of each particle of diameter %f = %d\n",
              Dinput[INERTAGG][i], Volpart[i]);
    }
    fprintf(Logfile, "Total pixels based on PDF is %d\n", total_phase_vox);
    fprintf(Logfile, "Making adjustments of particle numbers now...\n");

    extra_pixels = 0;
    for (i = 0; i < Size_classes[INERTAGG] - 1; i++) {
      target_vox_i = (int)(((float)(target_phase_vox)*Pdf[INERTAGG][i]) + 0.5);
      fprintf(Logfile, "Target pixels in size class %d = %d\n", i,
              target_vox_i);
      extra_pixels += (target_vox_i - (numparts[INERTAGG][i] * Volpart[i]));
      fprintf(Logfile, "Extra pixels (cumulative) = %d\n", extra_pixels);
      if (Volpart[i] < (int)(fabs((float)extra_pixels))) {
        delta_particles = (float)(extra_pixels) / (float)(Volpart[i]);
        numparts[INERTAGG][i] += delta_particles;
        total_phase_vox += (delta_particles * Volpart[i]);
        extra_pixels -= (delta_particles * Volpart[i]);
        fprintf(Logfile, "Reduced number of particles in size class %d by %d\n",
                i, delta_particles);
      }
    }

    /***
     * Finally, adjust the number of the smallest size class to
     * make the overall volume fraction exact
     ***/

    if (Dinput[INERTAGG][Size_classes[INERTAGG] - 1] <= 1.0) {
      numparts[INERTAGG][Size_classes[INERTAGG] - 1] +=
          (target_phase_vox - total_phase_vox);
    }
  }

  /* ADDITION OF AGGREGATE TO BINDER FINISHED */

  /***
   *  All PSD information is now settled.  Must lump all the information
   *  by diameter across phases
   ***/

  /***
   * Determine numsize by scanning through the numparts array and counting
   * all nonzero entries
   ***/

  numsize = 0;
  for (i = 1; i < NPHASES; i++) {
    for (j = 0; j < Size_classes[i]; j++) {
      if (numparts[i][j] > 0) {
        if (Dinput[i][j] > 1.0) {
          diam[numsize] = Dinput[i][j];
          frad[numsize] = (float)(diam[numsize] / 2.0);
          num[numsize] = numparts[i][j];
          phase[numsize] = i;
          numsize++;
        } else {
          Onepixnum[i] = numparts[i][j];
          if (Verbose)
            fprintf(Logfile, "\nOne-pix particles of phase %d = %d", i,
                    Onepixnum[i]);
        }
      }
    }
  }

  if (numsize > NUMSIZES || numsize < 0) {
    freegenmic();
    bailout("genmic", "Bad value for numsize");
    exit(1);
  }

  /* Now sort on diam in descending order */

  for (i = 0; i < numsize; i++) {
    for (j = (i + 1); j < numsize; j++) {
      if (diam[i] < diam[j]) {
        tval = diam[i];
        diam[i] = diam[j];
        diam[j] = tval;
        tval = frad[i];
        frad[i] = frad[j];
        frad[j] = tval;
        linval = num[i];
        num[i] = num[j];
        num[j] = linval;
        inval = phase[i];
        phase[i] = phase[j];
        phase[j] = inval;
      }
    }
  }

  fprintf(Logfile, "Enter dispersion factor (separation distance ");
  fprintf(Logfile, "in pixels) for spheres (0-2)\n");
  fprintf(Logfile, "0 corresponds to totally random placement\n");
  read_string(instring, sizeof(instring));
  Dispdist = atoi(instring);
  fprintf(Logfile, "%d \n", Dispdist);
  if ((Dispdist < 0) || (Dispdist > 2)) {
    freegenmic();
    bailout("genmic", "Bad value for dispersion distance");
    exit(1);
  }

  fprintf(Logfile, "Enter probability for gypsum particles ");
  fprintf(Logfile, "on a random particle basis (0.0-1.0) \n");
  read_string(instring, sizeof(instring));
  Probgyp = atof(instring);
  fprintf(Logfile, "%f \n", Probgyp);
  if ((Probgyp < -TINY) || (Probgyp > 1.0 + TINY)) {
    freegenmic();
    bailout("genmic", "Bad value for total gypsum probability");
    exit(1);
  }

  fprintf(Logfile,
          "Enter probability for hemihydrate form of gypsum (0.0-1.0)\n");
  read_string(instring, sizeof(instring));
  Probhem = atof(instring);
  fprintf(Logfile, "%f\n", Probhem);
  fprintf(Logfile,
          "Enter probability for anhydrite form of gypsum (0.0-1.0)\n");
  read_string(instring, sizeof(instring));
  Probanh = atof(instring);
  fprintf(Logfile, "%f\n", Probanh);
  if ((Probhem < -TINY) || (Probhem > 1.0 + TINY) || (Probanh < -TINY) ||
      (Probanh > 1.0 + TINY) || ((Probanh + Probhem) > 1.0 + TINY + TINY)) {

    freegenmic();
    bailout("genmic", "Bad value for hemihyd or anhydrite probs");
    exit(1);
  }

  if ((numsize > 0) && (numsize < (NUMSIZES + 1))) {

    if (Verbose) {
      fprintf(Logfile, "Calculated information for ");
      fprintf(Logfile, "each particle class (largest size 1st)\n");
      fprintf(Logfile, "Phases are %d- Cement and (random) calcium ", C3S);
      fprintf(Logfile, "sulfate, %d- C2S, %d- Gypsum, ", C2S, GYPSUM);
      fprintf(Logfile, "%d- hemihydrate %d- anhydrite ", HEMIHYD, ANHYDRITE);
      fprintf(Logfile, "%d- Silica fume, %d- Inert, ", SFUME, INERT);
      fprintf(Logfile, "%d- Slag, %d- CaCO3 %d- Fly Ash, ", SLAG, CACO3,
              FLYASH);
      fprintf(Logfile, "%d- Lime\n", FREELIME);
    }

    Ntheta = Nphi = 0;

    for (ip = 0; ip < numsize; ip++) {

      /* Convert sphere diameter to volume in pixels */

      if (Verbose) {
        fprintf(Logfile, "Adding particles of effective diameter %d\n",
                (int)diam[ip]);
        fprintf(Logfile, "Phase of these particles is %d \n", phase[ip]);
        fprintf(Logfile, "Calculated number of these particles is %d\n",
                num[ip]);
        fflush(Logfile);
      }
      Volpart[ip] = diam2vol(diam[ip]);

      if (phase[ip] == C3S) {
        Target_total += num[ip] * Volpart[ip];
        if (Volpart[ip] <= 1767) {
          /* Particle diameter less than 15 micrometers */
          Target_total_lt15 += num[ip] * Volpart[ip];
        }
      }
    }

    Target_sulfate = (double)Target_total * Probgyp;
    Target_anhydrite = (double)Target_total * Probgyp * Probanh;
    Target_hemi = (double)Target_total * Probgyp * Probhem;

    /* Modify probability of calcium sulfate so that all calcium sulfates
        are placed at diameters less than 15 micrometers */

    if (Target_total_lt15 > 0)
      Probgyp = (Target_sulfate / Target_total_lt15);
    if (Verbose) {
      fprintf(Logfile, "\nTarget_sulfate = %d", Target_sulfate);
      fprintf(Logfile, "\nTarget_anhydrite = %d", Target_anhydrite);
      fprintf(Logfile, "\nTarget_hemi = %d", Target_hemi);
      fflush(Logfile);
    }

    /***
     *    Place particles at random
     ***/

    if (Verbose) {
      fprintf(Logfile, "\nGoing into genparticles now...");
      fflush(Logfile);
    }

    /* We don't need the return value in this case */
    nplaced = genparticles(numsize, num, frad, phase);
    if (Verbose) {
      fprintf(Logfile, "\nBack Out of genparticles now...");
      fflush(Logfile);
    }

    /*** Sanity check on pore voxels ***/
    /*
    totpix = 0;
    for (kkk = 0; kkk < Zsyssize; ++kkk) {
        for (jjj = 0; jjj < Ysyssize; ++jjj) {
            for (iii = 0; iii < Xsyssize; ++iii) {
                if (Cemreal.val[getInt3dindex(Cemreal,iii,jjj,kkk)] == 0)
    totpix++;
            }
        }
    }
   fprintf(Logfile,"\nTotal pore voxels now is %d",totpix);
    */
  }

  free_Int3darray(&Bbox);
  if (Y)
    free_complexmatrix(Y, 0, Nnn, -Nnn, Nnn);
  if (AA)
    free_complexmatrix(AA, 0, Nnn, -Nnn, Nnn);
  if (A)
    free_complexmatrix(A, 0, Nnn, -Nnn, Nnn);
  if (xgvec)
    free_fvector(xgvec);
  if (wgvec)
    free_fvector(wgvec);

  return;
}

/***
 *    drawfloc
 *
 *    Routine to draw a particle during flocculation routine
 *
 *     Arguments:
 *        struct particle *partpoint is the pointer to this particle structure
 *        const int mode is set to Erase or Draw
 *
 *     Returns:    integer flag telling whether sphere will fit
 *
 *    Calls:        No other routines
 *    Called by:    makefloc
 ***/
void drawfloc(struct particle *partpoint, const int mode) {
  int xp, yp, zp, i;
  int pid, phid;
  char strmode[10];

  pid = phid = POROSITY;
  sprintf(strmode, "Erasing");
  if (mode == Draw) {
    sprintf(strmode, "Drawing");
    pid = partpoint->partid + 1;
    phid = partpoint->partphase;
  }

  /* Check all pixels belonging to the particle */

  for (i = 0; i < partpoint->numpix; i++) {
    xp = partpoint->xi[i];
    yp = partpoint->yi[i];
    zp = partpoint->zi[i];
    Cement.val[getInt3dindex(Cement, xp, yp, zp)] = pid;
    Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] = phid;
  }
  return;
}

/***
 *    checkfloc
 *
 *    Routine to check spherical particle placement during flocculation
 *
 *     Arguments:
 *        struct particle *partpoint points to the current particle structure
 *        int dx,dy,dz is the direction of movement of this particle
 *
 *     Returns:    int flag indicating if placement is possible
 *
 *    Calls:        No other routines
 *    Called by:    makefloc
 ***/
int checkfloc(struct particle *partpoint, int dx, int dy, int dz) {
  int blocked_by, xp, yp, zp, i, xmark;

  blocked_by = 0; /* Flag indicating if placement is possible */

  /* Check all pixels belonging to the particle */

  xmark = partpoint->xi[0] + dx;
  for (i = 0; (i < partpoint->numpix) && (!blocked_by); i++) {

    xp = partpoint->xi[i] + dx;
    yp = partpoint->yi[i] + dy;
    zp = partpoint->zi[i] + dz;
    xp += checkbc(xp, Xsyssize);
    yp += checkbc(yp, Ysyssize);
    zp += checkbc(zp, Zsyssize);

    /* Check for overlap with aggregate */

    if ((Simwall) && ((xmark - Wallpos) * (xp - Wallpos)))
      blocked_by = ((int)TMPAGGID);

    if ((Cement.val[getInt3dindex(Cement, xp, yp, zp)] > POROSITY) &&
        (!blocked_by)) {

      /* Particle hit; record its ID */

      blocked_by = Cement.val[getInt3dindex(Cement, xp, yp, zp)] - 1;
    }
  }

  /***
   *    Return flag indicating if sphere will fit (=0)
   *    or not (=ID of particle preventing the fit)
   ***/

  return (blocked_by);
}

/***
 *    makefloc
 *
 *    New routine to perform flocculation of particles
 *
 *     Arguments:    None
 *     Returns:    Nothing
 *
 *    Calls:        drawfloc, checkfloc, ran1
 *    Called by:    main program
 **/
void makefloc(void) {
  register int i, j, ipart;
  float degfloc;
  int targetnumflocs, numflocs, numdeleted;
  int blocked_by, dx, dy, dz, moveran, flochit;
  char instring[MAXSTRING];
  struct particle *partpoint, *partkeep, *parttmp;
  int *index;

  dx = dy = dz = 0;
  partpoint = NULL;
  partkeep = NULL;
  parttmp = NULL;

  /***
   *    Allocate memory for index table
   ***/

  index = ivector(Npart + 1);
  if (!index) {
    freegenmic();
    bailout("makefloc", "Memory allocation error");
    exit(1);
  }

  for (i = 1; i <= Npart; i++) {
    index[i] = Particle[i]->partid;
  }

  /*  This routine asks for the degree of flocculation.  A value of 0 */
  /*  means that no intentional flocs will be made, while a value of 1 */
  /*  means that the routine will continue until every particle is */
  /*  attached to a floc */

  fprintf(Logfile, "\nEnter the degree of flocculation desired (0.0 to 1.0): ");
  fflush(Logfile);
  read_string(instring, sizeof(instring));
  degfloc = atof(instring);
  fprintf(Logfile, "%f\n", degfloc);
  fflush(Logfile);
  targetnumflocs = Npart;
  if (degfloc > 0.0) {
    targetnumflocs = (int)(((float)(Npart)) * (1.0 - degfloc));
    if (targetnumflocs > Npart)
      targetnumflocs = Npart;
    if (targetnumflocs < 1)
      targetnumflocs = 1;
  }
  fprintf(Logfile, "Target number of flocs is %d\n", targetnumflocs);
  fflush(Logfile);

  numflocs = Npart;
  while (numflocs > targetnumflocs) {

    numdeleted = 0;
    /* Try to move each floc in turn */

    for (ipart = 1; ipart <= Npart; ipart++) {
      if (Particle[ipart] == NULL) {
        numdeleted++;
      } else {

        /* Move this particle in a randomly chosen Cartesian direction */

        moveran = 6.0 * ran1(Seed);

        dx = dy = dz = 0;

        switch (moveran) {
        case 0:
          dx = 1;
          break;
        case 1:
          dx = (-1);
          break;
        case 2:
          dy = 1;
          break;
        case 3:
          dy = (-1);
          break;
        case 4:
          dz = 1;
          break;
        case 5:
          dz = (-1);
          break;
        default:
          break;
        }

        /* First erase all particles in the floc */

        partpoint = Particle[ipart];
        while (partpoint != NULL) {
          drawfloc(partpoint, Erase); /* set to porosity */
          partkeep = partpoint;
          partpoint = partpoint->nextpart;
        }

        /* Now try to draw the floc at new location */

        partpoint = Particle[ipart];
        blocked_by = 0;
        while ((partpoint != NULL) && (!blocked_by)) {
          blocked_by =
              checkfloc(partpoint, dx, dy, dz); /* zero if not blocked */
          partkeep = partpoint;
          partpoint = partpoint->nextpart;
        }

        if (!blocked_by) {

          /* Floc fits at new location, so draw it there */
          partpoint = Particle[ipart];
          while (partpoint != NULL) {
            /* Update pixel locations for particle */
            for (j = 0; j < partpoint->numpix; j++) {
              partpoint->xi[j] += dx;
              partpoint->yi[j] += dy;
              partpoint->zi[j] += dz;
              partpoint->xi[j] += checkbc(partpoint->xi[j], Xsyssize);
              partpoint->yi[j] += checkbc(partpoint->yi[j], Ysyssize);
              partpoint->zi[j] += checkbc(partpoint->zi[j], Zsyssize);
            }
            drawfloc(partpoint, Draw);
            partpoint = partpoint->nextpart;
          }

        } else {

          /* Floc does not fit at this location. */
          /* First of all, put the floc in its most recent unblocked location
           */
          partpoint = Particle[ipart];
          while (partpoint != NULL) {
            drawfloc(partpoint, Draw);
            partkeep = partpoint;
            partpoint = partpoint->nextpart;
          }

          /* At this point, partkeep should point to the last particle in the
           * moving floc */

          /* Now, what did the floc hit? */

          if (blocked_by != TMPAGGID) {
            flochit = index[blocked_by];
            partpoint = Particle[ipart];
            /* Floc hit another particle.  Add that particle to the floc */
            /* Move all of the particles from the blocking cluster to the
             * moving cluster */
            parttmp = Particle[flochit];
            /* parttmp is the floc containing the blocking particle */
            /* so point the last particle in the moving floc (partkeep) to the
               first particle in the blocking floc, which is pointed to by
               parttmp */
            partkeep->nextpart = parttmp;
            while (parttmp != NULL) {
              index[parttmp->partid] = ipart;
              parttmp->flocid = partpoint->flocid;
              parttmp = parttmp->nextpart;
            }

            /* Now we no longer need the blocking floc structure because it
               has been merged with the moving floc */
            Particle[flochit] = NULL;
            /*
            free_particlevector(Particle[index[blocked_by]]);
           fprintf(Logfile,"\nMemory freeing was successful");
            fflush(Logfile);
            */
            if (Particle[flochit] != NULL) {
              fprintf(stderr, "\nWARNING line 3775: Hit floc was not erased "
                              "from memory.");
              fflush(stderr);
              Particle[flochit] = NULL;
            }
            numflocs--;
          }
        }
      }
    }
    fprintf(Logfile,
            "\nNumber flocs deleted so far is %d and number of flocs is %d\n",
            numdeleted, numflocs);
    fflush(Logfile);
  }

  if (index)
    free_ivector(index);

  NumberOfFlocs = numflocs;
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
  int npor, nc2s, ngyp, ncem, nagg, nsfume, ninert, nfreelime;
  int nflyash, nanh, nhem, ncaco3, nslag;
  int nc3a, nc4af, nk2so4, nna2so4;
  int i, j, k, valph;

  /* Counters for the various phase fractions */

  npor = ngyp = ncem = nagg = ninert = 0;
  nfreelime = nflyash = nanh = ncaco3 = 0;
  nslag = nc3a = nfreelime = nhem = nc4af = 0;
  nk2so4 = nna2so4 = 0;
  ;
  nslag = nc2s = nsfume = nflyash = nanh = 0;
  nhem = ncaco3 = nfreelime = 0;

  /* Check all pixels in 3-D microstructure */

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        valph = Cemreal.val[getInt3dindex(Cemreal, i, j, k)];
        switch (valph) {
        case POROSITY:
          npor++;
          break;
        case C3S:
          ncem++;
          break;
        case C2S:
          nc2s++;
          break;
        case C3A:
          nc3a++;
          break;
        case C4AF:
          nc4af++;
          break;
        case K2SO4:
          nk2so4++;
          break;
        case NA2SO4:
          nna2so4++;
          break;
        case GYPSUM:
          ngyp++;
          break;
        case HEMIHYD:
          nhem++;
          break;
        case ANHYDRITE:
          nanh++;
          break;
        case INERTAGG:
          nagg++;
          break;
        case SFUME:
          nsfume++;
          break;
        case INERT:
          ninert++;
          break;
        case SLAG:
          nslag++;
          break;
        case FLYASH:
          nflyash++;
          break;
        case CACO3:
          ncaco3++;
          break;
        case FREELIME:
          nfreelime++;
          break;
        default:
          fprintf(stderr, "\nWARNING line 3885:  Unidentifiable phase ID (%d) ",
                  valph);
          fprintf(stderr, "encountered.\nPixel at location ");
          fprintf(stderr, "(%d,%d,%d)\n", i, j, k);
          fflush(stderr);
          break;
        }
      }
    }
  }

  /* Output results */

  if (Verbose) {
    fprintf(Logfile, "\nPhase counts are: \n");
    fprintf(Logfile, "\tPorosity = %d \n", npor);
    fprintf(Logfile, "\tCement = %d \n", ncem);
    fprintf(Logfile, "\tC2S = %d \n", nc2s);
    fprintf(Logfile, "\tGypsum = %d \n", ngyp);
    fprintf(Logfile, "\tAnhydrite = %d \n", nanh);
    fprintf(Logfile, "\tHemihydrate = %d \n", nhem);
    fprintf(Logfile, "\tSilica fume = %d \n", nsfume);
    fprintf(Logfile, "\tInert = %d \n", ninert);
    fprintf(Logfile, "\tSlag = %d \n", nslag);
    fprintf(Logfile, "\tCaCO3 = %d \n", ncaco3);
    fprintf(Logfile, "\tFly Ash = %d \n", nflyash);
    fprintf(Logfile, "\tAggregate = %d \n", nagg);
  }

  return;
}

/***
 *    measagg
 *
 *    Routine to measure phase fractions as a
 *    function of distance from aggregate surface
 *
 *     Arguments:    None
 *     Returns:    Nothing
 *
 *    Calls:        No other routines
 *    Called by:    main program
 ***/
void measagg(void) {
  int phase[NPHASES], ptot, icnt, ixlo, ixhi, iy, iz, phid, idist;

  fprintf(Logfile, "Distance  Porosity  Cement  C2S  Gypsum  Anhydrite ");
  fprintf(Logfile, "Hemihydrate Pozzolan  Inert   Slag  CaCO3   Fly Ash\n");

  /* Increase distance from aggregate in increments of one */

  for (idist = 1; idist <= Wallpos; idist++) {

    /* Pixel to the left of aggregate surface */

    ixlo = Wallpos - idist;

    /* Pixel to the right of aggregate surface */

    ixhi = Wallpos + idist;

    /* Initialize phase counts for this distance */

    for (icnt = 0; icnt < NPHASES; icnt++) {
      phase[icnt] = 0;
    }

    ptot = 0;

    /***
     *    Check all pixels which are this distance
     *    from aggregate surface
     ***/

    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 0; iz < Zsyssize; iz++) {

        phid = Cemreal.val[getInt3dindex(Cemreal, ixlo, iy, iz)];
        ptot++;
        if (phid <= FLYASH) {
          phase[phid]++;
        }

        phid = Cemreal.val[getInt3dindex(Cemreal, ixhi, iy, iz)];
        ptot++;
        if (phid <= FLYASH) {
          phase[phid]++;
        }
      }
    }

    /* Output results for this distance from surface */

    fprintf(Logfile, "%d   ", idist);
    fprintf(Logfile, "%d   ", phase[POROSITY]);
    fprintf(Logfile, "%d    ", phase[C3S]);
    fprintf(Logfile, "%d  ", phase[C2S]);
    fprintf(Logfile, "%d  ", phase[GYPSUM]);
    fprintf(Logfile, "%d ", phase[ANHYDRITE]);
    fprintf(Logfile, "%d ", phase[HEMIHYD]);
    fprintf(Logfile, "%d  ", phase[SFUME]);
    fprintf(Logfile, "%d ", phase[INERT]);
    fprintf(Logfile, "%d ", phase[SLAG]);
    fprintf(Logfile, "%d ", phase[CACO3]);
    fprintf(Logfile, "%d\n", phase[FLYASH]);
  }

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

    freegenmic();
    bailout("genmic", "Memory allocation failure");
    fflush(Logfile);
    exit(1);
  }

  fprintf(Logfile, "Enter phase to analyze 0) pores 1) Cement  \n");
  read_string(instring, sizeof(instring));
  npix = atoi(instring);
  fprintf(Logfile, "%d \n", npix);
  if ((npix != POROSITY) && (npix != C3S)) {
    freegenmic();
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

      if (((Cement.val[getInt3dindex(Cement, i, j, k)] == npix) &&
           ((Cement.val[getInt3dindex(Cement, i, j, Zsyssize - 1)] == npix) ||
            (Cement.val[getInt3dindex(Cement, i, j, Zsyssize - 1)] ==
             (npix + Burnt)))) ||
          ((Cement.val[getInt3dindex(Cement, i, j, Zsyssize - 1)] > 0) &&
           (Cement.val[getInt3dindex(Cement, i, j, k)] > 0) &&
           (Cement.val[getInt3dindex(Cement, i, j, k)] < Burnt) &&
           (npix == C3S))) {

        /* Start a burn front */

        Cement.val[getInt3dindex(Cement, i, j, k)] += Burnt;
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
                if ((Cement.val[getInt3dindex(Cement, x1, y1, z1)] == npix) ||
                    ((Cement.val[getInt3dindex(Cement, x1, y1, z1)] > 0) &&
                     (Cement.val[getInt3dindex(Cement, x1, y1, z1)] < Burnt) &&
                     (npix == C3S))) {

                  ntot++;
                  Cement.val[getInt3dindex(Cement, x1, y1, z1)] += Burnt;
                  nnew++;

                  if (nnew >= Maxburning) {
                    fprintf(Logfile, "error in size of nnew \n");
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

  fprintf(Logfile, "Phase ID= %d \n", npix);
  fprintf(Logfile, "Number accessible from top= %d \n", ntop);
  fprintf(Logfile, "Number contained in through pathways= %d \n", nthrough);

  /***
   *    Return the burnt sites to their original
   *    phase values
   ***/

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {
        if (Cement.val[getInt3dindex(Cement, i, j, k)] >= Burnt) {
          Cement.val[getInt3dindex(Cement, i, j, k)] -= Burnt;
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
  int totpix, iii, jjj, kkk;
  char filen[MAXSTRING], filepart[MAXSTRING], filestruct[MAXSTRING], ch;
  FILE *outfile, *partfile, *infile;

  /*** Sanity check on placed pixels ***/
  totpix = 0;
  for (kkk = 0; kkk < Zsyssize; ++kkk) {
    for (jjj = 0; jjj < Ysyssize; ++jjj) {
      for (iii = 0; iii < Xsyssize; ++iii) {
        if (Cemreal.val[getInt3dindex(Cemreal, iii, jjj, kkk)] == 0)
          totpix++;
      }
    }
  }
  fprintf(Logfile, "... Total pore voxels is now %d\n", totpix);
  fflush(Logfile);

  fprintf(Logfile, "Enter name of file for final microstructure image\n");
  read_string(filen, sizeof(filen));
  fprintf(Logfile, "%s\n", filen);

  outfile = filehandler("genmic", filen, "WRITE");
  if (!outfile) {
    freegenmic();
    exit(1);
  }

  fprintf(Logfile, "Enter name of file to save particle IDs to \n");
  read_string(filepart, sizeof(filepart));
  fprintf(Logfile, "%s\n", filepart);

  partfile = filehandler("genmic", filepart, "WRITE");
  if (!partfile) {
    freegenmic();
    exit(1);
  }

  /***
   *    Images must carry along information about the
   *    VCCTL software version used to create the file, the system
   *    size, and the image resolution.
   ***/

  if (write_imgheader(outfile, Xsyssize, Ysyssize, Zsyssize, Res)) {
    fclose(outfile);
    fclose(partfile);
    freegenmic();
    bailout("genmic", "Error writing microstructure image header");
    exit(1);
  }

  if (write_imgheader(partfile, Xsyssize, Ysyssize, Zsyssize, Res)) {
    fclose(outfile);
    fclose(partfile);
    freegenmic();
    bailout("genmic", "Error writing particle image header");
    exit(1);
  }

  /***
   *  2025 August 04
   *  New convention is to write microstructures in C-order, where Z varies
   *the fastest, then Y, then X.
   ***/
  for (ix = 0; ix < Xsyssize; ix++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 0; iz < Zsyssize; iz++) {
        valout = Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
        /*
        if (valout == (int)(INERTAGG)) {
          valout = (int)(POROSITY);
        }
        */
        fprintf(outfile, "%d\n", valout);
        valout = Cement.val[getInt3dindex(Cement, ix, iy, iz)];
        if (valout == (int)(TMPAGGID)) {
          valout = (int)(POROSITY);
        } else if (valout < 0) {
          valout = (int)(POROSITY);
        }

        fprintf(partfile, "%d\n", valout);
      }
    }
  }

  fclose(outfile);
  fclose(partfile);

  /*** PUT NICK's STUFF RIGHT HERE ***/

  sprintf(filestruct, "%s.struct", filen);
  outfile = filehandler("genmic", filestruct, "WRITE");
  infile = filehandler("genmic", "scratchaggfile.dat", "READ");
  fprintf(outfile, "%d\n", Npart);
  while (!feof(infile)) {
    ch = getc(infile);
    if (!feof(infile))
      putc(ch, outfile);
  }

  fclose(infile);
  fflush(outfile);
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
    for (m = 0; m <= 2 * n; m++) {
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
 *    particlevector
 *
 *    Routine to allocate memory for a 1D vector of pointers to particle
 *structures. All array indices are assumed to start with zero.
 *
 *    Arguments:    int number of pixels in the particle
 *    Returns:    Pointer to memory location of first element
 *
 *    Calls:        no other routines
 *    Called by:    main routine
 *
 ***/
struct particle *particlevector(int numpix) {
  struct particle *ps;
  /* Allocate space for new particle info */

  ps = (struct particle *)malloc(sizeof(struct particle));
  if (ps != NULL) {
    ps->xi = (int *)malloc(numpix * sizeof(int));
    if (ps->xi != NULL) {
      ps->yi = (int *)malloc(numpix * sizeof(int));
      if (ps->yi != NULL) {
        ps->zi = (int *)malloc(numpix * sizeof(int));
        if (ps->zi != NULL) {
          ps->numpix = numpix;
          ps->nextpart = NULL;
          return (ps);
        } else {
          free(ps->yi);
          free(ps->xi);
          free(ps);
        }
      } else {
        free(ps->xi);
        free(ps);
      }
    } else {
      free(ps);
    }
  }

  return (ps);
}

void free_particlevector(struct particle *ps) {
  if (ps != NULL) {
    fprintf(Logfile, "\n\t\tFreeing floc ps now...");
    fflush(Logfile);
    if (ps->xi != NULL) {
      fprintf(Logfile, "\n\t\t\tFreeing floc ps->xi now... ");
      fflush(Logfile);
      free(ps->xi);
      fprintf(Logfile, "Done ");
      fflush(Logfile);
    }
    if (ps->yi != NULL) {
      fprintf(Logfile, "\n\t\t\tFreeing floc ps->yi now... ");
      fflush(Logfile);
      free(ps->yi);
      fprintf(Logfile, "Done ");
      fflush(Logfile);
    }
    if (ps->zi != NULL) {
      fprintf(Logfile, "\n\t\t\tFreeing floc ps->zi now... ");
      fflush(Logfile);
      free(ps->zi);
      fprintf(Logfile, "Done ");
      fflush(Logfile);
    }
    if (ps != NULL) {
      fprintf(Logfile, "\n\t\t\tFreeing floc ps now... ");
      fflush(Logfile);
      free(ps);
      fprintf(Logfile, "Done ");
      fflush(Logfile);
    }
  }
  ps = NULL;
  return;
}

/***
 *    particlepointervector
 *
 *    Routine to allocate memory for a 1D vector of pointers to particle
 *structures. All array indices are assumed to start with zero.
 *
 *    Arguments:    int number of elements in each dimension
 *    Returns:    Pointer to memory location of first element
 *
 *    Calls:        no other routines
 *    Called by:    main routine
 *
 ***/
struct particle **particlepointervector(int size) {
  struct particle **ps;
  size_t oneparticlesize, particlesize;

  oneparticlesize = sizeof(struct particle *);
  particlesize = size * oneparticlesize;
  ps = (struct particle **)malloc(particlesize);
  if (!ps) {
    fprintf(Logfile, "\n\nCould not allocate space for particlepointervector.");
    return (NULL);
  }

  return (ps);
}

/***
 *    free_particlepointervector
 *
 *    Routine to free the allocated memory for a 1D array of
 *    pointers to particle structures
 *
 *    All array indices are assumed to start with zero.
 *
 *    Arguments:    Pointer to memory location of first element
 *
 *     Returns:    Nothing
 *
 *    Calls:        no other routines
 *    Called by:    main routine
 *
 ***/
void free_particlepointervector(struct particle **ps) {
  int i = 0;
  for (i = 0; i < Npartc; i++) {
    if (ps[i] != NULL) {
      if (ps[i]->xi != NULL)
        free((char *)(ps[i]->xi));
      if (ps[i]->yi != NULL)
        free((char *)(ps[i]->yi));
      if (ps[i]->zi != NULL)
        free((char *)(ps[i]->zi));
    }
  }
  free((char *)(ps[0]));
  free((char *)(ps));

  return;
}

/******************************************************
 *
 * Function distrib3d.c to distribute cement clinker
 * phases in agreement with experimentally obtained
 * 2-point correlation functions for each phase.
 *
 * Particles are composed of either cement clinker or gypsum,
 * follow a user-specified size distribution, and can be
 * either flocculated, random, or dispersed.  Phase
 * distribution occurs only within the cement clinker particles
 *
 * Programmer:    Dale P. Bentz
 *                 Building and Fire Research Laboratory
 *                NIST
 *                100 Bureau Drive Mail Stop 8621
 *                Gaithersburg, MD  20899-8621   USA
 *                (301) 975-5865      FAX: (301) 990-6891
 *                E-mail: dale.bentz@nist.gov
 *
 *******************************************************/

int distrib3d(void) {
  fprintf(Logfile, "\n=== DEBUG: Entering distrib3d() ===");
  fflush(Logfile);

  /* Stack canary to detect corruption */
  const unsigned long stack_canary = 0xDEADBEEF;
  fprintf(Logfile, "\n=== DEBUG: Stack canary set to 0x%lx ===", stack_canary);
  fflush(Logfile);

  int nskip[6]; /* number of lines to skip as header in corr. files */
  register int i, j, k;
  int fileSizeInBytes = 0;
  int alumval, alum2;
  int alumdo = 1, k2so4do = 1;
  float volin, rhtest, eps, corr_res, sumarea, sumvol;
  double rdesire;
  char filecem[MAXSTRING];
  char filec3s[MAXSTRING], filesil[MAXSTRING], filealum[MAXSTRING];
  char filek2so4[MAXSTRING], filec34a[MAXSTRING];
  char filena2so4[MAXSTRING];
  char buff[MAXSTRING], instring[MAXSTRING];
  FILE *testfile;

  corr_res = 0.0;
  eps = 1.0e-5;

  /* Initialize global variables before using them */

  for (i = 0; i < MAXNUMPHASES; i++) {
    Volume[i] = 0;
    Surface[i] = 0;
  }

  for (i = 0; i < MAXSPH; i++) {
    Xsph[i] = 0;
    Ysph[i] = 0;
    Zsph[i] = 0;
  }

  /* Initialize local variables before using them */

  for (i = 0; i < 6; i++)
    nskip[i] = 0;

  fprintf(Logfile, "\n=== DEBUG: Variable initialization completed ===");
  fflush(Logfile);

  /* Set up the correlation filenames */

  fprintf(Logfile, "Enter path/root name of cement correlation files\n");
  read_string(filecem, sizeof(filecem));
  fprintf(Logfile, "%s\n", filecem);
  fflush(Logfile);

  /* Use root names to build names of correlation files */

  sprintf(filesil, "%s", filecem);
  strcat(filesil, ".sil");
  if (Verbose)
    fprintf(Logfile, "\n%s", filesil);

  sprintf(filec3s, "%s", filecem);
  strcat(filec3s, ".c3s");
  if (Verbose)
    fprintf(Logfile, "\n%s", filec3s);
  fflush(Logfile);

  sprintf(filealum, "%s", filecem);
  strcat(filealum, ".alu");
  if (Verbose)
    fprintf(Logfile, "\n%s", filealum);
  fflush(Logfile);

  sprintf(filek2so4, "%s", filecem);
  strcat(filek2so4, ".k2o");
  if (Verbose)
    fprintf(Logfile, "\n%s", filek2so4);
  fflush(Logfile);
  Verbose = 1;
  sprintf(filena2so4, "%s", filecem);
  strcat(filena2so4, ".n2o");
  if (Verbose)
    fprintf(Logfile, "\n%s", filena2so4);
  fflush(Logfile);

  /***
   *    Test to see whether we have the c3a correlation file
   *    or the c4af correlation file.  Test it by assuming the
   *    c4af file and attempting to open it.  If it does not
   *    exist, or if its size is less than 100 bytes (that is,
   *    functionally empty or corrupted) then we can assume
   *    that the c3a file is the correct one.
   ***/

  alumval = C4AF;
  sprintf(filec34a, "%s", filecem);
  strcat(filec34a, ".c4f");
  testfile = filehandler("distrib3d", filec34a, "READ_NOFAIL");
  if (!testfile) {
    /* c4af correlation kernel does not exist */
    sprintf(filec34a, "%s", filecem);
    strcat(filec34a, ".c3a");
    alumval = C3A;
  } else {
    /* testfile exists and is open; check its size */
    fseek(testfile, 0, SEEK_END);
    fileSizeInBytes = ftell(testfile);
    if (fileSizeInBytes < 100) {
      /* c4af correlation kernel exists but is empty or corrupted */
      sprintf(filec34a, "%s", filecem);
      strcat(filec34a, ".c3a");
      alumval = C3A;
    }
    fclose(testfile);
  }

  /***
   *    Attempt to read resolution of each correlation file and
   *    check them all for consistency
   ***/

  if (Verbose)
    fprintf(Logfile, "\nReading each correlation function file now... ");
  fflush(Logfile);
  for (i = 1; i <= 6; i++) {
    if (Verbose)
      fprintf(Logfile, "\n%d: ", i);
    switch (i) {
    case 1:
      strcpy(buff, filesil);
      break;
    case 2:
      strcpy(buff, filec3s);
      break;
    case 3:
      strcpy(buff, filealum);
      break;
    case 4:
      strcpy(buff, filek2so4);
      break;
    case 5:
      strcpy(buff, filena2so4);
      break;
    case 6:
      strcpy(buff, filec34a);
      break;
    }

    if (Verbose)
      fprintf(Logfile, "Trying to open file %s \n", buff);
    testfile = filehandler("distrib3d", buff, "READ_NOFAIL");
    if (!testfile) {
      if (i < 3) {
        freedistrib3d();
        bailout("distrib3d", "Could not open file");
        exit(1);
      } else if (i == 3) {
        alumdo = 0;
        fprintf(Logfile, "=== No alu file detected, set alumdo = 0 \n");
        fflush(Logfile);
      } else if (i == 4) {
        fprintf(Logfile, "=== No k2o file detected, set k2so4do = 0 \n");
        k2so4do = 0;
      }
    } else {
      fscanf(testfile, "%s", buff);
      if (!strcmp(buff, CORRRESSTRING)) {
        fscanf(testfile, "%s", instring);
        corr_res = atof(instring);
        nskip[i] = 2;
      } else {

        /***
         *    No resolution was specified.  Default the resolution
         *    to DEFAULTCORRRES to be backwards compatible with
         *    VCCTL Ver. 2.0
         ***/

        corr_res = DEFAULTCORRRES;
        nskip[i] = 0;
      }

      fclose(testfile);
    }
    if (i == 1) {

      /*** This is the first correlation file to be opened ***/

      Corr_res = corr_res;

    } else if (fabs(corr_res - Corr_res) > eps) {

      /*** Incompatible resolutions between corr files ***/

      bailout("distrib3d", "Incompatible resolutions");
      exit(1);
    }
  }
  if (Verbose)
    fprintf(Logfile, "Done.\n");

  /***
   *    Scan in the volume fractions and surface fractions
   *    of the four cement clinker phases
   *    and the two alkali sulfates when present
   ***/

  sumvol = sumarea = 0.0;
  for (i = C3S; i <= NA2SO4; i++) {
    Volf[i] = Surff[i] = 0.0;
    read_string(instring, sizeof(instring));
    volin = atof(instring);
    Volf[i] = volin;
    sumvol += volin;
    if (Verbose)
      fprintf(Logfile, "%f\n", Volf[i]);
    read_string(instring, sizeof(instring));
    volin = atof(instring);
    Surff[i] = volin;
    sumarea += volin;
    if (Verbose)
      fprintf(Logfile, "%f\n", Surff[i]);
    fflush(Logfile);
  }

  /* Normalize Volf and Surff */

  for (i = C3S; i <= NA2SO4; i++) {
    Volf[i] *= (1.0 / sumvol);
    Surff[i] *= (1.0 / sumarea);
  }

#if LIMITFILTER > 0
  Fsize = FILTERSIZE;
#else
  Fsize = (int)(((float)FILTERSIZE) * Resmag);
#endif

  Hsize_r = HISTSIZE;
  Hsize_s = HISTSIZE * (Iresmag * Iresmag * Iresmag);

  if (Fsize > (Minsyssize / 3))
    Fsize = Minsyssize / 3;

  /***
   *    Define the template radius for sintering now.
   *    It must be an odd number
   ***/

  Tradius = (int)(((float)TEMPLATE_RADIUS) * Resmag);
  if ((Tradius % 2) == 0)
    Tradius++;

  /***
   *    Allocate memory for all global variables
   ***/

  allmem();

  fprintf(Logfile, "\n=== DEBUG: Memory allocation completed ===");
  fflush(Logfile);

  /* Initialize curvature to zero */
  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {
        Curvature[i][j][k] = 0;
      }
    }
  }

  fprintf(Logfile, "\n=== DEBUG: Curvature initialization completed ===");
  fflush(Logfile);

  /***
   *    First filtering between silicates and
   *    aluminates/ferrites/alkali sulfates
   ***/

  volin = Volf[C3S] + Volf[C2S];

  /***
   *    No need to go through with this if the
   *    cement clinker is composed solely of
   *    silicate phases
   ***/

  if (Verbose)
    fprintf(Logfile, "Volin is %f", volin);

  if (volin < 1.0) {

    fprintf(Logfile, "\n=== DEBUG: About to call first rand3d() ===");
    fflush(Logfile);

    if (rand3d(C3S, alumval, filesil, nskip[1], volin, R, Filter, S, Xr)) {
      freedistrib3d();
      bailout("distrib3d", "Problem with rand3d");
      exit(1);
    }

    fprintf(Logfile, "\n=== DEBUG: First rand3d() completed successfully ===");
    fflush(Logfile);

    /* Check stack canary after first rand3d */
    if (stack_canary != 0xDEADBEEF) {
      fprintf(Logfile,
              "\n!!! STACK CORRUPTION DETECTED after first rand3d: canary = "
              "0x%lx !!!",
              stack_canary);
      fflush(Logfile);
    } else {
      fprintf(Logfile,
              "\n=== DEBUG: Stack canary still intact after first rand3d ===");
      fflush(Logfile);
    }

    if (Verbose)
      fprintf(Logfile, "\nOut of rand3d first time.");

    /***
     *    First sintering.  Arrays volume and surface are defined
     *    in stat3d
     ***/

    stat3d();
    if (Verbose)
      fprintf(Logfile, "\nOut of stat3d first time.");

    rdesire = (double)((Surff[C3S] + Surff[C2S]) *
                       (double)(Surface[C3S] + Surface[alumval]));

    /***
     *    Only perform sintering on the interface between
     *    the combined C3S/C2S domains and the combined
     *    C3A/C4AF/alkali sulfate domains if the desired hydraulic
     *    radius for the C3S/C2S domains is positive
     *    (this will almost certainly be the case every time)
     ***/

    if (Verbose)
      fprintf(Logfile, "\nRdesire is %g\n", rdesire);
    if (rdesire > 0.0) {

      /***
       *    Sinter the C3S (silicate) phase if the desired
       *    hydraulic radius for C3S is LESS than the
       *    current hydraulic radius for C3S ...
       ***/

      if ((int)rdesire < Surface[C3S]) {

        rhtest = (6.0 / 4.0) * (float)(Volume[C3S]) / rdesire;
        sinter3d(C3S, alumval, rhtest);

        /***
         *    ... Otherwise, the hydraulic radius for C3S is
         *    already less than or equal to the desired value.
         *    Therefore, treat the aluminate/ferrite/alkali sulfate  domains
         *as the solid and sinter them instead.  This effectively increases
         *the hydraulic radius of the C3S/C2S domains
         ***/

      } else {

        rdesire = (Surff[C3A] + Surff[C4AF] + Surff[K2SO4] + Surff[NA2SO4]) *
                  (float)(Surface[C3S] + Surface[alumval]);

        if (Verbose)
          fprintf(Logfile, "\nRdesire is %f\n", rdesire);
        if (rdesire > 0.0) {
          rhtest = (6.0 / 4.0) * (float)(Volume[alumval]) / rdesire;
          sinter3d(alumval, C3S, rhtest);
          if (Verbose)
            fprintf(Logfile, "\nOut of sinter3d: alumval,C3S\n");
        }
      }
    }
  }

  if (Verbose) {
    fprintf(Logfile, "\nOut of sinter3d.  Checking phase stats...");
    stat3d();
    fprintf(Logfile, "\nGetting ready to filter C2S from C3S.");
    fflush(Logfile);
  }

  /***
   *    Second filtering between C3S and C2S; defines
   *    the boundaries between C3S and C2S phases
   *    But only need to go through this if there
   *    are some silicates in the cement clinker
   ***/

  if ((Volf[C3S] + Volf[C2S]) > 0.0) {

    /***
     *    volin is fraction of silicates composed of C3S.
     *    Only need to do this if both types of silicate
     *    are present in the clinker
     ***/

    volin = Volf[C3S] / (Volf[C3S] + Volf[C2S]);

    if (Verbose)
      fprintf(Logfile, "\nVolin is %f", volin);
    fflush(Logfile);

    if (volin < 1.0 && volin > 0.0) {

      if (rand3d(C3S, C2S, filec3s, nskip[2], volin, R, Filter, S, Xr)) {
        freedistrib3d();
        bailout("distrib3d", "Problem with rand3d");
        exit(1);
      }

      /***
       *    Second sintering.  Arrays volume and surface
       *    are defined in stat3d, and need to be refreshed
       *    because of prior sintering.
       ***/

      stat3d();
      rdesire = (Surff[C3S] / (Surff[C3S] + Surff[C2S])) *
                (float)(Surface[C3S] + Surface[C2S]);

      /***
       *    Only perform sintering on the interface between
       *    the C3S and C2S domains if the desired hydraulic
       *    radius for the C3S domains is positive
       *    (this will almost certainly be the case every time)
       ***/

      if (Verbose)
        fprintf(Logfile, "\nRdesire is %f\n", rdesire);
      if (rdesire > 0.0) {

        /***
         *    Sinter the C3S phase if the desired
         *    hydraulic radius for C3S is LESS than the
         *    current hydraulic radius for C3S ...
         ***/

        if ((int)rdesire < Surface[C3S]) {

          rhtest = (6.0 / 4.0) * (float)(Volume[C3S]) / rdesire;
          sinter3d(C3S, C2S, rhtest);
          if (Verbose)
            fprintf(Logfile, "\nOut of sinter3d: C3S,C2S");

          /***
           *    ... Otherwise, the hydraulic radius for C3S is
           *    already less than or equal to the desired value.
           *    Therefore, treat the C2S domains as
           *    the solid and sinter them instead.  This effectively
           *    increases the hydraulic radius of the C3S
           *    domains
           ***/

        } else {

          rdesire = (Surff[C2S] / (Surff[C3S] + Surff[C2S])) *
                    (float)(Surface[C3S] + Surface[C2S]);

          if (Verbose)
            fprintf(Logfile, "\nRdesire is %f\n", rdesire);
          if (rdesire > 0.0) {
            rhtest = (6.0 / 4.0) * (float)(Volume[C2S]) / rdesire;
            sinter3d(C2S, C3S, rhtest);
            if (Verbose)
              fprintf(Logfile, "\nOut of sinter3d: C2S,C3S");
          }
        }
      }
    }
  }

  /***
   *    Third filtering between aluminates and alkali sulfates defines
   *    the boundaries between aluminates and alkali sulfate phases
   *    But only need to go through this if there
   *    are some alkali sulfates in the cement clinker
   ***/

  if ((alumdo == 1) && ((Volf[K2SO4] + Volf[NA2SO4]) > 0.0)) {

    /***
     *    volin is fraction of aluminates composed of C3A and C4AF.
     ***/

    volin = (Volf[C3A] + Volf[C4AF]) /
            (Volf[C3A] + Volf[C4AF] + Volf[K2SO4] + Volf[NA2SO4]);

    if (Verbose)
      fprintf(Logfile, "\nVolin is %f", volin);

    if (volin < 1.0 && volin > 0.0) {

      if (rand3d(alumval, K2SO4, filealum, nskip[3], volin, R, Filter, S, Xr)) {
        freedistrib3d();
        bailout("distrib3d", "Problem with rand3d");
        exit(1);
      }

      /***
       *    Second sintering.  Arrays volume and surface
       *    are defined in stat3d, and need to be refreshed
       *    because of prior sintering.
       ***/

      stat3d();
      rdesire = ((Surff[C3A] + Surff[C4AF]) /
                 (Surff[C3A] + Surff[C4AF] + Surff[K2SO4] + Surff[NA2SO4])) *
                (float)(Surface[alumval] + Surface[K2SO4]);

      /***
       *    Only perform sintering on the interface between
       *    the aluminate and alkali sulfate domains if the desired hydraulic
       *    radius for the aluminate domains is positive
       *    (this will almost certainly be the case every time)
       ***/

      if (Verbose)
        fprintf(Logfile, "\nRdesire is %f\n", rdesire);
      if (rdesire > 0.0) {

        /***
         *    Sinter the aluminate phases if the desired
         *    hydraulic radius for the aluminates is LESS than the
         *    current hydraulic radius for the aluminates ...
         ***/

        if ((int)rdesire < Surface[alumval]) {

          rhtest = (6.0 / 4.0) * (float)(Volume[alumval]) / rdesire;
          sinter3d(alumval, K2SO4, rhtest);
          if (Verbose)
            fprintf(Logfile, "\nOut of sinter3d: alumval,K2SO4");

          /***
           *    ... Otherwise, the hydraulic radius for aluminates is
           *    already less than or equal to the desired value.
           *    Therefore, treat the alkali sulfate domains as
           *    the solid and sinter them instead.  This effectively
           *    increases the hydraulic radius of the aluminate
           *    domains
           ***/

        } else {

          rdesire =
              ((Surff[K2SO4] + Surff[NA2SO4]) /
               (Surff[C3A] + Surff[C4AF] + Surff[K2SO4] + Surff[NA2SO4])) *
              (float)(Surface[alumval] + Surface[K2SO4]);

          if (Verbose)
            fprintf(Logfile, "\nRdesire is %f\n", rdesire);
          if (rdesire > 0.0) {
            rhtest = (6.0 / 4.0) * (float)(Volume[K2SO4]) / rdesire;
            sinter3d(K2SO4, alumval, rhtest);
            if (Verbose)
              fprintf(Logfile, "\nOut of sinter3d: K2SO4,alumval");
          }
        }
      }
    }
  }

  /***
   *    Fourth filtering to define the
   *    boundaries between K2SO4 and NA2SO4
   *    But only need to go through this if there
   *    is NA2SO4 in the cement clinker
   ***/

  if ((k2so4do == 1) && (Volf[NA2SO4] > 0.0)) {

    /* volin is fraction of K2SO4 in alkali sulfates */

    volin = Volf[K2SO4] / (Volf[K2SO4] + Volf[NA2SO4]);

    /***
     *    Only need to do this if both K2SO4 and
     *    NA2SO4 phases are in the clinker
     ***/

    if (Verbose)
      fprintf(Logfile, "\nVolin is %f", volin);
    if (volin < 1.0 && volin > 0.0) {

      if (rand3d(K2SO4, NA2SO4, filek2so4, nskip[4], volin, R, Filter, S, Xr)) {
        freedistrib3d();
        bailout("distrib3d", "Problem with rand3d");
        exit(1);
      }

      /***
       *    Fourth sintering, this time on the
       *    interface between K2SO4 and NA2SO4 domains.
       *    Arrays volume and surface are defined in stat3d,
       *    and need to be refreshed from prior sintering.
       ***/

      stat3d();
      if (Verbose)
        fprintf(Logfile, "\nOut of stat3d");
      rdesire = (Surff[K2SO4] / (Surff[K2SO4] + Surff[NA2SO4])) *
                (float)(Surface[K2SO4] + Surface[NA2SO4]);

      /***
       *    Only perform sintering on the interface between
       *    the K2SO4 and NA2SO$ domains if the desired hydraulic
       *    radius for the K2SO4 domains is positive
       *    (this will almost certainly be the case every time)
       ***/

      if (Verbose)
        fprintf(Logfile, "\nRdesire is %f\n", rdesire);
      if (rdesire > 0.0) {

        /***
         *    Sinter the K2SO4 phases if the desired
         *    hydraulic radius for the K2SO4 is LESS than the
         *    current hydraulic radius for the K2SO4 ...
         ***/

        if ((int)rdesire < Surface[K2SO4]) {

          rhtest = (6.0 / 4.0) * (float)(Volume[K2SO4]) / rdesire;
          sinter3d(K2SO4, NA2SO4, rhtest);
          if (Verbose)
            fprintf(Logfile, "\nOut of sinter3d: K2SO4,NA2SO4");

          /***
           *    ... Otherwise, the hydraulic radius for K2SO4 is
           *    already less than or equal to the desired value.
           *    Therefore, treat the NA2SO4 domains as
           *    the solid and sinter them instead.  This effectively
           *    increases the hydraulic radius of the K2SO4
           *    domains
           ***/

        } else {

          rdesire = (Surff[NA2SO4] / (Surff[K2SO4] + Surff[NA2SO4])) *
                    (float)(Surface[NA2SO4] + Surface[K2SO4]);

          if (Verbose)
            fprintf(Logfile, "\nRdesire is %f\n", rdesire);
          if (rdesire > 0.0) {
            rhtest = (6.0 / 4.0) * (float)(Volume[NA2SO4]) / rdesire;
            sinter3d(NA2SO4, K2SO4, rhtest);
            if (Verbose)
              fprintf(Logfile, "\nOut of sinter3d: NA2SO4,K2SO4");
            fflush(Logfile);
          }
        }
      }
    }
  }

  /***
   *    Fifth (final) filtering to define the
   *    boundaries between C3A and C4AF
   ***/

  /* volin is fraction of aluminates composed of phase alumval */

  volin = Volf[alumval] / (Volf[C4AF] + Volf[C3A]);
  alum2 = C3A;
  if (alumval == C3A)
    alum2 = C4AF;

  /***
   *    Only need to do this if both aluminate and
   *    ferrite phases are in the clinker
   ***/

  if (Verbose)
    fprintf(Logfile, "\nVolin is %f", volin);
  if (volin < 1.0 && volin > 0.0) {

    if (rand3d(alumval, alum2, filec34a, nskip[5], volin, R, Filter, S, Xr)) {
      freedistrib3d();
      bailout("distrib3d", "Problem with rand3d");
      exit(1);
    }

    /***
     *    Fifth (final) sintering, this time on the
     *    interface between aluminate and ferrite domains.
     *    Arrays volume and surface are defined in stat3d,
     *    and need to be refreshed from prior sintering.
     ***/

    stat3d();
    if (Verbose)
      fprintf(Logfile, "\nOut of stat3d");

    if (alumval == C4AF) {

      rdesire = (Surff[C4AF] / (Surff[C3A] + Surff[C4AF])) *
                (float)(Surface[C3A] + Surface[C4AF]);

      /***
       *    Only perform sintering on the interface between
       *    the C3A and C4AF domains if the desired hydraulic
       *    radius for the C4AF domains is positive
       *    (this will almost certainly be the case every time)
       ***/

      if (rdesire > 0.0) {

        /***
         *    Sinter the C4AF phase if the desired
         *    hydraulic radius for C4AF is LESS than the
         *    current hydraulic radius for C4AF ...
         ***/

        if ((int)rdesire < Surface[C4AF]) {

          rhtest = (6.0 / 4.0) * (float)(Volume[C4AF]) / rdesire;
          sinter3d(C4AF, C3A, rhtest);

          /***
           *    ... Otherwise, the hydraulic radius for C4AF is
           *    already less than or equal to the desired value.
           *    Therefore, treat the C3A domains as
           *    the solid and sinter them instead.  This effectively
           *    increases the hydraulic radius of the C4AF
           *    domains
           ***/

        } else {

          rdesire = (Surff[C3A] / (Surff[C3A] + Surff[C4AF])) *
                    (float)(Surface[C3A] + Surface[C4AF]);

          if (rdesire > 0.0) {
            rhtest = (6.0 / 4.0) * (float)(Volume[C3A]) / rdesire;
            sinter3d(C3A, C4AF, rhtest);
          }
        }
      }

    } else {

      /***
       *    The majority Al-containing phase is C3A instead
       *    of C4AF
       ***/

      rdesire = (Surff[C3A] / (Surff[C3A] + Surff[C4AF])) *
                (float)(Surface[C3A] + Surface[C4AF]);

      /***
       *    Only perform sintering on the interface between
       *    the C3A and C4AF domains if the desired hydraulic
       *    radius for the C3A domains is positive
       *    (this will almost certainly be the case every time)
       ***/

      if (rdesire > 0.0) {

        /***
         *    Sinter the C3A phase if the desired
         *    hydraulic radius for C3A is LESS than the
         *    current hydraulic radius for C3A ...
         ***/

        if ((int)rdesire < Surface[C3A]) {

          rhtest = (6.0 / 4.0) * (float)(Volume[C3A]) / rdesire;
          sinter3d(C3A, C4AF, rhtest);

          /***
           *    ... Otherwise, the hydraulic radius for C3A is
           *    already less than or equal to the desired value.
           *    Therefore, treat the C4AF domains as
           *    the solid and sinter them instead.  This effectively
           *    increases the hydraulic radius of the C3A
           *    domains
           ***/

        } else {

          rdesire = (Surff[C4AF] / (Surff[C3A] + Surff[C4AF])) *
                    (float)(Surface[C3A] + Surface[C4AF]);

          if (rdesire > 0.0) {
            rhtest = (6.0 / 4.0) * (float)(Volume[C4AF]) / rdesire;
            sinter3d(C4AF, C3A, rhtest);
          }
        }
      }
    }
  }

  fprintf(Logfile,
          "\nDone with distributing clinker phases.  Freeing memory now.");
  fflush(Logfile);

  /* Free up the dynamically allocated memory */

  freedistrib3d();

  fprintf(Logfile, "\n=== DEBUG: About to return from distrib3d() ===");
  fflush(Logfile);

  /* Check stack canary before return */
  if (stack_canary != 0xDEADBEEF) {
    fprintf(Logfile,
            "\n!!! STACK CORRUPTION DETECTED: canary = 0x%lx (expected "
            "0xDEADBEEF) !!!",
            stack_canary);
    fflush(Logfile);
  } else {
    fprintf(Logfile, "\n=== DEBUG: Stack canary intact, safe to return ===");
    fflush(Logfile);
  }

  /* WORKAROUND: Use longjmp instead of return to bypass corrupted return
   * address */
  fprintf(Logfile,
          "\n=== DEBUG: Using longjmp to bypass return address corruption ===");
  fflush(Logfile);

  /* Set global success flag and jump back to main */
  distrib3d_success = 1;
  longjmp(distrib3d_jmpbuf, 1);

  /* This line should never be reached */
  fprintf(stderr,
          "\n!!! ERROR line 5568: longjmp failed, trying normal return !!!");
  fflush(stderr);
  return (0);
}

/***
 *    maketemp
 *
 *    Routine to create a template for the sphere of
 *    interest of radius size to be used in
 *    curvature evaluation
 *
 *     Arguments:    int size (the radius of the sphere)
 *     Returns:    int number of pixels in sphere
 *
 *    Calls:        no other routines
 *    Called by:    runsint
 ***/
int maketemp(int size) {
  int icirc, xval, yval, zval;
  float xtmp, ytmp, dist;

  /***
   *    Determine and store the locations of all
   *    pixels in the 3-D sphere
   ***/

  icirc = 0;
  for (xval = (-size); xval <= size; xval++) {

    xtmp = (float)(xval * xval);
    for (yval = (-size); yval <= size; yval++) {

      ytmp = (float)(yval * yval);
      for (zval = (-size); zval <= size; zval++) {

        dist = sqrt(xtmp + ytmp + (float)(zval * zval));

        if (dist <= ((float)size + 0.5)) {

          Xsph[icirc] = xval;
          Ysph[icirc] = yval;
          Zsph[icirc] = zval;
          icirc++;

          if (icirc >= MAXSPH) {
            freedistrib3d();
            bailout("distrib3d", "Too many elements in template");
            exit(1);
          }
        }
      }
    }
  }

  /***
   *    Return the number of pixels contained in
   *    sphere of radius (size+0.5)
   ***/

  return (icirc);
}

/***
 *    phcount
 *
 *    Routine to count phase fractions (porosity
 *    and solids)
 *
 *     Arguments:    None
 *     Returns:    Nothing
 *
 *    Calls:        no other routines
 *    Called by:    main program
 ***/
void phcount(void) {
  int npore, nsolid[MAXNUMPHASES];
  int ix, iy, iz;

  npore = 0;
  for (ix = 1; ix < MAXNUMPHASES; ix++) {
    nsolid[ix] = 0;
  }

  /* Check all pixels in the 3-D system */

  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {

        if (Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] == 0) {
          npore++;
        } else {
          nsolid[Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)]]++;
        }
      }
    }
  }

  fprintf(Logfile, "Pores are: %d \n", npore);
  fprintf(Logfile, "Solids are: %d %d %d %d %d %d\n", nsolid[1], nsolid[2],
          nsolid[3], nsolid[4], nsolid[5], nsolid[6]);
}

/***
 *    surfpix
 *
 *    Routine to return number of surface faces
 *    exposed to porosity for pixel located at
 *    coordinates (xin,yin,zin)
 *
 *     Arguments:    int coordinates (xin,yin,zin)
 *     Returns:    number of faces exposed to porosity
 *
 *    Calls:        no other routines
 *    Called by:    rhcalc
 ***/
int surfpix(int xin, int yin, int zin) {
  int npix, ix1, iy1, iz1;

  npix = 0;

  /***
   *    Check each of the six immediate neighbors
   *    using periodic boundary conditions
   ***/

  ix1 = xin - 1;
  if (ix1 < 0)
    ix1 += Xsyssize;
  if (Cemreal.val[getInt3dindex(Cemreal, ix1, yin, zin)] == POROSITY)
    npix++;

  ix1 = xin + 1;
  if (ix1 >= Xsyssize)
    ix1 -= Xsyssize;
  if (Cemreal.val[getInt3dindex(Cemreal, ix1, yin, zin)] == POROSITY)
    npix++;

  iy1 = yin - 1;
  if (iy1 < 0)
    iy1 += Ysyssize;
  if (Cemreal.val[getInt3dindex(Cemreal, xin, iy1, zin)] == POROSITY)
    npix++;

  iy1 = yin + 1;
  if (iy1 >= Ysyssize)
    iy1 -= Ysyssize;
  if (Cemreal.val[getInt3dindex(Cemreal, xin, iy1, zin)] == POROSITY)
    npix++;

  iz1 = zin - 1;
  if (iz1 < 0)
    iz1 += Zsyssize;
  if (Cemreal.val[getInt3dindex(Cemreal, xin, yin, iz1)] == POROSITY)
    npix++;

  iz1 = zin + 1;
  if (iz1 >= Zsyssize)
    iz1 -= Zsyssize;
  if (Cemreal.val[getInt3dindex(Cemreal, xin, yin, iz1)] == POROSITY)
    npix++;

  return (npix);
}

/***
 *    rhcalc
 *
 *    Routine to return the current hydraulic radius
 *    for phase phin
 *
 *    Arguments:    Integer phase id
 *    Returns:    Float hydraulic radius
 *
 *    Calls:        surfpix
 *    Called by:    runsint
 ***/
float rhcalc(int phin) {
  int ix, iy, iz;
  int porc, surfc;
  float rhval;

  porc = surfc = 0;

  /* Check all pixels in the 3-D volume */

  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {

        if (Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] == phin) {
          porc++;
          surfc += surfpix(ix, iy, iz);
        }
      }
    }
  }

  rhval = (float)(porc * 6.0 / (4.0 * (float)surfc));
  if (Verbose) {
    fprintf(Logfile, "Phase area count is %d \n", porc);
    fprintf(Logfile, "Phase surface count is %d \n", surfc);
    fprintf(Logfile, "Hydraulic radius is %f \n", rhval);
  }

  return (rhval);
}

/***
 *    countem
 *
 *    Routine to return the count of pixels, within
 *    a spherical template, that are of phase phin
 *    or porosity (phase POROSITY)
 *
 *    Arguments:    Integer pixel coordinates and phase id
 *    Returns:    Integer count of pixels within template that
 *                    are phase phin
 *
 *    Calls:        checkbc
 *    Called by:    sysinit
 ***/
int countem(int xp, int yp, int zp, int phin) {
  int xc, yc, zc;
  int cumnum, ic;

  cumnum = 0;

  for (ic = 0; ic < Nsph; ic++) {

    xc = xp + Xsph[ic];
    yc = yp + Ysph[ic];
    zc = zp + Zsph[ic];

    /* Use periodic boundaries */

    xc += checkbc(xc, Xsyssize);
    yc += checkbc(yc, Ysyssize);
    zc += checkbc(zc, Zsyssize);

    if ((xc != xp) || (yc != yp) || (zc != zp)) {

      if ((Cemreal.val[getInt3dindex(Cemreal, xc, yc, zc)] == phin) ||
          (Cemreal.val[getInt3dindex(Cemreal, xc, yc, zc)] == POROSITY)) {

        cumnum++;
      }
    }
  }

  return (cumnum);
}

/***
 *    sysinit
 *
 *    Routine to initialize system by determining the
 *    local curvature of all phase ph1 and ph2 pixels
 *
 *    Arguments:    Phase ids of phase 1 and phase 2
 *    Returns:    Nothing
 *
 *    Calls:        countem
 *    Called by:    runsint
 *
 ***/
void sysinit(int ph1, int ph2) {
  int count, xl, yl, zl;
  char buff[MAXSTRING];

  count = 0;

  /* Process all pixels in the 3-D box */

  for (zl = 0; zl < Zsyssize; zl++) {
    for (yl = 0; yl < Ysyssize; yl++) {
      for (xl = 0; xl < Xsyssize; xl++) {

        /***
         *    Determine local curvature.  For phase 1,
         *    want to determine number of porosity
         *    pixels (phase = POROSITY) in
         *    immediate neighborhood
         ***/

        if (Cemreal.val[getInt3dindex(Cemreal, xl, yl, zl)] == ph1) {
          count = countem(xl, yl, zl, POROSITY);
        }

        /***
         *    For phase 2, want to determine number
         *    of either porosity OR phase 2 pixels in
         *    immediate neighborhood
         ***/

        if (Cemreal.val[getInt3dindex(Cemreal, xl, yl, zl)] == ph2) {
          count = countem(xl, yl, zl, ph2);
        }

        if ((count < 0) || (count >= Nsph)) {
          freedistrib3d();
          sprintf(buff, "Curvature count = %d, Nsph = %d", count, Nsph);
          bailout("distrib3d", buff);
          exit(1);
        }

        /***
         *    Case where we have a ph1 surface pixel
         *    with non-zero local curvature
         ***/

        if ((count >= 0) &&
            (Cemreal.val[getInt3dindex(Cemreal, xl, yl, zl)] == ph1)) {

          Curvature[xl][yl][zl] = count;

          /* Update solid curvature histogram */

          Nsolid[count]++;
        }

        /***
         *    Case where we have a ph2 surface pixel
         ***/

        if ((count >= 0) &&
            (Cemreal.val[getInt3dindex(Cemreal, xl, yl, zl)] == ph2)) {

          Curvature[xl][yl][zl] = count;

          /* Update air curvature histogram */

          Nair[count]++;
        }
      }
    }

    /* end of xl loop */
  }

  return;
}

/***
 *    sysscan
 *
 *    Routine to scan system and determine Nsolid (ph2)
 *    and Nair (ph1) histograms based on the values in
 *    phase and curvature arrays
 *
 *    Arguments:    Phase ids of phase 1 (solid) and
 *                    phase 2 ("air")
 *    Returns:    Nothing
 *
 *    Calls:        no other routines
 *    Called by:    runsint
 *
 ***/
void sysscan(int ph1, int ph2) {
  int xd, yd, zd, curvval;
  char buff[MAXSTRING];

  /* Scan all pixels in 3-D system */

  for (zd = 0; zd < Zsyssize; zd++) {
    for (yd = 0; yd < Ysyssize; yd++) {
      for (xd = 0; xd < Xsyssize; xd++) {

        curvval = Curvature[xd][yd][zd];

        if ((curvval < 0) || (curvval >= Nsph)) {
          sprintf(buff, "Curvature = %d, Nsph = %d", curvval, Nsph);
          freedistrib3d();
          bailout("distrib3d", buff);
          exit(1);
        }

        if (Cemreal.val[getInt3dindex(Cemreal, xd, yd, zd)] == ph2) {
          Nair[curvval]++;
        } else if (Cemreal.val[getInt3dindex(Cemreal, xd, yd, zd)] == ph1) {
          Nsolid[curvval]++;
        }
      }
    }
  }

  return;
}

/***
 *    procsol
 *
 *    Routine to return how many bins of the solid
 *    curvature histogram to use to accommodate
 *    nsearch pixels moving.  Want to use highest
 *    values first.
 *
 *    Arguments:    Int number of pixels to move
 *    Returns:    Top valfound bins of histogram to use
 *
 *    Calls:        no other routines
 *    Called by:    movepix
 *
 ***/
int procsol(int nsearch) {
  int valfound, i, stop;
  int nsofar;

  /* search histogram from top down until cumulative count */
  /* exceeds nsearch */

  if (Verbose)
    fprintf(Logfile, "\nIn procsol now...");
  valfound = Nsph - 1;
  nsofar = stop = 0;

  for (i = (Nsph - 1); ((i >= 0) && (!stop)); i--) {

    nsofar += Nsolid[i];
    if (nsofar > nsearch) {
      valfound = i;
      stop = 1;
    }
  }

  return (valfound);
}

/***
 *    procair
 *
 *    Routine to return how many bins of the "air"
 *    curvature histogram to use to accommodate
 *    nsearch pixels moving.  Want to use lowest
 *    values first.
 *
 *    Arguments:    Int number of pixels to move
 *    Returns:    Top valfound bins of histogram to use
 *
 *    Calls:        no other routines
 *    Called by:    movepix
 *
 ***/
int procair(int nsearch) {
  int valfound, i, stop;
  int nsofar;

  /* search histogram from top down until cumulative count */
  /* exceeds nsearch */

  if (Verbose)
    fprintf(Logfile, "\nIn procair now...");
  valfound = nsofar = stop = 0;

  for (i = 0; ((i < Nsph) && (!stop)); i++) {

    nsofar += Nair[i];
    if (nsofar > nsearch) {
      valfound = i;
      stop = 1;
    }
  }

  return (valfound);
}

/***
 *    movepix
 *
 *    Routine to move requested number of pixels (ntomove)
 *    from highest curvature ph1 sites to lowest curvature
 *    ph2 sites
 *
 *    Arguments:    Int phase id for phases 1 and 2
 *            Long Int number of pixels to move
 *
 *    Returns:    Int flag indicating function is done
 *                    = 1 if desired Rh achieved
 *                    = 0 if equilibrium was reached
 *                        before Rh could be reached
 *
 *    Calls:        procsol and procair
 *    Called by:    runsint
 *
 ***/
int movepix(int ntomove, int ph1, int ph2) {
  register int xp, yp, zp;
  int count1, count2, ntot, countc, i;
  int cmin, cmax, cfg, alldone;
  int nsolc, nairc, nsum, nsolm, nairm, nst1, nst2, next1, next2;
  float pck, plsol, plair;

  if (Verbose)
    fprintf(Logfile, "\nIn Movepix now...");
  alldone = 0;

  /***
   *    Determine critical bin values for removal
   *    of ph2 pixels
   ***/

  count1 = procsol(ntomove);
  nsum = cfg = 0;
  cmax = count1;

  for (i = Nsph - 1; i > count1; i--) {

    if ((Nsolid[i] > 0) && (!cfg)) {
      cfg = 1;
      cmax = i;
    }

    nsum += Nsolid[i];
  }

  /***
   *    Don't need to move all the ph1 pixels with
   *    this value of curvature, so determine
   *    movement probability for all ph1 pixels having
   *    curvature in this bin of the Nsolid histogram
   ***/

  plsol = (float)(ntomove - nsum) / (float)Nsolid[count1];
  next1 = ntomove - nsum;
  nst1 = Nsolid[count1];

  /***
   *    Determine critical bin values for removal
   *    of ph2 pixels
   ***/

  count2 = procair(ntomove);
  nsum = cfg = 0;
  cmin = count2;

  for (i = 0; i < count2; i++) {
    if ((Nair[i] > 0) && (!cfg)) {
      cfg = 1;
      cmin = i;
    }

    nsum += Nair[i];
  }

  /***
   *    Don't need to move all the ph2 pixels with
   *    this value of curvature, so determine
   *    movement probability for all ph2 pixels having
   *    curvature in this bin of the Nsolid histogram
   ***/

  plair = (float)(ntomove - nsum) / (float)Nair[count2];
  next2 = ntomove - nsum;
  nst2 = Nair[count2];

  /***
   *    Check to see if equilibrium has been reached ---
   *    if so, then no further increase in hydraulic
   *    radius is possible
   ***/

  if (cmin >= cmax) {
    alldone = 1;
    if (Verbose)
      fprintf(Logfile, "Stopping - at equilibrium \ncmin- %d  cmax- %d \n",
              cmin, cmax);
    return (alldone);
  }

  /* Initialize counters for performing sintering */

  ntot = nsolc = nairc = nsolm = nairm = 0;

  /* Now process each pixel in turn */

  for (zp = 0; zp < Zsyssize; zp++) {
    for (yp = 0; yp < Ysyssize; yp++) {
      for (xp = 0; xp < Xsyssize; xp++) {

        countc = Curvature[xp][yp][zp];

        /* Handle ph1 case first */

        if (Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] == ph1) {

          if (countc > count1) {

            /***
             *    Definitely convert from ph1 to ph2
             ***/

            Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] = ph2;

            /* Update appropriate histogram cells */

            Nsolid[countc]--;
            Nair[countc]++;
            ntot++;

            /* Store the location of the modified pixel */

          } else if (countc == count1) {

            /***
             *    Borderline curvature... move based on
             *    probability
             ***/

            nsolm++;

            /***
             *    Generate probability for pixel
             *    being removed
             ***/

            pck = ran1(Seed);
            if ((pck < 0) || (pck > 1.0))
              pck = 1.0;

            if (((pck < plsol) && (nsolc < next1)) ||
                ((nst1 - nsolm) < (next1 - nsolc))) {

              nsolc++;

              /* Convert ph1 pixel to ph2 */

              Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] = ph2;

              /* Update appropriate histogram cells */

              Nsolid[count1]--;
              Nair[count1]++;

              /* Store the location of the modified pixel */

              ntot++;
            }
          }

          /* Handle phase 2 case here */

        } else if (Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] == ph2) {

          if (countc < count2) {

            /***
             *    Definitely convert ph2 pixel to ph1
             ***/

            Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] = ph1;

            /* Update appropriate histogram cells */

            Nsolid[countc]++;
            Nair[countc]--;

            /* Store the location of the modified pixel */

            ntot++;

          } else if (countc == count2) {

            /***
             *    Borderline curvature... move based on
             *    probability
             ***/

            nairm++;

            /***
             *    Generate probability for pixel
             *    being placed
             ***/

            pck = ran1(Seed);
            if ((pck < 0) || (pck > 1.0))
              pck = 1.0;

            if (((pck < plair) && (nairc < next2)) ||
                ((nst2 - nairm) < (next2 - nairc))) {

              nairc++;

              /* Convert ph2 to ph1 */

              Cemreal.val[getInt3dindex(Cemreal, xp, yp, zp)] = ph1;

              /* Update appropriate histogram cells */

              Nsolid[count2]++;
              Nair[count2]--;

              /* Store the location of the modified pixel */

              ntot++;
            }
          }
        }

      } /* end of zp loop */
    } /* end of yp loop */
  } /* end of xloop */

  if (Verbose)
    fprintf(Logfile, "ntot is %d \n", ntot);
  return (alldone);
}

/***
 *    sinter3d
 *
 *    Routine to execute user-input number of cycles
 *    of sintering algorithm
 *
 *    Arguments:    Int phase id for phases 1 and 2
 *                Float target value of hydraulic radius
 *
 *    Returns:    Nothing
 *
 *    Calls:        maketemp, rhcalc, sysinit, sysscan, and movepix
 *    Called by:    main routine
 *
 ***/
void sinter3d(int ph1id, int ph2id, float rhtarget) {
  int natonce, i, j, rflag, equilibrated;
  int curvsum1, curvsum2, pixsum1, pixsum2;
  float rhnow, avecurv1, avecurv2;

  /***
   *    Initialize the solid and air count histograms
   ***/

  for (i = 0; i < Hsize_s; i++) {
    Nsolid[i] = 0;
    Nair[i] = 0;
  }

  /* Obtain needed user input */

  natonce = MAX2MOVE * Isizemag;

  Nsph = maketemp(Tradius);

  if (Verbose) {
    fprintf(Logfile, "Nsph is %d \n", Nsph);
    fprintf(Logfile, "Checking stats for C3S...");
    stat3d();
    fflush(Logfile);
  }

  rflag = 0; /* always initialize system */
  if (!rflag) {
    if (Verbose)
      fprintf(Logfile, "Entering sysinit now...");
    sysinit(ph1id, ph2id);
    if (Verbose)
      fprintf(Logfile, "\nOut of sysinit now...");
  } else {
    sysscan(ph1id, ph2id);
  }

  i = 0;
  if (Verbose) {
    fprintf(Logfile, "Entering rhcalc now...");
    fprintf(Logfile, "Checking stats for C3S...");
    stat3d();
    fflush(Logfile);
  }

  rhnow = rhcalc(ph1id);
  if (Verbose)
    fprintf(Logfile, "\nOut of rhcalc now...\nRhnow = %f, Rhtarget = %f\n",
            rhnow, rhtarget);
  while ((rhnow < rhtarget) && (i < MAXCYC)) {

    i++;
    if (Verbose)
      fprintf(Logfile, "Now: %f  Target: %f \nCycle: %d \n", rhnow, rhtarget,
              i);
    equilibrated = movepix(natonce, ph1id, ph2id);

    if (Verbose) {
      fprintf(Logfile, "Out of movepix.");
      fprintf(Logfile, "Checking stats for C3S...");
      stat3d();
      fflush(Logfile);
    }

    /***
     *    If equilibrium is reached, then return
     *    to calling routine
     ***/

    if (equilibrated)
      return;

    curvsum1 = curvsum2 = pixsum1 = pixsum2 = 0;

    /* Determine average curvatures for phid1 and phid2 */

    for (j = 0; j <= Nsph; j++) {
      pixsum1 += Nsolid[j];
      curvsum1 += (j * Nsolid[j]);
      pixsum2 += Nair[j];
      curvsum2 += (j * Nair[j]);
    }

    avecurv1 = ((float)curvsum1) / ((float)pixsum1);
    avecurv2 = ((float)curvsum2) / ((float)pixsum2);
    if (Verbose)
      fprintf(Logfile, "Ave. solid curvature: %f \nAve. air curvature: %f \n",
              avecurv1, avecurv2);

    rhnow = rhcalc(ph1id);
    if (Verbose) {
      fprintf(Logfile, "Out of rhcalc.");
      fprintf(Logfile, "Checking stats for C3S...");
      stat3d();
      fflush(Logfile);
    }
  }

  return;
}

/***
 *    stat3d
 *
 *    Routine to compute spatial statistics on the
 *    3D microstructure
 *
 *    Arguments:    None
 *    Returns:    Nothing
 *
 *    Calls:        no other routines
 *    Called by:    main routine
 *
 ***/
void stat3d(void) {
  int valin, ix, iy, iz, ix1, iy1, iz1, k;
  int voltot, surftot;

  for (ix = POROSITY; ix <= MAXNUMPHASES - 8; ix++) {
    Volume[ix] = Surface[ix] = 0;
  }

  /* Read in image and accumulate volume totals */

  ix1 = iy1 = iz1 = 0;
  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {
        valin = Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
        Volume[valin]++;
        if (valin != POROSITY && valin != EMPTYP && valin != EMPTYDP &&
            valin != CRACKP && valin != DRIEDP) {

          /***
           *    Check six neighboring pixels
           *    for porosity
           ***/

          for (k = 1; k <= 6; k++) {

            switch (k) {
            case 1:
              ix1 = ix - 1;
              if (ix1 < 0)
                ix1 += Xsyssize;
              iy1 = iy;
              iz1 = iz;
              break;
            case 2:
              ix1 = ix + 1;
              if (ix1 >= Xsyssize)
                ix1 -= Xsyssize;
              iy1 = iy;
              iz1 = iz;
              break;
            case 3:
              iy1 = iy - 1;
              if (iy1 < 0)
                iy1 += Ysyssize;
              ix1 = ix;
              iz1 = iz;
              break;
            case 4:
              iy1 = iy + 1;
              if (iy1 >= Ysyssize)
                iy1 -= Ysyssize;
              ix1 = ix;
              iz1 = iz;
              break;
            case 5:
              iz1 = iz - 1;
              if (iz1 < 0)
                iz1 += Zsyssize;
              iy1 = iy;
              ix1 = ix;
              break;
            case 6:
              iz1 = iz + 1;
              if (iz1 >= Zsyssize)
                iz1 -= Zsyssize;
              iy1 = iy;
              ix1 = ix;
              break;
            default:
              break;
            }

            if (Cemreal.val[getInt3dindex(Cemreal, ix1, iy1, iz1)] ==
                POROSITY) {
              Surface[valin]++;
            }
          }
        }
      }
    }
  }

  if (Verbose) {
    fprintf(Logfile, "Phase    Volume      Surface     Volume    Surface \n");
    fprintf(Logfile, " ID      count        count      fraction  fraction \n");

    /* Only include clinker phases in surface area fraction calculation */

    surftot = Surface[C3S] + Surface[C2S] + Surface[C3A] + Surface[C4AF] +
              Surface[K2SO4] + Surface[NA2SO4];
    voltot = Volume[C3S] + Volume[C2S] + Volume[C3A] + Volume[C4AF] +
             Volume[K2SO4] + Volume[NA2SO4];

    fprintf(Logfile, "  %d    %8d     %8d  \n", POROSITY, Volume[POROSITY],
            Surface[POROSITY]);

    for (k = C3S; k <= NA2SO4; k++) {
      fprintf(Logfile, "  %d    %8d     %8d     %.5f   %.5f\n", k, Volume[k],
              Surface[k], (double)Volume[k] / (double)voltot,
              (double)Surface[k] / (double)surftot);
    }

    fprintf(Logfile, "Total  %8d     %8d\n\n\n", voltot, surftot);
  }

  return;
}

/***
 *    rand3d
 *
 *    Routine to generate a Gaussian random noise image and
 *    then filter it according to the 2-point correlation function
 *    for the phase of interest
 *
 *    Arguments:    Phase ID in, Phase ID out, correlation filename,
 *                int number of strings to skip (due to possible
 *                header line for resolution information),
 *                float xpt=volume fraction, r[] is the array of
 *                radius values in corr file, filter[][][] is the
 *                3D filter array, s[] is the value of the correlation
 *                function at a given (radial) position, xr[] is
 *                the float version of r[]
 *
 *    Returns:    0 if normal execution, non-zero if error occurred
 *
 *    Calls:        no other routines
 *    Called by:    main routine
 *
 ***/
int rand3d(int phasein, int phaseout, char filecorr[MAXSTRING], int nskip,
           float xpt, int *r, float ***filter, float *s, float *xr) {
  register int i, j, k, ix, iy, iz;
  int done, step, ilo, ihi;
  int valin, pvalin, r1, r2, i1, i2, i3, j1, k1;
  int ido, iii, jjj, index;
  float s2, ss, sdiff, xtmp, ytmp, slope, intercept, diff;
  float val2, t1, t2, x1, x2, u1, xrad, resmax, resmin;
  float filval, radius, sect, sumtot, vcrit;
  int xtot;
  char buff[MAXSTRING], instring[MAXSTRING];
  FILE *corrfile;

  /***
   *    Create the Gaussian noise image
   ***/

  if (Verbose)
    fprintf(Logfile, "\nEntering rand3d...\nVolin = %f", xpt);

  i1 = i2 = i3 = 0;

  for (i = 0; i < Xsyssize * Ysyssize * Zsyssize / 2; i++) {

    u1 = ran1(Seed);
    t1 = PI2 * ran1(Seed);
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

  if ((corrfile = fopen(filecorr, "r")) == NULL) {
    fprintf(stderr, "ERROR line 6595 in distrib3d, fn. rand3d:\n");
    fprintf(stderr, "\n\tCannot open correlation function file");
    fprintf(stderr, "\n\tcalled %s.  Exiting now.", filecorr);
    fflush(stderr);
    return (1);
  }

  /*** Skip over resolution information if it is given ***/

  fprintf(Logfile, "\nIn rand3d, line 6032:  filecorr = %s, nskip = %d\n",
          filecorr, nskip);

  for (i = 1; i <= nskip; i++) {
    fscanf(corrfile, "%s", buff);
  }

  fscanf(corrfile, "%s", instring);
  fprintf(Logfile, "In rand3d, line 5969:  instring = %s\n", instring);
  ido = atoi(instring);
  fprintf(Logfile, "In rand3d, line 5971:  ido = %d\n", ido);

  if (Verbose)
    fprintf(Logfile,
            "\n\tNumber of points in correlation file is %d \n\tVolin %f\n",
            ido, xpt);

  /***
   *    When reading in the correlation file, must make
   *    the resolution of the correlation function
   *    compatible with the resolution of the system
   *    as specified by global variable Res
   ***/

  fprintf(Logfile, "In rand3d, line 5982, Fsize = %d\n", Fsize);
  for (i = 0; i < ido; i++) {
    fscanf(corrfile, "%s", instring);
    fprintf(Logfile, "In rand3d, line 5985, i = %d of %d:  instring = %s\n", i,
            ido, instring);
    valin = atoi(instring);
    fprintf(Logfile, "In rand3d, line 5987:  valin = %d\n", valin);
    fscanf(corrfile, "%s", instring);
    fprintf(Logfile, "In rand3d, line 5989, i = %d of %d:  instring = %s\n", i,
            ido, instring);
    val2 = atof(instring);
    fprintf(Logfile, "In rand3d, line 5991:  val2 = %f\n", val2);

    /***
     *    valin is the radial distance in micrometers.
     *    Convert it to pixels using Res and Corr_res
     ***/

    pvalin = (int)((((float)valin) * (Corr_res / Res)) + 0.40);
    /* r[pvalin] = (int)(((float)valin)*Corr_res); */
    if (pvalin >= 2 * Fsize)
      break;
    r[pvalin] = pvalin;
    s[pvalin] = val2;
    xr[pvalin] = (float)r[pvalin];
  }

  ido = i;
  fclose(corrfile);

  /***
   *    Now linearly interpolate the other values,
   *    depending on the value of Res
   ***/

  step = (int)(Corr_res / Res);
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
  if (Verbose)
    fprintf(Logfile, "\n\tss = %f  s2 = %f  sdiff = %f", ss, s2, sdiff);
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
          fprintf(stderr, "ERROR line 6697 in distrib3d, fn. rand3d:\n");
          fprintf(stderr, "\t%d and %d, %f and ", r1, r2, s[r1]);
          fprintf(stderr, "%f with xtmp of %f\n", s[r2], xtmp);
          fflush(stderr);
          return (3);
        }

        xrad = radius - r1;

        /***
         *    Interpolate the correlation function
         *    between the two values at r2 and r1, for
         *    which it is known, to estimate its value
         *    at some r for which r1 <= r <= r2
         *
         *    We also normalize the value of filter to
         *    the value of the correlation file at 0.
         ***/

        filval = s[r1] + (s[r2] - s[r1]) * xrad;
        filter[i][j][k] = (filval - s2) / sdiff;
      }
    }
  }

  /* Now filter the image, maintaining periodic boundaries */

  if (Verbose)
    fprintf(Logfile,
            "\n\tDone loading up the convolution matrix.\n\tVolin = %f", xpt);
  resmax = 0.0;
  resmin = 1.0;

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        Rres[i][j][k] = 0.0;

        /***
         *    Only perform the filtering within regions
         *    that are candidates for this phase
         ***/

        if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == phasein) {

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

  sect = (resmax - resmin) / ((float)Hsize_r);
  if (Verbose)
    fprintf(Logfile, "\n\tDone filtering image.\n\tVolin = %f\n\tSect is %f",
            xpt, sect);

  /***
   *    Now threshold the image by creating a histogram
   *    of the values of Rres[i][j][k] and determining
   *    a cutoff bin to define the phase
   **/

  for (i = 1; i <= Hsize_r; i++) {
    Sum[i] = 0;
  }

  xtot = 0;
  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        /***
         *    Only examine within regions
         *    that are candidates for this phase
         ***/

        if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == phasein) {
          xtot++;

          /***
           *    Find the bin number for this pixel and add
           *    the pixel to the statistics
           ***/

          index = 1 + (int)((Rres[i][j][k] - resmin) / sect);

          if (index > Hsize_r)
            index = Hsize_r;
          Sum[index]++;
        }
      }
    }
  }

  sumtot = vcrit = 0.0;
  done = 0;

  if (Verbose) {
    fprintf(Logfile,
            "\n\tDone thresholding first pass.\n\tVolin = %f, xtot = %d", xpt,
            xtot);
    fprintf(Logfile, "\n\tResmin = %f  Resmax = %f", resmin, resmax);
  }

  /* Determine which bin to choose for correct thresholding */

  for (i = 1; ((i <= Hsize_r) && (!done)); i++) {

    sumtot += (float)(((double)Sum[i]) / ((double)xtot));

    if (sumtot > xpt) { /* xpt is input to the function */

      ytmp = (float)i;
      vcrit = resmin + (resmax - resmin) * (ytmp - 0.5) / ((float)Hsize_r);
      done = 1;
    }
  }

  if (Verbose)
    fprintf(Logfile, "Critical volume fraction is %f\n\tVolin = %f", vcrit,
            xpt);

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == phasein) {

          if (Rres[i][j][k] > vcrit) {
            Cemreal.val[getInt3dindex(Cemreal, i, j, k)] = phaseout;
          }
        }
      }
    }
  }

  if (Verbose)
    fprintf(Logfile, "\n\tVolin = %f", xpt);
  return (0);
}

/***
 *    addonepixels
 *
 *     Function to manage the addition of one-pixel particles
 *    to the microstructure
 *
 *     Arguments:    None
 *
 *     Returns:    Exit status (0 is okay, 1 otherwise)
 *
 *    Calls:        addrand
 *    Called by:    main program
 ***/
int addonepixels(void) {
  register int i, j, k;
  int phtodo, onepixfloc, pheach, assignpartnum, numsizes, nplaced;
  int nadd, totclinkpix, totfapix, tot[NPHASES], target[NPHASES];
  int nleft, tottarget, numeach;
  float sizeeach;

  /***
   * One-pixel particles are assigned a particle number of zero
   ***/
  /* assignpartnum = 0; */

  /***
   * One-pixel particles are assigned a unique particle number
   ***/
  assignpartnum = 1;

  i = j = 1;

  /***
   *    Allow user to iteratively add one-pixel
   *    particles of various phases.  Typical application
   *    would be for addition of silica fume
   ***/

  for (phtodo = 0; phtodo < NPHASES; phtodo++) {

    /*
   fprintf(Logfile,"Should these particles flocculate to surfaces? No (0) or
   Yes (1):
    "); read_string(instring,sizeof(instring)); onepixfloc = atoi(instring);
    */
    onepixfloc = 0;

    nadd = Onepixnum[phtodo];
    fprintf(Logfile, "\nAdding %d of phase %d", nadd, phtodo);

    if (nadd > 0) {

      switch (phtodo) {
      case C3S:

        /****
         * Get total number of clinker pixels
         ****/
        totclinkpix = 0;
        for (i = 0; i < NPHASES; i++) {
          tot[i] = 0;
          target[i] = 0;
        }

        for (k = 0; k < Zsyssize; k++) {
          for (j = 0; j < Ysyssize; j++) {
            for (i = 0; i < Xsyssize; i++) {
              if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == C3S) {
                totclinkpix++;
                tot[C3S]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == C2S) {
                totclinkpix++;
                tot[C2S]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == C3A) {
                totclinkpix++;
                tot[C3A]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == C4AF) {
                totclinkpix++;
                tot[C4AF]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] ==
                         K2SO4) {
                totclinkpix++;
                tot[K2SO4]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] ==
                         NA2SO4) {
                totclinkpix++;
                tot[NA2SO4]++;
              }
            }
          }
        }

        /***
         * After adding one-pixel particles, there will
         * be this many cement pixels
         ***/

        totclinkpix += nadd;
        nleft = nadd;
        tottarget = 0;
        for (i = C3S; i <= NA2SO4; i++) {
          target[i] = (Volf[i] * nadd) + 0.5;
          /*
          target[i] = (int)((Volf[i]*(float)totclinkpix)
                         - (float)tot[i] + 0.5);
                         */
          if (target[i] < 0)
            target[i] = 0;
          tottarget += target[i];
        }

        /***
         * Normalize the targets
         ***/

        /*
        for (i = C3S; (i <= NA2SO4); i++) {

            target[i] = (int)(0.5 +
        ((float)(target[i]*nadd)/(float)tottarget));
        }

        tottarget = 0;
        for (i = C3S; (i <= NA2SO4); i++) {
            tottarget += target[i];
        }
        */

        for (i = C3S; (i <= NA2SO4) && (nleft > 0); i++) {

          if (Verbose) {
            fprintf(Logfile, "\t%d pixels of ", target[i]);
            switch (i) {
            case C3S:
              fprintf(Logfile, "C3S\n");
              break;
            case C2S:
              fprintf(Logfile, "C2S\n");
              break;
            case C3A:
              fprintf(Logfile, "C3A\n");
              break;
            case C4AF:
              fprintf(Logfile, "C4AF\n");
              break;
            case K2SO4:
              fprintf(Logfile, "K2SO4\n");
              break;
            case NA2SO4:
              fprintf(Logfile, "NA2SO4\n");
              break;
            default:
              fprintf(Logfile, "unrecognized phase\n");
              break;
            }
          }

          if (Dispdist == 1) {
            numsizes = 1;
            numeach = target[i];
            sizeeach = 0.5;
            pheach = i;
            nplaced = genparticles(numsizes, &numeach, &sizeeach, &pheach);
            if (nplaced < numeach) {
              numeach -= (nplaced);
              fprintf(Logfile,
                      "\nCould not add all one-pixel particles dispersed.");
              fprintf(Logfile,
                      "\nAdding %d extra random locations to make up...",
                      numeach);
              addrand(i, numeach, onepixfloc, assignpartnum);
            }
          } else {
            addrand(i, target[i], onepixfloc, assignpartnum);
          }
        }

        break;

      case FLYASH:

        /****
         * Get total number of fly ash particles
         ****/

        totfapix = 0;
        for (i = 0; i < NPHASES; i++) {
          tot[i] = 0;
          target[i] = 0;
        }

        for (k = 0; k < Zsyssize; k++) {
          for (j = 0; j < Ysyssize; j++) {
            for (i = 0; i < Xsyssize; i++) {
              if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == ASG) {
                totfapix++;
                tot[ASG]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] == CAS2) {
                totfapix++;
                tot[CAS2]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] ==
                         FAC3A) {
                totfapix++;
                tot[FAC3A]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] ==
                         CACL2) {
                totfapix++;
                tot[CACL2]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] ==
                         AMSIL) {
                totfapix++;
                tot[AMSIL]++;
              } else if (Cemreal.val[getInt3dindex(Cemreal, i, j, k)] ==
                         ANHYDRITE) {
                totfapix++;
                tot[ANHYDRITE]++;
              }
            }
          }
        }

        /***
         * After adding one-pixel particles, there will
         * be this many fly ash one-pixel particles
         ***/

        totfapix += nadd;
        nleft = nadd;
        tottarget = 0;
        for (i = 0; i < 6; i++) {
          switch (i) {
          case 0:
            j = ASG;
            break;
          case 1:
            j = CAS2;
            break;
          case 2:
            j = FAC3A;
            break;
          case 3:
            j = CACL2;
            break;
          case 4:
            j = AMSIL;
            break;
          case 5:
            j = ANHYDRITE;
            break;
          default:
            break;
          }
          target[j] = (int)((Volf[j] * (float)totfapix) - (float)tot[j] + 0.5);
          tottarget += target[j];
        }

        /***
         * Normalize the targets
         ***/

        for (i = 0; i < 6; i++) {
          switch (i) {
          case 0:
            j = ASG;
            break;
          case 1:
            j = CAS2;
            break;
          case 2:
            j = FAC3A;
            break;
          case 3:
            j = CACL2;
            break;
          case 4:
            j = AMSIL;
            break;
          case 5:
            j = ANHYDRITE;
            break;
          default:
            break;
          }

          target[j] =
              (int)(0.5 + ((float)(target[j] * nadd) / (float)tottarget));
        }

        tottarget = 0;
        for (i = 0; i < 6; i++) {
          switch (i) {
          case 0:
            j = ASG;
            break;
          case 1:
            j = CAS2;
            break;
          case 2:
            j = FAC3A;
            break;
          case 3:
            j = CACL2;
            break;
          case 4:
            j = AMSIL;
            break;
          case 5:
            j = ANHYDRITE;
            break;
          default:
            break;
          }

          tottarget += target[j];
        }

        if (Verbose)
          fprintf(Logfile, "\nAdding %d fly ash pixels now...\n", tottarget);
        for (i = 0; (i < 6) && (nleft > 0); i++) {

          if (Verbose)
            fprintf(Logfile, "\t%d pixels of ", target[i]);
          switch (i) {
          case 0:
            if (Verbose)
              fprintf(Logfile, "ASG\n");
            j = ASG;
            break;
          case 1:
            if (Verbose)
              fprintf(Logfile, "CAS2\n");
            j = CAS2;
            break;
          case 2:
            if (Verbose)
              fprintf(Logfile, "FAC3A\n");
            j = FAC3A;
            break;
          case 3:
            if (Verbose)
              fprintf(Logfile, "CACL2\n");
            j = CACL2;
            break;
          case 4:
            if (Verbose)
              fprintf(Logfile, "AMSIL\n");
            j = AMSIL;
            break;
          case 5:
            if (Verbose)
              fprintf(Logfile, "ANHYDRITE\n");
            j = ANHYDRITE;
            break;
          default:
            break;
          }

          if (Dispdist == 1) {
            numsizes = 1;
            numeach = target[j];
            sizeeach = 0.5;
            pheach = j;
            nplaced = genparticles(numsizes, &numeach, &sizeeach, &pheach);
            if (nplaced < numeach) {
              numeach -= (nplaced);
              fprintf(Logfile,
                      "\nCould not add all one-pixel particles dispersed.");
              fprintf(Logfile,
                      "\nAdding %d extra random locations to make up...",
                      numeach);
              addrand(j, numeach, onepixfloc, assignpartnum);
            }
          } else {
            addrand(j, target[j], onepixfloc, assignpartnum);
          }
        }

        break;

      default:
        if (Dispdist == 1) {
          numsizes = 1;
          numeach = nadd;
          sizeeach = 0.5;
          pheach = phtodo;
          nplaced = genparticles(numsizes, &numeach, &sizeeach, &pheach);
          if (nplaced < numeach) {
            numeach -= (nplaced);
            fprintf(Logfile,
                    "\nCould not add all one-pixel particles dispersed.");
            fprintf(Logfile, "\nAdding %d extra random locations to make up...",
                    numeach);
            addrand(phtodo, numeach, 0, assignpartnum);
          }
        } else {
          addrand(phtodo, nadd, 0, assignpartnum);
        }
        break;
      }
    }
  }

  return (0);
}

/***
 *    addrand
 *
 *     Add nneed one-pixel elements of phase randid at random
 *     locations in the microstructure
 *
 *     Arguments:    int phase id
 *                 int number to place
 *                 int flocculate (1) or not (0)
 *                 int whether or not to assign a particle number
 *
 *     Returns:    nothing
 *
 *    Calls:        no other routines
 *    Called by:    main program
 ***/
void addrand(int randid, int nneed, int onepixfloc, int assignpartnum) {
  int inc, ic, success, ix, iy, iz, dim, dir, newsite, oldval;

  /***
   *    Add number of requested phase pixels at
   *    random pore locations
   ***/

  for (ic = 1; ic <= nneed; ic++) {
    success = 0;

    while (!success) {

      ix = (int)((float)Xsyssize * ran1(Seed));
      iy = (int)((float)Ysyssize * ran1(Seed));
      iz = (int)((float)Zsyssize * ran1(Seed));

      if (ix == Xsyssize)
        ix = 0;
      if (iy == Ysyssize)
        iy = 0;
      if (iz == Zsyssize)
        iz = 0;

      if (Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] == POROSITY ||
          Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] == CRACKP) {
        oldval = Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
        Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] = randid;
        if (assignpartnum) {
          Npart++;
          Cement.val[getInt3dindex(Cement, ix, iy, iz)] = Npart;
        }
        success = 1;
        if (onepixfloc == 1) {
          /***
           * Flocculate this particle to a nearby surface
           * Pic a random direction to fly
           ***/
          dim = (int)(3.0 * ran1(Seed));
          dir = (int)(2.0 * ran1(Seed));
          inc = (dir == 0) ? 1 : -1;

          switch (dim) {
          case 0: /* X-direction flight */
            newsite = ix + inc;
            newsite += checkbc(newsite, Xsyssize);
            while ((newsite != ix) &&
                   ((Cemreal.val[getInt3dindex(Cemreal, newsite, iy, iz)] ==
                     POROSITY) ||
                    (Cemreal.val[getInt3dindex(Cemreal, newsite, iy, iz)] ==
                     CRACKP))) {
              newsite += inc;
              newsite += checkbc(newsite, Xsyssize);
            }
            if (newsite != ix) {
              newsite -= inc;
              newsite += checkbc(newsite, Xsyssize);
              Cemreal.val[getInt3dindex(Cemreal, newsite, iy, iz)] =
                  Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
              Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] = oldval;
              if (assignpartnum) {
                Cement.val[getInt3dindex(Cement, newsite, iy, iz)] =
                    Cement.val[getInt3dindex(Cement, ix, iy, iz)];
                Cement.val[getInt3dindex(Cement, ix, iy, iz)] = 0;
              }
            }
            break;
          case 1: /* Y-direction flight */
            newsite = iy + inc;
            newsite += checkbc(newsite, Ysyssize);
            while ((newsite != iy) &&
                   ((Cemreal.val[getInt3dindex(Cemreal, ix, newsite, iz)] ==
                     POROSITY) ||
                    (Cemreal.val[getInt3dindex(Cemreal, ix, newsite, iz)] ==
                     CRACKP))) {
              newsite += inc;
              newsite += checkbc(newsite, Ysyssize);
            }
            if (newsite != iy) {
              newsite -= inc;
              newsite += checkbc(newsite, Ysyssize);
              Cemreal.val[getInt3dindex(Cemreal, ix, newsite, iz)] =
                  Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
              Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] = oldval;
              if (assignpartnum) {
                Cement.val[getInt3dindex(Cement, ix, newsite, iz)] =
                    Cement.val[getInt3dindex(Cement, ix, iy, iz)];
                Cement.val[getInt3dindex(Cement, ix, iy, iz)] = 0;
              }
            }
            break;
          case 2: /* Z-direction flight */
            newsite = iz + inc;
            newsite += checkbc(newsite, Zsyssize);
            while ((newsite != iz) &&
                   ((Cemreal.val[getInt3dindex(Cemreal, ix, iy, newsite)] ==
                     POROSITY) ||
                    (Cemreal.val[getInt3dindex(Cemreal, ix, iy, newsite)] ==
                     CRACKP))) {
              newsite += inc;
              newsite += checkbc(newsite, Zsyssize);
            }
            if (newsite != iz) {
              newsite -= inc;
              newsite += checkbc(newsite, Zsyssize);
              Cemreal.val[getInt3dindex(Cemreal, ix, iy, newsite)] =
                  Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
              Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] = oldval;
              if (assignpartnum) {
                Cement.val[getInt3dindex(Cement, ix, iy, newsite)] =
                    Cement.val[getInt3dindex(Cement, ix, iy, iz)];
                Cement.val[getInt3dindex(Cement, ix, iy, iz)] = 0;
              }
            }
            break;
          case 3: /* Do nothing */
            break;
          }
        }
      }
    }
  }
  return;
}

/***
 *    freegenmic
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
void freegenmic(void) {
  register int i;

  if (Cement.val)
    free_Int3darray(&Cement);

  if (Cemreal.val)
    free_Int3darray(&Cemreal);

  if (Bbox.val)
    free_Int3darray(&Bbox);

  if (Particle)
    free_particlepointervector(Particle);

  for (i = 0; i < NSPHASES; i++) {
    if (Verbose) {
      if (Phase_shape[i].xg) {
        fprintf(Logfile, "\nFreeing Phase_shape[%d].xg vector...", i);
      } else {
        fprintf(Logfile, "\nPhase_shape[%d].xg vector is freed already", i);
      }
      fflush(Logfile);
    }
    if (Phase_shape[i].xg)
      free_fvector(Phase_shape[i].xg);

    if (Verbose) {
      if (Phase_shape[i].wg) {
        fprintf(Logfile, "\nFreeing Phase_shape[%d].wg vector...", i);
      } else {
        fprintf(Logfile, "\nPhase_shape[%d].wg vector is freed already", i);
      }
      fflush(Logfile);
    }
    if (Phase_shape[i].wg)
      free_fvector(Phase_shape[i].wg);
  }

  if (Verbose) {
    if (Y) {
      fprintf(Logfile, "\nFreeing Y complexmatrix...");
    } else {
      fprintf(Logfile, "\nY complexmatrix is freed already");
    }
    fflush(Logfile);
  }
  if (Y)
    free_complexmatrix(Y, 0, Nnn, -Nnn, Nnn);

  if (Verbose) {
    if (A) {
      fprintf(Logfile, "\nFreeing A complexmatrix...");
    } else {
      fprintf(Logfile, "\nA complexmatrix is freed already");
    }
    fflush(Logfile);
  }
  if (A)
    free_complexmatrix(A, 0, Nnn, -Nnn, Nnn);

  if (Verbose) {
    fprintf(Logfile, "\nDone freeing all the memory I know about");
    fflush(Logfile);
  }

  return;
}

/***
 *    freedistrib3d
 *
 *    Releases all dynamically allocated memory for the
 *    distrib3d function
 *
 *    SHOULD ONLY BE CALLED IF ALL MEMORY HAS ALREADY BEEN
 *    DYNAMICALLY ALLOCATED
 *
 *    Arguments:    None
 *    Returns:    Nothing
 *
 *    Calls:        free_ivector, free_fvector, free_fcube
 *    Called by:    distrib3d
 *
 ***/
void freedistrib3d(void) {
  if (R)
    free_ivector(R);
  if (S)
    free_fvector(S);
  if (Xr)
    free_fvector(Xr);
  if (Filter)
    free_fcube(Filter, Fsize + 1);
  if (Nsolid)
    free_ivector(Nsolid);
  if (Nair)
    free_ivector(Nair);
  if (Curvature)
    free_usibox(Curvature, Xsyssize + 1, Ysyssize + 1);
  if (Sum)
    free_ivector(Sum);
  if (Normm)
    free_fbox(Normm, Xsyssize + 1, Ysyssize + 1);
  if (Rres)
    free_fbox(Rres, Xsyssize + 1, Ysyssize + 1);

  return;
}

/***
 *    allmem
 *
 *    Attempts to dynamically allocate memory for this
 *    program.
 *
 *    Arguments:    None
 *    Returns:    Nothing
 *
 *    Calls:        ivector, fvector, fcube
 *    Called by:    main
 *
 ***/
void allmem(void) {

  R = NULL;
  S = NULL;
  Xr = NULL;
  Filter = NULL;
  Nsolid = NULL;
  Nair = NULL;
  Curvature = NULL;
  Sum = NULL;
  Normm = NULL;
  Rres = NULL;

  R = ivector(2 * Fsize);
  S = fvector(2 * Fsize);
  Xr = fvector(2 * Fsize);
  Filter = fcube(Fsize + 1);
  Nsolid = ivector(Hsize_s);
  Nair = ivector(Hsize_s);
  Curvature = usibox(Xsyssize + 1, Ysyssize + 1, Zsyssize + 1);
  Sum = ivector(Hsize_r + 2);
  Normm = fbox(Xsyssize + 1, Ysyssize + 1, Zsyssize + 1);
  Rres = fbox(Xsyssize + 1, Ysyssize + 1, Zsyssize + 1);

  if (!R || !S || !Xr || !Filter || !Nsolid || !Nair || !Curvature || !Sum ||
      !Normm || !Rres) {

    freedistrib3d();
    bailout("distrib3d", "Memory allocation failure");
    fflush(stdout);
    exit(1);
  }

  return;
}

/******************************************************
 *
 * Function distfa to distribute fly ash phases
 * randomly amongst monophase particles or on
 * a pixel basis.  This is a combination of the
 * standalone programs distfapart and distfarand,
 * originally programmed by Dale Bentz (May 1997)
 *
 *******************************************************/
int distfa(int fadchoice) {
  int *phase, *partid;
  int ix, iy, iz, valin, valout, partin;
  int count, c1, phnew, mult;
  int totcnt, ascnt, cacl2cnt, amsilcnt, inertcnt;
  int anhcnt, cas2cnt, c3acnt;
  int markc3a, markas, markcacl2, markamsil, markinert, markanh, markcas2;
  float probasg, probcacl2, probsio2;
  float probc3a, prph, probcas2, probanh;
  char instring[MAXSTRING];

  totcnt = 0;
  cas2cnt = anhcnt = c3acnt = ascnt = cacl2cnt = amsilcnt = inertcnt = 0;
  mult = 0;
  partid = NULL;
  phase = NULL;

  if (fadchoice == 0) {

    /***
     *    This block prepares for distributing among
     *    monophase particles.  Not needed if distributing
     *    randomly pixel by pixel
     ***/

    phase = NULL;
    partid = NULL;
    mult = 1;

    /***
     *    Initial allocation of memory for phase
     *    and partid arrays
     ***/

    phase = (int *)calloc((size_t)Npartc, sizeof(int));
    if (!phase) {
      bailout("distfapart", "Could not allocate memory for phase");
      exit(1);
    }

    partid = (int *)calloc((size_t)Npartc, sizeof(int));
    if (!partid) {
      free(phase);
      bailout("distfapart", "Could not allocate memory for partid");
      exit(1);
    }

    ascnt = cacl2cnt = amsilcnt = inertcnt = 0;
    cas2cnt = anhcnt = c3acnt = 0;

    /* Determine total number of fly ash pixels in image */
    totcnt = 0;
    for (iz = 0; iz < Zsyssize; iz++) {
      for (iy = 0; iy < Ysyssize; iy++) {
        for (ix = 0; ix < Xsyssize; ix++) {
          if (Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] == FLYASH)
            totcnt++;
        }
      }
    }
  }

  /* Get user input for phase probabilities (volume fractions)     */
  /* This is needed whether distributing among monophase particles */
  /*     or randomly on a pixel by pixel basis                     */

  fprintf(Logfile,
          "Enter probability for fly ash to be aluminosilicate glass \n");
  read_string(instring, sizeof(instring));
  probasg = atof(instring);
  fprintf(Logfile, "%f\n", probasg);
  Volf[ASG] = probasg;
  fprintf(Logfile,
          "Enter probability for fly ash to be calcium aluminodisilicate \n");
  read_string(instring, sizeof(instring));
  probcas2 = atof(instring);
  fprintf(Logfile, "%f\n", probcas2);
  Volf[CAS2] = probcas2;
  fprintf(Logfile,
          "Enter probability for fly ash to be tricalcium aluminate \n");
  read_string(instring, sizeof(instring));
  probc3a = atof(instring);
  fprintf(Logfile, "%f\n", probc3a);
  Volf[FAC3A] = probc3a;
  fprintf(Logfile, "Enter probability for fly ash to be calcium chloride \n");
  read_string(instring, sizeof(instring));
  probcacl2 = atof(instring);
  fprintf(Logfile, "%f\n", probcacl2);
  Volf[CACL2] = probcacl2;
  fprintf(Logfile, "Enter probability for fly ash to be silica \n");
  read_string(instring, sizeof(instring));
  probsio2 = atof(instring);
  fprintf(Logfile, "%f\n", probsio2);
  Volf[AMSIL] = probsio2;
  fprintf(Logfile, "Enter probability for fly ash to be anhydrite \n");
  read_string(instring, sizeof(instring));
  probanh = atof(instring);
  fprintf(Logfile, "%f\n", probanh);
  Volf[ANHYDRITE] = probanh;

  /* Determine goal counts for each phase */

  markas = probasg * (float)totcnt;
  markamsil = probsio2 * (float)totcnt;
  markcacl2 = probcacl2 * (float)totcnt;
  markanh = probanh * (float)totcnt;
  markcas2 = probcas2 * (float)totcnt;
  markc3a = probc3a * (float)totcnt;
  markinert =
      (1.0 - probasg - probsio2 - probcacl2 - probanh - probcas2 - probc3a) *
      (float)totcnt;

  /***
   *    Convert probabilities to cumulative
   *
   *    Order must be the same as in for loop below
   ***/

  probcacl2 += probasg;
  probsio2 += probcacl2;
  probanh += probsio2;
  probcas2 += probanh;
  probc3a += probcas2;

  if (fadchoice == 0) {
    for (ix = 0; ix < Npartc; ix++) {
      phase[ix] = partid[ix] = 0;
    }

    count = 0;

    /* First scan-- find each particle and assign phases */

    for (iz = 0; iz < Zsyssize; iz++) {
      for (iy = 0; iy < Ysyssize; iy++) {
        for (ix = 0; ix < Xsyssize; ix++) {

          valin = Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];
          partin = Cement.val[getInt3dindex(Cement, ix, iy, iz)];

          if ((valin == FLYASH) && (partid[partin] == 0)) {

            count++;

            /* Check if we have run out of allocated memory */

            if (count >= mult * Npartc) {
              mult++;
              partid = (int *)realloc((int *)partid, (size_t)(mult * Npartc));
              if (!partid) {
                free(phase);
                bailout("distfa", "Could not reallocate partid");
                exit(1);
              }

              phase = (int *)realloc((int *)phase, (size_t)(mult * Npartc));
              if (!phase) {
                free(partid);
                bailout("distfapart", "Could not reallocate partid");
                exit(1);
              }
            }

            partid[partin] = count;

            valout = INERT;
            do {
              prph = ran1(Seed);

              if ((prph < probasg) && (ascnt < markas)) {

                valout = ASG;

              } else if ((prph < probcacl2) && (cacl2cnt < markcacl2)) {

                valout = CACL2;

              } else if ((prph < probsio2) && (amsilcnt < markamsil)) {

                valout = AMSIL;

              } else if ((prph < probanh) && (anhcnt < markanh)) {

                valout = ANHYDRITE;

              } else if ((prph < probcas2) && (cas2cnt < markcas2)) {

                valout = CAS2;

              } else if ((prph < probc3a) && (c3acnt < markc3a)) {

                valout = FAC3A;
              }
            } while ((valout == INERT) && (inertcnt > markinert));

            phase[count] = valout;
          }

          if (valin == FLYASH) {

            c1 = partid[partin];
            phnew = phase[c1];

            switch (phnew) {
            case ASG:
              ascnt++;
              break;
            case CACL2:
              cacl2cnt++;
              break;
            case AMSIL:
              amsilcnt++;
              break;
            case ANHYDRITE:
              anhcnt++;
              break;
            case CAS2:
              cas2cnt++;
              break;
            case C3A:
              c3acnt++;
              break;
            case INERT:
              inertcnt++;
              break;
            default:
              break;
            }
          }

        } /* End of iz loop */
      } /* End of iy loop */
    } /* End of ix loop */
  }

  /* Above scan is needed only if distributing among */
  /* monophase particles.  The scane below is needed */
  /* either way                                      */

  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {

        partin = Cement.val[getInt3dindex(Cement, ix, iy, iz)];
        valin = Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)];

        if (valin == FLYASH) {
          if (fadchoice == 0) {
            count = partid[partin];
            Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] = phase[count];
          } else {
            valout = INERT;
            prph = ran1(Seed);
            if (prph < probasg) {

              valout = ASG;

            } else if (prph < probcacl2) {

              valout = CACL2;

            } else if (prph < probsio2) {

              valout = AMSIL;

            } else if (prph < probanh) {

              valout = ANHYDRITE;

            } else if (prph < probcas2) {

              valout = CAS2;

            } else if (prph < probc3a) {

              valout = FAC3A;
            }

            Cemreal.val[getInt3dindex(Cemreal, ix, iy, iz)] = valout;
          }
        }
      }
    }
  }

  if (fadchoice == 0) {
    free(partid);
    free(phase);
  }
  return (0);
  /* GODZILLA */
}

char *rfc8601_timespec(struct timespec *tv) {
  char time_str[127];
  double fractional_seconds;
  int milliseconds;
  struct tm tm; // our "broken down time"
  char *rfc8601;

  rfc8601 = malloc(256);

  memset(&tm, 0, sizeof(struct tm));
  sprintf(time_str, "%ld UTC", tv->tv_sec);

  // convert our timespec into broken down time
  strptime(time_str, "%s %U", &tm);

  // do the math to convert nanoseconds to integer milliseconds
  fractional_seconds = (double)tv->tv_nsec;
  fractional_seconds /= 1e6;
  fractional_seconds = round(fractional_seconds);
  milliseconds = (int)fractional_seconds;

  // print date and time without milliseconds
  strftime(time_str, sizeof(time_str), "%Y-%m-%dT%H:%M:%S", &tm);

  // add on the fractional seconds and Z for the UTC Timezone
  sprintf(rfc8601, "%s.%dZ", time_str, milliseconds);

  return rfc8601;
}
