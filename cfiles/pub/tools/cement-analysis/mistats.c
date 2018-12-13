/************************************************************************
*                                                                     
*      Program: mistats.c                                            
*      Purpose: To convert volume fractions of the major cement
*              phases to mass fractions.  Takes input as the number
*              of pixels found for each of these four phases      
*      	(output from program statsimp)
*                                                            
*      Programmer: Jeffrey W. Bullard
*                  NIST
*                  100 Bureau Drive Stop 8621
*                  Building 226 Room B-350
*                  Gaithersburg, MD  20899-8621
*                  Phone: (301) 975-5725
*                  Fax: (301) 990-6891
*                  E-mail: bullard@nist.gov
*
************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#include "vcctl.h"

#define LC3S			C3S
#define LC2S			LC3S + 1
#define LC3A			LC2S + 1
#define LC4AF		LC3A + 1
#define LGYPSUM		LC4AF + 1
#define LLIME		LGYPSUM + 1
#define	LKAOLIN		LLIME + 1
#define LSLAG		LKAOLIN + 1
#define LKSULF		LSLAG + 1
#define LNASULF		LKSULF + 1
#define LPERICLASE	LNASULF + 1
#define LSILICA		LPERICLASE + 1
#define LC3SVF		LSILICA + 1
#define LC2SVF		LC3SVF + 1
#define LC3AVF		LC2SVF + 1
#define LC4AFVF		LC3AVF + 1
#define LK2SO4VF	LC4AFVF + 1
#define LNA2SO4VF	LK2SO4VF + 1
#define LC3SAF		LNA2SO4VF + 1
#define LC2SAF		LC3SAF + 1
#define LC3AAF		LC2SAF + 1
#define LC4AFAF		LC3AAF + 1
#define LK2SO4AF	LC4AFAF + 1
#define LNA2SO4AF	LK2SO4AF + 1
#define LC3SMF		LNA2SO4AF + 1
#define LC2SMF		LC3SMF + 1
#define LC3AMF		LC2SMF + 1
#define LC4AFMF		LC3AMF + 1
#define LK2SO4MF	LC4AFMF + 1
#define LNA2SO4MF	LK2SO4MF + 1

#define NQUANT		LNA2SO4MF + 1

#define MAXIMAGES	10

struct imgdat
{
	float val[NQUANT];
} img_var;

void print_banner(void);
void genlatex();
void genascii();

/****
* Global Variables
****/
float avg[NQUANT],stddev[NQUANT];
int numin;

