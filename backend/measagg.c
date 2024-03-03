/******************************************************
 *
 * Program measagg.c to measure phase fractions as a function
 * of distance away from an aggregate surface
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
#include <stdio.h>
#include <stdlib.h>

#define AGGPH 28

/***
 *	Global variables
 ***/
int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
float Res = DEFAULTRESOLUTION;

/* VCCTL software version used to create input file */
float Version;

int main(void) {
  register int i, j, k, iy, iz;
  short int ***mic;
  int phase[NPHASES], ptot, valin, ovalin, ixmin, ixmax;
  int icnt, ixlo, ixhi, phid, idist, aggsize;
  char filein[MAXSTRING], fileout[MAXSTRING], instring[MAXSTRING];
  FILE *infile, *aggfile;

  printf("Enter name of file with the image to be analyzed \n");
  read_string(filein, sizeof(filein));

  infile = filehandler("measagg", filein, "READ");
  if (!infile) {
    exit(1);
  }

  /***
   *	Determine whether system size and resolution
   *	are specified in the image file
   ***/

  if (read_imgheader(infile, &Version, &Xsyssize, &Ysyssize, &Zsyssize, &Res)) {
    fclose(infile);
    bailout("measagg", "Error reading image header");
    exit(1);
  }

  printf("\nXsyssize is %d", Xsyssize);
  printf("\nYsyssize is %d", Ysyssize);
  printf("\nZsyssize is %d\n", Zsyssize);
  printf("Res is %f\n", Res);
  fflush(stdout);

  /***
   *	Allocate memory for mic array
   ***/

  mic = sibox(Xsyssize, Ysyssize, Zsyssize);
  if (!mic) {
    bailout("measagg", "Could not allocate memory for mic array");
    exit(1);
  }

  ixmin = Xsyssize - 1;
  ixmax = 0;

  /***
   *	Read the microstructure and determine
   *	aggregate limits
   ***/

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valin = convert_id(ovalin, Version);

        if ((valin == INERTAGG) && (i < ixmin)) {
          ixmin = i;
        }

        if ((valin == INERTAGG) && (i > ixmax)) {
          ixmax = i;
        }

        mic[i][j][k] = valin;
      }
    }
  }

  fclose(infile);
  printf("ixmin and ixmax are %d and %d \n", ixmin, ixmax);
  printf("Enter name of file to write \n");
  read_string(fileout, sizeof(fileout));
  aggfile = filehandler("measagg", fileout, "WRITE");
  if (!aggfile) {
    free_sibox(mic, Xsyssize, Ysyssize);
    exit(1);
  }

  printf("Distance ");
  fprintf(aggfile, "Distance ");
  for (i = POROSITY; i < NPHASES; i++) {
    switch (i) {
    case POROSITY:
      printf("Porosity  ");
      fprintf(aggfile, "Porosity  ");
      break;
    case C3S:
      printf("C3S (Cement) ");
      fprintf(aggfile, "C3S (Cement) ");
      break;
    case C2S:
      printf("C2S ");
      fprintf(aggfile, "C2S ");
      break;
    case C3A:
      printf("C3A ");
      fprintf(aggfile, "C3A ");
      break;
    case C4AF:
      printf("C4AF ");
      fprintf(aggfile, "C4AF ");
      break;
    case GYPSUM:
      printf("Gypsum ");
      fprintf(aggfile, "Gypsum ");
      break;
    case HEMIHYD:
      printf("Hemihydrate ");
      fprintf(aggfile, "Hemihydrate ");
      break;
    case ANHYDRITE:
      printf("Anhydrite ");
      fprintf(aggfile, "Anhydrite ");
      break;
    case K2SO4:
      printf("K2SO4 ");
      fprintf(aggfile, "K2SO4 ");
      break;
    case NA2SO4:
      printf("NA2SO4 ");
      fprintf(aggfile, "NA2SO4 ");
      break;
    case SFUME:
      printf("SilicaFume ");
      fprintf(aggfile, "SilicaFume ");
      break;
    case INERT:
      printf("Inert ");
      fprintf(aggfile, "Inert ");
      break;
    case SLAG:
      printf("Slag ");
      fprintf(aggfile, "Slag ");
      break;
    case ASG:
      printf("ASG ");
      fprintf(aggfile, "ASG ");
      break;
    case CAS2:
      printf("CAS2 ");
      fprintf(aggfile, "CAS2 ");
      break;
    case FAC3A:
      printf("FAC3A ");
      fprintf(aggfile, "FAC3A ");
      break;
    case FLYASH:
      printf("FlyAsh ");
      fprintf(aggfile, "FlyAsh ");
      break;
    case CH:
      printf("CH ");
      fprintf(aggfile, "CH ");
      break;
    case CSH:
      printf("CSH ");
      fprintf(aggfile, "CSH ");
      break;
    case C3AH6:
      printf("C3AH6 ");
      fprintf(aggfile, "C3AH6 ");
      break;
    case ETTR:
      printf("ETTR ");
      fprintf(aggfile, "ETTR ");
      break;
    case ETTRC4AF:
      printf("ETTRC4AF ");
      fprintf(aggfile, "ETTRC4AF ");
      break;
    case AFM:
      printf("AFm ");
      fprintf(aggfile, "AFm ");
      break;
    case FH3:
      printf("FH3 ");
      fprintf(aggfile, "FH3 ");
      break;
    case POZZCSH:
      printf("PozzCSH ");
      fprintf(aggfile, "PozzCSH ");
      break;
    case SLAGCSH:
      printf("SlagCSH ");
      fprintf(aggfile, "SlagCSH ");
      break;
    case CACL2:
      printf("CaCl2 ");
      fprintf(aggfile, "CaCl2 ");
      break;
    case FRIEDEL:
      printf("Friedel ");
      fprintf(aggfile, "Friedel ");
      break;
    case STRAT:
      printf("Strat ");
      fprintf(aggfile, "Strat ");
      break;
    case GYPSUMS:
      printf("GYPSUMS ");
      fprintf(aggfile, "GYPSUMS ");
      break;
    case ABSGYP:
      printf("AbsGyp ");
      fprintf(aggfile, "AbsGyp ");
      break;
    case CACO3:
      printf("CaCO3 ");
      fprintf(aggfile, "CaCO3 ");
      break;
    case AFMC:
      printf("AFmC ");
      fprintf(aggfile, "AFmC ");
      break;
    case BRUCITE:
      printf("Brucite ");
      fprintf(aggfile, "Brucite ");
      break;
    case MS:
      printf("MS ");
      fprintf(aggfile, "MS ");
      break;
    case EMPTYP:
      printf("EmptyPor");
      fprintf(aggfile, "EmptyPor ");
      break;
    default:
      break;
    }
  }

  fflush(stdout);
  fflush(aggfile);

  aggsize = ixmax - ixmin + 1;

  printf("aggsize is %d \n", aggsize);

  /* Increase distance from aggregate in increments of one */

  for (idist = 1; idist <= (Xsyssize - aggsize) / 2; idist++) {

    /* Pixel left of aggregate surface */
    ixlo = ((Xsyssize - aggsize + 2) / 2) - idist;

    /* Pixel right of aggregate surface */
    ixhi = ((Xsyssize + aggsize) / 2) + idist;

    /* Initialize phase counts for this distance */
    for (icnt = 0; icnt < NPHASES; icnt++) {
      phase[icnt] = 0;
    }

    ptot = 0;

    /***
     *	Check all pixels which are this distance
     *	from aggregate surface
     ***/

    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 0; iz < Zsyssize; iz++) {
        phid = mic[ixlo][iy][iz];
        ptot++;
        phase[phid]++;
        phid = mic[ixhi][iy][iz];
        ptot++;
        phase[phid]++;
      }
    }

    /* Output results for this distance from surface */

    fprintf(aggfile, "%d ", idist);
    for (i = 0; i < NPHASES; i++) {
      if (i <= NSPHASES && i != INERTAGG) {
        fprintf(aggfile, "%d ", phase[i]);
      } else if (i == EMPTYP) {
        fprintf(aggfile, "%d\n", phase[i]);
      }
    }
  }

  fclose(aggfile);
  free_sibox(mic, Xsyssize, Ysyssize);

  return (0);
}
