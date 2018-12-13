/*
 * DefaultNameBuilder.java
 *
 * Created on October 27, 2005, 3:07 PM
 *
 * To change this template, choose Tools | Options and locate the template under
 * the Source Creation and Management node. Right-click the template and choose
 * Open. You can then make changes to the template in the Source Editor.
 */

package nist.bfrl.vcctl.util;

import java.sql.SQLException;
import nist.bfrl.vcctl.database.OperationDatabase;
import nist.bfrl.vcctl.database.CementDatabase;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;

/**
 *
 * @author tahall
 */
public class DefaultNameBuilder {
    
    /*
    static public String buildDefaultName(String base, String suffix) throws SQLException {
        long num = 1;
        boolean exists = true;
        String retname ="";
        while (exists) {
            String defname = base;
            if (num < 10) {
                defname += "0";
            }
            defname += num;
            defname = SuffixChecker.addSuffix(defname, suffix);
            
            exists = !OperationDatabase.isUniqueProfileName(defname);
            if (!exists) {
                try {
                    exists |= CementDatabase.nameExists(defname);
                } catch (SQLArgumentException ex) {
                    ex.printStackTrace();
                }
            }
            if (!exists) {
                retname = defname;
            }
            num++;
        }
        return retname;
    }
     **/
    
    static public String buildDefaultMaterialName(String material, String base, String suffix) throws SQLArgumentException, SQLException {
        long num = 0;
        String numstring;
        boolean exists = true;
        String retname ="";
        while (exists) {
            String defname = base;
            
            if (num > 0) {
                if (num < 10) {
                    numstring = "0" + num;
                } else {
                    numstring = "" + num;
                }
                defname += "_" + numstring;
            }
            defname = SuffixChecker.addSuffix(defname, suffix);
            
            exists = !CementDatabase.isUniqueMaterialNameOfType(material, defname);
            if (!exists) {
                retname = defname;
            }
            num++;
        }
        return retname;
    }
    
    static public String buildDefaultOperationNameForUser(String base, String suffix, String userName) throws SQLException, SQLArgumentException {
        long num = 0;
        String numstring;
        boolean exists = true;
        String retname ="";
        while (exists) {
            String defname = base;
            
            if (num > 0) {
                if (num < 10) {
                    numstring = "0" + num;
                } else {
                    numstring = "" + num;
                }
                defname += "_" + numstring;
            }
            defname = SuffixChecker.addSuffix(defname, suffix);
            
            exists = !OperationDatabase.isUniqueOperationNameForUser(defname, userName);
            if (!exists) {
                retname = defname;
            }
            num++;
        }
        return retname;
    }
}
