/***
 *	burn3d
 *
 * 	Assess the connectivity (percolation) of combination
 * 	of any two phases, not distinguishing between them
 *
 * 	Ability to add second phase in combination was incorporated
 * 	on 24 May 2004, specifically to handle saturated porosity
 * 	(POROSITY) in combination with saturated porosity in a
 * 	crack (CRACKP) formed during hydration cycle.
 *
 * 	Two matrices are used:  one to store the recently burnt
 * 	locations, and one to store the newly-found burnt locations
 *
 * 	Arguments:	int npix1: ID of first phase to burn
 * 				int npix2: ID of second phase to burn
 * 				int d1: x-direction flag
 * 				int d2: y-direction flag
 * 				int d3: z-direction flag
 *
 * 	Returns:	1 if a connected path is found, 0 otherwise
 *
 *	Calls:		No other routines
 *	Called by:	disrealnew
 ***/

/***
 *	Functions defining coordinates for
 *	burning in any of three directions
 ***/

#define cx(x, y, z, a, b, c) (1 - b - c) * x + (1 - a - c) * y + (1 - a - b) * z
#define cy(x, y, z, a, b, c) (1 - a - b) * x + (1 - b - c) * y + (1 - a - c) * z
#define cz(x, y, z, a, b, c) (1 - a - c) * x + (1 - a - b) * y + (1 - b - c) * z

