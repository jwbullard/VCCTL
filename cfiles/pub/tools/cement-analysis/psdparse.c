/**********
*
* 	psdparse.c
*
* 	Program to take an experimentally determined particle
* 	size distribution and convert it into a form that can
* 	be used by the VCCTL software
*
* 	Operates on cumulative PSD data
*
* 	Jeffrey W. Bullard --- June 2002
*
***********/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ctype.h>
#include "vcctl.h"

#define NUMBINS		21
#define MAXNUM		200

int main(void) {

	int another=1,i,j,jlow,jhi,number_entries,done;
	float pdiam[NUMBINS][2],t1,t2;
	float diam[MAXNUM],frac[MAXNUM],totfrac,slope,intercept;
	char decid,infile[MAXSTRING],outfile[MAXSTRING];
	FILE *fpin,*fpout;

	pdiam[0][0] = 1.0;
	pdiam[1][0] = 3.0;
	pdiam[2][0] = 5.0;
	pdiam[3][0] = 7.0;
	pdiam[4][0] = 9.0;
	pdiam[5][0] = 11.0;
	pdiam[6][0] = 13.0;
	pdiam[7][0] = 15.0;
	pdiam[8][0] = 17.0;
	pdiam[9][0] = 19.0;
	pdiam[10][0] = 21.0;
	pdiam[11][0] = 23.0;
	pdiam[12][0] = 25.0;
	pdiam[13][0] = 27.0;
	pdiam[14][0] = 29.0;
	pdiam[15][0] = 31.0;
	pdiam[16][0] = 35.0;
	pdiam[17][0] = 41.0;
	pdiam[18][0] = 47.0;
	pdiam[19][0] = 61.0;
	pdiam[20][0] = 73.0;
	pdiam[0][1] = 0.0;
	pdiam[1][1] = 0.0;
	pdiam[2][1] = 0.0;
	pdiam[3][1] = 0.0;
	pdiam[4][1] = 0.0;
	pdiam[5][1] = 0.0;
	pdiam[6][1] = 0.0;
	pdiam[7][1] = 0.0;
	pdiam[8][1] = 0.0;
	pdiam[9][1] = 0.0;
	pdiam[10][1] = 0.0;
	pdiam[11][1] = 0.0;
	pdiam[12][1] = 0.0;
	pdiam[13][1] = 0.0;
	pdiam[14][1] = 0.0;
	pdiam[15][1] = 0.0;
	pdiam[16][1] = 0.0;
	pdiam[17][1] = 0.0;
	pdiam[18][1] = 0.0;
	pdiam[19][1] = 0.0;
	pdiam[20][1] = 0.0;

	i = 0;

	printf("\n\n");
	printf("\nEnter file name to read:  ");
	read_string(infile,sizeof(infile));
	if ((fpin = fopen(infile,"r")) == NULL) {
		printf("\n\nERROR:  Could not open file %s for reading\n",infile);
		exit(1);
	}
	
	j = 0;
	while (!feof(fpin) && j < MAXNUM) {
		fscanf(fpin,"%f %f",&diam[j],&frac[j]);
		if (!feof(fpin)) {
			frac[j] = frac[j]/100.0;
			j++;
		}
	}
	fclose(fpin);

	number_entries = j;

	/***
	*	Perform bubble sort in ascending order of
	*	particle diameters
	***/

	for (i = 0; i < number_entries - 1; i++) {
		for (j = (i+1); j < number_entries; j++) {
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

	/*** Bubble sort is finished ***/

	/***
	*	Construct cumulative PSD for the
	*	pdiam values instead of the diam values,
	*	using linear interpolation
	***/

	for (i = 0; i < 20; i++) {
		done = 0;
		j = 0;
		pdiam[i][1] = 0.0;
		while ((j < number_entries) && (!done)) {
			if (diam[j] < pdiam[i][0]) {
				j++;
			} else {

				/***
				*	Interpolate between j-1 and j
				***/

				slope = (frac[j] - frac[j-1]) / (diam[j] - diam[j-1]);
				intercept = frac[j-1];
				pdiam[i][1] = slope * (pdiam[i][0] - diam[j-1]);
				pdiam[i][1] += intercept;
				done = 1;
			}
		}
	}
	
	pdiam[20][1] = 1.0;

	/***
	*	Form differential PSD based on the interpolated
	*	cumulative PSD (simple subtraction)
	***/

	for (i = 20; i > 0; i--) {
		pdiam[i][1] -= pdiam[i-1][1];
	}

	/***
	*	Now attempt to open a PSD file and write to it
	***/

	printf("\n\nEnter a PSD file name to create:  ");
	read_string(outfile,sizeof(outfile));
	if ((fpout = fopen(outfile,"w")) == NULL) {
		printf("\n\nERROR:  Could not open file %s for output",outfile);
		exit(1);
	}

	/***
	*	Print header
	***/

	totfrac = 0.0;
	fprintf(fpout,"Diameter_(um) Wt._frac.\n");
	for (i = 0; i < NUMBINS; i++) {
		fprintf(fpout,"%d %f\n",(int) pdiam[i][0],pdiam[i][1]);
		totfrac += pdiam[i][1];
	}
	fclose(fpout);
	printf("\n\nTotal fraction is %f\n\n",totfrac);
}
