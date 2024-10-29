/*
 * DBFile.java
 *
 * Created on January 24, 2006, 4:08 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.database;

import java.sql.*;
import java.util.logging.Level;
import java.util.logging.Logger;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.exceptions.SQLDuplicatedKeyException;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.DefaultNameBuilder;
import nist.bfrl.vcctl.util.FileTypes;

/**
 *
 * @author tahall
 */
public class DBFile {
    
    /** Creates a new instance of DBFile */
    public DBFile(String type) {
        try {
            this.type = type;
            name = DefaultNameBuilder.buildDefaultMaterialName(Constants.DB_FILE_TABLE_NAME, FileTypes.typeDescription(type), "");
        } catch (SQLArgumentException ex) {
            Logger.getLogger(DBFile.class.getName()).log(Level.SEVERE, null, ex);
        } catch (SQLException ex) {
            Logger.getLogger(DBFile.class.getName()).log(Level.SEVERE, null, ex);
        }
    }
    
    public DBFile(String name, String type, byte[] data, byte[] inf) {
        this.name = name;
        this.type = type;
        this.data = data;
        this.inf = inf;
    }
    
    public DBFile(String name, String type, String dataString, String infString) {
        this.name = name;
        this.type = type;
        this.dataString = dataString;
        this.infString = infString;
    }

    public DBFile(String name, String type, byte[] data) {
        this.name = name;
        this.type = type;
        this.data = data;
    }

    public DBFile(String name, String type, String dataString) {
        this.name = name;
        this.type = type;
        this.dataString = dataString;
    }
    
    /**
     * Holds value of property name.
     */
    private String name;
    
    /**
     * Getter for property name.
     * @return Value of property name.
     */
    public String getName() {
        return this.name;
    }
    
    /**
     * Setter for property name.
     * @param name New value of property name.
     */
    public void setName(String name) {
        this.name = name;
    }
    
    /**
     * Holds value of property type.
     */
    private String type;
    
    /**
     * Getter for property type.
     * @return Value of property type.
     */
    public String getType() {
        return this.type;
    }
    
    /**
     * Setter for property type.
     * @param type New value of property type.
     */
    public void setType(String type) {
        this.type = type;
    }
    
    /**
     * Holds value of property data.
     */
    private byte[] data;
    
    /**
     * Getter for property data.
     * @return Value of property data.
     */
    public byte[] getData() {
        return this.data;
    }
    
    /**
     * Setter for property data.
     * @param data New value of property data.
     */
    public void setData(byte[] data) {
        this.data = data;
    }
    
    public String dataString;
    
    public String getDataString() {
        this.dataString = blobToString(this.data);
        return dataString;
    }
    
    public void setDataString(String data) {
        this.dataString = data;
    }

    /**
     * Holds value of property inf.
     */
    private byte[] inf;

    /**
     * Getter for property inf.
     * @return Value of property inf.
     */
    public byte[] getInf() {
        return this.inf;
    }

    /**
     * Setter for property inf.
     * @param ionf New value of property inf.
     */
    public void setInf(byte[] inf) {
        this.inf = inf;
    }

    public String infString;

    public String getInfString() {
        this.infString = blobToString(this.inf);
        return infString;
    }

    public void setInfString(String infString) {
        this.infString = infString;
    }
    
    private void save() throws SQLArgumentException, SQLDuplicatedKeyException, SQLException {
        CementDatabase.saveDBFile(this);
    }
    
    public void saveFromStrings() throws SQLArgumentException, SQLDuplicatedKeyException, SQLException {
        if (this.dataString != null) {
            this.data = this.dataString.getBytes();
        }
        if (this.infString != null) {
            this.inf = this.infString.getBytes();
        }
        save();
    }
    
    public void delete() throws SQLException {
        CementDatabase.deleteDBFile(this);
    }
    
    public static DBFile load(String name) throws SQLException, SQLArgumentException {
        return CementDatabase.loadDBFile(name);
    }

    /**
     * Getter for property typeDescription.
     * @return Value of property typeDescription.
     */
    public String getTypeDescription() {
        return FileTypes.typeDescription(this.type);
    }
    
    private String blobToString(byte[] blob) {
        if (blob == null) {
            return new String("");
        }
        return new String(blob);
    }
}
