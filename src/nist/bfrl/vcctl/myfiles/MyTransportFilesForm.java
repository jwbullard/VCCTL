/*
 * MyTransportFilesForm.java
 *
 * Created on October 28, 2011, 3:00 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.myfiles;

import java.util.Map;
import nist.bfrl.vcctl.database.Operation;
import org.apache.struts.action.ActionForm;

/**
 *
 * @author mscialom
 */
public class MyTransportFilesForm extends ActionForm {

    /**
     * Holds value of property transportFactorOperations.
     */
    private Map<String,Operation> transportFactorOperations;

    /**
     * keyed getter for property transportFactorOperations.
     * @param key key of the property.
     * @return Value of the property at <CODE>key</CODE>.
     */
    public Operation getTransportFactorOperations(String key) {
        return this.transportFactorOperations.get(key);
    }

    /**
     * Getter for property transportFactorOperations.
     * @return Value of property transportFactorOperations.
     */
    public Map<String,Operation> getTransportFactorOperations() {
        return this.transportFactorOperations;
    }

    /**
     * Setter for property transportFactorOperations.
     * @param operations New value of property transportFactorOperations.
     */
    public void setTransportFactorOperations(Map<String,Operation> transportFactorOperations) {
        this.transportFactorOperations = transportFactorOperations;
    }
}
