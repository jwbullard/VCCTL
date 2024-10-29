/*
 * DistributeClinkerPhases.java
 *
 * Created on August 12, 2005, 11:53 AM
 */

package nist.bfrl.vcctl.operation.microstructure;

import java.sql.SQLException;
import nist.bfrl.vcctl.database.CementDatabase;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.ServerFile;

import java.io.*;

/**
 *
 * @author tahall
 */
public class DistributeClinkerPhases {
    
    /** Creates a new instance of DistributeClinkerPhases */
    public DistributeClinkerPhases() {
    }
    
    public static void openCorrelationFiles(String cement, String directory) throws SQLArgumentException, SQLException {
        // int last_slash = rootPath.lastIndexOf(File.separator);
        // String cement = rootPath.substring(last_slash+1);

        String rootPath = directory;
        if (!rootPath.endsWith(File.separator)) {
            rootPath = rootPath + File.separator;
        }
        rootPath = rootPath + cement;
        String psddata = CementDatabase.getSil(cement);
        if (psddata != null) {
            ServerFile.saveToFile(rootPath+".sil", psddata.getBytes());
        }
        psddata = CementDatabase.getC3s(cement);
        if (psddata != null) {
            ServerFile.saveToFile(rootPath+".c3s", psddata.getBytes());
        }
        psddata = CementDatabase.getC4f(cement);
        if (psddata != null) {
            ServerFile.saveToFile(rootPath+".c4f", psddata.getBytes());
        }
        psddata = CementDatabase.getC3a(cement);
        if (psddata != null) {
            ServerFile.saveToFile(rootPath+".c3a", psddata.getBytes());
        }
        psddata = CementDatabase.getN2o(cement);
        if (psddata != null) {
            ServerFile.saveToFile(rootPath+".n2o", psddata.getBytes());
        }
        psddata = CementDatabase.getK2o(cement);
        if (psddata != null) {
            ServerFile.saveToFile(rootPath+".k2o", psddata.getBytes());
        }
        psddata = CementDatabase.getAlu(cement);
        if (psddata != null) {
            ServerFile.saveToFile(rootPath+".alu", psddata.getBytes());
        }
    }
    
}
