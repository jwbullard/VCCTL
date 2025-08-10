/***
 *	pHpred
 *
 * 	Predict the pH of the pore solution based on the
 * 	concentration of ions
 *
 *	Note that everything is being done on a
 *	one gram cement basis
 *
 * 	Arguments:	None
 *
 * 	Returns:	Nothing
 *
 *	Calls:		No other routines
 *	Called by:	disrealnew
 ***/

/***
 *	Molar masses of ions and oxides from sodium and potassium
 *
 *	Na = sodium, K = potassium
 ***/
#define MMNa 22.9898
#define MMK 39.102
#define MMNa2O 61.979
#define MMK2O 94.203

/***
 *	Basis for B factors must be adapted from 100 g to 1 g
 *
 *	Reference: Taylor, H.F.W., "A Method for Predicting Alkali Ion
 *		Concentrations in Cement Pore Solutions," Advances in
 *		Cement Research, Vol. 1, No. 1, 5-16, 1987.
 ***/

/* From Taylor paper in liters (31 mL/1000/ 100 g) */
#define BNa 0.00031

/* From Taylor paper in liters (20 mL/1000/ 100 g) */
#define BK 0.00020

/* From Taylor paper in liters (3 mL/1000/ 1 g silica) */
#define BprimeNa 0.0030

/* From Taylor paper in liters (3.3 mL/1000/ 1 g silica) */
#define BprimeK 0.0033

/* Ksp values for CH and gypsum */
/* Source: Reardon, Cement and Concrete Research, Vol. 20 (2), 175-192, 1990. */
#define KspCH25C 0.00000646
#define KspGypsum 0.0000263
#define Ksparcanite 0.016595869 /* added on 3 June 2004 */

/***
 *	Note: Thenardite, Na2SO4 is highly soluble in water, and no Ksp value is
 *	given for it (3 June 2004)
 ***/

/***
 *	Approximate Ksp value for syngenite is 1E-7
 *
 *	Reference: Gartner, Tang, and Weiss, JACerS,
 *		Vol. 68 (12), 667-673, 1985.
 *
 *	A more recent Ksp value for syngenite is 3.5E-8,
 *
 *	Reference: Reardon, Cement and Concrete Research,
 *	 	Vol. 20 (2), 175-192, 1990.
 ***/
/* #define KspSyngenite 0.00000004 */

#define KspSyngenite 0.00000010

/***
 *	Source: H.F.W. Taylor, Cement Chemistry, 2nd Edition.
 *		Telford Publishing, London, 1997.
 ***/
#define SpecgravSyngenite 2.607

/* Moles of K+ per mole of syngenite */
#define KperSyn 2.0

/* Some activity stuff */
#define activeA0 0.0366  /* A at 295 K (from Ken Snyder) */
#define activeB0 0.01035 /* B at 295 K (from Ken Snyder) */

/* z are the absolute charges (valences) per ion */
#define zCa 2.0
#define zSO4 2.0
#define zOH 1.0
#define zNa 1.0
#define zK 1.0

/* a is similar to an ionic radius (in Angstroms) */
#define aK 1.33
#define aCa 1.0
#define aOH 3.0
#define aNa 3.0
#define aSO4                                                                   \
  4.5 /***                                                                     \
       *	Estimated aSO4 as sum of S ionic                                      \
       *	radius and O ionic diameter                                           \
       ***/

/***
 *	Ionic conductivities
 *
 *	References:
 *
 *		K.A. Snyder, Feng, Keen, and T.O. Mason, Cement and Concrete
 *Research
 *
 *		CRC Hanbook of Chemistry and Physics (1983) pp. D-175
 *
 *	Pore solution conductivity = sum (zi * [i]*lambdai)
 *
 *	where	lambdai = (lambdai_0/(1.+Gi*(Istrength^0.5)))
 *	and     Istrength is in units of M (mol/L)
 *
 *	Units: S cm-cm eq.^(-1)
 ***/
#define lambdaOH_0 198.0
#define lambdaNa_0 50.1
#define lambdaK_0 73.5
#define lambdaSO4_0 39.5

