/******************************************************
 *
 * Program chlorattack3d to simulate diffusion/binding
 * of chloride ions in cement, performed within a 3-D
 * pixel-based microstructure
 *
 * Date: Fall 2001            Programmers: D.P. Bentz
 *                                         E.P.Nielsen
 *
 * Making a small change to test CVS repository
 *
 * Model bases:
 *    Each pixel is one cubic micron
 *    Each diffusing CaCl2-- diffusing species is equivalent
 *       to 0.8241e-13 grams
 *    This means that:
 *       Each ETTR pixel can react with 2 diffusing CaCl2, when
 *       	more than 90% of AFM phase is consumed
 *       Each ETTRC4AF pixel can react with 2 diffusing CaCl2, when
 *       	more than 90% of AFM phase is consumed
 *       Each C3AH6 pixel can react with 9 diffusing CaCl2
 *       Each AFM pixel can react with 3 diffusing CaCl2
 *       Each AFMC pixel can react with 5 diffusing CaCl2
 *
 * Each diffusing species moves a step each cycle
 * regardless of whether it is in a gel phase or
 * capillary porosity.  This means that all results have
 * to be corrected by the diffusivity computed for the
 * 3-D image using the conjugate gradient technique
 * (i.e. no binding/reaction)
 *
 *******************************************************/
#include "include/vcctl.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MOLEFACTOR                                                             \
  1.0E12 /* cubic micrometers per                                              \
                                                 cubic centimeter */
#define NUMANTS 500000

#define SPERETTR 2     /* diffusing species per ETTR pixel */
#define SPERETTRC4AF 2 /* diffusing species per ETTRC4AF pixel */
#define SPERC3AH6 9    /* diffusing species per C3AH6 pixel */
#define SPERAFM 3      /* diffusing species per AFM pixel */
#define SPERAFMC 5     /* diffusing species per monocarbonate pixel */

#define MASSCACL2 0.8241E-13 /*Mass of CaCl2 in one pixel*/

/***
 *	Global variables
 *
 *	System size is Xsyssize,Ysyssize,Zsyssize
 *	Resolution is Res
 ***/
int Syspix = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
int Xsyssize, Ysyssize, Zsyssize;
int Isizemag = 1;
float Res = DEFAULTRESOLUTION;
float Sizemag = 1.0;

/***
 *	Mic holds the evolving microstructure
 *
 *	React holds the number of reacted diffusing
 *	species at each reactive pixel site
 ***/

short int ***Mic, ***React;
float MwCl = 35.45;
float MwCaCl2 = 111.0;
int *Seed;
int *Ndiff;
int *Nrettr, *Nrettrc4af, *Nrafm, *Nrc3ah6;
int *Afmorig, *Ettrorig, *Ettrc4aforig;
int *C3ah6orig, *Gypsumcount, *Friedelcount;
int *Gypsumorig, *Friedelorig, *Nrafmc, *Afmcorig, *Ccorig;
int *Straingyp, *Strainbrucite, *Strainettr;
int *Strainfriedel;
double *Density, *Nrgel;
int *Nrcap;
double *Clreacted, *Clchemisorb, Clreactmax;
float Layer_volume;

/* VCCTL software version number used to make the input file */
float Version;

/* coordinates of diffusing species in (Xnew,Ynew,Znew) */
short int *Xnew, *Ynew, *Znew;

int Nantsurf, Ntotdiff = 0;
double Molesperpixel[MS + 1], Cfre, Cbound;

/***
 *	Function declarations
 ***/
void remsurf(int nrem);
void extphase(int phtomake, int xcur, int ycur, int zcur);
void allmem(void);
void freeallmem(void);

#include "include/properties.h"

