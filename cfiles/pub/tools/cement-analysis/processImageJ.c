/***********************************************************
 * Program processImageJ takes the ASCII text output from
 * an ImageJ image and converts it into all the files needed for VCCTL 9:
 *
 *     (1) A color gif file for viewing
 *     (2) A PFC file with volume and area fractions
 *     (3) A correlation function kernel for each phase combination
 *     (4) One file each for the mass fractions of gypsum, hemihyd, and anhydrite
 *
 ***********************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "vcctl.h"

#define MAXDIM 3000
#define CSIZE 60    /* Extent of correlation computation in pixels */

#define DEFAULT 1
#define MANUAL 2
#define NUMMENUCHOICES 2

#define LC3S 1
#define LC2S 2
#define LC3A 3
#define LC4AF 4
#define LGYP 5
#define LPORE 6
#define LK2SO4 7
#define LNA2SO4 8
#define LFREELIME 9
#define LCACO3 10
#define LMGCA 11 
#define LKAOLIN 12
#define LSILICA 13
#define LCAS 14
#define LSLAG 15
#define LINERT 16
#define LC3SVF		LINERT + 1
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

struct imgdat
{
    float val[NQUANT];
} img_var;

/* Function declarations */
int checkArgs(int argc, char *argv[]);
void printUsageMessage();
int getImageDimensions(char *ifilename, float *scale);
int setIDVals(char *ifilename, int *processphaselist, int *vcctlphaselist);
int getCalciumSulfateCarriers();
int createGIFImage(int imagenum, int *processphaselist, int *vcctlphaselist);
int computeStats();
void multipleImageStats();
int calculateCorrelationFunctions(float scalef);
int getAlkaliInformation();
int getTextInformation();
int corrcalc(int maskval, float scalef);
int corrxy2r(char *buff);
void copyLegend();
long int area(int mask);
void printBanner();
void genASCII();

/* Global variables declared here */
int Img[MAXDIM][MAXDIM],Cimg[MAXDIM][MAXDIM],numin;
long int c3s,c2s,c3a,c4af,k2so4,na2so4,gyp;
long int ac3s,ac2s,ac3a,ac4af,ak2so4,ana2so4;
long int mgca,silica,cas,slag,kaolin,freelime;
long int solid,clink,Xsize,Ysize,totarea;
float vfc3s,vfc2s,vfc3a,vfc4af,vfk2so4;
float vfna2so4,vfgyp,vfmgca,vfsilica,vfcas,vfslag;
float vfkaolin,vffreelime;
float cfc3s,cfc2s,cfc3a,cfc4af,cfk2so4,cfna2so4;
float afc3s,afc2s,afc3a,afc4af,afk2so4,afna2so4;
float mc3s,mc2s,mc3a,mc4af,mk2so4,mna2so4,mtot;
float mfc3s,mfc2s,mfc3a,mfc4af,mfk2so4,mfna2so4;
float avg[NQUANT],stddev[NQUANT];
char Inputrt[MAXSTRING],Filert[MAXSTRING],Filext[MAXSTRING];

int NumImagesToProcess = 1;
int Verbose = 0;

