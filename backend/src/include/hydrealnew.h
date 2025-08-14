/***
 *    hydrealnew
 *
 *     Collection of functions to perform hydration
 *     reactions on a 3D microstructure
 *
 *     Arguments:    None
 *     Returns:    Nothing
 *
 *    Calls:        No other routines
 *    Called by:    disrealnew
 ***/

/***
 *    moveone
 *
 *    Select a new neighboring location to (xloc, yloc, zloc)
 *    for a diffusing species
 *
 *     Arguments:    Int pointers to location (x,y,z)
 *                 Int pointer to act, the direction (1 through 6)
 *                 Int sumold
 *
 *     Returns:    Prime number flag indicating direction chosen
 *
 *    Calls:        ran1
 *    Called by:    movecsh, extettr, extfh3, movegyp, extafm,
 *                moveettr, extpozz, movefh3, extc3ah5, movec3a,
 *                extfriedel, movecacl2, extstrat, moveas
 ***/
void extpozz(int xpres, int ypres, int zpres, int *poreid);

int moveone(int *xloc, int *yloc, int *zloc, int *act, int sumold) {
  int plok, sumnew, xl1, yl1, zl1, act1;

  sumnew = 1;

  /* Store the input values for location */

  xl1 = (*xloc);
  yl1 = (*yloc);
  zl1 = (*zloc);
  act1 = (*act);

  /***
   *    Choose one of six directions (at random)
   *    for the new location
   ***/

  plok = 6.0 * ran1(Seed);
  if ((plok > 5) || (plok < 0))
    plok = 5;

  switch (plok) {
  case 0:
    xl1--;
    act1 = 1;
    if (xl1 < 0)
      xl1 = Xsyssize - 1;
    if (sumold % 2 != 0)
      sumnew = 2;
    break;
  case 1:
    xl1++;
    act1 = 2;
    if (xl1 >= Xsyssize)
      xl1 = 0;
    if (sumold % 3 != 0)
      sumnew = 3;
    break;
  case 2:
    yl1--;
    act1 = 3;
    if (yl1 < 0)
      yl1 = Ysyssize - 1;
    if (sumold % 5 != 0)
      sumnew = 5;
    break;
  case 3:
    yl1++;
    act1 = 4;
    if (yl1 >= Ysyssize)
      yl1 = 0;
    if (sumold % 7 != 0)
      sumnew = 7;
    break;
  case 4:
    zl1--;
    act1 = 5;
    if (zl1 < 0)
      zl1 = Zsyssize - 1;
    if (sumold % 11 != 0)
      sumnew = 11;
    break;
  case 5:
    zl1++;
    act1 = 6;
    if (zl1 >= Zsyssize)
      zl1 = 0;
    if (sumold % 13 != 0)
      sumnew = 13;
    break;
  default:
    break;
  }

  /* Return the new location */

  *xloc = xl1;
  *yloc = yl1;
  *zloc = zl1;
  *act = act1;

  /***
   *    Sumnew returns a prime number indicating
   *    that a specific direction has been chosen
   ***/

  return (sumnew);
}

/***
 *    getporenv
 *
 *    Return id of majority of neighboring saturated
 *    pore pixels for pixel located at (xck,yck,zck).
 *    Possible return values are POROSITY and CRACKP
 *
 *     Arguments:    Int location coordinates (xck,yck,zck)
 *
 *     Returns:    Int pore id (either POROSITY or CRACKP)
 *
 *    Calls:        No other routines
 *
 *    Called by:    all the move routines (movecsh, etc.)
 *
 *    (Function implement 24 May 2004)
 ***/
int getporenv(int xck, int yck, int zck) {
  int ixe, iye, ize, x2, y2, z2, check;
  int porecnt = 0, crackcnt = 0;

  /***
   *    Examine all pixels in a 3*3*3 box
   *    centered at (xck,yck,zck) except for
   *    the central pixel
   ***/

  for (ixe = (-1); ixe <= 1; ixe++) {
    x2 = xck + ixe;
    for (iye = (-1); iye <= 1; iye++) {
      y2 = yck + iye;
      for (ize = (-1); ize <= 1; ize++) {

        if ((ixe != 0) || (iye != 0) || (ize != 0)) {
          z2 = zck + ize;

          /* adjust to maintain periodic boundaries */

          x2 += checkbc(x2, Xsyssize);
          y2 += checkbc(y2, Ysyssize);
          z2 += checkbc(z2, Zsyssize);

          check = Mic[x2][y2][z2];

          if (check == POROSITY)
            porecnt++;
          if (check == CRACKP)
            crackcnt++;
        }
      }
    }
  }

  if (porecnt >= crackcnt) {
    return (POROSITY);
  } else {
    return (CRACKP);
  }
}

/***
 *    edgecnt
 *
 *    Return count of number of neighboring pixels for pixel
 *    (xck,yck,zck) which are NOT phase ph1, ph2, or ph3
 *    which are input as parameters
 *
 *     Arguments:    Int location coordinates (xck,yck,zck)
 *                 Int Phase IDs ph1 ph2 ph3
 *
 *     Returns:    Int count of neighbor pixels that are not
 *                 type ph1, ph2, ph3
 *
 *    Calls:        No other routines
 *
 *    Called by:    extettr, extfh3, extafm, extpozz,
 *                extc3ah5, extfriedel, extstrat
 ***/
int edgecnt(int xck, int yck, int zck, int ph1, int ph2, int ph3) {
  int ixe, iye, ize, edgeback, x2, y2, z2, check;

  /***
   *    Counter for number of neighboring pixels
   *    which are not ph1, ph2, or ph3
   ***/

  edgeback = 0;

  /***
   *    Examine all pixels in a 3*3*3 box
   *    centered at (xck,yck,zck) except for
   *    the central pixel
   ***/

  for (ixe = (-1); ixe <= 1; ixe++) {
    x2 = xck + ixe;
    for (iye = (-1); iye <= 1; iye++) {
      y2 = yck + iye;
      for (ize = (-1); ize <= 1; ize++) {

        if ((ixe != 0) || (iye != 0) || (ize != 0)) {
          z2 = zck + ize;

          /* adjust to maintain periodic boundaries */

          x2 += checkbc(x2, Xsyssize);
          y2 += checkbc(y2, Ysyssize);
          z2 += checkbc(z2, Zsyssize);

          check = Mic[x2][y2][z2];

          if ((check != ph1) && (check != ph2) && (check != ph3)) {

            edgeback++;
          }
        }
      }
    }
  }

  /***
   *    Return number of neighboring pixels which
   *    are not ph1, ph2, or ph3
   ***/

  return (edgeback);
}

/***
 *    extcsh
 *
 *    Add extra CSH when diffusing CSH reacts
 *
 *     Arguments:    int x,y,z position of current pixel
 *                 pointer to id of saturated porosity locally
 *
 *     Returns:    Nothing
 *
 *    Calls:        edgecnt
 *
 *    Called by:    movecsh
 ***/
void extcsh(int xpres, int ypres, int zpres, int *poreid) {
  int numnear1, numnear2, xchr, ychr, zchr, fchr, check, msface, pval;
  int tries;

  fchr = tries = 0;

  /***
   *    Locate CSH at random location in pore space
   *    in contact with at least another CSH or C3S
   *    or C2S
   ***/

  if (*poreid < 0) {
    if (Cyccnt > Crackcycle) {
      *poreid = getporenv(xpres, ypres, zpres);
    } else {
      *poreid = (int)(POROSITY);
    }
  }
  pval = (int)(*poreid);

  while (!fchr) {

    tries++;

    /* Generate a random location in the 3-D system */

    xchr = (int)((float)Xsyssize * ran1(Seed));
    ychr = (int)((float)Ysyssize * ran1(Seed));
    zchr = (int)((float)Zsyssize * ran1(Seed));
    if (xchr >= Xsyssize)
      xchr = 0;
    if (ychr >= Ysyssize)
      ychr = 0;
    if (zchr >= Zsyssize)
      zchr = 0;

    check = Mic[xchr][ychr][zchr];

    /* If location is porosity of proper type, locate the CSH there */

    if (check == pval) {

      numnear1 = edgecnt(xchr, ychr, zchr, CSH, C3S, C2S);
      numnear2 = edgecnt(xchr, ychr, zchr, POZZCSH, SFUME, CACO3);

      /***
       *    Be sure that at least one neighboring pixel
       *    is C2S, C3S, or diffusing CSH
       ***/

      if ((numnear1 < 26) || (numnear2 < 26) || (tries > MAXTRIES)) {
        Mic[xchr][ychr][zchr] = CSH;
        Count[CSH]++;
        Count[pval]--;
        Cshage[xchr][ychr][zchr] = Cyccnt;
        if (Cshgeom == PLATE) {
          msface = (int)(3.0 * ran1(Seed) + 1.0);
          if (msface > 3)
            msface = 1;
          Faces[xchr][ychr][zchr] = msface;
          Ncshplateinit++;
        }
        fchr = 1;
      }
    }
  }

  return;
}

/***
 *    movecsh
 *
 *    Move a diffusing CSH pixel
 *
 *     Arguments:    Int current location coordinates xcur,ycur,zcur
 *                 Int flag indicating if this is the final diffusion step
 *                Int cycorig
 *                Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int flag indicating action taken
 *                     (reaction or diffusion/no movement)
 *
 *    Calls:        moveone,extcsh
 *
 *    Called by:    hydrate
 ***/
int movecsh(int xcur, int ycur, int zcur, int finalstep, int cycorig) {
  int xnew, ynew, znew, action, sumback, sumin, check, poreid;
  int msface, mstest, mstest2;
  float prcsh, prcsh1, prcsh2, prtest;
  float pcshcrit, pchcrit, pc3acrit;

  mstest = mstest2 = 0;
  action = 0;
  poreid = -1;

  /* Store current location of species */

  xnew = xcur;
  ynew = ycur;
  znew = zcur;
  sumin = 1;

  sumback = moveone(&xnew, &ynew, &znew, &action, sumin);

  if (Cshgeom == PLATE) {
    /* Determine eligible faces based on direction of move */
    if (xnew != xcur) {
      mstest = 1;
      mstest2 = 2;
    }
    if (ynew != ycur) {
      mstest = 2;
      mstest2 = 3;
    }
    if (znew != zcur) {
      mstest = 3;
      mstest2 = 1;
    }
  }

  if (!action) {
    fprintf(stderr, "\nERROR in movecsh: Value of action is %d", action);
    fflush(stderr);
  }

  check = Mic[xnew][ynew][znew];

  /***
   *    If new location is solid CSH, and plate growth is
   *    favorable, then convert diffusing
   *    CSH species to solid CSH.  Also allow precipitation
   *    on pozzolanic CSH and slag CSH
   ***/

  prcsh = ran1(Seed);

  /***
   *    pcshcrit changed to 0.1 from 0.001 on 2 Apr 2003
   *    pchcrit changed from 0.1 to 0.01 on 1 March 2006
   ***/

  pcshcrit = 0.001;
  pc3acrit = 0.2;
  pchcrit = 0.01;

  if ((check == CSH) &&
      ((Cshgeom == RANDOM) || (Faces[xnew][ynew][znew] == 0) ||
       (Faces[xnew][ynew][znew] == mstest) ||
       (Faces[xnew][ynew][znew] == mstest2))) {

    /* Decrement count of diffusing CSH species ... */

    Count[DIFFCSH]--;

    /* ... and increment count of solid CSH if needed */

    prtest = Molarvcsh[Cyccnt] / Molarvcsh[cycorig];
    prcsh1 = ran1(Seed);
    if (prcsh1 <= prtest) {
      Mic[xcur][ycur][zcur] = CSH;
      if (Cshgeom == PLATE) {
        Faces[xcur][ycur][zcur] = Faces[xnew][ynew][znew];
        Ncshplategrow++;
      }
      Cshage[xcur][ycur][zcur] = Cyccnt;
      Count[CSH]++;
    } else {

      /***
       *    If necessary, find majority type of saturated porosity
       *    (either CRACKP or POROSITY)
       *    (24 May 2004)
       ****/

      poreid = POROSITY;
      if (Icyc > Crackcycle)
        poreid = getporenv(xcur, ycur, zcur);
      Mic[xcur][ycur][zcur] = poreid;
      Count[poreid]++;
    }

    /***
     *    May need extra solid CSH if temperature
     *    goes down with time
     ***/

    if (prtest > 1.0) {
      prcsh2 = ran1(Seed);
      if (prcsh2 < (prtest - 1.0)) {
        extcsh(xcur, ycur, zcur, &poreid);
      }
    }

    action = 0;

  } else if ((check == SLAGCSH) || (check == POZZCSH) || (finalstep) ||
             (((check == C3S) || (check == C2S)) && (prcsh < pcshcrit)) ||
             (((check == C3A) || (check == OC3A) || (check == C4AF)) &&
              (prcsh < pc3acrit)) ||
             ((check == CH) && (prcsh < pchcrit)) || (check == CACO3)) {

    /* Decrement count of diffusing CSH species ... */

    Count[DIFFCSH]--;

    /* ... and increment count of solid CSH if needed */

    prtest = Molarvcsh[Cyccnt] / Molarvcsh[cycorig];
    prcsh1 = ran1(Seed);
    if (prcsh1 <= prtest) {
      Mic[xcur][ycur][zcur] = CSH;
      Cshage[xcur][ycur][zcur] = Cyccnt;
      if (Cshgeom == PLATE) {
        msface = (int)(2.0 * ran1(Seed) + 1.0);
        if (msface > 2)
          msface = 1;
        if (msface == 1) {
          Faces[xcur][ycur][zcur] = mstest;
        } else {
          Faces[xcur][ycur][zcur] = mstest2;
        }
        Ncshplateinit++;
      }
      Count[CSH]++;

    } else {

      /***
       *    If necessary, find majority type of saturated porosity
       *    (either CRACKP or POROSITY)
       *    (24 May 2004)
       ****/

      poreid = POROSITY;
      if (Cyccnt > Crackcycle)
        poreid = getporenv(xcur, ycur, zcur);
      Mic[xcur][ycur][zcur] = poreid;
      Count[poreid]++;
    }

    /***
     *    May need extra solid CSH if temperature
     *    goes down with time
     ***/

    if (prtest > 1.0) {
      prcsh2 = ran1(Seed);
      if (prcsh2 < (prtest - 1.0)) {
        extcsh(xcur, ycur, zcur, &poreid);
      }
    }

    action = 0;

  } else if (check == SFUME) {

    /***
     *    Check for pozzolanic reaction with silica fume
     *
     *    Molar reaction postulate:
     *
     *    CSH + 0.545 S -> 1.545 (POZZCSH)
     *
     *    This works out because Ca/Si = 1.7 for CSH and
     *    Ca/Si = 1.1 for POZZCSH.
     *
     *    On a volume basis, 1 unit of CSH can react
     *    with 0.136 units of SFUME to make 1.46 units
     *    of POZZCSH
     ***/

    /* Decrement count of diffusing CSH species ... */

    Count[DIFFCSH]--;
    Mic[xcur][ycur][zcur] = POZZCSH;
    Count[POZZCSH]++;

    /* Check to see if we need to dissolve the SFUME */

    prcsh1 = ran1(Seed);
    if (prcsh1 <= 0.136) {
      /* YES, dissolve the silica fume */
      Mic[xnew][ynew][znew] = POZZCSH;
      Count[POZZCSH]++;
      Count[SFUME]--;
      Nsilica_rx++;
      prcsh1 = ran1(Seed);
      if (prcsh1 <= (0.46 - 0.136)) {
        extpozz(xcur, ycur, zcur, &poreid);
      }
    } else {
      prcsh1 = ran1(Seed);
      if (prcsh1 <= 0.46) {
        extpozz(xcur, ycur, zcur, &poreid);
      }
    }

    action = 0;
  }

  if (action != 0) {

    /***
     *    If diffusion step is possible, perform it.  Allow
     *    diffusion into either POROSITY or CRACKP (i.e.
     *    water in a saturated crack formed during hydration)
     *    (24 May 2004)
     ****/

    if (check == POROSITY || check == CRACKP) {
      Mic[xcur][ycur][zcur] = check;
      Mic[xnew][ynew][znew] = DIFFCSH;
    } else {

      /***
       *    Indicate that diffusing CSH species remained
       *    at original location
       ***/

      action = 7;
    }
  }

  return (action); /* 0 if something happened, 7 otherwise */
}

/***
 *    extfh3
 *
 *    Add extra FH3 when gypsum, hemihydrate, anhydrite, CAS2,
 *    or CaCl2 reacts with C4AF at location (xpres, ypres, zpres)
 *
 *     Arguments:    Int coordinates xpres, ypres, zpres
 *                 Int pointer to id of local saturated porosity
 *
 *     Returns:    Nothing
 *
 *    Calls:        moveone,edgecnt
 *
 *    Called by:    movegyp,moveettr,movecas2,movehem,moveanh,movecacl2
 ***/
