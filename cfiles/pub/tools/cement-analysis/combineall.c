#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#include <time.h>
#include "vcctl.h"

#define CA 0
#define SI 1
#define AL 2
#define FE 3
#define S 4
#define K 5
#define NA 6
#define MG 7

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

#define ISIZE 512

#define VOLUME	0
#define AREA	1

#define PNM 0
#define RAS 1

#define C3S_DEN		3.21
#define C2S_DEN		3.28
#define C3A_DEN		3.03
#define C4AF_DEN	3.73
#define K2SO4_DEN	2.66
#define NA2SO4_DEN	2.68

const int PORTCEM=0;
const int BLEND=1;

short int ***image,**imgact,**imgproc;
int **Img;
long int Czero;
long int Cnc3s,Cnc2s,Cnc3a,Cnc4af,Cnac3s,Cnac2s,Cnac3a,Cnac4af;
long int Cnk2so4,Cnna2so4,Cnak2so4,Cnana2so4;
float Cvfc3s,Cvfc2s,Cvfc3a,Cvfc4af,Cvfk2so4,Cvfna2so4;
float Cafc3s,Cafc2s,Cafc3a,Cafc4af,Cafk2so4,Cafna2so4;
float Cmfc3s,Cmfc2s,Cmfc3a,Cmfc4af,Cmfk2so4,Cmfna2so4;
long int phcount[SLAG+1];
int xsize,ysize,Cemtype;
int nmgca,nc3s,nc2s,nc3a,nc4af,ngyp,nlime,npotsulf,nkaolin,nsilica,nslag,nsodsulf,ncas;
char Filert[MAXSTRING],Filext[MAXSTRING];
void segngh(int ix, int iy, int extent);
void median(void);
void median1(void);
void bkfill(void);
void bkfill1(void);
int countngh(int ix, int iy);
void onegone(void);
long int statsimp(int bit,int type);

void vol2mass(void);
void genlatex(float fc3s, float fc2s, float fc3a, float fc4af,
	float fgyp, float flime, float fkaolin, float fslag, float fks,
	float fnas, float fmgca, float fsilica, float fcas);