int main(void) {
  int ix, iy, iz, seed1, nlen;
  int i, antx, anty, antz, ich, inval, oinval;
  int cxn, cyn, czn, phid, sel1, numadd, initdepth;
  int ia, ncyc, icyc, iant, nleft, norg, nadd;
  int chinit = 0, afminit = 0, c3ah6init = 0, ettrinit = 0, ettrc4init = 0;
  float prand, preact, ptest, alpha, beta, chlorconc;
  double volume_available;
  char filein[MAXSTRING], fileout[MAXSTRING];
  char fplot[MAXSTRING], fileroot[MAXSTRING], exten[MAXSTRING];
  char instring[MAXSTRING];
  FILE *micfile, *newmic, *plotfile;

  Mic = NULL;
  React = NULL;
  Ndiff = NULL;
  Nrettr = NULL;
  Nrafm = NULL;
  Nrc3ah6 = NULL;
  Afmorig = NULL;
  Ettrorig = NULL;
  Gypsumorig = NULL;
  C3ah6orig = NULL;
  Ettrc4aforig = NULL;
  Nrafmc = NULL;
  Afmcorig = NULL;
  Ccorig = NULL;
  Nrcap = NULL;
  Nrgel = NULL;
  Straingyp = NULL;
  Strainbrucite = NULL;
  Strainettr = NULL;
  Strainfriedel = NULL;
  Gypsumcount = NULL;
  Friedelcount = NULL;
  Density = NULL;
  Clreacted = NULL;
  Clchemisorb = NULL;

  /* Initialize global array Molesperpixel */

  for (i = 0; i <= MS; i++) {
    Molesperpixel[i] = 0.0;
  }

  /* Establish needed specific gravities and molar volumes */

  assign_properties();

  for (ix = 0; ix <= MS; ix++) {
    Molesperpixel[ix] = 0.0;
  }

  /*Molesperpixel[CH]=1./Molarv[CH]/MOLEFACTOR;*/
  /*Molesperpixel[MS]=1./Molarv[MS]/MOLEFACTOR;*/
  /*Molesperpixel[GYPSUM]=1./Molarv[GYPSUM]/MOLEFACTOR;*/
  /*Molesperpixel[C3AH6]=1./Molarv[C3AH6]/MOLEFACTOR;*/
  /*Molesperpixel[BRUCITE]=1./Molarv[BRUCITE]/MOLEFACTOR;*/
  /*Molesperpixel[AFM]=1./Molarv[AFM]/MOLEFACTOR;*/
  /*Molesperpixel[ETTR]=1./Molarv[ETTR]/MOLEFACTOR;*/
  /*Molesperpixel[ETTRC4AF]=1./Molarv[ETTRC4AF]/MOLEFACTOR;*/
  /*Molesperpixel[FRIEDEL]=1./Molarv[FRIEDEL]/MOLEFACTOR;*/

  /* Get user input */

  printf("Enter random number seed \n");
  read_string(instring, sizeof(instring));
  seed1 = atoi(instring);
  printf("Random seed: %d \n", seed1);
  Seed = (&seed1);

  printf("Enter name of file with input microstructure \n");
  read_string(filein, sizeof(filein));
  printf("File for input: %s\n", filein);

  printf("Enter name of image file to write \n");
  read_string(fileout, sizeof(fileout));
  printf("File for output: %s\n", fileout);

  printf("Enter probability of reaction: ");
  read_string(instring, sizeof(instring));
  preact = atof(instring);
  printf("Probability of reaction: %f \n", preact);

  printf("Allow chemical adsorption of Cl in C-S-H? [0(yes)/1(no)]\n");
  read_string(instring, sizeof(instring));
  sel1 = atoi(instring);
  if (!sel1) {
    printf("Define alpha in Langmuir isotherm\n");
    read_string(instring, sizeof(instring));
    alpha = atof(instring);
    printf("Define beta in Langmuir isotherm\n");
    read_string(instring, sizeof(instring));
    beta = atof(instring);
  } else {
    alpha = beta = 0.0;
  }

  printf("Enter molarity of chloride solution (0.0,1.0):  ");
  read_string(instring, sizeof(instring));
  chlorconc = atof(instring);
  printf("\nChloride solution concentration %f M\n", chlorconc);

  printf("Enter initial penetration depth of chlorides (in microns): ");
  read_string(instring, sizeof(instring));
  initdepth = atoi(instring);
  printf("\nInitial penetration depth:  %d microns\n", initdepth);

  printf("Enter number of steps (cycles) to execute \n");
  read_string(instring, sizeof(instring));
  ncyc = atoi(instring);
  printf("Cycles requested: %d \n", ncyc);

  /***
   *	Determine system size and resolution
   *	First read in microstructure from datafile
   ***/

  micfile = filehandler("chlorattack3d", filein, "READ");
  if (!micfile) {
    exit(1);
  }

  newmic = filehandler("chlorattack3d", fileout, "WRITE");
  if (!newmic) {
    exit(1);
  }

  /***
   *	Determine whether system size and resolution
   *	are specified in the image file
   ***/

  if (read_imgheader(micfile, &Version, &Xsyssize, &Ysyssize, &Zsyssize,
                     &Res)) {
    fclose(micfile);
    bailout("chlorattack3d", "Error reading image header");
    freeallmem();
    exit(1);
  }

  /***
   *	Convert molarity to number of ants per pixel
   ***/

  chlorconc = (chlorconc / 0.743102) * Res * Res * Res;

  Syspix = (Xsyssize * Ysyssize * Zsyssize);
  Sizemag = (float)((double)Syspix / pow((double)DEFAULTSYSTEMSIZE, 3.0));
  Isizemag = (int)(Sizemag + 0.5);

  printf("\nXsyssize is %d\n", Xsyssize);
  printf("\nYsyssize is %d\n", Ysyssize);
  printf("\nZsyssize is %d\n", Zsyssize);
  printf("Res is %f\n", Res);
  fflush(stdout);

  /* Define the number of pixels per layer */

  Layer_volume = (float)(Xsyssize * Ysyssize);

  /***
   *	Must now allocate memory for all the arrays
   ***/

  allmem();

  /***
   *	Set up boundary conditions:
   *		all porosity at top surface
   *		all solid material at bottom surface
   ***/

  for (ix = 0; ix < Xsyssize; ix++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      Mic[ix][iy][0] = 0;
      Mic[ix][iy][Zsyssize + 1] = 1;
      React[ix][iy][0] = React[ix][iy][Zsyssize + 1] = 0;
    }
  }

  /* Initialize array of original AFM counts and reacted counts */

  for (iz = 0; iz < (Zsyssize + 2); iz++) {
    Ndiff[iz] = 0;
    Nrafm[iz] = 0;
    Nrc3ah6[iz] = 0;
    Straingyp[iz] = 0;
    Strainettr[iz] = 0;
    Strainbrucite[iz] = 0;
    Strainfriedel[iz] = 0;
    Afmorig[iz] = 0;
    C3ah6orig[iz] = 0;
    Ettrorig[iz] = 0;
    Ettrc4aforig[iz] = 0;
    Friedelcount[iz] = 0;
    Friedelorig[iz] = 0;
    Gypsumorig[iz] = 0;
    Gypsumcount[iz] = 0;
    Nrcap[iz] = 0;
    Nrgel[iz] = 0.0;
    Density[iz] = 0.0;
    Clreacted[iz] = 0.0;
    Clchemisorb[iz] = 0.0;
    Nrafmc[iz] = 0;
    Afmcorig[iz] = 0;
    Ccorig[iz] = 0;
  }

  Clreactmax = 0.0;

  /* Read in microstructure from datafile */

  for (ix = 0; ix < Xsyssize; ix++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 1; iz < Zsyssize + 1; iz++) {

        if (feof(micfile)) {
          freeallmem();
          bailout("chlorattack3d", "End of file encountered");
          exit(1);
        }

        fscanf(micfile, "%s", instring);
        oinval = atoi(instring);
        inval = convert_id(oinval, Version);
        Mic[ix][iy][iz] = inval;
        React[ix][iy][iz] = 0;
        Density[iz] += ((Specgrav[inval] / MOLEFACTOR) / Layer_volume);

        if (inval == CH)
          chinit++;

        if (inval == ETTR) {
          ettrinit++;
          Ettrorig[iz]++;
          Clreactmax += (float)SPERETTR;
        }

        if (inval == ETTRC4AF) {
          ettrc4init++;
          Ettrc4aforig[iz]++;
          Clreactmax += (float)SPERETTRC4AF;
        }

        if (inval == AFM) {
          afminit++;
          Afmorig[iz]++;

          /* 3 for AFM and 1 for 1/2 ettringite */

          Clreactmax += 4.0;
        }

        if (inval == C3AH6) {
          c3ah6init++;
          C3ah6orig[iz]++;
          Clreactmax += (float)SPERC3AH6;
        }

        if ((inval == POROSITY) || (inval == EMPTYP) || (inval == DIFFCSH) ||
            (inval == DIFFCH) || (inval == DIFFGYP) || (inval == DIFFC3A) ||
            (inval == DIFFC4A) || (inval == DIFFFH3) || (inval == DIFFETTR) ||
            (inval == DIFFCACO3) || (inval == DIFFAS) || (inval == DIFFANH) ||
            (inval == DIFFHEM) || (inval == DIFFCAS2) || (inval == DIFFCACL2) ||
            (inval == DRIEDP) || (inval == EMPTYDP) || (inval == MS)) {

          Nrcap[iz]++;
        }

        if (inval == CSH) {

          Nrgel[iz] += 0.38; /* gel porosity */

        } else if ((inval == POZZCSH) || (inval == SLAGCSH)) {

          Nrgel[iz] += 0.20; /* gel porosity */
        }

        if (inval == FRIEDEL)
          Friedelorig[iz]++;
        if (inval == GYPSUM)
          Gypsumorig[iz]++;
        if (inval == AFMC)
          Afmcorig[iz]++;
        if (inval == CACO3)
          Ccorig[iz]++;
      }
    }
  }

  Clreactmax = Clreactmax * MASSCACL2 * 2.0 * MwCl;
  Clreactmax = Clreactmax / (MwCaCl2 * (float)Zsyssize);

  fclose(micfile);

  printf("Initial counts for CH, AFM, C3AH6 and ettringite(2) are ");
  printf("%d, %d, %d, ", chinit, afminit, c3ah6init);
  printf("%d, and %d.\n", ettrinit, ettrc4init);
  fflush(stdout);

  printf("Ntotdiff is %d \n", Ntotdiff);

  printf("Cycle Layer Diffusing Bound \n");

  Ntotdiff = 0;

  /***
   *	Add ants to the top initdepth layers
   *	BELOW the surface layer
   *	at random locations until each layer
   *	has the specified concentration of ants
   ***/

  for (iz = 1; iz <= initdepth; iz++) {
    nleft = (int)Layer_volume;
    volume_available = ((double)(Nrcap[iz])) + Nrgel[iz];
    numadd = (chlorconc * volume_available);

    nadd =
        numadd -
        Ndiff[iz]; /* number ants left to add
                                                                to this layer */
    while (nadd > 0 && nleft > 0) {
      prand = ran1(Seed);
      ix = (int)((float)Xsyssize * prand);
      prand = ran1(Seed);
      iy = (int)((float)Ysyssize * prand);
      phid = Mic[ix][iy][iz];

      /***
       *	Check whether the ant can be placed here
       *	(ich = 1) or not (ich = 0).  Multiple ants
       *	may reside in the same pixel (these are
       *	boson ants).
       ***/

      ich = 0;
      if ((phid == POROSITY) || (phid == CSH) || (phid == EMPTYP) ||
          (phid == DRIEDP) || (phid == POZZCSH) || (phid == SLAGCSH)) {
        ich = 1;
      }

      if (ich) {
        if (Ntotdiff >= NUMANTS * Isizemag) {
          freeallmem();
          bailout("chlorattack3d", "Too many ants");
          exit(1);
        }

        Ntotdiff++;
        Xnew[Ntotdiff] = ix;
        Ynew[Ntotdiff] = iy;
        Znew[Ntotdiff] = iz;
        Ndiff[iz]++;
        nadd--;
        nleft = (int)Layer_volume;
      } else {
        nleft--;
      }
    }
  }

  /***
   *	Main loop for chloride attack
   ***/

  /***
   *	Determine the number of ants to maintain at the surface
   *	throughout the simulation
   ***/

  Nantsurf = (chlorconc * Layer_volume);

  for (icyc = 1; icyc <= ncyc; icyc++) {
    nleft = 0;
    nadd = Nantsurf - Ndiff[0];
    if (nadd > 0) {

      /* Add some ants to the top surface at random locations... */

      for (ia = 0; ia < nadd; ia++) {
        prand = ran1(Seed);
        ix = (int)((float)Xsyssize * prand);
        prand = ran1(Seed);
        iy = (int)((float)Ysyssize * prand);
        if (iy >= Ysyssize)
          iy = Ysyssize - 1;
        if (ix >= Xsyssize)
          ix = Xsyssize - 1;

        if (Ntotdiff >= NUMANTS * Isizemag) {
          freeallmem();
          bailout("chlorattack3d", "Too many ants.");
          exit(1);
        }

        Ntotdiff++;
        Xnew[Ntotdiff] = ix;
        Ynew[Ntotdiff] = iy;
        Znew[Ntotdiff] = 0;
        Ndiff[0]++;
      }
    }

    /* ... or remove them, if necessary */

    if (nadd < 0) {
      remsurf(Ndiff[0] - Nantsurf);
    }

    norg = Ntotdiff;

    /* Move each ant in turn */

    for (iant = 1; iant <= norg; iant++) {

      /* Get current location of this ant */

      antx = Xnew[iant];
      anty = Ynew[iant];
      antz = Znew[iant];

      /***
       *	Update location of ant based on a
       *	randomly chosen direction
       ***/

      ich = 1 + (int)(6.0 * ran1(Seed));
      if (ich > 6)
        ich = 6;

      cxn = antx;
      cyn = anty;
      czn = antz;

      switch (ich) {

      case 1:
        cxn = antx - 1;
        break;
      case 2:
        cxn = antx + 1;
        break;
      case 3:
        cyn = anty - 1;
        break;
      case 4:
        cyn = anty + 1;
        break;
      case 5:
        czn = antz - 1;
        break;
      case 6:
        czn = antz + 1;
        break;
      default:
        break;
      }

      cxn += checkbc(cxn, Xsyssize);
      cyn += checkbc(cyn, Ysyssize);

      /* Don't let ants leave via the top surface */

      if (czn < 0)
        ich = 0;

      if (ich != 0) {

        /* Check to see what phase ant is moving into */

        phid = Mic[cxn][cyn][czn];
        if ((phid != POROSITY) && (phid != AFMC) && (phid != CSH) &&
            (phid != ETTR) && (phid != AFM) && (phid != ETTRC4AF) &&
            (phid != EMPTYP) && (phid != DRIEDP) && (phid != C3AH6) &&
            (phid != POZZCSH) && (phid != SLAGCSH)) {

          ich = 0;

        } else if (phid == AFM) {
          ich = 0;

          /* Can't move, but can react */

          if ((ran1(Seed) < preact) && (React[cxn][cyn][czn] < SPERAFM)) {

            Clreacted[czn] += (double)(MASSCACL2 * 2.0 * (MwCl / MwCaCl2));
            React[cxn][cyn][czn]++;

            if (React[cxn][cyn][czn] == SPERAFM) {

              /***
               *	Convert to FRIEDEL with probability
               *	ptest, else ETTR
               *
               *	Plus, account for possible need for
               *	extra ETTR
               ***/

              ptest = ((2.0 / 3.0) * (Molarv[FRIEDEL] / Molarv[AFM]));
              if (ran1(Seed) < ptest) {
                Mic[cxn][cyn][czn] = FRIEDEL;
                Friedelcount[czn]++;
                Density[czn] +=
                    ((Specgrav[FRIEDEL] - Specgrav[AFM]) / MOLEFACTOR) /
                    Layer_volume;
              } else {
                Mic[cxn][cyn][czn] = ETTR;
                Ettrorig[czn]++;
                Density[czn] +=
                    ((Specgrav[ETTR] - Specgrav[AFM]) / MOLEFACTOR) /
                    Layer_volume;
              }

              ptest += (1.0 / 3.0) * (Molarv[ETTR] / Molarv[AFM]);
              if (ran1(Seed) < ptest - 1.0) {
                extphase(ETTR, cxn, cyn, czn);
              }
              Nrafm[czn]++;
              React[cxn][cyn][czn] = 0;
            }

            Ndiff[antz]--;
            ich = (-1);
          }

        } else if (phid == C3AH6) {

          ich = 0;
          if ((ran1(Seed) < preact) && (React[cxn][cyn][czn] < SPERC3AH6)) {

            Clreacted[czn] += (double)(MASSCACL2 * 2.0 * (MwCl / MwCaCl2));
            React[cxn][cyn][czn]++;
            if (React[cxn][cyn][czn] == SPERC3AH6) {
              Mic[cxn][cyn][czn] = FRIEDEL;
              Friedelcount[czn]++;
              Density[czn] +=
                  ((Specgrav[FRIEDEL] - Specgrav[C3AH6]) / MOLEFACTOR) /
                  Layer_volume;

              ptest = (Molarv[FRIEDEL] / Molarv[C3AH6]) - 1.0;
              if (ran1(Seed) < ptest) {
                extphase(FRIEDEL, cxn, cyn, czn);
              }
              Nrc3ah6[czn]++;
              React[cxn][cyn][czn] = 0;
            }

            Ndiff[antz]--;
            ich = (-1);
          }

        } else if (phid == AFMC) {

          ich = 0;
          if ((ran1(Seed) < preact) && (React[cxn][cyn][czn] < SPERAFMC)) {

            Clreacted[czn] += (double)(MASSCACL2 * 2.0 * (MwCl / MwCaCl2));
            React[cxn][cyn][czn]++;
            if (React[cxn][cyn][czn] == SPERAFMC) {
              Mic[cxn][cyn][czn] = FRIEDEL;
              Friedelcount[czn]++;
              Density[czn] +=
                  ((Specgrav[FRIEDEL] - Specgrav[AFMC]) / MOLEFACTOR) /
                  Layer_volume;

              ptest = (Molarv[FRIEDEL] / Molarv[AFMC]) - 1.0;
              if (ran1(Seed) < ptest) {
                extphase(FRIEDEL, cxn, cyn, czn);
              }

              ptest = (Molarv[CACO3] / Molarv[AFMC]);
              if (ran1(Seed) < ptest) {
                extphase(CACO3, cxn, cyn, czn);
              }

              Nrafmc[czn]++;
              React[cxn][cyn][czn] = 0;
            }

            Ndiff[antz]--;
            ich = (-1);
          }
        } else if ((phid == ETTR) && (Nrafm[czn] > (Afmorig[czn] * 0.9)) &&
                   (Nrafmc[czn] > (Afmcorig[czn] * 0.9))) {

          ich = 0;
          if ((ran1(Seed) < preact) && (React[cxn][cyn][czn] < SPERETTR)) {

            Clreacted[czn] += (double)(MASSCACL2 * 2.0 * (MwCl / MwCaCl2));
            React[cxn][cyn][czn]++;
            if (React[cxn][cyn][czn] == SPERETTR) {

              /***
               *	Need to convert current ettringite
               *	to either gypsum, friedel's salt or
               *	porosity
               ***/

              ptest = (Molarv[GYPSUM] * 3.0 / Molarv[ETTR]);
              if (ran1(Seed) < ptest) {
                Mic[cxn][cyn][czn] = GYPSUM;
                Gypsumcount[czn]++;
                Density[czn] +=
                    ((Specgrav[GYPSUM] - Specgrav[ETTR]) / MOLEFACTOR) /
                    Layer_volume;

              } else if (ran1(Seed) <
                         (ptest + Molarv[FRIEDEL] / Molarv[ETTR])) {

                Mic[cxn][cyn][czn] = FRIEDEL;
                Friedelcount[czn]++;
                Density[czn] +=
                    ((Specgrav[FRIEDEL] - Specgrav[ETTR]) / MOLEFACTOR) /
                    Layer_volume;

              } else {

                Mic[cxn][cyn][czn] = POROSITY;
                Nrcap[czn]++;
                Density[czn] +=
                    ((Specgrav[POROSITY] - Specgrav[ETTR]) / MOLEFACTOR) /
                    Layer_volume;
              }

              Nrettr[czn]++;
              React[cxn][cyn][czn] = 0;
            }

            Ndiff[antz]--;
            ich = (-1);
          }

        } else if ((phid == ETTRC4AF) && (Nrafm[czn] > (Afmorig[czn] * 0.9))) {

          ich = 0;
          if ((ran1(Seed) < preact) && (React[cxn][cyn][czn] < SPERETTRC4AF)) {

            Clreacted[czn] += (double)(MASSCACL2 * 2.0 * (MwCl / MwCaCl2));
            React[cxn][cyn][czn]++;
            if (React[cxn][cyn][czn] == SPERETTRC4AF) {
              ptest = (Molarv[GYPSUM] * 3.0 / Molarv[ETTRC4AF]);
              if (ran1(Seed) < ptest) {
                Mic[cxn][cyn][czn] = GYPSUM;
                Gypsumcount[czn]++;
                Density[czn] +=
                    ((Specgrav[GYPSUM] - Specgrav[ETTRC4AF]) / MOLEFACTOR) /
                    Layer_volume;
              } else if (ran1(Seed) <
                         (ptest + Molarv[FRIEDEL] / Molarv[ETTR])) {
                Mic[cxn][cyn][czn] = FRIEDEL;
                Friedelcount[czn]++;
                Density[czn] +=
                    ((Specgrav[FRIEDEL] - Specgrav[ETTRC4AF]) / MOLEFACTOR) /
                    Layer_volume;
              } else {
                Mic[cxn][cyn][czn] = POROSITY;
                Nrcap[czn]++;
                Density[czn] +=
                    ((Specgrav[POROSITY] - Specgrav[ETTRC4AF]) / MOLEFACTOR) /
                    Layer_volume;
              }

              Nrettrc4af[czn]++;
              React[cxn][cyn][czn] = 0;
            }

            Ndiff[antz]--;
            ich = (-1);
          }
        } else if (((phid == CSH) || (phid == POZZCSH) || (phid == SLAGCSH)) &&
                   (!sel1)) {

          Cfre = Ndiff[czn] * 1000.0 * MASSCACL2 * 2.0 * MOLEFACTOR /
                 (MwCaCl2 * (((double)Nrcap[czn]) + Nrgel[czn]));

          Cbound = (Clreactmax + Clchemisorb[czn]) * 1000.0 /
                   (Density[czn] * Layer_volume * MwCl);

          if (Cbound <= (alpha * Cfre / (1.0 + beta * Cfre))) {
            Clchemisorb[czn] += (double)(MASSCACL2 * 2.0 * (MwCl / MwCaCl2));
            Ndiff[antz]--;
            ich = (-1);
          }
        }
      }

      /* Ant stays where it is */

      if (ich == 0) {
        cxn = antx;
        cyn = anty;
        czn = antz;
      }

      /* Ant moves to new location */

      if (ich >= 0) {
        Ndiff[antz]--;
        Ndiff[czn]++;

        /* If not adsorbed, update ant data structure */

        nleft++;
        Xnew[nleft] = cxn;
        Ynew[nleft] = cyn;
        Znew[nleft] = czn;
      }
    }

    Ntotdiff = nleft;
  }

  /***
   *	Construct name of the plot file
   ***/

  nlen = strcspn(filein, ".");
  strncpy(fileroot, filein, nlen);
  strcpy(exten, &filein[nlen + 4]);
  strcpy(fplot, fileroot);
  strcat(fplot, ".cap");
  strcat(fplot, exten);

  plotfile = filehandler("chlorattack3d", fplot, "WRITE");
  if (!plotfile) {
    freeallmem();
    exit(1);
  }

  for (i = 0; i < Zsyssize + 2; i++) {
    fprintf(plotfile, "%d %d %d %d ", icyc, i, Ndiff[i], Nrettr[i]);
    fprintf(plotfile, "%d %d %d ", Nrettrc4af[i], Nrafm[i], Nrc3ah6[i]);
    fprintf(plotfile, "%d %d ", Friedelcount[i], Gypsumcount[i]);
    fprintf(plotfile, "%d %d ", Ettrorig[i], Ettrc4aforig[i]);
    fprintf(plotfile, "%d %d ", Afmorig[i], C3ah6orig[i]);
    fprintf(plotfile, "%d %d ", Friedelorig[i], Gypsumorig[i]);
    fprintf(plotfile, "%d %d ", Straingyp[i], Strainfriedel[i]);
    fprintf(plotfile, "%d %d ", Afmcorig[i], Ccorig[i]);
    fprintf(plotfile, "%d %d ", Nrafmc[i], Nrcap[i]);
    fprintf(plotfile, "%f %f ", Nrgel[i], Density[i] * MOLEFACTOR);
    fprintf(plotfile, "%f ", Clreacted[i] * MOLEFACTOR);
    fprintf(plotfile, "%f\n", Clchemisorb[i] * MOLEFACTOR);
  }
  fclose(plotfile);

  /***
   *	Output the VCCTL version number to
   *	microstructure file
   ***/

  if (write_imgheader(newmic, Xsyssize, Ysyssize, Zsyssize, Res)) {
    fclose(newmic);
    bailout("chlorattack3d", "Error writing image header");
    freeallmem();
    exit(1);
  }

  for (ix = 0; ix < Xsyssize; ix++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 1; iz < Zsyssize + 1; iz++) {

        fprintf(newmic, "%d\n", Mic[ix][iy][iz]);
      }
    }
  }

  fclose(newmic);

  freeallmem();
  return (0);
}

