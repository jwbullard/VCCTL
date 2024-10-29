/*
 * InitialMicrostructure.java
 *
 * Created on May 3, 2005, 9:12 AM
 */

package nist.bfrl.vcctl.operation.microstructure;

import java.sql.SQLException;
import nist.bfrl.vcctl.exceptions.DBFileException;
import nist.bfrl.vcctl.exceptions.PSDTooSmallException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.operation.*;
import nist.bfrl.vcctl.operation.sample.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.application.Vcctl;
import nist.bfrl.vcctl.util.*;

import java.util.*;
import java.io.*;

/**
 *
* @author tahall
 */
public class InitialMicrostructure {
    
    /***************************************************************************
     ***************************************************************************
     **
     ** Public functions:
     **       1. The setParameters(...) member functions set necessary
     **          parameters from the ActionForms.
     **
     ***************************************************************************
     **************************************************************************/
    
    public boolean setParameters(GenerateMicrostructureForm microstructureForm) throws PSDTooSmallException, SQLArgumentException, DBFileException, SQLException {
        
        /**
         * Set the simulation parameters
         */
        
        try {
            /**
             * Get the random number generator seed
             */
            int rng_seed = Integer.valueOf(microstructureForm.getRng_seed());
            if (rng_seed == 0 || microstructureForm.isUse_own_random_seed() == false) {
                // get an integer between -32768 and 0
                rng_seed = -(int)(Math.round(Math.random()*Math.pow(2.0,15.0)));
            }
            
            setRng_seed(rng_seed);
            
            /**
             * Get the resolution
             */
            double binder_resolution = Double.valueOf(microstructureForm.getBinder_resolution());
            setBinder_resolution(binder_resolution);
            
            /**
             * Get x, y, and z dimensions
             * Dimensions are given in millimeters, so we add to divide them by the resolution
             */
            int xdim = (int)(Double.valueOf(microstructureForm.getBinder_x_dim())/binder_resolution);
            int ydim = (int)(Double.valueOf(microstructureForm.getBinder_y_dim())/binder_resolution);
            int zdim = (int)(Double.valueOf(microstructureForm.getBinder_z_dim())/binder_resolution);
            
            setBinder_xdim(xdim);
            setBinder_ydim(ydim);
            setBinder_zdim(zdim);
            
            /**
             * Use real shapes (true) or spheres (false).  If true,
             * get the shape set.
             */
            boolean real_shapes = microstructureForm.isReal_shapes();
            setReal_shapes(real_shapes);
            
            String shape_set;
            if (real_shapes) {
                shape_set = microstructureForm.getShape_set();
            } else {
                shape_set = "";
            }
            setShape_set(shape_set);
            
            /**
             * Flocculation: a value of zero for degree of flocculation means no
             *               flocculation.
             */
            if (microstructureForm.isUse_flocculation())
                setFlocdegree(Double.valueOf(microstructureForm.getFlocdegree()));
            else
                setFlocdegree(0.0);
            
            /**
             * Aggregate thickness
             */
            /*
            int aggregate_thickness = Integer.valueOf(microstructureForm.getAggregate_thickness());
            setAggregate_thickness(aggregate_thickness);
             **/
            
            /**
             * Dispersion distance: must be one of 0, 1, or 2.
             */
            if (microstructureForm.isUse_dispersion_distance())
                setDispersion_distance(Integer.valueOf(microstructureForm.getDispersion_distance()));
            else
                setDispersion_distance(0);
            
            /**
             * Get the file name, append .img if necessary
             */
            this.setMixName(microstructureForm.getMix_name());
            /*
            String mixName = microstructureForm.getFile_name();
            if (mixName.indexOf(".img") < 0) {
                mixName += ".img";
            }
            setFilename(mixName);
             **/
            
            /**
             * Notes on this "Generate microstructure" operation: free-form notes
             * that can contain any information the user chooses
             */
            this.setNotes(microstructureForm.getNotes());
        } catch (NumberFormatException nfe) {
            nfe.printStackTrace();
            return false;
        }
        
        
        /**
         * SCM, calcium sulfates and aggregate parameters
         **/
        
        /**
         *  Step 1: get all the mass fractions and check that they add up
         *  correctly.
         */
        // long binder_pixels = 0;
        long cement_pixels = 0;
        long clinker_pixels = 0;
        long silica_fume_pixels = 0;
        long fly_ash_pixels = 0;
        long slag_pixels = 0;
        long caco3_pixels = 0;
        long free_lime_pixels = 0;
        long inert_filler_pixels = 0;
        long dihydrate_pixels = 0;
        long hemihydrate_pixels = 0;
        long anhydrite_pixels = 0;
        
        long coarse_aggregate_pixels = 0;
        long fine_aggregate_pixels = 0;
        
        long systemVolume = this.getBinder_xdim() * this.getBinder_ydim() * this.getBinder_zdim();
        double binder_volfrac = 0.0;
        double cement_volfrac = 0.0;
        double clinker_volfrac = 0.0;
        double silica_fume_volfrac = 0.0;
        double fly_ash_volfrac = 0.0;
        double slag_volfrac = 0.0;
        double caco3_volfrac = 0.0;
        double free_lime_volfrac = 0.0;
        double inert_filler_volfrac = 0.0;
        double dihydrate_volfrac = 0.0;
        double hemihydrate_volfrac = 0.0;
        double anhydrite_volfrac = 0.0;
        
        long binderVolume;
        
        double coarse_aggregate_volfrac = 0.0;
        double fine_aggregate_volfrac = 0.0;
        
        try {
            String vfi;
            vfi = microstructureForm.getBinder_volfrac();
            binder_volfrac = Double.parseDouble(vfi);
            
            this.setBinderVolumeFraction(binder_volfrac);
            
            // normalize binder vol frac, because it's the volume fraction in the MIX (which include the aggregate)
            // genmic expect vol frac(water) + vol frac(binder) = 1
            if (binder_volfrac <= 0.0) {
                return false;
            }
            
            double waterVolFrac = Double.parseDouble(microstructureForm.getWater_volfrac());
            
            this.setWaterVolumeFraction(waterVolFrac);
            
            // binder_volfrac = binder_volfrac / (binder_volfrac + waterVolFrac);
            
            // binder_pixels = (long)(binder_volfrac * systemVolume);
            
            vfi = microstructureForm.getSilica_fume_volfrac();
            silica_fume_volfrac = Double.parseDouble(vfi);
            silica_fume_pixels = (long)(silica_fume_volfrac * systemVolume);
            
            vfi = microstructureForm.getFly_ash_volfrac();
            fly_ash_volfrac = Double.parseDouble(vfi);
            fly_ash_pixels = (long)(fly_ash_volfrac * systemVolume);
            
            vfi = microstructureForm.getSlag_volfrac();
            slag_volfrac = Double.parseDouble(vfi);
            slag_pixels = (long)(slag_volfrac * systemVolume);
            
            vfi = microstructureForm.getCaco3_volfrac();
            caco3_volfrac = Double.parseDouble(vfi);
            caco3_pixels = (long)(caco3_volfrac * systemVolume);
            
            vfi = microstructureForm.getFree_lime_volfrac();
            free_lime_volfrac = Double.parseDouble(vfi);
            free_lime_pixels = (long)(free_lime_volfrac * systemVolume);
            
            vfi = microstructureForm.getInert_filler_volfrac();
            inert_filler_volfrac = Double.parseDouble(vfi);
            inert_filler_pixels = (long)(inert_filler_volfrac * systemVolume);
            
            // For Sulfates (Dihydrate, anhydrate, hemihydrate),
            // the fraction specified on the form is a fraction of
            // the cement volume fraction. So let's normalized them!
            vfi = microstructureForm.getCement_volfrac();
            cement_volfrac = Double.parseDouble(vfi);
            cement_pixels = (long)(cement_volfrac * systemVolume);
            
            vfi = microstructureForm.getDihydrate_volfrac();
            dihydrate_volfrac = Double.parseDouble(vfi);
            dihydrate_volfrac *= cement_volfrac;
            dihydrate_pixels = (long)(dihydrate_volfrac * systemVolume);
            
            vfi = microstructureForm.getAnhydrite_volfrac();
            anhydrite_volfrac = Double.parseDouble(vfi);
            anhydrite_volfrac *= cement_volfrac;
            anhydrite_pixels = (long)(anhydrite_volfrac * systemVolume);
            
            vfi = microstructureForm.getHemihydrate_volfrac();
            hemihydrate_volfrac = Double.parseDouble(vfi);
            hemihydrate_volfrac *= cement_volfrac;
            hemihydrate_pixels = (long)(hemihydrate_volfrac * systemVolume);
            
            // Now adjust the number of clinker pixels by subtracting off
            // sulfate phase fractions
            clinker_volfrac = cement_volfrac - (dihydrate_volfrac + anhydrite_volfrac + hemihydrate_volfrac);
            clinker_pixels = cement_pixels - (dihydrate_pixels + anhydrite_pixels + hemihydrate_pixels);
            
            // These fractions are no longer used in genmic, so set them to 0.0
            this.setDihydrate_mass_fraction(0.0);
            this.setDihydrate_volume_fraction(0.0);
            this.setAnhydrite_mass_fraction(0.0);
            this.setAnhydrite_volume_fraction(0.0);
            this.setHemihydrate_mass_fraction(0.0);
            this.setHemihydrate_volume_fraction(0.0);
        } catch (NumberFormatException nfe) {
            throw new RuntimeException(nfe);
        }
        
        /**
         *  Step 2: get the pdf (distribution) used for each
         *  nonzero mass fraction component and generate a
         *  sample from that pdf + mass fraction.
         */
        // First, remove any existing samples, dissolution bias numbers, etc.
        clear_sample_info();
        
        
        String operationName = microstructureForm.getMix_name();
        String userName = this.getUser_name();
        UserDirectory userDir = new UserDirectory(userName);
        
        // First, cement, which must have a psd and a positive mass fraction
        String cementName = microstructureForm.getCementName();
        String cementPSD = CementDatabase.getCementPSD(microstructureForm.getCementName());
        String psdpath = userDir.getOperationFilePath(microstructureForm.getMix_name(), Constants.CEMENT_PSD_FILE);
        String phaseName;
        phasesVolumeFractions = new HashMap();
        
        ServerFile.saveToFile(psdpath,CementDatabase.getPSDData(cementPSD));
        
        this.setCement_psd(cementPSD);
        String psdtext = CementDatabase.getPSDText(cementPSD);
        PSD psd = new PSD(cementPSD, psdtext);
        PSDSample sample = create_sample3(psd, clinker_pixels);
        phaseName = "c3s";
        add_to_sample_info(phaseName, sample);
        this.phasesVolumeFractions.put(phaseName,new Double(clinker_volfrac));
        
        /**
         * For the others, check that volume fraction is > 0.0
         */
        if (silica_fume_volfrac > 0.0) {   // Silica fume
            String silica_fume = microstructureForm.getSilica_fume_psd();
            if (silica_fume.equalsIgnoreCase("none")) { return false; }
            psdtext = CementDatabase.getPSDText(silica_fume);
            psd = new PSD(silica_fume, psdtext);
            sample = create_sample3(psd, silica_fume_pixels);
            phaseName = "silica_fume";
            add_to_sample_info(phaseName, sample);
            this.phasesVolumeFractions.put(phaseName,new Double(silica_fume_volfrac));
        }
        
        if (fly_ash_volfrac > 0.0) {   // Fly ash
            String fly_ash = microstructureForm.getFly_ash_psd();
            if (fly_ash.equalsIgnoreCase("none")) { return false; }
            String flyash_psd = FlyAsh.get_psd(fly_ash);
            psdtext = CementDatabase.getPSDText(flyash_psd);
            psd = new PSD(fly_ash, psdtext);
            sample = create_sample3(psd, fly_ash_pixels);
            phaseName = "fly_ash";
            add_to_sample_info(phaseName, sample);
            this.phasesVolumeFractions.put(phaseName,new Double(fly_ash_volfrac));
        }
        
        if (slag_volfrac > 0.0) {   // Slag
            String slag = microstructureForm.getSlag_psd();
            if (slag.equalsIgnoreCase("none")) { return false; }
            String slag_psd = Slag.get_psd(slag);
            psdtext = CementDatabase.getPSDText(slag_psd);
            psd = new PSD(slag, psdtext);
            sample = create_sample3(psd, slag_pixels);
            phaseName = "slag";
            add_to_sample_info(phaseName, sample);
            this.phasesVolumeFractions.put(phaseName,new Double(slag_volfrac));
        }
        
        if (caco3_volfrac > 0.0) {   // Caco3
            String caco3 = microstructureForm.getCaco3_psd();
            if (caco3.equalsIgnoreCase("none")) { return false; }
            psdtext = CementDatabase.getPSDText(caco3);
            psd = new PSD(caco3, psdtext);
            sample = create_sample3(psd, caco3_pixels);
            phaseName = "caco3";
            add_to_sample_info(phaseName, sample);
            this.phasesVolumeFractions.put(phaseName,new Double(caco3_volfrac));
        }
        
        if (free_lime_volfrac > 0.0) {   // Free lime
            String free_lime = microstructureForm.getFree_lime_psd();
            if (free_lime.equalsIgnoreCase("none")) { return false; }
            psdtext = CementDatabase.getPSDText(free_lime);
            psd = new PSD(free_lime, psdtext);
            sample = create_sample3(psd, free_lime_pixels);
            phaseName = "free_lime";
            add_to_sample_info(phaseName, sample);
            this.phasesVolumeFractions.put(phaseName,new Double(free_lime_volfrac));
        }
        
        if (inert_filler_volfrac > 0.0) {   // Inert filler
            String inert_filler = microstructureForm.getInert_filler_psd();
            if (inert_filler.equalsIgnoreCase("none")) { return false; }
            String ifpsd = InertFiller.get_psd(inert_filler);
            psdtext = CementDatabase.getPSDText(ifpsd);
            psd = new PSD(inert_filler, psdtext);
            sample = create_sample3(psd, inert_filler_pixels);
            phaseName = "inert_filler";
            add_to_sample_info(phaseName, sample);
            this.phasesVolumeFractions.put(phaseName,new Double(inert_filler_volfrac));
        }
        
//* The sulfates *//
        if (dihydrate_volfrac > 0.0) {
            String dihydrate = microstructureForm.getDihydrate_psd();
            if (dihydrate.equalsIgnoreCase("none")) { return false; }
            psdtext = CementDatabase.getPSDText(dihydrate);
            psd = new PSD(dihydrate, psdtext);
            sample = create_sample3(psd, dihydrate_pixels);
            phaseName = "dihydrate";
            add_to_sample_info(phaseName, sample);
            this.phasesVolumeFractions.put(phaseName,new Double(dihydrate_volfrac));
        }
        
        if (anhydrite_volfrac > 0.0) {
            String anhydrite = microstructureForm.getAnhydrite_psd();
            if (anhydrite.equalsIgnoreCase("none")) { return false; }
            psdtext = CementDatabase.getPSDText(anhydrite);
            psd = new PSD(anhydrite, psdtext);
            sample = create_sample3(psd, anhydrite_pixels);
            phaseName = "anhydrite";
            add_to_sample_info(phaseName, sample);
            this.phasesVolumeFractions.put(phaseName,new Double(anhydrite_volfrac));
        }
        
        if (hemihydrate_volfrac > 0.0) {
            String hemihydrate = microstructureForm.getHemihydrate_psd();
            if (hemihydrate.equalsIgnoreCase("none")) { return false; }
            psdtext = CementDatabase.getPSDText(hemihydrate);
            psd = new PSD(hemihydrate, psdtext);
            sample = create_sample3(psd, hemihydrate_pixels);
            phaseName = "hemihydrate";
            add_to_sample_info(phaseName, sample);
            this.phasesVolumeFractions.put(phaseName,new Double(hemihydrate_volfrac));
        }

        /**
         * Phases distribution
         */

        // Get the name of the PSD used to distribute clinker phases
        // String psdpath = microstructureForm.getPsd_selected();
        
        // psdpath = microstructureForm.getCement_psd();
        
        this.setDistribute_clinker_phases_psd(microstructureForm.getCementName());
        
        // Get the volume fractions and surface area fractions
        double[] volfrac = new double[6];
        volfrac[0] = Double.parseDouble(microstructureForm.getC3s_vf());
        volfrac[1] = Double.parseDouble(microstructureForm.getC2s_vf());
        volfrac[2] = Double.parseDouble(microstructureForm.getC3a_vf());
        volfrac[3] = Double.parseDouble(microstructureForm.getC4af_vf());
        volfrac[4] = Double.parseDouble(microstructureForm.getK2so4_vf());
        volfrac[5] = Double.parseDouble(microstructureForm.getNa2so4_vf());
        
        double[] safrac = new double[6];
        safrac[0] = Double.parseDouble(microstructureForm.getC3s_saf());
        safrac[1] = Double.parseDouble(microstructureForm.getC2s_saf());
        safrac[2] = Double.parseDouble(microstructureForm.getC3a_saf());
        safrac[3] = Double.parseDouble(microstructureForm.getC4af_saf());
        safrac[4] = Double.parseDouble(microstructureForm.getK2so4_saf());
        safrac[5] = Double.parseDouble(microstructureForm.getNa2so4_saf());
        
        this.setVolfrac(volfrac);
        this.setSafrac(safrac);
        
        // Use the Fly Ash set in the 'blend' page
        String flyash_input = microstructureForm.getFlyAshPhaseDistributionInput();
        this.setFlyash_distribution_input(flyash_input);
        
        
        /**
         * Aggregate
         **/
        
        if (microstructureForm.isAdd_aggregate()) {
            coarse_aggregate01_mass_fraction = Double.parseDouble(microstructureForm.getCoarse_aggregate01_massfrac());
            coarse_aggregate02_mass_fraction = Double.parseDouble(microstructureForm.getCoarse_aggregate02_massfrac());
            fine_aggregate01_mass_fraction = Double.parseDouble(microstructureForm.getFine_aggregate01_massfrac());
            fine_aggregate02_mass_fraction = Double.parseDouble(microstructureForm.getFine_aggregate02_massfrac());

            coarse_aggregate01_display_name = microstructureForm.getCoarse_aggregate01_display_name();
            fine_aggregate01_display_name = microstructureForm.getFine_aggregate01_display_name();
            coarse_aggregate02_display_name = microstructureForm.getCoarse_aggregate02_display_name();
            fine_aggregate02_display_name = microstructureForm.getFine_aggregate02_display_name();

            double coarseAggregate01VolFrac = Double.parseDouble(microstructureForm.getCoarse_aggregate01_volfrac());
            double coarseAggregate02VolFrac = Double.parseDouble(microstructureForm.getCoarse_aggregate02_volfrac());

            double fineAggregate01VolFrac = Double.parseDouble(microstructureForm.getFine_aggregate01_volfrac());
            double fineAggregate02VolFrac = Double.parseDouble(microstructureForm.getFine_aggregate02_volfrac());

            double binderVolFrac = Double.parseDouble(microstructureForm.getBinder_volfrac());
            double waterVolFrac = Double.parseDouble(microstructureForm.getWater_volfrac());
            double airVolumeFraction = Double.parseDouble(microstructureForm.getAir_volfrac());
            
            double coarseAggregate01SpecificGravity = Double.parseDouble(microstructureForm.getCoarse_aggregate01_sg());
            double coarseAggregate02SpecificGravity = Double.parseDouble(microstructureForm.getCoarse_aggregate02_sg());
            /* Convert to cubic millimeters */
            coarseAggregate01SpecificGravity /= 1000.0;
            coarseAggregate02SpecificGravity /= 1000.0;

            double fineAggregate01SpecificGravity = Double.parseDouble(microstructureForm.getFine_aggregate01_sg());
            /* Convert to cubic millimeters */
            fineAggregate01SpecificGravity /= 1000.0;
            double fineAggregate02SpecificGravity = Double.parseDouble(microstructureForm.getFine_aggregate02_sg());
            /* Convert to cubic millimeters */
            fineAggregate02SpecificGravity /= 1000.0;

            // Convert to cubic millimeters. Verify that's correct
            coarseAggregate01VolFrac *= 1000;
            fineAggregate01VolFrac *= 1000;
            coarseAggregate02VolFrac *= 1000;
            fineAggregate02VolFrac *= 1000;

            binderVolFrac *= 1000;
            waterVolFrac *= 1000;
            
            double volcondensed = coarseAggregate01VolFrac + coarseAggregate02VolFrac + fineAggregate01VolFrac + fineAggregate02VolFrac + binderVolFrac + waterVolFrac;
            airVolumeFraction =  volcondensed * (airVolumeFraction/(1.0 - airVolumeFraction));
            
            double totalVolume = volcondensed + airVolumeFraction;
            
            /***
             * = Now scale all volumes by totalVolume,
             * = to get the volume fraction for each component,
             * = then multiply by the number of voxels in the system
             * = to determine the number of voxels that should be
             * = assigned to each component
             ***/
            
            coarseAggregate01VolFrac /= totalVolume;
            fineAggregate01VolFrac /= totalVolume;
            coarseAggregate02VolFrac /= totalVolume;
            fineAggregate02VolFrac /= totalVolume;

            binderVolFrac /= totalVolume;
            waterVolFrac /= totalVolume;
            airVolumeFraction /= totalVolume;
            
            this.setCoarse_aggregate01_vol_fraction(coarseAggregate01VolFrac);
            this.setFine_aggregate01_vol_fraction(fineAggregate01VolFrac);
            this.setCoarse_aggregate02_vol_fraction(coarseAggregate02VolFrac);
            this.setFine_aggregate02_vol_fraction(fineAggregate02VolFrac);

            
            double concrete_resolution = Double.valueOf(microstructureForm.getConcrete_resolution());
            setConcrete_resolution(concrete_resolution);
            
            // dimensions are given in millimeters, so we add to divide them by the resolution
            setConcrete_xdim((int)(Double.valueOf(microstructureForm.getConcrete_x_dim())/concrete_resolution));
            setConcrete_ydim((int)(Double.valueOf(microstructureForm.getConcrete_y_dim())/concrete_resolution));
            setConcrete_zdim((int)(Double.valueOf(microstructureForm.getConcrete_z_dim())/concrete_resolution));
            
//            total_available_pixels = (long)((long)this.getConcrete_xdim() * (long)this.getConcrete_ydim() * (long)this.getConcrete_zdim());
            long total_available_pixels = (long)((long)this.getConcrete_xdim() * (long)this.getConcrete_ydim() * (long)this.getConcrete_zdim());
            
            /**
             * Coarse aggregate
             **/
            
            if (microstructureForm.isAdd_coarse_aggregate01() && coarseAggregate01VolFrac > 0) {
                // Parse diameters and mass fractions
                Aggregate coarseAggregate01 = Aggregate.load(microstructureForm.getCoarse_aggregate01_display_name());
                coarse_aggregate01_name = coarseAggregate01.getName();

                String[][] coarse01Grading = microstructureForm.getCoarse01Grading();
                String gradingName01 = Constants.COARSE_AGGREGATE_GRADING_NAME_01;
                String gradingPath01 = userDir.getOperationDir(operationName);
                if (!gradingPath01.endsWith(File.separator))
                    gradingPath01 = gradingPath01 + File.separator;
                String grading01 = microstructureForm.getCoarse_aggregate01_grading();
                
                ServerFile.writeTextFile(gradingPath01,gradingName01,grading01);
                
                gradingPath01 = gradingPath01 + gradingName01;
                
                this.setCoarse_aggregate01_grading_path(gradingPath01);
                
                int coarse01SieveNumber = coarse01Grading[1].length;
                coarse01_sieves = new Sieve[coarse01SieveNumber];
                present_coarse01_sieves_number = 0;
                
                int i;
                
                double massFrac01;
                for (i = 0; i < coarse01SieveNumber; i++) {
                    coarse01_sieves[i] = new Sieve();
                    coarse01_sieves[i].setMinDiameter(Double.parseDouble(coarse01Grading[1][i]));
                    massFrac01 = Double.parseDouble(coarse01Grading[2][i]);
                    coarse01_sieves[i].setMassFraction(massFrac01);
                    if (massFrac01 > 0)
                        present_coarse01_sieves_number++;
                }
                
                coarse_aggregate01_max_diameter = Double.parseDouble(microstructureForm.getCoarse_aggregate01_grading_max_diam());
                
                if (coarse_aggregate01_max_diameter < Constants.EPSILON)
                    coarse_aggregate01_max_diameter = 1.10 * coarse01_sieves[0].getMinDiameter();
                
                /***
                 * = All mass fractions must be converted to volume fractions if
                 * = visualizing the aggregate packing
                 ***/
                if (microstructureForm.isUse_visualize_concrete()) {

                    double volFrac01;
                    double totalVolume01 = 0.0;
                    for (i = 0; i < coarse01SieveNumber; i++) {
                        volFrac01 = coarse01_sieves[i].getMassFraction() / coarseAggregate01SpecificGravity;
                        coarse01_sieves[i].setVolFraction(volFrac01);
                        totalVolume01 += volFrac01;
                    }
                
                    /***
                     * = To get actual volume fraction, we need to divide by
                     * = total volume in all the size bins, but then also need
                     * = to multiply by the global volume fraction
                     ***/
                
                    if (totalVolume01 > 0.0) {
                        for (i = 0; i < coarse01SieveNumber; i++) {
                            volFrac01 = coarse01_sieves[i].getVolFraction() * (coarseAggregate01VolFrac / totalVolume01);
                            coarse01_sieves[i].setVolFraction(volFrac01);
                        }
                    } else {
                        for (i = 0; i < coarse01SieveNumber; i++) {
                            coarse01_sieves[i].setVolFraction(0.0);
                        }
                    }

                    /***
                     * = Now the number of solid voxels to be assigned to each sieve
                     * = can be found by multiplying the volume fractions above by
                     * = the number of voxels in the system
                     *
                     * = Also the effective diameters must be divided by the system
                     * = resolution (in mm/voxel edge)
                     ***/
                
                    double diam01;
                    for (i = 0; i < coarse01SieveNumber; i++) {
                        coarse01_sieves[i].setVoxels((long)(coarse01_sieves[i].getVolFraction() * total_available_pixels + 0.5));
                        diam01 = coarse01_sieves[i].getMinDiameter() / concrete_resolution;
                        coarse01_sieves[i].setMinDiameter(diam01);
                    }
                
                    coarse_aggregate01_max_diameter /= concrete_resolution;

                    /***
                     * = Next need to figure out how many particles of each sieve
                     * = class to request.  To do this, call diam2vol using the volume
                     * = weighted average diameter of each sieve class.  By convention,
                     * = always err on the side of too few particles instead of too many
                     ***/
                
                    double avediam01 = (Math.pow(coarse_aggregate01_max_diameter,3.0) + Math.pow(coarse01_sieves[0].getMinDiameter(),3.0))/2.0;
                    avediam01 = Math.pow(avediam01,(1.0/3.0));
                    long numvox = 0;
                    if (avediam01 > 2.5) {
                        numvox = diam2vol(avediam01);
                        coarse01_sieves[0].setNumber((int)(coarse01_sieves[0].getVoxels() / (double)numvox));
                    } else {
                        coarse01_sieves[0].setNumber(0);
                    }
                
                    int number01;
                    for (i = 1; i < coarse01SieveNumber; i++) {
                        avediam01 = (Math.pow(coarse01_sieves[i-1].getMinDiameter(),3.0) + Math.pow(coarse01_sieves[i].getMinDiameter(),3.0))/2.0;
                        avediam01 = Math.pow(avediam01,(1./3.));
                        if (avediam01 > 2.5) {
                            numvox = diam2vol(avediam01);
                            number01 = (int)(coarse01_sieves[i].getVoxels() / numvox);
                            coarse01_sieves[i].setNumber(number01);
                        } else {
                            coarse01_sieves[i].setNumber(0);
                        }
                    }
                }
            }

            if (microstructureForm.isAdd_coarse_aggregate02() && coarseAggregate02VolFrac > 0) {
                // Parse diameters and mass fractions
                Aggregate coarseAggregate02 = Aggregate.load(microstructureForm.getCoarse_aggregate02_display_name());
                coarse_aggregate02_name = coarseAggregate02.getName();

                String[][] coarse02Grading = microstructureForm.getCoarse02Grading();
                String gradingName02 = Constants.COARSE_AGGREGATE_GRADING_NAME_02;
                String gradingPath02 = userDir.getOperationDir(operationName);
                if (!gradingPath02.endsWith(File.separator))
                    gradingPath02 = gradingPath02 + File.separator;
                String grading02 = microstructureForm.getCoarse_aggregate02_grading();

                ServerFile.writeTextFile(gradingPath02,gradingName02,grading02);

                gradingPath02 = gradingPath02 + gradingName02;

                this.setCoarse_aggregate02_grading_path(gradingPath02);

                int coarse02SieveNumber = coarse02Grading[1].length;
                coarse02_sieves = new Sieve[coarse02SieveNumber];
                present_coarse02_sieves_number = 0;

                int i;

                double massFrac02;
                for (i = 0; i < coarse02SieveNumber; i++) {
                    coarse02_sieves[i] = new Sieve();
                    coarse02_sieves[i].setMinDiameter(Double.parseDouble(coarse02Grading[1][i]));
                    massFrac02 = Double.parseDouble(coarse02Grading[2][i]);
                    coarse02_sieves[i].setMassFraction(massFrac02);
                    if (massFrac02 > 0)
                        present_coarse02_sieves_number++;
                }

                coarse_aggregate02_max_diameter = Double.parseDouble(microstructureForm.getCoarse_aggregate02_grading_max_diam());

                if (coarse_aggregate02_max_diameter < Constants.EPSILON)
                    coarse_aggregate02_max_diameter = 1.10 * coarse02_sieves[0].getMinDiameter();

                /***
                 * = All mass fractions must be converted to volume fractions if
                 * = visualizing the aggregate packing
                 ***/

                if (microstructureForm.isUse_visualize_concrete()) {
                    double volFrac02;
                    double totalVolume02 = 0.0;
                    for (i = 0; i < coarse02SieveNumber; i++) {
                        volFrac02 = coarse02_sieves[i].getMassFraction() / coarseAggregate02SpecificGravity;
                        coarse02_sieves[i].setVolFraction(volFrac02);
                        totalVolume02 += volFrac02;
                    }

                    /***
                     * = To get actual volume fraction, we need to divide by
                     * = total volume in all the size bins, but then also need
                     * = to multiply by the global volume fraction
                     ***/

                    if (totalVolume02 > 0.0) {
                        for (i = 0; i < coarse02SieveNumber; i++) {
                            volFrac02 = coarse02_sieves[i].getVolFraction() * (coarseAggregate02VolFrac / totalVolume02);
                            coarse02_sieves[i].setVolFraction(volFrac02);
                        }
                    } else {
                        for (i = 0; i < coarse02SieveNumber; i++) {
                            coarse02_sieves[i].setVolFraction(0.0);
                        }
                    }

                    /***
                     * = Now the number of solid voxels to be assigned to each sieve
                     * = can be found by multiplying the volume fractions above by
                     * = the number of voxels in the system
                     *
                     * = Also the effective diameters must be divided by the system
                     * = resolution (in mm/voxel edge)
                     ***/

                    double diam02;
                    for (i = 0; i < coarse02SieveNumber; i++) {
                        coarse02_sieves[i].setVoxels((long)(coarse02_sieves[i].getVolFraction() * total_available_pixels + 0.5));
                        diam02 = coarse02_sieves[i].getMinDiameter() / concrete_resolution;
                        coarse02_sieves[i].setMinDiameter(diam02);
                    }

                    coarse_aggregate02_max_diameter /= concrete_resolution;

                    /***
                     * = Next need to figure out how many particles of each sieve
                     * = class to request.  To do this, call diam2vol using the volume
                     * = weighted average diameter of each sieve class.  By convention,
                     * = always err on the side of too few particles instead of too many
                     ***/

                    double avediam02 = (Math.pow(coarse_aggregate02_max_diameter,3.0) + Math.pow(coarse02_sieves[0].getMinDiameter(),3.0))/2.0;
                    avediam02 = Math.pow(avediam02,(1.0/3.0));
                    long numvox = 0;
                    if (avediam02 > 2.5) {
                        numvox = diam2vol(avediam02);
                        coarse02_sieves[0].setNumber((int)(coarse02_sieves[0].getVoxels() / (double)numvox));
                    } else {
                        coarse02_sieves[0].setNumber(0);
                    }

                    int number02;
                    for (i = 1; i < coarse02SieveNumber; i++) {
                        avediam02 = (Math.pow(coarse02_sieves[i-1].getMinDiameter(),3.0) + Math.pow(coarse02_sieves[i].getMinDiameter(),3.0))/2.0;
                        avediam02 = Math.pow(avediam02,(1./3.));
                        if (avediam02 > 2.5) {
                            numvox = diam2vol(avediam02);
                            number02 = (int)(coarse02_sieves[i].getVoxels() / numvox);
                            coarse02_sieves[i].setNumber(number02);
                        } else {
                            coarse02_sieves[i].setNumber(0);
                        }
                    }
                }
            }

            /**
             * Fine aggregate
             **/
            
            if (microstructureForm.isAdd_fine_aggregate01() && fineAggregate01VolFrac > 0) {
                Aggregate fineAggregate01 = Aggregate.load(microstructureForm.getFine_aggregate01_display_name());
                fine_aggregate01_name = fineAggregate01.getName();
                // Parse diameters and mass fractions
                String[][] fine01Grading = microstructureForm.getFine01Grading();
                String gradingName01 = Constants.FINE_AGGREGATE_GRADING_NAME_01;
                String gradingPath01 = userDir.getOperationDir(operationName);
                if (!gradingPath01.endsWith(File.separator))
                    gradingPath01 = gradingPath01 + File.separator;
                String grading01 = microstructureForm.getFine_aggregate01_grading();
                
                ServerFile.writeTextFile(gradingPath01,gradingName01,grading01);
                
                gradingPath01 = gradingPath01 + gradingName01;
                
                this.setFine_aggregate01_grading_path(gradingPath01);
                
                int fine01SieveNumber = fine01Grading[1].length;
                fine01_sieves = new Sieve[fine01SieveNumber];
                present_fine01_sieves_number = 0;
                
                int i;
                
                double massFrac01;
                for (i = 0; i < fine01SieveNumber; i++) {
                    fine01_sieves[i] = new Sieve();
                    fine01_sieves[i].setMinDiameter(Double.parseDouble(fine01Grading[1][i]));
                    massFrac01 = Double.parseDouble(fine01Grading[2][i]);
                    fine01_sieves[i].setMassFraction(massFrac01);
                    if (massFrac01 > 0)
                        present_fine01_sieves_number++;
                }
                
                fine_aggregate01_max_diameter = Double.parseDouble(microstructureForm.getFine_aggregate01_grading_max_diam());
                
                if (fine_aggregate01_max_diameter < Constants.EPSILON)
                    fine_aggregate01_max_diameter = 1.10 * fine01_sieves[0].getMinDiameter();
                
                /***
                 * = All mass fractions must be converted to volume fractions if
                 * = visualizing the aggregate packing
                 ***/
                
                if (microstructureForm.isUse_visualize_concrete()) {

                    double totalVolume01 = 0.0;
                    for (i = 0; i < fine01SieveNumber; i++) {
                        fine01_sieves[i].setVolFraction(fine01_sieves[i].getMassFraction() / fineAggregate01SpecificGravity);
                        totalVolume01 += fine01_sieves[i].getVolFraction();
                    }
                
                    /***
                     * = To get actual volume fraction, we need to divide by
                     * = total volume in all the size bins, but then also need
                     * = to multiply by the global volume fraction
                     ***/
                
                    double volFrac01;
                    if (totalVolume01 > 0.0) {
                        for (i = 0; i < fine01SieveNumber; i++) {
                            volFrac01 = fine01_sieves[i].getVolFraction() * (fineAggregate01VolFrac / totalVolume01);
                            fine01_sieves[i].setVolFraction(volFrac01);
                        }
                    } else {
                        for (i = 0; i < fine01SieveNumber; i++) {
                            fine01_sieves[i].setVolFraction(0.0);
                        }
                    }

                    /***
                     * = Now the number of solid voxels to be assigned to each sieve
                     * = can be found by multiplying the volume fractions above by
                     * = the number of voxels in the system
                     *
                     * = Also the effective diameters must be divided by the system
                     * = resolution (in mm/voxel edge)
                     ***/
                
                    double diam01;
                    for (i = 0; i < fine01SieveNumber; i++) {
                        fine01_sieves[i].setVoxels((long)(fine01_sieves[i].getVolFraction() * total_available_pixels + 0.5));
                        diam01 = fine01_sieves[i].getMinDiameter() / concrete_resolution;
                        fine01_sieves[i].setMinDiameter(diam01);
                    }
                
                    fine_aggregate01_max_diameter /= concrete_resolution;

                    /***
                     * = Next need to figure out how many particles of each sieve
                     * = class to request.  To do this, call diam2vol using the volume
                     * = weighted average diameter of each sieve class.  By convention,
                     * = always err on the side of too few particles instead of too many
                     ***/
                
                    double avediam01 = (Math.pow(fine_aggregate01_max_diameter,3.0) + Math.pow(fine01_sieves[0].getMinDiameter(),3.0))/2.0;
                    long numvox01 = 0;
                    avediam01 = Math.pow(avediam01,(1.0/3.0));
                    if (avediam01 > 2.5) {
                        numvox01 = diam2vol(avediam01);
                        fine01_sieves[0].setNumber((int)(fine01_sieves[0].getVoxels() / (double)numvox01));
                    } else {
                        fine01_sieves[0].setNumber(0);
                    }
                
                    int number01;
                    for (i = 1; i < fine01SieveNumber; i++) {
                        avediam01 = (Math.pow(fine01_sieves[i-1].getMinDiameter(),3.0) + Math.pow(fine01_sieves[i].getMinDiameter(),3.0))/2.0;
                        avediam01 = Math.pow(avediam01,(1./3.));
                        if (avediam01 > 2.5) {
                            numvox01 = diam2vol(avediam01);
                            number01 = (int)(fine01_sieves[i].getVoxels() / numvox01);
                        } else {
                            number01 = 0;
                        }
                        fine01_sieves[i].setNumber(number01);
                    }
                }
            }

            if (microstructureForm.isAdd_fine_aggregate02() && fineAggregate02VolFrac > 0) {
                Aggregate fineAggregate02 = Aggregate.load(microstructureForm.getFine_aggregate02_display_name());
                fine_aggregate02_name = fineAggregate02.getName();
                // Parse diameters and mass fractions
                String[][] fine02Grading = microstructureForm.getFine02Grading();
                String gradingName02 = Constants.FINE_AGGREGATE_GRADING_NAME_02;
                String gradingPath02 = userDir.getOperationDir(operationName);
                if (!gradingPath02.endsWith(File.separator))
                    gradingPath02 = gradingPath02 + File.separator;
                String grading02 = microstructureForm.getFine_aggregate02_grading();

                ServerFile.writeTextFile(gradingPath02,gradingName02,grading02);

                gradingPath02 = gradingPath02 + gradingName02;

                this.setFine_aggregate02_grading_path(gradingPath02);

                int fine02SieveNumber = fine02Grading[1].length;
                fine02_sieves = new Sieve[fine02SieveNumber];
                present_fine02_sieves_number = 0;

                int i;

                double massFrac02;
                for (i = 0; i < fine02SieveNumber; i++) {
                    fine02_sieves[i] = new Sieve();
                    fine02_sieves[i].setMinDiameter(Double.parseDouble(fine02Grading[1][i]));
                    massFrac02 = Double.parseDouble(fine02Grading[2][i]);
                    fine02_sieves[i].setMassFraction(massFrac02);
                    if (massFrac02 > 0)
                        present_fine02_sieves_number++;
                }

                fine_aggregate02_max_diameter = Double.parseDouble(microstructureForm.getFine_aggregate02_grading_max_diam());

                if (fine_aggregate02_max_diameter < Constants.EPSILON)
                    fine_aggregate02_max_diameter = 1.10 * fine02_sieves[0].getMinDiameter();

                /***
                 * = All mass fractions must be converted to volume fractions if
                 * = visualizing the aggregate packing
                 ***/

                if (microstructureForm.isUse_visualize_concrete()) {

                    double totalVolume02 = 0.0;
                    for (i = 0; i < fine02SieveNumber; i++) {
                        fine02_sieves[i].setVolFraction(fine02_sieves[i].getMassFraction() / fineAggregate02SpecificGravity);
                        totalVolume02 += fine02_sieves[i].getVolFraction();
                    }

                    /***
                     * = To get actual volume fraction, we need to divide by
                     * = total volume in all the size bins, but then also need
                     * = to multiply by the global volume fraction
                     ***/

                    double volFrac02;
                    if (totalVolume02 > 0.0) {
                        for (i = 0; i < fine02SieveNumber; i++) {
                            volFrac02 = fine02_sieves[i].getVolFraction() * (fineAggregate02VolFrac / totalVolume02);
                            fine02_sieves[i].setVolFraction(volFrac02);
                        }
                    } else {
                        for (i = 0; i < fine02SieveNumber; i++) {
                            fine02_sieves[i].setVolFraction(0.0);
                        }
                    }

                    /***
                     * = Now the number of solid voxels to be assigned to each sieve
                     * = can be found by multiplying the volume fractions above by
                     * = the number of voxels in the system
                     *
                     * = Also the effective diameters must be divided by the system
                     * = resolution (in mm/voxel edge)
                     ***/

                    double diam02;
                    for (i = 0; i < fine02SieveNumber; i++) {
                        fine02_sieves[i].setVoxels((long)(fine02_sieves[i].getVolFraction() * total_available_pixels + 0.5));
                        diam02 = fine02_sieves[i].getMinDiameter() / concrete_resolution;
                        fine02_sieves[i].setMinDiameter(diam02);
                    }

                    fine_aggregate02_max_diameter /= concrete_resolution;


                    /***
                     * = Next need to figure out how many particles of each sieve
                     * = class to request.  To do this, call diam2vol using the volume
                     * = weighted average diameter of each sieve class.  By convention,
                     * = always err on the side of too few particles instead of too many
                     ***/

                    double avediam02 = (Math.pow(fine_aggregate02_max_diameter,3.0) + Math.pow(fine02_sieves[0].getMinDiameter(),3.0))/2.0;
                    avediam02 = Math.pow(avediam02,(1.0/3.0));
                    long numvox02 = 0;
                    if (avediam02 > 2.5) {
                        numvox02 = diam2vol(avediam02);
                        fine02_sieves[0].setNumber((int)(fine02_sieves[0].getVoxels() / (double)numvox02));
                    } else {
                        fine02_sieves[0].setNumber(0);
                    }

                    int number02;
                    for (i = 1; i < fine02SieveNumber; i++) {
                        avediam02 = (Math.pow(fine02_sieves[i-1].getMinDiameter(),3.0) + Math.pow(fine02_sieves[i].getMinDiameter(),3.0))/2.0;
                        avediam02 = Math.pow(avediam02,(1./3.));
                        if (avediam02 > 2.5) {
                            numvox02 = diam2vol(avediam02);
                            number02 = (int)(fine02_sieves[i].getVoxels() / numvox02);
                            fine02_sieves[i].setNumber(number02);
                        } else {
                            fine02_sieves[i].setNumber(0);
                        }
                    }
                }
            }
        }
        
        
        return true;
    }
    
