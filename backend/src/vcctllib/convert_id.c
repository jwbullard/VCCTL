/******************************************************************************
 *	Function convert_id takes as input the integer id read from a
 *	microstructure file, and then converts it to the appropriate value
 *	based on the discrepancy between the current version of VCCTL and the
 *	version of VCCTL under which the microstructure file was created.
 *
 * 	Arguments:	int initial phase id
 * 				float version of VCCTL detected
 *
 * 	Returns:	int new phase id
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

int convert_id(int curid, float version) { return curid; }
