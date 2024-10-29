/*
 * ImageSlice.java
 *
 * Created on February 13, 2006, 4:52 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.image;

import java.io.*;
import java.awt.image.BufferedImage;
import java.awt.Color;
import javax.imageio.*;

import nist.bfrl.vcctl.application.Vcctl;
import nist.bfrl.vcctl.util.ServerFile;
import nist.bfrl.vcctl.util.UserDirectory;

/**
 *
 * @author tahall
 */
public class ImageSlice {
    
    static public ImageSlice INSTANCE = new ImageSlice();
    
    static private String current_slice_name = "current-slice.png";
    
    /** Creates a new instance of ImageSlice */
    protected ImageSlice() {
    }
    
    private String getCurrentSlicePath() {
        String path = Vcctl.getImageDirectory()+current_slice_name;
        
        return path;
    }
    
    public void setBlankSlice() {
        String slicePath = getCurrentSlicePath();
        // Delete any instance of 'current-slice.png'
        File fpng = new File(slicePath);
        if (fpng.exists()) {
            fpng.delete();
        }
        
        /*
         * Create a 1x1 image of all-black pixels
         */
        int black = new Color(0, 0, 0).getRGB();
        try {
            BufferedImage bi = new BufferedImage(1, 1, BufferedImage.TYPE_INT_ARGB);
            bi.setRGB(0, 0, black);
            ImageIO.write(bi, "png", new File(slicePath));
        } catch (IOException iox) {
            iox.printStackTrace();
        }
    }
    
    public String createSlice(String userName, String operationName,
            String imageName,
            int plane,
            int sliceNumber,
            int viewdepth,
            int bse,
            int magnification) {
        
        /**
         * Delete slice
         **/
        
        String slicepath = Vcctl.getImageDirectory() + imageName;
        File sliceFile = new File(slicepath);
        if (sliceFile.exists()) {
            sliceFile.delete();
        }
        
        sliceNumber = correctSlice(sliceNumber, plane, userName, operationName, imageName);
        
        
        if (magnification < 1) {
            magnification = 1;
        } else if (magnification > 10) {
            magnification = 10;
        }
        
        /**
         * The operation name is the same as the 3-D image name
         */
        String inpath = ServerFile.getUserOperationDir(userName, operationName);
        inpath += imageName;
        
        /**
         * Create a file name for this slice
         */
        
        //String pngfilename = current_slice_name;
        String pngfilename = imageName + "." + Integer.toString(plane)
        + "." + Integer.toString(sliceNumber)
        + ".x" + Integer.toString(magnification)
        + "." + Integer.toString(viewdepth)
        + "." + Integer.toString(bse)
        + ".png";
        String pngoutpath = Vcctl.getImageDirectory() + pngfilename;
        
        // Make sure that current file is deleted
        boolean success = new File(pngoutpath).delete();
        
        String intext = inpath + '\n' +
                pngoutpath + '\n' +
                Integer.toString(plane) + '\n' +
                Integer.toString(sliceNumber) + '\n' +
                Integer.toString(viewdepth) + '\n' +
                Integer.toString(bse) + '\n' +
                Integer.toString(magnification);
        
        ServerFile.writeUserOpTextFile(userName, operationName, "oneimage.input", intext);
        /**
         * Execute the command and get the output
         **/
        String dir = Vcctl.getBinDirectory();
        String command = dir + "oneimage";
        
        ProcessBuilder pb = new ProcessBuilder(command);
        String opdir = ServerFile.getUserOperationDir(userName, operationName);
        pb.directory(new File(opdir));
        
        // Write input to oneimage
        Process child = null;
        try {
            child = pb.start();
            OutputStream out = child.getOutputStream();
            out.write(intext.getBytes());
            out.close();
        } catch (IOException iox) {
            
        }
        
        // Capture oneimage output
        InputStream in = child.getInputStream();
        StringBuffer outtext = new StringBuffer("");
        try {
            if (in != null) {
                BufferedReader reader = new BufferedReader(new InputStreamReader(in));
                String line = reader.readLine();
                while ((line != null)) {
                    outtext.append(line).append("\n");
                    line = reader.readLine();
                }
            }
        } catch (IOException iox) {
            // Do nothing
        }
        ServerFile.writeUserOpTextFile(userName, operationName, "oneimage.output", outtext.toString());
        
        
        return pngfilename;
    }
    
    /**
     * Get the operation state data in order to check the range of
     * acceptable values for 'slice' and return the correct value
     */
    public static int correctSlice(int sliceNumber, int plane, String userName, String operationName, String imageName) {
        
        /**
         * Get the operation state data in order to check the range of
         * acceptable values for 'slice'
         */
        
        UserDirectory userDir = new UserDirectory(userName);
        String imagePath = userDir.getOperationFilePath(operationName, imageName);
        String smax_x = "";
        String smax_y = "";
        String smax_z = "";
        try {
            BufferedReader in = new BufferedReader(new FileReader(imagePath));
            String line;
            String[] elem;
            for (int i=0; i<4; i++) {
                line = in.readLine();
                elem = line.split(" ");
                if (i == 1) {
                    smax_x = elem[1].trim();
                } else if (i ==2) {
                    smax_y = elem[1].trim();
                } else if (i == 3) {
                    smax_z = elem[1].trim();
                }
            }
            in.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
        
        /**
         * Convert slice from a string to an integer
         * within bounds
         */
        int max_z = 99;
        int max_x = 99;
        int max_y = 99;
        try {
            max_x = Integer.parseInt(smax_x) - 1;
            max_y = Integer.parseInt(smax_y) - 1;
            max_z = Integer.parseInt(smax_z) - 1;
        } catch (NumberFormatException nfe) {
            nfe.printStackTrace();
        }
        
        /**
         * Check the bounds:
         */
        if (sliceNumber < 0) {
            sliceNumber = 0;
        }
        if (plane == 1) {
            if (sliceNumber > max_z) {
                sliceNumber = max_z;
            }
        } else if (plane == 2) {
            if (sliceNumber > max_y) {
                sliceNumber = max_y;
            }
        } else {
            if (sliceNumber > max_x) {
                sliceNumber = max_x;
            }
        }
        return sliceNumber;
    }
}