    private void clear_sample_info() {
        sample_file.clear();
        dissolution_bias.clear();
    }
    
    private void add_to_sample_info(String name, PSDSample sample) {
        sample_file.put(name, sample);
        double pixbias = sample.getOne_pixel_bias();
        dissolution_bias.put(name, pixbias);
    }

    private PSDSample create_sample3(PSD psd, String mixName, long total_pixels) throws PSDTooSmallException {
        PSDSample sample = new PSDSample();
        double resolution = this.getBinder_resolution();
        // long max_diameter = this.getBinder_xdim() - this.getAggregate_thickness();
        long maxDiameter = this.getBinder_xdim();
        if (this.getBinder_ydim() < maxDiameter) {
            maxDiameter = this.getBinder_ydim();
        }
        if (this.getBinder_zdim() < maxDiameter) {
            maxDiameter = this.getBinder_zdim();
        }
        maxDiameter = (long)(Constants.SIZE_SAFETY_COEFFICIENT * maxDiameter);
        sample.set_parameters(psd, resolution, maxDiameter, total_pixels);
        
        return sample;
    }
    
    private PSDSample create_sample3(PSD psd, long total_pixels) throws PSDTooSmallException {
        return create_sample3(psd, "temp-name", total_pixels);
    }    
    
    /*
    private static String get_psd_from_sample(String samplename, String userName) {
        Operation sample_op = OperationDatabase.getOperationForUser(samplename, userName);
        String state = new String(sample_op.getState());
        String[] vars = state.split("\n");
        String psdname = vars[4].substring(vars[4].indexOf('=')+1);
        
        return psdname.trim();
    }
     **/
    
