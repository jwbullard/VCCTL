/*
 * MyFilesForm.java
 *
 * Created on September 13, 2007, 3:05 AM
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
public class MyFilesForm extends ActionForm {
    
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
