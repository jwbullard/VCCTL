/******************************************************************************
 *	Function skip_imgheader skips over the header information in
 *	a microstructure file to the first line of data
 *
 * 	Arguments:	file pointer
 *
 *	Returns:	nothing
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
#include <string.h>

void skip_imgheader(FILE *fpin) {
  register int i;
  int done;
  char buff[MAXSTRING];

  done = 0;
  i = 0;
  while (!done && i < 10) {
    i++;
    fscanf(fpin, "%s", buff);
    if (!strcmp(buff, IMGRESSTRING)) {
      fscanf(fpin, "%s", buff);
      done = 1;
    }
  }

  return;
}
