/*
 * RegisterForm.java
 *
 * Created on August 21, 2007, 3:33 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.admin;

import org.apache.struts.action.ActionForm;

/**
 *
 * @author mscialom
 */
public class RegisterForm extends ActionForm {
    /**
     * Holds value of property userName.
     */
    private String userName;

    /**
     * Getter for property userName.
     * @return Value of property userName.
     */
    public String getUserName() {
        return this.userName;
    }

    /**
     * Setter for property userName.
     * @param userName New value of property userName.
     */
    public void setUserName(String userName) {
        this.userName = userName;
    }

    /**
     * Holds value of property password.
     */
    private String password;

    /**
     * Getter for property password.
     * @return Value of property password.
     */
    public String getPassword() {
        return this.password;
    }

    /**
     * Setter for property password.
     * @param password New value of property password.
     */
    public void setPassword(String password) {
        this.password = password;
    }

    /**
     * Holds value of property email.
     */
    private String email;

    /**
     * Getter for property email.
     * @return Value of property email.
     */
    public String getEmail() {
        return this.email;
    }

    /**
     * Setter for property email.
     * @param email New value of property email.
     */
    public void setEmail(String email) {
        this.email = email;
    }
    
}
