/*
c  BACKGROUND

c  This program accepts as input a 3-d digital image, converting it
c  into a real conductor network. The conjugate gradient method
c  is used to solve this finite difference representation of Laplace's
c  equation for real conductivity problems.
c  Periodic boundary conditions are maintained.
c  In the comments below, (USER) means that this is a section of code
c  that the user might have to change for his particular problem.
c  Therefore the user is encouraged to search for this string.

c  PROBLEM AND VARIABLE DEFINITION

c  The mathematical problem that the conjugate gradient algorithm solves
c  is the minimization of the quadratic form 1/2 uAu, where
c  u is the vector of voltages, and A is generated from the bond
c  conductances between pixels. Nodes are thought of as being in the
c  center of pixels. The minimization is constrained by maintaining an
c  general direction applied electric field across the sample.
c  The vectors gx,gy,gz are bond conductances, u is the voltage array,
c  and gb,h, and Ah are auxiliary variables, used in subroutine dembx.
c  The vector pix contains the phase labels for each pixel.
c  The small vector a(i) is the volume fraction
c  of the i'th phase, and currx, curry, currz are the total volume-averaged
c  currents in the x,y, and z directions.

c  DIMENSIONS

c  The vectors gx,gy,gz,u,gb,h,Ah,list,pix are all dimensioned
c  ns2 = (nx+2)*(ny+2)*(nz+2).  This number is used, rather than the
c  system size nx x ny x nz, because an extra layer of pixels is
c  put around the system to be able to maintain periodic boundary
c  conditions (see manual, Sec. 3.3). The arrays pix and list are also
c  dimensioned this way.
c  At present the program is set up for up to 100
c  phases, but that can easily be changed by the user, by changing the
c  dimension of sigma, a, and be. Note that be has both dimensions
c  equal to each other. The parameter nphase gives the number of
c  phases being considered. The parameter ntot is the total number
c  of phases possible in the program, and should be equal to the
c  dimension of sigma, a, and be.
c  All arrays are passed to subroutines in the call statements.

c  STRONGLY RECOMMENDED:  READ MANUAL BEFORE USING THE PROGRAM!!

c  (USER)  Change these dimensions for different system sizes.  All
c  dimensions in the subroutines are passed, so do not need to be changed.
c  The dimensions of sigma, a, and be should be equal to the value of ntot.
                                                                */
#include "include/vcctl.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NPHASE OFFSET
#define NPHMAX OFFSET + 1
#define NMIC 1

/* Defines for the conctransport function */
#define NG 120
#define EMT_ITERATIONS 10000
#define SHAPEFACTOR 1.10
#define MAXSIZECLASSES 500
#define MAXAGGTYPES 4
#define NUMFINESOURCES 2
#define NUMCOARSESOURCES 2

/* Global variables */

double *gx, *gy, *u, *gz;
double *gb, *h, *Ah, *Lsigma;
static double currx, curry, currz, sigma[NPHMAX][4];
static double pcurr[NPHMAX][4];
static double a[NPHMAX], be[NPHMAX][NPHMAX][4];
int *pix;
int *list;
int Nsites;
double gtest, ex, ey, ez;
int nx, ny, nz, nx1, nx2, ny1, ny2, nz1, nz2, L22, ns2, nphase, ntot;
int npoints, ic = 0;
int fxyz;
FILE *outfile, *resultsfile, *pcfile;
char Outfolder[MAXSTRING], Resultsfilename[MAXSTRING];
char Filesep;
char Outfilename[MAXSTRING], PCfilename[MAXSTRING], Layerfilename[MAXSTRING];
char filein[MAXSTRING], fileout[MAXSTRING], fileresults[MAXSTRING], ch;

/* Variables for ITZ calculations */
double currxt, curryt, currzt;

int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
float Res = DEFAULTRESOLUTION;
/* VCCTL software version used to create input file */
float Version;

/***
 *	Tiny number that sets the minimum volume fraction
 *	possible for a phase
 ***/
double pthresh;
const double Eps = 1.0e-6;

/* Global variables for conctransport */

double *Xg, *Wg;
double S_conctransport[MAXSIZECLASSES];
double Si_conctransport[MAXSIZECLASSES];
double Diam_conctransport[MAXSIZECLASSES];
double Vf_conctransport[MAXSIZECLASSES];
int N_conctransport;
int Ng;

/* Function declarations for conctransport */

int conctransport(int nagg1, double sigma, double sigmax);
void freallmem_conctransport(void);
void effective(double itzwidth, double sitz);
void slope(double itzwidth, double *ss0, double s1);
int getGausspoints(void);
void legendr(int n, double *x, double *pn, double *pnm1, double *pnp1);

void freeallmem(void) {
  if (!pix)
    free_ivector(pix);
  if (!list)
    free_ivector(list);
  if (!gx)
    free_dvector(gx);
  if (!gy)
    free_dvector(gy);
  if (!gz)
    free_dvector(gz);
  if (!gb)
    free_dvector(gb);
  if (!u)
    free_dvector(u);
  if (!h)
    free_dvector(h);
  if (!Ah)
    free_dvector(Ah);
  if (!Ah)
    free_dvector(Ah);

  return;
}

void ppixel(int *nagg1) {
  FILE *infile;
  int i, j, k, valin, intvalin, ovalin, i1, j1, k1, foundagg;
  int m, m1, temp1, temp0, smallersize;
  char instring[MAXSTRING];

  printf("\nInside ppixel function.\n");
  fflush(stdout);

  foundagg = 0;

  /*  Initialize phase fraction array. */
  for (i = 1; i <= nphase; i++) {
    a[i] = 0.0;
  }

  infile = filehandler("transport", filein, "READ");
  if (!infile) {
    freeallmem();
    exit(1);
  }

  /****
   *	NOTE:  MUST READ
   *			(1) VERSION NUMBER (Version)
   *			(2) SYSTEM SIZE (Xsyssize,Ysyssize,Zsyssize)
   *			(3) SYSTEM RESOLUTION (Res)
   *
   ****/

  printf("Image file opened successfully.\n");
  fflush(stdout);

  if (read_imgheader(infile, &Version, &Xsyssize, &Ysyssize, &Zsyssize, &Res)) {
    fclose(infile);
    bailout("transport", "Error reading image header");
    freeallmem();
    exit(1);
  }

  *nagg1 = Xsyssize;

  /* Use 1-d labelling scheme as shown in manual */
  for (k = 2; k <= nz1; k++) {
    temp0 = (k - 1) * L22;
    for (j = 2; j <= ny1; j++) {
      temp1 = (j - 1) * nx2 + temp0;
      for (i = 2; i <= nx1; i++) {
        m = temp1 + i;
        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        intvalin = convert_id(ovalin, Version);

        /***
         *	If this is an image output from a suspended
         *	hydration run, there will still be diffusing
         *	ants in the microstructure.  These must be
         *	converted to their solid counterparts to be
         *	consistent with the previous way of calculating
         *	formation factor.  Follows exactly the same
         *	convention as disrealnew.c for outputting
         *	intermediate images of the microstructure during
         *	hydration.
         ***/

        switch (intvalin) {
        case DIFFCSH:
          valin = CSH;
          break;
        case DIFFCH:
          valin = CH;
          break;
        case DIFFGYP:
          valin = GYPSUM;
          break;
        case DIFFC3A:
          valin = C3A;
          break;
        case DIFFC4A:
          valin = C3A;
          break;
        case DIFFFH3:
          valin = FH3;
          break;
        case DIFFETTR:
          valin = ETTR;
          break;
        case DIFFCACO3:
          valin = CACO3;
          break;
        case DIFFAS:
          valin = ASG;
          break;
        case DIFFANH:
          valin = ANHYDRITE;
          break;
        case DIFFHEM:
          valin = HEMIHYD;
          break;
        case DIFFCAS2:
          valin = CAS2;
          break;
        case DIFFCACL2:
          valin = CACL2;
          break;
        default:
          valin = intvalin;
          break;
        }

        pix[m] = valin + 1;
        a[pix[m]] += 1.0;
        if (valin == INERTAGG) {
          foundagg = 1;
          if (i < *nagg1)
            *nagg1 = i;
        }
      }
    }
  }

  smallersize = (nz1 - 1) * (ny1 - 1) * (nx1 - 1);
  for (i = 1; i <= nphase; i++) {
    a[i] /= ((double)(smallersize));
  }

  fclose(infile);
  printf("\nClosed infile successfully.\n");

  /* Set nagg1, aggregate slab thickness, to zero if no aggregate was
     discovered in the microstructure */

  if (!foundagg)
    *nagg1 = 0;
  printf("nagg1 = %d\n", *nagg1);

  /*  now map periodic boundaries of pix (see Section 3.3, Figure 3 in manual)
   */
  for (k = 1; k <= nz2; k++) {
    for (j = 1; j <= ny2; j++) {
      for (i = 1; i <= nx2; i++) {
        if ((i <= 1) || (i == nx2) || (j == 1) || (j == ny2) || (k == 1) ||
            (k == nz2)) {
          k1 = k;
          if (k == 1) {
            k1 = k + nz;
          } else if (k == nz2) {
            k1 = k - nz;
          }
          j1 = j;
          if (j == 1) {
            j1 = j + ny;
          } else if (j == ny2) {
            j1 = j - ny;
          }
          i1 = i;
          if (i == 1) {
            i1 = i + nx;
          } else if (i == nx2) {
            i1 = i - nx;
          }

          m = (k - 1) * L22 + (j - 1) * nx2 + i;
          m1 = (k1 - 1) * L22 + (j1 - 1) * nx2 + i1;
          pix[m] = pix[m1];
        }
      }
    }
  }

  /*  Check for wrong phase labels--less than 1 or greater than nphase */

  for (m = 1; m <= ns2; m++) {
    if (pix[m] < 1) {
      fprintf(outfile, "Phase label in pix < 1 --- error at %d \n", m);
      fflush(outfile);
      exit(1);
    } else if (pix[m] > nphase) {
      fprintf(outfile,
              "Phase label in pix[%d] = %d > nphase ( = %d)  --- error at "
              "line %d \n",
              m, pix[m], nphase, m);
      fflush(outfile);
      exit(1);
    }
  }
}

