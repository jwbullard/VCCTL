/*
 * VcctlDB.java
 *
 * Created on March 14, 2005, 2:04 PM
 */

package nist.bfrl.vcctl.database;

import org.apache.derby.jdbc.EmbeddedDriver;
import java.sql.Connection;
import java.sql.*;
import nist.bfrl.vcctl.application.Vcctl;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.application.*;

/**
 *
 * @author tahall
 */
public class VCCTLDatabase {
    /**
     *  Database initialization
     */
    static private boolean driverLoaded = false;
    static private boolean returnValue = false;
    static private String oldDbDir = "";
    static public boolean loadDriver() {
        if (!driverLoaded) {
            try {
                Class.forName("org.apache.derby.jdbc.EmbeddedDriver").newInstance();
                driverLoaded = true;
            } catch (Exception ex) {
                ex.printStackTrace();
                driverLoaded = false;
            }
        }
        
        return driverLoaded;
    }
    
}
