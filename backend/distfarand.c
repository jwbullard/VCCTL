/******************************************************
 *
 * Program distfarand to distribute fly ash phases
 * randomly on a pixel basis amongst fly ash particles
 * (May 1997)
 *
 * Programmer:	Dale P. Bentz
 * 				Building and Fire Research Laboratory
 *				NIST
 *				100 Bureau Drive Mail Stop 8621
 *				Gaithersburg, MD  20899-8621   USA
 *				(301) 975-5865      FAX: (301) 990-6891
 *				E-mail: dale.bentz@nist.gov
 *
 * Contact:		Jeffrey W. Bullard
 * 				Building and Fire Research Laboratory
 *				NIST
 *				100 Bureau Drive Mail Stop 8621
 *				Gaithersburg, MD  20899-8621   USA
 *				(301) 975-5725      FAX: (301) 990-6891
 *				E-mail: bullard@nist.gov
 *
 *******************************************************/
#include "include/vcctl.h"
#include <stdio.h>
#include <stdlib.h>

#define NPARTC 12000

/***
 *	Global variables
 ***/

int *Seed;
int Xsyssize, Ysyssize, Zsyssize;
float Res = DEFAULTRESOLUTION;
/* VCCTL software version used to create input file */
float Version;

int main(void) {
  int ix, iy, iz, valin, ovalin, valout, nseed;
  float probasg, probcacl2, probsio2;
  float probc3a, prph, probcas2, probanh;
  char filein[MAXSTRING], fileout[MAXSTRING];
  char instring[MAXSTRING];
  FILE *infile, *outfile;

  printf("Enter random number seed value (<0)\n");
  read_string(instring, sizeof(instring));
  nseed = atoi(instring);
  printf("%d\n", nseed);
  Seed = &nseed;

  printf("Enter name of file for input \n");
  read_string(filein, sizeof(filein));
  printf("%s\n", filein);

  printf("Enter name of file for output \n");
  read_string(fileout, sizeof(fileout));
  printf("%s\n", fileout);

  /* Get user input for phase probabilities (volume fractions) */

  printf("Enter probability for fly ash to be aluminosilicate glass \n");
  read_string(instring, sizeof(instring));
  probasg = atof(instring);
  printf("%f\n", probasg);
  printf("Enter probability for fly ash to be calcium aluminodisilicate \n");
  read_string(instring, sizeof(instring));
  probcas2 = atof(instring);
  printf("%f\n", probcas2);
  printf("Enter probability for fly ash to be tricalcium aluminate \n");
  read_string(instring, sizeof(instring));
  probc3a = atof(instring);
  printf("%f\n", probc3a);
  printf("Enter probability for fly ash to be calcium chloride \n");
  read_string(instring, sizeof(instring));
  probcacl2 = atof(instring);
  printf("%f\n", probcacl2);
  printf("Enter probability for fly ash to be silica \n");
  read_string(instring, sizeof(instring));
  probsio2 = atof(instring);
  printf("%f\n", probsio2);
  printf("Enter probability for fly ash to be anhydrite \n");
  read_string(instring, sizeof(instring));
  probanh = atof(instring);
  printf("%f\n", probanh);
  fflush(stdout);

  /***
   *	Convert probabilities to cumulative
   *
   *	Order must be the same as in for loop below
   ***/

  probcacl2 += probasg;
  probsio2 += probcacl2;
  probanh += probsio2;
  probcas2 += probanh;
  probc3a += probcas2;

  infile = filehandler("distfarand", filein, "READ");
  if (!infile) {
    exit(1);
  }

  outfile = filehandler("distfarand", fileout, "WRITE");
  if (!outfile) {
    fclose(infile);
    exit(1);
  }

  /***
   *	Determine whether system size and resolution
   *	are specified in the image file
   ***/

  if (read_imgheader(infile, &Version, &Xsyssize, &Ysyssize, &Zsyssize, &Res)) {
    fclose(infile);
    fclose(outfile);
    bailout("distfarand", "Error reading image header");
    exit(1);
  }

  /***
   *	Print header information about software version,
   *	system size, and resolution to the output file
   ***/

  if (write_imgheader(outfile, Xsyssize, Ysyssize, Zsyssize, Res)) {
    fclose(infile);
    fclose(outfile);
    bailout("distfarand", "Error reading image header");
    exit(1);
  }

  /* First scan-- find each particle and assign phases */

  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {

        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valin = convert_id(ovalin, Version);

        valout = valin;

        if (valin == FLYASH) {

          valout = INERT;
          prph = ran1(Seed);
          if (prph < probasg) {

            valout = ASG;

          } else if (prph < probcacl2) {

            valout = CACL2;

          } else if (prph < probsio2) {

            valout = AMSIL;

          } else if (prph < probanh) {

            valout = ANHYDRITE;

          } else if (prph < probcas2) {

            valout = CAS2;

          } else if (prph < probc3a) {

            valout = C3A;
          }
        }

        fprintf(outfile, "%d\n", valout);

      } /* End of iz loop */
    }   /* End of iy loop */
  }     /* End of ix loop */

  fclose(infile);
  fclose(outfile);
  return (0);
}