/*  Subroutine that determines the correct bond conductances that are used
  to compute multiplication by the matrix A */

void bond(void) {
  int i, j, k;
  int m, m1, temp0, temp1, temp2;

  /*  Set values of conductor for phase(i,m)--phase(j,m) interface,
   store in array be(i,j,m), m=1,2,3. If either phase i or j
    has zero conductivity in the m'th direction, then be(i,j,m)= 0.0. */

  for (m = 1; m <= 3; m++) {
    for (i = 1; i <= nphase; i++) {
      for (j = 1; j <= nphase; j++) {
        if (sigma[i][m] == 0.0) {
          be[i][j][m] = 0.0;
        } else {
          if (sigma[j][m] == 0.0) {
            be[i][j][m] = 0.0;
          } else {
            be[i][j][m] = 1. / (0.5 / sigma[i][m] + 0.5 / sigma[j][m]);
          }
        }
      }
    }
  }
  fflush(stdout);

  /*  Trim off x and y faces so that no current can flow past periodic
    boundaries.  This step is not really necessary, as the voltages on the
    periodic boundaries will be matched to the corresponding real voltages
    in each conjugate gradient step.  */
  temp1 = ny1 * nx2;
  for (k = 1; k <= nz2; k++) {
    temp0 = (k - 1) * L22;
    for (j = 1; j <= ny2; j++) {
      gx[temp0 + nx2 * j] = 0.0;
    }
    temp2 = temp0 + temp1;
    for (i = 1; i <= nx2; i++) {
      gy[temp2 + i] = 0.0;
    }
  }

  /*  Set up conductor network
     bulk--gz */
  for (k = 1; k <= nz1; k++) {
    temp0 = (k - 1) * L22;
    temp1 = k * L22;
    for (j = 1; j <= ny2; j++) {
      temp2 = (j - 1) * nx2;
      for (i = 1; i <= nx2; i++) {
        m = temp0 + temp2 + i;
        m1 = L22 + m;
        gz[m] = be[pix[m]][pix[m1]][3];
      }
    }
  }

  /*  bulk---gy */
  for (k = 1; k <= nz1; k++) {
    temp0 = (k - 1) * L22;
    for (j = 1; j <= ny1; j++) {
      temp2 = (j - 1) * nx2;
      temp1 = j * nx2;
      for (i = 1; i <= nx2; i++) {
        m = temp0 + temp2 + i;
        m1 = nx2 + m;
        gy[m] = be[pix[m]][pix[m1]][2];
      }
    }
  }

  /*  bulk--gx */
  for (k = 1; k <= nz1; k++) {
    temp0 = (k - 1) * L22;
    for (j = 1; j <= ny2; j++) {
      temp2 = (j - 1) * nx2;
      for (i = 1; i <= nx1; i++) {
        m = temp0 + temp2 + i;
        m1 = m + 1;
        gx[m] = be[pix[m]][pix[m1]][1];
      }
    }
  }

  return;
}

/* The matrix product subroutine */
void prod(void) {
  int i, temp0, temp1, m;
  int j, k;

  /*  Perform basic matrix multiplication, results in incorrect information at
    periodic boundaries. */
  for (i = 1; i <= ns2; i++) {
    gb[i] = 0.0;
  }

  for (i = (L22 + 1); i <= (ns2 - L22); i++) {
    gb[i] = (-u[i]) *
            (gx[i - 1] + gx[i] + gz[i - L22] + gz[i] + gy[i] + gy[i - nx2]);
    gb[i] += gx[i - 1] * u[i - 1] + gx[i] * u[i + 1] +
             gz[i - L22] * u[i - L22] + gz[i] * u[i + L22] +
             gy[i] * u[i + nx2] + gy[i - nx2] * u[i - nx2];
  }

  /*  Correct terms at periodic boundaries (Section 3.3 in manual) */

  /*  x faces */
  for (k = 1; k <= nz2; k++) {
    temp0 = (k - 1) * L22;
    for (j = 1; j <= ny2; j++) {
      temp1 = temp0 + nx2 * (j - 1);
      gb[temp1 + nx2] = gb[temp1 + 2];
      gb[temp1 + 1] = gb[temp1 + nx1];
    }
  }

  /*   y faces */
  for (k = 1; k <= nz2; k++) {
    temp0 = (k - 1) * L22;
    for (i = 1; i <= nx2; i++) {
      gb[temp0 + i] = gb[temp0 + ny * nx2 + i];
      gb[temp0 + ny1 * nx2 + i] = gb[temp0 + nx2 + i];
    }
  }

  /*  z faces  */
  temp0 = nz * L22;
  temp1 = nz1 * L22;
  for (m = 1; m <= L22; m++) {
    gb[m] = gb[m + temp0];
    gb[m + temp1] = gb[m + L22];
  }
}

/* The 2nd matrix product subroutine */
void prod1(void) {
  int i, temp0, temp1, m;
  int j, k;

  /*  Perform basic matrix multiplication, results in incorrect information at
    periodic boundaries. */
  for (i = 1; i <= ns2; i++) {
    Ah[i] = 0.0;
  }

  for (i = (L22 + 1); i <= (ns2 - L22); i++) {
    Ah[i] = (-h[i]) *
            (gx[i - 1] + gx[i] + gz[i - L22] + gz[i] + gy[i] + gy[i - nx2]);
    Ah[i] += gx[i - 1] * h[i - 1] + gx[i] * h[i + 1] +
             gz[i - L22] * h[i - L22] + gz[i] * h[i + L22] +
             gy[i] * h[i + nx2] + gy[i - nx2] * h[i - nx2];
  }

  /*  Correct terms at periodic boundaries (Section 3.3 in manual) */

  /*  x faces */
  for (k = 1; k <= nz2; k++) {
    temp0 = (k - 1) * L22;
    for (j = 1; j <= ny2; j++) {
      temp1 = temp0 + nx2 * (j - 1);
      Ah[temp1 + nx2] = Ah[temp1 + 2];
      Ah[temp1 + 1] = Ah[temp1 + nx1];
    }
  }

  /*   y faces */
  for (k = 1; k <= nz2; k++) {
    temp0 = (k - 1) * L22;
    for (i = 1; i <= nx2; i++) {
      Ah[temp0 + i] = Ah[temp0 + ny * nx2 + i];
      Ah[temp0 + ny1 * nx2 + i] = Ah[temp0 + nx2 + i];
    }
  }

  /*  z faces  */
  temp0 = nz * L22;
  temp1 = nz1 * L22;
  for (m = 1; m <= L22; m++) {
    Ah[m] = Ah[m + temp0];
    Ah[m + temp1] = Ah[m + L22];
  }
}