void extfh3(int xpres, int ypres, int zpres, int *poreid) {
  int multf, numnear, sump, xchr, ychr, zchr, check, fchr, i1, newact, pval;
  int tries;

  /***
   *    First try 6 neighboring locations until
   *        a) successful,
   *        b) all 6 sites are tried and full, or
   *        c) 500 tries are made
   ***/

  fchr = 0;
  sump = 1;

  /* 30030 is product of first six prime numbers */

  for (i1 = 1; ((i1 <= 500) && (!fchr) && (sump != 30030)); i1++) {

    /* Choose a nearest neighbor at random */

    xchr = xpres;
    ychr = ypres;
    zchr = zpres;
    newact = 0;

    multf = moveone(&xchr, &ychr, &zchr, &newact, sump);

    if (!newact) {
      fprintf(stderr, "\nERROR in extfh3: Value of newact is %d", newact);
      fflush(stderr);
    }

    check = Mic[xchr][ychr][zchr];

    /***
     *    If neighbor is POROSITY or CRACKP, then locate the
     *    FH3 there, because it is local growth
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xchr][ychr][zchr] = FH3;
      Count[FH3]++;
      Count[check]--;
      fchr = 1;
    } else {
      sump *= multf;
    }
  }

  /***
   *    If no neighbor available, locate FH3 at random
   *    location in pore space in contact with at least
   *    one FH3.  Because growth is non-local here, we
   *    only allow growth into the same kind of saturated
   *    porosity as was locally available at the reaction site
   *    (24 May 2004)
   ***/

  tries = 0;
  if (*poreid < 0) {
    if (Cyccnt > Crackcycle) {
      *poreid = getporenv(xpres, ypres, zpres);
    } else {
      *poreid = (int)(POROSITY);
    }
  }
  pval = (int)(*poreid);

  while (!fchr) {

    tries++;

    /* Generate a random location in the 3-D system */

    xchr = (int)((float)Xsyssize * ran1(Seed));
    ychr = (int)((float)Ysyssize * ran1(Seed));
    zchr = (int)((float)Zsyssize * ran1(Seed));

    if (xchr >= Xsyssize)
      xchr = 0;
    if (ychr >= Ysyssize)
      ychr = 0;
    if (zchr >= Zsyssize)
      zchr = 0;

    check = Mic[xchr][ychr][zchr];

    /***
     *    If location is porosity of the majority type at the location
     *    of the original growth (POROSITY or CRACKP),
     *    locate the FH3 there, because here growth is non-local
     *    (24 May 2004)
     ***/

    if (check == pval) {

      numnear = edgecnt(xchr, ychr, zchr, FH3, FH3, DIFFFH3);

      /***
       *    Be sure that at least one neighboring
       *    pixel is FH3 or diffusing FH3
       ***/

      if ((numnear < 26) || (tries > MAXTRIES)) {
        Mic[xchr][ychr][zchr] = FH3;
        Count[FH3]++;
        Count[pval]--;
        fchr = 1;
      }
    }
  }

  return;
}

/***
 *    extettr
 *
 *    Add extra ettringite when gypsum, hemihydrate, or anhydrite
 *    reacts with aluminates at location (xpres, ypres, zpres)
 *
 *    Add the ettringite in a manner consistent with an acicular
 *    growth form
 *
 *     Arguments:    Int coordinates xpres, ypres, zpres
 *                 Int type of ettringite
 *                     etype = 0 ---> primary ettringite
 *                     etype = 1 ---> iron-rich stable ettringite
 *                 int id of saturated porosity where original
 *                 reaction happened (24 May 2004)
 *
 *     Returns:    Int flag indicating action taken
 *
 *    Calls:        moveone, edgecnt
 *
 *    Called by:    movegyp, movehem, moveanh, movec3a
 ***/
int extettr(int xpres, int ypres, int zpres, int etype, int *poreid) {
  int check, newact, multf, numnear, sump, xchr, ychr, zchr, fchr, i1;
  int numalum, numsil, pval;
  int tries;
  float pneigh, ptest;

  /***
   *    First try neighboring locations until
   *        a) successful, or
   *        b) 1000 tries are made
   ***/

  fchr = 0;
  sump = 1;

  /***
   *    Note that 30030 is the product of the first six prime numbers,
   *    indicating that all six sites have been tried
   ***/

  for (i1 = 1; ((i1 <= 1000) && (!fchr)); i1++) {

    /***
     *    Determine location of neighbor
     *    (using periodic boundaries)
     ***/

    xchr = xpres;
    ychr = ypres;
    zchr = zpres;

    newact = 0;
    multf = moveone(&xchr, &ychr, &zchr, &newact, sump);

    if (!newact) {
      fprintf(stderr, "\nERROR in extettr: Value of newact is %d", newact);
      fflush(stderr);
    }

    check = Mic[xchr][ychr][zchr];

    /***
     *    If neighbor is porosity of any saturated kind,
     *    and conditions are favorable, based on number
     *    of neighboring ettringite, C3A, or C4AF pixels,
     *    then locate    the ettringite there.  We allow
     *    growth into either POROSITY or CRACKP because
     *    it is local growth
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {

      /* Be sure ettringite doesn't touch C3S */

      numsil = edgecnt(xchr, ychr, zchr, C3S, C2S, C3S);
      numsil = 26 - numsil;

      if (etype == 0) {
        numnear = edgecnt(xchr, ychr, zchr, ETTR, ETTR, ETTR);
        numalum = edgecnt(xchr, ychr, zchr, C3A, OC3A, C3A);
        numalum = 26 - numalum;
      } else {
        numnear = edgecnt(xchr, ychr, zchr, ETTRC4AF, ETTRC4AF, ETTRC4AF);
        numalum = edgecnt(xchr, ychr, zchr, C4AF, C4AF, C4AF);
        numalum = 26 - numalum;
      }

      pneigh = (float)(numnear + 1) / 26.0;
      pneigh *= pneigh;

      if (numalum <= 1)
        pneigh = 0.0;
      if (numalum >= 2)
        pneigh += 0.5;
      if (numalum >= 3)
        pneigh += 0.25;
      if (numalum >= 5)
        pneigh += 0.25;

      ptest = ran1(Seed);
      if (numsil < 1) {
        if (pneigh >= ptest) {
          if (etype == 0) {
            Mic[xchr][ychr][zchr] = ETTR;
            Count[ETTR]++;
          } else {
            Mic[xchr][ychr][zchr] = ETTRC4AF;
            Count[ETTRC4AF]++;
          }
          fchr = 1;
          Count[check]--;
        }
      }
    }
  }

  /***
   *    If no neighbor available, locate ettringite
   *    at random location in pore space in contact
   *    with at least another ettringite or aluminate
   *    surface.  Here because the growth is non-local,
   *    we only allow it into saturated porosity of the
   *    same type as that where the original reaction
   *    occured
   *    (24 May 2004)
   ***/

  tries = 0;
  if (*poreid < 0) {
    if (Cyccnt > Crackcycle) {
      *poreid = getporenv(xpres, ypres, zpres);
    } else {
      *poreid = (int)(POROSITY);
    }
  }
  pval = (int)(*poreid);

  while (!fchr) {

    tries++;
    newact = 7;

    /* Generate a random location in the 3-D system */

    xchr = (int)((float)Xsyssize * ran1(Seed));
    ychr = (int)((float)Ysyssize * ran1(Seed));
    zchr = (int)((float)Zsyssize * ran1(Seed));

    if (xchr >= Xsyssize)
      xchr = 0;
    if (ychr >= Ysyssize)
      ychr = 0;
    if (zchr >= Zsyssize)
      zchr = 0;

    check = Mic[xchr][ychr][zchr];

    /* If location is porosity, locate the ettringite there */

    if (check == pval) {

      numsil = edgecnt(xchr, ychr, zchr, C3S, C2S, C3S);
      numsil = 26 - numsil;
      if (etype == 0) {
        numnear = edgecnt(xchr, ychr, zchr, ETTR, C3A, C4AF);
        if (numnear == 26)
          numnear = edgecnt(xchr, ychr, zchr, OC3A, OC3A, OC3A);
      } else {
        numnear = edgecnt(xchr, ychr, zchr, ETTRC4AF, C3A, C4AF);
        if (numnear == 26)
          numnear = edgecnt(xchr, ychr, zchr, OC3A, OC3A, OC3A);
      }

      /***
       *    Be sure that at least one neighboring pixel
       *    is either ettringite or aluminate clinker
       ***/

      if ((tries > MAXTRIES) || ((numnear < 26) && (numsil < 1))) {
        if (etype == 0) {
          Mic[xchr][ychr][zchr] = ETTR;
          Count[ETTR]++;
        } else {
          Mic[xchr][ychr][zchr] = ETTRC4AF;
          Count[ETTRC4AF]++;
        }

        fchr = 1;
        Count[pval]--;
      }
    }
  }

  return (newact); /* 7 if nothing was done */
}

/***
 *    extch
 *
 *    Add extra CH when gypsum, hemihydrate, or anhydrite, CaCl2,
 *    or diffusing CAS2 reacts with C4AF
 *
 *     Arguments:    int poreid is the saturated porosity type at the
 *                 location of the original reaction (24 May 2004)
 *
 *     Returns:    Nothing
 *
 *    Calls:        edgecnt
 *
 *    Called by:    movegyp,movehem,moveanh,moveettr,movecas2,movecacl2
 ***/
void extch(int xpres, int ypres, int zpres, int *poreid) {
  int numnear, xchr, ychr, zchr, fchr, check, pval;
  int tries;

  fchr = tries = 0;

  /***
   *    Locate CH at random location in pore space
   *    in contact with at least one other CH
   ***/

  if (*poreid < 0) {
    if (Cyccnt > Crackcycle) {
      *poreid = getporenv(xpres, ypres, zpres);
    } else {
      *poreid = (int)(POROSITY);
    }
  }
  pval = (int)(*poreid);

  while (!fchr) {

    tries++;

    /* Generate a random location in the 3-D system */

    xchr = (int)((float)Xsyssize * ran1(Seed));
    ychr = (int)((float)Ysyssize * ran1(Seed));
    zchr = (int)((float)Zsyssize * ran1(Seed));

    if (xchr >= Xsyssize)
      xchr = 0;
    if (ychr >= Ysyssize)
      ychr = 0;
    if (zchr >= Zsyssize)
      zchr = 0;

    check = Mic[xchr][ychr][zchr];

    /***
     *    If location is porosity of the same type as that
     *    found at the original reaction location,
     *    locate the CH there.  We do this because the
     *    growth is non-local
     ***/

    if (check == pval) {

      numnear = edgecnt(xchr, ychr, zchr, CH, DIFFCH, CH);

      /***
       *    Be sure that at least one neighboring pixel
       *    is CH or diffusing CH
       ***/

      if ((numnear < 26) || (tries > MAXTRIES)) {
        Mic[xchr][ychr][zchr] = CH;
        Count[CH]++;
        Count[pval]--;
        fchr = 1;
      }
    }
  }

  return;
}

/***
 *    extgyps
 *
 *    Add extra secondary gypsum when hemihydrate or anhydrite hydrates
 *    or diffusing CAS2 reacts with C4AF
 *
 *     Arguments:    Int coordinates of present location xpres,ypres,zpres
 *                 int id of saturated porosity where original reaction
 *                 occured (24 May 2004)
 *
 *     Returns:    Nothing
 *
 *    Calls:        moveone,edgecnt
 *
 *    Called by:    movehem,moveanh
 ***/
