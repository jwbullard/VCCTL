/*
 * SampleData.java
 *
 * Created on April 18, 2005, 11:50 AM
 */

package nist.bfrl.vcctl.operation.sample;

import java.beans.*;
import java.io.*;

import java.util.ArrayList;
import java.text.*;
import nist.bfrl.vcctl.exceptions.PSDTooSmallException;

import nist.bfrl.vcctl.operation.PSD;

/**
 * @author tahall
 */
public class PSDSample extends Object implements Serializable {
    
    public double diameter[];
    public double massfrac[];
    
    /**
     * Holds value of property resolution.
     */
    private double resolution;
    
    /**
     * Holds value of property one_pixel_bias.
     */
    private double one_pixel_bias;
    
    public void set_parameters(PSD psd,
            double resolution,
            long maxDiameter,
            long total_pixels) throws PSDTooSmallException {
        
        setResolution(resolution);
        setMax_diameter(maxDiameter);
        initialize_arrays(psd);
        // set_number_of_particles2(total_pixels);
        one_pixel_bias = new OnePixelBias(psd.diameter, psd.massfrac, diameter).calculate();
    }
    
    public PSDSample() {
        /*
         * Empty constructor
         */
    }
    
    /**
     * Getter for property resolution.
     * @return Value of property resolution.
     */
    public double getResolution() {
        
        return this.resolution;
    }
    
    /**
     * Setter for property resolution.
     * @param resolution New value of property resolution.
     */
    public void setResolution(double resolution) {
        
        this.resolution = resolution;
    }
    
    public void initialize_arrays(PSD psd) {
        quantize_diameters(psd.diameter);
        compute_mass_fractions(psd.diameter, psd.massfrac);
    }
    
    private void quantize_diameters(ArrayList diam) {
        /**
         * qdiam holds the quantized diameters, which
         * are multiples of the system resolution,
         * i.e., diameter[0] = resolution in microns,
         * equivalent to one pixel.
         */
        ArrayList qdiam = new ArrayList();
        double diameter = getResolution();
        double step = getResolution();
        // First diameter is 1 * resolution
        qdiam.add(new Double(diameter));
        
        /**
         * Loop through all diameters in the PSD
         * Creating quantized diameters at all
         * multiples of the resolution up to the
         * largest particle size.
         *
         * Once particle sizes begin exceeding
         * 31.0 microns, we do not add diameters
         * for zero-probability bins; below 31.0,
         * we do.
         *
         * Also, no particle with diameter greater
         * than SIZE_SAFETY_COEFFICIENT * minimum dimension can
         * be in the sample.
         */
        
        // double max_diameter = 0.8 * (double)this.getMax_diameter();
        double maxDiameter = (double)this.getMax_diameter();
        
        for (int i=0; i<diam.size(); i++) {
            double nextdiam = (Double)diam.get(i);
            // if (nextdiam > max_diameter) {
            if (nextdiam > maxDiameter) {
                break;
            }
            double cutoff = diameter + step/2.0;
            if (nextdiam <= cutoff) {
                continue;
            } else {
                while (nextdiam > cutoff) {
                    diameter += step;
                    cutoff += step;
                    if (diameter <= 31.0) {
                        qdiam.add(new Double(diameter));
                    }
                }
                if (diameter > 31.0) {
                    qdiam.add(new Double(diameter));
                }
            }
        }
        
        /**
         * Copy quantized diameters into an array of doubles
         * for easier access with no casting needed.
         */
        this.diameter = new double[qdiam.size()];
        for (int j=0; j<this.diameter.length; j++) {
            this.diameter[j] = (Double)qdiam.get(j);
        }
    }
    
    public void compute_mass_fractions(ArrayList diam, ArrayList massfrac) {
        if (diameter == null) {
            throw new RuntimeException();
        }
        
        /**
         * Create the array to hold the mass fractions
         * and get the system resolution, in microns.
         */
        this.massfrac = new double[diameter.length];
        double res = getResolution();
        
        /**
         * Step 1: build a cumulative probability distribution
         */
        double[] cumprob = new double[massfrac.size()];
        cumprob[0] = (Double)massfrac.get(0);
        for (int i=1; i<cumprob.length; i++) {
            cumprob[i] = cumprob[i-1] + (Double)massfrac.get(i);
        }
        
        /**
         * Step 2: calculate the cumulative mass fraction at
         * the bin levels.
         */
        double[] cum_bin_prob = new double[diameter.length];
        
        for (int i=0; i<(cum_bin_prob.length-1); i++) {
            double cutoff = 0.5 * (diameter[i] + diameter[i+1]);
            int j;
            for (j=0; j<diam.size(); j++) {
                if ((Double)diam.get(j) >= cutoff) {
                    break;
                }
            }
            
            double dj = (Double)diam.get(j);
            double cj = cumprob[j];
            double cj1, dj1;
            if (j == 0) {
                cj1 = 0.0;
                dj1 = 0.0;
            } else {
                cj1 = cumprob[j-1];
                dj1 = (Double)diam.get(j-1);
            }
            double cpb_i = cj1 + (cutoff - dj1)*(cj - cj1) / (dj - dj1);
            cum_bin_prob[i] = cpb_i;
        }
        cum_bin_prob[cum_bin_prob.length-1] = 1.0;
        
        this.massfrac[0] = cum_bin_prob[0];
        for (int i=1; i < this.massfrac.length; i++) {
            this.massfrac[i] = cum_bin_prob[i] - cum_bin_prob[i-1];
        }
    }
    
    public double total_mass_fraction() {
        if (this.massfrac == null) {
            return 0.0;
        }
        
        double total = 0.0;
        for (int i=0; i<this.massfrac.length; i++) {
            total += this.massfrac[i];
        }
        
        return total;
    }
    
    /**
     * Getter for property one_pixel_bias.
     * @return Value of property one_pixel_bias.
     */
    public double getOne_pixel_bias() {
        
        return this.one_pixel_bias;
    }
    
    static private NumberFormat pbf = new DecimalFormat("0.000000");

    /**
     * Holds value of property max_diameter.
     */
    private long max_diameter;

    /**
     * Getter for property max_diameter.
     * @return Value of property max_diameter.
     */
    public long getMax_diameter() {
        return this.max_diameter;
    }

    /**
     * Setter for property max_diameter.
     * @param max_diameter New value of property max_diameter.
     */
    public void setMax_diameter(long max_diameter) {
        this.max_diameter = max_diameter;
    }

}