int main(void)
{
	int nskip,i,ix,iy,ival;
	int thresh;
	int thr[MG+1],thrcao,thrsio;
	int fval,maxval,extype;
	float valsi,valca,ratiocasi,fval1;
	long int totcnt,hist[256];
	FILE *infile,*outfile;
	char blend[3],valin,elem[MG+1][10],filenow[MAXSTRING],fileout[MAXSTRING],buff[MAXSTRING];

	image = NULL;
	imgact = NULL;
	imgproc = NULL;
	Img = NULL;

	totcnt=0;
	for(i=0;i<=LSLAG;i++){
		phcount[i]=0;
	}

	sprintf(elem[0],"ca");
	sprintf(elem[1],"si");
	sprintf(elem[2],"al");
	sprintf(elem[3],"fe");
	sprintf(elem[4],"s");
	sprintf(elem[5],"k");
	sprintf(elem[6],"na");
	sprintf(elem[7],"mg");
	printf("Enter file root for processing: ");
	read_string(Filert,sizeof(Filert));
	printf("\n%s\n",Filert);
    do {
	    printf("Enter extension of graphics file(pnm,ppm,ras): ");
	    read_string(Filext,sizeof(Filext));
	    printf("\n%s\n",Filext);
    } while (strcmp(Filext,"pnm") && strcmp(Filext,"ppm") && strcmp(Filext,"ras"));

    Cemtype = PORTCEM;
    printf("Fly Ash present (Y or N)? [N]");
    read_string(blend,sizeof(blend));
    if (toupper(blend[0]) == 'Y') Cemtype = BLEND;
            
    if (!strcmp(Filext,"pnm") || !strcmp(Filext,"ppm")) {
        extype = PNM;
        nskip = 0;
    } else {
        extype = RAS;
        printf("Enter number of pixels to skip at start: ");
        read_string(buff,sizeof(buff));
        nskip = atoi(buff);
        printf("\n%d\n",nskip);
    }

	/* Read in all starting images */
	for(i=0;i<=MG;i++){
		printf("Enter threshold value for element %s (0-255) \n",elem[i]);
		read_string(buff,sizeof(buff));
        thresh = atoi(buff);
		printf("%d\n",thresh);
		thr[i]=thresh;
		sprintf(filenow,"%s%s.%s",Filert,elem[i],Filext);
		sprintf(fileout,"%s%s.hst",Filert,elem[i]);
		printf("%s\n",filenow);
		infile=fopen(filenow,"rb");
		outfile=fopen(fileout,"w");
		for(ix=0;ix<256;ix++){
			hist[ix]=0;
		}
        for (ix=0;ix<nskip;ix++) {
            fscanf(infile,"%c",&valin);
        }

        switch (extype) {

            case PNM:
		        fscanf(infile,"%s",buff);
		        fscanf(infile,"%d %d",&ix,&iy);

		        if (i == 0) {
			        xsize = ix;
			        ysize = iy;
                } else if (ix != xsize || iy != ysize) {
			        printf("\nERROR: Image size mismatch.  Exiting\n\n");
                    free_sirect(imgproc);
                    free_sirect(imgact);
                    free_sibox(image);
                    free_irect(Img);
			        exit(1);
                }
		        fscanf(infile,"%d",&maxval);
                break;

            case RAS:
                if (i == 0) {
                    printf("Input x size\n");
                    read_string(buff,sizeof(buff));
                    xsize = atoi(buff);
                    printf("Input y size\n");
                    read_string(buff,sizeof(buff));
                    ysize = atoi(buff);
                    printf("%d  %d \n",xsize,ysize);
                    Cemtype = PORTCEM;
                    printf("Fly Ash present (Y or N)? [N]");
                    read_string(blend,sizeof(blend));
                    if (toupper(blend[0]) == 'Y') Cemtype = BLEND;
                }
                break;

            default:
                break;
        }
	

        if (i == 0) {

            /***
            *	Allocate memory for arrays based on xsize and ysize
            ***/

            image = sibox((long int)(xsize+1),(long int)ysize,(long int)(MG+1));
            if (!image) {
                printf("\nERROR allocating memory for array called image.  Exiting.");
                exit(1);
            }
            imgact = sirect((long int)(xsize+1),(long int)ysize);
            if (!imgact) {
                printf("\nERROR allocating memory for array called imgact.  Exiting.");
                free_sibox(image);
                exit(1);
            }
            imgproc = sirect((long int)(xsize+1),(long int)ysize);
            if (!imgproc) {
                printf("\nERROR allocating memory for array called imgproc.  Exiting.");
                free_sirect(imgact);
                free_sibox(image);
                exit(1);
            }
            Img = irect((long int)(xsize),(long int)(xsize));
            if (!Img) {
                printf("\nERROR allocating memory for array called Img.  Exiting.");
                free_sirect(imgproc);
                free_sirect(imgact);
                free_sibox(image);
                exit(1);
            }
		}

		for(iy=0;iy<ysize;iy++){
		for(ix=0;ix<xsize;ix++){
			fscanf(infile,"%c",&valin);
			ival=valin;
			if(ival<0){ival+=256;}
			hist[ival]+=1;
			image[ix][iy][i]=ival;
		}
		}
		for(ix=0;ix<256;ix++){
			fprintf(outfile,"%d %ld \n",ix,hist[ix]);
		}
		fclose(infile);    
		fclose(outfile);    
	}
	/* Now create the histogram file for the Ca/Si ratio */
	/* cementcasi.hst for example */
		for(ix=0;ix<256;ix++){
			hist[ix]=0;
		}
		for(iy=0;iy<ysize;iy++){
		for(ix=0;ix<xsize;ix++){
			if((image[ix][iy][CA]>=thr[CA])&&(image[ix][iy][SI]>=thr[SI])&&(image[ix][iy][AL]<thr[AL])){
				fval1=50.*(float)image[ix][iy][CA]/(float)image[ix][iy][SI];
				ival=(int)fval1;
				if(ival>255){ival=255;}
				hist[ival]+=1;
			}
		}
		}

	/* Now output the Ca/Si historgram file */
		sprintf(fileout,"%scasi.hst",Filert);
		outfile=fopen(fileout,"w");
		for(ix=0;ix<256;ix++){
			fprintf(outfile,"%f %ld \n",(float)ix/50.,hist[ix]);
		}
		fclose(outfile);

	printf("Enter threshold value for element free lime \n");
    read_string(buff,sizeof(buff));
    thresh = atoi(buff);
	printf("%d\n",thresh);
	thrcao=thresh;
	printf("Enter threshold value for silica \n");
    read_string(buff,sizeof(buff));
    thresh = atoi(buff);
	printf("%d\n",thresh);
	thrsio=thresh;
	printf("Enter critical ratio for C3S vs. C2S \n");
    read_string(buff,sizeof(buff));
    ratiocasi = atof(buff);
	printf("%f\n",ratiocasi);

        /* Set the initial phase assignments in the resultant image */
        /* Process each pixel in the 2-D image in turn */
	for(iy=0;iy<ysize;iy++){
	for(ix=0;ix<xsize;ix++){
		totcnt+=1;
		fval=(-100);
                /* traverse the decision tree */
		if(image[ix][iy][CA]>thr[CA]){
			if(image[ix][iy][AL]>thr[AL]){
				if(image[ix][iy][FE]>thr[FE]){
					fval=LC4AF;
					phcount[LC4AF]++;
				} else {
					if((image[ix][iy][SI]>thr[SI])) {
                        if (image[ix][iy][MG]>thr[MG]) {
						    fval=LSLAG;
						    phcount[LSLAG]++;
                        } else if (Cemtype == BLEND) {
                            fval = LCAS;
                            phcount[LCAS]++;
                        }
					} else {
						fval=LC3A;
						phcount[LC3A]+=1;
                    }
				}
			} else if(image[ix][iy][SI]>thr[SI]) {
				if(image[ix][iy][MG]>thr[MG]){
					fval=LSLAG;
					phcount[LSLAG]+=1;
				} else {
					valsi=(float)(image[ix][iy][SI]);
					valca=(float)(image[ix][iy][CA]);
					if((valca/valsi)>ratiocasi){
						fval=LC3S;
						phcount[LC3S]+=1;
					} else {
					    fval=LC2S;
					    phcount[LC2S]+=1;
					}
				}
			} else if(image[ix][iy][S]>thr[S]) {
				fval=LGYP;
				phcount[LGYP]+=1;
			}
			else if(image[ix][iy][MG]>thr[MG]){
				fval=LMGCA;
				phcount[LMGCA]+=1;
			}
			else if(image[ix][iy][CA]>thrcao){
				fval=LFREELIME;
				phcount[LFREELIME]+=1;
			}
		}
		else if(image[ix][iy][MG]>thr[MG]){
			if((image[ix][iy][SI]>thr[SI])&&(image[ix][iy][AL]>thr[AL])){
				fval=LSLAG;
				phcount[LSLAG]+=1;
			}
			else{
				fval=LMGCA;
				phcount[LMGCA]+=1;
			}
		}
		else if(image[ix][iy][S]>thr[S]){
			if(image[ix][iy][K]>thr[K]){
				fval=LK2SO4;
				phcount[LK2SO4]+=1;
			} else if(image[ix][iy][NA]>thr[NA]) {
				fval = LNA2SO4;
				phcount[LNA2SO4]+=1;
			} else {
				fval=LGYP;
				phcount[LGYP]+=1;
			}
		}
		else if(image[ix][iy][SI]>thr[SI]){
			if(image[ix][iy][AL]>((int)(1.5*(float)thr[AL]))){
				fval=LKAOLIN;
				phcount[LKAOLIN]+=1;
			}
			else if(image[ix][iy][SI]>thrsio){
				fval=LSILICA;
				phcount[LSILICA]+=1;
			}
                        else if(image[ix][iy][AL]>thr[AL]){
				fval=LKAOLIN;
				phcount[LKAOLIN]+=1;
			}
		}
			
		imgact[ix][iy]=fval;
		if(fval<0){imgact[ix][iy]=0;}
	}
	}

	printf("Input any integer to continue \n");
	scanf("%d",&i);
    read_string(buff,sizeof(buff));
    i = atoi(buff);
        /* Remove the one-pixel particles */
	onegone();
        /* Fill in the one-pixel voids in two passes of the filling algorithm */
	bkfill();
	bkfill1();
	printf("Input any integer to continue \n");
    read_string(buff,sizeof(buff));
    i = atoi(buff);
        /* Perform two iterations of the median filtering algorthm */
	median(); 
	median1(); 

	/* Free dynamically allocated memory */

	free_irect(Img);
	free_sirect(imgproc);
	free_sirect(imgact);
	free_sibox(image);

	exit(0);
}