void extgyps(int xpres, int ypres, int zpres, int *poreid) {
  int multf, numnear, sump, xchr, ychr, zchr, check, fchr, i1, newact, pval;
  int tries;

  /***
   *    First try 6 neighboring locations until
   *        a) successful,
   *        b) all 6 sites are tried and full, or
   *        c) 500 tries are made
   *
   *    Note that 30300 is the product of the first six prime
   *    numbers, indicating that all nearest neighbors have
   *    been examined
   ***/

  fchr = 0;
  sump = 1;
  for (i1 = 1; ((i1 <= 500) && (!fchr) && (sump != 30030)); i1++) {

    /* Choose a neighbor at random */

    xchr = xpres;
    ychr = ypres;
    zchr = zpres;
    newact = 0;
    multf = moveone(&xchr, &ychr, &zchr, &newact, sump);

    if (!newact) {
      fprintf(stderr, "\nERROR in extgyps: Value of newact is %d", newact);
      fflush(stdout);
    }

    check = Mic[xchr][ychr][zchr];

    /***
     *    If neighbor is porosity then locate
     *    the GYPSUMS there. Either POROSITY or CRACKP
     *    is allowed because growth is local
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xchr][ychr][zchr] = GYPSUMS;
      Count[GYPSUMS]++;
      Count[check]--;
      fchr = 1;
    } else {
      sump *= multf;
    }
  }

  /***
   *    If no neighbor available, locate GYPSUMS
   *    at random location in pore space in contact
   *    with at least one other GYPSUMS.  Here we only
   *    allow growth into saturated porosity of the
   *    type found at the location of the original
   *    reaction because growth is non-local.
   *    (24 May 2004)
   ***/

  tries = 0;
  if (*poreid < 0) {
    if (Cyccnt > Crackcycle) {
      *poreid = getporenv(xpres, ypres, zpres);
    } else {
      *poreid = (int)(POROSITY);
    }
  }
  pval = (int)(*poreid);
  while (!fchr) {

    tries++;

    /* Generate a random location in the 3-D system */

    xchr = (int)((float)Xsyssize * ran1(Seed));
    ychr = (int)((float)Ysyssize * ran1(Seed));
    zchr = (int)((float)Zsyssize * ran1(Seed));

    if (xchr >= Xsyssize)
      xchr = 0;
    if (ychr >= Ysyssize)
      ychr = 0;
    if (zchr >= Zsyssize)
      zchr = 0;

    check = Mic[xchr][ychr][zchr];

    /* If location is porosity, locate the GYPSUMS there */

    if (check == pval) {
      numnear = edgecnt(xchr, ychr, zchr, HEMIHYD, GYPSUMS, ANHYDRITE);

      /***
       *    Be sure that at least one neighboring pixel
       *    is Gypsum in some form, or that we have run
       *    out of tries
       ***/

      if ((numnear < 26) || (tries > MAXTRIES)) {
        Mic[xchr][ychr][zchr] = GYPSUMS;
        Count[GYPSUMS]++;
        Count[pval]--;
        fchr = 1;
      }
    }
  }

  return;
}

/***
 *    moveanh
 *
 *     Move a diffusing ANHYDRITE pixel
 *
 *     Arguments:    Int coordinates of present location xcur,ycur,zcur
 *                 Int flag indicating whether final diffusion step
 *                 Float nucprgyp
 *                 Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int return flag indicating action taken
 *                     (reaction or diffusion/no movement)
 *
 *    Calls:        moveone,extettr,extfh3,extgyps,extch
 *
 *    Called by:    hydrate
 ***/
int moveanh(int xcur, int ycur, int zcur, int finalstep, float nucprgyp) {
  int xnew, ynew, znew, action, sumback, sumin, check, poreid;
  int nexp, iexp, xexp, yexp, zexp, newact, ettrtype;
  float pgen, pexp, pext, p2diff;

  action = check = 0;
  poreid = -1;

  /* First check for nucleation */

  pgen = ran1(Seed);
  p2diff = ran1(Seed);

  if ((nucprgyp >= pgen) || (finalstep)) {

    /* Nucleate secondary gypsum at this spot */

    action = 0;
    Mic[xcur][ycur][zcur] = GYPSUMS;
    Count[DIFFANH]--;
    Count[GYPSUMS]++;
    pexp = ran1(Seed);
    if (pexp < 0.4) {
      extgyps(xcur, ycur, zcur, &poreid);
    }

  } else {

    /* Store current location of species */

    xnew = xcur;
    ynew = ycur;
    znew = zcur;
    sumin = 1;
    sumback = moveone(&xnew, &ynew, &znew, &action, sumin);

    if (!action) {
      fprintf(stderr, "\nERROR in moveanh: Value of action is %d", action);
      fflush(stderr);
    }

    check = Mic[xnew][ynew][znew];

    /***
     *    If new location is solid GYPSUM(S) or
     *    diffusing GYPSUM, then convert diffusing
     *    ANHYDRITE species to solid GYPSUM
     ***/

    if ((check == GYPSUM) || (check == GYPSUMS) || (check == DIFFGYP)) {

      Mic[xcur][ycur][zcur] = GYPSUMS;

      /***
       *    Decrement count of diffusing ANHYDRITE species
       *    and increment count of solid GYPSUMS
       ***/

      Count[DIFFANH]--;
      Count[GYPSUMS]++;
      action = 0;

      /* Add extra gypsum as necessary */

      pexp = ran1(Seed);
      if (pexp < 0.4) {
        extgyps(xnew, ynew, znew, &poreid);
      }

      /***
       *    If new location is C3A/OC3A or diffusing C3A,
       *    execute conversion to ettringite (including
       *    necessary volumetric expansion)
       ***/

    } else if ((((check == C3A) || (check == OC3A)) &&
                (p2diff < SOLIDC3AGYP)) ||
               ((check == DIFFC3A) && (p2diff < C3AGYP)) ||
               ((check == DIFFC4A) && (p2diff < C3AGYP))) {

      /* Convert diffusing gypsum to an ettringite pixel */

      ettrtype = 0;
      Mic[xcur][ycur][zcur] = ETTR;
      if (check == DIFFC4A) {

        /***
         *    Collided with an Fe-containing C4AF ant.  Make
         *    iron-rich stable ettringite instead of primary
         ***/

        ettrtype = 1;
        Mic[xcur][ycur][zcur] = ETTRC4AF;
      }

      action = 0;
      Count[DIFFANH]--;
      Count[check]--;

      /***
       *    Determine if C3A should be converted to ettringite.
       *
       *    1 unit of hemihydrate requires 0.569 units of C3A
       *    and should form 4.6935 units of ettringite
       *
       *    We already formed one pixel of ettringite immediately
       *    above, so we need nexp = 3 more of them
       ***/

      pexp = ran1(Seed);
      nexp = 3;
      if (pexp <= 0.569) {
        if (ettrtype == 0) {
          Mic[xnew][ynew][znew] = ETTR;
          Count[ETTR]++;
        } else {
          Mic[xnew][ynew][znew] = ETTRC4AF;
          Count[ETTRC4AF]++;
        }

        nexp--;

      } else {

        /***
         *    Maybe someday, use a new FIXEDC3A here
         *    so it won't dissolve later
         ***/

        if (check == C3A || check == OC3A) {
          Mic[xnew][ynew][znew] = check;
          Count[check]++;
        } else {
          if (ettrtype == 0) {
            Count[DIFFC3A]++;
            Mic[xnew][ynew][znew] = DIFFC3A;
          } else {
            Count[DIFFC4A]++;
            Mic[xnew][ynew][znew] = DIFFC4A;
          }
        }
      }

      /***
       *    Create extra ettringite pixels to maintain
       *    volume stoichiometry
       *
       *    xexp, yexp, and zexp hold coordinates of most
       *    recently added ettringite species as we attempt
       *    to grow an acicular ettringite crystal shape
       ***/

      xexp = xcur;
      yexp = ycur;
      zexp = zcur;

      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extettr(xexp, yexp, zexp, ettrtype, &poreid);

        /* Update xexp, yexp and zexp as needed */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /***
       *    Added a total of 4 ettringite pixels already.
       *    Probabilistic-based expansion for last
       *    partial pixel
       ***/

      pexp = ran1(Seed);
      if (pexp <= 0.6935) {
        newact = extettr(xexp, yexp, zexp, ettrtype, &poreid);
      }
    }

    /***
     *    If new location is C4AF, execute conversion to
     *    ettringite (including necessary volumetric
     *    expansion)
     ***/

    if ((check == C4AF) && (p2diff < SOLIDC4AFGYP)) {
      Mic[xcur][ycur][zcur] = ETTRC4AF;
      Count[ETTRC4AF]++;
      Count[DIFFANH]--;

      /***
       *    Determine if C4AF should be converted to ettringite
       *
       *    1 unit of gypsum requires 0.8174 units of C4AF
       *    and should form 4.6935 units of ettringite.  Already
       *    made one pixel immediately above, so we need
       *    nexp = 3 more complete ones and then 0.6935 more
       *    on top of that.
       ***/

      nexp = 3;
      pexp = ran1(Seed);
      if (pexp <= 0.8174) {

        Mic[xnew][ynew][znew] = ETTRC4AF;
        Count[ETTRC4AF]++;
        Count[C4AF]--;
        nexp--;

        pext = ran1(Seed);

        /* Probabilistic addition of extra CH */

        if (pext < 0.2584) {
          extch(xcur, ycur, zcur, &poreid);
        }

        pext = ran1(Seed);

        /* Probabilistic addition of extra FH3 */

        if (pext < 0.5453) {
          extfh3(xnew, ynew, znew, &poreid);
        }

      } else {

        /***
         *    Maybe someday, use a new FIXEDC4AF here
         *    so it won't dissolve later
         ***/

        Mic[xnew][ynew][znew] = C4AF;
      }

      /***
       *    Create extra ettringite pixels to maintain
       *    volume stoichiometry
       *
       *    xexp, yexp and zexp hold coordinates of most
       *    recently added ettringite species as we
       *    attempt to grow an acicular crystal shape
       ***/

      xexp = xcur;
      yexp = ycur;
      zexp = zcur;
      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extettr(xexp, yexp, zexp, 1, &poreid);

        /* Update xexp, yexp and zexp as needed */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /***
       *    Probabilistic-based expansion for last
       *    ettringite pixel
       ***/

      pexp = ran1(Seed);
      if (pexp <= 0.6935) {
        newact = extettr(xexp, yexp, zexp, 1, &poreid);
      }
      action = 0;
    }
  }

  if (action != 0) {

    /***
     *    If diffusion step is possible, perform it
     *    Allow diffusion into either POROSITY or
     *    CRACKP (i.e. saturated cracks formed during
     *    the hydration process)
     *    (24 May 2004)
     ****/

    if (check == POROSITY || check == CRACKP) {

      Mic[xcur][ycur][zcur] = check;
      Mic[xnew][ynew][znew] = DIFFANH;

    } else {

      /***
       *    Indicate that diffusing ANHYDRITE species
       *    remained at original location
       ***/

      action = 7;
    }
  }

  return (action); /* 7 if no action taken */
}

/***
 *    movehem
 *
 *     Move a diffusing HEMIHYDRATE pixel
 *
 *     Arguments:    Int coordinates of present location xcur,ycur,zcur
 *                 Int flag indicating whether final diffusion step
 *                 Float nucprgyp is nucleation probability
 *                 Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int return flag indicating action taken
 *                     (reaction or diffusion/no movement)
 *
 *    Calls:        moveone,extettr,extch,extfh3
 *
 *    Called by:    hydrate
 ***/
int movehem(int xcur, int ycur, int zcur, int finalstep, float nucprgyp) {
  int xnew, ynew, znew, action, sumback, sumin, check, poreid;
  int nexp, iexp, xexp, yexp, zexp, newact, ettrtype;
  float pgen, pexp, pext, p2diff;

  action = check = 0;
  poreid = -1;

  /* First check for nucleation */

  pgen = ran1(Seed);
  p2diff = ran1(Seed);

  if ((nucprgyp >= pgen) || (finalstep)) {

    /* Nucleate GYPSUMS at this location */

    action = 0;
    Mic[xcur][ycur][zcur] = GYPSUMS;
    Count[DIFFHEM]--;
    Count[GYPSUMS]++;

    /* Add extra gypsum as necessary */

    pexp = ran1(Seed);
    if (pexp < 0.4) {
      extgyps(xcur, ycur, zcur, &poreid);
    }
  } else {

    /* Store current location of species */

    xnew = xcur;
    ynew = ycur;
    znew = zcur;
    sumin = 1;
    sumback = moveone(&xnew, &ynew, &znew, &action, sumin);

    if (!action) {
      fprintf(stderr, "\nERROR in movehem: Value of action is %d", action);
      fflush(stderr);
    }

    check = Mic[xnew][ynew][znew];

    /***
     *    If new location is solid GYPSUM(S) or
     *    diffusing GYPSUM, then convert diffusing
     *    HEMIHYDRATE species to solid GYPSUM
     ***/

    if ((check == GYPSUM) || (check == GYPSUMS) || (check == DIFFGYP)) {

      Mic[xcur][ycur][zcur] = GYPSUMS;

      /***
       *    Decrement count of diffusing HEMIHYDRATE species
       *    and increment count of solid GYPSUMS
       ***/

      Count[DIFFHEM]--;
      Count[GYPSUMS]++;
      action = 0;

      /* Add extra gypsum as necessary */

      pexp = ran1(Seed);
      if (pexp < 0.4) {
        extgyps(xnew, ynew, znew, &poreid);
      }

      /***
       *    If new location is C3A or diffusing C3A,
       *    execute conversion to ettringite (including
       *    necessary volumetric expansion)
       ***/

    } else if ((((check == C3A) || (check == OC3A)) &&
                (p2diff < SOLIDC3AGYP)) ||
               ((check == DIFFC3A) && (p2diff < C3AGYP)) ||
               ((check == DIFFC4A) && (p2diff < C3AGYP))) {

      /* Convert diffusing gypsum to an ettringite pixel */

      ettrtype = 0;
      Mic[xcur][ycur][zcur] = ETTR;
      if (check == DIFFC4A) {
        ettrtype = 1;
        Mic[xcur][ycur][zcur] = ETTRC4AF;
      }

      action = 0;
      Count[DIFFHEM]--;
      Count[check]--;

      /***
       *    Determine if C3A should be converted to
       *    ettringite
       *
       *    1 unit of hemihydrate requires 0.5583 units of C3A
       *    and should form 4.6053 units of ettringite.  Already
       *    made one pixel of ettringite immediately above,
       *    so we need nexp = 3 more complete ones and then
       *    0.6053 on top of that.
       ***/

      nexp = 3;
      pexp = ran1(Seed);
      if (pexp <= 0.5583) {

        if (ettrtype == 0) {
          Mic[xnew][ynew][znew] = ETTR;
          Count[ETTR]++;
        } else {
          Mic[xnew][ynew][znew] = ETTRC4AF;
          Count[ETTRC4AF]++;
        }

        nexp--;

      } else {

        /***
         *    Maybe someday, use a new FIXEDC3A here so
         *    it won't dissolve later
         ***/

        if (check == C3A || check == OC3A) {
          Mic[xnew][ynew][znew] = check;
          Count[check]++;
        } else {
          if (ettrtype == 0) {
            Count[DIFFC3A]++;
            Mic[xnew][ynew][znew] = DIFFC3A;
          } else {
            Count[DIFFC4A]++;
            Mic[xnew][ynew][znew] = DIFFC4A;
          }
        }
      }

      /***
       *    Create extra ettringite pixels to maintain
       *    volume stoichiometry
       *
       *    xexp, yexp, and zexp hold coordinates of
       *    most recently added ettringite species as we
       *    attempt to grow an acicular crystal shape
       ***/

      xexp = xcur;
      yexp = ycur;
      zexp = zcur;
      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extettr(xexp, yexp, zexp, ettrtype, &poreid);

        /* Update xexp, yexp and zexp as needed */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /***
       *    Probabilistic-based expansion for last
       *    ettringite pixel
       ***/

      pexp = ran1(Seed);
      if (pexp <= 0.6053) {
        newact = extettr(xexp, yexp, zexp, ettrtype, &poreid);
      }
    } /* Done handling C3A-type locations */

    /***
     *    If new location is C4AF, execute conversion to
     *    ettringite (including necessary volumetric
     *    expansion)
     ***/

    if ((check == C4AF) && (p2diff < SOLIDC4AFGYP)) {
      Mic[xcur][ycur][zcur] = ETTRC4AF;
      Count[ETTRC4AF]++;
      Count[DIFFHEM]--;

      /***
       *    Determine if C4AF should be converted to ettringite
       *
       *    1 unit of gypsum requires 0.802 units of C4AF and
       *    should form 4.6053 units of ettringite.  Already made
       *    one pixel of ettringite immediately above, so need
       *    nexp = 3 more complete ones, and then 0.6053 on
       *    top of that.
       ***/

      nexp = 3;
      pexp = ran1(Seed);
      if (pexp <= 0.802) {
        Mic[xnew][ynew][znew] = ETTRC4AF;
        Count[ETTRC4AF]++;
        Count[C4AF]--;
        nexp--;

        /* Addition of extra CH */

        pext = ran1(Seed);
        if (pext < 0.2584) {
          extch(xcur, ycur, zcur, &poreid);
        }

        /* Addition of extra FH3 */
        pext = ran1(Seed);
        if (pext < 0.5453) {
          extfh3(xnew, ynew, znew, &poreid);
        }
      } else {

        /***
         *    Maybe someday, use a new FIXEDC4AF here so
         *    it won't dissolve later
         ***/

        Mic[xnew][ynew][znew] = C4AF;
      }

      /***
       *    Create extra ettringite pixels to maintain
       *    volume stoichiometry
       *
       *    xexp, yexp and zexp hold coordinates of most
       *    recently added ettringite species as we attempt
       *    to grow an acicular crystal shape
       ***/

      xexp = xcur;
      yexp = ycur;
      zexp = zcur;

      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extettr(xexp, yexp, zexp, 1, &poreid);

        /* Update xexp, yexp and zexp as needed */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /***
       *    Probabilistic-based expansion for last
       *    ettringite pixel
       ***/

      pexp = ran1(Seed);
      if (pexp <= 0.6053) {
        newact = extettr(xexp, yexp, zexp, 1, &poreid);
      }

      action = 0;

    } /* Done handling C4AF locations */
  }

  if (action != 0) {

    /***
     *    If diffusion step is possible, perform it
     *    Allow diffusion into either POROSITY or
     *    CRACKP (i.e. saturated crack formed during
     *    hydration process)
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xcur][ycur][zcur] = check;
      Mic[xnew][ynew][znew] = DIFFHEM;
    } else {
      /***
       *    Indicate that diffusing HEMIHYDRATE species
       *    remained at original location
       ***/
      action = 7;
    }
  }

  return (action); /* 7 if nothing happened */
}
/***
 *    moveso4
 *
 *     Move a diffusing SO4 pixel (formed by dissolution of alkali sulfates)
 *
 *     Arguments:    Int coordinates of present location xcur,ycur,zcur
 *                 Int flag indicating whether final diffusion step
 *                 Float nucprgyp is nucleation probability
 *
 *     Returns:    Int return flag indicating action taken
 *                     (reaction or diffusion/no movement)
 *
 *    Calls:        moveone,extettr,extch,extfh3
 *
 *    Called by:    hydrate
 ***/
int moveso4(int xcur, int ycur, int zcur, int finalstep, float nucprgyp) {
  int xnew, ynew, znew, action, sumback, sumin, check, poreid;
  float pgen, pexp, p2diff;

  action = check = 0;
  poreid = -1;

  /* First check for nucleation */

  pgen = ran1(Seed);
  p2diff = ran1(Seed);

  if ((nucprgyp >= pgen) || (finalstep)) {

    /* Nucleate GYPSUMS at this location */

    Nucsulf2gyps++;
    action = 0;
    Mic[xcur][ycur][zcur] = GYPSUMS;
    Count[DIFFSO4]--;
    Count[GYPSUMS]++;

    /***
     *    Add extra gypsum as necessary.  On average, one pixel of
     *    DIFFSO4 should form 1.29 pixels of GYPSUMS
     ***/

    pexp = ran1(Seed);
    if (pexp < 0.29) {
      extgyps(xcur, ycur, zcur, &poreid);
    }

  } else {

    /* Store current location of species */

    xnew = xcur;
    ynew = ycur;
    znew = zcur;
    sumin = 1;
    sumback = moveone(&xnew, &ynew, &znew, &action, sumin);

    if (!action) {
      fprintf(stderr, "\nERROR in moveso4: Value of action is %d", action);
      fflush(stderr);
    }

    check = Mic[xnew][ynew][znew];

    if (check == DIFFCH) {

      /***
       *    Convert both pixels to GYPSUMS
       ***/

      action = 0;
      Mic[xnew][ynew][znew] = GYPSUMS;
      Mic[xcur][ycur][zcur] = GYPSUMS;

      /***
       *    Still need 0.2435 pixels of GYPSUMS
       ***/

      pexp = ran1(Seed);
      if (pexp < 0.2435) {
        extgyps(xcur, ycur, zcur, &poreid);
      }
    }
  }

  if (action != 0) {

    /***
     *    If diffusion step is possible, perform it
     *    Allow diffusion into either POROSITY or
     *    CRACKP (i.e. saturated crack formed during
     *    hydration process)
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xcur][ycur][zcur] = check;
      Mic[xnew][ynew][znew] = DIFFSO4;
    } else {

      /***
       *    Indicate that diffusing HEMIHYDRATE species
       *    remained at original location
       ***/

      action = 7;
    }
  }

  return (action); /* 7 if nothing happened */
}

/***
 *    extfriedel
 *
 *     Add extra Friedel's salt when CaCl2 reacts with
 *     C3A or C4AF at location (xpres,ypres,zpres)
 *
 *     Arguments:    Int coordinates of present location xpres,ypres,zpres
 *
 *     Returns:    Int return flag indicating action taken
 *                     (reaction or diffusion/no movement)
 *
 *    Calls:        moveone, edgecnt
 *
 *    Called by:    movecacl2, movec3a
 ***/