    /**
     * Private helper function to convert a solid mass fraction to a
     * 'water-cement ratio' for generating samples
     */
    private double water_solid_ratio_from_massfrac(double massfrac) {
        return (1.0-massfrac)/massfrac;
    }
    
    /** Creates a new instance of InitialMicrostructure */
    public InitialMicrostructure(String user_name) {
        setUser_name(user_name);
        
        sample_file = new HashMap();
        dissolution_bias = new HashMap();
    }
    
    
    private void reset_input() {
        genpartrun_input = new StringBuffer();
    }
    
    class Particle {
        public double volumeFraction;
        public double radius;
        public int phase;
        
        public Particle() {
            
        }
        
        Particle(double volumeFraction, double radius, int phase) {
            this.volumeFraction = volumeFraction;
            this.radius = radius;
            this.phase = phase;
        }
        
        public double getVolumeFraction() {
            return this.volumeFraction;
        }
        
        public void setVolumeFraction(double volumeFraction) {
            this.volumeFraction = volumeFraction;
        }
        
        public double getRadius() {
            return this.radius;
        }
        
        public void setRadius(double radius) {
            this.radius = radius;
        }
        
        public int getPhase() {
            return this.phase;
        }
        
        public void setPhase(int phase) {
            this.phase = phase;
        }
    }
    
