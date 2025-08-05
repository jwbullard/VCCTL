/******************************************************
 *
 * Program oneimage
 *
 * Creates a PPM file for one slice of a
 * 3D microstructure
 ******************************************************/
#include "include/png.h"
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
  int valout, i1, j1, i, viewdepth, bse, ix, iy;
  int dx, dy, j, k, iscale, dxtot, dytot, view, slice;
  int ***mic;
  int *red, *green, *blue;
  float res;
  double **dshade;
  char filein[MAXSTRING], fileout[MAXSTRING], instring[MAXSTRING];
  FILE *infile;
  bitmap_t image;

  mic = NULL;
  image.pixels = NULL;
  red = NULL;
  green = NULL;
  blue = NULL;

  red = ivector(NPHASES);
  if (!red) {
    bailout("oneimage", "Could not allocate memory for red vector");
    exit(1);
  }
  green = ivector(NPHASES);
  if (!green) {
    bailout("oneimage", "Could not allocate memory for red vector");
    free_ivector(red);
    exit(1);
  }
  blue = ivector(NPHASES);
  if (!blue) {
    bailout("oneimage", "Could not allocate memory for red vector");
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

  read_string(instring, sizeof(instring));
  viewdepth = atoi(instring);
  printf("%d\n", viewdepth);
  fflush(stdout);

  printf("\nSimulate backscattered electron image? (Yes = 1, No = 0): ");
  fflush(stdout);

  read_string(instring, sizeof(instring));
  bse = atoi(instring);
  printf("%d\n", bse);
  fflush(stdout);

  cemcolors(red, green, blue, bse);

  /***
   *    Open the input 3D image file
   *    and the 2D output image file
   ***/

  infile = filehandler("oneimage", filein, "READ");
  if (!infile) {
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

  image.width = dxtot;
  image.height = dytot;

  /***
   *    Allocate memory for image pixels
   ***/

  image.pixels = pixelvector(dxtot * dytot);
  if (!image.pixels) {
    bailout("oneimage", "Could not allocate memory for image pixels");
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  printf("\nSuccessfully allocated memory for image pixels.");
  fflush(stdout);

  /***
   *    Allocate memory for dshade array if viewing depth is enabled
   ***/

  dshade = drect(dx * iscale, dy * iscale);
  if (!dshade) {
    fclose(infile);
    bailout("oneimage", "Could not allocate memory for image array");
    free_pixelvector(image.pixels);
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

  mic = ibox(xsyssize, ysyssize, zsyssize);
  if (!mic) {
    fclose(infile);
    bailout("oneimage", "Could not allocate memory for mic");
    if (dshade)
      free_drect(dshade, dx * iscale);
    free_pixelvector(image.pixels);
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    fflush(stdout);
    exit(1);
  }

  printf("\nSuccessfully allocated memory for mic array.");
  fflush(stdout);

  printf("\nPreparing to scan image file... ");
  fflush(stdout);

  /**
   * 2025 August 5
   * New convention for reading and writing image data is C-order (z varies
   * fastest, then y, then x)
   **/

  for (i = 0; i < xsyssize; i++) {
    for (j = 0; j < ysyssize; j++) {
      for (k = 0; k < zsyssize; k++) {
        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valout = convert_id(ovalin, Version);
        mic[i][j][k] = valout;
      }
    }
  }

  printf("done");
  fflush(stdout);
  fclose(infile);

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
          iy = j * iscale + j1;
          for (i1 = 0; i1 < iscale; i1++) {
            ix = i * iscale + i1;
            dshade[ix][iy] = 0.1 * (10.0 - nd);
            pixel_t *pixel = pixel_at(&image, ix, iy);
            if (valout == SANDINCONCRETE) {
              pixel->red = (int)(R_MUTEDFIREBRICK)*dshade[ix][iy];
              pixel->green = (int)(G_MUTEDFIREBRICK)*dshade[ix][iy];
              pixel->blue = (int)(B_MUTEDFIREBRICK)*dshade[ix][iy];
            } else {
              pixel->red = red[valout] * dshade[ix][iy];
              pixel->green = green[valout] * dshade[ix][iy];
              pixel->blue = blue[valout] * dshade[ix][iy];
            }
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
          iy = k * iscale + j1;
          for (i1 = 0; i1 < iscale; i1++) {
            ix = i * iscale + i1;
            dshade[ix][iy] = 0.1 * (10.0 - nd);
            pixel_t *pixel = pixel_at(&image, ix, iy);
            if (valout == SANDINCONCRETE) {
              pixel->red = (int)(R_MUTEDFIREBRICK)*dshade[ix][iy];
              pixel->green = (int)(G_MUTEDFIREBRICK)*dshade[ix][iy];
              pixel->blue = (int)(B_MUTEDFIREBRICK)*dshade[ix][iy];
            } else {
              pixel->red = red[valout] * dshade[ix][iy];
              pixel->green = green[valout] * dshade[ix][iy];
              pixel->blue = blue[valout] * dshade[ix][iy];
            }
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
          iy = k * iscale + j1;
          for (i1 = 0; i1 < iscale; i1++) {
            ix = j * iscale + i1;
            dshade[ix][iy] = 0.1 * (10.0 - nd);
            pixel_t *pixel = pixel_at(&image, ix, iy);
            if (valout == SANDINCONCRETE) {
              pixel->red = (int)(R_MUTEDFIREBRICK)*dshade[ix][iy];
              pixel->green = (int)(G_MUTEDFIREBRICK)*dshade[ix][iy];
              pixel->blue = (int)(B_MUTEDFIREBRICK)*dshade[ix][iy];
            } else {
              pixel->red = red[valout] * dshade[ix][iy];
              pixel->green = green[valout] * dshade[ix][iy];
              pixel->blue = blue[valout] * dshade[ix][iy];
            }
          }
        }
      }
    }
    break;
  }

  printf("\n\nSuccessfully made image with all pixels.");
  printf("\nSaving as png file: %s", fileout);
  fflush(stdout);
  save_png_to_file(&image, fileout);
  printf("\nPNG file saved.");

  /***
   *    Free dynamically allocated memory
   ***/

  free_ibox(mic, xsyssize, ysyssize);
  free_pixelvector(image.pixels);
  free_drect(dshade, dx * iscale);
  free_ivector(blue);
  free_ivector(green);
  free_ivector(red);
  printf("\n\n");

  return (0);
}