int extfriedel(int xpres, int ypres, int zpres, int *poreid) {
  int multf, numnear, sump, xchr, ychr, zchr, check, fchr, i1, newact, pval;
  int tries;

  /***
   *    First try 6 neighboring locations until
   *        a) successful,
   *        b) all 6 sites are tried and full, or
   *        c) 500 tries are made
   *
   *    Note that 30300 is the product of the first
   *    six prime numbers, indicating that all six
   *    nearest neighbors have been tried.
   ***/

  fchr = 0;
  sump = 1;

  for (i1 = 1; ((i1 <= 500) && (!fchr) && (sump != 30030)); i1++) {

    /* Choose a neighbor at random */

    xchr = xpres;
    ychr = ypres;
    zchr = zpres;
    newact = 0;
    multf = moveone(&xchr, &ychr, &zchr, &newact, sump);

    if (!newact) {
      fprintf(stderr, "\nERROR in extfriedel: Value of newact is %d", newact);
      fflush(stderr);
    }

    check = Mic[xchr][ychr][zchr];

    /***
     *    Because growth is local, if neighbor is saturated porosity
     *    of any kind (POROSITY or CRACKP) then locate the
     *    Friedel's salt there
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xchr][ychr][zchr] = FRIEDEL;
      Count[FRIEDEL]++;
      Count[check]--;
      fchr = 1;
    } else {
      sump *= multf;
    }
  }

  /***
   *    If no neighbor available, locate FRIEDEL at
   *    random location in pore space in contact with
   *    at least one other FRIEDEL, or place it
   *    anyway if MAXTRIES attempts have been made
   *    Here, because the growth is non-local, we
   *    allow growth only into the same kind of saturated
   *    porosity as that found at the original reaction site
   *    (24 May 2004)
   ***/

  tries = 0;
  if (*poreid < 0) {
    if (Cyccnt > Crackcycle) {
      *poreid = getporenv(xpres, ypres, zpres);
    } else {
      *poreid = (int)(POROSITY);
    }
  }
  pval = (int)(*poreid);

  while (!fchr) {

    tries++;
    newact = 7; /* Signifies nothing happened yet */

    /* Generate a random location in the 3-D system */

    xchr = (int)((float)Xsyssize * ran1(Seed));
    ychr = (int)((float)Ysyssize * ran1(Seed));
    zchr = (int)((float)Zsyssize * ran1(Seed));
    if (xchr >= Xsyssize)
      xchr = 0;
    if (ychr >= Ysyssize)
      ychr = 0;
    if (zchr >= Zsyssize)
      zchr = 0;

    check = Mic[xchr][ychr][zchr];

    /* If location is porosity, locate the FRIEDEL there */

    if (check == pval) {

      numnear = edgecnt(xchr, ychr, zchr, FRIEDEL, FRIEDEL, DIFFCACL2);

      /***
       *    Be sure that at least one neighboring pixel
       *    is FRIEDEL or diffusing CACL2
       ***/

      if ((numnear < 26) || (tries > MAXTRIES)) {
        Mic[xchr][ychr][zchr] = FRIEDEL;
        Count[FRIEDEL]++;
        Count[pval]--;
        fchr = 1;
      }
    }
  }

  return (newact); /* 7 if no action was taken */
}

/***
 *    extstrat
 *
 *     Add extra stratlingite when AS reacts with
 *     CH at location (xpres,ypres,zpres), or when
 *     diffusing CAS2 reacts with aluminates
 *
 *     Arguments:    Int coordinates of present location xpres,ypres,zpres
 *
 *     Returns:    Int return flag indicating action taken
 *                     (reaction or diffusion/no movement)
 *
 *    Calls:        moveone, edgecnt
 *
 *    Called by:    moveas, movech, movecas2
 ***/
int extstrat(int xpres, int ypres, int zpres, int *poreid) {
  int multf, numnear, sump, xchr, ychr, zchr, check, fchr, i1, newact, pval;
  int tries;

  /***
   *    First try 6 neighboring locations until
   *        a) successful,
   *        b) all 6 sites are tried and full, or
   *        c) 500 tries are made
   *
   *    Note that 30300 is the product of the first
   *    six prime numbers, indicating that all six
   *    nearest neighbors have been tried
   ***/

  fchr = 0;
  sump = 1;

  for (i1 = 1; ((i1 <= 500) && (!fchr) && (sump != 30030)); i1++) {

    /* Choose a neighbor at random */

    xchr = xpres;
    ychr = ypres;
    zchr = zpres;
    newact = 0;
    multf = moveone(&xchr, &ychr, &zchr, &newact, sump);

    if (!newact) {
      fprintf(stderr, "\nERROR in extstrat: Value of newact is %d", newact);
      fflush(stderr);
    }

    check = Mic[xchr][ychr][zchr];

    /***
     *    If neighbor is porosity then locate
     *    the stratlingite there.  Because growth is
     *    local, we allow growth into any kind of
     *    saturated porosity (POROSITY or CRACKP)
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xchr][ychr][zchr] = STRAT;
      Count[STRAT]++;
      Count[check]--;
      fchr = 1;
    } else {
      sump *= multf;
    }
  }

  /***
   *    If no neighbor available, locate STRAT at
   *    random location in pore space in contact with
   *    at least one other STRAT, or place it anyway
   *    if MAXTRIES attempts have been made.  Because
   *    now growth is non-local, allow growth only into
   *    saturated porosity of the same type as that found
   *    at the original reaction site
   *    (24 May 2004)
   ***/

  tries = 0;
  if (*poreid < 0) {
    if (Cyccnt > Crackcycle) {
      *poreid = getporenv(xpres, ypres, zpres);
    } else {
      *poreid = (int)(POROSITY);
    }
  }
  pval = (int)(*poreid);

  while (!fchr) {

    tries++;
    newact = 7; /* Indicates nothing happened yet */

    /* Generate a random location in the 3-D system */

    xchr = (int)((float)Xsyssize * ran1(Seed));
    ychr = (int)((float)Ysyssize * ran1(Seed));
    zchr = (int)((float)Zsyssize * ran1(Seed));
    if (xchr >= Xsyssize)
      xchr = 0;
    if (ychr >= Ysyssize)
      ychr = 0;
    if (zchr >= Zsyssize)
      zchr = 0;

    check = Mic[xchr][ychr][zchr];

    /* If location is porosity, locate the STRAT there */

    if (check == pval) {

      numnear = edgecnt(xchr, ychr, zchr, STRAT, DIFFCAS2, DIFFAS);

      /***
       *    Be sure that at least one neighboring pixel
       *    is STRAT, diffusing CAS2, or diffusing AS
       ***/

      if ((numnear < 26) || (tries > MAXTRIES)) {
        Mic[xchr][ychr][zchr] = STRAT;
        Count[STRAT]++;
        Count[pval]--;
        fchr = 1;
      }
    }
  }

  return (newact); /* 7 if no action was taken */
}

/***
 *    movegyp
 *
 *     Move a diffusing gypsum pixel from current
 *     location (xcur,ycur,zcur)
 *
 *     Arguments:    Int coordinates of present location
 *                     xcur,ycur,zcur
 *                 Int flag indicating if this is the
 *                     final diffusion step (1 if so)
 *                Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int return flag indicating action taken
 *                     (reaction or diffusion/no movement)
 *
 *    Calls:        moveone, extettr, extch, extfh3
 *
 *    Called by:    hydrate
 ***/
int movegyp(int xcur, int ycur, int zcur, int finalstep) {
  int check, xnew, ynew, znew, action, nexp, iexp, poreid;
  int xexp, yexp, zexp, newact, sumold, sumgarb, ettrtype;
  float pexp, pext, p2diff;

  sumold = 1;
  poreid = -1;

  /***
   *    First be sure that a diffusing gypsum species is
   *    located at xcur,ycur,zcur.  If not, return to
   *    calling routine
   ***/

  if (Mic[xcur][ycur][zcur] != DIFFGYP) {
    action = 0;
    return (action);
  }

  /* Determine new coordinates (periodic boundaries are used) */

  xnew = xcur;
  ynew = ycur;
  znew = zcur;
  action = 0;
  sumgarb = moveone(&xnew, &ynew, &znew, &action, sumold);

  if (!action) {
    fprintf(stderr, "\nERROR in movegyp: Value of action is %d", action);
    fflush(stderr);
  }

  check = Mic[xnew][ynew][znew];

  p2diff = ran1(Seed);

  /* If new location is CSH, check for absorption of gypsum */

  if ((check == CSH) &&
      ((double)Count[ABSGYP] < (Gypabsprob * (double)Count[CSH]))) {

    pexp = ran1(Seed);
    if (pexp < AGRATE) {

      /* Update counts for absorbed and diffusing gypsum */

      Count[ABSGYP]++;
      Count[DIFFGYP]--;
      Mic[xcur][ycur][zcur] = ABSGYP;
      action = 0;
    }

    /***
     *    If new location is C3A or diffusing C3A, execute
     *    conversion to ettringite (including necessary
     *    volumetric expansion)
     *
     *    Use p2diff to try to favor formation of ettringite
     *    on aluminate surfaces as opposed to in solution
     ***/

  } else if ((((check == C3A) || (check == OC3A)) && (p2diff < SOLIDC3AGYP)) ||
             ((check == DIFFC3A) && (p2diff < C3AGYP)) ||
             ((check == DIFFC4A) && (p2diff < C3AGYP))) {

    /* Convert diffusing gypsum to an ettringite pixel */

    ettrtype = 0;
    Mic[xcur][ycur][zcur] = ETTR;

    /***
     *    Convert to iron-rich stable form if encountering
     *    a diffusing C4AF pixel
     ***/

    if (check == DIFFC4A) {
      ettrtype = 1;
      Mic[xcur][ycur][zcur] = ETTRC4AF;
    }

    action = 0;
    Count[DIFFGYP]--;
    Count[check]--;

    /***
     *    Determine if C3A should be converted to ettringite
     *
     *    1 unit of gypsum requires 0.40 units of C3A and
     *    should form 3.30 units of ettringite.  Already added
     *    one pixel of ettringite immediately above, so nees
     *    nexp = 2 more complete ones, and then 0.30 more on
     *    top of that.
     ***/

    nexp = 2;
    pexp = ran1(Seed);
    if (pexp <= 0.40) {
      if (ettrtype == 0) {
        Mic[xnew][ynew][znew] = ETTR;
        Count[ETTR]++;
      } else {
        Mic[xnew][ynew][znew] = ETTRC4AF;
        Count[ETTRC4AF]++;
      }
      nexp--;

    } else {

      /***
       *    Maybe someday, use a new FIXEDC3A here
       *    so it won't dissolve later
       ***/

      if (check == C3A || check == OC3A) {

        Mic[xnew][ynew][znew] = check;
        Count[check]++;

      } else {

        if (ettrtype == 0) {
          Count[DIFFC3A]++;
          Mic[xnew][ynew][znew] = DIFFC3A;
        } else {
          Count[DIFFC4A]++;
          Mic[xnew][ynew][znew] = DIFFC4A;
        }
      }
    }

    /***
     *    Create extra ettringite pixels to maintain
     *    volume stoichiometry
     *
     *    xexp, yexp, and zexp hold coordinates of most
     *    recently added ettringite species as we attempt
     *    to grow an acicular crystal shape
     ***/

    xexp = xcur;
    yexp = ycur;
    zexp = zcur;

    for (iexp = 1; iexp <= nexp; iexp++) {

      newact = extettr(xexp, yexp, zexp, ettrtype, &poreid);

      /* Update xexp, yexp and zexp as needed */

      switch (newact) {
      case 1:
        xexp--;
        if (xexp < 0)
          xexp = (Xsyssize - 1);
        break;
      case 2:
        xexp++;
        if (xexp >= Xsyssize)
          xexp = 0;
        break;
      case 3:
        yexp--;
        if (yexp < 0)
          yexp = (Ysyssize - 1);
        break;
      case 4:
        yexp++;
        if (yexp >= Ysyssize)
          yexp = 0;
        break;
      case 5:
        zexp--;
        if (zexp < 0)
          zexp = (Zsyssize - 1);
        break;
      case 6:
        zexp++;
        if (zexp >= Zsyssize)
          zexp = 0;
        break;
      default:
        break;
      }
    }

    /***
     *    Probabilistic-based expansion for last
     *    ettringite pixel
     ***/

    pexp = ran1(Seed);
    if (pexp <= 0.30) {
      newact = extettr(xexp, yexp, zexp, ettrtype, &poreid);
    }
  }

  /***
   *    If new location is C4AF execute conversion to
   *    ettringite (including necessary volumetric
   *    expansion)
   ***/

  if ((check == C4AF) && (p2diff < SOLIDC4AFGYP)) {

    Mic[xcur][ycur][zcur] = ETTRC4AF;
    Count[ETTRC4AF]++;
    Count[DIFFGYP]--;

    /***
     *    Determine if C4AF should be converted to ettringite
     *
     *    1 unit of gypsum requires 0.575 units of C4AF and
     *    should form 3.30 units of ettringite.  Already added
     *    one pixel of ettringite immediately above, so need
     *    nexp = 2 more complete ones, and then 0.30 more
     *    on top of that.
     ***/

    nexp = 2;
    pexp = ran1(Seed);
    if (pexp <= 0.575) {

      Mic[xnew][ynew][znew] = ETTRC4AF;
      Count[ETTRC4AF]++;
      Count[C4AF]--;
      nexp--;

      /* Addition of extra CH */

      pext = ran1(Seed);
      if (pext < 0.2584) {
        extch(xnew, ynew, znew, &poreid);
      }

      /* Addition of extra FH3 */

      pext = ran1(Seed);
      if (pext < 0.5453) {
        extfh3(xnew, ynew, znew, &poreid);
      }

    } else {

      /***
       *    Maybe someday, use a new FIXEDC4AF here so
       *    it won't dissolve later
       ***/

      Mic[xnew][ynew][znew] = C4AF;
    }

    /***
     *    Create extra ettringite pixels to maintain
     *    volume stoichiometry
     *
     *    xexp, yexp and zexp hold coordinates of most
     *    recently added ettringite species as we attempt
     *    to grow an acicular crystal shape
     ***/

    xexp = xcur;
    yexp = ycur;
    zexp = zcur;
    for (iexp = 1; iexp <= nexp; iexp++) {

      newact = extettr(xexp, yexp, zexp, 1, &poreid);

      /* Update xexp, yexp and zexp as needed */

      switch (newact) {
      case 1:
        xexp--;
        if (xexp < 0)
          xexp = (Xsyssize - 1);
        break;
      case 2:
        xexp++;
        if (xexp >= Xsyssize)
          xexp = 0;
        break;
      case 3:
        yexp--;
        if (yexp < 0)
          yexp = (Ysyssize - 1);
        break;
      case 4:
        yexp++;
        if (yexp >= Ysyssize)
          yexp = 0;
        break;
      case 5:
        zexp--;
        if (zexp < 0)
          zexp = (Zsyssize - 1);
        break;
      case 6:
        zexp++;
        if (zexp >= Zsyssize)
          zexp = 0;
        break;
      default:
        break;
      }
    }

    /* Probabilistic-based expansion for last ettringite pixel */

    pexp = ran1(Seed);
    if (pexp <= 0.30) {
      newact = extettr(xexp, yexp, zexp, 1, &poreid);
    }

    action = 0;
  }

  /***
   *    If last diffusion step and no reaction, convert
   *    back to primary solid gypsum
   ***/

  if ((action != 0) && (finalstep)) {
    action = 0;
    Count[DIFFGYP]--;
    Count[GYPSUM]++;
    Mic[xcur][ycur][zcur] = GYPSUM;
  }

  if (action != 0) {

    /***
     *    If diffusion is possible, execute it
     *    Allow diffusion into either POROSITY or
     *    CRACKP (i.e. saturated crack pore formed
     *    during hydration process)
     *    (24 May 2004)
     ****/

    if (check == POROSITY || check == CRACKP) {
      Mic[xcur][ycur][zcur] = check;
      Mic[xnew][ynew][znew] = DIFFGYP;
    } else {

      /***
       *    Indicate that diffusing gypsum remained at
       *    original location
       ***/

      action = 7;
    }
  }

  return (action); /* 7 if no action was taken */
}

/***
 *    movecacl2
 *
 *     Move a diffusing CaCl2 pixel from current
 *     location (xcur,ycur,zcur)
 *
 *     Arguments:    Int coordinates of present location
 *                     xcur,ycur,zcur
 *                 Int flag indicating if this is the
 *                     final diffusion step (1 if so)
 *                Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int return flag indicating action taken
 *                     (reaction or diffusion/no movement)
 *
 *    Calls:        moveone, extfriedel, extch, extfh3
 *
 *    Called by:    hydrate
 ***/
int movecacl2(int xcur, int ycur, int zcur, int finalstep) {
  int check, xnew, ynew, znew, action, nexp, iexp, poreid;
  int xexp, yexp, zexp, newact, sumold, sumgarb, keep;
  float pexp, pext;

  sumold = 1;
  poreid = -1;
  keep = 0;

  /***
   *    First be sure that a diffusing CaCl2 species is
   *    located at xcur,ycur,zcur.  If not, return to
   *    calling routine
   ***/

  if (Mic[xcur][ycur][zcur] != DIFFCACL2) {
    action = 0;
    return (action);
  }

  /* Determine new coordinates (periodic boundaries are used) */

  xnew = xcur;
  ynew = ycur;
  znew = zcur;
  action = 0;
  sumgarb = moveone(&xnew, &ynew, &znew, &action, sumold);

  if (!action) {
    fprintf(stderr, "\nERROR in movecacl2: Value of action is %d", action);
    fflush(stderr);
  }

  check = Mic[xnew][ynew][znew];

  /***
   *    If new location is C3A/OC3A or diffusing C3A, execute
   *    conversion to Friedel's salt (including necessary
   *    volumetric expansion)
   ***/

  if ((check == C3A) || (check == OC3A) || (check == DIFFC3A) ||
      (check == DIFFC4A)) {

    /* Convert diffusing C3A or C3A to a Friedel's salt pixel */

    action = 0;
    Mic[xnew][ynew][znew] = FRIEDEL;
    Count[FRIEDEL]++;
    Count[check]--;

    /***
     *    Determine if diffusing CaCl2 should be converted
     *    to FRIEDEL
     *
     *    0.5793 unit of CaCl2 requires 1 unit of C3A
     *    and should form 3.3295 units of FRIEDEL.  Already
     *    added one pixel of FRIEDEL, so need nexp = 2 more
     *    complete ones, plus 0.3295 more on top of that.
     ***/

    nexp = 2;
    pexp = ran1(Seed);
    if (pexp <= 0.5793) {
      Mic[xcur][ycur][zcur] = FRIEDEL;
      Count[FRIEDEL]++;
      Count[DIFFCACL2]--;
      nexp--;
    } else {
      keep = 1;
    }

    /***
     *    Create extra Friedel's salt pixels to maintain
     *    volume stoichiometry
     *
     *    xexp, yexp, and zexp hold coordinates of most
     *    recently added FRIEDEL
     ***/

    xexp = xcur;
    yexp = ycur;
    zexp = zcur;
    for (iexp = 1; iexp <= nexp; iexp++) {

      newact = extfriedel(xexp, yexp, zexp, &poreid);

      /* Update xexp, yexp and zexp as needed */

      switch (newact) {
      case 1:
        xexp--;
        if (xexp < 0)
          xexp = (Xsyssize - 1);
        break;
      case 2:
        xexp++;
        if (xexp >= Xsyssize)
          xexp = 0;
        break;
      case 3:
        yexp--;
        if (yexp < 0)
          yexp = (Ysyssize - 1);
        break;
      case 4:
        yexp++;
        if (yexp >= Ysyssize)
          yexp = 0;
        break;
      case 5:
        zexp--;
        if (zexp < 0)
          zexp = (Zsyssize - 1);
        break;
      case 6:
        zexp++;
        if (zexp >= Zsyssize)
          zexp = 0;
        break;
      default:
        break;
      }
    }

    /* Probabilistic-based expansion for last FRIEDEL pixel */

    pexp = ran1(Seed);
    if (pexp <= 0.3295) {
      newact = extfriedel(xexp, yexp, zexp, &poreid);
    }

    /***
     *    If new location is C4AF execute conversion to
     *    Friedel's salt (including necessary volumetric
     *    expansion)
     ***/

  } else if (check == C4AF) {

    Mic[xnew][ynew][znew] = FRIEDEL;
    Count[FRIEDEL]++;
    Count[C4AF]--;

    /***
     *    Determine if CACL2 should be converted to FRIEDEL
     *
     *    0.4033 unit of CaCl2 requires 1 unit of C4AF
     *    and should form 2.3176 units of FRIEDEL.  Already
     *    added one pixel of FRIEDEL immediately above, so
     *    need nexp = 1 more complete one, plus 0.3176 on
     *    top of that.
     *
     *    Also 0.6412 units of CH and 1.3522 units of FH3
     *    per unit of CACL2
     ***/

    nexp = 1;
    pexp = ran1(Seed);
    if (pexp <= 0.4033) {

      Mic[xcur][ycur][zcur] = FRIEDEL;
      Count[FRIEDEL]++;
      Count[DIFFCACL2]--;
      nexp--;

      /* Addition of extra CH */
      pext = ran1(Seed);
      if (pext < 0.6412) {
        extch(xcur, ycur, zcur, &poreid);
      }

      /* Addition of extra FH3 */
      pext = ran1(Seed);
      if (pext < 0.3522) {
        extfh3(xnew, ynew, znew, &poreid);
      }

      extfh3(xnew, ynew, znew, &poreid);

    } else {
      keep = 1;
    }

    /***
     *    Create extra Friedel's salt pixels to maintain
     *    volume stoichiometry
     *
     *    xexp, yexp and zexp hold coordinates of most
     *    recently added FRIEDEL
     ***/

    xexp = xcur;
    yexp = ycur;
    zexp = zcur;
    for (iexp = 1; iexp <= nexp; iexp++) {

      newact = extfriedel(xexp, yexp, zexp, &poreid);

      /* Update xexp, yexp and zexp as needed */

      switch (newact) {
      case 1:
        xexp--;
        if (xexp < 0)
          xexp = (Xsyssize - 1);
        break;
      case 2:
        xexp++;
        if (xexp >= Xsyssize)
          xexp = 0;
        break;
      case 3:
        yexp--;
        if (yexp < 0)
          yexp = (Ysyssize - 1);
        break;
      case 4:
        yexp++;
        if (yexp >= Ysyssize)
          yexp = 0;
        break;
      case 5:
        zexp--;
        if (zexp < 0)
          zexp = (Zsyssize - 1);
        break;
      case 6:
        zexp++;
        if (zexp >= Zsyssize)
          zexp = 0;
        break;
      default:
        break;
      }
    }

    /* Probabilistic-based expansion for last FRIEDEL pixel */

    pexp = ran1(Seed);
    if (pexp <= 0.3176) {
      newact = extfriedel(xexp, yexp, zexp, &poreid);
    }

    action = 0;

  } /* Done handling C4AF pixel case */

  /***
   *    If last diffusion step and no reaction, convert
   *    back to solid CaCl2
   ***/

  if ((action != 0) && (finalstep)) {
    action = 0;
    Count[DIFFCACL2]--;
    Count[CACL2]++;
    Mic[xcur][ycur][zcur] = CACL2;
  }

  if (action != 0) {

    /***
     *    If diffusion is possible, execute it
     *    Allow diffusion into either POROSITY or
     *    CRACKP (i.e. saturated crack pore formed
     *    during hydration process)
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xcur][ycur][zcur] = check;
      Mic[xnew][ynew][znew] = DIFFCACL2;
    } else {

      /***
       *    Indicate that diffusing CACL2 remained at
       *    original location
       ***/

      action = 7;
    }
  }

  if (keep)
    action = 7;

  return (action); /* 7 if no action was taken */
}

/***
 *    movecas2
 *
 *     Move a diffusing CAS2 pixel from current
 *     location (xcur,ycur,zcur)
 *
 *     Arguments:    Int coordinates of present location
 *                     xcur,ycur,zcur
 *                 Int flag indicating if this is the
 *                     final diffusion step (1 if so)
 *                Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int return flag indicating action taken
 *                     (reaction or diffusion/no movement)
 *
 *    Calls:        moveone, extstrat, extch, extfh3
 *
 *    Called by:    hydrate
 ***/
int movecas2(int xcur, int ycur, int zcur, int finalstep) {
  int check, xnew, ynew, znew, action, nexp, iexp, poreid;
  int xexp, yexp, zexp, newact, sumold, sumgarb, keep;
  float pexp, pext;

  sumold = 1;
  poreid = -1;
  keep = 0;

  /***
   *    First be sure that a diffusing CAS2 species is
   *    located at xcur,ycur,zcur.  If not, return to
   *    calling routine
   ***/

  if (Mic[xcur][ycur][zcur] != DIFFCAS2) {
    action = 0;
    return (action);
  }

  /* Determine new coordinates (periodic boundaries are used) */

  xnew = xcur;
  ynew = ycur;
  znew = zcur;
  action = 0;
  sumgarb = moveone(&xnew, &ynew, &znew, &action, sumold);

  if (!action) {
    fprintf(stderr, "\nERROR in movecas2: Value of action is %d", action);
    fflush(stderr);
  }

  check = Mic[xnew][ynew][znew];

  /***
   *    If new location is C3A/OC3A or diffusing C3A, execute
   *    conversion to stratlingite (including necessary
   *    volumetric expansion)
   ***/

  if ((check == C3A) || (check == OC3A) || (check == DIFFC3A) ||
      (check == DIFFC4A)) {

    /* Convert diffusing CAS2 to a stratlingite pixel */

    action = 0;
    Mic[xcur][ycur][zcur] = STRAT;
    Count[STRAT]++;
    Count[DIFFCAS2]--;

    /***
     *    Determine if diffusing or solid C3A should be
     *    converted to STRAT
     *
     *    1 unit of CAS2 requires 0.886 units of C3A and
     *    should form 4.286 units of STRAT
     *
     *    Already converted one pixel to stratlingite
     *    immediately above, so need to convert nexp = 3
     *    more complete ones, and then 0.286 more on top
     *    of that.
     ***/

    nexp = 3;
    pexp = ran1(Seed);
    if (pexp <= 0.886) {
      Mic[xnew][ynew][znew] = STRAT;
      Count[STRAT]++;
      Count[check]--;
      nexp--;
    }

    /***
     *    Create extra stratlingite pixels to maintain
     *    volume stoichiometry
     *
     *    xexp, yexp, and zexp hold coordinates of most
     *    recently added STRAT
     ***/

    xexp = xcur;
    yexp = ycur;
    zexp = zcur;

    /***
     *    Loop over the total number of stratlingite
     *    pixels still needed.
     ***/

    for (iexp = 1; iexp <= nexp; iexp++) {

      newact = extstrat(xexp, yexp, zexp, &poreid);

      /* Update xexp, yexp and zexp as needed */

      switch (newact) {
      case 1:
        xexp--;
        if (xexp < 0)
          xexp = (Xsyssize - 1);
        break;
      case 2:
        xexp++;
        if (xexp >= Xsyssize)
          xexp = 0;
        break;
      case 3:
        yexp--;
        if (yexp < 0)
          yexp = (Ysyssize - 1);
        break;
      case 4:
        yexp++;
        if (yexp >= Ysyssize)
          yexp = 0;
        break;
      case 5:
        zexp--;
        if (zexp < 0)
          zexp = (Zsyssize - 1);
        break;
      case 6:
        zexp++;
        if (zexp >= Zsyssize)
          zexp = 0;
        break;
      default:
        break;
      }
    }

    /***
     *    Added 4 pixels of stratlingite already.  Need an
     *    extra 0.286, which we add probabilistically
     ***/

    pexp = ran1(Seed);
    if (pexp <= 0.286) {
      newact = extstrat(xexp, yexp, zexp, &poreid);
    }

    /***
     *    If new location is C4AF execute conversion
     *    to stratlingite (including necessary volumetric
     *    expansion)
     ***/

  } else if (check == C4AF) {

    Mic[xnew][ynew][znew] = STRAT;
    Count[STRAT]++;
    Count[C4AF]--;

    /***
     *    Determine if CAS2 should be converted to STRAT
     *
     *    0.786 units of CAS2 requires 1 unit of C4AF and
     *    should form 3.37 units of STRAT.  Already made
     *    one pixel of STRAT immediately above, so we
     *    still have to make nexp = 2 more.
     *
     *    Also 0.2586 units of CH and 0.5453 units of FH3
     *    per unit of C4AF
     ***/

    nexp = 2;
    pexp = ran1(Seed);
    if (pexp <= 0.786) {

      Mic[xcur][ycur][zcur] = STRAT;
      Count[STRAT]++;
      Count[DIFFCAS2]--;
      nexp--;

      /***
       *    Addition of extra CH
       *
       *    0.329 = (0.2586 / 0.786)
       ***/

      pext = ran1(Seed);
      if (pext < 0.329) {
        extch(xnew, ynew, znew, &poreid);
      }

      /***
       *    Addition of extra FH3
       *
       *    0.6938 = (0.5453 / 0.786)
       ***/

      pext = ran1(Seed);
      if (pext < 0.6938) {
        extfh3(xnew, ynew, znew, &poreid);
      }

    } else {

      /***
       *    CAS2 does not convert to STRAT this time
       ***/

      keep = 1;
    }

    /***
     *    Create extra stratlingite pixels to maintain
     *    volume stoichiometry
     *
     *    xexp, yexp and zexp hold coordinates of most
     *    recently added STRAT
     ***/

    xexp = xcur;
    yexp = ycur;
    zexp = zcur;

    /***
     *    Loop over the number of stratlingite pixels
     *    still needed
     ***/

    for (iexp = 1; iexp <= nexp; iexp++) {

      newact = extstrat(xexp, yexp, zexp, &poreid);

      /* Update xexp, yexp and zexp as needed */

      switch (newact) {
      case 1:
        xexp--;
        if (xexp < 0)
          xexp = (Xsyssize - 1);
        break;
      case 2:
        xexp++;
        if (xexp >= Xsyssize)
          xexp = 0;
        break;
      case 3:
        yexp--;
        if (yexp < 0)
          yexp = (Ysyssize - 1);
        break;
      case 4:
        yexp++;
        if (yexp >= Ysyssize)
          yexp = 0;
        break;
      case 5:
        zexp--;
        if (zexp < 0)
          zexp = (Zsyssize - 1);
        break;
      case 6:
        zexp++;
        if (zexp >= Zsyssize)
          zexp = 0;
        break;
      default:
        break;
      }
    }

    /***
     *    Added 3 pixels of stratlingite already.  Need an
     *    extra 0.37, which we add probabilistically
     ***/

    pexp = ran1(Seed);
    if (pexp <= 0.37) {
      newact = extstrat(xexp, yexp, zexp, &poreid);
    }

    action = 0;
  }

  /***
   *    If last diffusion step and no reaction, convert
   *    back to solid CAS2
   ***/

  if ((action != 0) && (finalstep)) {
    action = 0;
    Count[DIFFCAS2]--;
    Count[CAS2]++;
    Mic[xcur][ycur][zcur] = CAS2;
  }

  if (action != 0) {

    /***
     *    If diffusion is possible, execute it
     *    Allow diffusion into either POROSITY or
     *    CRACKP (i.e. saturated crack pore formed
     *    during hydration process)
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xcur][ycur][zcur] = check;
      Mic[xnew][ynew][znew] = DIFFCAS2;
    } else {

      /***
       *    Indicate that diffusing CAS2 remained at
       *    original location
       ***/

      action = 7;
    }
  }

  if (keep)
    action = 7;

  return (action); /* 7 if no action taken */
}

