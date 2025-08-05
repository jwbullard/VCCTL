/******************************************************
 *
 * Program disrealnew.c to hydrate three-dimensional cement
 * and gypsum particles in a 3-D box with periodic boundaries.
 * Uses cellular automata techniques and preserves correct
 * hydration volume stoichiometry.
 *
 * History of modifications:
 *
 *     (1) Heat of formation data added 12/92
 *     (2) 3D version created 7/94
 *     (3) General C version created 8/94
 *     (4) Modified to have pseudo-continuous dissolution 11/94
 *     (5) In this program, dissolved silicates are located close
 *            to dissolution source within a 17*17*17 box centered
 *            at dissolution source
 *     (6) Hydration under self-desiccating conditions included 9/95
 *     (7) Additions for adiabatic hydration conditions included 9/96
 *     (8) Adjustments for pozzolanic reaction included 11/96
 *     (9) Additions for calcium chloride to Friedel's salt added 4/97
 *    (10) Additions for stratlingite formation added 4/97
 *    (11) Additions for anhydrite to gypsum conversion added 5/97
 *    (12) Additions for calcium aluminodisilicate added 7/97
 *    (13) Ettringite unstable above 70 C added 9/98
 *    (14) Hemihydrate to gypsum conversion added 9/98
 *    (15) Decided to base Alpha only on four major clinker phases 9/98
 *    (16) Updated dissolution to allow next nearest neighbors, etc. 9/98
 *    (17) Created stable iron-rich ettringite 3/99
 *    (18) Phases renumbered 1/00
 *    (19) Changed Cshscale to 70000 to better model induction CS 6/01
 *    (20) Sulfate reactions modified by Claus-Jochen Haecker 6/00
 *    (21) Reactions between CaCO3 and Afm phase added 8/00
 *    (22) Slag incorporation 2/01
 *    (23) pH and pore solution concentration added 8/01
 *    (24) Influence of pH on hydration added 2/13/02
 *    (25) Surface retardation added 3/28/02
 *    (26) Critical amount of CSH needed to end induction changed from
 *            mass basis to volume basis 7/10/02
 *    (27) Allow formation of a crack in the microstructure at
 *            any cycle during hydration.  User specifies crack
 *            width and orientation, as well as the cycle at which
 *            to form the crack 5/24/04
 *    (28) Incorporate Na2SO4 (thenardite) and K2SO4 (arcanite)
 *            as solid phases which can dissolve and influence the
 *            pore solution composition 6/4/04
 *    (29) Allow different initial temperature for fictitious
 *            aggregate particles 11/15/04
 *    (30) Allow input of continuous isothermal calorimetry data
 *            for calibration of kinetics, to partially supplant
 *            the time conversion factor 6/29/07
 *    (31) More robust fitting to calorimetry data and chemical
 *            shrinkage data 3/6/13
 *    (32) Changed Cshscale to 35000, 12/22/2021
 *    (33) Added ability for and CSH CH to nucleate on silica
 *            fume, 12/22/2021
 *
 * Other notes:
 *
 *     (a) Temperature-variable C-S-H properties added 8/98
 *            molar volumes and water consumption based on values
 *            given in Geiker thesis on chemical shrinkage
 *     (b) Modelling of induction period based on an impermeable layer
 *            theory
 *
 * Programmers:   Dale P. Bentz and Jeffrey W. Bullard
 *                Engineering Laboratory
 *                NIST
 *                100 Bureau Drive Mail Stop 8621
 *                Gaithersburg, MD  20899-8621   USA
 *                (301) 975-5865      FAX: (301) 990-6891
 *                E-mail: dale.bentz@nist.gov
 *
 * Contact:       Jeffrey W. Bullard
 *                Zachry Department of Civil and Environmental Engineering
 *                Department of Materials Science and Engineering
 *                Texas A&M University
 *                3136 TAMU
 *                College Station, TX  77845   USA
 *                (979) 458-6482
 *                E-mail: jwbullard@tamu.edu
 *******************************************************/
#include "disrealnew.h"
#include "include/vcctl.h"
#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/***
 *    Function declarations
 ***/
void checkargs(int argc, char *argv[]);
int get_input(float *pnucch, float *pscalech, float *pnuchg, float *pscalehg,
              float *pnucfh3, float *pscalefh3, float *pnucgyp,
              float *pscalegyp, int *nmovstep);
void init(void);
int initialize_output_files(void);
void manage_deactivation_behavior(void);
void performdeactivation(int pid, float fracdeact);
void performreactivation(int pid, float fracreact, int finalreact);
int chckedge(int phase, int xck, int yck, int zck);
void resetcrackpores(void);
void passone(int low, int high, int cycid, int cshexflag);
int countphase(int phid);
int loccsh(int xcur, int ycur, int zcur, int sourcepore);
int countbox(int boxsize, int qx, int qy, int qz);
void makeinert(int ndesire);
void extslagcsh(int xpres, int ypres, int zpres);
void dissolve(int cycle);
void addrand(int randid, int nneed, int onepixfloc);
void addcrack();
void addseeds(int phid, float prob);
void calcT(double mass);
void measuresurf(void);
void findnewtime(float dval, float act_nrg, float *previousUncorrectedTime,
                 char *typestring);
void createfittocycles(void);
void freeallmem(void);

/***
 *    Supplementary programs
 ***/
#include "include/burn3d.h"     /* percolation of porosity assessment */
#include "include/burnset.h"    /* set point assessment */
#include "include/hydrealnew.h" /* hydration execution */
#include "include/pHpred.h"     /* pore solution pH prediction */
#include "include/parthyd.h"    /* particle hydration assessment */
#include "include/properties.h" /* Physical properties of the phases */

int main(int argc, char *argv[]) {
  int ntimes, valin, nmovstep;
  int cycflag, ix, iy, iz;
  int pixtmp, i, j, k;
  int customentry;
  float pnucch, pscalech, pnuchg, pscalehg, pnucfh3, pscalefh3;
  float psfact, betfact, pnucgyp, pscalegyp;
  float thtimelo, thtimehi, thtemplo, thtemphi;
  float kslag;
  float act_nrg, recip_Tdiff, tmod, smod;
  float dval, previousUncorrectedTime;
  double gfloat, space, mass_cement, mass_cem_now, mass_cur, kpozz;
  char typestring[MAXSTRING];
  char strsuff[MAXSTRING], strsuffa[MAXSTRING], strsuffb[MAXSTRING];
  char buff[MAXSTRING], instring[MAXSTRING];
  FILE *outfile, *thfile;

  /* Initialize global arrays */

  for (ix = 0; ix <= NPHASES; ix++) {
    Discount[ix] = Count[ix] = 0;
  }

  for (ix = 0; ix < 3; ix++) {
    Nphc[ix] = 0;
    Indx[ix] = 0;
    Bvec[ix] = 0.0;
    Con_fracp[ix] = 0.0;
    Con_fracs[ix] = 0.0;
  }

  for (ix = 0; ix <= NSPHASES; ix++) {
    PHcoeff[ix][0] = 0.0;
    PHcoeff[ix][1] = 0.0;
    PHcoeff[ix][2] = 0.0;
    FitpH[ix][0][0] = 0.0;
    FitpH[ix][0][1] = 0.0;
    FitpH[ix][0][2] = 0.0;
    FitpH[ix][1][0] = 0.0;
    FitpH[ix][1][1] = 0.0;
    FitpH[ix][1][2] = 0.0;
  }

  Antsize = sizeof(struct Ants);
  Togosize = sizeof(struct Togo);
  Alksulfsize = sizeof(struct Alksulf);

  cycflag = 0;

  thtimelo = thtimehi = thtemplo = thtemphi = 0.0;
  thfile = NULL;

  checkargs(argc, argv);

  /*
      printf("Enter name of progress file: \n");
      read_string(instring,sizeof(instring));
      sprintf(Progfilename,"%s",instring);
  */

  printf("\nExecuting disrealnew now...\n");
  if (get_input(&pnucch, &pscalech, &pnuchg, &pscalehg, &pnucfh3, &pscalefh3,
                &pnucgyp, &pscalegyp, &nmovstep)) {
    printf("\nForced to exit prematurely\n");
    exit(1);
  }

  ntimes = (int)Maxdiffsteps;

  init();

  /***
   *    Open and read temperature history file
   ***/

  if (Adiaflag == 2) {
    sprintf(buff, "%stemphist.dat", Outputdir);
    thfile = filehandler("disrealnew", buff, "READ");
    if (!thfile) {
      freeallmem();
      exit(1);
    }
    fscanf(thfile, "%s", instring);
    thtimelo = atof(instring);
    fscanf(thfile, "%s", instring);
    thtimehi = atof(instring);
    fscanf(thfile, "%s", instring);
    thtemplo = atof(instring);
    fscanf(thfile, "%s", instring);
    thtemphi = atof(instring);
    if (Verbose)
      printf("%f %f %f %f\n", thtimelo, thtimehi, thtemplo, thtemphi);
  }

  /***
   *    Set up names for output files, and
   *    print headers where necessary
   ***/

  if (initialize_output_files()) {
    freeallmem();
    bailout("disrealnew", "Could not open file");
    exit(1);
  }

  /***
   *    Krate is the rate constant relative to 298.15 K
   *    E_act must be given here in kJ/mole/K
   *
   *    1000.0 is a unit conversion factor from kJ to J
   *    8.314 is the gas constant in SI units
   *    273.15 is the additive constant to convert C to K
   *    298.15 is the reference temperature for the system, to
   *        which all other temperatures are referenced when
   *        computing changes in rate constants due to thermal
   *        activation.
   ***/

  act_nrg = 1000.0 * E_act / 8.314;

  recip_Tdiff = (1.0 / (Temp_cur_b + 273.15)) - (1.0 / 298.15);
  Krate = exp(-(act_nrg * recip_Tdiff));

  /* Calculate pozzolanic and slag reaction rate constants */

  act_nrg = 1000.0 * E_act_pozz / 8.314;
  kpozz = exp(-(act_nrg * recip_Tdiff));

  act_nrg = 1000.0 * E_act_slag / 8.314;
  kslag = exp(-(act_nrg * recip_Tdiff));

  /***
   *    Modify probability of pozzolanic reaction
   *    based on ratio of pozzolanic reaction rate
   *    to hydration rate
   ***/

  /***
   *    Modify silica fume probabilities first.  There are
   *    two effects postulated:
   *    1. Early age effect due to nucleating capability
   *       of silica fume with high BET values
   *    2. Later age pozzolanic reactivity due to
   *       SiO2 content of the silica fume (Psfume)
   ***/

  /** Late age effect dictated by Psfume **/
  /** Psfume is for converting DIFFCH to POZZCSH **/

  Psfume = PSFUME * (kpozz / Krate);
  psfact = (SF_SiO2_val) / (SF_SiO2_normal);
  betfact = (SF_BET_val) / (SF_BET_normal);
  Psfume *= (3.0 * psfact * psfact * betfact);
  if (Psfume > 1.0)
    Psfume = 1.0;
  LOI_factor = 25.0 * (SF_LOI_val / SF_LOI_normal);
  if (LOI_factor < 1.0)
    LOI_factor = 1.0;

  if (Verbose)
    printf("\n01. Psfume = %f", Psfume);

  Pamsil = PAMSIL * (kpozz / Krate);

  /* ASSUME same holds for dissolution of fly ash phases */

  Disprob[ASG] = Disbase[ASG] * (kpozz / Krate);
  Disprob[CAS2] = Disbase[CAS2] * (kpozz / Krate);

  /* Modify probability of slag dissolution */

  Disprob[SLAG] = Slagreact * Disbase[SLAG] * (kslag / Krate);

  /* Set initial properties of CSH */

  Molarvcsh[0] = Molarv[CSH];
  Watercsh[0] = Waterc[CSH];

  /* Modify probability that CSH grows at POROSITY because of seeding */
  /*  First calculate volume of saturated porosity.  Units of Csh_seeds */
  /*  is number per um3, so it is automatically a probability of a voxel */
  /*  being a seed */

  PCSHseednuc = Csh_seeds;
  if (PCSHseednuc > 1.0)
    PCSHseednuc = 1.0;

  printf("\nProbability of CSH growing on a seed in solution = %f",
         PCSHseednuc);

  /* Add CSH one-pixel particles randomly throughout the pore solution */

  addseeds(CSH, PCSHseednuc);

  /***
   *    Initial surface counts of cement
   ***/

  measuresurf();

  /***
   *    This is the MAIN loop over hydration cycles
   ***/

  Time_cur = 0.0;
  NextMovieTime = Time_cur + MovieFrameFreq;
  NextImageTime = Time_cur + OutTimefreq;
  NextBurnTime = Time_cur + Burntimefreq;
  NextSetTime = Time_cur + Settimefreq;
  NextPhydTime = Time_cur + Phydtimefreq;

  customentry = 0;
  previousUncorrectedTime = 0.0;

  for (Icyc = 1;
       ((Icyc <= Ncyc) && (Alpha_cur < Alpha_max) && (Time_cur < End_time));
       Icyc++) {

    /* Write progress to progress file */

    /*
            Fprog = filehandler("genmic",Progfilename,"WRITE");
            fprintf(Fprog,"%d\t%d",Icyc,Ncyc);
            fclose(Fprog);
    */

    if (Verbose) {
      printf("\nCycle %d\n", Icyc);
      printf("Binder Temp = %f", Temp_cur_b);
      if (Mass_agg > 0.0) {
        printf("; Aggregate Temp = %f\n", Temp_cur_agg);
      } else {
        Temp_cur_agg = Temp_cur_b;
        printf("\n");
      }
    }

    /***
     *    Handle deactivation of surfaces if necessary
     ***/

    if (Numdeact > 0) {
      manage_deactivation_behavior();
    }

    if (Temp_cur_b <= 80.0) { /* T units in deg C */

      tmod = (Temp_cur_b - 20.0) / (80.0 - 20.0);

    } else {

      tmod = 1.0;
    }

    Molarvcsh[Icyc] = Molarv[CSH] + (Molarvcshcoeff_T * tmod);
    Watercsh[Icyc] = Waterc[CSH] + (Watercshcoeff_T * tmod);

    if (Icyc == Ncyc || Alpha_cur >= Alpha_max || Time_cur >= End_time)
      cycflag = 1;

    /***
     *    Dissolve necessary pixels and form
     *    ants for diffusion
     ***/

    dissolve(Icyc);

    /***
     *  Calculate volume ratio of sulfates to C3A on first cycle only
     *  This must be done after dissolve because only then are the initial
     *  counts of each phase available
     ***/

    if (Icyc == 1) {
      SulftoC3A =
          ((float)(Ncsbar + Heminit + Anhinit)) / ((float)(C3ainit + Oc3ainit));
      if (SulftoC3A <= 0.8) {
        smod = 0.0;
      } else if (SulftoC3A <= 1.25) {
        smod = (SulftoC3A - 0.8) / (1.25 - 0.8);
      } else {
        smod = 1.0;
      }
      printf("\n\n\n******SulftoC3A = %f", SulftoC3A);
      printf("\n\n\n******Just changed Molarvcsh from %f ", Molarv[CSH]);
      Molarv[CSH] += (Molarvcshcoeff_sulf * smod);
      printf("to %f ***************\n\n\n", Molarv[CSH]);
      fflush(stdout);
    }

    if (Verbose) {
      printf("Number dissolved this pass- %d ", Nmade);
      printf("total diffusing- %d \n", Ngoing);

      if (Icyc == 1) {
        printf("Ncsbar is %d   Netbar is %d \n", Ncsbar, Netbar);
      }
      fflush(stdout);
    }

    hydrate(cycflag, ntimes, pnucch, pscalech, pnuchg, pscalehg, pnucfh3,
            pscalefh3, pnucgyp, pscalegyp);

    /* Cement + aggregate +water + filler=1;  that's all there is */

    mass_cement = 1.0 - (Mass_agg + Mass_fill + Mass_water + Mass_CH);
    mass_cem_now = mass_cement;

    /***
     *    Handle adiabatic case first
     ***/

    if (Adiaflag == 1) {

      /***
       *    Determine heat capacity of current mixture,
       *    accounting for imbibed water if necessary
       ***/

      if (Sealed == 1) {

        /* Accounting for aggregate separately (15 Nov 2004) */

        Cp_b = Cp_pozz * Mass_fill;
        Cp_b += Cp_cement * mass_cement;
        Cp_b += Cp_ch * Mass_CH;

        Cp_b += (Cp_h2o * Mass_water) -
                (Alpha_cur * WN * mass_cement * (Cp_h2o - Cp_bh2o));
        if (AggTempEffect == 0)
          Cp_b += (Cp_agg * Mass_agg);

        mass_cem_now = mass_cement;

      } else {

        /***
         *    If not sealed, need to account for extra capillary
         *    water drawn in.
         *
         *    Basis is WCHSH(0.06) g H2O per gram cement for
         *    chemical shrinkage
         *
         *    Need to adjust mass basis to account for extra
         *    imbibed H2O
         ***/

        mass_cur = 1.0 + (WCHSH * mass_cement * Alpha_cur);

        /* Accounting for aggregate separately (15 Nov 2004) */

        Cp_b = Cp_pozz * Mass_fill / mass_cur;
        Cp_b += (Cp_cement * mass_cement / mass_cur);
        Cp_b += (Cp_ch * Mass_CH / mass_cur);

        Cp_b += (Cp_h2o * Mass_water) -
                (Alpha_cur * WN * mass_cement * (Cp_h2o - Cp_bh2o));

        Cp_b += (WCHSH * Cp_h2o * Alpha_cur * mass_cement);
        if (AggTempEffect == 0)
          Cp_b += ((Cp_agg * Mass_agg) / mass_cur);

        mass_cem_now = mass_cement / mass_cur;
      }

      /***
       *    Determine rate constant based on Arrhenius expression
       *
       *    Recall that Temp_cur_b is in degrees Celsius
       *
       *    1000.0 converts kJ to J
       *    8.314 is the gas constant in SI units
       *    273.15 adds to T to convert from C to K
       *    298.15 is the reference temperature (in K) to which
       *        all other temperatures are compared when computing
       *        changes in rate constants due to thermal activation
       ***/

      act_nrg = 1000.0 * E_act / 8.314;
      recip_Tdiff = (1.0 / (Temp_cur_b + 273.15)) - (1.0 / 298.15);
      Krate = exp(-(act_nrg * recip_Tdiff));

      /* Calculate pozzolanic and slag reaction rate constant */

      act_nrg = 1000.0 * E_act_pozz / 8.314;
      kpozz = exp(-(act_nrg * recip_Tdiff));
      act_nrg = 1000.0 * E_act_slag / 8.314;
      kslag = exp(-(act_nrg * recip_Tdiff));

      /***
       *    Modify silica fume probabilities.  There are
       *    two effects postulated:
       *    1. Early age effect due to nucleating capability
       *       of silica fume with high BET values
       *    2. Later age pozzolanic reactivity due to
       *       SiO2 content of the silica fume (Psfume)
       ***/

      /** Late age effect dictated by Psfume **/
      /** Psfume is for converting DIFFCH to POZZCSH **/

      Psfume = PSFUME * (kpozz / Krate);
      psfact = (SF_SiO2_val) / (SF_SiO2_normal);
      betfact = (SF_BET_val) / (SF_BET_normal);
      Psfume *= (3.0 * psfact * psfact * betfact);
      if (Psfume > 1.0)
        Psfume = 1.0;
      LOI_factor = 25.0 * (SF_LOI_val / SF_LOI_normal);
      if (LOI_factor < 1.0)
        LOI_factor = 1.0;

      /***
       *    Modify probability of pozzolanic and slag
       *    reactions based on ratio of pozzolanic (slag)
       *    reaction rate to the hydration rate
       ***/

      Pamsil = PAMSIL * (kpozz / Krate);
      Disprob[ASG] = Disbase[ASG] * (kpozz / Krate);
      Disprob[CAS2] = Disbase[CAS2] * (kpozz / Krate);
      Disprob[SLAG] = Slagreact * Disbase[SLAG] * (kslag / Krate);

      /***
       *    Update temperature based on heat generated
       *    and current Cp
       ***/

      if (mass_cem_now > 0.01) {

        /***
         *     If the temperature of the aggregate is different
         *     from that of the binder, then we calculate the
         *     temperature change of each separately due to
         *     energy conservation principles, otherwise, we
         *     handle temperature changes as previously
         ***/

        calcT(mass_cem_now);

      } else {

        calcT(Mass_fill_pozz);
      }

    } else if (Adiaflag == 2) {

      /***
       *    Update system temperature based on current time
       *    and requested temperature history
       ***/

      while ((Time_cur > thtimehi) && (!feof(thfile))) {
        fscanf(thfile, "%s", instring);
        thtimelo = atof(instring);
        fscanf(thfile, "%s", instring);
        thtimehi = atof(instring);
        fscanf(thfile, "%s", instring);
        thtemplo = atof(instring);
        fscanf(thfile, "%s", instring);
        thtemphi = atof(instring);
        if (Verbose) {
          printf("New temperature history values : \n");
          printf("%f %f ", thtimelo, thtimehi);
          printf("%f %f\n", thtemplo, thtemphi);
        }
      }

      if ((thtimehi - thtimelo) > 0.0) {
        Temp_cur_b = thtemplo + ((thtemphi - thtemplo) * (Time_cur - thtimelo) /
                                 (thtimehi - thtimelo));
        Temp_cur_agg = Temp_cur_b;
      } else {
        Temp_cur_b = thtemplo;
        Temp_cur_agg = Temp_cur_b;
      }

      /***
       *    1000.0 converts kJ to J
       *    8.314 is the gas constant in SI units
       *    273.15 adds to T to convert from C to K
       *    298.15 is the reference temperature (in K) to which
       *        all other temperatures are compared when computing
       *        changes in rate constants due to thermal activation
       ***/

      act_nrg = 1000.0 * E_act / 8.314;
      recip_Tdiff = (1.0 / (Temp_cur_b + 273.15)) - (1.0 / 298.15);
      Krate = exp(-(act_nrg * recip_Tdiff));

      /* Calculate pozzolanic and slag reaction rate constant */

      act_nrg = 1000.0 * E_act_pozz / 8.314;
      kpozz = exp(-(act_nrg * recip_Tdiff));
      act_nrg = 1000.0 * E_act_slag / 8.314;
      kslag = exp(-(act_nrg * recip_Tdiff));

      /***
       *    Modify probability of pozzolanic and slag
       *    reactions based on ratio of pozzolanic (slag)
       *    reaction rate to the hydration rate
       ***/

      /** Late age effect dictated by Psfume **/
      /** Psfume is for converting DIFFCH to POZZCSH **/

      Psfume = PSFUME * (kpozz / Krate);
      psfact = (SF_SiO2_val) / (SF_SiO2_normal);
      betfact = (SF_BET_val) / (SF_BET_normal);
      Psfume *= (3.0 * psfact * psfact * betfact);
      if (Psfume > 1.0)
        Psfume = 1.0;
      LOI_factor = 25.0 * (SF_LOI_val / SF_LOI_normal);
      if (LOI_factor < 1.0)
        LOI_factor = 1.0;

      Pamsil = PAMSIL * (kpozz / Krate);
      Disprob[ASG] = Disbase[ASG] * (kpozz / Krate);
      Disprob[CAS2] = Disbase[CAS2] * (kpozz / Krate);
      Disprob[SLAG] = Slagreact * Disbase[SLAG] * (kslag / Krate);
    }

    /***
     *    Modify time based on simple numerical integration,
     *    simulating maturity approach with parabolic kinetics
     *    (Knudsen model)
     ***/

    if (Verbose)
      printf("\nIcyc = %d AND Cyccnt = %d\n", Icyc, Cyccnt);
    if (Cyccnt > 1) {
      switch (TimeCalibrationMethod) {
      case CALORIMETRIC:
        dval = Heat_new * Heat_cf;
        sprintf(typestring, "calorimetric");
        if (dval < DataValue[0]) {
          if (Verbose)
            printf("\ndval = %f, DataValue[0] = %f, DataValue[1] = %f\n", dval,
                   DataValue[0], DataValue[1]);
          TimeHistory[Cyccnt] = DataTime[0];
        } else {
          findnewtime(dval, act_nrg, &previousUncorrectedTime, typestring);
        }
        break;
      case CHEMICALSHRINKAGE:
        dval = Chs_new;
        if (dval <= 0.0)
          dval = 0.00001;
        sprintf(typestring, "chemical shrinkage");
        if (dval < DataValue[0]) {
          if (Verbose)
            printf("\ndval = %f, DataValue[0] = %f, DataValue[1] = %f\n", dval,
                   DataValue[0], DataValue[1]);
          TimeHistory[Cyccnt] = DataTime[0];
        } else {
          findnewtime(dval, act_nrg, &previousUncorrectedTime, typestring);
        }
        break;
      default:
        Time_step = (2.0 * (float)(Cyccnt - 1) - 1.0) * Beta / Krate;
        Time_cur += Time_step;
        TimeHistory[Cyccnt] = Time_cur;
        break;
      }
    }

    /* Initialize and calculate gel-space ratio */

    Gsratio2 = 0.0;
    Gsratio2 += (double)(Count[CH] + Count[CSH]);
    Gsratio2 += (double)(Count[C3AH6] + Count[ETTR]);
    Gsratio2 += (double)(Count[POZZCSH] + Count[SLAGCSH]);
    Gsratio2 += (double)(Count[FH3] + Count[AFM] + Count[ETTRC4AF]);
    Gsratio2 += (double)(Count[FRIEDEL] + Count[STRAT]);
    Gsratio2 += (double)(Count[ABSGYP] + Count[AFMC]);

    space = (double)(Count[POROSITY] + Count[CRACKP] + Count[EMPTYP]);

    Gsratio2 = (Gsratio2) / (Gsratio2 + space);

    gfloat = 0.0;
    if (W_to_c != 0.0) {
      gfloat = (double)((0.68 * Alpha_cur) / (0.32 * Alpha_cur + W_to_c));
    }

    if (Verbose)
      printf("Entering pHpred");
    pHpred();
    if (Verbose) {
      printf("Returned from call to pHpred");
      fflush(stdout);
    }

    /***
     *    Check percolation of pore space
     *
     *    Note that first two variables passed correspond
     *    to phases to check in combination.
     *    Could easily add calls to
     *    check for percolation of CH, CSH, etc.
     *    (24 May 2004)
     ***/

    if ((Time_cur >= NextBurnTime) && ((Porefl1 + Porefl2 + Porefl3) != 0)) {

      /* Burn across x */

      NextBurnTime = Time_cur + Burntimefreq;

      if (Verbose) {
        printf("\nGoing to check percolation of porosity in X... ");
        fflush(stdout);
      }
      Porefl1 = burn3d(((int)POROSITY), ((int)CRACKP), 1, 0, 0);
      if (Verbose) {
        printf("Done!\n");
        fflush(stdout);
      }
      if (Porefl1 == -1) {
        freeallmem();
        bailout("disrealnew", "Problem in burn3d");
        exit(1);
      }
      /* Burn across y */
      if (Verbose) {
        printf("\nGoing to check percolation of porosity in Y... ");
        fflush(stdout);
      }
      Porefl2 = burn3d(((int)POROSITY), ((int)CRACKP), 0, 1, 0);
      if (Verbose) {
        printf("Done!\n");
        fflush(stdout);
      }
      if (Porefl2 == -1) {
        freeallmem();
        bailout("disrealnew", "Problem in burn3d");
        exit(1);
      }
      /* Burn across z */
      if (Verbose) {
        printf("\nGoing to check percolation of porosity in Z... ");
        fflush(stdout);
      }
      Porefl3 = burn3d(((int)POROSITY), ((int)CRACKP), 0, 0, 1);
      if (Verbose) {
        printf("Done!\n");
        fflush(stdout);
      }
      if (Porefl3 == -1) {
        freeallmem();
        bailout("disrealnew", "Problem in burn3d");
        exit(1);
      }

      /***
       *    Switch to self-desiccating conditions
       *    when porosity disconnects
       ***/

      /*
                  if (Crackwidth == 0 || Icyc < Crackcycle) {
                      if (((Porefl1 + Porefl2 + Porefl3) == 0) && (!Sealed)) {
                          Water_off = Water_left;
                          Pore_off = Countkeep;
                          Sealed = 1;
                          if (Verbose) printf("Switching to self-desiccating at
         cycle %d \n",Cyccnt);
                      }
                  } else {
                       if ((Porefl1 == 0) && (Crackorient == 1) && (!Sealed)) {
                           Water_off = Water_left;
                           Pore_off = Countkeep;
                           Sealed = 1;
                           if (Verbose) printf("Switching to self-desiccating at
         cycle %d \n",Cyccnt); } else if ((Porefl2 == 0) && (Crackorient == 2)
         && (!Sealed)) { Water_off = Water_left; Pore_off = Countkeep; Sealed =
         1; if (Verbose) printf("Switching to self-desiccating at cycle %d
         \n",Cyccnt); } else if ((Porefl3 == 0) && (Crackorient == 3) &&
         (!Sealed)) { Water_off = Water_left; Pore_off = Countkeep; Sealed = 1;
                           if (Verbose) printf("Switching to self-desiccating at
         cycle %d \n",Cyccnt);
                       }
                  }
      */
    }

    /* Check percolation of solids (set point) */

    if ((Time_cur >= NextSetTime) && (!Setflag)) {

      NextSetTime = Time_cur + Settimefreq;

      if (Verbose) {
        printf("\nGoing to check percolation of solids in X... ");
        fflush(stdout);
      }
      Sf1 = burnset(1, 0, 0); /* Burn across x */
      if (Verbose) {
        printf("Done!\nGoing to check percolation of solids in Y... ");
        fflush(stdout);
      }
      Sf2 = burnset(0, 1, 0); /* Burn across y */
      if (Verbose) {
        printf("Done!\nGoing to check percolation of solids in Z... ");
        fflush(stdout);
      }
      Sf3 = burnset(0, 0, 1); /* Burn across z */
      if (Verbose) {
        printf("Done!");
        fflush(stdout);
      }

      Setflag = Sf1 * Sf2 * Sf3;
    }

    /* Check hydration of particles */

    if (Time_cur >= NextPhydTime) {
      NextPhydTime = Time_cur + Phydtimefreq;
      if ((parthyd()) == MEMERR) {
        freeallmem();
        bailout("disrealnew", "Problem with parthyd");
        exit(1);
      }
    }

    /* Total up phase counts */

    if (Cyccnt > 1) {
      for (k = 0; k < NPHASES; k++)
        Count[k] = 0;
      for (i = 0; i < Xsyssize; i++) {
        for (j = 0; j < Ysyssize; j++) {
          for (k = 0; k < Zsyssize; k++) {
            Count[(int)(Mic[i][j][k])]++;
          }
        }
      }
    }

    if (Crackwidth > 0 && (Time_cur >= Cracktime)) {

      /***
       *    Crack the microstructure and change the
       *    effective system size
       ***/

      if (Verbose) {
        printf("\nPreparing to place a crack in the microstructure.");
        printf("\n\tCrack width = %d", Crackwidth);
        printf("\n\tX size currently is %d", Xsyssize);
        printf("\n\tY size currently is %d", Ysyssize);
        printf("\n\tZ size currently is %d", Zsyssize);
        fflush(stdout);
      }
      addcrack();
      if (Verbose) {
        printf("\n\tAfter cracking, X size is %d", Xsyssize);
        printf("\n\tAfter cracking, Y size is %d", Ysyssize);
        printf("\n\tAfter cracking, Z size is %d", Zsyssize);
        fflush(stdout);
      }

      for (k = 0; k < NPHASES; k++)
        Count[k] = 0;
      for (i = 0; i < Xsyssize; i++) {
        for (j = 0; j < Ysyssize; j++) {
          for (k = 0; k < Zsyssize; k++) {
            Count[(int)(Mic[i][j][k])]++;
          }
        }
      }

      /***
       *    Must update anything that depends on system size, except
       *    for those things that are updated once each cycle
       ***/

      Syspix = Xsyssize * Ysyssize * Zsyssize;
      if (Verbose)
        printf("\n\tSyspix changes from %d to %d", Syspix_orig, Syspix);
      Sizemag = ((float)Syspix) / (pow(((double)(DEFAULTSYSTEMSIZE)), 3.0));
      if (Verbose)
        printf("\n\tSizemag changes from %f to %f", Sizemag_orig, Sizemag);
      Isizemag = (int)(Sizemag + 0.5);

      Heat_cf *= ((double)Syspix) / ((double)Syspix_orig);
      Cshscale *= Sizemag / Sizemag_orig;
      C3ah6_scale *= Sizemag / Sizemag_orig;
      pscalech *= Sizemag / Sizemag_orig;
      pscalegyp *= Sizemag / Sizemag_orig;
      pscalehg *= Sizemag / Sizemag_orig;
      pscalefh3 *= Sizemag / Sizemag_orig;

      /***
       *    Last thing to do is to determine the curing
       *    condition of the crack (saturated or sealed), which
       *    we set to whatever the user wanted at the beginning
       *    of the run
       ***/
      /***
       *    Commented this block out on 2 July 2004 because
       *    now we have CRACKP and POROSITY.  We originally
       *    wanted to keep the  crack from drying out due to
       *    sealed conditions, but only POROSITY pixels now can
       *    be consumed under sealed conditions.
       ***/
      /*

      if ((Sealed) && (!Sealed_after_crack)) {
          if (Verbose) printf("\nSwitching to saturated conditions after
      cracking.\n");
      }
      Sealed = Sealed_after_crack;
      */

      /* Make sure we don't do this block again */

      Cracktime = End_time + 100.0;
    }

    /***
     *     As currently set up, crack porosity (CRACKP) can
     *     diffuse into regular saturated porosity (POROSITY).
     *     Every 5 cycles after a crack is added, we call the
     *     function resetcrackpores to redistribute these pixels
     *     back to the crack
     ***/

    /*
    if ((Icyc > Crackcycle) && (((Icyc - Crackcycle)%5) == 0)) {
        resetcrackpores();
    }
    */

    /* Output movie microstructure if one is desired */

    fflush(stdout);
    if ((MovieFrameFreq > 0.0) && (Time_cur >= NextMovieTime)) {
      printf("\nMaking movie frame");
      fflush(stdout);
      NextMovieTime = Time_cur + MovieFrameFreq;
      /* Check to see if movie file has been created already */
      Movfile = filehandler("disrealnew", Moviename, "READ_NOFAIL");
      if (!Movfile) {
        printf("\nMovie file not found.  Creating it now...");
        fflush(stdout);
        Movfile = filehandler("disrealnew", Moviename, "WRITE");
        if (!Movfile) {
          freeallmem();
          exit(1);
        }
        printf("Success.");
        fflush(stdout);

        fprintf(Movfile, "%s ", VERSIONSTRING);
        fprintf(Movfile, "%s\n", VERSIONNUMBER);
        if (Crackorient == 1 || Crackorient == 2) {
          fprintf(Movfile, "%s ", XSIZESTRING);
          fprintf(Movfile, "%d\n", Xsyssize);
          fprintf(Movfile, "%s ", YSIZESTRING);
          fprintf(Movfile, "%d\n", Ysyssize);
        }
        if (Crackorient == 3) {
          fprintf(Movfile, "%s ", XSIZESTRING);
          fprintf(Movfile, "%d\n", Xsyssize);
          fprintf(Movfile, "%s ", YSIZESTRING);
          fprintf(Movfile, "%d\n", Zsyssize);
        }
        fprintf(Movfile, "%s ", IMGRESSTRING);
        fprintf(Movfile, "%4.2f\n", Res);

      } else {
        printf("\nMovie file exists.  Appending to it...");
        fflush(stdout);
        fclose(Movfile);
        Movfile = filehandler("disrealnew", Moviename, "APPEND");
        if (!Movfile) {
          freeallmem();
          exit(1);
        }
      }

      /***
       *    Currently can only make a hydration movie for
       *    slice 50.  Make this user-defined later on
       ***/

      if (Crackorient == 1 || Crackorient == 2) {
        for (iy = 0; iy < Ysyssize; iy++) {
          for (ix = 0; ix < Xsyssize; ix++) {
            fprintf(Movfile, "%d\n", (int)Mic[ix][iy][50]);
          }
        }
      } else {
        for (iz = 0; iz < Zsyssize; iz++) {
          for (ix = 0; ix < Xsyssize; ix++) {
            fprintf(Movfile, "%d\n", (int)Mic[ix][50][iz]);
          }
        }
      }

      fclose(Movfile);
      printf("\nMade movie frame successfully and closed movie file");
      fflush(stdout);
    }

    /***
     *    Output complete 3D microstructure once for every entry
     *    in the outputalpha.dat file
     ***/

    if (((CustomImageTime != NULL) &&
         (Time_cur >= CustomImageTime[customentry])) ||
        ((Alpha_cur > 0.0) && (Time_cur >= NextImageTime))) {

      if (Verbose)
        printf("Writing microstructure image");
      customentry++;

      NextImageTime = Time_cur + OutTimefreq;
      sprintf(strsuffa, "%.2fh.%d.%1d", Time_cur, (int)Temp_0, Csh2flag);
      sprintf(strsuffb, "%1d%1d", Adiaflag, Sealed);
      strcpy(strsuff, strsuffa);
      strcat(strsuff, strsuffb);
      sprintf(Micname, "%s%s.img.", Outputdir, Fileroot);
      strcat(Micname, strsuff);

      Micfile = filehandler("disrealnew", Micname, "WRITE");
      if (!Micfile) {
        sprintf(buff, "Could not open file %s", Micname);
        bailout("disrealnew", buff);
        freeallmem();
        exit(1);
      }

      Imageindexfile = filehandler("disrealnew", Imageindexname, "APPEND");
      if (!Imageindexfile) {
        sprintf(buff, "Could not open file %s", Imageindexname);
        bailout("disrealnew", buff);
        freeallmem();
        exit(1);
      }
      fprintf(Imageindexfile, "%f\t%s\n", Time_cur, Micname);
      fclose(Imageindexfile);

      if (write_imgheader(Micfile, Xsyssize, Ysyssize, Zsyssize, Res)) {
        fclose(Micfile);
        freeallmem();
        bailout("disrealnew", "Error writing image header");
        exit(1);
      }

      /**
       * 2025 August 05
       * New convention is to read and write image data in C-order (z
       * varies the fastest, then y, then x)
       **/
      for (ix = 0; ix < Xsyssize; ix++) {
        for (iy = 0; iy < Ysyssize; iy++) {
          for (iz = 0; iz < Zsyssize; iz++) {

            pixtmp = (int)Mic[ix][iy][iz];

            switch (pixtmp) {
            case DIFFCSH:
              /* pixtmp = CSH; */
              pixtmp = POROSITY;
              break;
            case DIFFANH:
              /* pixtmp = ANHYDRITE; */
              pixtmp = POROSITY;
              break;
            case DIFFHEM:
              /* pixtmp = HEMIHYD; */
              pixtmp = POROSITY;
              break;
            case DIFFGYP:
              /* pixtmp = GYPSUM; */
              pixtmp = POROSITY;
              break;
            case DIFFCACL2:
              /* pixtmp = CACL2; */
              pixtmp = POROSITY;
              break;
            case DIFFCACO3:
              /* pixtmp = CACO3; */
              pixtmp = POROSITY;
              break;
            case DIFFCAS2:
              /* pixtmp = CAS2; */
              pixtmp = POROSITY;
              break;
            case DIFFAS:
              /* pixtmp = ASG; */
              pixtmp = POROSITY;
              break;
            case DIFFETTR:
              /* pixtmp = ETTR; */
              pixtmp = POROSITY;
              break;
            case DIFFC3A:

              /***
               *    Any precipitation of diffusing C3A
               *    is assumed to form cubic C3A instead
               *    of orthorhombic C3A
               ***/

              /* pixtmp = C3A; */
              pixtmp = POROSITY;
              break;
            case DIFFC4A:

              /***
               *    Any diffusing C4AF has already
               *    converted to FH3 and CH, so you can
               *    not really represent it as C4AF anymore.
               *    Best you can do is represent it as
               *    C3A
               ***/

              /* pixtmp = C3A; */
              pixtmp = POROSITY;
              break;
            case DIFFFH3:
              /* pixtmp = FH3; */
              pixtmp = POROSITY;
              break;
            case DIFFCH:
              /* pixtmp = CH; */
              pixtmp = POROSITY;
              break;
            default:
              break;
            }

            fprintf(Micfile, "%d\n", pixtmp);

          } /* End of loop in z */
        } /* End of loop in y */
      } /* End of loop in x */

      fclose(Micfile);

      /* With microstructure now written, calculate pore size distribution */
      printf("\nCalculating pore size distribution now...");
      if (calcporedist3d(Micname)) {
        printf(
            "\nThere was a problem calculating the pore size distribution.\n");
      }
      printf("Done calculating pore size distribution.\n");
    }

    /* Attempt to open master data file */

    Datafile = filehandler("disrealnew", Datafilename, "APPEND");
    if (!Datafile) {
      freeallmem();
      exit(1);
    }
    fprintf(Datafile, "%d,%.4f,%.4f,%.4f,", Cyccnt - 1, Time_cur, Alpha_cur,
            Alpha_fa_cur);
    fprintf(Datafile, "%.4f,%.4f,%.4f,", (Heat_new * Heat_cf), Temp_cur_b,
            Gsratio2);
    fprintf(Datafile, "%.4f,%.4f,%.5f,%.4f,", Wn_o, Wn_i, Chs_new, PH_cur);
    fprintf(Datafile, "%.4f,%.4f,%.4f,%.4f,", Conductivity, Concnaplus,
            Conckplus, Conccaplus);
    fprintf(Datafile, "%.4f,%.4f,%.4f,%.4f,", Concsulfate, ActivityK,
            ActivityCa, ActivityOH);
    fprintf(Datafile, "%.4f,%.4f,", ActivitySO4,
            ((float)Count[POROSITY] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,%.4f,", Con_fracp[0], Con_fracp[1],
            Con_fracp[2]);
    fprintf(Datafile, "%.4f,",
            (Con_fracp[0] + Con_fracp[1] + Con_fracp[2]) / 3.0);
    fprintf(Datafile, "%.4f,%.4f,%.4f,", Con_fracs[0], Con_fracs[1],
            Con_fracs[2]);
    fprintf(Datafile, "%.4f,",
            (Con_fracs[0] + Con_fracs[1] + Con_fracs[2]) / 3.0);
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[C3S] / (float)Syspix),
            ((float)Count[C2S] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[C3A] / (float)Syspix),
            ((float)Count[OC3A] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[C4AF] / (float)Syspix),
            ((float)Count[K2SO4] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[NA2SO4] / (float)Syspix),
            ((float)Count[GYPSUM] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[HEMIHYD] / (float)Syspix),
            ((float)Count[ANHYDRITE] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[CACO3] / (float)Syspix),
            ((float)Count[FREELIME] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[SFUME] / (float)Syspix),
            ((float)Count[INERT] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[SLAG] / (float)Syspix),
            ((float)Count[ASG] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[CAS2] / (float)Syspix),
            ((float)Count[AMSIL] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[CH] / (float)Syspix),
            ((float)Count[CSH] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[POZZCSH] / (float)Syspix),
            ((float)Count[SLAGCSH] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[C3AH6] / (float)Syspix),
            ((float)(Count[ETTR] + Count[ETTRC4AF]) / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[AFM] / (float)Syspix),
            ((float)Count[FH3] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[CACL2] / (float)Syspix),
            ((float)Count[FRIEDEL] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[STRAT] / (float)Syspix),
            ((float)Count[GYPSUMS] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f,", ((float)Count[ABSGYP] / (float)Syspix),
            ((float)Count[AFMC] / (float)Syspix));
    fprintf(Datafile, "%.4f,%.4f\n", ((float)Count[INERTAGG] / (float)Syspix),
            ((float)Count[EMPTYP] / (float)Syspix));
    fclose(Datafile);

  } /*    End of loop over all hydration cycles */

  /***
   *    Hydration cycles are finished.  Clean up from here.
   ***/

  /* Last call to dissolve to terminate hydration */

  valin = 0;
  dissolve(valin);

  /* Output final microstructure */

  outfile = filehandler("disrealnew", Fileoname, "WRITE");
  if (!outfile) {
    freeallmem();
    exit(1);
  }

  Imageindexfile = filehandler("disrealnew", Imageindexname, "APPEND");
  if (!Imageindexfile) {
    sprintf(buff, "Could not open file %s", Imageindexname);
    bailout("disrealnew", buff);
    freeallmem();
    exit(1);
  }
  fprintf(Imageindexfile, "%f\t%s\n", Time_cur, Fileoname);
  fclose(Imageindexfile);

  if (write_imgheader(outfile, Xsyssize, Ysyssize, Zsyssize, Res)) {
    fclose(outfile);
    freeallmem();
    bailout("disrealnew", "Error writing image header");
    exit(1);
  }

  for (ix = 0; ix < Xsyssize; ix++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 0; iz < Zsyssize; iz++) {
        fprintf(outfile, "%d\n", (int)Mic[ix][iy][iz]);
      }
    }
  }
  fclose(outfile);

  if (calcporedist3d(Fileoname)) {
    printf("\nThere was a problem calculating the pore size distribution.\n");
  }

  /***
   *    Check percolation of pore space
   *    Note that first two variables passed correspond to
   *    combined phases to check.  Could easily add calls
   *    to check for percolation of CH, CSH, etc.
   ***/

  if ((Burntimefreq > 0.0) && (Burntimefreq <= End_time) &&
      ((Porefl1 + Porefl2 + Porefl3) != 0)) {

    /* Burn across x */
    Porefl1 = burn3d(((int)POROSITY), ((int)CRACKP), 1, 0, 0);
    if (Porefl1 == MEMERR) {
      freeallmem();
      bailout("disrealnew", "Problem in burn3d");
      exit(1);
    }
    /* Burn across y */
    Porefl2 = burn3d(((int)POROSITY), ((int)CRACKP), 0, 1, 0);
    if (Porefl2 == MEMERR) {
      freeallmem();
      bailout("disrealnew", "Problem in burn3d");
      exit(1);
    }
    /* Burn across z */
    Porefl3 = burn3d(((int)POROSITY), ((int)CRACKP), 0, 0, 1);
    if (Porefl3 == MEMERR) {
      freeallmem();
      bailout("disrealnew", "Problem in burn3d");
      exit(1);
    }
  }

  /* Check percolation of solids (set point) */

  if ((Settimefreq > 0.0) && (Settimefreq <= End_time) && (!Setflag)) {

    Sf1 = burnset(1, 0, 0); /* Burn across x */
    Sf2 = burnset(0, 1, 0); /* Burn across y */
    Sf3 = burnset(0, 0, 1); /* Burn across z */

    Setflag = Sf1 * Sf2 * Sf3;
    if (Verbose)
      printf("\nSetflag = %d", Setflag);
  }

  /* Output last lines of heat and chemical shrinkage files */

  if (Cyccnt > 1) {
    Time_step = ((2.0 * ((float)Cyccnt)) - 1.0) * Beta / Krate;
    Time_cur += Time_step;
  }

  /* Initialize and calculate gel-space ratio */

  Gsratio2 = 0.0;
  Gsratio2 += (double)(Count[CH] + Count[CSH]);
  Gsratio2 += (double)(Count[C3AH6] + Count[ETTR]);
  Gsratio2 += (double)(Count[POZZCSH] + Count[SLAGCSH]);
  Gsratio2 += (double)(Count[FH3] + Count[AFM] + Count[ETTRC4AF]);
  Gsratio2 += (double)(Count[FRIEDEL] + Count[STRAT]);
  Gsratio2 += (double)(Count[ABSGYP] + Count[AFMC]);

  space = (double)(Count[POROSITY] + Count[CRACKP] + Count[EMPTYP]);
  Gsratio2 = (Gsratio2) / (Gsratio2 + space);

  gfloat = (double)((0.68 * Alpha_cur) / (0.32 * Alpha_cur + W_to_c));
  gfloat =
      (double)(Count[EMPTYP] + Count[POROSITY] + Count[CRACKP] - Water_left);
  gfloat *= (Heat_cf / 1000.0);

  Cyccnt++;

  /* Final call to pHpred */

  if (Verbose) {
    printf("\nMaking final call to pHpred...");
    fflush(stdout);
  }
  pHpred();

  /* Attempt to open master data file */

  Datafile = filehandler("disrealnew", Datafilename, "APPEND");
  if (!Datafile) {
    freeallmem();
    exit(1);
  }
  fprintf(Datafile, "%d,%.4f,%.4f,%.4f,", Cyccnt - 1, Time_cur, Alpha_cur,
          Alpha_fa_cur);
  fprintf(Datafile, "%.4f,%.4f,%.4f,", (Heat_new * Heat_cf), Temp_cur_b,
          Gsratio2);
  fprintf(Datafile, "%.4f,%.4f,%.5f,%.4f,", Wn_o, Wn_i, Chs_new, PH_cur);
  fprintf(Datafile, "%.4f,%.4f,%.4f,%.4f,", Conductivity, Concnaplus, Conckplus,
          Conccaplus);
  fprintf(Datafile, "%.4f,%.4f,%.4f,%.4f,", Concsulfate, ActivityK, ActivityCa,
          ActivityOH);
  fprintf(Datafile, "%.4f,%.4f,", ActivitySO4,
          ((float)Count[POROSITY] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,%.4f,", Con_fracp[0], Con_fracp[1],
          Con_fracp[2]);
  fprintf(Datafile, "%.4f,",
          (Con_fracp[0] + Con_fracp[1] + Con_fracp[2]) / 3.0);
  fprintf(Datafile, "%.4f,%.4f,%.4f,", Con_fracs[0], Con_fracs[1],
          Con_fracs[2]);
  fprintf(Datafile, "%.4f,",
          (Con_fracs[0] + Con_fracs[1] + Con_fracs[2]) / 3.0);
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[C3S] / (float)Syspix),
          ((float)Count[C2S] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[C3A] / (float)Syspix),
          ((float)Count[OC3A] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[C4AF] / (float)Syspix),
          ((float)Count[K2SO4] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[NA2SO4] / (float)Syspix),
          ((float)Count[GYPSUM] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[HEMIHYD] / (float)Syspix),
          ((float)Count[ANHYDRITE] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[CACO3] / (float)Syspix),
          ((float)Count[FREELIME] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[SFUME] / (float)Syspix),
          ((float)Count[INERT] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[SLAG] / (float)Syspix),
          ((float)Count[ASG] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[CAS2] / (float)Syspix),
          ((float)Count[AMSIL] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[CH] / (float)Syspix),
          ((float)Count[CSH] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[POZZCSH] / (float)Syspix),
          ((float)Count[SLAGCSH] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[C3AH6] / (float)Syspix),
          ((float)(Count[ETTR] + Count[ETTRC4AF]) / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[AFM] / (float)Syspix),
          ((float)Count[FH3] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[CACL2] / (float)Syspix),
          ((float)Count[FRIEDEL] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[STRAT] / (float)Syspix),
          ((float)Count[GYPSUMS] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f,", ((float)Count[ABSGYP] / (float)Syspix),
          ((float)Count[AFMC] / (float)Syspix));
  fprintf(Datafile, "%.4f,%.4f\n", ((float)Count[INERTAGG] / (float)Syspix),
          ((float)Count[EMPTYP] / (float)Syspix));
  fclose(Datafile);

  /* Attempt to open time history file */

  Datafile = filehandler("disrealnew", "TimeHistory.dat", "WRITE");
  if (!Datafile) {
    freeallmem();
    exit(1);
  }
  for (i = 0; i < Cyccnt; i++) {
    fprintf(Datafile, "%d %f\n", i, TimeHistory[i]);
  }
  fclose(Datafile);

  freeallmem();
  return (0);
}

