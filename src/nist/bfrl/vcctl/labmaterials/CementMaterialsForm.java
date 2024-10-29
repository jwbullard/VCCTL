/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import nist.bfrl.vcctl.database.Cement;
import nist.bfrl.vcctl.database.DBFile;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;
import org.apache.struts.upload.FormFile;

/**
 *
 * @author bullard
 */
public class CementMaterialsForm extends ActionForm {
public void reset() {
        uploaded_file = null;
    }

    /**
     * Holds value of property file_type.
     */
    private String file_type;

    /**
     * Holds value of property cement.
     */
    private Cement cement;

    /**
     * Getter for property cement.
     * @return Value of property cement.
     */
    public Cement getCement() {
        return this.cement;
    }

    /**
     * Setter for property cement.
     * @param cement New value of property cement.
     */
    public void setCement(Cement cement) {
        this.cement = cement;
    }

//    private String cemName;
//
//    /**
//     * Getter for property cemName
//     * @return Value of property cemName.
//     */
//    public String getCemName() {
//        return this.cemName;
//    }
//
//    /**
//    * Setter for property cemName.
//     * @param cemName New value of property cemName.
//     */
//    public void setCemName(Cement cement) {
//        this.cemName = cement.getName();
//    }

    /**
     * Holds value of property gif.
     */
    private String gif;

    /**
     * Getter for property gif
     * @return Value of property gif.
     */

    public String getGif() {
        return this.gif;
    }

    /**
     * Setter for property gif.
     * @param gif New value of property gif.
     */
    public void setGif(String gif) {
        this.gif = gif;
    }

    /**
     * Getter for property file_type.
     * @return Value of property file_type.
     */
    public String getFile_type() {

        return this.file_type;
    }

    /**
     * Setter for property file_type.
     * @param file_type New value of property file_type.
     */
    public void setFile_type(String file_type) {

        this.file_type = file_type;
    }

    /**
     * Holds value of property uploaded_file.
     */
    private FormFile uploaded_file;

    /**
     * Getter for property uploaded_file.
     * @return Value of property uploaded_file.
     */
    public FormFile getUploaded_file() {
        return this.uploaded_file;
    }

    /**
     * Setter for property uploaded_file.
     * @param uploaded_file New value of property uploaded_file.
     */
    public void setUploaded_file(FormFile uploaded_file) {
        this.uploaded_file = uploaded_file;
    }

    /**
     * Holds value of property cementDataFile.
     */
    private DBFile cementDataFile;

    /**
     * Getter for property cementDataFile.
     * @return Value of property cementDataFile.
     */
    public DBFile getCementDataFile() {
        return this.cementDataFile;
    }

    /**
     * Setter for property cementDataFile.
     * @param cementDataFile New value of property cementDataFile.
     */
    public void setCementDataFile(DBFile cementDataFile) {
        this.cementDataFile = cementDataFile;
    }

}
