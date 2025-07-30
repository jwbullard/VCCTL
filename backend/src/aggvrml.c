/******************************************************
 *
 * Program aggvrml
 *
 * Makes a VRML file of an aggregate shape, using
 * spherical harmonic expansion.
 *
 * Original fortran code written by E.J. Garboczi, 2002
 * Translated to C by J.W. Bullard, 2003
 *
 ******************************************************/

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
// #include <malloc.h>
#include "include/vcctl.h"

#define NNN 20

/***
 *	If the next line is commented out, then it is assumed that
 *	there are NNN terms in the spherical harmonic expansion.
 *	Otherwise, if it is not commented, then the program determines
 *	the number of terms from the number of lines in the *-anm.dat
 *	file itself.
 ***/

/*
#define DEFAULTNNN		1
*/

/***
 *	Number of grid points used in theta and phi directions
 *	to reconstruct particle surface. You can use down to
 *	about 100 for each and still get particles that are decent
 *	looking. The number of lines in the VRML files scale like
 *	NTHETA*NPHI. NOTE: Better to have odd number.
 *
 *	Allow three different levels of resolution, depending on
 *	the value of resval in the main program (0=low, 1=med, 2=high)
 ***/
#define NTHETA_LOW 41
#define NPHI_LOW 41
#define NTHETA_MED 101
#define NPHI_MED 101
#define NTHETA_HIGH 209
#define NPHI_HIGH 209

#define NNNMAX 200
#define NMAX 500

#define RESOLVE_LOW 0
#define RESOLVE_MED 1
#define RESOLVE_HIGH 2

/***
 *	ZMAX gives the viewpoint from which particle is represented
 *	in VRML browser, "eye" is at 7 * ZMAX.  This usually works
 *	fairly well
 ***/
#define ZMAX 0.0

/***
 *	RGB values for the color of the surface.  Set to bright gray
 ***/

#define RED 0.923106
#define GREEN 0.923106
#define BLUE 0.923106

/***
 *	Global variables
 ***/
double Pi, Version;
fcomplex **Y;
int Nnn, Ntheta, Nphi;

/***
 *	Function declarations
 ***/
void harm(double theta, double phi);
double fac(int j);

