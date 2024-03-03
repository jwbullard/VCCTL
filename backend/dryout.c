/******************************************************
 *
 * Program dryout
 *
 * Reads a 3D VCCTL image file and dries it to a prescribed
 * degree of saturation if possible.
 ******************************************************/
#include "include/vcctl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* System size (in pixels) and resolution (in microns) */

int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
int Syspix = DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE * DEFAULTSYSTEMSIZE;
float Res = DEFAULTRESOLUTION;

/* Number of types of pixels and solid pixels*/
int Npixtypes, Nsphases;

/* VCCTL software version used to create input file */
float Version;
int Cubesize = 7;
int Cubemin = 3;

/***
 *	Data structure for elements to remove to simulate
 *	self-dessication.  The list is once again a doubly linked
 *	list to be dynamically allocated and managed
 ***/
typedef struct _Togo {
  int x, y, z, npore;
  struct _Togo *nexttogo;
  struct _Togo *prevtogo;
} Togo;

/***
 *	Global variables
 ***/
int ***Mic;
float Version;

size_t Togosize;

/***
 *	Saturated porosity of CSH gel
 ***/
const float Gelporefrac = 0.38;

/***
 *	Function declarations
 ***/
void removewater(int ndesire, int *spc, int *dpc);
int countbox(int boxsize, int qx, int qy, int qz);

int main(void) {
  register int i, j, k;
  int ovalin, valout;
  int cshcount, aggcount, satporecount, dryporecount, totporecount;
  int numtoremove, target_satporecount;
  float target_deg_sat, cur_deg_sat, min_deg_sat, target_satcap;
  float vfcsh, satcap, drycap, gelporosity;
  char filein[MAXSTRING], fileout[MAXSTRING], instring[MAXSTRING];
  FILE *infile, *outfile;

  Togosize = sizeof(Togo);

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

  infile = filehandler("dryout", filein, "READ");
  if (!infile) {
    exit(1);
  }

  /***
   *	Read first line of image file to determine
   *	if size is specified.  If it is specified
   *	then read it.  If not, set the size to 100
   ***/

  if (read_imgheader(infile, &Version, &Xsyssize, &Ysyssize, &Zsyssize, &Res)) {
    bailout("oneimage", "Error reading image header");
    exit(1);
  }

  printf("\nDone reading image header:");
  printf("\n\tVersion = %f", Version);
  printf("\n\txsyssize = %d", Xsyssize);
  printf("\n\tysyssize = %d", Ysyssize);
  printf("\n\tzsyssize = %d", Zsyssize);
  printf("\n\tres = %f\n", Res);
  fflush(stdout);

  Mic = ibox(Xsyssize, Ysyssize, Zsyssize);
  if (!Mic) {
    fclose(infile);
    bailout("dryout", "Could not allocate memory for Mic");
    fflush(stdout);
    exit(1);
  }

  printf("\nSuccessfully allocated memory for Mic array.");
  fflush(stdout);

  printf("\nPreparing to scan image file... ");
  fflush(stdout);
  cshcount = satporecount = dryporecount = aggcount = 0;
  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {
        fscanf(infile, "%s", instring);
        ovalin = atoi(instring);
        valout = convert_id(ovalin, Version);
        Mic[i][j][k] = valout;
        if (valout == INERTAGG)
          aggcount++;
        if (valout == CSH || valout == POZZCSH)
          cshcount++;
        if (valout == POROSITY)
          satporecount++;
        if (valout == EMPTYP || valout == EMPTYDP || valout == DRIEDP)
          dryporecount++;
      }
    }
  }

  fclose(infile);

  totporecount = satporecount + dryporecount;

  printf("Done!");
  fflush(stdout);

  printf("Enter the desired degree of saturation: \n");
  fflush(stdout);
  read_string(instring, sizeof(instring));
  printf("%s\n", instring);
  fflush(stdout);
  target_deg_sat = atof(instring);

  /***
   * Calculate current degree of saturation and minimum possible degree of
   *saturation
   ***/

  vfcsh = ((float)cshcount) /
          ((float)((Xsyssize * Ysyssize * Zsyssize) - aggcount));
  gelporosity = vfcsh * Gelporefrac;
  satcap = ((float)satporecount) /
           ((float)((Xsyssize * Ysyssize * Zsyssize) - aggcount));
  drycap = ((float)dryporecount) /
           ((float)((Xsyssize * Ysyssize * Zsyssize) - aggcount));
  cur_deg_sat = (satcap + gelporosity) / (satcap + gelporosity + drycap);
  min_deg_sat = gelporosity / (satcap + gelporosity + drycap);

  printf("\nVolume fraction CSH = %f\n", vfcsh);
  printf("\nSaturated gel porosity = %f\n", gelporosity);
  printf("\nSaturated capillary porosity = %f\n", satcap);
  printf("\nDry capillary porosity = %f\n", drycap);
  printf("\nCurrent degree of saturation = %f\n", cur_deg_sat);
  printf("Minimum degree of saturation = %f\n", min_deg_sat);
  if (target_deg_sat < min_deg_sat) {
    target_deg_sat = min_deg_sat;
    printf("Setting target degree of saturation to minimum value = %f\n",
           target_deg_sat);
  }
  fflush(stdout);

  /***
   * How many pixels of saturated porosity should we remove to achieve this
   *degree of saturation?
   ***/

  target_satcap =
      (target_deg_sat * (satcap + gelporosity + drycap)) - gelporosity;
  target_satporecount =
      (int)((target_satcap *
             ((float)((Xsyssize * Ysyssize * Zsyssize) - aggcount))) +
            0.5);
  numtoremove = satporecount - target_satporecount;

  removewater(numtoremove, &satporecount, &dryporecount);

  /***
   *  Did it work?
   ***/

  satcap = ((float)satporecount) /
           ((float)((Xsyssize * Ysyssize * Zsyssize) - aggcount));
  drycap = ((float)dryporecount) /
           ((float)((Xsyssize * Ysyssize * Zsyssize) - aggcount));
  cur_deg_sat = (satcap + gelporosity) / (satcap + gelporosity + drycap);

  printf("\n\nDone with removing moisture.\n");
  printf("New degree of saturation = %f\n", cur_deg_sat);
  printf("Percentage error = %f\n\n",
         (cur_deg_sat - target_deg_sat) / (target_deg_sat));

  /***
   * Now output the final microstructure
   ***/

  outfile = filehandler("dryout", fileout, "WRITE");
  if (!outfile) {
    exit(1);
  }

  if (write_imgheader(outfile, Xsyssize, Ysyssize, Zsyssize, Res)) {
    fclose(outfile);
    free_ibox(Mic, Xsyssize, Ysyssize);
    bailout("dryout", "Error writing image header");
    exit(1);
  }

  for (k = 0; k < Zsyssize; k++) {
    for (j = 0; j < Ysyssize; j++) {
      for (i = 0; i < Xsyssize; i++) {
        fprintf(outfile, "%d\n", Mic[i][j][k]);
      }
    }
  }

  fclose(outfile);
  free_ibox(Mic, Xsyssize, Ysyssize);
  return (0);
}