/*  Subroutine to compute the total current in the x, y, and z directions */
void current(int doitz, int ilast) {
  int i, j, k;
  int m, temp0, temp1;
  double cur1, cur2, cur3;
  double ocurrx, ocurry, ocurrz;
  double ncurry, ncurrz;
  double utotx, outotx;
  double utoty, outoty, nutoty;
  double utotz, outotz, nutotz;

  /*  initialize the volume averaged currents */

  if (ilast) {
    printf("\n\tInitializing current variables to zero");
    fflush(stdout);
  }

  for (i = 1; i < NPHMAX; i++) {
    pcurr[i][0] = 0.0;
    pcurr[i][1] = 0.0;
    pcurr[i][2] = 0.0;
  }

  currx = 0.0;
  curry = 0.0;
  currz = 0.0;
  utotx = 0.0;
  utoty = 0.0;
  utotz = 0.0;

  /*  Only loop over real sites and bonds in order to get true total current */

  if (ilast) {
    printf("\n\tLooping over real sites and bonds");
    fflush(stdout);
  }

  for (i = 2; i <= nx1; i++) {
    if (ilast) {
      printf("\n\t\tx = %d", i);
      fflush(stdout);
    }
    ocurrx = currx;
    ocurry = curry;
    ocurrz = currz;
    outotx = utotx;
    outoty = utoty;
    outotz = utotz;
    for (j = 2; j <= ny1; j++) {
      for (k = 2; k <= nz1; k++) {
        temp0 = (k - 1) * L22;
        temp1 = temp0 + (j - 1) * nx2;
        m = temp1 + i;

        /*  cur1, cur2, cur3 are the currents in one pixel */

        cur1 =
            0.5 * ((u[m - 1] - u[m]) * gx[m - 1] + (u[m] - u[m + 1]) * gx[m]);
        cur2 = 0.5 * ((u[m - nx2] - u[m]) * gy[m - nx2] +
                      (u[m] - u[m + nx2]) * gy[m]);
        cur3 = 0.5 * ((u[m - L22] - u[m]) * gz[m - L22] +
                      (u[m] - u[m + L22]) * gz[m]);
        utotx += 0.5 * ((u[m - 1] - u[m + 1]));
        utoty += 0.5 * ((u[m - nx2] - u[m + nx2]));
        utotz += 0.5 * ((u[m - L22] - u[m + L22]));

        /*  sum pixel currents into volume averages */

        currx += cur1;
        pcurr[pix[m]][0] += cur1 / ((double)fxyz);
        curry += cur2;
        pcurr[pix[m]][1] += cur2 / ((double)fxyz);
        currz += cur3;
        pcurr[pix[m]][2] += cur3 / ((double)fxyz);
      }
    }

    /*  Averaging depends on whether layer averaging (doitz) was chosen or not
     */

    if (doitz && ilast) {

      printf("\n\t\t\taveraging currents");
      fflush(stdout);

      /* Average current over this x layer */
      ncurry = (curry - ocurry) / ((double)L22);
      ncurrz = (currz - ocurrz) / ((double)L22);

      /* Average field over this x layer */
      nutoty = (utoty - outoty) / ((double)L22);
      nutotz = (utotz - outotz) / ((double)L22);

      Lsigma[i] = (1.0 / 2.0) * ((ncurry / nutoty) + (ncurrz / nutotz));
    }
  }

  currx /= (double)fxyz;
  curry /= (double)fxyz;
  currz /= (double)fxyz;
  if (currx < 0.0)
    currx = 0.0;
  if (curry < 0.0)
    curry = 0.0;
  if (currz < 0.0)
    currz = 0.0;
  return;
}

/*  Subroutine that performs the conjugate gradient solution routine to
  find the correct set of nodal voltages */
void dembx(int ndlist, int doitz) {
  double gg, hAh, lambda, gglast, gamma;
  int i, m, k, ncgsteps, icc;

  /*  Note:  voltage gradients are maintained because in the conjugate gradient
    relaxation algorithm, the voltage vector is only modified by adding a
    periodic vector to it. */
  /*  First stage, compute initial value of gradient (gb), initialize h, the
    conjugate gradient direction, and compute norm squared of gradient vector.
  */

  prod();
  for (i = 1; i <= ns2; i++) {
    h[i] = gb[i];
  }

  /*   Variable gg is the norm squared of the gradient vector */
  gg = 0.0;
  for (k = 1; k <= ndlist; k++) {
    m = list[k];
    gg += gb[m] * gb[m];
  }
  fprintf(outfile, "After first stage gg is %lf \n", gg);
  fflush(outfile);
  /*   Second stage, initialize Ah variable, compute parameter lamdba,
    make first change in voltage array, update gradient (gb) vector */
  if (gg >= gtest) {
    prod1();
    hAh = 0.0;
    for (k = 1; k <= ndlist; k++) {
      m = list[k];
      hAh += h[m] * Ah[m];
    }

    lambda = gg / hAh;
    for (i = 1; i <= ns2; i++) {
      u[i] -= lambda * h[i];
      gb[i] -= lambda * Ah[i];
    }

    /*  third stage:  iterate conjugate gradient solution process until
      gg < gtest criterion is satisfied.
      (USER) The parameter ncgsteps is the total number of conjugate gradient
      steps to go through.  Only in very unusual problems, like when the
      conductivity of one phase is much higher than all the rest, will this many
      steps be used. */
    ncgsteps = 8000;

    for (icc = 1; ((icc <= ncgsteps) && (gg >= gtest)); icc++) {
      gglast = gg;
      gg = 0.0;
      for (k = 1; k <= ndlist; k++) {
        m = list[k];
        gg += gb[m] * gb[m];
      }
      if (gg >= gtest) {
        gamma = gg / gglast;
        /*  update conjugate gradient direction */
        for (i = 1; i <= ns2; i++) {
          h[i] = gb[i] + gamma * h[i];
        }
        prod1();
        hAh = 0.0;
        for (k = 1; k <= ndlist; k++) {
          m = list[k];
          hAh += h[m] * Ah[m];
        }
        lambda = gg / hAh;
        /*  update voltage, gradient vectors */
        for (i = 1; i <= ns2; i++) {
          u[i] -= lambda * h[i];
          gb[i] -= lambda * Ah[i];
        }

      } /* end of 2nd if gg gt gtest loop */
      ic = icc;
      if ((icc % 30) == 0) {
        fprintf(outfile, "After %d cycles \n", icc);
        fprintf(outfile, "gg = %lf\n", gg);
        current(doitz, 0);
        fprintf(outfile, "currx = %lf\n", currx);
        fprintf(outfile, "curry = %lf\n", curry);
        fprintf(outfile, "currz = %lf\n", currz);
        fflush(outfile);
      }
    } /* end of ncgsteps loop */
    if (gg >= gtest) {
      fprintf(outfile, "\nNO CONVERGENCE: %d steps\n", ncgsteps);
    }
  } /* end of if gg gt gtest loop */
}

