#include <stdio.h>
#include <math.h>

main(){
	int i,j,k,partdiam;
	float partvol[100],massfrac[100],volfrac[100];
	float totmass,totvol,partmass;
	FILE *infile,*outfile;
	char filein[80],fileout[80],str1[80],str2[80];

	for(i=0;i<100;i++){
		partvol[i]=0.0;
		massfrac[i]=0.0;
		volfrac[i]=0.0;
	}

	partvol[1]=1.0;
	partvol[3]=19.;
	partvol[5]=81.;
	partvol[7]=179.;
	partvol[9]=389.;
	partvol[11]=739.;
	partvol[13]=1189.;
	partvol[15]=1791.;
	partvol[17]=2553.;
	partvol[19]=3695.;
	partvol[21]=4945.;
	partvol[23]=6403.;
	partvol[25]=8217.;
	partvol[27]=10395.;
	partvol[29]=12893.;
	partvol[31]=15515.;
	partvol[33]=18853.;
	partvol[35]=22575.;
	partvol[37]=26745.;
	partvol[39]=31103.;
	partvol[41]=36137.;
	partvol[47]=54435.;
	partvol[61]=119009.;
	partvol[73]=203965.;
	partvol[87]=345243.;

	printf("Enter name of file with the raw PSD \n");
	scanf("%s",filein);
	printf("%s\n",filein);
	infile=fopen(filein,"r");
	fscanf(infile,"%s %s",str1,str2);

	printf("Enter name of file for output\n");
	scanf("%s",fileout);
	printf("%s\n",fileout);
	outfile=fopen(fileout,"w");
	fprintf(outfile,"%s %s Part_vol  Number_frac\n",str1,str2);

	totvol=0.0;
	totmass=0.0;
	while(!feof(infile)){
		fscanf(infile,"%d %f",&partdiam,&partmass);
		if (!feof(infile)) {
			if(partvol[partdiam]==0.0){
				printf("error for particle size %d \n",partdiam);
				exit(1);
			}
			massfrac[partdiam]=partmass;
			totmass+=partmass;
			volfrac[partdiam]=partmass/partvol[partdiam];
			totvol+=partmass/partvol[partdiam];
			printf("partdiam = %d, total mass = %f\n",partdiam,totmass);
		}
	}

	printf("total mass and volume are %f and %f \n",totmass,totvol);


	for(i=0;i<100;i++){
		volfrac[i]/=totvol;
		if(massfrac[i]!=0.0){
			fprintf(outfile,"%d  %f  %.0f  %f\n",i,massfrac[i],partvol[i],volfrac[i]);
		}
	}

	fclose(outfile);
	fclose(infile);
}
