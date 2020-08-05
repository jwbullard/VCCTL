/****************************************************** 
*
* Program genaggpack_settle.c to generate three-dimensional packing
* of aggregate particles, sampling from the aggregate database
*
* Tries to encourage higher packing fractions by settling the particles
* to the bottom of the box as much as possible.
*
* Programmer:    Jeffrey W. Bullard
*                Texas A&M University
*                3136 TAMU
*                College Station, TX  77843-3136   USA
*                (979) 458-6482
*                E-mail: jubullard@tamu.edu
*                                                                     
* October 2004
*******************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include "vcctl.h"

/*
#define CHOOSE_BASED_ON_SIZE
*/

#define MAXSP    10000

#define MAXLINES    3500
#define NNN                14    

#define AGG    INERTAGG    /* phase identifiers, just for this program */
#define ITZ 2

#define COARSE    0
#define FINE    1

/***
*    Number of grid points used in theta and phi directions
*    to reconstruct particle surface. You can use down to
*    about 100 for each and still get particles that are decent
*    looking. The number of lines in the VRML files scale like
*    NTHETA*NPHI. NOTE: Better to have odd number.
*    Allow three different levels of resolution, depending on
*    the value of resval in the main program (0=low, 1=med, 2=high)
***/
#define NTHETAPTS        1000

/* maximum number of random tries for particle placement */
#define MAXTRIES        150000

/* Error flag for memory violation */
#define MEMERR            -1

#define MAXSIZECLASSES        74

/***
*    Note that each particle must have a separate ID
*    to allow for flocculation
***/

#define SPHERES            0
#define REALSHAPE        1

/***
*  Set the number of distinct shapes to use within a size class
*  Negative number indicates a new shape for every particle
***/

#define CEM                100    

/* max. number of particles allowed in box */
#define NPARTC            2400000

/* Default for burned id must be at least 100 greater than NPARTC */
#define BURNT            2440000
#define FCHECK            BURNT        /* Temporary flag for checking
                                        floc collisions */

#define MAXBURNING        2390000

/* maximum number of different particle sizes */
#define NUMSOURCES	2     /* number of different sources allowed for each aggregate type */
#define NUMAGGBINS	148  /* MAXSIZECLASSES * NUMSOURCES */

/***
*    Defines for main menu choice
***/

#define EXIT            1
#define SPECSIZE        EXIT + 1
#define ADDCOARSEPART    SPECSIZE + 1
#define ADDFINEPART        ADDCOARSEPART + 1
#define MEASURE            ADDFINEPART + 1
#define CONNECTIVITY    MEASURE + 1
#define OUTPUTMIC        CONNECTIVITY + 1

/***
*    Parameter for comparing the difference between
*    two floats
***/

#define TINY            1.0e-6

#define STAY    0
#define MOVE    1
#define ERASE    2

/***
*    FINEAGGRES is the cutoff resolution at or above which the ITZ
*    will not be resolved
***/
const float FINEAGGRES = 0.10;

/***
*    Data structure for doubly linked list of pore and ITZ voxels
*    to be used in adjusting volume of real-shape particles
***/

struct Pore {
    int ns;    /* voxel number */
    int radius;  /* effective radius of porosity surrounding a pore */
    struct Pore *next;
    struct Pore *prev;
};

/***
*    Data structure for linked list of surface voxels
*    to be used in adjusting volume of real-shape particles
***/

struct Surfvox {
    int x,y,z;    /* position of surface voxel in bounding box */
};

/***
*    Data structure for particles
***/

struct particle {
    int partid;        /* index for particle */
    int partphase;  /* phase identifier for this
                        particle (C3S or GYPSUM, etc) */
    int settled;     /* Whether or not particle has been repositioned */
    int numvox;      /* number of voxels in particle */
    int numperiph;   /* number of periphery voxels */
    int xc,yc,zc;    /* center of bounding box */
    int minz;        /* minimum z-coordinate */
    int xd,yd,zd;    /* dimensions of bounding box */
    int *pvid;        /* list of periphery voxel ids */
    int *xi, *yi, *zi;  /* list of all voxel locations */
};

/***
*    Global variable declarations:
*
*        Agg stores the 3-D particle structure
*
*        Pagg stores the particle id numbers
*        (each particle with its own ID)
*
*        Bbox stores the local aggregate particle
***/

/*** JWB ***/
int Filecount = 0;

int Verbose;
int Debug;
Int3d Agg,Pagg,Bbox;

/***
*    System size (voxels per edge), number of
*    particles, and size of aggregate
***/
int Sysvox = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
int Boxsize = DEFAULTSYSTEMSIZE;
int Zlayersize = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
int Mindimen = DEFAULTSYSTEMSIZE;
int Maxtries = MAXTRIES;
int Numaggbins = NUMAGGBINS;
const float Size_safety_coeff = 0.40;
int Isizemag = 1;
float Sizemag = 1.0;
int Npart,Aggsize,Shape;

int MaxBinWithoutSorting = 1;
int MaxPoreSizeToCheck = DEFAULTSYSTEMSIZE/2;

long int Recur01, Recur02;
/***
*  Set the number of distinct shapes to use within a size class
*  Negative number indicates a new shape for every particle
***/

const int Shapesperbin = 25;

int Npartc,Burnt,Maxburning;
int Allocated = 0;

int N_total = 0;
int N_target = 0;

int Volpart[NUMSOURCES][MAXSIZECLASSES];

/***
*    System resolution (micrometers per voxel edge)
***/
float Resolution = DEFAULTRESOLUTION;
/* const float Resolution_safety_coeff = 2.0; */
/* CHANGE THESE BACK SOON - JWB 2020 MAY 7 */
const float Resolution_safety_coeff = 1.0;

/* VCCTL software version used to create input file */
float Version;

/* Random number seed */
int *Seed;

/* Itz thickness in voxels */
int Itz;

double Pi;

fcomplex **Y,**A,**AA;
int Ntheta,Nphi;
int Nnn = NNN;

/* File root for real shape anm files */
char Pathroot[MAXSTRING],Shapeset[MAXSTRING];
char Filesep;

/* Gaussian quadrature points for real shape particles */
float *Xg,*Wg;

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
    int Nnn;    /* Number terms to get within
                                5% of Gaussian curvature */
    float NGC; /* normalized Gaussian curvature */
    float length;
    float width;
    float thickness;
    float nlength;
    float nwidth;
};

/* Pointer to a 1D list of pointers to particle structures */
struct particle **Particle;
int *Pindextable;  /* index table to store particle ids for sorting purposes */

/* Pointers to head and tail of doubly linked list of pore voxels */
struct Pore *Pore_head = NULL;
struct Pore *Pore_tail = NULL;

/***
*    Function declarations
***/

void checkargs(int argc, char *argv[]);
int getsystemsize(void);
int genpacking(int type, int numsources, int sourceeach[NUMAGGBINS],
                  int voleach[NUMAGGBINS], int vp[NUMAGGBINS],
                  int numeach[NUMAGGBINS], float sizeeach[NUMAGGBINS],
                  FILE *fpout);
int packspheres(int type, int numsources, int sourceeach[NUMAGGBINS],
                  int voleach[NUMAGGBINS], int vp[NUMAGGBINS],
                  int numeach[NUMAGGBINS], float sizeeach[NUMAGGBINS],
                  FILE *fpout);
int placesphereclass(int numtoplace, int nvoxthis, int phaseid, int calcporesizes,
                     float frad, int *nxp, int *nyp, int *nzp, FILE *fpout);
int placeshapeclass(int numtoplace, int nvoxthis, int phaseid, int numshapes,
                     int numpershape, int calcporesizes,
                     struct lineitem shapedata[MAXLINES], float frad, FILE *fpout);
int packrealshapes(int type, int numshapes, int numsources, int sourceeach[NUMAGGBINS],
                  int voleach[NUMAGGBINS], int vp[NUMAGGBINS],
                  int numeach[NUMAGGBINS], float sizeeach[NUMAGGBINS],
                  struct lineitem line[MAXLINES],
                  FILE *fpout);
int placepartclass(int numtoplace, int nvoxthis, int calcporesizes,
                     float frad, int *nxp, int *nyp, int *nzp);
int readshapelines(struct lineitem line[MAXLINES]);
int digitizesphere(int *nxp, int *nyp, int *nzp, int targetvox, float radius);
int digitizerealshape(int newshape,int *nxp, int *nyp,
                      int *nzp, int targetvox,
                      int numshapes, struct lineitem line[MAXLINES]);
int rotatebox(int *nxp, int *nyp, int *nzp);
int countBbox(int nxp, int nyp, int nzp);
int checksphere(int xin, int yin, int zin, int *nxp, int *nyp, int *nzp);
int findsphereloc(int *x, int *y, int *z, int *nxp, int *nyp, int *nzp,
                  int *numpores, int *firstnpores, float frad);
int findshapeloc(int *x, int *y, int *z, int *nxp, int *nyp, int *nzp,
                  int *numpores, int *firstnpores, int nvoxthis, int numshapes,
                  struct lineitem line[MAXLINES], float frad);
int placesphere(int xin, int yin, int zin, int nxp, int nyp, int nzp,
              int volume, int phaseid);
int checkrealshape(int xin, int yin, int zin, int nxp, int nyp, int nzp);
int placerealshape(int xin, int yin, int zin, int nxp, int nyp, int nzp,
              int volume, int phaseid);
int settle(void);
int sortParticles(void);
int image(int *nxp, int *nyp, int *nzp);
int smallimage(int *nxp, int *nyp, int *nzp, int vol);
int sphereimage(int *nxp, int *nyp, int *nzp, float rad);
int adjustvol(int diff, int nxp, int nyp, int nzp);
int create(int type, int numtimes);
int printbox(char *Filename, int nxp, int nyp, int nzp);
int isPeriph(int x, int y, int z);
int voxpos(int x, int y, int z);
int getXfromNs(int ns);
int getYfromNs(int ns);
int getZfromNs(int ns);
float meanradius(int numdiv,float min, float max);
int additz(void);
void measure(void);
void connect(void);
void outmic(void);
void harm(double theta, double phi);
double fac(int j);
struct particle *particlevector(int size);
void free_particlevector(struct particle *ps);
struct particle **particlepointervector(int size);
void free_particlepointervector(struct particle **ps);
void freeallmem(void);

/* Functions for doubly linked list */

int Pore_create_porelist(int calcsizes,float frad, int *firstnpores);
int getPoreRadius(int x, int y, int z);
int Pore_push(int val, int radius);
struct Pore *Pore_find_pos(int pos);
struct Pore *Pore_find_val(int val);
int Pore_delete_val(int time, int val);
int Pore_display(void);
int Pore_delete(void);
int Pore_length(void);

/* Functions for merge sorting */
int max(int x, int y);
int min(int x, int y);
struct Pore *merge(struct Pore *a, struct Pore *b);
int mergeSort(void);
void split(struct Pore *head, struct Pore **a, struct Pore **b);

