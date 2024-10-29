/*
 * Util.java
 *
 * Created on June 14, 2005, 2:29 PM
 */

package nist.bfrl.vcctl.util;

import java.io.*;
import java.security.*;
import java.text.ParseException;
import java.util.*;
import java.util.zip.*;
import java.util.Date;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.text.NumberFormat;
import java.util.Locale;

/**
 *
 * @author tahall
 */
public class Util {
    
    
    /**
     * Given a File, return the file data in a byte array
     */
    public static byte[] getBytesFromFile(File file) throws IOException {
        InputStream is = new FileInputStream(file);
        
        // Get the size of the file
        long length = file.length();
        
        // You cannot create an array using a long type.
        // It needs to be an int type.
        // Before converting to an int type, check
        // to ensure that file is not larger than Integer.MAX_VALUE.
        if (length > Integer.MAX_VALUE) {
            // File is too large
        }
        
        // Create the byte array to hold the data
        byte[] bytes = new byte[(int)length];
        
        // Read in the bytes
        int offset = 0;
        int numRead = 0;
        while (offset < bytes.length
                && (numRead=is.read(bytes, offset, bytes.length-offset)) >= 0) {
            offset += numRead;
        }
        
        // Ensure all the bytes have been read in
        if (offset < bytes.length) {
            throw new IOException("Could not completely read file "+file.getName());
        }
        
        // Close the input stream and return bytes
        is.close();
        return bytes;
    }
    
    public static int SECONDS_PER_HOUR = 60*60;
    public static int SECONDS_PER_DAY = 60*60*24;
    
    public static String elapsed_time(long seconds) {
        long days = seconds / SECONDS_PER_DAY;
        seconds -= (days * SECONDS_PER_DAY);
        long hours = seconds / SECONDS_PER_HOUR;
        seconds -= (hours * SECONDS_PER_HOUR);
        
        String et = Long.toString(days)+"d "+ Long.toString(hours)+"h "+ Long.toString(seconds)+"s";
        
        return et;
    }
    
    /*
     * Method to copy a file
     */
    public static void copy (String source, String destination)	{
	try {
	    // Préparation du flux d'entrée
	    File sourceFile = new File(source);
	    FileInputStream fis = new FileInputStream(sourceFile);
	    BufferedInputStream bis = new BufferedInputStream(fis);
	    long l = sourceFile.length();

	    // Préparation du flux de sortie
	    FileOutputStream fos = new FileOutputStream(destination);
            BufferedOutputStream bos = new BufferedOutputStream(fos);

	    // Copie des octets du flux d'entrée vers le flux de sortie
	    for(long i=0;i<l;i++) {
                bos.write(bis.read());
	    }

	    // Fermeture des flux de données
	    bos.flush();
	    bos.close();
	    bis.close();

	} catch (Exception e) {
	    System.err.println("File access error !");
	    e.printStackTrace();
	}

	System.out.println("Copy done");
    }

    // The following method does not work, perhaps because the File arguments
    // end with a file separator?  Must debug.  I know that the target location
    // directory is NOT being created as implied by the targetLocation.mkdir()
    // command

    public static void copyDirectory(File sourceLocation , File targetLocation)
    throws IOException {

        if (sourceLocation.isDirectory()) {
            if (!targetLocation.exists()) {
                targetLocation.mkdirs();
            }

            String[] children = sourceLocation.list();
            for (int i=0; i<children.length; i++) {
                copyDirectory(new File(sourceLocation, children[i]),
                        new File(targetLocation, children[i]));
            }
        } else {

            InputStream in = new FileInputStream(sourceLocation);
            OutputStream out = new FileOutputStream(targetLocation);

            // Copy the bits from instream to outstream
            byte[] buf = new byte[1024];
            int len;
            while ((len = in.read(buf)) > 0) {
                out.write(buf, 0, len);
            }
            in.close();
            out.close();
        }
    }

    public static int searchStringInArray(String string, String[]array) {
        for (int i = 0; i < array.length; i++) {
            if (array[i].equalsIgnoreCase(string))
                return i;
        }
        return -1;
    }
    
