/*
 * HydrationMovie.java
 *
 * Created on November 6, 2013, 12:47 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.image;

import java.io.*;
import java.io.File;
import java.awt.image.BufferedImage;
import java.awt.Color;
import javax.imageio.*;
import javax.imageio.stream.ImageOutputStream;
import javax.imageio.stream.FileImageOutputStream;
import org.apache.commons.io.FileUtils;
import nist.bfrl.vcctl.application.Vcctl;
import nist.bfrl.vcctl.util.ServerFile;
import nist.bfrl.vcctl.util.UserDirectory;
import nist.bfrl.vcctl.image.GifSequenceWriter;

/**
 *
 * @author bullard
 */
public class HydrationMovie {
    
    static public HydrationMovie INSTANCE = new HydrationMovie();
    
    static private String current_movie_name = "current-movie.gif";
    
    /** Creates a new instance of HydrationMovie */
    protected HydrationMovie() {
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
            String movieName, int bse,
            int magnification, double framespeed) throws IOException {
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
        
        String gifrootname = movieName
        + ".x" + Integer.toString(magnification)
        + "." + Integer.toString(bse);
        String giffilename = movieName
        + ".x" + Integer.toString(magnification)
        + "." + Integer.toString(bse)
        + ".gif";
        String gifoutpath = Vcctl.getImageDirectory() + giffilename;
        String gifrootpath = Vcctl.getImageDirectory() + gifrootname;

        // Make sure that current file is deleted
        boolean success = new File(gifoutpath).delete();
        
        String intext = inpath + '\n' +
                gifoutpath + '\n' +
                Integer.toString(bse) + '\n' +
                Integer.toString(magnification) + '\n';
        
        ServerFile.writeUserOpTextFile(userName, operationName, "hydmovie.input", intext);
        /**
         * Execute the command and get the output
         **/
        String dir = Vcctl.getBinDirectory();
        String command = dir + "hydmovie";
        
        ProcessBuilder pb = new ProcessBuilder(command);
        String opdir = ServerFile.getUserOperationDir(userName, operationName);
        pb.directory(new File(opdir));
        
        // Write input to hydmovie
        Process child = null;
        try {
            child = pb.start();
            OutputStream out = child.getOutputStream();
            out.write(intext.getBytes());
            out.close();
        } catch (IOException iox) {
            
        }
        
        // Capture hydmovie output
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
            String msg = iox.getMessage();
            System.out.println(msg);
        }
        ServerFile.writeUserOpTextFile(userName, operationName, "hydmovie.output", outtext.toString());
        
        inpath = ServerFile.getUserOperationDir(userName, operationName);
        File folder = new File(inpath);
        String[] existingpngfiles = folder.list(new FilenameFilter() {
            public boolean accept(File folder, String name) {
                return name.toLowerCase().endsWith(".png");
            }
        });
        
        /* prepend the path to the file names */
        for (int i = 0; i < existingpngfiles.length; i++) {
            existingpngfiles[i] = inpath + existingpngfiles[i];
        }

        // grab the output image type from the first image in the sequence
        File firstpngfile = new File(existingpngfiles[0]);
        BufferedImage firstImage = null;
        try {
            firstImage = ImageIO.read(firstpngfile);
        }
        catch (IOException iox) {
            String msg = iox.getMessage();
            System.out.println(msg);
        }

        // create a new BufferedOutputStream with the last argument
        gifoutpath = Vcctl.getImageDirectory() + giffilename;
        ImageOutputStream output =
              new FileImageOutputStream(new File(gifoutpath));

        // create a gif sequence with the type of the first image, 1 second
        // between frames, which loops continuously

        GifSequenceWriter writer = null;
        try {
            if (framespeed <= 0.0) framespeed = 0.1;
            int timebetweenframes = (int)(1000.0/framespeed);
            writer = new GifSequenceWriter(output, firstImage.getType(), timebetweenframes, false);
        }
        catch (IOException iox) {
            String msg = iox.getMessage();
            System.out.println(msg);
        }

        // write out the first image to our sequence...
        writer.writeToSequence(firstImage);
        for(int i=1; i<existingpngfiles.length; i++) {
            BufferedImage nextImage = ImageIO.read(new File(existingpngfiles[i]));
            writer.writeToSequence(nextImage);
        }

        writer.close();
        output.close();
        
        /* Now delete all the png files we just made form the operation directory */
        final File[] allpngfiles = folder.listFiles(new FilenameFilter() {
            public boolean accept(File folder, String name) {
                return name.toLowerCase().endsWith(".png");
            }
        });

        for ( final File file : allpngfiles ) {
            if ( !file.delete() ) {
                System.err.println( "Can't remove " + file.getAbsolutePath() );
            }
        }

        return giffilename;
    }
    
}