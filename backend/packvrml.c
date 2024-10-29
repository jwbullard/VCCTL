/******************************************************
 *
 * Program packvrml
 *
 * Takes a 3-D image, makes six *.ppm files of the sides
 * to be put on the sides of a VRML box
 *
 * Original fortran code written by E.J. Garboczi, 2004
 * Translated to C by J.W. Bullard, 2004
 *
 ******************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
// #include <malloc.h>
#include "include/vcctl.h"

#define AGGPACK 1
#define CEMPACK 2
#define CREATEPGMS 1
#define PGMS2GIFS 2
#define CREATEVRML 3
#define EXIT 4
#define MINCHOICE CREATEPGMS
#define MAXCHOICE EXIT

#define AGG 1
#define ITZ 2

#define AGGR 128
#define AGGG 128
#define AGGB 128

#define ITZR 51
#define ITZG 205
#define ITZB 51

/* Global variables */
char Outdir[MAXSTRING];

/***
 *	Function declarations
 ***/
int createpgms(void);
int makevrml(int packtype, float x1, float x2, float y1, float y2, float z1,
             float z2);
int pgms2gifs(void);

int main(void) {
  int choice;

  /* Main menu */

  choice = 0;
  unsigned int finished = 0;

  do {
    do {

      printf("Main menu:\n");
      printf("\t%d. Make bounding pgm images\n", (int)CREATEPGMS);
      printf("\t%d. Convert pgm images to gif images (requires Imagemagick)\n",
             (int)PGMS2GIFS);
      printf("\t%d. Create VRML file\n", (int)CREATEVRML);
      printf("\t%d. Exit\n", (int)EXIT);
      read_string(instring, sizeof(instring));
      choice = atoi(instring);
      printf("%d\n", choice);

    } while (choice < (int)MINCHOICE || choice > (int)MAXCHOICE);

    switch (choice) {
    case CREATEPGMS:
      if (createpgms() > 0) {
        printf("\nError in creating PGM files\n");
      }
      break;
    case PGMS2GIFS:
      if (pgms2gifs() > 0) {
        printf("\nError in converting PGM files\n");
      }
      break;
    case CREATEVRML:
      if (makevrml() > 0) {
        printf("\nError in creating VRML file\n");
      }
      break;
    case EXIT:
      finished = 1;
      break;
    default:
      finished = 1;
      break;
    }
  } while (!finished);

  /* Mopping up after exiting here */
}