/* Routine to count neighboring pixels in an extent * extent square */
/* centered at each pixel in microstructure */
void segngh(int ix, int iy, int extent)
{
	int ix1,iy1;
	int pin;

	for(ix1=(ix-extent);ix1<=(ix+extent);ix1++){
	for(iy1=(iy-extent);iy1<=(iy+extent);iy1++){

	if((ix1>=0)&&(ix1<xsize)&&(iy1>=0)&&(iy1<ysize)){
		pin=imgact[ix1][iy1];

		if(pin==LC3S){
			nc3s+=1;
		}
		else if(pin==LC2S){
			nc2s+=1;
		}
		else if(pin==LC3A){
			nc3a+=1;
		}
		else if(pin==LC4AF){
			nc4af+=1;
		}
		else if(pin==LGYP){
			ngyp+=1;
		}
		else if(pin==LFREELIME){
			nlime+=1;
		}
		else if(pin==LK2SO4){
			npotsulf+=1;
		}
		else if(pin==LNA2SO4){
			nsodsulf+=1;
		}
		else if(pin==LKAOLIN){
			nkaolin+=1;
		}
		else if(pin==LSILICA){
			nsilica+=1;
		}
		else if(pin==LCAS){
			ncas+=1;
		}
		else if(pin==LSLAG){
			nslag+=1;
		}
		else if(pin==LMGCA){
			nmgca+=1;
		}
	}

	}
	}
}
/* Routine to execute a median filter on the 2-D image */	
void median(void)
{
	int i,j,totngh;
	float maxfrac,pblack,fc3s,fc2s,fc3a,fc4af,fgyp;
	float flime,fks,fmgca,fkaolin,fsilica,fslag,fcas,fnas;
	int color,pixin,colorm;
	long int cblack,cwhite,cc3s,cc2s,cc3a,cc4af,cgyp,ctot;
	long int clime,cks,cmgca,ckaolin,csilica,cslag,ccas,cnas;

        /* Initialize counters */
	cc3s=cc2s=cmgca=ckaolin=cc3a=cnas=ccas=0;
	cc4af=cgyp=cwhite=cblack=clime=cks=csilica=cslag=0;

        /* Now process each pixel in the 2-D microstructure */
	for(i=0;i<xsize;i++){
	for(j=0;j<ysize;j++){

		pixin=imgact[i][j];
                /* Determine the phase of the current pixel */
		color=LPORE;
		if(pixin==LC3S){
			color=LC3S;
		}
		else if(pixin==LC2S){
			color=LC2S;
		}
		else if(pixin==LC3A){
			color=LC3A;
		}
		else if(pixin==LK2SO4){
			color=LK2SO4;
		}
		else if(pixin==LNA2SO4){
			color=LNA2SO4;
		}
		else if(pixin==LMGCA){
			color=LMGCA;
		}
		else if(pixin==LKAOLIN){
			color=LKAOLIN;
		}
		else if(pixin==LFREELIME){
			color=LFREELIME;
		}
		else if(pixin==LC4AF){
			color=LC4AF;
		}
		else if(pixin==LSILICA){
			color=LSILICA;
		}
		else if(pixin==LCAS){
			color=LCAS;
		}
		else if(pixin==LSLAG){
			color=LSLAG;
		}
		else if(pixin==LGYP){
			color=LGYP;
		}

        /* If the pixel is solid, may need to perform the median filter there */
	if(pixin!=LPORE){
        /* Count the number of solid neighbors */
	nc3s=nc2s=nc3a=nc4af=ngyp=nmgca=nkaolin=nlime=npotsulf=nsodsulf=nsilica=nslag=ncas=0;
	nsodsulf=0;
	segngh(i,j,2);
	totngh=nc3s+nc2s+nc3a+nc4af+nmgca+ngyp+nkaolin+nlime+npotsulf+nsodsulf+nsilica+nslag;
        /* If there are neighboring solid pixels, perform the median filter */
	if(totngh>1){
		nc3s=nc2s=nc3a=nc4af=ngyp=nmgca=nlime=nkaolin=npotsulf=nsilica=ncas=0;
		nslag=nsodsulf=0;
		segngh(i,j,3);
		totngh=nc3s+nc2s+nc3a+nc4af+nmgca+ngyp+nlime+nkaolin+npotsulf+nsodsulf+nsilica+nslag+ncas;
		if(totngh>0){
                /* Determine the most probable phase in the immediate neighborhood */
		maxfrac=(float)nc3s/(float)totngh;
		colorm=LC3S;
		if(maxfrac<(float)nc2s/(float)totngh){
			maxfrac=(float)nc2s/(float)totngh;
			colorm=LC2S;
		}
		if(maxfrac<(float)nc3a/(float)totngh){
			maxfrac=(float)nc3a/(float)totngh;
			colorm=LC3A;
		}
		if(maxfrac<(float)nc4af/(float)totngh){
			maxfrac=(float)nc4af/(float)totngh;
			colorm=LC4AF;
		}
		if(maxfrac<(float)ngyp/(float)totngh){
			maxfrac=(float)ngyp/(float)totngh;
			colorm=LGYP;
		}
		if(maxfrac<(float)nlime/(float)totngh){
			maxfrac=(float)nlime/(float)totngh;
			colorm=LFREELIME;
		}
		if(maxfrac<(float)npotsulf/(float)totngh){
			maxfrac=(float)npotsulf/(float)totngh;
			colorm=LK2SO4;
		}
		if(maxfrac<(float)nsodsulf/(float)totngh){
			maxfrac=(float)nsodsulf/(float)totngh;
			colorm=LNA2SO4;
		}
		if(maxfrac<(float)nkaolin/(float)totngh){
			maxfrac=(float)nkaolin/(float)totngh;
			colorm=LKAOLIN;
		}
		if(maxfrac<(float)nsilica/(float)totngh){
			maxfrac=(float)nsilica/(float)totngh;
			colorm=LSILICA;
		}
		if(maxfrac<(float)ncas/(float)totngh){
			maxfrac=(float)ncas/(float)totngh;
			colorm=LCAS;
		}
		if(maxfrac<(float)nslag/(float)totngh){
			maxfrac=(float)nslag/(float)totngh;
			colorm=LSLAG;
		}
		if(maxfrac<(float)nmgca/(float)totngh){
			maxfrac=(float)nmgca/(float)totngh;
			colorm=LMGCA;
		}

               /* Rules for updating the pixel being examined */
		if((color!=LPORE)&&(maxfrac>=0.8)&&(totngh>=5)){
			color=colorm;
		}
		if((color!=LPORE)&&(color!=LK2SO4)&&(color!=LNA2SO4)
			&&(maxfrac>=0.6)&&(totngh>=5)){
			color=colorm;
		}
		if((color==LC2S)&&(maxfrac>=0.5)&&(totngh>=5)){
			color=colorm;
		}
		if((color==LFREELIME)&&(maxfrac>=0.25)&&(totngh>=4)){
			color=colorm;
		}
		if((color==LMGCA)&&(maxfrac>=0.5)&&(totngh>=4)){
			color=colorm;
		}
		if((color==LMGCA)&&(colorm==C3S)&&(maxfrac>=0.3)&&(totngh>=4)){
			color=colorm;
		}
		imgproc[i][j]=color;
		}

                /* Tabulate the new phase counts */
		if(color==LPORE){
			cblack+=1;
		}
		else if(color==LC3S){
			cc3s+=1;
		}
		else if(color==LC2S){
			cc2s+=1;
		}
		else if(color==LC3A){
			cc3a+=1;
		}
		else if(color==LC4AF){
			cc4af+=1;
		}
		else if(color==LGYP){
			cgyp+=1;
		}
		else if(color==LFREELIME){
			clime+=1;
		}
		else if(color==LK2SO4){
			cks+=1;
		}
		else if(color==LNA2SO4){
			cnas+=1;
		}
		else if(color==LKAOLIN){
			ckaolin+=1;
		}
		else if(color==LSILICA){
			csilica+=1;
		}
		else if(color==LCAS){
			ccas+=1;
		}
		else if(color==LSLAG){
			cslag+=1;
		}
		else if(color==LMGCA){
			cmgca+=1;
		}
	}
	}

	}
	}

        /* Output the new phase fractions to the user */
	ctot=cc3s+cc2s+cmgca+cc3a+cc4af+cgyp+cks+cnas+clime+ckaolin+csilica+cslag+ccas;
	pblack=(float)cblack/(float)(ctot+cblack);
	fc3s=(float)cc3s/(float)ctot;
	fc2s=(float)cc2s/(float)ctot;
	fks=(float)cks/(float)ctot;
	fnas=(float)cnas/(float)ctot;
	fmgca=(float)cmgca/(float)ctot;
	fc3a=(float)cc3a/(float)ctot;
	fgyp=(float)cgyp/(float)ctot;
	flime=(float)clime/(float)ctot;
	fkaolin=(float)ckaolin/(float)ctot;
	fslag=(float)cslag/(float)ctot;
	fcas=(float)ccas/(float)ctot;
	fsilica=(float)csilica/(float)ctot;
	fc4af=(float)cc4af/(float)ctot;

	printf("Fraction pore = %f \n",pblack);
	printf("Fraction C2S = %f \n",fc2s);
	printf("Fraction C3S = %f \n",fc3s);
	printf("Fraction C4AF = %f \n",fc4af);
	printf("Fraction C3A = %f \n",fc3a);
	printf("Fraction gypsum= %f \n",fgyp);
	printf("Fraction Free lime= %f \n",flime);
	printf("Fraction Kaolin= %f \n",fkaolin);
	printf("Fraction Potassium sulfate= %f \n",fks);
	printf("Fraction Sodium sulfate= %f \n",fnas);
	printf("Fraction MgCa phase= %f\n",fmgca);
        printf("Fraction silica = %f\n",fsilica);
        if (Cemtype == BLEND) printf("Fraction CAS = %f\n",fcas);
        printf("Fraction Slag = %f\n",fslag);
	for(j=0;j<ysize;j++){
	for(i=0;i<xsize;i++){
		imgact[i][j]=imgproc[i][j];
	}
	}
}
/* Routine to perform a median filter and output the resultant */
/* microstructure to two image files (one for further analysis and */	
/* one for viewing) */
void median1(void)
{
	int i,j,totngh;
	float maxfrac,pblack,fc3s,fc2s,fc3a,fc4af,fgyp;
	float flime,fks,fnas,fmgca,fkaolin,fsilica,fslag,fcas;
	int color,pixin,colorm;
	long int cblack,cwhite,cc3s,cc2s,cc3a,cc4af,cgyp,ctot,cslag;
	long int clime,cks,cnas,cmgca,ckaolin,csilica,ccas;
	FILE *finfile,*foutfile,*fcolorfile,*fmistats;
	char file1[MAXSTRING],file2[MAXSTRING],file3[MAXSTRING],answer[5],cmdnew[MAXSTRING];

	cc3s=cc2s=cmgca=ckaolin=cc3a=cslag=cnas=0;
	cc4af=cgyp=cwhite=cblack=clime=cks=csilica=ccas=0;

	for(i=0;i<xsize;i++){
	for(j=0;j<ysize;j++){

		pixin=imgact[i][j];
		color=LPORE;
		if(pixin==LC3S){
			color=LC3S;
		}
		else if(pixin==LC2S){
			color=LC2S;
		}
		else if(pixin==LC3A){
			color=LC3A;
		}
		else if(pixin==LK2SO4){
			color=LK2SO4;
		}
		else if(pixin==LNA2SO4){
			color=LNA2SO4;
		}
		else if(pixin==LMGCA){
			color=LMGCA;
		}
		else if(pixin==LKAOLIN){
			color=LKAOLIN;
		}
		else if(pixin==LSILICA){
			color=LSILICA;
		}
		else if(pixin==LCAS){
			color=LCAS;
		}
		else if(pixin==LSLAG){
			color=LSLAG;
		}
		else if(pixin==LFREELIME){
			color=LFREELIME;
		}
		else if(pixin==LC4AF){
			color=LC4AF;
		}
		else if(pixin==LGYP){
			color=LGYP;
		}

	if(pixin!=LPORE){
	nc3s=nc2s=nc3a=nc4af=ngyp=nmgca=nkaolin=nlime=npotsulf=nsilica=ncas=0;
	nslag=nsodsulf=0;
	segngh(i,j,1);
	totngh=nc3s+nc2s+nc3a+nc4af+nmgca+ngyp+nkaolin+nlime+npotsulf+nsodsulf+nsilica+nslag+ncas;
	if(totngh>1){
		nc3s=nc2s=nc3a=nc4af=ngyp=nmgca=nlime=nkaolin=npotsulf=nsilica=ncas=0;
		nslag=nsodsulf=0;
		segngh(i,j,2);
		totngh=nc3s+nc2s+nc3a+nc4af+nmgca+ngyp+nlime+nkaolin+npotsulf+nsodsulf+nsilica+nslag+ncas;
		if(totngh>0){
		maxfrac=(float)nc3s/(float)totngh;
		colorm=LC3S;
		if(maxfrac<(float)nc2s/(float)totngh){
			maxfrac=(float)nc2s/(float)totngh;
			colorm=LC2S;
		}
		if(maxfrac<(float)nc3a/(float)totngh){
			maxfrac=(float)nc3a/(float)totngh;
			colorm=LC3A;
		}
		if(maxfrac<(float)nc4af/(float)totngh){
			maxfrac=(float)nc4af/(float)totngh;
			colorm=LC4AF;
		}
		if(maxfrac<(float)ngyp/(float)totngh){
			maxfrac=(float)ngyp/(float)totngh;
			colorm=LGYP;
		}
		if(maxfrac<(float)nlime/(float)totngh){
			maxfrac=(float)nlime/(float)totngh;
			colorm=LFREELIME;
		}
		if(maxfrac<(float)npotsulf/(float)totngh){
			maxfrac=(float)npotsulf/(float)totngh;
			colorm=LK2SO4;
		}
		if(maxfrac<(float)nsodsulf/(float)totngh){
			maxfrac=(float)nsodsulf/(float)totngh;
			colorm=LNA2SO4;
		}
		if(maxfrac<(float)nkaolin/(float)totngh){
			maxfrac=(float)nkaolin/(float)totngh;
			colorm=LKAOLIN;
		}
		if(maxfrac<(float)nsilica/(float)totngh){
			maxfrac=(float)nsilica/(float)totngh;
			colorm=LSILICA;
		}
		if(maxfrac<(float)ncas/(float)totngh){
			maxfrac=(float)ncas/(float)totngh;
			colorm=LCAS;
		}
		if(maxfrac<(float)nslag/(float)totngh){
			maxfrac=(float)nslag/(float)totngh;
			colorm=LSLAG;
		}
		if(maxfrac<(float)nmgca/(float)totngh){
			maxfrac=(float)nmgca/(float)totngh;
			colorm=LMGCA;
		}
	
		if((color!=LPORE)&&(maxfrac>=0.8)&&(totngh>=5)){
			color=colorm;
		}
		if((color!=LPORE)&&(color!=LK2SO4)&&(color!=LNA2SO4)&&(maxfrac>=0.6)&&(totngh>=5)){
			color=colorm;
		}
		if((color==LC2S)&&(maxfrac>=0.5)&&(totngh>=5)){
			color=colorm;
		}
		if((color==LFREELIME)&&(maxfrac>=0.25)&&(totngh>=4)){
			color=colorm;
		}
		if((color==LMGCA)&&(maxfrac>=0.5)&&(totngh>=4)){
			color=colorm;
		}
		if((color==LMGCA)&&(colorm==C3S)&&(maxfrac>=0.3)&&(totngh>=4)){
			color=colorm;
		}
		imgproc[i][j]=color;
		}

		if(color==LPORE){
			cblack+=1;
		}
		else if(color==LC3S){
			cc3s+=1;
		}
		else if(color==LC2S){
			cc2s+=1;
		}
		else if(color==LC3A){
			cc3a+=1;
		}
		else if(color==LC4AF){
			cc4af+=1;
		}
		else if(color==LGYP){
			cgyp+=1;
		}
		else if(color==LFREELIME){
			clime+=1;
		}
		else if(color==LK2SO4){
			cks+=1;
		}
		else if(color==LNA2SO4){
			cnas+=1;
		}
		else if(color==LKAOLIN){
			ckaolin+=1;
		}
		else if(color==LSILICA){
			csilica+=1;
		}
		else if(color==LCAS){
			ccas+=1;
		}
		else if(color==LSLAG){
			cslag+=1;
		}
		else if(color==LMGCA){
			cmgca+=1;
		}
	}
	}

	}
	}

	ctot=cc3s+cc2s+cmgca+cc3a+cc4af+cgyp+cks+cnas+clime+ckaolin+csilica+cslag+ccas;
	pblack=(float)cblack/(float)(ctot+cblack);
	fc3s=(float)cc3s/(float)ctot;
	fc2s=(float)cc2s/(float)ctot;
	fks=(float)cks/(float)ctot;
	fnas=(float)cnas/(float)ctot;
	fmgca=(float)cmgca/(float)ctot;
	fc3a=(float)cc3a/(float)ctot;
	fgyp=(float)cgyp/(float)ctot;
	flime=(float)clime/(float)ctot;
	fkaolin=(float)ckaolin/(float)ctot;
	fsilica=(float)csilica/(float)ctot;
	fslag=(float)cslag/(float)ctot;
	fcas=(float)ccas/(float)ctot;
	fc4af=(float)cc4af/(float)ctot;

	printf("Fraction pore = %f \n",pblack);
	printf("Fraction C2S = %f \n",fc2s);
	printf("Fraction C3S = %f \n",fc3s);
	printf("Fraction C4AF = %f \n",fc4af);
	printf("Fraction C3A = %f \n",fc3a);
	printf("Fraction gypsum= %f \n",fgyp);
	printf("Fraction Free lime= %f \n",flime);
	printf("Fraction Kaolin= %f \n",fkaolin);
	printf("Fraction Potassium sulfate= %f \n",fks);
	printf("Fraction Sodium sulfate= %f \n",fnas);
	printf("Fraction MgCa phase= %f\n",fmgca);
	printf("Fraction silica phase= %f\n",fsilica);
	if (Cemtype == BLEND) printf("Fraction CAS phase= %f\n",fcas);
	printf("Fraction Slag phase= %f\n",fslag);
        printf("Total count is %ld \n",ctot);
	
	printf("Enter binary filename to open for output \n");
    read_string(file1,sizeof(file1));
	printf("%s\n",file1);
	printf("Enter filename to open for phase ID image \n");
    read_string(file2,sizeof(file2));
	printf("%s\n",file2);
	printf("Enter filename to open for COLOR image \n");
    read_string(file3,sizeof(file3));
	printf("%s\n",file3);
	finfile=fopen(file1,"w");
	foutfile=fopen(file2,"w");
	fcolorfile=fopen(file3,"w");
	fprintf(foutfile,"P2\n");
	fprintf(foutfile,"%d %d\n",xsize,ysize);
	fprintf(foutfile,"255\n");
	fprintf(fcolorfile,"P3\n");
	fprintf(fcolorfile,"%d %d\n",xsize,ysize);
	fprintf(fcolorfile,"255\n");
	Czero = 0;
	for(i=0;i<xsize;i++){
	for(j=0;j<ysize;j++){
		imgact[i][j]=imgproc[i][j];
		if (imgact[i][j] == 0) Czero++;
		Img[i][j] = (int)(pow(2.,((float)imgact[i][j])));
		fprintf(finfile,"%c",(char)imgact[i][j]);
	}
	}
	for(j=0;j<ysize;j++){
	for(i=0;i<xsize;i++){
		fprintf(foutfile,"%d\n",imgact[i][j]);
		switch (imgact[i][j]) {
			case LPORE:
				fprintf(fcolorfile,"0 0 0\n");
				break;
			case LC3S:
				fprintf(fcolorfile,"162 117 95\n");
				break;
			case LC2S:
				fprintf(fcolorfile,"0 128 255\n");
				break;
			case LC3A:
				fprintf(fcolorfile,"178 178 178\n");
				break;
			case LC4AF:
				fprintf(fcolorfile,"253 253 253\n");
				break;
			case LGYP:
				fprintf(fcolorfile,"255 255 0\n");
				break;
			case LFREELIME:
				fprintf(fcolorfile,"51 205 51\n");
				break;
			case LK2SO4:
				fprintf(fcolorfile,"255 0 0\n");
				break;
			case LNA2SO4:
				fprintf(fcolorfile,"255 192 0\n");
				break;
			case LMGCA:
				fprintf(fcolorfile,"255 105 180\n");
				break;
			case LKAOLIN:
				fprintf(fcolorfile,"255 165 0\n");
				break;
			case LSILICA:
				fprintf(fcolorfile,"0 255 255\n");
				break;
			case LCAS:
				fprintf(fcolorfile,"0 0 128\n");
				break;
			case LSLAG:
				fprintf(fcolorfile,"0 100 0\n");
				break;
			default:
				break;
		}
	}
	}
	fclose(finfile);
	fclose(foutfile);
	fclose(fcolorfile);

	Cnc3s = statsimp(2,VOLUME);
	Cnc2s = statsimp(4,VOLUME);
	Cnc3a = statsimp(8,VOLUME);
	Cnc4af = statsimp(16,VOLUME);
	Cnk2so4 = statsimp(32,VOLUME);
	Cnna2so4 = statsimp(64,VOLUME);
	Cnac3s = statsimp(2,AREA);
	Cnac2s = statsimp(4,AREA);
	Cnac3a = statsimp(8,AREA);
	Cnac4af = statsimp(16,AREA);
	Cnak2so4 = statsimp(32,VOLUME);
	Cnana2so4 = statsimp(64,VOLUME);

	vol2mass();

	printf("\n\nGenerate pdf file? [no]");
    read_string(answer,sizeof(answer));
	if (strlen(answer) < 1) {
		strcpy(answer,"no");
	}

	if (answer[0] == 'Y' || answer[0] == 'y') {
		genlatex(fc3s,fc2s,fc3a,fc4af,fgyp,flime,fkaolin,fslag,fks,fnas,
			fmgca,fsilica,fcas);
	}

	printf("\n\nAdd data to mistats file? [no]");
    read_string(answer,sizeof(answer));
	if (strlen(answer) < 1) {
		strcpy(answer,"no");
	}

	if (answer[0] == 'Y' || answer[0] == 'y') {

		if ((fmistats = fopen("averages.dat","a+")) == NULL) {
			printf("\nCannot open file for appending.");
			return;
		}

		fprintf(fmistats,"%6.4f c3s\n",fc3s);
		fprintf(fmistats,"%6.4f c2s\n",fc2s);
		fprintf(fmistats,"%6.4f c3a\n",fc3a);
		fprintf(fmistats,"%6.4f c4af\n",fc4af);
		fprintf(fmistats,"%6.4f gypsum\n",fgyp);
		fprintf(fmistats,"%6.4f lime\n",flime);
		fprintf(fmistats,"%6.4f kaolin\n",fkaolin);
		fprintf(fmistats,"%6.4f slag\n",fslag);
		fprintf(fmistats,"%6.4f potsulf\n",fks);
		fprintf(fmistats,"%6.4f sodsulf\n",fnas);
		fprintf(fmistats,"%6.4f mgca\n",fmgca);
		fprintf(fmistats,"%6.4f silica\n",fsilica);
		if (Cemtype == BLEND) fprintf(fmistats,"%6.4f cas\n",fcas);
		fprintf(fmistats,"%6.4f c3svol\n",Cvfc3s);
		fprintf(fmistats,"%6.4f c2svol\n",Cvfc2s);
		fprintf(fmistats,"%6.4f c3avol\n",Cvfc3a);
		fprintf(fmistats,"%6.4f c4afvol\n",Cvfc4af);
		fprintf(fmistats,"%6.4f k2so4vol\n",Cvfk2so4);
		fprintf(fmistats,"%6.4f na2so4vol\n",Cvfna2so4);
		fprintf(fmistats,"%6.4f c3ssurf\n",Cafc3s);
		fprintf(fmistats,"%6.4f c2ssurf\n",Cafc2s);
		fprintf(fmistats,"%6.4f c3asurf\n",Cafc3a);
		fprintf(fmistats,"%6.4f c4afsurf\n",Cafc4af);
		fprintf(fmistats,"%6.4f k2so4surf\n",Cafk2so4);
		fprintf(fmistats,"%6.4f na2so4surf\n",Cafna2so4);
		fprintf(fmistats,"%6.4f c3smass\n",Cmfc3s);
		fprintf(fmistats,"%6.4f c2smass\n",Cmfc2s);
		fprintf(fmistats,"%6.4f c3amass\n",Cmfc3a);
		fprintf(fmistats,"%6.4f c4afmass\n",Cmfc4af);
		fprintf(fmistats,"%6.4f k2so4mass\n",Cmfk2so4);
		fprintf(fmistats,"%6.4f na2so4mass\n",Cmfna2so4);
		fprintf(fmistats,"***************\n");
		fclose(fmistats);
	}

	sprintf(cmdnew,"gimp %s &",file3);
	system(cmdnew);
	return;
}
/* Routine to fill in one pixel void pixels */
/* surrounded by seven or eight solid neighbors */
void bkfill(void) 
{
	int i,j,totngh;
	float maxfrac,pblack,fc3s,fc2s,fc3a,fc4af,fgyp;
	float flime,fks,fnas,fmgca,fkaolin,fsilica,fslag,fcas;
	int pixin,color,colorm;
	long int cblack,cmgca,cwhite,cc3s,cc2s,cc3a,cc4af,cgyp,ctot;
	long int nfill,clime,cks,cnas,ckaolin,csilica,cslag,ccas;

	cc3s=cc2s=cc3a=cc4af=cmgca=cgyp=cwhite=cblack=clime=cks=0;
	cslag=cnas=ckaolin=csilica=nfill=ccas=0;
    fcas=fslag=fsilica=fkaolin=fmgca=fnas=fks=flime=0.0;
    fgyp=fc4af=fc3a=fc2s=fc3s=0.0;

	for(i=0;i<xsize;i++){
	for(j=0;j<ysize;j++){

	        pixin=color=imgact[i][j];

        /* If pixel is a void pixel totally surrounded by solids, */
        /* convert it to the most prevalent phase in the surrounding pixels */
	if(color==LPORE){
	nc3s=nc2s=nc3a=nc4af=ngyp=nmgca=nlime=npotsulf=nsodsulf=nkaolin=nsilica=nslag=ncas=0;
	segngh(i,j,1);
	totngh=nc3s+nc2s+nc3a+nc4af+ngyp+nmgca+nlime+npotsulf+nsodsulf+nkaolin+nsilica+nslag+ncas;
	if(totngh>=7){
	maxfrac=(float)nc3s/(float)totngh;
	colorm=LC3S;
	if(maxfrac<(float)nc2s/(float)totngh){
		maxfrac=(float)nc2s/(float)totngh;
		colorm=LC2S;
	}
	if(maxfrac<(float)nc3a/(float)totngh){
		maxfrac=(float)nc3a/(float)totngh;
		colorm=LC3A;
	}
	if(maxfrac<(float)nc4af/(float)totngh){
		maxfrac=(float)nc4af/(float)totngh;
		colorm=LC4AF;
	}
	if(maxfrac<(float)ngyp/(float)totngh){
		maxfrac=(float)ngyp/(float)totngh;
		colorm=LGYP;
	}
	if(maxfrac<(float)nlime/(float)totngh){
		maxfrac=(float)nlime/(float)totngh;
		colorm=LFREELIME;
	}
	if(maxfrac<(float)npotsulf/(float)totngh){
		maxfrac=(float)npotsulf/(float)totngh;
		colorm=LK2SO4;
	}
	if(maxfrac<(float)nsodsulf/(float)totngh){
		maxfrac=(float)nsodsulf/(float)totngh;
		colorm=LNA2SO4;
	}
	if(maxfrac<(float)nkaolin/(float)totngh){
		maxfrac=(float)nkaolin/(float)totngh;
		colorm=LKAOLIN;
	}
	if(maxfrac<(float)nsilica/(float)totngh){
		maxfrac=(float)nsilica/(float)totngh;
		colorm=LSILICA;
	}
	if(maxfrac<(float)ncas/(float)totngh){
		maxfrac=(float)ncas/(float)totngh;
		colorm=LCAS;
	}
	if(maxfrac<(float)nslag/(float)totngh){
		maxfrac=(float)nslag/(float)totngh;
		colorm=LSLAG;
	}
	if(maxfrac<(float)nmgca/(float)totngh){
		maxfrac=(float)nmgca/(float)totngh;
		colorm=LMGCA;
	}

	if((color==LPORE)&&(maxfrac>=0.3)){
		color=colorm;
	}

	}
	}

        /* If changed, update the pixel on the screen */
	if(color!=pixin){
		nfill+=1;
	}
	imgproc[i][j]=color;
        /* Tabulate and report the new phase counts */
	if(color==LPORE){
		cblack+=1;
	}
	if(color==LC3S){
		cc3s+=1;
	}
	if(color==LC2S){
		cc2s+=1;
	}
	if(color==LC3A){
		cc3a+=1;
	}
	if(color==LC4AF){
		cc4af+=1;
	}
	if(color==LGYP){
		cgyp+=1;
	}
	if(color==LFREELIME){
		clime+=1;
	}
	if(color==LK2SO4){
		cks+=1;
	}
	if(color==LNA2SO4){
		cnas+=1;
	}
	if(color==LMGCA){
		cmgca+=1;
	}
	if(color==LKAOLIN){
		ckaolin+=1;
	}
	if(color==LSILICA){
		csilica+=1;
	}
	if(color==LCAS){
		ccas+=1;
	}
	if(color==LSLAG){
		cslag+=1;
	}

	}
	}
	ctot=cmgca+cc3s+cc2s+cc3a+cc4af+cgyp+cks+cnas+clime+ckaolin+csilica+cslag+ccas;
	pblack=(float)cblack/(float)(ctot+cblack);
	fc3s=(float)cc3s/(float)ctot;
	flime=(float)clime/(float)ctot;
	fmgca=(float)cmgca/(float)ctot;
	fkaolin=(float)ckaolin/(float)ctot;
	fkaolin=(float)ccas/(float)ctot;
	fslag=(float)cslag/(float)ctot;
	fsilica=(float)csilica/(float)ctot;
	fks=(float)cks/(float)ctot;
	fnas=(float)cnas/(float)ctot;
	fc2s=(float)cc2s/(float)ctot;
	fc3a=(float)cc3a/(float)ctot;
	fgyp=(float)cgyp/(float)ctot;
	fc4af=(float)cc4af/(float)ctot;

	printf("Updated %ld pixels \n",nfill);
	printf("Fraction pore = %f \n",pblack);
	printf("Fraction C2S = %f \n",fc2s);
	printf("Fraction C3S = %f \n",fc3s);
	printf("Fraction C4AF = %f \n",fc4af);
	printf("Fraction C3A = %f \n",fc3a);
	printf("Fraction gypsum= %f \n",fgyp);
	printf("Fraction Free lime= %f \n",flime);
	printf("Fraction Potassium sulfate= %f \n",fks);
	printf("Fraction Sodium sulfate= %f \n",fnas);
	printf("Fraction Kaolin phase= %f\n",fkaolin);
	printf("Fraction MgCA phase= %f\n",fmgca);
	printf("Fraction Silica phase= %f\n",fsilica);
	if (Cemtype == BLEND) printf("Fraction CAS phase= %f\n",fcas);
	printf("Fraction Slag phase= %f\n",fslag);
	
	for(i=0;i<xsize;i++){
	for(j=0;j<ysize;j++){
		imgact[i][j]=imgproc[i][j];
	}
	}

}
/* Routine to fill in one pixel void pixels */
/* surrounded by eight solid neighbors */
void bkfill1(void) 
{
	int i,j,totngh;
	float maxfrac,pblack,fc3s,fc2s,fc3a,fc4af,fgyp;
	float flime,fks,fnas,fmgca,fkaolin,fsilica,fslag,fcas;
	int pixin,color,colorm;
	long int cblack,cmgca,cwhite,cc3s,cc2s,cc3a,cc4af,cgyp,ctot;
	long int nfill,clime,cks,cnas,ckaolin,csilica,cslag,ccas;

	cc3s=cc2s=cc3a=cc4af=cmgca=cgyp=cwhite=cblack=clime=cks=cnas=ccas=0;
	ckaolin=csilica=nfill=cslag=0;

	for(i=0;i<xsize;i++){
	for(j=0;j<ysize;j++){

	        pixin=color=imgact[i][j];

	if(color==LPORE){
	nc3s=nc2s=nc3a=nc4af=ngyp=nmgca=nlime=npotsulf=nsodsulf=nkaolin=nsilica=nslag=ncas=0;
	segngh(i,j,1);
	totngh=nc3s+nc2s+nc3a+nc4af+ngyp+nmgca+nlime+npotsulf+nsodsulf+nkaolin+nsilica+nslag+ncas;
	if(totngh==8){
	maxfrac=(float)nc3s/(float)totngh;
	colorm=LC3S;
	if(maxfrac<(float)nc2s/(float)totngh){
		maxfrac=(float)nc2s/(float)totngh;
		colorm=LC2S;
	}
	if(maxfrac<(float)nc3a/(float)totngh){
		maxfrac=(float)nc3a/(float)totngh;
		colorm=LC3A;
	}
	if(maxfrac<(float)nc4af/(float)totngh){
		maxfrac=(float)nc4af/(float)totngh;
		colorm=LC4AF;
	}
	if(maxfrac<(float)ngyp/(float)totngh){
		maxfrac=(float)ngyp/(float)totngh;
		colorm=LGYP;
	}
	if(maxfrac<(float)nlime/(float)totngh){
		maxfrac=(float)nlime/(float)totngh;
		colorm=LFREELIME;
	}
	if(maxfrac<(float)npotsulf/(float)totngh){
		maxfrac=(float)npotsulf/(float)totngh;
		colorm=LK2SO4;
	}
	if(maxfrac<(float)nsodsulf/(float)totngh){
		maxfrac=(float)nsodsulf/(float)totngh;
		colorm=LNA2SO4;
	}
	if(maxfrac<(float)nkaolin/(float)totngh){
		maxfrac=(float)nkaolin/(float)totngh;
		colorm=LKAOLIN;
	}
	if(maxfrac<(float)nsilica/(float)totngh){
		maxfrac=(float)nsilica/(float)totngh;
		colorm=LSILICA;
	}
	if(maxfrac<(float)ncas/(float)totngh){
		maxfrac=(float)ncas/(float)totngh;
		colorm=LCAS;
	}
	if(maxfrac<(float)nslag/(float)totngh){
		maxfrac=(float)nslag/(float)totngh;
		colorm=LSLAG;
	}
	if(maxfrac<(float)nmgca/(float)totngh){
		maxfrac=(float)nmgca/(float)totngh;
		colorm=LMGCA;
	}

	if((color==LPORE)&&(maxfrac>=0.3)){
		color=colorm;
	}

	}
	}

	if(color!=pixin){
		nfill+=1;
	}
	imgproc[i][j]=color;
	if(color==LPORE){
		cblack+=1;
	}
	if(color==LC3S){
		cc3s+=1;
	}
	if(color==LC2S){
		cc2s+=1;
	}
	if(color==LC3A){
		cc3a+=1;
	}
	if(color==LC4AF){
		cc4af+=1;
	}
	if(color==LGYP){
		cgyp+=1;
	}
	if(color==LFREELIME){
		clime+=1;
	}
	if(color==LK2SO4){
		cks+=1;
	}
	if(color==LNA2SO4){
		cnas+=1;
	}
	if(color==LMGCA){
		cmgca+=1;
	}
	if(color==LKAOLIN){
		ckaolin+=1;
	}
	if(color==LSILICA){
		csilica+=1;
	}
	if(color==LCAS){
		ccas+=1;
	}
	if(color==LSLAG){
		cslag+=1;
	}

	}
	}
	ctot=cmgca+cc3s+cc2s+cc3a+cc4af+cgyp+cks+cnas+clime+ckaolin+csilica+cslag+ccas;
	pblack=(float)cblack/(float)(ctot+cblack);
	fc3s=(float)cc3s/(float)ctot;
	flime=(float)clime/(float)ctot;
	fmgca=(float)cmgca/(float)ctot;
	fkaolin=(float)ckaolin/(float)ctot;
	fslag=(float)cslag/(float)ctot;
	fsilica=(float)csilica/(float)ctot;
	fcas=(float)ccas/(float)ctot;
	fks=(float)cks/(float)ctot;
	fnas=(float)cnas/(float)ctot;
	fc2s=(float)cc2s/(float)ctot;
	fc3a=(float)cc3a/(float)ctot;
	fgyp=(float)cgyp/(float)ctot;
	fc4af=(float)cc4af/(float)ctot;

	printf("Updated %ld pixels \n",nfill);
	printf("Fraction pore = %f \n",pblack);
	printf("Fraction C2S = %f \n",fc2s);
	printf("Fraction C3S = %f \n",fc3s);
	printf("Fraction C4AF = %f \n",fc4af);
	printf("Fraction C3A = %f \n",fc3a);
	printf("Fraction gypsum= %f \n",fgyp);
	printf("Fraction Free lime= %f \n",flime);
	printf("Fraction Potassium sulfate= %f \n",fks);
	printf("Fraction Sodium sulfate= %f \n",fnas);
	printf("Fraction Kaolin phase= %f\n",fkaolin);
	printf("Fraction MgCA phase= %f\n",fmgca);
	printf("Fraction Silica phase= %f\n",fsilica);
	if (Cemtype == BLEND) printf("Fraction CAS phase= %f\n",fcas);
	printf("Fraction Slag phase= %f\n",fslag);
	
	for(i=0;i<xsize;i++){
	for(j=0;j<ysize;j++){
		imgact[i][j]=imgproc[i][j];
	}
	}

}
/* Routine to count the neighboring pixels that are pores */
int countngh(int ix, int iy)
{
	int ix1,iy1;
	int nfound;
	
	
	nfound=0;
	for(ix1=(ix-1);ix1<=(ix+1);ix1++){
	for(iy1=(iy-1);iy1<=(iy+1);iy1++){

	if((ix1>=0)&&(ix1<xsize)&&(iy1>=0)&&(iy1<ysize)){

		if(imgact[ix1][iy1]==0){
			nfound+=1;
		}
	}

	}
	}
	return(nfound);
}
/* Routine to remove the one-pixel regions of solids */	
void onegone(void)
{
	int i,j;
	int nc3s,color;
	long int ndone;

	ndone=0;
	for(i=0;i<xsize;i++){
	for(j=0;j<ysize;j++){

	color=imgact[i][j];
	imgproc[i][j]=imgact[i][j];
	if(imgact[i][j]!=0){

		nc3s=0;
		nc3s=countngh(i,j); 
		if(nc3s==8){ 
			imgproc[i][j]=0;
			ndone+=1;
		}
	}

	}
	}
	for(i=0;i<xsize;i++){
	for(j=0;j<ysize;j++){
		imgact[i][j]=imgproc[i][j];
	}
	}

	printf("Updated %ld pixels \n",ndone);
}
long int statsimp(int mask,int type)
{
	int i,j;
	long int sum,edgesum;

	sum = edgesum = 0;
	for (i = 1; i < (xsize - 1); i++) {
		for (j = 1; j < (ysize - 1); j++) {

			if((mask&(Img[i][j])) != 0) {
				sum++;

				/* Check immediate 4 neighbors for edges */

				if (((Img[i-1][j])) == 1) {
					edgesum++;
				}

				if (((Img[i+1][j])) == 1) {
					edgesum++;
				}

				if (((Img[i][j-1])) == 1) {
					edgesum++;
				}

				if(((Img[i][j+1])) == 1) {
					edgesum++;
				}
			}

		}
	}

	if (type == VOLUME) {
		return(sum);
	} else {
		return(edgesum);
	}

}
void vol2mass(void)
{
	long int totpix,totppix;
	float mc3s,mc2s,mc3a,mc4af,mk2so4,mna2so4,mtot;

	totpix = Cnc3s + Cnc2s + Cnc3a + Cnc4af + Cnk2so4 + Cnna2so4;
	totppix = Cnac3s + Cnac2s + Cnac3a + Cnac4af + Cnak2so4 + Cnana2so4;

	Cvfc3s = ((float) Cnc3s) / ((float) totpix);
	Cvfc2s = ((float) Cnc2s) / ((float) totpix);
	Cvfc3a = ((float) Cnc3a) / ((float) totpix);
	Cvfc4af = ((float) Cnc4af) / ((float) totpix);
	Cvfk2so4 = ((float) Cnk2so4) / ((float) totpix);
	Cvfna2so4 = ((float) Cnna2so4) / ((float) totpix);

	Cafc3s = ((float) Cnac3s) / ((float) totppix);
	Cafc2s = ((float) Cnac2s) / ((float) totppix);
	Cafc3a = ((float) Cnac3a) / ((float) totppix);
	Cafc4af = ((float) Cnac4af) / ((float) totppix);
	Cafk2so4 = ((float) Cnak2so4) / ((float) totppix);
	Cafna2so4 = ((float) Cnana2so4) / ((float) totppix);

	mc3s = Cnc3s * C3S_DEN;
	mc2s = Cnc2s * C2S_DEN;
	mc3a = Cnc3a * C3A_DEN;
	mc4af = Cnc4af * C4AF_DEN;
	mk2so4 = Cnk2so4 * K2SO4_DEN;
	mna2so4 = Cnna2so4 * NA2SO4_DEN;

	mtot = mc3s + mc2s + mc3a + mc4af + mk2so4 + mna2so4;

	Cmfc3s = mc3s / mtot;
	Cmfc2s = mc2s / mtot;
	Cmfc3a = mc3a / mtot;
	Cmfc4af = mc4af / mtot;
	Cmfk2so4 = mk2so4 / mtot;
	Cmfna2so4 = mna2so4 / mtot;

}
void genlatex(float fc3s, float fc2s, float fc3a, float fc4af,
	float fgyp, float flime, float fkaolin, float fslag, float fks,
	float fnas, float fmgca, float fsilica, float fcas)
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
	fprintf(flatex,"C$_3$S = & %6.4f & Kaolin = & %6.4f \\\\ \n",fc3s,fkaolin);
	fprintf(flatex,"C$_2$S = & %6.4f & Slag = & %6.4f \\\\ \n",fc2s,fslag);
	fprintf(flatex,"C$_3$A = & %6.4f & Potassium Sulf = & %6.4f \\\\ \n",fc3a,fks);
	fprintf(flatex,"C$_4$AF = & %6.4f & Sodium Sulf = & %6.4f \\\\ \n",fc4af,fnas);
	fprintf(flatex,"Gypsum = & %6.4f & SiO$_2$ = & %6.4f \\\\ \n",fgyp,fsilica);
	if (Cemtype == BLEND) {
        fprintf(flatex,"Free Lime = & %6.4f & CAS$_2$ = & %6.4f \\\\ \n",flime,fcas);
	    fprintf(flatex,"Mg/Ca = & %6.4f & & \n",fmgca);
    } else {
	    fprintf(flatex,"Free Lime = & %6.4f & Mg/Ca = & %6.4f \n",flime,fmgca);
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
	fprintf(flatex,"C$_3$S & %6.4f & %6.4f & %6.4f \\\\ \n",Cvfc3s,Cafc3s,Cmfc3s);
	fprintf(flatex,"C$_2$S & %6.4f & %6.4f & %6.4f \\\\ \n",Cvfc2s,Cafc2s,Cmfc2s);
	fprintf(flatex,"C$_3$A & %6.4f & %6.4f & %6.4f \\\\ \n",Cvfc3a,Cafc3a,Cmfc3a);
	fprintf(flatex,"C$_4$AF & %6.4f & %6.4f & %6.4f \\\\ \n",Cvfc4af,Cafc4af,Cmfc4af);
	fprintf(flatex,"K$_2$SO$_4$ & %6.4f & %6.4f & %6.4f \\\\ \n",Cvfk2so4,Cafk2so4,Cmfk2so4);
	fprintf(flatex,"Na$_2$SO$_4$ & %6.4f & %6.4f & %6.4f \\\\ \n",Cvfna2so4,Cafna2so4,Cmfna2so4);
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
