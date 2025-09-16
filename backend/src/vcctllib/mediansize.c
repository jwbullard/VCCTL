/******************************************************************************
 *	Function mediansize reads PSD file pointed to by argument and
 *	calculates the median diameter.
 *
 * 	Arguments:	file pointer
 *
 *	Returns:	double median size
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
#include <stdlib.h>

double mediansize(FILE *fpin) {
  char *instring, *newstring;
  double vollo, diamlo, diamhi, volhi;
  double answer = -1.0;

  if (!fpin)
    return (answer);

  diamhi = volhi = 0.0;
  while (!feof(fpin)) {
    fread_string(fpin, instring); /* read and discard header */
    if (!feof(fpin)) {
      newstring = strtok(instring, ",");
      diamlo = diamhi;
      vollo = volhi;
      diamhi = atof(newstring);
      newstring = strtok(NULL, ",");
      volhi += atof(newstring);
      if (volhi >= 0.5) {
        answer = diamlo + (diamhi - diamlo) * (0.5 - vollo) / (volhi - vollo);
      }
    }
  }
  return (answer);
}
