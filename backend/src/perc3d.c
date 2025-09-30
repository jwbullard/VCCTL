/*****************************************************
 *
 * Program perc3d.c to test connectivity of various
 * phases in a 3D microstructure
 *
 * Programmer:	Jeffrey W. Bullard
 *              Zachry Department of Civil and Environmental Engineering
 *              Department of Materials Science and Engineering
 *              Texas A&M University
 *              College Station, Texas 77843
 *              jwbullard@tamu.edu
 *
 *******************************************************/
#include "include/vcctl.h"
#include <locale.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#define TOTCSH OFFSET
#define TOTGYP OFFSET + 1

#define MEMERR -1

/* label for a burnt pixel */
#define BURNT 70

/* default size of matrices for holding burning locations */
#define SIZE2D 200000

/* functions defining coordinates for burning in any of three directions */
#define cx(x, y, z, a, b, c) (1 - b - c) * x + (1 - a - c) * y + (1 - a - b) * z
#define cy(x, y, z, a, b, c) (1 - a - b) * x + (1 - b - c) * y + (1 - a - c) * z
#define cz(x, y, z, a, b, c) (1 - a - c) * x + (1 - a - b) * y + (1 - b - c) * z

/***
 *	Global variables
 ***/
short int ***Mic;
int Xsyssize = DEFAULTSYSTEMSIZE;
int Ysyssize = DEFAULTSYSTEMSIZE;
int Zsyssize = DEFAULTSYSTEMSIZE;
float Res = DEFAULTRESOLUTION;

/* VCCTL software version used to create input file */
float Version;

int Ntot = 0, Nperc = 0, Nburnt = 0;
FILE *Resfile;

struct BurnProps {
  int totvox;
  int x_vox_connected;
  int y_vox_connected;
  int z_vox_connected;
  int x_vox_percolated;
  int y_vox_percolated;
  int z_vox_percolated;
  int isPercInX;
  int isPercInY;
  int isPercInZ;
};

/* DFS stack structure for connectivity analysis */
typedef struct {
  int x, y, z;
} StackPoint;

int burn3d(int npix, struct BurnProps *burnprops);

