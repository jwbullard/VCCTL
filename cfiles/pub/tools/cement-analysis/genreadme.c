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

	register int i;
	char buff[MAXSTRING],buff1[MAXSTRING],blaine[MAXSTRING];
	char method[MAXSTRING];
	char name[MAXSTRING],suffix[MAXSTRING],numimages[MAXSTRING];
	char ave[MAXSTRING],range[MAXSTRING];
	char avec3s[MAXSTRING],avec2s[MAXSTRING];
	char avec3a[MAXSTRING],avec4af[MAXSTRING];
	char avek2s[MAXSTRING],aven2s[MAXSTRING];
	FILE *infile,*txt;

	if (argc != 2) {
		printf("\n\nUsage: genreadme infile.dat\n\n");
		exit(0);
	}

	if ((infile = fopen(argv[1],"r")) == NULL) {
		printf("\n\nCould not open input file %s.  Exiting.\n\n",argv[1]);
		exit(1);
	}

	if ((txt = fopen("README","w")) == NULL) {
		printf("\n\nCould not open output file %s.  Exiting.\n\n",buff);
		fclose(infile);
		exit(1);
	}

	fscanf(infile,"%s %s",buff1,buff);
	for (i = 0; i < strlen(buff); i++) {
		buff1[i] = toupper(buff[i]);
        if (buff[i] == '_') {
            buff[i] = ' ';
            buff1[i] = ' ';
        }
	}

	fprintf(txt,"INFORMATION ON %s\n\n",buff1);
	fprintf(txt,"General Information:\n\n");
	fprintf(txt,"Image and correlation files for %s,\n",buff);
	fprintf(txt,"with a specific surface area of about ");
	fscanf(infile,"%s %s",buff1,blaine);
	fscanf(infile,"%s %s",buff1,method);
	fprintf(txt,"%s m^2/kg (according to ",blaine);
	if (atoi(method) == 0) {
		fprintf(txt,"unknown technique");
	} else if (atoi(method) == 1) {
		fprintf(txt,"Blaine fineness");
	} else if (atoi(method) == 2) {
		fprintf(txt,"nitrogen adsorption");
	} else if (atoi(method) == 3) {
		fprintf(txt,"PSD analysis");
	}
	fprintf(txt,").\n\n\n");
	fprintf(txt,"IMAGE\n");
	fprintf(txt,"-----\n\n");
	fscanf(infile,"%s %s",buff1,name);
	fprintf(txt,"Original processed 2D SEM image is ");
	fprintf(txt,"%s.gif\n(500X Magnification- 256 um by 200 um)\n\n",name);
	fprintf(txt,"MICROSTRUCTURE\n");
	fprintf(txt,"--------------\n\n");
	fprintf(txt,"* Particle size distribution is available ");
	fprintf(txt,"in %s.psd\n",name);
	fprintf(txt,"* Extracted correlation files (1 um/pixel):\n");
	for (i = 1; i <= 5; i++) {
		fscanf(infile,"%s %s",buff1,suffix);
		fprintf(txt," -- %s.%s : ",name,suffix);
		if (!strcmp(suffix,"sil")) {
			fprintf(txt,"C3S and C2S\n");
		} else if (!strcmp(suffix,"c3s")) {
			fprintf(txt,"C3S\n");
		} else if (!strcmp(suffix,"c2s")) {
			fprintf(txt,"C2S\n");
		} else if (!strcmp(suffix,"c3a")) {
			fprintf(txt,"C3A\n");
		} else if (!strcmp(suffix,"c4f")) {
			fprintf(txt,"C4AF\n");
		} else if (!strcmp(suffix,"alu")) {
			fprintf(txt,"C3A and C4AF\n");
		} else if (!strcmp(suffix,"k2o")) {
			fprintf(txt,"K2SO4\n");
		}
	}
	fprintf(txt,"\n");
	fprintf(txt,"FRACTIONS OF THE FOUR MAJOR CLINKER ");
	fprintf(txt,"PHASES\n\n");
	fscanf(infile,"%s %s",buff1,numimages);
	if (!strcmp(numimages,"one")) {
		fprintf(txt,"(Based on one image)\n\n");
	} else if (!strcmp(numimages,"two")) {
		fprintf(txt,"(Average (range) of two images)\n\n");
	} else {
		fprintf(txt,"(Average (std. dev.) of %s images)\n\n",numimages);
	}
	fprintf(txt,"PHASE   AREA          PERIMETER");
	fprintf(txt,"-----   ----          ---------");
	fprintf(txt,"C3S     ");
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(txt,"%s            ",ave);
    } else {
	    fprintf(txt,"%s (%s)   ",ave,range);
    }
	strcpy(avec3s,ave);
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(txt,"%s\n",ave);
    } else {
	    fprintf(txt,"%s (%s)\n",ave,range);
    }
	fscanf(infile,"%s %s %s",buff1,ave,range);
	fprintf(txt,"C2S     ");
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(txt,"%s            ",ave);
    } else {
	    fprintf(txt,"%s (%s)   ",ave,range);
    }
	strcpy(avec2s,ave);
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(txt,"%s\n",ave);
    } else {
	    fprintf(txt,"%s (%s)\n",ave,range);
    }
	fscanf(infile,"%s %s %s",buff1,ave,range);
	fprintf(txt,"C3A     ");
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(txt,"%s            ",ave);
    } else {
	    fprintf(txt,"%s (%s)   ",ave,range);
    }
	strcpy(avec3a,ave);
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(txt,"%s\n",ave);
    } else {
	    fprintf(txt,"%s (%s)\n",ave,range);
    }
	fscanf(infile,"%s %s %s",buff1,ave,range);
	fprintf(txt,"C4AF    ");
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(txt,"%s            ",ave);
    } else {
	    fprintf(txt,"%s (%s)   ",ave,range);
    }
	strcpy(avec4af,ave);
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(txt,"%s\n",ave);
    } else {
	    fprintf(txt,"%s (%s)\n",ave,range);
    }
	fscanf(infile,"%s %s %s",buff1,ave,range);
	fprintf(txt,"K2SO4   ");
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(txt,"%s            ",ave);
    } else {
	    fprintf(txt,"%s (%s)   ",ave,range);
    }
	strcpy(avek2s,ave);
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(txt,"%s\n",ave);
    } else {
	    fprintf(txt,"%s (%s)\n",ave,range);
    }
	fscanf(infile,"%s %s %s",buff1,ave,range);
	fprintf(txt,"Na2SO4  ");
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(txt,"%s            ",ave);
    } else {
	    fprintf(txt,"%s (%s)   ",ave,range);
    }
	strcpy(aven2s,ave);
	fscanf(infile,"%s %s %s",buff1,ave,range);
	if (!strcmp(numimages,"one")) {
	    fprintf(txt,"%s\n",ave);
    } else {
	    fprintf(txt,"%s (%s)\n",ave,range);
    }
    fprintf(txt,"\n\n");
	fprintf(txt,"OVERALL PHASE FRACTIONS\n\n");
	if (!strcmp(numimages,"one")) {
		fprintf(txt,"(Based on one image)\n\n");
	} else if (!strcmp(numimages,"two")) {
		fprintf(txt,"(Average (range) of two images)\n\n");
	} else {
		fprintf(txt,"(Average (std. dev.) of %s images)\n\n",numimages);
	}
	fprintf(txt,"PHASE\t\tAREA\n");
	fprintf(txt,"-----\t\t----\n");
	fscanf(infile,"%s",buff1);
	while (strcmp(buff1,"gypamount")) {
		fscanf(infile,"%s %s",ave,range);
		fprintf(txt,"%s\t",buff1);
	    if (!strcmp(numimages,"one")) {
		    fprintf(txt,"%s\n",ave);
	    } else {
		    fprintf(txt,"%s (%s)\n",ave,range);
        }
		fscanf(infile,"%s",buff1);
	}
    fprintf(txt,"\n\n");
	fscanf(infile,"%s",ave);
	fprintf(txt,"Gypsum typically added as %4.2f per cent on a ",atof(ave)*100.0);
	fprintf(txt,"volume basis.");
	fclose(infile);
	fclose(txt);
}