int main(int argc, char *argv[])
{
    int choice,imagenumber;
    int vcctlphaselist[NPHASES],processphaselist[NPHASES];
    float scalef;
    char ifilename[MAXSTRING],buff[MAXSTRING];

    Xsize = Ysize = 0;
    imagenumber = 0;
    choice = -1;
    scalef = 0.0;

    if (checkArgs(argc,argv)) {
        exit(1);
    }

    /* Find out how many images the user wants to average */
    
    while (imagenumber < NumImagesToProcess) {

        printf("\n\nEnter the root name of the image file (without the extension): ");
        read_string(buff,sizeof(buff));
        sprintf(Inputrt,"%s",buff);
        printf("\n%s",Inputrt);

        printf("\n\nEnter the root name of the output files (without the extension): ");
        read_string(buff,sizeof(buff));
        sprintf(Filert,"%s",buff);
        printf("\n%s",Filert);
        
        /* The following function gets the image dimensions and scale factor */

        Xsize = Ysize = 0;
        scalef = 0.0;
        if (getImageDimensions(ifilename,&scalef)) {
            exit(1);
        }

        /* Get information from user on calcium sulfate carriers and write to files */

        if (getCalciumSulfateCarriers()) {
            exit(1);
        }

        /* Next collect information on alkali content */

        if (getAlkaliInformation()) {
            exit(1);
        }

        /* Next collect textual information */

        if (getTextInformation()) {
            exit(1);
        }

        /* Next, scan the image once for data and populate the microstructure */
        /* Also determines the list of integer values in the input file and assign */
        /* them to VCCTL values */

        if (setIDVals(ifilename,processphaselist,vcctlphaselist)) {
            exit(1);
        }

        /* Create the gif image with official VCCTL color coding */
        /* Also create the masked array */

        if (createGIFImage(imagenumber,processphaselist,vcctlphaselist)) {
            exit(1);
        }

        /* Next compute and output the phase statistics */

        if (Verbose) {
            printf("\nComputing phase statistics for image number %d... ",imagenumber);
            fflush(stdout);
        }

        if (computeStats()) {
            exit(1);
        }

        if (Verbose) {
            printf("Done!\n");
            fflush(stdout);
        }

        imagenumber++;  /* Now go to the next image to process */
    }

    
    if (NumImagesToProcess > 1) multipleImageStats(); /* Average the volume and area fractions for all images */

    /* Next compute and output the correlation functions */

    if (calculateCorrelationFunctions(scalef)) {
        exit(1);
    }

    /* Finally, copy the image legend to the working directory */

    /* copyLegend(); */

    printf("\n\nCalculations are finished.  Exiting.\n\n");
    fflush(stdout);


    exit(0);
}

int checkArgs(int argc, char *argv[])
{
    register int i;
    int status = 0;
    if (argc > 1) {
        for (i = 1; i < argc; i++) {
            if ((!strcmp(argv[i],"-v")) || (!strcmp(argv[i],"--verbose"))) {
                Verbose = 1;
            } else if (((!strcmp(argv[i],"-n")) || (!strcmp(argv[i],"--number"))) && i < (argc - 1)) {
                NumImagesToProcess = atoi(argv[i+1]);
            } else {
                printUsageMessage();
                status = 1;
            }
        }
    } else if (argc != 1) {
        printUsageMessage();
        status = 1;
    } else {
        Verbose = 0;
    }

    return(status);
}

void printUsageMessage()
{
    printf("\n\nUsage: processImageJ [-v] [-n numberimagefields]");
    printf("\n\t -v (or --verbose) : use verbose output");
    printf("\n\t -n num (or --number num) : average num image fields (default is 1)\n\n");
    return;
}