int main(int argc, char *argv[])
{
    int userc;    /* User choice from menu */
    int nseed,numtimes;
    double time_spent;
    clock_t begin,end;
    char instring[MAXSTRING];
    register int ig,jg,kg;

    begin = clock();

    /* Initialize global arrays */
    for (jg = 0; jg < NUMSOURCES; jg++) {
        for (ig = 0; ig < MAXSIZECLASSES; ig++) {
            Volpart[jg][ig] = 0;
        }
    }

    numtimes = 0;

    A = NULL;
    AA = NULL;
    Y = NULL;
    Xg = NULL;
    Wg = NULL;
    Particle = NULL;

    Pi = 4.0 * atan(1.0);

    Ntheta = Nphi = 0;

    /* Check command-line arguments */
    checkargs(argc,argv);

    printf("Enter random number seed value (a negative integer) \n");
    read_string(instring,sizeof(instring));
    nseed = atoi(instring);
    if (nseed > 0) nseed = (-1 * nseed);
    printf("%d \n",nseed);
    Seed=(&nseed);

    /* Initialize counters and system parameters */

    Npart = 0;

    /***
    *    Present menu and execute user choice
    ***/

    do {
        printf(" \n Input User Choice \n");
        printf("%d) Exit \n",EXIT);
        printf("%d) Specify system size \n",SPECSIZE);
        printf("%d) Add coarse aggregate particles \n",ADDCOARSEPART);
        printf("%d) Add fine aggregate particles \n",ADDFINEPART);
        printf("%d) Measure global phase fractions \n",MEASURE);
        printf("%d) Measure single phase connectivity ",CONNECTIVITY);
        printf("(pores or solids) \n");
        printf("%d) Output current packing to file \n",OUTPUTMIC);

        read_string(instring,sizeof(instring));
        userc = atoi(instring);
        printf("%d \n",userc);
        fflush(stdout);

        switch (userc) {
            case SPECSIZE:
                if (getsystemsize() == MEMERR) {
                    freeallmem();
                    bailout("genaggpack","Memory allocation error");
                    exit(1);
                }

                /* Clear the 3-D system to all porosity to start */

                for(kg = 0; kg < Zsyssize; kg++) {
                    for (jg = 0; jg < Ysyssize; jg++) {
                        for(ig = 0; ig < Xsyssize; ig++) {
                            Agg.val[getInt3dindex(Agg,ig,jg,kg)] = POROSITY;
                            Pagg.val[getInt3dindex(Pagg,ig,jg,kg)] = POROSITY;
                        }
                    }
                }
                break;
            case ADDCOARSEPART:
                if (create((int)COARSE,numtimes) == MEMERR) {
                    freeallmem();
                    bailout("genaggpack","Error");
                    exit(1);
                }
                numtimes++;
                break;
            case ADDFINEPART:
                if (create((int)FINE,numtimes) == MEMERR) {
                    freeallmem();
                    bailout("genaggpack","Error");
                    fflush(stdout);
                    exit(1);
                }
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
    end = clock();
    time_spent = (double)(end - begin) / CLOCKS_PER_SEC;
    printf("\n\n***Time of execution = %.3f s\n\n",time_spent);
    return(0);
}

/***
*   checkargs    
*
*     Checks command-line arguments
*
*     Arguments:  int argc, char *argv[]
*     Returns:    nothing
*
*    Calls:        no routines
*    Called by:    main program
***/
void checkargs(int argc, char *argv[])
{
    register unsigned int i;

    /* Is verbose output requested? */

    Verbose = 0;
    Debug = 0;
    for (i = 1; i < argc; i++) {
        if ((!strcmp(argv[i],"-v")) || (!strcmp(argv[i],"--verbose"))) Verbose = 1;
        if ((!strcmp(argv[i],"-d")) || (!strcmp(argv[i],"--debug"))) Debug = 1;
    }

    if (Debug) {
        printf("\n\nWARNING:  Debug mode produces a LOT of output");
    }
}

/***
*    getsystemsize
*
*     Gets the dimension, in voxels, of the system per edge
*
*     Arguments:    none
*     Returns:    status flag (0 if okay, -1 if memory allocation error)
*
*    Calls:        no routines
*    Called by:    main program
***/
int getsystemsize(void)
{
    char instring[MAXSTRING];

    Xsyssize = Ysyssize = Zsyssize = 0;
    Resolution = 0.0;

    printf("Enter X dimension of system \n");
    read_string(instring,sizeof(instring));
    Xsyssize = atoi(instring);
    printf("%d\n",Xsyssize);
    printf("Enter Y dimension of system \n");
    read_string(instring,sizeof(instring));
    Ysyssize = atoi(instring);
    printf("%d\n",Ysyssize);
    printf("Enter Z dimension of system \n");
    read_string(instring,sizeof(instring));
    Zsyssize = atoi(instring);
    printf("%d\n",Zsyssize);

    if ((Xsyssize <= 0) || (Xsyssize > MAXSIZE)
        || (Ysyssize <= 0) || (Ysyssize > MAXSIZE)
        || (Zsyssize <= 0) || (Zsyssize > MAXSIZE)) {

        return(MEMERR);
    }

    Zlayersize = Xsyssize * Ysyssize;

    Boxsize = Xsyssize;
    if (Ysyssize < Boxsize) Boxsize = Ysyssize;
    if (Zsyssize < Boxsize) Boxsize = Zsyssize;
    Boxsize = Boxsize / 2;

    printf("Enter system resolution (millimeters per voxel) \n");
    read_string(instring,sizeof(instring));
    Resolution = atof(instring);
    printf("%4.2f\n",Resolution);

    /***
    *    Now dynamically allocate the memory for the Agg and Pagg array
    ***/

    Sysvox = (int)(Xsyssize * Ysyssize * Zsyssize);
    Sizemag = ((float)Sysvox) / (pow(((double)DEFAULTSYSTEMSIZE),3.0));
    Maxtries = (int)(Maxtries * Sizemag);
    Isizemag = (int)(Sizemag + 0.5);
    if (Isizemag < 1) Isizemag = 1;
    Npartc = (int)(NPARTC * Isizemag);
    Burnt = (int)(BURNT * Isizemag);
    Maxburning = (int)(MAXBURNING * Isizemag);

    if (!Agg.val) {
        if (Int3darray(&Agg,Xsyssize,Ysyssize,Zsyssize)) {
            return(MEMERR);
        }
    }

    if (!Pagg.val) {
        if (Int3darray(&Pagg,Xsyssize,Ysyssize,Zsyssize)) {
            return(MEMERR);
        }
    }

    Allocated = 1;

    Particle = NULL;
    Particle = particlepointervector(Npartc);
    if (!Particle) {
        return(MEMERR);
    }

    Pindextable = ivector(Npartc);
    if (!Pindextable) {
        return(MEMERR);
    }

    return(0);
}

/***
*    checksphere
*
*    routine to check if a digitized sphere will fit
*
*     Arguments:
*         int xin,yin,zin is the center of the sphere to add
*         int *nxp,*nyp,*nzp is the lower left front corner of bounding box
*             for real particles
*
*     Returns:    integer flag telling whether sphere will fit
*
*    Calls:        checkbc
*    Called by:    packspheres
***/
int checksphere(int xin,int yin,int zin,int *nxp,int *nyp,int *nzp)
{
    int fits,i,j,k,dum;
    int i1,j1,k1,xc,yc,zc;

    fits = 1;    /* Flag indicating if placement is possible */

    xc = (int)((float)(0.50 * (*nxp)) + 0.01);
    yc = (int)((float)(0.50 * (*nyp)) + 0.01);
    zc = (int)((float)(0.50 * (*nzp)) + 0.01);

    k = j = i = 0;
    fits = 1;
    while (k <= (*nzp) && fits) {
        j = 0;
        while (j <= (*nyp) && fits) {
            i = 0;
            while (i <= (*nxp) && fits) {
                i1 = xin + (i - xc);
                i1 += checkbc(i1,Xsyssize);
                j1 = yin + (j - yc);
                j1 += checkbc(j1,Ysyssize);
                k1 = zin + (k - zc);
                k1 += checkbc(k1,Zsyssize);
                dum = voxpos(i1,j1,k1);
                if (Agg.val[getInt3dindex(Agg,i1,j1,k1)] != POROSITY
                    && Bbox.val[getInt3dindex(Bbox,i,j,k)] != POROSITY) {
                    fits = 0;
                }
                i++;
            }
            j++;
        }
        k++;
    }

    return(fits);
}

/***
*    checkrealshape
*
*    routine to check or perform placement of real-shaped particle
*    centered at location (xin,yin,zin) of volume vol
*
*     Arguments:
*         int xin,yin,zin is the centroid of the sphere to add
*         int *nxp,*nyp,*nzp is the lower left front corner of bounding box
*             for real particles
*
*     Returns:    integer flag telling whether sphere will fit
*
*    Calls:        checkbc
*    Called by:    packrealshapes
***/
int checkrealshape(int xin,int yin,int zin,int nxp,int nyp,int nzp)
{
    int fits,i,j,k,dum;
    int i1,j1,k1,xc,yc,zc;

    if (Debug) {
        printf("\nIn checkrealshape, (x,y,z) = (%d,%d,%d)",xin,yin,zin);
        printf("and (nxp,nyp,nzp) = (%d,%d,%d)",nxp,nyp,nzp);
        fflush(stdout);
    }

    xc = (int)((float)(0.50 * nxp) + 0.01);
    yc = (int)((float)(0.50 * nyp) + 0.01);
    zc = (int)((float)(0.50 * nzp) + 0.01);

    fits = 1;    /* Flag indicating if placement is possible */

    for (k = 0; k <= nzp && fits; ++k) {
        for (j = 0; j <= nyp && fits; ++j) {
            for (i = 0; i <= nxp && fits; ++i) {
                i1 = xin + (i - xc);
                i1 += checkbc(i1,Xsyssize);
                j1 = yin + (j - yc);
                j1 += checkbc(j1,Ysyssize);
                k1 = zin + (k - zc);
                k1 += checkbc(k1,Zsyssize);
                dum = voxpos(i1,j1,k1);
                if (Agg.val[getInt3dindex(Agg,i1,j1,k1)] != POROSITY
                    && Bbox.val[getInt3dindex(Bbox,i,j,k)] != POROSITY) {
                    fits = 0;
                }
            }
        }
    }

    if (Debug) {
        printf("\nLeaving checkrealshape with fits = %d",fits);
        fflush(stdout);
    }

    return(fits);
}

/***
*    placesphere
*
*    routine to perform placement of a sphere with
*    ID phasein, centered at location (xin,yin,zin) of volume vol
*
*     Arguments:
*         int xin,yin,zin is the centroid of the sphere to add
*         int nxp,nyp,nzp is the lower left front corner of bounding box
*             for real particles
*         int vol is the number of voxels
*         int phaseid phase to assign
*
*     Returns:    number of voxels placed
*
*    Calls:        checkbc
*    Called by:    packspheres
***/
int placesphere(int xin,int yin,int zin,int nxp,int nyp,int nzp,
                int vol,int phaseid)
{
    int i,j,k;
    int i1,j1,k1,numvox,numperiph,xc,yc,zc;
    int minz,cursphere;

    minz = Zsyssize + 5;

    if (Debug) {
        printf("\nIn placesphere, Vol = %d, ",vol);
        printf("(x,y,z) = (%d,%d,%d), phase = %d",xin,yin,zin,phaseid);
        fflush(stdout);
    }

    xc = (int)((float)(0.50 * nxp) + 0.01);
    yc = (int)((float)(0.50 * nyp) + 0.01);
    zc = (int)((float)(0.50 * nzp) + 0.01);

    cursphere = Npart - 1;
    if (Debug) {
        printf("\n\t\tBeginning of pore list is %d",(Pore_head)->ns);
        fflush(stdout);
        printf("\n\t\tPore head value = ");
        fflush(stdout);
        printf("%d",(Pore_head)->ns);
        fflush(stdout);
        printf("\n\t\tPore list length =  ");
        fflush(stdout);
        printf("%d",Pore_length());
        fflush(stdout);
    }

    /* Pore_display(); */

    /* Allocate space for new particle info */

    Particle[cursphere] = particlevector(vol);
    if (!Particle[cursphere]) {
        bailout("genaggpack","Memory allocation error");
        fflush(stdout);
        printf("\nNeed to delete %d pore voxels from list 06",Pore_length());
        fflush(stdout);
        if (Pore_delete()) {
            printf("\nError: Had trouble deleting Pore list");
            fflush(stdout);
        }
    }

    Particle[cursphere]->partid = Npart;
    Particle[cursphere]->partphase = phaseid;
    Particle[cursphere]->settled = 0;
    Particle[cursphere]->xd = nxp;
    Particle[cursphere]->yd = nyp;
    Particle[cursphere]->zd = nzp;
    Particle[cursphere]->xc = xin + (int)(0.5 * Particle[cursphere]->xd + 0.5);
    Particle[cursphere]->xc += checkbc(Particle[cursphere]->xc,Xsyssize);
    Particle[cursphere]->yc = yin + (int)(0.5 * Particle[cursphere]->yd + 0.5);
    Particle[cursphere]->yc += checkbc(Particle[cursphere]->yc,Ysyssize);
    Particle[cursphere]->zc = zin + (int)(0.5 * Particle[cursphere]->zd + 0.5);
    Particle[cursphere]->zc += checkbc(Particle[cursphere]->zc,Zsyssize);

    Pindextable[cursphere] = cursphere;

    k = j = i = 0;
    numvox = numperiph = 0;
    while (k <= nzp) {
        j = 0;
        while (j <= nyp) {
            i = 0;
            while (i <= nxp) {
                i1 = xin + (i - xc);
                i1 += checkbc(i1,Xsyssize);
                j1 = yin + (j - yc);
                j1 += checkbc(j1,Ysyssize);
                k1 = zin + (k - zc);
                k1 += checkbc(k1,Zsyssize);
                if (Bbox.val[getInt3dindex(Bbox,i,j,k)] == AGG) {
                    Agg.val[getInt3dindex(Agg,i1,j1,k1)] = phaseid;
                    Pagg.val[getInt3dindex(Pagg,i1,j1,k1)] = Npart;
                    if (Debug) {
                        printf("\nDeleting one voxel %d, ",voxpos(i1,j1,k1));
                        printf("%d so far",numvox);
                        fflush(stdout);
                    }

                    /* Need to store voxel positions on the periphery separately */

                    if (isPeriph(i,j,k)) {
                        Particle[cursphere]->pvid[numperiph] = numvox;
                        if (k1 < minz) {
                            minz = k1;
                            Particle[cursphere]->minz = numvox;
                        }
                        numperiph++;
                    }
                    Particle[cursphere]->xi[numvox] = i1;
                    Particle[cursphere]->yi[numvox] = j1;
                    Particle[cursphere]->zi[numvox] = k1;
                    numvox++;
                }
                i++;
            }
            j++;
        }
        k++;
    }

    Particle[cursphere]->numperiph = numperiph;
    if (minz == 0) Particle[cursphere]->settled = 1;

    if (numperiph > 1500) {
        printf("\nFound large sphere number %d:",cursphere);
        printf("\n\tParticle[%d]->partid = %d",cursphere,Particle[cursphere]->partid);
        printf("\n\tParticle[%d]->nump = %d",cursphere,numvox);
        printf("\n\tParticle[%d]->numperiph = %d",cursphere,Particle[cursphere]->numperiph);
        printf("\n\tParticle[%d]->partphase = %d",cursphere,Particle[cursphere]->partphase);
        printf("\n\tParticle[%d]->center = (%d,",cursphere,Particle[cursphere]->xc);
        printf("%d,%d)",Particle[cursphere]->yc,Particle[cursphere]->zc);
        fflush(stdout);
    }

    if (Debug) {
        printf("\nLeaving placesphere after placing particle with %d voxels",numvox);
        fflush(stdout);
    }

    return(numvox);
}

/***
*    placerealshape
*
*    routine to check or perform placement of real-shaped particle
*    of ID phasein, centered at location (xin,yin,zin) of volume vol
*
*     Arguments:
*         int xin,yin,zin is the centroid of the sphere to add
*         int nxp,nyp,nzp is the lower left front corner of bounding box
*             for real particles
*         int vol is the number of voxels
*         int phaseid to assign to cemreal image
*
*     Returns:    number of voxels placed
*
*    Calls:        checkbc
*    Called by:    packrealshapes
***/
int placerealshape(int xin,int yin,int zin,int nxp,int nyp,int nzp,
                   int numvoxthis,int phaseid)
{
    int i,j,k;
    int i1,j1,k1,numvox,vol,numperiph,xc,yc,zc;
    int minz,curpart;

    minz = Zsyssize + 5;

    numvox = vol = 0;
    k = j = i = 0;
    while (k <= nzp) {
        j = 0;
        while (j <= nyp) {
            i = 0;
            while (i <= nxp) {
                if (Bbox.val[getInt3dindex(Bbox,i,j,k)] == AGG) vol++;
                i++;
            }
            j++;
        }
        k++;
    }

    if (Debug) {
        printf("\nIn placerealshape, Vol = %d compared to %d, ",vol,numvoxthis);
        printf("(x,y,z) = (%d,%d,%d), phase = %d",xin,yin,zin,phaseid);
        fflush(stdout);
    }

    xc = (int)((float)(0.50 * nxp) + 0.01);
    yc = (int)((float)(0.50 * nyp) + 0.01);
    zc = (int)((float)(0.50 * nzp) + 0.01);

    curpart = Npart - 1;
    if (Debug) {
        printf("\n\t\tBeginning of pore list is %d",(Pore_head)->ns);
        fflush(stdout);
        printf("\n\t\tPore head value = ");
        fflush(stdout);
        printf("%d",(Pore_head)->ns);
        fflush(stdout);
        printf("\n\t\tPore list length =  ");
        fflush(stdout);
        printf("%d",Pore_length());
        fflush(stdout);
    }

    /* Pore_display(); */

    /* Allocate space for new particle info */

    Particle[curpart] = particlevector(vol);
    if (!Particle[curpart]) {
        bailout("genaggpack","Memory allocation error");
        fflush(stdout);
        printf("\nNeed to delete %d pore voxels from list 06",Pore_length());
        fflush(stdout);
        if (Pore_delete()) {
            printf("\nError: Had trouble deleting Pore list");
            fflush(stdout);
        }
    }

    if (Npart >= 1258 && Npart <= 3935) {
        printf("\nSuccessfully allocated Particle %d",curpart);
        fflush(stdout);
    }

    Particle[curpart]->partid = Npart;
    Particle[curpart]->partphase = phaseid;
    Particle[curpart]->settled = 0;
    Particle[curpart]->xd = nxp;
    Particle[curpart]->yd = nyp;
    Particle[curpart]->zd = nzp;
    Particle[curpart]->xc = xin + (int)(0.5 * Particle[curpart]->xd + 0.5);
    Particle[curpart]->xc += checkbc(Particle[curpart]->xc,Xsyssize);
    Particle[curpart]->yc = yin + (int)(0.5 * Particle[curpart]->yd + 0.5);
    Particle[curpart]->yc += checkbc(Particle[curpart]->yc,Ysyssize);
    Particle[curpart]->zc = zin + (int)(0.5 * Particle[curpart]->zd + 0.5);
    Particle[curpart]->zc += checkbc(Particle[curpart]->zc,Zsyssize);

    Pindextable[curpart] = curpart;

    if (Npart >= 1258 && Npart <= 3935) {
        printf("\n\tParticle[%d]->partid = %d",curpart,Particle[curpart]->partid);
        printf("\n\tParticle[%d]->partphase = %d",curpart,Particle[curpart]->partphase);
        printf("\n\tParticle[%d]->settled = %d",curpart,Particle[curpart]->settled);
        printf("\n\tParticle[%d]->xd = %d",curpart,Particle[curpart]->xd);
        printf("\n\tParticle[%d]->yd = %d",curpart,Particle[curpart]->yd);
        printf("\n\tParticle[%d]->zd = %d",curpart,Particle[curpart]->zd);
        printf("\n\tParticle[%d]->xc = %d",curpart,Particle[curpart]->xc);
        printf("\n\tParticle[%d]->yc = %d",curpart,Particle[curpart]->yc);
        printf("\n\tParticle[%d]->zc = %d",curpart,Particle[curpart]->zc);
        fflush(stdout);
    }

    k = j = i = 0;
    numvox = numperiph = 0;
    while (k <= nzp) {
        j = 0;
        while (j <= nyp) {
            i = 0;
            while (i <= nxp) {
                i1 = xin + (i - xc);
                /* i1 = xin + i; */
                i1 += checkbc(i1,Xsyssize);
                j1 = yin + (j - yc);
                /* j1 = yin + j; */
                j1 += checkbc(j1,Ysyssize);
                k1 = zin + (k - zc);
                /* k1 = zin + k; */
                k1 += checkbc(k1,Zsyssize);
                if (Debug) {
                    printf("\n*(i,j,k) = (%d,%d,%d), (xin,yin,zin) = (%d,%d,%d), (i1,j1,k1) = (%d,%d,%d)",i,j,k,xin,yin,zin,i1,j1,k1);
                    fflush(stdout);
                }
                if (Bbox.val[getInt3dindex(Bbox,i,j,k)] == AGG) {
                    Agg.val[getInt3dindex(Agg,i1,j1,k1)] = phaseid;
                    Pagg.val[getInt3dindex(Pagg,i1,j1,k1)] = Npart;
                    if (Debug) {
                        printf("\nDeleting one voxel %d, %d so far",voxpos(i1,j1,k1),numvox);
                        fflush(stdout);
                    }

                    /* Need to store voxel positions on the periphery separately */

                    if (isPeriph(i,j,k)) {
                        Particle[curpart]->pvid[numperiph] = numvox;
                        if (k1 < minz) {
                            minz = k1;
                            Particle[curpart]->minz = numvox;
                        }
                        numperiph++;
                    }
                    Particle[curpart]->xi[numvox] = i1;
                    Particle[curpart]->yi[numvox] = j1;
                    Particle[curpart]->zi[numvox] = k1;
                    if (curpart == 1834) {
                        printf("\nParticle[%d]->xi[%d] = %d, ",curpart,numvox,Particle[curpart]->xi[numvox]);
                        printf("Particle[%d]->yi[%d] = %d, ",curpart,numvox,Particle[curpart]->yi[numvox]);
                        printf("Particle[%d]->zi[%d] = %d",curpart,numvox,Particle[curpart]->zi[numvox]);
                        fflush(stdout);
                    }
                    numvox++;
                }
                i++;
            }
            j++;
        }
        k++;
    }

    Particle[curpart]->numperiph = numperiph;
    if (minz == 0) Particle[curpart]->settled = 1;

    if (numperiph > 1500) {
        printf("\nFound large particle number %d:",curpart);
        printf("\n\tParticle[%d]->partid = %d",curpart,Particle[curpart]->partid);
        printf("\n\tParticle[%d]->nump = %d",curpart,numvox);
        printf("\n\tParticle[%d]->numperiph = %d",curpart,Particle[curpart]->numperiph);
        printf("\n\tParticle[%d]->partphase = %d",curpart,Particle[curpart]->partphase);
        printf("\n\tParticle[%d]->center = (%d,",curpart,Particle[curpart]->xc);
        printf("%d,%d)",Particle[curpart]->yc,Particle[curpart]->zc);
        fflush(stdout);
    }

    if (Debug) {
        printf("\nLeaving checkrealpart after placing particle with %d voxels",numvox);
        fflush(stdout);
    }

    return(numvox);
}

/***
*    settle
*
*    routine to move the placed particles "downward" toward the bottom
*    of the box in an attempt to free up more space for additional particles
*
*     Arguments:
*         None
*
*     Returns:    number of particles that attempted to settle
*
*    Calls:        checkbc
*    Called by:    genparticles
***/
int settle(void)
{
    int i,j,k,vnum,part,per;
    int iold,jold,kold;
    int inew,jnew,knew;
    int iback,jback,kback;
    int partid,pvid,idx;
    int status = 0;
    int blocked = 0;
    int downshift;
    int numsettled = 0;
    int numshift,xshift,yshift;
    int maxshift = 4;

    /* Sort the particles in ascending order of their minimum
     * z-coordinate
     */ 

    if (Verbose) {
        printf("\nSETTLE:  Sorting particles...");
        fflush(stdout);
    }
    status = sortParticles();
    if (Verbose) {
        printf(" Done!\n");
        fflush(stdout);
    }

    /* Starting with the "lowest" particles, move them straight down
     * until they hit something or their minimum z-coordinate is zero
     *
     * When they hit an obstacle, make a random shift in the xy plane
     * and try to move down some more.  Repeat this procedure for
     * a maximum of maxshift attempts
     */ 

    for (idx = 0; idx < Npart; idx++) {

        part = Pindextable[idx];

        if (Debug) {
            printf("\nWorking on particle %d of %d",part,Npart);
            fflush(stdout);
        }
        if (Particle[part] == NULL) {
            printf("\nERROR:  Trying to access a particle without a Particle structure allocated");
            fflush(stdout);
        } else if (!Particle[part]->settled) {
            if (Debug) {
                printf("\nSettling particle %d of %d with ",part,Npart-1);
                printf("%d periphery voxels (numperiph[0] = ",Particle[part]->numperiph);
                printf("%d ...",Particle[0]->numperiph);
                fflush(stdout);
            }

            numsettled++;
            blocked = per = numshift = 0;
            downshift = xshift = yshift = 0;
            partid = Particle[part]->partid;

            do {
                if (Debug) {
                    printf("\n    Particle %d, downshift = %d, numperiph[0] = %d",part,downshift,Particle[0]->numperiph);
                    fflush(stdout);
                }
                /* Make a trial move one z down and check periphery voxels */
                while (per < Particle[part]->numperiph && !blocked) {
                    pvid = Particle[part]->pvid[per];
                    if (Debug) {
                        printf("\n        Particle %d, Periph voxel %d at ",part,per);
                        fflush(stdout);
                    }
                    i = Particle[part]->xi[pvid] + xshift;
                    i += checkbc(i,Xsyssize);
                    j = Particle[part]->yi[pvid] + yshift;
                    j += checkbc(j,Ysyssize);
                    k = Particle[part]->zi[pvid] - 1;
                    if (k < 0) blocked = 1;
                    if (Debug) {
                        printf("(%d,%d,%d) ->",i,j,k+1);
                        fflush(stdout);
                    }
                    k += checkbc(k,Zsyssize);
                    if (Debug) {
                        printf(" (%d,%d,%d), blocked =  %d, numperiph[%d] = %d",i,j,k,blocked,part,Particle[part]->numperiph);
                        fflush(stdout);
                    }
                    if ((Pagg.val[getInt3dindex(Pagg,i,j,k)] != partid)
                            && (Pagg.val[getInt3dindex(Pagg,i,j,k)] != POROSITY)) {
                        blocked = 1;
                        if (Debug) {
                            printf(" BLOCKED!!");
                        }
                    }
                    per++;
                }

                /** Update all the particle's voxel positions if not blocked **/

                if (!blocked) {
                    if (Debug) {
                        printf("\n            NOT BLOCKED! Moving down for real, numperiph[0] = %d",Particle[0]->numperiph);
                        fflush(stdout);
                    }

                    /* Update all voxel positions */
                    for (vnum = 0; vnum < Particle[part]->numvox; vnum++) {
                        if (Debug) {
                            printf("\n                Settling voxel %d of %d at (",vnum,Particle[part]->numvox);
                            fflush(stdout);
                        }
                        inew = Particle[part]->xi[vnum] + xshift;
                        inew += checkbc(inew,Xsyssize);
                        jnew = Particle[part]->yi[vnum] + yshift;
                        jnew += checkbc(jnew,Ysyssize);
                        iold = Particle[part]->xi[vnum];
                        jold = Particle[part]->yi[vnum];
                        kold = Particle[part]->zi[vnum];
                        knew = kold - 1;
                        knew += checkbc(knew,Zsyssize);
                        if (Debug) {
                            printf("%d,%d,%d) -> (%d,%d,%d), numperiph[0] = %d",iold,jold,kold,inew,jnew,knew,Particle[0]->numperiph);
                            fflush(stdout);
                        }
                        Particle[part]->xi[vnum] = inew;
                        Particle[part]->yi[vnum] = jnew;
                        Particle[part]->zi[vnum] = knew;

                        /* Also need to update actual microstructure voxel states */
                        iback = iold - xshift;
                        iback += checkbc(iback,Xsyssize);
                        jback = jold - yshift;
                        jback += checkbc(jback,Ysyssize);
                        kback = kold + 1;
                        kback += checkbc(kback,Zsyssize);
                        if (Debug) {
                            printf("\n                Changing ids, numperiph[0] = %d... ",Particle[0]->numperiph);
                            fflush(stdout);
                        }
                        Pagg.val[getInt3dindex(Pagg,inew,jnew,knew)] = partid;
                        Agg.val[getInt3dindex(Agg,inew,jnew,knew)] = Particle[part]->partphase;
                        if (Pagg.val[getInt3dindex(Pagg,iback,jback,kback)] != partid) {
                            Pagg.val[getInt3dindex(Pagg,iold,jold,kold)] = POROSITY;
                            Agg.val[getInt3dindex(Agg,iold,jold,kold)] = POROSITY;
                        }
                        if (Debug) {
                            printf("Done, numperiph[0] = %d",Particle[0]->numperiph);
                            fflush(stdout);
                        }
                    }

                    downshift++;
                    xshift = yshift = 0;
                    numshift = 0;
                    per = 0;

                } else if (numshift < maxshift) {

                    if (Debug) {
                        printf("\n\tBLOCKED! Shifting %d, numperiph[0] = %d",numshift,Particle[0]->numperiph);
                        fflush(stdout);
                    }
                    switch (numshift) {
                        case 0:
                            xshift = 1;
                            yshift = 0;
                            break;
                        case 1:
                            xshift = -1;
                            yshift = 0;
                            break;
                        case 2:
                            yshift = 1;
                            xshift = 0;
                            break;
                        default:
                            yshift = -1;
                            xshift = 0;
                            break;
                    }

                    blocked = 0;
                    per = 0;
                    numshift++;
                }

            } while ((!blocked) && (numshift <= maxshift));


            Particle[part]->settled = 1;

            if (Debug) {
                printf("\nDone with particle %d, moving on to particle ",part);
                printf("%d of %d\n",part+1,Npart);
                fflush(stdout);
            }
        }
    }

    printf("\nDone settling.");
    fflush(stdout);

    return(numsettled);
}

/***
*    sortParticles
*
*    routine to sort the list of particles in ascending order of
*    their minimum z-coordinate
*
*     Arguments:
*         None
*
*     Returns:    0 if function worked, 1 if it failed somehow
*
*    Calls:        nothing
*    Called by:    settle
***/
int sortParticles(void)
{
    int i,j,k;
    int isperiph;
    char fname[128];
    FILE *fpout;

    int icop = 0;

    sprintf(fname,"ParticleData-%d.txt",Filecount);
    Filecount++;

    fpout = filehandler("genaggpack",fname,"WRITE");
    if (!fpout) { 
        freeallmem();
        return(MEMERR);
    }
    
    for (i = 0; i < Npart; i++) {
        Pindextable[i] = i;
    }

    for (i = 0; i < Npart; i++) {
        if (i != 0) fprintf(fpout,"\n");
        fprintf(fpout,"Particle %d:\n",i);
        fflush(fpout);
        fprintf(fpout,"\tpartid = %d\n",Particle[i]->partid);
        fflush(fpout);
        fprintf(fpout,"\tpartphase = %d\n",Particle[i]->partphase);
        fflush(fpout);
        fprintf(fpout,"\tsettled = %d\n",Particle[i]->settled);
        fflush(fpout);
        fprintf(fpout,"\tnumvox = %d\n",Particle[i]->numvox);
        fflush(fpout);
        fprintf(fpout,"\tnumperiph = %d\n",Particle[i]->numperiph);
        fflush(fpout);
        fprintf(fpout,"\t(xc,yc,zc) = (%d,%d,%d)\n",Particle[i]->xc,Particle[i]->yc,Particle[i]->zc);
        fflush(fpout);
        fprintf(fpout,"\tminz = %d\n",Particle[i]->minz);
        fflush(fpout);
        for (j = 0; j < Particle[i]->numvox; j++) {
            fprintf(fpout,"\t\tVoxel %d: (%d,%d,%d)",j,Particle[i]->xi[j],Particle[i]->yi[j],Particle[i]->zi[j]);
            fflush(fpout);
            isperiph = 0;
            for (k = 0; k < Particle[i]->numperiph; k++) {
                if (Particle[i]->pvid[k] == j) isperiph = 1;
            }
            if (isperiph) {
                fprintf(fpout," [periph]\n");
            } else {
                fprintf(fpout,"\n");
            }
            fflush(fpout);
        }
    }

    fclose(fpout);

    /* Allocate space for Particle copy */
    /*
    pcop = particlevector(1000);
    if (pcop == NULL) {
        printf("\nERROR:  Could not allocate temporary memory for particle sorting");
        fflush(stdout);
        return (MEMERR);
    }
    */

    /* Naive bubble sort (my favorite kind!) */

    for (i = 0; i < Npart; i++) {
        for (j = (i+1); j < Npart; j++) {
            if (Particle[Pindextable[j]]->minz < Particle[Pindextable[i]]->minz) {
                icop = Pindextable[j];
                Pindextable[j] = Pindextable[i];
                Pindextable[i] = icop;
            }
        }
    }

    /*
    free(pcop);
    */

    return(0);
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
*     Returns:    integer flag telling number of solid voxels in the particle
*
*    Calls:        checkbc
*    Called by:    genparticles
***/
int image(int *nxp, int *nyp, int *nzp)
{
    int partc = 0;
    int n,m,i,j,k,count;
    int minx,miny,minz,maxx,maxy,maxz;
    fcomplex rr;
    double xc,yc,zc,x1,y1,z1,r;
    double theta,phi;

    xc = (0.50 * (*nxp)) + 0.01;
    yc = (0.50 * (*nyp)) + 0.01;
    zc = (0.50 * (*nzp)) + 0.01;

    if (Debug) {
        printf("\nEntering first image loop: nxp = %d, nyp= %d, ",*nxp,*nyp);
        printf("nzp = %d, Nnn = %d",*nzp,Nnn);
        fflush(stdout);
    }   

    for (k = 0; k < Boxsize; k++) {
        for (j = 0; j < Boxsize; j++) {
            for (i = 0; i < Boxsize; i++) {
                Bbox.val[getInt3dindex(Bbox,i,j,k)] = POROSITY;
            }
        }
    }

    /***
    *    Assigning solid voxels within Bbox, with id AGG
    ***/

    /*** JWB:  FIND MINIMUM ENCLOSING DIMENSIONS FOR THIS PARTICLE  ***/
    /*** JWB:  IDEA IS TO USE THE LONGEST DIMENSION TO SET THE PORE ***/
    /*** JWB:  RADIUS TO CHECK FOR FITTING                          ***/

    count = 0;
    for (k = 0; k <= *nzp
        && (*nzp < (int)(0.8 * Zsyssize))
        && (*nyp < (int)(0.8 * Ysyssize))
        && (*nxp < (int)(0.8 * Xsyssize)); k++) {
        for (j = 0; j <= *nyp; j++) {
            for (i = 0; i <= *nxp; i++) {

                x1 = (double) i;
                y1 = (double) j;
                z1 = (double) k;

                r = sqrt(((x1-xc)*(x1-xc))
                        + ((y1-yc)*(y1-yc))
                        + ((z1-zc)*(z1-zc)));
                if (r == 0.0) {
                    count++;
                    Bbox.val[getInt3dindex(Bbox,i,j,k)] = AGG;
                    break;
                }

                theta = acos((z1-zc)/r);
                phi = atan((y1-yc)/(x1-xc));

                if ((y1-yc) < 0.0 && (x1-xc) < 0.0) phi += Pi;
                if ((y1-yc) > 0.0 && (x1-xc) < 0.0) phi += Pi;
                if ((y1-yc) < 0.0 && (x1-xc) > 0.0) phi += 2.0 * Pi;
                harm(theta,phi);
                rr = Complex(0.0,0.0);
                rr = Cmul(AA[0][0],Y[0][0]);
                for (n = 1; n <= Nnn; n++) {
                    for (m = -n; m <= n; m++) {
                           rr = Cadd(rr,Cmul(AA[n][m],Y[n][m]));
                    }
                }

                if (r <= (rr.r)) {
                    Bbox.val[getInt3dindex(Bbox,i,j,k)] = AGG;
                    count++;
                }
            }
        }
    }

    maxx = maxy = maxz = 0;
    minx = Xsyssize;
    miny = Ysyssize;
    minz = Zsyssize;
    for (k = 0; k <= *nzp; ++k) {
        for (j = 0; j <= *nyp; ++j) {
            for (i = 0; i <= *nxp; ++i) {
                if (Bbox.val[getInt3dindex(Bbox,i,j,k)] == AGG) {
                    if (i > maxx) maxx = i;
                    if (j > maxy) maxy = j;
                    if (k > maxz) maxz = k;
                    if (i < minx) minx = i;
                    if (j < miny) miny = j;
                    if (k < minz) minz = k;
                }
            }
        }
    }

    /* Move particles to smallest possible box */

    for (k = 0; k <= maxz; ++k) {
        for (j = 0; j <= maxy; ++j) {
            for (i = 0; i <= maxx; ++i) {
                Bbox.val[getInt3dindex(Bbox,i,j,k)] =
                    Bbox.val[getInt3dindex(Bbox,minx+i,miny+j,minz+k)];
            }
        }
    }

    *nzp = maxz - minz;
    *nyp = maxy - miny;
    *nxp = maxx - minx;

    partc = count;

    return(partc);
}

/***
*    smallimage
*
*     Special case of digitizing images for real-shaped
*     particles when their volume is less than four voxels.
*     In this case, we bypass SH reconstruction, volume
*     adjustment, etc., and just manually place the particles
*     in Bbox
*
*     Arguments:
*         int nxp,nyp,nzp are the dimensions of the bounding box
*         int vol is the number of voxels comprising the particle
*
*     Returns:    integer flag telling number of solid voxels in the particle
*
*    Calls:        checkbc
*    Called by:    genparticles
***/
int smallimage(int *nxp, int *nyp, int *nzp, int vol)
{
    int min,maxdim = 10;
    int orient;
    int i,j,k,v;
    float choice,dist,di2,dj2,dk2;

    min = 1;

    /***
    *    Initialize Bbox array to porosity.  We initialize out to a cube
    *    having edge length equal to the maximum edge length of the
    *    bounding box, because later we may do a rigid body rotation,
    *    reflection, or inversion of the entire contents in place.
    ***/

    for (k = 0; k < maxdim; k++) {
        for (j = 0; j < maxdim; j++) {
            for (i = 0; i < maxdim; i++) {
                Bbox.val[getInt3dindex(Bbox,i,j,k)] = POROSITY;
            }
        }
    }

    /***
    *    Assigning solid voxels within Bbox, with id SANDINCONCRETE
    ***/

    if (vol <= 4) {

        *nxp = 6;
        *nyp = 6;
        *nzp = 6;
    
        if (vol == 4) {
            orient = 1 + (int)(3.0 * ran1(Seed));
            switch (orient) {
                case 1:
                    Bbox.val[getInt3dindex(Bbox,min,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min+1,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min+1,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min+1,min+1,min)] = SANDINCONCRETE;
                    *nzp = 5;
                    break;
                case 2:
                    Bbox.val[getInt3dindex(Bbox,min,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min,min+1)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min+1,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min+1,min+1)] = SANDINCONCRETE;
                    *nxp = 5;
                    break;
                case 3:
                    Bbox.val[getInt3dindex(Bbox,min,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min+1,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min,min+1)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min+1,min,min+1)] = SANDINCONCRETE;
                    *nyp = 5;
                    break;
                default:
                    Bbox.val[getInt3dindex(Bbox,min,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min+1,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min+1,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min+1,min+1,min)] = SANDINCONCRETE;
                    *nzp = 5;
                    break;
            }
            return(4);
        } else if (vol == 3) {
            orient = 1 + (int)(3.0 * ran1(Seed));
            switch (orient) {
                case 1:
                    Bbox.val[getInt3dindex(Bbox,min,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min+1,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min+1,min)] = SANDINCONCRETE;
                    *nzp = 5;
                    break;
                case 2:
                    Bbox.val[getInt3dindex(Bbox,min,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min,min+1)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min+1,min)] = SANDINCONCRETE;
                    *nxp = 5;
                    break;
                case 3:
                    Bbox.val[getInt3dindex(Bbox,min,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min,min+1)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min+1,min,min)] = SANDINCONCRETE;
                    *nyp = 5;
                    break;
                default:
                    Bbox.val[getInt3dindex(Bbox,min,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min+1,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min+1,min)] = SANDINCONCRETE;
                    *nzp = 5;
                    break;
            }
            return(3);
        } else {
            orient = 1 + (int)(3.0 * ran1(Seed));
            switch (orient) {
                case 1:
                    Bbox.val[getInt3dindex(Bbox,min,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min+1,min,min)] = SANDINCONCRETE;
                    *nyp = 5;
                    *nzp = 5;
                    break;
                case 2:
                    Bbox.val[getInt3dindex(Bbox,min,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min+1,min)] = SANDINCONCRETE;
                    *nxp = 5;
                    *nzp = 5;
                    break;
                case 3:
                    Bbox.val[getInt3dindex(Bbox,min,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min,min,min+1)] = SANDINCONCRETE;
                    *nxp = 5;
                    *nyp = 5;
                    break;
                default:
                    Bbox.val[getInt3dindex(Bbox,min,min,min)] = SANDINCONCRETE;
                    Bbox.val[getInt3dindex(Bbox,min+1,min,min)] = SANDINCONCRETE;
                    *nyp = 5;
                    *nzp = 5;
                    break;
            }
            return(2);
        }

    } else {  /*  Volume is greater than 4.  Use a corroded sphere of diameter 3 */

        *nxp = 5;
        *nyp = 5;
        *nzp = 5;

        for (k = -1; k <2; k++) {
            dk2 = (float)(k * k);
            for (j = -1; j <2; j++) {
                dj2 = (float)(j * j);
                for (i = -1; i <2; i++) {
                    di2 = (float)(i * i);
                    dist = sqrt(di2 + dj2 + dk2);
                    if ((dist - 0.5) <= 1.5) {
                        Bbox.val[getInt3dindex(Bbox,3+i,3+j,3+k)] = SANDINCONCRETE;
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
            if (Bbox.val[getInt3dindex(Bbox,3+i,3+j,3+k)] == SANDINCONCRETE) {
                Bbox.val[getInt3dindex(Bbox,3+i,3+j,3+k)] = POROSITY;
                v -= 1;
            }
        }
        return(vol);
    }
}

/***
*    sphereimage
*
*     For spheres, populates the Bbox matrix with the
*     sphere, placing 1's everywhere
*
*     Arguments:
*         int nxp,nyp,nzp is the dimension of the bounding box
*         float rad is the radius of the sphere
*
*     Returns:    integer flag telling number of solid voxels in the sphere
*
*    Calls:        checkbc
*    Called by:    genparticles
***/
int sphereimage(int *nxp, int *nyp, int *nzp, float rad)
{
    int partc = 0;
    int idiam,irad,i,j,k,ixc,jxc,kxc,count;
    float xc,yc,zc,xdist,ydist,zdist,dist,offset,ftmp;

    /* Initialize Bbox to porosity everywhere */

    for (k = 0; k <= *nzp; k++) {
        for (j = 0; j <= *nyp; j++) {
            for (i = 0; i <= *nxp; i++) {
                Bbox.val[getInt3dindex(Bbox,i,j,k)] = POROSITY;
            }
        }
    }

    xc = (0.50 * (*nxp)) + 0.01;
    yc = (0.50 * (*nyp)) + 0.01;
    zc = (0.50 * (*nzp)) + 0.01;

    ixc = (int)(xc + 0.5);
    jxc = (int)(yc + 0.5);
    kxc = (int)(zc + 0.5);

    idiam = (int)((2.0 * rad) + 0.5);
    if ((idiam%2) == 0) {
        offset = -0.5;
        irad = idiam / 2;
    } else {
        offset = 0.0;
        irad = (idiam - 1) / 2;
    }

    if (Debug) {
        printf("\nEntering sphereimage loop: nxp = %d, nyp= %d, ",*nxp,*nyp);
        printf("nzp = %d, frad = %.3f, irad = %d",*nzp,rad,irad);
        fflush(stdout);
    }   

    /***
    *    Assigning solid voxels within Bbox, with id AGG
    ***/

    count = 0;
    for (k = -(irad); k <= irad; k++) {
        ftmp = (float)(k - offset);
        zdist = ftmp * ftmp;
        for (j = -(irad); j <= irad; j++) {
            ftmp = (float)(j - offset);
            ydist = ftmp * ftmp;
            for (i = -(irad); i <= irad; i++) {
                ftmp = (float)(i - offset);
                xdist = ftmp * ftmp;
                dist = sqrt(xdist + ydist + zdist);
                if ((dist - 0.5) <= ((float)irad)) {
                    Bbox.val[getInt3dindex(Bbox,i+xc,j+yc,k+zc)] = AGG;
                    count++;
                }
            }
        }
    }

    partc = count;

    return(partc);
}

/***
*    adjustvol
*
*     For real shape particles, adjusts by several voxels the
*     volume of the particle.  Needed to get exact match of voxel
*     volume to target value.
*
*   Only fool-proof way to do this seems to be to find the surface
*   of the particle, make a linked list of the surface voxels and
*   then select one at random
*
*     Arguments:
*         int number to add (negative if subtracting)
*         int x,y,and z dimensions of the bounding box
*
*     Returns:    integer flag telling number of solid voxels added
*
*    Calls:        no functions
*    Called by:    genparticles
***/
int adjustvol(int diff, int nxp, int nyp, int nzp)
{
    int i,j,k,count,absdiff,n;
    int choice,numsp;
    struct Surfvox sp[MAXSP];

    /* Initialize local sp array */

    for (i = 0; i < MAXSP; i++) {
        sp[i].x = 0;
        sp[i].y = 0;
        sp[i].z = 0;
    }

    absdiff = abs(diff);

    /* Populate list of surface voxels */

    numsp = 0;
    if (diff > 0) {
        /* add solid voxels to surface */
        for (i = 1; i < nxp; i++) {
            for (j = 1; j < nyp; j++) {
                for (k = 1; k < nzp; k++) {
                    if (Bbox.val[getInt3dindex(Bbox,i,j,k)] == POROSITY
                           && ( (Bbox.val[getInt3dindex(Bbox,i+1,j,k)] == AGG)
                               || (Bbox.val[getInt3dindex(Bbox,i-1,j,k)] == AGG)
                               || (Bbox.val[getInt3dindex(Bbox,i,j+1,k)] == AGG)
                               || (Bbox.val[getInt3dindex(Bbox,i,j-1,k)] == AGG)
                               || (Bbox.val[getInt3dindex(Bbox,i,j,k+1)] == AGG)
                               || (Bbox.val[getInt3dindex(Bbox,i,j,k-1)] == AGG)
                        ) ) {
                        /* add i,j,k to surface voxels */
                        sp[numsp].x = i;
                        sp[numsp].y = j;
                        sp[numsp].z = k;
                        numsp++;
                    }
                }
            }
        }
    } else {
        /* remove solid voxels from surface */
        for (i = 0; i <= nxp; i++) {
            for (j = 0; j <= nyp; j++) {
                for (k = 0; k <= nzp; k++) {
                    if (Bbox.val[getInt3dindex(Bbox,i,j,k)] == AGG
                           && ( (Bbox.val[getInt3dindex(Bbox,i+1,j,k)] == POROSITY)
                              || (Bbox.val[getInt3dindex(Bbox,i-1,j,k)] == POROSITY)
                              || (Bbox.val[getInt3dindex(Bbox,i,j+1,k)] == POROSITY)
                              || (Bbox.val[getInt3dindex(Bbox,i,j-1,k)] == POROSITY)
                              || (Bbox.val[getInt3dindex(Bbox,i,j,k+1)] == POROSITY)
                              || (Bbox.val[getInt3dindex(Bbox,i,j,k-1)] == POROSITY)
                        ) ) {
                        /* add i,j,k to surface voxels */

                        sp[numsp].x = i;
                        sp[numsp].y = j;
                        sp[numsp].z = k;
                        numsp++;
                    }
                }
            }
        }
    }

    if (Debug) {
        printf("\nIn adjustvol, diff = %d and num surf vox = %d",diff,numsp);
        fflush(stdout);
    }

    count = 0;
    for (n = 1; n <= absdiff; n++) {
        
        /***
        *    randomly select a surface voxel from the list
        ***/
        
        choice = (int)(numsp * ran1(Seed)); 
        if (Debug) {
            printf("\n\tIn adjustvol random choice = %d",choice);
            fflush(stdout);
        }

        if (choice > numsp) break;
        if (Bbox.val[getInt3dindex(Bbox,sp[choice].x,sp[choice].y,sp[choice].z)] == AGG) {
            Bbox.val[getInt3dindex(Bbox,sp[choice].x,sp[choice].y,sp[choice].z)] = POROSITY;
            count--;
        } else {
            Bbox.val[getInt3dindex(Bbox,sp[choice].x,sp[choice].y,sp[choice].z)] = AGG;
            count++;
        }
        for (i = choice; i < numsp - 1; i++) {
            sp[i].x = sp[i+1].x;
            sp[i].y = sp[i+1].y;
            sp[i].z = sp[i+1].z;
        }
        sp[numsp-1].x = 0;
        sp[numsp-1].y = 0;
        sp[numsp-1].z = 0;
        numsp--;
        if (Debug) {
            printf("\n\t\tcount = %d and numsp = %d",count,numsp);
            fflush(stdout);
        }
    }

    return(count);
}

/***
*    additz
*
*     Adds a layer of id ITZ
*     around the periphery of all particles.
*
*     Arguments:  None
*     Returns:    int number of ITZ voxels created
*
*    Calls:        no functions
*    Called by:    genparticles
***/
int additz(void)
{
    int i,j,k,ii,jj,kk,pos,found;
    int pval,firstnpores;
    int numpores = 0;
    int count = 0;
    struct Pore *temp = NULL;

    /* Create the pore list */
    numpores = Pore_create_porelist(0,1.0,&firstnpores);

    for (temp = Pore_head; temp != Pore_tail; temp = temp->next) {
        i = getXfromNs(temp->ns);
        j = getYfromNs(temp->ns);
        k = getZfromNs(temp->ns);
        found = 0;
        for (pos = 0; pos < 18 && !found; pos++) {
            switch (pos) {
                case 0:  /* x neg, y 0, z 0 */
                    ii = i - 1 + checkbc(i-1,Xsyssize);
                    jj = j;
                    kk = k;
                    break;
                case 1:  /* x pos, y 0, z 0 */
                    ii = i + 1 + checkbc(i+1,Xsyssize);
                    jj = j;
                    kk = k;
                    break;
                case 2:  /* x 0, y neg, z 0 */
                    jj = j - 1 + checkbc(j-1,Ysyssize);
                    ii = i;
                    kk = k;
                    break;
                case 3:  /* x 0, y pos, z 0 */
                    jj = j + 1 + checkbc(j+1,Ysyssize);
                    ii = i;
                    kk = k;
                    break;
                case 4:  /* x 0, y 0, z neg */
                    kk = k - 1 + checkbc(k-1,Zsyssize);
                    ii = i;
                    jj = j;
                    break;
                case 5:  /* x 0, y 0, z pos */
                    kk = k + 1 + checkbc(k+1,Zsyssize);
                    ii = i;
                    jj = j;
                    break;
                case 6:  /* x neg, y neg, z 0 */
                    ii = i - 1 + checkbc(i-1,Xsyssize);
                    jj = j - 1 + checkbc(j-1,Ysyssize);
                    kk = k;
                    break;
                case 7:  /* x pos, y neg, z 0 */
                    ii = i + 1 + checkbc(i+1,Xsyssize);
                    jj = j - 1 + checkbc(j-1,Ysyssize);
                    kk = k;
                    break;
                case 8:  /* x neg, y pos, z 0 */
                    ii = i - 1 + checkbc(i-1,Xsyssize);
                    jj = j + 1 + checkbc(j+1,Ysyssize);
                    kk = k;
                    break;
                case 9:  /* x pos, y pos, z 0 */
                    ii = i + 1 + checkbc(i+1,Xsyssize);
                    jj = j + 1 + checkbc(j+1,Ysyssize);
                    kk = k;
                    break;
                case 10:  /* x neg, y 0, z neg */
                    ii = i - 1 + checkbc(i-1,Xsyssize);
                    kk = k - 1 + checkbc(k-1,Zsyssize);
                    jj = j;
                    break;
                case 11:  /* x pos, y 0, z neg */
                    ii = i + 1 + checkbc(i+1,Xsyssize);
                    kk = k - 1 + checkbc(k-1,Zsyssize);
                    jj = j;
                    break;
                case 12:  /* x neg, y 0, z pos */
                    ii = i - 1 + checkbc(i-1,Xsyssize);
                    kk = k + 1 + checkbc(k+1,Zsyssize);
                    jj = j;
                    break;
                case 13:  /* x pos, y 0, z pos */
                    ii = i + 1 + checkbc(i+1,Xsyssize);
                    kk = k + 1 + checkbc(k+1,Zsyssize);
                    jj = j;
                    break;
                case 14:  /* x 0, y neg, z neg */
                    jj = j - 1 + checkbc(j-1,Ysyssize);
                    kk = k - 1 + checkbc(k-1,Zsyssize);
                    ii = i;
                    break;
                case 15:  /* x 0, y pos, z neg */
                    jj = j + 1 + checkbc(j+1,Ysyssize);
                    kk = k - 1 + checkbc(k-1,Zsyssize);
                    ii = i;
                    break;
                case 16:  /* x 0, y neg, z pos */
                    jj = j - 1 + checkbc(j-1,Ysyssize);
                    kk = k + 1 + checkbc(k+1,Zsyssize);
                    ii = i;
                    break;
                case 17:  /* x 0, y pos, z pos */
                    jj = j + 1 + checkbc(j+1,Ysyssize);
                    kk = k + 1 + checkbc(k+1,Zsyssize);
                    ii = i;
                    break;
            }

            pval = Agg.val[getInt3dindex(Agg,ii,jj,kk)];
            if ((pval != POROSITY) && (pval != ITZ)) {
                Agg.val[getInt3dindex(Agg,i,j,k)] = ITZ;
                count++;
                found = 1;
            }
        }
    }

    return(count);
}

/***
*    genpacking
*
*    Control routine to place spheres of various sizes and phases at random
*    locations in 3-D microstructure.
*
*     Arguments:
*        int type is the type of aggregate (FINE or COARSE)
*        int numsources is the number of sources of this type of aggregate
*        int sourceeach is which source of this aggregate class
*        int voleach holds the volume in voxels of each size class
*        int vp is the volume of a single particle in a given bin (in voxels)
*        int numeach holds the number of particles in each size class
*        float sizeeach holds the radius in voxels of each size class
*        FILE *fpout is the output file to write the SPH coefficients
*    Returns:    
*        0 if okay; nonzero if not
num*
*    Calls:        makesph, ran1
*    Called by:    create
***/
int genpacking(int type, int numsources, int sourceeach[NUMAGGBINS],
                  int voleach[NUMAGGBINS], int vp[NUMAGGBINS],
                  int numeach[NUMAGGBINS], float sizeeach[NUMAGGBINS],
                  FILE *fpout)
{
    int numshapes = 0;
    struct lineitem shapedata[MAXLINES];

    if (Shape == SPHERES) {

        packspheres(type,numsources,sourceeach,
                  voleach,vp,numeach,sizeeach,fpout);

    } else {

        /* Read the different shapes from the database */

        numshapes = readshapelines(shapedata);

        if (numshapes > 0) {
            if (packrealshapes(type,numshapes,numsources,sourceeach,
                  voleach,vp,numeach,sizeeach,shapedata,fpout) == MEMERR) {
                return(MEMERR);
            }
        } else {
            return(MEMERR);
        }

    }

    return(0);
}

/***
*    packspheres
*
*    Routine to place spheres of various sizes and phases at random
*    locations in 3-D microstructure.
*
*     Arguments:
*        int type is the type of aggregate (FINE or COARSE)
*        int numsources is the number of sources of this type of aggregate
*        int sourceeach is which source of this aggregate class
*        int voleach holds the volume in voxels of each size class
*        int vp is the volume of a single particle in a given bin (in voxels)
*        int numeach holds the number of particles in each size class
*        float sizeeach holds the radius in voxels of each size class
*        FILE *fpout is the output file to write the SPH coefficients
*    Returns:    
*        0 if okay; nonzero if not
num*
*    Calls:        makesph, ran1
*    Called by:    create
***/
int packspheres(int type, int numsources, int sourceeach[NUMAGGBINS],
                  int voleach[NUMAGGBINS], int vp[NUMAGGBINS],
                  int numeach[NUMAGGBINS], float sizeeach[NUMAGGBINS],
                  FILE *fpout)
{
    register int ig;
    int nxp,nyp,nzp,partc;
    int nvoxthis,numtoplace,numsphereplaced,phaseid,calcporesizes;
    int numvoxdiff,nextraspheres;
    float frad;

    /***
    *    Generate spheres of each size class
    *    in turn (largest first)
    ***/

    if (Verbose) {
        if (type == (int)COARSE) {
            printf("\nPlacing spherical coarse aggregate particles now...");
        } else {
            printf("\nPlacing spherical fine aggregate particles now...");
        }
        fflush(stdout);
    }

    /*** Loop over all size classes from big to small ***/

    numvoxdiff = 0;

    for (ig = 0; ig < Numaggbins; ig++) {

        /* Choose the correct voxel id for this aggregate */

        switch (sourceeach[ig]) {
            case 0:
                phaseid = FINEAGG01INCONCRETE;
                if (type == (int)COARSE) phaseid = COARSEAGG01INCONCRETE;
                break;
            case 1:
                phaseid = FINEAGG02INCONCRETE;
                if (type == (int)COARSE) phaseid = COARSEAGG02INCONCRETE;
                break;
            default:
                phaseid = FINEAGG01INCONCRETE;
                if (type == (int)COARSE) phaseid = COARSEAGG01INCONCRETE;
                break;
        }

        calcporesizes = 0;
        if (ig > MaxBinWithoutSorting) calcporesizes = 1;
 
        numtoplace = numeach[ig];        /* number of particles in this bin */
        nvoxthis = vp[ig];               /* volume of these particles in voxels */
        frad = (float)(sizeeach[ig]);    /* radius in voxel edge lengths */

        /* Produce a digitized sphere in Bbox */

        partc = digitizesphere(&nxp,&nyp,&nzp,nvoxthis,frad);

        /* Extra particles because prior class did not all fit? */
        nextraspheres = (int)((((float)(numvoxdiff)) / ((float)(partc))) + 0.5);
        numtoplace += nextraspheres;

        if (Verbose) {
            printf("\nPlacing sphere class %d of %d...",ig,Numaggbins);
            printf("\nTrying to add an extra %d spheres to this class",nextraspheres);
            printf("\n\t(%d total) because prior class did not all fit",numtoplace);
            fflush(stdout);
        }

        numsphereplaced = placesphereclass(numtoplace,nvoxthis,phaseid,
                                           calcporesizes,frad,
                                           &nxp,&nyp,&nzp,fpout);

        /* Move any remaining volume from this class to the next class */

        numvoxdiff = partc * (numtoplace - numsphereplaced);

        if (Verbose) {
            printf("\nPlaced %d of %d particles in class %d",numsphereplaced,numtoplace,ig);
            fflush(stdout);
            if (numvoxdiff != 0) {
                printf("\nPushing %d voxels to next size class",numvoxdiff);
            }
            fflush(stdout);
        }
    }

    return(0);
}

/***
*    placesphereclass
*
*    Routine to place spheres of various sizes and phases at random
*    locations in 3-D microstructure.
*
*     Arguments:
*               int numtoplace total spheres to place
*               int nvoxthis number of voxels in one sphere of this class
*               int phaseid is the phase id of the voxels in this sphere
*               int calcporesizes whether or not calculate the pore sizes
*               float frad the radius of these spheres
*               int *nxp, *nyp, *nzp, the dimenions of the bounding box Bbox
*               FILE *fpout for structure characteristics
*    Returns:    
*               number of spheres placed
num*
*    Calls:        makesph, ran1
*    Called by:    create
***/
int placesphereclass(int numtoplace, int nvoxthis, int phaseid, int calcporesizes,
                     float frad, int *nxp, int *nyp, int *nzp, FILE *fpout)
{
    register int jg;
    int fits,firstnpores,numpores;
    int ntotal,numvox,numsphereplaced,can_settle;
    int x,y,z;

    ntotal = numvox = numsphereplaced = 0;

    for (jg = 0; jg < numtoplace; jg++) {

        printf("\n**Working on sphere %d of %d ",jg,numtoplace);
        fflush(stdout);

        numpores = Pore_create_porelist(calcporesizes,frad,&firstnpores);

        if (numpores < 1) {
            printf("\nError:  Had trouble getting pore voxel list");
            fflush(stdout);
            return(MEMERR);
        }
    
        /* Iterate on this next loop until a placement position is found */

        fits = 0;
        can_settle = 1;

        do {

            if (firstnpores > 0) {

                fits = findsphereloc(&x,&y,&z,nxp,nyp,nzp,&numpores,&firstnpores,frad);
                if (Debug) {
                    printf("\nfits = %d, firstnpores = %d",fits,firstnpores);
                }

            } else {

                if (Verbose) {
                   printf("\nCould not find a spot for sphere %d\n",Npart);
                   printf("\n\tTotal pore voxels left is %d\n\n",numpores);
                   printf("\n\tSee if rearranging helps...");
                   fflush(stdout);
                }

                can_settle = settle();

                if (can_settle) {
                    numpores = Pore_create_porelist(calcporesizes,frad,&firstnpores);

                    if (firstnpores == 0) {
                        printf("\nWARNING: Settled the particles but there are ");
                        printf("\n         still no pores large enough to fit ");
                        printf("\n         the next particle");
                    }
                }
            }

        } while((!fits)  && ((firstnpores > 0) || (can_settle)));

        if (firstnpores == 0 && (!can_settle)) {

            /* Need to push the unplaced volume of this bin to the next
             * bin down */

            if (Verbose && (numsphereplaced < numtoplace)) {
                printf("\nWARNING: Only able to place %d ",numsphereplaced);
                printf("of %d in",numsphereplaced);
                printf("\n         this size class even with settling");
                fflush(stdout);
            }
            return(numsphereplaced);
        }

        /* Place the sphere at x,y,z */

        Npart++;
        if (Npart > Npartc) {
            printf("\nToo many spheres being generated \n");
            printf("\tUser needs to increase value of NPARTC\n");
            printf("\tat top of C-code\n\n");
            if (Pore_delete()) {
                printf("\nError: Had trouble deleting Pore list");
                fflush(stdout);
            }
            return(numsphereplaced);
        }

        if (Verbose) {
             printf("\nPlacing sphere");
             fflush(stdout);
             if (Debug) {
                 printf(" at (%d,%d,%d)",x,y,z);
             }
             fflush(stdout);
        }

        numvox = placesphere(x,y,z,(*nxp),(*nyp),(*nzp),nvoxthis,phaseid);

        ntotal += (int)numvox;
        N_total += (int)numvox;

        numsphereplaced++;

        if (Verbose) {
             printf("\nPlaced!");
             if (Debug) {
                 printf(" This particle has = %d voxels, wanted %d",numvox,nvoxthis);
                 printf("\n\tRunning voxel total for this class = %d ",ntotal);
                 printf("[numpartplaced (%d)]",numsphereplaced);
             }
             fflush(stdout);
        }

        numpores = Pore_length();

        /***************  PUT NICK'S STUFF RIGHT HERE ***********************/
        /*
             Centroid:  X-coord = x + ((0.5*nnxp)+0.01);
             Centroid:  Y-coord = y + ((0.5*nnyp)+0.01);
             Centroid:  Z-coord = z + ((0.5*nnzp)+0.01);
             Need to output the AA[n][m] matrix one row at a time
        */

        fprintf(fpout,"%d %d %d 0\n",x,y,z);
        fprintf(fpout,"0 0 %.10f 0.0000000000\n",(float)(frad));

    }

    printf("\nActual volume _placed  in this bin was %d",ntotal);
    fflush(stdout);

    if (Pore_delete()) {
        printf("\nError: Had trouble deleting Pore list");
        fflush(stdout);
    }

    return(numsphereplaced);
}

/***
*    findsphereloc
*
*    Routine to randomly select a pore and see if a sphere fits there
*
*     Arguments:
*        int *x, *y, *z, the Cartesian coordinates of the pore
*        int *nxp, *nyp, *nzp, the sphere bounding box dimenions
*        int *firstnpores, how far down the sorted Pore list to search
*        int *numpores, the length of the pore list
*        float frad the radius of the sphere particle to place
*
*    Returns:    
*        1 if a good location is found, zero otherwise
*
*    Calls:        makesph, ran1
*    Called by:    create
***/
int findsphereloc(int *x, int *y, int *z,
                  int *nxp, int *nyp, int *nzp,
                  int *numpores, int *firstnpores, float frad)
{
    int fits,ranpos;
    struct Pore *curpore = NULL;

    ranpos = (int)((float)(*firstnpores) * ran1(Seed));
    if (Debug) {
        printf("\nfindsphereloc: Looking for voxel number %d of ",ranpos);
        printf("%d (numpores = %d)",(*firstnpores),(*numpores));
        fflush(stdout);
    }

    curpore = Pore_find_pos(ranpos);

    if (curpore == NULL) {
        printf("\nfindsphereloc: Cannot find voxel ");
        printf("position %d of %d",ranpos,(*numpores));
        fflush(stdout);
        return(MEMERR);
    } else {
        if (Debug) {
            printf("\nfindsphereloc: Found the voxel at %d with ",ranpos);
            printf("radius %d, frad = %.2f",curpore->radius,frad);
            fflush(stdout);
        }
    }

    (*x) = getXfromNs(curpore->ns);
    if (Debug) {
        printf("%d,",(*x));
        fflush(stdout);
    }
    (*y) = getYfromNs(curpore->ns);
    if (Debug) {
        printf("%d,",(*y));
        fflush(stdout);
    }
    (*z) = getZfromNs(curpore->ns);
    if (Debug) {
        printf("%d,",(*z));
        fflush(stdout);
    }

    /***
    *    See if the sphere will fit at x,y,z
    *    Include dispersion distance when checking
    *    to ensure requested separation between spheres
    ***/

    fits = checksphere(*x,*y,*z,nxp,nyp,nzp);

    if (!fits) {
        if (Debug) {
            printf("\nParticle would NOT fit at %d",voxpos((*x),(*y),(*z)));
            fflush(stdout);
        }
        /* Remove this pore from the list of available ones */
        if (Debug) {
            printf("\nGoing into Pore_delete_val 00 with %d pores",(*numpores));
            fflush(stdout);
        }
    
        if (Pore_delete_val(1,voxpos((*x),(*y),(*z)))) {
            printf("\nError: Had trouble deleting current pore");
            fflush(stdout);
            return(MEMERR);
        }

        (*numpores)--;
        (*firstnpores)--;
        if (Debug) {
            printf("\nNow there are %d pores in the list",(*numpores));
            fflush(stdout);
        }
    }

    return(fits);
}
/***
*    findshapeloc
*
*    Routine to randomly select a pore and see if a particle can be
*    made to fit there
*
*     Arguments:
*        int *x, *y, *z, the Cartesian coordinates of the pore
*        int *nxp, *nyp, *nzp, the sphere bounding box dimenions
*        int *firstnpores, how far down the sorted Pore list to search
*        int *numpores, the length of the pore list
*        float frad the radius of the sphere particle to place
*
*    Returns:    
*        1 if a good location is found, zero otherwise
*
*    Calls:        makesph, ran1
*    Called by:    create
***/
int findshapeloc(int *x, int *y, int *z, int *nxp, int *nyp, int *nzp,
                  int *numpores, int *firstnpores, int nvoxthis,
                  int numshapes, struct lineitem shapedata[MAXLINES],
                  float frad)
{
    int fits,newshape,ranpos,numtries,partc;
    struct Pore *curpore = NULL;

    ranpos = (int)((float)(*firstnpores) * ran1(Seed));
    if (Debug) {
        printf("\nfindsphereloc: Looking for voxel number %d of ",ranpos);
        printf("%d (numpores = %d)",(*firstnpores),(*numpores));
        fflush(stdout);
    }

    curpore = Pore_find_pos(ranpos);

    if (curpore == NULL) {
        printf("\nfindshapeloc: Cannot find voxel ");
        printf("position %d of %d",ranpos,(*numpores));
        fflush(stdout);
        return(MEMERR);
    } else {
        if (Debug) {
            printf("\nfindshapeloc: Found the voxel at %d with ",ranpos);
            printf("radius %d, frad = %.2f",curpore->radius,frad);
            fflush(stdout);
        }
    }

    (*x) = getXfromNs(curpore->ns);
    if (Debug) {
        printf("%d,",(*x));
        fflush(stdout);
    }
    (*y) = getYfromNs(curpore->ns);
    if (Debug) {
        printf("%d,",(*y));
        fflush(stdout);
    }
    (*z) = getZfromNs(curpore->ns);
    if (Debug) {
        printf("%d,",(*z));
        fflush(stdout);
    }

    /***
    *    See if the particle will fit at x,y,z
    ***/

    /* Try each pore several times if necessary */

    numtries = 0;

    do {

        if (Debug) {
            printf("\n---> Going into checkrealshape, nxp,nyp,nzp = ");
            printf("(%d,%d,%d)",(*nxp),(*nyp),(*nzp));
            fflush(stdout);
        }

        fits = checkrealshape(*x,*y,*z,*nxp,*nyp,*nzp);

        if (Debug) {
            printf("\n------> Out of checkrealshape, nxp,nyp,nzp = ");
            printf("(%d,%d,%d)",(*nxp),(*nyp),(*nzp));
            fflush(stdout);
        }

        numtries++;

        if (!fits) {
            if (numtries%3 == 0) {
                newshape = 1;
            } else {
                newshape = 0;
            }

            if (Debug) {
                printf("\n--------> Into digitizerealshape with newshape = %d",newshape);
                fflush(stdout);
            }

            /* First instance of digitizerealshape, in function findshapeloc */

            partc = digitizerealshape(newshape,nxp,nyp,nzp,nvoxthis,
                                  numshapes,shapedata);

            if (Debug) {
                printf("\nOut of digitizerealshape with partc = ");
                fflush(stdout);
                printf("%d",partc);
                fflush(stdout);
            }

            if (partc != nvoxthis) {
                printf("\nWARNING 01: Digitization created particle with %d voxels ",partc);
                printf("\n            instead of intended %d",nvoxthis);
                fflush(stdout);
                if (partc == MEMERR) {
                    return(MEMERR);
                }
            }

            if (Debug) {
                printf("\n------------> numtries = %d, nxp,nyp,nzp = ",numtries);
                printf("(%d,%d,%d)",(*nxp),(*nyp),(*nzp));
                fflush(stdout);
            }
        }

    } while (!fits && numtries < 9);

    if (!fits) {

        if (Verbose) {
            printf("\nTried this pore %d times and still did not fit.",numtries);
            printf("Moving on to another pore.");
            fflush(stdout);
        }

        if (Debug) {
            printf("\nParticle would NOT fit at %d",voxpos((*x),(*y),(*z)));
            fflush(stdout);
        }
        /* Remove this pore from the list of available ones */
        if (Debug) {
            printf("\nGoing into Pore_delete_val 00 with %d pores",(*numpores));
            fflush(stdout);
        }
    
        if (Pore_delete_val(1,voxpos((*x),(*y),(*z)))) {
            printf("\nError: Had trouble deleting current pore");
            fflush(stdout);
            return(MEMERR);
        }

        (*numpores)--;
        (*firstnpores)--;
        if (Debug) {
            printf("\nNow there are %d pores in the list",(*numpores));
            fflush(stdout);
        }
    }

    return(fits);
}

/***
*    digitizesphere
*
*    Routine to digitize a copy of a sphere in Bbox
*
*     Arguments:
*        nxp,nyp,nzp is the bounding box for the sphere
*        targetvox is the number of solid voxels in the sphere
*        radius is the radius of the digitized sphere to create
*
*    Returns:    
*       number of voxels in the sphere
*
*    Calls:        makesph, ran1
*    Called by:    create
***/
int digitizesphere(int *nxp, int *nyp, int *nzp, int targetvox, float radius)
{
    int partc;

    /* Make a digital copy of the sphere */
            
    *nxp = *nyp = *nzp = 3 + ((int)(2.0 * radius) + 0.5);
    if (Verbose) {
        printf("\nnxp = %d nyp = %d nzp = %d",*nxp,*nyp,*nzp);
        fflush(stdout);
    }

    if ( ((*nxp) < (int)(0.8 * Xsyssize))
            && ((*nyp) < (int)(0.8 * Ysyssize))
            && ((*nzp) < (int)(0.8 * Zsyssize)) ) {

            /* This function populates Bbox */

            partc = sphereimage(nxp,nyp,nzp,radius);

            if (Verbose) {
                printf("\nAfter sphereimage function, nominal particle ");
                printf("volume %d, actual %d voxels", targetvox,partc);
                fflush(stdout);
            }
     } else {
         printf("\nCurrent sphere is too big for the system.");
         partc = -1;
     }

    return(partc);
}

/***
*    digitizerealshape
*
*    Routine to digitize a copy of a real shape with a target number
*    of voxels in a box
*
*     Arguments:
*        newshape is 1 if we need to read a new shape from the database
*        nxp,nyp,nzp is the bounding box for the sphere
*        targetvox is the number of solid voxels in the sphere
*        radius is the radius of the digitized sphere to create
*
*    Returns:    
*       number of voxels in the sphere
*
*    Calls:        makesph, ran1
*    Called by:    create
***/
int digitizerealshape(int newshape, int *nxp, int *nyp, int *nzp, int targetvox,
                      int numshapes, struct lineitem shapedata[MAXLINES])
{
    int m,n,i,j,k,ii,jj,na,foundpart;
    int n1,nnxp,nnyp,nnzp,opartc,partc,pcount[10];
    int extvox,orient,toobig;
    int klow,khigh,mp,begin,end;
    int oldabsdiff,absdiff,voxfrac;
    float rx,ry,rz,aa1,aa2;
    float maxrx,maxry,maxrz;
    float vol1,volume,volumecalc,v1;
    float length,width;
    double factor,theta,phi,cosbeta,sinbeta,alpha,gamma,beta,total,abc;
    double realnum,saveratio,ratio[10];
    fcomplex r1,ddd,icmplx;
    char filename[MAXSTRING];
    FILE *anmfile;


    if (newshape) {

        begin = 2;
        end = numshapes;

        toobig = foundpart = 0;
        voxfrac = (int)(0.03 * targetvox);

        do {
            if (targetvox > 4) {
                if (toobig || !foundpart) {

                    if (Verbose) {
                        printf("\nGetting new shape file...");
                        fflush(stdout);
                    }

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
    
                    n1 = begin + (int)(numshapes * ran1(Seed));

                    sprintf(filename,"%s%s%c%s",Pathroot,Shapeset,Filesep,shapedata[n1].name);
                    anmfile = filehandler("genaggpack",filename,"READ");
                    if (!anmfile) { 
                        freeallmem();
                        return(MEMERR);
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
                            fscanf(anmfile,"%d %d %f %f",&ii,&jj,&aa1,&aa2);
                            A[n][m] = Complex(aa1,aa2);
                        }
                    }
                    if (Verbose) printf("\nRead anms");
                    fclose(anmfile);

                    width = shapedata[n1].width /Resolution;    /* in voxels */
                    length = shapedata[n1].length / Resolution;    /* in voxels */

                    if (Verbose) {
                        printf("\nOpened %s ; width = %f ",shapedata[n1].name,width);
                        printf("length = %f voxels\n",length);
                        printf("vol = %d voxels",targetvox);
                        fflush(stdout);
                    }

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
                            harm(theta,phi);
                            r1 = Complex(0.0,0.0);
                            r1 = Cmul(A[0][0],Y[0][0]);
                            for (n = 1; n <= Nnn; n++) {
                                for (m = n; m >= -n; m--) {
                                    r1 = Cadd(r1,Cmul(A[n][m],Y[n][m]));
                                }
                            }
                            rx = (r1.r * sin(theta) * cos(phi));
                            ry = (r1.r * sin(theta) * sin(phi));
                            rz = (r1.r * cos(theta));

                            if (fabs(rx) > maxrx) maxrx = fabs(rx);
                            if (fabs(ry) > maxry) maxry = fabs(ry);
                            if (fabs(rz) > maxrz) maxrz = fabs(rz);

                            v1 = sin(theta)/3.0;
                            v1 *= (r1.r * r1.r * r1.r);
                            v1 *= (Wg[i] * Wg[j]);
                            volumecalc += v1;
                        }
                    }
                    volumecalc *= factor;

                    /* This is an estimate of the amount the characteristic dimension
                     * differs from * the radius we want
                     */

                    saveratio = pow((1.003 * (double)targetvox / volumecalc),(1./3.));

                    /***
                    *    Will multiply all SH coefficients by the following
                    *    ratio to dilate the size to the correct amount
                    ***/
    
                    if (Verbose) {
                        printf("\nCalculated volume from SH coefficients before ");
                        printf("scaling = %f voxels",volumecalc);
                        printf("\nCalculated length scaling ratio = %f",saveratio);
                        fflush(stdout);
                    }

                }

                /***
                *    Rotate coefficients A[n][m] by a random amount
                *    Store in AA[n][m] matrix, then reassign into A
                *    We remember the ratio from the last particle
                *    provided we haven't used a new shape file
                ***/

                beta = Pi * ran1(Seed);

                cosbeta=cos(beta/2.0);
                sinbeta=sin(beta/2.0);

                /* Must not have cosbeta or sinbeta exactly zero */

                if (cosbeta == 0.0) {
                    beta += 1.0e-10;
                    cosbeta = cos(beta/2.0);
                }
                if (sinbeta == 0.0) {
                    beta += 1.0e-10;
                    sinbeta = sin(beta/2.0);
                }

                alpha = 2.0 * Pi * ran1(Seed);
                gamma = 2.0 * Pi * ran1(Seed);

                /* Modiy the spherical harmonic coefficients to
                 * achieve the size we need. AA are the modified SH coefficients,
                 * whereas A (above) are the originals */

                for (n = 0; n <= Nnn; n++) {
                    for (m = -n; m <= n; m++) {
                        AA[n][m] = Complex(0.0,0.0);
                        for (mp = -n; mp <= n; mp++) {
                            realnum = sqrt(fac(n+mp)*fac(n-mp)/fac(n+m)/fac(n-m));
                            ddd = Complex(realnum,0.0);
                            klow = max(0,m-mp);
                            khigh = min(n-mp,n+m);
                            total = 0.0;
                            for (k = klow; k <= khigh; k++) {
                                abc = pow(-1.0,k+mp-m);
                                abc *= (fac(n+m)/fac(k)/fac(n+m-k));
                                abc *= (fac(n-m)/fac(n-mp-k)/fac(mp+k-m));
                                total += abc * (pow(cosbeta,2*n+m-mp-2*k)) * (pow(sinbeta,2*k+mp-m));
                            }
                            icmplx = Complex(total*cos(mp*alpha),total*(-sin(mp*alpha)));
                            ddd = Cmul(ddd,icmplx);
                            icmplx = Complex(cos(m*gamma),(-sin(m*gamma)));
                            ddd = Cmul(ddd,icmplx);
                            icmplx = Cmul(A[n][mp],ddd);
                            AA[n][m] = Cadd(AA[n][m],icmplx);
                        }
    
                        /***
                        *    All SH coefficients multiplied by ratio to
                        *    dilate the thickness to be in range of the
                        *    bounding sieve openings
                        ***/

                        AA[n][m] = RCmul(saveratio,AA[n][m]);
                    }
                }
    

                /***
                *    Compute volume of particle using the AA coefficients (modified)
                ***/

                volume = 0.0;
    
                maxrx = maxry = maxrz = 0.0;
                for (i = 1; i <= Ntheta; i++) {
                    theta = 0.5 * Pi * (Xg[i] + 1.0);
                    for (j = 1; j <= Nphi; j++) {
                        phi = Pi * (Xg[j] + 1.0);
                        harm(theta,phi);
                        r1 = Complex(0.0,0.0);
                        r1 = Cmul(AA[0][0],Y[0][0]);
                        for (n = 1; n <= Nnn; n++) {
                            for (m = n; m >= -n; m--) {
                                r1 = Cadd(r1,Cmul(AA[n][m],Y[n][m]));
                            }
                        }
                        rx = (r1.r * sin(theta) * cos(phi));
                        ry = (r1.r * sin(theta) * sin(phi));
                        rz = (r1.r * cos(theta));

                        if (fabs(rx) > maxrx) maxrx = fabs(rx);
                        if (fabs(ry) > maxry) maxry = fabs(ry);
                        if (fabs(rz) > maxrz) maxrz = fabs(rz);

                        v1 = sin(theta)/3.0;
                        v1 *= (r1.r * r1.r * r1.r);
                        v1 *= (Wg[i] * Wg[j]);
                        volume += v1;
                    }
                }

                volume *= factor;
                vol1 = volume;
                if (Verbose) {
                    printf("\nComputed volume after scaling = %f voxels",volume);
                    printf("\nMaxrx = %f Maxry = %f Maxrz = %f",maxrx,maxry,maxrz);
                    fflush(stdout);
                }

                na = 0;
                partc = 0;
                oldabsdiff = targetvox;
                absdiff = 0;
                pcount[0] = (int)vol1;
                do {
                    if (na == 0) {
                        /* Initial try */
                        ratio[na] = saveratio;
                        pcount[na] = (int)vol1;
                        if (Verbose) {
                            printf("\nratio[%d] = %f, ",na,ratio[na]);
                            printf("pcount[%d] = %d",na,pcount[na]);
                            fflush(stdout);
                        }
                    } else if (na == 1) {
                        /* Tried once, make a modification based on error in that try */
                        pcount[na] = partc;
                        ratio[na] = ratio[na-1]
                                * pow(0.5 * ((float)pcount[na])/((float)pcount[na-1]),(1./3.));
                     
                        /* Adjust the AA coefficients now */
                        for (n = 0; n <= Nnn; n++) {
                            for (m = n; m >= -n; m--) {
                                AA[n][m] = RCmul(ratio[na]/ratio[na-1],AA[n][m]);
                            }
                        }
    
                        maxrx *= (ratio[na]/ratio[na-1]);
                        maxry *= (ratio[na]/ratio[na-1]);
                        maxrz *= (ratio[na]/ratio[na-1]);
                        if (Verbose) {
                            printf("\nratio[%d] = %f, pcount[%d] = %d",na,ratio[na],na,pcount[na]);
                            fflush(stdout);
                        }
                    } else {
                        /* Multiple tries made, still trying to fine tune the adjustments */
                        oldabsdiff = labs(pcount[na-2] - targetvox);
                        absdiff = labs(pcount[na-1] - targetvox);
                        if (Verbose) {
                            printf("\noldabsdiff = %d, absdiff = %d",oldabsdiff,absdiff);
                            fflush(stdout);
                        }
                        if (absdiff <= oldabsdiff) {
                            pcount[na] = partc;
                            ratio[na] = ratio[na-1]
                                * pow(0.5 * ((float)pcount[na])/((float)pcount[na-1]),(1./3.));
                            
                            /* Adjust the AA coefficients again */
                            for (n = 0; n <= Nnn; n++) {
                                for (m = n; m >= -n; m--) {
                                    AA[n][m] = RCmul(ratio[na]/ratio[na-1],AA[n][m]);
                                }
                            }
    
                            maxrx *= (ratio[na]/ratio[na-1]);
                            maxry *= (ratio[na]/ratio[na-1]);
                            maxrz *= (ratio[na]/ratio[na-1]);
                            if (Verbose) {
                                printf("\nratio[%d] = %f, ",na,ratio[na]);
                                printf("pcount[%d] = %d",na,pcount[na]);
                                fflush(stdout);
                            }
                        } else {
                            ratio[na] = ratio[na - 2];
                            pcount[na] = partc;
                            for (n = 0; n <= Nnn; n++) {
                                for (m = n; m >= -n; m--) {
                                    AA[n][m] = RCmul(ratio[na]/ratio[na-1],AA[n][m]);
                                }
                            }
                            maxrx *= (ratio[na]/ratio[na-1]);
                            maxry *= (ratio[na]/ratio[na-1]);
                            maxrz *= (ratio[na]/ratio[na-1]);
                            if (Verbose) {
                                printf("\nratio[%d] = %f, ",na,ratio[na]);
                                printf("pcount[%d] = %d",na,pcount[na]);
                                fflush(stdout);
                            }
                        }
                    }
    
                    if (Verbose) {
                        printf("\nna = %d",na);
                        printf("\ntarget volume = %d",targetvox);
                        printf("\ncomputed volume = %f",vol1);
                        printf("\nNew scaling ratio = %f",ratio[na]);
                        fflush(stdout);
                    }
    
                    /* Digitize the particles all over again */

                    /*  Estimate dimensions of bounding box */
    
                    (*nxp) = 3 + ((int)(2.0 * maxrx));
                    (*nyp) = 3 + ((int)(2.0 * maxry));
                    (*nzp) = 3 + ((int)(2.0 * maxrz));
    
                    if (Verbose) {
                        printf("\nnxp = %d nyp = %d nzp = %d",(*nxp),(*nyp),(*nzp));
                    }
    
                    if (((*nxp) < (int)(0.8 * Xsyssize))
                        && ((*nyp) < (int)(0.8 * Ysyssize))
                        && ((*nzp) < (int)(0.8 * Zsyssize))) {
                        foundpart = 1;
    
                        /* Here is where the digization happens */
    
                        partc = image(nxp,nyp,nzp);
                        if (partc == 0) {
                            if (Verbose) printf("\nCurrent particle too big for system.");
                            toobig = 1;
                            foundpart = 0;
                        } else {
                            if (Verbose) {
                                printf("\nAfter image function, nominal particle volume ");
                                printf("%d, actual %d voxels",(int)targetvox,(int)partc);
                                fflush(stdout);
                            }
                            toobig = 0;
                            foundpart = 1;
                        }
                    } else {
                        if (Verbose) printf("\nCurrent particle too big for system.");
                        toobig = 1;
                        foundpart = 0;
                    }
                    saveratio = ratio[na];
                    na++;
    
                } while(abs(partc - targetvox) > max(4,voxfrac) && na < 1 && !toobig);
    
                if (Verbose) {
                    printf("\nConverged? partc = %d and vol = ",partc);
                    printf("%d, na = %d",targetvox,na);
                    fflush(stdout);
                }
                            
                if (!toobig && foundpart) {
                    if (Verbose) {
                        printf("\nDone scaling the anms");
                        fflush(stdout);
                    }

                    if (partc != targetvox) {
                        if (Verbose) {
                            printf("\nAdditional adjustment needed to match ");
                            printf("volume, partc = %d",partc);
                            fflush(stdout);
                        }
                        extvox = adjustvol(targetvox - partc,(*nxp),(*nyp),(*nzp));
                        partc += extvox;
                        if (Verbose) {
                            printf("\nAfter adjustment, partc = %d",partc);
                            fflush(stdout);
                        }
                    }

                    /***
                    *    Done generating the shape image for the particle
                    ***/
    
                    nnxp = (*nxp);
                    nnyp = (*nyp);
                    nnzp = (*nzp);

                } else {
                    toobig = 1;
                    foundpart = 0;
                }

            } else {

                /* This is a small particle */
                /* No SH reconstruction */
    
                if (targetvox > 1) {
                    partc = smallimage(nxp,nyp,nzp,targetvox);
                    orient = 1 + (int)(14.0 * ran1(Seed));
                } else {
                    partc = orient = 1;
                }
                nnxp = (*nxp);
                nnyp = (*nyp);
                nnzp = (*nzp);
                foundpart = 1;
            }

        } while (!foundpart);

    } else {
        
        /* Already have a digitized shape, just need to rotate it */

        opartc = countBbox(*nxp,*nyp,*nzp);
        if (Verbose) {
            printf("\nGoing into rotatebox with %d voxels, (nxp,nyp,nzp) = ",opartc);
            printf("(%d,%d,%d)",*nxp,*nyp,*nzp);
            fflush(stdout);
        }
        partc = rotatebox(nxp,nyp,nzp);
        if (partc != opartc) {
            printf("\nPROBLEM: original voxels = %d and rotated voxels = %d",opartc,partc);
            fflush(stdout);
        }

        if (Verbose) {
            printf("\nRotated particle ONCE with %d voxels, (nxp,nyp,nzp) = ",partc);
            printf("(%d,%d,%d)... ",*nxp,*nyp,*nzp);
            fflush(stdout);
        }

    }

    if (Verbose) {
        printf("Returning from digitizerealshape now.");
        fflush(stdout);
    }

    return(partc);
}