/***
 *    checkargs
 *
 *     Check command-line arguments used to invoke disrealnew
 *
 *     Arguments:    int argc, char *argv[]
 *     Returns:    nothing
 *
 *    Calls:        no routines
 *    Called by:    main program
 ***/
void checkargs(int argc, char *argv[]) {
  register unsigned int i;

  /* Is verbose output requested? */

  Verbose = 0;
  for (i = 1; i < argc; i++) {
    if ((!strcmp(argv[i], "-v")) || (!strcmp(argv[i], "--verbose")))
      Verbose = 1;
  }
}

/***
 *    get_input
 *
 *     Gather input data and parameters for running simulation
 *
 *     Arguments:    none
 *     Returns:    0 if okay, nonzero otherwise
 *
 *    Calls:        no routines
 *    Called by:    main program
 ***/
int get_input(float *pnucch, float *pscalech, float *pnuchg, float *pscalehg,
              float *pnucfh3, float *pscalefh3, float *pnucgyp,
              float *pscalegyp, int *nmovstep) {
  int i, j, k, status = 0;
  int onepixfloc = 0;
  int nlen, phtodo, valin, ovalin, dphase, deactphase;
  int ix, iy, iz, x, y;
  int newx, newy, newz;
  int nadd;
  char ch, imgfile[MAXSTRING], pimgfile[MAXSTRING];
  char buff[MAXSTRING], prmname[MAXSTRING], custcycfile[MAXSTRING];
  char name[MAXSTRING], answer[MAXSTRING], calfilename[MAXSTRING];
  char buff1[MAXSTRING], buff2[MAXSTRING], instring[MAXSTRING];
  float dfrac, dends, dterm, bias, pc3a, b_estimate;
  float newver, newres;
  FILE *fimgfile, *fpimgfile, *fprmfile, *fcofile, *fcalfile;

  /***
   *    Allocate memory for dissolution probability arrays
   *    and some other variables that are phase-specific.
   ***/

  if (Verbose)
    printf("\tAllocating Disprob ...");
  Disprob = fvector(NSPHASES + 1);
  if (!Disprob) {
    bailout("disrealnew", "Could not allocate memory for Disprob");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Disbase ...");
  Disbase = fvector(NSPHASES + 1);
  if (!Disbase) {
    bailout("disrealnew", "Could not allocate memory for Disbase");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Discoeff ...");
  Discoeff = fvector(NSPHASES + 1);
  if (!Discoeff) {
    bailout("disrealnew", "Could not allocate memory for Discoeff");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Soluble ...");
  Soluble = ivector(NSPHASES + 1);
  if (!Soluble) {
    bailout("disrealnew", "Could not allocate memory for Soluble");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Creates ...");
  Creates = ivector(NSPHASES + 1);
  if (!Creates) {
    bailout("disrealnew", "Could not allocate memory for Creates");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Onepixelbias ...");
  Onepixelbias = fvector(NSPHASES + 1);
  if (!Onepixelbias) {
    bailout("disrealnew", "Could not allocate memory for Onepixelbias");
    return (1);
  }

  /***
   *    Allocate memory for the activation/deactivation start
   *    and stop flags for each phase in the system.
   ***/

  if (Verbose)
    printf("  done\n\tAllocating Startflag ...");
  Startflag = ivector(NSPHASES + 1);
  if (!Startflag) {
    bailout("disrealnew", "Could not allocate memory for Startflag");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Stopflag ...");
  Stopflag = ivector(NSPHASES + 1);
  if (!Stopflag) {
    bailout("disrealnew", "Could not allocate memory for Stopflag");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Deactphaselist ...");
  Deactphaselist = ivector(NSPHASES + 1);
  if (!Deactphaselist) {
    bailout("disrealnew", "Could not allocate memory for Deactphaselist");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Deactfrac ...");
  Deactfrac = fvector(NSPHASES + 1);
  if (!Deactfrac) {
    bailout("disrealnew", "Could not allocate memory for Deactfrac");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Reactfrac ...");
  Reactfrac = fvector(NSPHASES + 1);
  if (!Reactfrac) {
    bailout("disrealnew", "Could not allocate memory for Reactfrac");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Deactinit ...");
  Deactinit = fvector(NSPHASES + 1);
  if (!Deactinit) {
    bailout("disrealnew", "Could not allocate memory for Deactinit");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Deactends ...");
  Deactends = fvector(NSPHASES + 1);
  if (!Deactends) {
    bailout("disrealnew", "Could not allocate memory for Deactends");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Deactterm ...");
  Deactterm = fvector(NSPHASES + 1);
  if (!Deactterm) {
    bailout("disrealnew", "Could not allocate memory for Deactterm");
    return (1);
  }

  /***
   *    Allocate memory for the arrays that store the influence
   *    of pH on solubility of each phase in the system.
   ***/

  if (Verbose)
    printf("  done\n\tAllocating PHsulfcoeff ...");
  PHsulfcoeff = fvector(NSPHASES + 1);
  if (!Deactterm) {
    bailout("disrealnew", "Could not allocate memory for Deactterm");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating PHfactor ...");
  PHfactor = fvector(NSPHASES + 1);
  if (!Deactterm) {
    bailout("disrealnew", "Could not allocate memory for Deactterm");
    return (1);
  }

  /***
   *    Get name of hydration parameter file.  This contains
   *    all of the baseline parameters for dissolution probabilities,
   *    nucleation probabilities, etc.
   ***/

  printf("Enter name of file containing hydration parameters\n");
  read_string(prmname, sizeof(prmname));
  printf("%s\n", prmname);
  fflush(stdout);

  fprmfile = filehandler("disrealnew", prmname, "READ");
  if (!fprmfile) {
    return (1);
  }

  fscanf(fprmfile, "%s %s", name, instring);
  Cubesize = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, Cubesize);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  CUBEMIN = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, CUBEMIN);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  PSFUME = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, PSFUME);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  SF_SiO2_val = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, SF_SiO2_val);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  SF_BET_val = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, SF_BET_val);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  SF_LOI_val = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, SF_LOI_val);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  SF_SiO2_normal = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, SF_SiO2_normal);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  SF_BET_normal = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, SF_BET_normal);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  SF_LOI_normal = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, SF_LOI_normal);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  PAMSIL = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, PAMSIL);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  MAXTRIES = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, MAXTRIES);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  DISBIAS = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, DISBIAS);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  Disbias = DISBIAS;
  fscanf(fprmfile, "%s %s", name, instring);
  DISMIN = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, DISMIN);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  Dismin = DISMIN;
  fscanf(fprmfile, "%s %s", name, instring);
  DISMIN2 = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, DISMIN2);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  Dismin2 = DISMIN2;
  fscanf(fprmfile, "%s %s", name, instring);
  DISMINSLAG = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, DISMINSLAG);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  Disminslag = DISMINSLAG;
  fscanf(fprmfile, "%s %s", name, instring);
  DISMINASG = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, DISMINASG);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  Disminasg = DISMINASG;
  fscanf(fprmfile, "%s %s", name, instring);
  DISMINCAS2 = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, DISMINCAS2);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  Dismincas2 = DISMINCAS2;
  fscanf(fprmfile, "%s %s", name, instring);
  DISMIN_C3A_0 = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, DISMIN_C3A_0);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  Dismin_c3a = DISMIN_C3A_0;
  fscanf(fprmfile, "%s %s", name, instring);
  DISMIN_C4AF_0 = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, DISMIN_C4AF_0);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  Dismin_c4af = DISMIN_C4AF_0;
  fscanf(fprmfile, "%s %s", name, instring);
  DK2SO4MAX = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, DK2SO4MAX);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  DNA2SO4MAX = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, DNA2SO4MAX);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  DETTRMAX = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, DETTRMAX);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  DGYPMAX = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, DGYPMAX);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  DCACO3MAX = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, DCACO3MAX);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  DCACL2MAX = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, DCACL2MAX);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  DCAS2MAX = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, DCAS2MAX);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  DASMAX = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, DASMAX);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  CHCRIT = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, CHCRIT);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  *pnucch = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, *pnucch);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  *pscalech = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, *pscalech);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  *pnucgyp = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, *pnucgyp);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  *pscalegyp = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, *pscalegyp);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  *pnuchg = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, *pnuchg);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  *pscalehg = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, *pscalehg);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  *pnucfh3 = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, *pnucfh3);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  *pscalefh3 = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, *pscalefh3);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  C3AH6CRIT = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, C3AH6CRIT);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  CSHSCALE = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, CSHSCALE);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  C3AH6_SCALE = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, C3AH6_SCALE);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  C3AH6GROW = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, C3AH6GROW);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  CHGROW = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, CHGROW);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  CHGROWAGG = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, CHGROWAGG);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  ETTRGROW = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, ETTRGROW);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  C3AETTR = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, C3AETTR);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  C3AGYP = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, C3AGYP);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  SOLIDC3AGYP = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, SOLIDC3AGYP);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  SOLIDC4AFGYP = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, SOLIDC4AFGYP);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  AGRATE = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, AGRATE);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  PCSH2CSH = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, PCSH2CSH);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  A0_CHSOL = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, A0_CHSOL);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  A1_CHSOL = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, A1_CHSOL);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  WCSCALE = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, WCSCALE);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  DISTLOCCSH = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, DISTLOCCSH);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  NEIGHBORS = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, NEIGHBORS);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  WN = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, WN);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  WCHSH = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, WCHSH);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  MAXDIFFSTEPS = atoi(instring);
  if (Verbose)
    printf("%s %d\n", name, MAXDIFFSTEPS);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }
  fscanf(fprmfile, "%s %s", name, instring);
  PDIFFCSH = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, PDIFFCSH);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }

  /***
   *    Number of sulfates absorbed per 100 CSH units
   *    Currently not used by program
   ***/

  fscanf(fprmfile, "%s %s", name, instring);
  Gypabsprob = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, Gypabsprob);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }

  /***
   *    Gel porosity of CSH, POZZCSH, and SLAGCSH
   *    Used in pHpred function
   ***/

  fscanf(fprmfile, "%s %s", name, instring);
  CSH_Porosity = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, CSH_Porosity);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }

  fscanf(fprmfile, "%s %s", name, instring);
  POZZCSH_Porosity = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, POZZCSH_Porosity);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }

  fscanf(fprmfile, "%s %s", name, instring);
  SLAGCSH_Porosity = atof(instring);
  if (Verbose)
    printf("%s %f\n", name, SLAGCSH_Porosity);
  if (feof(fprmfile)) {
    printf("Premature end of parameter file!!\n");
    return (1);
  }

  /***
   *    Read X and Y values for a second-order fit
   *    of the dependence of solubility/reactivity on pH.
   *
   *    History of default values for specific phases:
   *
   *    FitpH[SFUME][x][0] changed from 12.7 to 12.71 on 27 April 2003
   *    FitpH[SFUME][x][1] changed from 13.085 to 13.095 on 27 April 2003
   *    FitpH[SFUME][x][2] changed from 13.185 to 13.195 on 27 April 2003
   *
   *     FitpH[AMSIL] is equal to FitpH[SFUME] by default
   *
   *    FitpH[AS][x][0] changed from 12.7 to 12.71 on 27 April 2003
   *    FitpH[AS][x][1] changed from 13.085 to 13.095 on 27 April 2003
   *    FitpH[AS][x][2] changed from 13.185 to 13.195 on 27 April 2003
   *
   *    FitpH[CAS2][x][0] changed from 12.7 to 12.71 on 27 April 2003
   *    FitpH[CAS2][x][1] changed from 13.085 to 13.100 on 27 April 2003
   *    FitpH[CAS2][x][2] changed from 13.185 to 13.200 on 27 April 2003
   ***/

  x = 0;
  y = 1;

  for (k = POROSITY; k <= NSPHASES; k++) {
    if (Verbose) {
      switch (k) {
      case POROSITY:
        strcpy(buff, "POROSITY");
        break;
      case C3S:
        strcpy(buff, "C3S");
        break;
      case C2S:
        strcpy(buff, "C2S");
        break;
      case C3A:
        strcpy(buff, "C3A");
        break;
      case C4AF:
        strcpy(buff, "C4AF");
        break;
      case NA2SO4:
        strcpy(buff, "NA2SO4");
        break;
      case K2SO4:
        strcpy(buff, "K2SO4");
        break;
      case GYPSUM:
        strcpy(buff, "GYP");
        break;
      case HEMIHYD:
        strcpy(buff, "HEM");
        break;
      case ANHYDRITE:
        strcpy(buff, "ANH");
        break;
      case SFUME:
        strcpy(buff, "SFUME");
        break;
      case AMSIL:
        strcpy(buff, "AMSIL");
        break;
      case INERT:
        strcpy(buff, "INERT");
        break;
      case INERTAGG:
        strcpy(buff, "AGG");
        break;
      case ASG:
        strcpy(buff, "ASG");
        break;
      case CAS2:
        strcpy(buff, "CAS2");
        break;
      case SLAG:
        strcpy(buff, "SLAG");
        break;
      case CH:
        strcpy(buff, "CH");
        break;
      case CSH:
        strcpy(buff, "CSH");
        break;
      case ETTR:
        strcpy(buff, "ETTR");
        break;
      case ETTRC4AF:
        strcpy(buff, "ETTRC4AF");
        break;
      case AFM:
        strcpy(buff, "AFM");
        break;
      case C3AH6:
        strcpy(buff, "C3AH6");
        break;
      case FH3:
        strcpy(buff, "FH3");
        break;
      case CACO3:
        strcpy(buff, "CACO3");
        break;
      case FREELIME:
        strcpy(buff, "FREELIME");
        break;
      case OC3A:
        strcpy(buff, "OC3A");
        break;
      case BRUCITE:
        strcpy(buff, "BRUCITE");
        break;
      case MS:
        strcpy(buff, "MS");
        break;
      case STRAT:
        strcpy(buff, "STRAT");
        break;
      case FRIEDEL:
        strcpy(buff, "FRIEDEL");
        break;
      case AFMC:
        strcpy(buff, "AFMC");
        break;
      case CACL2:
        strcpy(buff, "CACL2");
        break;
      case FAC3A:
        strcpy(buff, "FAC3A");
        break;
      case FLYASH:
        strcpy(buff, "FLYASH");
        break;
      case POZZCSH:
        strcpy(buff, "POZZCSH");
        break;
      case SLAGCSH:
        strcpy(buff, "SLAGCSH");
        break;
      case GYPSUMS:
        strcpy(buff, "GYPS");
        break;
      case ABSGYP:
        strcpy(buff, "ABSGYP");
        break;
      default:
        strcpy(buff, "UNKNOWN");
        break;
      }
    }

    /* Set PHfactor to 1.0 initially */

    PHfactor[k] = 1.0;

    fscanf(fprmfile, "%s %s", name, instring);
    Discoeff[k] = atof(instring);
    if (Verbose) {
      printf("\n%s:\n", buff);
      printf("\t%s %f\n", name, Discoeff[k]);
    }
    if (feof(fprmfile)) {
      printf("Premature end of parameter file!!\n");
      return (1);
    }
    for (i = x; i <= y; i++) {
      for (j = 0; j < 3; j++) {
        fscanf(fprmfile, "%s %s", name, instring);
        FitpH[k][i][j] = atof(instring);
        if (Verbose)
          printf("\t%s %f\n", name, FitpH[k][i][j]);
        if (feof(fprmfile)) {
          printf("Premature end of parameter file!!\n");
          return (1);
        }
      }
    }
    fscanf(fprmfile, "%s %s", name, instring);
    PHsulfcoeff[k] = atof(instring);
    if (Verbose)
      printf("\t%s %f\n", name, PHsulfcoeff[k]);
    if (feof(fprmfile)) {
      printf("Premature end of parameter file!!\n");
      return (1);
    }
    if (k == CSH) {
      fscanf(fprmfile, "%s %s", name, instring);
      Molarvcshcoeff_T = atof(instring);
      if (Verbose)
        printf("\t%s %f\n", name, Molarvcshcoeff_T);
      if (feof(fprmfile)) {
        printf("Premature end of parameter file!!\n");
        return (1);
      }
      fscanf(fprmfile, "%s %s", name, instring);
      Watercshcoeff_T = atof(instring);
      if (Verbose)
        printf("\t%s %f\n", name, Watercshcoeff_T);
      if (feof(fprmfile)) {
        printf("Premature end of parameter file!!\n");
        return (1);
      }
      fscanf(fprmfile, "%s %s", name, instring);
      Molarvcshcoeff_pH = atof(instring);
      if (Verbose)
        printf("\t%s %f\n", name, Molarvcshcoeff_pH);
      if (feof(fprmfile)) {
        printf("Premature end of parameter file!!\n");
        return (1);
      }
      fscanf(fprmfile, "%s %s", name, instring);
      Watercshcoeff_pH = atof(instring);
      if (Verbose)
        printf("\t%s %f\n", name, Watercshcoeff_pH);
      if (feof(fprmfile)) {
        printf("Premature end of parameter file!!\n");
        return (1);
      }
      Molarvcshcoeff_sulf = -10.0;
    }
  }

  fclose(fprmfile);

  /***
   *    Done reading parameters from parameter file.  These are
   *    the parameters that previously were hard-wired at compile
   *    time.
   *
   *    Next, read the user-input variables for the hydration
   *    simulation in question
   ***/

  printf("Enter random number seed \n");
  read_string(instring, sizeof(instring));
  Iseed = atoi(instring);
  if (Iseed > 0)
    Iseed = (-1 * Iseed);
  printf("%d\n", Iseed);
  Seed = (&Iseed);

  if (Verbose)
    printf("Dissolution bias is set at %f \n", DISBIAS);

  /***
   *    Open file and read in original cement
   *    particle microstructure
   ***/

  printf("Enter name of directory containing initial microstructure files\n");
  printf("Be sure to include final file separator:  ");
  read_string(Micdir, sizeof(Micdir));
  Filesep = Micdir[strlen(Micdir) - 1];
  if ((Filesep != '/') && (Filesep != '\\')) {
    printf("\nNo final file separator found.  Using /");
    Filesep = '/';
  }
  printf("%s\n", Micdir);
  printf("Enter name of file from which the initial ");
  printf("microstructure will be read\n");
  read_string(name, sizeof(name));
  printf("%s\n", name);
  nlen = strcspn(name, ".");
  strncpy(Fileroot, name, nlen);
  sprintf(imgfile, "%s%s", Micdir, name);
  if (Verbose)
    printf("nlen is %d and Fileroot is now %s \n", nlen, Fileroot);

  printf("\nEnter name of particle image file:  ");
  read_string(name, sizeof(name));
  printf("%s\n", name);
  sprintf(pimgfile, "%s%s", Micdir, name);

  printf("\nEnter name of directory to store OUTPUT files\n");
  printf("Be sure to include final file separator:  ");
  read_string(Outputdir, sizeof(Outputdir));
  printf("%s\n", Outputdir);

  /***
   *    Assign various physical properties of phases
   ***/

  assign_properties();

  printf("Enter fraction of C3A that is to be orthorhombic ");
  printf("instead of cubic: ");
  read_string(instring, sizeof(instring));
  Oc3afrac = atof(instring);
  printf("%f\n", Oc3afrac);

  printf("Enter number of seeds for CSH nucleation per um3 of mix water: ");
  read_string(instring, sizeof(instring));
  Csh_seeds = atof(instring);
  printf("%f\n", Csh_seeds);

  printf("Enter aging time in days: ");
  read_string(instring, sizeof(instring));
  End_time = atof(instring);
  printf("\n%f \n", End_time);
  End_time *= 24.0; /* Convert days to hours */

  printf("Place a crack (y or n)? [n] ");
  read_string(answer, sizeof(answer));
  printf("%s\n", answer);
  if (strlen(answer) < 1) {
    strcpy(answer, "n");
  }

  if (toupper(answer[0]) == 'Y') {
    printf("\nEnter total crack width (in pixels): ");
    read_string(instring, sizeof(instring));
    Crackwidth = atoi(instring);
    printf("%d", Crackwidth);
    printf("\nEnter time at which to crack (in h): ");
    read_string(instring, sizeof(instring));
    Cracktime = atof(instring);
    printf("%f", Cracktime);
    printf("\nEnter orientation of crack as follows:");
    printf("\n\t 1 = parallel to yz plane");
    printf("\n\t 2 = parallel to xz plane");
    printf("\n\t 3 = parallel to xy plane");
    printf("\nOrientation: ");
    read_string(instring, sizeof(instring));
    Crackorient = atoi(instring);
    if (Crackorient > 3)
      Crackorient = 3;
    printf("%d\n", Crackorient);

  } else {
    Crackwidth = 0;
    Cracktime = -1.0;
    Crackorient = 1;
  }

  printf("Customize times for outputting microstructure (y or n)? [n] ");
  read_string(answer, sizeof(answer));
  printf("%s\n", answer);
  if (strlen(answer) < 1) {
    strcpy(answer, "n");
  }

  if (toupper(answer[0]) == 'Y') {
    Tcustomoutputentries = 0;
    sprintf(custcycfile, "%scustomoutput.dat", Outputdir);
    fcofile = filehandler("disrealnew", custcycfile, "READ");
    if (!fcofile) {
      freeallmem();
      exit(1);
    }
    while (!feof(fcofile)) {
      fscanf(fcofile, "%s", buff);
      if (!feof(fcofile))
        Tcustomoutputentries++;
    }

    CustomImageTime = fvector(Tcustomoutputentries);
    if (!CustomImageTime) {
      freeallmem();
      exit(1);
    }

    fclose(fcofile);
    fcofile = filehandler("disrealnew", custcycfile, "READ");
    if (!fcofile) {
      freeallmem();
      exit(1);
    }
    for (i = 0; i < Tcustomoutputentries; i++) {
      fscanf(fcofile, "%s", buff);
      CustomImageTime[i] = atof(buff);
    }
    fclose(fcofile);

  } else {
    CustomImageTime = NULL;
    printf("Output hydrating microstructure every ____ hours: ");
    read_string(instring, sizeof(instring));
    OutTimefreq = atof(instring);
    printf("\n%f\n", OutTimefreq);
  }

  /****
   *    NOTE:  MUST READ
   *            (1) SOFTWARE VERSION OF INPUT FILE (Version)
   *            (1) SYSTEM SIZE (Xsyssize,Ysyssize,Zsyssize)
   *            (2) SYSTEM RESOLUTION (Res)
   *
   *    Then set global variables Syspix, Sizemag, Isizemag
   *    rather than hardwiring them as preprocessor
   *    defines
   ****/

  fimgfile = filehandler("disrealnew", imgfile, "READ");
  if (!fimgfile) {
    return (1);
  }

  if (read_imgheader(fimgfile, &Version, &Xsyssize_orig, &Ysyssize_orig,
                     &Zsyssize_orig, &Res)) {
    fclose(fimgfile);
    freeallmem();
    bailout("disrealnew", "Error reading image header");
    exit(1);
  }

  if (Verbose) {
    printf("\nDone reading image header...\n");
    printf("\tVersion = %f\n", Version);
    printf("\tX size = %d\n", Xsyssize_orig);
    printf("\tY size = %d\n", Ysyssize_orig);
    printf("\tZ size = %d\n", Ysyssize_orig);
    printf("\tResolution = %f\n", Res);
    fflush(stdout);
  }

  Xsyssize = Xsyssize_orig;
  Ysyssize = Ysyssize_orig;
  Zsyssize = Zsyssize_orig;

  Syspix = Xsyssize * Ysyssize * Zsyssize;
  Syspix_orig = Syspix;
  Sizemag = ((float)Syspix) / (pow(((double)(DEFAULTSYSTEMSIZE)), 3.0));
  if (Verbose)
    printf("\nSizemag = %f", Sizemag);
  Sizemag_orig = Sizemag;
  Isizemag = (int)(Sizemag + 0.5);
  Isizemag_orig = Isizemag;

  if (Crackorient == 1)
    Xsyssize += Crackwidth;
  if (Crackorient == 2)
    Ysyssize += Crackwidth;
  if (Crackorient == 3)
    Zsyssize += Crackwidth;

  /***
   *    Must now allocate the memory for all the 3D arrays
   *    (See disrealnew.h for their declaration)
   ***/

  if (Verbose)
    printf("\tAllocating Mic with dimensions %d %d %d...", Xsyssize, Ysyssize,
           Zsyssize);
  Mic = cbox(Xsyssize, Ysyssize, Zsyssize);
  if (!Mic) {
    freeallmem();
    fclose(fimgfile);
    bailout("disrealnew", "Could not allocate memory for Mic array");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Micorig ...");

  Micorig = cbox(Xsyssize, Ysyssize, Zsyssize);
  if (!Micorig) {
    freeallmem();
    fclose(fimgfile);
    bailout("disrealnew", "Could not allocate memory for Micorig array");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Micpart ...");

  Micpart = sibox(Xsyssize, Ysyssize, Zsyssize);
  if (!Micpart) {
    freeallmem();
    fclose(fimgfile);
    bailout("disrealnew", "Could not allocate memory for Micpart array");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Cshage ...");

  Cshage = sibox(Xsyssize, Ysyssize, Zsyssize);
  if (!Cshage) {
    freeallmem();
    fclose(fimgfile);
    bailout("disrealnew", "Could not allocate memory for Cshage array");
    return (1);
  }
  if (Verbose)
    printf(" done\n\tAllocating Deactivated ...");

  Deactivated = sibox(Xsyssize, Ysyssize, Zsyssize);
  if (!Deactivated) {
    fclose(fimgfile);
    freeallmem();
    bailout("disrealnew", "Could not allocate memory for Deactivated array");
    return (1);
  }
  if (Verbose)
    printf(" done\n");

  Cshscale = CSHSCALE * Sizemag;
  C3ah6_scale = C3AH6_SCALE * Sizemag;

  /***
   *    Adjust the maximum number of diffusion steps
   *    per cycle based on system resolution.  That is,
   *    if each step is 0.5 microns instead of 1.0 microns
   *    and we want the same RMS distance to be achieved
   *    in a cycle, then we need (1/0.5)^2 the steps we
   *    had originally
   ***/

  Maxdiffsteps = MAXDIFFSTEPS / (Res * Res);

  /****************************************/

  /***
   *    Reset Xsyssize, Ysyssize, and Zsyssize back to
   *    the original system size until the microstructure
   *    actually cracks
   ***/

  Xsyssize = Xsyssize_orig;
  Ysyssize = Ysyssize_orig;
  Zsyssize = Zsyssize_orig;

  if (Verbose)
    printf("\nPreparing to read image file ...");
  for (ix = 0; ix < Xsyssize; ix++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 0; iz < Zsyssize; iz++) {

        Cshage[ix][iy][iz] = 0;
        Deactivated[ix][iy][iz] = 1;
        fscanf(fimgfile, "%s", instring);
        ovalin = atoi(instring);
        valin = convert_id(ovalin, Version);

        /***
         * Check if C3A needs to be converted to orthorhombic
         ***/

        if (valin == C3A) {
          pc3a = ran1(Seed);
          if (pc3a < Oc3afrac) {
            valin = OC3A;
          }
        }
        Mic[ix][iy][iz] = valin;

        Micorig[ix][iy][iz] = Mic[ix][iy][iz];

      } /* End of loop in iz */
    } /* End of loop in iy */
  } /* End of loop in ix */

  fclose(fimgfile);
  if (Verbose)
    printf(" done\n");

  /* Now read in particle IDs from file */

  fpimgfile = filehandler("disrealnew", pimgfile, "READ");
  if (!fpimgfile) {
    printf("\nCould not open fpimgfile: %s. Exiting ...", pimgfile);
    fflush(stdout);
    freeallmem();
    exit(1);
  }

  /***
   *    As before, must either read in the first
   *    two lines of size and resolution
   *    information ...
   ***/

  if (read_imgheader(fpimgfile, &newver, &newx, &newy, &newz, &newres)) {
    printf("\nTrouble reading header of fpimgfile: %s. Exiting ...", pimgfile);
    fflush(stdout);
    fclose(fpimgfile);
    freeallmem();
    bailout("disrealnew", "Error reading image header");
    exit(1);
  }

  for (ix = 0; ix < Xsyssize; ix++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 0; iz < Zsyssize; iz++) {

        fscanf(fpimgfile, "%s", instring);
        valin = atoi(instring);
        Micpart[ix][iy][iz] = valin;
      }
    }
  }

  fclose(fpimgfile);

  if (Version != newver) {
    printf("WARNING: Some files were created with differing\n");
    printf("\tVCCTL software versions.  This may create a");
    printf("\tconflict.");
  }
  if (Xsyssize != newx) {
    printf("Xsyssize = %d, New x size = %d", Xsyssize, newx);
    fflush(stdout);
    freeallmem();
    bailout("disrealnew", "Incompatible size declarations");
    exit(1);
  }

  if (Ysyssize != newy) {
    printf("Ysyssize = %d, New y size = %d", Ysyssize, newy);
    fflush(stdout);
    freeallmem();
    printf("Ysyssize = %d, New y size = %d", Ysyssize, newy);
    bailout("disrealnew", "Incompatible size declarations");
    exit(1);
  }

  if (Zsyssize != newz) {
    printf("Zsyssize = %d, New y size = %d", Ysyssize, newy);
    fflush(stdout);
    freeallmem();
    bailout("disrealnew", "Incompatible size declarations");
    exit(1);
  }

  /***
   *    Allow user to iteratively add one-pixel
   *    particles of various phases.
   *
   *    VCCTL software adds the one-pixel particles at the
   *    microstructure creation stage rather than here, but
   *    we keep this structure in place for possible manual
   *    addition of one-pixel particles by the user.
   ***/

  printf("Enter number of one pixel particles to add (-1 to quit) \n");
  fflush(stdout);
  read_string(instring, sizeof(instring));
  nadd = atoi(instring);
  printf("%d\n", nadd);

  while (nadd >= 0) {

    onepixfloc = 0; /* No flocculation of one-pixel particles */
    /*
    printf("Should these particles flocculate ");
    printf("to surfaces? No (0) or Yes (1): ");
    read_string(instring,sizeof(instring));
    onepixfloc = atoi(instring);
    */

    printf("Enter dissolution bias for these one pixel particles\n");
    read_string(instring, sizeof(instring));
    bias = atof(instring);
    printf("%f\n", bias);

    printf("Enter phase to add \n");
    if (Verbose) {
      printf("\tC3S %d\n", C3S);
      printf("\tC2S %d\n", C2S);
      printf("\tC3A %d\n", C3A);
      printf("\tC4AF %d\n", C4AF);
      printf("\tGYPSUM %d\n", GYPSUM);
      printf("\tHEMIHYD %d\n", HEMIHYD);
      printf("\tANHYDRITE %d\n", ANHYDRITE);
      printf("\tSILICA FUME %d\n", SFUME);
      printf("\tINERT %d\n", INERT);
      printf("\tSLAG %d\n", SLAG);
      printf("\tASG %d\n", ASG);
      printf("\tCAS2 %d\n", CAS2);
      printf("\tAMORPHOUS SILICA %d\n", AMSIL);
      printf("\tCH %d\n", CH);
      printf("\tCSH %d\n", CSH);
      printf("\tC3AH6 %d\n", C3AH6);
      printf("\tEttringite %d\n", ETTR);
      printf("\tStable Ettringite from C4AF %d\n", ETTRC4AF);
      printf("\tAFM %d\n", AFM);
      printf("\tFH3 %d\n", FH3);
      printf("\tPOZZCSH %d\n", POZZCSH);
      printf("\tSLAGCSH %d\n", SLAGCSH);
      printf("\tCACL2 %d\n", CACL2);
      printf("\tFriedels salt %d\n", FRIEDEL);
      printf("\tStratlingite %d\n", STRAT);
      printf("\tCalcium carbonate %d\n", CACO3);
      printf("\tAFmc %d\n", AFMC);
      printf("\tBrucite %d\n", BRUCITE);
      printf("\tMS %d\n", MS);
      printf("\tFree Lime %d\n", FREELIME);
    }

    read_string(instring, sizeof(instring));
    phtodo = atoi(instring);
    printf("%d \n", phtodo);

    if ((phtodo < 0) || (phtodo > NSPHASES)) {
      freeallmem();
      bailout("disrealnew", "Bad ID for one-pixel particle");
      exit(1);
    }

    Onepixelbias[phtodo] = bias;

    if (nadd > 0)
      addrand(phtodo, nadd, onepixfloc);

    printf("Enter number of one pixel particles ");
    printf("to add (-1 to quit) \n");
    read_string(instring, sizeof(instring));
    nadd = atoi(instring);
    printf("%d\n", nadd);
  }

  fflush(stdout);

  /***
   *    Parameters for adiabatic temperature rise calculation
   ***/

  printf("Enter the initial temperature of binder ");
  printf("in degrees Celsius \n");
  read_string(instring, sizeof(instring));
  Temp_0 = atof(instring);
  printf("%f \n", Temp_0);
  Temp_cur_b = Temp_0;

  printf("Hydration under 0) isothermal, 1) adiabatic ");
  printf("or 2) programmed temperature history conditions \n");
  read_string(instring, sizeof(instring));
  Adiaflag = atoi(instring);
  printf("%d \n", Adiaflag);
  AggTempEffect = 1;
  if ((Adiaflag == 0) || (Mass_agg * Cp_agg <= 0.0) ||
      (fabs(Temp_0_agg - Temp_0) < 0.5) || (U_coeff_agg <= 0.0))
    AggTempEffect = 0;

  printf("Enter the ambient temperature ");
  printf("in degrees Celsius \n");
  read_string(instring, sizeof(instring));
  T_ambient = atof(instring);
  printf("%f \n", T_ambient);

  printf("Enter the overall heat transfer coefficient ");
  printf("in J/g/C/s \n");
  read_string(instring, sizeof(instring));
  U_coeff = atof(instring);
  printf("%f \n", U_coeff);

  printf("Enter apparent activation energy for hydration ");
  printf("in kJ/mole \n");
  read_string(instring, sizeof(instring));
  E_act = atof(instring);
  printf("%f \n", E_act);

  printf("Enter apparent activation energy for pozzolanic ");
  printf("reactions in kJ/mole \n");
  read_string(instring, sizeof(instring));
  E_act_pozz = atof(instring);
  printf("%f \n", E_act_pozz);

  printf("Enter apparent activation energy for slag ");
  printf("reactions in kJ/mole \n");
  read_string(instring, sizeof(instring));
  E_act_slag = atof(instring);
  printf("%f \n", E_act_slag);

  printf("Calibrate time using beta factor (0), ");
  printf("early-age calorimetry data (1), or ");
  printf("early-age chemical shrinkage data (2): ");
  read_string(instring, sizeof(instring));
  TimeCalibrationMethod = atoi(instring);
  if (TimeCalibrationMethod == BETAFACTOR) {
    printf("\nEnter kinetic factor to convert cycles ");
    printf("to time at 25 C \n");
    read_string(instring, sizeof(instring));
    Beta = atof(instring);
    printf("%f \n", Beta);
  } else {
    printf("\nEnter file name for early-age data: ");
    read_string(name, sizeof(name));
    printf("\n%s \n", name);
    sprintf(calfilename, "%s", name);

    /***
     *  At this point, the isothermal calorimetry file
     *  must have data taken
     *  AT 25 degrees C.  We will correct the time scale using the
     *  user-supplied activation energy for hydration
     ***/

    fcalfile = filehandler("disrealnew", calfilename, "READ");
    if (!fcalfile) {
      freeallmem();
      sprintf(buff, "Could not open time calibration ");
      sprintf(buff, "file %s", calfilename);
      bailout("disrealnew", buff);
      return (1);
    }

    /***
     * The calorimetry file must be two-column ASCII text file.
     * First column must be time in hours, second column must
     * be CUMULATIVE heat in J per gram of CEMENT initially.
     * There must be a header line, but it does not matter
     * what is on it.
     ***/

    NDataLines = 0;
    do {
      ch = getc(fcalfile);
    } while (ch != '\n' && !feof(fcalfile));

    while (!feof(fcalfile)) {
      fscanf(fcalfile, "%s %s", buff1, buff2);
      if (!feof(fcalfile))
        NDataLines++;
    }

    if (NDataLines == 0) {
      freeallmem();
      sprintf(buff, "Calibration file ended ");
      sprintf(buff, "prematurely: %s", calfilename);
      bailout("disrealnew", buff);
      return (1);
    }

    /***
     * Allocate memory for storing calibration data in DataTime
     * and DataValue vectors.
     ***/

    DataTime = fvector(NDataLines);
    if (!DataTime) {
      freeallmem();
      fclose(fcalfile);
      bailout("disrealnew", "Could not allocate memory for DataTime array");
      return (1);
    }

    DataValue = fvector(NDataLines);
    if (!DataValue) {
      freeallmem();
      fclose(fcalfile);
      bailout("disrealnew", "Could not allocate memory for DataValue array");
      return (1);
    }

    /***
     * Now go back and read the data into the DataTime and DataValue vectors
     ***/

    rewind(fcalfile);
    do {
      ch = getc(fcalfile);
    } while (ch != '\n' && !feof(fcalfile));

    i = 0;
    if (Verbose)
      printf("\nNDataLines = %d", NDataLines);
    while ((i < NDataLines) && !feof(fcalfile)) {
      fscanf(fcalfile, "%s %s", buff1, buff2);
      if (i == 0) {
        DataTime[i] = atof(buff1);
        DataValue[i] = atof(buff2);
        if (Verbose) {
          printf("\nDataTime[%d] = %f, ", i, DataTime[i]);
          printf("DataValue[%d] = %f\n", i, DataValue[i]);
        }
        i++;
      } else {
        DataTime[i] = atof(buff1);
        DataValue[i] = atof(buff2);
        if ((DataTime[i] > DataTime[i - 1]) &&
            (DataValue[i] >= DataValue[i - 1]))
          i++;
      }
    }

    NDataLines = i;

    fclose(fcalfile);
    printf("Enter temperature at which calibration data ");
    printf("were obtained (in deg C): ");
    read_string(buff, sizeof(buff));
    printf("%s \n", buff);
    DataMeasuredAtTemperature = atof(buff);
  }

  /* Have enough information to calculate upper bound on number of cycles */

  if (TimeCalibrationMethod == BETAFACTOR) {
    b_estimate = Beta * exp((1000.0 * E_act / 8.314) *
                            ((1.0 / (Temp_0 + 273.15)) - (1.0 / 298.15)));
    Ncyc = (int)((2.0 * sqrt(End_time / b_estimate)) + 0.5);
  } else {
    /* No way to estimate Ncyc rationally, so set it to a very large value and
     * be prepared to allocate more memory as needed */
    Ncyc = 10000;
  }

  if (Crackwidth == 0)
    Cracktime = End_time + 100.0;
  if (CustomImageTime != NULL) {
    OutTimefreq = End_time + 1.0;
    printf("\nSetting DOH frequency for outputting ");
    printf("microstructure = %f\n", OutTimefreq);
    fflush(stdout);
  }

  /***
   *    Allocate memory for Time_cur, Molarvcsh, and Watercsh, which
   *    hold the time-dependent values of the molar volumes
   *    and water content of CSH
   ***/

  TimeHistory = fvector(Ncyc);
  if (!TimeHistory) {
    freeallmem();
    bailout("disrealnew", "Could not allocate memory for TimeHistory array");
    exit(1);
  }
  TimeHistory[0] = 0.0;

  Molarvcsh = fvector(Ncyc);
  if (!Molarvcsh) {
    freeallmem();
    bailout("disrealnew", "Could not allocate memory for Molarvcsh array");
    exit(1);
  }

  Watercsh = fvector(Ncyc);
  if (!Watercsh) {
    freeallmem();
    bailout("disrealnew", "Could not allocate memory for Watercsh array");
    exit(1);
  }

  printf("Enter maximum degree of hydration to achieve ");
  printf("before terminating \n");
  read_string(instring, sizeof(instring));
  Alpha_max = atof(instring);
  printf("%f \n", Alpha_max);

  printf("Do you wish hydration under 0) saturated ");
  printf("or 1) sealed conditions \n");
  read_string(instring, sizeof(instring));
  Sealed = atoi(instring);
  printf("%d \n", Sealed);

  Sealed_after_crack = Sealed;

  *pscalech *= Sizemag;
  if (Verbose) {
    printf("Nuc. prob. and scale factor for CH nucleation \n");
    printf("%f %f \n", *pnucch, *pscalech);
  }

  *pscalegyp *= Sizemag;
  if (Verbose) {
    printf("Nuc. prob. and scale factor for gypsum nucleation \n");
    printf("%f %f \n", *pnucgyp, *pscalegyp);
  }

  *pscalehg *= Sizemag;
  if (Verbose) {
    printf("Nuc. prob. and scale factor for C3AH6 nucleation \n");
    printf("%f %f \n", *pnuchg, *pscalehg);
  }

  *pscalefh3 *= Sizemag;
  if (Verbose) {
    printf("Nuc. prob. and scale factor for FH3 nucleation \n");
    printf("%f %f \n", *pnucfh3, *pscalefh3);
  }

  printf("Enter time frequency for checking pore ");
  printf("space percolation (in h): ");
  read_string(instring, sizeof(instring));
  Burntimefreq = atof(instring);
  printf("\n%f\n", Burntimefreq);

  printf("Enter time frequency for checking percolation ");
  printf("of solids (set) (in h): ");
  read_string(instring, sizeof(instring));
  Settimefreq = atof(instring);
  printf("\n%f\n", Settimefreq);

  printf("Enter time frequency for checking hydration ");
  printf("of particles (in h): ");
  read_string(instring, sizeof(instring));
  Phydtimefreq = atof(instring);
  printf("\n%f\n", Phydtimefreq);

  printf("Enter mass fraction of aggregate in concrete \n");
  read_string(buff, sizeof(buff));
  printf("%s \n", buff);
  Mass_agg = (double)(atof(buff));

  printf("Enter initial temperature of aggregate in concrete \n");
  read_string(instring, sizeof(instring));
  Temp_0_agg = atof(instring);
  printf("%f \n", Temp_0_agg);
  Temp_cur_agg = Temp_0_agg;

  printf("Enter heat transfer coefficient between aggregate and binder \n");
  read_string(instring, sizeof(instring));
  U_coeff_agg = atof(instring);
  printf("%f \n", U_coeff_agg);

  printf("CSH to pozzolanic CSH 0) prohibited or 1) allowed \n");
  read_string(instring, sizeof(instring));
  Csh2flag = atoi(instring);
  printf("%d \n", Csh2flag);

  printf("CH precipitation on aggregate surfaces ");
  printf("0) prohibited or 1) allowed \n");
  read_string(instring, sizeof(instring));
  Chflag = atoi(instring);
  printf("%d \n", Chflag);

  printf("Output hydration movie frame every ____ hours: ");
  read_string(instring, sizeof(instring));
  MovieFrameFreq = atof(instring);
  if (MovieFrameFreq > End_time)
    MovieFrameFreq = End_time + 1.0;
  if (MovieFrameFreq <= 0.0)
    MovieFrameFreq = End_time + 1.0;
  printf("\n%f \n", MovieFrameFreq);

  *nmovstep = 1;
  if ((MovieFrameFreq > 0.0) && (MovieFrameFreq < 1.0)) {
    *nmovstep = (int)(End_time / MovieFrameFreq);
    if (*nmovstep < 1)
      *nmovstep = 1;
  }

  /***
   *    Allow user to iteratively specify surface
   *    deactivation parameters for particles of various
   *    phases.  First initialize all the deactivation
   *    arrays to zero, and then gather the information
   ***/

  for (i = 0; i <= NSPHASES; i++) {
    Deactfrac[i] = 0.0;
    Reactfrac[i] = 0.0;
    Deactinit[i] = 0;
    Deactends[i] = 0;
    Deactterm[i] = 0;
    Deactphaselist[i] = 0;
    Startflag[i] = 0;
    Stopflag[i] = 0;
  }

  printf("Enter phase id of surface to deactivate (-1 to quit) \n");
  read_string(instring, sizeof(instring));
  dphase = atoi(instring);
  printf("%d\n", dphase);

  Numdeact = 0;
  while (dphase != -1) {
    deactphase = dphase;

    printf("Enter fraction of surface to deactivate \n");
    read_string(instring, sizeof(instring));
    dfrac = atof(instring);
    printf("%f\n", dfrac);
    Deactfrac[deactphase] = dfrac;

    Deactphaselist[Numdeact] = deactphase;
    Numdeact++;

    if ((deactphase < C3S) || (deactphase > NSPHASES)) {
      freeallmem();
      bailout("disrealnew", "Bad ID for deactivated phase");
      exit(1);
    }

    printf("Time to implement deactivation (in hours)\n");
    read_string(instring, sizeof(instring));
    Deactinit[deactphase] = atof(instring);
    printf("%f\n", Deactinit[deactphase]);

    printf("Time to begin reactivation (in hours)\n");
    read_string(instring, sizeof(instring));
    dends = atof(instring);
    printf("%f\n", dends);
    Deactends[deactphase] = dends;

    printf("Time of full reactivation (in hours)\n");
    read_string(instring, sizeof(instring));
    dterm = atof(instring);
    printf("%f\n", dterm);
    Deactterm[deactphase] = dterm;

    if (dterm == dends) {
      Reactfrac[deactphase] = 1.0;
    } else {
      Reactfrac[deactphase] = 1.0 / (dterm - dends + 1);
    }

    printf("Enter phase id of surface to deactivate (-1 to quit) \n");
    read_string(instring, sizeof(instring));
    dphase = atoi(instring);
    printf("%d\n", dphase);
  }

  printf("Does pH influence hydration kinetics ");
  printf("0) no or 1) yes \n");
  read_string(instring, sizeof(instring));
  PHactive = atoi(instring);
  printf("%d\n", PHactive);

  /***
   *    Set possibility of topochemical conversion of silicates
   *    to CSH if pH effect is active, and also set the proximity
   *    within which dissolved silicates are placed relative to the
   *    dissolution source, to simulate the higher-density CSH
   *    that is thought to form in the presence of alkalies
   *    (see Juenger and Jennings, ACI Materials Journal,
   *    Vol. 98, No. 3, pp. 251-255 (2001).
   ***/

  fflush(stdout);
  return (status);
}