int main(void) {
  int i, j, ii, jj, number, num, resval;
  int n, m;
  float aa1, aa2;
  double a1, a2, xx, yy, zz, zmax, theta, phi;
  fcomplex rad;
  fcomplex **a;
  char shcname[MAXSTRING], vrmlname[MAXSTRING], buff[MAXSTRING];
  char buff1[MAXSTRING], buff2[MAXSTRING], buff3[MAXSTRING], buff4[MAXSTRING];
  FILE *infile, *vrmlfile;

  Y = NULL;
  a = NULL;

  /*	Assign value of Pi */

  Pi = 4.0 * atan(1.0);

  printf("Enter desired resolution of image (0=low, 1=med, 2=high) \n");
  read_string(buff, sizeof(buff));
  resval = atoi(buff);
  printf("%d\n", resval);

  if (resval == RESOLVE_LOW) {
    Ntheta = NTHETA_LOW;
    Nphi = NPHI_LOW;
  } else if (resval == RESOLVE_MED) {
    Ntheta = NTHETA_MED;
    Nphi = NPHI_MED;
  } else if (resval == RESOLVE_HIGH) {
    Ntheta = NTHETA_HIGH;
    Nphi = NPHI_HIGH;
  }

  printf("Enter name of file with SH coefficient data: ");
  read_string(shcname, sizeof(shcname));
  printf("%s\n", shcname);
  fflush(stdout);
  printf("Enter number of terms to use: ");
  read_string(buff, sizeof(buff));
  Nnn = atoi(buff);
  printf("%d\n", Nnn);
  fflush(stdout);
  printf("Enter name of VRML file to create: ");
  read_string(vrmlname, sizeof(vrmlname));
  printf("%s\n", vrmlname);
  fflush(stdout);

#ifdef DEFAULTNNN
  Nnn = NNN;
#endif

  /*	Allocate memory for the complex a and Y arrays */

  Y = complexmatrix(0, Nnn, -Nnn, Nnn);
  if (Y != NULL) {
    printf("Success with Y\n");
    fflush(stdout);
  } else {
    printf("Failure with Y\n");
    fflush(stdout);
    exit(1);
  }

  a = complexmatrix(0, Nnn, -Nnn, Nnn);

  if (a != NULL) {
    printf("Success with a\n");
    fflush(stdout);
  } else {
    printf("Failure with a\n");
    fflush(stdout);
    free_complexmatrix(Y, 0, Nnn, -Nnn, Nnn);
    exit(1);
  }

  infile = filehandler("aggvrml", shcname, "READ");
  if (!infile) {
    free_complexmatrix(a, 0, Nnn, -Nnn, Nnn);
    free_complexmatrix(Y, 0, Nnn, -Nnn, Nnn);
    exit(1);
  }

  printf("\nNnn = %d", Nnn);
  for (n = 0; n <= Nnn; n++) {
    for (m = n; m >= -n; m--) {
      fscanf(infile, "%s %s %s %s", buff1, buff2, buff3, buff4);
      ii = atoi(buff1);
      jj = atoi(buff2);
      aa1 = atof(buff3);
      aa2 = atof(buff4);
      a1 = (double)aa1;
      a2 = (double)aa2;
      a[n][m] = Complex(a1, a2);
    }
  }

  fclose(infile);

  /* Done reading input data.  Attempt to open the output file */

  vrmlfile = filehandler("aggvrml", vrmlname, "WRITE");
  if (!vrmlfile) {
    free_complexmatrix(a, 0, Nnn, -Nnn, Nnn);
    free_complexmatrix(Y, 0, Nnn, -Nnn, Nnn);
    exit(1);
  }

  /* Write out header of VRML file */

  fprintf(vrmlfile, "#VRML V2.0 utf8\n");
  fprintf(vrmlfile, "NavigationInfo {\n");
  fprintf(vrmlfile, "type [\"EXAMINE\",\"WALK\",\"FLY\"]\n");
  fprintf(vrmlfile, "}\n");
  fprintf(vrmlfile, "Group {\n");
  fprintf(vrmlfile, "children [\n");
  fprintf(vrmlfile, "Shape {\n");
  fprintf(vrmlfile, "geometry IndexedFaceSet {\n");
  fprintf(vrmlfile, "solid TRUE\n");
  fprintf(vrmlfile, "ccw FALSE\n");
  fprintf(vrmlfile, "coord Coordinate{\n");
  fprintf(vrmlfile, "point [\n");
  fflush(vrmlfile);

  zmax = ZMAX;
  for (i = 1; i <= Ntheta; i++) {
    for (j = 1; j <= Nphi; j++) {
      theta = (((double)(i)) - 1.0) * Pi / ((double)Ntheta);

      /* Don't want theta = 0 or theta = Pi */

      if (i == 1)
        theta = 0.001 * Pi;
      if (i == Ntheta)
        theta = 0.999 * Pi;

      phi = 2.0 * Pi * ((double)(j)-1.0) / ((double)Nphi);

      harm(theta, phi);

      rad = Cmul(a[0][0], Y[0][0]);
      for (n = 1; n <= Nnn; n++) {
        for (m = n; m >= -n; m--) {
          rad = Cadd(rad, Cmul(a[n][m], Y[n][m]));
        }
      }

      xx = rad.r * sin(theta) * cos(phi);
      yy = rad.r * sin(theta) * sin(phi);
      zz = rad.r * cos(theta);

      if (zmax < zz)
        zmax = zz;

      if (i == 1 && j == 1) {
        fprintf(vrmlfile, "%20.10f %20.10f %20.10f\n", 0.0, 0.0, zz);
      }
      fprintf(vrmlfile, "%20.10f %20.10f %20.10f\n", xx, yy, zz);

      if (i == Ntheta && j == Nphi) {
        fprintf(vrmlfile, "%20.10f %20.10f %20.10f\n", 0.0, 0.0, zz);
      }
    }
  }

  fprintf(vrmlfile, "]\n");
  fprintf(vrmlfile, "}\n");
  fprintf(vrmlfile, "coordIndex [\n");

  /* first do top end "cap" in triangles */

  for (j = 1; j <= Nphi - 1; j++) {
    fprintf(vrmlfile, "0 %d %d -1\n", j + 1, j);
  }
  fprintf(vrmlfile, "0 1 %d -1\n", Ntheta);

  /***
   *	Done with top end cap.  Now fill in rectangles
   *	along bulk of particle
   ***/

  for (i = 1; i <= Ntheta - 1; i++) {
    for (j = 1; j <= Nphi; j++) {
      number = Ntheta * (i - 1) + j;
      if (j == Nphi) {
        num = number + 1 - Nphi;
        fprintf(vrmlfile, "%d %d ", number, num);
        fprintf(vrmlfile, "%d %d -1\n", num + Ntheta, number + Ntheta);
      } else {
        fprintf(vrmlfile, "%d %d ", number, number + 1);
        fprintf(vrmlfile, "%d %d -1\n", number + 1 + Ntheta, number + Ntheta);
      }
    }
  }

  /* Finally do bottom end cap in triangles */

  number = Ntheta * Nphi + 1;
  for (j = 1; j <= Nphi - 1; j++) {
    num = ((Ntheta - 1) * Nphi) + j;
    fprintf(vrmlfile, "%d %d %d -1\n", number, num, num + 1);
  }
  fprintf(vrmlfile, "%d %d ", number, number - 1);
  fprintf(vrmlfile, "%d -1\n", (Ntheta - 1) * Nphi + 1);

  /* Done with bottom end cap */

  fprintf(vrmlfile, "]\n");

  /***
   *	creaseAngle does not seem to matter very much,
   *	so keep at this value
   ***/

  fprintf(vrmlfile, "creaseAngle 0.8\n");
  fprintf(vrmlfile, "}\n");
  fprintf(vrmlfile, "appearance Appearance {\n");
  fprintf(vrmlfile, "material Material {\n");
  fprintf(vrmlfile, "diffuseColor %f %f %f \n", RED, GREEN, BLUE);
  fprintf(vrmlfile, "}\n");
  fprintf(vrmlfile, "}\n");
  fprintf(vrmlfile, "}\n");
  fprintf(vrmlfile, "Viewpoint {\n");
  fprintf(vrmlfile, "position  %6.4f  %6.4f  %9.4f\n", 0.0, 0.0, 7.0 * zmax);
  fprintf(vrmlfile, "}\n");
  fprintf(vrmlfile, "]\n");
  fprintf(vrmlfile, "}\n");

  fclose(vrmlfile);
  free_complexmatrix(a, 0, Nnn, -Nnn, Nnn);
  free_complexmatrix(Y, 0, Nnn, -Nnn, Nnn);

  return (0);
}

