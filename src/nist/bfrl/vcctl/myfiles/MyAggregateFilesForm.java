/*
 * MyAggregateFilesForm.java
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
public class MyAggregateFilesForm extends ActionForm {

    /**
     * Holds value of property aggregateOperations.
     */
    private Map<String,Operation> aggregateOperations;

    /**
     * keyed getter for property aggregateOperations.
     * @param key key of the property.
     * @return Value of the property at <CODE>key</CODE>.
     */
    public Operation getAggregateOperations(String key) {
        return this.aggregateOperations.get(key);
    }

    /**
     * Getter for property aggregateOperations.
     * @return Value of property aggregateOperations.
     */
    public Map<String,Operation> getAggregateOperations() {
        return this.aggregateOperations;
    }

    /**
     * Setter for property aggregateOperations.
     * @param operations New value of property aggregateOperations.
     */
    public void setAggregateOperations(Map<String,Operation> aggregateOperations) {
        this.aggregateOperations = aggregateOperations;
    }
}