/***
 *    init
 *
 *     Initialize values for solubilities, pH effect, etc.
 *
 *     Arguments:    none
 *     Returns:    nothing
 *
 *    Calls:        no routines
 *    Called by:    main program
 ***/
void init(void) {
  int i, k, x, y;
  float xv1, xv2, xv3, yv1, yv2, yv3;
  float chperslag, poreperslag;
  float resfact;
  char buff[MAXSTRING], instring[MAXSTRING];
  FILE *slagfile, *alkalifile;

  Ngoing = 0;
  Porefl1 = Porefl2 = Porefl3 = 1;
  Pore_off = Water_off = 0;
  Heat_old = Heat_new = 0.0;

  /* Current and previous cycle CH counts */

  Chold = Chnew = 0;

  /* Elapsed time according to maturity principles */

  Time_cur = 0.0;
  Poregone = Poretodo = 0;

  /* Initialize counters, etc. */

  Nsilica_rx = Nasr = Nslagr = 0;
  Nsilica = 0;
  Ncsbar = 0;
  Netbar = 0;
  Porinit = 0;
  Cyccnt = 0;
  Setflag = 0;
  C3sinit = C2sinit = C3ainit = C4afinit = Crackpinit = 0;
  Anhinit = Heminit = Slaginit = Freelimeinit = 0;
  Nasulfinit = Ksulfinit = 0;

  /* Initialize structure for Ants */

  Headant = (struct Ants *)malloc(Antsize);
  Headant->prevant = NULL;
  Headant->nextant = NULL;
  Headant->x = 0;
  Headant->y = 0;
  Headant->z = 0;

  /* special ID indicating first ant in list */
  Headant->id = 100;
  Headant->cycbirth = 0;
  Tailant = Headant;

  /* Initialize potassium sulfate doubly linked list */
  Headks = (struct Alksulf *)malloc(Alksulfsize);
  Headks->prevas = NULL;
  Headks->nextas = NULL;
  Headks->x = 0;
  Headks->y = 0;
  Headks->z = 0;
  Tailks = Headks;

  /* Initialize sodium sulfate doubly-linked list */
  Headnas = (struct Alksulf *)malloc(Alksulfsize);
  Headnas->prevas = NULL;
  Headnas->nextas = NULL;
  Headnas->x = 0;
  Headnas->y = 0;
  Headnas->z = 0;
  Tailnas = Headnas;

  /* Set initial pH of pore solution at time t = 0 */

  PH_cur = 7.0;

  resfact = pow((1.0 / Res), 1.25);

  for (i = C3S; i <= NSPHASES; i++) {

    /***
     *    Source of the following data is
     *    H.F.W. Taylor, "Cement Chemistry" 2nd Edition. Telford
     *    Publishing, London, 1997.
     *
     *    NOTE that for the first cycle, of the clinker phases
     *    only the aluminates and gypsum are soluble (silicates
     *    are not soluble initially)
     ***/

    /***
     *    Soluble[x] - flag indicating if phase x is soluble
     *    Disprob[x] - probability of dissolution (relative diss. rate)
     ***/

    if (Verbose)
      printf("\nSetting Disbase[%d]: resfact = %f, Discoeff[%d] = %f, DISBIAS "
             "= %f",
             i, resfact, i, Discoeff[i], DISBIAS);
    Disprob[i] = Disbase[i] = resfact * Discoeff[i] / DISBIAS;

    switch (i) {

    case C3S:
      Soluble[i] = 0;
      Creates[i] = DIFFCSH;
      break;

    case C2S:
      Soluble[i] = 0;
      Creates[i] = DIFFCSH;
      break;

    case C3A:
      Soluble[i] = 1;

      /***
       *    Default value of Discoeff increased back
       *    to 0.4 from 0.25 7/8/99
       ***/

      Creates[i] = POROSITY;
      break;

    case OC3A:
      Soluble[i] = 1;
      Creates[i] = POROSITY;
      break;

    case C4AF:
      Soluble[i] = 1;
      Creates[i] = POROSITY;
      break;

    case K2SO4:
      Soluble[i] = 1;
      Creates[i] = POROSITY;
      break;

    case NA2SO4:
      Soluble[i] = 1;
      Creates[i] = POROSITY;
      break;

    case GYPSUM:
      Soluble[i] = 1;

      /***
       *    History of Discoeff values for GYPSUM
       *
       *    Changed from 0.05 to 0.015  9/29/98
       *    Changed to 0.040 10/15/98
       *    Back to 0.05 from 0.10 7/8/99
       *    From 0.05 to 0.02 4/4/00
       *    From 0.02 to 0.025 8/13/01
       *
       *    From 0.025 to 0.025 * DISBIAS, so that
       *    it can be divided by DISBIAS just like the
       *    others 16 July 2003
       ***/

      /***
       *    geaendert am 04.04.00, urspr. 0.05
       *    dissolved gypsum distributed at random
       *    throughout microstructure
       ***/

      Creates[i] = POROSITY;
      break;

    case GYPSUMS:
      Soluble[i] = 1;

      /***
       *    History of Discoeff values for GYPSUMS
       *
       *    Changed from 0.05 to 0.015  9/29/98
       *    Changed to 0.020 10/15/98
       *    From 0.02 to 0.025 8/13/01
       *
       *    From 0.025 to 0.025 * DISBIAS, so that
       *    it can be divided by DISBIAS just like the
       *    others 16 July 2003
       *
       *    And also changed all sulfate based
       *        dissolution rates
       ***/

      Creates[i] = POROSITY;
      break;

    case ANHYDRITE:
      Soluble[i] = 1;

      /***
       *    Set default anhydrite dissolution at 4/5ths
       *        of that of gypsum
       *
       *    Source: Uchikawa et al., CCR, 1984
       ***/

      /***
       *    Dissolved anhydrite distributed at random
       *    throughout microstructure
       ***/

      Creates[i] = POROSITY;
      break;

    case HEMIHYD:
      Soluble[i] = 1;

      /***
       *    Set default hemihydrate dissolution at
       *        3 times that of gypsum
       *
       *     Source: Uchikawa et al., CCR, 1984
       *
       *    Changed to 1.5 times that of gypsum 6/1/00
       ***/

      /***
       *    geändert am 01.06.00, urspr. 3.0
       *
       *    Dissolved hemihydrate distributed at random
       *    throughout microstructure
       ***/

      Creates[i] = POROSITY;
      break;

    case CH:

      /***
       *    CH soluble to allow for Ostwald
       *    ripening of crystals
       ***/

      Soluble[i] = 1;
      Creates[i] = DIFFCH;

      /***
       *    Solubility of CH known to decrease in the
       *    presence of alkali species.  See
       *    Sprung and Rechenberg, Proc. Symp. Effect
       *    of Alkalies on Properties of Concrete,
       *    C & CA London, Sept. 1976, p. 109 (1977),
       *    and Jawed and Skalny, Cem. Concr. Res. Vol. 8
       *    pp. 37-52 (1978).
       ***/

      break;

    case CACO3:

      /* CaCO3 is only mildly soluble by default */

      Soluble[i] = 1;
      Creates[i] = DIFFCACO3;
      break;

    case FREELIME:

      /* CaO is readily soluble */

      Soluble[i] = 1;
      Creates[i] = DIFFCH;
      break;

    case SLAG:

      /***
       *    Slag is not truly soluble, but use
       *    its dissolution probability for reaction
       *    probability
       ***/

      Soluble[i] = 0;
      Creates[i] = 0;
      break;

    case C3AH6:
      Soluble[i] = 1;

      /***
       *    Changed default value of Discoeff from 0.5
       *    to 0.01 06.09.00
       ***/

      Creates[i] = POROSITY;

      /***
       *    Solubility of hydrogarnet observed to depend on
       *    concentration of alkali species; see Jawed and
       *    Skalny, Cem. Concr. Res., Vol. 8 pp. 37-52 (1978),
       *    and Berger et al,m Oric, 6th Intl. Congr. Chemistry
       *    of Cement, suppl. paper, Moscow (1974).
       ***/

      break;

    case ETTR:

      /* Ettringite is initially INSOLUBLE */

      Soluble[i] = 0;

      /***
       *    Default value of Discoeff changed to
       *    0.008 from 0.020  3/11/99
       ***/

      Creates[i] = DIFFETTR;

      /***
       *    Solubility of ettringite observed to depend on
       *    concentration of alkali species; see Jawed and
       *    Skalny, Cem. Concr. Res., Vol. 8 pp. 37-52 (1978),
       *    and Berger et al,m Oric, 6th Intl. Congr. Chemistry
       *    of Cement, suppl. paper, Moscow (1974).
       ***/

      break;

    case ETTRC4AF:

      /***
       *    Iron-rich ettringite is INSOLUBLE by default,
       *    that it, Discoeff = 0.0 by default
       ***/

      Soluble[i] = 0;
      Creates[i] = ETTRC4AF;
      break;

    case CACL2:

      /* calcium chloride is soluble */

      Soluble[i] = 1;
      Creates[i] = DIFFCACL2;
      break;

    case ASG:

      /* aluminosilicate glass is soluble */

      Soluble[i] = 1;

      /***
       *    Decreased default Discoeff[ASG] from 0.2 to 0.055556
       *    to better fit experimental data of Xiuping Feng
       *    on flyash consumption
       *
       *    4 Apr 2003
       *
       *    Changed default Discoeff from 0.055556 to 0.051
       *
       *    27 Apr 2003
       ***/

      Creates[i] = DIFFAS;
      break;

    case CAS2:

      /* calcium aluminodisilicate is soluble */

      Soluble[i] = 1;

      /***
       *    Decreased default Discoeff[ASG] from 0.2 to 0.043478
       *    to better fit experimental data of Xiuping Feng
       *    on flyash consumption
       *
       *    4 Apr 2003
       *
       *    Changed default Discoeff from 0.043478 to 0.04
       *
       *    27 Apr 2003
       ***/

      Creates[i] = DIFFCAS2;
      break;

    default:
      Creates[i] = 0;
      Soluble[i] = 0;
    }
  }

  /***
   *    Read in values for alkali characteristics and
   *    convert them to fractions from percentages
   ***/

  sprintf(buff, "%salkalichar.dat", Outputdir);
  alkalifile = filehandler("disrealnew", buff, "READ");
  if (!alkalifile) {
    freeallmem();
    exit(1);
  }
  fscanf(alkalifile, "%s", instring);
  Totsodium = atof(instring);
  fscanf(alkalifile, "%s", instring);
  Totpotassium = atof(instring);
  fscanf(alkalifile, "%s", instring);
  Rssodium = atof(instring);
  fscanf(alkalifile, "%s", instring);
  Rspotassium = atof(instring);
  fscanf(alkalifile, "%s", buff);
  if (!feof(alkalifile)) {
    Sodiumhydrox = atof(buff);
    fscanf(alkalifile, "%s", instring);
    Potassiumhydrox = atof(instring);
  } else {
    Sodiumhydrox = 0.0;
    Potassiumhydrox = 0.0;
  }
  fclose(alkalifile);

  Totsodium /= 100.0;
  Totpotassium /= 100.0;
  Rssodium /= 100.0;
  Rspotassium /= 100.0;
  Sodiumhydrox /= 100.0;
  Potassiumhydrox /= 100.0;

  sprintf(buff, "%salkaliflyash.dat", Outputdir);
  alkalifile = filehandler("disrealnew", buff, "READ_NOFAIL");
  if (!alkalifile) {
    Totfasodium = 0.0;
    Totfapotassium = 0.0;
    Rsfasodium = 0.0;
    Rsfasodium = 0.0;
  } else {
    fscanf(alkalifile, "%s", instring);
    Totfasodium = atof(instring);
    fscanf(alkalifile, "%s", instring);
    Totfapotassium = atof(instring);
    fscanf(alkalifile, "%s", instring);
    Rsfasodium = atof(instring);
    fscanf(alkalifile, "%s", instring);
    Rsfapotassium = atof(instring);
    Totfasodium /= 100.0;
    Totfapotassium /= 100.0;
    Rsfasodium /= 100.0;
    Rsfapotassium /= 100.0;
    fclose(alkalifile);
  }

  /* Read in values for slag characteristics */

  sprintf(buff, "%sslagchar.dat", Outputdir);
  slagfile = filehandler("disrealnew", buff, "READ");
  if (!slagfile) {
    freeallmem();
    exit(1);
  }
  fscanf(slagfile, "%s", instring);
  ;
  fscanf(slagfile, "%s", instring);

  fscanf(slagfile, "%s", instring);
  Specgrav[SLAG] = atof(instring);

  fscanf(slagfile, "%s", instring);
  Specgrav[SLAGCSH] = atof(instring);

  fscanf(slagfile, "%s", instring);
  Molarv[SLAG] = atof(instring);

  fscanf(slagfile, "%s", instring);
  Molarv[SLAGCSH] = atof(instring);

  fscanf(slagfile, "%s", instring);
  Slagcasi = atof(instring);
  fscanf(slagfile, "%s", instring);
  Slaghydcasi = atof(instring);
  fscanf(slagfile, "%s", instring);
  Siperslag = atof(instring);
  fscanf(slagfile, "%s", instring);
  Waterc[SLAGCSH] = Siperslag * (atof(instring));

  /***
   *    No information about dehydration of
   *    Slag CSH, so assume the same behavior
   *    as for normal CSH, that is that about
   *    60% of the water (by mass) is retained
   *    at T = 105C.
   *
   *    (see H.F.W. Taylor, Mater. Res. Soc. Proc.
   *    Vol. 85, p. 47 (1987))
   ***/

  Nh2o[SLAGCSH][0] = Waterc[SLAGCSH];
  Nh2o[SLAGCSH][1] = 0.60 * Nh2o[SLAGCSH][0];

  fscanf(slagfile, "%s", instring);
  Slagc3a = atof(instring);
  fscanf(slagfile, "%s", instring);
  Slagreact = atof(instring);

  fclose(slagfile);

  Waterc[SLAG] = 0.0;
  Nh2o[SLAG][0] = 0.0;
  Nh2o[SLAG][1] = 0.0;
  Heatf[SLAG] = 0.0;

  Heatf[SLAGCSH] = 0.0;

  /* Compute slag probabilities as defined above */

  chperslag = Siperslag * (Slaghydcasi - Slagcasi) + (3.0 * Slagc3a);
  if (chperslag < 0.0)
    chperslag = 0.0;

  P2slag = Molarv[SLAG];
  P2slag += Molarv[CH] * chperslag;

  poreperslag = Waterc[SLAGCSH] - chperslag + Waterc[C3AH6] * Slagc3a;

  P2slag += Molarv[POROSITY] * poreperslag;
  P2slag -= Molarv[SLAGCSH];
  P2slag -= Molarv[C3AH6] * Slagc3a;
  P2slag /= Molarv[SLAG];

  P1slag = 1.0 - P2slag;

  P3slag = (Molarv[SLAGCSH] / Molarv[SLAG]) - P1slag;

  P4slag = chperslag * Molarv[CH] / Molarv[SLAG];

  P5slag = Slagc3a * Molarv[C3A] / Molarv[SLAG];
  if (P5slag > 1.0) {
    P5slag = 1.0;
    printf("WARNING:  C3A/slag value exceeded 1.0.  ");
    printf("Resetting to 1.0 \n");
  }
  if (Verbose) {
    printf("\nP1slag = %f", P1slag);
    printf("\nP2slag = %f", P2slag);
    printf("\nP3slag = %f", P3slag);
    printf("\nP4slag = %f", P4slag);
    printf("\nP5slag = %f", P5slag);
  }

  /***
   *    Set up second-order fit for pH effects on solubility/reactivity
   *    of cement phases and pozzolanic compounds
   ***/

  x = 0;
  y = 1;

  for (k = C3S; k <= NSPHASES; k++) {

    xv1 = FitpH[k][x][0];
    xv2 = FitpH[k][x][1];
    xv3 = FitpH[k][x][2];
    yv1 = FitpH[k][y][0];
    yv2 = FitpH[k][y][1];
    yv3 = FitpH[k][y][2];

    /***
     *    These are the three coefficients for a second order
     *    fit of PHfactor to pH for cement, evaluated later
     *    in this function.
     *
     *    10 April 2003
     ***/

    PHcoeff[k][2] = (yv3 - yv1) * (xv2 - xv1) - (yv2 - yv1) * (xv3 - xv1);

    PHcoeff[k][2] /= (((xv3 * xv3 - xv1 * xv1) * (xv2 - xv1)) -
                      ((xv2 * xv2 - xv1 * xv1) * (xv3 - xv1)));

    PHcoeff[k][1] = (yv2 - yv1) - (PHcoeff[k][2] * (xv2 * xv2 - xv1 * xv1));
    PHcoeff[k][1] /= (xv2 - xv1);

    PHcoeff[k][0] = yv1 - (PHcoeff[k][1] * xv1) - (PHcoeff[k][2] * xv1 * xv1);
  }

  return;
}