/***
 *    removewater
 *
 *    Create ndesire pixels of empty pore space to simulate
 *    self-desiccation
 *
 *     Arguments:    int ndesire (number to create)
 *
 *     Returns:    nothing
 *
 *    Calls:        countbox
 *    Called by:    main
 ***/
void removewater(int ndesire, int *spc, int *dpc) {
  int idesire;
  int px, py, pz, placed, cntpore, cntmax;
  Togo *headtogo, *tailtogo, *newtogo, *lasttogo, *onetogo;

  /***
   *    First allocate and initialize the first member
   *    of the linked list
   ***/

  headtogo = (Togo *)malloc(Togosize);
  headtogo->x = headtogo->y = headtogo->z = (-1);
  headtogo->npore = 0;
  headtogo->nexttogo = NULL;
  headtogo->prevtogo = NULL;
  tailtogo = headtogo;
  cntmax = 0;

  /***
   *    Add needed number of elements to the end of the list
   *    Consider allocating the space in chunks of, say, 50,
   *    instead of one at a time to speed up execution
   ***/

  for (idesire = 2; idesire <= ndesire; idesire++) {
    newtogo = (Togo *)malloc(Togosize);
    newtogo->npore = 0;
    newtogo->x = newtogo->y = newtogo->z = (-1);
    tailtogo->nexttogo = newtogo;
    newtogo->prevtogo = tailtogo;
    tailtogo = newtogo;
  }

  /* Now scan the microstructure and RANK the sites */

  for (pz = 0; pz < Zsyssize; pz++) {
    for (py = 0; py < Ysyssize; py++) {
      for (px = 0; px < Xsyssize; px++) {

        if (Mic[px][py][pz] == POROSITY) {
          cntpore = countbox(Cubesize, px, py, pz);

          if (cntpore > cntmax)
            cntmax = cntpore;

          /***
           *    Store this site value at appropriate place in
           *    sorted linked list
           ***/

          if (cntpore > (tailtogo->npore)) {
            placed = 0;
            lasttogo = tailtogo;
            while (!placed) {
              newtogo = lasttogo->prevtogo;
              if (!newtogo) {
                placed = 2;
              } else if (cntpore <= (newtogo->npore)) {
                placed = 1;
              }

              if (!placed)
                lasttogo = newtogo;
            }

            onetogo = (Togo *)malloc(Togosize);
            onetogo->x = px;
            onetogo->y = py;
            onetogo->z = pz;
            onetogo->npore = cntpore;

            /* Insertion at the head of the list */

            if (placed == 2) {
              onetogo->prevtogo = NULL;
              onetogo->nexttogo = headtogo;
              headtogo->prevtogo = onetogo;
              headtogo = onetogo;
            }

            if (placed == 1) {
              onetogo->nexttogo = lasttogo;
              onetogo->prevtogo = newtogo;
              lasttogo->prevtogo = onetogo;
              newtogo->nexttogo = onetogo;
            }

            /* Eliminate the last element */

            lasttogo = tailtogo;
            tailtogo = tailtogo->prevtogo;
            tailtogo->nexttogo = NULL;
            free(lasttogo);
          }
        }

      } /* End of loop in z */
    }   /* End of loop in y */
  }     /* End of loop in x */

  /***
   *    Now remove the sites starting at the
   *    head of the list and free all of the
   *    used memory
   ***/

  for (idesire = 1; idesire <= ndesire; idesire++) {
    px = headtogo->x;
    py = headtogo->y;
    pz = headtogo->z;

    if (px != (-1)) {
      Mic[px][py][pz] = EMPTYP;
      *spc -= 1;
      *dpc += 1;
    }

    lasttogo = headtogo;
    headtogo = headtogo->nexttogo;
    free(lasttogo);
  }

  /***
   *    If only small cubes of porosity were found,
   *    then adjust Cubesize to have a more efficient
   *    search in the future
   ***/

  if (Cubesize > Cubemin) {
    if ((2 * cntmax) < (Cubesize * Cubesize * Cubesize)) {
      Cubesize -= 2;
    }
  }
  return;
}