int main(void) {
  int i, j, k, micro, phasein, phasemax, doitz, oval, nagg1;
  int m, nlist = 0, temp1, temp0;
  char phasename[MAXSTRING];
  double ety, etz, sigmax, xj, layersigma;
  double sigma0, sigma1, sigma2, avesigma, formfact;

  doitz = oval = nagg1 = 0;
  layersigma = 0.0;

  /* Initialize global arrays */

  for (i = 0; i < NPHMAX; i++) {
    sigma[i][0] = 0.0;
    sigma[i][1] = 0.0;
    sigma[i][2] = 0.0;
    sigma[i][3] = 0.0;
    pcurr[i][0] = 0.0;
    pcurr[i][1] = 0.0;
    pcurr[i][2] = 0.0;
    pcurr[i][3] = 0.0;
    a[i] = 0.0;
    for (j = 0; j < NPHMAX; j++) {
      be[i][j][0] = 0.0;
      be[i][j][1] = 0.0;
      be[i][j][2] = 0.0;
      be[i][j][3] = 0.0;
    }
  }

  phasemax = NPHASE;

  printf("\nInside main routine.\n");

  printf("\n\nEnter the fully-resolved name of the input image: ");
  fflush(stdout);
  read_string(filein, sizeof(filein));

  printf("File name is %s\n", filein);
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

  printf("Enter fully-resolved name of major output file: ");
  read_string(Outfilename, sizeof(Outfilename));
  printf("\nOutput file name is %s\n", Outfilename);

  printf("Enter fully-resolved name of final results file: ");
  read_string(Resultsfilename, sizeof(Resultsfilename));
  printf("\nResults file name is %s\n", Resultsfilename);

  read_string(PCfilename, sizeof(PCfilename));
  printf("Relative phase contributions file name is %s\n", PCfilename);
  printf("\nRelative phase contributions will be printed to file %s\n",
         PCfilename);

  sprintf(Layerfilename, "%sITZConductivity.dat", Outfolder);
  printf("\nEffective moduli as function of distance normal to");
  printf("\n\taggregate surface (if needed) will be printed to file %s\n",
         Layerfilename);
  fflush(stdout);

  /****
   *	NOTE:  MUST READ
   *			(1) VERSION NUMBER (Version)
   *			(2) SYSTEM SIZE (Xsyssize,Ysyssize,Zsyssize)
   *			(3) SYSTEM RESOLUTION (Res)
   *
   ****/

  if (probe_imgheader(filein, &Version, &Xsyssize, &Ysyssize, &Zsyssize,
                      &Res)) {
    bailout("transport", "Error writing image header");
    freeallmem();
    exit(1);
  }

  printf("\nDone scanning image for system characteristics...");
  fflush(stdout);

  Nsites = (Xsyssize + 2) * (Ysyssize + 2) * (Zsyssize + 2);

  pix = NULL;
  list = NULL;
  gx = NULL;
  gy = NULL;
  gz = NULL;
  u = NULL;
  gb = NULL;
  h = NULL;
  Ah = NULL;
  Lsigma = NULL;

  pix = ivector(Nsites);
  list = ivector(Nsites);
  gx = dvector(Nsites);
  gy = dvector(Nsites);
  gz = dvector(Nsites);
  u = dvector(Nsites);
  gb = dvector(Nsites);
  h = dvector(Nsites);
  Ah = dvector(Nsites);
  Lsigma = dvector(Xsyssize + 10);

  if (!pix || !list || !gx || !gy || !gz || !u || !gb || !h || !Ah || !Lsigma) {

    freeallmem();
    bailout("transport", "Memory allocation failure");
    fflush(stdout);
    exit(1);
  }

  pthresh = 1.0 / ((double)(Xsyssize * Ysyssize * Zsyssize));

  printf("\nRead infile for system characteristics...");
  fflush(stdout);

  /* Zero out the conductivity matrix values for all phases */
  for (i = 1; i < NPHMAX; i++) {
    sigma[i][1] = 0.0;
    sigma[i][2] = 0.0;
    sigma[i][3] = 0.0;
    pcurr[i][1] = 0.0;
    pcurr[i][2] = 0.0;
    pcurr[i][3] = 0.0;
  }

  /*  (USER) real image size is nx x ny x nz */
  nx = Xsyssize;
  ny = Ysyssize;
  nz = Zsyssize;
  fxyz = (nx * ny * nz);

  /*  auxiliary variables involving the system size */
  nx1 = nx + 1;
  ny1 = ny + 1;
  nz1 = nz + 1;
  nx2 = nx + 2;
  ny2 = ny + 2;
  nz2 = nz + 2;
  L22 = nx2 * ny2;
  /*  computational image size ns2 is nx2 x ny2 x nz2 */
  ns2 = nx2 * ny2 * nz2;

  /*  (USER) set cutoff for norm squared of gradient, gtest.  gtest is
    the stopping criterion, compared to gb*gb. When gb*gb is less
    than gtest=abc*ns2, then the rms value of the gradient at a pixel
    is less than sqrt(abc). */
  gtest = (1.0e-12) * 5000.0 * ns2;

  /*  (USER) nphase is the number of phases being considered in the problem.
    The values of pix(m) will run from 1 to nphase. ntot is the total
    number of phases possible in the program, and is the dimension of
    sigma, a, and be. */
  nphase = NPHASE;
  ntot = NPHMAX;

  /*  Make list of real (interior) sites, used in subroutine dembx.  The 1-d
    labelling scheme goes over all ns2 sites, so a list of the real sites
    is needed. */
  for (i = 2; i <= nx1; i++) {
    for (j = 2; j <= ny1; j++) {
      temp1 = (j - 1) * nx2;
      for (k = 2; k <= nz1; k++) {
        m = i + temp1 + (k - 1) * L22;
        nlist += 1;
        list[nlist] = m;
      }
    }
  }

  /*  (USER) input value of real conductivity tensor for each phase
    (diagonal only). 1,2,3 = x,y,z, respectively. */

  /*** NEED printfs here to debug.  Program is exiting very quickly ***/

  /*
      printf("\nEnter name of file for writing major output: ");
          read_string(fileout,sizeof(fileout));
      printf("\n%s\n",fileout);

      printf("\nEnter name of file for writing final results: ");
          read_string(fileresults,sizeof(fileresults));
      printf("\n%s\n",fileresults);
  */

  sigmax = 1.0;
  phasein = POROSITY;
  /*
  while(phasein >= 0){
          read_string(instring,sizeof(instring));
      phasein = atoi(instring);
          read_string(instring,sizeof(instring));
      condin = (double)(atof(instring));
          if (phasein >= 0) {
          sigma[phasein+1][1] = condin;
              sigma[phasein+1][2] = condin;
              sigma[phasein+1][3] = condin;
              if (condin > sigmax) {
                      sigmax = condin;
                      phasemax = phasein;
              }
              printf("\nsigma[%d][1] = %f",phasein+1,sigma[phasein+1][1]);
      }
  }
  fflush(stdout);
  */

  /* Manually assign relative conductivities for phases */

  sigma[(POROSITY) + 1][1] = 1.0;
  sigma[(POROSITY) + 1][2] = 1.0;
  sigma[(POROSITY) + 1][3] = 1.0;

  sigma[(DRIEDP) + 1][1] = 0.0;
  sigma[(DRIEDP) + 1][2] = 0.0;
  sigma[(DRIEDP) + 1][3] = 0.0;

  sigma[(EMPTYDP) + 1][1] = 0.0;
  sigma[(EMPTYDP) + 1][2] = 0.0;
  sigma[(EMPTYDP) + 1][3] = 0.0;

  sigma[(EMPTYP) + 1][1] = 0.0;
  sigma[(EMPTYP) + 1][2] = 0.0;
  sigma[(EMPTYP) + 1][3] = 0.0;

  sigma[(CRACKP) + 1][1] = 1.0;
  sigma[(CRACKP) + 1][2] = 1.0;
  sigma[(CRACKP) + 1][3] = 1.0;

  sigma[(CSH) + 1][1] = 0.0025;
  sigma[(CSH) + 1][2] = 0.0025;
  sigma[(CSH) + 1][3] = 0.0025;

  sigma[(POZZCSH) + 1][1] = 0.002;
  sigma[(POZZCSH) + 1][2] = 0.002;
  sigma[(POZZCSH) + 1][3] = 0.002;

  sigma[(SLAGCSH) + 1][1] = 0.002;
  sigma[(SLAGCSH) + 1][2] = 0.002;
  sigma[(SLAGCSH) + 1][3] = 0.002;

  sigma[(INERTAGG) + 1][1] = 0.000;
  sigma[(INERTAGG) + 1][2] = 0.000;
  sigma[(INERTAGG) + 1][3] = 0.000;

  outfile = filehandler("transport", Outfilename, "WRITE");
  if (!outfile) {
    freeallmem();
    exit(1);
  }
  printf("\nSuccessfully opened output file...");
  fflush(stdout);
  resultsfile = filehandler("transport", Resultsfilename, "WRITE");
  if (!resultsfile) {
    freeallmem();
    exit(1);
  }
  printf("\nSuccessfully opened results file...");
  fflush(stdout);
  pcfile = filehandler("transport", PCfilename, "WRITE");
  if (!pcfile) {
    freeallmem();
    exit(1);
  }
  printf("\nSuccessfully opened phase information file...");
  fflush(stdout);

  fprintf(outfile, "Image %s is (%d,%d,%d)  No. of real sites %d \n\n", filein,
          nx, ny, nz, fxyz);
  fprintf(outfile, "POROSITY: sigma = %f\n", sigma[(POROSITY) + 1][1]);
  fprintf(outfile, "CSH: sigma = %f\n", sigma[(CSH) + 1][1]);
  fprintf(outfile, "POZZCSH: sigma = %f\n", sigma[(POZZCSH) + 1][1]);
  fprintf(outfile, "SLAGCSH: sigma = %f\n\n", sigma[(SLAGCSH) + 1][1]);
  fflush(outfile);

  /*  Compute average current in each pixel.
   (USER) npoints is the number of microstructures to use. */

  npoints = NMIC;
  for (micro = 1; micro <= npoints; micro++) {

    /* Read in a microstructure in subroutine ppixel, and set up pix(m)
      with the appropriate phase assignments. */
    ppixel(&nagg1);
    /*   output phase volume fractions */
    fprintf(outfile, "Phase fraction of Water-filled Porosity = %lf \n",
            a[POROSITY + 1]);
    fprintf(outfile, "Phase fraction of C3S = %lf \n", a[C3S + 1]);
    fprintf(outfile, "Phase fraction of C2S = %lf \n", a[C2S + 1]);
    fprintf(outfile, "Phase fraction of C3A = %lf \n", a[C3A + 1]);
    fprintf(outfile, "Phase fraction of C4AF = %lf \n", a[C4AF + 1]);
    fprintf(outfile, "Phase fraction of Gypsum = %lf \n",
            a[GYPSUM] + a[ABSGYP] + a[GYPSUMS]);
    fprintf(outfile, "Phase fraction of Hemihydrate = %lf \n", a[HEMIHYD + 1]);
    fprintf(outfile, "Phase fraction of Anhydrite = %lf \n", a[ANHYDRITE + 1]);
    fprintf(outfile, "Phase fraction of Silica fume = %lf \n", a[SFUME + 1]);
    fprintf(outfile, "Phase fraction of Amorphous silica = %lf \n",
            a[AMSIL + 1]);
    fprintf(outfile, "Phase fraction of Inert filler = %lf \n", a[INERT + 1]);
    fprintf(outfile, "Phase fraction of Slag = %lf \n", a[SLAG + 1]);
    fprintf(outfile, "Phase fraction of ASG = %lf \n", a[ASG + 1]);
    fprintf(outfile, "Phase fraction of CAS2 = %lf \n", a[CAS2 + 1]);
    fprintf(outfile, "Phase fraction of CH = %lf \n", a[CH + 1]);
    fprintf(outfile, "Phase fraction of C-S-H = %lf \n", a[CSH + 1]);
    fprintf(outfile, "Phase fraction of C3AH6 = %lf \n", a[C3AH6 + 1]);
    fprintf(outfile, "Phase fraction of Ettringite = %lf \n",
            a[ETTR + 1] + a[ETTRC4AF + 1]);
    fprintf(outfile, "Phase fraction of Afm = %lf \n", a[AFM + 1]);
    fprintf(outfile, "Phase fraction of FH3 = %lf \n", a[FH3 + 1]);
    fprintf(outfile, "Phase fraction of Pozzolanic CSH = %lf \n",
            a[POZZCSH + 1]);
    fprintf(outfile, "Phase fraction of Slag CSH = %lf \n", a[SLAGCSH + 1]);
    fprintf(outfile, "Phase fraction of CaCl2 = %lf \n", a[CACL2 + 1]);
    fprintf(outfile, "Phase fraction of Friedel salt = %lf \n", a[FRIEDEL + 1]);
    fprintf(outfile, "Phase fraction of Stratlingite = %lf \n", a[STRAT + 1]);
    fprintf(outfile, "Phase fraction of Calcium carbonate = %lf \n",
            a[CACO3 + 1]);
    fprintf(outfile, "Phase fraction of Monocarboaluminate = %lf \n",
            a[AFMC + 1]);
    fprintf(outfile, "Phase fraction of Empty Porosity = %lf \n",
            a[EMPTYP + 1]);
    fprintf(outfile, "Phase fraction of Aggregate = %lf \n", a[INERTAGG + 1]);
    fflush(outfile);

    /*  If any aggregate is in the system, then this is a concrete or mortar, so
       we need to do the calculation on the ITZ */

    if (a[INERTAGG + 1] > 0.0)
      doitz = 1;

    /*  (USER) Set components of applied field, E = (ex,ey,ez) */
    ex = 1.0;
    ey = 1.0;
    ez = 1.0;
    fprintf(outfile, "Applied field components: \n");
    fprintf(outfile, "ex = %lf   ey=  %lf  ez=  %lf \n", ex, ey, ez);
    fprintf(outfile, "sigmax = %lf \n", sigmax);
    fflush(outfile);

    /*   Initialize the voltage distribution by putting on uniform field. */
    for (k = 1; k <= nz2; k++) {
      temp0 = (k - 1) * L22;
      etz = ez * (float)k;
      for (j = 1; j <= ny2; j++) {
        temp1 = (j - 1) * nx2;
        ety = ey * (float)j;
        for (i = 1; i <= nx2; i++) {
          m = temp0 + temp1 + i;
          u[m] = (-ex * (float)i) - ety - etz;
        }
      }
    }

    /*  Subroutine bond sets up conductor network in gx,gy,gz 1-d arrays */
    printf("\nGoing into bond ...pix[2] = %d", pix[2]);
    fflush(stdout);
    printf("\nsigmax = %lf", sigmax);
    fflush(stdout);
    bond();
    printf("\nOut of bond ...");
    fflush(stdout);
    printf("\nsigmax = %lf", sigmax);
    fflush(stdout);

    /*  Subroutine dembx accepts gx,gy,gz and solves for the voltage field
      that minimizes the dissipated energy.   */
    dembx(nlist, doitz);
    printf("\nOut of dembx ...");
    fflush(stdout);
    printf("\nsigmax = %lf", sigmax);
    fflush(stdout);

    /*  find final current after voltage solution is done */
    printf("\nGoing into current for the last time now..");
    fflush(stdout);
    current(doitz, 1);
    printf("\nOut of current");
    fflush(stdout);
    printf("\nsigmax = %lf", sigmax);
    fflush(stdout);
    printf("RESULTS:\n");
    fflush(stdout);
    fprintf(outfile, "RESULTS:\n");
    fflush(outfile);
    /*
    printf("Max_sigmaval %lf \n",sigmax);
    fflush(stdout);
    fprintf(outfile,"Max_sigmaval %lf \n",sigmax);
    fflush(outfile);
    */
    printf("Max_phases %d \n", phasemax);
    fflush(stdout);
    fprintf(outfile, "Max_phases %d \n", phasemax);
    fflush(outfile);
    printf("Field_x %lf \n", ex);
    fflush(stdout);
    fprintf(outfile, "Field_x %lf \n", ex);
    fflush(outfile);
    printf("Curr_x %lf \n", currx);
    fflush(stdout);
    fprintf(outfile, "Curr_x %lf \n", currx);
    fflush(outfile);
    printf("Field_y %lf \n", ey);
    fflush(stdout);
    fprintf(outfile, "Field_y %lf \n", ey);
    fflush(outfile);
    printf("Curr_y %lf \n", curry);
    fflush(stdout);
    fprintf(outfile, "Curr_y %lf \n", curry);
    fflush(outfile);
    printf("Field_z %lf \n", ez);
    fflush(stdout);
    fprintf(outfile, "Field_z %lf \n", ez);
    fflush(outfile);
    printf("Curr_z %lf \n", currz);
    fflush(stdout);
    fprintf(outfile, "Curr_z %lf \n", currz);
    fflush(outfile);
    printf("Cycles_needed %d \n", ic);
    fflush(stdout);
    fprintf(outfile, "Cycles_needed %d \n", ic);
    fflush(outfile);
    printf("*****\n");
    fflush(stdout);
    fprintf(outfile, "*****\n");
    fflush(outfile);
  }

  /* Calculate overall formation factor */

  sigma0 = (currx / ex) / sigmax;
  sigma1 = (curry / ey) / sigmax;
  sigma2 = (currz / ez) / sigmax;

  if (sigma0 < (0.01 * sigma1)) {
    avesigma = (1.0 / 2.0) * (sigma1 + sigma2);
  } else {
    avesigma = (1.0 / 3.0) * (sigma0 + sigma1 + sigma2);
  }

  formfact = -1.0;
  if (avesigma > Eps && sigmax > Eps)
    formfact = sigma[1][1] / (avesigma * sigmax);

  fprintf(resultsfile, "EFFECTIVE CONDUCTIVITY OF PASTE:\n\n");
  fprintf(resultsfile, "\tX-direction conductivity = %lf\n", sigma0);
  fprintf(resultsfile, "\tY-direction conductivity = %lf\n", sigma1);
  fprintf(resultsfile, "\tZ-direction conductivity = %lf\n\n", sigma2);
  if (formfact > 0.0) {
    fprintf(resultsfile, "FORMATION FACTOR OF PASTE = %lf\n\n", formfact);
    fprintf(resultsfile, "TRANSPORT FACTOR OF PASTE = %lf\n\n", 1.0 / formfact);
  } else {
    fprintf(resultsfile, "FORMATION FACTOR OF PASTE UNDEFINED\n\n");
  }

  /***
   *	Compute contribution to the global conductivity
   *	of each phase in the microstructure
   ***/

  fprintf(pcfile, "PHASE-SPECIFIC INFORMATION\n\n");
  for (i = 1; i <= NPHASE; i++) {
    if (a[i] > pthresh) {
      id2phasename(i - 1, phasename);
      fprintf(pcfile, "Phase %s\n", phasename);
      fprintf(pcfile, "\tVolume fraction: %lf\n", a[i]);
      fprintf(pcfile, "\tConductivity %lf\n", sigma[i][1]);
      if (currx < 1.0e-5) {
        fprintf(pcfile, "\tFraction of X-direction conductivity not defined "
                        "because X-direction current is too low\n");
      } else {
        fprintf(pcfile, "\tFraction of X-direction conductivity: %lf\n",
                pcurr[i][0] / currx);
      }
      if (curry < 1.0e-5) {
        fprintf(pcfile, "\tFraction of Y-direction conductivity not defined "
                        "because Y-direction current is too low\n");
      } else {
        fprintf(pcfile, "\tFraction of Y-direction conductivity: %lf\n",
                pcurr[i][1] / curry);
      }
      if (currz < 1.0e-5) {
        fprintf(pcfile, "\tFraction of Z-direction conductivity not defined "
                        "because Z-direction current is too low\n");
      } else {
        fprintf(pcfile, "\tFraction of Z-direction conductivity: %lf\n\n",
                pcurr[i][2] / currz);
      }
      fprintf(outfile, "Phase %s\n", phasename);
      fprintf(outfile, "\tVfrac %lf\n", a[i]);
      fprintf(outfile, "\tConductivity %lf\n", sigma[i][1]);
      if (currx < 1.0e-5) {
        fprintf(outfile, "\tFraction of X-direction conductivity not defined "
                         "because X-direction current is too low\n");
      } else {
        fprintf(outfile, "\tFraction of X-direction conductivity: %lf\n",
                pcurr[i][0] / currx);
      }
      if (curry < 1.0e-5) {
        fprintf(outfile, "\tFraction of Y-direction conductivity not defined "
                         "because Y-direction current is too low\n");
      } else {
        fprintf(outfile, "\tFraction of Y-direction conductivity: %lf\n",
                pcurr[i][1] / curry);
      }
      if (currz < 1.0e-5) {
        fprintf(outfile, "\tFraction of Z-direction conductivity not defined "
                         "because Z-direction current is too low\n");
      } else {
        fprintf(outfile, "\tFraction of Z-direction conductivity: %lf\n\n",
                pcurr[i][2] / currz);
      }
      fprintf(outfile, "\tCurrent_x %lf\n", pcurr[i][0]);
      if (currx < 1.0e-5) {
        fprintf(outfile, "\tCurrent_x_frac not defined because X-direction "
                         "current is too low\n");
      } else {
        fprintf(outfile, "\tCurrent_x_frac %lf\n", pcurr[i][0] / currx);
      }
      fprintf(outfile, "\tCurrent_y %lf\n", pcurr[i][1]);
      if (curry < 1.0e-5) {
        fprintf(outfile, "\tCurrent_y_frac not defined because Y-direction "
                         "current is too low\n");
      } else {
        fprintf(outfile, "\tCurrent_y_frac %lf\n", pcurr[i][1] / curry);
      }
      fprintf(outfile, "\tCurrent_z %lf\n", pcurr[i][2]);
      if (currz < 1.0e-5) {
        fprintf(outfile, "\tCurrent_z_frac not defined because Z-direction "
                         "current is too low\n");
      } else {
        fprintf(outfile, "\tCurrent_z_frac %lf\n\n", pcurr[i][2] / currz);
      }
    }
  }

  if (outfile != NULL)
    fclose(outfile);

  /***
   *	Now, if ITZ calculation turned on, then we have to output
   *	the layer-by-layer average values of sigma
   ***/

  /***
   *	Now average on both sides of aggregate, plot 1st pixel at x = 0.5,
   *	2nd pixel at x = 1.5, etc.
   ***/

  if ((doitz) && (nagg1 > 0)) {
    outfile = filehandler("transport", Layerfilename, "WRITE");
    if (!outfile) {
      printf("\n\nWARNING:  Could not open output file %s", Layerfilename);
    }
    printf("*****\n\n");
    printf("LAYER_DATA:\n\n");
    xj = -0.5;
    for (i = nagg1 - 1; i >= 0; i--) {
      xj += 1.0;
      layersigma = 0.50 * (Lsigma[i] + Lsigma[Xsyssize - i - 1]);
      printf("%.1f %.4f\n", xj, layersigma);
      fprintf(outfile, "%.1f %.4f\n", xj, layersigma);
    }
    printf("END");
    fclose(outfile);
  }

  printf("\nDone with cement paste calculations.");
  if (doitz) {
    oval = conctransport(nagg1, avesigma, sigmax);
  }

  if (outfile != NULL)
    fclose(outfile);
  if (resultsfile != NULL)
    fclose(resultsfile);
  if (pcfile != NULL)
    fclose(pcfile);

  freeallmem();

  return (0);
}

