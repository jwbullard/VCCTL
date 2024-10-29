/*
 * Grading.java
 *
 * Created on March 22, 2007, 10:33 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.database;

import java.sql.*;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.exceptions.SQLDuplicatedKeyException;

/**
 *
 * @author mscialom
 */
public class Grading {
    
    /**
     * Holds value of property name.
     */
    private String name = null;
    
    /**
     * Holds value of property type.
     */
    private int type;
    
    /**
     * Holds value of property grading.
     */
    private byte[] grading = null;
    
    
    /** Creates a new instance of InertFiller */
    public Grading() {
    }
    
    public void save() throws SQLDuplicatedKeyException, SQLArgumentException, SQLException {
        CementDatabase.saveGrading(this);
    }
    
    public static Grading load(String name) throws SQLException, SQLArgumentException {
        return CementDatabase.loadGrading(name);
    }
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public int getType() {
        return type;
    }
    
    public void setType(int type) {
        this.type = type;
    }
    
    public byte[] getGrading() {
        return grading;
    }
    
    public void setGrading(byte[] grading) {
        this.grading = grading;
    }
    
    /**
     * Holds value of property max_diameter.
     */
    private double max_diameter;
    
    /**
     * Getter for property max_diameter.
     * @return Value of property max_diameter.
     */
    public double getMax_diameter() {
        return this.max_diameter;
    }
    
    /**
     * Setter for property max_diameter.
     * @param max_diameter New value of property max_diameter.
     */
    public void setMax_diameter(double max_diameter) {
        this.max_diameter = max_diameter;
    }
}