int main(int argc, char *argv[]) {
  int ix, iy, iz, i;
  int valin, ovalin, phasein, garb;
  float voxelVolume = 1.0;
  char filein[MAXSTRING], fileout[MAXSTRING], instring[MAXSTRING];
  char phasename[MAXSTRING];
  char *locale;
  wchar_t mu = 0x03BC;
  wchar_t sup1 = 0x00B9;
  wchar_t sup2 = 0x00B2;
  wchar_t sup3 = 0x00B3;
  wchar_t supminus = 0x207B;
  struct BurnProps burnData;
  FILE *infile;

  /* Set up locale for printing unicode when necessary */
  locale = setlocale(LC_ALL, "");

  /* Check for command line arguments */
  if (argc != 3) {
    printf("Usage: %s <input_file> <output_file>\n", argv[0]);
    printf("\nEnter name of input image file: ");
    read_string(filein, sizeof(filein));
    printf("\n%s", filein);
    printf("\nEnter name of output file: ");
    read_string(fileout, sizeof(fileout));
    printf("\n%s", fileout);
    fflush(stdout);
  } else {
    /* Use command line arguments */
    strcpy(filein, argv[1]);
    strcpy(fileout, argv[2]);
    printf("Input file: %s \n", filein);
    printf("Output file: %s \n", fileout);
  }

  infile = filehandler("perc3d", filein, "READ");
  if (!infile) {
    exit(1);
  }

  if (read_imgheader(infile, &Version, &Xsyssize, &Ysyssize, &Zsyssize, &Res)) {
    fclose(infile);
    bailout("perc3d", "Error reading image header");
    exit(1);
  }

  voxelVolume = Res * Res * Res; /* in um3 */

  /***
   *	Allocate memory for Mic array
   ***/

  Mic = sibox(Xsyssize, Ysyssize, Zsyssize);
  if (!Mic) {
    fclose(infile);
    bailout("perc3d", "Could not allocate memory for Mic array");
    exit(1);
  }

  /**
   * 2025 August 05
   * New convention is to use C-ordering for reading and writing
   * microstructure image files (Z varies fastest, then Y, then X)
   **/
  for (ix = 0; ix < Xsyssize; ix++) {
    for (iy = 0; iy < Ysyssize; iy++) {
      for (iz = 0; iz < Zsyssize; iz++) {
        fscanf(infile, "%d", &ovalin);
        valin = convert_id(ovalin, Version);
        Mic[ix][iy][iz] = valin;
      }
    }
  }

  fclose(infile);

  Resfile = filehandler("perc3d", fileout, "WRITE");
  if (!Resfile) {
    fclose(infile);
    free_sibox(Mic, Xsyssize, Ysyssize);
    exit(1);
  }

  /* Write header to the results file */
  fprintf(Resfile, "MICROSTRUCTURE CONNECTIVITY ANALYSIS\n");
  fprintf(Resfile, "==============================");
  fprintf(Resfile, "==============================\n");
  fprintf(Resfile, "\nPERIODIC BOUNDARY CONDITIONS: Enabled");
  fprintf(
      Resfile,
      "\nDIRECTIONAL PERCOLATION: All three directions tested independently");
  fprintf(Resfile,
          "\n\nPercolation ratio: Fraction of phase in percolated structure");
  fprintf(Resfile, "\nHigher values indicate better connectivity of a phase");

  for (i = 0; i < NSPHASES; ++i) {
    garb = burn3d(i, &burnData);
    if (garb == MEMERR) {
      bailout("perc3d", "Could not allocate memory in burn3d function");
      exit(1);
    }
    if (burnData.totvox > 0) {
      id2phasename(i, phasename);
      fprintf(Resfile, "\n\n%s (Phase %d):", phasename, i);
      fwprintf(Resfile, L"\n Total volume: %.2f %lcm%lc  (%d voxels)",
               ((float)(burnData.totvox) * voxelVolume), mu, sup3,
               burnData.totvox);
      fwprintf(Resfile,
               L"\n Volume connected in X direction: %.2f %lcm%lc (%d voxels)",
               ((float)(burnData.x_vox_connected) * voxelVolume), mu, sup3,
               burnData.x_vox_connected);
      fwprintf(Resfile,
               L"\n Volume connected in Y direction: %.2f %lcm%lc (%d voxels)",
               ((float)(burnData.y_vox_connected) * voxelVolume), mu, sup3,
               burnData.y_vox_connected);
      fwprintf(Resfile,
               L"\n Volume connected in Z direction: %.2f %lcm%lc (%d voxels)",
               ((float)(burnData.z_vox_connected) * voxelVolume), mu, sup3,
               burnData.z_vox_connected);
      fwprintf(Resfile,
               L"\n Volume percolated in X direction: %.2f %lcm%lc (%d voxels)",
               ((float)(burnData.x_vox_percolated) * voxelVolume), mu, sup3,
               burnData.x_vox_percolated);
      fwprintf(Resfile,
               L"\n Volume percolated in Y direction: %.2f %lcm%lc (%d voxels)",
               ((float)(burnData.y_vox_percolated) * voxelVolume), mu, sup3,
               burnData.y_vox_percolated);
      fwprintf(Resfile,
               L"\n Volume percolated in Z direction: %.2f %lcm%lc (%d voxels)",
               ((float)(burnData.z_vox_percolated) * voxelVolume), mu, sup3,
               burnData.z_vox_percolated);
      fprintf(Resfile, "\n Percolation ratio, X direction: %.2f",
              ((float)(burnData.x_vox_percolated) / (float)(burnData.totvox)));
      fprintf(Resfile, "\n Percolation ratio, Y direction: %.2f",
              ((float)(burnData.y_vox_percolated) / (float)(burnData.totvox)));
      fprintf(Resfile, "\n Percolation ratio, Z direction: %.2f",
              ((float)(burnData.z_vox_percolated) / (float)(burnData.totvox)));
      fflush(Resfile);
    }
  }

  fclose(Resfile);

  free_sibox(Mic, Xsyssize, Ysyssize);

  return (0);
}

/***
 *	burn3d
 *
 * 	Assess the connectivity (percolation) of a single phase
 *
 * 	Two matrices are used:  one to store the recently burnt
 * 	locations, and one to store the newly-found burnt locations
 *
 * 	Arguments:	int npix: ID of phase to burn
 * 				int d1: x-direction flag
 * 				int d2: y-direction flag
 * 				int d3: z-direction flag
 *
 * 	Returns:	0 if no errors
 * 				MEMERR if a memory error is encountered
 *
 *	Calls:		No other routines
 *	Called by:	main function
 ***/