/************************ conctransport.c **********************************/
/* BACKGROUND                                                              */
/* This function takes conductivity data on a cement binder, together with */
/* grading and transport properties of coarse and fine aggregate, to       */
/* estimate the effective conductivity of the concrete or mortar           */
/*                                                                         */
/* Programmer:  Dr. Edward J. Garboczi (NIST/BFRL)- (301)975.6708          */
/* C-conversion by Dr. Jeffrey W. Bullard           (301)975.5725          */
/*                                                                         */
/***************************************************************************/
int conctransport(int nagg1, double avesigma, double sigmax) {
  register int i, j, k, ii;
  int itzpix, numfinebins[NUMFINESOURCES], numfinebinstot, cnt, done;
  int num_fine_sources, num_coarse_sources;
  int finebegin[NUMFINESOURCES], fineend[NUMFINESOURCES];
  int coarsebegin[NUMCOARSESOURCES], coarseend[NUMCOARSESOURCES];
  double scem, fine_agg_vf[NUMFINESOURCES], coarse_agg_vf[NUMCOARSESOURCES];
  double sitz, condrat, itzwidth, tdval;
  char ch, buff[MAXSTRING], instring[MAXSTRING];
  char buff1[MAXSTRING];
  char cempsdfile[MAXSTRING];
  char coarsegfile[MAXSTRING], finegfile[MAXSTRING];
  double sum, sfine, scoarse, sign, finevftot, coarsevftot;
  double aggfrac, airfrac;
  double target_agg_vf, sumint, conductivity;
  double s, ssave[EMT_ITERATIONS], sint[EMT_ITERATIONS];
  double track, xtrack[EMT_ITERATIONS];
  double ss, xs, z, ba, alpha;
  FILE *gfile, *cempsd;

  /* Initialize global arrays */

  sum = 0.0;
  done = 0;
  aggfrac = 0.0;
  finevftot = coarsevftot = 0.0;

  for (i = 0; i < MAXSIZECLASSES; i++) {
    S_conctransport[i] = 0.0;
    Si_conctransport[i] = 0.0;
    Diam_conctransport[i] = 0.0;
    Vf_conctransport[i] = 0.0;
  }

  /* Initialize local arrays */

  for (i = 0; i < EMT_ITERATIONS; i++) {
    ssave[i] = sint[i] = xtrack[i] = 0.0;
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

  printf("\n\nEnter fully resolved name of cement PSD file: ");
  read_string(cempsdfile, sizeof(cempsdfile));
  printf("\n%s\n", cempsdfile);
  cempsd = filehandler("conctransport", cempsdfile, "READ");
  if (!cempsd) {
    sprintf(buff1, "Could not open cement PSD file %s", cempsdfile);
    warning("conctransport", buff1);
    warning("conctransport", "Using median cement PSD of 15 micrometers");
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

    ss = 0.0;
    for (i = nagg1 - 1; i > (nagg1 - itzpix - 1); i--) {
      ss += 0.50 * (Lsigma[i] + Lsigma[Xsyssize - i - 1]);
    }

    ss *= (1.0 / ((double)(itzpix)));
    sitz = ss;

    printf("\nCalculated conductivity of ITZ = %f", sitz);

    /* Now find values for bulk paste */

    ss = 0.0;
    for (i = (nagg1 - itzpix - 1); i >= 0; i--) {
      ss += 0.50 * (Lsigma[i] + Lsigma[Xsyssize - i - 1]);
    }

    ss *= (1.0 / ((double)(nagg1 - itzpix)));
    scem = ss;

  } else {

    printf("\nNo aggregate found in microstructure...");
    itzwidth = 0.0;
    sitz = avesigma;
    scem = avesigma;
  }

  /* condrat is the ratio of the itz conductivity to bulk paste conductivity */
  condrat = sitz / scem;

  printf("\nCalculated conductivity of ITZ = %f", sitz);
  printf("\nCalculated conductivity of bulk paste = %f", scem);

  /* Convert itzwidth to mm */
  itzwidth *= 0.001;
  printf("\nITZ width is %f mm\n", itzwidth);

  printf("\nEnter the number of sources of fine aggregate: ");
  read_string(buff1, sizeof(buff1));
  num_fine_sources = atoi(buff1);
  if (num_fine_sources < 0)
    num_fine_sources = 0;
  if (num_fine_sources > (int)NUMFINESOURCES)
    num_fine_sources = (int)NUMFINESOURCES;

  sum = 0.0;
  N_conctransport = 0;
  for (k = 0; k < num_fine_sources; k++) {
    printf("\nEnter volume fraction of fine aggregate source %d: ", k + 1);
    read_string(buff, sizeof(buff));
    fine_agg_vf[k] = atof(buff);
    finevftot += fine_agg_vf[k];
    printf("%f", fine_agg_vf[k]);

    finebegin[k] = N_conctransport;
    if (fine_agg_vf[k] > 0.0) {
      printf("\nFine aggregate grading file must have three ");
      printf("\ncolumns of data: one for sieve description, one for ");
      printf("\nopening diameter (mm) and one for fraction retained.");
      printf("\nThe columns must be TAB-DELIMITED.");
      printf(
          "\nEnter fully-resolved name of grading file for fine aggregate %d: ",
          k + 1);
      read_string(finegfile, sizeof(finegfile));
      printf("\n%s\n", finegfile);
      gfile = filehandler("conctransport", finegfile, "READ");
      if (!gfile) {
        bailout("conctransport", "Could not open fine grading file");
        return (1);
      }
      printf("\nEnter conductivity for fine aggregate %d: ", k + 1);
      read_string(buff, sizeof(buff));
      sfine = atof(buff);
      printf("%f", sfine);

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
              Diam_conctransport[N_conctransport] = atof(buff);
            } else if (i == 2) {
              Vf_conctransport[N_conctransport] = fine_agg_vf[k] * (atof(buff));
              sum += Vf_conctransport[N_conctransport];
              S_conctransport[N_conctransport] = sfine;
              Si_conctransport[N_conctransport] = sfine;
              printf("\n%d: Diam = %f, Vf = %f, sum = %f", N_conctransport,
                     Diam_conctransport[N_conctransport],
                     Vf_conctransport[N_conctransport], sum);
              N_conctransport++;
              cnt++;
            }
          }
        }
      }

      fclose(gfile);
    }
    numfinebins[k] = cnt;
    fineend[k] = N_conctransport;
  }
  numfinebinstot = N_conctransport;

  printf("\nEnter the number of sources of coarse aggregate: ");
  read_string(buff1, sizeof(buff1));
  num_coarse_sources = atoi(buff1);
  if (num_coarse_sources < 0)
    num_coarse_sources = 0;
  if (num_coarse_sources > (int)NUMCOARSESOURCES)
    num_coarse_sources = (int)NUMCOARSESOURCES;

  for (k = 0; k < num_coarse_sources; k++) {
    printf("\n\nEnter volume fraction of coarse aggregate %d: ", k + 1);
    read_string(buff, sizeof(buff));
    coarse_agg_vf[k] = atof(buff);
    coarsevftot = coarse_agg_vf[k];
    printf("%f", coarse_agg_vf[k]);

    coarsebegin[k] = N_conctransport;
    if (coarse_agg_vf[k] > 0.0) {
      printf("\nCoarse aggregate grading file must have three ");
      printf("\ncolumns of data: one for sieve description, one for ");
      printf("\nopening diameter (mm) and one for fraction retained.");
      printf("\nThe columns must be TAB-DELIMITED.");
      printf("\n\nEnter fully-resolved name of grading file for coarse "
             "aggregate %d: ",
             k + 1);
      read_string(coarsegfile, sizeof(coarsegfile));
      printf("\n%s\n", coarsegfile);
      gfile = filehandler("conctransport", coarsegfile, "READ");
      if (!gfile) {
        bailout("conctransport", "Could not open coarse grading file");
        return (1);
      }
      printf("\nEnter conductivity for coarse aggregate %d: ", k + 1);
      read_string(buff, sizeof(buff));
      scoarse = atof(buff);
      printf("%f", scoarse);

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
              Diam_conctransport[N_conctransport] = atof(buff);
            } else if (i == 2) {
              Vf_conctransport[N_conctransport] =
                  coarse_agg_vf[k] * (atof(buff));
              sum += Vf_conctransport[N_conctransport];
              S_conctransport[N_conctransport] = scoarse;
              Si_conctransport[N_conctransport] = scoarse;
              printf("\n%d: Diam = %f, Vf = %f, sum = %f", N_conctransport,
                     Diam_conctransport[N_conctransport],
                     Vf_conctransport[N_conctransport], sum);
              N_conctransport++;
            }
          }
        }
      }

      fclose(gfile);
    }
    coarseend[k] = N_conctransport;
  }

  /* Bubble sort on each aggregate type individually, then assign average
   * diameters */
  for (k = 0; k < num_fine_sources; k++) {
    for (i = finebegin[k]; i < fineend[k]; i++) {
      for (j = (i + 1); j < fineend[k]; j++) {
        if (Diam_conctransport[i] < Diam_conctransport[j]) {
          tdval = Diam_conctransport[i];
          Diam_conctransport[i] = Diam_conctransport[j];
          Diam_conctransport[j] = tdval;
          tdval = Vf_conctransport[i];
          Vf_conctransport[i] = Vf_conctransport[j];
          Vf_conctransport[j] = tdval;
          tdval = S_conctransport[i];
          S_conctransport[i] = S_conctransport[j];
          S_conctransport[j] = tdval;
          tdval = Si_conctransport[i];
          Si_conctransport[i] = Si_conctransport[j];
          Si_conctransport[j] = tdval;
        }
      }
    }
  }

  for (k = 0; k < num_coarse_sources; k++) {
    for (i = coarsebegin[k]; i < coarseend[k]; i++) {
      for (j = (i + 1); j < coarseend[k]; j++) {
        if (Diam_conctransport[i] < Diam_conctransport[j]) {
          tdval = Diam_conctransport[i];
          Diam_conctransport[i] = Diam_conctransport[j];
          Diam_conctransport[j] = tdval;
          tdval = Vf_conctransport[i];
          Vf_conctransport[i] = Vf_conctransport[j];
          Vf_conctransport[j] = tdval;
          tdval = S_conctransport[i];
          S_conctransport[i] = S_conctransport[j];
          S_conctransport[j] = tdval;
          tdval = Si_conctransport[i];
          Si_conctransport[i] = Si_conctransport[j];
          Si_conctransport[j] = tdval;
        }
      }
    }
  }

  /* Now sorted within source, assign average diameters */
  /* Actual diameter in a sieve should be something like the average
   * between the sieve opening and the opening of the next largest
   * sieve */

  for (k = 0; k < num_fine_sources; k++) {
    for (i = finebegin[k] + 1; i < fineend[k]; i++) {
      Diam_conctransport[i] =
          0.5 * (Diam_conctransport[i] + Diam_conctransport[i - 1]);
    }
    Diam_conctransport[finebegin[k]] *= 1.10;
  }

  for (k = 0; k < num_coarse_sources; k++) {
    for (i = coarsebegin[k] + 1; i < coarseend[k]; i++) {
      Diam_conctransport[i] =
          0.5 * (Diam_conctransport[i] + Diam_conctransport[i - 1]);
    }
    Diam_conctransport[coarsebegin[k]] *= 1.10;
  }

  /* Final bubble sort on entire aggregate distribution */

  for (i = 0; i < N_conctransport - 1; i++) {
    for (j = (i + 1); j < N_conctransport; j++) {
      if (Diam_conctransport[i] < Diam_conctransport[j]) {
        tdval = Diam_conctransport[i];
        Diam_conctransport[i] = Diam_conctransport[j];
        Diam_conctransport[j] = tdval;
        tdval = Vf_conctransport[i];
        Vf_conctransport[i] = Vf_conctransport[j];
        Vf_conctransport[j] = tdval;
        tdval = S_conctransport[i];
        S_conctransport[i] = S_conctransport[j];
        S_conctransport[j] = tdval;
        tdval = Si_conctransport[i];
        Si_conctransport[i] = Si_conctransport[j];
        Si_conctransport[j] = tdval;
      }
    }
  }

  if (fabs(sum - 1.0) > 0.005) {
    printf("\n\nVolume fraction data sums to %.4f ...", sum);
    printf("\nWill now renormalize the data to 1.0 ...");

    for (i = 0; i < N_conctransport; i++) {
      if (sum > 0.0)
        Vf_conctransport[i] /= sum;
    }
  }

  /* Print final normalized total aggregate grading */

  printf("\n\nNORMALIZED AGGREGATE GRADING:");
  for (i = 0; i < N_conctransport; i++) {
    printf("\nDiam = %f Vf = %f, ", Diam_conctransport[i], Vf_conctransport[i]);
    printf("S = %f Si = %f", S_conctransport[i], Si_conctransport[i]);
  }
  printf("\n");

  aggfrac = finevftot + coarsevftot;
  printf("\nTotal aggregate volume fraction = %f", aggfrac);
  fprintf(resultsfile, "\nCONCRETE CONDUCTIVITY INFORMATION:\n");
  fprintf(resultsfile, "\taggfrac: %f\n", aggfrac);

  printf("\n\nEnter the volume fraction of air: ");
  read_string(buff, sizeof(buff));
  airfrac = atof(buff);
  printf("\n%f", airfrac);
  fprintf(resultsfile, "\tairfrac: %f\n", airfrac);

  for (i = 0; i < N_conctransport; i++) {
    Vf_conctransport[i] *= (aggfrac / (aggfrac + airfrac));
  }
  Diam_conctransport[N_conctransport] = 0.04;
  S_conctransport[N_conctransport] = 0.0;
  Si_conctransport[N_conctransport] = 0.0;
  Vf_conctransport[N_conctransport] = airfrac / (aggfrac + airfrac);
  target_agg_vf = (aggfrac + airfrac);

  effective(itzwidth, sitz);

  s = scem;
  ssave[0] = s;
  ss = 0.0;

  /***
   * Concrete differential EMT method
   * Solve volume fraction in terms of conductivity, i.e.
   *   conductivity is the integrating variable, not volume fraction
   * Loop over effective particles, S_conctransport, to compute <m>
   * All conductivities are given in terms of the initial matrix
   *   conductivity
   ***/

  ssave[0] = scem;
  sint[0] = 0.0;
  xs = track = 0.0;
  ss = -1.0;

  /* Get the Gaussian quadrature points */

  Ng = (int)NG;
  getGausspoints();
  i = 1;
  done = 0;

  while ((i < EMT_ITERATIONS) && (!done)) {
    printf("\nEMT iteration %d out of Max %d", i, ((int)EMT_ITERATIONS));
    fflush(stdout);
    sign = ss / fabs(ss);
    ssave[i] = scem * (1.0 + (sign * (((double)i) * 0.0099)));
    /*
    printf("\n\tDummy conductivity variable = %f",ssave[i]);
    */
    sumint = 0.0;

    /* Here is loop over Gaussian points */

    for (j = 0; j < Ng; j++) {

      conductivity = 0.5 * (ssave[i] - ssave[i - 1]) * Xg[j] +
                     0.5 * (ssave[i] + ssave[i - 1]);
      /*
      printf("\n\t\tGaussian weights X[%d] W[%d] = %f,%f, Quadrature point =
      %f",j,j,Xg[j],Wg[j],conductivity);
      */

      /* Compute the mean slope, ss, over different sieves */
      ss = 0.0;
      for (ii = 0; ii <= N_conctransport; ii++) {
        if (Diam_conctransport[ii] > 0.0) {
          ba = (Diam_conctransport[ii] + 2.0 * itzwidth) /
               Diam_conctransport[ii];
          alpha = pow(ba, 3.0);
          ss += (Vf_conctransport[ii] *
                 (3.0 * alpha * (S_conctransport[ii] - conductivity)) /
                 ((2.0 * conductivity) + S_conctransport[ii]));
        }
      }

      /* Now do EMT integral */

      sumint -= (0.5 * (ssave[i] - ssave[i - 1]) * Wg[j] / (ss * conductivity));
    }

    sint[i] = sumint;

    /* track keeps a running total of the integral */

    track += sint[i];

    /* xtrack keeps a running track of the volume fraction obtained in the
     * integral so far */

    xtrack[i] = 1.0 - exp(track);
    printf("\n\tVf = %f (target = %f), ssave = %f, slope = %f", xtrack[i],
           target_agg_vf, ssave[i], ss);
    fflush(stdout);

    if (xtrack[i] > target_agg_vf) {
      z = (target_agg_vf - xtrack[i - 1]) / (xtrack[i] - xtrack[i - 1]);
      xs = ssave[i - 1] + (z * (ssave[i] - ssave[i - 1]));
      break;
    }
    i++;
  }

  fprintf(resultsfile, "\tAggregate_vol_frac: %.4f\n", target_agg_vf);
  for (i = 0; i < num_fine_sources; i++) {
    fprintf(resultsfile, "\t\tFine aggregate source %d: %.4f\n", i,
            fine_agg_vf[i]);
  }
  for (i = 0; i < num_coarse_sources; i++) {
    fprintf(resultsfile, "\t\tCoarse aggregate source %d: %.4f\n", i,
            coarse_agg_vf[i]);
  }
  fprintf(resultsfile, "\tEff_Conductivity: %.4f\n", xs);
  if (xs > 0.0) {
    fprintf(resultsfile, "\nFORMATION FACTOR OF CONCRETE = %lf", sigmax / xs);
    fprintf(resultsfile, "\nTRANSPORT FACTOR OF CONCRETE = %lf", xs / sigmax);
  } else {
    fprintf(resultsfile, "\nFORMATION FACTOR OF CONCRETE UNDEFINED");
  }
  return (0);
}

