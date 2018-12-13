/******************************************************
*                                                                      
* memutil.c is a collection of functions designed to
* help with dynamic allocation of arrays of various
* dimensions and different data types
*
* General form of a function name is for the data type
* to come first:
*
* 	i = integer                      li = long integer
* 	si = short integer               f = float
* 	usi = unsigned short integer     c = char
*                                                                     
* This is immediately followed by the dimension:
*
* 	vector = 1-D
* 	square = 2-D of equal dimensions
* 	cube = 3-D of equal dimensions
* 	box = 3-D of unequal dimensions in x,y,z
*
*******************************************************/
#include <stdio.h>
#include <stdlib.h>
#include "vcctl.h"

/***
*	ivector
*
*	Routine to allocate memory for an 1D array of integers
*
*	Arguments:	int number of elements in array
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
int *ivector(long int size)
{
	int *iv;

	iv = (int *)calloc((size_t)size,sizeof(int));
	if (!iv) {
		printf("\n\nCould not allocate space for int vector.");
		return(NULL);
	}

	return(iv);
}

/***
*	sivector
*
*	Routine to allocate memory for an 1D array of short integers
*
*	Arguments:	int number of elements in array
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
short int *sivector(long int size)
{
	short int *iv;

	iv = (short int *)calloc((size_t)size,sizeof(short int));
	if (!iv) {
		printf("\n\nCould not allocate space for short int vector.");
		return(NULL);
	}

	return(iv);
}

/***
*	livector
*
*	Routine to allocate memory for an 1D array of long integers
*
*	Arguments:	int number of elements in array
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
long int *livector(long int size)
{
	long int *iv;

	iv = (long int *)calloc((size_t)size,sizeof(long int));
	if (!iv) {
		printf("\n\nCould not allocate space for long int vector.");
		return(NULL);
	}

	return(iv);
}

/***
*	fvector
*
*	Routine to allocate memory for an 1D array of floats
*
*	Arguments:	int number of elements in array
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
float *fvector(long int size)
{
	float *fv;

	fv = (float *)calloc((size_t)size,sizeof(float));
	if (!fv) {
		printf("\n\nCould not allocate space for float vector.");
		return(NULL);
	}

	return(fv);
}

/***
*	dvector
*
*	Routine to allocate memory for an 1D array of doubles
*
*	Arguments:	int number of elements in array
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
double *dvector(long int size)
{
	double *dv;

	dv = (double *)calloc((size_t)size,sizeof(double));
	if (!dv) {
		printf("\n\nCould not allocate space for double vector.");
		return(NULL);
	}

	return(dv);
}

/***
*	ldvector
*
*	Routine to allocate memory for an 1D array of long doubles
*
*	Arguments:	int number of elements in array
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
long double *ldvector(long int size)
{
	long double *ldv;

	ldv = (long double *)calloc((size_t)size,sizeof(long double));
	if (!ldv) {
		printf("\n\nCould not allocate space for long double vector.");
		return(NULL);
	}

	return(ldv);
}

/***
*	pixelvector
*
*	Routine to allocate memory for an 1D array of pixel_t elements
*
*	Arguments:	int number of elements in array
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
pixel_t *pixelvector(long int size)
{
	pixel_t *ptv;

	ptv = (pixel_t *)calloc((size_t)size,sizeof(pixel_t));
	if (!ptv) {
		printf("\n\nCould not allocate space for pixel_t vector.");
		return(NULL);
	}

	return(ptv);
}

/***
*	sisquare
*
*	Routine to allocate memory for an 2D square array of short
*	ints.  All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
short int **sisquare(long int size)
{
	long int i;
	short int **is;

	is = (short int **)malloc((size_t)size*sizeof(short int*));
	if (!is) {
		printf("\n\nCould not allocate space for row of square array.");
		return(NULL);
	}

	is[0] = (short int *)malloc((size_t)(size*size)*sizeof(short int));

	if (!is[0]) {
		printf("\n\nCould not allocate space for column of square array.");
		return(NULL);
	}

	for (i = 1; i < size; i++) {
		is[i] = is[i-1] + size;
	}

	return(is);
}

/***
*	sirect
*
*	Routine to allocate memory for an 2D rectangle array of short
*	ints.  All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
short int **sirect(long int xsize, long int ysize)
{
	long int i;
	short int **is;

	is = (short int **)malloc((size_t)xsize*sizeof(short int*));
	if (!is) {
		printf("\n\nCould not allocate space for row of rectangle array.");
		return(NULL);
	}

	is[0] = (short int *)malloc((size_t)(ysize*xsize)*sizeof(short int));

	if (!is[0]) {
		printf("\n\nCould not allocate space for column of rectangle array.");
		return(NULL);
	}

	for (i = 1; i < xsize; i++) {
		is[i] = is[i-1] + ysize;
	}

	return(is);
}

/***
*	irect
*
*	Routine to allocate memory for an 2D rectangle array of
*	ints.  All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
int **irect(long int xsize, long int ysize)
{
	long int i;
	int **is;

	is = (int **)malloc((size_t)xsize*sizeof(int*));
	if (!is) {
		printf("\n\nCould not allocate space for row of rectangle array.");
		return(NULL);
	}

	is[0] = (int *)malloc((size_t)(ysize*xsize)*sizeof(int));

	if (!is[0]) {
		printf("\n\nCould not allocate space for column of rectangle array.");
		return(NULL);
	}

	for (i = 1; i < xsize; i++) {
		is[i] = is[i-1] + ysize;
	}

	return(is);
}

/***
*	drect
*
*	Routine to allocate memory for an 2D rectangle array of doubles
*	All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
double **drect(long int xsize, long int ysize)
{
	long int i;
	double **is;

	is = (double **)malloc((size_t)xsize*sizeof(double*));
	if (!is) {
		printf("\n\nCould not allocate space for row of rectangle array.");
		return(NULL);
	}

	is[0] = (double *)malloc((size_t)(ysize*xsize)*sizeof(double));

	if (!is[0]) {
		printf("\n\nCould not allocate space for column of rectangle array.");
		return(NULL);
	}

	for (i = 1; i < xsize; i++) {
		is[i] = is[i-1] + ysize;
	}

	return(is);
}

/***
*	ccube
*
*	Routine to allocate memory for an 3D array of chars
*	All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
char ***ccube(long int size)
{
	long int i,j;
	char ***fc;

	fc = (char ***)malloc((size_t)size*sizeof(char**));
	if (!fc) {
		printf("\n\nCould not allocate space for row of cube.");
		return(NULL);
	}

	fc[0] = (char **)malloc((size_t)(size*size)*sizeof(char*));

	if (!fc[0]) {
		printf("\n\nCould not allocate space for column of cube.");
		return(NULL);
	}

	fc[0][0] = (char *)malloc((size_t)(size*size*size)*sizeof(char));

	if (!fc[0][0]) {
		printf("\n\nCould not allocate space for depth of cube.");
		return(NULL);
	}
	
	for (j = 1; j < size; j++) {
		fc[0][j] = fc[0][j-1] + size;
	}

	for (i = 1; i < size; i++) {
		fc[i] = fc[i-1] + size;
		fc[i][0] = fc[i-1][0] + (size*size);
		for (j = 1; j < size; j++) {
			fc[i][j] = fc[i][j-1] + size;
		}
	}

	return(fc);
}

/***
*	cbox
*
*	Routine to allocate memory for an 3D array of chars
*	All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
char ***cbox(long int xsize, long int ysize, long int zsize)
{
	long int i,j;
	char ***fc;

	fc = (char ***)malloc((size_t)xsize*sizeof(char**));
	if (!fc) {
		printf("\n\nCould not allocate space for row of box.");
		return(NULL);
	}

	fc[0] = (char **)malloc((size_t)(ysize*xsize)*sizeof(char*));

	if (!fc[0]) {
		printf("\n\nCould not allocate space for column of box.");
		return(NULL);
	}

	fc[0][0] = (char *)malloc((size_t)(zsize*ysize*xsize)*sizeof(char));

	if (!fc[0][0]) {
		printf("\n\nCould not allocate space for depth of box.");
		return(NULL);
	}
	
	for (j = 1; j < ysize; j++) {
		fc[0][j] = fc[0][j-1] + zsize;
	}

	for (i = 1; i < xsize; i++) {
		fc[i] = fc[i-1] + ysize;
		fc[i][0] = fc[i-1][0] + (zsize*ysize);
		for (j = 1; j < ysize; j++) {
			fc[i][j] = fc[i][j-1] + zsize;
		}
	}

	return(fc);
}

/***
*	sicube
*
*	Routine to allocate memory for an 3D array of short ints
*	All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
short int ***sicube(long int size)
{
	long int i,j;
	short int ***fc;

	fc = (short int ***)malloc((size_t)size*sizeof(short int**));
	if (!fc) {
		printf("\n\nCould not allocate space for row of cube.");
		return(NULL);
	}

	fc[0] = (short int **)malloc((size_t)(size*size)*sizeof(short int*));

	if (!fc[0]) {
		printf("\n\nCould not allocate space for column of cube.");
		return(NULL);
	}

	fc[0][0] = (short int *)malloc((size_t)(size*size*size)*sizeof(short int));

	if (!fc[0][0]) {
		printf("\n\nCould not allocate space for depth of cube.");
		return(NULL);
	}
	
	for (j = 1; j < size; j++) {
		fc[0][j] = fc[0][j-1] + size;
	}

	for (i = 1; i < size; i++) {
		fc[i] = fc[i-1] + size;
		fc[i][0] = fc[i-1][0] + (size*size);
		for (j = 1; j < size; j++) {
			fc[i][j] = fc[i][j-1] + size;
		}
	}

	return(fc);
}

/***
*	sibox
*
*	Routine to allocate memory for an 3D array of short ints
*	All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
short int ***sibox(long int xsize, long int ysize, long int zsize)
{
	long int i,j;
	short int ***fc;

	fc = (short int ***)malloc((size_t)xsize*sizeof(short int**));
	if (!fc) {
		printf("\n\nCould not allocate space for row of box.");
		return(NULL);
	}

	fc[0] = (short int **)malloc((size_t)(ysize*xsize)*sizeof(short int*));

	if (!fc[0]) {
		printf("\n\nCould not allocate space for column of box.");
		return(NULL);
	}

	fc[0][0] = (short int *)malloc((size_t)(zsize*ysize*xsize)*sizeof(short int));

	if (!fc[0][0]) {
		printf("\n\nCould not allocate space for depth of box.");
		return(NULL);
	}
	
	for (j = 1; j < ysize; j++) {
		fc[0][j] = fc[0][j-1] + zsize;
	}

	for (i = 1; i < xsize; i++) {
		fc[i] = fc[i-1] + ysize;
		fc[i][0] = fc[i-1][0] + (zsize*ysize);
		for (j = 1; j < ysize; j++) {
			fc[i][j] = fc[i][j-1] + zsize;
		}
	}

	return(fc);
}

/***
*	fcube
*
*	Routine to allocate memory for an 3D array of floats
*	All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
float ***fcube(long int size)
{
	long int i,j;
	float ***fc;

	fc = (float ***)malloc((size_t)size*sizeof(float**));
	if (!fc) {
		printf("\n\nCould not allocate space for row of fcube.");
		return(NULL);
	}

	fc[0] = (float **)malloc((size_t)(size*size)*sizeof(float*));

	if (!fc[0]) {
		printf("\n\nCould not allocate space for column of fcube.");
		return(NULL);
	}

	fc[0][0] = (float *)malloc((size_t)(size*size*size)*sizeof(float));

	if (!fc[0][0]) {
		printf("\n\nCould not allocate space for depth of fcube.");
		return(NULL);
	}
	
	for (j = 1; j < size; j++) {
		fc[0][j] = fc[0][j-1] + size;
	}

	for (i = 1; i < size; i++) {
		fc[i] = fc[i-1] + size;
		fc[i][0] = fc[i-1][0] + (size*size);
		for (j = 1; j < size; j++) {
			fc[i][j] = fc[i][j-1] + size;
		}
	}

	return(fc);
}

/***
*	fbox
*
*	Routine to allocate memory for an 3D array of floats
*	All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
float ***fbox(long int xsize, long int ysize, long int zsize)
{
	long int i,j;
	float ***fc;

	fc = (float ***)malloc((size_t)xsize*sizeof(float**));
	if (!fc) {
		printf("\n\nCould not allocate space for row of box.");
		return(NULL);
	}

	fc[0] = (float **)malloc((size_t)(ysize*xsize)*sizeof(float*));

	if (!fc[0]) {
		printf("\n\nCould not allocate space for column of box.");
		return(NULL);
	}

	fc[0][0] = (float *)malloc((size_t)(zsize*ysize*xsize)*sizeof(float));

	if (!fc[0][0]) {
		printf("\n\nCould not allocate space for depth of box.");
		return(NULL);
	}
	
	for (j = 1; j < ysize; j++) {
		fc[0][j] = fc[0][j-1] + zsize;
	}

	for (i = 1; i < xsize; i++) {
		fc[i] = fc[i-1] + ysize;
		fc[i][0] = fc[i-1][0] + (zsize*ysize);
		for (j = 1; j < ysize; j++) {
			fc[i][j] = fc[i][j-1] + zsize;
		}
	}

	return(fc);
}

/***
*	dbox
*
*	Routine to allocate memory for an 3D array of doubles
*	All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
double ***dbox(long int xsize, long int ysize, long int zsize)
{
	long int i,j;
	double ***fc;

	fc = (double ***)malloc((size_t)xsize*sizeof(double**));
	if (!fc) {
		printf("\n\nCould not allocate space for row of box.");
		return(NULL);
	}

	fc[0] = (double **)malloc((size_t)(ysize*xsize)*sizeof(double*));

	if (!fc[0]) {
		printf("\n\nCould not allocate space for column of box.");
		return(NULL);
	}

	fc[0][0] = (double *)malloc((size_t)(zsize*ysize*xsize)*sizeof(double));

	if (!fc[0][0]) {
		printf("\n\nCould not allocate space for depth of box.");
		return(NULL);
	}
	
	for (j = 1; j < ysize; j++) {
		fc[0][j] = fc[0][j-1] + zsize;
	}

	for (i = 1; i < xsize; i++) {
		fc[i] = fc[i-1] + ysize;
		fc[i][0] = fc[i-1][0] + (zsize*ysize);
		for (j = 1; j < ysize; j++) {
			fc[i][j] = fc[i][j-1] + zsize;
		}
	}

	return(fc);
}

/***
*	icube
*
*	Routine to allocate memory for an 3D array of ints
*	All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
int ***icube(long int size)
{
	long int i,j;
	int ***fc;

	fc = (int ***)malloc((size_t)size*sizeof(int**));
	if (!fc) {
		printf("\n\nCould not allocate space for row of icube.");
		return(NULL);
	}

	fc[0] = (int **)malloc((size_t)(size*size)*sizeof(int*));

	if (!fc[0]) {
		printf("\n\nCould not allocate space for column of icube.");
		return(NULL);
	}

	fc[0][0] = (int *)malloc((size_t)(size*size*size)*sizeof(int));

	if (!fc[0][0]) {
		printf("\n\nCould not allocate space for depth of icube.");
		return(NULL);
	}
	
	for (j = 1; j < size; j++) {
		fc[0][j] = fc[0][j-1] + size;
	}

	for (i = 1; i < size; i++) {
		fc[i] = fc[i-1] + size;
		fc[i][0] = fc[i-1][0] + (size*size);
		for (j = 1; j < size; j++) {
			fc[i][j] = fc[i][j-1] + size;
		}
	}

	return(fc);
}

/***
*	ibox
*
*	Routine to allocate memory for an 3D array of ints
*	All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
int ***ibox(long int xsize, long int ysize, long int zsize)
{
	long int i,j;
	int ***fc;

	fc = (int ***)malloc((size_t)xsize*sizeof(int**));
	if (!fc) {
		printf("\n\nCould not allocate space for row of box.");
		return(NULL);
	}

	fc[0] = (int **)malloc((size_t)(ysize*xsize)*sizeof(int*));

	if (!fc[0]) {
		printf("\n\nCould not allocate space for column of box.");
		return(NULL);
	}

	fc[0][0] = (int *)malloc((size_t)(zsize*ysize*xsize)*sizeof(int));

	if (!fc[0][0]) {
		printf("\n\nCould not allocate space for depth of box.");
		return(NULL);
	}
	
	for (j = 1; j < ysize; j++) {
		fc[0][j] = fc[0][j-1] + zsize;
	}

	for (i = 1; i < xsize; i++) {
		fc[i] = fc[i-1] + ysize;
		fc[i][0] = fc[i-1][0] + (zsize*ysize);
		for (j = 1; j < ysize; j++) {
			fc[i][j] = fc[i][j-1] + zsize;
		}
	}

	return(fc);
}

/***
*	usicube
*
*	Routine to allocate memory for an 3D array of unsigned short ints.
*	All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
unsigned short int ***usicube(long int size)
{
	long int i,j;
	unsigned short int ***fc;

	fc = (unsigned short int ***)malloc((size_t)size*sizeof(unsigned short int**));
	if (!fc) {
		printf("\n\nCould not allocate space for row of usicube.");
		return(NULL);
	}

	fc[0] = (unsigned short int **)malloc((size_t)(size*size)*sizeof(unsigned short int*));

	if (!fc[0]) {
		printf("\n\nCould not allocate space for column of usicube.");
		return(NULL);
	}

	fc[0][0] = (unsigned short int *)malloc((size_t)(size*size*size)*sizeof(unsigned short int));

	if (!fc[0][0]) {
		printf("\n\nCould not allocate space for depth of usicube.");
		return(NULL);
	}
	
	for (j = 1; j < size; j++) {
		fc[0][j] = fc[0][j-1] + size;
	}

	for (i = 1; i < size; i++) {
		fc[i] = fc[i-1] + size;
		fc[i][0] = fc[i-1][0] + (size*size);
		for (j = 1; j < size; j++) {
			fc[i][j] = fc[i][j-1] + size;
		}
	}

	return(fc);
}

/***
*	usibox
*
*	Routine to allocate memory for an 3D array of unsigned short ints
*	All array indices are assumed to start with zero.
*
*	Arguments:	int number of elements in each dimension
*	Returns:	Pointer to memory location of first element
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
unsigned short int ***usibox(long int xsize, long int ysize, long int zsize)
{
	long int i,j;
	unsigned short int ***fc;

	fc = (unsigned short int ***)malloc((size_t)xsize*sizeof(unsigned short int**));
	if (!fc) {
		printf("\n\nCould not allocate space for row of box.");
		return(NULL);
	}

	fc[0] = (unsigned short int **)malloc((size_t)(ysize*xsize)*sizeof(unsigned short int*));

	if (!fc[0]) {
		printf("\n\nCould not allocate space for column of box.");
		return(NULL);
	}

	fc[0][0] = (unsigned short int *)malloc((size_t)(zsize*ysize*xsize)*sizeof(unsigned short int));

	if (!fc[0][0]) {
		printf("\n\nCould not allocate space for depth of box.");
		return(NULL);
	}
	
	for (j = 1; j < ysize; j++) {
		fc[0][j] = fc[0][j-1] + zsize;
	}

	for (i = 1; i < xsize; i++) {
		fc[i] = fc[i-1] + ysize;
		fc[i][0] = fc[i-1][0] + (zsize*ysize);
		for (j = 1; j < ysize; j++) {
			fc[i][j] = fc[i][j-1] + zsize;
		}
	}

	return(fc);
}

/***
*	free_fvector
*
*	Routine to free the allocated memory for a vector of floats
*	All array indices are assumed to start with zero.
*
*	Arguments:	float pointer to memory
*
*	Returns:	nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_fvector(float *fv)
{
	free(fv);
    if (fv) fv = NULL;

	return;
}

/***
*	free_dvector
*
*	Routine to free the allocated memory for a vector of doubles
*	All array indices are assumed to start with zero.
*
*	Arguments:	double pointer to memory
*
*	Returns:	nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_dvector(double *dv)
{
	free(dv);
    if (dv) dv = NULL;

	return;
}

/***
*	free_ldvector
*
*	Routine to free the allocated memory for a vector of long doubles
*	All array indices are assumed to start with zero.
*
*	Arguments:	long double pointer to memory
*
*	Returns:	nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_ldvector(long double *ldv)
{
	free(ldv);
    if (ldv) ldv = NULL;

	return;
}

/***
*	free_pixelvector
*
*	Routine to free the allocated memory for a vector of pixel_t elements
*	All array indices are assumed to start with zero.
*
*	Arguments:	pixel_t pointer to memory
*
*	Returns:	nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_pixelvector(pixel_t *ptv)
{
    free(ptv);
    if (ptv) ptv = NULL;

    return;
}

/***
*	free_ivector
*
*	Routine to free the allocated memory for a vector of ints
*	All array indices are assumed to start with zero.
*
*	Arguments:	int pointer to memory
*
*	Returns:	nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_ivector(int *iv)
{
	free(iv);
    if (iv) iv = NULL;

	return;
}

/***
*	free_sivector
*
*	Routine to free the allocated memory for a vector of short ints
*	All array indices are assumed to start with zero.
*
*	Arguments:	short int pointer to memory
*
*	Returns:	nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_sivector(short int *iv)
{
	free(iv);
    if (iv) iv = NULL;

	return;
}

/***
*	free_livector
*
*	Routine to free the allocated memory for a vector of long ints
*	All array indices are assumed to start with zero.
*
*	Arguments:	long int pointer to memory
*
*	Returns:	nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_livector(long int *iv)
{
	free(iv);
    if (iv) iv = NULL;

	return;
}

/***
*	free_sicube
*
*	Routine to free the allocated memory for a 3D array of short ints
*	All array indices are assumed to start with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine, freeallmem
*
***/
void free_sicube(short int ***fc)
{
	free((char*) (fc[0][0]));
    if (fc[0][0]) fc[0][0] = NULL;
	free((char*) (fc[0]));
    if (fc[0]) fc[0] = NULL;
	free((char*) (fc));
    if (fc) fc = NULL;

	return;
}

