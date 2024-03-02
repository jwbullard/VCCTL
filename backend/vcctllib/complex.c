#include "../include/vcctlcomplex.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

fcomplex Cadd(fcomplex a, fcomplex b) {
  fcomplex c;
  c.r = a.r + b.r;
  c.i = a.i + b.i;
  return c;
}

fcomplex Csub(fcomplex a, fcomplex b) {
  fcomplex c;
  c.r = a.r - b.r;
  c.i = a.i - b.i;
  return c;
}

fcomplex Cmul(fcomplex a, fcomplex b) {
  fcomplex c;
  c.r = a.r * b.r - a.i * b.i;
  c.i = a.i * b.r + a.r * b.i;
  return c;
}

fcomplex Complex(float re, float im) {
  fcomplex c;
  c.r = re;
  c.i = im;
  return c;
}

fcomplex Conjg(fcomplex z) {
  fcomplex c;
  c.r = z.r;
  c.i = -z.i;
  return c;
}

fcomplex Cdiv(fcomplex a, fcomplex b) {
  fcomplex c;
  float r, den;
  if (fabs(b.r) >= fabs(b.i)) {
    r = b.i / b.r;
    den = b.r + r * b.i;
    c.r = (a.r + r * a.i) / den;
    c.i = (a.i - r * a.r) / den;
  } else {
    r = b.r / b.i;
    den = b.i + r * b.r;
    c.r = (a.r * r + a.i) / den;
    c.i = (a.i * r - a.r) / den;
  }
  return c;
}

float Cabs(fcomplex z) {
  float x, y, ans, temp;
  x = fabs(z.r);
  y = fabs(z.i);
  if (x == 0.0)
    ans = y;
  else if (y == 0.0)
    ans = x;
  else if (x > y) {
    temp = y / x;
    ans = x * sqrt(1.0 + temp * temp);
  } else {
    temp = x / y;
    ans = y * sqrt(1.0 + temp * temp);
  }
  return ans;
}

fcomplex Csqrt(fcomplex z) {
  fcomplex c;
  float x, y, w, r;
  if ((z.r == 0.0) && (z.i == 0.0)) {
    c.r = 0.0;
    c.i = 0.0;
    return c;
  } else {
    x = fabs(z.r);
    y = fabs(z.i);
    if (x >= y) {
      r = y / x;
      w = sqrt(x) * sqrt(0.5 * (1.0 + sqrt(1.0 + r * r)));
    } else {
      r = x / y;
      w = sqrt(y) * sqrt(0.5 * (r + sqrt(1.0 + r * r)));
    }
    if (z.r >= 0.0) {
      c.r = w;
      c.i = z.i / (2.0 * w);
    } else {
      c.i = (z.i >= 0) ? w : -w;
      c.r = z.i / (2.0 * c.i);
    }
    return c;
  }
}

fcomplex RCmul(float x, fcomplex a) {
  fcomplex c;
  c.r = x * a.r;
  c.i = x * a.i;
  return c;
}

/******************************************************
 *	complexmatrix
 *
 *	Routine to allocate memory for an 2D array of complex
 *	numbers (type fcomplex from Numerical Recipes code complex.c)
 *
 *	Array is of the form y[nrl,nrh][ncl,nch]
 *
 *	Arguments: int nrl,nrh,ncl,nch
 *	Returns:	Pointer to first element of array
 *
 *	Calls: No other routines
 *	Called by:  main
 *
 ******************************************************/
fcomplex **complexmatrix(int nrl, int nrh, int ncl, int nch) {
  int i;
  int nrow = nrh - nrl + 1;
  int ncol = nch - ncl + 1;
  fcomplex **m;

  m = NULL;

  /* allocate pointers to rows */

  m = (fcomplex **)malloc((size_t)((nrow + 1) * sizeof(fcomplex *)));
  if (!m) {
    return (NULL);
  }
  m++;
  m -= nrl;

  /* allocate rows and set pointers to them */

  m[nrl] = (fcomplex *)malloc((size_t)((nrow * ncol + 1) * sizeof(fcomplex)));
  if (!m[nrl]) {
    return (NULL);
  }
  m[nrl]++;
  m[nrl] -= ncl;

  for (i = nrl + 1; i <= nrh; i++)
    m[i] = m[i - 1] + ncol;

  /* return pointer to array of pointers to rows */

  return (m);
}

/***
 *	free_complexmatrix
 *
 *	Routine to free the allocated memory for a 2D array of complex
 *	numbers (type fcomplex in Numerical Recipes complex.c
 *
 *	Arguments:	Pointer to pointer to fcomplex type (the matrix)
 *				beginning and ending row indices (int nrl, int
 *nrh) beginning and ending column indices (int ncl, int nch)
 *
 * 	Returns:	Nothing
 *
 *	Calls:		no other routines
 *	Called by:	createvrml main routine
 *
 ***/
void free_complexmatrix(fcomplex **m, int nrl, int nrh, int ncl, int nch) {
  free((char *)(m[nrl] + ncl - 1));
  free((char *)(m + nrl - 1));
  return;
}
