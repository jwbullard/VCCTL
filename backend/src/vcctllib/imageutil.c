/******************************************************************************
 *	Collection of functions to help with creating microstructure
 *	images and movies
 *
 *       8 November 2013
 ******************************************************************************/
#include "../include/png.h"
#include "../include/vcctl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/******************************************************************************
 *	Function cemcolors assigns colors of cement paste phases into
 *	red, green, and blue channels passed to it.
 *
 * 	Arguments:	pointer to red array
 * 				pointer to green array
 * 				pointer to blue array
 *			integer gray (0 for color, 1 for grayscale);
 *
 *	Returns:	void
 *
 *	Programmer:	Jeffrey W. Bullard
 *				NIST
 *				100 Bureau Drive, Stop 8615
 *				Gaithersburg, Maryland  20899-8615
 *				USA
 *
 *				Phone:	301.975.5725
 *				Fax:	301.990.6891
 *				bullard@nist.gov
 *
 *	16 March 2004
 ******************************************************************************/
void cemcolors(int *red, int *green, int *blue, int gray) {
  register int i;
  int refgray = 250;

  if (gray) {
    for (i = 0; i < NPHASES; i++) {
      switch (i) {
      case FREELIME:
        red[i] = green[i] = blue[i] = (int)(refgray + 0.5);
        break;
      case C4AF:
        red[i] = green[i] = blue[i] = (int)(0.98 * refgray + 0.5);
        break;
      case C3S:
        red[i] = green[i] = blue[i] = (int)(0.88 * refgray + 0.5);
        break;
      case C2S:
        red[i] = green[i] = blue[i] = (int)(0.80 * refgray + 0.5);
        break;
      case K2SO4:
        red[i] = green[i] = blue[i] = (int)(0.80 * refgray + 0.5);
        break;
      case C3A:
        red[i] = green[i] = blue[i] = (int)(0.78 * refgray + 0.5);
        break;
      case FAC3A:
        red[i] = green[i] = blue[i] = (int)(0.78 * refgray + 0.5);
        break;
      case OC3A:
        red[i] = green[i] = blue[i] = (int)(0.75 * refgray + 0.5);
        break;
      case CAS2:
        red[i] = green[i] = blue[i] = (int)(0.708 * refgray + 0.5);
        break;
      case CH:
        red[i] = green[i] = blue[i] = (int)(0.743 * refgray + 0.5);
        break;
      case FH3:
        red[i] = green[i] = blue[i] = (int)(0.743 * refgray + 0.5);
        break;
      case INERTAGG:
        red[i] = green[i] = blue[i] = (int)(0.776 * refgray + 0.5);
        break;
      case SANDINCONCRETE:
        red[i] = green[i] = blue[i] = (int)(0.776 * refgray + 0.5);
        break;
      case ASG:
        red[i] = green[i] = blue[i] = (int)(0.708 * refgray + 0.5);
        break;
      case FLYASH:
        red[i] = green[i] = blue[i] = (int)(0.708 * refgray + 0.5);
        break;
      case ANHYDRITE:
        red[i] = green[i] = blue[i] = (int)(0.60 * refgray + 0.5);
        break;
      case HEMIHYD:
        red[i] = green[i] = blue[i] = (int)(0.56 * refgray + 0.5);
        break;
      case CSH:
        red[i] = green[i] = blue[i] = (int)(0.638 * refgray + 0.5);
        break;
      case POZZCSH:
        red[i] = green[i] = blue[i] = (int)(0.608 * refgray + 0.5);
        break;
      case SLAGCSH:
        red[i] = green[i] = blue[i] = (int)(0.608 * refgray + 0.5);
        break;
      case AFMC:
        red[i] = green[i] = blue[i] = (int)(0.560 * refgray + 0.5);
        break;
      case C3AH6:
        red[i] = green[i] = blue[i] = (int)(0.553 * refgray + 0.5);
        break;
      case GYPSUM:
        red[i] = green[i] = blue[i] = (int)(0.45 * refgray + 0.5);
        break;
      case ABSGYP:
        red[i] = green[i] = blue[i] = (int)(0.45 * refgray + 0.5);
        break;
      case GYPSUMS:
        red[i] = green[i] = blue[i] = (int)(0.45 * refgray + 0.5);
        break;
      case AFM:
        red[i] = green[i] = blue[i] = (int)(0.487 * refgray + 0.5);
        break;
      case STRAT:
        red[i] = green[i] = blue[i] = (int)(0.487 * refgray + 0.5);
        break;
      case SFUME:
        red[i] = green[i] = blue[i] = (int)(0.43 * refgray + 0.5);
        break;
      case AMSIL:
        red[i] = green[i] = blue[i] = (int)(0.43 * refgray + 0.5);
        break;
      case NA2SO4:
        red[i] = green[i] = blue[i] = (int)(0.432 * refgray + 0.5);
        break;
      case ETTR:
        red[i] = green[i] = blue[i] = (int)(0.422 * refgray + 0.5);
        break;
      case ETTRC4AF:
        red[i] = green[i] = blue[i] = (int)(0.422 * refgray + 0.5);
        break;
      case SLAG:
        red[i] = green[i] = blue[i] = (int)(0.40 * refgray + 0.5);
        break;
      case BRUCITE:
        red[i] = green[i] = blue[i] = (int)(0.330 * refgray + 0.5);
        break;
      case CACL2:
        red[i] = green[i] = blue[i] = (int)(0.330 * refgray + 0.5);
        break;
      case FRIEDEL:
        red[i] = green[i] = blue[i] = (int)(0.330 * refgray + 0.5);
        break;
      case CACO3:
        red[i] = green[i] = blue[i] = (int)(0.330 * refgray + 0.5);
        break;
      case MS:
        red[i] = green[i] = blue[i] = (int)(0.330 * refgray + 0.5);
        break;
      case INERT:
        red[i] = green[i] = blue[i] = (int)(0.50 * refgray + 0.5);
        break;
      case POROSITY:
        red[i] = green[i] = blue[i] = 0;
        break;
      case EMPTYP:
        red[i] = green[i] = blue[i] = (int)(0.0392 * refgray + 0.5);
        break;
      case EMPTYDP:
        red[i] = green[i] = blue[i] = (int)(0.0392 * refgray + 0.5);
        break;
      case DRIEDP:
        red[i] = green[i] = blue[i] = (int)(0.0392 * refgray + 0.5);
        break;
      default:
        red[i] = green[i] = blue[i] = 0;
      }
    }
  } else {
    for (i = 0; i < NPHASES; i++) {
      switch (i) {
      case POROSITY:
        red[i] = R_BLACK;
        green[i] = R_BLACK;
        blue[i] = R_BLACK;
        break;
      case EMPTYP:
        red[i] = R_CHARCOAL;
        green[i] = R_CHARCOAL;
        blue[i] = R_CHARCOAL;
        break;
      case EMPTYDP:
        red[i] = R_CHARCOAL;
        green[i] = R_CHARCOAL;
        blue[i] = R_CHARCOAL;
        break;
      case DRIEDP:
        red[i] = R_CHARCOAL;
        green[i] = R_CHARCOAL;
        blue[i] = R_CHARCOAL;
        break;
      case CH:
        red[i] = R_BLUE;
        green[i] = G_BLUE;
        blue[i] = B_BLUE;
        break;
      case CSH:
        red[i] = R_WHEAT;
        green[i] = G_WHEAT;
        blue[i] = B_WHEAT;
        break;
      case C3S:
        red[i] = R_BROWN;
        green[i] = G_BROWN;
        blue[i] = B_BROWN;
        break;
      case C2S:
        red[i] = R_CFBLUE;
        green[i] = G_CFBLUE;
        blue[i] = B_CFBLUE;
        break;
      case C3A:
        red[i] = R_GRAY;
        green[i] = G_GRAY;
        blue[i] = B_GRAY;
        break;
      case C4AF:
        red[i] = R_WHITE;
        green[i] = G_WHITE;
        blue[i] = B_WHITE;
        break;
      case K2SO4:
        red[i] = R_RED;
        green[i] = G_RED;
        blue[i] = B_RED;
        break;
      case NA2SO4:
        red[i] = R_SALMON;
        green[i] = G_SALMON;
        blue[i] = B_SALMON;
        break;
      case GYPSUM:
        red[i] = R_YELLOW;
        green[i] = G_YELLOW;
        blue[i] = B_YELLOW;
        break;
      case ABSGYP:
        red[i] = R_YELLOW;
        green[i] = G_YELLOW;
        blue[i] = B_YELLOW;
        break;
      case GYPSUMS:
        red[i] = R_YELLOW;
        green[i] = G_YELLOW;
        blue[i] = B_YELLOW;
        break;
      case HEMIHYD:
        red[i] = R_LYELLOW;
        green[i] = G_LYELLOW;
        blue[i] = B_LYELLOW;
        break;
      case ANHYDRITE:
        red[i] = R_GOLD;
        green[i] = G_GOLD;
        blue[i] = B_GOLD;
        break;
      case SFUME:
        red[i] = R_AQUA;
        green[i] = G_AQUA;
        blue[i] = B_AQUA;
        break;
      case AMSIL:
        red[i] = R_AQUA;
        green[i] = G_AQUA;
        blue[i] = B_AQUA;
        break;
      case INERT:
        red[i] = R_PLUM;
        green[i] = G_PLUM;
        blue[i] = B_PLUM;
        break;
      case ETTR:
        red[i] = R_LOLIVE;
        green[i] = G_LOLIVE;
        blue[i] = B_LOLIVE;
        break;
      case ETTRC4AF:
        red[i] = R_LOLIVE;
        green[i] = G_LOLIVE;
        blue[i] = B_LOLIVE;
        break;
      case AFM:
        red[i] = R_OLIVE;
        green[i] = G_OLIVE;
        blue[i] = B_OLIVE;
        break;
      case AFMC:
        red[i] = R_OLIVE;
        green[i] = G_OLIVE;
        blue[i] = B_OLIVE;
        break;
      case STRAT:
        red[i] = R_DOLIVE;
        green[i] = G_DOLIVE;
        blue[i] = B_DOLIVE;
        break;
      case CACL2:
        red[i] = R_PEACH;
        green[i] = G_PEACH;
        blue[i] = B_PEACH;
        break;
      case FRIEDEL:
        red[i] = R_MAGENTA;
        green[i] = G_MAGENTA;
        blue[i] = B_MAGENTA;
        break;
      case FH3:
        red[i] = R_DAQUA;
        green[i] = G_DAQUA;
        blue[i] = B_DAQUA;
        break;
      case POZZCSH:
        red[i] = R_LTURQUOISE;
        green[i] = G_LTURQUOISE;
        blue[i] = B_LTURQUOISE;
        break;
      case INERTAGG:
        red[i] = R_FIREBRICK;
        green[i] = G_FIREBRICK;
        blue[i] = B_FIREBRICK;
        break;
      case SANDINCONCRETE:
        red[i] = R_MUTEDFIREBRICK;
        green[i] = G_MUTEDFIREBRICK;
        blue[i] = B_MUTEDFIREBRICK;
        break;
      case COARSEAGG01INCONCRETE:
        red[i] = R_FIREBRICK;
        green[i] = G_FIREBRICK;
        blue[i] = B_FIREBRICK;
        break;
      case COARSEAGG02INCONCRETE:
        red[i] = R_MAGENTA;
        green[i] = G_MAGENTA;
        blue[i] = B_MAGENTA;
        break;
      case FINEAGG01INCONCRETE:
        red[i] = R_FIREBRICK;
        green[i] = G_FIREBRICK;
        blue[i] = B_FIREBRICK;
        break;
      case FINEAGG02INCONCRETE:
        red[i] = R_MAGENTA;
        green[i] = G_MAGENTA;
        blue[i] = B_MAGENTA;
        break;
      case CACO3:
        red[i] = R_LIME;
        green[i] = G_LIME;
        blue[i] = B_LIME;
        break;
      case FREELIME:
        red[i] = R_LLIME;
        green[i] = G_LLIME;
        blue[i] = B_LLIME;
        break;
      case FLYASH:
        red[i] = R_DGRAY;
        green[i] = G_DGRAY;
        blue[i] = B_DGRAY;
        break;
      case FAC3A:
        red[i] = R_GRAY;
        green[i] = G_GRAY;
        blue[i] = B_GRAY;
        break;
      case ASG:
        red[i] = R_ORANGE;
        green[i] = G_ORANGE;
        blue[i] = B_ORANGE;
        break;
      case SLAGCSH:
        red[i] = R_SEAGREEN;
        green[i] = G_SEAGREEN;
        blue[i] = B_SEAGREEN;
        break;
      case SLAG:
        red[i] = R_DGREEN;
        green[i] = G_DGREEN;
        blue[i] = B_DGREEN;
        break;
      case CAS2:
        red[i] = R_DBLUE;
        green[i] = G_DBLUE;
        blue[i] = B_DBLUE;
        break;
      case BRUCITE:
        red[i] = R_DLIME;
        green[i] = G_DLIME;
        blue[i] = B_DLIME;
        break;
      case MS:
        red[i] = R_ORANGERED;
        green[i] = G_ORANGERED;
        blue[i] = B_ORANGERED;
        break;
      default:
        red[i] = R_LAVENDER;
        green[i] = G_LAVENDER;
        blue[i] = B_LAVENDER;
      }
    }
  }

  return;
}

