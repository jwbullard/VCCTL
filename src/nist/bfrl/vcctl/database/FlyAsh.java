/*
 * FlyAsh.java
 *
 * Created on December 29, 2005, 11:00 AM
 */

package nist.bfrl.vcctl.database;

import java.beans.*;
import java.io.Serializable;

import java.sql.*;
import nist.bfrl.vcctl.exceptions.DBFileException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.DefaultNameBuilder;

/**
 * @author tahall
 */
public class FlyAsh extends Object implements Serializable {
    
    public FlyAsh() throws DBFileException {
        try {
            name = DefaultNameBuilder.buildDefaultMaterialName(Constants.FLY_ASH_TABLE_NAME, "Fly ash", "");
            this.setSpecific_gravity(Constants.FLY_ASH_DEFAULT_SPECIFIC_GRAVITY);
            this.setDescription("");
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
     * Holds value of property distribute_phases_by.
     */
    private int distribute_phases_by;
    
    /**
     * Getter for property distribute_phases_by.
     * @return Value of property distribute_phases_by.
     */
    public int getDistribute_phases_by() {
        
        return this.distribute_phases_by;
    }
    
    /**
     * Setter for property distribute_phases_by.
     * @param distribute_phases_by New value of property distribute_phases_by.
     */
    public void setDistribute_phases_by(int distribute_phases_by) {
        
        this.distribute_phases_by = distribute_phases_by;
    }
    
    /**
     * Holds value of property aluminosilicate_glass_fraction.
     */
    private double aluminosilicate_glass_fraction;
    
    /**
     * Getter for property aluminosilicate_glass_fraction.
     * @return Value of property aluminosilicate_glass_fraction.
     */
    public double getAluminosilicate_glass_fraction() {
        
        return this.aluminosilicate_glass_fraction;
    }
    
    /**
     * Setter for property aluminosilicate_glass_fraction.
     * @param aluminosilicate_glass_fraction New value of property aluminosilicate_glass_fraction.
     */
    public void setAluminosilicate_glass_fraction(double aluminosilicate_glass_fraction) {
        
        this.aluminosilicate_glass_fraction = aluminosilicate_glass_fraction;
    }
    
    /**
     * Holds value of property calcium_aluminum_disilicate_fraction.
     */
    private double calcium_aluminum_disilicate_fraction;
    
    /**
     * Getter for property calcium_aluminum_disilicate_fraction.
     * @return Value of property calcium_aluminum_disilicate_fraction.
     */
    public double getCalcium_aluminum_disilicate_fraction() {
        
        return this.calcium_aluminum_disilicate_fraction;
    }
    
    /**
     * Setter for property calcium_aluminum_disilicate_fraction.
     * @param calcium_aluminum_disilicate_fraction New value of property calcium_aluminum_disilicate_fraction.
     */
    public void setCalcium_aluminum_disilicate_fraction(double calcium_aluminum_disilicate_fraction) {
        
        this.calcium_aluminum_disilicate_fraction = calcium_aluminum_disilicate_fraction;
    }
    
    /**
     * Holds value of property tricalcium_aluminate_fraction.
     */
    private double tricalcium_aluminate_fraction;
    
    /**
     * Getter for property tricalcium_aluminate_fraction.
     * @return Value of property tricalcium_aluminate_fraction.
     */
    public double getTricalcium_aluminate_fraction() {
        
        return this.tricalcium_aluminate_fraction;
    }
    
    /**
     * Setter for property tricalcium_aluminate_fraction.
     * @param tricalcium_aluminate_fraction New value of property tricalcium_aluminate_fraction.
     */
    public void setTricalcium_aluminate_fraction(double tricalcium_aluminate_fraction) {
        
        this.tricalcium_aluminate_fraction = tricalcium_aluminate_fraction;
    }
    
    /**
     * Holds value of property calcium_chloride_fraction.
     */
    private double calcium_chloride_fraction;
    
    /**
     * Getter for property calcium_chloride_fraction.
     * @return Value of property calcium_chloride_fraction.
     */
    public double getCalcium_chloride_fraction() {
        
        return this.calcium_chloride_fraction;
    }
    
    /**
     * Setter for property calcium_chloride_fraction.
     * @param calcium_chloride_fraction New value of property calcium_chloride_fraction.
     */
    public void setCalcium_chloride_fraction(double calcium_chloride_fraction) {
        
        this.calcium_chloride_fraction = calcium_chloride_fraction;
    }
    
    /**
     * Holds value of property silica_fraction.
     */
    private double silica_fraction;
    
    /**
     * Getter for property silica_fraction.
     * @return Value of property silica_fraction.
     */
    public double getSilica_fraction() {
        
        return this.silica_fraction;
    }
    
    /**
     * Setter for property silica_fraction.
     * @param silica_fraction New value of property silica_fraction.
     */
    public void setSilica_fraction(double silica_fraction) {
        
        this.silica_fraction = silica_fraction;
    }
    
    /**
     * Holds value of property anhydrite_fraction.
     */
    private double anhydrite_fraction;
    
    /**
     * Getter for property anhydrite_fraction.
     * @return Value of property anhydrite_fraction.
     */
    public double getAnhydrite_fraction() {
        
        return this.anhydrite_fraction;
    }
    
    /**
     * Setter for property anhydrite_fraction.
     * @param anhydrite_fraction New value of property anhydrite_fraction.
     */
    public void setAnhydrite_fraction(double anhydrite_fraction) {
        
        this.anhydrite_fraction = anhydrite_fraction;
    }
    
    public void save() throws SQLException {
        CementDatabase.saveFlyAsh(this);
    }

    public void saveAs() throws SQLException {
        CementDatabase.saveFlyAshAs(this);
    }
    
    public void delete() throws SQLException {
        CementDatabase.deleteFlyAsh(this);
    }
    
    static public FlyAsh load(String name) throws SQLException, SQLArgumentException, DBFileException {
        return CementDatabase.loadFlyAsh(name);
    }
    
    /**
     * Getter for property sum_of_fractions.
     * @return Value of property sum_of_fractions.
     */
    public double getSum_of_fractions() {
        
        double sum = this.getAluminosilicate_glass_fraction() +
                this.getCalcium_aluminum_disilicate_fraction() +
                this.getTricalcium_aluminate_fraction() +
                this.getCalcium_chloride_fraction() +
                this.getSilica_fraction() +
                this.getAnhydrite_fraction();
        sum = Math.round(sum * 10000.0) / 10000.0; // round to 4 dec
        return sum;
    }
    
    public static double get_specific_gravity(String name) throws SQLException, SQLArgumentException, DBFileException {
        FlyAsh f = FlyAsh.load(name);
        
        if (f != null) {
            return f.getSpecific_gravity();
        } else {
            return Constants.FLY_ASH_DEFAULT_SPECIFIC_GRAVITY;
        }
    }
    
    public static String get_psd(String name) throws SQLException, SQLArgumentException, DBFileException {
        FlyAsh f = FlyAsh.load(name);
        
        return f.getPsd();
    }
    
    /**
     * Holds value of property description.
     */
    private String description;
    
    /**
     * Getter for property description.
     * @return Value of property description.
     */
    public String getDescription() {
        
        return this.description;
    }
    
    /**
     * Setter for property description.
     * @param description New value of property description.
     */
    public void setDescription(String description) {
        
        this.description = description;
    }
    
}