int createpgms(void) {
  register int i, j, k;
  int nx1, nx2, ny1, ny2, nz1, nz2, ppix, valin;
  int xsize, ysize, zsize, choice, packtype, maxval, val;
  int *red, *green, *blue;
  float x1, x2, y1, y2, z1, z2;
  float res, ver;
  char packname[MAXSTRING], filetype[5], fileext[5];
  char outname[MAXSTRING], cmdnew[MAXSTRING], instring[MAXSTRING];
  int ***pix;
  FILE *infile, *outfile;

  /* Initialize local arrays */

  sprintf(filetype, "AB");
  sprintf(fileext, "AB");

  /* Allocate memory for red, green, and blue vectors */

  red = ivector(NPHASES);
  if (!red) {
    bailout("packvrml", "Could not allocate memory for red vector");
    exit(1);
  }
  green = ivector(NPHASES);
  if (!green) {
    bailout("packvrml", "Could not allocate memory for green vector");
    free_ivector(red);
    exit(1);
  }
  blue = ivector(NPHASES);
  if (!blue) {
    bailout("packvrml", "Could not allocate memory for green vector");
    free_ivector(green);
    free_ivector(red);
    exit(1);
  }

  printf("Enter name of packing file \n");
  read_string(packname, sizeof(packname));
  printf("%s\n", packname);
  printf("Enter name of directory to place all output files.\n");
  printf("Remember to include final file separator \n");
  read_string(Outdir, sizeof(Outdir));
  printf("%s\n", Outdir);

  do {

    printf("Is this:\n");
    printf("\t1. Aggregate packing\n");
    printf("\t2. Cement particle packing\n");
    read_string(instring, sizeof(instring));
    packtype = atoi(instring);
    printf("%d\n", packtype);

  } while (packtype != AGGPACK && packtype != CEMPACK);

  strcpy(filetype, "P3");
  strcpy(fileext, "pgm");
  maxval = 255;

  for (i = 0; i < NPHASES; i++) {
    red[i] = 0;
    green[i] = 0;
    blue[i] = 0;
  }

  switch (packtype) {
  case AGGPACK:
    red[AGG] = AGGR;
    green[AGG] = AGGG;
    blue[AGG] = AGGB;
    red[ITZ] = ITZR;
    green[ITZ] = ITZG;
    blue[ITZ] = ITZB;
    break;
  case CEMPACK:
    cemcolors(red, green, blue, 0);
    break;
  }
  ``
      /*  Must open microstructure and read the header */

      infile = filehandler("packvrml", packname, "READ");
  if (!infile) {
    exit(1);
  }

  if (read_imgheader(infile, &ver, &xsize, &ysize, &zsize, &res)) {
    bailout("aggpackvrml", "Error reading microstructure image header");
    fflush(stdout);
    exit(1);
  }

  printf("Enter lower bound for x (0 to %d)\n", xsize);
  read_string(instring, sizeof(instring));
  nx1 = atoi(instring);
  printf("%d\n", nx1);
  printf("Enter upper bound for x (%d to %d)\n", (nx1 + 1), xsize);
  read_string(instring, sizeof(instring));
  nx2 = atoi(instring);
  printf("%d\n", nx2);
  printf("Enter lower bound for y (0 to %d)\n", ysize);
  read_string(instring, sizeof(instring));
  ny1 = atoi(instring);
  printf("%d\n", ny1);
  printf("Enter upper bound for y (%d to %d)\n", (ny1 + 1), ysize);
  read_string(instring, sizeof(instring));
  ny2 = atoi(instring);
  printf("%d\n", ny2);
  printf("Enter lower bound for z (0 to %d)\n", zsize);
  read_string(instring, sizeof(instring));
  nz1 = atoi(instring);
  printf("%d\n", nz1);
  printf("Enter upper bound for z (%d to %d)\n", (nz1 + 1), zsize);
  read_string(instring, sizeof(instring));
  nz2 = atoi(instring);
  printf("%d\n", nz2);

  /*	Allocate memory for the microstructure image */

  pix = ibox(xsize, ysize, zsize);
  if (!pix) {
    bailout("aggpackvrml", "Memory allocation failure");
    fflush(stdout);
    exit(1);
  }

  /* Now read the aggregate file and populate the pix array */

  if (packtype == AGGPACK) {
    for (k = 0; k < zsize; k++) {
      for (j = 0; j < ysize; j++) {
        for (i = 0; i < xsize; i++) {
          fscanf(infile, "%s", instring);
          ppix = atoi(instring);
          pix[i][j][k] = ppix;
        }
      }
    }
  } else {
    for (k = 0; k < zsize; k++) {
      for (j = 0; j < ysize; j++) {
        for (i = 0; i < xsize; i++) {
          fscanf(infile, "%s", instring);
          valin = atoi(instring);
          ppix = convert_id(valin, ver);
          pix[i][j][k] = ppix;
        }
      }
    }
  }

  /* Done reading packing file */

  fclose(infile);

  /***
   *	Actual physical coordinate values of corners of box, will
   *	be between 0 and 1
   ***/

  x1 = ((float)nx1 - 1.0) / ((float)(xsize));
  y1 = ((float)ny1 - 1.0) / ((float)(ysize));
  z1 = ((float)nz1 - 1.0) / ((float)(zsize));
  x2 = ((float)nx2) / ((float)(xsize));
  y2 = ((float)ny2) / ((float)(ysize));
  z2 = ((float)nz2) / ((float)(zsize));

  /***
   *	Make the six ppm files now
   ***/

  /***
   *	pix[nx1][ny1-ny2][nz1-nz2] is the -x side
   *	pix[nx2][ny1-ny2][nz1-nz2] is the +x side
   ***/

  /* 1. -x image */
  sprintf(outname, "%sminusx.%s", Outdir, fileext);
  outfile = filehandler("packvrml", outname, "WRITE");
  if (!outfile) {
    exit(1);
  }
  fprintf(outfile, "%s\n", filetype);
  fprintf(outfile, "%d %d\n", nz2 - nz1 + 1, ny2 - ny1 + 1);
  fprintf(outfile, "%d\n", maxval);
  for (j = ny2; j >= ny1; j--) {
    for (k = nz1; k <= nz2; k++) {
      val = pix[nx1][j][k];
      fprintf(outfile, "%d %d %d\n", red[val], green[val], blue[val]);
    }
  }
  fclose(outfile);

  /* 2. +x image */
  sprintf(outname, "%splusx.%s", Outdir, fileext);
  outfile = filehandler("packvrml", outname, "WRITE");
  if (!outfile) {
    exit(1);
  }
  fprintf(outfile, "%s\n", filetype);
  fprintf(outfile, "%d %d\n", ny2 - ny1 + 1, nz2 - nz1 + 1);
  fprintf(outfile, "%d\n", maxval);
  for (k = nz2; k >= nz1; k--) {
    for (j = ny1; j <= ny2; j++) {
      val = pix[nx2][j][k];
      fprintf(outfile, "%d %d %d\n", red[val], green[val], blue[val]);
    }
  }
  fclose(outfile);

  /***
   *	pix[nx1-nx2][ny2][nz1-nz2] is the -y side
   *	pix[nx1-nx2][ny1][nz1-nz2] is the +y side
   ***/

  /* 3. -y image */
  sprintf(outname, "%sminusy.%s", Outdir, fileext);
  outfile = filehandler("packvrml", outname, "WRITE");
  if (!outfile) {
    exit(1);
  }
  fprintf(outfile, "%s\n", filetype);
  fprintf(outfile, "%d %d\n", nx2 - nx1 + 1, nz2 - nz1 + 1);
  fprintf(outfile, "%d\n", maxval);
  for (k = nz2; k >= nz1; k--) {
    for (i = nx1; i <= nx2; i++) {
      val = pix[i][ny1][k];
      fprintf(outfile, "%d %d %d\n", red[val], green[val], blue[val]);
    }
  }
  fclose(outfile);

  /* 4. +y image */
  sprintf(outname, "%splusy.%s", Outdir, fileext);
  outfile = filehandler("packvrml", outname, "WRITE");
  if (!outfile) {
    exit(1);
  }
  fprintf(outfile, "%s\n", filetype);
  fprintf(outfile, "%d %d\n", nz2 - nz1 + 1, nx2 - nx1 + 1);
  fprintf(outfile, "%d\n", maxval);
  for (i = nx2; i >= nx1; i--) {
    for (k = nz1; k <= nz2; k++) {
      val = pix[i][ny2][k];
      fprintf(outfile, "%d %d %d\n", red[val], green[val], blue[val]);
    }
  }
  fclose(outfile);

  /***
   *	pix[nx1-nx2][ny1-ny2][nz1] is the -z side
   *	pix[nx1-nx2][ny1-ny2][nz2] is the +z side
   ***/

  /* 5. -z image */
  sprintf(outname, "%sminusz.%s", Outdir, fileext);
  outfile = filehandler("packvrml", outname, "WRITE");
  if (!outfile) {
    exit(1);
  }
  fprintf(outfile, "%s\n", filetype);
  fprintf(outfile, "%d %d\n", nx2 - nx1 + 1, ny2 - ny1 + 1);
  fprintf(outfile, "%d\n", maxval);
  for (j = ny2; j >= ny1; j--) {
    for (i = nx1; i <= nx2; i++) {
      val = pix[i][j][nz1];
      fprintf(outfile, "%d %d %d\n", red[val], green[val], blue[val]);
    }
  }
  fclose(outfile);

  /* 6. +z image */
  sprintf(outname, "%splusz.%s", Outdir, fileext);
  outfile = filehandler("packvrml", outname, "WRITE");
  if (!outfile) {
    exit(1);
  }
  fprintf(outfile, "%s\n", filetype);
  fprintf(outfile, "%d %d\n", nx2 - nx1 + 1, ny2 - ny1 + 1);
  fprintf(outfile, "%d\n", maxval);
  for (j = ny2; j >= ny1; j--) {
    for (i = nx1; i <= nx2; i++) {
      val = pix[i][j][nz2];
      fprintf(outfile, "%d %d %d\n", red[val], green[val], blue[val]);
    }
  }
  fclose(outfile);

  /***
   *	All ppm/pgm files are made, need to convert them to GIF files
   *	here.  Use same root names, different extensions.
   ***/

  sprintf(cmdnew, "convert %sminusx.%s %sminusx.gif", Outdir, fileext, Outdir);
  system(cmdnew);
  sprintf(cmdnew, "convert %splusx.%s %splusx.gif", Outdir, fileext, Outdir);
  system(cmdnew);
  sprintf(cmdnew, "convert %sminusy.%s %sminusy.gif", Outdir, fileext, Outdir);
  system(cmdnew);
  sprintf(cmdnew, "convert %splusy.%s %splusy.gif", Outdir, fileext, Outdir);
  system(cmdnew);
  sprintf(cmdnew, "convert %sminusz.%s %sminusz.gif", Outdir, fileext, Outdir);
  system(cmdnew);
  sprintf(cmdnew, "convert %splusz.%s %splusz.gif", Outdir, fileext, Outdir);
  system(cmdnew);

  /***
   *	Function makevrml actually prints out the VRML file
   ***/

  makevrml(packtype, x1, x2, y1, y2, z1, z2);

  free_ibox(pix, xsize, ysize);
  free_ivector(blue);
  free_ivector(green);
  free_ivector(red);

  return (0);
}