void effective(double itzwidth, double sitz) {
  register int i;
  double ba, c;

  printf("\nIn function effective:");
  for (i = 0; i < N_conctransport; i++) {

    printf("\n\tDiam[%d] = %f, itzwidth = %f", i, Diam_conctransport[i],
           itzwidth);
    ba = (Diam_conctransport[i] + 2.0 * itzwidth) / Diam_conctransport[i];
    c = pow(ba, 3.0);

    printf("\nba = %f and c = %f", ba, c);
    printf("\nSi_conctransport[%d] = %f and sitz = %f", i, Si_conctransport[i],
           sitz);
    S_conctransport[i] = sitz * ((2.0 * (Si_conctransport[i] - sitz)) +
                                 (c * (Si_conctransport[i] + (2.0 * sitz))));
    S_conctransport[i] /= ((c * (Si_conctransport[i] + 2.0 * sitz)) -
                           (Si_conctransport[i] - sitz));

    printf("\nS_conctransport[%d] = %f", i, S_conctransport[i]);
  }
  fflush(stdout);

  return;
}

void slope(double itzwidth, double *ss, double s) {
  int i;
  double ba, alpha;

  *ss = 0.0;

  for (i = 0; i <= N_conctransport; i++) {
    ba = (Diam_conctransport[i] + 2.0 * itzwidth) / Diam_conctransport[i];
    alpha = pow(ba, 3.0);
    *ss += (Vf_conctransport[i] * (3.0 * alpha * (S_conctransport[i] - s)) /
            ((2.0 * s) + S_conctransport[i]));
  }

  *ss *= SHAPEFACTOR;

  return;
}

