/************************  elastic.c ***************************************/
/* BACKGROUND                                                              */
/* This is a control program to call cpelas.c (see below) and then, when   */
/* that program is finished, to pass control to concelas.c (see below) to  */
/* calculate concrete elastic properties and compressive strength          */
/*                                                                         */
/* Programmer:  Dr. Jeffrey W. Bullard (NIST/BFRL)- (301)975.5725          */
/*                                                                         */
/***************************************************************************/
/* **********************  cpelas.c  ************************************** */
/* BACKGROUND                                                               */
/* Programmer: Dr. Edward J. Garboczi (NIST/BFRL)- (301)975-6708            */
/* C conversion by: Dale P. Bentz (NIST) (301)975-5865                      */
/* C conversion performed: 12/01                                            */

/* This program solves the linear elastic equations in a                    */
/* random linear elastic material, subject to an applied macroscopic strain,*/
/* using the finite element method.  Each pixel in the 3-D digital          */
/* image is a cubic tri-linear finite element,  having its own              */
/* elastic moduli tensor. Periodic boundary conditions are maintained.      */
/* In the comments below, (USER) means that this is a section of code that  */
/* the user might have to change for his particular problem. Therefore the  */
/* user is encouraged to search for this string.                            */

/* PROBLEM AND VARIABLE DEFINITION                                          */

/* The problem being solved is the minimization of the energy               */
/* 1/2 uAu + b u + C, where A is the Hessian matrix composed of the         */
/* stiffness matrices (dk) for each pixel/element, b is a constant vector   */
/* and C is a constant that are determined by the applied strain and        */
/* the periodic boundary conditions, and u is a vector of                   */
/* all the displacements. The solution                                      */
/* method used is the conjugate gradient relaxation algorithm.              */
/* Other variables are:  gb is the gradient = Au+b, h is an                 */
/* auxiliary variable used in the conjugate gradient algorithm (in dembx),  */
/* dk(n,i,j) is the stiffness matrix of the n'th phase, cmod(n,i,j) is      */
/* the elastic moduli tensor of the n'th phase, pix is a vector that gives  */
/* the phase label of each pixel, ib is a matrix that gives the labels of   */
/* the 27 (counting itself) neighbors of a given node, prob is the volume   */
/* fractions of the various phases,                                         */
/* strxx, stryy, strzz, strxz, stryz, and strxy are the six Voigt           */
/* volume averaged total stresses, and                                      */
/* sxx, syy, szz, sxz, syz, and sxy are the six Voigt                       */
/* volume averaged total strains.                                           */

/* DIMENSIONS                                                               */

/* The vectors u,gb,b, and h are dimensioned to be the system size,         */
/* ns=nx*ny*nz, with three components, where the digital image of the       */
/* microstructure considered is a rectangular paralleliped, nx x ny x nz    */
/* in size.  The arrays pix and ib are are also dimensioned to the system   */
/* size.  The array ib has 27 components, for the 27 neighbors of a node.   */
/* Note that the program is set up at present to have at most 50            */
/* different phases.  This can easily be changed, simply by changing        */
/* the dimensions of dk, prob, and cmod. The parameter nphase gives the     */
/* number of phases being considered in the problem.                        */
/* All arrays are passed between subroutines using simple common statements.*/
/* In the C version, these arrays are declared static and global            */
/*                                                                          */
/* MODIFICATIONS:                                                           */
/*                                                                          */
/* 13 September 2004:  Added changes to allow calculations on individual    */
/*                     layers in the interfacial transition zone adjacent   */
/*                     to an aggregate slab.                                */
/*                                                                          */
/*                     Added moduli data for K2SO4 and NA2SO4               */
/*                                                                          */
/* STRONGLY SUGGESTED:  READ THE MANUAL BEFORE USING PROGRAM!!              */
/* Manual available at NISTIR 6269 from NTIS or at:                         */
/*           http://ciks.cbt.nist.gov/~garbocz/manual/man.html              */

#include "include/vcctl.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* (USER) Change these dimensions - e.g., NX, NY, and NZ                    */
#define NX DEFAULTSYSTEMSIZE
#define NY DEFAULTSYSTEMSIZE
#define NZ DEFAULTSYSTEMSIZE

#define NDIM 3     /* number of dimensions for problem - 3-D */
#define NSP OFFSET /* maximum number of phases */

/* Defines for concelas function */
#define RKITS 799
#define SHAPEFACTOR 1.10
#define MAXSIZECLASSES 500
#define MAXAGGTYPES 4
#define NUMFINESOURCES 2
#define NUMCOARSESOURCES 2

/* Global variables for cpelas */

char Outfolder[MAXSTRING];
char Outfilename[MAXSTRING], PCfilename[MAXSTRING], Layerfilename[MAXSTRING];
char Filesep;
double **u, **gb, **b, **h;
double ***Aa, **A, **Vv, ***A1, *K, *G, **Cc;
double cmod[NSP][6][6], dk[NSP][8][3][8][3];
double phasemod[NSP][2], prob[NSP], gg = 0.0, gtest = 0.0;
short int in[27], jjn[27], kn[27];
int **ib;
short int *pix, *part;

double strxx, stryy, strzz, strxz, stryz, strxy;
double exx, eyy, ezz, exz, eyz, exy;
double stressall[NSP][16];
double C;
double sxx, syy, szz, sxz, syz, sxy;

/* Variables for ITZ calculations */
double sxxt, syyt, szzt, sxzt, syzt, sxyt;
double strxxt, stryyt, strzzt, strxzt, stryzt, strxyt;

int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
int Syspix;
float Res = DEFAULTRESOLUTION;
/* VCCTL software version used to create input file */
float Version;

/***
 *	Flag to determine whether to break connections between
 *	anhydrous particles
 ***/
int Sever;

/***
 *	Tiny number that sets the minimum volume fraction
 *	possible for a phase
 ***/
double pthresh;

/* Global variables for concelas */

double K_concelas[MAXSIZECLASSES];
double G_concelas[MAXSIZECLASSES];
double Ki_concelas[MAXSIZECLASSES];
double Gi_concelas[MAXSIZECLASSES];
double Diam_concelas[MAXSIZECLASSES];
double Vf_concelas[MAXSIZECLASSES];
int N_concelas;

/* Information for progress file (for taskbar functionality */

char Progfilename[MAXSTRING];
FILE *Fprog;

/* Function declarations for concelas */

int concelas(int nagg1, double bulkmod, double shearmod);
void freallmem_concelas(void);
void effective(double itzwidth, double kitz, double gitz);
void slope(double *kk, double *gg, double k, double g);

/* Freeallmem frees all dynamically allocated memory */

void freeallmem(void) {
  if (u)
    free_drect(u, Syspix);
  if (gb)
    free_drect(gb, Syspix);
  if (b)
    free_drect(b, Syspix);
  if (h)
    free_drect(h, Syspix);
  if (ib)
    free_irect(ib, Syspix);
  if (pix)
    free_sivector(pix);
  if (part)
    free_sivector(part);
  if (Aa)
    free_dbox(Aa, Xsyssize, 36);
  if (A)
    free_drect(A, 36);
  if (Vv)
    free_drect(Vv, Xsyssize);
  if (A1)
    free_dbox(A1, Xsyssize, 36);
  if (Cc)
    free_drect(Cc, 6);
  if (K)
    free_dvector(K);
  if (G)
    free_dvector(G);

  return;
}

/*  Subroutine that sets up microstructural image */
void ppixel(int nphase, int *doitz, int *nagg1) {
  int nxy, nx, ny, nz, i, j, k, inval, oinval;
  int foundagg;
  int m, m1, m2, count;
  FILE *infile, *pinfile;
  char filein[MAXSTRING], pfilein[MAXSTRING], buff[MAXSTRING],
      instring[MAXSTRING];
  FILE *fpout;

  /* Get user input for filename to read in microstructure */
  printf("Enter full path and name of file with input microstructure: ");
  read_string(filein, sizeof(filein));
  printf("\n%s\n", filein);

  /* Determine the separator character */

  printf("Enter whether to break connections between\n");
  printf("anhydrous cement particles (1) or not (0): ");
  read_string(buff, sizeof(buff));
  /* Sever = atoi(buff); */
  Sever = 1;
  printf("\n%d (set automatically, not your fault.\n", Sever);
  printf("ITZ Calculation? (1 for Yes, 0 for No): ");
  read_string(buff, sizeof(buff));
  *doitz = atoi(buff);
  printf("\n%d\n", *doitz);
  fflush(stdout);
  printf("Enter name of folder to output data files");
  printf("\n(Include final separator in path) ");
  read_string(Outfolder, sizeof(Outfolder));
  Filesep = Outfolder[strlen(Outfolder) - 1];
  if ((Filesep != '/') && (Filesep != '\\')) {
    printf("\nNo final file separator detected.  Using /");
    Filesep = '/';
  }
  printf("\n%s\n", Outfolder);
  printf("Enter fully resolved name of file to output calculated effective "
         "moduli: ");
  sprintf(Outfilename, "%sEffectiveModuli.dat", Outfolder);
  printf("\nEffective elastic moduli will be printed to file %s\n",
         Outfilename);
  sprintf(PCfilename, "%sPhaseContributions.dat", Outfolder);
  printf("\nRelative phase contributions will be printed to file %s\n",
         PCfilename);
  if (*doitz) {
    sprintf(Layerfilename, "%sITZmoduli.dat", Outfolder);
    printf("\nEffective moduli as function of distance normal to");
    printf("\n\taggregate surface will be printed to file %s\n", Layerfilename);
  }
  infile = filehandler("cpelas", filein, "READ");
  if (!infile) {
    freeallmem();
    exit(1);
  }

  /****
   *	NOTE:  MUST READ
   *			(1) VCCTL VERSION NUMBER (Version)
   *			(1) SYSTEM SIZE (Xsyssize,Ysyssize,Zsyssize)
   *			(2) SYSTEM RESOLUTION (Res)
   *
   ****/

  if (read_imgheader(infile, &Version, &Xsyssize, &Ysyssize, &Zsyssize, &Res)) {
    fclose(infile);
    bailout("cpelas", "Error reading image header");
    freeallmem();
    exit(1);
  }

  Syspix = Xsyssize * Ysyssize * Zsyssize;

  printf("\nSyspix = %d", Syspix);
  fflush(stdout);

  nx = Xsyssize;
  ny = Ysyssize;
  nz = Zsyssize;

  *nagg1 = Xsyssize;

  /***
   *	Allocate arrays dynamically based on system size
   ***/

  u = NULL;
  gb = NULL;
  b = NULL;
  h = NULL;
  ib = NULL;
  pix = NULL;
  part = NULL;

  u = drect(Syspix, 3);
  gb = drect(Syspix, 3);
  b = drect(Syspix, 3);
  h = drect(Syspix, 3);
  ib = irect(Syspix, 27);
  pix = sivector(Syspix);
  part = sivector(Syspix);

  if (!u || !gb || !b || !h || !ib || !pix || !part) {
    freeallmem();
    bailout("cpelas", "Memory allocation failure");
    fflush(stdout);
    exit(1);
  }

  Vv = NULL;
  Aa = NULL;
  A = NULL;
  A1 = NULL;
  K = NULL;
  G = NULL;
  Cc = NULL;
  if (doitz) {
    Vv = drect(Xsyssize, 36);
    Aa = dbox(Xsyssize, 36, 36);
    A = drect(36, 37);
    A1 = dbox(Xsyssize, 36, 36);
    K = dvector(Xsyssize);
    G = dvector(Xsyssize);
    Cc = drect(6, 6);

    if (!Vv || !Aa || !A || !A1 || !K || !G || !Cc) {
      freeallmem();
      bailout("cpelas", "Memory allocation failure");
      fflush(stdout);
      exit(1);
    }
  }

  pthresh = 1.0 / ((double)(Syspix));

  /*  (USER)  If you want to set up a test image inside the program, instead of
   */
  /*  reading it in from a file, this should be done inside this subroutine. */

  printf("\nReading image file now... ");
  fflush(stdout);
  foundagg = 0;
  count = 0;
  nxy = Xsyssize * Ysyssize;
  for (k = 0; k < Zsyssize; k++) {
    m1 = k * nxy;
    for (j = 0; j < Ysyssize; j++) {
      m2 = j * Xsyssize;
      for (i = 0; i < Xsyssize; i++) {
        m = m1 + m2 + i;
        fscanf(infile, "%s", instring);
        oinval = atoi(instring);
        inval = convert_id(oinval, Version);
        if (inval == C3S)
          count++;
        pix[m] = inval;

        /***
         *	Check for presence of aggregate, which will
         *	launch a separate ITZ calculation after the
         *	moduli are calculated
         ***/

        if (inval == INERTAGG) {
          foundagg = 1;

          /***
           *	VCCTL forces aggregate to be in yz plane when
           *	microstructure is created
           ***/

          if (i < *nagg1)
            *nagg1 = i;
        }

        if ((inval < 0) || (inval > NSP)) {
          sprintf(buff, "Phase label in pix has value of %d", inval);
          bailout("cpelas", buff);
          fflush(stdout);
          exit(1);
        }
      }
    }
  }

  fclose(infile);
  printf(" done.  Count of C3S = %d\n", count);
  fflush(stdout);

  count = 0;
  for (m = 0; m < Xsyssize * Ysyssize * Zsyssize; m++) {
    if (pix[m] == C3S)
      count++;
  }

  printf("Now using pix, Count of C3S = %d\n", count);
  fflush(stdout);

  if (!foundagg)
    *nagg1 = (Xsyssize / 2);

  printf("nagg1 = %d\n", *nagg1);
  fflush(stdout);
  /* Get user input for filename to read in particle ids */
  printf("Enter name of file with particle ids \n");
  read_string(pfilein, sizeof(pfilein));
  printf("%s\n", pfilein);
  fflush(stdout);
  if (Sever) {
    pinfile = filehandler("cpelas", pfilein, "READ");
    if (!pinfile) {
      freeallmem();
      exit(1);
    }
    if (breakflocs(pinfile, pix, part, in, jjn, kn, Xsyssize, Ysyssize,
                   Zsyssize, Version, Res)) {
      fclose(pinfile);
      exit(1);
    }
    fclose(pinfile);
  }
  count = 0;
  for (m = 0; m < Xsyssize * Ysyssize * Zsyssize; m++) {
    if (pix[m] == C3S)
      count++;
  }
  printf("After breakflocs, Count of C3S = %d\n", count);
  fflush(stdout);

  fpout = fopen("newcem.img", "w");
  fprintf(fpout, "Version: 7.0\n");
  fprintf(fpout, "X_Size: %d\n", Xsyssize);
  fprintf(fpout, "Y_Size: %d\n", Ysyssize);
  fprintf(fpout, "Z_Size: %d\n", Zsyssize);
  fprintf(fpout, "Image_Resolution: 1.00\n");
  for (m = 0; m < Xsyssize * Ysyssize * Zsyssize; m++) {
    fprintf(fpout, "%d\n", pix[m]);
  }
  fclose(fpout);
}

/*  Subroutine assig that counts volume fractions */

void assig(int ns, int nphase) {
  int i;
  int m, count;

  /* Zero out the phase volume fractions */
  for (i = 0; i < nphase; i++) {
    prob[i] = 0.0;
  }

  /* Process each pixel in turn and accumulate volume counts */
  count = 0;
  for (m = 0; m < ns; m++) {
    prob[pix[m]] += 1;
    if (pix[m] == C3S)
      count++;
  }

  printf("\nNumber of %d pixels found is %f or %d", C3S, prob[C3S], count);
  printf("\nns = %d, so vfrac[%d] = %f", ns, C3S, (prob[C3S] / ((double)ns)));
  fflush(stdout);
  /* Convert from phase count to volume fraction */
  for (i = 0; i < nphase; i++) {
    prob[i] /= (double)ns;
  }
}

/*  Subroutine that sets up the elastic moduli variables,  */
/*  the stiffness matrices,dk, the linear term in */
/*  displacements, b, and the constant term, C, that appear in the total energy
 */
/*  due to the periodic boundary conditions */

