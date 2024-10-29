/*
 * Cement.java
 *
 * Created on February 24, 2006, 3:17 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.database;

import java.sql.*;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;

/**
 *
 * @author tahall
 */
public class Cement {
    
    /** Creates a new instance of Cement */
    public Cement() {
    }
    
    private void save() throws SQLException {
        if (this.alkaliFile == null || this.alkaliFile.length() == 0)
            this.alkaliFile = Constants.DEFAULT_CEMENT_ALKALI_CHARACTERISTICS_FILE;
        
        CementDatabase.saveCement(this);
    }

    private void saveAs() throws SQLException {
        if (this.alkaliFile == null || this.alkaliFile.length() == 0)
            this.alkaliFile = Constants.DEFAULT_CEMENT_ALKALI_CHARACTERISTICS_FILE;

        CementDatabase.saveCementAs(this);
    }
    
    public void saveFromStrings() throws SQLException {
        if (this.aluString != null) {
            this.alu = this.aluString.getBytes();
        }
        if (this.c3aString != null) {
            this.c3a = this.c3aString.getBytes();
        }
        if (this.c3sString != null) {
            this.c3s = this.c3sString.getBytes();
        }
        if (this.c4fString != null) {
            this.c4f = this.c4fString.getBytes();
        }
        if (this.infString != null) {
            this.inf = this.infString.getBytes();
        }
        if (this.k2oString != null) {
            this.k2o = this.k2oString.getBytes();
        }
        if (this.n2oString != null) {
            this.n2o = this.n2oString.getBytes();
        }
        if (this.pfcString != null) {
            this.pfc = this.pfcString.getBytes();
        }
        if (this.silString != null) {
            this.sil = this.silString.getBytes();
        }
        if (this.txtString != null) {
            this.txt = this.txtString.getBytes();
        }
        if (this.xrdString != null) {
            this.xrd = this.xrdString.getBytes();
        }
        save();
    }

        public void saveAsFromStrings() throws SQLException {
        if (this.aluString != null) {
            this.alu = this.aluString.getBytes();
        }
        if (this.c3aString != null) {
            this.c3a = this.c3aString.getBytes();
        }
        if (this.c3sString != null) {
            this.c3s = this.c3sString.getBytes();
        }
        if (this.c4fString != null) {
            this.c4f = this.c4fString.getBytes();
        }
        if (this.infString != null) {
            this.inf = this.infString.getBytes();
        }
        if (this.k2oString != null) {
            this.k2o = this.k2oString.getBytes();
        }
        if (this.n2oString != null) {
            this.n2o = this.n2oString.getBytes();
        }
        if (this.pfcString != null) {
            this.pfc = this.pfcString.getBytes();
        }
        if (this.silString != null) {
            this.sil = this.silString.getBytes();
        }
        if (this.txtString != null) {
            this.txt = this.txtString.getBytes();
        }
        if (this.xrdString != null) {
            this.xrd = this.xrdString.getBytes();
        }
        saveAs();
    }
    
