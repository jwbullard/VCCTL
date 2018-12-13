/*
 * User.java
 *
 * Created on March 16, 2005, 1:33 PM
 */

package nist.bfrl.vcctl.database;

import java.beans.*;
import java.io.Serializable;
import java.sql.*;

import java.util.*;

/**
 * @author tahall
 */
public class User extends Object implements Serializable {
    
    static private HashMap users;
    static {
        users = new HashMap();
    }
    
    /**
     * Holds value of property name.
     */
    private String name;
    
    /**
     * Holds value of property password.
     */
    /*
    private String password;
    
    boolean usePassword;
     **/
    
    /*
    public User() {
        name = "";
        password = "";
        usePassword = false;
    }
     **/
    
    /*
    public User(String name, int id) {
        this.name = name;
        this.password = "";
        this.usePassword = false;
        this.id = id;
        users.put(name, this);
    }
     **/
    
    
    public User(String name, String email) {
        this.name = name;
        this.email = email;
        
        /*
         * Add to map of all users
         *
         */
        users.put(name, this);
    }
    
    /*
    private boolean isValid() {
        if (name.length() < 1) {
            return false;
        }
        
        return true;
    }
     **/
    
    /**
     * Holds value of property id.
     */
    /*
    private int id;
     **/
    
    /*
    public static int findUser(String name,
            String password) {
        
        int retval = 1;
        
        return retval;
    }
     **/
    
    
    /**
     * Getter for property name.
     * @return Value of property name.
     */
    public String getName() {
        
        return this.name;
    }
    
    /**
     * Setter for property name.
     * @param name New value of property name.
     */
    public void setName(String name) {
        
        this.name = name;
    }
    
    /**
     * Getter for property password.
     * @return Value of property password.
     */
    /*
    public String getPassword() {
        
        return this.password;
    }
     **/
    
    /**
     * Setter for property password.
     * @param password New value of property password.
     */
    /*
    public void setPassword(String password) {
        
        this.password = password;
    }
     **/
    
    /**
     * Getter for property id.
     * @return Value of property id.
     */
    /*
    public int getId() {
        
        return this.id;
    }
     **/

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

    /**
     * Holds value of property registration_date.
     */
    private Timestamp registration_date;

    /**
     * Getter for property registration_date.
     * @return Value of property registration_date.
     */
    public Timestamp getRegistration_date() {
        return this.registration_date;
    }

    /**
     * Setter for property registration_date.
     * @param registration_date New value of property registration_date.
     */
    public void setRegistration_date(Timestamp registration_date) {
        this.registration_date = registration_date;
    }

    /**
     * Holds value of property last_login.
     */
    private Timestamp last_login;

    /**
     * Getter for property last_login.
     * @return Value of property last_login.
     */
    public Timestamp getLast_login() {
        return this.last_login;
    }

    /**
     * Setter for property last_login.
     * @param last_login New value of property last_login.
     */
    public void setLast_login(Timestamp last_login) {
        this.last_login = last_login;
    }


    
}