/***
*    rotatebox
*
*    Routine to digitize a copy of a real shape with a target number
*    of voxels in a box
*
*     Arguments:
*        nxp,nyp,nzp is the bounding box for the sphere
*        targetvox is the number of solid voxels in the sphere
*        radius is the radius of the digitized sphere to create
*
*    Returns:    
*       number of voxels in the sphere
*
*    Calls:        ran1
*    Called by:    digitizerealshape
***/
int rotatebox(int *nxp, int *nyp, int *nzp)
{
    register int i,j,k;
    int maxx,maxy,maxz,minx,miny,minz;
    float alphad,betad,gammad;
    int xc,yc,zc;
    int aftercount,newi,newj,newk;
    int maxboxsize;
    int rotmat[3][3];

    double alpha,beta,gam,sa,ca,sb,cb,sg,cg;

    double halfpi = 2.0 * atan(1.0);

    Int3d nbox;

    maxboxsize = (*nxp) + 5;
    if (maxboxsize < (*nyp)) maxboxsize = (*nyp) + 5;
    if (maxboxsize < (*nzp)) maxboxsize = (*nzp) + 5;

    if (maxboxsize > Xsyssize) {
        printf("\nWARNING: maxboxsize of %d compared to ",maxboxsize);
        printf("(%d,%d,%d)",Xsyssize,Ysyssize,Zsyssize);
        fflush(stdout);
        return(MEMERR);
    }

    if (Int3darray(&nbox,Boxsize,Boxsize,Boxsize)) {
        bailout("genaggpack","Memory allocation error for nbox");
        return(MEMERR);
    } else {
        for (k = 0; k <= Boxsize; ++k) {
           for (j = 0; j <= Boxsize; ++j) {
              for (i = 0; i <= Boxsize; ++i) {
                  nbox.val[getInt3dindex(nbox,i,j,k)] = POROSITY;
              }
           }
        }
    }

    /* Choose three random rotation angles about x, y, z axes */

    alpha = halfpi * (double)((int)(4.0 * ran1(Seed))); /* about z axis */
    beta = halfpi * (double)((int)(4.0 * ran1(Seed)));  /* about y axis */
    gam = halfpi * (double)((int)(4.0 * ran1(Seed)));   /* about x axis */

    alphad = alpha * 180.0 / (2.0 * halfpi);
    betad = beta * 180.0 / (2.0 * halfpi);
    gammad = gam * 180.0 / (2.0 * halfpi);

    /*
    printf("\nIn rotatebox: %.1f, %.1f, %.1f",alphad,betad,gammad);
    fflush(stdout);
    */

    sa = sin(alpha);
    ca = cos(alpha);
    sb = sin(beta);
    cb = cos(beta);
    sg = sin(gam);
    cg = cos(gam);

    /* Construct the 3D rotation matrix */

    rotmat[0][0] = (int)(ca*cb);
    rotmat[0][1] = (int)(ca*sb*sg - (sa*cg));
    rotmat[0][2] = (int)(ca*sb*cg + (sa*sg));
    rotmat[1][0] = (int)(sa*cb);
    rotmat[1][1] = (int)(sa*sb*sg + (ca*cg));
    rotmat[1][2] = (int)(sa*sb*cg - (ca*sg));
    rotmat[2][0] = (int)(-sb);
    rotmat[2][1] = (int)(cb*sg);
    rotmat[2][2] = (int)(cb*cg);
    
    /* Translate all voxel coordinates by uniform positive amount to make sure
     * they won't become negative during rotation */

    for (k = 0; k <= maxboxsize; ++k) {
       for (j = 0; j <= maxboxsize; ++j) {
          for (i = 0; i <= maxboxsize; ++i) {
              nbox.val[getInt3dindex(nbox,i,j,k)]
              = Bbox.val[getInt3dindex(Bbox,i,j,k)];
          }
       }
    }

    minx = miny = minz = 3 * maxboxsize;
    maxx = maxy = maxz = 0;

    for (k = 0; k <= maxboxsize; ++k) {
       for (j = 0; j <= maxboxsize; ++j) {
          for (i = 0; i <= maxboxsize; ++i) {
              if (nbox.val[getInt3dindex(nbox,i,j,k)] != POROSITY) {
                  if (i < minx) minx = i;
                  if (i > maxx) maxx = i;
                  if (j < miny) miny = j;
                  if (j > maxy) maxy = j;
                  if (k < minz) minz = k;
                  if (k > maxz) maxz = k;
              }
          }
       }
    }

    /* Find center of translated particle */

    xc = 0.5 * (maxx + minx); /* + 0.5; */
    yc = 0.5 * (maxy + miny); /* + 0.5; */
    zc = 0.5 * (maxz + minz); /* + 0.5; */

    /* Rotate the particle */

    for (k = 0; k <= maxboxsize; ++k) {
       for (j = 0; j <= maxboxsize; ++j) {
          for (i = 0; i <= maxboxsize; ++i) {
              Bbox.val[getInt3dindex(Bbox,i,j,k)] = POROSITY;
          }
       }
    }

    /* Determine the minimum untranslated coordinates after rotation */

    minx = miny = minz = maxboxsize;

    for (k = 0; k <= maxboxsize; ++k) {
       for (j = 0; j <= maxboxsize; ++j) {
          for (i = 0; i <= maxboxsize; ++i) {
              newi = rotmat[0][0] * (i-xc) + rotmat[0][1] * (j-yc) + rotmat[0][2] * (k-zc);
              newj = rotmat[1][0] * (i-xc) + rotmat[1][1] * (j-yc) + rotmat[1][2] * (k-zc);
              newk = rotmat[2][0] * (i-xc) + rotmat[2][1] * (j-yc) + rotmat[2][2] * (k-zc);
              if (newi < minx) minx = newi;
              if (newj < miny) miny = newj;
              if (newk < minz) minz = newk;
          }
       }
    }

    for (k = 0; k <= maxboxsize; ++k) {
       for (j = 0; j <= maxboxsize; ++j) {
          for (i = 0; i <= maxboxsize; ++i) {
              newi = rotmat[0][0] * (i-xc) + rotmat[0][1] * (j-yc) + rotmat[0][2] * (k-zc);
              newj = rotmat[1][0] * (i-xc) + rotmat[1][1] * (j-yc) + rotmat[1][2] * (k-zc);
              newk = rotmat[2][0] * (i-xc) + rotmat[2][1] * (j-yc) + rotmat[2][2] * (k-zc);

              Bbox.val[getInt3dindex(Bbox,newi-minx,newj-miny,newk-minz)]
                  = nbox.val[getInt3dindex(nbox,i,j,k)];
          }
       }
    }

    /* Find min and max x,y,z coords of new particle */

    minx = miny = minz = 3 * maxboxsize;
    maxx = maxy = maxz = 0;

    for (k = 0; k <= maxboxsize; ++k) {
       for (j = 0; j <= maxboxsize; ++j) {
          for (i = 0; i <= maxboxsize; ++i) {
              if (Bbox.val[getInt3dindex(Bbox,i,j,k)] != POROSITY) {
                  if (i < minx) minx = i;
                  if (i > maxx) maxx = i;
                  if (j < miny) miny = j;
                  if (j > maxy) maxy = j;
                  if (k < minz) minz = k;
                  if (k > maxz) maxz = k;
              }
          }
       }
    }

    (*nxp) = maxx - minx;
    (*nyp) = maxy - miny;
    (*nzp) = maxz - minz;

    aftercount = 0;

    for (k = 0; k <= maxboxsize; ++k) {
       for (j = 0; j <= maxboxsize; ++j) {
          for (i = 0; i <= maxboxsize; ++i) {
              Bbox.val[getInt3dindex(Bbox,i,j,k)]
              = Bbox.val[getInt3dindex(Bbox,i+minx,j+miny,k+minz)];
              if (Bbox.val[getInt3dindex(Bbox,i,j,k)] != POROSITY) aftercount++;
          }
       }
    }

    if (nbox.val) free_Int3darray(&nbox);

    return(aftercount);
}

