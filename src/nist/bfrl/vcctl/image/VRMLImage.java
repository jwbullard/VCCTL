/*
 * To change this template, choose Tools | Templates
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
public class VRMLImage {
    static public VRMLImage INSTANCE = new VRMLImage();

    static private String current_vrml_name = "current-vrml.vrml";

    /** Creates a new instance of VRMLImage */
    protected VRMLImage() {
    }

    private String getCurrentVRMLPath() {
        String path = Vcctl.getImageDirectory()+current_vrml_name;

        return path;
    }

    public void setBlankVRML() {
        String vrmlPath = getCurrentVRMLPath();
        // Delete any instance of 'current-vrml.vrml'
        File fvrml = new File(vrmlPath);
        if (fvrml.exists()) {
            fvrml.delete();
        }

        /*
         * Create a blank VRML image
         * Still needs to be done
         */

        int black = new Color(0, 0, 0).getRGB();
        try {
            BufferedImage bi = new BufferedImage(1, 1, BufferedImage.TYPE_INT_ARGB);
            bi.setRGB(0, 0, black);
            ImageIO.write(bi, "png", new File(vrmlPath));
        } catch (IOException iox) {
            iox.printStackTrace();
        }
    }

    public String createVRML(String userName, String operationName,
            String imageName, int upperx, int uppery, int upperz) {
        /**
         * Delete slice
         **/

        String vrmlpath = Vcctl.getImageDirectory() + imageName;
        File vrmlFile = new File(vrmlpath);
        if (vrmlFile.exists()) {
            vrmlFile.delete();
        }

        /**
         * The operation name is the same as the 3-D image name
         */
        String inpath = ServerFile.getUserOperationDir(userName, operationName);
        inpath += imageName;

        /**
         * Create a file name for this VRML file
         */

        String vrmlfilename = imageName+"." + ".vrml";
        String vrmloutpath = Vcctl.getImageDirectory();
        if (!vrmloutpath.endsWith(File.separator)) {
            vrmloutpath = vrmloutpath + File.separator;
        }

        // Make sure that current file is deleted
        // boolean success = new File(vrmloutpath).delete();

        String intext = inpath + '\n' +
                vrmloutpath + '\n' + '1' + '\n' +
                '0' + '\n' + Integer.toString(upperx) + '\n' +
                '0' + '\n' + Integer.toString(uppery) + '\n' +
                '0' + '\n' + Integer.toString(upperz);

        ServerFile.writeUserOpTextFile(userName, operationName, "packvrml.input", intext);
        /**
         * Execute the command and get the output
         **/
        String dir = Vcctl.getBinDirectory();
        String command = dir + "packvrml";

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
        ServerFile.writeUserOpTextFile(userName, operationName, "packvrml.output", outtext.toString());

        /**
         * Image written out is true VRML file.  No conversion necessary
         */
        // BufferedImage image = null;
        // File ppmfile = new File(ppmoutpath);
        // byte[] sliceBytes = null;
        // try {
        //     image = PPMImage.read(ppmfile);
        //     ImageIO.write(image, "png", new File(pngoutpath));
        // } catch (IOException iox) {
            // Do nothing
        // }
        // ppmfile.delete();

        return vrmlfilename;
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