/***************************************************************
 *	makevrml
 *
 *	Takes the six .ppm files created and pastes them on the sides
 *	of an orthorhombic VRML box
 ***************************************************************/
void makevrml(int packtype, float x1, float x2, float y1, float y2, float z1,
              float z2) {

  char vrmlname[MAXSTRING];
  FILE *vrmlfile;

  sprintf(vrmlname, "%saggpack.wrl", Outdir);

  vrmlfile = filehandler("packvrml", vrmlname, "WRITE");
  if (!vrmlfile) {
    exit(1);
  }

  /* Write out header of VRML file */

  fprintf(vrmlfile, "#VRML V2.0 utf8\n");
  fprintf(vrmlfile, "#IndexedFaceSet\n");
  fprintf(vrmlfile, "Background {skyColor [0.2 0.2 1.0]}\n");
  fprintf(vrmlfile, "Group {\n");
  fprintf(vrmlfile, "     children [\n");
  /* Sets up three lights: top and two sides */
  fprintf(vrmlfile, "DirectionalLight {\n");
  fprintf(vrmlfile, "  on TRUE\n");
  fprintf(vrmlfile, "  intensity 1\n");
  fprintf(vrmlfile, "  ambientIntensity 1.0\n");
  fprintf(vrmlfile, "  color 1 1 1\n");
  fprintf(vrmlfile, "  direction 1 0 0\n");
  fprintf(vrmlfile, "}\n");
  fprintf(vrmlfile, "DirectionalLight {\n");
  fprintf(vrmlfile, "  on TRUE\n");
  fprintf(vrmlfile, "  intensity 1\n");
  fprintf(vrmlfile, "  ambientIntensity 1.0\n");
  fprintf(vrmlfile, "  color 1 1 1\n");
  fprintf(vrmlfile, "  direction 0 1 0\n");
  fprintf(vrmlfile, "}\n");
  fprintf(vrmlfile, "DirectionalLight {\n");
  fprintf(vrmlfile, "  on TRUE\n");
  fprintf(vrmlfile, "  intensity 1\n");
  fprintf(vrmlfile, "  ambientIntensity 1.0\n");
  fprintf(vrmlfile, "  color 1 1 1\n");
  fprintf(vrmlfile, "  direction 0 0 1\n");
  fprintf(vrmlfile, "}\n");
  fflush(vrmlfile);

  /* Sets up six sides of box, appropriate image is mapped to each side */

  /* minus z size */

  fprintf(vrmlfile, "Viewpoint {position 0.5 0.5 1.5 }\n");
  fprintf(vrmlfile, "Shape {\n");
  fprintf(vrmlfile, "  appearance Appearance{\n");
  fprintf(vrmlfile, "     material Material {diffuseColor    1 1 1}\n");
  fprintf(vrmlfile, "     texture ImageTexture {url \"minusz.gif\"}\n");
  fprintf(vrmlfile, "  }\n");
  fprintf(vrmlfile, "  geometry IndexedFaceSet {\n");
  fprintf(vrmlfile, "     coord Coordinate {\n");
  fprintf(vrmlfile, "        point [\n");
  fprintf(vrmlfile, "           #bottom\n");
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 0\n", x1, y1, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 1\n", x2, y1, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 2\n", x2, y2, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 3\n", x1, y2, z1);
  fprintf(vrmlfile, "           #top\n");
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 4\n", x1, y1, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 5\n", x2, y1, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 6\n", x2, y2, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 7\n", x1, y2, z2);
  fprintf(vrmlfile, "        ]\n");
  fprintf(vrmlfile, "     }\n");
  fprintf(vrmlfile, "     coordIndex [\n");
  fprintf(vrmlfile, "        #z bottom\n");
  fprintf(vrmlfile, "        3, 2, 1, 0, 3, -1,\n");
  fprintf(vrmlfile, "     ]\n");
  fprintf(vrmlfile, "     texCoord TextureCoordinate{\n");
  fprintf(vrmlfile,
          "        point "
          "[0.0000,0.0000,1.0000,0.0000,1.0000,1.0000,0.0000,1.0000]}\n");
  fprintf(vrmlfile, "  }\n");
  fprintf(vrmlfile, "}\n");

  /* Plus z side */

  fprintf(vrmlfile, "Shape {\n");
  fprintf(vrmlfile, "  appearance Appearance{\n");
  fprintf(vrmlfile, "     material Material {diffuseColor    1 1 1}\n");
  fprintf(vrmlfile, "     texture ImageTexture {url \"plusz.gif\"}\n");
  fprintf(vrmlfile, "  }\n");
  fprintf(vrmlfile, "  geometry IndexedFaceSet {\n");
  fprintf(vrmlfile, "     coord Coordinate {\n");
  fprintf(vrmlfile, "        point [\n");
  fprintf(vrmlfile, "           #bottom\n");
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 0\n", x1, y1, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 1\n", x2, y1, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 2\n", x2, y2, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 3\n", x1, y2, z1);
  fprintf(vrmlfile, "           #top\n");
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 4\n", x1, y1, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 5\n", x2, y1, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 6\n", x2, y2, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 7\n", x1, y2, z2);
  fprintf(vrmlfile, "        ]\n");
  fprintf(vrmlfile, "     }\n");
  fprintf(vrmlfile, "     coordIndex [\n");
  fprintf(vrmlfile, "        #z top\n");
  fprintf(vrmlfile, "        4, 5, 6, 7, 4, -1,\n");
  fprintf(vrmlfile, "     ]\n");
  fprintf(vrmlfile, "     texCoord TextureCoordinate{\n");
  fprintf(vrmlfile,
          "        point "
          "[0.0000,0.0000,1.0000,0.0000,1.0000,1.0000,0.0000,1.0000]}\n");
  fprintf(vrmlfile, "  }\n");
  fprintf(vrmlfile, "}\n");

  /* Plus x side */

  fprintf(vrmlfile, "Shape {\n");
  fprintf(vrmlfile, "  appearance Appearance{\n");
  fprintf(vrmlfile, "     material Material {diffuseColor    1 1 1}\n");
  fprintf(vrmlfile, "     texture ImageTexture {url \"plusx.gif\"}\n");
  fprintf(vrmlfile, "  }\n");
  fprintf(vrmlfile, "  geometry IndexedFaceSet {\n");
  fprintf(vrmlfile, "     coord Coordinate {\n");
  fprintf(vrmlfile, "        point [\n");
  fprintf(vrmlfile, "           #bottom\n");
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 0\n", x1, y1, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 1\n", x2, y1, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 2\n", x2, y2, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 3\n", x1, y2, z1);
  fprintf(vrmlfile, "           #top\n");
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 4\n", x1, y1, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 5\n", x2, y1, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 6\n", x2, y2, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 7\n", x1, y2, z2);
  fprintf(vrmlfile, "        ]\n");
  fprintf(vrmlfile, "     }\n");
  fprintf(vrmlfile, "     coordIndex [\n");
  fprintf(vrmlfile, "        #+x side\n");
  fprintf(vrmlfile, "        1, 2, 6, 5, 1, -1,\n");
  fprintf(vrmlfile, "     ]\n");
  fprintf(vrmlfile, "     texCoord TextureCoordinate{\n");
  fprintf(vrmlfile,
          "        point "
          "[0.0000,0.0000,1.0000,0.0000,1.0000,1.0000,0.0000,1.0000]}\n");
  fprintf(vrmlfile, "  }\n");
  fprintf(vrmlfile, "}\n");

  /* Minus x side */

  fprintf(vrmlfile, "Shape {\n");
  fprintf(vrmlfile, "  appearance Appearance{\n");
  fprintf(vrmlfile, "     material Material {diffuseColor    1 1 1}\n");
  fprintf(vrmlfile, "     texture ImageTexture {url \"minusx.gif\"}\n");
  fprintf(vrmlfile, "  }\n");
  fprintf(vrmlfile, "  geometry IndexedFaceSet {\n");
  fprintf(vrmlfile, "     coord Coordinate {\n");
  fprintf(vrmlfile, "        point [\n");
  fprintf(vrmlfile, "           #bottom\n");
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 0\n", x1, y1, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 1\n", x2, y1, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 2\n", x2, y2, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 3\n", x1, y2, z1);
  fprintf(vrmlfile, "           #top\n");
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 4\n", x1, y1, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 5\n", x2, y1, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 6\n", x2, y2, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 7\n", x1, y2, z2);
  fprintf(vrmlfile, "        ]\n");
  fprintf(vrmlfile, "     }\n");
  fprintf(vrmlfile, "     coordIndex [\n");
  fprintf(vrmlfile, "        #-x side\n");
  fprintf(vrmlfile, "        0, 4, 7, 3, 0, -1,\n");
  fprintf(vrmlfile, "     ]\n");
  fprintf(vrmlfile, "     texCoord TextureCoordinate{\n");
  fprintf(vrmlfile,
          "        point "
          "[0.0000,0.0000,1.0000,0.0000,1.0000,1.0000,0.0000,1.0000]}\n");
  fprintf(vrmlfile, "  }\n");
  fprintf(vrmlfile, "}\n");

  /* Plus y side */

  fprintf(vrmlfile, "Shape {\n");
  fprintf(vrmlfile, "  appearance Appearance{\n");
  fprintf(vrmlfile, "     material Material {diffuseColor    1 1 1}\n");
  fprintf(vrmlfile, "     texture ImageTexture {url \"plusy.gif\"}\n");
  fprintf(vrmlfile, "  }\n");
  fprintf(vrmlfile, "  geometry IndexedFaceSet {\n");
  fprintf(vrmlfile, "     coord Coordinate {\n");
  fprintf(vrmlfile, "        point [\n");
  fprintf(vrmlfile, "           #bottom\n");
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 0\n", x1, y1, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 1\n", x2, y1, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 2\n", x2, y2, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 3\n", x1, y2, z1);
  fprintf(vrmlfile, "           #top\n");
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 4\n", x1, y1, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 5\n", x2, y1, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 6\n", x2, y2, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 7\n", x1, y2, z2);
  fprintf(vrmlfile, "        ]\n");
  fprintf(vrmlfile, "     }\n");
  fprintf(vrmlfile, "     coordIndex [\n");
  fprintf(vrmlfile, "        #+y side\n");
  fprintf(vrmlfile, "        3, 7, 6, 2, 3, -1,\n");
  fprintf(vrmlfile, "     ]\n");
  fprintf(vrmlfile, "     texCoord TextureCoordinate{\n");
  fprintf(vrmlfile,
          "        point "
          "[0.0000,0.0000,1.0000,0.0000,1.0000,1.0000,0.0000,1.0000]}\n");
  fprintf(vrmlfile, "  }\n");
  fprintf(vrmlfile, "}\n");

  /* Minus y side */

  fprintf(vrmlfile, "Shape {\n");
  fprintf(vrmlfile, "  appearance Appearance{\n");
  fprintf(vrmlfile, "     material Material {diffuseColor    1 1 1}\n");
  fprintf(vrmlfile, "     texture ImageTexture {url \"minusy.gif\"}\n");
  fprintf(vrmlfile, "  }\n");
  fprintf(vrmlfile, "  geometry IndexedFaceSet {\n");
  fprintf(vrmlfile, "     coord Coordinate {\n");
  fprintf(vrmlfile, "        point [\n");
  fprintf(vrmlfile, "           #bottom\n");
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 0\n", x1, y1, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 1\n", x2, y1, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 2\n", x2, y2, z1);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 3\n", x1, y2, z1);
  fprintf(vrmlfile, "           #top\n");
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 4\n", x1, y1, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 5\n", x2, y1, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 6\n", x2, y2, z2);
  fprintf(vrmlfile, "           %.4f %.4f %.4f #vertex 7\n", x1, y2, z2);
  fprintf(vrmlfile, "        ]\n");
  fprintf(vrmlfile, "     }\n");
  fprintf(vrmlfile, "     coordIndex [\n");
  fprintf(vrmlfile, "        #-y side\n");
  fprintf(vrmlfile, "        0, 1, 5, 4, 0, -1,\n");
  fprintf(vrmlfile, "     ]\n");
  fprintf(vrmlfile, "     texCoord TextureCoordinate{\n");
  fprintf(vrmlfile,
          "        point "
          "[0.0000,0.0000,1.0000,0.0000,1.0000,1.0000,0.0000,1.0000]}\n");
  fprintf(vrmlfile, "  }\n");
  fprintf(vrmlfile, "}\n");
  fprintf(vrmlfile, "]}");

  fclose(vrmlfile);

  return;
}
