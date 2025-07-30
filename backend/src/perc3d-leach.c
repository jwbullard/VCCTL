/*****************************************************
 *
 * Program perc3d-leach.c to test connectivity of the
 * combination of phases POROSITY and EMPTYP
 * in a 3D microstructure
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

#define TOTCSH OFFSET
#define TOTGYP OFFSET + 1

#define MEMERR -1

/* label for a burnt pixel */
#define BURNT 70

/* default size of matrices for holding burning locations */
#define SIZE2D 49000

/* functions defining coordinates for burning in any of three directions */
#define cx(x, y, z, a, b, c) (1 - b - c) * x + (1 - a - c) * y + (1 - a - b) * z
#define cy(x, y, z, a, b, c) (1 - a - b) * x + (1 - b - c) * y + (1 - a - c) * z
#define cz(x, y, z, a, b, c) (1 - a - c) * x + (1 - a - b) * y + (1 - b - c) * z

/***
 *	Global variables
 ***/
short int ***Mic;
int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
float Res = DEFAULTRESOLUTION;

/* VCCTL software version used to create input file */
float Version;

int Npores = 0, Ntot = 0, Nperc = 0, Nburnt = 0;
float Tot_porosity;

int burn3d(int npix, int d1, int d2, int d3);
int main(void) {
  register int ix, iy, iz;
  int valin, ovalin, garb;
  float x_frac_connected, y_frac_connected, z_frac_connected,
      ave_frac_connected;
  char filein[MAXSTRING], fileout[MAXSTRING], micfilename[MAXSTRING];
  FILE *infile, *outfile, *micfile;

  printf("\nEnter name of file with image list: ");
  read_string(filein, sizeof(filein));
  printf("\n%s", filein);
  fflush(stdout);

  infile = filehandler("perc3d-leach", filein, "READ");
  if (!infile) {
    exit(1);
  }

  printf("\nEnter name of file to store percolation results: ");
  read_string(fileout, sizeof(fileout));
  printf("\n%s", fileout);
  fflush(stdout);

  outfile = filehandler("perc3d-leach", fileout, "WRITE");
  if (!outfile) {
    exit(1);
  }

  do {

    fscanf(infile, "%s", micfilename);
    micfile = filehandler("perc3d-leach", micfilename, "READ");
    if (!micfile) {
      fclose(infile);
      exit(1);
    }
    printf("\nOpened microstructure file %s... ", micfilename);
    fflush(stdout);

    if (read_imgheader(micfile, &Version, &Xsyssize, &Ysyssize, &Zsyssize,
                       &Res)) {
      fclose(micfile);
      bailout("perc3d-leach", "Error reading image header");
      exit(1);
    }

    /***
     *	Allocate memory for Mic array
     ***/

    Mic = sibox(Xsyssize, Ysyssize, Zsyssize);
    if (!Mic) {
      fclose(infile);
      fclose(micfile);
      bailout("perc3d-leach", "Could not allocate memory for Mic array");
      exit(1);
    }

    Npores = 0;
    for (iz = 0; iz < Zsyssize; iz++) {
      for (iy = 0; iy < Ysyssize; iy++) {
        for (ix = 0; ix < Xsyssize; ix++) {
          fscanf(micfile, "%d", &ovalin);
          valin = convert_id(ovalin, Version);
          Mic[ix][iy][iz] = valin;
          if (valin == POROSITY || valin == EMPTYP)
            Npores++;
        }
      }
    }

    fclose(micfile);

    Tot_porosity = ((float)(Npores)) /
                   ((float)(Xsyssize) * (float)(Ysyssize) * (float)(Zsyssize));
    printf("total porosity = %f\n", Tot_porosity);

    garb = burn3d(EMPTYP, 1, 0, 0);
    if (garb == MEMERR) {
      bailout("perc3d-leach",
              "Could not allocate memory in burn3d function (x)");
      exit(1);
    }
    x_frac_connected = (float)(garb) / (float)(Npores);
    printf("Fraction connected in x direction = %f\n", x_frac_connected);

    garb = burn3d(EMPTYP, 0, 1, 0);
    if (garb == MEMERR) {
      bailout("perc3d-leach",
              "Could not allocate memory in burn3d function (y)");
      exit(1);
    }
    y_frac_connected = (float)(garb) / (float)(Npores);
    printf("Fraction connected in y direction = %f\n", y_frac_connected);

    garb = burn3d(EMPTYP, 0, 0, 1);
    if (garb == MEMERR) {
      bailout("perc3d-leach",
              "Could not allocate memory in burn3d function (z)");
      exit(1);
    }
    z_frac_connected = (float)(garb) / (float)(Npores);
    printf("Fraction connected in z direction = %f\n", z_frac_connected);

    ave_frac_connected =
        (x_frac_connected + y_frac_connected + z_frac_connected) / 3.0;
    fprintf(outfile, "%f %f\n", Tot_porosity, ave_frac_connected);

    free_sibox(Mic, Xsyssize, Ysyssize);

  } while (!feof(infile));

  fclose(outfile);

  return (0);
}

