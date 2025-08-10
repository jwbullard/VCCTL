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
    printf("\n\nCould not allocate space for norig array.");
    return (MEMERR);
  }

  nleft = (int *)calloc((size_t)NPARTHYD, sizeof(int));
  if (!nleft) {
    printf("\n\nCould not allocate space for nleft array.");
    free(norig);
    return (MEMERR);
  }

  if (Verbose_flag == 2)
    printf("\nIn parthyd now.");
  for (ix = 0; ix < NPARTHYD; ix++) {
    nleft[ix] = norig[ix] = 0;
  }

  phydfile = filehandler("parthyd", Phrname, "APPEND");
  if (!phydfile) {
    return (MEMERR);
  }

  fprintf(phydfile, "%d %f\n", Cyccnt, Alpha_cur);

  partmax = 0;

  /***
   *	Scan the microstructure pixel by pixel
   *	and update counts
   ***/

  if (Verbose_flag == 2)
    printf("NPARTHYD is %d", NPARTHYD);
  for (ix = 0; ix < Xsyssize; ix++) {
    if (Verbose_flag == 2)
      printf("\tx = %d\n", ix);
    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 0; iz < Zsyssize; iz++) {
        if (Micpart[ix][iy][iz] != 0) {
          valpart = Micpart[ix][iy][iz];
          if (valpart > partmax)
            partmax = valpart;
          valmic = Mic[ix][iy][iz];
          if ((valmic == C3S) || (valmic == C2S) || (valmic == C3A) ||
              (valmic == C4AF) || (valmic == OC3A) || (valmic == K2SO4) ||
              (valmic == NA2SO4)) {

            if (valpart >= mult1 * NPARTHYD) {
              if (Verbose_flag == 2)
                printf("\t\tReallocating nleft now... ");
              mult1++;
              nleft = (int *)realloc((int *)nleft, (size_t)(mult1 * NPARTHYD));
              if (Verbose_flag == 2)
                printf("... Done!\n");
              if (!nleft) {
                printf("\n\nERROR in parthyd:  Could not reallocate space for "
                       "nleft array.");
                fflush(stdout);
                free(norig);
                return (MEMERR);
              }
            }

            nleft[valpart]++;
          }

          valmicorig = Micorig[ix][iy][iz];

          if ((valmicorig == C3S) || (valmicorig == C2S) ||
              (valmicorig == C3A) || (valmicorig == C4AF) ||
              (valmicorig == OC3A) || (valmicorig == K2SO4) ||
              (valmicorig == NA2SO4)) {

            if (valpart >= mult2 * NPARTHYD) {
              if (Verbose_flag == 2)
                printf("\t\tReallocating norig now... ");
              mult2++;
              norig = (int *)realloc((int *)norig, (size_t)(mult2 * NPARTHYD));
              if (Verbose_flag == 2)
                printf("... Done!\n");
              if (!norig) {
                printf("\n\nERROR in parthyd:  Could not reallocate space for "
                       "norig array.");
                fflush(stdout);
                free(nleft);
                return (MEMERR);
              }
            }
            norig[valpart]++;
          }
        }
      }
    }
  }

  /* Output results to end of particle hydration file */

  if (Verbose_flag == 2)
    printf("\nMain loop of parthyd concluded.");
  fflush(stdout);
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
