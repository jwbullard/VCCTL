/*
 * OnePixelBias.java
 *
 * Created on April 26, 2005, 1:12 PM
 */

package nist.bfrl.vcctl.operation.sample;

import java.util.ArrayList;
import nist.bfrl.vcctl.exceptions.PSDTooSmallException;

/**
 *
 * @author tahall
 */
public class OnePixelBias {
    
    private double factor = Math.PI / 6.00;
       
    private double[] raw_diameter;
    private double[] raw_fraction;
    private double d0, d1;
    
    /** Creates a new instance of OnePixelBias */
    public OnePixelBias(ArrayList raw_diam, ArrayList raw_frac, double[] quantized_diam) throws PSDTooSmallException {
        if (quantized_diam.length >= 2) {
            raw_diameter = new double[raw_diam.size()];
            for (int i=0; i<raw_diameter.length; i++) {
                raw_diameter[i] = (Double)raw_diam.get(i);
            }
            
            raw_fraction = new double[raw_frac.size()];
            for (int i=0; i<raw_fraction.length; i++) {
                raw_fraction[i] = (Double)raw_frac.get(i);
            }
            
            d0 = quantized_diam[0];
            d1 = quantized_diam[1];
        } else {
            throw new PSDTooSmallException("The PSD contains less than 2 different diameters.");
        }
    }
    
    public double calculate() {
        double[] cumpsd = new double[raw_diameter.length];
        
        double bias = 1.0;
        boolean cutoff_reached = false;
        double one_pixel_cutoff = (d0 + d1) / 2.0;
        int upperbin = 0;
        
        cumpsd[0] = raw_fraction[0];
        
        double cpi;
        for (int i=1; (i<raw_diameter.length) && !cutoff_reached; i++) {
            cpi = cumpsd[i-1] + raw_fraction[i];
            cumpsd[i] = cpi;
            if (raw_diameter[i] > one_pixel_cutoff) {
                cutoff_reached = true;
                upperbin = i;
            }
        }
        
        if (upperbin != 1) {
            /**
             * First, normalize the cumulative psd for those diameters up to
             * and including the cutoff point
             **/
            for (int i=0; i<=upperbin; i++) {
                cpi = cumpsd[i];
                cumpsd[i] /= cumpsd[upperbin];
                cpi = cumpsd[i];
            }
            
            /***
             *	Calculate the volume density function normalized
             *	between 0 and 0.5 * (dval1 + dval2) effective diameter
             ***/
            double [] vdist = new double[upperbin+1];
            for (int i = 1; i <= upperbin; i++) {
                double vdi = cumpsd[i] - cumpsd[i-1];
                vdist[i] = vdi;
            }
            vdist[0] = 0.0;
           
            double[] kernel = new double[upperbin+1];
            kernel[0] = 0.0;
            for (int i = 1; i <= upperbin; i++) {
                kernel[i] = vdist[i] * d0 / raw_diameter[i];
            }
            
            /* Apply trapezoidal rule */
            
            bias = 0.0;
            for (int i = 1; i <= upperbin; i++) {
                bias += 0.5 * (raw_diameter[i] - raw_diameter[i-1]) * (kernel[i-1] + kernel[i]);
            }
            
            /* Now divide by integral of vdist over the range of interest */
            
            for (int i = 1; i <= upperbin; i++) {
                kernel[i] = vdist[i];
            }
            
            double denom = 0.0;
            for (int i = 1; i <= upperbin; i++) {
                denom += 0.5 * (raw_diameter[i] - raw_diameter[i-1]) * (kernel[i-1] + kernel[i]);
            }
            
            bias /= denom;
        }
        
        return bias;
    }
}