int main (void)
{
	int i,j;
	char buff[MAXSTRING],buff1[MAXSTRING],answer[5];
	struct imgdat p[MAXIMAGES];
	FILE *infile;

	/* Initialize arrays to zero */

	for (i = 0; i < NQUANT; i++) {
		avg[i] = 0.0;
		stddev[i] = 0.0;
	}

	print_banner();

	printf("\n\nEnter data file name: ");
	read_string(buff,sizeof(buff));
	if ((infile = fopen(buff,"r")) == NULL) {
		printf("\n\nERROR in mistats");
		printf("\n\tCould not open file %s",buff);
		printf("\n\tExiting now.\n\n");
		exit(1);
	}

	i = 0;
	while (!feof(infile)) {
		fscanf(infile,"%s %s",buff1,buff);
		if (!feof(infile)) {
			p[i].val[LC3S] = atof(buff1);
			fscanf(infile,"%f %s",&p[i].val[LC2S],buff);
			fscanf(infile,"%f %s",&p[i].val[LC3A],buff);
			fscanf(infile,"%f %s",&p[i].val[LC4AF],buff);
			fscanf(infile,"%f %s",&p[i].val[LGYPSUM],buff);
			fscanf(infile,"%f %s",&p[i].val[LLIME],buff);
			fscanf(infile,"%f %s",&p[i].val[LKAOLIN],buff);
			fscanf(infile,"%f %s",&p[i].val[LSLAG],buff);
			fscanf(infile,"%f %s",&p[i].val[LKSULF],buff);
			fscanf(infile,"%f %s",&p[i].val[LNASULF],buff);
			fscanf(infile,"%f %s",&p[i].val[LPERICLASE],buff);
			fscanf(infile,"%f %s",&p[i].val[LSILICA],buff);
			fscanf(infile,"%f %s",&p[i].val[LC3SVF],buff);
			fscanf(infile,"%f %s",&p[i].val[LC2SVF],buff);
			fscanf(infile,"%f %s",&p[i].val[LC3AVF],buff);
			fscanf(infile,"%f %s",&p[i].val[LC4AFVF],buff);
			fscanf(infile,"%f %s",&p[i].val[LK2SO4VF],buff);
			fscanf(infile,"%f %s",&p[i].val[LNA2SO4VF],buff);
			fscanf(infile,"%f %s",&p[i].val[LC3SAF],buff);
			fscanf(infile,"%f %s",&p[i].val[LC2SAF],buff);
			fscanf(infile,"%f %s",&p[i].val[LC3AAF],buff);
			fscanf(infile,"%f %s",&p[i].val[LC4AFAF],buff);
			fscanf(infile,"%f %s",&p[i].val[LK2SO4AF],buff);
			fscanf(infile,"%f %s",&p[i].val[LNA2SO4AF],buff);
			fscanf(infile,"%f %s",&p[i].val[LC3SMF],buff);
			fscanf(infile,"%f %s",&p[i].val[LC2SMF],buff);
			fscanf(infile,"%f %s",&p[i].val[LC3AMF],buff);
			fscanf(infile,"%f %s",&p[i].val[LC4AFMF],buff);
			fscanf(infile,"%f %s",&p[i].val[LK2SO4MF],buff);
			fscanf(infile,"%f %s",&p[i].val[LNA2SO4MF],buff);
			fscanf(infile,"%s",buff);
			i++;
		}
	}

	numin = i;

	/***
	*	All data are now in the array.
	*	Compute relevant statistical quantities
	***/

	for (j = LC3S; j < NQUANT; j++) {
		avg[j] = 0.0;
		stddev[j] = 0.0;
	}

	for (i = 0; i < numin; i++) {
		for (j = LC3S; j < NQUANT; j++) {
			avg[j] += p[i].val[j];
		}
	}
	
	/* Compute averages */

	for (i = LC3S; i < NQUANT; i++) {
		avg[i] = avg[i] / ((float)numin);
	}

	/* Compute std dev or range */

	if (numin >= 3) {
		for (i = 0; i < NQUANT; i++) {
			for (j = 0; j < numin; j++) {
				stddev[i] += (avg[i] - p[j].val[i]) * (avg[i] - p[j].val[i]);
			}
			stddev[i] = sqrt(stddev[i]/((float)numin));
		}
	} else if (numin > 1) {
		for (i = 0; i < NQUANT; i++) {
			stddev[i] = (p[0].val[i] - p[1].val[i]);
			stddev[i] = sqrt(stddev[i] * stddev[i]);
		}
	} else {
		for (i = 0; i < NQUANT; i++) {
			stddev[i] = 0.0;
		}
	}

	/***
	*	Time to print statistical information
	***/

	if (numin >= 3) {
		sprintf(buff,"SD");
	} else if (numin > 1) {
		sprintf(buff,"Range");
	}

	if (numin > 0) {
		for (i = 0; i < NQUANT; i++) {
			switch(i) {
				case LC3S:
					printf("\n\nFinal image avg. C3S = %7.5f",avg[i]);
					break;
				case LC2S:
					printf("Final image avg. C2S = %7.5f",avg[i]);
					break;
				case LC3A:
					printf("Final image avg. C3A = %7.5f",avg[i]);
					break;
				case LC4AF:
					printf("Final image avg. C4AF = %7.5f",avg[i]);
					break;
				case LGYPSUM:
					printf("Final image avg. GYPSUM = %7.5f",avg[i]);
					break;
				case LLIME:
					printf("Final image avg. LIME = %7.5f",avg[i]);
					break;
				case LKAOLIN:
					printf("Final image avg. KAOLIN = %7.5f",avg[i]);
					break;
				case LSLAG:
					printf("Final image avg. SLAG = %7.5f",avg[i]);
					break;
				case LKSULF:
					printf("Final image avg. KSULF = %7.5f",avg[i]);
					break;
				case LNASULF:
					printf("Final image avg. NASULF = %7.5f",avg[i]);
					break;
				case LPERICLASE:
					printf("Final image avg. PERICLASE = %7.5f",avg[i]);
					break;
				case LSILICA:
					printf("Final image avg. SILICA = %7.5f",avg[i]);
					break;
				case LC3SVF:
					printf("Final C3SVF = %7.5f",avg[i]);
					break;
				case LC2SVF:
					printf("Final C2SVF = %7.5f",avg[i]);
					break;
				case LC3AVF:
					printf("Final C3AVF = %7.5f",avg[i]);
					break;
				case LC4AFVF:
					printf("Final C4AFVF = %7.5f",avg[i]);
					break;
				case LK2SO4VF:
					printf("Final K2SO4VF = %7.5f",avg[i]);
					break;
				case LNA2SO4VF:
					printf("Final NA2SO4VF = %7.5f",avg[i]);
					break;
				case LC3SAF:
					printf("Final C3SAF = %7.5f",avg[i]);
					break;
				case LC2SAF:
					printf("Final C2SAF = %7.5f",avg[i]);
					break;
				case LC3AAF:
					printf("Final C3AAF = %7.5f",avg[i]);
					break;
				case LC4AFAF:
					printf("Final C4AFAF = %7.5f",avg[i]);
					break;
				case LK2SO4AF:
					printf("Final K2SO4AF = %7.5f",avg[i]);
					break;
				case LNA2SO4AF:
					printf("Final NA2SO4AF = %7.5f",avg[i]);
					break;
				case LC3SMF:
					printf("Final C3SMF = %7.5f",avg[i]);
					break;
				case LC2SMF:
					printf("Final C2SMF = %7.5f",avg[i]);
					break;
				case LC3AMF:
					printf("Final C3AMF = %7.5f",avg[i]);
					break;
				case LC4AFMF:
					printf("Final C4AFMF = %7.5f",avg[i]);
					break;
				case LK2SO4MF:
					printf("Final K2SO4MF = %7.5f",avg[i]);
					break;
				case LNA2SO4MF:
					printf("Final NA2SO4MF = %7.5f",avg[i]);
					break;
			}

			if (numin > 1) {
				printf("; %s = %7.5f",buff,stddev[i]);
			}
			printf("\n");
		}

		printf("\n\nGenerate results as pdf (p) or ascii (a)? [p]");
        read_string(answer,sizeof(answer));
		if (strlen(answer) < 1) {
			strcpy(answer,"n");
		}

		if (toupper(answer[0]) == 'P') {
			printf("\nC3S = %6.4f\n",avg[LC3S]);
			genlatex();
		} else if (toupper(answer[0]) == 'A') {
			genascii();
		}

	}
    exit(0);
}