int getGausspoints(void) {
  int m, i;
  double eps = 1.0e-14;
  double dn, e1, t, x0, den, d1, pnm1, pn, pnp1, dpn, d2pn, u, v, x1;
  double *x, *w;

  const double Pi = 4.0 * atan(1.0);

  /* Allocate memory for the Xg and Wg vectors */

  if (Xg)
    free_dvector(Xg);
  Xg = dvector(Ng + 1);
  if (!Xg) {
    printf("\nERROR: Could not allocate memory for x quadrature points.");
    printf("  Exiting.");
    fflush(stdout);
    return (1);
  }

  if (Wg)
    free_dvector(Wg);
  Wg = dvector(Ng + 1);
  if (!Wg) {
    printf("\nERROR: Could not allocate memory for w quadrature points.");
    printf("  Exiting.");
    fflush(stdout);
    free_dvector(Xg);
    return (1);
  }

  /* Allocate memory for the local x and w vectors */

  x = dvector(Ng + 1);
  if (!x) {
    printf("\nERROR: Could not allocate memory for theta quadrature points.");
    printf("  Exiting.");
    fflush(stdout);
    free_dvector(Wg);
    free_dvector(Xg);
    return (1);
  }

  w = dvector(Ng + 1);
  if (!w) {
    printf("\nERROR: Could not allocate memory for phi quadrature points.");
    printf("  Exiting.");
    fflush(stdout);
    free_dvector(x);
    free_dvector(Wg);
    free_dvector(Xg);
    return (1);
  }

  /* Now populate the quadrature points */

  m = (Ng + 1) / 2;
  dn = (double)(Ng);
  e1 = dn * (dn + 1.0);
  for (i = 1; i <= m; i++) {
    t = ((4.0 * (double)(i)) - 1.0) * Pi / (4.0 * dn + 2.0);
    x0 = (1.0 - (1.0 - (1.0 / dn)) / (8.0 * dn * dn)) * cos(t);
    do {
      legendr(Ng, &x0, &pn, &pnm1, &pnp1);
      den = 1.0 - (x0 * x0);
      d1 = dn * (pnm1 - (x0 * pn));
      dpn = d1 / den;
      d2pn = ((2.0 * x0 * dpn) - (e1 * pn)) / den;
      u = pn / dpn;
      v = d2pn / dpn;
      x1 = x0 - (u * (1.0 + (0.50 * u * v)));
      x0 = x1;
    } while ((x1 - x0) >= eps);
    x0 = x1;
    legendr(Ng, &x0, &pn, &pnm1, &pnp1);
    x[i] = x0;
    w[i] = (2.0 * (1.0 - (x0 * x0))) / pow((dn * pnm1), 2.0);
  }

  if (m + m > Ng)
    x[m] = 0.0;

  for (i = 1; i <= m; i++) {
    Xg[i] = -x[i];
    Xg[i + m] = x[m + 1 - i];
    Wg[i] = w[i];
    Wg[i + m] = w[m + 1 - i];
  }

  /*  Free the locally dynamically allocated memory */

  free_dvector(w);
  free_dvector(x);
  return (0);
}

void legendr(int n, double *x, double *pn, double *pnm1, double *pnp1) {
  int k;
  double pkm1, pk, t1, pkp1;

  pkm1 = 1.0;
  pk = *x;
  for (k = 2; k <= n; k++) {
    t1 = (*x) * pk;
    pkp1 = t1 - pkm1 - ((t1 - pkm1) / ((double)(k))) + t1;
    pkm1 = pk;
    pk = pkp1;
  }

  *pn = pk;
  *pnm1 = pkm1;
  t1 = (*x) * (*pn);
  *pnp1 = t1 - (*pnm1) - ((t1 - (*pnm1)) / ((double)(k + 1))) + t1;
  return;
}