    public static double round(double number, int rounding) {
        return ((double)Math.round(number * Math.pow(10,rounding)))/Math.pow(10,rounding);
    }
    
    /*
     * Hash the string given in paramater
     * @param key : the string to be hashed
     * @return the hashed string
     */
    
    public static String hash(String key) {
        byte[] uniqueKey = key.getBytes();
        byte[] hash = null;
        
        try {
            hash = MessageDigest.getInstance("MD5").digest(uniqueKey);
        }
        
        catch (NoSuchAlgorithmException e) {
            throw new Error("no MD5 support in this VM");
        }
        
        StringBuffer hashString = new StringBuffer();
        
        for (int i = 0; i < hash.length; ++i) {
            String hex = Integer.toHexString(hash[i]);
            if (hex.length() == 1) {
                hashString.append('0');
                hashString.append(hex.charAt(hex.length() - 1));
            } else {
                hashString.append(hex.substring(hex.length() - 2));
            }
        }
        
        return hashString.toString();
        
    }
    
    /*
     * Test une chaine et une valeur encodée (chaine hexadécimale)
     * @param clearTextTestPassword : la chaine non codée à tester
     * @param encodedActualPassword : la valeur hexa MD5 de référence
     * @return true si vérifié false sinon
     */
    public static boolean testPassword(String clearTextTestPassword, String encodedActualPassword) throws NoSuchAlgorithmException {
        String encodedTestPassword = hash(clearTextTestPassword);
        
        return (encodedTestPassword.equals(encodedActualPassword));
    }

    /*
     * Get the current date and time in format to insert into database
     */

    public static String currentDateTime() {
        DateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        Date date = new Date();
        return dateFormat.format(date);
    }

    public static double stringToDouble(String strval) throws ParseException {
        NumberFormat fmt = NumberFormat.getInstance();
        Number number = fmt.parse(strval);
        double dValue = number.doubleValue();
        return (dValue);
    }
    /**
     * @return a Properties object containing the environment variables and their associated values.
     * @throws Throwable if an execption occurs.
     */
    /*
    public static java.util.Properties getEnvironment()  {
        
        
        Process p = null;
        java.util.Properties envVars = new java.util.Properties();
        Runtime r = Runtime.getRuntime();
        String OS = System.getProperty("os.name").toLowerCase();
        try {
            // Get the Windows 95 environment variables
            if (OS.indexOf("windows 9") > -1) {
                p = r.exec( "command.com /c set" );
            }
            // Get the Windows NT environment variables
            else if (OS.indexOf("nt") > -1) {
                p = r.exec( "cmd.exe /c set" );
            }
            // Get the Windows 2000 environment variables
            else if (OS.indexOf("2000") > -1) {
                p = r.exec( "cmd.exe /c set" );
            }
            // Get the Windows XP environment variables
            else if (OS.indexOf("xp") > -1) {
                p = r.exec( "cmd.exe /c set" );
            }
            // Get the unix environment variables
            else if (OS.indexOf("mac os x") > -1) {
                p = r.exec( "env" );
            }
            // Get the unix environment variables
            else if (OS.indexOf("linux") > -1) {
                p = r.exec( "env" );
            }
            // Get the unix environment variables
            else if (OS.indexOf("unix") > -1) {
                p = r.exec( "/bin/env" );
            }
            // Get the unix environment variables
            else if (OS.indexOf("sunos") > -1) {
                p = r.exec( "/bin/env" );
            } else  {
                System.out.println("OS not known: " + OS);
            }
        } catch (java.io.IOException e) {
            e.printStackTrace();
        }
        java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(p.getInputStream()));
        String line;
        try {
            int idx;
            String key, value;
            while( (line = br.readLine()) != null ) {
                idx = line.indexOf('=');
                // if there is no equals sign on the line skip to the net line
                // this occurs when there are newline characters in the environment variable
                // 
                if (idx < 0) continue;
                
                key = line.substring( 0, idx );
                value = line.substring( idx+1 );
                envVars.setProperty( key, value );
            }
        } catch (java.io.IOException e) {
            e.printStackTrace();
        }
        return envVars;
    }
     * */
}