int burn3d(int npix1, int npix2, int d1, int d2, int d3) {
  static int BURNT;
  static int SIZE2D;
  int ***xformMic;
  int i, inew, j, k, x1, y1, z1, igood, jnew, icur, bflag;
  int *nmatx, *nmaty, *nmatz, *nnewx, *nnewy, *nnewz;
  int mult1, mult2, xm, ym, zm;
  int dir, ival, dimensions[3];
  int xl, xh, j1, k1, px, py, pz, qx, qy, qz, xcn, ycn, zcn;
  int ntop, nthrough, ncur, nnew, ntot;
  float alpha_burn = 0.0;
  double mass_burn = 0.0;

  if (Verbose) {
    printf("\nI am in burn3d...");
    fflush(stdout);
  }

  /* Initialize local arrays */

  dimensions[0] = Xsyssize;
  dimensions[1] = Ysyssize;
  dimensions[2] = Zsyssize;

  /* Bubble sort the dimensions in descending order */
  for (i = 0; i < 2; i++) {
    for (j = (i + 1); j < 3; j++) {
      if (dimensions[i] < dimensions[j]) {
        ival = dimensions[i];
        dimensions[i] = dimensions[j];
        dimensions[j] = ival;
      }
    }
  }

  SIZE2D = (5 * dimensions[0] * dimensions[1]);

  if (d1 == 1 && d2 == 0 && d3 == 0) {
    dir = 0;
    dimensions[0] = Xsyssize;
    dimensions[1] = Ysyssize;
    dimensions[2] = Zsyssize;
  } else if (d1 == 0 && d2 == 1 && d3 == 0) {
    dir = 1;
    dimensions[0] = Ysyssize;
    dimensions[1] = Zsyssize;
    dimensions[2] = Xsyssize;
  } else {
    dir = 2;
    dimensions[0] = Zsyssize;
    dimensions[1] = Xsyssize;
    dimensions[2] = Ysyssize;
  }

  Nphc[dir] = 0;

  BURNT = (int)((OFFSET) + (OFFSET));

  xformMic = NULL;

  /***
   *	No convenient way to reset the system after
   *	burning is done, so just store the initial
   *	(transformed) microstructure by brute force and then
   *	reset at the end (1 Jun004)
   ***/

  xformMic = ibox(dimensions[0], dimensions[1], dimensions[2]);
  if (!xformMic) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for xformMic.");
    printf("\n\tExiting now.");
    fflush(stdout);
    return (MEMERR);
  }

  for (zm = 0; zm < Zsyssize; zm++) {
    for (ym = 0; ym < Ysyssize; ym++) {
      for (xm = 0; xm < Xsyssize; xm++) {
        px = cx(xm, ym, zm, d1, d2, d3);
        py = cy(xm, ym, zm, d1, d2, d3);
        pz = cz(xm, ym, zm, d1, d2, d3);
        xformMic[px][py][pz] = Mic[xm][ym][zm];
      }
    }
  }

  if (Verbose) {
    printf("\nAssignment to xformMic is complete.");
    fflush(stdout);
  }

  nmatx = nmaty = nmatz = NULL;
  nnewx = nnewy = nnewz = NULL;
  mult1 = mult2 = 1;

  nmatx = ivector(SIZE2D);
  if (Verbose) {
    printf("\nAllocated nmatx...");
    fflush(stdout);
  }
  nmaty = ivector(SIZE2D);
  if (Verbose) {
    printf("\nAllocated nmaty...");
    fflush(stdout);
  }
  nmatz = ivector(SIZE2D);
  if (Verbose) {
    printf("\nAllocated nmatz...");
    fflush(stdout);
  }
  nnewx = ivector(SIZE2D);
  if (Verbose) {
    printf("\nAllocated nnewx...");
    fflush(stdout);
  }
  nnewy = ivector(SIZE2D);
  if (Verbose) {
    printf("\nAllocated nnewy...");
    fflush(stdout);
  }
  nnewz = ivector(SIZE2D);
  if (Verbose) {
    printf("\nAllocated nnewz...");
    fflush(stdout);
  }

  if (!nmatx) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for nmatx.");
    printf("\n\tExiting now.");
    fflush(stdout);
    free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }
  if (!nmaty) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for nmaty.");
    printf("\n\tExiting now.");
    fflush(stdout);
    free_ivector(nmatx);
    free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }
  if (!nmatz) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for nmatz.");
    printf("\n\tExiting now.");
    fflush(stdout);
    free_ivector(nmaty);
    free_ivector(nmatx);
    free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }
  if (!nnewx) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for nnewx.");
    printf("\n\tExiting now.");
    fflush(stdout);
    free_ivector(nmatz);
    free_ivector(nmaty);
    free_ivector(nmatx);
    free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }
  if (!nnewy) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for nnewy.");
    printf("\n\tExiting now.");
    fflush(stdout);
    free_ivector(nnewx);
    free_ivector(nmatz);
    free_ivector(nmaty);
    free_ivector(nmatx);
    free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }
  if (!nnewz) {
    printf("\nERROR in burn3d:");
    printf("\n\tCould not allocate space for newz.");
    printf("\n\tExiting now.");
    fflush(stdout);
    free_ivector(nnewy);
    free_ivector(nnewx);
    free_ivector(nmatz);
    free_ivector(nmaty);
    free_ivector(nmatx);
    free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }

  /***
   *	Counters for number of pixels of phase accessible
   *	from surface #1 and number which are part of a
   *	percolated pathway to surface #2
   ***/

  ntop = bflag = nthrough = 0;

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

  for (k = 0; k < dimensions[2]; k++) {
    for (j = 0; j < dimensions[1]; j++) {

      igood = ncur = ntot = 0;

      /* Transform coordinates */

      px = i;
      py = j;
      pz = k;

      if (xformMic[px][py][pz] == npix1 || xformMic[px][py][pz] == npix2) {

        /* Start a burn front */

        xformMic[px][py][pz] = BURNT;
        ntot++;
        ncur++;

        /***
         *	Burn front is stored in matrices nmat*
         *	and nnew*
         ***/

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

              y1 += checkbc(y1, dimensions[1]);
              z1 += checkbc(z1, dimensions[2]);

              /***
               *	Nonperiodic in x so be sure to remain
               *	in the 3-D box
               ***/

              if ((x1 >= 0) && (x1 < dimensions[0])) {

                /* Transform coordinates */

                px = x1;
                py = y1;
                pz = z1;

                if (xformMic[px][py][pz] == npix1 ||
                    xformMic[px][py][pz] == npix2) {
                  ntot++;
                  xformMic[px][py][pz] = BURNT;
                  nnew++;

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

        ntop += ntot;
        xl = 0;
        xh = dimensions[0] - 1;

        /***
         *	See if current path extends through
         *	the microstructure
         ***/

        for (j1 = 0; j1 < dimensions[1]; j1++) {
          for (k1 = 0; k1 < dimensions[2]; k1++) {

            px = xl;
            py = j1;
            pz = k1;
            qx = xh;
            qy = j1;
            qz = k1;

            if ((xformMic[px][py][pz] == BURNT) &&
                (xformMic[qx][qy][qz] == BURNT)) {

              igood = 2;
            }

            if (xformMic[px][py][pz] == BURNT) {
              xformMic[px][py][pz] = BURNT + 1;
            }

            if (xformMic[qx][qy][qz] == BURNT) {
              xformMic[qx][qy][qz] = BURNT + 1;
            }
          }
        }

        if (igood == 2)
          nthrough += ntot;
      }
    }
  }

  /***
   *	Finished sampling all pixels of type npix1 and npix2 along
   *	the bottom x face
   *
   *	Return the burnt sites to their original
   *	phase values
   ***/

  for (k = 0; k < dimensions[2]; k++) {
    for (j = 0; j < dimensions[1]; j++) {
      for (i = 0; i < dimensions[0]; i++) {

        if (xformMic[i][j][k] >= BURNT) {

          Nphc[dir]++;
        } else if (xformMic[i][j][k] == npix1 || xformMic[i][j][k] == npix2) {
          Nphc[dir]++;
        }
      }
    }
  }

  if (Verbose) {
    if (npix1 != npix2) {
      printf("Phase IDs = %d and %d \n", npix1, npix2);
    } else {
      printf("Phase ID = %d \n", npix1);
    }
    printf("Number accessible from first surface = %d \n", ntop);
    printf("Number contained in through pathways= %d \n", nthrough);
    fflush(stdout);
  }

  mass_burn += (double)(Specgrav[C3S] * Count[C3S]);
  mass_burn += (double)(Specgrav[C2S] * Count[C2S]);
  mass_burn += (double)(Specgrav[C3A] * Count[C3A]);
  mass_burn += (double)(Specgrav[C4AF] * Count[C4AF]);
  alpha_burn = 1.0 - (mass_burn / Cemmass);

  Con_fracp[dir] = 0.0;

  if (Verbose)
    printf("Nphc[%d] = %d\n", dir, Nphc[dir]);
  if (Nphc[dir] > 0) {
    Con_fracp[dir] = (float)nthrough / (float)Nphc[dir];
    if (Verbose)
      printf("Con_fracp[%d] = %f\n", dir, Con_fracp[dir]);
  }

  if (nthrough > 0)
    bflag = 1;

  free_ivector(nnewz);
  free_ivector(nnewy);
  free_ivector(nnewx);
  free_ivector(nmatz);
  free_ivector(nmaty);
  free_ivector(nmatx);
  free_ibox(xformMic, dimensions[0], dimensions[1]);

  return (bflag);
}
