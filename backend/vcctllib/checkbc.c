/******************************************************************************
 *	Function checkbc checks a value for whether it exists inside the
 *	system or outside, and then performs an arithmetic operation, based
 *	on periodic boundary conditions, to bring the value back within the
 *	system if necessary.
 *
 * 	Arguments:	int starting value
 * 				int system size
 *
 * 	Returns:	int value by which to adjust the starting value
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

int checkbc(int pos, int size) {
  int adj = 0;

  if (pos < 0) {
    adj = size;
  } else if (pos >= size) {
    adj = -(size);
  }

  return (adj);
}