/***
 *    initialize_output_files
 *
 *     Sets up output file names, pointers, and prints headers where
 *     necessary.
 *
 *     Arguments:    none
 *     Returns:    0 if okay, nonzero otherwise
 *
 *    Calls:        no routines
 *    Called by:    main program
 ***/
int initialize_output_files(void) {
  int numchar, numsep, i, j;
  char strsuff[MAXSTRING], strsuffa[MAXSTRING], strsuffb[MAXSTRING];
  char sepchar, outputdirnosep[MAXSTRING], dfileroot[MAXSTRING];
  char *p;

  sprintf(strsuffa, ".%d.%1d", (int)Temp_0, Csh2flag);
  sprintf(strsuffb, "%1d%1d", Adiaflag, Sealed);
  strcpy(strsuff, strsuffa);
  strcat(strsuff, strsuffb);

  numchar = strlen(Outputdir);
  for (i = 0; i < (numchar - 1); i++) {
    outputdirnosep[i] = Outputdir[i];
  }
  outputdirnosep[numchar - 1] = '\0';
  sepchar = Outputdir[numchar - 1];

  /* Tokenize the string outputdirnosep */

  numsep = 0;
  for (i = 0; i < strlen(outputdirnosep) - 1; i++) {
    if (outputdirnosep[i] == sepchar)
      numsep++;
  }
  i = j = 0;
  while (j < numsep) {
    if (outputdirnosep[i] == sepchar)
      j++;
    i++;
  }
  p = &outputdirnosep[i];
  strcpy(dfileroot, p);
  if (Verbose) {
    printf("\nOutputdir is: %s", Outputdir);
    printf("\noutputdirnosep is: %s", outputdirnosep);
    printf("\nSeparation character is %c", sepchar);
    printf("Number of separation characters is %d", numsep);
    printf("\n\ndfileroot is: %s\n\n", dfileroot);
  }

  /* sprintf(Datafilename,"%s%s.data",Outputdir,dfileroot); */
  sprintf(Datafilename, "%s%s.csv", Outputdir, dfileroot);
  sprintf(Imageindexname, "%simage_index.txt", Outputdir);

  sprintf(Moviename, "%s%s.mov", Outputdir, dfileroot);
  /* strcat(Moviename,strsuff); */

  sprintf(Parname, "%s%s.params", Outputdir, dfileroot);

  sprintf(Fileoname, "%s%s.img", Outputdir, dfileroot);
  strcat(Fileoname, strsuff);

  sprintf(Phrname, "%s%s.phr", Outputdir, dfileroot);
  strcat(Phrname, strsuff);

  /* Store parameters input in parameter file */

  return (0);
}

/***
 *    manage_deactivation_behavior
 *
 *     Determines which phases to deactivate, when to deactivate them,
 *     and when, if ever, to reactivate them.
 *
 *     Arguments:    none
 *     Returns:    nothing
 *
 *    Calls:        performdeactivation,performreactivation
 *    Called by:    main program
 ***/
void manage_deactivation_behavior(void) {
  register int i;
  int j;

  for (i = 0; i < Numdeact; i++) {
    j = Deactphaselist[i];
    if ((Deactfrac[j] > 0.0) && (Time_cur >= Deactinit[j]) &&
        Startflag[j] == 0) {

      Startflag[j] = 1;
      if (Verbose) {
        printf("\nDeactivating now at time %f...", Time_cur);
        printf(" phase %d\n", j);
        printf("\tFraction to deactivate is %f\n", Deactfrac[j]);
      }
      performdeactivation(j, Deactfrac[j]);
    }

    /***
     *    Decide if any reactivation is necessary
     ***/

    if ((Deactfrac[j] > 0.0) && (Time_cur >= Deactends[j]) &&
        (Time_cur <= Deactterm[j])) {

      if (Time_cur == Deactterm[j]) {
        Stopflag[j] = 1;
        if (Verbose) {
          printf("\nTerminating deactivation for phase %d \nat time %f\n", j,
                 Time_cur);
        }
      } else if (Verbose) {
        printf("\nPartially reactivating for phase %d \nat time %f\n", j,
               Time_cur);
      }

      performreactivation(j, Reactfrac[j], Stopflag[j]);

    } else if ((Deactfrac[j] > 0.0) && (Time_cur >= Deactterm[j]) &&
               Stopflag[j] == 0) {

      Stopflag[j] = 1;
      if (Verbose)
        printf("\nTerminating deactivation for phase %d \nat time %f\n", j,
               Time_cur);
    }
  }

  return;
}

/***
 *    performdeactivation
 *
 *     Deactivate a fraction (fracdeact) of the
 *     a given phase to prevent its hydrating
 *
 *     Arguments:    int phase id to deactivate
 *                 float fraction to deactivate
 *
 *     Returns:    nothing
 *
 *    Calls:        ran1
 *    Called by:    main program
 ***/
void performdeactivation(int pid, float fracdeact) {
  int kx, ky, kz, jx, jy, jz, faceid;
  float prdeact;

  /* Scan entire 3-D microstructure */

  jx = jy = jz = 0;
  for (kx = 0; kx < Xsyssize; kx++) {
    for (ky = 0; ky < Ysyssize; ky++) {
      for (kz = 0; kz < Zsyssize; kz++) {

        /***
         *    Choose which phases to deactivate
         ***/

        if (Mic[kx][ky][kz] == pid) {

          for (faceid = 0; faceid < 6; faceid++) {
            switch (faceid) {
            case 0:
              jx = kx + 1;
              if (jx > (Xsyssize - 1))
                jx = 0;
              jy = ky;
              jz = kz;
              break;
            case 1:
              jx = kx - 1;
              if (jx < 0)
                jx = Xsyssize - 1;
              jy = ky;
              jz = kz;
              break;
            case 2:
              jy = ky + 1;
              if (jy > (Ysyssize - 1))
                jy = 0;
              jx = kx;
              jz = kz;
              break;
            case 3:
              jy = ky - 1;
              if (jy < 0)
                jy = Ysyssize - 1;
              jx = kx;
              jz = kz;
              break;
            case 4:
              jz = ky + 1;
              if (jz > (Zsyssize - 1))
                jz = 0;
              jx = kx;
              jy = ky;
              break;
            case 5:
              jz = ky - 1;
              if (jz < 0)
                jz = Zsyssize - 1;
              jx = kx;
              jy = ky;
              break;
            default:
              break;
            }

            /***
             *    If the neighboring pixel is porosity,
             *    perhaps deactivate this pixel face
             ***/

            if (Mic[jx][jy][jz] == POROSITY || Mic[jx][jy][jz] == CRACKP) {

              prdeact = ran1(Seed);
              if (prdeact < fracdeact) {

                /***
                 *    Deactivation is by multiplying
                 *    by prime factor
                 ***/

                Deactivated[kx][ky][kz] *= Primevalues[faceid];
              }
            }
          }
        }

      } /* End of loop over Z */
    } /* End of loop over Y */
  } /* End of loop over X */
}

/***
 *    performreactivation
 *
 *     Reactivate a fraction (fracreact) of the
 *     a deactivated surface to allow its hydrating
 *
 *     Arguments:    int phase id to reactivate
 *                 float fraction to deactivate
 *                 int finalreact
 *
 *     Returns:    nothing
 *
 *    Calls:        ran1
 *    Called by:    main program
 ***/
void performreactivation(int pid, float fracreact, int finalreact) {
  int kx, ky, kz, faceid, cv;
  float prreact;

  /* Scan entire 3-D microstructure */

  for (kx = 0; kx < Xsyssize; kx++) {
    for (ky = 0; ky < Ysyssize; ky++) {
      for (kz = 0; kz < Zsyssize; kz++) {

        if (Mic[kx][ky][kz] == pid) {

          for (faceid = 0; faceid < 6; faceid++) {
            cv = Deactivated[kx][ky][kz] % Primevalues[faceid];
            if (!cv) {
              prreact = ran1(Seed);
              if ((prreact < fracreact) || (finalreact)) {

                /***
                 *    Reactivation is by dividing by
                 *    prime factor
                 ***/

                Deactivated[kx][ky][kz] /= Primevalues[faceid];
              }
            }

          } /* End of loop over faces of pixel */
        }

      } /* End of loop over Z */
    } /* End of loop over Y */
  } /* End of loop over X */
}

/***
 *    chckedge
 *
 *     Check if a pixel located at (xck,yck,zck) is on a
 *     surface with pore space in the 3D system
 *
 *     Arguments:    int phase to check
 *                 integer x,y, and z coordinates to check
 *
 *     Returns:    1 if on a surface, 0 otherwise
 *
 *    Calls:        no other routines
 *    Called by:    passone
 ***/
int chckedge(int phase, int xck, int yck, int zck) {
  int edgeback = 0;
  int x2, y2, z2;
  int ip;

  /***
   *    Check all neighboring pixels (6, 18, or 26)
   *    and use periodic boundary conditions
   *
   *    Change number of NEIGHBORS in header file
   *    called disrealnew.h
   ***/

  for (ip = 0; ((ip < NEIGHBORS) && (!edgeback)); ip++) {

    x2 = xck + Xoff[ip];
    y2 = yck + Yoff[ip];
    z2 = zck + Zoff[ip];

    x2 += checkbc(x2, Xsyssize);
    y2 += checkbc(y2, Ysyssize);
    z2 += checkbc(z2, Zsyssize);

    if (Mic[x2][y2][z2] == POROSITY || Mic[x2][y2][z2] == CRACKP ||
        Mic[x2][y2][z2] == CSH || Mic[x2][y2][z2] == POZZCSH ||
        Mic[x2][y2][z2] == SLAGCSH) {
      edgeback = 1;
    }
    /* JWB: Added this block as a trial to prevent adjacent
     * particles from blocking each other's dissolution
     */
    else if (Micpart[xck][yck][zck] != Micpart[x2][y2][z2]) {
      edgeback = 1;
    }
  }

  return (edgeback);
}

/***
 *    resetcrackpores
 *
 *     Scans over all pixels.  If a pixel of type POROSITY or CRACKP
 *     is found, then checks nearest neighbors to decide majority type
 *     of pore pixels surrounding a pixel at position xck,yck,zck
 *
 *     Arguments:    none
 *
 *     Returns:    nothing
 *
 *    Calls:        no other routines
 *    Called by:    main function
 ***/
void resetcrackpores(void) {
  int porecnt, crackcnt, curid;
  int x1, y1, z1, x2, y2, z2;
  int ip;

  /***
   *    Check all neighboring pixels (6, 18, or 26)
   *    and use periodic boundary conditions
   *
   *    Change number of NEIGHBORS in header file
   *    called disrealnew.h
   ***/

  for (x1 = 0; x1 < Zsyssize; x1++) {
    for (y1 = 0; y1 < Ysyssize; y1++) {
      for (z1 = 0; z1 < Zsyssize; z1++) {
        if (Mic[x1][y1][z1] == POROSITY || Mic[x1][y1][z1] == CRACKP) {

          curid = Mic[x1][y1][z1];
          porecnt = crackcnt = 0;
          for (ip = 0; ip < NEIGHBORS; ip++) {

            x2 = x1 + Xoff[ip];
            y2 = y1 + Yoff[ip];
            z2 = z1 + Zoff[ip];

            x2 += checkbc(x2, Xsyssize);
            y2 += checkbc(y2, Ysyssize);
            z2 += checkbc(z2, Zsyssize);

            if (Mic[x2][y2][z2] == POROSITY)
              porecnt++;
            if (Mic[x2][y2][z2] == CRACKP)
              crackcnt++;
          }

          if ((porecnt >= crackcnt) && curid == CRACKP) {
            Mic[x1][y1][z1] = POROSITY;
            Count[CRACKP]--;
            Count[POROSITY]++;
          } else if ((crackcnt < porecnt) && curid == POROSITY) {
            Mic[x1][y1][z1] = CRACKP;
            Count[CRACKP]++;
            Count[POROSITY]--;
          }
        }
      }
    }
  }

  return;
}

/***
 *    countphase
 *
 *       Scan microstructure and determine the number of voxels of a particular
 *phase
 *
 *     Arguments:    int phid (phase id to check)
 *
 *     Returns:    int number of voxels of that phase
 *
 *    Calls:        nothing
 *    Called by:    main
 ***/
int countphase(int phid) {
  register int xid, yid, zid;
  int cntphase = 0;

  /* Scan the entire 3-D microstructure */

  for (xid = 0; xid < Xsyssize; xid++) {
    for (yid = 0; yid < Ysyssize; yid++) {
      for (zid = 0; zid < Zsyssize; zid++) {

        if (Mic[xid][yid][zid] == phid)
          cntphase += 1;

      } /* end of xid */
    } /* end of yid */
  } /* end of zid */

  return (cntphase);
}

/***
 *    passone
 *
 *     First pass through microstructure during dissolution.
 *     Low and high indicate the phase ID range to check for
 *     surface sites.
 *
 *     Arguments:    int low, high (phase id range to check)
 *                 int cycid
 *                 int cshexflag (0 or 1 only)
 *
 *     Returns:    nothing
 *
 *    Calls:        chckedge
 *    Called by:    dissolve
 ***/
void passone(int low, int high, int cycid, int cshexflag) {
  int i, xid, yid, zid, phid, edgef, phread, cshcyc;

  /* Gypready used to determine if any soluble gypsum remains */

  if ((low <= GYPSUM) && (GYPSUM <= high)) {
    Gypready = 0;
  }

  /* Zero out count for the relevant phases */

  for (i = low; i <= high; i++) {
    Count[i] = 0;
  }

  /* Scan the entire 3-D microstructure */

  for (xid = 0; xid < Xsyssize; xid++) {
    for (yid = 0; yid < Ysyssize; yid++) {
      for (zid = 0; zid < Zsyssize; zid++) {

        phread = Mic[xid][yid][zid];

        /* Update heat data and water consumed for solid CSH */

        if ((cshexflag) && (phread == CSH)) {
          cshcyc = Cshage[xid][yid][zid];
          Heatsum += Heatf[CSH] / Molarvcsh[cshcyc];
          Molesh2o += Watercsh[cshcyc] / Molarvcsh[cshcyc];
        }

        /* Identify phase and update count */

        phid = NPHASES + 10; /* Clearly out of bounds */

        for (i = low; ((i <= high) && (phid == NPHASES + 10)); i++) {

          if (Mic[xid][yid][zid] == i) {

            phid = i;

            /* Update count for this phase */

            Count[i]++;

            if ((i == GYPSUM) || (i == GYPSUMS)) {
              Gypready++;
            }

            /* If first cycle, then accumulate initial counts */

            if ((cycid == 1) || ((cycid == 0) && (Ncyc == 0))) {

              /***
               *    Ordered in terms of likely volume
               *    fractions (largest to smallest) to
               *    speed execution
               ***/

              if (i == POROSITY) {
                Porinit++;
              } else if (i == C3S) {
                C3sinit++;
              } else if (i == C2S) {
                C2sinit++;
              } else if (i == C3A) {
                C3ainit++;
              } else if (i == OC3A) {
                Oc3ainit++;
              } else if (i == C4AF) {
                C4afinit++;
              } else if (i == K2SO4) {
                Ksulfinit++;
              } else if (i == NA2SO4) {
                Nasulfinit++;
              } else if (i == GYPSUM) {
                Ncsbar++;
              } else if (i == GYPSUMS) {
                Ncsbar++;
              } else if (i == ANHYDRITE) {
                Anhinit++;
              } else if (i == HEMIHYD) {
                Heminit++;
              } else if (i == SFUME || i == AMSIL) {
                Nsilica++;
              } else if (i == SLAG) {
                Slaginit++;
              } else if (i == FREELIME) {
                Freelimeinit++;
              } else if (i == ETTR) {
                Netbar++;
              } else if (i == ETTRC4AF) {
                Netbar++;
              } else if (i == CRACKP) {
                Crackpinit++;
              }
            }
          }
        }

        /***
         *    Currently do NOT identify
         *    SURFACE pixels of K2SO4 and NA2SO4
         ***/

        if (phid != NPHASES + 10 && Mic[xid][yid][zid] != K2SO4 &&
            Mic[xid][yid][zid] != NA2SO4) {

          /***
           *    If phase is soluble, see if it is
           *    in contact with porosity
           ***/

          if ((cycid != 0) && (Soluble[phid] == 1)) {
            edgef = chckedge(phid, xid, yid, zid);
            if (edgef == 1) {

              /***
               *    Surface eligible species has an
               *    ID that is OFFSET greater than its
               *    original value.  Means that it is
               *    ready for dissolution.
               ***/

              Mic[xid][yid][zid] += (int)(OFFSET);
            }
          }
        }

      } /* end of xid */
    } /* end of yid */
  } /* end of zid */
}

/***
 *    loccsh
 *
 *     Place a diffusing CSH species near dissolution source
 *     at (xcur,ycur,zcur)
 *
 *     Arguments:    int x,y, and z coordinates
 *                 int id of pore type used to create the diffusing species
 *                 (change added 24 May 2004)
 *
 *     Returns:    1 if species is placed, 0 otherwise
 *
 *    Calls:        no other routines
 *    Called by:    dissolve
 ***/
int loccsh(int xcur, int ycur, int zcur, int sourcepore) {
  int effort, tries, xmod, ymod, zmod;
  int maxtries = 500;
  int halfbox;
  struct Ants *antnew;

  /* effort indicates if appropriate location found */
  effort = 0;

  tries = 0;

  /* Execute up to maxtries tries in immediate vicinity */

  halfbox = Distloccsh / 2;
  while ((!effort) && (tries < maxtries)) {

    tries++;
    xmod = (-halfbox) + (int)(Distloccsh * ran1(Seed));
    ymod = (-halfbox) + (int)(Distloccsh * ran1(Seed));
    zmod = (-halfbox) + (int)(Distloccsh * ran1(Seed));
    if (xmod > halfbox)
      xmod = halfbox;
    if (ymod > halfbox)
      ymod = halfbox;
    if (zmod > halfbox)
      zmod = halfbox;

    xmod += xcur;
    ymod += ycur;
    zmod += zcur;

    /* Periodic boundary conditions */

    xmod += checkbc(xmod, Xsyssize);
    ymod += checkbc(ymod, Ysyssize);
    zmod += checkbc(zmod, Zsyssize);

    if (Mic[xmod][ymod][zmod] == sourcepore) {
      effort = 1;
      Mic[xmod][ymod][zmod] = DIFFCSH;
      Nmade++;
      Ngoing++;

      /***
       *    Add this diffusing CSH species
       *    to the linked list.  May want to look at
       *    allocating space for new ants in chunks of,
       *    say, 50, rather than one at a time.
       ***/

      antnew = (struct Ants *)malloc(Antsize);
      antnew->x = xmod;
      antnew->y = ymod;
      antnew->z = zmod;
      antnew->id = DIFFCSH;
      antnew->cycbirth = Cyccnt;

      /***
       *    Now connect this ant structure to
       *    end of linked list
       ***/

      antnew->prevant = Tailant;
      Tailant->nextant = antnew;
      antnew->nextant = NULL;
      Tailant = antnew;
    }
  }

  return (effort);
}

/***
 *    countbox
 *
 *     Count the number of pore pixels within a cube of
 *     size boxsize, centered at (qx,qy,qz)
 *
 *     Arguments:    int boxsize
 *                 int x,y, and z coordinates of box center
 *
 *     Returns:    int number of pore pixels found within box
 *
 *    Calls:        no other routines
 *    Called by:    makeinert
 ***/
int countbox(int boxsize, int qx, int qy, int qz) {
  int nfound, ix, iy, iz, qxlo, qxhi, qylo, qyhi, qzlo, qzhi;
  int hx, hy, hz, boxhalf;

  boxhalf = boxsize / 2;
  nfound = 0;
  qxlo = qx - boxhalf;
  qxhi = qx + boxhalf;
  qylo = qy - boxhalf;
  qyhi = qy + boxhalf;
  qzlo = qz - boxhalf;
  qzhi = qz + boxhalf;

  /***
   *    Count the number of requisite pixels in the
   *    3-D cube box using periodic boundaries
   ***/

  for (ix = qxlo; ix <= qxhi; ix++) {
    hx = ix;
    hx += checkbc(hx, Xsyssize);

    for (iy = qylo; iy <= qyhi; iy++) {
      hy = iy;
      hy += checkbc(hy, Ysyssize);

      for (iz = qzlo; iz <= qzhi; iz++) {
        hz = iz;
        hz += checkbc(hz, Zsyssize);

        /***
         *    Count if porosity, diffusing species,
         *    or empty porosity
         ***/

        if ((Mic[hx][hy][hz] == POROSITY) || (Mic[hx][hy][hz] > NSPHASES)) {

          nfound++;
        }

      } /* End of loop over z */
    } /* End of loop over y */
  } /* End of loop over x */

  return (nfound);
}

/***
 *    makeinert
 *
 *    Create ndesire pixels of empty pore space to simulate
 *    self-desiccation
 *
 *     Arguments:    int ndesire (number to create)
 *
 *     Returns:    nothing
 *
 *    Calls:        countbox
 *    Called by:    dissolve
 ***/
void makeinert(int ndesire) {
  int idesire;
  int px, py, pz, placed, cntpore, cntmax;
  struct Togo *headtogo, *tailtogo, *newtogo, *lasttogo, *onetogo;

  /***
   *    First allocate and initialize the first member
   *    of the linked list
   ***/

  headtogo = (struct Togo *)malloc(Togosize);
  headtogo->x = headtogo->y = headtogo->z = (-1);
  headtogo->npore = 0;
  headtogo->nexttogo = NULL;
  headtogo->prevtogo = NULL;
  tailtogo = headtogo;
  cntmax = 0;

  /***
   *    Add needed number of elements to the end of the list
   *    Consider allocating the space in chunks of, say, 50,
   *    instead of one at a time to speed up execution
   ***/

  for (idesire = 2; idesire <= ndesire; idesire++) {
    newtogo = (struct Togo *)malloc(Togosize);
    newtogo->npore = 0;
    newtogo->x = newtogo->y = newtogo->z = (-1);
    tailtogo->nexttogo = newtogo;
    newtogo->prevtogo = tailtogo;
    tailtogo = newtogo;
  }

  /* Now scan the microstructure and RANK the sites */

  for (pz = 0; pz < Zsyssize; pz++) {
    for (py = 0; py < Ysyssize; py++) {
      for (px = 0; px < Xsyssize; px++) {

        if (Mic[px][py][pz] == POROSITY) {
          cntpore = countbox(Cubesize, px, py, pz);

          if (cntpore > cntmax)
            cntmax = cntpore;

          /***
           *    Store this site value at appropriate place in
           *    sorted linked list
           ***/

          if (cntpore > (tailtogo->npore)) {
            placed = 0;
            lasttogo = tailtogo;
            while (!placed) {
              newtogo = lasttogo->prevtogo;
              if (!newtogo) {
                placed = 2;
              } else if (cntpore <= (newtogo->npore)) {
                placed = 1;
              }

              if (!placed)
                lasttogo = newtogo;
            }

            onetogo = (struct Togo *)malloc(Togosize);
            onetogo->x = px;
            onetogo->y = py;
            onetogo->z = pz;
            onetogo->npore = cntpore;

            /* Insertion at the head of the list */

            if (placed == 2) {
              onetogo->prevtogo = NULL;
              onetogo->nexttogo = headtogo;
              headtogo->prevtogo = onetogo;
              headtogo = onetogo;
            }

            if (placed == 1) {
              onetogo->nexttogo = lasttogo;
              onetogo->prevtogo = newtogo;
              lasttogo->prevtogo = onetogo;
              newtogo->nexttogo = onetogo;
            }

            /* Eliminate the last element */

            lasttogo = tailtogo;
            tailtogo = tailtogo->prevtogo;
            tailtogo->nexttogo = NULL;
            free(lasttogo);
          }
        }

      } /* End of loop in z */
    } /* End of loop in y */
  } /* End of loop in x */

  /***
   *    Now remove the sites starting at the
   *    head of the list and free all of the
   *    used memory
   ***/

  for (idesire = 1; idesire <= ndesire; idesire++) {
    px = headtogo->x;
    py = headtogo->y;
    pz = headtogo->z;

    if (px != (-1)) {
      Mic[px][py][pz] = EMPTYP;
      Count[POROSITY]--;
      Count[EMPTYP]++;
    }

    lasttogo = headtogo;
    headtogo = headtogo->nexttogo;
    free(lasttogo);
  }

  /***
   *    If only small cubes of porosity were found,
   *    then adjust Cubesize to have a more efficient
   *    search in the future
   ***/

  if (Cubesize > CUBEMIN) {
    if ((2 * cntmax) < (Cubesize * Cubesize * Cubesize)) {
      Cubesize -= 2;
    }
  }
}

/***
 *    extslagcsh
 *
 *     Add extra SLAGCSH when SLAG reacts at position
 *     (xpres,ypres,zpres)
 *
 *     Arguments:    int x,y, and z coordinates
 *
 *     Returns:    nothing
 *
 *    Calls:        moveone, edgecnt
 *    Called by:    dissolve
 ***/
void extslagcsh(int xpres, int ypres, int zpres) {
  int check, sump, xchr, ychr, zchr, fchr, i1, action, numnear;
  int maxtries = 100;
  int maxxtries = 5000;
  int tries;

  /***
   *    First try 6 neighboring locations until
   *        a) successful,
   *        b) all 6 sites are tried, or
   *        c) 100 tries are made
   ***/

  fchr = 0;
  sump = 1;

  for (i1 = 1; ((i1 <= maxtries) && (!fchr) && (sump != 30030)); i1++) {

    /***
     *    Determine location of neighbor
     *    (using periodic boundaries)
     ***/

    xchr = xpres;
    ychr = ypres;
    zchr = zpres;
    action = 0;

    sump *= moveone(&xchr, &ychr, &zchr, &action, sump);
    if (!action && (Verbose == 1))
      printf("Error in value of action in extpozz \n");

    check = Mic[xchr][ychr][zchr];

    /* If neighbor is porosity, locate the SLAG CSH there */

    if (check == POROSITY || check == CRACKP) {
      Mic[xchr][ychr][zchr] = SLAGCSH;
      Count[SLAGCSH]++;
      if (check == POROSITY)
        Count[POROSITY]--;
      if (check == CRACKP)
        Count[CRACKP]--;
      fchr = 1;
    }
  }

  /***
   *    If no neighbor available, locate SLAGCSH
   *    at random location in pore space
   ***/

  tries = 0;
  while (!fchr) {

    tries++;

    /***
     *    Generate a random location in the 3-D system
     ***/

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
     *    extra SLAGCSH there
     ***/

    if (check == POROSITY) {
      numnear = edgecnt(xchr, ychr, zchr, SLAG, CSH, SLAGCSH);

      /***
       *    Be sure that one neighboring species is CSH or
       *    SLAG material (anywhere within a 3x3x3 cube)
       *    If more than maxxtries tries have already been made
       *    then locate it at this pore pixel no matter what
       ***/

      if ((tries > maxxtries) || (numnear < NEIGHBORS)) {
        Mic[xchr][ychr][zchr] = SLAGCSH;
        Count[SLAGCSH]++;
        Count[POROSITY]--;
        fchr = 1;
      }
    }
  }
}

