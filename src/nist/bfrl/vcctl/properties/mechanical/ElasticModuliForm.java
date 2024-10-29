/*
 * ElasticModuliForm.java
 *
 * Created on May 25, 2006, 2:30 PM
 */

package nist.bfrl.vcctl.properties.mechanical;

import javax.servlet.http.HttpServletRequest;
import org.apache.struts.action.ActionErrors;
import org.apache.struts.action.ActionMapping;
import org.apache.struts.action.ActionMessage;

/**
 *
 * @author tahall
 * @version
 */

public class ElasticModuliForm extends org.apache.struts.action.ActionForm {
    
    /**
     *
     */
    public ElasticModuliForm() {
        super();
        // TODO Auto-generated constructor stub
    }
    
    public ActionErrors validate(ActionMapping mapping,
            HttpServletRequest request) {
        ActionErrors errors = new ActionErrors();
        
        return errors;
    }
    
    public String getElasticInput() {
        String filename = this.getMicrostructure().split("/")[1];
        
        String early_age = "0";
        if (this.isEarly_age_option()) {
            early_age = "1";
        }
        String resolve = "0";
        if (this.isResolve_spatial_variations()) {
            resolve = "1";
        }
        
        return "../" + filename + "\n" + early_age + "\n" + resolve + "\n";
    }
    
    /**
     * Holds value of property microstructure.
     */
    private String microstructure;
    
    /**
     * Getter for property microstructure.
     * @return Value of property microstructure.
     */
    public String getMicrostructure() {
        return this.microstructure;
    }
    
    /**
     * Setter for property microstructure.
     * @param microstructure New value of property microstructure.
     */
    public void setMicrostructure(String microstructure) {
        this.microstructure = microstructure;
    }
    
    /**
     * Holds value of property resolve_spatial_variations.
     */
    private boolean resolve_spatial_variations;
    
    /**
     * Getter for property resolve_spatial_variations.
     * @return Value of property resolve_spatial_variations.
     */
    public boolean isResolve_spatial_variations() {
        return this.resolve_spatial_variations;
    }
    
    /**
     * Setter for property resolve_spatial_variations.
     * @param resolve_spatial_variations New value of property resolve_spatial_variations.
     */
    public void setResolve_spatial_variations(boolean resolve_spatial_variations) {
        this.resolve_spatial_variations = resolve_spatial_variations;
    }
    
    /**
     * Holds value of property early_age_option.
     */
    private boolean early_age_option;
    
    /**
     * Getter for property early_age_option.
     * @return Value of property early_age_option.
     */
    public boolean isEarly_age_option() {
        return this.early_age_option;
    }
    
    /**
     * Setter for property early_age_option.
     * @param early_age_option New value of property early_age_option.
     */
    public void setEarly_age_option(boolean early_age_option) {
        this.early_age_option = early_age_option;
    }


}
