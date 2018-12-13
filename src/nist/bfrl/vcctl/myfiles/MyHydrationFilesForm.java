/*
 * MyHydrationFilesForm.java
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
public class MyHydrationFilesForm extends ActionForm {

    /**
     * Holds value of property hydrationOperations.
     */
    private Map<String,Operation> hydrationOperations;

    /**
     * keyed getter for property hydrationOperations.
     * @param key key of the property.
     * @return Value of the property at <CODE>key</CODE>.
     */
    public Operation getHydrationOperations(String key) {
        return this.hydrationOperations.get(key);
    }

    /**
     * Getter for property hydrationOperations.
     * @return Value of property hydrationOperations.
     */
    public Map<String,Operation> getHydrationOperations() {
        return this.hydrationOperations;
    }

    /**
     * Setter for property hydrationOperations.
     * @param operations New value of property hydrationOperations.
     */
    public void setHydrationOperations(Map<String,Operation> hydrationOperations) {
        this.hydrationOperations = hydrationOperations;
    }
}
