#include "../include/vcctl.h"
#include <stdio.h>

/******************************************************************************
 *	Function bailout prints error message to stdout
 *
 * 	Arguments:	char string of program name
 * 				char error message
 *
 * 	Returns:	nothing
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
void bailout(char *name, char *msg) {
  printf("\nERROR in %s:", name);
  printf("\n\t%s", msg);
  printf("\n\tExiting now.\n");
  fflush(stdout);
  return;
}

/******************************************************************************
 *	Function warning prints error message to stdout
 *
 * 	Arguments:	char string of program name
 * 				char error message
 *
 * 	Returns:	nothing
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
void warning(char *name, char *msg) {
  printf("\nWARNING in %s:", name);
  printf("\n\t%s", msg);
  printf("\n\tCheck integrity of output files\n");
  fflush(stdout);
  return;
}