    /**
     * Given a list of particles, return a sorted list of them.
     */
    private List sortParticles(List particle) {
        /**
         * First, construct an array of the radii only
         */
        ArrayList sorted = new ArrayList();
        double[] radius = new double[particle.size()];
        for (int i=0; i<radius.length; i++) {
            Particle part = (Particle)particle.get(i);
            radius[i] = part.radius;
        }
        /**
         * Call the built-in array sorting algorithm, which
         * returns an array sorted from smallest to largest
         */
        Arrays.sort(radius);
        
        /**
         * For each radius in the sorted array, find its
         * corresponding particle entry in the list and
         * build the sorted list.  Sorted list has largest
         * radius in first element, smallest in last element.
         */
        for (int i=radius.length-1; i >= 0; i--) {
            for (int j=0; j<particle.size(); j++) {
                Particle part = (Particle)particle.get(j);
                if (part.radius == radius[i]) {
                    sorted.add(part);
                    particle.remove(j);
                }
            }
        }
        return sorted;
    }

    /**
     * Append a line of text to the genpartrun input.
     */
    private void writeLineToGenpartrunInput(String line) {
        genpartrun_input.append(line).append("\n");
    }
    private void writeLineToGenpartrunInput(double dblval) {
        genpartrun_input.append(dblval).append("\n");
    }
    private void writeLineToGenpartrunInput(int intval) {
        genpartrun_input.append(intval).append("\n");
    }
    private void writeLineToGenpartrunInput(long longval) {
        genpartrun_input.append(longval).append("\n");
    }
    // write assumes that 'lines' contains all
    // necessary newline characters
    private void writeToGenpartrunInput(String lines) {
        genpartrun_input.append(lines);
    }
    

    public void create_genpartrun_input3() {
        final int EXIT = 1;
        final int SPECIFY_SYSTEM_SIZE = EXIT + 1; // 2
        final int ADD_PARTICLES = SPECIFY_SYSTEM_SIZE + 1; // 3
        final int FLOCCULATE_SYSTEM = ADD_PARTICLES + 1; // 4
        final int MEASURE_GLOBAL_PHASE_FRACTIONS = FLOCCULATE_SYSTEM + 1; // 5
        final int ADD_AGGREGATE = MEASURE_GLOBAL_PHASE_FRACTIONS + 1; // 6
        final int MEASURE_SINGLE_PHASE_CONNECTIVITY = ADD_AGGREGATE + 1; // 7
        final int MEASURE_PHASE_FRACTIONS_VS_DISTANCE_FROM_AGGREGATE_SURFACE = MEASURE_SINGLE_PHASE_CONNECTIVITY + 1;  // 8
        final int DISTRIBUTE_CLINKER_PHASES = MEASURE_PHASE_FRACTIONS_VS_DISTANCE_FROM_AGGREGATE_SURFACE + 1; // 9
        final int OUTPUT = DISTRIBUTE_CLINKER_PHASES + 1; // 10
        final int ADD_ONE_PIXEL_PARTICLES = OUTPUT + 1; // 11
        final int DISTRIBUTE_FLY_ASH_PHASES = ADD_ONE_PIXEL_PARTICLES + 1;  //12
        
        /**
         * Calculate and prepare input values
         */
        double total_gypsum_probability = getAnhydrite_volume_fraction() +
                getDihydrate_volume_fraction() +
                getHemihydrate_volume_fraction();
        
        /**
         * 0. Reset the input text.
         */
        reset_input();
        
        /**
         * 1. random number generator seed (no menu number needed, always first
         *    item in the input).
         */
        writeLineToGenpartrunInput(getRng_seed());
        
        /**
         * 2. System size:
         */
        writeLineToGenpartrunInput(SPECIFY_SYSTEM_SIZE); // menu option 2
        writeLineToGenpartrunInput(getBinder_xdim());        // x dimension
        writeLineToGenpartrunInput(getBinder_ydim());        // y dimension
        writeLineToGenpartrunInput(getBinder_zdim());        // z dimension
        writeLineToGenpartrunInput(getBinder_resolution());  // resolution in microns per pixel
        
        /**
         * 6. Aggregate thickness (this must be done after number two)
         */
        UserDirectory userDir = new UserDirectory(this.getUser_name());
        String psdpath = userDir.getOperationFilePath(this.getMixName(), Constants.CEMENT_PSD_FILE);
        if (this.getFine_aggregate01_vol_fraction() > 0 || this.getCoarse_aggregate01_vol_fraction() > 0 || this.getFine_aggregate02_vol_fraction() > 0 || this.getCoarse_aggregate02_vol_fraction() > 0) {
            writeLineToGenpartrunInput(ADD_AGGREGATE);
        }
        
        /**
         * 3. Add particles (cement, gypsum, etc.) to microstructure
         */
        writeLineToGenpartrunInput(ADD_PARTICLES);                        // menu option 3
        writeLineToGenpartrunInput(isReal_shapes() ? 1 : 0);  // Spheres (0) or real shapes (1)
        if (isReal_shapes()) {
            writeLineToGenpartrunInput(Vcctl.getParticleShapeSetDirectory());
            writeLineToGenpartrunInput(shape_set);
        }
        
        writeLineToGenpartrunInput(this.getBinderVolumeFraction()); // NON normalized volume fraction - total volume includes vol fraction of aggregate
        writeLineToGenpartrunInput(this.getWaterVolumeFraction()); // same remark
        
        writeLineToGenpartrunInput(sample_file.size()); // 
        
        // Iterate over all entries in map of sample files
        double resolution = this.getBinder_resolution();
        boolean flyashPresent = false;
        for (Iterator it=sample_file.entrySet().iterator(); it.hasNext(); ) {
            Map.Entry entry = (Map.Entry)it.next();
            String phase = (String)entry.getKey();
            PSDSample sample = (PSDSample)entry.getValue();
            int phaseNumber = Phase.number(phase);
            
            if (phaseNumber == Phase.number("fly_ash"))
                flyashPresent = true;
            
            writeLineToGenpartrunInput(phaseNumber); // phase ID
            
            writeLineToGenpartrunInput(((Double)this.phasesVolumeFractions.get(phase)).doubleValue()); // phase volume fraction
            
            
            double massFractions[] = sample.massfrac;
            double diameters[] = sample.diameter;
            int counter = 0;
            
            // Determine how many diameters have non-zero mass fractions
            // and then write that number to the input file so that genmic can
            // know how many entries to read.  It would be cleaner to change
            // the size of the diameters array and the massFractions array so that
            // only non-zero mass fractions are included in them.
            
            for (int i=0; i<diameters.length; i++) {
                if (massFractions[i] > 0.0) {
                    counter++;
                }
            }
            
            writeLineToGenpartrunInput(counter); // number of different diameters
            
            for (int i=0; i<diameters.length; i++) {
                if (massFractions[i] > 0.0) {
                    writeLineToGenpartrunInput(diameters[i]); // diameter
                    writeLineToGenpartrunInput(sample.massfrac[i]);
                }
            }
        }
        
        writeLineToGenpartrunInput(getDispersion_distance()); // Dispersion factor [0-2]
        
        if (total_gypsum_probability > 0.0) {
            writeLineToGenpartrunInput(total_gypsum_probability); // Prob. of gypsum particles (all three types)
            writeLineToGenpartrunInput(getAnhydrite_volume_fraction()/total_gypsum_probability);  // Prob. of anhydrite
            writeLineToGenpartrunInput(getHemihydrate_volume_fraction()/total_gypsum_probability); // Prob. of hemihydrate
        } else {
            writeLineToGenpartrunInput(0.0);
            writeLineToGenpartrunInput(0.0);
            writeLineToGenpartrunInput(0.0);
        }
        
        /**
         * 4. Flocculation (if specified)
         */
        if (getFlocdegree() > 0.0) {
            writeLineToGenpartrunInput(FLOCCULATE_SYSTEM);
            writeLineToGenpartrunInput(getFlocdegree());
        }
        
        /**
         * 5. MEASURE_GLOBAL_PHASE_FRACTIONS global phase fractions (no input)
         */
        
        /**
         * 7. MEASURE_GLOBAL_PHASE_FRACTIONS single phase MEASURE_SINGLE_PHASE_CONNECTIVITY (pores or solids)
         */
        
        /**
         * 8. MEASURE_GLOBAL_PHASE_FRACTIONS phase fractions vs. distance from aggregate surface
         */
        
        String mixName = getMixName();
        String opname = mixName;
        
        /**
         * 9. Distribute clinker phases
         */
        writeLineToGenpartrunInput(DISTRIBUTE_CLINKER_PHASES);
        
        String psdname = getDistribute_clinker_phases_psd();
        psdpath = userDir.getOperationFilePath(opname, psdname);
        
        // UserDirectory ud = UserDirectory.INSTANCE;
        // psdpath = userDir.getOperationFilePath(opname, Constants.CEMENT_PSD_FILE);
        writeLineToGenpartrunInput(psdpath);
        double[] volfrac = getVolfrac();
        double[] safrac = getSafrac();
        for (int i = 0; i < volfrac.length; i++) {
            writeLineToGenpartrunInput(volfrac[i]);
            writeLineToGenpartrunInput(safrac[i]);
        }
        
        /**
         * Distribute fly ash phases, if fly ash is present
         */
        if (flyashPresent) {
            writeLineToGenpartrunInput(DISTRIBUTE_FLY_ASH_PHASES);
            writeToGenpartrunInput(getFlyash_distribution_input());
        }
        
        /*
         * Send e-mail notification
         */
        //writeLineToGenpartrunInput(11);
        //writeLineToGenpartrunInput(getUser_name());
        
        /*
         * 11. Add one-pixel particles
         *
         */
        writeLineToGenpartrunInput(ADD_ONE_PIXEL_PARTICLES);
        
        /**
         * 10. Output current microstructure to file
         */
        writeLineToGenpartrunInput(OUTPUT);
        
        String fileName = mixName;
        String pfileName = mixName;
        if (fileName.indexOf(".img") < 0) {
            fileName += ".img";
        }
        if (pfileName.indexOf(".pimg") < 0) {
            pfileName += ".pimg";
        }
            
        String imgpath = userDir.getOperationFilePath(opname, fileName);
        String pimgpath = userDir.getOperationFilePath(opname, pfileName);
        writeLineToGenpartrunInput(imgpath);
        writeLineToGenpartrunInput(pimgpath);
        
        /*
         * 1. Exit
         */
        writeLineToGenpartrunInput(EXIT);
    }    
        
    
    
    
    