/***
 *    dissolve
 *
 *     Implement one cycle of dissolution
 *
 *     Arguments:    int cycle number
 *
 *     Returns:    nothing
 *
 *    Calls:        passone, loccsch, makeinert
 *    Called by:    main program
 ***/
void dissolve(int cycle) {
  int gct = 0;
  int nc3aext, ncshext, nchext, ngypext, nanhext;
  int nsum5, nsum4, nsum3, nsum2, nhemext, nsum6, nsum7, nsum8, nc4aext,
      nso4ext, vcement;
  int nkspix, nnaspix, totks, totnas, skipnodes;
  int pixdeact, phid, phnew, plnew, cread;
  int i, k, x, y, xl, yl, zl, curx, cury, curz, xc, yc, plok;
  int zc, cycnew, sollime, sourcepore;
  int placed, cshrand, maxsulfate, maxallowed;
  int ctest, ncshgo, nsurf, suminit;
  int xext, nhgd, npchext, nslagc3a = 0;
  float na2omintotmass, k2omintotmass, mwna2so4, mwna2o, mwk2so4, mwk2o;
  float plfh3, savechgone, sulfavemolarv, mk2so4, mna2so4;
  float dfact, dfact1, molesdh2o, h2oinit, heat4, fhemext, fc4aext;
  double factCSH, factPOZZCSH, factTfract;
  double Pozzcshscale = 20000.0;
  float pconvert, pc3scsh, pc2scsh, calcx, calcy, calcz, tdisfact;
  float frafm, frettr, frhyg, frtot, mc3ar, mc4ar, p3init, fact, satsquared;
  float resfact, molwh2o, volpix, ohadj;
  double massdiff, mass105, mass1000, fchext, fc3aext, fanhext;
  double mass_now, tot_mass, mass_fa_now, vol_fa_now, pdis, psfact;
  double other_solid_volume_per_gcem;
  double empty_volume_per_gcem;
  double water_volume_per_gcem;
  double cement_volume_per_gcem;
  float refporefrac, xv1, yv1, yv3;
  struct Ants *antadd;
  struct Alksulf *curas;
  FILE *fpout01;

  resfact = pow((1.0 / Res), 1.25);

  /***
   *    volpix is the volume of one pixel, in cm^3
   *
   *    molwh2o is the molecular mass of water, in g/mole
   ***/

  volpix = pow(Res * 0.00010, 3.0);
  molwh2o = 18.0;

  /* Initialize variables */

  Nmade = 0;

  /***
   *    Counter for number of CSH diffusing species to
   *    be located at random locations in microstructure
   ***/

  npchext = ncshgo = cshrand = 0;

  /*    New and old values for heat released */

  Heat_old = Heat_new;

  /* Initialize dissolution and phase counters */

  nsurf = 0;
  for (i = 0; i < NPHASES; i++) {
    Discount[i] = 0;
    Count[i] = 0;
  }

  /* PASS ONE: identify all edge points which are soluble */

  /***
   *    Molesh2o is the number of MOLES of water consumed by all hydration
   *        reactions over all cycles. It is set to zero at the
   *        beginning of each dissolve cycle and
   *        recalculated by counting the current number of voxels of
   *        each hydration product and multiplying by number of moles
   *        of water per voxel of that hydration product, which is
   *        Waterc[i] / Molarv[i].
   *
   *        Note Waterc[i] is the number of moles of water consumed per
   *        mole of the product created, Molarv[i] is the volume per
   *        mole of the the product, so Waterc[i] / Molarv[i] is the
   *        moles of water consumed per unit volume of the product created.
   ***/

  Soluble[C3AH6] = 0;
  Heatsum = Molesh2o = 0.0;

  /***
   *    Function passone determines initial number of each phase
   *    if cycle = 1, otherwise just determines if a pixel is
   *    eligible for dissolution.  Every eligible pixel will
   *    have its phaseid value increased by OFFSET after passone
   *    has finished
   ***/

  passone(POROSITY, NPHASES - 1, cycle, 1);
  sollime = 0;

  for (zl = 0; zl < Zsyssize; zl++) {
    for (yl = 0; yl < Ysyssize; yl++) {
      for (xl = 0; xl < Xsyssize; xl++) {
        if (Mic[xl][yl][zl] == (FREELIME + OFFSET)) {
          sollime++;
        }
      }
    }
  }

  Sulf_solid = Count[GYPSUM];
  Sulf_solid += Count[GYPSUMS];
  Sulf_solid += Count[HEMIHYD];
  Sulf_solid += Count[ANHYDRITE];
  Sulf_solid += Count[K2SO4];
  Sulf_solid += Count[NA2SO4];

  /***
   *    If first cycle, then determine all mixture
   *    proportions based on user input and original
   *    microstructure
   ***/

  if (cycle == 1) {

    /* Mass of cement in system */

    Cemmass = Specgrav[C3S] * (float)Count[C3S];
    Cemmass += Specgrav[C2S] * (float)Count[C2S];
    Cemmass += Specgrav[C3A] * (float)Count[C3A];
    Cemmass += Specgrav[OC3A] * (float)Count[OC3A];
    Cemmass += Specgrav[C4AF] * (float)Count[C4AF];
    /* Cemmass += Specgrav[K2SO4] * (float)Count[K2SO4]; */
    /* Cemmass += Specgrav[NA2SO4] * (float)Count[NA2SO4]; */

    Cemmasswgyp = Cemmass + (Specgrav[GYPSUM] * (float)Count[GYPSUM]) +
                  (Specgrav[ANHYDRITE] * (float)Count[ANHYDRITE]) +
                  (Specgrav[HEMIHYD] * (float)Count[HEMIHYD]);

    Totfract = (float)(Count[C3S] + Count[C2S] + Count[C3A] + Count[OC3A]);
    Totfract += (float)(Count[C4AF] + Count[GYPSUM] + Count[HEMIHYD] +
                        Count[ANHYDRITE]);

    Totfract /= (float)(Syspix);

    /***
     *    Check that Totsodium and Totpotassium are
     *    not less than necessary to be consistent
     *    with the counts of NA2SO4 and K2SO4
     ***/

    mna2so4 = Specgrav[NA2SO4] * (float)Count[NA2SO4];
    mk2so4 = Specgrav[K2SO4] * (float)Count[K2SO4];

    /* Molecular weights of the alkali compounds involved */
    mwna2so4 = 142.04;
    mwna2o = 61.98;
    mwk2so4 = 174.26;
    mwk2o = 94.2;

    /* Minimum total mass of sodium oxide per gram of cement */
    na2omintotmass = (mna2so4 * (mwna2o / mwna2so4)) / Cemmasswgyp;

    /* Minimum total mass of potassium oxide per gram of cement */
    k2omintotmass = (mk2so4 * (mwk2o / mwk2so4)) / Cemmasswgyp;

    if (Totsodium < na2omintotmass) {
      /*
      printf("\nWARNING:  Prescribed total mass of Na2O ");
      printf("\n\tin alkali characteristics file is less ");
      printf("\n\tthan is consistent with the mass of ");
      printf("\n\tNA2SO4 in the microstructure.");
      printf("\n\n\tResetting Totsodium variable to be ")'
      printf("\n\tconsistent... Totsodium is now \n");
      Totsodium = na2omintotmass;
      printf("%f \n",Totsodium);
      */
    }

    if (Totpotassium < k2omintotmass) {
      /*
      printf("\nWARNING:  Prescribed total mass of K2O ");
      printf("\n\tin alkali characteristics file is less ");
      printf("\n\tthan is consistent with the mass of ");
      printf("\n\tK2SO4 in the microstructure.");
      printf("\n\n\tResetting Totpotassium variable to be ")'
      printf("\n\tconsistent... Totpotassium is now \n");
      Totpotassium = k2omintotmass;
      printf("%f \n",Totpotassium);
      */
    }

    /***
     *    All NA2SO4 and K2SO4 are considered readily soluble, so
     *    we check that Rssodium and Rspotassium are consistent
     *    with the counts of these alkali salts
     ***/

    if (Rssodium < na2omintotmass) {
      /*
      printf("\nWARNING:  Prescribed mass of readily soluble Na2O ");
      printf("\n\tin alkali characteristics file is less ");
      printf("\n\tthan is consistent with the mass of ");
      printf("\n\tNA2SO4 in the microstructure.");
      printf("\n\n\tResetting Rssodium variable to be ")'
      printf("\n\tconsistent... Rssodium is now \n");
      Rssodium = na2omintotmass;
      printf("%f \n",Rssodium);
      */
    }

    if (Rspotassium < k2omintotmass) {
      /*
      printf("\nWARNING:  Prescribed mass of readily soluble K2O ");
      printf("\n\tin alkali characteristics file is less ");
      printf("\n\tthan is consistent with the mass of ");
      printf("\n\tK2SO4 in the microstructure.");
      printf("\n\n\tResetting Rspotassium variable to be ")'
      printf("\n\tconsistent... Rspotassium is now \n");
      Rspotassium = k2omintotmass;
      printf("%f \n",Rspotassium);
      */
    }

    Flyashmass = Specgrav[SFUME] * (float)Count[SFUME];
    Flyashmass += Specgrav[AMSIL] * (float)Count[AMSIL];
    Flyashmass += Specgrav[ASG] * (float)Count[ASG];
    Flyashmass += Specgrav[CAS2] * (float)Count[CAS2];
    Flyashvol = (float)Count[SFUME];
    Flyashvol += (float)Count[AMSIL];
    Flyashvol += (float)Count[ASG];
    Flyashvol += (float)Count[CAS2];

    vcement = Count[C3S] + Count[C2S] + Count[C3A] + Count[OC3A] + Count[C4AF] +
              Count[GYPSUM] + Count[HEMIHYD] + Count[ANHYDRITE];

    Meancemdens = Cemmasswgyp / ((float)vcement);
    cement_volume_per_gcem = 1.0 / Meancemdens;

    CH_mass = Specgrav[CH] * (float)Count[CH];

    /* Total mass in system neglecting single aggregate */

    tot_mass = Cemmass + CH_mass + (float)Count[POROSITY] +
               (Specgrav[INERT] * (float)Count[INERT]) +
               (Specgrav[CACL2] * (float)Count[CACL2]) +
               (Specgrav[ASG] * (float)Count[ASG]) +
               (Specgrav[SLAG] * (float)Count[SLAG]) +
               (Specgrav[HEMIHYD] * (float)Count[HEMIHYD]) +
               (Specgrav[ANHYDRITE] * (float)Count[ANHYDRITE]) +
               (Specgrav[CAS2] * (float)Count[CAS2]) +
               (Specgrav[CSH] * (float)Count[CSH]) +
               (Specgrav[GYPSUM] * (float)Count[GYPSUM]) +
               (Specgrav[GYPSUMS] * (float)Count[GYPSUMS]) +
               (Specgrav[SFUME] * (float)Count[SFUME]) +
               (Specgrav[AMSIL] * (float)Count[AMSIL]) +
               (Specgrav[FREELIME] * (float)Count[FREELIME]) +
               (Specgrav[CACO3] * (float)Count[CACO3]);

    /***
     *    Calculation of total solid mass, in g,
     *    at 105C and 1000C
     ***/

    Mass_105 = Mass_1000 = massdiff = 0.0;

    for (i = POROSITY; i <= NSPHASES; i++) {

      /***
       *     Explicit decision NOT to include water in a saturated crack
       *     pore in the nonevaporable water calculations.
       ***/

      Mass_105 +=
          ((double)Count[i] *
           (Specgrav[i] - (molwh2o * (Nh2o[i][0] - Nh2o[i][1]) / Molarv[i])));

      massdiff += ((double)(Count[i]) * Nh2o[i][1] / Molarv[i]);
    }

    Mass_105 *= ((double)volpix);
    massdiff *= ((double)(volpix * molwh2o));

    Mass_1000 = Mass_105 - massdiff;

    /***
     *    Water-to-cement ratio.  Decision to NOT include cracked pore water
     *    in the accounting for w/c.  Could amend this later if desired
     ***/

    if (Cemmass != 0.0) {
      W_to_c = (float)(((double)Count[POROSITY]) / Cemmasswgyp);
    } else {
      W_to_c = 0.0;
    }

    if ((tot_mass - (float)(Count[POROSITY])) != 0.0) {
      W_to_s = (float)(((double)Count[POROSITY]) /
                       (tot_mass - (float)(Count[POROSITY])));
    } else {
      W_to_s = 0.0;
    }

    /* Adjust masses for presence of aggregates in concrete */

    Mass_water = ((1.0 - Mass_agg) * (float)Count[POROSITY]) / tot_mass;
    Mass_CH = ((1.0 - Mass_agg) * CH_mass) / tot_mass;

    /* Pozzolan-to-cement ratio */
    if (Cemmass != 0.0) {
      S_to_c = (float)(((double)Count[INERT] * Specgrav[INERT] +
                        (double)Count[CACL2] * Specgrav[CACL2] +
                        (double)Count[ASG] * Specgrav[ASG] +
                        (double)Count[CAS2] * Specgrav[CAS2] +
                        (double)Count[SLAG] * Specgrav[SLAG] +
                        (double)Count[AMSIL] * Specgrav[AMSIL] +
                        (double)Count[SFUME] * Specgrav[SFUME]) /
                       Cemmass);
    } else {
      S_to_c = 0.0;
    }

    /* Convert to kJ/kg for heat produced */

    water_volume_per_gcem = W_to_c;
    if (Cemmass != 0.0) {
      empty_volume_per_gcem =
          (double)((Count[EMPTYP] + Count[CRACKP]) / Cemmass);
      other_solid_volume_per_gcem =
          (double)((double)(Count[INERT] + Count[INERTAGG] + Count[SLAG] +
                            Count[AMSIL] + Count[SFUME] + Count[CACL2] +
                            Count[ASG] + Count[CAS2]) /
                   Cemmass);
    } else {
      empty_volume_per_gcem = 0.0;
      other_solid_volume_per_gcem = 0.0;
    }

    if (W_to_c > 0.01) {

      /***
       *    Heat conversion factor converts the model heat
       *    units to kJ per kg of CEMENT (not including other solids).
       *
       *    Model units of heat are (kJ/system volume)
       *
       *       J                kJ       cm3 sys
       *    ------- = 1000 * -------     -------
       *     g cem             cm3 sys    g cem
       *
       *
       * where
       *
       *      cm^3 sys    cm^3 cem     cm3 H2O   cm3 other solid
       *     ---------- = --------- + -------- + ----------------
       *      g cem       g cem        g cem       g cem
       *
       *                + cm3 Empty
       *                  ---------
       *                   g cem
       *
       *                = (cement_volume_per_gcem
       *                   + water_volume_per_gcem
       *                   + other_solid_volume_per_gcem
       *                   + empty_volume_per_gcem)
       *
       ***/

      Heat_cf = (double)((1000.0 / ((double)Syspix)) *
                         (cement_volume_per_gcem + water_volume_per_gcem +
                          other_solid_volume_per_gcem + empty_volume_per_gcem));

    } else {

      /***
       *    With w/c < 0.01, we use volume per 1 gram
       *    of SILICA FUME. Otherwise, the conversion
       *    is the same as in the previous comment
       ***/

      Heat_cf = (double)((1000.0 / ((double)Syspix)) *
                         ((1.0 / Specgrav[SFUME]) +
                          (double)(Count[POROSITY] + Count[CH] + Count[INERT]) /
                              (Specgrav[SFUME] * (double)Count[SFUME])));
    }

    Mass_fill_pozz =
        (1.0 - Mass_agg) * ((double)Count[SFUME] * Specgrav[SFUME]) / tot_mass;

    Mass_fill = (1.0 - Mass_agg) *
                ((double)Count[INERT] * Specgrav[INERT] +
                 (double)Count[ASG] * Specgrav[ASG] +
                 (double)Count[SLAG] * Specgrav[SLAG] +
                 (double)Count[CAS2] * Specgrav[CAS2] +
                 (double)Count[CACO3] * Specgrav[CACO3] +
                 (double)Count[SFUME] * Specgrav[SFUME] +
                 (double)Count[AMSIL] * Specgrav[AMSIL] +
                 (double)Count[CACL2] * Specgrav[CACL2]) /
                tot_mass;

    if (Verbose) {
      printf("Calculated w/c is %.4f\n", W_to_c);
      printf("Calculated s/c is %.4f \n", S_to_c);
      printf("Calculated heat conversion factor is %f \n", Heat_cf);
      printf("Calculated mass fractions of water and filler ");
      printf("are %.4f  and %.4f \n", Mass_water, Mass_fill);
    }
  }

  cement_volume_per_gcem = 1.0 / Meancemdens;
  molesdh2o = 0.0;

  /* Alpha is the degree of hydration */

  Alpha = 0.0;

  /***
   *    heat4 contains measured heat release for
   *    C4AF hydration, based on
   *    Fukuhara et al., Cem. and Conc. Res. article
   ***/

  heat4 = 0.0;

  /* Total cement mass corrected for hydration */
  mass_now = mass_fa_now = 0.0;

  /* Initial combined counts of cement phases */
  suminit = C3sinit + C2sinit + C3ainit + C4afinit;
  suminit += (Ksulfinit + Nasulfinit);

  /***
   *    ctest is number of diffusing gypsum pixels that
   *    are likely to form ettringite.
   *
   *    1 unit of C3A can react with 2.5 units of Gypsum
   ***/

  ctest = Count[DIFFGYP];
  fflush(stdout);

  if ((float)ctest > (2.5 * (double)(Count[DIFFC3A] + Count[DIFFC4A]))) {
    ctest = 2.5 * (double)(Count[DIFFC3A] + Count[DIFFC4A]);
  }

  mass105 = mass1000 = massdiff = 0.0;

  for (i = 0; i < NPHASES; i++) {

    /***
     *    Calculate contribution to non-evaporable water of
     *    the solid phases
     ***/

    if ((i <= NSPHASES && (i != CSH)) || i == CRACKP) {

      mass105 +=
          ((double)Count[i] *
           (Specgrav[i] - (molwh2o * (Nh2o[i][0] - Nh2o[i][1]) / Molarv[i])));

      massdiff += ((double)(Count[i]) * Nh2o[i][1] / Molarv[i]);

    } else if (i == CSH) {

      /***
       *    Assume that CSH loses 40% of its water at 105
       *    (see H.F.W. Taylor, Mater. Res. Soc. Proc.,
       *    Vol. 85, p. 47 (1987))
       ***/

      mass105 += ((double)Count[i] *
                  (Specgrav[CSH] -
                   (molwh2o * 0.4 * Watercsh[cycle] / Molarvcsh[cycle])));

      massdiff += ((double)(Count[i]) * (1.0 - 0.4) * Watercsh[cycle] /
                   Molarvcsh[cycle]);
    }

    if ((i != POROSITY) && (i != CRACKP) && (i <= NSPHASES) &&
        (i != INERTAGG) && (i != CSH) && (i != FAC3A) && (i != FLYASH)) {

      Heatsum += ((double)Count[i] * Heatf[i] / Molarv[i]);

      /***
       *    Tabulate moles of H2O consumed by
       *    reactions so far
       ***/

      /***
       *   Molesh2o is the MOLES of water consumed by
       *   hydration reactions
       ***/
      Molesh2o += ((double)Count[i] * Waterc[i] / Molarv[i]);
    }

    /* ASSUME that all C3A which can, does form ettringite */

    if (i == DIFFC3A) {

      Heatsum += (((double)Count[DIFFC3A] - ((float)ctest / 2.5)) * Heatf[C3A] /
                  Molarv[C3A]);
    }

    /* ASSUME that all C4AF which can, does form ettringite */

    if (i == DIFFC4A) {
      Heatsum += (((double)Count[DIFFC4A] - ((float)ctest / 2.5)) *
                  Heatf[C4AF] / Molarv[C4AF]);
    }

    /***
     *    ASSUME all gypsum which can, does form ettringite.
     *    The remainder will remain as gypsum
     ***/

    if (i == DIFFGYP) {

      Heatsum +=
          ((double)(Count[DIFFGYP] - ctest) * Heatf[GYPSUM] / Molarv[GYPSUM]);

      /***
       *    3.3 is the molar expansion from GYPSUM to ETTR
       ***/

      Heatsum += ((float)ctest * 3.30 * Heatf[ETTR] / Molarv[ETTR]);
      molesdh2o += ((float)ctest * 3.30 * Waterc[ETTR] / Molarv[ETTR]);

    } else if (i == DIFFCH) {

      Heatsum += ((double)Count[DIFFCH] * Heatf[CH] / Molarv[CH]);
      molesdh2o += ((double)Count[DIFFCH] * Waterc[CH] / Molarv[CH]);

    } else if (i == DIFFFH3) {

      Heatsum += ((double)Count[DIFFFH3] * Heatf[FH3] / Molarv[FH3]);
      molesdh2o += ((double)Count[DIFFFH3] * Waterc[FH3] / Molarv[FH3]);

    } else if (i == DIFFCSH) {

      /***
       *    Use current CSH properties,
       *    i.e. Molarvcsh[cycle]  and Watercsh[cycle]
       ***/

      Heatsum += ((double)Count[DIFFCSH] * Heatf[CSH] / Molarvcsh[cycle]);
      molesdh2o +=
          ((double)Count[DIFFCSH] * Watercsh[cycle] / Molarvcsh[cycle]);

    } else if (i == DIFFETTR) {

      Heatsum += ((double)Count[DIFFETTR] * Heatf[ETTR] / Molarv[ETTR]);
      molesdh2o += ((double)Count[DIFFETTR] * Waterc[ETTR] / Molarv[ETTR]);

    } else if (i == DIFFCACL2) {

      Heatsum += ((double)Count[DIFFCACL2] * Heatf[CACL2] / Molarv[CACL2]);
      molesdh2o += ((double)Count[DIFFCACL2] * Waterc[CACL2] / Molarv[CACL2]);

    } else if (i == DIFFAS) {

      Heatsum += ((double)Count[DIFFAS] * Heatf[ASG] / Molarv[ASG]);
      molesdh2o += ((double)Count[DIFFAS] * Waterc[ASG] / Molarv[ASG]);

    } else if (i == DIFFCAS2) {

      Heatsum += ((double)Count[DIFFCAS2] * Heatf[CAS2] / Molarv[CAS2]);
      molesdh2o += ((double)Count[DIFFCAS2] * Waterc[CAS2] / Molarv[CAS2]);

    } else if (i == DIFFANH) {

      /***
       *    ASSUME that all diffusing anhydrite leads
       *    to gypsum formation
       ***/

      Heatsum += ((double)Count[DIFFANH] * Heatf[GYPSUMS] / Molarv[GYPSUMS]);

      /* 2 moles of water per mole of gypsum formed */

      molesdh2o += ((double)Count[DIFFANH] * 2.0 / Molarv[GYPSUMS]);

    } else if (i == DIFFHEM) {

      /***
       *    ASSUME that all diffusing hemihydrate leads
       *    to gypsum formation
       ***/

      Heatsum += ((double)Count[DIFFHEM] * Heatf[GYPSUMS] / Molarv[GYPSUMS]);

      /* 1.5 moles of water per mole of gypsum formed */

      molesdh2o += ((double)Count[DIFFHEM] * 1.5 / Molarv[GYPSUMS]);

    } else if (i == C3S) {

      Alpha += ((double)(C3sinit - Count[C3S]));
      mass_now += (Specgrav[C3S] * (double)Count[C3S]);
      heat4 += (0.517 * (double)(C3sinit - Count[C3S]) * Specgrav[C3S]);

    } else if (i == C2S) {

      Alpha += ((double)(C2sinit - Count[C2S]));
      mass_now += (Specgrav[C2S] * (double)Count[C2S]);
      heat4 += (0.262 * (double)(C2sinit - Count[C2S]) * Specgrav[C2S]);

    } else if (i == C3A) {

      Alpha += ((double)(C3ainit - Count[C3A]));
      mass_now += (Specgrav[C3A] * (double)Count[C3A]);
      mc3ar = ((double)(C3ainit - Count[C3A]) / Molarv[C3A]);
      mc4ar = ((double)(C4afinit - Count[C4AF]) / Molarv[C4AF]);

      if ((mc3ar + mc4ar) > 0.0) {
        frhyg =
            (mc3ar / (mc3ar + mc4ar)) * (double)Count[C3AH6] / Molarv[C3AH6];
      } else {
        frhyg = 0.0;
      }

      frettr = (double)Count[ETTR] / Molarv[ETTR];
      frafm = 3.0 * (double)Count[AFM] / Molarv[AFM];
      frtot = frafm + frettr + frhyg;

      if (frtot > 0.0) {
        frettr /= frtot;
        frafm /= frtot;
        frhyg /= frtot;
        heat4 +=
            (frafm * 1.144 * (double)(C3ainit - Count[C3A]) * Specgrav[C3A]);
        heat4 +=
            (frhyg * 0.908 * (double)(C3ainit - Count[C3A]) * Specgrav[C3A]);
        heat4 +=
            (frettr * 1.672 * (double)(C3ainit - Count[C3A]) * Specgrav[C3A]);
      }

    } else if (i == OC3A) {

      Alpha += ((double)(Oc3ainit - Count[OC3A]));
      mass_now += (Specgrav[OC3A] * (double)Count[OC3A]);
      mc3ar = (double)(Oc3ainit - Count[OC3A]) / Molarv[OC3A];
      mc4ar = (double)(C4afinit - Count[C4AF]) / Molarv[C4AF];

      if ((mc3ar + mc4ar) > 0.0) {
        frhyg =
            (mc3ar / (mc3ar + mc4ar)) * (double)Count[C3AH6] / Molarv[C3AH6];
      } else {
        frhyg = 0.0;
      }

      frettr = (double)Count[ETTR] / Molarv[ETTR];
      frafm = 3.0 * (double)Count[AFM] / Molarv[AFM];
      frtot = frafm + frettr + frhyg;

      if (frtot > 0.0) {
        frettr /= frtot;
        frafm /= frtot;
        frhyg /= frtot;
        heat4 +=
            (frafm * 1.144 * (double)(Oc3ainit - Count[OC3A]) * Specgrav[OC3A]);
        heat4 +=
            (frhyg * 0.908 * (double)(Oc3ainit - Count[OC3A]) * Specgrav[OC3A]);
        heat4 += (frettr * 1.672 * (double)(Oc3ainit - Count[OC3A]) *
                  Specgrav[OC3A]);
      }

    } else if (i == C4AF) {

      Alpha += ((double)(C4afinit - Count[C4AF]));
      mass_now += (Specgrav[C4AF] * (double)Count[C4AF]);
      mc3ar = (double)(C3ainit - Count[C3A]) / Molarv[C3A];
      mc3ar += ((double)(Oc3ainit - Count[OC3A]) / Molarv[OC3A]);
      mc4ar = (double)(C4afinit - Count[C4AF]) / Molarv[C4AF];

      if ((mc3ar + mc4ar) > 0.0) {
        frhyg =
            (mc4ar / (mc3ar + mc4ar)) * (double)Count[C3AH6] / Molarv[C3AH6];
      } else {
        frhyg = 0.0;
      }

      frettr = (double)Count[ETTRC4AF] / Molarv[ETTRC4AF];
      frtot = frettr + frhyg;

      if (frtot > 0.0) {
        frettr /= frtot;
        frhyg /= frtot;
        heat4 +=
            (frhyg * 0.418 * (double)(C4afinit - Count[C4AF]) * Specgrav[C4AF]);
        heat4 += (frettr * 0.725 * (double)(C4afinit - Count[C4AF]) *
                  Specgrav[C4AF]);
      }

    } else if (i == ANHYDRITE) {

      /*
      Alpha+=(float)(Anhinit-Count[ANHYDRITE]);
      mass_now+=Specgrav[ANHYDRITE]*(float)Count[ANHYDRITE];
      */

      /***
       *    0.187 kJ/g anhydrite for
       *    anhydrite --> gypsum conversion
       ***/

      heat4 +=
          (0.187 * (double)(Anhinit - Count[ANHYDRITE]) * Specgrav[ANHYDRITE]);

      /***
       *    2 moles of water consumed per mole of
       *    anhydrite reacted
       ***/

      Molesh2o +=
          ((double)(Anhinit - Count[ANHYDRITE]) * 2.0 / Molarv[ANHYDRITE]);

    } else if (i == HEMIHYD) {

      /*
      Alpha += (float)(Heminit - Count[HEMIHYD]);
      mass_now += Specgrav[HEMIHYD] * (float)Count[HEMIHYD];
      */

      /***
       *    0.132 kJ/g hemihydrate for
       *    hemihydrate-->gypsum conversion
       ***/

      heat4 += (0.132 * (double)(Heminit - Count[HEMIHYD]) * Specgrav[HEMIHYD]);

      /***
       *    1.5 moles of water consumed per mole
       *    of hemihydrate converted
       ***/

      Molesh2o += ((double)(Heminit - Count[HEMIHYD]) * 1.5 / Molarv[HEMIHYD]);

    } else if (i == K2SO4) {

      /***
       *    0.070 kJ/g potassium sulfate for
       *    k2so4-->gypsum conversion
       ***/

      heat4 += (0.070 * (double)(Ksulfinit - Count[K2SO4]) * Specgrav[K2SO4]);

      /***
       *    All K2SO4 dissolved assumed to form GYPSUMS,
       *    thus consuming 2.0 moles of water
       ***/

      Molesh2o += ((double)(Ksulfinit - Count[K2SO4]) * 2.0 / Molarv[K2SO4]);

    } else if (i == NA2SO4) {

      /***
       *    0.442 kJ/g sodium sulfate for
       *    na2so4-->gypsum conversion
       ***/

      heat4 +=
          (0.442 * (double)(Nasulfinit - Count[NA2SO4]) * Specgrav[NA2SO4]);

      /***
       *    All NA2SO4 dissolved assumed to form GYPSUMS,
       *    thus consuming 2.0 moles of water
       ***/

      Molesh2o += ((double)(Nasulfinit - Count[NA2SO4]) * 2.0 / Molarv[NA2SO4]);

    } else if (i == FREELIME) {

      heat4 += (0.979 * (double)(Freelimeinit - Count[FREELIME]) *
                Specgrav[FREELIME]);
    }
  }

  mass105 *= volpix;
  massdiff *= (volpix * molwh2o);

  mass1000 = mass105 - massdiff;

  /***
   *    Calculate non-evaporable water content on relative to
   *        (1) original dry cement powder
   *        (2) ignited cement powder
   ***/

  if (mass1000 <= 0.0 || Mass_105 <= 0.0) {
    Wn_o = 0.0;
    Wn_i = 0.0;
  } else {
    Wn_o = ((mass105 * Mass_1000) / (mass1000 * Mass_105)) - 1.0;

    Wn_i = (mass105 / mass1000) - 1.0;
    Wn_i -= ((Mass_105 / Mass_1000) - 1.0);
  }

  if (suminit != 0) {
    Alpha /= (float)suminit;
  } else {
    Alpha = 0.0;
  }

  /* Current degree of hydration on a mass basis */

  if (Cemmass > 0.0) {
    Alpha_cur = 1.0 - (mass_now / Cemmass);
  } else {
    Alpha_cur = 0.0;
  }

  /* Current degree of hydration of fly ash on a mass basis */

  mass_fa_now = Specgrav[SFUME] * (double)Count[SFUME];
  mass_fa_now += Specgrav[AMSIL] * (double)Count[AMSIL];
  mass_fa_now += Specgrav[ASG] * (double)Count[ASG];
  mass_fa_now += Specgrav[CAS2] * (double)Count[CAS2];
  vol_fa_now = (double)Count[SFUME];
  vol_fa_now += (double)Count[AMSIL];
  vol_fa_now += (double)Count[ASG];
  vol_fa_now += (double)Count[CAS2];

  if (Flyashmass > 0.0) {
    Alpha_fa_cur = 1.0 - (mass_fa_now / Flyashmass);
    Alpha_fa_vol = 1.0 - (vol_fa_now / Flyashvol);
  } else {
    Alpha_fa_cur = 0.0;
    Alpha_fa_vol = 0.0;
  }

  /***
   * h2oinit is the intial number of MOLES of water.  Water
   * and saturated porosity are assumed to be one and the same,
   * so Porinit, being the number of voxels of saturated porosity
   * and therefore a measure of the saturated pore volume, is
   * assumed to be the same as the volume of pure water
   ***/
  h2oinit = (float)Porinit / Molarv[POROSITY];

  /***
   *    Only will be important if a crack is added at
   *    the zeroth cycle, which currently is not possible
   *    (24 May 2004)
   ***/

  h2oinit += (float)Crackpinit / Molarv[CRACKP];

  /***
   *    ASSUME 0.78 kJ/g S for pozzolanic reaction
   *
   *    Each unit of silica fume consumes 1.35 units of CH,
   *    so divide Nsilica_rx by 1.35 to get silca fume which has reacted
   *    (Nsilica_rx = number silica units that have reacted)
   ***/

  psfact = (SF_SiO2_val) / 100.0;
  heat4 += 0.78 * psfact * ((float)Nsilica_rx / 1.35) * Specgrav[SFUME];

  /***
   *    ASSUME 0.8 kJ/g S for slag reaction
   *
   *    Seems consistent with measurements made by
   *    Biernacki and Richardson
   ***/

  heat4 += 0.8 * ((float)Nslagr) * Specgrav[SLAG];

  /***
   *    ASSUME 0.8 kJ/g AS for stratlingite formation (DeLarrard)
   *
   *    Each unit of AS consumes 1.3267 units of CH,
   *    so divide Nasr by 1.3267 to get ASG which has reacted
   ***/

  heat4 += 0.8 * ((float)Nasr / 1.3267) * Specgrav[ASG];

  /***
   *    Should be additional code here for heat release
   *    due to CAS2 --> stratlingite conversion, but data
   *    are unavailable at this time
   ***/

  /***
   *    Adjust heat sum for water left in system...
   *    The addition of 0.5 ensures that we round to the
   *    nearest integer
   *
   *    h2oinit is the initial MOLES of water in the system
   *    Molesh2o is the number of MOLES of water consumed by all hydration
   *        reactions over all cycles. It is set to zero at the
   *        beginning of each dissolve cycle and
   *        recalculated
   *
   *    Water_left is the VOLUME of liquid water remaining in the system,
   *    which should include water in capillary pores AND water in
   *    CSH gel pores.
   *
   ***/

  Water_left = (h2oinit - Molesh2o) * Molarv[POROSITY] + 0.5;
  Water_left += Count[CRACKP];
  Countkeep = Count[POROSITY] + Count[CRACKP];
  Heatsum += ((h2oinit - Molesh2o - molesdh2o) * Heatf[POROSITY]);

  if (Cyccnt == 0) {
    Datafile = filehandler("disrealnew", Datafilename, "WRITE");
    if (!Datafile) {
      freeallmem();
      exit(1);
    }
    fprintf(Datafile, "Cycle,time(h),Alpha_mass,");
    fprintf(Datafile, "Alpha_fa_mass,heat(kJ/kg_cem),");
    fprintf(Datafile, "Temperature(C),Gsratio,");
    fprintf(Datafile, "Wno(g/g),Wni(g/g),ChemShrink(mL/g),pH,");
    fprintf(Datafile, "Conductivity(S/m),[Na+](M),[K+](M),[Ca++](M),");
    fprintf(Datafile, "[SO4--](M),{K+},{Ca++},{OH-},{SO4--},");
    fprintf(Datafile, "Vfpore,Poreconnx,Poreconny,Poreconnz,Poreconnave,");
    fprintf(Datafile, "Solidconnx,Solidconny,Solidconnz,Solidconnave,");
    fprintf(Datafile, "VfC3S,VfC2S,VfC3A,VfOC3A,");
    fprintf(Datafile, "VfC4AF,VfK2SO4,VfNA2SO4,VfGYPSUM,");
    fprintf(Datafile, "VfHEMIHYD,VfANHYDRITE,VfCACO3,");
    fprintf(Datafile, "VfFREELIME,VfSFUME,VfINERT,");
    fprintf(Datafile, "VfSLAG,VfASG,VfCAS2,VfAMSIL,");
    fprintf(Datafile, "VfCH,VfCSH,VfPOZZCSH,VfSLAGCSH,");
    fprintf(Datafile, "VfC3AH6,VfETTR,VfAFM,VfFH3,");
    fprintf(Datafile, "VfCACL2,VfFRIEDEL,VfSTRAT,VfGYPSUMS,");
    fprintf(Datafile, "VfABSGYP,VfAFMC,VfINERTAGG,VfEMPTYP\n");
    fclose(Datafile);

    if ((fpout01 = fopen("SfumeEffect.csv", "w")) == NULL) {
      printf("\nWARNING:  Could not open SfumeEffect.csv to write header\n");
    } else {
      fprintf(fpout01,
              "CSH,TOTCSH,Cs_acc,Psfume,dface,Cshscale,Disprob[C3S]\n");
      fclose(fpout01);
    }
  }

  /***
   *    Use heat4 for all adiabatic calculations
   *    due to best agreement with calorimetry data
   ***/

  Heat_new = heat4;

  /***
   *    Should we include water in saturated CRACKP in the
   *    calculations for chemical shrinkage?  Currently, no.
   *    (24 May 2004)
   ***/

  Chs_new = ((double)(Count[EMPTYP] + Count[POROSITY] - Water_left) * Heat_cf /
             1000.0);

  if (Verbose)
    printf("\nChs_new = %f\n", Chs_new);
  if (((Water_left + Water_off) < 0) && (Sealed == 1)) {
    if (Verbose)
      printf("All water consumed at cycle %d \n", Cyccnt);
    fflush(stdout);
    freeallmem();
    bailout("dissolve", "Normal exit");
    exit(1);
  }

  /***
   *    Attempt to create empty porosity to account
   *    for self-desiccation
   *
   *    Water_left is the total volume of LIQUID water in the system,
   *    which can occupy both capillary pores, (POROSITY) voxels, and
   *    also part of the CSH voxels depending on the internal
   *    gel porosity.
   *
   *    Water_off is the volume of LIQUID water that was in the
   *    system at the moment the pore space depercolated, otherwise
   *    it is zero.
   *
   *   See H.F.W. Taylor, Mater. Res. Soc. Proc.
   * 	Vol. 85, p. 47 (1987) for information on
   * 	stoichiometry at 105 C
   *
   *   In that paper, Taylor proposes that the molar
   *   ratio of BOUND H2O to Ca is 1.4. So if C-S-H
   *   is defined as 1 mol CSH = 1 mol Si, then 1 mol
   *   of CSH has 1.7 mol Ca and therefore 2.38 moles
   *   of bound water per mole of CSH.
   *
   *   So Waterc[CSH] of 4.0 assumes
   *   1.62 moles of free water per mole of CSH.
   *   Using the Molarv[CSH] value of 107.81 cm3
   *   below, and the fact that 1.62 moles of free water
   *   occupies a volume of 29.16 cm3, this implies that
   *   CSH has an internal free-water pore volume
   *   of 29.16 cm3/mole or a free water volume
   *   fraction of 0.27.
   *
   *   Therefore, the condition below was changed to account
   *   for the free water in CSH.
   *
   *   @TODO Change the hard-wired 0.27 factor below to account
   *   for changes in free water volume fraction due to
   *   temperature change.
   *
   *	18 Dec 2020
   *
   ***/

  if ((Sealed == 1) && ((Count[POROSITY] + Count[CRACKP] + (0.27 * Count[CSH]) -
                         Water_left) > 0)) {
    Poretodo =
        (Count[POROSITY] + Count[CRACKP] + (0.27 * Count[CSH]) - Pore_off) -
        (Water_left - Water_off) - Slagemptyp;

    if (Poretodo > 0) {
      makeinert(Poretodo);
      Poregone += Poretodo;
    }
  }

  /***
   *    The following is an adjusted pH to compensate
   *    for the water/c ratio, relative to a w/c
   *    of 0.4.  This appears to be necessary only for
   *    flyash reactions.  Eventually should be eliminated
   *    in favor of something more realistic.
   ***/

  ohadj = log10(pow((W_to_c / 0.503130), 0.75) * pow(10.0, (PH_cur - 14.0)));
  ohadj += 14.0;

  /***
   *    Output phase counts
   *    phfile for reactant and product phases
   ***/

  if (cycle == 0) {
    return;
  }

  Cyccnt++;

  /* Update current volume count for CH */
  Chold = Chnew;
  Chnew = Count[CH];

  /***
   *    See if ettringite is soluble yet:
   *        (a) Gypsum 75% consumed (changed 09.09.01 from 80% to 75%),
   *        (b) or system temperature exceeds 70 C
   ***/

  if (((Ncsbar + Anhinit + Heminit) > 0.0) || (Temp_cur_b >= 70.0)) {

    /* Account for all sulfate sources and forms */

    fact = (double)Count[GYPSUM] + 1.42 * (double)Count[ANHYDRITE] +
           1.4 * (double)Count[HEMIHYD] + 1.13 * (double)Count[K2SO4] +
           1.4 * (double)Count[NA2SO4] + (double)Count[GYPSUMS];
    fact /= ((double)Ncsbar + 1.42 * (double)Anhinit +
             1.13 * (double)Ksulfinit + 1.4 * (double)Nasulfinit +
             1.4 * (double)Heminit + ((double)Netbar / 3.30));

    if ((!Soluble[ETTR]) &&
        ((Temp_cur_b >= 70.0) || (Count[AFM] > 0) || (fact < 0.25))) {

      Soluble[ETTR] = 1;
      if (Verbose)
        printf("Ettringite is soluble beginning at cycle %d \n", cycle);

      /* Identify all new soluble ettringite */

      passone(ETTR, ETTR, 2, 0);
    }
  } /* end of soluble ettringite test */

  /***
   *    Calculate the volume fraction of saturated porosity
   *    relative to the reference volume fraction for a system
   *    with initial w/c of 0.4.  That is, Vfpores is 1.0 when
   *    the porosity is equal to the initial porosity for a system
   *    with w/c of 0.4
   *
   *    18 April 2003
   *
   *    Currently, we do NOT include water in saturated cracks
   *    formed during hydration as part of the volume fraction of
   *    porosity.  Modify the line below to change this.
   *
   *    24 May 2004
   ***/

  Relvfpores = ((double)Count[POROSITY]) / ((double)Syspix);

  /***
   *    Normalize to that for w/c = 0.4 (= WCSCALE)
   ***/

  refporefrac = 1.0 / (1.0 + (Specgrav[POROSITY] / (Meancemdens * WCSCALE)));
  Relvfpores /= refporefrac;

  /***
   *    The following are all maximum or critical numbers
   *    of diffusing pixels.  For example, DETTRMAX is an
   *    absolute number of pixels, which must be modified
   *    to reflect increases in system size and changes
   *    in the volume fraction of porosity
   *
   *    Change made 4 April 2003
   ***/

  Dk2so4max = (int)(((double)DK2SO4MAX) * Sizemag * Relvfpores);
  Dna2so4max = (int)(((double)DNA2SO4MAX) * Sizemag * Relvfpores);
  Dettrmax = (int)(((double)DETTRMAX) * Sizemag * Relvfpores);
  Dgypmax = (int)(((double)DGYPMAX) * Sizemag * Relvfpores);
  Dcaco3max = (int)(((double)DCACO3MAX) * Sizemag * Relvfpores);
  Dcacl2max = (int)(((double)DCACL2MAX) * Sizemag * Relvfpores);
  Dcas2max = (int)(((double)DCAS2MAX) * Sizemag * Relvfpores);
  Dasmax = (int)(((double)DASMAX) * Sizemag * Relvfpores);

  Chcrit = CHCRIT * Sizemag * Relvfpores;

  /***
   *    Adjust Chcrit higher if pozzolanic material is
   *    available in the system (4 April 2003)
   *
   *    Disabled on 9 April 2003
   ***/

  if ((((double)(Count[SFUME] + Count[AMSIL])) / ((double)Syspix)) > 0.01) {
    Chcrit *= 10.0;
  }

  C3ah6crit = C3AH6CRIT * Sizemag * Relvfpores;

  /***
   *    Adjust ettringite solubility
   *    if too many ettringites already in solution
   ***/

  if (Count[DIFFETTR] > Dettrmax) {
    Disprob[ETTR] = 0.0;
  } else {
    Disprob[ETTR] = Disbase[ETTR];
  }

  /***
   *    Adjust CaCl2 solubility
   *    if too many CaCl2 already in solution
   ***/

  if (Count[DIFFCACL2] > Dcacl2max) {
    Disprob[CACL2] = 0.0;
  } else {
    Disprob[CACL2] = Disbase[CACL2];
  }

  /***
   *    Adjust CaCO3 solubility
   *    if too many CaCO3 already in solution
   ***/

  if ((Count[DIFFCACO3] > Dcaco3max) && (!Soluble[ETTR])) {
    Disprob[CACO3] = 0.0;
  } else if (Count[DIFFCACO3] > (4 * Dcaco3max)) {
    Disprob[CACO3] = 0.0;
  } else {
    Disprob[CACO3] = Disbase[CACO3];
  }

  /***
   *    Adjust solubility of CH based on amount of CH
   *    currently diffusing
   *
   *    Note that CH is always soluble to allow some
   *    Ostwald ripening of the CH crystals
   ***/

  if ((double)Count[DIFFCH] >= Chcrit) {
    Disprob[CH] = Disbase[CH] * Chcrit / (double)Count[DIFFCH];
  } else {
    Disprob[CH] = Disbase[CH];
  }

  /***
   *    Adjust solubility of CH for temperature
   *
   *    Fit to data provided in
   *
   *        H.F.W. Taylor, "Cement Chemistry", 2nd Edition,
   *        Telford Publishing, London, 1997
   *
   *    Scale to a reference temperature of 25 C
   *    and adjust based on availability of pozzolan
   ***/

  if (Verbose)
    printf("Count[DIFFCH] = %d, Chcrit = %f, Disbase[CH] = %f\n", Count[DIFFCH],
           Chcrit, Disbase[CH]);
  if (Verbose)
    printf("CH dissolution probability changes from %f ", Disprob[CH]);
  Disprob[CH] *=
      ((A0_CHSOL - (A1_CHSOL * Temp_cur_b)) / (A0_CHSOL - (A1_CHSOL * 25.0)));

  if ((((double)Count[SFUME]) / ((double)Syspix)) > 0.01) {
    if (PHfactor[SFUME] * Psfume > 0.0) {
      Disprob[CH] *= PHfactor[SFUME] * (Psfume / PSFUME);
    }
  } else if ((((double)Count[AMSIL]) / ((double)Syspix)) > 0.01) {
    if (PHfactor[AMSIL] * Pamsil > 0.0) {
      Disprob[CH] *= PHfactor[AMSIL] * (Pamsil / PAMSIL);
    }
  }

  if (Verbose)
    printf("to %f \n", Disprob[CH]);

  /***
   *    Adjust solubility of ASG and CAS2 phases
   *    based on pH rise during hydration
   *
   *     This is now handled later in this function
   *     with PHfactors for ASG, CAS2, and AMSIL
   ***/

  Disprob[ASG] = Disbase[ASG];
  Disprob[CAS2] = Disbase[CAS2];

  /***
   *    Address solubility of C3AH6 (hydrogarnet)
   *
   *    If lots of gypsum or reactive ettringite,
   *    allow C3AH6 to dissolve to generate diffusing
   *    C3A species
   ***/

  fact =
      ((double)Ncsbar + 1.42 * (double)Anhinit + 1.4 * (double)Heminit) * 0.05;
  if (((Count[GYPSUM] + Count[GYPSUMS]) > (int)(fact)) || (Count[ETTR] > 500)) {

    Soluble[C3AH6] = 1;

    /* Identify all new soluble C3AH6 */
    passone(C3AH6, C3AH6, 2, 0);

    /***
     *    C3AH6 is soluble, so we must determine Disprob for it.
     *    Base C3AH6 solubility on maximum sulfate in solution
     *    from gypsum or ettringite available for dissolution
     *
     *    The more the sulfate, the higher this solubility
     *    should be
     ***/

    maxsulfate = Count[DIFFGYP];
    if ((maxsulfate < Count[DIFFETTR]) && (Soluble[ETTR] == 1)) {
      maxsulfate = Count[DIFFETTR];
    }

    /***
     *    Adjust C3AH6 solubility based on potential
     *    gypsum which will dissolve
     ***/

    maxallowed = (int)((double)Gypready * Disprob[GYPSUM] *
                       (double)Count[POROSITY] / ((double)(Syspix)));

    if (maxsulfate < maxallowed)
      maxsulfate = maxallowed;

    if (maxsulfate > 0) {
      Disprob[C3AH6] = Disbase[C3AH6] * (double)maxsulfate / C3ah6crit;
      if (Disprob[C3AH6] > 0.5)
        Disprob[C3AH6] = 0.5;
    } else {
      Disprob[C3AH6] = Disbase[C3AH6];
    }

  } else {

    Soluble[C3AH6] = 0;

  } /* end of soluble C3AH6 test */

  /* See if silicates are soluble yet */

  if ((!Soluble[C3S]) && ((cycle > 1) || (Count[ETTR] > 0) ||
                          (Count[AFM] > 0) || (Count[ETTRC4AF] > 0))) {

    Soluble[C2S] = 1;
    Soluble[C3S] = 1;

    /* Identify all new soluble silicates */
    passone(C3S, C2S, 2, 0);

  } /* end of soluble silicate test */

  /***
   *    Adjust solubility of C3S and C2S with
   *    CSH concentration for simulation of
   *    induction period
   ***/

  tdisfact = A0_CHSOL - (Temp_cur_b * A1_CHSOL);

  /***
   *    Calculation of Cs_acc; acceleration of C3S and C2S
   *        reaction by CaSO4
   *
   *    Calculation of Ca_acc; acceleration of C3A and C4AF
   *        reaction by CaSO4
   ***/

  if ((Ncsbar + Anhinit + Heminit) == 0) {
    Cs_acc = 1.0;
    Ca_acc = 1.0;
    Dismin_c3a = resfact * 5.0 * DISMIN_C3A_0;
    Dismin_c4af = resfact * 5.0 * DISMIN_C4AF_0;
  } else {
    Pfract = ((float)Count[POROSITY]) / ((float)Syspix);
    Sulf_conc = Sulf_cur * Tfractw05 * Pfractw05 / Totfract / Pfract;
    if ((double)Sulf_conc < 10.0) {
      Cs_acc = 1.0;
      Ca_acc = 1.0;
      Dismin_c3a = resfact * DISMIN_C3A_0;
      Dismin_c4af = resfact * DISMIN_C4AF_0;
    } else if ((double)Sulf_conc < 20.0) {
      Cs_acc = 1.0 + ((double)Sulf_conc - (10.0)) / 10.0;
      Ca_acc = 1.0;
      Dismin_c3a = resfact * DISMIN_C3A_0;
      Dismin_c4af = resfact * DISMIN_C4AF_0;
    } else {
      Cs_acc = 1.0 + (float)log10((double)Sulf_conc);
      Ca_acc = 1.0;
      Dismin_c3a =
          (6.0 - (float)log10((double)Sulf_conc)) * resfact * DISMIN_C3A_0;
      Dismin_c4af =
          (6.0 - (float)log10((double)Sulf_conc)) * resfact * DISMIN_C4AF_0;

      if (Dismin_c3a < resfact * DISMIN_C3A_0) {
        Dismin_c3a = resfact * DISMIN_C3A_0;
      }
      if (Dismin_c4af < resfact * DISMIN_C4AF_0) {
        Dismin_c4af = resfact * DISMIN_C4AF_0;
      }
    }
  }

  factCSH = (double)(Count[CSH]) / (double)(Cshscale);
  factPOZZCSH = (double)(Count[POZZCSH]) / (double)(Pozzcshscale);
  factTfract = Tfractw04 / (Surffract * Totfract);

  fact = (factCSH + factPOZZCSH) * factTfract;

  dfact = tdisfact * fact * fact * Cs_acc;
  if (Count[SFUME] >= (0.05 * (double)(Syspix))) {
    dfact /= LOI_factor;
  }
  if (Verbose) {
    printf("\n****Modifying dissolution probabilities : ");
    printf("\n    tdisfact = %f and Cs_acc = %f", tdisfact, Cs_acc);
    printf("\n    Psfume = %f", Psfume);
    printf("\n    fact = %f", fact);
    printf("\n        Count[CSH] = %d", Count[CSH]);
    printf(" Tfractw04 = %f", Tfractw04);
    printf(" Cshscale = %f", Cshscale);
    printf("\n        Surffract = %f", Surffract);
    printf(" Totfract = %f\n", Totfract);
    printf("\n        resfact = %f dfact = %f\n", resfact, dfact);
    printf("\n        A0_CHSOL = %f", A0_CHSOL);
    printf(" A1_CHSOL = %f", A1_CHSOL);
    printf(" Temp_cur_b = %f\n\n", Temp_cur_b);
    fflush(stdout);
  }

  Disprob[C3S] = (resfact * DISMIN) + (dfact * Disbase[C3S]);
  Disprob[C2S] = (resfact * DISMIN2) + (dfact * Disbase[C2S]);

  if (Disprob[C3S] > (1.0 * Disbase[C3S])) {
    Disprob[C3S] = (1.0 * Disbase[C3S]);
  }

  if (Disprob[C2S] > (1.0 * Disbase[C2S])) {
    Disprob[C2S] = (1.0 * Disbase[C2S]);
  }

  if ((fpout01 = fopen("SfumeEffect.csv", "a")) == NULL) {
    printf("\nWARNING:  Could not open");
    printf(" SfumeEffect.csv for writing\n");
  } else {
    fprintf(fpout01, "\n%f,%f,%f,%f,%f,%f,%f", (double)Count[CSH],
            (double)(Count[CSH] + Count[POZZCSH]), Cs_acc, Psfume, dfact,
            Cshscale, Disprob[C3S]);
    fclose(fpout01);
  }

  /***
   *    THIS NEXT LINE IS FOR TESTING ONLY
   ***/

  /* Disprob[C3S] = Disbase[C3S]; */

  /***************************************/

  /***
   *    Also adjust slag and fly ash dissolution rates here.
   *
   *    Really slow down initial slag and fly ash dissolutions.
   *    Ultimately should be linked to pH of pore solution,
   *    most likely
   ***/

  Disprob[SLAG] =
      Slagreact * ((resfact * DISMINSLAG) + dfact * Disbase[SLAG]) / 10.0;

  if (Disprob[SLAG] > (Slagreact * Disbase[SLAG])) {
    Disprob[SLAG] = (Slagreact * Disbase[SLAG]);
  }

  if (Disprob[C3S] == Disbase[C3S]) {
    Disprob[SLAG] = Slagreact * Disbase[SLAG];
  }

  Disprob[ASG] = (resfact * DISMINASG) + (dfact * Disbase[ASG] / 5.0);

  if (Disprob[ASG] > (1.0 * Disbase[ASG])) {
    Disprob[ASG] = (1.0 * Disbase[ASG]);
  }

  if (Disprob[C3S] == Disbase[C3S]) {
    Disprob[ASG] = Disbase[ASG];
  }

  Disprob[CAS2] = (resfact * DISMINCAS2) + (dfact * Disbase[CAS2] / 5.0);

  if (Disprob[CAS2] > (1.0 * Disbase[CAS2])) {
    Disprob[CAS2] = (1.0 * Disbase[CAS2]);
  }

  if (Disprob[C3S] == Disbase[C3S]) {
    Disprob[CAS2] = Disbase[CAS2];
  }

  /***
   *    Adjust CAS2 solubility
   *    if too many CAS2 already in solution
   ***/

  if (Count[DIFFCAS2] > Dcas2max) {
    Disprob[CAS2] *= pow((Dcas2max / ((double)Count[DIFFCAS2])), 2.0);
  }

  /***
   *    Adjust ASG solubility
   *    if too many ASG already in solution
   ***/

  if (Count[DIFFAS] > Dasmax) {
    Disprob[ASG] *= pow((Dasmax / ((double)Count[DIFFAS])), 2.0);
  }

  if (Verbose)
    printf("Silicate probabilities: %f %f\n", Disprob[C3S], Disprob[C2S]);

  /***
   *    ASSUME that aluminate dissolution controlled by formation
   *    of impermeable layer proportional to CSH concentration
   *    if sulfates are present in the system
   ***/

  if ((Ncsbar + Heminit + Anhinit) > (1000 * Isizemag)) {

    dfact1 = tdisfact * fact * fact * Ca_acc;

    Disprob[C3A] = Dismin_c3a + (dfact1 * Disbase[C3A]);
    Disprob[OC3A] = Dismin_c3a + (dfact1 * Disbase[OC3A]);
    Disprob[C4AF] = Dismin_c4af + (dfact1 * Disbase[C4AF]);

    if (Disprob[C3A] > (1.0 * Disbase[C3A])) {
      Disprob[C3A] = (1.0 * Disbase[C3A]);
    }

    if (Disprob[OC3A] > (1.0 * Disbase[OC3A])) {
      Disprob[OC3A] = (1.0 * Disbase[OC3A]);
    }

    if (Disprob[C4AF] > (1.0 * Disbase[C4AF])) {
      Disprob[C4AF] = (1.0 * Disbase[C4AF]);
    }

    /***
     *    Location to add in dissolution reduction in
     *    calcium sulfate phases if needed
     ***/

    Disprob[GYPSUM] = (Disbase[GYPSUM] / 15.0) + (dfact1 * Disbase[GYPSUM]);

    if (Disprob[GYPSUM] > Disbase[GYPSUM]) {
      Disprob[GYPSUM] = Disbase[GYPSUM];
    }

    Disprob[GYPSUMS] = (Disbase[GYPSUMS] / 15.0) + (dfact1 * Disbase[GYPSUMS]);

    if (Disprob[GYPSUMS] > Disbase[GYPSUMS]) {
      Disprob[GYPSUMS] = Disbase[GYPSUMS];
    }

    /***
     *    Adjust gypsum solubility if too many diffusing
     *    gypsums already in solution
     ***/

    if (Count[DIFFGYP] > Dgypmax) {
      Disprob[GYPSUM] = Disprob[GYPSUMS] = 0.0;
    }

    Disprob[HEMIHYD] = (Disbase[HEMIHYD] / 15.0) + (dfact1 * Disbase[HEMIHYD]);

    if (Disprob[HEMIHYD] > Disbase[HEMIHYD]) {
      Disprob[HEMIHYD] = Disbase[HEMIHYD];
    }

    Disprob[ANHYDRITE] =
        (Disbase[ANHYDRITE] / 15.0) + (dfact1 * Disbase[ANHYDRITE]);

    if (Disprob[ANHYDRITE] > Disbase[ANHYDRITE]) {
      Disprob[ANHYDRITE] = Disbase[ANHYDRITE];
    }

  } else {

    /***
     *    Cause flash set by increasing dissolution rates
     *    of C3A and C4AF each by a factor of four
     ***/

    Disprob[C3A] = 4.0 * Disbase[C3A];
    Disprob[OC3A] = 4.0 * Disbase[OC3A];
    Disprob[C4AF] = 4.0 * Disbase[C4AF];
    Disprob[GYPSUM] = Disbase[GYPSUM];
    Disprob[HEMIHYD] = Disbase[HEMIHYD];
    Disprob[ANHYDRITE] = Disbase[ANHYDRITE];
  }

  /***
   *    Reduce dissolution probabilities based on
   *    saturation of system
   ***/

  /* fact is 22% of the system volume */

  fact = 0.22 * (double)Syspix;

  if ((Count[EMPTYP] > 0) && ((Count[POROSITY] + Count[EMPTYP]) < fact)) {

    if (Countpore == 0)
      Countpore = Count[EMPTYP];

    Saturation = (double)(Count[POROSITY]) /
                 (double)(Count[POROSITY] + Count[EMPTYP] - Countpore);

    /***
     *    Roughly according to results of Jensen, powers for
     *    RH sensitivity are:
     *        C3S --> -19
     *        C2S --> -29
     *        C3A --> -6
     *        OC3A --> -6, but this is just a guess based on C3A
     *        C4AF--> -6
     *
     *    Adjust fly ash silicates (ASG and CAS2) and
     *    pozzolanic reactivity by same factor as
     *    C3S (also CH)
     ***/

    satsquared = Saturation * Saturation;
    if (Verbose)
      printf("\nsaturation = %f\n", Saturation);
    Disprob[C3S] *= satsquared;
    Disprob[C3S] *= satsquared;
    Disprob[C3S] *= satsquared;
    Disprob[C3S] *= satsquared;
    Disprob[C3S] *= satsquared;
    Disprob[C3S] *= satsquared;
    Disprob[C3S] *= satsquared;
    Disprob[C3S] *= satsquared;
    Disprob[C3S] *= satsquared;
    Disprob[C3S] *= (Saturation);

    Disprob[SLAG] *= satsquared;
    Disprob[SLAG] *= satsquared;
    Disprob[SLAG] *= satsquared;
    Disprob[SLAG] *= satsquared;
    Disprob[SLAG] *= satsquared;
    Disprob[SLAG] *= satsquared;
    Disprob[SLAG] *= satsquared;
    Disprob[SLAG] *= satsquared;
    Disprob[SLAG] *= satsquared;
    Disprob[SLAG] *= (Saturation);

    Disprob[CH] *= satsquared;
    Disprob[CH] *= satsquared;
    Disprob[CH] *= satsquared;
    Disprob[CH] *= satsquared;
    Disprob[CH] *= satsquared;
    Disprob[CH] *= satsquared;
    Disprob[CH] *= satsquared;
    Disprob[CH] *= satsquared;
    Disprob[CH] *= satsquared;
    Disprob[CH] *= (Saturation);

    /***
     *    Removed dependence on RH of flyash silicate
     *    dissolution    probabilities and pozzolanic
     *    reaction rate on RH,to better fit recent
     *    experimental data on flyash consumption
     *    under sealed conditions    (Garboczi and Feng,
     *    unpublished).
     *
     *    April 18 2003
     ***/

    /*
    Disprob[ASG] *= satsquared;
    Disprob[ASG] *= satsquared;
    Disprob[ASG] *= satsquared;
    Disprob[ASG] *= satsquared;
    Disprob[ASG] *= satsquared;
    Disprob[ASG] *= satsquared;
    Disprob[ASG] *= satsquared;
    Disprob[ASG] *= satsquared;
    Disprob[ASG] *= satsquared;
    Disprob[ASG] *= (Saturation);

    Disprob[CAS2] *= satsquared;
    Disprob[CAS2] *= satsquared;
    Disprob[CAS2] *= satsquared;
    Disprob[CAS2] *= satsquared;
    Disprob[CAS2] *= satsquared;
    Disprob[CAS2] *= satsquared;
    Disprob[CAS2] *= satsquared;
    Disprob[CAS2] *= satsquared;
    Disprob[CAS2] *= satsquared;
    Disprob[CAS2] *= (Saturation);

    Ppozz *= satsquared;
    Ppozz *= satsquared;
    Ppozz *= satsquared;
    Ppozz *= satsquared;
    Ppozz *= satsquared;
    Ppozz *= satsquared;
    Ppozz *= satsquared;
    Ppozz *= satsquared;
    Ppozz *= satsquared;
    Ppozz *= (Saturation);
    */

    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= satsquared;
    Disprob[C2S] *= (Saturation);

    Disprob[C3A] *= satsquared;
    Disprob[C3A] *= satsquared;
    Disprob[C3A] *= satsquared;

    Disprob[OC3A] *= satsquared;
    Disprob[OC3A] *= satsquared;
    Disprob[OC3A] *= satsquared;

    Disprob[C4AF] *= satsquared;
    Disprob[C4AF] *= satsquared;
    Disprob[C4AF] *= satsquared;

  } /* Done reducing dissolutions based on saturation */

  if (Verbose) {
    printf("Silicate and aluminate probabilities: ");
    printf("%f %f ", Disprob[C3S], Disprob[C2S]);
    printf("%f %f %f %f %f\n", Disprob[C3A], Disprob[OC3A], Disprob[C4AF],
           Disprob[GYPSUM], Disprob[HEMIHYD]);
    printf("Cs_acc is %f and Ca_acc is %f Sulf_cur is %d Sulf_conc is %f\n",
           Cs_acc, Ca_acc, Sulf_cur, Sulf_conc);
    printf("Pfract is %f and Totfract is %f and Tfractw05 is %f and Pfractw05 "
           "is %f\n",
           Pfract, Totfract, Tfractw05, Pfractw05);
  }

  /***
   *    PASS TWO:  Perform the dissolution of species
   *
   *    Determine the pH factor to use.  Only use pH
   *    influence if user asked for it AND hydration
   *    has proceeded beyond the induction period
   *
   *    Set possibility of topochemical conversion of silicates
   *    to CSH if pH effect is active, and also set the proximity
   *    within which dissolved silicates are placed relative to the
   *    dissolution source, to simulate the higher-density CSH
   *    that is thought to form in the presence of alkalies
   *    (see Juenger and Jennings, ACI Materials Journal,
   *    Vol. 98, No. 3, pp. 251-255 (2001).
   *
   *    pH influences the proximity of location of
   *    dissolved silicates to the dissolution source,
   *    to simulate the higher-density CSH reported in
   *    the presence of alkalies.  Assume this happens
   *    from the very beginning of hydration.
   *
   *    pH also "turns on" the possibility of direct
   *    topochemical conversion of anhydrous silicates
   *    to CSH.  Assume this happens from the very beginning
   *    of hydration
   ***/

  Distloccsh = DISTLOCCSH;
  Pdirectcsh = 0.0;
  if (PHactive == 1) {
    if (PH_cur > 13.75) {
      Distloccsh = 0.5 * DISTLOCCSH;
      Pdirectcsh = 0.001;
    } else if (PH_cur > 13.25) {
      Distloccsh = 0.75 * DISTLOCCSH;
      Pdirectcsh = 0.0005;
    } else if (PH_cur > 13.00) {
      Distloccsh = 0.85 * DISTLOCCSH;
      Pdirectcsh = 0.00025;
    }
  }

  if ((PHactive == 1) &&
      (Count[CSH] > ((Cshscale * (Surffract * Totfract) *
                      (Surffract * Totfract) / (Tfractw04) / (Tfractw04)) /
                     8.0))) {

    /***
     *    Calculate pH factor for each phase
     ***/

    for (k = C3S; k <= NSPHASES; k++) {

      if ((k != SFUME) && (k != AMSIL) && (k != ASG) && (k != CAS2)) {

        PHfactor[k] = PHcoeff[k][2] * pow(PH_cur, 2.0);
        PHfactor[k] += PHcoeff[k][1] * PH_cur;
        PHfactor[k] += PHcoeff[k][0];
        PHfactor[k] -= (PHsulfcoeff[k] * Concsulfate);

      } else {

        x = 0;
        y = 1;

        xv1 = FitpH[k][x][0];
        yv1 = FitpH[k][y][0];
        yv3 = FitpH[k][y][2];

        PHfactor[k] = PHcoeff[k][2] * pow(ohadj, 2.0);
        PHfactor[k] += PHcoeff[k][1] * ohadj;
        PHfactor[k] += PHcoeff[k][0];
        PHfactor[k] -= (PHsulfcoeff[k] * Concsulfate);

        if (PHfactor[k] < yv1 || ohadj < xv1)
          PHfactor[k] = yv1;
        if (PHfactor[k] > yv3)
          PHfactor[k] = yv3;

        /***
         *    Just for these fly ash phases, we adjust the
         *    PHfactor by the relative w/c ratio once again,
         *    to agree with experimental data, obtained by
         *    Feng and Garboczi, showing that the extent of
         *    reaction as a function of doh is basically
         *    independent of w/c
         ***/

        PHfactor[k] *= pow((0.50313 / W_to_c), 3.0);
      }
    }

    /* 2/02:  PHfactor = 0.30*(((14.1-PH_cur)/0.3)-1.0); */
    /* 3/02:  PHfactor = 0.60*(((14.1-PH_cur)/0.5)-1.0); */

    /***
     *    Molar volume of CSH depends on pH according to
     *    observations compiled in Jawed and Skalny,
     *    Cem. Concr. Res., Vol. 8 pp. 37-52 (1978).
     ***/

    Molarvcsh[Icyc] +=
        Molarvcshcoeff_pH * (PHfactor[C3S] + (PHsulfcoeff[C3S] * Concsulfate));
    Watercsh[Icyc] +=
        Watercshcoeff_pH * (PHfactor[C3S] + (PHsulfcoeff[C3S] * Concsulfate));
  }

  nhgd = 0;

  /* Update molar volume ratios for CSH formation */

  pc3scsh = (Molarvcsh[Cyccnt] / Molarv[C3S]) - 1.0;
  pc2scsh = (Molarvcsh[Cyccnt] / Molarv[C2S]) - 1.0;

  /* Once again, scan all pixels in microstructure */

  Slagemptyp = 0;

  /*
  Count[DIFFSO4] = Count[NA2SO4] = 0;
  for (k = 0; k < Zsyssize; k++) {
      for (j = 0; j < Ysyssize; j++) {
          for (iii = 0; i < Xsyssize; i++) {
              if (Mic[i][j][k] == (DIFFSO4)) Count[DIFFSO4]++;
              if (Mic[i][j][k] == (NA2SO4)) Count[NA2SO4]++;
          }
      }
  }

  if (Verbose) printf("\nEntering Main dissolve loop, Count[DIFFSO4] = %d,
  Count[NA2SO4] = %d ...\n",Count[DIFFSO4],Count[NA2SO4]); fflush(stdout);
  */

  for (zl = 0; zl < Zsyssize; zl++) {
    for (yl = 0; yl < Ysyssize; yl++) {
      for (xl = 0; xl < Xsyssize; xl++) {

        /***
         *    Work only with pixels that are marked for
         *     dissolution.  Convert them back to their
         *     original ID before doing anything else
         *
         *     Note that K2SO4 and NA2SO4 are handled
         *     differently below this loop (7 June 2004)
         ***/

        if (Mic[xl][yl][zl] > OFFSET &&
            (Mic[xl][yl][zl] - (OFFSET)) != (K2SO4) &&
            (Mic[xl][yl][zl] - (OFFSET)) != (NA2SO4)) {

          phid = (int)Mic[xl][yl][zl] - (OFFSET);
          if (phid == GYPSUM)
            gct++;

          /* Attempt a one-step random walk to dissolve */

          plnew = (int)((float)NEIGHBORS * ran1(Seed));
          if ((plnew < 0) || (plnew >= NEIGHBORS)) {
            plnew = NEIGHBORS - 1;
          }

          xc = xl + Xoff[plnew];
          yc = yl + Yoff[plnew];
          zc = zl + Zoff[plnew];

          xc += checkbc(xc, Xsyssize);
          yc += checkbc(yc, Ysyssize);
          zc += checkbc(zc, Zsyssize);

          pixdeact = 0;
          if ((Xoff[plnew] == (-1)) &&
              (Deactivated[xl][yl][zl] % Primevalues[1] == 0)) {

            pixdeact = 1;
          }

          if ((!pixdeact) && (Xoff[plnew] == 1) &&
              (Deactivated[xl][yl][zl] % Primevalues[0] == 0)) {

            pixdeact = 1;
          }

          if ((!pixdeact) && (Yoff[plnew] == (-1)) &&
              (Deactivated[xl][yl][zl] % Primevalues[3] == 0)) {

            pixdeact = 1;
          }

          if ((!pixdeact) && (Yoff[plnew] == 1) &&
              (Deactivated[xl][yl][zl] % Primevalues[2] == 0)) {

            pixdeact = 1;
          }

          if ((!pixdeact) && (Zoff[plnew] == (-1)) &&
              (Deactivated[xl][yl][zl] % Primevalues[5] == 0)) {

            pixdeact = 1;
          }

          if ((!pixdeact) && (Zoff[plnew] == 1) &&
              (Deactivated[xl][yl][zl] % Primevalues[4] == 0)) {

            pixdeact = 1;
          }

          /* Generate probability for dissolution */

          pdis = ran1(Seed);

          /***
           *    Bias dissolution for one pixel particles as
           *    indicated by a pixel value of zero in the
           *    particle microstructure image
           *
           *    We do allow dissolution of unhydrated material
           *    into water in saturated crack pores formed during
           *    the hydration process (24 May 2004)
           ***/

          if (((pdis <= (PHfactor[phid] * Disprob[phid])) ||
               ((pdis <=
                 (Onepixelbias[phid] * PHfactor[phid] * Disprob[phid])) &&
                (Micpart[xl][yl][zl] == 0))) &&
              (Mic[xc][yc][zc] == POROSITY || Mic[xc][yc][zc] == CRACKP) &&
              (!pixdeact)) {

            /***
             *    Special case of possible topochemical
             *    transformation of C3S to CSH without
             *    dissolution (NOT YET ENABLED, 24 April 2003)
             ***/

            /*
            if (Verbose) {
                if (phid == C3S) {
                    printf("\nDissolving C3S: pdis = %f\tdisprob = ",pdis);
                    if (Micpart[xl][yl][zl] == 0) {
                        printf("%f",Onepixelbias[phid] * PHfactor[phid] *
            Disprob[phid]); } else { printf("%f",PHfactor[phid] *
            Disprob[phid]);
                    }
                } else if (phid == C2S) {
                    printf("\nDissolving C2S: pdis = %f\tdisprob = ",pdis);
                    if (Micpart[xl][yl][zl] == 0) {
                        printf("%f",Onepixelbias[phid] * PHfactor[phid] *
            Disprob[phid]); } else { printf("%f",PHfactor[phid] *
            Disprob[phid]);
                    }
                } else if (phid == C3A) {
                    printf("\nDissolving C3A: pdis = %f\tdisprob = ",pdis);
                    if (Micpart[xl][yl][zl] == 0) {
                        printf("%f",Onepixelbias[phid] * PHfactor[phid] *
            Disprob[phid]); } else { printf("%f",PHfactor[phid] *
            Disprob[phid]);
                    }
                } else if (phid == C4AF) {
                    printf("\nDissolving C4AF: pdis = %f\tdisprob = ",pdis);
                    if (Micpart[xl][yl][zl] == 0) {
                        printf("%f",Onepixelbias[phid] * PHfactor[phid] *
            Disprob[phid]); } else { printf("%f",PHfactor[phid] *
            Disprob[phid]);
                    }
                } else if (phid == GYPSUM) {
                    printf("\nDissolving GYPSUM: pdis = %f\tdisprob = ",pdis);
                    if (Micpart[xl][yl][zl] == 0) {
                        printf("%f",Onepixelbias[phid] * PHfactor[phid] *
            Disprob[phid]); } else { printf("%f",PHfactor[phid] *
            Disprob[phid]);
                    }
                }
                fflush(stdout);
            }
            */

            Discount[phid]++;
            cread = Creates[phid];
            Count[phid]--;

            /***
             *     The space formerly occupied by the unhydrated pixel now
             *     becomes filled with whatever solvent was used to dissolve
             *     it (POROSITY or CRACKP) (24 May 2004)
             ***/

            sourcepore = Mic[xc][yc][zc];
            Mic[xl][yl][zl] = sourcepore;

            if (phid == C3AH6)
              nhgd++;

            /* Special dissolution for C4AF */

            if (phid == C4AF) {
              plfh3 = ran1(Seed);
              if ((plfh3 < 0.0) || (plfh3 > 1.0))
                plfh3 = 1.0;

              /***
               *    For every C4AF that dissolves, 0.5453
               *    diffusing FH3 species should be created
               ***/

              if (plfh3 <= 0.5453) {
                cread = DIFFFH3;
              }
            }

            if (cread == POROSITY) {

              /***
               *    Increment count of POROSITY or CRACKP, depending
               *    on which was used in the dissolution of the solid
               *    (24 May 2004)
               ***/

              Count[sourcepore]++;

            } else {
              Nmade++;
              Ngoing++;
              phnew = cread;
              Count[phnew]++;
              Mic[xc][yc][zc] = phnew;

              /* Add an ant for this diffusing pixel */

              antadd = (struct Ants *)malloc(Antsize);
              antadd->x = xc;
              antadd->y = yc;
              antadd->z = zc;
              antadd->id = phnew;
              antadd->cycbirth = Cyccnt;

              /***
               *    Connect this ant structure to end
               *    of linked list
               ***/

              antadd->prevant = Tailant;
              Tailant->nextant = antadd;
              antadd->nextant = NULL;
              Tailant = antadd;
            }

            /***
             *    Extra CSH diffusing species based
             *    on current temperature
             ***/

            if ((phid == C3S) || (phid == C2S)) {

              plfh3 = ran1(Seed);
              if (((phid == C2S) && (plfh3 <= pc2scsh)) || (plfh3 <= pc3scsh)) {

                placed = loccsh(xc, yc, zc, sourcepore);
                if (placed) {
                  Count[DIFFCSH]++;
                  Count[sourcepore]--;
                } else {
                  cshrand++;
                }
              }
            }

            if ((phid == C2S) && (pc2scsh > 1.0)) {
              plfh3 = ran1(Seed);
              if (plfh3 <= (pc2scsh - 1.0)) {
                placed = loccsh(xc, yc, zc, sourcepore);
                if (placed) {
                  Count[DIFFCSH]++;
                  Count[sourcepore]--;
                } else {
                  cshrand++;
                }
              }
            }

          } else {

            /***
             *    Pixel does NOT dissolve, just reset its phase
             *    ID back to its original value
             ***/

            Mic[xl][yl][zl] -= OFFSET;
          }

        } /* end of if edge block */

        /***
         *    Now check if CSH to pozzolanic CSH conversion is
         *    possible:
         *
         *        (1) Only if CH is less than 30% in volume,
         *        (2) Only if CSH is in contact with at
         *            least one porosity, AND
         *        (3) User wishes to implement this option
         ***/

        if (((Count[SFUME] + Count[AMSIL]) >= (0.013 * (double)(Syspix))) &&
            (Chnew < (0.30 * (double)(Syspix))) && (Csh2flag == 1)) {

          if (Mic[xl][yl][zl] == CSH) {
            if ((countbox(3, xl, yl, zl)) >= 1) {
              pconvert = ran1(Seed);
              if (pconvert < PCSH2CSH) {
                Count[CSH]--;
                plfh3 = ran1(Seed);

                /***
                 *    Molarvcsh units of C1.7SHx goes to
                 *    101.81 units of C1.1SH3.9 with 19.86
                 *    units of CH so p=calcy
                 ***/

                calcz = 0.0;
                cycnew = Cshage[xl][yl][zl];
                calcy = Molarv[POZZCSH] / Molarvcsh[cycnew];
                if (calcy > 1.0) {
                  calcz = calcy - 1.0;
                  calcy = 1.0;
                  if (Verbose) {
                    printf("WARNING:  Problem of not ");
                    printf("creating enough pozzolanic ");
                    printf("CSH during CSH conversion");
                    printf("\nCurrent binder temperature");
                    printf("is %f C\n", Temp_cur_b);
                  }
                }

                if (plfh3 <= calcy) {
                  Mic[xl][yl][zl] = POZZCSH;
                  Count[POZZCSH]++;
                } else {
                  Mic[xl][yl][zl] = DIFFCH;
                  Nmade++;
                  ncshgo++;
                  Ngoing++;
                  Count[DIFFCH]++;

                  /***
                   *    Allocate memory for the new
                   *    diffusing species in the linked list
                   ***/

                  antadd = (struct Ants *)malloc(Antsize);
                  antadd->x = xl;
                  antadd->y = yl;
                  antadd->z = zl;
                  antadd->id = DIFFCH;
                  antadd->cycbirth = Cyccnt;

                  /***
                   *    Now connect this ant structure
                   *    to end of linked list
                   ***/

                  antadd->prevant = Tailant;
                  Tailant->nextant = antadd;
                  antadd->nextant = NULL;
                  Tailant = antadd;
                }

                /***
                 *    Possibly need even more pozzolanic CSH
                 *
                 *    Would need a diffusing pozzolanic
                 *    CSH species???
                 ***/

                /*
                if (calcz > 0.0) {
                    plfh3 = ran1(Seed);
                    if (plfh3 <= calcz) {
                        cshrand++;
                    }
                }
                */

                plfh3 = ran1(Seed);
                calcx = (19.86 / Molarvcsh[cycnew]) - (1.0 - calcy);

                /* Ex. 0.12658=(19.86/108.)-(1.-0.94269) */

                if (plfh3 < calcx)
                  npchext++;
              }
            }
          }
        }

        /***
         *    See if slag can react --- must be
         *    in contact with at least one porosity pixel
         ***/

        if (Mic[xl][yl][zl] == SLAG) {

          if ((countbox(3, xl, yl, zl)) >= 1) {
            pconvert = ran1(Seed);
            if (pconvert < (PHfactor[SLAG] * Disprob[SLAG])) {

              Nslagr++;
              Count[SLAG]--;
              Discount[SLAG]++;

              /* Check on extra C3A generation */

              plfh3 = ran1(Seed);
              if (plfh3 < P5slag)
                nslagc3a++;

              /* Convert slag to reaction products */

              plfh3 = ran1(Seed);
              if (plfh3 < P1slag) {
                Mic[xl][yl][zl] = SLAGCSH;
                Count[SLAGCSH]++;
              } else {
                if (Sealed == 1) {

                  /* Create empty porosity at slag site */
                  Slagemptyp++;
                  Mic[xl][yl][zl] = EMPTYP;
                  Count[EMPTYP]++;
                } else {

                  /***
                   *    We do not distinguish between saturated
                   *    porosity and saturated crack porosity
                   *    here (24 May 2004)
                   ***/

                  Mic[xl][yl][zl] = POROSITY;
                  Count[POROSITY]++;
                }
              }

              /* Add in extra SLAGCSH as needed */

              p3init = P3slag;
              while (p3init > 1.0) {
                extslagcsh(xl, yl, zl);
                p3init -= 1.0;
              }

              plfh3 = ran1(Seed);
              if (plfh3 < p3init)
                extslagcsh(xl, yl, zl);
            }
          }
        }

      } /* end of zl loop */
    } /* end of yl loop */
  } /* end of xl loop */

  /*
  Count[DIFFSO4] = Count[NA2SO4] = 0;
  for (k = 0; k < Zsyssize; k++) {
      for (j = 0; j < Ysyssize; j++) {
          for (i = 0; i < Xsyssize; i++) {
              if (Mic[i][j][k] == (DIFFSO4)) Count[DIFFSO4]++;
              if (Mic[i][j][k] == (NA2SO4)) Count[NA2SO4]++;
          }
      }
  }

  if (Verbose) printf("\nLeaving Main dissolve loop, Count[DIFFSO4] = %d,
  Count[NA2SO4] = %d ...\n",Count[DIFFSO4],Count[NA2SO4]); fflush(stdout);
  */

  /***
   *    Next, dissolve the necessary number of sodium sulfate
   *    and potassium sulfate pixels.  nkspix and nnaspix are
   *    the total number of pixels of K2SO4 and NA2SO4 that
   *    need to be dissolved during this cycle
   *
   *    This is a dissolution proportional to the amount that
   *    pHpred function predicts should be dissolved of the
   *    the readily soluble species in the cement.
   *
   *    Eventually may want to make this microstructure based;
   *    that is, may want to treat NA2SO4 and K2SO4 like any other
   *    pixel that has a probability of dissolving, and then let
   *    the number dissolved be input to pHpred, rather than
   *    letting pHpred dictate the amount of pixels to be
   *    dissolved.  However, currently our measurements of
   *    total and readily soluble alkalies appear to be more
   *    accurate than the SEM/X-ray analysis measurements.
   *
   *    Note that currently the dissolution probability
   *    is unity.  That is, as soon as each eligible
   *    alkali sulfate is found, it dissolves.
   ***/

  /* Cumulative pixels of Pot. Sulf. that need to dissolve */
  nkspix = Ksulfinit * (Releasedk / (Totpotassium / MMK2O));
  /* Subtract from this the number dissolved in previous cycles */
  nkspix -= (Ksulfinit - Count[K2SO4]);

  /* Cumulative pixels of Sod. Sulf. that need to dissolve */
  nnaspix = Nasulfinit * (Releasedna / (Totsodium / MMNa2O));
  /* Subtract from this the number dissolved in previous cycles */
  nnaspix -= (Nasulfinit - Count[NA2SO4]);

  /*
  if (Verbose) {
        printf("\n***Ksulfinit = %d Count[K2SO4] = %d",Ksulfinit,Count[K2SO4]);
      printf("\n***Releasedk = %f Totpotassium = %f",Releasedk,Totpotassium);
      printf("\n***nkspix = %d",nkspix);
      printf("\n***Nasulfinit = %d Count[NA2SO4] =
  %d",Nasulfinit,Count[NA2SO4]); printf("\n***Releasedna = %f Totsodium =
  %f",Releasedna,Totsodium); printf("\n***nnaspix = %d",nnaspix);
      fflush(stdout);
  }
  */

  /***
   *    Determine number of potassium sulfates eligible
   *    for dissolution and put them in a linked list
   ***/

  totks = totnas = 0;
  if (Ksulfinit > 0 && Count[K2SO4] > 0) {

    /* delete the pot sulf linked list */

    while (Headks != Tailks) {
      if (Tailks->prevas == NULL) {
        Tailks = Headks;
      } else {
        Tailks = Tailks->prevas;
      }
    }

    Headks->prevas = NULL;
    Headks->nextas = NULL;
    Headks->x = 0;
    Headks->y = 0;
    Headks->z = 0;
  }

  if (Nasulfinit > 0 && Count[NA2SO4] > 0) {
    /* delete the sod sulf linked list */

    while (Headnas != Tailnas) {
      if (Tailnas->prevas == NULL) {
        Tailnas = Headnas;
      } else {
        Tailnas = Tailnas->prevas;
      }
    }

    Headnas->prevas = NULL;
    Headnas->nextas = NULL;
    Headnas->x = 0;
    Headnas->y = 0;
    Headnas->z = 0;
  }

  /*
  Count[DIFFSO4] = Count[NA2SO4] = 0;
  for (k = 0; k < Zsyssize; k++) {
      for (j = 0; j < Ysyssize; j++) {
          for (i = 0; i < Xsyssize; i++) {
              if (Mic[i][j][k] == (DIFFSO4)) Count[DIFFSO4]++;
              if (Mic[i][j][k] == (NA2SO4)) Count[NA2SO4]++;
          }
      }
  }

  if (Verbose) printf("\nEntering loop for ksulf list, Count[DIFFSO4] = %d,
  Count[NA2SO4] = %d ...\n",Count[DIFFSO4],Count[NA2SO4]);
  */

  /***
   *    This next line turns off dissolution of NA2SO4 and K2SO4 completely
   ***/

  nkspix = nnaspix = 0;

  /**************************/

  if (nkspix < Count[K2SO4] && nkspix > 0) {
    totks = 0;
    for (zl = 0; zl < Zsyssize; zl++) {
      for (yl = 0; yl < Ysyssize; yl++) {
        for (xl = 0; xl < Xsyssize; xl++) {
          if (Mic[xl][yl][zl] == ((int)(K2SO4) + (int)(OFFSET))) {

            /***
             *    Uncomment above and comment below to query
             *    only SURFACE pixels of K2SO4
             ***/

            /*
            if (Mic[xl][yl][zl] == ((int)(K2SO4)))
            */
            totks++;
            curas = (struct Alksulf *)malloc(Alksulfsize);
            curas->x = xl;
            curas->y = yl;
            curas->z = zl;

            /***
             *    Now connect this node to
             *    end of linked list
             ***/

            curas->prevas = Tailks;
            Tailks->nextas = curas;
            curas->nextas = NULL;
            Tailks = curas;
          }
        }
      }
    }
  } else if (nkspix > 0) {

    /* Dissolve all the K2SO4 pixels in this cycle */

    for (zl = 0; zl < Zsyssize; zl++) {
      for (yl = 0; yl < Ysyssize; yl++) {
        for (xl = 0; xl < Xsyssize; xl++) {
          if (Mic[xl][yl][zl] == (K2SO4)) {
            Mic[xl][yl][zl] = POROSITY;
            Discount[K2SO4]++;
            Count[K2SO4]--;
            nkspix--;
          }
        }
      }
    }

    totks = 0;
  }

  /*
  Count[DIFFSO4] = Count[NA2SO4] = 0;
  for (k = 0; k < Zsyssize; k++) {
      for (j = 0; j < Ysyssize; j++) {
          for (i = 0; i < Xsyssize; i++) {
              if (Mic[i][j][k] == (DIFFSO4)) Count[DIFFSO4]++;
              if (Mic[i][j][k] == (NA2SO4)) Count[NA2SO4]++;
          }
      }
  }

  if (Verbose) printf("\nEntering loop for nasulf list, Count[DIFFSO4] = %d,
  Count[NA2SO4] = %d ...\n",Count[DIFFSO4],Count[NA2SO4]);
  */

  if (nnaspix < Count[NA2SO4] && nnaspix > 0) {
    totnas = 0;
    for (zl = 0; zl < Zsyssize; zl++) {
      for (yl = 0; yl < Ysyssize; yl++) {
        for (xl = 0; xl < Xsyssize; xl++) {
          if (Mic[xl][yl][zl] == ((int)(NA2SO4) + (int)(OFFSET))) {

            /***
             *    Uncomment above and comment below to query
             *    only SURFACE pixels of NA2SO4
             ***/

            /*
            if (Mic[xl][yl][zl] == ((int)(NA2SO4)))
            */
            totnas++;
            curas = (struct Alksulf *)malloc(Alksulfsize);
            curas->x = xl;
            curas->y = yl;
            curas->z = zl;

            /***
             *    Now connect this node to
             *    end of linked list
             ***/

            curas->prevas = Tailnas;
            Tailnas->nextas = curas;
            curas->nextas = NULL;
            Tailnas = curas;
          }
        }
      }
    }
  } else if (nnaspix > 0) {

    /* Dissolve all NA2SO4 pixels in this cycle */

    for (zl = 0; zl < Zsyssize; zl++) {
      for (yl = 0; yl < Ysyssize; yl++) {
        for (xl = 0; xl < Xsyssize; xl++) {
          if (Mic[xl][yl][zl] == (NA2SO4)) {
            Mic[xl][yl][zl] = POROSITY;
            Discount[NA2SO4]++;
            Count[NA2SO4]--;
            nnaspix--;
          }
        }
      }
    }
    totnas = 0;
  }

  /*
  Count[DIFFSO4] = Count[NA2SO4] = 0;
  for (k = 0; k < Zsyssize; k++) {
      for (j = 0; j < Ysyssize; j++) {
          for (i = 0; i < Xsyssize; i++) {
              if (Mic[i][j][k] == (DIFFSO4)) Count[DIFFSO4]++;
              if (Mic[i][j][k] == (NA2SO4)) Count[NA2SO4]++;
          }
      }
  }

  if (Verbose) printf("\nLeaving loop for nasulf list, Count[DIFFSO4] = %d,
  Count[NA2SO4] = %d ...\n",Count[DIFFSO4],Count[NA2SO4]);
  */

  /***
   *    Linked lists are established, now process
   ***/

  /*
  if (Verbose) printf("\ntotks = %d",totks);
  */
  while (nkspix > 0 && totks > 0) {
    skipnodes = (int)((float)totks * ran1(Seed));
    curas = Headks;
    for (i = 0; i < skipnodes; i++) {
      curas = curas->nextas;
    }

    /***
     *    Now we are positioned randomly within the list
     *    Remove this element from the list
     ***/

    curx = curas->x;
    cury = curas->y;
    curz = curas->z;

    if (curas->prevas == NULL) {
      Headks = curas->nextas;
    } else {
      curas->prevas->nextas = curas->nextas;
    }

    if (curas->nextas == NULL) {
      Tailks = curas->prevas;
    } else {
      curas->nextas->prevas = curas->prevas;
    }

    Mic[curx][cury][curz] = POROSITY;
    Discount[K2SO4]++;
    Count[K2SO4]--;
    nkspix--;
    totks--;

    /***
     *    Now look for other soluble K2SO4 that may have been
     *    uncovered by this dissolution event
     ***/

    for (i = 0; i < 6; i++) {
      xl = curx;
      yl = cury;
      zl = curz;
      switch (i) {
      case 0:
        xl++;
        xl += checkbc(xl, Xsyssize);
        break;
      case 1:
        xl--;
        xl += checkbc(xl, Xsyssize);
        break;
      case 2:
        yl++;
        yl += checkbc(yl, Ysyssize);
        break;
      case 3:
        yl--;
        yl += checkbc(yl, Ysyssize);
        break;
      case 4:
        zl++;
        zl += checkbc(zl, Zsyssize);
        break;
      case 5:
        zl--;
        zl += checkbc(zl, Zsyssize);
        break;
      }

      if (Mic[xl][yl][zl] == (int)(K2SO4)) {

        /* add to end of linked list */

        totks++;
        Mic[xl][yl][zl] += (OFFSET);
        curas = (struct Alksulf *)malloc(Alksulfsize);
        curas->x = xl;
        curas->y = yl;
        curas->z = zl;

        /***
         *    Now connect this node to
         *    end of linked list
         ***/

        curas->prevas = Tailks;
        Tailks->nextas = curas;
        curas->nextas = NULL;
        Tailks = curas;
      }
    }
  }

  /*
  Count[DIFFSO4] = Count[NA2SO4] = 0;
  for (k = 0; k < Zsyssize; k++) {
      for (j = 0; j < Ysyssize; j++) {
          for (i = 0; i < Xsyssize; i++) {
              if (Mic[i][j][k] == (DIFFSO4)) Count[DIFFSO4]++;
              if (Mic[i][j][k] == (NA2SO4)) Count[NA2SO4]++;
          }
      }
  }

  if (Verbose) printf("\nFinished processing ksulf list, Count[DIFFSO4] = %d,
  Count[NA2SO4] = %d ...\n",Count[DIFFSO4],Count[NA2SO4]);
  */

  /***
   *    Now go through remainder of linked list and
   *    reset the phase ids
   ***/

  if (Headnas != Tailnas) {
    curas = Headks;
    while (curas != NULL) {
      curx = curas->x;
      cury = curas->y;
      curz = curas->z;
      Mic[curx][cury][curz] = (K2SO4);
      curas = curas->nextas;
    }
  }

  /*
  if (Verbose) printf("\nFinished processing ksulf ants, step 2, in
  dissolve...\nnnaspix = %d, totnas = %d\n",nnaspix,totnas);
  */

  while (nnaspix > 0 && totnas > 0) {
    skipnodes = (int)((float)totnas * ran1(Seed));
    curas = Headnas;
    for (i = 0; i < skipnodes; i++) {
      curas = curas->nextas;
    }

    /***
     *    Now we are positioned randomly within the list
     *    Remove this element from the list
     ***/

    curx = curas->x;
    cury = curas->y;
    curz = curas->z;

    if (curas->prevas == NULL) {
      Headnas = curas->nextas;
    } else {
      curas->prevas->nextas = curas->nextas;
    }

    if (curas->nextas == NULL) {
      Tailnas = curas->prevas;
    } else {
      curas->nextas->prevas = curas->prevas;
    }

    Mic[curx][cury][curz] = POROSITY;
    Discount[NA2SO4]++;
    Count[NA2SO4]--;
    nnaspix--;
    totnas--;

    /***
     *    Now look for other soluble NA2SO4 that may have been
     *    uncovered by this dissolution event
     ***/

    for (i = 0; i < 6; i++) {
      xl = curx;
      yl = cury;
      zl = curz;
      switch (i) {
      case 0:
        xl++;
        xl += checkbc(xl, Xsyssize);
        break;
      case 1:
        xl--;
        xl += checkbc(xl, Xsyssize);
        break;
      case 2:
        yl++;
        yl += checkbc(yl, Ysyssize);
        break;
      case 3:
        yl--;
        yl += checkbc(yl, Ysyssize);
        break;
      case 4:
        zl++;
        zl += checkbc(zl, Zsyssize);
        break;
      case 5:
        zl--;
        zl += checkbc(zl, Zsyssize);
        break;
      }

      if (Mic[xl][yl][zl] == (int)(NA2SO4)) {

        /* add to end of linked list */

        totnas++;
        Mic[xl][yl][zl] += (OFFSET);
        curas = (struct Alksulf *)malloc(Alksulfsize);
        curas->x = xl;
        curas->y = yl;
        curas->z = zl;

        /***
         *    Now connect this node to
         *    end of linked list
         ***/

        curas->prevas = Tailnas;
        Tailnas->nextas = curas;
        curas->nextas = NULL;
        Tailnas = curas;
      }
    }
  }

  /*
  Count[DIFFSO4] = Count[NA2SO4] = 0;
  for (k = 0; k < Zsyssize; k++) {
      for (j = 0; j < Ysyssize; j++) {
          for (i = 0; i < Xsyssize; i++) {
              if (Mic[i][j][k] == (DIFFSO4)) Count[DIFFSO4]++;
              if (Mic[i][j][k] == (NA2SO4)) Count[NA2SO4]++;
          }
      }
  }

  if (Verbose) printf("\nFinished processing nasulf list, Count[DIFFSO4] = %d,
  Count[NA2SO4] = %d ...\n",Count[DIFFSO4],Count[NA2SO4]);
  */

  /***
   *    Now go through remainder of linked list and
   *    reset the phase ids
   ***/

  if (Headnas != Tailnas) {
    curas = Headnas;
    while (curas != NULL) {
      curx = curas->x;
      cury = curas->y;
      curz = curas->z;
      Mic[curx][cury][curz] = (NA2SO4);
      curas = curas->nextas;
    }
  }

  /*
  Count[DIFFSO4] = Count[NA2SO4] = 0;
  for (k = 0; k < Zsyssize; k++) {
      for (j = 0; j < Ysyssize; j++) {
          for (i = 0; i < Xsyssize; i++) {
              if (Mic[i][j][k] == (DIFFSO4)) Count[DIFFSO4]++;
              if (Mic[i][j][k] == (NA2SO4)) Count[NA2SO4]++;
          }
      }
  }

  if (Verbose) {
      printf("\nFinished resetting nasulf ids, Count[DIFFSO4] = %d,
  Count[NA2SO4] = %d ...\n",Count[DIFFSO4],Count[NA2SO4]); printf("\nEligible
  gypsum count = %d\n",gct);
  }
  */

  if ((ncshgo != 0) && (Verbose == 1))
    printf("CSH dissolved is %d \n", ncshgo);

  if ((npchext > 0) && (Verbose == 1))
    printf("Extra CH required is %d at cycle %d \n", npchext, cycle);

  /***
   *    Now add in the extra diffusing species for dissolution
   *
   *    Expansion factors from Young and Hansen and Mindess and
   *    Young (Concrete)
   ***/

  ncshext = cshrand;
  if ((cshrand != 0) && (Verbose == 1))
    printf("cshrand is %d \n", cshrand);

  /***
   *    Extra diffusing CH, Gypsum, C3A, and SO4 are added at totally random
   *    locations, rather than at the dissolution site
   ***/

  fchext = (0.61 * (double)Discount[C3S]) + (0.191 * (double)Discount[C2S]) +
           (0.2584 * (double)Discount[C4AF]) +
           (0.954 * (double)Discount[FREELIME]);

  nchext = fchext;
  if (fchext > (double)nchext) {
    pdis = ran1(Seed);
    if ((fchext - (double)nchext) > pdis)
      nchext++;
  }

  nchext += npchext;

  /***
   *    Adjust CH addition for slag consumption and
   *    nucleation of secondary gypsum from dissolved
   *    alkali sulfates (8 June 2004)
   ***/

  Slagcum += Discount[SLAG];
  Chgone = (int)(P4slag * (float)Slagcum);
  Slagcum -= (int)((float)Chgone / P4slag);
  savechgone = Chgone;
  Chgone = 0;
  sulfavemolarv = (float)(Discount[K2SO4]) * Molarv[K2SO4];
  sulfavemolarv += (float)(Discount[NA2SO4]) * Molarv[NA2SO4];
  if (sulfavemolarv > 0.0) {
    sulfavemolarv /= ((float)(Discount[K2SO4] + Discount[NA2SO4]));
    Chgone = (int)((float)(Nucsulf2gyps)*Molarv[CH] / sulfavemolarv);
    Nucsulf2gyps -= (int)(((float)Chgone) * sulfavemolarv / Molarv[CH]);
  }
  Chgone += savechgone;
  nchext -= Chgone;
  nchext -= DIFFCHdeficit;
  DIFFCHdeficit = 0;

  if (nchext < 0) {
    DIFFCHdeficit -= nchext;
    nchext = 0;
  }

  fc3aext = (double)Discount[C3A] + (double)Discount[OC3A];
  fc3aext += (0.5917 * (double)Discount[C3AH6]);
  nc3aext = fc3aext + nslagc3a;
  if (fc3aext > (double)nc3aext) {
    pdis = ran1(Seed);
    if ((fc3aext - (double)nc3aext) > pdis)
      nc3aext++;
  }

  fc4aext = 0.696 * (double)Discount[C4AF];
  nc4aext = fc4aext;
  if (fc4aext > (double)nc4aext) {
    pdis = ran1(Seed);
    if ((fc4aext - (double)nc4aext) > pdis)
      nc4aext++;
  }

  /* Both forms of GYPSUM form same DIFFGYP species */

  ngypext = Discount[GYPSUM] + Discount[GYPSUMS];

  /***
   *    Convert to diffusing anhydrite at volume
   *    necessary for final gypsum formation
   *
   *    (1 anhydrite --> 1.423 gypsum)
   *
   *    Since hemihydrate can now react with C3A, etc.,
   *    can't do expansion here any longer  7/99
   ***/

  /*    fanhext = 1.423 * (float)Discount[ANHYDRITE]; */

  fanhext = (double)Discount[ANHYDRITE];
  nanhext = fanhext;
  if (fanhext > (double)nanhext) {
    pdis = ran1(Seed);
    if ((fanhext - (double)nanhext) > pdis)
      nanhext++;
  }

  /***
   *    Convert to diffusing hemiydrate at volume necessary
   *    for final gypsum formation
   *
   *    (1 hemihydrate --> 1.4 gypsum)
   *
   *    Since hemihydrate can now react with C3A, etc.,
   *    can't do expansion here any longer  7/99
   ***/

  /*    fhemext=1.3955*(float)Discount[HEMIHYD];  */

  fhemext = (double)Discount[HEMIHYD];

  nhemext = fhemext;
  if (fhemext > (double)nhemext) {
    pdis = ran1(Seed);
    if ((fhemext - (double)nhemext) > pdis)
      nhemext++;
  }

  /*
  Count[DIFFSO4] = Count[NA2SO4] = 0;
  for (k = 0; k < Zsyssize; k++) {
      for (j = 0; j < Ysyssize; j++) {
          for (i = 0; i < Xsyssize; i++) {
              if (Mic[i][j][k] == (DIFFSO4)) Count[DIFFSO4]++;
              if (Mic[i][j][k] == (NA2SO4)) Count[NA2SO4]++;
          }
      }
  }

  if (Verbose) printf("\nGetting ready to add DIFFSO4, Count[DIFFSO4] = %d,
  Count[NA2SO4] = %d ...\n",Count[DIFFSO4],Count[NA2SO4]);
  */

  nso4ext = (Discount[K2SO4] + Discount[NA2SO4]);
  Count[DIFFGYP] += ngypext;
  Count[DIFFANH] += nanhext;
  Count[DIFFHEM] += nhemext;
  Count[DIFFCH] += nchext;
  Count[DIFFCSH] += ncshext;
  Count[DIFFC3A] += nc3aext;
  Count[DIFFC4A] += nc4aext;
  Count[DIFFSO4] += nso4ext;

  nsum2 = nchext + ncshext;
  nsum3 = nsum2 + nc3aext;
  nsum4 = nsum3 + nc4aext;
  nsum5 = nsum4 + ngypext;
  nsum6 = nsum5 + nhemext;
  nsum7 = nsum6 + nanhext;
  nsum8 = nsum7 + nso4ext;

  for (xext = 1; xext <= nsum8; xext++) {
    plok = 0;
    do {
      xc = (int)((float)Xsyssize * ran1(Seed));
      yc = (int)((float)Ysyssize * ran1(Seed));
      zc = (int)((float)Zsyssize * ran1(Seed));
      if (xc >= Xsyssize)
        xc = 0;
      if (yc >= Ysyssize)
        yc = 0;
      if (zc >= Zsyssize)
        zc = 0;

      if (Mic[xc][yc][zc] == POROSITY) {
        plok = 1;
        phid = DIFFCH;
        Count[POROSITY]--;

        if (xext > nsum7) {
          phid = DIFFSO4;
        } else if (xext > nsum6) {
          phid = DIFFANH;
        } else if (xext > nsum5) {
          phid = DIFFHEM;
        } else if (xext > nsum4) {
          phid = DIFFGYP;
        } else if (xext > nsum3) {
          phid = DIFFC4A;
        } else if (xext > nsum2) {
          phid = DIFFC3A;
        } else if (xext > nchext) {
          phid = DIFFCSH;
        }

        Mic[xc][yc][zc] = phid;
        Nmade++;
        Ngoing++;

        /***
         *    Allocate memory for this diffusing
         *    element in the doubly linked list
         ***/

        antadd = (struct Ants *)malloc(Antsize);
        antadd->x = xc;
        antadd->y = yc;
        antadd->z = zc;
        antadd->id = phid;
        antadd->cycbirth = Cyccnt;

        /***
         *    Now connect this ant structure to end
         *    of linked list
         ***/

        antadd->prevant = Tailant;
        Tailant->nextant = antadd;
        antadd->nextant = NULL;
        Tailant = antadd;
      }

    } while (!plok);

  } /* end of xext for extra species generation */

  /* Check that this worked out correctly */

  Count[DIFFSO4] = Count[NA2SO4] = 0;
  /*
  for (k = 0; k < Zsyssize; k++) {
      for (j = 0; j < Ysyssize; j++) {
          for (i = 0; i < Xsyssize; i++) {
              if (Mic[i][j][k] == (DIFFSO4)) Count[DIFFSO4]++;
              if (Mic[i][j][k] == (NA2SO4)) Count[NA2SO4]++;
          }
      }
  }

  if (Verbose) printf("\nFinished adding DIFFSO4, Count[DIFFSO4] = %d,
  Count[NA2SO4] = %d ...\n",Count[DIFFSO4],Count[NA2SO4]);
  */

  if (Verbose) {
    printf("Dissolved- %d %d %d %d %d %d %d %d %d %d %d %d %d %d\n",
           Count[DIFFCSH], Count[DIFFCH], Count[DIFFGYP], Count[DIFFC3A],
           Count[DIFFFH3], Count[DIFFETTR], Count[DIFFAS], Count[DIFFCAS2],
           Count[DIFFCACL2], Count[DIFFCACO3], Count[DIFFGYP], Count[DIFFHEM],
           Count[DIFFANH], Count[DIFFSO4]);
  }

  /***
   *    Measure of sulfate anions in solution, so add in DIFFSO4 species
   *    created by dissolution of alkali sulfates (7 June 2004)
   ***/

  Sulf_cur = Count[DIFFGYP] + Count[DIFFANH] + Count[DIFFHEM] + Count[DIFFSO4];

  /* If too many diffusing gypsums already in solution... */

  if (Sulf_cur > Dgypmax) {
    Disprob[GYPSUM] = 0.0;
    Disprob[ANHYDRITE] = 0.0;
    Disprob[HEMIHYD] = 0.0;
    Disprob[GYPSUMS] = 0.0;
  } else {
    Disprob[GYPSUM] = Disbase[GYPSUM];
    Disprob[ANHYDRITE] = Disbase[ANHYDRITE];
    Disprob[HEMIHYD] = Disbase[HEMIHYD];
    Disprob[GYPSUMS] = Disbase[GYPSUMS];
  }

  Count[DIFFSO4] = Count[NA2SO4] = 0;
  /*
  for (k = 0; k < Zsyssize; k++) {
      for (j = 0; j < Ysyssize; j++) {
          for (i = 0; i < Xsyssize; i++) {
              if (Mic[i][j][k] == (DIFFSO4)) Count[DIFFSO4]++;
              if (Mic[i][j][k] == (NA2SO4)) Count[NA2SO4]++;
          }
      }
  }

  if (Verbose) {
      printf("\nEnd of dissolve cycle, Count[DIFFSO4] = %d, Count[NA2SO4] = %d
  ...\n",Count[DIFFSO4],Count[NA2SO4]); printf("C3AH6 dissolved- %d with prob.
  of %f \n",nhgd,Disprob[C3AH6]);
  }
  */
}