/***
 *    moveas
 *
 *     Move a diffusing AS pixel from current
 *     location (xcur,ycur,zcur)
 *
 *     Arguments:    Int coordinates of present location
 *                     xcur,ycur,zcur
 *                 Int flag indicating if this is the
 *                     final diffusion step (1 if so)
 *                Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int return flag indicating action taken
 *                     (reaction or diffusion/no movement)
 *
 *    Calls:        moveone, extstrat
 *
 *    Called by:    hydrate
 ***/
int moveas(int xcur, int ycur, int zcur, int finalstep) {
  int check, xnew, ynew, znew, action, nexp, iexp, poreid;
  int xexp, yexp, zexp, newact, sumold, sumgarb, keep;
  float pexp;

  sumold = 1;
  poreid = -1;
  keep = 0;

  /***
   *    First be sure that a diffusing AS species is
   *    located at xcur,ycur,zcur.  If not, return to
   *    calling routine
   ***/

  if (Mic[xcur][ycur][zcur] != DIFFAS) {
    action = 0;
    return (action);
  }

  /* Determine new coordinates (periodic boundaries are used) */

  xnew = xcur;
  ynew = ycur;
  znew = zcur;
  action = 0;
  sumgarb = moveone(&xnew, &ynew, &znew, &action, sumold);

  if (!action) {
    fprintf(stderr, "\nERROR in moveas: Value of action is %d", action);
    fflush(stderr);
  }

  check = Mic[xnew][ynew][znew];

  /***
   *    If new location is CH or diffusing CH, execute
   *    conversion to stratlingite (including necessary
   *    volumetric expansion)
   ***/

  if ((check == CH) || (check == DIFFCH)) {

    /* Convert diffusing CH or solid CH to a stratlingite pixel */

    action = 0;
    Mic[xnew][ynew][znew] = STRAT;
    Count[STRAT]++;
    Count[check]--;

    /***
     *    Determine if diffusing AS should be converted
     *    to STRAT
     *
     *    0.7538 unit of AS requires 1 unit of CH and
     *    should form 3.26 units of STRAT.  Already made
     *    1 pixel of STRAT immediately above, so need
     *    nexp = 2 more complete ones, and then 0.26 more
     *    on top of that.
     ***/

    nexp = 2;
    pexp = ran1(Seed);
    if (pexp <= 0.7538) {
      Mic[xcur][ycur][zcur] = STRAT;
      Count[STRAT]++;
      Count[DIFFAS]--;
      nexp--;
    } else {
      keep = 1;
    }

    /***
     *    Create extra stratlingite pixels to maintain
     *    volume stoichiometry
     *
     *    xexp, yexp, and zexp hold coordinates of most
     *    recently added STRAT
     ***/

    xexp = xcur;
    yexp = ycur;
    zexp = zcur;
    for (iexp = 1; iexp <= nexp; iexp++) {

      newact = extstrat(xexp, yexp, zexp, &poreid);

      /* Update xexp, yexp and zexp as needed */

      switch (newact) {
      case 1:
        xexp--;
        if (xexp < 0)
          xexp = (Xsyssize - 1);
        break;
      case 2:
        xexp++;
        if (xexp >= Xsyssize)
          xexp = 0;
        break;
      case 3:
        yexp--;
        if (yexp < 0)
          yexp = (Ysyssize - 1);
        break;
      case 4:
        yexp++;
        if (yexp >= Ysyssize)
          yexp = 0;
        break;
      case 5:
        zexp--;
        if (zexp < 0)
          zexp = (Zsyssize - 1);
        break;
      case 6:
        zexp++;
        if (zexp >= Zsyssize)
          zexp = 0;
        break;
      default:
        break;
      }
    }

    /***
     *    Added 3 pixels of stratlingite already.  Need an
     *    extra 0.26, which we add probabilistically
     ***/

    /**** ASK DALE ABOUT THE FACTOR OF 0.32 HERE ****/

    pexp = ran1(Seed);
    if (pexp <= 0.326) {
      newact = extstrat(xexp, yexp, zexp, &poreid);
    }
  }

  /***
   *    If last diffusion step and no reaction, convert
   *    back to solid ASG
   ***/

  if ((action != 0) && (finalstep)) {
    action = 0;
    Count[DIFFAS]--;
    Count[ASG]++;
    Mic[xcur][ycur][zcur] = ASG;
  }

  if (action != 0) {

    /***
     *    If diffusion is possible, execute it
     *    Allow diffusion into either POROSITY or
     *    CRACKP (i.e. saturated crack pore formed
     *    during hydration process)
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xcur][ycur][zcur] = check;
      Mic[xnew][ynew][znew] = DIFFAS;
    } else {

      /***
       *    Indicate that diffusing AS remained at
       *    original location
       ***/

      action = 7;
    }
  }

  if (keep)
    action = 7;

  return (action); /* 7 if no action taken */
}

/***
 *    movecaco3
 *
 *     Move a diffusing CACO3 pixel from current
 *     location (xcur,ycur,zcur)
 *
 *     Arguments:    Int coordinates of present location
 *                     xcur,ycur,zcur
 *                 Int flag indicating if this is the
 *                     final diffusion step (1 if so)
 *                Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int return flag indicating action taken
 *                     (reaction or diffusion/no movement)
 *
 *    Calls:        moveone, extettr
 *
 *    Called by:    hydrate
 ***/
int movecaco3(int xcur, int ycur, int zcur, int finalstep) {
  int check, xnew, ynew, znew, action, poreid;
  int xexp, yexp, zexp, newact, sumold, sumgarb, keep;
  float pexp;

  sumold = 1;
  poreid = -1;
  keep = 0;

  /***
   *    First be sure that a diffusing CACO3 species is
   *    located at xcur,ycur,zcur.  If not, return to
   *    calling routine
   ***/

  if (Mic[xcur][ycur][zcur] != DIFFCACO3) {
    action = 0;
    return (action);
  }

  /* Determine new coordinates (periodic boundaries are used) */

  xnew = xcur;
  ynew = ycur;
  znew = zcur;
  action = 0;
  sumgarb = moveone(&xnew, &ynew, &znew, &action, sumold);

  if (!action) {
    fprintf(stderr, "\nERROR in movecaco3: Value of action is %d", action);
    fflush(stderr);
  }

  check = Mic[xnew][ynew][znew];

  /***
   *    If new location is AFM execute conversion to
   *    carboaluminate and ettringite (including necessary
   *    volumetric expansion)
   ***/

  if (check == AFM) {

    /***
     *    Convert AFM to a carboaluminate or
     *    ettringite pixel
     ***/

    action = 0;
    pexp = ran1(Seed);
    if (pexp <= 0.479192) {
      Mic[xnew][ynew][znew] = AFMC;
      Count[AFMC]++;
    } else {
      Mic[xnew][ynew][znew] = ETTR;
      Count[ETTR]++;
    }

    Count[check]--;

    /***
     *    Determine if diffusing CACO3 should be converted
     *    to AFMC
     *
     *    0.078658 unit of CACO3 requires 1 unit of AFM and
     *    should form 0.55785 units of AFMC
     ***/

    pexp = ran1(Seed);
    if (pexp <= 0.078658) {
      Mic[xcur][ycur][zcur] = AFMC;
      Count[AFMC]++;
      Count[DIFFCACO3]--;
    } else {
      keep = 1;
    }

    /***
     *    Create extra ettringite pixels to maintain
     *    volume stoichiometry
     *
     *    xexp, yexp, and zexp hold coordinates of
     *    most recently added ETTR as we attempt to grow
     *    ettringite as an acicular crystal shape
     ***/

    xexp = xnew;
    yexp = ynew;
    zexp = znew;

    /* Probabilistic-based expansion for new ettringite pixel */

    pexp = ran1(Seed);
    if (pexp <= 0.26194) {
      newact = extettr(xexp, yexp, zexp, 0, &poreid);
    }

  } /* Done handling AFM pixel */

  /***
   *    If last diffusion step and no reaction,
   *    convert back to solid CACO3
   ***/

  if ((action != 0) && (finalstep)) {
    action = 0;
    Count[DIFFCACO3]--;
    Count[CACO3]++;
    Mic[xcur][ycur][zcur] = CACO3;
  }

  if (action != 0) {

    /***
     *    If diffusion is possible, execute it
     *    Allow diffusion into either POROSITY
     *    or CRACKP (i.e. saturated crack pore
     *    formed during hydration process)
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xcur][ycur][zcur] = check;
      Mic[xnew][ynew][znew] = DIFFCACO3;
    } else {

      /***
       *    Indicate that diffusing CACO3 remained at
       *    original location
       ***/

      action = 7;
    }
  }

  if (keep)
    action = 7;

  return (action);
}

/***
 *    extafm
 *
 *     Add extra AFm phase when diffusing ettringite
 *     reacts with C3A (diffusing or solid) at location
 *     (xpres, ypres, zpres)
 *
 *     Arguments:    Int coordinates of present location
 *                     xpres,ypres,zpres
 *
 *     Returns:    Nothing
 *
 *    Calls:        moveone, edgecnt
 *
 *    Called by:    moveettr, movec3a
 ***/
