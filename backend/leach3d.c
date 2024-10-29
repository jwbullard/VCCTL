/******************************************************
 *
 * Program leach3d.c to leach one or more phases
 * from a hydrated 3D microstructure
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

#define NEIGHBORS 6 /* Number of neighbors to check in leaching */
#define NUMLEACHABLE 6

/***
 *	Global variables
 ***/

int ***Mic;
int Xsyssize, Ysyssize, Zsyssize;
int Phase[NUMLEACHABLE], Leach[NUMLEACHABLE];
int *Seed;
int Xoff[27] = {1, 0, 0,  -1, 0, 0, 1, 1, -1, -1, 0,  0,  0, 0,
                1, 1, -1, -1, 1, 1, 1, 1, -1, -1, -1, -1, 0};
int Yoff[27] = {0, 1, 0, 0, -1, 0,  1, -1, 1, -1, 1,  -1, 1, -1,
                0, 0, 0, 0, 1,  -1, 1, -1, 1, 1,  -1, -1, 0};
int Zoff[27] = {0, 0,  1, 0,  0, -1, 0,  0,  0, 0,  1, 1,  -1, -1,
                1, -1, 1, -1, 1, 1,  -1, -1, 1, -1, 1, -1, 0};
float Res;

/* VCCTL software version used to create input file */
float Version;

/***
 *	Function declarations
 ***/

int chckedge(int xck, int yck, int zck);
void passleach(float prleach);

int main(void) {
  int iseed, k, ix, iy, iz, valin, ovalin, chl, c3sl, c2sl, c3al, c4afl,
      leachcyc;
  float testf, leachprob;
  char filein[MAXSTRING], fileout[MAXSTRING], instring[MAXSTRING];
  FILE *infile, *outfile;

  Mic = NULL;

  Phase[1] = CH;
  Phase[2] = C3S;
  Phase[3] = C2S;
  Phase[4] = C3A;
  Phase[5] = C4AF;

  printf("Enter name of file to be leached: \n");
  read_string(filein, sizeof(filein));
  printf("%s\n", filein);
  printf("Enter name of file to store leached microstructure in: \n");
  read_string(fileout, sizeof(fileout));
  printf("%s\n", fileout);

  infile = filehandler("leach3d", filein, "READ");
  if (!infile) {
    exit(1);
  }

  /****
   *	NOTE:  MUST READ
   *			(1) SOFTWARE VERSION (Version)
   *			(1) SYSTEM SIZE (Xsyssize,Ysyssize,Zsyssize)
   *			(2) SYSTEM RESOLUTION (Res)
   *
   ****/

  if (read_imgheader(infile, &Version, &Xsyssize, &Ysyssize, &Zsyssize, &Res)) {
    fclose(infile);
    bailout("leach3d", "Error reading image header");
    exit(1);
  }

  /***
   *	Allocate memory for the global 3D array
   *	called Mic
   ***/

  Mic = ibox(Xsyssize, Ysyssize, Zsyssize);
  if (!Mic) {
    fclose(infile);
    bailout("leach3d", "Could not allocate memory for Mic array");
    exit(1);
  }

  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {

        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valin = convert_id(ovalin, Version);
        Mic[ix][iy][iz] = valin;
      }
    }
  }

  fclose(infile);

  printf("Enter on/off (0/1) selections for CH, C3S, C2S, C3A,and C4AF \n");
  printf("(one entry per line)\n");
  read_string(instring, sizeof(instring));
  chl = atoi(instring);
  Leach[1] = chl;
  read_string(instring, sizeof(instring));
  c3sl = atoi(instring);
  Leach[2] = c3sl;
  read_string(instring, sizeof(instring));
  c2sl = atoi(instring);
  Leach[3] = c2sl;
  read_string(instring, sizeof(instring));
  c3al = atoi(instring);
  Leach[4] = c3al;
  read_string(instring, sizeof(instring));
  c4afl = atoi(instring);
  Leach[5] = c4afl;

  printf("Enter number of cycles of leaching to execute \n");
  read_string(instring, sizeof(instring));
  leachcyc = atoi(instring);
  printf("Enter probability for leaching a selected pixel\n");
  read_string(instring, sizeof(instring));
  leachprob = atof(instring);
  printf("Enter random number seed for leaching \n");
  read_string(instring, sizeof(instring));
  iseed = atoi(instring);
  if (iseed > 0)
    iseed = (-1 * iseed);
  Seed = &iseed;
  testf = ran1(Seed);

  if (!leachcyc) {

    /***
     *	User asked to leach the phases completely
     *	from the microstructure, so the task is
     *	a simple seek-and-destroy on those phases
     ***/

    for (iz = 0; iz < Zsyssize; iz++) {
      for (iy = 0; iy < Ysyssize; iy++) {
        for (ix = 0; ix < Xsyssize; ix++) {

          for (k = 1; k < NUMLEACHABLE; k++) {
            if ((Mic[ix][iy][iz] == Phase[k]) && (Leach[k])) {

              Mic[ix][iy][iz] = POROSITY;
            }
          }
        }
      }
    }
  } else {

    /***
     *	User asked to leach for only a given number
     *	of cycles.  Function passleach takes care of
     *	the leaching over one cycle
     ***/

    for (ix = 1; ix <= leachcyc; ix++) {
      passleach(leachprob);
    }
  }

  outfile = filehandler("leach3d", fileout, "WRITE");
  if (!outfile) {
    free_ibox(Mic, Xsyssize, Ysyssize);
    exit(1);
  }

  /***
   *	Output the image header to the final
   *	microstructure
   ***/

  if (write_imgheader(outfile, Xsyssize, Ysyssize, Zsyssize, Res)) {
    fclose(outfile);
    free_ibox(Mic, Xsyssize, Ysyssize);
    bailout("leach3d", "Error writing image header");
    exit(1);
  }

  for (iz = 0; iz < Zsyssize; iz++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (ix = 0; ix < Xsyssize; ix++) {
        fprintf(outfile, "%d\n", Mic[ix][iy][iz]);
      }
    }
  }

  fclose(outfile);
  free_ibox(Mic, Xsyssize, Ysyssize);

  return (0);
}

