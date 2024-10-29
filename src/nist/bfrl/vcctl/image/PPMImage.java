/*
 * PPMImage.java
 *
 * Created on February 15, 2006, 9:37 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.image;

import java.io.*;
import java.awt.image.BufferedImage;
import java.awt.Color;

/**
 *
 * @author tahall
 */
public class PPMImage {
    
    /** Creates a new instance of PPMImage */
    public PPMImage() {
    }
    
    static public BufferedImage read(File imfile) {
        /**
         * Open the file for reading
         */
        BufferedImage img = null;
        BufferedReader in = null;
        String fullPath = imfile.getAbsolutePath();
        try {
            in = new BufferedReader(new FileReader(fullPath));
        } catch (IOException iox) {
            return null;
        }
        
        String line;
        int xdim = 100;
        int ydim = 100;
        try {
            /**
             * Read the first three lines of the file, which contain the header
             * The second line contains the dimensions of the image.
             */
            for (int i=0; i<3; i++) {
                line = in.readLine();
                if (i == 1) {
                    line = line.trim();
                    String dim[] = line.split(" ");
                    xdim = Integer.parseInt(dim[0]);
                    ydim = Integer.parseInt(dim[1]);
                }
            }
            
            /**
             * Allocate the image
             */
            img = new BufferedImage(xdim, ydim, BufferedImage.TYPE_3BYTE_BGR);
            
            /**
             * Read in the pixels.  Each pixel is on a separate line.
             * Convert the line of text to an integer RGB value.
             */
            int rgb;
            for (int j=0; j<ydim; j++) {
                for (int i=0; i<xdim; i++) {
                    rgb = rgbPixelValue(in.readLine());
                    img.setRGB(i, j, rgb);
                }
            }
        } catch (IOException iox) {
            return null;
        } catch (NumberFormatException nfe) {
            // Error reading the image dimensions or pixel values
            return null;
        }
        
        return img;
    }
    
    static public int rgbPixelValue(String pixel) {
        int rgbval = 0;
        pixel = pixel.trim();
        String rgb[] = pixel.split(" ");

        /**
         * Convert the strings to integers, then get a single integer
         * RGB value using the Color class
         */
        try {
            int red = Integer.parseInt(rgb[0]);
            int green = Integer.parseInt(rgb[1]);
            int blue = Integer.parseInt(rgb[2]);
            
            rgbval = new Color(red, green, blue).getRGB();
        } catch (NumberFormatException nfe) {
            return Color.black.getRGB();
        }
        return rgbval;
    }
    
}