void femat(int nx, int ny, int nz, int ns, int nphase) {

  double dndx[8], dndy[8], dndz[8], cmu[6][6], ck[6][6], g[3][3][3];
  double es[6][8][3], delta[8][3], cumtot = 0.0;
  register double sum, sum1, sum2;
  float x, y, z;
  int is[8], m, l, k, j, i, ijk, n1, n2, n3, n, mm, nn, ii, jj, ll, kk, i3, i8,
      m8, m4, nxy;
  int m3;

  nxy = nx * ny;

  /*  (USER) NOTE:  complete elastic modulus matrix is used, so an anisotropic
   */
  /*  matrix could be directly input at any point, since program is written  */
  /*  to use a general elastic moduli tensor, but is only explicitly  */
  /*  implemented for isotropic materials. */

  /*  initialize stiffness matrices */
  for (m = 0; m < nphase; m++) {
    for (i = 0; i < 8; i++) {
      for (k = 0; k < 3; k++) {
        for (j = 0; j < 8; j++) {
          for (l = 0; l < 3; l++) {
            dk[m][i][k][j][l] = 0.0;
          }
        }
      }
    }
  }

  /* set up elastic moduli matrices for each kind of element */
  /*  ck and cmu are the bulk and shear modulus matrices, which need to be */
  /*  weighted by the actual bulk and shear moduli */

  for (i = 0; i < 6; i++) {
    for (j = 0; j < 6; j++) {
      ck[i][j] = 0.0;
      cmu[i][j] = 0.0;
    }
  }
  ck[0][0] = 1.0;
  ck[0][1] = 1.0;
  ck[0][2] = 1.0;
  ck[1][0] = 1.0;
  ck[1][1] = 1.0;
  ck[1][2] = 1.0;
  ck[2][0] = 1.0;
  ck[2][1] = 1.0;
  ck[2][2] = 1.0;

  cmu[0][0] = 4.0 / 3.0;
  cmu[0][1] = (-2.0) / 3.0;
  cmu[0][2] = (-2.0) / 3.0;
  cmu[1][0] = (-2.0) / 3.0;
  cmu[1][1] = 4.0 / 3.0;
  cmu[1][2] = (-2.0) / 3.0;
  cmu[2][0] = (-2.0) / 3.0;
  cmu[2][1] = (-2.0) / 3.0;
  cmu[2][2] = 4.0 / 3.0;
  cmu[3][3] = 1.0;
  cmu[4][4] = 1.0;
  cmu[5][5] = 1.0;

  for (k = 0; k < nphase; k++) {
    for (i = 0; i < 6; i++) {
      for (j = 0; j < 6; j++) {
        cmod[k][i][j] = phasemod[k][0] * ck[i][j] + phasemod[k][1] * cmu[i][j];
      }
    }
  }

  /*  set up Simpson's integration rule weight vector */
  for (i = 0; i < 3; i++) {
    for (j = 0; j < 3; j++) {
      for (k = 0; k < 3; k++) {
        g[i][j][k] = 1.0;
        if (i == 1) {
          g[i][j][k] *= 4.0;
        }
        if (j == 1) {
          g[i][j][k] *= 4.0;
        }
        if (k == 1) {
          g[i][j][k] *= 4.0;
        }
      }
    }
  }

  /*  loop over the nphase kinds of pixels and Simpson's rule quadrature */
  /*  points in order to compute the stiffness matrices.  Stiffness matrices */
  /*  of trilinear finite elements are quadratic in x, y, and z, so that */
  /*  Simpson's rule quadrature gives exact results. */

  for (ijk = 0; ijk < nphase; ijk++) {
    for (k = 0; k < 3; k++) {
      for (j = 0; j < 3; j++) {
        for (i = 0; i < 3; i++) {
          x = (float)(i) / 2.0;
          y = (float)(j) / 2.0;
          z = (float)(k) / 2.0;
          /*  dndx means the negative derivative, with respect to x, of the
           * shape */
          /*  matrix N (see manual, Sec. 2.2), dndy, and dndz are similar. */
          dndx[0] = (-(1.0 - y)) * (1.0 - z);
          dndx[1] = (1.0 - y) * (1.0 - z);
          dndx[2] = y * (1.0 - z);
          dndx[3] = (-y) * (1.0 - z);
          dndx[4] = (-(1.0 - y)) * z;
          dndx[5] = (1.0 - y) * z;
          dndx[6] = y * z;
          dndx[7] = (-y) * z;
          dndy[0] = (-(1.0 - x)) * (1.0 - z);
          dndy[1] = (-x) * (1.0 - z);
          dndy[2] = x * (1.0 - z);
          dndy[3] = (1.0 - x) * (1.0 - z);
          dndy[4] = (-(1.0 - x)) * z;
          dndy[5] = (-x) * z;
          dndy[6] = x * z;
          dndy[7] = (1.0 - x) * z;
          dndz[0] = (-(1.0 - x)) * (1.0 - y);
          dndz[1] = (-x) * (1.0 - y);
          dndz[2] = (-x) * y;
          dndz[3] = (-(1.0 - x)) * y;
          dndz[4] = (1.0 - x) * (1.0 - y);
          dndz[5] = x * (1.0 - y);
          dndz[6] = x * y;
          dndz[7] = (1.0 - x) * y;

          /*  now build strain matrix */
          for (n1 = 0; n1 < 6; n1++) {
            for (n2 = 0; n2 < 8; n2++) {
              for (n3 = 0; n3 < 3; n3++) {
                es[n1][n2][n3] = 0.0;
              }
            }
          }

          for (n = 0; n < 8; n++) {
            es[0][n][0] = dndx[n];
            es[1][n][1] = dndy[n];
            es[2][n][2] = dndz[n];
            es[3][n][0] = dndz[n];
            es[3][n][2] = dndx[n];
            es[4][n][1] = dndz[n];
            es[4][n][2] = dndy[n];
            es[5][n][0] = dndy[n];
            es[5][n][1] = dndx[n];
          }
          sum2 = g[i][j][k];
          /*  Matrix multiply to determine value at (x,y,z), multiply by */
          /*  proper weight, and sum into dk, the stiffness matrix */
          for (ii = 0; ii < 8; ii++) {
            for (mm = 0; mm < 3; mm++) {
              for (jj = 0; jj < 8; jj++) {
                for (nn = 0; nn < 3; nn++) {

                  /*  Define sum over strain matrices and elastic moduli matrix
                   * for */
                  /*  stiffness matrix */
                  sum = 0.0;
                  for (kk = 0; kk < 6; kk++) {
                    sum1 = es[kk][ii][mm];
                    for (ll = 0; ll < 6; ll++) {
                      sum += sum1 * cmod[ijk][kk][ll] * es[ll][jj][nn];
                    }
                  }
                  dk[ijk][ii][mm][jj][nn] += sum2 * sum / 216.;
                  cumtot += sum2 * sum / 216.;
                }
              }
            }
          }
        }
      }
    }
  }
  /*  Set up vector for linear term, b, and constant term, C, */
  /*  in the elastic energy.  This is done using the stiffness matrices, */
  /*  and the periodic terms in the applied strain that come in at the  */
  /*  boundary pixels via the periodic boundary conditions and the  */
  /*  condition that an applied macroscopic strain exists (see Sec. 2.2  */
  /*  in the manual). It is easier to set b up this way than to analytically */
  /*  write out all the terms involved. */

  /*  Initialize b and C */
  for (m3 = 0; m3 < ns; m3++) {
    for (m = 0; m < 3; m++) {
      b[m3][m] = 0.0;
    }
  }
  C = 0.0;

  /*  For all cases, the correspondence between 1-8 finite element node */
  /*  labels and 1-27 neighbor labels is (see Table 4 in manual):   */
  /*  1:ib(m,27), 2:ib(m,3), */
  /*  3:ib(m,2),4:ib(m,1), */
  /*  5:ib(m,26),6:ib(m,19) */
  /*  7:ib(m,18),8:ib(m,17)  */
  /*  In C version, all indices begin at 0, so 1 was subtracted from all */
  /*    values given in original Fortran code 11/27/01  */
  is[0] = 26;
  is[1] = 2;
  is[2] = 1;
  is[3] = 0;
  is[4] = 25;
  is[5] = 18;
  is[6] = 17;
  is[7] = 16;

  /*  x=nx face */
  for (i8 = 0; i8 < 8; i8++) {
    for (i3 = 0; i3 < 3; i3++) {
      delta[i8][i3] = 0.0;
    }
  }

  for (i8 = 1; i8 < 7; i8++) {
    if ((i8 == 1) || (i8 == 2) || (i8 == 5) || (i8 == 6)) {
      delta[i8][0] = exx * (double)nx;
      delta[i8][1] = exy * (double)nx;
      delta[i8][2] = exz * (double)nx;
    }
  }

  for (j = 1; j <= (ny - 1); j++) {
    for (k = 0; k < (nz - 1); k++) {
      m = nxy * k + j * nx - 1;
      for (nn = 0; nn < 3; nn++) {
        for (mm = 0; mm < 8; mm++) {
          sum = 0.0;
          for (m4 = 0; m4 < 3; m4++) {
            for (m8 = 0; m8 < 8; m8++) {
              sum += delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn];
              C += 0.5 * delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn] *
                   delta[mm][nn];
            }
          }
          b[ib[m][is[mm]]][nn] += sum;
        }
      }
    }
  }

  /*  y=ny face */
  for (i3 = 0; i3 < 3; i3++) {
    for (i8 = 0; i8 < 8; i8++) {
      delta[i8][i3] = 0.0;
    }
  }

  for (i8 = 2; i8 < 8; i8++) {
    if ((i8 == 2) || (i8 == 3) || (i8 == 6) || (i8 == 7)) {
      delta[i8][0] = exy * (double)ny;
      delta[i8][1] = eyy * (double)ny;
      delta[i8][2] = eyz * (double)ny;
    }
  }

  for (i = 0; i < (nx - 1); i++) {
    for (k = 0; k < (nz - 1); k++) {
      m = nxy * k + nx * (ny - 1) + i;
      for (nn = 0; nn < 3; nn++) {
        for (mm = 0; mm < 8; mm++) {
          sum = 0.0;
          for (m4 = 0; m4 < 3; m4++) {
            for (m8 = 0; m8 < 8; m8++) {
              sum += delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn];
              C += 0.5 * delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn] *
                   delta[mm][nn];
            }
          }
          b[ib[m][is[mm]]][nn] += sum;
        }
      }
    }
  }

  /*  z=nz face */
  for (i3 = 0; i3 < 3; i3++) {
    for (i8 = 0; i8 < 8; i8++) {
      delta[i8][i3] = 0.0;
    }
  }
  for (i8 = 4; i8 < 8; i8++) {
    delta[i8][0] = exz * (double)nz;
    delta[i8][1] = eyz * (double)nz;
    delta[i8][2] = ezz * (double)nz;
  }

  for (i = 0; i < (nx - 1); i++) {
    for (j = 0; j < (ny - 1); j++) {
      m = nxy * (nz - 1) + nx * j + i;
      for (nn = 0; nn < 3; nn++) {
        for (mm = 0; mm < 8; mm++) {
          sum = 0.0;
          for (m4 = 0; m4 < 3; m4++) {
            for (m8 = 0; m8 < 8; m8++) {
              sum += delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn];
              C += 0.5 * delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn] *
                   delta[mm][nn];
            }
          }
          b[ib[m][is[mm]]][nn] += sum;
        }
      }
    }
  }

  /*  x=nx y=ny edge  */
  for (i3 = 0; i3 < 3; i3++) {
    for (i8 = 0; i8 < 8; i8++) {
      delta[i8][i3] = 0.0;
    }
  }
  for (i8 = 1; i8 < 8; i8++) {
    if ((i8 == 1) || (i8 == 5)) {
      delta[i8][0] = exx * (double)nx;
      delta[i8][1] = exy * (double)nx;
      delta[i8][2] = exz * (double)nx;
    }
    if ((i8 == 3) || (i8 == 7)) {
      delta[i8][0] = exy * (double)ny;
      delta[i8][1] = eyy * (double)ny;
      delta[i8][2] = eyz * (double)ny;
    }
    if ((i8 == 2) || (i8 == 6)) {
      delta[i8][0] = exy * (double)ny + exx * (double)nx;
      delta[i8][1] = eyy * (double)ny + exy * (double)nx;
      delta[i8][2] = eyz * (double)ny + exz * (double)nx;
    }
  }

  for (k = 1; k <= (nz - 1); k++) {
    m = nxy * k - 1;
    for (nn = 0; nn < 3; nn++) {
      for (mm = 0; mm < 8; mm++) {
        sum = 0.0;
        for (m4 = 0; m4 < 3; m4++) {
          for (m8 = 0; m8 < 8; m8++) {
            sum += delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn];
            C += 0.5 * delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn] *
                 delta[mm][nn];
          }
        }
        b[ib[m][is[mm]]][nn] += sum;
      }
    }
  }

  /*  x=nx z=nz edge  */
  for (i3 = 0; i3 < 3; i3++) {
    for (i8 = 0; i8 < 8; i8++) {
      delta[i8][i3] = 0.0;
    }
  }
  for (i8 = 1; i8 < 8; i8++) {
    if ((i8 == 1) || (i8 == 2)) {
      delta[i8][0] = exx * (double)nx;
      delta[i8][1] = exy * (double)nx;
      delta[i8][2] = exz * (double)nx;
    }
    if ((i8 == 4) || (i8 == 7)) {
      delta[i8][0] = exz * (double)nz;
      delta[i8][1] = eyz * (double)nz;
      delta[i8][2] = ezz * (double)nz;
    }
    if ((i8 == 5) || (i8 == 6)) {
      delta[i8][0] = exz * (double)nz + exx * (double)nx;
      delta[i8][1] = eyz * (double)nz + exy * (double)nx;
      delta[i8][2] = ezz * (double)nz + exz * (double)nx;
    }
  }

  for (j = 0; j < (ny - 1); j++) {
    m = nxy * (nz - 1) + nx * j + nx - 1;
    for (nn = 0; nn < 3; nn++) {
      for (mm = 0; mm < 8; mm++) {
        sum = 0.0;
        for (m4 = 0; m4 < 3; m4++) {
          for (m8 = 0; m8 < 8; m8++) {
            sum += delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn];
            C += 0.5 * delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn] *
                 delta[mm][nn];
          }
        }
        b[ib[m][is[mm]]][nn] += sum;
      }
    }
  }

  /*  y=ny z=nz edge  */
  for (i3 = 0; i3 < 3; i3++) {
    for (i8 = 0; i8 < 8; i8++) {
      delta[i8][i3] = 0.0;
    }
  }
  for (i8 = 4; i8 < 8; i8++) {
    if ((i8 == 4) || (i8 == 5)) {
      delta[i8][0] = exz * (double)nz;
      delta[i8][1] = eyz * (double)nz;
      delta[i8][2] = ezz * (double)nz;
    }
    if ((i8 == 6) || (i8 == 7)) {
      delta[i8][0] = exy * (double)ny + exz * (double)nz;
      delta[i8][1] = eyy * (double)ny + eyz * (double)nz;
      delta[i8][2] = eyz * (double)ny + ezz * (double)nz;
    }
  }

  for (i = 0; i < (nx - 1); i++) {
    m = nxy * (nz - 1) + nx * (ny - 1) + i;
    for (nn = 0; nn < 3; nn++) {
      for (mm = 0; mm < 8; mm++) {
        sum = 0.0;
        for (m4 = 0; m4 < 3; m4++) {
          for (m8 = 0; m8 < 8; m8++) {
            sum += delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn];
            C += 0.5 * delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn] *
                 delta[mm][nn];
          }
        }
        b[ib[m][is[mm]]][nn] += sum;
      }
    }
  }
  /* c  x=nx y=ny z=nz corner  */
  for (i3 = 0; i3 < 3; i3++) {
    for (i8 = 0; i8 < 8; i8++) {
      delta[i8][i3] = 0.0;
    }
  }
  for (i8 = 1; i8 < 8; i8++) {
    if (i8 == 1) {
      delta[i8][0] = exx * (double)nx;
      delta[i8][1] = exy * (double)nx;
      delta[i8][2] = exz * (double)nx;
    }
    if (i8 == 3) {
      delta[i8][0] = exy * (double)ny;
      delta[i8][1] = eyy * (double)ny;
      delta[i8][2] = eyz * (double)ny;
    }
    if (i8 == 4) {
      delta[i8][0] = exz * (double)nz;
      delta[i8][1] = eyz * (double)nz;
      delta[i8][2] = ezz * (double)nz;
    }
    if (i8 == 7) {
      delta[i8][0] = exy * (double)ny + exz * (double)nz;
      delta[i8][1] = eyy * (double)ny + eyz * (double)nz;
      delta[i8][2] = eyz * (double)ny + ezz * (double)nz;
    }
    if (i8 == 5) {
      delta[i8][0] = exx * (double)nx + exz * (double)nz;
      delta[i8][1] = exy * (double)nx + eyz * (double)nz;
      delta[i8][2] = exz * (double)nx + ezz * (double)nz;
    }
    if (i8 == 2) {
      delta[i8][0] = exx * (double)nx + exy * (double)ny;
      delta[i8][1] = exy * (double)nx + eyy * (double)ny;
      delta[i8][2] = exz * (double)nx + eyz * (double)ny;
    }
    if (i8 == 6) {
      delta[i8][0] = exx * (double)nx + exy * (double)ny + exz * (double)nz;
      delta[i8][1] = exy * (double)nx + eyy * (double)ny + eyz * (double)nz;
      delta[i8][2] = exz * (double)nx + eyz * (double)ny + ezz * (double)nz;
    }
  }

  m = nx * ny * nz - 1;
  for (nn = 0; nn < 3; nn++) {
    for (mm = 0; mm < 8; mm++) {
      sum = 0.0;
      for (m4 = 0; m4 < 3; m4++) {
        for (m8 = 0; m8 < 8; m8++) {
          sum += delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn];
          C += 0.5 * delta[m8][m4] * dk[pix[m]][m8][m4][mm][nn] * delta[mm][nn];
        }
      }
      b[ib[m][is[mm]]][nn] += sum;
    }
  }
}

