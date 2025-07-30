/******************************************************
 *
 * Program distfapart to distribute fly ash phases
 * randomly amongst monophase particles (May 1997)
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
#include <string.h>

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
  int *phase, *partid;
  int jx, jy, jz;
  int ix, iy, iz, valin, ovalin, valout, partin;
  int nseed, count, c1, phnew, mult;
  int totcnt, ascnt, cacl2cnt, amsilcnt, inertcnt;
  int anhcnt, cas2cnt, c3acnt;
  int markc3a, markas, markcacl2, markamsil, markinert, markanh, markcas2;
  float probasg, probcacl2, probsio2;
  float probc3a, prph, probcas2, probanh;
  float jver, jres;
  char filein[MAXSTRING], fileout[MAXSTRING], filepart[MAXSTRING];
  char instring[MAXSTRING];
  FILE *infile, *partfile, *outfile;

  phase = NULL;
  partid = NULL;
  mult = 1;

  /***
   *	Initial allocation of memory for phase
   *	and partid arrays
   ***/

  phase = (int *)calloc((size_t)NPARTC, sizeof(int));
  if (!phase) {
    bailout("distfapart", "Could not allocate memory for phase");
    exit(1);
  }

  partid = (int *)calloc((size_t)NPARTC, sizeof(int));
  if (!partid) {
    free(phase);
    bailout("distfapart", "Could not allocate memory for partid");
    exit(1);
  }

  ascnt = cacl2cnt = amsilcnt = inertcnt = 0;
  cas2cnt = anhcnt = c3acnt = 0;

  printf("Enter random number seed value (<0)\n");
  read_string(instring, sizeof(instring));
  nseed = atoi(instring);
  printf("%d\n", nseed);
  Seed = &nseed;

  printf("Enter name of file for input \n");
  read_string(filein, sizeof(filein));
  printf("%s\n", filein);
  printf("Enter name of file for particle IDs \n");
  read_string(filepart, sizeof(filepart));
  printf("%s\n", filepart);

  printf("Enter name of file for output \n");
  read_string(fileout, sizeof(fileout));
  printf("%s\n", fileout);

  printf("Enter total number of fly ash pixels \n");
  read_string(instring, sizeof(instring));
  totcnt = atoi(instring);
  printf("%d\n", totcnt);

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

  /* Determine goal counts for each phase */

  markas = probasg * (float)totcnt;
  markamsil = probsio2 * (float)totcnt;
  markcacl2 = probcacl2 * (float)totcnt;
  markanh = probanh * (float)totcnt;
  markcas2 = probcas2 * (float)totcnt;
  markc3a = probc3a * (float)totcnt;
  markinert =
      (1.0 - probasg - probsio2 - probcacl2 - probanh - probcas2 - probc3a) *
      (float)totcnt;

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

  infile = filehandler("distfapart", filein, "READ");
  if (!infile) {
    free(phase);
    free(partid);
    exit(1);
  }

  partfile = filehandler("distfapart", filepart, "READ");
  if (!partfile) {
    fclose(infile);
    free(phase);
    free(partid);
    exit(1);
  }

  for (ix = 0; ix < NPARTC; ix++) {
    phase[ix] = partid[ix] = 0;
  }

  count = 0;

  /***
   *	Determine whether system size and resolution
   *	are specified in the image file
   ***/

  if (read_imgheader(infile, &Version, &Xsyssize, &Ysyssize, &Zsyssize, &Res)) {
    fclose(infile);
    fclose(partfile);
    free(phase);
    free(partid);
    bailout("distfapart", "Error reading image header");
    exit(1);
  }

  if (read_imgheader(partfile, &jver, &jx, &jy, &jz, &jres)) {
    fclose(infile);
    fclose(partfile);
    free(phase);
    free(partid);
    bailout("distfapart", "Error reading image header");
    exit(1);
  }

  /* First scan-- find each particle and assign phases */

  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {

        fscanf(partfile, "%s", instring);
        partin = atoi(instring);
        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);

        valin = convert_id(ovalin, Version);

        if ((valin == FLYASH) && (partid[partin] == 0)) {

          count++;

          if (count >= mult * NPARTC) {
            mult++;
            partid = (int *)realloc((int *)partid, (size_t)(mult * NPARTC));
            if (!partid) {
              free(phase);
              fclose(partfile);
              fclose(infile);
              bailout("distfapart", "Could not reallocate partid");
              exit(1);
            }

            phase = (int *)realloc((int *)phase, (size_t)(mult * NPARTC));
            if (!phase) {
              free(partid);
              fclose(partfile);
              fclose(infile);
              bailout("distfapart", "Could not reallocate partid");
              exit(1);
            }
          }

          partid[partin] = count;

          valout = INERT;
          do {
            prph = ran1(Seed);

            if ((prph < probasg) && (ascnt < markas)) {

              valout = ASG;

            } else if ((prph < probcacl2) && (cacl2cnt < markcacl2)) {

              valout = CACL2;

            } else if ((prph < probsio2) && (amsilcnt < markamsil)) {

              valout = AMSIL;

            } else if ((prph < probanh) && (anhcnt < markanh)) {

              valout = ANHYDRITE;

            } else if ((prph < probcas2) && (cas2cnt < markcas2)) {

              valout = CAS2;

            } else if ((prph < probc3a) && (c3acnt < markc3a)) {

              valout = C3A;
            }
          } while ((valout == INERT) && (inertcnt > markinert));

          phase[count] = valout;
        }

        if (valin == FLYASH) {

          c1 = partid[partin];
          phnew = phase[c1];

          switch (phnew) {
          case ASG:
            ascnt++;
            break;
          case CACL2:
            cacl2cnt++;
            break;
          case AMSIL:
            amsilcnt++;
            break;
          case ANHYDRITE:
            anhcnt++;
            break;
          case CAS2:
            cas2cnt++;
            break;
          case C3A:
            c3acnt++;
            break;
          case INERT:
            inertcnt++;
            break;
          default:
            break;
          }
        }

      } /* End of iz loop */
    }   /* End of iy loop */
  }     /* End of ix loop */

  rewind(infile);
  rewind(partfile);

  if (read_imgheader(infile, &jver, &jx, &jy, &jz, &jres)) {
    fclose(infile);
    fclose(partfile);
    free(phase);
    free(partid);
    bailout("distfapart", "Error reading image header");
    exit(1);
  }

  if (read_imgheader(partfile, &jver, &jx, &jy, &jz, &jres)) {
    fclose(infile);
    fclose(partfile);
    free(phase);
    free(partid);
    bailout("distfapart", "Error reading image header");
    exit(1);
  }

  /* Now distribute phases in second scan */

  outfile = filehandler("distfapart", fileout, "WRITE");
  if (!outfile) {
    free(phase);
    free(partid);
    fclose(infile);
    fclose(partfile);
    exit(1);
  }

  /***
   *	Output the software version to the final
   *	microstructure
   ***/

  if (write_imgheader(outfile, Xsyssize, Ysyssize, Zsyssize, Res)) {
    free(phase);
    free(partid);
    fclose(outfile);
    fclose(infile);
    fclose(partfile);
    bailout("distfapart", "Error writing image header");
    exit(1);
  }

  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {

        fscanf(partfile, "%s", instring);
        partin = atoi(instring);
        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valin = convert_id(ovalin, Version);
        valout = valin;

        if (valin == FLYASH) {
          count = partid[partin];
          valout = phase[count];
        }

        fprintf(outfile, "%d\n", valout);
      }
    }
  }

  fclose(infile);
  fclose(partfile);
  fclose(outfile);

  free(partid);
  free(phase);
  return (0);
}
