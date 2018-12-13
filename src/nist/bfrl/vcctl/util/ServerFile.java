/*
 * ServerFile.java
 *
 * Created on August 12, 2005, 11:00 AM
 */

package nist.bfrl.vcctl.util;

import java.io.*;

/**
 *
 * @author tahall
 */
public class ServerFile {
    
    /** Creates a new instance of ServerFile */
    public ServerFile() {
    }
    
    static public boolean saveToFile(String path, byte[] data) {
        boolean success = false;
        try {
            File file = new File(path);
            if (file.exists()) {
                file.delete();
            }
            success = file.createNewFile();
            // file.deleteOnExit();
            FileOutputStream out = new FileOutputStream(file);
            out.write(data);
            out.close();
        } catch (IOException io) {
            throw new RuntimeException(io);
        }
        
        return success;
    }
    
    public static void writeTextFile(String fullPath, String text) {
        try {
            BufferedWriter out = new BufferedWriter(new FileWriter(fullPath));
            out.write(text);
            out.close();
        } catch (IOException iox) {
            
        }
    }
    
    public static void writeTextFile(String dir, String fileName, String text) {
        writeTextFile(dir + fileName, text);
    }
    
    // Append the text to the end of a file.  The file will be created if
    // necessary.
    public static void appendTextFile(String dir, String fileName, String text) {
        String fullPath = dir + fileName;
        try {
            BufferedWriter out = new BufferedWriter(new FileWriter(fullPath, true));
            out.write(text);
            out.close();
        } catch (IOException iox) {
            
        }
    }
    
    public static String readTextFile(String dir, String fileName) {
        if (!dir.endsWith(File.separator)) {
            dir += File.separator;
        }
        String fullPath = dir + fileName;
        StringBuffer buf = new StringBuffer();
        try {
            BufferedReader in = new BufferedReader(new FileReader(fullPath));
            String line;
            while ((line = in.readLine()) != null) {
                buf.append(line).append("\n");
            }
            in.close();
        } catch (IOException iox) {
            
        }
        return buf.toString();
    }
    
    public static byte[] readBinaryFile(String dir, String fileName) {
        String fullPath = dir + fileName;
        
        File file = new File(fullPath);
        if (!file.exists()) {
            return null;
        }
        try {
            return getBytesFromFile(file);
        } catch (IOException iox) {
            throw new RuntimeException(iox);
        }
    }
    
    //public static void writePubTextFile(String fileName, String text) {
    //    writeTextFile(Vcctl.getPublicDir(), fileName, text);
    //}
    
    //public static String readPubTextFile(String fileName) {
    //    return readTextFile(Vcctl.getPublicDir(), fileName);
    //}
    
    /*
    public static byte[] readPubBinaryFile(String fileName) {
        return readBinaryFile(Vcctl.getPublicDir(), fileName);
    }
     **/
    
    private static byte[] getBytesFromFile(File file) throws IOException {
        InputStream is = new FileInputStream(file);
        
        long length = file.length();
        
        if (length > Integer.MAX_VALUE) {
            // file is too large
            throw new IOException("File is too large");
        }
        
        byte[] bytes = new byte[(int)length];
        
        int offset = 0;
        int numRead = 0;
        while ((offset < bytes.length) &&
                (numRead = is.read(bytes, offset, bytes.length-offset)) >= 0) {
            offset += numRead;
        }
        
        if (offset < bytes.length) {
            throw new IOException("Could not completely read file "+file.getName());
        }
        
        is.close();
        return bytes;
    }
    
    /*
    public static boolean deletePubFile(String name) {
        return deleteFile(Vcctl.getPublicDir(), name);
    }
     **/
    
    public static boolean deleteFile(String dir, String name) {
        boolean success = true;
        String fullPath = dir + name;
        File file = new File(fullPath);
        boolean exists = file.exists();
        if (exists) {
            success = file.delete();
        }
        return success;
    }
    
    /**
     * Operation directory and operation file operations
     */
    public static String getUserOperationDir(String userName, String opname) {
        UserDirectory userDir = new UserDirectory(userName);
        String opdir = userDir.getOperationDir(opname);
        // String opdir = Vcctl.getPublicDir()+opname;
        File pubdir = new File(opdir);
        if (!pubdir.exists()) {
            pubdir.mkdir();
        }
        return pubdir.getAbsolutePath()+File.separator;
    }
    
    private static boolean deleteDirectory(File dir) {
        boolean delete_ok = true;
        if (dir.isDirectory()) {
            for ( File sub:dir.listFiles()) {
                if (sub.isDirectory()) {
                    delete_ok &= deleteDirectory(sub);
                } else {
                    delete_ok &= sub.delete();
                }
            }
            delete_ok &= dir.delete();
        }
        return delete_ok;
    }
    
    public static boolean deleteOperationDirForUser(String opname, String userName) {
        String opdir = getUserOperationDir(userName, opname);
        File pubdir = new File(opdir);
        if (pubdir.exists()) {
            return deleteDirectory(pubdir);
        }
        return true;
    }
    
    public static void writeUserOpTextFile(String userName, String opname, String fileName, String text) {
        String opdir = getUserOperationDir(userName, opname);
        writeTextFile(opdir, fileName, text);
    }
    
    public static void appendUserOpTextFile(String userName, String opname, String fileName, String text) {
        String opdir = getUserOperationDir(userName, opname);
        appendTextFile(opdir, fileName, text);
    }
    
    public static String readUserOpTextFile(String userName, String opname, String fileName) {
        String opdir = getUserOperationDir(userName, opname);
        return readTextFile(opdir, fileName);
    }
    
    public static byte[] readUserOpBinaryFile(String userName, String opname, String fileName) {
        String opdir = getUserOperationDir(userName, opname);
        return readBinaryFile(opdir, fileName);
    }
}
