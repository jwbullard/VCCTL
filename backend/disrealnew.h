/******************************************************
 *
 * Header file specific to program disrealnew.h
 *
 * Programmer:	Dale P. Bentz and Jeffrey W. Bullard
 * 				Engineering Laboratory
 *				NIST
 *				100 Bureau Drive Mail Stop 8621
 *				Gaithersburg, MD  20899-8621   USA
 *				(301) 975-5865      FAX: (301) 990-6891
 *				E-mail: dale.bentz@nist.gov
 *
 * Contact:		Jeffrey W. Bullard
 *               Zachry Department of Civil and Environmental Engineering
 *				Department of Materials Science and Engineering
 *				Texas A&M University
 *				3136 TAMU
 *				College Station, TX  77845  USA
 *				(979) 458-6482
 *				E-mail: jwbullard@tamu.edu
 *
 *******************************************************/

/***
 *	Pre-processor defines
 ***/

/* Maximum number of cycles of hydration */
#define MAXCYC 30000

/* For hydration under sealed conditions: */
#define CUBEMAX 7 /* Maximum cube size for checking pore size */

static int CUBEMIN = 3; /* Minimum cube size for checking pore size */

/* Maximum number of random attempts to place a new pixel phase */
static int MAXTRIES = 5000;

#define MEMERR -1

/* Different choices for calibrating time scale */

#define BETAFACTOR 0
#define CALORIMETRIC 1
#define CHEMICALSHRINKAGE 2

/***
 *	Biases to dissolution probabilities.  Determined by
 *	reaction rates in H.F.W. Taylor, "Cement Chemistry", 2nd.
 *	Edition. Telford Publishing, London, 1997.  Also determined
 *	in part by calibration to experimental data.
 ***/
static float DISBIAS = 30.0;         /* Dissolution bias- to change
                                                     all dissolution rates */
static float DISMIN = 0.001;         /* Minimum dissolution for C3S */
static float DISMIN2 = 0.00025;      /* Minimum dissolution for C2S */
static float DISMINSLAG = 0.0001;    /* Minimum dissolution for SLAG */
static float DISMINASG = 0.0005;     /* Minimum dissolution for ASG */
static float DISMINCAS2 = 0.0005;    /* Minimum dissolution for CAS2 */
static float DISMIN_C3A_0 = 0.002;   /* Minimum dissolution for C3A */
static float DISMIN_C4AF_0 = 0.0005; /* Minimum dissolution for C4AF */

/***
 *	Default maximum number of diffusing ants
 ***/
static int DK2SO4MAX = 200000;   /* Added 3 June 2004 */
static int DNA2SO4MAX = 2000000; /* Added 3 June 2004 */
static int DETTRMAX = 1200;
static int DGYPMAX = 2000;
static int DCACO3MAX = 1000;
static int DCACL2MAX = 2000;
static int DCAS2MAX = 2000;
static int DASMAX = 2000;

/***
 *	Default solubilities of CH and C3AH6
 ***/
static float CHCRIT = 50.0;
static float C3AH6CRIT = 10.0;

/***
 *	Default scale of CSH and C3AH6 that defines
 *	transition between induction and acceleration
 ***/
static float CSHSCALE = 70000.0;
static float C3AH6_SCALE = 2000.0;

/***
 *	Reaction probabilities for growth of various solid phases
 ***/
static float C3AH6GROW = 0.01; /* C3AH6 growth */
static float CHGROW = 1.0;     /* CH growth */
static float CHGROWAGG = 1.0;  /* CH growth on aggregate surface */
static float ETTRGROW = 0.002; /* Ettringite growth */

/***
 *	Probabilities for various hydration reactions
 *	between diffusing species
 ***/
static float C3AETTR = 0.001;    /* Diffusing C3A with solid ettringite */
static float C3AGYP = 0.001;     /* Diffusing C3A with diffusing gypsum,
                                                 diffusing anhydrite, and
                                                 diffusing hemihydrate */
static float SOLIDC3AGYP = 0.5;  /* Solid C3A with diffusing sulfate */
static float SOLIDC4AFGYP = 0.1; /* Solid C4AF with diffusing sulfate */

static float PSFUME = 0.05; /* Probability for pozzolanic reaction,
                                                   assuming a silica-fume source
                               with high surface area */

