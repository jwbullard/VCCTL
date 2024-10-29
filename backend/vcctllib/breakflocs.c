/******************************************************
 * breakflocs is a VCCTL function for eliminating contacts
 * between anhydrous particles in contact
 *******************************************************/

/***
 *	breakflocs
 *
 *	Routine to eliminate particle-particle contacts if
 *	the particles are both anhydrous cement phases
 *
 *	Arguments:	Particle file pointer (pfile)
 *				Array of pix values (p)
 *				Array of particle ids (part)
 *				System size (ssize)
 *				VCCTL Version number (version)
 *				Resolution of microstructure (resol)
 *
 *	Returns:	Status flag (0 if okay, nonzero otherwise)
 *
 *	Calls:		checkbc
 *	Called by:	cpelas.c program
 ***/
#include "../include/vcctl.h"
#include <stdio.h>

int breakflocs(FILE *pfile, short int *p, short int *part, short int *in,
               short int *jn, short int *kn, int xsize, int ysize, int zsize,
               float version, float resol) {
  int status = 0;
  int nxy, i, j, k, ijk, n, inval, oinval, nsw, done;
  int i1, j1, k1, ipp, px, py, pz;
  int m, m1, m2, mm, npartmin, npartmax, taggednpartmax;
  float pres, pver;
  float tiny = 1.0e-4;
  char buff[MAXSTRING];

  /***
   *	Set up neighbor table for 3 x 3 x 3 box of neighbor pixels
   ***/

  in[0] = 0;
  in[1] = 1;
  in[2] = 1;
  in[3] = 1;
  in[4] = 0;
  in[5] = (-1);
  in[6] = (-1);
  in[7] = (-1);

  jn[0] = 1;
  jn[1] = 1;
  jn[2] = 0;
  jn[3] = (-1);
  jn[4] = (-1);
  jn[5] = (-1);
  jn[6] = 0;
  jn[7] = 1;

  for (n = 0; n < 8; n++) {
    kn[n] = 0;
    kn[n + 8] = (-1);
    kn[n + 16] = 1;
    in[n + 8] = in[n];
    in[n + 16] = in[n];
    jn[n + 8] = jn[n];
    jn[n + 16] = jn[n];
  }
  in[24] = 0;
  in[25] = 0;
  in[26] = 0;
  jn[24] = 0;
  jn[25] = 0;
  jn[26] = 0;
  kn[24] = (-1);
  kn[25] = 1;
  kn[26] = 0;

  printf("\nNeighbor table in breakflocs:\n");
  for (n = 0; n < 27; n++) {
    printf("\t%d\t%d\t%d\n", in[n], jn[n], kn[n]);
  }
  fflush(stdout);
  nxy = xsize * ysize;
  npartmin = xsize * ysize * zsize;
  npartmax = taggednpartmax = 0;

  if (read_imgheader(pfile, &pver, &px, &py, &pz, &pres)) {
    printf("\nTrouble reading header of pfile. Exiting ...\n");
    fflush(stdout);
    fclose(pfile);
  }

  printf("\n\tImage Version = %f ; Pimage Version = %f", version, pver);
  printf("\n\tImage Xsize = %d ; Pimage Xsize = %d", xsize, px);
  printf("\n\tImage Ysize = %d ; Pimage Ysize = %d", ysize, py);
  printf("\n\tImage Zsize = %d ; Pimage Zsize = %d", zsize, pz);
  printf("\n\tImage Resolution = %f ; Pimage Resolution = %f", resol, pres);

  /***
   *  Find out maximum and minimum particle labels
   ***/

  for (k = 0; k < pz; k++) {
    m1 = k * nxy;
    for (j = 0; j < py; j++) {
      m2 = j * px;
      for (i = 0; i < px; i++) {
        m = m1 + m2 + i;
        fscanf(pfile, "%d", &inval);
        part[m] = inval;
        if ((npartmin > part[m]) && (part[m] != 0))
          npartmin = part[m];
        if ((npartmax < part[m]) && (part[m] != 0))
          npartmax = part[m];
      }
    }
  }

  printf("\nMinimum particle label = %d\n", npartmin);
  printf("Maximum particle label = %d\n", npartmax);
  fflush(stdout);
  taggednpartmax = npartmax;

  /***
   *  Now generate particle labels for all one-pixel cement particles
   *  Cement particles currently include clinker, gypsum phases, and
   *  limestone
   ***/

  for (k = 0; k < zsize; k++) {
    m1 = k * nxy;
    for (j = 0; j < ysize; j++) {
      m2 = j * xsize;
      for (i = 0; i < xsize; i++) {
        m = m1 + m2 + i;
        oinval = part[m];
        inval = p[m];
        if (inval == C3S || inval == C2S || inval == C3A || inval == OC3A ||
            inval == C4AF || inval == GYPSUM || inval == HEMIHYD ||
            inval == ANHYDRITE || inval == CACO3 || inval == NA2SO4 ||
            inval == K2SO4) {

          /***
           *  If cementitious, but not in part[m], then must
           *  be a one-pixel particle, so add to the particle list
           ***/

          if (oinval == 0) {
            npartmax++;
            part[m] = npartmax;
          }
        }
      }
    }
  }

  /***
   *  Find all possible pixels and process them to eliminate
   *  bonds between anhydrous cement particles that are due
   *  to a presumed weak attraction like flocculation or
   *  incidental contact
   ***/

  printf("\nTagged all one-pixel particles now:\n");
  printf("\tMinimum particle label = %d\n", npartmin);
  printf("\tMaximum particle label = %d\n", npartmax);
  fflush(stdout);

  nsw = 0; /* Number of particles switched off */
  for (k = 0; k < zsize; k++) {
    m1 = k * nxy;
    for (j = 0; j < ysize; j++) {
      m2 = j * xsize;
      for (i = 0; i < xsize; i++) {
        m = m1 + m2 + i;
        inval = p[m];
        if (inval == C3S || inval == C2S || inval == C3A || inval == OC3A ||
            inval == C4AF || inval == GYPSUM || inval == HEMIHYD ||
            inval == ANHYDRITE || inval == CACO3 || inval == NA2SO4 ||
            inval == K2SO4) {

          done = 0;
          for (ijk = 0; ijk < 27 && !done; ijk++) {
            i1 = i + in[ijk];
            j1 = j + jn[ijk];
            k1 = k + kn[ijk];
            i1 += checkbc(i1, xsize);
            j1 += checkbc(j1, ysize);
            k1 += checkbc(k1, zsize);

            mm = (k1 * nxy) + (j1 * xsize) + i1;

            ipp = p[mm];

            if (ipp == C3S || ipp == C2S || ipp == C3A || ipp == OC3A ||
                ipp == C4AF || ipp == GYPSUM || ipp == HEMIHYD ||
                ipp == ANHYDRITE || ipp == CACO3 || ipp == NA2SO4 ||
                ipp == K2SO4) {

              if (part[m] > part[mm]) {
                p[m] = EMPTYP;
                part[m] = 0;
                nsw++;
                done = 1;
              } else if (part[m] < part[mm]) {
                p[mm] = EMPTYP;
                part[mm] = 0;
                nsw++;
                done = 1;
              }
            }
          }
        }
      }
    }
  }

  printf("\nTotal number switched = %d\n", nsw);
  fflush(stdout);
  return (status);
}
