/******************************************************
 *
 * properties
 *
 * Assigns all physical and chemical properties
 * of cement phases
 *
 * Called by:	genpartnew, distrib3d, disrealnew
 *
 ******************************************************/
#include "vcctl.h"

/***
 *	Global variables for specific gravity,
 *	isobaric specific heat, dissolution probability
 *	water consumption, heat of formation, molar volume,
 *	and water content.
 *
 *	Water content, Nh2o, is the number of moles of water in each
 *	mole of the given phases.  It is given three different values
 *	here:
 *			Nh2o[i][0] = stoichiometric coeff of water at 25C
 *			Nh2o[i][1] = stoichiometric coeff of water at 105C
 *
 *	On the other hand, water consumption, Waterc,
 *	is the number of MOLES of water consumed in the hydration
 *	reaction that produces the given phase.  Thus, the
 *	water content for dihydrate is 2.0, while the water
 *	consumption is 0.0 because it is a starting phase.
 *
 ***/
float Specgrav[NPHASES], Waterc[NPHASES], Nh2o[NPHASES][2];
float Heatf[NPHASES], Molarv[NPHASES];
float Cp_agg, Cp_ch, Cp_pozz, Cp_cement, Cp_h2o, Cp_bh2o;

/***
 *	Function declaration
 ***/
void assign_properties(void);

/******************************************************
 *
 *	assign_properties
 *
 *	Function to assign physical and chemical properties
 *	to the cement paste phases
 *
 * 	Molar volumes are in cm^3/mole
 * 	Heats of formation are in kJ/mole
 * 	Heat capacities are in J/g/K
 *
 * 	See paper by Fukuhara et al., Cem. & Con. Res.
 * 		Volume 11, pp. 407-414, 1981
 *       and CRC for heats of formation, etc.
 *
 *	Arguments:	None
 *	Returns:	Nothing
 *
 ******************************************************/