/* Note that CRC has 60./2 for the following */
#define lambdaCa_0 29.5

/* Units for the following: (eq.^2 mol/L)^(-0.5) */
#define GOH 0.353
#define GK 0.548
#define GNa 0.733
#define GCa 0.771
#define GSO4 0.877

/* Conversion from cm2/Liter to 1/m */
#define cm2perL2m 0.1

#define EPSS 6.e-8
#define MAXIT 100

void laguer(fcomplex a[], int m, fcomplex *x, float eps, int polish) {
  int j, iter;
  float err, dxold, cdx, abx;
  fcomplex sq, h, gp, gm, g2, g, b, d, dx, f, x1;

  dxold = Cabs(*x);
  for (iter = 1; iter <= MAXIT; iter++) {
    b = a[m];
    err = Cabs(b);
    d = f = Complex(0.0, 0.0);
    abx = Cabs(*x);
    for (j = m - 1; j >= 0; j--) {
      f = Cadd(Cmul(*x, f), d);
      d = Cadd(Cmul(*x, d), b);
      b = Cadd(Cmul(*x, b), a[j]);
      err = Cabs(b) + abx * err;
    }
    err *= EPSS;
    if (Cabs(b) <= err)
      return;
    g = Cdiv(d, b);
    g2 = Cmul(g, g);
    h = Csub(g2, RCmul(2.0, Cdiv(f, b)));
    sq = Csqrt(RCmul((float)(m - 1), Csub(RCmul((float)m, h), g2)));
    gp = Cadd(g, sq);
    gm = Csub(g, sq);
    if (Cabs(gp) < Cabs(gm))
      gp = gm;
    dx = Cdiv(Complex((float)m, 0.0), gp);
    x1 = Csub(*x, dx);
    if (x->r == x1.r && x->i == x1.i)
      return;
    *x = x1;
    cdx = Cabs(dx);
    if (iter > 6 && cdx >= dxold)
      return;
    dxold = cdx;
    if (!polish)
      if (cdx <= eps * Cabs(*x))
        return;
  }
  bailout("disrealnew", "Too many iterations in routine LAGUER");
}

#undef EPSS
#undef MAXIT

#define EPS 2.0e-6
#define MAXM 100

void zroots(fcomplex a[], int m, fcomplex roots[], int polish) {
  int jj, j, i;
  fcomplex x, b, c, ad[MAXM];
  /* void laguer(); */

  for (j = 0; j <= m; j++)
    ad[j] = a[j];
  for (j = m; j >= 1; j--) {
    x = Complex(0.0, 0.0);
    laguer(ad, j, &x, EPS, 0);
    if (fabs(x.i) <= (2.0 * EPS * fabs(x.r)))
      x.i = 0.0;
    roots[j] = x;
    b = ad[j];
    for (jj = j - 1; jj >= 0; jj--) {
      c = ad[jj];
      ad[jj] = b;
      b = Cadd(Cmul(x, b), c);
    }
  }
  if (polish)
    for (j = 1; j <= m; j++)
      laguer(a, m, &roots[j], EPS, 1);
  for (j = 2; j <= m; j++) {
    x = roots[j];
    for (i = j - 1; i >= 1; i--) {
      if (roots[i].r <= x.r)
        break;
      roots[i + 1] = roots[i];
    }
    roots[i + 1] = x;
  }
}

#undef EPS
#undef MAXM