static float SF_SiO2_val = 94.3;
static float SF_SiO2_normal = 94.3;
static float SF_BET_val = 24.0;
static float SF_BET_normal = 24.0;
static float SF_LOI_val = 2.0;
static float SF_LOI_normal = 2.0;
static float LOI_factor = 1.0;

/***
 *	Introduce a pozzolanic phase for fly ash, less reactive
 *	than silica fume, referred to as AMSIL
 *	(stands for amorphous silica).  This is its intrinsic
 *	reactivity
 *
 ***/
static float PAMSIL = 0.009;

/***
 *	Factor determining conversion of C-S-H gel to pozzolanic
 *	C-S-H gel
 ***/
static float PCSH2CSH = 0.002;

/***
 *	Probability of gypsum absorption into C-S-H gel
 ***/
float AGRATE = 0.25;

/***
 *	Parameters determining the variation with temperature
 *	of the solubility of CH.  Data taken from
 *	H.F.W. Taylor, "Cement Chemistry", 2nd Edition.
 *	Telford, London, 1997.
 ***/
static float A0_CHSOL = 1.325;
static float A1_CHSOL = 0.008162;

/***
 *	Scale factors for determining transition between induction
 *	and acceleration of silicate hydration
 ***/
static float WCSCALE = 0.4; /* Influence of w/c on induction */

/***
 *	Maximum distance from silicate surfaces to locate
 *	diffusing CSH
 ***/
static int DISTLOCCSH = 17;

/***
 *	Number of neighbors to consider when checking
 *	for allowing dissolution (6, 18, or 26)
 ***/
static int NEIGHBORS = 26;

/***
 *	Water bound per gram of cement during hydration
 ***/
static float WN = 0.23;

/***
 *	Water imbibed per gram of cement during chemical shrinkage
 *	(estimate)
 ***/
static float WCHSH = 0.06;

/***
 *	Maximum number of diffusion steps in each cycle
 ***/
static int MAXDIFFSTEPS = 500;

/***
 *	Probability of a diffusion step in C-S-H gel, taken
 *	from E.J. Garboczi and D.P. Bentz,
 *	J. Mater. Sci, 27 2083-2092 (1992).
 ***/
static float PDIFFCSH = 0.0004;

/***
 *	Data structure for diffusing species (generically called ants)
 *	Structure in the form of a doubly linked list.  The size of the
 *	list is dynamically allocated and managed so that the list
 *	may shrink or grow in size as needed.
 *
 ****
 *	NOTE: IF SYSTEM SIZE EXCEEDS 256, NEED TO CHANGE X, Y, AND Z TO
 * 			INT VARIABLES
 ***/
struct Ants {
  unsigned int x, y, z, id;
  int cycbirth;
  struct Ants *nextant;
  struct Ants *prevant;
};

/***
 *	Data structure for elements to remove to simulate
 *	self-dessication.  The list is once again a doubly linked
 *	list to be dynamically allocated and managed
 ***/
struct Togo {
  int x, y, z, npore;
  struct Togo *nexttogo;
  struct Togo *prevtogo;
};

/***
 *	Data structure for alkali sulfates to dissolve.
 *	The list is once again a doubly linked
 *	list to be dynamically allocated and managed
 ***/
struct Alksulf {
  unsigned int x, y, z;
  struct Alksulf *nextas;
  struct Alksulf *prevas;
};

/***
 *	Global variable declarations:
 *
 ***/

size_t Antsize, Togosize, Alksulfsize;

int Verbose;
int AggTempEffect = 1;

/***
 *		microstructure stored in array mic of type char
 *			to reduce storage requirements
 *
 *		initial particle ids stored in array micpart
 *			(used to assess set point)
 ***/

char ***Mic = NULL;
char ***Micorig = NULL;
short int ***Micpart = NULL;
short int ***Cshage = NULL;
short int ***Faces = NULL;
float *CustomImageTime = NULL;

/* Arrays for keeping track of surface deactivation */

short int ***Deactivated = NULL;
int Verbose;
int *Startflag = NULL;
int *Stopflag = NULL;
int *Deactphaselist = NULL;
float *Deactfrac = NULL;
float *Reactfrac = NULL;
float *Deactinit = NULL;
float *Deactends = NULL;
float *Deactterm = NULL;

