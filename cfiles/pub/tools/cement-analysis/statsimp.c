/************************************************************************/
/*                                                                      */
/*      Program: statsimp.c                                             */
/*      Purpose: To compute the area and surface areas                  */
/*              for one or more phases of a cement particle image       */
/*      Programmer: Dale P. Bentz                                       */
/*		    NIST                                                */
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
#include <string.h>
#include <math.h>
#include "vcctl.h"

#define ISIZE 1024

int flag[5];

/* Note that program is limited to a ISIZE*ISIZE image size */
int main(void)
{
        int mask,i,j,image[ISIZE][ISIZE],xsize,ysize;
        int inval;
        long int sum,edgesum,czero=0;
        float fsum;
        char filen[MAXSTRING],buff[MAXSTRING],chin;
        FILE *infile;

        ysize = xsize = ISIZE - 1;
       do{
                printf("\nEnter size of image in x direction: ");
                read_string(buff,sizeof(buff));
                xsize = atoi(buff);
                printf("\nEnter size of image in y direction: ");
                read_string(buff,sizeof(buff));
                xsize = atoi(buff);
                printf("\n%d %d \n",xsize,ysize);
       } while ((xsize>ISIZE)||(ysize>ISIZE));

        printf("\nEnter name of image file: ");
        read_string(filen,sizeof(filen));

        infile=fopen(filen,"r");

        mask=1;
        /* Read in the image and assign powers of two as phase values */
        /* To enable tabulation of multiple phases simultaneously if needed */
        for(i=0;i<xsize;i++){
        for(j=0;j<ysize;j++){
                fscanf(infile,"%c",&chin);
		inval=(int)chin;
                if(inval==0){
			czero+=1;
		}
                image [i] [j]=(int)(pow(2.,(float)inval));
        }
        }
        fclose(infile);
        printf("Zero count is %ld Non-zero is %ld \n",czero,ysize*xsize-czero);

/* Now perform calculation */
/* Allow user to execute counting as many times as desired */
        while(mask!=0){
                printf("Phase assignments are assumed to be as follows: \n\n");
                printf("Phase      Image ID   Mask value \n \n");
                printf("Pores          0          1\n");
                printf("C3S            1          2\n");
                printf("C2S            2          4\n");
                printf("C3A            3          8\n");
                printf("C4AF           4         16\n");

            printf("Enter composite value for mask to use during this run \n");
            printf("Example: for C3S and C2S together, composite would be 2+4=6 \n");
                printf("Enter 0 to exit program \n");
                read_string(buff,sizeof(buff));
                mask = atoi(buff);
                printf("%d\n",mask);

                /* Determine area and perimeter counts for this phase(s) */
                /* Perimeter count is number of pixel edges of phase(s) */
                /* in contact with porosity */
                /* Image is non-periodic so ignore a one-pixel layer around the edge */
                if(mask!=0){
                sum=edgesum=0;
                for(i=1;i<(xsize-1);i++){
                for(j=1;j<(ysize-1);j++){

                if((mask&(image[i][j]))!=0){
                        sum+=1;
                        /* Check immediate 4 neighbors for edges */
                        if(((image[i-1][j]))==1){
                                edgesum+=1;
                        }
                        if(((image[i+1][j]))==1){
                                edgesum+=1;
                        }
                        if(((image[i][j-1]))==1){
                                edgesum+=1;
                        }
                        if(((image[i][j+1]))==1){
                                edgesum+=1;
                        }
                }

                }
                }

                printf("Area- %ld pixels Perimeter- %ld \n",sum,edgesum);
                fsum=(float)sum/((float)(xsize-2)*(float)(ysize-2));
                printf("Phase fraction is %f \n",fsum);
                }
        } /* end of while mask loop */
        exit(0);
}