/***
 *    addrand
 *
 *     Add nneed one-pixel elements of phase randid at random
 *     locations in the microstructure
 *
 *     Arguments:    int phase id
 *                 int number to place
 *                 int flocculate (1) or not (0)
 *
 *     Returns:    nothing
 *
 *    Calls:        no other routines
 *    Called by:    main program
 ***/
void addrand(int randid, int nneed, int onepixfloc) {
  int success, ix, iy, iz, inc, dim, dir, newsite, oldval;
  int ic;
  float pc3a;

  /***
   *    Add number of requested phase pixels at
   *    random pore locations
   ***/

  for (ic = 1; ic <= nneed; ic++) {
    success = 0;

    while (!success) {

      ix = (int)((float)Xsyssize * ran1(Seed));
      iy = (int)((float)Ysyssize * ran1(Seed));
      iz = (int)((float)Zsyssize * ran1(Seed));

      if (ix == Xsyssize)
        ix = 0;
      if (iy == Ysyssize)
        iy = 0;
      if (iz == Zsyssize)
        iz = 0;

      if (Mic[ix][iy][iz] == POROSITY || Mic[ix][iy][iz] == CRACKP) {
        oldval = Mic[ix][iy][iz];
        Mic[ix][iy][iz] = randid;
        Micorig[ix][iy][iz] = randid;
        if (randid == C3A) {
          pc3a = ran1(Seed);
          if (pc3a < Oc3afrac) {
            Mic[ix][iy][iz] = OC3A;
            Micorig[ix][iy][iz] = OC3A;
          }
        }
        success = 1;
        if (onepixfloc == 1) {
          /***
           * Flocculate this particle to a nearby surface
           * Pic a random direction to fly
           ***/
          dim = (int)(3.0 * ran1(Seed));
          dir = (int)(2.0 * ran1(Seed));
          inc = (dir == 0) ? 1 : -1;

          switch (dim) {
          case 0: /* X-direction flight */
            newsite = ix + inc;
            newsite += checkbc(newsite, Xsyssize);
            while ((newsite != ix) && ((Mic[newsite][iy][iz] == POROSITY) ||
                                       (Mic[newsite][iy][iz] == CRACKP))) {
              newsite += inc;
              newsite += checkbc(newsite, Xsyssize);
            }
            if (newsite != ix) {
              newsite -= inc;
              newsite += checkbc(newsite, Xsyssize);
              Mic[newsite][iy][iz] = Mic[ix][iy][iz];
              Micorig[newsite][iy][iz] = Micorig[ix][iy][iz];
              Mic[ix][iy][iz] = oldval;
              Micorig[ix][iy][iz] = oldval;
            }
            break;
          case 1: /* Y-direction flight */
            newsite = iy + inc;
            newsite += checkbc(newsite, Ysyssize);
            while ((newsite != iy) && ((Mic[ix][newsite][iz] == POROSITY) ||
                                       (Mic[ix][newsite][iz] == CRACKP))) {
              newsite += inc;
              newsite += checkbc(newsite, Ysyssize);
            }
            if (newsite != iy) {
              newsite -= inc;
              newsite += checkbc(newsite, Ysyssize);
              Mic[ix][newsite][iz] = Mic[ix][iy][iz];
              Micorig[ix][newsite][iz] = Micorig[ix][iy][iz];
              Mic[ix][iy][iz] = oldval;
              Micorig[ix][iy][iz] = oldval;
            }
            break;
          case 2: /* Z-direction flight */
            newsite = iz + inc;
            newsite += checkbc(newsite, Zsyssize);
            while ((newsite != iz) && ((Mic[ix][iy][newsite] == POROSITY) ||
                                       (Mic[ix][iy][newsite] == CRACKP))) {
              newsite += inc;
              newsite += checkbc(newsite, Zsyssize);
            }
            if (newsite != iz) {
              newsite -= inc;
              newsite += checkbc(newsite, Zsyssize);
              Mic[ix][iy][newsite] = Mic[ix][iy][iz];
              Micorig[ix][iy][newsite] = Micorig[ix][iy][iz];
              Mic[ix][iy][iz] = oldval;
              Micorig[ix][iy][iz] = oldval;
            }
            break;
          case 3: /* Do nothing */
            break;
          }
        }
      }
    }
  }
}

