/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import nist.bfrl.vcctl.database.Slag;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;
import org.apache.struts.upload.FormFile;

/**
 *
 * @author bullard
 */
public class SlagMaterialsForm extends ActionForm {
    public void reset() {

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

}
