/******************************************************************
*	Declarations of functions in the vcctl library.
*	Note that all functions related to complex numbers
*	have their own header file (called vcctlcomplex.h) and
*	all the library functions themselves are self-contained in the
*	source code complex.c
*
*	Programmer:	Jeffrey W. Bullard
*				NIST
*				100 Bureau Drive Stop 8615
*				Gaithersburg, MD  20899 USA
*
*				301.975.5725
*				bullard@nist.gov
*
*	23 March 2004
******************************************************************/
void bailout(char *name, char *msg);
void warning(char *name, char *msg);
int breakflocs(FILE *pfile, short int *p, short int *part, short int *in,
short int *jn, short int *kn, int xsize, int ysize, int zsize,
float version, float resol);
int calcporedist3d(char *name);
void cemcolors(int *r, int *g, int *b, int gray);
int checkbc(int pos, int size);
int convert_id(int curid, float version);
long int diam2vol(float diameter);
void id2phasename(int curid, char *phasename);
FILE *filehandler(char *prog, char *filename, char *tocheck);
void fread_string(FILE *fpin, char *chstr);
double mediansize(FILE *fpin);
void messages();
char *gtime(void);
int *ivector(size_t size);
short int *sivector(size_t size);
long int *livector(size_t size);
float *fvector(size_t size);
double *dvector(size_t size);
long double *ldvector(size_t size);
pixel_t *pixelvector(size_t size);
short int **sisquare(size_t size);
short int **sirect(size_t xsize, size_t ysize);
int **irect(size_t xsize, size_t ysize);
double **drect(size_t xsize, size_t ysize);
char ***ccube(size_t size);
char ***cbox(size_t xsize, size_t ysize, size_t zsize);
short int ***sicube(size_t size);
short int ***sibox(size_t xsize, size_t ysize, size_t zsize);
float ***fcube(size_t size);
float ***fbox(size_t xsize, size_t ysize, size_t zsize);
double ***dbox(size_t xsize, size_t ysize, size_t zsize);
int ***icube(size_t size);
int ***ibox(size_t xsize, size_t ysize, size_t zsize);
int Int3darray(Int3d *thing, size_t xsize, size_t ysize, size_t zsize);
size_t getInt3dindex(Int3d thing, size_t x, size_t y, size_t z);
unsigned short int ***usicube(size_t size);
unsigned short int ***usibox(size_t xsize, size_t ysize, size_t zsize);
void free_fvector(float *fv);
void free_dvector(double *dv);
void free_ldvector(long double *ldv);
void free_pixelvector(pixel_t *ptv);
void free_ivector(int *iv);
void free_sivector(short int *iv);
void free_livector(long int *iv);
void free_sicube(short int ***fc,size_t size);
void free_sibox(short int ***fc,size_t xsize,size_t ysize);
void free_ccube(char ***fc,size_t size);
void free_cbox(char ***fc,size_t xsize,size_t ysize);
void free_fcube(float ***fc,size_t size);
void free_fbox(float ***fc,size_t xsize,size_t ysize);
void free_dbox(double ***fc,size_t xsize,size_t ysize);
void free_icube(int ***fc,size_t size);
void free_ibox(int ***fc,size_t xsize,size_t ysize);
void free_Int3darray(Int3d *thing);
void free_usicube(unsigned short int ***fc,size_t size);
void free_usibox(unsigned short int ***fc,size_t xsize,size_t ysize);
void free_sisquare(short int **is,size_t size);
void free_sirect(short int **is,size_t xsize);
void free_irect(int **is,size_t xsize);
void free_drect(double **is,size_t xsize);
int probe_imgheader(char *name, float *ver, int *xsize, int *ysize,
	int *zsize, float *res);
double ran1(int *idum);
int read_imgheader(FILE *fpin, float *ver, int *xsize, int *ysize,
	int *zsize, float *res);
void read_string(char *chstr, long unsigned int size);
void skip_imgheader(FILE *fpin);
int write_imgheader(FILE *fpout, int xsize, int ysize,
	int zsize, float res);
pixel_t *pixel_at(bitmap_t * bitmap, int x, int y);
int save_png_to_file (bitmap_t *bitmap, const char *path);

