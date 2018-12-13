/*
 * LoginForm.java
 *
 * Created on January 19, 2005, 3:10 PM
 */

package nist.bfrl.vcctl.admin;

import org.apache.struts.action.*;

/**
 * @author tahall
 */
public class LoginForm extends ActionForm {

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
    
}