/***
 *	burn3d
 *
 * 	Assess the connectivity (percolation) of a single phase
 *
 * 	Two matrices are used:  one to store the recently burnt
 * 	locations, and one to store the newly-found burnt locations
 *
 * 	Arguments:	int npix: ID of phase to burn
 * 				int d1: x-direction flag
 * 				int d2: y-direction flag
 * 				int d3: z-direction flag
 *
 * 	Returns:	number of pixels in connected pathway
 * 				MEMERR if a memory error is encountered
 *
 *	Calls:		No other routines
 *	Called by:	disrealnew
 ***/

int burn3d(int npix, int d1, int d2, int d3) {
  register int i, j, k, j1, k1;
  int inew, x1, y1, z1, igood, jnew, icur, bflag;
  int *nmatx, *nmaty, *nmatz, *nnewx, *nnewy, *nnewz;
  int mult1, mult2, npix1, npix2, npix3;
  int xl, xh, px, py, pz, qx, qy, qz, xcn, ycn, zcn;
  int ntop, nthrough, ncur, nnew, nphc;

  npix1 = npix;
  npix2 = npix;
  npix3 = npix;
  if (npix == ETTR) {
    npix1 = ETTRC4AF;
  }
  if (npix == EMPTYP) {
    npix1 = POROSITY;
  }
  if (npix == TOTCSH) {
    npix2 = SLAGCSH;
    npix1 = POZZCSH;
    npix = CSH;
  }
  if (npix == TOTGYP) {
    npix3 = GYPSUMS;
    npix2 = ANHYDRITE;
    npix1 = HEMIHYD;
    npix = GYPSUM;
  }
  if (npix == C3A) {
    npix1 = OC3A;
    npix = C3A;
  }

  nmatx = nmaty = nmatz = NULL;
  nnewx = nnewy = nnewz = NULL;
  mult1 = mult2 = 1;

  nmatx = (int *)calloc(SIZE2D, sizeof(int));
  nmaty = (int *)calloc(SIZE2D, sizeof(int));
  nmatz = (int *)calloc(SIZE2D, sizeof(int));
  nnewx = (int *)calloc(SIZE2D, sizeof(int));
  nnewy = (int *)calloc(SIZE2D, sizeof(int));
  nnewz = (int *)calloc(SIZE2D, sizeof(int));

  if (!nmatx) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for nmatx.");
    printf("\n\tExiting now.");
    return (MEMERR);
  }
  if (!nmaty) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for nmaty.");
    printf("\n\tExiting now.");
    free(nmatx);
    return (MEMERR);
  }
  if (!nmatz) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for nmatz.");
    printf("\n\tExiting now.");
    free(nmatx);
    free(nmaty);
    return (MEMERR);
  }
  if (!nnewx) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for nnewx.");
    printf("\n\tExiting now.");
    free(nmatx);
    free(nmaty);
    free(nmatz);
    return (MEMERR);
  }
  if (!nnewy) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for nnewy.");
    printf("\n\tExiting now.");
    free(nmatx);
    free(nmaty);
    free(nmatz);
    free(nnewx);
    return (MEMERR);
  }
  if (!nnewz) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for newz.");
    printf("\n\tExiting now.");
    free(nmatx);
    free(nmaty);
    free(nmatz);
    free(nnewx);
    free(nnewy);
    return (MEMERR);
  }

  /***
   *	Counters for number of pixels of phase accessible
   *	from surface #1 and number which are part of a
   *	percolated pathway to surface #2
   ***/

  ntop = bflag = nthrough = nphc = 0;
  printf("\nIn burn3d. Beginning.");
  fflush(stdout);

  /***
   *	Percolation is assessed from top to bottom only
   *	and burning algorithm is periodic in other two
   *	directions.
   *
   *	Use of directional flags allow transformation of
   *	coordinates to burn in direction of choosing
   *	(x, y, or z)
   ***/

  i = 0; /* Starting from the bottom x face */

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {

      igood = ncur = Ntot = 0;

      /* Transform coordinates */

      px = cx(i, j, k, d1, d2, d3);
      py = cy(i, j, k, d1, d2, d3);
      pz = cz(i, j, k, d1, d2, d3);

      if (Mic[px][py][pz] == npix || Mic[px][py][pz] == npix1 ||
          Mic[px][py][pz] == npix2 || Mic[px][py][pz] == npix3) {

        /* Start a burn front */

        Mic[px][py][pz] = BURNT;
        Ntot++;
        ncur++;

        /***
         *	Burn front is stored in matrices nmat*
         *	and nnew*
         ***/

        if (ncur >= (mult1 * SIZE2D)) {

          /***
           *	Must allocate more memory
           ***/

          mult1++;
          nmatx = (int *)realloc((int *)nmatx, (mult1 * SIZE2D));
          nmaty = (int *)realloc((int *)nmaty, (mult1 * SIZE2D));
          nmatz = (int *)realloc((int *)nmatz, (mult1 * SIZE2D));

          if (!nmatx) {
            printf("\nERROR in burn3d:");
            printf("\n\tCould not reallocate space for nmatx.");
            printf("\n\tExiting now.");
            free(nmaty);
            free(nmatz);
            free(nnewx);
            free(nnewy);
            free(nnewz);
            return (MEMERR);
          }
          if (!nmaty) {
            printf("\nERROR in burn3d:");
            printf("\n\tCould not reallocate space for nmaty.");
            printf("\n\tExiting now.");
            free(nmatx);
            free(nmatz);
            free(nnewx);
            free(nnewy);
            free(nnewz);
            return (MEMERR);
          }
          if (!nmatz) {
            printf("\nERROR in burn3d:");
            printf("\n\tCould not reallocate space for nmatz.");
            printf("\n\tExiting now.");
            free(nmatx);
            free(nmaty);
            free(nnewx);
            free(nnewy);
            free(nnewz);
            return (MEMERR);
          }
        }

        nmatx[ncur] = i;
        nmaty[ncur] = j;
        nmatz[ncur] = k;

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
              if (jnew == 1)
                x1--;
              if (jnew == 2)
                x1++;
              if (jnew == 3)
                y1--;
              if (jnew == 4)
                y1++;
              if (jnew == 5)
                z1--;
              if (jnew == 6)
                z1++;

              /* Periodic in y and z directions */

              y1 += checkbc(y1, Ysyssize);
              z1 += checkbc(z1, Zsyssize);

              /***
               *	Nonperiodic in x so be sure to remain
               *	in the 3-D box
               ***/

              if ((x1 >= 0) && (x1 < Xsyssize)) {

                /* Transform coordinates */

                px = cx(x1, y1, z1, d1, d2, d3);
                py = cy(x1, y1, z1, d1, d2, d3);
                pz = cz(x1, y1, z1, d1, d2, d3);

                if (Mic[px][py][pz] == npix || Mic[px][py][pz] == npix1 ||
                    Mic[px][py][pz] == npix2) {

                  Ntot++;
                  Mic[px][py][pz] = BURNT;
                  nnew++;

                  if (nnew >= (mult2 * SIZE2D)) {

                    /***
                     *	Must allocate more memory
                     ***/

                    mult2++;
                    nnewx = (int *)realloc((int *)nnewx, (mult2 * SIZE2D));
                    nnewy = (int *)realloc((int *)nnewy, (mult2 * SIZE2D));
                    nnewz = (int *)realloc((int *)nnewz, (mult2 * SIZE2D));

                    if (!nnewx) {
                      printf("\nERROR in burn3d:");
                      printf("\n\tCould not reallocate space for nnewx.");
                      printf("\n\tExiting now.");
                      free(nmaty);
                      free(nmatz);
                      free(nmatx);
                      free(nnewy);
                      free(nnewz);
                      return (MEMERR);
                    }
                    if (!nnewy) {
                      printf("\nERROR in burn3d:");
                      printf("\n\tCould not reallocate space for nnewy.");
                      printf("\n\tExiting now.");
                      free(nmatx);
                      free(nmatz);
                      free(nnewx);
                      free(nmaty);
                      free(nnewz);
                      return (MEMERR);
                    }
                    if (!nnewz) {
                      printf("\nERROR in burn3d:");
                      printf("\n\tCould not reallocate space for nnewz.");
                      printf("\n\tExiting now.");
                      free(nmatx);
                      free(nmaty);
                      free(nnewx);
                      free(nnewy);
                      free(nmatz);
                      return (MEMERR);
                    }
                  }

                  nnewx[nnew] = x1;
                  nnewy[nnew] = y1;
                  nnewz[nnew] = z1;
                }
              }
            } /* End of loop over nearest neighbors */
          }   /* End of loop over current burn front */

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

        /* Run out of fuel.  Burning is over */

        ntop += Ntot;
        xl = 0;
        xh = Xsyssize - 1;

        /***
         *	See if current path extends through
         *	the microstructure
         ***/

        for (j1 = 0; j1 < Ysyssize; j1++) {
          for (k1 = 0; k1 < Zsyssize; k1++) {

            px = cx(xl, j1, k1, d1, d2, d3);
            py = cy(xl, j1, k1, d1, d2, d3);
            pz = cz(xl, j1, k1, d1, d2, d3);
            qx = cx(xh, j1, k1, d1, d2, d3);
            qy = cy(xh, j1, k1, d1, d2, d3);
            qz = cz(xh, j1, k1, d1, d2, d3);

            if ((Mic[px][py][pz] == BURNT) && (Mic[qx][qy][qz] == BURNT)) {

              igood = 2;
            }

            if (Mic[px][py][pz] == BURNT) {
              Mic[px][py][pz]++;
            }

            if (Mic[qx][qy][qz] == BURNT) {
              Mic[qx][qy][qz]++;
            }
          }
        }

        if (igood == 2)
          nthrough += Ntot;
      }
    }
  }

  /***
   *	Finished sampling all pixels of type npix along
   *	the bottom x face
   *
   *	Return the burnt sites to their original
   *	phase values
   ***/

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {

        if (Mic[i][j][k] >= BURNT) {

          nphc++;
          Mic[i][j][k] = npix;

        } else if ((Mic[i][j][k] == npix) || (Mic[i][j][k] == npix1) ||
                   (Mic[i][j][k] == npix2)) {
          nphc++;
        }
      }
    }
  }

  /*
  printf("Phase ID = %d \n",npix);
  printf("Number accessible from first surface = %d \n",ntop);
  printf("Number contained in through pathways= %d \n",nthrough);
  fflush(stdout);
  */

  Ntot = nphc;
  Nperc = nthrough;
  Nburnt = ntop;

  free(nmatx);
  free(nmaty);
  free(nmatz);
  free(nnewx);
  free(nnewy);
  free(nnewz);

  return (nthrough);
}
