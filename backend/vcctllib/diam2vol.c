/******************************************************************************
 *	Function diam2vol converts sphere diameter to number of pixels
 *
 * 	Arguments:	float diameter of real sphere
 *
 * 	Returns:	int number of pixels in digitized sphere
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
 *       Added to VCCTL library on 13 December 2013
 ******************************************************************************/
#include "../include/vcctl.h"
#include <math.h>

int diam2vol(float diameter) {
  int count = 0;
  int i, j, k;
  int idiam, irad;
  float dist, ftmp, offset;
  float xdist, ydist, zdist;

  idiam = (int)(diameter + 0.5);
  if ((idiam % 2) == 0) {
    offset = -0.5;
    irad = idiam / 2;
  } else {
    offset = 0.0;
    irad = (idiam - 1) / 2;
  }
  /* radius = 0.5 * diameter; */

  for (k = -(irad); k <= (irad); k++) {
    ftmp = (float)(k - offset);
    zdist = ftmp * ftmp;
    for (j = -(irad); j <= (irad); j++) {
      ftmp = (float)(j - offset);
      ydist = ftmp * ftmp;
      for (i = -(irad); i <= (irad); i++) {
        ftmp = (float)(i - offset);
        xdist = ftmp * ftmp;
        dist = sqrt(xdist + ydist + zdist);
        if ((dist - 0.5) <= ((float)irad))
          count++;
      }
    }
  }

  return (count);
}