int getImageDimensions(char *ifilename, float *scalef)
{
    long int numpix;
    float scaleval;
    char buff[MAXSTRING],ch;
    FILE *fpin;

    sprintf(ifilename,"%s.txt",Inputrt);
    if (Verbose) printf("\nInput file is %s",ifilename);

    if ((fpin = fopen(ifilename,"r")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",ifilename);
        return(1);
    }

    /* Count the tabs to find out how many columns */
    /* Count the newlines to find out how many rows */

    numpix = 1;
    Ysize = 0;
    while (!feof(fpin)) {
        fscanf(fpin,"%c",&ch);
        if (!feof(fpin)) {
            if (ch == '\n') {
                if (Ysize == 0) Xsize = numpix;
                Ysize++;
            } else if ((ch == '\t') && (Ysize == 0)) {
                numpix++;
            }
        }
    }

    fclose(fpin);
    if (Xsize >= MAXDIM || Ysize >= MAXDIM) {
        printf("\n\nImage is too big.  Change MAXDIM and recompile this program.\n\n");
        return(1);
    }

    if (Verbose) {
        printf("\n\nImage format OK.  X size = %ld, Y size = %ld\n",Xsize,Ysize);
        fflush(stdout);
    }

    scaleval = -1.0;
    while (scaleval <= 0.0 || scaleval > 1.0) {
        printf("\n\nEnter micrometers per pixel (< 1.0):  ");
        /*
        printf("\n\tEnter 1 if the image pixel = 1 micron");
        printf("\n\tEnter 2 if the image pixel = 0.5 micron");
        printf("\n\tEnter 3 if the image pixel = 0.33 micron");
        printf("\n\tEnter 4 if the image pixel = 0.25 micron");
        printf("\n? ");
	*/
        read_string(buff,sizeof(buff));
        scaleval = atof(buff);
        if (scaleval <= 0.0 || scaleval > 1.0) {
            printf("\n\nInvalid scale factor value.  Try again, please.");
        }
    }

    *scalef = (1.0/scaleval);

    return(0);
}

int setIDVals(char *ifilename, int *processphaselist, int *vcctlphaselist)
{
    register int i,j;
    int inputphaselist[NPHASES],k,done,inid,tempval,choice,numph = 0;
    char buff[MAXSTRING];
    FILE *fpin;

    if ((fpin = fopen(ifilename,"r")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",ifilename);
        return(1);
    }

    /* Initialize input phase list */
    for (j = 0; j < NPHASES; j++) {
        inputphaselist[j] = -1;
        processphaselist[j] = -1;
        vcctlphaselist[j] = -1;
    }

    if (Verbose) {
        printf("\n\nScanning image for phase identifiers...");
        fflush(stdout);
    }

    for (j = 0; j < Ysize; j++) {
        for (i = 0; i < Xsize; i++) {
            fscanf(fpin,"%s",buff);
            inid = atoi(buff);
            Img[i][j] = inid;
            done = 0;
            k = 0;
            while (k < numph && done == 0) {
                if (inputphaselist[k] == inid) done = 1;
                k++;
            }
            if (done == 0) {
                inputphaselist[numph] = inid;
                numph++;
            }
        }
    }

    fclose(fpin);

    /* Now we have a list of all the input phase identifier numbers. */
    /* Sort the list */

    for (i = 0; i < numph - 1; i++) {
        for (j = i + 1; j < numph; j++) {
            if (inputphaselist[i] > inputphaselist[j]) {
                tempval = inputphaselist[i];
                inputphaselist[i] = inputphaselist[j];
                inputphaselist[j] = tempval;
            }
        }
    }

    if (Verbose) {
        printf(" Done!");
        fflush(stdout);
    }
    printf("\nHere are the %d phase identifiers I found:\n",numph);
    k = 0;
    while (k < numph) {
        printf("\t %d",inputphaselist[k]);
        k++;
    }
    fflush(stdout);

    /* Now prompt user to assign phases to these identifiers */

    printf("\n\nPlease assign phases to these identifiers by selecting\n");
    printf("one of the following options:\n");
    choice = -1;
    while (choice <= 0 || choice > NUMMENUCHOICES) {
        printf("\t%d. Default (C3S = 1, C2S = 2, C3A = 3, C4AF = 4,\n",DEFAULT);
        printf("\t       gypsum = 5, void = 6, arcanite = 7, thenardite = 8,\n");
        printf("\t       free lime = 9, limestone = 10, periclase = 11\n");
        printf("\t       kaolin = 12, silica = 13\n");
        printf("\t%d. Manually assign phases\n? ",MANUAL);
        read_string(buff,sizeof(buff));
        choice = atoi(buff);
        printf("\n%d\n",choice);
    }

    switch (choice) {
        case DEFAULT:
            processphaselist[1] = LC3S; 
            processphaselist[2] = LC2S; 
            processphaselist[3] = LC3A; 
            processphaselist[4] = LC4AF; 
            processphaselist[5] = LGYP; 
            processphaselist[6] = LPORE; 
            processphaselist[7] = LK2SO4; 
            processphaselist[8] = LNA2SO4; 
            processphaselist[9] = LFREELIME; 
            processphaselist[10] = LCACO3; 
            processphaselist[11] = LMGCA; 
            processphaselist[12] = LKAOLIN; 
            processphaselist[13] = LSILICA; 
            vcctlphaselist[1] = C3S; 
            vcctlphaselist[2] = C2S; 
            vcctlphaselist[3] = C3A; 
            vcctlphaselist[4] = C4AF; 
            vcctlphaselist[5] = GYPSUM; 
            vcctlphaselist[6] = POROSITY; 
            vcctlphaselist[7] = K2SO4; 
            vcctlphaselist[8] = NA2SO4; 
            vcctlphaselist[9] = FREELIME; 
            vcctlphaselist[10] = CACO3; 
            vcctlphaselist[11] = INERT; 
            vcctlphaselist[12] = INERT; 
            vcctlphaselist[13] = INERT; 
            break;
        case MANUAL:
            k = 1;
            while (k <= numph) {
                printf("\nAssign VCCTL phase number for image id = %d.  Choices are:\n",k);
                printf("\tPorosity (choose %d)\n",LPORE);
                printf("\tAlite (choose %d)\n",LC3S);
                printf("\tBelite (choose %d)\n",LC2S);
                printf("\tAluminate (choose %d)\n",LC3A);
                printf("\tFerrite (choose %d)\n",LC4AF);
                printf("\tArcanite (choose %d)\n",LK2SO4);
                printf("\tThenardite (choose %d)\n",LNA2SO4);
                printf("\tGypsum (choose %d)\n",LGYP);
                printf("\tFree lime (choose %d)\n",LFREELIME);
                printf("\tCalcite/Limestone (choose %d)\n",LCACO3);
                printf("\tPericlase (choose %d)\n",LMGCA);
                printf("\tKaolin (choose %d)\n",LKAOLIN);
                printf("\tSilica (choose %d)\n",LSILICA);
                printf("\tCAS glass (choose %d)\n",LCAS);
                printf("\tSlag (choose %d)\n",LSLAG);
                printf("\tOther (choose %d)\n",LINERT);
                read_string(buff,sizeof(buff));
                choice = atoi(buff);
                if (choice != LPORE && choice != LC3S && choice != LC2S && choice != LC3A
                    && choice != LC4AF && choice != LK2SO4 && choice != LNA2SO4 && choice != LGYP
                    && choice != LFREELIME && choice != LMGCA && choice != LKAOLIN && choice != LSILICA
                    && choice != LCAS && choice != SLAG) choice = INERT;
                processphaselist[k] = choice;
                if (choice == LPORE) { vcctlphaselist[k] = POROSITY; }
                else if (choice == LC3S) { vcctlphaselist[k] = C3S; }
                else if (choice == LC2S) { vcctlphaselist[k] = C2S; }
                else if (choice == LC3A) { vcctlphaselist[k] = C3A; }
                else if (choice == LC4AF) { vcctlphaselist[k] = C4AF; }
                else if (choice == LK2SO4) { vcctlphaselist[k] = K2SO4; }
                else if (choice == LNA2SO4) { vcctlphaselist[k] = NA2SO4; }
                else if (choice == LGYP) { vcctlphaselist[k] = GYPSUM; }
                else if (choice == LFREELIME) { vcctlphaselist[k] = FREELIME; }
                else if (choice == LCACO3) { vcctlphaselist[k] = CACO3; }
                else if (choice == LMGCA) { vcctlphaselist[k] = INERT; }
                else if (choice == LKAOLIN) { vcctlphaselist[k] = INERT; }
                else if (choice == LCAS) { vcctlphaselist[k] = CAS2; }
                else if (choice == LSLAG) { vcctlphaselist[k] = SLAG; }
                else { vcctlphaselist[k] = INERT; }
                printf("\n%d\n",choice);
                if (choice == LCACO3) choice = LFREELIME;
                processphaselist[k] = choice;
                k++;
            }
            break;
    }

    return(0);
}

int getCalciumSulfateCarriers()
{
    float gypval,hemval,anhval;
    char gypch[MAXSTRING];
    FILE *fpgyp;

    printf("\n\nWhat is the mass fraction of gypsum in the cement? ");
    read_string(gypch,sizeof(gypch));
    gypval = atof(gypch);
    printf("\n\nWhat is the mass fraction of hemihydrate in the cement? ");
    read_string(gypch,sizeof(gypch));
    hemval = atof(gypch);
    printf("\n\nWhat is the mass fraction of anhydrite in the cement? ");
    read_string(gypch,sizeof(gypch));
    anhval = atof(gypch);
    fflush(stdout);

    /* Output the calcium sulfate mass fractions to data files */

    sprintf(gypch,"%s.gyp",Filert);
    if ((fpgyp = fopen(gypch,"w")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",gypch);
        return(1);
    }
    fprintf(fpgyp,"%6.4f",gypval);
    fclose(fpgyp);

    sprintf(gypch,"%s.hem",Filert);
    if ((fpgyp = fopen(gypch,"w")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",gypch);
        return(1);
    }
    fprintf(fpgyp,"%6.4f",hemval);
    fclose(fpgyp);

    sprintf(gypch,"%s.anh",Filert);
    if ((fpgyp = fopen(gypch,"w")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",gypch);
        return(1);
    }
    fprintf(fpgyp,"%6.4f",anhval);
    fclose(fpgyp);

    return(0);
}

int createGIFImage(int imagenumber, int *processphaselist, int *vcctlphaselist)
{
    register int i,j;
    int choice;
    int red[NPHASES],green[NPHASES],blue[NPHASES];
    char FileP3[MAXSTRING],buff[MAXSTRING];
    FILE *fpp3;

    cemcolors(red,green,blue,0);

    sprintf(FileP3,"%s.pnm",Filert);

    if ((fpp3 = fopen(FileP3,"w")) == NULL) {
        printf("\n\nERROR: File %s could not be created\n\n",FileP3);
        return(1);
    }

    fprintf(fpp3,"P3\n");
    fprintf(fpp3,"%d %d\n",(int)Xsize,(int)Ysize);
    fprintf(fpp3,"255\n");

    for (j = 0; j < Ysize; j++) {
        for (i = 0; i < Xsize; i++) {
            choice = vcctlphaselist[Img[i][j]];
            fprintf(fpp3,"%d %d %d\n",red[choice],green[choice],blue[choice]);
            choice = processphaselist[Img[i][j]];
            Cimg[i][j] = (int)(pow(2.0,(float)choice));
            Img[i][j] = choice;
        }
    }

    fclose(fpp3);

    /* Convert the pnm image to gif */
    /* Note:  This requires that ImageMagick be installed on your computer and that */
    /*        its convert command is in your system path                            */

    if (Verbose) {
        printf("\n\nConverting pnm image to gif image... ");
        fflush(stdout);
    }
    sprintf(buff,"convert %s.pnm %s.gif",Filert,Filert);
    system(buff);
    if (Verbose) {
        printf("Done!\n");
        fflush(stdout);
    }

    return(0);
}

int computeStats(void)
{
    register int i,j;
    int inid;
    char buff[MAXSTRING];
    FILE *fmistats;

    solid = clink = 0;
    c3s = c2s = c3a = c4af = k2so4 = na2so4 = 0;
    gyp = mgca = silica = cas = slag = kaolin = freelime = 0;

    for (j = 0; j < Ysize; j++) {
        for (i = 0; i < Xsize; i++) {
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

    if (NumImagesToProcess > 1) {
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

    } else {

        sprintf(buff,"%s.pfc",Filert);
        if ((fmistats = fopen(buff,"w")) == NULL) {
            printf("\nCannot open file for appending.");
            return(1);
        }
        fprintf(fmistats,"%6.4f %6.4f\n",cfc3s,afc3s);
        fprintf(fmistats,"%6.4f %6.4f\n",cfc2s,afc2s);
        fprintf(fmistats,"%6.4f %6.4f\n",cfc3a,afc3a);
        fprintf(fmistats,"%6.4f %6.4f\n",cfc4af,afc4af);
        fprintf(fmistats,"%6.4f %6.4f\n",cfk2so4,afk2so4);
        fprintf(fmistats,"%6.4f %6.4f",cfna2so4,afna2so4);
        fclose(fmistats);

    }

    return(0);
}

long int area(int mask)
{
    register int i,j;
    long int edgesum;

    edgesum = 0;
    for (i = 1; i < (Xsize - 1); i++) {
        for (j = 1; j < (Ysize - 1); j++) {

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

void multipleImageStats(void)
{
	int i,j;
	char buff[MAXSTRING],buff1[MAXSTRING];
	struct imgdat p[MAXIMAGES];
	FILE *infile;

	/* Initialize arrays to zero */

	for (i = 0; i < NQUANT; i++) {
		avg[i] = 0.0;
		stddev[i] = 0.0;
	}

	if (Verbose) printBanner();

	if ((infile = fopen("averages.dat","r")) == NULL) {
		printf("\n\nERROR in multipleImageStats");
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
			fscanf(infile,"%f %s",&p[i].val[LGYP],buff);
			fscanf(infile,"%f %s",&p[i].val[LFREELIME],buff);
			fscanf(infile,"%f %s",&p[i].val[LKAOLIN],buff);
			fscanf(infile,"%f %s",&p[i].val[LSLAG],buff);
			fscanf(infile,"%f %s",&p[i].val[LK2SO4],buff);
			fscanf(infile,"%f %s",&p[i].val[LNA2SO4],buff);
			fscanf(infile,"%f %s",&p[i].val[LMGCA],buff);
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
                    if (Verbose) {
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
				case LGYP:
					printf("Final image avg. GYPSUM = %7.5f",avg[i]);
					break;
				case LFREELIME:
					printf("Final image avg. LIME = %7.5f",avg[i]);
					break;
				case LKAOLIN:
					printf("Final image avg. KAOLIN = %7.5f",avg[i]);
					break;
				case LSLAG:
					printf("Final image avg. SLAG = %7.5f",avg[i]);
					break;
				case LK2SO4:
					printf("Final image avg. KSULF = %7.5f",avg[i]);
					break;
				case LNA2SO4:
					printf("Final image avg. NASULF = %7.5f",avg[i]);
					break;
				case LMGCA:
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
		}

                genASCII();

	}
        return;
}

/**********
*		
*	Function printBanner
*
*	Prints a one-line banner at the beginning of the program
*
*	Arguments:  None
*	Returns:	Nothing
*
**********/
void printBanner(void)
{
	printf("\n\n***GENERATE STATISTICS FOR MULTIPLE IMAGES***\n\n");
	return;
}

/**********
*		
*	Function genASCII
*
*	Generate ascii text file
*
*	Arguments:      None
*
*	Returns:	Nothing
*
**********/
void genASCII()
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
	fprintf(fascii,"Pot. Sulf. = %6.4f",avg[LK2SO4]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n",stddev[LK2SO4]);
	} else {
		fprintf(fascii,"\n");
	}
	fprintf(fascii,"     C4AF = %6.4f",avg[LC4AF]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\t\t",stddev[LC4AF]);
	} else {
		fprintf(fascii," \t\t");
	}
	fprintf(fascii,"Sod. Sulf. = %6.4f",avg[LNA2SO4]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n",stddev[LNA2SO4]);
	} else {
		fprintf(fascii,"\n");
	}
	fprintf(fascii,"Mg/Ca = %6.4f",avg[LMGCA]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\t\t",stddev[LMGCA]);
	} else {
		fprintf(fascii,"\t\t");
	}
	fprintf(fascii,"   Gypsum = %6.4f",avg[LGYP]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n",stddev[LGYP]);
	} else {
		fprintf(fascii," \n");
	}
	fprintf(fascii,"Silica = %6.4f",avg[LSILICA]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\t\t",stddev[LSILICA]);
	} else {
		fprintf(fascii,"\t\t");
	}
	fprintf(fascii,"Free Lime = %6.4f",avg[LFREELIME]);
	if (numin > 1) {
		fprintf(fascii," (%6.4f)\n\n\n",stddev[LFREELIME]);
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

int calculateCorrelationFunctions(float scalef)
{
    /* For silicates */
    printf("\nComputing correlation function kernel for combined silicates... ");
    fflush(stdout);
    sprintf(Filext,"sil");
    if (corrcalc(6,scalef)) {
        return(1);
    }

    printf("Done!");
    fflush(stdout);

    /* For C3S */
    printf("\nComputing correlation function kernel for C3S... ");
    fflush(stdout);
    sprintf(Filext,"c3s");
    if (corrcalc(2,scalef)) {
        return(1);
    }
    printf("Done!");
    fflush(stdout);

    /* For aluminates */
    printf("\nComputing correlation function kernel for combined aluminates... ");
    fflush(stdout);
    sprintf(Filext,"alu");
    if (corrcalc(24,scalef)) {
        return(1);
    }
    printf("Done!");
    fflush(stdout);

    if (vfc3a >= vfc4af) {
        printf("\nComputing correlation function kernel for C3A... ");
        fflush(stdout);
        sprintf(Filext,"c3a");
        if (corrcalc(8,scalef)) {
            return(1);
        }
        printf("Done!");
        fflush(stdout);
    } else {
        printf("\nComputing correlation function kernel for C4AF... ");
        fflush(stdout);
        sprintf(Filext,"c4f");
        if (corrcalc(16,scalef)) {
            return(1);
        }
        printf("Done!");
        fflush(stdout);
    }

    if (vfk2so4 > 0.0) {
        printf("\nComputing correlation function kernel for K2SO4... ");
        fflush(stdout);
        sprintf(Filext,"k2o");
        if (corrcalc(32,scalef)) {
            return(1);
        }
        printf("Done!");
        fflush(stdout);
    }

    if (vfna2so4 > 0.0) {
        printf("\nComputing correlation function kernel for Na2SO4... ");
        fflush(stdout);
        sprintf(Filext,"n2o");
        if (corrcalc(64,scalef)) {
            return(1);
        }
        printf("Done!\n");
        fflush(stdout);
    }

    return(0);
}

int corrcalc(int mask, float scalef)
{
    int i,j;
    int xoff,yoff,iscale,jscale;
    long int sum,ntot;
    double fsum;
    float fxoff,fyoff,fiscale,fjscale;
    char fileo[MAXSTRING],buff[MAXSTRING];
    FILE *outfile;

    sprintf(fileo,"%s_xy.%s",Filert,Filext);
    if ((outfile = fopen(fileo,"w")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",fileo);
        return(1);
    }

    /* Output header consisting of the extent of the correlation matrix */
    fprintf(outfile,"%d %d\n",CSIZE+1,CSIZE+1);

    /* Now perform calculation */
    /* Correlation is computed only over a distance of CSIZE pixels, which ALWAYS are 1 micrometer */

    fflush(stdout);
    for (i = 0; i <= CSIZE; i++){
        for (j = 0; j <= CSIZE; j++){
            fflush(stdout);
            sum = 0;
            ntot = 0;

            /* iscale and jscale represent limits of correlation calculation since */
            /* original image is assumed to be non-periodic */

            fiscale = (float)(i * scalef);
            fjscale = (float)(j * scalef);
            iscale = (int)(fiscale + 0.5);
            jscale = (int)(fjscale + 0.5);

            /* Be sure to skip to every scalef pixel to adjust resolution */

            for (fxoff = 0.0; fxoff < (Xsize-fiscale); fxoff += scalef){
                xoff = (int)(fxoff + 0.5);
                for (fyoff = 0.0; fyoff < (Ysize-fjscale); fyoff += scalef){
                    yoff = (int)(fyoff + 0.5);
                    ntot += 1;
                    /* Increment counter if both pixels contain one of the necessary phases */
                    if (((mask&(Cimg[xoff][yoff]))!=0)&&
                       ((mask&(Cimg[(int)(fxoff+fiscale+0.5)][(int)(fyoff+fjscale+0.5)]))!=0)){
                       sum += 1;
                    }
	        }
            }

            /* Determine and output value for S(x,y) */
            fsum = (double)sum/(double)ntot;
            fprintf(outfile,"%d %d %lf \n",i,j,fsum);
            fflush(outfile);

        }
    }

    fclose(outfile);

    if (Verbose) {
        printf("\nGoing into corrxy2r with %s and %s... ",fileo,Filext);
        fflush(stdout);
    }
    if (corrxy2r(fileo)) {
        return(1);
    }
    if (Verbose) {
        printf("Done!  Attempting to erase the intermediate file %s... ",fileo);
        fflush(stdout);
    }
    sprintf(buff,"erase /F /Q %s",fileo);
    system(buff);
    if (Verbose) {
        printf("Done!\n");
        fflush(stdout);
    }

    return(0);
}

int corrxy2r(char *buff)
{
    FILE *infile,*outfile;
    int i,j,x,y,r,l,xm,ym,nx,ny,status;
    float sorg[CSIZE+5][CSIZE+5],ssum,snew,z,theta;
    float xt,yt,s1,s2,st,xr;
    char buff1[MAXSTRING];
    double PIVAL = 3.1415926;

    status = 0;
    if ((infile = fopen(buff,"r")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",buff);
	fflush(stdout);
        return(1);
    }

    /* Read in extent of original S(x,y) calculation, usually 60x60 */
    fscanf(infile,"%d %d\n",&nx,&ny);
    if (Verbose) printf(" %2d %2d",nx,ny);

    /* Read in all of the S(x,y) values */
    if (Verbose) {
        printf("\n00 00");
	fflush(stdout);
    }
    for (i = 0; i < nx; i++){
        for (j = 0; j < ny; j++){
            if (Verbose) printf("\b\b\b\b\b%2d %2d",i,j);
            fflush(stdout);
            fscanf(infile,"%d %d %f \n",&x,&y,&z);
            sorg[x][y] = z;
        }
    }

    fclose(infile);

    /* Open output file and write out correlation extent as first value */
    sprintf(buff1,"%s.%s",Filert,Filext);

    if ((outfile = fopen(buff1,"w")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",buff1);
	fflush(stdout);
        return(1);
    }

    fprintf(outfile,"%d\n",nx-1);

    /* Now convert S(x,y) to S(r) format */

    for (r = 0; r < (ny-1); r++) {
        ssum = 0.0;
        xr = (float)r;
		
        for (l = 0; l <= (2*r); l++){
		
            if(xr==0){theta=0;}
            else{theta=PIVAL*(float)l/(4.*xr);}
            xt=xr*cos(theta);
            yt=xr*sin(theta);
            xm=(int)xt;
            ym=(int)yt;

            /* Use bilinear interpolation */
            s1=(sorg [xm] [ym])-(sorg [xm] [ym] - sorg [xm+1] [ym])*(xt-(float)xm);
            s2=(sorg [xm] [ym+1])-(sorg [xm] [ym+1] -sorg [xm+1] [ym+1])*(xt-(float)xm);

            st=s1-(s1-s2)*(yt-(float)ym);
            ssum+=st;
        }

        snew=ssum/(2.*(float)r+1.);
        if (Verbose) printf("%d %f \n",r,snew);
        fprintf(outfile,"%d %f\n",r,snew);

    }

    fclose(outfile);
    return(0);
}

int getAlkaliInformation()
{
    float val;
    char buff[MAXSTRING],outfilename[MAXSTRING];
    FILE *fpout;

    sprintf(outfilename,"%s.alk",Filert);
    if ((fpout = fopen(outfilename,"w")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",outfilename);
	fflush(stdout);
        return(1);
    }

    printf("\n\nThe next questions relate to the alkali content of the cement:");

    val = 0.1;
    printf("\n\tWhat is the equivalent Na2O %% by mass (default = 0.1)? ");
    read_string(buff,sizeof(buff));
    if (strlen(buff) >= 2) val = atof(buff);
    fprintf(fpout,"%6.4f",val);

    val = 0.2;
    printf("\n\tWhat is the equivalent K2O %% by mass (default = 0.2)? ");
    read_string(buff,sizeof(buff));
    if (strlen(buff) >= 2) val = atof(buff);
    fprintf(fpout,"\n%6.4f",val);

    val = 0.02;
    printf("\n\tWhat is readily-soluble Na2O %% by mass (default = 0.02)? ");
    read_string(buff,sizeof(buff));
    if (strlen(buff) >= 2) val = atof(buff);
    fprintf(fpout,"\n%6.4f",val);

    val = 0.08;
    printf("\n\tWhat is the readily-soluble K2O %% by mass (default = 0.08)? ");
    read_string(buff,sizeof(buff));
    if (strlen(buff) >= 2) val = atof(buff);
    fprintf(fpout,"\n%6.4f",val);

    val = 0.000;
    printf("\n\tWhat is the %% by mass of Na2O added as NaOH to the solution (default = 0)? ");
    read_string(buff,sizeof(buff));
    if (strlen(buff) >= 2) val = atof(buff);
    fprintf(fpout,"\n%6.4f",val);

    val = 0.000;
    printf("\n\tWhat is the %% by mass of K2O added as KOH to the solution (default = 0)? ");
    read_string(buff,sizeof(buff));
    if (strlen(buff) >= 2) val = atof(buff);
    fprintf(fpout,"\n%6.4f",val);

    fclose(fpout);
    return(0);
}

int getTextInformation()
{
    int choice;
    char buff[2*MAXSTRING],outfilename[MAXSTRING];
    FILE *fpout;

    sprintf(outfilename,"%s.inf",Filert);
    if ((fpout = fopen(outfilename,"w")) == NULL) {
        printf("\n\nERROR: File %s could not be opened\n\n",outfilename);
	fflush(stdout);
        return(1);
    }

    printf("\n\nThe next entries relate to general information about the cement:");

    printf("\n\tProvide a descriptive name for the cement: ");
    read_string(buff,sizeof(buff));
    fprintf(fpout,"Desc     %s",buff);

    printf("\n\tBriefly describe the source of the cement: ");
    read_string(buff,sizeof(buff));
    fprintf(fpout,"\nSource   %s",buff);

    printf("\n\tWhen was the cement characterized? ");
    read_string(buff,sizeof(buff));
    fprintf(fpout,"\nDate     %s",buff);

    printf("\n\tWhat is the surface area of the cement, in m2/kg? ");
    read_string(buff,sizeof(buff));
    fprintf(fpout,"\nFineness %s",buff);

    printf("\n\tIs this value based on");
    printf("\n\t\t1. Blaine");
    printf("\n\t\t2. Particle Size Distribution");
    printf("\n\t\t3. BET");
    printf("\n\t\t4. Other");
    printf("\n\t? ");
    read_string(buff,sizeof(buff));
    choice = atoi(buff);
    fprintf(fpout," (based on ");
    switch (choice) {
        case 1:
            fprintf(fpout,"Blaine)");
            break;
        case 2:
            fprintf(fpout,"PSD analysis)");
            break;
        case 3:
            fprintf(fpout,"BET analysis)");
            break;
        default:
            fprintf(fpout,"an unspecified technique)");
            break;
    }

    fclose(fpout);

    return(0);
}

void copyLegend()
{
    char buff[MAXSTRING];
    sprintf(buff,"copy /Y C:\\legend.gif %s_legend.gif",Filert);
    system(buff);
}