/***
 *    countbox
 *
 *     Count the number of pore pixels within a cube of
 *     size boxsize, centered at (qx,qy,qz)
 *
 *     Arguments:    int boxsize
 *                 int x,y, and z coordinates of box center
 *
 *     Returns:    int number of pore pixels found within box
 *
 *    Calls:        no other routines
 *    Called by:    makeinert
 ***/
int countbox(int boxsize, int qx, int qy, int qz) {
  int nfound, ix, iy, iz, qxlo, qxhi, qylo, qyhi, qzlo, qzhi;
  int hx, hy, hz, boxhalf;

  boxhalf = boxsize / 2;
  nfound = 0;
  qxlo = qx - boxhalf;
  qxhi = qx + boxhalf;
  qylo = qy - boxhalf;
  qyhi = qy + boxhalf;
  qzlo = qz - boxhalf;
  qzhi = qz + boxhalf;

  /***
   *    Count the number of requisite pixels in the
   *    3-D cube box using periodic boundaries
   ***/

  for (ix = qxlo; ix <= qxhi; ix++) {
    hx = ix;
    hx += checkbc(hx, Xsyssize);

    for (iy = qylo; iy <= qyhi; iy++) {
      hy = iy;
      hy += checkbc(hy, Ysyssize);

      for (iz = qzlo; iz <= qzhi; iz++) {
        hz = iz;
        hz += checkbc(hz, Zsyssize);

        /***
         *    Count if porosity, diffusing species,
         *    or empty porosity
         ***/

        if ((Mic[hx][hy][hz] == POROSITY) || (Mic[hx][hy][hz] > NSPHASES)) {

          nfound++;
        }

      } /* End of loop over z */
    }   /* End of loop over y */
  }     /* End of loop over x */

  return (nfound);
}
