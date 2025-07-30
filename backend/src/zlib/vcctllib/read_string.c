/******************************************************************************
 *	Function read_string for linux reads a string from stdin, with the
 *possibility that the string contains spaces, thus rendering scanf useless.
 *
 * 	Arguments:	pointer to character array
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
#include <string.h>

void read_string(char *chstr, unsigned int size) {
  unsigned int i = 0;
  if (fgets(chstr, size, stdin)) {
    char *newline = strchr(chstr, '\n'); /* check for trailing newline */
    if (newline) {
      *newline = '\0'; /* replace newline with terminating null */
    }
  }
  return;
}
