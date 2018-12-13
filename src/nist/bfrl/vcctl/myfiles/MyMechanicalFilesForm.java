/*
 * MyMechanicalFilesForm.java
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
public class MyMechanicalFilesForm extends ActionForm {

    /**
     * Holds value of property elasticModuliOperations.
     */
    private Map<String,Operation> elasticModuliOperations;

    /**
     * keyed getter for property elasticModuliOperations.
     * @param key key of the property.
     * @return Value of the property at <CODE>key</CODE>.
     */
    public Operation getElasticModuliOperations(String key) {
        return this.elasticModuliOperations.get(key);
    }

    /**
     * Getter for property elasticModuliOperations.
     * @return Value of property elasticModuliOperations.
     */
    public Map<String,Operation> getElasticModuliOperations() {
        return this.elasticModuliOperations;
    }

    /**
     * Setter for property elasticModuliOperations.
     * @param operations New value of property elasticModuliOperations.
     */
    public void setElasticModuliOperations(Map<String,Operation> elasticModuliOperations) {
        this.elasticModuliOperations = elasticModuliOperations;
    }
}
