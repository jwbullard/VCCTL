/******************************************************************************
 *	Function convert_id takes as input the integer id read from a
 *	microstructure file, and then converts it to the appropriate value
 *	based on the discrepancy between the current version of VCCTL and the
 *	version of VCCTL under which the microstructure file was created.
 *
 * 	Arguments:	int initial phase id
 * 				float version of VCCTL detected
 *
 * 	Returns:	int new phase id
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

int convert_id(int curid, float version) {
  int newid, ver;

  ver = (int)version;
  newid = curid;

  switch (ver) {
  case 2:
    if (curid > 4) {
      switch (curid) {
      case 5:
        newid = GYPSUM;
        break;
      case 6:
        newid = HEMIHYD;
        break;
      case 7:
        newid = ANHYDRITE;
        break;
      case 8:
        newid = SFUME;
        break;
      case 9:
        newid = INERT;
        break;
      case 10:
        newid = SLAG;
        break;
      case 11:
        newid = ASG;
        break;
      case 12:
        newid = CAS2;
        break;
      case 13:
        newid = CH;
        break;
      case 14:
        newid = CSH;
        break;
      case 15:
        newid = C3AH6;
        break;
      case 16:
        newid = ETTR;
        break;
      case 17:
        newid = ETTRC4AF;
        break;
      case 18:
        newid = AFM;
        break;
      case 19:
        newid = FH3;
        break;
      case 20:
        newid = POZZCSH;
        break;
      case 21:
        newid = SLAGCSH;
        break;
      case 22:
        newid = CACL2;
        break;
      case 23:
        newid = FRIEDEL;
        break;
      case 24:
        newid = STRAT;
        break;
      case 25:
        newid = GYPSUMS;
        break;
      case 26:
        newid = CACO3;
        break;
      case 27:
        newid = AFMC;
        break;
      case 28:
        newid = INERTAGG;
        break;
      case 29:
        newid = ABSGYP;
        break;
      case 30:
        newid = DIFFCSH;
        break;
      case 31:
        newid = DIFFCH;
        break;
      case 32:
        newid = DIFFGYP;
        break;
      case 33:
        newid = DIFFC3A;
        break;
      case 34:
        newid = DIFFC4A;
        break;
      case 35:
        newid = DIFFFH3;
        break;
      case 36:
        newid = DIFFETTR;
        break;
      case 37:
        newid = DIFFCACO3;
        break;
      case 38:
        newid = DIFFAS;
        break;
      case 39:
        newid = DIFFANH;
        break;
      case 40:
        newid = DIFFHEM;
        break;
      case 41:
        newid = DIFFCAS2;
        break;
      case 42:
        newid = DIFFCACL2;
        break;
      case 45:
        newid = EMPTYP;
        break;
      default:
        break;
      }
    }
    break;
  case 3:
    if (curid > 4) {
      switch (curid) {
      case 5:
        newid = GYPSUM;
        break;
      case 6:
        newid = HEMIHYD;
        break;
      case 7:
        newid = ANHYDRITE;
        break;
      case 8:
        newid = SFUME;
        break;
      case 9:
        newid = INERT;
        break;
      case 10:
        newid = SLAG;
        break;
      case 11:
        newid = INERTAGG;
        break;
      case 12:
        newid = ASG;
        break;
      case 13:
        newid = CAS2;
        break;
      case 14:
        newid = FAC3A;
        break;
      case 15:
        newid = FLYASH;
        break;
      case 16:
        newid = CH;
        break;
      case 17:
        newid = CSH;
        break;
      case 18:
        newid = C3AH6;
        break;
      case 19:
        newid = ETTR;
        break;
      case 20:
        newid = ETTRC4AF;
        break;
      case 21:
        newid = AFM;
        break;
      case 22:
        newid = FH3;
        break;
      case 23:
        newid = POZZCSH;
        break;
      case 24:
        newid = SLAGCSH;
        break;
      case 25:
        newid = CACL2;
        break;
      case 26:
        newid = FRIEDEL;
        break;
      case 27:
        newid = STRAT;
        break;
      case 28:
        newid = GYPSUMS;
        break;
      case 29:
        newid = ABSGYP;
        break;
      case 30:
        newid = CACO3;
        break;
      case 31:
        newid = AFMC;
        break;
      case 32:
        newid = BRUCITE;
        break;
      case 33:
        newid = MS;
        break;
      case 34:
        newid = DIFFCSH;
        break;
      case 35:
        newid = DIFFCH;
        break;
      case 36:
        newid = DIFFGYP;
        break;
      case 37:
        newid = DIFFC3A;
        break;
      case 38:
        newid = DIFFC4A;
        break;
      case 39:
        newid = DIFFFH3;
        break;
      case 40:
        newid = DIFFETTR;
        break;
      case 41:
        newid = DIFFCACO3;
        break;
      case 42:
        newid = DIFFAS;
        break;
      case 43:
        newid = DIFFANH;
        break;
      case 44:
        newid = DIFFHEM;
        break;
      case 45:
        newid = DIFFCAS2;
        break;
      case 46:
        newid = DIFFCACL2;
        break;
      case 47:
        newid = DRIEDP;
        break;
      case 48:
        newid = EMPTYDP;
        break;
      case 49:
        newid = EMPTYP;
        break;
      default:
        break;
      }
    }
    break;
  default:
    if (curid > 4 && curid < 50) {
      newid = curid + 2;
      break;
    } else if (curid >= 50) {
      newid = curid + 3;
    }
    break;
  }

  return newid;
}