/*  Subroutine computes the total energy, utot, and the gradient, gb */

double energy(int nx, int ny, int nz, int ns) {
  int m;
  int m3, j, n;
  double utot = 0.0;

  for (m = 0; m < ns; m++) {
    for (m3 = 0; m3 < 3; m3++) {
      gb[m][m3] = 0.0;
    }
  }

  /*  Do global matrix multiply via small stiffness matrices, gb = A * u */
  /*  The long statement below correctly brings in all the terms from  */
  /*  the global matrix A using only the small stiffness matrices. */
  utot = C;
  for (m = 0; m < ns; m++) {
    for (j = 0; j < 3; j++) {
      for (n = 0; n < 3; n++) {
        gb[m][j] += u[ib[m][0]][n] * (dk[pix[ib[m][26]]][0][j][3][n] +
                                      dk[pix[ib[m][6]]][1][j][2][n] +
                                      dk[pix[ib[m][24]]][4][j][7][n] +
                                      dk[pix[ib[m][14]]][5][j][6][n]) +
                    u[ib[m][1]][n] * (dk[pix[ib[m][26]]][0][j][2][n] +
                                      dk[pix[ib[m][24]]][4][j][6][n]) +
                    u[ib[m][2]][n] * (dk[pix[ib[m][26]]][0][j][1][n] +
                                      dk[pix[ib[m][4]]][3][j][2][n] +
                                      dk[pix[ib[m][12]]][7][j][6][n] +
                                      dk[pix[ib[m][24]]][4][j][5][n]) +
                    u[ib[m][3]][n] * (dk[pix[ib[m][4]]][3][j][1][n] +
                                      dk[pix[ib[m][12]]][7][j][5][n]) +
                    u[ib[m][4]][n] * (dk[pix[ib[m][5]]][2][j][1][n] +
                                      dk[pix[ib[m][4]]][3][j][0][n] +
                                      dk[pix[ib[m][13]]][6][j][5][n] +
                                      dk[pix[ib[m][12]]][7][j][4][n]) +
                    u[ib[m][5]][n] * (dk[pix[ib[m][5]]][2][j][0][n] +
                                      dk[pix[ib[m][13]]][6][j][4][n]) +
                    u[ib[m][6]][n] * (dk[pix[ib[m][5]]][2][j][3][n] +
                                      dk[pix[ib[m][6]]][1][j][0][n] +
                                      dk[pix[ib[m][13]]][6][j][7][n] +
                                      dk[pix[ib[m][14]]][5][j][4][n]) +
                    u[ib[m][7]][n] * (dk[pix[ib[m][6]]][1][j][3][n] +
                                      dk[pix[ib[m][14]]][5][j][7][n]) +
                    u[ib[m][8]][n] * (dk[pix[ib[m][24]]][4][j][3][n] +
                                      dk[pix[ib[m][14]]][5][j][2][n]) +
                    u[ib[m][9]][n] * (dk[pix[ib[m][24]]][4][j][2][n]) +
                    u[ib[m][10]][n] * (dk[pix[ib[m][12]]][7][j][2][n] +
                                       dk[pix[ib[m][24]]][4][j][1][n]) +
                    u[ib[m][11]][n] * (dk[pix[ib[m][12]]][7][j][1][n]) +
                    u[ib[m][12]][n] * (dk[pix[ib[m][12]]][7][j][0][n] +
                                       dk[pix[ib[m][13]]][6][j][1][n]) +
                    u[ib[m][13]][n] * (dk[pix[ib[m][13]]][6][j][0][n]) +
                    u[ib[m][14]][n] * (dk[pix[ib[m][13]]][6][j][3][n] +
                                       dk[pix[ib[m][14]]][5][j][0][n]) +
                    u[ib[m][15]][n] * (dk[pix[ib[m][14]]][5][j][3][n]) +
                    u[ib[m][16]][n] * (dk[pix[ib[m][26]]][0][j][7][n] +
                                       dk[pix[ib[m][6]]][1][j][6][n]) +
                    u[ib[m][17]][n] * (dk[pix[ib[m][26]]][0][j][6][n]) +
                    u[ib[m][18]][n] * (dk[pix[ib[m][26]]][0][j][5][n] +
                                       dk[pix[ib[m][4]]][3][j][6][n]) +
                    u[ib[m][19]][n] * (dk[pix[ib[m][4]]][3][j][5][n]) +
                    u[ib[m][20]][n] * (dk[pix[ib[m][4]]][3][j][4][n] +
                                       dk[pix[ib[m][5]]][2][j][5][n]) +
                    u[ib[m][21]][n] * (dk[pix[ib[m][5]]][2][j][4][n]) +
                    u[ib[m][22]][n] * (dk[pix[ib[m][5]]][2][j][7][n] +
                                       dk[pix[ib[m][6]]][1][j][4][n]) +
                    u[ib[m][23]][n] * (dk[pix[ib[m][6]]][1][j][7][n]) +
                    u[ib[m][24]][n] * (dk[pix[ib[m][13]]][6][j][2][n] +
                                       dk[pix[ib[m][12]]][7][j][3][n] +
                                       dk[pix[ib[m][14]]][5][j][1][n] +
                                       dk[pix[ib[m][24]]][4][j][0][n]) +
                    u[ib[m][25]][n] * (dk[pix[ib[m][5]]][2][j][6][n] +
                                       dk[pix[ib[m][4]]][3][j][7][n] +
                                       dk[pix[ib[m][26]]][0][j][4][n] +
                                       dk[pix[ib[m][6]]][1][j][5][n]) +
                    u[ib[m][26]][n] * (dk[pix[ib[m][26]]][0][j][0][n] +
                                       dk[pix[ib[m][6]]][1][j][1][n] +
                                       dk[pix[ib[m][5]]][2][j][2][n] +
                                       dk[pix[ib[m][4]]][3][j][3][n] +
                                       dk[pix[ib[m][24]]][4][j][4][n] +
                                       dk[pix[ib[m][14]]][5][j][5][n] +
                                       dk[pix[ib[m][13]]][6][j][6][n] +
                                       dk[pix[ib[m][12]]][7][j][7][n]);
      }
      utot += (u[m][j] * (0.5 * gb[m][j] + b[m][j]));
      gb[m][j] += b[m][j];
    }
  }

  return (utot);
}

/*  Subroutine that computes the six average stresses and six  */
/*  average strains. */

void stress(int nx, int ny, int nz, int ns, int doitz, int micro, int ilast) {

  double uu[8][3];
  double dndx[8], dndy[8], dndz[8], es[6][8][3];
  int nxy, nyz, n1, n2, n3, k, j, i, mm, n8, n;
  int m;
  double str11, str12, str13, str22, str23, str33;
  double s11, s12, s13, s22, s23, s33;

  nxy = nx * ny;
  nyz = ny * nz;

  /***
   *	Initialize stressall global variable here
   ***/

  for (j = 0; j < 16; j++) {
    for (i = 0; i < NSP; i++) {
      stressall[i][j] = 0.0;
    }
  }

  /***
   *	Initialize new total stress and strain variables
   ***/
  strxxt = stryyt = strzzt = 0.0; /* stresses */
  strxzt = stryzt = strxyt = 0.0;
  sxxt = syyt = szzt = 0.0; /* strains */
  sxzt = syzt = sxyt = 0.0;

  /*  set up single element strain matrix */
  /*  dndx, dndy, and dndz are the components of the average strain  */
  /*  matrix in a pixel */

  dndx[0] = (-0.25);
  dndx[1] = 0.25;
  dndx[2] = 0.25;
  dndx[3] = (-0.25);
  dndx[4] = (-0.25);
  dndx[5] = 0.25;
  dndx[6] = 0.25;
  dndx[7] = (-0.25);
  dndy[0] = (-0.25);
  dndy[1] = (-0.25);
  dndy[2] = 0.25;
  dndy[3] = 0.25;
  dndy[4] = (-0.25);
  dndy[5] = (-0.25);
  dndy[6] = 0.25;
  dndy[7] = 0.25;
  dndz[0] = (-0.25);
  dndz[1] = (-0.25);
  dndz[2] = (-0.25);
  dndz[3] = (-0.25);
  dndz[4] = 0.25;
  dndz[5] = 0.25;
  dndz[6] = 0.25;
  dndz[7] = 0.25;

  /*  Build averaged strain matrix, follows code in femat, but for average */
  /*  strain over the pixel, not the strain at a point. */
  for (n1 = 0; n1 < 6; n1++) {
    for (n2 = 0; n2 < 8; n2++) {
      for (n3 = 0; n3 < 3; n3++) {
        es[n1][n2][n3] = 0.0;
      }
    }
  }
  for (n1 = 0; n1 < 8; n1++) {
    es[0][n1][0] = dndx[n1];
    es[1][n1][1] = dndy[n1];
    es[2][n1][2] = dndz[n1];
    es[3][n1][0] = dndz[n1];
    es[3][n1][2] = dndx[n1];
    es[4][n1][1] = dndz[n1];
    es[4][n1][2] = dndy[n1];
    es[5][n1][0] = dndy[n1];
    es[5][n1][1] = dndx[n1];
  }

  /*  Compute components of the average stress and strain tensors in each pixel
   */
  for (i = 0; i < nx; i++) {
    strxx = 0.0;
    stryy = 0.0;
    strzz = 0.0;
    strxz = 0.0;
    stryz = 0.0;
    strxy = 0.0;
    sxx = 0.0;
    syy = 0.0;
    szz = 0.0;
    sxz = 0.0;
    syz = 0.0;
    sxy = 0.0;
    for (k = 0; k < nz; k++) {
      for (j = 0; j < ny; j++) {
        m = k * nxy + j * nx + i;

        /*  load in elements of 8-vector using pd. bd. conds. */

        for (mm = 0; mm < 3; mm++) {
          uu[0][mm] = u[m][mm];
          uu[1][mm] = u[ib[m][2]][mm];
          uu[2][mm] = u[ib[m][1]][mm];
          uu[3][mm] = u[ib[m][0]][mm];
          uu[4][mm] = u[ib[m][25]][mm];
          uu[5][mm] = u[ib[m][18]][mm];
          uu[6][mm] = u[ib[m][17]][mm];
          uu[7][mm] = u[ib[m][16]][mm];
        }

        /*  Correct for periodic boundary conditions, some displacements are
         * wrong */
        /*  for a pixel on a periodic boundary.  Since they come from an
         * opposite  */
        /*  face, need to put in applied strain to correct them. */

        if (i == (nx - 1)) {
          uu[1][0] += exx * (double)nx;
          uu[1][1] += exy * (double)nx;
          uu[1][2] += exz * (double)nx;
          uu[2][0] += exx * (double)nx;
          uu[2][1] += exy * (double)nx;
          uu[2][2] += exz * (double)nx;
          uu[5][0] += exx * (double)nx;
          uu[5][1] += exy * (double)nx;
          uu[5][2] += exz * (double)nx;
          uu[6][0] += exx * (double)nx;
          uu[6][1] += exy * (double)nx;
          uu[6][2] += exz * (double)nx;
        }

        if (j == (ny - 1)) {
          uu[2][0] += exy * (double)ny;
          uu[2][1] += eyy * (double)ny;
          uu[2][2] += eyz * (double)ny;
          uu[3][0] += exy * (double)ny;
          uu[3][1] += eyy * (double)ny;
          uu[3][2] += eyz * (double)ny;
          uu[6][0] += exy * (double)ny;
          uu[6][1] += eyy * (double)ny;
          uu[6][2] += eyz * (double)ny;
          uu[7][0] += exy * (double)ny;
          uu[7][1] += eyy * (double)ny;
          uu[7][2] += eyz * (double)ny;
        }

        if (k == (nz - 1)) {
          uu[4][0] += exz * (double)nz;
          uu[4][1] += eyz * (double)nz;
          uu[4][2] += ezz * (double)nz;
          uu[5][0] += exz * (double)nz;
          uu[5][1] += eyz * (double)nz;
          uu[5][2] += ezz * (double)nz;
          uu[6][0] += exz * (double)nz;
          uu[6][1] += eyz * (double)nz;
          uu[6][2] += ezz * (double)nz;
          uu[7][0] += exz * (double)nz;
          uu[7][1] += eyz * (double)nz;
          uu[7][2] += ezz * (double)nz;
        }

        /*  local stresses and strains in a pixel */

        str11 = 0.0;
        str22 = 0.0;
        str33 = 0.0;
        str13 = 0.0;
        str23 = 0.0;
        str12 = 0.0;
        s11 = 0.0;
        s22 = 0.0;
        s33 = 0.0;
        s13 = 0.0;
        s23 = 0.0;
        s12 = 0.0;
        for (n8 = 0; n8 < 8; n8++) {
          for (n3 = 0; n3 < 3; n3++) {
            s11 += es[0][n8][n3] * uu[n8][n3];
            s22 += es[1][n8][n3] * uu[n8][n3];
            s33 += es[2][n8][n3] * uu[n8][n3];
            s13 += es[3][n8][n3] * uu[n8][n3];
            s23 += es[4][n8][n3] * uu[n8][n3];
            s12 += es[5][n8][n3] * uu[n8][n3];
            for (n = 0; n < 6; n++) {
              str11 += cmod[pix[m]][0][n] * es[n][n8][n3] * uu[n8][n3];
              str22 += cmod[pix[m]][1][n] * es[n][n8][n3] * uu[n8][n3];
              str33 += cmod[pix[m]][2][n] * es[n][n8][n3] * uu[n8][n3];
              str13 += cmod[pix[m]][3][n] * es[n][n8][n3] * uu[n8][n3];
              str23 += cmod[pix[m]][4][n] * es[n][n8][n3] * uu[n8][n3];
              str12 += cmod[pix[m]][5][n] * es[n][n8][n3] * uu[n8][n3];
            }
          }
        }

        /*  sum local strains and stresses into global values */

        strxx += str11;
        stryy += str22;
        strzz += str33;
        strxy += str12;
        strxz += str13;
        stryz += str23;
        sxx += s11;
        syy += s22;
        szz += s33;
        sxy += s12;
        sxz += s13;
        syz += s23;

        /***
         *	These variables originally defined to add up
         *	over all layers when calculating full
         *	elastic stiffness tensor (all 36 components)
         *
         *	Now, when not doing full stiffness tensor, this
         *	is used for total instead of layer averages
         *	(see below)
         ***/

        strxxt += str11;
        stryyt += str22;
        strzzt += str33;
        strxyt += str12;
        strxzt += str13;
        stryzt += str23;
        sxxt += s11;
        syyt += s22;
        szzt += s33;
        sxyt += s12;
        sxzt += s13;
        syzt += s23;

        stressall[pix[m]][0] += str11;
        stressall[pix[m]][1] += str22;
        stressall[pix[m]][2] += str33;
        stressall[pix[m]][3] += str12;
        stressall[pix[m]][4] += str13;
        stressall[pix[m]][5] += str23;
        stressall[pix[m]][6] += s11;
        stressall[pix[m]][7] += s22;
        stressall[pix[m]][8] += s33;
        stressall[pix[m]][9] += s12;
        stressall[pix[m]][10] += s13;
        stressall[pix[m]][11] += s23;
      }
    }

    /* Averaging depends on whether layer averaging (doitz) was chosen or not */

    if (doitz) {

      /*  Layer average of stresses and strains in each layer */

      strxx /= (double)nyz;
      stryy /= (double)nyz;
      strzz /= (double)nyz;
      strxz /= (double)nyz;
      stryz /= (double)nyz;
      strxy /= (double)nyz;
      sxx /= (double)nyz;
      syy /= (double)nyz;
      szz /= (double)nyz;
      sxz /= (double)nyz;
      syz /= (double)nyz;
      sxy /= (double)nyz;

      if (ilast) {
        /*
        i1 = 6 * micro;
        Vv[i][i1] = strxx;
        Vv[i][i1+1] = stryy;
        Vv[i][i1+2] = strzz;
        Vv[i][i1+3] = strxz;
        Vv[i][i1+4] = stryz;
        Vv[i][i1+5] = strxy;
        Aa[i][i1][0] = strxx;
        Aa[i][i1][1] = stryy;
        Aa[i][i1][2] = strzz;
        Aa[i][i1][3] = strxz;
        Aa[i][i1][4] = stryz;
        Aa[i][i1][5] = strxy;
        for (iii = 0; iii < 6; iii++) {
                Aa[i][i1+1][6+iii] = Aa[ii][i1][iii];
                Aa[i][i1+2][12+iii] = Aa[ii][i1][iii];
                Aa[i][i1+3][18+iii] = Aa[ii][i1][iii];
                Aa[i][i1+4][24+iii] = Aa[ii][i1][iii];
                Aa[i][i1+5][30+iii] = Aa[ii][i1][iii];
        }
        */

        /***
         *  All the stuff above is for full elastic
         *  stiffness tensor.  Uncomment it if you want
         *  the full stiffness tensor.  Takes 6
         *  independent solutions (see initial switch
         *  statement in main function for selecting
         *  strains for each case of micro, with npoints
         *  equal to six
         *
         *  The equations below just give the bulk and
         *  shear modulus (isotropic average) in each
         *  layer
         ***/

        K[i] = (1.0 / 3.0) * (strxx + stryy + strzz) / (sxx + syy + szz);
        G[i] = (1.0 / 3.0) * ((strxz / sxz) + (stryz / syz) + (strxy / sxy));
      }
    }
  }

  if (ilast) {

    /***
     *	Calculation of bulk quantities, like the individual
     *	contributions of different phases, and the total
     *	stress and strain components.
     *
     *	Only makes sense when doing all the strains at once
     *	instead of in six different iterations (see original
     *	switch statement in main function)
     ***/

    for (j = 0; j < 12; j++) {
      for (i = 0; i < NSP; i++) {
        stressall[i][j] /= (double)ns;
      }
    }

    strxxt /= (double)ns;
    stryyt /= (double)ns;
    strzzt /= (double)ns;
    strxzt /= (double)ns;
    stryzt /= (double)ns;
    strxyt /= (double)ns;
    sxxt /= (double)ns;
    syyt /= (double)ns;
    szzt /= (double)ns;
    sxzt /= (double)ns;
    syzt /= (double)ns;
    sxyt /= (double)ns;
  }
}

