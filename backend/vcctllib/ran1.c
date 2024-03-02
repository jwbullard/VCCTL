/***
 *	ran1
 *
 * 	Generate a pseudo-random number in the
 * 	interval [0.0,1.0]
 *
 * 	Taken directly from
 *
 * 	W.H. Press, S.A. Teukolsky, W.T. Vetterling, and B.P. Flannery.
 * 	"Numerical Recipes in C".  2nd Edition. Cambridge
 * 	University Press,	London, 1997.
 *
 * 	Arguments:	int seed
 *
 * 	Returns:	float random number
 *
 *	Calls:		passone, loccsch, makeinert
 *	Called by:	main program
 ***/

#include "../include/vcctl.h"

#define IA 16807
#define IM 2147483647
#define IQ 127773
#define IR 2836
#define NTAB 32
#define EPS (1.2E-07)
#define MAX(a, b) (a > b) ? a : b
#define MIN(a, b) (a < b) ? a : b

double ran1(int *idum) {
  int j, k;
  static int iv[NTAB], iy = 0;
  static double NDIV = 1.0 / (1.0 + (IM - 1.0) / NTAB);
  static double RNMX = (1.0 - EPS);
  static double AM = (1.0 / IM);

  if ((*idum <= 0) || (iy == 0)) {
    *idum = MAX(-*idum, *idum);

    for (j = NTAB + 7; j >= 0; j--) {
      k = *idum / IQ;
      *idum = IA * (*idum - k * IQ) - IR * k;
      if (*idum < 0)
        *idum += IM;
      if (j < NTAB)
        iv[j] = *idum;
    }

    iy = iv[0];
  }

  k = *idum / IQ;
  *idum = IA * (*idum - k * IQ) - IR * k;
  if (*idum < 0)
    *idum += IM;
  j = iy * NDIV;
  iy = iv[j];
  iv[j] = *idum;
  return MIN(AM * iy, RNMX);
}
