/************************************************************************/
/*                                                                      */
/*      Program: rgbimage.c                                          */
/*      Purpose: To produce an RGB color raster image                   */
/*				 from three pnm files (one per channel					*/
/*              (Ca=red, Si=green, and Al=blue for example)             */
/*      Programmer: Dale P. Bentz                                       */
/*		    NIST               			                                */
/*                  100 Bureau Drive Stop 8621                          */
/*                  Building 226 Room B-350                             */
/*                  Gaithersburg, MD  20899-8621                        */
/*                  Phone: (301) 975-5865                               */
/*                  Fax: (301) 990-6891                                 */
/*                  E-mail: dale.bentz@nist.gov                         */
/*                                                                      */
/************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include "vcctl.h"

#define PNM 0
#define RAS 1

int main(void) {
	FILE *infile1,*infile2,*infile3,*outfile;
	char filein1[MAXSTRING],filein2[MAXSTRING],filein3[MAXSTRING],fileout[MAXSTRING];
	char buff[MAXSTRING],Filext[5];
	unsigned char valin;
	int vred,vgreen,vblue,maxval,extype;
	int i,nskip,dx,dy,j,scf;
	int ix,iy;

    do {
	    printf("Enter type of graphics file (pnm,ppm,ras): ");
        read_string(Filext,sizeof(Filext));
	    printf("\n%s\n",Filext);
    } while (strcmp(Filext,"pnm") && strcmp(Filext,"ppm") && strcmp(Filext,"ras"));

    if (!strcmp(Filext,"ras")) {
        extype = RAS;
    } else {
        extype = PNM;
    }

	printf("Enter root name of file with red data: ");
	read_string(filein1,sizeof(filein1));
	printf("\n%s\n",filein1);
    strcat(filein1,".");
    strcat(filein1,Filext);
	printf("Enter root name of file with green data: ");
	read_string(filein2,sizeof(filein2));
	printf("\n%s\n",filein2);
    strcat(filein2,".");
    strcat(filein2,Filext);
	printf("Enter root name of file with blue data: ");
	read_string(filein3,sizeof(filein3));
	printf("\n%s\n",filein3);
    strcat(filein3,".");
    strcat(filein3,Filext);
	printf("Enter root name of PNM output file to create: ");
	read_string(fileout,sizeof(fileout));
	printf("\n%s\n",fileout);
    strcat(fileout,".pnm");

    nskip = 0;
    if (extype == RAS) {
        printf("Enter number of pixels to skip at start);, x dimension, and y dimension: ");
        read_string(buff,sizeof(buff));
        nskip = atoi(buff);
        printf("Enter x dimension, and y dimension: ");
        read_string(buff,sizeof(buff));
        dx = atoi(buff);
        printf("Enter y dimension, and y dimension: ");
        read_string(buff,sizeof(buff));
        dy = atoi(buff);
        printf("\n%d %d %d \n",nskip,dx,dy);
    }

	printf("Enter scale factor to scale greylevels by \n");
    read_string(buff,sizeof(buff));
    scf = atoi(buff);
	printf("%d\n",scf);

	infile1=fopen(filein1,"rb");
	infile2=fopen(filein2,"rb");
	infile3=fopen(filein3,"rb");

    switch (extype) {
        case PNM:
	        fscanf(infile1,"%s",buff);
	        fscanf(infile2,"%s",buff);
	        fscanf(infile3,"%s",buff);
	        fscanf(infile1,"%d %d",&dx,&dy);
	        fscanf(infile2,"%d %d",&ix,&iy);
	        if (ix != dx || iy != dy) {
		        printf("\nERROR: Image size mismatch.  Exiting\n\n");
		        exit(1);
	        }
	        fscanf(infile3,"%d %d",&ix,&iy);
	        if (ix != dx || iy != dy) {
		        printf("\nERROR: Image size mismatch.  Exiting\n\n");
		        exit(1);
	        }
	        fscanf(infile1,"%d",&maxval);
	        fscanf(infile2,"%d",&maxval);
	        fscanf(infile3,"%d",&maxval);
            break;
        case RAS:
            for(i=0;i<nskip;i++){
		        fscanf(infile1,"%c",&valin);
		        fscanf(infile2,"%c",&valin);
		        fscanf(infile3,"%c",&valin);
            }
            break;
        default:
            break;
	}

	printf("\nPreparing to open output file.\n");
	outfile=fopen(fileout,"w");

	fprintf(outfile,"P3\n");
	fprintf(outfile,"%d %d\n",dx,dy);
	fprintf(outfile,"255\n");

	for(j=0;j<dy;j++){
	for(i=0;i<dx;i++){

		fscanf(infile1,"%c",&valin);
		vred=scf*(int)valin;
		if(vred>255){vred=255;}
		fscanf(infile2,"%c",&valin);
		vgreen=scf*(int)valin;
		if(vgreen>255){vgreen=255;}
		fscanf(infile3,"%c",&valin);
		vblue=scf*(int)valin;
		if(vblue>255){vblue=255;}
		fprintf(outfile,"%d %d %d\n",vred,vgreen,vblue);
	}
	}

	fclose(infile1);
	fclose(infile2);
	fclose(infile3);
	fclose(outfile);
    exit(0);
}