/******************************************************************************
 *	Function to return the pixel of a bitmap at a prescribed point (x,y)
 *
 * 	Arguments:	pointer to bitmap_t structure
 *			int x coordinate of point in bitmap
 * 			int y coordinate of point in bitmap
 *
 *	Returns:	pointer to pixel_t
 *
 *       This function is courtesy of Ben Bullock (ben.bullock@lemoda.net)
 *       For more information, visit http://www.lemoda.net/c/write-png/
 ******************************************************************************/
pixel_t *pixel_at(bitmap_t *bitmap, int x, int y) {
  return bitmap->pixels + bitmap->width * y + x;
}

/******************************************************************************
 *	Function to write a bitmap to a PNG file specified by path
 *
 * 	Arguments:	pointer to bitmap_t structure
 *			const char pointer to path string
 *
 *	Returns:	0 on success, non-zero on error
 *
 *       This function is courtesy of Ben Bullock (ben.bullock@lemoda.net)
 *       For more information, visit http://www.lemoda.net/c/write-png/
 ******************************************************************************/
int save_png_to_file(bitmap_t *bitmap, const char *path) {
  FILE *fp;
  png_structp png_ptr = NULL;
  png_infop info_ptr = NULL;
  size_t x, y;
  png_byte **row_pointers = NULL;

  /* "status" contains the return value of this function. At first
     it is set to a value which means 'failure'. When the routine
     has finished its work, it is set to a value which means
     'success'. */
  int status = -1;
  /* The following number is set by trial and error only. I cannot
     see where it it is documented in the libpng manual.
  */
  int pixel_size = 3;
  int depth = 8;

  fp = fopen(path, "wb");
  if (!fp) {
    goto fopen_failed;
  }

  png_ptr = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
  if (png_ptr == NULL) {
    goto png_create_write_struct_failed;
  }

  info_ptr = png_create_info_struct(png_ptr);
  if (info_ptr == NULL) {
    goto png_create_info_struct_failed;
  }

  /* Set up error handling. */

  if (setjmp(png_jmpbuf(png_ptr))) {
    goto png_failure;
  }

  /* Set image attributes. */

  png_set_IHDR(png_ptr, info_ptr, bitmap->width, bitmap->height, depth,
               PNG_COLOR_TYPE_RGB, PNG_INTERLACE_NONE,
               PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);

  /* Initialize rows of PNG. */

  row_pointers = png_malloc(png_ptr, bitmap->height * sizeof(png_byte *));
  for (y = 0; y < bitmap->height; ++y) {
    png_byte *row =
        png_malloc(png_ptr, sizeof(uint8_t) * bitmap->width * pixel_size);
    row_pointers[y] = row;
    for (x = 0; x < bitmap->width; ++x) {
      pixel_t *pixel = pixel_at(bitmap, x, y);
      *row++ = pixel->red;
      *row++ = pixel->green;
      *row++ = pixel->blue;
    }
  }

  /* Write the image data to "fp". */

  png_init_io(png_ptr, fp);
  png_set_rows(png_ptr, info_ptr, row_pointers);
  png_write_png(png_ptr, info_ptr, PNG_TRANSFORM_IDENTITY, NULL);

  /* The routine has successfully written the file, so we set
     "status" to a value which indicates success. */

  status = 0;

  for (y = 0; y < bitmap->height; y++) {
    png_free(png_ptr, row_pointers[y]);
  }
  png_free(png_ptr, row_pointers);

png_failure:
png_create_info_struct_failed:
  png_destroy_write_struct(&png_ptr, &info_ptr);
png_create_write_struct_failed:
  fclose(fp);
fopen_failed:
  return status;
}