    /**
     * Append a line of text to the genaggpack input.
     */
    private void writeLineToGenaggpackInput(String line) {
        genaggpackInput.append(line).append("\n");
    }
    private void writeLineToGenaggpackInput(double dblval) {
        genaggpackInput.append(dblval).append("\n");
    }
    private void writeLineToGenaggpackInput(int intval) {
        genaggpackInput.append(intval).append("\n");
    }
    private void writeLineToGenaggpackInput(long longval) {
        genaggpackInput.append(longval).append("\n");
    }
    // write assumes that 'lines' contains all
    // necessary newline characters
    private void writeToGenaggpackInput(String lines) {
        genaggpackInput.append(lines);
    }
    
    
    /* Create the input file for genaggpack
     *
     **/
    public void createGenaggpackInput() {
        final int EXIT = 1; // 1
        final int SPECIFY_SYSTEM_SIZE = EXIT + 1; // 2
        final int ADD_COARSE_AGGREGATE_PARTICLES = SPECIFY_SYSTEM_SIZE + 1; // 3
        final int ADD_FINE_AGGREGATE_PARTICLES = ADD_COARSE_AGGREGATE_PARTICLES + 1; // 4
        final int MEASURE_GLOBAL_PHASE_FRACTIONS = ADD_FINE_AGGREGATE_PARTICLES + 1; // 7
        final int MEASURE_SINGLE_PHASE_CONNECTIVITY = MEASURE_GLOBAL_PHASE_FRACTIONS + 1; // 8
        final int OUTPUT = MEASURE_SINGLE_PHASE_CONNECTIVITY + 1; // 9
        final int EMAIL = OUTPUT + 1; // 10
        final int TRANSPARENT_BINDER = 0;  // Change to 1 if you want transparent binder
        
        final int ANALYSE_ITZ = 2;
        
        /**
         * 0. Reset the input text.
         */
        genaggpackInput = new StringBuffer();
        
        /**
         * 1. random number generator seed (no menu number needed, always first
         *    item in the input).
         */
        writeLineToGenaggpackInput(getRng_seed());
        
        /**
         * 2. System size:
         */
        writeLineToGenaggpackInput(SPECIFY_SYSTEM_SIZE); // menu option 2
        writeLineToGenaggpackInput(getConcrete_xdim());        // x dimension
        writeLineToGenaggpackInput(getConcrete_ydim());        // y dimension
        writeLineToGenaggpackInput(getConcrete_zdim());        // z dimension
        
        double resolution = getConcrete_resolution();
        
        writeLineToGenaggpackInput(resolution);  // resolution in microns per pixel
        
        /**
         * 3. Add coarse aggregate
         */
        if (coarse_aggregate01_mass_fraction > Constants.EPSILON || coarse_aggregate02_mass_fraction > Constants.EPSILON) {
            writeLineToGenaggpackInput(ADD_COARSE_AGGREGATE_PARTICLES);
            writeLineToGenaggpackInput("1"); // use real shapes for the moment...
            writeLineToGenaggpackInput(Vcctl.getAggregateDirectory());
            if (coarse_aggregate01_mass_fraction > Constants.EPSILON && coarse_aggregate02_mass_fraction > Constants.EPSILON) {
                writeLineToGenaggpackInput("2");
            } else {
                writeLineToGenaggpackInput("1");
            }

            if (coarse_aggregate01_mass_fraction > Constants.EPSILON) {
                writeLineToGenaggpackInput(coarse_aggregate01_name);
                writeLineToGenaggpackInput(present_coarse01_sieves_number);
            
                int coarseSieveNumber = coarse01_sieves.length;
            
                int i;
                long voxels;
                String line;
                for (i = 0; i < coarseSieveNumber; i++) {
                    voxels = coarse01_sieves[i].getVoxels();
                    if (voxels > 0) {
                        writeLineToGenaggpackInput(voxels);
                        if (i == 0) { // if biggest coarse sieve
                            // line = Double.toString(coarse_sieves[0].getMinDiameter()*resolution/2.0);
                            writeLineToGenaggpackInput(Double.toString(coarse01_sieves[0].getMinDiameter()*resolution/2.0));
                            // line = line+" "+Double.toString(coarse_aggregate_max_diameter*resolution/2.0);
                            // writeLineToGenaggpackInput(line);
                            writeLineToGenaggpackInput(Double.toString(coarse_aggregate01_max_diameter*resolution/2.0));
                        } else {
                            //line = Double.toString(coarse_sieves[i].getMinDiameter()*resolution/2.0);
                            writeLineToGenaggpackInput(Double.toString(coarse01_sieves[i].getMinDiameter()*resolution/2.0));
                            //line = line+" "+Double.toString(coarse_sieves[i-1].getMinDiameter()*resolution/2.0);
                            //writeLineToGenaggpackInput(line);
                            writeLineToGenaggpackInput(Double.toString(coarse01_sieves[i-1].getMinDiameter()*resolution/2.0));
                        }
                    }
                }
                
                if (coarse_aggregate02_mass_fraction > Constants.EPSILON) {
                    writeLineToGenaggpackInput(coarse_aggregate02_name);
                    writeLineToGenaggpackInput(present_coarse02_sieves_number);
            
                    coarseSieveNumber = coarse02_sieves.length;
            
                    for (i = 0; i < coarseSieveNumber; i++) {
                        voxels = coarse02_sieves[i].getVoxels();
                        if (voxels > 0) {
                            writeLineToGenaggpackInput(voxels);
                            if (i == 0) { // if biggest coarse sieve
                                // line = Double.toString(coarse_sieves[0].getMinDiameter()*resolution/2.0);
                                writeLineToGenaggpackInput(Double.toString(coarse02_sieves[0].getMinDiameter()*resolution/2.0));
                                // line = line+" "+Double.toString(coarse_aggregate_max_diameter*resolution/2.0);
                                // writeLineToGenaggpackInput(line);
                                writeLineToGenaggpackInput(Double.toString(coarse_aggregate02_max_diameter*resolution/2.0));
                            } else {
                                //line = Double.toString(coarse_sieves[i].getMinDiameter()*resolution/2.0);
                                writeLineToGenaggpackInput(Double.toString(coarse02_sieves[i].getMinDiameter()*resolution/2.0));
                                //line = line+" "+Double.toString(coarse_sieves[i-1].getMinDiameter()*resolution/2.0);
                                //writeLineToGenaggpackInput(line);
                                writeLineToGenaggpackInput(Double.toString(coarse02_sieves[i-1].getMinDiameter()*resolution/2.0));
                            }
                        }
                    }
                    
                }
            } else {
                writeLineToGenaggpackInput(coarse_aggregate02_name);
                writeLineToGenaggpackInput(present_coarse02_sieves_number);

                int coarseSieveNumber = coarse02_sieves.length;

                int i;
                long voxels;
                String line;
                for (i = 0; i < coarseSieveNumber; i++) {
                    voxels = coarse02_sieves[i].getVoxels();
                    if (voxels > 0) {
                        writeLineToGenaggpackInput(voxels);
                        if (i == 0) { // if biggest coarse sieve
                            // line = Double.toString(coarse_sieves[0].getMinDiameter()*resolution/2.0);
                            writeLineToGenaggpackInput(Double.toString(coarse02_sieves[0].getMinDiameter()*resolution/2.0));
                            // line = line+" "+Double.toString(coarse_aggregate_max_diameter*resolution/2.0);
                            // writeLineToGenaggpackInput(line);
                            writeLineToGenaggpackInput(Double.toString(coarse_aggregate02_max_diameter*resolution/2.0));
                        } else {
                            //line = Double.toString(coarse_sieves[i].getMinDiameter()*resolution/2.0);
                            writeLineToGenaggpackInput(Double.toString(coarse02_sieves[i].getMinDiameter()*resolution/2.0));
                            //line = line+" "+Double.toString(coarse_sieves[i-1].getMinDiameter()*resolution/2.0);
                            //writeLineToGenaggpackInput(line);
                            writeLineToGenaggpackInput(Double.toString(coarse02_sieves[i-1].getMinDiameter()*resolution/2.0));
                        }
                    }
                }

            }
        }

        /**
         * 4. Add fine aggregate
         */
        if (fine_aggregate01_mass_fraction > Constants.EPSILON || fine_aggregate02_mass_fraction > Constants.EPSILON) {
            writeLineToGenaggpackInput(ADD_FINE_AGGREGATE_PARTICLES);
            writeLineToGenaggpackInput("1"); // use real shapes for the moment...
            writeLineToGenaggpackInput(Vcctl.getAggregateDirectory());
            if (fine_aggregate01_mass_fraction > Constants.EPSILON && fine_aggregate02_mass_fraction > Constants.EPSILON) {
                writeLineToGenaggpackInput("2");
            } else {
                writeLineToGenaggpackInput("1");
            }

            if (fine_aggregate01_mass_fraction > Constants.EPSILON) {
                writeLineToGenaggpackInput(fine_aggregate01_name);
                writeLineToGenaggpackInput(present_fine01_sieves_number);

                int fineSieveNumber = fine01_sieves.length;

                int i;
                long voxels;
                String line;
                for (i = 0; i < fineSieveNumber; i++) {
                    voxels = fine01_sieves[i].getVoxels();
                    if (voxels > 0) {
                        writeLineToGenaggpackInput(voxels);
                        if (i == 0) { // if biggest coarse sieve
                            // line = Double.toString(coarse_sieves[0].getMinDiameter()*resolution/2.0);
                            writeLineToGenaggpackInput(Double.toString(fine01_sieves[0].getMinDiameter()*resolution/2.0));
                            // line = line+" "+Double.toString(coarse_aggregate_max_diameter*resolution/2.0);
                            // writeLineToGenaggpackInput(line);
                            writeLineToGenaggpackInput(Double.toString(fine_aggregate01_max_diameter*resolution/2.0));
                        } else {
                            //line = Double.toString(coarse_sieves[i].getMinDiameter()*resolution/2.0);
                            writeLineToGenaggpackInput(Double.toString(fine01_sieves[i].getMinDiameter()*resolution/2.0));
                            //line = line+" "+Double.toString(coarse_sieves[i-1].getMinDiameter()*resolution/2.0);
                            //writeLineToGenaggpackInput(line);
                            writeLineToGenaggpackInput(Double.toString(fine01_sieves[i-1].getMinDiameter()*resolution/2.0));
                        }
                    }
                }

                if (fine_aggregate02_mass_fraction > Constants.EPSILON) {
                    writeLineToGenaggpackInput(fine_aggregate02_name);
                    writeLineToGenaggpackInput(present_fine02_sieves_number);

                    fineSieveNumber = fine02_sieves.length;

                    for (i = 0; i < fineSieveNumber; i++) {
                        voxels = fine02_sieves[i].getVoxels();
                        if (voxels > 0) {
                            writeLineToGenaggpackInput(voxels);
                            if (i == 0) { // if biggest coarse sieve
                                // line = Double.toString(coarse_sieves[0].getMinDiameter()*resolution/2.0);
                                writeLineToGenaggpackInput(Double.toString(fine02_sieves[0].getMinDiameter()*resolution/2.0));
                                // line = line+" "+Double.toString(coarse_aggregate_max_diameter*resolution/2.0);
                                // writeLineToGenaggpackInput(line);
                                writeLineToGenaggpackInput(Double.toString(fine_aggregate02_max_diameter*resolution/2.0));
                            } else {
                                //line = Double.toString(coarse_sieves[i].getMinDiameter()*resolution/2.0);
                                writeLineToGenaggpackInput(Double.toString(fine02_sieves[i].getMinDiameter()*resolution/2.0));
                                //line = line+" "+Double.toString(coarse_sieves[i-1].getMinDiameter()*resolution/2.0);
                                //writeLineToGenaggpackInput(line);
                                writeLineToGenaggpackInput(Double.toString(fine02_sieves[i-1].getMinDiameter()*resolution/2.0));
                            }
                        }
                    }

                }
            } else {
                writeLineToGenaggpackInput(fine_aggregate02_name);
                writeLineToGenaggpackInput(present_fine02_sieves_number);

                int fineSieveNumber = fine02_sieves.length;

                int i;
                long voxels;
                String line;
                for (i = 0; i < fineSieveNumber; i++) {
                    voxels = fine02_sieves[i].getVoxels();
                    if (voxels > 0) {
                        writeLineToGenaggpackInput(voxels);
                        if (i == 0) { // if biggest coarse sieve
                            // line = Double.toString(coarse_sieves[0].getMinDiameter()*resolution/2.0);
                            writeLineToGenaggpackInput(Double.toString(fine02_sieves[0].getMinDiameter()*resolution/2.0));
                            // line = line+" "+Double.toString(coarse_aggregate_max_diameter*resolution/2.0);
                            // writeLineToGenaggpackInput(line);
                            writeLineToGenaggpackInput(Double.toString(fine_aggregate02_max_diameter*resolution/2.0));
                        } else {
                            //line = Double.toString(coarse_sieves[i].getMinDiameter()*resolution/2.0);
                            writeLineToGenaggpackInput(Double.toString(fine02_sieves[i].getMinDiameter()*resolution/2.0));
                            //line = line+" "+Double.toString(coarse_sieves[i-1].getMinDiameter()*resolution/2.0);
                            //writeLineToGenaggpackInput(line);
                            writeLineToGenaggpackInput(Double.toString(fine02_sieves[i-1].getMinDiameter()*resolution/2.0));
                        }
                    }
                }

            }
        }
        
        /**
         * 6. Measure single phase connectivity
         **/
        writeLineToGenaggpackInput(MEASURE_SINGLE_PHASE_CONNECTIVITY);
        
        /**
         * 2. Analyse ITZ
         **/
        writeLineToGenaggpackInput(ANALYSE_ITZ);
        
        /**
         * 7. Create output file
         **/
        writeLineToGenaggpackInput(OUTPUT);
        String fileName = Constants.AGGREGATE_IMAGE_FILE_NAME;
        String foderName = Constants.AGGREGATE_FILES_DIRECTORY_NAME;
        String opName = getMixName() + File.separator + foderName;
        // UserDirectory ud = UserDirectory.INSTANCE;
        UserDirectory userDir = new UserDirectory(this.getUser_name());
        String imgPath = userDir.getOperationFilePath(opName, fileName);
        writeLineToGenaggpackInput(imgPath);
        writeLineToGenaggpackInput(TRANSPARENT_BINDER);
        
        /**
         * 5. Name of the stt file
         **/
        writeLineToGenaggpackInput(MEASURE_GLOBAL_PHASE_FRACTIONS);
        fileName = Constants.AGGREGATE_STATS_FILE_NAME;
        // ud = UserDirectory.INSTANCE;
        String sttPath = userDir.getOperationFilePath(opName, fileName);
        writeLineToGenaggpackInput(sttPath);
        
        /*
         * 8. Exit
         */
        writeLineToGenaggpackInput(EXIT);
        
    }
    
    
    /***************************************************************************
     ***************************************************************************
     **
     ** Property member variables, with their accessor (i.e., get/set) functions
     **
     ***************************************************************************
     **************************************************************************/
    
    /**
     * Holds value of property rng_seed.
     */
    private int rng_seed;
    
    /**
     * Getter for property rng_seed.
     * @return Value of property rng_seed.
     */
    public int getRng_seed() {
        
        return this.rng_seed;
    }
    
    /**
     * Setter for property rng_seed.
     * @param rng_seed New value of property rng_seed.
     */
    public void setRng_seed(int rng_seed) {
        
        this.rng_seed = rng_seed;
    }
    