/***
 *	remsurf
 *
 *	Routine to remove diffusing ants from top layer to
 *	maintain proper concentration
 *
 *	Arguments:	Long integer
 *	Returns:	Void
 ***/
void remsurf(int nrem) {
  int ngone, nrleft, il, nkeep;
  char buff[MAXSTRING];

  nkeep = Ntotdiff;
  nrleft = ngone = 0;

  /***
   *	Process all diffusing species and remove the
   *	necessary number
   ***/

  for (il = 1; il <= nkeep; il++) {
    if ((Znew[il] == 0) && (ngone < nrem)) {

      /* Remove the diffusing ant */

      ngone++;
      Ntotdiff--;
      Ndiff[0]--;
    } else {
      nrleft++;
      Xnew[nrleft] = Xnew[il];
      Ynew[nrleft] = Ynew[il];
      Znew[nrleft] = Znew[il];
    }
  }

  if (Nantsurf < Ndiff[0]) {
    sprintf(buff, "Nantsurf = %d Ndiff[0] = %d", Nantsurf, Ndiff[0]);
    freeallmem();
    bailout("chlorattack3d", buff);
    exit(1);
  }
}

/***
 *	extphase
 *
 *	Routine to add a pixel of solid phase phtomake near
 *	location (xcur,ycur,zcur) in a porosity pixel
 *
 *	Arguments:	Phase id, location (xcur, ycur, zcur)
 *	Returns:	Void
 ***/
