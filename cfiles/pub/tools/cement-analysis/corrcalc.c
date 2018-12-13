/************************************************************************/
/*                                                                      */
/*      Program: corrcalc.c                                             */
/*      Purpose: To compute the 2-D correlation function in S(x,y) form */
/*              for one or more phases of a cement particle image       */
/*      Programmer: Dale P. Bentz                                       */
/*                  NIST                                                */
/*                  100 Bureau Drive Stop 8621                          */
/*                  Building 226 Room B-350                             */
/*                  Gaithersburg, MD  20899-8621                        */
/*                  Phone: (301) 975-5865                               */
/*                  Fax: (301) 990-6891                                 */
/*                  E-mail: dale.bentz@nist.gov	                        */
/*                                                                      */
/************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "vcctl.h"

#define CSIZE 200   /* Extent of correlation computation in pixels */
#define ISIZE 1100  /* Limit on image size */

int flag[5];

/* Note that maximum image size is ISIZE*ISIZE */
int main()
{
        int mask,i,j,image[ISIZE][ISIZE],xsize,ysize;
        int scalef,xoff,yoff,inval,iscale,jscale;
        long int sum,ntot;
        double fsum;
        char chin,filen[MAXSTRING],fileo[MAXSTRING],buff[MAXSTRING];
        FILE *infile,*outfile;

        do{
                printf("\nEnter size of image in x direction: ");
                read_string(buff,sizeof(buff));
                xsize = atoi(buff);
                printf("\nEnter size of image in y direction: ");
                read_string(buff,sizeof(buff));
                ysize = atoi(buff);
                printf("\n%d %d \n",xsize,ysize);
        } while ((xsize>ISIZE)||(ysize>ISIZE));

/* Assumed file format is a simple list of integers (one per line) */
/* representing phases as indicated below and with y in the inner loop */
        printf("Enter name of image file \n");
        read_string(filen,sizeof(filen));
        infile=fopen(filen,"r");

        printf("Enter name of correlation file to create\n");
        read_string(fileo,sizeof(fileo));
        outfile=fopen(fileo,"w");
/* Output header consisting of the extent of the correlation matrix */
        fprintf(outfile,"%d %d\n",CSIZE+1,CSIZE+1);

/* If original image is acquired at a resolution much less than */
/* 1 um/pixel, scaling factor can be used to for example skip every other */
/* pixel to adjust to appropriate resolution */
        scalef=1;
        printf("Enter scaling factor to use (default=%d) \n",scalef);
        printf("If image is acquired at 250X, scale factor is 1. \n");
        printf("If image is acquired at 500X, scale factor is 2. \n");
        printf("If image is acquired at 750X, scale factor is 3. \n");
        printf("If image is acquired at 1000X, scale factor is 4. \n");
        read_string(buff,sizeof(buff));
        scalef = atoi(buff);
        printf("%d \n",scalef);

        printf("Phase assignments are assumed to be as follows: \n\n");
        printf("Phase      Image ID   Mask value \n");
        printf(" \n");
        printf("Pores, etc.    0          1\n");
        printf("C3S            1          2\n");
        printf("C2S            2          4\n");
        printf("C3A            3          8\n");
        printf("C4AF           4         16\n");
        printf("K2SO4          5         32\n");
        printf("Na2SO4         6         64\n");

/* Composite mask is a simple logical and of the above values */
/* Example: For C3S+C2S, mask would be 2&4 = 6 */
        printf("Enter composite value for mask to employ during this run \n");
	printf("Example- for C3S+C2S together, composite value would be 2+4=6 \n");
        read_string(buff,sizeof(buff));
        mask = atoi(buff);
        printf("%d\n",mask);

/* Read in the original image and convert values to 2**i format */
/* so that simple and operations may be employed to compute correlation */
        for(i=0;i<xsize;i++){
        for(j=0;j<ysize;j++){
                fscanf(infile,"%c",&chin);
		inval=(int)chin;
                image [i] [j]=(int)(pow(2.,(float)inval));
        }
        }

        fclose(infile);
        printf("Finished reading in file \n");
        fflush(stdout);

/* Now perform calculation */
/* Correlation is computed only over a distance of CSIZE pixels */
        for(i=0;i<=CSIZE;i++){
        for(j=0;j<=CSIZE;j++){
                sum=0;
                ntot=0;

/* iscale and jscale represent limits of correlation calculation since */
/* original image is assumed to be non-periodic */
                iscale=i*scalef;
                jscale=j*scalef;
/* Be sure to skip to every scalef pixel to adjust resolution */
                for(xoff=0;xoff<(xsize-iscale);xoff+=scalef){
                for(yoff=0;yoff<(ysize-jscale);yoff+=scalef){
                        ntot+=1;
/* Increment counter if both pixels contain one of the necessary phases */
                if(((mask&(image[xoff][yoff]))!=0)&&
                       ((mask&(image[xoff+iscale][yoff+jscale]))!=0)){
                       sum+=1;
                }
		
                }
                }
/* Determine and output value for S(x,y) */
        fsum=(double)sum/(double)ntot;
        fprintf(outfile,"%d %d %lf \n",i,j,fsum);
        fflush(outfile);

        }
        }

        fclose(outfile);
        exit(0);
}