void extafm(int xpres, int ypres, int zpres, int *poreid) {
  int check, sump, xchr, ychr, zchr, fchr, i1, newact, numnear, pval;
  int tries;

  /***
   *    First try 6 neighboring locations until
   *        a) successful,
   *        b) all 6 sites are tried, or
   *        c) 100 tries are made
   *
   *    Note that 30030 is the product of the first six
   *    prime numbers, indicating that all six nearest
   *    neighbors have been tried
   ***/

  fchr = 0;
  sump = 1;

  for (i1 = 1; ((i1 <= 100) && (!fchr) && (sump != 30030)); i1++) {

    /* Determine location of neighbor (using periodic boundaries) */

    xchr = xpres;
    ychr = ypres;
    zchr = zpres;
    newact = 0;
    sump *= moveone(&xchr, &ychr, &zchr, &newact, sump);

    if (!newact) {
      fprintf(stderr, "\nERROR in extafm: Value of newact is %d", newact);
      fflush(stderr);
    }

    check = Mic[xchr][ychr][zchr];

    /***
     *    If neighbor is porosity, locate the AFm phase there.
     *    Porosity can be of any saturated kind because the growth
     *    is local
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xchr][ychr][zchr] = AFM;
      Count[AFM]++;
      Count[check]--;
      fchr = 1;
    }
  }

  /***
   *    If no neighbor available, locate AFm phase at random
   *    location in pore space.  Here because the growth is
   *    non-local, we allow it to occur only into the same kind
   *    of saturated porosity as that found at the original
   *    reaction site
   *    (24 May 2004)
   ***/

  tries = 0;
  if (*poreid < 0) {
    if (Cyccnt > Crackcycle) {
      *poreid = getporenv(xpres, ypres, zpres);
    } else {
      *poreid = (int)(POROSITY);
    }
  }
  pval = (int)(*poreid);

  while (!fchr) {

    tries++;

    /* Generate a random location in the 3-D system */

    xchr = (int)((float)Xsyssize * ran1(Seed));
    ychr = (int)((float)Ysyssize * ran1(Seed));
    zchr = (int)((float)Zsyssize * ran1(Seed));
    if (xchr >= Xsyssize)
      xchr = 0;
    if (ychr >= Ysyssize)
      ychr = 0;
    if (zchr >= Zsyssize)
      zchr = 0;

    check = Mic[xchr][ychr][zchr];

    /* If location is porosity, locate the extra AFm there */

    if (check == pval) {

      numnear = edgecnt(xchr, ychr, zchr, AFM, C3A, C4AF);
      if (numnear == 26)
        numnear = edgecnt(xchr, ychr, zchr, AFM, OC3A, C4AF);

      /***
       *    Be sure that at least one neighboring pixel
       *    is Afm phase, C3A, OC3A, or C4AF
       ***/

      if ((numnear < 26) || (tries > MAXTRIES)) {
        Mic[xchr][ychr][zchr] = AFM;
        Count[AFM]++;
        Count[pval]--;
        fchr = 1;
      }
    }
  }

  return;
}

/***
 *    moveettr
 *
 *     Move a diffusing ettringite pixel currently located
 *     at (xcur, ycur, zcur)
 *
 *     Arguments:    Int coordinates of present location
 *                     xcur,ycur,zcur
 *                 Int flag indicating if this is the final
 *                     diffusion step
 *                Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int flag indicating action taken
 *                     (reaction/diffusion or no action)
 *
 *    Calls:        moveone, extch, extfh3, extafm
 *
 *    Called by:    hydrate
 ***/
int moveettr(int xcur, int ycur, int zcur, int finalstep) {
  int check, xnew, ynew, znew, action, poreid;
  int sumold, sumgarb;
  float pexp, pafm, pgrow;

  poreid = -1;

  /***
   *    First be sure a diffusing ettringite species is
   *    located at xcur,ycur,zcur.  If not, return to
   *    calling routine
   ***/

  if (Mic[xcur][ycur][zcur] != DIFFETTR) {
    action = 0;
    return (action);
  }

  /* Determine new coordinates (periodic boundaries are used) */

  xnew = xcur;
  ynew = ycur;
  znew = zcur;
  action = 0;
  sumold = 1;
  sumgarb = moveone(&xnew, &ynew, &znew, &action, sumold);

  if (!action) {
    fprintf(stderr, "\nERROR in moveettr: Value of action is %d", action);
    fflush(stderr);
  }

  check = Mic[xnew][ynew][znew];

  /***
   *    If new location is C4AF, execute conversion to
   *    AFM phase (including necessary volumetric
   *    expansion)
   ***/

  if (check == C4AF) {

    /* Convert diffusing ettringite to AFM phase */

    Mic[xcur][ycur][zcur] = AFM;
    Count[AFM]++;
    Count[DIFFETTR]--;

    /***
     *    Determine if C4AF should be converted to Afm
     *    or FH3
     *
     *    1 unit of ettringite requires 0.348 units of
     *    C4AF to form 1.278 units of Afm, 0.0901 units
     *    of CH and 0.1899 units of FH3
     ***/

    pexp = ran1(Seed);
    if (pexp <= 0.278) {
      Mic[xnew][ynew][znew] = AFM;
      Count[AFM]++;
      Count[C4AF]--;

      /***
       *    Addition of extra CH
       *
       *    0.3241 = (0.0901 / 0.278)
       ***/

      pafm = ran1(Seed);
      if (pafm < 0.3241) {
        extch(xnew, ynew, znew, &poreid);
      }

      /***
       *    Addition of extra FH3
       *
       *    0.4313 = ((0.1899 - (0.348 - 0.278))/0.278)
       ***/

      pafm = ran1(Seed);
      if (pafm < 0.4313) {
        extfh3(xnew, ynew, znew, &poreid);
      }
    } else if (pexp <= 0.348) {

      Mic[xnew][ynew][znew] = FH3;
      Count[FH3]++;
      Count[C4AF]--;
    }

    action = 0;

    /* Done handling case of C4AF pixel */

    /***
     *    If new location is C3A/OC3A or diffusing C3A,
     *    execute conversion to AFM phase (including
     *    necessary volumetric expansion)
     ***/

  } else if ((check == C3A) || (check == OC3A) || (check == DIFFC3A)) {

    /* Convert diffusing ettringite to AFM phase */

    action = 0;
    Mic[xcur][ycur][zcur] = AFM;
    Count[DIFFETTR]--;
    Count[AFM]++;
    Count[check]--;

    /***
     *    Determine if C3A should be converted to AFm
     *
     *    1 unit of ettringite requires 0.2424 units of C3A
     *    and should form 1.278 units of AFm phase
     ***/

    pexp = ran1(Seed);
    if (pexp <= 0.2424) {
      Mic[xnew][ynew][znew] = AFM;
      Count[AFM]++;
      pafm = (-0.1);
    } else {

      /***
       *    Maybe someday, use a new FIXEDC3A here
       *    so it won't dissolve later
       ***/

      if (check == C3A || check == OC3A) {
        Mic[xnew][ynew][znew] = check;
        Count[check]++;
      } else {
        Mic[xnew][ynew][znew] = DIFFC3A;
        Count[DIFFC3A]++;
      }

      /* pafm = (0.278 - 0.2424) / (1.0 - 0.2424); */

      pafm = 0.04699;
    }

    /* Probabilistic-based expansion for new AFm phase pixel */

    pexp = ran1(Seed);
    if (pexp <= pafm) {
      extafm(xcur, ycur, zcur, &poreid);
    }

    /* Done handling C3A pixel case  */

    /* Otherwise check for conversion back to solid ettringite */

  } else if (check == ETTR) {

    pgrow = ran1(Seed);
    if (pgrow <= ETTRGROW) {
      Mic[xcur][ycur][zcur] = ETTR;
      Count[ETTR]++;
      Count[DIFFETTR]--;
      action = 0;
    }
  }

  /***
   *    If last diffusion step and no reaction,
   *    convert back to solid ettringite
   ***/

  if ((action != 0) && (finalstep)) {
    action = 0;
    Mic[xcur][ycur][zcur] = ETTR;
    Count[DIFFETTR]--;
    Count[ETTR]++;
  }

  if (action != 0) {

    /***
     *    If diffusion is possible, execute it
     *    Allow diffusion into either POROSITY or
     *    CRACKP (i.e. saturated crack pore formed
     *    during hydration process)
     *    (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xcur][ycur][zcur] = check;
      Mic[xnew][ynew][znew] = DIFFETTR;
    } else {

      /***
       *    Indicate that diffusing ettringite remained at
       *    original location
       ***/

      action = 7;
    }
  }

  return (action); /* 7 if no action taken */
}

/***
 *    extpozz
 *
 *     Add extra pozzolanic CSH when CH reacts at
 *     pozzolanic surface (e.g. silica fume) at location
 *     (xpres, ypres, zpres)
 *
 *     Arguments:    Int coordinates of present location
 *                     xpres,ypres,zpres
 *
 *     Returns:    Nothing
 *
 *    Calls:        moveone, edgecnt
 *
 *    Called by:    movech
 ***/