int dembx(int ns, int ldemb, int kkk) {
  double lambda, gamma, hAh, gglast, Ahtemp;
  int Lstep;
  int m3, ijk, j, n;
  int m;

  /*
  printf("In dembx now, ldemb = %d gg = %lf gtest = %lf...\n",ldemb,gg,gtest);
  fflush(stdout);
  */
  /*  Initialize the conjugate direction vector on first call to dembx only */
  /*  For calls to dembx after the first, we want to continue using the  */
  /*  value of h determined in the previous call. Of course, if npoints is */
  /*  greater than 1, this initialization step will be run for every new */
  /*  microstructure used, as kkk is reset to 1 every time the counter micro */
  /*  is increased. */
  if (kkk == 0) {
    /*
    printf("First dembx call\n");
    fflush(stdout);
    */
    for (m = 0; m < ns; m++) {
      for (m3 = 0; m3 < 3; m3++) {
        h[m][m3] = gb[m][m3];
      }
    }
  }

  /*  Lstep counts the number of conjugate gradient steps taken in */
  /*  each call to dembx */
  Lstep = 0;

  for (ijk = 0; ((ijk < ldemb) && (gg >= gtest)); ijk++) {
    /*
    printf("\tdembx iteration %d gg = %lf gtest = %lf\n",ijk,gg,gtest);
    fflush(stdout);
    */
    Lstep += 1;

    /*  Do global matrix multiply via small stiffness matrices, Ahtemp = A * h
     */
    /*  The long statement below correctly brings in all the terms from */
    /*  the global matrix A using only the small stiffness matrices dk. */
    hAh = 0.0;
    for (m = 0; m < ns; m++) {
      for (j = 0; j < 3; j++) {
        Ahtemp = 0.0;
        for (n = 0; n < 3; n++) {
          Ahtemp += h[ib[m][0]][n] * (dk[pix[ib[m][26]]][0][j][3][n] +
                                      dk[pix[ib[m][6]]][1][j][2][n] +
                                      dk[pix[ib[m][24]]][4][j][7][n] +
                                      dk[pix[ib[m][14]]][5][j][6][n]) +
                    h[ib[m][1]][n] * (dk[pix[ib[m][26]]][0][j][2][n] +
                                      dk[pix[ib[m][24]]][4][j][6][n]) +
                    h[ib[m][2]][n] * (dk[pix[ib[m][26]]][0][j][1][n] +
                                      dk[pix[ib[m][4]]][3][j][2][n] +
                                      dk[pix[ib[m][12]]][7][j][6][n] +
                                      dk[pix[ib[m][24]]][4][j][5][n]) +
                    h[ib[m][3]][n] * (dk[pix[ib[m][4]]][3][j][1][n] +
                                      dk[pix[ib[m][12]]][7][j][5][n]) +
                    h[ib[m][4]][n] * (dk[pix[ib[m][5]]][2][j][1][n] +
                                      dk[pix[ib[m][4]]][3][j][0][n] +
                                      dk[pix[ib[m][13]]][6][j][5][n] +
                                      dk[pix[ib[m][12]]][7][j][4][n]) +
                    h[ib[m][5]][n] * (dk[pix[ib[m][5]]][2][j][0][n] +
                                      dk[pix[ib[m][13]]][6][j][4][n]) +
                    h[ib[m][6]][n] * (dk[pix[ib[m][5]]][2][j][3][n] +
                                      dk[pix[ib[m][6]]][1][j][0][n] +
                                      dk[pix[ib[m][13]]][6][j][7][n] +
                                      dk[pix[ib[m][14]]][5][j][4][n]) +
                    h[ib[m][7]][n] * (dk[pix[ib[m][6]]][1][j][3][n] +
                                      dk[pix[ib[m][14]]][5][j][7][n]) +
                    h[ib[m][8]][n] * (dk[pix[ib[m][24]]][4][j][3][n] +
                                      dk[pix[ib[m][14]]][5][j][2][n]) +
                    h[ib[m][9]][n] * (dk[pix[ib[m][24]]][4][j][2][n]) +
                    h[ib[m][10]][n] * (dk[pix[ib[m][12]]][7][j][2][n] +
                                       dk[pix[ib[m][24]]][4][j][1][n]) +
                    h[ib[m][11]][n] * (dk[pix[ib[m][12]]][7][j][1][n]) +
                    h[ib[m][12]][n] * (dk[pix[ib[m][12]]][7][j][0][n] +
                                       dk[pix[ib[m][13]]][6][j][1][n]) +
                    h[ib[m][13]][n] * (dk[pix[ib[m][13]]][6][j][0][n]) +
                    h[ib[m][14]][n] * (dk[pix[ib[m][13]]][6][j][3][n] +
                                       dk[pix[ib[m][14]]][5][j][0][n]) +
                    h[ib[m][15]][n] * (dk[pix[ib[m][14]]][5][j][3][n]) +
                    h[ib[m][16]][n] * (dk[pix[ib[m][26]]][0][j][7][n] +
                                       dk[pix[ib[m][6]]][1][j][6][n]) +
                    h[ib[m][17]][n] * (dk[pix[ib[m][26]]][0][j][6][n]) +
                    h[ib[m][18]][n] * (dk[pix[ib[m][26]]][0][j][5][n] +
                                       dk[pix[ib[m][4]]][3][j][6][n]) +
                    h[ib[m][19]][n] * (dk[pix[ib[m][4]]][3][j][5][n]) +
                    h[ib[m][20]][n] * (dk[pix[ib[m][4]]][3][j][4][n] +
                                       dk[pix[ib[m][5]]][2][j][5][n]) +
                    h[ib[m][21]][n] * (dk[pix[ib[m][5]]][2][j][4][n]) +
                    h[ib[m][22]][n] * (dk[pix[ib[m][5]]][2][j][7][n] +
                                       dk[pix[ib[m][6]]][1][j][4][n]) +
                    h[ib[m][23]][n] * (dk[pix[ib[m][6]]][1][j][7][n]) +
                    h[ib[m][24]][n] * (dk[pix[ib[m][13]]][6][j][2][n] +
                                       dk[pix[ib[m][12]]][7][j][3][n] +
                                       dk[pix[ib[m][14]]][5][j][1][n] +
                                       dk[pix[ib[m][24]]][4][j][0][n]) +
                    h[ib[m][25]][n] * (dk[pix[ib[m][5]]][2][j][6][n] +
                                       dk[pix[ib[m][4]]][3][j][7][n] +
                                       dk[pix[ib[m][26]]][0][j][4][n] +
                                       dk[pix[ib[m][6]]][1][j][5][n]) +
                    h[ib[m][26]][n] * (dk[pix[ib[m][26]]][0][j][0][n] +
                                       dk[pix[ib[m][6]]][1][j][1][n] +
                                       dk[pix[ib[m][5]]][2][j][2][n] +
                                       dk[pix[ib[m][4]]][3][j][3][n] +
                                       dk[pix[ib[m][24]]][4][j][4][n] +
                                       dk[pix[ib[m][14]]][5][j][5][n] +
                                       dk[pix[ib[m][13]]][6][j][6][n] +
                                       dk[pix[ib[m][12]]][7][j][7][n]);
        }
        hAh += h[m][j] * Ahtemp;
      }
    }

    lambda = gg / hAh;
    gglast = gg;
    gg = 0.0;
    for (m = 0; m < ns; m++) {
      for (j = 0; j < 3; j++) {
        Ahtemp = 0.0;
        for (n = 0; n < 3; n++) {
          Ahtemp += h[ib[m][0]][n] * (dk[pix[ib[m][26]]][0][j][3][n] +
                                      dk[pix[ib[m][6]]][1][j][2][n] +
                                      dk[pix[ib[m][24]]][4][j][7][n] +
                                      dk[pix[ib[m][14]]][5][j][6][n]) +
                    h[ib[m][1]][n] * (dk[pix[ib[m][26]]][0][j][2][n] +
                                      dk[pix[ib[m][24]]][4][j][6][n]) +
                    h[ib[m][2]][n] * (dk[pix[ib[m][26]]][0][j][1][n] +
                                      dk[pix[ib[m][4]]][3][j][2][n] +
                                      dk[pix[ib[m][12]]][7][j][6][n] +
                                      dk[pix[ib[m][24]]][4][j][5][n]) +
                    h[ib[m][3]][n] * (dk[pix[ib[m][4]]][3][j][1][n] +
                                      dk[pix[ib[m][12]]][7][j][5][n]) +
                    h[ib[m][4]][n] * (dk[pix[ib[m][5]]][2][j][1][n] +
                                      dk[pix[ib[m][4]]][3][j][0][n] +
                                      dk[pix[ib[m][13]]][6][j][5][n] +
                                      dk[pix[ib[m][12]]][7][j][4][n]) +
                    h[ib[m][5]][n] * (dk[pix[ib[m][5]]][2][j][0][n] +
                                      dk[pix[ib[m][13]]][6][j][4][n]) +
                    h[ib[m][6]][n] * (dk[pix[ib[m][5]]][2][j][3][n] +
                                      dk[pix[ib[m][6]]][1][j][0][n] +
                                      dk[pix[ib[m][13]]][6][j][7][n] +
                                      dk[pix[ib[m][14]]][5][j][4][n]) +
                    h[ib[m][7]][n] * (dk[pix[ib[m][6]]][1][j][3][n] +
                                      dk[pix[ib[m][14]]][5][j][7][n]) +
                    h[ib[m][8]][n] * (dk[pix[ib[m][24]]][4][j][3][n] +
                                      dk[pix[ib[m][14]]][5][j][2][n]) +
                    h[ib[m][9]][n] * (dk[pix[ib[m][24]]][4][j][2][n]) +
                    h[ib[m][10]][n] * (dk[pix[ib[m][12]]][7][j][2][n] +
                                       dk[pix[ib[m][24]]][4][j][1][n]) +
                    h[ib[m][11]][n] * (dk[pix[ib[m][12]]][7][j][1][n]) +
                    h[ib[m][12]][n] * (dk[pix[ib[m][12]]][7][j][0][n] +
                                       dk[pix[ib[m][13]]][6][j][1][n]) +
                    h[ib[m][13]][n] * (dk[pix[ib[m][13]]][6][j][0][n]) +
                    h[ib[m][14]][n] * (dk[pix[ib[m][13]]][6][j][3][n] +
                                       dk[pix[ib[m][14]]][5][j][0][n]) +
                    h[ib[m][15]][n] * (dk[pix[ib[m][14]]][5][j][3][n]) +
                    h[ib[m][16]][n] * (dk[pix[ib[m][26]]][0][j][7][n] +
                                       dk[pix[ib[m][6]]][1][j][6][n]) +
                    h[ib[m][17]][n] * (dk[pix[ib[m][26]]][0][j][6][n]) +
                    h[ib[m][18]][n] * (dk[pix[ib[m][26]]][0][j][5][n] +
                                       dk[pix[ib[m][4]]][3][j][6][n]) +
                    h[ib[m][19]][n] * (dk[pix[ib[m][4]]][3][j][5][n]) +
                    h[ib[m][20]][n] * (dk[pix[ib[m][4]]][3][j][4][n] +
                                       dk[pix[ib[m][5]]][2][j][5][n]) +
                    h[ib[m][21]][n] * (dk[pix[ib[m][5]]][2][j][4][n]) +
                    h[ib[m][22]][n] * (dk[pix[ib[m][5]]][2][j][7][n] +
                                       dk[pix[ib[m][6]]][1][j][4][n]) +
                    h[ib[m][23]][n] * (dk[pix[ib[m][6]]][1][j][7][n]) +
                    h[ib[m][24]][n] * (dk[pix[ib[m][13]]][6][j][2][n] +
                                       dk[pix[ib[m][12]]][7][j][3][n] +
                                       dk[pix[ib[m][14]]][5][j][1][n] +
                                       dk[pix[ib[m][24]]][4][j][0][n]) +
                    h[ib[m][25]][n] * (dk[pix[ib[m][5]]][2][j][6][n] +
                                       dk[pix[ib[m][4]]][3][j][7][n] +
                                       dk[pix[ib[m][26]]][0][j][4][n] +
                                       dk[pix[ib[m][6]]][1][j][5][n]) +
                    h[ib[m][26]][n] * (dk[pix[ib[m][26]]][0][j][0][n] +
                                       dk[pix[ib[m][6]]][1][j][1][n] +
                                       dk[pix[ib[m][5]]][2][j][2][n] +
                                       dk[pix[ib[m][4]]][3][j][3][n] +
                                       dk[pix[ib[m][24]]][4][j][4][n] +
                                       dk[pix[ib[m][14]]][5][j][5][n] +
                                       dk[pix[ib[m][13]]][6][j][6][n] +
                                       dk[pix[ib[m][12]]][7][j][7][n]);
        }
        u[m][j] -= lambda * h[m][j];
        gb[m][j] -= lambda * Ahtemp;
        gg += gb[m][j] * gb[m][j];
      }
    }

    if (gg >= gtest) {

      gamma = gg / gglast;
      for (m = 0; m < ns; m++) {
        for (m3 = 0; m3 < 3; m3++) {
          h[m][m3] = gb[m][m3] + gamma * h[m][m3];
        }
      }

    } /* end of if gg condition */
  }

  return (Lstep);
}

