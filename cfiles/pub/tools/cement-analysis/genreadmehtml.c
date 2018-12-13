/*********************************************************
*	Generates html page for a characterized cement,
*	given input data file for the phase fractions, number
*	of images used to average, etc.
*********************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "vcctl.h"

int main(int argc, char *argv[])
{

	register int i;
	char buff[MAXSTRING],buff1[MAXSTRING],blaine[MAXSTRING];
	char method[MAXSTRING];
	char name[MAXSTRING],suffix[MAXSTRING],numimages[MAXSTRING];
	char ave[MAXSTRING],range[MAXSTRING];
	char avec3s[MAXSTRING],avec2s[MAXSTRING];
	char avec3a[MAXSTRING],avec4af[MAXSTRING];
	char avek2s[MAXSTRING],aven2s[MAXSTRING];
	char c3svstring[10],c3sastring[10];
	char c2svstring[10],c2sastring[10];
	char c3avstring[10],c3aastring[10];
	char c4fvstring[10],c4fastring[10];
	char k2ovstring[10],k2oastring[10];
	char n2ovstring[10],n2oastring[10];
	FILE *infile,*htm;

	if (argc != 2) {
		printf("\n\nUsage: genreadmehtml infile.dat\n\n");
		exit(0);
	}

	if ((infile = fopen(argv[1],"r")) == NULL) {
		printf("\n\nCould not open input file %s.  Exiting.\n\n",argv[1]);
		exit(1);
	}

	if ((htm = fopen("README.html","w")) == NULL) {
		printf("\n\nCould not open output file %s.  Exiting.\n\n",buff);
		fclose(infile);
		exit(1);
	}

	sprintf(c3svstring,"c3sv");
	sprintf(c3sastring,"c3sa");
	sprintf(c2svstring,"c2sv");
	sprintf(c2sastring,"c2sa");
	sprintf(c3avstring,"c3av");
	sprintf(c3aastring,"c3av");
	sprintf(c4fvstring,"c4fv");
	sprintf(c4fastring,"c4fa");
	sprintf(k2ovstring,"k2sv");
	sprintf(k2oastring,"k2sa");
	sprintf(n2ovstring,"n2sv");
	sprintf(n2oastring,"n2sa");

	fscanf(infile,"%s %s",buff1,buff);
	fprintf(htm,"<HTML>%c",10);
	fprintf(htm,"<HEAD>%c",10);
	fprintf(htm,"<TITLE>Information on %s</TITLE>%c",buff,10);
	fprintf(htm,"</HEAD>%c",10);
	fprintf(htm,"<BODY bgcolor=\"#ffffff\"%c",10);
	fprintf(htm,"\tbackground=\"../images2/vcctl_logo_bg.gif\">%c",10);
	fprintf(htm,"<CENTER>%c",10);

	for (i = 0; i < strlen(buff); i++) {
		buff1[i] = toupper(buff[i]);
	}

	fprintf(htm,"<H2>INFORMATION ON %s</H2>%c",buff1,10);
	fprintf(htm,"</CENTER>%c",10);
	fprintf(htm,"<H2>General</H2>%c",10);
	fprintf(htm,"<H4>Image and correlation files for %s, %c",buff,10);
	fprintf(htm,"with a specific surface area of about ");
	fscanf(infile,"%s %s",buff1,blaine);
	fscanf(infile,"%s %s",buff1,method);
	fprintf(htm,"%s m<sup>2</sup>/kg (according to ",blaine);
	if (atoi(method) == 0) {
		fprintf(htm,"unknown technique");
	} else if (atoi(method) == 1) {
		fprintf(htm,"Blaine fineness");
	} else if (atoi(method) == 2) {
		fprintf(htm,"nitrogen adsorption");
	} else if (atoi(method) == 3) {
		fprintf(htm,"PSD analysis");
	}
	fprintf(htm,").</H4>%c",10);
	fprintf(htm,"<H2>Image</H2>%c",10);
	fscanf(infile,"%s %s",buff1,name);
	fprintf(htm,"<H4>Original processed 2D SEM image is ");
	fprintf(htm,"%s.gif (500X Magnification- 256 &#181m by 200 ",name);
	fprintf(htm,"&#181m))</H4>%c",10);
	fprintf(htm,"<H2>Microstructure</H2>%c",10);
	fprintf(htm,"<H4>Discretized particle size distribution is available ");
	fprintf(htm,"in %s.psd</H4>%c",name,10);
	fprintf(htm,"<H4>Extracted correlation files (1 &#181m/pixel):%c",10);
	fprintf(htm,"<UL>%c",10);
	fscanf(infile,"%s",buff1);
	while (strcmp(buff1,"numimg")) {
		fscanf(infile,"%s",suffix);
		fprintf(htm,"<LI> %s.%s --- ",name,suffix);
		if (!strcmp(suffix,"sil")) {
			fprintf(htm,"C<sub>3</sub>S and C<sub>2</sub>S%c",10);
		} else if (!strcmp(suffix,"c3s")) {
			fprintf(htm,"C<sub>3</sub>S%c",10);
		} else if (!strcmp(suffix,"c2s")) {
			fprintf(htm,"C<sub>2</sub>S%c",10);
		} else if (!strcmp(suffix,"alu")) {
			fprintf(htm,"C<sub>3</sub>A and C<sub>4</sub>AF%c",10);
		} else if (!strcmp(suffix,"c3a")) {
			fprintf(htm,"C<sub>3</sub>A%c",10);
		} else if (!strcmp(suffix,"c4f")) {
			fprintf(htm,"C<sub>4</sub>AF%c",10);
		} else if (!strcmp(suffix,"k2o")) {
			fprintf(htm,"K<sub>2</sub>SO<sub>4</sub>%c",10);
		} else if (!strcmp(suffix,"n2o")) {
			fprintf(htm,"Na<sub>2</sub>SO<sub>4</sub>%c",10);
		}
		fscanf(infile,"%s",buff1);
	}
	fprintf(htm,"</UL></H4>%c",10);
	fprintf(htm,"<hr noshade>%c",10);
	fprintf(htm,"<CENTER>%c",10);
	fprintf(htm,"<H2>Phase Fractions of the Major Clinker ");
	fprintf(htm,"Phases</H2>%c",10);
	fscanf(infile,"%s",numimages);
	if (!strcmp(numimages,"one")) {
		fprintf(htm,"<H4>Based on one image</H4>%c",10);
	} else if (!strcmp(numimages,"two")) {
		fprintf(htm,"<H4>Average (range) of two images</H4>%c",10);
	} else {
		fprintf(htm,"<H4>Average (std. dev.) of %s images</H4>%c",numimages,10);
	}
	fprintf(htm,"<table width=45%% border=1>%c",10);
	fprintf(htm,"<tr><td align=center>PHASE</td><td align=");
	fprintf(htm,"center>AREA</td><td align=center>PERIMETER ");
	fprintf(htm,"(SURFACE)</td></tr>%c",10);
	fscanf(infile,"%s",buff1);
	while (strcmp(buff1,"C<SUB>3</SUB>S")) {
		fscanf(infile,"%s %s",ave,range);
		if (!strcmp(buff1,c3svstring)) {
			fprintf(htm,"<tr><td align=center>C<sub>3</sub>S</td><td ");
			strcpy(avec3s,ave);
		} else if (!strcmp(buff1,c2svstring)) {
			fprintf(htm,"<tr><td align=center>C<sub>2</sub>S</td><td ");
			strcpy(avec2s,ave);
		} else if (!strcmp(buff1,c3avstring)) {
			fprintf(htm,"<tr><td align=center>C<sub>3</sub>A</td><td ");
			strcpy(avec3a,ave);
		} else if (!strcmp(buff1,c4fvstring)) {
			fprintf(htm,"<tr><td align=center>C<sub>4</sub>AF</td><td ");
			strcpy(avec4af,ave);
		} else if (!strcmp(buff1,k2ovstring)) {
			fprintf(htm,"<tr><td align=center>K<sub>2</sub>SO<sub>4</sub></td><td ");
			strcpy(avek2s,ave);
		} else if (!strcmp(buff1,n2ovstring)) {
			fprintf(htm,"<tr><td align=center>Na<sub>2</sub>SO<sub>4</sub></td><td ");
			strcpy(aven2s,ave);
		}
	if (!strcmp(numimages,"one")) {
	    fprintf(htm,"align=center>%s</td>",ave);
    } else {
	    fprintf(htm,"align=center>%s (%s)</td>",ave,range);
    }
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(htm,"<td align=center>%s</td></tr>%c",ave,10);
    } else {
	    fprintf(htm,"<td align=center>%s (%s)</td></tr>%c",ave,range,10);
    }
	fscanf(infile,"%s",buff1);
	}

	fprintf(htm,"</table>%c",10);
	fprintf(htm,"<hr noshade>%c",10);
	fprintf(htm,"<H2>Overall Phase Fractions</H2>%c",10);
	if (!strcmp(numimages,"one")) {
		fprintf(htm,"<H4>Based on one image</H4>%c",10);
	} else if (!strcmp(numimages,"two")) {
		fprintf(htm,"<H4>Average (range) of two images</H4>%c",10);
	} else {
		fprintf(htm,"<H4>Average (std. dev.) of %s images</H4>%c",numimages,10);
	}
	fprintf(htm,"<table width=30%% border=1>%c",10);
	fprintf(htm,"<tr><td align=center>PHASE</td><td align=center>AREA</td></tr>%c",10);
	while (strcmp(buff1,"gypamount")) {
		fscanf(infile,"%s %s",ave,range);
		fprintf(htm,"<tr><td align=center>%s</td>",buff1);
	    if (!strcmp(numimages,"one")) {
		    fprintf(htm,"<td align=center>%s</td></tr>%c",ave,10);
	    } else {
		    fprintf(htm,"<td align=center>%s (%s)</td></tr>%c",ave,range,10);
        }
		fscanf(infile,"%s",buff1);
	}
	fprintf(htm,"</table>%c",10);
	fprintf(htm,"</CENTER>%c",10);
	fprintf(htm,"<hr noshade>%c",10);
	fscanf(infile,"%s",ave);
	fprintf(htm,"<H4>Gypsum typically added as %4.2f per cent on a ",atof(ave)*100.0);
	fprintf(htm,"volume basis.</H4>%c",10);
	fprintf(htm,"<H4>Use the back button on your Web browser to ");
	fprintf(htm,"return to the cement image.</H4>%c",10);
	fprintf(htm,"<P>&nbsp;</P></BODY>%c",10);
	fprintf(htm,"</HTML>%c",10);

	fclose(infile);
	fclose(htm);
    exit(0);
}
