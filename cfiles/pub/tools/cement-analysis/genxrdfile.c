/*********************************************************
*	Generates text page showing the XRD data for a given
*	cement
*********************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "vcctl.h"

const float SGC3S = 3.15;
const float SGC2S = 3.28;
const float SGC3AC = 3.03;
const float SGC3AO = 3.05;
const float SGC4AF = 3.73;
const float SGGYPSUM = 2.32;
const float SGHEMIHYD = 2.74;
const float SGANHYDRITE = 2.61;
const float SGNA2SO4 = 2.68;
const float SGK2SO4 = 2.662;
const float SGLIMESTONE = 2.71;
const float SGLIME = 3.31;
const float SGMGO = 3.78;
const float SGLANGBEINITE = 2.83;
const float SGQUARTZ = 2.62;

int main(int argc, char *argv[])
{

	register int i;
    int imax;
	char buff[MAXSTRING],buff1[MAXSTRING];
    float mfrac[100],vfrac[100],totvol;
	FILE *infile,*fpout;

    imax = 0;
    totvol = 0.0;

	if (argc != 3) {
		printf("\n\nUsage: genxrdfile infile_name outfile_name\n\n");
		exit(0);
	}

	if ((infile = fopen(argv[1],"r")) == NULL) {
		printf("\n\nCould not open input file %s.  Exiting.\n\n",argv[1]);
		exit(1);
	}

	if ((fpout = fopen(argv[2],"w")) == NULL) {
		printf("\n\nCould not open output file %s.  Exiting.\n\n",argv[2]);
		fclose(infile);
		exit(1);
	}

	fscanf(infile,"%s %s",buff1,buff);
    i = 0;
    while (!feof(infile)) {
        fscanf(infile,"%s %s",buff1,buff);
        if (!feof(infile)) {
            mfrac[i] = atof(buff);
            if (!strcmp(buff1,"alite")) {
                vfrac[i] = mfrac[i] / SGC3S;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"belite")) {
                vfrac[i] = mfrac[i] / SGC2S;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"alpha-c2s")) {
                vfrac[i] = mfrac[i] / SGC2S;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"ferrite")) {
                vfrac[i] = mfrac[i] / SGC4AF;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"alum-c")) {
                vfrac[i] = mfrac[i] / SGC3AC;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"alum-o")) {
                vfrac[i] = mfrac[i] / SGC3AO;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"periclase")) {
                vfrac[i] = mfrac[i] / SGMGO;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"arcanite")) {
                vfrac[i] = mfrac[i] / SGK2SO4;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"langbeinite")) {
                vfrac[i] = mfrac[i] / SGLANGBEINITE;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"thenardite")) {
                vfrac[i] = mfrac[i] / SGNA2SO4;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"anhydrite")) {
                vfrac[i] = mfrac[i] / SGANHYDRITE;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"bassanite")) {
                vfrac[i] = mfrac[i] / SGHEMIHYD;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"gypsum")) {
                vfrac[i] = mfrac[i] / SGGYPSUM;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"calcite")) {
                vfrac[i] = mfrac[i] / SGLIMESTONE;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"lime")) {
                vfrac[i] = mfrac[i] / SGLIME;
                totvol += vfrac[i];
                imax = i;
                i++;
            } else if (!strcmp(buff1,"quartz")) {
                vfrac[i] = mfrac[i] / SGQUARTZ;
                totvol += vfrac[i];
                imax = i;
                i++;
            }
        }
    }

    fclose(infile);

    for (i = 0; i <= imax; i++) {
        vfrac[i] *= (100.0 / totvol);
    }

	if ((infile = fopen(argv[1],"r")) == NULL) {
		printf("\n\nCould not open input file %s.  Exiting.\n\n",argv[1]);
		exit(1);
	}

    fprintf(fpout,"PHASE         MASS %%        VOLUME %%\n");
    fprintf(fpout,"-----         ------        --------\n");
	fscanf(infile,"%s %s",buff1,buff);
    for (i = 0; i <= imax; i++) {
       fscanf(infile,"%s %s",buff1,buff);
       if (!strcmp(buff1,"alite")) {
           fprintf(fpout,"C3S           %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"belite")) {
           fprintf(fpout,"C2S           %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"alpha-c2s")) {
           fprintf(fpout,"C2S-alpha     %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"ferrite")) {
           fprintf(fpout,"C4AF          %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"alum-c")) {
           fprintf(fpout,"C3A-cubic     %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"alum-o")) {
           fprintf(fpout,"C3A-orth.     %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"periclase")) {
           fprintf(fpout,"Mg/Ca         %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"arcanite")) {
           fprintf(fpout,"K2SO4         %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"langbeinite")) {
           fprintf(fpout,"Langbeinite   %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"thenardite")) {
           fprintf(fpout,"Na2SO4        %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"anhydrite")) {
           fprintf(fpout,"Anhydrite     %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"bassanite")) {
           fprintf(fpout,"Hemihydrate   %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"gypsum")) {
           fprintf(fpout,"Gypsum        %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"calcite")) {
           fprintf(fpout,"CaCO3         %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"lime")) {
           fprintf(fpout,"Lime          %7f          %7f\n",mfrac[i],vfrac[i]);
        } else if (!strcmp(buff1,"quartz")) {
           fprintf(fpout,"Quartz        %7f          %7f\n",mfrac[i],vfrac[i]);
        }
    }
    fclose(fpout);
    fclose(infile);
    exit(0);
}
