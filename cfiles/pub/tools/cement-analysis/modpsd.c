#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "vcctl.h"

#define MAXPART	500

/* Global variables */

FILE *Fpin,*Fpout;

int checkargs(int argc, char *argv[]);
float diameter2volume(float diam);

int main(int argc, char *argv[])
{
	int i,maxbin;
	float partdiam[MAXPART],partvol[MAXPART];
	float massfrac[MAXPART],volfrac[MAXPART];
	float totmass,totvol;
	char filein[MAXSTRING],fileout[MAXSTRING],ch;

	i = checkargs(argc,argv);
	if (i == 1) {
		printf("\n\nUsage:\tmodpsd infile outfile\n\n");
		exit(1);
	} else if (i > 0) {
		exit(1);
	}

	for(i=0;i<MAXPART;i++){
		partvol[i]=0.0;
		massfrac[i]=0.0;
		volfrac[i]=0.0;
	}

	/*
	partvol[1]=1.0;
	partvol[3]=19.;
	partvol[5]=81.;
	partvol[7]=179.;
	partvol[9]=389.;
	partvol[11]=739.;
	partvol[13]=1189.;
	partvol[15]=1791.;
	partvol[17]=2553.;
	partvol[19]=3695.;
	partvol[21]=4945.;
	partvol[23]=6403.;
	partvol[25]=8217.;
	partvol[27]=10395.;
	partvol[29]=12893.;
	partvol[31]=15515.;
	partvol[33]=18853.;
	partvol[35]=22575.;
	partvol[37]=26745.;
	partvol[39]=31103.;
	partvol[41]=36137.;
	partvol[47]=54435.;
	partvol[61]=119009.;
	partvol[73]=203965.;
	partvol[87]=345243.;
	*/

	printf("Enter name of file with the raw PSD \n");
	strcpy(filein,argv[1]);
	printf("%s\n",filein);

	/* Read the one-line header and discard it */
	ch = 'A';
	while (ch != '\n') {
		fscanf(Fpin,"%c",&ch);
	}

	printf("Enter name of file for output\n");
	strcpy(fileout,argv[2]);
	printf("%s\n",fileout);
	fprintf(Fpout,"Diam_(um)  Wt._frac.  Part_vol  Number_frac\n");

	totvol=0.0;
	totmass=0.0;
	i = 0;
	while(!feof(Fpin)){
		fscanf(Fpin,"%f %f",&partdiam[i],&massfrac[i]);
		partvol[i] = diameter2volume(partdiam[i]);
		if (!feof(Fpin)) {
			if(partvol[i]==0.0){
				printf("error for particle size %f \n",partdiam[i]);
				exit(1);
			}
			totmass+=massfrac[i];
			volfrac[i]=massfrac[i]/partvol[i];
			totvol+=volfrac[i];
			printf("partdiam = %f, total mass = %f\n",partdiam[i],totmass);
			i++;
		}
	}

	maxbin = i;

	printf("total mass and volume are %f and %f \n",totmass,totvol);


	for(i=0;i<maxbin;i++){
		volfrac[i]/=totvol;
		if(massfrac[i]!=0.0){
			fprintf(Fpout,"%f  %f  %f  %f\n",partdiam[i],massfrac[i],partvol[i],volfrac[i]);
		}
	}

	fclose(Fpout);
	fclose(Fpin);
    exit(0);
}

float diameter2volume(float diam)
{
	float pi,volume=0.0;

	pi = 4.0 * atan(1.0);
	volume = (4.0 * pi / 3.0) * pow((diam/2.0),3.0);
	return(volume);
}

int checkargs(int argc, char *argv[])
{
       int status=0;
       int inindex,outindex;

       if (argc != 3) {
          status = 1;
          return status;
       }

       inindex = outindex = 0;
                
       if ((Fpin = fopen(argv[1],"r")) == NULL) {
             printf("\n\nERROR: Could not open file %s\n\n",argv[1]);
             status = 2;
             return status;
       }

       if ((Fpout = fopen(argv[2],"w")) == NULL) {
              printf("\n\nERROR: Could not open file %s\n\n",argv[2]);
              status = 2;
              return status;
       }

       return status;
}