    public void delete() throws SQLException {
        CementDatabase.deleteCement(this);
    }
    
    
    static public Cement load(String cementName) throws SQLException, SQLArgumentException {
        return CementDatabase.loadCement(cementName);
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
     * Holds value of property pfc.
     */
    private byte[] pfc;
    
    /**
     * Getter for property pfc.
     * @return Value of property pfc.
     */
    public byte[] getPfc() {
        return this.pfc;
    }
    
    /**
     * Setter for property pfc.
     * @param pfc New value of property pfc.
     */
    public void setPfc(byte[] pfc) {
        this.pfc = pfc;
    }
    
    public String pfcString;
    
    public String getPfcString() {
        this.pfcString = blobToString(this.pfc);
        return pfcString;
    }
    
    public void setPfcString(String pfc) {
        this.pfcString = pfc;
    }
    
    /**
     * Holds value of property gif.
     */
    private byte[] gif;
    
    /**
     * Getter for property gif.
     * @return Value of property gif.
     */
    public byte[] getGif() {
        return this.gif;
    }

    public String getGifString() {
        String gstring = blobToString(gif);
        return gstring;
    }

    /**
     * Setter for property gif.
     * @param gif New value of property gif.
     */
    public void setGif(byte[] gif) {
        this.gif = gif;
    }
    
    /**
     * Holds value of property legend_gif.
     */
    private byte[] legend_gif;
    
    /**
     * Getter for property legend_gif.
     * @return Value of property legend_gif.
     */
    public byte[] getLegend_gif() {
        return this.legend_gif;
    }
    
    /**
     * Setter for property legend_gif.
     * @param legend_gif New value of property legend_gif.
     */
    public void setLegend_gif(byte[] legend_gif) {
        this.legend_gif = legend_gif;
    }
    
    /**
     * Holds value of property sil.
     */
    private byte[] sil;
    
    /**
     * Getter for property sil.
     * @return Value of property sil.
     */
    public byte[] getSil() {
        return this.sil;
    }
    
    public String silString;
    
    public String getSilString() {
        this.silString = blobToString(this.sil);
        return silString;
    }
    
    public void setSilString(String sil) {
        this.silString = sil;
    }
    
    /**
     * Setter for property sil.
     * @param sil New value of property sil.
     */
    public void setSil(byte[] sil) {
        this.sil = sil;
    }
    
    /**
     * Holds value of property c3s.
     */
    private byte[] c3s;
    
    /**
     * Getter for property c3s.
     * @return Value of property c3s.
     */
    public byte[] getC3s() {
        return this.c3s;
    }
    
    /**
     * Setter for property c3s.
     * @param c3s New value of property c3s.
     */
    public void setC3s(byte[] c3s) {
        this.c3s = c3s;
    }
    
    public String c3sString;
    
    public String getC3sString() {
        this.c3sString = blobToString(this.c3s);
        return c3sString;
    }
    
    public void setC3sString(String c3s) {
        this.c3sString = c3s;
    }
    
    /**
     * Holds value of property c3a.
     */
    private byte[] c3a;
    
    /**
     * Getter for property c3a.
     * @return Value of property c3a.
     */
    public byte[] getC3a() {
        return this.c3a;
    }
    
    public String c3aString;
    
    public String getC3aString() {
        this.c3aString = blobToString(this.c3a);
        return c3aString;
    }
    
    public void setC3aString(String c3a) {
        this.c3aString = c3a;
    }
    
    /**
     * Setter for property c3a.
     * @param c3a New value of property c3a.
     */
    public void setC3a(byte[] c3a) {
        this.c3a = c3a;
    }
    
    /**
     * Holds value of property n2o.
     */
    private byte[] n2o;
    
    /**
     * Getter for property n2o.
     * @return Value of property n2o.
     */
    public byte[] getN2o() {
        return this.n2o;
    }
    
    public String n2oString;
    
    public String getN2oString() {
        this.n2oString = blobToString(this.n2o);
        return n2oString;
    }
    
    public void setN2oString(String n2o) {
        this.n2oString = n2o;
    }
    
    /**
     * Setter for property n2o.
     * @param n2o New value of property n2o.
     */
    public void setN2o(byte[] n2o) {
        this.n2o = n2o;
    }
    
    /**
     * Holds value of property k2o.
     */
    private byte[] k2o;
    
    /**
     * Getter for property k2o.
     * @return Value of property k2o.
     */
    public byte[] getK2o() {
        return this.k2o;
    }
    
    public String k2oString;
    
    public String getK2oString() {
        this.k2oString = blobToString(this.k2o);
        return k2oString;
    }
    
    public void setK2oString(String k2o) {
        this.k2oString = k2o;
    }
    
    /**
     * Setter for property k2o.
     * @param k2o New value of property k2o.
     */
    public void setK2o(byte[] k2o) {
        this.k2o = k2o;
    }
    
    /**
     * Holds value of property alu.
     */
    private byte[] alu;
    
    /**
     * Getter for property alu.
     * @return Value of property alu.
     */
    public byte[] getAlu() {
        return this.alu;
    }
    
    public String aluString;
    
    public String getAluString() {
        this.aluString = blobToString(this.alu);
        return aluString;
    }
    
    public void setAluString(String alu) {
        this.aluString = alu;
    }
    
    /**
     * Setter for property alu.
     * @param alu New value of property alu.
     */
    public void setAlu(byte[] alu) {
        this.alu = alu;
    }
    
    /**
     * Holds value of property dihyd.
     */
    private double dihyd;
    
    /**
     * Getter for property dihyd.
     * @return Value of property dihyd.
     */
    public double getDihyd() {
        return this.dihyd;
    }
    
    /**
     * Setter for property dihyd.
     * @param dihyd New value of property dihyd.
     */
    public void setDihyd(double dihyd) {
        this.dihyd = dihyd;
    }
    
    /**
     * Holds value of property anhyd.
     */
    private double anhyd;
    
    /**
     * Getter for property anhyd.
     * @return Value of property anhyd.
     */
    public double getAnhyd() {
        return this.anhyd;
    }
    
    /**
     * Setter for property anhyd.
     * @param anhyd New value of property anhyd.
     */
    public void setAnhyd(double anhyd) {
        this.anhyd = anhyd;
    }
    
    /**
     * Holds value of property hemihyd.
     */
    private double hemihyd;
    
    /**
     * Getter for property hemihyd.
     * @return Value of property hemihyd.
     */
    public double getHemihyd() {
        return this.hemihyd;
    }
    
    /**
     * Setter for property hemihyd.
     * @param hemihyd New value of property hemihyd.
     */
    public void setHemihyd(double hemihyd) {
        this.hemihyd = hemihyd;
    }
    
    /**
     * Holds value of property txt.
     */
    private byte[] txt;
    
    /**
     * Getter for property txt.
     * @return Value of property txt.
     */
    public byte[] getTxt() {
        return this.txt;
    }
    
    /**
     * Setter for property txt.
     * @param txt New value of property txt.
     */
    public void setTxt(byte[] txt) {
        this.txt = txt;
    }
    
    public String txtString;
    
    public String getTxtString() {
        this.txtString = blobToString(this.txt);
        return txtString;
    }
    
    public void setTxtString(String txt) {
        this.txtString = txt;
    }
    
    /**
     * Holds value of property xrd.
     */
    private byte[] xrd;
    
    /**
     * Getter for property xrd.
     * @return Value of property xrd.
     */
    public byte[] getXrd() {
        return this.xrd;
    }
    
    /**
     * Setter for property xrd.
     * @param xrd New value of property xrd.
     */
    public void setXrd(byte[] xrd) {
        this.xrd = xrd;
    }
    
    public String xrdString;
    
    public String getXrdString() {
        this.xrdString = blobToString(this.xrd);
        return xrdString;
    }
    
    public void setXrdString(String xrd) {
        this.xrdString = xrd;
    }
    
    public void setColumn(String colname,
            byte[] data) {
        if (colname.equalsIgnoreCase("pfc")) {
            this.setPfc(data);
        } else if (colname.equalsIgnoreCase("gif")) {
            this.setGif(data);
        } else if (colname.equalsIgnoreCase("legend_gif")) {
            this.setLegend_gif(data);
        } else if (colname.equalsIgnoreCase("sil")) {
            this.setSil(data);
        } else if (colname.equalsIgnoreCase("c3a")) {
            this.setC3a(data);
        } else if (colname.equalsIgnoreCase("c3s")) {
            this.setC3s(data);
        } else if (colname.equalsIgnoreCase("c4f")) {
            this.setC4f(data);
        } else if (colname.equalsIgnoreCase("k2o")) {
            this.setK2o(data);
        } else if (colname.equalsIgnoreCase("n2o")) {
            this.setN2o(data);
        } else if (colname.equalsIgnoreCase("alu")) {
            this.setAlu(data);
        } else if (colname.equalsIgnoreCase("txt")) {
            this.setTxt(data);
        } else if (colname.equalsIgnoreCase("xrd")) {
            this.setXrd(data);
        } else if (colname.equalsIgnoreCase("inf")) {
            this.setInf(data);
        } else if (colname.equalsIgnoreCase("dihyd")) {
            double dval = blobToDouble(data);
            this.setDihyd(dval);
        } else if (colname.equalsIgnoreCase("hemihyd")) {
            double dval = blobToDouble(data);
            this.setHemihyd(dval);
        } else if (colname.equalsIgnoreCase("anhyd")) {
            double dval = blobToDouble(data);
            this.setAnhyd(dval);
        }
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
    
    public String infString;
    
    public String getInfString() {
        this.infString = blobToString(this.inf);
        return infString;
    }
    
    public void setInfString(String inf) {
        this.infString = inf;
    }
    
    /**
     * Setter for property inf.
     * @param inf New value of property inf.
     */
    public void setInf(byte[] inf) {
        this.inf = inf;
    }
    
    /**
     * Holds value of property c4f.
     */
    private byte[] c4f;
    
    /**
     * Getter for property c4f.
     * @return Value of property c4f.
     */
    public byte[] getC4f() {
        return this.c4f;
    }
    
    public String c4fString;
    
    public String getC4fString() {
        this.c4fString = blobToString(this.c4f);
        return c4fString;
    }
    
    public void setC4fString(String c4f) {
        this.c4fString = c4f;
    }
    
    /**
     * Setter for property c4f.
     * @param c4f New value of property c4f.
     */
    public void setC4f(byte[] c4f) {
        this.c4f = c4f;
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

    /**
     * Holds value of property alkaliFile.
     */
    private String alkaliFile;
    
    /**
     * Getter for property alkaliFile.
     * @return Value of property alkaliFile.
     */
    public String getAlkaliFile() {
        return this.alkaliFile;
    }
    
    /**
     * Setter for property alkaliFile.
     * @param alkaliFile New value of property alkaliFile.
     */
    public void setAlkaliFile(String alkaliFile) {
        this.alkaliFile = alkaliFile;
    }
}