    /**
     * Holds value of property binder_xdim.
     */
    private int binder_xdim;
    
    /**
     * Getter for property xdim.
     * @return Value of property xdim.
     */
    public int getBinder_xdim() {
        return this.binder_xdim;
    }
    
    /**
     * Setter for property xdim.
     * @param xdim New value of property xdim.
     */
    public void setBinder_xdim(int binder_xdim) {
        this.binder_xdim = binder_xdim;
    }
    
    /**
     * Holds value of property binder_ydim.
     */
    private int binder_ydim;
    
    /**
     * Getter for property ydim.
     * @return Value of property ydim.
     */
    public int getBinder_ydim() {
        return this.binder_ydim;
    }
    
    /**
     * Setter for property ydim.
     * @param ydim New value of property ydim.
     */
    public void setBinder_ydim(int binder_ydim) {
        this.binder_ydim = binder_ydim;
    }
    
    /**
     * Holds value of property binder_zdim.
     */
    private int binder_zdim;
    
    /**
     * Getter for property zdim.
     * @return Value of property zdim.
     */
    public int getBinder_zdim() {
        return this.binder_zdim;
    }
    
    /**
     * Setter for property zdim.
     * @param zdim New value of property zdim.
     */
    public void setBinder_zdim(int binder_zdim) {
        this.binder_zdim = binder_zdim;
    }
    
    /**
     * Holds value of property binder_resolution.
     */
    private double binder_resolution;
    
    /**
     * Getter for property resolution.
     * @return Value of property resolution.
     */
    public double getBinder_resolution() {
        return this.binder_resolution;
    }
    
    /**
     * Setter for property resolution.
     * @param resolution New value of property resolution.
     */
    public void setBinder_resolution(double binder_resolution) {
        this.binder_resolution = binder_resolution;
    }
    
    /**
     * Holds value of property mixName.
     */
    private String mixName;
    
    /**
     * Getter for property mixName.
     * @return Value of property mixName.
     */
    public String getMixName() {
        return this.mixName;
    }
    
    /**
     * Setter for property mixName.
     * @param mixName New value of property mixName.
     */
    public void setMixName(String mixName) {
        this.mixName = mixName;
    }
    
    /**
     * Holds value of property anhydrite_mass_fraction.
     */
    private double anhydrite_mass_fraction;
    
    /**
     * Getter for property anhydrite_mass_fraction.
     * @return Value of property anhydrite_mass_fraction.
     */
    public double getAnhydrite_mass_fraction()  {
        
        return this.anhydrite_mass_fraction;
    }
    
    /**
     * Setter for property anhydrite_mass_fraction.
     * @param anhydrite_mass_fraction New value of property anhydrite_mass_fraction.
     */
    public void setAnhydrite_mass_fraction(double anhydrite_mass_fraction)  {
        
        this.anhydrite_mass_fraction = anhydrite_mass_fraction;
    }
    
    /**
     * Holds value of property anhydrite_volume_fraction.
     */
    private double anhydrite_volume_fraction;
    
    /**
     * Getter for property anhydrite_volume_fraction.
     * @return Value of property anhydrite_volume_fraction.
     */
    public double getAnhydrite_volume_fraction()  {
        
        return this.anhydrite_volume_fraction;
    }
    
    /**
     * Setter for property anhydrite_volume_fraction.
     * @param anhydrite_volume_fraction New value of property anhydrite_volume_fraction.
     */
    public void setAnhydrite_volume_fraction(double anydrate_volume_fraction) {
        
        this.anhydrite_volume_fraction = anhydrite_volume_fraction;
    }
    
    /**
     * Holds value of property dihydrate_mass_fraction.
     */
    private double dihydrate_mass_fraction;
    
    /**
     * Getter for property dihydrate_mass_fraction.
     * @return Value of property dihydrate_mass_fraction.
     */
    public double getDihydrate_mass_fraction() {
        
        return this.dihydrate_mass_fraction;
    }
    
    /**
     * Setter for property dihydrate_mass_fraction.
     * @param dihydrate_mass_fraction New value of property dihydrate_mass_fraction.
     */
    public void setDihydrate_mass_fraction(double dihydrate_mass_fraction) {
        
        this.dihydrate_mass_fraction = dihydrate_mass_fraction;
    }
    
    /**
     * Holds value of property dihydrate_volume_fraction.
     */
    private double dihydrate_volume_fraction;
    
    /**
     * Getter for property dihydrate_volume_fraction.
     * @return Value of property dihydrate_volume_fraction.
     */
    public double getDihydrate_volume_fraction() {
        
        return this.dihydrate_volume_fraction;
    }
    
    /**
     * Setter for property dihydrate_volume_fraction.
     * @param dihydrate_volume_fraction New value of property dihydrate_volume_fraction.
     */
    public void setDihydrate_volume_fraction(double dihydrate_volume_fraction) {
        
        this.dihydrate_volume_fraction = dihydrate_volume_fraction;
    }
    
    /**
     * Holds value of property hemihydrate_mass_fraction.
     */
    private double hemihydrate_mass_fraction;
    
    /**
     * Getter for property hemihydrate_mass_fraction.
     * @return Value of property hemihydrate_mass_fraction.
     */
    public double getHemihydrate_mass_fraction() {
        
        return this.hemihydrate_mass_fraction;
    }
    
    /**
     * Setter for property hemihydrate_mass_fraction.
     * @param hemihydrate_mass_fraction New value of property hemihydrate_mass_fraction.
     */
    public void setHemihydrate_mass_fraction(double hemihydrate_mass_fraction) {
        
        this.hemihydrate_mass_fraction = hemihydrate_mass_fraction;
    }
    
    /**
     * Holds value of property hemihydrate_volume_fraction.
     */
    private double hemihydrate_volume_fraction;
    
    /**
     * Getter for property hemihydrate_volume_fraction.
     * @return Value of property hemihydrate_volume_fraction.
     */
    public double getHemihydrate_volume_fraction() {
        
        return this.hemihydrate_volume_fraction;
    }
    
    /**
     * Setter for property hemihydrate_volume_fraction.
     * @param hemihydrate_volume_fraction New value of property hemihydrate_volume_fraction.
     */
    public void setHemihydrate_volume_fraction(double hemihydrate_volume_fraction) {
        
        this.hemihydrate_volume_fraction = hemihydrate_volume_fraction;
    }
    
    
    /**
     * Holds value of property water_solid_ratio.
     */
    private double water_solid_ratio;
    
    /**
     * Getter for property water_solid_ratio.
     * @return Value of property water_solid_ratio.
     */
    public double getWater_solid_ratio() {
        
        return this.water_solid_ratio;
    }
    
    /**
     * Setter for property water_solid_ratio.
     * @param water_solid_ratio New value of property water_solid_ratio.
     */
    public void setWater_solid_ratio(double water_solid_ratio) {
        
        this.water_solid_ratio = water_solid_ratio;
    }
    
    /**
     * Holds value of property genpartrun_input.
     */
    private StringBuffer genpartrun_input;
    
    /**
     * Getter for property genpartrun_input.
     * @return Value of property genpartrun_input.
     */
    public String getGenpartrun_input() {
        
        return this.genpartrun_input.toString();
    }
    
    /**
     * Holds value of property genaggpackInput.
     */
    private StringBuffer genaggpackInput;
    
    /**
     * Getter for property genaggpackInput.
     * @return Value of property genaggpackInput.
     */
    public String getGenaggpackInput() {
        
        return this.genaggpackInput.toString();
    }
    
    /**
     * Holds value of property real_shapes.
     */
    private boolean real_shapes;
    
    /**
     * Getter for property real_shapes.
     * @return Value of property real_shapes.
     */
    public boolean isReal_shapes() {
        
        return this.real_shapes;
    }
    
    /**
     * Setter for property real_shapes.
     * @param real_shapes New value of property real_shapes.
     */
    public void setReal_shapes(boolean real_shapes) {
        
        this.real_shapes = real_shapes;
    }
    
    /**
     * Holds value of property shape_set.
     */
    private String shape_set;
    
    /**
     * Getter for property shape_set.
     * @return Value of property shape_set.
     */
    public String getShape_set() {
        
        return this.shape_set;
    }
    
    /**
     * Setter for property shape_set.
     * @param shape_set New value of property shape_set.
     */
    public void setShape_set(String shape_set) {
        
        this.shape_set = shape_set;
    }
    
    /**
     * Holds value of property flocdegree.
     */
    private double flocdegree;
    
    /**
     * Getter for property flocdegree.
     * @return Value of property flocdegree.
     */
    public double getFlocdegree() {
        
        return this.flocdegree;
    }
    
    /**
     * Setter for property flocdegree.
     * @param flocdegree New value of property flocdegree.
     */
    public void setFlocdegree(double flocdegree) {
        
        this.flocdegree = flocdegree;
    }
    
    /**
     * Holds value of property dispersion_distance.
     */
    private int dispersion_distance;
    
    /**
     * Holds value of property user_name.
     */
    private String user_name;
    
    /**
     * Holds value of property cement_psd.
     */
    private String cement_psd;
    
    /**
     * Holds value of property volfrac.
     */
    private double[] volfrac;
    
    /**
     * Holds value of property safrac.
     */
    private double[] safrac;
    
    /**
     * Holds value of property sample_file.
     * PSD Sample files used to generate microstructure in a map,
     * with key=phase
     */
    private Map sample_file;
    
    /**
     * Holds value of property particle_list.
     */
    // private List particle_list;
    
    /**
     * Holds value of property dissolution_bias.
     */
    private Map dissolution_bias;
    
    /**
     * Getter for property dispersion_distance.
     * @return Value of property dispersion_distance.
     */
    
    public int getDispersion_distance() {
        
        return this.dispersion_distance;
    }
    
    /**
     * Setter for property dispersion_distance.
     * @param dispersion_distance New value of property dispersion_distance.
     */
    public void setDispersion_distance(int dispersion_distance) {
        
        this.dispersion_distance = dispersion_distance;
    }
    
    /**
     * Getter for property user_name.
     * @return Value of property user_name.
     */
    public String getUser_name() {
        
        return this.user_name;
    }
    
    /**
     * Setter for property user_name.
     * @param user_name New value of property user_name.
     */
    public void setUser_name(String user_name) {
        
        this.user_name = user_name;
    }
    
    /**
     * Getter for property cement_psd.
     * @return Value of property cement_psd.
     */
    public String getCement_psd() {
        
        return this.cement_psd;
    }
    
    /**
     * Setter for property cement_psd.
     * @param cement_psd New value of property cement_psd.
     */
    public void setCement_psd(String cement_psd) {
        
        this.cement_psd = cement_psd;
    }
    
    /**
     * Getter for property volfrac.
     * @return Value of property volfrac.
     */
    public double[] getVolfrac() {
        
        return this.volfrac;
    }
    
    /**
     * Setter for property volfrac.
     * @param volfrac New value of property volfrac.
     */
    public void setVolfrac(double[] volfrac) {
        
        this.volfrac = volfrac;
    }
    
    /**
     * Getter for property safrac.
     * @return Value of property safrac.
     */
    public double[] getSafrac() {
        
        return this.safrac;
    }
    
    /**
     * Setter for property safrac.
     * @param safrac New value of property safrac.
     */
    public void setSafrac(double[] safrac) {
        
        this.safrac = safrac;
    }
    
    /**
     * Getter for property sample_file.
     * @return Value of property sample_file.
     */
    public Map getSample_file() {
        
        return this.sample_file;
    }
    
    /**
     * Setter for property sample_file.
     * @param sample_file New value of property sample_file.
     */
    public void setSample_file(Map sample_file) {
        
        this.sample_file = sample_file;
    }
    
    public static InitialMicrostructure create_from_state(String name, String userName) throws SQLException, SQLArgumentException {
        Operation op = OperationDatabase.getOperationForUser(name, userName);
        if (op != null) {
            byte[] imxml = op.getState();
            return (InitialMicrostructure)OperationState.restore_from_Xml(imxml);
        } else {
            return null;
        }
    }
    
    // The output string is in same format as input to disrealnew, so
    // it can be appended as is, without parsing
    public String get_bias_info() {
        StringBuffer buf = new StringBuffer();
        double bias = (Double)dissolution_bias.get("c3s");
        // Output bias followed by phase numbers
        for (int i=0; i<6; i++) {
            if (volfrac[i] > 0.0) {
                buf.append(0).append("\n");
                buf.append(bias).append("\n");
                buf.append(i+1).append("\n");
            }
        }
        // Now loop over other entries in dissolution_bias
        Set<String> phases = dissolution_bias.keySet();
        for (String phase:phases) {
            if (!phase.equalsIgnoreCase("c3s")) {
                int num = Phase.number(phase);
                bias = (Double)dissolution_bias.get(phase);
                buf.append(0).append("\n");
                buf.append(bias).append("\n");
                buf.append(num).append("\n");
            }
        }
        
        // No more bias numbers
        buf.append(-1).append("\n");
        // Write out result
        return buf.toString();
    }
    
    /**
     * Getter for property dissolution_bias.
     * @return Value of property dissolution_bias.
     */
    public Map getDissolution_bias() {
        
        return this.dissolution_bias;
    }
    
    /**
     * Setter for property dissolution_bias.
     * @param dissolution_bias New value of property dissolution_bias.
     */
    public void setDissolution_bias(Map dissolution_bias) {
        
        this.dissolution_bias = dissolution_bias;
    }
    
    /**
     * Holds value of property flyash_distribution_input.
     */
    private String flyash_distribution_input;
    
    /**
     * Getter for property flyash_distribution_input.
     * @return Value of property flyash_distribution_input.
     */
    public String getFlyash_distribution_input() {
        
        return this.flyash_distribution_input;
    }
    
    /**
     * Setter for property flyash_distribution_input.
     * @param flyash_distribution_input New value of property flyash_distribution_input.
     */
    public void setFlyash_distribution_input(String flyash_distribution_input) {
        
        this.flyash_distribution_input = flyash_distribution_input;
    }
    
    /**
     * Holds value of property notes.
     */
    private String notes;
    
    /**
     * Getter for property notes.
     * @return Value of property notes.
     */
    public String getNotes() {
        return this.notes;
    }
    
    /**
     * Setter for property notes.
     * @param notes New value of property notes.
     */
    public void setNotes(String notes) {
        this.notes = notes;
    }
    
    public class Sieve {
        /**
         * Holds value of property minDiameter.
         */
        private double minDiameter;
        
        /**
         * Getter for property minDiameter.
         * @return Value of property minDiameter.
         */
        public double getMinDiameter() {
            return this.minDiameter;
        }
        
