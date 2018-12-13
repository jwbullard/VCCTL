/***********************************************************
 * Program pnm2stats takes the raw ASCII text file (.pnm)
 * produced by either combineall or by convertImageJ, and
 * computes statistics on clinker components and all solids
 *
 ***********************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "vcctl.h"

#define LPORE 0
#define LC3S 1
#define LC2S 2
#define LC3A 3
#define LC4AF 4
#define LK2SO4 5
#define LNA2SO4 6
#define LGYP 7
#define LFREELIME 8
#define LMGCA 9
#define LKAOLIN 10
#define LSILICA 11
#define LCAS 12
#define LSLAG 13

#define C3S_DEN 3.21
#define C2S_DEN 3.28
#define C3A_DEN 3.03
#define C4AF_DEN 3.73
#define K2SO4_DEN 2.66
#define NA2SO4_DEN 2.68

#define RC3S R_BROWN
#define GC3S G_BROWN
#define BC3S B_BROWN

#define RC2S R_CFBLUE
#define GC2S G_CFBLUE
#define BC2S B_CFBLUE

#define RC3A R_GRAY
#define GC3A G_GRAY
#define BC3A B_GRAY

#define RC4AF R_WHITE
#define GC4AF G_WHITE
#define BC4AF B_WHITE

#define RK2SO4 R_RED
#define GK2SO4 G_RED
#define BK2SO4 B_RED

#define RNA2SO4 255
#define GNA2SO4 192
#define BNA2SO4 0

#define RGYP R_YELLOW
#define GGYP G_YELLOW
#define BGYP B_YELLOW

#define RFREELIME R_LLIME
#define GFREELIME G_LLIME
#define BFREELIME B_LLIME

#define RMGCA R_PLUM
#define GMGCA G_PLUM
#define BMGCA B_PLUM

#define RKAOLIN 255 
#define GKAOLIN 165
#define BKAOLIN 0

#define RSILICA 0
#define GSILICA 255
#define BSILICA 255

#define RCAS 0
#define GCAS 0
#define BCAS 128

#define RSLAG 0
#define GSLAG 100
#define BSLAG 0

#define VOLUME 0
#define AREA 0

int **irect(long int xsize, long int ysize);
void free_irect(int **is);
long int area(int mask);
void genlatex();

int **Img;
long int c3s,c2s,c3a,c4af,k2so4,na2so4,gyp;
long int ac3s,ac2s,ac3a,ac4af,ak2so4,ana2so4;
long int mgca,silica,cas,slag,kaolin,freelime;
long int solid,clink,xsize,ysize,totarea;
float vfc3s,vfc2s,vfc3a,vfc4af,vfk2so4;
float vfna2so4,vfgyp,vfmgca,vfsilica,vfcas,vfslag;
float vfkaolin,vffreelime;
float cfc3s,cfc2s,cfc3a,cfc4af,cfk2so4,cfna2so4;
float afc3s,afc2s,afc3a,afc4af,afk2so4,afna2so4;
float mc3s,mc2s,mc3a,mc4af,mk2so4,mna2so4,mtot;
float mfc3s,mfc2s,mfc3a,mfc4af,mfk2so4,mfna2so4;
char Filert[MAXSTRING];

int main(int argc, char *argv[])
{
    register int i,j;
    int inid,r,g,b;
    char buff[MAXSTRING];
    FILE *fpin,*fmistats;

    if (argc != 2) {
        printf("\n\nUsage: pnm2stats fileroot\n\n");
        exit(1);
    }

    sprintf(buff,"%s.pnm",argv[1]);
    if ((fpin = fopen(buff,"r")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",argv[1]);
        exit(1);
    }

    strcpy(Filert,argv[1]);

    solid = clink = 0;
    c3s = c2s = c3a = c4af = k2so4 = na2so4 = 0;
    gyp = mgca = silica = cas = slag = kaolin = freelime = 0;
    fscanf(fpin,"%s",buff);
    fscanf(fpin,"%ld %ld",&xsize,&ysize);

    Img = irect(xsize,ysize);
    if (Img == NULL) {
        printf("\n\nERROR:  Could not allocate memory for array.\n\n");
        exit(1);
    }

    fscanf(fpin,"%s",buff);
    for (j = 0; j < ysize; j++) {
        for (i = 0; i < xsize; i++) {
            fscanf(fpin,"%d %d %d",&r,&g,&b);
            if (r == RC3S && g == GC3S && b == BC3S) Img[i][j] = LC3S;
            else if (r == RC2S && g == GC2S && b == BC2S) Img[i][j] = LC2S;
            else if (r == RC3A && g == GC3A && b == BC3A) Img[i][j] = LC3A;
            else if (r == RC4AF && g == GC4AF && b == BC4AF) Img[i][j] = LC4AF;
            else if (r == RK2SO4 && g == GK2SO4 && b == BK2SO4) Img[i][j] = LK2SO4;
            else if (r == RNA2SO4 && g == GNA2SO4 && b == BNA2SO4) Img[i][j] = LNA2SO4;
            else if (r == RGYP && g == GGYP && b == BGYP) Img[i][j] = LGYP;
            else if (r == RFREELIME && g == GFREELIME && b == BFREELIME) Img[i][j] = LFREELIME;
            else if (r == RMGCA && g == GMGCA && b == BMGCA) Img[i][j] = LMGCA;
            else if (r == RKAOLIN && g == GKAOLIN && b == BKAOLIN) Img[i][j] = LKAOLIN;
            else if (r == RSILICA && g == GSILICA && b == BSILICA) Img[i][j] = LSILICA;
            else if (r == RCAS && g == GCAS && b == BCAS) Img[i][j] = LCAS;
            else if (r == RSLAG && g == GSLAG && b == BSLAG) Img[i][j] = LSLAG;
            else Img[i][j] = LPORE;
        }
    }
    fclose(fpin);

    for (j = 0; j < ysize; j++) {
        for (i = 0; i < xsize; i++) {
            inid = Img[i][j];
            switch (inid) {
                case LC3S:
                    c3s++;
                    clink++;
                    solid++;
                    break;
                case LC2S:
                    c2s++;
                    clink++;
                    solid++;
                    break;
                case LC3A:
                    c3a++;
                    clink++;
                    solid++;
                    break;
                case LC4AF:
                    c4af++;
                    clink++;
                    solid++;
                    break;
                case LK2SO4:
                    k2so4++;
                    clink++;
                    solid++;
                    break;
                case LNA2SO4:
                    na2so4++;
                    clink++;
                    solid++;
                    break;
                case LGYP:
                    gyp++;
                    solid++;
                    break;
                case LFREELIME:
                    freelime++;
                    solid++;
                    break;
                case LMGCA:
                    mgca++;
                    solid++;
                    break;
                case LKAOLIN:
                    kaolin++;
                    solid++;
                    break;
                case LCAS:
                    cas++;
                    solid++;
                    break;
                case LSILICA:
                    silica++;
                    solid++;
                    break;
                case LSLAG:
                    slag++;
                    solid++;
                    break;
                default:
                    break;
            }
        }
    }

    ac3s = area(LC3S);
    ac2s = area(LC2S);
    ac3a = area(LC3A);
    ac4af = area(LC4AF);
    ak2so4 = area(LK2SO4);
    ana2so4 = area(LNA2SO4);

    totarea = ac3s + ac2s + ac3a + ac4af + ak2so4 + ana2so4;
    afc3s = ((float)ac3s)/((float)totarea);
    afc2s = ((float)ac2s)/((float)totarea);
    afc3a = ((float)ac3a)/((float)totarea);
    afc4af = ((float)ac4af)/((float)totarea);
    afk2so4 = ((float)ak2so4)/((float)totarea);
    afna2so4 = ((float)ana2so4)/((float)totarea);

	mc3s = c3s * C3S_DEN;
	mc2s = c2s * C2S_DEN;
	mc3a = c3a * C3A_DEN;
	mc4af = c4af * C4AF_DEN;
	mk2so4 = k2so4 * K2SO4_DEN;
	mna2so4 = na2so4 * NA2SO4_DEN;

	mtot = mc3s + mc2s + mc3a + mc4af + mk2so4 + mna2so4;

	mfc3s = mc3s / mtot;
	mfc2s = mc2s / mtot;
	mfc3a = mc3a / mtot;
	mfc4af = mc4af / mtot;
	mfk2so4 = mk2so4 / mtot;
	mfna2so4 = mna2so4 / mtot;

    vfc3s = ((float)c3s) / ((float)solid);
    cfc3s = ((float)c3s) / ((float)clink);
    vfc2s = ((float)c2s) / ((float)solid);
    cfc2s = ((float)c2s) / ((float)clink);
    vfc3a = ((float)c3a) / ((float)solid);
    cfc3a = ((float)c3a) / ((float)clink);
    vfc4af = ((float)c4af) / ((float)solid);
    cfc4af = ((float)c4af) / ((float)clink);
    vfk2so4 = ((float)k2so4) / ((float)solid);
    cfk2so4 = ((float)k2so4) / ((float)clink);
    vfna2so4 = ((float)na2so4) / ((float)solid);
    cfna2so4 = ((float)na2so4) / ((float)clink);

    vfgyp = ((float)gyp) / ((float)solid);
    vffreelime = ((float)freelime) / ((float)solid);
    vfmgca = ((float)mgca) / ((float)solid);
    vfkaolin = ((float)kaolin) / ((float)solid);
    vfcas = ((float)cas) / ((float)solid);
    vfsilica = ((float)silica) / ((float)solid);
    vfslag = ((float)slag) / ((float)solid);

    if ((fmistats = fopen("averages.dat","a+")) == NULL) {
        printf("\nCannot open file for appending.");
        return(1);
    }
    fprintf(fmistats,"%6.4f c3s\n",vfc3s);
    fprintf(fmistats,"%6.4f c2s\n",vfc2s);
    fprintf(fmistats,"%6.4f c3a\n",vfc3a);
    fprintf(fmistats,"%6.4f c4af\n",vfc4af);
    fprintf(fmistats,"%6.4f gyp\n",vfgyp);
    fprintf(fmistats,"%6.4f lime\n",vffreelime);
    fprintf(fmistats,"%6.4f kaolin\n",vfkaolin);
    fprintf(fmistats,"%6.4f slag\n",vfslag);
    fprintf(fmistats,"%6.4f potsulf\n",vfk2so4);
    fprintf(fmistats,"%6.4f sodsulf\n",vfna2so4);
    fprintf(fmistats,"%6.4f mgca\n",vfmgca);
    fprintf(fmistats,"%6.4f silica\n",vfsilica);
    if (cas > 0) fprintf(fmistats,"%6.4f cas\n",vfcas);
    fprintf(fmistats,"%6.4f c3svol\n",cfc3s);
    fprintf(fmistats,"%6.4f c2svol\n",cfc2s);
    fprintf(fmistats,"%6.4f c3avol\n",cfc3a);
    fprintf(fmistats,"%6.4f c4afvol\n",cfc4af);
    fprintf(fmistats,"%6.4f k2so4vol\n",cfk2so4);
    fprintf(fmistats,"%6.4f na2so4vol\n",cfna2so4);
    fprintf(fmistats,"%6.4f c3ssurf\n",afc3s);
    fprintf(fmistats,"%6.4f c2ssurf\n",afc2s);
    fprintf(fmistats,"%6.4f c3asurf\n",afc3a);
    fprintf(fmistats,"%6.4f c4afsurf\n",afc4af);
    fprintf(fmistats,"%6.4f k2so4surf\n",afk2so4);
    fprintf(fmistats,"%6.4f na2so4surf\n",afna2so4);
    fprintf(fmistats,"%6.4f c3smass\n",mfc3s);
    fprintf(fmistats,"%6.4f c2smass\n",mfc2s);
    fprintf(fmistats,"%6.4f c3amass\n",mfc3a);
    fprintf(fmistats,"%6.4f c4afmass\n",mfc4af);
    fprintf(fmistats,"%6.4f k2so4mass\n",mfk2so4);
    fprintf(fmistats,"%6.4f na2so4mass\n",mfna2so4);
    fprintf(fmistats,"***************\n");
    fclose(fmistats);

    genlatex();
    free_irect(Img);

    exit(0);
}

long int area(int mask)
{
	register int i,j;
	long int edgesum;

	edgesum = 0;
	for (i = 1; i < (xsize - 1); i++) {
		for (j = 1; j < (ysize - 1); j++) {

			if(Img[i][j] == mask) {

				/* Check immediate 4 neighbors for edges */

				if (((Img[i-1][j])) == LPORE) {
					edgesum++;
				}

				if (((Img[i+1][j])) == LPORE) {
					edgesum++;
				}

				if (((Img[i][j-1])) == LPORE) {
					edgesum++;
				}

				if(((Img[i][j+1])) == LPORE) {
					edgesum++;
				}
			}

		}
	}

    return(edgesum);
}

