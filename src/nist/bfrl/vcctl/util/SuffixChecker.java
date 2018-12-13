/*
 * SuffixChecker.java
 *
 * Created on October 27, 2005, 3:01 PM
 *
 * To change this template, choose Tools | Options and locate the template under
 * the Source Creation and Management node. Right-click the template and choose
 * Open. You can then make changes to the template in the Source Editor.
 */

package nist.bfrl.vcctl.util;

/**
 *
 * @author tahall
 */
public class SuffixChecker {
    
    /** Creates a new instance of SuffixChecker */
    public SuffixChecker() {
    }
    
    static public boolean hasSuffix(String name, String suffix) {
        return name.endsWith(suffix);
    }
    
    static public String addSuffix(String name, String suffix) {
        if (!name.endsWith(suffix)) {
            // Check also that name doesn't end with a 'dot'
            if (name.endsWith(".")) {
                name = name.substring(0, name.length()-2);
            }
            name = name + suffix;
        }
        return name;
    }
}