/**********
*		
*	Function print_banner
*
*	Prints a one-line banner at the beginning of the program
*
*	Arguments:  None
*	Returns:	Nothing
*
**********/
void print_banner(void)
{
	printf("\n\n***GENERATE STATISTICS FOR MULTIPLE IMAGES***\n\n");
	return;
}

/**********
*		
*	Function genlatex
*
*	Generate latex file and compile it in pdf format
*
*	Arguments:  None
*
*	Returns:    Nothing
*
**********/
void genlatex()
{
	register int i;
	char filename[MAXSTRING],cmdnew[MAXSTRING],dirname[MAXSTRING];
	FILE *flatex,*scrfile,*mkf;

	sprintf(filename,"averages.tex");
	if ((flatex = fopen(filename,"w")) == NULL) {
		printf("\n\nCould not open latex file for writing\n\n");
		return;
	}
	
	printf("\nC3S = %f",avg[C3S]);
	printf("\nPDF file will be called averages.pdf ..."),
	printf("\n\nGive a name for this directory: ");
    read_string(dirname,sizeof(dirname));

	i = 0;
	while (i < strlen(dirname)) {
		if (dirname[i] == 95) {
			dirname[i] = 45;
		}
		i++;
	}

	fprintf(flatex,"\\documentclass[12pt]{article}\n");
	fprintf(flatex,"\\begin{document}\n");
	fprintf(flatex,"\\begin{center}\n");
	fprintf(flatex,"{\\large{Average phase fractions for {\\bf %s}}}\n",dirname);
	fprintf(flatex,"\\end{center}\n");
	fprintf(flatex,"\n\\vspace{0.125in}\n");
	if (numin > 1) {
		fprintf(flatex,"\\begin{center}\n");
		fprintf(flatex,"Uncertainties reported as ");
		if (numin > 2) {
			fprintf(flatex,"estimated standard deviation of ");
			fprintf(flatex,"{\\bf %d} values\n",numin);
		} else {
			fprintf(flatex,"range of {\\bf two} values\n");
		}
		fprintf(flatex,"\\end{center}\n");
		fprintf(flatex,"\n\\vspace{0.125in}\n");
	}
	fprintf(flatex,"\\begin{center}\n");
	fprintf(flatex,"\\begin{tabular}{r l r l} \\\\ \n");
	printf("\nC3S = %6.4f\n",avg[LC3S]);
	fprintf(flatex,"C$_3$S = & %6.4f",avg[LC3S]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LC3S]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"Kaolin = & %6.4f",avg[LKAOLIN]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) \\\\ \n ",stddev[LKAOLIN]);
	} else {
		fprintf(flatex," \\\\ \n ");
	}
	fprintf(flatex,"C$_2$S = & %6.4f",avg[LC2S]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LC2S]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"Slag = & %6.4f",avg[LSLAG]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) \\\\ \n ",stddev[LSLAG]);
	} else {
		fprintf(flatex," \\\\ \n ");
	}
	fprintf(flatex,"C$_3$A = & %6.4f",avg[LC3A]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LC3A]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"Pot. Sulf. = & %6.4f",avg[LKSULF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) \\\\ \n ",stddev[LKSULF]);
	} else {
		fprintf(flatex," \\\\ \n ");
	}
	fprintf(flatex,"C$_4$AF = & %6.4f",avg[LC4AF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LC4AF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"Sod. Sulf. = & %6.4f",avg[LNASULF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) \\\\ \n ",stddev[LKSULF]);
	} else {
		fprintf(flatex," \\\\ \n ");
	}
	fprintf(flatex,"Mg/Ca = & %6.4f",avg[LPERICLASE]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & \n ",stddev[LPERICLASE]);
	} else {
		fprintf(flatex," & \n ");
	}
	fprintf(flatex,"Gypsum = & %6.4f",avg[LGYPSUM]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) \\\\ ",stddev[LGYPSUM]);
	} else {
		fprintf(flatex," \\\\ ");
	}
	fprintf(flatex,"Silica = & %6.4f",avg[LSILICA]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & \n ",stddev[LSILICA]);
	} else {
		fprintf(flatex," & \n ");
	}
	fprintf(flatex,"Free Lime = & %6.4f",avg[LLIME]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) \\\\ ",stddev[LLIME]);
	} else {
		fprintf(flatex," \\\\ ");
	}

	fprintf(flatex,"\\end{tabular}\n");
	fprintf(flatex,"\\end{center}\n\n");

	fprintf(flatex,"\\vspace{0.25in}\n");
	fprintf(flatex,"\\begin{center}\n");
	fprintf(flatex,"{\\large{Average Clinker fractions for ");
	fprintf(flatex,"{\\bf %s}}}\n",dirname);
	fprintf(flatex,"\\end{center}\n");
	fprintf(flatex,"\n\\vspace{0.125in}\n");
	if (numin > 1) {
		fprintf(flatex,"\\begin{center}\n");
		fprintf(flatex,"Uncertainties reported as ");
		if (numin > 2) {
			fprintf(flatex,"estimated standard deviation of ");
			fprintf(flatex,"{\\bf %d} values\n",numin);
		} else {
			fprintf(flatex,"range of {\\bf two} values\n");
		}
		fprintf(flatex,"\\end{center}\n");
		fprintf(flatex,"\n\\vspace{0.125in}\n");
	}
	fprintf(flatex,"\n\\vspace{0.125in}\n");
	fprintf(flatex,"\\begin{tabular}{c|c|c|c} \\\\ \n");
	fprintf(flatex,"{\\bf Phase} & {\\bf Volume Fraction} & ");
	fprintf(flatex,"{\\bf Area Fraction} & {\\bf Mass Fraction} ");
	fprintf(flatex,"\\\\ \\hline\n");
	fprintf(flatex,"C$_3$S = & %6.4f",avg[LC3SVF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LC3SVF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"%6.4f",avg[LC3SAF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LC3SAF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"%6.4f",avg[LC3SMF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) \\\\ \n ",stddev[LC3SMF]);
	} else {
		fprintf(flatex," \\\\ \n ");
	}
	fprintf(flatex,"C$_2$S = & %6.4f",avg[LC2SVF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LC2SVF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"%6.4f",avg[LC2SAF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LC2SAF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"%6.4f",avg[LC2SMF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) \\\\ \n ",stddev[LC2SMF]);
	} else {
		fprintf(flatex," \\\\ \n ");
	}
	fprintf(flatex,"C$_3$A = & %6.4f",avg[LC3AVF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LC3AVF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"%6.4f",avg[LC3AAF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LC3AAF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"%6.4f",avg[LC3AMF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) \\\\ \n ",stddev[LC3AMF]);
	} else {
		fprintf(flatex," \\\\ \n ");
	}
	fprintf(flatex,"C$_4$AF = & %6.4f",avg[LC4AFVF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LC4AFVF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"%6.4f",avg[LC4AFAF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LC4AFAF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"%6.4f",avg[LC4AFMF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) \n ",stddev[LC4AFMF]);
	} else {
		fprintf(flatex," \n ");
	}

	fprintf(flatex,"K$_2$SO$_4$ = & %6.4f",avg[LK2SO4VF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LK2SO4VF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"%6.4f",avg[LK2SO4AF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LK2SO4AF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"%6.4f",avg[LK2SO4MF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) \n ",stddev[LK2SO4MF]);
	} else {
		fprintf(flatex," \n ");
	}

	fprintf(flatex,"NA$_2$SO$_4$ = & %6.4f",avg[LNA2SO4VF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LNA2SO4VF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"%6.4f",avg[LNA2SO4AF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) & ",stddev[LNA2SO4AF]);
	} else {
		fprintf(flatex," & ");
	}
	fprintf(flatex,"%6.4f",avg[LNA2SO4MF]);
	if (numin > 1) {
		fprintf(flatex," (%6.4f) \n ",stddev[LNA2SO4MF]);
	} else {
		fprintf(flatex," \n ");
	}

	fprintf(flatex,"\\end{tabular}\n\n");
	fprintf(flatex,"\\end{document}");
	fclose(flatex);
	
	if ((mkf = fopen("Makefile","w")) == NULL) {
		printf("\n\nCannot open Makefile \n\n");
		return;
	}

	fprintf(mkf,"all:\taverages clean\n");
	fprintf(mkf,"averages:\taverages.tex\n");
	fprintf(mkf,"\tpdflatex averages; pdflatex averages\n");
	fprintf(mkf,"clean:\n");
	fprintf(mkf,"\t/bin/rm -f *.aux *.out *.log\n");
	fclose(mkf);
	
	if ((scrfile = fopen("mtex.scr","w")) == NULL) {
		printf("\n\nCannot open mtex.scr file \n\n");
		return;
	}

	fprintf(scrfile,"make all >& makelog\n");
	fprintf(scrfile,"gv -quiet averages.pdf\n");
	fclose(scrfile);
	system("chmod 777 mtex.scr");
	
	sprintf(cmdnew,"bash ./mtex.scr &");
	system(cmdnew);

	return;
}
/**********
*		
*	Function genascii
*
*	Generate ascii text file
*
*	Arguments:      None
*
*	Returns:	Nothing
*
**********/
void genascii()
{
	register int i;
	char filename[80],dirname[80];
	FILE *fascii;

	sprintf(filename,"averages.txt");
	if ((fascii = fopen(filename,"w")) == NULL) {
		printf("\n\nCould not open latex file for writing\n\n");
		return;
	}
	
	printf("\nASCII file will be called averages.txt ..."),
	printf("\n\nGive a name for this directory: ");
	scanf("%s",dirname);

	i = 0;
	while (i < strlen(dirname)) {
		if (dirname[i] == 95) {
			dirname[i] = 45;
		}
		i++;
	}

	fprintf(fascii,"\n\n");
	fprintf(fascii,"AVERAGE PHASE VOLUME FRACTIONS FOR %s",dirname);
	fprintf(fascii,"\n\n");
	if (numin > 1) {
		fprintf(fascii,"Uncertainties reported as ");
		if (numin > 2) {
			fprintf(fascii,"estimated standard deviation of ");
			fprintf(fascii,"%d values",numin);
		} else {
			fprintf(fascii,"range of two values");
		}
		fprintf(fascii,"\n\n");
	}

	fprintf(fascii,"      C3S = %6.4f",avg[LC3S]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\t\t",stddev[LC3S]);
	} else {
		fprintf(fascii," \t\t");
	}
	fprintf(fascii,"Kaolin = %6.4f",avg[LKAOLIN]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n",stddev[LKAOLIN]);
	} else {
		fprintf(fascii,"\n");
	}
	fprintf(fascii,"      C2S = %6.4f",avg[LC2S]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\t\t",stddev[LC2S]);
	} else {
		fprintf(fascii," \t\t");
	}
	fprintf(fascii,"Slag = %6.4f",avg[LSLAG]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n",stddev[LSLAG]);
	} else {
		fprintf(fascii,"\n");
	}
	fprintf(fascii,"      C3A = %6.4f",avg[LC3A]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\t\t",stddev[LC3A]);
	} else {
		fprintf(fascii," \t\t");
	}
	fprintf(fascii,"Pot. Sulf. = %6.4f",avg[LKSULF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n",stddev[LKSULF]);
	} else {
		fprintf(fascii,"\n");
	}
	fprintf(fascii,"     C4AF = %6.4f",avg[LC4AF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\t\t",stddev[LC4AF]);
	} else {
		fprintf(fascii," \t\t");
	}
	fprintf(fascii,"Sod. Sulf. = %6.4f",avg[LNASULF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n",stddev[LNASULF]);
	} else {
		fprintf(fascii,"\n");
	}
	fprintf(fascii,"Mg/Ca = %6.4f",avg[LPERICLASE]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\t\t",stddev[LPERICLASE]);
	} else {
		fprintf(fascii,"\t\t");
	}
	fprintf(fascii,"   Gypsum = %6.4f",avg[LGYPSUM]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n",stddev[LGYPSUM]);
	} else {
		fprintf(fascii," \n");
	}
	fprintf(fascii,"Silica = %6.4f",avg[LSILICA]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\t\t",stddev[LSILICA]);
	} else {
		fprintf(fascii,"\t\t");
	}
	fprintf(fascii,"Free Lime = %6.4f",avg[LLIME]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n\n\n",stddev[LLIME]);
	} else {
		fprintf(fascii,"\n\n\n");
	}

	fprintf(fascii,"AVERAGE CLINKER FRACTIONS FOR %s",dirname);
	fprintf(fascii,"\n\n");
	if (numin > 1) {
		fprintf(fascii,"Uncertainties reported as ");
		if (numin > 2) {
			fprintf(fascii,"estimated standard deviation of ");
			fprintf(fascii,"%d values",numin);
		} else {
			fprintf(fascii,"range of two values");
		}
		fprintf(fascii,"\n\n");
	}

	fprintf(fascii,"Phase    Volume Fraction     Area Fraction      Mass Fraction\n\n");
	fprintf(fascii," C3S     %6.4f",avg[LC3SVF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)    ",stddev[LC3SVF]);
	} else {
		fprintf(fascii,"             ");
	}
	fprintf(fascii,"%6.4f",avg[LC3SAF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)    ",stddev[LC3SAF]);
	} else {
		fprintf(fascii,"             ");
	}
	fprintf(fascii,"%6.4f",avg[LC3SMF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n",stddev[LC3SMF]);
	} else {
		fprintf(fascii,"\n");
	}

	fprintf(fascii," C2S     %6.4f",avg[LC2SVF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)    ",stddev[LC2SVF]);
	} else {
		fprintf(fascii,"             ");
	}
	fprintf(fascii,"%6.4f",avg[LC2SAF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)    ",stddev[LC2SAF]);
	} else {
		fprintf(fascii,"             ");
	}
	fprintf(fascii,"%6.4f",avg[LC2SMF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n",stddev[LC2SMF]);
	} else {
		fprintf(fascii,"\n");
	}

	fprintf(fascii," C3A     %6.4f",avg[LC3AVF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)    ",stddev[LC3AVF]);
	} else {
		fprintf(fascii,"             ");
	}
	fprintf(fascii,"%6.4f",avg[LC3AAF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)    ",stddev[LC3AAF]);
	} else {
		fprintf(fascii,"             ");
	}
	fprintf(fascii,"%6.4f",avg[LC3AMF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n",stddev[LC3AMF]);
	} else {
		fprintf(fascii,"\n");
	}

	fprintf(fascii,"C4AF     %6.4f",avg[LC4AFVF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)    ",stddev[LC4AFVF]);
	} else {
		fprintf(fascii,"             ");
	}
	fprintf(fascii,"%6.4f",avg[LC4AFAF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)    ",stddev[LC4AFAF]);
	} else {
		fprintf(fascii,"             ");
	}
	fprintf(fascii,"%6.4f",avg[LC4AFMF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)",stddev[LC4AFMF]);
	}

	fclose(fascii);
	
	return;
}