/******************************************************
 *
 *	harm
 *
 * 	Compute spherical harmonics (complex) for a value
 * 	of x = cos(theta), phi = angle phi so
 * 	-1 < x < 1, P(n,m), -n < m < n, 0 < n
 *
 * 	Uses two recursion relations plus exact formulas for
 * 	the associated Legendre functions up to n=8
 *
 *	Arguments:	double theta and phi coordinates
 *	Returns:	Nothing
 *
 *	Calls: 		fac
 *	Called by:  main
 *
 ******************************************************/
void harm(double theta, double phi) {
  int i, m, n, mm, nn;
  double x, s, xn, xm;
  double realnum;
  double p[NNNMAX + 1][NMAX + 1];
  fcomplex fc1, fc2, fc3;

  x = cos(theta);
  s = (double)(sqrt((double)(1.0 - (x * x))));

  for (n = 0; n <= NNNMAX; n++) {
    for (m = 0; m <= NMAX; m++) {
      p[n][m] = 0.0;
    }
  }

  p[0][0] = 1.0;
  p[1][0] = x;
  p[1][1] = s;
  p[2][0] = 0.5 * (3. * x * x - 1.);
  p[2][1] = 3. * x * s;
  p[2][2] = 3. * (1. - x * x);
  p[3][0] = 0.5 * x * (5. * x * x - 3.);
  p[3][1] = 1.5 * (5. * x * x - 1.) * s;
  p[3][2] = 15. * x * (1. - x * x);
  p[3][3] = 15. * (pow(s, 3));
  p[4][0] = 0.125 * (35. * (pow(x, 4)) - 30. * x * x + 3.);
  p[4][1] = 2.5 * (7. * x * x * x - 3. * x) * s;
  p[4][2] = 7.5 * (7. * x * x - 1.) * (1. - x * x);
  p[4][3] = 105. * x * (pow(s, 3));
  p[4][4] = 105. * (pow((1. - x * x), 2));
  p[5][0] = 0.125 * x * (63. * (pow(x, 4)) - 70. * x * x + 15.);
  p[5][1] = 0.125 * 15. * s * (21. * (pow(x, 4)) - 14. * x * x + 1.);
  p[5][2] = 0.5 * 105. * x * (1. - x * x) * (3. * x * x - 1.);
  p[5][3] = 0.5 * 105. * (pow(s, 3)) * (9. * x * x - 1.);
  p[5][4] = 945. * x * (pow((1. - x * x), 2));
  p[5][5] = 945. * (pow(s, 5));
  p[6][0] =
      0.0625 * (231. * (pow(x, 6)) - 315. * (pow(x, 4)) + 105. * x * x - 5.);
  p[6][1] = 0.125 * 21. * x * (33. * (pow(x, 4)) - 30. * x * x + 5.) * s;
  p[6][2] =
      0.125 * 105. * (1. - x * x) * (33. * (pow(x, 4)) - 18. * x * x + 1.);
  p[6][3] = 0.5 * 315. * (11. * x * x - 3.) * x * (pow(s, 3));
  p[6][4] = 0.5 * 945. * (1. - x * x) * (1. - x * x) * (11. * x * x - 1.);
  p[6][6] = 10395. * pow((1. - x * x), 3);
  p[7][0] = 0.0625 * x *
            (429. * (pow(x, 6)) - 693. * (pow(x, 4)) + 315. * x * x - 35.);
  p[7][1] = 0.0625 * 7. * s *
            (429. * (pow(x, 6)) - 495. * (pow(x, 4)) + 135. * x * x - 5.);
  p[7][2] = 0.125 * 63. * x * (1. - x * x) *
            (143. * (pow(x, 4)) - 110. * x * x + 15.);
  p[7][3] =
      0.125 * 315. * (pow(s, 3)) * (143. * (pow(x, 4)) - 66. * x * x + 3.);
  p[7][4] = 0.5 * 3465. * x * (1. - x * x) * (1. - x * x) * (13. * x * x - 3.);
  p[7][5] = 0.5 * 10395. * (pow(s, 5)) * (13. * x * x - 1.);
  p[7][6] = 135135. * x * (1. - x * x) * (1. - x * x) * (1. - x * x);
  p[7][7] = 135135. * (pow(s, 7));
  p[8][0] = (1. / 128.) * (6435. * (pow(x, 8)) - 12012. * (pow(x, 6)) +
                           6930. * (pow(x, 4)) - 1260. * x * x + 35.);
  p[8][1] = 0.0625 * 9. * x * s *
            (715. * (pow(x, 6)) - 1001. * (pow(x, 4)) + 385. * x * x - 35.);
  p[8][2] = 0.0625 * 315. * (1. - x * x) *
            (143. * (pow(x, 6)) - 143. * (pow(x, 4)) + 33. * x * x - 1.);
  p[8][3] =
      0.125 * 3465. * x * (pow(s, 3)) * (39. * (pow(x, 4)) - 26. * x * x + 3.);
  p[8][4] = 0.125 * 10395. * (1. - x * x) * (1. - x * x) *
            (65. * (pow(x, 4)) - 26. * x * x + 1.);
  p[8][5] = 0.5 * 135135. * x * (pow(s, 5)) * (5. * x * x - 1.);
  p[8][6] = 0.5 * 135135. * (pow((1. - x * x), 3)) * (15. * x * x - 1.);
  p[8][7] = 2027025. * x * (pow(s, 7));
  p[8][8] = 2027025. * (pow((1. - x * x), 4));

  /* Now generate spherical harmonics for n = 0,8 (follows Arfken) */

  for (n = 0; n <= 8; n++) {

    /* does n = 0 separately */

    if (n == 0) {
      Y[0][0].r = 1.0 / (sqrt(4.0 * Pi));
      Y[0][0].i = 0.0;
      /*
      printf("\nn = %d m = %d Y.r = %f Y.i = %f",n,0,Y[0][0].r,Y[0][0].i);
      fflush(stdout);
      */
    } else {
      for (m = n; m >= -n; m--) {
        if (m >= 0) {
          fc1 = Complex(cos(m * phi), sin(m * phi));
          realnum = (pow(-1., m)) *
                    sqrt(((2 * n + 1) / 4. / Pi) * fac(n - m) / fac(n + m)) *
                    p[n][m];
          Y[n][m] = RCmul(realnum, fc1);
          /*
          printf("\nn = %d m = %d Y.r = %f Y.i = %f",n,m,Y[n][m].r,Y[n][m].i);
          fflush(stdout);
          */

        } else if (m < 0) {
          mm = -m;
          fc1 = Conjg(Y[n][m]);
          realnum = pow(-1.0, mm);
          Y[n][m] = RCmul(realnum, fc1);
          /*
          printf("\nn = %d m = %d Y.r = %f Y.i = %f",n,m,Y[n][m].r,Y[n][m].i);
          fflush(stdout);
          */
        }
      }
    }
  }

  /***
   *	Use recursion relations for n >= 9
   *	Do recursion on spherical harmonics, because they are
   *	better behaved numerically
   ***/

  for (n = 9; n <= Nnn; n++) {
    for (m = 0; m <= n - 2; m++) {
      xn = (double)(n - 1);
      xm = (double)m;
      realnum = (2. * xn + 1.) * x;
      Y[n][m] = RCmul(realnum, Y[n - 1][m]);
      /*
      if (n == 31) {
      printf("\n1n = %d m = %d Y.r = %f Y.i = %f",n,m,Y[n][m].r,Y[n][m].i);
      fflush(stdout);
      }
      */
      realnum =
          -sqrt((2. * xn + 1.) * ((xn * xn) - (xm * xm)) / (2. * xn - 1.));
      fc1 = RCmul(realnum, Y[n - 2][m]);
      Y[n][m] = Cadd(Y[n][m], fc1);
      /*
      if (n == 31) {
      printf("\n2n = %d m = %d Y.r = %f Y.i = %f",n,m,Y[n][m].r,Y[n][m].i);
      fflush(stdout);
      }
      */
      realnum = (sqrt((2. * xn + 1.) * (pow((xn + 1.), 2) - (xm * xm)) /
                      (2. * xn + 3.)));
      Y[n][m] = RCmul((1.0 / realnum), Y[n][m]);
      /*
      if (n == 31) {
      printf("\n3n = %d m = %d Y.r = %f Y.i = %f",n,m,Y[n][m].r,Y[n][m].i);
      fflush(stdout);
      }
      */
    }

    nn = (2 * n) - 1;
    p[n][n] = pow(s, n);
    /*
    if (n == 31) {
            printf("\nx = %f theta = %f s = %f",x,theta,s);
            fflush(stdout);
    }
    */
    for (i = 1; i <= nn; i += 2) {
      p[n][n] *= (double)i;
      /*
      if (n == 31) {
              printf("\n\t\ti = %d p[n][n] = %f",i,p[n][n]);
      }
      */
    }

    fc1 = Complex(cos(n * phi), sin(n * phi));
    realnum = (pow(-1., n)) *
              sqrt(((2 * n + 1) / 4. / Pi) * fac(n - n) / fac(n + n)) * p[n][n];
    Y[n][n] = RCmul(realnum, fc1);
    /*
    if (n == 31) {
    printf("\n4n = %d n = %d Y.r = %f Y.i = %f",n,n,Y[n][n].r,Y[n][n].i);
    printf("\n\tn = %d s = %f p[n][n] = %f realnum = %f",n,s,p[n][n],realnum);
    printf("\n\tx = %f",x);
    fflush(stdout);
    }
    */

    /***
     *	Now do second to the top m=n-1 using the exact m=n,
     *	and the recursive m=n-2 found previously
     ***/

    xm = (double)(n - 1);
    xn = (double)n;

    realnum = -1.0;
    fc1 = Complex(cos(phi), sin(phi));
    fc2 = Cmul(fc1, Y[n][n - 2]);
    Y[n][n - 1] = RCmul(realnum, fc2);
    /*
    if (n == 31) {
            printf("\n5n = %d n-1 = %d Y.r = %f Y.i =
    %f",n,n-1,Y[n][n-1].r,Y[n][n-1].i); fflush(stdout);
    }
    */
    realnum =
        (xn * (xn + 1.) - xm * (xm - 1.)) / sqrt((xn + xm) * (xn - xm + 1.));
    /*
    if (n == 31) {
    printf("\n\txn = %f xm = %f realnum = %f",xn,xm,realnum);
    }
    */
    Y[n][n - 1] = RCmul(realnum, Y[n][n - 1]);
    /*
    if (n == 31) {
            printf("\n6n = %d n-1 = %d Y.r = %f Y.i =
    %f",n,n-1,Y[n][n-1].r,Y[n][n-1].i); fflush(stdout);
    }
    */

    realnum = sqrt((xn - xm) * (xn + xm + 1.));
    fc1 = Complex(cos(phi), -sin(phi));
    fc2 = Cmul(fc1, Y[n][n]);
    fc3 = RCmul(realnum, fc2);
    Y[n][n - 1] = Csub(Y[n][n - 1], fc3);
    /*
    if (n == 31) {
            printf("\n7n = %d n-1 = %d Y.r = %f Y.i =
    %f",n,n-1,Y[n][n-1].r,Y[n][n-1].i); fflush(stdout);
    }
    */

    realnum = (s / 2.0 / xm / x);
    Y[n][n - 1] = RCmul(realnum, Y[n][n - 1]);
    /*
    if (n == 31) {
    printf("\n\ts = %f xm = %f x = %f realnum = %f",s,xm,x,realnum);
            printf("\n8n = %d n-1 = %d Y.r = %f Y.i =
    %f",n,n-1,Y[n][n-1].r,Y[n][n-1].i); fflush(stdout);
    }
    */
  }

  /* now fill in -m terms */

  for (n = 0; n <= Nnn; n++) {
    for (m = -1; m >= -n; m--) {
      mm = -m;
      realnum = pow(-1.0, mm);
      fc1 = Conjg(Y[n][mm]);
      Y[n][m] = RCmul(realnum, fc1);
      /*
      if (n == 31) {
      printf("\n9n = %d m = %d Y.r = %f Y.i = %f",n,m,Y[n][m].r,Y[n][m].i);
      fflush(stdout);
      }
      */
    }
  }

  return;
}

/******************************************************
 *
 *	fac
 *
 *	This is the factorial function, as used in function harm
 *
 *	Arguments:	int n
 *	Returns:	double fact;
 *
 *	Calls: No other routines
 *	Called by:  harm
 *
 ******************************************************/
double fac(int j) {
  int i;
  double fact;

  if (j <= 1) {
    fact = 1.0;
  } else {
    fact = 1.0;
    for (i = 1; i <= j; i++) {
      fact *= (double)i;
    }
  }

  return fact;
}
