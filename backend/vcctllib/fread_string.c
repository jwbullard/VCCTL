/******************************************************************************
 *	Function fread_stdring reads a string from a file, with the possibility
 *	that the string contains spaces, thus rendering scanf useless.
 *
 * 	Arguments:	File pointer
 * 	            pointer to character array
 *
 *	Returns:	Nothing
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
 *	28 October 2005
 ******************************************************************************/
#include "../include/vcctl.h"
#include <stdio.h>

void fread_string(FILE *fpin, char *chstr) {
  fflush(stdout);
  fgets(chstr, (int)MAXSTRING, fpin);
}
