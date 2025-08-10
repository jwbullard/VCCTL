#ifndef VCCTL_H
#define VCCTL_H
/***
 *	This is the public header file required for
 *	VCCTL programs.  Every VCCTL program that wishes
 *	to operate within the VCCTL system must include
 *	this header file
 *
 *	Programmer:  Jeffrey W. Bullard
 *				 NIST
 *				 100 Bureau Drive Stop 8615
 *				 Gaithersburg, MD  20899-8615
 *
 *				 Phone:	301.975.5725
 *				 Fax:	301.990.6892
 *				 bullard@nist.gov
 *
 *				 15 March 2004
 ***/
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/***
 *	Version number string and version number
 *	for identifying the version under which a
 *	particular file was created
 ***/
#define VERSIONSTRING "Version:"
#define VERSIONNUMBER "7.0"

#define MAXSTRING 128 /* maximum length of strings */

/***
 *	The gnuplot command
 ***/
#define PLOT "/usr/bin/gnuplot"

/***
 *	ImageMagick convert command
 ***/
#define CONVERT "/usr/bin/convert"

/***
 *	Shell command
 ***/
#define SHELL "bash"

/*******************************************************
 * Variables related to system size and
 * resolution
 *******************************************************/

#define MAXSIZE 400 /* maximum system size in pixels per dimension */
#define DEFAULTSYSTEMSIZE 100

#define LOWRES 1.00
#define MEDLORES 0.75
#define MEDHIRES 0.50
#define HIGHRES 0.25

#define DEFAULTRESOLUTION LOWRES

#define XSIZESTRING "X_Size:"
#define YSIZESTRING "Y_Size:"
#define ZSIZESTRING "Z_Size:"
#define IMGSIZESTRING "Image_Size:"
#define IMGRESSTRING "Image_Resolution:"

/***
 *	Pre-defined strings for info files
 ***/
#define ONEPIXBIASSTRING "One_pixel_bias:"
#define AGGTHICKSTRING "Aggregate_thickness:"
#define PFILESTRING "Particle_file:"
#define NUM1PIXSTRING "One_pixel_particles:"
#define VFC3SSTRING "Vol_frac_C3S:"
#define VFC2SSTRING "Vol_frac_C2S:"
#define VFC3ASTRING "Vol_frac_C3A:"
#define VFC4AFSTRING "Vol_frac_C4AF:"
#define VFK2SO4STRING "Vol_frac_K2SO4:"
#define VFNA2SO4STRING "Vol_frac_NA2SO4:"
#define SFC3SSTRING "Surf_frac_C3S:"
#define SFC2SSTRING "Surf_frac_C2S:"
#define SFC3ASTRING "Surf_frac_C3A:"
#define SFC4ASTRING "Surf_frac_C4AF:"
#define SFK2SO4STRING "Surf_frac_K2SO4:"
#define SFNA2SO4STRING "Surf_frac_NA2SO4:"
#define VFGYPSTRING "Vol_frac_Dihydrate:"
#define VFHEMSTRING "Vol_frac_Hemihydrate:"
#define VFANHSTRING "Vol_frac_Anhydrite:"

/******************************************************
 * Define phase identifier for all species
 ******************************************************/

/***
 *	To add a new solid phase, insert its id before
 *	NSPHASES, and adjust the parameter directly
 *	underneath it.
 ***/

/***
 *	To add a new diffusing species, insert its id
 *	before NDIFFPHASES, and adjust the parameter
 *	directly underneath it.
 ***/

/***
 *	These are phases present in unhydrated
 *	blended cements
 ***/

