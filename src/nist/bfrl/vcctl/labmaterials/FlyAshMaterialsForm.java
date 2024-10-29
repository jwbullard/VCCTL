/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import nist.bfrl.vcctl.database.FlyAsh;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;
import org.apache.struts.upload.FormFile;

/**
 *
 * @author bullard
 */
public class FlyAshMaterialsForm extends ActionForm{

    public void reset() {

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

}