void modlayer(int *nagg1) {
  register int i, j, ii, jj;
  int i1, i2, i3, i4, i5, i6, m, m1;
  double set, kk, ggg, c11avg, c12avg, c44avg, c11final, xj;

  /***
   *	Argument nagg1 is the label for the start of the aggregate
   *	in the X dimension
   ***/

  /***
   *	There are six sets of original strains, and Xsyssize layers.
   *	The six original strains are
   *
   *	    (0) exx = 0.1, all others zero
   *	    (1) eyy = 0.1, all others zero
   *	    (2) ezz = 0.1, all others zero
   *	    (3) exz = 0.05, all others zero
   *	    (4) eyz = 0.05, all others zero
   *	    (5) exy = 0.05, all others zero
   *
   *	The minimum x position of the aggregate is nagg1 (passed as an
   *	argument to this function).
   ***/

  for (j = 0; j < 36;
       j++) { /* 36 components in FULL stress and strain tensors */
    for (i = 0; i < 36; i++) {
      A[i][j] = 0.0;
      for (ii = 0; ii < Xsyssize; ii++) {
        A1[ii][i][j] = 0.0;
      }
    }
  }

  /***
   *	Vv and Aa tensors already have been generated at end of stress function
   *	Next, switch rows to make block diagonal set of equations
   ***/

  for (ii = 0; ii < Xsyssize; ii++) {
    for (i = 0; i < 6; i++) {
      i1 = i * 5;
      i2 = (i - 1) * 5;
      i3 = (i - 2) * 5;
      i4 = (i - 3) * 5;
      i5 = (i - 4) * 5;
      i6 = (i - 5) * 5;
      for (j = 0; j < 36; j++) {
        A1[ii][i][j] = Aa[ii][i + i1][j];
        A1[ii][i + 6][j] = Aa[ii][i + 6 + i2][j];
        A1[ii][i + 12][j] = Aa[ii][i + 12 + i3][j];
        A1[ii][i + 18][j] = Aa[ii][i + 18 + i4][j];
        A1[ii][i + 24][j] = Aa[ii][i + 24 + i5][j];
        A1[ii][i + 30][j] = Aa[ii][i + 30 + i6][j];
      }
    }
  }

  /***
   *	Now do loop in layers, determining the full elastic
   *	modulus tensor in each layer, then take the isotropic
   *	average of it
   ***/

  for (ii = 0; ii < Xsyssize; ii++) {
    for (j = 0; j < 36; j++) {
      A[j][36] = Vv[ii][j];
      for (i = 0; i < 36; i++) {
        A[i][j] = A1[ii][i][j];
      }
    }

    /***
     *	Solves m X m system of linear equations viat
     *	Gaussian elimination.  A[i][j] is the matrix,
     *	A[m][m+1], the last column, is the RHS of Ax = b
     ***/

    m = 36;
    m1 = m + 1;

    /* Begin Gaussian elimination */

    for (jj = 0; jj < m; jj++) {

      /***
       *	Make [jj][jj] element of matrix = 1, modify other
       *	elements of row as needed
       ***/

      set = A[jj][jj];

      for (j = 0; j < m1; j++) {
        A[jj][j] /= set;
      }

      /* Zero out all entries in jj column */

      for (i = 0; i < m; i++) {
        if (i != jj) {
          set = A[i][jj];
          for (j = 0; j < m1; j++) {
            A[i][j] -= (A[jj][j] * set);
          }
        }
      }
    }

    for (jj = 0; jj < 6; jj++) {
      i1 = jj * 6;
      Cc[jj][0] = A[i1][36];
      Cc[jj][1] = A[i1 + 1][36];
      Cc[jj][2] = A[i1 + 2][36];
      Cc[jj][3] = A[i1 + 3][36];
      Cc[jj][4] = A[i1 + 4][36];
      Cc[jj][5] = A[i1 + 5][36];
    }

    /* Perform isotropic average with Cc[i][j] */

    c11avg = (Cc[0][0] + Cc[1][1] + Cc[2][2]) / 3.0;
    c12avg =
        (Cc[0][1] + Cc[0][2] + Cc[1][0] + Cc[1][2] + Cc[2][0] + Cc[2][1]) / 6.0;
    c44avg = (Cc[3][3] + Cc[4][4] + Cc[5][5]) / 3.0;
    c11final = 0.2 * ((3.0 * c11avg) + (2.0 * c12avg) + (4.0 * c44avg));
    G[ii] = 0.2 * (c11avg - c12avg + (3.0 * c44avg));
    K[ii] = c11final - (4.0 * G[ii] / 3.0);
  }

  /***
   *	Now average on both sides of aggregate, plot 1st pixel at x = 0.5,
   *	2nd pixel at x = 1.5, etc.
   ***/

  xj = -0.5;
  for (i = *nagg1 - 1; i >= 0; i--) {
    xj += 1.0;
    kk = 0.50 * (K[i] + K[Xsyssize - i - 1]);
    ggg = 0.50 * (G[i] + G[Xsyssize - i - 1]);
    printf("%.1f,%.4f,%.4f\n", xj, kk, ggg);
  }
}