/***
*    countBbox
*
*    Routine to count the voxels in a digital copy of a particle
*
*     Arguments:
*        nxp,nyp,nzp is the bounding box for the sphere
*
*    Returns:    
*       number of voxels in the sphere
*
*    Calls:        Nothing
*    Called by:    digitizerealshape
***/
int countBbox(int nxp, int nyp, int nzp)
{
    register int i,j,k;
    int maxboxsize;
    int partc = 0;

    maxboxsize = nxp + 5;
    if (maxboxsize < nyp) maxboxsize = nyp + 5;
    if (maxboxsize < nzp) maxboxsize = nzp + 5;

    partc = 0;
    for (k = 0; k <= maxboxsize; ++k) {
       for (j = 0; j <= maxboxsize; ++j) {
          for (i = 0; i <= maxboxsize; ++i) {
              if (Bbox.val[getInt3dindex(Bbox,i,j,k)] != POROSITY) partc++;
          }
       }
    }

    return(partc);
}

/***
*
*    packrealshapes
*
*    Routine to place real shapes of various sizes and phases at random
*    locations in 3-D microstructure.
*
*     Arguments:
*        int type is the type of aggregate (FINE or COARSE)
*        int numsources is the number of sources of this type of aggregate
*        int sourceeach is which source of this aggregate class
*        int voleach holds the volume in voxels of each size class
*        int vp is the volume of a single particle in a given bin (in voxels)
*        int numeach holds the number of particles in each size class
*        float sizeeach holds the radius in voxels of each size class
*        FILE *fpout is the output file to write the SPH coefficients
*    Returns:    
*        0 if okay; nonzero if not
num*
*    Calls:        makesph, ran1
*    Called by:    create
***/
int packrealshapes(int type, int numshapes, int numsources, int sourceeach[NUMAGGBINS],
                  int voleach[NUMAGGBINS], int vp[NUMAGGBINS],
                  int numeach[NUMAGGBINS], float sizeeach[NUMAGGBINS],
                  struct lineitem shapedata[MAXLINES],
                  FILE *fpout)
{
    int ig,foundpart,n1,numpershape,numitems,toobig;
    int numlines,begin,end,voxfrac,phaseid,calcporesizes;
    int nextraparticles,numvoxdiff,numtoplace;
    int numpores,numitz,numpartplaced,nvoxthis,diff,ntotal;
    float frad;

    calcporesizes = 0;

    /* Initialize local arrays */

    numitz = numpores = numpartplaced = 0;

    /***
    *    Generate spheres of each size class
    *    in turn (largest first)
    ***/

    if (Verbose) {
        if (type == (int)COARSE) {
            printf("\nPlacing real coarse aggregate particles now...");
        } else {
            printf("\nPlacing real fine aggregate particles now...");
        }
        fflush(stdout);
    }

    n1 = 1;

    numitems = numshapes; /* Will skip the header */
    numlines = numitems - 2;

    diff = numvoxdiff = 0;

    for (ig = 0; ig < Numaggbins; ig++) {

        /* Choose the correct voxel id for this aggregate */
        printf("\n\tSize bin = %d of %d, source = %d",ig,Numaggbins,sourceeach[ig]);
        fflush(stdout);

        switch (sourceeach[ig]) {
            case 0:
                phaseid = FINEAGG01INCONCRETE;
                if (type == (int)COARSE) phaseid = COARSEAGG01INCONCRETE;
                break;
            case 1:
                phaseid = FINEAGG02INCONCRETE;
                if (type == (int)COARSE) phaseid = COARSEAGG02INCONCRETE;
                break;
            default:
                phaseid = FINEAGG01INCONCRETE;
                if (type == (int)COARSE) phaseid = COARSEAGG01INCONCRETE;
                break;
        }

        foundpart = 1;
        toobig = 0;
        ntotal = 0;

        calcporesizes = 0;
        if (ig > MaxBinWithoutSorting) calcporesizes = 1;

        numtoplace = numeach[ig];
        nvoxthis = vp[ig]; /* volume of this particle in voxels */
        frad = (sizeeach[ig]);  /* diam in voxel edge lengths */
        MaxPoreSizeToCheck = (int)(4.0 * frad);
        voxfrac = (int)(0.03 * nvoxthis);

        if (Verbose) {
            printf("\nEffective diameter = %.2f voxels",frad);
            printf("\nTotal volume needed = %d voxels",(int)voleach[ig]);
            fflush(stdout);
        }

        begin = 2;
        end = numlines;

        numpershape = max((numeach[ig] / Shapesperbin),1);

        nextraparticles = (int)((((float)(numvoxdiff)) / ((float)(nvoxthis))) + 0.5); 
        numtoplace += nextraparticles;

        printf("\nPlacing real shape class %d of %d...",ig,Numaggbins);
        if (nextraparticles > 0) {
            printf("\nTrying to add an extra %d particles to this class",nextraparticles);
            printf("\n\t(%d total) because prior class did not all fit",numtoplace);
        } else {
            printf("\nTrying to add %d particles in this class",numtoplace);
        }

        numpartplaced = placeshapeclass(numtoplace,nvoxthis,phaseid,numshapes,
                                        numpershape,calcporesizes,shapedata,frad,
                                        fpout);

        if (numpartplaced == MEMERR) {
            return(MEMERR);
        }

        if (Verbose) {
            printf("\nPlaced %d of %d particles in class %d",numpartplaced,numtoplace,ig);
            fflush(stdout);
        }

        /* Move any remaining volume from this class to the next class */
        numvoxdiff = nvoxthis * (numtoplace - numpartplaced);

    }

    return(0);
}

