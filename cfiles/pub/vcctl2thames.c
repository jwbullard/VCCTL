#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include "./vcctl.h"

int Xsize,Ysize,Zsize;
int Xsizeorig,Ysizeorig,Zsizeorig;
float Version,Res;

int ***Mic;

int main(int argc, char *argv[])
{
    register int i,j,k;
    int ival,val;
    char buff[128],filename[128];
    FILE *fpin,*fpout;

    if (argc != 2) {
       printf("\n\nUSAGE:  vcctl2thames [image file name]\n\n");
       return(0);
    }

    fpin = filehandler("vcctl2thames",argv[1],"READ");

    /* Read in the vcctl microstructure image header */
    if (read_imgheader(fpin,&Version,&Xsize,&Ysize,&Zsize,&Res)) {
        fclose(fpin);
        bailout("vcctl2thames","Error reading image header");
        return(1);
    }

    Mic = ibox(Xsize,Ysize,Zsize);

    sprintf(filename,"%s.init",argv[1]);

    if ((fpout = fopen(filename,"w")) == NULL) {
        printf("\nERROR:  Could not open file %s. Exiting.\n\n",filename);
        free_ibox(Mic,Xsize,Ysize);
        exit(1);
    }

    fprintf(fpout,"Version: 5.0\n");
    fprintf(fpout,"X_Size: %d\n",Xsize);
    fprintf(fpout,"Y_Size: %d\n",Ysize);
    fprintf(fpout,"Z_Size: %d\n",Zsize);
    fprintf(fpout,"Image_Resolution: 1.0\n");

    /* Read in the vcctl microstructure image */

    for (k = 0; k < Zsize; k++) {
        for (j = 0; j < Ysize; j++) {
            for (i = 0; i < Xsize; i++) {
                fscanf(fpin,"%s",buff);
                ival = atoi(buff);
                switch (ival) {
                    case POROSITY:
                        val = 1;
                        break;
                    case C3S:
                        val = 2;
                        break;
                    case C2S:
                        val = 3;
                        break;
                    case C3A:
                        val = 4;
                        break;
                    case C4AF:
                        val = 5;
                        break;
                    case CAS2:
                        val = 6;
                        break;
                    case K2SO4:
                        val = 7;
                        break;
                    case NA2SO4:
                        val = 8;
                        break;
                    case GYPSUM:
                        val = 9;
                        break;
                    case HEMIHYD:
                        val = 10;
                        break;
                    case ANHYDRITE:
                        val = 10;
                        break;
                    case CACO3:
                        val = 11;
                        break;
                    case CH:
                        val = 12;
                        break;
                    case CSH:
                        val = 13;
                        break;
                    case AFMC:
                        val = 14;
                        break;
                    case AFM:
                        val = 15;
                        break;
                    case ETTR:
                        val = 16;
                        break;
                    case BRUCITE:
                        val = 17;
                        break;
                    case FREELIME:
                        val = 18;
                        break;
                    default:
                        val = 0;
                        break;
                }
                Mic[i][j][k] = val;
            }
        }
    }

    fclose(fpin);

    /* Now write the rest of the thames image file */

    for (k = 0; k < Zsize; k++) {
        for (j = 0; j < Ysize; j++) {
            for (i = 0; i < Xsize; i++) {
                fprintf(fpout,"%d\n",Mic[i][j][k]);
            }
        }
    }

    fclose(fpout);
    free_ibox(Mic,Xsize,Ysize);
    exit(0);
}
