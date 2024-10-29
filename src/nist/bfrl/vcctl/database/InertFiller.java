/*
 * InertFiller.java
 *
 * Created on January 11, 2006, 9:55 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.database;

import java.sql.*;
import nist.bfrl.vcctl.exceptions.DBFileException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;

import nist.bfrl.vcctl.util.DefaultNameBuilder;

/**
 *
 * @author tahall
 */
public class InertFiller {
    
    /** Creates a new instance of InertFiller */
    public InertFiller() throws DBFileException {
        String newName;
        try {
            newName = DefaultNameBuilder.buildDefaultMaterialName(Constants.INERT_FILLER_TABLE_NAME, "Inert filler", "");
            this.setName(newName);
            this.setSpecific_gravity(Constants.INERT_FILLER_DEFAULT_SPECIFIC_GRAVITY);
            if (CementDatabase.dbFileExists(Constants.DEFAULT_PSD))
                this.setPsd(Constants.DEFAULT_PSD);
            else
                this.setPsd(CementDatabase.getFirstPSDName());
        } catch (SQLArgumentException ex) {
            ex.printStackTrace();
        } catch (SQLException ex) {
            ex.printStackTrace();
        }
    }
    
    public void save() throws SQLException {
        CementDatabase.saveInertFiller(this);
    }

    public void saveAs() throws SQLException {
        CementDatabase.saveInertFillerAs(this);
    }
    
    public void delete() throws SQLException {
        CementDatabase.deleteInertFiller(this);
    }
    
    public static InertFiller load(String name) throws SQLException, SQLArgumentException, DBFileException {
        return CementDatabase.loadInertFiller(name);
    }
    
    public static double get_specific_gravity(String fillname) throws SQLException, SQLArgumentException, DBFileException {
        InertFiller fill = InertFiller.load(fillname);
        
        if (fill != null) {
            return fill.getSpecific_gravity();
        } else {
            return Constants.INERT_FILLER_DEFAULT_SPECIFIC_GRAVITY;
        }
    }
    
    public static String get_psd(String name) throws SQLException, SQLArgumentException, DBFileException {
        InertFiller fill = InertFiller.load(name);
        
        return fill.getPsd();
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
     * Holds value of property specific_gravity.
     */
    private double specific_gravity;
    
    /**
     * Getter for property specific_gravity.
     * @return Value of property specific_gravity.
     */
    public double getSpecific_gravity() {
        
        return this.specific_gravity;
    }
    
    /**
     * Setter for property specific_gravity.
     * @param specific_gravity New value of property specific_gravity.
     */
    public void setSpecific_gravity(double specific_gravity) {
        
        this.specific_gravity = specific_gravity;
    }
    
    /**
     * Holds value of property psd.
     */
    private String psd;
    
    /**
     * Getter for property psd.
     * @return Value of property psd.
     */
    public String getPsd() {
        
        return this.psd;
    }
    
    /**
     * Setter for property psd.
     * @param psd New value of property psd.
     */
    public void setPsd(String psd) {
        
        this.psd = psd;
    }
    
    /**
     * Holds value of property description.
     */
    private String description;
    
    /**
     * Getter for property descr.
     * @return Value of property descr.
     */
    public String getDescription() {
        
        return this.description;
    }
    
    /**
     * Setter for property descr.
     * @param descr New value of property descr.
     */
    public void setDescription(String description) {
        
        this.description = description;
    }
    
}