/***
*	free_sibox
*
*	Routine to free the allocated memory for a 3D array of short ints
*	All array indices are assumed to start with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine, freeallmem
*
***/
void free_sibox(short int ***fc)
{
	free((char*) (fc[0][0]));
    if (fc[0][0]) fc[0][0] = NULL;
	free((char*) (fc[0]));
    if (fc[0]) fc[0] = NULL;
	free((char*) (fc));
    if (fc) fc = NULL;

	return;
}


/***
*	free_ccube
*
*	Routine to free the allocated memory for a 3D array of chars
*	All array indices are assumed to start with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine, freeallmem
*
***/
void free_ccube(char ***fc)
{
	free((char*) (fc[0][0]));
    if (fc[0][0]) fc[0][0] = NULL;
	free((char*) (fc[0]));
    if (fc[0]) fc[0] = NULL;
	free((char*) (fc));
    if (fc) fc = NULL;

	return;
}

/***
*	free_cbox
*
*	Routine to free the allocated memory for a 3D array of chars
*	All array indices are assumed to start with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine, freeallmem
*
***/
void free_cbox(char ***fc)
{
	free((char*) (fc[0][0]));
    if (fc[0][0]) fc[0][0] = NULL;
	free((char*) (fc[0]));
    if (fc[0]) fc[0] = NULL;
	free((char*) (fc));
    if (fc) fc = NULL;

	return;
}


