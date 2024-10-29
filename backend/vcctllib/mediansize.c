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
  char ch, buff[MAXSTRING], instring[MAXSTRING];
  double vollo, diamlo, diamhi, volhi;
  double answer = -1.0;

  if (!fpin)
    return (answer);

  ch = getc(fpin);
  if (ch != '0' && ch != '1' && ch != '2' && ch != '3' && ch != '4' &&
      ch != '5' && ch != '6' && ch != '7' && ch != '8' && ch != '9') {
    fread_string(fpin, instring); /* read and discard header */
  } else {
    rewind(fpin);
  }

  diamhi = volhi = 0.0;
  while (!feof(fpin) && answer < 0.0) {
    fscanf(fpin, "%s %s", buff, instring);
    if (!feof(fpin)) {
      diamlo = diamhi;
      vollo = volhi;
      diamhi = atof(buff);
      volhi += atof(instring);
      if (volhi >= 0.5) {
        answer = diamlo + (diamhi - diamlo) * (0.5 - vollo) / (volhi - vollo);
      }
    }
  }

  return (answer);
}
