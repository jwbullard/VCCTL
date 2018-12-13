/***********************************************************
 * Program convertImageJ takes the ASCII text output from
 * an ImageJ image and converts it to two different files:
 *
 *     (1) A color pnm file (P3) -- for viewing
 *     (2) A raw binary img file -- for correlation functions
 *
***********************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "vcctl.h" 

#define IC3S 1
#define IC2S 2
#define IC3A 3
#define IC4AF 4
#define IMGCA 5
#define IK2SO4 6
#define IGYP 7
#define IPORE 8
#define INA2SO4 9
#define ILIME 10
#define ICACO3 11
#define IKAOLIN 12
#define ISILICA 13

#define MAXDIM 3000

int main(int argc, char *argv[])
{
    register int i,j;
    int inid,outid,inputphases;
    int red[NPHASES],green[NPHASES],blue[NPHASES];
    int mic[MAXDIM][MAXDIM];
    long int xsize, ysize,numpix;
    char FileP2[MAXSTRING],FileP3[MAXSTRING],buff[MAXSTRING],ch;
    FILE *fpin,*fpp2,*fpp3;

    cemcolors(red,green,blue,0);

    xsize = ysize = 0;

    if (argc != 2) {
        printf("\n\nUsage: convertImageJ filename\n\n");
        exit(1);
    }

    if ((fpin = fopen(argv[1],"r")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",argv[1]);
        exit(1);
    }

    /* Count the tabs to find out how many columns */
    /* Count the newlines to find out how many rows */

    numpix = 1;
    ysize = 0;
    while (!feof(fpin)) {
        fscanf(fpin,"%c",&ch);
        if (!feof(fpin)) {
            if (ch == '\n') {
                if (ysize == 0) xsize = numpix;
                ysize++;
            } else if ((ch == '\t') && (ysize == 0)) {
                numpix++;
            }
        }
    }

    fclose(fpin);
    if (xsize >= MAXDIM || ysize >= MAXDIM) {
        printf("\n\nImage is too big.  Change MAXDIM and recompile this program.\n\n");
        exit(1);
    }

    printf("\n\n Image format OK.  X size = %ld, Y size = %ld\n",xsize,ysize);
    fflush(stdout);

    if ((fpin = fopen(argv[1],"r")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",argv[1]);
        exit(1);
    }

    sprintf(FileP2,"%s.img",argv[1]);
    sprintf(FileP3,"%s.pnm",argv[1]);

    if ((fpp2 = fopen(FileP2,"w")) == NULL) {
        printf("\n\nERROR: File %s could not be created\n\n",FileP2);
        exit(1);
    }
    if ((fpp3 = fopen(FileP3,"w")) == NULL) {
        printf("\n\nERROR: File %s could not be created\n\n",FileP3);
        exit(1);
    }

    fprintf(fpp3,"P3\n");
    fprintf(fpp3,"%d %d\n",(int)xsize,(int)ysize);
    fprintf(fpp3,"255\n");

    for (j = 0; j < ysize; j++) {
        for (i = 0; i < xsize; i++) {
            fscanf(fpin,"%s",buff);
            inid = atoi(buff);
            mic[i][j] = inid;
            switch (inid) {
                case IPORE:
                    outid = (int)POROSITY;
                    break;
                case IC3S:
                    outid = (int)C3S;
                    break;
                case IC2S:
                    outid = (int)C2S;
                    break;
                case IC3A:
                    outid = (int)C3A;
                    break;
                case IC4AF:
                    outid = (int)C4AF;
                    break;
                case IMGCA:
                    outid = (int)INERT;
                    break;
                case IK2SO4:
                    outid = (int)K2SO4;
                    break;
                case ILIME:
                    outid = (int)FREELIME;
                    break;
                case IGYP:
                    outid = (int)GYPSUM;
                    break;
                    /*
                case MISC1:
                    outid = (int)POROSITY;
                    break;
                case MISC2:
                    outid = (int)POROSITY;
                    break;
                case MISC3:
                    outid = (int)POROSITY;
                    break;
                case IQUARTZ:
                    outid = (int)SILICA;
                    break;
                case ICASI:
                    outid = (int)C3S;
                    break;
                    */
                default:
                    outid = (int)POROSITY;
                    break;
            }
            fprintf(fpp3,"%d %d %d\n",red[outid],green[outid],blue[outid]);
            fprintf(fpp2,"%c",(char)(outid));
        }
    }

    fclose(fpin);
    fclose(fpp2);
    fclose(fpp3);
    exit(0);
}
