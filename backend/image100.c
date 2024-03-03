/******************************************************
 *
 * Program image100
 *
 * Makes an animated GIF file out of multiple single
 * GIF image files for viewing as a movie within a
 * web browser using the program animview
 *
 ******************************************************/
#include "include/vcctl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/***
 *	Global variables
 ***/
float Version;

int main(void) {
  int valin, ovalin, planeid, xsyssize, ysyssize, zsyssize;
  int valout, i1, j1, i, i1000, i100, i10, i0, iz, izz, ix, iy;
  int dx, dy, j, iscale, dxtot, dytot, nd, nslices, done;
  int ***mic, **image;
  int *red, *green, *blue;
  float res;
  double **ndeep;
  char filein[MAXSTRING], fileout[MAXSTRING], buff[MAXSTRING],
      instring[MAXSTRING];
  char filenew[MAXSTRING], cmd[MAXSTRING], fileroot[MAXSTRING];
  FILE *infile, *outfile, *infofile;

  image = NULL;
  mic = NULL;
  red = NULL;
  green = NULL;
  blue = NULL;
  ndeep = NULL;

  red = ivector(NPHASES);
  if (!red) {
    bailout("image100", "Could not allocate memory for red vector");
    return (1);
  }
  green = ivector(NPHASES);
  if (!green) {
    bailout("image100", "Could not allocate memory for green vector");
    free_ivector(red);
    return (1);
  }
  blue = ivector(NPHASES);
  if (!blue) {
    bailout("image100", "Could not allocate memory for blue vector");
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  cemcolors(red, green, blue, 0);

  printf("Enter name of file with raw (3-D image) data \n");
  fflush(stdout);
  read_string(filein, sizeof(filein));
  printf("%s\n", filein);
  printf("Enter root name of image file to create \n");
  fflush(stdout);
  read_string(fileout, sizeof(fileout));
  printf("%s\n", fileout);
  printf("Enter plane normal to viewing direction: \n");
  printf("\t1. xy plane \n");
  printf("\t2. xz plane \n");
  printf("\t3. yz plane \n");
  fflush(stdout);
  read_string(instring, sizeof(instring));
  planeid = atoi(instring);
  printf("%d\n", planeid);
  fflush(stdout);
  printf("Enter magnification factor: \n");
  fflush(stdout);
  read_string(instring, sizeof(instring));
  iscale = atoi(instring);
  printf("%d\n", iscale);
  fflush(stdout);

  /***
   *	Open the input 3D image file
   ***/

  infile = filehandler("image100", filein, "READ");
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
    bailout("image100", "Error reading image header");
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  /***
   *	Write the software version, image size,
   *	and resolution to the file called
   *	fileroot.imd, where fileroot is the
   *	root name specified for	the animation
   ***/

  sprintf(buff, "%s.imd", fileout);
  infofile = filehandler("image100", buff, "WRITE");
  if (!infofile) {
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  fprintf(infofile, "%s %s\n", VERSIONSTRING, VERSIONNUMBER);
  fprintf(infofile, "%s %d\n", XSIZESTRING, xsyssize);
  fprintf(infofile, "%s %d\n", YSIZESTRING, ysyssize);
  fprintf(infofile, "%s %4.2f", IMGRESSTRING, res);
  fclose(infofile);

  /***
   *	Assume a rectangular image
   ****/

  mic = ibox(xsyssize, ysyssize, zsyssize);
  if (!mic) {
    bailout("image100", "Could not allocate memory for mic");
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  for (iz = 0; iz < zsyssize; iz++) {
    for (iy = 0; iy < ysyssize; iy++) {
      for (ix = 0; ix < xsyssize; ix++) {
        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valin = convert_id(ovalin, Version);
        mic[ix][iy][iz] = valin;
      }
    }
  }

  switch (planeid) {
  case 1:
    nslices = zsyssize;
    dx = xsyssize;
    dy = ysyssize;
    break;

  case 2:
    nslices = ysyssize;
    dx = xsyssize;
    dy = zsyssize;
    break;
  case 3:
    nslices = xsyssize;
    dx = ysyssize;
    dy = zsyssize;
    break;
  }

  dxtot = dx * iscale;
  dytot = dy * iscale;

  /***
   *	Allocate memory for mic, image, and ndeep arrays
   ***/

  image = irect(dxtot, dytot);
  if (!image) {
    bailout("image100", "Could not allocate memory for image");
    free_ibox(mic, xsyssize, ysyssize);
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  ndeep = drect(dxtot, dytot);
  if (!ndeep) {
    bailout("image100", "Could not allocate memory for ndeep");
    free_ibox(mic, xsyssize, ysyssize);
    free_irect(image, dxtot);
    free_ivector(blue);
    free_ivector(green);
    free_ivector(red);
    return (1);
  }

  for (iz = 0; iz < nslices; iz++) {
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
    sprintf(filenew, "%s%1d%1d%1d%1d.ppm", fileout, i1000, i100, i10, i0);

    /***
     *	Create PPM file for this slice
     ***/

    outfile = filehandler("image100", filenew, "WRITE");
    if (!outfile) {
      free_ibox(mic, xsyssize, ysyssize);
      free_drect(ndeep, dxtot);
      free_irect(image, dxtot);
      free_ivector(blue);
      free_ivector(green);
      free_ivector(red);
      return (1);
    }
    fprintf(outfile, "P3\n");
    fprintf(outfile, "%d %d\n", dx * iscale, dy * iscale);
    fprintf(outfile, "%d\n", SAT);

    /***
     *	Read this slice out of the 3D image
     *	and write it to the PPM file
     ***/

    switch (planeid) {
    case 1:
      for (j = 0; j < dy; j++) {
        for (i = 0; i < dx; i++) {

          izz = iz;
          nd = 0;
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

          valout = mic[i][j][izz];

          for (j1 = 0; j1 < iscale; j1++) {
            for (i1 = 0; i1 < iscale; i1++) {
              image[i * iscale + i1][j * iscale + j1] = valout;
              ndeep[i * iscale + i1][j * iscale + j1] = 0.1 * (10.0 - nd);
            }
          }
        }
      }
      break;

    case 2:
      for (j = 0; j < dy; j++) {
        for (i = 0; i < dx; i++) {

          izz = iz;
          nd = 0;
          done = 0;
          do {
            if (nd == 10 || mic[i][izz][j] != POROSITY) {
              done = 1;
            } else {
              nd++;
              izz++;
              if (izz >= ysyssize)
                izz -= ysyssize;
            }
          } while (!done);

          valout = mic[i][izz][j];

          for (j1 = 0; j1 < iscale; j1++) {
            for (i1 = 0; i1 < iscale; i1++) {
              image[i * iscale + i1][j * iscale + j1] = valout;
              ndeep[i * iscale + i1][j * iscale + j1] = 0.1 * (10.0 - nd);
            }
          }
        }
      }
      break;

    case 3:
      for (j = 0; j < dy; j++) {
        for (i = 0; i < dx; i++) {

          izz = iz;
          nd = 0;
          done = 0;
          do {
            if (nd == 10 || mic[izz][i][j] != POROSITY) {
              done = 1;
            } else {
              nd++;
              izz++;
              if (izz >= xsyssize)
                izz -= xsyssize;
            }
          } while (!done);

          valout = mic[izz][i][j];

          for (j1 = 0; j1 < iscale; j1++) {
            for (i1 = 0; i1 < iscale; i1++) {
              image[i * iscale + i1][j * iscale + j1] = valout;
              ndeep[i * iscale + i1][j * iscale + j1] = 0.1 * (10.0 - nd);
            }
          }
        }
      }
      break;
    }

    for (j = 0; j < dytot; j++) {
      for (i = 0; i < dxtot; i++) {
        fprintf(outfile, "%d ", (int)((ndeep[i][j] * red[image[i][j]]) + 0.5));
        fprintf(outfile, "%d ",
                (int)((ndeep[i][j] * green[image[i][j]]) + 0.5));
        fprintf(outfile, "%d\n",
                (int)((ndeep[i][j] * blue[image[i][j]]) + 0.5));
      }
    }

    fclose(outfile);

    /***
     *	Each PPM file must be converted to an
     *	individual GIF file, which is accomplished
     *	using the ImageMagick convert utility
     ***/

    sprintf(cmd, "convert %s.ppm %s.gif", fileroot, fileroot);
    printf("\n%s", cmd);
    system(cmd);
    sprintf(cmd, "rm %s.ppm", fileroot);
    printf("\n%s", cmd);
    fflush(stdout);
    system(cmd);
  }

  sprintf(cmd, "convert -loop 5 -delay 10 %s0*.gif %s.gif", fileout, fileout);
  printf("\n%s", cmd);
  fflush(stdout);
  system(cmd);

  fclose(infile);

  /***
   *	Remove all the individual GIF files
   ***/

  for (iz = 0; iz < nslices; iz++) {
    i1000 = iz / 1000;
    i100 = (iz / 100) - (10 * i1000);
    i10 = (iz / 10) - (10 * (iz / 100));
    i0 = iz - (10 * (iz / 10));
    sprintf(cmd, "rm %s%1d%1d%1d%1d.gif", fileout, i1000, i100, i10, i0);
    /* system(cmd); */
  }

  /***
   *	Free the dynamically allocated memory
   ***/

  free_ibox(mic, xsyssize, ysyssize);
  free_drect(ndeep, dxtot);
  free_irect(image, dxtot);
  free_ivector(blue);
  free_ivector(green);
  free_ivector(red);
  printf("\n\n");

  return (0);
}
