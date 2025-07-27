/******************************************************************************
 *	Function gtime prints pretty version of time and date to stdout
 *
 * 	Arguments:	nothing
 *
 * 	Returns:	output char array
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
#include <stdio.h>
#include <stdlib.h>
#ifndef __included_time_h
#define __included_time_h
#include <time.h>
#endif
#include "../include/vcctl.h"

char *gtime(void) {
  struct tm *ptr;
  time_t lt;

  lt = time(NULL);
  ptr = localtime(&lt);
  return (asctime(ptr));
}