void assign_properties(void) {
  int i;

  for (i = 0; i < NPHASES; i++) {
    Molarv[i] = 0.0;
    Heatf[i] = 0.0;
    Waterc[i] = 0.0;
    Nh2o[i][0] = 0.0;
    Nh2o[i][1] = 0.0;
    Specgrav[i] = 0.0;
  }

  Molarv[POROSITY] = 18.068; /* Molarv and Specgrav updated 9 Feb 2004 */
  Heatf[POROSITY] = (-285.83);
  Waterc[POROSITY] = 1.0;
  Nh2o[POROSITY][0] = 1.0;
  Nh2o[POROSITY][1] = 0.0;
  Specgrav[POROSITY] = 0.99707;

  /***
   *	Properties of porosity formed by cracking.  Currently set to
   *	contain water.  Modify here if it is desired that cracked
   *	porosity be empty (24 May 2004)
   ***/

  Molarv[CRACKP] = 18.068;
  Heatf[CRACKP] = (-285.83);
  Waterc[CRACKP] = 1.0;
  Nh2o[CRACKP][0] = 1.0;
  Nh2o[CRACKP][1] = 0.0;
  Specgrav[CRACKP] = 0.99707;

  Molarv[C3S] = 71.129; /* Molarv and Specgrav updated 9 Feb 2004 */
  Heatf[C3S] = (-2927.82);
  Waterc[C3S] = 0.0;
  Nh2o[C3S][0] = 0.0;
  Nh2o[C3S][1] = 0.0;
  Specgrav[C3S] = 3.21;
  Cp_cement = 0.75;

  Molarv[C2S] = 52.513; /* Molarv and Specgrav updated 9 Feb 2004 */
  Heatf[C2S] = (-2311.6);
  Waterc[C2S] = 0.0;
  Nh2o[C2S][0] = 0.0;
  Nh2o[C2S][1] = 0.0;
  Specgrav[C2S] = 3.28;

  Molarv[C3A] = 88.94; /* Molarv and Specgrav updated 9 Feb 2004 */
  Heatf[C3A] = (-3587.8);
  Waterc[C3A] = 0.0;
  Nh2o[C3A][0] = 0.0;
  Nh2o[C3A][1] = 0.0;
  Specgrav[C3A] = 3.038;

  Molarv[OC3A] = 88.53;    /* Molarv and Specgrav updated 9 Feb 2004 */
  Heatf[OC3A] = (-3587.8); /* Not known, set to value for C3A */
  Waterc[OC3A] = 0.0;
  Nh2o[OC3A][0] = 0.0;
  Nh2o[OC3A][1] = 0.0;
  Specgrav[OC3A] = 3.052; /* Guess for orthorhombic from Taylor */

  Molarv[FAC3A] = Molarv[C3A];
  Heatf[FAC3A] = Heatf[C3A];
  Waterc[FAC3A] = Waterc[C3A];
  Nh2o[FAC3A][0] = Nh2o[C3A][0];
  Nh2o[FAC3A][1] = Nh2o[C3A][1];
  Specgrav[FAC3A] = Specgrav[C3A];

  Molarv[C4AF] = 130.29; /* Molarv and Specgrav updated 9 Feb 2004 */
  Heatf[C4AF] = (-5090.3);
  Waterc[C4AF] = 0.0;
  Nh2o[C4AF][0] = 0.0;
  Nh2o[C4AF][1] = 0.0;
  Specgrav[C4AF] = 3.73;

  /* Properties for Arcanite */
  Molarv[K2SO4] = 65.46; /* Molarv and Specgrav updated 9 Feb 2004 */
  Heatf[K2SO4] = -1438.82;
  Waterc[K2SO4] = 0.0;
  Nh2o[K2SO4][0] = 0.0;
  Nh2o[K2SO4][1] = 0.0;
  Specgrav[K2SO4] = 2.662;

  /* Properties for thenardite */
  Molarv[NA2SO4] = 53.0; /* Molarv and Specgrav updated 9 Feb 2004 */
  Heatf[NA2SO4] = -1388.07;
  Waterc[NA2SO4] = 0.0;
  Nh2o[NA2SO4][0] = 0.0;
  Nh2o[NA2SO4][1] = 0.0;
  Specgrav[NA2SO4] = 2.68;

  Molarv[GYPSUM] = 74.21; /* Molarv updated 9 Feb 2004 */
  Heatf[GYPSUM] = (-2022.6);
  Waterc[GYPSUM] = 0.0;
  Nh2o[GYPSUM][0] = 2.0; /* Gypsum is same as dihydrate */
  Nh2o[GYPSUM][1] = 0.5; /* Converts to hemihydrate at 70-200 C */
  Specgrav[GYPSUM] = 2.32;

  Molarv[ANHYDRITE] = 52.16;
  Heatf[ANHYDRITE] = (-1424.6);
  Waterc[ANHYDRITE] = 0.0;
  Nh2o[ANHYDRITE][0] = 0.0;
  Nh2o[ANHYDRITE][1] = 0.0;
  Specgrav[ANHYDRITE] = 2.61;

  Molarv[HEMIHYD] = 52.973; /* Molarv and Specgrav updated 9 Feb 2004 */
  Heatf[HEMIHYD] = (-1574.65);
  Waterc[HEMIHYD] = 0.0;
  Nh2o[HEMIHYD][0] = 0.5;
  Nh2o[HEMIHYD][1] = 0.5;
  Specgrav[HEMIHYD] = 2.74;

  /***
   *	For improvement in chemical shrinkage
   *	correspondence.  Changed molar volume
   *	of C_1.7-S-H_4.0 to 108.0
   *
   * 	See H.F.W. Taylor, Mater. Res. Soc. Proc.
   * 	Vol. 85, p. 47 (1987) for information on
   * 	stoichiometry at 105 C
   *
   *   In that paper, Taylor proposes that the molar
   *   ratio of BOUND H2O to Ca is 1.4. So if C-S-H
   *   is defined as 1 mol CSH = 1 mol Si, then 1 mol
   *   of CSH has 1.7 mol Ca and therefore 2.38 moles
   *   of bound water per mole of CSH.
   *
   *   So Waterc[CSH] of 4.0 assumes that there is
   *   1.62 moles of free water per mole of CSH.
   *   Using the Molarv[CSH] value of 107.81 cm3
   *   below, and that 1.62 moles of water occupies
   *   a volume of 29.16 cm3, this implies that
   *   CSH has an internal free-water pore volume
   *   of 29.16 cm3/mole or a free water volume
   *   fraction of 0.27.
   *
   *	18 Dec 2020
   *
   ***/

  Molarv[CSH] = 107.81; /* Molarv and Specgrav updated 9 Feb 2004 */
  Heatf[CSH] = (-3283.0);
  Waterc[CSH] = 4.0;
  Nh2o[CSH][0] = 4.0;
  Nh2o[CSH][1] = 0.50 * Nh2o[CSH][0];

  /* Changed above coeff from 0.6 to 0.4, 8 Jan 2004 */

  Specgrav[CSH] = 2.11;

  Molarv[CH] = 33.078; /* Molarv updated 9 Feb 2004 */
  Heatf[CH] = (-986.1);
  Waterc[CH] = 1.0;
  Nh2o[CH][0] = 1.0;
  Nh2o[CH][1] = 1.0;
  Specgrav[CH] = 2.24;
  Cp_ch = 0.75;

  /***
   *	Assume that CaCO3 has the calcite
   *	structure
   ***/

  Molarv[CACO3] = 36.93;
  Heatf[CACO3] = (-1206.92);
  Waterc[CACO3] = 0.0;
  Nh2o[CACO3][0] = 0.0;
  Nh2o[CACO3][1] = 0.0;
  Specgrav[CACO3] = 2.71;

  /***
   *	Assume that CaO has the alpha cubic
   *	structure
   ***/

  Molarv[FREELIME] = 16.943;
  Heatf[FREELIME] = (-635.77);
  Waterc[FREELIME] = 0.0;
  Nh2o[FREELIME][0] = 0.0;
  Nh2o[FREELIME][1] = 0.0;
  Specgrav[FREELIME] = 3.31;

  /***
   * 	See H.F.W. Taylor, Mater. Res. Soc. Proc.
   * 	Vol. 85, p. 47 (1987) for information on
   * 	stoichiometry at 105 C
   *
   *	Still need to determine heat of
   *	formation of AFMC
   ***/
  Molarv[AFMC] = 261.91;
  Heatf[AFMC] = (0.0);
  Waterc[AFMC] = 11.0;
  Nh2o[AFMC][0] = 13.0;
  Nh2o[AFMC][1] = 9.0;
  Specgrav[AFMC] = 2.17;

  Molarv[GYPSUMS] = Molarv[GYPSUM];
  Heatf[GYPSUMS] = Heatf[GYPSUM];
  Waterc[GYPSUMS] = 2.0;
  Nh2o[GYPSUMS][0] = Nh2o[GYPSUM][0];
  Nh2o[GYPSUMS][1] = Nh2o[GYPSUM][1];
  Specgrav[GYPSUMS] = Specgrav[GYPSUM];

  Molarv[ABSGYP] = Molarv[GYPSUM];
  Heatf[ABSGYP] = Heatf[GYPSUM];
  Waterc[ABSGYP] = 2.0;
  Nh2o[ABSGYP][0] = Nh2o[GYPSUM][0];
  Nh2o[ABSGYP][1] = Nh2o[GYPSUM][1];
  Specgrav[ABSGYP] = Specgrav[GYPSUM];

  /***
   *	No data available for dehydration of
   *	hydrogarnet at 105 C, so assume that
   *	none occurs
   ***/
  Molarv[C3AH6] = 150.12; /* Molarv updated 9 Feb 2004 */
  Heatf[C3AH6] = (-5548.0);
  Waterc[C3AH6] = 6.0;
  Nh2o[C3AH6][0] = 6.0;
  Nh2o[C3AH6][1] = 6.0;
  Specgrav[C3AH6] = 2.52;

  /***
   *	Changed molar volume of FH3 to 69.8
   *	Specific gravity of 3.0
   *
   *	23 May 1995
   ***/

  Molarv[FH3] = 69.803; /* Molarv and Specgrav updated 9 Feb 2004 */
  Heatf[FH3] = (-823.9);
  Waterc[FH3] = 3.0;
  Nh2o[FH3][0] = 3.0;
  Nh2o[FH3][1] = 3.0;
  Specgrav[FH3] = 3.062;

  /***
   *	Changed molar volume of ettringite to 735
   *	Specific gravity of 1.7
   *
   * 	See H.F.W. Taylor, Mater. Res. Soc. Proc.
   * 	Vol. 85, p. 47 (1987) for information on
   * 	stoichiometry at 105 C
   *
   *	24 May 1995
   ***/

  Molarv[ETTR] = 735.01; /* Molarv and Specgrav updated 9 Feb 2004 */
  Heatf[ETTR] = (-17539.0);
  Waterc[ETTR] = 26.0;
  Nh2o[ETTR][0] = 32.0;
  Nh2o[ETTR][1] = 8.0;
  Specgrav[ETTR] = 1.7076;

  Molarv[ETTRC4AF] = Molarv[ETTR];
  Heatf[ETTRC4AF] = Heatf[ETTR];
  Waterc[ETTRC4AF] = Waterc[ETTR];
  Nh2o[ETTRC4AF][0] = Nh2o[ETTR][0];
  Nh2o[ETTRC4AF][1] = Nh2o[ETTR][1];
  Specgrav[ETTRC4AF] = Specgrav[ETTR];

  Molarv[AFM] = 312.82; /* Molarv updated 9 Feb 2004 */
  Heatf[AFM] = (-8778.0);

  /***
   *	Each mole of AFM that forms requires
   *	12 moles of water, two of which are supplied
   *	by gypsum in forming ettringite.  This
   *	leaves 10 moles to be incorporated from
   *	free water
   *
   * 	See H.F.W. Taylor, Mater. Res. Soc. Proc.
   * 	Vol. 85, p. 47 (1987) for information on
   * 	stoichiometry at 105 C
   *
   ***/

  Waterc[AFM] = 10.0;
  Nh2o[AFM][0] = 13.0;
  Nh2o[AFM][1] = 9.0;
  Specgrav[AFM] = 1.99;

  Molarv[CACL2] = 51.62;
  Heatf[CACL2] = (-795.8);
  Waterc[CACL2] = 0.0;
  Nh2o[CACL2][0] = 0.0;
  Nh2o[CACL2][1] = 0.0;
  Specgrav[CACL2] = 2.15;

  /***
   *	No data available for heat of formation
   *	of Friedel's salt.  Also no data on
   *	dehydration at 105 C, so assume that
   *	none occurs at T <= 105 C
   ***/
  Molarv[FRIEDEL] = 296.662;
  Heatf[FRIEDEL] = (0.0);
  Waterc[FRIEDEL] = 10.0;
  Nh2o[FRIEDEL][0] = 10.0;
  Nh2o[FRIEDEL][1] = 10.0;
  Specgrav[FRIEDEL] = 1.892;

  /***
   *	Basic reaction for ASG is to form
   *	Stratlingite:
   *
   *		2CH + ASG + 6H --> C2ASH8
   ***/

  Molarv[ASG] = 49.9;
  /* No data available for heat of formation */
  Heatf[ASG] = (0.0);
  Waterc[ASG] = 0.0;
  Nh2o[ASG][0] = 0.0;
  Nh2o[ASG][1] = 0.0;
  Specgrav[ASG] = 3.247;

  Molarv[CAS2] = 100.62;
  /* No data available for heat of formation */
  Heatf[CAS2] = (0.0);
  Waterc[CAS2] = 0.0;
  Nh2o[CAS2][0] = 0.0;
  Nh2o[CAS2][1] = 0.0;
  Specgrav[CAS2] = 2.77;

  /***
   *	No data available for heat of formation
   *	of stratlingite, nor for dehydration at
   *	T = 105 C.  Assume that no dehydration
   *	occurs for T <= 105 C
   ***/
  Molarv[STRAT] = 215.63;
  Heatf[STRAT] = (0.0);
  Waterc[STRAT] = 8.0;
  Nh2o[STRAT][0] = 8.0;
  Nh2o[STRAT][1] = 8.0;
  Specgrav[STRAT] = 1.94;

  /***
   *	Use heat of formation and specific gravity
   *	of quartz for unreacted pozzolanic phase, modeled
   *	as silica fume
   *
   *	Source:  CRC Handbook of Chemistry and Physics
   ***/
  Molarv[SFUME] = 27.0;
  Heatf[SFUME] = (-907.5);
  Waterc[SFUME] = 0.0;
  Nh2o[SFUME][0] = 0.0;
  Nh2o[SFUME][1] = 0.0;
  Specgrav[SFUME] = 2.2;
  Cp_pozz = 0.75;

  /***
   *	Use these same values for unreacted
   *	fly ash pozzolanic phase.  Only difference between
   *	AMSIL and SFUME is the intrinsic reactivity, which
   *	is not reflected here.
   ***/
  Molarv[AMSIL] = Molarv[SFUME];
  Heatf[AMSIL] = Heatf[SFUME];
  Waterc[AMSIL] = Waterc[SFUME];
  Nh2o[AMSIL][0] = Nh2o[SFUME][0];
  Nh2o[AMSIL][1] = Nh2o[SFUME][1];
  Specgrav[AMSIL] = Specgrav[SFUME];

  /***
   *	Data for pozzolanic C-S-H based on work of
   *	Atlassi, DeLarrand, and Jensen.  Gives a
   *	chemical shrinkage of 0.2 g H2O/g CSF
   *
   *	Estimated heat of formation based on heat
   *	release of 780 J/g condensed silica fume
   *
   *	Changed stoichiometry to be C_1.1-S-H_2.9
   *	to see effect on results (22 Jan 1997).
   *
   *	Molecular mass it 191.8 g/mole
   *	Changed molar volume to 101.81 (10 Mar 1997)
   *
   * 	No data available for dehydration at T = 105 C.
   * 	Assume the same dehydration behavior as for
   * 	C-S-H gel, that is that about 60% of the water
   * 	(by mass) is retained by T = 105 C (see
   * 	H.F.W. Taylor, Mater. Res. Soc. Proc.
   * 	Vol. 85, p. 47 (1987) for information on
   * 	CSH stoichiometry at 105 C)
   *
   ***/

  Molarv[POZZCSH] = 101.81;
  Heatf[POZZCSH] = (-2299.1);
  Waterc[POZZCSH] = 2.9;
  Nh2o[POZZCSH][0] = 2.9;
  Nh2o[POZZCSH][1] = 0.60 * Nh2o[POZZCSH][0];
  Specgrav[POZZCSH] = 1.884;

  /***
   *	Assume inert filler has same specific gravity
   *	and molar volume as quartz
   ***/

  Molarv[INERT] = 27.0;
  Heatf[INERT] = (0.0);
  Waterc[INERT] = 0.0;
  Nh2o[INERT][0] = 0.0;
  Nh2o[INERT][1] = 0.0;
  Specgrav[INERT] = 2.2;

  /***
   *	SLAG properties are read in the slag
   *	characteristics file within disrealnew,
   *	so they are not given here
   ***/

  Molarv[SLAG] = 27.0;
  Heatf[SLAG] = (0.0);
  Waterc[SLAG] = 0.0;
  Nh2o[SLAG][0] = 0.0;
  Nh2o[SLAG][1] = 0.0;
  Specgrav[SLAG] = 2.2;

  /***
   *	Should be no FLYASH phase in disrealnew.c,
   *	but we use these data as fictitious placeholders
   *	for the non-evaporable water calculations to
   *	prevent divide-by-zero errors just in case.
   *	The data themselves are not to be regarded
   *	as accurate.
   ***/

  Molarv[FLYASH] = Molarv[CAS2];
  Heatf[FLYASH] = Heatf[CAS2];
  Waterc[FLYASH] = Waterc[CAS2];
  Nh2o[FLYASH][0] = Nh2o[CAS2][0];
  Nh2o[FLYASH][1] = Nh2o[CAS2][1];
  Specgrav[FLYASH] = Specgrav[CAS2];

  /***
   *	Assume inert aggregate has same specific gravity
   *	and molar volume as quartz
   ***/

  Molarv[INERTAGG] = 27.0;
  Heatf[INERTAGG] = (0.0);
  Waterc[INERTAGG] = 0.0;
  Nh2o[INERTAGG][0] = 0.0;
  Nh2o[INERTAGG][1] = 0.0;
  Specgrav[INERTAGG] = 2.2;

  /***
   *	Data for brucite and magnesium sulfate taken from
   *	CRC Handbook of Physics and Chemistry, 63rd Ed.
   ***/

  Molarv[BRUCITE] = 24.72;
  /* Heat of formation data unavailable */
  Heatf[BRUCITE] = (0.0);
  Waterc[BRUCITE] = 1.0;
  Nh2o[BRUCITE][0] = 1.0;
  Nh2o[BRUCITE][1] = 1.0;
  Specgrav[BRUCITE] = 2.36;

  Molarv[MS] = 45.25;
  /* Heat of formation data unavailable */
  Heatf[MS] = (0.0);
  Waterc[MS] = 0.0;
  Nh2o[MS][0] = 0.0;
  Nh2o[MS][1] = 0.0;
  Specgrav[MS] = 2.66;

  Molarv[EMPTYP] = 18.0; /* Set to that of water for some calculations */
  Heatf[EMPTYP] = (-285.83);
  Waterc[EMPTYP] = 0.0;
  Nh2o[EMPTYP][0] = 0.0;
  Nh2o[EMPTYP][1] = 0.0;
  Specgrav[EMPTYP] = 1.0;

  /***
   *	Heat capacities for other phases
   *	not already defined
   ***/

  Cp_agg = 0.84;
  Cp_h2o = 4.18;
  Cp_bh2o = 2.20;

  return;
}
