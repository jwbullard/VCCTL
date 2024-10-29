/*
 * DBFileException.java
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
public class DBFileException extends Exception {
    
    /**
     * Constructs a new exception with the specified detail message, error type and data type
     * @param errorType The error type
     * @param type The data type
     * @param message The detail message.
     */
    public DBFileException(String errorType, String type, String message) {
        super(message);
        this.errorType = errorType;
        this.type = type;
    }
    
    /**
     * Constructs a new exception with the specified detail message, error type and data type
     * @param errorType The error type
     * @param message The detail message.
     */
    public DBFileException(String errorType, String message) {
        super(message);
        this.errorType = errorType;
    }
    
    /**
     * Constructs a new exception with the specified cause, error type and data type
     * @param errorType The error type
     * @param type The data type
     * @param cause The cause.
     */
    public DBFileException(String errorType, String type, Throwable cause) {
        super(cause);
        this.errorType = errorType;
        this.type = type;
    }
    
    /**
     * Constructs a new exception with the specified detail message and cause.
     * @param errorType The error type
     * @param type The data type
     * @param message The detail message.
     * @param cause The cause.
     */
    public DBFileException(String errorType, String type, String message, Throwable cause) {
        super(message, cause);
        this.errorType = errorType;
        this.type = type;
    }

    /**
     * Holds value of property errorType.
     */
    private String errorType;

    /**
     * Getter for property type.
     * @return Value of property type.
     */
    public String getErrorType() {
        return this.errorType;
    }

    /**
     * Setter for property type.
     * @param type New value of property type.
     */
    public void setErrorType(String errorType) {
        this.errorType = errorType;
    }

    /**
     * Holds value of property type.
     */
    private String type;

    /**
     * Getter for property type.
     * @return Value of property type.
     */
    public String getType() {
        return this.type;
    }

    /**
     * Setter for property type.
     * @param type New value of property type.
     */
    public void setType(String type) {
        this.type = type;
    }
    
}
