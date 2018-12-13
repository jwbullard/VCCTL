/*
 * SQLDuplicatedKeyException.java
 *
 * Created on December 12, 2007, 3:43 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.exceptions;

import java.sql.SQLException;

/**
 *
 * @author mscialom
 */
public class SQLDuplicatedKeyException extends SQLException {
    
    /**
     * Constructs a new exception with the specified detail message, table and key
     * @param table The table
     * @param key The key
     * @param message The detail message.
     */
    public SQLDuplicatedKeyException(String table, String key, String message) {
        super(message);
        this.table = table;
        this.key = key;
    }
    
    /**
     * Constructs a new exception with the specified detail message, table and key
     * @param table The table
     * @param key The key
     * @param additionalParameter The additionalParameter
     * @param message The detail message.
     */
    public SQLDuplicatedKeyException(String table, String key, String additionalParameter, String message) {
        super(message);
        this.table = table;
        this.key = key;
        this.additionalParameter = additionalParameter;
    }
    
    /**
     * Constructs a new exception with the specified SQLState, table and key
     * @param table The table
     * @param key The key
     * @param SQLState The SQLState.
     */
    public SQLDuplicatedKeyException(String table, String key, String message, String SQLState, int vendorCode) {
        super(message, SQLState, vendorCode);
        this.table = table;
        this.key = key;
    }
    
    /**
     * Constructs a new exception with the specified SQLState, table and key
     * @param table The table
     * @param key The key
     * @param additionalParameter The additionalParameter
     * @param SQLState The SQLState.
     */
    public SQLDuplicatedKeyException(String table, String key, String additionalParameter, String message, String SQLState, int vendorCode) {
        super(message, SQLState, vendorCode);
        this.table = table;
        this.key = key;
        this.additionalParameter = additionalParameter;
    }

    /**
     * Holds value of property table.
     */
    private String table;

    /**
     * Getter for property table.
     * @return Value of property table.
     */
    public String getTable() {
        return this.table;
    }

    /**
     * Setter for property table.
     * @param table New value of property table.
     */
    public void setTable(String table) {
        this.table = table;
    }

    /**
     * Holds value of property key.
     */
    private String key;

    /**
     * Getter for property key.
     * @return Value of property key.
     */
    public String getKey() {
        return this.key;
    }

    /**
     * Setter for property key.
     * @param key New value of property key.
     */
    public void setKey(String key) {
        this.key = key;
    }

    /**
     * Holds value of property additionalParameter.
     */
    private String additionalParameter;

    /**
     * Getter for property additionalParameter.
     * @return Value of property additionalParameter.
     */
    public String getAdditionalParameter() {
        return this.additionalParameter;
    }

    /**
     * Setter for property additionalParameter.
     * @param additionalParameter New value of property additionalParameter.
     */
    public void setAdditionalParameter(String additionalParameter) {
        this.additionalParameter = additionalParameter;
    }
    
}