        /**
         * Setter for property minDiameter.
         * @param minDiameter New value of property minDiameter.
         */
        public void setMinDiameter(double minDiameter) {
            this.minDiameter = minDiameter;
        }
        
        /**
         * Holds value of property massFraction.
         */
        private double massFraction;
        
        /**
         * Getter for property massFraction.
         * @return Value of property massFraction.
         */
        public double getMassFraction() {
            return this.massFraction;
        }
        
        /**
         * Setter for property massFraction.
         * @param massFraction New value of property massFraction.
         */
        public void setMassFraction(double massFraction) {
            this.massFraction = massFraction;
        }
        
        /**
         * Holds value of property volFraction.
         */
        private double volFraction;
        
        /**
         * Getter for property volFraction.
         * @return Value of property volFraction.
         */
        public double getVolFraction() {
            return this.volFraction;
        }
        
        /**
         * Setter for property volFraction.
         * @param volFraction New value of property volFraction.
         */
        public void setVolFraction(double volFraction) {
            this.volFraction = volFraction;
        }
        
        /**
         * Holds value of property voxels.
         */
        private long voxels;
        
        /**
         * Getter for property voxels.
         * @return Value of property voxels.
         */
        public long getVoxels() {
            return this.voxels;
        }
        
        /**
         * Setter for property voxels.
         * @param voxels New value of property voxels.
         */
        public void setVoxels(long voxels) {
            this.voxels = voxels;
        }
        
        /**
         * Holds value of property number.
         */
        private int number;
        
        /**
         * Getter for property number.
         * @return Value of property number.
         */
        public int getNumber() {
            return this.number;
        }
        
        /**
         * Setter for property number.
         * @param number New value of property number.
         */
        public void setNumber(int number) {
            this.number = number;
        }
        
    }
    
    /**
     * Holds value of property coarse01_sieves.
     */
    private Sieve[] coarse01_sieves;
    
    /**
     * Getter for property coarse01_Sieves.
     * @return Value of property coarse01_Sieves.
     */
    public Sieve[] getCoarse01_sieves() {
        return this.coarse01_sieves;
    }
    
    /**
     * Setter for property coarse01_Sieves.
     * @param coarse01_Sieves New value of property coarse01_Sieves.
     */
    public void setCoarse01_sieves(Sieve[] coarse01_sieves) {
        this.coarse01_sieves = coarse01_sieves;
    }
    
    /**
     * Holds value of property fine01_sieves.
     */
    private Sieve[] fine01_sieves;
    
    /**
     * Getter for property fine01_sieves.
     * @return Value of property fine01_sieves.
     */
    public Sieve[] getFine01_sieves() {
        return this.fine01_sieves;
    }
    
    /**
     * Setter for property fine01_sieves.
     * @param fine01_sieves New value of property fine01_sieves.
     */
    public void setFine01_sieves(Sieve[] fine01_sieves) {
        this.fine01_sieves = fine01_sieves;
    }

    /**
     * Holds value of property coarse02_sieves.
     */
    private Sieve[] coarse02_sieves;

    /**
     * Getter for property coarse01_Sieves.
     * @return Value of property coarse02_Sieves.
     */
    public Sieve[] getCoarse02_sieves() {
        return this.coarse02_sieves;
    }

    /**
     * Setter for property coarse02_Sieves.
     * @param coarse02_Sieves New value of property coarse02_Sieves.
     */
    public void setCoarse02_sieves(Sieve[] coarse02_sieves) {
        this.coarse02_sieves = coarse02_sieves;
    }

    /**
     * Holds value of property fine02_sieves.
     */
    private Sieve[] fine02_sieves;

    /**
     * Getter for property fine02_sieves.
     * @return Value of property fine02_sieves.
     */
    public Sieve[] getFine02_sieves() {
        return this.fine02_sieves;
    }

    /**
     * Setter for property fine02_sieves.
     * @param fine02_sieves New value of property fine02_sieves.
     */
    public void setFine02_sieves(Sieve[] fine02_sieves) {
        this.fine02_sieves = fine02_sieves;
    }

    /***
     * = diam2vol
     *
     * = Converts sphere diameter to number of pixels
     *
     *  = Arguments: = int diameter of sphere
     *  = Returns: = int number of pixels in sphere
     ***/
    long diam2vol(double diameter) {
        long count=0;
        int i,j,k;
        int idiam,irad;
        double dist,radius,ftmp,offset;
        double xdist,ydist,zdist;

        idiam = (int)(diameter + 0.5);
        if ((idiam%2) == 0) {
            offset = -0.5;
            irad = idiam / 2;
        } else {
            offset = 0.0;
            irad = (idiam - 1) / 2;
        }
        radius = 0.5 * diameter;
        
        for (k = -(irad); k <= (irad); k++) {
            ftmp = (double)(k - offset);
            zdist = ftmp * ftmp;
            for (j = -(irad); j <= (irad); j++) {
                ftmp = (double)(j - offset);
                ydist = ftmp * ftmp;
                for (i = -(irad); i <= (irad); i++) {
                    ftmp = (double)(i - offset);
                    xdist = ftmp * ftmp;
                    dist = Math.sqrt(xdist + ydist + zdist);
                    if ((dist - 0.5) <= ((double)irad)) count++;
                }
            }
        }
        
        return(count);
    }
    
    /**
     * Holds value of property coarse_aggregate01_mass_fraction.
     */
    private double coarse_aggregate01_mass_fraction;
    
    /**
     * Getter for property coarse_aggregate01_mass_fration.
     * @return Value of property coarse_aggregate01_mass_fration.
     */
    public double getCoarse_aggregate01_mass_fraction() {
        return this.coarse_aggregate01_mass_fraction;
    }
    
    /**
     * Setter for property coarse_aggregate01_mass_fration.
     * @param coarse_aggregate01_mass_fration New value of property coarse_aggregate01_mass_fration.
     */
    public void setCoarse_aggregate01_mass_fraction(double coarse_aggregate01_mass_fraction) {
        this.coarse_aggregate01_mass_fraction = coarse_aggregate01_mass_fraction;
    }
    
    /**
     * Holds value of property fine_aggregate01_mass_fraction.
     */
    private double fine_aggregate01_mass_fraction;
    
    /**
     * Getter for property fine_aggregate01_mass_fraction.
     * @return Value of property fine_aggregate01_mass_fraction.
     */
    public double getFine_aggregate01_mass_fraction() {
        return this.fine_aggregate01_mass_fraction;
    }
    
    /**
     * Setter for property fine_aggregate01_mass_fraction.
     * @param fine_aggregate01_mass_fraction New value of property fine_aggregate01_mass_fraction.
     */
    public void setFine_aggregate01_mass_fraction(double fine_aggregate01_mass_fraction) {
        this.fine_aggregate01_mass_fraction = fine_aggregate01_mass_fraction;
    }

     /**
     * Holds value of property coarse_aggregate02_mass_fraction.
     */
    private double coarse_aggregate02_mass_fraction;

    /**
     * Getter for property coarse_aggregate02_mass_fration.
     * @return Value of property coarse_aggregate02_mass_fration.
     */
    public double getCoarse_aggregate02_mass_fraction() {
        return this.coarse_aggregate02_mass_fraction;
    }

    /**
     * Setter for property coarse_aggregate02_mass_fration.
     * @param coarse_aggregate02_mass_fration New value of property coarse_aggregate02_mass_fration.
     */
    public void setCoarse_aggregate02_mass_fraction(double coarse_aggregate02_mass_fraction) {
        this.coarse_aggregate02_mass_fraction = coarse_aggregate02_mass_fraction;
    }

    /**
     * Holds value of property fine_aggregate02_mass_fraction.
     */
    private double fine_aggregate02_mass_fraction;

    /**
     * Getter for property fine_aggregate02_mass_fraction.
     * @return Value of property fine_aggregate02_mass_fraction.
     */
    public double getFine_aggregate02_mass_fraction() {
        return this.fine_aggregate02_mass_fraction;
    }

    /**
     * Setter for property fine_aggregate02_mass_fraction.
     * @param fine_aggregate02_mass_fraction New value of property fine_aggregate02_mass_fraction.
     */
    public void setFine_aggregate02_mass_fraction(double fine_aggregate02_mass_fraction) {
        this.fine_aggregate02_mass_fraction = fine_aggregate02_mass_fraction;
    }

    /**
     * Holds value of property coarse_aggregate01_name.
     */
    private String coarse_aggregate01_name;
    
    /**
     * Getter for property coarse_aggregate01_name.
     * @return Value of property coarse_aggregate01_name.
     */
    public String getCoarse_aggregate01_name() {
        return this.coarse_aggregate01_name;
    }
    
    /**
     * Setter for property coarse_aggregate01_name.
     * @param coarse_aggregate01_name New value of property coarse_aggregate01_name.
     */
    public void setCoarse_aggregate01_name(String coarse_aggregate01_name) {
        this.coarse_aggregate01_name = coarse_aggregate01_name;
    }

    /**
     * Holds value of property coarse_aggregate01_display_name.
     */
    private String coarse_aggregate01_display_name;

    /**
     * Getter for property coarse_aggregate01_display_name.
     * @return Value of property coarse_aggregate01_display_name.
     */
    public String getCoarse_aggregate01_display_name() {
        return this.coarse_aggregate01_display_name;
    }

    /**
     * Setter for property coarse_aggregate01_display_name.
     * @param coarse_aggregate01_display_name New value of property coarse_aggregate01_display_name.
     */
    public void setCoarse_aggregate01_display_name(String coarse_aggregate01_display_name) {
        this.coarse_aggregate01_display_name = coarse_aggregate01_display_name;
    }
    
    /**
     * Holds value of property fine_aggregate01_name.
     */
    private String fine_aggregate01_name;
    
    /**
     * Getter for property fine_aggregate01_name.
     * @return Value of property fine_aggregate01_name.
     */
    public String getFine_aggregate01_name() {
        return this.fine_aggregate01_name;
    }
    
    /**
     * Setter for property fine_aggregate01_name.
     * @param fine_aggregate01_name New value of property fine_aggregate01_name.
     */
    public void setFine_aggregate01_name(String fine_aggregate01_name) {
        this.fine_aggregate01_name = fine_aggregate01_name;
    }

    /**
     * Holds value of property fine_aggregate01_display_name.
     */
    private String fine_aggregate01_display_name;

    /**
     * Getter for property fine_aggregate01_display_name.
     * @return Value of property fine_aggregate01_display_name.
     */
    public String getFine_aggregate01_display_name() {
        return this.fine_aggregate01_display_name;
    }

    /**
     * Setter for property fine_aggregate01_display_name.
     * @param fine_aggregate01_display_name New value of property fine_aggregate01_display_name.
     */
    public void setFine_aggregate01_display_name(String fine_aggregate01_display_name) {
        this.fine_aggregate01_display_name = fine_aggregate01_display_name;
    }

     /**
     * Holds value of property coarse_aggregate02_name.
     */
    private String coarse_aggregate02_name;

    /**
     * Getter for property coarse_aggregate02_name.
     * @return Value of property coarse_aggregate02_name.
     */
    public String getCoarse_aggregate02_name() {
        return this.coarse_aggregate02_name;
    }

    /**
     * Setter for property coarse_aggregate02_name.
     * @param coarse_aggregate02_name New value of property coarse_aggregate02_name.
     */
    public void setCoarse_aggregate02_name(String coarse_aggregate02_name) {
        this.coarse_aggregate02_name = coarse_aggregate02_name;
    }

    /**
     * Holds value of property coarse_aggregate02_display_name.
     */
    private String coarse_aggregate02_display_name;

    /**
     * Getter for property coarse_aggregate02_display_name.
     * @return Value of property coarse_aggregate02_display_name.
     */
    public String getCoarse_aggregate02_display_name() {
        return this.coarse_aggregate02_display_name;
    }

    /**
     * Setter for property coarse_aggregate02_display_name.
     * @param coarse_aggregate02_display_name New value of property coarse_aggregate02_display_name.
     */
    public void setCoarse_aggregate02_display_name(String coarse_aggregate02_display_name) {
        this.coarse_aggregate02_display_name = coarse_aggregate02_display_name;
    }

    /**
     * Holds value of property fine_aggregate02_name.
     */
    private String fine_aggregate02_name;

    /**
     * Getter for property fine_aggregate02_name.
     * @return Value of property fine_aggregate02_name.
     */
    public String getFine_aggregate02_name() {
        return this.fine_aggregate02_name;
    }

    /**
     * Setter for property fine_aggregate02_name.
     * @param fine_aggregate02_name New value of property fine_aggregate02_name.
     */
    public void setFine_aggregate02_name(String fine_aggregate02_name) {
        this.fine_aggregate02_name = fine_aggregate02_name;
    }

    /**
     * Holds value of property fine_aggregate02_display_name.
     */
    private String fine_aggregate02_display_name;

    /**
     * Getter for property fine_aggregate02_display_name.
     * @return Value of property fine_aggregate02_display_name.
     */
    public String getFine_aggregate02_display_name() {
        return this.fine_aggregate02_display_name;
    }

    /**
     * Setter for property fine_aggregate02_display_name.
     * @param fine_aggregate02_display_name New value of property fine_aggregate02_display_name.
     */
    public void setFine_aggregate02_display_name(String fine_aggregate02_display_name) {
        this.fine_aggregate02_display_name = fine_aggregate02_display_name;
    }

    /**
     * Holds value of property present_coarse01_sieves_number.
     */
    private int present_coarse01_sieves_number;
    
    /**
     * Getter for property present_coarse01_sieves_number.
     * @return Value of property present_coarse01_sieves_number.
     */
    public int getpresent_coarse01_sieves_number() {
        return this.present_coarse01_sieves_number;
    }
    
    /**
     * Setter for property present_coarse01_sieves_number.
     * @param present_coarse01_sieves_number New value of property present_coarse01_sieves_number.
     */
    public void setpresent_coarse01_sieves_number(int present_coarse01_sieves_number) {
        this.present_coarse01_sieves_number = present_coarse01_sieves_number;
    }
    
    /**
     * Holds value of property present_fine01_sieves_number.
     */
    private int present_fine01_sieves_number;
    
    /**
     * Getter for property present_fine01_sieves_number.
     * @return Value of property present_fine01_sieves_number.
     */
    public int getPresent_fine01_sieves_number() {
        return this.present_fine01_sieves_number;
    }
    
