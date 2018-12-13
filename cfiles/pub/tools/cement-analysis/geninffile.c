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

	float tot;
	float c3s,c2s,c3a,c4f,k2s,n2s;
	char buff[MAXSTRING],buff1[MAXSTRING],blaine[MAXSTRING];
	char method[MAXSTRING];
	char suffix[MAXSTRING],numimages[MAXSTRING];
	char c3svstring[10],c2svstring[10],c3avstring[10],c4fvstring[10];
	char k2svstring[10],n2svstring[10];
	FILE *infile,*inf;

	c3s = c2s = c3a = c4f = k2s = n2s = tot = 0.00000;

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

	sprintf(buff,"%s-info.dat",argv[1]);
	if ((inf = fopen(buff,"w")) == NULL) {
		printf("\n\nCould not open output file %s.  Exiting.\n\n",buff);
		fclose(infile);
		exit(1);
	}

	fscanf(infile,"%s %s",buff1,buff);
	fprintf(inf,"%s\n",buff);
	printf("%s\n",buff);
	fscanf(infile,"%s %s",buff1,blaine);
	fscanf(infile,"%s %s",buff1,method);
	if (!strcmp(blaine,"??")) {
		fprintf(inf,"---\n");
		printf("---\n");
	} else {
		fprintf(inf,"%s\n",blaine);
		printf("%s\n",blaine);
	}
	printf("%s\n",method);
	fflush(stdout);
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
			fscanf(infile,"%s",buff);
		} else if (!strcmp(buff1,c2svstring)) {
			c2s = atof(buff);
			tot += c2s;
			fscanf(infile,"%s",buff);
			fscanf(infile,"%s %s",buff,buff1);
			fscanf(infile,"%s",buff);
		} else if (!strcmp(buff1,c3avstring)) {
			c3a = atof(buff);
			tot += c3a;
			fscanf(infile,"%s",buff);
			fscanf(infile,"%s %s",buff,buff1);
			fscanf(infile,"%s",buff);
		} else if (!strcmp(buff1,c4fvstring)) {
			c4f = atof(buff);
			tot += c4f;
			fscanf(infile,"%s",buff);
			fscanf(infile,"%s %s",buff,buff1);
			fscanf(infile,"%s",buff);
		} else if (!strcmp(buff1,k2svstring)) {
			k2s = atof(buff);
			tot += k2s;
			fscanf(infile,"%s",buff);
			fscanf(infile,"%s %s",buff,buff1);
			fscanf(infile,"%s",buff);
		} else if (!strcmp(buff1,n2svstring)) {
			n2s = atof(buff);
			tot += n2s;
			fscanf(infile,"%s",buff);
			fscanf(infile,"%s %s",buff,buff1);
			fscanf(infile,"%s",buff);
		}
		fscanf(infile,"%s",buff1);
	}

	/* Renormalize the four major clinker phases */

	tot -= (k2s + n2s);
	printf("\nC3S = %f, tot = %f ",c3s,tot);
	c3s /= tot;
	printf("new C3S = %f",c3s);
	printf("\nC2S = %f, tot = %f ",c2s,tot);
	c2s /= tot;
	printf("new C2S = %f",c2s);
	printf("\nC3A = %f, tot = %f ",c3a,tot);
	c3a /= tot;
	printf("new C3A = %f",c3a);
	printf("\nC4AF = %f, tot = %f ",c4f,tot);
	c4f /= tot;
	printf("new C4AF = %f\n",c4f);

	fprintf(inf,"%6.4f\n",c3s);
	fprintf(inf,"%6.4f\n",c2s);
	fprintf(inf,"%6.4f\n",c3a);
	fprintf(inf,"%6.4f\n",c4f);
	printf("%6.4f\n",c3s);
	printf("%6.4f\n",c2s);
	printf("%6.4f\n",c3a);
	printf("%6.4f\n",c4f);
	fclose(infile);
	fclose(inf);
    exit(0);
}
