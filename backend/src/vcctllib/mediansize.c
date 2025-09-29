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
#include <string.h>

double mediansize(FILE *fpin) {
  char buff[500], *newstring;
  double vollo, diamlo, diamhi, volhi;
  double answer = -1.0;
  const double defaultdiam = 10.0;

  if (!fpin) {
    return (answer);
  } else {
    fprintf(stderr, "\nI am about to read the first line");
    fflush(stderr);
    fread_string(fpin, buff); /* read and discard header */
    fprintf(stderr, "\n%s", buff);
    fflush(stderr);
  }

  diamhi = volhi = 0.0;
  while (!feof(fpin)) {
    fread_string(fpin, buff);
    fprintf(stderr, "\n%s", buff);
    fflush(stderr);
    if (!feof(fpin)) {
      newstring = strtok(buff, ",");
      fprintf(stderr, "\n\t%s", newstring);
      diamlo = diamhi;
      vollo = volhi;
      diamhi = atof(newstring);
      newstring = strtok(NULL, ",");
      fprintf(stderr, "\t%s", newstring);
      volhi += atof(newstring);
      if (volhi >= 0.5) {
        answer = diamlo + (diamhi - diamlo) * (0.5 - vollo) / (volhi - vollo);
        return (answer);
      }
    }
  }
  /* To get this far means that the psd data were not normalized */
  /* Issue a warning and then return a default anwer */
  fprintf(stderr,
          "WARNING: Cement psd data were not normalized. Returning a default "
          "median size of %.2f micrometers",
          defaultdiam);
  return (defaultdiam);
}