int main(void) {
  int m3, i, j, k, n, nx, ny, nz, nphase, ijk, nxy, i1, j1, k1, npoints, kmax,
      ldemb;
  int kkk, micro, doitz, nagg1, oval;
  int m, ns, m1, ltot = 0, Lstep, count;
  double utot, x, y, z;
  double bulk, shear, young, pois, save;
  float kk, xj, sum = 0.0;
  char phasename[MAXSTRING];
  FILE *outfile;

  /*
              printf("Enter name of progress file: \n");
              read_string(instring,sizeof(instring));
          sprintf(Progfilename,"%s",instring);
  */

  /* Initialize global arrays to zero */

  for (i = 0; i < NSP; i++) {
    phasemod[i][0] = 0.0;
    phasemod[i][1] = 0.0;
    prob[i] = 0.0;
    for (j = 0; j < 6; j++) {
      for (k = 0; k < 6; k++) {
        cmod[i][j][k] = 0.0;
      }
    }
    for (j = 0; j < 8; j++) {
      for (k = 0; k < 3; k++) {
        for (i1 = 0; i1 < 8; i1++) {
          for (j1 = 0; j1 < 3; j1++) {
            dk[i][j][k][i1][j1] = 0.0;
          }
        }
      }
    }
    for (j = 0; j < 16; j++) {
      stressall[i][j] = 0.0;
    }
  }

  /*  (USER) nphase is the number of phases being considered in the problem. */
  /*  The values of pix(m) will run from 1 to nphase. */
  nphase = NSPHASES + 1;

  /* (USER) */
  /* The parameter phasemod(i,j) is the bulk (i,0) and shear (i,1) moduli of  */
  /* the i'th phase. These can be input in terms of Young's moduli E(i,0) and */
  /* Poisson's ratio nu (i,1).  The program, in do loop 1144, then changes them
   */
  /* to bulk and shear moduli, using relations for isotropic elastic */
  /* moduli.  For anisotropic elastic material, one can directly input */
  /* the elastic moduli tensor cmod in subroutine femat, and skip this part. */
  /* If you wish to input in terms of bulk (0) and shear (1), then make sure */
  /* to comment out the for loop afterward. */

  /* initialize all the phase elastic properties to zero */
  for (ijk = 0; ijk <= nphase; ijk++) {
    phasemod[ijk][0] = 0.0;
    phasemod[ijk][1] = 0.0;
  }

  /***************************  28 July 2012 ****************************
      Many values below updated on 28 July 2012, based on new results in
      measurement and calculation of single-phase moduli using high-pressure
      diffraction and DFT, respectively

      Voigt bound on phase moduli (i.e., locking grain boundary
      approximation, shear relaxation within grain, is generally appropriate
      and consistent with the finite element application here.  Reuss values,
      always less than or equal two Voigt values, (i.e. sliding grain boundary
      approximation, hydrostatic stress, may be appropriate at the
      contact of two clinker particles
  ***************************  28 July 2012 ****************************/

  /*  C3S (Voigt bounds on C3S, i.e. locking grain, as recommended by Angel by
     literature search, especially calculations by Manzano et al in 2009 */
  /*
          phasemod[C3S][0]=112.0;
          phasemod[C3S][1]=52.0;
  */
  /*  C2S (Voigt bounds on beta-C2S, i.e. locking grain, as recommended by Angel
     by literature search, especially calculations by Manzano et al in 2009 */
  /*
          phasemod[C2S][0]=111.0;
          phasemod[C2S][1]=53.1;
  */
  /* C3A (DFT simulations by Manzano et al 2009, C3A is cubic so Voigt and Reuss
     bulk moduli are equal, we use the Voigt value for shear modulus because of
     the assumption of locked grain boundaries) */
  /*
          phasemod[C3A][0]=102.9;
          phasemod[C3A][1]=54.4;
  */
  /* C4AF (Voigt estimate on brownmillerite, i.e. locking grain, as recommended
     by Angel by literature search, especially high-pressure diffraction studies
     of Ross et al. 2002 and Vanpeteghem et al 2008 */
  /*
          phasemod[C4AF][0]=151.0;
          phasemod[C4AF][1]=50.2;
  */

  /* K2SO4 = arcanite */
  /*
          phasemod[K2SO4][0] = 31.89;
          phasemod[K2SO4][1] = 17.42;
  */
  /* NA2SO4 = thenardite */
  /*
          phasemod[NA2SO4][0] = 43.396;
          phasemod[NA2SO4][1] = 22.292;
  */
  /* Gypsum (Voigt values determined from ultrasonic interferometry, by
     Haussuehl, 1965). May want to use Reuss values for those voxels at the
     surface of the particle */
  /* phasemod[GYPSUM][0]=44.2; */ /* Voigt value */
  /* phasemod[GYPSUM][1]=17.3; */ /* Voigt value */
  /* phasemod[GYPSUM][0]=41.0; */ /* Reuss value */
  /* phasemod[GYPSUM][1]=17.3; */ /* Reuss value */
  /* Anhydrite (from compression tests on single crystals, Schewerdtner et al
     1965. All tensor components measured to within 7% error.  Voigt and Reuss
     values calculated from these */
  /* phasemod[ANHYDRITE][0] = 58.0; */ /* Voigt value */
  /* phasemod[ANHYDRITE][0] = 53.0; */ /* Reuss value */
  /* phasemod[ANHYDRITE][1] = 36.0; */ /* assuming Poisson ratio = 0.25 */
  /* Hemihydrate (i.e. bassanite).  Reuss values reported in a powder
     compression study. Angel suggests estimating Voigt values based on the
     anisotropy ratio of the crystal, which is 1.30 */
  /* phasemod[HEMIHYD][0]=90.0; */ /* Voigt value */
  /* phasemod[HEMIHYD][1]=54.0; */
  /* phasemod[HEMIHYD][0]=86.0; */ /* Reuss value */
  /* phasemod[HEMIHYD][1]=51.6; */ /* Reuss value */
  /* pozzolan (no pozzolan) -- assume same as silica */
  /*
          phasemod[SFUME][0]=phasemod[AMSIL][0] = 36.4;
          phasemod[SFUME][1]=phasemod[AMSIL][1] = 31.2;
  */
  /* inert  --- assume same as calcite mineral.  Data from Brillouin
     spectroscopy (Chen et al 2001) provides Voigt values on bulk and shear
     moduli */
  /*
          phasemod[INERT][0] = 79.3;
          phasemod[INERT][1] = 37.4;
  */
  /* slag --- assume same as C3S */
  /*
          phasemod[SLAG][0]=phasemod[C3S][0];
          phasemod[SLAG][1]=phasemod[C3S][1];
  */
  /* ASG flyash  -- assume same as AMSIL */
  /*
          phasemod[ASG][0]=phasemod[AMSIL][0];
          phasemod[ASG][1]=phasemod[AMSIL][1];
  */
  /* CAS2 fly ash -- assume same as AMSIL */
  /*
          phasemod[CAS2][0]=phasemod[AMSIL][0];
          phasemod[CAS2][1]=phasemod[AMSIL][1];
  */
  /* Portlandite, data from Brillouin spectroscopy (Speziale et al. 2008)
       provides Voigt bounds on bulk and shear moduli */
  /*
          phasemod[CH][0]=37.2;
          phasemod[CH][1]=24.4;
  */
  /* C-S-H */
  /*  A model */
  /*        phasemod[CSH][0]=24.0; */
  /*        phasemod[CSH][1]=0.2; */
  /*  B and C  model */
  /*        phasemod[CSH][0]=20.0; */
  /*        phasemod[CSH][1]=0.25; */
  /*  D model */
  /*       phasemod[CSH][0]=22.4; */
  /*        phasemod[CSH][1]=0.25; */
  /*  E model, suggested by Artioli and Angel */
  /*
          phasemod[CSH][0]=31.0;
          phasemod[CSH][1]=13.0;
  */
  /* C3AH6 (same as C-S-H for now) */
  /*
          phasemod[C3AH6][0]=phasemod[CSH][0];
          phasemod[C3AH6][1]=phasemod[CSH][1];
  */
  /* Ettringite (Voigt value from Brillouin spectroscopy, Speziale et al 2008)
   */
  /*
          phasemod[ETTR][0] = 27.7;
          phasemod[ETTR][1] = 9.9;
  */
  /* Ettringite (from C4AF, assume same as regular ettringite for now) */
  /*
          phasemod[ETTRC4AF][0]=phasemod[ETTR][0];
          phasemod[ETTRC4AF][1]=phasemod[ETTR][1];
  */
  /* Afm (same as C-S-H) for now */
  /*        phasemod[AFM][0]=phasemod[CSH][0]; */
  /*        phasemod[AFM][1]=phasemod[CSH][1]; */
  /* Model C Afm same as CH now, also as suggested by Angel due to
      similarity of structure to portlandite */
  /*
          phasemod[AFM][0]=phasemod[CH][0];
          phasemod[AFM][1]=phasemod[CH][1];
  */
  /* FH3 (same as C-S-H for now) */
  /*
          phasemod[FH3][0]=phasemod[CSH][0];
          phasemod[FH3][1]=phasemod[CSH][1];
  */
  /* pozzolanic C-S-H */
  /*
          phasemod[POZZCSH][0]=phasemod[CSH][0];
          phasemod[POZZCSH][1]=phasemod[CSH][1];
  */
  /* Slag C-S-H */
  /*
          phasemod[SLAGCSH][0]=phasemod[CSH][0];
          phasemod[SLAGCSH][1]=phasemod[CSH][1];
  */
  /* CaCl2 (in fly ash) */
  /*
          phasemod[CACL2][0]=phasemod[CH][0];
          phasemod[CACL2][1]=phasemod[CH][1];
  */
  /* Friedel's Salt */
  /*
          phasemod[FRIEDEL][0]=phasemod[ETTR][0];
          phasemod[FRIEDEL][1]=phasemod[ETTR][1];
  */
  /* Stratlingite (from fly ash presence) */
  /*
          phasemod[STRAT][0]=phasemod[ETTR][0];
          phasemod[STRAT][1]=phasemod[ETTR][1];
  */
  /* Secondary gypsum (same modulus as regular gypsum) */
  /*
          phasemod[GYPSUMS][0]=phasemod[GYPSUM][0];
          phasemod[GYPSUMS][1]=phasemod[GYPSUM][1];
  */
  /* CaCO3 (calcite form, Voigt values determined by Brillouin spectroscopy,
   * Chen et al. 2001) */
  /*
          phasemod[CACO3][0] = 79.3;
          phasemod[CACO3][1] = 37.4;
  */
  /* Afmc (same as C-S-H for now) */
  /*        phasemod[AFMC][0]=phasemod[CSH][0]; */
  /*        phasemod[AFMC][1]=phasemod[CSH][1]; */
  /* Model C Afmc same as AFM now */
  /*
          phasemod[AFMC][0]=phasemod[AFM][0];
          phasemod[AFMC][1]=phasemod[AFM][1];
  */
  /* Inert aggregate -- assume limestone aggregate */
  /*
          phasemod[INERTAGG][0]= phasemod[CSH][0];
          phasemod[INERTAGG][1]= phasemod[CSH][1];
  */
  /* Absorbed gypsum (in C-S-H) treat as regular gypsum */
  /*
          phasemod[ABSGYP][0]=phasemod[GYPSUM][0];
          phasemod[ABSGYP][1]=phasemod[GYPSUM][1];
  */
  /* Fly ash */
  /*
          phasemod[30][0]=phasemod[AMSIL][0];
          phasemod[30][1]=phasemod[AMSIL][1];
  */
  /* C3A (fly ash) */
  /*
          phasemod[35][0]=phasemod[C3A][0];
          phasemod[35][1]=phasemod[C3A][1];
  */
  /* Empty porosity (no water) */
  /*
          phasemod[EMPTYP][0]=0.0;
          phasemod[EMPTYP][1]=0.0;
  */
  /* Water-filled porosity (change from label of zero in hydration program) */
  /*  input as bulk modulus (1) and shear modulus (2), preserve in do 1144 below
   */
  /*
          phasemod[POROSITY][0]=2.2;
          phasemod[POROSITY][1]=0.0;
  */

  /**************************************************************************
   *  Elastic moduli below are from previous version of elastic.c, prior
   *  to July 2012, when the values were update to those above.  Note that
   *  these values are Young's modulus and Poisson ratio, not bulk and shear
   *  modulus, so they will need to be converted using the for loop at the
   *  end of this list  */

  phasemod[C3S][0] = 117.6;
  phasemod[C3S][1] = 0.314;
  phasemod[C2S][0] = phasemod[C3S][0];
  phasemod[C2S][1] = phasemod[C3S][1];
  phasemod[C3A][0] = phasemod[C3S][0];
  phasemod[C3A][1] = phasemod[C3S][1];
  phasemod[C4AF][0] = phasemod[C3S][0];
  phasemod[C4AF][1] = phasemod[C3S][1];
  phasemod[K2SO4][0] = 44.2;
  phasemod[K2SO4][1] = 0.269;
  phasemod[NA2SO4][0] = 57.1;
  phasemod[NA2SO4][1] = 0.2807;
  phasemod[GYPSUM][0] = 45.7;
  phasemod[GYPSUM][1] = 0.33;
  phasemod[ANHYDRITE][0] = 80.0;
  phasemod[ANHYDRITE][1] = 0.275;
  phasemod[HEMIHYD][0] = 0.5 * (phasemod[GYPSUM][0] + phasemod[ANHYDRITE][0]);
  phasemod[HEMIHYD][1] = 0.5 * (phasemod[GYPSUM][1] + phasemod[ANHYDRITE][1]);
  phasemod[SFUME][0] = phasemod[AMSIL][0] = 72.8;
  phasemod[SFUME][1] = phasemod[AMSIL][1] = 0.167;
  phasemod[INERT][0] = 79.6;
  phasemod[INERT][1] = 0.31;
  phasemod[SLAG][0] = phasemod[C3S][0];
  phasemod[SLAG][1] = phasemod[C3S][1];
  phasemod[ASG][0] = phasemod[AMSIL][0];
  phasemod[ASG][1] = phasemod[AMSIL][1];
  phasemod[CAS2][0] = phasemod[AMSIL][0];
  phasemod[CAS2][1] = phasemod[AMSIL][1];
  phasemod[CH][0] = 42.3;
  phasemod[CH][1] = 0.324;
  phasemod[CSH][0] = 22.4;
  phasemod[CSH][1] = 0.25;
  phasemod[C3AH6][0] = phasemod[CSH][0];
  phasemod[C3AH6][1] = phasemod[CSH][1];
  phasemod[ETTR][0] = phasemod[CSH][0];
  phasemod[ETTR][1] = phasemod[CSH][1];
  phasemod[ETTRC4AF][0] = phasemod[CSH][0];
  phasemod[ETTRC4AF][1] = phasemod[CSH][1];
  phasemod[AFM][0] = phasemod[CH][0];
  phasemod[AFM][1] = phasemod[CH][1];
  phasemod[FH3][0] = phasemod[CSH][0];
  phasemod[FH3][1] = phasemod[CSH][1];
  phasemod[POZZCSH][0] = phasemod[CSH][0];
  phasemod[POZZCSH][1] = phasemod[CSH][1];
  phasemod[SLAGCSH][0] = phasemod[CSH][0];
  phasemod[SLAGCSH][1] = phasemod[CSH][1];
  phasemod[CACL2][0] = phasemod[CH][0];
  phasemod[CACL2][1] = phasemod[CH][1];
  phasemod[FRIEDEL][0] = phasemod[ETTR][0];
  phasemod[FRIEDEL][1] = phasemod[ETTR][1];
  phasemod[STRAT][0] = phasemod[ETTR][0];
  phasemod[STRAT][1] = phasemod[ETTR][1];
  phasemod[GYPSUMS][0] = phasemod[GYPSUM][0];
  phasemod[GYPSUMS][1] = phasemod[GYPSUM][1];
  phasemod[CACO3][0] = 79.6;
  phasemod[CACO3][1] = 0.31;
  phasemod[AFMC][0] = phasemod[AFM][0];
  phasemod[AFMC][1] = phasemod[AFM][1];
  phasemod[INERTAGG][0] = 79.6;
  phasemod[INERTAGG][1] = 0.31;
  phasemod[ABSGYP][0] = phasemod[GYPSUM][0];
  phasemod[ABSGYP][1] = phasemod[GYPSUM][1];
  phasemod[30][0] = phasemod[AMSIL][0];
  phasemod[30][1] = phasemod[AMSIL][1];
  phasemod[35][0] = phasemod[C3A][0];
  phasemod[35][1] = phasemod[C3A][1];
  phasemod[EMPTYP][0] = 0.0;
  phasemod[EMPTYP][1] = 0.0;
  phasemod[POROSITY][0] = 2.0;
  phasemod[POROSITY][1] = 0.0;

  for (ijk = 1; ijk <= nphase; ijk++) {
    save = phasemod[ijk][0];
    phasemod[ijk][0] = phasemod[ijk][0] / 3. / (1. - 2. * phasemod[ijk][1]);
    phasemod[ijk][1] = save / 2. / (1. + phasemod[ijk][1]);
  }

  /* Compute the average stress and strain in each microstructure.        */
  /* (USER) npoints is the number of microstructures to use. */

  npoints = 1;

  /*  Read in a microstructure in subroutine ppixel, and set up pix(m) */
  /*  with the appropriate phase assignments. */

  ppixel(nphase, &doitz, &nagg1);

  /* (USER)  nx,ny,nz give the size of the lattice */

  nx = Xsyssize;
  ny = Ysyssize;
  nz = Zsyssize;

  /* ns=total number of sites */

  ns = nx * ny * nz;
  /*  (USER) gtest is the stopping criterion, the number  */
  /*  to which the quantity gg=gb*gb is compared. */
  /*  Usually gtest = abc*ns, so that when gg < gtest, the rms value */
  /*  per pixel of gb is less than sqrt(abc).  */
  gtest = (1.e-7) * (double)ns;

  printf("%d %d %d %d\n", nx, ny, nz, ns);
  fflush(stdout);

  /*  Construct the neighbor table, ib(m,n) */

  /*  First construct the 27 neighbor table in terms of delta i, delta j, and */
  /*  delta k information (see Table 3 in manual) */
  /* Leave indices running from 1 to 27 in C code */
  in[0] = 0;
  in[1] = 1;
  in[2] = 1;
  in[3] = 1;
  in[4] = 0;
  in[5] = (-1);
  in[6] = (-1);
  in[7] = (-1);

  jjn[0] = 1;
  jjn[1] = 1;
  jjn[2] = 0;
  jjn[3] = (-1);
  jjn[4] = (-1);
  jjn[5] = (-1);
  jjn[6] = 0;
  jjn[7] = 1;

  for (n = 0; n < 8; n++) {
    kn[n] = 0;
    kn[n + 8] = (-1);
    kn[n + 16] = 1;
    in[n + 8] = in[n];
    in[n + 16] = in[n];
    jjn[n + 8] = jjn[n];
    jjn[n + 16] = jjn[n];
  }
  in[24] = 0;
  in[25] = 0;
  in[26] = 0;
  jjn[24] = 0;
  jjn[25] = 0;
  jjn[26] = 0;
  kn[24] = (-1);
  kn[25] = 1;
  kn[26] = 0;

  /*  Now construct neighbor table according to 1-d labels */
  /*  Matrix ib(m,n) gives the 1-d label of the n'th neighbor (n=0,26) of */
  /*  the node labelled m. */
  printf("\nConstructing neighbor table now... ");
  fflush(stdout);
  nxy = nx * ny;
  for (k = 0; k < nz; k++) {
    for (j = 0; j < ny; j++) {
      for (i = 0; i < nx; i++) {
        m = nxy * k + nx * j + i;
        for (n = 0; n < 27; n++) {
          i1 = i + in[n];
          j1 = j + jjn[n];
          k1 = k + kn[n];
          if (i1 < 0) {
            i1 += nx;
          } else if (i1 >= nx) {
            i1 -= nx;
          }
          if (j1 < 0) {
            j1 += ny;
          } else if (j1 >= ny) {
            j1 -= ny;
          }
          if (k1 < 0) {
            k1 += nz;
          } else if (k1 >= nz) {
            k1 -= nz;
          }
          m1 = nxy * k1 + nx * j1 + i1;
          ib[m][n] = m1;
        }
      }
    }
  }
  printf("done\n");
  fflush(stdout);

  /* Count and output the volume fractions of the different phases */
  count = 0;
  for (i = 0; i < ns; i++) {
    if (pix[i] == C3S)
      count++;
  }
  printf("\nBefore assig, Count C3S = %d", count);
  fflush(stdout);

  assig(ns, nphase);
  for (i = 0; i < nphase; i++) {
    if (prob[i] > 0.0) {
      printf("Phase %d bulk = %lf shear = %lf volume = %lf \n", i,
             phasemod[i][0], phasemod[i][1], prob[i]);
      fflush(stdout);
    }
    sum = sum + prob[i];
  }

  printf("Sum of volume fractions = %f\n", sum);
  fflush(stdout);

  /*  (USER) Set applied strains */
  /*  Actual shear strain applied in do 1050 loop is exy, exz, and eyz as */
  /*  given in the statements below.  The engineering shear strain, by which */
  /*  the shear modulus is usually defined, is twice these values. */

  /*  npoints different loading configurations for ITZ calculation */
  /*  npoints = 6 for FULL elastic stiffness tensor solution, = 1 otherwise */

  if (!doitz)
    npoints = 1;

  for (micro = 0; micro < npoints; micro++) {
    switch (micro) {
    case 0:
      if (npoints == 1) {
        exx = 0.1;
        eyy = 0.1;
        ezz = 0.1;
        exz = 0.1 / 2.;
        eyz = 0.1 / 2.;
        exy = 0.1 / 2.;
      } else {
        exx = 0.1;
        eyy = 0.0;
        ezz = 0.0;
        exz = 0.0;
        eyz = 0.0;
        exy = 0.0;
      }
      break;
    case 1:
      exx = 0.0;
      eyy = 0.1;
      ezz = 0.0;
      exz = 0.0;
      eyz = 0.0;
      exy = 0.0;
      break;
    case 2:
      exx = 0.0;
      eyy = 0.0;
      ezz = 0.1;
      exz = 0.0;
      eyz = 0.0;
      exy = 0.0;
      break;
    case 3:
      exx = 0.0;
      eyy = 0.0;
      ezz = 0.0;
      exz = 0.1 / 2.0;
      eyz = 0.0;
      exy = 0.0;
      break;
    case 4:
      exx = 0.0;
      eyy = 0.0;
      ezz = 0.0;
      exz = 0.0;
      eyz = 0.1 / 2.0;
      exy = 0.0;
      break;
    case 5:
      exx = 0.0;
      eyy = 0.0;
      ezz = 0.0;
      exz = 0.0;
      eyz = 0.0;
      exy = 0.1 / 2.0;
      break;
    }
    /*
if (doitz) {
    printf("Doing Configuration %d ...\n",micro);
    printf("------------------\n",micro);
}
*/
    printf("Applied engineering strains:\n");
    printf("exx   eyy   ezz   exz   eyz   exy\n");
    printf("%lf %lf %lf %lf %lf %lf\n", exx, eyy, ezz, 2. * exz, 2. * eyz,
           2. * exy);
    fflush(stdout);

    /* Set up the elastic modulus variables, finite element stiffness matrices,
     */
    /* the constant, C, and vector, b, required for computing the energy. */
    /*  (USER) If anisotropic elastic moduli tensors are used, these need to be
     */
    /*  input in subroutine femat. */

    femat(nx, ny, nz, ns, nphase);
    printf("C is %lf \n", C);
    fflush(stdout);

    /* Apply chosen strains as a homogeneous macroscopic strain  */
    /* as the initial condition. */

    printf("Applying homogeneous macroscopic strain now... ");
    fflush(stdout);
    for (k = 0; k < nz; k++) {
      for (j = 0; j < ny; j++) {
        for (i = 0; i < nx; i++) {
          m = nxy * k + nx * j + i;
          x = (double)i;
          y = (double)j;
          z = (double)k;
          u[m][0] = x * exx + y * exy + z * exz;
          u[m][1] = x * exy + y * eyy + z * eyz;
          u[m][2] = x * exz + y * eyz + z * ezz;
        }
      }
    }
    printf(" \n...done\n");
    fflush(stdout);

    /*  RELAXATION LOOP */
    /*  (USER) kmax is the maximum number of times dembx will be called, with */
    /*  ldemb conjugate gradient steps performed during each call.  The total */
    /*  number of conjugate gradient steps allowed for a given elastic */
    /*  computation is kmax*ldemb. */
    kmax = 40;
    ldemb = 100;
    /*  Call energy to get initial energy and initial gradient */
    utot = energy(nx, ny, nz, ns);
    /*  gg is the norm squared of the gradient (gg=gb*gb) */
    gg = 0.0;
    for (m3 = 0; m3 < 3; m3++) {
      for (m = 0; m < ns; m++) {
        gg += gb[m][m3] * gb[m][m3];
      }
    }
    printf("Initial energy = %lf gg= %lf gtest = %lf\n", utot, gg, gtest);
    fflush(stdout);

    for (kkk = 0; ((kkk < kmax) && (gg >= gtest)); kkk++) {

      /* Write information to the progress file */

      /*
                      Fprog = filehandler("genmic",Progfilename,"WRITE");
                  fprintf(Fprog,"%d\t%d",kkk,kmax);
                  fclose(Fprog);
      */

      /*  call dembx to go into the conjugate gradient solver */
      /*
      printf("Calling dembx with gg= %lf gtest = %lf\n",gg,gtest);
      fflush(stdout);
      */
      Lstep = dembx(ns, ldemb, kkk);
      ltot += Lstep;
      /*
      printf("Out of dembx, Lstep = %d gg = %lf gtest = %lf\n",Lstep,gg,gtest);
      fflush(stdout);
      */
      /*  Call energy to compute energy after dembx call. If gg < gtest, this */
      /*  will be the final energy.  If gg is still larger than gtest, then this
       */
      /*  will give an intermediate energy with which to check how the  */
      /*  relaxation process is coming along. */
      utot = energy(nx, ny, nz, ns);
      printf("Energy = %lf gg= %lf gtest = %lf\n", utot, gg, gtest);
      printf("Number of conjugate steps = %d\n", ltot);
      fflush(stdout);
      /*  If relaxation process is not finished, continue */
      if (gg > gtest) {
        /*  If relaxation process will continue, compute and output stresses */
        /*  and strains as an additional aid to judge how the  */
        /*  relaxation procedure is progressing. */
        stress(nx, ny, nz, ns, doitz, micro, 0);
        printf("stresses:  xx,yy,zz,xz,yz,xy\n");
        printf("%lf %lf %lf %lf %lf %lf\n", strxxt / (double)ns,
               stryyt / (double)ns, strzzt / (double)ns, strxzt / (double)ns,
               stryzt / (double)ns, strxyt / (double)ns);
        printf("strains:  xx,yy,zz,xz,yz,xy\n");
        printf("%lf %lf %lf %lf %lf %lf \n", sxxt / (double)ns,
               syyt / (double)ns, szzt / (double)ns, sxzt / (double)ns,
               syzt / (double)ns, sxyt / (double)ns);
        fflush(stdout);
      }
    }

    stress(nx, ny, nz, ns, doitz, micro, 1);
    printf("stresses:  xx,yy,zz,xz,yz,xy\n");
    printf("%lf %lf %lf %lf %lf %lf\n", strxxt, stryyt, strzzt, strxzt, stryzt,
           strxyt);
    printf("strains:  xx,yy,zz,xz,yz,xy\n");
    printf("%lf %lf %lf %lf %lf %lf \n", sxxt, syyt, szzt, sxzt, syzt, sxyt);
    fflush(stdout);
  }

  if (npoints == 1) {

    /***
     *	Compute global elastic moduli
     ***/

    bulk = (strxxt + stryyt + strzzt) / (sxxt + syyt + szzt) / 3.;
    shear = (strxyt / sxyt + strxzt / sxzt + stryzt / syzt) / 3.;
    young = 9. * bulk * shear / (3. * bulk + shear);
    pois = (3. * bulk - 2. * shear) / 2. / (3. * bulk + shear);
    printf("\nEFFECTIVE MODULI:\n\n");
    printf("bulk_modulus %lf\n", bulk);
    printf("shear_modulus %lf\n", shear);
    printf("Youngs_modulus %lf\n", young);
    printf("Poissons_ratio %lf\n", pois);
    printf("\n*****\n");
    printf("\nRELATIVE CONTRIBUTIONS OF EACH PHASE:\n");

    outfile = filehandler("cpelas", Outfilename, "WRITE");
    if (!outfile) {
      printf("\n\nWARNING:  Could not open output file %s", Outfilename);
    } else {

      fprintf(outfile, "CEMENT PASTE ELASTIC MODULI:\n");
      fprintf(outfile, "\tbulk_modulus %lf GPa\n", bulk);
      fprintf(outfile, "\tshear_modulus %lf GPa\n", shear);
      fprintf(outfile, "\tYoungs_modulus %lf GPa\n", young);
      fprintf(outfile, "\tPoissons_ratio %lf\n", pois);
      fclose(outfile);
    }

    /***
     *	Compute contribution to the global moduli
     *	of each phase in the microstructure
     ***/

    outfile = filehandler("cpelas", PCfilename, "WRITE");
    if (!outfile) {
      printf("\n\nWARNING:  Could not open output file %s", PCfilename);
    }
    for (i = 0; i < NSP; i++) {
      if (prob[i] > pthresh) {
        stressall[i][12] =
            (stressall[i][0] + stressall[i][1] + stressall[i][2]) /
            (exx + eyy + ezz);
        stressall[i][12] /= 3.0;

        stressall[i][13] = (stressall[i][3] / exy);
        stressall[i][13] += (stressall[i][4] / exz);
        stressall[i][13] += (stressall[i][5] / eyz);
        stressall[i][13] /= 6.0; /* Divide by extra 2.0 because global shear
                                    strains are doubled */

        stressall[i][14] = (9.0 * stressall[i][12] * stressall[i][13]) /
                           ((3.0 * stressall[i][12]) + stressall[i][13]);

        stressall[i][15] =
            ((3.0 * stressall[i][12]) - (2.0 * stressall[i][13])) /
            (2.0 * ((3.0 * stressall[i][12]) + stressall[i][13]));

        id2phasename(i, phasename);
        printf("Phase %s\n", phasename);
        printf("\tVfrac %lf\n", prob[i]);
        printf("\tBulk_Modulus %lf\n", stressall[i][12]);
        printf("\tBulk_Modulus_Fraction %lf\n", stressall[i][12] / bulk);
        printf("\tShear_Modulus %lf\n", stressall[i][13]);
        printf("\tShear_Modulus_Fraction %lf\n", stressall[i][13] / shear);
        printf("\tYoung_Modulus %lf\n", stressall[i][14]);
        printf("\tYoung_Modulus_Fraction %lf\n\n", stressall[i][14] / young);

        if (outfile != NULL) {
          fprintf(outfile, "Phase %s\n", phasename);
          fprintf(outfile, "\tVfrac %lf\n", prob[i]);
          fprintf(outfile, "\tBulk_Modulus %lf\n", stressall[i][12]);
          fprintf(outfile, "\tBulk_Modulus_Fraction %lf\n",
                  stressall[i][12] / bulk);
          fprintf(outfile, "\tShear_Modulus %lf\n", stressall[i][13]);
          fprintf(outfile, "\tShear_Modulus_Fraction %lf\n",
                  stressall[i][13] / shear);
          fprintf(outfile, "\tYoung_Modulus %lf\n", stressall[i][14]);
          fprintf(outfile, "\tYoung_Modulus_Fraction %lf\n\n",
                  stressall[i][14] / young);
        }
      }
    }

    if (outfile != NULL)
      fclose(outfile);

    /***
     *	Now, if ITZ calculation turned on, then we have to output
     *	the layer-by-layer average values of K and G
     ***/

    /***
     *	Now average on both sides of aggregate, plot 1st pixel at x = 0.5,
     *	2nd pixel at x = 1.5, etc.
     ***/

    if ((doitz) && (nagg1 > 0)) {
      outfile = filehandler("cpelas", Layerfilename, "WRITE");
      if (!outfile) {
        printf("\n\nWARNING:  Could not open output file %s", Layerfilename);
      }
      printf("*****\n\n");
      printf("LAYER_DATA:\n\n");
      xj = -0.5;
      for (i = nagg1 - 1; i >= 0; i--) {
        xj += 1.0;
        kk = 0.50 * (K[i] + K[Xsyssize - i - 1]);
        gg = 0.50 * (G[i] + G[Xsyssize - i - 1]);
        young = 9. * kk * gg / (3. * kk + gg);
        pois = (3. * kk - 2. * gg) / 2. / (3. * kk + gg);
        printf("%.1f %.4f %.4f %.4f %.4f\n", xj, kk, gg, young, pois);
        fprintf(outfile, "%.1f %.4f %.4f %.4f %.4f\n", xj, kk, gg, young, pois);
      }
      printf("END");
      fclose(outfile);
    }

  } else {

    /***
     *	Only uncomment this call to modlayer if we are trying to
     *	solve the full elastic stiffness tensor (all 36 components)
     ***/
    /*
    modlayer(&nagg1);
    */
  }

  printf("\nDone with cement paste calculations.");
  if (doitz) {
    oval = concelas(nagg1, bulk, shear);
  }

  freeallmem();
  return (0);
}

