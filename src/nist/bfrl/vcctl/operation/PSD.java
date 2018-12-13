/*
 * PSD.java
 *
 * Created on April 4, 2005, 4:01 PM
 */

package nist.bfrl.vcctl.operation;

import java.util.ArrayList;
import java.io.*;

/**
 *
 * @author tahall
 */
public class PSD {
    
    private String name;
    
    public String getName() {
        return this.name;
    }
    
    /** Creates a new instance of PSD */
    public PSD(String name, String psdfiletext) {
        this.name = name;
        diameter = new ArrayList();
        massfrac = new ArrayList();
        parse(psdfiletext);
    }
    
    public ArrayList diameter;
    public ArrayList massfrac;
    
    /**
     * Holds value of property rows.
     */
    private void parse(String psdfiletext) {
        try {
            BufferedReader rdr = new BufferedReader(new StringReader(psdfiletext));
            String line = rdr.readLine();
            // First line might be table header
            if (line.contains("Diam") || line.contains("frac")) {
                line = rdr.readLine();
            }
            Double[] res = new Double[2];
            while (line != null) {
                // Each row is an array of two doubles
                res = parseLine(line);
                if (res != null) {
                    diameter.add(res[0]);
                    massfrac.add(res[1]);
                }
                
                line = rdr.readLine();
            }
            
        } catch (IOException io) {
            System.out.println(io);
        }
    }
    
    private Double[] parseLine(String line) {
        Double[] retval = null;
        line = line.trim();
        // Delimiter may be space or tab
        int iDelimiter = line.indexOf(' ');
        if (iDelimiter == -1) {
            iDelimiter = line.indexOf('\t');
        }
        try {
            double diam = Double.valueOf(line.substring(0, iDelimiter));
            double prob = Double.valueOf(line.substring(iDelimiter).trim());
            retval = new Double[2];
            retval[0] = diam;
            retval[1] = prob;
        } catch (NumberFormatException nfe) {
            // Cannot parse doubles
            System.err.println(nfe);
        }
        
        return retval;
    }
    
}
