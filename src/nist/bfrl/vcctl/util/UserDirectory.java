/*
 * UserDirectory.java
 *
 * Created on October 25, 2005, 8:53 AM
 *
 * To change this template, choose Tools | Options and locate the template under
 * the Source Creation and Management node. Right-click the template and choose
 * Open. You can then make changes to the template in the Source Editor.
 */

package nist.bfrl.vcctl.util;

import java.io.*;
import java.util.ArrayList;

import nist.bfrl.vcctl.application.Vcctl;

/**
 *
 * @author tahall
 */
public class UserDirectory {
    // static public UserDirectory INSTANCE = new UserDirectory();
    
    /** Creates a new instance of UserDirectory */
    public UserDirectory(String userName) {
        String publicDir = Vcctl.getUserDirectory();
        if (publicDir.charAt(publicDir.length() - 1) != File.separatorChar)
            publicDir = publicDir + File.separator;
        setPath(publicDir + userName + File.separator);
    }
    
    // Private member to set the path.  Should be called
    // from either initializeDirectory() or moveDirectory()
    private boolean setPath(String path) {
        boolean success = true;
        try {
            File dir = new File(path);
            if (!dir.exists()) {
                success = dir.mkdirs();
            }
            this.path = dir.getCanonicalPath();
        } catch (IOException iox) {
            success = false;
        }
        
        return success;
    }
    
    // Path of the VCCTL user directory
    private String path;
    String getPath() {
        return path;
    }
    
    // Return the full path of the directory that contains
    // all files related to the given operation
    //
    // Create the directory, if necessary
    public String getOperationDir(String opname) {
        File fopdir = new File(getPath(), opname);
        String opdir = "";
        if (!fopdir.exists()) {
            fopdir.mkdirs();
        }
        try {
            if (fopdir.exists()) {
                opdir = fopdir.getCanonicalPath();
            }
        } catch (IOException iox) {
            opdir = "";
        }
        
        return opdir;
    }
    
    // Returns the full, canonical path of the file and operation specified
    // This function DOES NOT create the file or check if it exists
    public String getOperationFilePath(String opname, String filename) {
        String opdir = getOperationDir(opname);
        File opfile = new File(opdir, filename);
        String filepath = "";
        try {
            filepath = opfile.getCanonicalPath();
        } catch (IOException iox) {
            filepath = "";
        }
        return filepath;
    }
    
    // Return the names of all files belonging to an operation
    public String[] getOperationFileNames(String opname) {
        String opdir = getOperationDir(opname);
        File fopdir = new File(opdir);
        
        File[] filesList = fopdir.listFiles();
        
        ArrayList<String> filesNames = new ArrayList();
        for (int i = 0; i < filesList.length; i++) {
            if (!filesList[i].isDirectory() && !filesList[i].getName().startsWith("."))
                filesNames.add(filesList[i].getName());
        }
        return (String[]) filesNames.toArray(new String[filesNames.size()]);
    }
    
    // Return the names of all folder belonging to an operation
    public String[] getOperationFolderNames(String opname) {
        String opdir = getOperationDir(opname);
        File fopdir = new File(opdir);
        
        File[] folderList = fopdir.listFiles();
        
        ArrayList<String> folderNames = new ArrayList();
        for (int i = 0; i < folderList.length; i++) {
            if (folderList[i].isDirectory() && !folderList[i].getName().startsWith("."))
                folderNames.add(folderList[i].getName());
        }
        return (String[]) folderNames.toArray(new String[folderNames.size()]);
    }
    
    /*
     * This function searches all the files in an operation directory
     * and deletes any that end in '.zip'  The only file that should end
     * in '.zip' is one that is an archive of all the files in the directory.
     * Such a file should be regenerated each time it is needed as an archive
     * of the files can be created at any stage of the operation's execution and
     * thus can change.
     */
    public void deleteZipFiles(String opname) {
        String opdir = getOperationDir(opname);
        File fopdir = new File(opdir);
        
        String[] files = fopdir.list();
        boolean deleted = false;
        for (int i=0; i<files.length; i++) {
            String filename = getOperationFilePath(opname, files[i]);
            if (filename.endsWith(".zip")) {
                File fzip = new File(filename);
                deleted = fzip.delete();
            }
        }
    }
    
    /*
     * This function searches all the files in an operation directory
     * and deletes any that end in '.slicein' or '.sliceout'  These files
     * are created when viewing an image slice and are the input and output
     * files of the 'oneimage' application.
     */
    public void deleteSliceFiles(String opname) {
        String opdir = getOperationDir(opname);
        File fopdir = new File(opdir);
        
        String[] files = fopdir.list();
        boolean deleted = false;
        for (int i=0; i<files.length; i++) {
            String filename = getOperationFilePath(opname, files[i]);
            if (filename.endsWith(".slicein") || filename.endsWith(".sliceout")) {
                File fzip = new File(filename);
                deleted = fzip.delete();
            }
        }
    }
}
