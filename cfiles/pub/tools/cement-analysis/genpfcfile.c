/*********************************************************
*	Generates html page for a characterized cement,
*	given input data file for the phase fractions, number
*	of images used to average, etc.
*********************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "vcctl.h"

int main(int argc, char *argv[])
{
	float tot,atot;
	float c3s,c2s,c3a,c4f,k2s,n2s;
	float ac3s,ac2s,ac3a,ac4f,ak2s,an2s;
	char buff[MAXSTRING],buff1[MAXSTRING],blaine[MAXSTRING];
	char method[MAXSTRING];
	char suffix[MAXSTRING],numimages[MAXSTRING];
	char c3svstring[10],c2svstring[10],c3avstring[10],c4fvstring[10];
	char k2svstring[10],n2svstring[10];
	FILE *infile,*inf;

	c3s = c2s = c3a = c4f = k2s = n2s = tot = 0.00000;
	ac3s = ac2s = ac3a = ac4f = ak2s = an2s = atot = 0.00000;

	sprintf(c3svstring,"c3sv");
	sprintf(c2svstring,"c2sv");
	sprintf(c3avstring,"c3av");
	sprintf(c4fvstring,"c4fv");
	sprintf(k2svstring,"k2sv");
	sprintf(n2svstring,"n2sv");

	if (argc != 2) {
		printf("\n\nUsage: geninffile rootname\n\n");
		exit(0);
	}

	sprintf(buff,"%shtml.txt",argv[1]);
	if ((infile = fopen(buff,"r")) == NULL) {
		printf("\n\nCould not open input file %s.  Exiting.\n\n",buff);
		exit(1);
	}

	sprintf(buff,"%s.pfc",argv[1]);
	if ((inf = fopen(buff,"w")) == NULL) {
		printf("\n\nCould not open output file %s.  Exiting.\n\n",buff);
		fclose(infile);
		exit(1);
	}

	fscanf(infile,"%s %s",buff1,buff);
	fscanf(infile,"%s %s",buff1,blaine);
	fscanf(infile,"%s %s",buff1,method);
	fscanf(infile,"%s %s",buff1,buff);
	fscanf(infile,"%s",buff1);
	while (strcmp(buff1,"numimg")) {
		fscanf(infile,"%s",suffix);
		fscanf(infile,"%s",buff1);
	}
	fscanf(infile,"%s",numimages);
	fscanf(infile,"%s",buff1);
	while (strcmp(buff1,"C<SUB>3</SUB>S")) {
		fscanf(infile,"%s",buff);
		if (!strcmp(buff1,c3svstring)) {
			c3s = atof(buff);
			tot += c3s;
			fscanf(infile,"%s",buff);
			fscanf(infile,"%s %s",buff,buff1);
			ac3s = atof(buff1);
			atot += ac3s;
			fscanf(infile,"%s",buff);
		} else if (!strcmp(buff1,c2svstring)) {
			c2s = atof(buff);
			tot += c2s;
			fscanf(infile,"%s",buff);
			fscanf(infile,"%s %s",buff,buff1);
			ac2s = atof(buff1);
			atot += ac2s;
			fscanf(infile,"%s",buff);
		} else if (!strcmp(buff1,c3avstring)) {
			c3a = atof(buff);
			tot += c3a;
			fscanf(infile,"%s",buff);
			fscanf(infile,"%s %s",buff,buff1);
			ac3a = atof(buff1);
			atot += ac3a;
			fscanf(infile,"%s",buff);
		} else if (!strcmp(buff1,c4fvstring)) {
			c4f = atof(buff);
			tot += c4f;
			fscanf(infile,"%s",buff);
			fscanf(infile,"%s %s",buff,buff1);
			ac4f = atof(buff1);
			atot += ac4f;
			fscanf(infile,"%s",buff);
		} else if (!strcmp(buff1,k2svstring)) {
			k2s = atof(buff);
			tot += k2s;
			fscanf(infile,"%s",buff);
			fscanf(infile,"%s %s",buff,buff1);
			ak2s = atof(buff1);
			atot += ak2s;
			fscanf(infile,"%s",buff);
		} else if (!strcmp(buff1,n2svstring)) {
			n2s = atof(buff);
			tot += n2s;
			fscanf(infile,"%s",buff);
			fscanf(infile,"%s %s",buff,buff1);
			an2s = atof(buff1);
			atot += an2s;
			fscanf(infile,"%s",buff);
		}
		fscanf(infile,"%s",buff1);
	}

	/* Renormalize the four major clinker phases */

	c3s /= tot;
	c2s /= tot;
	c3a /= tot;
	c4f /= tot;
	k2s /= tot;
	n2s /= tot;
	ac3s /= atot;
	ac2s /= atot;
	ac3a /= atot;
	ac4f /= atot;
	ak2s /= atot;
	an2s /= atot;
	fprintf(inf,"%6.4f %6.4f\n",c3s,ac3s);
	fprintf(inf,"%6.4f %6.4f\n",c2s,ac2s);
	fprintf(inf,"%6.4f %6.4f\n",c3a,ac3a);
	fprintf(inf,"%6.4f %6.4f\n",c4f,ac4f);
	fprintf(inf,"%6.4f %6.4f\n",k2s,ak2s);
	fprintf(inf,"%6.4f %6.4f\n",n2s,an2s);
	fclose(infile);
	fclose(inf);
    exit(0);
}