/***
 *    addseeds
 *
 *     Displace one half of the microstructure a set number
 *     of pixels, leaving a crack-like strip down the
 *     center of the image
 *
 *     Arguments:  Phase id of seeds to add
 *                 Probability of a pore pixel converting to a seed
 *
 *     Returns:    nothing
 *
 *    Calls:        no other routines
 *    Called by:    main program
 ***/
void addseeds(int phid, float prob) {
  register int i, j, k;
  float pcomp;

  if (prob > 1.0e-10) {
    for (k = 0; k < Zsyssize; k++) {
      for (j = 0; j < Ysyssize; j++) {
        for (i = 0; i < Xsyssize; i++) {
          if (Mic[i][j][k] == POROSITY) {
            pcomp = ran1(Seed);
            if (pcomp < prob)
              Mic[i][j][k] = phid;
          }
        }
      }
    }
  }

  return;
}

/***
 *    addcrack
 *
 *     Displace one half of the microstructure a set number
 *     of pixels, leaving a crack-like strip down the
 *     center of the image
 *
 *     Arguments:    None
 *
 *     Returns:    nothing
 *
 *    Calls:        no other routines
 *    Called by:    main program
 ***/
void addcrack(void) {
  register int i, j, k;
  int start;
  struct Ants *ant;

  ant = Headant;

  /***
   *    Two tasks must be performed here.  First of all,
   *    we must displace all the actual pixels.  Then we must
   *    update the positions of all the diffusing species
   *
   *    All crack space is added as phase CRACKP instead of
   *    as simply saturated porosity, to allow differentiation
   *    in the way global properties, like maximum number
   *    of diffusing species, are computed.
   *
   *    (24 May 2004)
   ***/

  switch (Crackorient) {

  case 1: /* Crack in x direction (yz plane) */

    if (Verbose)
      printf("\n\t\tCracking in yz plane...");

    start = (Xsyssize / 2) - 1;

    for (i = Xsyssize - 1; i > start; i--) {
      for (j = 0; j < Ysyssize; j++) {
        for (k = 0; k < Zsyssize; k++) {
          Mic[i + Crackwidth][j][k] = Mic[i][j][k];
          Micpart[i + Crackwidth][j][k] = Micpart[i][j][k];
          Cshage[i + Crackwidth][j][k] = Cshage[i][j][k];
          Deactivated[i + Crackwidth][j][k] = Deactivated[i][j][k];

          if (i <= start + Crackwidth) {
            Mic[i][j][k] = CRACKP;
            Count[CRACKP]++;
            Micpart[i][j][k] = 0;
            Cshage[i][j][k] = 0;
            Deactivated[i][j][k] = 1;
          }
        }
      }
    }

    /***
     *    Microstructure is displaced, now move all the ants
     ***/

    while (ant != NULL) {
      if (ant->x > start)
        ant->x += Crackwidth;
      ant = ant->nextant;
    }

    /*** Finally, change the x dimension ***/

    Xsyssize += Crackwidth;

    break;

  case 2: /* Crack in y direction (xz plane) */

    if (Verbose)
      printf("\n\t\tCracking in xz plane...");

    start = (Ysyssize / 2) - 1;

    for (j = Ysyssize - 1; j > start; j--) {
      for (i = 0; i < Xsyssize; i++) {
        for (k = 0; k < Zsyssize; k++) {
          Mic[i][j + Crackwidth][k] = Mic[i][j][k];
          Micpart[i][j + Crackwidth][k] = Micpart[i][j][k];
          Cshage[i][j + Crackwidth][k] = Cshage[i][j][k];
          Deactivated[i][j + Crackwidth][k] = Deactivated[i][j][k];

          if (j <= start + Crackwidth) {
            Mic[i][j][k] = CRACKP;
            Count[CRACKP]++;
            Micpart[i][j][k] = 0;
            Cshage[i][j][k] = 0;
            Deactivated[i][j][k] = 1;
          }
        }
      }
    }

    /***
     *    Microstructure is displaced, now move all the ants
     ***/

    if (Verbose) {
      printf("\n\t\t\tPreparing to move ants now ...");
      fflush(stdout);
    }
    while (ant != NULL) {
      if (ant->y > start)
        ant->y += Crackwidth;
      ant = ant->nextant;
    }
    if (Verbose) {
      printf(" done");
      fflush(stdout);
    }

    /*** Finally, change the y dimension ***/

    Ysyssize += Crackwidth;

    break;

  case 3: /* Crack in z direction (xy plane) */

    if (Verbose)
      printf("\n\t\tCracking in xy plane...");

    start = (Zsyssize / 2) - 1;

    for (k = Zsyssize - 1; k > start; k--) {
      for (i = 0; i < Xsyssize; i++) {
        for (j = 0; j < Ysyssize; j++) {
          Mic[i][j][k + Crackwidth] = Mic[i][j][k];
          Micpart[i][j][k + Crackwidth] = Micpart[i][j][k];
          Cshage[i][j][k + Crackwidth] = Cshage[i][j][k];
          Deactivated[i][j][k + Crackwidth] = Deactivated[i][j][k];

          if (k <= start + Crackwidth) {
            Mic[i][j][k] = CRACKP;
            Count[CRACKP]++;
            Micpart[i][j][k] = 0;
            Cshage[i][j][k] = 0;
            Deactivated[i][j][k] = 1;
          }
        }
      }
    }

    /***
     *    Microstructure is displaced, now move all the ants
     ***/

    while (ant != NULL) {
      if (ant->z > start)
        ant->z += Crackwidth;
      ant = ant->nextant;
    }

    /*** Finally, change the z dimension ***/

    Zsyssize += Crackwidth;
    break;

  default:
    break;
  }

  return;
}

