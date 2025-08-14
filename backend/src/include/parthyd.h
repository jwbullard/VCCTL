
/***
 *	parthyd
 *
 * 	Assess relative particle hydration
 *
 * 	Arguments:	None
 * 	Returns:	Status flag (0 if okay, -1 if not exiting);
 *
 *	Calls:		No other routines
 *	Called by:	disrealnew
 ***/

#define NPARTHYD 200000

int parthyd(void) {
  int *norig, *nleft, mult1, mult2;
  int ix, iy, iz, valpart, partmax;
  float alpart;
  char valmic, valmicorig;
  FILE *phydfile;

  /* Initialize the particle count arrays */

  norig = NULL;
  nleft = NULL;

  mult1 = mult2 = 1;

  norig = (int *)calloc((size_t)NPARTHYD, sizeof(int));
  if (!norig) {
    fprintf(stderr, "\nERROR: Could not allocate space for norig array.");
    fflush(stderr);
    return (MEMERR);
  }

  nleft = (int *)calloc((size_t)NPARTHYD, sizeof(int));
  if (!nleft) {
    fprintf(stderr, "\nERROR: Could not allocate space for nleft array.");
    fflush(stderr);
    free(norig);
    return (MEMERR);
  }

  if (Verbose_flag > 1) {
    fprintf(stderr, "\nDEBUG: In parthyd now.");
    fflush(stderr);
  }
  for (ix = 0; ix < NPARTHYD; ix++) {
    nleft[ix] = norig[ix] = 0;
  }

  phydfile = filehandler("parthyd", Phrname, "APPEND");
  if (!phydfile) {
    fprintf(stderr, "\nERROR: Cannot open file %s", Phrname);
    fflush(stderr);
    return (MEMERR);
  }

  if (Verbose_flag > 1) {
    fprintf(stderr, "\nDEBUG: Opened %s", Phrname);
    fflush(stderr);
  }

  fprintf(phydfile, "%d %f\n", Cyccnt, Alpha_cur);

  partmax = 0;

  /***
   *	Scan the microstructure pixel by pixel
   *	and update counts
   ***/

  if (Verbose_flag > 1) {
    fprintf(stderr, "\nDEBUG: NPARTHYD is %d", NPARTHYD);
    fflush(stderr);
  }

  for (ix = 0; ix < Xsyssize; ix++) {
    if (Verbose_flag > 1) {
      fprintf(stderr, "\nDEBUG: x = %d", ix);
      fflush(stderr);
    }
    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 0; iz < Zsyssize; iz++) {

        /* CRITICAL: Add array bounds validation before access */
        if (ix >= Xsyssize || iy >= Ysyssize || iz >= Zsyssize) {
          fprintf(
              stderr,
              "\nERROR: Array bounds exceeded at (%d,%d,%d), limits=(%d,%d,%d)",
              ix, iy, iz, Xsyssize, Ysyssize, Zsyssize);
          fflush(stderr);
          return (MEMERR);
        }

        if (Micpart[ix][iy][iz] != 0) {
          valpart = Micpart[ix][iy][iz];

          /* CRITICAL: Check for negative valpart causing buffer underflow */
          if (valpart < 0) {
            continue; /* Skip this particle to prevent segfault */
          }

          if (valpart > partmax)
            partmax = valpart;

          valmic = Mic[ix][iy][iz];
          if ((valmic == C3S) || (valmic == C2S) || (valmic == C3A) ||
              (valmic == C4AF) || (valmic == OC3A) || (valmic == K2SO4) ||
              (valmic == NA2SO4)) {

            if (valpart >= mult1 * NPARTHYD) {
              if (Verbose_flag > 2) {
                fprintf(stderr, "\nDEBUG: Reallocating nleft now... ");
                fflush(stderr);
              }
              mult1++;
              nleft = (int *)realloc((int *)nleft,
                                     (size_t)(mult1 * NPARTHYD * sizeof(int)));
              if (Verbose_flag > 1) {
                fprintf(stderr, " Done!");
                fflush(stderr);
              }
              if (!nleft) {
                fprintf(stderr,
                        "\nERROR in parthyd:  Could not reallocate space for "
                        "nleft array.");
                fflush(stderr);
                free(norig);
                return (MEMERR);
              }
              /* Initialize newly allocated memory to zero */
              for (int i = (mult1 - 1) * NPARTHYD; i < mult1 * NPARTHYD; i++) {
                nleft[i] = 0;
              }
            }

            /* CRITICAL: Protection against negative array access */
            if (valpart >= 0 && valpart < mult1 * NPARTHYD) {
              nleft[valpart]++;
            }
          }

          valmicorig = Micorig[ix][iy][iz];

          if ((valmicorig == C3S) || (valmicorig == C2S) ||
              (valmicorig == C3A) || (valmicorig == C4AF) ||
              (valmicorig == OC3A) || (valmicorig == K2SO4) ||
              (valmicorig == NA2SO4)) {

            if (valpart >= mult2 * NPARTHYD) {
              if (Verbose_flag > 2) {
                fprintf(stderr, "\nDEBUG: Reallocating norig now... ");
                fflush(stderr);
              }
              mult2++;
              norig = (int *)realloc((int *)norig,
                                     (size_t)(mult2 * NPARTHYD * sizeof(int)));
              if (Verbose_flag > 2) {
                fprintf(stderr, " Done!");
                fflush(stderr);
              }
              if (!norig) {
                fprintf(stderr,
                        "\nERROR in parthyd:  Could not reallocate space for "
                        "norig array.");
                fflush(stderr);
                free(nleft);
                return (MEMERR);
              }
              /* Initialize newly allocated memory to zero */
              for (int i = (mult2 - 1) * NPARTHYD; i < mult2 * NPARTHYD; i++) {
                norig[i] = 0;
              }
            }
            /* CRITICAL: Protection against negative array access */
            if (valpart >= 0 && valpart < mult2 * NPARTHYD) {
              norig[valpart]++;
            }
          }
        }
      }
    }
  }

  /* Output results to end of particle hydration file */

  if (Verbose_flag > 2) {
    fprintf(stderr, "\nDEBUG: Main loop of parthyd concluded.");
    fflush(stderr);
  }
  for (ix = 100; ix <= partmax; ix++) {

    alpart = 0.0;

    if (norig[ix] != 0) {
      alpart = 1.0 - ((double)nleft[ix] / (double)norig[ix]);
    }

    fprintf(phydfile, "%d %d %d %.3f\n", ix, norig[ix], nleft[ix], alpart);
  }

  fclose(phydfile);
  free(norig);
  free(nleft);

  return (0);
}
