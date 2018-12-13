/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import nist.bfrl.vcctl.database.Aggregate;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;
import org.apache.struts.upload.FormFile;

/**
 *
 * @author bullard
 */
public class AggregateMaterialsForm extends ActionForm {
    public void reset() {
        uploaded_coarse_aggregate_file = null;
        uploaded_fine_aggregate_file = null;
    }

    /**
     * Holds value of property uploaded_coarse_aggregate_file.
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

}
