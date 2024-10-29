/*
 * LabMaterialsForm.java
 *
 * Created on May 5, 2005, 3:18 PM
 */

package nist.bfrl.vcctl.labmaterials;

import nist.bfrl.vcctl.database.Cement;
import nist.bfrl.vcctl.database.Aggregate;
import nist.bfrl.vcctl.database.DBFile;
import nist.bfrl.vcctl.database.FlyAsh;
import nist.bfrl.vcctl.database.InertFiller;
import nist.bfrl.vcctl.database.Slag;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;
import org.apache.struts.upload.FormFile;

/**
 *
 * @author tahall
 */
public class LabMaterialsForm extends ActionForm {
    
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

    private String cemName;

    /**
     * Getter for property cemName
     * @return Value of property cemName.
     */
    public String getCemName() {
        return this.cemName;
    }

    /**
     * Setter for property cemName.
     * @param cemName New value of property cemName.
     */
    public void setCemName(Cement cement) {
        this.cemName = cement.getName();
    }

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
     * Holds value of property uploaded_file.
     */
    private FormFile uploaded_coarse_aggregate_file;

    /**
     * Getter for property uploaded_coarse_aggregate_file.
     * @return Value of property uploaded_coarse_aggregate_file.
     */
    public FormFile getUploaded_coarse_aggregate_file() {
        return this.uploaded_coarse_aggregate_file;
    }

    /**
     * Setter for property uploaded_coarse_aggreate_file.
     * @param uploaded_coarse_aggregate_file New value of property uploaded_coarse_aggregate_file.
     */
    public void setUploaded_coarse_aggregate_file(FormFile uploaded_file) {
        this.uploaded_coarse_aggregate_file = uploaded_file;
    }

    /**
     * Holds value of property uploaded_fine_aggregate_file.
     */
    private FormFile uploaded_fine_aggregate_file;

    /**
     * Getter for property uploaded_fine_aggregate_file.
     * @return Value of property uploaded_fine_aggregate_file.
     */
    public FormFile getUploaded_fine_aggregate_file() {
        return this.uploaded_fine_aggregate_file;
    }

    /**
     * Setter for property uploaded_fine_aggreate_file.
     * @param uploaded_fine_aggregate_file New value of property uploaded_fine_aggregate_file.
     */
    public void setUploaded_fine_aggregate_file(FormFile uploaded_file) {
        this.uploaded_fine_aggregate_file = uploaded_file;
    }

    /**
     * Holds value of property slag.
     */
    private Slag slag;

    /**
     * Getter for property slag.
     * @return Value of property slag.
     */
    public Slag getSlag() {
        return this.slag;
    }

    /**
     * Setter for property slag.
     * @param slag New value of property slag.
     */
    public void setSlag(Slag slag) {
        this.slag = slag;
    }

    /**
     * Holds value of property flyAsh.
     */
    private FlyAsh flyAsh;

    /**
     * Getter for property flyAsh.
     * @return Value of property flyAsh.
     */
    public FlyAsh getFlyAsh() {
        return this.flyAsh;
    }

    /**
     * Setter for property flyAsh.
     * @param flyAsh New value of property flyAsh.
     */
    public void setFlyAsh(FlyAsh flyAsh) {
        this.flyAsh = flyAsh;
    }

    /**
     * Holds value of property inertFiller.
     */
    private InertFiller inertFiller;

    /**
     * Getter for property inertFiller.
     * @return Value of property inertFiller.
     */
    public InertFiller getInertFiller() {
        return this.inertFiller;
    }

    /**
     * Setter for property inertFiller.
     * @param inertFiller New value of property inertFiller.
     */
    public void setInertFiller(InertFiller inertFiller) {
        this.inertFiller = inertFiller;
    }

     /**
     * Holds value of property coarseAggregate.
     */
    private Aggregate coarseAggregate;

    /**
     * Getter for property coarseAggregate
     * @return Value of property coarseAggregate.
     */
    public Aggregate getCoarseAggregate() {
        return this.coarseAggregate;
    }

    /**
     * Setter for property coarseAggregate.
     * @param coarseAggregate New value of property coarseAggregate.
     */
    public void setCoarseAggregate(Aggregate coarseAggregate) {
        this.coarseAggregate = coarseAggregate;
    }

     /**
     * Holds value of property fineAggregate.
     */
    private Aggregate fineAggregate;

    /**
     * Getter for property fineAggregate
     * @return Value of property fineAggregate.
     */
    public Aggregate getFineAggregate() {
        return this.fineAggregate;
    }

    /**
     * Setter for property fineAggregate.
     * @param fineAggregate New value of property fineAggregate.
     */
    public void setFineAggregate(Aggregate fineAggregate) {
        this.fineAggregate = fineAggregate;
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
