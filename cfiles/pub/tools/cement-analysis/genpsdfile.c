/***************************************************
*	genpsdfile.c
*
*	Program to convert a tab-delimited, two-column
*	PSD data file into a .psd file that can be used
*	by the VCCTL.  In most instances, this will involve
*	nothing more than changing the column headers
****************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include "vcctl.h"

#define DIFF_FRAC	0
#define DIFF_PERCENT	1
#define CUM_FRAC		2
#define CUM_PERCENT		3

#define SMALLVAL 0.001

#define MAXNUM			500

int checkargs(int argc, char *argv[], float *maxdiam);
FILE *Fpin,*Fpout;

int main(int argc, char *argv[])
{
        int i,j;
		char sdiam[MAXSTRING],sfrac[MAXSTRING],ch;
		float diam[MAXNUM],frac[MAXNUM],t1;
        int numlines,psdtype;
        float maxval,sumval,maxdiam;

        maxdiam = 1.0e6;
        i = checkargs(argc,argv,&maxdiam);
        if (i == 1) {
           printf("\n\nUsage:\tgenpsdfile -i infile -o outfile [--max maxdiam] \n\n");
           exit(1);
        } else if (i > 0) {
           exit(1);
        }

        ch = 'A';
        while (ch != '\n') {
           fscanf(Fpin,"%c",&ch);
        }

        fprintf(Fpout,"Diam_(um)\tWt._frac.");
		i = 0;
        while (!feof(Fpin)) {
           fscanf(Fpin,"%s %s",sdiam,sfrac);
           if (!feof(Fpin)) {
               if (i >= MAXNUM) {
                   printf("\n\nERROR:\tToo many size classes.  Change\n");
                   printf("\tvariable MAXNUM to a greater number ");
                   printf("and recompile.");
                   printf("\n\tExiting now.\n\n");
                   exit(1);
               }
               if (atof(sdiam) < maxdiam) {
                   diam[i] = atof(sdiam);
                   frac[i] = atof(sfrac);
                   if (frac[i] - 100.0000 > 0.001) {
                       printf("\n\nERROR:\tMaximum PSD value exceeds\n");
                       printf("\t100, which is impossible. ");
                       printf("\n\tExiting now.\n\n");
                       exit(1);
                   }
                   i++;
               }
            }
         }

         numlines = i;

         /***
         *   Perform bubble sort in ascending order of
         *   particle diameters
         ***/

         for (i = 0; i < numlines - 1; i++) {
            for (j = (i+1); j < numlines; j++) {
               if (diam[i] > diam[j]) {
                  t1 = diam[i];
                  diam[i] = diam[j];
                  diam[j] = t1;
                  t1 = frac[i];
                  frac[i] = frac[j];
                  frac[j] = t1;
               }
             }
          }

          /*** Bubble sort is finished. ***/
          /*** Determine whether cumulative or differential data input ***/

         maxval = 0.0;
         sumval = 0.0;
         for (i = 0; i < numlines; i++) {
            if (maxval < frac[i]) maxval = frac[i];
            sumval += frac[i];
         }
 
         if ((maxval > 1.5) && (fabs(maxval-frac[numlines - 1]) < SMALLVAL)) {
             psdtype = CUM_PERCENT;
             printf("\nPSD Type is detected to be CUM_PERCENT\n");
         } else if ((maxval > 1.5 && (fabs(maxval-frac[numlines-1])) > SMALLVAL)) {
             psdtype = DIFF_PERCENT;
             printf("\nPSD Type is detected to be DIFF_PERCENT\n");
         } else if (fabs(maxval-frac[numlines-1]) < SMALLVAL) {
             psdtype = CUM_FRAC;
             printf("\nPSD Type is detected to be CUM_FRAC\n");
         } else {
             psdtype = DIFF_FRAC;
             printf("\nPSD Type is detected to be DIFF_FRAC\n");
         }

         /*** Convert values based on type of input ***/

         for (i = numlines-1; i >= 0; i--) {
             if (psdtype == CUM_PERCENT || psdtype == CUM_FRAC) {
		         if (i == 0) {
                   	frac[i] = (frac[i]) / maxval;
				 } else {
                   	frac[i] = (frac[i] - frac[i-1]) / maxval;
				 }
             } else {
                 frac[i] /= sumval;
             }
          }
		
          /***Now print differential PSD ***/


          if (diam[0] > 0.25) {
              fprintf(Fpout,"\n0.100\t0.00000");
          }
          for (i = 0; i < numlines; i++) {
              fprintf(Fpout,"\n%.3f\t%.6f",diam[i],frac[i]);
          }

          fclose(Fpin);
          fclose(Fpout);
          exit(0);
}

int checkargs(int argc, char *argv[], float *maxdiam)
{
       int i,status=0;
       int inindex,outindex,maxindex;

       inindex = outindex = maxindex = 0;
       i = 1;
       while (i < argc) {
           if ((!strcmp(argv[i],"-i")) || (!strcmp(argv[i],"-I"))) {
                   inindex = i + 1;
                   if (inindex >= argc) {
                      status = 1;
                      return status;
                   }
           } else if ((!strcmp(argv[i],"-o"))
                 || (!strcmp(argv[i],"-O"))) {
                   outindex = i + 1;
                   if (outindex >= argc) {
                      status = 1;
                      return status;
                   }
           } else if ((!strcmp(argv[i],"--max"))
                 || (!strcmp(argv[i],"-m"))) {
                   maxindex = i + 1;
                   if (maxindex >= argc) {
                      status = 1;
                      return status;
                   }
                   *maxdiam = atof(argv[maxindex]);
           }

           i++;
       }

       /* inindex is the index of the input file name, etc. */
                
       if (inindex == 0 || outindex == 0) {
           status = 1;
           return status;
       }

       if ((Fpin = fopen(argv[inindex],"r")) == NULL) {
             printf("\n\nERROR: Could not open file %s\n\n",argv[inindex]);
             status = 2;
             return status;
       }

       if ((Fpout = fopen(argv[outindex],"w")) == NULL) {
              printf("\n\nERROR: Could not open file %s\n\n",argv[outindex]);
              status = 2;
              return status;
       }

       return status;
}