#define POROSITY 0            /* 0 */
#define C3S POROSITY + 1      /* 1 */
#define C2S C3S + 1           /* 2 */
#define C3A C2S + 1           /* 3 */
#define C4AF C3A + 1          /* 4 */
#define K2SO4 C4AF + 1        /* 5 */
#define NA2SO4 K2SO4 + 1      /* 6 */
#define GYPSUM NA2SO4 + 1     /* 7 */
#define HEMIHYD GYPSUM + 1    /* 8 */
#define ANHYDRITE HEMIHYD + 1 /* 9 */
#define SFUME ANHYDRITE + 1   /* 10 */
#define INERT SFUME + 1       /* 11 */
#define SLAG INERT + 1        /* 12 */
#define INERTAGG SLAG + 1     /* 13 */

/***
 *	The next three phases are distributed
 *	primarily within flyash.  Other phases
 *	that are distributed within flyash are
 *	also found as species during hydration,
 *	such as CaCl2
 ***/

/* Aluminosilicate glass */
#define ASG INERTAGG + 1 /* 14 */
#define CAS2 ASG + 1     /* 15 */
#define AMSIL CAS2 + 1   /* 16 */
/* C3A phase within flyash */
#define FAC3A AMSIL + 1 /* 17 */

#define FLYASH FAC3A + 1 /* 18 */

/* Total number of "cement" phases */
#define NCEMPHASES FLYASH + 1

/***
 *	The following are hydration products
 ***/

#define CH FLYASH + 1  /* 19 */
#define CSH CH + 1     /* 20 */
#define C3AH6 CSH + 1  /* 21 */
#define ETTR C3AH6 + 1 /* 22 */

/* Iron-rich stable ettringite */
#define ETTRC4AF ETTR + 1 /* 23 */

#define AFM ETTRC4AF + 1    /* 24 */
#define FH3 AFM + 1         /* 25 */
#define POZZCSH FH3 + 1     /* 26 */
#define SLAGCSH POZZCSH + 1 /* 27 */
#define CACL2 SLAGCSH + 1   /* 28 */

/* Friedel's salt */
#define FRIEDEL CACL2 + 1 /* 29 */

/* Stratlingite (C2ASH8) */
#define STRAT FRIEDEL + 1 /* 30 */

/* Gypsum formed from hemihydrate and anhydrite */
#define GYPSUMS STRAT + 1  /* 31 */
#define ABSGYP GYPSUMS + 1 /* 32 */

#define CACO3 ABSGYP + 1 /* 33 */
#define AFMC CACO3 + 1   /* 34 */

/***
 *	Phases for chloride ingress model and
 *	sulfate attack model
 ***/
#define BRUCITE AFMC + 1 /* 35 */
#define MS BRUCITE + 1   /* 36 */

/* Free lime */
#define FREELIME MS + 1 /* 37 */

/* Orthorhombic C3A */
#define OC3A FREELIME + 1 /* 38 */

/* Number of SOLID phases (excludes saturated porosity */

#define NSPHASES OC3A /* 38 */

/***
 *	Diffusing species
 ***/
#define DIFFCSH NSPHASES + 1   /* 39 */
#define DIFFCH DIFFCSH + 1     /* 40 */
#define DIFFGYP DIFFCH + 1     /* 41 */
#define DIFFC3A DIFFGYP + 1    /* 42 */
#define DIFFC4A DIFFC3A + 1    /* 43 */
#define DIFFFH3 DIFFC4A + 1    /* 44 */
#define DIFFETTR DIFFFH3 + 1   /* 45 */
#define DIFFCACO3 DIFFETTR + 1 /* 46 */
#define DIFFAS DIFFCACO3 + 1   /* 47 */
#define DIFFANH DIFFAS + 1     /* 48 */
#define DIFFHEM DIFFANH + 1    /* 49 */
#define DIFFCAS2 DIFFHEM + 1   /* 50 */
#define DIFFCACL2 DIFFCAS2 + 1 /* 51 */
#define DIFFSO4 DIFFCACL2 + 1  /* 52 */

#define NDIFFPHASES DIFFSO4 + 1 /* 53 */

/***
 *	Special types of porosity
 ***/

