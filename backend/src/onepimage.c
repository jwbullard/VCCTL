/******************************************************
 *
 * Program oneimage
 *
 * Creates a PPM file for one slice of a
 * 3D particle index microstructure
 ******************************************************/
#include "include/vcctl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/***
 *    Global variables
 ***/
float Version;

int main(void) {
  int ovalin, xsyssize, ysyssize, zsyssize, izz, done, nd;
  int valout, i1, j1, i, viewdepth, bse;
  int dx, dy, j, k, iscale, dxtot, dytot, view, slice;
  int ***mic;
  int **image, *red, *green, *blue;
  float res;
  double **dshade;
  char filein[MAXSTRING], fileout[MAXSTRING], instring[MAXSTRING];
  FILE *infile, *outfile;

  red = ivector(NPHASES);
  if (!red) {
    bailout("image100", "Could not allocate memory for red vector");
    exit(1);
  }
  green = ivector(NPHASES);
  if (!green) {
    bailout("image100", "Could not allocate memory for red vector");
    free_ivector(red);
    exit(1);
  }
  blue = ivector(NPHASES);
  if (!blue) {
    bailout("image100", "Could not allocate memory for red vector");
    free_ivector(green);
    free_ivector(red);
    exit(1);
  }

  printf("Enter name of file with raw (3-D image) data \n");
  fflush(stdout);
  read_string(filein, sizeof(filein));
  printf("%s\n", filein);
  fflush(stdout);
  printf("Enter name of image file to create \n");
  fflush(stdout);
  read_string(fileout, sizeof(fileout));
  printf("%s\n", fileout);
  fflush(stdout);

  printf("View orthogonal to:\n");
  printf("\t1. yz plane\n");
  printf("\t2. xz plane\n");
  printf("\t3. xy plane\n");
  printf("Enter orientation to view:  ");
  fflush(stdout);
  read_string(instring, sizeof(instring));
  view = atoi(instring);
  printf("%d\n", view);
  fflush(stdout);

  printf("\nEnter slice to view: ");
  fflush(stdout);
  read_string(instring, sizeof(instring));
  slice = atoi(instring);
  printf("%d\n", slice);
  fflush(stdout);

  printf("\nDepth perception enabled? (Yes = 1, No = 0): ");
  fflush(stdout);

  /*
  read_string(instring,sizeof(instring));
  viewdepth = atoi(instring);
  printf("%d\n",viewdepth);
  fflush(stdout);
  */
  viewdepth = 0;

  printf("\nSimulate backscattered electron image? (Yes = 1, No = 0): ");
  fflush(stdout);

  /*
  read_string(instring,sizeof(instring));
  bse = atoi(instring);
  printf("%d\n",bse);
  fflush(stdout);
  */

  bse = 0;

  cemcolors(red, green, blue, bse);

  /***
   *    Open the input 3D image file
   *    and the 2D output image file
   ***/

  infile = filehandler("oneimage", filein, "READ");
  if (!infile) {
    exit(1);
  }

  outfile = filehandler("oneimage", fileout, "WRITE");
  if (!outfile) {
    exit(1);
  }

  /***
   *    Read first line of image file to determine
   *    if size is specified.  If it is specified
   *    then read it.  If not, set the size to 100
   ***/

  if (read_imgheader(infile, &Version, &xsyssize, &ysyssize, &zsyssize, &res)) {
    bailout("oneimage", "Error reading image header");
    exit(1);
  }

  printf("\nDone reading image header:");
  printf("\n\tVersion = %f", Version);
  printf("\n\txsyssize = %d", xsyssize);
  printf("\n\tysyssize = %d", ysyssize);
  printf("\n\tzsyssize = %d", zsyssize);
  printf("\n\tres = %f\n", res);
  fflush(stdout);

  /***
   *    Assume a square image, which is okay if the
   *    3D system is a cube
   ****/

  if (view == 1) {
    dx = ysyssize;
    dy = zsyssize;
  } else if (view == 2) {
    dx = xsyssize;
    dy = zsyssize;
  } else {
    dx = xsyssize;
    dy = ysyssize;
  }

  printf("Enter factor by which to scale image:  \n");
  fflush(stdout);
  read_string(instring, sizeof(instring));
  iscale = atoi(instring);
  printf("%d\n", iscale);
  fflush(stdout);
  dxtot = dx * iscale;
  dytot = dy * iscale;

  /***
   *    Allocate memory for image array
   ***/

  image = irect(dx * iscale, dy * iscale);
  if (!image) {
    fclose(infile);
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    bailout("oneimage", "Could not allocate memory for image array");
    exit(1);
  }

  printf("\nSuccessfully allocated memory for image array.");
  fflush(stdout);

  /***
   *    Allocate memory for dshade array
   ***/

  dshade = drect(dx * iscale, dy * iscale);
  if (!dshade) {
    fclose(infile);
    bailout("oneimage", "Could not allocate memory for image array");
    free_irect(image, dx * iscale);
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    exit(1);
  }

  printf("\nSuccessfully allocated memory for dshade array.");
  fflush(stdout);

  /***
   *    Allocate memory for microstructure image
   ***/

  mic = NULL;
  mic = ibox(xsyssize, ysyssize, zsyssize);
  if (!mic) {
    fclose(infile);
    bailout("oneimage", "Could not allocate memory for mic");
    if (dshade)
      free_drect(dshade, dx * iscale);
    free_irect(image, dx * iscale);
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    fflush(stdout);
    exit(1);
  }

  printf("\nSuccessfully allocated memory for mic array.");
  fflush(stdout);

  /***
   *    Header information for PPM file
   ***/

  printf("\nWriting PPM image header");
  fflush(stdout);

  fprintf(outfile, "P3\n");
  fprintf(outfile, "%d %d\n", dx * iscale, dy * iscale);
  fprintf(outfile, "%d\n", SAT);
  fflush(outfile);

  printf("\nPreparing to scan image file... ");
  fflush(stdout);
  for (k = 0; k < zsyssize; k++) {
    for (j = 0; j < ysyssize; j++) {
      for (i = 0; i < xsyssize; i++) {
        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valout = convert_id(ovalin, Version);
        mic[i][j][k] = ((valout) % ((int)(NPHASES)-1)) + 1;
      }
    }
  }

  printf("done");
  fflush(stdout);

  switch (view) {

  case 3: /* xy plane */
    for (j = 0; j < ysyssize; j++) {
      for (i = 0; i < xsyssize; i++) {

        izz = slice;
        nd = 0;
        if (viewdepth) {
          done = 0;
          do {
            if (nd == 10 || mic[i][j][izz] != POROSITY) {
              done = 1;
            } else {
              nd++;
              izz++;
              if (izz >= zsyssize)
                izz -= zsyssize;
            }
          } while (!done);
        }

        valout = mic[i][j][izz];
        for (j1 = 0; j1 < iscale; j1++) {
          for (i1 = 0; i1 < iscale; i1++) {

            image[i * iscale + i1][j * iscale + j1] = valout;
            dshade[i * iscale + i1][j * iscale + j1] = 0.1 * (10.0 - nd);
          }
        }
      }
    }
    break;

  case 2: /* xz plane */
    for (k = 0; k < zsyssize; k++) {
      for (i = 0; i < xsyssize; i++) {

        izz = slice;
        nd = 0;
        if (viewdepth) {
          done = 0;
          do {
            if (nd == 10 || mic[i][izz][k] != POROSITY) {
              done = 1;
            } else {
              nd++;
              izz++;
              if (izz >= ysyssize)
                izz -= ysyssize;
            }
          } while (!done);
        }

        valout = mic[i][izz][k];
        for (j1 = 0; j1 < iscale; j1++) {
          for (i1 = 0; i1 < iscale; i1++) {

            image[i * iscale + i1][k * iscale + j1] = valout;
            dshade[i * iscale + i1][k * iscale + j1] = 0.1 * (10.0 - nd);
          }
        }
      }
    }
    break;

  default: /* yz plane */
    for (k = 0; k < zsyssize; k++) {
      for (j = 0; j < ysyssize; j++) {

        izz = slice;
        nd = 0;
        if (viewdepth) {
          done = 0;
          do {
            if (nd == 10 || mic[izz][j][k] != POROSITY) {
              done = 1;
            } else {
              nd++;
              izz++;
              if (izz >= xsyssize)
                izz -= xsyssize;
            }
          } while (!done);
        }

        valout = mic[izz][j][k];
        for (j1 = 0; j1 < iscale; j1++) {
          for (i1 = 0; i1 < iscale; i1++) {
            image[j * iscale + i1][k * iscale + j1] = valout;
            dshade[j * iscale + i1][k * iscale + j1] = 0.1 * (10.0 - nd);
          }
        }
      }
    }
    break;
  }

  fclose(infile);

  /***
   *    Write one pixel per line of PPM file
   ***/

  printf("\nPreparing to write remainder of PPM file");
  fflush(stdout);

  for (j = 0; j < (dy * iscale); j++) {
    for (i = 0; i < (dx * iscale); i++) {
      if (image[i][j] == SANDINCONCRETE) {
        fprintf(outfile, "%d ", (int)((dshade[i][j] * R_MUTEDFIREBRICK) + 0.5));
        fprintf(outfile, "%d ", (int)((dshade[i][j] * G_MUTEDFIREBRICK) + 0.5));
        fprintf(outfile, "%d\n",
                (int)((dshade[i][j] * B_MUTEDFIREBRICK) + 0.5));
      } else {
        fprintf(outfile, "%d ", (int)((dshade[i][j] * red[image[i][j]]) + 0.5));
        fprintf(outfile, "%d ",
                (int)((dshade[i][j] * green[image[i][j]]) + 0.5));
        fprintf(outfile, "%d\n",
                (int)((dshade[i][j] * blue[image[i][j]]) + 0.5));
      }
    }
  }

  fclose(outfile);

  /***
   *    Free dynamically allocated memory
   ***/

  free_ibox(mic, xsyssize, ysyssize);
  free_drect(dshade, dx * iscale);
  free_irect(image, dx * iscale);
  free_ivector(blue);
  free_ivector(green);
  free_ivector(red);

  return (0);
}
