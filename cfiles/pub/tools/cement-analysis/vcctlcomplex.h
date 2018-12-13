/******************************************************************
*	Declarations of functions relating to complex numbers
*	in the vcctl library.  All the function definitions
*	associated with these declarations are contained in the
*	source code complex.c
*
*	Programmer:	Jeffrey W. Bullard
*				NIST
*				100 Bureau Drive Stop 8615
*				Gaithersburg, MD  20899 USA
*
*				301.975.5725
*				bullard@nist.gov
*
*	23 March 2004
******************************************************************/

typedef struct FCOMPLEX {float r,i;} fcomplex;

fcomplex Cadd(fcomplex a, fcomplex b);
fcomplex Csub(fcomplex a, fcomplex b);
fcomplex Cmul(fcomplex a, fcomplex b);
fcomplex Complex(float re, float im);
fcomplex Conjg(fcomplex z);
fcomplex Cdiv(fcomplex a, fcomplex b);
float Cabs(fcomplex z);
fcomplex Csqrt(fcomplex z);
fcomplex RCmul(float x, fcomplex a);
fcomplex **complexmatrix(long nrl, long nrh, long ncl, long nch);
void free_complexmatrix(fcomplex **m, long nrl, long nrh, long ncl, long nch);