#define DRIEDP NDIFFPHASES /* 53 */
#define EMPTYDP DRIEDP + 1 /* 54 */

/***
 *	Empty porosity due to self dessication
 ***/
#define EMPTYP EMPTYDP + 1 /* 55 */

/***
 *	Crack porosity, defined as the porosity
 *	created when the microstructure is cracked.
 *	Can be saturated or empty, depending on the
 *	application (24 May 2004)
 ***/
#define CRACKP EMPTYP + 1 /* 56 */

/***
 *	Offset for highlighting potentially
 *	soluble surface pixels in disrealnew
 ***/

#define OFFSET CRACKP + 1 /* 57 */

/***
 *	Total number of types of pixels, which
 *	INCLUDES diffusing species
 ***/
#define NDIFFUS OFFSET

#define SANDINCONCRETE OFFSET + 3 /* 60 */
#define COARSEAGG01INCONCRETE SANDINCONCRETE + 1
#define COARSEAGG02INCONCRETE COARSEAGG01INCONCRETE + 1
#define FINEAGG01INCONCRETE COARSEAGG02INCONCRETE + 1
#define FINEAGG02INCONCRETE FINEAGG01INCONCRETE + 1

#define NPHASES FINEAGG02INCONCRETE + 1

/*********************************************************
 * Defines all colors used in VCCTL
 *********************************************************/

#define SAT 255

#define R_BROWN 162
#define G_BROWN 117
#define B_BROWN 95

#define R_BLUE 0
#define G_BLUE 0
#define B_BLUE SAT

#define R_CFBLUE 0
#define G_CFBLUE 128
#define B_CFBLUE SAT

#define R_RED SAT
#define G_RED 0
#define B_RED 0

#define R_GREEN 0
#define G_GREEN SAT
#define B_GREEN 0

#define R_WHITE SAT
#define G_WHITE SAT
#define B_WHITE SAT

#define R_BLACK 0
#define G_BLACK 0
#define B_BLACK 0

#define R_AQUA 0
#define G_AQUA SAT
#define B_AQUA SAT

#define R_LTURQUOISE 174
#define G_LTURQUOISE 237
#define B_LTURQUOISE 237

#define R_YELLOW SAT
#define G_YELLOW SAT
#define B_YELLOW 0

#define R_LYELLOW SAT
#define G_LYELLOW SAT
#define B_LYELLOW SAT / 2

#define R_GOLD SAT
#define G_GOLD 215
#define B_GOLD 0

#define R_OLIVE SAT / 2
#define G_OLIVE SAT / 2
#define B_OLIVE 0

#define R_LOLIVE 150
#define G_LOLIVE 150
#define B_LOLIVE 0

#define R_DOLIVE SAT / 4
#define G_DOLIVE SAT / 4
#define B_DOLIVE 0

#define R_DBLUE 0
#define G_DBLUE 0
#define B_DBLUE SAT / 2

#define R_VIOLET SAT / 2
#define G_VIOLET 0
#define B_VIOLET SAT

#define R_LAVENDER 230
#define G_LAVENDER 230
#define B_LAVENDER 250

#define R_PLUM 238
#define G_PLUM 174
#define B_PLUM 238

#define R_FIREBRICK 178
#define G_FIREBRICK 34
#define B_FIREBRICK 34

#define R_MUTEDFIREBRICK 178
#define G_MUTEDFIREBRICK 128
#define B_MUTEDFIREBRICK 128

#define R_SEAGREEN SAT / 2
#define G_SEAGREEN 250
#define B_SEAGREEN SAT / 2

#define R_MAGENTA SAT
#define G_MAGENTA 0
#define B_MAGENTA SAT

#define R_ORANGE SAT
#define G_ORANGE 165
#define B_ORANGE 0

#define R_PEACH SAT
#define G_PEACH 170
#define B_PEACH 128

#define R_WHEAT 245
#define G_WHEAT 222
#define B_WHEAT 179