/***
*	free_fcube
*
*	Routine to free the allocated memory for a 3D array of floats
*	All array indices are assumed to start with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_fcube(float ***fc)
{
	free((char*) (fc[0][0]));
    if (fc[0][0]) fc[0][0] = NULL;
	free((char*) (fc[0]));
    if (fc[0]) fc[0] = NULL;
	free((char*) (fc));
    if (fc) fc = NULL;

	return;
}

/***
*	free_fbox
*
*	Routine to free the allocated memory for a 3D array of floats
*	All array indices are assumed to start with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_fbox(float ***fc)
{
	free((char*) (fc[0][0]));
    if (fc[0][0]) fc[0][0] = NULL;
	free((char*) (fc[0]));
    if (fc[0]) fc[0] = NULL;
	free((char*) (fc));
    if (fc) fc = NULL;

	return;
}

/***
*	free_dbox
*
*	Routine to free the allocated memory for a 3D array of doubles
*	All array indices are assumed to start with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_dbox(double ***fc)
{
	free((char*) (fc[0][0]));
    if (fc[0][0]) fc[0][0] = NULL;
	free((char*) (fc[0]));
    if (fc[0]) fc[0] = NULL;
	free((char*) (fc));
    if (fc) fc = NULL;

	return;
}

/***
*	free_icube
*
*	Routine to free the allocated memory for a 3D array of ints
*	All array indices are assumed to start with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_icube(int ***fc)
{
	free((char*) (fc[0][0]));
    if (fc[0][0]) fc[0][0] = NULL;
	free((char*) (fc[0]));
    if (fc[0]) fc[0] = NULL;
	free((char*) (fc));
    if (fc) fc = NULL;

	return;
}

/***
*	free_ibox
*
*	Routine to free the allocated memory for a 3D array of ints
*	All array indices are assumed to start with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_ibox(int ***fc)
{
	free((char*) (fc[0][0]));
    if (fc[0][0]) fc[0][0] = NULL;
	free((char*) (fc[0]));
    if (fc[0]) fc[0] = NULL;
	free((char*) (fc));
    if (fc) fc = NULL;

	return;
}


/***
*	free_usicube
*
*	Routine to free the allocated memory for a 3D array of unsigned
*	short ints.
*
*	All array indices are assumed to start with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_usicube(unsigned short int ***fc)
{
	free((char*) (fc[0][0]));
    if (fc[0][0]) fc[0][0] = NULL;
	free((char*) (fc[0]));
    if (fc[0]) fc[0] = NULL;
	free((char*) (fc));
    if (fc) fc = NULL;

	return;
}

/***
*	free_usibox
*
*	Routine to free the allocated memory for a 3D array of unsigned
*	short ints.
*
*	All array indices are assumed to start with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_usibox(unsigned short int ***fc)
{
	free((char*) (fc[0][0]));
    if (fc[0][0]) fc[0][0] = NULL;
	free((char*) (fc[0]));
    if (fc[0]) fc[0] = NULL;
	free((char*) (fc));
    if (fc) fc = NULL;

	return;
}


/***
*	free_sisquare
*
*	Routine to free the allocated memory for a 2D square array
*	of short ints.  All array indices are assumed to start
*	with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_sisquare(short int **is)
{
	free((char*) (is[0]));
    if (is[0]) is[0] = NULL;
	free((char*) (is));
    if (is) is = NULL;

	return;
}

/***
*	free_sirect
*
*	Routine to free the allocated memory for a 2D rectangular array
*	of short ints.  All array indices are assumed to start
*	with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_sirect(short int **is)
{
	free((char*) (is[0]));
    if (is[0]) is[0] = NULL;
	free((char*) (is));
    if (is) is = NULL;

	return;
}

/***
*	free_irect
*
*	Routine to free the allocated memory for a 2D rectangular array
*	of ints.  All array indices are assumed to start
*	with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_irect(int **is)
{
	free((char*) (is[0]));
    if (is[0]) is[0] = NULL;
	free((char*) (is));
    if (is) is = NULL;

	return;
}

/***
*	free_drect
*
*	Routine to free the allocated memory for a 2D rectangular array
*	of doubles.  All array indices are assumed to start
*	with zero.
*
*	Arguments:	Pointer to memory location of first element
*
* 	Returns:	Nothing
*
*	Calls:		no other routines
*	Called by:	main routine
*
***/
void free_drect(double **is)
{
	free((char*) (is[0]));
    if (is[0]) is[0] = NULL;
	free((char*) (is));
    if (is) is = NULL;

	return;
}