/***
*    placeshapeclass
*
*    Routine to place spheres of various sizes and phases at random
*    locations in 3-D microstructure.
*
*     Arguments:
*               int numtoplace total spheres to place
*               int nvoxthis number of voxels in one sphere of this class
*               int phaseid is the phase id of the voxels in this sphere
*               int calcporesizes whether or not calculate the pore sizes
*               float frad the radius of these spheres
*               int *nxp, *nyp, *nzp, the dimenions of the bounding box Bbox
*               FILE *fpout for structure characteristics
*    Returns:    
*               number of spheres placed
*
*    Calls:        makesph, ran1
*    Called by:    create
***/
int placeshapeclass(int numtoplace, int nvoxthis, int phaseid, int numshapes,
                     int numpershape,
                     int calcporesizes, struct lineitem shapedata[MAXLINES],
                     float frad, FILE *fpout)

{

    register int jg;
    int fits,firstnpores,numpores,newshape,partc;
    int ntotal,numvox,numpartplaced,can_settle;
    int x,y,z,nxp,nyp,nzp;

    ntotal = numvox = numpartplaced = partc = 0;

    for (jg = 0; jg < numtoplace; jg++) {

        /* Initialize the pore voxel list */
        if (Debug) {
            printf("\nCreating pore voxel list... ");
            fflush(stdout);
        }

        numpores = Pore_create_porelist(calcporesizes,frad,&firstnpores);

        if (numpores < 1) {
            printf("\nError:  Had trouble getting pore voxel list");
            fflush(stdout);
            return(MEMERR);
        }
    
        if (Verbose || Debug) {
            printf("\n\n**Placed %d of %d total particles ",jg,numtoplace);
            fflush(stdout);
        }

        N_target += nvoxthis;

        if (jg == 0 || (!(numpartplaced%numpershape))) {

            /* Produce a new digitized real shape in Bbox */

            newshape = 1;

        } else {

            /* Randomly rotate the existing particle */

            newshape = 0;
        }

        /* Second  instance of digitizerealshape, in function placeshapeclass */

        partc = digitizerealshape(newshape,&nxp,&nyp,&nzp,nvoxthis,
                                  numshapes,shapedata);

        if (Verbose) {
            printf("\nOut of digitizerealshape with partc = ");
            fflush(stdout);
            printf("%d",partc);
            fflush(stdout);
        }

        if (partc != nvoxthis) {
            printf("\nWARNING 01: Digitization created particle with %d voxels ",partc);
            printf("\n            instead of intended %d",nvoxthis);
            fflush(stdout);
            if (partc == MEMERR) {
                return(MEMERR);
            }
        }

        fits = 0;
        can_settle = 1;

        do {

            if (firstnpores > 0) {

                if (Verbose) {
                    printf("\nGoing into findshapeloc...");
                    fflush(stdout);
                }
                fits = findshapeloc(&x,&y,&z,&nxp,&nyp,&nzp,&numpores,&firstnpores,
                        nvoxthis,numshapes,shapedata,frad);
                if (Verbose) {
                    printf("\nfits = %d, firstnpores = %d",fits,firstnpores);
                    fflush(stdout);
                }

            } else {

                if (Verbose) {
                    printf("\nCould not find a spot for particle %d\n",Npart);
                    printf("\n\tTotal pore voxels left is %d\n\n",numpores);
                    printf("\n\tSee if rearranging helps...");
                    fflush(stdout);
                }

                can_settle = settle();

                if (can_settle) {
                    numpores = Pore_create_porelist(calcporesizes,frad,&firstnpores);

                    if ((firstnpores == 0) && Verbose) {
                        printf("\nWARNING: Settled the particles but there are ");
                        printf("\n         still no pores large enought to fit ");
                        printf("\n         the next particle");
                        fflush(stdout);
                    }
                }
            }

        } while((!fits) && ((firstnpores > 0) || (can_settle)));

        if (firstnpores == 0 && (!can_settle)) {

            /* Need to push the unplaced volume of this bin to the next
             * bin down */

            if (Verbose && (numpartplaced < numtoplace)) {
                printf("\nWARNING: Only able to place %d of %d in",numpartplaced,numtoplace);
                printf("\n         this size class even with settline");
                fflush(stdout);
            }

            return(numpartplaced);
        }

        /* Place the particle at x,y,z */

        Npart++;
        if (Npart > Npartc) {
            printf("\nToo many particles being generated \n");
            printf("\tUser needs to increase value of NPARTC\n");
            printf("\tat top of C code\n\n");
            if (Pore_delete()) {
                printf("\nError: Had trouble deleting Pore list");
                fflush(stdout);
            }
            return(numpartplaced);
        }

        if (Debug) {
             printf("\nPlacing particle at (%d,%d,%d)",x,y,z);
            fflush(stdout);
        }

        numvox = placerealshape(x,y,z,nxp,nyp,nzp,partc,phaseid);
        if (numvox != partc) {
            printf("\nWARNING 02: Placing created particle with %d voxels ",numvox);
            printf("\n            instead of intended %d",partc);
            fflush(stdout);
            if (partc == MEMERR) {
                return(MEMERR);
            }
        }

        ntotal += (int)numvox;
        N_total += (int)numvox;

        numpartplaced++;
        printf("\nPlaced particle %d of %d, Npart = %d",numpartplaced,numtoplace,Npart);
        fflush(stdout);

        if (Verbose) {
             printf("\nPlaced! numvox = %d, wanted %d",numvox,nvoxthis);
             printf("\n\tRunning ntotal = %d [numpartplaced (%d) ",ntotal,numpartplaced);
             printf("* nvoxthis (%d)= %d]",nvoxthis,numpartplaced*nvoxthis);
             fflush(stdout);
        }

        numpores = Pore_length();

        /***************  PUT NICK'S STUFF RIGHT HERE ***********************/
        /*
             Centroid:  X-coord = x + ((0.5*nnxp)+0.01);
             Centroid:  Y-coord = y + ((0.5*nnyp)+0.01);
             Centroid:  Z-coord = z + ((0.5*nnzp)+0.01);
             Need to output the AA[n][m] matrix one row at a time
        */

        fprintf(fpout,"%d %d %d 0\n",x,y,z);
        fprintf(fpout,"0 0 %.10f 0.0000000000\n",(float)(frad));

    }

    printf("\nActual volume _placed  in this bin was %d",ntotal);
    fflush(stdout);

    if (Pore_delete()) {
        printf("\nError: Had trouble deleting Pore list");
        fflush(stdout);
    }

    return(numpartplaced);
}

