/*
 * PSDTooSmallException.java
 *
 * Created on September 10, 2007, 2:19 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.exceptions;

/**
 *
 * @author mscialom
 */

public class PSDTooSmallException extends Exception {
    public PSDTooSmallException(String text) {
        super(text);
    }
}