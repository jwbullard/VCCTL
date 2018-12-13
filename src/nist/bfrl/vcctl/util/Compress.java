/*
 * Compress.java
 *
 * Created on June 21, 2005, 11:31 AM
 */

package nist.bfrl.vcctl.util;

import java.io.*;
import java.util.zip.*;

/**
 *
 * @author tahall
 */
public class Compress {
    
    /** Creates a new instance of Compress */
    public Compress() {
    }
    
    static public boolean imgCompress(String imgname, String pimgname) {
        boolean success = true;
        
        return success;
    }
    
    public static byte[] gunzipBytes(byte[] gzippedBytes) {
        
        byte[] decompressedData = null;
        
        try {
            GZIPInputStream in = new GZIPInputStream(new ByteArrayInputStream(gzippedBytes));
            
            // Create an expandable byte array to hold the decompressed data
            ByteArrayOutputStream out = new ByteArrayOutputStream(gzippedBytes.length);
            
            // Decompress the data
            byte[] buf = new byte[1024];
            int len;
            while ((len = in.read(buf)) > 0) {
                out.write(buf, 0, len);
            }
            
            // Get the decompressed data
            decompressedData = out.toByteArray();
            
            in.close();
            out.close();
        } catch (IOException iox) {
            throw new RuntimeException(iox);
        }
        
        return decompressedData;
    }
    
    public static boolean gunzipFile(String inFilename, String outFilename) {
        boolean success = true;
        
        try {
            // Open the compressed file
            GZIPInputStream in = new GZIPInputStream(new FileInputStream(inFilename));
            
            // Open the output file
            OutputStream out = new FileOutputStream(outFilename);
            
            // Transfer bytes from the compressed file to the output file
            byte[] buf = new byte[1024];
            int len;
            while ((len = in.read(buf)) > 0) {
                out.write(buf, 0, len);
            }
            
            // Close the file and stream
            in.close();
            out.close();
        } catch (IOException e) {
            success = false;
        }
        
        return success;
    }
    
    public static boolean gzipFile(String inFilename, String outFilename) {
        
        boolean success = true;
        
        try {
            // Create the GZIP output stream
            GZIPOutputStream out = new GZIPOutputStream(new FileOutputStream(outFilename));
            
            // Open the input file
            FileInputStream in = new FileInputStream(inFilename);
            
            // Transfer bytes from the input file to the GZIP output stream
            byte[] buf = new byte[1024];
            int len;
            while ((len = in.read(buf)) > 0) {
                out.write(buf, 0, len);
            }
            in.close();
            
            // Complete the GZIP file
            out.finish();
            out.close();
        } catch (IOException e) {
            success = false;
        }
        
        return success;
    }
    
}