/************************ concelas.c ***************************************/
/* BACKGROUND                                                              */
/* This function takes elastic data on a cement binder, together with      */
/* grading and elastic properties of coarse and fine aggregate, to         */
/* estimate the effective elastic properties and compressive strength of   */
/* the concrete or mortar                                                  */
/*                                                                         */
/* Programmer:  Dr. Edward J. Garboczi (NIST/BFRL)- (301)975.6708          */
/* C-conversion by Dr. Jeffrey W. Bullard           (301)975.5725          */
/*                                                                         */
/***************************************************************************/
int concelas(int nagg1, double bulkmod, double shearmod) {
  register int i, j, m;
  int itzpix, numfinebins[NUMFINESOURCES], numfinebinstot, cnt;
  int num_fine_sources, num_coarse_sources;
  int finebegin[NUMFINESOURCES], fineend[NUMFINESOURCES];
  int coarsebegin[NUMCOARSESOURCES], coarseend[NUMCOARSESOURCES];
  double poisscem, kcem, ecem, gcem, fine_agg_vf[NUMFINESOURCES];
  double coarse_agg_vf[NUMCOARSESOURCES], eitz, itzwidth, poissitz, kitz, gitz,
      tdval, val;
  char ch, buff[MAXSTRING], instring[MAXSTRING];
  char buff1[MAXSTRING];
  char cempsdfile[MAXSTRING];
  char coarsegfile[MAXSTRING], finegfile[MAXSTRING];
  double sum, kfine, kcoarse, gfine, gcoarse, finevftot, coarsevftot;
  double aggfrac, airfrac;
  double target_matrix_vf;
  double k, g, ksave[RKITS], gsave[RKITS], xx[RKITS];
  double q1, q2, q3, q4, q5, r1, r2, r3, r4, r5, xe, xg, xk, z;
  const double h = -0.0010;
  double kk, gg, mortar_cube_strngth, concrete_cube_strngth, cylinder_strngth;
  FILE *fpout, *gfile, *cempsd;

  /* Initialize global arrays */

  for (i = 0; i < MAXSIZECLASSES; i++) {
    K_concelas[i] = 0.0;
    G_concelas[i] = 0.0;
    Ki_concelas[i] = 0.0;
    Gi_concelas[i] = 0.0;
    Diam_concelas[i] = 0.0;
    Vf_concelas[i] = 0.0;
  }

  /* Initialize local arrays */

  for (i = 0; i < RKITS; i++) {
    ksave[i] = gsave[i] = xx[i] = 0.0;
  }

  for (i = 0; i < NUMFINESOURCES; i++) {
    fine_agg_vf[i] = 0.0;
    numfinebins[i] = 0;
    finebegin[i] = fineend[i] = 0;
  }

  for (i = 0; i < NUMCOARSESOURCES; i++) {
    coarse_agg_vf[i] = 0.0;
    coarsebegin[i] = coarseend[i] = 0;
  }

  fpout = filehandler("concelas", Outfilename, "APPEND");
  if (!fpout) {
    bailout("concelas", "Could not open file Concrete.dat");
    return (1);
  }

  printf("\n\nEnter fully resolved name of cement PSD file: ");
  read_string(cempsdfile, sizeof(cempsdfile));
  printf("\n%s\n", cempsdfile);
  cempsd = filehandler("concelas", cempsdfile, "READ");
  if (!cempsd) {
    sprintf(buff1, "Could not open cement PSD file %s", cempsdfile);
    warning("concelas", buff1);
    warning("concelas", "Using median cement PSD of 15 micrometers");
    itzwidth = 10.0;
  } else {
    itzwidth = mediansize(cempsd);
    fclose(cempsd);
  }

  if (nagg1 > 0) { /*  Aggregate must be present for this to execute */

    /* Convert itzwidth to cement paste image pixel widths */
    itzpix = (int)((itzwidth / Res) + 0.5);
    printf("\n\nCalculated ITZ width is %f micrometers (%d voxels)\n", itzwidth,
           itzpix);

    /* Knowing the ITZ width, find average values of
     * the bulk and shear moduli inside the ITZ */

    kk = gg = 0.0;
    for (i = nagg1 - 1; i > (nagg1 - itzpix - 1); i--) {
      kk += 0.50 * (K[i] + K[Xsyssize - i - 1]);
      gg += 0.50 * (G[i] + G[Xsyssize - i - 1]);
    }

    kk *= (1.0 / ((double)(itzpix)));
    gg *= (1.0 / ((double)(itzpix)));
    kitz = kk;
    gitz = gg;

    eitz = (9.0 * kitz * gitz) / ((3.0 * kitz) + gitz);
    poissitz = ((3.0 * kitz) - (2.0 * gitz)) / (2.0 * ((3.0 * kitz) + gitz));

    printf("\nCalculated bulk modulus of ITZ = %f", kitz);
    printf("\nCalculated shear modulus of ITZ = %f", gitz);

    /* Now find values for bulk and shear moduli of bulk paste */

    kk = gg = 0.0;
    for (i = (nagg1 - itzpix - 1); i >= 0; i--) {
      kk += 0.50 * (K[i] + K[Xsyssize - i - 1]);
      gg += 0.50 * (G[i] + G[Xsyssize - i - 1]);
    }

    kk *= (1.0 / ((double)(nagg1 - itzpix)));
    gg *= (1.0 / ((double)(nagg1 - itzpix)));
    kcem = kk;
    gcem = gg;

  } else {

    printf("\nNo aggregate found in microstructure...");
    itzwidth = 0.0;
    kitz = bulkmod;
    gitz = shearmod;
    kcem = bulkmod;
    gcem = shearmod;
  }

  ecem = (9.0 * kcem * gcem) / ((3.0 * kcem) + gcem);
  poisscem = ((3.0 * kcem) - (2.0 * gcem)) / (2.0 * ((3.0 * kcem) + gcem));
  printf("\nCalculated bulk modulus of ITZ = %f", kitz);
  printf("\nCalculated shear modulus of ITZ = %f", gitz);
  printf("\nCalculated bulk modulus of bulk paste = %f", kcem);
  printf("\nCalculated shear modulus of bulk paste = %f\n", gcem);

  /* Convert itzwidth to mm */
  itzwidth *= 0.001;
  printf("\nITZ width is %f mm\n", itzwidth);

  /*
  printf("\nEnter the number of sources of fine aggregate: ");
  read_string(buff1,sizeof(buff1));
  num_fine_sources = atoi(buff1);
  if (num_fine_sources < 0) num_fine_sources = 0;
  if (num_fine_sources > (int)NUMFINESOURCES) num_fine_sources =
  (int)NUMFINESOURCES;
  */

  sum = 0.0;
  N_concelas = 0;
  finevftot = coarsevftot = 0.0;
  num_fine_sources = num_coarse_sources = 0;
  for (m = 0; m < (int)NUMFINESOURCES; m++) {
    printf("\nEnter volume fraction of fine aggregate %d: ", m + 1);
    read_string(buff, sizeof(buff));
    val = atof(buff);
    if (val > 0) {
      fine_agg_vf[num_fine_sources] = val;
      finevftot += fine_agg_vf[num_fine_sources];
      printf("%f", fine_agg_vf[num_fine_sources]);

      finebegin[num_fine_sources] = N_concelas;
      printf("\nFine aggregate grading file must have three ");
      printf("\ncolumns of data: one for sieve description, one for ");
      printf("\nopening diameter (mm) and one for fraction retained.");
      printf("\nThe columns must be TAB-DELIMITED.");
      printf("\nEnter fully-resolved name of fine agg grading file: ");
      read_string(finegfile, sizeof(finegfile));
      printf("\n%s\n", finegfile);
      gfile = filehandler("concelas", finegfile, "READ");
      if (!gfile) {
        bailout("concelas", "Could not open fine grading file");
        return (1);
      }
      printf("\nEnter BULK modulus for fine aggregate %d (in GPa): ",
             num_fine_sources + 1);
      read_string(buff, sizeof(buff));
      kfine = atof(buff);
      printf("%f", kfine);
      printf("\nEnter SHEAR modulus for fine aggregate %d (in GPa): ",
             num_fine_sources + 1);
      read_string(buff, sizeof(buff));
      gfine = atof(buff);
      printf("%f", gfine);

      ch = getc(gfile);
      if (ch != '0' && ch != '1' && ch != '2' && ch != '3' && ch != '4' &&
          ch != 5 && ch != 6 && ch != 7 && ch != 8 && ch != 9) {
        fread_string(gfile, instring); /* read and discard header */
      } else {
        rewind(gfile);
      }
      cnt = 0;
      while (!feof(gfile)) {
        for (i = 0; i < 3; i++) {
          j = 0;
          ch = getc(gfile);
          if (!feof(gfile)) {
            while (ch != '\t' && ch != '\n' && !feof(gfile)) {
              buff[j] = ch;
              ch = getc(gfile);
              j++;
            }
            buff[j] = '\0';
            if (i == 1) {
              Diam_concelas[N_concelas] = atof(buff);
            } else if (i == 2) {
              Vf_concelas[N_concelas] =
                  fine_agg_vf[num_fine_sources] * (atof(buff));
              sum += Vf_concelas[N_concelas];
              K_concelas[N_concelas] = kfine;
              Ki_concelas[N_concelas] = kfine;
              G_concelas[N_concelas] = gfine;
              Gi_concelas[N_concelas] = gfine;
              printf("\n%d: Diam = %f, Vf = %f, sum = %f", N_concelas,
                     Diam_concelas[N_concelas], Vf_concelas[N_concelas], sum);
              N_concelas++;
              cnt++;
            }
          }
        }
      }

      fclose(gfile);
      numfinebins[num_fine_sources] = cnt;
      fineend[num_fine_sources] = N_concelas;
      num_fine_sources++;
    }
  }
  numfinebinstot = N_concelas;

  /*
  printf("\nEnter the number of sources of coarse aggregate: ");
  read_string(buff1,sizeof(buff1));
  num_coarse_sources = atoi(buff1);
  if (num_coarse_sources < 0) num_coarse_sources = 0;
  if (num_coarse_sources > (int)NUMCOARSESOURCES) num_coarse_sources =
  (int)NUMCOARSESOURCES;
  */

  for (m = 0; m < (int)NUMCOARSESOURCES; m++) {
    printf("\n\nEnter volume fraction of coarse aggregate %d: ",
           num_coarse_sources + 1);
    read_string(buff, sizeof(buff));
    val = atof(buff);
    if (val > 0) {
      coarse_agg_vf[num_coarse_sources] = val;
      coarsevftot = coarse_agg_vf[num_coarse_sources];
      printf("%f", coarse_agg_vf[num_coarse_sources]);

      coarsebegin[num_coarse_sources] = N_concelas;
      printf("\nCoarse aggregate grading file must have three ");
      printf("\ncolumns of data: one for sieve description, one for ");
      printf("\nopening diameter (mm) and one for fraction retained.");
      printf("\nThe columns must be TAB-DELIMITED.");
      printf("\n\nEnter fully-resolved name of coarse agg grading file: ");
      read_string(coarsegfile, sizeof(coarsegfile));
      printf("\n%s\n", coarsegfile);
      gfile = filehandler("concelas", coarsegfile, "READ");
      if (!gfile) {
        bailout("concelas", "Could not open coarse grading file");
        return (1);
      }
      printf("\nEnter BULK modulus for coarse aggregate %d (in GPa): ",
             num_coarse_sources + 1);
      read_string(buff, sizeof(buff));
      kcoarse = atof(buff);
      printf("%f", kcoarse);
      printf("\nEnter SHEAR modulus for coarse aggregate %d (in GPa): ",
             num_coarse_sources + 1);
      read_string(buff, sizeof(buff));
      gcoarse = atof(buff);
      printf("%f", gcoarse);

      ch = getc(gfile);
      if (ch != '0' && ch != '1' && ch != '2' && ch != '3' && ch != '4' &&
          ch != 5 && ch != 6 && ch != 7 && ch != 8 && ch != 9) {
        fread_string(gfile, instring); /* read and discard header */
      } else {
        rewind(gfile);
      }
      while (!feof(gfile)) {
        for (i = 0; i < 3; i++) {
          j = 0;
          ch = getc(gfile);
          if (!feof(gfile)) {
            while (ch != '\t' && ch != '\n' && !feof(gfile)) {
              buff[j] = ch;
              ch = getc(gfile);
              j++;
            }
            buff[j] = '\0';
            if (i == 1) {
              Diam_concelas[N_concelas] = atof(buff);
            } else if (i == 2) {
              Vf_concelas[N_concelas] =
                  coarse_agg_vf[num_coarse_sources] * (atof(buff));
              sum += Vf_concelas[N_concelas];
              K_concelas[N_concelas] = kcoarse;
              Ki_concelas[N_concelas] = kcoarse;
              G_concelas[N_concelas] = gcoarse;
              Gi_concelas[N_concelas] = gcoarse;
              printf("\n%d: Diam = %f, Vf = %f, sum = %f", N_concelas,
                     Diam_concelas[N_concelas], Vf_concelas[N_concelas], sum);
              N_concelas++;
            }
          }
        }
      }

      fclose(gfile);
      coarseend[num_coarse_sources] = N_concelas;
      num_coarse_sources++;
    }
  }

  /* Bubble sort on each aggregate type individually, then assigne average
   * diameters */

  for (m = 0; m < num_fine_sources; m++) {
    for (i = finebegin[m]; i < fineend[m]; i++) {
      for (j = (i + 1); j < fineend[m]; j++) {
        if (Diam_concelas[i] < Diam_concelas[j]) {
          tdval = Diam_concelas[i];
          Diam_concelas[i] = Diam_concelas[j];
          Diam_concelas[j] = tdval;
          tdval = Vf_concelas[i];
          Vf_concelas[i] = Vf_concelas[j];
          Vf_concelas[j] = tdval;
          tdval = K_concelas[i];
          K_concelas[i] = K_concelas[j];
          K_concelas[j] = tdval;
          tdval = Ki_concelas[i];
          Ki_concelas[i] = Ki_concelas[j];
          Ki_concelas[j] = tdval;
          tdval = G_concelas[i];
          G_concelas[i] = G_concelas[j];
          G_concelas[j] = tdval;
          tdval = Gi_concelas[i];
          Gi_concelas[i] = Gi_concelas[j];
          Gi_concelas[j] = tdval;
        }
      }
    }
  }

  for (m = 0; m < num_coarse_sources; m++) {
    for (i = coarsebegin[m]; i < coarseend[m]; i++) {
      for (j = (i + 1); j < coarseend[m]; j++) {
        if (Diam_concelas[i] < Diam_concelas[j]) {
          tdval = Diam_concelas[i];
          Diam_concelas[i] = Diam_concelas[j];
          Diam_concelas[j] = tdval;
          tdval = Vf_concelas[i];
          Vf_concelas[i] = Vf_concelas[j];
          Vf_concelas[j] = tdval;
          tdval = K_concelas[i];
          K_concelas[i] = K_concelas[j];
          K_concelas[j] = tdval;
          tdval = Ki_concelas[i];
          Ki_concelas[i] = Ki_concelas[j];
          Ki_concelas[j] = tdval;
          tdval = G_concelas[i];
          G_concelas[i] = G_concelas[j];
          G_concelas[j] = tdval;
          tdval = Gi_concelas[i];
          Gi_concelas[i] = Gi_concelas[j];
          Gi_concelas[j] = tdval;
        }
      }
    }
  }

  /* Now sorted within source, assign average diameters */
  /* Actual diameter in a sieve should be something like the average
   * between the sieve opening and the opening of the next largest
   * sieve */

  for (m = 0; m < num_fine_sources; m++) {
    for (i = finebegin[m] + 1; i < fineend[m]; i++) {
      Diam_concelas[i] = 0.5 * (Diam_concelas[i] + Diam_concelas[i - 1]);
    }
    Diam_concelas[finebegin[m]] *= 1.10;
  }

  for (m = 0; m < num_coarse_sources; m++) {
    for (i = coarsebegin[m] + 1; i < coarseend[m]; i++) {
      Diam_concelas[i] = 0.5 * (Diam_concelas[i] + Diam_concelas[i - 1]);
    }
    Diam_concelas[coarsebegin[m]] *= 1.10;
  }

  /* Final bubble sort on entire aggregate distribution */

  for (i = 0; i < N_concelas - 1; i++) {
    for (j = (i + 1); j < N_concelas; j++) {
      if (Diam_concelas[i] < Diam_concelas[j]) {
        tdval = Diam_concelas[i];
        Diam_concelas[i] = Diam_concelas[j];
        Diam_concelas[j] = tdval;
        tdval = Vf_concelas[i];
        Vf_concelas[i] = Vf_concelas[j];
        Vf_concelas[j] = tdval;
        tdval = K_concelas[i];
        K_concelas[i] = K_concelas[j];
        K_concelas[j] = tdval;
        tdval = Ki_concelas[i];
        Ki_concelas[i] = Ki_concelas[j];
        Ki_concelas[j] = tdval;
        tdval = G_concelas[i];
        G_concelas[i] = G_concelas[j];
        G_concelas[j] = tdval;
        tdval = Gi_concelas[i];
        Gi_concelas[i] = Gi_concelas[j];
        Gi_concelas[j] = tdval;
      }
    }
  }

  if (fabs(sum - 1.0) > 0.005) {
    printf("\n\nVolume fraction data sums to %.4f ...", sum);
    printf("\nWill now renormalize the data to 1.0 ...");

    for (i = 0; i < N_concelas; i++) {
      Vf_concelas[i] /= sum;
    }
  }

  /* Print final normalized total aggregate grading */

  printf("\n\nNORMALIZED AGGREGATE GRADING:");
  for (i = 0; i < N_concelas; i++) {
    printf("\nDiam = %f Vf = %f", Diam_concelas[i], Vf_concelas[i]);
  }
  printf("\n");

  aggfrac = finevftot + coarsevftot;
  printf("\nTotal aggregate volume fraction = %f", aggfrac);
  fprintf(fpout, "\nCONCRETE ELASTIC MODULI INFORMATION:\n");
  fprintf(fpout, "\taggfrac: %f\n", aggfrac);

  printf("\n\nEnter the volume fraction of air: ");
  read_string(buff, sizeof(buff));
  airfrac = atof(buff);
  printf("\n%f, Setting it to zero now...", airfrac);
  fprintf(fpout, "\tairfrac: %f\n", airfrac);

  for (i = 0; i < N_concelas; i++) {
    Vf_concelas[i] *= (aggfrac / (aggfrac + airfrac));
  }
  Diam_concelas[N_concelas] = 0.04;
  K_concelas[N_concelas] = 0.0;
  G_concelas[N_concelas] = 0.0;
  Ki_concelas[N_concelas] = 0.0;
  Gi_concelas[N_concelas] = 0.0;
  Vf_concelas[N_concelas] = airfrac / (aggfrac + airfrac);
  target_matrix_vf = 1.0 - (aggfrac + airfrac);

  effective(itzwidth, kitz, gitz);

  k = kcem;
  g = gcem;
  ksave[0] = k;
  gsave[0] = g;
  xx[0] = 1.0;

  for (i = 0; i < RKITS; i++) {

    xx[i + 1] = 1.0 + ((double)(i + 1) * h);

    slope(&kk, &gg, k, g);
    q1 = -h * g * gg / xx[i];
    r1 = -h * k * kk / xx[i];
    printf("\n\t Iteration %d: q1 = %f, r1 = %f", i, q1, r1);

    slope(&kk, &gg, k + r1 / 2.0, g + q1 / 2.0);
    q2 = -h * (g + q1 / 2.0) * gg / (xx[i] + (0.50 * h));
    r2 = -h * (k + r1 / 2.0) * kk / (xx[i] + (0.50 * h));
    printf("\n\t Iteration %d: q2 = %f, r2 = %f", i, q2, r2);

    slope(&kk, &gg, k + r2 / 2.0, g + q2 / 2.0);
    q3 = -h * (g + q2 / 2.0) * gg / (xx[i] + (0.50 * h));
    r3 = -h * (k + r2 / 2.0) * kk / (xx[i] + (0.50 * h));
    printf("\n\t Iteration %d: q3 = %f, r3 = %f", i, q3, r3);

    slope(&kk, &gg, k + r3, g + q3);
    q4 = -h * (g + q3) * gg / (xx[i] + h);
    r4 = -h * (k + r3) * kk / (xx[i] + h);
    printf("\n\t Iteration %d: q4 = %f, r4 = %f", i, q4, r4);

    q5 = (q1 + (2.0 * q2) + (2.0 * q3) + q4) / 6.0;
    r5 = (r1 + (2.0 * r2) + (2.0 * r3) + r4) / 6.0;
    printf("\n\t Iteration %d: q5 = %f, r5 = %f", i, q5, r5);

    g += q5;
    k += r5;

    xe = 1.0 / (((1.0 / k) + (3.0 / g)) / 9.0);

    gsave[i + 1] = g;
    ksave[i + 1] = k;
    xk = k;
    xg = g;
    printf("\n\t Iteration %d: k = %f, g = %f", i, k, g);
    fflush(stdout);
    if (xx[i + 1] < target_matrix_vf) {
      z = (target_matrix_vf - xx[i]) / (xx[i + 1] - xx[i]);
      xg = gsave[i] + (z * (gsave[i + 1] - gsave[i]));
      xk = ksave[i] + (z * (ksave[i + 1] - ksave[i]));
      xe = 1.0 / (((1.0 / xk) + (3.0 / xg)) / 9.0);
      break;
    }
  }

  /*  Fit for MORTAR cube strength below comes from Luca Valentini, U. Padua */
  /* mortar_cube_strngth = 0.003315 * pow(xe,2.642); */

  /*  Fit for MORTAR cube strength below is for SCG mortars only prior to 2012
   */
  /*  Re-fit February 2013 */
  mortar_cube_strngth = 5.0e-4 * pow(xe, 3.18577);

  /*  Fit for CONCRETE cube strength below comes from Pichet S., SCG/SRI */
  /*  Re-fit February 2013 */
  /*  Re-fit again 20 March 2013 */
  concrete_cube_strngth = 5.0e-4 * pow(xe, 3.0586);

  /*  Fit for CONCRETE cylinder strength below comes from Pichet S., SCG/SRI */
  /*  Re-fit February 2013 */
  /*  Re-fit again 20 March 2013 */
  cylinder_strngth = 3.0e-4 * pow(xe, 3.0586);

  fprintf(fpout, "\tMatrix_vol_frac: %.4f\n", target_matrix_vf);
  fprintf(fpout, "\tEff_Young_mod: %.4f GPa\n", xe);
  fprintf(fpout, "\tEff_Shear_mod: %.4f GPa\n", xg);
  fprintf(fpout, "\tEff_Bulk_mod: %.4f GPa\n", xk);
  fprintf(fpout,
          "\tMortar_Cylinder_Compressive_strength (power fit): %.4f MPa\n",
          cylinder_strngth);
  fprintf(fpout, "\tMortar_Cube_Compressive_strength (power fit): %.4f MPa\n",
          mortar_cube_strngth);
  fprintf(fpout, "\tConcrete_Cube_Compressive_strength (power fit): %.4f MPa\n",
          concrete_cube_strngth);
  fprintf(fpout,
          "\tConcrete_Cylinder_Compressive_strength (0.62*cube): %.4f MPa\n",
          concrete_cube_strngth * 0.624);
  fclose(fpout);
  return (0);
}

