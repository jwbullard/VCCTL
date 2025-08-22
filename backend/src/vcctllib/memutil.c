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
#include "../include/vcctl.h"
#include <stdio.h>
#include <stdlib.h>

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
int *ivector(size_t size) {
  int *iv;

  iv = (int *)malloc(size * sizeof(int));
  if (!iv) {
    printf("\n\nCould not allocate space for int vector.");
    return (NULL);
  }

  return (iv);
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
short int *sivector(size_t size) {
  short int *iv;

  iv = (short int *)malloc(size * sizeof(short int));
  if (!iv) {
    printf("\n\nCould not allocate space for short int vector.");
    return (NULL);
  }

  return (iv);
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
long int *livector(size_t size) {
  long int *iv;

  iv = (long int *)malloc(size * sizeof(long int));
  if (!iv) {
    printf("\n\nCould not allocate space for long int vector.");
    return (NULL);
  }

  return (iv);
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
float *fvector(size_t size) {
  float *fv;

  fv = (float *)malloc(size * sizeof(float));
  if (!fv) {
    printf("\n\nCould not allocate space for float vector.");
    return (NULL);
  }

  return (fv);
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
double *dvector(size_t size) {
  double *dv;

  dv = (double *)malloc(size * sizeof(double));
  if (!dv) {
    printf("\n\nCould not allocate space for double vector.");
    return (NULL);
  }

  return (dv);
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
pixel_t *pixelvector(size_t size) {
  pixel_t *ptv;

  ptv = (pixel_t *)malloc(size * sizeof(pixel_t));
  if (!ptv) {
    printf("\n\nCould not allocate space for pixel_t vector.");
    return (NULL);
  }

  return (ptv);
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
short int **sisquare(size_t size) {
  size_t i;
  short int **is;

  is = (short int **)malloc(size * sizeof(*is));
  if (!is) {
    printf("\n\nCould not allocate space for row of sisquare.");
    return (NULL);
  }

  for (i = 0; i < size; ++i) {
    is[i] = NULL;
  }

  for (i = 0; i < size; ++i) {
    is[i] = (short int *)malloc(size * sizeof(*is[i]));
    if (!is[i]) {
      printf("\n\nCould not allocate space for column of sisquare.");
      free_sisquare(is, size);
      return (NULL);
    }
  }

  return (is);
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
short int **sirect(size_t xsize, size_t ysize) {
  size_t i;
  short int **is;

  is = (short int **)malloc(xsize * sizeof(*is));
  if (!is) {
    printf("\n\nCould not allocate space for row of sirect.");
    return (NULL);
  }

  for (i = 0; i < xsize; ++i) {
    is[i] = NULL;
  }

  for (i = 0; i < xsize; ++i) {
    is[i] = (short int *)malloc(ysize * sizeof(*is[i]));
    if (!is[i]) {
      printf("\n\nCould not allocate space for column of sirect.");
      free_sirect(is, xsize);
      return (NULL);
    }
  }

  return (is);
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
int **irect(size_t xsize, size_t ysize) {
  size_t i;
  int **is;

  is = (int **)malloc(xsize * sizeof(*is));
  if (!is) {
    printf("\n\nCould not allocate space for row of irect.");
    return (NULL);
  }

  for (i = 0; i < xsize; ++i) {
    is[i] = NULL;
  }

  for (i = 0; i < xsize; ++i) {
    is[i] = (int *)malloc(ysize * sizeof(*is[i]));
    if (!is[i]) {
      printf("\n\nCould not allocate space for column of irect.");
      free_irect(is, xsize);
      return (NULL);
    }
  }

  return (is);
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
double **drect(size_t xsize, size_t ysize) {
  size_t i;
  double **is;

  is = (double **)malloc(xsize * sizeof(*is));
  if (!is) {
    printf("\n\nCould not allocate space for row of drect.");
    return (NULL);
  }

  for (i = 0; i < xsize; ++i) {
    is[i] = NULL;
  }

  for (i = 0; i < xsize; ++i) {
    is[i] = (double *)malloc(ysize * sizeof(*is[i]));
    if (!is[i]) {
      printf("\n\nCould not allocate space for column of drect.");
      free_drect(is, xsize);
      return (NULL);
    }
  }

  return (is);
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
char ***ccube(size_t size) {
  size_t i, j;
  char ***fc;

  fc = (char ***)malloc(size * sizeof(*fc));
  if (!fc) {
    printf("\n\nCould not allocate space for column of ccube.");
    return (NULL);
  }

  for (i = 0; i < size; ++i) {
    fc[i] = NULL;
  }

  for (i = 0; i < size; ++i) {
    fc[i] = (char **)malloc(size * sizeof(*fc[i]));
    if (!fc[i]) {
      printf("\n\nCould not allocate space for row of ccube.");
      free_ccube(fc, size);
      return (NULL);
    }
  }

  for (i = 0; i < size; ++i) {
    for (j = 0; j < size; ++j) {
      fc[i][j] = NULL;
    }
  }

  for (i = 0; i < size; ++i) {
    for (j = 0; j < size; ++j) {
      fc[i][j] = (char *)malloc(size * sizeof(*fc[i][j]));
      if (!fc[i][j]) {
        printf("\n\nCould not allocate space for depth of ccube.");
        free_ccube(fc, size);
        return (NULL);
      }
    }
  }

  return (fc);
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
char ***cbox(size_t xsize, size_t ysize, size_t zsize) {
  size_t i, j;
  char ***fc;

  fc = (char ***)malloc(xsize * sizeof(*fc));
  if (!fc) {
    printf("\n\nCould not allocate space for column of cbox.");
    return (NULL);
  }

  for (i = 0; i < xsize; ++i) {
    fc[i] = NULL;
  }

  for (i = 0; i < xsize; ++i) {
    fc[i] = (char **)malloc(ysize * sizeof(*fc[i]));
    if (!fc[i]) {
      printf("\n\nCould not allocate space for row of cbox.");
      free_cbox(fc, xsize, ysize);
      return (NULL);
    }
  }

  for (i = 0; i < xsize; ++i) {
    for (j = 0; j < ysize; ++j) {
      fc[i][j] = NULL;
    }
  }

  for (i = 0; i < xsize; ++i) {
    for (j = 0; j < ysize; ++j) {
      fc[i][j] = (char *)malloc(zsize * sizeof(*fc[i][j]));
      if (!fc[i][j]) {
        printf("\n\nCould not allocate space for depth of cbox.");
        free_cbox(fc, xsize, ysize);
        return (NULL);
      }
    }
  }

  return (fc);
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
short int ***sicube(size_t size) {
  size_t i, j;
  short int ***fc;

  fc = (short int ***)malloc(size * sizeof(*fc));
  if (!fc) {
    printf("\n\nCould not allocate space for column of sicube.");
    return (NULL);
  }

  for (i = 0; i < size; ++i) {
    fc[i] = NULL;
  }

  for (i = 0; i < size; ++i) {
    fc[i] = (short int **)malloc(size * sizeof(*fc[i]));
    if (!fc[i]) {
      printf("\n\nCould not allocate space for row of sicube.");
      free_sicube(fc, size);
      return (NULL);
    }
  }

  for (i = 0; i < size; ++i) {
    for (j = 0; j < size; ++j) {
      fc[i][j] = NULL;
    }
  }

  for (i = 0; i < size; ++i) {
    for (j = 0; j < size; ++j) {
      fc[i][j] = (short int *)malloc(size * sizeof(*fc[i][j]));
      if (!fc[i][j]) {
        printf("\n\nCould not allocate space for depth of sicube.");
        free_sicube(fc, size);
        return (NULL);
      }
    }
  }

  return (fc);
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
short int ***sibox(size_t xsize, size_t ysize, size_t zsize) {
  size_t i, j;
  short int ***fc;

  fc = (short int ***)malloc(xsize * sizeof(*fc));
  if (!fc) {
    printf("\n\nCould not allocate space for column of sibox.");
    return (NULL);
  }

  for (i = 0; i < xsize; ++i) {
    fc[i] = NULL;
  }

  for (i = 0; i < xsize; ++i) {
    fc[i] = (short int **)malloc(ysize * sizeof(*fc[i]));
    if (!fc[i]) {
      printf("\n\nCould not allocate space for row of sibox.");
      free_sibox(fc, xsize, ysize);
      return (NULL);
    }
  }

  for (i = 0; i < xsize; ++i) {
    for (j = 0; j < ysize; ++j) {
      fc[i][j] = NULL;
    }
  }

  for (i = 0; i < xsize; ++i) {
    for (j = 0; j < ysize; ++j) {
      fc[i][j] = (short int *)malloc(zsize * sizeof(*fc[i][j]));
      if (!fc[i][j]) {
        printf("\n\nCould not allocate space for depth of sibox.");
        free_sibox(fc, xsize, ysize);
        return (NULL);
      }
    }
  }

  return (fc);
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
float ***fcube(size_t size) {
  size_t i, j;
  float ***fc;

  fc = (float ***)malloc(size * sizeof(*fc));
  if (!fc) {
    printf("\n\nCould not allocate space for column of fcube.");
    return (NULL);
  }

  for (i = 0; i < size; ++i) {
    fc[i] = NULL;
  }

  for (i = 0; i < size; ++i) {
    fc[i] = (float **)malloc(size * sizeof(*fc[i]));
    if (!fc[i]) {
      printf("\n\nCould not allocate space for row of fcube.");
      free_fcube(fc, size);
      return (NULL);
    }
  }

  for (i = 0; i < size; ++i) {
    for (j = 0; j < size; ++j) {
      fc[i][j] = NULL;
    }
  }

  for (i = 0; i < size; ++i) {
    for (j = 0; j < size; ++j) {
      fc[i][j] = (float *)malloc(size * sizeof(*fc[i][j]));
      if (!fc[i][j]) {
        printf("\n\nCould not allocate space for depth of fcube.");
        free_fcube(fc, size);
        return (NULL);
      }
    }
  }

  return (fc);
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
float ***fbox(size_t xsize, size_t ysize, size_t zsize) {
  size_t i, j;
  float ***fc;

  fc = (float ***)malloc(xsize * sizeof(*fc));
  if (!fc) {
    printf("\n\nCould not allocate space for column of fbox.");
    return (NULL);
  }

  for (i = 0; i < xsize; ++i) {
    fc[i] = NULL;
  }

  for (i = 0; i < xsize; ++i) {
    fc[i] = (float **)malloc(ysize * sizeof(*fc[i]));
    if (!fc[i]) {
      printf("\n\nCould not allocate space for row of fbox.");
      free_fbox(fc, xsize, ysize);
      return (NULL);
    }
  }

  for (i = 0; i < xsize; ++i) {
    for (j = 0; j < ysize; ++j) {
      fc[i][j] = NULL;
    }
  }

  for (i = 0; i < xsize; ++i) {
    for (j = 0; j < ysize; ++j) {
      fc[i][j] = (float *)malloc(zsize * sizeof(*fc[i][j]));
      if (!fc[i][j]) {
        printf("\n\nCould not allocate space for depth of sibox.");
        free_fbox(fc, xsize, ysize);
        return (NULL);
      }
    }
  }

  return (fc);
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
double ***dbox(size_t xsize, size_t ysize, size_t zsize) {
  size_t i, j;
  double ***fc;

  fc = (double ***)malloc(xsize * sizeof(*fc));
  if (!fc) {
    printf("\n\nCould not allocate space for column of dbox.");
    return (NULL);
  }

  for (i = 0; i < xsize; ++i) {
    fc[i] = NULL;
  }

  for (i = 0; i < xsize; ++i) {
    fc[i] = (double **)malloc(ysize * sizeof(*fc[i]));
    if (!fc[i]) {
      printf("\n\nCould not allocate space for row of dbox.");
      free_dbox(fc, xsize, ysize);
      return (NULL);
    }
  }

  for (i = 0; i < xsize; ++i) {
    for (j = 0; j < ysize; ++j) {
      fc[i][j] = NULL;
    }
  }

  for (i = 0; i < xsize; ++i) {
    for (j = 0; j < ysize; ++j) {
      fc[i][j] = (double *)malloc(zsize * sizeof(*fc[i][j]));
      if (!fc[i][j]) {
        printf("\n\nCould not allocate space for depth of dbox.");
        free_dbox(fc, xsize, ysize);
        return (NULL);
      }
    }
  }

  return (fc);
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
int ***icube(size_t size) {
  size_t i, j;
  int ***fc;

  fc = (int ***)malloc(size * sizeof(*fc));
  if (!fc) {
    printf("\n\nCould not allocate space for column of icube.");
    return (NULL);
  }

  for (i = 0; i < size; ++i) {
    fc[i] = NULL;
  }

  for (i = 0; i < size; ++i) {
    fc[i] = (int **)malloc(size * sizeof(*fc[i]));
    if (!fc[i]) {
      printf("\n\nCould not allocate space for row of icube.");
      free_icube(fc, size);
      return (NULL);
    }
  }

  for (i = 0; i < size; ++i) {
    for (j = 0; j < size; ++j) {
      fc[i][j] = NULL;
    }
  }

  for (i = 0; i < size; ++i) {
    for (j = 0; j < size; ++j) {
      fc[i][j] = (int *)malloc(size * sizeof(*fc[i][j]));
      if (!fc[i][j]) {
        printf("\n\nCould not allocate space for depth of icube.");
        free_icube(fc, size);
        return (NULL);
      }
    }
  }

  return (fc);
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
int ***ibox(size_t xsize, size_t ysize, size_t zsize) {
  size_t i, j;
  int ***fc;

  fc = (int ***)malloc(xsize * sizeof(*fc));
  if (!fc) {
    printf("\n\nCould not allocate space for column of ibox.");
    return (NULL);
  }

  for (i = 0; i < xsize; ++i) {
    fc[i] = NULL;
  }

  for (i = 0; i < xsize; ++i) {
    fc[i] = (int **)malloc(ysize * sizeof(*fc[i]));
    if (!fc[i]) {
      printf("\n\nCould not allocate space for row of ibox.");
      free_ibox(fc, xsize, ysize);
      return (NULL);
    }
  }

  for (i = 0; i < xsize; ++i) {
    for (j = 0; j < ysize; ++j) {
      fc[i][j] = NULL;
    }
  }

  for (i = 0; i < xsize; ++i) {
    for (j = 0; j < ysize; ++j) {
      fc[i][j] = (int *)malloc(zsize * sizeof(*fc[i][j]));
      if (!fc[i][j]) {
        printf("\n\nCould not allocate space for depth of ibox.");
        free_ibox(fc, xsize, ysize);
        return (NULL);
      }
    }
  }

  return (fc);
}

/***
 *	Int3Darray
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
int Int3darray(Int3d *thing, size_t xsize, size_t ysize, size_t zsize) {
  thing->x = xsize;
  thing->y = ysize;
  thing->z = zsize;
  thing->val = NULL;
  thing->val = malloc(thing->x * thing->y * thing->z * sizeof(*thing->val));
  if (thing->val == NULL) {
    return (1);
  }
  return (0);
}

/***
 *	getInt3Dindex
 *
 *	Routine to allocate memory for an 3D array of ints
 *	All array indices are assumed to start with zero.
 *
 *	Arguments:	int number of elements in each dimension
 *	Returns:	Pointer to memory location of first zlement
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
size_t getInt3dindex(Int3d thing, size_t x, size_t y, size_t z) {
  /* Assumes C-ordering */
  /* return ((x * thing.y * thing.z) + (y * thing.z) + z); */
  /* Assumes A-ordering */
  return ((z * thing.y * thing.x) + (y * thing.x) + x);
}

/***
 *	free_Int3Darray
 *
 *	Routine to deallocate memory for an 3D array of ints
 *	All array indices are assumed to start with zero.
 *
 *	Arguments:	int number of elements in each dimension
 *	Returns:	Pointer to memory location of first element
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
void free_Int3darray(Int3d *thing) {
  free(thing->val);
  return;
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
unsigned short int ***usicube(size_t size) {
  size_t i, j;
  unsigned short int ***fc;

  fc = (unsigned short int ***)malloc(size * sizeof(*fc));
  if (!fc) {
    printf("\n\nCould not allocate space for column of usicube.");
    return (NULL);
  }

  for (i = 0; i < size; ++i) {
    fc[i] = NULL;
  }

  for (i = 0; i < size; ++i) {
    fc[i] = (unsigned short int **)malloc(size * sizeof(*fc[i]));
    if (!fc[i]) {
      printf("\n\nCould not allocate space for row of usicube.");
      free_usicube(fc, size);
      return (NULL);
    }
  }

  for (i = 0; i < size; ++i) {
    for (j = 0; j < size; ++j) {
      fc[i][j] = NULL;
    }
  }

  for (i = 0; i < size; ++i) {
    for (j = 0; j < size; ++j) {
      fc[i][j] = (unsigned short int *)malloc(size * sizeof(*fc[i][j]));
      if (!fc[i][j]) {
        printf("\n\nCould not allocate space for depth of usicube.");
        free_usicube(fc, size);
        return (NULL);
      }
    }
  }

  return (fc);
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
unsigned short int ***usibox(size_t xsize, size_t ysize, size_t zsize) {
  size_t i, j;
  unsigned short int ***fc;

  fc = (unsigned short int ***)malloc(xsize * sizeof(*fc));
  if (!fc) {
    printf("\n\nCould not allocate space for column of usibox.");
    return (NULL);
  }

  for (i = 0; i < xsize; ++i) {
    fc[i] = NULL;
  }

  for (i = 0; i < xsize; ++i) {
    fc[i] = (unsigned short int **)malloc(ysize * sizeof(*fc[i]));
    if (!fc[i]) {
      printf("\n\nCould not allocate space for row of usibox.");
      free_usibox(fc, xsize, ysize);
      return (NULL);
    }
  }

  for (i = 0; i < xsize; ++i) {
    for (j = 0; j < ysize; ++j) {
      fc[i][j] = NULL;
    }
  }

  for (i = 0; i < xsize; ++i) {
    for (j = 0; j < ysize; ++j) {
      fc[i][j] = (unsigned short int *)malloc(zsize * sizeof(*fc[i][j]));
      if (!fc[i][j]) {
        printf("\n\nCould not allocate space for depth of usibox.");
        free_usibox(fc, xsize, ysize);
        return (NULL);
      }
    }
  }

  return (fc);
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
void free_fvector(float *fv) {
  free(fv);
  if (fv)
    fv = NULL;

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
void free_dvector(double *dv) {
  free(dv);
  if (dv)
    dv = NULL;

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
void free_ldvector(long double *ldv) {
  free(ldv);
  if (ldv)
    ldv = NULL;

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
void free_pixelvector(pixel_t *ptv) {
  free(ptv);
  if (ptv)
    ptv = NULL;

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
void free_ivector(int *iv) {
  free(iv);
  if (iv)
    iv = NULL;

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
void free_sivector(short int *iv) {
  free(iv);
  if (iv)
    iv = NULL;

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
void free_livector(long int *iv) {
  free(iv);
  if (iv)
    iv = NULL;

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
void free_sicube(short int ***fc, size_t size) {
  size_t i, j;
  for (i = 0; i < size; ++i) {
    if (fc[i] != NULL) {
      for (j = 0; j < size; ++j) {
        free(fc[i][j]);
      }
      free(fc[i]);
    }
  }
  free(fc);

  return;
}

/***
 *	free_sibox
 *
 *	Routine to free the allocated memory for a 3D array of short ints
 *	All array indices are assumed to start with zero.
 *
 *	Arguments:	Pointer to memory location of first element
 *	            x dimension of box
 *	            y dimension of box
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine, freeallmem
 *
 ***/
void free_sibox(short int ***fc, size_t xsize, size_t ysize) {
  size_t i, j;
  for (i = 0; i < xsize; ++i) {
    if (fc[i] != NULL) {
      for (j = 0; j < ysize; ++j) {
        free(fc[i][j]);
      }
      free(fc[i]);
    }
  }
  free(fc);

  return;
}

/***
 *	free_ccube
 *
 *	Routine to free the allocated memory for a 3D array of chars
 *	All array indices are assumed to start with zero.
 *
 *	Arguments:	Pointer to memory location of first element
 *	            dimension of cube
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine, freeallmem
 *
 ***/
void free_ccube(char ***fc, size_t size) {
  size_t i, j;
  for (i = 0; i < size; ++i) {
    if (fc[i] != NULL) {
      for (j = 0; j < size; ++j) {
        free(fc[i][j]);
      }
      free(fc[i]);
    }
  }
  free(fc);

  return;
}

/***
 *	free_cbox
 *
 *	Routine to free the allocated memory for a 3D array of chars
 *	All array indices are assumed to start with zero.
 *
 *	Arguments:	Pointer to memory location of first element
 *	            x dimension of the box
 *	            y dimension of the box
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine, freeallmem
 *
 ***/
void free_cbox(char ***fc, size_t xsize, size_t ysize) {
  size_t i, j;
  for (i = 0; i < xsize; ++i) {
    if (fc[i] != NULL) {
      for (j = 0; j < ysize; ++j) {
        free(fc[i][j]);
      }
      free(fc[i]);
    }
  }
  free(fc);

  return;
}

/***
 *	free_fcube
 *
 *	Routine to free the allocated memory for a 3D array of floats
 *	All array indices are assumed to start with zero.
 *
 *	Arguments:	Pointer to memory location of first element
 *	            dimension of the cube
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
void free_fcube(float ***fc, size_t size) {
  size_t i, j;
  for (i = 0; i < size; ++i) {
    if (fc[i] != NULL) {
      for (j = 0; j < size; ++j) {
        free(fc[i][j]);
      }
      free(fc[i]);
    }
  }
  free(fc);

  return;
}

/***
 *	free_fbox
 *
 *	Routine to free the allocated memory for a 3D array of floats
 *	All array indices are assumed to start with zero.
 *
 *	Arguments:	Pointer to memory location of first element
 *	            x dimension of the box
 *	            y dimension of the box
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
void free_fbox(float ***fc, size_t xsize, size_t ysize) {
  size_t i, j;
  for (i = 0; i < xsize; ++i) {
    if (fc[i] != NULL) {
      for (j = 0; j < ysize; ++j) {
        free(fc[i][j]);
      }
      free(fc[i]);
    }
  }
  free(fc);

  return;
}

/***
 *	free_dbox
 *
 *	Routine to free the allocated memory for a 3D array of doubles
 *	All array indices are assumed to start with zero.
 *
 *	Arguments:	Pointer to memory location of first element
 *	            x dimension of the box
 *	            y dimension of the box
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
void free_dbox(double ***fc, size_t xsize, size_t ysize) {
  size_t i, j;
  for (i = 0; i < xsize; ++i) {
    if (fc[i] != NULL) {
      for (j = 0; j < ysize; ++j) {
        free(fc[i][j]);
      }
      free(fc[i]);
    }
  }
  free(fc);

  return;
}

/***
 *	free_icube
 *
 *	Routine to free the allocated memory for a 3D array of ints
 *	All array indices are assumed to start with zero.
 *
 *	Arguments:	Pointer to memory location of first element
 *	            dimension of the cube
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
void free_icube(int ***fc, size_t size) {
  size_t i, j;
  for (i = 0; i < size; ++i) {
    if (fc[i] != NULL) {
      for (j = 0; j < size; ++j) {
        free(fc[i][j]);
      }
      free(fc[i]);
    }
  }
  free(fc);

  return;
}

/***
 *	free_ibox
 *
 *	Routine to free the allocated memory for a 3D array of ints
 *	All array indices are assumed to start with zero.
 *
 *	Arguments:	Pointer to memory location of first element
 *	            x dimension of the box
 *	            y dimension of the box
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
void free_ibox(int ***fc, size_t xsize, size_t ysize) {
  size_t i, j;
  if (fc != NULL) {
    for (i = 0; i < xsize; ++i) {
      if (fc[i] != NULL) {
        for (j = 0; j < ysize; ++j) {
          if (fc[i][j] != NULL)
            free(fc[i][j]);
        }
        if (fc[i] != NULL)
          free(fc[i]);
      }
    }
  }
  fc = NULL;

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
 *	            dimension of the cube
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
void free_usicube(unsigned short int ***fc, size_t size) {
  size_t i, j;
  for (i = 0; i < size; ++i) {
    if (fc[i] != NULL) {
      for (j = 0; j < size; ++j) {
        free(fc[i][j]);
      }
      free(fc[i]);
    }
  }
  free(fc);

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
 *	            x dimension of the box
 *	            y dimension of the box
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
void free_usibox(unsigned short int ***fc, size_t xsize, size_t ysize) {
  size_t i, j;
  for (i = 0; i < xsize; ++i) {
    if (fc[i] != NULL) {
      for (j = 0; j < ysize; ++j) {
        free(fc[i][j]);
      }
      free(fc[i]);
    }
  }
  free(fc);

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
 *	            dimension of the square
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
void free_sisquare(short int **is, size_t size) {
  size_t i;
  for (i = 0; i < size; ++i) {
    if (is[i] != NULL) {
      free(is[i]);
    }
  }
  free(is);

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
 *	            x dimension of the rectangle
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
void free_sirect(short int **is, size_t xsize) {
  size_t i;
  for (i = 0; i < xsize; ++i) {
    if (is[i] != NULL) {
      free(is[i]);
    }
  }
  free(is);

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
 *	            x dimension of the rectangle
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
void free_irect(int **is, size_t xsize) {
  size_t i;
  for (i = 0; i < xsize; ++i) {
    if (is[i] != NULL) {
      free(is[i]);
    }
  }
  free(is);

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
 *	            x dimension of the rectangle
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	main routine
 *
 ***/
void free_drect(double **is, size_t xsize) {
  size_t i;
  for (i = 0; i < xsize; ++i) {
    if (is[i] != NULL) {
      free(is[i]);
    }
  }
  free(is);

  return;
}
