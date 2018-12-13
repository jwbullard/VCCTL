/*
 * MyMicrostructureFilesForm.java
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
public class MyMicrostructureFilesForm extends ActionForm {

    /**
     * Holds value of property microstructureOperations.
     */
    private Map<String,Operation> microstructureOperations;

    /**
     * keyed getter for property microstructureOperations.
     * @param key key of the property.
     * @return Value of the property at <CODE>key</CODE>.
     */
    public Operation getMicrostructureOperations(String key) {
        return this.microstructureOperations.get(key);
    }

    /**
     * Getter for property microstructureOperations.
     * @return Value of property microstructureOperations.
     */
    public Map<String,Operation> getMicrostructureOperations() {
        return this.microstructureOperations;
    }

    /**
     * Setter for property microstructureOperations.
     * @param operations New value of property microstructureOperations.
     */
    public void setMicrostructureOperations(Map<String,Operation> microstructureOperations) {
        this.microstructureOperations = microstructureOperations;
    }
}
