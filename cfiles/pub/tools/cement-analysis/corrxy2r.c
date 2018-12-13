/************************************************************************/
/*                                                                      */
/*      Program: corrxy2r.c                                             */
/*      Purpose: To convert the 2-D correlation function from S(x,y)    */
/*              form to S(r) form for use in 3-D reconstructions        */
/*      Programmer: Dale P. Bentz                                       */
/*                  NIST                                                */
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

#define PIVAL 3.1415926

/* Reference for S(x,y)---> S(r) conversion */
/* Berryman, J.G., "Measurement of Spatial Correlation Functions */
/* Using Image Processing Techniques," J. Appl. Phys., 57 (7), 2374-2384,*/
/* 1985 */

int main (void)
{
        FILE *infile,*outfile;
        int nx,ny,i,j,x,y,r,l,xm,ym;
        float sorg [306] [306],ssum,snew,z,theta;
        float xt,yt,s1,s2,st,xr;
        char fname[MAXSTRING],wname[MAXSTRING];

        printf("Enter filename containing raw [S(x,y)] data \n");
        read_string(fname,sizeof(fname));

        infile=fopen(fname,"r");

/* Read in extent of original S(x,y) calculation, usually 60x60 */
        fscanf(infile,"%d %d\n",&nx,&ny);

/* Read in all of the S(x,y) values */
        for(i=0;i<nx;i++){
        for(j=0;j<ny;j++){
                fscanf(infile,"%d %d %f \n",&x,&y,&z);
                sorg [x] [y]=z;
        }
        }

        fclose(infile);

        printf("Enter filename to write results to \n");
        read_string(wname,sizeof(wname));

/* Open output file and write out correlation extent as first value */
        outfile=fopen(wname,"w");
        fprintf(outfile,"%d\n",nx-1);

/* Now convert S(x,y) to S(r) format */
        for(r=0;r<(ny-1);r++){

                ssum=0.0;
                xr=(float)r;
		
                for(l=0;l<=(2*r);l++){
		
                        if(xr==0){theta=0;}
                        else{theta=PIVAL*(float)l/(4.*xr);}
                        xt=xr*cos(theta);
                        yt=xr*sin(theta);
                        xm=(int)xt;
                        ym=(int)yt;

	/* Use bilinear interpolation */
    s1=(sorg [xm] [ym])-(sorg [xm] [ym] - sorg [xm+1] [ym])*(xt-(float)xm);
    s2=(sorg [xm] [ym+1])-(sorg [xm] [ym+1] -sorg [xm+1] [ym+1])*(xt-(float)xm);

                        st=s1-(s1-s2)*(yt-(float)ym);
                        ssum+=st;
                }

                snew=ssum/(2.*(float)r+1.);
                printf("%d %f \n",r,snew);
                fprintf(outfile,"%d %f\n",r,snew);

        }
        fclose(outfile);
        exit(0);
}
