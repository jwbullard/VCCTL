/******************************************************************************
 *	Function filehandler does graceful handling of opening
 *	files for various input/output combinations as requested
 *	by function call, and also prints nice message to stdout
 *	if something goes wrong.
 *
 *	Programmer:	Jeffrey W. Bullard
 *				NIST
 *				100 Bureau Drive, Stop 8615
 *				Gaithersburg, Maryland  20899-8615
 *				USA
 *
 *				Phone:	301.975.5725
 *				Fax:	301.990.6891
 *				bullard@nist.gov
 *
 *	16 March 2004
 ******************************************************************************/
#include "../include/vcctl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

FILE *filehandler(char *prog, char *filename, char *tocheck) {
  FILE *fptr;

  fptr = NULL;

  if (!strcmp(tocheck, "NOCLOBBER")) {
    if ((fptr = fopen(filename, "r")) != NULL) {
      printf("\nERROR in %s:", prog);
      printf("\n\tFile %s already exists.", filename);
      printf("\n\tPlease verify file name. Program is ");
      printf("exiting now.\n\n");
      fflush(stdout);
      fclose(fptr);
      fptr = NULL;
    } else if ((fptr = fopen(filename, "w")) == NULL) {
      printf("\nERROR in %s:", prog);
      printf("\n\tCould not create file %s", filename);
      printf("\n\tPlease verify write permissions. Program is ");
      printf("exiting now.\n\n");
      fflush(stdout);
    }
  } else if (!strcmp(tocheck, "READ")) {

    if ((fptr = fopen(filename, "r")) == NULL) {
      printf("\nERROR in %s:", prog);
      printf("\n\tFile %s could not be opened for ", filename);
      printf("reading.");
      printf("\n\tPlease verify file name. Program is ");
      printf("exiting now.\n\n");
      fflush(stdout);
    }

  } else if (!strcmp(tocheck, "READ_NOFAIL")) {

    fptr = fopen(filename, "r");

  } else if (!strcmp(tocheck, "WRITE")) {

    if ((fptr = fopen(filename, "w")) == NULL) {
      printf("\nERROR in %s:", prog);
      printf("\n\tFile %s could not be created.", filename);
      printf("\n\tPlease verify file name. Program is ");
      printf("exiting now.\n\n");
      fflush(stdout);
    }

  } else if (!strcmp(tocheck, "APPEND")) {

    if ((fptr = fopen(filename, "a")) == NULL) {
      printf("\nERROR in %s:", prog);
      printf("\n\tFile %s could not be opened for ", filename);
      printf("appending.");
      printf("\n\tPlease verify file name. Program ");
      printf("is exiting now.\n\n");
      fflush(stdout);
    }
  }

  return (fptr);
}
