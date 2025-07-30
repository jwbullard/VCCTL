/******************************************************
 *
 * Program sulfattack3d to simulate diffusion/binding
 * of sulfate ions in cement, performed within a 3-D
 * pixel-based microstructure
 *
 * Date: Fall 2001            Programmers: D.P. Bentz
 *                                         E.P.Nielsen
 *
 * Model bases:
 *    Each pixel is one cubic micron
 *    Each diffusing MgSO4-- diffusing species is equivalent
 *       to 0.40311e-13 grams
 *    This means that:
 *       Each CH pixel can react with 90 diffusing MgSO4
 *       Each C3AH6 pixel can react with 20 diffusing MgSO4
 *       Each AFm pixel can react with 19 diffusing MgSO4
 *       Each AFmc pixels can react with 34 diffusing MgSO4
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

/***
 *	Are we in debugging mode or not
 ***/

#define DEBUG FALSE

#define MOLEFACTOR                                                             \
  1.0E12 /* cubic micrometers per                                              \
                                         cubic centimeter */
#define NUMANTS 500000

#define SPERCH 90    /* diffusing species per CH pixel */
#define SPERC3AH6 20 /* diffusing species per C3AH6 pixel */
#define SPERAFM 19   /* diffusing species per AFM pixel */
#define SPERAFMC 34  /* diffusing species per AFMC pixel */

/***
 *	Global variables declarations:
 *
 * 	Xsyssize,Ysyssize,Zsyssize is the system size
 * 	Res is the system resolution
 ***/
int Syspix = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
int Isizemag = 1;
float Res = DEFAULTRESOLUTION;
float Sizemag = 1.0;

/* VCCTL software version used to create input file */
float Version;

/***
 *	Mic holds the evolving microstructure
 *
 *	React holds the number of reacted diffusing species
 *	at each reactive pixel site
 ***/

int *Seed;
short int ***Mic, ***React;
int *Ndiff, *Nrch, *Nrafm, *Nrc3ah6;
int *Afmorig, *Noch, *Ettrorig, *Bruciteorig;
int *Gypsumorig, *C3ah6orig, *Ettrc4aforig;
int *Chorig, *Nrafmc, *Afmcorig, *Ccorig;
double *Nrgel;
int *Nrcap;
float *Strainbrucite, *Strainettr, *Strainafm, *Straingyp;
float Layer_volume;

/***
 * coordinates of diffusing species in (Xnew,Ynew,Znew)
 ***/

short int *Xnew, *Ynew, *Znew;
int Nantsurf, Ntotdiff = 0;
double Molesperpixel[MS + 1];

/***
 *	Function declarations
 ***/

void remsurf(int nrem);
void extphase(int phtomake, int xcur, int ycur, int zcur);
int distchreac(int ztodo);
void removech(int xcur, int ycur, int zcur);
void allmem(void);
void freeallmem(void);

#include "include/properties.h"