void extphase(int phtomake, int xcur, int ycur, int zcur) {
  int xtry, ytry, ztry, xi, yi, found;
  int tries = 0;

  /* Try immediate neighborhod on same level */

  xtry = xcur;
  ytry = ycur;
  ztry = zcur;
  found = 0;
  for (xi = (-2); ((xi <= 2) && (!found)); xi++) {
    for (yi = (-2); ((yi <= 2) && (!found)); yi++) {

      xtry = xcur + xi;
      ytry = ycur + yi;

      /***
       *	Apply periodic boundaries in x and y
       *	directions as needed
       ***/

      xtry += checkbc(xtry, Xsyssize);
      ytry += checkbc(ytry, Ysyssize);

      if ((Mic[xtry][ytry][ztry] == POROSITY) ||
          (Mic[xtry][ytry][ztry] == EMPTYP) ||
          (Mic[xtry][ytry][ztry] == DRIEDP)) {
        found = 1;
        Mic[xtry][ytry][ztry] = phtomake;
      }
    }
  }

  /* Try above layer if needed */

  if (!found) {
    ztry = zcur - 1;
    if (ztry > 0) {
      found = 0;
      for (xi = (-2); ((xi <= 2) && (!found)); xi++) {
        for (yi = (-2); ((yi <= 2) && (!found)); yi++) {

          xtry = xcur + xi;
          ytry = ycur + yi;

          /***
           *	Apply periodic boundaries in x and y
           *	directions as needed
           ***/

          xtry += checkbc(xtry, Xsyssize);
          ytry += checkbc(ytry, Ysyssize);

          if ((Mic[xtry][ytry][ztry] == POROSITY) ||
              (Mic[xtry][ytry][ztry] == EMPTYP) ||
              (Mic[xtry][ytry][ztry] == DRIEDP)) {
            found = 1;
            Mic[xtry][ytry][ztry] = phtomake;
          }
        }
      }
    }
  }

  /* Try below layer if needed */

  if (!found) {
    ztry = zcur + 1;
    if (ztry < Zsyssize + 1) {
      found = 0;
      for (xi = (-2); ((xi <= 2) && (!found)); xi++) {
        for (yi = (-2); ((yi <= 2) && (!found)); yi++) {

          xtry = xcur + xi;
          ytry = ycur + yi;

          /***
           *	Apply periodic boundaries in x and y
           *	directions as needed
           ***/

          xtry += checkbc(xtry, Xsyssize);
          ytry += checkbc(ytry, Ysyssize);

          if ((Mic[xtry][ytry][ztry] == POROSITY) ||
              (Mic[xtry][ytry][ztry] == EMPTYP) ||
              (Mic[xtry][ytry][ztry] == DRIEDP)) {
            found = 1;
            Mic[xtry][ytry][ztry] = phtomake;
          }
        }
      }
    }
  }

  /* Try at random on same layer */

  if (!found) {
    ztry = zcur;
    while ((tries < (int)Layer_volume) && (!found)) {
      tries++;
      xtry = Xsyssize * ran1(Seed);
      ytry = Ysyssize * ran1(Seed);
      if ((Mic[xtry][ytry][ztry] == POROSITY) ||
          (Mic[xtry][ytry][ztry] == EMPTYP) ||
          (Mic[xtry][ytry][ztry] == DRIEDP)) {
        found = 1;
        Mic[xtry][ytry][ztry] = phtomake;
      }
    }
  }

  /* Try at random on layer above */

  if (!found) {
    ztry = zcur - 1;
    tries = 0;
    if (ztry > 0) {
      while ((tries < (int)Layer_volume) && (!found)) {
        tries++;
        xtry = Xsyssize * ran1(Seed);
        ytry = Ysyssize * ran1(Seed);
        if ((Mic[xtry][ytry][ztry] == POROSITY) ||
            (Mic[xtry][ytry][ztry] == EMPTYP) ||
            (Mic[xtry][ytry][ztry] == DRIEDP)) {
          found = 1;
          Mic[xtry][ytry][ztry] = phtomake;
        }
      }
    }
  }

  /* Try at random on layer below */

  if (!found) {
    ztry = zcur + 1;
    tries = 0;
    if (ztry < Zsyssize + 1) {
      while ((tries < (int)Layer_volume) && (!found)) {
        tries++;
        xtry = Xsyssize * ran1(Seed);
        ytry = Ysyssize * ran1(Seed);
        if ((Mic[xtry][ytry][ztry] == POROSITY) ||
            (Mic[xtry][ytry][ztry] == EMPTYP) ||
            (Mic[xtry][ytry][ztry] == DRIEDP)) {
          found = 1;
          Mic[xtry][ytry][ztry] = phtomake;
        }
      }
    }
  }

  if ((phtomake == FRIEDEL) && (found)) {
    Friedelcount[ztry]++;
    Nrcap[ztry]--;
    Density[ztry] +=
        (((Specgrav[FRIEDEL] - Specgrav[AFM]) / MOLEFACTOR) / Layer_volume);
  }

  if ((phtomake == ETTR) && (found)) {
    Ettrorig[ztry]++;
    Nrcap[ztry]--;
    if (React[xcur][ycur][zcur] == SPERAFM) {
      Density[ztry] +=
          (((Specgrav[ETTR] - Specgrav[AFM]) / MOLEFACTOR) / Layer_volume);
    } else {
      Density[ztry] +=
          (((Specgrav[ETTR] - Specgrav[C3AH6]) / MOLEFACTOR) / Layer_volume);
    }

    React[xtry][ytry][ztry] = 0;
  }

  if ((phtomake == CACO3) && (found)) {
    Ccorig[ztry]++;
    Nrcap[ztry]--;
    Density[ztry] +=
        (((Specgrav[CACO3] - Specgrav[AFMC]) / MOLEFACTOR) / Layer_volume);

    React[xtry][ytry][ztry] = 0;
  }

  if (!found) {
    printf("Couldn't find a porosity pixel to create phase ");
    printf("%d at layer %d \n", phtomake, zcur);
    if (phtomake == BRUCITE) {
      Strainbrucite[zcur]++;
    } else if (phtomake == ETTR) {
      Strainettr[zcur]++;
    } else if (phtomake == GYPSUM) {
      Straingyp[zcur]++;
    } else if (phtomake == FRIEDEL) {
      Strainfriedel[zcur]++;
    }
  }
}

