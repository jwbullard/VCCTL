/*
 * Aggregate.java
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
import nist.bfrl.vcctl.util.Constants;

/**
 *
 * @author mscialom
 */
public class Aggregate {
    
    /**
     * Holds value of property name.
     */
    private String name = null;

    /**
     * Holds value of property display_name.
     */
    private String display_name = null;

    
    /**
     * Holds value of property type.
     */
    private int type;

     /**
     * Holds value of property type.
     */
    private double specific_gravity;

    /**
     * Holds value of property image.
     */
    private byte[] image = null;
    
    /**
     * Holds value of property txt.
     */
    private byte[] txt = null;
    
    /**
     * Holds value of property inf.
     */
    private byte[] inf = null;

     /**
     * Holds value of property bulk_modulus
     */
    private double bulk_modulus;
    
     /**
     * Holds value of property shear_modulus.
     */
    private double shear_modulus;
    
    /**
     * Holds value of property conductivity.
     */
    private double conductivity;

    /**
     * Holds value of property shape_stats.
     */
    private byte[] shape_stats;

    private String shapestatsString;

    /** Creates a new instance of Aggregate */
    public Aggregate() {
    }
    
    public void save() throws SQLArgumentException, SQLDuplicatedKeyException, SQLException {
        if (this.infString != null) {
            this.inf = this.infString.getBytes();
        }
        if (this.shapestatsString != null) {
            this.shape_stats = this.shapestatsString.getBytes();
        }
        CementDatabase.saveAggregate(this);
    }

    public void saveAs() throws SQLArgumentException, SQLDuplicatedKeyException, SQLException {
        if (this.infString != null) {
            this.inf = this.infString.getBytes();
        }
        if (this.shapestatsString != null) {
            this.shape_stats = this.shapestatsString.getBytes();
        }
        CementDatabase.saveAggregateAs(this);
    }

    public void delete() throws SQLException {
        CementDatabase.deleteAggregate(this);
    }

    public static Aggregate load(String name) throws SQLException, SQLArgumentException {
        return CementDatabase.loadAggregate(name);
    }
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }

    public String getDisplay_name() {
        return display_name;
    }

    public void setDisplay_name(String display_name) {
        this.display_name = display_name;
    }
    
    public int getType() {
        return type;
    }
    
    public void setType(int type) {
        this.type = type;
    }
    
    public byte[] getImage() {
        return image;
    }
    
    public void setImage(byte[] image) {
        this.image = image;
    }
    
    public byte[] getTxt() {
        return txt;
    }
    
    public void setTxt(byte[] txt) {
        this.txt = txt;
    }
    
    public byte[] getInf() {
        return inf;
    }
    
    public void setInf(byte[] inf) {
        this.inf = inf;
    }

    public String infString;

    public String getInfString() {
        this.infString = blobToString(this.inf);
        return infString;
    }

    public void setInfString(String inf) {
        this.infString = inf;
    }
    public double getSpecific_gravity() {
        return specific_gravity;
    }

    public void setSpecific_gravity(double sg) {
        this.specific_gravity = sg;
    }

    public double getBulk_modulus() {
        return bulk_modulus;
    }

    public void setBulk_modulus(double bm) {
        this.bulk_modulus = bm;
    }

    public double getShear_modulus() {
        return shear_modulus;
    }

    public void setShear_modulus(double sm) {
        this.shear_modulus = sm;
    }
    
    public double getConductivity() {
        return conductivity;
    }

    public void setConductivity(double cond) {
        this.conductivity = cond;
    }

    public byte[] getShape_stats() {
        return shape_stats;
    }

    public void setShapestatsString(String sss) {
        this.shapestatsString = sss;
    }

    public String getShapestatsString() {
        this.shapestatsString = blobToString(this.shape_stats);
        return shapestatsString;
    }

    public void setShape_stats(byte[] ss) {
        this.shape_stats = ss;
    }

    public void setColumn(String colname,
            byte[] data) {
        if (colname.equalsIgnoreCase("gif")) {
            this.setImage(data);
        } else if (colname.equalsIgnoreCase("display_name")) {
            String dname = blobToString(data);
            this.setDisplay_name(dname);
        } else if (colname.equalsIgnoreCase("bulk_modulus")) {
            double dval = blobToDouble(data);
            this.setBulk_modulus(dval);
        } else if (colname.equalsIgnoreCase("shear_modulus")) {
            double dval = blobToDouble(data);
            this.setShear_modulus(dval);
        } else if (colname.equalsIgnoreCase("specific_gravity")) {
            double dval = blobToDouble(data);
            this.setSpecific_gravity(dval);
        } else if (colname.equalsIgnoreCase("conductivity")) {
            double dval = blobToDouble(data);
            this.setConductivity(dval);
        } else if (colname.equalsIgnoreCase("inf")) {
            this.setInf(data);
        } else if (colname.equalsIgnoreCase("shape_stats")) {
            this.setShape_stats(data);
            this.setShapestatsString(blobToString(data));
        }
    }

    private String blobToString(byte[] blob) {
        if (blob == null) {
            return new String("");
        }
        return new String(blob);
    }

    private double blobToDouble(byte[] blob) {
        if (blob == null) {
            return 0.0;
        }
        String str = new String(blob);
        double newDouble = Double.parseDouble(str);
        return newDouble;
    }
    
}
