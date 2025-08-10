/***
 *	burnset
 *
 * 	Assess connectivity (percolation) of solids for set estimation.
 *
 *	Definition of set is a through pathway of cement and fly ash (slag)
 *	particles connected together by a form of CSH, C3AH6, or ettringite
 *
 *	Two matrices are used here: one to store the recently burnt locations
 *	the other to store the newly found burnt locations
 *
 * 	Arguments:	int d1: x-direction flag
 * 				int d2: y-direction flag
 * 				int d3: z-direction flag
 *
 * 	Returns:	1 if a connected path is found, 0 otherwise
 *
 *	Calls:		No other routines
 *	Called by:	disrealnew
 ***/

/* Label for a burnt pixel */

#ifndef BURNT
#define BURNT ((OFFSET) + 1)
#endif

/***
 *	Functions defining coordinates for
 *	burning in any of three directions
 ***/

#define cx(x, y, z, a, b, c) (1 - b - c) * x + (1 - a - c) * y + (1 - a - b) * z
#define cy(x, y, z, a, b, c) (1 - a - b) * x + (1 - b - c) * y + (1 - a - c) * z
#define cz(x, y, z, a, b, c) (1 - a - c) * x + (1 - a - b) * y + (1 - b - c) * z

int burnset(int d1, int d2, int d3) {
  int ***newmat, ***xformMic, ***xformMicpart;
  int *nnewx, *nnewy, *nnewz, *nmatx, *nmaty, *nmatz;
  int ntop, nthrough, icur, inew, ncur, nnew, ntot, count_solid, SIZESET;
  int i, j, k, setyet, dir, ival, dimensions[3];
  int xl, xh, j1, k1, px, py, pz, qx, qy, qz, xm, ym, zm;
  int xcn, ycn, zcn, x1, y1, z1, igood, jnew;
  float alpha_burn = 0.0, tvar;
  double mass_burn = 0.0;

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

  SIZESET = (5 * dimensions[0] * dimensions[1]);

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

  /***
   *	Counters for number of pixels of phase accessible from
   *	surface #1 and number which are part of a percolated
   *	pathway to surface #2
   ***/

  if (Verbose_flag == 2) {
    printf("\nIn burnset: d1 = %d, d2 = %d, d3 = %d", d1, d2, d3);
    fflush(stdout);
  }

  /***
   *	No convenient way to reset the system after
   *	burning is done, so just store the initial
   *	(transformed) microstructure by brute force and then
   *	reset at the end (1 June 2004)
   ***/

  xformMic = NULL;
  xformMic = ibox(dimensions[0], dimensions[1], dimensions[2]);
  if (!xformMic) {
    printf("\nERROR in burnset:");
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
  if (Verbose_flag == 2) {
    printf("\nAssignment to xformMic is complete.");
    fflush(stdout);
  }

  /*  Allocate memory for transformed Micpart array */

  xformMicpart = NULL;
  xformMicpart = ibox(dimensions[0], dimensions[1], dimensions[2]);
  if (!xformMicpart) {
    printf("\nERROR in burnset:");
    printf("\n\tCould not allocate space for xformMicpart.");
    printf("\n\tExiting now.");
    fflush(stdout);
    if (xformMic)
      free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }

  for (zm = 0; zm < Zsyssize; zm++) {
    for (ym = 0; ym < Ysyssize; ym++) {
      for (xm = 0; xm < Xsyssize; xm++) {
        px = cx(xm, ym, zm, d1, d2, d3);
        py = cy(xm, ym, zm, d1, d2, d3);
        pz = cz(xm, ym, zm, d1, d2, d3);
        xformMicpart[px][py][pz] = Micpart[xm][ym][zm];
      }
    }
  }
  if (Verbose_flag == 2) {
    printf("\nAssignment to xformMicpart is complete.");
    fflush(stdout);
  }

  /*  Allocate memory for transformed newmat array */

  newmat = NULL;
  newmat = ibox(dimensions[0], dimensions[1], dimensions[2]);
  if (!newmat) {
    printf("\nERROR in burnset:");
    printf("\n\tCould not allocate space for newmat.");
    printf("\n\tExiting now.");
    fflush(stdout);
    if (xformMicpart)
      free_ibox(xformMicpart, dimensions[0], dimensions[1]);
    if (xformMic)
      free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }

  for (zm = 0; zm < Zsyssize; zm++) {
    for (ym = 0; ym < Ysyssize; ym++) {
      for (xm = 0; xm < Xsyssize; xm++) {
        px = cx(xm, ym, zm, d1, d2, d3);
        py = cy(xm, ym, zm, d1, d2, d3);
        pz = cz(xm, ym, zm, d1, d2, d3);
        newmat[px][py][pz] = xformMic[px][py][pz];
      }
    }
  }
  if (Verbose_flag == 2) {
    printf("\nAssignment to newmat is complete.");
    fflush(stdout);
  }

  nmatx = nmaty = nmatz = NULL;
  nnewx = nnewy = nnewz = NULL;

  if (Verbose_flag == 2) {
    printf("\nI am in burnset...");
    fflush(stdout);
  }

  nmatx = ivector(SIZESET);
  if (Verbose_flag == 2) {
    printf("\nAllocated nmatx...");
    fflush(stdout);
  }
  nmaty = ivector(SIZESET);
  if (Verbose_flag == 2) {
    printf("\nAllocated nmaty...");
    fflush(stdout);
  }
  nmatz = ivector(SIZESET);
  if (Verbose_flag == 2) {
    printf("\nAllocated nmatz...");
    fflush(stdout);
  }
  nnewx = ivector(SIZESET);
  if (Verbose_flag == 2) {
    printf("\nAllocated nnewx...");
    fflush(stdout);
  }
  nnewy = ivector(SIZESET);
  if (Verbose_flag == 2) {
    printf("\nAllocated nnewy...");
    fflush(stdout);
  }
  nnewz = ivector(SIZESET);
  if (Verbose_flag == 2) {
    printf("\nAllocated nnewz...");
    fflush(stdout);
  }

  if (!nmatx) {
    printf("\nERROR in burnset:");
    printf("\n\tCould not allocate space for nmatx.");
    printf("\n\tExiting now.");
    fflush(stdout);
    if (xformMicpart)
      free_ibox(xformMicpart, dimensions[0], dimensions[1]);
    if (xformMic != NULL)
      free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }
  if (!nmaty) {
    printf("\nERROR in burnset:");
    printf("\n\tCould not allocate space for nmaty.");
    printf("\n\tExiting now.");
    fflush(stdout);
    free_ivector(nmatx);
    if (xformMicpart)
      free_ibox(xformMicpart, dimensions[0], dimensions[1]);
    if (xformMic != NULL)
      free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }
  if (!nmatz) {
    printf("\nERROR in burnset:");
    printf("\n\tCould not allocate space for nmatz.");
    printf("\n\tExiting now.");
    fflush(stdout);
    free_ivector(nmaty);
    free_ivector(nmatx);
    if (xformMicpart)
      free_ibox(xformMicpart, dimensions[0], dimensions[1]);
    if (xformMic != NULL)
      free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }
  if (!nnewx) {
    printf("\nERROR in burnset:");
    printf("\n\tCould not allocate space for nnewx.");
    printf("\n\tExiting now.");
    fflush(stdout);
    free_ivector(nmatz);
    free_ivector(nmaty);
    free_ivector(nmatx);
    if (xformMicpart)
      free_ibox(xformMicpart, dimensions[0], dimensions[1]);
    if (xformMic != NULL)
      free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }
  if (!nnewy) {
    printf("\nERROR in burnset:");
    printf("\n\tCould not allocate space for nnewy.");
    printf("\n\tExiting now.");
    fflush(stdout);
    free_ivector(nnewx);
    free_ivector(nmatz);
    free_ivector(nmaty);
    free_ivector(nmatx);
    if (xformMicpart)
      free_ibox(xformMicpart, dimensions[0], dimensions[1]);
    if (xformMic != NULL)
      free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }
  if (!nnewz) {
    printf("\nERROR in burnset:");
    printf("\n\tCould not allocate space for newz.");
    printf("\n\tExiting now.");
    fflush(stdout);
    free_ivector(nnewy);
    free_ivector(nnewx);
    free_ivector(nmatz);
    free_ivector(nmaty);
    free_ivector(nmatx);
    if (xformMicpart)
      free_ibox(xformMicpart, dimensions[0], dimensions[1]);
    if (xformMic != NULL)
      free_ibox(xformMic, dimensions[0], dimensions[1]);
    return (MEMERR);
  }

  ntop = nthrough = setyet = 0;

  if (Verbose_flag == 2) {
    printf("\nAll memory allocation went okay...");
    fflush(stdout);
  }

  /***
   *	Percolation is assessed from top to bottom only in
   *	transformed coordinates and burning algorithm is
   *	periodic in other two directions
   ***/

  i = 0; /* Starting from the bottom x face */

  for (k = 0; k < dimensions[2]; k++) {
    for (j = 0; j < dimensions[1]; j++) {
      if (Verbose_flag == 2 && dir == 1) {
        printf("\nLoop j,k = %d,%d", j, k);
        fflush(stdout);
      }

      igood = ncur = ntot = 0;

      /* Transform coordinates */

      px = i;
      py = j;
      pz = k;

      /***
       *	Start from a cement clinker, slag, fly ash,
       *	ettringite, C3AH6, or CSH pixel
       ***/

      if ((xformMic[px][py][pz] == C3S) || (xformMic[px][py][pz] == C2S) ||
          (xformMic[px][py][pz] == K2SO4) || (xformMic[px][py][pz] == NA2SO4) ||
          (xformMic[px][py][pz] == SLAG) || (xformMic[px][py][pz] == ASG) ||
          (xformMic[px][py][pz] == CAS2) || (xformMic[px][py][pz] == SFUME) ||
          (xformMic[px][py][pz] == AMSIL) || (xformMic[px][py][pz] == CSH) ||
          (xformMic[px][py][pz] == POZZCSH) ||
          (xformMic[px][py][pz] == SLAGCSH) ||
          (xformMic[px][py][pz] == C3AH6) || (xformMic[px][py][pz] == ETTR) ||
          (xformMic[px][py][pz] == ETTRC4AF) || (xformMic[px][py][pz] == C3A) ||
          (xformMic[px][py][pz] == C4AF)) {

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

            /* Convert to directional coordinates */

            qx = xcn;
            qy = ycn;
            qz = zcn;

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

              /* Periodic in y and z direction */

              y1 += checkbc(y1, dimensions[1]);
              z1 += checkbc(z1, dimensions[2]);

              /***
               *	Nonperiodic in x, so be sure to
               *	remain in the 3-D box
               ***/

              if ((x1 >= 0) && (x1 < dimensions[0])) {

                px = x1;
                py = y1;
                pz = z1;

                /***
                 *	First condition for propagation
                 *	of burning:
                 *
                 *		1) new pixel is CSH or
                 *			ETTR or C3AH6
                 ***/

                if ((xformMic[px][py][pz] == CSH) ||
                    (xformMic[px][py][pz] == POZZCSH) ||
                    (xformMic[px][py][pz] == SLAGCSH) ||
                    (xformMic[px][py][pz] == ETTRC4AF) ||
                    (xformMic[px][py][pz] == C3AH6) ||
                    (xformMic[px][py][pz] == ETTR)) {

                  ntot++;
                  xformMic[px][py][pz] = BURNT;
                  nnew++;

                  if (nnew >= SIZESET) {
                    printf("\nERROR in burnset:");
                    printf("\n\tSize of nnew %d ", nnew);
                    printf("must be less than ");
                    printf("%d\n", SIZESET);
                    fflush(stdout);
                  }

                  nnewx[nnew] = x1;
                  nnewy[nnew] = y1;
                  nnewz[nnew] = z1;

                  /***
                   *	Second condition for burning:
                   *
                   *		2) Old pixel is CSH or ETTR
                   *			or C3AH6, and new pixel
                   *			is one of cement clinker,
                   *			slag, of fly ash phases
                   ***/

                } else if (((newmat[qx][qy][qz] == CSH) ||
                            (newmat[qx][qy][qz] == SLAGCSH) ||
                            (newmat[qx][qy][qz] == POZZCSH) ||
                            (newmat[qx][qy][qz] == ETTRC4AF) ||
                            (newmat[qx][qy][qz] == C3AH6) ||
                            (newmat[qx][qy][qz] == ETTR)) &&
                           ((xformMic[px][py][pz] == C3S) ||
                            (xformMic[px][py][pz] == C2S) ||
                            (xformMic[px][py][pz] == K2SO4) ||
                            (xformMic[px][py][pz] == NA2SO4) ||
                            (xformMic[px][py][pz] == CAS2) ||
                            (xformMic[px][py][pz] == SLAG) ||
                            (xformMic[px][py][pz] == SFUME) ||
                            (xformMic[px][py][pz] == AMSIL) ||
                            (xformMic[px][py][pz] == ASG) ||
                            (xformMic[px][py][pz] == C3A) ||
                            (xformMic[px][py][pz] == C4AF))) {

                  ntot++;
                  xformMic[px][py][pz] = BURNT;
                  nnew++;

                  if (nnew >= SIZESET) {
                    printf("\nERROR in burnset:");
                    printf("\n\tSize of nnew %d ", nnew);
                    printf("must be less than ");
                    printf("%d\n", SIZESET);
                    fflush(stdout);
                  }

                  nnewx[nnew] = x1;
                  nnewy[nnew] = y1;
                  nnewz[nnew] = z1;

                  /***
                   *	Third condition for burning:
                   *
                   * 	3) Old and new pixels belong
                   * 		to one of cement clinker,
                   * 		slag, or fly ash phases
                   *
                   * 		AND are contained in the
                   * 		same initial cement particle
                   *
                   * 		AND it is not a one-pixel
                   * 		particle
                   ***/

                } else if ((xformMicpart[qx][qy][qz] ==
                            xformMicpart[px][py][pz]) &&
                           (xformMicpart[qx][qy][qz] != 0) &&
                           ((xformMic[px][py][pz] == C3S) ||
                            (xformMic[px][py][pz] == C2S) ||
                            (xformMic[px][py][pz] == K2SO4) ||
                            (xformMic[px][py][pz] == NA2SO4) ||
                            (xformMic[px][py][pz] == SFUME) ||
                            (xformMic[px][py][pz] == AMSIL) ||
                            (xformMic[px][py][pz] == SLAG) ||
                            (xformMic[px][py][pz] == ASG) ||
                            (xformMic[px][py][pz] == CAS2) ||
                            (xformMic[px][py][pz] == C3A) ||
                            (xformMic[px][py][pz] == C4AF)) &&
                           ((newmat[qx][qy][qz] == C3S) ||
                            (newmat[qx][qy][qz] == C2S) ||
                            (newmat[qx][qy][qz] == K2SO4) ||
                            (newmat[qx][qy][qz] == NA2SO4) ||
                            (newmat[qx][qy][qz] == SLAG) ||
                            (newmat[qx][qy][qz] == ASG) ||
                            (newmat[qx][qy][qz] == SFUME) ||
                            (newmat[qx][qy][qz] == AMSIL) ||
                            (newmat[qx][qy][qz] == CAS2) ||
                            (newmat[qx][qy][qz] == C3A) ||
                            (newmat[qx][qy][qz] == C4AF))) {

                  ntot++;
                  xformMic[px][py][pz] = BURNT;
                  nnew++;

                  if (nnew >= SIZESET) {
                    printf("\nERROR in burnset:");
                    printf("\n\tSize of nnew %d ", nnew);
                    printf("must be less than ");
                    printf("%d\n", SIZESET);
                    fflush(stdout);
                  }

                  nnewx[nnew] = x1;
                  nnewy[nnew] = y1;
                  nnewz[nnew] = z1;
                }
              } /* nonperiodic if delimiter */
            } /* End of loop over nearest neighbors */
          } /* End of loop over current burn front */

          if (nnew > 0) {

            ncur = nnew;

            /* Update the burn front matrices */

            for (icur = 1; icur <= ncur; icur++) {
              nmatx[icur] = nnewx[icur];
              nmaty[icur] = nnewy[icur];
              nmatz[icur] = nnewz[icur];
            }
          }

        } while (nnew > 0);

        /* Out of fuel.  Burning is over */

        ntop += ntot;

        xl = 0;
        xh = dimensions[0] - 1;

        /* Check for percolated path through system */

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

  if (Verbose_flag == 2) {
    printf("Phase ID= Solid Phases \n");
    printf("Number accessible from first surface = %d \n", ntop);
    printf("Number contained in through pathways= %d \n", nthrough);
    fflush(stdout);
  }

  mass_burn += (double)(Specgrav[C3S] * Count[C3S]);
  mass_burn += (double)(Specgrav[C2S] * Count[C2S]);
  mass_burn += (double)(Specgrav[C3A] * Count[C3A]);
  mass_burn += (double)(Specgrav[C4AF] * Count[C4AF]);

  alpha_burn = 1.0 - (mass_burn / Cemmass);
  Con_fracs[dir] = 0.0;

  count_solid =
      Count[C3S] + Count[C2S] + Count[C3A] + Count[K2SO4] + Count[NA2SO4];
  count_solid +=
      Count[C4AF] + Count[ETTR] + Count[CSH] + Count[POZZCSH] + Count[SLAGCSH];
  count_solid += Count[C3AH6] + Count[ETTRC4AF] + Count[SFUME];
  count_solid += Count[AMSIL] + Count[ASG] + Count[SLAG] + Count[CAS2];

  if (Verbose_flag == 2)
    printf("Count solids = %d\n", count_solid);
  if (count_solid > 0) {
    Con_fracs[dir] = (float)nthrough / (float)count_solid;
    if (Verbose_flag == 2)
      printf("Con_fracs[%d] = %f\n", dir, Con_fracs[dir]);
  }

  tvar = Time_cur + (2.0 * (float)(Cyccnt)-1.0) * (Beta / Krate);

  if (Con_fracs[dir] > 0.985)
    setyet = 1;

  /***
   *	Free all dynamically allocated memory
   ***/

  free_ivector(nmatx);
  free_ivector(nmaty);
  free_ivector(nmatz);
  free_ivector(nnewx);
  free_ivector(nnewy);
  free_ivector(nnewz);
  if (newmat != NULL)
    free_ibox(newmat, dimensions[0], dimensions[1]);
  if (xformMicpart != NULL)
    free_ibox(xformMicpart, dimensions[0], dimensions[1]);
  if (xformMic != NULL)
    free_ibox(xformMic, dimensions[0], dimensions[1]);

  /***
   *	Return flag indicating if set has
   *	indeed occurred
   ***/

  return (setyet);
}