/* Arrays for variable CSH molar volume and water consumption */

float *Molarvcsh = NULL;
float *Watercsh = NULL;

float SulftoC3A;

/* Arrays for keeping track of dissolution probabilities of solid phases */

float *Disprob = NULL;
float *Disbase = NULL;
float *Discoeff = NULL;
float *Onepixelbias = NULL;
int *Soluble = NULL;
int *Creates = NULL;

/* Arrays for storing pH effects on solubility for each phase */

float *PHsulfcoeff = NULL;
float *PHfactor = NULL;

/* Information for in-situ cracking of microstructure */
int Crackwidth = 0;
int Crackcycle = 0;
int Crackorient = 1; /* 1 for x, 2 for y, 3 for z */

/* System size (in pixels) and resolution (in microns) */

int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
int Xsyssize_orig = DEFAULTSYSTEMSIZE;
int Ysyssize_orig = DEFAULTSYSTEMSIZE;
int Zsyssize_orig = DEFAULTSYSTEMSIZE;
int Syspix = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
int Syspix_orig = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
float Res = DEFAULTRESOLUTION;
float Sizemag = 1.0;
float Sizemag_orig = 1.0;
int Isizemag = 1;
int Isizemag_orig = 1;

/* Number of types of pixels and solid pixels*/
int Npixtypes, Nsphases;

/* VCCTL software version used to create input file */
float Version;

/* Counts for dissolved and solid species */
int Discount[NPHASES + 1], Count[NPHASES + 1];
int Ncshplategrow = 1;
int Ncshplateinit = 0;

/***
 *	Counts for pozzolan reacted, initial pozzolan,
 *	gypsum, ettringite, initial porosity, and
 *	aluminosilicate reacted
 ***/
int Nsilica_rx = 0, Nsilica = 0, Ncsbar = 0, Netbar = 0;
int Porinit = 0, Freelimeinit = 0;
int Ksbarinit, Nsbarinit;
int Nasr = 0, Nslagr = 0, Slagemptyp = 0;

/* Initial clinker phase counts */
int C3sinit, C2sinit, C3ainit, Oc3ainit, C4afinit, Anhinit, Heminit, Crackpinit,
    Chold, Chnew;
int Nasulfinit, Ksulfinit;
int Nmade, Ngoing, Gypready, Poregone, Poretodo, Countpore = 0;
int Countkeep, Water_left, Water_off, Pore_off;
int Ncyc, Cyccnt, Cubesize, Sealed, Sealed_after_crack, Outfreq, Phydfreq,
    Numdeact;
int Icyc, Burnfreq, Setfreq, Setflag, Sf1, Sf2, Sf3, Porefl1, Porefl2, Porefl3;
int Ticyc, Tcyccnt, Tncyc, Suspend = 1, Icycstart = 1;
int Tcustomoutputentries;
float Burntimefreq, Settimefreq, Phydtimefreq, OutTimefreq;
float NextBurnTime, NextSetTime, NextPhydTime;

/***
 *	X,Y,Z relative coordinates from the center of a 3x3x3 cube
 ***/
int Xoff[27] = {1, 0, 0,  -1, 0, 0, 1, 1, -1, -1, 0,  0,  0, 0,
                1, 1, -1, -1, 1, 1, 1, 1, -1, -1, -1, -1, 0};
int Yoff[27] = {0, 1, 0, 0, -1, 0,  1, -1, 1, -1, 1,  -1, 1, -1,
                0, 0, 0, 0, 1,  -1, 1, -1, 1, 1,  -1, -1, 0};
int Zoff[27] = {0, 0,  1, 0,  0, -1, 0,  0,  0, 0,  1, 1,  -1, -1,
                1, -1, 1, -1, 1, 1,  -1, -1, 1, -1, 1, -1, 0};

/***
 *	Parameters for kinetic modelling ---- maturity approach
 ***/