/***
 *	chckedge
 *
 * 	Check if a pixel located at (xck,yck,zck) is on a
 * 	surface with pore space in the 3D system
 *
 * 	Arguments:	integer x,y, and z coordinates to check
 *
 * 	Returns:	1 if on a surface, 0 otherwise
 *
 *	Calls:		no other routines
 *	Called by:	passleach
 ***/
int chckedge(int xck, int yck, int zck) {
  int edgeback = 0;
  int x2, y2, z2;
  int ip;

  /***
   *	Check all neighboring pixels (6, 18, or 26)
   *	and use periodic boundary conditions
   *
   *	Change number of NEIGHBORS in header file
   *	called disrealnew.h
   ***/

  for (ip = 0; ((ip < NEIGHBORS) && (!edgeback)); ip++) {

    x2 = xck + Xoff[ip];
    y2 = yck + Yoff[ip];
    z2 = zck + Zoff[ip];

    x2 += checkbc(x2, Xsyssize);
    y2 += checkbc(y2, Ysyssize);
    z2 += checkbc(z2, Zsyssize);

    if (Mic[x2][y2][z2] == POROSITY)
      edgeback = 1;
  }

  return (edgeback);
}

/***
 *	passleach
 *
 *	Routine to adjust local position if outside system boundaries
 *	Uses periodic boundary conditions in every direction
 *
 *	Arguments:	Float probability of leaching
 *	Returns:	Nothing
 *
 *	Calls:		No functions
 *	Called by:	main
 ***/
void passleach(float prleach) {
  int xid, yid, zid, phid, edgef, phread;

  /***
   *	Scan the entire 3-D microstructure
   *	and identify leachable sites
   ***/

  for (zid = 0; zid < Zsyssize; zid++) {
    for (yid = 0; yid < Ysyssize; yid++) {
      for (xid = 0; xid < Xsyssize; xid++) {

        phread = Mic[xid][yid][zid];
        phid = 0;

        if (phread == CH) {
          phid = 1;
        } else if (phread == C3S) {
          phid = 2;
        } else if (phread == C2S) {
          phid = 3;
        } else if (phread == C3A) {
          phid = 4;
        } else if (phread == C4AF) {
          phid = 5;
        }

        /* Only examine leachable phases */

        if (phid != 0) {

          /***
           *	If phase is soluble, see if it
           *	is in contact with porosity
           ***/

          if (Leach[phid] == 1) {

            edgef = chckedge(xid, yid, zid);

            if (edgef) {

              /***
               *	Surface eligible species has an
               *	ID OFFSET greater than its original
               *	value
               ***/

              Mic[xid][yid][zid] += OFFSET;
            }
          }
        }

      } /* End of zid */
    }   /* End of yid */
  }     /* End of xid */

  /* Now perform the leaching */

  for (zid = 0; zid < Zsyssize; zid++) {
    for (yid = 0; yid < Ysyssize; yid++) {
      for (xid = 0; xid < Xsyssize; xid++) {

        if (Mic[xid][yid][zid] >= OFFSET) {

          if (ran1(Seed) < prleach) {
            Mic[xid][yid][zid] = 0;
          } else {

            /***
             *	Restore the pixel to its
             *	original phase
             ***/

            Mic[xid][yid][zid] -= OFFSET;
          }
        }
      }
    }
  }
}