/***
 *	allmem
 *
 *	Attempts to dynamically allocate memory for this
 *	program.
 *
 *	Arguments:	None
 *	Returns:	Nothing
 *
 *	Calls:		sicube,ivector,fvector,sivector
 *	Called by:	main
 *
 ***/
void allmem(void) {
  Mic = sibox(Xsyssize + 2, Ysyssize + 2, Zsyssize + 2);
  React = sibox(Xsyssize + 2, Ysyssize + 2, Zsyssize + 2);
  Ndiff = ivector(Zsyssize + 2);
  Nrettr = ivector(Zsyssize + 2);
  Nrettrc4af = ivector(Zsyssize + 2);
  Nrafm = ivector(Zsyssize + 2);
  Nrc3ah6 = ivector(Zsyssize + 2);
  Afmorig = ivector(Zsyssize + 2);
  Ettrorig = ivector(Zsyssize + 2);
  Gypsumorig = ivector(Zsyssize + 2);
  C3ah6orig = ivector(Zsyssize + 2);
  Ettrc4aforig = ivector(Zsyssize + 2);
  Nrafmc = ivector(Zsyssize + 2);
  Afmcorig = ivector(Zsyssize + 2);
  Ccorig = ivector(Zsyssize + 2);
  Nrcap = ivector(Zsyssize + 2);
  Nrgel = dvector(Zsyssize + 2);
  Straingyp = ivector(Zsyssize + 2);
  Strainbrucite = ivector(Zsyssize + 2);
  Strainettr = ivector(Zsyssize + 2);
  Gypsumcount = ivector(Zsyssize + 2);
  Friedelcount = ivector(Zsyssize + 2);
  Friedelorig = ivector(Zsyssize + 2);
  Strainfriedel = ivector(Zsyssize + 2);
  Density = dvector(Zsyssize + 2);
  Clreacted = dvector(Zsyssize + 2);
  Clchemisorb = dvector(Zsyssize + 2);
  Xnew = sivector(NUMANTS * Isizemag);
  Ynew = sivector(NUMANTS * Isizemag);
  Znew = sivector(NUMANTS * Isizemag);
  if (!Znew || !Ynew || !Xnew || !Clchemisorb || !Clreacted || !Density ||
      !Strainfriedel || !Friedelcount || !Gypsumcount || !Strainettr ||
      !Strainbrucite || !Straingyp || !Nrgel || !Nrcap || !Ccorig ||
      !Afmcorig || !Nrafmc || !Ettrc4aforig || !C3ah6orig || !Gypsumorig ||
      !Ettrorig || !Afmorig || !Nrc3ah6 || !Nrafm || !Nrettrc4af || !Nrettr ||
      !Ndiff || !React || !Mic) {

    freeallmem();
    bailout("chlorattack3d", "Memory allocation error");
    exit(1);
  }

  return;
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
 *	Calls:		free_sicube, free_ivector, free_fvector, free_sivector
 *	Called by:	main
 *
 ***/
void freeallmem(void) {
  if (Mic)
    free_sibox(Mic, Xsyssize + 2, Ysyssize + 2);
  if (React)
    free_sibox(React, Xsyssize + 2, Ysyssize + 2);
  if (Ndiff)
    free_ivector(Ndiff);
  if (Nrettr)
    free_ivector(Nrettr);
  if (Nrafm)
    free_ivector(Nrafm);
  if (Nrc3ah6)
    free_ivector(Nrc3ah6);
  if (Afmorig)
    free_ivector(Afmorig);
  if (Ettrorig)
    free_ivector(Ettrorig);
  if (Gypsumorig)
    free_ivector(Gypsumorig);
  if (C3ah6orig)
    free_ivector(C3ah6orig);
  if (Ettrc4aforig)
    free_ivector(Ettrc4aforig);
  if (Nrafmc)
    free_ivector(Nrafmc);
  if (Afmcorig)
    free_ivector(Afmcorig);
  if (Ccorig)
    free_ivector(Ccorig);
  if (Nrcap)
    free_ivector(Nrcap);
  if (Nrgel)
    free_dvector(Nrgel);
  if (Straingyp)
    free_ivector(Straingyp);
  if (Strainbrucite)
    free_ivector(Strainbrucite);
  if (Strainettr)
    free_ivector(Strainettr);
  if (Strainfriedel)
    free_ivector(Strainfriedel);
  if (Gypsumcount)
    free_ivector(Gypsumcount);
  if (Friedelcount)
    free_ivector(Friedelcount);
  if (Density)
    free_dvector(Density);
  if (Clreacted)
    free_dvector(Clreacted);
  if (Clchemisorb)
    free_dvector(Clchemisorb);
  if (Xnew)
    free_sivector(Xnew);
  if (Ynew)
    free_sivector(Ynew);
  if (Znew)
    free_sivector(Znew);

  return;
}