void extpozz(int xpres, int ypres, int zpres, int *poreid) {
  int check, sump, xchr, ychr, zchr, fchr, i1, newact, numnear1, numnear2, pval;
  int tries;

  /***
   *    First try 6 neighboring locations until
   *        a) successful,
   *        b) all 6 sites are tried, or
   *        c) 100 tries are made
   *
   *    Note that 30030 is the product of the first six
   *    prime numbers, indicating that all six nearest
   *    neighbors have been tried
   ***/

  fchr = 0;
  sump = 1;

  for (i1 = 1; ((i1 <= 100) && (!fchr) && (sump != 30030)); i1++) {

    /* Determine location of neighbor (using periodic boundaries) */

    xchr = xpres;
    ychr = ypres;
    zchr = zpres;
    newact = 0;
    sump *= moveone(&xchr, &ychr, &zchr, &newact, sump);

    if (!newact) {
      fprintf(stderr, "\nERROR in extpozz: Value of newact is %d", newact);
      fflush(stderr);
    }

    check = Mic[xchr][ychr][zchr];

    /***
     *     If neighbor is porosity, locate the phase there.
     *     We allow growth into any kind of saturated porosity
     *     (CRACKP or POROSITY) because the growth is local
     *     (24 May 2004)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xchr][ychr][zchr] = POZZCSH;
      Count[POZZCSH]++;
      Count[check]--;
      fchr = 1;
    }
  }

  /***
   *    If no neighbor available, locate pozzolanic
   *    CSH at random location in pore space.  Now that
   *    the growth is non-local, allow it to occur only
   *    into the same kind of saturated porosity as that
   *    found at the original reaction site
   *    (24 May 2004)
   ***/

  tries = 0;
  if (*poreid < 0) {
    if (Cyccnt > Crackcycle) {
      *poreid = getporenv(xpres, ypres, zpres);
    } else {
      *poreid = (int)(POROSITY);
    }
  }
  pval = (int)(*poreid);

  while (!fchr) {

    tries++;

    /* Generate a random location in the 3-D system */

    xchr = (int)((float)Xsyssize * ran1(Seed));
    ychr = (int)((float)Ysyssize * ran1(Seed));
    zchr = (int)((float)Zsyssize * ran1(Seed));
    if (xchr >= Xsyssize)
      xchr = 0;
    if (ychr >= Ysyssize)
      ychr = 0;
    if (zchr >= Zsyssize)
      zchr = 0;

    check = Mic[xchr][ychr][zchr];

    /***
     *    If location is porosity, locate the
     *    extra pozzolanic CSH there
     ***/

    if (check == pval) {

      numnear1 = edgecnt(xchr, ychr, zchr, SFUME, CSH, POZZCSH);
      numnear2 = edgecnt(xchr, ychr, zchr, AMSIL, CSH, POZZCSH);

      /***
       *    Be sure that one neighboring species is CSH
       *    or pozzolanic material
       ***/

      if ((numnear1 < 26 || numnear2 < 26) || (tries > MAXTRIES)) {
        Mic[xchr][ychr][zchr] = POZZCSH;
        Count[POZZCSH]++;
        Count[pval]--;
        fchr = 1;
      }
    }
  }

  return;
}

/***
 *    movefh3
 *
 *     Move a diffusing FH3 pixel currently located
 *     at (xcur, ycur, zcur), with nucleation
 *    probability nucprob
 *
 *     Arguments:    Int coordinates of present location
 *                     xcur,ycur,zcur
 *                 Int flag indicating if this is the final
 *                     diffusion step
 *                 Float nucleation probability
 *                Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int flag indicating action taken
 *                     (reaction/diffusion or no action)
 *
 *    Calls:        moveone
 *
 *    Called by:    hydrate
 ***/
int movefh3(int xcur, int ycur, int zcur, int finalstep, float nucprob) {
  int check, xnew, ynew, znew, action, sumold, sumgarb;
  float pgen;

  /***
   *    First check for nucleation, which will occur if
   *        a) nucleation probability exceeds random value, or
   *        b) this is the final diffusion step
   ***/

  pgen = ran1(Seed);

  if ((nucprob >= pgen) || (finalstep)) {
    action = 0;
    Mic[xcur][ycur][zcur] = FH3;
    Count[FH3]++;
    Count[DIFFFH3]--;

  } else {

    /* Determine new location (using periodic boundaries) */

    xnew = xcur;
    ynew = ycur;
    znew = zcur;
    action = 0;
    sumold = 1;
    sumgarb = moveone(&xnew, &ynew, &znew, &action, sumold);

    if (!action) {
      fprintf(stderr, "\nERROR in movefh3: Value of action is %d", action);
      fflush(stderr);
    }

    check = Mic[xnew][ynew][znew];

    /***
     *    Check for growth of FH3 crystal, which will
     *    occur spontaneously if diffusing FH3 collides
     *    with solid FH3
     ***/

    if (check == FH3) {
      Mic[xcur][ycur][zcur] = FH3;
      Count[FH3]++;
      Count[DIFFFH3]--;
      action = 0;
    }

    if (action != 0) {

      /***
       *    If diffusion is possible, execute it
       *    Allow diffusion into either POROSITY or
       *    CRACKP (i.e. saturated crack pore formed
       *    during hydration process)
       *    (24 May 2004)
       ***/

      if (check == POROSITY || check == CRACKP) {
        Mic[xcur][ycur][zcur] = check;
        Mic[xnew][ynew][znew] = DIFFFH3;
      } else {

        /***
         *    Indicate that diffusing FH3 species
         *    remained at original location
         ***/

        action = 7;
      }
    }
  }

  return (action); /* 7 if no action taken */
}

/***
 *    movech
 *
 *     Move a diffusing CH pixel currently located
 *     at (xcur, ycur, zcur), with nucleation
 *    probability nucprob
 *
 *     Arguments:    Int coordinates of present location
 *                     xcur,ycur,zcur
 *                 Int flag indicating if this is the final
 *                     diffusion step
 *                 Float nucleation probability
 *                Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int flag indicating action taken
 *                     (reaction/diffusion or no action)
 *
 *    Calls:        moveone, extpozz, extstrat
 *
 *    Called by:    hydrate
 ***/
int movech(int xcur, int ycur, int zcur, int finalstep, float nucprob) {
  int check, xnew, ynew, znew, action, sumgarb, sumold, poreid;
  float pexp, pgen, pfix;

  poreid = -1;

  /***
   *    First check for nucleation, which will occur if
   *        a) nucleation probability exceeds random value, or
   *        b) this is the final diffusion step
   ***/

  pgen = ran1(Seed);
  if ((nucprob >= pgen) || (finalstep)) {

    action = 0;
    Mic[xcur][ycur][zcur] = CH;
    Count[DIFFCH]--;
    Count[CH]++;

  } else {

    /* Determine new location (using periodic boundaries) */

    xnew = xcur;
    ynew = ycur;
    znew = zcur;
    action = 0;
    sumold = 1;
    sumgarb = moveone(&xnew, &ynew, &znew, &action, sumold);

    if (!action) {
      fprintf(stderr, "\nERROR in movech: Value of action is %d", action);
      fflush(stderr);
    }

    check = Mic[xnew][ynew][znew];

    /***
     *    Check for growth of CH crystal, which will occur
     *    with probability CHGROW if a diffusing CH collides
     *    with solid CH
     ***/

    if ((check == CH) && (pgen <= CHGROW)) {
      Mic[xcur][ycur][zcur] = CH;
      Count[DIFFCH]--;
      Count[CH]++;
      action = 0;
    }

    /***
     *    Check for growth of CH crystal on aggregate surface,
     *    which will occur with probability CHGROWAGG if a
     *    diffusing CH collides with inert aggregate surface
     *
     *     Also requires that Chflag be turned on by user
     *
     *    (suggestion of Sidney Diamond)
     ***/

    if (((check == INERTAGG) || (check == CACO3)) && (pgen <= CHGROWAGG) &&
        (Chflag)) {
      Mic[xcur][ycur][zcur] = CH;
      Count[DIFFCH]--;
      Count[CH]++;
      action = 0;

      /***
       *    Check for pozzolanic reaction with silica fume
       *
       *    36.41 units CH can react with 27 units of S to make POZZCSH
       ***/

    } else if ((((pgen <= PHfactor[SFUME] * Psfume) && (check == SFUME)) ||
                ((pgen <= PHfactor[AMSIL] * Pamsil) && (check == AMSIL))) &&
               (Nsilica_rx <= ((double)Nsilica * 1.35))) {

      action = 0;
      Mic[xcur][ycur][zcur] = POZZCSH;
      Count[POZZCSH]++;

      /***
       *    Update counter of number of diffusing CH
       *    that have reacted pozzolanically
       ***/

      Nsilica_rx++;
      Count[DIFFCH]--;

      /* Convert pozzolan to pozzolanic CSH as needed */

      pfix = ran1(Seed);
      if (pfix <= (1.0 / 1.35)) {
        Mic[xnew][ynew][znew] = POZZCSH;
        Count[check]--;
        Count[POZZCSH]++;
      }

      /***
       *    Allow for extra pozzolanic CSH as needed
       *
       *    Should form 101.81 units of pozzolanic CSH for
       *    each 36.41 units of CH and 27 units of S
       *
       *    1.05466 = (101.81 - 36.41 - 27) / 36.41
       ***/

      pexp = ran1(Seed);
      extpozz(xcur, ycur, zcur, &poreid);
      if (pexp <= 0.05466) {
        extpozz(xcur, ycur, zcur, &poreid);
      }

    } else if (check == DIFFAS) {
      action = 0;
      Mic[xcur][ycur][zcur] = STRAT;
      Count[DIFFCH]--;
      Count[STRAT]++;

      /***
       *    Update counter of number of diffusing CH
       *    that have reacted to form stratlingite
       ***/

      Nasr++;

      /* Convert DIFFAS to STRAT as needed */

      pfix = ran1(Seed);
      if (pfix <= 0.7538) {
        Mic[xnew][ynew][znew] = STRAT;
        Count[STRAT]++;
        Count[DIFFAS]--;
      }

      /***
       *    Allow for extra stratlingite as needed
       *
       *    1.5035 = (215.63 - 66.2 - 49.9) / 66.2
       ***/

      extstrat(xcur, ycur, zcur, &poreid);

      pexp = ran1(Seed);
      if (pexp <= 0.5035) {
        extstrat(xcur, ycur, zcur, &poreid);
      }

    } /* Done handling the DIFFAS pixel case */

    if (action != 0) {

      /***
       *    If diffusion is possible, execute it
       *    Allow diffusion into either POROSITY or
       *    CRACKP (i.e. saturated crack pore formed
       *    during hydration process)
       *    (24 May 2004)
       ***/

      if (check == POROSITY || check == CRACKP) {
        Mic[xcur][ycur][zcur] = check;
        Mic[xnew][ynew][znew] = DIFFCH;
      } else {

        /***
         *    Indicate that diffusing CH species
         *    remained at original location
         ***/

        action = 7;
      }
    }
  }

  return (action);
}

/***
 *    extc3ah6
 *
 *     Add extra C3AH6 when diffusing C3A nucleates or
 *     reacts at C3AH6 surface at location
 *     (xpres, ypres, zpres)
 *
 *     Arguments:    Int coordinates of present location
 *                     xpres,ypres,zpres
 *                 int id of type of saturated porosity at the
 *                     original reaction site (24 May 2004)
 *
 *     Returns:    Nothing
 *
 *    Calls:        moveone, edgecnt
 *
 *    Called by:    movec3a
 ***/
void extc3ah6(int xpres, int ypres, int zpres, int *poreid) {
  int check, sump, xchr, ychr, zchr, fchr, i1, action, numnear, pval;
  int tries;

  /***
   *    First try 6 neighboring locations until
   *        a) successful,
   *        b) all 6 sites are tried, or
   *        c) 100 tries are made
   *
   *    Note that 30030 is the product of the first six
   *    prime numbers, indicating that all six nearest
   *    neighbors have been tried
   ***/

  fchr = 0;
  sump = 1;

  for (i1 = 1; ((i1 <= 100) && (!fchr) && (sump != 30030)); i1++) {

    /* Determine location of neighbor (using periodic boundaries) */

    xchr = xpres;
    ychr = ypres;
    zchr = zpres;
    action = 0;
    sump *= moveone(&xchr, &ychr, &zchr, &action, sump);

    if (!action) {
      fprintf(stderr, "\nERROR in extc3ah6: Value of action is %d", action);
      fflush(stderr);
    }

    check = Mic[xchr][ychr][zchr];

    /***
     *    If neighbor is pore space, convert it to C3AH6
     *    Because growth is local, we allow it to occur into
     *    any kind of saturated porosity (CRACKP or POROSITY)
     ***/

    if (check == POROSITY || check == CRACKP) {
      Mic[xchr][ychr][zchr] = C3AH6;
      Count[C3AH6]++;
      Count[check]--;
      fchr = 1;
    }
  }

  /***
   *    If unsuccessful, add C3AH6 at random location in pore space
   *    Now, because growth is non-local, allow it to occur only into
   *    the kind of saturated porosity as that found at the original
   *    reaction site
   *    (24 May 2004)
   ***/

  tries = 0;
  if (*poreid < 0) {
    if (Cyccnt > Crackcycle) {
      *poreid = getporenv(xpres, ypres, zpres);
    } else {
      *poreid = (int)(POROSITY);
    }
  }
  pval = (int)(*poreid);

  while (!fchr) {

    tries++;

    xchr = (int)((float)Xsyssize * ran1(Seed));
    ychr = (int)((float)Ysyssize * ran1(Seed));
    zchr = (int)((float)Zsyssize * ran1(Seed));
    if (xchr >= Xsyssize)
      xchr = 0;
    if (ychr >= Ysyssize)
      ychr = 0;
    if (zchr >= Zsyssize)
      zchr = 0;
    check = Mic[xchr][ychr][zchr];

    if (check == pval) {

      numnear = edgecnt(xchr, ychr, zchr, C3AH6, C3A, C3AH6);
      if (numnear == 26)
        numnear = edgecnt(xchr, ychr, zchr, OC3A, C3AH6, C3AH6);

      /***
       *    Be sure that new C3AH6 is in contact with
       *    at least one other C3AH6 or C3A/OC3A
       ***/

      if ((numnear < 26) || (tries > MAXTRIES)) {
        Mic[xchr][ychr][zchr] = C3AH6;
        Count[C3AH6]++;
        Count[pval]--;
        fchr = 1;
      }
    }
  }

  return;
}

/***
 *    movec3a
 *
 *     Move a diffusing C3A pixel currently located
 *     at (xcur, ycur, zcur), with nucleation
 *    probability nucprob
 *
 *     Arguments:    Int coordinates of present location
 *                     xcur,ycur,zcur
 *                 Int flag indicating if this is the final
 *                     diffusion step
 *                 Float nucleation probability
 *                Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int flag indicating action taken
 *                     (reaction/diffusion or no action)
 *
 *    Calls:        moveone, extc3ah6, extettr, extafm, extstrat,
 *                extfriedel
 *
 *    Called by:    hydrate
 ***/
int movec3a(int xcur, int ycur, int zcur, int finalstep, float nucprob) {
  int check, xnew, ynew, znew, action, sumgarb, sumold, poreid;
  int xexp, yexp, zexp, nexp, iexp, newact;
  float pgen, pexp, pafm, pgrow, p2diff;

  poreid = -1;

  /***
   *    First be sure that a diffusing C3A species
   *    is at (xcur,ycur,zcur)
   ***/

  if (Mic[xcur][ycur][zcur] != DIFFC3A) {
    action = 0;
    return (action);
  }

  /***
   *    Check for nucleation into solid C3AH6, which will
   *    occur with probability nucprob or with certainty if
   *    this is the final diffusion step
   ***/

  pgen = ran1(Seed);
  p2diff = ran1(Seed);

  if ((nucprob >= pgen) || (finalstep)) {
    action = 0;
    Mic[xcur][ycur][zcur] = C3AH6;
    Count[C3AH6]++;
    Count[DIFFC3A]--;

    /***
     *    Allow for probabilistic-based expansion of C3AH6
     *    crystal to account for volume stoichiometry
     ***/

    /*** ASK DALE ABOUT FACTOR OF 0.69 ***/

    pexp = ran1(Seed);
    if (pexp <= 0.69) {
      extc3ah6(xcur, ycur, zcur, &poreid);
    }

  } else {

    /* Determine new coordinates (using periodic boundaries) */

    xnew = xcur;
    ynew = ycur;
    znew = zcur;
    action = 0;
    sumold = 1;
    sumgarb = moveone(&xnew, &ynew, &znew, &action, sumold);
    if (!action) {
      fprintf(stderr, "\nERROR in movec3a: Value of action is %d", action);
      fflush(stderr);
    }

    check = Mic[xnew][ynew][znew];

    /***
     *    Check for growth of C3AH6 crystal, which will occur
     *    with probability C3AH6GROW if the diffusing C3A
     *    collides with a solid C3AH6 surface.  We choose
     *    C3AH6GROW < 1 in this case to attempt to promote
     *    ettringite formation and AFm formation
     ***/

    if (check == C3AH6) {

      pgrow = ran1(Seed);
      if (pgrow <= C3AH6GROW) {
        Mic[xcur][ycur][zcur] = C3AH6;
        Count[C3AH6]++;
        Count[DIFFC3A]--;
        action = 0;

        /***
         *    Allow for probabilistic-based expansion of C3AH6
         *    crystal to account for volume stoichiometry
         ***/

        /*** ASK DALE ABOUT FACTOR OF 0.69 (AGAIN) ***/

        pexp = ran1(Seed);
        if (pexp <= 0.69) {
          extc3ah6(xcur, ycur, zcur, &poreid);
        }
      }

      /***
       *    Examine reaction with diffusing gypsum to
       *    form ettringite
       *
       *    Only allow reaction with diffusing gypsum
       ***/

    } else if ((check == DIFFGYP) && (p2diff < C3AGYP)) {

      /* Convert diffusing gypsum to ettringite */

      Mic[xnew][ynew][znew] = ETTR;
      Count[ETTR]++;
      Count[DIFFGYP]--;
      action = 0;

      /***
       *    Convert diffusing C3A to solid ettringite
       *    or else leave as a diffusing C3A
       ***/

      nexp = 2;
      pexp = ran1(Seed);
      if (pexp <= 0.40) {
        Mic[xcur][ycur][zcur] = ETTR;
        Count[ETTR]++;
        Count[DIFFC3A]--;
        nexp--;
      } else {

        /***
         *    Indicate that diffusing species
         *    remains in current location
         ***/

        action = 7;
      }

      /***
       *    Perform expansion that occurs when
       *    ettringite is formed
       *
       *    xexp, yexp and zexp are the coordinates of
       *    the last ettringite pixel to be added
       *    as we attempt to grow in an acicular
       *    crystal shape
       ***/

      xexp = xnew;
      yexp = ynew;
      zexp = znew;
      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extettr(xexp, yexp, zexp, 0, &poreid);

        /* Update xexp, yexp and zexp */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /* Probabilistic-based expansion for last ettringite pixel */

      pexp = ran1(Seed);
      if (pexp <= 0.30) {
        newact = extettr(xexp, yexp, zexp, 0, &poreid);
      }

      /***
       *    Either pixel is not diffusing gypsum or p2diff was
       *    >= C3AGYP.  One alternative is that the pixel is
       *    diffusing hemihydrate.
       *
       *    Examine reaction with diffusing hemihydrate
       *    to form ettringite
       *
       *    Only allow reaction with diffusing hemihydrate
       ***/

    } else if ((check == DIFFHEM) && (p2diff < C3AGYP)) {

      /* Convert diffusing hemihydrate to ettringite */

      Mic[xnew][ynew][znew] = ETTR;
      Count[ETTR]++;
      Count[DIFFHEM]--;
      action = 0;

      /***
       *    Convert diffusing C3A to solid ettringite
       *    or else leave as a diffusing C3A
       ***/

      /*** ASK DALE ABOUT FACTOR OF 0.5583 ***/

      nexp = 3;
      pexp = ran1(Seed);
      if (pexp <= 0.5583) {
        Mic[xcur][ycur][zcur] = ETTR;
        Count[ETTR]++;
        Count[DIFFC3A]--;
        nexp--;
      } else {

        /***
         *    Indicate that diffusing species
         *    remains in current location
         ***/

        action = 7;
      }

      /***
       *    Perform expansion that occurs when ettringite
       *    is formed
       *
       *    xexp, yexp and zexp are the coordinates of the
       *    last ettringite pixel to be added as we try to
       *    grow the ettringite in an acicular crystal shape
       ***/

      xexp = xnew;
      yexp = ynew;
      zexp = znew;
      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extettr(xexp, yexp, zexp, 0, &poreid);

        /* Update xexp, yexp and zexp */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /* Probabilistic-based expansion for last ettringite pixel */

      /*** ASK DALE ABOUT FACTOR OF 0.6053 ***/
      pexp = ran1(Seed);
      if (pexp <= 0.6053) {
        newact = extettr(xexp, yexp, zexp, 0, &poreid);
      }

      /***
       *    Either pixel is neither diffusing gypsum nor
       *    diffusing hemihydrate, or p2diff was >= C3AGYP.
       *    Another alternative is that the pixel is
       *    diffusing anhydrite.
       *
       *    Examine reaction with diffusing anhydrite
       *    to form ettringite
       *
       *    Only allow reaction with diffusing anhydrite
       ***/

    } else if ((check == DIFFANH) && (p2diff < C3AGYP)) {

      /* Convert diffusing anhydrite to ettringite */

      Mic[xnew][ynew][znew] = ETTR;
      Count[ETTR]++;
      Count[DIFFANH]--;
      action = 0;

      /***
       *    Convert diffusing C3A to solid ettringite
       *    or else leave as a diffusing C3A
       ***/

      nexp = 3;
      pexp = ran1(Seed);
      if (pexp <= 0.569) {
        Mic[xcur][ycur][zcur] = ETTR;
        Count[ETTR]++;
        Count[DIFFC3A]--;
        nexp--;
      } else {

        /***
         *    Indicate that diffusing species remains
         *    in current location
         ***/

        action = 7;
      }

      /***
       *    Perform expansion that occurs when ettringite
       *    is formed
       *
       *    xexp, yexp and zexp are the coordinates
       *    of the last ettringite pixel to be added
       *    as we try to grow in an acicular crystal shape
       ***/

      xexp = xnew;
      yexp = ynew;
      zexp = znew;
      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extettr(xexp, yexp, zexp, 0, &poreid);

        /* Update xexp, yexp and zexp */
        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /* Probabilistic-based expansion for last ettringite pixel */

      /*** ASK DALE ABOUT FACTOR OF 0.6935 ***/
      pexp = ran1(Seed);
      if (pexp <= 0.6935) {
        newact = extettr(xexp, yexp, zexp, 0, &poreid);
      }

      /***
       *    Either pixel is neither diffusing gypsum nor
       *    diffusing hemihydrate nor diffusing anhydrite,
       *    or p2diff was >= C3AGYP.
       *
       *    Another alternative is that the pixel is
       *    diffusing CaCl2.  Examine reaction with
       *    diffusing CaCl2    to form Friedel's salt
       *
       *    Only allow reaction with diffusing CaCl2
       ***/

    } else if (check == DIFFCACL2) {

      /* Convert diffusing C3A to Friedel's salt */

      Mic[xcur][ycur][zcur] = FRIEDEL;
      Count[FRIEDEL]++;
      Count[DIFFC3A]--;
      action = 0;

      /***
       *    Convert diffusing CACL2 to solid FRIEDEL or
       *    else leave as a diffusing CACL2
       ***/

      /*** ASK DALE ABOUT FACTOR OF 0.5793 ***/

      nexp = 2;
      pexp = ran1(Seed);
      if (pexp <= 0.5793) {
        Mic[xnew][ynew][znew] = FRIEDEL;
        Count[FRIEDEL]++;
        Count[DIFFCACL2]--;
        nexp--;
      }

      /***
       *    Perform expansion that occurs when Friedel's
       *    salt is formed
       *
       *    xexp, yexp and zexp are the coordinates of
       *    the last FRIEDEL pixel to be added
       ***/

      xexp = xnew;
      yexp = ynew;
      zexp = znew;
      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extfriedel(xexp, yexp, zexp, &poreid);

        /* Update xexp, yexp and zexp */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /* Probabilistic-based expansion for last FRIEDEL pixel */

      /*** ASK DALE ABOUT FACTOR OF 0.3295 ***/

      pexp = ran1(Seed);
      if (pexp <= 0.3295) {
        newact = extfriedel(xexp, yexp, zexp, &poreid);
      }

      /***
       *    Either pixel is neither diffusing gypsum nor
       *    diffusing hemihydrate nor diffusing anhydrite,
       *    or p2diff was >= C3AGYP, or pixel was also
       *    not CaCl2 (regardless of p2diff)
       *
       *    Another alternative is that the pixel is
       *    diffusing CAS2.  Examine reaction with
       *    diffusing CAS2 to form stratlingite
       *
       *    Only allow reaction with diffusing CAS2
       ***/

    } else if (check == DIFFCAS2) {

      /* Convert diffusing CAS2 to stratlingite */

      Mic[xnew][ynew][znew] = STRAT;
      Count[STRAT]++;
      Count[DIFFCAS2]--;
      action = 0;

      /***
       *    Convert diffusing C3A to solid STRAT or else
       *    leave as a diffusing C3A
       ***/

      /*** ASK DALE ABOUT FACTOR OF 0.886 ***/
      nexp = 3;
      pexp = ran1(Seed);
      if (pexp <= 0.886) {
        Mic[xcur][ycur][zcur] = STRAT;
        Count[STRAT]++;
        Count[DIFFC3A]--;
        nexp--;
      } else {

        /***
         *    Indicate that diffusing species remains
         *    in current location
         ***/

        action = 7;
      }

      /***
       *    Perform expansion that occurs when
       *    stratlingite is formed
       *
       *    xexp, yexp and zexp are the coordinates
       *    of the last STRAT pixel to be added
       ***/

      xexp = xnew;
      yexp = ynew;
      zexp = znew;
      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extstrat(xexp, yexp, zexp, &poreid);

        /* Update xexp, yexp and zexp */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /* Probabilistic-based expansion for last STRAT pixel */

      /*** ASK DALE ABOUT FACTOR OF 0.286 ***/
      pexp = ran1(Seed);
      if (pexp <= 0.286) {
        newact = extstrat(xexp, yexp, zexp, &poreid);
      }
    }

    /***
     *    Done examining reactions with HEMIHYD, ANHYDRITE,
     *    CaCl2, and CAS2.  Now check for reaction with
     *    diffusing or solid ettringite to form AFm.
     *
     *    Reaction at solid ettringite only possible if
     *    ettringite is soluble and even then only with
     *    a probability C3AETTR < 1 to avoid formation
     *    of too much AFm when ettringite first becomes
     *    soluble.
     ***/

    pgrow = ran1(Seed);
    if ((check == DIFFETTR) ||
        ((check == ETTR) && (Soluble[ETTR] == 1) && (pgrow <= C3AETTR))) {

      /* Convert diffusing or solid ettringite to AFm */

      Mic[xnew][ynew][znew] = AFM;
      Count[AFM]++;
      Count[check]--;
      action = 0;

      /***
       *    Convert diffusing C3A to AFm or leave
       *    as diffusing C3A
       ***/

      /*** ASK DALE ABOUT FACTOR OF 0.2424 ***/

      pexp = ran1(Seed);
      if (pexp <= 0.2424) {
        Mic[xcur][ycur][zcur] = AFM;
        Count[AFM]++;
        Count[DIFFC3A]--;
        pafm = (-0.1);
      } else {

        /***
         *    Indicate that diffusing C3A remained at
         *    original location
         ***/

        action = 7;
        pafm = 0.04699;
      }

      /* Probabilistic-based expansion for new AFm pixel */

      pexp = ran1(Seed);
      if (pexp <= pafm) {
        extafm(xnew, ynew, znew, &poreid);
      }
    }

    /***
     *    Done checking for all possible reactions.  If none
     *    have happened, then attempt diffusion of the C3A
     *    pixel
     ***/

    if ((action != 0) && (action != 7)) {

      /***
       *    If diffusion is possible, execute it
       *    Allow diffusion into either POROSITY
       *    or CRACKP (i.e. saturated crack pore
       *    formed during hydration process)
       *    (24 May 2004)
       ***/

      if (check == POROSITY || check == CRACKP) {
        Mic[xcur][ycur][zcur] = check;
        Mic[xnew][ynew][znew] = DIFFC3A;
      } else {

        /***
         *    Indicate that diffusing C3A remained
         *    at original location
         ***/

        action = 7;
      }
    }
  }

  return (action); /* 7 if no action taken */
}

/***
 *    movec4a
 *
 *     Move a diffusing C4A pixel currently located
 *     at (xcur, ycur, zcur), with nucleation
 *    probability nucprob
 *
 *     Arguments:    Int coordinates of present location
 *                     xcur,ycur,zcur
 *                 Int flag indicating if this is the final
 *                     diffusion step
 *                 Float nucleation probability
 *                Int id of saturated porosity type in which diffusion is
 *occuring
 *
 *     Returns:    Int flag indicating action taken
 *                     (reaction/diffusion or no action)
 *
 *    Calls:        moveone, extc3ah6, extettr, extafm, extstrat,
 *                extfriedel
 *
 *    Called by:    hydrate
 ***/
int movec4a(int xcur, int ycur, int zcur, int finalstep, float nucprob) {
  int check, xnew, ynew, znew, action, sumgarb, sumold, poreid;
  int xexp, yexp, zexp, nexp, iexp, newact;
  float pgen, pexp, pafm, pgrow, p2diff;

  poreid = -1;

  /***
   *    First be sure that a diffusing C4A species
   *    is at (xcur,ycur,zcur)
   ***/

  if (Mic[xcur][ycur][zcur] != DIFFC4A) {
    action = 0;
    return (action);
  }

  /***
   *    Check for nucleation into solid C3AH6, which will
   *    occur with probability nucprob or with certainty if
   *    this is the final diffusion step
   ***/

  pgen = ran1(Seed);
  p2diff = ran1(Seed);

  if ((nucprob >= pgen) || (finalstep)) {
    action = 0;
    Mic[xcur][ycur][zcur] = C3AH6;
    Count[C3AH6]++;
    Count[DIFFC4A]--;

    /***
     *    Allow for probabilistic-based expansion of C3AH6
     *    crystal to account for volume stoichiometry
     ***/

    /*** ASK DALE ABOUT FACTOR OF 0.69 ***/

    pexp = ran1(Seed);
    if (pexp <= 0.69) {
      extc3ah6(xcur, ycur, zcur, &poreid);
    }

  } else {

    /* Determine new coordinates (using periodic boundaries) */

    xnew = xcur;
    ynew = ycur;
    znew = zcur;
    action = 0;
    sumold = 1;
    sumgarb = moveone(&xnew, &ynew, &znew, &action, sumold);
    if (!action) {
      fprintf(stderr, "\nERROR in movec4a: Value of action is %d", action);
      fflush(stderr);
    }

    check = Mic[xnew][ynew][znew];

    /***
     *    Check for growth of C3AH6 crystal, which will occur
     *    with probability C3AH6GROW if the diffusing C3A
     *    collides with a solid C3AH6 surface.  We choose
     *    C3AH6GROW < 1 in this case to attempt to promote
     *    ettringite formation and AFm formation
     ***/

    if (check == C3AH6) {

      pgrow = ran1(Seed);
      if (pgrow <= C3AH6GROW) {
        Mic[xcur][ycur][zcur] = C3AH6;
        Count[C3AH6]++;
        Count[DIFFC4A]--;
        action = 0;

        /***
         *    Allow for probabilistic-based expansion of C3AH6
         *    crystal to account for volume stoichiometry
         ***/

        /*** ASK DALE ABOUT FACTOR OF 0.69 (AGAIN) ***/

        pexp = ran1(Seed);
        if (pexp <= 0.69) {
          extc3ah6(xcur, ycur, zcur, &poreid);
        }
      }

      /***
       *    Examine reaction with diffusing gypsum to
       *    form ettringite
       *
       *    Only allow reaction with diffusing gypsum
       ***/

    } else if ((check == DIFFGYP) && (p2diff < C3AGYP)) {

      /* Convert diffusing gypsum to ettringite */

      Mic[xnew][ynew][znew] = ETTRC4AF;
      Count[ETTRC4AF]++;
      Count[DIFFGYP]--;
      action = 0;

      /***
       *    Convert diffusing C4A to solid ettringite
       *    or else leave as a diffusing C4A
       ***/

      /*** ASK DALE ABOUT FACTOR OF 0.40 ***/

      nexp = 2;
      pexp = ran1(Seed);
      if (pexp <= 0.40) {
        Mic[xcur][ycur][zcur] = ETTRC4AF;
        Count[ETTRC4AF]++;
        Count[DIFFC4A]--;
        nexp--;
      } else {

        /***
         *    Indicate that diffusing species
         *    remains in current location
         ***/

        action = 7;
      }

      /***
       *    Perform expansion that occurs when
       *    ettringite is formed
       *
       *    xexp, yexp and zexp are the coordinates of
       *    the last ettringite pixel to be added
       *    as we attempt to grow in an acicular
       *    crystal shape
       ***/

      xexp = xnew;
      yexp = ynew;
      zexp = znew;
      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extettr(xexp, yexp, zexp, 1, &poreid);

        /* Update xexp, yexp and zexp */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /* Probabilistic-based expansion for last ettringite pixel */

      pexp = ran1(Seed);
      if (pexp <= 0.30) {
        newact = extettr(xexp, yexp, zexp, 1, &poreid);
      }

      /***
       *    Either pixel is not diffusing gypsum or p2diff was
       *    >= C3AGYP.  One alternative is that the pixel is
       *    diffusing hemihydrate.
       *
       *    Examine reaction with diffusing hemihydrate
       *    to form ettringite
       *
       *    Only allow reaction with diffusing hemihydrate
       ***/

    } else if ((check == DIFFHEM) && (p2diff < C3AGYP)) {

      /* Convert diffusing hemihydrate to ettringite */

      Mic[xnew][ynew][znew] = ETTRC4AF;
      Count[ETTRC4AF]++;
      Count[DIFFHEM]--;
      action = 0;

      /***
       *    Convert diffusing C4A to solid ettringite
       *    or else leave as a diffusing C4A
       ***/

      /*** ASK DALE ABOUT FACTOR OF 0.5583 ***/

      nexp = 3;
      pexp = ran1(Seed);
      if (pexp <= 0.5583) {
        Mic[xcur][ycur][zcur] = ETTRC4AF;
        Count[ETTRC4AF]++;
        Count[DIFFC4A]--;
        nexp--;
      } else {

        /***
         *    Indicate that diffusing species
         *    remains in current location
         ***/

        action = 7;
      }

      /***
       *    Perform expansion that occurs when ettringite
       *    is formed
       *
       *    xexp, yexp and zexp are the coordinates of the
       *    last ettringite pixel to be added as we try to
       *    grow the ettringite in an acicular crystal shape
       ***/

      xexp = xnew;
      yexp = ynew;
      zexp = znew;
      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extettr(xexp, yexp, zexp, 1, &poreid);

        /* Update xexp, yexp and zexp */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /* Probabilistic-based expansion for last ettringite pixel */

      /*** ASK DALE ABOUT FACTOR OF 0.6053 ***/
      pexp = ran1(Seed);
      if (pexp <= 0.6053) {
        newact = extettr(xexp, yexp, zexp, 1, &poreid);
      }

      /***
       *    Either pixel is neither diffusing gypsum nor
       *    diffusing hemihydrate, or p2diff was >= C3AGYP.
       *    Another alternative is that the pixel is
       *    diffusing anhydrite.
       *
       *    Examine reaction with diffusing anhydrite
       *    to form ettringite
       *
       *    Only allow reaction with diffusing anhydrite
       ***/

    } else if ((check == DIFFANH) && (p2diff < C3AGYP)) {

      /* Convert diffusing anhydrite to ettringite */

      Mic[xnew][ynew][znew] = ETTRC4AF;
      Count[ETTRC4AF]++;
      Count[DIFFANH]--;
      action = 0;

      /***
       *    Convert diffusing C4A to solid ettringite
       *    or else leave as a diffusing C4A
       ***/

      nexp = 3;
      pexp = ran1(Seed);
      if (pexp <= 0.569) {
        Mic[xcur][ycur][zcur] = ETTRC4AF;
        Count[ETTRC4AF]++;
        Count[DIFFC4A]--;
        nexp--;
      } else {

        /***
         *    Indicate that diffusing species remains
         *    in current location
         ***/

        action = 7;
      }

      /***
       *    Perform expansion that occurs when ettringite
       *    is formed
       *
       *    xexp, yexp and zexp are the coordinates
       *    of the last ettringite pixel to be added
       *    as we try to grow in an acicular crystal shape
       ***/

      xexp = xnew;
      yexp = ynew;
      zexp = znew;
      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extettr(xexp, yexp, zexp, 1, &poreid);

        /* Update xexp, yexp and zexp */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /* Probabilistic-based expansion for last ettringite pixel */

      /*** ASK DALE ABOUT FACTOR OF 0.6935 ***/
      pexp = ran1(Seed);
      if (pexp <= 0.6935) {
        newact = extettr(xexp, yexp, zexp, 1, &poreid);
      }

      /***
       *    Either pixel is neither diffusing gypsum nor
       *    diffusing hemihydrate nor diffusing anhydrite,
       *    or p2diff was >= C3AGYP.
       *
       *    Another alternative is that the pixel is
       *    diffusing CaCl2.  Examine reaction with
       *    diffusing CaCl2    to form Friedel's salt
       *
       *    Only allow reaction with diffusing CaCl2
       ***/

    } else if (check == DIFFCACL2) {

      /* Convert diffusing C4A to Friedel's salt */

      Mic[xcur][ycur][zcur] = FRIEDEL;
      Count[FRIEDEL]++;
      Count[DIFFC4A]--;
      action = 0;

      /***
       *    Convert diffusing CACL2 to solid FRIEDEL or
       *    else leave as a diffusing CACL2
       ***/

      /*** ASK DALE ABOUT FACTOR OF 0.5793 ***/

      nexp = 2;
      pexp = ran1(Seed);
      if (pexp <= 0.5793) {
        Mic[xnew][ynew][znew] = FRIEDEL;
        Count[FRIEDEL]++;
        Count[DIFFCACL2]--;
        nexp--;
      }

      /***
       *    Perform expansion that occurs when Friedel's
       *    salt is formed
       *
       *    xexp, yexp and zexp are the coordinates of
       *    the last FRIEDEL pixel to be added
       ***/

      xexp = xnew;
      yexp = ynew;
      zexp = znew;
      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extfriedel(xexp, yexp, zexp, &poreid);

        /* Update xexp, yexp and zexp */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /* Probabilistic-based expansion for last FRIEDEL pixel */

      /*** ASK DALE ABOUT FACTOR OF 0.3295 ***/

      pexp = ran1(Seed);
      if (pexp <= 0.3295) {
        newact = extfriedel(xexp, yexp, zexp, &poreid);
      }

      /***
       *    Either pixel is neither diffusing gypsum nor
       *    diffusing hemihydrate nor diffusing anhydrite,
       *    or p2diff was >= C3AGYP, or pixel was also
       *    not CaCl2 (regardless of p2diff)
       *
       *    Another alternative is that the pixel is
       *    diffusing CAS2.  Examine reaction with
       *    diffusing CAS2 to form stratlingite
       *
       *    Only allow reaction with diffusing CAS2
       ***/

    } else if (check == DIFFCAS2) {

      /* Convert diffusing CAS2 to stratlingite */

      Mic[xnew][ynew][znew] = STRAT;
      Count[STRAT]++;
      Count[DIFFCAS2]--;
      action = 0;

      /***
       *    Convert diffusing C3A to solid STRAT or else
       *    leave as a diffusing C3A
       ***/

      /*** ASK DALE ABOUT FACTOR OF 0.886 ***/
      nexp = 3;
      pexp = ran1(Seed);
      if (pexp <= 0.886) {
        Mic[xcur][ycur][zcur] = STRAT;
        Count[STRAT]++;
        Count[DIFFC4A]--;
        nexp--;
      } else {

        /***
         *    Indicate that diffusing species remains
         *    in current location
         ***/

        action = 7;
      }

      /***
       *    Perform expansion that occurs when
       *    stratlingite is formed
       *
       *    xexp, yexp and zexp are the coordinates
       *    of the last STRAT pixel to be added
       ***/

      xexp = xnew;
      yexp = ynew;
      zexp = znew;
      for (iexp = 1; iexp <= nexp; iexp++) {

        newact = extstrat(xexp, yexp, zexp, &poreid);

        /* Update xexp, yexp and zexp */

        switch (newact) {
        case 1:
          xexp--;
          if (xexp < 0)
            xexp = (Xsyssize - 1);
          break;
        case 2:
          xexp++;
          if (xexp >= Xsyssize)
            xexp = 0;
          break;
        case 3:
          yexp--;
          if (yexp < 0)
            yexp = (Ysyssize - 1);
          break;
        case 4:
          yexp++;
          if (yexp >= Ysyssize)
            yexp = 0;
          break;
        case 5:
          zexp--;
          if (zexp < 0)
            zexp = (Zsyssize - 1);
          break;
        case 6:
          zexp++;
          if (zexp >= Zsyssize)
            zexp = 0;
          break;
        default:
          break;
        }
      }

      /* Probabilistic-based expansion for last STRAT pixel */

      /*** ASK DALE ABOUT FACTOR OF 0.286 ***/
      pexp = ran1(Seed);
      if (pexp <= 0.286) {
        newact = extstrat(xexp, yexp, zexp, &poreid);
      }
    }

    /***
     *    Done examining reactions with HEMIHYD, ANHYDRITE,
     *    CaCl2, and CAS2.  Now check for reaction with
     *    diffusing or solid ettringite to form AFm.
     *
     *    Reaction at solid ettringite only possible if
     *    ettringite is soluble and even then only with
     *    a probability C3AETTR < 1 to avoid formation
     *    of too much AFm when ettringite first becomes
     *    soluble.
     ***/

    pgrow = ran1(Seed);
    if ((check == DIFFETTR) ||
        ((check == ETTR) && (Soluble[ETTR] == 1) && (pgrow <= C3AETTR))) {

      /* Convert diffusing or solid ettringite to AFm */

      Mic[xnew][ynew][znew] = AFM;
      Count[AFM]++;
      Count[check]--;
      action = 0;

      /***
       *    Convert diffusing C4A to AFm or leave
       *    as diffusing C4A
       ***/

      /*** ASK DALE ABOUT FACTOR OF 0.2424 ***/

      pexp = ran1(Seed);
      if (pexp <= 0.2424) {
        Mic[xcur][ycur][zcur] = AFM;
        Count[AFM]++;
        Count[DIFFC4A]--;
        pafm = (-0.1);
      } else {

        /***
         *    Indicate that diffusing C3A remained at
         *    original location
         ***/

        action = 7;
        pafm = 0.04699;
      }

      /* Probabilistic-based expansion for new AFm pixel */

      pexp = ran1(Seed);
      if (pexp <= pafm) {
        extafm(xnew, ynew, znew, &poreid);
      }
    }

    /***
     *    Done checking for all possible reactions.  If none
     *    have happened, then attempt diffusion of the C3A
     *    pixel
     ***/

    if ((action != 0) && (action != 7)) {

      /***
       *    If diffusion is possible, execute it
       *    Allow diffusion into either POROSITY
       *    or CRACKP (i.e. saturated crack pore
       *    formed during hydration process)
       *    (24 May 2004)
       ***/

      if (check == POROSITY || check == CRACKP) {
        Mic[xcur][ycur][zcur] = check;
        Mic[xnew][ynew][znew] = DIFFC4A;
      } else {

        /***
         *    Indicate that diffusing C3A remained
         *    at original location
         ***/

        action = 7;
      }
    }
  }

  return (action); /* 7 if no action taken */
}

/***
 *    hydrate
 *
 *     Oversee hydration by updating position of all
 *     remaining diffusing species
 *
 *     Arguments:    Int final cycle flag
 *                 Int maximum number of diffusion steps per cycle
 *
 *     Returns:    Nothing
 *
 *    Calls:        movech, movec3a, movefh3, moveettr, movecsh,
 *                movegyp, movecas2, moveas, movecacl2
 *
 *    Called by:    hydrate
 ***/
void hydrate(int fincyc, int stepmax, float chpar1, float chpar2, float hgpar1,
             float hgpar2, float fhpar1, float fhpar2, float gypar1,
             float gypar2) {
  int xpl, ypl, zpl, phpl, agepl, xpnew, ypnew, zpnew;
  int istep, termflag, reactf;
  int nleft, ntodo, ndale;
  float chprob, c3ah6prob, fh3prob, gypprob;
  float beterm;
  struct Ants *curant, *antgone;

  reactf = 0;
  ntodo = nleft = Nmade;
  termflag = 0;

  /***
   *    Perform diffusion until all reacted or max. # of
   *    diffusion steps reached
   ***/

  for (istep = 1; ((istep <= stepmax) && (nleft > 0)); istep++) {

    if ((fincyc) && (istep == stepmax))
      termflag = 1;

    nleft = ndale = 0;

    /* Determine probabilities for CH and C3AH6 nucleation */

    beterm = exp(-(double)(Count[DIFFCH]) / chpar2);
    chprob = chpar1 * (1.0 - beterm);

    beterm = exp(-(double)(Count[DIFFC3A]) / hgpar2);
    c3ah6prob = hgpar1 * (1.0 - beterm);

    beterm = exp(-(double)(Count[DIFFFH3]) / fhpar2);
    fh3prob = fhpar1 * (1.0 - beterm);

    /***
     *    DIFFSO4 are diffusing sulfates that form from dissolution
     *    of K2SO4 or NA2SO4 (7 June 2004)
     ***/

    beterm = exp(-(double)(Count[DIFFANH] + Count[DIFFHEM] + Count[DIFFSO4]) /
                 gypar2);
    gypprob = gypar1 * (1.0 - beterm);

    /* Process each diffusing species in turn */

    curant = Headant->nextant;

    while (curant) {

      ndale++;
      xpl = curant->x;
      ypl = curant->y;
      zpl = curant->z;
      phpl = curant->id;
      agepl = curant->cycbirth;

      /***
       *    First ensure that ant is still at the position
       *    being examined
       ***/

      if (Mic[xpl][ypl][zpl] != phpl) {

        /* Remove ant from list */

        if (ndale == 1) {
          Headant->nextant = curant->nextant;
        } else {
          (curant->prevant)->nextant = curant->nextant;
        }

        if (curant->nextant) {
          (curant->nextant)->prevant = curant->prevant;
        } else {
          Tailant = curant->prevant;
        }

        antgone = curant;
        curant = curant->nextant;
        free(antgone);
        Ngoing--;

        /***
         *    Based on ID, call appropriate routine
         *    to process diffusing species
         ***/

      } else {

        switch (phpl) {
        case DIFFCSH:
          reactf = movecsh(xpl, ypl, zpl, termflag, agepl);
          break;
        case DIFFANH:
          reactf = moveanh(xpl, ypl, zpl, termflag, gypprob);
          break;
        case DIFFHEM:
          reactf = movehem(xpl, ypl, zpl, termflag, gypprob);
          break;
        case DIFFSO4:
          reactf = moveso4(xpl, ypl, zpl, termflag, gypprob);
          break;
        case DIFFCH:
          reactf = movech(xpl, ypl, zpl, termflag, chprob);
          break;
        case DIFFFH3:
          reactf = movefh3(xpl, ypl, zpl, termflag, fh3prob);
          break;
        case DIFFGYP:
          reactf = movegyp(xpl, ypl, zpl, termflag);
          break;
        case DIFFC3A:
          reactf = movec3a(xpl, ypl, zpl, termflag, c3ah6prob);
          break;
        case DIFFC4A:
          reactf = movec4a(xpl, ypl, zpl, termflag, c3ah6prob);
          break;
        case DIFFETTR:
          reactf = moveettr(xpl, ypl, zpl, termflag);
          break;
        case DIFFCACL2:
          reactf = movecacl2(xpl, ypl, zpl, termflag);
          break;
        case DIFFCAS2:
          reactf = movecas2(xpl, ypl, zpl, termflag);
          break;
        case DIFFAS:
          reactf = moveas(xpl, ypl, zpl, termflag);
          break;
        case DIFFCACO3:
          reactf = movecaco3(xpl, ypl, zpl, termflag);
          break;
        default:
          fprintf(stderr, "\nERROR in hydrate: ID of phase is %d", phpl);
          fflush(stderr);
          break;
        }

        /* If no reaction */

        if (reactf != 0) {

          nleft++;
          xpnew = xpl;
          ypnew = ypl;
          zpnew = zpl;

          /* Update location of diffusing species */

          switch (reactf) {
          case 1:
            xpnew--;
            if (xpnew < 0)
              xpnew = (Xsyssize - 1);
            break;
          case 2:
            xpnew++;
            if (xpnew >= Xsyssize)
              xpnew = 0;
            break;
          case 3:
            ypnew--;
            if (ypnew < 0)
              ypnew = (Ysyssize - 1);
            break;
          case 4:
            ypnew++;
            if (ypnew >= Ysyssize)
              ypnew = 0;
            break;
          case 5:
            zpnew--;
            if (zpnew < 0)
              zpnew = (Zsyssize - 1);
            break;
          case 6:
            zpnew++;
            if (zpnew >= Zsyssize)
              zpnew = 0;
            break;
          default:
            break;
          }

          /* Store new location of diffusing species */

          curant->x = xpnew;
          curant->y = ypnew;
          curant->z = zpnew;
          curant->id = phpl;
          curant = curant->nextant;

          /* End of react != 0 block */

        } else {

          /***
           *    Otherwise, there was a reaction that took
           *    the diffusing ant out of the game.
           *    Therefore, we must remove that annihiliated
           *    ant from the list
           ***/

          if (ndale == 1) {
            Headant->nextant = curant->nextant;
          } else {
            (curant->prevant)->nextant = curant->nextant;
          }

          if (curant->nextant) {
            (curant->nextant)->prevant = curant->prevant;
          } else {
            Tailant = curant->prevant;
          }

          antgone = curant;
          curant = curant->nextant;
          free(antgone);
          Ngoing--;
        }
      }

    } /* end of curant loop */

    ntodo = nleft;

  } /* end of istep loop */
}