int main(void) {
  int ix, iy, iz, seed1, nlen;
  int i, antx, anty, antz, ich, inval, oinval;
  int cxn, cyn, czn, phid, initdepth, outfreq;
  int ia, ncyc, icyc, iant, nleft, norg, nadd, numadd;
  int chinit = 0, afminit = 0, c3ah6init = 0, ettrinit = 0, ettrc4init = 0;
  float prand, preact, ptest, sulfconc = 0.0;
  double volume_available;
  char filein[MAXSTRING], fileout[MAXSTRING], buff[MAXSTRING];
  char fplot[MAXSTRING], exten[MAXSTRING], fileroot[MAXSTRING];
  char strsuff[MAXSTRING], instring[MAXSTRING];
  FILE *micfile, *newmic, *plotfile;

  /* Initialize global array Molesperpixel */

  for (ix = 0; ix <= MS; ix++) {
    Molesperpixel[ix] = 0.0;
  }

  Mic = NULL;
  React = NULL;
  Ndiff = NULL;
  Nrch = NULL;
  Nrafm = NULL;
  Nrc3ah6 = NULL;
  Afmorig = NULL;
  Noch = NULL;
  Ettrorig = NULL;
  Bruciteorig = NULL;
  Gypsumorig = NULL;
  C3ah6orig = NULL;
  Ettrc4aforig = NULL;
  Chorig = NULL;
  Nrafmc = NULL;
  Afmcorig = NULL;
  Ccorig = NULL;
  Nrcap = NULL;
  Nrgel = NULL;
  Straingyp = NULL;
  Strainbrucite = NULL;
  Strainettr = NULL;
  Strainafm = NULL;

  /* Establish needed specific gravities and molar volumes */

  for (ix = 0; ix <= MS; ix++) {
    Molesperpixel[ix] = 0.0;
  }

  Molesperpixel[CH] = 1.0 / Molarv[CH] / MOLEFACTOR;
  Molesperpixel[MS] = 1.0 / Molarv[MS] / MOLEFACTOR;
  Molesperpixel[GYPSUM] = 1.0 / Molarv[GYPSUM] / MOLEFACTOR;
  Molesperpixel[C3AH6] = 1.0 / Molarv[C3AH6] / MOLEFACTOR;
  Molesperpixel[BRUCITE] = 1.0 / Molarv[BRUCITE] / MOLEFACTOR;
  Molesperpixel[AFM] = 1.0 / Molarv[AFM] / MOLEFACTOR;
  Molesperpixel[ETTR] = 1.0 / Molarv[ETTR] / MOLEFACTOR;

  /* Get user input */

  printf("Enter random number seed \n");
  read_string(instring, sizeof(instring));
  seed1 = atoi(instring);
  if (seed1 > 0)
    seed1 = (-1 * seed1);
  printf("Random seed: %d \n", seed1);
  Seed = (&seed1);
  printf("Enter name of file with input microstructure \n");
  read_string(filein, sizeof(filein));
  printf("File for input: %s\n", filein);
  printf("Enter name of file with final microstructure \n");
  read_string(fileout, sizeof(fileout));
  printf("File for final microstructure: %s\n", fileout);
  printf("Enter molarity of sulfate solution (0.0,1.0)\n");
  read_string(instring, sizeof(instring));
  sulfconc = atof(instring);
  printf("Molarity of sulfate agents: %f\n", sulfconc);

  printf("Enter initial penetration depth of sulfates \n");
  read_string(instring, sizeof(instring));
  initdepth = atoi(instring);
  printf("Initial penetration depth: %d\n", initdepth);
  printf("Enter reaction probability for sulfate attack \n");
  read_string(instring, sizeof(instring));
  preact = atof(instring);
  printf("Reaction probability for sulfate attack: %f\n", preact);
  printf("Enter number of cycles to execute \n");
  read_string(instring, sizeof(instring));
  ncyc = atoi(instring);
  printf("Number of cycles: %d\n", ncyc);
  printf("Output full microstructure once every? (cycles) \n");
  read_string(instring, sizeof(instring));
  outfreq = atoi(instring);
  printf("Output frequency: %d\n", outfreq);
  if (outfreq <= 0)
    outfreq = ncyc + 1;

  /* Read in microstructure from datafile */

  micfile = filehandler("sulfattack3d", filein, "READ");
  if (!micfile) {
    exit(1);
  }

  /***
   *	Determine whether software version, system size
   *	and resolution are specified in the image file
   ***/

  if (read_imgheader(micfile, &Version, &Xsyssize, &Ysyssize, &Zsyssize,
                     &Res)) {
    fclose(micfile);
    bailout("sulfattack3d", "Error reading image header");
    exit(1);
  }

  /***
   *	Convert molarity to number of ants per pixel
   ***/

  sulfconc = (sulfconc / 0.334892) * Res * Res * Res;

  Syspix = Xsyssize * Ysyssize * Zsyssize;
  Sizemag = ((float)Syspix) / (pow(((double)DEFAULTSYSTEMSIZE), 3.0));
  Isizemag = (int)(Sizemag + 0.5);

  printf("\nXsyssize is %d", Xsyssize);
  printf("\nYsyssize is %d", Ysyssize);
  printf("\nZsyssize is %d\n", Zsyssize);
  printf("Res is %f\n", Res);
  fflush(stdout);

  /* Define the 'volume' per layer */

  Layer_volume = (float)(Xsyssize * Ysyssize);

  /***
   *	Must now allocate memory for all the arrays
   ***/

  allmem();

  /***
   *	Set up boundary conditions:
   *
   *	all porosity at top surface
   *	all solid material at bottom surface
   ***/

  for (ix = 0; ix < Xsyssize; ix++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      Mic[ix][iy][0] = 0;
      Mic[ix][iy][Zsyssize + 1] = 1;
      React[ix][iy][0] = React[ix][iy][Zsyssize + 1] = 0;
    }
  }

  /* Initialize array of original AFM counts and reacted counts */

  for (iz = 0; iz < Zsyssize + 2; iz++) {
    Ndiff[iz] = 0;
    Nrch[iz] = 0;
    Nrafm[iz] = 0;
    Nrc3ah6[iz] = 0;
    Straingyp[iz] = 0;
    Strainettr[iz] = 0;
    Strainbrucite[iz] = 0;
    Strainafm[iz] = 0;
    Afmorig[iz] = 0;
    Nrcap[iz] = 0;
    Nrgel[iz] = 0.0;
    Bruciteorig[iz] = 0;
    Ettrorig[iz] = 0;
    Gypsumorig[iz] = 0;
    Ettrc4aforig[iz] = 0;
    Chorig[iz] = 0;
    C3ah6orig[iz] = 0;
    Noch[iz] = 0;
    Afmcorig[iz] = 0;
    Nrafmc[iz] = 0;
    Ccorig[iz] = 0;
  }

  for (iz = 1; iz < Zsyssize + 1; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {
        if (feof(micfile)) {
          freeallmem();
          bailout("sulfattack3d", "End of file encountered");
          exit(1);
        }

        fscanf(micfile, "%s", instring);
        oinval = atoi(instring);
        inval = convert_id(oinval, Version);
        Mic[ix][iy][iz] = inval;
        React[ix][iy][iz] = 0;

        if (inval == CH) {
          chinit++;
          Chorig[iz]++;
        }

        if (inval == ETTR) {
          ettrinit++;
          Ettrorig[iz]++;
        }

        if (inval == ETTRC4AF) {
          ettrc4init++;
          Ettrc4aforig[iz]++;
        }

        if (inval == AFM) {
          afminit++;
          Afmorig[iz]++;
        }

        if (inval == C3AH6) {
          c3ah6init++;
          C3ah6orig[iz]++;
        }

        if (inval == AFMC)
          Afmcorig[iz]++;
        if (inval == CACO3)
          Ccorig[iz]++;
        if (inval == BRUCITE)
          Bruciteorig[iz]++;
        if (inval == GYPSUM)
          Gypsumorig[iz]++;

        /***
         *	Check if the pixel is in capillary pore space ...
         ***/

        if ((inval == POROSITY) || (inval == EMPTYP) || (inval == DIFFCSH) ||
            (inval == DIFFCH) || (inval == DIFFGYP) || (inval == DIFFC3A) ||
            (inval == DIFFC4A) || (inval == DIFFFH3) || (inval == DIFFETTR) ||
            (inval == DIFFCACO3) || (inval == DIFFAS) || (inval == DIFFANH) ||
            (inval == DIFFHEM) || (inval == DIFFCAS2) || (inval == DIFFCACL2) ||
            (inval == DRIEDP) || (inval == EMPTYDP) || (inval == MS)) {

          Nrcap[iz]++;

        } else if (inval == CSH) {

          /***
           *	... or is in normal C-S-H gel space ...
           ***/

          Nrgel[iz] += 0.38;

        } else if ((inval == POZZCSH) || (inval == SLAGCSH)) {

          /***
           *	... or is in pozzolanic C-S-H or slag
           *	hydration product.
           ***/

          Nrgel[iz] += 0.20;
        }
      }
    }
  }

  fclose(micfile);
  printf("Initial counts for CH, AFM, C3AH6 and ettringite(2) are %d, %d, "
         "%d, %d, and %d.\n",
         chinit, afminit, c3ah6init, ettrinit, ettrc4init);
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
    volume_available = ((double)Nrcap[iz] + Nrgel[iz]);
    numadd = sulfconc * volume_available;

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
          bailout("sulfattack3d", "Too many ants");
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
   *	Main loop for sulfate attack
   ***/

  /***
   *	Determine the number of ants to maintain at the surface
   *	throughout the simulation
   ***/

  Nantsurf = sulfconc * Layer_volume;

  for (icyc = 1; icyc <= ncyc; icyc++) {
    nleft = 0;
    nadd = Nantsurf - Ndiff[0]; /* number ants left to add */
    if (nadd > 0) {
      for (ia = 0; ia < nadd; ia++) {
        prand = ran1(Seed);
        ix = (int)((float)Xsyssize * prand);
        prand = ran1(Seed);
        iy = (int)((float)Ysyssize * prand);

        if (Ntotdiff >= NUMANTS * Isizemag) {
          freeallmem();
          bailout("sulfattack3d", "Too many ants");
          exit(1);
        }
        Ntotdiff++;
        Xnew[Ntotdiff] = ix;
        Ynew[Ntotdiff] = iy;
        Znew[Ntotdiff] = 0;
        Ndiff[0]++;
      }
    }

    /* Or remove them, if necessary */

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
       *	Update location of ant based on a randomly
       *	chosen direction
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

      /***
       *	Adjust for periodic boundary conditions if necessary
       ***/

      cxn += checkbc(cxn, Xsyssize);
      cyn += checkbc(cyn, Ysyssize);

      /* Don't let ants leave via the top surface */

      if (czn < 0)
        ich = 0;

      if (ich != 0) {

        /* Check to see what phase ant is moving into */

        phid = Mic[cxn][cyn][czn];
        if ((phid != POROSITY) && (phid != AFMC) && (phid != CSH) &&
            (phid != CH) && (phid != AFM) && (phid != EMPTYP) &&
            (phid != DRIEDP) && (phid != C3AH6) && (phid != POZZCSH) &&
            (phid != SLAGCSH)) {
          ich = 0;
        }
        if ((phid == CH) && (Nrafm[czn] < (Afmorig[czn] * 0.85)) &&
            (Nrafmc[czn] < (Afmcorig[czn] * 0.85))) {
          ich = 0;
        } else if (phid == AFM) {
          ich = 0;

          /* Can't move, but can react */

          if ((ran1(Seed) < preact) && (React[cxn][cyn][czn] < SPERAFM)) {

            React[cxn][cyn][czn]++;
            if (React[cxn][cyn][czn] == SPERAFM) {
              React[cxn][cyn][czn] = 0;
              Mic[cxn][cyn][czn] = ETTR;
              Ettrorig[czn]++;
              extphase(ETTR, cxn, cyn, czn);
              ptest = (Molarv[ETTR] / Molarv[AFM]) - 2.0;
              if (ran1(Seed) < ptest) {
                extphase(ETTR, cxn, cyn, czn);
              }
              ptest = (2.0 * Molarv[BRUCITE] / Molarv[AFM]);
              if (ran1(Seed) < ptest) {
                extphase(BRUCITE, cxn, cyn, czn);
              }

              /* deplete CH as needed */

              ptest = (2.0 * Molarv[CH] / Molarv[AFM]);
              if (ran1(Seed) < ptest) {
                removech(cxn, cyn, czn);
              }
              Nrafm[czn]++;
            }
            Ndiff[antz]--;
            ich = (-1);
          }
        } else if (phid == C3AH6) {
          ich = 0;
          if ((ran1(Seed) < preact) && (React[cxn][cyn][czn] < SPERC3AH6)) {

            React[cxn][cyn][czn]++;

            if (React[cxn][cyn][czn] == SPERC3AH6) {
              Mic[cxn][cyn][czn] = AFM;
              Afmorig[czn]++;
              React[cxn][cyn][czn] = 0;
              extphase(AFM, cxn, cyn, czn);
              ptest = (Molarv[AFM] / Molarv[C3AH6]) - 2.0;
              if (ran1(Seed) < ptest) {
                extphase(AFM, cxn, cyn, czn);
              }
              ptest = (Molarv[BRUCITE] / Molarv[C3AH6]);
              if (ran1(Seed) < ptest) {
                extphase(BRUCITE, cxn, cyn, czn);
              }

              /* deplete CH as needed */

              ptest = (Molarv[CH] / Molarv[C3AH6]);
              if (ran1(Seed) < ptest) {
                removech(cxn, cyn, czn);
              }
              Nrc3ah6[czn]++;
            }

            Ndiff[antz]--;
            ich = (-1);
          }
        } else if (phid == AFMC) {
          ich = 0;
          if ((ran1(Seed) < preact) && (React[cxn][cyn][czn] < SPERAFMC)) {

            React[cxn][cyn][czn]++;

            if (React[cxn][cyn][czn] == SPERAFMC) {
              Mic[cxn][cyn][czn] = ETTR;
              React[cxn][cyn][czn] = 0;
              Ettrorig[czn]++;
              extphase(ETTR, cxn, cyn, czn);
              ptest = (Molarv[ETTR] / Molarv[AFMC]) - 2.0;
              if (ran1(Seed) < ptest) {
                extphase(ETTR, cxn, cyn, czn);
              }
              ptest = (Molarv[CACO3] / Molarv[AFMC]);
              if (ran1(Seed) < ptest) {
                extphase(CACO3, cxn, cyn, czn);
              }
              ptest = 3. * (Molarv[BRUCITE] / Molarv[AFMC]);
              if (ran1(Seed) < ptest) {
                extphase(BRUCITE, cxn, cyn, czn);
              }
              ptest = (3. * Molarv[CH] / Molarv[AFMC]);
              if (ran1(Seed) < ptest) {
                removech(cxn, cyn, czn);
              }

              Nrafmc[czn]++;
            }

            Ndiff[antz]--;
            ich = (-1);
          }

          /***
           *	CH is only reactive after AFM
           *	has been locally 85% consumed
           ***/

        } else if ((phid == CH) && (Nrafm[czn] > (Afmorig[czn] * 0.85)) &&
                   (Nrafmc[czn] > (Afmcorig[czn] * 0.85))) {

          ich = 0;
          if ((ran1(Seed) < preact) && (React[cxn][cyn][czn] < SPERCH)) {

            React[cxn][cyn][czn]++;
            if (React[cxn][cyn][czn] == SPERCH) {
              Mic[cxn][cyn][czn] = GYPSUM;
              React[cxn][cyn][czn] = 0;
              Gypsumorig[czn]++;
              extphase(GYPSUM, cxn, cyn, czn);
              ptest = (Molarv[GYPSUM] / Molarv[CH]) - 2.0;
              if (ran1(Seed) < ptest) {
                extphase(GYPSUM, cxn, cyn, czn);
              }
              ptest = (Molarv[BRUCITE] / Molarv[CH]);
              if (ran1(Seed) < ptest) {
                extphase(BRUCITE, cxn, cyn, czn);
              }
              Nrch[czn]++;
            }
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

    /***
     *	Output the microstructure every outfreq cycles
     ***/

    if (icyc > 0 && (icyc % outfreq == 0)) {

      strcpy(buff, fileout);
      sprintf(strsuff, ".%d-%d", icyc, ncyc);
      strcat(buff, strsuff);
      newmic = filehandler("sulfattack3d", buff, "WRITE");
      if (!newmic) {
        freeallmem();
        exit(1);
      }

      /***
       *	Output the software version to the
       *	microstructure image
       ***/

      if (write_imgheader(newmic, Xsyssize, Ysyssize, Zsyssize, Res)) {
        fclose(newmic);
        bailout("sulfattack3d", "Error writing image header");
        exit(1);
      }

      for (iz = 1; iz < Zsyssize + 1; iz++) {
        for (iy = 0; iy < Ysyssize; iy++) {
          for (ix = 0; ix < Xsyssize + 1; ix++) {
            fprintf(newmic, "%d\n", Mic[ix][iy][iz]);
          }
        }
      }

      fclose(newmic);
    }
  }

  /***
   *	Construct name of the plot file
   ***/

  nlen = strcspn(filein, ".");
  strncpy(fileroot, filein, nlen);
  strcpy(exten, &filein[nlen + 4]);
  strcpy(fplot, fileroot);
  strcat(fplot, ".sap");
  strcat(fplot, exten);

  plotfile = filehandler("sulfattack3d", fplot, "WRITE");
  if (!plotfile) {
    freeallmem();
    exit(1);
  }

  for (i = 0; i < Zsyssize + 2; i++) {
    fprintf(plotfile, "%d %d %d %d ", icyc, i, Ndiff[i], Nrch[i]);
    fprintf(plotfile, "%d %d %d ", Nrafm[i], Nrc3ah6[i], Nrcap[i]);
    fprintf(plotfile, "%f %f ", Nrgel[i], Straingyp[i]);
    fprintf(plotfile, "%f %f ", Strainbrucite[i], Strainettr[i]);
    fprintf(plotfile, "%f %d %d ", Strainafm[i], Chorig[i], Ettrorig[i]);
    fprintf(plotfile, "%d %d ", Ettrc4aforig[i], Afmorig[i]);
    fprintf(plotfile, "%d %d ", Gypsumorig[i], Bruciteorig[i]);
    fprintf(plotfile, "%d %d %d ", C3ah6orig[i], Noch[i], Afmcorig[i]);
    fprintf(plotfile, "%d %d\n", Ccorig[i], Nrafmc[i]);
  }
  fclose(plotfile);

  newmic = filehandler("sulfattack3d", fileout, "WRITE");
  if (!newmic) {
    freeallmem();
    exit(1);
  }

  /***
   *	Output the image header to the final
   *	microstructure
   ***/

  if (write_imgheader(newmic, Xsyssize, Ysyssize, Zsyssize, Res)) {
    fclose(newmic);
    bailout("sulfattack3d", "Error writing image header");
    freeallmem();
    exit(1);
  }

  for (iz = 1; iz < Zsyssize + 1; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {
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
 *	Arguments:	int nrem
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
    bailout("sulfattack3d", buff);
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

  if (found) {
    if (phtomake == AFM) {
      Afmorig[ztry]++;
      Nrcap[ztry]--;
    } else if (phtomake == BRUCITE) {
      Bruciteorig[ztry]++;
      Nrcap[ztry]--;
    } else if (phtomake == ETTR) {
      Ettrorig[ztry]++;
      Nrcap[ztry]--;
    } else if (phtomake == GYPSUM) {
      Gypsumorig[ztry]++;
      Nrcap[ztry]--;
    } else if (phtomake == CACO3) {
      Ccorig[ztry]++;
      Nrcap[ztry]--;
    }

    /* Clear out reaction counter for this pixel */

    React[xtry][ytry][ztry] = 0;

  } else {

    /* Update appropriate strain counter */

    printf("Couldn't find a porosity pixel to create phase ");
    printf("%d at layer %d \n", phtomake, zcur);
    fflush(stdout);
    if (phtomake == BRUCITE) {
      Strainbrucite[zcur] += 1.0;
    } else if (phtomake == ETTR) {
      Strainettr[zcur] += 1.0;
    } else if (phtomake == GYPSUM) {
      Straingyp[zcur] += 1.0;
    } else if (phtomake == AFM) {
      Strainafm[zcur] += 1.0;
    }
  }

  return;
}

/***
 *
 *	distchreac
 *
 *	Routine to
 *
 *	Arguments:	Integer z coordinate
 *	Returns:	Integer found (0 if failure, 1 if success)
 *
 ***/
int distchreac(int ztodo) {
  int xtry, ytry, ztry, found = 0, tries = 0;

  /* Try at random on same layer */

  ztry = ztodo;

  while ((tries < (int)Layer_volume) && (!found)) {
    tries++;
    xtry = Xsyssize * ran1(Seed);
    ytry = Ysyssize * ran1(Seed);
    if ((Mic[xtry][ytry][ztry] == CH) &&
        (React[xtry][ytry][ztry] < (SPERCH - 1))) {

      found = 1;
      React[xtry][ytry][ztry]++;
    }
  }

  /* Try at random on layer above */

  if (!found) {
    ztry = ztodo - 1;
    tries = 0;
    if (ztry > 0) {
      while ((tries < (int)Layer_volume) && (!found)) {
        tries++;
        xtry = Xsyssize * ran1(Seed);
        ytry = Ysyssize * ran1(Seed);
        if ((Mic[xtry][ytry][ztry] == CH) &&
            (React[xtry][ytry][ztry] < (SPERCH - 1))) {

          found = 1;
          React[xtry][ytry][ztry]++;
        }
      }
    }
  }

  /* Try at random on layer below */

  if (!found) {
    ztry = ztodo + 1;
    tries = 0;
    if (ztry < Zsyssize + 1) {
      while ((tries < (int)Layer_volume) && (!found)) {
        tries++;
        xtry = Xsyssize * ran1(Seed);
        ytry = Ysyssize * ran1(Seed);
        if ((Mic[xtry][ytry][ztry] == CH) &&
            (React[xtry][ytry][ztry] < (SPERCH - 1))) {
          found = 1;
          React[xtry][ytry][ztry]++;
        }
      }
    }
  }

  return (found);
}

/***
 *
 *	removech
 *
 *	Routine to remove a pixel of CH near
 *	location (xcur,ycur,zcur) and replace it with a porosity pixel
 *
 *	Arguments:	Integer coordinates (xcur, ycur, zcur)
 *	Returns:	Void
 ***/
void removech(int xcur, int ycur, int zcur) {
  int xtry, ytry, ztry, xi, yi, found, remflag;
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

      if (Mic[xtry][ytry][ztry] == CH) {
        found = 1;
        Mic[xtry][ytry][ztry] = POROSITY;
        Nrch[ztry]++;
        Nrcap[ztry]++;
      }
    }
  }

  /* Try above layer if needed */

  if (!found) {
    ztry = zcur - 1;
    if (ztry > 0) {
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

          if (Mic[xtry][ytry][ztry] == CH) {
            found = 1;
            Mic[xtry][ytry][ztry] = POROSITY;
            Nrch[ztry]++;
            Nrcap[ztry]++;
          }
        }
      }
    }
  }

  /* Try below layer if needed */

  if (!found) {
    ztry = zcur + 1;
    if (ztry < Zsyssize + 1) {
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

          if (Mic[xtry][ytry][ztry] == CH) {
            found = 1;
            Mic[xtry][ytry][ztry] = POROSITY;
            Nrch[ztry]++;
            Nrcap[ztry]++;
          }
        }
      }
    }
  }

  if (!found) {

    /* Try at random on same layer */

    ztry = zcur;
    while ((tries < (int)Layer_volume) && (!found)) {
      tries++;
      xtry = Xsyssize * ran1(Seed);
      ytry = Ysyssize * ran1(Seed);
      if (Mic[xtry][ytry][ztry] == CH) {
        found = 1;
        Mic[xtry][ytry][ztry] = POROSITY;
        Nrch[ztry]++;
        Nrcap[ztry]++;
      }
    }
  }

  if (!found) {

    /* Try at random on layer above */

    ztry = zcur - 1;
    tries = 0;
    if (ztry > 0) {
      while ((tries < (int)Layer_volume) && (!found)) {
        tries++;
        xtry = Xsyssize * ran1(Seed);
        ytry = Ysyssize * ran1(Seed);
        if (Mic[xtry][ytry][ztry] == CH) {
          found = 1;
          Mic[xtry][ytry][ztry] = POROSITY;
          Nrch[ztry]++;
          Nrcap[ztry]++;
        }
      }
    }
  }

  if (!found) {

    /* Try at random on layer below */

    ztry = zcur + 1;
    tries = 0;
    if (ztry < Zsyssize + 1) {
      while ((tries < (int)Layer_volume) && (!found)) {
        tries++;
        xtry = Xsyssize * ran1(Seed);
        ytry = Ysyssize * ran1(Seed);
        if (Mic[xtry][ytry][ztry] == CH) {
          found = 1;
          Mic[xtry][ytry][ztry] = POROSITY;
          Nrch[ztry]++;
          Nrcap[ztry]++;
        }
      }
    }
  }

  if (!found) {
    Noch[zcur]++;
  } else {

    /* Account for partially reacted CH pixels */

    while (React[xtry][ytry][ztry] > 0) {
      React[xtry][ytry][ztry]--;
      remflag = distchreac(ztry);
      if (!remflag) {
        printf("Could not distribute CH reaction at layer %d \n", ztry);
        fflush(stdout);
      }
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
 *	Calls:		sibox,ivector,fvector,sivector
 *	Called by:	main
 *
 ***/
void allmem(void) {
  Mic = sibox(Xsyssize + 2, Ysyssize + 2, Zsyssize + 2);
  React = sibox(Xsyssize + 2, Ysyssize + 2, Zsyssize + 2);
  Ndiff = ivector(Zsyssize + 2);
  Nrch = ivector(Zsyssize + 2);
  Nrafm = ivector(Zsyssize + 2);
  Nrc3ah6 = ivector(Zsyssize + 2);
  Afmorig = ivector(Zsyssize + 2);
  Noch = ivector(Zsyssize + 2);
  Ettrorig = ivector(Zsyssize + 2);
  Bruciteorig = ivector(Zsyssize + 2);
  Gypsumorig = ivector(Zsyssize + 2);
  C3ah6orig = ivector(Zsyssize + 2);
  Ettrc4aforig = ivector(Zsyssize + 2);
  Chorig = ivector(Zsyssize + 2);
  Nrafmc = ivector(Zsyssize + 2);
  Afmcorig = ivector(Zsyssize + 2);
  Ccorig = ivector(Zsyssize + 2);
  Nrcap = ivector(Zsyssize + 2);
  Nrgel = dvector(Zsyssize + 2);
  Straingyp = fvector(Zsyssize + 2);
  Strainbrucite = fvector(Zsyssize + 2);
  Strainettr = fvector(Zsyssize + 2);
  Strainafm = fvector(Zsyssize + 2);
  Xnew = sivector(NUMANTS * Isizemag);
  Ynew = sivector(NUMANTS * Isizemag);
  Znew = sivector(NUMANTS * Isizemag);

  if (!Mic || !React || !Ndiff || !Nrch || !Nrafm || !Nrc3ah6 || !Afmorig ||
      !Noch || !Ettrorig || !Bruciteorig || !Gypsumorig || !C3ah6orig ||
      !Ettrc4aforig || !Chorig || !Nrafmc || !Afmcorig || !Ccorig || !Nrcap ||
      !Nrgel || !Straingyp || !Strainbrucite || Strainettr || Strainafm ||
      Xnew || Ynew || Znew) {

    freeallmem();
    bailout("sulfattack3d", "Memory allocation failure");
    fflush(stdout);
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
 *	Calls:		free_sibox, free_ivector, free_fvector, free_sivector
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
  if (Nrch)
    free_ivector(Nrch);
  if (Nrafm)
    free_ivector(Nrafm);
  if (Nrc3ah6)
    free_ivector(Nrc3ah6);
  if (Afmorig)
    free_ivector(Afmorig);
  if (Noch)
    free_ivector(Noch);
  if (Ettrorig)
    free_ivector(Ettrorig);
  if (Bruciteorig)
    free_ivector(Bruciteorig);
  if (Gypsumorig)
    free_ivector(Gypsumorig);
  if (C3ah6orig)
    free_ivector(C3ah6orig);
  if (Ettrc4aforig)
    free_ivector(Ettrc4aforig);
  if (Chorig)
    free_ivector(Chorig);
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
    free_fvector(Straingyp);
  if (Strainbrucite)
    free_fvector(Strainbrucite);
  if (Strainettr)
    free_fvector(Strainettr);
  if (Strainafm)
    free_fvector(Strainafm);
  if (Xnew)
    free_sivector(Xnew);
  if (Ynew)
    free_sivector(Ynew);
  if (Znew)
    free_sivector(Znew);

  return;
}