void genlatex()
{
	register int i;
	char filename[MAXSTRING],cmdnew[MAXSTRING];
	FILE *flatex,*scrfile,*mkf;

	i = 0;
	while (i < strlen(Filert)) {
		if (Filert[i] == 95) {
			Filert[i] = 45;
		}
		i++;
	}

	sprintf(filename,"%s.tex",Filert);
	if ((flatex = fopen(filename,"w")) == NULL) {
		printf("\n\nCould not open latex file for writing\n\n");
		return;
	}
	
	fprintf(flatex,"\\documentclass{article}\n");
	fprintf(flatex,"\\begin{document}\n");
	fprintf(flatex,"\\begin{center}\n");
	fprintf(flatex,"{\\large{Phase fractions for {\\bf %s}}}\n",Filert);
	fprintf(flatex,"\\end{center}\n");
	fprintf(flatex,"\n\\vspace{0.125in}\n");
	fprintf(flatex,"\\begin{center}\n");
	fprintf(flatex,"\\begin{tabular}{r l r l} \\\\ \n");
	fprintf(flatex,"C$_3$S = & %6.4f & Kaolin = & %6.4f \\\\ \n",vfc3s,vfkaolin);
	fprintf(flatex,"C$_2$S = & %6.4f & Slag = & %6.4f \\\\ \n",vfc2s,vfslag);
	fprintf(flatex,"C$_3$A = & %6.4f & Potassium Sulf = & %6.4f \\\\ \n",vfc3a,vfk2so4);
	fprintf(flatex,"C$_4$AF = & %6.4f & Sodium Sulf = & %6.4f \\\\ \n",vfc4af,vfna2so4);
	fprintf(flatex,"Gypsum = & %6.4f & SiO$_2$ = & %6.4f \\\\ \n",vfgyp,vfsilica);
	if (cas > 0) {
        fprintf(flatex,"Free Lime = & %6.4f & CAS$_2$ = & %6.4f \\\\ \n",vffreelime,vfcas);
	    fprintf(flatex,"Mg/Ca = & %6.4f & & \n",vfmgca);
    } else {
	    fprintf(flatex,"Free Lime = & %6.4f & Mg/Ca = & %6.4f \n",vffreelime,vfmgca);
    }
	fprintf(flatex,"\\end{tabular}\n");
	fprintf(flatex,"\\end{center}\n\n");

	fprintf(flatex,"\\vspace{0.25in}\n");
	fprintf(flatex,"\\begin{center}\n");
	fprintf(flatex,"{\\large{Clinker fractions for {\\bf %s}}}\n",Filert);
	fprintf(flatex,"\\end{center}\n");
	fprintf(flatex,"\n\\vspace{0.125in}\n");
	fprintf(flatex,"\\begin{tabular}{c|c|c|c} \\\\ \n");
	fprintf(flatex,"{\\bf Phase} & {\\bf Volume Fraction} & ");
	fprintf(flatex,"{\\bf Area Fraction} & {\\bf Mass Fraction} ");
	fprintf(flatex,"\\\\ \\hline\n");
	fprintf(flatex,"C$_3$S & %6.4f & %6.4f & %6.4f \\\\ \n",cfc3s,afc3s,mfc3s);
	fprintf(flatex,"C$_2$S & %6.4f & %6.4f & %6.4f \\\\ \n",cfc2s,afc2s,mfc2s);
	fprintf(flatex,"C$_3$A & %6.4f & %6.4f & %6.4f \\\\ \n",cfc3a,afc3a,mfc3a);
	fprintf(flatex,"C$_4$AF & %6.4f & %6.4f & %6.4f \\\\ \n",cfc4af,afc4af,mfc4af);
	fprintf(flatex,"K$_2$SO$_4$ & %6.4f & %6.4f & %6.4f \\\\ \n",cfk2so4,afk2so4,mfk2so4);
	fprintf(flatex,"Na$_2$SO$_4$ & %6.4f & %6.4f & %6.4f \\\\ \n",cfna2so4,afna2so4,mfna2so4);
	fprintf(flatex,"\\end{tabular}\n\n");
	fprintf(flatex,"\\end{document}");
	fclose(flatex);
	
	if ((mkf = fopen("Makefile","w")) == NULL) {
		printf("\n\nCannot open Makefile \n\n");
		return;
	}

	fprintf(mkf,"all:\t%s clean\n",Filert);
	fprintf(mkf,"%s:\t%s.tex\n",Filert,Filert);
	fprintf(mkf,"\tpdflatex %s; pdflatex %s\n",Filert,Filert);
	fprintf(mkf,"clean:\n");
	fprintf(mkf,"\t/bin/rm -f *.aux *.out *.log\n");
	fclose(mkf);
	
	if ((scrfile = fopen("mtex.scr","w")) == NULL) {
		printf("\n\nCannot open mtex.scr file \n\n");
		return;
	}

	fprintf(scrfile,"make all >& makelog\n");
	fprintf(scrfile,"open %s.pdf &\n",Filert);
	fclose(scrfile);
	system("chmod 777 mtex.scr");
	
	sprintf(cmdnew,"bash ./mtex.scr &");
	system(cmdnew);

	return;
	
}