int Indx[3];
float End_time, Cracktime;
float Temp_0, Temp_0_agg, Temp_cur, Temp_cur_b, Temp_cur_agg, Time_step = 0.0;
float Time_cur, *TimeHistory, E_act, Beta;
float W_to_c = 0.0, W_to_s = 0.0, S_to_c, Krate, CalKrate;
float Totfract = 1.0;
float Tfractw04 = 0.438596;
float Tfractw05 = 0.384615;
float Pfractw05 = 0.615385;
float Surffract, Pfract, Sulf_conc;
int Scntcement = 0, Scnttotal = 0, TimeCalibrationMethod;
float U_coeff = 0.0, U_coeff_agg = 0.0, T_ambient = 25.;
float Alpha, Alpha_cur, Alpha_max, Alpha_fa_cur, Alpha_fa_vol;
float E_act_pozz, E_act_slag;
float Bvec[3];
double Mass_water, Mass_fill, Cemmass, Mass_agg, Cp_b, Heat_old, Heat_new;
double CH_mass, Mass_CH, Mass_fill_pozz, Cemmasswgyp, Heat_cf, Chs_new,
    Flyashmass;
double Flyashvol;

/***
 * Parameters for holding experimental calorimetric data
 * to be used to calibrate early age time
 ***/
int NDataLines, CurDataLine = 1;
float DataMeasuredAtTemperature, DataFinalTemperature, *DataTime, *DataValue;

/***
 *	Distance from dissolution source within which dissolved
 *	CSH must be located (Default is 17 in older versions)
 *	Can vary as a function of pH.
 ***/
int Distloccsh;

/***
 *	Probability of direct topochemical conversion of anhydrous
 *	C3S and C2S to CSH.  Can vary depending on pH.
 ***/
float Pdirectcsh;

/***
 *	Mass of original dry cement at T = 105 C and 1000 C
 *	Used for calculation of non-evaporable water
 ***/
double Mass_105, Mass_1000;

/***
 *	Non-evaporable water relative to initial and
 *	ignited cement, respectively
 ***/
float Wn_o, Wn_i;

/***
 *	Average (mean) cement density in g/cm^3;
 *	Calculated during first cycle in function dissolve.
 *	Default guess given here for safety.
 ***/
float Meancemdens = 3.2;

/* Arrays for variable CSH molar volume and water consumption */
float Heatsum, Molesh2o, Saturation = 1.0;

/* Arrays for dissolution probabilities for each phase */
float Gypabsprob, Psfume, Psfnuc, Pamsil;

/* Solubility flags and diffusing species created for each phase */
/* Also flag for C1.7SH4.0 to C1.1SH3.9 conversion */
int Csh2flag, Adiaflag, Chflag, Nummovsl;
float MovieFrameFreq, NextMovieTime, NextImageTime;

/* Cs_acc increases Disprob[C3S] and Disprob[C2S] if gypsum is present */
float Cs_acc = 1.0;

/* Ca_acc increases Disprob[C3A] and Disprob[C4AF] if gypsum is present */
float Ca_acc = 1.0;

/* Number of CSH seeds per mL of mix water */
float Csh_seeds = 0.0;
float PCSHseednuc = 0.0;

/* Fraction of C3A that is orthorhombic instead of cubic */
float Oc3afrac = 0.0;

/* Gel porosity of CSH, POZZCSH, and SLAGCSH */
float CSH_Porosity = 0.38;
float POZZCSH_Porosity = 0.20;
float SLAGCSH_Porosity = 0.20;

float Disbias = 30.0;
float Dismin = 0.001;
float Dismin2 = 0.00025;
float Disminslag = 0.0001;
float Disminasg = 0.0005;
float Dismincas2 = 0.0005;
float Dismin_c3a = 0.002;
float Dismin_c4af = 0.0005;
double Gsratio2 = 0.0;

float Maxdiffsteps = 500;

/* Slag probabilities */
float P1slag; /* Probability SLAG is converted to SLAGCSH */
float P2slag; /* Probability SLAG is converted to POROSITY or EMPTYP */
float P3slag; /* Probability adjoining pixel is converted to SLAGCSH */
float P4slag; /* Probability CH is consumed during SLAG reaction */
float P5slag; /* Probability a C3A diffusing species is created */

