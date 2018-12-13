/*
 * MicrostructureMovie.java
 *
 * Created on November 6, 2013, 11:47 AM
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
 * @author bullard
 */
public class MicrostructureMovie {
    
    static public MicrostructureMovie INSTANCE = new MicrostructureMovie();
    
    static private String current_movie_name = "current-movie.gif";
    
    /** Creates a new instance of MicrostructureMovie */
    protected MicrostructureMovie() {
    }
    
    private String getCurrentMoviePath() {
        String path = Vcctl.getImageDirectory()+current_movie_name;
        
        return path;
    }
    
    public void setBlankMovie() {
        String moviePath = getCurrentMoviePath();
        // Delete any instance of 'current-movie.gif'
        File fpng = new File(moviePath);
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
            ImageIO.write(bi, "gif", new File(moviePath));
        } catch (IOException iox) {
            iox.printStackTrace();
        }
    }
    
    public String createMovie(String userName, String operationName,
            String movieName,
            int plane,
            int magnification) {
        /**
         * Delete movie
         **/
        
        String moviepath = Vcctl.getImageDirectory() + movieName;
        File movieFile = new File(moviepath);
        if (movieFile.exists()) {
            movieFile.delete();
        }
        
        
        if (magnification < 1) {
            magnification = 1;
        } else if (magnification > 10) {
            magnification = 10;
        }
        
        /**
         * The operation name is the same as the 3-D image name
         */
        String inpath = ServerFile.getUserOperationDir(userName, operationName);
        inpath += movieName;
        
        /**
         * Create a file name for this movie
         */
        
        //String pngfilename = current_slice_name;
        String gifrootname = movieName+"."+Integer.toString(plane)
        + ".x" + Integer.toString(magnification);
        String giffilename = movieName+"."+Integer.toString(plane)
        + ".x" + Integer.toString(magnification)
        + ".gif";
        String gifoutpath = Vcctl.getImageDirectory() + giffilename;
        String gifrootpath = Vcctl.getImageDirectory() + gifrootname;

        // Make sure that current file is deleted
        boolean success = new File(gifoutpath).delete();
        
        String intext = inpath + '\n' +
                gifrootpath + '\n' +
                Integer.toString(plane) + '\n' +
                Integer.toString(magnification) + '\n';
        
        ServerFile.writeUserOpTextFile(userName, operationName, "image100.input", intext);
        /**
         * Execute the command and get the output
         **/
        String dir = Vcctl.getBinDirectory();
        String command = dir + "image100";
        
        ProcessBuilder pb = new ProcessBuilder(command);
        String opdir = ServerFile.getUserOperationDir(userName, operationName);
        pb.directory(new File(opdir));
        
        // Write input to image100
        Process child = null;
        try {
            child = pb.start();
            OutputStream out = child.getOutputStream();
            out.write(intext.getBytes());
            out.close();
        } catch (IOException iox) {
            
        }
        
        // Capture image100 output
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
        ServerFile.writeUserOpTextFile(userName, operationName, "image100.output", outtext.toString());
        
        return giffilename;
    }
    
}