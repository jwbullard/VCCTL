/*****************************************************
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
 * Programmer:	Jeffrey W Bullard
 *              Zachry Department of Civil and Environmental Engineering
 *              Department of Materials Science and Engineering
 *              Texas A&M University
 *              100 Spence Street, 3136 TAMU
 *              College Station, Texas  77843
 *				E-mail: jwbullard@tamu.edu
 *
 *******************************************************/
#include "include/vcctl.h"
#include <locale.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

/***
 *	Global variables
 ***/
float Version;

#include "include/properties.h"

int main(int argc, char *argv[]) {
  int ***mic;
  int flag;
  int valin, ovalin, ix, iy, iz, ix1, iy1, iz1, k, kk, syssize, totalsysvoxels;
  int xsyssize, ysyssize, zsyssize, totalsolidvoxels, totalporevoxels;
  int volcount[NPHASES], surfcount[NPHASES];
  float volume[NPHASES], totalsolidvolume, totalporevolume, totalvolume;
  float surface[NPHASES], totalsurfacearea;
  float mass[NPHASES], totalmass, totalsolidmass, totalporemass;
  float facearea, voxelvolume, voxelvolumeInCm3;
  float frac;

  /* Resolution in units of micrometers */
  float res, resInCm;
  char filen[MAXSTRING], fileout[MAXSTRING], buff[MAXSTRING];
  char phasename[MAXSTRING], instring[MAXSTRING];
  char *locale;
  wchar_t mu = 0x03BC;
  wchar_t sup1 = 0x00B9;
  wchar_t sup2 = 0x00B2;
  wchar_t sup3 = 0x00B3;
  wchar_t supminus = 0x207B;
  wchar_t multsym = 0x00D7;
  FILE *infile, *statfile;

  /* Set up locale for printing unicode when necessary */
  locale = setlocale(LC_ALL, "");

  /* Initialize local arrays */

  totalsurfacearea = totalvolume = totalmass = 0.0;
  totalsolidvolume = totalporevolume = totalsolidmass = totalporemass = 0.0;
  totalsolidvoxels = totalporevoxels = 0;
  for (k = 0; k < NPHASES; k++) {
    volume[k] = surface[k] = mass[k] = 0.0;
    volcount[k] = surfcount[k] = 0;
  }

  /***
   *	Assign physical and chemical properties of
   *	phases.  Function comes from properties.c
   ***/

  assign_properties();

  /* Check for command line arguments */
  if (argc != 3) {
    printf("Usage: %s <input_file> <output_file>\n", argv[0]);
    printf("Enter name of microstructure file to open \n");
    read_string(filen, sizeof(filen));
    printf("%s \n", filen);
    printf("Enter name of file to write statistics to \n");
    read_string(fileout, sizeof(fileout));
    printf("%s \n", fileout);
  } else {
    /* Use command line arguments */
    strcpy(filen, argv[1]);
    strcpy(fileout, argv[2]);
    printf("Input file: %s \n", filen);
    printf("Output file: %s \n", fileout);
  }

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
    facearea = res * res; /* in um2 */
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

  totalsysvoxels = xsyssize * ysyssize * zsyssize;
  resInCm = res * 1.0e-4;
  voxelvolume = res * res * res; /* in um3 */
  voxelvolumeInCm3 = resInCm * resInCm * resInCm;

  /***
   *	Dynamically allocate the memory for mic array
   ***/

  mic = ibox(xsyssize, ysyssize, zsyssize);

  /* Read in image and accumulate volume totals */

  /**
   * 2025 August 05
   * The new convention is to read and write image data using
   * C-order (z varies fastest, then y, and then x)
   **/

  for (ix = 0; ix < xsyssize; ix++) {
    for (iy = 0; iy < ysyssize; iy++) {
      for (iz = 0; iz < zsyssize; iz++) {

        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valin = convert_id(ovalin, Version);
        mic[ix][iy][iz] = valin;

        if (valin < NSPHASES) {

          volcount[valin]++;

          /***
           *	orthorhombic C3A counts as C3A, too, for
           *	clinker purposes
           ***/

          mass[valin] += ((float)Specgrav[valin]);
          if (valin == OC3A) {
            volcount[C3A]++;
            mass[C3A] += ((float)Specgrav[valin]);
          }

          if (valin != POROSITY && valin != DRIEDP && valin != EMPTYDP &&
              valin != EMPTYP) {

            totalsolidvoxels++;

            /** totalmass has units of voxel * (g per cm3) **/
            /** This is the same as g /(cm3 per voxel) **/
            /** It is the total solid mass **/
            totalsolidmass += ((float)(Specgrav[valin]));
          } else {
            totalporevoxels++;
            totalporemass += ((float)Specgrav[valin]);
          }

          /***
           *	Specific gravities are declared
           *	and defined in properties.c
           ***/

        } else {

          /***
           *	Anything not recognized is
           *	generates an error
           ***/

          printf("\n\nERROR: Urecognized phase id (%d)\n\n", valin);
          exit(1);
        }
      }
    }
  }

  fclose(infile);

  ix1 = iy1 = iz1 = 0;
  for (ix = 0; ix < xsyssize; ix++) {
    for (iy = 0; iy < ysyssize; iy++) {
      for (iz = 0; iz < zsyssize; iz++) {

        if ((mic[ix][iy][iz] != POROSITY) && (mic[ix][iy][iz] <= NSPHASES)) {

          valin = mic[ix][iy][iz];

          /* Check six neighboring pixels for porosity */

          for (k = 1; k <= 6; k++) {

            /* Each face bordering porosity adds one to surfcount */
            /* So a single voxel could have a surfcount up to six */
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

              surfcount[valin]++;
            }
          }
        }
      }
    }
  }

  /**
   * Now generate statistics
   **/

  totalvolume = (float)(totalsysvoxels)*voxelvolume;

  for (k = 0; k < NPHASES; k++) {
    volume[k] = ((float)(volcount[k])) * voxelvolume;
    mass[k] *= (voxelvolumeInCm3);
    if (k != POROSITY && k != DRIEDP && k != EMPTYDP && k != EMPTYP) {
      totalsolidvolume += volume[k];
      surface[k] = ((float)(surfcount[k])) * facearea;
      totalsurfacearea += surface[k];
      totalsolidmass += mass[k];
    } else {
      totalporevolume += volume[k];
      totalporemass += mass[k];
    }
  }

  k = POROSITY;

  fprintf(statfile, "MICROSTRUCTURE VOLUME & SURFACE AREA ANALYSIS\n");
  fprintf(statfile, "==============================");
  fprintf(statfile, "==============================\n\n");
  fwprintf(statfile, L"Total Volume: %.2f %lcm%lc (%d voxels)\n", totalvolume,
           mu, sup3, totalsysvoxels);
  fwprintf(statfile, L"Total Solid Volume: %.2f %lcm%lc (%d voxels)\n",
           totalsolidvolume, mu, sup3);
  fwprintf(statfile, L"Total Surface Area: %.2f %lcm%lc\n", totalsurfacearea,
           mu, sup2);
  fwprintf(statfile, L"Total Pore Volume: %.2f %lcm%lc\n", totalporevolume, mu,
           sup3);
  fprintf(statfile, "Pore Volume Fraction: %.5f\n",
          (totalporevolume / totalvolume));
  fwprintf(statfile, L"Voxel Size: %.3f %lc %.3f %lc %.3f %lcm%lc\n\n", res,
           multsym, res, multsym, res, mu, sup3);
  fprintf(statfile, "PHASE BREAKDOWN:\n");
  fprintf(statfile, "----------------------------------------");

  for (k = 0; k < NSPHASES; ++k) {
    if (volume[k] > 1.0e-9) {
      id2phasename(k, phasename);
      fprintf(statfile, "\n\n%s (Phase %2d):", phasename, k);
      fwprintf(statfile, L"\n Volume: %.2g %lcm%lc", volume[k], mu, sup3);
      if (k != 0) {
        fwprintf(statfile, L"\n Surface Area: %.2g %lcm%lc", surface[k], mu,
                 sup2);
        fwprintf(statfile, L"\n Specific Surface Area: %.2g %lcm%lc%lc",
                 (surface[k] / volume[k]), mu, supminus, sup1);
      }
      fprintf(statfile, "\n Voxel Count: %d", volcount[k]);
      frac = volume[k] / totalvolume;
      fprintf(statfile, "\n Volume Fraction: %.4f", frac);
      fprintf(statfile, "\n Volume Percentage: %.2f %%", (100.0 * frac));
    }
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