/***
 *    calcT
 *
 *     Calculate temperature of binder and aggregate
 *
 *     Arguments:    double mass of solid
 *
 *     Returns:    nothing
 *
 *    Calls:        no other routines
 *    Called by:    main program
 ***/
void calcT(double mass) {
  float dg = Heat_cf * (Heat_new - Heat_old);
  float dTb, dTbam, dTagg, fact, dampen, Tao, Tbo;

  Tbo = Temp_cur_b;
  Tao = Temp_cur_agg;
  dTb = dTagg = 0.0;
  dampen = 1.0;
  fact = 1.0;

  if (AggTempEffect == 1) {
    if ((mass * Cp_b) > (Mass_agg * Cp_agg)) {
      do {
        fact = dampen * Time_step * U_coeff_agg / (Mass_agg * Cp_agg);
        dTagg = -(Tao - Tbo) * fact;
        dTb = -(Mass_agg * Cp_agg * dTagg) / (mass * Cp_b);
        dampen *= 0.75;
      } while ((Tao - Tbo) * ((Tao + dTagg) - (Tbo + dTb)) < 0.0);
    } else {
      do {
        fact = dampen * Time_step * U_coeff_agg / (mass * Cp_b);
        dTb = -(Tbo - Tao) * fact;
        dTagg = -(mass * Cp_b * dTb) / (Mass_agg * Cp_agg);
        dampen *= 0.75;
      } while ((Tao - Tbo) * ((Tao + dTagg) - (Tbo + dTb)) < 0.0);
    }

    Temp_cur_b += (dTb + (mass * dg / Cp_b));
    dTbam = -((Temp_cur_b - T_ambient) * Time_step * U_coeff / Cp_b);
    if (fabs(dTbam) >= fabs(Temp_cur_b - T_ambient)) {
      Temp_cur_b = T_ambient;
    } else {
      Temp_cur_b += dTbam;
    }
    Temp_cur_agg += dTagg;
    Temp_0 = Temp_cur_b;
    Temp_0_agg = Temp_cur_agg;
    if (fabs(Temp_0 - Temp_0_agg) <= 0.5)
      AggTempEffect = 0;

  } else {
    Temp_cur_b += (dTb + (mass * dg / Cp_b));
    dTbam = -((Temp_cur_b - T_ambient) * Time_step * U_coeff / Cp_b);
    if (fabs(dTbam) >= fabs(Temp_cur_b - T_ambient)) {
      Temp_cur_b = T_ambient;
    } else {
      Temp_cur_b += dTbam;
    }
    Temp_0 = Temp_0_agg = Temp_cur_agg = Temp_cur_b;
  }

  /*
      printf("\nIN CALCT:  AggTempEffect = %d",AggTempEffect);
      printf("\n\tMass = %f\tMass_agg = %f\n\tCp_b = %f\tCp_agg =
     %f",mass,Mass_agg,Cp_b,Cp_agg); printf("\n\tTbo = %f\tTao = %f\n\tdtime =
     %f\tfact = %f",Tbo,Tao,Time_step,fact); printf("\n\tdg = %f\tdTagg =
     %f\tdTb = %f",dg,dTagg,dTb); printf("\n\tTemp_cur_b = %f\tTemp_cur_agg =
     %f",Temp_cur_b,Temp_cur_agg); printf("\n\tU_coeff = %f\tU_coeff_agg =
     %f\n",U_coeff,U_coeff_agg);
  */

  return;
}

/***
 *    measuresurf
 *
 *    Releases all dynamically allocated memory for this
 *    program.
 *
 *    SHOULD ONLY BE CALLED IF ALL MEMORY HAS ALREADY BEEN
 *    DYNAMICALLY ALLOCATED
 *
 *    Arguments:    None
 *    Returns:    Nothing
 *
 *    Calls:        free_ccube, free_sicube
 *    Called by:    main,dissolve
 *
 ***/
void measuresurf(void) {
  int kx, ky, kz, jx, jy, jz, faceid;

  jx = jy = jz = 0;
  for (kx = 0; kx < Xsyssize; kx++) {
    for (ky = 0; ky < Ysyssize; ky++) {
      for (kz = 0; kz < Zsyssize; kz++) {
        if (Mic[kx][ky][kz] == POROSITY) {

          for (faceid = 0; faceid < 6; faceid++) {
            switch (faceid) {
            case 0:
              jx = kx + 1;
              if (jx > (Xsyssize - 1))
                jx = 0;
              jy = ky;
              jz = kz;
              break;
            case 1:
              jx = kx - 1;
              if (jx < 0)
                jx = Xsyssize - 1;
              jy = ky;
              jz = kz;
              break;
            case 2:
              jy = ky + 1;
              if (jy > (Ysyssize - 1))
                jy = 0;
              jx = kx;
              jz = kz;
              break;
            case 3:
              jy = ky - 1;
              if (jy < 0)
                jy = Ysyssize - 1;
              jx = kx;
              jz = kz;
              break;
            case 4:
              jz = ky + 1;
              if (jz > (Zsyssize - 1))
                jz = 0;
              jx = kx;
              jy = ky;
              break;
            case 5:
              jz = ky - 1;
              if (jz < 0)
                jz = Zsyssize - 1;
              jx = kx;
              jy = ky;
              break;
            default:
              break;
            }

            if ((Mic[jx][jy][jz] == C3S) || (Mic[jx][jy][jz] == C2S) ||
                (Mic[jx][jy][jz] == C3A) || (Mic[jx][jy][jz] == OC3A) ||
                (Mic[jx][jy][jz] == C4AF) || (Mic[jx][jy][jz] == INERT) ||
                (Mic[jx][jy][jz] == SFUME) || (Mic[jx][jy][jz] == CACO3)) {

              Scnttotal++;
              if ((Mic[jx][jy][jz] == C3S) || (Mic[jx][jy][jz] == C2S) ||
                  (Mic[jx][jy][jz] == C3A) || (Mic[jx][jy][jz] == OC3A) ||
                  (Mic[jx][jy][jz] == C4AF)) {

                Scntcement++;
              }
            }
          }
        }
      }
    }
  }

  Surffract = (float)Scntcement / (float)Scnttotal;
  if (Verbose) {
    printf("Cement surface count is %d \n", Scntcement);
    printf("Total surface count is %d \n", Scnttotal);
    printf("Surface fraction is %f \n", Surffract);
    fflush(stdout);
  }
}

/***
 *    findnewtime
 *
 *    Search experimental kinetic data (calorimetric or chemical shrinkage) for
 *    a match to the current time.  If the experimental data end before the
 *current time is reached, use a generalized quadratic fit procedure to end of
 *    experimental data and extrapolate to later times
 *
 *    Arguments:  float dval is the simulated heat or chemical shrinkage
 *                float act_nrg is the activation energy for temperature change
 *effects float *previousUncorrectedTime is a pointer to the address holding the
 *previous time before any temperature corrections are applied string
 **typestring identifies whether the data are calorimetric or chemical shrinkage
 *    Returns:    Nothing
 *
 *    Called by:    main
 *
 ***/
void findnewtime(float dval, float act_nrg, float *previousUncorrectedTime,
                 char *typestring) {
  register int i;
  float h_interp_factor = -1.0;
  float calFileSaysTimeShouldBe, uncorrectedTime_step, recip_Tdiff;

  if (Verbose)
    printf("\nCurDataLine = %d, NDataLines = %d\n", CurDataLine, NDataLines);
  if (CurDataLine < NDataLines) {
    /* Use linear interpolation of the measured data to get the current time */
    for (i = CurDataLine; (i < NDataLines) && (h_interp_factor < 0.0); i++) {
      /* if (Verbose) */ printf(
          "\ndval = %f, DataValue[%d] = %f, DataValue[%d] = %f\n", dval, i - 1,
          DataValue[i - 1], i, DataValue[i]);
      if ((dval >= DataValue[i - 1]) && (dval <= DataValue[i])) {
        h_interp_factor =
            (dval - DataValue[i - 1]) / (DataValue[i] - DataValue[i - 1]);

        /* First determine how much time has elapsed since the last cycle */
        /* according to the calorimetry data, ASSUMING that the temperature */
        /* is the same as that used to measure the */
        /* the isothermal calorimetry data */

        calFileSaysTimeShouldBe =
            DataTime[i - 1] +
            (h_interp_factor * (DataTime[i] - DataTime[i - 1]));
        uncorrectedTime_step =
            calFileSaysTimeShouldBe - *previousUncorrectedTime;

        /* Now we correct the time difference for the actual temperature */
        /* prevailing during this heat change */

        recip_Tdiff = (1.0 / (Temp_cur_b + 273.15)) -
                      (1.0 / (DataMeasuredAtTemperature + 273.15));
        CalKrate = exp(-(act_nrg * recip_Tdiff));
        Time_step = uncorrectedTime_step / CalKrate;
        TimeHistory[Cyccnt] = TimeHistory[Cyccnt - 1] + Time_step;
        Time_cur = TimeHistory[Cyccnt];
        printf("\n**calFileSaysTimeShouldBe = %f, previousUncorrectedTime = %f",
               calFileSaysTimeShouldBe, *previousUncorrectedTime);
        printf("\n**uncorrectedTime_step = %f", uncorrectedTime_step);
        printf("\n**Temp_cur_b = %f, DataMeasuredAtTemperature = %f",
               Temp_cur_b, DataMeasuredAtTemperature);
        printf("\n**recip_Tdiff = %f", recip_Tdiff);
        printf("\n**act_nrg = %f, CalKrate = %f", act_nrg, CalKrate);
        printf("\n**Time_step = %f, Time_cur = %f\n", Time_step, Time_cur);
        /* if (Verbose) { */
        printf("\n**dval = %f", dval);
        printf("\n**DataValue[%d] = %f, DataValue[%d] = %f", i - 1,
               DataValue[i - 1], i, DataValue[i]);
        printf("\n**DataTime[%d] = %f, DataTime[%d] = %f", i - 1,
               DataTime[i - 1], i, DataTime[i]);
        printf("\n**h_interp_factor = %f", h_interp_factor);
        printf("\n**TimeHistory[%d] = %f and TimeHistory[%d] = %f\n", Cyccnt,
               TimeHistory[Cyccnt], Cyccnt - 1, TimeHistory[Cyccnt - 1]);
        printf("\n**Time_cur = %f\n", Time_cur);
        /* } */
        fflush(stdout);
        *previousUncorrectedTime = calFileSaysTimeShouldBe;
        CurDataLine = i;
      }
    }

    if (h_interp_factor < 0.0) { /* h_interp_factor never calculated; < 0 is the
                                    initialized nonsense value */

      /*  We have just now run past the useful experimental data for time
       * calibration */

      CurDataLine = NDataLines + 1;

      /* if (Verbose) */ printf("\nNo more useful %s data for calibration\n",
                                typestring);
      fflush(stdout);

      /* Now need to estimate Beta for the remaining iterations   */
      /* Estimate with the most recent time history data          */
      /* Use a quadratic regression over the last NTOTAKE points  */

      createfittocycles();

      /* Now, the vector Bvec contains the coefficients of the best-fit */
      /* quadratic equation for mapping */

      /* We record the simulation temperature at which the calorimetry data */
      /* ended, because any further adjustments in the quadratic fit due */
      /* to temperature change should be referenced to the temperature */
      /* at which the fit was made */

      DataFinalTemperature = Temp_cur_b;
      Time_step = (2.0 * Bvec[0] * (float)((Cyccnt - 1)) + (Bvec[1]));
      if (Time_step <= 0.0) {
        printf("\n\n****\n");
        printf("ERROR: Time step is %f at cycle = %d\n", Time_step, Cyccnt);
        printf("       Bvec[0] = %f , Bvec[1] = %f\n", Bvec[0], Bvec[1]);
        printf("****\n\n");
        freeallmem();
        bailout("disrealnew",
                "Problem with time extrapolation from calorimetry");
        exit(1);
      }
      TimeHistory[Cyccnt] = TimeHistory[Cyccnt - 1] + Time_step;
      /* if (Verbose) */ printf("\nQuadratic fit is %g n*n + %g n + %g\n",
                                Bvec[0], Bvec[1], Bvec[2]);
    }
  } else {

    /* Any further change in temperature since the calorimetry data ended must
     * influence */
    /* the dilation or contraction of the quadratic extrapolation */

    recip_Tdiff =
        (1.0 / (Temp_cur_b + 273.15)) - (1.0 / (DataFinalTemperature + 273.15));
    CalKrate = exp(-(act_nrg * recip_Tdiff));
    Time_step = (2.0 * Bvec[0] * (float)((Cyccnt - 1)) + (Bvec[1])) / CalKrate;
    if (Time_step <= 0.0) {
      printf("\n\n****\n");
      printf("ERROR: Time step is %f at cycle = %d\n", Time_step, Cyccnt);
      printf("       Bvec[0] = %f , Bvec[1] = %f\n", Bvec[0], Bvec[1]);
      printf("****\n\n");
      freeallmem();
      bailout("disrealnew", "Problem with time extrapolation from calorimetry");
      exit(1);
    }
    Time_cur += Time_step;
    TimeHistory[Cyccnt] = Time_cur;
  }

  return;
}

/***
 *    createfittocycles
 *
 *    Use second-order Lagrange interpolation to fit a quadratic form to the
 *most recent data for time versus cycles, enabling one to extrapolate to later
 *times
 *
 *    Arguments:  none
 *    Returns:    Nothing
 *
 *    Called by:    main
 *
 ***/
void createfittocycles(void) {
  float x1, x2, x3, a1, a2, a3, b1, b2, b3, y1, y2, y3;
  float sum_xy, sum_x, sum_y, sum_x2, numpoints;
  int i1, i2, i3;
  int increment, done;

  i3 = Cyccnt - 1;
  i1 = i2 = i3;
  increment = 20;
  done = 0;

  x3 = (float)(i3);
  y3 = TimeHistory[i3];

  do {
    i2 = i3 - increment;
    i1 = i2 - increment;

    x2 = (float)(i2);
    x1 = (float)(i1);
    y2 = TimeHistory[i2];
    y1 = TimeHistory[i1];

    a1 = (x1 - x2) * (x1 - x3);
    a2 = (x2 - x1) * (x2 - x3);
    a3 = (x3 - x1) * (x3 - x2);

    b1 = y1 / a1;
    b2 = y2 / a2;
    b3 = y3 / a3;

    Bvec[0] = b1 + b2 + b3; /* quadratic coefficient */
    Bvec[1] = (b1 * (x2 + x3)) + (b2 * (x1 + x3)) + (b3 * (x1 + x2));
    Bvec[1] *= (-1.0); /* linear coefficient */
    Bvec[2] = (b1 * x2 * x3) + (b2 * x1 * x3) +
              (b3 * x1 * x2); /* constant coefficient */
    increment += 10;

  } while (Bvec[0] < 0.0 && i1 > increment);

  if (Bvec[0] < 0.0) {

    /* No quadratic fit was found; default to linear fit with warning */
    printf(
        "WARNING: No quadratic fit could be found to the measurement data!\n");
    printf("         This likely is caused by terminating the measurements\n");
    printf("         too soon.\n\n");
    printf("         Defaulting to a LINEAR fit, which may not yield good "
           "results\n");
    printf("         at later times.\n\n");

    increment = 20;
    numpoints = 3.0;

    i2 = i3 - increment;
    i1 = i2 - increment;
    x2 = (float)(i2);
    x1 = (float)(i1);
    y2 = TimeHistory[i2];
    y1 = TimeHistory[i1];

    /* Linear regression using three points */

    Bvec[0] = 0.0;

    sum_xy = (x1 * y1) + (x2 * y2) + (x3 * y3);
    sum_x = (x1 + x2 + x3);
    sum_y = (y1 + y2 + y3);
    sum_x2 = (x1 * x1) + (x2 * x2) + (x3 * x3);

    Bvec[1] = ((numpoints * sum_xy) - (sum_x * sum_y)) /
              ((numpoints * sum_x2) - (sum_x * sum_x));
    Bvec[2] = (sum_y - (Bvec[0] * sum_x)) / numpoints;
  }
  return;
}

/***
 *    freeallmem
 *
 *    Releases all dynamically allocated memory for this
 *    program.
 *
 *    SHOULD ONLY BE CALLED IF ALL MEMORY HAS ALREADY BEEN
 *    DYNAMICALLY ALLOCATED
 *
 *    Arguments:    None
 *    Returns:    Nothing
 *
 *    Calls:        free_ccube, free_sicube
 *    Called by:    main,dissolve
 *
 ***/
void freeallmem(void) {
  int ntick;
  struct Ants *curant, *antgone;
  struct Alksulf *curas, *asgone;

  if (Mic)
    free_cbox(Mic, Xsyssize, Ysyssize);
  if (Verbose)
    printf("\nFreed cbox Mic");
  if (Micorig)
    free_cbox(Micorig, Xsyssize, Ysyssize);
  if (Verbose)
    printf("\nFreed cbox Micorig");
  if (Micpart)
    free_sibox(Micpart, Xsyssize, Ysyssize);
  if (Verbose)
    printf("\nFreed sibox Micpart");
  if (Cshage)
    free_sibox(Cshage, Xsyssize, Ysyssize);
  if (Verbose)
    printf("\nFreed sibox Cshage");
  if (Deactivated)
    free_sibox(Deactivated, Xsyssize, Ysyssize);
  if (Verbose)
    printf("\nFreed sibox Deactivated");
  if (Startflag)
    free_ivector(Startflag);
  if (Verbose)
    printf("\nFreed ivector Startflag");
  if (Stopflag)
    free_ivector(Stopflag);
  if (Verbose)
    printf("\nFreed ivector Stopflag");
  if (Deactphaselist)
    free_ivector(Deactphaselist);
  if (Verbose)
    printf("\nFreed ivector Deactphaselist");
  if (Deactfrac)
    free_fvector(Deactfrac);
  if (Verbose)
    printf("\nFreed fvector Deactfrac");
  if (Reactfrac)
    free_fvector(Reactfrac);
  if (Verbose)
    printf("\nFreed fvector Reactfrac");
  if (Deactinit)
    free_fvector(Deactinit);
  if (Verbose)
    printf("\nFreed fvector Deactinit");
  if (Deactends)
    free_fvector(Deactends);
  if (Verbose)
    printf("\nFreed fvector Deactends");
  if (Deactterm)
    free_fvector(Deactterm);
  if (Verbose)
    printf("\nFreed fvector Deactterm");
  if (Molarvcsh)
    free_fvector(Molarvcsh);
  if (Verbose)
    printf("\nFreed fvector Molarvcsh");
  if (Watercsh)
    free_fvector(Watercsh);
  if (Verbose)
    printf("\nFreed fvector Watercsh");
  if (Disprob)
    free_fvector(Disprob);
  if (Verbose)
    printf("\nFreed fvector Disprob");
  if (Disbase)
    free_fvector(Disbase);
  if (Verbose)
    printf("\nFreed fvector Disbase");
  if (Discoeff)
    free_fvector(Discoeff);
  if (Verbose)
    printf("\nFreed fvector Discoeff");
  if (Soluble)
    free_ivector(Soluble);
  if (Verbose)
    printf("\nFreed ivector Soluble");
  if (Creates)
    free_ivector(Creates);
  if (Verbose)
    printf("\nFreed ivector Creates");
  if (Onepixelbias)
    free_fvector(Onepixelbias);
  if (Verbose)
    printf("\nFreed fvector Onepixelbias");
  if (PHsulfcoeff)
    free_fvector(PHsulfcoeff);
  if (Verbose)
    printf("\nFreed fvector PHsulfcoeff");
  if (PHfactor)
    free_fvector(PHfactor);
  if (Verbose)
    printf("\nFreed fvector PHfactor");
  if (CustomImageTime)
    free_fvector(CustomImageTime);
  if (Verbose)
    printf("\nFreed fvector CustomImageTime");
  if (DataTime)
    free_fvector(DataTime);
  if (Verbose)
    printf("\nFreed fvector DataTime");
  if (DataValue)
    free_fvector(DataValue);
  if (Verbose)
    printf("\nFreed fvector DataValue");
  if (TimeHistory)
    free_fvector(TimeHistory);
  if (Verbose)
    printf("\nFreed fvector TimeHistory");

  /*** Now free the ants ***/

  if (Headant) {
    ntick = 0;
    curant = Headant->nextant;
    while (curant) {
      ntick++;
      if (ntick == 1) {
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
    }
    if (Verbose)
      printf("\nFreed all ants except Headant... ");
    free(Headant);
    if (Verbose)
      printf("freed Headant\n");
  }

  if (Headks) {
    ntick = 0;
    curas = Headks->nextas;
    while (curas) {
      ntick++;
      if (ntick == 1) {
        Headks->nextas = curas->nextas;
      } else {
        (curas->prevas)->nextas = curas->nextas;
      }
      if (curas->nextas) {
        (curas->nextas)->prevas = curas->prevas;
      } else {
        Tailks = curas->prevas;
      }
      asgone = curas;
      curas = curas->nextas;
      free(asgone);
    }
    if (Verbose)
      printf("\nFreed all ks except Headks... ");
    free(Headks);
    if (Verbose)
      printf("freed Headks\n");
  }

  if (Headnas) {
    ntick = 0;
    curas = Headnas->nextas;
    while (curas) {
      ntick++;
      if (ntick == 1) {
        Headnas->nextas = curas->nextas;
      } else {
        (curas->prevas)->nextas = curas->nextas;
      }
      if (curas->nextas) {
        (curas->nextas)->prevas = curas->prevas;
      } else {
        Tailnas = curas->prevas;
      }
      asgone = curas;
      curas = curas->nextas;
      free(asgone);
    }
    if (Verbose)
      printf("\nFreed all nas except Headnas... ");
    free(Headnas);
    if (Verbose)
      printf("freed Headnas\n");
  }

  return;
}