void pHpred(void) {
  int nt, j, syngen_change = 0, syn_old = 0;
  /* int ndissk2so4,ndissna2so4; */
  float sumbest, sumtest, pozzreact, KspCH;
  double mf3, vf3;
  double A, B, C, conctest, concsulfate1;
  double volpore, grams_cement;
  double test_precip;
  double Istrength, Anow, Bnow, Inew;
  double volfact, massfact;
  fcomplex coef[5], roots[5];

  /* Initialize local arrays */
  coef[0] = Complex(0.0, 0.0);
  coef[1] = Complex(0.0, 0.0);
  coef[2] = Complex(0.0, 0.0);
  coef[3] = Complex(0.0, 0.0);
  coef[4] = Complex(0.0, 0.0);
  roots[0] = Complex(0.0, 0.0);
  roots[1] = Complex(0.0, 0.0);
  roots[2] = Complex(0.0, 0.0);
  roots[3] = Complex(0.0, 0.0);
  roots[4] = Complex(0.0, 0.0);

  Conductivity = 0.0;
  Concnaplus = 0.0;
  Conckplus = 0.0;
  Concohminus = 0.0;

  if (Verbose_flag == 2)
    printf("\nIn pHpred...");

  /* Update CH activity product based on current system temperature */
  /* Factors derived from fitting CH solubility vs. temperature */
  /* data in Taylor book (p. 117) */

  KspCH = KspCH25C * (1.534385 - 0.02057 * Temp_cur);
  /***
   *	volfact is decimeters per pixel edge
   *	Note: 1 liter = 1 dm^3
   *	Note: Units of Res are microns per pixel, and there are
   *			0.00001 dm in one micron
   ***/

  volfact = ((double)Res) * 0.000010;

  /***
   *	massfact is centimeters per pixel edge
   *	Note: Units of Res are microns per pixel, and there are
   *			0.0001 cm in one micron
   ***/

  massfact = ((double)Res) * 0.00010;

  if (Conccaplus > 1.0)
    Conccaplus = 0.0;

  /***
   *	Calculate volume of pore solution in
   *	the concrete in Liters.  We choose NOT
   *	to include saturated porosity in cracks
   *	as part of the total saturated porosity
   *	(24 May 2004)
   ***/

  volpore = (double)Count[POROSITY];

  /* 0.38 is gel porosity in CSH.  Once thought to be 0.28 */
  volpore += ((double)CSH_Porosity) * ((double)Count[CSH]);

  /* 0.2 is porosity in pozzolanic-CSH */
  volpore += ((double)POZZCSH_Porosity) * ((double)Count[POZZCSH]);

  /* 0.2 is an educated guess for the porosity in slag-CSH */
  volpore += ((double)SLAGCSH_Porosity) * ((double)Count[SLAGCSH]);

  /***
   *	Convert from pixels (cubic micrometers) to
   *	Liters (cubic decimeters)
   ***/

  vf3 = volfact * volfact * volfact;

  volpore *= vf3;

  /* Compute pore volume PER GRAM OF CEMENT */

  mf3 = massfact * massfact * massfact;
  grams_cement = Cemmasswgyp * mf3;

  volpore /= grams_cement;

  /* Compute grams of pozzolan which have reacted */

  pozzreact = ((double)Nsilica_rx / 1.35) * mf3 * Specgrav[SFUME];

  /***
   *	Compute moles of released potassium and
   *	sodium PER GRAM OF CEMENT.  Used to have to do this
   *	as releasing 90 % of the readily soluble immediately,
   *	releasing the remaining 10 % of the readily soluble
   *	during the first hour, assuming that all
   *	readily soluble was	dissolved after one hour
   *
   *	Now, with readily soluble alkali tied directly to the
   *	number of pixels of NA2SO4 and K2SO4, it may be possible
   *	to do this more directly, except for fly ash phases,
   *	which still	have to be done the previous way.
   *
   *	Here is how you would do it if you were to base pore
   *	solution composition on the dissolution events
   ***/

  /*
  ndissk2so4 = Ksulfinit - Count[K2SO4];
  Releasedk = 2.0 * Potassiumhydrox;
  Releasedk += (2.0 * (((float)ndissk2so4 * Specgrav[K2SO4]) / Cemmasswgyp));
  Releasedk += (2.0 * (Totpotassium - Rspotassium) * Alpha_cur);
  */

  /*
  ndissna2so4 = Nasulfinit - Count[NA2SO4];
  Releasedna = 2.0 * Sodiumhydrox;
  Releasedna += (2.0 * (((float)ndissna2so4 * Specgrav[NA2SO4]) / Cemmasswgyp));
  Releasedna += (2.0 * (Totsodium - Rssodium) * Alpha_cur);
  */

  if (Time_cur > 1.0) {

    Rsk_released = Rspotassium;
    Rsna_released = Rssodium;

    /***
     *	Need to disable this next line IF we go to the
     *	k new way of calculating released k above
     ***/

    Releasedk = (2.0 * (Rspotassium + Potassiumhydrox +
                        (Totpotassium - Rsk_released) * Alpha_cur));

    Releasedk += (2.0 * (Flyashmass / Cemmasswgyp) *
                  (Rsfapotassium + (Totfapotassium - Rsfapotassium) *
                                       Alpha_fa_cur)); /* from fly ash */
    Releasedk /= MMK2O;

    /***
     *	Need to disable this next line IF we go to the
     *	new way of calculating released na above
     ***/
    Releasedna = (2.0 * (Rssodium + Sodiumhydrox +
                         (Totsodium - Rsna_released) * Alpha_cur));

    Releasedna += (2.0 * (Flyashmass / Cemmasswgyp) *
                   (Rsfasodium + (Totfasodium - Rsfasodium) * Alpha_fa_cur));
    Releasedna /= MMNa2O;

  } else {

    /***
     *	Proportion the early time release over the first hour:
     *
     *	90% immediately and the remaining 10% over the first hour
     *	(based on limited data from Davide Zampini (MBT))
     ***/

    /***
     *	Need to disable this next line IF we go to the
     *	 new way of calculating released k above
     ***/

    Rsk_released = (0.9 + 0.1 * Time_cur) * (Rspotassium);
    Rsna_released = (0.9 + 0.1 * Time_cur) * (Rssodium);

    Releasedk = (2.0 * (Potassiumhydrox + Rsk_released +
                        (Totpotassium - Rspotassium) * Alpha_cur));

    Releasedk += (2.0 * (Flyashmass / Cemmasswgyp) *
                  ((0.9 + 0.1 * Time_cur) * Rsfapotassium +
                   (Totfapotassium - Rsfapotassium) * Alpha_fa_cur));

    Releasedk /= MMK2O;

    /***
     *	Need to disable this next line IF we go to the
     *	 new way of calculating released na above
     ***/
    Releasedna = (2.0 * (Sodiumhydrox + Rsna_released +
                         (Totsodium - Rssodium) * Alpha_cur));

    Releasedna += (2.0 * (Flyashmass / Cemmasswgyp) *
                   ((0.9 + 0.1 * Time_cur) * Rsfasodium +
                    (Totfasodium - Rsfasodium) * Alpha_fa_cur));

    Releasedna /= MMNa2O;
  }

  /***
   *	Compute concentrations of K+ and Na+ in pore
   *	solution currently
   *
   *	Remember to decrease K+ by:
   *
   *		KperSyn * (moles of syngenite precipitated)
   *
   *	Units must be in moles/gram for both
   ****/

  Conckplus = ((Releasedk - Moles_syn_precip * KperSyn) /
               (volpore + BK * Alpha_cur + BprimeK * pozzreact));

  Concnaplus =
      (Releasedna) / (volpore + BNa * Alpha_cur + BprimeNa * pozzreact);

  /* Do the following loop while Syngenite is precipitating */

  if (Verbose_flag == 2)
    printf("\nConckplus and Concnaplus are %f and %f", Conckplus, Concnaplus);

  do {

    if (Verbose_flag == 2)
      printf("\nIn syngenite precipitation loop.");
    /***
     *	Now compute the activities (estimated)
     *	of Ca++ and OH-
     ***/

    ActivityCa = ActivityOH = ActivitySO4 = ActivityK = 1.0;
    Inew = 0.0;

    if (Verbose_flag == 2) {
      printf("\nConcnaplus = %f", Concnaplus);
      printf("\nConckplus = %f", Conckplus);
      printf("\nIs ettringite soluble? ");
      if (!Soluble[ETTR]) {
        printf("NO (ETTR is %d)\n", ETTR);
      } else {
        printf("YES (ETTR is %d)\n", ETTR);
      }
      fflush(stdout);
    }
    if (((Concnaplus + Conckplus) > 0.0) && (!Soluble[ETTR])) {

      if (Verbose_flag == 2)
        printf("\nEttringite not soluble.");

      /* Factor of 1000 to convert from M to mmol/L */

      Istrength = (zK * zK * Conckplus);
      Istrength += (zNa * zNa * Concnaplus);
      Istrength += (zCa * zCa * Conccaplus);
      Istrength *= 1000.0;

      if (Istrength < 1.0)
        Istrength = 1.0;

      nt = 0;
      while (((fabs(Istrength - Inew) / Istrength) > 0.10) && nt < 10000) {

        nt++;
        Istrength = (zK * zK * Conckplus);
        Istrength += (zNa * zNa * Concnaplus);
        Istrength += (zCa * zCa * Conccaplus);
        Istrength *= 1000.0;

        if (Istrength < 1.0)
          Istrength = 1.0;

        Anow = activeA0 * 295.0 * sqrt(295.0) /
               ((Temp_cur + 273.15) * sqrt(Temp_cur + 273.15));

        Bnow = activeB0 * sqrt(295.0) / (sqrt(Temp_cur + 273.15));

        /* Equations from papers of Marchand et al. */

        /* Ca cation activity */

        ActivityCa = (-Anow * zCa * zCa * sqrt(Istrength)) /
                     (1.0 + (aCa * Bnow * sqrt(Istrength)));

        ActivityCa += (0.2 - (0.0000417 * Istrength)) * Anow * zCa * zCa *
                      Istrength / sqrt(1000.0);

        ActivityCa = exp(ActivityCa);

        /* (OH) anion activity */

        ActivityOH = (-Anow * zOH * zOH * sqrt(Istrength)) /
                     (1.0 + (aOH * Bnow * sqrt(Istrength)));

        ActivityOH += (0.2 - 0.0000417 * Istrength) * Anow * zOH * zOH *
                      Istrength / sqrt(1000.0);

        ActivityOH = exp(ActivityOH);

        /* K cation activity */

        ActivityK = (-Anow * zK * zK * sqrt(Istrength)) /
                    (1.0 + (aK * Bnow * sqrt(Istrength)));

        ActivityK += (0.2 - 0.0000417 * Istrength) * Anow * zK * zK *
                     Istrength / sqrt(1000.0);

        ActivityK = exp(ActivityK);

        /* SO4 anion activity */

        ActivitySO4 = (-Anow * zSO4 * zSO4 * sqrt(Istrength)) /
                      (1.0 + (aSO4 * Bnow * sqrt(Istrength)));

        ActivitySO4 += (0.2 - 0.0000417 * Istrength) * Anow * zSO4 * zSO4 *
                       Istrength / sqrt(1000.0);

        ActivitySO4 = exp(ActivitySO4);

        /***
         *	Now try to find roots of quartic
         *	polynomial to determine sulfate, OH-,
         *	and calcium ion concentrations
         *
         *	A = (-KspCH)
         *
         *	Now with activities
         ***/

        /***
         *	LOOK OUT!  KspCH likely to depend on pore
         *	solution composition itself, but it is treated
         *	here as if it does not.  Also all the Ksps should
         *	depend on temperature, but in the model this
         *	is taken into account only for CH
         ***/

        A = (-(KspCH) / (ActivityCa * ActivityOH * ActivityOH));
        B = Conckplus + Concnaplus;
        C = (-2.0 * KspGypsum / (ActivityCa * ActivitySO4));

        Concohminus = Conckplus + Concnaplus;

        coef[0] = Complex(C, 0.0);
        coef[1] = Complex((A + 2. * B * C) / C, 0.0);
        coef[2] = Complex(B * B / C + 4., 0.0);
        coef[3] = Complex(4. * B / C, 0.0);
        coef[4] = Complex(4. / C, 0.0);

        roots[1] = Complex(0.0, 0.0);
        roots[2] = Complex(0.0, 0.0);
        roots[3] = Complex(0.0, 0.0);
        roots[4] = Complex(0.0, 0.0);

        /* roots represent Ca++ concentration */

        zroots(coef, 4, roots, 1);

        sumbest = 100;

        /***
         *	Find the best real root for
         *	electoneutrality
         ***/

        if (Verbose_flag == 2)
          printf("\nHoping to print out the roots now\n");
        for (j = 1; j <= 4; j++) {

          if (Verbose_flag == 2)
            printf("pH root %d is (%f,%f)\n", j, roots[j].r, roots[j].i);

          if (((roots[j].i) == 0.0) && ((roots[j].r) > 0.0)) {

            /* conctest is the computed OH- concentration */

            conctest = sqrt(
                KspCH / (roots[j].r * ActivityCa * ActivityOH * ActivityOH));

            concsulfate1 = KspGypsum / (roots[j].r * ActivityCa * ActivitySO4);

            sumtest = Concnaplus + Conckplus;
            sumtest += 2.0 * roots[j].r;
            sumtest -= conctest;
            sumtest -= 2.0 * concsulfate1;

            if (fabs(sumtest) < sumbest) {
              sumbest = fabs(sumtest);
              Concohminus = conctest;
              Conccaplus = roots[j].r;
              Concsulfate = concsulfate1;
            }
          }
        }

        /* Update ionic strength */

        Inew = (zK * zK * Conckplus);
        Inew += (zNa * zNa * Concnaplus);
        Inew += (zCa * zCa * Conccaplus);
        Inew *= 1000.0;

      } /* end of while loop for Istrength-Inew */
      if (nt >= 10000) {
        printf("\npHpred was caught in an infinite loop with insoluble "
               "ettringite.");
        fflush(stdout);
      }

    } else {
      if (Verbose_flag == 2)
        printf("\nEttringite is soluble or alkali concentration is zero.");

      /* Factor of 1000 to convert from M to mmol/L */

      Istrength = (zK * zK * Conckplus);
      Istrength += (zNa * zNa * Concnaplus);
      Istrength += (zCa * zCa * Conccaplus);
      Istrength *= 1000.0;

      if (Istrength < 1.0)
        Istrength = 1.0;

      nt = 0;
      while (((fabs(Istrength - Inew) / Istrength) > 0.10) && nt < 10000) {

        nt++;
        Istrength = (zK * zK * Conckplus);
        Istrength += (zNa * zNa * Concnaplus);
        Istrength += (zCa * zCa * Conccaplus);
        Istrength *= 1000.0;

        Anow = activeA0 * 295.0 * sqrt(295.0) /
               ((Temp_cur + 273.15) * sqrt(Temp_cur + 273.15));

        Bnow = activeB0 * sqrt(295.0) / (sqrt(Temp_cur + 273.15));

        /* Equations from papers of Marchand et al. */

        /* Ca cation activity */

        ActivityCa = (-Anow * zCa * zCa * sqrt(Istrength)) /
                     (1.0 + (aCa * Bnow * sqrt(Istrength)));

        ActivityCa += (0.2 - (0.0000417 * Istrength)) * Anow * zCa * zCa *
                      Istrength / sqrt(1000.0);

        ActivityCa = exp(ActivityCa);

        /* (OH) anion activity */

        ActivityOH = (-Anow * zOH * zOH * sqrt(Istrength)) /
                     (1.0 + (aOH * Bnow * sqrt(Istrength)));

        ActivityOH += (0.2 - (0.0000417 * Istrength)) * Anow * zOH * zOH *
                      Istrength / sqrt(1000.0);

        ActivityOH = exp(ActivityOH);

        /* K cation activity */

        ActivityK = (-Anow * zK * zK * sqrt(Istrength)) /
                    (1.0 + (aK * Bnow * sqrt(Istrength)));

        ActivityK += (0.2 - (0.0000417 * Istrength)) * Anow * zK * zK *
                     Istrength / sqrt(1000.0);

        ActivityK = exp(ActivityK);

        /***
         *	Calculate pH by assuming simply that
         *	(OH)- balances the sum of Na+ and K+
         ***/

        Concohminus = Conckplus + Concnaplus;

        if ((Conccaplus) > (0.1 * (Concohminus))) {
          Concohminus += (2.0 * Conccaplus);
        }

        Conccaplus = (KspCH / (ActivityCa * ActivityOH * ActivityOH *
                               Concohminus * Concohminus));

        Concsulfate = 0.0;

        /* Update ionic strength */

        Inew = (zK * zK * Conckplus);
        Inew += (zNa * zNa * Concnaplus);
        Inew += (zCa * zCa * Conccaplus);
        Inew *= 1000.0;

      } /* end of while loop for Istrength-Inew */
      if (nt >= 10000) {
        printf(
            "\npHpred was caught in an infinite loop with soluble ettringite.");
        fflush(stdout);
      }
    }

    /* Check for syngenite precipitation */

    syngen_change = 0;

    if (syn_old != 2) {

      test_precip = Conckplus * Conckplus * ActivityK * ActivityK;
      test_precip *= Conccaplus * ActivityCa;
      test_precip *= Concsulfate * Concsulfate * ActivitySO4 * ActivitySO4;

      if (test_precip > KspSyngenite) {

        if (Verbose_flag == 2)
          printf("Syngenite precipitating at cycle %d\n", Cyccnt);
        syngen_change = syn_old = 1;

        /***
         *	Units of moles_syn_precip are moles
         *	PER GRAM OF CEMENT
         ***/

        if (Conckplus > 0.002) {

          Conckplus -= 0.001;
          Moles_syn_precip += (0.001 * volpore / KperSyn);

        } else if (Conckplus > 0.0002) {

          Conckplus -= 0.0001;
          Moles_syn_precip += (0.0001 * volpore / KperSyn);

        } else {
          Moles_syn_precip += (Conckplus * volpore / KperSyn);
          Conckplus = 0.0;
        }
      }

      /***
       *	Check for syngenite dissolution---
       *
       *	How to control dissolution rates???
       *
       *		Have 0.001 * KperSyn increase in Conckplus each cycle
       *
       *		Only one dissolution per cycle --- purpose of syn_old.
       *
       *	Also, allow NO dissolution if if some precipitation already
       *	took place in that cycle
       ***/

      if ((!syn_old) && (Moles_syn_precip > 0.0)) {

        syngen_change = syn_old = 2;

        /*
        Conckplus += (Moles_syn_precip / 10.0) / volpore;
        */

        if ((Moles_syn_precip / volpore) > 0.001) {

          Conckplus += (0.001 * KperSyn);
          Moles_syn_precip -= (0.001 * volpore);

        } else {

          Conckplus += (Moles_syn_precip * KperSyn / volpore);
          Moles_syn_precip = 0.0;
        }
      }
    }

  } while (syngen_change != 0);

  /* End of syngenite precipitation loop */

  if (Verbose_flag == 2)
    printf("\nDone with syngenite precipitation.");

  if (Concohminus < (0.0000001)) {

    Concohminus = 0.0000001;
    Conccaplus = (KspCH / (ActivityCa * ActivityOH * ActivityOH * Concohminus *
                           Concohminus));
  }

  PH_cur = 14.0 + log10(Concohminus * ActivityOH);

  /***
   *	Calculation of solution conductivity
   *	Reference: K.A. Snyder, Feng, Keen, and Mason, Cement and Concrete
   *Research, 2003
   *
   *	First convert ionic strength back to M units
   ***/

  Istrength /= 1000.0;

  Conductivity +=
      zCa * Conccaplus * (lambdaCa_0 / (1.0 + GCa * sqrt(Istrength)));

  Conductivity +=
      zOH * Concohminus * (lambdaOH_0 / (1.0 + GOH * sqrt(Istrength)));

  Conductivity +=
      zNa * Concnaplus * (lambdaNa_0 / (1.0 + GNa * sqrt(Istrength)));

  Conductivity += zK * Conckplus * (lambdaK_0 / (1.0 + GK * sqrt(Istrength)));

  Conductivity +=
      zSO4 * Concsulfate * (lambdaSO4_0 / (1.0 + GSO4 * sqrt(Istrength)));

  Conductivity *= cm2perL2m;

  return;
}
