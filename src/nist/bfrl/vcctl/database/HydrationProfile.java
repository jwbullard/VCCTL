/*
 * HydrationProfile.java
 *
 * Created on February 7, 2006, 5:13 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.database;

/**
 *
 * @author tahall
 */
public class HydrationProfile {
    
    /** Creates a new instance of HydrationProfile */
    public HydrationProfile() {
    }

    /**
     * Holds value of property name.
     */
    private String name;

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
     * Holds value of property state.
     */
    private byte[] state;

    /**
     * Getter for property state.
     * @return Value of property state.
     */
    public byte[] getState() {
        return this.state;
    }

    /**
     * Setter for property state.
     * @param state New value of property state.
     */
    public void setState(byte[] state) {
        this.state = state;
    }
    
    /*
    public void save() throws SQLException, SQLArgumentException {
        String name = this.getName();
        byte[] xml = this.getState();
        
        OperationDatabase.save_profile(name, xml);
    }
     **/
    
    /*
    public byte[] load(String name) throws SQLException, SQLArgumentException {
        byte[] xml = OperationDatabase.load_profile(name);
        
        return xml;
    }
     **/
    
}