void effective(double itzwidth, double kitz, double gitz) {
  register int i;
  double ba, c, nui, nuitz, geff, eta1, eta2, eta3, aa, bb, cc, gg, arg;

  printf("\nIn function effective:");
  nuitz = 0;
  for (i = 0; i <= N_concelas; i++) {

    ba = Diam_concelas[i] / (Diam_concelas[i] + 2.0 * itzwidth);
    c = pow(ba, 3.0);

    if (i == N_concelas) {
      nui = 0.4;
    } else {
      nui = ((3.0 * Ki_concelas[i]) - (2.0 * Gi_concelas[i])) /
            (2.0 * ((3.0 * Ki_concelas[i]) + Gi_concelas[i]));

      nuitz = ((3.0 * kitz) - (2.0 * gitz)) / (2.0 * ((3.0 * kitz) + gitz));
    }
    K_concelas[i] = c * (Ki_concelas[i] - kitz) /
                    (1.0 + (1.0 - c) * (Ki_concelas[i] - kitz) /
                               (kitz + (4.0 * gitz / 3.0)));

    K_concelas[i] += kitz;

    printf("\nK_concelas[%d] = %f, nui = %f, nuitz = %f", i, K_concelas[i], nui,
           nuitz);

    geff = G_concelas[i] / gitz - 1.0;
    printf(", geff[%d] = %f", i, geff);

    eta1 =
        geff * (7.0 - 10.0 * nuitz) * (7.0 + 5.0 * nui) + 105.0 * (nui - nuitz);

    eta2 = geff * (7.0 + 5.0 * nui) + 35.0 * (1.0 - nui);

    eta3 = geff * (8.0 - 10.0 * nuitz) + 15.0 * (1.0 - nuitz);

    aa = 8.0 * geff * (4.0 - 5.0 * nuitz) * eta1 * pow(c, (10.0 / 3.0));
    aa -=
        (2.0 * (63.0 * geff * eta2 + 2.0 * eta1 * eta3) * pow(c, (7.0 / 3.0)));

    aa += (252.0 * geff * eta2 * pow(c, (5.0 / 3.0)));

    aa -= (50.0 * geff * (7.0 - 12.0 * nuitz + 8.0 * nuitz * nuitz) * eta2 * c);

    aa += (4.0 * (7.0 - 10.0 * nuitz) * eta2 * eta3);

    bb = (-2.0 * geff * (1.0 - 5.0 * nuitz) * eta1 * pow(c, (10.0 / 3.0)));

    bb +=
        (2.0 * (63.0 * geff * eta2 + 2.0 * eta1 * eta3) * pow(c, (7.0 / 3.0)));

    bb -= (252.0 * geff * eta2 * pow(c, (5.0 / 3.0)));

    bb += (75.0 * geff * (3.0 - nuitz) * eta2 * nuitz * c);

    bb += (1.50 * (15.0 * nuitz - 7.0) * eta2 * eta3);

    cc = 4.0 * geff * (5.0 * nuitz - 7.0) * eta1 * pow(c, (10.0 / 3.0));

    cc -=
        (2.0 * (63.0 * geff * eta2 + 2.0 * eta1 * eta3) * pow(c, (7.0 / 3.0)));

    cc += (252.0 * geff * eta2 * pow(c, (5.0 / 3.0)));

    cc += (25.0 * geff * (nuitz * nuitz - 7.0) * eta2 * c);

    cc -= ((7.0 + 5.0 * nuitz) * eta2 * eta3);

    arg = (4.0 * bb * bb) - (4.0 * aa * cc);
    if ((aa != 0.0) && (arg >= 0.0)) {
      gg = (-2.0 * bb + sqrt(arg)) / (2.0 * aa);
    } else {
      gg = 0.0;
    }

    G_concelas[i] = gg * gitz;
    printf(", G_concelas[%d] = %f", i, G_concelas[i]);
  }
  fflush(stdout);

  return;
}

void slope(double *kk, double *gg, double k, double g) {
  int i;
  double q = (4.0 / 3.0);
  double t = (8.0 / 9.0);

  *kk = 0.0;
  *gg = 0.0;

  for (i = 0; i <= N_concelas; i++) {
    *kk += (Vf_concelas[i] * ((k + (q * g)) * (K_concelas[i] / k - 1.0) /
                              (K_concelas[i] + (q * g))));
    *gg += (Vf_concelas[i] *
            (5.0 * (k + (q * g)) * (G_concelas[i] - g) /
             (3.0 * g * (k + (t * g)) + 2.0 * G_concelas[i] * (k + 2.0 * g))));
  }

  *kk *= SHAPEFACTOR;
  *gg *= SHAPEFACTOR;

  return;
}
