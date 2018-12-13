/************************************************************************/
/*                                                                      */
/*      Program: vol2mass.c                                             */
/*      Purpose: To convert volume fractions of the four major cement   */
/*              phases to mass fractions.  Takes input as the number    */
/*              of pixels found for each of these four phases           */
/*      	(output from program statsimp)                              */
/*                                                                      */
/*      Programmer: Jeffrey W. Bullard                                  */
/*                  NIST                                                */
/*                  100 Bureau Drive Stop 8621                          */
/*                  Building 226 Room B-350                             */
/*                  Gaithersburg, MD  20899-8621                        */
/*                  Phone: (301) 975-5725                               */
/*                  Fax: (301) 990-6891                                 */
/*                  E-mail: bullard@nist.gov                            */
/*                                                                      */
/************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "vcctl.h"

/***
*	The following densities are given in units of Mg/m^3
*	Data obtained from:
*
*		D.P. Bentz, J. Am. Ceram. Soc. Vol. 80 [1] 3-21 (1997).
*
***/

#define C3S_DEN		3.21
#define C2S_DEN		3.28
#define C3A_DEN		3.03
#define C4AF_DEN	3.73

void print_banner(void);

int main (void)
{
	int totpix = 0;
	int totppix = 0;
	int nc3s,nc2s,nc3a,nc4af;
	int npc3s,npc2s,npc3a,npc4af;
	float mc3s,mc2s,mc3a,mc4af,mtot;
	float vfc3s,vfc2s,vfc3a,vfc4af;
	float pfc3s,pfc2s,pfc3a,pfc4af;
	float mfc3s,mfc2s,mfc3a,mfc4af;
    char buff[MAXSTRING];

	print_banner();

	printf("\n\nEnter number of AREA pixels for phase C3S: ");
    read_string(buff,sizeof(buff));
    nc3s = atoi(buff);
	totpix += nc3s;

	printf("\nEnter number of AREA pixels for phase C2S: ");
    read_string(buff,sizeof(buff));
    nc2s = atoi(buff);
	totpix += nc2s;

	printf("\nEnter number of AREA pixels for phase C3A: ");
    read_string(buff,sizeof(buff));
    nc3a = atoi(buff);
	totpix += nc3a;

	printf("\nEnter number of AREA pixels for phase C4AF: ");
    read_string(buff,sizeof(buff));
    nc4af = atoi(buff);
	totpix += nc4af;

	printf("\n\nEnter number of PERIMETER pixels for phase C3S: ");
    read_string(buff,sizeof(buff));
    npc3s = atoi(buff);
	totppix += npc3s;

	printf("\nEnter number of PERIMETER pixels for phase C2S: ");
    read_string(buff,sizeof(buff));
    npc2s = atoi(buff);
	totppix += npc2s;

	printf("\nEnter number of PERIMETER pixels for phase C3A: ");
    read_string(buff,sizeof(buff));
    npc3a = atoi(buff);
	totppix += npc3a;

	printf("\nEnter number of PERIMETER pixels for phase C4AF: ");
    read_string(buff,sizeof(buff));
    npc4af = atoi(buff);
	totppix += npc4af;

	vfc3s = ((float) nc3s) / ((float) totpix);
	vfc2s = ((float) nc2s) / ((float) totpix);
	vfc3a = ((float) nc3a) / ((float) totpix);
	vfc4af = ((float) nc4af) / ((float) totpix);

	pfc3s = ((float) npc3s) / ((float) totppix);
	pfc2s = ((float) npc2s) / ((float) totppix);
	pfc3a = ((float) npc3a) / ((float) totppix);
	pfc4af = ((float) npc4af) / ((float) totppix);

	mc3s = nc3s * C3S_DEN;
	mc2s = nc2s * C2S_DEN;
	mc3a = nc3a * C3A_DEN;
	mc4af = nc4af * C4AF_DEN;

	mtot = mc3s + mc2s + mc3a + mc4af;

	mfc3s = mc3s / mtot;
	mfc2s = mc2s / mtot;
	mfc3a = mc3a / mtot;
	mfc4af = mc4af / mtot;

	printf("***PHASE FRACTIONS***\n\n");
	printf("\tC3S:  By Volume: %f\tBy Mass: %f\n",vfc3s,mfc3s);
	printf("\tC2S:  By Volume: %f\tBy Mass: %f\n",vfc2s,mfc2s);
	printf("\tC3A:  By Volume: %f\tBy Mass: %f\n",vfc3a,mfc3a);
	printf("\tC4AF: By Volume: %f\tBy Mass: %f\n\n",vfc4af,mfc4af);

	printf("***PERIMETER FRACTIONS***\n\n");
	printf("\tC3S:  %f\n",pfc3s);
	printf("\tC2S:  %f\n",pfc2s);
	printf("\tC3A:  %f\n",pfc3a);
	printf("\tC4AF: %f\n\n",pfc4af);
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
	printf("\n\n***CONVERT VOLUME FRACTION TO MASS FRACTION***\n\n");
	return;
}
