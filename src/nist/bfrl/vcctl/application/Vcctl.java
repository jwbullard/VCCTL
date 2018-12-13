/*
 * Vcctl.java
 *
 * Created on April 22, 2005, 10:22 AM
 */

package nist.bfrl.vcctl.application;

import java.awt.Color;
import java.util.ArrayList;
import java.io.*;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.ServerFile;

/**
 *
 * @author tahall
 */
public class Vcctl {
    
    /** Creates a new instance of Vcctl */
    public Vcctl() {
    }

    static private String version = "9.5";
    static public String getVersion() {
        return version;
    }
    
    static private String vcctlroot = "";
    static private String userName = "";
    
    static public void setRootDir(String rootdir) {
        vcctlroot = rootdir;
    }
    static public String getRootDir() {
        return vcctlroot + File.separator;
    }

    static public void setUserName(String uname) {
        userName = uname;
    }

    static public String getUserName() {
        return userName;
    }

    static public String getImageDirectory() {
        String imgdir = getRootDir() + "image" + File.separator;
        return imgdir;
    }
    
    /*
    static public String getMicrostructureDir() {
        return getPublicDir();
    }
     **/
    
    /*
    static public String getPublicDir() {
        String pubdir = "";
        String osname = System.getProperty("os.name");
        if (osname.toLowerCase().contains("windows")) {
            pubdir = "c:\\vcctl\\pub\\";
        } else {
            pubdir = System.getProperty("user.home");
            pubdir += (File.separator+"vcctl"+File.separator+"pub"+File.separator);
        }
        File dir = new File(pubdir);
        if (!dir.exists()) {
            boolean ok = dir.mkdirs();
            if (!ok) {
                String msg = "Cannot create directory: "+pubdir;
                throw new RuntimeException();
            }
        }
        return pubdir;
    }
     **/
    
    static private String vcctlDir;
    
    static {
        /*
        Map<String, String> env = System.getenv();
        for (String envName : env.keySet()) {
            System.out.format("%s=%s%n", envName, env.get(envName));
        }

        vcctlDir = System.getenv("VCCTL_HOME");
         * */
        
        String vcctlProfileDir;
        String osName = System.getProperty("os.name");
        if (osName.toLowerCase().contains("windows")) {
            vcctlProfileDir = "c:\\";
        } else if (osName.toLowerCase().contains("mac")) {
            // vcctlProfileDir = System.getProperty("/Applications/VCCTL.app/Contents/MacOS");
            vcctlProfileDir = System.getProperty("user.home");

        } else {
            vcctlProfileDir = System.getProperty("user.home");
        }
        String vcctlProfile = ServerFile.readTextFile(vcctlProfileDir, Constants.VCCTL_PROFILE_FILE_NAME);
        String[] lines = vcctlProfile.split("\n");
        if (lines[0].startsWith("VCCTL_HOME:")) {
            vcctlDir = lines[0].substring("VCCTL_HOME:".length());
            if (!vcctlDir.endsWith(File.separator)) {
                vcctlDir += File.separator;
            }
        }
        
        if (vcctlDir == null || vcctlDir.equalsIgnoreCase("")) {
            if (osName.toLowerCase().contains("windows")) {
                vcctlDir = "c:\\vcctl\\";
            } else if (osName.toLowerCase().contains("mac")) {
               // vcctlDir = "/Applications/VCCTL.app/Contents/MacOS/";
                vcctlDir = System.getProperty("user.home");
                vcctlDir += (File.separator + "vcctl" + File.separator);
            } else {
                vcctlDir = System.getProperty("user.home");
                vcctlDir += (File.separator + "vcctl" + File.separator);
            }
        }
        File dir = new File(vcctlDir);
        if (!dir.exists()) {
            boolean ok = dir.mkdirs();
            if (!ok) {
                String msg = "Cannot create directory: " + vcctlDir;
                throw new RuntimeException();
            }
        }
    }
    
    static public String getVcctlDirectory() {
        return vcctlDir;
    }
    
    static public String getBinDirectory() {
        return getVcctlDirectory() + Constants.BIN_DIRECTORY_NAME + File.separator;
    }
    
    static public String getDataDirectory() {
        return getVcctlDirectory() + Constants.DATA_DIRECTORY_NAME + File.separator;
    }
    
    static public String getUserDirectory() {
        return getVcctlDirectory() + Constants.USER_DIRECTORY_NAME + File.separator;
    }
    
    static public String getAggregateDirectory() {
        return getDataDirectory() + Constants.AGGREGATE_DIRECTORY_NAME + File.separator;
    }
    
    static public String getParticleShapeSetDirectory() {
        return getDataDirectory() + Constants.PARTICLE_SHAPE_SET_DIRECTORY_NAME + File.separator;
    }

    static public String getDBDirectory() {
        if (getUserName().length() > 0) {
            return getUserDirectory() + getUserName() + File.separator + Constants.DATABASE_DIRECTORY_NAME + File.separator;
        } else {
            return getDataDirectory() + Constants.DATABASE_DIRECTORY_NAME + File.separator;
        }
    }

    static public String getDBDirectoryNoSep() {
        if (getUserName().length() > 0) {
            return getUserDirectory() + getUserName() + File.separator + Constants.DATABASE_DIRECTORY_NAME;
        } else {
            return getDataDirectory() + Constants.DATABASE_DIRECTORY_NAME;
        }
    }

    /**
    static public String getParametersFilesDirectory() {
        return getDataDirectory()+Constants.PARAMETERS_FILES_DIRECTORY_NAME+File.separator;
    }
    
    static public String getAlkaliFilesDirectory() {
        return getDataDirectory()+Constants.ALKALI_FILES_DIRECTORY_NAME+File.separator;
    }
    
    static public String getSlagCharacteristicsFilesDirectory() {
        return getDataDirectory()+Constants.SLAG_CHARACTERISTICS_FILES_DIRECTORY_NAME+File.separator;
    }
     **/
}
