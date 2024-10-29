/*
 * OperationState.java
 *
 * Created on August 30, 2005, 11:25 AM
 */

package nist.bfrl.vcctl.operation;

import java.beans.*;
import java.io.*;

/**
 *
 * @author tahall
 */
public class OperationState {
    
    /** Creates a new instance of OperationState */
    public OperationState() {
    }
    
    public static byte[] save_to_Xml(Object opbean) {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        XMLEncoder encoder = new XMLEncoder(new BufferedOutputStream(bos));
        
        encoder.writeObject(opbean);
        encoder.close();
        
        return bos.toByteArray();
    }
    
    public static Object restore_from_Xml(byte[] opxml) {
        ByteArrayInputStream bis = new ByteArrayInputStream(opxml);
        XMLDecoder decoder = new XMLDecoder(new BufferedInputStream(bis));
        
        Object opform = decoder.readObject();
        decoder.close();
        
        return opform;
    }
    
}
