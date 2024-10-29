/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import nist.bfrl.vcctl.database.InertFiller;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;
import org.apache.struts.upload.FormFile;

/**
 *
 * @author bullard
 */
public class FillerMaterialsForm extends ActionForm {
    public void reset() {

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

}
