/******************************************************
 *
 * Program hydmovie
 *
 * Makes an animated GIF file out of multiple single
 * GIF image files
 *
 ******************************************************/
#include <png.h>
#include "include/vcctl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/***
 *	Global variables
 ***/
float Version;

int main(void) {
  int valin, ovalin, nframes, xsyssize, ysyssize, zsyssize, numlines;
  int valout, i1, j1, i, i1000, i100, i10, i0, iz, ix, iy;
  int dx, dy, j, iscale, dxtot, dytot, bse;
  int ***mic;
  int *red, *green, *blue;
  float res;
  char filein[MAXSTRING], fileout[MAXSTRING], instring[MAXSTRING];
  char finalname[MAXSTRING];
  char filenew[MAXSTRING], fileroot[MAXSTRING];
  FILE *infile;
  bitmap_t image;

  mic = NULL;
  image.pixels = NULL;
  red = NULL;
  green = NULL;
  blue = NULL;

  red = ivector(NPHASES);
  if (!red) {
    bailout("hydmovie", "Could not allocate memory for red vector");
    return (1);
  }
  green = ivector(NPHASES);
  if (!green) {
    bailout("hydmovie", "Could not allocate memory for green vector");
    free_ivector(red);
    return (1);
  }
  blue = ivector(NPHASES);
  if (!blue) {
    bailout("hydmovie", "Could not allocate memory for blue vector");
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  printf("Enter name of file with raw (3-D image) data \n");
  fflush(stdout);
  read_string(filein, sizeof(filein));
  printf("%s\n", filein);
  sprintf(fileout, "%s", filein);
  printf("Enter final name of movie file to create \n");
  fflush(stdout);
  read_string(finalname, sizeof(finalname));
  printf("%s\n", finalname);

  printf("\nSimulate backscattered electron image? (Yes = 1, No = 0): ");
  fflush(stdout);

  read_string(instring, sizeof(instring));
  bse = atoi(instring);
  printf("%d\n", bse);
  fflush(stdout);

  cemcolors(red, green, blue, bse);

  /***
   *	Open the input movie file
   ***/

  infile = filehandler("hydmovie", filein, "READ");
  if (!infile) {
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  /***
   *	Read first line of image file to determine
   *	if software version is specified.  If it is
   *	specified then read it and all the other size
   *	and resolution information.  If not, set the
   *	size and resolution to default values for Version 2.0
   ***/

  if (read_imgheader(infile, &Version, &xsyssize, &ysyssize, &zsyssize, &res)) {
    fclose(infile);
    bailout("hydmovie", "Error reading image header");
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  /***
   *  	Determine number of movie frames
   ***/

  numlines = 0;
  while (!feof(infile)) {
    fscanf(infile, "%s", instring);
    if (!feof(infile))
      numlines++;
  }

  nframes = (numlines / (xsyssize * ysyssize));

  fclose(infile);

  /***
   *	Open the input movie file again
   ***/

  infile = filehandler("hydmovie", filein, "READ");
  if (!infile) {
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  /***
   *	Read the header again
   ***/

  if (read_imgheader(infile, &Version, &xsyssize, &ysyssize, &zsyssize, &res)) {
    fclose(infile);
    bailout("hydmovie", "Error reading image header");
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  /***
   *	Assume a rectangular image
   ****/

  dx = xsyssize;
  dy = ysyssize;
  printf("Enter factor by which to scale image \n");
  read_string(instring, sizeof(instring));
  iscale = atoi(instring);
  printf("%d\n", iscale);
  dxtot = dx * iscale;
  dytot = dy * iscale;

  /***
   *	Allocate memory for mic and image arrays
   ***/

  image.width = dxtot;
  image.height = dytot;

  image.pixels = pixelvector(dxtot * dytot);
  if (!image.pixels) {
    bailout("hydmovie", "Could not allocate memory for image pixels");
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  mic = ibox(xsyssize, ysyssize, nframes);
  if (!mic) {
    bailout("hydmovie", "Could not allocate memory for mic");
    free_pixelvector(image.pixels);
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  /* Read the hydration movie file */
  for (iz = 0; iz < nframes; iz++) {
    for (iy = 0; iy < ysyssize; iy++) {
      for (ix = 0; ix < xsyssize; ix++) {
        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valin = convert_id(ovalin, Version);
        mic[ix][iy][iz] = valin;
      }
    }
  }

  /***
   * Microstructure is stored, just magnify as needed and output
   * individual ppm files
   ***/

  for (iz = 0; iz < nframes; iz++) {

    /***
     *	Read this frame out of the 3D image
     * 	and create bitmap for it
     ***/

    for (j = 0; j < dy; j++) {
      for (i = 0; i < dx; i++) {

        valout = mic[i][j][iz];

        for (j1 = 0; j1 < iscale; j1++) {
          iy = j * iscale + j1;
          for (i1 = 0; i1 < iscale; i1++) {
            ix = i * iscale + i1;
            pixel_t *pixel = pixel_at(&image, ix, iy);
            pixel->red = red[valout];
            pixel->green = green[valout];
            pixel->blue = blue[valout];
          }
        }
      }
    }

    /* Write the image for this fram to a file given by filenew */

    i1000 = iz / 1000;
    i100 = (iz / 100) - (10 * i1000);
    i10 = (iz / 10) - (10 * (iz / 100));
    i0 = iz - (10 * (iz / 10));

    /***
     *	Each slice has its own name, e.g. slice
     *	49 will have the name fileroot0049.ppm,
     *	where fileroot is the name given by the
     *	user for the movie
     ***/

    sprintf(fileroot, "%s%1d%1d%1d%1d", fileout, i1000, i100, i10, i0);
    sprintf(filenew, "%s%1d%1d%1d%1d.png", fileout, i1000, i100, i10, i0);

    save_png_to_file(&image, filenew);
  }

  fflush(stdout);
  fclose(infile);

  /***
   * Free the dynamically allocated memory
   ***/

  free_ibox(mic, xsyssize, ysyssize);
  free_pixelvector(image.pixels);
  free_ivector(blue);
  free_ivector(green);
  free_ivector(red);
  printf("\n\n");

  return (0);
}