/* Ca/Si ratios for SLAG and SLAGCSH */
float Slagcasi, Slaghydcasi;
float Slagc3a;   /* C3A/slag molar ratio */
float Siperslag; /* S ratio of SLAG (per mole) */
float Slagreact; /* Base dissolution reactivity factor for SLAG */
int DIFFCHdeficit = 0, Slaginit = 0; /* Deficit in CH due to SLAG reaction */
int Slagcum = 0, Chgone = 0, Nucsulf2gyps = 0;
int Nch_slag = 0; /* number of CH consumed by SLAG reaction */
int Sulf_cur = 0;
int Sulf_solid;

/***
 *	Keeps track of the relative volume fraction of
 *	porosity each cycle.  Gets set every cycle in
 *	the function dissolve.
 *
 *	4 Apr 2003
 ***/

float Relvfpores;

/***
 *	Define maximum number of diffusing species of each kind
 *	to keep them from filling the pore space.  Should scale
 *	with the pore volume, which in turn scales with system
 *	size (Isizemag is the actual system size divided by 1E6)
 ***/
int Dk2so4max, Dna2so4max; /* Added 3 June 2004 */
int Dettrmax, Dgypmax, Dcaco3max, Dcacl2max, Dcas2max, Dasmax;

/***
 *	Control the maximum concentration of CH diffusing species
 *	by defining a critical concentration above which the
 *	pore solution concentration decreases due to CH precipitation
 *	In other words, this parameter Chcrit specifies the solubility
 *	limit of CH
 ***/
float Chcrit;

/***
 *	Allow limited dissolution of hydrogarnet (C3AH6) to provide a
 *	mechanism by which it may react with sulfates
 ***/
float C3ah6crit;

/***
 *	Scale factors for determining transition between induction
 *	and acceleration of silicate hydration.  Cshscale is the
 *	CSH required to terminate induction
 ***/
float Cshscale;

/***
 *	Scale factor for hydrogarnet controlling induction
 *	of aluminates
 ***/
float C3ah6_scale;

/* Random number seed */
int Iseed;
int *Seed;

/* Variables for alkali predictions */
float PH_cur, Totsodium, Totpotassium, Rssodium, Rspotassium;
float Releasedk, Releasedna;
float Sodiumhydrox, Potassiumhydrox;
float Rsk_released = 0.0, Rsna_released = 0.0;
float Totfasodium, Totfapotassium, Rsfasodium, Rsfapotassium;

/* Array for whether pH influences phase solubility or reactivity */
float FitpH[NSPHASES + 1][2][3], PHcoeff[NSPHASES + 1][3];
float Molarvcshcoeff_T, Watercshcoeff_T;
float Molarvcshcoeff_pH, Watercshcoeff_pH;
float Molarvcshcoeff_sulf;
int PHactive, Resatcyc, Cshgeom;

/* Choices for C-S-H growth morphology */
const int RANDOM = 0;
const int PLATE = 1;

/* Make Conccaplus global to speed up execution and Moles_syn_precip */
/* global to accumulate properly */
double Conccaplus = 0.0, Moles_syn_precip = 0.0, Concsulfate = 0.0;
double Conductivity, Concnaplus, Conckplus, Concohminus;
double ActivityCa, ActivityOH, ActivitySO4, ActivityK;
int Primevalues[6] = {2, 3, 5, 7, 11, 13};
int Cshboxsize;

/* Percolation global variables */
int Nphc[3];
double Con_fracp[3], Con_fracs[3];

struct Ants *Headant, *Tailant;
struct Alksulf *Headnas, *Tailnas;
struct Alksulf *Headks, *Tailks;

/* Boolean variables to keep track of whether slag and fly ash
   are present in the microstructure */

int SlagIsPresent, FlyashIsPresent;

/* File names */
char Datafilename[MAXSTRING], Fileoname[MAXSTRING], Moviename[MAXSTRING];
char Parname[MAXSTRING], Micname[MAXSTRING], Phrname[MAXSTRING];
char Cmdnew[MAXSTRING], Fileroot[MAXSTRING];
char Imageindexname[MAXSTRING];
char Filesep;

/* File pointers */
FILE *Imageindexfile, *Datafile, *Movfile, *Micfile, *Parfile;

/* Special directories */
char Micdir[MAXSTRING], Outputdir[MAXSTRING];

/* Progress file for taskbar functionality */
char Progfilename[MAXSTRING];
FILE *Fprog;