    /**
     * Setter for property present_fine01_sieves_number.
     * @param present_fine01_sieves_number New value of property present_fine01_sieves_number.
     */
    public void setPresent_fine01_sieves_number(int present_fine01_sieves_number) {
        this.present_fine01_sieves_number = present_fine01_sieves_number;
    }
    
    /**
     * Holds value of property coarse_aggregate01_max_diameter.
     */
    private double coarse_aggregate01_max_diameter;
    
    /**
     * Getter for property coarse_aggregate01_max_diameter.
     * @return Value of property coarse_aggregate01_max_diameter.
     */
    public double getCoarse_aggregate01_max_diameter() {
        return this.coarse_aggregate01_max_diameter;
    }
    
    /**
     * Setter for property coarse_aggregate01_max_diameter.
     * @param coarse_aggregate01_max_diameter New value of property coarse_aggregate01_max_diameter.
     */
    public void setCoarse_aggregate01_max_diameter(double coarse_aggregate01_max_diameter) {
        this.coarse_aggregate01_max_diameter = coarse_aggregate01_max_diameter;
    }
    
    /**
     * Holds value of property fine_aggregate01_max_diameter.
     */
    private double fine_aggregate01_max_diameter;
    
    /**
     * Getter for property fine_aggregate01_max_diameter.
     * @return Value of property fine_aggregate01_max_diameter.
     */
    public double getFine_aggregate01_max_diameter() {
        return this.fine_aggregate01_max_diameter;
    }
    
    /**
     * Setter for property fine_aggregate01_max_diameter.
     * @param fine_aggregate01_max_diameter New value of property fine_aggregate01_max_diameter.
     */
    public void setFine_aggregate01_max_diameter(double fine_aggregate01_max_diameter) {
        this.fine_aggregate01_max_diameter = fine_aggregate01_max_diameter;
    }

     /**
     * Holds value of property present_coarse02_sieves_number.
     */
    private int present_coarse02_sieves_number;

    /**
     * Getter for property present_coarse02_sieves_number.
     * @return Value of property present_coarse02_sieves_number.
     */
    public int getpresent_coarse02_sieves_number() {
        return this.present_coarse02_sieves_number;
    }

    /**
     * Setter for property present_coarse02_sieves_number.
     * @param present_coarse02_sieves_number New value of property present_coarse02_sieves_number.
     */
    public void setpresent_coarse02_sieves_number(int present_coarse02_sieves_number) {
        this.present_coarse02_sieves_number = present_coarse02_sieves_number;
    }

    /**
     * Holds value of property present_fine02_sieves_number.
     */
    private int present_fine02_sieves_number;

    /**
     * Getter for property present_fine02_sieves_number.
     * @return Value of property present_fine02_sieves_number.
     */
    public int getPresent_fine02_sieves_number() {
        return this.present_fine02_sieves_number;
    }

    /**
     * Setter for property present_fine02_sieves_number.
     * @param present_fine02_sieves_number New value of property present_fine02_sieves_number.
     */
    public void setPresent_fine02_sieves_number(int present_fine02_sieves_number) {
        this.present_fine02_sieves_number = present_fine02_sieves_number;
    }

    /**
     * Holds value of property coarse_aggregate02_max_diameter.
     */
    private double coarse_aggregate02_max_diameter;

    /**
     * Getter for property coarse_aggregate02_max_diameter.
     * @return Value of property coarse_aggregate02_max_diameter.
     */
    public double getCoarse_aggregate02_max_diameter() {
        return this.coarse_aggregate02_max_diameter;
    }

    /**
     * Setter for property coarse_aggregate02_max_diameter.
     * @param coarse_aggregate02_max_diameter New value of property coarse_aggregate02_max_diameter.
     */
    public void setCoarse_aggregate02_max_diameter(double coarse_aggregate02_max_diameter) {
        this.coarse_aggregate02_max_diameter = coarse_aggregate02_max_diameter;
    }

    /**
     * Holds value of property fine_aggregate02_max_diameter.
     */
    private double fine_aggregate02_max_diameter;

    /**
     * Getter for property fine_aggregate02_max_diameter.
     * @return Value of property fine_aggregate02_max_diameter.
     */
    public double getFine_aggregate02_max_diameter() {
        return this.fine_aggregate02_max_diameter;
    }

    /**
     * Setter for property fine_aggregate02_max_diameter.
     * @param fine_aggregate02_max_diameter New value of property fine_aggregate02_max_diameter.
     */
    public void setFine_aggregate02_max_diameter(double fine_aggregate02_max_diameter) {
        this.fine_aggregate02_max_diameter = fine_aggregate02_max_diameter;
    }

    /**
     * Holds value of property concrete_resolution.
     */
    private double concrete_resolution;
    
    /**
     * Getter for property concrete_resolution.
     * @return Value of property concrete_resolution.
     */
    public double getConcrete_resolution() {
        return this.concrete_resolution;
    }
    
    /**
     * Setter for property concrete_resolution.
     * @param concrete_resolution New value of property concrete_resolution.
     */
    public void setConcrete_resolution(double concrete_resolution) {
        this.concrete_resolution = concrete_resolution;
    }
    
    /**
     * Holds value of property concrete_xdim.
     */
    private int concrete_xdim;
    
    /**
     * Getter for property concrete_xdim.
     * @return Value of property concrete_xdim.
     */
    public int getConcrete_xdim() {
        return this.concrete_xdim;
    }
    
    /**
     * Setter for property concrete_xdim.
     * @param concrete_xdim New value of property concrete_xdim.
     */
    public void setConcrete_xdim(int concrete_xdim) {
        this.concrete_xdim = concrete_xdim;
    }
    
    /**
     * Holds value of property concrete_ydim.
     */
    private int concrete_ydim;
    
    /**
     * Getter for property concrete_ydim.
     * @return Value of property concrete_ydim.
     */
    public int getConcrete_ydim() {
        return this.concrete_ydim;
    }
    
    /**
     * Setter for property concrete_ydim.
     * @param concrete_ydim New value of property concrete_ydim.
     */
    public void setConcrete_ydim(int concrete_ydim) {
        this.concrete_ydim = concrete_ydim;
    }
    
    /**
     * Holds value of property concrete_zdim.
     */
    private int concrete_zdim;
    
    /**
     * Getter for property concrete_zdim.
     * @return Value of property concrete_zdim.
     */
    public int getConcrete_zdim() {
        return this.concrete_zdim;
    }
    
    /**
     * Setter for property concrete_zdim.
     * @param concrete_zdim New value of property concrete_zdim.
     */
    public void setConcrete_zdim(int concrete_zdim) {
        this.concrete_zdim = concrete_zdim;
    }

    /**
     * Holds value of property fine_aggregate01_vol_fraction.
     */
    private double fine_aggregate01_vol_fraction;

    /**
     * Getter for property fine_aggregate01_vol_fraction.
     * @return Value of property fine_aggregate01_vol_fraction.
     */
    public double getFine_aggregate01_vol_fraction() {
        return this.fine_aggregate01_vol_fraction;
    }

    /**
     * Setter for property fine_aggregate01_vol_fraction.
     * @param fine_aggregate01_vol_fraction New value of property fine_aggregate01_vol_fraction.
     */
    public void setFine_aggregate01_vol_fraction(double fine_aggregate01_vol_fraction) {
        this.fine_aggregate01_vol_fraction = fine_aggregate01_vol_fraction;
    }

    /**
     * Holds value of property coarse_aggregate01_vol_fraction.
     */
    private double coarse_aggregate01_vol_fraction;

    /**
     * Getter for property coarse_aggregate01_vol_fraction.
     * @return Value of property coarse_aggregate01_vol_fraction.
     */
    public double getCoarse_aggregate01_vol_fraction() {
        return this.coarse_aggregate01_vol_fraction;
    }

    /**
     * Setter for property coarse_aggregate01_vol_fraction.
     * @param coarse_aggregate01_vol_fraction New value of property coarse_aggregate01_vol_fraction.
     */
    public void setCoarse_aggregate01_vol_fraction(double coarse_aggregate01_vol_fraction) {
        this.coarse_aggregate01_vol_fraction = coarse_aggregate01_vol_fraction;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_path.
     */
    private String coarse_aggregate01_grading_path;

    /**
     * Getter for property coarse_aggregate01_grading_path.
     * @return Value of property coarse_aggregate01_grading_path.
     */
    public String getCoarse_aggregate01_grading_path() {
        return this.coarse_aggregate01_grading_path;
    }

    /**
     * Setter for property coarse_aggregate01_grading_path.
     * @param coarse_aggregate01_grading_path New value of property coarse_aggregate01_grading_path.
     */
    public void setCoarse_aggregate01_grading_path(String coarse_aggregate01_grading_path) {
        this.coarse_aggregate01_grading_path = coarse_aggregate01_grading_path;
    }

    /**
     * Holds value of property fine_aggregate01_grading_path.
     */
    private String fine_aggregate01_grading_path;

    /**
     * Getter for property fine_aggregate01_grading_path.
     * @return Value of property fine_aggregate01_grading_path.
     */
    public String getFine_aggregate01_grading_path() {
        return this.fine_aggregate01_grading_path;
    }

    /**
     * Setter for property fine_aggregate01_grading_path.
     * @param fine_aggregate01_grading_path New value of property fine_aggregate01_grading_path.
     */
    public void setFine_aggregate01_grading_path(String fine_aggregate01_grading_path) {
        this.fine_aggregate01_grading_path = fine_aggregate01_grading_path;
    }

    /**
     * Holds value of property fine_aggregate02_vol_fraction.
     */
    private double fine_aggregate02_vol_fraction;

    /**
     * Getter for property fine_aggregate02_vol_fraction.
     * @return Value of property fine_aggregate02_vol_fraction.
     */
    public double getFine_aggregate02_vol_fraction() {
        return this.fine_aggregate02_vol_fraction;
    }

    /**
     * Setter for property fine_aggregate02_vol_fraction.
     * @param fine_aggregate02_vol_fraction New value of property fine_aggregate02_vol_fraction.
     */
    public void setFine_aggregate02_vol_fraction(double fine_aggregate02_vol_fraction) {
        this.fine_aggregate02_vol_fraction = fine_aggregate02_vol_fraction;
    }

    /**
     * Holds value of property coarse_aggregate02_vol_fraction.
     */
    private double coarse_aggregate02_vol_fraction;

    /**
     * Getter for property coarse_aggregate02_vol_fraction.
     * @return Value of property coarse_aggregate02_vol_fraction.
     */
    public double getCoarse_aggregate02_vol_fraction() {
        return this.coarse_aggregate02_vol_fraction;
    }

    /**
     * Setter for property coarse_aggregate02_vol_fraction.
     * @param coarse_aggregate02_vol_fraction New value of property coarse_aggregate02_vol_fraction.
     */
    public void setCoarse_aggregate02_vol_fraction(double coarse_aggregate02_vol_fraction) {
        this.coarse_aggregate02_vol_fraction = coarse_aggregate02_vol_fraction;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_path.
     */
    private String coarse_aggregate02_grading_path;

    /**
     * Getter for property coarse_aggregate02_grading_path.
     * @return Value of property coarse_aggregate02_grading_path.
     */
    public String getCoarse_aggregate02_grading_path() {
        return this.coarse_aggregate02_grading_path;
    }

    /**
     * Setter for property coarse_aggregate02_grading_path.
     * @param coarse_aggregate02_grading_path New value of property coarse_aggregate02_grading_path.
     */
    public void setCoarse_aggregate02_grading_path(String coarse_aggregate02_grading_path) {
        this.coarse_aggregate02_grading_path = coarse_aggregate02_grading_path;
    }

    /**
     * Holds value of property fine_aggregate02_grading_path.
     */
    private String fine_aggregate02_grading_path;

    /**
     * Getter for property fine_aggregate02_grading_path.
     * @return Value of property fine_aggregate02_grading_path.
     */
    public String getFine_aggregate02_grading_path() {
        return this.fine_aggregate02_grading_path;
    }

    /**
     * Setter for property fine_aggregate02_grading_path.
     * @param fine_aggregate02_grading_path New value of property fine_aggregate02_grading_path.
     */
    public void setFine_aggregate02_grading_path(String fine_aggregate02_grading_path) {
        this.fine_aggregate02_grading_path = fine_aggregate02_grading_path;
    }

    /**
     * Holds value of property waterVolumeFraction.
     */
    private Double waterVolumeFraction;

    /**
     * Getter for property waterVolumeFraction.
     * @return Value of property waterVolumeFraction.
     */
    public Double getWaterVolumeFraction() {
        return this.waterVolumeFraction;
    }

    /**
     * Setter for property waterVolumeFraction.
     * @param waterVolumeFraction New value of property waterVolumeFraction.
     */
    public void setWaterVolumeFraction(Double waterVolumeFraction) {
        this.waterVolumeFraction = waterVolumeFraction;
    }

    /**
     * Holds value of property phasesVolumeFractions.
     */
    private Map phasesVolumeFractions;

    /**
     * Getter for property phasesVolumeFractions.
     * @return Value of property phasesVolumeFractions.
     */
    public Map getPhasesVolumeFractions() {
        return this.phasesVolumeFractions;
    }

    /**
     * Setter for property phasesVolumeFractions.
     * @param phasesVolumeFractions New value of property phasesVolumeFractions.
     */
    public void setPhasesVolumeFractions(Map phasesVolumeFractions) {
        this.phasesVolumeFractions = phasesVolumeFractions;
    }

    /**
     * Holds value of property binderVolumeFraction.
     */
    private double binderVolumeFraction;

    /**
     * Getter for property binderVolumeFraction.
     * @return Value of property binderVolumeFraction.
     */
    public double getBinderVolumeFraction() {
        return this.binderVolumeFraction;
    }

    /**
     * Setter for property binderVolumeFraction.
     * @param binderVolumeFraction New value of property binderVolumeFraction.
     */
    public void setBinderVolumeFraction(double binderVolumeFraction) {
        this.binderVolumeFraction = binderVolumeFraction;
    }

    /**
     * Holds value of property distribute_clinker_phases_psd.
     */
    private String distribute_clinker_phases_psd;

    /**
     * Getter for property distribute_clinker_phases_psd.
     * @return Value of property distribute_clinker_phases_psd.
     */
    public String getDistribute_clinker_phases_psd() {
        return this.distribute_clinker_phases_psd;
    }

    /**
     * Setter for property distribute_clinker_phases_psd.
     * @param distribute_clinker_phases_psd New value of property distribute_clinker_phases_psd.
     */
    public void setDistribute_clinker_phases_psd(String distribute_clinker_phases_psd) {
        this.distribute_clinker_phases_psd = distribute_clinker_phases_psd;
    }
}