#define R_TAN 210
#define G_TAN 180
#define B_TAN 140

#define R_DGREEN 0
#define G_DGREEN 100
#define B_DGREEN 0

#define R_LGREEN SAT / 2
#define G_LGREEN SAT
#define B_LGREEN SAT / 2

#define R_LIME 51
#define G_LIME 205
#define B_LIME 51

#define R_DLIME 26
#define G_DLIME 103
#define B_DLIME 26

#define R_LLIME 128
#define G_LLIME 255
#define B_LLIME 0

#define R_LYELLOW SAT
#define G_LYELLOW SAT
#define B_LYELLOW SAT / 2

#define R_GRAY 178
#define G_GRAY 178
#define B_GRAY 178

#define R_DGRAY SAT / 4
#define G_DGRAY SAT / 4
#define B_DGRAY SAT / 4

#define R_CHARCOAL 50
#define G_CHARCOAL 50
#define B_CHARCOAL 50

#define R_LGRAY 3 * SAT / 4
#define G_LGRAY 3 * SAT / 4
#define B_LGRAY 3 * SAT / 4

#define R_DAQUA SAT / 4
#define G_DAQUA SAT / 2
#define B_DAQUA SAT / 2

#define R_SALMON SAT
#define G_SALMON SAT / 2
#define B_SALMON SAT / 2

#define R_SKYBLUE SAT / 4
#define G_SKYBLUE SAT / 2
#define B_SKYBLUE SAT

#define R_DPINK SAT
#define G_DPINK 0
#define B_DPINK SAT / 2

#define R_PINK SAT
#define G_PINK 105
#define B_PINK 180

#define R_ORANGERED SAT
#define G_ORANGERED 69
#define B_ORANGERED 0

#define HTMLCODE 0
#define PLAINCODE 1

/* typedefs */

/* A coloured pixel. */

typedef struct {
  uint8_t red;
  uint8_t green;
  uint8_t blue;
} pixel_t;

/* Support for image rendering */

/* A picture. */

typedef struct {
  pixel_t *pixels;
  size_t width;
  size_t height;
} bitmap_t;

/* Different types of arrays */

typedef struct {
  int xsize;
  int *val;
} Int1d;

typedef struct {
  int xsize;
  short int *val;
} ShortInt1d;

typedef struct {
  int xsize;
  long int *val;
} LongInt1d;

typedef struct {
  int xsize;
  float *val;
} Float1d;

typedef struct {
  int xsize;
  float *val;
} Double1d;

typedef struct {
  int xsize;
  pixel_t *val;
} Pixel1d;

typedef struct {
  int xsize;
  int ysize;
  int *val;
} Int2d;

typedef struct {
  int xsize;
  int ysize;
  short int *val;
} ShortInt2d;

typedef struct {
  int xsize;
  int ysize;
  long int *val;
} LongInt2d;

typedef struct {
  int xsize;
  int ysize;
  float *val;
} Float2d;

typedef struct {
  int xsize;
  int ysize;
  double *val;
} Double2d;

typedef struct {
  int xsize;
  int ysize;
  char *val;
} Char2d;

typedef struct {
  size_t x;
  size_t y;
  size_t z;
  int *val;
} Int3d;

typedef struct {
  int xsize;
  int ysize;
  int zsize;
  short int *val;
} ShortInt3d;

typedef struct {
  int xsize;
  int ysize;
  int zsize;
  long int *val;
} LongInt3d;

typedef struct {
  int xsize;
  int ysize;
  int zsize;
  float *val;
} Float3d;

typedef struct {
  int xsize;
  int ysize;
  int zsize;
  double *val;
} Double3d;

typedef struct {
  int xsize;
  int ysize;
  int zsize;
  char *val;
} Char3d;

/***
 *	Function declarations needed by VCCTL
 ***/
#include "vcctlcomplex.h"
#include "vcctlfuncs.h"

#endif
