/******************************************************************************
 *	Function id2phasename takes as input the integer id read from a
 *	microstructure file, and then converts it to the appropriate name
 *	of the phase associated with that id value.
 *
 * 	Arguments:	int initial phase id
 *
 * 	Returns:	char *name of the phase
 *
 *	Programmer:	Jeffrey W. Bullard
 *				NIST
 *				100 Bureau Drive, Stop 8615
 *				Gaithersburg, Maryland  20899-8615
 *				USA
 *
 *				Phone:	301.975.5725
 *				Fax:	301.990.6891
 *				bullard@nist.gov
 *
 *	16 March 2004
 ******************************************************************************/
#include "../include/vcctl.h"
#include <stdio.h>

void id2phasename(int curid, char *phasename) {
  switch (curid) {
  case POROSITY:
    sprintf(phasename, "POROSITY");
    break;
  case C3S:
    sprintf(phasename, "C3S");
    break;
  case C2S:
    sprintf(phasename, "C2S");
    break;
  case C3A:
    sprintf(phasename, "C3A");
    break;
  case OC3A:
    sprintf(phasename, "OC3A");
    break;
  case C4AF:
    sprintf(phasename, "C4AF");
    break;
  case K2SO4:
    sprintf(phasename, "K2SO4");
    break;
  case NA2SO4:
    sprintf(phasename, "NA2SO4");
    break;
  case GYPSUM:
    sprintf(phasename, "GYPSUM");
    break;
  case HEMIHYD:
    sprintf(phasename, "HEMIHYD");
    break;
  case ANHYDRITE:
    sprintf(phasename, "ANHYDRITE");
    break;
  case SFUME:
    sprintf(phasename, "SFUME");
    break;
  case INERT:
    sprintf(phasename, "INERT");
    break;
  case SLAG:
    sprintf(phasename, "SLAG");
    break;
  case INERTAGG:
    sprintf(phasename, "AGG");
    break;
  case ASG:
    sprintf(phasename, "ASG");
    break;
  case CAS2:
    sprintf(phasename, "CAS2");
    break;
  case AMSIL:
    sprintf(phasename, "AMSIL");
    break;
  case FAC3A:
    sprintf(phasename, "FAC3A");
    break;
  case FLYASH:
    sprintf(phasename, "FLYASH");
    break;
  case CH:
    sprintf(phasename, "CH");
    break;
  case CSH:
    sprintf(phasename, "CSH");
    break;
  case C3AH6:
    sprintf(phasename, "C3AH6");
    break;
  case ETTR:
    sprintf(phasename, "ETTR");
    break;
  case ETTRC4AF:
    sprintf(phasename, "ETTRC4AF");
    break;
  case AFM:
    sprintf(phasename, "AFM");
    break;
  case FH3:
    sprintf(phasename, "FH3");
    break;
  case POZZCSH:
    sprintf(phasename, "POZZCSH");
    break;
  case SLAGCSH:
    sprintf(phasename, "SLAGCSH");
    break;
  case CACL2:
    sprintf(phasename, "CACL2");
    break;
  case FRIEDEL:
    sprintf(phasename, "FRIEDEL");
    break;
  case STRAT:
    sprintf(phasename, "STRAT");
    break;
  case GYPSUMS:
    sprintf(phasename, "GYPSUMS");
    break;
  case ABSGYP:
    sprintf(phasename, "ABSGYP");
    break;
  case CACO3:
    sprintf(phasename, "CACO3");
    break;
  case AFMC:
    sprintf(phasename, "AFMC");
    break;
  case BRUCITE:
    sprintf(phasename, "BRUCITE");
    break;
  case MS:
    sprintf(phasename, "MS");
    break;
  case FREELIME:
    sprintf(phasename, "FREELIME");
    break;
  case DIFFCSH:
    sprintf(phasename, "DIFFCSH");
    break;
  case DIFFCH:
    sprintf(phasename, "DIFFCH");
    break;
  case DIFFGYP:
    sprintf(phasename, "DIFFGYP");
    break;
  case DIFFC3A:
    sprintf(phasename, "DIFFC3A");
    break;
  case DIFFC4A:
    sprintf(phasename, "DIFFC4A");
    break;
  case DIFFFH3:
    sprintf(phasename, "DIFFFH3");
    break;
  case DIFFETTR:
    sprintf(phasename, "DIFFETTR");
    break;
  case DIFFCACO3:
    sprintf(phasename, "DIFFCACO3");
    break;
  case DIFFAS:
    sprintf(phasename, "DIFFAS");
    break;
  case DIFFANH:
    sprintf(phasename, "DIFFANH");
    break;
  case DIFFHEM:
    sprintf(phasename, "DIFFHEM");
    break;
  case DIFFCAS2:
    sprintf(phasename, "DIFFCAS2");
    break;
  case DIFFCACL2:
    sprintf(phasename, "DIFFCACL2");
    break;
  case DIFFSO4:
    sprintf(phasename, "DIFFSO4");
    break;
  case DRIEDP:
    sprintf(phasename, "DRIEDP");
    break;
  case EMPTYDP:
    sprintf(phasename, "EMPTYDP");
    break;
  case EMPTYP:
    sprintf(phasename, "EMPTYP");
    break;
  case CRACKP:
    sprintf(phasename, "CRACKP");
    break;
  default:
    sprintf(phasename, "UNKNOWN");
    break;
  }
}
