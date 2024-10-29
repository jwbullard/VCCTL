/*
 * Slag.java
 *
 * Created on January 3, 2006, 4:56 PM
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
public class Slag extends Object implements Serializable {
    
    public Slag() throws DBFileException {
        String newName;
        try {
            newName = DefaultNameBuilder.buildDefaultMaterialName(Constants.SLAG_TABLE_NAME, "Slag", "");
            this.setName(newName);
            this.setSpecific_gravity(Constants.SLAG_DEFAULT_SPECIFIC_GRAVITY);
            if (CementDatabase.dbFileExists(Constants.DEFAULT_PSD))
                this.setPsd(Constants.DEFAULT_PSD);
            else
                this.setPsd(CementDatabase.getFirstPSDName());
            this.setMolecular_mass(Constants.SLAG_DEFAULT_MOLECULAR_MASS);
            this.setCasi_mol_ratio(Constants.SLAG_DEFAULT_CA_SI_MOLAR_RATIO);
            this.setSi_per_mole(Constants.SLAG_DEFAULT_SI_PER_MOLE);
            this.setBase_slag_reactivity(Constants.BASE_SLAG_DEFAULT_REACTIVITY);
            this.setHp_molecular_mass(Constants.SLAG_GEL_HYDRATION_PRODUCT_DEFAULT_MOLECULAR_MASS);
            this.setHp_density(Constants.SLAG_GEL_HYDRATION_PRODUCT_DEFAULT_DENSITY);
            this.setHp_casi_mol_ratio(Constants.SLAG_GEL_HYDRATION_PRODUCT_DEFAULT_CA_SI_MOLAR_RATIO);
            this.setHp_h2osi_mol_ratio(Constants.SLAG_GEL_HYDRATION_PRODUCT_DEFAULT_H20_SI_MOLAR_RATIO);
            this.setC3a_per_mole(0.0);
            this.setDescription("");
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
     * Holds value of property molecular_mass.
     */
    private double molecular_mass;
    
    /**
     * Getter for property molecular_mass.
     * @return Value of property molecular_mass.
     */
    public double getMolecular_mass() {
        
        return this.molecular_mass;
    }
    
    /**
     * Setter for property molecular_mass.
     * @param molecular_mass New value of property molecular_mass.
     */
    public void setMolecular_mass(double molecular_mass) {
        
        this.molecular_mass = molecular_mass;
    }
    
    /**
     * Getter for property density.
     * @return Value of property density.
     */
    public double getDensity() {
        
        return this.getSpecific_gravity() * Constants.WATER_DENSITY;
    }
    
    /**
     * Holds value of property casi_mol_ratio.
     */
    private double casi_mol_ratio;
    
    /**
     * Getter for property casi_mol_ratio.
     * @return Value of property casi_mol_ratio.
     */
    public double getCasi_mol_ratio() {
        
        return this.casi_mol_ratio;
    }
    
    /**
     * Setter for property casi_mol_ratio.
     * @param casi_mol_ratio New value of property casi_mol_ratio.
     */
    public void setCasi_mol_ratio(double casi_mol_ratio) {
        
        this.casi_mol_ratio = casi_mol_ratio;
    }
    
    /**
     * Holds value of property si_per_mole.
     */
    private double si_per_mole;
    
    /**
     * Getter for property si_per_mole.
     * @return Value of property si_per_mole.
     */
    public double getSi_per_mole() {
        
        return this.si_per_mole;
    }
    
    /**
     * Setter for property si_per_mole.
     * @param si_per_mole New value of property si_per_mole.
     */
    public void setSi_per_mole(double si_per_mole) {
        
        this.si_per_mole = si_per_mole;
    }
    
    /**
     * Holds value of property base_slag_reactivity.
     */
    private double base_slag_reactivity;
    
    /**
     * Getter for property base_slag_reactivity.
     * @return Value of property base_slag_reactivity.
     */
    public double getBase_slag_reactivity() {
        
        return this.base_slag_reactivity;
    }
    
    /**
     * Setter for property base_slag_reactivity.
     * @param base_slag_reactivity New value of property base_slag_reactivity.
     */
    public void setBase_slag_reactivity(double base_slag_reactivity) {
        
        this.base_slag_reactivity = base_slag_reactivity;
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
    
    /**
     * Holds value of property hp_molecular_mass.
     */
    private double hp_molecular_mass;
    
    /**
     * Getter for property hp_molecular_mass.
     * @return Value of property hp_molecular_mass.
     */
    public double getHp_molecular_mass() {
        
        return this.hp_molecular_mass;
    }
    
    /**
     * Setter for property hp_molecular_mass.
     * @param hp_molecular_mass New value of property hp_molecular_mass.
     */
    public void setHp_molecular_mass(double hp_molecular_mass) {
        
        this.hp_molecular_mass = hp_molecular_mass;
    }
    
    /**
     * Holds value of property hp_density.
     */
    private double hp_density;
    
    /**
     * Getter for property hp_density.
     * @return Value of property hp_density.
     */
    public double getHp_density() {
        
        return this.hp_density;
    }
    
    /**
     * Setter for property hp_density.
     * @param hp_density New value of property hp_density.
     */
    public void setHp_density(double hp_density) {
        
        this.hp_density = hp_density;
    }
    
    /**
     * Holds value of property hp_casi_mol_ratio.
     */
    private double hp_casi_mol_ratio;
    
    /**
     * Getter for property hp_casi_mol_ratio.
     * @return Value of property hp_casi_mol_ratio.
     */
    public double getHp_casi_mol_ratio() {
        
        return this.hp_casi_mol_ratio;
    }
    
    /**
     * Setter for property hp_casi_mol_ratio.
     * @param hp_casi_mol_ratio New value of property hp_casi_mol_ratio.
     */
    public void setHp_casi_mol_ratio(double hp_casi_mol_ratio) {
        
        this.hp_casi_mol_ratio = hp_casi_mol_ratio;
    }
    
    /**
     * Holds value of property hp_h2osi_mol_ratio.
     */
    private double hp_h2osi_mol_ratio;
    
    /**
     * Getter for property hp_h2osi_mol_ratio.
     * @return Value of property hp_h2osi_mol_ratio.
     */
    public double getHp_h2osi_mol_ratio() {
        
        return this.hp_h2osi_mol_ratio;
    }
    
    /**
     * Setter for property hp_h2osi_mol_ratio.
     * @param hp_h2osi_mol_ratio New value of property hp_h2osi_mol_ratio.
     */
    public void setHp_h2osi_mol_ratio(double hp_h2osi_mol_ratio) {
        
        this.hp_h2osi_mol_ratio = hp_h2osi_mol_ratio;
    }
    
    /**
     * Holds value of property c3a_per_mole.
     */
    private double c3a_per_mole;
    
    /**
     * Getter for property c3a_per_mole.
     * @return Value of property c3a_per_mole.
     */
    public double getC3a_per_mole() {
        
        return this.c3a_per_mole;
    }
    
    /**
     * Setter for property c3a_per_mole.
     * @param c3a_per_mole New value of property c3a_per_mole.
     */
    public void setC3a_per_mole(double c3a_per_mole) {
        
        this.c3a_per_mole = c3a_per_mole;
    }
    
    public void save() throws SQLException {
        CementDatabase.saveSlag(this);
    }

    public void saveAs() throws SQLException {
        CementDatabase.saveSlagAs(this);
    }
    
    public void delete() throws SQLException {
        CementDatabase.deleteSlag(this);
    }
    
    public static Slag load(String name) throws SQLException, SQLArgumentException, DBFileException {
        return CementDatabase.loadSlag(name);
    }
    
    public static double get_specific_gravity(String slagname) throws SQLException, SQLArgumentException, DBFileException {
        Slag slag = Slag.load(slagname);
        
        if (slag != null) {
            return slag.getSpecific_gravity();
        } else {
            return Constants.SLAG_DEFAULT_SPECIFIC_GRAVITY;
        }
    }
    
    public static String get_psd(String name) throws SQLException, SQLArgumentException, DBFileException {
        Slag slag = Slag.load(name);
        
        return slag.getPsd();
    }
    
    /*
     * Return twelve-line text in format of a slag characteristics file
     */
    public String getFileText() {
        StringBuffer buf = new StringBuffer("");
        /*****************************************************
         * In comments below, "product" refers to the Slag gel
         * hydration product
         *****************************************************/
        
        // 1. Molecular mass of slag in g/mol
        double mol_mass = this.getMolecular_mass();
        buf.append(mol_mass).append('\n');
        
        // 2. Molecular mass of product in g/mol
        double mol_mass_product = this.getHp_molecular_mass();
        buf.append(mol_mass_product).append('\n');
        
        // 3. Density of slag in g/cm3
        double density = this.getDensity();
        buf.append(density).append('\n');
        
        // 4. Density of product in g/cm3
        double density_product = this.getHp_density();
        buf.append(density_product).append('\n');
        
        // 5. Molar volume of slag in cm3/mol
        buf.append(mol_mass / density).append('\n');
        
        // 6. Molar volume of product in cm3/mol
        buf.append(mol_mass_product / density_product).append('\n');
        
        // 7. Ca/Si molar ratio of slag
        buf.append(this.getCasi_mol_ratio()).append('\n');
        
        // 8. Ca/Si molar ratio of product
        buf.append(this.getHp_casi_mol_ratio()).append('\n');
        
        // 9. Si per mole of slag
        buf.append(this.getSi_per_mole()).append('\n');
        
        // 10. H2O/Si molar ratio of product
        buf.append(this.getHp_h2osi_mol_ratio()).append('\n');
        
        // 11. C3A per mole of slag in product
        buf.append(this.getC3a_per_mole()).append('\n');
        
        // 12. Base slag reactivity
        buf.append(this.getBase_slag_reactivity()).append('\n');
        
        
        return buf.toString();
    }
    
    /**
     * Getter for property molar_volume.
     * @return Value of property molar_volume.
     */
    public double getMolar_volume() {
        return (this.molecular_mass/this.getDensity());
    }
    
    /**
     * Getter for property hp_molar_volume.
     * @return Value of property hp_molar_volume.
     */
    public double getHp_molar_volume() {
        return (this.hp_molecular_mass/this.hp_density);
    }
    
    
}
