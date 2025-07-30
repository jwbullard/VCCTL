/******************************************************
 *
 * Program stat3d.c
 *
 * Reads in a 3-D image and outputs
 *
 * 	(1) phase volumes
 * 	(2) volume fractions
 * 	(3) pore-exposed surface area fractions
 * 	(4) mass fractions
 *
 *	Only processes the phase values 0-10, 24 and 25
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
#include <string.h>

/***
 *	Global variables
 ***/
float Version;

#include "include/properties.h"

int main(void) {
  int ***mic;
  int phaselist[NPHASES], flag;
  int valin, ovalin, ix, iy, iz, ix1, iy1, iz1, k, kk, syssize;
  int xsyssize, ysyssize, zsyssize;
  int voltot, surftot, totalvol;
  int volume[NPHASES], surface[NPHASES], surfpix[NPHASES];
  double mass[NPHASES], totmass, totalmass;
  float res;
  char filen[MAXSTRING], fileout[MAXSTRING], buff[MAXSTRING];
  char phasename[MAXSTRING], instring[MAXSTRING];
  FILE *infile, *statfile;

  /* Initialize local arrays */

  for (ix = 0; ix < NPHASES; ix++) {
    phaselist[ix] = 0;
    volume[ix] = surface[ix] = surfpix[ix] = 0;
    mass[ix] = 0.0;
  }

  /***
   *	Assign physical and chemical properties of
   *	phases.  Function comes from properties.c
   ***/

  assign_properties();

  printf("Enter name of file to open \n");
  read_string(filen, sizeof(filen));
  printf("%s \n", filen);
  printf("Enter name of file to write statistics to \n");
  read_string(fileout, sizeof(fileout));
  printf("%s \n", fileout);

  for (ix = 0; ix < NPHASES; ix++) {
    volume[ix] = surface[ix] = 0;
    mass[ix] = 0.0;
    phaselist[ix] = -1;
  }

  /***
   *	Specify the phases about which to print
   *	statistics, other than porosity and clinker
   ***/

  phaselist[1] = C3S;
  phaselist[2] = C2S;
  phaselist[3] = C3A;
  phaselist[4] = C4AF;
  phaselist[5] = K2SO4;
  phaselist[6] = NA2SO4;
  phaselist[7] = GYPSUM;
  phaselist[8] = HEMIHYD;
  phaselist[9] = ANHYDRITE;
  phaselist[10] = OC3A;
  phaselist[11] = SFUME;
  phaselist[12] = INERT;
  phaselist[13] = SLAG;
  phaselist[14] = ASG;
  phaselist[15] = CAS2;
  phaselist[16] = AMSIL;
  phaselist[17] = CH;
  phaselist[18] = CSH;
  phaselist[19] = C3AH6;
  phaselist[20] = ETTR;
  phaselist[21] = ETTRC4AF;
  phaselist[22] = AFM;
  phaselist[23] = FH3;
  phaselist[24] = POZZCSH;
  phaselist[25] = SLAGCSH;
  phaselist[26] = CACL2;
  phaselist[27] = FRIEDEL;
  phaselist[28] = STRAT;
  phaselist[29] = GYPSUMS;
  phaselist[30] = CACO3;
  phaselist[31] = FREELIME;
  phaselist[32] = AFMC;
  phaselist[33] = INERTAGG;
  phaselist[34] = ABSGYP;
  phaselist[35] = FLYASH;
  phaselist[36] = FAC3A;
  phaselist[37] = EMPTYP;

  /***
   *	Open input and output files.  Output file
   *	will be ultimately read by statcalc for
   *	displaying in web page format
   ***/

  infile = fopen(filen, "r");
  statfile = fopen(fileout, "w");

  /***
   *	Determine whether software version, system
   *	size and resolution are specified in the image file
   ***/

  fscanf(infile, "%s", buff);
  if (!strcmp(buff, VERSIONSTRING)) {
    fscanf(infile, "%s", instring);
    Version = atof(instring);
    fscanf(infile, "%s", buff); /* Desc. of system size */
    if (!strcmp(buff, XSIZESTRING)) {
      fscanf(infile, "%s", instring);
      xsyssize = atoi(instring);
      fscanf(infile, "%s", buff);
      fscanf(infile, "%s", instring);
      ysyssize = atoi(instring);
      fscanf(infile, "%s", buff);
      fscanf(infile, "%s", instring);
      zsyssize = atoi(instring);
    } else {
      fscanf(infile, "%s", instring);
      syssize = atoi(instring);
      xsyssize = syssize;
      ysyssize = syssize;
      zsyssize = syssize;
    }
    fscanf(infile, "%s", buff); /* Desc. of resolution */
    fscanf(infile, "%s", instring);
    res = atof(instring);
  } else {

    /***
     *	This image file was generated prior to
     *	Version 3.0.  Allow backward compatibility
     *	by defaulting system size to 100 and
     *	system resolution to 1.0
     ***/

    Version = 2.0;
    syssize = DEFAULTSYSTEMSIZE;
    xsyssize = syssize;
    ysyssize = syssize;
    zsyssize = syssize;
    res = DEFAULTRESOLUTION;
    rewind(infile);
  }

  /***
   *	Dynamically allocate the memory for mic array
   ***/

  mic = ibox(xsyssize, ysyssize, zsyssize);

  /* Read in image and accumulate volume totals */

  totalmass = 0.0;
  totalvol = 0;
  for (iz = 0; iz < zsyssize; iz++) {
    for (iy = 0; iy < ysyssize; iy++) {
      for (ix = 0; ix < xsyssize; ix++) {

        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valin = convert_id(ovalin, Version);
        mic[ix][iy][iz] = valin;

        if (valin < NPHASES) {

          volume[valin]++;

          /***
           *	orthorhombic C3A counts as C3A, too, for
           *	clinker purposes
           ***/

          if (valin == OC3A)
            volume[C3A]++;

          if (valin != POROSITY && valin != DRIEDP && valin != EMPTYDP &&
              valin != EMPTYP) {

            totalvol++;
            totalmass += ((double)(Specgrav[valin]));
          }

          /***
           *	Specific gravities are declared
           *	and defined in properties.c
           ***/

          mass[valin] += ((double)Specgrav[valin]);
          if (valin == OC3A)
            mass[C3A] += ((double)Specgrav[valin]);

        } else {

          /***
           *	Anything not recognized is
           *	assumed to be water-filled
           *	porosity
           ***/

          volume[POROSITY]++;
        }
      }
    }
  }

  fclose(infile);

  ix1 = iy1 = iz1 = 0;
  for (iz = 0; iz < zsyssize; iz++) {
    for (iy = 0; iy < ysyssize; iy++) {
      for (ix = 0; ix < xsyssize; ix++) {

        flag = 0;

        if ((mic[ix][iy][iz] != POROSITY) && (mic[ix][iy][iz] <= NSPHASES)) {

          valin = mic[ix][iy][iz];

          /* Check six neighboring pixels for porosity */

          for (k = 1; k <= 6 && !flag; k++) {

            switch (k) {
            case 1:
              ix1 = ix - 1;
              if (ix1 < 0)
                ix1 += xsyssize;
              iy1 = iy;
              iz1 = iz;
              break;
            case 2:
              ix1 = ix + 1;
              if (ix1 >= xsyssize)
                ix1 -= xsyssize;
              iy1 = iy;
              iz1 = iz;
              break;
            case 3:
              iy1 = iy - 1;
              if (iy1 < 0)
                iy1 += ysyssize;
              ix1 = ix;
              iz1 = iz;
              break;
            case 4:
              iy1 = iy + 1;
              if (iy1 >= ysyssize)
                iy1 -= ysyssize;
              ix1 = ix;
              iz1 = iz;
              break;
            case 5:
              iz1 = iz - 1;
              if (iz1 < 0)
                iz1 += zsyssize;
              iy1 = iy;
              ix1 = ix;
              break;
            case 6:
              iz1 = iz + 1;
              if (iz1 >= zsyssize)
                iz1 -= zsyssize;
              iy1 = iy;
              ix1 = ix;
              break;
            default:
              break;
            }

            if ((mic[ix1][iy1][iz1] == POROSITY) ||
                (mic[ix1][iy1][iz1] > NSPHASES)) {

              surface[valin]++;
              flag = 1;
            }
          }
        }
        if (flag)
          surfpix[valin]++;
      }
    }
  }

  /***
   *	Only include clinker phases in surface
   *	area fraction calculation
   ***/

  printf("Phase\tVol.Pix\tSurf.Pix\tVol.frac\tSurf.frac\tMass.frac\n");
  fprintf(statfile,
          "Phase\tVol.Pix\tSurf.Pix\tVol.frac\tSurf.frac\tMass.frac\n");

  surftot = surface[C3S] + surface[C2S];
  surftot += surface[C3A] + surface[C4AF];
  surftot += surface[K2SO4] + surface[NA2SO4];

  voltot = volume[C3S] + volume[C2S];
  voltot += volume[C3A] + volume[C4AF];
  voltot += volume[K2SO4] + volume[NA2SO4];

  totmass = mass[C3S] + mass[C2S];
  totmass += mass[C3A] + mass[C4AF];
  totmass += mass[K2SO4] + mass[NA2SO4];

  k = POROSITY;

  id2phasename(k, phasename);
  printf("%s\t%8d", phasename, volume[POROSITY]);
  printf("\t%8d      \n", surface[POROSITY]);
  fprintf(statfile, "%s\t%8d", phasename, volume[POROSITY]);
  fprintf(statfile, "\t%8d      \n", surface[POROSITY]);

  /***
   *	Print extra information about clinker phases
   ***/

  for (k = C3S; k <= NA2SO4; k++) {
    id2phasename(k, phasename);
    printf("%s\t%8d\t%8d", phasename, volume[k], surface[k]);
    printf("\t%.5f", (double)volume[k] / (double)voltot);
    printf("\t%.5f", (double)surface[k] / (double)surftot);
    printf("\t%.5f\n", (double)mass[k] / (double)totmass);
    fprintf(statfile, "%s\t%8d\t%8d", phasename, volume[k], surface[k]);
    fprintf(statfile, "\t%.5f", (double)volume[k] / (double)voltot);
    fprintf(statfile, "\t%.5f", (double)surface[k] / (double)surftot);
    fprintf(statfile, "\t%.5f\n", (double)mass[k] / (double)totmass);
  }

  printf("TOTAL\t%8d\t%8d\n\n", voltot, surftot);
  fprintf(statfile, "TOTAL\t%8d\t%8d", voltot, surftot);
  fprintf(statfile, "\t%.5f", (double)voltot / (double)totalvol);
  fprintf(statfile, "\t\t%.5f\n\n", (double)totmass / (double)totalmass);

  /***
   *	Now print generic information on volume
   *	count and surface count for all other
   *	phases specified in phaselist
   ***/

  for (k = 1; phaselist[k] >= 0; k++) {
    kk = phaselist[k];
    id2phasename(kk, phasename);
    printf("\n%s\t%8d\t%8d", phasename, volume[kk], surface[kk]);
    printf("\t%.5f", (double)volume[kk] / (double)totalvol);
    printf("\t%.5f\n", (double)mass[kk] / (double)totalmass);
    fprintf(statfile, "\n%s\t%8d\t%8d", phasename, volume[kk], surface[kk]);
    fprintf(statfile, "\t%.5f", (double)volume[kk] / (double)totalvol);
    fprintf(statfile, "\t%.5f\n", (double)mass[kk] / (double)totalmass);
  }

  fclose(statfile);

  /***
   *	Free the allocated memory
   ***/

  free_ibox(mic, xsyssize, ysyssize);

  /***
   *	Update the key file now that calculation is finished
   ***/

  return (0);
}