/***
*
*    readshapelines 
*
*    Read all the shape information for the source from a database
*
*    Arguments: array of shape data structs
*
*    Returns:   number of lines read; nonzero if not
*
*    Calls:        Nothing
*    Called by:    genpacking
***/
int readshapelines(struct lineitem line[MAXLINES])
{
    register int i;
    char filename[MAXSTRING],buff[MAXSTRING];
    FILE *geomfile;

    /* Place real shapes instead of spheres */

    sprintf(filename,"%s%s%c%s-geom.dat",Pathroot,Shapeset,Filesep,Shapeset);
    geomfile = filehandler("genaggpack",filename,"READ");
    if (!geomfile) {
        freeallmem();
        return(MEMERR);
    } else if (Verbose) {
        printf("Successfully opened geom file\n");
        fflush(stdout);
    }

    /* Scan header and discard */
    fread_string(geomfile,buff);


    /* Read the rest of the geom file one line at a time */
    i = 0;
    while(!feof(geomfile) && i < MAXLINES) {
        fscanf(geomfile,"%s",buff);
        if (!feof(geomfile)) {
            strcpy(line[i].name,buff);
            fscanf(geomfile,"%s",buff);
            line[i].xlow = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].xhi = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].ylow = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].yhi = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].zlow = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].zhi = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].volume = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].surfarea = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].nsurfarea = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].diam = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].Itrace = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].Nnn = atoi(buff);
            fscanf(geomfile,"%s",buff);
            line[i].NGC = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].length = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].width = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].thickness = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].nlength = atof(buff);
            fscanf(geomfile,"%s",buff);
            line[i].nwidth = atof(buff);
            i++;
        }

        /* Line scanned in now */
    }

    /* Close geomfile */
    fclose(geomfile);

    return(i);
}

/***
*    create
*
*    Routine to obtain user input and create an aggregate
*    microstructure.
*
*    Arguments:  0 for coarse aggregates, 1 for fine aggregates
*    Returns:    Nothing
*
*    Calls:        genparticles
*    Called by:    main program
***/
int create(int type, int numtimes)
{
    int i,j,k,kk,ival,numsize[NUMSOURCES];
    int num_sources,ns;
    int sourceeach[NUMAGGBINS];
    int vol[NUMSOURCES][MAXSIZECLASSES],inval1,lval,total_voxels,extra_voxels;
    int voleach[NUMAGGBINS],vp[NUMAGGBINS],numeach[NUMAGGBINS];
    int target_voxels_i,delta_particles;
    int numparts[NUMSOURCES][MAXSIZECLASSES];
    int ip,radmin[NUMSOURCES][MAXSIZECLASSES],radmax[NUMSOURCES][MAXSIZECLASSES];
    float rvalmin,rvalmax,fval,val1,val2;
    char buff[MAXSTRING],gaussname[MAXSTRING];
    char coarseness_string[10],scratchname[MAXSTRING],instring[MAXSTRING];
    float fradmin[NUMSOURCES][MAXSIZECLASSES],fradmax[NUMSOURCES][MAXSIZECLASSES];
    float diam[NUMSOURCES][MAXSIZECLASSES],frad[NUMSOURCES][MAXSIZECLASSES];
    float sizeeach[NUMAGGBINS];
    FILE *fgauss,*fscratch;

    /* Initialize local arrays */

    fgauss = NULL;
    num_sources = 1;

    for (i = 0; i < NUMSOURCES; i++) {
        numsize[i] = 0;
        for (j = 0; j < MAXSIZECLASSES; j++) {
            vol[i][j] = numparts[i][j] = 0;
            radmin[i][j] = radmax[i][j] = 0;
            fradmin[i][j] = fradmax[i][j] = frad[i][j] = diam[i][j] = 0.0;
        }
    }

    for (i = 0; i < NUMAGGBINS; i++) {
        voleach[i] = numeach[i] = vp[i] = sourceeach[i] = 0;
        sizeeach[i] = 0.0;
    }

    if (type == (int)COARSE) strcpy(coarseness_string,"coarse");
    if (type == (int)FINE) strcpy(coarseness_string,"fine");

    printf("\nAdd SPHERES (0) or REAL-SHAPE (1) particles? ");
    fflush(stdout);
    read_string(instring,sizeof(instring));
    Shape = atoi(instring);
    printf("%d\n",Shape);
    fflush(stdout);

    if (numtimes == 0) {
        sprintf(scratchname,"scratchaggfile.dat");
        fscratch = filehandler("genaggpack",scratchname,"WRITE");
        if (!fscratch) {
            bailout("genaggpack","Could not open aggregate structure file");
            return(MEMERR);
        }
        fprintf(fscratch,"%d %d %d\n",Xsyssize,Ysyssize,Zsyssize);
        Mindimen = Xsyssize;
        if (Ysyssize < Mindimen) Mindimen = Ysyssize;
        if (Zsyssize < Mindimen) Mindimen = Zsyssize;
        Itz = 0;
        /*
        if (Resolution < FINEAGGRES) Itz = 1;
        */
    } else {
        sprintf(scratchname,"scratchaggfile.dat");
        fscratch = filehandler("genaggpack",scratchname,"APPEND");
        if (!fscratch) {
            bailout("genaggpack","Could not open aggregate structure file");
            return(MEMERR);
        }
    }
        
    printf("Where is the %s aggregate shape database?",coarseness_string);
    printf("\n(Include final separator in path) ");
    fflush(stdout);
    read_string(buff,sizeof(buff));
    Filesep = buff[strlen(buff)-1];
    if ((Filesep != '/') && (Filesep != '\\')) {
        printf("\nNo final file separator detected.  Using /");
        Filesep = '/';
    }
    printf("%s\n",buff);
    sprintf(Pathroot,"%s",buff);
    fflush(stdout);

    printf("\nHow many %s aggregate sources (1 - %d)? ",coarseness_string,(int)NUMSOURCES);
    fflush(stdout);
    read_string(instring,sizeof(instring));
    num_sources = atoi(instring);
    printf("%d\n",num_sources);
    fflush(stdout);
    if (num_sources < 1 || num_sources > (int)NUMSOURCES) {
        bailout("genaggpack","Illegal number of aggregate sources");
        fflush(stdout);
        return(MEMERR);
    }

    if (Shape != SPHERES) {

        /* Determine number of Gaussian quadrature points from file */

        if (Ntheta == 0) {
            sprintf(gaussname,"%sgauss120.dat",Pathroot);
            if (Verbose) printf("\nGauss file name is %s",gaussname);
            fgauss = filehandler("genaggpack",gaussname,"READ");
            if (!fgauss) {
                bailout("genaggpack","Could not open Gauss points file");
                fflush(stdout);
                return(MEMERR);
            }

            while (!feof(fgauss)) {
                fscanf(fgauss,"%f %f",&val1,&val2);
                if (!feof(fgauss)) Ntheta++;
            }
            fclose(fgauss);
            Nphi = Ntheta;
        }

        /***
        *    Allocate memory for the spherical harmonic arrays and
        *    for the Bbox array (only needed for real shapes)
        ***/

        if (!A) A = complexmatrix((long)0, (long)Nnn, (long)(-Nnn), (long)(Nnn));
        if (!AA) AA = complexmatrix((long)0, (long)Nnn, (long)(-Nnn), (long)(Nnn));
        if (!Y) Y = complexmatrix((long)0, (long)Nnn, (long)(-Nnn), (long)(Nnn));


        if (!A || !AA || !Y) {
            bailout("genaggpack","Memory allocation error for complex matrix");
            return(MEMERR);
        }

        /* Allocate memory for Gaussian quadrature points */

        if (!Xg) {
            Xg = fvector((long)(Ntheta + 1));
            if (!Xg) {
                bailout("genaggpack","Could not allocate memory for Xg");
                return(MEMERR);
            }
        }

        if (!Wg) {
            Wg = fvector((long)(Nphi + 1));
            if (!Wg) {
                bailout("genaggpack","Could not allocate memory for Wg");
                return(MEMERR);
            }
        }

        /* Read Gaussian quadrature points from file */

        sprintf(gaussname,"%sgauss120.dat",Pathroot);
        if (Verbose) printf("\nGauss file name is %s",gaussname);
        fflush(stdout);
        fgauss = filehandler("genaggpack",gaussname,"READ");
        if (!fgauss) {
            bailout("genaggpack","Could not open Gauss points file");
            return(MEMERR);
        }

        for (i = 1; i <= Ntheta; i++) {
            fscanf(fgauss,"%f %f",&Xg[i],&Wg[i]);
        }
        fclose(fgauss);

    }

    /*  The remainder happens whether spheres or real-shape */

    /* Allocate memory for the array holding the particle image */

    if (!Bbox.val) {
        if (Int3darray(&Bbox,Boxsize,Boxsize,Boxsize)) {
            bailout("genaggpack","Memory allocation error for Bbox");
            return(MEMERR);
        }
    }

    for (ns = 0; ns < num_sources; ns++) {
        printf("Source %d:  Take %s aggregate shapes from what data set?",ns+1,coarseness_string);
        printf("\n(No separator at the beginning or end) ");
        read_string(Shapeset,sizeof(Shapeset));
        printf("%s\n",Shapeset);
        if ((Shapeset[strlen(Shapeset)-1] == '/') || (Shapeset[strlen(Shapeset)-1] == '\\')) {
            Shapeset[strlen(Shapeset)-1] = '\0';
        }


        printf("Enter number of different size particles ");
        printf("to use(max. is %d)\n",MAXSIZECLASSES);
        read_string(instring,sizeof(instring));
        numsize[ns] = atoi(instring);
        printf("%d",numsize[ns]);

        if (numsize[ns] > MAXSIZECLASSES || numsize[ns] < 0) {
            bailout("genaggpack","Bad value for numsize");
            return(MEMERR);
        } else {
            printf("\nEnter information for ");
            printf("each particle class (largest size 1st)");

            /***
            *    Obtain input for each size class of particles
            ***/

            for (ip = 0; ip < numsize[ns]; ip++) {

                printf("\nEnter total volume of particles of class %d in voxels",ip+1);
                read_string(instring,sizeof(instring));
                inval1 = (int)(atoi(instring));
                printf("%d",inval1);
                vol[ns][ip] = inval1;
                printf("\nEnter smallest effective radius (in mm) ");
                printf("of particles in size class %d",ip+1);
                printf("\n(Real number <= %f please)",(float)(Mindimen/2));
                read_string(buff,sizeof(buff));
                printf("%s",buff);
                rvalmin = atof(buff);
                printf("\nEnter largest effective radius (in mm) ");
                printf("of particles in size class %d",ip+1);
                printf("\n(Real number <= %f please)",(float)(Mindimen/2));
                read_string(buff,sizeof(buff));
                printf("%s",buff);
                rvalmax = atof(buff);
                if ((2.0 * rvalmin) < (float)(Resolution_safety_coeff * Resolution)) {
                    printf("\nERROR:  Minimum particle radius is too small for the");
                    printf("\n        resolution of the system.  Some small particles");
                    printf("\n        may not be resolved in the image.");
                    return(MEMERR);
                }
                if ((2.0 * rvalmin) > (float)(Size_safety_coeff * Mindimen)) {
                    printf("\nERROR:  Entire size class is too large for the");
                    printf("\n        size of the system.  This class will not");
                    printf("\n        be resolved in the image.");
                    return(MEMERR);
                }
                if ((2.0 * rvalmax) < (Resolution_safety_coeff * Resolution)) {
                    printf("\nERROR:  Entire size class is too small for the");
                    printf("\n        resolution of the system.  This class will not");
                    printf("\n        be resolved in the image.");
                    return(MEMERR);
                }
                if ((2.0 * rvalmax) > (float)(Size_safety_coeff * Mindimen)) {
                    printf("\nWARNING:  Maximum particle radius is too large for the");
                    printf("\n          size of the system.  Some large particles");
                    printf("\n          may not be resolved in the image.");
                    return(MEMERR);
                }

                fradmin[ns][ip] = rvalmin/Resolution; /* voxel units now */
                fradmax[ns][ip] = rvalmax/Resolution; /* voxel units now */
                radmin[ns][ip] = (int)(rvalmin/Resolution);  /* voxel units now */
                radmax[ns][ip] = (int)(rvalmax/Resolution);  /* voxel units now */

                /***
                 *  Determine volume weighted average radius
                 *  Use Trapezoidal Rule
                 ***/

                frad[ns][ip] = meanradius(100,fradmin[ns][ip],fradmax[ns][ip]);
                if (Verbose) {
                    printf("\nMin rad = %f voxels, ",fradmin[ns][ip]);
                    printf("Max rad = %f voxels, ",fradmax[ns][ip]);
                    printf("Mean radius of particle = %f voxels",frad[ns][ip]);
                    fflush(stdout);
                }
                diam[ns][ip] = 2.0 * frad[ns][ip];
                Volpart[ns][ip] = (int)diam2vol(diam[ns][ip]);

            }

            /***
            * Determine number of particles of each diameter to add, assuming spheres.
            * Try to get the actual overall volume fraction closer to the target while
            * maintaining fidelity to the PSD
            *
            * The approach below starts with the largest size particles, and tries
            * to stay close to the desired fraction of particles this diameter
            * and larger
            *
            * Remember, total_solid_voxels and total_voxels refer only to the phase
            * in question, not the combination of all the phases.
            ***/
             
            total_voxels = 0;
            for (ip = 0; ip < numsize[ns]; ip++) {
                numparts[ns][ip] = (int)(((float)vol[ns][ip]/(float)(Volpart[ns][ip])) + 0.5);
                total_voxels += numparts[ns][ip] * Volpart[ns][ip];
                printf("\n\nSource %d, Size class %d (max %d): ",ns,ip,numsize[ns]-1);
                printf("Number of particles of diameter %f = ",diam[ns][ip]);
                printf("%d\n\tVolume of each particle of diameter ",numparts[ns][ip]);
                printf("%f = %d",diam[ns][ip],Volpart[ns][ip]);
            }
            printf("\nTotal voxels on first pass = %d, ",total_voxels);
            printf("making adjustments of particle numbers now...");
            fflush(stdout);

            extra_voxels = 0;
            for (ip = 0; ip < numsize[ns]; ip++) {
                target_voxels_i = vol[ns][ip];
                printf("\nTarget voxels in size class %d ",ip);
                printf("(of %d for source %d) = %d",numsize[ns]-1,ns,target_voxels_i);
                fflush(stdout);
                extra_voxels += (target_voxels_i - (numparts[ns][ip] * Volpart[ns][ip]));
                printf("\n\tExtra voxels (cumulative) = %d",extra_voxels);
                fflush(stdout);
                if (Volpart[ns][ip] < (int)(fabs((float)extra_voxels))) {
                    delta_particles = (int)((float)(extra_voxels)/(float)(Volpart[ns][ip]));
                    numparts[ns][ip] += delta_particles;
                    total_voxels += (delta_particles * Volpart[ns][ip]);
                    extra_voxels -= (delta_particles * Volpart[ns][ip]);
                    printf("\n\t\tIncreased number of particles in size class ");
                    printf("%d by %d",ip,delta_particles);
                    fflush(stdout);
                }
            }

            /***
             * Finally, adjust the number of the smallest size class to
             * make the overall volume fraction exact
             ***/

            printf("\nSource %d (of %d), ",ns,(int)NUMSOURCES);
            printf("number of bins = %d (of %d)",numsize[ns],(int)MAXSIZECLASSES);
            fflush(stdout);
            if (diam[ns][numsize[ns]-1] <= 1.0) {
                numparts[ns][numsize[ns]-1] += extra_voxels;
                if (numparts[ns][numsize[ns]-1] < 0) numparts[ns][numsize[ns]-1] = 0;
            }

        }
    }

    /* Next thing to do is to sort the particles by size */

    k = 0;
    for (i = 0; i < NUMSOURCES; i++) {
        for (j = 0; j < MAXSIZECLASSES; j++) {

            /* Only keep a source-size class if it has some particles to place */

            if (numparts[i][j] > 0) {
                voleach[k] = vol[i][j];
                numeach[k] = numparts[i][j];
                sizeeach[k] = frad[i][j];
                vp[k] = Volpart[i][j];
                sourceeach[k] = i;
                k++;
            }
        }
    }

    Numaggbins = k;

    if (Debug) {
        printf("\nBubble sorting arrays... ");
        fflush(stdout);
    }

    for (i = 0; i < Numaggbins; i++) {
        for (j = (i+1); j < Numaggbins; j++) {
            if (sizeeach[i] < sizeeach[j]) {

                ival = sourceeach[i];
                sourceeach[i] = sourceeach[j];
                sourceeach[j] = ival;

                lval = voleach[i];
                voleach[i] = voleach[j];
                voleach[j] = lval;

                lval = numeach[i];
                numeach[i] = numeach[j];
                numeach[j] = lval;

                fval = sizeeach[i];
                sizeeach[i] = sizeeach[j];
                sizeeach[j] = fval;

                lval = vp[i];
                vp[i] = vp[j];
                vp[j] = lval;

            }
        }
    }
    
    if (Verbose) {
        lval = 0;
        printf(" Done!\nResults:");
            for (i = 0; i < Numaggbins; i++) {
                lval += voleach[i];
                printf("\n\tRad = %.3f, Src = %d, ",sizeeach[i],sourceeach[i]);
                printf("Tot vox = %d, Num needed = %d",voleach[i],numeach[i]);
                fflush(stdout);
            }

        printf("\n****Total solid voxels to place = %d (system size = %d)",lval,Sysvox);
        printf("\n****That is a volume fraction of %f",(float)((float)lval/(float)Sysvox));
        printf("\n\n");
        fflush(stdout);
    }

    /***
    *    Place particles at random    
    ***/

    kk = genpacking(type,num_sources,sourceeach,
                    voleach,vp,numeach,sizeeach,fscratch);

    if (kk == MEMERR) {
        fclose(fscratch);
        return(MEMERR);
    }
   
    fclose(fscratch);
    return(0);
}

