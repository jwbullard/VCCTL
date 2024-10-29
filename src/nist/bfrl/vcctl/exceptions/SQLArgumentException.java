/*
 * SQLArgumentException.java
 *
 * Created on November 22, 2007, 3:08 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.exceptions;

/**
 *
 * @author mscialom
 */
public class SQLArgumentException extends Exception {
    
    /**
     * Constructs a new exception with the specified detail message.
     * @param errorType The error type
     * @param column The table column corresponding to the empty argument
     * @param message The detail message.
     */
    public SQLArgumentException(String errorType, String column, String message) {
        super(message);
        this.errorType = errorType;
        this.column = column;
    }

    /**
     * Holds value of property column.
     */
    private String column;

    /**
     * Getter for property column.
     * @return Value of property column.
     */
    public String getColumn() {
        return this.column;
    }

    /**
     * Setter for property column.
     * @param column New value of property column.
     */
    public void setColumn(String column) {
        this.column = column;
    }

    /**
     * Holds value of property errorType.
     */
    private String errorType;

    /**
     * Getter for property errorType.
     * @return Value of property errorType.
     */
    public String getErrorType() {
        return this.errorType;
    }

    /**
     * Setter for property errorType.
     * @param errorType New value of property errorType.
     */
    public void setErrorType(String errorType) {
        this.errorType = errorType;
    }
    
}