int burn3d(int npix, struct BurnProps *burnprops) {
  int i, j, k, j1, k1, dir;
  int d1, d2, d3, xsize, ysize, zsize;
  int inew, x1, y1, z1, igood, jnew, icur, status;
  int *nmatx, *nmaty, *nmatz, *nnewx, *nnewy, *nnewz;
  int mult1, mult2, npix1, npix2, npix3;
  int xl, xh, px, py, pz, qx, qy, qz, xcn, ycn, zcn;
  int ntop, nthrough, ncur, nnew, nphc;
  int npix_tot_count = 0;

  burnprops->totvox = 0;
  burnprops->x_vox_connected = 0;
  burnprops->y_vox_connected = 0;
  burnprops->z_vox_connected = 0;
  burnprops->isPercInX = 0;
  burnprops->isPercInY = 0;
  burnprops->isPercInZ = 0;

  npix1 = npix;
  npix2 = npix;
  npix3 = npix;
  if (npix == ETTR) {
    npix1 = ETTRC4AF;
  }
  if (npix == EMPTYP) {
    npix1 = POROSITY;
  }
  if (npix == TOTCSH) {
    npix2 = SLAGCSH;
    npix1 = POZZCSH;
    npix = CSH;
  }
  if (npix == TOTGYP) {
    npix3 = GYPSUMS;
    npix2 = ANHYDRITE;
    npix1 = HEMIHYD;
    npix = GYPSUM;
  }
  if (npix == C3A) {
    npix1 = OC3A;
    npix = C3A;
  }

  /**
   * Before starting analysis, find out how many
   * total voxels of this phase(s) are in the whole microstructure
   **/

  for (i = 0; i < Xsyssize; ++i) {
    for (j = 0; j < Ysyssize; ++j) {
      for (k = 0; k < Zsyssize; ++k) {
        if (Mic[i][j][k] == npix || Mic[i][j][k] == npix1 ||
            Mic[i][j][k] == npix2 || Mic[i][j][k] == npix3) {
          npix_tot_count++;
        }
      }
    }
  }

  burnprops->totvox = npix_tot_count;

  if (npix_tot_count == 0)
    return (0);

  /**
   * dir = 0 <--> x direction
   * dir = 1 <--> y direction
   * dir = 2 <--> z direction
   **/

  for (dir = 0; dir < 3; ++dir) {
    d1 = d2 = d3 = 0;
    if (dir == 0) {
      d1 = 1;
      xsize = Xsyssize;
      ysize = Ysyssize;
      zsize = Zsyssize;
    } else if (dir == 1) {
      d2 = 1;
      xsize = Ysyssize;
      ysize = Xsyssize;
      zsize = Zsyssize;
    } else {
      d3 = 1;
      xsize = Zsyssize;
      ysize = Ysyssize;
      zsize = Xsyssize;
    }
    /***
     *	Counters for number of pixels of phase accessible
     *	from surface #1 and number which are part of a
     *	percolated pathway to surface #2
     ***/

    ntop = status = nthrough = nphc = 0;

    /***
     *	Percolation is assessed from top to bottom only
     *	and burning algorithm is periodic in other two
     *	directions.
     *
     *	Use of directional flags allow transformation of
     *	coordinates to burn in direction of choosing
     *	(x, y, or z)
     ***/

    i = 0; /* Starting from the bottom x face */

    for (k = 0; k < zsize; k++) {
      for (j = 0; j < ysize; j++) {

        ncur = Ntot = 0;

        /* Transform coordinates */

        px = cx(i, j, k, d1, d2, d3);
        py = cy(i, j, k, d1, d2, d3);
        pz = cz(i, j, k, d1, d2, d3);

        if (Mic[px][py][pz] == npix || Mic[px][py][pz] == npix1 ||
            Mic[px][py][pz] == npix2 || Mic[px][py][pz] == npix3) {

          /* Start a burn front */

          Mic[px][py][pz] = BURNT;
          Ntot++;
          ncur++;

          /***
           * DEPTH-FIRST SEARCH (DFS) CONNECTIVITY ALGORITHM
           * Efficiently finds all connected voxels using minimal memory
           * Use a reasonable stack size to avoid memory exhaustion
           * Stack size of 10000 = ~120KB per component
           ***/

#define DFS_STACK_SIZE 10000
          StackPoint *dfs_stack =
              (StackPoint *)malloc(DFS_STACK_SIZE * sizeof(StackPoint));
          if (!dfs_stack) {
            fprintf(stderr, "Error: Could not allocate DFS stack (size=%d)\n", DFS_STACK_SIZE);
            return (MEMERR);
          }

          // Initialize DFS stack
          int stack_top = 0;
          dfs_stack[stack_top].x = i;
          dfs_stack[stack_top].y = j;
          dfs_stack[stack_top].z = k;
          stack_top++;

          // DFS main loop
          while (stack_top > 0) {
            stack_top--;
            int curr_x = dfs_stack[stack_top].x;
            int curr_y = dfs_stack[stack_top].y;
            int curr_z = dfs_stack[stack_top].z;

            // Check all 6 neighbors
            for (jnew = 1; jnew <= 6; jnew++) {
              x1 = curr_x;
              y1 = curr_y;
              z1 = curr_z;

              if (jnew == 1)
                x1--;
              if (jnew == 2)
                x1++;
              if (jnew == 3)
                y1--;
              if (jnew == 4)
                y1++;
              if (jnew == 5)
                z1--;
              if (jnew == 6)
                z1++;

              y1 += checkbc(y1, ysize);
              z1 += checkbc(z1, zsize);

              if ((x1 >= 0) && (x1 < xsize)) {
                px = cx(x1, y1, z1, d1, d2, d3);
                py = cy(x1, y1, z1, d1, d2, d3);
                pz = cz(x1, y1, z1, d1, d2, d3);

                if (px < 0 || px >= Xsyssize || py < 0 || py >= Ysyssize ||
                    pz < 0 || pz >= Zsyssize) {
                  continue;
                }

                if ((Mic[px][py][pz] == npix || Mic[px][py][pz] == npix1 ||
                     Mic[px][py][pz] == npix2 || Mic[px][py][pz] == npix3) &&
                    Mic[px][py][pz] != BURNT) {

                  Ntot++;
                  Mic[px][py][pz] = BURNT;

                  if (stack_top < DFS_STACK_SIZE - 1) {
                    dfs_stack[stack_top].x = x1;
                    dfs_stack[stack_top].y = y1;
                    dfs_stack[stack_top].z = z1;
                    stack_top++;
                  } else {
                    free(dfs_stack);
                    return (MEMERR);
                  }
                }
              }
            }
          }

          free(dfs_stack);

          /* Connected component found - add to total */
          ntop += Ntot;
        }
      }
    }

    /***
     * PERCOLATION ANALYSIS
     * Check if BURNT voxels span from one face to the opposite face
     * Uses original algorithm logic but optimized to run once per direction
     ***/

    xl = 0;
    xh = xsize - 1;

    // Mark voxels on boundary faces and check for percolation
    for (j1 = 0; j1 < ysize; j1++) {
      for (k1 = 0; k1 < zsize; k1++) {

        px = cx(xl, j1, k1, d1, d2, d3);
        py = cy(xl, j1, k1, d1, d2, d3);
        pz = cz(xl, j1, k1, d1, d2, d3);
        qx = cx(xh, j1, k1, d1, d2, d3);
        qy = cy(xh, j1, k1, d1, d2, d3);
        qz = cz(xh, j1, k1, d1, d2, d3);

        // Bounds check
        if (px >= 0 && px < Xsyssize && py >= 0 && py < Ysyssize && pz >= 0 &&
            pz < Zsyssize && qx >= 0 && qx < Xsyssize && qy >= 0 &&
            qy < Ysyssize && qz >= 0 && qz < Zsyssize) {

          // Check if both faces have BURNT voxels (indicates percolation path)
          if ((Mic[px][py][pz] == BURNT) && (Mic[qx][qy][qz] == BURNT)) {
            nthrough =
                ntop; // All connected voxels are part of percolating network
            break;
          }

          // Mark face voxels (increment BURNT values for later restoration)
          if (Mic[px][py][pz] == BURNT) {
            Mic[px][py][pz]++;
          }
          if (Mic[qx][qy][qz] == BURNT) {
            Mic[qx][qy][qz]++;
          }
        }
      }
      if (nthrough > 0)
        break;
    }

    /***
     *	Finished sampling all pixels of type npix along
     *	the bottom x face
     *
     *	Return the burnt sites to their original
     *	phase values
     ***/

    for (k = 0; k < zsize; k++) {
      for (j = 0; j < ysize; j++) {
        for (i = 0; i < xsize; i++) {

          /* Transform coordinates */
          px = cx(i, j, k, d1, d2, d3);
          py = cy(i, j, k, d1, d2, d3);
          pz = cz(i, j, k, d1, d2, d3);

          if (Mic[px][py][pz] >= BURNT) {

            nphc++;
            Mic[px][py][pz] = npix;

          } else if ((Mic[px][py][pz] == npix) || (Mic[px][py][pz] == npix1) ||
                     (Mic[px][py][pz] == npix2) || (Mic[px][py][pz] == npix3)) {
            nphc++;
          }
        }
      }
    }

    if (dir == 0) {
      burnprops->x_vox_connected = ntop;
      burnprops->x_vox_percolated = nthrough;
      if (nthrough > 0)
        burnprops->isPercInX = 1;
    } else if (dir == 1) {
      burnprops->y_vox_connected = ntop;
      burnprops->y_vox_percolated = nthrough;
      if (nthrough > 0)
        burnprops->isPercInY = 1;
    } else {
      burnprops->z_vox_connected = ntop;
      burnprops->z_vox_percolated = nthrough;
      if (nthrough > 0)
        burnprops->isPercInZ = 1;
    }

    /***
     * NOTE: No need to free BFS arrays since DFS algorithm doesn't use them.
     * Each connected component allocates and frees its own small DFS stack
     *locally.
     ***/

  } /* End of loop over different directions */

  return (status);
}