/***
*    printbox 
*
*    Routine to print the contents of Bbox
*
*    Arguments:  Filename
*    Returns:    0 if okay, nonzero otherwise
*
*    Calls:        filehandler
*    Called by:    nothing
***/
int printbox(char *filename, int nxp, int nyp, int nzp)
{
    register int i,j,k;
    FILE *fpout;

    fpout = filehandler("genaggpack",filename,"WRITE");
    if (!fpout) {
        return(1);
    }

    fprintf(fpout,"%d,%d,%d\n",nxp,nyp,nzp);

    for (k = 0; k <= nzp; ++k) {
        for (j = 0; j <= nyp; ++j) {
            if (j == 0) {
                fprintf(fpout,"\n%d:\t",k);
            } else {
                fprintf(fpout,"\t");
            }
            for (i = 0; i <= nxp; ++i) {
                if (Bbox.val[getInt3dindex(Bbox,i,j,k)] == POROSITY) {
                    fprintf(fpout,"0 ");
                } else {
                    fprintf(fpout,"1 ");
                }
            }
            fprintf(fpout,"\n");
        }
    }

    fclose(fpout);
    return(0);
}

/***
* Decide if a solid voxel is on the periphery of a particle
*
*     Arguments:  x, y, z coordinates of voxel
*     
*     Returns:    1 if periphery, 0 if not
***/
int isPeriph(int x, int y, int z)
{
    int neigh,newpos;

    for (neigh = 0; neigh < 6; neigh++) {  /* Check first nearest neighbors only */
        switch (neigh) {
            case 0:
               newpos = z + 1;
               newpos += checkbc(newpos,Zsyssize);
               if (Bbox.val[getInt3dindex(Bbox,x,y,newpos)] == POROSITY) {
                   return(1);
               }
               break;
            case 1:
               newpos = z - 1;
               newpos += checkbc(newpos,Zsyssize);
               if (Bbox.val[getInt3dindex(Bbox,x,y,newpos)] == POROSITY) {
                   return(1);
               }
            case 2:
               newpos = y + 1;
               newpos += checkbc(newpos,Ysyssize);
               if (Bbox.val[getInt3dindex(Bbox,x,newpos,z)] == POROSITY) {
                   return(1);
               }
               break;
            case 3:
               newpos = y - 1;
               newpos += checkbc(newpos,Ysyssize);
               if (Bbox.val[getInt3dindex(Bbox,x,newpos,z)] == POROSITY) {
                   return(1);
               }
               break;
            case 4:
               newpos = x + 1;
               newpos += checkbc(newpos,Xsyssize);
               if (Bbox.val[getInt3dindex(Bbox,newpos,y,z)] == POROSITY) {
                   return(1);
               }
               break;
            default:
               newpos = x - 1;
               newpos += checkbc(newpos,Xsyssize);
               if (Bbox.val[getInt3dindex(Bbox,newpos,y,z)] == POROSITY) {
                   return(1);
               }
               break;
        }
    }
    return(0);
}


/***
* Get the integer id of a voxel
*
*     Arguments:  x, y, z coordinates of voxel
*     
*     Returns:    int id of voxel
***/
int voxpos(int x, int y, int z)
{
    return ( (z * Zlayersize) + (y * Xsyssize) + x);
}

/***
* Get the X coordinate from integer id of a voxel
*
*     Arguments:  id of voxel
*     
*     Returns:    int x coordinate
***/
int getXfromNs(int ns)
{
    int x,y,z;

    z = ns / (Zlayersize);
    y = (ns - (z * Zlayersize)) / Xsyssize;
    x = ns - (z * Zlayersize) - (y * Xsyssize);
    return x;
}

/***
* Get the Y coordinate from integer id of a voxel
*
*     Arguments:  id of voxel
*     
*     Returns:    int y coordinate
***/
int getYfromNs(int ns)
{
    int y,z;

    z = ns / (Zlayersize);
    y = (ns - (z * Zlayersize)) / Xsyssize;

    return y;
}

/***
* Get the X coordinate from integer id of a voxel
*
*     Arguments:  id of voxel
*     
*     Returns:    int z coordinate
***/
int getZfromNs(int ns)
{
    return (ns / (Zlayersize));
}

