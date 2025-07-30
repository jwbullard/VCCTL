#include "include/vcctl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int Xsize, Ysize, Zsize;
int Xsizeorig, Ysizeorig, Zsizeorig;
float Version, Res;

int ***Mic;

int main(int argc, char *argv[]) {
  register int i, j, k;
  int ival, val;
  char buff[128], filename[128];
  FILE *fpin, *fpout;

  if (argc != 2) {
    printf("\n\nUSAGE:  thames2vcctl [image file name]\n\n");
    return (0);
  }

  fpin = filehandler("thames2vcctl", argv[1], "READ");

  /* Read in the thames microstructure image header */
  if (read_imgheader(fpin, &Version, &Xsize, &Ysize, &Zsize, &Res)) {
    fclose(fpin);
    bailout("vcctl2thames", "Error reading image header");
    return (1);
  }

  Mic = ibox(Xsize, Ysize, Zsize);

  sprintf(filename, "%s.vcctl.img", argv[1]);

  if ((fpout = fopen(filename, "w")) == NULL) {
    printf("\nERROR:  Could not open file %s. Exiting.\n\n", filename);
    free_ibox(Mic, Xsize, Ysize);
    exit(1);
  }

  fprintf(fpout, "Version: 5.0\n");
  fprintf(fpout, "X_Size: %d\n", Xsize);
  fprintf(fpout, "Y_Size: %d\n", Ysize);
  fprintf(fpout, "Z_Size: %d\n", Zsize);
  fprintf(fpout, "Image_Resolution: 1.0\n");

  /* Read in the thames microstructure image */

  for (k = 0; k < Zsize; k++) {
    for (j = 0; j < Ysize; j++) {
      for (i = 0; i < Xsize; i++) {
        fscanf(fpin, "%s", buff);
        ival = atoi(buff);
        switch (ival) {
        case 0:
          val = EMPTYP;
          break;
        case 1:
          val = POROSITY;
          break;
        case 2:
          val = C3S;
          break;
        case 3:
          val = C2S;
          break;
        case 4:
          val = C3A;
          break;
        case 5:
          val = C4AF;
          break;
        case 6:
          val = K2SO4;
          break;
        case 7:
          val = NA2SO4;
          break;
        case 8:
          val = GYPSUM;
          break;
        case 9:
          val = HEMIHYD;
          break;
        case 10:
          val = CACO3;
          break;
        case 11:
          val = CH;
          break;
        case 12:
          val = CSH;
          break;
        case 13:
          val = AFMC;
          break;
        case 14:
          val = AFM;
          break;
        case 15:
          val = ETTR;
          break;
        case 16:
          val = BRUCITE;
          break;
        case 17:
          val = C3AH6;
          break;
        case 18:
          val = AFM;
          break;
        case 19:
          val = FREELIME;
          break;
        case 20:
          val = FREELIME;
          break;
        default:
          val = POROSITY;
          break;
        }
        Mic[i][j][k] = val;
      }
    }
  }

  fclose(fpin);

  /* Now write the rest of the vcctl image file */

  for (k = 0; k < Zsize; k++) {
    for (j = 0; j < Ysize; j++) {
      for (i = 0; i < Xsize; i++) {
        fprintf(fpout, "%d\n", Mic[i][j][k]);
      }
    }
  }

  fclose(fpout);
  free_ibox(Mic, Xsize, Ysize);
  exit(0);
}