/***
* Use trapezoidal rule to find the volume weighted mean radius of
* a sphere between minimum and maximum radius values.
*
*     Arguments:  numdiv is number of integration points
*                 minval is minimum radius value
*                 maxval is maximum radius valud
*     
*     Returns:    volume weighted mean radius
***/
float meanradius(int numdiv, float minval, float maxval)
{
    register int i;
    float dx,rval;
    float numerator_int,denominator_int;
    float averadius;

    /***
     *  Determine volume weighted average radius
     *  Use Trapezoidal Rule
     ***/

    dx = (maxval - minval)/(float)(numdiv);

    rval = minval;
    numerator_int = (rval * rval * rval * rval);
    denominator_int = (rval * rval * rval);
    rval += dx;
    for (i = 1; i < numdiv; i++) {
        numerator_int += (2.0 * rval * rval * rval * rval);
        denominator_int += (2.0 * rval * rval * rval);
        rval += dx;
    }

    numerator_int += (rval * rval * rval * rval);
    denominator_int += (rval * rval * rval);

    averadius = numerator_int / denominator_int;
    return(averadius);
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
void measure(void)
{
    int npor,nagg,nitz;
    register int i,j,k;
    char filen[MAXSTRING];
    int valph;
    FILE *outfile;

    /* Counters for the various phase fractions */

    npor = nagg = nitz = 0;;

    /* Check all voxels in 3-D microstructure */

    printf("\nEnter full path and name of file for writing statistics: ");
    read_string(filen,sizeof(filen));
    printf("\n%s\n",filen);
    outfile = filehandler("genaggpack",filen,"WRITE");
    if (!outfile) {
        freeallmem();
        exit(1);
    }

    for (k = 0; k < Zsyssize; k++) {
        for (j = 0; j < Ysyssize; j++) {
            for (i = 0; i < Xsyssize; i++) {

                valph = Agg.val[getInt3dindex(Agg,i,j,k)];    
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

    fprintf(outfile,"\nPhase counts are: \n");
    fprintf(outfile,"\tPorosity = %d \n",npor);
    fprintf(outfile,"\tAggregate = %d \n",nagg);
    fprintf(outfile,"\tITZ = %d \n",nitz);
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
void connect(void)
{
    register int i,j,k;
    int inew,ntop,nthrough,ncur,nnew,ntot;
    int *nmatx,*nmaty,*nmatz,*nnewx,*nnewy,*nnewz;
    int xcn,ycn,zcn,nvox,x1,y1,z1,igood;
    int jnew,icur;
    char instring[MAXSTRING];

    nmatx = nmaty = nmatz = NULL;
    nnewx = nnewy = nnewz = NULL;

    nmatx = ivector(Maxburning);
    nmaty = ivector(Maxburning);
    nmatz = ivector(Maxburning);
    nnewx = ivector(Maxburning);
    nnewy = ivector(Maxburning);
    nnewz = ivector(Maxburning);

    if (!nmatx || !nmaty || !nmatz
        || !nnewx || !nnewy || !nnewz) {

        freeallmem();
        bailout("genaggpack","Memory allocation failure");
        fflush(stdout);
        exit(1);
    }

    printf("Enter phase to analyze 0) pores 1) Aggregate 2) ITZ  \n");
    read_string(instring,sizeof(instring));
    nvox = atoi(instring);
    printf("%d \n",nvox);
    if ((nvox != POROSITY) && (nvox != AGG) && (nvox != ITZ)) {
        freeallmem();
        bailout("connect","Bad ID to analyze connectivity");
        exit(1);
    }

    /***
    *    Counters for number of voxels of phase
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
            igood = 0;    /* Indicates if bottom has been reached */

            if (((Agg.val[getInt3dindex(Agg,i,j,k)] == nvox)
                    && ((Agg.val[getInt3dindex(Agg,i,j,Zsyssize-1)] == nvox)
                    || (Agg.val[getInt3dindex(Agg,i,j,Zsyssize-1)] == (nvox + Burnt))))
                || ((Agg.val[getInt3dindex(Agg,i,j,Zsyssize-1)] > 0)
                    && (Agg.val[getInt3dindex(Agg,i,j,k)] > 0)
                    && (Agg.val[getInt3dindex(Agg,i,j,k)] < Burnt)
                    && (nvox == AGG || nvox == ITZ))) {

                /* Start a burn front */

                Agg.val[getInt3dindex(Agg,i,j,k)] += Burnt;
                ntot++;
                ncur++;

                /***
                *    Burn front is stored in matrices
                *    nmat* and nnew*
                ***/

                nmatx[ncur] = i;
                nmaty[ncur] = j;
                nmatz[ncur] = 0;

                /* Burn as long as new (fuel) voxels are found */

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
                                    if (x1 < 0) x1 += Xsyssize;
                                    break;
                                case 2:
                                    x1++;
                                    if (x1 >= Xsyssize) x1 -= Xsyssize;
                                    break;
                                case 3:
                                    y1--;
                                    if (y1 < 0) y1 += Ysyssize;
                                    break;
                                case 4:
                                    y1++;
                                    if (y1 >= Ysyssize) y1 -= Ysyssize;
                                    break;
                                case 5:
                                    z1--;
                                    if (z1 < 0) z1 += Zsyssize;
                                    break;
                                case 6:
                                    z1++;
                                    if (z1 >= Zsyssize) z1 -= Zsyssize;
                                    break;
                                default:
                                    break;
                            }

                            /***
                            *    Nonperiodic in z direction so
                            *    be sure to remain in the 3-D box
                            ****/

                            if ((z1 >= 0) && (z1 < Zsyssize)) {
                                if ((Agg.val[getInt3dindex(Agg,x1,y1,z1)] == nvox)
                                    || ((Agg.val[getInt3dindex(Agg,x1,y1,z1)] > 0)
                                        && (Agg.val[getInt3dindex(Agg,x1,y1,z1)] < Burnt)
                                        && (nvox == AGG || nvox == ITZ))) {

                                    ntot++;
                                    Agg.val[getInt3dindex(Agg,x1,y1,z1)] += Burnt;
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

                                    if (z1 == Zsyssize - 1) igood = 1;
                                }
                            }
                        }
                    }

                    if (nnew > 0) {

                        ncur = nnew;

                        /* update the burn front matrices */

                        for (icur = 1; icur <= ncur; icur++) {
                            nmatx[icur]=nnewx[icur];
                            nmaty[icur]=nnewy[icur];
                            nmatz[icur]=nnewz[icur];
                        }
                    }

                } while (nnew > 0);

                ntop += ntot;
                if (igood) nthrough += ntot;

            }
        }
    }

    printf("Phase ID= %d \n",nvox);
    printf("Number accessible from top= %d \n",ntop);
    printf("Number contained in through pathways= %d \n",nthrough);

    /***
    *    Return the burnt sites to their original
    *    phase values
    ***/
    
    for (k = 0; k < Zsyssize; k++) {
        for (j = 0; j < Ysyssize; j++) {
            for (i = 0; i < Xsyssize; i++) {
                if (Agg.val[getInt3dindex(Agg,i,j,k)] >= Burnt) {
                    Agg.val[getInt3dindex(Agg,i,j,k)] -= Burnt;
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
void outmic(void)
{
    int ix,iy,iz,valout;
    int transparent;
    char filen[MAXSTRING],pfilen[MAXSTRING],buff[MAXSTRING],filestruct[MAXSTRING],ch;
    FILE *outfile,*poutfile,*infile;

    printf("Enter name of file for final packing image\n");
    read_string(filen,sizeof(filen));
    printf("%s\n",filen);

    transparent = 1;
    printf("Show cement binder as opaque (0) or transparent (1)?\n");
    read_string(buff,sizeof(buff));
    printf("%s\n",buff);
    transparent = atoi(buff);

    outfile = filehandler("genaggpack",filen,"WRITE");
    if (!outfile) {
        freeallmem();
        exit(1);
    }

    sprintf(pfilen,"%s.pimg",filen);
    poutfile = filehandler("genaggpack",pfilen,"WRITE");
    if (!poutfile) {
        freeallmem();
        exit(1);
    }


    /***
    *    Images must carry along information about the
    *    VCCTL software version used to create the file, the system
    *    size, and the image resolution.
    ***/

    if (write_imgheader(outfile,Xsyssize,Ysyssize,Zsyssize,Resolution)) {
        fclose(outfile);
        freeallmem();
        bailout("genaggpack","Error writing image header");
        exit(1);
    }

    if (write_imgheader(poutfile,Xsyssize,Ysyssize,Zsyssize,Resolution)) {
        fclose(outfile);
        freeallmem();
        bailout("genaggpack","Error writing image header");
        exit(1);
    }

    for (iz = 0; iz < Zsyssize; iz++) {
        for (iy = 0; iy < Ysyssize; iy++) {
            for (ix = 0; ix < Xsyssize; ix++) {
                valout = Agg.val[getInt3dindex(Agg,ix,iy,iz)];
                if ((transparent != 1) && valout == POROSITY) valout = C3A;
                fprintf(outfile,"%1d\n",valout);
                valout = Pagg.val[getInt3dindex(Pagg,ix,iy,iz)];
                fprintf(poutfile,"%d\n",valout);
            }
        }
    }

    fclose(outfile);
    fclose(poutfile);

    sprintf(filestruct,"%s.struct",filen);
    outfile = filehandler("genaggpack",filestruct,"WRITE");
    infile = filehandler("genaggpack","scratchaggfile.dat","READ");

    fprintf(outfile,"%d\n",Npart);
    while (!feof(infile)) {
        ch = getc(infile);
        if (!feof(infile)) putc(ch,outfile);
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
void harm(double theta, double phi)
{
    int i,m,n,mm,nn;
    double x,s,xn,xm;
    double realnum;
    double p[NNN+1][2*(NNN+1)];
    fcomplex fc1,fc2,fc3;

    x = cos(theta);
    s = (double)(sqrt((double)(1.0-(x*x))));

    for (n = 0; n <= Nnn; n++) {
        for (m = 0; m <= 2*(Nnn); m++) {
            p[n][m] = 0.0;
        }
    }

    p[0][0]=1.0;
    p[1][0]=x;
    p[1][1]=s;
    p[2][0]=0.5*(3.*x*x-1.);
    p[2][1]=3.*x*s;
    p[2][2]=3.*(1.-x*x);
    p[3][0]=0.5*x*(5.*x*x-3.);
    p[3][1]=1.5*(5.*x*x-1.)*s;
    p[3][2]=15.*x*(1.-x*x);
    p[3][3]=15.*(pow(s,3));
    p[4][0]=0.125*(35.*(pow(x,4))-30.*x*x+3.);
    p[4][1]=2.5*(7.*x*x*x-3.*x)*s;
    p[4][2]=7.5*(7.*x*x-1.)*(1.-x*x);
    p[4][3]=105.*x*(pow(s,3));
    p[4][4]=105.*(pow((1.-x*x),2));
    p[5][0]=0.125*x*(63.*(pow(x,4))-70.*x*x+15.);
    p[5][1]=0.125*15.*s*(21.*(pow(x,4))-14.*x*x+1.);
    p[5][2]=0.5*105.*x*(1.-x*x)*(3.*x*x-1.);
    p[5][3]=0.5*105.*(pow(s,3))*(9.*x*x-1.);
    p[5][4]=945.*x*(pow((1.-x*x),2));
    p[5][5]=945.*(pow(s,5));
    p[6][0]=0.0625*(231.*(pow(x,6))-315.*(pow(x,4))+105.*x*x-5.);
    p[6][1]=0.125*21.*x*(33.*(pow(x,4))-30.*x*x+5.)*s;
    p[6][2]=0.125*105.*(1.-x*x)*(33.*(pow(x,4))-18.*x*x+1.);
    p[6][3]=0.5*315.*(11.*x*x-3.)*x*(pow(s,3));
    p[6][4]=0.5*945.*(1.-x*x)*(1.-x*x)*(11.*x*x-1.);
    p[6][6]=10395.*pow((1.-x*x),3);
    p[7][0]=0.0625*x*(429.*(pow(x,6))-693.*(pow(x,4))+315.*x*x-35.);
    p[7][1]=0.0625*7.*s*(429.*(pow(x,6))-495.*(pow(x,4))+135.*x*x-5.);
    p[7][2]=0.125*63.*x*(1.-x*x)*(143.*(pow(x,4))-110.*x*x+15.);
    p[7][3]=0.125*315.*(pow(s,3))*(143.*(pow(x,4))-66.*x*x+3.);
    p[7][4]=0.5*3465.*x*(1.-x*x)*(1.-x*x)*(13.*x*x-3.);
    p[7][5]=0.5*10395.*(pow(s,5))*(13.*x*x-1.);
    p[7][6]=135135.*x*(1.-x*x)*(1.-x*x)*(1.-x*x);
    p[7][7]=135135.*(pow(s,7));
    p[8][0]=(1./128.)*(6435.*(pow(x,8))-12012.*(pow(x,6))+6930.*(pow(x,4))-
                1260.*x*x+35.);
    p[8][1]=0.0625*9.*x*s*(715.*(pow(x,6))-1001.*(pow(x,4))+385.*x*x-35.);
    p[8][2]=0.0625*315.*(1.-x*x)*(143.*(pow(x,6))-143.*(pow(x,4))+33.*x*x-1.);
    p[8][3]=0.125*3465.*x*(pow(s,3))*(39.*(pow(x,4))-26.*x*x+3.);
    p[8][4]=0.125*10395.*(1.-x*x)*(1.-x*x)*(65.*(pow(x,4))-26.*x*x+1.);
    p[8][5]=0.5*135135.*x*(pow(s,5))*(5.*x*x-1.);
    p[8][6]=0.5*135135.*(pow((1.-x*x),3))*(15.*x*x-1.);
    p[8][7]=2027025.*x*(pow(s,7));
    p[8][8]=2027025.*(pow((1.-x*x),4));

    /* Now generate spherical harmonics for n = 0,8 (follows Arfken) */

    for (n = 0; n <= 8; n++) {

    /* does n = 0 separately */

        if (n == 0) {
            Y[0][0].r = 1.0 / (sqrt(4.0 * Pi));
            Y[0][0].i = 0.0;
        } else {
            for (m = n; m >= -n; m--) {
                if (m >= 0) {
                    fc1 = Complex(cos(m*phi),sin(m*phi));
                    realnum = (pow(-1.,m))*sqrt( ((2*n+1)/4./Pi) *
                        fac(n-m)/fac(n+m) ) * p[n][m];
                    Y[n][m] = RCmul(realnum,fc1);

                } else if (m < 0) {
                    mm = -m;
                    fc1 = Conjg(Y[n][m]);
                    realnum = pow(-1.0,mm);
                    Y[n][m] = RCmul(realnum,fc1);
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
            xn = (double)(n-1);
            xm = (double)m;
            realnum = (2.*xn+1.)*x;
            Y[n][m] = RCmul(realnum,Y[n-1][m]);
            realnum = -sqrt((2.*xn+1.)*((xn*xn)-(xm*xm)) /(2.*xn-1.));
            fc1 = RCmul(realnum,Y[n-2][m]);
            Y[n][m] = Cadd(Y[n][m],fc1);
            realnum = (sqrt((2.*xn+1.)*(pow((xn+1.),2)-(xm*xm))/(2.*xn+3.)));
            Y[n][m] = RCmul((1.0/realnum),Y[n][m]);
        }

        nn = (2 * n) - 1;
        p[n][n] = pow(s,n);
        for (i = 1; i <= nn; i += 2) {
            p[n][n] *= (double)i;
        }

        fc1 = Complex(cos(n*phi),sin(n*phi));
        realnum = (pow(-1.,n))*sqrt(((2*n+1)/4./Pi)*fac(n-n)/fac(n+n)) * p[n][n];
        Y[n][n] = RCmul(realnum,fc1);

        /***
        *    Now do second to the top m=n-1 using the exact m=n,
        *    and the recursive m=n-2 found previously
        ***/

        xm = (double)(n-1);
        xn = (double)n;

        realnum = -1.0;
        fc1 = Complex(cos(phi),sin(phi));
        fc2 = Cmul(fc1,Y[n][n-2]);
        Y[n][n-1] = RCmul(realnum,fc2);
        realnum = ( xn*(xn+1.)-xm*(xm-1.) ) / sqrt((xn+xm)*(xn-xm+1.));
        Y[n][n-1] = RCmul(realnum,Y[n][n-1]);

        realnum = sqrt((xn-xm)*(xn+xm+1.));
        fc1 = Complex(cos(phi),-sin(phi));
        fc2 = Cmul(fc1,Y[n][n]);
        fc3 = RCmul(realnum,fc2);
        Y[n][n-1] = Csub(Y[n][n-1],fc3);

        realnum = (s/2.0/xm/x);
        Y[n][n-1] = RCmul(realnum,Y[n][n-1]);
    }

    /* now fill in -m terms */

    for (n = 0; n <= Nnn; n++) {
        for (m = -1; m >= -n; m--) {
            mm = -m;
            realnum = pow(-1.0,mm);
            fc1 = Conjg(Y[n][mm]);
            Y[n][m] = RCmul(realnum,fc1);
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
double fac(int j)
{
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
*    Routine to allocate memory for a 1D vector of pointers to particle structures.
*    All array indices are assumed to start with zero.
*
*    Arguments:    int number of voxels in the particle
*    Returns:    Pointer to memory location of first element
*
*    Calls:        no other routines
*    Called by:    main routine
*
***/
struct particle *particlevector(int numvox)
{
    struct particle *ps;
    /* Allocate space for new particle info */

    ps = (struct particle *)malloc(sizeof(struct particle));
    if (ps != NULL) {
        ps->pvid = (int *)malloc(numvox * sizeof(int));
        ps->xi = (int *)malloc(numvox * sizeof(int));
        if (ps->xi != NULL && ps->pvid != NULL) {
            ps->yi = (int *)malloc(numvox * sizeof(int));
            if (ps->yi != NULL) {
                ps->zi = (int *)malloc(numvox * sizeof(int));
                if (ps->zi != NULL) {
                    ps->numvox = numvox;
                    return(ps);
                } else {
                    free(ps->yi);
                    free(ps->pvid);
                    free(ps->xi);
                    free(ps);
                }
            } else {
                free(ps->pvid);
                free(ps->xi);
                free(ps);
            }
        } else {
            if (ps->xi) free(ps->xi);
            if (ps->pvid) free(ps->pvid);
            free(ps);
        }
    }

    return(ps);
}

void free_particlevector(struct particle *ps)
{
    if (ps != NULL) {
        printf("\n\t\tFreeing Particle ps now...");
        fflush(stdout);
        if (ps->pvid != NULL) {
            printf("\n\t\t\tFreeing Particle ps->pvid now... ");
            fflush(stdout);
            free(ps->pvid);
            printf("Done ");
            fflush(stdout);
        }
        if (ps->xi != NULL) {
            printf("\n\t\t\tFreeing Particle ps->xi now... ");
            fflush(stdout);
            free(ps->xi);
            printf("Done ");
            fflush(stdout);
        }
        if (ps->yi != NULL) {
            printf("\n\t\t\tFreeing Particle ps->yi now... ");
            fflush(stdout);
            free(ps->yi);
            printf("Done ");
            fflush(stdout);
        }
        if (ps->zi != NULL) {
            printf("\n\t\t\tFreeing Particle ps->zi now... ");
            fflush(stdout);
            free(ps->zi);
            printf("Done ");
            fflush(stdout);
        }
        printf("\n\t\t\tFreeing Particle ps now... ");
        fflush(stdout);
        free(ps);
        printf("Done ");
        fflush(stdout);
    }

    ps = NULL;

    return;
}

/***
*    particlepointervector
*
*    Routine to allocate memory for a 1D vector of pointers to particle structures.
*    All array indices are assumed to start with zero.
*
*    Arguments:    int number of elements in each dimension
*    Returns:    Pointer to memory location of first element
*
*    Calls:        no other routines
*    Called by:    main routine
*
***/
struct particle **particlepointervector(int size)
{
    struct particle **ps;
    size_t oneparticlesize,particlesize;

    oneparticlesize = sizeof(struct particle*);
    particlesize = size * oneparticlesize;
    ps = (struct particle **)malloc(particlesize);
    if (!ps) {
        printf("\n\nCould not allocate space for particlepointervector.");
        return(NULL);
    }

    return(ps);
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
void free_particlepointervector(struct particle **ps)
{
    int i = 0;
    for (i = 0; i < Npartc; i++) {
        if (ps[i] != NULL) {
            if (ps[i]->pvid != NULL) free((char*) (ps[i]->pvid));
            if (ps[i]->xi != NULL) free((char*) (ps[i]->xi));
            if (ps[i]->yi != NULL) free((char*) (ps[i]->yi));
            if (ps[i]->zi != NULL) free((char*) (ps[i]->zi));
        }
    }
    free((char*) (ps[0]));
    free((char*) (ps));

    return;
}

/***
*    Pore_create_porelist
*
*    Create a doubly linked list of pore voxels
*
*    Arguments:  calcsizes is 1 if we should calculate the pore sizes
*                frad is the radius of the particle trying to fit in the pores
*                firstnpores is how many elements at the beginning of the
*                        list are larger than the particle
*    Returns:    number of pore voxels found
*
*    Called by:  genparticles
*
***/
int Pore_create_porelist(int calcsizes, float frad, int *firstnpores)
{
    register int i,j,k;
    int numpores = 0;
    int radius = 0;
    struct Pore *Pore_current;

    int default_radius = Xsyssize / 2;

    /***
     * Check to make sure that list does not already exist
     ***/

    if (Pore_head) {
        if (Debug) {
            printf("\n*In Pore_create_porelist, need to delete current list...");
            fflush(stdout);
        }
        Pore_delete();
        if (Debug) {
            printf("\n*Done deleting current list");
            fflush(stdout);
        }
    }

    for (k = 0; k < Zsyssize; k++) {
        for (j = 0; j < Ysyssize; j++) {
            for (i = 0; i < Xsyssize; i++) {
                if (Debug) {
                    printf("\n**In Pore_create_porelist, (%d,%d,%d)",i,j,k);
                    fflush(stdout);
                }
                /*  Intentionally do not add ITZ to this list */
                if (Agg.val[getInt3dindex(Agg,i,j,k)] == POROSITY) {
                    if (calcsizes) {
                        radius = getPoreRadius(i,j,k);
                    } else {
                        radius = default_radius;
                    }
                    if (Pore_push(voxpos(i,j,k),radius)) {
                         printf("\nError: Had trouble pushing %d",voxpos(i,j,k));
                         fflush(stdout);
                         return (MEMERR);
                    }
                    numpores++;
                }
            }
        }
    }

    (*firstnpores) = numpores;

    if (calcsizes) {

        if (Verbose) {
            printf("\nPore_create_porelist: Sorting the pore list ");
            printf("in descending order of size... ");
            fflush(stdout);
        }
        if (mergeSort()) {;
            printf("\nERROR: mergeSort failed");
            fflush(stdout);
        } else {
            printf(" Done!");
            fflush(stdout);
        }

        /* Find the cutoff element in the list */

        (*firstnpores) = 0;
        Pore_current = Pore_head;

        while ((Pore_current->radius >= (int)(frad+0.5))
                && (Pore_current->next != NULL)) {

            (*firstnpores)++;
            Pore_current = Pore_current->next;
        }

        if (Verbose) {
            printf("\nPore_create_porelist: Firstnpores = %d, ",(*firstnpores));
            printf("numpores = %d, min radius = %d",numpores,Pore_head->radius);
            fflush(stdout);
        }
    }

    return(numpores);
}

/***
*    getPoreRadius
*
*    Calculates and returns the radius of the largest sphere centered
*    on a pore voxel that contains only pore voxels (measure of the pore size)
*
*    Arguments:  x,y,z coordinates of the pore voxel in question
*    Returns:    radius of largest sphere that contains only pore voxels
*
*    Called by:  Pore_create_porelist
*
***/
int getPoreRadius(int x, int y, int z)
{
    register int i,j,k;
    int xp,yp,zp;
    int maxrad,rad;
    float i2,j2,k2,dist;

    maxrad = MaxPoreSizeToCheck;

    for (rad = 1; (rad <= MaxPoreSizeToCheck); rad++) {
        for (k = -rad; k <= rad; ++k) {
            k2 = k * k;
            zp = z + k;
            zp += checkbc(zp,Zsyssize);
            for (j = -rad; j <= rad; ++j) {
                j2 = j * j;
                yp = y + j;
                yp += checkbc(yp,Ysyssize);
                for (i = -rad; i <= rad; ++i) {
                    i2 = i * i;
                    xp = x + i;
                    xp += checkbc(xp,Xsyssize);
                    dist = sqrt(i2 + j2 + k2);
                    if (Agg.val[getInt3dindex(Agg,xp,yp,zp)] != POROSITY) {
                        return ((int)(dist - 0.5));
                    }
                }
            }
        }
    }

    return(MaxPoreSizeToCheck);
}

/***
*    Pore_push
*
*    Push a new item at beginning of a doubly linked list of pore voxel positions
*
*    Arguments:  
*                voxel position id and pore radius
*    Returns:    int status (0 is okay)
*
*    Called by:  genparticles
*
***/
int Pore_push(int val, int radius)
{

    /* Check if head element has been established yet */

    if (Pore_head == NULL) {

        Pore_head = (struct Pore*)malloc(sizeof(struct Pore));
        if (!Pore_head) {
            return(1);
        }
        Pore_head->ns = val;
        Pore_head->radius = radius;
        Pore_head->prev = NULL;
        Pore_head->next = NULL;
        Pore_tail = Pore_head;

        return(0);

    } else {

    /* allocate new element */
    
        struct Pore *newlink = (struct Pore*)malloc(sizeof(struct Pore));
        if (!newlink) {
            return(1);
        }

        newlink->ns = val;
        newlink->radius = radius;
        newlink->prev = NULL;
        newlink->next = Pore_head;

        /* Change prev of head item to the new item */
        Pore_head->prev = newlink;

        /* Move the head to point to the new item */
        Pore_head = newlink;

        return(0);
    }
}

/***
*    Pore_find_pos
*
*    Go to a particular position and return pointer to the voxel
*
*    Arguments:  
*                voxel position id
*    Returns:    int status (0 is okay)
*
*    Called by:  genparticles
*
***/
struct Pore *Pore_find_pos(int pos)
{
    int idx = 0;
    struct Pore *temp = Pore_head;

    for (idx = 0; idx < pos; idx++) {
        if (temp != Pore_tail) {
            temp = temp->next;
        } else {
            return NULL;
        }
    }

    return (temp);
}

/***
*    Pore_find_val
*
*    Find a link with a given value and return pointer to the voxel
*
*    Arguments:  
*                voxel position id
*    Returns:    int status (0 is okay)
*
*    Called by:  genparticles
*
***/
struct Pore *Pore_find_val(int val)
{
    struct Pore *temp;
    struct Pore *noval = NULL;

    temp = Pore_head;

    if (temp->ns == val) {
        return(temp);
    }

    while (temp != NULL) {
        if (temp->ns == val) {
            return(temp);
        }
        temp = temp->next;
    }

    return (noval);
}

/***
*    Pore_delete_val

*    Delete item from a doubly linked list of pore voxel positions
*
*    Arguments:  Value (id) of item to delete
*    Returns:    int status (0 is okay)
*
*    Called by:  genparticles
*
***/ 
int Pore_delete_val(int time, int val)
{
    struct Pore *target;
    
    /* Get a pointer to the pore we want to delete */
    if (Debug) {
        printf("\nTrying to find the pore with val = %d... ",val);
        fflush(stdout);
    }
    target = Pore_find_val(val);
    if (Debug) {
        printf("found value %d",(target)->ns);
        fflush(stdout);
    }

    if (Pore_head == NULL) {
        printf("\nSorry, Pore_head is NULL in Pore_delete_val");
        fflush(stdout);
        return(1);
    }

    if (target == NULL) {
        printf("\nSorry, target is NULL in Pore_delete_val");
        fflush(stdout);
        return(1);
    }

    /* If element to be deleted is the head element */
    if (Pore_head == target) {
        Pore_head = target->next;
    }

    /* If element to be deleted is the tail element */
    if (Pore_tail == target) {
        Pore_tail = target->prev;
    }

    /* Change next only if element to be deleted is NOT the last one */
    if (target->next != NULL) {
        target->next->prev = target->prev;
    }

    /* Change prev only if element to be deleted is NOT the first one */
    if (target->prev != NULL) {
        target->prev->next = target->next;
    }

    /* Finally, free the memory occupied by target */
    free(target);

    return(0);
}

/***
*    Pore_display
*
*    Displays entire doubly linked list of pore voxel positions
*
*    Arguments:  None
*    Returns:    int status (0 is okay)
*
*    Called by:  genparticles
*
***/
int Pore_display(void)
{
    int idx = 0;
    struct Pore *temp = Pore_head;

    printf("\nBEGIN LIST:");
    while (temp != NULL) {
        printf("\n\tElement[%d] = %d, radius = %d",idx,temp->ns,temp->radius);
        fflush(stdout);
        temp = temp->next;
        idx++;
    }
    printf("\nEND LIST\n");
    fflush(stdout);
    return (0);
}

/***
*    Pore_length
*
*    Get the length of the doubly linked list
*
*    Arguments:  None
*    Returns:    Number of elements in the list
*
*    Called by:  genparticles
*
***/
int Pore_length(void)
{
    int length = 0;
    struct Pore *temp = Pore_head;

    while (temp != NULL) {
        length++;
        temp = temp->next;
    }
    return length;
}

/***
*    Pore_delete
*
*    Delete entire doubly linked list of pore voxel positions
*
*    Arguments:  None
*    Returns:    int status (0 is okay)
*
*    Called by:  genparticles
*
***/
int Pore_delete(void)
{
    struct Pore *temp;

    if (Verbose) {
        printf("\nIn Pore_delete... ");
        fflush(stdout);
    }
    if (Pore_head == NULL) {
        if (Verbose) printf("\n\nList is already deleted.\n");
        return (0);
    }

    /* Element to be deleted is the head element */
    do {
        temp = Pore_head;
        if (Debug) {
            printf("\n\t***** Deleting pore %d...",temp->ns);
            fflush(stdout);
        }
        Pore_head = Pore_head->next;
        free(temp);
        if (Debug) {
            printf("Done!");
            fflush(stdout);
        }
    } while (Pore_head != NULL);

    if (Debug) {
        if (Pore_head != NULL) {
            printf("\nUh-oh.  Pore_head should be NULL but is not!");
            fflush(stdout);
        } else {
            printf(" Done!");
            fflush(stdout);
        }
    }
    return (0);
}

/* Functions for merge sorting */
/***
*    max
*
*    Return the maximum of two integers
*
*    Arguments: x and y are two integers to compare
*    Returns:    maximum of the two integers
*
*    Calls: Nothing
*    Called by: merge_helper
***/
int max(int x, int y)
{
    if (x > y) {
        return x;
    } else {
        return y;
    }
}

/***
*    min
*
*    Return the minimum of two integers
*
*    Arguments: x and y are two integers to compare
*    Returns:    minimum of the two integers
*
*    Calls: Nothing
*    Called by: merge_helper
***/
int min(int x, int y)
{
    if (x < y) {
        return x;
    } else {
        return y;
    }
}

/***
*    mergeSort
*
*    Sets up an iterative merge sort of a doubly linked list.  The list is
*    first copied into an array called copy, and enough memory is
*    also allocated to a scratch array of the same size.
*
*    When the sorting is done, the sorted list is stored in the copy
*    array, so we use it to re-generate the doubly linked list.
*
*    Arguments: None
*
*    Returns:   0 if okay, nonzero otherwise
*
*    Calls: merge
*    Called by: Pore_create_porelist
***/
int mergeSort(void)
{
    int rght, left, rend, length;
    int i,j,k,m;
    int val, rad;
    struct Pore *copy, *scratch, *temp;
    
    length = Pore_length();

    /* Allocate memory for copy of pore list and for scratch list */

    copy = (struct Pore*)malloc(length * sizeof(struct Pore));
    if (!copy) {
        return(MEMERR);
    }

    scratch = (struct Pore*)malloc(length * sizeof(struct Pore));
    if (!scratch) {
        free(copy);
        return(MEMERR);
    }

    /* Load current pore list into copy */

    i = 0;
    temp = Pore_head;
    while (i < length && temp != NULL) {
        copy[i].ns = temp->ns;
        copy[i].radius = temp->radius;
        temp = temp->next;
        i++;
    }

    /* Sort the copy list from lowest radius to highest */
    /* We will reverse the order when we put it back into the Pore list */

    for (k = 1; k < length; k *= 2) { 
        for (left = 0; left + k < length; left += (k*2)) {
            rght = left + k;
            rend = rght + k;
            if (rend > length) rend = length;
            m = left;
            i = left;
            j = rght;
            while (i < rght && j < rend) {
                if (copy[i].radius <= copy[j].radius) {
                    scratch[m] = copy[i];
                    i++;
                } else {
                    scratch[m] = copy[j];
                    j++;
                }
                m++;
            }
            while (i < rght) {
               scratch[m] = copy[i];
               i++;
               m++;
            }
            while (j < rend) {
                scratch[m] = copy[j];
                j++;
                m++;
            }
            for (m = left; m < rend; m++) {
                copy[m] = scratch[m];
            }
        }
    }

    Pore_delete();

    /* Now the list is sorted into the copy list */
    /* Remake the Pore list in reverse order */

    for (i = 0; i < length; i++) {
        val = copy[i].ns;
        rad = copy[i].radius;
        if (Pore_push(val,rad)) {
             printf("\nError: Had trouble pushing %d",val);
             fflush(stdout);
             return (MEMERR);
        }
    }

    /* Now free the allocated memory */

    free(scratch);
    free(copy);

    return(0);
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
void freeallmem(void)
{
    if (Agg.val) free_Int3darray(&Agg);
    if (Pagg.val) free_Int3darray(&Pagg);
    if (Bbox.val) free_Int3darray(&Bbox);
    if (Particle) free_particlepointervector(Particle);
    if (Xg) free_fvector(Xg);
    if (Wg) free_fvector(Wg);
    if (Y) free_complexmatrix(Y, (long)0, (long)Nnn, (long)(-Nnn), (long)(Nnn));
    if (A) free_complexmatrix(A, (long)0, (long)Nnn, (long)(-Nnn), (long)(Nnn));

    return;
}
